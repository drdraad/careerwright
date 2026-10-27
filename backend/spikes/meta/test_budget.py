import pytest

from spikes.meta.budget import (
    BudgetExceededError,
    BudgetPolicy,
    CallPlan,
    SpentSoFar,
    authorise_call,
)

POLICY = BudgetPolicy(max_calls=3, max_production_calls=1, max_cost_nano_usd=10_000_000)


def plan(*, production: bool = False, worst_case: int = 1_000_000) -> CallPlan:
    return CallPlan(is_production_model=production, worst_case_nano_usd=worst_case)


def test_call_within_every_cap_is_authorised() -> None:
    spent = SpentSoFar(calls=1, production_calls=0, committed_nano_usd=2_000_000)

    authorise_call(POLICY, spent, plan())


def test_call_count_cap_includes_free_calls() -> None:
    spent = SpentSoFar(calls=3, production_calls=0, committed_nano_usd=0)

    with pytest.raises(BudgetExceededError, match="call cap"):
        authorise_call(POLICY, spent, plan(worst_case=0))


def test_production_model_has_its_own_cap() -> None:
    spent = SpentSoFar(calls=1, production_calls=1, committed_nano_usd=0)

    with pytest.raises(BudgetExceededError, match="production"):
        authorise_call(POLICY, spent, plan(production=True))


def test_test_model_call_is_not_limited_by_production_cap() -> None:
    spent = SpentSoFar(calls=1, production_calls=1, committed_nano_usd=0)

    authorise_call(POLICY, spent, plan(production=False))


def test_worst_case_reservation_must_fit_remaining_cost_budget() -> None:
    spent = SpentSoFar(calls=0, production_calls=0, committed_nano_usd=9_500_000)

    with pytest.raises(BudgetExceededError, match="cost cap"):
        authorise_call(POLICY, spent, plan(worst_case=500_001))


def test_reservation_exactly_at_cost_cap_is_allowed() -> None:
    spent = SpentSoFar(calls=0, production_calls=0, committed_nano_usd=9_500_000)

    authorise_call(POLICY, spent, plan(worst_case=500_000))
