"""The interview task end to end in process: a Pydantic AI agent with the strict output
schema, the deterministic check and its one bounded repair, on the fixture interviewer and
on a fake provider (MODEL-03, PROF-02, PROF-05). No network, no database."""

import itertools
import uuid
from datetime import UTC, datetime

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import ContentFilterError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelRequest, ModelResponse

from nessa.identity.failures import FailureClass, classify_failure
from nessa.identity.model_registry import ModelMode
from nessa.money import Money
from nessa.profile.document import empty_profile
from nessa.profile.fixture_interviewer import REPLY_PREFIX, fixture_turn
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
from tests.support.fake_models import FakeFailure, fake_model_builder

AT = datetime(2027, 1, 1, tzinfo=UTC)


def ignore(_reply: str) -> None:
    """A partial-reply sink that keeps nothing."""


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
    streamed: list[str] = []

    proposal = run_interview_turn(
        fixture_interviewer_model(),
        ModelMode.FIXTURE,
        ctx.model_dump_json().encode(),
        streamed.append,
    )

    assert len(streamed) > 1  # in pieces, as it arrives
    assert grows(streamed)
    assert streamed[-1] == proposal.reply  # the whole reply, and only the reply


def run_fake(failure: FakeFailure | None) -> tuple[object, list[object], list[str]]:
    model = fake_model_builder(failure=failure)("muse-spark-1.3-contributor", None)
    ctx = turn_input("I could work in Leeds and spend about £1,500.")
    streamed: list[str] = []
    with capture_run_messages() as messages:
        try:
            result: object = run_interview_turn(
                model, ModelMode.CONTRIBUTOR, ctx.model_dump_json().encode(), streamed.append
            )
        except Exception as error:  # the activity classifies this
            result = error
    return result, list(messages), streamed


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


def test_the_fixture_ignores_an_amount_beyond_the_money_bound() -> None:
    for message in ("I could spend £1,000,000,000.", "I could spend £1234567890."):
        ctx = turn_input(message)

        out = fixture_turn(prompt_context(ctx))
        proposal, problems = check_turn(out, ctx, ProposalOrigin.FIXTURE)

        assert problems == []  # a demo turn never fails on what the person typed
        assert proposal is not None
        assert proposal.changes == []
