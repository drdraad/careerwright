"""Records of the evidence and acquisition module (spec section 18: SourceAttempt,
SourceClaim, JobPosting).

A source attempt is one try to obtain one source by one input route: a fetched page, an
Adzuna request or text a person pasted. A claim is one field value read from a source, with
the span that supports it, its dates and how it was validated. A job copy is one source's
view of a vacancy; deduplication (`nessa.evidence.jobs`) groups copies into one canonical
job without discarding any. Money is integer minor units; unknown is null, never zero.
"""

from datetime import date, datetime
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

SHA256_PATTERN = r"^[0-9a-f]{64}$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InputRoute(StrEnum):
    """How a source reached Nessa. Pasted text is its own route, never a retrieval."""

    FETCH = "fetch"  # a permitted page fetched by the acquisition worker
    ADZUNA = "adzuna"  # the Adzuna job-search API (live-vacancy mode)
    PASTED_TEXT = "pasted_text"  # text a person pasted, with its own provenance


class AttemptStatus(StrEnum):
    PENDING = "pending"  # recorded before the request; a crash leaves it to be settled
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"  # refused by policy (URL, address, source manifest or robots.txt)
    FAILED = "failed"  # tried and did not get a usable source


class AttemptReason(StrEnum):
    """Why an attempt was blocked or failed: a label, classified from types and statuses,
    never a message. The URL checks' refusals (`addresses.UrlRefusal`) are among them."""

    # The URL and address checks (blocked)
    MALFORMED_URL = "malformed_url"
    URL_TOO_LONG = "url_too_long"
    SCHEME_NOT_ALLOWED = "scheme_not_allowed"
    CREDENTIALS_IN_URL = "credentials_in_url"
    PORT_NOT_ALLOWED = "port_not_allowed"
    HOST_NOT_ALLOWED = "host_not_allowed"
    ADDRESS_NOT_ALLOWED = "address_not_allowed"
    REDIRECT_DOWNGRADE = "redirect_downgrade"
    # The source permission manifest and robots.txt (blocked)
    SOURCE_DENIED = "source_denied"
    SOURCE_API_ONLY = "source_api_only"
    ROBOTS_DISALLOWED = "robots_disallowed"
    ADZUNA_CREDENTIALS_NOT_CONFIGURED = "adzuna_credentials_not_configured"
    # Tried, and no usable source (failed); `http_status` gives an HTTP error's status
    HTTP_ERROR = "http_error"
    ROBOTS_UNREACHABLE = "robots_unreachable"
    TIMEOUT = "timeout"
    TOO_LARGE = "too_large"
    TOO_MANY_REDIRECTS = "too_many_redirects"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    UNSUPPORTED_CONTENT_ENCODING = "unsupported_content_encoding"
    HOST_NOT_FOUND = "host_not_found"
    TLS_FAILED = "tls_failed"
    CONNECTION_FAILED = "connection_failed"
    RESPONSE_INVALID = "response_invalid"
    BODY_HASH_MISMATCH = "body_hash_mismatch"
    ACQUISITION_WORKER_UNAVAILABLE = "acquisition_worker_unavailable"
    INTERRUPTED = "interrupted"  # a crash during the request: settled when the step re-runs
    ACCESS_REVOKED = "access_revoked"
    INTERNAL_ERROR = "internal_error"  # a defect in the acquisition worker, never transient


class Extraction(StrEnum):
    """Why a retrieved source gave no posting that could be published. Only `no_job_posting`
    (its structured data was read and holds none) says no vacancy was there; the others
    say the page could not be read, which is never "none found" (GC6)."""

    NO_STRUCTURED_DATA = "no_structured_data"  # no JSON-LD at all (model extraction: round 2)
    JSONLD_INVALID = "jsonld_invalid"  # not valid JSON, or a job posting without a title
    CONFLICTING_JOB_POSTINGS = "conflicting_job_postings"  # postings that disagree
    NO_JOB_POSTING = "no_job_posting"  # structured data read: no job posting in it


UNREADABLE = frozenset(
    {Extraction.NO_STRUCTURED_DATA, Extraction.JSONLD_INVALID, Extraction.CONFLICTING_JOB_POSTINGS}
)


class RightsClass(StrEnum):
    """The page classes of the session 1 rights policy (H-06; `corpus/README.md`)."""

    GOVUK = "govuk"
    PUBLIC_SECTOR = "public-sector"
    COURSE_PROVIDER = "course-provider"
    PROFESSIONAL_BODY = "professional-body"
    EMPLOYER_POSTING = "employer-posting"
    JOB_BOARD = "job-board"
    OTHER = "other"


class Retention(StrEnum):
    """What a workspace keeps of a source's body."""

    BODY = "body"  # the body, sealed, private to the workspace ("keep privately")
    EXCERPTS = "excerpts"  # the hash and the claims' minimal excerpts only


class ValidationState(StrEnum):
    """How a claim's value was established. Only deterministic code approves a value."""

    STRUCTURED = "structured"  # parsed from structured data (JSON-LD, an official API)
    USER_SUPPLIED = "user_supplied"  # stated by the person with pasted text
    QUARANTINED = "quarantined"  # malformed, conflicting or unsupported: never used


class ClaimField(StrEnum):
    TITLE = "title"
    EMPLOYER = "employer"
    LOCATION = "location"
    WORK_MODE = "work_mode"
    SALARY = "salary"
    DATE_POSTED = "date_posted"
    VALID_THROUGH = "valid_through"
    EMPLOYMENT_TYPE = "employment_type"
    DESCRIPTION = "description"
    APPLY_URL = "apply_url"
    SOURCE_JOB_ID = "source_job_id"


class PayBasis(StrEnum):
    """Advertised (stated by the source), predicted (a provider's estimate, such as
    Adzuna's `salary_is_predicted`) and unknown stay distinct (spec section 6)."""

    ADVERTISED = "advertised"
    PREDICTED = "predicted"
    UNKNOWN = "unknown"


class SalaryPeriod(StrEnum):
    """The period a source states pay per (the profile's salary floor has its own)."""

    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    HOUR = "hour"


class DescriptionKind(StrEnum):
    FULL = "full"
    SNIPPET = "snippet"  # never treated as a full description (JOB-05)


class AdvertiserKind(StrEnum):
    EMPLOYER = "employer"  # the hiring employer advertises its own vacancy
    AGENCY = "agency"  # a staffing agency advertises for an employer it may not name
    UNKNOWN = "unknown"


class WorkMode(StrEnum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"


class SourceSpan(StrictModel):
    """Where a value is in its source: character offsets into the source's text (a page's
    decoded HTML or the pasted text), or for an API response a JSON pointer; with a minimal
    excerpt either way, so a reviewer can find what supported the value at retrieval time."""

    source_sha256: str = Field(pattern=SHA256_PATTERN)
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)
    pointer: str | None = Field(default=None, max_length=200)
    excerpt: str = Field(max_length=400)

    @model_validator(mode="after")
    def _located(self) -> "SourceSpan":
        offsets = self.start is not None and self.end is not None
        if offsets == (self.pointer is not None) or (self.start is None) != (self.end is None):
            raise ValueError("a span has offsets or a pointer, not both and not neither")
        if offsets and self.end is not None and self.start is not None and self.end <= self.start:
            raise ValueError("a span ends after it starts")
        return self


class Salary(StrictModel):
    """Pay as the source gives it, before any normalisation. GBP in minor units; a period
    the source does not state stays None (never assumed to be a year)."""

    currency: str = Field(pattern=r"^[A-Z]{3}$")
    minimum_minor_units: int | None = Field(default=None, ge=0)
    maximum_minor_units: int | None = Field(default=None, ge=0)
    period: SalaryPeriod | None
    basis: PayBasis

    @model_validator(mode="after")
    def _ordered(self) -> "Salary":
        low, high = self.minimum_minor_units, self.maximum_minor_units
        if low is None and high is None:
            raise ValueError("a salary has at least one amount")
        if low is not None and high is not None and high < low:
            raise ValueError("a salary's maximum is not below its minimum")
        return self


class Location(StrictModel):
    label: str = Field(min_length=1, max_length=200)
    locality: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=60)


ClaimValue = str | Salary | Location | date | None
# A text value keeps no more of its source than an excerpt does (review A M4), so a
# reference-only page's claims never hold more than its excerpts. An apply link is a
# checked URL, not page text, and is kept whole.
CLAIM_TEXT_CHARS = 200


class Claim(StrictModel):
    """One field value from one source (spec section 18, SourceClaim)."""

    field: ClaimField
    value: ClaimValue
    span: SourceSpan
    validation: ValidationState
    issue: str | None = Field(default=None, max_length=120)  # why a claim is quarantined

    @field_validator("value")
    @classmethod
    def _bounded(cls, value: ClaimValue, info: ValidationInfo) -> ClaimValue:
        if isinstance(value, str) and info.data.get("field") is not ClaimField.APPLY_URL:
            return value[:CLAIM_TEXT_CHARS]
        return value


class JobCopy(StrictModel):
    """One source's view of one vacancy, every value with its claim. Values are None when
    the source does not give them: unknown, never empty or zero."""

    source_job_id: str | None = Field(default=None, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    employer: str | None = Field(default=None, max_length=300)
    advertiser: AdvertiserKind
    locations: list[Location] = Field(default_factory=list, max_length=20)
    work_mode: WorkMode | None = None
    salary: Salary | None = None
    date_posted: date | None = None
    valid_through: datetime | None = None
    employment_type: str | None = Field(default=None, max_length=60)
    description_kind: DescriptionKind | None = None
    # Fingerprints of the description's normalised words (`jobs.description_fingerprints`):
    # all of them, and the first few, which a snippet of the same advert shares.
    description_fingerprint: str | None = Field(default=None, pattern=SHA256_PATTERN)
    description_lead: str | None = Field(default=None, pattern=SHA256_PATTERN)
    apply_url: str | None = Field(default=None, max_length=2_048)
    claims: list[Claim] = Field(default_factory=list)
    extraction_error: str | None = Field(default=None, max_length=120)
