"""Pay evidence for an occupation, and the salary floor (spec sections 4 and 5; TAX1-02,
TAX1-03, TAX1-05, TAX1-06, JOB-05, DIV1-07; ADR 0010). Pure: the store reads, this decides.

UK SOC 2020 mapping. An ESCO occupation names one ISCO-08 unit group; ONS's coding index
links that group to every SOC 2020 unit group one of its job titles is coded to. Careerwright keeps
all of them (`candidates`) and narrows them only by an exact title: an ESCO label that is an
index title within exactly one candidate (`title_resolved`). Nothing here is a reviewed
mapping: only an accountable reviewer's decision, recorded in the mapping review pack, makes
one (`reviewed`, human gate H-10), and only a reviewed mapping gives modelled pay, so one
ISCO group's ASHE figure is never given to every ESCO occupation in it and no median is
averaged across a many-to-many mapping (TAX1-03).

ASHE figures keep their geography, a work region, never a city (TAX1-06), their period and
pay definition, and ONS's marker where a figure is withheld. One snapshot is not a trend
(TAX1-05): the trend is always `unavailable` with `single_snapshot`.

The salary floor (H-11 item 4) is a hard filter: something is left out only when the
highest pay it states, in the floor's period and in GBP, is below the floor. Pay that is
unknown, predicted by a provider, in another period (never converted: annualising needs
hours) or not published is never below it; each such case is counted with its reason.
"""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careerwright.catalogue.ashe import PAY_DEFINITION, AshePeriod, Reliability, reliability

# The ASHE figure a floor is compared with: the 90th percentile, the highest ONS publishes.
# An occupation is below a floor only when nine in ten of its full-time jobs in the region
# pay less (provisional product decision, R6: never remove a career most of whose jobs pay
# less but some pay enough).
FLOOR_STATISTIC = "p90"


class MappingResolution(StrEnum):
    NO_CANDIDATE = "no_candidate"  # the index codes no job title of the ISCO group
    SINGLE_CANDIDATE = "single_candidate"  # the index links the group to one unit group
    TITLE_RESOLVED = "title_resolved"  # an ESCO label is an index title in one candidate
    AMBIGUOUS = "ambiguous"  # several candidates and no single title match


class ReviewState(StrEnum):
    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    # A recorded review names a unit group the index does not link the occupation's ISCO
    # group to: it is not applied, and the mapping stays unreviewed for pay.
    REVIEW_NOT_A_CANDIDATE = "review_not_a_candidate"


class MappingReview(BaseModel):
    """An accountable reviewer's decision on one ESCO occupation's UK SOC 2020 unit group
    (human gate H-10): data entry, never a model's output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    esco_uri: str = Field(pattern=r"^http://data\.europa\.eu/esco/occupation/[0-9a-f-]{36}$")
    soc_code: str = Field(pattern=r"^[0-9]{4}$")
    reviewer: str = Field(min_length=1, max_length=120)
    reviewed_on: date
    reasons: str = Field(min_length=1, max_length=2000)


class MappingReviewPack(BaseModel):
    """The pinned, dated pack of reviewed mappings (committed; empty until a reviewer
    exists)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pack_version: str = Field(min_length=1, max_length=40)
    dated: date
    reviews: list[MappingReview]

    @model_validator(mode="after")
    def _one_per_occupation(self) -> "MappingReviewPack":
        uris = [r.esco_uri for r in self.reviews]
        if len(set(uris)) != len(uris):
            raise ValueError("a mapping review pack reviews one occupation once")
        return self

    def review_of(self, esco_uri: str) -> MappingReview | None:
        return next((r for r in self.reviews if r.esco_uri == esco_uri), None)


REVIEW_PACK = Path(__file__).parent / "packs" / "uk_soc_mapping_reviews.json"


def committed_reviews() -> MappingReviewPack:
    return MappingReviewPack.model_validate(json.loads(REVIEW_PACK.read_text(encoding="utf-8")))


@dataclass(frozen=True)
class SocLink:
    """What the coding index says about one SOC 2020 unit group for an ISCO-08 group."""

    soc_code: str
    title: str
    index_entries: int  # job titles of the ISCO group the index codes to this unit group


@dataclass(frozen=True)
class SocCandidate:
    soc_code: str
    title: str
    index_entries: int
    title_match: bool  # an ESCO label is one of this unit group's index titles


@dataclass(frozen=True)
class UkSocMapping:
    isco_code: str
    resolution: MappingResolution
    candidates: tuple[SocCandidate, ...]  # every candidate, most index entries first
    proposed_soc_code: str | None  # the single or title-resolved candidate: not reviewed
    review: MappingReview | None
    review_state: ReviewState

    @property
    def reviewed_soc_code(self) -> str | None:
        if self.review is None or self.review_state is not ReviewState.REVIEWED:
            return None
        return self.review.soc_code


def uk_soc_mapping(
    isco_code: str,
    links: Iterable[SocLink],
    title_matches: Iterable[str],
    review: MappingReview | None,
) -> UkSocMapping:
    """`title_matches`: the unit groups among `links` with an index title equal to one of
    the occupation's ESCO labels (normalised)."""
    matched = set(title_matches)
    candidates = tuple(
        SocCandidate(link.soc_code, link.title, link.index_entries, link.soc_code in matched)
        for link in sorted(links, key=lambda link: (-link.index_entries, link.soc_code))
    )
    codes = {c.soc_code for c in candidates}
    titled = [c.soc_code for c in candidates if c.title_match]
    if not candidates:
        resolution, proposed = MappingResolution.NO_CANDIDATE, None
    elif len(candidates) == 1:
        resolution, proposed = MappingResolution.SINGLE_CANDIDATE, candidates[0].soc_code
    elif len(titled) == 1:
        resolution, proposed = MappingResolution.TITLE_RESOLVED, titled[0]
    else:
        resolution, proposed = MappingResolution.AMBIGUOUS, None
    if review is None:
        state = ReviewState.UNREVIEWED
    elif review.soc_code in codes:
        state = ReviewState.REVIEWED
    else:
        state = ReviewState.REVIEW_NOT_A_CANDIDATE
    return UkSocMapping(isco_code, resolution, candidates, proposed, review, state)


@dataclass(frozen=True)
class PayBenchmark:
    """One ASHE estimate as shown: an official pay benchmark for a SOC 2020 unit group in a
    work region, never a city's or a job's pay."""

    soc_code: str
    soc_title: str
    region_code: str
    region_name: str
    period: AshePeriod
    figures: Mapping[str, int | None]  # statistic -> pence; None when ONS withholds it
    markers: Mapping[str, str]  # statistic -> ONS's marker for a withheld value
    jobs_thousands: Decimal | None
    cvs: Mapping[str, Decimal | None]  # statistic -> its own coefficient of variation (%)
    geography: str = "region"

    def reliability(self, statistic: str) -> Reliability:
        """ONS's quality band for one statistic, from its own CV (fix round 1, review A M4):
        a withheld value marked `x` is unreliable, any other withheld value unknown."""
        if self.figures.get(statistic) is None:
            withheld = self.markers.get(statistic) == "x"
            return Reliability.UNRELIABLE if withheld else Reliability.UNKNOWN
        return reliability(self.cvs.get(statistic))

    @property
    def pay_definition(self) -> str:
        return PAY_DEFINITION[self.period]


class ModelledPayUnavailable(StrEnum):
    """Why an occupation has no modelled pay (it is then unknown, never zero)."""

    NO_REVIEWED_MAPPING = "no_reviewed_mapping"
    NO_WORK_AREA = "no_work_area"  # the person named no city, so no region
    NOT_PUBLISHED = "not_published"  # ASHE has no estimate for the code and region


class TrendState(StrEnum):
    UNAVAILABLE = "unavailable"


class TrendReason(StrEnum):
    SINGLE_SNAPSHOT = "single_snapshot"  # one ASHE release is held: no comparable history


@dataclass(frozen=True)
class ModelledPay:
    """Pay for the occupation from ASHE through its reviewed mapping: `modelled`, distinct
    from advertised and provider-predicted pay (JOB-05), and regional, never a city's."""

    soc_code: str
    benchmarks: tuple[PayBenchmark, ...]


def modelled_pay(
    mapping: UkSocMapping, region_codes: Iterable[str], benchmarks: Iterable[PayBenchmark]
) -> ModelledPay | ModelledPayUnavailable:
    soc_code = mapping.reviewed_soc_code
    if soc_code is None:
        return ModelledPayUnavailable.NO_REVIEWED_MAPPING
    regions = set(region_codes)
    if not regions:
        return ModelledPayUnavailable.NO_WORK_AREA
    found = tuple(
        b
        for b in sorted(benchmarks, key=lambda b: (b.region_code, b.period))
        if b.soc_code == soc_code and b.region_code in regions
    )
    return ModelledPay(soc_code, found) if found else ModelledPayUnavailable.NOT_PUBLISHED


# --- the salary floor --------------------------------------------------------------------


class FloorVerdict(StrEnum):
    BELOW = "below"  # left out: the highest pay stated is below the floor
    MEETS = "meets"
    UNKNOWN = "unknown"  # kept: never treated as below the floor


class FloorUnknown(StrEnum):
    """Why pay could not be compared with the floor; each is kept, and counted."""

    NO_PAY = "no_pay"  # no pay stated
    # A minimum with no maximum ("from £24,000", "£24,000+"): where pay ends is not stated
    # (fix round 1, review A I1).
    NO_UPPER_AMOUNT = "no_upper_amount"
    PREDICTED = "predicted"  # a provider's estimate, never the advertiser's own figure
    BASIS_UNKNOWN = "basis_unknown"  # stated, but not said to be advertised or predicted
    PERIOD_DIFFERS = "period_differs"  # another period: never converted
    PERIOD_NOT_STATED = "period_not_stated"
    OTHER_CURRENCY = "other_currency"
    NO_REVIEWED_MAPPING = "no_reviewed_mapping"  # an occupation without reviewed UK SOC
    NO_WORK_AREA = "no_work_area"
    NOT_PUBLISHED = "not_published"  # ASHE withholds the figure the floor is compared with


@dataclass(frozen=True)
class SalaryFloorRule:
    """The person's floor as they gave it: gross, in GBP pence, per a period."""

    minor_units: int
    period: str  # "year", "month", "week" or "hour"


@dataclass(frozen=True)
class StatedPay:
    """Pay as a source states it, for the floor: its basis, currency, period and amounts. One
    amount is both its minimum and maximum; a minimum with no maximum is open above ("from
    £24,000"); a maximum with no minimum is "up to"."""

    basis: str  # "advertised", "predicted" or "unknown"
    currency: str
    period: str | None
    minimum_minor_units: int | None
    maximum_minor_units: int | None


def _against(floor: SalaryFloorRule, pay: StatedPay) -> FloorVerdict:
    """One comparable amount: its stated maximum decides; with none, its minimum can only
    show that it meets the floor, never that it is below it."""
    if pay.maximum_minor_units is not None:
        below = pay.maximum_minor_units < floor.minor_units
        return FloorVerdict.BELOW if below else FloorVerdict.MEETS
    if pay.minimum_minor_units is not None and pay.minimum_minor_units >= floor.minor_units:
        return FloorVerdict.MEETS
    return FloorVerdict.UNKNOWN


def floor_verdict(
    floor: SalaryFloorRule, stated: Iterable[StatedPay]
) -> tuple[FloorVerdict, FloorUnknown | None]:
    """One job's pay (all its copies) against the floor: advertised GBP pay in the floor's
    period decides. Any copy that meets it keeps the job; a copy open above (a minimum with
    no maximum) keeps it as unknown; only stated maxima, all below, leave it out. Anything
    else is unknown with its reason."""
    pays = list(stated)
    advertised = [p for p in pays if p.basis == "advertised"]
    comparable = [p for p in advertised if p.currency == "GBP" and p.period == floor.period]
    if comparable:
        verdicts = {_against(floor, p) for p in comparable}
        if FloorVerdict.MEETS in verdicts:
            return FloorVerdict.MEETS, None
        if FloorVerdict.UNKNOWN in verdicts:
            return FloorVerdict.UNKNOWN, FloorUnknown.NO_UPPER_AMOUNT
        return FloorVerdict.BELOW, None
    if any(p.currency != "GBP" for p in advertised):
        return FloorVerdict.UNKNOWN, FloorUnknown.OTHER_CURRENCY
    if any(p.period is not None for p in advertised):
        return FloorVerdict.UNKNOWN, FloorUnknown.PERIOD_DIFFERS
    if advertised:
        return FloorVerdict.UNKNOWN, FloorUnknown.PERIOD_NOT_STATED
    if any(p.basis == "predicted" for p in pays):
        return FloorVerdict.UNKNOWN, FloorUnknown.PREDICTED
    if pays:
        return FloorVerdict.UNKNOWN, FloorUnknown.BASIS_UNKNOWN
    return FloorVerdict.UNKNOWN, FloorUnknown.NO_PAY


def modelled_floor_verdict(
    floor: SalaryFloorRule,
    modelled: ModelledPay | ModelledPayUnavailable,
    region_codes: Iterable[str],
) -> tuple[FloorVerdict, FloorUnknown | None]:
    """An occupation against the floor through its modelled pay: below only when, in every
    region of the person's cities, ASHE's 90th percentile for the floor's period is below
    it. A region whose figure is withheld, or a period ASHE has no table for (a month),
    keeps it."""
    if isinstance(modelled, ModelledPayUnavailable):
        return FloorVerdict.UNKNOWN, FloorUnknown(modelled.value)
    if floor.period not in {p.value for p in AshePeriod}:
        return FloorVerdict.UNKNOWN, FloorUnknown.PERIOD_DIFFERS
    in_period = {b.region_code: b for b in modelled.benchmarks if b.period == floor.period}
    figures = [
        in_period[r].figures.get(FLOOR_STATISTIC) if r in in_period else None
        for r in sorted(set(region_codes))
    ]
    if not figures or any(f is None for f in figures):
        return FloorVerdict.UNKNOWN, FloorUnknown.NOT_PUBLISHED
    # ASHE's own figure against the floor, never through the advertised-pay rule (fix round
    # 1, review A M6): modelled pay is not advertised pay.
    if all(f is not None and f < floor.minor_units for f in figures):
        return FloorVerdict.BELOW, None
    return FloorVerdict.MEETS, None


@dataclass(frozen=True)
class FloorCounts:
    """What the floor did, in counts: what it left out, what met it, and what it kept
    because the pay could not be compared, by reason."""

    floor: SalaryFloorRule
    left_out: int
    meets: int
    unknown: Mapping[FloorUnknown, int]

    @property
    def kept_unknown(self) -> int:
        return sum(self.unknown.values())


def floor_counts(
    floor: SalaryFloorRule, verdicts: Iterable[tuple[FloorVerdict, FloorUnknown | None]]
) -> FloorCounts:
    left_out = meets = 0
    unknown: dict[FloorUnknown, int] = {}
    for verdict, reason in verdicts:
        if verdict is FloorVerdict.BELOW:
            left_out += 1
        elif verdict is FloorVerdict.MEETS:
            meets += 1
        elif reason is not None:
            unknown[reason] = unknown.get(reason, 0) + 1
    return FloorCounts(floor, left_out, meets, dict(sorted(unknown.items())))
