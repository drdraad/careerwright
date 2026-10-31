"""SQL for the person's planning input versions (adapter; planning's only SQL). Append-only."""

import uuid
from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from careerwright.db import Tx, is_unique_violation
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.planning.inputs import PlanningInputsDocument

_COLUMNS = "workspace_id, version, document, created_by, created_at"


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
