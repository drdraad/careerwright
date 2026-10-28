"""Setup-only commands. They connect with the migration-owner roles, which runtime never uses.

- `setup-database`: migrate the application database, migrate DBOS's system database and
  grant its runtime role, then seed (idempotent; `make dev` and `make demo` run it).
- `migrate [--revision R]`: application database only (tests use it to stop part-way).
- `seed`: invited identities and the fixture workspace, created only if missing.
- `reset-demo`: recreate the named fixture workspace; no other workspace is touched.
"""

import argparse
import logging

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from dbos import DBOS

from nessa.config import OpsSettings
from nessa.db import Tx, create_engine
from nessa.identity import store as identity_store
from nessa.identity.records import EventKind
from nessa.logs import configure_logging
from nessa.profile import store as profile_store
from nessa.profile.commands import cited_sources
from nessa.profile.records import SourceKind
from nessa.seed import (
    FIXTURE_KEY,
    FIXTURE_OWNER,
    FIXTURE_SOURCE_ID,
    FIXTURE_WORKSPACE_ID,
    FIXTURE_WORKSPACE_NAME,
    INVITED_ACTORS,
    fixture_profile,
)
from nessa.vocabulary import DataMode

DBOS_RUNTIME_ROLE = "nessa_dbos_runtime"
_log = logging.getLogger("nessa.cli")


def migrate_app(engine: sa.Engine, revision: str = "head") -> None:
    config = Config()
    config.set_main_option("script_location", "nessa:migrations")
    with engine.begin() as conn:
        config.attributes["connection"] = conn
        command.upgrade(config, revision)


def migrate_dbos(settings: OpsSettings) -> None:
    database = settings.dbos_owner_database
    url = sa.make_url(database.url).set(password=database.password().get_secret_value())
    DBOS.migrate(url.render_as_string(hide_password=False), application_role=DBOS_RUNTIME_ROLE)


def _create_fixture_workspace(tx: Tx, settings: OpsSettings, *, last_event_seq: int) -> None:
    fixture = fixture_profile(settings.fixtures_dir)
    identity_store.insert_workspace(
        tx,
        workspace_id=FIXTURE_WORKSPACE_ID,
        owner_actor_id=FIXTURE_OWNER.actor_id,
        name=FIXTURE_WORKSPACE_NAME,
        data_mode=DataMode.DEMO,
        synthetic=True,
        fixture_key=FIXTURE_KEY,
        last_event_seq=last_event_seq,
    )
    profile_store.insert_source(
        tx,
        source_ref_id=FIXTURE_SOURCE_ID,
        workspace_id=FIXTURE_WORKSPACE_ID,
        kind=SourceKind.FIXTURE,
        label="Synthetic fixture persona P01 (supplied M0 pack)",
        locator=fixture.persona_locator,
        content_sha256=fixture.persona_sha256,
        observed_at=fixture.observed_at,
    )
    profile_store.insert_profile_version(tx, FIXTURE_WORKSPACE_ID, 1, fixture.document, None)
    profile_store.link_sources(tx, FIXTURE_WORKSPACE_ID, 1, cited_sources(fixture.document))
    created = EventKind.WORKSPACE_RESET if last_event_seq else EventKind.WORKSPACE_CREATED
    identity_store.append_event(tx, FIXTURE_WORKSPACE_ID, created, str(FIXTURE_WORKSPACE_ID))
    identity_store.append_event(
        tx, FIXTURE_WORKSPACE_ID, EventKind.PROFILE_VERSION_CREATED, "1", detail={"version": 1}
    )


def seed(engine: sa.Engine, settings: OpsSettings) -> None:
    with engine.begin() as tx:
        for actor in INVITED_ACTORS:
            identity_store.upsert_actor(tx, actor.actor_id, actor.email, actor.display_name)
        if identity_store.fixture_workspace(tx, FIXTURE_KEY) is None:
            _create_fixture_workspace(tx, settings, last_event_seq=0)


def reset_demo(engine: sa.Engine, settings: OpsSettings) -> None:
    with engine.begin() as tx:
        existing = identity_store.fixture_workspace(tx, FIXTURE_KEY)
        # Event numbers continue, so a client resuming from Last-Event-ID sees the reset.
        last_seq = existing[1] if existing else 0
        identity_store.delete_fixture_workspace(tx, FIXTURE_KEY)
        _create_fixture_workspace(tx, settings, last_event_seq=last_seq)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup-database")
    migrate = sub.add_parser("migrate")
    migrate.add_argument("--revision", default="head")
    sub.add_parser("seed")
    sub.add_parser("reset-demo")
    args = parser.parse_args(argv)

    configure_logging("setup")
    settings = OpsSettings()
    engine = create_engine(settings.migrator_database, application_name="nessa-setup", pool_size=1)
    try:
        match args.command:
            case "setup-database":
                migrate_app(engine)
                migrate_dbos(settings)
                seed(engine, settings)
            case "migrate":
                migrate_app(engine, args.revision)
            case "seed":
                seed(engine, settings)
            case "reset-demo":
                reset_demo(engine, settings)
        _log.info("setup command finished", extra={"command": args.command})
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
