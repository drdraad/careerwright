"""SQL for runs, the outbox, model attempts, sealed run inputs and outputs, and the sealed
partial reply a run streams (adapter).

Under the worker role, every statement runs in a transaction scoped to one run
(`run_transaction`), and row-level security limits it to that run's workspace.
"""

import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import exc

from nessa.db import Tx, is_unique_violation
from nessa.identity.keyring import SealedValue
from nessa.identity.model_registry import Usage
from nessa.identity.records import Attempt, PartialCompleteness, Run, RunKind
from nessa.identity.spend import SpendState
from nessa.vocabulary import DataMode, WorkState

_RUN_COLUMNS = (
    "r.run_id, r.workspace_id, r.kind, r.data_mode, r.synthetic, r.requested_by, r.model_id, "
    "r.model_mode, r.status, r.failure_class, r.output_id, r.created_at, r.started_at, "
    "r.finished_at, r.profile_version, c.requested_at AS cancel_requested_at"
)
_RUNS = "nessa.runs r LEFT JOIN nessa.run_cancellations c ON c.run_id = r.run_id"
MODEL_RUN_WORKFLOW = "nessa.model_run"
ACQUISITION_WORKFLOW = "nessa.acquisition_run"
_ATTEMPT_COLUMNS = (
    "attempt_id, model_id, started_at, finished_at, outcome, spend_state, reserved_nano_usd, "
    "cost_nano_usd, input_tokens, cached_input_tokens, output_tokens, reasoning_tokens, "
    "web_search_queries, provider_response_id, requests_sent"
)
# The committed cost of an attempt (nessa.identity.spend.committed_cost, in SQL).
_COMMITTED = (
    "CASE spend_state WHEN 'reconciled' THEN cost_nano_usd "
    "WHEN 'none' THEN 0 ELSE reserved_nano_usd END"
)


def _run(row: sa.RowMapping) -> Run:
    return Run(
        run_id=row["run_id"],
        workspace_id=row["workspace_id"],
        kind=RunKind(row["kind"]),
        data_mode=DataMode(row["data_mode"]),
        synthetic=row["synthetic"],
        requested_by=row["requested_by"],
        model_id=row["model_id"],
        model_mode=row["model_mode"],
        status=WorkState(row["status"]),
        failure_class=row["failure_class"],
        output_id=row["output_id"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        profile_version=row["profile_version"],
        cancel_requested_at=row["cancel_requested_at"],
    )


def insert_run(
    tx: Tx,
    run: Run,
    workflow_id: str,
    sealed_input: SealedValue | None,
    *,
    workflow_name: str = MODEL_RUN_WORKFLOW,
) -> None:
    """The run, its sealed input (if it has one) and its outbox entry naming the workflow
    that executes it, in the caller's transaction (transactional outbox)."""
    tx.execute(
        sa.text(
            "INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, "
            "requested_by, model_id, model_mode, status, profile_version) VALUES (:id, :ws, "
            ":mode, :synthetic, :kind, :by, :model, :model_mode, 'queued', :profile_version)"
        ),
        {
            "id": run.run_id,
            "ws": run.workspace_id,
            "mode": run.data_mode.value,
            "synthetic": run.synthetic,
            "kind": run.kind.value,
            "by": run.requested_by,
            "model": run.model_id,
            "model_mode": run.model_mode,
            "profile_version": run.profile_version,
        },
    )
    if sealed_input is not None:
        tx.execute(
            sa.text(
                "INSERT INTO nessa.run_inputs (run_id, workspace_id, key_version, nonce, "
                "ciphertext) VALUES (:id, :ws, :version, :nonce, :ciphertext)"
            ),
            {
                "id": run.run_id,
                "ws": run.workspace_id,
                "version": sealed_input.key_version,
                "nonce": sealed_input.nonce,
                "ciphertext": sealed_input.ciphertext,
            },
        )
    tx.execute(
        sa.text(
            "INSERT INTO nessa.outbox (workspace_id, run_id, workflow_id, workflow_name) "
            "VALUES (:ws, :id, :workflow, :name)"
        ),
        {"ws": run.workspace_id, "id": run.run_id, "workflow": workflow_id, "name": workflow_name},
    )


def sealed_input(tx: Tx, run_id: uuid.UUID) -> SealedValue | None:
    """Worker: the run's sealed input, visible only while its requester may still act."""
    row = tx.execute(
        sa.text("SELECT key_version, nonce, ciphertext FROM nessa.run_inputs WHERE run_id = :id"),
        {"id": run_id},
    ).one_or_none()
    if row is None:
        return None
    return SealedValue(row.key_version, bytes(row.nonce), bytes(row.ciphertext))


def erase_input(tx: Tx) -> bool:
    """Worker: erase the executed run's sealed input, if its kind's input is erased once it
    is terminal and it is (migration 0021, `nessa.erase_run_input`), whether or not its
    requester may still act. Returns whether an input was erased."""
    return bool(tx.execute(sa.text("SELECT nessa.erase_run_input()")).scalar_one())


def all_sealed_inputs(tx: Tx) -> list[tuple[uuid.UUID, uuid.UUID, SealedValue]]:
    """Setup only (master-key rotation): every sealed run input, locked."""
    rows = tx.execute(
        sa.text(
            "SELECT run_id, workspace_id, key_version, nonce, ciphertext "
            "FROM nessa.run_inputs ORDER BY run_id FOR UPDATE"
        )
    )
    return [
        (r.run_id, r.workspace_id, SealedValue(r.key_version, bytes(r.nonce), bytes(r.ciphertext)))
        for r in rows
    ]


def replace_sealed_input(tx: Tx, run_id: uuid.UUID, sealed: SealedValue) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.run_inputs SET key_version = :version, nonce = :nonce, "
            "ciphertext = :ciphertext WHERE run_id = :id"
        ),
        {
            "id": run_id,
            "version": sealed.key_version,
            "nonce": sealed.nonce,
            "ciphertext": sealed.ciphertext,
        },
    )


def upsert_partial(tx: Tx, run: Run, sealed: SealedValue, completeness: PartialCompleteness) -> int:
    """Worker: the run's streamed reply so far, replacing the last; returns its sequence."""
    return int(
        tx.execute(
            sa.text(
                "INSERT INTO nessa.run_partials (run_id, workspace_id, seq, completeness, "
                "key_version, nonce, ciphertext) VALUES (:run, :ws, 1, :completeness, :version, "
                ":nonce, :ciphertext) ON CONFLICT (run_id) DO UPDATE SET "
                "seq = nessa.run_partials.seq + 1, completeness = EXCLUDED.completeness, "
                "key_version = EXCLUDED.key_version, nonce = EXCLUDED.nonce, "
                "ciphertext = EXCLUDED.ciphertext, updated_at = clock_timestamp() RETURNING seq"
            ),
            {
                "run": run.run_id,
                "ws": run.workspace_id,
                "completeness": completeness.value,
                "version": sealed.key_version,
                "nonce": sealed.nonce,
                "ciphertext": sealed.ciphertext,
            },
        ).scalar_one()
    )


def mark_partial_stopped(tx: Tx, run_id: uuid.UUID) -> int | None:
    """Worker: a streaming partial has stopped; its new sequence, or None if the run has no
    streaming partial."""
    seq = tx.execute(
        sa.text(
            "UPDATE nessa.run_partials SET seq = seq + 1, completeness = 'stopped', "
            "updated_at = clock_timestamp() WHERE run_id = :id AND completeness = 'streaming' "
            "RETURNING seq"
        ),
        {"id": run_id},
    ).scalar_one_or_none()
    return None if seq is None else int(seq)


def delete_partial(tx: Tx, run_id: uuid.UUID) -> None:
    """Worker: the validated output supersedes the streamed reply (same transaction)."""
    tx.execute(sa.text("DELETE FROM nessa.run_partials WHERE run_id = :id"), {"id": run_id})


def partial(
    tx: Tx, run_id: uuid.UUID
) -> tuple[int, PartialCompleteness, SealedValue, datetime] | None:
    row = tx.execute(
        sa.text(
            "SELECT seq, completeness, key_version, nonce, ciphertext, updated_at "
            "FROM nessa.run_partials WHERE run_id = :id"
        ),
        {"id": run_id},
    ).one_or_none()
    if row is None:
        return None
    sealed = SealedValue(row.key_version, bytes(row.nonce), bytes(row.ciphertext))
    return int(row.seq), PartialCompleteness(row.completeness), sealed, row.updated_at


def all_sealed_partials(tx: Tx) -> list[tuple[uuid.UUID, uuid.UUID, SealedValue]]:
    """Setup only (master-key rotation): every sealed partial reply, locked."""
    rows = tx.execute(
        sa.text(
            "SELECT run_id, workspace_id, key_version, nonce, ciphertext "
            "FROM nessa.run_partials ORDER BY run_id FOR UPDATE"
        )
    )
    return [
        (r.run_id, r.workspace_id, SealedValue(r.key_version, bytes(r.nonce), bytes(r.ciphertext)))
        for r in rows
    ]


def replace_sealed_partial(tx: Tx, run_id: uuid.UUID, sealed: SealedValue) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.run_partials SET key_version = :version, nonce = :nonce, "
            "ciphertext = :ciphertext WHERE run_id = :id"
        ),
        {
            "id": run_id,
            "version": sealed.key_version,
            "nonce": sealed.nonce,
            "ciphertext": sealed.ciphertext,
        },
    )


def run(tx: Tx, run_id: uuid.UUID, *, lock: bool = False) -> Run | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_RUN_COLUMNS} FROM {_RUNS} WHERE r.run_id = :id"
                + (" FOR UPDATE OF r" if lock else "")
            ),
            {"id": run_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _run(row)


def runs(
    tx: Tx,
    workspace_id: uuid.UUID,
    *,
    before: tuple[datetime, uuid.UUID] | None,
    limit: int,
    kind: RunKind | None = None,
) -> list[Run]:
    """Newest first; only runs of `kind`, if given."""
    cursor = "AND (r.created_at, r.run_id) < (:at, :rid) " if before else ""
    of_kind = "AND r.kind = :kind " if kind else ""
    rows = tx.execute(
        sa.text(
            f"SELECT {_RUN_COLUMNS} FROM {_RUNS} WHERE r.workspace_id = :ws "
            f"{cursor}{of_kind}ORDER BY r.created_at DESC, r.run_id DESC LIMIT :limit"
        ),
        {
            "ws": workspace_id,
            "limit": limit,
            **({"at": before[0], "rid": before[1]} if before else {}),
            **({"kind": kind.value} if kind else {}),
        },
    ).mappings()
    return [_run(row) for row in rows]


def authorised_workspace(tx: Tx) -> uuid.UUID | None:
    """Worker: the run's workspace if its requester still owns it and is still invited."""
    value = tx.execute(sa.text("SELECT nessa.authorised_run_workspace()")).scalar_one()
    return None if value is None else uuid.UUID(str(value))


def mark_running(tx: Tx, run_id: uuid.UUID) -> bool:
    """Queued -> running; returns whether this call made the transition."""
    updated = tx.execute(
        sa.text(
            "UPDATE nessa.runs SET status = 'running', started_at = clock_timestamp() "
            "WHERE run_id = :id AND status = 'queued'"
        ),
        {"id": run_id},
    )
    return updated.rowcount == 1


def finish_run(
    tx: Tx,
    run_id: uuid.UUID,
    status: WorkState,
    *,
    output_id: uuid.UUID | None,
    failure: str | None,
) -> bool:
    """Record a terminal state once; a later re-publication changes nothing."""
    updated = tx.execute(
        sa.text(
            "UPDATE nessa.runs SET status = :status, output_id = :output, "
            "failure_class = :failure, started_at = coalesce(started_at, clock_timestamp()), "
            "finished_at = clock_timestamp() "
            "WHERE run_id = :id AND status IN ('queued', 'running')"
        ),
        {"id": run_id, "status": status.value, "output": output_id, "failure": failure},
    )
    return updated.rowcount == 1


def interrupt_unfinished_attempts(tx: Tx, run_id: uuid.UUID) -> int:
    """A re-executed activity finds attempts its predecessor never finished: the call may
    have been billed, so the reservation stays committed with an unknown cost."""
    updated = tx.execute(
        sa.text(
            "UPDATE nessa.model_attempts SET finished_at = clock_timestamp(), "
            "outcome = 'interrupted', spend_state = CASE spend_state WHEN 'held' THEN 'unknown' "
            "ELSE spend_state END WHERE run_id = :id AND finished_at IS NULL"
        ),
        {"id": run_id},
    )
    return int(updated.rowcount)


def accepted_output(tx: Tx, run_id: uuid.UUID) -> uuid.UUID | None:
    value = tx.execute(
        sa.text("SELECT output_id FROM nessa.run_outputs WHERE run_id = :id"), {"id": run_id}
    ).scalar_one_or_none()
    return None if value is None else uuid.UUID(str(value))


def insert_attempt(
    tx: Tx,
    *,
    run: Run,
    period: date,
    spend_state: SpendState,
    reserved_nano_usd: int = 0,
    credential_id: uuid.UUID | None = None,
    outcome: str | None = None,
) -> int:
    """An attempt that makes no provider call (`SpendState.NONE`) records a known zero cost."""
    finished = "clock_timestamp()" if outcome is not None else "NULL"
    return int(
        tx.execute(
            sa.text(
                "INSERT INTO nessa.model_attempts (run_id, workspace_id, model_id, credential_id, "
                "period_start, reserved_nano_usd, spend_state, cost_nano_usd, outcome, "
                "finished_at) VALUES (:run, :ws, :model, :credential, :period, :reserved, "
                f":state, :cost, :outcome, {finished}) RETURNING attempt_id"
            ),
            {
                "run": run.run_id,
                "ws": run.workspace_id,
                "model": run.model_id,
                "credential": credential_id,
                "period": period,
                "reserved": reserved_nano_usd,
                "state": spend_state.value,
                "cost": 0 if spend_state is SpendState.NONE else None,
                "outcome": outcome,
            },
        ).scalar_one()
    )


def finish_attempt(
    tx: Tx,
    attempt_id: int,
    *,
    outcome: str,
    usage: Usage | None,
    reasoning_tokens: int | None,
    provider_response_id: str | None,
    cost_nano_usd: int | None,
    spend_state: SpendState,
    requests_sent: int | None,
) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.model_attempts SET finished_at = clock_timestamp(), outcome = :outcome, "
            "spend_state = :state, cost_nano_usd = :cost, input_tokens = :input, "
            "cached_input_tokens = :cached, output_tokens = :output, "
            "reasoning_tokens = :reasoning, web_search_queries = :searches, "
            "provider_response_id = :response, requests_sent = :requests "
            "WHERE attempt_id = :id"
        ),
        {
            "id": attempt_id,
            "outcome": outcome,
            "state": spend_state.value,
            "cost": cost_nano_usd,
            "input": usage.input_tokens if usage else None,
            "cached": usage.cached_input_tokens if usage else None,
            "output": usage.output_tokens if usage else None,
            "reasoning": reasoning_tokens,
            "searches": usage.web_search_queries if usage else None,
            "response": provider_response_id,
            "requests": requests_sent,
        },
    )


def lock_spend(tx: Tx, workspace_id: uuid.UUID) -> None:
    """Serialise reservations per workspace for the rest of the transaction."""
    tx.execute(
        sa.text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"nessa-spend:{workspace_id}"},
    )


def committed_spend(
    tx: Tx, workspace_id: uuid.UUID, run_id: uuid.UUID, period: date
) -> tuple[int, int]:
    row = tx.execute(
        sa.text(
            f"SELECT coalesce(sum({_COMMITTED}) FILTER (WHERE period_start = :period), 0) "
            f"AS period, coalesce(sum({_COMMITTED}) FILTER (WHERE run_id = :run), 0) AS run "
            "FROM nessa.model_attempts WHERE workspace_id = :ws"
        ),
        {"ws": workspace_id, "run": run_id, "period": period},
    ).one()
    return int(row.period), int(row.run)


def insert_output(
    tx: Tx, *, output_id: uuid.UUID, run: Run, sealed: SealedValue, content_sha256: str
) -> tuple[uuid.UUID, bool]:
    """The first validated output for a run; returns (output_id, newly accepted)."""
    try:
        with tx.begin_nested():
            tx.execute(
                sa.text(
                    "INSERT INTO nessa.run_outputs (output_id, run_id, workspace_id, key_version, "
                    "nonce, ciphertext, content_sha256) VALUES (:id, :run, :ws, :version, :nonce, "
                    ":ciphertext, :sha)"
                ),
                {
                    "id": output_id,
                    "run": run.run_id,
                    "ws": run.workspace_id,
                    "version": sealed.key_version,
                    "nonce": sealed.nonce,
                    "ciphertext": sealed.ciphertext,
                    "sha": content_sha256,
                },
            )
    except exc.IntegrityError as error:
        if not is_unique_violation(error):
            raise
        existing = accepted_output(tx, run.run_id)
        if existing is None:
            raise
        return existing, False
    return output_id, True


def sealed_output(tx: Tx, run_id: uuid.UUID) -> tuple[uuid.UUID, SealedValue] | None:
    row = tx.execute(
        sa.text(
            "SELECT output_id, key_version, nonce, ciphertext FROM nessa.run_outputs "
            "WHERE run_id = :id"
        ),
        {"id": run_id},
    ).one_or_none()
    if row is None:
        return None
    return row.output_id, SealedValue(row.key_version, bytes(row.nonce), bytes(row.ciphertext))


def all_sealed_outputs(tx: Tx) -> list[tuple[uuid.UUID, uuid.UUID, SealedValue]]:
    """Setup only (master-key rotation): every sealed run output, locked."""
    rows = tx.execute(
        sa.text(
            "SELECT output_id, workspace_id, key_version, nonce, ciphertext "
            "FROM nessa.run_outputs ORDER BY output_id FOR UPDATE"
        )
    )
    return [
        (
            r.output_id,
            r.workspace_id,
            SealedValue(r.key_version, bytes(r.nonce), bytes(r.ciphertext)),
        )
        for r in rows
    ]


def replace_sealed_output(tx: Tx, output_id: uuid.UUID, sealed: SealedValue) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.run_outputs SET key_version = :version, nonce = :nonce, "
            "ciphertext = :ciphertext WHERE output_id = :id"
        ),
        {
            "id": output_id,
            "version": sealed.key_version,
            "nonce": sealed.nonce,
            "ciphertext": sealed.ciphertext,
        },
    )


def attempts(tx: Tx, run_id: uuid.UUID) -> list[Attempt]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_ATTEMPT_COLUMNS} FROM nessa.model_attempts WHERE run_id = :id "
            "ORDER BY attempt_id"
        ),
        {"id": run_id},
    ).mappings()
    return [Attempt(**dict(row)) for row in rows]


def period_spend(tx: Tx, workspace_id: uuid.UUID, period: date) -> tuple[int, int]:
    """(committed nano-USD, attempts whose cost is unknown) for one period."""
    row = tx.execute(
        sa.text(
            f"SELECT coalesce(sum({_COMMITTED}), 0) AS committed, "
            "count(*) FILTER (WHERE spend_state IN ('unknown', 'held')) AS unknown "
            "FROM nessa.model_attempts WHERE workspace_id = :ws AND period_start = :period"
        ),
        {"ws": workspace_id, "period": period},
    ).one()
    return int(row.committed), int(row.unknown)


def pending_outbox(tx: Tx, limit: int = 50) -> list[tuple[int, str, uuid.UUID, str]]:
    """(outbox ID, workflow ID, run ID, workflow name) of entries not yet dispatched. A run
    cancelled before dispatch is never started."""
    rows = tx.execute(
        sa.text(
            "SELECT o.outbox_id, o.workflow_id, o.run_id, o.workflow_name FROM nessa.outbox o "
            "WHERE o.dispatched_at IS NULL AND NOT EXISTS "
            "(SELECT 1 FROM nessa.run_cancellations c WHERE c.run_id = o.run_id) "
            "ORDER BY o.outbox_id LIMIT :limit"
        ),
        {"limit": limit},
    )
    return [(r.outbox_id, r.workflow_id, r.run_id, r.workflow_name) for r in rows]


# The advisory lock a run's cancellation and the starting of a run by it both take, so a cancel
# either sees a run that was started or the starting sees the cancel (migration 0023).
_STARTED_RUNS_LOCK = 8237


def lock_started_runs(tx: Tx, run_id: uuid.UUID) -> None:
    """Hold the run's cancellation lock until the transaction ends. Taken before any row
    lock (the API's cancel takes it before the workspace's), so it never deadlocks with the
    worker, which takes it before writing an event."""
    tx.execute(
        sa.text("SELECT pg_advisory_xact_lock(hashtextextended(CAST(:run AS text), :key))"),
        {"run": run_id, "key": _STARTED_RUNS_LOCK},
    )


def unsettled_started_runs(tx: Tx, run_id: uuid.UUID) -> list[Run]:
    """API: the runs this run started (`started_by_run`) that are still queued or running."""
    rows = tx.execute(
        sa.text(
            f"SELECT {_RUN_COLUMNS} FROM {_RUNS} WHERE r.started_by_run = :run "
            "AND r.status IN ('queued', 'running') ORDER BY r.created_at"
        ),
        {"run": run_id},
    ).mappings()
    return [_run(row) for row in rows]


def request_cancellation(tx: Tx, run: Run, requested_by: uuid.UUID) -> bool:
    """API: record the request once; returns whether this call recorded it."""
    inserted = tx.execute(
        sa.text(
            "INSERT INTO nessa.run_cancellations (run_id, workspace_id, requested_by) "
            "VALUES (:run, :ws, :by) ON CONFLICT (run_id) DO NOTHING"
        ),
        {"run": run.run_id, "ws": run.workspace_id, "by": requested_by},
    )
    return inserted.rowcount == 1


def pending_cancellations(tx: Tx, limit: int = 50) -> list[tuple[uuid.UUID, str, bool]]:
    """Worker, unscoped: (run ID, workflow ID, dispatched) of requests not yet acted on."""
    rows = tx.execute(
        sa.text(
            "SELECT c.run_id, o.workflow_id, o.dispatched_at IS NOT NULL AS dispatched "
            "FROM nessa.run_cancellations c JOIN nessa.outbox o ON o.run_id = c.run_id "
            "WHERE c.signalled_at IS NULL ORDER BY c.requested_at LIMIT :limit"
        ),
        {"limit": limit},
    )
    return [(r.run_id, r.workflow_id, r.dispatched) for r in rows]


def mark_cancellation_signalled(tx: Tx, run_id: uuid.UUID) -> None:
    tx.execute(
        sa.text(
            "UPDATE nessa.run_cancellations SET signalled_at = clock_timestamp() WHERE run_id = :id"
        ),
        {"id": run_id},
    )


def mark_dispatched(tx: Tx, outbox_id: int) -> None:
    tx.execute(
        sa.text("UPDATE nessa.outbox SET dispatched_at = clock_timestamp() WHERE outbox_id = :id"),
        {"id": outbox_id},
    )
