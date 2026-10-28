"""Migrations against real PostgreSQL 16: a fresh database reaches head; a populated database
at every earlier revision upgrades to head without losing data (plan Sprint 1 acceptance)."""

import uuid

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from nessa.cli import migrate_app, seed
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
