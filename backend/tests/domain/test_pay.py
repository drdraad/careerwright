"""UK SOC 2020 mapping, modelled pay and the salary floor (ADR 0010; TAX1-02, TAX1-03,
TAX1-05, TAX1-06, JOB-05, DIV1-07). Pure rules; every figure synthetic."""

from datetime import date

import pytest

from nessa.catalogue.ashe import AshePeriod
from nessa.catalogue.pay import (
    FloorUnknown,
    FloorVerdict,
    MappingResolution,
    MappingReview,
    MappingReviewPack,
    ModelledPay,
    ModelledPayUnavailable,
    PayBenchmark,
    ReviewState,
    SalaryFloorRule,
    SocLink,
    StatedPay,
    committed_reviews,
    floor_counts,
    floor_verdict,
    modelled_floor_verdict,
    modelled_pay,
    uk_soc_mapping,
)
from tests.support.reference_data import DATA_ANALYST, LONDON, NORTH_WEST

LINKS = [SocLink("2135", "IT business analysts", 1), SocLink("3544", "Data analysts", 2)]
FLOOR = SalaryFloorRule(2_600_000, "year")


def review(soc_code: str = "3544") -> MappingReview:
    return MappingReview(
        esco_uri=DATA_ANALYST,
        soc_code=soc_code,
        reviewer="A. Reviewer (synthetic)",
        reviewed_on=date(2026, 10, 29),
        reasons="Synthetic review for a test.",
    )


def benchmark(region: str, period: AshePeriod, p90: int | None, soc: str = "3544") -> PayBenchmark:
    return PayBenchmark(
        soc_code=soc,
        soc_title="Data analysts",
        region_code=region,
        region_name="North West" if region == NORTH_WEST else "London",
        period=period,
        figures={"median": 3_000_000, "p90": p90},
        markers={} if p90 is not None else {"p90": "x"},
        jobs_thousands=None,
        median_cv=None,
    )


@pytest.mark.req("TAX1-02")
@pytest.mark.parametrize(
    ("links", "titles", "resolution", "proposed"),
    [
        ([], [], MappingResolution.NO_CANDIDATE, None),
        (LINKS[:1], [], MappingResolution.SINGLE_CANDIDATE, "2135"),
        (LINKS, ["3544"], MappingResolution.TITLE_RESOLVED, "3544"),
        (LINKS, [], MappingResolution.AMBIGUOUS, None),
        (LINKS, ["3544", "2135"], MappingResolution.AMBIGUOUS, None),
    ],
)
def test_every_candidate_stays_visible_and_only_a_single_title_narrows_them(
    links: list[SocLink], titles: list[str], resolution: MappingResolution, proposed: str | None
) -> None:
    mapping = uk_soc_mapping("2511", links, titles, None)

    assert mapping.resolution is resolution
    assert mapping.proposed_soc_code == proposed
    assert [c.soc_code for c in mapping.candidates] == sorted(
        (link.soc_code for link in links), key=lambda c: c != "3544"
    )  # most index entries first, none dropped
    assert mapping.review_state is ReviewState.UNREVIEWED
    assert mapping.reviewed_soc_code is None  # proposed is never reviewed


@pytest.mark.req("TAX1-03")
def test_only_a_reviewed_mapping_gives_modelled_pay_and_never_a_blend_of_codes() -> None:
    figures = [benchmark(NORTH_WEST, AshePeriod.YEAR, 5_200_000)]
    title_resolved = uk_soc_mapping("2511", LINKS, ["3544"], None)
    reviewed = uk_soc_mapping("2511", LINKS, ["3544"], review())
    not_a_candidate = uk_soc_mapping("2511", LINKS, [], review("9999"))

    assert modelled_pay(title_resolved, [NORTH_WEST], figures) is (
        ModelledPayUnavailable.NO_REVIEWED_MAPPING
    )
    assert not_a_candidate.review_state is ReviewState.REVIEW_NOT_A_CANDIDATE
    assert modelled_pay(not_a_candidate, [NORTH_WEST], figures) is (
        ModelledPayUnavailable.NO_REVIEWED_MAPPING
    )
    other_code = benchmark(NORTH_WEST, AshePeriod.YEAR, 1, "2135")
    found = modelled_pay(reviewed, [NORTH_WEST], [*figures, other_code])
    assert isinstance(found, ModelledPay)
    assert found.soc_code == "3544"
    assert [b.soc_code for b in found.benchmarks] == ["3544"]  # the other code's figure unused
    assert modelled_pay(reviewed, [], figures) is ModelledPayUnavailable.NO_WORK_AREA
    assert modelled_pay(reviewed, [LONDON], figures) is ModelledPayUnavailable.NOT_PUBLISHED


@pytest.mark.req("TAX1-06")
def test_a_benchmark_is_regional_and_says_what_pay_it_is() -> None:
    shown = benchmark(NORTH_WEST, AshePeriod.YEAR, 5_200_000)

    assert shown.geography == "region"
    assert "full-time" in shown.pay_definition
    assert "annual" in shown.pay_definition.casefold()


def test_the_committed_review_pack_is_empty_until_an_accountable_reviewer_exists() -> None:
    pack = committed_reviews()

    assert pack.reviews == []  # H-10: not run, requires a human
    with pytest.raises(ValueError, match="once"):
        MappingReviewPack(pack_version="x", dated=date(2026, 10, 29), reviews=[review(), review()])


@pytest.mark.req("DIV1-07", "JOB-05")
@pytest.mark.parametrize(
    ("stated", "verdict", "reason"),
    [
        ([StatedPay("advertised", "GBP", "year", 2_500_000)], FloorVerdict.BELOW, None),
        ([StatedPay("advertised", "GBP", "year", 2_600_000)], FloorVerdict.MEETS, None),
        # A range is below only when its top is: the highest stated amount decides.
        (
            [StatedPay("advertised", "GBP", "year", 2_400_000),
             StatedPay("advertised", "GBP", "year", 2_700_000)],
            FloorVerdict.MEETS,
            None,
        ),
        ([StatedPay("predicted", "GBP", "year", 1_000_000)], FloorVerdict.UNKNOWN,
         FloorUnknown.PREDICTED),
        ([StatedPay("advertised", "GBP", "hour", 1_200)], FloorVerdict.UNKNOWN,
         FloorUnknown.PERIOD_DIFFERS),
        ([StatedPay("advertised", "GBP", None, 1_000_000)], FloorVerdict.UNKNOWN,
         FloorUnknown.PERIOD_NOT_STATED),
        ([StatedPay("advertised", "EUR", "year", 1_000_000)], FloorVerdict.UNKNOWN,
         FloorUnknown.OTHER_CURRENCY),
        ([], FloorVerdict.UNKNOWN, FloorUnknown.NO_PAY),
        # Advertised pay in the floor's period decides over a provider's prediction.
        (
            [StatedPay("predicted", "GBP", "year", 9_000_000),
             StatedPay("advertised", "GBP", "year", 2_000_000)],
            FloorVerdict.BELOW,
            None,
        ),
    ],
)  # fmt: skip
def test_only_stated_gbp_pay_in_the_floor_s_period_can_be_below_it(
    stated: list[StatedPay], verdict: FloorVerdict, reason: FloorUnknown | None
) -> None:
    assert floor_verdict(FLOOR, stated) == (verdict, reason)


@pytest.mark.req("DIV1-07", "TAX1-06")
def test_modelled_pay_is_below_the_floor_only_in_every_region_and_on_the_published_90th() -> None:
    reviewed = uk_soc_mapping("2511", LINKS, [], review())
    low_nw = benchmark(NORTH_WEST, AshePeriod.YEAR, 2_500_000)
    high_ldn = benchmark(LONDON, AshePeriod.YEAR, 6_400_000)
    withheld_ldn = benchmark(LONDON, AshePeriod.YEAR, None)

    def verdict(
        regions: list[str], figures: list[PayBenchmark], floor: SalaryFloorRule = FLOOR
    ) -> tuple[FloorVerdict, FloorUnknown | None]:
        return modelled_floor_verdict(floor, modelled_pay(reviewed, regions, figures), regions)

    assert verdict([NORTH_WEST], [low_nw]) == (FloorVerdict.BELOW, None)
    assert verdict([NORTH_WEST, LONDON], [low_nw, high_ldn]) == (FloorVerdict.MEETS, None)
    assert verdict([NORTH_WEST, LONDON], [low_nw, withheld_ldn]) == (
        FloorVerdict.UNKNOWN,
        FloorUnknown.NOT_PUBLISHED,
    )
    assert verdict([NORTH_WEST], [low_nw], SalaryFloorRule(200_000, "month")) == (
        FloorVerdict.UNKNOWN,
        FloorUnknown.PERIOD_DIFFERS,  # ASHE has no monthly table; nothing is converted
    )
    unreviewed = uk_soc_mapping("2511", LINKS, ["3544"], None)
    assert modelled_floor_verdict(
        FLOOR, modelled_pay(unreviewed, [NORTH_WEST], [low_nw]), [NORTH_WEST]
    ) == (FloorVerdict.UNKNOWN, FloorUnknown.NO_REVIEWED_MAPPING)


@pytest.mark.req("DIV1-07")
def test_the_floor_s_counts_explain_what_it_left_out_and_why_the_rest_was_kept() -> None:
    counts = floor_counts(
        FLOOR,
        [
            (FloorVerdict.BELOW, None),
            (FloorVerdict.MEETS, None),
            (FloorVerdict.UNKNOWN, FloorUnknown.PREDICTED),
            (FloorVerdict.UNKNOWN, FloorUnknown.PREDICTED),
            (FloorVerdict.UNKNOWN, FloorUnknown.NO_PAY),
        ],
    )

    assert (counts.left_out, counts.meets, counts.kept_unknown) == (1, 1, 3)
    assert counts.unknown == {FloorUnknown.NO_PAY: 1, FloorUnknown.PREDICTED: 2}
