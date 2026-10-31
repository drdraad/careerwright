"""The route search (spec section 12, OPT-1, ROU-1; S6.1, S6.2, S6.5, S6.7): a canonical
depth-first search over skip or one start per concept, every candidate checked by the Task 11
route checker, every distinct feasible schedule kept (dominated ones included), the three
layers peeled over that archive, families grouped for presentation only, and coverage that is
`complete` only when the declared tree is exhausted. Expected values come from the fixtures and
from hand-worked constructed cases, never from the search itself."""

import itertools
import subprocess
import sys
from typing import Any

import pytest

from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.planning.catalogue import (
    ActionConcept,
    ActionKind,
    Fact,
    FundingInstrument,
    InstrumentKind,
    OfferGate,
    Offering,
    RecordState,
    Support,
    Variant,
    WorkPatternKind,
)
from careerwright.planning.checker import (
    FindingCode,
    FindingKind,
    RouteQualification,
    Scenario,
    Verdict,
)
from careerwright.planning.compiler import (
    Commitment,
    ExistingDebt,
    MonthlyInput,
    PlanningInputs,
    ReadinessBasis,
    WorkRights,
    compile_input,
)
from careerwright.planning.layers import dominates
from careerwright.planning.search import (
    RANK_SECONDS,
    M0SearchLimits,
    Outcome,
    PruningRule,
    RankLimitReachedError,
    SearchCancelledError,
    SearchCoverage,
    SearchResult,
    StopReason,
    rank_archive,
    search_archive,
    search_routes,
)
from tests.support.capability import fixture
from tests.support.planning import (
    CONSTRUCTED,
    COURSES,
    ROW,
    START,
    catalogue_of,
    directai_fixture,
    directai_instance,
    month_end,
    month_start,
    option,
    pattern,
    person,
    readiness_of,
    repayments_beside_an_unknown,
    support,
    trace_catalogue,
    trace_inputs,
    trace_readiness,
    trace_route,
    undated_relief,
)

# Enough cash that no constructed case below is about the reserve (it has its own tests).
OPENING = 1_000_000
TIMES = {"elapsed_ms", "rank_ms"}  # the stages' times: the only fields a replay may change
Option = tuple[ActionConcept, Offering, Variant]
Options = list[Option]


def trace() -> MonthlyInput:
    return compile_input(trace_inputs(), trace_catalogue(), readiness=trace_readiness())


def directai() -> MonthlyInput:
    inputs, catalogue, readiness = directai_instance()
    return compile_input(inputs, catalogue, readiness=readiness)


def someone(**changes: Any) -> PlanningInputs:
    return person(opening=OPENING, **changes)


def care(hours: int) -> Commitment:
    return Commitment(label="care", hours_per_week=hours, cited=CONSTRUCTED)


def course(
    name: str,
    *,
    first: int = 0,
    months: int = 1,
    fee: int = 0,
    hours: int | None = 0,
    **extra: Any,
) -> Option:
    """A course starting `first` months after the planning start, for `months` calendar
    months, its fee paid in its first month."""
    begins = month_start(START, first)
    return option(
        name,
        start=begins,
        finish=month_end(begins, months),
        hours=hours,
        payments=((0, fee),) if fee else (),
        **extra,
    )


def solve(
    inputs: PlanningInputs, options: Options, readiness: ReadinessBasis, **limits: int
) -> SearchResult:
    monthly = compile_input(inputs, catalogue_of(*options), readiness=readiness)
    return search_routes(monthly, limits=M0SearchLimits(**limits))


def routes(result: SearchResult) -> list[tuple[str, ...]]:
    return [tuple(s.route) for s in result.schedules]


def by_route(result: SearchResult) -> dict[tuple[str, ...], tuple[int, int, int | None]]:
    return {
        tuple(s.route): (s.months_to_readiness, s.objective_cost.minor_units, s.layer)
        for s in result.schedules
    }


# The fixtures.


@pytest.mark.req("TRACE01-03", "OPT1-08", "OPT1-05", "OPT1-16")
def test_trace_01_completes_with_a_b_c_in_f1_d_in_f2_and_e_in_f3() -> None:
    result = search_routes(trace())
    expected = fixture("worked_trace.json")["expected"]

    assert result.coverage is SearchCoverage.COMPLETE
    assert result.stop_reason is None
    assert result.outcome is Outcome.ROUTES_FOUND
    assert result.layers_exact
    assert result.objective_basis == "economic"
    assert result.scenario is Scenario.BASE
    assert sorted(routes(result)) == sorted(
        (f"TRACE-01/{a.rsplit(':', 1)[-1]}",) for [a] in expected["feasible_nonempty_action_sets"]
    )
    found = by_route(result)
    for letter in COURSES:
        route = trace_route(letter)
        time, cost, _ = found[(f"TRACE-01/{letter}",)]
        assert (time, cost) == (route["time_months"], route["economic_cost_minor"])
    layers = {f"TRACE-01/{x}": n for n, front in enumerate(expected["fronts"], 1) for x in front}
    assert {route[0]: layer for route, (_, _, layer) in found.items()} == layers
    # E's dominators are B and D, and only they.
    point = {route[0]: (time, cost) for route, (time, cost, _) in found.items()}
    assert sorted(r for r, p in point.items() if dominates(p, point["TRACE-01/E"])) == [
        "TRACE-01/B",
        "TRACE-01/D",
    ]
    # The empty route is feasible but reaches no milestone. One course at a time (the
    # exclusive group), so the tree is the empty route and the five courses.
    assert result.feasible_without_milestone == 1
    assert result.expanded_states == 6
    assert result.unexplored_branches == 0


@pytest.mark.req("TRACE01-03", "OPT1-06")
def test_trace_01_s_schedules_keep_their_checks_identity_and_versions() -> None:
    monthly = trace()
    result = search_routes(monthly)
    [b] = [s for s in result.schedules if s.route == ["TRACE-01/B"]]

    assert result.input_version == monthly.input_version
    assert result.label.name == "TRACE-01"
    assert monthly.readiness is not None
    assert result.matrix_version == monthly.readiness.matrix.matrix_version
    assert result.definition_version == monthly.readiness.matrix.definition_version
    assert result.canonical_order == [f"fixture:course:{x}" for x in COURSES]
    assert result.algorithm_version
    assert result.pruning_version
    assert result.limits == M0SearchLimits()
    assert (result.instance.concepts, result.instance.starts_per_concept) == (5, 1)
    assert result.instance.months == 6
    assert result.instance.selection_space == 6  # the empty route and one of five courses
    assert (b.months_to_readiness, b.readiness_month) == (4, "2027-05")
    assert b.direct_cost.minor_units == 60000
    assert b.economic_cost is not None
    assert b.economic_cost.minor_units == 60000
    assert b.verdict is Verdict.QUALIFIED  # synthetic, provisional matrix: never unqualified
    assert len({s.family_id for s in result.schedules}) == 5


@pytest.mark.req("DIRECTAI-01", "OPT1-08", "OPT1-16")
def test_the_a_to_i_fixture_completes_with_its_three_layers_in_direct_spending_mode() -> None:
    result = search_routes(directai())
    stated = directai_fixture()["routes"]

    assert result.coverage is SearchCoverage.COMPLETE
    assert result.objective_basis == "direct_spending"
    assert by_route(result) == {
        (r["id"],): (r["time_months"], r["direct_spend_minor"], r["expected_layer"]) for r in stated
    }
    assert all(s.economic_cost is None for s in result.schedules)  # no baseline: direct only


@pytest.mark.req("PARETO-03")
def test_layers_rank_one_target_s_routes_never_another_s() -> None:
    trace_result, directai_result = search_routes(trace()), search_routes(directai())
    b = next(s for s in trace_result.schedules if s.route == ["TRACE-01/B"])

    # TRACE-01's B (4 months, £600) is sooner and cheaper than every A-I route, but it is a
    # route to another target, so it betters none of them: A, B and C stay in F1.
    assert trace_result.target_title != directai_result.target_title
    assert all(
        dominates((b.months_to_readiness, b.objective_cost.minor_units), (time, cost))
        for time, cost, _ in by_route(directai_result).values()
    )
    assert sorted(r for r, (_, _, layer) in by_route(directai_result).items() if layer == 1) == [
        (f"fixture:directai:route:{x}",) for x in "ABC"
    ]


@pytest.mark.req("DIRECTAI-03")
def test_the_two_fixtures_share_no_route_or_family_id() -> None:
    trace_result, directai_result = search_routes(trace()), search_routes(directai())
    schedules = [*trace_result.schedules, *directai_result.schedules]
    route_ids = [r for s in schedules for r in s.route]
    family_ids = [f.family_id for f in [*trace_result.families, *directai_result.families]]

    assert len(route_ids) == len(set(route_ids)) == 14
    assert all(r.startswith("fixture:directai:route:") for r in route_ids[5:])
    assert len(family_ids) == len(set(family_ids)) == 14


# The declared tree.


@pytest.mark.req("OPT1-01")
def test_each_allowed_set_is_visited_once_and_never_more_than_six_actions() -> None:
    options = [course(f"c{n}") for n in range(7)]
    teaches = {f"offering:c{n}": (ROW,) for n in range(7)}
    result = solve(someone(horizon=2), options, readiness_of(teaches))

    # Nothing prunes here: the tree is every set of at most six of seven courses.
    assert result.instance.selection_space == 127
    assert result.expanded_states == 127
    assert len(result.schedules) == 126  # every non-empty set reaches readiness
    assert max(len(s.route) for s in result.schedules) == 6
    assert len(set(routes(result))) == len(result.schedules)
    assert all(list(s.route) == sorted(s.route) for s in result.schedules)  # canonical order


@pytest.mark.req("OPT1-01")
def test_one_start_per_concept_one_per_exclusive_group_and_one_bridge_role() -> None:
    accepted = OfferGate(accepted=True, role_class="synthetic bridge role")
    options = [
        course("a-jan", concept="a"),
        course("a-apr", first=3, concept="a"),
        course("x", group="core"),
        course("y", group="core"),
        course("job1", kind=ActionKind.WORK, offer=accepted, wage=10000),
        course("job2", kind=ActionKind.WORK, offer=accepted, wage=10000),
    ]
    result = solve(someone(horizon=6), options, readiness_of({"offering:a-jan": (ROW,)}))
    seen = [set(s.route) for s in result.schedules]

    assert len(seen) == 9  # a-jan with skip, x or y and with skip, job1 or job2
    assert not any({"a-jan", "a-apr"} <= r for r in seen)
    assert not any({"x", "y"} <= r for r in seen)
    assert not any({"job1", "job2"} <= r for r in seen)
    # skip, a-jan or a-apr; skip, x or y; skip, job1 or job2: 3 x 3 x 3 sets.
    assert result.instance.selection_space == result.expanded_states == 27
    assert result.instance.starts_per_concept == 2


@pytest.mark.req("OPT1-01", "ROU1-02", "FAMILY-01", "ROU1-03")
def test_a_later_intake_is_a_schedule_of_the_same_family_and_the_family_shows_its_best_layer() -> (
    None
):
    options = [
        course("a-jan", months=2, fee=500, concept="a"),
        course("a-apr", first=3, months=2, fee=500, concept="a"),
        course("b", months=3, fee=900),
    ]
    teaches = {"offering:a-jan": (ROW,), "offering:a-apr": (ROW,), "offering:b": (ROW,)}
    result = solve(someone(horizon=8), options, readiness_of(teaches))
    found = by_route(result)

    assert found[("a-jan",)] == (2, 500, 1)
    assert found[("a-apr",)] == (5, 500, 2)  # the same cost later: bettered by January's
    [a] = [f for f in result.families if ["a-jan"] in f.routes]
    assert sorted(a.routes) == [["a-apr"], ["a-jan"]]
    assert a.best_layer == 1  # its lowest layer, labelled as the family's best
    [b] = [f for f in result.families if ["b"] in f.routes]
    assert b.family_id != a.family_id


@pytest.mark.req("OPT1-01", "ROU1-01", "OPT1-02")
def test_parallel_prerequisites_are_kept_parallel_and_before_the_course_they_open() -> None:
    options = [
        course("intro", months=2, fee=100, grants=["gate:one"]),
        course("lab", months=3, fee=100, grants=["gate:two"]),
        course("main", first=3, months=2, fee=400, prerequisites=["gate:one", "gate:two"]),
        course("later", first=5, fee=50),
    ]
    result = solve(someone(horizon=8), options, readiness_of({"offering:main": (ROW,)}))

    # Only routes with both prerequisites reach the target: main alone, or with one of them,
    # fails its prerequisite in this monthly model, and nothing after main can grant either.
    assert routes(result) == [("intro", "lab", "main"), ("intro", "lab", "main", "later")]
    assert result.pruned[PruningRule.PREREQUISITE] == 3  # main, intro + main, lab + main
    family = next(f for f in result.families if ["intro", "lab", "main"] in f.routes)
    actions = [a.concept_id for a in family.actions]
    order = {(actions[i], actions[j]) for i, j in family.precedence}
    assert order == {("concept:intro", "concept:main"), ("concept:lab", "concept:main")}


@pytest.mark.req("OPT1-01", "ROU1-01")
def test_the_same_actions_in_sequence_or_in_parallel_are_different_families() -> None:
    options = [
        course("a", months=2, fee=100),
        course("b-now", months=2, fee=100, concept="b"),
        course("b-later", first=2, months=2, fee=100, concept="b"),
    ]
    teaches = {"offering:b-now": (ROW,), "offering:b-later": (ROW,)}
    result = solve(someone(horizon=8), options, readiness_of(teaches))
    family = {tuple(s.route): s.family_id for s in result.schedules}

    assert family[("a", "b-now")] != family[("a", "b-later")]  # parallel, then in sequence
    assert family[("b-now",)] == family[("b-later",)]  # one action: a later intake


@pytest.mark.req("RDY1-03", "OPT1-08")
def test_zero_action_readiness_puts_the_empty_route_in_f1_at_no_time() -> None:
    options = [course("refresher", months=2, fee=300)]
    result = solve(someone(horizon=4), options, readiness_of({}, current=2))
    found = by_route(result)

    assert found[()] == (0, 0, 1)
    assert found[("refresher",)] == (0, 300, 2)  # optional development, never forced
    assert result.outcome is Outcome.ROUTES_FOUND


@pytest.mark.req("OPT1-02", "OPT1-13")
def test_a_superset_that_lowers_the_economic_cost_is_kept_and_ranks_first() -> None:
    inputs = someone(horizon=6, pay=200000, baseline=200000, objective="economic", hours=30)
    accepted = OfferGate(accepted=True, role_class="weekend support role")
    options = [
        course("course", months=3, fee=60000, hours=6),
        course("weekend-job", months=6, hours=4, kind=ActionKind.WORK, offer=accepted, wage=20000),
    ]
    result = solve(inputs, options, readiness_of({"offering:course": (ROW,)}))
    found = by_route(result)

    assert found[("course",)] == (3, 60000, 2)
    # The job pays £200 a month above the baseline for six months, so the superset's economic
    # cost is £600 - £1,200 = -£600. Accumulated cost never prunes.
    assert found[("course", "weekend-job")] == (3, -60000, 1)


@pytest.mark.req("PARETO-02", "ROU1-03")
def test_exact_ties_share_a_point_and_a_layer_and_keep_both_routes() -> None:
    options = [course("left", months=2, fee=500), course("right", months=2, fee=500)]
    teaches = {"offering:left": (ROW,), "offering:right": (ROW,)}
    result = solve(someone(horizon=4), options, readiness_of(teaches), max_selected_actions=1)

    assert by_route(result) == {("left",): (2, 500, 1), ("right",): (2, 500, 1)}
    [point] = result.points
    assert (point.months_to_readiness, point.objective_cost.minor_units, point.layer) == (2, 500, 1)
    assert sorted(point.routes) == [["left"], ["right"]]
    assert len(result.families) == 2  # two different courses: two families


@pytest.mark.req("FAMILY-02", "ROU1-03")
def test_grouping_partitions_the_archive_and_changes_nothing_in_it() -> None:
    result = search_routes(directai())
    archive = sorted(routes(result))

    assert sorted(tuple(r) for f in result.families for r in f.routes) == archive
    assert sorted(tuple(r) for p in result.points for r in p.routes) == archive
    layer = {tuple(s.route): s.layer for s in result.schedules}
    for family in result.families:
        layers = [layer[tuple(r)] for r in family.routes]
        assert family.best_layer == min((n for n in layers if n is not None), default=None)


# Sound pruning: each rule cuts only what it proves, and the archive is what the tree holds.


@pytest.mark.req("OPT1-02")
def test_a_spend_cap_prunes_only_sets_that_exceed_it() -> None:
    options = [course(n, fee=500) for n in ("a", "b", "c")]
    teaches = {f"offering:{n}": (ROW,) for n in ("a", "b", "c")}
    result = solve(someone(horizon=2, direct_cap=1000), options, readiness_of(teaches))

    assert sorted(routes(result)) == [("a",), ("a", "b"), ("a", "c"), ("b",), ("b", "c"), ("c",)]
    assert result.pruned == {PruningRule.DIRECT_SPEND_CAP: 1}  # a, b and c together
    assert result.expanded_states == 7  # the triple is never evaluated
    assert result.coverage is SearchCoverage.COMPLETE


@pytest.mark.req("OPT1-02")
def test_a_monthly_payment_cap_prunes_only_months_that_exceed_it() -> None:
    february = option("c", start=START, finish=month_end(START, 2), payments=((1, 600),))
    options = [course("a", fee=600), course("b", fee=600), february]
    teaches = {f"offering:{n}": (ROW,) for n in ("a", "b", "c")}
    result = solve(someone(horizon=2, monthly_cap=1000), options, readiness_of(teaches))

    # a and b both pay £600 in January: £1,200 of £1,000. c pays in February.
    assert sorted(routes(result)) == [("a",), ("a", "c"), ("b",), ("b", "c"), ("c",)]
    assert result.pruned == {PruningRule.MONTHLY_PAYMENT_CAP: 1}
    assert result.expanded_states == 6


@pytest.mark.req("OPT1-02")
def test_a_prerequisite_a_later_concept_can_grant_in_time_is_never_pruned() -> None:
    options = [
        course("main-jan", concept="main", prerequisites=["gate:one"]),
        course("main-jun", first=5, concept="main", prerequisites=["gate:one"]),
        course("intro", first=1, months=2, grants=["gate:one"]),  # February and March
    ]
    teaches = {"offering:main-jan": (ROW,), "offering:main-jun": (ROW,)}
    result = solve(someone(horizon=8), options, readiness_of(teaches))

    # The concept "main" comes first (its January intake), so intro is added after it. June's
    # intake can still be opened by intro (usable from April); January's cannot.
    assert routes(result) == [("main-jun", "intro")]
    assert result.pruned == {PruningRule.PREREQUISITE: 1}  # main-jan, whose child cannot help


@pytest.mark.req("OPT1-02")
def test_a_workload_breach_prunes_only_when_no_later_option_can_lower_the_job_s_hours() -> None:
    inputs = someone(horizon=3, hours=30, availability=40, pay=150000)
    reduced = pattern(WorkPatternKind.REDUCED_HOURS, 10, 100000)
    options = [
        course("evening", months=3, hours=8),
        course("weekend", months=3, hours=8),
        course("x-reduced-hours", months=3, pattern=reduced),  # after both in canonical order
    ]
    result = solve(inputs, options, readiness_of({"offering:evening": (ROW,)}))

    # evening + weekend is 46 hours of 40, but the option after them lowers the job's hours,
    # so the pair's subtree is kept, and its extension fits: 10 + 8 + 8 = 26 hours.
    assert ("evening", "weekend") not in routes(result)
    assert ("evening", "weekend", "x-reduced-hours") in routes(result)
    assert PruningRule.WORKLOAD not in result.pruned


@pytest.mark.req("OPT1-02")
def test_a_workload_breach_no_later_option_can_relieve_is_pruned() -> None:
    inputs = someone(horizon=3, hours=30, availability=40, pay=150000)
    options = [
        course("evening", months=3, hours=8),
        course("weekend", months=3, hours=8),
        course("x-short", months=1, hours=1),
    ]
    result = solve(inputs, options, readiness_of({"offering:evening": (ROW,)}))

    assert routes(result) == [("evening",), ("evening", "x-short")]
    assert result.pruned == {PruningRule.WORKLOAD: 1}  # evening + weekend
    assert result.expanded_states == 7  # evening + weekend + x-short is never evaluated


@pytest.mark.req("OPT1-02", "OPT1-07")
def test_an_option_no_route_can_contain_is_set_aside_with_its_reason() -> None:
    options = [
        course("dear", fee=2000),
        option("undated", start=None, finish=None),
        course("fine", fee=200),
    ]
    teaches = {"offering:fine": (ROW,), "offering:dear": (ROW,), "offering:undated": (ROW,)}
    result = solve(someone(horizon=4, direct_cap=1000), options, readiness_of(teaches))

    assert {s.variant_id: s.codes for s in result.set_aside} == {
        "dear": [FindingCode.DIRECT_SPEND_CAP],
        "undated": [FindingCode.DATES_UNKNOWN],
    }
    # Everything each one's own check found, unknowns apart from violations.
    assert {s.variant_id: (s.unresolved, s.violations) for s in result.set_aside} == {
        "dear": ([], [FindingCode.DIRECT_SPEND_CAP]),
        "undated": ([FindingCode.DATES_UNKNOWN], []),
    }
    assert routes(result) == [("fine",)]
    assert result.coverage is SearchCoverage.COMPLETE


# What a result says when no route is found: never "no route" unless it is proved.


@pytest.mark.req("LIMITS-05", "OPT1-07")
def test_a_complete_empty_archive_is_no_route_in_the_bounded_model() -> None:
    options = [course("dear", fee=2000), course("unrelated", fee=100)]
    inputs = someone(horizon=3, direct_cap=1000)
    result = solve(inputs, options, readiness_of({"offering:dear": (ROW,)}))

    assert result.coverage is SearchCoverage.COMPLETE
    assert result.schedules == []
    assert result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    assert result.feasible_without_milestone == 2  # the empty route and "unrelated" alone


@pytest.mark.req("OPT1-07", "LIMITS-05")
def test_an_option_with_unknown_dates_leaves_the_result_unresolved_never_no_route() -> None:
    options = [option("undated", start=None, finish=None)]
    result = solve(someone(horizon=3), options, readiness_of({"offering:undated": (ROW,)}))

    assert result.coverage is SearchCoverage.COMPLETE
    assert result.schedules == []
    assert result.outcome is Outcome.UNRESOLVED


@pytest.mark.req("OPT1-07", "LIMITS-05")
def test_an_option_without_weekly_hours_is_set_aside_as_unknown_whatever_the_known_load() -> None:
    # The job and the care already take 38 of 36 hours, so the checker reports this course's
    # months as over the limit rather than unknown; its own hours are still not stated.
    inputs = someone(horizon=3, hours=30, availability=36, commitments=[care(8)])
    options = [course("untimed", months=2, hours=None)]
    result = solve(inputs, options, readiness_of({"offering:untimed": (ROW,)}))

    assert [(s.variant_id, s.kind) for s in result.set_aside] == [
        ("untimed", FindingKind.UNRESOLVED)
    ]
    assert FindingCode.WORKLOAD_UNKNOWN in result.set_aside[0].codes
    assert result.outcome is Outcome.UNRESOLVED
    # The breach is the person's own, every month, so it is told once, on the result.
    assert {f.code for f in result.starting_violations} == {FindingCode.WORKLOAD}
    assert result.set_aside[0].violations == []


@pytest.mark.req("OPT1-07", "LIMITS-05", "OPT1-02")
def test_an_empty_route_over_its_hours_never_hides_an_undated_option_behind_no_route() -> None:
    result = search_routes(undated_relief())

    # The empty route breaks the workload limit and no dated option can lower the job's hours,
    # so nothing is feasible as stated; but the undated option might, once its dates are known.
    assert result.coverage is SearchCoverage.COMPLETE
    assert result.schedules == []
    assert [(s.variant_id, s.kind) for s in result.set_aside] == [
        ("reduced-undated", FindingKind.UNRESOLVED)
    ]
    assert result.outcome is Outcome.UNRESOLVED


@pytest.mark.req("OPT1-07")
def test_an_option_is_never_blamed_for_a_breach_the_person_s_starting_position_already_has() -> (
    None
):
    result = search_routes(undated_relief())
    [undated] = result.set_aside

    # March and April's workload breach is the person's own (37 hours of 25), and the very
    # breach this option would cure once dated: it is reported once, on the result, never as
    # what rules the option out (re-review 13a, I2).
    assert [(f.code, f.month) for f in result.starting_violations] == [
        (FindingCode.WORKLOAD, "2027-03"),
        (FindingCode.WORKLOAD, "2027-04"),
    ]
    assert undated.unresolved == [FindingCode.DATES_UNKNOWN]
    assert undated.violations == []


@pytest.mark.req("OPT1-07")
def test_a_course_with_an_unknown_cost_is_not_blamed_for_a_reserve_already_broken() -> None:
    # £600 opening cash and £1,000 living costs, with pay arriving late: January's lowest
    # balance is below the £500 reserve before anything is chosen.
    inputs = person(horizon=3, opening=60_000, living=100_000, reserve=50_000, pay=200_000)
    options = [course("unpriced", first=1, unknown_cost="not stated")]
    result = solve(inputs, options, readiness_of({"offering:unpriced": (ROW,)}))
    [unpriced] = result.set_aside

    assert [(f.code, f.month) for f in result.starting_violations] == [
        (FindingCode.RESERVE, "2027-01")
    ]
    assert unpriced.unresolved == [FindingCode.COST_UNKNOWN]
    assert unpriced.violations == []


@pytest.mark.req("OPT1-07", "LIMITS-05")
def test_an_unknown_hard_limit_leaves_every_route_unresolved_and_says_which() -> None:
    options = [course("fine", fee=200)]
    result = solve(
        someone(horizon=3, reserve=None), options, readiness_of({"offering:fine": (ROW,)})
    )

    assert result.outcome is Outcome.UNRESOLVED
    assert result.coverage is SearchCoverage.COMPLETE
    assert [(f.code, f.reason) for f in result.blocking_inputs] == [
        (FindingCode.LIMIT_UNKNOWN, "reserve")
    ]
    assert result.expanded_states == 1  # every route has it: nothing further is checked
    assert result.pruned == {PruningRule.INPUT_UNRESOLVED: 1}


# Task 12a's findings, classed for the set-aside screen and pruning (ADR 0016 rule 2).


@pytest.mark.req("OPT1-07", "BND1-04", "PLN-11")
def test_unknown_work_rights_leave_every_route_unresolved_and_say_so() -> None:
    options = [course("fine", fee=200)]
    result = solve(
        someone(horizon=3, work_rights=WorkRights.UNKNOWN),
        options,
        readiness_of({"offering:fine": (ROW,)}),
    )

    assert result.outcome is Outcome.UNRESOLVED  # never "no route", never ineligible
    assert [f.code for f in result.blocking_inputs] == [FindingCode.WORK_RIGHTS_UNKNOWN]
    assert result.pruned == {PruningRule.INPUT_UNRESOLVED: 1}


@pytest.mark.req("OPT1-07", "OPT1-02", "PLN-06")
def test_an_option_waiting_on_the_person_s_own_confirmation_is_set_aside_with_it() -> None:
    concept, offering, variant = course("refused", fee=200)
    stated = concept.model_copy(
        update={"entry_requirements": [Fact(field="entry_requirement", value="GCSE maths")]}
    )
    two = (support(paid_to="provider", amount=50), support(paid_to="provider", amount=50))
    options = [
        (stated, offering, variant.model_copy(update={"entry_requirements_met": False})),
        course("stacked", fee=200, supports=two),
        course(
            "eligible-only",
            eligibility_conditions=[Fact(field="eligibility_age", value={"minimum_age": 19})],
        ),
        course("fine", fee=200),
    ]
    teaches = {f"offering:{n}": (ROW,) for n in ("refused", "stacked", "eligible-only", "fine")}
    result = solve(someone(horizon=3), options, readiness_of(teaches))

    # Each is that option's own: every route containing it repeats it.
    assert {s.variant_id: (s.codes, s.kind) for s in result.set_aside} == {
        "refused": ([FindingCode.ENTRY_REQUIREMENTS_NOT_MET], FindingKind.UNRESOLVED),
        "stacked": ([FindingCode.STACKING_UNCONFIRMED], FindingKind.UNRESOLVED),
        "eligible-only": ([FindingCode.ELIGIBILITY_UNCONFIRMED], FindingKind.UNRESOLVED),
    }
    assert routes(result) == [("fine",)]
    assert result.outcome is Outcome.ROUTES_FOUND


@pytest.mark.req("OPT1-02", "BND1-06")
def test_a_second_conditional_job_transition_is_pruned_and_never_archived() -> None:
    awaiting = OfferGate(accepted=False, role_class="synthetic role")
    options = [
        course("apprenticeship", kind=ActionKind.APPRENTICESHIP, offer=awaiting, wage=10000),
        course("bridge-job", kind=ActionKind.WORK, offer=awaiting, wage=10000),
        course("z-later", first=1),
    ]
    teaches = {f"offering:{n}": (ROW,) for n in ("apprenticeship", "bridge-job", "z-later")}
    result = solve(someone(horizon=3), options, readiness_of(teaches))

    assert not any({"apprenticeship", "bridge-job"} <= set(r) for r in routes(result))
    assert result.pruned == {PruningRule.JOB_TRANSITIONS: 1}
    # The empty route, three singles, three pairs: the pair's extension is never checked.
    assert result.expanded_states == 7
    assert result.not_feasible == 1


@pytest.mark.req("OPT1-07", "LIMITS-05", "FIN1-06")
def test_repayments_alone_above_the_payment_cap_are_the_starting_position_never_an_option_s() -> (
    None
):
    card = ExistingDebt(
        debt_id="card", monthly_repayment_minor=1500, balance_minor=None, cited=CONSTRUCTED
    )
    options = [course("fine", fee=200), course("dear", fee=900)]
    teaches = {"offering:fine": (ROW,), "offering:dear": (ROW,)}
    result = solve(
        someone(horizon=2, monthly_cap=1000, existing_debts=[card]), options, readiness_of(teaches)
    )

    assert [(f.code, f.month, f.reason) for f in result.starting_violations] == [
        (FindingCode.REPAYMENTS_ABOVE_PAYMENT_CAP, "2027-01", "card"),
        (FindingCode.REPAYMENTS_ABOVE_PAYMENT_CAP, "2027-02", "card"),
    ]
    assert result.set_aside == []  # no option is blamed for the person's own repayments
    assert result.pruned == {PruningRule.MONTHLY_PAYMENT_CAP: 1}
    assert result.expanded_states == 3  # the empty route and each option alone
    assert result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL  # nothing here is unknown


@pytest.mark.req("OPT1-07", "LIMITS-05", "FIN1-06")
def test_repayments_no_option_can_lower_rule_out_every_route_whatever_is_unknown() -> None:
    result = search_routes(repayments_beside_an_unknown())

    # Whatever the unpriced course turns out to cost, every route repays £15 a month against a
    # £10 cap: the truth is no route while the repayments exceed it, never "confirm the cost".
    assert result.coverage is SearchCoverage.COMPLETE
    assert [s.variant_id for s in result.set_aside] == ["unpriced"]
    assert {f.code for f in result.starting_violations} == {
        FindingCode.REPAYMENTS_ABOVE_PAYMENT_CAP
    }
    assert result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL
    # Even beside an input not stated (every route is unresolved), the repayments decide it.
    unstated = repayments_beside_an_unknown()
    unstated = unstated.model_copy(
        update={"inputs": unstated.inputs.model_copy(update={"reserve_minor": None})}
    )
    assert search_routes(unstated).outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL


@pytest.mark.req("OPT1-07", "OPT1-02", "PLN-06")
def test_one_scheme_on_two_options_is_unresolved_never_pruned_and_exclusive_schemes_are_cut() -> (
    None
):
    waiver = support(paid_to="provider", amount=None, kind=InstrumentKind.FEE_WAIVER)
    options = [
        course("first", fee=500, supports=(waiver,)),
        course("second", fee=500, supports=(waiver,)),
    ]
    teaches = {"offering:first": (ROW,), "offering:second": (ROW,)}
    shared = solve(someone(horizon=2), options, readiness_of(teaches))

    # Each alone uses the waiver once; together they wait on the person's confirmation.
    assert routes(shared) == [("first",), ("second",)]
    assert shared.unresolved == 1
    assert shared.set_aside == []  # it is no one option's own finding
    confirmed = solve(
        someone(horizon=2, shared_schemes=["funding:constructed"]), options, readiness_of(teaches)
    )
    assert ("first", "second") in routes(confirmed)

    def granted(instrument_id: str) -> Support:
        return support(paid_to="provider", amount=100).model_copy(
            update={"instrument_id": instrument_id}
        )

    exclusive = [
        course("a", fee=500, supports=(granted("funding:a"),)),
        course("b", fee=500, supports=(granted("funding:b"),)),
        course("both", fee=500, supports=(granted("funding:a"), granted("funding:b"))),
        course("z-later", first=1),
    ]
    catalogue = catalogue_of(*exclusive).model_copy(
        update={
            "instruments": [
                FundingInstrument(
                    instrument_id="funding:a",
                    programme=None,
                    kind=InstrumentKind.GRANT,
                    jurisdiction="GB-ENG",
                    review_state=RecordState.ACCEPTED_ASSUMPTION,
                    exclusive_with=["funding:b"],
                )
            ]
        }
    )
    teaches = {f"offering:{n}": (ROW,) for n in ("a", "b", "both", "z-later")}
    monthly = compile_input(someone(horizon=2), catalogue, readiness=readiness_of(teaches))
    cut = search_routes(monthly)

    # On one option they are its own breach; across two the breach persists, so it is cut.
    assert [(s.variant_id, s.kind) for s in cut.set_aside] == [("both", FindingKind.VIOLATION)]
    assert FindingCode.EXCLUSIVE_SCHEMES in cut.set_aside[0].codes
    assert not any({"a", "b"} <= set(r) for r in routes(cut))
    assert cut.pruned == {PruningRule.EXCLUSIVE_SCHEMES: 1}


@pytest.mark.req("OPT1-07", "TIME1-03", "PLN-05")
def test_a_course_behind_an_application_is_a_conditional_route_never_set_aside() -> None:
    # The controller's C09 ruling: no recorded admission is a condition, never "not feasible".
    applied = course(
        "applied",
        first=2,
        application_deadline=month_end(START, 1),
        application_gate="admission:offering:applied",
    )
    result = solve(someone(horizon=4), [applied], readiness_of({"offering:applied": (ROW,)}))

    assert result.set_aside == []
    [schedule] = result.schedules
    assert [(c.kind, c.verification) for c in schedule.conditions] == [
        ("application", "confirm_admission")
    ]
    assert RouteQualification.CONDITIONAL_APPLICATION in schedule.qualifications
    assert result.outcome is Outcome.ROUTES_FOUND


@pytest.mark.req("OPT1-07")
def test_a_feasible_route_whose_readiness_cannot_be_assessed_is_unresolved_not_no_route() -> None:
    options = [course("fine", fee=200)]
    # The person has not said how well they do the row: no usable evidence, never level 0, and
    # the course teaches something else.
    basis = readiness_of({}).model_copy(update={"evidence": []})
    result = solve(someone(horizon=3), options, basis)

    assert result.schedules == []
    assert result.readiness_unknown == 2
    assert result.outcome is Outcome.UNRESOLVED


# Coverage and limits: a stopped run is never complete and never "no route".


@pytest.mark.req("OPT1-05", "LIMITS-05")
def test_a_run_stopped_at_its_state_limit_is_budget_truncated_with_its_reason() -> None:
    options = [course(f"c{n}") for n in range(4)]
    teaches = {f"offering:c{n}": (ROW,) for n in range(4)}
    result = solve(someone(horizon=2), options, readiness_of(teaches), max_states=3)

    assert result.coverage is SearchCoverage.BUDGET_TRUNCATED
    assert result.stop_reason is StopReason.STATE_LIMIT
    assert result.expanded_states == 3
    assert not result.layers_exact
    assert result.outcome is Outcome.ROUTES_FOUND
    assert routes(result) == [("c0",), ("c1",)]  # checked before the stop, and kept
    assert result.unexplored_branches > 0
    assert result.narrowings


@pytest.mark.req("OPT1-05", "LIMITS-05")
def test_a_stopped_run_with_nothing_found_is_none_found_before_the_limit() -> None:
    options = [course("c0"), course("c1")]
    result = solve(someone(horizon=2), options, readiness_of({"offering:c1": (ROW,)}), max_states=2)

    assert result.coverage is SearchCoverage.BUDGET_TRUNCATED
    assert result.schedules == []
    assert result.outcome is Outcome.NONE_FOUND_BEFORE_LIMIT


@pytest.mark.req("OPT1-05")
def test_a_run_stopped_by_the_clock_says_so() -> None:
    options = [course(f"c{n}") for n in range(3)]
    teaches = {f"offering:c{n}": (ROW,) for n in range(3)}
    monthly = compile_input(
        someone(horizon=2), catalogue_of(*options), readiness=readiness_of(teaches)
    )
    ticks = iter([0.0, 0.0, 0.0])  # the start, then the first two checks; then 31 s have passed

    result = search_routes(monthly, clock=lambda: next(ticks, 31.0))

    assert result.coverage is SearchCoverage.BUDGET_TRUNCATED
    assert result.stop_reason is StopReason.WALL_TIME_LIMIT
    assert result.expanded_states == 2


@pytest.mark.req("OPT1-05")
def test_a_full_archive_stops_the_run_before_a_schedule_goes_unrecorded() -> None:
    options = [course(f"c{n}") for n in range(3)]
    teaches = {f"offering:c{n}": (ROW,) for n in range(3)}
    result = solve(someone(horizon=2), options, readiness_of(teaches), max_feasible_archive=2)

    assert result.coverage is SearchCoverage.BUDGET_TRUNCATED
    assert result.stop_reason is StopReason.ARCHIVE_LIMIT
    assert routes(result) == [("c0",), ("c1",)]


@pytest.mark.req("OPT1-10", "LIMITS-01")
def test_a_state_limited_run_replays_exactly_and_keeps_every_schedule_it_met() -> None:
    monthly = directai()
    limits = M0SearchLimits(max_states=5)
    first, second = search_routes(monthly, limits=limits), search_routes(monthly, limits=limits)
    complete = search_routes(monthly)

    assert first.stop_reason is StopReason.STATE_LIMIT
    assert first.model_dump(exclude=TIMES) == second.model_dump(exclude=TIMES)
    # What it met is the complete run's archive up to where it stopped, in the order met.
    assert routes(first) == routes(complete)[: len(first.schedules)]
    assert first.schedules


# The rank stage (S6.8; review 13a, M3): its own time and its own limit, apart from the search.


@pytest.mark.req("OPT1-11")
def test_the_rank_stage_is_timed_apart_from_the_search_and_never_on_its_clock() -> None:
    monthly = directai()
    archive = search_archive(monthly, clock=lambda: 0.0)  # the search's clock stands still
    ticks = itertools.count(1000.0, 0.25)  # the rank stage's: each read a quarter-second on

    result = rank_archive(archive, clock=lambda: next(ticks))

    assert result.elapsed_ms == 0  # the search's own time: ranking never adds to it
    assert 0 < result.rank_ms < RANK_SECONDS * 1000
    assert result.rank_seconds == RANK_SECONDS
    assert result.model_dump(exclude=TIMES) == search_routes(monthly).model_dump(exclude=TIMES)


@pytest.mark.req("OPT1-11")
def test_the_rank_stage_stops_at_its_own_limit_and_never_claims_ranks() -> None:
    archive = search_archive(directai())
    ticks = iter([0.0])  # the stage starts; every later read is at its limit

    with pytest.raises(RankLimitReachedError):
        rank_archive(archive, clock=lambda: next(ticks, float(RANK_SECONDS)))


# Cancellation (DUR-05; L0 runs the search in the worker, so a cancel reaches it there).


@pytest.mark.req("LIMITS-06", "DUR-05")
def test_a_cancel_reaches_the_search_at_its_next_check_and_leaves_no_result() -> None:
    asked: list[int] = []

    def cancelled() -> bool:
        asked.append(len(asked) + 1)
        return len(asked) == 3  # the person cancels while the second candidate is checked

    with pytest.raises(SearchCancelledError):
        search_routes(directai(), cancelled=cancelled)
    # Asked before each candidate, and nothing checked or asked once it was cancelled.
    assert asked == [1, 2, 3]


@pytest.mark.req("LIMITS-06", "DUR-05")
def test_a_cancel_during_the_rank_stage_leaves_no_result() -> None:
    archive = search_archive(directai())

    with pytest.raises(SearchCancelledError):
        rank_archive(archive, cancelled=lambda: True)


@pytest.mark.req("OPT1-10", "OPT1-12")
def test_a_complete_run_on_the_same_input_reproduces_the_same_result() -> None:
    monthly = directai()
    first, second = search_routes(monthly), search_routes(monthly)

    assert first.model_dump(exclude=TIMES) == second.model_dump(exclude=TIMES)
    assert first.input_version == monthly.input_version


@pytest.mark.req("OPT1-12")
def test_a_changed_input_is_a_new_snapshot_and_leaves_an_earlier_result_alone() -> None:
    monthly = trace()
    before = search_routes(monthly)
    changed = compile_input(
        trace_inputs(direct_spend_cap_minor=100000),
        trace_catalogue(),
        readiness=trace_readiness(),
    )
    after = search_routes(changed)

    assert changed.input_version != monthly.input_version
    assert after.input_version == changed.input_version
    assert ("TRACE-01/E",) not in routes(after)  # £1,300 is above the new £1,000 cap
    assert ("TRACE-01/E",) in routes(before)
    with pytest.raises(ValueError, match="frozen"):
        monthly.inputs = changed.inputs  # type: ignore[misc]


# Scope: the search refuses what the M0 model does not declare.


def test_a_search_needs_the_target_s_readiness_basis() -> None:
    monthly = compile_input(trace_inputs(), trace_catalogue(), readiness=None)

    with pytest.raises(CareerwrightError) as raised:
        search_routes(monthly)
    assert raised.value.code is ErrorCode.VALIDATION_FAILED


@pytest.mark.req("OPT1-05")
def test_a_catalogue_beyond_the_m0_bounds_is_refused_never_searched_in_part() -> None:
    three = [course(f"a{n}", first=n, concept="a") for n in range(3)]
    many = [course(f"c{n}") for n in range(3)]

    with pytest.raises(CareerwrightError) as starts:
        solve(someone(horizon=6), three, readiness_of({}))
    with pytest.raises(CareerwrightError) as concepts:
        solve(someone(horizon=6), many, readiness_of({}), max_actions=2)
    assert starts.value.code is concepts.value.code is ErrorCode.MODEL_SCOPE_EXCEEDED
    assert starts.value.details["reason"] == "starts_per_concept"
    assert concepts.value.details["reason"] == "concepts"


@pytest.mark.req("OPT1-09")
def test_candidate_evaluation_loads_no_network_model_or_database_client() -> None:
    probe = (
        "import sys, careerwright.planning.search; "
        "print(','.join(sorted({m.split('.')[0] for m in sys.modules})))"
    )
    # Our own interpreter, isolated, running a fixed probe.
    loaded = subprocess.run(  # noqa: S603
        [sys.executable, "-I", "-c", probe], capture_output=True, text=True, check=True
    ).stdout.strip()
    clients = {
        "sqlalchemy",
        "psycopg",
        "alembic",
        "dbos",
        "httpx",
        "httpx2",
        "httpcore",
        "httpcore2",
        "pydantic_ai",
        "openai",
        "fastapi",
        "starlette",
        "scrapling",
        "firebase_admin",
    }

    assert "careerwright" in loaded.split(",")
    assert clients.isdisjoint(loaded.split(","))
