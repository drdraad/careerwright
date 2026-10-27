"""S0.3/S0.4 durability and journal-privacy evidence against real PostgreSQL 16 and DBOS.

Run: `uv run pytest -m integration spikes/durable -v` (starts and removes the spike container).
Every scenario ends by scanning both databases and the worker logs for the credential and
the private text. Workers are real processes; "kill" is SIGKILL.
"""

import json
import os
import secrets
import signal
import subprocess
import sys
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr

from spikes.durable import stack
from spikes.durable.leak_scan import Finding, Needle, scan
from spikes.durable.live_run import PRIVATE_TEXT_FRAGMENT, run_live_check
from spikes.durable.models import FAKE_MODEL_ID, FakeFailure
from spikes.durable.stack import SpikeStack, Worker, query, start_worker, wait_for
from spikes.durable.store import AppStore, OutboxEntry
from spikes.durable.worker import keyring_from_file
from spikes.durable.workflow import ACTIVITY_MAX_ATTEMPTS, ProfileProposal
from spikes.meta.ledger import Ledger
from spikes.meta.live_spike import BUDGET_SCOPE

pytestmark = pytest.mark.integration

RUN_TIMEOUT_S = 60.0


@pytest.fixture(scope="session")
def spike(tmp_path_factory: pytest.TempPathFactory) -> Iterator[SpikeStack]:
    try:
        started = stack.start(tmp_path_factory.mktemp("keys") / "master.key")
        AppStore(started.app_url, keyring_from_file(started.master_key_file)).install_schema()
        yield started
    finally:
        stack.stop()


@dataclass
class Scenario:
    spike: SpikeStack
    store: AppStore
    workspace_id: str
    credential_id: str
    api_key: SecretStr
    private_text: str
    sentinel: str
    # Only in the prompt's second line, which the fake model never echoes.
    prompt_only_sentinel: str
    log_dir: Path
    logs: list[Path] = field(default_factory=list)
    workers: list[Worker] = field(default_factory=list)

    def submit(self) -> OutboxEntry:
        return self.store.submit_run(self.workspace_id, self.credential_id, self.private_text)

    def worker(self, name: str, **settings: str) -> Worker:
        log = self.log_dir / f"{name}.log"
        self.logs.append(log)
        worker = start_worker(self.spike, log, **settings)
        self.workers.append(worker)
        return worker

    def run(self, run_id: str) -> dict[str, Any]:
        return query(self.spike.app_url, "SELECT * FROM runs WHERE run_id = %s", (run_id,))[0]

    def attempts(self, run_id: str) -> list[dict[str, Any]]:
        return query(
            self.spike.app_url,
            "SELECT * FROM activity_attempts WHERE run_id = %s ORDER BY attempt_id",
            (run_id,),
        )

    def outputs(self, run_id: str) -> list[dict[str, Any]]:
        return query(self.spike.app_url, "SELECT * FROM run_outputs WHERE run_id = %s", (run_id,))

    def wait_terminal(self, run_id: str) -> dict[str, Any]:
        wait_for(
            lambda: self.run(run_id)["status"] != "queued", timeout_s=RUN_TIMEOUT_S, what="run"
        )
        return self.run(run_id)

    def journal(self, workflow_id: str) -> dict[str, Any]:
        dbos_db = self.spike.superuser_url_for("nessa_spike_dbos")
        status = query(
            dbos_db, "SELECT * FROM dbos.workflow_status WHERE workflow_uuid = %s", (workflow_id,)
        )
        inputs = query(
            dbos_db,
            "SELECT inputs FROM dbos.workflow_input WHERE workflow_uuid = %s",
            (workflow_id,),
        )
        output = query(
            dbos_db,
            "SELECT output, error FROM dbos.workflow_output WHERE workflow_uuid = %s",
            (workflow_id,),
        )
        steps = query(
            dbos_db,
            "SELECT function_name, output, error FROM dbos.operation_outputs "
            "WHERE workflow_uuid = %s ORDER BY function_id",
            (workflow_id,),
        )
        return {"status": status, "inputs": inputs, "output": output, "steps": steps}

    def leaks(self) -> list[Finding]:
        needles = [
            Needle("credential", self.api_key.get_secret_value(), fragment_length=12),
            Needle("private text", self.sentinel),
            Needle("prompt-only private text", self.prompt_only_sentinel),
            Needle("private text window", self.private_text, fragment_length=PRIVATE_TEXT_FRAGMENT),
        ]
        cells = [
            *stack.database_cells(self.spike.superuser_url_for("nessa_spike_dbos")),
            *stack.database_cells(self.spike.superuser_url_for("nessa_spike_app")),
            *((log.name, log.read_text(encoding="utf-8")) for log in self.logs),
        ]
        return scan(cells, needles)


@pytest.fixture
def scenario(spike: SpikeStack, tmp_path: Path) -> Iterator[Scenario]:
    store = AppStore(spike.app_url, keyring_from_file(spike.master_key_file))
    workspace_id = str(uuid.uuid4())
    api_key = SecretStr("sk-spike-" + secrets.token_hex(16))
    sentinel = f"PRIVATE-SENTINEL-{secrets.token_hex(8)}"
    prompt_only_sentinel = f"PROMPT-ONLY-SENTINEL-{secrets.token_hex(8)}"
    started = Scenario(
        spike=spike,
        store=store,
        workspace_id=workspace_id,
        credential_id=store.store_credential(workspace_id, api_key),
        api_key=api_key,
        private_text=(
            f"Synthetic CV: I coach new starters ({sentinel}).\n"
            f"Unechoed detail: {prompt_only_sentinel}."
        ),
        sentinel=sentinel,
        prompt_only_sentinel=prompt_only_sentinel,
        log_dir=tmp_path,
    )
    yield started
    # A failed assertion must not leave a worker running against the session stack.
    for worker in started.workers:
        worker.kill_if_running()


def assert_identifier_only_journal(scenario: Scenario, entry: OutboxEntry) -> dict[str, Any]:
    journal = scenario.journal(entry.workflow_id)
    assert json.loads(journal["inputs"][0]["inputs"]) == {
        "positionalArgs": [entry.run_id],
        "namedArgs": {},
    }
    output: dict[str, Any] = json.loads(journal["output"][0]["output"])
    assert set(output) in ({"status", "output_id"}, {"status", "failure_class"})
    assert {s["function_name"] for s in journal["steps"]} <= {
        "nessa_spike.bounded_model_activity",
        "nessa_spike.publish_outcome",
    }
    return output


def test_worker_killed_mid_activity_recovers_to_one_accepted_output(scenario: Scenario) -> None:
    entry = scenario.submit()
    first = scenario.worker("first", fake_delay_s="30")
    wait_for(lambda: len(scenario.attempts(entry.run_id)) == 1, timeout_s=30, what="attempt")
    # Dispatch must already be recorded, so only DBOS recovery can finish this run.
    wait_for(lambda: not scenario.store.pending_outbox(), timeout_s=10, what="dispatch mark")
    first.kill()
    assert scenario.run(entry.run_id)["status"] == "queued"
    assert scenario.journal(entry.workflow_id)["status"][0]["status"] == "PENDING"

    second = scenario.worker("second")
    run = scenario.wait_terminal(entry.run_id)
    assert second.stop() == 0

    assert run["status"] == "succeeded"
    outputs = scenario.outputs(entry.run_id)
    assert len(outputs) == 1
    attempts = scenario.attempts(entry.run_id)
    assert [a["outcome"] for a in attempts] == [None, "succeeded"]
    journal_output = assert_identifier_only_journal(scenario, entry)
    assert journal_output == {"status": "succeeded", "output_id": str(run["output_id"])}
    assert scenario.journal(entry.workflow_id)["status"][0]["status"] == "SUCCESS"
    proposal = ProfileProposal.model_validate_json(
        scenario.store.open_output(journal_output["output_id"])
    )
    assert scenario.sentinel in proposal.evidence_quote  # private content exists, sealed
    assert scenario.leaks() == []


def test_worker_killed_after_output_persisted_keeps_first_accepted_output(
    scenario: Scenario,
) -> None:
    entry = scenario.submit()
    first = scenario.worker("first", crash_at="after_output_persisted")
    assert first.wait_exit(RUN_TIMEOUT_S) == -signal.SIGKILL
    [accepted] = scenario.outputs(entry.run_id)

    second = scenario.worker("second")
    run = scenario.wait_terminal(entry.run_id)
    second.stop()

    assert scenario.outputs(entry.run_id) == [accepted]  # same row, untouched
    assert run["output_id"] == accepted["output_id"]
    assert [a["outcome"] for a in scenario.attempts(entry.run_id)] == [None, "reused_accepted"]
    assert assert_identifier_only_journal(scenario, entry)["output_id"] == str(
        accepted["output_id"]
    )
    assert scenario.leaks() == []


def test_outbox_replay_after_dispatch_crash_starts_one_workflow(scenario: Scenario) -> None:
    entry = scenario.submit()
    first = scenario.worker("first", crash_at="after_dispatch_before_mark", fake_delay_s="1")
    assert first.wait_exit(RUN_TIMEOUT_S) == -signal.SIGKILL
    outbox = query(
        scenario.spike.app_url, "SELECT * FROM outbox WHERE run_id = %s", (entry.run_id,)
    )
    assert outbox[0]["dispatched_at"] is None  # the crash lost the dispatch mark

    second = scenario.worker("second")
    run = scenario.wait_terminal(entry.run_id)
    wait_for(
        lambda: (
            query(
                scenario.spike.app_url,
                "SELECT dispatched_at FROM outbox WHERE run_id = %s",
                (entry.run_id,),
            )[0]["dispatched_at"]
            is not None
        ),
        timeout_s=10,
        what="outbox replay",
    )
    second.stop()

    assert run["status"] == "succeeded"
    assert len(scenario.journal(entry.workflow_id)["status"]) == 1
    workflows_for_run = query(
        scenario.spike.superuser_url_for("nessa_spike_dbos"),
        "SELECT workflow_uuid FROM dbos.workflow_input WHERE inputs LIKE %s",
        (f"%{entry.run_id}%",),
    )
    assert len(workflows_for_run) == 1
    assert len(scenario.outputs(entry.run_id)) == 1
    assert [a["outcome"] for a in scenario.attempts(entry.run_id)].count("succeeded") == 1
    assert scenario.leaks() == []


def test_replaying_a_completed_outbox_entry_has_no_effect(scenario: Scenario) -> None:
    entry = scenario.submit()
    first = scenario.worker("first")
    scenario.wait_terminal(entry.run_id)
    first.stop()
    attempts_before = scenario.attempts(entry.run_id)
    query_redeliver = "UPDATE outbox SET dispatched_at = NULL WHERE run_id = %s RETURNING outbox_id"
    assert query(scenario.spike.app_url, query_redeliver, (entry.run_id,))

    second = scenario.worker("second")
    wait_for(lambda: not scenario.store.pending_outbox(), timeout_s=10, what="redelivered entry")
    second.stop()

    assert scenario.attempts(entry.run_id) == attempts_before
    assert len(scenario.outputs(entry.run_id)) == 1
    assert len(scenario.journal(entry.workflow_id)["status"]) == 1
    assert scenario.leaks() == []


def test_transient_provider_error_is_retried_by_the_dbos_step_only(scenario: Scenario) -> None:
    entry = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.RATE_LIMIT_ONCE.value)
    run = scenario.wait_terminal(entry.run_id)
    worker.stop()

    assert run["status"] == "succeeded"
    assert [a["outcome"] for a in scenario.attempts(entry.run_id)] == ["transient_429", "succeeded"]
    assert len(scenario.outputs(entry.run_id)) == 1
    # The provider body echoed 20 characters of the key; none of it may be persisted or logged.
    assert scenario.leaks() == []


def test_exhausted_retries_fail_visibly_not_as_empty_success(scenario: Scenario) -> None:
    entry = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.ALWAYS_UNAVAILABLE.value)
    run = scenario.wait_terminal(entry.run_id)
    worker.stop()

    assert (run["status"], run["failure_class"], run["output_id"]) == (
        "failed",
        "provider_unavailable",
        None,
    )
    assert len(scenario.attempts(entry.run_id)) == ACTIVITY_MAX_ATTEMPTS
    assert scenario.outputs(entry.run_id) == []
    assert assert_identifier_only_journal(scenario, entry) == {
        "status": "failed",
        "failure_class": "provider_unavailable",
    }
    assert scenario.leaks() == []


def test_provider_error_echoing_the_key_is_not_journalled(scenario: Scenario) -> None:
    entry = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.AUTH_ECHO.value)
    run = scenario.wait_terminal(entry.run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "provider_authentication")
    assert [a["outcome"] for a in scenario.attempts(entry.run_id)] == ["provider_authentication"]
    assert_identifier_only_journal(scenario, entry)
    assert scenario.leaks() == []


def test_connection_errors_are_retried_then_fail_visibly(scenario: Scenario) -> None:
    entry = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.CONNECTION_ERROR.value)
    run = scenario.wait_terminal(entry.run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "provider_unavailable")
    outcomes = [a["outcome"] for a in scenario.attempts(entry.run_id)]
    assert outcomes == ["transient_connection"] * ACTIVITY_MAX_ATTEMPTS
    assert assert_identifier_only_journal(scenario, entry) == {
        "status": "failed",
        "failure_class": "provider_unavailable",
    }
    # The connection error's message echoed the key; it must not reach the journal or logs.
    assert scenario.leaks() == []


def test_unexpected_error_fails_typed_without_its_message(scenario: Scenario) -> None:
    entry = scenario.submit()
    worker = scenario.worker("worker", fake_failure=FakeFailure.UNEXPECTED_ERROR.value)
    run = scenario.wait_terminal(entry.run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "unknown_failure")
    [attempt] = scenario.attempts(entry.run_id)
    assert attempt["outcome"] == "unknown_failure:RuntimeError"
    assert attempt["finished_at"] is not None
    assert assert_identifier_only_journal(scenario, entry) == {
        "status": "failed",
        "failure_class": "unknown_failure",
    }
    journal = scenario.journal(entry.workflow_id)
    assert journal["status"][0]["status"] == "SUCCESS"
    assert [step["error"] for step in journal["steps"]] == [None, None]
    # The RuntimeError quoted the key and the private input; only its class name may persist.
    assert scenario.leaks() == []


def test_revoked_credential_stops_before_any_model_call(scenario: Scenario) -> None:
    scenario.store.revoke_credential(scenario.credential_id)
    entry = scenario.submit()
    worker = scenario.worker("worker")
    run = scenario.wait_terminal(entry.run_id)
    worker.stop()

    assert (run["status"], run["failure_class"]) == ("failed", "credential_unavailable")
    [attempt] = scenario.attempts(entry.run_id)
    assert (attempt["outcome"], attempt["input_tokens"]) == ("credential_unavailable", None)
    assert scenario.leaks() == []


def test_negative_control_durability_capability_journals_private_output(
    scenario: Scenario,
) -> None:
    entry = scenario.submit()
    # The probe processes this run itself; mark it so no later worker dispatches it again.
    scenario.store.mark_dispatched(entry.outbox_id)
    run_id = entry.run_id
    log = scenario.log_dir / "probe.log"
    scenario.logs.append(log)
    env = {
        **os.environ,
        "NESSA_SPIKE_APP_URL": scenario.spike.app_url,
        "NESSA_SPIKE_DBOS_URL": scenario.spike.dbos_url,
        "NESSA_SPIKE_MASTER_KEY_FILE": str(scenario.spike.master_key_file),
        "NESSA_SPIKE_PROBE_RUN_ID": run_id,
        "PYDANTIC_AI_NO_BANNER": "1",
    }
    with log.open("wb") as handle:
        subprocess.run(
            [sys.executable, "-m", "spikes.durable.capability_probe"],
            cwd=stack.BACKEND_DIR,
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=RUN_TIMEOUT_S,
        )

    findings = scenario.leaks()
    print("capability probe findings:", sorted({(f.location, f.needle_label) for f in findings}))
    assert ("dbos.operation_outputs", "private text") in {
        (f.location, f.needle_label) for f in findings
    }


def test_live_check_ledgers_every_attempt_even_when_the_run_fails(
    spike: SpikeStack, tmp_path: Path
) -> None:
    # Deliberately last: it leaves PENDING workflows behind for the session stack teardown.
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    newest = "SELECT coalesce(max(outbox_id), 0) AS newest FROM outbox"
    before = query(spike.app_url, newest)[0]["newest"]

    with pytest.raises(TimeoutError):
        run_live_check(
            spike,
            ledger,
            api_key=SecretStr("sk-spike-" + secrets.token_hex(16)),
            model_id="muse-spark-1.3-contributor",  # priced for the reservation; never contacted
            production_model="muse-spark-1.3",
            log_dir=tmp_path,
            run_timeout_s=10,
            worker_overrides={"activity_model": FAKE_MODEL_ID, "fake_delay_s": "60"},
            markdown_path=tmp_path / "live-usage.md",
        )

    attempts = query(  # attempts of the runs this live check submitted
        spike.app_url,
        "SELECT a.attempt_id FROM activity_attempts a JOIN outbox o USING (run_id) "
        "WHERE o.outbox_id > %s",
        (before,),
    )
    assert attempts  # calls were in flight when the run failed
    records = ledger.records()
    assert {json.loads(r.notes)["activity_attempt"] for r in records} == {
        a["attempt_id"] for a in attempts
    }
    paid = [r for r in records if r.reserved_nano_usd > 0]
    assert paid
    assert all(r.estimated_cost_nano_usd is None for r in paid)  # in flight: unknown, not zero
    assert ledger.spent(BUDGET_SCOPE).committed_nano_usd == sum(r.reserved_nano_usd for r in paid)
