"""Remaining-horizon actuals are kept separate from future route spending."""

from datetime import date

from careerwright.planning.checker import check_route
from careerwright.planning.comparison import basis
from careerwright.planning.compiler import (
    MonthlyInput,
    RemainingPayment,
    ReplanBasis,
    compile_input,
)
from careerwright.planning.search import search_routes
from tests.support.planning import ROW, catalogue_of, option, readiness_of, trace_inputs


def remaining_input(*, sunk: int = 90000, owed: int = 25000, future: int = 10000) -> MonthlyInput:
    old = trace_inputs()
    inputs = old.model_copy(
        update={
            "planning_start": date(2027, 1, 1),
            "horizon_months": 2,
            "opening_cash_minor": 200000,
            "baseline": old.baseline.model_copy(update={"net_income_by_month": [200000, 200000]})
            if old.baseline
            else None,
            "continuation": old.continuation.model_copy(
                update={"net_income_by_month": [200000, 200000]}
            ),
            "living_outgoings_by_month": [100000, 100000],
            "weekly_availability_by_month": [40, 40],
            "replan": ReplanBasis(
                from_plan_version=3,
                completed_variants=["old-course"],
                excluded_variants=["old-course"],
                sunk_paid_minor=sunk,
                remaining_payments=[
                    RemainingPayment(
                        variant_id="old-course", due=date(2027, 1, 15), amount_minor=owed
                    ),
                    RemainingPayment(
                        variant_id="old-course", due=date(2027, 3, 15), amount_minor=future
                    ),
                ],
            ),
        }
    )
    return compile_input(inputs, catalogue_of(), readiness=readiness_of({}))


def test_sunk_cost_is_disclosed_but_not_charged_again_and_future_debt_is_counted_once() -> None:
    monthly = remaining_input()
    check = check_route(monthly, [])
    direct, cash = check.ledgers.direct, check.ledgers.liquidity

    # Independent cash oracle: January 200000 - 100000 - 25000 = 75000,
    # then 200000 late pay; February 275000 - 100000 = 175000.
    assert [m.payments_minor for m in direct.months] == [25000, 0]
    assert [(x.due, x.amount_minor) for x in direct.beyond_horizon] == [("2027-03-15", 10000)]
    assert direct.total_minor == 35000
    assert [m.lower_bound_minor for m in cash.months] == [75000, 175000]
    assert [m.closing_minor for m in cash.months] == [275000, 375000]
    assert check.economic_cost is not None
    assert check.economic_cost.minor_units == 35000
    accounting = basis(monthly)
    assert accounting.opening_cash is not None
    assert accounting.opening_cash.minor_units == 200000
    assert accounting.replan is not None
    assert accounting.replan.sunk_paid.minor_units == 90000
    assert monthly.input_version != remaining_input(sunk=90001).input_version
    assert monthly.input_version != remaining_input(owed=25001).input_version


def test_payment_after_horizon_counts_in_total_but_not_monthly_cash_or_cap() -> None:
    monthly = remaining_input(future=200000)
    check = check_route(monthly, [])
    assert check.direct_cost is not None
    assert check.direct_cost.minor_units == 225000
    assert check.ledgers.direct.beyond_horizon[0].amount_minor == 200000
    assert [m.payments_minor for m in check.ledgers.liquidity.months] == [25000, 0]
    assert [m.lower_bound_minor for m in check.ledgers.liquidity.months] == [75000, 175000]
    assert any(f.code == "direct_spend_cap" for f in check.findings)
    assert not any(f.code == "monthly_payment_cap" for f in check.findings)


def test_completed_report_does_not_create_capability_evidence() -> None:
    monthly = remaining_input()
    check = check_route(monthly, [])
    assert check.months_to_readiness is None
    assert monthly.readiness is not None
    assert all(
        e.self_assessed_level is not None and e.self_assessed_level < 2
        for e in monthly.readiness.evidence
    )


def test_fixed_old_payment_and_new_option_share_the_direct_cap() -> None:
    old = remaining_input()
    expensive = option(
        "new-course",
        start=date(2027, 1, 1),
        finish=date(2027, 1, 31),
        payments=((0, 120000),),
    )
    monthly = compile_input(
        old.inputs,
        catalogue_of(expensive),
        readiness=readiness_of({"offering:new-course": [ROW]}),
    )
    check = check_route(monthly, ["new-course"])
    assert check.direct_cost is not None
    assert check.direct_cost.minor_units == 155000
    assert any(f.code == "direct_spend_cap" for f in check.findings)
    result = search_routes(monthly)
    assert not any("new-course" in schedule.route for schedule in result.schedules)


def test_fixed_old_payment_and_new_option_share_the_monthly_cap() -> None:
    old = remaining_input()
    inputs = old.inputs.model_copy(
        update={"direct_spend_cap_minor": 200000, "monthly_payment_cap_minor": 140000}
    )
    course = option(
        "new-course",
        start=date(2027, 1, 1),
        finish=date(2027, 1, 31),
        payments=((0, 120000),),
    )
    monthly = compile_input(
        inputs, catalogue_of(course), readiness=readiness_of({"offering:new-course": [ROW]})
    )
    check = check_route(monthly, ["new-course"])
    assert check.ledgers.direct.months[0].payments_minor == 145000
    assert any(f.code == "monthly_payment_cap" for f in check.findings)
    assert not any("new-course" in s.route for s in search_routes(monthly).schedules)
