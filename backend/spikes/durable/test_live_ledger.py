from pathlib import Path

from spikes.durable.live_run import LedgeredRun, ledger_attempts
from spikes.durable.workflow import ACTIVITY_MAX_ATTEMPTS
from spikes.meta.ledger import CallOutcome, Ledger
from spikes.meta.live_spike import BUDGET_SCOPE

UNREACHABLE_DB = "postgresql://nobody@127.0.0.1:1/none?connect_timeout=2"
RESERVED = 1_000_000


def test_unreadable_attempts_are_ledgered_as_worst_case_possible_calls(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    runs = [
        LedgeredRun("run-paid", "real key", "muse-spark-1.3-contributor", RESERVED, free=False),
        LedgeredRun("run-free", "invalid key", "muse-spark-1.3-contributor", 0, free=True),
    ]

    ledger_attempts(ledger, UNREACHABLE_DB, runs, production_model="muse-spark-1.3")

    records = ledger.records()
    assert len(records) == 2 * ACTIVITY_MAX_ATTEMPTS
    assert all(r.outcome is CallOutcome.FAILED for r in records)
    assert all((r.error_type or "").startswith("attempts_unreadable") for r in records)
    paid = [r for r in records if r.reserved_nano_usd == RESERVED]
    assert len(paid) == ACTIVITY_MAX_ATTEMPTS
    assert all(r.estimated_cost_nano_usd is None for r in paid)  # unknown, never zero
    spent = ledger.spent(BUDGET_SCOPE)
    assert spent.calls == 2 * ACTIVITY_MAX_ATTEMPTS
    assert spent.committed_nano_usd == ACTIVITY_MAX_ATTEMPTS * RESERVED


def test_production_model_attempts_count_against_the_production_cap(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    runs = [LedgeredRun("run", "real key", "muse-spark-1.3", RESERVED, free=False)]

    ledger_attempts(ledger, UNREACHABLE_DB, runs, production_model="muse-spark-1.3")

    assert ledger.spent(BUDGET_SCOPE).production_calls == ACTIVITY_MAX_ATTEMPTS
