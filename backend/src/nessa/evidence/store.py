"""SQL for acquisition targets, source attempts, sealed source documents, jobs, their source
copies, claims and favourites (adapter).

The API runs these inside `actor_transaction` and the worker inside `run_transaction`;
row-level security limits each to its workspace, and the worker to the run it executes
while the run's requester may act (migration 0013).
"""

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import sqlalchemy as sa

from nessa.db import Tx
from nessa.evidence.acquire import AcquisitionResult
from nessa.evidence.addresses import UrlRefusal
from nessa.evidence.records import AttemptStatus, Claim, InputRoute, JobCopy
from nessa.identity.keyring import SealedValue

_ATTEMPT_COLUMNS = (
    "attempt_id, run_id, position, retry_of, route, provider, requested_url, final_url, "
    "redirects, status, reason, transient, http_status, content_type, address, "
    "content_sha256, byte_count, rights_class, rights_status, retention, http_requests, "
    "cost_nano_usd, created_by, started_at, finished_at"
)


@dataclass(frozen=True)
class TargetRow:
    run_id: uuid.UUID
    position: int
    route: InputRoute
    url: str | None  # a checked URL; None for a query or a refused URL
    query: dict[str, Any] | None
    status: str
    refusal: UrlRefusal | None = None  # why a submitted URL was refused
    refused_host: str | None = None  # its host as plain text, never a link


@dataclass(frozen=True)
class AttemptRow:
    attempt_id: uuid.UUID
    run_id: uuid.UUID | None
    position: int | None
    retry_of: uuid.UUID | None
    route: InputRoute
    provider: str
    requested_url: str | None
    final_url: str | None
    redirects: list[str]
    status: AttemptStatus
    reason: str | None
    transient: bool
    http_status: int | None
    content_type: str | None
    address: str | None
    content_sha256: str | None
    byte_count: int | None
    rights_class: str | None
    rights_status: str | None
    retention: str | None
    http_requests: int
    cost_nano_usd: int | None
    created_by: uuid.UUID | None
    started_at: datetime
    finished_at: datetime | None


@dataclass(frozen=True)
class CopyRow:
    copy_id: uuid.UUID
    job_id: uuid.UUID | None
    attempt_id: uuid.UUID
    provider: str
    copy: JobCopy  # its claims are read separately
    extraction_error: str | None
    created_at: datetime


@dataclass(frozen=True)
class JobRow:
    job_id: uuid.UUID
    exemplar: bool
    first_seen_at: datetime
    last_success_at: datetime | None
    last_attempt_at: datetime
    closed_at: datetime | None
    favourite: bool


@dataclass(frozen=True)
class ClaimRow:
    claim_id: int
    attempt_id: uuid.UUID
    copy_id: uuid.UUID
    claim: Claim
    retrieved_at: datetime
    published_on: date | None
    valid_until: datetime | None


def _attempt(row: sa.RowMapping) -> AttemptRow:
    values = dict(row)
    values["route"] = InputRoute(values["route"])
    values["status"] = AttemptStatus(values["status"])
    return AttemptRow(**values)


# --- targets ----------------------------------------------------------------------------


def insert_target(
    tx: Tx,
    *,
    run_id: uuid.UUID,
    workspace_id: uuid.UUID,
    position: int,
    route: InputRoute,
    url: str | None,
    query: dict[str, Any] | None,
    refusal: UrlRefusal | None = None,
    refused_host: str | None = None,
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO nessa.acquisition_targets (run_id, workspace_id, position, route, url, "
            "query, refusal, refused_host) VALUES (:run, :ws, :position, :route, :url, "
            "CAST(:query AS jsonb), :refusal, :refused_host)"
        ),
        {
            "run": run_id,
            "ws": workspace_id,
            "position": position,
            "route": route.value,
            "url": url,
            "query": None if query is None else json.dumps(query),
            "refusal": refusal.value if refusal else None,
            "refused_host": refused_host,
        },
    )


def targets(tx: Tx, run_id: uuid.UUID) -> list[TargetRow]:
    rows = tx.execute(
        sa.text(
            "SELECT run_id, position, route, url, query, status, refusal, refused_host "
            "FROM nessa.acquisition_targets WHERE run_id = :run ORDER BY position"
        ),
        {"run": run_id},
    ).mappings()
    return [
        TargetRow(
            r["run_id"],
            r["position"],
            InputRoute(r["route"]),
            r["url"],
            r["query"],
            r["status"],
            UrlRefusal(r["refusal"]) if r["refusal"] else None,
            r["refused_host"],
        )
        for r in rows
    ]


def set_target_status(tx: Tx, run_id: uuid.UUID, position: int, status: str) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.acquisition_targets SET status = :status "
            "WHERE run_id = :run AND position = :position"
        ),
        {"run": run_id, "position": position, "status": status},
    )


def urls_in_flight(tx: Tx, workspace_id: uuid.UUID, urls: list[str]) -> dict[str, uuid.UUID]:
    """URL -> the queued or running acquisition run already working on it."""
    if not urls:
        return {}
    rows = tx.execute(
        sa.text(
            "SELECT DISTINCT ON (t.url) t.url, t.run_id FROM nessa.acquisition_targets t "
            "JOIN nessa.runs r ON r.run_id = t.run_id "
            "WHERE t.workspace_id = :ws AND t.url = ANY(:urls) AND t.status = 'queued' "
            "AND r.status IN ('queued', 'running') "
            "AND NOT EXISTS (SELECT 1 FROM nessa.run_cancellations c WHERE c.run_id = r.run_id) "
            "ORDER BY t.url, r.created_at"
        ),
        {"ws": workspace_id, "urls": urls},
    )
    return {r.url: r.run_id for r in rows}


def url_history(tx: Tx, workspace_id: uuid.UUID, url: str) -> tuple[int, datetime | None]:
    """(consecutive failures since the last success, the last attempt's start) for a URL."""
    rows = tx.execute(
        sa.text(
            "SELECT status, started_at FROM nessa.source_attempts "
            "WHERE workspace_id = :ws AND requested_url = :url AND status <> 'pending' "
            "ORDER BY started_at DESC LIMIT 20"
        ),
        {"ws": workspace_id, "url": url},
    ).all()
    failures = 0
    for row in rows:
        if row.status == AttemptStatus.SUCCEEDED.value:
            break
        failures += 1
    return failures, (rows[0].started_at if rows else None)


# --- attempts ---------------------------------------------------------------------------


def insert_attempt(
    tx: Tx,
    *,
    attempt_id: uuid.UUID,
    workspace_id: uuid.UUID,
    run_id: uuid.UUID | None,
    position: int | None,
    retry_of: uuid.UUID | None,
    route: InputRoute,
    provider: str,
    requested_url: str | None,
    created_by: uuid.UUID | None = None,
) -> None:
    """Recorded before the request, so a crash leaves a pending attempt to settle."""
    tx.execute(
        sa.text(
            "INSERT INTO nessa.source_attempts (attempt_id, workspace_id, run_id, position, "
            "retry_of, route, provider, requested_url, status, created_by) VALUES (:id, :ws, "
            ":run, :position, :retry_of, :route, :provider, :url, 'pending', :by)"
        ),
        {
            "id": attempt_id,
            "ws": workspace_id,
            "run": run_id,
            "position": position,
            "retry_of": retry_of,
            "route": route.value,
            "provider": provider[:253],
            "url": requested_url,
            "by": created_by,
        },
    )


def insert_pasted_attempt(
    tx: Tx,
    *,
    attempt_id: uuid.UUID,
    workspace_id: uuid.UUID,
    created_by: uuid.UUID,
    requested_url: str | None,
    sha256: str,
    byte_count: int,
    rights_status: str,
) -> None:
    """API: pasted text is complete when it arrives, so its attempt is recorded finished in
    one statement (the API may insert attempts, never change them)."""
    tx.execute(
        sa.text(
            "INSERT INTO nessa.source_attempts (attempt_id, workspace_id, route, provider, "
            "requested_url, status, content_type, content_sha256, byte_count, rights_status, "
            "retention, created_by, finished_at) VALUES (:id, :ws, 'pasted_text', "
            "'pasted_text', :url, 'succeeded', 'text/plain', :sha, :bytes, :rights, 'body', "
            ":by, clock_timestamp())"
        ),
        {
            "id": attempt_id,
            "ws": workspace_id,
            "url": requested_url,
            "sha": sha256,
            "bytes": byte_count,
            "rights": rights_status,
            "by": created_by,
        },
    )


def finish_attempt(
    tx: Tx, attempt_id: uuid.UUID, result: AcquisitionResult, *, http_requests: int
) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.source_attempts SET final_url = :final, redirects = CAST(:redirects AS "
            "jsonb), status = :status, reason = :reason, transient = :transient, http_status = "
            ":http, content_type = :ctype, address = :address, content_sha256 = :sha, "
            "retrieved_sha256 = :retrieved, "
            "byte_count = :bytes, rights_class = :class, rights_status = :rights, retention = "
            ":retention, http_requests = :requests, cost_nano_usd = 0, "
            "finished_at = clock_timestamp() WHERE attempt_id = :id"
        ),
        {
            "id": attempt_id,
            "final": result.final_url,
            "redirects": json.dumps(result.redirects),
            "status": result.status.value,
            "reason": result.reason,
            "transient": result.transient,
            "http": result.http_status,
            "ctype": (result.content_type or None) and result.content_type[:120],
            "address": result.address,
            "sha": result.content_sha256,
            "retrieved": result.retrieved_sha256,
            "bytes": result.byte_count,
            "class": result.rights_class.value if result.rights_class else None,
            "rights": result.rights_status,
            "retention": result.retention.value if result.retention else None,
            "requests": http_requests,
        },
    )


def settle_pending_attempts(tx: Tx, run_id: uuid.UUID, position: int) -> int:
    """A re-executed step finds an attempt its predecessor never finished (a crash during
    the request): it failed, as far as anyone can tell."""
    updated = tx.execute(
        sa.text(
            "UPDATE nessa.source_attempts SET status = 'failed', reason = 'interrupted', "
            "transient = true, finished_at = clock_timestamp() "
            "WHERE run_id = :run AND position = :position AND status = 'pending'"
        ),
        {"run": run_id, "position": position},
    )
    return int(updated.rowcount)


def last_attempt(tx: Tx, run_id: uuid.UUID, position: int) -> AttemptRow | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_ATTEMPT_COLUMNS} FROM nessa.source_attempts "
                "WHERE run_id = :run AND position = :position ORDER BY started_at DESC LIMIT 1"
            ),
            {"run": run_id, "position": position},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _attempt(row)


def attempts_of_run(tx: Tx, run_id: uuid.UUID) -> list[AttemptRow]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_ATTEMPT_COLUMNS} FROM nessa.source_attempts WHERE run_id = :run "
            "ORDER BY position, started_at"
        ),
        {"run": run_id},
    ).mappings()
    return [_attempt(r) for r in rows]


def attempt(tx: Tx, attempt_id: uuid.UUID) -> AttemptRow | None:
    row = (
        tx.execute(
            sa.text(f"SELECT {_ATTEMPT_COLUMNS} FROM nessa.source_attempts WHERE attempt_id = :id"),
            {"id": attempt_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _attempt(row)


def coverage(tx: Tx, workspace_id: uuid.UUID) -> dict[str, int]:
    """Latest attempt status per source the workspace tried (spec section 7: "Display
    result count, deduplication count and coverage status")."""
    rows = tx.execute(
        sa.text(
            "SELECT status, count(*) AS n FROM (SELECT DISTINCT ON (coalesce(requested_url, "
            "attempt_id::text)) status FROM nessa.source_attempts WHERE workspace_id = :ws "
            "ORDER BY coalesce(requested_url, attempt_id::text), started_at DESC) latest "
            "GROUP BY status"
        ),
        {"ws": workspace_id},
    )
    return {r.status: int(r.n) for r in rows}


# --- documents --------------------------------------------------------------------------


def insert_document(
    tx: Tx, *, attempt_id: uuid.UUID, workspace_id: uuid.UUID, sha256: str, sealed: SealedValue
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO nessa.source_documents (attempt_id, workspace_id, content_sha256, "
            "key_version, nonce, ciphertext) VALUES (:id, :ws, :sha, :version, :nonce, "
            ":ciphertext)"
        ),
        {
            "id": attempt_id,
            "ws": workspace_id,
            "sha": sha256,
            "version": sealed.key_version,
            "nonce": sealed.nonce,
            "ciphertext": sealed.ciphertext,
        },
    )


def document_kept(tx: Tx, attempt_id: uuid.UUID) -> bool:
    return (
        tx.execute(
            sa.text("SELECT 1 FROM nessa.source_documents WHERE attempt_id = :id"),
            {"id": attempt_id},
        ).first()
        is not None
    )


def all_sealed_documents(tx: Tx) -> list[tuple[uuid.UUID, uuid.UUID, SealedValue]]:
    """Setup only (master-key rotation): every sealed source document, locked."""
    rows = tx.execute(
        sa.text(
            "SELECT attempt_id, workspace_id, key_version, nonce, ciphertext "
            "FROM nessa.source_documents ORDER BY attempt_id FOR UPDATE"
        )
    )
    return [
        (
            r.attempt_id,
            r.workspace_id,
            SealedValue(r.key_version, bytes(r.nonce), bytes(r.ciphertext)),
        )
        for r in rows
    ]


def replace_sealed_document(tx: Tx, attempt_id: uuid.UUID, sealed: SealedValue) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.source_documents SET key_version = :version, nonce = :nonce, "
            "ciphertext = :ciphertext WHERE attempt_id = :id"
        ),
        {
            "id": attempt_id,
            "version": sealed.key_version,
            "nonce": sealed.nonce,
            "ciphertext": sealed.ciphertext,
        },
    )


# --- jobs, copies and claims ------------------------------------------------------------


def candidate_copies(
    tx: Tx, workspace_id: uuid.UUID, *, provider: str, source_job_id: str | None, title_key: str
) -> list[tuple[uuid.UUID, dict[str, Any]]]:
    """(job, facts) of published copies that could be the same vacancy: the same source ID
    from the same provider, or the same title key (`jobs.same_job` decides). Exemplars are
    never candidates. Oldest job first."""
    rows = tx.execute(
        sa.text(
            "SELECT c.job_id, c.facts FROM nessa.job_copies c JOIN nessa.jobs j "
            "ON j.job_id = c.job_id WHERE c.workspace_id = :ws AND NOT j.exemplar AND "
            "((c.provider = :provider AND c.source_job_id = :source_id) "
            "OR c.facts ->> 'title_key' = :title) ORDER BY j.first_seen_at, c.created_at"
        ),
        {"ws": workspace_id, "provider": provider, "source_id": source_job_id, "title": title_key},
    )
    return [(r.job_id, r.facts) for r in rows]


def insert_job(
    tx: Tx, *, job_id: uuid.UUID, workspace_id: uuid.UUID, exemplar: bool, at: datetime
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO nessa.jobs (job_id, workspace_id, exemplar, first_seen_at, "
            "last_success_at, last_attempt_at) VALUES (:id, :ws, :exemplar, :at, :success, :at)"
        ),
        {
            "id": job_id,
            "ws": workspace_id,
            "exemplar": exemplar,
            "at": at,
            "success": None if exemplar else at,
        },
    )


def job_verified(tx: Tx, job_id: uuid.UUID, at: datetime) -> None:
    """A successful retrieval: freshness starts again from `at`, and a reopened advert is
    no longer closed."""
    tx.execute(
        sa.text(
            "UPDATE nessa.jobs SET last_success_at = greatest(last_success_at, :at), "
            "last_attempt_at = greatest(last_attempt_at, :at), closed_at = NULL "
            "WHERE job_id = :id AND NOT exemplar"
        ),
        {"id": job_id, "at": at},
    )


def jobs_from_url(tx: Tx, workspace_id: uuid.UUID, url: str) -> list[uuid.UUID]:
    rows = tx.execute(
        sa.text(
            "SELECT DISTINCT c.job_id FROM nessa.job_copies c JOIN nessa.source_attempts a "
            "ON a.attempt_id = c.attempt_id WHERE c.workspace_id = :ws AND a.requested_url = :url "
            "AND c.job_id IS NOT NULL"
        ),
        {"ws": workspace_id, "url": url},
    )
    return [r.job_id for r in rows]


def job_attempted(tx: Tx, job_ids: list[uuid.UUID], at: datetime, *, closed: bool) -> None:
    """A failed refresh: the attempt time moves, the last success never does (FRESH-03). A
    source that says the advert is gone (HTTP 410) closes it."""
    if not job_ids:
        return
    tx.execute(
        sa.text(
            "UPDATE nessa.jobs SET last_attempt_at = greatest(last_attempt_at, :at), "
            "closed_at = CASE WHEN :closed THEN coalesce(closed_at, :at) ELSE closed_at END "
            "WHERE job_id = ANY(:ids)"
        ),
        {"ids": job_ids, "at": at, "closed": closed},
    )


def insert_copy(
    tx: Tx,
    *,
    copy_id: uuid.UUID,
    workspace_id: uuid.UUID,
    job_id: uuid.UUID | None,
    attempt_id: uuid.UUID,
    provider: str,
    copy: JobCopy,
    facts: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> None:
    body = json.loads(copy.model_dump_json(exclude={"claims"}))
    body.update(extra or {})
    tx.execute(
        sa.text(
            "INSERT INTO nessa.job_copies (copy_id, workspace_id, job_id, attempt_id, provider, "
            "source_job_id, facts, copy, extraction_error) VALUES (:id, :ws, :job, :attempt, "
            ":provider, :source_id, CAST(:facts AS jsonb), CAST(:copy AS jsonb), :error)"
        ),
        {
            "id": copy_id,
            "ws": workspace_id,
            "job": job_id,
            "attempt": attempt_id,
            "provider": provider,
            "source_id": copy.source_job_id,
            "facts": json.dumps(facts),
            "copy": json.dumps(body),
            "error": copy.extraction_error,
        },
    )


def insert_claims(
    tx: Tx,
    *,
    workspace_id: uuid.UUID,
    attempt_id: uuid.UUID,
    copy_id: uuid.UUID,
    copy: JobCopy,
    retrieved_at: datetime,
) -> None:
    for claim in copy.claims:
        data = json.loads(claim.model_dump_json())
        tx.execute(
            sa.text(
                "INSERT INTO nessa.source_claims (workspace_id, attempt_id, copy_id, field, "
                "value, validation, issue, span, retrieved_at, published_on, valid_until) "
                "VALUES (:ws, :attempt, :copy, :field, CAST(:value AS jsonb), :validation, "
                ":issue, CAST(:span AS jsonb), :retrieved, :published, :until)"
            ),
            {
                "ws": workspace_id,
                "attempt": attempt_id,
                "copy": copy_id,
                "field": claim.field.value,
                "value": json.dumps(data["value"]),
                "validation": claim.validation.value,
                "issue": claim.issue,
                "span": json.dumps(data["span"]),
                "retrieved": retrieved_at,
                "published": copy.date_posted,
                "until": copy.valid_through,
            },
        )


def _copy_row(row: sa.Row[Any]) -> CopyRow:
    return CopyRow(
        copy_id=row.copy_id,
        job_id=row.job_id,
        attempt_id=row.attempt_id,
        provider=row.provider,
        copy=JobCopy.model_validate(
            {k: v for k, v in row.copy.items() if k in JobCopy.model_fields}
        ),
        extraction_error=row.extraction_error,
        created_at=row.created_at,
    )


_COPY_COLUMNS = "copy_id, job_id, attempt_id, provider, copy, extraction_error, created_at"


def copies_of_jobs(tx: Tx, job_ids: list[uuid.UUID]) -> list[CopyRow]:
    if not job_ids:
        return []
    rows = tx.execute(
        sa.text(
            f"SELECT {_COPY_COLUMNS} FROM nessa.job_copies WHERE job_id = ANY(:ids) "
            "ORDER BY created_at"
        ),
        {"ids": job_ids},
    )
    return [_copy_row(r) for r in rows]


def copies_of_attempts(tx: Tx, attempt_ids: list[uuid.UUID]) -> list[CopyRow]:
    if not attempt_ids:
        return []
    rows = tx.execute(
        sa.text(
            f"SELECT {_COPY_COLUMNS} FROM nessa.job_copies WHERE attempt_id = ANY(:ids) "
            "ORDER BY created_at"
        ),
        {"ids": attempt_ids},
    )
    return [_copy_row(r) for r in rows]


def claims_of_copies(tx: Tx, copy_ids: list[uuid.UUID]) -> list[ClaimRow]:
    if not copy_ids:
        return []
    rows = tx.execute(
        sa.text(
            "SELECT claim_id, attempt_id, copy_id, field, value, validation, issue, span, "
            "retrieved_at, published_on, valid_until FROM nessa.source_claims "
            "WHERE copy_id = ANY(:ids) ORDER BY claim_id"
        ),
        {"ids": copy_ids},
    )
    return [
        ClaimRow(
            r.claim_id,
            r.attempt_id,
            r.copy_id,
            Claim.model_validate(
                {
                    "field": r.field,
                    "value": r.value,
                    "span": r.span,
                    "validation": r.validation,
                    "issue": r.issue,
                }
            ),
            r.retrieved_at,
            r.published_on,
            r.valid_until,
        )
        for r in rows
    ]


_JOB_COLUMNS = (
    "j.job_id, j.exemplar, j.first_seen_at, j.last_success_at, j.last_attempt_at, j.closed_at, "
    "(f.job_id IS NOT NULL) AS favourite"
)
_JOBS = (
    "nessa.jobs j LEFT JOIN nessa.job_favourites f ON f.workspace_id = j.workspace_id "
    "AND f.job_id = j.job_id"
)


def jobs(
    tx: Tx,
    workspace_id: uuid.UUID,
    *,
    favourites_only: bool,
    before: tuple[datetime, uuid.UUID] | None,
    limit: int,
) -> list[JobRow]:
    cursor = "AND (j.first_seen_at, j.job_id) < (:at, :id) " if before else ""
    favourite = "AND f.job_id IS NOT NULL " if favourites_only else ""
    rows = tx.execute(
        sa.text(
            f"SELECT {_JOB_COLUMNS} FROM {_JOBS} WHERE j.workspace_id = :ws {cursor}{favourite}"
            "ORDER BY j.first_seen_at DESC, j.job_id DESC LIMIT :limit"
        ),
        {
            "ws": workspace_id,
            "limit": limit,
            **({"at": before[0], "id": before[1]} if before else {}),
        },
    ).mappings()
    return [JobRow(**dict(r)) for r in rows]


def job(tx: Tx, workspace_id: uuid.UUID, job_id: uuid.UUID) -> JobRow | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_JOB_COLUMNS} FROM {_JOBS} WHERE j.workspace_id = :ws AND j.job_id = :id"
            ),
            {"ws": workspace_id, "id": job_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else JobRow(**dict(row))


def job_count(tx: Tx, workspace_id: uuid.UUID) -> int:
    return int(
        tx.execute(
            sa.text("SELECT count(*) FROM nessa.jobs WHERE workspace_id = :ws"),
            {"ws": workspace_id},
        ).scalar_one()
    )


def set_favourite(tx: Tx, workspace_id: uuid.UUID, job_id: uuid.UUID, actor_id: uuid.UUID) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO nessa.job_favourites (workspace_id, job_id, created_by) "
            "VALUES (:ws, :job, :by) ON CONFLICT DO NOTHING"
        ),
        {"ws": workspace_id, "job": job_id, "by": actor_id},
    )


def clear_favourite(tx: Tx, workspace_id: uuid.UUID, job_id: uuid.UUID) -> None:
    tx.execute(
        sa.text("DELETE FROM nessa.job_favourites WHERE workspace_id = :ws AND job_id = :job"),
        {"ws": workspace_id, "job": job_id},
    )


def exemplar_count(tx: Tx, workspace_id: uuid.UUID, target_key: str) -> int:
    return int(
        tx.execute(
            sa.text(
                "SELECT count(*) FROM nessa.job_copies WHERE workspace_id = :ws "
                "AND copy ->> 'exemplar_for' = :target"
            ),
            {"ws": workspace_id, "target": target_key},
        ).scalar_one()
    )
