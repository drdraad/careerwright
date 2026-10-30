"""Capability use cases (S4.1-S4.6; ADR 0012): read the matrices, the question graph and
readiness for the person's targets; record evidence, requirement statements and matrix
edits; stop or resume the questions.

Reads are computed from the current profile's targets, the committed option pack and
capability reference, the held ESCO release and the workspace's own records, so nothing
derived is stored and nothing goes stale silently: every result carries the versions it was
computed from. A target's pack target is the one with the same title; its ESCO seed is the
occupation ESCO labels with exactly that title, or else the pack target's crosswalk.

Every write is one command (direct edits now, confirmed chat proposals later, through the
same command): it locks the workspace, checks the expected capability version, records one
append-only row, moves the version on by one and appends a status event. A refused write
records nothing.
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from careerwright.capability import store, usual
from careerwright.capability.evidence import (
    Answer,
    EvidenceContext,
    Holding,
    Level,
    Method,
    Month,
    RequirementStatement,
    SkillEvidence,
)
from careerwright.capability.matrix import (
    LEVELLED_KINDS,
    EscoSeed,
    EscoSkillRelation,
    Importance,
    Matrix,
    OccupationBasis,
    OccupationNote,
    RowEdit,
    apply_edits,
    build_matrix,
    check_edit,
    find_pack_target,
    pick_occupation,
)
from careerwright.capability.outcomes import PlannedOutcome, pack_outcomes
from careerwright.capability.questions import QuestionGraph, question_graph
from careerwright.capability.readiness import Assessment, assess
from careerwright.capability.reference import Reference, load_reference
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.esco import concept_id, normalise_label
from careerwright.catalogue.option_pack import Pack, Target, load_pack
from careerwright.catalogue.records import TaxonomyRelease
from careerwright.catalogue.taxonomy import held_release
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import store as evidence_store
from careerwright.evidence.jobs import title_key
from careerwright.identity import store as identity_store
from careerwright.identity.access import Actor
from careerwright.identity.records import EventKind
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile import store as profile_store
from careerwright.profile.commands import current_profile
from careerwright.profile.document import FieldState, TextValue
from careerwright.vocabulary import DataMode

# The versions the capability model reads: Task 7c's reviewed pack is a new version here.
PACK_VERSION = "0.1.0"
REFERENCE_VERSION = "0.1.0"


@dataclass(frozen=True)
class CapabilityData:
    """The committed, pinned inputs, loaded and checked once when the API starts."""

    pack: Pack
    reference: Reference
    outcomes: tuple[PlannedOutcome, ...]


def committed_data() -> CapabilityData:
    pack = load_pack(PACK_VERSION)
    reference = load_reference(REFERENCE_VERSION, pack)
    return CapabilityData(pack, reference, tuple(pack_outcomes(pack, reference)))


@dataclass(frozen=True)
class CapabilityView:
    version: int
    questions_stopped: bool
    profile_version: int
    synthetic: bool  # the workspace's label, carried by every result
    data_mode: DataMode
    matrices: list[Matrix]
    evidence: list[SkillEvidence]
    statements: list[RequirementStatement]


def capability_view(tx: Tx, workspace_id: uuid.UUID, data: CapabilityData) -> CapabilityView:
    workspace = visible_workspace(tx, workspace_id)
    profile = current_profile(tx, workspace_id)
    titles = profile.document.target_titles
    targets = list(titles.value or []) if titles.state is FieldState.PROVIDED else []
    matrices: list[Matrix] = []
    if targets:
        release = held_release(tx)  # TAXONOMY_UNAVAILABLE without one: never an empty matrix
        chosen = _chosen(tx, workspace_id)
        matrices = [
            _matrix(
                tx,
                workspace_id,
                title,
                data,
                release,
                chosen=chosen.get(title_key(title)),
                synthetic=workspace.synthetic,
            )
            for title in targets
        ]
    state = store.state(tx, workspace_id)
    return CapabilityView(
        version=state.version,
        questions_stopped=state.questions_stopped,
        profile_version=profile.version,
        synthetic=workspace.synthetic,
        data_mode=workspace.data_mode,
        matrices=matrices,
        evidence=store.evidence(tx, workspace_id),
        statements=store.statements(tx, workspace_id),
    )


def _matrix(
    tx: Tx,
    workspace_id: uuid.UUID,
    title: str,
    data: CapabilityData,
    release: TaxonomyRelease,
    *,
    chosen: uuid.UUID | None,
    synthetic: bool,
) -> Matrix:
    """A target found by its title, or else through its ESCO occupation, which is how a
    target chosen in the product is stored (ESCO's preferred label)."""
    key = title_key(title)
    by_title, _, _ = find_pack_target(title, data.pack, data.reference, None)
    seed, note = _seed(tx, title, by_title, data.reference, release, chosen)
    pack_target, basis, pack_note = find_pack_target(title, data.pack, data.reference, seed)
    return build_matrix(
        title,
        pack=data.pack,
        reference=data.reference,
        pack_target=pack_target,
        pack_target_basis=basis or "title",
        pack_target_note=pack_note,
        occupation=seed,
        exemplars=evidence_store.exemplar_count(tx, workspace_id, key),
        synthetic=synthetic,
        edits=store.edits(tx, workspace_id, key),
        occupation_note=note,
    )


def _chosen(tx: Tx, workspace_id: uuid.UUID) -> dict[str, uuid.UUID]:
    """The occupations the person chose as targets, read from each choice's own source (its
    ESCO URI), by their preferred label's title key; a later choice of a title wins. A choice
    from another release is absent (as in `careerwright.profile.sketch`)."""
    uris = profile_store.chosen_occupation_uris(tx, workspace_id)
    concepts = taxonomy_store.concepts_by_uri(tx, uris)
    chosen: dict[str, uuid.UUID] = {}
    for uri in uris:
        detail = taxonomy_store.occupation(tx, concepts[uri]) if uri in concepts else None
        if detail is not None:
            chosen[title_key(detail.preferred_label)] = detail.concept_id
    return chosen


def _seed(
    tx: Tx,
    title: str,
    pack_target: Target | None,
    reference: Reference,
    release: TaxonomyRelease,
    chosen: uuid.UUID | None,
) -> tuple[EscoSeed | None, OccupationNote | None]:
    """The occupation the person chose; else the one ESCO labels with the title (preferring
    its preferred label where several do); else the pack target's crosswalk."""
    concept, picked, note = pick_occupation(
        title, chosen=chosen, matches=taxonomy_store.label_matches(tx, normalise_label(title))
    )
    crosswalk = reference.crosswalk_for(pack_target.target_id) if pack_target else None
    basis: OccupationBasis
    if concept is not None and picked is not None:
        basis = picked
    elif crosswalk is not None:
        concept, basis = concept_id(crosswalk.esco_occupation), "pack_crosswalk"
    else:
        return None, note
    detail = taxonomy_store.occupation(tx, concept)
    if detail is None:
        return None, OccupationNote.NOT_IN_HELD_TAXONOMY
    seed = EscoSeed(
        release=release.dataset_id,
        concept_id=detail.concept_id,
        label=detail.preferred_label,
        regulated=detail.regulated,
        basis=basis,
        skills=[
            EscoSkillRelation(
                skill_id=s.skill_id,
                label=s.preferred_label,
                skill_type=s.skill_type,
                relation="essential" if s.relation == "essential" else "optional",
            )
            for s in detail.skills
        ],
    )
    return seed, None


def readiness(view: CapabilityView, data: CapabilityData) -> list[Assessment]:
    return [
        assess(
            matrix,
            evidence=view.evidence,
            statements=view.statements,
            outcomes=data.outcomes,
            evidence_version=view.version,
        )
        for matrix in view.matrices
    ]


def questions(view: CapabilityView) -> QuestionGraph:
    return question_graph(
        view.matrices,
        evidence=view.evidence,
        statements=view.statements,
        evidence_version=view.version,
        stopped=view.questions_stopped,
    )


class _Command(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0, description="0 while nothing has been recorded.")


class RecordEvidence(_Command):
    """An answer about a skill: the level is chosen against `rubric_version`'s anchors. The
    subject is a skill of a target's matrix, or one of the essential skills the person's
    role usually needs (`esco:<skill ID>`): "I've used this" is `answer: used`, no level."""

    subject: str = Field(min_length=1, max_length=200)
    rubric_version: str | None = Field(default=None, max_length=200)
    answer: Answer
    self_assessed_level: Level | None = None
    example: str | None = Field(default=None, max_length=1_000)
    last_done: Month | None = None
    context: EvidenceContext | None = None
    independence: Literal["independent", "with_help"] | None = None
    complexity: Literal["routine", "complex"] | None = None
    tools: str | None = Field(default=None, max_length=300)
    ai_assisted: bool | None = None
    method: Method = Method.SELF_REPORT
    demonstrated_level: Level | None = None
    assessed_by: str | None = Field(default=None, max_length=300)
    reviewed_on: date | None = None
    outcome_id: str | None = Field(default=None, max_length=200)


class RecordStatement(_Command):
    """Whether the person holds a credential, experience or eligibility requirement."""

    subject: str = Field(min_length=1, max_length=200)
    holding: Holding
    verified: bool = Field(description="Checked at its source: a register, a right to work check.")
    verification_note: str | None = Field(default=None, max_length=300)


class EditRow(_Command):
    """Set a row's importance, or challenge its source, at the checkpoint."""

    target: TextValue = Field(description="One of the profile's target titles.")
    matrix_version: str = Field(min_length=1, max_length=40, description="The matrix shown.")
    row_id: str = Field(min_length=1, max_length=300)
    action: Literal["set_importance", "challenge"]
    importance: Importance | None = None
    reason: str = Field(min_length=1, max_length=400)
    warning_acknowledged: bool = Field(
        default=False,
        description="The person read that relaxing an employer's requirement may leave the "
        "plan unable to satisfy those postings.",
    )


class SetQuestions(_Command):
    stopped: bool = Field(description="Stop or pause the questions; false resumes them.")


@dataclass(frozen=True)
class CapabilityChange:
    version: int
    questions_stopped: bool
    recorded_id: uuid.UUID | None
    matrix_version: str | None = None
    definition_version: str | None = None


def _invalid(reason: str, message: str, field: str) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        message,
        stage=ErrorStage.CAPABILITY,
        details={"field": field, "reason": reason},
    )


def _advance(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, expected: int, *, stopped: bool | None = None
) -> tuple[int, bool]:
    """The next capability version; the caller holds the workspace lock."""
    current = store.state(tx, workspace_id)
    keep = current.questions_stopped if stopped is None else stopped
    if expected != current.version or not store.advance_state(
        tx, workspace_id, expected, stopped=keep, by=actor.actor_id
    ):
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "Your skills and evidence changed since you loaded them. Reload, then try again.",
            stage=ErrorStage.CAPABILITY,
            details={"current_version": current.version},
        )
    return expected + 1, keep


def _event(tx: Tx, workspace_id: uuid.UUID, version: int) -> None:
    identity_store.append_event(
        tx,
        workspace_id,
        EventKind.CAPABILITY_UPDATED,
        str(workspace_id),
        detail={"version": version},
    )


def record_evidence(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: RecordEvidence,
    *,
    data: CapabilityData,
    now: datetime,
) -> CapabilityChange:
    visible_workspace(tx, workspace_id, lock=True)
    view = capability_view(tx, workspace_id, data)
    rows = [
        r
        for m in view.matrices
        for r in m.rows
        if r.subject == command.subject and r.kind in LEVELLED_KINDS and r.gate is None
    ]
    role = usual.role_occupation(tx, workspace_id)
    usual_subjects = (
        {usual.subject_of(s.skill_id) for s in usual.essential_skills(role)} if role else set()
    )
    if not rows and command.subject not in usual_subjects:
        raise _invalid(
            "not_a_skill",
            "That skill is not in your targets' matrices or your role's usual skills.",
            "subject",
        )
    rubrics = {r.rubric.version_id for r in rows if r.rubric is not None}
    levelled = command.self_assessed_level is not None or command.demonstrated_level is not None
    if command.rubric_version is not None and command.rubric_version not in rubrics:
        raise _invalid(
            "not_its_rubric", "Choose a level against that skill's own rubric.", "rubric_version"
        )
    if levelled and command.rubric_version is None:
        raise _invalid(
            "level_without_rubric", "A level is chosen against a rubric.", "rubric_version"
        )
    if command.outcome_id is not None and not any(
        o.outcome_id == command.outcome_id and o.skill_id in {r.row_id for r in rows}
        for o in data.outcomes
    ):
        raise _invalid(
            "not_its_outcome", "That planned outcome is not for this skill.", "outcome_id"
        )
    try:
        evidence = SkillEvidence(
            evidence_id=uuid.uuid4(),
            recorded_by=actor.actor_id,
            recorded_at=now,
            **command.model_dump(exclude={"expected_version"}),
        )
    except ValidationError:
        raise _invalid(
            "inconsistent_evidence", "Those answers don't fit together; check them.", "answer"
        ) from None
    return record_checked_evidence(tx, actor, workspace_id, command.expected_version, evidence)


def record_checked_evidence(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, expected_version: int, evidence: SkillEvidence
) -> CapabilityChange:
    """Record evidence its command already checked, as the next capability version; the
    caller holds the workspace lock."""
    version, stopped = _advance(tx, actor, workspace_id, expected_version)
    store.insert_evidence(tx, workspace_id, version, evidence)
    _event(tx, workspace_id, version)
    return CapabilityChange(version, stopped, evidence.evidence_id)


def record_statement(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: RecordStatement,
    *,
    data: CapabilityData,
    now: datetime,
) -> CapabilityChange:
    visible_workspace(tx, workspace_id, lock=True)
    view = capability_view(tx, workspace_id, data)
    rows = [
        r
        for m in view.matrices
        for r in m.rows
        if r.subject == command.subject and (r.gate is not None or r.kind not in LEVELLED_KINDS)
    ]
    if not rows:
        raise _invalid(
            "not_a_requirement", "That requirement is not in your targets' matrices.", "subject"
        )
    if all(r.gate is not None and not r.gate.modelled for r in rows):
        # Nobody has modelled what this regulation requires, so no statement can settle it.
        raise _invalid("not_modelled", "That requirement is not modelled yet.", "subject")
    try:
        statement = RequirementStatement(
            statement_id=uuid.uuid4(),
            recorded_by=actor.actor_id,
            recorded_at=now,
            **command.model_dump(exclude={"expected_version"}),
        )
    except ValidationError:
        raise _invalid(
            "verified_only_if_held", "Only a requirement you hold can be verified.", "verified"
        ) from None
    version, stopped = _advance(tx, actor, workspace_id, command.expected_version)
    store.insert_statement(tx, workspace_id, version, statement)
    _event(tx, workspace_id, version)
    return CapabilityChange(version, stopped, statement.statement_id)


def edit_row(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: EditRow,
    *,
    data: CapabilityData,
    now: datetime,
) -> CapabilityChange:
    """Returns the change; `recorded_id` is None when the edit changes nothing."""
    visible_workspace(tx, workspace_id, lock=True)
    view = capability_view(tx, workspace_id, data)
    key = title_key(command.target)
    matrix = next((m for m in view.matrices if m.target_key == key), None)
    if matrix is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND,
            "That is not one of your target roles.",
            stage=ErrorStage.CAPABILITY,
        )
    if command.expected_version != view.version or command.matrix_version != matrix.matrix_version:
        raise CareerwrightError(
            ErrorCode.STALE_INPUT_VERSION,
            "These requirements changed since you loaded them. Reload, then try again.",
            stage=ErrorStage.CAPABILITY,
            details={"current_version": view.version, "matrix_version": matrix.matrix_version},
        )
    if command.action == "set_importance":
        if command.importance is None:
            raise _invalid("importance_required", "Choose the importance to set.", "importance")
        changes = check_edit(
            matrix,
            command.row_id,
            command.importance,
            warning_acknowledged=command.warning_acknowledged,
        )
        if not changes:
            return CapabilityChange(
                view.version,
                view.questions_stopped,
                None,
                matrix.matrix_version,
                matrix.definition_version,
            )
    elif command.importance is not None:
        raise _invalid(
            "challenge_has_no_importance", "A challenge sets no importance.", "importance"
        )
    elif matrix.row(command.row_id) is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND,
            "That requirement is not in this matrix.",
            stage=ErrorStage.CAPABILITY,
        )
    edit = RowEdit(
        edit_id=uuid.uuid4(),
        row_id=command.row_id,
        action=command.action,
        importance=command.importance,
        reason=command.reason,
        warning_acknowledged=command.warning_acknowledged,
        recorded_by=actor.actor_id,
        recorded_at=now,
        from_matrix_version=matrix.matrix_version,
        from_definition_version=matrix.definition_version,
    )
    after = apply_edits(matrix, [edit])
    recorded = edit.model_copy(
        update={
            "to_matrix_version": after.matrix_version,
            "to_definition_version": after.definition_version,
        }
    )
    version, stopped = _advance(tx, actor, workspace_id, command.expected_version)
    store.insert_edit(tx, workspace_id, version, key, recorded)
    _event(tx, workspace_id, version)
    return CapabilityChange(
        version, stopped, edit.edit_id, after.matrix_version, after.definition_version
    )


def set_questions(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: SetQuestions
) -> CapabilityChange:
    visible_workspace(tx, workspace_id, lock=True)
    version, stopped = _advance(
        tx, actor, workspace_id, command.expected_version, stopped=command.stopped
    )
    _event(tx, workspace_id, version)
    return CapabilityChange(version, stopped, None)
