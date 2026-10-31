"""The deterministic demo interviewer (plan section 2: demo mode uses deterministic model
fixtures; section 3: a fixture adapter keeps the live adapter's failure and provenance
contract, with its synthetic origin retained).

It reads the same prompt context a live model reads and answers the same InterviewTurn
schema, from a few fixed patterns in the person's latest message: English city names from
the list, "N hours", "£N" (a monthly amount if the sentence says month), "I am a ...",
"I enjoy ...", "I want to be a ..." (a target), "rather not say" about money, and a message
that is only "Skip", "Unknown" or "Prefer not to say", which answers the question in front of
the person. Its output passes the same validation and is stored with origin `fixture`; its
reply says it is the demo interviewer. It is a stand-in for exercising the product offline,
not an evaluation of interviewing.

It never asks the same question twice in a row once it is answered (Task W2E, the audit's F1):
the question in front of the person is the opening their entry asked, or the one it asked
after their last answered message, recomputed from what that message said (its fixed
patterns) and the answers saved since. A question it couldn't note an answer to is asked
again, with the way on the web shows there: an example reply or Skip, or at the role question
its two buttons. Once nothing is left to ask, any message gets what to do next. The open
question an unsure person starts with is only ever the opening: any reply moves on to the
first practical question.
"""

import re
from dataclasses import dataclass

from careerwright.catalogue.places import ENGLISH_CITIES
from careerwright.profile.document import MAX_CITIES, MAX_TARGETS, MAX_TASKS, FieldState
from careerwright.profile.interview import (
    AnsweredState,
    InterviewTurnOutput,
    ModelUpdate,
    ProfileField,
    PromptContext,
)
from careerwright.profile.records import Basis, EntryMode

REPLY_PREFIX = "Demo interviewer (synthetic): "
SMALLER_STEP_REPLY = (
    "Thank you for telling me. There's no rush: you can pause here, or come back to this later."
)
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
ROLE_QUESTION = QUESTIONS[ProfileField.TARGET_TITLES]
SURE_QUESTION = "Which role are you aiming for, and at what level?"
UNSURE_QUESTION = "What would you most like to be different about your working life?"
_HOURS = re.compile(r"\b([0-9]{1,3}(?:\.[0-9]{1,2})?)\s*(?:hours?|hrs?)\b", re.IGNORECASE)
# At most nine whole-pound digits, the bound `interview.MONEY_PATTERN` accepts; a longer
# amount matches nothing, so the fixture never proposes a value the check would refuse.
_MONEY = re.compile(
    r"£\s?([0-9]{1,3}(?:,[0-9]{3}){1,2}|[0-9]{1,9})(?![0-9]|,[0-9])(?:\.([0-9]{1,2}))?"
)
_MONTH = re.compile(r"\b(?:a|per|each|every) month\b|\bmonthly\b", re.IGNORECASE)
# An amount in a sentence about pay is a salary floor, not a spending limit; a sentence
# about spending ("£1,500 a year on courses") is a limit even with a period in it.
_PAY = re.compile(r"\b(?:salary|earn(?:ing)?|paid|wages?|work for)\b", re.IGNORECASE)
_SPEND = re.compile(r"\b(?:spend|spending|budget|afford|cost|fees?|course|courses)\b", re.I)
_HOURLY = re.compile(r"\b(?:an|per|a) hour\b|\bhourly\b", re.IGNORECASE)
_WEEKLY = re.compile(r"\b(?:a|per|each|every) week\b|\bweekly\b", re.IGNORECASE)
_ROLE = re.compile(
    r"\bI(?:'m| am| work as) (?:a|an) ([A-Za-z][A-Za-z -]{2,60}?)(?=[.,;!?]| in | at | and |$)"
)
_ENJOY = re.compile(r"\bI (?:really )?(?:enjoy|love|like) ([^.,;!?]{3,80})", re.IGNORECASE)
_TARGET = re.compile(
    r"\bI want to be (?:a|an) ([A-Za-z][A-Za-z -]{2,60}?)(?=[.,;!?]| in | at | and |$)",
    re.IGNORECASE,
)
_DECLINE = re.compile(r"\b(?:rather not say|prefer not to say)\b", re.IGNORECASE)
_MONEY_WORDS = re.compile(r"\b(?:budget|spend|money|afford|pay)\b", re.IGNORECASE)
# The whole message is one of the answers the opening hint names (STATE-08).
_ANSWER_WORD = re.compile(r"(skip|unknown|prefer not to say)[.!]?", re.IGNORECASE)
_ANSWER_STATE = {
    "skip": (AnsweredState.SKIPPED, "You said to skip this question."),
    "unknown": (AnsweredState.UNKNOWN, "You said you don't know."),
    "prefer not to say": (AnsweredState.PREFER_NOT_TO_SAY, "You said you would rather not say."),
}
# The way on names only what the web shows (app review I1): example replies under a demo
# question; "Show me suggestions" and "Name a role" (`ROLE_OR_EXPLORE` in the web's
# vocabulary) at the role question of a person who isn't sure; and after the last question,
# with nothing in front for Skip to answer, the views that are always there.
COULDNT_NOTE = "Thank you. I couldn't note anything from that. Tap an example reply, or say Skip."
COULDNT_NOTE_ROLE = (
    "Thank you. I couldn't note anything from that. Tap Show me suggestions or Name a role."
)
NOTHING_LEFT = (
    "Thank you. I have no more questions. Open Suggestions for work that could suit you, or "
    "What we know to change an answer."
)


@dataclass(frozen=True)
class _Ask:
    """One question the demo interviewer asks, and the field it asks about (none for the open
    question an unsure person starts with)."""

    field: ProfileField | None
    question: str


_OPEN = _Ask(None, UNSURE_QUESTION)
_SURE_TARGET = _Ask(ProfileField.TARGET_TITLES, SURE_QUESTION)


def asked_field(question: str | None) -> ProfileField | None:
    """The field one of the demo interviewer's questions asks about; None for any other text
    (a model's question is never classified)."""
    asks = {SURE_QUESTION: ProfileField.TARGET_TITLES, **{q: f for f, q in QUESTIONS.items()}}
    return None if question is None else asks.get(question)


def _order(entry: EntryMode | None) -> list[_Ask]:
    """The questions in the order the entry the person chose leads with: a sure person
    confirms the target first; anyone else answers the practical questions, then is asked
    whether they have a role in mind."""
    practical = [_Ask(field, QUESTIONS[field]) for field in CRITICAL]
    if entry is EntryMode.SURE:
        return [_SURE_TARGET, *practical]
    return [*practical, _Ask(ProfileField.TARGET_TITLES, QUESTIONS[ProfileField.TARGET_TITLES])]


def _first_unanswered(context: PromptContext, answered: set[ProfileField]) -> _Ask | None:
    return next(
        (
            ask
            for ask in _order(context.entry)
            if ask.field is not None
            and ask.field not in answered
            and context.profile[ask.field].state is FieldState.UNASKED
        ),
        None,
    )


def _in_front(context: PromptContext) -> _Ask | None:
    """The question the person is answering: on their first message, the opening question the
    web asks for their entry (none if they typed before choosing one); after that, the one
    asked after their last answered message, recomputed from what that message said and the
    answers saved since (so a change they kept none of still counts as asked about)."""
    earlier = [
        m
        for m in context.messages
        if m.ref != context.current_message and m.ref in context.your_earlier_replies
    ]
    if not earlier:
        return {EntryMode.SURE: _SURE_TARGET, EntryMode.UNSURE: _OPEN, None: None}[context.entry]
    last = earlier[-1]
    noted = {update.field for update in _proposals(context, last.ref, last.text)}
    return _first_unanswered(context, noted)


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
        if (_PAY.search(sentence) or _HOURLY.search(sentence)) and not _SPEND.search(sentence):
            period = (
                "hour"
                if _HOURLY.search(sentence)
                else "week"
                if _WEEKLY.search(sentence)
                else "month"
                if monthly
                else "year"
            )
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
    if target := _TARGET.search(text):
        targets = list(dict.fromkeys([*_listed(context, ProfileField.TARGET_TITLES), target[1]]))
        if len(targets) <= MAX_TARGETS:
            updates.append(
                _update(
                    ProfileField.TARGET_TITLES,
                    ref,
                    "You said the role you want.",
                    items=[title.strip() for title in targets],
                )
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


def fixture_turn(context: PromptContext, *, smaller_step: bool = False) -> InterviewTurnOutput:
    """`smaller_step`: the turn's instructions carry the smaller-step instruction, so the
    reply acknowledges the message and offers a smaller step, and no question is asked."""
    current = next(m for m in context.messages if m.ref == context.current_message)
    in_front = _in_front(context)
    updates = _proposals(context, current.ref, current.text)
    answered = {u.field for u in updates}
    # A message that is only one of these words matches no other pattern.
    word = _ANSWER_WORD.fullmatch(current.text.strip())
    if word and in_front is not None and in_front.field is not None:
        state, reason = _ANSWER_STATE[word[1].casefold()]
        updates.append(_update(in_front.field, current.ref, reason, state=state))
        answered.add(in_front.field)
    missing = [
        field
        for field in CRITICAL
        if field not in answered and context.profile[field].state is FieldState.UNASKED
    ]
    after = _first_unanswered(context, answered)
    question = None if smaller_step or after is None else after.question
    noted = f"I noted {len(updates)} thing{'s' if len(updates) != 1 else ''} for you to review."
    # The question goes only in next_question; the web app shows it once, apart (PROF-08).
    if updates:
        said = noted
    elif after is None:  # nothing left to ask: what to do next, never a loop back to Skip
        said = NOTHING_LEFT
    elif after == in_front:  # asked again because nothing could be noted: the way on
        said = COULDNT_NOTE_ROLE if after.question == ROLE_QUESTION else COULDNT_NOTE
    else:
        said = "Thank you."
    if smaller_step:
        said = SMALLER_STEP_REPLY + (f" {noted}" if updates else "")
    reply = REPLY_PREFIX + said
    return InterviewTurnOutput(
        reply=reply,
        proposed_updates=updates,
        next_question=question,
        missing_critical_fields=missing,
        ready_for_review=bool(updates),
    )
