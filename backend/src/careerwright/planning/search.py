"""The route search (spec section 12, OPT-1, ROU-1 and "Consequence of the M0 limits"; plan
Sprint 6a: S6.1, S6.2, S6.5, S6.7). Deterministic for a fixed input, and pure but for the
clock it reads for the wall-time limit: no SQL, no network, no model.

**The declared tree** (S6.1). Concepts are taken in a canonical order: the earliest start among
a concept's variants, then its ID; a concept's variants by start, then ID. A node is a selected
set in that order, and its children each add one variant of a later concept, so every allowed
set is visited exactly once; order and parallelism come from the variants' own dates, never
from permuting a list. Allowed: at most `max_selected_actions` (six), one start per concept,
one concept per exclusive group and one bridge role (a `work` action: spec section 12, "at
most one bridge-role transition"). The empty route is the root, because zero actions can
already reach readiness (RDY-1). Every candidate is checked by the Task 11 route checker
(`check_route`) in the base scenario: its gates, timetable, cash, workload and the capability
model's readiness milestone (ADR 0013).

**Sound pruning** (S6.2; `PRUNING_VERSION`). A subtree is cut only when no route in it can be
feasible. Each proof rests on how `check_route` computes a finding in the base scenario, where
every selected variant is present on its own dates, and on one fact of the tree: a subtree only
adds variants of later concepts.

1. *Input-level unknowns.* The empty route's unresolved findings (`limit_unknown`,
   `baseline_missing`, `workload_unknown` for unstated availability, `work_rights_unknown` and
   `work_rights_not_held`) come from the inputs alone, so every route has them: nothing is
   checked further, and the result names them.
2. *A variant no route can use* is set aside before the search: unknown dates, cost, entry
   requirements or weekly hours, a payment due before the planning start, a start before it,
   an application deadline already passed, the person's "no" to its entry requirements, an
   eligibility condition of its stated fee not confirmed, supports whose stacking is not
   confirmed, its own tuition fee loan counted with no amount stated (Task 12c), or, alone, a
   direct cost or a month's payments above its cap, or two schemes recorded as exclusive among
   its own supports. Each is computed
   from the variant by itself (its dates, its payments, own support and own loan, its hours, the
   person's answers about it), so every route containing it repeats it, or, for unknown weekly
   hours, is unknown or over the limit in each month the variant is active. The screen runs
   before every other cut, the empty route's included, so an option set aside for an unknown
   always reaches the outcome; its record keeps every unknown and every breach its own check
   found, apart.
3. *Spend caps.* A route's direct cost is the sum of each variant's own net cost, never below
   zero (a variant's support and its tuition fee loan reduce only its own fees; the fee a loan
   pays is in neither figure), and a month's payments are the sum of
   each variant's own payments in it, beside debt repayments fixed by the inputs. Adding a
   variant never lowers either, so a child whose sum already exceeds the direct-spend cap or a
   month's payment cap is never checked, nor anything below it; nor is a node whose
   repayments alone already exceed that cap. The sums come from each variant checked alone,
   so a node whose own rows are null (supports not yet confirmed to combine) is summed alike.
4. *Conflicting work patterns, session clashes, a second conditional job transition and two
   schemes recorded as exclusive* persist: both variants stay active in that month, with the
   same patterns and sessions, and adding a variant never takes away an offer still to be
   accepted or a support already counted.
5. *Workload in a month.* The load is the job's hours, the fixed commitments and the active
   variants' weekly hours. The job's hours come from the first variant in route order that is
   active with a work pattern, else from the continuation. Later variants come later in route
   order, so the job's hours can change only if no selected variant sets them in that month
   and some later variant active then has a work pattern. Otherwise every extension's load is
   at least this one's.
6. *A prerequisite* not usable by a variant's start stays unusable unless a later variant
   grants it and is usable by then: every variant in the search has dates (rule 2).

Never pruned: the reserve and the deficit cap (a later receipt, such as pay, a wage or support
paid to the person, can lift a month); an application completing too late or in its deadline's
month (a later application can be in time); readiness (never on current readiness); and the
objectives (no dominance pruning: F2 and F3 need dominated schedules, and economic cost can
fall as a route grows).

**The archive** (S6.5) keeps every distinct feasible schedule that reaches the readiness
milestone, dominated ones included, in memory under the archive cap (L0 keeps no disk archive:
spec section 22). A feasible schedule without the milestone is counted, never archived: it is
not a route to the target.

**Two stages** (S6.8; review 13a, M3). The search stage (`search_archive`) walks the tree under
the M0 limits, read before each candidate on its own clock. The rank stage (`rank_archive`)
then layers the whole archive (`layers.rank`, qualified against Sprint 6a's peeling) and groups
families and equal points for presentation only (`families`), on its own clock and under its
own limit, `RANK_SECONDS`, read before each of its passes: no result claims ranks until it has
finished, and one that reaches its limit gives none (`RankLimitReachedError`). Each stage
records its own time (`elapsed_ms`, `rank_ms`). `search_routes` runs both.

**Cancellation** (DUR-05). A cancel check, read with the limits before each candidate and
before each rank pass, stops the search where it is (`SearchCancelledError`): a cancelled
search gives no result, never a truncated one.

**Coverage** (S6.7). `complete` only after the whole declared tree is exhausted under these
rules; a run stopped by a limit is `budget_truncated` with its exact reason, keeps everything
it found, and is never "no route". A complete run with an empty archive is
`NO_ROUTE_IN_BOUNDED_MODEL` only if nothing it met was unresolved (an unknown is never a no),
or if the starting position breaks a limit no option can lower: existing repayments above the
payment cap rule out every route whatever is unknown. Never pruned on, and never a variant's
own: one scheme on two options before the person confirms it pays for both (unresolved).
"""

import time
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.capability.readiness import Qualification, ReadinessState
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.money import Money, SignedMoney
from careerwright.planning.catalogue import ActionKind, CatalogueLabel
from careerwright.planning.checker import (
    Condition,
    Feasibility,
    Finding,
    FindingCode,
    FindingKind,
    RouteCheck,
    RouteQualification,
    Scenario,
    Verdict,
    check_route,
)
from careerwright.planning.compiler import CompiledVariant, MonthlyInput
from careerwright.planning.families import (
    EqualPoint,
    Family,
    FamilyKey,
    equal_points,
    families,
    family_key,
)
from careerwright.planning.layers import rank
from careerwright.planning.ledgers import LoanToRepay

ALGORITHM_VERSION = "canonical-dfs-1"
PRUNING_VERSION = "sound-pruning-5"  # the six rules above: change it with any rule
# The rank stage's own limit (S6.8). Ranking the archive cap's 50,000 schedules takes about a
# second (`tools.rank_benchmark`), so it is a bound, never the expected case.
RANK_SECONDS = 5
_READINESS_UNKNOWN = frozenset(
    {ReadinessState.NOT_YET_ASSESSED, ReadinessState.INSUFFICIENT_COVERAGE}
)
# Rule 2: a variant's own findings, which every route containing it repeats. Task 12a's are
# computed from the variant alone too: the person's "no" to its entry requirements, its stated
# fee's unconfirmed eligibility conditions, and its supports' unconfirmed stacking.
_OWN_UNRESOLVED = frozenset(
    {
        FindingCode.DATES_UNKNOWN,
        FindingCode.COST_UNKNOWN,
        FindingCode.ENTRY_REQUIREMENTS_UNCONFIRMED,
        FindingCode.PAYMENT_BEFORE_START,
        FindingCode.WORKLOAD_UNKNOWN,
        FindingCode.ENTRY_REQUIREMENTS_NOT_MET,
        FindingCode.ELIGIBILITY_UNCONFIRMED,
        FindingCode.STACKING_UNCONFIRMED,
        # Task 12c: its own tuition fee loan counts but states no amount.
        FindingCode.LOAN_AMOUNT_UNKNOWN,
    }
)
_OWN_VIOLATIONS = frozenset(
    {
        FindingCode.STARTS_BEFORE_PLANNING,
        FindingCode.DIRECT_SPEND_CAP,
        FindingCode.MONTHLY_PAYMENT_CAP,
        FindingCode.EXCLUSIVE_SCHEMES,  # two exclusive schemes on the one option
    }
)
# A starting breach the inputs alone fix: no option, known or unknown, can lower existing
# repayments, so every route breaks it and the truth is no route, whatever else is unknown
# (review 12a, Important 3). Any other starting breach some option could relieve (receipts
# lift the reserve, pay the deficit, a work pattern the workload), so it keeps the outcome
# open while something is unknown.
_FIXED_BY_INPUTS = frozenset({FindingCode.REPAYMENTS_ABOVE_PAYMENT_CAP})


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class M0SearchLimits(StrictModel):
    """Spec section 18's `M0SearchLimits`: the declared model's bounds, then the run's caps."""

    max_actions: int = Field(default=24, ge=1, le=24)  # concepts in one target's search
    max_starts_per_action: int = Field(default=2, ge=1, le=2)
    max_selected_actions: int = Field(default=6, ge=0, le=6)
    max_months: int = Field(default=24, ge=1, le=24)
    wall_seconds: int = Field(default=30, ge=1, le=30)
    max_states: int = Field(default=1_000_000, ge=1, le=1_000_000)
    max_feasible_archive: int = Field(default=50_000, ge=1, le=50_000)


class SearchCoverage(StrEnum):
    """`search_coverage` (spec section 12)."""

    COMPLETE = "complete"
    BUDGET_TRUNCATED = "budget_truncated"


class StopReason(StrEnum):
    STATE_LIMIT = "state_limit"
    WALL_TIME_LIMIT = "wall_time_limit"
    ARCHIVE_LIMIT = "archive_limit"


class Outcome(StrEnum):
    ROUTES_FOUND = "routes_found"  # lead with "Best trade-offs found"
    NONE_FOUND_BEFORE_LIMIT = "none_found_before_limit"  # stopped early: never "no route"
    UNRESOLVED = "unresolved"  # complete, nothing proved feasible, something unknown
    # Complete, and either nothing unknown or a starting breach no option can lower.
    NO_ROUTE_IN_BOUNDED_MODEL = "no_route_in_bounded_model"


class PruningRule(StrEnum):
    INPUT_UNRESOLVED = "input_unresolved"
    DIRECT_SPEND_CAP = "direct_spend_cap"
    MONTHLY_PAYMENT_CAP = "monthly_payment_cap"
    CONFLICTING_WORK_PATTERNS = "conflicting_work_patterns"
    SESSION_CLASH = "session_clash"
    JOB_TRANSITIONS = "job_transitions"
    EXCLUSIVE_SCHEMES = "exclusive_schemes"
    WORKLOAD = "workload"
    PREREQUISITE = "prerequisite"


class Narrowing(StrEnum):
    """What could help a stopped search (spec section 12): codes the web words as what could
    help, never as a promise that the narrowed search finishes."""

    FEWER_CONCEPTS = "fewer_concepts"
    ONE_START = "one_start"
    SHORTER_HORIZON = "shorter_horizon"


# Named from what stopped the search. Fewer concepts or one start shrink the tree of selected
# sets, which every limit counts. A shorter horizon leaves that tree as it is and only makes
# each check quicker (Task 13a measured about 13 s at 12 months against 26 s at 24), so it can
# help only a search the clock stopped.
_NARROWINGS = {
    StopReason.STATE_LIMIT: (Narrowing.FEWER_CONCEPTS, Narrowing.ONE_START),
    StopReason.ARCHIVE_LIMIT: (Narrowing.FEWER_CONCEPTS, Narrowing.ONE_START),
    StopReason.WALL_TIME_LIMIT: (
        Narrowing.FEWER_CONCEPTS,
        Narrowing.ONE_START,
        Narrowing.SHORTER_HORIZON,
    ),
}


class InstanceSize(StrictModel):
    concepts: int
    starts_per_concept: int  # the most any concept has
    months: int
    variants: int
    selection_space: int  # the allowed selected sets before any pruning


class SetAside(StrictModel):
    """A variant no route can contain (rule 2), with everything its own check found."""

    variant_id: str
    codes: list[FindingCode]  # its own findings that set it aside
    kind: Literal[FindingKind.VIOLATION, FindingKind.UNRESOLVED]  # a breach of its own, or not
    unresolved: list[FindingCode]  # every unknown it has: what the person can confirm
    # Every rule it breaks as stated, alone, that the person's starting position does not
    # already break (those are the result's `starting_violations`): what rules it out.
    violations: list[FindingCode]


class Schedule(StrictModel):
    """One feasible schedule reaching the milestone: its identity, objectives and check."""

    route: list[str]  # variant IDs in canonical order
    family_id: str
    months_to_readiness: int
    readiness_month: str
    objective_cost: SignedMoney  # economic or direct only, as the input's objective basis
    direct_cost: Money
    economic_cost: SignedMoney | None
    verdict: Verdict
    qualifications: list[RouteQualification | Qualification]
    conditions: list[Condition]
    preferences: list[Finding]  # an optional preference left unmet: never a hard limit
    # What a tuition fee loan paid to the provider pays, as a loan to repay (Task 12c). The
    # default reads a result stored before it existed.
    loans_to_repay: list[LoanToRepay] = Field(default_factory=list)
    layer: int | None  # 1 to 3; None: beyond the third layer


class SearchResult(StrictModel):
    input_version: str
    label: CatalogueLabel
    target_title: str
    matrix_version: str
    definition_version: str
    objective_basis: Literal["economic", "direct_spending"]
    scenario: Scenario
    algorithm_version: str
    pruning_version: str
    limits: M0SearchLimits
    instance: InstanceSize
    canonical_order: list[str]  # concept IDs
    coverage: SearchCoverage
    stop_reason: StopReason | None
    outcome: Outcome
    layers_exact: bool  # only with complete coverage, and only over the declared model
    expanded_states: int  # candidates checked
    feasible_without_milestone: int
    readiness_unknown: int  # of those, readiness the capability model cannot yet assess
    unresolved: int
    not_feasible: int
    blocking_inputs: list[Finding]  # input-level unknowns: every route has them
    # What the person's starting position (the empty route) already breaks: told once here,
    # never blamed on an option.
    starting_violations: list[Finding]
    set_aside: list[SetAside]
    pruned: dict[PruningRule, int]  # subtrees cut, by rule
    unexplored_branches: int  # pending when the run stopped; 0 when complete
    elapsed_ms: int  # the search stage, until it ended or stopped: what its 30 s limit reads
    rank_ms: int  # the rank stage, on its own clock
    rank_seconds: int  # the rank stage's own limit
    narrowings: list[Narrowing]  # when stopped: what could help, by what stopped it
    schedules: list[Schedule]  # the whole encountered archive, dominated schedules included
    families: list[Family]
    points: list[EqualPoint]


class SearchCancelledError(Exception):
    """The person cancelled the run: the search stopped at its next check. Never a result."""


class RankLimitReachedError(Exception):
    """The rank stage reached its own limit before it finished: no result claims ranks."""


def _never() -> bool:
    return False


def search_routes(
    monthly: MonthlyInput,
    *,
    limits: M0SearchLimits | None = None,
    clock: Callable[[], float] = time.monotonic,
    cancelled: Callable[[], bool] = _never,
) -> SearchResult:
    """Every feasible schedule to the target in the declared model, or a truthful stop: the
    search stage, then the rank stage."""
    archive = search_archive(monthly, limits=limits, clock=clock, cancelled=cancelled)
    return rank_archive(archive, clock=clock, cancelled=cancelled)


def search_archive(
    monthly: MonthlyInput,
    *,
    limits: M0SearchLimits | None = None,
    clock: Callable[[], float] = time.monotonic,
    cancelled: Callable[[], bool] = _never,
) -> "Archive":
    """The search stage: every feasible schedule met before the tree ended or a limit stopped
    it, not yet ranked. Raises `SearchCancelledError` once `cancelled` says so."""
    search = _Search(monthly, limits or M0SearchLimits(), clock, cancelled)
    search.run()
    return Archive(search)


def rank_archive(
    archive: "Archive",
    *,
    clock: Callable[[], float] = time.monotonic,
    cancelled: Callable[[], bool] = _never,
    limit_seconds: int = RANK_SECONDS,
) -> SearchResult:
    """The rank stage: the three layers over the whole archive, then its families and equal
    points, each pass begun only inside `limit_seconds` on the stage's own clock. Raises
    `RankLimitReachedError` or `SearchCancelledError`, never a result claiming ranks it lacks."""
    search = archive.search
    started = clock()

    def check() -> None:
        if cancelled():
            raise SearchCancelledError
        if clock() - started >= limit_seconds:
            raise RankLimitReachedError

    check()
    layers = rank(
        [(s.months_to_readiness, s.objective_cost.minor_units) for s, _ in search.archive]
    )
    check()
    schedules = [
        schedule.model_copy(update={"layer": layer})
        for (schedule, _), layer in zip(search.archive, layers, strict=True)
    ]
    check()
    keys = [key for _, key in search.archive]
    grouped = families([(s.route, key, s.layer) for s, key in zip(schedules, keys, strict=True)])
    check()
    points = equal_points(
        [(s.route, s.months_to_readiness, s.objective_cost, s.layer) for s in schedules]
    )
    rank_ms = round((clock() - started) * 1000)
    return search.result(schedules, grouped, points, rank_ms=rank_ms, rank_seconds=limit_seconds)


class Archive:
    """The search stage's end: every distinct feasible schedule it met, dominated ones
    included, in the order met, with what the search found. Only `rank_archive` reads it."""

    def __init__(self, search: "_Search") -> None:
        self.search = search

    def __len__(self) -> int:
        return len(self.search.archive)


class _LimitError(Exception):
    """A run's limit was reached: it unwinds the search, which then reports where it stopped."""

    def __init__(self, reason: StopReason) -> None:
        self.reason = reason


@dataclass(frozen=True)
class _Node:
    route: tuple[CompiledVariant, ...]  # canonical order
    position: int  # its last concept's place in the canonical order; -1 for the root
    check: RouteCheck
    groups: frozenset[str]
    bridge: bool  # a bridge role is selected


@dataclass(frozen=True)
class _Spend:
    direct: int
    payments: tuple[int, ...]  # by month of the horizon


class _Search:
    def __init__(
        self,
        monthly: MonthlyInput,
        limits: M0SearchLimits,
        clock: Callable[[], float],
        cancelled: Callable[[], bool],
    ) -> None:
        check_scope(monthly, limits)
        self.monthly = monthly
        self.limits = limits
        self.clock = clock
        self.cancelled = cancelled
        self.started = clock()
        self.concepts = _canonical(monthly.variants)
        self.positions = {c[0].concept_id: n for n, c in enumerate(self.concepts)}
        self.month_index = {label: n for n, label in enumerate(monthly.months, 1)}
        self.expanded = 0
        self.archive: list[tuple[Schedule, FamilyKey]] = []  # as encountered
        self.without_milestone = 0
        self.readiness_unknown = 0
        self.unresolved = 0
        self.not_feasible = 0
        self.blocking: list[Finding] = []
        self.starting: list[Finding] = []  # the empty route's violations: the starting position
        self.set_aside: list[SetAside] = []
        self.excluded: set[str] = set()
        self.spend: dict[str, _Spend] = {}
        self.pruned: Counter[PruningRule] = Counter()
        self.unexplored = 0
        self.stop: StopReason | None = None
        self.elapsed_ms = 0  # the search's own time, until it stops: not the result's assembly

    def run(self) -> None:
        try:
            self._search()
        except _LimitError as stopped:
            self.stop = stopped.reason
        self.elapsed_ms = round((self.clock() - self.started) * 1000)

    # The tree.

    def _search(self) -> None:
        check = self._evaluate(())
        root = _Node(route=(), position=-1, check=check, groups=frozenset(), bridge=False)
        self.blocking = [f for f in check.findings if f.kind is FindingKind.UNRESOLVED]
        self.starting = [f for f in check.findings if f.kind is FindingKind.VIOLATION]
        if self.blocking:
            self.pruned[PruningRule.INPUT_UNRESOLVED] += 1  # rule 1
            return
        # The screen comes before any cut, so every option set aside for an unknown reaches
        # the outcome, however early the search ends (review 13a, Important 1): the cut below
        # sees an undated option as never active, so it could otherwise hide one.
        singles = self._screen(root)
        rule = self._cut(root) if singles else None
        if rule is not None:
            self.pruned[rule] += 1
            return
        for n, single in enumerate(singles):
            try:
                self._expand(single)
            except _LimitError:
                self.unexplored += len(singles) - n - 1
                raise

    def _screen(self, root: _Node) -> list[_Node]:
        """Every variant alone, in canonical order: rule 2 sets some aside for the whole tree."""
        variants = [v for concept in self.concepts for v in concept]
        checked: list[tuple[CompiledVariant, RouteCheck]] = []
        for n, variant in enumerate(variants):
            try:
                checked.append((variant, self._evaluate((variant,))))
            except _LimitError:
                self.unexplored += len(variants) - n
                raise
        singles = []
        for variant, check in checked:
            codes = self._own_findings(variant, check)
            if codes:
                violation = any(
                    c in _OWN_VIOLATIONS or c is FindingCode.APPLICATION_TOO_LATE for c in codes
                )
                unresolved = _codes(check, FindingKind.UNRESOLVED)
                unresolved += [c for c in codes if c in _OWN_UNRESOLVED and c not in unresolved]
                self.set_aside.append(
                    SetAside(
                        variant_id=variant.variant_id,
                        codes=codes,
                        kind=FindingKind.VIOLATION if violation else FindingKind.UNRESOLVED,
                        unresolved=unresolved,
                        violations=self._own_violations(check),
                    )
                )
                self.excluded.add(variant.variant_id)
                continue
            self.spend[variant.variant_id] = _spend(check)
            singles.append(self._child(root, variant, check))
        return singles

    def _expand(self, node: _Node) -> None:
        later = self._candidates(node)
        if not later:
            return
        rule = self._cut(node)
        if rule is not None:
            self.pruned[rule] += 1
            return
        children = []
        for variant in later:
            exceeded = self._exceeds(node, variant)
            if exceeded is None:
                children.append(variant)
            else:
                self.pruned[exceeded] += 1  # rule 3: never checked, nor anything below it
        for n, variant in enumerate(children):
            try:
                check = self._evaluate((*node.route, variant))
            except _LimitError:
                self.unexplored += len(children) - n
                raise
            try:
                self._expand(self._child(node, variant, check))
            except _LimitError:
                self.unexplored += len(children) - n - 1
                raise

    def _candidates(self, node: _Node) -> list[CompiledVariant]:
        """The children the declared tree allows: one variant of a later concept."""
        if len(node.route) >= self.limits.max_selected_actions:
            return []
        found = []
        for concept in self.concepts[node.position + 1 :]:
            group = concept[0].exclusive_group
            if group is not None and group in node.groups:
                continue
            found += [
                v
                for v in concept
                if v.variant_id not in self.excluded
                and not (node.bridge and v.kind is ActionKind.WORK)
            ]
        return found

    def _child(self, node: _Node, variant: CompiledVariant, check: RouteCheck) -> _Node:
        group = variant.exclusive_group
        return _Node(
            route=(*node.route, variant),
            position=self.positions[variant.concept_id],
            check=check,
            groups=node.groups | {group} if group is not None else node.groups,
            bridge=node.bridge or variant.kind is ActionKind.WORK,
        )

    def _evaluate(self, route: tuple[CompiledVariant, ...]) -> RouteCheck:
        if self.cancelled():
            raise SearchCancelledError  # never a limit: a cancelled search gives no result
        if self.expanded >= self.limits.max_states:
            raise _LimitError(StopReason.STATE_LIMIT)
        if self.clock() - self.started >= self.limits.wall_seconds:
            raise _LimitError(StopReason.WALL_TIME_LIMIT)
        check = check_route(self.monthly, [v.variant_id for v in route])
        self.expanded += 1
        if check.feasibility is Feasibility.UNRESOLVED:
            self.unresolved += 1
        elif check.feasibility is Feasibility.NOT_FEASIBLE_IN_MODEL:
            self.not_feasible += 1
        elif check.months_to_readiness is None:
            self.without_milestone += 1
            if check.readiness_state in _READINESS_UNKNOWN:
                self.readiness_unknown += 1
        elif len(self.archive) >= self.limits.max_feasible_archive:
            raise _LimitError(StopReason.ARCHIVE_LIMIT)
        else:
            key = family_key(route)
            self.archive.append((_schedule(route, check, key), key))
        return check

    def _own_violations(self, check: RouteCheck) -> list[FindingCode]:
        """The rules a variant breaks alone that the starting position does not already break
        in the same month (re-review 13a, I2): the person's own breach, such as a reserve
        already short or hours already over, is told once on the result, never blamed on the
        option, which may even be the one that would cure it."""
        starting = {(f.code, f.month) for f in self.starting}
        found: list[FindingCode] = []
        for finding in check.findings:
            own = (finding.code, finding.month) not in starting
            if finding.kind is FindingKind.VIOLATION and own and finding.code not in found:
                found.append(finding.code)
        return found

    # The pruning rules (the module docstring has their proofs).

    def _own_findings(self, variant: CompiledVariant, check: RouteCheck) -> list[FindingCode]:
        """Rule 2: what this variant alone brings into every route containing it."""
        inputs = self.monthly.inputs
        passed = (
            variant.application_deadline is not None
            and variant.application_deadline < inputs.planning_start
            and variant.application_gate not in inputs.initial_gates
        )
        codes: list[FindingCode] = []
        for finding in check.findings:
            own = finding.code in _OWN_UNRESOLVED or finding.code in _OWN_VIOLATIONS
            if (own or (finding.code is FindingCode.APPLICATION_TOO_LATE and passed)) and (
                finding.code not in codes
            ):
                codes.append(finding.code)
        # Its weekly hours are unknown in a month it is active, even where the checker reports
        # that month as over the limit because the known load already is.
        untimed = (
            variant.placed
            and variant.weekly_hours is None
            and any(1 <= m <= inputs.horizon_months for m in variant.active)
        )
        if untimed and FindingCode.WORKLOAD_UNKNOWN not in codes:
            codes.append(FindingCode.WORKLOAD_UNKNOWN)
        return codes

    def _exceeds(self, node: _Node, variant: CompiledVariant) -> PruningRule | None:
        """Rule 3: the child's direct cost or a month's payments already exceed their cap. A
        route's spend is the sum of its variants' own (each checked alone, with every amount
        known), so a node whose own ledger rows are null (supports not yet confirmed to
        combine) is summed all the same."""
        inputs = self.monthly.inputs
        months = len(self.monthly.months)
        direct = sum(self.spend[v.variant_id].direct for v in (*node.route, variant))
        payments = [
            sum(self.spend[v.variant_id].payments[m] for v in (*node.route, variant))
            for m in range(months)
        ]
        cap = inputs.direct_spend_cap_minor
        if cap is not None and direct > cap:
            return PruningRule.DIRECT_SPEND_CAP
        monthly_cap = inputs.monthly_payment_cap_minor
        debt = [m.debt_service_minor for m in node.check.ledgers.liquidity.months]
        if monthly_cap is not None and any(
            paid + repaid > monthly_cap for paid, repaid in zip(payments, debt, strict=True)
        ):
            return PruningRule.MONTHLY_PAYMENT_CAP
        return None

    def _cut(self, node: _Node) -> PruningRule | None:
        """Rules 3 to 6 on a checked node: a finding no later variant can repair."""
        for finding in node.check.findings:
            code = finding.code
            if code is FindingCode.DIRECT_SPEND_CAP:
                return PruningRule.DIRECT_SPEND_CAP
            if code in (FindingCode.MONTHLY_PAYMENT_CAP, FindingCode.REPAYMENTS_ABOVE_PAYMENT_CAP):
                return PruningRule.MONTHLY_PAYMENT_CAP
            if code is FindingCode.CONFLICTING_WORK_PATTERNS:
                return PruningRule.CONFLICTING_WORK_PATTERNS
            if code is FindingCode.SESSION_CLASH:
                return PruningRule.SESSION_CLASH
            if code is FindingCode.JOB_TRANSITIONS:
                return PruningRule.JOB_TRANSITIONS
            if code is FindingCode.EXCLUSIVE_SCHEMES:
                return PruningRule.EXCLUSIVE_SCHEMES
            month = self.month_index.get(finding.month or "")
            if code is FindingCode.WORKLOAD and month is not None and self._load_stays(node, month):
                return PruningRule.WORKLOAD
            needer = finding.variant_id
            if (
                code is FindingCode.PREREQUISITE_NOT_USABLE
                and needer is not None
                and self._gate_stays(node, needer, finding.reason)
            ):
                return PruningRule.PREREQUISITE
        return None

    def _later(self, node: _Node) -> list[CompiledVariant]:
        """Every variant a subtree of `node` may add (a superset of its children's choices)."""
        return [
            v
            for concept in self.concepts[node.position + 1 :]
            for v in concept
            if v.variant_id not in self.excluded
        ]

    def _load_stays(self, node: _Node, month: int) -> bool:
        """Rule 5: the job's hours in `month` are set, or no later variant can change them."""
        if any(v.work_pattern is not None and _active(v, month) for v in node.route):
            return True
        return not any(v.work_pattern is not None and _active(v, month) for v in self._later(node))

    def _gate_stays(self, node: _Node, needer_id: str, gate: str | None) -> bool:
        """Rule 6: no later variant grants the gate in time for the variant that needs it."""
        needer = next(v for v in node.route if v.variant_id == needer_id)
        if gate is None or needer.start_index is None:
            return False
        return not any(
            gate in v.grants and v.usable_index is not None and v.usable_index <= needer.start_index
            for v in self._later(node)
        )

    # The result.

    def result(
        self,
        schedules: list[Schedule],
        grouped: list[Family],
        points: list[EqualPoint],
        *,
        rank_ms: int,
        rank_seconds: int,
    ) -> SearchResult:
        """The result, from the rank stage's layered schedules, families and points."""
        monthly = self.monthly
        readiness = monthly.readiness
        if readiness is None:  # refused in `check_scope`
            raise ValueError("a route search needs the readiness basis")
        complete = self.stop is None
        size = self._size()
        return SearchResult(
            input_version=monthly.input_version,
            label=monthly.label,
            target_title=readiness.matrix.target_title,
            matrix_version=readiness.matrix.matrix_version,
            definition_version=readiness.matrix.definition_version,
            objective_basis=monthly.inputs.objective_basis,
            scenario=Scenario.BASE,
            algorithm_version=ALGORITHM_VERSION,
            pruning_version=PRUNING_VERSION,
            limits=self.limits,
            instance=size,
            canonical_order=[concept[0].concept_id for concept in self.concepts],
            coverage=SearchCoverage.COMPLETE if complete else SearchCoverage.BUDGET_TRUNCATED,
            stop_reason=self.stop,
            outcome=self._outcome(complete),
            layers_exact=complete,
            expanded_states=self.expanded,
            feasible_without_milestone=self.without_milestone,
            readiness_unknown=self.readiness_unknown,
            unresolved=self.unresolved,
            not_feasible=self.not_feasible,
            blocking_inputs=self.blocking,
            starting_violations=self.starting,
            set_aside=self.set_aside,
            pruned=dict(self.pruned),
            unexplored_branches=self.unexplored,
            elapsed_ms=self.elapsed_ms,
            rank_ms=rank_ms,
            rank_seconds=rank_seconds,
            narrowings=_narrowings(size, self.stop),
            schedules=schedules,
            families=grouped,
            points=points,
        )

    def _outcome(self, complete: bool) -> Outcome:
        if self.archive:
            return Outcome.ROUTES_FOUND
        if not complete:
            return Outcome.NONE_FOUND_BEFORE_LIMIT
        # A starting breach no option can lower rules out every route: no unknown, an input's
        # included, could change that (review 12a, Important 3).
        if any(f.code in _FIXED_BY_INPUTS for f in self.starting):
            return Outcome.NO_ROUTE_IN_BOUNDED_MODEL
        # Every route carries a blocking input's unknown, even where something else fails too.
        unknown = (
            self.blocking
            or self.unresolved
            or self.readiness_unknown
            or any(s.kind is FindingKind.UNRESOLVED for s in self.set_aside)
        )
        return Outcome.UNRESOLVED if unknown else Outcome.NO_ROUTE_IN_BOUNDED_MODEL

    def _size(self) -> InstanceSize:
        return InstanceSize(
            concepts=len(self.concepts),
            starts_per_concept=max((len(c) for c in self.concepts), default=0),
            months=self.monthly.inputs.horizon_months,
            variants=len(self.monthly.variants),
            selection_space=_selection_space(self.concepts, self.limits.max_selected_actions),
        )


def check_scope(monthly: MonthlyInput, limits: M0SearchLimits) -> None:
    """Refuse a search the declared model does not hold, never searching it in part: one
    without the target's readiness basis, or a catalogue beyond the M0 bounds."""
    if monthly.readiness is None:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "A route search needs the target's requirements and the person's evidence.",
            stage=ErrorStage.PLANNING,
            details={"reason": "readiness_basis_missing"},
        )
    starts = Counter(v.concept_id for v in monthly.variants)
    for reason, size, limit in (
        ("concepts", len(starts), limits.max_actions),
        ("starts_per_concept", max(starts.values(), default=0), limits.max_starts_per_action),
        ("months", monthly.inputs.horizon_months, limits.max_months),
    ):
        if size > limit:
            raise CareerwrightError(
                ErrorCode.MODEL_SCOPE_EXCEEDED,
                "This comparison is larger than the monthly model searches.",
                stage=ErrorStage.PLANNING,
                details={"reason": reason, "limit": limit},
            )


def _canonical(variants: Sequence[CompiledVariant]) -> list[list[CompiledVariant]]:
    """Concepts by their earliest start, then ID; a concept's variants by start, then ID. A
    variant with no dates sorts after every dated one."""

    def start(v: CompiledVariant) -> tuple[bool, int]:
        return (v.start_index is None, v.start_index or 0)

    by_concept: dict[str, list[CompiledVariant]] = defaultdict(list)
    for variant in variants:
        by_concept[variant.concept_id].append(variant)
    concepts = [sorted(vs, key=lambda v: (start(v), v.variant_id)) for vs in by_concept.values()]
    return sorted(concepts, key=lambda vs: (start(vs[0]), vs[0].concept_id))


def _selection_space(concepts: list[list[CompiledVariant]], most: int) -> int:
    """The allowed selected sets: an exclusive group counts as one choice among its concepts'
    variants, at most `most` selected and at most one bridge role."""
    choices: dict[str, list[CompiledVariant]] = defaultdict(list)
    for concept in concepts:
        group = concept[0].exclusive_group
        choices[group if group is not None else f"concept {concept[0].concept_id}"] += concept
    ways: Counter[tuple[int, bool]] = Counter({(0, False): 1})
    for options in choices.values():
        work = sum(v.kind is ActionKind.WORK for v in options)
        plain = len(options) - work
        grown: Counter[tuple[int, bool]] = Counter()
        for (selected, bridge), count in ways.items():
            grown[(selected, bridge)] += count
            if selected < most:
                grown[(selected + 1, bridge)] += count * plain
                if not bridge:
                    grown[(selected + 1, True)] += count * work
        ways = grown
    return sum(ways.values())


def _narrowings(size: InstanceSize, stop: StopReason | None) -> list[Narrowing]:
    """What could help a search `stop` ended, among the narrowings its size can still take."""
    if stop is None:
        return []
    open_to = {
        Narrowing.FEWER_CONCEPTS: size.concepts > 1,
        Narrowing.ONE_START: size.starts_per_concept > 1,
        Narrowing.SHORTER_HORIZON: size.months > 1,
    }
    return [n for n in _NARROWINGS[stop] if open_to[n]]


def _codes(check: RouteCheck, kind: FindingKind) -> list[FindingCode]:
    """A check's finding codes of one kind, each once, in the order found."""
    found: list[FindingCode] = []
    for finding in check.findings:
        if finding.kind is kind and finding.code not in found:
            found.append(finding.code)
    return found


def _active(variant: CompiledVariant, month: int) -> bool:
    if variant.start_index is None or variant.finish_index is None:
        return False
    return variant.start_index <= month <= variant.finish_index


def _spend(check: RouteCheck) -> _Spend:
    """A variant's own spend, from its check alone. A searched variant's amounts are all known
    (rule 2 sets aside an option whose amounts are not); were one not, 0 could only prune
    less."""
    direct = check.direct_cost.minor_units if check.direct_cost is not None else 0
    return _Spend(
        direct=direct,
        payments=tuple(m.payments_minor or 0 for m in check.ledgers.direct.months),
    )


def _schedule(route: tuple[CompiledVariant, ...], check: RouteCheck, key: FamilyKey) -> Schedule:
    """A feasible check that reaches the milestone, kept without its ledgers (the check is
    deterministic, so `check_route` recomputes them for a chosen route). Its layer comes later,
    over the whole archive."""
    if (
        check.months_to_readiness is None
        or check.readiness_month is None
        or check.objective_cost is None
        or check.direct_cost is None
    ):
        raise ValueError("an archived schedule reaches its milestone at a known cost")
    return Schedule(
        route=[v.variant_id for v in route],
        family_id=key.family_id,
        months_to_readiness=check.months_to_readiness,
        readiness_month=check.readiness_month,
        objective_cost=check.objective_cost,
        direct_cost=check.direct_cost,
        economic_cost=check.economic_cost,
        verdict=check.verdict,
        qualifications=check.qualifications,
        conditions=check.conditions,
        preferences=[f for f in check.findings if f.kind is FindingKind.PREFERENCE],
        loans_to_repay=check.loans_to_repay,
        layer=None,
    )
