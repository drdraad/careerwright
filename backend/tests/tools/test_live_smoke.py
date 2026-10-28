"""The live smoke's caps refuse before any call, and every provider attempt is ledgered
(ruling R5). Offline: nothing here contacts Meta."""

from pathlib import Path
from typing import Any

import pytest

from nessa.identity.model_choice import ModelChoice
from tools.live_smoke import MAX_CALLS, CapExceededError, authorise, ledger_attempts
from tools.usage_ledger import CallOutcome, Ledger


@pytest.mark.req("MODEL-09")
def test_the_test_model_fits_the_cap_and_is_not_a_production_call() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    model_id, worst_case = authorise(models, production=False)

    assert model_id == "muse-spark-1.3-contributor"
    assert worst_case == MAX_CALLS * 809_600  # 4,000 in x $0.10/M + 2,048 out x $0.20/M


@pytest.mark.req("MODEL-09")
def test_a_production_model_configured_as_the_test_model_needs_the_explicit_flag() -> None:
    models = ModelChoice.configure("muse-spark-1.3", "muse-spark-1.3", "test")

    with pytest.raises(CapExceededError, match="--production-model"):
        authorise(models, production=False)
    assert authorise(models, production=True)[0] == "muse-spark-1.3"


@pytest.mark.req("MODEL-09")
def test_a_model_whose_worst_case_breaks_the_cost_cap_is_refused() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-wonder-1.0", "test")

    with pytest.raises(CapExceededError, match="exceeds the cap"):
        authorise(models, production=True)


def attempt(**values: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "attempt_id": 1,
        "model_id": "muse-spark-1.3-contributor",
        "outcome": "succeeded",
        "spend_state": "reconciled",
        "reserved_nano_usd": 809_600,
        "cost_nano_usd": 40_000,
        "input_tokens": 150,
        "cached_input_tokens": 0,
        "output_tokens": 120,
        "reasoning_tokens": 80,
        "web_search_queries": 0,
        "provider_response_id": "resp_x",
    }
    return base | values


@pytest.mark.req("MODEL-09")
def test_every_attempt_that_reached_meta_is_ledgered_and_unknown_stays_unknown(
    tmp_path: Path,
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    attempts = [
        attempt(attempt_id=1, outcome="interrupted", spend_state="unknown", cost_nano_usd=None),
        attempt(attempt_id=2, outcome="credential_unavailable", spend_state="none"),
        attempt(attempt_id=3),
    ]

    seqs = ledger_attempts(ledger, attempts, "run-1", production_model="muse-spark-1.3")

    records = ledger.records()
    assert seqs == [1, 2]
    assert [r.outcome for r in records] == [CallOutcome.FAILED, CallOutcome.OK]
    assert records[0].estimated_cost_nano_usd is None  # unknown, never zero
    assert records[1].estimated_cost_nano_usd == 40_000
    assert not any(r.is_production_model for r in records)
