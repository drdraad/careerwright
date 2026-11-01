"""The Skills chapter's reads and its one new write (Task 10, backend half; ADR 0012 as
amended; ADR 0006: direct edits and confirmed chat proposals through the same commands).

The read gathers, for each target, what `careerwright.capability.skills` turns into facts: its
matrix and current readiness, the person's "not part of my job" marks beside it, their own
example adverts with the spans they chose, and their qualifications; and, once, the usual
skills of their role's kind of work (absent, never empty, when there is no role) and the
question graph shared across targets.

The write records the person's selection of spans in one of their own examples for a target:
an expected capability version and an Idempotency-Key, no model run. Every other Skills
write is an existing command: evidence, requirement statements and matrix edits
(`careerwright.capability.commands`) and the marks (`careerwright.profile.title_details`). A chat
proposal of any of these, when one exists, commits only through the same command.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import Field

from careerwright.capability import store, usual
from careerwright.capability.adverts import (
    MAX_SPANS_PER_EXAMPLE,
    AdvertSpan,
    check_spans,
    read_spans,
)
from careerwright.capability.commands import (
    CapabilityChange,
    CapabilityData,
    VersionedCommand,
    advance_version,
    capability_event,
    capability_view,
    pack_targets,
    questions,
    readiness,
)
from careerwright.capability.evidence import SkillEvidence
from careerwright.capability.questions import QuestionGraph
from careerwright.capability.skills import (
    AdvertExample,
    PersonQualification,
    TargetSkills,
    requirement_texts,
    target_skills,
)
from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.records import OccupationDetail
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import acquisition
from careerwright.evidence.jobs import title_key
from careerwright.identity.access import Actor
from careerwright.identity.keyring import Keyring
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile.commands import current_profile
from careerwright.profile.document import (
    FieldState,
    ProfileDocument,
    QualificationAnswer,
    TextValue,
)
from careerwright.profile.records import TargetLink
from careerwright.profile.targets import target_titles
from careerwright.profile.title_details import role_marks, target_details
from careerwright.vocabulary import DataMode


@dataclass(frozen=True)
class UsualInRole:
    """The essential skills ESCO lists for the kind of work of the person's role: usual in
    their role, not confirmed yet (display only)."""

    role_title: str
    occupation: OccupationDetail
    skills: list[usual.UsualSkill]  # never empty: no skills, no panel


@dataclass(frozen=True)
class SkillsView:
    version: int  # the capability version: every Skills write's expected version
    profile_version: int
    synthetic: bool
    data_mode: DataMode
    targets: list[TargetSkills]
    questions: QuestionGraph
    usual_in_role: UsualInRole | None  # None: no role, or none naming one occupation
    qualifications: list[PersonQualification]


def _qualifications(document: ProfileDocument) -> list[PersonQualification]:
    field = document.qualifications
    if field.state is not FieldState.PROVIDED or not field.value:
        return []
    return [
        PersonQualification(name=q.name, status=q.status)
        for q in field.value
        if isinstance(q, QualificationAnswer)
    ]


def _usual_in_role(
    tx: Tx,
    workspace_id: uuid.UUID,
    document: ProfileDocument,
    data: CapabilityData,
    evidence: list[SkillEvidence],
) -> UsualInRole | None:
    role = document.current_role
    if role.state is not FieldState.PROVIDED or not role.value:
        return None  # no role given, or "I haven't had a job yet": no panel, never an empty one
    occupation = usual.role_occupation(tx, workspace_id, pack_targets(data))
    if occupation is None:
        return None
    marks = role_marks(tx, workspace_id, document)
    found = usual.usual_skills(occupation, evidence, marks)
    return UsualInRole(str(role.value), occupation, found) if found else None


def skills_view(
    tx: Tx, workspace_id: uuid.UUID, data: CapabilityData, keyring: Keyring
) -> SkillsView:
    view = capability_view(tx, workspace_id, data)
    document = current_profile(tx, workspace_id).document
    qualifications = _qualifications(document)
    details = target_details(tx, workspace_id, document)
    examples = acquisition.examples(tx, keyring, workspace_id)
    selections = {(s.target_key, s.job_id): s for s in store.span_selections(tx, workspace_id)}
    texts = [q.name for q in qualifications]
    texts += [t for m in view.matrices for r in m.rows if r.required for t in requirement_texts(r)]
    keys = taxonomy_store.concept_keys(tx, texts) if qualifications else {t: "" for t in texts}
    targets: list[TargetSkills] = []
    for matrix, record, assessment in zip(
        view.matrices, view.records, readiness(view, data), strict=True
    ):
        held = details.get(record.key)
        shown: list[AdvertExample] = []
        for example in examples.get(matrix.target_key, []):
            chosen = selections.get((matrix.target_key, example.job_id))
            if chosen is not None and chosen.content_sha256 != example.sha256:
                raise CareerwrightError(  # kept text never changes: never shown as no spans
                    ErrorCode.INTERNAL_ERROR,
                    "An example's chosen parts don't match its text.",
                    stage=ErrorStage.CAPABILITY,
                )
            shown.append(
                AdvertExample(
                    job_id=example.job_id,
                    title=example.title,
                    employer=example.employer,
                    text=example.text,
                    spans=read_spans(example.text, chosen.spans) if chosen else [],
                )
            )
        targets.append(
            target_skills(
                matrix,
                assessment,
                none_of_these=record.link is TargetLink.NONE_OF_THESE,
                marks=frozenset(held.not_part_of_job) if held else frozenset(),
                details_version=held.version if held else 0,
                examples=shown,
                qualifications=qualifications,
                keys=keys,
            )
        )
    return SkillsView(
        version=view.version,
        profile_version=view.profile_version,
        synthetic=view.synthetic,
        data_mode=view.data_mode,
        targets=targets,
        questions=questions(view),
        usual_in_role=_usual_in_role(tx, workspace_id, document, data, view.evidence),
        qualifications=qualifications,
    )


class SelectAdvertSpans(VersionedCommand):
    """The parts of one of the person's own example adverts that say what the target asks
    for, as character offsets into its text. An empty list clears the selection."""

    target: TextValue = Field(description="One of the profile's target titles.")
    job_id: uuid.UUID = Field(description="One of the person's own examples for that target.")
    spans: list[AdvertSpan] = Field(max_length=MAX_SPANS_PER_EXAMPLE)


def select_advert_spans(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: SelectAdvertSpans,
    *,
    keyring: Keyring,
    now: datetime,
) -> CapabilityChange:
    visible_workspace(tx, workspace_id, lock=True)
    key = title_key(command.target)
    document = current_profile(tx, workspace_id).document
    if not key or key not in {title_key(t) for t in target_titles(document)}:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND,
            "That is not one of your target roles.",
            stage=ErrorStage.CAPABILITY,
        )
    example = next(
        (
            e
            for e in acquisition.examples(tx, keyring, workspace_id).get(key, [])
            if e.job_id == command.job_id
        ),
        None,
    )
    if example is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND,
            "That is not one of your examples for this target.",
            stage=ErrorStage.CAPABILITY,
        )
    spans = check_spans(example.text, command.spans)
    version, stopped = advance_version(tx, actor, workspace_id, command.expected_version)
    selection_id = uuid.uuid4()
    store.insert_span_selection(
        tx,
        workspace_id,
        version,
        selection_id=selection_id,
        target_key=key,
        job_id=example.job_id,
        content_sha256=example.sha256,
        spans=spans,
        recorded_by=actor.actor_id,
        recorded_at=now,
    )
    capability_event(tx, workspace_id, version)
    return CapabilityChange(version, stopped, selection_id)
