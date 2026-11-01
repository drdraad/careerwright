"""SQL for sealed credentials and spend limits (adapter).

The API role can insert a sealed credential and revoke one but cannot select its nonce or
ciphertext; only the worker (scoped to an authorised run) and the setup-only reseal command
read sealed material.
"""

import uuid
from datetime import datetime

import sqlalchemy as sa

from careerwright.db import Tx
from careerwright.identity.keyring import SealedValue
from careerwright.identity.records import Credential
from careerwright.identity.spend import SpendLimits

_META_COLUMNS = (
    "credential_id, workspace_id, provider, key_version, consented_at, created_by, created_at, "
    "revoked_at, replaced_by"
)


def _credential(row: sa.RowMapping) -> Credential:
    return Credential(
        credential_id=row["credential_id"],
        workspace_id=row["workspace_id"],
        provider=row["provider"],
        key_version=row["key_version"],
        consented_at=row["consented_at"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        revoked_at=row["revoked_at"],
        replaced_by=row["replaced_by"],
    )


def insert_credential(
    tx: Tx,
    *,
    credential_id: uuid.UUID,
    workspace_id: uuid.UUID,
    sealed: SealedValue,
    consented_at: datetime,
    created_by: uuid.UUID,
) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.credentials (credential_id, workspace_id, provider, "
            "key_version, "
            "nonce, ciphertext, consented_at, created_by) VALUES (:id, :ws, 'meta', :version, "
            ":nonce, :ciphertext, :consented, :by)"
        ),
        {
            "id": credential_id,
            "ws": workspace_id,
            "version": sealed.key_version,
            "nonce": sealed.nonce,
            "ciphertext": sealed.ciphertext,
            "consented": consented_at,
            "by": created_by,
        },
    )


def credentials(tx: Tx, workspace_id: uuid.UUID) -> list[Credential]:
    rows = tx.execute(
        sa.text(
            f"SELECT {_META_COLUMNS} FROM careerwright.credentials WHERE workspace_id = :ws "
            "ORDER BY created_at, credential_id"
        ),
        {"ws": workspace_id},
    ).mappings()
    return [_credential(row) for row in rows]


def credential(tx: Tx, workspace_id: uuid.UUID, credential_id: uuid.UUID) -> Credential | None:
    row = (
        tx.execute(
            sa.text(
                f"SELECT {_META_COLUMNS} FROM careerwright.credentials "
                "WHERE workspace_id = :ws AND credential_id = :id"
            ),
            {"ws": workspace_id, "id": credential_id},
        )
        .mappings()
        .one_or_none()
    )
    return None if row is None else _credential(row)


def revoke(tx: Tx, credential_id: uuid.UUID, *, revoked_by: uuid.UUID) -> None:
    tx.execute(
        sa.text(
            "UPDATE careerwright.credentials SET revoked_at = clock_timestamp(), revoked_by = :by "
            "WHERE credential_id = :id AND revoked_at IS NULL"
        ),
        {"id": credential_id, "by": revoked_by},
    )


def set_replaced_by(tx: Tx, credential_id: uuid.UUID, replacement_id: uuid.UUID) -> None:
    tx.execute(
        sa.text("UPDATE careerwright.credentials SET replaced_by = :new WHERE credential_id = :id"),
        {"id": credential_id, "new": replacement_id},
    )


def sealed_active_credential(
    tx: Tx, workspace_id: uuid.UUID
) -> tuple[uuid.UUID, SealedValue] | None:
    """Worker only: the workspace's active Meta key, sealed. Revoked keys are never returned."""
    row = tx.execute(
        sa.text(
            "SELECT credential_id, key_version, nonce, ciphertext FROM careerwright.credentials "
            "WHERE workspace_id = :ws AND provider = 'meta' AND revoked_at IS NULL"
        ),
        {"ws": workspace_id},
    ).one_or_none()
    if row is None:
        return None
    return row.credential_id, SealedValue(row.key_version, bytes(row.nonce), bytes(row.ciphertext))


def all_sealed(tx: Tx) -> list[tuple[uuid.UUID, uuid.UUID, SealedValue]]:
    """Setup only (master-key rotation): every credential, revoked ones included."""
    rows = tx.execute(
        sa.text(
            "SELECT credential_id, workspace_id, key_version, nonce, ciphertext "
            "FROM careerwright.credentials ORDER BY credential_id FOR UPDATE"
        )
    )
    return [
        (
            r.credential_id,
            r.workspace_id,
            SealedValue(r.key_version, bytes(r.nonce), bytes(r.ciphertext)),
        )
        for r in rows
    ]


def replace_sealed(tx: Tx, credential_id: uuid.UUID, sealed: SealedValue) -> None:
    tx.execute(
        sa.text(
            "UPDATE careerwright.credentials SET key_version = :version, nonce = :nonce, "
            "ciphertext = :ciphertext WHERE credential_id = :id"
        ),
        {
            "id": credential_id,
            "version": sealed.key_version,
            "nonce": sealed.nonce,
            "ciphertext": sealed.ciphertext,
        },
    )


def ensure_spend_limits(tx: Tx, workspace_id: uuid.UUID, defaults: SpendLimits) -> None:
    tx.execute(
        sa.text(
            "INSERT INTO careerwright.spend_limits (workspace_id, run_limit_nano_usd, "
            "period_limit_nano_usd) VALUES (:ws, :run, :period) ON CONFLICT DO NOTHING"
        ),
        {
            "ws": workspace_id,
            "run": defaults.run_limit_nano_usd,
            "period": defaults.period_limit_nano_usd,
        },
    )


def spend_limits(tx: Tx, workspace_id: uuid.UUID) -> tuple[SpendLimits, int] | None:
    row = tx.execute(
        sa.text(
            "SELECT run_limit_nano_usd, period_limit_nano_usd, version FROM "
            "careerwright.spend_limits "
            "WHERE workspace_id = :ws"
        ),
        {"ws": workspace_id},
    ).one_or_none()
    if row is None:
        return None
    return SpendLimits(row.run_limit_nano_usd, row.period_limit_nano_usd), row.version


def update_spend_limits(
    tx: Tx, workspace_id: uuid.UUID, expected_version: int, limits: SpendLimits
) -> bool:
    updated = tx.execute(
        sa.text(
            "UPDATE careerwright.spend_limits SET run_limit_nano_usd = :run, "
            "period_limit_nano_usd = :period, version = version + 1, "
            "updated_at = clock_timestamp() WHERE workspace_id = :ws AND version = :expected"
        ),
        {
            "ws": workspace_id,
            "expected": expected_version,
            "run": limits.run_limit_nano_usd,
            "period": limits.period_limit_nano_usd,
        },
    )
    return updated.rowcount == 1
