"""The InterviewTurn contract (spec section 4 "Schema governance", section 18).

One interview turn sends the model the minimum profile subset and the person's recent
messages, and gets back a bounded `InterviewTurnOutput`: a reply, proposed field updates
that cite the supporting messages, the next question, missing critical fields and whether
the proposals are ready for review. The model proposes; nothing here changes the profile.

`check_turn` validates the output against the turn's context, deterministically: only
profile fields can be named (keys, secrets and plan commitments are not profile fields, so
no output can reach them; PROF-06), every update cites at least one of the person's
messages, values are parsed by the field's kind with integer money, cities must be on the
English list, and list bounds hold. What it returns is the stored `InterviewProposal`, with
server-assigned change IDs, message IDs in place of prompt labels, each change marked if it
is a hard constraint that only the person's explicit confirmation can establish (PROF-04),
and a basis the server verified: the model's "stated" is kept only when the value appears
in the messages it cites, otherwise the change is shown as "inferred" (PROF-01). Problems
become the text of the one bounded repair request (PROF-05).

Structural bounds are checked here rather than as schema keywords, so the JSON schema sent
to Meta stays within strict mode (as for the connection check).
"""

import json
import re
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from careerwright.catalogue.places import ENGLISH_CITIES
from careerwright.errors import CareerwrightError
from careerwright.identity.model_registry import worst_case_cost_nano_usd
from careerwright.money import Money
from careerwright.profile.document import (
    FIELD_NAMES,
    FIELD_SPECS,
    FieldInput,
    FieldKind,
    FieldState,
    PayPeriod,
    ProfileDocument,
    QualificationAnswer,
    SalaryFloor,
    checked_input,
    input_type,
)
from careerwright.profile.records import Basis, ConversationMode, EntryMode
from careerwright.profile.safety import (
    SUPPORT_TURN_INSTRUCTION,
    has_risk_stem,
    inferred_sensitive_terms,
    recorded_health_terms,
)

# Version 2 (Task 6): the person's entry and conversation mode, the work-style field, and
# the support and inference rules. Version 3: one question, in next_question only. Version 4:
# the smaller-step instruction for a turn whose message triggers the support screen. Version 5
# (Task 6f): someone may not have had a job yet (the `no_job_yet` answer), what the person is
# doing now and their qualifications, and "their next step" for "the change".
PROMPT_VERSION = "interview-turn-5"
INPUT_FORMAT: Literal["careerwright.interview-turn-input"] = "careerwright.interview-turn-input"
MAX_MESSAGE = 2_000
MAX_REPLY = 1_200
MAX_QUESTION = 300
MAX_REASON = 300
MAX_UPDATES = len(FIELD_NAMES)
MAX_REFS = 5
HISTORY_MESSAGES = 6  # the current message plus up to five earlier ones
# Bounds for the spend reservation (bytes bound tokens for byte-level BPE tokenizers).
MAX_PROMPT_BYTES = 8_500  # instructions plus the rendered context
SCHEMA_ALLOWANCE_TOKENS = 2_500  # the output JSON schema Meta receives
MAX_OUTPUT_TOKENS = 1_500
REPAIR_ALLOWANCE_TOKENS = 2_000  # validation problems sent back with the repair request
MAX_REQUESTS = 2  # the first request and at most one repair (bounded validation repair)
MONEY_PATTERN = re.compile(r"^[0-9]{1,9}(\.[0-9]{1,2})?$")
HOURS_PATTERN = re.compile(r"^[0-9]{1,3}(\.[0-9]{1,2})?$")
SALARY_PATTERN = re.compile(
    r"^([0-9]{1,9}(?:\.[0-9]{1,2})?)(?:\s+(?:per|a|an|each)\s+(year|month|week|hour))?$"
)
# How a person names each pay period, for checking that a "stated" floor's period is theirs.
_PERIOD_WORDS = {
    period: re.compile(rf"\b(?:(?:an?|per|each|every) {period}|{adverb})\b", re.IGNORECASE)
    for period, adverb in (
        (PayPeriod.YEAR, r"yearly|annual(?:ly)?|per annum"),
        (PayPeriod.MONTH, r"monthly"),
        (PayPeriod.WEEK, r"weekly"),
        (PayPeriod.HOUR, r"hourly"),
    )
}


class ProfileField(StrEnum):
    """The only names a proposal may use: the profile's own fields."""

    PREFERRED_NAME = "preferred_name"
    CURRENT_ROLE = "current_role"
    CITIES = "cities"
    TARGET_TITLES = "target_titles"
    WEEKLY_STUDY_HOURS = "weekly_study_hours"
    DIRECT_SPEND_CAP = "direct_spend_cap"
    MONTHLY_PAYMENT_CAP = "monthly_payment_cap"
    ENJOYED_TASKS = "enjoyed_tasks"
    CONFIDENT_TASKS = "confident_tasks"
    EVIDENCED_TASKS = "evidenced_tasks"
    WORK_STYLE = "work_style"
    MINIMUM_SALARY = "minimum_salary"
    WORK_STATUS = "work_status"
    QUALIFICATIONS = "qualifications"
    DISLIKED_TASKS = "disliked_tasks"


class AnsweredState(StrEnum):
    """A proposal answers a field; it never returns one to "not asked"."""

    PROVIDED = "provided"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    NO_JOB_YET = "no_job_yet"  # the current role only (`document.checked_input`)


class ModelUpdate(BaseModel):
    """One proposed field update, as the model writes it."""

    model_config = ConfigDict(extra="forbid")

    field: ProfileField
    state: AnsweredState
    text: str | None  # text fields; hours and money as a plain decimal number
    items: list[str] | None  # list fields
    basis: Basis
    message_refs: list[str]
    reason: str


class InterviewTurnOutput(BaseModel):
    """The model's whole output for one turn (sent to Meta as a strict JSON schema)."""

    model_config = ConfigDict(extra="forbid")

    reply: str
    proposed_updates: list[ModelUpdate]
    next_question: str | None
    missing_critical_fields: list[ProfileField]
    ready_for_review: bool


class ContextMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str  # "m1", "m2", ...: what the model cites
    message_id: uuid.UUID
    text: str
    sent_at: datetime


class ContextField(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: FieldState
    value: object = None


class TurnInput(BaseModel):
    """Everything one turn sends the model: sealed into the run at submission, so the worker
    never reads profile or conversation tables (ADR 0004 decision 5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    format: Literal["careerwright.interview-turn-input"] = INPUT_FORMAT
    prompt_version: str = PROMPT_VERSION
    profile_version: int
    profile: dict[ProfileField, ContextField]
    messages: list[ContextMessage]  # oldest first; the last is the current message
    replies: dict[str, str]  # message ref -> what Careerwright replied to it, if it did
    # The person's interview preferences (defaults keep inputs sealed before them readable).
    entry_mode: EntryMode | None = None
    conversation_mode: ConversationMode = ConversationMode.PRACTICAL


class ProposedChange(BaseModel):
    """One validated proposal, as stored and shown for review."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    change_id: str
    field: ProfileField
    state: AnsweredState
    value: SalaryFloor | Money | list[QualificationAnswer] | list[str] | float | str | None
    basis: Basis
    message_ids: list[uuid.UUID]
    reason: str
    hard_constraint: bool

    def field_input(self) -> FieldInput:
        return input_type(self.field.value).model_validate(
            {"state": self.state.value, "value": _plain(self.value)}
        )


class ProposalOrigin(StrEnum):
    MODEL = "model"
    FIXTURE = "fixture"  # the deterministic demo interviewer: synthetic, never a live answer


class InterviewProposal(BaseModel):
    """A turn's validated output: the run output that is sealed, and what review shows."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    origin: ProposalOrigin
    prompt_version: str
    profile_version: int
    reply: str
    changes: list[ProposedChange]
    next_question: str | None
    missing_critical_fields: list[ProfileField]
    ready_for_review: bool


def _plain(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value.value if isinstance(value, StrEnum) else value


def _bounded(text: str, limit: int) -> bool:
    return 1 <= len(text.strip()) <= limit


def _money(text: str) -> Money | None:
    if not MONEY_PATTERN.match(text):
        return None
    try:
        pounds = Decimal(text)
    except InvalidOperation:
        return None
    return Money(minor_units=int(pounds * 100), currency="GBP")  # GBP: 2 minor digits


def _hours(text: str) -> float | None:
    if not HOURS_PATTERN.match(text) or Decimal(text) > 168:
        return None
    return float(Decimal(text))


def _value(update: ModelUpdate, problems: list[str]) -> object:
    name = update.field.value
    spec = FIELD_SPECS[name]
    if update.state is not AnsweredState.PROVIDED:
        if update.text is not None or update.items is not None:
            problems.append(f"{name}: a {update.state.value} answer has no text or items")
        return None
    if spec.kind in (FieldKind.LIST, FieldKind.QUALIFICATIONS):
        if update.text is not None or not update.items:
            problems.append(f"{name}: a list field needs items and no text")
            return None
        if spec.kind is FieldKind.QUALIFICATIONS:
            return _qualifications(update.items, name, problems)
        return [item.strip() for item in update.items]
    if update.items is not None or update.text is None:
        problems.append(f"{name}: this field needs text and no items")
        return None
    text = update.text.strip()
    if spec.kind is FieldKind.MONEY:
        money = _money(text)
        if money is None:
            problems.append(f"{name}: give pounds as digits, such as 1500 or 1500.50")
        return money
    if spec.kind is FieldKind.HOURS:
        hours = _hours(text)
        if hours is None:
            problems.append(f"{name}: give weekly hours as a number from 0 to 168")
        return hours
    if spec.kind is FieldKind.SALARY:
        salary = _salary(text)
        if salary is None:
            problems.append(
                f"{name}: give gross pounds above 0 and the period, such as 28000 per year "
                "(no floor is unknown or skipped)"
            )
        return salary
    return text


_QUALIFICATION_ITEM = re.compile(r"^(achieved|expected):\s*(\S.*)$", re.IGNORECASE)


def _qualification_parts(item: str) -> tuple[str, str] | None:
    """A qualification as the model writes it, "achieved: GCSE maths" or "expected: A-level
    biology": its status and its name, or None for any other shape."""
    match = _QUALIFICATION_ITEM.match(item.strip())
    return None if match is None else (match.group(1).casefold(), match.group(2).strip())


def _qualifications(items: list[str], name: str, problems: list[str]) -> object:
    parts = [_qualification_parts(item) for item in items]
    if any(part is None for part in parts):
        problems.append(f'{name}: give each as "achieved: name" or "expected: name"')
        return None
    return [{"name": text, "status": status} for status, text in filter(None, parts)]


def _salary(text: str) -> SalaryFloor | None:
    """Gross pounds and the period as given; a year unless the person said otherwise."""
    match = SALARY_PATTERN.match(text)
    money = _money(match.group(1)) if match else None
    if match is None or money is None or money.minor_units == 0:
        return None
    return SalaryFloor(amount=money, period=PayPeriod(match.group(2) or PayPeriod.YEAR.value))


_DIGIT_GROUPING = re.compile(r"(?<=[0-9]),(?=[0-9]{3}\b)")


def _quotable(text: str) -> str:
    """Text as a stated value is compared: case, spacing and digit grouping aside."""
    return " ".join(_DIGIT_GROUPING.sub("", text).casefold().split())


def _quoted(value: str, texts: list[str]) -> bool:
    needle = _quotable(value)
    pattern = re.compile(rf"(?<!\w){re.escape(needle)}(?!\w)")
    return bool(needle) and any(pattern.search(_quotable(text)) for text in texts)


def _basis(update: ModelUpdate, cited: list[str], held: object) -> Basis:
    """`stated` only when the model claims it and every new value the update proposes
    appears in the messages it cites (items the profile already holds need no quote);
    anything else, including an answer with no value to quote, is shown as `inferred`. A
    qualification's status and a work status are always readings of their words, never their
    words (Task 6f review I1), so both are always `inferred`."""
    if update.basis is not Basis.STATED or update.state is not AnsweredState.PROVIDED:
        return Basis.INFERRED
    if FIELD_SPECS[update.field.value].kind in (FieldKind.QUALIFICATIONS, FieldKind.WORK_STATUS):
        return Basis.INFERRED
    if update.items is not None:
        kept = {_quotable(str(item)) for item in held} if isinstance(held, list) else set()
        values = [item for item in update.items if _quotable(item) not in kept]
    elif FIELD_SPECS[update.field.value].kind is FieldKind.SALARY:
        match = SALARY_PATTERN.match(update.text or "")
        period = PayPeriod(match.group(2)) if match and match.group(2) else None
        # The period is part of the value: a defaulted or different one is not their words.
        if period is None or not any(_PERIOD_WORDS[period].search(text) for text in cited):
            return Basis.INFERRED
        values = [match.group(1) if match else ""]
    else:
        values = [update.text or ""]
    if values and all(_quoted(value, cited) for value in values):
        return Basis.STATED
    return Basis.INFERRED


def _inference_problems(output: InterviewTurnOutput, person: list[str]) -> list[str]:
    """The support and inference rules (`careerwright.profile.safety`): nothing the person never
    mentioned about health, diagnoses, personality types or percentages, and no health
    condition recorded in a career field."""
    values = {
        update.field.value: [update.text or "", *(update.items or [])]
        for update in output.proposed_updates
    }
    written = [output.reply, output.next_question or ""]
    written += [update.reason for update in output.proposed_updates]
    written += [value for field_values in values.values() for value in field_values]
    problems = []
    inferred = inferred_sensitive_terms(written, person)
    if inferred:
        problems.append(
            "do not suggest a health condition, diagnosis, personality type or percentage the "
            f"person did not mention ({', '.join(inferred)})"
        )
    for name, field_values in values.items():
        if recorded_health_terms(field_values):
            problems.append(
                f"{name}: health conditions are not recorded in career fields; ask which "
                "adjustment would help instead"
            )
    return problems


def check_turn(
    output: InterviewTurnOutput, context: TurnInput, origin: ProposalOrigin
) -> tuple[InterviewProposal | None, list[str]]:
    """The validated proposal, or the problems that prevent it (never both). On a turn whose
    message triggers the support screen, any next question is dropped, never repaired: that
    turn asks no career question (`careerwright.profile.safety`; recomputed, never stored)."""
    problems: list[str] = []
    question = None if has_risk_stem(context.messages[-1].text) else output.next_question
    if not _bounded(output.reply, MAX_REPLY):
        problems.append(f"reply: 1-{MAX_REPLY} characters")
    if question is not None and not _bounded(question, MAX_QUESTION):
        problems.append(f"next_question: 1-{MAX_QUESTION} characters, or null")
    # One question at a time (PROF-08), asked once: the reply and the question are shown apart,
    # so a question in the reply is refused only beside a next question (with none, there is
    # nothing to repeat, and a rhetorical "?" is not worth a paid repair).
    if question is not None:
        if "?" in output.reply:
            problems.append("reply: no question here; ask the one question only in next_question")
        if question.count("?") > 1:
            problems.append("next_question: one question only")
    if len(set(output.missing_critical_fields)) != len(output.missing_critical_fields):
        problems.append("missing_critical_fields: name each field once")
    if len(output.proposed_updates) > MAX_UPDATES:
        problems.append(f"proposed_updates: at most {MAX_UPDATES}")
    fields = [u.field for u in output.proposed_updates]
    if len(set(fields)) != len(fields):
        problems.append("proposed_updates: at most one update per field")
    refs = {m.ref: m.message_id for m in context.messages}
    texts = {m.ref: m.text for m in context.messages}
    problems += _inference_problems(output, list(texts.values()))
    changes: list[ProposedChange] = []
    for index, update in enumerate(output.proposed_updates, start=1):
        name = update.field.value
        cited = list(dict.fromkeys(update.message_refs))
        if not cited or len(cited) > MAX_REFS or any(ref not in refs for ref in cited):
            problems.append(f"{name}: cite 1-{MAX_REFS} of the message refs {sorted(refs)}")
            continue
        if not _bounded(update.reason, MAX_REASON):
            problems.append(f"{name}: reason 1-{MAX_REASON} characters")
        value = _value(update, problems)
        try:
            typed = input_type(name).model_validate(
                {"state": update.state.value, "value": _plain(value)}
            )
            checked = checked_input(name, typed)
        except ValidationError:
            problems.append(f"{name}: the value is not valid for this field")
            continue
        except CareerwrightError as error:
            problems.append(f"{name}: {error.message}")
            continue
        changes.append(
            ProposedChange(
                change_id=f"c{index}",
                field=update.field,
                state=update.state,
                value=_plain(checked.value),
                basis=_basis(
                    update, [texts[ref] for ref in cited], context.profile[update.field].value
                ),
                message_ids=[refs[ref] for ref in cited],
                reason=update.reason.strip(),
                hard_constraint=FIELD_SPECS[name].hard_constraint,
            )
        )
    if problems:
        return None, problems
    return (
        InterviewProposal(
            origin=origin,
            prompt_version=context.prompt_version,
            profile_version=context.profile_version,
            reply=output.reply.strip(),
            changes=changes,
            next_question=question.strip() if question else None,
            missing_critical_fields=output.missing_critical_fields,
            ready_for_review=output.ready_for_review,
        ),
        [],
    )


def context_profile(document: ProfileDocument) -> dict[ProfileField, ContextField]:
    """The minimum subset the model needs: each field's state and value, except the
    preferred name's value (it plays no part in the interview), and no source IDs."""
    subset: dict[ProfileField, ContextField] = {}
    for name in FIELD_NAMES:
        field = getattr(document, name)
        value = None if name == "preferred_name" else _plain(field.value)
        subset[ProfileField(name)] = ContextField(state=field.state, value=value)
    return subset


INSTRUCTIONS = f"""\
You are the interviewer in Careerwright, a career-planning service for people in England.
Write a short, warm reply in British English, with no question in it. Ask at most one
question, only in next_question: the one that most changes the next decision. Never ask
again for something the profile already holds.

From the person's messages, propose updates to their profile fields. Propose only what a
message states, or clearly implies; mark implications as "inferred". Every update cites the
refs of the messages that support it (such as "m2"). Leave out fields the messages do not
address. Use "unknown", "skipped" or "prefer_not_to_say" when the person says so, and for
current_role only, "no_job_yet" when they say they haven't had a job yet (never a job title).

Field formats: text fields take "text"; list fields take "items", the complete list after
the update (keep the items the profile already holds that still apply); weekly_study_hours is a
number of hours per week as text, such as "6"; money is pounds as digits, such as "1500"
(direct_spend_cap: the most they would spend on their next step in total; monthly_payment_cap:
the most in any one month). minimum_salary: the lowest gross pay they would accept, as
pounds and the period they gave, such as "28000 per year" or "12.50 per hour" (a year
unless they say otherwise; never convert it). cities: only names from this list:
{", ".join(place.label for place in ENGLISH_CITIES)}.
enjoyed_tasks: what they enjoy; confident_tasks: what they believe they can do;
evidenced_tasks: what they have done and can show. Keep these three apart. work_style:
how they say they like to work (optional; never ask for it twice, accept a skip).
work_status: what they are doing now, as text, one of working, in_education_or_training,
looking_for_work, caring, other. qualifications: items such as "achieved: GCSE maths" or
"expected: A-level biology" (expected while they are taking it or awaiting the result). Both
are optional: ask for each at most once and accept a skip. Never ask their age.
Someone may not have had a job yet: ask about school or college, volunteering, caring,
clubs and hobbies; never treat no job as a gap.

"entry" is how the person chose to start. "sure": they know their direction; confirm the
target role and the level they aim for, then the practical limits, and do not explore
interests or work style unless they raise them. "unsure": they want to explore; before
naming any career, ask about kinds of tasks they enjoy or find draining. null: not chosen.
"mode" is the tone they chose. "practical": brief and concrete. "gentle": acknowledge
uncertainty kindly and offer small steps. "challenge": question one assumption, politely.
If they say they feel overwhelmed, acknowledge it in one sentence and offer one smaller
next step. Never invent a past income, a baseline or a budget they did not give.

Do not ask about or infer health, diagnoses, personality types, aptitude or protected
characteristics. If the person describes a health condition, ask only which practical
adjustment would help, and never record the condition in a field. Never give a match
percentage. Answer only with the JSON object.
"""


CONTEXT_MARKER = "Context (JSON):\n"


class PromptMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    text: str


class PromptContext(BaseModel):
    """What the model reads: no IDs, no sources, no timestamps."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: dict[ProfileField, ContextField]
    messages: list[PromptMessage]
    your_earlier_replies: dict[str, str]
    current_message: str
    entry: EntryMode | None = None
    mode: ConversationMode = ConversationMode.PRACTICAL


def render_prompt(context: TurnInput) -> str:
    """The user prompt: the context as JSON. The fixture interviewer reads the same text."""
    prompt = PromptContext(
        profile=context.profile,
        messages=[PromptMessage(ref=m.ref, text=m.text) for m in context.messages],
        your_earlier_replies=context.replies,
        current_message=context.messages[-1].ref,
        entry=context.entry_mode,
        mode=context.conversation_mode,
    )
    payload = json.loads(prompt.model_dump_json())
    return CONTEXT_MARKER + json.dumps(payload, ensure_ascii=False, sort_keys=True)


def instructions(context: TurnInput) -> str:
    """The turn's instructions: with the smaller-step instruction when, and only when, the
    current message triggers the support screen (`careerwright.profile.safety`). Recomputed from the
    message for every request, so nothing about the screen is sealed or stored."""
    if has_risk_stem(context.messages[-1].text):
        return f"{INSTRUCTIONS}\n{SUPPORT_TURN_INSTRUCTION}\n"
    return INSTRUCTIONS


def prompt_bytes(context: TurnInput) -> int:
    return len(instructions(context).encode()) + len(render_prompt(context).encode())


def worst_case_nano_usd(model_id: str) -> int:
    """Per activity attempt: every request at the input bound (the repair request also
    carries the first output and the problems) and the output bound."""
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
