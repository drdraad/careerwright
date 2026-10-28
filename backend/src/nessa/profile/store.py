"""SQL for profile versions and source references (adapter). Both tables are append-only."""

import uuid
from collections.abc import Iterable
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from nessa.db import Tx, is_unique_violation
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.profile.document import ProfileDocument
from nessa.profile.records import Basis, ProfileVersion, SourceKind, SourceReference

_SOURCE_COLUMNS = (
    "source_ref_id, workspace_id, kind, label, locator, content_sha256, recorded_by, "
    "observed_at, created_at, run_id, message_ids, basis"
)
_VERSION_COLUMNS = "workspace_id, version, document, created_by, created_at"


def stale_version(current: int) -> NessaError:
    return NessaError(
        ErrorCode.STALE_INPUT_VERSION,
        "The profile changed since you loaded it. Reload, then apply your edit again.",
        stage=ErrorStage.PROFILE,
        retryable=False,
        details={"current_version": current},
    )


def _version(row: sa.RowMapping) -> ProfileVersion:
    return ProfileVersion(
        workspace_id=row["workspace_id"],
        version=row["version"],
        document=ProfileDocument.model_validate(row["document"]),
        created_by=row["created_by"],
        created_at=row["created_at"],
    )


def _source(row: sa.RowMapping) -> SourceReference:
    return SourceReference(
        source_ref_id=row["source_ref_id"],
        workspace_id=row["workspace_id"],
        kind=SourceKind(row["kind"]),
        label=row["label"],
        locator=row["locator"],
        content_sha256=row["content_sha256"],
        recorded_by=row["recorded_by"],
        observed_at=row["observed_at"],
        created_at=row["created_at"],
        run_id=row["run_id"],
        message_ids=tuple(row["message_ids"] or ()),
        basis=Basis(row["basis"]) if row["basis"] else None,
    )


def insert_source(
    tx: Tx,
    *,
    source_ref_id: uuid.UUID,
    workspace_id: uuid.UUID,
    kind: SourceKind,
    label: str,
    observed_at: datetime,
    recorded_by: uuid.UUID | None = None,
    locator: str | None = None,
    content_sha256: str | None = None,
    run_id: uuid.UUID | None = None,
    message_ids: tuple[uuid.UUID, ...] = (),
    basis: Basis | None = None,
) -> None:
    # Only a conversation source names a turn, messages and a basis, and only it or an
    # occupation choice a run (CHECKs hold the others to NULL), so other kinds are written
    # without those columns.
    conversation = kind is SourceKind.CONVERSATION
    extra = ", run_id, message_ids, basis" if conversation else ""
    extra_values = ", :run, :messages, :basis" if conversation else ""
    if kind is SourceKind.OCCUPATION_CHOICE:
        extra, extra_values = ", run_id", ", :run"
    tx.execute(
        sa.text(
            "INSERT INTO nessa.source_references (source_ref_id, workspace_id, kind, label, "
            f"locator, content_sha256, recorded_by, observed_at{extra}) VALUES (:id, :ws, "
            f":kind, :label, :locator, :sha, :by, :observed{extra_values})"
        ),
        {
            "id": source_ref_id,
            "ws": workspace_id,
            "kind": kind.value,
            "label": label,
            "locator": locator,
            "sha": content_sha256,
            "by": recorded_by,
            "observed": observed_at,
            **(
                {
                    "run": run_id,
                    "messages": list(message_ids),
                    "basis": basis.value if basis else None,
                }
                if conversation
                else {"run": run_id}
                if kind is SourceKind.OCCUPATION_CHOICE
                else {}
            ),
        },
    )


def list_sources(
    tx: Tx, workspace_id: uuid.UUID, *, after: tuple[datetime, uuid.UUID] | None, limit: int
) -> list[SourceReference]:
    cursor = "AND (created_at, source_ref_id) > (:after_at, :after_id) " if after else ""
    rows = tx.execute(
        sa.text(
            f"SELECT {_SOURCE_COLUMNS} FROM nessa.source_references WHERE workspace_id = :ws "
            f"{cursor}ORDER BY created_at, source_ref_id LIMIT :limit"
        ),
        {
            "ws": workspace_id,
            "limit": limit,
            **({"after_at": after[0], "after_id": after[1]} if after else {}),
        },
    ).mappings()
    return [_source(row) for row in rows]


def current_profile(tx: Tx, workspace_id: uuid.UUID) -> ProfileVersion | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_VERSION_COLUMNS} FROM nessa.profile_versions WHERE workspace_id = :ws "
                "ORDER BY version DESC LIMIT 1"
            ),
            {"ws": workspace_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _version(row)


def profile_version(tx: Tx, workspace_id: uuid.UUID, version: int) -> ProfileVersion | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_VERSION_COLUMNS} FROM nessa.profile_versions "
                "WHERE workspace_id = :ws AND version = :version"
            ),
            {"ws": workspace_id, "version": version},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _version(row)


def list_profile_versions(
    tx: Tx, workspace_id: uuid.UUID, *, before: int | None, limit: int
) -> list[ProfileVersion]:
    cursor = "AND version < :before " if before is not None else ""
    rows = tx.execute(
        sa.text(
            f"SELECT {_VERSION_COLUMNS} FROM nessa.profile_versions WHERE workspace_id = :ws "
            f"{cursor}ORDER BY version DESC LIMIT :limit"
        ),
        {"ws": workspace_id, "limit": limit, **({"before": before} if before is not None else {})},
    ).mappings()
    return [_version(row) for row in rows]


def insert_profile_version(
    tx: Tx,
    workspace_id: uuid.UUID,
    version: int,
    document: ProfileDocument,
    created_by: uuid.UUID | None,
) -> ProfileVersion:
    try:
        with tx.begin_nested():
            row = (
                tx.execute(
                    sa.text(
                        "INSERT INTO nessa.profile_versions (workspace_id, version, "
                        "schema_version, document, created_by) VALUES (:ws, :version, :schema, "
                        f"CAST(:document AS jsonb), :by) RETURNING {_VERSION_COLUMNS}"
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
            # A concurrent writer took this version number first.
            raise stale_version(version) from None
        raise
    return _version(row)


def link_sources(
    tx: Tx, workspace_id: uuid.UUID, version: int, source_ids: Iterable[uuid.UUID]
) -> None:
    for source_id in sorted(set(source_ids)):
        tx.execute(
            sa.text(
                "INSERT INTO nessa.profile_version_sources (workspace_id, version, source_ref_id) "
                "VALUES (:ws, :version, :source)"
            ),
            {"ws": workspace_id, "version": version, "source": source_id},
        )
