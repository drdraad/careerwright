"""The search against an independent Cartesian-product oracle on generated tiny instances
(spec section 12, OPT-1; S6.6; plan section 7). The oracle (`tests/support/route_oracle.py`)
shares no code with the search or the route checker. Generated instances reach every rule the
pruning rests on (both spend caps, repayments alone above the payment cap, work patterns,
sessions, workload, prerequisites, exclusive groups, bridge roles, two offers still to accept,
every unknown that sets an option aside, Task 12a's included: a "no" to the entry requirements,
unconfirmed eligibility conditions, supports not confirmed to stack, work rights not known to
be held, Task 12c's tuition fee loan with no amount) and the ones it must never prune on (the
reserve, receipts, support, debt, the deficit cap, applications, economic cost). Task 12c's
tuition fee loan paid to the provider comes in every state (approved, applied for, not applied
for, refused, any eligibility, no amount), and what it pays must agree too."""

from datetime import date, time

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from careerwright.planning.catalogue import (
    ActionConcept,
    ActionKind,
    AwardState,
    EligibilityStatus,
    Fact,
    FundingInstrument,
    InstrumentKind,
    OfferGate,
    Offering,
    RecordState,
    Recurring,
    Session,
    Support,
    TuitionFeeLoan,
    Variant,
    WorkPattern,
    WorkPatternKind,
)
from careerwright.planning.checker import Feasibility, check_route
from careerwright.planning.compiler import (
    Commitment,
    ExistingDebt,
    MonthlyInput,
    ReceiptTiming,
    WorkRights,
    compile_input,
)
from careerwright.planning.layers import peel
from careerwright.planning.ledgers import LoanToRepay
from careerwright.planning.search import SearchCoverage, search_routes
from tests.support.planning import (
    CONSTRUCTED,
    START,
    catalogue_of,
    gbp,
    loan_statuses,
    month_end,
    month_start,
    option,
    pattern,
    person,
    readiness_of,
    repayments_beside_an_unknown,
    support,
    tuition_loan,
    undated_relief,
)
from tests.support.route_oracle import Oracle

ROWS = ("fixture:row-one", "fixture:row-two")
GATES = ("gate:one", "gate:two")
CONDITIONS = ("eligibility_age", "eligibility_residency")
SCHEMES = ("funding:one", "funding:two")
FEE = st.integers(min_value=0, max_value=40_000)
BIG_FEE = st.integers(min_value=0, max_value=300_000)  # a university's fee, above most caps
SLOW = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
STATUS = {
    Feasibility.FEASIBLE: "feasible",
    Feasibility.NOT_FEASIBLE_IN_MODEL: "not_feasible",
    Feasibility.UNRESOLVED: "unresolved",
}
Option = tuple[ActionConcept, Offering, Variant]


def odds(draw: st.DrawFn, one_in: int) -> bool:
    """True about once in `one_in` draws."""
    return draw(st.integers(min_value=1, max_value=one_in)) == 1


def work_pattern(draw: st.DrawFn) -> WorkPattern:
    return pattern(
        draw(st.sampled_from(WorkPatternKind)),
        draw(st.integers(min_value=0, max_value=35)),
        draw(st.integers(min_value=50_000, max_value=250_000)),
    )


def funding(draw: st.DrawFn) -> Support:
    to_provider = draw(st.booleans())
    approved = draw(st.booleans())
    granted = support(
        paid_to="provider" if to_provider else "person",
        amount=None if to_provider and odds(draw, 3) else draw(FEE),
        month=draw(st.integers(min_value=0, max_value=2)),
        eligibility=EligibilityStatus.CONFIRMED
        if approved
        else draw(st.sampled_from(EligibilityStatus)),
        award=AwardState.APPROVED
        if approved
        else draw(st.sampled_from([AwardState.NOT_APPLIED, AwardState.APPLIED])),
        assumed=not approved and draw(st.booleans()),
        early=draw(st.booleans()),
    )
    # Two schemes, so one scheme now and then pays for two options (review 12a, Important 2).
    return granted.model_copy(update={"instrument_id": draw(st.sampled_from(SCHEMES))})


def fee_loan(draw: st.DrawFn, unknowns: bool) -> TuitionFeeLoan:
    """A tuition fee loan paid to the provider (Task 12c) in any of its statuses: approved, not
    yet applied for or applied for, refused, with any eligibility; now and then no amount."""
    approved = draw(st.booleans())
    return tuition_loan(
        None if unknowns and odds(draw, 4) else draw(BIG_FEE),
        application=AwardState.APPROVED
        if approved
        else draw(
            st.sampled_from([AwardState.NOT_APPLIED, AwardState.APPLIED, AwardState.REFUSED])
        ),
        eligibility=EligibilityStatus.CONFIRMED
        if approved
        else draw(st.sampled_from(EligibilityStatus)),
    )


@st.composite
def variant(
    draw: st.DrawFn, name: str, concept: str, horizon: int, group: str | None, unknowns: bool
) -> Option:
    def unknown() -> bool:
        return unknowns and odds(draw, 30)

    begins = month_start(START, draw(st.integers(min_value=0, max_value=horizon)))
    dated = not unknown()
    kind = (
        ActionKind.WORK
        if odds(draw, 6)
        else ActionKind.APPRENTICESHIP
        if odds(draw, 6)
        else ActionKind.LEARNING
    )
    offered = kind is not ActionKind.LEARNING or odds(draw, 10)
    # An eligible learner's fee (review 13a, C07): each condition confirmed or not.
    conditions = (
        [Fact(field=field, value="a stated condition") for field in CONDITIONS]
        if odds(draw, 5)
        else []
    )
    statuses = {
        field: draw(st.sampled_from(EligibilityStatus))
        for field in CONDITIONS
        if bool(conditions) and draw(st.booleans())
    }
    deadline = None
    if odds(draw, 12):  # a deadline at the end of December 2026 has passed by the start
        deadline = month_end(START, draw(st.integers(min_value=0, max_value=horizon)))
    hour = draw(st.sampled_from([9, 18]))  # two Monday sessions clash when at the same hour
    sessions = [Session(weekday=0, starts=time(hour), ends=time(hour + 2))] if odds(draw, 4) else []
    recurring = None
    if odds(draw, 10):
        recurring = Recurring(
            amount=gbp(draw(st.integers(min_value=1, max_value=20_000))),
            at_least=unknowns and odds(draw, 4),
            count=None
            if unknowns and odds(draw, 3)
            else draw(st.integers(min_value=1, max_value=4)),
            cited=CONSTRUCTED,
        )
    # A tuition fee loan (Task 12c) comes with a fee for it to pay, so routes that use it are
    # reached; a fee above the caps then lets the loan make the difference.
    loan = fee_loan(draw, unknowns) if odds(draw, 3) else None
    fees = st.lists(
        st.tuples(st.integers(min_value=0, max_value=horizon), FEE if loan is None else BIG_FEE),
        min_size=0 if loan is None else 1,
        max_size=2,
    )
    concept_record, offering, chosen = option(
        name,
        start=begins if dated else None,
        finish=month_end(begins, draw(st.integers(min_value=1, max_value=3))) if dated else None,
        hours=None if unknown() else draw(st.integers(min_value=0, max_value=12)),
        payments=tuple(draw(fees)),
        due=((date(2026, 12, 15), draw(FEE)),) if unknown() else (),
        kind=kind,
        pattern=work_pattern(draw) if odds(draw, 3) else None,
        wage=draw(st.integers(min_value=0, max_value=100_000)) if offered else None,
        supports=tuple(funding(draw) for _ in range(draw(st.sampled_from([0, 0, 0, 1, 2])))),
        stacking_confirmed=draw(st.booleans()),
        tuition_fee_loan=loan,
        condition_statuses=statuses,
        eligibility_conditions=conditions,
        offer=OfferGate(accepted=draw(st.booleans()), role_class="synthetic role")
        if offered
        else None,
        unknown_cost="not stated" if unknown() else None,
        recurring=recurring,
        group=group,
        concept=concept,
        sessions=sessions,
        grants=[draw(st.sampled_from(GATES))] if odds(draw, 3) else [],
        prerequisites=[draw(st.sampled_from(GATES))] if odds(draw, 5) else [],
        application_deadline=deadline,
        application_gate="gate:one" if deadline is not None else None,
    )
    if unknown():
        concept_record = concept_record.model_copy(
            update={"entry_requirements": [Fact(field="entry", value="a stated requirement")]}
        )
        # Not yet answered, or the person's own yes or no.
        met = draw(st.sampled_from([None, True, False]))
        chosen = chosen.model_copy(update={"entry_requirements_met": met})
    return concept_record, offering, chosen


@st.composite
def instances(draw: st.DrawFn, *, unknowns: bool) -> MonthlyInput:
    """A person and two to four concepts of one or two starts each, over up to six months.
    With `unknowns`, now and then a limit, a date, a cost, an hour count, an entry
    confirmation or the person's evidence is not stated."""
    horizon = draw(st.integers(min_value=1, max_value=6))
    economic = draw(st.booleans())

    def unknown() -> bool:
        return unknowns and odds(draw, 40)

    def limit(low: int, high: int) -> int | None:
        return None if unknown() else draw(st.integers(min_value=low, max_value=high))

    debts = []
    if odds(draw, 5):
        # Now and then repayments alone above the monthly payment cap (session 2, D15).
        most = 120_000 if odds(draw, 2) else 20_000
        debts = [
            ExistingDebt(
                debt_id="debt:constructed",
                monthly_repayment_minor=draw(st.integers(min_value=0, max_value=most)),
                balance_minor=draw(st.one_of(st.none(), st.integers(0, 100_000))),
                annual_interest_bps=draw(st.one_of(st.none(), st.integers(0, 3_000))),
                cited=CONSTRUCTED,
            )
        ]
    commitments = [
        Commitment(label="care", hours_per_week=draw(st.integers(0, 8)), cited=CONSTRUCTED)
    ]
    # Mostly a person who could take something on: pay above living costs, some savings, a
    # few hours to spare; sometimes none of that.
    pay = draw(st.integers(min_value=0, max_value=250_000))
    hours = draw(st.integers(min_value=0, max_value=35))
    living_top = 250_000 if odds(draw, 6) else pay
    inputs = person(
        horizon=horizon,
        opening=draw(st.integers(min_value=0, max_value=400_000)),
        living=draw(st.integers(min_value=0, max_value=living_top)),
        reserve=limit(0, 20_000),
        pay=pay,
        hours=hours,
        availability=None if unknown() else hours + draw(st.integers(min_value=0, max_value=25)),
        baseline=None if economic and unknown() else draw(st.integers(0, 250_000)),
        objective="economic" if economic else "direct_spending",
        timing=draw(st.sampled_from(ReceiptTiming)),
        direct_cap=limit(40_000, 200_000),
        monthly_cap=limit(30_000, 100_000),
        monthly_deficit_cap_minor=draw(st.integers(0, 300_000)) if odds(draw, 8) else None,
        commitments=commitments if odds(draw, 5) else [],
        existing_debts=debts,
        initial_gates=[draw(st.sampled_from(GATES))] if odds(draw, 4) else [],
        work_rights=draw(st.sampled_from([WorkRights.UNKNOWN, WorkRights.NOT_HELD]))
        if unknown()
        else WorkRights.HELD,
        # The person sometimes confirms the first scheme may pay for several options.
        shared_schemes=[SCHEMES[0]] if odds(draw, 3) else [],
    )
    options = []
    for c in range(draw(st.integers(min_value=2, max_value=4))):
        group = "group:shared" if odds(draw, 4) else None
        for s in range(draw(st.integers(min_value=1, max_value=2))):
            options.append(draw(variant(f"v{c}{s}", f"c{c}", horizon, group, unknowns)))
    rows = ROWS[: draw(st.integers(min_value=1, max_value=2))]
    teaches = {
        o.offering_id: tuple(draw(st.lists(st.sampled_from(rows), unique=True)))
        for _, o, _ in options
    }
    basis = readiness_of(teaches, rows=rows, current=2 if odds(draw, 8) else 1)
    if unknowns and odds(draw, 12):
        basis = basis.model_copy(update={"evidence": []})  # nothing said yet: not level 0
    catalogue = catalogue_of(*options)
    if odds(draw, 3):  # the catalogue records the two schemes as exclusive of each other
        catalogue = catalogue.model_copy(update={"instruments": [exclusive_schemes()]})
    return compile_input(inputs, catalogue, readiness=basis)


def borrowed(loans: list[LoanToRepay]) -> int | None:
    """What a route's tuition fee loans pay in all, or None where an amount is not known."""
    if any(loan.amount is None for loan in loans):
        return None
    return sum(loan.amount.minor_units for loan in loans if loan.amount is not None)


def exclusive_schemes() -> FundingInstrument:
    return FundingInstrument(
        instrument_id=SCHEMES[0],
        programme=None,
        kind=InstrumentKind.GRANT,
        jurisdiction="GB-ENG",
        review_state=RecordState.ACCEPTED_ASSUMPTION,
        exclusive_with=[SCHEMES[1]],
    )


# Both families in each test: with unknowns (the result must stay unresolved, never "no
# route"), and with none (dense archives, so the layers and the pruning rules are reached).
INSTANCES = st.one_of(instances(unknowns=True), instances(unknowns=False))


@pytest.mark.req("OPT1-07")
def test_the_oracle_counts_an_option_s_own_unknown_as_something_unknown() -> None:
    oracle = Oracle(undated_relief()).solve()

    # Every route breaks the workload limit as stated, but the undated option's dates might
    # lower the job's hours once known (review 13a, Important 1).
    assert not oracle.archive
    assert all(c.status == "not_feasible" for c in oracle.checks.values())
    assert oracle.something_unknown
    assert oracle.outcome == "unresolved"


# Task 12a fix round 1, read again by the oracle.


@pytest.mark.req("OPT1-08", "OPT1-07", "FIN1-06")
def test_the_oracle_says_no_route_where_repayments_alone_break_the_cap_whatever_is_unknown() -> (
    None
):
    oracle = Oracle(repayments_beside_an_unknown()).solve()

    # Whatever the unpriced course costs, no option lowers a repayment.
    assert oracle.repayments_rule_out_every_route
    assert not oracle.archive
    assert oracle.outcome == "no_route_in_bounded_model"


@pytest.mark.req("OPT1-08", "PLN-06")
def test_the_oracle_holds_one_scheme_on_two_options_open_and_exclusive_schemes_broken() -> None:
    waiver = support(paid_to="provider", amount=None).model_copy(
        update={"instrument_id": SCHEMES[0]}
    )
    other = support(paid_to="provider", amount=1000).model_copy(
        update={"instrument_id": SCHEMES[1]}
    )
    options = [
        option("first", payments=((0, 5000),), supports=(waiver,)),
        option("second", payments=((0, 5000),), supports=(waiver,)),
        option("third", payments=((0, 5000),), supports=(other,)),
    ]
    teaches = {f"offering:{n}": (ROWS[0],) for n in ("first", "second", "third")}
    readiness = readiness_of(teaches, rows=ROWS[:1])
    funds = person(opening=1_000_000)  # the reserve is another rule
    plain = Oracle(compile_input(funds, catalogue_of(*options), readiness=readiness))
    exclusive = catalogue_of(*options).model_copy(update={"instruments": [exclusive_schemes()]})
    recorded = Oracle(compile_input(funds, exclusive, readiness=readiness))
    confirms = funds.model_copy(update={"shared_schemes": [SCHEMES[0]]})
    shared = Oracle(compile_input(confirms, catalogue_of(*options), readiness=readiness))

    assert plain.check(frozenset({"first", "second"})).status == "unresolved"
    assert shared.check(frozenset({"first", "second"})).status == "feasible"
    assert plain.check(frozenset({"first", "third"})).status == "feasible"
    assert recorded.check(frozenset({"first", "third"})).status == "not_feasible"


@pytest.mark.req("OPT1-08", "TIME1-03")
def test_the_oracle_reads_a_course_behind_an_application_as_conditional_never_not_feasible() -> (
    None
):
    applied = option(
        "applied",
        start=month_start(START, 2),
        finish=month_end(START, 3),
        application_deadline=month_end(START, 1),
        application_gate="admission:offering:applied",
    )
    readiness = readiness_of({"offering:applied": (ROWS[0],)}, rows=ROWS[:1])
    oracle = Oracle(compile_input(person(horizon=4), catalogue_of(applied), readiness=readiness))

    assert oracle.check(frozenset({"applied"})).status == "feasible"


@pytest.mark.req("OPT1-08", "FUNDING-06")
def test_the_oracle_reads_a_tuition_fee_loan_in_every_state() -> None:
    oracle = Oracle(loan_statuses())

    def alone(name: str) -> tuple[str, int | None, int | None]:
        checked = oracle.check(frozenset({name}))
        return checked.status, checked.cost, checked.borrowed

    # Approved, applied for or not yet applied for: the £9,000 is the lender's, not the
    # student's, so £1,500 limits hold (the last two rest on approval, beside the self-paid
    # route the search does not read).
    assert alone("approved") == ("feasible", 0, 900_000)
    assert alone("applied") == ("feasible", 0, 900_000)
    assert alone("not-applied") == ("feasible", 0, 900_000)
    # Refused, or for someone ineligible: the student pays, beyond their limits.
    assert alone("refused") == ("not_feasible", 900_000, 0)
    assert alone("ineligible") == ("not_feasible", 900_000, 0)
    # No amount: unresolved, never £0.
    assert alone("no-amount") == ("unresolved", None, None)
    # A £1,000 grant first, then a £7,500 loan: £500 is the student's, in March.
    assert alone("part-loan") == ("feasible", 50_000, 750_000)
    assert oracle.solve().outcome == "routes_found"


@pytest.mark.req("OPT1-08", "OPT1-02", "OPT1-07")
@SLOW
@example(monthly=undated_relief())  # review 13a, Important 1
@example(monthly=repayments_beside_an_unknown())  # review 12a, Important 3
@example(monthly=loan_statuses())  # Task 12c: the tuition fee loan in every state
@given(monthly=INSTANCES)
def test_the_search_finds_exactly_the_oracle_s_feasible_schedules_objectives_and_layers(
    monthly: MonthlyInput,
) -> None:
    result = search_routes(monthly)
    oracle = Oracle(monthly).solve()
    found = {frozenset(s.route): s for s in result.schedules}

    assert result.coverage is SearchCoverage.COMPLETE
    assert {r: (s.months_to_readiness, s.objective_cost.minor_units) for r, s in found.items()} == (
        oracle.archive
    )
    assert {r: s.layer for r, s in found.items()} == {
        r: (n if n <= 3 else None) for r, n in oracle.layers.items()
    }
    assert {r: borrowed(s.loans_to_repay) for r, s in found.items()} == {
        r: oracle.checks[r].borrowed for r in oracle.archive
    }
    assert result.feasible_without_milestone == oracle.without_milestone
    # Both directions (review 12a, Important 3): "no route" exactly when the oracle proves it,
    # "unresolved" exactly when something unknown could still change the answer.
    assert result.outcome.value == oracle.outcome
    # Every candidate the search checked is one the oracle's tree holds, once each.
    assert result.expanded_states <= len(oracle.checks)


@pytest.mark.req("OPT1-11")
@SLOW
@example(monthly=undated_relief())
@given(monthly=INSTANCES)
def test_the_rank_stage_s_layers_equal_iterative_peeling_on_every_complete_search(
    monthly: MonthlyInput,
) -> None:
    # S6.8: the efficient layering, qualified against Sprint 6a's peeling on the same archive.
    result = search_routes(monthly)
    points = [(s.months_to_readiness, s.objective_cost.minor_units) for s in result.schedules]

    assert result.coverage is SearchCoverage.COMPLETE
    assert [s.layer for s in result.schedules] == peel(points)


@pytest.mark.req("OPT1-08", "FUNDING-06")
@SLOW
@example(monthly=loan_statuses())
@given(monthly=INSTANCES)
def test_the_independent_checker_agrees_with_the_route_checker_on_every_candidate(
    monthly: MonthlyInput,
) -> None:
    oracle = Oracle(monthly)

    for route in oracle.routes():
        mine = oracle.check(route)
        theirs = check_route(monthly, sorted(route))
        assert mine.status == STATUS[theirs.feasibility], sorted(route)
        # What the tuition fee loans pay, as loans to repay (Task 12c): unknown stays unknown.
        assert mine.borrowed == borrowed(theirs.loans_to_repay), sorted(route)
        if mine.status == "feasible":
            assert mine.months == theirs.months_to_readiness, sorted(route)
            cost = theirs.objective_cost.minor_units if theirs.objective_cost else None
            assert mine.cost == cost, sorted(route)
