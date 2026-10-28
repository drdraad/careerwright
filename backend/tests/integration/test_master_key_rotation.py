"""Master-key rotation (MODEL-05): add a key version, reseal everything the master key seals,
retire the old version. Runs on its own database so the session's records are untouched."""

import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa

from nessa.cli import ResealIncompleteError, migrate_app, reseal, seed
from nessa.identity import credential_store
from nessa.identity.credentials import credential_context
from nessa.identity.keyring import Keyring, MasterKeyError, SealedValue, load_keyring
from nessa.identity.runs import input_context, output_context
from nessa.seed import FIXTURE_OWNER
from tests.support.infra import Infra, migrator_engine
from tools.localenv import add_master_key_version, ensure_local_home

pytestmark = pytest.mark.integration


def add_workspace(tx: sa.Connection) -> uuid.UUID:
    workspace: uuid.UUID = tx.exec_driver_sql(
        "INSERT INTO nessa.workspaces (workspace_id, owner_actor_id, name, data_mode, "
        "synthetic) VALUES (gen_random_uuid(), %(owner)s, 'Rotation', 'live_assisted', "
        "true) RETURNING workspace_id",
        {"owner": FIXTURE_OWNER.actor_id},
    ).scalar_one()
    return workspace


def add_sealed_output(
    tx: sa.Connection, keyring: Keyring, workspace: uuid.UUID, text: str
) -> uuid.UUID:
    run_id, output_id = uuid.uuid4(), uuid.uuid4()
    tx.exec_driver_sql(
        "INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, requested_by, "
        "model_id, model_mode, status) VALUES (%(run)s, %(ws)s, 'live_assisted', true, "
        "'connection_check', %(owner)s, 'muse-spark-1.3-contributor', 'contributor', 'running')",
        {"run": run_id, "ws": workspace, "owner": FIXTURE_OWNER.actor_id},
    )
    sealed = keyring.seal(text.encode(), output_context(workspace, output_id))
    tx.exec_driver_sql(
        "INSERT INTO nessa.run_outputs (output_id, run_id, workspace_id, key_version, nonce, "
        "ciphertext, content_sha256) VALUES (%(out)s, %(run)s, %(ws)s, %(v)s, %(n)s, %(c)s, "
        "repeat('0', 64))",
        {
            "out": output_id,
            "run": run_id,
            "ws": workspace,
            "v": sealed.key_version,
            "n": sealed.nonce,
            "c": sealed.ciphertext,
        },
    )
    return output_id


def add_sealed_input(
    tx: sa.Connection, keyring: Keyring, workspace: uuid.UUID, text: str
) -> uuid.UUID:
    run_id = uuid.uuid4()
    tx.exec_driver_sql(
        "INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, requested_by, "
        "model_id, model_mode, status, profile_version) VALUES (%(run)s, %(ws)s, "
        "'live_assisted', true, 'interview_turn', %(owner)s, 'muse-spark-1.3-contributor', "
        "'contributor', 'queued', 0)",
        {"run": run_id, "ws": workspace, "owner": FIXTURE_OWNER.actor_id},
    )
    sealed = keyring.seal(text.encode(), input_context(workspace, run_id))
    tx.exec_driver_sql(
        "INSERT INTO nessa.run_inputs (run_id, workspace_id, key_version, nonce, ciphertext) "
        "VALUES (%(run)s, %(ws)s, %(v)s, %(n)s, %(c)s)",
        {
            "run": run_id,
            "ws": workspace,
            "v": sealed.key_version,
            "n": sealed.nonce,
            "c": sealed.ciphertext,
        },
    )
    return run_id


@pytest.fixture
def rotation(infra: Infra, tmp_path: Path) -> tuple[Infra, str, Path]:
    database = f"nessa_rotation_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    home = tmp_path / "home"
    ensure_local_home(home)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine)
        seed(engine, infra.ops_settings(database))
    finally:
        engine.dispose()
    return infra, database, home


@pytest.mark.req("MODEL-05")
def test_resealing_moves_every_sealed_record_to_the_new_master_key_version(
    rotation: tuple[Infra, str, Path],
) -> None:
    infra, database, home = rotation
    engine = migrator_engine(infra, database)
    keys: dict[uuid.UUID, str] = {}
    outputs: dict[uuid.UUID, str] = {}
    try:
        old = load_keyring(home / "keys")
        with engine.begin() as tx:
            workspace = add_workspace(tx)
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
                keys[credential_id] = key
            for text in ('{"suggested_title": "A", "reason": "B"}', '{"x": 1}'):
                outputs[add_sealed_output(tx, old, workspace, text)] = text
            inputs = {add_sealed_input(tx, old, workspace, '{"messages": []}'): '{"messages": []}'}

        add_master_key_version(home)
        resealed = reseal(engine, load_keyring(home / "keys"))
        again = reseal(engine, load_keyring(home / "keys"))
    finally:
        engine.dispose()

    assert resealed == {"credentials": 2, "run_inputs": 1, "run_outputs": 2}
    assert again == {"credentials": 0, "run_inputs": 0, "run_outputs": 0}
    # Retire version 1: the new key alone opens every sealed record.
    (home / "keys" / "v1.key").unlink()
    only_new = load_keyring(home / "keys")
    for row in infra.query(
        "SELECT credential_id, workspace_id, key_version, nonce, ciphertext FROM nessa.credentials",
        database=database,
    ):
        assert row["key_version"] == 2
        sealed = SealedValue(2, bytes(row["nonce"]), bytes(row["ciphertext"]))
        context = credential_context(row["workspace_id"], row["credential_id"])
        assert only_new.open(sealed, context).decode() == keys[row["credential_id"]]
    for row in infra.query(
        "SELECT output_id, workspace_id, key_version, nonce, ciphertext FROM nessa.run_outputs",
        database=database,
    ):
        assert row["key_version"] == 2
        sealed = SealedValue(2, bytes(row["nonce"]), bytes(row["ciphertext"]))
        context = output_context(row["workspace_id"], row["output_id"])
        assert only_new.open(sealed, context).decode() == outputs[row["output_id"]]
    for row in infra.query(
        "SELECT run_id, workspace_id, key_version, nonce, ciphertext FROM nessa.run_inputs",
        database=database,
    ):
        assert row["key_version"] == 2
        sealed = SealedValue(2, bytes(row["nonce"]), bytes(row["ciphertext"]))
        opened = only_new.open(sealed, input_context(row["workspace_id"], row["run_id"]))
        assert opened.decode() == inputs[row["run_id"]]
    with pytest.raises(MasterKeyError, match="version 1"):
        only_new.open(SealedValue(1, b"\0" * 12, b"\0" * 32), context)


@pytest.mark.req("MODEL-05")
def test_reseal_refuses_to_report_success_while_any_sealed_table_holds_an_old_version(
    rotation: tuple[Infra, str, Path],
) -> None:
    """A sealed table added later but forgotten by the reseal command must stop the old key
    being retired, not pass silently."""
    infra, database, home = rotation
    engine = migrator_engine(infra, database)
    try:
        with engine.begin() as tx:
            tx.exec_driver_sql("CREATE TABLE nessa.future_sealed (key_version integer NOT NULL)")
            tx.exec_driver_sql("INSERT INTO nessa.future_sealed VALUES (1)")
        add_master_key_version(home)
        with pytest.raises(ResealIncompleteError, match="future_sealed"):
            reseal(engine, load_keyring(home / "keys"))
    finally:
        engine.dispose()
