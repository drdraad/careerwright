"""Live check of the pinned composition with the real key (S0.4), budget-capped (R5).

Run from `backend/`: `uv run python -m spikes.durable.live_run`.

Two runs go through the real worker and DBOS on a fresh spike database: one with the real
Meta key (sealed into the credential store from `.env`, opened only inside the activity) on
the test model, and one with an unissued key, which must fail as `provider_authentication`.
Afterwards both databases and the worker log are scanned for the keys and the private text,
the journal is printed, and the stack is removed with its volume.
"""

import json
import secrets
import tempfile
import uuid
from pathlib import Path

from pydantic import SecretStr

from spikes.durable import stack
from spikes.durable.leak_scan import Needle, scan
from spikes.durable.store import AppStore
from spikes.durable.worker import keyring_from_file
from spikes.durable.workflow import ACTIVITY_MAX_ATTEMPTS, ProfileProposal
from spikes.meta.budget import CallPlan, SpentSoFar, authorise_call
from spikes.meta.ledger import CallOutcome, Ledger, LiveCallEntry
from spikes.meta.live_spike import (
    BUDGET_SCOPE,
    LEDGER_PATH,
    POLICY,
    RESPONSES_ENDPOINT,
    SCHEMA_LIMITS,
    write_markdown,
)
from spikes.meta.pricing import Usage, estimate_cost_nano_usd, worst_case_cost_nano_usd
from spikes.meta.settings import MetaSettings

RUN_TIMEOUT_S = 180.0


def _reserve(ledger: Ledger, model_id: str) -> int:
    """Authorise the worst case: every activity attempt of the real-key run, plus one free call."""
    per_attempt = worst_case_cost_nano_usd(
        model_id,
        max_input_tokens=SCHEMA_LIMITS.max_input_tokens,
        max_output_tokens=SCHEMA_LIMITS.max_output_tokens,
        max_web_searches=0,
    )
    spent = ledger.spent(BUDGET_SCOPE)
    for attempt in range(ACTIVITY_MAX_ATTEMPTS + 1):
        authorise_call(
            POLICY,
            SpentSoFar(
                calls=spent.calls + attempt,
                production_calls=spent.production_calls,
                committed_nano_usd=spent.committed_nano_usd + attempt * per_attempt,
            ),
            CallPlan(is_production_model=False, worst_case_nano_usd=per_attempt),
        )
    return per_attempt


def _record_attempts(
    ledger: Ledger, app: str, run_id: str, *, purpose: str, reserved: int, free: bool
) -> None:
    for attempt in stack.query(
        app, "SELECT * FROM activity_attempts WHERE run_id = %s ORDER BY attempt_id", (run_id,)
    ):
        if attempt["input_tokens"] is not None:
            usage = Usage(
                input_tokens=attempt["input_tokens"],
                cached_input_tokens=attempt["cached_input_tokens"],
                output_tokens=attempt["output_tokens"],
                web_search_queries=attempt["web_search_queries"],
            )
            cost: int | None = estimate_cost_nano_usd(attempt["model_id"], usage)
        else:
            usage, cost = None, (0 if free else None)
        ledger.append(
            LiveCallEntry(
                budget_scope=BUDGET_SCOPE,
                purpose=purpose,
                model_id=attempt["model_id"],
                is_production_model=False,
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.OK if attempt["outcome"] == "succeeded" else CallOutcome.FAILED,
                reserved_nano_usd=0 if free else reserved,
                estimated_cost_nano_usd=cost,
                http_status=401 if attempt["outcome"] == "provider_authentication" else None,
                error_type=None if attempt["outcome"] == "succeeded" else attempt["outcome"],
                input_tokens=usage.input_tokens if usage else None,
                cached_input_tokens=usage.cached_input_tokens if usage else None,
                output_tokens=usage.output_tokens if usage else None,
                reasoning_tokens=attempt["reasoning_tokens"],
                web_search_queries=usage.web_search_queries if usage else None,
                provider_response_id=attempt["provider_response_id"],
                notes=json.dumps({"activity_attempt": attempt["attempt_id"], "via": "DBOS step"}),
            )
        )


def main() -> None:
    settings = MetaSettings()
    ledger = Ledger(LEDGER_PATH)
    reserved = _reserve(ledger, settings.test_model)
    with tempfile.TemporaryDirectory(prefix="nessa-spike-") as tmp:
        work = Path(tmp)
        spike = stack.start(work / "master.key")
        try:
            store = AppStore(spike.app_url, keyring_from_file(spike.master_key_file))
            store.install_schema()
            sentinel = f"PRIVATE-SENTINEL-{secrets.token_hex(8)}"
            private_text = (
                f"Synthetic CV, not a real person ({sentinel}): I supervise warehouse shifts "
                "in Leeds and enjoy training new starters."
            )
            # No fixed prefix: every 12-character window must be secret material, or the
            # fragment scan matches public names such as the DBOS app version.
            fake_key = SecretStr(secrets.token_urlsafe(32))
            real_ws, fake_ws = str(uuid.uuid4()), str(uuid.uuid4())
            real_run = store.submit_run(
                real_ws, store.store_credential(real_ws, settings.api_key), private_text
            )
            fake_run = store.submit_run(
                fake_ws, store.store_credential(fake_ws, fake_key), private_text
            )

            log = work / "worker.log"
            worker = stack.start_worker(spike, log, activity_model=settings.test_model)
            for entry in (real_run, fake_run):
                stack.wait_for(
                    lambda e=entry: (
                        stack.query(  # type: ignore[misc]
                            spike.app_url, "SELECT status FROM runs WHERE run_id = %s", (e.run_id,)
                        )[0]["status"]
                        != "queued"
                    ),
                    timeout_s=RUN_TIMEOUT_S,
                    what=f"run {entry.run_id}",
                )
            print("worker exit code:", worker.stop())

            _record_attempts(
                ledger,
                spike.app_url,
                real_run.run_id,
                purpose="schema output inside DBOS activity (key opened just in time)",
                reserved=reserved,
                free=False,
            )
            _record_attempts(
                ledger,
                spike.app_url,
                fake_run.run_id,
                purpose="invalid key inside DBOS activity",
                reserved=0,
                free=True,
            )
            write_markdown(ledger)

            dbos_db = spike.superuser_url_for("nessa_spike_dbos")
            for name, entry in (("real-key run", real_run), ("invalid-key run", fake_run)):
                run = stack.query(
                    spike.app_url,
                    "SELECT status, failure_class, output_id::text FROM runs WHERE run_id = %s",
                    (entry.run_id,),
                )[0]
                print(f"\n== {name}: {run}")
                for table, column in (
                    ("workflow_status", "status, name, serialization, recovery_attempts"),
                    ("workflow_input", "inputs"),
                    ("workflow_output", "output, error"),
                    ("operation_outputs", "function_id, function_name, output, error"),
                ):
                    rows = stack.query(
                        dbos_db,
                        f"SELECT {column} FROM dbos.{table} WHERE workflow_uuid = %s",  # noqa: S608
                        (entry.workflow_id,),
                    )
                    print(f"dbos.{table}: {rows}")
                if run["output_id"]:
                    proposal = ProfileProposal.model_validate_json(
                        store.open_output(run["output_id"])
                    )
                    print("validated output (opened from sealed store):", proposal.model_dump())

            needles = [
                Needle("real Meta key", settings.api_key.get_secret_value(), fragment_length=12),
                Needle("invalid key", fake_key.get_secret_value(), fragment_length=12),
                Needle("private text", sentinel),
            ]
            cells = [
                *stack.database_cells(dbos_db),
                *stack.database_cells(spike.superuser_url_for("nessa_spike_app")),
                (log.name, log.read_text(encoding="utf-8")),
            ]
            findings = scan(cells, needles)
            print(f"\nleak scan: {len(cells)} rows/logs scanned, findings: {findings}")
        finally:
            stack.stop()
            print("spike stack and volume removed")


if __name__ == "__main__":
    main()
