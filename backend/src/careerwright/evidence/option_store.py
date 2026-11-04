"""Workspace-private option research and its proposed source records."""

import uuid
from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.engine import RowMapping

from careerwright.catalogue.planning import Catalogue
from careerwright.db import Tx


@dataclass(frozen=True)
class ResearchRow:
    research_id: uuid.UUID
    workspace_id: uuid.UUID
    target: str
    city: str
    search_run_id: uuid.UUID
    reading_run_id: uuid.UUID | None
    review_state: str
    created_at: datetime
    reading_started_at: datetime | None


@dataclass(frozen=True)
class RecordRow:
    record_id: uuid.UUID
    workspace_id: uuid.UUID
    research_id: uuid.UUID
    attempt_id: uuid.UUID
    record_kind: str
    record_position: int
    catalogue: Catalogue
    source_url: str
    retrieved_at: datetime
    expires_at: datetime


_RESEARCH = (
    "research_id, workspace_id, target, city, search_run_id, reading_run_id, review_state, "
    "created_at, reading_started_at"
)
_RECORD = (
    "record_id, workspace_id, research_id, attempt_id, record_kind, record_position, "
    "catalogue, source_url, "
    "retrieved_at, expires_at"
)
_RECORD_COLUMNS = tuple(part.strip() for part in _RECORD.split(","))


def insert_research(
    tx: Tx,
    *,
    research_id: uuid.UUID,
    workspace_id: uuid.UUID,
    target: str,
    city: str,
    search_run_id: uuid.UUID,
    now: datetime,
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.option_researches "
            "(research_id, workspace_id, target, city, search_run_id, created_at) "
            "VALUES (:id, :ws, :target, :city, :search, :now)"
        ),
        {
            "id": research_id,
            "ws": workspace_id,
            "target": target,
            "city": city,
            "search": search_run_id,
            "now": now,
        },
    )


def research(
    tx: Tx, workspace_id: uuid.UUID, research_id: uuid.UUID, *, lock: bool = False
) -> ResearchRow | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_RESEARCH} FROM careerwright.option_researches "
                "WHERE workspace_id = :ws AND research_id = :id" + (" FOR UPDATE" if lock else "")
            ),
            {"ws": workspace_id, "id": research_id},
        )
        .mappings()
        .one_or_none()
    )
    return ResearchRow(**row) if row else None


def researches(tx: Tx, workspace_id: uuid.UUID, limit: int) -> list[ResearchRow]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_RESEARCH} FROM careerwright.option_researches "
            "WHERE workspace_id = :ws ORDER BY created_at DESC, research_id LIMIT :limit"
        ),
        {"ws": workspace_id, "limit": limit},
    ).mappings()
    return [ResearchRow(**row) for row in rows]


def set_reading(tx: Tx, research_id: uuid.UUID, run_id: uuid.UUID, now: datetime) -> None:
    tx.execute(
        sa.text(
            "UPDATE careerwright.option_researches SET reading_run_id = :run, "
            "reading_started_at = :now WHERE research_id = :id AND reading_run_id IS NULL"
        ),
        {"id": research_id, "run": run_id, "now": now},
    )


def insert_record(
    tx: Tx,
    *,
    record_id: uuid.UUID,
    workspace_id: uuid.UUID,
    research_id: uuid.UUID,
    attempt_id: uuid.UUID,
    kind: str,
    position: int,
    catalogue: Catalogue,
    source_url: str,
    retrieved_at: datetime,
    expires_at: datetime,
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.researched_option_records "
            "(record_id, workspace_id, research_id, attempt_id, record_kind, "
            "record_position, catalogue, source_url, retrieved_at, expires_at) "
            "VALUES (:id, :ws, :research, :attempt, :kind, :position, "
            "CAST(:catalogue AS jsonb), :url, :retrieved, :expires) "
            "ON CONFLICT ON CONSTRAINT researched_option_record_slot DO NOTHING"
        ),
        {
            "id": record_id,
            "ws": workspace_id,
            "research": research_id,
            "attempt": attempt_id,
            "kind": kind,
            "position": position,
            "catalogue": catalogue.model_dump_json(),
            "url": source_url,
            "retrieved": retrieved_at,
            "expires": expires_at,
        },
    )


def _record(row: RowMapping) -> RecordRow:
    return RecordRow(
        record_id=row["record_id"],
        workspace_id=row["workspace_id"],
        research_id=row["research_id"],
        attempt_id=row["attempt_id"],
        record_kind=row["record_kind"],
        record_position=row["record_position"],
        catalogue=Catalogue.model_validate(row["catalogue"]),
        source_url=row["source_url"],
        retrieved_at=row["retrieved_at"],
        expires_at=row["expires_at"],
    )


def records(tx: Tx, workspace_id: uuid.UUID, research_id: uuid.UUID) -> list[RecordRow]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_RECORD} FROM careerwright.researched_option_records "
            "WHERE workspace_id = :ws AND research_id = :research "
            "ORDER BY retrieved_at, record_kind, record_position"
        ),
        {"ws": workspace_id, "research": research_id},
    ).mappings()
    return [_record(row) for row in rows]


def active_records(tx: Tx, workspace_id: uuid.UUID) -> list[tuple[str, RecordRow]]:
    """Check the stored fee/intake or funding availability/rule deadline on every read;
    expired facts never enter a route search, even if the UI has not refreshed yet."""
    columns = ", ".join(f"o.{name}" for name in _RECORD_COLUMNS)
    rows = tx.execute(
        sa.text(
            f"SELECT r.target, {columns} FROM careerwright.researched_option_records o "
            "JOIN careerwright.option_researches r ON r.research_id = o.research_id "
            "WHERE o.workspace_id = :ws AND o.expires_at > CURRENT_TIMESTAMP "
            "ORDER BY o.retrieved_at, o.record_kind, o.record_position"
        ),
        {"ws": workspace_id},
    ).mappings()
    return [(row["target"], _record(row)) for row in rows]
