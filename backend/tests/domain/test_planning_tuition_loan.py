"""A tuition fee loan paid straight to the provider is a loan to repay (Task 12c; spec section
22, the product owner's school-leaver decision 6 of 2026-11-01; section 12, FIN-1; ADR 0013
decision 5 as amended). On constructed synthetic cases with hand-worked values: the fee it pays
is in neither the cash ledger, nor direct spending, nor the monthly payment cap's payments, and
the route carries it as a loan to repay with its amount and month; one not yet approved makes
the route conditional, beside the route where the person pays; an unknown amount leaves the
route unresolved, never £0; every other loan is still refused as support; and the search sets
an option whose loan amount is unknown aside, archiving the loan-funded degree."""

from typing import Any

import pytest
from pydantic import ValidationError

from careerwright.money import Money
from careerwright.planning.catalogue import (
    ActionConcept,
    AwardState,
    EligibilityStatus,
    InstrumentKind,
    Offering,
    Variant,
)
from careerwright.planning.checker import (
    Condition,
    Feasibility,
    FindingCode,
    FindingKind,
    RouteCheck,
    RouteQualification,
    Scenario,
    check_route,
    evaluate_route,
)
from careerwright.planning.compiler import PlanningInputs, compile_input
from careerwright.planning.families import family_key
from careerwright.planning.inputs import SupportInput, TuitionFeeLoanInput
from careerwright.planning.ledgers import LoanToRepay
from careerwright.planning.search import PRUNING_VERSION, Outcome, SearchResult, search_routes
from tests.support.planning import (
    ROW,
    START,
    catalogue_of,
    grant_beside_loan,
    month_end,
    option,
    person,
    readiness_of,
    support,
    tuition_loan,
)

FEE = 953_500  # £9,535: a year's fee, paid in the course's first month
JAN, MAR = "2027-01", "2027-03"
Option = tuple[ActionConcept, Offering, Variant]


def gbp(minor: int) -> Money:
    return Money(minor_units=minor, currency="GBP")


def student(**changes: Any) -> PlanningInputs:
    """A school leaver with £200 saved and no pay, and a student's limits: £1,500 to spend on
    the change and £1,500 a month (synthetic)."""
    return person(
        horizon=3,
        opening=20_000,
        direct_cap=150_000,
        monthly_cap=150_000,
        **changes,
    )


def degree(payments: tuple[tuple[int, int], ...] = ((0, FEE),), **more: Any) -> Option:
    """A synthetic three-month course standing for a degree's first year (January to March)."""
    return option("degree", finish=month_end(START, 3), payments=payments, **more)


def check(
    inputs: PlanningInputs, *options: Option, scenario: Scenario = Scenario.BASE
) -> RouteCheck:
    monthly = compile_input(inputs, catalogue_of(*options))
    return check_route(monthly, [variant.variant_id for _, _, variant in options], scenario)


def codes(result: RouteCheck) -> set[FindingCode]:
    return {f.code for f in result.findings}


def column(result: RouteCheck, ledger: str, name: str) -> list[int | None]:
    months = getattr(result.ledgers, ledger).months
    return [getattr(m, name) for m in months]


@pytest.mark.req("FUNDING-06", "FIN1-10", "FUNDING-03")
def test_a_confirmed_loan_keeps_the_fee_out_of_cash_spending_and_the_payment_cap() -> None:
    self_paid = check(student(), degree())
    funded = check(student(), degree(tuition_fee_loan=tuition_loan(FEE)))

    # Counted as the student's own money, the fee breaks every limit it meets.
    assert self_paid.feasibility is Feasibility.NOT_FEASIBLE_IN_MODEL
    assert {
        FindingCode.DIRECT_SPEND_CAP,
        FindingCode.MONTHLY_PAYMENT_CAP,
        FindingCode.RESERVE,
    } <= codes(self_paid)
    # Paid straight to the university by the loan, it is on neither side: no payment, no
    # receipt, no support at the provider, no direct spending.
    assert funded.feasibility is Feasibility.FEASIBLE
    assert funded.findings == []
    assert column(funded, "direct", "payments_minor") == [0, 0, 0]
    assert column(funded, "direct", "paid_to_provider_minor") == [0, 0, 0]  # never support
    assert column(funded, "direct", "support_minor") == [0, 0, 0]
    assert column(funded, "liquidity", "payments_minor") == [0, 0, 0]
    assert column(funded, "liquidity", "early_receipts_minor") == [0, 0, 0]  # never a receipt
    assert column(funded, "liquidity", "later_receipts_minor") == [0, 0, 0]
    assert column(funded, "liquidity", "closing_minor") == [20_000, 20_000, 20_000]
    assert funded.direct_cost == gbp(0)
    assert funded.peak_monthly_payment == gbp(0)
    assert funded.ledgers.direct.beyond_horizon == []
    assert funded.ledgers.direct.unscheduled == []
    # The route carries it as a loan to repay: its amount and month, its repayment unknown.
    assert funded.loans_to_repay == [
        LoanToRepay(
            variant_id="degree", due=JAN, amount=gbp(FEE), repayment=None, conditional=False
        )
    ]
    assert funded.conditions == []
    # The person states it, so a route resting on it is qualified (never a reviewed record).
    assert RouteQualification.ACCEPTED_ASSUMPTIONS in funded.qualifications


@pytest.mark.req("FUNDING-06", "FIN1-02", "ECON-01")
def test_the_economic_cost_counts_the_fee_once_because_the_loan_is_repaid_later() -> None:
    economic = student(objective="economic", baseline=0)

    funded = check(economic, degree(tuition_fee_loan=tuition_loan(FEE)))
    direct = check(student(), degree(tuition_fee_loan=tuition_loan(FEE)))

    # FIN-1: loan principal is a liquidity source, not a discount. The fee is a cost over the
    # horizon, counted once; it is not the student's spending now.
    assert funded.feasibility is Feasibility.FEASIBLE
    assert funded.direct_cost == gbp(0)
    assert funded.economic_cost is not None
    assert funded.economic_cost.minor_units == FEE
    assert funded.objective_cost is not None
    assert funded.objective_cost.minor_units == FEE
    # The direct-spending comparison reads direct spending only.
    assert direct.objective_cost is not None
    assert direct.objective_cost.minor_units == 0


@pytest.mark.req("FUNDING-06", "FIN1-10")
def test_the_loan_pays_the_fees_left_after_provider_support_up_to_its_amount_by_month() -> None:
    grant = support(paid_to="provider", amount=100_000)
    split = degree(
        payments=((0, 450_000), (2, 450_000)),
        supports=(grant,),
        tuition_fee_loan=tuition_loan(600_000),
    )
    rich = person(horizon=3, opening=1_000_000)

    result = check(rich, split)

    # The grant covers £1,000 of January's fee first; the loan pays the next £6,000 (£3,500 in
    # January, £2,500 in March); the person pays March's remaining £2,000.
    assert column(result, "direct", "paid_to_provider_minor") == [100_000, 0, 0]
    assert column(result, "direct", "payments_minor") == [0, 0, 200_000]
    assert result.direct_cost == gbp(200_000)
    assert result.loans_to_repay == [
        LoanToRepay(variant_id="degree", due=JAN, amount=gbp(350_000), conditional=False),
        LoanToRepay(variant_id="degree", due=MAR, amount=gbp(250_000), conditional=False),
    ]


@pytest.mark.req("FUNDING-06")
def test_a_loan_never_pays_an_extra_cost_and_a_grant_to_the_person_counts_once() -> None:
    course = degree(
        tuition_fee_loan=tuition_loan(FEE),
        supports=(support(paid_to="person", amount=50_000, month=0),),
    )
    concept, offering, variant = course
    plan = offering.payment_plans[0]
    extra = plan.payments[0].model_copy(update={"kind": "extra", "amount": gbp(5_000)})
    with_extra = offering.model_copy(
        update={"payment_plans": [plan.model_copy(update={"payments": [*plan.payments, extra]})]}
    )

    result = check(
        person(horizon=3, opening=20_000, objective="economic", baseline=0),
        (concept, with_extra, variant),
    )

    # The £50 extra cost is the person's; the loan pays the tuition only.
    assert column(result, "direct", "payments_minor") == [5_000, 0, 0]
    assert result.loans_to_repay == [
        LoanToRepay(variant_id="degree", due=JAN, amount=gbp(FEE), conditional=False)
    ]
    # The £500 grant is a receipt. Against direct spending it lowers only the tuition the
    # person pays, which is none, never the extra (as before Task 12c): fix round 1.
    assert column(result, "liquidity", "later_receipts_minor") == [50_000, 0, 0]
    assert column(result, "direct", "support_minor") == [0, 0, 0]
    assert result.direct_cost == gbp(5_000)
    # The economic cost counts the fee and the extra once, less the grant once.
    assert result.economic_cost is not None
    assert result.economic_cost.minor_units == FEE + 5_000 - 50_000


@pytest.mark.req("FUNDING-06", "FUNDING-03", "OPT1-07")
def test_a_grant_beside_a_loan_never_takes_an_option_s_direct_spending_below_zero() -> None:
    # Review 12c, Critical 1: a £1,000 grant to the student beside a loan paying the whole
    # £9,000 fee once read as -£1,000 of the degree's own spending, which the search's
    # spend-cap pruning cannot see, so it said "no route" while the checker passed one.
    monthly = grant_beside_loan()

    degree_alone = check_route(monthly, ["degree"])
    both = check_route(monthly, ["course", "degree"])
    economic = check(
        person(horizon=3, opening=1_000_000, objective="economic", baseline=0),
        degree(
            tuition_fee_loan=tuition_loan(900_000),
            payments=((0, 900_000),),
            supports=(support(paid_to="person", amount=100_000, month=0),),
        ),
    )
    result = search_routes(monthly)

    assert degree_alone.direct_cost == gbp(0)
    assert column(degree_alone, "direct", "support_minor") == [0, 0, 0]
    assert column(degree_alone, "liquidity", "later_receipts_minor") == [100_000, 0, 0]
    # The £1,200 course is the student's own, above their £1,000 cap: the grant beside the
    # loan never pays for another option.
    assert both.direct_cost == gbp(120_000)
    assert FindingCode.DIRECT_SPEND_CAP in codes(both)
    assert result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    assert result.schedules == []
    # The cost over the horizon: the fee once, less the grant once.
    assert economic.economic_cost is not None
    assert economic.economic_cost.minor_units == 800_000


@pytest.mark.req("FUNDING-06", "FUNDING-05")
def test_a_loan_not_yet_approved_that_pays_nothing_makes_nothing_conditional() -> None:
    # Review 12c, Minor 1: no fee for it to pay, or every fee waived at the provider.
    hoped = tuition_loan(FEE, application=AwardState.APPLIED)
    waiver = support(paid_to="provider", amount=None, kind=InstrumentKind.FEE_WAIVER)
    no_fee = check(student(), degree(payments=(), tuition_fee_loan=hoped))
    waived = check(student(), degree(supports=(waiver,), tuition_fee_loan=hoped))
    unpriced = check(
        student(),
        degree(payments=(), tuition_fee_loan=tuition_loan(None, application=AwardState.APPLIED)),
    )

    for result in (no_fee, waived):
        assert result.feasibility is Feasibility.FEASIBLE
        assert result.conditions == []
        assert RouteQualification.CONDITIONAL_LOAN not in result.qualifications
        assert result.loans_to_repay == []
    # With its amount unknown, what it pays is not known, so the route still rests on it.
    assert [c.kind for c in unpriced.conditions] == ["loan"]


@pytest.mark.req("FUNDING-06", "FUNDING-05")
@pytest.mark.parametrize(
    ("application", "eligibility", "counted"),
    [
        (AwardState.APPLIED, EligibilityStatus.POTENTIALLY_ELIGIBLE, True),
        (AwardState.NOT_APPLIED, EligibilityStatus.CONFIRMED, True),
        (AwardState.APPLIED, EligibilityStatus.INELIGIBLE, False),
        (AwardState.APPLIED, EligibilityStatus.INSUFFICIENT_INFORMATION, False),
        (AwardState.REFUSED, EligibilityStatus.CONFIRMED, False),
    ],
)
def test_a_loan_not_yet_approved_gives_a_conditional_route_beside_the_self_paid_one(
    application: AwardState, eligibility: EligibilityStatus, counted: bool
) -> None:
    hoped = tuition_loan(FEE, application=application, eligibility=eligibility)
    monthly = compile_input(student(), catalogue_of(degree(tuition_fee_loan=hoped)))

    evaluation = evaluate_route(monthly, ["degree"])
    funded, unfunded = evaluation.scenario(Scenario.BASE), evaluation.scenario(Scenario.NO_AWARD)

    assert (funded.feasibility is Feasibility.FEASIBLE) is counted
    assert funded.conditions == (
        [
            Condition(
                kind="loan",
                variant_id="degree",
                instrument_id=None,
                verification="confirm_loan_approved",
            )
        ]
        if counted
        else []
    )
    assert (RouteQualification.CONDITIONAL_LOAN in funded.qualifications) is counted
    assert RouteQualification.CONDITIONAL_AWARD not in funded.qualifications  # never an award
    assert funded.loans_to_repay == (
        [LoanToRepay(variant_id="degree", due=JAN, amount=gbp(FEE), conditional=True)]
        if counted
        else []
    )
    # Beside it, the route where the student pays the fee: on their own limits.
    assert unfunded.feasibility is Feasibility.NOT_FEASIBLE_IN_MODEL
    assert column(unfunded, "direct", "payments_minor") == [FEE, 0, 0]
    assert unfunded.loans_to_repay == []
    assert unfunded.conditions == []


@pytest.mark.req("FUNDING-06")
def test_a_confirmed_loan_counts_in_every_scenario() -> None:
    monthly = compile_input(student(), catalogue_of(degree(tuition_fee_loan=tuition_loan(FEE))))

    for result in evaluate_route(monthly, ["degree"]).checks:
        assert result.feasibility is Feasibility.FEASIBLE, result.scenario
        assert result.loans_to_repay == [
            LoanToRepay(variant_id="degree", due=JAN, amount=gbp(FEE), conditional=False)
        ]


@pytest.mark.req("FUNDING-06", "PLN-08")
def test_a_delayed_loan_pays_only_the_fees_that_fall_due_after_it_arrives() -> None:
    hoped = tuition_loan(FEE, application=AwardState.APPLIED)
    course = degree(payments=((0, 300_000), (2, 300_000)), tuition_fee_loan=hoped)

    delayed = check(person(horizon=3, opening=1_000_000), course, scenario=Scenario.DELAY)

    # Two months late, as an award paid to the provider would be (ADR 0013 decision 9).
    assert column(delayed, "direct", "payments_minor") == [300_000, 0, 0]
    assert delayed.loans_to_repay == [
        LoanToRepay(variant_id="degree", due=MAR, amount=gbp(300_000), conditional=True)
    ]


@pytest.mark.req("FUNDING-06")
def test_an_unknown_loan_amount_leaves_the_route_unresolved_never_zero() -> None:
    unpriced = tuition_loan(None)

    result = check(student(), degree(tuition_fee_loan=unpriced))

    assert result.feasibility is Feasibility.UNRESOLVED
    [unknown] = result.findings
    assert (unknown.code, unknown.kind, unknown.variant_id) == (
        FindingCode.LOAN_AMOUNT_UNKNOWN,
        FindingKind.UNRESOLVED,
        "degree",
    )
    assert result.direct_cost is None  # never £0
    assert column(result, "direct", "payments_minor") == [None, None, None]
    assert result.loans_to_repay == [
        LoanToRepay(variant_id="degree", due=None, amount=None, conditional=False)
    ]
    # Not yet approved, the route where the student pays is still known beside it.
    hoped = tuition_loan(None, application=AwardState.APPLIED)
    monthly = compile_input(student(), catalogue_of(degree(tuition_fee_loan=hoped)))
    unfunded = check_route(monthly, ["degree"], Scenario.NO_AWARD)
    assert unfunded.direct_cost == gbp(FEE)


@pytest.mark.req("FUNDING-06", "FUNDING-04")
def test_a_maintenance_loan_stated_as_support_is_still_refused() -> None:
    for paid_to, month in (("person", 0), ("provider", None)):
        with pytest.raises(ValidationError, match="loan is information"):
            SupportInput(
                instrument_id="funding:maintenance-loan",
                kind=InstrumentKind.LOAN,
                amount=gbp(400_000),
                paid_to=paid_to,
                paid_month_offset=month,
                eligibility=EligibilityStatus.CONFIRMED,
                award=AwardState.APPROVED,
            )
    with pytest.raises(ValidationError, match="confirmed eligibility"):
        TuitionFeeLoanInput(
            amount=gbp(FEE),
            eligibility=EligibilityStatus.POTENTIALLY_ELIGIBLE,
            application=AwardState.APPROVED,
        )


@pytest.mark.req("FUNDING-06", "ROU1-01")
def test_the_loan_is_material_financing_in_the_route_s_family() -> None:
    plain = compile_input(student(), catalogue_of(degree()))
    funded = compile_input(student(), catalogue_of(degree(tuition_fee_loan=tuition_loan(FEE))))

    assert family_key(plain.variants).family_id != family_key(funded.variants).family_id
    [action] = family_key(funded.variants).actions
    assert action.financing == ["tuition_fee_loan:approved"]


# The search (ADR 0016's amendment for Task 12c).


def _search(*options: Option) -> SearchResult:
    teaches = {o.offering_id: (ROW,) for _, o, _ in options}
    monthly = compile_input(student(), catalogue_of(*options), readiness=readiness_of(teaches))
    return search_routes(monthly)


@pytest.mark.req("FUNDING-06", "OPT1-07")
def test_the_search_archives_the_loan_funded_degree_and_sets_an_unknown_amount_aside() -> None:
    confirmed = _search(degree(tuition_fee_loan=tuition_loan(FEE)))
    hoped = _search(degree(tuition_fee_loan=tuition_loan(FEE, application=AwardState.APPLIED)))
    unpriced = _search(degree(tuition_fee_loan=tuition_loan(None)))
    self_paid = _search(degree())

    assert PRUNING_VERSION == "sound-pruning-5"
    [schedule] = confirmed.schedules
    assert (schedule.route, schedule.direct_cost) == (["degree"], gbp(0))
    assert schedule.loans_to_repay == [
        LoanToRepay(variant_id="degree", due=JAN, amount=gbp(FEE), conditional=False)
    ]
    [conditional] = hoped.schedules
    assert [c.kind for c in conditional.conditions] == ["loan"]
    assert RouteQualification.CONDITIONAL_LOAN in conditional.qualifications
    # An unknown amount is the option's own unknown, in every route containing it.
    assert unpriced.schedules == []
    assert unpriced.outcome is Outcome.UNRESOLVED
    [aside] = unpriced.set_aside
    assert (aside.variant_id, aside.codes) == ("degree", [FindingCode.LOAN_AMOUNT_UNKNOWN])
    # Paying the fee itself, the student has no route within their limits.
    assert self_paid.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
