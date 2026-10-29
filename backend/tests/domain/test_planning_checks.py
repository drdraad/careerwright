"""The checker's rules one at a time, on constructed synthetic cases with hand-worked values
(plan section 8: PREFUND, PAYCAP, TIME, WORKLOAD, ECON, FUNDING; spec section 12, TIME-1,
FIN-1, "Hard feasibility constraints" and "Uncertainty and conditional plans"; S5.4-S5.6).
Where a case is a fixture persona's (P02, P03), its values are read from the fixture."""

from datetime import date, time

import pytest
from pydantic import ValidationError

from nessa.capability.outcomes import (
    Confidence,
    EvidenceKind,
    OutcomeReview,
    OutcomeSpan,
    OutcomeType,
    PlannedOutcome,
    Provenance,
)
from nessa.capability.readiness import Qualification
from nessa.errors import ErrorCode, NessaError
from nessa.planning.catalogue import (
    ActionKind,
    AwardState,
    EligibilityStatus,
    Fact,
    InstrumentKind,
    OfferGate,
    RecordState,
    Session,
    WorkPatternKind,
)
from nessa.planning.checker import (
    Feasibility,
    FindingCode,
    FindingKind,
    RouteCheck,
    RouteQualification,
    Scenario,
    Verdict,
    check_route,
    evaluate_route,
)
from nessa.planning.compiler import (
    Commitment,
    ExistingDebt,
    PlanningInputs,
    ReadinessBasis,
    ReceiptTiming,
    compile_input,
)
from tests.support.capability import fixture, self_report, skill_row, synthetic_matrix
from tests.support.planning import (
    CONSTRUCTED,
    catalogue_of,
    option,
    pattern,
    person,
    support,
)

JAN, FEB, MAR, APR = (date(2027, m, 1) for m in (1, 2, 3, 4))


def check(
    inputs: PlanningInputs,
    *options: tuple,  # type: ignore[type-arg]
    route: list[str] | None = None,
    scenario: Scenario = Scenario.BASE,
    readiness: ReadinessBasis | None = None,
) -> RouteCheck:
    monthly = compile_input(inputs, catalogue_of(*options), readiness=readiness)
    names = route if route is not None else [variant.variant_id for _, _, variant in options]
    return check_route(monthly, names, scenario)


def codes(result: RouteCheck) -> set[str]:
    return {f.code.value for f in result.findings}


def finding(result: RouteCheck, code: FindingCode) -> list[tuple[str | None, int | None]]:
    return [(f.month, f.amount) for f in result.findings if f.code is code]


# PREFUND: conservative prefunding (TIME1-05).


@pytest.mark.req("PREFUND-01", "TIME1-05")
def test_a_late_wage_does_not_rescue_a_day_one_fee_although_the_month_ends_positive() -> None:
    # £100 opening, a £200 fee on day one, £300 pay on day 28, reserve £0.
    result = check(person(opening=10000, pay=30000), option("fee", payments=((0, 20000),)))

    assert finding(result, FindingCode.RESERVE) == [("2027-01", -10000)]
    assert result.ledgers.liquidity.months[0].closing_minor == 20000  # +£200 at month end
    assert result.feasibility is Feasibility.NOT_FEASIBLE_IN_MODEL


@pytest.mark.req("PREFUND-02", "TIME1-05")
def test_pay_proven_to_arrive_before_the_fee_pays_for_it() -> None:
    inputs = person(opening=10000, pay=30000, timing=ReceiptTiming.BEFORE_OUTFLOWS)
    result = check(inputs, option("fee", payments=((0, 20000),)))

    assert result.ledgers.liquidity.months[0].lower_bound_minor == 20000  # 100 + 300 - 200
    assert result.feasibility is Feasibility.FEASIBLE


@pytest.mark.req("PREFUND-03", "TIME1-05", "FIN1-04")
def test_an_unconfirmed_grant_or_an_unaccepted_offer_never_funds_an_earlier_payment() -> None:
    unconfirmed = support(
        amount=30000,
        eligibility=EligibilityStatus.POTENTIALLY_ELIGIBLE,
        award=AwardState.APPLIED,
        assumed=True,
        early=True,  # stated early, but an unconfirmed grant is never proven early
    )
    approved = support(amount=30000, early=True)
    day_one = ((0, 20000),)
    hoped = check(person(opening=10000), option("fee", payments=day_one, supports=(unconfirmed,)))
    confirmed = check(person(opening=10000), option("fee", payments=day_one, supports=(approved,)))

    assert finding(hoped, FindingCode.RESERVE) == [("2027-01", -10000)]
    assert confirmed.feasibility is Feasibility.FEASIBLE

    def with_job(accepted: bool) -> RouteCheck:
        job = option(
            "job",
            kind=ActionKind.WORK,
            wage=30000,
            hours=20,
            offer=OfferGate(accepted=accepted, role_class="data clerk"),
        )
        early = ReceiptTiming.BEFORE_OUTFLOWS  # the person's own pay is early: not this wage
        return check(person(opening=10000, timing=early), option("fee", payments=day_one), job)

    unaccepted, accepted = with_job(False), with_job(True)
    assert finding(unaccepted, FindingCode.RESERVE) == [("2027-01", -10000)]
    assert accepted.feasibility is Feasibility.FEASIBLE


# PAYCAP: the monthly payment cap is not the direct budget (FIN1-06).


@pytest.mark.req("PAYCAP-01", "FIN1-06")
def test_most_of_the_fee_due_at_once_fails_the_payment_cap_within_the_direct_budget() -> None:
    inputs = person(horizon=4, opening=1_000_000, direct_cap=300000, monthly_cap=25000)
    course = option(
        "course",
        finish=date(2027, 4, 30),
        payments=((0, 180000), (1, 20000), (2, 20000), (3, 20000)),
    )
    result = check(inputs, course)

    assert finding(result, FindingCode.MONTHLY_PAYMENT_CAP) == [("2027-01", 180000)]
    assert FindingCode.DIRECT_SPEND_CAP.value not in codes(result)
    assert result.direct_cost is not None
    assert result.direct_cost.minor_units == 240000


@pytest.mark.req("PAYCAP-02", "FIN1-06")
def test_p03_s_option_is_rejected_for_the_payment_cap_among_every_other_limit_it_breaks() -> None:
    p03 = fixture("personas/P03.json")
    reject = p03["expected"]["reject_option"]
    upfront, total = reject["upfront_fee_minor"], reject["total_fee_minor"]
    inputs = person(
        horizon=2,
        opening=p03["opening_cash_minor"],
        reserve=p03["reserve_minor"],
        direct_cap=p03["direct_spend_cap_minor"],
        monthly_cap=p03["monthly_payment_cap_minor"],
    )
    course = option(
        "course", finish=date(2027, 2, 28), payments=((0, upfront), (1, total - upfront))
    )
    result = check(inputs, course)

    # Hand check H1: every violated limit is listed; membership, never "the only reason".
    assert p03["expected"]["reject_reason"] in codes(result)
    assert FindingCode.RESERVE.value in codes(result)
    assert FindingCode.DIRECT_SPEND_CAP.value not in codes(result)  # £300 of a £300 cap


@pytest.mark.req("PAYCAP-03", "FIN1-06")
def test_a_cap_is_met_at_equality_and_broken_by_one_penny() -> None:
    def run(payment: int, direct_cap: int) -> set[str]:
        inputs = person(opening=1_000_000, monthly_cap=20000, direct_cap=direct_cap)
        return codes(check(inputs, option("c", payments=((0, payment),))))

    assert run(20000, 20000) == set()
    assert run(20001, 30000) == {"monthly_payment_cap"}
    assert run(20000, 19999) == {"direct_spend_cap"}


@pytest.mark.req("FIN1-06", "FIN1-10")
def test_the_direct_budget_payment_cap_deficit_cap_and_reserve_are_four_limits() -> None:
    inputs = person(
        horizon=2,
        opening=1_000_000,
        baseline=200000,
        pay=200000,
        hours=30,
        objective="economic",
        direct_cap=100000,
        monthly_cap=20000,
        monthly_deficit_cap_minor=50000,
        reserve=10000,
    )
    reduced = pattern(WorkPatternKind.REDUCED_HOURS, 20, 150000)
    course = option(
        "course", finish=date(2027, 2, 28), payments=((0, 10000), (1, 10000)), pattern=reduced
    )
    result = check(inputs, course)

    # £100 paid and £500 of pay lost a month: only the deficit limit (£500) is passed.
    assert finding(result, FindingCode.MONTHLY_DEFICIT_CAP) == [
        ("2027-01", 60000),
        ("2027-02", 60000),
    ]
    assert codes(result) == {"monthly_deficit_cap"}
    without_baseline = check(person(monthly_deficit_cap_minor=50000), option("c"))
    assert FindingCode.BASELINE_MISSING.value in codes(without_baseline)
    # An economic-cost cap is an optional preference, never a hard limit.
    preferring = inputs.model_copy(
        update={"monthly_deficit_cap_minor": None, "economic_cost_cap_minor": 100000}
    )
    preferred = check(preferring, course)
    [unmet] = preferred.findings
    assert (unmet.code, unmet.kind) == (FindingCode.ECONOMIC_COST_CAP, FindingKind.PREFERENCE)
    assert preferred.feasibility is Feasibility.FEASIBLE


# TIME: the monthly grid's rules (TIME1-02, TIME1-03).


@pytest.mark.req("TIME-02", "TIME1-02", "PLN-03")
def test_a_prerequisite_is_usable_only_from_the_month_after_its_completion() -> None:
    first = option("first", start=JAN, finish=date(2027, 3, 31), grants=["gate:first"])
    too_soon = option("next", start=date(2027, 3, 15), finish=APR, prerequisites=["gate:first"])
    in_time = option("next", start=APR, finish=date(2027, 4, 30), prerequisites=["gate:first"])

    failed = check(person(horizon=6), first, too_soon)
    passed = check(person(horizon=6), first, in_time)
    missing = check(person(horizon=6), in_time)

    assert [(f.code, f.month, f.reason) for f in failed.findings] == [
        (FindingCode.PREREQUISITE_NOT_USABLE, "2027-03", "gate:first")
    ]
    assert passed.feasibility is Feasibility.FEASIBLE
    assert codes(missing) == {"prerequisite_not_usable"}


def _admission(finish: date) -> tuple:  # type: ignore[type-arg]
    return option(
        "apply", kind=ActionKind.APPLICATION, start=JAN, finish=finish, grants=["admission:x"]
    )


@pytest.mark.req("TIME-03", "TIME1-03", "PLN-01")
def test_an_application_in_its_deadline_month_is_unresolved_never_ineligible() -> None:
    course = option(
        "course",
        start=APR,
        finish=date(2027, 4, 30),
        prerequisites=["admission:x"],
        application_deadline=date(2027, 3, 15),
        application_gate="admission:x",
    )
    early = check(person(horizon=6), _admission(date(2027, 2, 10)), course)
    same = check(person(horizon=6), _admission(date(2027, 3, 5)), course)
    late = check(person(horizon=6), _admission(date(2027, 4, 2)), course)
    exempt = check(person(horizon=6, initial_gates=["admission:x"]), course)

    assert early.feasibility is Feasibility.FEASIBLE
    [unresolved] = same.findings
    assert unresolved.code is FindingCode.COARSE_MODEL_UNRESOLVED
    assert unresolved.kind is FindingKind.UNRESOLVED
    assert same.feasibility is Feasibility.UNRESOLVED
    assert FindingCode.APPLICATION_TOO_LATE.value in codes(late)
    assert exempt.feasibility is Feasibility.FEASIBLE  # a completed admission, verified
    unapplied = check(person(horizon=6), course)
    assert codes(unapplied) == {"prerequisite_not_usable"}  # no application at all


@pytest.mark.req("TIME-03", "TIME1-03")
def test_a_deadline_that_has_passed_cannot_be_ignored() -> None:
    course = option(
        "course",
        start=APR,
        finish=date(2027, 4, 30),
        prerequisites=["admission:x"],
        application_deadline=date(2026, 12, 1),
        application_gate="admission:x",
    )

    result = check(person(horizon=6), _admission(date(2027, 1, 20)), course)

    assert FindingCode.APPLICATION_TOO_LATE.value in codes(result)


# WORKLOAD: the weekly envelope, evaluated once a month (TIME1-04).


@pytest.mark.req("WORKLOAD-01", "TIME1-04")
def test_two_twenty_hour_courses_in_one_week_fail_twenty_available_hours() -> None:
    result = check(person(availability=20), option("first", hours=20), option("second", hours=20))

    # The envelope sums the weekly maxima: 40 > 20. A naive monthly total, 40 <= 4 x 20,
    # would have passed.
    assert finding(result, FindingCode.WORKLOAD) == [("2027-01", 40)]


@pytest.mark.req("WORKLOAD-02", "TIME1-04")
def test_a_known_session_clash_fails_separately_from_the_hours() -> None:
    tuesday = Session(weekday=1, starts=time(18), ends=time(20))
    wednesday = Session(weekday=2, starts=time(18), ends=time(20))
    clash = check(
        person(availability=40),
        option("first", hours=5, sessions=[tuesday]),
        option("second", hours=5, sessions=[tuesday]),
    )
    apart = check(
        person(availability=40),
        option("first", hours=5, sessions=[tuesday]),
        option("second", hours=5, sessions=[wednesday]),
    )

    assert codes(clash) == {"session_clash"}
    assert apart.feasibility is Feasibility.FEASIBLE


@pytest.mark.req("WORKLOAD-03", "TIME1-04")
def test_total_hours_without_a_timetable_leave_the_envelope_unknown_never_a_pass() -> None:
    result = check(person(availability=40), option("course", hours=None))

    assert codes(result) == {"workload_unknown"}
    assert result.feasibility is Feasibility.UNRESOLVED
    assert result.verdict is Verdict.UNRESOLVED
    # Without dates as well, the missing timetable is still named on its own.
    undated = check(person(availability=40), option("course", start=None, hours=None))
    assert codes(undated) == {"dates_unknown", "workload_unknown"}


@pytest.mark.req("WORKLOAD-04", "TIME1-04", "PLN-02")
def test_work_care_and_commute_count_once_in_the_envelope() -> None:
    commitments = [
        Commitment(label="care", hours_per_week=5, cited=CONSTRUCTED),
        Commitment(label="commute", hours_per_week=5, cited=CONSTRUCTED),
    ]
    inputs = person(availability=50, hours=30, commitments=commitments)

    fits = check(inputs, option("course", hours=10))  # 30 + 5 + 5 + 10 = 50
    over = check(inputs, option("course", hours=11))

    assert fits.feasibility is Feasibility.FEASIBLE
    # The limit is the stated availability: commitments are a load, never also a cut in it.
    assert [(f.amount, f.limit) for f in over.findings] == [(51, 50)]


# ECON: one horizon, one baseline, income counted once (FIN1-03, TIME1-06).


@pytest.mark.req("ECON-01", "FIN1-03", "OPTN-02", "FIN1-12")
def test_an_apprentice_s_wage_replaces_the_current_pay_and_is_counted_once() -> None:
    inputs = person(horizon=3, baseline=200000, pay=200000, hours=30, objective="economic")
    leave = pattern(WorkPatternKind.LEAVE_CURRENT_JOB, 0, 0)
    apprenticeship = option(
        "apprenticeship",
        kind=ActionKind.APPRENTICESHIP,
        finish=date(2027, 3, 31),
        hours=37,
        pattern=leave,
        wage=150000,
        offer=OfferGate(accepted=True),
    )
    course = option("course", finish=date(2027, 3, 31), hours=6)
    monthly = compile_input(inputs, catalogue_of(apprenticeship, course))

    paid = check_route(monthly, ["apprenticeship"])
    studied = check_route(monthly, ["course"])

    assert [m.route_minor for m in paid.ledgers.income.months] == [150000] * 3
    assert paid.economic_cost is not None
    assert paid.economic_cost.minor_units == 3 * 50000
    assert paid.feasibility is Feasibility.FEASIBLE  # 37 training-and-work hours, once
    assert paid.horizon_months == studied.horizon_months == 3
    assert paid.ledgers.income.baseline_label == studied.ledgers.income.baseline_label


@pytest.mark.req("ECON-02", "FIN1-03")
def test_the_fin_1_example_trades_time_against_economic_cost() -> None:
    inputs = person(
        horizon=12, opening=1_000_000, baseline=200000, pay=200000, hours=30,
        objective="economic",
    )  # fmt: skip
    away = pattern(WorkPatternKind.TEMPORARY_STUDY_BREAK, 0, 0)
    short = option("short", finish=date(2027, 6, 30), hours=35, pattern=away,
                   payments=((0, 300000),))  # fmt: skip
    part_time = option("part-time", finish=date(2027, 12, 31), hours=10, payments=((0, 500000),))

    fast = check(inputs, short)
    slow = check(inputs, part_time)

    assert fast.economic_cost is not None
    assert slow.economic_cost is not None
    assert fast.economic_cost.minor_units == 1_500_000  # £3,000 + six months of £2,000
    assert slow.economic_cost.minor_units == 500_000  # £5,000, pay kept


@pytest.mark.req("ECON-03", "FIN1-05")
def test_a_negative_economic_cost_is_kept_and_never_cash_available_today() -> None:
    inputs = person(horizon=3, opening=50000, living=40000, baseline=100000, pay=100000,
                    objective="economic")  # fmt: skip
    better = option(
        "job", kind=ActionKind.WORK, finish=date(2027, 3, 31), hours=35, wage=150000,
        pattern=pattern(WorkPatternKind.LEAVE_CURRENT_JOB, 0, 0), offer=OfferGate(accepted=True),
    )  # fmt: skip
    result = check(inputs, better)

    assert result.economic_cost is not None
    assert result.economic_cost.minor_units == -150000
    first = result.ledgers.liquidity.months[0]
    assert first.early_receipts_minor == 0
    assert first.lower_bound_minor == 50000 - 40000  # tomorrow's pay is not today's cash


@pytest.mark.req("ECON-04", "FIN1-02")
def test_payments_due_after_the_horizon_stay_in_direct_cost_with_their_dates() -> None:
    course = option(
        "course",
        finish=date(2027, 2, 28),
        payments=((0, 10000), (1, 10000), (2, 10000), (3, 10000)),
    )
    result = check(person(horizon=2, opening=100000), course)

    assert result.direct_cost is not None
    assert result.direct_cost.minor_units == 40000
    assert [(i.due, i.amount_minor) for i in result.ledgers.direct.beyond_horizon] == [
        ("2027-03", 10000),
        ("2027-04", 10000),
    ]
    assert [m.payments_minor for m in result.ledgers.liquidity.months] == [10000, 10000]


@pytest.mark.req("ECON-05", "FIN1-01", "TIME1-06")
def test_after_its_activities_a_route_follows_the_stated_continuation_never_a_target_wage() -> None:
    inputs = person(horizon=3, baseline=200000, pay=180000, hours=30, objective="economic")
    away = pattern(WorkPatternKind.TEMPORARY_STUDY_BREAK, 0, 0)
    result = check(inputs, option("course", finish=date(2027, 1, 31), hours=35, pattern=away))

    assert [m.route_minor for m in result.ledgers.income.months] == [0, 180000, 180000]
    assert result.ledgers.income.continuation_label == "the current role, unchanged"


@pytest.mark.req("ECON-06", "FIN1-07", "FIN1-11")
def test_a_missing_baseline_leaves_the_economic_comparison_unresolved_never_zero() -> None:
    p02 = fixture("personas/P02.json")
    assert p02["income_baseline_status"] == "unconfirmed"  # its income of 0 is not a baseline
    fee = option("course", payments=((0, 5000),))
    economic = check(person(opening=10000, objective="economic"), fee)
    direct = check(person(opening=10000, objective="direct_spending"), fee)

    assert codes(economic) == {"baseline_missing"}
    assert economic.economic_cost is None
    assert economic.objective_cost is None
    assert economic.verdict is Verdict.UNRESOLVED
    assert direct.objective_cost is not None
    assert direct.objective_cost.minor_units == 5000  # the explicit direct-spending mode
    assert direct.objective_basis == "direct_spending"


# FUNDING: potential is not an award; support counted once (spec section 10, FIN1-10).


@pytest.mark.req("FUNDING-01", "TIME1-05")
def test_p03_s_unconfirmed_grant_contributes_nothing_to_unconditional_figures() -> None:
    p03 = fixture("personas/P03.json")
    grant = support(
        amount=p03["unconfirmed_grant_minor"],
        eligibility=EligibilityStatus.POTENTIALLY_ELIGIBLE,
        award=AwardState.NOT_APPLIED,
    )
    course = option("course", payments=((0, 30000),), supports=(grant,))
    result = check(person(opening=p03["opening_cash_minor"]), course)

    assert p03["expected"]["unconfirmed_grant_in_unconditional_ledger"] == 0
    assert sum(m.support_minor for m in result.ledgers.direct.months) == 0
    assert sum(m.later_receipts_minor for m in result.ledgers.liquidity.months) == 0
    assert result.direct_cost is not None
    assert result.direct_cost.minor_units == 30000
    assert result.conditions == []


@pytest.mark.req("FUNDING-02", "FIN1-04", "PLN-05", "OPTN-04")
def test_bridge_wages_start_only_at_the_offer_gate_and_go_with_it() -> None:
    bridge = option(
        "bridge",
        kind=ActionKind.WORK,
        start=MAR,
        finish=date(2027, 4, 30),
        hours=30,
        wage=120000,
        offer=OfferGate(accepted=False, role_class="customer data assistant"),
    )
    monthly = compile_input(person(horizon=4), catalogue_of(bridge))

    base = check_route(monthly, ["bridge"], Scenario.BASE)
    none = check_route(monthly, ["bridge"], Scenario.NO_OFFER)

    assert fixture("personas/P03.json")["expected"]["bridge_wages_before_offer"] == 0
    assert [m.route_minor for m in base.ledgers.income.months] == [0, 0, 120000, 120000]
    assert [c.kind for c in base.conditions] == ["offer"]
    assert base.conditions[0].verification == "confirm_offer_accepted"
    assert RouteQualification.CONDITIONAL_OFFER in base.qualifications
    assert [m.route_minor for m in none.ledgers.income.months] == [0, 0, 0, 0]


@pytest.mark.req("FUNDING-03", "FIN1-10")
def test_support_paid_to_the_provider_or_to_the_person_is_counted_once() -> None:
    waiver = support(paid_to="provider", kind=InstrumentKind.FEE_WAIVER)
    grant = support(amount=30000)
    to_provider = check(person(), option("c", payments=((0, 30000),), supports=(waiver,)))
    to_person = check(person(opening=30000), option("c", payments=((0, 30000),), supports=(grant,)))

    month = to_provider.ledgers.direct.months[0]
    assert (month.payments_minor, month.paid_to_provider_minor) == (0, 30000)
    assert to_provider.ledgers.liquidity.months[0].later_receipts_minor == 0  # neither side
    assert to_provider.direct_cost is not None
    assert to_provider.direct_cost.minor_units == 0
    cash = to_person.ledgers.liquidity.months[0]
    assert (cash.payments_minor, cash.later_receipts_minor) == (30000, 30000)  # both sides
    assert to_person.direct_cost is not None
    assert to_person.direct_cost.minor_units == 0  # never -£300


@pytest.mark.req("FUNDING-04", "FIN1-10")
def test_a_loan_is_never_planned_and_existing_debt_is_a_fixed_commitment() -> None:
    with pytest.raises(ValidationError, match="loan is information"):
        support(amount=30000, kind=InstrumentKind.LOAN)

    debt = ExistingDebt(
        debt_id="card",
        monthly_repayment_minor=10000,
        balance_minor=50000,
        annual_interest_bps=1200,
        cited=CONSTRUCTED,
    )
    result = check(person(horizon=2, opening=100000, existing_debts=[debt]), option("c"))

    assert [m.debt_service_minor for m in result.ledgers.liquidity.months] == [10000, 10000]
    [ledger] = result.ledgers.debts
    assert [(m.interest_minor, m.closing_minor) for m in ledger.months] == [
        (500, 40500),  # 1% a month on £500
        (405, 30905),
    ]


@pytest.mark.req("FUNDING-05")
@pytest.mark.parametrize(
    ("eligibility", "counted"),
    [
        (EligibilityStatus.CONFIRMED, True),
        (EligibilityStatus.POTENTIALLY_ELIGIBLE, True),
        (EligibilityStatus.INELIGIBLE, False),
        (EligibilityStatus.INSUFFICIENT_INFORMATION, False),
    ],
)
def test_a_funded_scenario_sits_beside_the_unfunded_one_with_a_blocking_verification(
    eligibility: EligibilityStatus, counted: bool
) -> None:
    hoped = support(amount=20000, eligibility=eligibility, award=AwardState.APPLIED, assumed=True)
    course = option("c", payments=((0, 30000),), supports=(hoped,))
    evaluation = evaluate_route(compile_input(person(opening=100000), catalogue_of(course)), ["c"])
    funded, unfunded = evaluation.scenario(Scenario.BASE), evaluation.scenario(Scenario.NO_AWARD)

    assert funded.direct_cost is not None
    assert unfunded.direct_cost is not None
    assert funded.direct_cost.minor_units == (10000 if counted else 30000)
    assert unfunded.direct_cost.minor_units == 30000
    assert [c.verification for c in funded.conditions] == (
        ["verify_funding_award"] if counted else []
    )
    assert (RouteQualification.CONDITIONAL_AWARD in funded.qualifications) is counted
    assert unfunded.conditions == []


@pytest.mark.req("FUNDING-05")
def test_only_an_approved_award_counts_in_every_scenario() -> None:
    approved = support(amount=20000)
    course = option("c", payments=((0, 30000),), supports=(approved,))
    evaluation = evaluate_route(compile_input(person(opening=100000), catalogue_of(course)), ["c"])

    for result in evaluation.checks:
        assert result.direct_cost is not None
        assert result.direct_cost.minor_units == 10000
        assert result.conditions == []
    with pytest.raises(ValidationError, match="confirmed eligibility"):
        support(amount=1, eligibility=EligibilityStatus.POTENTIALLY_ELIGIBLE)


# Scenarios: an accepted offer gates both experience and wages (S5.6, FIN1-04, PLN-08).


def _job_readiness() -> ReadinessBasis:
    row = "fixture:supervised-task"
    outcome = PlannedOutcome(
        outcome_id="outcome:job",
        offering_id="offering:job",
        option_id="concept:job",
        option_title="job",
        skill_id=row,
        outcome_type=OutcomeType.SKILL_LEVEL,
        level_on_completion=2,
        evidence_kind=EvidenceKind.ASSESSED_WORK_SAMPLE,
        confidence=Confidence.PROVISIONAL,
        source_span=OutcomeSpan(
            claim_id=None,
            source_id="fixture:constructed",
            source_hash="0" * 64,
            start=0,
            end=10,
            pointer=None,
            retrieved_at=None,
            excerpt="supervised task, assessed by the employer",
        ),
        rubric_version="fixture-rubric-1",
        review_state=OutcomeReview.ACCEPTED_ASSUMPTION,
        provenance=Provenance.PROVIDER_CLAIM,
        as_of=JAN,
    )
    return ReadinessBasis(
        matrix=synthetic_matrix("Synthetic target", [skill_row(row, 2, "fixture-rubric-1")]),
        evidence=[self_report(row, 1, "fixture-rubric-1")],
        statements=[],
        outcomes=[outcome],
        evidence_version=1,
    )


@pytest.mark.req("FIN1-04", "PLN-05", "PLN-08", "PLN-04")
def test_delay_and_no_offer_change_both_the_time_and_the_income() -> None:
    job = option(
        "job",
        kind=ActionKind.WORK,
        finish=date(2027, 3, 31),
        hours=30,
        wage=120000,
        offer=OfferGate(accepted=False, role_class="supervised data role"),
    )
    monthly = compile_input(person(horizon=6), catalogue_of(job), readiness=_job_readiness())
    evaluation = evaluate_route(monthly, ["job"])
    base, delay, none = (evaluation.scenario(s) for s in Scenario if s is not Scenario.NO_AWARD)

    assert evaluation.delay_months == 2
    assert (base.months_to_readiness, base.readiness_month) == (3, "2027-04")
    assert [m.route_minor for m in base.ledgers.income.months] == [120000] * 3 + [0] * 3
    assert (delay.months_to_readiness, delay.readiness_month) == (5, "2027-06")
    assert [m.route_minor for m in delay.ledgers.income.months] == [0, 0] + [120000] * 3 + [0]
    assert none.months_to_readiness is None
    assert none.verdict is Verdict.READINESS_NOT_REACHED
    assert sum(m.route_minor for m in none.ledgers.income.months) == 0


# OPTN-09: a proposed record never enters an unqualified "affordable and feasible" result.


@pytest.mark.req("OPTN-09")
def test_a_qualified_readiness_never_gives_an_unqualified_verdict() -> None:
    def verdict(state: RecordState, *, synthetic: bool) -> RouteCheck:
        course = option(
            "job", state=state, synthetic=synthetic, kind=ActionKind.WORK,
            finish=date(2027, 3, 31), offer=OfferGate(accepted=True),
        )  # fmt: skip
        inputs = person(horizon=6, synthetic=synthetic)
        return check(inputs, course, readiness=_job_readiness())

    proposed = verdict(RecordState.PROPOSED, synthetic=False)
    reviewed = verdict(RecordState.REVIEWED, synthetic=False)

    assert proposed.verdict is Verdict.QUALIFIED
    assert RouteQualification.PROPOSED_RECORDS in proposed.qualifications
    # Every record of the route reviewed, yet its readiness rests on an accepted assumption,
    # a proposed rubric and a provisional matrix: each is named, and the verdict is qualified
    # (R9; spec section 10: an accepted provisional mapping supports no unqualified claim).
    assert reviewed.verdict is Verdict.QUALIFIED
    assert reviewed.readiness_qualifications
    assert set(reviewed.readiness_qualifications) <= set(reviewed.qualifications)
    assert {
        Qualification.PROVISIONAL_MATRIX,
        Qualification.PROPOSED_RUBRICS,
        Qualification.PLANNED_OUTCOME_ASSUMPTION,
    } <= set(reviewed.qualifications)
    assert verdict(RecordState.REVIEWED, synthetic=True).verdict is Verdict.QUALIFIED


@pytest.mark.req("PLN-03")
def test_one_concept_per_exclusive_group_and_at_most_six_actions() -> None:
    grouped = check(person(), option("a", group="core"), option("b", group="core"))
    seven = [option(f"o{n}") for n in range(7)]
    monthly = compile_input(person(), catalogue_of(*seven))

    assert codes(grouped) == {"exclusive_group"}
    with pytest.raises(NessaError) as refused:
        check_route(monthly, [v.variant_id for _, _, v in seven])
    assert refused.value.code is ErrorCode.MODEL_SCOPE_EXCEEDED


@pytest.mark.req("OPTN-03", "PLN-06")
def test_stated_entry_requirements_keep_a_route_unresolved_until_the_person_confirms() -> None:
    concept, offering, variant = option("course")
    required = concept.model_copy(
        update={"entry_requirements": [Fact(field="entry_requirement", value="GCSE maths")]}
    )
    met = variant.model_copy(update={"entry_requirements_met": True})

    unconfirmed = check(person(), (required, offering, variant))
    confirmed = check(person(), (required, offering, met))

    assert codes(unconfirmed) == {"entry_requirements_unconfirmed"}
    assert unconfirmed.feasibility is Feasibility.UNRESOLVED
    assert confirmed.feasibility is Feasibility.FEASIBLE


# Fix round 1: unknown limits, payments before the start, delayed awards, existing debt.


@pytest.mark.req("FIN1-06", "TIME1-05")
@pytest.mark.parametrize(
    ("limit", "field"),
    [
        ("direct_spend_cap", "direct_spend_cap_minor"),
        ("monthly_payment_cap", "monthly_payment_cap_minor"),
        ("reserve", "reserve_minor"),
    ],
)
def test_an_unknown_hard_limit_is_unresolved_never_a_pass(limit: str, field: str) -> None:
    inputs = person(opening=100000).model_copy(update={field: None})
    result = check(inputs, option("course", payments=((0, 5000),)))

    [found] = result.findings
    assert (found.code, found.kind, found.reason) == (
        FindingCode.LIMIT_UNKNOWN,
        FindingKind.UNRESOLVED,
        limit,
    )
    assert result.feasibility is Feasibility.UNRESOLVED
    # The deficit cap applies only when the person sets one: absent, it is no finding.
    assert codes(check(person(opening=100000), option("course"))) == set()


@pytest.mark.req("FIN1-02", "ECON-04")
def test_a_payment_due_before_the_planning_start_is_named_never_dropped() -> None:
    # The review's probe: a February course with a £500 deposit due 15 December 2026.
    course = option(
        "course",
        start=FEB,
        finish=date(2027, 2, 28),
        payments=((0, 10000),),
        due=((date(2026, 12, 15), 50000),),
    )
    result = check(person(horizon=3, opening=100000), course)

    [found] = result.findings
    assert (found.code, found.kind, found.amount) == (
        FindingCode.PAYMENT_BEFORE_START,
        FindingKind.UNRESOLVED,
        50000,
    )
    assert found.reason is not None
    assert "2026-12-15" in found.reason
    assert result.direct_cost is None  # whether it was paid is not guessed
    assert result.feasibility is Feasibility.UNRESOLVED
    assert [(i.due, i.amount_minor) for i in result.ledgers.direct.before_start] == [
        ("2026-12-15", 50000)
    ]


@pytest.mark.req("FUNDING-05", "PLN-08")
def test_a_delayed_award_to_the_provider_leaves_the_person_paying_until_it_arrives() -> None:
    # The review's probe: an assumed fee waiver paid to the provider.
    waiver = support(
        paid_to="provider",
        kind=InstrumentKind.FEE_WAIVER,
        eligibility=EligibilityStatus.POTENTIALLY_ELIGIBLE,
        award=AwardState.APPLIED,
        assumed=True,
    )
    course = option(
        "c",
        finish=date(2027, 3, 31),
        payments=((0, 10000), (1, 10000), (2, 10000)),
        supports=(waiver,),
    )
    evaluation = evaluate_route(
        compile_input(person(horizon=3, opening=100000), catalogue_of(course)), ["c"]
    )

    def paid(scenario: Scenario) -> list[int]:
        return [m.payments_minor for m in evaluation.scenario(scenario).ledgers.direct.months]

    assert paid(Scenario.BASE) == [0, 0, 0]
    assert paid(Scenario.DELAY) == [10000, 10000, 0]  # the award arrives two months late
    assert paid(Scenario.NO_AWARD) == [10000, 10000, 10000]


@pytest.mark.req("FIN1-10", "FIN1-06")
def test_existing_debt_repayments_count_inside_the_monthly_payment_cap() -> None:
    # Spec section 12: P_m + R_m <= M_m.
    debt = ExistingDebt(
        debt_id="card", monthly_repayment_minor=10000, balance_minor=None, cited=CONSTRUCTED
    )
    inputs = person(opening=100000, monthly_cap=20000, existing_debts=[debt])

    over = check(inputs, option("course", payments=((0, 15000),)))
    within = check(inputs, option("course", payments=((0, 10000),)))

    assert finding(over, FindingCode.MONTHLY_PAYMENT_CAP) == [("2027-01", 25000)]
    assert within.feasibility is Feasibility.FEASIBLE  # 10000 + 10000 = 20000, at the cap
