"""The one validation repair stays within the tokens its kind's reservation allows, for every
model-backed run kind (carry-forward from Task 6b; MODEL-08).

Pydantic AI answers an output that fails the strict schema with the validation errors, and
each error quotes the rejected input: for invalid JSON, the whole output. The repair request
already carries that output once as the model's own turn (the reservation's output term), so
the quote spent it a second time against an allowance of 1,000 or 2,000 tokens. These tests
drive each kind's agent with a fake provider and measure the feedback exactly as the
provider receives it. Bytes bound tokens, so a byte count within the allowance is a token
count within it.
"""

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field

import pytest
from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, NativeOutput, capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

from nessa.identity.activity import PartialSink, RepairBound
from nessa.identity.model_registry import ModelMode
from nessa.profile import discovery, interview, slate_explanation
from nessa.profile.discovery_agent import run_discovery
from nessa.profile.interview_agent import run_interview_turn
from nessa.profile.slate_explanation_agent import run_explanation
from tests.domain import test_discovery_contract, test_interview_agent, test_slate_explanation


def ignore(text: str, *, complete: bool) -> None:
    """A partial-reply sink that keeps nothing."""


@dataclass(frozen=True)
class Kind:
    name: str
    call: Callable[[FunctionModel, ModelMode, bytes | None, PartialSink], object]
    raw_input: Callable[[], bytes]
    max_output_tokens: int
    repair_allowance_tokens: int


KINDS = [
    Kind(
        "interview_turn",
        run_interview_turn,
        lambda: test_interview_agent.turn_input("I live in Leeds").model_dump_json().encode(),
        interview.MAX_OUTPUT_TOKENS,
        interview.REPAIR_ALLOWANCE_TOKENS,
    ),
    Kind(
        "discovery",
        run_discovery,
        lambda: test_discovery_contract.context().model_dump_json().encode(),
        discovery.MAX_OUTPUT_TOKENS,
        discovery.REPAIR_ALLOWANCE_TOKENS,
    ),
    Kind(
        "slate_explanation",
        run_explanation,
        lambda: test_slate_explanation.context().model_dump_json().encode(),
        slate_explanation.MAX_OUTPUT_TOKENS,
        slate_explanation.REPAIR_ALLOWANCE_TOKENS,
    ),
]


@dataclass
class Provider:
    """Answers every request with `reply` and keeps what each request carried."""

    reply: str
    received: list[list[ModelMessage]] = field(default_factory=list)

    def model(self) -> FunctionModel:
        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            self.received.append(list(messages))
            return ModelResponse(parts=[TextPart(self.reply)])

        async def stream(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str]:
            self.received.append(list(messages))  # the interview turn streams its reply
            yield self.reply

        return FunctionModel(respond, stream_function=stream)

    def feedback(self) -> str:
        """The text of the repair request's new user turn, as the provider received it."""
        repair = self.received[1][-1]
        assert isinstance(repair, ModelRequest)
        texts = [p.content for p in repair.parts if isinstance(p, UserPromptPart)]
        assert texts, repair
        return "".join(t if isinstance(t, str) else json.dumps(t, default=str) for t in texts)


def largest_rejected_output(kind: Kind) -> str:
    """Output that fills the kind's output bound at one byte per token and is not JSON:
    the worst case, a quote as long as the output itself."""
    return "{" + "x" * (kind.max_output_tokens - 1)


def schema_mismatch(kind: Kind) -> str:
    """Valid JSON whose every value has the wrong type, quoted back field by field."""
    return json.dumps({"reply": ["y" * 200] * 6, "queries": "z" * 900, "explanations": 7})


@pytest.mark.req("MODEL-08")
@pytest.mark.parametrize("kind", KINDS, ids=[k.name for k in KINDS])
@pytest.mark.parametrize("reply", [largest_rejected_output, schema_mismatch])
def test_a_schema_repair_fits_its_allowance_and_never_quotes_the_rejected_output(
    kind: Kind, reply: Callable[[Kind], str]
) -> None:
    rejected = reply(kind)
    provider = Provider(rejected)

    # The second answer fails too, so the run ends `invalid_model_output`.
    with capture_run_messages(), pytest.raises(UnexpectedModelBehavior):
        kind.call(provider.model(), ModelMode.CONTRIBUTOR, kind.raw_input(), ignore)

    assert len(provider.received) == 2  # the first request and one repair, never a third
    shown = provider.feedback()
    assert len(shown.encode()) <= kind.repair_allowance_tokens
    for filler in ("x", "y", "z"):
        assert filler * 40 not in shown  # the rejected output is not quoted back
    assert "schema" in shown  # it still says what is wrong


class Out(BaseModel):
    answer: str


@pytest.mark.req("MODEL-08")
def test_a_task_s_own_repair_message_is_cut_to_fit_and_says_how_many_problems_were_left_out() -> (
    None
):
    provider = Provider(Out(answer="no").model_dump_json())
    agent = Agent(
        provider.model(),
        output_type=NativeOutput(Out),
        retries={"tools": 0, "output": 1},
        capabilities=[RepairBound(600)],
    )

    @agent.output_validator
    def refuse(output: Out) -> Out:
        problems = [f"problem {n}: {'quoted model text ' * 20}" for n in range(30)]
        raise ModelRetry("Answer again, fixing these problems:\n- " + "\n- ".join(problems))

    with pytest.raises(UnexpectedModelBehavior):
        asyncio.run(agent.run("go", usage_limits=UsageLimits(request_limit=2)))

    shown = provider.feedback()
    assert len(shown.encode()) <= 600
    assert "Answer again, fixing these problems:" in shown
    assert "- problem 0:" in shown
    assert "more problems." in shown


@pytest.mark.req("MODEL-08")
def test_a_repair_message_that_fits_is_sent_unchanged() -> None:
    provider = Provider(Out(answer="no").model_dump_json())
    agent = Agent(
        provider.model(),
        output_type=NativeOutput(Out),
        retries={"tools": 0, "output": 1},
        capabilities=[RepairBound(600)],
    )

    @agent.output_validator
    def refuse(output: Out) -> Out:
        raise ModelRetry("Say yes.")

    with pytest.raises(UnexpectedModelBehavior):
        asyncio.run(agent.run("go", usage_limits=UsageLimits(request_limit=2)))

    assert "<retry_feedback>\nSay yes.\n</retry_feedback>" in provider.feedback()
