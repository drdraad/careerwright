"""SQL for the capability state, skill evidence, requirement statements, matrix edits and
overlooked strengths (adapter; migrations 0029 and 0031). Every table but the state is
append-only."""

import uuid
from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from careerwright.capability.evidence import (
    Answer,
    EvidenceContext,
    Holding,
    Method,
    RequirementStatement,
    SkillEvidence,
)
from careerwright.capability.matrix import Importance, RowEdit
from careerwright.capability.strength import StrengthChoice, StrengthDecision, StrengthRequest
from careerwright.db import Tx, is_unique_violation


@dataclass(frozen=True)
class CapabilityState:
    version: int  # 0: nothing recorded yet
    questions_stopped: bool
    updated_by: uuid.UUID | None
    updated_at: datetime | None


def state(tx: Tx, workspace_id: uuid.UUID) -> CapabilityState:
    row = (
        tx.execute(
            sa.text(
                "SELECT version, questions_stopped, updated_by, updated_at "
                "FROM careerwright.capability_states WHERE workspace_id = :ws"
            ),
            {"ws": workspace_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return CapabilityState(0, False, None, None)
    return CapabilityState(
        row["version"], row["questions_stopped"], row["updated_by"], row["updated_at"]
    )


def advance_state(
    tx: Tx, workspace_id: uuid.UUID, expected_version: int, *, stopped: bool, by: uuid.UUID
) -> bool:
    """Insert version 1, or move `expected_version` on by one; False if it is not current
    (the caller holds the workspace lock, so only a stale expectation fails)."""
    values = {"ws": workspace_id, "expected": expected_version, "stopped": stopped, "by": by}
    if expected_version == 0:
        inserted = tx.execute(
            sa.text(
                "INSERT INTO careerwright.capability_states (workspace_id, version, "
                "questions_stopped, "
                "updated_by) VALUES (:ws, 1, :stopped, :by) ON CONFLICT (workspace_id) DO NOTHING"
            ),
            values,
        )
        return inserted.rowcount == 1
    updated = tx.execute(
        sa.text(
            "UPDATE careerwright.capability_states SET version = version + 1, "
            "questions_stopped = :stopped, updated_by = :by, updated_at = clock_timestamp() "
            "WHERE workspace_id = :ws AND version = :expected"
        ),
        values,
    )
    return updated.rowcount == 1


_EVIDENCE_COLUMNS = (
    "evidence_id, subject, rubric_version, answer, self_assessed_level, example, last_done, "
    "context, independence, complexity, tools, ai_assisted, method, demonstrated_level, "
    "assessed_by, reviewed_on, outcome_id, recorded_by, recorded_at"
)


def insert_evidence(
    tx: Tx, workspace_id: uuid.UUID, state_version: int, evidence: SkillEvidence
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.skill_evidence (workspace_id, state_version, "
            f"{_EVIDENCE_COLUMNS}) "
            "VALUES (:ws, :version, :evidence_id, :subject, :rubric_version, :answer, "
            ":self_assessed_level, :example, :last_done, :context, :independence, :complexity, "
            ":tools, :ai_assisted, :method, :demonstrated_level, :assessed_by, :reviewed_on, "
            ":outcome_id, :recorded_by, :recorded_at)"
        ),
        {"ws": workspace_id, "version": state_version, **evidence.model_dump(mode="json")},
    )


def evidence(tx: Tx, workspace_id: uuid.UUID) -> list[SkillEvidence]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_EVIDENCE_COLUMNS} FROM careerwright.skill_evidence WHERE workspace_id = :ws "
            "ORDER BY recorded_at, evidence_id"
        ),
        {"ws": workspace_id},
    ).mappings()
    return [
        SkillEvidence(
            **{
                **row,
                "answer": Answer(row["answer"]),
                "method": Method(row["method"]),
                "context": EvidenceContext(row["context"]) if row["context"] else None,
            }
        )
        for row in rows
    ]


_STATEMENT_COLUMNS = (
    "statement_id, subject, holding, verified, verification_note, recorded_by, recorded_at"
)


def insert_statement(
    tx: Tx, workspace_id: uuid.UUID, state_version: int, statement: RequirementStatement
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.requirement_statements (workspace_id, state_version, "
            f"{_STATEMENT_COLUMNS}) VALUES (:ws, :version, :statement_id, :subject, :holding, "
            ":verified, :verification_note, :recorded_by, :recorded_at)"
        ),
        {"ws": workspace_id, "version": state_version, **statement.model_dump(mode="json")},
    )


def statements(tx: Tx, workspace_id: uuid.UUID) -> list[RequirementStatement]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_STATEMENT_COLUMNS} FROM careerwright.requirement_statements "
            "WHERE workspace_id = :ws ORDER BY recorded_at, statement_id"
        ),
        {"ws": workspace_id},
    ).mappings()
    return [RequirementStatement(**{**row, "holding": Holding(row["holding"])}) for row in rows]


_EDIT_COLUMNS = (
    "edit_id, row_id, action, importance, reason, warning_acknowledged, recorded_by, "
    "recorded_at, from_matrix_version, from_definition_version, to_matrix_version, "
    "to_definition_version"
)


def insert_edit(
    tx: Tx, workspace_id: uuid.UUID, state_version: int, target_key: str, edit: RowEdit
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.matrix_edits (workspace_id, state_version, target_key, "
            f"{_EDIT_COLUMNS}) VALUES (:ws, :version, :target, :edit_id, :row_id, :action, "
            ":importance, :reason, :warning_acknowledged, :recorded_by, :recorded_at, "
            ":from_matrix_version, :from_definition_version, :to_matrix_version, "
            ":to_definition_version)"
        ),
        {
            "ws": workspace_id,
            "version": state_version,
            "target": target_key,
            **edit.model_dump(mode="json"),
        },
    )


def edits(tx: Tx, workspace_id: uuid.UUID, target_key: str) -> list[RowEdit]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_EDIT_COLUMNS} FROM careerwright.matrix_edits WHERE workspace_id = :ws "
            "AND target_key = :target ORDER BY recorded_at, edit_id"
        ),
        {"ws": workspace_id, "target": target_key},
    ).mappings()
    return [
        RowEdit(
            **{
                **row,
                "importance": Importance(row["importance"]) if row["importance"] else None,
            }
        )
        for row in rows
    ]


def insert_strength(tx: Tx, request: StrengthRequest) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.strength_proposals (strength_id, workspace_id, turn_id, "
            "created_by, created_at) VALUES (:id, :ws, :turn, :by, :at)"
        ),
        {
            "id": request.strength_id,
            "ws": request.workspace_id,
            "turn": request.turn_id,
            "by": request.created_by,
            "at": request.created_at,
        },
    )


def strength_for_turn(
    tx: Tx, workspace_id: uuid.UUID, turn_id: uuid.UUID
) -> StrengthRequest | None:
    row = (
        tx.execute(
            sa.text(
                "SELECT strength_id, workspace_id, turn_id, created_by, created_at "
                "FROM careerwright.strength_proposals WHERE workspace_id = :ws AND turn_id = :turn"
            ),
            {"ws": workspace_id, "turn": turn_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else StrengthRequest(**dict(row))


def insert_strength_decision(tx: Tx, decided: StrengthDecision) -> bool:
    """False if the strength already has a decision (the first one stands)."""
    try:
        with tx.begin_nested():
            tx.execute(
                sa.text(
                    "INSERT INTO careerwright.strength_decisions (strength_id, workspace_id, "
                    "decision, evidence_id, decided_by, decided_at) VALUES (:id, :ws, :decision, "
                    ":evidence, :by, :at)"
                ),
                {
                    "id": decided.strength_id,
                    "ws": decided.workspace_id,
                    "decision": decided.decision.value,
                    "evidence": decided.evidence_id,
                    "by": decided.decided_by,
                    "at": decided.decided_at,
                },
            )
    except exc.IntegrityError as error:
        if is_unique_violation(error):
            return False
        raise
    return True


def strength_decision(tx: Tx, strength_id: uuid.UUID) -> StrengthDecision | None:
    row = (
        tx.execute(
            sa.text(
                "SELECT strength_id, workspace_id, decision, evidence_id, decided_by, decided_at "
                "FROM careerwright.strength_decisions WHERE strength_id = :id"
            ),
            {"id": strength_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    return StrengthDecision(**{**row, "decision": StrengthChoice(row["decision"])})
