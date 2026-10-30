"""The source search as a run task (adapter; ADR 0003: search is Meta's own, through
`NativeTool(WebSearchTool(...))`, never the `WebSearch` capability whose local fallback would
reach another provider).

One request on whatever model the worker built for the run: strict JSON output
(`NativeOutput`), search context `low`, at most `MAX_TOOL_CALLS` tool calls asked of the
Responses API (`max_tool_calls`), the search's sources included so each candidate's
grounding can be checked, and no repair (`search.MAX_REQUESTS`). A response cut off at its
token limit ends the run (`TruncationGuard`). Demo workspaces never search (a database
CHECK), so there is no fixture model for this kind.
"""

import asyncio
from typing import Any

from pydantic_ai import Agent, NativeOutput, RunContext
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    NativeToolCallPart,
    NativeToolReturnPart,
)
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from pydantic_ai.native_tools import WebSearchTool, WebSearchUserLocation
from pydantic_ai.usage import UsageLimits

from careerwright.evidence import search
from careerwright.evidence.search import (
    INSTRUCTIONS,
    MAX_OUTPUT_TOKENS,
    MAX_REQUESTS,
    MAX_TOOL_CALLS,
    SearchInput,
    SearchOutput,
    SearchProposal,
    render_prompt,
)
from careerwright.identity.activity import PartialSink, RunTask, TruncationGuard
from careerwright.identity.model_registry import ModelMode


def searched(messages: list[ModelMessage]) -> tuple[set[str], list[str]]:
    """(URLs the search returned or opened, the queries it ran), from the native tool parts
    of the run's responses."""
    sources: set[str] = set()
    queries: list[str] = []
    for message in messages:
        if not isinstance(message, ModelResponse):
            continue
        for part in message.parts:
            if isinstance(part, NativeToolReturnPart) and isinstance(part.content, dict):
                listed: Any = part.content.get("sources")
                for source in listed if isinstance(listed, list) else []:
                    if isinstance(source, dict) and isinstance(source.get("url"), str):
                        sources.add(source["url"])
            elif isinstance(part, NativeToolCallPart):
                args: Any = part.args if isinstance(part.args, dict) else {}
                if isinstance(args.get("query"), str):
                    queries.append(args["query"][:200])
                if isinstance(args.get("url"), str):  # an open-page action
                    sources.add(args["url"])
    return sources, queries


def run_search(
    model: Model,
    mode: ModelMode,
    raw_input: bytes | None,
    _sink: PartialSink,
    *,
    max_tool_calls: int = MAX_TOOL_CALLS,
) -> SearchProposal:
    """`max_tool_calls` is the product's two; only the live qualification of the bound
    (`tools.live_smoke --search-bound`) asks for one."""
    if raw_input is None:
        raise ValueError("a source search has a sealed input")
    context = SearchInput.model_validate_json(raw_input)
    agent = Agent(
        model,
        output_type=NativeOutput(SearchOutput),
        instructions=INSTRUCTIONS,
        retries={"tools": 0, "output": 0},
        capabilities=[
            TruncationGuard(),
            NativeTool(
                WebSearchTool(
                    search_context_size="low",
                    user_location=WebSearchUserLocation(country="GB"),
                )
            ),
        ],
    )
    accepted: list[SearchProposal] = []

    @agent.output_validator
    def _check(ctx: RunContext[None], output: SearchOutput) -> SearchOutput:
        sources, queries = searched(ctx.messages)
        accepted.append(search.check_search(output, context, sources=sources, queries=queries))
        return output

    settings = OpenAIResponsesModelSettings(
        max_tokens=MAX_OUTPUT_TOKENS,
        openai_include_web_search_sources=True,
        extra_body={"max_tool_calls": max_tool_calls},
    )
    asyncio.run(
        agent.run(
            render_prompt(context),
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
            model_settings=settings,
        )
    )
    return accepted[-1]


SOURCE_SEARCH_TASK = RunTask(
    call=run_search,
    worst_case_nano_usd=search.worst_case_nano_usd,
    has_input=True,
    # Meta runs the searches inside the one request, so `request_limit` cannot bound them:
    # the activity holds the captured usage to the reservation's bounds on every path, a
    # reply that also failed included (review B N4).
    exceeded_bound=search.exceeded_bound,
)
