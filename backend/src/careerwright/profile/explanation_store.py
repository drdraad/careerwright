"""SQL for slate explanations (adapter): which run writes the one current explanation a
discovery's slate may have. A link is only ever marked replaced, never changed otherwise."""

import uuid
from datetime import datetime

import sqlalchemy as sa

from careerwright.db import Tx
from careerwright.profile.records import ExplanationRequest

_COLUMNS = "explanation_id, workspace_id, discovery_id, created_by, created_at"


def insert(tx: Tx, request: ExplanationRequest) -> None:
    tx.execute(
        sa.text(
            f"INSERT INTO careerwright.slate_explanations ({_COLUMNS}) "
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
    """The discovery's current link (never a replaced one)."""
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_COLUMNS} FROM careerwright.slate_explanations "
                "WHERE workspace_id = :ws AND discovery_id = :discovery AND replaced_at IS NULL"
            ),
            {"ws": workspace_id, "discovery": discovery_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else ExplanationRequest(**row)


def replace(tx: Tx, explanation_id: uuid.UUID, at: datetime) -> bool:
    """Marks a current link replaced; whether it was current."""
    result = tx.execute(
        sa.text(
            "UPDATE careerwright.slate_explanations SET replaced_at = :at "
            "WHERE explanation_id = :id AND replaced_at IS NULL"
        ),
        {"id": explanation_id, "at": at},
    )
    return result.rowcount == 1
