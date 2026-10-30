"""The person's skill evidence and requirement statements (spec section 9; S4.2; ADR 0012).
Pure: no SQL, no network, no model.

Evidence is about a subject shared across targets (an ESCO skill, a pack row, a gate), so
an answer is asked once. Its level is chosen against one rubric's anchors and counts only
for rows with that rubric: the same label in another target may have another rubric or
required level, so the example is reused there and the level asked again.

Three things are kept apart (ASSESS-01): the level the person gives themselves, a level a
reviewed demonstration or assessment shows, and the confidence of the evidence. An
unsupported claim stays self-reported, never false. What counts towards readiness
(ADR 0012, provisional):

- a reviewed demonstration or assessment: its level, `provisional`, never `corroborated`:
  L0 has no reviewer, so every demonstration is the person's own entry and a result that
  rests on one says so (`person_confirmed_demonstration`);
- otherwise the latest self-report with a concrete example and when it was last done: its
  level, `provisional`;
- a self-report without an example is kept as `unsupported`, and counts for nothing.

The five answers mean different things (spec section 9). "I have not learned this" and "I
understand it but have not tried" are a known level 0: nothing to ask again, a gap to learn.
"I am unsure" is an unresolved assumption: unknown, never level 0, and not asked again.
"I did it with help" is at most level 1, since levels 2 to 4 are defined by independence
(spec section 8's anchors). An answer that contradicts its level is refused. A level-free
answer given under one rubric fills another target's row only when that row has no answer
of its own, never supersedes one, and is reopened by a later level under another rubric.

Course enrolment and completion are not evidence at all: an assessed completion counts only
once its evidence is reviewed (OUT1-05). Time in a job never adds a level by itself.

Requirement statements answer the non-skill rows: credentials, experience and eligibility.
A protected gate is satisfied only when the person holds it and has verified it; unverified
stays unresolved, never ineligible.
"""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careerwright.capability.outcomes import Confidence

Level = Annotated[int, Field(ge=0, le=4)]
Month = Annotated[str, Field(pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$")]
EXAMPLE_CHARS = 1_000
NOTE_CHARS = 300


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Answer(StrEnum):
    """The five answers the interview pattern distinguishes, each in the same neutral tone."""

    DONE_INDEPENDENTLY = "done_independently"
    DONE_WITH_HELP = "done_with_help"
    UNDERSTAND_NOT_TRIED = "understand_not_tried"
    NOT_LEARNED = "not_learned"
    UNSURE = "unsure"


NOT_YET_DONE = frozenset({Answer.NOT_LEARNED, Answer.UNDERSTAND_NOT_TRIED})  # known level 0
WITH_HELP_MAX = 1  # "1 performs with guidance"; 2 to 4 are independent (spec section 8)


class Method(StrEnum):
    SELF_REPORT = "self_report"
    WORK_SAMPLE = "work_sample"  # an optional short sample or artifact, reviewed
    ASSESSMENT = "assessment"  # a formal assessment, such as a course's assessed completion


class EvidenceContext(StrEnum):
    """Where it was done: transferable evidence from any of these counts."""

    PAID_WORK = "paid_work"
    STUDY = "study"
    VOLUNTEERING = "volunteering"
    CARING = "caring"
    OTHER = "other"


class SkillEvidence(StrictModel):
    evidence_id: uuid.UUID
    subject: str = Field(min_length=1, max_length=200)
    rubric_version: str | None = Field(default=None, max_length=200)  # the anchors shown
    answer: Answer
    self_assessed_level: Level | None
    example: str | None = Field(default=None, max_length=EXAMPLE_CHARS)  # what they did
    last_done: Month | None = None  # recency
    context: EvidenceContext | None = None
    independence: Literal["independent", "with_help"] | None = None
    complexity: Literal["routine", "complex"] | None = None
    tools: str | None = Field(default=None, max_length=NOTE_CHARS)  # help and tools used
    # AI-assisted work is legitimate where the target's real tasks allow it, and is never
    # presented as unaided: the flag travels with every reading of this evidence.
    ai_assisted: bool | None = None
    method: Method = Method.SELF_REPORT
    demonstrated_level: Level | None = None
    assessed_by: str | None = Field(default=None, max_length=NOTE_CHARS)
    reviewed_on: date | None = None  # a demonstration counts only once reviewed
    outcome_id: str | None = Field(default=None, max_length=200)  # an assessed completion's
    recorded_by: uuid.UUID
    recorded_at: datetime

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        level = self.self_assessed_level
        if self.answer is Answer.UNSURE and level is not None:
            raise ValueError("an unsure answer has no level: unknown is not level 0")
        if self.answer in NOT_YET_DONE and level not in (None, 0):
            raise ValueError("that answer contradicts its level: no performance yet is level 0")
        if self.answer is Answer.DONE_WITH_HELP and level is not None and level > WITH_HELP_MAX:
            raise ValueError("'with help' contradicts an independent level (2 to 4)")
        if self.method is Method.SELF_REPORT:
            if self.demonstrated_level is not None or self.reviewed_on is not None:
                raise ValueError("a self-report has no demonstrated level and no review")
            if self.outcome_id is not None:
                raise ValueError("only an assessment closes a planned outcome")
        elif self.demonstrated_level is None:
            raise ValueError("a demonstration or assessment states the level it showed")
        if self.outcome_id is not None and self.method is not Method.ASSESSMENT:
            raise ValueError("only an assessment closes a planned outcome")
        return self


class Holding(StrEnum):
    HELD = "held"
    NOT_HELD = "not_held"
    UNKNOWN = "unknown"  # "I don't know": marked unresolved


class RequirementStatement(StrictModel):
    statement_id: uuid.UUID
    subject: str = Field(min_length=1, max_length=200)
    holding: Holding
    verified: bool  # the person checked it at its source (a register, a right to work check)
    verification_note: str | None = Field(default=None, max_length=NOTE_CHARS)
    recorded_by: uuid.UUID
    recorded_at: datetime

    @model_validator(mode="after")
    def _verified_only_if_held(self) -> Self:
        if self.verified and self.holding is not Holding.HELD:
            raise ValueError("only a requirement the person holds can be verified")
        return self


class RowEvidence(StrictModel):
    """What one row reads from the evidence on its subject, against its own rubric."""

    level: Level | None  # what counts towards readiness; None is unknown
    basis: Literal["demonstrated", "self_reported", "none"]
    confidence: Confidence | None  # never corroborated while L0 has no reviewer
    answer: Answer | None  # the latest self-report's answer, of the five
    self_assessed_level: Level | None
    demonstrated_level: Level | None
    last_done: str | None
    independence: Literal["independent", "with_help"] | None
    tools: str | None
    ai_assisted: bool | None
    evidence_ids: list[uuid.UUID]  # what this reading rests on
    shared_from_other_rubric: bool  # an answer exists for another rubric: reuse, ask again
    conflict: bool  # self-report and demonstration disagree: a clarification, never blame


def row_evidence(
    subject: str, rubric_version: str | None, evidence: list[SkillEvidence]
) -> RowEvidence:
    on_subject = [e for e in evidence if e.subject == subject]
    own = [e for e in on_subject if _own(e, rubric_version)]
    foreign = [e for e in on_subject if not _own(e, rubric_version)]
    shown = [e for e in own if e.method is not Method.SELF_REPORT and e.reviewed_on is not None]
    latest, disagreeing = _reading(own, foreign)
    demonstrated = max(
        (e.demonstrated_level for e in shown if e.demonstrated_level is not None), default=None
    )
    claimed = latest.self_assessed_level if latest is not None else None
    if latest is not None and latest.answer in NOT_YET_DONE:
        claimed = 0  # no performance yet: a known level 0, whatever the rubric
    concrete = latest is not None and bool(latest.example) and latest.last_done is not None
    level: int | None
    basis: Literal["demonstrated", "self_reported", "none"]
    confidence: Confidence | None
    if demonstrated is not None:
        # The person entered the demonstration and its review: L0 has no reviewer.
        level, basis, confidence = demonstrated, "demonstrated", Confidence.PROVISIONAL
    elif latest is not None and latest.answer in NOT_YET_DONE:
        level, basis, confidence = 0, "self_reported", Confidence.PROVISIONAL
    elif latest is not None and latest.answer is Answer.UNSURE:
        level, basis, confidence = None, "self_reported", None
    elif claimed is not None and concrete:
        level, basis, confidence = claimed, "self_reported", Confidence.PROVISIONAL
    elif claimed is not None:
        level, basis, confidence = None, "self_reported", Confidence.UNSUPPORTED
    else:
        level, basis, confidence = None, "none", None
    used = [*shown, *([latest] if latest is not None else [])]
    return RowEvidence(
        level=level,
        basis=basis,
        confidence=confidence,
        answer=latest.answer if latest is not None else None,
        self_assessed_level=claimed,
        demonstrated_level=demonstrated,
        last_done=latest.last_done if latest is not None else None,
        independence=latest.independence if latest is not None else None,
        tools=latest.tools if latest is not None else None,
        ai_assisted=latest.ai_assisted if latest is not None else None,
        evidence_ids=[e.evidence_id for e in used],
        shared_from_other_rubric=bool(foreign),
        conflict=disagreeing
        or (demonstrated is not None and claimed is not None and claimed != demonstrated),
    )


LEVEL_FREE = frozenset({*NOT_YET_DONE, Answer.UNSURE})


def _own(evidence: SkillEvidence, rubric_version: str | None) -> bool:
    return evidence.rubric_version is not None and evidence.rubric_version == rubric_version


def _level_free(evidence: SkillEvidence) -> bool:
    return evidence.method is Method.SELF_REPORT and evidence.answer in LEVEL_FREE


def _levelled(evidence: SkillEvidence) -> bool:
    return (
        evidence.method is Method.SELF_REPORT
        and evidence.self_assessed_level is not None
        and (evidence.answer not in LEVEL_FREE)
    )


def _reading(
    own: list[SkillEvidence], foreign: list[SkillEvidence]
) -> tuple[SkillEvidence | None, bool]:
    """The self-report a row reads, and whether another rubric's answer disagrees with it.

    A row's own answer (under its rubric) always wins. An answer that needs no level (unsure,
    or not yet done) given under another rubric fills a row that has no answer of its own,
    and never supersedes one: if it is later and says "not yet done" against an own level
    above 0, that is a conflict, asked as a clarification (S4.2: shared, never assumed the
    same). A later levelled answer under another rubric reopens a level-free reading, so the
    row is asked again against its own rubric (review N1)."""
    reports = sorted(
        (e for e in own if e.method is Method.SELF_REPORT), key=lambda e: e.recorded_at
    )
    free = sorted((e for e in foreign if _level_free(e)), key=lambda e: e.recorded_at)
    levelled_at = max((e.recorded_at for e in foreign if _levelled(e)), default=None)
    latest = reports[-1] if reports else (free[-1] if free else None)
    if latest is None:
        return None, False
    if _level_free(latest) and levelled_at is not None and levelled_at > latest.recorded_at:
        return None, False  # reopened: another rubric's later level, asked again here
    disagreeing = (
        bool(reports)
        and not _level_free(latest)
        and (latest.self_assessed_level or 0) > 0
        and any(e.answer in NOT_YET_DONE and e.recorded_at > latest.recorded_at for e in free)
    )
    return latest, disagreeing


def latest_statement(
    subject: str, statements: list[RequirementStatement]
) -> RequirementStatement | None:
    found = [s for s in statements if s.subject == subject]
    return max(found, key=lambda s: s.recorded_at) if found else None
