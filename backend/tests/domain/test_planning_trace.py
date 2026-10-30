"""The route checker reproduces TRACE-01 exactly before any optimiser exists (spec section
20; plan Sprint 5 acceptance; FIN-1, TIME-1): every ledger part of every route, route B's
£600 direct and economic cost, £150 peak payment and £4,850 minimum prefunded cash, and the
dates. Expected values are the fixture's own and the hand check's
(`docs/evidence/fixture-hand-check.md`), never read back from the checker."""

import pytest

from careerwright.capability.readiness import ReadinessState
from careerwright.planning.checker import Feasibility, Scenario, check_route, evaluate_route
from careerwright.planning.compiler import MonthlyInput, compile_input
from tests.support.capability import fixture
from tests.support.planning import (
    COURSES,
    trace_catalogue,
    trace_inputs,
    trace_readiness,
    trace_route,
)

# Hand check section 4: each route's lowest prefunded balance and its month.
LOWEST = {
    "A": (180000, "2027-03"),
    "B": (485000, "2027-01"),
    "C": (470000, "2027-01"),
    "D": (472500, "2027-01"),
    "E": (474000, "2027-01"),
}


def compiled() -> MonthlyInput:
    return compile_input(trace_inputs(), trace_catalogue(), readiness=trace_readiness())


@pytest.mark.req("TRACE01-01", "FIN1-03", "TEST1-01")
@pytest.mark.parametrize("letter", COURSES)
def test_each_route_s_direct_spend_income_loss_and_economic_cost(letter: str) -> None:
    route = trace_route(letter)
    check = check_route(compiled(), [f"TRACE-01/{letter}"])

    assert check.feasibility is Feasibility.FEASIBLE
    assert check.direct_cost is not None
    assert check.direct_cost.minor_units == route["direct_spend_minor"]
    assert check.economic_cost is not None
    assert check.economic_cost.minor_units == route["economic_cost_minor"]
    assert check.income_change is not None
    assert -check.income_change.minor_units == (
        route["economic_cost_minor"] - route["direct_spend_minor"]
    )
    assert [m.route_minor for m in check.ledgers.income.months] == route["income_by_month_minor"]
    assert [m.payments_minor for m in check.ledgers.direct.months] == route[
        "payments_by_month_minor"
    ]


@pytest.mark.req("TRACE01-02", "TIME1-05")
@pytest.mark.parametrize("letter", COURSES)
def test_each_route_is_prefunded_every_month_with_late_wages(letter: str) -> None:
    check = check_route(compiled(), [f"TRACE-01/{letter}"])
    lowest, month = LOWEST[letter]
    liquidity = check.ledgers.liquidity

    assert liquidity.complete
    assert check.minimum_prefunded_cash is not None
    assert check.minimum_prefunded_cash.minor_units == lowest
    assert min(liquidity.months, key=lambda m: m.lower_bound_minor).month == month
    assert all(m.lower_bound_minor >= 50000 for m in liquidity.months)
    assert check.peak_monthly_payment is not None
    assert check.peak_monthly_payment.minor_units <= 150000
    assert check.direct_cost is not None
    assert check.direct_cost.minor_units <= 150000


@pytest.mark.req("TRACE01-02", "TRACE01-08", "TIME1-02", "FIN1-01")
def test_route_b_is_the_print_snapshot_s_route() -> None:
    printed = fixture("worked_trace.json")["expected"]["print_snapshot"]
    check = check_route(compiled(), ["TRACE-01/B"])

    assert check.months_to_readiness == printed["time_months"] == 4
    assert check.readiness_month == "2027-05"  # finishes 30 April, usable from 1 May
    assert check.readiness_state is ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION
    assert check.readiness_state.value == printed["readiness_status"]
    assert check.direct_cost is not None
    assert check.economic_cost is not None
    assert check.direct_cost.minor_units == printed["direct_spend_minor"] == 60000
    assert check.economic_cost.minor_units == printed["economic_cost_minor"] == 60000
    assert check.peak_monthly_payment is not None
    assert check.peak_monthly_payment.minor_units == printed["peak_monthly_payment_minor"]
    assert check.minimum_prefunded_cash is not None
    assert check.minimum_prefunded_cash.minor_units == printed["minimum_prefunded_cash_minor"]
    assert check.horizon_months == printed["comparison_horizon_months"] == 6


@pytest.mark.req("TRACE01-08", "TIME-04", "TIME1-01")
@pytest.mark.parametrize("letter", COURSES)
def test_actual_dates_stay_beside_the_model_months(letter: str) -> None:
    route = trace_route(letter)
    action = next(
        a
        for a in fixture("worked_trace.json")["catalogue"]["actions"]
        if a["id"] == f"fixture:course:{letter}"
    )
    variant = compiled().variant(f"TRACE-01/{letter}")

    assert variant.start_date is not None
    assert variant.finish_date is not None
    assert variant.start_date.isoformat() == route["actual_start_date"]
    assert variant.finish_date.isoformat() == route["actual_finish_date"]
    assert variant.active == action["intakes"][0]["active_months"]
    check = check_route(compiled(), [f"TRACE-01/{letter}"])
    assert check.months_to_readiness == route["time_months"]


@pytest.mark.req("TRACE01-07", "TIME1-04")
def test_route_a_at_forty_hours_of_forty_passes_and_forty_one_fails() -> None:
    at_limit = check_route(compiled(), ["TRACE-01/A"])
    over = compile_input(trace_inputs(), trace_catalogue(A=41), readiness=trace_readiness())
    failed = check_route(over, ["TRACE-01/A"])

    assert at_limit.feasibility is Feasibility.FEASIBLE
    assert failed.feasibility is Feasibility.NOT_FEASIBLE_IN_MODEL
    workload = [f for f in failed.findings if f.code == "workload"]
    assert [(f.month, f.amount, f.limit) for f in workload] == [
        ("2027-01", 41, 40),
        ("2027-02", 41, 40),
    ]


@pytest.mark.req("TRACE01-06", "OUT1-05")
def test_the_checker_never_changes_current_evidence() -> None:
    basis = trace_readiness()
    check_route(compile_input(trace_inputs(), trace_catalogue(), readiness=basis), ["TRACE-01/B"])

    assert [e.self_assessed_level for e in basis.evidence] == [1, 1, 2]


@pytest.mark.req("PLN-08")
def test_a_route_without_conditions_reads_the_same_in_every_fixed_scenario() -> None:
    evaluation = evaluate_route(compiled(), ["TRACE-01/B"])
    base = evaluation.scenario(Scenario.BASE)

    assert [c.scenario for c in evaluation.checks] == list(Scenario)
    for check in evaluation.checks:
        assert check.conditions == []
        assert check.economic_cost == base.economic_cost
        assert check.months_to_readiness == base.months_to_readiness


@pytest.mark.req("TRACE01-02")
def test_the_compiled_input_is_versioned_by_its_content() -> None:
    first, again = compiled(), compiled()
    changed = compile_input(
        trace_inputs(reserve_minor=50001), trace_catalogue(), readiness=trace_readiness()
    )

    assert first.input_version == again.input_version
    assert changed.input_version != first.input_version
