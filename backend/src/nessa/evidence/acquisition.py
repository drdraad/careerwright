"""Acquisition runs, pasted text, jobs and favourites (spec sections 6, 7 and 11; ADR 0009).

API side: an acquisition run is submitted with up to ten URLs or one Adzuna search (live-
vacancy workspaces only). A URL already being fetched in this workspace is joined, not
fetched again, and one that failed recently waits out its back-off (FRESH-04). Pasted text
is a separate input route: recorded at once, never fetched, kept as the person's own
example of a target (at most three per target, JOB-06) and never a live vacancy.

Worker side, one DBOS step per target (`nessa.evidence.workflow`): the attempt is recorded
before the request, the restricted acquisition worker is asked for the source, and the
result is recorded in one transaction: the attempt, the body where the rights class permits
keeping it (sealed), each job copy with its claims, attached to a canonical job by
`jobs.same_job`. A failed or blocked source is an attempt with its reason, never "no
vacancies"; a failed refresh moves a job's last attempt and never its last success. A
cancelled run fetches nothing more.
"""

import base64
import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any
from urllib.parse import urlsplit

from pydantic import Field, StringConstraints, model_validator

from nessa.config import RuntimeMode
from nessa.db import Engine, Tx, run_transaction
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.evidence import store
from nessa.evidence.acquire import ADZUNA_PROVIDER, AcquisitionResult
from nessa.evidence.addresses import CheckedUrl, UrlRefusal, check_url
from nessa.evidence.adzuna import CREDENTIAL_PARAMETERS, AdzunaQuery, recorded_url
from nessa.evidence.freshness import (
    FreshnessKind,
    FreshnessView,
    RefreshDecision,
    SourceTimes,
    freshness,
    refresh_decision,
)
from nessa.evidence.jobs import (
    canonical_facts,
    description_fingerprints,
    facts_from_json,
    facts_json,
    same_job,
    title_key,
)
from nessa.evidence.records import (
    AdvertiserKind,
    AttemptStatus,
    Claim,
    ClaimField,
    DescriptionKind,
    InputRoute,
    JobCopy,
    Location,
    Retention,
    SourceSpan,
    StrictModel,
    ValidationState,
)
from nessa.evidence.service_client import AcquisitionClient, AcquisitionUnavailableError
from nessa.identity import run_store
from nessa.identity import store as identity_store
from nessa.identity.access import Actor
from nessa.identity.activity import ActivityRuntime, Outcome, cancelled, failed, publish, succeeded
from nessa.identity.failures import FailureClass
from nessa.identity.keyring import Keyring, RecordContext
from nessa.identity.records import EventKind, Run, RunKind
from nessa.identity.runs import open_output, output_context, submit_keyless_run, visible_run
from nessa.identity.workspaces import visible_workspace
from nessa.vocabulary import DataMode, WorkState

MAX_URLS = 10
MAX_EXEMPLARS_PER_TARGET = 3
MAX_PASTED_CHARS = 50_000
DOCUMENT_KIND = "source_document"
PASTED_PROVIDER = "pasted_text"
PASTED_RIGHTS = "pasted by the person: their own input, kept privately in this workspace"

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


@dataclass(frozen=True)
class Skipped:
    url: str
    reason: str  # "in_flight" or "backing_off"
    run_id: uuid.UUID | None = None
    retry_at: datetime | None = None


@dataclass(frozen=True)
class SubmittedAcquisition:
    run: Run | None  # None when every URL was joined or is backing off
    skipped: list[Skipped] = field(default_factory=list)


def _refused(reason: str) -> NessaError:
    return NessaError(
        ErrorCode.VALIDATION_FAILED,
        "That address can't be recorded safely. Remove any user name, password or key from "
        "it, then try again.",
        stage=ErrorStage.REQUEST,
        details={"field": "urls", "reason": reason},
    )


def _recordable(url: str) -> str:
    """The URL as it will be recorded. One that cannot be recorded safely (a credential in
    it, malformed, too long) is refused now; any other refusal is the worker's to record as
    a blocked attempt, so a policy denial is always on record (ACQ-06)."""
    checked = check_url(url)
    if checked in (UrlRefusal.MALFORMED, UrlRefusal.URL_TOO_LONG, UrlRefusal.CREDENTIALS_IN_URL):
        raise _refused(str(checked))
    lowered = url.lower()
    if any(f"{name}=" in lowered for name in CREDENTIAL_PARAMETERS):
        raise _refused(UrlRefusal.CREDENTIALS_IN_URL.value)
    return checked.url if isinstance(checked, CheckedUrl) else url


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
        raise NessaError(
            ErrorCode.MODE_NOT_SUPPORTED,
            "Adzuna searches run only in a live-vacancy workspace.",
            stage=ErrorStage.EXECUTION,
        )
    urls = list(dict.fromkeys(_recordable(url) for url in command.urls))
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
            skipped.append(Skipped(url, "in_flight", run_id=in_flight[url]))
        elif decision.action is RefreshDecision.Action.BACK_OFF:
            skipped.append(Skipped(url, "backing_off", retry_at=decision.retry_at))
        else:
            started.append(url)
    if not started and command.adzuna is None:
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
    for position, url in enumerate(started):
        store.insert_target(
            tx,
            run_id=run.run_id,
            workspace_id=workspace_id,
            position=position,
            route=InputRoute.FETCH,
            url=url,
            query=None,
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
        raise NessaError(
            ErrorCode.VALIDATION_FAILED,
            "Name the target role this example is for.",
            stage=ErrorStage.REQUEST,
            details={"field": "target", "reason": "no_words"},
        )
    if store.exemplar_count(tx, workspace_id, target) >= MAX_EXEMPLARS_PER_TARGET:
        raise NessaError(
            ErrorCode.LIMIT_EXCEEDED,
            "You already have three examples for this target. Remove one to add another.",
            stage=ErrorStage.REQUEST,
            details={"reason": "exemplars_per_target", "limit": MAX_EXEMPLARS_PER_TARGET},
        )
    source_url = _recordable(command.source_url) if command.source_url else None
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


@dataclass(frozen=True)
class TargetView:
    target: store.TargetRow
    status: str  # as stored, or `cancelled` / `not_attempted` for a queued target of an ended run
    attempts: list[store.AttemptRow]


@dataclass(frozen=True)
class AcquisitionView:
    run: Run
    targets: list[TargetView]
    job_ids: list[uuid.UUID]


def acquisition(tx: Tx, workspace_id: uuid.UUID, run_id: uuid.UUID) -> AcquisitionView:
    run = visible_run(tx, workspace_id, run_id)
    if run.kind is not RunKind.ACQUISITION:
        raise NessaError(ErrorCode.NOT_FOUND, "No such acquisition.", stage=ErrorStage.EXECUTION)
    attempts = store.attempts_of_run(tx, run_id)
    views = []
    for target in store.targets(tx, run_id):
        status = target.status
        if status == "queued" and run.status is WorkState.CANCELLED:
            status = "cancelled"
        elif status == "queued" and run.status in (WorkState.COMPLETE, WorkState.FAILED):
            status = "not_attempted"
        views.append(
            TargetView(target, status, [a for a in attempts if a.position == target.position])
        )
    copies = store.copies_of_attempts(tx, [a.attempt_id for a in attempts])
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


def _view(tx: Tx, job: store.JobRow, copies: list[store.CopyRow], now: datetime) -> JobView:
    primary = _primary(copies)
    times = SourceTimes(
        last_attempt_at=job.last_attempt_at,
        last_success_at=job.last_success_at,
        published_at=None,
        valid_from=None,
        valid_until=primary.valid_through,
    )
    attempts = {}
    for c in copies:
        found = store.attempt(tx, c.attempt_id)
        if found is not None:
            attempts[c.attempt_id] = found
    return JobView(
        job,
        copies,
        primary,
        freshness(FreshnessKind.JOB, times, closed=job.closed_at is not None, now=now),
        attempts,
    )


@dataclass(frozen=True)
class JobListing:
    jobs: list[JobView]
    more: bool
    total_jobs: int
    city_counts: dict[str, int]
    coverage: dict[str, int]
    empty_reason: str | None  # STATE-02: why there is nothing, never a bare empty list


def list_jobs(
    tx: Tx,
    workspace_id: uuid.UUID,
    *,
    favourites_only: bool,
    before: tuple[datetime, uuid.UUID] | None,
    limit: int,
    now: datetime,
) -> JobListing:
    visible_workspace(tx, workspace_id)
    rows = store.jobs(
        tx, workspace_id, favourites_only=favourites_only, before=before, limit=limit + 1
    )
    page, more = rows[:limit], len(rows) > limit
    copies = store.copies_of_jobs(tx, [j.job_id for j in page])
    views = [_view(tx, j, [c for c in copies if c.job_id == j.job_id], now) for j in page]
    everything = store.jobs(tx, workspace_id, favourites_only=False, before=None, limit=10_000)
    all_copies = store.copies_of_jobs(tx, [j.job_id for j in everything])
    cities: dict[str, set[uuid.UUID]] = {}
    for c in all_copies:
        for location in c.copy.locations:
            label = location.locality or location.label
            if c.job_id is not None:
                cities.setdefault(label, set()).add(c.job_id)
    covered = store.coverage(tx, workspace_id)
    empty_reason = None
    if not everything:
        if not covered:
            empty_reason = "no_sources_checked"
        elif not covered.get(AttemptStatus.SUCCEEDED.value):
            empty_reason = "no_source_retrieved"
        else:
            empty_reason = "none_found_in_sources_checked"
    return JobListing(
        views,
        more,
        len(everything),
        {city: len(ids) for city, ids in sorted(cities.items())},
        covered,
        empty_reason,
    )


def job_detail(
    tx: Tx, workspace_id: uuid.UUID, job_id: uuid.UUID, *, now: datetime
) -> tuple[JobView, list[store.ClaimRow]]:
    visible_workspace(tx, workspace_id)
    job = store.job(tx, workspace_id, job_id)
    if job is None:
        raise NessaError(ErrorCode.NOT_FOUND, "No such job.", stage=ErrorStage.EXECUTION)
    copies = store.copies_of_jobs(tx, [job_id])
    return _view(tx, job, copies, now), store.claims_of_copies(tx, [c.copy_id for c in copies])


def set_favourite(
    tx: Tx, actor: Actor, workspace_id: uuid.UUID, job_id: uuid.UUID, *, favourite: bool
) -> None:
    visible_workspace(tx, workspace_id, lock=True)
    if store.job(tx, workspace_id, job_id) is None:
        raise NessaError(ErrorCode.NOT_FOUND, "No such job.", stage=ErrorStage.EXECUTION)
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


def _target_url(target: store.TargetRow) -> str:
    if target.route is InputRoute.ADZUNA and target.query is not None:
        return recorded_url(AdzunaQuery.model_validate(target.query))
    return target.url or ""


def _provider(target: store.TargetRow) -> str:
    """The host a target names (lower-case), before any check: the attempt records even a
    refused URL against its host."""
    if target.route is InputRoute.ADZUNA:
        return ADZUNA_PROVIDER
    try:
        host = urlsplit(target.url or "").hostname
    except ValueError:
        host = None
    return host or "unknown"


def _record_copies(
    tx: Tx, rt: AcquisitionRuntime, run: Run, attempt_id: uuid.UUID, result: AcquisitionResult
) -> None:
    now = result.fetched_at
    if result.body_b64 is not None and result.retention is Retention.BODY:
        body = base64.b64decode(result.body_b64)
        if hashlib.sha256(body).hexdigest() == result.content_sha256:
            store.insert_document(
                tx,
                attempt_id=attempt_id,
                workspace_id=run.workspace_id,
                sha256=result.content_sha256,
                sealed=rt.keyring.seal(body, document_context(run.workspace_id, attempt_id)),
            )
    for copy in result.copies:
        facts = canonical_facts(copy, provider=result.provider)
        job_id: uuid.UUID | None = None
        if copy.extraction_error is None:
            for candidate, stored in store.candidate_copies(
                tx,
                run.workspace_id,
                provider=result.provider,
                source_job_id=copy.source_job_id,
                title_key=facts.title_key,
            ):
                if same_job(facts, facts_from_json(stored)):
                    job_id = candidate
                    break
            if job_id is None:
                job_id = uuid.uuid4()
                store.insert_job(
                    tx, job_id=job_id, workspace_id=run.workspace_id, exemplar=False, at=now
                )
            else:
                store.job_verified(tx, job_id, now)
        copy_id = uuid.uuid4()
        store.insert_copy(
            tx,
            copy_id=copy_id,
            workspace_id=run.workspace_id,
            job_id=job_id,
            attempt_id=attempt_id,
            provider=result.provider,
            copy=copy,
            facts=facts_json(facts),
        )
        store.insert_claims(
            tx,
            workspace_id=run.workspace_id,
            attempt_id=attempt_id,
            copy_id=copy_id,
            copy=copy,
            retrieved_at=now,
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
        if target.status in ("succeeded", "blocked"):
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
        store.settle_pending_attempts(tx, run_id, position)
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
        else:
            result = rt.client.fetch(target.url or "")
    except AcquisitionUnavailableError:
        result = _unavailable(target, rt.clock())
    with run_transaction(rt.engine, run_id) as tx:
        if run_store.authorised_workspace(tx) != run.workspace_id:
            store.set_target_status(tx, run_id, position, AttemptStatus.FAILED.value)
            return {
                "status": AttemptStatus.FAILED.value,
                "reason": FailureClass.ACCESS_REVOKED.value,
            }
        store.finish_attempt(tx, attempt_id, result, http_requests=result.http_requests)
        if result.status is AttemptStatus.SUCCEEDED:
            _record_copies(tx, rt, run, attempt_id, result)
        elif target.url and result.requested_url:
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
    are the attempts, copies and claims."""

    targets: list[dict[str, str | int]]
    succeeded: int
    blocked: int
    failed: int


def publish_acquisition(rt: AcquisitionRuntime, run_id: uuid.UUID) -> None:
    """The run's terminal state from its targets: complete when at least one source was
    retrieved (the output says which did not), otherwise failed, `source_blocked` when every
    source was refused by policy and `retrieval_failed` otherwise. Never an empty success."""
    with run_transaction(rt.engine, run_id) as tx:
        run = run_store.run(tx, run_id, lock=True)
        if run is None:
            return
        if run.status is WorkState.CANCELLED or run.cancel_requested_at is not None:
            outcome: Outcome = cancelled()
        else:
            rows = store.targets(tx, run_id)
            statuses = [t.status for t in rows]
            if "succeeded" in statuses:
                summary = AcquisitionSummary(
                    targets=[{"position": t.position, "status": t.status} for t in rows],
                    succeeded=statuses.count("succeeded"),
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
    raw = open_output(tx, keyring, run)
    return None if raw is None else AcquisitionSummary.model_validate(json.loads(raw))
