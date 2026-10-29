"""The England option pack: its file format, the checks a pack must pass, and the loader of
the committed, hash-pinned versions (spec sections 10, 11 and 18; plan section 9; ADR 0008
decision 1; ADR 0011). Pure: no SQL, no network, no model.

What a pack is. An immutable public evidence pack of catalogue records for the qualification
personas' targets, built from real pages (the corpus, `corpus/manifest.json`): job postings
with their skill requirements, learning options with their dated offerings and planned
outcomes (OUT-1), and funding instruments. Every value a record holds is a claim: a value read
from one source, with its span (offsets into the hashed page text, or a JSON pointer into an
API response) and the exact excerpt there. A field either cites a claim or says why its value
is unknown; unknown is never zero or empty. Money is integer GBP minor units. Nothing in a
pack is synthetic.

Review. Every record carries `review_state`. A version an agent curated (0.1.0, Task 7b) is
all `proposed`: explorable, never in an unqualified "affordable and feasible" or readiness
result (ruling R9). A version published from a person's review record (Task 7c) marks the
accepted records `reviewed`, each naming its reviewer, date and session; the earlier version
stays unchanged. A format change bumps `format_version`; any change of content is a new
`pack_version`, and every version's file is pinned by its SHA-256 (`PINS`), so a committed
version can never change silently.

Consumers (Tasks 9 and 11) load a version through `load_pack` and map its records into their
own domain models; they read a field's value with `Pack.value`.
"""

import hashlib
import json
from collections import Counter
from collections.abc import Iterator
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    ValidationError,
    model_validator,
)

PACK_NAME = "nessa-england-option-pack"
FORMAT_VERSION = 1
EXCERPT_CHARS = 200  # the excerpt bound of the evidence records (`nessa.evidence.pages`)
PACKS_DIR = Path(__file__).parent / "packs" / "england_option_pack"
SCHEMA_PATH = PACKS_DIR / "england-option-pack.schema.json"
# Every committed version, pinned by the SHA-256 of its file's bytes: a version never
# changes; a correction or a review is a new version (Task 7c publishes the reviewed one).
PINS: dict[str, str] = {
    "0.1.0": "fe1f66691a5680a24a2dadab5b09426d0911433d3a5f0c165c3925a5043cb328",
}

SHA256 = r"^[0-9a-f]{64}$"
SOURCE_ID = r"^[JCF][0-9]{2}$"
SYNTHETIC_HOSTS = (".example", ".test", ".invalid", ".localhost", "localhost")
SYNTHETIC_MARK = "fixture:"


class OptionPackError(ValueError):
    """A pack that does not parse, or a committed version whose bytes are not its pin."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReviewState(StrEnum):
    PROPOSED = "proposed"  # curated, not reviewed: explorable, never unqualified (R9)
    REVIEWED = "reviewed"  # accepted in a person's recorded review (Task 7c)


class Review(StrictModel):
    """A person's recorded decision on a record (H-07, session 2), as Task 7c transcribes it."""

    reviewer: str = Field(min_length=1, max_length=120)
    decided_on: date
    session: str = Field(min_length=1, max_length=60)
    decision: str = Field(min_length=1, max_length=400)


class SourceKind(StrEnum):
    JOB_POSTING = "job_posting"
    COURSE_PAGE = "course_page"
    FUNDING_PAGE = "funding_page"


class Route(StrEnum):
    FETCH = "fetch"  # a page fetched through the acquisition pipeline: offsets
    ADZUNA = "adzuna"  # an Adzuna API response: JSON pointers


class Split(StrEnum):
    """Assigned by template family before any tuning (OI-09): never tune on holdout."""

    DEVELOPMENT = "development"
    HOLDOUT = "holdout"


class RightsClass(StrEnum):
    """The session 1 rights policy's classes (H-06), as the evidence records name them."""

    GOVUK = "govuk"
    PUBLIC_SECTOR = "public-sector"
    COURSE_PROVIDER = "course-provider"
    PROFESSIONAL_BODY = "professional-body"
    EMPLOYER_POSTING = "employer-posting"
    JOB_BOARD = "job-board"
    OTHER = "other"


class Retention(StrEnum):
    BODY = "body"  # kept privately on the curating machine (never in git)
    EXCERPTS = "excerpts"  # the hash and the claims' excerpts only


class Span(StrictModel):
    """Offsets into the hashed page text, or a JSON pointer into an API response."""

    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)
    pointer: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def _located(self) -> "Span":
        offsets = self.start is not None and self.end is not None
        if offsets == (self.pointer is not None) or (self.start is None) != (self.end is None):
            raise ValueError("a span has offsets or a pointer, not both and not neither")
        if self.start is not None and self.end is not None and self.end <= self.start:
            raise ValueError("a span ends after it starts")
        return self


class Source(StrictModel):
    """One corpus page (`corpus/manifest.json` slot) as it was retrieved."""

    source_id: str = Field(pattern=SOURCE_ID)
    kind: SourceKind
    route: Route
    url: str = Field(min_length=1, max_length=2_048)  # as recorded: never with a credential
    final_url: str | None = Field(default=None, max_length=2_048)
    retrieved_at: datetime
    http_status: int | None
    content_type: str | None
    sha256: str = Field(pattern=SHA256)  # of the text the spans index into
    rights_class: RightsClass
    rights_status: str = Field(min_length=1, max_length=1_200)
    retention: Retention
    template_family: str = Field(min_length=1, max_length=80)
    split: Split
    advert_pointer: str | None = None  # the advert within an API response
    # The most occurrences its excerpts were counted to: set where the page's text was not
    # kept and its excerpts were located before the locator counted past 5. A claim whose
    # `occurrences` equals it occurs at least that often. Null: every count is exact.
    occurrence_cap: int | None = Field(default=None, ge=1)


class Claim(StrictModel):
    """SourceClaim (spec section 18): one value read from one source, with its span and the
    exact excerpt there, as an agent labelled it (label review: not run, requires human)."""

    claim_id: str = Field(pattern=r"^[JCF][0-9]{2}\.[a-z0-9_.]+$")
    source_id: str = Field(pattern=SOURCE_ID)
    field: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    value: JsonValue
    span: Span
    excerpt: str = Field(min_length=1, max_length=EXCERPT_CHARS)
    # Of the excerpt in the hashed text; the span is the first. Exact, except a count that
    # reaches its source's `occurrence_cap`, which is a lower bound.
    occurrences: int = Field(default=1, ge=1)
    note: str | None = Field(default=None, max_length=600)  # the labeller's reading of it


class Unknown(StrictModel):
    """Why a field has no value: never zero, empty or a guess."""

    unknown: str = Field(min_length=1, max_length=400)


Ref = str | Unknown  # a claim's id, or why the value is unknown


class Target(StrictModel):
    target_id: str = Field(pattern=r"^[a-z0-9-]+$")
    persona: Literal["P01", "P02", "P03", "P04", "P05"]
    title: str = Field(min_length=1)
    city: str = Field(min_length=1)


class Skill(StrictModel):
    """A pack-local requirement row a target's postings share (`pack:<target>:<row>`); Task 9
    maps rows to ESCO and gives them rubrics."""

    skill_id: str = Field(pattern=r"^pack:[a-z0-9-]+:[a-z0-9-]+$")
    target_id: str
    label: str = Field(min_length=1)
    kind: Literal["skill", "credential", "experience"]


class Record(StrictModel):
    record_id: str = Field(pattern=r"^[a-z_]+:[A-Za-z0-9_.-]+$")
    review_state: ReviewState
    review: Review | None = None
    as_of: date  # the retrieval date of the evidence behind it: never "current"
    facts: list[str] = Field(default_factory=list)  # further span-cited facts (claim ids)


class JobPosting(Record):
    """One source's copy of a vacancy (spec section 18, JobPosting); copies of one vacancy
    share `vacancy_id` and count once."""

    source_id: str
    target_id: str
    vacancy_id: str
    title: Ref
    employer: Ref
    advertiser: Ref
    location: Ref
    work_mode: Ref
    salary: Ref
    date_posted: Ref
    valid_through: Ref
    employment_type: Ref
    description_kind: Ref
    status: Ref
    requirement_ids: list[str]


class SkillRequirement(Record):
    """A requirement row from a posting (spec section 18, SkillRequirement). A posting states
    no behaviourally anchored level, so `required_level` stays null until a reviewed rubric
    (Task 9) sets it."""

    job_posting_id: str
    target_id: str
    skill_id: str | None  # null: kept as text, no pack row maps it
    text: str  # the claim holding the requirement as the posting words it
    kind: Literal["skill", "credential", "experience", "eligibility", "task"]
    importance: Literal["essential", "preferred", "disputed", "unknown"]
    gate: str | None
    required_level: int | None = Field(ge=0, le=4)


class LearningOption(Record):
    """The stable syllabus and provider (spec section 18, LearningOption)."""

    source_id: str
    target_ids: list[str]
    title: Ref
    provider: Ref
    credential: Ref
    awarding_body: Ref
    recognising_body: Ref
    level: Ref
    delivery_mode: Ref
    assessment: Ref
    entry_requirements: list[str]


class Offering(Record):
    """A dated offer of an option (spec section 18, Offering): intake, fees, timetable."""

    option_id: str
    intake: Ref
    application_deadline: Ref
    duration: Ref
    schedule: Ref
    fee_total: Ref
    instalment: Ref
    wage: Ref  # an apprenticeship's: one composite action with its training
    location: Ref
    extra_costs: list[str]
    funding_conditions: list[str]


class Outcome(Record):
    """A planned outcome row, `PlanAction.outcomes` (OUT-1): never demonstrated competence.
    A level needs a rubric and an assessment that supports it; otherwise null."""

    offering_id: str
    skill_id: str
    level_on_completion: int | None = Field(ge=0, le=4)
    evidence_kind: Literal["topic_mention", "practice", "assessed_work_sample", "exam"]
    confidence: Literal["unsupported", "provisional", "corroborated"]
    source_span: str  # the claim holding the supporting extract
    rubric_version: str | None
    claim_state: Literal["planned_conditional"]


class FundingInstrument(Record):
    """A funding scheme's rules (spec section 18, FundingInstrument): never a conclusion about
    a person's eligibility (spec section 11), so its award state is always `not_assessed`."""

    source_ids: list[str]
    programme: Ref
    jurisdiction: Literal["GB-ENG"]
    instrument_kind: Literal["fee_waiver", "grant", "loan", "programme"]
    eligible_costs: Ref
    rules: list[str]
    timing: Ref
    repayment: Ref
    exclusions: list[str]
    award_state: Literal["not_assessed"]
    published_on: Ref
    rules_updated_on: Ref


class Pack(StrictModel):
    pack: Literal["nessa-england-option-pack"]
    format_version: Literal[1]
    pack_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    dated: date
    jurisdiction: Literal["GB-ENG"]
    currency: Literal["GBP"]
    synthetic: Literal[False]
    label_review: str
    notes: list[str]
    targets: list[Target]
    skills: list[Skill]
    sources: list[Source]
    claims: list[Claim]
    job_postings: list[JobPosting]
    skill_requirements: list[SkillRequirement]
    learning_options: list[LearningOption]
    offerings: list[Offering]
    outcomes: list[Outcome]
    funding_instruments: list[FundingInstrument]

    @model_validator(mode="after")
    def _unique(self) -> "Pack":
        ids = [
            *(s.source_id for s in self.sources),
            *(c.claim_id for c in self.claims),
            *(r.record_id for r in self.records()),
            *(t.target_id for t in self.targets),
            *(s.skill_id for s in self.skills),
        ]
        repeated = sorted(i for i, n in Counter(ids).items() if n > 1)
        if repeated:
            raise ValueError(f"identifiers used twice: {', '.join(repeated)}")
        return self

    def records(self) -> Iterator[Record]:
        yield from self.job_postings
        yield from self.skill_requirements
        yield from self.learning_options
        yield from self.offerings
        yield from self.outcomes
        yield from self.funding_instruments

    def claim(self, claim_id: str) -> Claim:
        return next(c for c in self.claims if c.claim_id == claim_id)

    def value(self, ref: Ref) -> JsonValue:
        """A field's value: its claim's, or None when the field says why it is unknown."""
        return None if isinstance(ref, Unknown) else self.claim(ref).value


def parse_pack(data: object) -> Pack:
    try:
        return Pack.model_validate(data)
    except ValidationError as error:
        raise OptionPackError(_first_problem(error)) from None


def _first_problem(error: ValidationError) -> str:
    first = error.errors()[0]
    where = ".".join(str(part) for part in first["loc"])
    return f"{where}: {first['msg']}"


# Value shapes (ADR 0011 decision 13). A claim's value has the one shape its field declares,
# and a record field checks the claim it cites against its own shape too, whatever that
# claim's field is called. A null value is the page withholding or lacking the value, so it
# has no shape. Every shape is numbers, ISO strings, fixed words or text: never a float and
# never a range written as a string. Money is integer GBP minor units, never negative.
Period = Literal["year", "month", "week", "day", "hour"]
Minor = Annotated[int, Field(ge=0)]
Text = Annotated[str, Field(min_length=1)]


def _iso_date_or_month(value: str) -> str:
    if len(value) == 7:
        datetime.strptime(value, "%Y-%m")
    elif len(value) == 10:
        date.fromisoformat(value)
    else:
        raise ValueError("not an ISO date or month")
    return value


def _iso_date_or_datetime(value: str) -> str:
    if len(value) == 10:
        date.fromisoformat(value)
    elif datetime.fromisoformat(value).utcoffset() is None:
        raise ValueError("a datetime without its UTC offset")
    return value


IsoDate = Annotated[str, AfterValidator(_iso_date_or_month)]  # YYYY-MM-DD, or YYYY-MM
Deadline = Annotated[str, AfterValidator(_iso_date_or_datetime)]


class Money(StrictModel):
    currency: Literal["GBP"]
    minor_units: Minor


class Rate(StrictModel):
    """An amount per period: a yearly fee, a yearly grant."""

    currency: Literal["GBP"]
    minor_units: Minor
    period: Period
    at_least: bool  # "at least £5,000 a year"


class Pay(StrictModel):
    """Advertised or provider-predicted pay: a range, a point (equal ends) or one bound."""

    currency: Literal["GBP"]
    minimum_minor_units: Minor | None
    maximum_minor_units: Minor | None
    period: Period | None  # null: the source states no period
    basis: Literal["advertised", "predicted", "unknown"]

    @model_validator(mode="after")
    def _range(self) -> "Pay":
        low, high = self.minimum_minor_units, self.maximum_minor_units
        if low is None and high is None:
            raise ValueError("pay with no amount")
        if low is not None and high is not None and high < low:
            raise ValueError("a maximum below its minimum")
        return self


class Instalment(StrictModel):
    """A payment plan: an amount per period, a number of payments, or both."""

    currency: Literal["GBP"]
    minor_units: Minor | None
    period: Period | None
    count: Annotated[int, Field(ge=1)] | None
    at_least: bool  # "from £69.52 a month"

    @model_validator(mode="after")
    def _stated(self) -> "Instalment":
        if self.minor_units is None and self.count is None:
            raise ValueError("an instalment with neither an amount nor a count")
        return self


class DurationPart(StrictModel):
    """One way of taking it (full time, part time, self-paced) and how long it lasts."""

    unit: Literal["hours", "weeks", "months", "years"]
    minimum: Annotated[int, Field(ge=1)] | None  # null with a maximum: "up to"
    maximum: Annotated[int, Field(ge=1)] | None
    mode: Literal["full_time", "part_time", "self_paced"] | None

    @model_validator(mode="after")
    def _range(self) -> "DurationPart":
        if self.minimum is None and self.maximum is None:
            raise ValueError("a duration with no length")
        if self.minimum is not None and self.maximum is not None and self.maximum < self.minimum:
            raise ValueError("a maximum below its minimum")
        return self


class Schedule(StrictModel):
    pattern: Literal["full_time", "part_time"] | None
    hours_per_week: Annotated[int, Field(ge=1)] | None

    @model_validator(mode="after")
    def _stated(self) -> "Schedule":
        if self.pattern is None and self.hours_per_week is None:
            raise ValueError("a schedule with neither a pattern nor hours")
        return self


class Place(StrictModel):
    label: Text
    locality: Text | None = None
    region: Text | None = None
    postal_code: Text | None = None


class AgeRule(StrictModel):
    minimum_age: Annotated[int, Field(ge=0, le=120)]
    on: Text | None = None  # the day the age is taken on, as the page words it


class EarningsRule(StrictModel):
    below_annual_gross: Money
    area: Text | None = None
    or_unemployed: bool = False


class LevelsRule(StrictModel):
    levels: Annotated[list[Annotated[int, Field(ge=0, le=8)]], Field(min_length=1)]


class LevelChange(StrictModel):
    levels: Annotated[list[Annotated[int, Field(ge=0, le=8)]], Field(min_length=1)]
    courses_starting_on_or_after: IsoDate
    use_instead: Text


class Crosswalk(StrictModel):
    candidates: Annotated[list[Text], Field(min_length=2)]
    resolved: Text | None


SHAPES: dict[str, TypeAdapter[Any]] = {
    "text": TypeAdapter(Text),
    "money": TypeAdapter(Money),
    "rate": TypeAdapter(Rate),
    "pay": TypeAdapter(Pay),
    "instalment": TypeAdapter(Instalment),
    "date": TypeAdapter(IsoDate),
    "dates": TypeAdapter(Annotated[list[IsoDate], Field(min_length=1)]),
    "deadline": TypeAdapter(Deadline),
    "duration": TypeAdapter(Annotated[list[DurationPart], Field(min_length=1)]),
    "schedule": TypeAdapter(Schedule),
    "place": TypeAdapter(Place),
    "level": TypeAdapter(Annotated[int, Field(ge=0, le=8)]),  # RQF level
    "count": TypeAdapter(Annotated[int, Field(ge=0)]),
    "flag": TypeAdapter(bool),
    "names": TypeAdapter(Annotated[list[Text], Field(min_length=1)]),
    "age_rule": TypeAdapter(AgeRule),
    "earnings_rule": TypeAdapter(EarningsRule),
    "levels": TypeAdapter(LevelsRule),
    "level_change": TypeAdapter(LevelChange),
    "crosswalk": TypeAdapter(Crosswalk),
    "advertiser": TypeAdapter(Literal["employer", "agency", "unknown"]),
    "work_mode": TypeAdapter(Literal["on_site", "hybrid", "remote"]),
    "description_kind": TypeAdapter(Literal["full", "snippet"]),
}
_BY_SHAPE = {
    "money": ("fee_total", "fee_was", "extra_cost", "exam_fee"),
    "rate": ("fee_per_year_home", "fee_per_year_international", "support_grant"),
    "pay": ("salary", "salary_conflict", "salary_annual_statement", "salary_point", "wage"),
    "instalment": ("instalment",),
    "date": (
        *("date_posted", "intake", "application_deadline", "published_on", "rules_updated_on"),
        *("contract_end", "price_valid_until"),
    ),
    "dates": ("intakes_stated",),
    "deadline": ("valid_through",),
    "duration": ("duration", "duration_conflict", "contract_duration", "duration_limit"),
    "schedule": ("schedule", "study_type", "weekly_hours"),
    "place": ("location", "location_conflict"),
    "level": ("level",),
    "count": ("guided_hours",),
    "flag": ("eligibility_no_other_funded_training",),
    "names": ("eligibility_residency", "work_locations"),
    "age_rule": ("eligibility_age", "rule_age"),
    "earnings_rule": ("eligibility_earnings", "rule_earnings"),
    "levels": ("rule_course_level",),
    "level_change": ("lle_interaction",),
    "crosswalk": ("occupation_crosswalk",),
    "advertiser": ("advertiser",),
    "work_mode": ("work_mode",),
    "description_kind": ("description_kind",),
}
# A claim field's shape; a field not listed here holds text.
CLAIM_FIELD_SHAPES: dict[str, str] = {f: shape for shape, fs in _BY_SHAPE.items() for f in fs}
# A record field's shape, checked on the claim it cites (a list field: on each claim it
# lists). Facts, rules and funding conditions take their claims' own field shapes.
RECORD_FIELD_SHAPES: dict[str, str] = {
    "JobPosting.title": "text",
    "JobPosting.employer": "text",
    "JobPosting.advertiser": "advertiser",
    "JobPosting.location": "place",
    "JobPosting.work_mode": "work_mode",
    "JobPosting.salary": "pay",
    "JobPosting.date_posted": "date",
    "JobPosting.valid_through": "deadline",
    "JobPosting.employment_type": "text",
    "JobPosting.description_kind": "description_kind",
    "JobPosting.status": "text",
    "SkillRequirement.text": "text",
    "LearningOption.title": "text",
    "LearningOption.provider": "text",
    "LearningOption.credential": "text",
    "LearningOption.awarding_body": "text",
    "LearningOption.recognising_body": "text",
    "LearningOption.level": "level",
    "LearningOption.delivery_mode": "text",
    "LearningOption.assessment": "text",
    "LearningOption.entry_requirements": "text",
    "Offering.intake": "date",
    "Offering.application_deadline": "date",
    "Offering.duration": "duration",
    "Offering.schedule": "schedule",
    "Offering.fee_total": "money",
    "Offering.instalment": "instalment",
    "Offering.wage": "pay",
    "Offering.location": "place",
    "Offering.extra_costs": "money",
    "Outcome.source_span": "text",
    "FundingInstrument.programme": "text",
    "FundingInstrument.eligible_costs": "text",
    "FundingInstrument.timing": "text",
    "FundingInstrument.repayment": "text",
    "FundingInstrument.exclusions": "text",
    "FundingInstrument.published_on": "date",
    "FundingInstrument.rules_updated_on": "date",
}


def check_pack(pack: Pack) -> list[str]:
    """Every problem in a parsed pack, each named; an empty list is a pack that passes."""
    found: list[str] = []
    found += _synthetic(pack)
    found += _claim_values(pack)
    found += _references(pack)
    found += _reviews(pack)
    found += _outcomes(pack)
    found += _splits(pack)
    found += _spans(pack)
    return found


def _synthetic(pack: Pack) -> list[str]:
    found = []
    for source in pack.sources:
        host = (urlsplit(source.url).hostname or "").lower()
        if host.endswith(SYNTHETIC_HOSTS) or not host:
            found.append(f"{source.source_id} is not a real public page ({host})")
    for claim in pack.claims:
        if SYNTHETIC_MARK in json.dumps(claim.value):
            found.append(f"{claim.claim_id} holds a fixture: identifier")
    return found


def _fits(shape: str, value: JsonValue) -> bool:
    """Whether a value has a shape. Strict: no number in a string, no float for an integer."""
    if value is None:
        return True
    try:
        SHAPES[shape].validate_python(value, strict=True)
    except ValidationError:
        return False
    return True


def _claim_values(pack: Pack) -> list[str]:
    """Each claim's value against its own field's shape; then each record field's shape
    against the claims it cites, where that differs."""
    found = [
        f"{c.claim_id} is not {shape}"
        for c in pack.claims
        if not _fits(shape := CLAIM_FIELD_SHAPES.get(c.field, "text"), c.value)
    ]
    claims = {c.claim_id: c for c in pack.claims}
    for record in pack.records():
        for name, claim_id in _refs(record):
            declared = RECORD_FIELD_SHAPES.get(f"{type(record).__name__}.{name}")
            claim = claims.get(claim_id)
            if declared is None or claim is None:
                continue
            if declared != CLAIM_FIELD_SHAPES.get(claim.field, "text") and not _fits(
                declared, claim.value
            ):
                found.append(f"{record.record_id}.{name} cites {claim_id}, which is not {declared}")
    return found


def _refs(record: Record) -> Iterator[tuple[str, str]]:
    """(field, claim id) for every claim a record cites."""
    for name, value in record:
        if name in ("record_id", "review", "review_state", "as_of"):
            continue
        if name in _CLAIM_LISTS and isinstance(value, list):
            yield from ((name, claim_id) for claim_id in value)
        elif name in _CLAIM_FIELDS and isinstance(value, str):
            yield name, value


_CLAIM_LISTS = frozenset(
    {"facts", "entry_requirements", "extra_costs", "funding_conditions", "rules", "exclusions"}
)
_CLAIM_FIELDS = frozenset(
    {
        *(f for f in JobPosting.model_fields if f not in Record.model_fields),
        *(f for f in LearningOption.model_fields if f not in Record.model_fields),
        *(f for f in Offering.model_fields if f not in Record.model_fields),
        *(f for f in FundingInstrument.model_fields if f not in Record.model_fields),
        "text",
        "source_span",
    }
) - {
    "source_id",
    "target_id",
    "vacancy_id",
    "requirement_ids",
    "target_ids",
    "option_id",
    "source_ids",
    "jurisdiction",
    "instrument_kind",
    "award_state",
}


def _own_sources(pack: Pack, record: Record) -> set[str]:
    by_id = {r.record_id: r for r in pack.records()}
    if isinstance(record, JobPosting | LearningOption):
        return {record.source_id}
    if isinstance(record, FundingInstrument):
        return set(record.source_ids)
    if isinstance(record, SkillRequirement):
        return _own_sources(pack, by_id[record.job_posting_id])
    if isinstance(record, Offering):
        return _own_sources(pack, by_id[record.option_id])
    if isinstance(record, Outcome):
        return _own_sources(pack, by_id[record.offering_id])
    return set()


def _references(pack: Pack) -> list[str]:
    found: list[str] = []
    claims = {c.claim_id: c for c in pack.claims}
    sources = {s.source_id for s in pack.sources}
    records = {r.record_id: r for r in pack.records()}
    targets = {t.target_id for t in pack.targets}
    skills = {s.skill_id for s in pack.skills}
    found += [
        f"{c.claim_id} names source {c.source_id}"
        for c in pack.claims
        if c.source_id not in sources
    ]
    links: list[tuple[str, str | None, type[Record] | None]] = []
    for r in pack.job_postings:
        links += [(r.record_id, r.target_id, None)]
        links += [(r.record_id, i, SkillRequirement) for i in r.requirement_ids]
    for q in pack.skill_requirements:
        links += [(q.record_id, q.job_posting_id, JobPosting), (q.record_id, q.target_id, None)]
    for o in pack.offerings:
        links += [(o.record_id, o.option_id, LearningOption)]
    for u in pack.outcomes:
        links += [(u.record_id, u.offering_id, Offering)]
    for record_id, linked, kind in links:
        if kind is None:
            if linked not in targets:
                found.append(f"{record_id} names target {linked}, which is not a target")
        elif not isinstance(records.get(linked or ""), kind):
            found.append(f"{record_id} names {linked}, which is not a {kind.__name__}")
    named = [q.skill_id for q in pack.skill_requirements] + [u.skill_id for u in pack.outcomes]
    for skill_id in named:
        if skill_id is not None and skill_id not in skills:
            found.append(f"{skill_id} is not a pack skill")
    if found:
        return found
    cited: set[str] = set()
    for record in pack.records():
        own = _own_sources(pack, record)
        for name, claim_id in _refs(record):
            cited.add(claim_id)
            claim = claims.get(claim_id)
            if claim is None:
                found.append(f"{record.record_id}.{name} cites {claim_id}, which is not a claim")
            elif claim.source_id not in own:
                found.append(
                    f"{record.record_id}.{name} cites {claim_id}, from {claim.source_id}, "
                    "not from its own source"
                )
    found += [f"claim {c} is cited by no record" for c in sorted(set(claims) - cited)]
    return found


def _reviews(pack: Pack) -> list[str]:
    found = []
    for record in pack.records():
        if record.review_state is ReviewState.REVIEWED and record.review is None:
            found.append(f"{record.record_id} is reviewed without a review record")
        if record.as_of > pack.dated:
            found.append(f"{record.record_id} is dated after its pack")
    return found


def _outcomes(pack: Pack) -> list[str]:
    found = []
    for outcome in pack.outcomes:
        if outcome.level_on_completion is None:
            continue
        if outcome.rubric_version is None:
            found.append(f"{outcome.record_id} has a level without a rubric version")
        elif outcome.confidence == "unsupported":
            found.append(f"{outcome.record_id} is unsupported, so its level must be null")
        elif outcome.evidence_kind == "topic_mention":
            found.append(f"{outcome.record_id} is a topic mention, so its level must be null")
    return found


def _splits(pack: Pack) -> list[str]:
    splits: dict[str, set[Split]] = {}
    for source in pack.sources:
        splits.setdefault(source.template_family, set()).add(source.split)
    return [
        f"template family {family} is in both splits"
        for family, found in sorted(splits.items())
        if len(found) > 1
    ]


def _spans(pack: Pack) -> list[str]:
    routes = {s.source_id: s.route for s in pack.sources}
    found = []
    for claim in pack.claims:
        route = routes.get(claim.source_id)
        if route is Route.FETCH and claim.span.pointer is not None:
            found.append(f"{claim.claim_id}: a fetched page's claim cites offsets, not a pointer")
        if route is Route.ADZUNA and claim.span.pointer is None:
            found.append(f"{claim.claim_id}: an API response's claim cites a JSON pointer")
    return found


def pack_path(version: str) -> Path:
    return PACKS_DIR / f"england-option-pack-{version}.json"


def load_pack(version: str, *, pins: dict[str, str] | None = None) -> Pack:
    """A committed version: its bytes checked against its pin, then parsed and checked."""
    pinned = (PINS if pins is None else pins).get(version)
    if pinned is None:
        raise OptionPackError(f"no committed option pack version {version}")
    data = pack_path(version).read_bytes()
    if hashlib.sha256(data).hexdigest() != pinned:
        raise OptionPackError(f"option pack {version} is not its pinned bytes")
    pack = parse_pack(json.loads(data))
    if pack.pack_version != version:
        raise OptionPackError(f"the file of version {version} says {pack.pack_version}")
    problems = check_pack(pack)
    if problems:
        raise OptionPackError(f"option pack {version}: {problems[0]}")
    return pack


def schema() -> dict[str, Any]:
    """The format as JSON Schema, committed beside the packs (`SCHEMA_PATH`): the pack's
    structure, each value shape, and the shape each claim field and record field declares."""
    exported = Pack.model_json_schema()
    exported["x-value-shapes"] = {name: SHAPES[name].json_schema() for name in sorted(SHAPES)}
    exported["x-claim-field-shapes"] = dict(sorted(CLAIM_FIELD_SHAPES.items()))
    exported["x-claim-field-shape-otherwise"] = "text"
    exported["x-record-field-shapes"] = dict(sorted(RECORD_FIELD_SHAPES.items()))
    return exported


def dump_pack(pack: Pack) -> str:
    """A pack's canonical text: one target, skill, source, claim or record per line, in the
    format's field order, defaults left out. Every committed version is in this form."""
    data = pack.model_dump(mode="json", exclude_defaults=True)
    lines = ["{"]
    for n, (key, value) in enumerate(data.items()):
        comma = "," if n < len(data) - 1 else ""
        if isinstance(value, list) and key != "notes":
            if not value:
                lines.append(f"  {json.dumps(key)}: []{comma}")
                continue
            lines.append(f"  {json.dumps(key)}: [")
            lines += [
                "    " + json.dumps(item, ensure_ascii=False) + ("," if m < len(value) - 1 else "")
                for m, item in enumerate(value)
            ]
            lines.append("  ]" + comma)
        else:
            lines.append(f"  {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}{comma}")
    return "\n".join([*lines, "}"]) + "\n"
