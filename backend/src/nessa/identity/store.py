"""SQL for actors, workspaces, events and command receipts (adapter; plain SQLAlchemy Core).

Every function runs inside a caller's transaction. Under a runtime role, row-level security
decides which rows exist; these functions never filter by owner themselves.
"""

import json
import uuid
from collections.abc import Mapping
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from nessa.db import Tx, is_unique_violation
from nessa.identity.access import Actor
from nessa.identity.records import EventKind, Receipt, Workspace, WorkspaceEvent
from nessa.vocabulary import DataMode, WorkState

_WORKSPACE_COLUMNS = (
    "workspace_id, owner_actor_id, name, data_mode, synthetic, fixture_key, version, "
    "created_at, updated_at"
)


class DuplicateReceiptError(Exception):
    """Another transaction recorded this idempotency key first."""


def _workspace(row: sa.RowMapping) -> Workspace:
    return Workspace(
        workspace_id=row["workspace_id"],
        owner_actor_id=row["owner_actor_id"],
        name=row["name"],
        data_mode=DataMode(row["data_mode"]),
        synthetic=row["synthetic"],
        fixture_key=row["fixture_key"],
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def resolve_active_actor(tx: Tx, firebase_uid: str, email: str) -> Actor | None:
    """The invited, active actor for a verified identity, or None (uninvited or revoked)."""
    row = tx.execute(
        sa.text("SELECT actor_id, access, display_name FROM nessa.resolve_actor(:uid, :email)"),
        {"uid": firebase_uid, "email": email},
    ).one_or_none()
    if row is None or row.access != "active":
        return None
    return Actor(row.actor_id, email, row.display_name)


def upsert_actor(tx: Tx, actor_id: uuid.UUID, email: str, display_name: str) -> None:
    """Setup only (migration owner): add or refresh an invitation."""
    tx.execute(
        sa.text(
            "INSERT INTO nessa.actors (actor_id, email, display_name, access) "
            "VALUES (:id, :email, :name, 'active') ON CONFLICT (actor_id) DO UPDATE "
            "SET email = excluded.email, display_name = excluded.display_name"
        ),
        {"id": actor_id, "email": email.lower(), "name": display_name},
    )


def insert_workspace(
    tx: Tx,
    *,
    workspace_id: uuid.UUID,
    owner_actor_id: uuid.UUID,
    name: str,
    data_mode: DataMode,
    synthetic: bool,
    fixture_key: str | None = None,
    last_event_seq: int = 0,
) -> Workspace:
    row = tx.execute(
        sa.text(
            "INSERT INTO nessa.workspaces (workspace_id, owner_actor_id, name, data_mode, "
            "synthetic, fixture_key, last_event_seq) VALUES (:id, :owner, :name, :mode, "
            f":synthetic, :fixture, :seq) RETURNING {_WORKSPACE_COLUMNS}"
        ),
        {
            "id": workspace_id,
            "owner": owner_actor_id,
            "name": name,
            "mode": data_mode.value,
            "synthetic": synthetic,
            "fixture": fixture_key,
            "seq": last_event_seq,
        },
    ).mappings()
    return _workspace(row.one())


def get_workspace(tx: Tx, workspace_id: uuid.UUID, *, lock: bool = False) -> Workspace | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_WORKSPACE_COLUMNS} FROM nessa.workspaces WHERE workspace_id = :id"
                + (" FOR UPDATE" if lock else "")
            ),
            {"id": workspace_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _workspace(row)


def list_workspaces(
    tx: Tx, *, after: tuple[datetime, uuid.UUID] | None, limit: int
) -> list[Workspace]:
    cursor = "WHERE (created_at, workspace_id) > (:after_at, :after_id) " if after else ""
    rows = tx.execute(
        sa.text(
            f"SELECT {_WORKSPACE_COLUMNS} FROM nessa.workspaces "
            f"{cursor}ORDER BY created_at, workspace_id LIMIT :limit"
        ),
        {"limit": limit, **({"after_at": after[0], "after_id": after[1]} if after else {})},
    ).mappings()
    return [_workspace(row) for row in rows]


def rename_workspace(
    tx: Tx, workspace_id: uuid.UUID, expected_version: int, name: str
) -> Workspace | None:
    """Optimistic update: None when the version moved on (or the workspace is not visible)."""
    row = (
        tx.execute(
            sa.text(
                "UPDATE nessa.workspaces SET name = :name, version = version + 1, "
                "updated_at = clock_timestamp() "
                "WHERE workspace_id = :id AND version = :expected "
                f"RETURNING {_WORKSPACE_COLUMNS}"
            ),
            {"id": workspace_id, "expected": expected_version, "name": name},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _workspace(row)


def fixture_workspace(tx: Tx, fixture_key: str) -> tuple[uuid.UUID, int] | None:
    """Setup only: the named fixture workspace and its last event sequence number."""
    row = tx.execute(
        sa.text(
            "SELECT workspace_id, last_event_seq FROM nessa.workspaces WHERE fixture_key = :key"
        ),
        {"key": fixture_key},
    ).one_or_none()
    return None if row is None else (row.workspace_id, row.last_event_seq)


def delete_fixture_workspace(tx: Tx, fixture_key: str) -> None:
    """Setup only: remove one fixture workspace and everything it owns (cascade)."""
    tx.execute(
        sa.text("DELETE FROM nessa.workspaces WHERE fixture_key = :key AND data_mode = 'demo'"),
        {"key": fixture_key},
    )


def append_event(
    tx: Tx,
    workspace_id: uuid.UUID,
    kind: EventKind,
    subject_id: str,
    *,
    state: WorkState | None = None,
    detail: Mapping[str, str | int] | None = None,
) -> int:
    # The workspace row lock orders sequence numbers by commit (see the table comment).
    seq = tx.execute(
        sa.text(
            "UPDATE nessa.workspaces SET last_event_seq = last_event_seq + 1 "
            "WHERE workspace_id = :id RETURNING last_event_seq"
        ),
        {"id": workspace_id},
    ).scalar_one()
    tx.execute(
        sa.text(
            "INSERT INTO nessa.workspace_events (workspace_id, seq, kind, subject_id, state, "
            "detail) VALUES (:id, :seq, :kind, :subject, :state, CAST(:detail AS jsonb))"
        ),
        {
            "id": workspace_id,
            "seq": seq,
            "kind": kind.value,
            "subject": subject_id,
            "state": state.value if state else None,
            "detail": json.dumps(dict(detail or {})),
        },
    )
    return int(seq)


def events_after(
    tx: Tx, workspace_id: uuid.UUID, after_seq: int, limit: int
) -> list[WorkspaceEvent]:
    rows = tx.execute(
        sa.text(
            "SELECT workspace_id, seq, kind, subject_id, state, detail, created_at "
            "FROM nessa.workspace_events WHERE workspace_id = :id AND seq > :after "
            "ORDER BY seq LIMIT :limit"
        ),
        {"id": workspace_id, "after": after_seq, "limit": limit},
    ).mappings()
    return [
        WorkspaceEvent(
            workspace_id=row["workspace_id"],
            seq=row["seq"],
            kind=EventKind(row["kind"]),
            subject_id=row["subject_id"],
            state=WorkState(row["state"]) if row["state"] else None,
            created_at=row["created_at"],
            detail=row["detail"],
        )
        for row in rows
    ]


def read_receipt(tx: Tx, actor_id: uuid.UUID, key: uuid.UUID) -> Receipt | None:
    row = tx.execute(
        sa.text(
            "SELECT command, request_sha256, status_code, response FROM nessa.command_receipts "
            "WHERE actor_id = :actor AND idempotency_key = :key"
        ),
        {"actor": actor_id, "key": key},
    ).one_or_none()
    return (
        None
        if row is None
        else Receipt(row.command, row.request_sha256, row.status_code, row.response)
    )


def write_receipt(tx: Tx, actor_id: uuid.UUID, key: uuid.UUID, receipt: Receipt) -> None:
    try:
        with tx.begin_nested():
            tx.execute(
                sa.text(
                    "INSERT INTO nessa.command_receipts (actor_id, idempotency_key, command, "
                    "request_sha256, status_code, response) VALUES (:actor, :key, :command, "
                    ":sha, :status, CAST(:response AS jsonb))"
                ),
                {
                    "actor": actor_id,
                    "key": key,
                    "command": receipt.command,
                    "sha": receipt.request_sha256,
                    "status": receipt.status_code,
                    "response": json.dumps(receipt.response),
                },
            )
    except exc.IntegrityError as error:
        if is_unique_violation(error):
            raise DuplicateReceiptError from None
        raise
