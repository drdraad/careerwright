"""API contract for the world's first moments (plan section 4; Sprint W SW.5): the origin (the
person's role, the skills it usually needs and the first destinations, with the unexpected
connection) and the overlooked strength. Computed by deterministic code over ESCO; only the
strength's proposal comes from a model, and code verifies it before it is shown."""

import uuid
from datetime import datetime

from pydantic import Field

from careerwright.api.catalogue_schemas import IscoGroupOut
from careerwright.api.discovery_schemas import (
    ConnectionOut,
    ReleaseRefOut,
    SalaryFloorOut,
    SuggestionOut,
)
from careerwright.api.schemas import ResponseModel, RunOut
from careerwright.capability.evidence import Answer
from careerwright.capability.strength import (
    DestinationKind,
    ProposedStrength,
    StrengthChoice,
    StrengthDecision,
)
from careerwright.capability.usual import UsualSkill, UsualState
from careerwright.catalogue.records import OccupationDetail, OccupationFacts
from careerwright.profile.exploration import FirstSlate, RoleState
from careerwright.profile.interview import ProfileField, ProposalOrigin
from careerwright.profile.slate_facts import FewerReason

FIXTURE_STRENGTH_LABEL = "Demo example (synthetic)"


class RoleOccupationOut(ResponseModel):
    concept_id: uuid.UUID
    title: str
    esco_uri: str
    isco_group: IscoGroupOut = Field(description="Its ISCO-08 unit group.")

    @classmethod
    def of_detail(cls, detail: OccupationDetail) -> "RoleOccupationOut":
        unit = detail.isco_groups[-1]
        return cls(
            concept_id=detail.concept_id,
            title=detail.preferred_label,
            esco_uri=detail.esco_uri,
            isco_group=IscoGroupOut(code=unit.code, label=unit.label),
        )

    @classmethod
    def of_facts(cls, facts: OccupationFacts) -> "RoleOccupationOut":
        return cls(
            concept_id=facts.concept_id,
            title=facts.preferred_label,
            esco_uri=facts.esco_uri,
            isco_group=IscoGroupOut(code=facts.unit.code, label=facts.unit.label),
        )


class RoleOut(ResponseModel):
    """What the person's answer to "What do you do now, or what did you do last?" names in
    ESCO. Nothing is guessed: an answer Careerwright couldn't match in ESCO joins nothing, and
    one it matched to several occupations asks the person to choose."""

    text: str | None = Field(description="The person's answer; null before they answer.")
    state: RoleState
    chosen: bool = Field(description="The person chose the occupation from ESCO.")
    occupation: RoleOccupationOut | None = Field(description="When it names one occupation.")
    choices: list[RoleOccupationOut] = Field(description="When several hold it as a title.")


class UsualSkillOut(ResponseModel):
    """An essential skill of the person's role in ESCO. `usual_in_role`: usual in your role,
    not confirmed yet, for display only (wherever anything is computed it is unresolved).
    `self_reported`: the person said they have used or done it (their own claim, never
    evidence). Record "I've used this" with `POST .../capability/evidence`, its `subject` and
    `answer: used`."""

    skill_id: uuid.UUID
    subject: str
    label: str
    skill_type: str | None
    state: UsualState
    answer: Answer | None = Field(description="The person's latest answer about it, if any.")
    evidence_id: uuid.UUID | None

    @classmethod
    def of(cls, usual: UsualSkill) -> "UsualSkillOut":
        return cls(
            skill_id=usual.skill.skill_id,
            subject=usual.subject,
            label=usual.skill.preferred_label,
            skill_type=usual.skill.skill_type,
            state=usual.state,
            answer=usual.answer,
            evidence_id=usual.evidence_id,
        )


class OriginOut(ResponseModel):
    """The world's answer to the first question, recomputed on each read with no model call:
    it works before a key is connected and in the demo. `destinations` are the first slate,
    joined to the role only by the essential skills they share in ESCO (never by words in a
    title), chosen by the slate's rules and the confirmed salary floor; the role itself is
    the origin, never a destination."""

    profile_version: int
    capability_version: int
    release: ReleaseRefOut
    role: RoleOut
    usual_skills: list[UsualSkillOut]
    destinations: list[SuggestionOut]
    fewer_reasons: list[FewerReason] = Field(
        description="Why there are fewer than six, if there are, as facts the web words."
    )
    connection: ConnectionOut | None
    salary_floor: SalaryFloorOut | None

    @classmethod
    def of(cls, first: FirstSlate, usual: list[UsualSkill], capability_version: int) -> "OriginOut":
        role = first.role
        return cls(
            profile_version=first.profile_version,
            capability_version=capability_version,
            release=ReleaseRefOut.of(first.release),
            role=RoleOut(
                text=role.text if role else None,
                state=first.state,
                chosen=bool(role and role.chosen),
                occupation=RoleOccupationOut.of_detail(first.occupation)
                if first.occupation
                else None,
                choices=[RoleOccupationOut.of_facts(f) for f in first.choices],
            ),
            usual_skills=[UsualSkillOut.of(u) for u in usual],
            destinations=[SuggestionOut.of(s, first.release) for s in first.suggestions],
            fewer_reasons=first.slate.fewer_reasons if first.slate else [],
            connection=ConnectionOut.of(first.connection) if first.connection else None,
            salary_floor=SalaryFloorOut.of(first.salary_floor) if first.salary_floor else None,
        )


class StrengthDestinationOut(ResponseModel):
    concept_id: uuid.UUID
    title: str
    kind: DestinationKind = Field(
        description="target: one the person chose; horizon: on their horizon."
    )


class ProposedStrengthOut(ResponseModel):
    """A proposal, never yet a fact: the person's own words (verified as a span of their
    answers) against a skill ESCO lists as essential to one of their destinations. It shows
    as a strength only once the person confirms it, and then as their own claim."""

    destination: StrengthDestinationOut
    skill_id: uuid.UUID
    skill_label: str
    subject: str
    quotation: str = Field(description="The person's words, in their own characters.")
    answer_field: ProfileField = Field(description="Which of their answers it quotes.")
    label: str | None = Field(description="Set for the demo's scripted, synthetic example.")

    @classmethod
    def of(cls, found: ProposedStrength, origin: ProposalOrigin) -> "ProposedStrengthOut":
        return cls(
            destination=StrengthDestinationOut(
                concept_id=found.destination.concept_id,
                title=found.destination.title,
                kind=found.destination.kind,
            ),
            skill_id=found.skill.skill_id,
            skill_label=found.skill.label,
            subject=f"esco:{found.skill.skill_id}",
            quotation=found.quotation.text,
            answer_field=found.quotation.answer_field,
            label=FIXTURE_STRENGTH_LABEL if origin is ProposalOrigin.FIXTURE else None,
        )


class StrengthDecisionOut(ResponseModel):
    strength_id: uuid.UUID
    decision: StrengthChoice
    evidence_id: uuid.UUID | None = Field(description="The self-report a confirmation recorded.")
    decided_by: uuid.UUID
    decided_at: datetime

    @classmethod
    def of(cls, decided: StrengthDecision) -> "StrengthDecisionOut":
        return cls(
            strength_id=decided.strength_id,
            decision=decided.decision,
            evidence_id=decided.evidence_id,
            decided_by=decided.decided_by,
            decided_at=decided.decided_at,
        )


class StrengthRunOut(ResponseModel):
    """The turn's one strength run (the command's answer: never the proposal itself)."""

    strength_id: uuid.UUID
    turn_id: uuid.UUID
    run: RunOut


class StrengthOut(StrengthRunOut):
    """The run, and once it is complete what it found: a proposal, or none (`found: false`,
    an answer, never a failure). A failed run's failure class says why there is none."""

    found: bool | None = Field(description="null until the run is complete.")
    proposal: ProposedStrengthOut | None
    decision: StrengthDecisionOut | None


class StrengthDecidedOut(ResponseModel):
    decision: StrengthDecisionOut
    capability_version: int
