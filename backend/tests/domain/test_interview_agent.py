"""The interview task end to end in process: a Pydantic AI agent with the strict output
schema, the deterministic check and its one bounded repair, on the fixture interviewer and
on a fake provider (MODEL-03, PROF-02, PROF-05). No network, no database."""

import itertools
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import ContentFilterError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from pydantic_ai.models.function import AgentInfo, FunctionModel

from careerwright.identity.activity import PartialWriter
from careerwright.identity.failures import FailureClass, classify_failure
from careerwright.identity.model_registry import ModelMode
from careerwright.money import Money
from careerwright.profile.document import FieldState, empty_profile
from careerwright.profile.fixture_interviewer import (
    CRITICAL,
    QUESTIONS,
    REPLY_PREFIX,
    SMALLER_STEP_REPLY,
    SURE_QUESTION,
    UNSURE_QUESTION,
    asked_field,
    fixture_turn,
)
from careerwright.profile.interview import (
    AnsweredState,
    ContextField,
    ContextMessage,
    InterviewProposal,
    InterviewTurnOutput,
    ProfileField,
    PromptContext,
    ProposalOrigin,
    TurnInput,
    check_turn,
    context_profile,
    render_prompt,
)
from careerwright.profile.interview_agent import fixture_interviewer_model, run_interview_turn
from careerwright.profile.records import EntryMode
from careerwright.profile.safety import SUPPORT_TURN_INSTRUCTION
from tests.support.fake_models import FakeFailure, fake_model_builder

AT = datetime(2027, 1, 1, tzinfo=UTC)


def ignore(text: str, *, complete: bool) -> None:
    """A partial-reply sink that keeps nothing."""


@dataclass
class Recorder:
    """A partial-reply sink that keeps every call: the reply so far, and whether it ended."""

    calls: list[tuple[str, bool]] = field(default_factory=list)

    def __call__(self, text: str, *, complete: bool) -> None:
        self.calls.append((text, complete))

    @property
    def texts(self) -> list[str]:
        return [text for text, _ in self.calls]


def turn_input(*texts: str) -> TurnInput:
    return TurnInput(
        profile_version=0,
        profile=context_profile(empty_profile()),
        messages=[
            ContextMessage(ref=f"m{i}", message_id=uuid.uuid4(), text=text, sent_at=AT)
            for i, text in enumerate(texts, start=1)
        ],
        replies={},
    )


def prompt_context(ctx: TurnInput) -> PromptContext:
    marker, _, body = render_prompt(ctx).partition("\n")
    assert marker == "Context (JSON):"
    return PromptContext.model_validate_json(body)


def test_the_fixture_reads_the_live_prompt_and_its_output_passes_the_same_check() -> None:
    ctx = turn_input(
        "I'm a warehouse supervisor and I could work in Leeds or Wakefield. I could give "
        "6 hours a week and spend about £1,500 in total. I enjoy training new starters."
    )

    out = fixture_turn(prompt_context(ctx))
    proposal, problems = check_turn(out, ctx, ProposalOrigin.FIXTURE)

    assert problems == []
    assert proposal is not None
    assert proposal.reply.startswith(REPLY_PREFIX)  # labelled synthetic in its own words
    values = {c.field: c.value for c in proposal.changes}
    assert values == {
        ProfileField.CITIES: ["Leeds", "Wakefield"],
        ProfileField.WEEKLY_STUDY_HOURS: 6.0,
        ProfileField.DIRECT_SPEND_CAP: Money(minor_units=150_000, currency="GBP"),
        ProfileField.CURRENT_ROLE: "warehouse supervisor",
        ProfileField.ENJOYED_TASKS: ["training new starters"],
    }
    assert all(c.message_ids == [ctx.messages[0].message_id] for c in proposal.changes)


def test_the_fixture_reads_a_monthly_amount_and_a_refusal_to_say() -> None:
    monthly = fixture_turn(prompt_context(turn_input("I can pay £80 a month.")))
    declined = fixture_turn(prompt_context(turn_input("I'd rather not say how much I can spend.")))

    assert [(u.field, u.text) for u in monthly.proposed_updates] == [
        (ProfileField.MONTHLY_PAYMENT_CAP, "80")
    ]
    assert [(u.field, u.state.value) for u in declined.proposed_updates] == [
        (ProfileField.DIRECT_SPEND_CAP, "prefer_not_to_say")
    ]


def test_the_fixture_asks_for_the_first_missing_critical_input_and_is_deterministic() -> None:
    ctx = prompt_context(turn_input("I could work in York."))

    first, again = fixture_turn(ctx), fixture_turn(ctx)

    assert first == again
    assert first.missing_critical_fields == [
        ProfileField.CURRENT_ROLE,
        ProfileField.WEEKLY_STUDY_HOURS,
        ProfileField.DIRECT_SPEND_CAP,
    ]
    assert first.next_question is not None
    assert "do you do" in first.next_question


@pytest.mark.req("PROF-04")
def test_the_fixture_reads_an_amount_about_pay_as_a_salary_floor_with_its_period() -> None:
    yearly = fixture_turn(prompt_context(turn_input("I need to earn at least £24,000 a year.")))
    hourly = fixture_turn(prompt_context(turn_input("I won't work for less than £12 an hour.")))

    assert [(u.field, u.text) for u in yearly.proposed_updates] == [
        (ProfileField.MINIMUM_SALARY, "24000 per year")
    ]
    assert [(u.field, u.text) for u in hourly.proposed_updates] == [
        (ProfileField.MINIMUM_SALARY, "12 per hour")  # an hourly rate is pay, never annualised
    ]
    spend = fixture_turn(prompt_context(turn_input("I could spend £900 on a course.")))
    assert [u.field for u in spend.proposed_updates] == [ProfileField.DIRECT_SPEND_CAP]
    # Task 6 review A-I-4: a weekly wage keeps its week; a yearly course budget is no floor.
    weekly = fixture_turn(prompt_context(turn_input("I get paid £500 a week.")))
    assert [(u.field, u.text) for u in weekly.proposed_updates] == [
        (ProfileField.MINIMUM_SALARY, "500 per week")
    ]
    budget = fixture_turn(prompt_context(turn_input("I could spend £1,500 a year on courses.")))
    assert [u.field for u in budget.proposed_updates] == [ProfileField.DIRECT_SPEND_CAP]


@pytest.mark.req("PROF-08", "REC1-10")
def test_the_fixture_follows_the_entry_the_person_chose() -> None:
    def asked(entry: EntryMode | None, text: str) -> str | None:
        ctx = turn_input(text).model_copy(update={"entry_mode": entry})
        return fixture_turn(prompt_context(ctx)).next_question

    sure = asked(EntryMode.SURE, "I could work in York.")
    unsure = asked(EntryMode.UNSURE, "Hello.")

    assert sure == SURE_QUESTION  # the target and its level first, no exploration
    # The open question (what they want to change) is the opening the web asks before any
    # practical limit; it is never asked twice (Task W2E, F1), so the first practical one follows.
    assert unsure == QUESTIONS[ProfileField.CURRENT_ROLE]
    assert asked(None, "I could work in York.") == asked(EntryMode.UNSURE, "I could work in York.")


def test_the_fixture_through_the_agent_returns_a_validated_fixture_proposal() -> None:
    ctx = turn_input("I could work in Bristol.")

    proposal = run_interview_turn(
        fixture_interviewer_model(), ModelMode.FIXTURE, ctx.model_dump_json().encode(), ignore
    )

    assert proposal.origin is ProposalOrigin.FIXTURE
    assert [(c.field, c.value) for c in proposal.changes] == [(ProfileField.CITIES, ["Bristol"])]


def grows(replies: list[str]) -> bool:
    """Each streamed reply extends the one before it."""
    return all(later.startswith(earlier) for earlier, later in itertools.pairwise(replies))


@pytest.mark.req("MODEL-03")
def test_the_fixture_streams_its_reply_before_the_validated_proposal_arrives() -> None:
    ctx = turn_input("I could work in Bristol, 5 hours a week.")
    streamed = Recorder()

    proposal = run_interview_turn(
        fixture_interviewer_model(), ModelMode.FIXTURE, ctx.model_dump_json().encode(), streamed
    )

    assert len(set(streamed.texts)) > 1  # in pieces, as it arrives
    assert grows(streamed.texts)
    # The whole reply, and only the reply, marked as ended; nothing after it.
    assert streamed.calls[-1] == (proposal.reply, True)
    assert [complete for _, complete in streamed.calls].count(True) == 1


@pytest.mark.req("MODEL-03")
def test_the_writer_stores_the_whole_reply_before_the_proposals_finish_streaming() -> None:
    ctx = turn_input("I could work in Bristol, 5 hours a week.")
    model = fixture_interviewer_model()
    assert isinstance(model, FunctionModel)
    stream, sent = model.stream_function, list[str]()
    assert stream is not None

    async def counted(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[Any]:
        async for chunk in stream(messages, info):
            if isinstance(chunk, str):
                sent.append(chunk)
            yield chunk

    model.stream_function = counted
    writes: list[tuple[str, int]] = []
    # A clock that never moves: no throttle window ever elapses, so only the first piece
    # and the flush at the reply's end can be written.
    writer = PartialWriter(lambda text: writes.append((text, len("".join(sent)))), clock=lambda: 0)

    proposal = run_interview_turn(model, ModelMode.FIXTURE, ctx.model_dump_json().encode(), writer)

    first, last = writes
    assert proposal.reply.startswith(first[0])
    assert last[0] == proposal.reply  # the whole reply is stored...
    assert last[1] < len("".join(sent))  # ...while the proposals are still streaming


def run_fake(failure: FakeFailure | None) -> tuple[object, list[object], list[str]]:
    model = fake_model_builder(failure=failure)("muse-spark-1.3-contributor", None)
    ctx = turn_input("I could work in Leeds and spend about £1,500.")
    streamed = Recorder()
    with capture_run_messages() as messages:
        try:
            result: object = run_interview_turn(
                model, ModelMode.CONTRIBUTOR, ctx.model_dump_json().encode(), streamed
            )
        except Exception as error:  # the activity classifies this
            result = error
    return result, list(messages), streamed.texts


@pytest.mark.req("MODEL-03")
def test_a_provider_reply_streams_and_a_repair_streams_afresh() -> None:
    result, _, streamed = run_fake(FakeFailure.INVALID_ONCE)

    assert isinstance(result, InterviewProposal)
    restart = next(
        i for i in range(1, len(streamed)) if not streamed[i].startswith(streamed[i - 1])
    )
    first, repaired = streamed[:restart], streamed[restart:]
    assert grows(first)
    assert grows(repaired)  # the repair's reply replaces the first one
    assert first[-1] == repaired[-1] == result.reply


@pytest.mark.req("MODEL-03")
def test_a_stream_cut_off_part_way_is_a_transient_failure_with_only_part_of_the_reply() -> None:
    result, _, streamed = run_fake(FakeFailure.CUT_MID_STREAM)

    assert isinstance(result, Exception)
    assert classify_failure(result).failure is None  # transient: the DBOS step retries
    full = run_fake(None)[0]
    assert isinstance(full, InterviewProposal)
    assert streamed
    assert grows(streamed)
    assert full.reply.startswith(streamed[-1])
    assert streamed[-1] != full.reply


@pytest.mark.req("PROF-05", "MODEL-03")
def test_an_invalid_output_is_repaired_once_with_the_problems_named() -> None:
    result, messages, _ = run_fake(FakeFailure.INVALID_ONCE)

    assert not isinstance(result, Exception), result
    requests = [m for m in messages if isinstance(m, ModelRequest)]
    assert len(requests) == 2  # the first request and one repair
    repair = str(requests[1].parts)
    assert "cities: cite 1-5 of the message refs ['m1']" in repair


@pytest.mark.req("PROF-05", "MODEL-03")
def test_an_output_still_invalid_after_the_repair_fails_typed_with_no_proposal() -> None:
    result, messages, _ = run_fake(FakeFailure.INVALID_ALWAYS)

    assert isinstance(result, UnexpectedModelBehavior)
    assert classify_failure(result).failure is FailureClass.INVALID_MODEL_OUTPUT
    assert sum(isinstance(m, ModelRequest) for m in messages) == 2  # bounded: never a third


@pytest.mark.req("MODEL-03")
def test_a_refusal_is_its_own_failure_not_a_retry() -> None:
    result, messages, _ = run_fake(FakeFailure.REFUSAL)

    assert isinstance(result, ContentFilterError)
    assert classify_failure(result).failure is FailureClass.MODEL_REFUSED
    assert sum(isinstance(m, ModelRequest) for m in messages) == 1


@pytest.mark.req("MODEL-03", "PROF-03")
def test_a_truncated_output_fails_at_once_and_is_never_parsed_or_repaired() -> None:
    result, messages, _ = run_fake(FakeFailure.TRUNCATED)

    assert isinstance(result, Exception)
    assert classify_failure(result).failure is FailureClass.OUTPUT_TRUNCATED
    assert sum(isinstance(m, ModelRequest) for m in messages) == 1  # no repair request
    # The cut-off response stays in the history, so its reported usage is still booked.
    [response] = [m for m in messages if isinstance(m, ModelResponse)]
    assert response.finish_reason == "length"


@pytest.mark.req("PROF-05", "MODEL-03")
def test_a_complete_but_schema_invalid_output_is_repaired_once_then_fails_typed() -> None:
    result, messages, _ = run_fake(FakeFailure.SCHEMA_INVALID_ALWAYS)

    assert isinstance(result, UnexpectedModelBehavior)
    assert classify_failure(result).failure is FailureClass.INVALID_MODEL_OUTPUT
    requests = [m for m in messages if isinstance(m, ModelRequest)]
    assert len(requests) == 2  # one repair, naming the schema problems
    assert "ready_for_review" in str(requests[1].parts)


def instructions_sent(model: FunctionModel, message: str) -> list[str]:
    """The instructions each request of one turn carried to the model."""
    stream, seen = model.stream_function, list[str]()
    assert stream is not None

    async def recorded(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[Any]:
        seen.append(info.instructions or "")
        async for chunk in stream(messages, info):
            yield chunk

    model.stream_function = recorded
    ctx = turn_input(message)
    run_interview_turn(model, ModelMode.CONTRIBUTOR, ctx.model_dump_json().encode(), ignore)
    return seen


@pytest.mark.req("PROF-09")
def test_every_request_of_a_turn_with_a_risk_stem_carries_the_smaller_step_instruction() -> None:
    def fake() -> FunctionModel:
        model = fake_model_builder(failure=FakeFailure.INVALID_ONCE)("test-model", None)
        assert isinstance(model, FunctionModel)
        return model

    flagged = instructions_sent(fake(), "I could work in Leeds. I took my life savings out.")
    plain = instructions_sent(fake(), "I could work in Leeds and spend about £1,500.")

    assert len(flagged) == len(plain) == 2  # the first request and the repair
    assert all(SUPPORT_TURN_INSTRUCTION in sent for sent in flagged)
    assert not any(SUPPORT_TURN_INSTRUCTION in sent for sent in plain)


@pytest.mark.req("PROF-09")
def test_the_fixture_follows_the_smaller_step_instruction_and_asks_no_career_question() -> None:
    def turn(message: str) -> InterviewProposal:
        ctx = turn_input(message)
        encoded = ctx.model_dump_json().encode()
        return run_interview_turn(fixture_interviewer_model(), ModelMode.FIXTURE, encoded, ignore)

    flagged = turn("I could work in Bristol. I took my life savings out to retrain.")
    plain = turn("I could work in Bristol.")

    assert flagged.next_question is None
    assert flagged.reply.startswith(REPLY_PREFIX + SMALLER_STEP_REPLY)
    assert [c.field for c in flagged.changes] == [ProfileField.CITIES]  # proceeds as usual
    assert plain.next_question is not None
    assert SMALLER_STEP_REPLY not in plain.reply


def demo_turn(
    *texts: str,
    entry: EntryMode | None = None,
    answered: dict[ProfileField, FieldState] | None = None,
) -> TurnInput:
    """A turn whose earlier messages each had a reply, with the given fields answered."""
    ctx = turn_input(*texts)
    profile = dict(ctx.profile)
    for name, state in (answered or {}).items():
        profile[name] = ContextField(state=state)
    return ctx.model_copy(
        update={
            "entry_mode": entry,
            "profile": profile,
            "replies": {
                m.ref: "Demo interviewer (synthetic): Thank you." for m in ctx.messages[:-1]
            },
        }
    )


def demo(ctx: TurnInput) -> InterviewTurnOutput:
    out = fixture_turn(prompt_context(ctx))
    proposal, problems = check_turn(out, ctx, ProposalOrigin.FIXTURE)
    assert problems == []  # every new answer passes the same check a model's does
    assert proposal is not None
    return out


@pytest.mark.req("STATE-09")
def test_the_demo_interviewer_takes_a_target_in_the_persons_words() -> None:
    out = demo(demo_turn("I want to be a nurse.", entry=EntryMode.SURE))

    assert [(u.field, u.items) for u in out.proposed_updates] == [
        (ProfileField.TARGET_TITLES, ["nurse"])
    ]
    assert out.next_question == QUESTIONS[ProfileField.CURRENT_ROLE]  # never the same again


@pytest.mark.req("STATE-09", "STATE-08")
def test_skip_unknown_and_prefer_not_to_say_answer_the_question_in_front() -> None:
    # The opening question a sure person sees is about the target.
    skipped = demo(demo_turn("Skip", entry=EntryMode.SURE))
    assert [(u.field, u.state) for u in skipped.proposed_updates] == [
        (ProfileField.TARGET_TITLES, AnsweredState.SKIPPED)
    ]
    assert skipped.next_question == QUESTIONS[ProfileField.CURRENT_ROLE]
    # Later, the question in front is the one asked after the last answered message.
    role_saved = {ProfileField.CURRENT_ROLE: FieldState.PROVIDED}
    unknown = demo(demo_turn("I'm a warehouse supervisor", "unknown.", answered=role_saved))
    assert [(u.field, u.state) for u in unknown.proposed_updates] == [
        (ProfileField.CITIES, AnsweredState.UNKNOWN)
    ]
    assert unknown.next_question == QUESTIONS[ProfileField.WEEKLY_STUDY_HOURS]
    before_budget = {
        ProfileField.CURRENT_ROLE: FieldState.PROVIDED,
        ProfileField.CITIES: FieldState.PROVIDED,
        ProfileField.WEEKLY_STUDY_HOURS: FieldState.PROVIDED,
    }
    declined = demo(demo_turn("5 hours a week", "Prefer not to say", answered=before_budget))
    assert [(u.field, u.state) for u in declined.proposed_updates] == [
        (ProfileField.DIRECT_SPEND_CAP, AnsweredState.PREFER_NOT_TO_SAY)
    ]
    assert declined.next_question == QUESTIONS[ProfileField.TARGET_TITLES]
    # A word inside a longer message is not the person skipping the question.
    assert demo(demo_turn("Skip the small talk", entry=EntryMode.SURE)).proposed_updates == []


@pytest.mark.req("STATE-09")
def test_the_question_in_front_follows_the_last_answered_message_even_when_none_was_kept() -> None:
    # "Leeds" was answered with the hours question next; the person kept none of its changes,
    # so their work areas are still not asked. "Skip" answers the hours question they saw.
    out = demo(demo_turn("I'm a warehouse supervisor in Leeds.", "Skip"))

    assert [(u.field, u.state) for u in out.proposed_updates] == [
        (ProfileField.WEEKLY_STUDY_HOURS, AnsweredState.SKIPPED)
    ]


@pytest.mark.req("STATE-09")
def test_the_open_question_is_the_opening_and_is_never_asked_twice() -> None:
    for reply in ("Hello.", "Skip", "More time outdoors"):
        out = demo(demo_turn(reply, entry=EntryMode.UNSURE))
        assert out.proposed_updates == []
        assert out.next_question == QUESTIONS[ProfileField.CURRENT_ROLE], reply
        assert out.reply == REPLY_PREFIX + "Thank you."


@pytest.mark.req("STATE-09")
def test_an_answer_the_demo_cant_read_says_so_and_names_the_way_on() -> None:
    out = demo(demo_turn("Something with animals", entry=EntryMode.SURE))

    assert out.proposed_updates == []
    assert out.next_question == SURE_QUESTION  # still not answered: asked again, with the way on
    assert out.reply == (
        REPLY_PREFIX + "Thank you. I couldn't note anything from that. Tap an example reply, or "
        "say Skip."
    )


EARLY_ANSWERS = {field: FieldState.PROVIDED for field in CRITICAL}


@pytest.mark.req("STATE-09")
def test_at_the_role_question_an_answer_the_demo_cant_read_names_its_two_buttons() -> None:
    """The web shows "Show me suggestions" and "Name a role" there, never example replies
    (`asksRoleOrExplore`), so the way on names those two (app review I1, the first probe)."""
    for reply in ("Explore", "I'd like to explore", "yes"):
        out = demo(demo_turn("Up to £600", reply, entry=EntryMode.UNSURE, answered=EARLY_ANSWERS))

        assert out.proposed_updates == []
        assert out.next_question == QUESTIONS[ProfileField.TARGET_TITLES], reply
        assert out.reply == (
            REPLY_PREFIX + "Thank you. I couldn't note anything from that. Tap Show me "
            "suggestions or Name a role."
        ), reply


@pytest.mark.req("STATE-09")
def test_after_the_last_question_any_message_says_what_to_do_next_and_skip_never_loops() -> None:
    """Nothing is in front and nothing comes after: no example replies are shown and Skip has
    nothing to answer, so the reply points to the views that are always there, the same for
    any message, and never tells the person to say Skip (app review I1, the second probe)."""
    everything = {**EARLY_ANSWERS, ProfileField.TARGET_TITLES: FieldState.PROVIDED}
    replies: set[str] = set()
    for texts in (("Hello.", "What next?"), ("Hello.", "Skip"), ("Hello.", "Skip", "Skip")):
        out = demo(demo_turn(*texts, entry=EntryMode.UNSURE, answered=everything))

        assert out.proposed_updates == [], texts
        assert out.next_question is None, texts
        assert "Skip" not in out.reply, texts
        assert "example" not in out.reply, texts
        replies.add(out.reply)
    assert replies == {
        REPLY_PREFIX + "Thank you. I have no more questions. Open Suggestions for work that "
        "could suit you, or What we know to change an answer."
    }


# The web's one-tap example replies for each demo question (`EXAMPLE_REPLIES` in
# apps/web/src/lib/vocabulary.ts), keyed by what the question asks about. At the role question
# of a person who isn't sure, the web shows "Show me suggestions" and "Name a role" instead, so
# there the walk types what the target question's examples say.
EXAMPLE_REPLIES: dict[ProfileField | None, tuple[str, ...]] = {
    None: ("I enjoy working with people", "Skip"),
    ProfileField.TARGET_TITLES: ("I want to be a nurse", "Skip"),
    ProfileField.CURRENT_ROLE: ("I'm a warehouse supervisor", "Skip"),
    ProfileField.CITIES: ("Leeds", "Skip"),
    ProfileField.WEEKLY_STUDY_HOURS: ("5 hours a week", "Unknown"),
    ProfileField.DIRECT_SPEND_CAP: ("Up to £600", "Prefer not to say"),
}


@pytest.mark.req("STATE-09")
def test_a_demo_conversation_tapping_example_replies_never_asks_the_same_question_twice() -> None:
    """Each run taps one example per question and saves what it notes, as a person would; the
    question shown after each reply is new, and the conversation ends."""
    for entry in (EntryMode.SURE, EntryMode.UNSURE):
        for pick in (0, 1):
            texts: list[str] = []
            answered: dict[ProfileField, FieldState] = {}
            shown: str | None = SURE_QUESTION if entry is EntryMode.SURE else UNSURE_QUESTION
            asked = [shown]
            about: ProfileField | None = (
                ProfileField.TARGET_TITLES if entry is EntryMode.SURE else None
            )
            while shown is not None:
                texts.append(EXAMPLE_REPLIES[about][pick])
                out = demo(demo_turn(*texts, entry=entry, answered=answered))
                if about is not None:
                    assert about in {u.field for u in out.proposed_updates}, texts[-1]
                for update in out.proposed_updates:
                    answered[update.field] = FieldState(update.state.value)
                shown = out.next_question
                assert shown not in asked, (entry, pick, texts)
                asked.append(shown)
                about = asked_field(shown)
                assert shown is None or about is not None, shown
            assert ProfileField.TARGET_TITLES in answered


def test_each_demo_question_names_what_it_asks_about() -> None:
    assert asked_field(SURE_QUESTION) is ProfileField.TARGET_TITLES
    for asked_about, question in QUESTIONS.items():
        assert asked_field(question) is asked_about
    assert asked_field("Which colour do you like?") is None
    assert asked_field(None) is None


def test_the_fixture_ignores_an_amount_beyond_the_money_bound() -> None:
    for message in ("I could spend £1,000,000,000.", "I could spend £1234567890."):
        ctx = turn_input(message)

        out = fixture_turn(prompt_context(ctx))
        proposal, problems = check_turn(out, ctx, ProposalOrigin.FIXTURE)

        assert problems == []  # a demo turn never fails on what the person typed
        assert proposal is not None
        assert proposal.changes == []
