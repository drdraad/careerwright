"""`make live-smoke`: one real connection-check run through the whole product, budget-capped.

Ruling R5. The key is read from the repository's gitignored `.env` into a `SecretStr`; it
is never a command argument and never printed. An isolated stack (its own Compose project,
ports, NESSA_HOME and volumes, removed afterwards) runs in live mode. The key travels the
product path: stored through the API with consent, sealed at once, opened only inside the
worker's bounded activity, which makes the call. Afterwards the worker is stopped, so no
further call can start, and then every attempt of the smoke workspace is appended to
`docs/evidence/live-usage.jsonl` (and the Markdown table) with its cost, even if the run
failed; if the worker cannot be confirmed stopped, every further call its spend limits
allow is ledgered too, with an unknown cost. Then both databases, every container log and
the API's own responses are scanned for the key.

Caps, checked before anything starts:
- per invocation: at most ACTIVITY_MAX_ATTEMPTS calls (the run's retry budget, also set as
  the workspace's run spend limit, so the product's own reservation enforces it), none on
  the production model unless `--production-model` (`PRODUCTION=1`), and a worst-case cost
  cap;
- per budget scope, cumulative over the ledger: calls, production calls and worst-case cost
  (`ScopeBudget`; conservative defaults, configurable through `NESSA_LIVE_SMOKE_*`), checked
  and spent under an exclusive lock on the ledger, so a concurrent invocation refuses.
The test model is a Contributor model, so the workspace is synthetic.

Run from `backend/`: `uv run --locked python -m tools.live_smoke [--production-model]`.
"""

import argparse
import json
import shutil
import sys
import tempfile
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import httpx2
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from nessa.identity import connection_check
from nessa.identity.activity import STORE_RETRY_BUDGET_S
from nessa.identity.meta import REQUEST_TIMEOUT_S
from nessa.identity.model_choice import ModelChoice
from nessa.identity.model_registry import format_usd
from nessa.identity.workflow import (
    ACTIVITY_BACKOFF_RATE,
    ACTIVITY_INTERVAL_S,
    ACTIVITY_MAX_ATTEMPTS,
)
from tools.leak_scan import Finding, Needle, scan
from tools.localenv import REPO_ROOT, ensure_local_home
from tools.stack import CORE_SERVICES, Ports, Stack
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry, ScopeSpend

MAX_CALLS = ACTIVITY_MAX_ATTEMPTS
MAX_COST_NANO_USD = 100_000_000  # $0.10 worst case per invocation
SMOKE_PORTS = Ports(api=57800, auth=57899, postgres=57832, web=57900)
# How long the smoke waits for the run: its worst case, where every attempt times out and
# both of its store transactions (prepare, settle) spend the whole store budget, with the
# step's backoff between attempts, plus a minute for the stack. Ledger completeness does not
# depend on it: the worker is stopped before the attempts are read.
RUN_TIMEOUT_S = (
    MAX_CALLS * (REQUEST_TIMEOUT_S + 2 * STORE_RETRY_BUDGET_S)
    + sum(ACTIVITY_INTERVAL_S * ACTIVITY_BACKOFF_RATE**i for i in range(MAX_CALLS - 1))
    + 60.0
)
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
    # The cumulative budget scope (ruling R5). Defaults: three smoke invocations, one of them
    # on the production model, and $0.30 worst case in all.
    budget_scope: str = Field(default="live-smoke", validation_alias="NESSA_LIVE_SMOKE_SCOPE")
    scope_max_calls: int = Field(default=9, ge=0, validation_alias="NESSA_LIVE_SMOKE_MAX_CALLS")
    scope_max_production_calls: int = Field(
        default=3, ge=0, validation_alias="NESSA_LIVE_SMOKE_MAX_PRODUCTION_CALLS"
    )
    scope_max_cost_nano_usd: int = Field(
        default=300_000_000, ge=0, validation_alias="NESSA_LIVE_SMOKE_MAX_COST_NANO_USD"
    )

    def budget(self) -> "ScopeBudget":
        return ScopeBudget(
            self.budget_scope,
            self.scope_max_calls,
            self.scope_max_production_calls,
            self.scope_max_cost_nano_usd,
        )


@dataclass(frozen=True)
class ScopeBudget:
    scope: str
    max_calls: int
    max_production_calls: int
    max_cost_nano_usd: int  # known costs plus the full reservation of every unknown one


class CapExceededError(SystemExit):
    pass


class WorkerNotStoppedError(RuntimeError):
    """The worker could not be confirmed stopped; every possible call has been ledgered."""


def authorise(
    models: ModelChoice, *, production: bool, budget: ScopeBudget, spent: ScopeSpend
) -> tuple[str, int]:
    """The model this invocation may use and its worst case, or refuse before any call:
    both this invocation's caps and what is left of the scope's cumulative budget."""
    model_id = models.production.model_id if production else models.test.model_id
    if models.is_production(model_id) and not production:
        raise CapExceededError("the test model is the production model: pass --production-model")
    worst_case = MAX_CALLS * connection_check.worst_case_nano_usd(model_id)
    if worst_case > MAX_COST_NANO_USD:
        raise CapExceededError(
            f"worst case {format_usd(worst_case)} exceeds the cap {format_usd(MAX_COST_NANO_USD)}"
        )
    if spent.calls + MAX_CALLS > budget.max_calls:
        raise CapExceededError(
            f"scope {budget.scope}: {spent.calls} of {budget.max_calls} calls used, "
            f"{MAX_CALLS} more needed"
        )
    if models.is_production(model_id) and (
        spent.production_calls + MAX_CALLS > budget.max_production_calls
    ):
        raise CapExceededError(
            f"scope {budget.scope}: {spent.production_calls} of {budget.max_production_calls} "
            f"production calls used, {MAX_CALLS} more needed"
        )
    if spent.committed_nano_usd + worst_case > budget.max_cost_nano_usd:
        raise CapExceededError(
            f"scope {budget.scope}: {format_usd(spent.committed_nano_usd)} of "
            f"{format_usd(budget.max_cost_nano_usd)} committed, worst case "
            f"{format_usd(worst_case)} more"
        )
    return model_id, worst_case


class SmokeTarget(Protocol):
    """A running Nessa the smoke drives: the isolated Compose stack (`StackTarget`), or in
    tests the integration stack with a fake-model worker."""

    @property
    def http(self) -> httpx2.Client: ...  # base URL: the API

    @property
    def web_origin(self) -> str: ...

    def sign_in(self) -> str: ...

    def superuser_url(self, database: str) -> str: ...

    def stop_worker(self) -> None: ...  # no model call can start after this returns

    def logs(self) -> str: ...


class Api:
    def __init__(self, target: SmokeTarget, token: str) -> None:
        self._target = target
        self._token = token
        self.responses: list[tuple[str, str]] = []

    def call(self, method: str, path: str, body: object = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._token}"}
        if method != "GET":
            headers |= {"Origin": self._target.web_origin, "Idempotency-Key": str(uuid.uuid4())}
        response = self._target.http.request(method, path, json=body, headers=headers)
        self.responses.append((f"{method} {path} -> {response.status_code}", response.text))
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed: {response.json()['error']['code']}")
        result: dict[str, Any] = response.json()
        return result


def _workspace_attempts(target: SmokeTarget, workspace_id: str) -> list[dict[str, Any]]:
    """Every attempt of the smoke workspace, whichever run made it, so no call escapes the
    ledger even if the client never learned its run ID."""
    with psycopg.connect(target.superuser_url("nessa_app"), row_factory=dict_row) as conn:
        return conn.execute(
            "SELECT * FROM nessa.model_attempts WHERE workspace_id = %s ORDER BY attempt_id",
            (workspace_id,),
        ).fetchall()


def ledger_attempts(
    ledger: Ledger, attempts: list[dict[str, Any]], *, scope: str, production_model: str
) -> list[int]:
    """One ledger row per attempt that reached the provider (a reservation was taken)."""
    seqs = []
    for attempt in attempts:
        if attempt["spend_state"] == "none":
            continue  # refused before any call: nothing was sent to Meta
        outcome = attempt["outcome"] or "unfinished"
        record = ledger.append(
            LiveCallEntry(
                budget_scope=scope,
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
    ledger: Ledger,
    model_id: str,
    reserved_nano_usd: int,
    models: ModelChoice,
    *,
    scope: str,
    count: int = MAX_CALLS,
    reason: str = "attempts unreadable",
) -> list[int]:
    """Calls that may have reached Meta but cannot be read back: record each one, with an
    unknown cost, rather than nothing."""
    return [
        ledger.append(
            LiveCallEntry(
                budget_scope=scope,
                purpose=f"{PURPOSE} (possible call; {reason})",
                model_id=model_id,
                is_production_model=models.is_production(model_id),
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.FAILED,
                reserved_nano_usd=reserved_nano_usd,
                error_type="attempts_unreadable",
            )
        ).seq
        for _ in range(count)
    ]


def ledger_workspace_calls(
    ledger: Ledger,
    target: SmokeTarget,
    workspace_id: str,
    *,
    model_id: str,
    worst_case: int,
    models: ModelChoice,
    scope: str,
    worker_stopped: bool,
) -> list[int]:
    """Every attempt the smoke workspace recorded. If the worker may still be running, also
    every further call its spend limits allow (MAX_CALLS in all), as possible calls."""
    per_call = worst_case // MAX_CALLS
    try:
        attempts = _workspace_attempts(target, workspace_id)
    except psycopg.Error:
        return ledger_possible_calls(ledger, model_id, per_call, models, scope=scope)
    seqs = ledger_attempts(
        ledger, attempts, scope=scope, production_model=models.production.model_id
    )
    if not worker_stopped:
        seqs += ledger_possible_calls(
            ledger,
            model_id,
            per_call,
            models,
            scope=scope,
            count=max(0, MAX_CALLS - len(seqs)),
            reason="worker not confirmed stopped",
        )
    return seqs


def leak_findings(target: SmokeTarget, api: Api, key: SecretStr) -> tuple[int, list[Finding]]:
    cells: list[tuple[str, str]] = list(api.responses)
    for database in ("nessa_app", "nessa_dbos"):
        with psycopg.connect(target.superuser_url(database), row_factory=dict_row) as conn:
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
    cells.append(("container logs", target.logs()))
    needles = [Needle("Meta key", key.get_secret_value(), fragment_length=12)]
    return len(cells), scan(cells, needles)


@dataclass(frozen=True)
class SmokeResult:
    status: str  # the run's final status, or why there is none
    findings: list[Finding]
    ledger_seqs: list[int]


def smoke(
    target: SmokeTarget,
    key: SecretStr,
    *,
    model_id: str,
    worst_case: int,
    models: ModelChoice,
    ledger: Ledger,
    scope: str,
    run_timeout_s: float = RUN_TIMEOUT_S,
) -> SmokeResult:
    """One connection-check run through the product, then the ledger. Once the key is stored
    the worker may call Meta, so from then on the attempts are ledgered whatever happens,
    after the worker has stopped."""
    api = Api(target, target.sign_in())
    workspace = api.call(
        "POST",
        "/v1/workspaces",
        {"name": "Live smoke (synthetic)", "data_mode": "live_assisted", "synthetic": True},
    )
    base = f"/v1/workspaces/{workspace['workspace_id']}"
    # The product's own reservation then refuses any call beyond this invocation's cap.
    api.call(
        "PUT",
        f"{base}/spend/limits",
        {
            "expected_version": 0,
            "run_limit_nano_usd": worst_case,
            "period_limit_nano_usd": worst_case,
        },
    )
    status = "not started"
    worker_stopped = True
    try:
        api.call(
            "POST",
            f"{base}/credentials",
            {"api_key": key.get_secret_value(), "consent_to_encrypted_storage": True},
        )
        run_id = str(api.call("POST", f"{base}/runs", {"kind": "connection_check"})["run_id"])
        deadline = time.monotonic() + run_timeout_s
        run = api.call("GET", f"{base}/runs/{run_id}")
        while run["status"] in ("queued", "running") and time.monotonic() < deadline:
            time.sleep(1)
            run = api.call("GET", f"{base}/runs/{run_id}")
        status = str(run["status"])
        api.call("GET", f"{base}/export")
        print(f"run {run_id}: {status} {run['failure_class'] or ''}".rstrip(), flush=True)
        if run["output"]:
            print(f"validated output: {run['output']}", flush=True)
    finally:
        # First: an attempt read while the worker runs could miss one.
        try:
            target.stop_worker()
        except Exception:  # any docker failure: the worker may still be calling
            worker_stopped = False
        seqs = ledger_workspace_calls(
            ledger,
            target,
            workspace["workspace_id"],
            model_id=model_id,
            worst_case=worst_case,
            models=models,
            scope=scope,
            worker_stopped=worker_stopped,
        )
        ledger.write_markdown()
        print(f"ledger rows appended: {seqs}", flush=True)
    if not worker_stopped:
        raise WorkerNotStoppedError(
            "the worker could not be confirmed stopped; every call it could still make is "
            "ledgered with an unknown cost"
        )
    # After the stop, so every log line the worker wrote is scanned.
    scanned, findings = leak_findings(target, api, key)
    print(f"leak scan: {scanned} rows/logs/responses, findings: {findings}", flush=True)
    return SmokeResult(status, findings, seqs)


@dataclass(frozen=True)
class StackTarget:
    stack: Stack
    http: httpx2.Client

    @property
    def web_origin(self) -> str:
        return self.stack.web_origin

    def sign_in(self) -> str:
        response = httpx2.post(
            f"{self.stack.auth_url}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
            params={"key": "emulator"},
            json={
                "email": "ada@nessa.test",
                "password": "nessa-demo-ada",
                "returnSecureToken": True,
            },
            timeout=20,
        )
        response.raise_for_status()
        return str(response.json()["idToken"])

    def superuser_url(self, database: str) -> str:
        password = (self.stack.home / "secrets" / "pg_superuser").read_text().strip()
        return f"postgresql://postgres:{password}@127.0.0.1:{self.stack.ports.postgres}/{database}"

    def stop_worker(self) -> None:
        self.stack.stop(("worker",))
        if "worker" in self.stack.running():  # `stop` falls back to an unchecked `kill`
            raise RuntimeError("the worker is still running after stop")

    def logs(self) -> str:
        return self.stack.logs()


@contextmanager
def smoke_stack(*, production: bool) -> Iterator[StackTarget]:
    """An isolated live-mode stack (own project, ports, NESSA_HOME, volumes), removed after."""
    home = Path(tempfile.mkdtemp(prefix="nessa-smoke-"))
    ensure_local_home(home)
    stack = Stack(
        project="nessa-l0-smoke",
        home=home,
        ports=SMOKE_PORTS,
        live=True,
        overrides=(("NESSA_SYNTHETIC_MODEL_ROLE", "production" if production else "test"),),
    )
    try:
        stack.down()
        stack.build()
        stack.up(*CORE_SERVICES)
        with httpx2.Client(base_url=stack.api_url, timeout=30) as http:
            yield StackTarget(stack, http)
    finally:
        stack.down()
        shutil.rmtree(home, ignore_errors=True)
        print("smoke stack, volumes and keys removed", flush=True)


def run_smoke(settings: SmokeSettings, *, production: bool, ledger: Ledger) -> int:
    models = ModelChoice.configure(
        settings.meta_test_model,
        settings.meta_production_model,
        "production" if production else "test",
    )
    budget = settings.budget()
    # One invocation at a time, from the budget check to the last ledger row (N6).
    with ledger.exclusive():
        model_id, worst_case = authorise(
            models, production=production, budget=budget, spent=ledger.spent(budget.scope)
        )
        print(
            f"live smoke: model {model_id} ({'production' if production else 'test'}); "
            f"at most {MAX_CALLS} calls, worst case {format_usd(worst_case)}",
            flush=True,
        )
        with smoke_stack(production=production) as target:
            result = smoke(
                target,
                settings.api_key,
                model_id=model_id,
                worst_case=worst_case,
                models=models,
                ledger=ledger,
                scope=budget.scope,
            )
    return 0 if result.status == "complete" and not result.findings else 1


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
