"""Master-key rotation (MODEL-05): add a key version, reseal, retire the old version.
Runs on its own database so the session's stored credentials are untouched."""

import secrets
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nessa.cli import migrate_app, reseal_credentials, seed
from nessa.identity import credential_store
from nessa.identity.credentials import credential_context
from nessa.identity.keyring import MasterKeyError, SealedValue, load_keyring
from nessa.seed import FIXTURE_OWNER
from tests.support.infra import Infra, migrator_engine
from tools.localenv import add_master_key_version, ensure_local_home

pytestmark = pytest.mark.integration


@pytest.mark.req("MODEL-05")
def test_resealing_moves_every_key_to_the_new_master_key_version(
    infra: Infra, tmp_path: Path
) -> None:
    database = f"nessa_rotation_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    home = tmp_path / "home"
    ensure_local_home(home)
    engine = migrator_engine(infra, database)
    plaintexts: dict[uuid.UUID, str] = {}
    try:
        migrate_app(engine)
        seed(engine, infra.ops_settings(database))
        old = load_keyring(home / "keys")
        with engine.begin() as tx:
            workspace = tx.exec_driver_sql(
                "INSERT INTO nessa.workspaces (workspace_id, owner_actor_id, name, data_mode, "
                "synthetic) VALUES (gen_random_uuid(), %(owner)s, 'Rotation', 'live_assisted', "
                "true) RETURNING workspace_id",
                {"owner": FIXTURE_OWNER.actor_id},
            ).scalar_one()
            for _ in range(2):
                credential_id, key = uuid.uuid4(), secrets.token_urlsafe(32)
                credential_store.insert_credential(
                    tx,
                    credential_id=credential_id,
                    workspace_id=workspace,
                    sealed=old.seal(key.encode(), credential_context(workspace, credential_id)),
                    consented_at=datetime.now(UTC),
                    created_by=FIXTURE_OWNER.actor_id,
                )
                credential_store.revoke(tx, credential_id, revoked_by=FIXTURE_OWNER.actor_id)
                plaintexts[credential_id] = key

        add_master_key_version(home)
        resealed = reseal_credentials(engine, load_keyring(home / "keys"))
        again = reseal_credentials(engine, load_keyring(home / "keys"))
    finally:
        engine.dispose()

    assert (resealed, again) == (2, 0)
    # Retire version 1: the new key alone opens every credential.
    (home / "keys" / "v1.key").unlink()
    only_new = load_keyring(home / "keys")
    rows = infra.query(
        "SELECT credential_id, workspace_id, key_version, nonce, ciphertext FROM nessa.credentials",
        database=database,
    )
    assert {row["key_version"] for row in rows} == {2}
    for row in rows:
        sealed = SealedValue(2, bytes(row["nonce"]), bytes(row["ciphertext"]))
        context = credential_context(row["workspace_id"], row["credential_id"])
        assert only_new.open(sealed, context).decode() == plaintexts[row["credential_id"]]
    with pytest.raises(MasterKeyError, match="version 1"):
        only_new.open(SealedValue(1, b"\0" * 12, b"\0" * 32), context)
    shutil.rmtree(home)
