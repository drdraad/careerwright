"""Readiness, gaps and the abstract action graph (spec section 10, RDY-1 and "Abstract
requirements before products"; S4.6; ADR 0012). Pure: no SQL, no network, no model.

For one target and one matrix version, readiness needs every required skill row at its
required evidenced level and every required credential, experience and eligibility row
satisfied, protected gates verified (RDY1-01). Unknown never passes and is never level 0.
A planned outcome counts only in a conditional scenario, after its completion gate, and
never changes the current evidence (RDY1-02). Nothing here ever finds a person ineligible:
an unresolved gate and a pathway outside the planning model are their own findings (RDY1-04).

The states keep what is known apart from what is not (Global Constraint 6):

- `insufficient_coverage`: no required row or gate is modelled (no rubric, no typed gate),
  so the target cannot be assessed and is never ready (an unknown target, or ESCO seed
  rows only, or a regulated occupation whose registration no typed gate models);
- `not_ready`: a known shortfall (below the required level, not held, beyond the model);
- `not_yet_assessed`: only unknowns stand in the way (no usable evidence, unresolved);
- `conditional_on_assessed_completion` and `ready_now_for_modelled_requirements`.

A conditional scenario whose completed offering has an assessed outcome with no stated
level for a required row is a partial sketch (`missing_outcome_level`).

Gaps are classified as learn, demonstrate, credential, experience, eligibility, information
or preference conflict, and each becomes one abstract action. No course is offered for an
evidence gap a small demonstration could close, nor for an eligibility gap education cannot
solve. When the person already meets the modelled requirements, the result leads with
reviewing current postings and applying (P05), with no forced training and no route chart
as its main result.

Every result carries the target, matrix and definition versions and the evidence version it
was computed from, and a result is used only against the same versions (MAP1-04). Each gap
depends only on its own row's subject, and names the evidence records it rests on, so an
evidence change alters only the gaps it affects (ASSESS-05). In L0 every result is
qualified: M0 matrices are provisional, and a proposed record never supports an
unqualified readiness result (OPTN-09, R9).
"""

import uuid
from collections.abc import Sequence
from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from nessa.capability.evidence import (
    Holding,
    RequirementStatement,
    RowEvidence,
    SkillEvidence,
    latest_statement,
    row_evidence,
)
from nessa.capability.matrix import (
    LEVELLED_KINDS,
    Importance,
    Matrix,
    MatrixRow,
    RowKind,
    RowScope,
    Uncertainty,
)
from nessa.capability.outcomes import (
    ASSESSED_KINDS,
    Confidence,
    EvidenceKind,
    OutcomeReview,
    OutcomeType,
    PlannedOutcome,
    Provenance,
    planned_level,
)
from nessa.capability.reference import GateKind
from nessa.errors import ErrorCode, ErrorStage, NessaError

# The M0 planning horizon (spec section 12, `M0SearchLimits.max_months`): a pathway whose
# shortest stated duration is longer is outside the model, never "impossible" (BND1-08).
MAX_PLANNING_MONTHS = 24


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RowStatus(StrEnum):
    MET = "met"
    BELOW_REQUIRED = "below_required"
    NO_USABLE_EVIDENCE = "no_usable_evidence"  # unknown: never level 0
    NOT_MODELLED = "not_modelled"  # required, but no rubric gives it a level
    SATISFIED = "satisfied"
    NOT_HELD = "not_held"
    UNRESOLVED = "unresolved"  # not stated, "don't know", or a protected gate unverified
    PATHWAY_OUTSIDE_MODEL = "pathway_outside_model"  # a blocker only
    # A blocker only, for the whole target: no required row or gate is modelled, so nothing
    # can be assessed (C1). Its `row_id` is None.
    NO_MODELLED_REQUIREMENTS = "no_modelled_requirements"


PASSING = frozenset({RowStatus.MET, RowStatus.SATISFIED})
# Findings not yet known that the person's answers can settle, as against a known shortfall.
# A row no rubric or typed gate models is a coverage gap instead (`insufficient_coverage`).
NOT_YET_KNOWN = frozenset({RowStatus.NO_USABLE_EVIDENCE, RowStatus.UNRESOLVED})
# A known shortfall: "not ready" whatever else is unknown or not modelled.
KNOWN_SHORTFALL = frozenset(
    {RowStatus.BELOW_REQUIRED, RowStatus.NOT_HELD, RowStatus.PATHWAY_OUTSIDE_MODEL}
)
# What makes a target assessable at all (review N6, provisional): a modelled skill row, or a
# modelled legal-practice or recognition gate. The right to work alone is not coverage.
_COVERING_GATES = frozenset({GateKind.LEGAL_PRACTICE, GateKind.RECOGNITION})


class GapKind(StrEnum):
    LEARN = "learn"
    DEMONSTRATE = "demonstrate"
    CREDENTIAL = "credential"
    EXPERIENCE = "experience"
    ELIGIBILITY = "eligibility"
    INFORMATION = "information"
    PREFERENCE_CONFLICT = "preference_conflict"


class ReadinessState(StrEnum):
    READY_NOW_FOR_MODELLED_REQUIREMENTS = "ready_now_for_modelled_requirements"
    CONDITIONAL_ON_ASSESSED_COMPLETION = "conditional_on_assessed_completion"
    NOT_READY = "not_ready"  # a known shortfall: below the level, not held, beyond the model
    NOT_YET_ASSESSED = "not_yet_assessed"  # only unknowns stand in the way: not a shortfall
    # Nothing required for the target is modelled (no rubric, no typed gate): it cannot be
    # assessed at all, so it is never ready (C1). Distinct from not yet assessed, which the
    # person's answers can settle.
    INSUFFICIENT_COVERAGE = "insufficient_coverage"


class PrimaryAction(StrEnum):
    REVIEW_CURRENT_POSTINGS_AND_APPLY = "review_current_postings_and_apply"
    ADDRESS_GAPS = "address_gaps"


class Qualification(StrEnum):
    """Why a result is not unqualified. M0 matrices are always provisional."""

    PROVISIONAL_MATRIX = "provisional_matrix"
    PROPOSED_RECORDS = "proposed_records"
    PROPOSED_RUBRICS = "proposed_rubrics"
    SELF_REPORTED_EVIDENCE = "self_reported_evidence"
    PLANNED_OUTCOME_ASSUMPTION = "planned_outcome_assumption"
    USER_ASSUMPTION = "user_assumption"
    # A partial sketch: a completed offering's assessed outcome for a required row states
    # no level (not ruled out: not yet assessed), so the scenario cannot count it.
    MISSING_OUTCOME_LEVEL = "missing_outcome_level"
    # L0 has no reviewer: a demonstration, and a protected gate's verification, rest on the
    # person's own statement.
    PERSON_CONFIRMED_DEMONSTRATION = "person_confirmed_demonstration"
    PERSON_CONFIRMED_VERIFICATION = "person_confirmed_verification"
    # A met required row whose evidence is in conflict (a demonstration and a self-report
    # disagree, or a later answer under another rubric says "not yet done"): the result rests
    # on evidence awaiting the person's clarification (spec section 9; re-review 2, R2-2).
    OPEN_CONFLICT = "open_conflict"


ActionKind = Literal[
    "review_postings_and_apply",
    "learn",
    "demonstrate",
    "obtain_credential",
    "gain_experience",
    "resolve_eligibility",
    "verify",
    "check_employer_acceptance",
]
_ACTION_KIND: dict[GapKind, ActionKind] = {
    GapKind.LEARN: "learn",
    GapKind.DEMONSTRATE: "demonstrate",
    GapKind.CREDENTIAL: "obtain_credential",
    GapKind.EXPERIENCE: "gain_experience",
    GapKind.ELIGIBILITY: "resolve_eligibility",
    GapKind.INFORMATION: "verify",
    GapKind.PREFERENCE_CONFLICT: "check_employer_acceptance",
}
_NOT_HELD_GAP = {
    RowKind.CREDENTIAL: GapKind.CREDENTIAL,
    RowKind.EXPERIENCE: GapKind.EXPERIENCE,
    RowKind.ELIGIBILITY: GapKind.ELIGIBILITY,
}
# Gaps a course or work-based option can address: never a demonstration gap (a small
# assessment closes it) and never an eligibility gap (education cannot solve it).
_OPTION_GAPS = frozenset({GapKind.LEARN, GapKind.CREDENTIAL, GapKind.EXPERIENCE})


class StatementView(StrictModel):
    statement_id: uuid.UUID
    holding: Holding
    verified: bool


class RowAssessment(StrictModel):
    row_id: str
    subject: str
    label: str
    kind: RowKind
    importance: Importance
    mandatory: bool
    protected: bool
    required_level: int | None
    status: RowStatus
    evidence: RowEvidence | None  # skill and task rows
    statement: StatementView | None  # credential, experience and eligibility rows
    planned_level: int | None = None  # conditional scenarios only
    eligible_to_apply_after_completion: bool = False  # a completed credential outcome
    review_state: Literal["proposed", "reviewed"]  # its matrix row's (R9)
    modelled: bool = True  # False: a regulated occupation's gate no typed gate models


class Blocker(StrictModel):
    row_id: str | None  # None: the whole target (`no_modelled_requirements`)
    kind: RowStatus


class Gap(StrictModel):
    gap_id: str
    row_id: str
    subject: str
    label: str
    kind: GapKind
    mandatory: bool  # a required row or gate, rather than a desirable improvement
    required_level: int | None
    evidenced_level: int | None
    evidence_ids: list[uuid.UUID]  # what it was computed from
    statement_id: uuid.UUID | None
    review_state: Literal["proposed", "reviewed"]  # its matrix row's (R9)


class CandidateOption(StrictModel):
    """An option whose planned outcome maps to the gap's row: "expected to address", never a
    recommendation, and never a reason the gap is closed."""

    outcome_id: str
    option_id: str
    offering_id: str
    option_title: str | None
    outcome_type: OutcomeType
    evidence_kind: EvidenceKind
    confidence: Confidence
    level_on_completion: int | None
    review_state: OutcomeReview
    provenance: Provenance
    addresses: bool  # its source supports the mapping at all
    # How a numeric readiness solve may use it: a missing level leaves a partial sketch.
    numeric_use: Literal["usable", "excluded_missing_level", "excluded_not_accepted", "not_a_level"]
    months_minimum: int | None
    outside_planning_model: bool
    as_of: date  # the retrieval date of its evidence: never "current" (R9)


class AbstractAction(StrictModel):
    action_id: str
    kind: ActionKind
    label: str  # the row's own label; the words around it are the interface's
    rows: list[str]
    mandatory: bool
    prerequisites: list[str] = Field(default_factory=list)  # action IDs
    candidates: list[CandidateOption] = Field(default_factory=list)
    state: Literal["open", "outside_planning_model"] = "open"
    code: ErrorCode | None = None


class EmployerCheck(StrictModel):
    """A posting's own essential requirement: check it against that posting before applying."""

    row_id: str
    requirement_id: str
    posting_id: str
    posting_title: str | None
    text: str | None
    kind: str


class Assessment(StrictModel):
    target_key: str
    target_title: str
    matrix_version: str
    definition_version: str
    evidence_version: int
    pack_version: str
    reference_version: str
    synthetic: bool
    scenario: Literal["current", "conditional"]
    completed: list[str]  # the offerings a conditional scenario assumes assessed and passed
    state: ReadinessState
    primary_action: PrimaryAction
    training_required: bool
    show_route_chart: bool  # never a degenerate frontier as the main result
    qualifications: list[Qualification]
    rows: list[RowAssessment]
    blockers: list[Blocker]
    gaps: list[Gap]
    actions: list[AbstractAction]
    employer_checks: list[EmployerCheck]
    optional_development: list[str]  # gap IDs of desirable improvements: a separate goal
    not_modelled_rows: int


def assess(
    matrix: Matrix,
    *,
    evidence: Sequence[SkillEvidence],
    statements: Sequence[RequirementStatement],
    outcomes: Sequence[PlannedOutcome],
    evidence_version: int,
    completed: frozenset[str] | None = None,
) -> Assessment:
    """The current readiness (no `completed`), or a conditional scenario in which these
    offerings were completed and assessed."""
    done = completed if completed is not None else frozenset()
    scoring = _Scoring(list(evidence), list(statements), list(outcomes), done)
    rows: list[RowAssessment] = []
    gaps: list[Gap] = []
    for row in matrix.rows:
        relaxed = Uncertainty.RELAXED_BY_PERSON in row.uncertainty
        desirable = row.importance is Importance.PREFERRED and row.rubric is not None
        if not (row.required or desirable or relaxed):
            continue
        assessed, gap = scoring.row(row)
        rows.append(assessed)
        if gap is not None and relaxed and not row.required:
            gap = gap.model_copy(update={"kind": GapKind.PREFERENCE_CONFLICT})
        if gap is not None:
            gaps.append(gap)
    by_row = {r.row_id: r for r in matrix.rows}
    actions = [_action(gap, by_row[gap.row_id], outcomes, gaps) for gap in gaps]
    blockers = [
        Blocker(row_id=r.row_id, kind=r.status)
        for r in rows
        if r.mandatory and r.status not in PASSING
    ]
    blockers += [
        Blocker(row_id=a.rows[0], kind=RowStatus.PATHWAY_OUTSIDE_MODEL)
        for a in actions
        if a.mandatory and a.state == "outside_planning_model"
    ]
    planned = completed is not None and any(
        r.mandatory
        and r.planned_level is not None
        and r.status is RowStatus.MET
        and (
            r.evidence is None
            or r.evidence.level is None
            or (r.required_level or 0) > r.evidence.level
        )
        for r in rows
    )
    uncovered = not any(_covers(r, by_row[r.row_id]) for r in rows if r.mandatory)
    if uncovered:
        blockers = [Blocker(row_id=None, kind=RowStatus.NO_MODELLED_REQUIREMENTS), *blockers]
    # A required row no rubric models, or a regulation no typed gate models: no answer can
    # settle it, so the target is not assessable (review N5). It stays a blocker of its own.
    coverage_gap = uncovered or any(
        r.mandatory and (r.status is RowStatus.NOT_MODELLED or not r.modelled) for r in rows
    )
    if any(b.kind in KNOWN_SHORTFALL for b in blockers):
        # A known shortfall is "not ready" whatever else is unknown or unmodelled: a coverage
        # gap never hides it (re-review 2, R2-1).
        state = ReadinessState.NOT_READY
    elif coverage_gap:
        state = ReadinessState.INSUFFICIENT_COVERAGE
    elif blockers:
        state = ReadinessState.NOT_YET_ASSESSED
    elif planned:
        state = ReadinessState.CONDITIONAL_ON_ASSESSED_COMPLETION
    else:
        state = ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS
    ready_now = state is ReadinessState.READY_NOW_FOR_MODELLED_REQUIREMENTS
    training = any(g.mandatory and g.kind in _OPTION_GAPS for g in gaps)
    if ready_now:
        apply = AbstractAction(
            action_id="action:apply",
            kind="review_postings_and_apply",
            label=matrix.target_title,
            rows=[],
            mandatory=False,
        )
        actions = [apply, *actions]
    return Assessment(
        target_key=matrix.target_key,
        target_title=matrix.target_title,
        matrix_version=matrix.matrix_version,
        definition_version=matrix.definition_version,
        evidence_version=evidence_version,
        pack_version=matrix.sources.pack_version,
        reference_version=matrix.sources.reference_version,
        synthetic=matrix.synthetic,
        scenario="current" if completed is None else "conditional",
        completed=sorted(done),
        state=state,
        primary_action=(
            PrimaryAction.REVIEW_CURRENT_POSTINGS_AND_APPLY
            if ready_now
            else PrimaryAction.ADDRESS_GAPS
        ),
        training_required=training,
        # From the plannable gaps, never the state: a mandatory gap an option could address
        # (learn, credential, experience). So never when ready now (no degenerate frontier),
        # nor when only unknowns or coverage gaps remain (re-review 2, R2-1).
        show_route_chart=training,
        qualifications=_qualifications(
            matrix, rows, planned, scoring.used, _missing_level(rows, outcomes, completed)
        ),
        rows=rows,
        blockers=blockers,
        gaps=gaps,
        actions=actions,
        employer_checks=_employer_checks(matrix),
        optional_development=[g.gap_id for g in gaps if not g.mandatory],
        not_modelled_rows=matrix.coverage.not_modelled_rows,
    )


class _Scoring:
    def __init__(
        self,
        evidence: list[SkillEvidence],
        statements: list[RequirementStatement],
        outcomes: list[PlannedOutcome],
        completed: frozenset[str],
    ) -> None:
        self.evidence = evidence
        self.statements = statements
        self.outcomes = outcomes
        self.completed = completed
        self.used: list[PlannedOutcome] = []

    def row(self, row: MatrixRow) -> tuple[RowAssessment, Gap | None]:
        if row.kind in LEVELLED_KINDS and row.gate is None:
            return self._levelled(row)
        return self._stated(row)

    def _levelled(self, row: MatrixRow) -> tuple[RowAssessment, Gap | None]:
        rubric = row.rubric.version_id if row.rubric is not None else None
        seen = row_evidence(row.subject, rubric, self.evidence)
        planned, used = planned_level(row.row_id, rubric, self.outcomes, self.completed)
        required = row.required_level
        effective = max((v for v in (seen.level, planned) if v is not None), default=None)
        claimed = seen.level if seen.level is not None else seen.self_assessed_level
        gap_kind: GapKind | None
        if required is None:
            status, gap_kind = RowStatus.NOT_MODELLED, GapKind.INFORMATION
        elif effective is not None and effective >= required:
            status, gap_kind = RowStatus.MET, None
            if seen.level is None or seen.level < required:
                self.used += used
        elif effective is not None or (claimed is not None and claimed < required):
            status, gap_kind = RowStatus.BELOW_REQUIRED, GapKind.LEARN
        elif claimed is not None:
            status, gap_kind = RowStatus.NO_USABLE_EVIDENCE, GapKind.DEMONSTRATE
        else:
            status, gap_kind = RowStatus.NO_USABLE_EVIDENCE, GapKind.INFORMATION
        assessed = RowAssessment(
            row_id=row.row_id,
            subject=row.subject,
            label=row.label,
            kind=row.kind,
            importance=row.importance,
            mandatory=row.required,
            protected=False,
            required_level=required,
            status=status,
            evidence=seen,
            statement=None,
            planned_level=planned,
            review_state=row.review_state,
        )
        return assessed, _gap(row, gap_kind, seen.level, seen.evidence_ids, None)

    def _stated(self, row: MatrixRow) -> tuple[RowAssessment, Gap | None]:
        statement = latest_statement(row.subject, self.statements)
        protected = row.gate is not None
        modelled = row.gate is None or row.gate.modelled
        gap_kind: GapKind | None
        if not modelled:
            # Nobody has modelled what this regulation requires: no statement settles it.
            status, gap_kind = RowStatus.UNRESOLVED, GapKind.INFORMATION
        elif statement is None or statement.holding is Holding.UNKNOWN:
            status, gap_kind = RowStatus.UNRESOLVED, GapKind.INFORMATION
        elif statement.holding is Holding.NOT_HELD:
            status, gap_kind = RowStatus.NOT_HELD, _NOT_HELD_GAP.get(row.kind, GapKind.INFORMATION)
        elif protected and not statement.verified:
            status, gap_kind = RowStatus.UNRESOLVED, GapKind.INFORMATION
        else:
            status, gap_kind = RowStatus.SATISFIED, None
        eligible = any(
            o.skill_id == row.row_id
            and o.outcome_type is OutcomeType.CREDENTIAL
            and o.counted
            and o.offering_id in self.completed
            and o.confidence is not Confidence.UNSUPPORTED
            for o in self.outcomes
        )
        assessed = RowAssessment(
            row_id=row.row_id,
            subject=row.subject,
            label=row.label,
            kind=row.kind,
            importance=row.importance,
            mandatory=row.required,
            protected=protected,
            required_level=None,
            status=status,
            evidence=None,
            statement=(
                StatementView(
                    statement_id=statement.statement_id,
                    holding=statement.holding,
                    verified=statement.verified,
                )
                if statement is not None
                else None
            ),
            eligible_to_apply_after_completion=eligible,
            review_state=row.review_state,
            modelled=modelled,
        )
        statement_id = statement.statement_id if statement is not None else None
        return assessed, _gap(row, gap_kind, None, [], statement_id)


def _gap(
    row: MatrixRow,
    kind: GapKind | None,
    evidenced: int | None,
    evidence_ids: list[uuid.UUID],
    statement_id: uuid.UUID | None,
) -> Gap | None:
    if kind is None:
        return None
    return Gap(
        gap_id=f"gap:{row.row_id}",
        row_id=row.row_id,
        subject=row.subject,
        label=row.label,
        kind=kind,
        mandatory=row.required,
        required_level=row.required_level,
        evidenced_level=evidenced,
        evidence_ids=evidence_ids,
        statement_id=statement_id,
        review_state=row.review_state,
    )


def _candidate(outcome: PlannedOutcome, row: MatrixRow) -> CandidateOption:
    rubric = row.rubric.version_id if row.rubric is not None else None
    if outcome.outcome_type is not OutcomeType.SKILL_LEVEL:
        use: Literal["usable", "excluded_missing_level", "excluded_not_accepted", "not_a_level"]
        use = "not_a_level"
    elif outcome.level_on_completion is None or outcome.rubric_version != rubric:
        use = "excluded_missing_level"
    elif not outcome.counted:
        use = "excluded_not_accepted"
    else:
        use = "usable"
    months = outcome.months_minimum
    return CandidateOption(
        outcome_id=outcome.outcome_id,
        option_id=outcome.option_id,
        offering_id=outcome.offering_id,
        option_title=outcome.option_title,
        outcome_type=outcome.outcome_type,
        evidence_kind=outcome.evidence_kind,
        confidence=outcome.confidence,
        level_on_completion=outcome.level_on_completion,
        review_state=outcome.review_state,
        provenance=outcome.provenance,
        addresses=outcome.confidence is not Confidence.UNSUPPORTED
        and outcome.review_state is not OutcomeReview.REJECTED,
        numeric_use=use,
        months_minimum=months,
        outside_planning_model=months is not None and months > MAX_PLANNING_MONTHS,
        as_of=outcome.as_of,
    )


def _action(
    gap: Gap, row: MatrixRow, outcomes: Sequence[PlannedOutcome], gaps: list[Gap]
) -> AbstractAction:
    # An unresolved credential gate also shows its pathways, for the case where it is not held.
    shows_options = gap.kind in _OPTION_GAPS or (
        gap.kind is GapKind.INFORMATION and row.gate is not None and row.kind is RowKind.CREDENTIAL
    )
    candidates = (
        [_candidate(o, row) for o in outcomes if o.skill_id == row.row_id] if shows_options else []
    )
    addressing = [c for c in candidates if c.addresses]
    outside = (
        gap.kind in _OPTION_GAPS
        and bool(addressing)
        and all(c.outside_planning_model for c in addressing)
    )
    with_gaps = {g.row_id for g in gaps}
    return AbstractAction(
        action_id=f"action:{row.row_id}",
        kind=_ACTION_KIND[gap.kind],
        label=row.label,
        rows=[row.row_id],
        mandatory=gap.mandatory,
        prerequisites=[f"action:{p}" for p in row.prerequisites if p in with_gaps],
        candidates=candidates,
        state="outside_planning_model" if outside else "open",
        code=ErrorCode.MODEL_SCOPE_EXCEEDED if outside else None,
    )


def _covers(assessed: RowAssessment, row: MatrixRow) -> bool:
    """Whether a required row makes the target assessable: a skill row a rubric models, or a
    modelled practice or recognition gate (review N6, provisional)."""
    if row.gate is not None:
        return row.gate.modelled and row.gate.kind in _COVERING_GATES
    return row.kind in LEVELLED_KINDS and assessed.status is not RowStatus.NOT_MODELLED


def _missing_level(
    rows: list[RowAssessment],
    outcomes: Sequence[PlannedOutcome],
    completed: frozenset[str] | None,
) -> bool:
    """Whether a completed offering's assessed, supported outcome for a required skill row
    states no level: its level is not yet assessed rather than ruled out (OUT-1's partial
    sketch). A topic mention or unassessed practice rules a level out, so it is not missing."""
    if completed is None:
        return False
    required = {r.row_id for r in rows if r.mandatory and r.evidence is not None}
    return any(
        o.offering_id in completed
        and o.skill_id in required
        and o.outcome_type is OutcomeType.SKILL_LEVEL
        and o.evidence_kind in ASSESSED_KINDS
        and o.confidence is not Confidence.UNSUPPORTED
        and o.level_on_completion is None
        and o.review_state is not OutcomeReview.REJECTED
        for o in outcomes
    )


def _qualifications(
    matrix: Matrix,
    rows: list[RowAssessment],
    planned: bool,
    used: list[PlannedOutcome],
    missing_level: bool,
) -> list[Qualification]:
    by_row = {r.row_id: r for r in matrix.rows}
    mandatory = [by_row[r.row_id] for r in rows if r.mandatory]
    found = {Qualification.PROVISIONAL_MATRIX}
    if any(r.review_state == "proposed" for r in mandatory):
        found.add(Qualification.PROPOSED_RECORDS)
    if any(r.rubric is not None and r.rubric.review_state == "proposed" for r in mandatory):
        found.add(Qualification.PROPOSED_RUBRICS)
    met = [r for r in rows if r.status is RowStatus.MET and r.evidence is not None]
    if any(r.evidence is not None and r.evidence.basis == "self_reported" for r in met):
        found.add(Qualification.SELF_REPORTED_EVIDENCE)
    if any(r.evidence is not None and r.evidence.basis == "demonstrated" for r in met):
        found.add(Qualification.PERSON_CONFIRMED_DEMONSTRATION)
    if any(r.protected and r.status is RowStatus.SATISFIED for r in rows):
        found.add(Qualification.PERSON_CONFIRMED_VERIFICATION)
    if any(r.mandatory and r.evidence is not None and r.evidence.conflict for r in met):
        found.add(Qualification.OPEN_CONFLICT)
    if planned:
        found.add(Qualification.PLANNED_OUTCOME_ASSUMPTION)
    if any(o.provenance is Provenance.USER_OVERRIDE for o in used):
        found.add(Qualification.USER_ASSUMPTION)
    if missing_level:
        found.add(Qualification.MISSING_OUTCOME_LEVEL)
    return [q for q in Qualification if q in found]


def _employer_checks(matrix: Matrix) -> list[EmployerCheck]:
    return [
        EmployerCheck(
            row_id=row.row_id,
            requirement_id=c.requirement_id,
            posting_id=c.posting_id,
            posting_title=c.posting_title,
            text=c.text,
            kind=c.stated_kind,
        )
        for row in matrix.rows
        if row.scope is RowScope.POSTING
        for c in row.citations
        if c.stated_importance is Importance.ESSENTIAL
    ]


def ensure_current(assessment: Assessment, matrix: Matrix) -> None:
    """A result is used only for the target definition it was computed for."""
    if (assessment.target_key, assessment.matrix_version, assessment.definition_version) != (
        matrix.target_key,
        matrix.matrix_version,
        matrix.definition_version,
    ):
        raise NessaError(
            ErrorCode.STALE_INPUT_VERSION,
            "This result was computed for an earlier version of the target's requirements.",
            stage=ErrorStage.CAPABILITY,
            details={
                "matrix_version": matrix.matrix_version,
                "definition_version": matrix.definition_version,
            },
        )
