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

from nessa.identity.activity import PartialWriter
from nessa.identity.failures import FailureClass, classify_failure
from nessa.identity.model_registry import ModelMode
from nessa.money import Money
from nessa.profile.document import empty_profile
from nessa.profile.fixture_interviewer import (
    REPLY_PREFIX,
    SMALLER_STEP_REPLY,
    SURE_QUESTION,
    UNSURE_QUESTION,
    fixture_turn,
)
from nessa.profile.interview import (
    ContextMessage,
    InterviewProposal,
    ProfileField,
    PromptContext,
    ProposalOrigin,
    TurnInput,
    check_turn,
    context_profile,
    render_prompt,
)
from nessa.profile.interview_agent import fixture_interviewer_model, run_interview_turn
from nessa.profile.records import EntryMode
from nessa.profile.safety import SUPPORT_TURN_INSTRUCTION
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
    assert unsure == UNSURE_QUESTION  # what they want to change, before any practical limit
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


def test_the_fixture_ignores_an_amount_beyond_the_money_bound() -> None:
    for message in ("I could spend £1,000,000,000.", "I could spend £1234567890."):
        ctx = turn_input(message)

        out = fixture_turn(prompt_context(ctx))
        proposal, problems = check_turn(out, ctx, ProposalOrigin.FIXTURE)

        assert problems == []  # a demo turn never fails on what the person typed
        assert proposal is not None
        assert proposal.changes == []
