"""Live check of the pinned composition with the real key (S0.4), budget-capped (R5).

Run from `backend/`: `uv run python -m spikes.durable.live_run`.

Two runs go through the real worker and DBOS on a fresh spike database: one with the real
Meta key (sealed into the credential store from `.env`, opened only inside the activity) on
the test model, and one with an unissued key, which must fail as `provider_authentication`.
Afterwards both databases and the worker log are scanned for the keys, the private text and
the model's output, the journal is printed, and the stack is removed with its volume.
"""

import json
import secrets
import tempfile
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from pydantic import SecretStr

from spikes.durable import stack
from spikes.durable.leak_scan import Finding, Needle, scan
from spikes.durable.stack import SpikeStack
from spikes.durable.store import AppStore
from spikes.durable.worker import keyring_from_file
from spikes.durable.workflow import ACTIVITY_MAX_ATTEMPTS, ProfileProposal
from spikes.meta.budget import CallPlan, SpentSoFar, authorise_call
from spikes.meta.ledger import CallOutcome, Ledger, LiveCallEntry
from spikes.meta.live_spike import (
    BUDGET_SCOPE,
    LEDGER_PATH,
    MARKDOWN_PATH,
    POLICY,
    RESPONSES_ENDPOINT,
    SCHEMA_LIMITS,
    write_markdown,
)
from spikes.meta.pricing import (
    UnknownModelPriceError,
    Usage,
    estimate_cost_nano_usd,
    worst_case_cost_nano_usd,
)
from spikes.meta.settings import MetaSettings

RUN_TIMEOUT_S = 180.0
# Long enough that no legitimate journal or log string matches by chance.
PRIVATE_TEXT_FRAGMENT = 24


@dataclass(frozen=True)
class LedgeredRun:
    """A run whose activity attempts are live Meta calls that must reach the ledger."""

    run_id: str
    purpose: str
    model_id: str
    reserved_nano_usd: int  # per attempt
    free: bool  # unissued key: Meta identifies no team to bill


def reserve_worker_calls(ledger: Ledger, model_id: str, *, is_production: bool) -> int:
    """Pre-authorise, as a batch, every attempt the worker may make: the real-key run's
    retries plus the free invalid-key call. Worker calls cannot be checked one by one."""
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
                production_calls=spent.production_calls + (attempt if is_production else 0),
                committed_nano_usd=spent.committed_nano_usd + attempt * per_attempt,
            ),
            CallPlan(is_production_model=is_production, worst_case_nano_usd=per_attempt),
        )
    return per_attempt


def _attempt_entry(
    run: LedgeredRun, attempt: Mapping[str, Any], production_model: str
) -> LiveCallEntry:
    usage: Usage | None = None
    cost: int | None = 0 if run.free else None
    if attempt["input_tokens"] is not None:
        usage = Usage(
            input_tokens=attempt["input_tokens"],
            cached_input_tokens=attempt["cached_input_tokens"],
            output_tokens=attempt["output_tokens"],
            web_search_queries=attempt["web_search_queries"],
        )
        try:
            cost = estimate_cost_nano_usd(attempt["model_id"], usage)
        except UnknownModelPriceError:
            cost = None
    outcome = attempt["outcome"]
    return LiveCallEntry(
        budget_scope=BUDGET_SCOPE,
        purpose=run.purpose,
        model_id=attempt["model_id"],
        is_production_model=attempt["model_id"] == production_model,
        endpoint=RESPONSES_ENDPOINT,
        outcome=CallOutcome.OK if outcome == "succeeded" else CallOutcome.FAILED,
        reserved_nano_usd=0 if run.free else run.reserved_nano_usd,
        estimated_cost_nano_usd=cost,
        http_status=401 if outcome == "provider_authentication" else None,
        # An unfinished attempt (worker stopped mid-call) has no outcome yet.
        error_type=None if outcome == "succeeded" else (outcome or "unfinished"),
        input_tokens=usage.input_tokens if usage else None,
        cached_input_tokens=usage.cached_input_tokens if usage else None,
        output_tokens=usage.output_tokens if usage else None,
        reasoning_tokens=attempt["reasoning_tokens"],
        web_search_queries=usage.web_search_queries if usage else None,
        provider_response_id=attempt["provider_response_id"],
        notes=json.dumps({"activity_attempt": attempt["attempt_id"], "via": "DBOS step"}),
    )


def ledger_attempts(
    ledger: Ledger, app_url: str, runs: Sequence[LedgeredRun], *, production_model: str
) -> None:
    """Append one row per activity attempt. If the attempt rows cannot be read, append the
    worst case (every allowed attempt as a possible call) rather than nothing."""
    try:
        attempts = {
            run.run_id: stack.query(
                app_url,
                "SELECT * FROM activity_attempts WHERE run_id = %s ORDER BY attempt_id",
                (run.run_id,),
            )
            for run in runs
        }
    except psycopg.Error as error:
        reason = type(error).__name__
        for run in runs:
            for _ in range(ACTIVITY_MAX_ATTEMPTS):
                ledger.append(
                    LiveCallEntry(
                        budget_scope=BUDGET_SCOPE,
                        purpose=f"{run.purpose} (possible call; attempt rows unreadable)",
                        model_id=run.model_id,
                        is_production_model=run.model_id == production_model,
                        endpoint=RESPONSES_ENDPOINT,
                        outcome=CallOutcome.FAILED,
                        reserved_nano_usd=0 if run.free else run.reserved_nano_usd,
                        estimated_cost_nano_usd=0 if run.free else None,
                        error_type=f"attempts_unreadable:{reason}",
                        notes=json.dumps({"run_id": run.run_id}),
                    )
                )
        return
    for run in runs:
        for attempt in attempts[run.run_id]:
            ledger.append(_attempt_entry(run, attempt, production_model))


def run_live_check(
    spike: SpikeStack,
    ledger: Ledger,
    *,
    api_key: SecretStr,
    model_id: str,
    production_model: str,
    log_dir: Path,
    run_timeout_s: float = RUN_TIMEOUT_S,
    worker_overrides: Mapping[str, str] | None = None,
    markdown_path: Path = MARKDOWN_PATH,
) -> list[Finding]:
    """Run both checks on an already started stack and return the leak-scan findings.

    Every activity attempt is ledgered before this returns or raises, so the caller can
    remove the stack (and its attempt rows) afterwards without losing live calls.
    """
    reserved = reserve_worker_calls(ledger, model_id, is_production=model_id == production_model)
    store = AppStore(spike.app_url, keyring_from_file(spike.master_key_file))
    store.install_schema()
    sentinel = f"PRIVATE-SENTINEL-{secrets.token_hex(8)}"
    private_text = (
        f"Synthetic CV, not a real person ({sentinel}): I supervise warehouse shifts "
        "in Leeds and enjoy training new starters."
    )
    # No fixed prefix: every 12-character window must be secret material, or the fragment
    # scan matches public names such as the DBOS app version.
    fake_key = SecretStr(secrets.token_urlsafe(32))
    real_ws, fake_ws = str(uuid.uuid4()), str(uuid.uuid4())
    real_run = store.submit_run(real_ws, store.store_credential(real_ws, api_key), private_text)
    fake_run = store.submit_run(fake_ws, store.store_credential(fake_ws, fake_key), private_text)
    ledgered = [
        LedgeredRun(
            real_run.run_id,
            "schema output inside DBOS activity (key opened just in time)",
            model_id,
            reserved,
            free=False,
        ),
        LedgeredRun(fake_run.run_id, "invalid key inside DBOS activity", model_id, 0, free=True),
    ]

    log = log_dir / "worker.log"
    worker = stack.start_worker(
        spike, log, **{"activity_model": model_id, **(worker_overrides or {})}
    )
    try:
        for entry in (real_run, fake_run):
            stack.wait_for(
                lambda e=entry: (  # type: ignore[misc]
                    stack.query(
                        spike.app_url, "SELECT status FROM runs WHERE run_id = %s", (e.run_id,)
                    )[0]["status"]
                    != "queued"
                ),
                timeout_s=run_timeout_s,
                what=f"run {entry.run_id}",
            )
        print("worker exit code:", worker.stop())
    finally:
        worker.kill_if_running()
        ledger_attempts(ledger, spike.app_url, ledgered, production_model=production_model)
        write_markdown(ledger, markdown_path)

    dbos_db = spike.superuser_url_for("nessa_spike_dbos")
    output_strings: list[str] = []
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
            proposal = ProfileProposal.model_validate_json(store.open_output(run["output_id"]))
            print("validated output (opened from sealed store):", proposal.model_dump())
            output_strings += [proposal.proposed_title, proposal.evidence_quote]

    needles = [
        Needle("real Meta key", api_key.get_secret_value(), fragment_length=12),
        Needle("invalid key", fake_key.get_secret_value(), fragment_length=12),
        Needle("private text", private_text, fragment_length=PRIVATE_TEXT_FRAGMENT),
        *(Needle("model output", text) for text in output_strings),
    ]
    cells = [
        *stack.database_cells(dbos_db),
        *stack.database_cells(spike.superuser_url_for("nessa_spike_app")),
        (log.name, log.read_text(encoding="utf-8")),
    ]
    findings = scan(cells, needles)
    print(f"\nleak scan: {len(cells)} rows/logs scanned, findings: {findings}")
    return findings


def main() -> None:
    settings = MetaSettings()
    with tempfile.TemporaryDirectory(prefix="nessa-spike-") as tmp:
        work = Path(tmp)
        try:
            spike = stack.start(work / "master.key")
            run_live_check(
                spike,
                Ledger(LEDGER_PATH),
                api_key=settings.api_key,
                model_id=settings.test_model,
                production_model=settings.production_model,
                log_dir=work,
            )
        finally:
            stack.stop()
            print("spike stack and volume removed")


if __name__ == "__main__":
    main()
