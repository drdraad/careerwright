"""Meta Model API price table and cost estimation in integer nano-USD.

Meta bills in USD per million tokens. One nano-USD per token is $1 per billion tokens, so
every published rate is an exact integer here and no float ever touches a cost.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

PRICING_SOURCE = "https://dev.meta.ai/docs/pricing-rate-limits"
PRICING_CHECKED_ON = "2026-10-27"

NANO_USD_PER_USD = 1_000_000_000
WEB_SEARCH_NANO_USD_PER_QUERY = 2_500_000  # $2.50 per 1,000 queries


@dataclass(frozen=True)
class TokenPrice:
    input_nano_usd_per_token: int
    cached_input_nano_usd_per_token: int
    output_nano_usd_per_token: int


_STANDARD_SPARK = TokenPrice(1_250, 150, 4_250)  # $1.25 / $0.15 cached / $4.25 per M
_CONTRIBUTOR_SPARK = TokenPrice(100, 2, 200)  # $0.10 / $0.002 cached / $0.20 per M

PRICES: dict[str, TokenPrice] = {
    "muse-spark-1.3": _STANDARD_SPARK,
    "muse-spark-1.2": _STANDARD_SPARK,
    "muse-spark-1.1": _STANDARD_SPARK,
    "muse-spark-1.3-contributor": _CONTRIBUTOR_SPARK,
    "muse-spark-1.2-contributor": _CONTRIBUTOR_SPARK,
    "muse-wonder-1.0": TokenPrice(4_000, 200, 20_000),
}


class UnknownModelPriceError(KeyError):
    """No published price is recorded for the model, so its cost cannot be estimated."""


@dataclass(frozen=True)
class Usage:
    """Billable units reported for one call.

    `input_tokens` includes cached tokens (Meta's Responses usage object counts cached
    tokens inside `input_tokens`); `output_tokens` includes reasoning tokens.
    """

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


def _price(model_id: str) -> TokenPrice:
    try:
        return PRICES[model_id]
    except KeyError:
        raise UnknownModelPriceError(model_id) from None


def estimate_cost_nano_usd(model_id: str, usage: Usage) -> int:
    price = _price(model_id)
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
    """Upper bound used to reserve budget before a call; no input is assumed cached."""
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
