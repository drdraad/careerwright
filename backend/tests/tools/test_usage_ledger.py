"""The R5 usage ledger (ported from the Sprint 0 spike)."""

from pathlib import Path

import pytest

from tools.usage_ledger import CallOutcome, Ledger, LedgerBusyError, LiveCallEntry, ScopeSpend


def entry(**overrides: object) -> LiveCallEntry:
    values: dict[str, object] = {
        "budget_scope": "live-smoke",
        "purpose": "connection check",
        "model_id": "muse-spark-1.3-contributor",
        "is_production_model": False,
        "endpoint": "POST /v1/responses",
        "outcome": CallOutcome.OK,
        "reserved_nano_usd": 1_000_000,
        "estimated_cost_nano_usd": 100_000,
        "input_tokens": 500,
        "cached_input_tokens": 0,
        "output_tokens": 250,
    }
    values.update(overrides)
    return LiveCallEntry.model_validate(values)


def test_append_assigns_sequence_and_persists(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")

    first = ledger.append(entry())
    second = ledger.append(entry(purpose="streaming"))

    assert (first.seq, second.seq) == (1, 2)
    assert [r.purpose for r in Ledger(tmp_path / "live-usage.jsonl").records()] == [
        "connection check",
        "streaming",
    ]


def test_markdown_shows_running_total_and_marks_unknown_cost(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(estimated_cost_nano_usd=1_000_000))
    ledger.append(entry(estimated_cost_nano_usd=None, outcome=CallOutcome.FAILED))
    ledger.append(entry(estimated_cost_nano_usd=2_500_000))

    table = ledger.render_markdown_table()

    assert "unknown" in table
    # Running total after call 3 is $0.0035 known, flagged incomplete because call 2 is unknown.
    assert "$0.003500 + unknown" in table


def test_failed_calls_show_whatever_status_and_error_are_known(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(outcome=CallOutcome.FAILED, http_status=401, error_type="invalid_api_key"))
    ledger.append(entry(outcome=CallOutcome.FAILED))

    table = ledger.render_markdown_table()

    assert "| failed (401 invalid_api_key) |" in table
    assert "| failed (no detail) |" in table


def test_the_committed_ledger_still_parses(tmp_path: Path) -> None:
    # The Sprint 0 rows must stay readable by the promoted ledger.
    records = Ledger().records()

    assert records
    assert [r.seq for r in records] == list(range(1, len(records) + 1))


@pytest.mark.req("MODEL-09")
def test_a_scope_s_spend_counts_its_calls_and_every_unknown_cost_at_its_reservation(
    tmp_path: Path,
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(estimated_cost_nano_usd=100_000))
    ledger.append(entry(estimated_cost_nano_usd=None, is_production_model=True))
    ledger.append(entry(budget_scope="task-1-sprint-0", estimated_cost_nano_usd=5_000_000))

    assert ledger.spent("live-smoke") == ScopeSpend(
        calls=2, production_calls=1, committed_nano_usd=100_000 + 1_000_000
    )
    assert ledger.spent("unused") == ScopeSpend(0, 0, 0)


@pytest.mark.req("MODEL-09")
def test_a_row_for_an_attempt_with_a_repair_counts_both_requests(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(http_requests=2, is_production_model=True))
    ledger.append(entry())

    assert ledger.spent("live-smoke").calls == 3
    assert ledger.spent("live-smoke").production_calls == 2
    assert "POST /v1/responses x 2" in ledger.render_markdown_table()


def test_the_markdown_is_written_next_to_its_ledger(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry())

    ledger.write_markdown()

    assert "| 1 |" in (tmp_path / "live-usage.md").read_text(encoding="utf-8")


@pytest.mark.req("MODEL-09")
def test_one_live_invocation_holds_the_ledger_at_a_time(tmp_path: Path) -> None:
    path = tmp_path / "live-usage.jsonl"

    with Ledger(path).exclusive():
        with pytest.raises(LedgerBusyError), Ledger(path).exclusive():
            pass
        Ledger(path).append(entry())  # appends inside the holder's own run still work

    with Ledger(path).exclusive():  # released: the next invocation may proceed
        pass
    assert len(Ledger(path).records()) == 1
