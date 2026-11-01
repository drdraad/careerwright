"""Response bodies of the capability endpoints. The matrices, question graph and readiness
results are the domain's own models (`careerwright.capability`), so the client is generated from
one definition of each state and enum (Global Constraint 10)."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from careerwright.api.origin_schemas import UsualSkillOut
from careerwright.capability.commands import CapabilityChange, CapabilityData
from careerwright.capability.matrix import Matrix
from careerwright.capability.questions import QuestionGraph
from careerwright.capability.readiness import Assessment
from careerwright.capability.skills import PersonQualification, TargetSkills
from careerwright.capability.skills_commands import SkillsView, UsualInRole
from careerwright.catalogue.option_pack import ReviewState
from careerwright.vocabulary import DataMode


class _Out(BaseModel):
    model_config = ConfigDict(frozen=True)


class PackLabel(_Out):
    """The option pack's date and review states, shown wherever its records are (R9)."""

    pack_version: str
    dated: date
    label_review: str
    records_proposed: int
    records_reviewed: int

    @classmethod
    def of(cls, data: CapabilityData) -> "PackLabel":
        states = [r.review_state for r in data.pack.records()]
        return cls(
            pack_version=data.pack.pack_version,
            dated=data.pack.dated,
            label_review=data.pack.label_review,
            records_proposed=sum(s is ReviewState.PROPOSED for s in states),
            records_reviewed=sum(s is ReviewState.REVIEWED for s in states),
        )


class ReferenceLabel(_Out):
    """The rubrics, crosswalks and gate types' version and review state."""

    reference_version: str
    dated: date
    review_state: str
    label_review: str

    @classmethod
    def of(cls, data: CapabilityData) -> "ReferenceLabel":
        reference = data.reference
        return cls(
            reference_version=reference.reference_version,
            dated=reference.dated,
            review_state=reference.review_state,
            label_review=reference.label_review,
        )


class MatricesOut(_Out):
    version: int  # the capability version: every write's expected version
    questions_stopped: bool
    profile_version: int  # the profile whose targets these are
    synthetic: bool  # the workspace's label: synthetic data is always labelled
    data_mode: DataMode
    pack: PackLabel
    reference: ReferenceLabel
    matrices: list[Matrix]  # one per target, in the profile's order; none without targets


class QuestionsOut(_Out):
    version: int
    profile_version: int
    synthetic: bool
    data_mode: DataMode
    pack: PackLabel  # the prompts show the pack's rows and the reference's anchors (R9)
    reference: ReferenceLabel
    graph: QuestionGraph


class ReadinessOut(_Out):
    version: int
    profile_version: int
    synthetic: bool
    data_mode: DataMode
    pack: PackLabel
    reference: ReferenceLabel
    assessments: list[Assessment]  # one per target: the current scenario


class UsualInRoleOut(_Out):
    """The essential skills ESCO lists for the kind of work of the person's role: usual in
    their role, not confirmed yet. Display only: wherever anything is computed it stays
    unresolved, and it is never evidence."""

    role_title: str  # in the person's words
    occupation_id: uuid.UUID
    occupation_label: str  # ESCO's preferred label
    skills: list[UsualSkillOut]  # never empty

    @classmethod
    def of(cls, found: UsualInRole) -> "UsualInRoleOut":
        return cls(
            role_title=found.role_title,
            occupation_id=found.occupation.concept_id,
            occupation_label=found.occupation.preferred_label,
            skills=[UsualSkillOut.of(s) for s in found.skills],
        )


class SkillsOut(_Out):
    """The Skills chapter's facts: for each target, what ESCO lists for its occupation, the
    person's own examples and the parts they chose, what the target asks with the person's
    qualifications beside it, and readiness wherever a rubric models it, with the rubrics'
    review state (`rubric_review`: `proposed` means a draft checklist; "not assessed yet"
    otherwise, never a result). Codes and numbers only: the web words them."""

    version: int  # the capability version: every Skills write's expected version
    profile_version: int
    synthetic: bool
    data_mode: DataMode
    pack: PackLabel  # the pack's date and review states, wherever its records are (R9)
    reference: ReferenceLabel
    targets: list[TargetSkills]  # one per target, in the profile's order
    questions: QuestionGraph  # the evidence questions, shared across targets
    usual_in_role: UsualInRoleOut | None = Field(
        description="Absent (null), never empty, when the person has no role, or none naming "
        "one ESCO occupation."
    )
    qualifications: list[PersonQualification]  # in the person's words, achieved or expected

    @classmethod
    def of(cls, view: SkillsView, data: CapabilityData) -> "SkillsOut":
        return cls(
            version=view.version,
            profile_version=view.profile_version,
            synthetic=view.synthetic,
            data_mode=view.data_mode,
            pack=PackLabel.of(data),
            reference=ReferenceLabel.of(data),
            targets=view.targets,
            questions=view.questions,
            usual_in_role=UsualInRoleOut.of(view.usual_in_role) if view.usual_in_role else None,
            qualifications=view.qualifications,
        )


class CapabilityChangeOut(_Out):
    version: int
    questions_stopped: bool
    recorded_id: uuid.UUID | None  # None: nothing was recorded (no change, or a state change)
    matrix_version: str | None  # an edit's resulting matrix and definition versions
    definition_version: str | None

    @classmethod
    def of(cls, change: CapabilityChange) -> "CapabilityChangeOut":
        return cls(
            version=change.version,
            questions_stopped=change.questions_stopped,
            recorded_id=change.recorded_id,
            matrix_version=change.matrix_version,
            definition_version=change.definition_version,
        )
