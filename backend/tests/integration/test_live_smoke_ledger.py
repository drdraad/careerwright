"""B-I1: `make live-smoke` ledgers every call that reached the provider, including calls
made after the client stopped waiting for the run (ruling R5). Offline: the smoke's own
orchestration (`tools.live_smoke.smoke`) drives the real API and a real worker process whose
fake model fails every call and logs each one; nothing contacts Meta."""

import json
import secrets
import time
from collections.abc import Iterator
from dataclasses import dataclass
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
from tools.live_smoke import MAX_CALLS, smoke
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


@pytest.fixture
def ledger(infra: Infra, tmp_path: Path) -> Iterator[Ledger]:
    used = Ledger(tmp_path / "live-usage.jsonl")
    yield used
    # The smoke run is left unfinished on purpose; keep later tests' workers from resuming it.
    for record in used.records():
        run_id = json.loads(record.notes)["run_id"]
        infra.query(
            "UPDATE dbos.workflow_status SET status = 'CANCELLED' WHERE workflow_uuid = %s",
            (f"nessa-run-{run_id}",),
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
