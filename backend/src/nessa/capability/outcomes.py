"""Planned course outcomes, `PlanAction.outcomes` (spec section 10, OUT-1; S4.5; ADR 0012).
Pure: no SQL, no network, no model.

An outcome maps an option's syllabus or assessment span to one matrix row. This module owns
what an outcome may claim (OUT1-11): the opportunity catalogue stores the records (the
option pack), a model or a curator only proposes them, and the review checkpoint accepts
them as modelling assumptions.

- **Mention, practice and assessed demonstration are distinct.** A level on completion needs
  an assessed kind (an exam or an assessed work sample), the row's rubric, and a source that
  supports it (not `unsupported`). "Introduction to SQL" never gives independent level 2: a
  topic mention or practice without assessment has a null level.
- **Credentials and supervised experience are their own outcome types,** never a level. A
  credential outcome leads only to eligibility to apply to the issuing body: no course ever
  satisfies a statutory gate, and accumulated levels never substitute for one.
- **A user override is an assumption,** never a provider claim and never expert validation:
  it keeps the provider's record unchanged beside it.
- **Planned, never demonstrated.** An outcome counts only in a conditional scenario after its
  completion gate, when accepted (`accepted_assumption`) or reviewed; it never changes the
  person's evidence. Overlapping outcomes take the highest level, never a sum.
"""

import uuid
from collections.abc import Iterable
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from nessa.capability.reference import Reference
from nessa.catalogue.option_pack import Pack

Level = Annotated[int, Field(ge=0, le=4)]
EXCERPT_CHARS = 400
MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidenceKind(StrEnum):
    TOPIC_MENTION = "topic_mention"  # named or taught
    PRACTICE = "practice"  # done, not assessed
    ASSESSED_WORK_SAMPLE = "assessed_work_sample"
    EXAM = "exam"


ASSESSED_KINDS = frozenset({EvidenceKind.ASSESSED_WORK_SAMPLE, EvidenceKind.EXAM})


class Confidence(StrEnum):
    """Categorical support from the source, never a model-generated probability."""

    UNSUPPORTED = "unsupported"
    PROVISIONAL = "provisional"
    CORROBORATED = "corroborated"


class OutcomeType(StrEnum):
    SKILL_LEVEL = "skill_level"
    CREDENTIAL = "credential"
    SUPERVISED_EXPERIENCE = "supervised_experience"


class OutcomeReview(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED_ASSUMPTION = "accepted_assumption"  # accepted at the checkpoint, conditional only
    REVIEWED = "reviewed"
    REJECTED = "rejected"


COUNTED_REVIEWS = frozenset({OutcomeReview.ACCEPTED_ASSUMPTION, OutcomeReview.REVIEWED})


class Provenance(StrEnum):
    PROVIDER_CLAIM = "provider_claim"  # read from the provider's page
    USER_OVERRIDE = "user_override"  # the person's correction: an assumption


class OutcomeSpan(StrictModel):
    """Source ID and hash, offsets or a pointer, retrieval date and the exact extract."""

    claim_id: str | None
    source_id: str
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    start: int | None
    end: int | None
    pointer: str | None
    retrieved_at: datetime | None
    excerpt: str = Field(min_length=1, max_length=EXCERPT_CHARS)


class CredentialOutcome(StrictModel):
    """What a credential outcome leads to: eligibility to apply, decided by the issuing body."""

    gate_key: str
    issuing_body: str  # who grants the credential or registration
    stated_recognition: str | None  # the recognising body as the page names it
    jurisdiction: str
    verification: str
    leads_to: Literal["eligibility_to_apply"] = "eligibility_to_apply"


class Assumption(StrictModel):
    reason: str = Field(min_length=1, max_length=400)
    recorded_by: uuid.UUID
    recorded_at: datetime


class PlannedOutcome(StrictModel):
    outcome_id: str
    offering_id: str
    option_id: str
    option_title: str | None
    skill_id: str  # the matrix row it is expected to address
    outcome_type: OutcomeType
    level_on_completion: Level | None
    evidence_kind: EvidenceKind
    confidence: Confidence
    source_span: OutcomeSpan
    rubric_version: str | None
    claim_state: Literal["planned_conditional"] = "planned_conditional"
    review_state: OutcomeReview
    provenance: Provenance
    overrides: str | None = None  # the provider outcome a user override stands beside
    assumption: Assumption | None = None  # who accepted or asserted it, and why
    credential: CredentialOutcome | None = None
    months_minimum: int | None = Field(default=None, ge=0)  # its shortest stated duration
    as_of: date  # retrieval date of the evidence: never "current"

    @model_validator(mode="after")
    def _supported(self) -> Self:
        if self.level_on_completion is not None:
            if self.outcome_type is not OutcomeType.SKILL_LEVEL:
                raise ValueError("a credential or experience outcome never has a level")
            if self.evidence_kind not in ASSESSED_KINDS:
                raise ValueError("a level on completion needs an assessed demonstration")
            if self.rubric_version is None:
                raise ValueError("a level on completion needs the rubric it is read against")
            if (
                self.provenance is Provenance.PROVIDER_CLAIM
                and self.confidence is Confidence.UNSUPPORTED
            ):
                raise ValueError("an unsupported outcome has no level")
        if (self.outcome_type is OutcomeType.CREDENTIAL) != (self.credential is not None):
            raise ValueError("a credential outcome names the credential it leads to")
        if self.provenance is Provenance.USER_OVERRIDE:
            if self.review_state not in (OutcomeReview.ACCEPTED_ASSUMPTION, OutcomeReview.REJECTED):
                raise ValueError("an override is an assumption: never proposed or reviewed")
            if self.overrides is None or self.assumption is None:
                raise ValueError("an override names the outcome it corrects and who made it")
        elif self.overrides is not None:
            raise ValueError("only an override names another outcome")
        return self

    @property
    def counted(self) -> bool:
        """Whether a conditional scenario may count it."""
        return self.review_state in COUNTED_REVIEWS


def minimum_months(duration: JsonValue) -> int | None:
    """The shortest stated way of taking it, in whole months (rounded up). A typical
    duration is not a bound and hours give no pace, so neither counts; None is unknown."""
    if not isinstance(duration, list):
        return None
    months: list[int] = []
    for part in duration:
        if not isinstance(part, dict) or part.get("typical") is True:
            continue
        low, unit = part.get("minimum"), part.get("unit")
        if not isinstance(low, int):
            continue
        if unit == "years":
            months.append(low * MONTHS_PER_YEAR)
        elif unit == "months":
            months.append(low)
        elif unit == "weeks":
            months.append(-(-low * MONTHS_PER_YEAR // WEEKS_PER_YEAR))
    return min(months, default=None)


def _text(value: JsonValue) -> str | None:
    return value if isinstance(value, str) else None


def pack_outcomes(pack: Pack, reference: Reference) -> list[PlannedOutcome]:
    """The pack's planned outcomes as this module's records, every one a provider claim."""
    offerings = {o.record_id: o for o in pack.offerings}
    options = {o.record_id: o for o in pack.learning_options}
    claims = {c.claim_id: c for c in pack.claims}
    sources = {s.source_id: s for s in pack.sources}
    skills = {s.skill_id: s for s in pack.skills}
    found = []
    for outcome in pack.outcomes:
        offering = offerings[outcome.offering_id]
        option = options[offering.option_id]
        claim = claims[outcome.source_span]
        source = sources[claim.source_id]
        kind = skills[outcome.skill_id].kind
        gate = reference.gate_for_row(outcome.skill_id)
        credential = None
        if kind == "credential" and gate is not None:
            credential = CredentialOutcome(
                gate_key=gate.gate_key,
                issuing_body=gate.issuing_body,
                stated_recognition=_text(pack.value(option.recognising_body)),
                jurisdiction=gate.jurisdiction,
                verification=gate.verification,
            )
        found.append(
            PlannedOutcome(
                outcome_id=outcome.record_id,
                offering_id=offering.record_id,
                option_id=option.record_id,
                option_title=_text(pack.value(option.title)),
                skill_id=outcome.skill_id,
                outcome_type=(
                    OutcomeType.CREDENTIAL
                    if kind == "credential"
                    else OutcomeType.SUPERVISED_EXPERIENCE
                    if kind == "experience"
                    else OutcomeType.SKILL_LEVEL
                ),
                level_on_completion=outcome.level_on_completion,
                evidence_kind=EvidenceKind(outcome.evidence_kind),
                confidence=Confidence(outcome.confidence),
                source_span=OutcomeSpan(
                    claim_id=claim.claim_id,
                    source_id=source.source_id,
                    source_hash=source.sha256,
                    start=claim.span.start,
                    end=claim.span.end,
                    pointer=claim.span.pointer,
                    retrieved_at=source.retrieved_at,
                    excerpt=claim.excerpt,
                ),
                rubric_version=outcome.rubric_version,
                review_state=OutcomeReview(outcome.review_state.value),
                provenance=Provenance.PROVIDER_CLAIM,
                credential=credential,
                months_minimum=minimum_months(pack.value(offering.duration)),
                as_of=outcome.as_of,
            )
        )
    return found


def accept(outcome: PlannedOutcome, *, by: uuid.UUID, at: datetime) -> PlannedOutcome:
    """The person accepts a provisional mapping as a modelling assumption: it may support a
    clearly conditional scenario, never an unqualified readiness claim."""
    return PlannedOutcome.model_validate(
        {
            **outcome.model_dump(),
            "review_state": OutcomeReview.ACCEPTED_ASSUMPTION,
            "assumption": Assumption(
                reason="accepted as a modelling assumption", recorded_by=by, recorded_at=at
            ),
        }
    )


def user_override(
    outcome: PlannedOutcome,
    *,
    evidence_kind: EvidenceKind,
    level_on_completion: int | None,
    rubric_version: str | None,
    reason: str,
    by: uuid.UUID,
    at: datetime,
) -> PlannedOutcome:
    """The person's correction of a mapping, kept beside the provider's record."""
    return PlannedOutcome.model_validate(
        {
            **outcome.model_dump(),
            "outcome_id": f"{outcome.outcome_id}#override",
            "evidence_kind": evidence_kind,
            "level_on_completion": level_on_completion,
            "rubric_version": rubric_version,
            "review_state": OutcomeReview.ACCEPTED_ASSUMPTION,
            "provenance": Provenance.USER_OVERRIDE,
            "overrides": outcome.outcome_id,
            "assumption": Assumption(reason=reason, recorded_by=by, recorded_at=at),
        }
    )


def planned_level(
    row_id: str,
    rubric_version: str | None,
    outcomes: Iterable[PlannedOutcome],
    completed: frozenset[str],
) -> tuple[int | None, list[PlannedOutcome]]:
    """The highest level the counted outcomes of completed offerings plan for a row, read
    against its rubric, and the outcomes used. Ordinal levels are never added."""
    used = [
        o
        for o in outcomes
        if o.skill_id == row_id
        and o.counted
        and o.offering_id in completed
        and o.outcome_type is OutcomeType.SKILL_LEVEL
        and o.level_on_completion is not None
        and o.rubric_version == rubric_version
    ]
    level = max(
        (o.level_on_completion for o in used if o.level_on_completion is not None), default=None
    )
    return level, used
