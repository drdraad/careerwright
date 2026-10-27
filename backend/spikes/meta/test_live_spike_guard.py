import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest

from spikes.meta.budget import BudgetExceededError
from spikes.meta.ledger import CallOutcome, Ledger
from spikes.meta.live_spike import POLICY, CallReport, run_guarded


class NetworkDownError(Exception):
    pass


def guarded(
    ledger: Ledger,
    tmp_path: Path,
    call: Callable[[], Awaitable[CallReport]],
    *,
    worst_case: int = 1_000,
) -> None:
    asyncio.run(
        run_guarded(
            ledger,
            purpose="probe",
            model_id="muse-spark-1.3-contributor",
            is_production=False,
            endpoint="POST /v1/responses",
            worst_case_nano_usd=worst_case,
            call=call,
            markdown_path=tmp_path / "live-usage.md",
        )
    )


def test_call_that_raises_is_still_logged_with_unknown_cost(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")

    async def network_down() -> CallReport:
        raise NetworkDownError

    with pytest.raises(NetworkDownError):
        guarded(ledger, tmp_path, network_down)

    [record] = ledger.records()
    assert (record.outcome, record.error_type) == (CallOutcome.FAILED, "NetworkDownError")
    assert record.estimated_cost_nano_usd is None
    assert ledger.spent("task-1-sprint-0").committed_nano_usd == 1_000


def test_refused_call_is_never_sent_or_logged(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    sent: list[bool] = []

    async def call() -> CallReport:
        sent.append(True)
        return CallReport(outcome=CallOutcome.OK)

    with pytest.raises(BudgetExceededError):
        guarded(ledger, tmp_path, call, worst_case=POLICY.max_cost_nano_usd + 1)

    assert sent == []
    assert ledger.records() == []
