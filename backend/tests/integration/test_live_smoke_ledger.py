"""B-I1: `make live-smoke` ledgers every call that reached the provider, including calls
made after the client stopped waiting for the run (ruling R5). Offline: the smoke's own
orchestration (`tools.live_smoke.smoke`) drives the real API and a real worker process whose
fake model fails every call and logs each one; nothing contacts Meta."""

import secrets
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from nessa.identity import connection_check
from nessa.identity.model_choice import ModelChoice
from tests.support.client import ApiClient
from tests.support.fake_models import FakeFailure
from tests.support.infra import WEB_ORIGIN, Infra, sign_in_seeded
from tests.support.workers import Worker, start_worker
from tools.live_smoke import MAX_CALLS, WorkerNotStoppedError, smoke
from tools.usage_ledger import Ledger

pytestmark = pytest.mark.integration
TEST_MODEL = "muse-spark-1.3-contributor"


@dataclass
class IntegrationTarget:
    infra: Infra
    http: TestClient
    worker: Worker
    web_origin: str = WEB_ORIGIN

    def sign_in(self) -> str:
        return sign_in_seeded("ada")

    def superuser_url(self, database: str) -> str:
        return self.infra.url("pg_superuser", database)

    def stop_worker(self) -> None:
        if self.worker.process.poll() is None:
            self.worker.stop()

    def logs(self) -> str:
        return self.worker.log_path.read_text(encoding="utf-8")


@dataclass
class UnstoppableTarget(IntegrationTarget):
    """The worker stop did not complete (`compose stop` failed, or Ctrl-C during it): the
    worker may still be calling."""

    failure: BaseException = field(
        default_factory=lambda: RuntimeError("docker compose stop failed (1)")
    )

    def stop_worker(self) -> None:
        raise self.failure


@pytest.fixture
def ledger(infra: Infra, tmp_path: Path) -> Iterator[Ledger]:
    yield Ledger(tmp_path / "live-usage.jsonl")
    # Smoke runs are left unfinished on purpose; keep later tests' workers from resuming them.
    for row in infra.query(
        "SELECT r.run_id FROM nessa.runs r JOIN nessa.workspaces w USING (workspace_id) "
        "WHERE w.name = 'Live smoke (synthetic)'"
    ):
        infra.query(
            "UPDATE dbos.workflow_status SET status = 'CANCELLED' "
            "WHERE workflow_uuid = %s AND status = 'PENDING'",
            (f"nessa-run-{row['run_id']}",),
            database="nessa_dbos",
        )


@pytest.mark.req("MODEL-09")
def test_every_call_the_worker_made_is_ledgered_even_after_the_poll_gave_up(
    infra: Infra, api: ApiClient, ledger: Ledger, tmp_path: Path
) -> None:
    calls = tmp_path / "calls.log"
    worker = start_worker(
        infra,
        tmp_path / "worker.log",
        fake_failure=FakeFailure.ALWAYS_UNAVAILABLE.value,
        fake_delay_s="1",
        call_log=str(calls),
    )
    models = ModelChoice.configure(TEST_MODEL, "muse-spark-1.3", "test")
    try:
        result = smoke(
            IntegrationTarget(infra, api.http, worker),
            SecretStr(f"sk-smoke-{secrets.token_urlsafe(32)}"),
            model_id=TEST_MODEL,
            worst_case=MAX_CALLS * connection_check.worst_case_nano_usd(TEST_MODEL),
            models=models,
            ledger=ledger,
            scope="integration-smoke",
            run_timeout_s=0.5,  # gives up while the run is still retrying
        )
        time.sleep(6)  # a slow teardown: long enough for every remaining retry to start
    finally:
        worker.kill_if_running()

    made = calls.read_text(encoding="utf-8").splitlines()
    records = ledger.records()
    assert result.status in ("queued", "running")
    assert made
    # A reservation is recorded before its call, so the ledger may only over-count.
    assert len(records) >= len(made)
    assert all(r.budget_scope == "integration-smoke" for r in records)
    assert all(r.estimated_cost_nano_usd is None for r in records)  # failed: cost unknown
    assert result.findings == []


@pytest.mark.req("MODEL-09")
@pytest.mark.parametrize(
    ("failure", "raised"),
    [
        (RuntimeError("docker compose stop failed (1)"), WorkerNotStoppedError),
        (KeyboardInterrupt(), KeyboardInterrupt),  # M1: Ctrl-C while `compose stop` runs
    ],
)
def test_a_worker_that_cannot_be_stopped_still_leaves_every_possible_call_ledgered(
    infra: Infra,
    api: ApiClient,
    ledger: Ledger,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    failure: BaseException,
    raised: type[BaseException],
) -> None:
    """N1, M1: the attempts are read and ledgered anyway, and every call the run could still
    make (the workspace's limits allow MAX_CALLS) is ledgered with an unknown cost, before
    the failure (or the interrupt) propagates. M2: a failed stop still gets its leak scan."""
    calls = tmp_path / "calls.log"
    worker = start_worker(
        infra,
        tmp_path / "worker.log",
        fake_failure=FakeFailure.ALWAYS_UNAVAILABLE.value,
        fake_delay_s="1",
        call_log=str(calls),
    )
    models = ModelChoice.configure(TEST_MODEL, "muse-spark-1.3", "test")
    try:
        with pytest.raises(raised) as stopped:
            smoke(
                UnstoppableTarget(infra, api.http, worker, failure=failure),
                SecretStr(f"sk-smoke-{secrets.token_urlsafe(32)}"),
                model_id=TEST_MODEL,
                worst_case=MAX_CALLS * connection_check.worst_case_nano_usd(TEST_MODEL),
                models=models,
                ledger=ledger,
                scope="integration-smoke",
                run_timeout_s=0.5,
            )
        time.sleep(8)  # the unstopped worker makes every call its limits allow
    finally:
        worker.kill_if_running()

    made = calls.read_text(encoding="utf-8").splitlines()
    records = ledger.records()
    assert len(records) == MAX_CALLS >= len(made) >= 1
    assert any("worker not confirmed stopped" in r.purpose for r in records)
    assert all(r.budget_scope == "integration-smoke" for r in records)
    if raised is WorkerNotStoppedError:
        assert "leak scan: " in capsys.readouterr().out
        assert "leak scan findings: []" in str(stopped.value)
