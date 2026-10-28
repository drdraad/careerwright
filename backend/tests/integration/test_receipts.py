"""Idempotency receipts hold response copies, so they belong to their workspace and are
removed with it (spec section 19 deletion; reset-demo leaves no copies behind)."""

import uuid

import pytest

from nessa.cli import migrate_app, reset_demo, seed
from nessa.seed import FIXTURE_WORKSPACE_ID
from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra, migrator_engine

pytestmark = pytest.mark.integration


def receipts_for(infra: Infra, workspace_id: object, database: str = "nessa_app") -> int:
    rows = infra.query(
        "SELECT count(*) AS n FROM nessa.command_receipts WHERE workspace_id = %s",
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
        "SELECT count(*) AS n FROM nessa.command_receipts WHERE workspace_id IS NULL"
    ) == [{"n": 0}]

    infra.query("DELETE FROM nessa.workspaces WHERE workspace_id = %s", (workspace_id,))

    assert receipts_for(infra, workspace_id) == 0


def test_reset_demo_removes_the_fixture_workspaces_receipts(infra: Infra) -> None:
    database = f"nessa_receipts_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine)
        settings = infra.ops_settings(database)
        seed(engine, settings)
        with engine.begin() as tx:
            tx.exec_driver_sql(
                "INSERT INTO nessa.command_receipts (actor_id, idempotency_key, command, "
                "request_sha256, status_code, response, workspace_id) SELECT owner_actor_id, "
                "gen_random_uuid(), 'write_profile', repeat('a', 64), 201, '{}'::jsonb, "
                "workspace_id FROM nessa.workspaces WHERE workspace_id = %(ws)s",
                {"ws": FIXTURE_WORKSPACE_ID},
            )
        assert receipts_for(infra, FIXTURE_WORKSPACE_ID, database) == 1

        reset_demo(engine, settings)
    finally:
        engine.dispose()

    assert receipts_for(infra, FIXTURE_WORKSPACE_ID, database) == 0
