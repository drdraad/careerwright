"""Server-side spend reservation (spec section 16, MODEL-08). Costs are integer nano-USD."""

from datetime import UTC, date, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nessa.config import ApiSettings
from nessa.identity.activity import ACTIVITY_MAX_ATTEMPTS
from nessa.identity.records import RunKind
from nessa.identity.spend import (
    BudgetScope,
    SpendLimits,
    SpendState,
    committed_cost,
    period_start,
    refused_scope,
)
from nessa.worker import TASKS

LIMITS = SpendLimits(run_limit_nano_usd=1_000, period_limit_nano_usd=5_000)


def test_a_reservation_within_both_limits_is_allowed() -> None:
    assert refused_scope(LIMITS, period_committed=3_000, run_committed=0, worst_case=1_000) is None


@pytest.mark.req("MODEL-08")
def test_the_run_limit_refuses_a_call_that_would_exceed_it() -> None:
    assert refused_scope(LIMITS, period_committed=0, run_committed=500, worst_case=501) is (
        BudgetScope.RUN
    )


@pytest.mark.req("MODEL-08")
def test_the_period_limit_refuses_a_call_that_would_exceed_it() -> None:
    assert refused_scope(LIMITS, period_committed=4_500, run_committed=0, worst_case=501) is (
        BudgetScope.PERIOD
    )


def test_a_reservation_exactly_at_a_limit_is_allowed() -> None:
    assert refused_scope(LIMITS, period_committed=4_000, run_committed=0, worst_case=1_000) is None


@pytest.mark.req("MODEL-08")
@pytest.mark.parametrize(
    ("state", "cost", "expected"),
    [
        (SpendState.RECONCILED, 120, 120),
        (SpendState.HELD, None, 900),  # a call may be in flight: its worst case counts
        (SpendState.UNKNOWN, None, 900),  # ambiguous charge: never zero, the reservation stays
        (SpendState.NONE, None, 0),  # no provider call was made
    ],
)
def test_committed_cost_by_spend_state(state: SpendState, cost: int | None, expected: int) -> None:
    assert committed_cost(state, reserved_nano_usd=900, cost_nano_usd=cost) == expected


def test_a_reconciled_attempt_must_have_a_known_cost() -> None:
    with pytest.raises(ValueError, match="cost"):
        committed_cost(SpendState.RECONCILED, reserved_nano_usd=900, cost_nano_usd=None)


def test_the_spend_period_is_the_utc_calendar_month() -> None:
    assert period_start(datetime(2026, 10, 31, 23, 59, tzinfo=UTC)) == date(2026, 10, 1)
    assert period_start(datetime(2026, 11, 1, 0, 0, tzinfo=UTC)) == date(2026, 11, 1)


def test_limits_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="negative"):
        SpendLimits(run_limit_nano_usd=-1, period_limit_nano_usd=0)


@pytest.mark.req("MODEL-04", "MODEL-08")
@pytest.mark.parametrize("kind", list(TASKS))
def test_the_default_run_limit_fits_every_step_retry_on_the_production_model(
    kind: RunKind,
) -> None:
    # Retried attempts that fail without usage each keep their full reservation; if they
    # did not all fit, a provider outage would be reported as an exceeded budget.
    default = ApiSettings.model_fields["default_run_spend_limit_nano_usd"].default
    production = ApiSettings.model_fields["meta_production_model"].default
    worst_case = TASKS[kind].worst_case_nano_usd(production)

    assert ACTIVITY_MAX_ATTEMPTS * worst_case <= default


@given(
    st.integers(0, 10_000), st.integers(0, 10_000), st.integers(0, 10_000), st.integers(0, 10_000)
)
def test_an_allowed_reservation_never_takes_committed_spend_past_a_limit(
    period: int, run: int, worst: int, extra: int
) -> None:
    limits = SpendLimits(run_limit_nano_usd=run + extra, period_limit_nano_usd=period + extra)

    if refused_scope(limits, period_committed=period, run_committed=run, worst_case=worst) is None:
        assert period + worst <= limits.period_limit_nano_usd
        assert run + worst <= limits.run_limit_nano_usd
