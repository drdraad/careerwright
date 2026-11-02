"""The deterministic demo interviewer (plan section 2: demo mode uses deterministic model
fixtures; section 3: a fixture adapter keeps the live adapter's failure and provenance
contract, with its synthetic origin retained).

It reads the same prompt context a live model reads and answers the same InterviewTurn
schema, from a few fixed patterns in the person's latest message: English city names from
the list, "N hours", "£N" (a monthly amount if the sentence says month), "I am a ...",
"I enjoy ...", "I don't enjoy ..." or "I hate ..." (a dislike, Task W2F), "I want to be a ..."
(a target), "rather not say" about money, and a message
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
from careerwright.profile.document import (
    MAX_CITIES,
    MAX_TARGETS,
    MAX_TASKS,
    FieldState,
    WorkStatus,
)
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
SURE_QUESTION = "Which role are you aiming for, and at what level?"
# The explore opening asks for no job (Task 6f, the product owner's decision 4; its final words
# are theirs, at session W2). The web's `OPENING_QUESTION.unsure` is the same sentence.
UNSURE_QUESTION = "What would you like your working life to be like?"
# Asked of an unsure person straight after the opening (Task 6f): what they enjoy, wherever.
ENJOY_QUESTION = "What do you enjoy doing, at school, at work or in your own time?"
QUESTIONS = {
    ProfileField.CURRENT_ROLE: "What do you do now, or what did you do most recently?",
    ProfileField.CITIES: "Which English cities could you work in? Name up to three.",
    ProfileField.WEEKLY_STUDY_HOURS: "About how many hours a week could you give to learning?",
    ProfileField.DIRECT_SPEND_CAP: (
        "What is the most you would spend on your next step in total? You can say you'd rather "
        "not say."
    ),
    ProfileField.TARGET_TITLES: "Do you have a role in mind, or would you like to explore?",
    ProfileField.ENJOYED_TASKS: ENJOY_QUESTION,
}
ROLE_QUESTION = QUESTIONS[ProfileField.TARGET_TITLES]
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
# What the person doesn't enjoy (Task W2F): its own answer, never an enjoyed task.
_DISLIKE = re.compile(
    r"\bI (?:hate|dislike|(?:don't|do not) (?:really )?(?:enjoy|like)) ([^.,;!?]{3,80})",
    re.IGNORECASE,
)
_TARGET = re.compile(
    r"\bI want to be (?:a|an) ([A-Za-z][A-Za-z -]{2,60}?)(?=[.,;!?]| in | at | and |$)",
    re.IGNORECASE,
)
# Task 6f: no job yet, what the person is doing now, a qualification, and something they do.
_NO_JOB = re.compile(
    r"\bI(?:'ve| have) never (?:had a job|worked)\b|\bI (?:haven't|have not) had a job\b",
    re.IGNORECASE,
)
_STUDYING = re.compile(
    r"\bI(?:'m| am) (?:a |an )?(?:[A-Za-z-]+ )?(?:student|pupil)\b"
    r"|\bI(?:'m| am) (?:at|in) (?:school|college|sixth form|university|uni)\b"
    r"|\bI(?:'m| am) in Year 1[0-3]\b",
    re.IGNORECASE,
)
_LOOKING = re.compile(r"\blooking for (?:work|a job)\b|\bunemployed\b", re.IGNORECASE)
_CARING = re.compile(r"\bI(?:'m| am) (?:a )?(?:full-time )?carer\b|\bI care for\b", re.I)
_QUALIFICATION_WORD = (
    r"(?:A[- ]levels?|GCSEs?|BTECs?|T[- ]Levels?|NVQs?|diploma|degree|apprenticeship)"
)
_EXPECTED = re.compile(
    rf"\b(?:doing|taking|studying(?: for)?) ([^.,;!?]{{0,60}}?\b{_QUALIFICATION_WORD}\b"
    r"[^.,;!?]{0,40})",
    re.IGNORECASE,
)
# Only an explicit verb of having it, never a bare "have" or "got to" (Task 6f review I2).
_ACHIEVED = re.compile(
    rf"\bI(?:'ve| have)? (?:got|passed) (?!to\b)([^.,;!?]{{0,60}}?\b{_QUALIFICATION_WORD}\b"
    r"[^.,;!?]{0,40})",
    re.IGNORECASE,
)
# A message that mentions a retake, a resit or a fail is never read as achieved.
_NOT_ACHIEVED = re.compile(r"\b(?:re-?tak|re-?sit|fail)", re.IGNORECASE)
_DONE = re.compile(r"\bI ((?:help|volunteer)\b[^.,;!?]{3,80})", re.IGNORECASE)
# What someone is, read by `_ROLE`, that is what they are doing now, never a job title.
_NOT_A_JOB = re.compile(r"\b(?:student|pupil|carer)$", re.IGNORECASE)
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
    confirms the target first; an unsure person is asked what they enjoy (Task 6f); anyone but
    a sure person answers the practical questions, then is asked whether they have a role in
    mind. The role question is asked only while the role is not asked: "I haven't had a job
    yet" answers it."""
    practical = [_Ask(field, QUESTIONS[field]) for field in CRITICAL]
    if entry is EntryMode.SURE:
        return [_SURE_TARGET, *practical]
    role_or_explore = _Ask(ProfileField.TARGET_TITLES, QUESTIONS[ProfileField.TARGET_TITLES])
    if entry is EntryMode.UNSURE:
        return [_Ask(ProfileField.ENJOYED_TASKS, ENJOY_QUESTION), *practical, role_or_explore]
    return [*practical, role_or_explore]


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
    if _NO_JOB.search(text):
        updates.append(
            _update(
                ProfileField.CURRENT_ROLE,
                ref,
                "You said you haven't had a job yet.",
                state=AnsweredState.NO_JOB_YET,
                basis=Basis.INFERRED,
            )
        )
    elif (role := _ROLE.search(text)) and not _NOT_A_JOB.search(role.group(1)):
        updates.append(
            _update(ProfileField.CURRENT_ROLE, ref, "You said what you do.", text=role.group(1))
        )
    if status := _status(text):
        updates.append(
            _update(
                ProfileField.WORK_STATUS,
                ref,
                "You said what you are doing now.",
                text=status.value,
                basis=Basis.INFERRED,
            )
        )
    if qualification := _qualification(text):
        held = [f"{q['status']}: {q['name']}" for q in _held_qualifications(context)]
        items = list(dict.fromkeys([*held, qualification]))
        if len(items) <= MAX_TASKS:
            updates.append(
                _update(
                    ProfileField.QUALIFICATIONS,
                    ref,
                    "You named a qualification.",
                    items=items,
                )
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
    if dislike := _DISLIKE.search(text):
        held = _listed(context, ProfileField.DISLIKED_TASKS)
        task = dislike.group(1).strip()
        disliked = held if task.casefold() in {h.casefold() for h in held} else [*held, task]
        if len(disliked) <= MAX_TASKS:
            updates.append(
                _update(
                    ProfileField.DISLIKED_TASKS,
                    ref,
                    "You said you don't enjoy this.",
                    items=disliked,
                )
            )
    if done := _DONE.search(text):
        tasks = list(dict.fromkeys([*_listed(context, ProfileField.EVIDENCED_TASKS), done[1]]))
        if len(tasks) <= MAX_TASKS:
            updates.append(
                _update(
                    ProfileField.EVIDENCED_TASKS,
                    ref,
                    "You said you do this.",
                    items=[task.strip() for task in tasks],
                )
            )
    return updates


def _status(text: str) -> WorkStatus | None:
    """What the person said they are doing now, from a few fixed phrases; None otherwise."""
    for pattern, status in (
        (_STUDYING, WorkStatus.IN_EDUCATION_OR_TRAINING),
        (_LOOKING, WorkStatus.LOOKING_FOR_WORK),
        (_CARING, WorkStatus.CARING),
    ):
        if pattern.search(text):
            return status
    return None


def _qualification(text: str) -> str | None:
    """One qualification in the model's item form: "expected: …" for one being taken,
    "achieved: …" for one they plainly have; None when the message names neither, or when it
    mentions a retake or a fail and names none being taken."""
    if expected := _EXPECTED.search(text):
        return f"expected: {expected.group(1).strip()}"
    if _NOT_ACHIEVED.search(text):
        return None
    if achieved := _ACHIEVED.search(text):
        return f"achieved: {achieved.group(1).strip()}"
    return None


def _held_qualifications(context: PromptContext) -> list[dict[str, str]]:
    current = context.profile[ProfileField.QUALIFICATIONS]
    if current.state is not FieldState.PROVIDED or not isinstance(current.value, list):
        return []
    return [item for item in current.value if isinstance(item, dict)]


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
