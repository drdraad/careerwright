"""SQL for the person's planning input versions and for route solves (adapter; planning's only
SQL). Input versions, solves and results are append-only; an attempt's stage and end are
written once each as it runs."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from careerwright.db import Tx, is_unique_violation
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.identity.records import Run
from careerwright.planning.inputs import PlanningInputsDocument
from careerwright.planning.plan_records import PlanSnapshot
from careerwright.planning.search import M0SearchLimits, SearchResult
from careerwright.planning.solve_records import (
    AttemptOutcome,
    SolveAttempt,
    SolveRecord,
    SolveStage,
)

_COLUMNS = "workspace_id, version, document, created_by, created_at"
_LIMITS = (
    "max_actions",
    "max_starts_per_action",
    "max_selected_actions",
    "max_months",
    "wall_seconds",
    "max_states",
    "max_feasible_archive",
)
_SOLVE_COLUMNS = (
    "run_id, workspace_id, solve_id, target_title, inputs_version, capability_version, "
    "input_version, planning_start, horizon_months, objective_basis, rank_seconds, "
    f"algorithm_version, pruning_version, created_by, created_at, {', '.join(_LIMITS)}"
)
_ATTEMPT_COLUMNS = "attempt_id, stage, outcome, started_at, finished_at"


def plan(tx: Tx, workspace_id: uuid.UUID, version: int | None = None) -> PlanSnapshot | None:
    """Read a selected immutable version, or the latest selected version."""
    clause = "AND version = :version" if version is not None else "ORDER BY version DESC LIMIT 1"
    row = tx.execute(
        sa.text(
            f"SELECT snapshot FROM careerwright.plan_versions WHERE workspace_id = :ws {clause}"
        ),
        {"ws": workspace_id, "version": version},
    ).scalar_one_or_none()
    return None if row is None else PlanSnapshot.model_validate(row)


def plan_versions(tx: Tx, workspace_id: uuid.UUID) -> list[PlanSnapshot]:
    rows = tx.execute(
        sa.text(
            "SELECT snapshot FROM careerwright.plan_versions WHERE workspace_id = :ws "
            "ORDER BY version"
        ),
        {"ws": workspace_id},
    ).scalars()
    return [PlanSnapshot.model_validate(row) for row in rows]


def insert_plan(
    tx: Tx,
    snapshot: PlanSnapshot,
    *,
    created_by: uuid.UUID | None = None,
    created_at: datetime | None = None,
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.plan_versions (workspace_id, version, plan_id, "
            "solve_run_id, schedule_index, snapshot, created_by, created_at) "
            "VALUES (:ws, :version, :plan, :run, :index, CAST(:snapshot AS jsonb), :by, :at)"
        ),
        {
            "ws": snapshot.workspace_id,
            "version": snapshot.version,
            "plan": snapshot.plan_id,
            "run": snapshot.source.solve_run_id,
            "index": snapshot.source.schedule_index,
            "snapshot": json.dumps(snapshot.model_dump(mode="json")),
            "by": created_by or snapshot.selected_by,
            "at": created_at or snapshot.selected_at,
        },
    )


@dataclass(frozen=True)
class StoredInputs:
    workspace_id: uuid.UUID
    version: int
    document: PlanningInputsDocument
    created_by: uuid.UUID
    created_at: datetime


def stale_version(current: int) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.STALE_INPUT_VERSION,
        "Your planning inputs changed since you loaded them. Reload, then try again.",
        stage=ErrorStage.PLANNING,
        details={"current_version": current},
    )


def _stored(row: sa.RowMapping) -> StoredInputs:
    return StoredInputs(
        workspace_id=row["workspace_id"],
        version=row["version"],
        document=PlanningInputsDocument.model_validate(row["document"]),
        created_by=row["created_by"],
        created_at=row["created_at"],
    )


def current_inputs(tx: Tx, workspace_id: uuid.UUID) -> StoredInputs | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_COLUMNS} FROM careerwright.planning_input_versions "
                "WHERE workspace_id = :ws ORDER BY version DESC LIMIT 1"
            ),
            {"ws": workspace_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _stored(row)


def insert_inputs(
    tx: Tx,
    workspace_id: uuid.UUID,
    version: int,
    document: PlanningInputsDocument,
    created_by: uuid.UUID,
) -> StoredInputs:
    try:
        with tx.begin_nested():
            row = (
                tx.execute(
                    sa.text(
                        "INSERT INTO careerwright.planning_input_versions (workspace_id, "
                        "version, schema_version, document, created_by) VALUES (:ws, :version, "
                        f":schema, CAST(:document AS jsonb), :by) RETURNING {_COLUMNS}"
                    ),
                    {
                        "ws": workspace_id,
                        "version": version,
                        "schema": document.schema_version,
                        "document": document.model_dump_json(),
                        "by": created_by,
                    },
                )
                .mappings()
                .one()
            )
    except exc.IntegrityError as error:
        if is_unique_violation(error):
            raise stale_version(version) from None  # a concurrent writer took this number
        raise
    return _stored(row)


# Route solves (Task 13b).


def _solve(row: sa.RowMapping) -> SolveRecord:
    return SolveRecord(
        run_id=row["run_id"],
        workspace_id=row["workspace_id"],
        solve_id=row["solve_id"],
        target_title=row["target_title"],
        inputs_version=row["inputs_version"],
        capability_version=row["capability_version"],
        input_version=row["input_version"],
        planning_start=row["planning_start"],
        horizon_months=row["horizon_months"],
        objective_basis=row["objective_basis"],
        limits=M0SearchLimits(**{name: row[name] for name in _LIMITS}),
        rank_seconds=row["rank_seconds"],
        algorithm_version=row["algorithm_version"],
        pruning_version=row["pruning_version"],
        created_by=row["created_by"],
        created_at=row["created_at"],
    )


def insert_solve(tx: Tx, solve: SolveRecord) -> None:
    """API: the solve as asked for, in the transaction that records its run."""
    limits = solve.limits.model_dump()
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.route_solves (run_id, workspace_id, solve_id, "
            "target_title, inputs_version, capability_version, input_version, planning_start, "
            "horizon_months, objective_basis, rank_seconds, algorithm_version, pruning_version, "
            f"created_by, {', '.join(_LIMITS)}) VALUES (:run, :ws, :solve, :title, :inputs, "
            ":capability, :input, :start, :horizon, :basis, :rank, :algorithm, :pruning, :by, "
            f"{', '.join(f':{name}' for name in _LIMITS)})"
        ),
        {
            "run": solve.run_id,
            "ws": solve.workspace_id,
            "solve": solve.solve_id,
            "title": solve.target_title,
            "inputs": solve.inputs_version,
            "capability": solve.capability_version,
            "input": solve.input_version,
            "start": solve.planning_start,
            "horizon": solve.horizon_months,
            "basis": solve.objective_basis,
            "rank": solve.rank_seconds,
            "algorithm": solve.algorithm_version,
            "pruning": solve.pruning_version,
            "by": solve.created_by,
            **{name: limits[name] for name in _LIMITS},
        },
    )


def solve(tx: Tx, run_id: uuid.UUID) -> SolveRecord | None:
    row = (
        tx.execute(
            sa.text(f"SELECT {_SOLVE_COLUMNS} FROM careerwright.route_solves WHERE run_id = :run"),
            {"run": run_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _solve(row)


def unsettled_solve(tx: Tx, workspace_id: uuid.UUID, solve_id: str) -> uuid.UUID | None:
    """API: the run of the same solve still queued or running in this workspace, if any, that
    the person has not asked to cancel: a cancelled one ends without a result, however long
    its worker takes to say so."""
    value = tx.execute(
        sa.text(
            "SELECT s.run_id FROM careerwright.route_solves s JOIN careerwright.runs r "
            "ON r.run_id = s.run_id WHERE s.workspace_id = :ws AND s.solve_id = :solve "
            "AND r.status IN ('queued', 'running') AND NOT EXISTS (SELECT 1 FROM "
            "careerwright.run_cancellations c WHERE c.run_id = r.run_id) "
            "ORDER BY s.created_at LIMIT 1"
        ),
        {"ws": workspace_id, "solve": solve_id},
    ).scalar_one_or_none()
    return None if value is None else uuid.UUID(str(value))


def solve_attempts(tx: Tx, run_id: uuid.UUID) -> list[SolveAttempt]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_ATTEMPT_COLUMNS} FROM careerwright.route_solve_attempts "
            "WHERE run_id = :run ORDER BY attempt_id"
        ),
        {"run": run_id},
    ).mappings()
    return [
        SolveAttempt(
            attempt_id=row["attempt_id"],
            stage=SolveStage(row["stage"]),
            outcome=AttemptOutcome(row["outcome"]) if row["outcome"] else None,
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )
        for row in rows
    ]


def end_unfinished_solve_attempts(tx: Tx, run_id: uuid.UUID, outcome: AttemptOutcome) -> int:
    """Worker: the run's attempts never finished end as `outcome`, never as a result. An
    execution finds its predecessor's (a crash, or a store that went away) `interrupted`; a
    run's publication settles any left when the run ends."""
    updated = tx.execute(
        sa.text(
            "UPDATE careerwright.route_solve_attempts SET outcome = :outcome, "
            "finished_at = clock_timestamp() WHERE run_id = :run AND finished_at IS NULL"
        ),
        {"run": run_id, "outcome": outcome.value},
    )
    return int(updated.rowcount)


def insert_solve_attempt(tx: Tx, run: Run) -> int:
    return int(
        tx.execute(
            sa.text(
                "INSERT INTO careerwright.route_solve_attempts (run_id, workspace_id) "
                "VALUES (:run, :ws) RETURNING attempt_id"
            ),
            {"run": run.run_id, "ws": run.workspace_id},
        ).scalar_one()
    )


def set_solve_stage(tx: Tx, attempt_id: int, stage: SolveStage) -> None:
    tx.execute(
        sa.text(
            "UPDATE careerwright.route_solve_attempts SET stage = :stage "
            "WHERE attempt_id = :id AND finished_at IS NULL"
        ),
        {"id": attempt_id, "stage": stage.value},
    )


def finish_solve_attempt(tx: Tx, attempt_id: int, outcome: AttemptOutcome) -> None:
    tx.execute(
        sa.text(
            "UPDATE careerwright.route_solve_attempts SET outcome = :outcome, "
            "finished_at = clock_timestamp() WHERE attempt_id = :id AND finished_at IS NULL"
        ),
        {"id": attempt_id, "outcome": outcome.value},
    )


def insert_solve_result(
    tx: Tx, run: Run, attempt_id: int, output_id: uuid.UUID, result: SearchResult
) -> None:
    """Worker: the stored result's facts, beside its sealed output, once."""
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.route_solve_results (run_id, workspace_id, attempt_id, "
            "output_id, coverage, stop_reason, outcome, layers_exact, expanded_states, archived, "
            "unexplored_branches, search_ms, rank_ms) VALUES (:run, :ws, :attempt, :output, "
            ":coverage, :stop, :outcome, :exact, :states, :archived, :unexplored, :search, :rank)"
        ),
        {
            "run": run.run_id,
            "ws": run.workspace_id,
            "attempt": attempt_id,
            "output": output_id,
            "coverage": result.coverage.value,
            "stop": result.stop_reason.value if result.stop_reason is not None else None,
            "outcome": result.outcome.value,
            "exact": result.layers_exact,
            "states": result.expanded_states,
            "archived": len(result.schedules),
            "unexplored": result.unexplored_branches,
            "search": result.elapsed_ms,
            "rank": result.rank_ms,
        },
    )
