"""The Skills chapter's facts for one target (Task 10, backend half; plan section 4's Skills
chapter; ADR 0012 as amended on 2026-10-31; ADR 0015). Pure: no SQL, no network, no model.

Facts and codes, never sentences (ruling R11): the web words every code.

- **What ESCO lists** for the target's occupation, labelled as ESCO's: the seed occupation
  the target's stored record names (the person's choice, the closest occupation they chose,
  the one occupation holding the title, or the pack's crosswalk), or none
  (`none_of_these`, or no occupation found). Each skill the person marked "not part of my
  job" carries the mark: a display state, never evidence, never a level.
- **What the target asks** (`requirements`): every required row of its matrix (the pack's
  rows, a protected gate, rows the person set essential), with its review state and the
  pack record's date, and the person's qualifications that name it as entry facts beside it.
- **Readiness where a rubric exists, with its review state.** A target is `assessed` when at
  least one required row is modelled by a rubric and the capability model's result is not
  `insufficient_coverage`; its readiness is the capability model's result, unchanged, and
  `rubric_review` says whether every rubric it rests on is `reviewed` or any is still
  `proposed` (the product owner's answer of 2026-11-01: show it, labelled as resting on a
  draft checklist). Otherwise it is `not_assessed`, with the reason (no rubric, then
  insufficient coverage) and what it asks, and no readiness result at all.
- **Entry facts.** A qualification the person gave names a requirement when its words, as a
  concept (`careerwright.concept_key`), appear whole in the requirement's label or in a
  posting's wording of it. Expected is never met; achieved is the person's own statement,
  so for a protected gate it stays unresolved until they verify it at its source (ADR 0012
  decision 4). Nothing here finds a person ineligible, and no entry fact feeds readiness.
  The parts the person chose in their own example adverts carry entry facts by the same rule:
  an advert's line is never a protected gate, so achieved there is
  `achieved_stated`.
"""

import uuid
from collections.abc import Mapping, Sequence
from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from careerwright.capability.adverts import SelectedSpan
from careerwright.capability.evidence import (
    Answer,
    Holding,
    Method,
    RequirementStatement,
    SkillEvidence,
    latest_statement,
)
from careerwright.capability.matrix import (
    GateInfo,
    Importance,
    Matrix,
    MatrixRow,
    OccupationLink,
    OccupationNote,
    PackTargetLink,
    PackTargetNote,
    RowKind,
    RowScope,
)
from careerwright.capability.readiness import Assessment, ReadinessState
from careerwright.profile.document import QualificationStatus


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SeedState(StrEnum):
    """Where the target's ESCO list comes from."""

    ESCO_OCCUPATION = "esco_occupation"  # an occupation its record names, by any link
    NONE_OF_THESE = "none_of_these"  # the person said none of the closest is their job
    NO_OCCUPATION = "no_occupation"  # none found (`occupation_note` says why)


class SkillsAssessmentState(StrEnum):
    ASSESSED = "assessed"
    NOT_ASSESSED = "not_assessed"  # "not assessed yet, here's what it asks": no readiness


class NotAssessedReason(StrEnum):
    # No required row a rubric models: a target outside the option pack, one with no closest
    # occupation, or one whose only modelled requirement is a protected gate.
    NO_RUBRIC = "no_rubric"
    # Rubrics model some of it, but a required row no answer can settle stands beside them (a
    # row with no rubric, or a regulation no typed gate models): the capability model's
    # `insufficient_coverage`.
    INSUFFICIENT_COVERAGE = "insufficient_coverage"


RubricReview = Literal["proposed", "reviewed"]


class EntryStanding(StrEnum):
    EXPECTED_NOT_MET = "expected_not_met"  # being taken, or a result to come: never met
    # Achieved, as the person states it, beside a protected gate: unresolved until they verify
    # it at its source (`POST .../capability/statements`), never ineligible.
    ACHIEVED_UNVERIFIED = "achieved_unverified"
    ACHIEVED_STATED = "achieved_stated"  # achieved, as the person states it: not checked


class EntryFact(StrictModel):
    """One of the person's qualifications, beside a requirement that names it."""

    qualification: str  # in the person's words
    status: QualificationStatus
    standing: EntryStanding


class EscoListedSkill(StrictModel):
    """A skill ESCO lists for the occupation's kind of work: ESCO's, never the person's."""

    skill_id: uuid.UUID
    subject: str  # `esco:<skill ID>`: what evidence about it is recorded against
    label: str
    skill_type: str | None
    relation: Literal["essential", "optional"]
    row_id: str  # the matrix row that carries it
    # The person marked it "not part of my job" (`PUT .../profile/titles`): a display state,
    # never evidence, never a level, never a demotion of a protected gate.
    not_part_of_job: bool


class SavedSkillAnswer(StrictModel):
    """The person's latest self-report against this row's rubric, for a later correction."""

    answer: Answer
    self_assessed_level: int | None
    example: str | None
    last_done: str | None


class Requirement(StrictModel):
    """A required row of the target's matrix: what the target asks."""

    row_id: str
    subject: str
    label: str
    kind: RowKind
    scope: RowScope
    importance: Importance
    gate: GateInfo | None  # a protected gate: always required, never demoted
    rubric_version: str | None  # None: not modelled
    rubric_review_state: Literal["proposed", "reviewed"] | None
    required_level: int | None
    review_state: Literal["proposed", "reviewed"]  # its pack records'
    as_of: date | None  # the latest retrieval date of the pack records it cites
    employer_specific: bool
    entry_facts: list[EntryFact]
    latest_holding: Holding | None
    source_urls: list[str]
    rubric_anchors: dict[int, str]
    latest_skill: SavedSkillAnswer | None


class ChosenPart(SelectedSpan):
    """A part the person chose in one of their own example adverts, with the qualifications
    of theirs that name it."""

    entry_facts: list[EntryFact]


class AdvertExample(StrictModel):
    """One of the person's own example adverts for the target, with their chosen spans."""

    job_id: uuid.UUID
    title: str | None
    employer: str | None
    text: str  # as it was kept, third parties' contact details removed
    spans: list[ChosenPart]  # the person's selection, in text order; empty: none chosen


class TargetSkills(StrictModel):
    target_key: str
    target_title: str
    matrix_version: str
    definition_version: str
    synthetic: bool
    seed: SeedState
    occupation: OccupationLink | None
    occupation_note: OccupationNote | None
    esco_release: str | None
    pack_target: PackTargetLink | None
    pack_target_note: PackTargetNote | None
    details_version: int = Field(
        ge=0, description="This target's title details, the marks' expected version."
    )
    esco_listed: list[EscoListedSkill]
    examples: list[AdvertExample]
    requirements: list[Requirement]
    assessment_state: SkillsAssessmentState
    not_assessed_reason: NotAssessedReason | None
    readiness: Assessment | None  # only when assessed: never a result otherwise
    # Only when assessed: `reviewed` when every rubric the result rests on is reviewed;
    # `proposed` when any is still a draft (the screens say "based on a draft checklist").
    rubric_review: RubricReview | None


class PersonQualification(StrictModel):
    """A qualification the person gave (Task 6f), in their words."""

    name: str
    status: QualificationStatus


def assessment_state(
    matrix: Matrix, assessment: Assessment
) -> tuple[SkillsAssessmentState, NotAssessedReason | None, RubricReview | None]:
    """Whether the target is assessed, why not, and the review state of the rubrics an
    assessed result rests on."""
    rubrics = [r.rubric for r in matrix.rows if r.required and r.rubric is not None]
    if not rubrics:
        return SkillsAssessmentState.NOT_ASSESSED, NotAssessedReason.NO_RUBRIC, None
    if assessment.state is ReadinessState.INSUFFICIENT_COVERAGE:
        return SkillsAssessmentState.NOT_ASSESSED, NotAssessedReason.INSUFFICIENT_COVERAGE, None
    review: RubricReview = (
        "reviewed" if all(r.review_state == "reviewed" for r in rubrics) else "proposed"
    )
    return SkillsAssessmentState.ASSESSED, None, review


def names(qualification_key: str, requirement_keys: Sequence[str]) -> bool:
    """Whether a qualification's words, as a concept, appear whole in a requirement's."""
    wanted = qualification_key.split()
    if not wanted:
        return False
    for key in requirement_keys:
        words = key.split()
        if any(words[i : i + len(wanted)] == wanted for i in range(len(words) - len(wanted) + 1)):
            return True
    return False


def requirement_texts(row: MatrixRow) -> list[str]:
    """The words a requirement is named by: its label and each posting's wording of it."""
    texts = [row.label]
    texts += [c.text for c in row.citations if c.text]
    texts += [c.gate_words for c in row.citations if c.gate_words]
    return texts


def _named_by(
    texts: Sequence[str],
    qualifications: Sequence[PersonQualification],
    keys: Mapping[str, str],
    *,
    protected: bool,
) -> list[EntryFact]:
    """The qualifications whose words name one of `texts`, each with its standing. `keys`
    holds every text as a concept."""
    if not qualifications:
        return []
    requirement_keys = [keys[t] for t in texts]
    found: list[EntryFact] = []
    for q in qualifications:
        if not names(keys[q.name], requirement_keys):
            continue
        if q.status is QualificationStatus.EXPECTED:
            standing = EntryStanding.EXPECTED_NOT_MET
        elif protected:
            standing = EntryStanding.ACHIEVED_UNVERIFIED
        else:
            standing = EntryStanding.ACHIEVED_STATED
        found.append(EntryFact(qualification=q.name, status=q.status, standing=standing))
    return found


def entry_facts(
    row: MatrixRow, qualifications: Sequence[PersonQualification], keys: Mapping[str, str]
) -> list[EntryFact]:
    """The qualifications that name this requirement, each with its standing."""
    return _named_by(requirement_texts(row), qualifications, keys, protected=row.gate is not None)


def chosen_parts(
    spans: Sequence[SelectedSpan],
    qualifications: Sequence[PersonQualification],
    keys: Mapping[str, str],
) -> list[ChosenPart]:
    """Each part the person chose in an advert, with the qualifications that name it. An
    advert's own line is never a protected gate."""
    return [
        ChosenPart(
            **span.model_dump(),
            entry_facts=_named_by([span.excerpt], qualifications, keys, protected=False),
        )
        for span in spans
    ]


def _saved_skill(row: MatrixRow, evidence: Sequence[SkillEvidence]) -> SavedSkillAnswer | None:
    if row.rubric is None:
        return None
    reports = sorted(
        (
            item
            for item in evidence
            if item.subject == row.subject
            and item.rubric_version == row.rubric.version_id
            and item.method is Method.SELF_REPORT
        ),
        key=lambda item: item.recorded_at,
    )
    if not reports:
        return None
    latest = reports[-1]
    return SavedSkillAnswer(
        answer=latest.answer,
        self_assessed_level=latest.self_assessed_level,
        example=latest.example,
        last_done=latest.last_done,
    )


def requirements(
    matrix: Matrix,
    qualifications: Sequence[PersonQualification],
    keys: Mapping[str, str],
    statements: Sequence[RequirementStatement] = (),
    evidence: Sequence[SkillEvidence] = (),
) -> list[Requirement]:
    return [
        Requirement(
            row_id=r.row_id,
            subject=r.subject,
            label=r.label,
            kind=r.kind,
            scope=r.scope,
            importance=r.importance,
            gate=r.gate,
            rubric_version=r.rubric.version_id if r.rubric else None,
            rubric_review_state=r.rubric.review_state if r.rubric else None,
            required_level=r.required_level,
            review_state=r.review_state,
            as_of=max((c.as_of for c in r.citations), default=None),
            employer_specific=r.employer_specific,
            entry_facts=entry_facts(r, qualifications, keys),
            latest_holding=(
                s.holding if (s := latest_statement(r.subject, list(statements))) else None
            ),
            source_urls=list(
                dict.fromkeys(
                    c.claim.url
                    for c in r.citations
                    if c.claim.url.startswith(("https://", "http://"))
                )
            ),
            rubric_anchors=dict(r.rubric.anchors) if r.rubric else {},
            latest_skill=_saved_skill(r, evidence),
        )
        for r in matrix.rows
        if r.required
    ]


def esco_listed(matrix: Matrix, marks: frozenset[uuid.UUID]) -> list[EscoListedSkill]:
    """Every skill ESCO lists for the seed occupation, essential first, as its rows carry it
    (an ESCO row, or a pack row its crosswalk folds in)."""
    found = [
        EscoListedSkill(
            skill_id=r.esco.skill_id,
            subject=f"esco:{r.esco.skill_id}",
            label=r.esco.label,
            skill_type=r.esco.skill_type,
            relation=r.esco.relation,
            row_id=r.row_id,
            not_part_of_job=r.esco.skill_id in marks,
        )
        for r in matrix.rows
        if r.esco is not None
    ]
    return sorted(found, key=lambda s: (s.relation != "essential", s.label))


def seed_state(matrix: Matrix, *, none_of_these: bool) -> SeedState:
    if matrix.sources.occupation is not None:
        return SeedState.ESCO_OCCUPATION
    return SeedState.NONE_OF_THESE if none_of_these else SeedState.NO_OCCUPATION


def target_skills(
    matrix: Matrix,
    assessment: Assessment,
    *,
    none_of_these: bool,
    marks: frozenset[uuid.UUID],
    details_version: int,
    examples: Sequence[AdvertExample],
    qualifications: Sequence[PersonQualification],
    keys: Mapping[str, str],
    statements: Sequence[RequirementStatement] = (),
    evidence: Sequence[SkillEvidence] = (),
) -> TargetSkills:
    """One target's Skills facts. `assessment` is the capability model's current result for
    this matrix; it is shown only when the target is assessed."""
    if (assessment.matrix_version, assessment.definition_version) != (
        matrix.matrix_version,
        matrix.definition_version,
    ):
        raise ValueError("the assessment is of another matrix")
    state, reason, review = assessment_state(matrix, assessment)
    sources = matrix.sources
    return TargetSkills(
        target_key=matrix.target_key,
        target_title=matrix.target_title,
        matrix_version=matrix.matrix_version,
        definition_version=matrix.definition_version,
        synthetic=matrix.synthetic,
        seed=seed_state(matrix, none_of_these=none_of_these),
        occupation=sources.occupation,
        occupation_note=sources.occupation_note,
        esco_release=sources.esco_release,
        pack_target=sources.pack_target,
        pack_target_note=sources.pack_target_note,
        details_version=details_version,
        esco_listed=esco_listed(matrix, marks),
        examples=list(examples),
        requirements=requirements(matrix, qualifications, keys, statements, evidence),
        assessment_state=state,
        not_assessed_reason=reason,
        readiness=assessment if state is SkillsAssessmentState.ASSESSED else None,
        rubric_review=review,
    )
