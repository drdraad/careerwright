"""The search against an independent Cartesian-product oracle on generated tiny instances
(spec section 12, OPT-1; S6.6; plan section 7). The oracle (`tests/support/route_oracle.py`)
shares no code with the search or the route checker. Generated instances reach every rule the
pruning rests on (both spend caps, work patterns, sessions, workload, prerequisites, exclusive
groups, bridge roles, every unknown that sets an option aside) and the ones it must never prune
on (the reserve, receipts, support, debt, the deficit cap, applications, economic cost)."""

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
    OfferGate,
    Offering,
    Recurring,
    Session,
    Support,
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
    compile_input,
)
from careerwright.planning.search import Coverage, Outcome, search_routes
from tests.support.planning import (
    CONSTRUCTED,
    START,
    catalogue_of,
    gbp,
    month_end,
    month_start,
    option,
    pattern,
    person,
    readiness_of,
    support,
    undated_relief,
)
from tests.support.route_oracle import Oracle

ROWS = ("fixture:row-one", "fixture:row-two")
GATES = ("gate:one", "gate:two")
FEE = st.integers(min_value=0, max_value=40_000)
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
    return support(
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


@st.composite
def variant(
    draw: st.DrawFn, name: str, concept: str, horizon: int, group: str | None, unknowns: bool
) -> Option:
    def unknown() -> bool:
        return unknowns and odds(draw, 30)

    begins = month_start(START, draw(st.integers(min_value=0, max_value=horizon)))
    dated = not unknown()
    kind = ActionKind.WORK if odds(draw, 6) else ActionKind.LEARNING
    offered = kind is ActionKind.WORK or odds(draw, 10)
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
    concept_record, offering, chosen = option(
        name,
        start=begins if dated else None,
        finish=month_end(begins, draw(st.integers(min_value=1, max_value=3))) if dated else None,
        hours=None if unknown() else draw(st.integers(min_value=0, max_value=12)),
        payments=tuple(
            draw(st.lists(st.tuples(st.integers(min_value=0, max_value=horizon), FEE), max_size=2))
        ),
        due=((date(2026, 12, 15), draw(FEE)),) if unknown() else (),
        kind=kind,
        pattern=work_pattern(draw) if odds(draw, 3) else None,
        wage=draw(st.integers(min_value=0, max_value=100_000)) if offered else None,
        supports=(funding(draw),) if odds(draw, 4) else (),
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
    if odds(draw, 6):
        debts = [
            ExistingDebt(
                debt_id="debt:constructed",
                monthly_repayment_minor=draw(st.integers(min_value=0, max_value=20_000)),
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
    return compile_input(inputs, catalogue_of(*options), readiness=basis)


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


@pytest.mark.req("OPT1-08", "OPT1-02", "OPT1-07")
@SLOW
@example(monthly=undated_relief())  # review 13a, Important 1
@given(monthly=INSTANCES)
def test_the_search_finds_exactly_the_oracle_s_feasible_schedules_objectives_and_layers(
    monthly: MonthlyInput,
) -> None:
    result = search_routes(monthly)
    oracle = Oracle(monthly).solve()
    found = {frozenset(s.route): s for s in result.schedules}

    assert result.coverage is Coverage.COMPLETE
    assert {r: (s.months_to_readiness, s.objective_cost.minor_units) for r, s in found.items()} == (
        oracle.archive
    )
    assert {r: s.layer for r, s in found.items()} == {
        r: (n if n <= 3 else None) for r, n in oracle.layers.items()
    }
    assert result.feasible_without_milestone == oracle.without_milestone
    # "No route" is said only when it is true, and never when something is unknown.
    if result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL:
        assert not oracle.archive
        assert not oracle.something_unknown
    if oracle.something_unknown and not oracle.archive:
        assert result.outcome is Outcome.UNRESOLVED
    # Every candidate the search checked is one the oracle's tree holds, once each.
    assert result.expanded_states <= len(oracle.checks)


@pytest.mark.req("OPT1-08")
@SLOW
@given(monthly=INSTANCES)
def test_the_independent_checker_agrees_with_the_route_checker_on_every_candidate(
    monthly: MonthlyInput,
) -> None:
    oracle = Oracle(monthly)

    for route in oracle.routes():
        mine = oracle.check(route)
        theirs = check_route(monthly, sorted(route))
        assert mine.status == STATUS[theirs.feasibility], sorted(route)
        if mine.status == "feasible":
            assert mine.months == theirs.months_to_readiness, sorted(route)
            cost = theirs.objective_cost.minor_units if theirs.objective_cost else None
            assert mine.cost == cost, sorted(route)
