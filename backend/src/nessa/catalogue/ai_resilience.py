"""The AI Resilience Score's record model, publication checks and lower-bound filter (spec
section 5, AIR-1; plan S3.6 as reduced in v1.1; ADR 0010). Pure: no model, no SQL.

What a score is. It assesses pressure on demand for human work over a five-year outlook,
including reduced staffing and entry-level hiring, on a 0 to 10 scale where higher is more
resilient; it is not a probability that a person loses a job, 0 is not certain elimination
and 10 is not a guarantee (AIR1-10). M0 publishes a range only, marked experimental, with
inherited geography and no seniority or local modifiers (AIR1-01).

How a record publishes. There is no formula: no code turns exposure, observed use or their
absence into a score (AIR1-03). A record is data entered through this model. A model's
proposal (`AssessmentOrigin.MODEL_PROPOSAL`) never publishes, whatever its decision says: a
reviewer who accepts one enters it as their own `reviewer_entry` (AIR1-04). A record is
published only when an accountable reviewer's recorded decision passes every check in
`publication_failures` (AIR1-02, AIR1-12): a reviewer entry; a reviewed mapping; stated
technological and geographic scope; observed supporting evidence from at least two
independent evidence families, not all of them exposure (task exposure, observed use: such
evidence keeps resilience unscored, spec AIR-1 step 4); the reviewer's grade of the
evidence; recorded contradictions; physical-automation coverage stated; the bounds the
decision approved; the rubric's bands (an integer inside a band only with a documented
anchor, and a widening reason for a range across bands); the five-year horizon and this
method version. A reviewed null skips the evidence checks: it is the reviewer's answer to
evidence that cannot support a range. A withdrawn record, or one a known material
correction affects, is never published (AIR1-07).

The reviewed pack is committed, versioned and dated, and loaded and checked when the API
starts, before any session: its corrections are applied then and invalidate the records
they affect at once. L0 has no accountable reviewer (human gate H-10), so the product pack
holds no record and every real role is unscored; one conspicuously labelled synthetic
record, in a pack of its own, qualifies the machinery in the fixture workspace only.

The filter: "Minimum AI Resilience: Any / 0-10" applies to the lower end of a published
range; unscored roles are included by default; unknown never becomes 0 or 10 (AIR1-05).
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

LABEL = "AI Resilience Score"
MEANING = (
    "Pressure on demand for human work in this role over five years, including reduced "
    "staffing and entry-level hiring: 0 to 10, higher is more resilient. It is not a "
    "probability that anyone will lose a job; 0 is not certain elimination and 10 is not a "
    "guarantee. Experimental: a range under a reviewed rubric, never a precise score."
)
METHOD_VERSION = "nessa-air-rubric-m0-1"
HORIZON_YEARS = 5
SCALE = (0, 10)


class Band(StrEnum):
    """The rubric's ordinal bands (spec section 5). Never averaged, subtracted or read as
    probabilities (AIR1-12)."""

    VERY_HIGH_PRESSURE = "0-2"
    ELEVATED_PRESSURE = "3-4"
    MIXED = "5-6"
    COMPARATIVELY_RESILIENT = "7-8"
    HIGHEST_RESILIENCE = "9-10"

    @property
    def bounds(self) -> tuple[int, int]:
        low, high = self.value.split("-")
        return int(low), int(high)


BAND_WORDS = {
    Band.VERY_HIGH_PRESSURE: "very high substitution pressure",
    Band.ELEVATED_PRESSURE: "elevated substitution pressure",
    Band.MIXED: "mixed or contested outlook",
    Band.COMPARATIVELY_RESILIENT: "comparatively resilient",
    Band.HIGHEST_RESILIENCE: "highest assessed resilience",
}
_BAND_LOWS = frozenset(b.bounds[0] for b in Band)
_BAND_HIGHS = frozenset(b.bounds[1] for b in Band)


def band_of(score: int) -> Band:
    return next(b for b in Band if b.bounds[0] <= score <= b.bounds[1])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidenceFamily(StrEnum):
    """Kinds of evidence that measure different things (spec section 5): capability,
    observed adoption, whole-workflow substitution, human accountability, labour demand,
    realised employment effects and physical automation. Their quantities stay distinct."""

    TASK_EXPOSURE = "task_exposure"  # technical potential (the ILO index)
    OBSERVED_USE = "observed_use"  # adoption (the Anthropic Economic Index)
    WORKFLOW_SUBSTITUTION = "workflow_substitution"
    HUMAN_ACCOUNTABILITY = "human_accountability"
    LABOUR_DEMAND = "labour_demand"
    EMPLOYMENT_EFFECTS = "employment_effects"
    PHYSICAL_AUTOMATION = "physical_automation"


class Bearing(StrEnum):
    PRESSURE = "pressure"
    PROTECTION = "protection"
    MIXED = "mixed"


class EvidenceItem(StrictModel):
    family: EvidenceFamily
    source_id: str = Field(min_length=1, max_length=120)  # a dataset_id or a cited source
    # Sources in one group are one source: two named sources repeating one study, or one
    # dataset's two measures, are not independent corroboration.
    independence_group: str = Field(min_length=1, max_length=120)
    measure: str = Field(min_length=1, max_length=500)
    bearing: Bearing
    # False when the source holds no observation for the role (no AI use observed): such an
    # item is never protection (a missing observation cannot justify a high score).
    observed: bool = True


class Anchor(StrictModel):
    """A documented anchor: the only way a bound inside a band is allowed."""

    value: int = Field(ge=SCALE[0], le=SCALE[1])
    description: str = Field(min_length=1, max_length=1000)


class ReviewerDecision(StrictModel):
    """An accountable reviewer's recorded decision (H-10), with the range it allows: a
    record whose bounds differ from these does not publish (fix round 1, review B M1)."""

    reviewer: str = Field(min_length=1, max_length=120)
    role: Literal["accountable reviewer"]
    decided_on: date
    outcome: Literal["range", "null"]  # null: no defensible range, the role stays unscored
    lower: int | None = Field(default=None, ge=SCALE[0], le=SCALE[1])  # null for a null
    upper: int | None = Field(default=None, ge=SCALE[0], le=SCALE[1])
    reasons: str = Field(min_length=1, max_length=2000)
    assumptions: list[str]
    # Why the range spans more than one band (the scenarios, the mapping): required then.
    widening_reason: str | None = Field(default=None, max_length=1000)


class EvidenceQuality(StrEnum):
    """The reviewer's grade of the evidence for the allowed range (spec section 18's
    "evidence quality"; the words are provisional, R6)."""

    LIMITED = "limited"
    MODERATE = "moderate"
    STRONG = "strong"


class Withdrawal(StrictModel):
    withdrawn_on: date
    reason: str = Field(min_length=1, max_length=1000)


class AssessmentOrigin(StrEnum):
    # A model proposed it. It never publishes, whatever its decision says: a reviewer who
    # accepts it enters it again as their own `reviewer_entry` (fix round 1, review B I2).
    MODEL_PROPOSAL = "model_proposal"
    REVIEWER_ENTRY = "reviewer_entry"  # entered by the accountable reviewer


class AssessmentRecord(StrictModel):
    """One AIResilienceAssessment (spec section 18), as entered."""

    record_id: str = Field(min_length=1, max_length=80)
    esco_uri: str = Field(pattern=r"^http://data\.europa\.eu/esco/occupation/[0-9a-f-]{36}$")
    seniority: str | None = None  # M0 inherits: no seniority modifier
    modifiers: list[str] = Field(default_factory=list)  # M0: no industry or local modifier
    horizon_years: int
    lower: int | None = Field(default=None, ge=SCALE[0], le=SCALE[1])
    upper: int | None = Field(default=None, ge=SCALE[0], le=SCALE[1])
    reference_point: int | None = None  # the reference-score mode is M1
    anchors: list[Anchor] = Field(default_factory=list)
    technological_scope: str = Field(max_length=500)
    geographic_scope: str = Field(max_length=500)
    mapping_reviewed: bool
    evidence: list[EvidenceItem]
    contradictions: list[str] | None  # None: not recorded; [] recorded as none found
    physical_automation_coverage: str | None = Field(default=None, max_length=500)
    evidence_quality: EvidenceQuality | None = None  # required for a range
    method_version: str
    origin: AssessmentOrigin
    synthetic: bool
    label: str | None = Field(default=None, max_length=200)  # a synthetic record's warning
    decision: ReviewerDecision | None = None
    withdrawal: Withdrawal | None = None

    @property
    def sources(self) -> frozenset[str]:
        return frozenset(item.source_id for item in self.evidence)


class PublicationFailure(StrEnum):
    """A check a record fails, so it cannot publish (AIR1-02, AIR1-12)."""

    NO_REVIEWER_DECISION = "no_reviewer_decision"
    MAPPING_NOT_REVIEWED = "mapping_not_reviewed"
    SCOPE_NOT_STATED = "scope_not_stated"
    NO_SUPPORTING_EVIDENCE = "no_supporting_evidence"
    FEWER_THAN_TWO_INDEPENDENT_FAMILIES = "fewer_than_two_independent_families"
    CONTRADICTIONS_NOT_RECORDED = "contradictions_not_recorded"
    PHYSICAL_AUTOMATION_NOT_STATED = "physical_automation_not_stated"
    RANGE_INVALID = "range_invalid"
    BOUND_WITHOUT_ANCHOR = "bound_without_anchor"
    REFERENCE_POINT_NOT_IN_M0 = "reference_point_not_in_m0"
    MODIFIER_NOT_IN_M0 = "modifier_not_in_m0"
    HORIZON_NOT_FIVE_YEARS = "horizon_not_five_years"
    UNKNOWN_METHOD_VERSION = "unknown_method_version"
    MISSING_USE_AS_PROTECTION = "missing_use_as_protection"
    SYNTHETIC_NOT_LABELLED = "synthetic_not_labelled"
    # Fix round 1 (review B I1, I2, M1, M6):
    # every observed item is exposure or observed use: exposure evidence only, so
    # resilience stays unscored (spec AIR-1 step 4)
    EXPOSURE_ONLY_EVIDENCE = "exposure_only_evidence"
    MODEL_PROPOSAL = "model_proposal"  # a model's proposal never publishes
    BOUNDS_NOT_DECIDED = "bounds_not_decided"  # the record's bounds are not the decision's
    EVIDENCE_QUALITY_NOT_STATED = "evidence_quality_not_stated"
    WIDENING_NOT_EXPLAINED = "widening_not_explained"  # a range across bands, no reason


# Families that measure exposure (technical potential, observed adoption), never what
# protects or substitutes the work: they alone cannot support a resilience range.
EXPOSURE_FAMILIES = frozenset({EvidenceFamily.TASK_EXPOSURE, EvidenceFamily.OBSERVED_USE})


def _independent_families(evidence: Iterable[EvidenceItem]) -> bool:
    """At least two families, from at least two independent sources, both observed."""
    observed = [item for item in evidence if item.observed]
    families = {item.family for item in observed}
    groups = {item.independence_group for item in observed}
    return len(families) >= 2 and len(groups) >= 2


def _evidence_failures(record: AssessmentRecord) -> list[PublicationFailure]:
    """Whether the evidence can support a range. A reviewed null needs none of this: it is
    the reviewer's answer to evidence that cannot (fix round 1, review B M2)."""
    observed = [item for item in record.evidence if item.observed]
    failures = []
    if not observed:
        failures.append(PublicationFailure.NO_SUPPORTING_EVIDENCE)
    if not _independent_families(record.evidence):
        failures.append(PublicationFailure.FEWER_THAN_TWO_INDEPENDENT_FAMILIES)
    if observed and all(item.family in EXPOSURE_FAMILIES for item in observed):
        failures.append(PublicationFailure.EXPOSURE_ONLY_EVIDENCE)
    if record.evidence_quality is None:
        failures.append(PublicationFailure.EVIDENCE_QUALITY_NOT_STATED)
    return failures


def _range_failures(record: AssessmentRecord) -> list[PublicationFailure]:
    failures = []
    low, high = record.lower, record.upper
    decision = record.decision
    if decision is not None and (decision.lower, decision.upper) != (low, high):
        failures.append(PublicationFailure.BOUNDS_NOT_DECIDED)
    if decision is not None and decision.outcome == "null":
        if low is not None or high is not None:
            failures.append(PublicationFailure.RANGE_INVALID)
        return failures
    if low is None or high is None or low > high:
        return [*failures, PublicationFailure.RANGE_INVALID]
    anchored = {anchor.value for anchor in record.anchors}
    if (low not in _BAND_LOWS and low not in anchored) or (
        high not in _BAND_HIGHS and high not in anchored
    ):
        failures.append(PublicationFailure.BOUND_WITHOUT_ANCHOR)
    across_bands = band_of(low) is not band_of(high)
    if across_bands and not (decision and (decision.widening_reason or "").strip()):
        failures.append(PublicationFailure.WIDENING_NOT_EXPLAINED)
    return failures


def publication_failures(record: AssessmentRecord) -> list[PublicationFailure]:
    """Every check the record fails; empty only for a publishable record. Deterministic."""
    failures: list[PublicationFailure] = []
    if record.origin is AssessmentOrigin.MODEL_PROPOSAL:
        failures.append(PublicationFailure.MODEL_PROPOSAL)
    if record.decision is None:
        failures.append(PublicationFailure.NO_REVIEWER_DECISION)
    if not record.mapping_reviewed:
        failures.append(PublicationFailure.MAPPING_NOT_REVIEWED)
    if not record.technological_scope.strip() or not record.geographic_scope.strip():
        failures.append(PublicationFailure.SCOPE_NOT_STATED)
    if record.decision is None or record.decision.outcome == "range":
        failures += _evidence_failures(record)
    if record.contradictions is None:
        failures.append(PublicationFailure.CONTRADICTIONS_NOT_RECORDED)
    if not (record.physical_automation_coverage or "").strip():
        failures.append(PublicationFailure.PHYSICAL_AUTOMATION_NOT_STATED)
    failures += _range_failures(record)
    if record.reference_point is not None:
        failures.append(PublicationFailure.REFERENCE_POINT_NOT_IN_M0)
    if record.seniority is not None or record.modifiers:
        failures.append(PublicationFailure.MODIFIER_NOT_IN_M0)
    if record.horizon_years != HORIZON_YEARS:
        failures.append(PublicationFailure.HORIZON_NOT_FIVE_YEARS)
    if record.method_version != METHOD_VERSION:
        failures.append(PublicationFailure.UNKNOWN_METHOD_VERSION)
    if any(not i.observed and i.bearing is not Bearing.PRESSURE for i in record.evidence):
        failures.append(PublicationFailure.MISSING_USE_AS_PROTECTION)
    if record.synthetic and "synthetic" not in (record.label or "").casefold():
        failures.append(PublicationFailure.SYNTHETIC_NOT_LABELLED)
    return failures


class Correction(StrictModel):
    """A known material correction to a source or a record: it invalidates what it affects
    at once, pending review (AIR1-07)."""

    correction_id: str = Field(min_length=1, max_length=80)
    noted_on: date
    description: str = Field(min_length=1, max_length=1000)
    affects_sources: list[str] = Field(default_factory=list)
    affects_records: list[str] = Field(default_factory=list)


class AssessmentPack(StrictModel):
    """The pinned, dated pack of assessment records and the corrections known to it."""

    pack_version: str = Field(min_length=1, max_length=40)
    dated: date
    method_version: str
    synthetic: bool
    records: list[AssessmentRecord]
    corrections: list[Correction]

    @model_validator(mode="after")
    def _consistent(self) -> "AssessmentPack":
        ids = [r.record_id for r in self.records]
        keys = [(r.esco_uri, r.seniority) for r in self.records]
        if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
            raise ValueError("a pack holds one record per ID and per occupation")
        if any(r.synthetic != self.synthetic for r in self.records):
            raise ValueError("a synthetic record is only ever in a synthetic pack, and back")
        if self.method_version != METHOD_VERSION:
            raise ValueError(f"the pack's method is not {METHOD_VERSION}")
        return self


def load_pack(path: Path) -> AssessmentPack:
    return AssessmentPack.model_validate(json.loads(path.read_text(encoding="utf-8")))


class RecordState(StrEnum):
    PROPOSED = "proposed"  # fails a publication check: never shown as a score
    PUBLISHED = "published"
    WITHDRAWN = "withdrawn"
    INVALIDATED = "invalidated"  # a known material correction affects it


@dataclass(frozen=True)
class CheckedRecord:
    record: AssessmentRecord
    state: RecordState
    failures: tuple[PublicationFailure, ...]
    corrections: tuple[str, ...]  # the corrections that invalidate it


def check_record(record: AssessmentRecord, corrections: Iterable[Correction]) -> CheckedRecord:
    affecting = tuple(
        c.correction_id
        for c in corrections
        if record.record_id in c.affects_records or record.sources & set(c.affects_sources)
    )
    failures = tuple(publication_failures(record))
    if record.withdrawal is not None:
        state = RecordState.WITHDRAWN
    elif affecting:
        state = RecordState.INVALIDATED
    elif failures:
        state = RecordState.PROPOSED
    else:
        state = RecordState.PUBLISHED
    return CheckedRecord(record, state, failures, affecting)


@dataclass(frozen=True)
class CheckedPack:
    """A pack as checked when the API starts: every record's state, corrections applied."""

    pack: AssessmentPack
    records: tuple[CheckedRecord, ...]

    def for_occupation(self, esco_uri: str) -> CheckedRecord | None:
        # M0 records inherit seniority, so one per occupation.
        return next((r for r in self.records if r.record.esco_uri == esco_uri), None)


def check_pack(pack: AssessmentPack) -> CheckedPack:
    return CheckedPack(pack, tuple(check_record(r, pack.corrections) for r in pack.records))


class AssessmentState(StrEnum):
    PUBLISHED_RANGE = "published_range"
    PUBLISHED_NULL = "published_null"  # reviewed: no defensible range, so unscored
    UNSCORED = "unscored"


class UnscoredReason(StrEnum):
    NO_RECORD = "no_record"  # no reviewed record (every real role in L0: H-10)
    NOT_PUBLISHABLE = "not_publishable"  # a record fails a publication check
    WITHDRAWN = "withdrawn"
    INVALIDATED = "invalidated"
    REVIEWED_NULL = "reviewed_null"


@dataclass(frozen=True)
class Assessment:
    """What the product shows for one occupation."""

    state: AssessmentState
    unscored_reason: UnscoredReason | None
    lower: int | None
    upper: int | None
    pack_version: str
    pack_dated: date
    synthetic: bool  # the record is synthetic; False when there is no record (review B M3)
    label: str | None
    record_id: str | None
    failures: tuple[PublicationFailure, ...] = ()
    evidence_quality: EvidenceQuality | None = None  # a published range's

    @property
    def bands(self) -> tuple[Band, ...]:
        if self.lower is None or self.upper is None:
            return ()
        return tuple(dict.fromkeys(band_of(s) for s in range(self.lower, self.upper + 1)))


_UNSCORED = {
    RecordState.PROPOSED: UnscoredReason.NOT_PUBLISHABLE,
    RecordState.WITHDRAWN: UnscoredReason.WITHDRAWN,
    RecordState.INVALIDATED: UnscoredReason.INVALIDATED,
}


def assessment(pack: CheckedPack, esco_uri: str) -> Assessment:
    found = pack.for_occupation(esco_uri)
    version, dated = pack.pack.pack_version, pack.pack.dated
    if found is None:
        return Assessment(
            state=AssessmentState.UNSCORED,
            unscored_reason=UnscoredReason.NO_RECORD,
            lower=None,
            upper=None,
            pack_version=version,
            pack_dated=dated,
            synthetic=False,  # no record: nothing synthetic is shown, even in the fixture pack
            label=None,
            record_id=None,
        )
    record = found.record
    published = found.state is RecordState.PUBLISHED
    null = published and record.decision is not None and record.decision.outcome == "null"
    if not published:
        state, reason = AssessmentState.UNSCORED, _UNSCORED[found.state]
    elif null:
        state, reason = AssessmentState.PUBLISHED_NULL, UnscoredReason.REVIEWED_NULL
    else:
        state, reason = AssessmentState.PUBLISHED_RANGE, None
    scored = state is AssessmentState.PUBLISHED_RANGE
    return Assessment(
        state=state,
        unscored_reason=reason,
        lower=record.lower if scored else None,
        upper=record.upper if scored else None,
        pack_version=version,
        pack_dated=dated,
        synthetic=record.synthetic,
        label=record.label,
        record_id=record.record_id,
        failures=() if published else found.failures,
        evidence_quality=record.evidence_quality if scored else None,
    )


@dataclass(frozen=True)
class ResilienceFilter:
    """Minimum AI Resilience: Any (None) or 0-10, on the lower end of the range."""

    minimum: int | None = None
    include_unscored: bool = True


class FilterOutcome(StrEnum):
    KEPT = "kept"
    BELOW_MINIMUM = "below_minimum"  # its range's lower end is below the minimum
    UNSCORED_KEPT = "unscored_kept"
    UNSCORED_EXCLUDED = "unscored_excluded"  # only when unscored roles are switched off


def filter_outcome(found: Assessment, chosen: ResilienceFilter) -> FilterOutcome:
    """Deterministic lower-bound filtering: an unscored role is never read as 0 or 10."""
    if found.state is not AssessmentState.PUBLISHED_RANGE or found.lower is None:
        if chosen.include_unscored:
            return FilterOutcome.UNSCORED_KEPT
        return FilterOutcome.UNSCORED_EXCLUDED
    if chosen.minimum is not None and found.lower < chosen.minimum:
        return FilterOutcome.BELOW_MINIMUM
    return FilterOutcome.KEPT


_PACKS = Path(__file__).parent / "packs"
PRODUCT_PACK = _PACKS / "ai_resilience.json"
FIXTURE_PACK = _PACKS / "ai_resilience_fixture.json"


@dataclass(frozen=True)
class AssessmentPacks:
    """The product pack (every workspace) and the synthetic fixture pack (the fixture
    workspace only), both checked."""

    product: CheckedPack
    fixture: CheckedPack

    def for_workspace(self, *, fixture_workspace: bool) -> CheckedPack:
        return self.fixture if fixture_workspace else self.product


def committed_packs() -> AssessmentPacks:
    """Loaded and checked once, when the API starts (before any session is enabled)."""
    product, fixture = load_pack(PRODUCT_PACK), load_pack(FIXTURE_PACK)
    if product.synthetic or not fixture.synthetic:
        raise ValueError("the product pack is never synthetic; the fixture pack always is")
    return AssessmentPacks(check_pack(product), check_pack(fixture))
