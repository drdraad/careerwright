"""`make live-smoke`: one real connection-check run through the whole product, budget-capped.

Ruling R5. The key is read from the repository's gitignored `.env` into a `SecretStr`; it
is never a command argument and never printed. An isolated stack (its own Compose project,
ports, NESSA_HOME and volumes, removed afterwards) runs in live mode. The key travels the
product path: stored through the API with consent, sealed at once, opened only inside the
worker's bounded activity, which makes the call. Afterwards every attempt is appended to
`docs/evidence/live-usage.jsonl` (and the Markdown table) with its cost, even if the run
failed, and both databases, every container log and the API's own responses are scanned
for the key.

Caps, checked before anything starts: at most ACTIVITY_MAX_ATTEMPTS calls (the run's retry
budget), none on the production model unless `--production-model` (`PRODUCTION=1`), and a
worst-case cost cap. The test model is a Contributor model, so the workspace is synthetic.

Run from `backend/`: `uv run --locked python -m tools.live_smoke [--production-model]`.
"""

import argparse
import json
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import httpx2
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from nessa.identity import connection_check
from nessa.identity.model_choice import ModelChoice
from nessa.identity.model_registry import format_usd
from nessa.identity.workflow import ACTIVITY_MAX_ATTEMPTS
from tools.leak_scan import Finding, Needle, scan
from tools.localenv import REPO_ROOT, ensure_local_home
from tools.stack import CORE_SERVICES, Ports, Stack
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry

BUDGET_SCOPE = "live-smoke"
MAX_CALLS = ACTIVITY_MAX_ATTEMPTS
MAX_COST_NANO_USD = 100_000_000  # $0.10 worst case per invocation
SMOKE_PORTS = Ports(api=57800, auth=57899, postgres=57832, web=57900)
RUN_TIMEOUT_S = 240.0
RESPONSES_ENDPOINT = "POST /v1/responses"
PURPOSE = "connection check via API, outbox and DBOS worker (key opened just in time)"


class SmokeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    api_key: SecretStr = Field(validation_alias="META_API_KEY")
    meta_test_model: str = Field(
        default="muse-spark-1.3-contributor", validation_alias="NESSA_META_TEST_MODEL"
    )
    meta_production_model: str = Field(
        default="muse-spark-1.3", validation_alias="NESSA_META_PRODUCTION_MODEL"
    )


class CapExceededError(SystemExit):
    pass


def authorise(models: ModelChoice, *, production: bool) -> tuple[str, int]:
    """The model this invocation may use and its worst case, or refuse before any call."""
    model_id = models.production.model_id if production else models.test.model_id
    if models.is_production(model_id) and not production:
        raise CapExceededError("the test model is the production model: pass --production-model")
    worst_case = MAX_CALLS * connection_check.worst_case_nano_usd(model_id)
    if worst_case > MAX_COST_NANO_USD:
        raise CapExceededError(
            f"worst case {format_usd(worst_case)} exceeds the cap {format_usd(MAX_COST_NANO_USD)}"
        )
    return model_id, worst_case


def _sign_in(stack: Stack) -> str:
    response = httpx2.post(
        f"{stack.auth_url}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
        params={"key": "emulator"},
        json={"email": "ada@nessa.test", "password": "nessa-demo-ada", "returnSecureToken": True},
        timeout=20,
    )
    response.raise_for_status()
    return str(response.json()["idToken"])


class Api:
    def __init__(self, stack: Stack, token: str) -> None:
        self._stack = stack
        self._token = token
        self.responses: list[tuple[str, str]] = []

    def call(self, method: str, path: str, body: object = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._token}"}
        if method != "GET":
            headers |= {"Origin": self._stack.web_origin, "Idempotency-Key": str(uuid.uuid4())}
        response = httpx2.request(
            method, f"{self._stack.api_url}{path}", json=body, headers=headers, timeout=30
        )
        self.responses.append((f"{method} {path} -> {response.status_code}", response.text))
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed: {response.json()['error']['code']}")
        result: dict[str, Any] = response.json()
        return result


def _superuser(stack: Stack, database: str) -> str:
    password = (stack.home / "secrets" / "pg_superuser").read_text().strip()
    return f"postgresql://postgres:{password}@127.0.0.1:{stack.ports.postgres}/{database}"


def _all_attempts(stack: Stack) -> list[dict[str, Any]]:
    """Every attempt in the smoke database, which exists for this invocation only, so no call
    escapes the ledger even if the client never learned its run ID."""
    with psycopg.connect(_superuser(stack, "nessa_app"), row_factory=dict_row) as conn:
        return conn.execute("SELECT * FROM nessa.model_attempts ORDER BY attempt_id").fetchall()


def ledger_attempts(
    ledger: Ledger, attempts: list[dict[str, Any]], *, production_model: str
) -> list[int]:
    """One ledger row per attempt that reached the provider (a reservation was taken)."""
    seqs = []
    for attempt in attempts:
        if attempt["spend_state"] == "none":
            continue  # refused before any call: nothing was sent to Meta
        outcome = attempt["outcome"] or "unfinished"
        record = ledger.append(
            LiveCallEntry(
                budget_scope=BUDGET_SCOPE,
                purpose=PURPOSE,
                model_id=attempt["model_id"],
                is_production_model=attempt["model_id"] == production_model,
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.OK if outcome == "succeeded" else CallOutcome.FAILED,
                reserved_nano_usd=attempt["reserved_nano_usd"],
                estimated_cost_nano_usd=attempt["cost_nano_usd"],
                error_type=None if outcome == "succeeded" else outcome,
                input_tokens=attempt["input_tokens"],
                cached_input_tokens=attempt["cached_input_tokens"],
                output_tokens=attempt["output_tokens"],
                reasoning_tokens=attempt["reasoning_tokens"],
                web_search_queries=attempt["web_search_queries"],
                provider_response_id=attempt["provider_response_id"],
                notes=json.dumps(
                    {"run_id": str(attempt["run_id"]), "attempt_id": attempt["attempt_id"]}
                ),
            )
        )
        seqs.append(record.seq)
    return seqs


def ledger_possible_calls(
    ledger: Ledger, model_id: str, reserved_nano_usd: int, models: ModelChoice
) -> list[int]:
    """The attempts could not be read: record every call the run was allowed to make, with an
    unknown cost, rather than nothing."""
    return [
        ledger.append(
            LiveCallEntry(
                budget_scope=BUDGET_SCOPE,
                purpose=f"{PURPOSE} (possible call; attempts unreadable)",
                model_id=model_id,
                is_production_model=models.is_production(model_id),
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.FAILED,
                reserved_nano_usd=reserved_nano_usd,
                error_type="attempts_unreadable",
            )
        ).seq
        for _ in range(MAX_CALLS)
    ]


def leak_findings(stack: Stack, api: Api, key: SecretStr) -> tuple[int, list[Finding]]:
    cells: list[tuple[str, str]] = list(api.responses)
    for database in ("nessa_app", "nessa_dbos"):
        with psycopg.connect(_superuser(stack, database), row_factory=dict_row) as conn:
            tables = conn.execute(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' "
                "AND table_schema NOT IN ('pg_catalog', 'information_schema')"
            ).fetchall()
            for table in tables:
                rows = conn.execute(
                    sql.SQL("SELECT row_to_json(t)::text AS row FROM {}.{} t").format(
                        sql.Identifier(table["table_schema"]), sql.Identifier(table["table_name"])
                    )
                ).fetchall()
                name = f"{database}:{table['table_schema']}.{table['table_name']}"
                cells += [(name, str(row["row"])) for row in rows]
    cells.append(("container logs", stack.logs()))
    needles = [Needle("Meta key", key.get_secret_value(), fragment_length=12)]
    return len(cells), scan(cells, needles)


def run_smoke(settings: SmokeSettings, *, production: bool, ledger: Ledger) -> int:
    models = ModelChoice.configure(
        settings.meta_test_model,
        settings.meta_production_model,
        "production" if production else "test",
    )
    model_id, worst_case = authorise(models, production=production)
    print(
        f"live smoke: model {model_id} ({'production' if production else 'test'}); "
        f"at most {MAX_CALLS} calls, worst case {format_usd(worst_case)}",
        flush=True,
    )
    home = Path(tempfile.mkdtemp(prefix="nessa-smoke-"))
    ensure_local_home(home)
    stack = Stack(
        project="nessa-l0-smoke",
        home=home,
        ports=SMOKE_PORTS,
        live=True,
        overrides=(("NESSA_SYNTHETIC_MODEL_ROLE", "production" if production else "test"),),
    )
    key_sent = False
    status = "not started"
    findings: list[Finding] = []
    try:
        stack.down()
        stack.build()
        stack.up(*CORE_SERVICES)
        api = Api(stack, _sign_in(stack))
        workspace = api.call(
            "POST",
            "/v1/workspaces",
            {"name": "Live smoke (synthetic)", "data_mode": "live_assisted", "synthetic": True},
        )
        base = f"/v1/workspaces/{workspace['workspace_id']}"
        key_sent = True  # from here on the worker may call Meta
        api.call(
            "POST",
            f"{base}/credentials",
            {"api_key": settings.api_key.get_secret_value(), "consent_to_encrypted_storage": True},
        )
        run_id = str(api.call("POST", f"{base}/runs", {"kind": "connection_check"})["run_id"])
        deadline = time.monotonic() + RUN_TIMEOUT_S
        run = api.call("GET", f"{base}/runs/{run_id}")
        while run["status"] in ("queued", "running") and time.monotonic() < deadline:
            time.sleep(1)
            run = api.call("GET", f"{base}/runs/{run_id}")
        status = str(run["status"])
        api.call("GET", f"{base}/export")
        print(f"run {run_id}: {status} {run['failure_class'] or ''}".rstrip(), flush=True)
        if run["output"]:
            print(f"validated output: {run['output']}", flush=True)
        scanned, findings = leak_findings(stack, api, settings.api_key)
        print(f"leak scan: {scanned} rows/logs/responses, findings: {findings}", flush=True)
    finally:
        if key_sent:
            try:
                attempts = _all_attempts(stack)
            except psycopg.Error:
                seqs = ledger_possible_calls(ledger, model_id, worst_case // MAX_CALLS, models)
            else:
                seqs = ledger_attempts(
                    ledger, attempts, production_model=models.production.model_id
                )
            ledger.write_markdown()
            print(f"ledger rows appended: {seqs}", flush=True)
        stack.down()
        shutil.rmtree(home, ignore_errors=True)
        print("smoke stack, volumes and keys removed", flush=True)
    return 0 if status == "complete" and not findings else 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--production-model",
        action="store_true",
        help="qualify the production model (counts as production calls)",
    )
    args = parser.parse_args(argv)
    sys.exit(run_smoke(SmokeSettings(), production=args.production_model, ledger=Ledger()))


if __name__ == "__main__":
    main()
