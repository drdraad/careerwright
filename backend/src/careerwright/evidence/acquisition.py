"""Acquisition runs, pasted text, jobs and favourites (spec sections 6, 7 and 11; ADR 0009).

API side: an acquisition run is submitted with up to ten URLs or one Adzuna search (live-
vacancy workspaces only). A URL already being fetched in this workspace is joined, not
fetched again, and one that failed recently waits out its back-off (FRESH-04). Pasted text
is a separate input route: recorded at once, never fetched, kept as the person's own
example of a target (at most three per target, JOB-06) and never a live vacancy.

Worker side, one DBOS step per target (`careerwright.evidence.workflow`): the attempt is recorded
before the request, the restricted acquisition worker is asked for the source, and the
result is recorded in one transaction: the attempt, the body where the rights class permits
keeping it (sealed), each job copy with its claims, attached to a canonical job by
`jobs.same_job`. A failed or blocked source is an attempt with its reason, never "no
vacancies"; a failed refresh moves a job's last attempt and never its last success. A
cancelled run fetches nothing more. A page whose structured data gave no posting is handed,
in the same transaction, to a model extraction run of its own (`extraction_runs`), or says
why it was not.
"""

import base64
import dataclasses
import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any
from urllib.parse import urlsplit

from pydantic import Field, StringConstraints, model_validator

from careerwright.catalogue.pay import FloorCounts, FloorVerdict, floor_counts
from careerwright.config import RuntimeMode
from careerwright.db import Engine, Tx, run_transaction
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.evidence import role_store, store
from careerwright.evidence.acquire import ADZUNA_PROVIDER, AcquisitionResult
from careerwright.evidence.addresses import CheckedUrl, UrlRefusal, check_url
from careerwright.evidence.adzuna import CREDENTIAL_PARAMETERS, AdzunaQuery, recorded_url
from careerwright.evidence.corroboration import check_title
from careerwright.evidence.extraction_runs import (
    ModelSpendEstimate,
    acquisition_model_spend,
    model_readable,
    start_extraction,
)
from careerwright.evidence.freshness import (
    FreshnessKind,
    FreshnessView,
    RefreshDecision,
    SourceTimes,
    freshness,
    refresh_decision,
)
from careerwright.evidence.jobs import (
    canonical_facts,
    description_fingerprints,
    facts_json,
    job_against_floor,
    title_key,
)
from careerwright.evidence.recording import record_copies
from careerwright.evidence.records import (
    AdvertiserKind,
    AttemptReason,
    AttemptStatus,
    Claim,
    ClaimField,
    DescriptionKind,
    ExtractionOutcome,
    InputRoute,
    JobCopy,
    Location,
    Retention,
    SourceSpan,
    StrictModel,
    ValidationState,
)
from careerwright.evidence.redaction import redact_text
from careerwright.evidence.service_client import AcquisitionClient, AcquisitionUnavailableError
from careerwright.identity import run_store
from careerwright.identity import store as identity_store
from careerwright.identity.access import Actor
from careerwright.identity.activity import (
    ActivityRuntime,
    Outcome,
    cancelled,
    failed,
    publish,
    succeeded,
)
from careerwright.identity.failures import FailureClass
from careerwright.identity.keyring import Keyring, RecordContext
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.records import EventKind, Run, RunKind
from careerwright.identity.runs import open_output, output_context, submit_keyless_run, visible_run
from careerwright.identity.spend import SpendLimits
from careerwright.identity.spend_limits import spend_summary
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile.commands import current_profile
from careerwright.profile.role_evidence import salary_floor
from careerwright.vocabulary import DataMode, WorkState

MAX_URLS = 10
MAX_EXEMPLARS_PER_TARGET = 3
MAX_PASTED_CHARS = 50_000
DOCUMENT_KIND = "source_document"
PASTED_PROVIDER = "pasted_text"
PASTED_RIGHTS = "pasted by the person: their own input, kept privately in this workspace"
RECORDABLE_PORTS = frozenset(range(1, 65_536))

Url = Annotated[str, StringConstraints(min_length=1, max_length=2_048)]


def document_context(workspace_id: uuid.UUID, attempt_id: uuid.UUID) -> RecordContext:
    return RecordContext(DOCUMENT_KIND, str(workspace_id), str(attempt_id))


# --- submission (API) -------------------------------------------------------------------


class SubmitAcquisition(StrictModel):
    """Up to ten URLs, or one Adzuna search: never both."""

    urls: list[Url] = Field(default_factory=list, max_length=MAX_URLS)
    adzuna: AdzunaQuery | None = None

    @model_validator(mode="after")
    def _one_route(self) -> "SubmitAcquisition":
        if bool(self.urls) == (self.adzuna is not None):
            raise ValueError("give either urls or adzuna")
        return self


class SkipReason(StrEnum):
    IN_FLIGHT = "in_flight"  # another run is fetching it: joined
    BACKING_OFF = "backing_off"  # it failed recently: tried again from `retry_at`


@dataclass(frozen=True)
class Skipped:
    url: str
    reason: SkipReason
    run_id: uuid.UUID | None = None
    retry_at: datetime | None = None


@dataclass(frozen=True)
class SubmittedAcquisition:
    run: Run | None  # None when every URL was joined or is backing off
    skipped: list[Skipped] = field(default_factory=list)


def _refused(reason: str) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        "That address can't be recorded safely. Remove any user name, password or key from "
        "it, then try again.",
        stage=ErrorStage.REQUEST,
        details={"field": "urls", "reason": reason},
    )


@dataclass(frozen=True)
class RefusedTarget:
    """A submitted URL the checks refuse (a `javascript:` scheme, a port, a local name, a
    private address): recorded by its refusal and its host as plain text, never as a URL."""

    refusal: UrlRefusal
    host: str | None


def _host_text(url: str) -> str | None:
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return None
    return host[:253] if host else None


def _recordable(url: str) -> str | RefusedTarget:
    """The checked URL as it will be recorded, or the refusal the worker records as a blocked
    attempt, so a policy denial is always on record (ACQ-06). One that cannot be recorded
    safely even as a refusal (a credential in it, malformed, too long) is refused now. Any
    port is recordable: an http(s) URL to a public name is safe to show as a link, and the
    worker's own check refuses a port other than 80 or 443 as a blocked attempt."""
    checked = check_url(url, allowed_ports=RECORDABLE_PORTS)
    if checked in (UrlRefusal.MALFORMED, UrlRefusal.URL_TOO_LONG, UrlRefusal.CREDENTIALS_IN_URL):
        raise _refused(str(checked))
    lowered = url.lower()
    if any(f"{name}=" in lowered for name in CREDENTIAL_PARAMETERS):
        raise _refused(UrlRefusal.CREDENTIALS_IN_URL.value)
    if isinstance(checked, CheckedUrl):
        return checked.url
    return RefusedTarget(checked, _host_text(url))


def submit_acquisition(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: SubmitAcquisition,
    *,
    runtime_mode: RuntimeMode,
    now: datetime,
) -> SubmittedAcquisition:
    workspace = visible_workspace(tx, workspace_id)
    if command.adzuna is not None and workspace.data_mode is not DataMode.LIVE_VACANCY:
        raise CareerwrightError(
            ErrorCode.MODE_NOT_SUPPORTED,
            "Adzuna searches run only in a live-vacancy workspace.",
            stage=ErrorStage.EXECUTION,
        )
    each = [_recordable(url) for url in command.urls]
    # A URL given twice is one target; each refused one is its own (it has no URL to match).
    recordable = [
        r for n, r in enumerate(each) if isinstance(r, RefusedTarget) or r not in each[:n]
    ]
    urls = [r for r in recordable if isinstance(r, str)]
    refused = [r for r in recordable if isinstance(r, RefusedTarget)]
    skipped: list[Skipped] = []
    started: list[str] = []
    in_flight = store.urls_in_flight(tx, workspace_id, urls)
    for url in urls:
        failures, last = store.url_history(tx, workspace_id, url)
        decision = refresh_decision(
            in_flight=url in in_flight,
            consecutive_failures=failures,
            last_attempt_at=last,
            now=now,
        )
        if decision.action is RefreshDecision.Action.JOIN:
            skipped.append(Skipped(url, SkipReason.IN_FLIGHT, run_id=in_flight[url]))
        elif decision.action is RefreshDecision.Action.BACK_OFF:
            skipped.append(Skipped(url, SkipReason.BACKING_OFF, retry_at=decision.retry_at))
        else:
            started.append(url)
    if not started and not refused and command.adzuna is None:
        return SubmittedAcquisition(None, skipped)
    run = submit_keyless_run(
        tx,
        actor,
        workspace_id,
        RunKind.ACQUISITION,
        runtime_mode=runtime_mode,
        workflow_name=run_store.ACQUISITION_WORKFLOW,
        now=now,
    )
    if command.adzuna is not None:
        store.insert_target(
            tx,
            run_id=run.run_id,
            workspace_id=workspace_id,
            position=0,
            route=InputRoute.ADZUNA,
            url=None,
            query=command.adzuna.model_dump(),
        )
    queued = [r for r in recordable if r in started or isinstance(r, RefusedTarget)]
    for position, target in enumerate(queued):
        store.insert_target(
            tx,
            run_id=run.run_id,
            workspace_id=workspace_id,
            position=position,
            route=InputRoute.FETCH,
            url=target if isinstance(target, str) else None,
            query=None,
            refusal=target.refusal if isinstance(target, RefusedTarget) else None,
            refused_host=target.host if isinstance(target, RefusedTarget) else None,
        )
    return SubmittedAcquisition(run, skipped)


# --- pasted text (API) ------------------------------------------------------------------


class PasteText(StrictModel):
    """A posting the person pasted: their own example of a target (spec section 7, "User
    examples versus discovered corpus")."""

    target: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    text: Annotated[str, StringConstraints(min_length=1, max_length=MAX_PASTED_CHARS)]
    employer: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None
    city: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    source_url: Url | None = Field(
        default=None, description="Where the person copied it from, as a reference only."
    )


def _user_claim(
    field_name: ClaimField, value: Any, text: str, sha256: str, stated: str, pointer: str
) -> Claim:
    start = text.find(stated)
    span = (
        SourceSpan(source_sha256=sha256, start=start, end=start + len(stated), excerpt=stated[:200])
        if start >= 0 and stated
        else SourceSpan(source_sha256=sha256, pointer=pointer, excerpt=stated[:200])
    )
    return Claim(field=field_name, value=value, span=span, validation=ValidationState.USER_SUPPLIED)


def _reference_url(url: str) -> str:
    """A pasted text's source, kept only as a checked URL (it is shown as a link)."""
    recorded = _recordable(url)
    if isinstance(recorded, RefusedTarget):
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "That source address can't be kept. Give the page's web address, or leave it out.",
            stage=ErrorStage.REQUEST,
            details={"field": "source_url", "reason": recorded.refusal.value},
        )
    return recorded


def paste_text(
    tx: Tx,
    actor: Actor,
    workspace_id: uuid.UUID,
    command: PasteText,
    *,
    keyring: Keyring,
    now: datetime,
) -> uuid.UUID:
    """Records the pasted posting and returns its job's ID. Nothing is fetched."""
    visible_workspace(tx, workspace_id, lock=True)
    target = title_key(command.target)
    if not target:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Name the target role this example is for.",
            stage=ErrorStage.REQUEST,
            details={"field": "target", "reason": "no_words"},
        )
    if store.exemplar_count(tx, workspace_id, target) >= MAX_EXEMPLARS_PER_TARGET:
        raise CareerwrightError(
            ErrorCode.LIMIT_EXCEEDED,
            "You already have three examples for this target. Remove one to add another.",
            stage=ErrorStage.REQUEST,
            details={"reason": "exemplars_per_target", "limit": MAX_EXEMPLARS_PER_TARGET},
        )
    source_url = _reference_url(command.source_url) if command.source_url else None
    # Third parties' contact details go before anything is hashed, sealed or claimed.
    command = command.model_copy(
        update={
            "text": redact_text(command.text),
            "title": redact_text(command.title),
            "employer": redact_text(command.employer) if command.employer else None,
        }
    )
    body = command.text.encode()
    sha256 = hashlib.sha256(body).hexdigest()
    attempt_id = uuid.uuid4()
    store.insert_pasted_attempt(
        tx,
        attempt_id=attempt_id,
        workspace_id=workspace_id,
        created_by=actor.actor_id,
        requested_url=source_url,
        sha256=sha256,
        byte_count=len(body),
        rights_status=PASTED_RIGHTS,
    )
    store.insert_document(
        tx,
        attempt_id=attempt_id,
        workspace_id=workspace_id,
        sha256=sha256,
        sealed=keyring.seal(body, document_context(workspace_id, attempt_id)),
    )
    fingerprint, lead = description_fingerprints(command.text)
    claims = [
        _user_claim(ClaimField.TITLE, command.title, command.text, sha256, command.title, "/title"),
        Claim(
            field=ClaimField.DESCRIPTION,
            value=DescriptionKind.FULL.value,
            span=SourceSpan(
                source_sha256=sha256,
                start=0,
                end=len(command.text),
                excerpt=command.text[:200],
            ),
            validation=ValidationState.USER_SUPPLIED,
        ),
    ]
    if command.employer:
        claims.append(
            _user_claim(
                ClaimField.EMPLOYER,
                command.employer,
                command.text,
                sha256,
                command.employer,
                "/employer",
            )
        )
    locations = [Location(label=command.city, locality=command.city)] if command.city else []
    for location in locations:
        claims.append(
            _user_claim(
                ClaimField.LOCATION, location, command.text, sha256, location.label, "/city"
            )
        )
    copy = JobCopy(
        title=command.title,
        employer=command.employer or None,
        advertiser=AdvertiserKind.UNKNOWN,
        locations=locations,
        description_kind=DescriptionKind.FULL,
        description_fingerprint=fingerprint,
        description_lead=lead,
        claims=claims,
    )
    job_id = uuid.uuid4()
    copy_id = uuid.uuid4()
    store.insert_job(tx, job_id=job_id, workspace_id=workspace_id, exemplar=True, at=now)
    store.insert_copy(
        tx,
        copy_id=copy_id,
        workspace_id=workspace_id,
        job_id=job_id,
        attempt_id=attempt_id,
        provider=PASTED_PROVIDER,
        copy=copy,
        facts=facts_json(canonical_facts(copy, provider=PASTED_PROVIDER)),
        extra={"exemplar_for": target},
    )
    store.insert_claims(
        tx,
        workspace_id=workspace_id,
        attempt_id=attempt_id,
        copy_id=copy_id,
        copy=copy,
        retrieved_at=now,
    )
    identity_store.append_event(tx, workspace_id, EventKind.RESEARCH_UPDATED, str(attempt_id))
    return job_id


# --- reading (API) ----------------------------------------------------------------------


class TargetStatus(StrEnum):
    QUEUED = "queued"
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NOT_ATTEMPTED = "not_attempted"  # queued when its run ended: never tried


class ModelExtractionState(StrEnum):
    """How model extraction went for a page it may read (fix round 2, rulings 9-10)."""

    PENDING = "pending"  # its run is queued or running, with nothing recorded yet
    POSTINGS_READ = "postings_read"  # its run recorded postings, at least one published
    # Its run recorded postings that all disagree on a critical field: none is published
    # (review C M5).
    POSTINGS_CONFLICTING = "postings_conflicting"
    NO_POSTING_FOUND = "no_posting_found"  # read, and no advert found: not "none found"
    NOT_READ = "not_read"  # its run failed or was cancelled first, or verified nothing
    NOT_RUN = "not_run"  # never started: `not_run` says why


_RECORDED_STATES = {
    ExtractionOutcome.POSTINGS_RECORDED: ModelExtractionState.POSTINGS_READ,
    ExtractionOutcome.POSTINGS_CONFLICTING: ModelExtractionState.POSTINGS_CONFLICTING,
    ExtractionOutcome.NO_POSTING_FOUND: ModelExtractionState.NO_POSTING_FOUND,
    ExtractionOutcome.POSTINGS_UNVERIFIED: ModelExtractionState.NOT_READ,
}


def extraction_state(row: store.ExtractionRow) -> ModelExtractionState:
    """What was recorded decides, whatever the run's state: a run cancelled while its call
    was out keeps its accepted result (DUR-05), so its page reads as what it recorded (review
    C M2); with nothing recorded, the run's state does. `store.coverage` follows the same
    order."""
    if row.run_id is None:
        return ModelExtractionState.NOT_RUN
    if row.outcome is not None:
        return _RECORDED_STATES[row.outcome]
    if row.run_status in (WorkState.QUEUED, WorkState.RUNNING):
        return ModelExtractionState.PENDING
    return ModelExtractionState.NOT_READ


@dataclass(frozen=True)
class TargetView:
    target: store.TargetRow
    status: TargetStatus  # as stored, or `cancelled`/`not_attempted` for one its run never tried
    attempts: list[store.AttemptRow]
    retrieved: dict[uuid.UUID, int]  # attempt -> the adverts (copies) it returned
    # attempt -> its page's model extraction, for a page extraction may read
    extractions: dict[uuid.UUID, store.ExtractionRow] = field(default_factory=dict)


@dataclass(frozen=True)
class AcquisitionView:
    run: Run
    targets: list[TargetView]
    job_ids: list[uuid.UUID]

    @property
    def partial(self) -> bool:
        """A search here matched more adverts than it returned (or did not say how many)."""
        return any(
            a.route is InputRoute.ADZUNA
            and a.status is AttemptStatus.SUCCEEDED
            and (a.total_matching is None or a.total_matching > t.retrieved.get(a.attempt_id, 0))
            for t in self.targets
            for a in t.attempts[-1:]
        )


def _left_behind(attempt: store.AttemptRow) -> store.AttemptRow:
    """An attempt still `pending` once its run has ended (its recording rolled back, or a
    crash and then a cancel) reads as failed, interrupted: never as still in progress (fix
    round 3, review B M1; read side only, like `store.coverage`)."""
    if attempt.status is not AttemptStatus.PENDING:
        return attempt
    return dataclasses.replace(
        attempt, status=AttemptStatus.FAILED, reason=AttemptReason.INTERRUPTED
    )


def acquisition(tx: Tx, workspace_id: uuid.UUID, run_id: uuid.UUID) -> AcquisitionView:
    run = visible_run(tx, workspace_id, run_id)
    if run.kind is not RunKind.ACQUISITION:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such acquisition.", stage=ErrorStage.EXECUTION
        )
    ended = run.status not in (WorkState.QUEUED, WorkState.RUNNING)
    attempts = [_left_behind(a) if ended else a for a in store.attempts_of_run(tx, run_id)]
    copies = store.copies_of_attempts(tx, [a.attempt_id for a in attempts])
    extractions = store.extractions_of_attempts(tx, [a.attempt_id for a in attempts])
    retrieved: dict[uuid.UUID, int] = {}
    for c in copies:
        retrieved[c.attempt_id] = retrieved.get(c.attempt_id, 0) + 1
    views = []
    for target in store.targets(tx, run_id):
        status = TargetStatus(target.status)
        mine = [a for a in attempts if a.position == target.position]
        if status is TargetStatus.QUEUED and run.status is WorkState.CANCELLED:
            status = TargetStatus.CANCELLED
        elif status is TargetStatus.QUEUED and ended:
            # Tried, but its run ended with the try unrecorded: failed, never "not tried".
            status = TargetStatus.FAILED if mine else TargetStatus.NOT_ATTEMPTED
        counts = {a.attempt_id: retrieved.get(a.attempt_id, 0) for a in mine}
        read = {
            a.attempt_id: extractions[a.attempt_id] for a in mine if a.attempt_id in extractions
        }
        views.append(TargetView(target, status, mine, counts, read))
    job_ids = list(dict.fromkeys(c.job_id for c in copies if c.job_id is not None))
    return AcquisitionView(run, views, job_ids)


@dataclass(frozen=True)
class JobView:
    job: store.JobRow
    copies: list[store.CopyRow]
    primary: JobCopy
    freshness: FreshnessView
    attempts: dict[uuid.UUID, store.AttemptRow]


def _primary(copies: list[store.CopyRow]) -> JobCopy:
    """The copy whose values the job shows: the newest full description, else the newest."""
    full = [c for c in copies if c.copy.description_kind is DescriptionKind.FULL]
    return (full or copies)[-1].copy


def _view(
    job: store.JobRow,
    copies: list[store.CopyRow],
    attempts: dict[uuid.UUID, store.AttemptRow],
    now: datetime,
) -> JobView:
    primary = _primary(copies)
    times = SourceTimes(
        last_attempt_at=job.last_attempt_at,
        last_success_at=job.last_success_at,
        published_at=None,
        valid_from=None,
        valid_until=primary.valid_through,
    )
    return JobView(
        job,
        copies,
        primary,
        freshness(FreshnessKind.JOB, times, closed=job.closed_at is not None, now=now),
        {c.attempt_id: attempts[c.attempt_id] for c in copies if c.attempt_id in attempts},
    )


def _views(
    tx: Tx, jobs: list[store.JobRow], copies: list[store.CopyRow], now: datetime
) -> list[JobView]:
    """Each job with its copies and their attempts, read in one query for the lot."""
    attempts = store.attempts_by_id(tx, list({c.attempt_id for c in copies}))
    return [_view(j, [c for c in copies if c.job_id == j.job_id], attempts, now) for j in jobs]


class Coverage(StrEnum):
    """The latest outcome of each source tried (pasted text is not a source tried)."""

    SUCCEEDED = "succeeded"  # retrieved and read
    NO_POSTING_READABLE = store.NO_POSTING_READABLE  # retrieved, but no posting could be read
    # Retrieved and read by model extraction, which found no advert on it: not evidence
    # that there is no vacancy (fix round 2, ruling 9).
    NO_POSTING_FOUND_BY_MODEL = store.NO_POSTING_FOUND_BY_MODEL
    BLOCKED = "blocked"
    FAILED = "failed"
    PENDING = "pending"  # being fetched, or being read by model extraction, now


class EmptyReason(StrEnum):
    """Why a listing has no vacancy (STATE-02): never a bare empty list. Only
    `none_found_in_sources_checked` says the sources read held none, and only an API's own
    empty answer can give it (fix round 2, review B N1); a page model extraction read and
    found no advert on gives `no_posting_found_by_model`, never that (ruling 9)."""

    NO_SOURCES_CHECKED = "no_sources_checked"
    SOURCES_PENDING = "sources_pending"  # still being fetched or read: no answer yet
    NO_SOURCE_RETRIEVED = "no_source_retrieved"
    NO_POSTING_READABLE = "no_posting_readable"
    NO_POSTING_FOUND_BY_MODEL = "no_posting_found_by_model"
    NONE_FOUND_IN_SOURCES_CHECKED = "none_found_in_sources_checked"
    # Vacancies were found, and the person's salary floor left every one out (Task 7 slice
    # B): the counts say how many.
    ALL_BELOW_SALARY_FLOOR = "all_below_salary_floor"


@dataclass(frozen=True)
class JobListing:
    jobs: list[JobView]  # the page: vacancies and the person's examples, newest first
    more: bool
    total_jobs: int  # vacancies the salary floor kept: an example is never one
    exemplars: int
    city_counts: dict[str, int]  # vacancies only, as `total_jobs`
    coverage: dict[Coverage, int]
    adverts: store.AdvertCounts | None  # retrieved n of the total matching, for searches
    empty_reason: EmptyReason | None
    # What the next acquisition may spend on the person's key (MODEL-08); None in demo.
    model_spend: ModelSpendEstimate | None = None
    # The confirmed salary floor's effect on the vacancies; None when the person set none.
    salary_floor: FloorCounts | None = None


def _empty_reason(
    total_jobs: int, covered: dict[Coverage, int], left_out: int = 0
) -> EmptyReason | None:
    if total_jobs:
        return None
    # An answer still coming is said first (review B N7), before what the floor left out
    # (slice 7B fix round 1, review A M3).
    if covered.get(Coverage.PENDING):
        return EmptyReason.SOURCES_PENDING
    if left_out:
        return EmptyReason.ALL_BELOW_SALARY_FLOOR
    if not covered:
        return EmptyReason.NO_SOURCES_CHECKED
    retrieved = (
        Coverage.SUCCEEDED,
        Coverage.NO_POSTING_READABLE,
        Coverage.NO_POSTING_FOUND_BY_MODEL,
    )
    if not any(covered.get(c) for c in retrieved):
        return EmptyReason.NO_SOURCE_RETRIEVED
    if covered.get(Coverage.NO_POSTING_READABLE):
        return EmptyReason.NO_POSTING_READABLE
    if covered.get(Coverage.NO_POSTING_FOUND_BY_MODEL):
        return EmptyReason.NO_POSTING_FOUND_BY_MODEL
    return EmptyReason.NONE_FOUND_IN_SOURCES_CHECKED


def list_jobs(
    tx: Tx,
    workspace_id: uuid.UUID,
    *,
    favourites_only: bool,
    before: tuple[datetime, uuid.UUID] | None,
    limit: int,
    now: datetime,
    models: ModelChoice,
    defaults: SpendLimits,
) -> JobListing:
    """One page of jobs, and the workspace's totals, counted in the database (no cap), with
    what the next acquisition may spend on the person's key: the read the research view
    makes before an acquisition starts (fix round 3, item 5). Its hard maximum follows the
    workspace's run limit, the default one until limits are stored (`spend_summary`).

    The person's confirmed salary floor is a hard filter (Task 7 slice B): a vacancy whose
    advertised pay in the floor's period is below it is left out of the page and the
    totals, and the floor's counts say how many, and why the rest were kept
    (`jobs.job_against_floor`). An example is never filtered: it is not a vacancy."""
    workspace = visible_workspace(tx, workspace_id)
    run_limit = spend_summary(tx, workspace_id, now, defaults).limits.run_limit_nano_usd
    floor = salary_floor(current_profile(tx, workspace_id).document)
    counts: FloorCounts | None = None
    left_out: list[uuid.UUID] = []
    if floor is not None:
        verdicts = {
            job: job_against_floor(floor, salaries)
            for job, salaries in store.vacancy_pay(tx, workspace_id).items()
        }
        counts = floor_counts(floor, verdicts.values())
        left_out = sorted(j for j, (v, _) in verdicts.items() if v is FloorVerdict.BELOW)
    rows = store.jobs(
        tx,
        workspace_id,
        favourites_only=favourites_only,
        before=before,
        limit=limit + 1,
        left_out=left_out,
    )
    page, more = rows[:limit], len(rows) > limit
    views = _views(tx, page, store.copies_of_jobs(tx, [j.job_id for j in page]), now)
    vacancies, exemplars = store.job_totals(tx, workspace_id)
    total_jobs = vacancies - len(left_out)
    covered = {Coverage(k): n for k, n in store.coverage(tx, workspace_id).items()}
    return JobListing(
        views,
        more,
        total_jobs,
        exemplars,
        store.city_counts(tx, workspace_id, left_out),
        covered,
        store.advert_counts(tx, workspace_id),
        _empty_reason(total_jobs, covered, len(left_out)),
        acquisition_model_spend(
            models,
            synthetic=workspace.synthetic,
            data_mode=workspace.data_mode,
            run_limit_nano_usd=run_limit,
        ),
        counts,
    )


def job_detail(
    tx: Tx, workspace_id: uuid.UUID, job_id: uuid.UUID, *, now: datetime
) -> tuple[JobView, list[store.ClaimRow]]:
    visible_workspace(tx, workspace_id)
    job = store.job(tx, workspace_id, job_id)
    if job is None:
        raise CareerwrightError(ErrorCode.NOT_FOUND, "No such job.", stage=ErrorStage.EXECUTION)
    copies = store.copies_of_jobs(tx, [job_id])
    [view] = _views(tx, [job], copies, now)
    return view, store.claims_of_copies(tx, [c.copy_id for c in copies])


def set_favourite(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, job_id: uuid.UUID, *, favourite: bool
) -> None:
    """A mark never lands between a merge's move of the favourites and its removal of the
    merged job, where the removal would take it with it (review B M2): the workspace's
    recording lock is taken first, before the workspace's row, in the order the worker
    takes them; a job a merge removed meanwhile is then not found."""
    store.lock_workspace_records(tx, workspace_id)
    visible_workspace(tx, workspace_id, lock=True)
    if store.job(tx, workspace_id, job_id) is None:
        raise CareerwrightError(ErrorCode.NOT_FOUND, "No such job.", stage=ErrorStage.EXECUTION)
    if favourite:
        store.set_favourite(tx, workspace_id, job_id, actor.actor_id)
    else:
        store.clear_favourite(tx, workspace_id, job_id)


# --- the worker's steps -----------------------------------------------------------------


class TransientAcquisitionError(Exception):
    """A source failed in a way a later try may not (a timeout, a 503, the acquisition
    worker unreachable, the database busy). Carries a label only."""

    def __init__(self, label: str) -> None:
        super().__init__(f"transient acquisition failure ({label})")
        self.label = label


@dataclass(frozen=True)
class AcquisitionRuntime:
    activity: ActivityRuntime  # the worker's engine, keyring and clock, and run publication
    client: AcquisitionClient
    models: ModelChoice  # the model an extraction run started for a page pins

    @property
    def engine(self) -> Engine:
        return self.activity.engine

    @property
    def keyring(self) -> Keyring:
        return self.activity.keyring

    @property
    def clock(self) -> Callable[[], datetime]:
        return self.activity.clock


def target_positions(rt: AcquisitionRuntime, run_id: uuid.UUID) -> list[int]:
    with run_transaction(rt.engine, run_id) as tx:
        return [t.position for t in store.targets(tx, run_id)]


def _unavailable(target: store.TargetRow, now: datetime) -> AcquisitionResult:
    return AcquisitionResult(
        route=target.route,
        provider=ADZUNA_PROVIDER if target.route is InputRoute.ADZUNA else "unknown",
        requested_url=_target_url(target),
        status=AttemptStatus.FAILED,
        reason="acquisition_worker_unavailable",
        transient=True,
        fetched_at=now,
    )


def _target_url(target: store.TargetRow) -> str | None:
    if target.route is InputRoute.ADZUNA and target.query is not None:
        return recorded_url(AdzunaQuery.model_validate(target.query))
    return target.url


def _provider(target: store.TargetRow) -> str:
    """The host a target names (lower-case): the attempt records even a refused URL against
    its host."""
    if target.route is InputRoute.ADZUNA:
        return ADZUNA_PROVIDER
    if target.url is None:
        return target.refused_host or "unknown"
    return urlsplit(target.url).hostname or "unknown"


def _kept_body_checked(result: AcquisitionResult) -> AcquisitionResult:
    """A source whose class keeps its body must arrive with a body that hashes to what its
    spans index into; otherwise nothing of it is recorded and the attempt fails, labelled
    (review B M6), never a success with its body silently missing."""
    if result.status is not AttemptStatus.SUCCEEDED or result.retention is not Retention.BODY:
        return result
    body = base64.b64decode(result.body_b64) if result.body_b64 is not None else None
    if body is not None and hashlib.sha256(body).hexdigest() == result.content_sha256:
        return result
    return result.model_copy(
        update={
            "status": AttemptStatus.FAILED,
            "reason": AttemptReason.BODY_HASH_MISMATCH,
            "transient": False,
            "retention": None,
            "body_b64": None,
            "copies": [],
            "extraction": None,
            "extraction_text": None,
            "role_text": None,
            "total": None,
        }
    )


def _record_document(
    tx: Tx, rt: AcquisitionRuntime, run: Run, attempt_id: uuid.UUID, result: AcquisitionResult
) -> None:
    if result.body_b64 is not None and result.retention is Retention.BODY:
        store.insert_document(
            tx,
            attempt_id=attempt_id,
            workspace_id=run.workspace_id,
            sha256=result.content_sha256 or "",
            sealed=rt.keyring.seal(
                base64.b64decode(result.body_b64), document_context(run.workspace_id, attempt_id)
            ),
        )


def _record_role_page(
    tx: Tx,
    rt: AcquisitionRuntime,
    run: Run,
    attempt_id: uuid.UUID,
    result: AcquisitionResult,
    title: str,
) -> None:
    """A page read for role research (Task 6e): its body where its class keeps it, and what
    code found of the title in its visible text. Its postings are never recorded as jobs and
    it is never handed to a model; the text itself is not kept."""
    _record_document(tx, rt, run, attempt_id, result)
    check = check_title(title, result.role_text or "", result.copies, provider=result.provider)
    role_store.insert_page_check(
        tx, attempt_id=attempt_id, workspace_id=run.workspace_id, check=check
    )


def _record_copies(
    tx: Tx, rt: AcquisitionRuntime, run: Run, attempt_id: uuid.UUID, result: AcquisitionResult
) -> None:
    now = result.fetched_at
    _record_document(tx, rt, run, attempt_id, result)
    record_copies(
        tx,
        workspace_id=run.workspace_id,
        attempt_id=attempt_id,
        provider=result.provider,
        copies=result.copies,
        at=now,
    )


def acquire_target(rt: AcquisitionRuntime, run_id: uuid.UUID, position: int) -> dict[str, str]:
    """One target: the attempt is recorded first, the source is asked for, and the result
    is recorded. Raises `TransientAcquisitionError` (after recording it) so the DBOS step
    retries; returns the target's outcome otherwise."""
    with run_transaction(rt.engine, run_id) as tx:
        run = run_store.run(tx, run_id, lock=True)
        target = next((t for t in store.targets(tx, run_id) if t.position == position), None)
        if run is None or target is None:
            return {"status": AttemptStatus.FAILED.value}
        if run.status is WorkState.CANCELLED or run.cancel_requested_at is not None:
            store.set_target_status(tx, run_id, position, "cancelled")
            return {"status": "cancelled"}
        if run.status not in (WorkState.QUEUED, WorkState.RUNNING):
            return {"status": target.status}
        previous = store.last_attempt(tx, run_id, position)
        finished_for_good = (
            target.status == "failed"
            and previous is not None
            and not (previous.transient or previous.status is AttemptStatus.PENDING)
        )
        if target.status in ("succeeded", "blocked") or finished_for_good:
            return {"status": target.status}  # recorded by an earlier execution of this step
        if run_store.mark_running(tx, run_id):
            identity_store.append_event(
                tx,
                run.workspace_id,
                EventKind.RUN_STATE_CHANGED,
                str(run_id),
                state=WorkState.RUNNING,
            )
        if run_store.authorised_workspace(tx) != run.workspace_id:
            store.set_target_status(tx, run_id, position, AttemptStatus.FAILED.value)
            return {
                "status": AttemptStatus.FAILED.value,
                "reason": FailureClass.ACCESS_REVOKED.value,
            }
        if store.settle_pending_attempts(tx, run_id, position):
            previous = store.last_attempt(tx, run_id, position)
        attempt_id = uuid.uuid4()
        store.insert_attempt(
            tx,
            attempt_id=attempt_id,
            workspace_id=run.workspace_id,
            run_id=run_id,
            position=position,
            retry_of=previous.attempt_id if previous else None,
            route=target.route,
            provider=_provider(target),
            requested_url=_target_url(target),
        )
    try:
        if target.route is InputRoute.ADZUNA and target.query is not None:
            result = rt.client.adzuna(AdzunaQuery.model_validate(target.query))
        elif target.url is not None:
            result = rt.client.fetch(target.url, read_text=target.role_title is not None)
        else:  # refused when submitted: recorded as blocked, nothing is asked for
            result = AcquisitionResult(
                route=InputRoute.FETCH,
                provider=_provider(target),
                requested_url=None,
                status=AttemptStatus.BLOCKED,
                reason=target.refusal.value if target.refusal else None,  # CHECK: never None
                fetched_at=rt.clock(),
            )
    except AcquisitionUnavailableError:
        result = _unavailable(target, rt.clock())
    result = _kept_body_checked(result)
    role_title = target.role_title  # a page read for role research: no posting, no model
    with run_transaction(rt.engine, run_id) as tx:
        if model_readable(result) and role_title is None:
            # First, before any other lock or insert: the page may start an extraction run,
            # which a cancel must see or be seen by. The cancel takes this lock and then the
            # workspace's row, which a kept body's document would already hold by its key
            # here, so taking it any later could deadlock (review C-1 N1).
            run_store.lock_started_runs(tx, run_id)
        # One recording at a time per workspace, from reading the candidates to the merge,
        # so a merge never deletes a job another run is recording onto (review B N2).
        store.lock_workspace_records(tx, run.workspace_id)
        if run_store.authorised_workspace(tx) != run.workspace_id:
            # Nothing it found is recorded; its attempt is settled, never left pending.
            store.settle_revoked_attempt(tx, attempt_id)
            store.set_target_status(tx, run_id, position, AttemptStatus.FAILED.value)
            return {
                "status": AttemptStatus.FAILED.value,
                "reason": FailureClass.ACCESS_REVOKED.value,
            }
        store.finish_attempt(tx, attempt_id, result, http_requests=result.http_requests)
        if result.status is AttemptStatus.SUCCEEDED and role_title is not None:
            _record_role_page(tx, rt, run, attempt_id, result, role_title)
        elif result.status is AttemptStatus.SUCCEEDED:
            _record_copies(tx, rt, run, attempt_id, result)
            # A page whose structured data gave no posting goes to the workspace's own model
            # extraction run, or says why not (fix round 2, rulings 9-10).
            start_extraction(tx, rt.keyring, rt.models, run, attempt_id, result, rt.clock())
        elif target.url and result.requested_url and role_title is None:
            store.job_attempted(
                tx,
                store.jobs_from_url(tx, run.workspace_id, result.requested_url),
                result.fetched_at,
                closed=result.http_status == 410,
            )
        store.set_target_status(tx, run_id, position, result.status.value)
        identity_store.append_event(
            tx,
            run.workspace_id,
            EventKind.RESEARCH_UPDATED,
            str(run_id),
            detail={"position": position},
        )
    if result.transient:
        raise TransientAcquisitionError(result.reason or "transient")
    return {"status": result.status.value, "attempt_id": str(attempt_id)}


class AcquisitionSummary(StrictModel):
    """A complete acquisition run's output: each target's outcome. The records themselves
    are the attempts, copies and claims. A source retrieved with no posting that could be
    read is counted apart from one that was read (`succeeded`), never as "none found"; one
    handed to a model extraction run is counted apart again, since that run says how it
    went (each attempt's `model_extraction`)."""

    targets: list[dict[str, str | int]]
    succeeded: int
    no_posting_readable: int = 0  # absent from summaries written before fix round 1
    model_extractions: int = 0  # absent from summaries written before fix round 2
    blocked: int
    failed: int


def publish_acquisition(rt: AcquisitionRuntime, run_id: uuid.UUID) -> None:
    """The run's terminal state from its targets: complete when at least one source was
    retrieved (the output says which did not, and which could not be read), otherwise
    failed: `access_revoked` when the requester lost access, `source_blocked` when every
    source was refused by policy and `retrieval_failed` otherwise. Never an empty success."""
    with run_transaction(rt.engine, run_id) as tx:
        run = run_store.run(tx, run_id, lock=True)
        if run is None:
            return
        if run.status is WorkState.CANCELLED or run.cancel_requested_at is not None:
            outcome: Outcome = cancelled()
        elif run_store.authorised_workspace(tx) != run.workspace_id:
            outcome = failed(FailureClass.ACCESS_REVOKED)
        else:
            rows = store.targets(tx, run_id)
            statuses = [t.status for t in rows]
            last = {a.position: a for a in store.attempts_of_run(tx, run_id)}
            unread = [
                last[t.position].attempt_id
                for t in rows
                if t.status == "succeeded" and last[t.position].unreadable
            ]
            started = store.extractions_of_attempts(tx, unread)
            handed = sum(1 for e in started.values() if e.run_id is not None)
            if "succeeded" in statuses:
                summary = AcquisitionSummary(
                    targets=[{"position": t.position, "status": t.status} for t in rows],
                    succeeded=statuses.count("succeeded") - len(unread),
                    no_posting_readable=len(unread) - handed,
                    model_extractions=handed,
                    blocked=statuses.count("blocked"),
                    failed=len(statuses) - statuses.count("succeeded") - statuses.count("blocked"),
                )
                body = summary.model_dump_json().encode()
                output_id = uuid.uuid4()
                accepted, _ = run_store.insert_output(
                    tx,
                    output_id=output_id,
                    run=run,
                    sealed=rt.keyring.seal(body, output_context(run.workspace_id, output_id)),
                    content_sha256=hashlib.sha256(body).hexdigest(),
                )
                outcome = succeeded(accepted)
            elif statuses and all(s == "blocked" for s in statuses):
                outcome = failed(FailureClass.SOURCE_BLOCKED)
            else:
                outcome = failed(FailureClass.RETRIEVAL_FAILED)
    publish(rt.activity, run_id, outcome)


def summary_of(tx: Tx, keyring: Keyring, run: Run) -> AcquisitionSummary | None:
    """A complete run's summary only: a cancelled or failed run's output is never used."""
    if run.status is not WorkState.COMPLETE:
        return None
    raw = open_output(tx, keyring, run)
    return None if raw is None else AcquisitionSummary.model_validate(json.loads(raw))
