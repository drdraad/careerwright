"""The Routes chapter's facts from real solver output (Task 14's backend half; ADR 0016
decisions 23 to 27): the comparison, the archive paged and viewed, and a chosen route's
details. Every number here comes from `search_routes` and `check_route` on the same input."""

from datetime import date
from typing import Any

import pytest

from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.money import SignedMoney
from careerwright.planning.catalogue import ActionKind, AwardState, OfferGate, RecordState
from careerwright.planning.checker import FindingCode, Scenario
from careerwright.planning.comparison import (
    COMPARATOR_RULE,
    PROJECTION_POINTS,
    DominanceReason,
    Lead,
    StepQualification,
    ViewFilter,
    comparison,
    project,
    route_detail,
    schedule_page,
)
from careerwright.planning.compiler import ExistingDebt, MonthlyInput, compile_input
from careerwright.planning.families import EqualPoint
from careerwright.planning.inputs import BaselineKind
from careerwright.planning.search import (
    M0SearchLimits,
    Narrowing,
    Outcome,
    SearchCoverage,
    SearchResult,
    search_routes,
)
from tests.support.planning import (
    CONSTRUCTED,
    START,
    catalogue_of,
    directai_fixture,
    directai_instance,
    month_end,
    month_start,
    option,
    person,
    readiness_of,
    supplied_costs,
    trace_catalogue,
    trace_inputs,
    trace_readiness,
    tuition_loan,
)

OPENING = 1_000_000


def trace() -> MonthlyInput:
    return compile_input(trace_inputs(), trace_catalogue(), readiness=trace_readiness())


def directai() -> MonthlyInput:
    inputs, catalogue, readiness = directai_instance()
    return compile_input(inputs, catalogue, readiness=readiness)


def course(name: str, *, first: int = 0, months: int = 1, **extra: Any) -> Any:
    begins = month_start(START, first)
    return option(name, start=begins, finish=month_end(begins, months), **extra)


def constructed(
    horizon: int, *options: Any, teaches: tuple[str, ...], **inputs: Any
) -> MonthlyInput:
    readiness = readiness_of({f"offering:{name}": ["fixture:route-skill"] for name in teaches})
    return compile_input(
        person(horizon=horizon, opening=OPENING, **inputs),
        catalogue_of(*options),
        readiness=readiness,
    )


def index_of(result: SearchResult, route: list[str]) -> int:
    return next(i for i, s in enumerate(result.schedules) if s.route == route)


def point_of(result: SearchResult, route: list[str]) -> int:
    s = result.schedules[index_of(result, route)]
    return next(
        i
        for i, p in enumerate(result.points)
        if (p.months_to_readiness, p.objective_cost) == (s.months_to_readiness, s.objective_cost)
    )


# The comparison.


@pytest.mark.req("TRACE01-05", "PARETO-04", "VIS2-02", "VIS2-04", "VIS2-01")
def test_trace_01_compares_a_b_c_in_f1_d_in_f2_and_e_in_f3_each_with_its_named_comparator() -> None:
    monthly = trace()
    result = search_routes(monthly)
    found = comparison(result, monthly)
    points = {p.point_id: p for p in found.points}
    letter = {point_of(result, [f"TRACE-01/{x}"]): x for x in "ABCDE"}
    by_letter = {x: points[p] for p, x in letter.items()}

    assert found.lead is Lead.BEST_TRADE_OFFS_FOUND
    assert found.code is None
    assert found.comparator_rule == COMPARATOR_RULE
    assert {x: p.layer for x, p in by_letter.items()} == dict(A=1, B=1, C=1, D=2, E=3)
    assert all(by_letter[x].comparator is None for x in "ABC")
    # D ties B at four months and costs more: bettered at the same time, on the boundary.
    d, b = by_letter["D"], by_letter["B"]
    assert d.comparator is not None
    assert letter[d.comparator.point_id] == "B"
    assert d.comparator.dominance is DominanceReason.CHEAPER_SAME_TIME
    assert d.comparator.months_sooner == 0
    assert d.comparator.cost_less.minor_units == (
        d.objective_cost.minor_units - b.objective_cost.minor_units
    )
    # E's dominators are B and D; the layer just above it holds D alone.
    e = by_letter["E"]
    assert e.comparator is not None
    assert letter[e.comparator.point_id] == "D"
    assert [letter[i] for i in e.dominators] == ["D"]
    # The cost definition beside the chart (TRACE-01: £2,000 a month, a six-month horizon).
    assert found.basis.objective_basis == "economic"
    assert (found.basis.planning_start, found.basis.horizon_months) == ("2027-01", 6)
    assert found.basis.currency == "GBP"
    assert found.basis.scenario is Scenario.BASE
    assert found.basis.baseline is not None
    assert [m.minor_units for m in found.basis.baseline.net_income_by_month] == [200000] * 6
    assert found.basis.baseline.kind is None  # a fixture's own baseline, not a stated kind
    assert found.label.name == "TRACE-01"
    assert found.label.synthetic
    assert found.limits == M0SearchLimits()
    assert (found.points_shown, found.points_total, found.schedules_total) == (5, 5, 5)
    assert found.families_shown == found.families_total == 5


@pytest.mark.req("DIRECTAI-02", "VIS2-04")
def test_the_a_to_i_fixture_compares_direct_spending_and_never_an_economic_cost() -> None:
    monthly = directai()
    result = search_routes(monthly)
    found = comparison(result, monthly)
    stated = {r["id"]: r for r in directai_fixture()["routes"]}

    assert found.basis.objective_basis == "direct_spending"
    assert found.basis.baseline is None
    page = schedule_page(result, ViewFilter())
    for item in page.items:
        [route] = item.route
        assert item.objective_cost.minor_units == item.direct_cost.minor_units
        assert item.objective_cost.minor_units == stated[route]["direct_spend_minor"]
        assert item.economic_cost is None
        assert item.layer == stated[route]["expected_layer"]
    # Every F2 and F3 point names a comparator in the layer above, in direct spending.
    for point in found.points:
        if point.layer in (2, 3):
            assert point.comparator is not None
            above = next(p for p in found.points if p.point_id == point.comparator.point_id)
            assert above.layer == point.layer - 1


@pytest.mark.req("OPT1-15", "API-02", "DUR-03")
def test_a_truncated_search_leads_with_best_trade_offs_its_size_and_what_could_help() -> None:
    monthly = directai()
    result = search_routes(monthly, limits=M0SearchLimits(max_states=4))
    found = comparison(result, monthly)

    assert result.coverage is SearchCoverage.BUDGET_TRUNCATED
    assert result.schedules  # the archive keeps what it met
    assert found.lead is Lead.BEST_TRADE_OFFS_FOUND
    assert found.code == "SOLVE_LIMIT_REACHED"
    assert not found.layers_exact
    assert found.instance == result.instance
    assert found.narrowings == [Narrowing.FEWER_CONCEPTS]
    assert {(m.horizon_months, m.starts_per_concept, m.concepts) for m in found.completes_at} == {
        (24, 1, 18),
        (24, 2, 10),
    }
    assert all(m.measured_on == date(2026, 10, 31) for m in found.completes_at)
    # A complete search names no measured size.
    assert comparison(search_routes(monthly), monthly).completes_at == []


@pytest.mark.req("PLN-12", "API-02")
def test_a_route_longer_than_the_model_is_its_own_state_never_no_route() -> None:
    # A three-year course: usable only after the 24-month model's last month.
    degree = course("degree", months=36)
    monthly = constructed(24, degree, teaches=("degree",))
    result = search_routes(monthly)
    found = comparison(result, monthly)

    assert result.coverage is SearchCoverage.COMPLETE
    assert result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    assert found.lead is Lead.LONGER_THAN_MODEL
    assert found.code is None  # never "no route"
    assert found.longer_than_model == ["degree"]
    assert found.beyond_horizon == []


@pytest.mark.req("PLN-12", "API-02")
def test_a_limit_that_rules_out_the_shorter_course_keeps_no_route_beside_a_long_degree() -> None:
    """Review 14A, Important 1: a two-month course over the direct-spend cap beside a 36-month
    degree. The long degree is not the whole reason nothing fits: the person's own limit rules
    out the shorter course, so no route leads, with its code, and the degree is named beside."""
    short = course("short", months=2, payments=((0, 500000),))
    degree = course("degree", months=36)
    monthly = constructed(24, short, degree, teaches=("short", "degree"), direct_cap=100000)
    result = search_routes(monthly)
    found = comparison(result, monthly)

    assert result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    assert found.lead is Lead.NO_ROUTE_IN_BOUNDED_MODEL
    assert found.code == "NO_ROUTE_IN_BOUNDED_MODEL"
    assert found.longer_than_model == ["degree"]
    [aside] = [s for s in found.set_aside if s.variant_id == "short"]
    assert FindingCode.DIRECT_SPEND_CAP in aside.violations  # the checker's breach, named


@pytest.mark.req("PLN-12", "API-02")
def test_a_starting_breach_keeps_no_route_beside_a_long_degree() -> None:
    """Review 14A, Important 1: repayments already above the payment cap rule out every route
    whatever its length, so no route leads, the breach named, the degree beside."""
    card = ExistingDebt(
        debt_id="card", monthly_repayment_minor=1500, balance_minor=None, cited=CONSTRUCTED
    )
    degree = course("degree", months=36)
    short = course("short", months=2)
    monthly = constructed(
        24, short, degree, teaches=("short", "degree"), monthly_cap=1000, existing_debts=[card]
    )
    result = search_routes(monthly)
    found = comparison(result, monthly)

    assert result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    assert found.lead is Lead.NO_ROUTE_IN_BOUNDED_MODEL
    assert found.code == "NO_ROUTE_IN_BOUNDED_MODEL"
    assert found.longer_than_model == ["degree"]
    assert {f.code for f in found.starting_violations} == {FindingCode.REPAYMENTS_ABOVE_PAYMENT_CAP}


@pytest.mark.req("PLN-12", "API-02")
def test_a_course_beyond_the_horizon_but_inside_the_model_is_named_and_no_route_stays_exact() -> (
    None
):
    longer = course("longer", months=10)
    monthly = constructed(6, longer, teaches=("longer",))
    result = search_routes(monthly)
    found = comparison(result, monthly)

    assert found.lead is Lead.NO_ROUTE_IN_BOUNDED_MODEL
    assert found.code == "NO_ROUTE_IN_BOUNDED_MODEL"  # only with complete coverage
    assert found.beyond_horizon == ["longer"]
    assert found.longer_than_model == []


def _points(*rows: tuple[int, int, int | None]) -> list[EqualPoint]:
    return [
        EqualPoint(
            months_to_readiness=m,
            objective_cost=SignedMoney(minor_units=c, currency="GBP"),
            layer=layer,
            routes=[[f"r{i}"]],
        )
        for i, (m, c, layer) in enumerate(rows)
    ]


@pytest.mark.req("VIS2-09")
def test_the_projection_keeps_every_ranked_point_the_extremes_and_pins_and_says_how_many() -> None:
    ranked = [(m, 1000 - m, 1) for m in range(3)]
    # Beyond F3, in order of time then cost: the soonest first, the cheapest last.
    beyond = [(10 + m, 5000 - m, None) for m in range(400)]
    points = _points(*ranked, *beyond)
    result = search_routes(directai()).model_copy(update={"points": points})

    shown = project(result, {200}, cap=50)

    assert {0, 1, 2} <= set(shown)  # every ranked point
    assert 3 in shown  # the soonest beyond F3
    assert len(points) - 1 in shown  # the cheapest beyond F3
    assert 200 in shown  # a pinned schedule's point
    assert len(shown) == 50
    assert shown == sorted(shown)
    assert project(result, set()) == sorted(project(result, set()))
    assert len(project(result, set())) == PROJECTION_POINTS


# The archive, paged and viewed.


@pytest.mark.req("VIS2-07", "FAMILY-02")
def test_a_view_hides_routes_without_changing_ranks_and_reranking_is_explicit() -> None:
    result = search_routes(directai())
    later = ViewFilter(min_months=7)

    viewed = schedule_page(result, later)
    reranked = schedule_page(result, later, rerank=True)

    assert viewed.rank_scope == "recorded"
    assert all(i.view_layer is None for i in viewed.items)
    assert all(i.months_to_readiness >= 7 for i in viewed.items)
    recorded = {i.index: result.schedules[i.index].layer for i in viewed.items}
    assert {i.index: i.layer for i in viewed.items} == recorded
    # With A (six months) hidden, D leads the view but keeps its recorded layer 2: a hidden
    # dominator never makes a route best overall.
    d = next(i for i in reranked.items if i.route == ["fixture:directai:route:D"])
    assert reranked.rank_scope == "within_view"
    assert (d.layer, d.view_layer) == (2, 1)
    assert [i.index for i in reranked.items] == [i.index for i in viewed.items]


@pytest.mark.req("VIS2-09", "FAMILY-02")
def test_pages_reach_every_retained_schedule_once_and_pins_keep_their_badge() -> None:
    result = search_routes(directai())
    seen: list[int] = []
    cursor = None
    while True:
        page = schedule_page(result, ViewFilter(), cursor=cursor, limit=2)
        assert page.total == page.retained == len(result.schedules)
        seen += [i.index for i in page.items]
        if page.next_cursor is None:
            break
        cursor = page.next_cursor
    assert seen == list(range(len(result.schedules)))

    a = index_of(result, ["fixture:directai:route:A"])
    pinned = schedule_page(result, ViewFilter(min_months=7), pinned=[a]).pinned
    assert [(p.schedule.index, p.in_view) for p in pinned] == [(a, False)]
    by_family = schedule_page(result, ViewFilter(family_id=result.schedules[a].family_id))
    assert [i.index for i in by_family.items] == [a]


# A chosen route.


@pytest.mark.req("VIS2-05", "VIS2-08", "TRACE01-05", "PLN-04", "API-04")
def test_trace_01_route_b_s_details_come_from_its_own_check() -> None:
    monthly = trace()
    result = search_routes(monthly)
    b = index_of(result, ["TRACE-01/B"])

    detail = route_detail(result, monthly, b)

    # Each cost apart: what the person pays, the pay they lose, and the economic cost.
    assert detail.costs.objective_basis == "economic"
    assert detail.costs.direct_cost is not None
    assert detail.costs.direct_cost.minor_units == 60000
    assert detail.costs.pay_difference is not None
    assert detail.costs.pay_difference.minor_units == 0
    assert detail.costs.economic_cost is not None
    assert detail.costs.economic_cost.minor_units == 60000
    assert detail.costs.peak_monthly_payment is not None
    assert detail.costs.peak_monthly_payment.minor_units == 15000
    assert detail.costs.minimum_prefunded_cash is not None
    assert detail.costs.minimum_prefunded_cash.minor_units == 485000
    assert [m.month for m in detail.months] == monthly.months
    assert sum(m.payments.minor_units for m in detail.months if m.payments) == 60000
    [step] = detail.steps
    assert step.variant_id == "TRACE-01/B"
    assert step.kind is ActionKind.LEARNING
    assert step.start_month == "2027-01"
    assert [p.amount.minor_units for p in step.payments] == [15000] * 4
    assert step.synthetic
    assert StepQualification.SYNTHETIC in step.qualified_by
    assert [r.record for r in step.records][:2] == ["concept", "offering"]
    # Readiness rests on the course's assessed completion: its verification is a milestone.
    assert [(m.kind, m.month) for m in detail.milestones] == [
        ("readiness", "2027-05"),
        ("verify_assessed_completion", "2027-05"),
    ]
    # TRACE-01 has no condition to move: every stress case is the base.
    assert [s.scenario for s in detail.scenarios] == [
        Scenario.DELAY,
        Scenario.NO_AWARD,
        Scenario.NO_OFFER,
    ]
    assert all(s.same_as_base for s in detail.scenarios)
    assert detail.self_paid is None
    assert detail.label.name == "TRACE-01"


@pytest.mark.req("FUNDING-06", "VIS2-03")
def test_a_loan_s_fee_is_a_loan_to_repay_and_one_not_approved_sits_beside_the_self_paid() -> None:
    fee = 900000
    funded = course(
        "funded",
        payments=((0, fee),),
        tuition_fee_loan=tuition_loan(fee, application=AwardState.APPLIED),
    )
    monthly = constructed(3, funded, teaches=("funded",))
    result = search_routes(monthly)

    detail = route_detail(result, monthly, index_of(result, ["funded"]))

    [loan] = detail.costs.loans_to_repay
    assert loan.amount is not None
    assert loan.amount.minor_units == fee
    assert loan.conditional
    assert loan.repayment is None
    assert detail.costs.direct_cost is not None
    assert detail.costs.direct_cost.minor_units == 0
    assert detail.self_paid is not None
    assert detail.self_paid.scenario is Scenario.NO_AWARD
    assert detail.self_paid.direct_cost is not None
    assert detail.self_paid.direct_cost.minor_units == fee
    [gate] = detail.gates
    assert (gate.kind, gate.verification, gate.month) == (
        "loan",
        "confirm_loan_approved",
        "2027-01",
    )
    assert detail.steps[0].fee_loan is not None


@pytest.mark.req("OPTN-13", "OUT1-09", "API-06")
def test_a_step_on_a_supplied_figure_or_a_proposed_record_names_why_it_is_qualified() -> None:
    monthly = supplied_costs()
    result = search_routes(monthly)
    resting = next(
        s for s in result.schedules if "supplied_figures" in [str(q) for q in s.qualifications]
    )
    detail = route_detail(result, monthly, index_of(result, resting.route))
    supplied = [s for s in detail.steps if s.supplied]
    assert supplied
    assert all(StepQualification.SUPPLIED_FIGURES in s.qualified_by for s in supplied)

    proposed = course("researched", state=RecordState.PROPOSED)
    monthly = constructed(2, proposed, teaches=("researched",))
    result = search_routes(monthly)
    [step] = route_detail(result, monthly, index_of(result, ["researched"])).steps
    assert StepQualification.PROPOSED_RECORD in step.qualified_by
    assert {r.review_state for r in step.records} == {RecordState.PROPOSED}
    assert step.title == "researched"
    assert all(c.basis.value != "person" for c in step.sources)


@pytest.mark.req("VIS2-05", "VIS2-08", "OPTN-04")
def test_the_gantt_shows_waits_before_a_start_and_an_offer_s_gate() -> None:
    later = course("later", first=2)
    job = course(
        "job",
        first=0,
        months=3,
        kind=ActionKind.WORK,
        wage=150000,
        offer=OfferGate(accepted=False, role_class="analyst"),
    )
    monthly = constructed(6, later, job, teaches=("later",))
    result = search_routes(monthly)

    alone = route_detail(result, monthly, index_of(result, ["later"]))
    assert [(w.first_month, w.last_month, w.months) for w in alone.waits] == [
        ("2027-01", "2027-02", 2)
    ]

    both = next(s.route for s in result.schedules if set(s.route) == {"later", "job"})
    detail = route_detail(result, monthly, index_of(result, both))
    assert detail.waits == []
    [gate] = detail.gates
    assert (gate.kind, gate.variant_id, gate.month) == ("offer", "job", "2027-01")
    work = next(s for s in detail.steps if s.variant_id == "job")
    assert work.offer is not None
    assert work.offer.role_class == "analyst"
    assert work.wage is not None
    assert work.wage.minor_units == 150000
    no_offer = next(s for s in detail.scenarios if s.scenario is Scenario.NO_OFFER)
    assert not no_offer.same_as_base


@pytest.mark.req("API-03")
def test_a_route_that_no_longer_rechecks_as_stored_is_refused_never_shown_with_other_numbers() -> (
    None
):
    monthly = trace()
    result = search_routes(monthly)
    b = index_of(result, ["TRACE-01/B"])
    tampered = result.schedules[b].model_copy(
        update={"objective_cost": SignedMoney(minor_units=1, currency="GBP")}
    )
    schedules = [tampered if i == b else s for i, s in enumerate(result.schedules)]

    with pytest.raises(CareerwrightError) as refused:
        route_detail(result.model_copy(update={"schedules": schedules}), monthly, b)
    assert refused.value.code is ErrorCode.STALE_INPUT_VERSION
    assert refused.value.details == {"reason": "solve_outdated"}
    with pytest.raises(CareerwrightError) as missing:
        route_detail(result, monthly, len(result.schedules))
    assert missing.value.code is ErrorCode.NOT_FOUND


def test_the_baseline_kind_is_named_when_the_person_stated_it() -> None:
    monthly = constructed(2, course("c"), teaches=("c",), baseline=0, objective="economic")
    staying = monthly.inputs.baseline
    assert staying is not None
    stated = monthly.model_copy(
        update={
            "inputs": monthly.inputs.model_copy(
                update={"baseline": staying.model_copy(update={"label": "current_role"})}
            )
        }
    )
    found = comparison(search_routes(stated), stated)
    assert found.basis.baseline is not None
    assert found.basis.baseline.kind is BaselineKind.CURRENT_ROLE
