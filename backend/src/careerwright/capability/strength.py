"""The overlooked strength (plan section 4, "Revelations are earned"; ADR 0014 decision 3;
Sprint W SW.5): the one revelation a model may propose.

One bounded model call per conversation turn that added answers. The run sends the model the
answers the turn's decision saved that describe work (never a name, place, money or hours,
SEC-05) and the essential skills ESCO lists for each of the person's destinations (a target
they chose, or a destination on their horizon), and gets back at most one proposal: a
destination, one of its essential skills, and a quotation of the person's own words that
shows it. The model writes no prose.

`check_strength` validates it deterministically: the destination is one the input named, the
skill is one ESCO lists as essential to that destination (the input carries only those),
and the quotation is an exact span of one of the person's answers at word boundaries,
holding a content word (`careerwright.profile.slate_explanation`'s verifier: only the quoted
words are checked). Finding none is an answer, never a failure. The strength shows only once
the person confirms it, and then as their own claim (self-reported), never as evidence.
"""

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from careerwright.catalogue.records import SkillRef
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity.model_registry import worst_case_cost_nano_usd
from careerwright.profile.discovery import EvidenceItem
from careerwright.profile.interview import ProfileField, ProposalOrigin
from careerwright.profile.slate_explanation import (
    accepted_quotation,
    content_words,
    quotable,
    quoted_span,
    repair_message,
)

PROMPT_VERSION = "overlooked-strength-1"
INPUT_FORMAT: Literal["careerwright.strength-input"] = "careerwright.strength-input"
# How many essential skills of each destination the prompt carries, most first: the first
# step whose prompt fits `MAX_PROMPT_BYTES` is used. The answers are never cut.
SKILL_STEPS = (24, 16, 10, 6, 3)
# Bounds for the spend reservation (bytes bound tokens for byte-level BPE tokenizers).
MAX_PROMPT_BYTES = 9_000  # instructions plus the rendered context, at every bound
SCHEMA_ALLOWANCE_TOKENS = 600
MAX_OUTPUT_TOKENS = 1_000
REPAIR_ALLOWANCE_TOKENS = 600
MAX_REQUESTS = 2  # the first request and at most one repair
ECHO_CHARS = 60
CONTEXT_MARKER = "Strength context (JSON):\n"
# The answers a strength may quote: what the person enjoys, believes they can do and has
# done. A title (their role or a target) is never quoted as a strength of itself.
ANSWER_FIELDS = (
    ProfileField.ENJOYED_TASKS,
    ProfileField.CONFIDENT_TASKS,
    ProfileField.EVIDENCED_TASKS,
)


def quotable_answers(answers: Sequence[EvidenceItem]) -> list[EvidenceItem]:
    """The answers a strength may quote: in `ANSWER_FIELDS`, and quotable as a whole."""
    return [
        item
        for item in answers
        if item.field in ANSWER_FIELDS and accepted_quotation(item.text, item.text)
    ]


class DestinationKind(StrEnum):
    TARGET = "target"  # a target the person chose
    HORIZON = "horizon"  # on their horizon: joined to their role by shared essential skills


class ModelStrength(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination: str  # the destination's ref in the prompt ("d1")
    skill: str  # the skill's ref ("s4"), one listed for that destination
    quotation: str  # a few of the person's words, copied exactly


class StrengthOutput(BaseModel):
    """The model's whole output (sent to Meta as a strict JSON schema): none, or one."""

    model_config = ConfigDict(extra="forbid")

    strengths: list[ModelStrength]


class SkillRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    skill_id: uuid.UUID
    label: str


class DestinationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    concept_id: uuid.UUID
    title: str
    kind: DestinationKind
    skills: list[str]  # the refs of its essential skills, as far as the prompt carries them


class StrengthInput(BaseModel):
    """Everything a strength run sends the model: sealed into the run at submission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    format: Literal["careerwright.strength-input"] = INPUT_FORMAT
    prompt_version: str = PROMPT_VERSION
    turn_id: uuid.UUID  # the turn whose added answers it reads (never sent to the model)
    profile_version: int  # the version that turn's decision created (never sent)
    release: str  # the ESCO release the skills come from (never sent)
    answers: list[EvidenceItem]
    destinations: list[DestinationRecord]
    skills: list[SkillRecord]


class Destination(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: uuid.UUID
    title: str
    kind: DestinationKind


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    skill_id: uuid.UUID
    label: str


class Quotation(BaseModel):
    """A verified quotation of the person's answer, in the answer's own characters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answer_field: ProfileField
    text: str


class ProposedStrength(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    destination: Destination
    skill: Skill  # essential to the destination in ESCO
    quotation: Quotation


class OverlookedStrength(BaseModel):
    """A strength run's validated output (sealed)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    origin: ProposalOrigin
    prompt_version: str
    turn_id: uuid.UUID
    profile_version: int
    release: str
    strength: ProposedStrength | None  # None: the model found none in these answers


@dataclass(frozen=True)
class StrengthRequest:
    """A strength run and the turn it read: at most one per turn."""

    strength_id: uuid.UUID  # the run
    workspace_id: uuid.UUID
    turn_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime


class StrengthChoice(StrEnum):
    CONFIRMED = "confirmed"  # recorded as the person's own claim (self-reported)
    DECLINED = "declined"  # nothing about the skill is recorded


@dataclass(frozen=True)
class StrengthDecision:
    strength_id: uuid.UUID
    workspace_id: uuid.UUID
    decision: StrengthChoice
    evidence_id: uuid.UUID | None  # the self-report a confirmation recorded
    decided_by: uuid.UUID
    decided_at: datetime


def _echo(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= ECHO_CHARS else f"{text[:ECHO_CHARS]}…"


def _quotation(text: str, answers: Sequence[EvidenceItem]) -> Quotation | None:
    for item in answers:
        span = quoted_span(text, item.text)
        if span is not None and quotable(span):
            return Quotation(answer_field=item.field, text=span)
    return None


def check_strength(
    output: StrengthOutput, context: StrengthInput, origin: ProposalOrigin
) -> tuple[OverlookedStrength | None, list[str]]:
    """The validated proposal (which may hold none), or the problems that prevent it."""
    problems: list[str] = []
    if len(output.strengths) > 1:
        problems.append("strengths: at most one strength, or none")
    destinations = {d.ref: d for d in context.destinations}
    skills = {s.ref: s for s in context.skills}
    proposed: ProposedStrength | None = None
    for given in output.strengths[:1]:  # past the bound: counted above, not checked
        destination = destinations.get(given.destination)
        if destination is None:
            problems.append(f"destination: one of {', '.join(destinations)}")
        elif given.skill not in destination.skills:
            problems.append(
                f"skill: one of the essential skills listed for {destination.ref}, by its ref"
            )
        quotation = _quotation(given.quotation, context.answers)
        if quotation is None:
            problems.append(
                f"quotation: “{_echo(given.quotation)}” is not an exact quotation of whole words "
                "that say something, from the person's answers"
            )
        if destination is not None and given.skill in destination.skills and quotation:
            skill = skills[given.skill]
            proposed = ProposedStrength(
                destination=Destination(
                    concept_id=destination.concept_id,
                    title=destination.title,
                    kind=destination.kind,
                ),
                skill=Skill(skill_id=skill.skill_id, label=skill.label),
                quotation=quotation,
            )
    if problems:
        return None, problems
    return (
        OverlookedStrength(
            origin=origin,
            prompt_version=context.prompt_version,
            turn_id=context.turn_id,
            profile_version=context.profile_version,
            release=context.release,
            strength=proposed,
        ),
        [],
    )


def strength_repair(problems: list[str]) -> str:
    return repair_message(problems)


INSTRUCTIONS = """\
You look for one overlooked strength in what a person told Careerwright, a career-planning
service in England: something they said that shows one of the essential skills of a
destination they are considering, which they may not have noticed. Use only the person's
confirmed answers ("answers") and each destination's essential skills, as ESCO lists them.

If one answer clearly shows one of a destination's essential skills, return it as the one
item of "strengths": the destination's ref, the ref of one skill listed under that
destination, and a quotation: a few words copied exactly from that answer that show it. If
no answer clearly shows one, return an empty list. Never guess, and never write anything
else. Answer only with the JSON object.
"""


class PromptDestination(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    title: str
    essential_skills: dict[str, str]  # skill ref -> label


class PromptStrengthContext(BaseModel):
    """What the model reads: answer texts by field and the destinations, nothing else."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answers: dict[ProfileField, list[str]]
    destinations: list[PromptDestination]


def prompt_context(context: StrengthInput) -> PromptStrengthContext:
    answers: dict[ProfileField, list[str]] = {}
    for item in context.answers:
        answers.setdefault(item.field, []).append(item.text)
    labels = {s.ref: s.label for s in context.skills}
    return PromptStrengthContext(
        answers=answers,
        destinations=[
            PromptDestination(
                ref=d.ref, title=d.title, essential_skills={r: labels[r] for r in d.skills}
            )
            for d in context.destinations
        ],
    )


def render_prompt(context: StrengthInput) -> str:
    """The user prompt. The fixture model reads the same text."""
    payload = json.loads(prompt_context(context).model_dump_json())
    return CONTEXT_MARKER + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def prompt_bytes(context: StrengthInput) -> int:
    return len(INSTRUCTIONS.encode()) + len(render_prompt(context).encode())


@dataclass(frozen=True)
class DestinationSkills:
    concept_id: uuid.UUID
    title: str
    kind: DestinationKind
    skills: list[SkillRef]  # its essential skills not yet claimed, in ESCO's order


def build_input(
    *,
    turn_id: uuid.UUID,
    profile_version: int,
    release: str,
    answers: list[EvidenceItem],
    destinations: Sequence[DestinationSkills],
) -> StrengthInput:
    """The run's input: every answer a strength may quote (`quotable_answers`) whole, and as
    many of each destination's essential skills as fit. A skill several destinations share
    has one ref. Answers too long for every step are refused (`LIMIT_EXCEEDED`) before any
    run or reservation exists."""
    answers = quotable_answers(answers)
    for per_destination in SKILL_STEPS:
        refs: dict[uuid.UUID, SkillRecord] = {}
        records: list[DestinationRecord] = []
        for n, destination in enumerate(destinations, start=1):
            carried: list[str] = []
            for skill in destination.skills[:per_destination]:
                if skill.skill_id not in refs:
                    refs[skill.skill_id] = SkillRecord(
                        ref=f"s{len(refs) + 1}",
                        skill_id=skill.skill_id,
                        label=skill.preferred_label,
                    )
                carried.append(refs[skill.skill_id].ref)
            records.append(
                DestinationRecord(
                    ref=f"d{n}",
                    concept_id=destination.concept_id,
                    title=destination.title,
                    kind=destination.kind,
                    skills=carried,
                )
            )
        context = StrengthInput(
            turn_id=turn_id,
            profile_version=profile_version,
            release=release,
            answers=answers,
            destinations=records,
            skills=list(refs.values()),
        )
        if prompt_bytes(context) <= MAX_PROMPT_BYTES:
            return context
    raise CareerwrightError(
        ErrorCode.LIMIT_EXCEEDED,
        "Your answers are too long to look for a strength in. Shorten some, then try again.",
        stage=ErrorStage.CAPABILITY,
        details={"reason": "answers_too_long", "max_prompt_bytes": MAX_PROMPT_BYTES},
    )


def worst_case_nano_usd(model_id: str) -> int:
    """Per activity attempt: both requests at the input and output bounds."""
    per_request = worst_case_cost_nano_usd(
        model_id,
        max_input_tokens=MAX_PROMPT_BYTES
        + SCHEMA_ALLOWANCE_TOKENS
        + MAX_OUTPUT_TOKENS
        + REPAIR_ALLOWANCE_TOKENS,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_web_searches=0,
    )
    return MAX_REQUESTS * per_request


def fixture_strength(context: PromptStrengthContext) -> StrengthOutput:
    """The demo's scripted strength (`careerwright-fixture-strength-1`; demo workspaces only,
    labelled synthetic): the first answer, in order, that shares a content word with an
    essential skill of a destination, quoted whole; none when no answer does. It reads the
    same prompt a live model reads and passes the same check."""
    for texts in context.answers.values():
        for text in texts:
            if not accepted_quotation(text, text):
                continue
            words = content_words(text)
            for destination in context.destinations:
                for ref, label in destination.essential_skills.items():
                    if words & content_words(label):
                        return StrengthOutput(
                            strengths=[
                                ModelStrength(
                                    destination=destination.ref, skill=ref, quotation=text
                                )
                            ]
                        )
    return StrengthOutput(strengths=[])
