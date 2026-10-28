"""The worker loop's scheduling (fast: the outbox and DBOS are stubbed at the module edge).

B-M1: a reconciliation pass that fails must not be retried on every 0.2 s pass, which would
also starve the heartbeat; it waits its interval like a pass that succeeded."""

import time
from pathlib import Path

import pytest

from nessa.db import StoreUnavailableError
from nessa.identity import worker


def test_a_failing_reconciliation_waits_its_interval_and_the_heartbeat_continues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    attempts: list[float] = []

    def failing_reconcile(runtime: object) -> int:
        attempts.append(time.monotonic())
        raise StoreUnavailableError()

    monkeypatch.setattr(worker, "dispatch_outbox", lambda engine: 0)
    monkeypatch.setattr(worker, "reconcile_errored_runs", failing_reconcile)
    monkeypatch.setattr(worker, "HEARTBEAT_FILE", tmp_path / "heartbeat")

    before = time.monotonic()
    due = worker.loop_pass(None, None, next_reconcile=0.0)  # type: ignore[arg-type]
    after = worker.loop_pass(None, None, next_reconcile=due)  # type: ignore[arg-type]

    assert len(attempts) == 1
    assert due >= before + worker.RECONCILE_INTERVAL_S
    assert after == due
    assert (tmp_path / "heartbeat").exists()  # the second pass still reported health
