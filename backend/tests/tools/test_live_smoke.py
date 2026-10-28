"""The live smoke's caps refuse before any call, and every provider attempt is ledgered
(ruling R5). Offline: nothing here contacts Meta."""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from nessa.identity.meta import REQUEST_TIMEOUT_S
from nessa.identity.model_choice import ModelChoice
from tools.live_smoke import (
    MAX_CALLS,
    RUN_TIMEOUT_S,
    CapExceededError,
    ScopeBudget,
    SmokeSettings,
    authorise,
    ledger_attempts,
    ledger_possible_calls,
)
from tools.localenv import REPO_ROOT
from tools.usage_ledger import CallOutcome, Ledger, ScopeSpend

ROOMY = ScopeBudget("live-smoke", max_calls=99, max_production_calls=99, max_cost_nano_usd=10**12)
NOTHING_SPENT = ScopeSpend(0, 0, 0)


@pytest.mark.req("MODEL-09")
def test_the_test_model_fits_the_cap_and_is_not_a_production_call() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    model_id, worst_case = authorise(models, production=False, budget=ROOMY, spent=NOTHING_SPENT)

    assert model_id == "muse-spark-1.3-contributor"
    assert worst_case == MAX_CALLS * 809_600  # 4,000 in x $0.10/M + 2,048 out x $0.20/M


@pytest.mark.req("MODEL-09")
def test_a_production_model_configured_as_the_test_model_needs_the_explicit_flag() -> None:
    models = ModelChoice.configure("muse-spark-1.3", "muse-spark-1.3", "test")

    with pytest.raises(CapExceededError, match="--production-model"):
        authorise(models, production=False, budget=ROOMY, spent=NOTHING_SPENT)
    assert authorise(models, production=True, budget=ROOMY, spent=NOTHING_SPENT)[0] == (
        "muse-spark-1.3"
    )


@pytest.mark.req("MODEL-09")
@pytest.mark.parametrize(
    ("value", "production"),
    [("1", True), ("0", False), ("false", False), ("yes", False), ("", False)],
)
def test_only_production_equals_one_opts_in_to_the_production_model(
    value: str, production: bool
) -> None:
    dry_run = subprocess.run(  # noqa: S603 - fixed make dry run, nothing executes
        ["make", "-n", "live-smoke", f"PRODUCTION={value}"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

    assert ("--production-model" in dry_run.stdout) is production


@pytest.mark.req("MODEL-09")
def test_a_model_whose_worst_case_breaks_the_cost_cap_is_refused() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-wonder-1.0", "test")

    with pytest.raises(CapExceededError, match="exceeds the cap"):
        authorise(models, production=True, budget=ROOMY, spent=NOTHING_SPENT)


@pytest.mark.req("MODEL-09")
@pytest.mark.parametrize(
    ("spent", "production", "refusal"),
    [
        (ScopeSpend(7, 0, 0), False, "of 9 calls used"),
        (ScopeSpend(1, 1, 0), True, "of 3 production calls used"),
        (ScopeSpend(1, 0, 298_000_000), False, "committed"),
    ],
)
def test_the_scope_s_cumulative_budget_refuses_once_the_next_invocation_would_breach_it(
    spent: ScopeSpend, production: bool, refusal: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key")
    budget = SmokeSettings(_env_file=None).budget()  # the conservative defaults
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    with pytest.raises(CapExceededError, match=refusal):
        authorise(models, production=production, budget=budget, spent=spent)
    assert authorise(models, production=production, budget=budget, spent=NOTHING_SPENT)


def test_the_smoke_waits_out_the_run_s_worst_case() -> None:
    # Three attempts that each time out, plus the step's 1 s and 2 s backoff.
    assert RUN_TIMEOUT_S > MAX_CALLS * REQUEST_TIMEOUT_S + 3


def attempt(**values: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "attempt_id": 1,
        "run_id": "run-1",
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

    seqs = ledger_attempts(ledger, attempts, scope="live-smoke", production_model="muse-spark-1.3")

    records = ledger.records()
    assert seqs == [1, 2]
    assert [r.outcome for r in records] == [CallOutcome.FAILED, CallOutcome.OK]
    assert records[0].estimated_cost_nano_usd is None  # unknown, never zero
    assert records[1].estimated_cost_nano_usd == 40_000
    assert not any(r.is_production_model for r in records)


@pytest.mark.req("MODEL-09")
def test_unreadable_attempts_are_ledgered_as_every_possible_call_with_unknown_cost(
    tmp_path: Path,
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    seqs = ledger_possible_calls(
        ledger, "muse-spark-1.3-contributor", 809_600, models, scope="live-smoke"
    )

    records = ledger.records()
    assert len(seqs) == MAX_CALLS
    assert all(r.estimated_cost_nano_usd is None for r in records)
    assert all(r.reserved_nano_usd == 809_600 for r in records)
