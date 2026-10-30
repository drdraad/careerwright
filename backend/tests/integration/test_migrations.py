"""Migrations against real PostgreSQL 16: a fresh database reaches head; a populated database
at every earlier revision upgrades to head without losing data (plan Sprint 1 acceptance)."""

import json
import uuid
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from careerwright.cli import migrate_app, seed
from careerwright.identity import store as identity_store
from careerwright.identity.records import EventKind
from careerwright.profile import store as profile_store
from careerwright.profile.document import ProfileInput, apply_profile_input, empty_profile
from careerwright.profile.records import SourceKind
from careerwright.seed import INVITED_ACTORS
from careerwright.vocabulary import DataMode
from tests.support.infra import Infra, migrator_engine

pytestmark = pytest.mark.integration


def head() -> str:
    config = Config()
    config.set_main_option("script_location", "careerwright:migrations")
    revision = ScriptDirectory.from_config(config).get_current_head()
    assert revision is not None
    return revision


@pytest.mark.req("BND1-14")
def test_a_fresh_database_migrates_to_head_and_seeds(infra: Infra) -> None:
    database = f"careerwright_fresh_{uuid.uuid4().hex[:8]}"
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
        "SELECT (SELECT count(*) FROM careerwright.actors) AS actors, "
        "(SELECT count(*) FROM careerwright.workspaces) AS workspaces, "
        "(SELECT count(*) FROM careerwright.profile_versions) AS versions",
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
            f"SELECT (to_jsonb(t) - %s::text[])::text AS row FROM careerwright.{table} t "  # noqa: S608
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
            "INSERT INTO careerwright.command_receipts (actor_id, idempotency_key, command, "
            "request_sha256, status_code, response) VALUES (%(actor)s, %(key)s, 'cmd', "
            "repeat('a', 64), 200, %(response)s::jsonb)",
            {"actor": owner, "key": key, "response": json.dumps(response)},
        )


ATTRIBUTABLE = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
UNATTRIBUTABLE = uuid.UUID("00000000-0000-4000-8000-0000000000a2")


@pytest.mark.req("BND1-14")
def test_a_populated_database_upgrades_to_head_without_losing_data(infra: Infra) -> None:
    database = f"careerwright_upgrade_{uuid.uuid4().hex[:8]}"
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
            f"SELECT {RECEIPT_COLUMNS_0001} FROM careerwright.command_receipts "  # noqa: S608
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
        "SELECT count(*) AS n FROM careerwright.source_references "
        "WHERE run_id IS NOT NULL OR message_ids IS NOT NULL OR basis IS NOT NULL",
        database=database,
    ) == [{"n": 0}]
    # 0003: a receipt is kept and attributed to the workspace its response names; a retry
    # cache that names none is dropped (documented in the migration).
    receipts = infra.query(
        f"SELECT {RECEIPT_COLUMNS_0001}, workspace_id FROM careerwright.command_receipts",  # noqa: S608
        database=database,
    )
    assert receipts == [{**receipt_before[0], "workspace_id": edited}]
    [version] = infra.query("SELECT version_num FROM alembic_version", database=database)
    assert version["version_num"] == head()
    # The upgraded data is still reachable through row-level security, and only by its owner.
    count = "SELECT count(*) AS n FROM careerwright.profile_versions"
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


@pytest.mark.req("MODEL-08", "MODEL-04")
def test_an_untouched_old_default_run_limit_upgrades_to_the_new_default(infra: Infra) -> None:
    database = f"careerwright_limits_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0008")
        seed(engine, infra.ops_settings(database))
        with engine.begin() as tx:
            rows = {
                "untouched": (100_000_000, 1),  # the old built-in default, never edited
                "chosen": (100_000_000, 2),  # the person set $0.10 themselves
                "lower": (50_000_000, 1),  # created under another configured default
            }
            workspaces = {name: add_edited_workspace(tx) for name in rows}
            for name, (run_limit, version) in rows.items():
                tx.exec_driver_sql(
                    "INSERT INTO careerwright.spend_limits (workspace_id, run_limit_nano_usd, "
                    "period_limit_nano_usd, version) VALUES (%(ws)s, %(run)s, 1000000000, %(v)s)",
                    {"ws": workspaces[name], "run": run_limit, "v": version},
                )

        migrate_app(engine)
    finally:
        engine.dispose()

    limits = {
        name: infra.query(
            "SELECT run_limit_nano_usd AS run, period_limit_nano_usd AS period, version "
            "FROM careerwright.spend_limits WHERE workspace_id = %s",
            (workspace,),
            database=database,
        )[0]
        for name, workspace in workspaces.items()
    }
    assert limits == {
        "untouched": {"run": 150_000_000, "period": 1_000_000_000, "version": 1},
        "chosen": {"run": 100_000_000, "period": 1_000_000_000, "version": 2},
        "lower": {"run": 50_000_000, "period": 1_000_000_000, "version": 1},
    }


@pytest.mark.req("MODEL-08")
def test_attempts_that_made_no_call_upgrade_to_a_known_zero_cost(infra: Infra) -> None:
    database = f"careerwright_zero_cost_{uuid.uuid4().hex[:8]}"
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
                    "INSERT INTO careerwright.runs (run_id, workspace_id, data_mode, synthetic, "
                    "kind, "
                    "requested_by, model_id, model_mode, status) SELECT %(run)s, workspace_id, "
                    "data_mode, synthetic, 'connection_check', owner_actor_id, "
                    "'muse-spark-1.3-contributor', 'contributor', 'queued' "
                    "FROM careerwright.workspaces WHERE workspace_id = %(ws)s",
                    {"run": run, "ws": workspace},
                )
                tx.exec_driver_sql(
                    "INSERT INTO careerwright.model_attempts (run_id, workspace_id, model_id, "
                    "period_start, spend_state, cost_nano_usd, finished_at, outcome) VALUES "
                    "(%(run)s, %(ws)s, 'muse-spark-1.3-contributor', date '2026-10-01', "
                    "%(state)s, %(cost)s, clock_timestamp(), 'x')",
                    {"run": run, "ws": workspace, "state": state, "cost": cost},
                )

        migrate_app(engine)
    finally:
        engine.dispose()

    rows = infra.query(
        "SELECT spend_state, cost_nano_usd FROM careerwright.model_attempts ORDER BY spend_state",
        database=database,
    )
    # No call was made, so the cost is known: zero. Unknown stays unknown.
    assert rows == [
        {"spend_state": "none", "cost_nano_usd": 0},
        {"spend_state": "reconciled", "cost_nano_usd": 40_000},
        {"spend_state": "unknown", "cost_nano_usd": None},
    ]


@pytest.mark.req("ACQ-01")
def test_0014_leaves_only_http_urls_in_url_fields(infra: Infra) -> None:
    database = f"careerwright_urls_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    unsafe = "javascript:alert(1)"
    try:
        migrate_app(engine, "0013")
        seed(engine, infra.ops_settings(database))
        with engine.begin() as tx:
            workspace = add_edited_workspace(tx)
            run, attempt = uuid.uuid4(), uuid.uuid4()
            tx.exec_driver_sql(
                "INSERT INTO careerwright.runs (run_id, workspace_id, data_mode, synthetic, kind, "
                "requested_by, status, failure_class, finished_at) SELECT %(run)s, workspace_id, "
                "data_mode, synthetic, 'acquisition', owner_actor_id, 'failed', 'source_blocked', "
                "clock_timestamp() FROM careerwright.workspaces WHERE workspace_id = %(ws)s",
                {"run": run, "ws": workspace},
            )
            tx.exec_driver_sql(
                "INSERT INTO careerwright.acquisition_targets (run_id, workspace_id, position, "
                "route, "
                "url, status) VALUES (%(run)s, %(ws)s, 0, 'fetch', %(url)s, 'blocked')",
                {"run": run, "ws": workspace, "url": unsafe},
            )
            tx.exec_driver_sql(
                "INSERT INTO careerwright.source_attempts (attempt_id, workspace_id, run_id, "
                "position, "
                "route, provider, requested_url, redirects, status, reason, finished_at) VALUES "
                "(%(id)s, %(ws)s, %(run)s, 0, 'fetch', 'unknown', %(url)s, %(redirects)s::jsonb, "
                "'blocked', 'scheme_not_allowed', clock_timestamp())",
                {
                    "id": attempt,
                    "ws": workspace,
                    "run": run,
                    "url": unsafe,
                    "redirects": json.dumps(["https://ok.example/a", "file:///etc/passwd"]),
                },
            )

        migrate_app(engine)
    finally:
        engine.dispose()

    [target] = infra.query(
        "SELECT url, refusal FROM careerwright.acquisition_targets", database=database
    )
    [kept] = infra.query(
        "SELECT requested_url, redirects, status, reason FROM careerwright.source_attempts",
        database=database,
    )
    assert target == {"url": None, "refusal": "scheme_not_allowed"}
    assert kept == {
        "requested_url": None,
        "redirects": ["https://ok.example/a"],
        "status": "blocked",
        "reason": "scheme_not_allowed",
    }
