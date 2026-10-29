"""API contract for an occupation's pay and AI evidence (ADR 0010; spec section 5).

Every figure says what it is and where it comes from: an ASHE benchmark is a SOC 2020 unit
group's in a work region (never a city's or a job's pay), modelled pay exists only through
a reviewed UK SOC mapping, the trend is unavailable from one snapshot, AI exposure and
observed use are shown as their sources measure them, and the AI Resilience Score is a
reviewed range or unscored, never derived from them.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field

from nessa.api.schemas import ResponseModel
from nessa.catalogue.ai_evidence import ExposureGradient, MatchType
from nessa.catalogue.ai_resilience import (
    BAND_WORDS,
    HORIZON_YEARS,
    LABEL,
    MEANING,
    METHOD_VERSION,
    Assessment,
    AssessmentState,
    Band,
    UnscoredReason,
)
from nessa.catalogue.ashe import STATISTICS, AshePeriod, Marker, Reliability
from nessa.catalogue.pay import (
    MappingResolution,
    ModelledPay,
    ModelledPayUnavailable,
    PayBenchmark,
    ReviewState,
    TrendReason,
    TrendState,
)
from nessa.catalogue.places import region_name
from nessa.catalogue.reference import OccupationEvidence, OnetMatch
from nessa.catalogue.reference_store import ReferenceRelease
from nessa.money import Money

ILO_MEASURE = (
    "Technical potential of generative AI to perform the ISCO-08 group's tasks, 0 to 1 (the "
    "mean and spread of its task scores): never a prediction of job loss, and the group's, "
    "not this occupation's alone."
)
OBSERVED_USE_MEASURE = (
    "Each task's share of the Claude conversations the Anthropic Economic Index mapped to "
    "tasks: observed use, not replacement. A task the release did not observe is not "
    "observed, never zero, and never protection."
)


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _money(pence: int | None) -> Money | None:
    return None if pence is None else Money(minor_units=pence, currency="GBP")


class Statistic(StrEnum):
    MEDIAN = "median"
    MEAN = "mean"
    P10 = "p10"
    P20 = "p20"
    P25 = "p25"
    P30 = "p30"
    P40 = "p40"
    P60 = "p60"
    P70 = "p70"
    P75 = "p75"
    P80 = "p80"
    P90 = "p90"


class PayStatisticOut(ResponseModel):
    statistic: Statistic
    amount: Money | None = Field(description="Gross pay; null when ONS withholds it.")
    withheld: Marker | None = Field(description="ONS's marker for a withheld value.")


class PayBenchmarkOut(ResponseModel):
    """An official pay benchmark (ONS ASHE): a unit group's pay in a work region."""

    soc_code: str
    soc_title: str
    region_code: str
    region_name: str
    geography: Literal["region"] = Field(description="Regional, never a city's figure.")
    population: Literal["full_time"]
    period: AshePeriod
    pay_definition: str
    jobs_thousands: str | None
    median_cv: str | None = Field(description="Coefficient of variation of the median, %.")
    reliability: Reliability
    statistics: list[PayStatisticOut]

    @classmethod
    def of(cls, benchmark: PayBenchmark) -> "PayBenchmarkOut":
        return cls(
            soc_code=benchmark.soc_code,
            soc_title=benchmark.soc_title,
            region_code=benchmark.region_code,
            region_name=benchmark.region_name,
            geography="region",
            population="full_time",
            period=benchmark.period,
            pay_definition=benchmark.pay_definition,
            jobs_thousands=_decimal(benchmark.jobs_thousands),
            median_cv=_decimal(benchmark.median_cv),
            reliability=benchmark.reliability,
            statistics=[
                PayStatisticOut(
                    statistic=Statistic(name),
                    amount=_money(benchmark.figures.get(name)),
                    withheld=Marker(benchmark.markers[name]) if name in benchmark.markers else None,
                )
                for name in STATISTICS
            ],
        )


class SocCandidateOut(ResponseModel):
    soc_code: str
    title: str
    index_entries: int = Field(description="Index titles of the ISCO group coded to it.")
    title_match: bool = Field(description="An ESCO label is one of its index titles.")
    benchmarks: list[PayBenchmarkOut] = Field(
        description="ASHE for this unit group in your cities' regions: about the unit group, "
        "not this occupation, unless the mapping is reviewed."
    )


class UkSocMappingOut(ResponseModel):
    """ESCO occupation to UK SOC 2020, with every candidate kept (TAX1-02)."""

    isco_code: str
    resolution: MappingResolution
    review_state: ReviewState
    proposed_soc_code: str | None = Field(description="A single or title match: unreviewed.")
    reviewed_soc_code: str | None
    reviewer: str | None
    reviewed_on: date | None
    candidates: list[SocCandidateOut]


class ModelledPayOut(ResponseModel):
    basis: Literal["modelled"] = Field(description="Never advertised or provider-predicted.")
    soc_code: str
    benchmarks: list[PayBenchmarkOut]


class TrendOut(ResponseModel):
    state: TrendState
    reason: TrendReason


class RegionOut(ResponseModel):
    code: str
    name: str


class IloExposureOut(ResponseModel):
    isco_code: str
    title: str
    tasks: int
    mean_score: str
    sd_score: str
    gradient: ExposureGradient
    measure: str = ILO_MEASURE


class ObservedTaskOut(ResponseModel):
    task: str
    share_pct: str


class OnetMatchOut(ResponseModel):
    onet_code: str
    onet_title: str
    match_type: MatchType
    in_release: bool = Field(description="False: the release lists no task for this code.")
    tasks_listed: int | None
    tasks_observed: int | None
    top_tasks: list[ObservedTaskOut]

    @classmethod
    def of(cls, match: OnetMatch) -> "OnetMatchOut":
        used = match.observed
        tasks = [] if used is None else used.top_tasks
        return cls(
            onet_code=match.onet_code,
            onet_title=match.onet_title,
            match_type=match.match_type,
            in_release=used is not None,
            tasks_listed=None if used is None else used.tasks_listed,
            tasks_observed=None if used is None else used.tasks_observed,
            top_tasks=[
                ObservedTaskOut(task=t.task, share_pct=format(t.share_pct, "f")) for t in tasks
            ],
        )


class AiEvidenceState(StrEnum):
    EXPOSURE_ONLY = "exposure_only"  # evidence is shown; resilience is not derived from it
    NO_EVIDENCE = "no_evidence"


class AiEvidenceOut(ResponseModel):
    state: AiEvidenceState
    ilo: IloExposureOut | None = Field(description="Null: the index does not score the group.")
    observed_use: list[OnetMatchOut] = Field(
        description="Per O*NET-SOC 2019 match from the ESCO to O*NET crosswalk, never averaged."
    )
    observed_use_measure: str = OBSERVED_USE_MEASURE


class AiResilienceOut(ResponseModel):
    label: str = LABEL
    meaning: str = MEANING
    experimental: Literal[True] = True
    horizon_years: int = HORIZON_YEARS
    geography: Literal["inherited"] = "inherited"
    state: AssessmentState
    unscored_reason: UnscoredReason | None
    lower: int | None
    upper: int | None
    bands: list[Band]
    band_words: list[str]
    synthetic: bool = Field(description="A synthetic fixture: never a real assessment.")
    synthetic_label: str | None
    pack_version: str
    pack_dated: date
    method_version: str = METHOD_VERSION

    @classmethod
    def of(cls, found: Assessment) -> "AiResilienceOut":
        return cls(
            state=found.state,
            unscored_reason=found.unscored_reason,
            lower=found.lower,
            upper=found.upper,
            bands=list(found.bands),
            band_words=[BAND_WORDS[b] for b in found.bands],
            synthetic=found.synthetic,
            synthetic_label=found.label if found.synthetic else None,
            pack_version=found.pack_version,
            pack_dated=found.pack_dated,
        )


class ReferenceReleaseOut(ResponseModel):
    """A pinned reference dataset's import manifest (TAX1-04): show its attribution wherever
    its figures appear."""

    dataset: str
    dataset_id: str
    version: str
    source_url: str
    sha256: str
    size_bytes: int
    native_code_version: str
    transformation_version: str
    licence: str
    attribution: str
    sample: bool = Field(description="A synthetic or reduced test copy: never real evidence.")
    record_count: int
    counts: dict[str, int]
    imported_at: datetime

    @classmethod
    def of(cls, release: ReferenceRelease) -> "ReferenceReleaseOut":
        return cls(
            dataset=release.dataset,
            dataset_id=release.dataset_id,
            version=release.version,
            source_url=release.source_url,
            sha256=release.sha256,
            size_bytes=release.size_bytes,
            native_code_version=release.native_code_version,
            transformation_version=release.transformation_version,
            licence=release.licence,
            attribution=release.attribution,
            sample=release.sample,
            record_count=release.record_count,
            counts=release.counts,
            imported_at=release.imported_at,
        )


class OccupationEvidenceOut(ResponseModel):
    concept_id: uuid.UUID
    title: str
    esco_uri: str
    regions: list[RegionOut] = Field(description="Your cities' regions: ASHE is regional.")
    uk_soc: UkSocMappingOut
    modelled_pay: ModelledPayOut | None
    modelled_pay_unavailable: ModelledPayUnavailable | None
    trend: TrendOut
    ai_evidence: AiEvidenceOut
    ai_resilience: AiResilienceOut
    releases: list[ReferenceReleaseOut]

    @classmethod
    def of(cls, evidence: OccupationEvidence) -> "OccupationEvidenceOut":
        mapping = evidence.mapping
        modelled = evidence.modelled
        observed = [OnetMatchOut.of(m) for m in evidence.onet_matches]
        exposure = evidence.ilo is not None or any(m.observed for m in evidence.onet_matches)
        return cls(
            concept_id=evidence.identity.concept_id,
            title=evidence.identity.preferred_label,
            esco_uri=evidence.identity.esco_uri,
            regions=[RegionOut(code=c, name=region_name(c)) for c in evidence.regions],
            uk_soc=UkSocMappingOut(
                isco_code=mapping.isco_code,
                resolution=mapping.resolution,
                review_state=mapping.review_state,
                proposed_soc_code=mapping.proposed_soc_code,
                reviewed_soc_code=mapping.reviewed_soc_code,
                reviewer=mapping.review.reviewer if mapping.review else None,
                reviewed_on=mapping.review.reviewed_on if mapping.review else None,
                candidates=[
                    SocCandidateOut(
                        soc_code=c.soc_code,
                        title=c.title,
                        index_entries=c.index_entries,
                        title_match=c.title_match,
                        benchmarks=[PayBenchmarkOut.of(b) for b in c.benchmarks],
                    )
                    for c in evidence.candidates
                ],
            ),
            modelled_pay=(
                ModelledPayOut(
                    basis="modelled",
                    soc_code=modelled.soc_code,
                    benchmarks=[PayBenchmarkOut.of(b) for b in modelled.benchmarks],
                )
                if isinstance(modelled, ModelledPay)
                else None
            ),
            modelled_pay_unavailable=(
                modelled if isinstance(modelled, ModelledPayUnavailable) else None
            ),
            trend=TrendOut(state=evidence.trend[0], reason=evidence.trend[1]),
            ai_evidence=AiEvidenceOut(
                state=AiEvidenceState.EXPOSURE_ONLY if exposure else AiEvidenceState.NO_EVIDENCE,
                ilo=None
                if evidence.ilo is None
                else IloExposureOut(
                    isco_code=evidence.ilo.isco_code,
                    title=evidence.ilo.title,
                    tasks=evidence.ilo.tasks,
                    mean_score=format(evidence.ilo.mean_score, "f"),
                    sd_score=format(evidence.ilo.sd_score, "f"),
                    gradient=evidence.ilo.gradient,
                ),
                observed_use=observed,
            ),
            ai_resilience=AiResilienceOut.of(evidence.assessment),
            releases=[ReferenceReleaseOut.of(r) for r in evidence.releases],
        )
