"""SQL for profile versions and source references, both append-only, and for each target's
stored record (adapter)."""

import uuid
from collections.abc import Iterable
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import exc

from careerwright.db import Tx, is_unique_violation
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.profile.document import ProfileDocument
from careerwright.profile.records import (
    Basis,
    ProfileVersion,
    SourceKind,
    SourceReference,
    TargetCoverage,
    TargetKind,
    TargetLink,
    TargetRecord,
)

_SOURCE_COLUMNS = (
    "source_ref_id, workspace_id, kind, label, locator, content_sha256, recorded_by, "
    "observed_at, created_at, run_id, message_ids, basis"
)
_VERSION_COLUMNS = "workspace_id, version, document, created_by, created_at"


def stale_version(current: int) -> CareerwrightError:
    return CareerwrightError(
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
            "INSERT INTO careerwright.source_references (source_ref_id, workspace_id, kind, label, "
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
            f"SELECT {_SOURCE_COLUMNS} FROM careerwright.source_references WHERE workspace_id = "
            ":ws "
            f"{cursor}ORDER BY created_at, source_ref_id LIMIT :limit"
        ),
        {
            "ws": workspace_id,
            "limit": limit,
            **({"after_at": after[0], "after_id": after[1]} if after else {}),
        },
    ).mappings()
    return [_source(row) for row in rows]


def source(tx: Tx, workspace_id: uuid.UUID, source_ref_id: uuid.UUID) -> SourceReference | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_SOURCE_COLUMNS} FROM careerwright.source_references "
                "WHERE workspace_id = :ws AND source_ref_id = :id"
            ),
            {"ws": workspace_id, "id": source_ref_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _source(row)


def occupation_choices(tx: Tx, workspace_id: uuid.UUID) -> list[tuple[str, uuid.UUID]]:
    """The occupations the person chose from the taxonomy (as targets, or as their current or
    last role), each by its ESCO URI with the source citing it, oldest first."""
    rows = tx.execute(
        sa.text(
            "SELECT locator, source_ref_id FROM careerwright.source_references "
            "WHERE workspace_id = :ws AND kind = :kind AND locator IS NOT NULL "
            "ORDER BY created_at, source_ref_id"
        ),
        {"ws": workspace_id, "kind": SourceKind.OCCUPATION_CHOICE.value},
    )
    return [(row.locator, row.source_ref_id) for row in rows]


_TARGET_COLUMNS = (
    "title_key, title, kind, occupation_uri, link, label_matches, coverage, pack_target_id, "
    "pack_target_basis, pack_version, source_ref_id"
)


def _target(row: sa.RowMapping) -> TargetRecord:
    return TargetRecord(
        title=row["title"],
        key=row["title_key"],
        kind=TargetKind(row["kind"]),
        occupation_uri=row["occupation_uri"],
        link=TargetLink(row["link"]),
        label_matches=tuple(row["label_matches"]),
        coverage=TargetCoverage(row["coverage"]),
        pack_target_id=row["pack_target_id"],
        pack_target_basis=row["pack_target_basis"],
        pack_version=row["pack_version"],
        source_ref_id=row["source_ref_id"],
    )


def target_records(tx: Tx, workspace_id: uuid.UUID, keys: Iterable[str]) -> dict[str, TargetRecord]:
    """The workspace's stored targets with these concept keys, by key."""
    rows = tx.execute(
        sa.text(
            f"SELECT {_TARGET_COLUMNS} FROM careerwright.target_records "
            "WHERE workspace_id = :ws AND title_key = ANY(CAST(:keys AS text[]))"
        ),
        {"ws": workspace_id, "keys": sorted(set(keys))},
    ).mappings()
    return {row["title_key"]: _target(row) for row in rows}


def upsert_target_record(
    tx: Tx, workspace_id: uuid.UUID, record: TargetRecord, recorded_by: uuid.UUID | None
) -> None:
    """Store a target's record; a later record of the same title (as a concept) replaces it."""
    tx.execute(
        sa.text(
            f"INSERT INTO careerwright.target_records (workspace_id, {_TARGET_COLUMNS}, "
            "recorded_by) VALUES (:ws, :key, :title, :kind, :occupation, :link, "
            "CAST(:matches AS text[]), :coverage, :pack_target, :basis, :pack_version, "
            ":source, :by) "
            "ON CONFLICT (workspace_id, title_key) DO UPDATE SET title = EXCLUDED.title, "
            "kind = EXCLUDED.kind, occupation_uri = EXCLUDED.occupation_uri, "
            "link = EXCLUDED.link, label_matches = EXCLUDED.label_matches, "
            "coverage = EXCLUDED.coverage, pack_target_id = EXCLUDED.pack_target_id, "
            "pack_target_basis = EXCLUDED.pack_target_basis, "
            "pack_version = EXCLUDED.pack_version, source_ref_id = EXCLUDED.source_ref_id, "
            "recorded_by = EXCLUDED.recorded_by, recorded_at = clock_timestamp()"
        ),
        {
            "ws": workspace_id,
            "key": record.key,
            "title": record.title,
            "kind": record.kind.value,
            "occupation": record.occupation_uri,
            "link": record.link.value,
            "matches": list(record.label_matches),
            "coverage": record.coverage.value,
            "pack_target": record.pack_target_id,
            "basis": record.pack_target_basis,
            "pack_version": record.pack_version,
            "source": record.source_ref_id,
            "by": recorded_by,
        },
    )


def current_profile(tx: Tx, workspace_id: uuid.UUID) -> ProfileVersion | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_VERSION_COLUMNS} FROM careerwright.profile_versions WHERE workspace_id "
                "= :ws "
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
                f"SELECT {_VERSION_COLUMNS} FROM careerwright.profile_versions "
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
            f"SELECT {_VERSION_COLUMNS} FROM careerwright.profile_versions WHERE workspace_id = "
            ":ws "
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
                        "INSERT INTO careerwright.profile_versions (workspace_id, version, "
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
                "INSERT INTO careerwright.profile_version_sources (workspace_id, version, "
                "source_ref_id) "
                "VALUES (:ws, :version, :source)"
            ),
            {"ws": workspace_id, "version": version, "source": source_id},
        )
