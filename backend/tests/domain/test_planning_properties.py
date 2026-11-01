"""Generated properties of the checker's money and dates (plan section 7: Hypothesis for
money and dates; plan section 8, "Properties worth generating"). Every amount is integer
minor units; the ledgers obey their identities; relaxing a resource bound never makes a
feasible route infeasible; the order a route lists its actions in changes nothing."""

from datetime import timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from careerwright.planning.checker import FindingKind, RouteCheck, check_route
from careerwright.planning.compiler import PlanningInputs, ReceiptTiming, compile_input
from tests.support.planning import START, catalogue_of, option, person

AMOUNTS = st.integers(min_value=0, max_value=300_000)


@st.composite
def cases(draw: st.DrawFn) -> tuple[PlanningInputs, list[tuple]]:  # type: ignore[type-arg]
    horizon = draw(st.integers(min_value=1, max_value=6))
    inputs = person(
        horizon=horizon,
        opening=draw(st.integers(min_value=0, max_value=1_000_000)),
        living=draw(AMOUNTS),
        reserve=draw(st.integers(min_value=0, max_value=50_000)),
        pay=draw(AMOUNTS),
        hours=draw(st.integers(min_value=0, max_value=40)),
        availability=draw(st.integers(min_value=0, max_value=60)),
        baseline=draw(st.one_of(st.none(), AMOUNTS)),
        objective="direct_spending",
        timing=draw(st.sampled_from(ReceiptTiming)),
        direct_cap=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=500_000))),
        monthly_cap=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=200_000))),
    )
    options = []
    for name in ("a", "b"):
        first = draw(st.integers(min_value=0, max_value=horizon - 1))
        length = draw(st.integers(min_value=0, max_value=80))
        begins = START + timedelta(days=31 * first)
        payments = draw(
            st.lists(
                st.tuples(st.integers(min_value=0, max_value=horizon + 2), AMOUNTS), max_size=4
            )
        )
        options.append(
            option(
                name,
                start=begins,
                finish=begins + timedelta(days=length),
                hours=draw(st.integers(min_value=0, max_value=30)),
                payments=tuple(payments),
            )
        )
    return inputs, options


def run(inputs: PlanningInputs, options: list[tuple], route: list[str]) -> RouteCheck:  # type: ignore[type-arg]
    return check_route(compile_input(inputs, catalogue_of(*options)), route)


def known(value: int | None) -> int:
    """A ledger figure these cases always know: every amount and month is stated."""
    assert value is not None
    return value


@pytest.mark.req("TIME1-05", "FIN1-03", "FIN1-10")
@settings(max_examples=150, deadline=None)
@given(case=cases())
def test_the_ledgers_keep_their_identities_in_whole_minor_units(
    case: tuple[PlanningInputs, list[tuple]],  # type: ignore[type-arg]
) -> None:
    inputs, options = case
    result = run(inputs, options, ["a", "b"])
    cash = result.ledgers.liquidity.months
    opening = inputs.opening_cash_minor

    for month in cash:
        outflows = month.living_minor + known(month.payments_minor) + month.debt_service_minor
        lower, closing = known(month.lower_bound_minor), known(month.closing_minor)
        assert month.opening_minor == opening
        assert lower == opening + known(month.early_receipts_minor) - outflows
        assert closing == lower + known(month.later_receipts_minor)
        assert lower <= closing  # later receipts are never negative
        opening = closing
    direct = result.ledgers.direct
    assert result.direct_cost is not None
    assert result.direct_cost.minor_units == sum(
        known(m.payments_minor) for m in direct.months
    ) + sum(i.amount_minor for i in direct.beyond_horizon)
    if inputs.baseline is not None:
        assert result.economic_cost is not None
        months = result.ledgers.income.months
        baseline = inputs.baseline.net_income_by_month
        lost = sum(b - known(m.route_minor) for b, m in zip(baseline, months, strict=True))
        assert result.economic_cost.minor_units == result.direct_cost.minor_units + lost
    every = [*cash, *direct.months, *result.ledgers.income.months]
    assert all(
        isinstance(v, int) and not isinstance(v, bool)
        for row in every
        for v in row.model_dump().values()
        if not isinstance(v, str | type(None))
    )


@pytest.mark.req("PLN-06", "FIN1-06")
@settings(max_examples=150, deadline=None)
@given(case=cases(), more=st.integers(min_value=0, max_value=100_000))
def test_relaxing_a_limit_never_adds_a_violation(
    case: tuple[PlanningInputs, list[tuple]],  # type: ignore[type-arg]
    more: int,
) -> None:
    inputs, options = case
    availability = inputs.weekly_availability_by_month or []
    relaxed = inputs.model_copy(
        update={
            "direct_spend_cap_minor": (
                None
                if inputs.direct_spend_cap_minor is None
                else inputs.direct_spend_cap_minor + more
            ),
            "monthly_payment_cap_minor": (
                None
                if inputs.monthly_payment_cap_minor is None
                else inputs.monthly_payment_cap_minor + more
            ),
            "reserve_minor": (
                None if inputs.reserve_minor is None else max(0, inputs.reserve_minor - more)
            ),
            "opening_cash_minor": inputs.opening_cash_minor + more,
            "weekly_availability_by_month": [min(168, h + more % 20) for h in availability],
        }
    )

    def violations(result: RouteCheck) -> set[tuple[str, str | None]]:
        return {(f.code.value, f.month) for f in result.findings if f.kind is FindingKind.VIOLATION}

    assert violations(run(relaxed, options, ["a", "b"])) <= violations(
        run(inputs, options, ["a", "b"])
    )


@pytest.mark.req("PLN-03")
@settings(max_examples=100, deadline=None)
@given(case=cases())
def test_the_order_a_route_names_its_actions_in_changes_nothing(
    case: tuple[PlanningInputs, list[tuple]],  # type: ignore[type-arg]
) -> None:
    inputs, options = case
    forward, backward = run(inputs, options, ["a", "b"]), run(inputs, options, ["b", "a"])

    def key(result: RouteCheck) -> object:
        return (
            result.feasibility,
            sorted((f.code.value, f.month or "", f.amount or 0) for f in result.findings),
            result.direct_cost,
            result.economic_cost,
            result.minimum_prefunded_cash,
            result.ledgers.liquidity.months,
        )

    assert key(forward) == key(backward)
