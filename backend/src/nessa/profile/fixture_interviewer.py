"""The deterministic demo interviewer (plan section 2: demo mode uses deterministic model
fixtures; section 3: a fixture adapter keeps the live adapter's failure and provenance
contract, with its synthetic origin retained).

It reads the same prompt context a live model reads and answers the same InterviewTurn
schema, from a few fixed patterns in the person's latest message: English city names from
the list, "N hours", "£N" (a monthly amount if the sentence says month), "I am a ...",
"I enjoy ...", and "rather not say" about money. Its output passes the same validation and
is stored with origin `fixture`; its reply says it is the demo interviewer. It is a
stand-in for exercising the product offline, not an evaluation of interviewing.
"""

import re

from nessa.catalogue.places import ENGLISH_CITIES
from nessa.profile.document import MAX_CITIES, MAX_TASKS, FieldState
from nessa.profile.interview import (
    AnsweredState,
    InterviewTurnOutput,
    ModelUpdate,
    ProfileField,
    PromptContext,
)
from nessa.profile.records import Basis, EntryMode

REPLY_PREFIX = "Demo interviewer (synthetic): "
# Spec section 3, early value: current work, weekly availability, budget and work area.
CRITICAL = (
    ProfileField.CURRENT_ROLE,
    ProfileField.CITIES,
    ProfileField.WEEKLY_STUDY_HOURS,
    ProfileField.DIRECT_SPEND_CAP,
)
QUESTIONS = {
    ProfileField.CURRENT_ROLE: "What do you do now, or what did you do most recently?",
    ProfileField.CITIES: "Which English cities could you work in? Name up to three.",
    ProfileField.WEEKLY_STUDY_HOURS: "About how many hours a week could you give to learning?",
    ProfileField.DIRECT_SPEND_CAP: (
        "What is the most you would spend on this change in total? You can say you'd rather "
        "not say."
    ),
    ProfileField.TARGET_TITLES: "Do you have a role in mind, or would you like to explore?",
}
SURE_QUESTION = "Which role are you aiming for, and at what level?"
UNSURE_QUESTION = "What would you most like to be different about your working life?"
_HOURS = re.compile(r"\b([0-9]{1,3}(?:\.[0-9]{1,2})?)\s*(?:hours?|hrs?)\b", re.IGNORECASE)
# At most nine whole-pound digits, the bound `interview.MONEY_PATTERN` accepts; a longer
# amount matches nothing, so the fixture never proposes a value the check would refuse.
_MONEY = re.compile(
    r"£\s?([0-9]{1,3}(?:,[0-9]{3}){1,2}|[0-9]{1,9})(?![0-9]|,[0-9])(?:\.([0-9]{1,2}))?"
)
_MONTH = re.compile(r"\b(?:a|per|each|every) month\b|\bmonthly\b", re.IGNORECASE)
# An amount in a sentence about pay is a salary floor, not a spending limit.
_PAY = re.compile(r"\b(?:salary|earn(?:ing)?|paid|wage|a year|per year|annual(?:ly)?)\b", re.I)
_HOURLY = re.compile(r"\b(?:an|per|a) hour\b|\bhourly\b", re.IGNORECASE)
_ROLE = re.compile(
    r"\bI(?:'m| am| work as) (?:a|an) ([A-Za-z][A-Za-z -]{2,60}?)(?=[.,;!?]| in | at | and |$)"
)
_ENJOY = re.compile(r"\bI (?:really )?(?:enjoy|love|like) ([^.,;!?]{3,80})", re.IGNORECASE)
_DECLINE = re.compile(r"\b(?:rather not say|prefer not to say)\b", re.IGNORECASE)
_MONEY_WORDS = re.compile(r"\b(?:budget|spend|money|afford|pay)\b", re.IGNORECASE)


def _sentence(text: str, start: int) -> str:
    begin = max(text.rfind(mark, 0, start) for mark in ".!?") + 1
    ends = [i for i in (text.find(mark, start) for mark in ".!?") if i != -1]
    return text[begin : min(ends) if ends else len(text)]


def _cities(text: str) -> list[str]:
    found: list[tuple[int, str]] = []
    for place in ENGLISH_CITIES:
        for name in (place.label, *place.aliases):
            match = re.search(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", text)
            if match:
                found.append((match.start(), place.label))
                break
    return [label for _, label in sorted(found)]


def _listed(context: PromptContext, field: ProfileField) -> list[str]:
    current = context.profile[field]
    if current.state is FieldState.PROVIDED and isinstance(current.value, list):
        return [str(item) for item in current.value]
    return []


def _update(
    field: ProfileField,
    ref: str,
    reason: str,
    *,
    text: str | None = None,
    items: list[str] | None = None,
    state: AnsweredState = AnsweredState.PROVIDED,
    basis: Basis = Basis.STATED,
) -> ModelUpdate:
    return ModelUpdate(
        field=field,
        state=state,
        text=text,
        items=items,
        basis=basis,
        message_refs=[ref],
        reason=reason,
    )


def _proposals(context: PromptContext, ref: str, text: str) -> list[ModelUpdate]:
    updates: list[ModelUpdate] = []
    named = _cities(text)
    merged = list(dict.fromkeys(_listed(context, ProfileField.CITIES) + named))
    if named and len(merged) <= MAX_CITIES:
        updates.append(_update(ProfileField.CITIES, ref, "You named these cities.", items=merged))
    if (hours := _HOURS.search(text)) and float(hours.group(1)) <= 168:
        updates.append(
            _update(
                ProfileField.WEEKLY_STUDY_HOURS,
                ref,
                "You gave a number of hours a week.",
                text=hours.group(1),
            )
        )
    if money := _MONEY.search(text):
        pounds = money.group(1).replace(",", "") + (f".{money.group(2)}" if money.group(2) else "")
        sentence = _sentence(text, money.start())
        monthly = _MONTH.search(sentence) is not None
        if _PAY.search(sentence) or _HOURLY.search(sentence):
            period = "hour" if _HOURLY.search(sentence) else "month" if monthly else "year"
            updates.append(
                _update(
                    ProfileField.MINIMUM_SALARY,
                    ref,
                    "You mentioned this as the least you would earn.",
                    text=f"{pounds} per {period}",
                    basis=Basis.INFERRED,
                )
            )
        else:
            updates.append(
                _update(
                    ProfileField.MONTHLY_PAYMENT_CAP if monthly else ProfileField.DIRECT_SPEND_CAP,
                    ref,
                    "You mentioned this amount as a limit.",
                    text=pounds,
                    basis=Basis.INFERRED,
                )
            )
    elif _DECLINE.search(text) and _MONEY_WORDS.search(text):
        updates.append(
            _update(
                ProfileField.DIRECT_SPEND_CAP,
                ref,
                "You said you would rather not say.",
                state=AnsweredState.PREFER_NOT_TO_SAY,
            )
        )
    if role := _ROLE.search(text):
        updates.append(
            _update(ProfileField.CURRENT_ROLE, ref, "You said what you do.", text=role.group(1))
        )
    if enjoy := _ENJOY.search(text):
        tasks = list(dict.fromkeys([*_listed(context, ProfileField.ENJOYED_TASKS), enjoy.group(1)]))
        if len(tasks) <= MAX_TASKS:
            updates.append(
                _update(
                    ProfileField.ENJOYED_TASKS,
                    ref,
                    "You said you enjoy this.",
                    items=[task.strip() for task in tasks],
                )
            )
    return updates


def _nothing_known(context: PromptContext) -> bool:
    return all(field.state is FieldState.UNASKED for field in context.profile.values())


def fixture_turn(context: PromptContext) -> InterviewTurnOutput:
    current = next(m for m in context.messages if m.ref == context.current_message)
    updates = _proposals(context, current.ref, current.text)
    answered = {u.field for u in updates}
    missing = [
        field
        for field in CRITICAL
        if field not in answered and context.profile[field].state is FieldState.UNASKED
    ]
    target_unasked = (
        ProfileField.TARGET_TITLES not in answered
        and context.profile[ProfileField.TARGET_TITLES].state is FieldState.UNASKED
    )
    # The entry the person chose leads: a sure person confirms the target first; an unsure
    # person starts from what they want to change, before any practical question.
    question: str | None
    if context.entry is EntryMode.SURE and target_unasked:
        question = SURE_QUESTION
    elif context.entry is EntryMode.UNSURE and not updates and _nothing_known(context):
        question = UNSURE_QUESTION
    elif missing:
        question = QUESTIONS[missing[0]]
    elif target_unasked:
        question = QUESTIONS[ProfileField.TARGET_TITLES]
    else:
        question = None
    noted = f"I noted {len(updates)} thing{'s' if len(updates) != 1 else ''} for you to review."
    reply = (
        REPLY_PREFIX + (noted if updates else "Thank you.") + (f" {question}" if question else "")
    )
    return InterviewTurnOutput(
        reply=reply,
        proposed_updates=updates,
        next_question=question,
        missing_critical_fields=missing,
        ready_for_review=bool(updates),
    )
