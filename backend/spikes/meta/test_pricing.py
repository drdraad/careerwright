import pytest

from spikes.meta.pricing import (
    UnknownModelPriceError,
    Usage,
    estimate_cost_nano_usd,
    format_usd,
    worst_case_cost_nano_usd,
)


def test_standard_spark_cost_is_exact_integer_nano_usd() -> None:
    # Hand check against https://dev.meta.ai/docs/pricing-rate-limits (2026-10-27):
    # 1,000 uncached input x $1.25/M = $0.00125; 200 cached x $0.15/M = $0.00003;
    # 500 output x $4.25/M = $0.002125. Total $0.003405.
    usage = Usage(input_tokens=1_200, cached_input_tokens=200, output_tokens=500)

    assert estimate_cost_nano_usd("muse-spark-1.3", usage) == 3_405_000


def test_contributor_spark_cost_uses_contributor_rates() -> None:
    # 1,000,000 uncached input x $0.10/M + 1,000,000 output x $0.20/M = $0.30.
    usage = Usage(input_tokens=1_000_000, cached_input_tokens=0, output_tokens=1_000_000)

    assert estimate_cost_nano_usd("muse-spark-1.3-contributor", usage) == 300_000_000


def test_web_search_queries_add_per_query_charge() -> None:
    # $2.50 per 1,000 queries = $0.0025 each, on top of tokens.
    usage = Usage(input_tokens=0, cached_input_tokens=0, output_tokens=0, web_search_queries=3)

    assert estimate_cost_nano_usd("muse-spark-1.3", usage) == 7_500_000


def test_unpriced_model_is_refused_rather_than_costed_as_zero() -> None:
    usage = Usage(input_tokens=1, cached_input_tokens=0, output_tokens=1)

    with pytest.raises(UnknownModelPriceError):
        estimate_cost_nano_usd("muse-spark-9.9", usage)


def test_cached_tokens_cannot_exceed_input_tokens() -> None:
    with pytest.raises(ValueError, match="cached"):
        Usage(input_tokens=10, cached_input_tokens=11, output_tokens=0)


def test_negative_usage_is_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        Usage(input_tokens=-1, cached_input_tokens=0, output_tokens=0)


def test_worst_case_assumes_every_input_token_is_uncached() -> None:
    # 10,000 x $1.25/M ($0.0125) + 2,000 x $4.25/M ($0.0085) + 2 x $0.0025 ($0.005) = $0.026.
    worst = worst_case_cost_nano_usd(
        "muse-spark-1.3", max_input_tokens=10_000, max_output_tokens=2_000, max_web_searches=2
    )

    assert worst == 26_000_000


@pytest.mark.parametrize(
    ("nano_usd", "expected"),
    [(0, "$0.000000"), (3_405_000, "$0.003405"), (1_500, "$0.000002"), (300_000_000, "$0.300000")],
)
def test_format_usd_rounds_half_up_to_micro_dollars(nano_usd: int, expected: str) -> None:
    assert format_usd(nano_usd) == expected
