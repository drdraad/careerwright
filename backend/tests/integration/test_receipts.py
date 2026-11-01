"""Idempotency receipts hold response copies, so they belong to their workspace and are
removed with it (spec section 19 deletion; reset-demo leaves no copies behind)."""

import uuid
from pathlib import Path

import psycopg
import pytest

from careerwright.cli import import_reference_data, migrate_app, reset_demo, seed
from careerwright.identity.keyring import load_keyring
from careerwright.identity.runs import output_context
from careerwright.seed import FIXTURE_WORKSPACE_ID
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra, migrator_engine
from tests.support.reference_data import sample_files

pytestmark = pytest.mark.integration


def receipts_for(infra: Infra, workspace_id: object, database: str = "careerwright_app") -> int:
    rows = infra.query(
        "SELECT count(*) AS n FROM careerwright.command_receipts WHERE workspace_id = %s",
        (workspace_id,),
        database=database,
    )
    return int(rows[0]["n"])


def test_every_receipt_names_its_workspace_and_goes_when_the_workspace_goes(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    workspace_id = api.create_workspace(ada, "Receipts")["workspace_id"]
    api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        ada,
        {"expected_version": 0, "profile": profile_with(cities=["Leeds"])},
    )
    assert receipts_for(infra, workspace_id) == 2  # the create and the profile write
    assert infra.query(
        "SELECT count(*) AS n FROM careerwright.command_receipts WHERE workspace_id IS NULL"
    ) == [{"n": 0}]

    infra.query("DELETE FROM careerwright.workspaces WHERE workspace_id = %s", (workspace_id,))

    assert receipts_for(infra, workspace_id) == 0


def test_reset_demo_removes_the_fixture_workspaces_receipts(infra: Infra, tmp_path: Path) -> None:
    database = f"careerwright_receipts_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine)
        settings = infra.ops_settings(database)
        # As setup does: the UK job-title index before the seed decides the fixture's target.
        import_reference_data(engine, sample_files(tmp_path))
        seed(engine, settings)
        with engine.begin() as tx:
            tx.exec_driver_sql(
                "INSERT INTO careerwright.command_receipts (actor_id, idempotency_key, command, "
                "request_sha256, status_code, response, workspace_id) SELECT owner_actor_id, "
                "gen_random_uuid(), 'write_profile', repeat('a', 64), 201, '{}'::jsonb, "
                "workspace_id FROM careerwright.workspaces WHERE workspace_id = %(ws)s",
                {"ws": FIXTURE_WORKSPACE_ID},
            )
        assert receipts_for(infra, FIXTURE_WORKSPACE_ID, database) == 1

        reset_demo(engine, settings)
    finally:
        engine.dispose()

    assert receipts_for(infra, FIXTURE_WORKSPACE_ID, database) == 0


@pytest.mark.req("DUR-05")
def test_a_cancel_receipt_and_an_unfinished_run_never_show_its_model_output(
    api: ApiClient, ada: str, infra: Infra
) -> None:
    # Review B M1: a cancel landing after the output was accepted but before the run was
    # published. The receipt is kept in plaintext, so it must not carry the output.
    workspace = api.create_workspace(ada, "Cancelled check")["workspace_id"]
    run_id, output_id = uuid.uuid4(), uuid.uuid4()
    sentinel = f"model-output-{uuid.uuid4().hex}"
    infra.query(
        "INSERT INTO careerwright.runs (run_id, workspace_id, data_mode, synthetic, kind, "
        "requested_by, "
        "model_id, model_mode, status) SELECT %s, workspace_id, data_mode, synthetic, "
        "'connection_check', owner_actor_id, 'muse-spark-1.3-contributor', 'contributor', "
        "'running' FROM careerwright.workspaces WHERE workspace_id = %s",
        (run_id, workspace),
    )
    body = f'{{"suggested_title": "{sentinel}", "reason": "{sentinel}"}}'.encode()
    sealed = load_keyring(infra.home / "keys").seal(body, output_context(workspace, output_id))
    infra.query(
        "INSERT INTO careerwright.run_outputs (output_id, run_id, workspace_id, key_version, "
        "nonce, "
        "ciphertext, content_sha256) VALUES (%s, %s, %s, %s, %s, %s, repeat('0', 64))",
        (output_id, run_id, workspace, sealed.key_version, sealed.nonce, sealed.ciphertext),
    )

    shown = api.get(f"/v1/workspaces/{workspace}/runs/{run_id}", ada)
    cancelled = api.write("POST", f"/v1/workspaces/{workspace}/runs/{run_id}/cancel", ada)
    receipts = infra.query(
        "SELECT response::text AS response FROM careerwright.command_receipts WHERE command = "
        "'cancel_run' AND workspace_id = %s",
        (workspace,),
    )

    assert shown.json()["output"] is None  # not complete: its result is not shown
    assert cancelled.status_code == 202, cancelled.text
    assert cancelled.json()["output"] is None
    assert [sentinel in r["response"] for r in receipts] == [False]


RECEIPT_AS_ACTOR = (
    "INSERT INTO careerwright.command_receipts (actor_id, idempotency_key, command, "
    "request_sha256, "
    "status_code, response, workspace_id) VALUES (%s, gen_random_uuid(), 'write_profile', "
    "repeat('a', 64), 201, '{}'::jsonb, %s)"
)


@pytest.mark.req("SEC-01")
def test_the_api_role_cannot_file_a_receipt_under_another_actor_s_workspace(
    api: ApiClient, ada: str, ben: str, infra: Infra
) -> None:
    """N5: the policy's WITH CHECK, as `careerwright_api` with Ben's identity set. His own
    workspace is accepted (the grant exists), so the refusal of Ada's is the policy."""
    adas = api.create_workspace(ada, "Ada's")["workspace_id"]
    bens = api.create_workspace(ben, "Ben's")["workspace_id"]
    [ben_actor] = infra.query(
        "SELECT actor_id FROM careerwright.actors WHERE email = 'ben@careerwright.test'"
    )
    ben_id = str(ben_actor["actor_id"])

    infra.as_role("pg_api", RECEIPT_AS_ACTOR, (ben_id, bens), actor=ben_id)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"):
        infra.as_role("pg_api", RECEIPT_AS_ACTOR, (ben_id, adas), actor=ben_id)

    assert receipts_for(infra, adas) == 1  # only Ada's own create receipt
