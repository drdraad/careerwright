"""The interview task end to end in process: a Pydantic AI agent with the strict output
schema, the deterministic check and its one bounded repair, on the fixture interviewer and
on a fake provider (MODEL-03, PROF-02, PROF-05). No network, no database."""

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
        fixture_interviewer_model(), ModelMode.FIXTURE, ctx.model_dump_json().encode()
    )

    assert proposal.origin is ProposalOrigin.FIXTURE
    assert [(c.field, c.value) for c in proposal.changes] == [(ProfileField.CITIES, ["Bristol"])]


def run_fake(failure: FakeFailure | None) -> tuple[object, list[object]]:
    model = fake_model_builder(failure=failure)("muse-spark-1.3-contributor", None)
    ctx = turn_input("I could work in Leeds and spend about £1,500.")
    with capture_run_messages() as messages:
        try:
            result: object = run_interview_turn(
                model, ModelMode.CONTRIBUTOR, ctx.model_dump_json().encode()
            )
        except Exception as error:  # the activity classifies this
            result = error
    return result, list(messages)


@pytest.mark.req("PROF-05", "MODEL-03")
def test_an_invalid_output_is_repaired_once_with_the_problems_named() -> None:
    result, messages = run_fake(FakeFailure.INVALID_ONCE)

    assert not isinstance(result, Exception), result
    requests = [m for m in messages if isinstance(m, ModelRequest)]
    assert len(requests) == 2  # the first request and one repair
    repair = str(requests[1].parts)
    assert "cities: cite 1-5 of the message refs ['m1']" in repair


@pytest.mark.req("PROF-05", "MODEL-03")
def test_an_output_still_invalid_after_the_repair_fails_typed_with_no_proposal() -> None:
    result, messages = run_fake(FakeFailure.INVALID_ALWAYS)

    assert isinstance(result, UnexpectedModelBehavior)
    assert classify_failure(result).failure is FailureClass.INVALID_MODEL_OUTPUT
    assert sum(isinstance(m, ModelRequest) for m in messages) == 2  # bounded: never a third


@pytest.mark.req("MODEL-03")
def test_a_refusal_is_its_own_failure_not_a_retry() -> None:
    result, messages = run_fake(FakeFailure.REFUSAL)

    assert isinstance(result, ContentFilterError)
    assert classify_failure(result).failure is FailureClass.MODEL_REFUSED
    assert sum(isinstance(m, ModelRequest) for m in messages) == 1


@pytest.mark.req("MODEL-03", "PROF-03")
def test_a_truncated_output_is_never_accepted() -> None:
    result, messages = run_fake(FakeFailure.TRUNCATED)

    # The cut-off JSON never validates; the activity classifies the run `output_truncated`
    # from the last response's finish reason (tests/integration/test_interview_turns.py).
    assert isinstance(result, UnexpectedModelBehavior)
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    assert responses[-1].finish_reason == "length"
