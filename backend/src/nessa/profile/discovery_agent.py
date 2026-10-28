"""Discovery as a run task, and the fixture query proposer as a model (adapter).

The task runs one Pydantic AI agent on whatever model the worker built for the run: Meta's
native provider for live workspaces, or the fixture proposer for demo workspaces. Both
answer the same strict JSON schema (`NativeOutput`) and pass the same deterministic check
(`discovery.check_discovery`); a failed check is sent back once as a repair request, and a
second failure ends the run `invalid_model_output`, as for an interview turn (ADR 0006
decision 9). A response cut off at its token limit ends the run at once. Nothing streams:
a discovery has no reply to show while it runs.
"""

import asyncio

from pydantic_ai import Agent, ModelRetry, NativeOutput
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

from nessa.identity.activity import PartialSink, RepairBound, RunTask, TruncationGuard
from nessa.identity.model_registry import FIXTURE_DISCOVERY_MODEL_ID, ModelMode
from nessa.profile import discovery
from nessa.profile.discovery import (
    CONTEXT_MARKER,
    INSTRUCTIONS,
    MAX_OUTPUT_TOKENS,
    MAX_REQUESTS,
    REPAIR_ALLOWANCE_TOKENS,
    DiscoveryInput,
    DiscoveryOutput,
    DiscoveryProposal,
    render_prompt,
)
from nessa.profile.fixture_discovery import fixture_queries, prompt_context
from nessa.profile.interview import ProposalOrigin


def run_discovery(
    model: Model, mode: ModelMode, raw_input: bytes | None, _sink: PartialSink
) -> DiscoveryProposal:
    if raw_input is None:
        raise ValueError("a discovery has a sealed input")
    context = DiscoveryInput.model_validate_json(raw_input)
    origin = ProposalOrigin.FIXTURE if mode is ModelMode.FIXTURE else ProposalOrigin.MODEL
    agent = Agent(
        model,
        output_type=NativeOutput(DiscoveryOutput),
        instructions=INSTRUCTIONS,
        retries={"tools": 0, "output": MAX_REQUESTS - 1},
        capabilities=[TruncationGuard(), RepairBound(REPAIR_ALLOWANCE_TOKENS)],
    )
    accepted: list[DiscoveryProposal] = []

    @agent.output_validator
    def _check(output: DiscoveryOutput) -> DiscoveryOutput:
        proposal, problems = discovery.check_discovery(output, context, origin)
        if proposal is None:
            raise ModelRetry(
                "The JSON object does not pass validation. Answer again with the whole object, "
                "fixing these problems:\n- " + "\n- ".join(problems)
            )
        accepted.append(proposal)
        return output

    asyncio.run(
        agent.run(
            render_prompt(context),
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
            model_settings={"max_tokens": MAX_OUTPUT_TOKENS},
        )
    )
    return accepted[-1]


DISCOVERY_TASK = RunTask(
    call=run_discovery,
    worst_case_nano_usd=discovery.worst_case_nano_usd,
    has_input=True,
)


def _prompt(messages: list[ModelMessage]) -> str:
    for message in reversed(messages):
        for part in getattr(message, "parts", ()):
            if (
                isinstance(part, UserPromptPart)
                and isinstance(part.content, str)
                and part.content.startswith(CONTEXT_MARKER)
            ):
                return part.content
    raise ValueError("the prompt has no discovery context")


def fixture_discovery_model() -> Model:
    """The deterministic demo query proposer behind Pydantic AI's model interface: no
    network, no key; it answers from the prompt with `fixture_queries`."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        output = fixture_queries(prompt_context(_prompt(messages)))
        return ModelResponse(
            parts=[TextPart(output.model_dump_json())], model_name=FIXTURE_DISCOVERY_MODEL_ID
        )

    return FunctionModel(respond, model_name=FIXTURE_DISCOVERY_MODEL_ID)
