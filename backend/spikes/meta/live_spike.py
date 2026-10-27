"""Budget-capped live qualification of Meta models through Pydantic AI's native Meta provider.

Run from `backend/`: `uv run python -m spikes.meta.live_spike <check> [--production-model]`.
Every HTTP call to Meta is authorised against the task budget first and appended to the
ledger afterwards, including failures and free calls. The key comes from `.env` only.
"""

import argparse
import asyncio
import json
import secrets
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import httpx2
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, NativeOutput, capture_run_messages
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelResponse, NativeToolCallPart
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.native_tools import WebSearchTool
from pydantic_ai.providers.meta import MetaProvider
from pydantic_ai.usage import UsageLimits

from spikes.meta.budget import BudgetPolicy, CallPlan, authorise_call
from spikes.meta.ledger import CallOutcome, Ledger, LiveCallEntry
from spikes.meta.pricing import (
    PRICING_CHECKED_ON,
    PRICING_SOURCE,
    Usage,
    estimate_cost_nano_usd,
    format_usd,
    worst_case_cost_nano_usd,
)
from spikes.meta.settings import CONTRIBUTOR_SUFFIX, REPO_ROOT, MetaSettings

META_BASE_URL = "https://api.meta.ai/v1"
BUDGET_SCOPE = "task-1-sprint-0"
# Controller cap for Task 1: at most 15 calls, 5 of them on the production model.
POLICY = BudgetPolicy(max_calls=15, max_production_calls=5, max_cost_nano_usd=300_000_000)
LEDGER_PATH = REPO_ROOT / "docs" / "evidence" / "live-usage.jsonl"
MARKDOWN_PATH = REPO_ROOT / "docs" / "evidence" / "live-usage.md"
RESPONSES_ENDPOINT = "POST /v1/responses"


class CareerSuggestion(BaseModel):
    """A bounded, typed proposal; structural validity is not factual truth."""

    title: str
    one_line_rationale: str
    confidence: Literal["low", "medium", "high"]
    transferable_skills: list[str] = Field(min_length=1, max_length=5)


class SourceLink(BaseModel):
    url: str
    title: str


class SearchFindings(BaseModel):
    sources: list[SourceLink] = Field(min_length=1, max_length=3)
    summary: str


SYNTHETIC_PROFILE_PROMPT = (
    "Synthetic test persona (not a real person): a warehouse shift supervisor in Leeds who "
    "enjoys training new starters and solving rota problems. Suggest one adjacent career."
)
SEARCH_PROMPT = (
    "Use web search. Find the official GOV.UK page about the Advanced Learner Loan in "
    "England. Return at most two source URLs you found by searching and a one-sentence summary."
)
INSTRUCTIONS = "Answer only with the requested JSON. Keep every string short."


@dataclass(frozen=True)
class CallLimits:
    max_input_tokens: int
    max_output_tokens: int
    max_web_searches: int


SCHEMA_LIMITS = CallLimits(max_input_tokens=4_000, max_output_tokens=2_048, max_web_searches=0)
# Search results are injected as input tokens, so the input bound is deliberately generous.
SEARCH_LIMITS = CallLimits(max_input_tokens=100_000, max_output_tokens=3_072, max_web_searches=10)


@dataclass
class CallReport:
    outcome: CallOutcome
    usage: Usage | None = None
    reasoning_tokens: int | None = None
    response_id: str | None = None
    http_status: int | None = None
    error_type: str | None = None
    cost_when_no_usage: int | None = None
    facts: dict[str, object] = field(default_factory=dict)


def meta_model(
    model_id: str,
    api_key: str,
    raw_bodies: list[dict[str, object]] | None = None,
    settings: OpenAIResponsesModelSettings | None = None,
) -> OpenAIResponsesModel:
    """Build the native Meta model; `raw_bodies` collects non-streamed JSON response bodies."""

    async def capture(response: httpx2.Response) -> None:
        if raw_bodies is not None and response.headers.get("content-type", "").startswith(
            "application/json"
        ):
            await response.aread()
            raw_bodies.append(response.json())

    http_client = httpx2.AsyncClient(timeout=120.0, event_hooks={"response": [capture]})
    # max_retries=0: the spike records every attempt; nothing retries behind its back.
    client = AsyncOpenAI(
        base_url=META_BASE_URL, api_key=api_key, max_retries=0, http_client=http_client
    )
    return OpenAIResponsesModel(
        model_id, provider=MetaProvider(openai_client=client), settings=settings
    )


def raw_billing_facts(raw_bodies: Sequence[dict[str, object]]) -> dict[str, object]:
    """Meta's own usage fields, to cross-check Pydantic AI's mapping and search billing."""
    facts: dict[str, object] = {}
    for body in raw_bodies:
        output = body.get("output")
        items = output if isinstance(output, list) else []
        facts["raw_usage"] = body.get("usage")
        facts["raw_tool_usage"] = body.get("tool_usage", "absent")
        facts["raw_output_item_types"] = [item.get("type") for item in items]
        facts["raw_web_search_actions"] = [
            (item.get("action") or {}).get("type")
            for item in items
            if item.get("type") == "web_search_call"
        ]
    return facts


def summarise_responses(messages: Sequence[ModelMessage]) -> tuple[Usage | None, int, str | None]:
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    if not responses:
        return None, 0, None
    usage = Usage(
        input_tokens=sum(r.usage.input_tokens for r in responses),
        cached_input_tokens=sum(r.usage.cache_read_tokens for r in responses),
        output_tokens=sum(r.usage.output_tokens for r in responses),
        web_search_queries=sum(r.usage.details.get("web_search_requests", 0) for r in responses),
    )
    reasoning = sum(r.usage.details.get("reasoning_tokens", 0) for r in responses)
    return usage, reasoning, responses[-1].provider_response_id


def native_tool_calls(messages: Sequence[ModelMessage]) -> list[str]:
    """Native tool calls as `tool:action`; only `search` actions are billed as queries."""
    return [
        f"{part.tool_name}:{part.args_as_dict().get('type', '?')}"
        for m in messages
        if isinstance(m, ModelResponse)
        for part in m.parts
        if isinstance(part, NativeToolCallPart)
    ]


def failure_from_http_error(error: ModelHTTPError) -> CallReport:
    return CallReport(
        outcome=CallOutcome.FAILED,
        http_status=error.status_code,
        error_type=error.provider_error_code or error.provider_error_type,
    )


async def run_guarded(
    ledger: Ledger,
    *,
    purpose: str,
    model_id: str,
    is_production: bool,
    endpoint: str,
    worst_case_nano_usd: int,
    call: Callable[[], Awaitable[CallReport]],
    markdown_path: Path = MARKDOWN_PATH,
) -> CallReport:
    authorise_call(
        POLICY,
        ledger.spent(BUDGET_SCOPE),
        CallPlan(is_production_model=is_production, worst_case_nano_usd=worst_case_nano_usd),
    )
    try:
        report = await call()
    except Exception as error:
        # The request may have reached Meta, so the call is logged with an unknown cost (the
        # budget commits its full reservation) before the error propagates.
        ledger.append(
            LiveCallEntry(
                budget_scope=BUDGET_SCOPE,
                purpose=purpose,
                model_id=model_id,
                is_production_model=is_production,
                endpoint=endpoint,
                outcome=CallOutcome.FAILED,
                reserved_nano_usd=worst_case_nano_usd,
                error_type=type(error).__name__,
            )
        )
        write_markdown(ledger, markdown_path)
        raise
    if report.usage is not None:
        cost: int | None = estimate_cost_nano_usd(model_id, report.usage)
    else:
        cost = report.cost_when_no_usage
    record = ledger.append(
        LiveCallEntry(
            budget_scope=BUDGET_SCOPE,
            purpose=purpose,
            model_id=model_id,
            is_production_model=is_production,
            endpoint=endpoint,
            outcome=report.outcome,
            reserved_nano_usd=worst_case_nano_usd,
            estimated_cost_nano_usd=cost,
            http_status=report.http_status,
            error_type=report.error_type,
            input_tokens=report.usage.input_tokens if report.usage else None,
            cached_input_tokens=report.usage.cached_input_tokens if report.usage else None,
            output_tokens=report.usage.output_tokens if report.usage else None,
            reasoning_tokens=report.reasoning_tokens if report.usage else None,
            web_search_queries=report.usage.web_search_queries if report.usage else None,
            provider_response_id=report.response_id,
            notes=json.dumps(report.facts, sort_keys=True, default=str),
        )
    )
    write_markdown(ledger, markdown_path)
    print(f"call #{record.seq} {purpose}: {report.outcome.value}")
    print(f"  cost: {'unknown' if cost is None else format_usd(cost)}")
    print(f"  facts: {json.dumps(report.facts, sort_keys=True, default=str, indent=2)}")
    return report


def model_settings(
    limits: CallLimits, effort: Literal["minimal", "low"]
) -> OpenAIResponsesModelSettings:
    return OpenAIResponsesModelSettings(
        max_tokens=limits.max_output_tokens, openai_reasoning_effort=effort
    )


async def check_invalid_key(settings: MetaSettings) -> CallReport:
    """A well-formed but unissued key must fail visibly with 401 and no output."""
    fake_key = "nessa-spike-invalid-" + secrets.token_hex(16)
    agent = Agent(
        meta_model(settings.test_model, fake_key),
        output_type=NativeOutput(CareerSuggestion),
        instructions=INSTRUCTIONS,
        retries=0,
    )

    async def call() -> CallReport:
        try:
            await agent.run(SYNTHETIC_PROFILE_PROMPT, usage_limits=UsageLimits(request_limit=1))
        except ModelHTTPError as error:
            report = failure_from_http_error(error)
            message = str(error)
            # The fake key is not secret, so its echo can be checked and the message shown.
            fragments = {fake_key[i : i + 8] for i in range(len(fake_key) - 7)}
            report.facts = {
                "exception": type(error).__name__,
                "message": message,
                "error_body_echoes_key_fragment": any(f in message for f in fragments),
            }
            # An unauthenticated request identifies no team, so nothing can be billed.
            report.cost_when_no_usage = 0
            return report
        raise AssertionError("an invalid key produced a successful run")

    return await run_guarded(
        Ledger(LEDGER_PATH),
        purpose="invalid key fails visibly",
        model_id=settings.test_model,
        is_production=settings.is_production_model(settings.test_model),
        endpoint=RESPONSES_ENDPOINT,
        worst_case_nano_usd=0,
        call=call,
    )


async def check_model_listing(settings: MetaSettings) -> CallReport:
    async def call() -> CallReport:
        async with httpx2.AsyncClient(base_url=META_BASE_URL, timeout=30.0) as client:
            response = await client.get(
                "/models",
                headers={"Authorization": f"Bearer {settings.api_key.get_secret_value()}"},
            )
        if response.status_code != httpx2.codes.OK:
            return CallReport(outcome=CallOutcome.FAILED, http_status=response.status_code)
        models = response.json().get("data", [])
        return CallReport(
            outcome=CallOutcome.OK,
            http_status=response.status_code,
            # Listing consumes no tokens; Meta's pricing page prices only tokens, searches,
            # images, audio and segmentation.
            cost_when_no_usage=0,
            facts={
                "models": [{k: m.get(k) for k in ("id", "created", "owned_by")} for m in models]
            },
        )

    return await run_guarded(
        Ledger(LEDGER_PATH),
        purpose="list entitled models",
        model_id="(none)",
        is_production=False,
        endpoint="GET /v1/models",
        worst_case_nano_usd=0,
        call=call,
    )


def qualification_agent(model: Model, *, search: bool) -> Agent[None, BaseModel]:
    """The agent every structured check uses: native JSON-schema output, no output retries,
    bounded output tokens, and Meta's native web search only when asked."""
    limits = SEARCH_LIMITS if search else SCHEMA_LIMITS
    output_type: type[BaseModel] = SearchFindings if search else CareerSuggestion
    return Agent(
        model,
        output_type=NativeOutput(output_type),
        instructions=INSTRUCTIONS,
        model_settings=model_settings(limits, effort="low" if search else "minimal"),
        capabilities=[NativeTool(WebSearchTool(search_context_size="low"))] if search else None,
        retries=0,
    )


async def check_structured(
    settings: MetaSettings, *, production: bool, stream: bool, search: bool
) -> CallReport:
    model_id = settings.production_model if production else settings.test_model
    limits = SEARCH_LIMITS if search else SCHEMA_LIMITS
    raw_bodies: list[dict[str, object]] = []
    agent = qualification_agent(
        meta_model(model_id, settings.api_key.get_secret_value(), raw_bodies), search=search
    )
    prompt = SEARCH_PROMPT if search else SYNTHETIC_PROFILE_PROMPT
    usage_limits = UsageLimits(request_limit=1)

    async def call() -> CallReport:
        started = time.monotonic()
        facts: dict[str, object] = {"mode": "streaming" if stream else "non-streaming"}
        with capture_run_messages() as messages:
            try:
                if stream:
                    output = await _stream_output(agent, prompt, usage_limits, started, facts)
                else:
                    result = await agent.run(prompt, usage_limits=usage_limits)
                    output = result.output
                outcome = CallOutcome.OK
                facts["validated_output"] = output.model_dump()
                facts["output_type"] = type(output).__name__
            except ModelHTTPError as error:
                report = failure_from_http_error(error)
                report.facts = {**facts, "exception": type(error).__name__}
                return report
            except (UnexpectedModelBehavior, UsageLimitExceeded) as error:
                outcome = CallOutcome.FAILED
                facts["exception"] = type(error).__name__
        facts["elapsed_s"] = round(time.monotonic() - started, 2)
        facts["native_tool_calls"] = native_tool_calls(messages)
        facts.update(raw_billing_facts(raw_bodies))
        usage, reasoning, response_id = summarise_responses(messages)
        return CallReport(
            outcome=outcome,
            usage=usage,
            reasoning_tokens=reasoning,
            response_id=response_id,
            facts=facts,
        )

    worst_case = worst_case_cost_nano_usd(
        model_id,
        max_input_tokens=limits.max_input_tokens,
        max_output_tokens=limits.max_output_tokens,
        max_web_searches=limits.max_web_searches,
    )
    purpose = " + ".join(
        p
        for p, on in (("schema output", True), ("streaming", stream), ("web search", search))
        if on
    )
    return await run_guarded(
        Ledger(LEDGER_PATH),
        purpose=purpose,
        model_id=model_id,
        # Follows the model, not the flag: a test model configured as the production model
        # still counts against the production-call cap.
        is_production=settings.is_production_model(model_id),
        endpoint=RESPONSES_ENDPOINT,
        worst_case_nano_usd=worst_case,
        call=call,
    )


async def _stream_output(
    agent: Agent[None, BaseModel],
    prompt: str,
    usage_limits: UsageLimits,
    started: float,
    facts: dict[str, object],
) -> BaseModel:
    partials = 0
    first_partial_s: float | None = None
    async with agent.run_stream(prompt, usage_limits=usage_limits) as streamed:
        async for _ in streamed.stream_output(debounce_by=None):
            partials += 1
            if first_partial_s is None:
                first_partial_s = round(time.monotonic() - started, 2)
        output = await streamed.get_output()
    facts["partial_outputs"] = partials
    facts["first_partial_s"] = first_partial_s
    return output


def write_markdown(ledger: Ledger, path: Path = MARKDOWN_PATH) -> None:
    path.write_text(
        "# Live Meta usage log\n\n"
        "Every HTTP call to the Meta Model API made by Nessa tooling, including failures and\n"
        "free calls (ruling R5). Generated from `live-usage.jsonl` by\n"
        "`backend/spikes/meta/live_spike.py`; do not edit the table by hand.\n\n"
        f"- Prices: {PRICING_SOURCE} (checked {PRICING_CHECKED_ON}); costs are estimates from\n"
        "  reported usage, in USD before tax. `unknown` means the charge could not be determined;\n"
        "  the budget then counts the call's full reservation.\n"
        "- `In` includes cached tokens; `Out` includes reasoning tokens (Meta usage semantics).\n"
        "- `Searches` is Pydantic AI's billed count: Meta's `tool_usage` count if present, else\n"
        "  `search` actions. Whether Meta reports `tool_usage` for search calls was not captured,\n"
        "  and Meta does not document whether other actions (`open_page`, `find_in_page`) are\n"
        "  billed. An upper bound adds $0.0025 per uncounted `web_search_call` item (calls 5\n"
        "  and 7: one each; see the JSONL `notes`). Rows 3-5 predate raw-usage and action-type\n"
        "  capture in the tool; their request path was otherwise the same.\n"
        "- Remaining credit: not exposed by any documented Meta API endpoint; check the\n"
        "  developer dashboard.\n"
        f"- Budget `{BUDGET_SCOPE}`: at most {POLICY.max_calls} calls, "
        f"{POLICY.max_production_calls} on the production model, "
        f"{format_usd(POLICY.max_cost_nano_usd)} worst-case committed spend.\n\n"
        f"{ledger.render_markdown_table()}\n",
        encoding="utf-8",
    )


CHECKS = ("invalid-key", "list-models", "schema", "stream", "search", "stream-search")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=CHECKS)
    parser.add_argument(
        "--production-model",
        action="store_true",
        help="use the production model (counts against the production-call cap)",
    )
    args = parser.parse_args(argv)
    settings = MetaSettings()
    mode = "Standard" if not settings.test_model.endswith(CONTRIBUTOR_SUFFIX) else "Contributor"
    print(f"test model: {settings.test_model} ({mode}); production: {settings.production_model}")
    match args.check:
        case "invalid-key":
            asyncio.run(check_invalid_key(settings))
        case "list-models":
            asyncio.run(check_model_listing(settings))
        case _:
            asyncio.run(
                check_structured(
                    settings,
                    production=args.production_model,
                    stream=args.check in ("stream", "stream-search"),
                    search=args.check in ("search", "stream-search"),
                )
            )


if __name__ == "__main__":
    main()
