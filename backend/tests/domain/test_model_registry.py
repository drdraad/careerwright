import pytest

from careerwright.identity.model_choice import ModelChoice, ModelConfigurationError
from careerwright.identity.model_registry import (
    FIXTURE_MODEL_ID,
    PRICE_VERSION,
    Capability,
    ModelMode,
    UnknownModelError,
    Usage,
    estimate_cost_nano_usd,
    format_usd,
    model_entry,
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
    usage = Usage(input_tokens=0, cached_input_tokens=0, output_tokens=0, web_search_queries=3)

    assert estimate_cost_nano_usd("muse-spark-1.3", usage) == 7_500_000


def test_unpriced_model_is_refused_rather_than_costed_as_zero() -> None:
    with pytest.raises(UnknownModelError):
        estimate_cost_nano_usd("muse-spark-9.9", Usage(1, 0, 1))


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


@pytest.mark.req("MODEL-02")
@pytest.mark.parametrize(
    ("model_id", "mode"),
    [
        ("muse-spark-1.3", ModelMode.STANDARD),
        ("muse-spark-1.3-contributor", ModelMode.CONTRIBUTOR),
        ("muse-spark-1.2-contributor", ModelMode.CONTRIBUTOR),
        ("muse-wonder-1.0", ModelMode.STANDARD),
    ],
)
def test_every_registered_model_records_its_privacy_mode(model_id: str, mode: ModelMode) -> None:
    assert model_entry(model_id).mode is mode


@pytest.mark.req("MODEL-01")
def test_the_registry_records_capabilities_and_evaluation_only_where_a_call_established_them() -> (
    None
):
    production, test = model_entry("muse-spark-1.3"), model_entry("muse-spark-1.3-contributor")
    wonder = model_entry("muse-wonder-1.0")  # Task 3b: ledger rows 36-37, then cases 38-43

    for entry in (production, test, wonder):
        assert entry.capabilities == frozenset(Capability)  # schema, streaming, search: ADR 0003
        assert "ADR 0003" in entry.evaluation
    assert "rows 36-37" in wonder.evaluation
    for listed_only in ("muse-spark-1.2", "muse-spark-1.1"):
        entry = model_entry(listed_only)
        assert (entry.capabilities, entry.evaluation) == (frozenset(), "not evaluated")
    assert PRICE_VERSION == "meta-2026-10-27"


def test_the_fixture_interviewer_is_free_and_not_a_meta_model() -> None:
    fixture = model_entry(FIXTURE_MODEL_ID)

    assert fixture.mode is ModelMode.FIXTURE
    assert estimate_cost_nano_usd(FIXTURE_MODEL_ID, Usage(1_000, 0, 1_000)) == 0
    with pytest.raises(ModelConfigurationError, match="Meta model"):
        ModelChoice.configure(FIXTURE_MODEL_ID, "muse-spark-1.3", "test")
    with pytest.raises(ModelConfigurationError, match="Standard"):
        ModelChoice.configure("muse-spark-1.3-contributor", FIXTURE_MODEL_ID, "test")


@pytest.mark.parametrize(
    ("nano_usd", "expected"),
    [(0, "$0.000000"), (3_405_000, "$0.003405"), (1_500, "$0.000002"), (300_000_000, "$0.300000")],
)
def test_format_usd_rounds_half_up_to_micro_dollars(nano_usd: int, expected: str) -> None:
    assert format_usd(nano_usd) == expected
