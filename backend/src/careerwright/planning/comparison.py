"""The Routes chapter's facts from a stored route solve (Task 14's backend half; spec sections
12 and 13, VIS-2 and ROU-1; ADR 0016 decisions 23 to 27). Pure: no SQL, no network, no model.

Everything here reads one solve's ranked result (`SearchResult`) and the monthly input it was
computed from (`MonthlyInput`). Nothing re-ranks the archive, merges a schedule or computes
affordability anew: ranks are the search's, a chosen route's ledgers are `check_route`'s on
the same input, and its stress cases are `evaluate_route`'s. Facts, never sentences (R11):
codes, numbers, months and money, which the web words.

- **The comparison** (`comparison`): what leads (`Lead`), the cost definition with its
  baseline, horizon, start and currency, the model's bounds and the coverage; a bounded
  projection of the equal points (`project`) with shown and total counts; families, best layer
  first; and every point's named comparator under one declared rule (`COMPARATOR_RULE`).
- **The archive, paged** (`schedule_page`): every retained schedule reachable, filtered by a
  view that never changes a recorded layer; reranking within the view is explicit and named
  apart (`view_layer`).
- **A chosen route** (`route_detail`): its cost parts, the monthly table, the steps a card and
  the Gantt show, the gates, waits and milestones, and the stress scenarios apart, never a
  finite point invented for one that fails or is unknown.
"""

from collections.abc import Sequence
from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.capability.readiness import Qualification, ReadinessState
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.money import Money, SignedMoney
from careerwright.planning.catalogue import (
    ActionKind,
    AwardState,
    CatalogueLabel,
    Citation,
    CitationBasis,
    EligibilityStatus,
    FeeLoanKind,
    InstrumentKind,
    RecordState,
    SuppliedFact,
    WorkPatternKind,
)
from careerwright.planning.checker import (
    Condition,
    Feasibility,
    Finding,
    RouteCheck,
    RouteQualification,
    Scenario,
    Verdict,
    evaluate_route,
)
from careerwright.planning.compiler import CompiledVariant, MonthlyInput
from careerwright.planning.families import FamilyAction
from careerwright.planning.inputs import BaselineKind
from careerwright.planning.layers import dominates, rank
from careerwright.planning.ledgers import Liability as Owed
from careerwright.planning.ledgers import LoanToRepay
from careerwright.planning.search import (
    InstanceSize,
    M0SearchLimits,
    Narrowing,
    Outcome,
    Schedule,
    SearchCoverage,
    SearchResult,
    SetAside,
    StopReason,
)

# ADR 0016 decision 23. A point bettered in the base scenario is compared with the points of
# the layer just above it that dominate it (F3 for a point beyond F3); by peeling there is
# always one. The named comparator is the soonest of them, and among equally soon ones the
# cheapest: an order on time, then cost, never a distance across months and pounds. The
# others are listed beside it.
COMPARATOR_RULE = "soonest_dominator_in_the_layer_above"
PROJECTION_POINTS = 200  # the most equal points a comparison shows at once
FAMILIES_SHOWN = 100  # the most families a comparison lists; every schedule stays in the pages
POINT_SCHEDULES = 20  # the schedules a point names; the rest are in the pages
DEFAULT_PAGE = 50
MAX_PAGE = 200

# What Task 13a measured to complete with no limit binding, so the whole selection space
# checked (`tools.route_search_sizes`, 2026-10-31; ADR 0016's Consequences): the most concepts
# at each horizon and number of starts. Facts beside a stopped search's narrowings: what
# searches of a size have done, never a promise that a narrowed one finishes.
MEASURED_ON = date(2026, 10, 31)
_MEASURED = {12: {1: 20, 2: 10}, 24: {1: 18, 2: 10}}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Lead(StrEnum):
    """What the Routes chapter leads with, one code per result."""

    BEST_TRADE_OFFS_FOUND = "best_trade_offs_found"  # routes, complete or not
    NONE_FOUND_BEFORE_LIMIT = "none_found_before_limit"  # stopped early: never "no route"
    UNRESOLVED = "unresolved"  # complete, nothing proved, something unknown: what to confirm
    # Nothing in the bounded model reaches the target only because an option it needs takes
    # longer than the 24-month model plans, with no breach of any limit (plan v1.6;
    # `_only_length`): its own state, never "no route", "not feasible" or impossible.
    LONGER_THAN_MODEL = "longer_than_model"
    NO_ROUTE_IN_BOUNDED_MODEL = "no_route_in_bounded_model"  # complete, nothing unknown


ResultCode = Literal["SOLVE_LIMIT_REACHED", "NO_ROUTE_IN_BOUNDED_MODEL"]


class DominanceReason(StrEnum):
    """How the comparator betters a point, in the comparison's own cost basis."""

    SOONER_AND_CHEAPER = "sooner_and_cheaper"
    SOONER_SAME_COST = "sooner_same_cost"
    CHEAPER_SAME_TIME = "cheaper_same_time"  # an equal-time tie on the boundary (PARETO-04)


class BaselineFact(StrictModel):
    """The confirmed counterfactual the economic cost is measured against."""

    kind: BaselineKind | None = Field(description="Null: a fixture's own baseline.")
    net_income_by_month: list[Money]


class ComparisonBasis(StrictModel):
    """One comparison's definitions, the same for every route in it (VIS2-01)."""

    objective_basis: Literal["economic", "direct_spending"]
    planning_start: str = Field(description="The comparison's first month, YYYY-MM.")
    horizon_months: int
    currency: Literal["GBP"]
    scenario: Scenario
    baseline: BaselineFact | None = Field(description="Null: no baseline; direct spending.")
    synthetic: bool


class MeasuredCompletion(StrictModel):
    """A size Task 13a measured to complete with no limit binding."""

    horizon_months: int
    starts_per_concept: int
    concepts: int
    measured_on: date


class Comparator(StrictModel):
    point_id: int
    dominance: DominanceReason
    months_sooner: int = Field(ge=0)
    cost_less: Money


class PointOut(StrictModel):
    point_id: int = Field(description="Its place in the result's equal points.")
    months_to_readiness: int
    objective_cost: SignedMoney
    layer: int | None
    schedule_count: int
    schedules: list[int] = Field(description="The first archive indexes at this point.")
    comparator: Comparator | None = Field(description="Null: in F1, bettered by nothing.")
    dominators: list[int] = Field(
        description="Every point of the layer above that betters it, by point_id."
    )


class FamilyOut(StrictModel):
    family_id: str
    best_layer: int | None = Field(description="The lowest layer of its schedules.")
    schedule_count: int
    best_schedule: int = Field(description="The first archive index at its best layer.")
    actions: list[FamilyAction]
    precedence: list[tuple[int, int]]


class Comparison(StrictModel):
    """A solve's comparison: the scatter's points, the families and what leads."""

    lead: Lead
    code: ResultCode | None = Field(
        description="Spec section 18's code: null when the lead is longer_than_model."
    )
    coverage: SearchCoverage
    stop_reason: StopReason | None
    outcome: Outcome
    layers_exact: bool
    comparator_rule: Literal["soonest_dominator_in_the_layer_above"]
    basis: ComparisonBasis
    label: CatalogueLabel
    limits: M0SearchLimits
    instance: InstanceSize
    narrowings: list[Narrowing]
    completes_at: list[MeasuredCompletion] = Field(
        description="When stopped: sizes measured to complete, beside the narrowings."
    )
    longer_than_model: list[str] = Field(
        description="Options whose completion falls beyond the 24-month model, by variant."
    )
    beyond_horizon: list[str] = Field(
        description="Options within the model whose completion falls beyond this horizon."
    )
    blocking_inputs: list[Finding]
    starting_violations: list[Finding]
    set_aside: list[SetAside]
    feasible_without_milestone: int
    readiness_unknown: int
    schedules_total: int
    points_total: int
    points_shown: int
    families_total: int
    families_shown: int
    points: list[PointOut]
    families: list[FamilyOut]


class ScheduleOut(StrictModel):
    index: int = Field(description="Its place in the archive: stable within a solve.")
    route: list[str]
    family_id: str
    point_id: int
    months_to_readiness: int
    readiness_month: str
    objective_cost: SignedMoney
    direct_cost: Money
    economic_cost: SignedMoney | None
    verdict: Verdict
    qualifications: list[RouteQualification | Qualification]
    conditions: list[Condition]
    preferences: list[Finding]
    loans_to_repay: list[LoanToRepay]
    layer: int | None = Field(description="As the search ranked it: never changed by a view.")
    view_layer: int | None = Field(
        description="Only when reranked: its layer within the view's schedules alone."
    )


class ViewFilter(StrictModel):
    """A view of the archive: it hides and shows, never re-ranks (VIS2-07)."""

    min_months: int | None = None
    max_months: int | None = None
    min_cost_minor: int | None = None
    max_cost_minor: int | None = None
    layer: int | None = Field(default=None, ge=1, le=3)
    family_id: str | None = None

    def holds(self, schedule: Schedule, layer: int | None) -> bool:
        months, cost = schedule.months_to_readiness, schedule.objective_cost.minor_units
        return (
            (self.min_months is None or months >= self.min_months)
            and (self.max_months is None or months <= self.max_months)
            and (self.min_cost_minor is None or cost >= self.min_cost_minor)
            and (self.max_cost_minor is None or cost <= self.max_cost_minor)
            and (self.layer is None or layer == self.layer)
            and (self.family_id is None or schedule.family_id == self.family_id)
        )


class PinnedSchedule(StrictModel):
    schedule: ScheduleOut
    in_view: bool = Field(description="False: pinned outside the view, kept with its badge.")


class SchedulePage(StrictModel):
    rank_scope: Literal["recorded", "within_view"]
    layers_exact: bool
    retained: int = Field(description="Every schedule the archive holds.")
    total: int = Field(description="The schedules the view holds.")
    items: list[ScheduleOut]
    next_cursor: int | None
    pinned: list[PinnedSchedule]


# A chosen route.


class StepQualification(StrEnum):
    """Why a step qualifies its route, from its own records (R9; Task 12b)."""

    PROPOSED_RECORD = "proposed_record"  # a record not reviewed: researched, or the pack's
    ACCEPTED_ASSUMPTION = "accepted_assumption"
    OWN_OPTION = "own_option"  # an option the person added themselves
    SUPPLIED_FIGURES = "supplied_figures"  # a figure the person supplied, not reviewed
    SYNTHETIC = "synthetic"


class RecordReview(StrictModel):
    record: Literal["concept", "offering", "support", "fee_loan"]
    record_id: str
    review_state: RecordState


class StepPayment(StrictModel):
    kind: Literal["fee", "instalment", "extra"]
    amount: Money
    month: str | None = Field(description="Its model month; null: before the start, or unset.")
    due: date | None


class StepRecurring(StrictModel):
    amount: Money
    at_least: bool
    count: int | None


class StepSupport(StrictModel):
    instrument_id: str
    kind: InstrumentKind
    amount: Money | None
    covers_fees_in_full: bool
    paid_to: Literal["provider", "person"]
    eligibility: EligibilityStatus
    award: AwardState
    review_state: RecordState


class StepLoan(StrictModel):
    kind: FeeLoanKind
    amount: Money | None
    eligibility: EligibilityStatus
    application: AwardState
    review_state: RecordState


class StepWork(StrictModel):
    kind: WorkPatternKind
    hours_per_week: int
    net_income: Money


class StepOffer(StrictModel):
    role_class: str | None
    accepted: bool


class RouteStep(StrictModel):
    """One action of the route: a step card's facts and the Gantt's band."""

    variant_id: str
    concept_id: str
    offering_id: str
    kind: ActionKind
    title: str | None
    provider: str | None
    start_date: date | None
    finish_date: date | None
    start_month: str | None
    finish_month: str | None
    usable_month: str | None = Field(description="From when what it grants is usable.")
    active_months: list[str] = Field(description="Every month it touches, beyond the horizon too.")
    weekly_hours: int | None
    payments: list[StepPayment]
    recurring: StepRecurring | None
    supports: list[StepSupport]
    fee_loan: StepLoan | None
    work_pattern: StepWork | None
    wage: Money | None = Field(description="Net pay a month after an accepted offer.")
    offer: StepOffer | None
    application_deadline: date | None
    prerequisites: list[str]
    grants: list[str]
    records: list[RecordReview]
    as_of: date | None = Field(description="Its evidence's retrieval date: never current.")
    supplied: list[SuppliedFact]
    added_by_person: bool
    synthetic: bool
    qualified_by: list[StepQualification]
    sources: list[Citation] = Field(description="The cited spans of its source values.")


class Gate(StrictModel):
    kind: Literal["offer", "award", "application", "loan"]
    variant_id: str
    instrument_id: str | None
    verification: str
    month: str | None = Field(description="The step's start month: the gate comes before it.")


class Wait(StrictModel):
    """Months before readiness in which no step is active."""

    first_month: str
    last_month: str
    months: int


class Milestone(StrictModel):
    # `readiness`: the modelled application-readiness milestone. `verify_assessed_completion`
    # (PLN-04): readiness rests on an assessed completion, so its result is verified there.
    kind: Literal["readiness", "verify_assessed_completion"]
    month: str
    months_to_readiness: int


class MonthRow(StrictModel):
    """One month of the route's money: null where it rests on an amount not known."""

    month: str
    payments: Money | None
    paid_to_provider: Money | None
    support: Money | None
    baseline_income: Money | None
    route_income: Money | None
    pay_difference: SignedMoney | None = Field(description="Baseline less route: lost pay > 0.")
    opening: SignedMoney | None
    early_receipts: Money | None
    living: Money
    debt_service: Money
    lower_bound: SignedMoney | None
    later_receipts: Money | None
    closing: SignedMoney | None


class Liability(StrictModel):
    variant_id: str
    due: str | None
    amount: Money


class DebtMonth(StrictModel):
    month: str
    opening: Money | None
    interest: Money | None
    repayment: Money
    closing: Money | None


class Debt(StrictModel):
    debt_id: str
    months: list[DebtMonth]


class CostParts(StrictModel):
    """Each cost kept apart and named by code (H-13): what the person pays (direct spending),
    the pay they lose or gain against the baseline, and the economic cost, their sum. Which one
    the comparison plots is its `objective_basis`."""

    objective_basis: Literal["economic", "direct_spending"]
    direct_cost: Money | None
    pay_difference: SignedMoney | None = Field(description="Over the horizon: lost pay > 0.")
    economic_cost: SignedMoney | None
    peak_monthly_payment: Money | None
    minimum_prefunded_cash: SignedMoney | None
    reserve: Money | None
    loans_to_repay: list[LoanToRepay] = Field(
        description="Fees a fee loan pays to the provider: a loan to repay, never spending."
    )


class ScenarioCheck(StrictModel):
    """The route under one stress case: no point is invented for one that fails or is unknown."""

    scenario: Scenario
    feasibility: Feasibility
    verdict: Verdict
    months_to_readiness: int | None
    readiness_month: str | None
    objective_cost: SignedMoney | None
    direct_cost: Money | None
    economic_cost: SignedMoney | None
    findings: list[Finding]
    same_as_base: bool


class RouteDetail(StrictModel):
    schedule: ScheduleOut
    label: CatalogueLabel
    basis: ComparisonBasis
    costs: CostParts
    months: list[MonthRow]
    beyond_horizon: list[Liability]
    unscheduled: list[Liability]
    before_start: list[Liability]
    debts: list[Debt]
    steps: list[RouteStep]
    gates: list[Gate]
    waits: list[Wait]
    milestones: list[Milestone]
    scenarios: list[ScenarioCheck] = Field(description="The stress cases, the base apart.")
    self_paid: ScenarioCheck | None = Field(
        description="With a fee loan not yet approved: the route where the person pays."
    )


# The comparison.


def result_code(result: SearchResult) -> ResultCode | None:
    """Spec section 18's codes for what a result is, as facts the web words, never as an
    error: a search a limit stopped, or a complete one that proves no route in the bounded
    model and catalogue."""
    if result.coverage is SearchCoverage.BUDGET_TRUNCATED:
        return "SOLVE_LIMIT_REACHED"
    if result.outcome is Outcome.NO_ROUTE_IN_BOUNDED_MODEL:
        return "NO_ROUTE_IN_BOUNDED_MODEL"
    return None


def comparison(
    result: SearchResult, monthly: MonthlyInput, *, pinned: Sequence[int] = ()
) -> Comparison:
    """The comparison, its projection keeping every ranked point, the extremes and the points
    of any `pinned` schedule."""
    longer, beyond = _long_options(monthly, result.limits)
    lead = _lead(result, longer)
    point_of = _point_index(result)
    pinned_points = {point_of[i] for i in pinned if 0 <= i < len(result.schedules)}
    shown = project(result, pinned_points)
    by_route = _archive_index(result)
    families = [
        FamilyOut(
            family_id=f.family_id,
            best_layer=f.best_layer,
            schedule_count=len(f.routes),
            best_schedule=next(
                by_route[tuple(r)]
                for r in f.routes
                if result.schedules[by_route[tuple(r)]].layer == f.best_layer
            ),
            actions=f.actions,
            precedence=f.precedence,
        )
        for f in result.families[:FAMILIES_SHOWN]
    ]
    at_point: dict[int, list[int]] = {}
    for index, point in enumerate(point_of):
        at_point.setdefault(point, []).append(index)
    return Comparison(
        lead=lead,
        code=None if lead is Lead.LONGER_THAN_MODEL else result_code(result),
        coverage=result.coverage,
        stop_reason=result.stop_reason,
        outcome=result.outcome,
        layers_exact=result.layers_exact,
        comparator_rule=COMPARATOR_RULE,
        basis=basis(monthly),
        label=result.label,
        limits=result.limits,
        instance=result.instance,
        narrowings=result.narrowings,
        completes_at=_completes_at(result),
        longer_than_model=longer,
        beyond_horizon=beyond,
        blocking_inputs=result.blocking_inputs,
        starting_violations=result.starting_violations,
        set_aside=result.set_aside,
        feasible_without_milestone=result.feasible_without_milestone,
        readiness_unknown=result.readiness_unknown,
        schedules_total=len(result.schedules),
        points_total=len(result.points),
        points_shown=len(shown),
        families_total=len(result.families),
        families_shown=len(families),
        points=[_point(result, p, at_point.get(p, [])) for p in shown],
        families=families,
    )


def basis(monthly: MonthlyInput) -> ComparisonBasis:
    inputs, baseline = monthly.inputs, monthly.inputs.baseline
    kinds = {k.value: k for k in BaselineKind}
    return ComparisonBasis(
        objective_basis=inputs.objective_basis,
        planning_start=monthly.months[0],
        horizon_months=inputs.horizon_months,
        currency=inputs.currency,
        scenario=Scenario.BASE,
        baseline=BaselineFact(
            kind=kinds.get(baseline.label),
            net_income_by_month=[_money(m) for m in baseline.net_income_by_month],
        )
        if baseline is not None
        else None,
        synthetic=inputs.synthetic,
    )


def project(
    result: SearchResult, pinned_points: set[int], cap: int = PROJECTION_POINTS
) -> list[int]:
    """The equal points shown, by point_id: every point in F1 to F3 (at most one a month in
    each, so never more than three times the horizon and one), the points of pinned schedules,
    the soonest and the cheapest beyond F3, and then others beyond F3 evenly spaced in order of
    time and cost, up to `cap`. A projection never relabels a sample as the frontier: the
    counts say what is shown."""
    points = result.points
    beyond = [i for i, p in enumerate(points) if p.layer is None]
    keep = {i for i, p in enumerate(points) if p.layer is not None} | pinned_points
    if beyond:
        cheapest = min(beyond, key=lambda i: (points[i].objective_cost.minor_units, i))
        keep |= {beyond[0], cheapest}
    rest = [i for i in beyond if i not in keep]
    room = cap - len(keep)
    if room >= len(rest):
        keep |= set(rest)
    elif room > 0:
        keep |= {rest[(k * len(rest)) // room] for k in range(room)}
    return sorted(keep)


def _point(result: SearchResult, point_id: int, schedules: list[int]) -> PointOut:
    point = result.points[point_id]
    here = (point.months_to_readiness, point.objective_cost.minor_units)
    above = 3 if point.layer is None else point.layer - 1
    dominators = [
        i
        for i, p in enumerate(result.points)
        if p.layer == above
        and above >= 1
        and dominates((p.months_to_readiness, p.objective_cost.minor_units), here)
    ]
    comparator = None
    if dominators:  # points are in order of time, then cost: the first is the soonest
        best = result.points[dominators[0]]
        months = point.months_to_readiness - best.months_to_readiness
        less = point.objective_cost.minor_units - best.objective_cost.minor_units
        dominance = (
            DominanceReason.CHEAPER_SAME_TIME
            if months == 0
            else DominanceReason.SOONER_AND_CHEAPER
            if less > 0
            else DominanceReason.SOONER_SAME_COST
        )
        comparator = Comparator(
            point_id=dominators[0],
            dominance=dominance,
            months_sooner=months,
            cost_less=_money(less),
        )
    return PointOut(
        point_id=point_id,
        months_to_readiness=point.months_to_readiness,
        objective_cost=point.objective_cost,
        layer=point.layer,
        schedule_count=len(schedules),
        schedules=schedules[:POINT_SCHEDULES],
        comparator=comparator,
        dominators=dominators,
    )


def _lead(result: SearchResult, longer: list[str]) -> Lead:
    if result.outcome is Outcome.ROUTES_FOUND:
        return Lead.BEST_TRADE_OFFS_FOUND
    if result.outcome is Outcome.NONE_FOUND_BEFORE_LIMIT:
        return Lead.NONE_FOUND_BEFORE_LIMIT
    if result.outcome is Outcome.UNRESOLVED:
        return Lead.UNRESOLVED
    return (
        Lead.LONGER_THAN_MODEL if _only_length(result, longer) else Lead.NO_ROUTE_IN_BOUNDED_MODEL
    )


def _only_length(result: SearchResult, longer: list[str]) -> bool:
    """Whether options longer than the model are the whole reason nothing fits (review 14A,
    Important 1): some option is longer, and nothing the checker lists rules out any route,
    shorter ones included. No breach in the starting position, no option set aside for a
    breach of its own, no candidate checked and found not feasible, and no subtree cut for a
    breach. Otherwise the bounded model's no-route leads, its violations named, and the long
    options are listed beside it."""
    return (
        bool(longer)
        and not result.starting_violations
        and not any(s.violations for s in result.set_aside)
        and result.not_feasible == 0
        and not any(result.pruned.values())
    )


def _long_options(monthly: MonthlyInput, limits: M0SearchLimits) -> tuple[list[str], list[str]]:
    """Placed options whose completion is usable only after the model's last month (longer
    than it plans), and those after this horizon but within the model. Readiness from an
    option usable from month u is reached u - 1 months after the start."""
    longer, beyond = [], []
    for v in monthly.variants:
        if v.usable_index is None:
            continue
        months = v.usable_index - 1
        if months > limits.max_months:
            longer.append(v.variant_id)
        elif months > monthly.inputs.horizon_months:
            beyond.append(v.variant_id)
    return longer, beyond


def _completes_at(result: SearchResult) -> list[MeasuredCompletion]:
    if result.coverage is SearchCoverage.COMPLETE:
        return []
    row = 12 if result.instance.months <= 12 else 24
    return [
        MeasuredCompletion(
            horizon_months=row,
            starts_per_concept=starts,
            concepts=concepts,
            measured_on=MEASURED_ON,
        )
        for starts, concepts in _MEASURED[row].items()
    ]


def _archive_index(result: SearchResult) -> dict[tuple[str, ...], int]:
    return {tuple(s.route): i for i, s in enumerate(result.schedules)}


def _point_index(result: SearchResult) -> list[int]:
    """Each schedule's equal point."""
    at = {
        (p.months_to_readiness, p.objective_cost.minor_units): i
        for i, p in enumerate(result.points)
    }
    return [at[(s.months_to_readiness, s.objective_cost.minor_units)] for s in result.schedules]


# The archive, paged.


def schedule_page(
    result: SearchResult,
    view: ViewFilter,
    *,
    cursor: int | None = None,
    limit: int = DEFAULT_PAGE,
    rerank: bool = False,
    pinned: Sequence[int] = (),
) -> SchedulePage:
    """The view's schedules in archive order from `cursor`, each with its recorded layer.
    `rerank` (explicit, "best within these choices"): layers over the view's schedules alone,
    beside the recorded ones, never in their place; a hidden dominator never makes a route
    best overall. Pinned schedules come back whether or not the view holds them."""
    point_of = _point_index(result)
    held = [i for i, s in enumerate(result.schedules) if view.holds(s, s.layer)]
    view_layers: dict[int, int | None] = {}
    if rerank:
        ranked = rank(
            [
                (
                    result.schedules[i].months_to_readiness,
                    result.schedules[i].objective_cost.minor_units,
                )
                for i in held
            ]
        )
        view_layers = dict(zip(held, ranked, strict=True))
    start = cursor or 0
    page = [i for i in held if i >= start][: max(1, min(limit, MAX_PAGE))]
    following = [i for i in held if i > page[-1]] if page else []

    def out(index: int) -> ScheduleOut:
        return _schedule_out(result, index, point_of[index], view_layers.get(index))

    held_set = set(held)
    return SchedulePage(
        rank_scope="within_view" if rerank else "recorded",
        layers_exact=result.layers_exact,
        retained=len(result.schedules),
        total=len(held),
        items=[out(i) for i in page],
        next_cursor=following[0] if following else None,
        pinned=[
            PinnedSchedule(schedule=out(i), in_view=i in held_set)
            for i in dict.fromkeys(pinned)
            if 0 <= i < len(result.schedules)
        ],
    )


def _schedule_out(
    result: SearchResult, index: int, point_id: int, view_layer: int | None
) -> ScheduleOut:
    s = result.schedules[index]
    return ScheduleOut(
        index=index,
        route=s.route,
        family_id=s.family_id,
        point_id=point_id,
        months_to_readiness=s.months_to_readiness,
        readiness_month=s.readiness_month,
        objective_cost=s.objective_cost,
        direct_cost=s.direct_cost,
        economic_cost=s.economic_cost,
        verdict=s.verdict,
        qualifications=s.qualifications,
        conditions=s.conditions,
        preferences=s.preferences,
        loans_to_repay=s.loans_to_repay,
        layer=s.layer,
        view_layer=view_layer,
    )


# A chosen route.


def outdated() -> CareerwrightError:
    """The stored solve cannot be rechecked as it was computed (an output stored before its
    input was kept, or a checker that has changed since): solve again, never other numbers."""
    return CareerwrightError(
        ErrorCode.STALE_INPUT_VERSION,
        "This route search is out of date.",
        stage=ErrorStage.PLANNING,
        details={"reason": "solve_outdated"},
    )


def route_detail(result: SearchResult, monthly: MonthlyInput, index: int) -> RouteDetail:
    """A chosen schedule's facts: its base check is `check_route` on the solve's own input and
    must repeat what the search archived, or the solve is out of date."""
    if not 0 <= index < len(result.schedules):
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such route in this search.", stage=ErrorStage.PLANNING
        )
    schedule = result.schedules[index]
    evaluation = evaluate_route(monthly, schedule.route)
    base = evaluation.scenario(Scenario.BASE)
    if (
        base.input_version != result.input_version
        or base.months_to_readiness != schedule.months_to_readiness
        or base.objective_cost != schedule.objective_cost
        or base.direct_cost != schedule.direct_cost
        or base.verdict is not schedule.verdict
    ):
        raise outdated()
    variants = [monthly.variant(v) for v in schedule.route]
    stresses = [_scenario(c, base) for c in evaluation.checks if c.scenario is not Scenario.BASE]
    loan_pending = RouteQualification.CONDITIONAL_LOAN in base.qualifications
    direct = base.ledgers.direct
    return RouteDetail(
        schedule=_schedule_out(result, index, _point_index(result)[index], None),
        label=result.label,
        basis=basis(monthly),
        costs=CostParts(
            objective_basis=monthly.inputs.objective_basis,
            direct_cost=base.direct_cost,
            pay_difference=_signed(base.ledgers.income.difference_minor),
            economic_cost=base.economic_cost,
            peak_monthly_payment=base.peak_monthly_payment,
            minimum_prefunded_cash=base.minimum_prefunded_cash,
            reserve=_money_or_none(base.ledgers.liquidity.reserve_minor),
            loans_to_repay=base.loans_to_repay,
        ),
        months=_months(base),
        beyond_horizon=[_liability(x) for x in direct.beyond_horizon],
        unscheduled=[_liability(x) for x in direct.unscheduled],
        before_start=[_liability(x) for x in direct.before_start],
        debts=[
            Debt(
                debt_id=d.debt_id,
                months=[
                    DebtMonth(
                        month=m.month,
                        opening=_money_or_none(m.opening_minor),
                        interest=_money_or_none(m.interest_minor),
                        repayment=_money(m.repayment_minor),
                        closing=_money_or_none(m.closing_minor),
                    )
                    for m in d.months
                ],
            )
            for d in base.ledgers.debts
        ],
        steps=[_step(monthly, v) for v in variants],
        gates=[
            Gate(
                kind=c.kind,
                variant_id=c.variant_id,
                instrument_id=c.instrument_id,
                verification=c.verification,
                month=_label(monthly, monthly.variant(c.variant_id).start_index),
            )
            for c in base.conditions
        ],
        waits=_waits(monthly, variants, schedule.months_to_readiness),
        milestones=_milestones(base, schedule),
        scenarios=stresses,
        self_paid=next(s for s in stresses if s.scenario is Scenario.NO_AWARD)
        if loan_pending
        else None,
    )


def _scenario(check: RouteCheck, base: RouteCheck) -> ScenarioCheck:
    return ScenarioCheck(
        scenario=check.scenario,
        feasibility=check.feasibility,
        verdict=check.verdict,
        months_to_readiness=check.months_to_readiness,
        readiness_month=check.readiness_month,
        objective_cost=check.objective_cost,
        direct_cost=check.direct_cost,
        economic_cost=check.economic_cost,
        findings=check.findings,
        # Everything the check found, its ledgers included (pay lost to no offer changes the
        # income even where the plotted cost does not), but the scenario's own name.
        same_as_base=check.model_dump(exclude={"scenario"})
        == base.model_dump(exclude={"scenario"}),
    )


def _months(check: RouteCheck) -> list[MonthRow]:
    ledgers = check.ledgers
    rows = []
    for direct, income, cash in zip(
        ledgers.direct.months, ledgers.income.months, ledgers.liquidity.months, strict=True
    ):
        rows.append(
            MonthRow(
                month=direct.month,
                payments=_money_or_none(direct.payments_minor),
                paid_to_provider=_money_or_none(direct.paid_to_provider_minor),
                support=_money_or_none(direct.support_minor),
                baseline_income=_money_or_none(income.baseline_minor),
                route_income=_money_or_none(income.route_minor),
                pay_difference=_signed(income.difference_minor),
                opening=_signed(cash.opening_minor),
                early_receipts=_money_or_none(cash.early_receipts_minor),
                living=_money(cash.living_minor),
                debt_service=_money(cash.debt_service_minor),
                lower_bound=_signed(cash.lower_bound_minor),
                later_receipts=_money_or_none(cash.later_receipts_minor),
                closing=_signed(cash.closing_minor),
            )
        )
    return rows


def _step(monthly: MonthlyInput, v: CompiledVariant) -> RouteStep:
    # The compiler's order: the concept's state, the offering's, each support's, the loan's.
    states = v.review_states
    records = [
        RecordReview(record="concept", record_id=v.concept_id, review_state=states[0]),
        RecordReview(record="offering", record_id=v.offering_id, review_state=states[1]),
        *(
            RecordReview(record="support", record_id=s.instrument_id, review_state=s.review_state)
            for s in v.supports
        ),
        *(
            [
                RecordReview(
                    record="fee_loan",
                    record_id=v.variant_id,
                    review_state=v.tuition_fee_loan.review_state,
                )
            ]
            if v.tuition_fee_loan is not None
            else []
        ),
    ]
    qualified = [
        q
        for q, holds in (
            (StepQualification.PROPOSED_RECORD, RecordState.PROPOSED in states),
            (StepQualification.ACCEPTED_ASSUMPTION, RecordState.ACCEPTED_ASSUMPTION in states),
            (StepQualification.OWN_OPTION, v.added_by_person),
            (StepQualification.SUPPLIED_FIGURES, bool(v.supplied)),
            (StepQualification.SYNTHETIC, v.synthetic),
        )
        if holds
    ]
    cited = [
        *(p.cited for p in v.payments),
        *([v.recurring.cited] if v.recurring is not None else []),
        *(s.cited for s in v.supports),
        *([v.tuition_fee_loan.cited] if v.tuition_fee_loan is not None else []),
        *([v.work_pattern.cited] if v.work_pattern is not None else []),
        *([v.wage.cited] if v.wage is not None else []),
    ]
    loan, pattern = v.tuition_fee_loan, v.work_pattern
    return RouteStep(
        variant_id=v.variant_id,
        concept_id=v.concept_id,
        offering_id=v.offering_id,
        kind=v.kind,
        title=v.title,
        provider=v.provider,
        start_date=v.start_date,
        finish_date=v.finish_date,
        start_month=_label(monthly, v.start_index),
        finish_month=_label(monthly, v.finish_index),
        usable_month=_label(monthly, v.usable_index),
        active_months=[monthly.month_label(i) for i in v.active],
        weekly_hours=v.weekly_hours,
        payments=[
            StepPayment(
                kind=p.kind,
                amount=_money(p.amount_minor),
                month=_label(monthly, v.start_index + p.offset)
                if p.offset is not None and v.start_index is not None
                else None,
                due=p.due,
            )
            for p in v.payments
        ],
        recurring=StepRecurring(
            amount=v.recurring.amount, at_least=v.recurring.at_least, count=v.recurring.count
        )
        if v.recurring is not None
        else None,
        supports=[
            StepSupport(
                instrument_id=s.instrument_id,
                kind=s.kind,
                amount=s.amount,
                covers_fees_in_full=s.covers_fees_in_full,
                paid_to=s.paid_to,
                eligibility=s.eligibility,
                award=s.award,
                review_state=s.review_state,
            )
            for s in v.supports
        ],
        fee_loan=StepLoan(
            kind=loan.kind,
            amount=loan.amount,
            eligibility=loan.eligibility,
            application=loan.application,
            review_state=loan.review_state,
        )
        if loan is not None
        else None,
        work_pattern=StepWork(
            kind=pattern.kind, hours_per_week=pattern.hours_per_week, net_income=pattern.net_income
        )
        if pattern is not None
        else None,
        wage=v.wage.net_income if v.wage is not None else None,
        offer=StepOffer(role_class=v.offer_gate.role_class, accepted=v.offer_gate.accepted)
        if v.offer_gate is not None
        else None,
        application_deadline=v.application_deadline,
        prerequisites=v.prerequisites,
        grants=v.grants,
        records=records,
        as_of=v.as_of,
        supplied=v.supplied,
        added_by_person=v.added_by_person,
        synthetic=v.synthetic,
        qualified_by=qualified,
        # The person's own figures are named by `supplied` and their answers: a person
        # citation's locator is Careerwright's note, never served (R11).
        sources=list(dict.fromkeys(c for c in cited if c.basis is not CitationBasis.PERSON)),
    )


def _waits(monthly: MonthlyInput, steps: list[CompiledVariant], months: int) -> list[Wait]:
    """Runs of months 1 to `months` (readiness is reached at that month boundary) that no step
    touches: waiting for a start, or for what a step grants to become usable."""
    touched = {i for v in steps for i in v.active}
    waits: list[Wait] = []
    run: list[int] = []
    for index in [*range(1, months + 1), None]:
        if index is not None and index not in touched:
            run.append(index)
            continue
        if run:
            waits.append(
                Wait(
                    first_month=monthly.month_label(run[0]),
                    last_month=monthly.month_label(run[-1]),
                    months=len(run),
                )
            )
            run = []
    return waits


def _milestones(check: RouteCheck, schedule: Schedule) -> list[Milestone]:
    found = [
        Milestone(
            kind="readiness",
            month=schedule.readiness_month,
            months_to_readiness=schedule.months_to_readiness,
        )
    ]
    if check.readiness_state is ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION:
        found.append(
            Milestone(
                kind="verify_assessed_completion",
                month=schedule.readiness_month,
                months_to_readiness=schedule.months_to_readiness,
            )
        )
    return found


def _liability(item: Owed) -> Liability:
    return Liability(variant_id=item.variant_id, due=item.due, amount=_money(item.amount_minor))


def _label(monthly: MonthlyInput, index: int | None) -> str | None:
    return monthly.month_label(index) if index is not None else None


def _money(minor: int) -> Money:
    return Money(minor_units=minor, currency="GBP")


def _money_or_none(minor: int | None) -> Money | None:
    return _money(minor) if minor is not None else None


def _signed(minor: int | None) -> SignedMoney | None:
    return SignedMoney(minor_units=minor, currency="GBP") if minor is not None else None
