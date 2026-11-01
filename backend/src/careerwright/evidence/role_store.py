"""SQL for role research's records (adapter; Task 6e, migration 0042): the research itself
(the title, its search and the acquisition that read its pages) and what code found of the
title on each page read.

The API runs these inside `actor_transaction`; the worker records a page's check inside
`run_transaction`, for its own run's attempt while the requester may act.
"""

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa

from careerwright.db import Tx
from careerwright.evidence.corroboration import TitleCheck
from careerwright.evidence.jobs import facts_from_json, facts_json


@dataclass(frozen=True)
class ResearchRow:
    research_id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    title_key: str
    search_run_id: uuid.UUID
    reading_run_id: uuid.UUID | None
    review_state: str
    created_at: datetime
    reading_started_at: datetime | None


_RESEARCH_COLUMNS = (
    "research_id, workspace_id, title, title_key, search_run_id, reading_run_id, review_state, "
    "created_at, reading_started_at"
)


def insert_research(
    tx: Tx,
    *,
    research_id: uuid.UUID,
    workspace_id: uuid.UUID,
    title: str,
    title_key: str,
    search_run_id: uuid.UUID,
    requested_by: uuid.UUID,
    now: datetime,
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.role_researches (research_id, workspace_id, title, "
            "title_key, search_run_id, requested_by, created_at) VALUES (:id, :ws, :title, "
            ":key, :search, :by, :now)"
        ),
        {
            "id": research_id,
            "ws": workspace_id,
            "title": title,
            "key": title_key,
            "search": search_run_id,
            "by": requested_by,
            "now": now,
        },
    )


def research(
    tx: Tx, workspace_id: uuid.UUID, research_id: uuid.UUID, *, lock: bool = False
) -> ResearchRow | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_RESEARCH_COLUMNS} FROM careerwright.role_researches "
                "WHERE workspace_id = :ws AND research_id = :id" + (" FOR UPDATE" if lock else "")
            ),
            {"ws": workspace_id, "id": research_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else ResearchRow(**row)


def researches(tx: Tx, workspace_id: uuid.UUID, limit: int) -> list[ResearchRow]:
    """The workspace's researches, newest first."""
    rows = tx.execute(
        sa.text(
            f"SELECT {_RESEARCH_COLUMNS} FROM careerwright.role_researches "
            "WHERE workspace_id = :ws ORDER BY created_at DESC, research_id LIMIT :limit"
        ),
        {"ws": workspace_id, "limit": limit},
    ).mappings()
    return [ResearchRow(**r) for r in rows]


def set_reading(tx: Tx, research_id: uuid.UUID, reading_run_id: uuid.UUID, now: datetime) -> None:
    tx.execute(
        sa.text(
            "UPDATE careerwright.role_researches SET reading_run_id = :run, "
            "reading_started_at = :now WHERE research_id = :id AND reading_run_id IS NULL"
        ),
        {"id": research_id, "run": reading_run_id, "now": now},
    )


def insert_page_check(
    tx: Tx, *, attempt_id: uuid.UUID, workspace_id: uuid.UUID, check: TitleCheck
) -> None:
    start, end = check.span if check.span is not None else (None, None)
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.role_page_checks (attempt_id, workspace_id, text_sha256, "
            "span_start, span_end, excerpt, passage_sha256, postings) VALUES (:attempt, :ws, "
            ":sha, :start, :end, :excerpt, :passage, CAST(:postings AS jsonb)) "
            "ON CONFLICT (attempt_id) DO NOTHING"
        ),
        {
            "attempt": attempt_id,
            "ws": workspace_id,
            "sha": check.text_sha256,
            "start": start,
            "end": end,
            "excerpt": check.excerpt,
            "passage": check.passage_sha256,
            "postings": json.dumps([facts_json(p) for p in check.postings]),
        },
    )


def page_checks(tx: Tx, attempt_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, TitleCheck]:
    if not attempt_ids:
        return {}
    rows = tx.execute(
        sa.text(
            "SELECT attempt_id, text_sha256, span_start, span_end, excerpt, passage_sha256, "
            "postings FROM careerwright.role_page_checks WHERE attempt_id = ANY(:ids)"
        ),
        {"ids": list(attempt_ids)},
    ).mappings()
    return {
        r["attempt_id"]: TitleCheck(
            text_sha256=r["text_sha256"],
            span=(r["span_start"], r["span_end"]) if r["span_start"] is not None else None,
            excerpt=r["excerpt"],
            passage_sha256=r["passage_sha256"],
            postings=tuple(facts_from_json(p) for p in r["postings"]),
        )
        for r in rows
    }
