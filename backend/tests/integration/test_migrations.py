"""Migrations against real PostgreSQL 16: a fresh database reaches head; a populated database
at every earlier revision upgrades to head without losing data (plan Sprint 1 acceptance)."""

import json
import uuid
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from nessa.cli import migrate_app, seed
from nessa.identity import store as identity_store
from nessa.identity.records import EventKind
from nessa.profile import store as profile_store
from nessa.profile.document import ProfileInput, apply_profile_input, empty_profile
from nessa.profile.records import SourceKind
from nessa.seed import INVITED_ACTORS
from nessa.vocabulary import DataMode
from tests.support.infra import Infra, migrator_engine

pytestmark = pytest.mark.integration


def head() -> str:
    config = Config()
    config.set_main_option("script_location", "nessa:migrations")
    revision = ScriptDirectory.from_config(config).get_current_head()
    assert revision is not None
    return revision


@pytest.mark.req("BND1-14")
def test_a_fresh_database_migrates_to_head_and_seeds(infra: Infra) -> None:
    database = f"nessa_fresh_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine)
        seed(engine, infra.ops_settings(database))
        seed(engine, infra.ops_settings(database))  # seeding twice changes nothing
    finally:
        engine.dispose()

    [version] = infra.query("SELECT version_num FROM alembic_version", database=database)
    assert version["version_num"] == head()
    counts = infra.query(
        "SELECT (SELECT count(*) FROM nessa.actors) AS actors, "
        "(SELECT count(*) FROM nessa.workspaces) AS workspaces, "
        "(SELECT count(*) FROM nessa.profile_versions) AS versions",
        database=database,
    )
    assert counts == [{"actors": 2, "workspaces": 1, "versions": 1}]


TABLES_0001 = (
    "actors",
    "workspaces",
    "source_references",
    "profile_versions",
    "profile_version_sources",
    "workspace_events",
)
RECEIPT_COLUMNS_0001 = "actor_id, idempotency_key, command, request_sha256, status_code, response"


# Columns later revisions add to 0001 tables (0005: a source's turn, messages and basis).
ADDED_SINCE_0001 = {"source_references": ["run_id", "message_ids", "basis"]}


def snapshot(infra: Infra, database: str) -> dict[str, list[dict[str, object]]]:
    """Every 0001 row with its 0001 columns, exactly."""
    return {
        table: infra.query(
            f"SELECT (to_jsonb(t) - %s::text[])::text AS row FROM nessa.{table} t "  # noqa: S608
            "ORDER BY 1",
            (ADDED_SINCE_0001.get(table, []),),
            database=database,
        )
        for table in TABLES_0001
    }


def add_receipts(tx: sa.Connection, workspace_id: uuid.UUID) -> None:
    """One receipt whose response names its workspace, and one retry cache that does not."""
    owner = INVITED_ACTORS[0].actor_id
    for key, response in (
        (ATTRIBUTABLE, {"workspace_id": str(workspace_id), "version": 2}),
        (UNATTRIBUTABLE, {"credential_id": str(uuid.uuid4())}),
    ):
        tx.exec_driver_sql(
            "INSERT INTO nessa.command_receipts (actor_id, idempotency_key, command, "
            "request_sha256, status_code, response) VALUES (%(actor)s, %(key)s, 'cmd', "
            "repeat('a', 64), 200, %(response)s::jsonb)",
            {"actor": owner, "key": key, "response": json.dumps(response)},
        )


ATTRIBUTABLE = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
UNATTRIBUTABLE = uuid.UUID("00000000-0000-4000-8000-0000000000a2")


@pytest.mark.req("BND1-14")
def test_a_populated_database_upgrades_to_head_without_losing_data(infra: Infra) -> None:
    database = f"nessa_upgrade_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0001")
        seed(engine, infra.ops_settings(database))  # the fixture workspace with its profile
        with engine.begin() as tx:
            edited = add_edited_workspace(tx)
            add_receipts(tx, edited)
        before = snapshot(infra, database)
        receipt_before = infra.query(
            f"SELECT {RECEIPT_COLUMNS_0001} FROM nessa.command_receipts "  # noqa: S608
            "WHERE idempotency_key = %s",
            (ATTRIBUTABLE,),
            database=database,
        )

        migrate_app(engine)
    finally:
        engine.dispose()

    assert snapshot(infra, database) == before
    # 0005's source columns are empty for every upgraded source: nothing is invented.
    assert infra.query(
        "SELECT count(*) AS n FROM nessa.source_references "
        "WHERE run_id IS NOT NULL OR message_ids IS NOT NULL OR basis IS NOT NULL",
        database=database,
    ) == [{"n": 0}]
    # 0003: a receipt is kept and attributed to the workspace its response names; a retry
    # cache that names none is dropped (documented in the migration).
    receipts = infra.query(
        f"SELECT {RECEIPT_COLUMNS_0001}, workspace_id FROM nessa.command_receipts",  # noqa: S608
        database=database,
    )
    assert receipts == [{**receipt_before[0], "workspace_id": edited}]
    [version] = infra.query("SELECT version_num FROM alembic_version", database=database)
    assert version["version_num"] == head()
    # The upgraded data is still reachable through row-level security, and only by its owner.
    count = "SELECT count(*) AS n FROM nessa.profile_versions"
    owner = infra.as_role("pg_api", count, actor=str(INVITED_ACTORS[0].actor_id), database=database)
    other = infra.as_role("pg_api", count, actor=str(INVITED_ACTORS[1].actor_id), database=database)
    assert (owner, other) == ([{"n": 3}], [{"n": 0}])


def add_edited_workspace(tx: sa.Connection) -> uuid.UUID:
    """A second workspace with two profile versions, written through the 0001-era stores."""
    owner = INVITED_ACTORS[0].actor_id
    workspace = identity_store.insert_workspace(
        tx,
        workspace_id=uuid.uuid4(),
        owner_actor_id=owner,
        name="Edited before the upgrade",
        data_mode=DataMode.LIVE_ASSISTED,
        synthetic=True,
    )
    now = datetime.now(UTC)
    document = empty_profile()
    for version, city in enumerate(("Leeds", "York"), start=1):
        source = uuid.uuid4()
        profile_store.insert_source(
            tx,
            source_ref_id=source,
            workspace_id=workspace.workspace_id,
            kind=SourceKind.DIRECT_ENTRY,
            label="Direct entry",
            recorded_by=owner,
            observed_at=now,
        )
        new = ProfileInput.model_validate(
            {
                **{name: {"state": "unasked"} for name in ProfileInput.model_fields},
                "cities": {"state": "provided", "value": [city]},
            }
        )
        document = apply_profile_input(document, new, source)
        profile_store.insert_profile_version(tx, workspace.workspace_id, version, document, owner)
        profile_store.link_sources(tx, workspace.workspace_id, version, [source])
        identity_store.append_event(
            tx, workspace.workspace_id, EventKind.PROFILE_VERSION_CREATED, str(version)
        )
    return workspace.workspace_id


@pytest.mark.req("MODEL-08")
def test_attempts_that_made_no_call_upgrade_to_a_known_zero_cost(infra: Infra) -> None:
    database = f"nessa_zero_cost_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0005")
        seed(engine, infra.ops_settings(database))
        with engine.begin() as tx:
            workspace = add_edited_workspace(tx)
            for state, cost in (("none", None), ("reconciled", 40_000), ("unknown", None)):
                run = uuid.uuid4()
                tx.exec_driver_sql(
                    "INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, "
                    "requested_by, model_id, model_mode, status) SELECT %(run)s, workspace_id, "
                    "data_mode, synthetic, 'connection_check', owner_actor_id, "
                    "'muse-spark-1.3-contributor', 'contributor', 'queued' "
                    "FROM nessa.workspaces WHERE workspace_id = %(ws)s",
                    {"run": run, "ws": workspace},
                )
                tx.exec_driver_sql(
                    "INSERT INTO nessa.model_attempts (run_id, workspace_id, model_id, "
                    "period_start, spend_state, cost_nano_usd, finished_at, outcome) VALUES "
                    "(%(run)s, %(ws)s, 'muse-spark-1.3-contributor', date '2026-10-01', "
                    "%(state)s, %(cost)s, clock_timestamp(), 'x')",
                    {"run": run, "ws": workspace, "state": state, "cost": cost},
                )

        migrate_app(engine)
    finally:
        engine.dispose()

    rows = infra.query(
        "SELECT spend_state, cost_nano_usd FROM nessa.model_attempts ORDER BY spend_state",
        database=database,
    )
    # No call was made, so the cost is known: zero. Unknown stays unknown.
    assert rows == [
        {"spend_state": "none", "cost_nano_usd": 0},
        {"spend_state": "reconciled", "cost_nano_usd": 40_000},
        {"spend_state": "unknown", "cost_nano_usd": None},
    ]
