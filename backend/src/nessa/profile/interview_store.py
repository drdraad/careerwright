"""SQL for interview turns and decisions (adapter). Both tables are append-only."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from nessa.db import Tx, is_unique_violation
from nessa.profile.records import InterviewTurn, TurnDecision

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
            "INSERT INTO nessa.interview_turns (turn_id, workspace_id, message_id, message, "
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
                f"SELECT {_TURN_COLUMNS} FROM nessa.interview_turns "
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
            f"SELECT {_TURN_COLUMNS} FROM nessa.interview_turns WHERE workspace_id = :ws "
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
            "SELECT message_id, created_at FROM nessa.interview_turns "
            "WHERE workspace_id = :ws AND message_id = ANY(:ids)"
        ),
        {"ws": workspace_id, "ids": sorted(message_ids)},
    )
    return {row.message_id: row.created_at for row in rows}


def decision(tx: Tx, turn_id: uuid.UUID) -> TurnDecision | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_DECISION_COLUMNS} FROM nessa.interview_decisions WHERE turn_id = :id"
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
                    "INSERT INTO nessa.interview_decisions (turn_id, workspace_id, decided_by, "
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
