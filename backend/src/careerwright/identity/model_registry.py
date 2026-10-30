"""Registry of the models Careerwright may call (spec section 16, MODEL-01): exact ID, privacy mode,
published price and its version, qualified capabilities and evaluation status.

Costs are integer nano-USD. Meta bills in USD per million tokens, so one nano-USD per token is
$1 per billion tokens: every published rate is an exact integer and no float touches a cost.
Contributor models let Meta train on traffic; they are for synthetic or public inputs only
(ADR 0003), which `careerwright.identity.model_choice` enforces when a run is submitted and the
activity checks again before the call. The fixture interviewer is not a provider model: it
answers demo workspaces only, deterministically and offline.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

PRICE_SOURCE = "https://dev.meta.ai/docs/pricing-rate-limits"
PRICE_VERSION = "meta-2026-10-27"

NANO_USD_PER_USD = 1_000_000_000
WEB_SEARCH_NANO_USD_PER_QUERY = 2_500_000  # $2.50 per 1,000 queries


class ModelMode(StrEnum):
    STANDARD = "standard"
    CONTRIBUTOR = "contributor"
    # Careerwright's deterministic stand-in for demo workspaces: no provider, no key, no network,
    # no cost. Its proposals are labelled synthetic and pass the same validation.
    FIXTURE = "fixture"


@dataclass(frozen=True)
class TokenPrice:
    input_nano_usd_per_token: int
    cached_input_nano_usd_per_token: int
    output_nano_usd_per_token: int


class Capability(StrEnum):
    SCHEMA_OUTPUT = "schema_output"  # strict JSON-schema output (`NativeOutput`)
    STREAMING = "streaming"
    WEB_SEARCH = "web_search"


@dataclass(frozen=True)
class ModelEntry:
    model_id: str
    mode: ModelMode
    price: TokenPrice
    # Capabilities established on this exact ID by a recorded live call, and where; a model
    # listed but never called has none (being listed does not prove it can be called).
    capabilities: frozenset[Capability] = frozenset()
    evaluation: str = "not evaluated"


_STANDARD_SPARK = TokenPrice(1_250, 150, 4_250)  # $1.25 / $0.15 cached / $4.25 per M
_CONTRIBUTOR_SPARK = TokenPrice(100, 2, 200)  # $0.10 / $0.002 cached / $0.20 per M
_SPARK_1_3 = frozenset(Capability)
FIXTURE_MODEL_ID = "careerwright-fixture-interviewer-1"
FIXTURE_DISCOVERY_MODEL_ID = "careerwright-fixture-discovery-1"
FIXTURE_EXPLAINER_MODEL_ID = "careerwright-fixture-explainer-1"

_REGISTRY = {
    entry.model_id: entry
    for entry in (
        ModelEntry(
            "muse-spark-1.3",
            ModelMode.STANDARD,
            _STANDARD_SPARK,
            _SPARK_1_3,
            "production: qualified, ADR 0003 (ledger calls 6-7)",
        ),
        ModelEntry("muse-spark-1.2", ModelMode.STANDARD, _STANDARD_SPARK),
        ModelEntry("muse-spark-1.1", ModelMode.STANDARD, _STANDARD_SPARK),
        ModelEntry(
            "muse-spark-1.3-contributor",
            ModelMode.CONTRIBUTOR,
            _CONTRIBUTOR_SPARK,
            _SPARK_1_3,
            "test model, synthetic data only: qualified, ADR 0003 (ledger calls 3-5, 8, 10)",
        ),
        ModelEntry("muse-spark-1.2-contributor", ModelMode.CONTRIBUTOR, _CONTRIBUTOR_SPARK),
        ModelEntry("muse-wonder-1.0", ModelMode.STANDARD, TokenPrice(4_000, 200, 20_000)),
        ModelEntry(
            FIXTURE_MODEL_ID,
            ModelMode.FIXTURE,
            TokenPrice(0, 0, 0),
            frozenset({Capability.SCHEMA_OUTPUT}),
            "deterministic demo interviewer; tested offline (ADR 0006)",
        ),
        ModelEntry(
            FIXTURE_DISCOVERY_MODEL_ID,
            ModelMode.FIXTURE,
            TokenPrice(0, 0, 0),
            frozenset({Capability.SCHEMA_OUTPUT}),
            "deterministic demo query proposer; tested offline (ADR 0007)",
        ),
        ModelEntry(
            FIXTURE_EXPLAINER_MODEL_ID,
            ModelMode.FIXTURE,
            TokenPrice(0, 0, 0),
            frozenset({Capability.SCHEMA_OUTPUT}),
            "deterministic demo explainer; tested offline (ADR 0007 decision 12)",
        ),
    )
}


class UnknownModelError(KeyError):
    """No published price or mode is recorded for the model, so it cannot be used."""


def model_entry(model_id: str) -> ModelEntry:
    try:
        return _REGISTRY[model_id]
    except KeyError:
        raise UnknownModelError(model_id) from None


@dataclass(frozen=True)
class Usage:
    """Billable units of one call. `input_tokens` includes cached tokens and `output_tokens`
    includes reasoning tokens (Meta's Responses usage semantics)."""

    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    web_search_queries: int = 0

    def __post_init__(self) -> None:
        counts = (
            self.input_tokens,
            self.cached_input_tokens,
            self.output_tokens,
            self.web_search_queries,
        )
        if min(counts) < 0:
            raise ValueError("usage counts cannot be negative")
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError("cached input tokens cannot exceed input tokens")


def estimate_cost_nano_usd(model_id: str, usage: Usage) -> int:
    price = model_entry(model_id).price
    uncached = usage.input_tokens - usage.cached_input_tokens
    return (
        uncached * price.input_nano_usd_per_token
        + usage.cached_input_tokens * price.cached_input_nano_usd_per_token
        + usage.output_tokens * price.output_nano_usd_per_token
        + usage.web_search_queries * WEB_SEARCH_NANO_USD_PER_QUERY
    )


def worst_case_cost_nano_usd(
    model_id: str, *, max_input_tokens: int, max_output_tokens: int, max_web_searches: int
) -> int:
    """Upper bound reserved before a call; no input is assumed cached."""
    return estimate_cost_nano_usd(
        model_id,
        Usage(
            input_tokens=max_input_tokens,
            cached_input_tokens=0,
            output_tokens=max_output_tokens,
            web_search_queries=max_web_searches,
        ),
    )


def format_usd(nano_usd: int) -> str:
    dollars = (Decimal(nano_usd) / NANO_USD_PER_USD).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )
    return f"${dollars}"
