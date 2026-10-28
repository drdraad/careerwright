"""SQL for slate explanations (adapter; the table is append-only): which run writes the one
explanation a discovery's slate may have."""

import uuid

import sqlalchemy as sa

from nessa.db import Tx
from nessa.profile.records import ExplanationRequest

_COLUMNS = "explanation_id, workspace_id, discovery_id, created_by, created_at"


def insert(tx: Tx, request: ExplanationRequest) -> None:
    tx.execute(
        sa.text(
            f"INSERT INTO nessa.slate_explanations ({_COLUMNS}) "
            "VALUES (:id, :ws, :discovery, :by, :at)"
        ),
        {
            "id": request.explanation_id,
            "ws": request.workspace_id,
            "discovery": request.discovery_id,
            "by": request.created_by,
            "at": request.created_at,
        },
    )


def for_discovery(
    tx: Tx, workspace_id: uuid.UUID, discovery_id: uuid.UUID
) -> ExplanationRequest | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_COLUMNS} FROM nessa.slate_explanations "
                "WHERE workspace_id = :ws AND discovery_id = :discovery"
            ),
            {"ws": workspace_id, "discovery": discovery_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else ExplanationRequest(**row)
