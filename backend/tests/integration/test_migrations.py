"""Migrations against real PostgreSQL 16: a fresh database reaches head; a populated database
at every earlier revision upgrades to head without losing data (plan Sprint 1 acceptance)."""

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
    "command_receipts",
)


def snapshot(infra: Infra, database: str) -> dict[str, list[dict[str, object]]]:
    return {
        table: infra.query(
            f"SELECT row_to_json(t)::text AS row FROM nessa.{table} t ORDER BY 1",  # noqa: S608
            database=database,
        )
        for table in TABLES_0001
    }


@pytest.mark.req("BND1-14")
def test_a_populated_database_upgrades_to_head_without_losing_data(infra: Infra) -> None:
    database = f"nessa_upgrade_{uuid.uuid4().hex[:8]}"
    infra.create_database(database)
    engine = migrator_engine(infra, database)
    try:
        migrate_app(engine, "0001")
        seed(engine, infra.ops_settings(database))  # the fixture workspace with its profile
        with engine.begin() as tx:
            add_edited_workspace(tx)
        before = snapshot(infra, database)

        migrate_app(engine)
    finally:
        engine.dispose()

    assert snapshot(infra, database) == before
    [version] = infra.query("SELECT version_num FROM alembic_version", database=database)
    assert version["version_num"] == head()
    # The upgraded data is still reachable through row-level security, and only by its owner.
    count = "SELECT count(*) AS n FROM nessa.profile_versions"
    owner = infra.as_role("pg_api", count, actor=str(INVITED_ACTORS[0].actor_id), database=database)
    other = infra.as_role("pg_api", count, actor=str(INVITED_ACTORS[1].actor_id), database=database)
    assert (owner, other) == ([{"n": 3}], [{"n": 0}])


def add_edited_workspace(tx: sa.Connection) -> None:
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
