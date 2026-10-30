"""SQL for interview turns and decisions (adapter; both tables are append-only) and the
interview preferences (one versioned row per workspace)."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from careerwright.db import Tx, is_unique_violation
from careerwright.profile.records import (
    ConversationMode,
    EntryMode,
    InterviewPreferences,
    InterviewTurn,
    TurnDecision,
)

_TURN_COLUMNS = (
    "turn_id, workspace_id, message_id, message, profile_version, created_by, created_at"
)
_DECISION_COLUMNS = (
    "turn_id, decided_by, decided_at, accepted_change_ids, rejected_change_ids, "
    "confirmed_hard_constraints, profile_version"
)


def _decision(row: sa.RowMapping) -> TurnDecision:
    return TurnDecision(
        turn_id=row["turn_id"],
        decided_by=row["decided_by"],
        decided_at=row["decided_at"],
        accepted_change_ids=tuple(row["accepted_change_ids"]),
        rejected_change_ids=tuple(row["rejected_change_ids"]),
        confirmed_hard_constraints=tuple(row["confirmed_hard_constraints"]),
        profile_version=row["profile_version"],
    )


def insert_turn(tx: Tx, turn: InterviewTurn) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.interview_turns (turn_id, workspace_id, message_id, message, "
            "profile_version, created_by, created_at) VALUES (:id, :ws, :message_id, :message, "
            ":version, :by, :at)"
        ),
        {
            "id": turn.turn_id,
            "ws": turn.workspace_id,
            "message_id": turn.message_id,
            "message": turn.message,
            "version": turn.profile_version,
            "by": turn.created_by,
            "at": turn.created_at,
        },
    )


def turn(tx: Tx, workspace_id: uuid.UUID, turn_id: uuid.UUID) -> InterviewTurn | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_TURN_COLUMNS} FROM careerwright.interview_turns "
                "WHERE workspace_id = :ws AND turn_id = :id"
            ),
            {"ws": workspace_id, "id": turn_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else InterviewTurn(**dict(row))


def turns(
    tx: Tx, workspace_id: uuid.UUID, *, before: tuple[datetime, uuid.UUID] | None, limit: int
) -> list[InterviewTurn]:
    """Newest first."""
    cursor = "AND (created_at, turn_id) < (:at, :id) " if before else ""
    rows = tx.execute(
        sa.text(
            f"SELECT {_TURN_COLUMNS} FROM careerwright.interview_turns WHERE workspace_id = :ws "
            f"{cursor}ORDER BY created_at DESC, turn_id DESC LIMIT :limit"
        ),
        {
            "ws": workspace_id,
            "limit": limit,
            **({"at": before[0], "id": before[1]} if before else {}),
        },
    ).mappings()
    return [InterviewTurn(**dict(row)) for row in rows]


def message_times(
    tx: Tx, workspace_id: uuid.UUID, message_ids: set[uuid.UUID]
) -> dict[uuid.UUID, datetime]:
    """When each of these messages was sent (missing IDs are simply absent)."""
    if not message_ids:
        return {}
    rows = tx.execute(
        sa.text(
            "SELECT message_id, created_at FROM careerwright.interview_turns "
            "WHERE workspace_id = :ws AND message_id = ANY(:ids)"
        ),
        {"ws": workspace_id, "ids": sorted(message_ids)},
    )
    return {row.message_id: row.created_at for row in rows}


def decision(tx: Tx, turn_id: uuid.UUID) -> TurnDecision | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_DECISION_COLUMNS} FROM careerwright.interview_decisions WHERE turn_id = "
                ":id"
            ),
            {"id": turn_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _decision(row)


def insert_decision(tx: Tx, workspace_id: uuid.UUID, decided: TurnDecision) -> bool:
    """False if the turn already has a decision (the first one stands)."""
    try:
        with tx.begin_nested():
            tx.execute(
                sa.text(
                    "INSERT INTO careerwright.interview_decisions (turn_id, workspace_id, "
                    "decided_by, "
                    "decided_at, accepted_change_ids, rejected_change_ids, "
                    "confirmed_hard_constraints, profile_version) VALUES (:id, :ws, :by, :at, "
                    ":accepted, :rejected, :confirmed, :version)"
                ),
                {
                    "id": decided.turn_id,
                    "ws": workspace_id,
                    "by": decided.decided_by,
                    "at": decided.decided_at,
                    "accepted": list(decided.accepted_change_ids),
                    "rejected": list(decided.rejected_change_ids),
                    "confirmed": list(decided.confirmed_hard_constraints),
                    "version": decided.profile_version,
                },
            )
    except exc.IntegrityError as error:
        if is_unique_violation(error):
            return False
        raise
    return True


def preferences(tx: Tx, workspace_id: uuid.UUID) -> InterviewPreferences | None:
    row = (
        tx.execute(
            sa.text(
                "SELECT workspace_id, version, entry_mode, conversation_mode, paused, "
                "updated_by, updated_at FROM careerwright.interview_preferences WHERE workspace_id "
                "= :ws"
            ),
            {"ws": workspace_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    return InterviewPreferences(
        workspace_id=row["workspace_id"],
        version=row["version"],
        entry_mode=EntryMode(row["entry_mode"]) if row["entry_mode"] else None,
        conversation_mode=(
            ConversationMode(row["conversation_mode"]) if row["conversation_mode"] else None
        ),
        paused=row["paused"],
        updated_by=row["updated_by"],
        updated_at=row["updated_at"],
    )


def write_preferences(
    tx: Tx,
    workspace_id: uuid.UUID,
    expected_version: int,
    *,
    entry_mode: EntryMode | None,
    conversation_mode: ConversationMode | None,
    paused: bool,
    updated_by: uuid.UUID,
) -> bool:
    """Insert version 1, or move `expected_version` on by one; False if it is not current
    (the caller holds the workspace lock, so only a stale expectation fails)."""
    values = {
        "ws": workspace_id,
        "expected": expected_version,
        "entry": entry_mode.value if entry_mode else None,
        "mode": conversation_mode.value if conversation_mode else None,
        "paused": paused,
        "by": updated_by,
    }
    if expected_version == 0:
        inserted = tx.execute(
            sa.text(
                "INSERT INTO careerwright.interview_preferences (workspace_id, entry_mode, "
                "conversation_mode, paused, version, updated_by) VALUES (:ws, :entry, :mode, "
                ":paused, 1, :by) ON CONFLICT (workspace_id) DO NOTHING"
            ),
            values,
        )
        return inserted.rowcount == 1
    updated = tx.execute(
        sa.text(
            "UPDATE careerwright.interview_preferences SET entry_mode = :entry, "
            "conversation_mode = :mode, paused = :paused, version = version + 1, "
            "updated_by = :by, updated_at = clock_timestamp() "
            "WHERE workspace_id = :ws AND version = :expected"
        ),
        values,
    )
    return updated.rowcount == 1
