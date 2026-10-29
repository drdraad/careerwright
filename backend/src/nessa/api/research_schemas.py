"""The research API contract: acquisitions, source attempts, jobs with their copies and
claims, and freshness (Task 7A). Enums come from the domain modules once (GC10)."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import Field

from nessa.api.schemas import ResponseModel, RunOut
from nessa.evidence.acquisition import AcquisitionSummary, JobView, Skipped, TargetView
from nessa.evidence.freshness import Freshness, FreshnessKind, FreshnessView
from nessa.evidence.records import (
    AdvertiserKind,
    AttemptStatus,
    ClaimField,
    DescriptionKind,
    InputRoute,
    Location,
    Retention,
    RightsClass,
    Salary,
    SourceSpan,
    ValidationState,
    WorkMode,
)
from nessa.evidence.search import SearchProposal
from nessa.evidence.store import AttemptRow, ClaimRow, CopyRow


class SourceAttemptOut(ResponseModel):
    """One try to obtain a source (spec section 18, SourceAttempt). Blocked and failed tries
    are kept with their reason; a URL never carries a credential."""

    attempt_id: uuid.UUID
    route: InputRoute
    provider: str
    requested_url: str | None
    final_url: str | None
    redirects: list[str]
    status: AttemptStatus
    reason: str | None = Field(description="Why it was blocked or failed: a label, never text.")
    transient: bool
    retry_of: uuid.UUID | None
    http_status: int | None
    content_type: str | None
    content_sha256: str | None
    byte_count: int | None
    rights_class: RightsClass | None
    rights_status: str | None
    retention: Retention | None
    http_requests: int
    cost_nano_usd: int | None = Field(description="0 for page fetches and Adzuna's free tier.")
    started_at: datetime
    finished_at: datetime | None

    @classmethod
    def of(cls, row: AttemptRow) -> "SourceAttemptOut":
        return cls(
            attempt_id=row.attempt_id,
            route=row.route,
            provider=row.provider,
            requested_url=row.requested_url or None,
            final_url=row.final_url,
            redirects=row.redirects,
            status=row.status,
            reason=row.reason,
            transient=row.transient,
            retry_of=row.retry_of,
            http_status=row.http_status,
            content_type=row.content_type,
            content_sha256=row.content_sha256,
            byte_count=row.byte_count,
            rights_class=RightsClass(row.rights_class) if row.rights_class else None,
            rights_status=row.rights_status,
            retention=Retention(row.retention) if row.retention else None,
            http_requests=row.http_requests,
            cost_nano_usd=row.cost_nano_usd,
            started_at=row.started_at,
            finished_at=row.finished_at,
        )


class TargetOut(ResponseModel):
    position: int
    route: InputRoute
    url: str | None
    query: dict[str, Any] | None
    status: str = Field(
        description="queued, succeeded, blocked, failed, cancelled, or not_attempted (the run "
        "ended before it)."
    )
    attempts: list[SourceAttemptOut]

    @classmethod
    def of(cls, view: TargetView) -> "TargetOut":
        return cls(
            position=view.target.position,
            route=view.target.route,
            url=view.target.url,
            query=view.target.query,
            status=view.status,
            attempts=[SourceAttemptOut.of(a) for a in view.attempts],
        )


class SkippedOut(ResponseModel):
    """A URL not fetched by this request: another run is fetching it (`in_flight`), or it
    failed recently and waits out its back-off (`backing_off`, until `retry_at`)."""

    url: str
    reason: str
    run_id: uuid.UUID | None
    retry_at: datetime | None

    @classmethod
    def of(cls, skipped: Skipped) -> "SkippedOut":
        return cls(
            url=skipped.url, reason=skipped.reason, run_id=skipped.run_id, retry_at=skipped.retry_at
        )


class AcquisitionSummaryOut(ResponseModel):
    succeeded: int
    blocked: int
    failed: int

    @classmethod
    def of(cls, summary: AcquisitionSummary) -> "AcquisitionSummaryOut":
        return cls(succeeded=summary.succeeded, blocked=summary.blocked, failed=summary.failed)


class AcquisitionOut(ResponseModel):
    run: RunOut
    targets: list[TargetOut]
    job_ids: list[uuid.UUID] = Field(description="The jobs this run's sources produced so far.")
    summary: AcquisitionSummaryOut | None = Field(
        description="A complete run's outcome per target; none until it is complete."
    )


class SubmittedAcquisitionOut(ResponseModel):
    acquisition: AcquisitionOut | None = Field(
        description="None when every URL was skipped: nothing was started."
    )
    skipped: list[SkippedOut]


class FreshnessOut(ResponseModel):
    """How current a source's data is, from its last successful retrieval (spec section 11).
    A failed refresh moves `last_attempt_at` only."""

    kind: FreshnessKind
    state: Freshness
    label: str
    usable_as_current: bool
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    valid_until: datetime | None
    verified_until: datetime | None
    max_age_hours: int

    @classmethod
    def of(cls, view: FreshnessView) -> "FreshnessOut":
        return cls(
            kind=view.kind,
            state=view.state,
            label=view.label,
            usable_as_current=view.usable_as_current,
            last_attempt_at=view.times.last_attempt_at,
            last_success_at=view.times.last_success_at,
            valid_until=view.times.valid_until,
            verified_until=view.verified_until,
            max_age_hours=int(view.max_age.total_seconds() // 3600),
        )


class JobCopyOut(ResponseModel):
    copy_id: uuid.UUID
    attempt_id: uuid.UUID
    provider: str
    route: InputRoute
    source_url: str | None
    source_job_id: str | None
    description_kind: DescriptionKind | None
    rights_status: str | None
    retrieved_at: datetime

    @classmethod
    def of(cls, row: CopyRow, attempt: AttemptRow | None) -> "JobCopyOut":
        return cls(
            copy_id=row.copy_id,
            attempt_id=row.attempt_id,
            provider=row.provider,
            route=attempt.route if attempt else InputRoute.FETCH,
            source_url=(attempt.final_url or attempt.requested_url) if attempt else None,
            source_job_id=row.copy.source_job_id,
            description_kind=row.copy.description_kind,
            rights_status=attempt.rights_status if attempt else None,
            retrieved_at=row.created_at,
        )


class JobOut(ResponseModel):
    """A canonical job: the values of its newest full copy, and every source copy. Unknown
    values are null, never zero; predicted pay is never advertised pay."""

    job_id: uuid.UUID
    title: str
    employer: str | None = Field(description="Null when the advert does not name the employer.")
    advertiser: AdvertiserKind
    locations: list[Location]
    work_mode: WorkMode | None
    salary: Salary | None
    salary_confirmed: bool = Field(description="True only for pay the source advertises.")
    employment_type: str | None
    date_posted: date | None
    description_kind: DescriptionKind | None
    exemplar: bool = Field(
        description="The person's pasted example of a target: never a live vacancy."
    )
    favourite: bool
    first_seen_at: datetime
    freshness: FreshnessOut
    copies: list[JobCopyOut]

    @classmethod
    def of(cls, view: JobView) -> "JobOut":
        primary = view.primary
        full = any(c.copy.description_kind is DescriptionKind.FULL for c in view.copies)
        return cls(
            job_id=view.job.job_id,
            title=primary.title,
            employer=primary.employer if primary.advertiser is not AdvertiserKind.AGENCY else None,
            advertiser=primary.advertiser,
            locations=primary.locations,
            work_mode=primary.work_mode,
            salary=primary.salary,
            salary_confirmed=primary.salary is not None
            and primary.salary.basis.value == "advertised",
            employment_type=primary.employment_type,
            date_posted=primary.date_posted,
            description_kind=DescriptionKind.FULL
            if full
            else (DescriptionKind.SNIPPET if view.copies else None),
            exemplar=view.job.exemplar,
            favourite=view.job.favourite,
            first_seen_at=view.job.first_seen_at,
            freshness=FreshnessOut.of(view.freshness),
            copies=[JobCopyOut.of(c, view.attempts.get(c.attempt_id)) for c in view.copies],
        )


class SourceClaimOut(ResponseModel):
    """One field value with the span that supports it (spec section 18, SourceClaim)."""

    claim_id: int
    copy_id: uuid.UUID
    attempt_id: uuid.UUID
    field: ClaimField
    value: Any
    validation: ValidationState
    issue: str | None
    span: SourceSpan
    retrieved_at: datetime
    published_on: date | None
    valid_until: datetime | None

    @classmethod
    def of(cls, row: ClaimRow) -> "SourceClaimOut":
        return cls(
            claim_id=row.claim_id,
            copy_id=row.copy_id,
            attempt_id=row.attempt_id,
            field=row.claim.field,
            value=row.claim.model_dump(mode="json")["value"],
            validation=row.claim.validation,
            issue=row.claim.issue,
            span=row.claim.span,
            retrieved_at=row.retrieved_at,
            published_on=row.published_on,
            valid_until=row.valid_until,
        )


class SearchOut(ResponseModel):
    """A source search: candidate pages only, never claims. The person chooses which to
    acquire; a candidate the search did not return is marked ungrounded."""

    search_id: uuid.UUID
    run: RunOut
    proposal: SearchProposal | None = Field(description="None until the run is complete.")


class JobDetailOut(ResponseModel):
    job: JobOut
    claims: list[SourceClaimOut]


class JobPage(ResponseModel):
    """A page of jobs, with counts that never double count a multi-city job and coverage
    that says how many sources were checked. An empty page says why (STATE-02)."""

    items: list[JobOut]
    next_cursor: str | None
    total_jobs: int = Field(description="Distinct jobs: a multi-city job counts once.")
    city_counts: dict[str, int] = Field(
        description="Jobs appearing in each city; a multi-city job appears in each."
    )
    coverage: dict[str, int] = Field(
        description="Sources tried, by their latest attempt's status (succeeded, blocked, "
        "failed, pending)."
    )
    empty_reason: str | None = Field(
        description="When there are no jobs: no_sources_checked, no_source_retrieved (every "
        "source failed or was blocked: not 'no vacancies') or none_found_in_sources_checked."
    )
