from pathlib import Path

from spikes.meta.ledger import CallOutcome, Ledger, LiveCallEntry


def entry(**overrides: object) -> LiveCallEntry:
    values: dict[str, object] = {
        "budget_scope": "task-1",
        "purpose": "schema output",
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
        "schema output",
        "streaming",
    ]


def test_spent_counts_calls_production_calls_and_committed_cost(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(estimated_cost_nano_usd=0, reserved_nano_usd=0, outcome=CallOutcome.FAILED))
    ledger.append(entry(is_production_model=True, estimated_cost_nano_usd=2_000_000))
    ledger.append(entry(budget_scope="other-task", estimated_cost_nano_usd=7_000_000))

    spent = ledger.spent("task-1")

    assert (spent.calls, spent.production_calls, spent.committed_nano_usd) == (2, 1, 2_000_000)


def test_unknown_cost_commits_its_full_reservation(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(estimated_cost_nano_usd=None, reserved_nano_usd=4_000_000))

    assert ledger.spent("task-1").committed_nano_usd == 4_000_000


def test_markdown_shows_running_total_and_marks_unknown_cost(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(estimated_cost_nano_usd=1_000_000))
    ledger.append(entry(estimated_cost_nano_usd=None, outcome=CallOutcome.FAILED))
    ledger.append(entry(estimated_cost_nano_usd=2_500_000))

    rows = [line for line in ledger.render_markdown_table().splitlines() if line.startswith("| 1")]
    table = ledger.render_markdown_table()

    assert len(rows) == 1
    assert "unknown" in table
    # Running total after call 3 is $0.0035 known, flagged as incomplete because call 2 is unknown.
    assert "$0.003500 + unknown" in table


def test_failed_calls_show_whatever_status_and_error_are_known(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(entry(outcome=CallOutcome.FAILED, http_status=401, error_type="invalid_api_key"))
    ledger.append(entry(outcome=CallOutcome.FAILED, error_type="ConnectError"))
    ledger.append(entry(outcome=CallOutcome.FAILED))

    table = ledger.render_markdown_table()

    assert "| failed (401 invalid_api_key) |" in table
    assert "| failed (ConnectError) |" in table
    assert "| failed (no detail) |" in table


def test_records_with_no_ledger_file_are_empty(tmp_path: Path) -> None:
    assert Ledger(tmp_path / "missing.jsonl").records() == []
