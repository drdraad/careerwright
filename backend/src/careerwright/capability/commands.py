"""Capability use cases (S4.1-S4.6; ADR 0012): read the matrices, the question graph and
readiness for the person's targets; record evidence, requirement statements and matrix
edits; stop or resume the questions.

Reads are computed from the current profile's targets, the committed option pack and
capability reference, the held ESCO release and the workspace's own records, so nothing
derived is stored and nothing goes stale silently: every result carries the versions it was
computed from. A target's pack target and its ESCO seed are what its stored record names
(`careerwright.profile.targets`, decided once when the target was chosen or saved): the
occupation the person chose, the one occupation holding the title as a label, or else the
pack target's crosswalk.

Every write is one command (direct edits now, confirmed chat proposals later, through the
same command): it locks the workspace, checks the expected capability version, records one
append-only row, moves the version on by one and appends a status event. A refused write
records nothing.
"""

import uuid
from dataclasses import dataclass, field
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
    PackTargetNote,
    RowEdit,
    apply_edits,
    build_matrix,
    check_edit,
)
from careerwright.capability.outcomes import PlannedOutcome, pack_outcomes
from careerwright.capability.questions import QuestionGraph, question_graph
from careerwright.capability.readiness import Assessment, assess
from careerwright.capability.reference import Reference, load_reference
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.esco import concept_id
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
from careerwright.profile.commands import current_profile
from careerwright.profile.document import TextValue
from careerwright.profile.records import TargetCoverage, TargetLink, TargetRecord
from careerwright.profile.targets import PackTarget, PackTargets, stored_targets, target_titles
from careerwright.vocabulary import DataMode

# The versions the capability model and planning read, each through its pin (`PINS`,
# `load_pack`, `load_reference`): Task 7f's reviewed school-leaver pack 0.4.0 (Task 12b), and
# the reference 0.2.0, carried unchanged to it because 0.4.0 keeps 0.2.0's targets, skill rows,
# requirements and postings (`reference.CARRIED_TO`). Earlier versions stay committed.
PACK_VERSION = "0.4.0"
REFERENCE_VERSION = "0.2.0"


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


def pack_targets(data: CapabilityData) -> PackTargets:
    """The pack's targets and the ESCO occupations their crosswalks name, as a target's stored
    record is decided against them (`careerwright.profile.targets`)."""
    return PackTargets(
        data.pack.pack_version,
        tuple(
            PackTarget(
                target.target_id,
                target.title,
                crosswalk.esco_occupation
                if (crosswalk := data.reference.crosswalk_for(target.target_id))
                else None,
            )
            for target in data.pack.targets
        ),
    )


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
    records: list[TargetRecord] = field(default_factory=list)  # each matrix's, in its order


def capability_view(tx: Tx, workspace_id: uuid.UUID, data: CapabilityData) -> CapabilityView:
    workspace = visible_workspace(tx, workspace_id)
    profile = current_profile(tx, workspace_id)
    matrices: list[Matrix] = []
    records: list[TargetRecord] = []
    if target_titles(profile.document):
        release = held_release(tx)  # TAXONOMY_UNAVAILABLE without one: never an empty matrix
        records = stored_targets(tx, workspace_id, profile.document, pack_targets(data))
        matrices = [
            _matrix(tx, workspace_id, record, data, release, synthetic=workspace.synthetic)
            for record in records
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
        records=records,
    )


def _matrix(
    tx: Tx,
    workspace_id: uuid.UUID,
    record: TargetRecord,
    data: CapabilityData,
    release: TaxonomyRelease,
    *,
    synthetic: bool,
) -> Matrix:
    """A target's matrix from its stored record: its pack target and its ESCO seed are what
    the record names (`careerwright.profile.targets`), never resolved from the title again."""
    key = title_key(record.title)
    seed, note = _seed(tx, record, release)
    pack_target = _pack_target(record, data.pack)
    several = record.coverage is TargetCoverage.SEVERAL_PACK_TARGETS
    return build_matrix(
        record.title,
        pack=data.pack,
        reference=data.reference,
        pack_target=pack_target,
        pack_target_basis=record.pack_target_basis or "title",
        pack_target_note=PackTargetNote.AMBIGUOUS_CROSSWALK if several else None,
        occupation=seed,
        exemplars=evidence_store.exemplar_count(tx, workspace_id, key),
        synthetic=synthetic,
        edits=store.edits(tx, workspace_id, key),
        occupation_note=note,
    )


def _pack_target(record: TargetRecord, pack: Pack) -> Target | None:
    if record.pack_target_id is None:
        return None
    target = next((t for t in pack.targets if t.target_id == record.pack_target_id), None)
    if target is None:  # a record decided against a pack that held a target this one lacks
        raise CareerwrightError(
            ErrorCode.INTERNAL_ERROR,
            "A target's record names a pack target the committed pack doesn't hold.",
            stage=ErrorStage.CAPABILITY,
        )
    return target


_BASIS: dict[TargetLink, OccupationBasis] = {
    TargetLink.OCCUPATION_CHOICE: "occupation_choice",
    TargetLink.EXACT_LABEL: "esco_label",
    TargetLink.PACK_CROSSWALK: "pack_crosswalk",
}


def _seed(
    tx: Tx, record: TargetRecord, release: TaxonomyRelease
) -> tuple[EscoSeed | None, OccupationNote | None]:
    """The occupation the record names, by any link: the person's choice, the one occupation
    holding the title as a label, or the pack target's crosswalk."""
    if record.occupation_uri is None:
        several = len(record.label_matches) > 1
        return None, OccupationNote.AMBIGUOUS_LABEL if several else OccupationNote.NO_EXACT_LABEL
    detail = taxonomy_store.occupation(tx, concept_id(record.occupation_uri))
    if detail is None:
        return None, OccupationNote.NOT_IN_HELD_TAXONOMY
    seed = EscoSeed(
        release=release.dataset_id,
        concept_id=detail.concept_id,
        label=detail.preferred_label,
        regulated=detail.regulated,
        basis=_BASIS[record.link],
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


class VersionedCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_version: int = Field(ge=0, description="0 while nothing has been recorded.")


class RecordEvidence(VersionedCommand):
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


class RecordStatement(VersionedCommand):
    """Whether the person holds a credential, experience or eligibility requirement."""

    subject: str = Field(min_length=1, max_length=200)
    holding: Holding
    verified: bool = Field(description="Checked at its source: a register, a right to work check.")
    verification_note: str | None = Field(default=None, max_length=300)


class EditRow(VersionedCommand):
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


class SetQuestions(VersionedCommand):
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


def advance_version(
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


def capability_event(tx: Tx, workspace_id: uuid.UUID, version: int) -> None:
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
    role = usual.role_occupation(tx, workspace_id, pack_targets(data))
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
    version, stopped = advance_version(tx, actor, workspace_id, expected_version)
    store.insert_evidence(tx, workspace_id, version, evidence)
    capability_event(tx, workspace_id, version)
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
    version, stopped = advance_version(tx, actor, workspace_id, command.expected_version)
    store.insert_statement(tx, workspace_id, version, statement)
    capability_event(tx, workspace_id, version)
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
    version, stopped = advance_version(tx, actor, workspace_id, command.expected_version)
    store.insert_edit(tx, workspace_id, version, key, recorded)
    capability_event(tx, workspace_id, version)
    return CapabilityChange(
        version, stopped, edit.edit_id, after.matrix_version, after.definition_version
    )


def set_questions(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, command: SetQuestions
) -> CapabilityChange:
    visible_workspace(tx, workspace_id, lock=True)
    version, stopped = advance_version(
        tx, actor, workspace_id, command.expected_version, stopped=command.stopped
    )
    capability_event(tx, workspace_id, version)
    return CapabilityChange(version, stopped, None)
