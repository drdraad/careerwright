"""The explanation task in process: a Pydantic AI agent with the strict output schema, the
deterministic check and its one bounded repair, on the fixture explainer and on a fake
provider answering each way the contract refuses (S2.7; REC1-11, MODEL-03). No network, no
database: the run's failure class is what the activity would record."""

import json
from collections.abc import Callable
from typing import Any

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryFeedbackPart,
    TextPart,
)
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel

from nessa.identity.failures import FailureClass, classify_failure
from nessa.identity.model_registry import ModelMode
from nessa.profile.interview import ProposalOrigin
from nessa.profile.slate_explanation import REPAIR_ALLOWANCE_TOKENS, SlateExplanation
from nessa.profile.slate_explanation_agent import fixture_explainer_model, run_explanation
from tests.domain.test_slate_explanation import GOOD_GARDENER, GOOD_MECHANIC, claim, context, quote


def ignore(text: str, *, complete: bool) -> None:
    """A partial-reply sink that keeps nothing (an explanation streams nothing)."""


def answer(mechanic: dict[str, Any]) -> str:
    return json.dumps(
        {
            "explanations": [
                {"occupation": "o1", "claims": [mechanic]},
                {"occupation": "o2", "claims": [GOOD_GARDENER]},
            ]
        }
    )


MISQUOTED = answer(
    claim(
        "You enjoy fixing bikes, and this work is about repairing them.",
        quote("answer", "repairing bicycles"),
        quote("esco", "repairs bicycle models"),
    )
)
INVENTED_ANSWER = answer(
    claim(
        "You love animals, and this work keeps you close to the bikes you care for.",
        quote("answer", "I love animals"),
        quote("esco", "repair bicycles"),
    )
)
FACT_ESCO_LACKS = answer(
    claim(
        "You like being outside, and this work is outdoors in all weathers.",
        quote("answer", "working outdoors"),
        quote("esco", "outdoors in all weathers"),
    )
)
READINESS = answer(
    claim(
        "You are ready to apply for this role now, given your repair work.",
        quote("answer", "repairing bicycles"),
        quote("esco", "repair bicycles"),
    )
)
INVALID_JSON = '{"explanations": [{"occupation": "o1", "claims": [{"text": "You enjoy'
VALID = answer(GOOD_MECHANIC)


def scripted(*replies: str, truncated: bool = False) -> Callable[[], FunctionModel]:
    """A provider answering each request with the next reply (the last one repeats)."""

    def build() -> FunctionModel:
        calls = iter(range(10_000))

        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            text = replies[min(next(calls), len(replies) - 1)]
            if truncated:
                return ModelResponse(
                    parts=[TextPart(text[: len(text) // 2])], finish_reason="length"
                )
            return ModelResponse(parts=[TextPart(text)])

        return FunctionModel(respond)

    return build


def run(
    build: Callable[[], Model], mode: ModelMode = ModelMode.CONTRIBUTOR
) -> tuple[SlateExplanation | Exception, list[ModelMessage]]:
    raw = context().model_dump_json().encode()
    with capture_run_messages() as messages:
        try:
            result: SlateExplanation | Exception = run_explanation(build(), mode, raw, ignore)
        except Exception as error:  # the activity classifies it
            result = error
    return result, messages


def requests(messages: list[ModelMessage]) -> list[ModelRequest]:
    return [m for m in messages if isinstance(m, ModelRequest)]


@pytest.mark.req("REC1-11", "MODEL-03")
@pytest.mark.parametrize(
    ("reply", "named"),
    [
        (MISQUOTED, "repairs bicycle models"),
        (INVENTED_ANSWER, "I love animals"),
        (FACT_ESCO_LACKS, "outdoors in all weathers"),
        (READINESS, "readiness"),
        (INVALID_JSON, "json_invalid"),
    ],
    ids=["misquotation", "invented answer", "fact ESCO lacks", "readiness claim", "invalid JSON"],
)
def test_a_refused_output_is_repaired_once_then_fails_typed_with_nothing_stored(
    reply: str, named: str
) -> None:
    result, messages = run(scripted(reply))

    assert isinstance(result, UnexpectedModelBehavior)
    assert classify_failure(result).failure is FailureClass.INVALID_MODEL_OUTPUT
    sent = requests(messages)
    assert len(sent) == 2  # the first request and one repair, never a third
    assert named in str(sent[1].parts)  # the repair names the problem


@pytest.mark.req("REC1-11", "MODEL-08")
def test_the_repair_sent_for_a_flood_of_problems_stays_within_its_allowance() -> None:
    # Fix round 1 (M2): whatever the output holds, the repair request's text fits the
    # tokens the reservation allows for it (bytes bound tokens).
    invented = [quote("answer", f"never said {'x' * 400} {n}") for n in range(30)]
    bad = claim("This repair work " * 30, *invented)
    flooded = json.dumps(
        {"explanations": [{"occupation": ref, "claims": [bad] * 9} for ref in ("o1", "o2")]}
    )

    result, messages = run(scripted(flooded))

    assert isinstance(result, UnexpectedModelBehavior)
    [retry] = [p for p in requests(messages)[1].parts if isinstance(p, RetryFeedbackPart)]
    shown = retry.model_response()  # the text the model is sent, with the agent's fence
    assert len(shown.encode()) <= REPAIR_ALLOWANCE_TOKENS
    assert "more problems" in shown


@pytest.mark.req("REC1-11", "MODEL-03")
def test_a_refused_output_that_its_repair_fixes_is_accepted() -> None:
    result, messages = run(scripted(MISQUOTED, VALID))

    assert isinstance(result, SlateExplanation), result
    assert result.origin is ProposalOrigin.MODEL
    assert len(requests(messages)) == 2


@pytest.mark.req("REC1-11", "MODEL-03")
def test_a_truncated_output_fails_at_once_and_is_never_parsed_or_repaired() -> None:
    result, messages = run(scripted(VALID, truncated=True))

    assert isinstance(result, Exception)
    assert classify_failure(result).failure is FailureClass.OUTPUT_TRUNCATED
    assert len(requests(messages)) == 1  # no repair request
    [response] = [m for m in messages if isinstance(m, ModelResponse)]
    assert response.finish_reason == "length"  # kept, so its usage is still booked


@pytest.mark.req("REC1-11", "BND1-11")
def test_the_fixture_explainer_answers_offline_through_the_same_agent() -> None:
    result, messages = run(fixture_explainer_model, ModelMode.FIXTURE)

    assert isinstance(result, SlateExplanation), result
    assert result.origin is ProposalOrigin.FIXTURE
    assert len(requests(messages)) == 1
    assert [s.title for s in result.suggestions] == ["bicycle mechanic", "landscape gardener"]
