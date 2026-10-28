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

from nessa.catalogue.places import ENGLISH_CITIES
from nessa.errors import NessaError
from nessa.identity.model_registry import worst_case_cost_nano_usd
from nessa.money import Money
from nessa.profile.document import (
    FIELD_NAMES,
    FIELD_SPECS,
    FieldInput,
    FieldKind,
    FieldState,
    ProfileDocument,
    checked_input,
    input_type,
)
from nessa.profile.records import Basis

PROMPT_VERSION = "interview-turn-1"
INPUT_FORMAT: Literal["nessa.interview-turn-input"] = "nessa.interview-turn-input"
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


class AnsweredState(StrEnum):
    """A proposal answers a field; it never returns one to "not asked"."""

    PROVIDED = "provided"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


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

    format: Literal["nessa.interview-turn-input"] = INPUT_FORMAT
    prompt_version: str = PROMPT_VERSION
    profile_version: int
    profile: dict[ProfileField, ContextField]
    messages: list[ContextMessage]  # oldest first; the last is the current message
    replies: dict[str, str]  # message ref -> what Nessa replied to it, if it did


class ProposedChange(BaseModel):
    """One validated proposal, as stored and shown for review."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    change_id: str
    field: ProfileField
    state: AnsweredState
    value: Money | list[str] | float | str | None
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
    return value.model_dump() if isinstance(value, BaseModel) else value


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
    if spec.kind is FieldKind.LIST:
        if update.text is not None or not update.items:
            problems.append(f"{name}: a list field needs items and no text")
            return None
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
    return text


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
    anything else, including an answer with no value to quote, is shown as `inferred`."""
    if update.basis is not Basis.STATED or update.state is not AnsweredState.PROVIDED:
        return Basis.INFERRED
    if update.items is not None:
        kept = {_quotable(str(item)) for item in held} if isinstance(held, list) else set()
        values = [item for item in update.items if _quotable(item) not in kept]
    else:
        values = [update.text or ""]
    if values and all(_quoted(value, cited) for value in values):
        return Basis.STATED
    return Basis.INFERRED


def check_turn(
    output: InterviewTurnOutput, context: TurnInput, origin: ProposalOrigin
) -> tuple[InterviewProposal | None, list[str]]:
    """The validated proposal, or the problems that prevent it (never both)."""
    problems: list[str] = []
    if not _bounded(output.reply, MAX_REPLY):
        problems.append(f"reply: 1-{MAX_REPLY} characters")
    if output.next_question is not None and not _bounded(output.next_question, MAX_QUESTION):
        problems.append(f"next_question: 1-{MAX_QUESTION} characters, or null")
    if len(set(output.missing_critical_fields)) != len(output.missing_critical_fields):
        problems.append("missing_critical_fields: name each field once")
    if len(output.proposed_updates) > MAX_UPDATES:
        problems.append(f"proposed_updates: at most {MAX_UPDATES}")
    fields = [u.field for u in output.proposed_updates]
    if len(set(fields)) != len(fields):
        problems.append("proposed_updates: at most one update per field")
    refs = {m.ref: m.message_id for m in context.messages}
    texts = {m.ref: m.text for m in context.messages}
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
        except NessaError as error:
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
            next_question=output.next_question.strip() if output.next_question else None,
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
You are the interviewer in Nessa, a career-planning service for people in England.
Write a short, warm reply in British English and ask at most one question: the one that
most changes the next decision. Never ask again for something the profile already holds.

From the person's messages, propose updates to their profile fields. Propose only what a
message states, or clearly implies; mark implications as "inferred". Every update cites the
refs of the messages that support it (such as "m2"). Leave out fields the messages do not
address. Use "unknown", "skipped" or "prefer_not_to_say" when the person says so.

Field formats: text fields take "text"; list fields take "items", the complete list after
the change (keep the items the profile already holds that still apply); weekly_study_hours is a
number of hours per week as text, such as "6"; money is pounds as digits, such as "1500"
(direct_spend_cap: the most they would spend on the change in total; monthly_payment_cap:
the most in any one month). cities: only names from this list:
{", ".join(place.label for place in ENGLISH_CITIES)}.
enjoyed_tasks: what they enjoy; confident_tasks: what they believe they can do;
evidenced_tasks: what they have done and can show. Keep these three apart.

Do not ask about or infer health, personality types, aptitude or protected
characteristics. If the person describes a health condition, ask only which practical
adjustment would help. Never give a match percentage. Answer only with the JSON object.
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


def render_prompt(context: TurnInput) -> str:
    """The user prompt: the context as JSON. The fixture interviewer reads the same text."""
    prompt = PromptContext(
        profile=context.profile,
        messages=[PromptMessage(ref=m.ref, text=m.text) for m in context.messages],
        your_earlier_replies=context.replies,
        current_message=context.messages[-1].ref,
    )
    payload = json.loads(prompt.model_dump_json())
    return CONTEXT_MARKER + json.dumps(payload, ensure_ascii=False, sort_keys=True)


def prompt_bytes(context: TurnInput) -> int:
    return len(INSTRUCTIONS.encode()) + len(render_prompt(context).encode())


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
