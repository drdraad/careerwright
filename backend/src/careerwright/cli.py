"""Setup-only commands. They connect with the migration-owner roles, which runtime never uses.

- `setup-database`: migrate the application database, migrate DBOS's system database and
  grant its runtime role, seed, then import the pinned ESCO release and the pinned reference
  datasets (ASHE, the SOC 2020 coding index, the AI evidence; ADR 0010) from the datasets
  directory where not imported yet (idempotent; `make dev` and `make demo` run it).
- `migrate [--revision R]`: application database only (tests use it to stop part-way).
- `seed`: invited identities and the five fixture workspaces, created only if missing.
- `reset-demo`: recreate the five named fixture workspaces; no other workspace is touched.
- `reseal`: master-key rotation step 2 (`make rotate-master-key` runs both steps):
  re-encrypt every sealed record (keys, run inputs, run outputs and partial replies) under
  the current key version.
"""

import argparse
import logging
import uuid
from collections.abc import Callable, Iterable
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from dbos import DBOS

from careerwright.capability.commands import committed_data, pack_targets
from careerwright.catalogue import reference_store, taxonomy_store
from careerwright.catalogue.esco import ESCO_RELEASE, parse_release
from careerwright.catalogue.reference import DATASETS, Dataset, import_dataset
from careerwright.catalogue.reference import is_held as is_reference_held
from careerwright.catalogue.releases import ReleasePin, read_verified
from careerwright.catalogue.taxonomy import import_release, is_held
from careerwright.config import OpsSettings
from careerwright.db import Tx, create_engine, url_with_password
from careerwright.evidence import store as evidence_store
from careerwright.evidence.acquisition import document_context
from careerwright.identity import credential_store, run_store
from careerwright.identity import store as identity_store
from careerwright.identity.credentials import credential_context
from careerwright.identity.keyring import Keyring, RecordContext, SealedValue, load_keyring
from careerwright.identity.records import EventKind
from careerwright.identity.runs import input_context, output_context, partial_context
from careerwright.logs import configure_logging
from careerwright.planning import store as planning_store
from careerwright.profile import store as profile_store
from careerwright.profile.commands import cited_sources
from careerwright.profile.records import SourceKind
from careerwright.profile.targets import record_targets
from careerwright.seed import (
    FIXTURE_OWNER,
    FIXTURE_PERSONAS,
    INVITED_ACTORS,
    FixturePersona,
    fixture_profile,
)
from careerwright.vocabulary import DataMode

DBOS_RUNTIME_ROLE = "careerwright_dbos_runtime"
_log = logging.getLogger("careerwright.cli")


def migrate_app(engine: sa.Engine, revision: str = "head") -> None:
    config = Config()
    config.set_main_option("script_location", "careerwright:migrations")
    with engine.begin() as conn:
        config.attributes["connection"] = conn
        command.upgrade(config, revision)


def migrate_dbos(settings: OpsSettings) -> None:
    DBOS.migrate(
        url_with_password(settings.dbos_owner_database), application_role=DBOS_RUNTIME_ROLE
    )


class ResealIncompleteError(RuntimeError):
    """A sealed table still holds an older key version: the old key file must be kept."""


def _reseal_rows(
    keyring: Keyring,
    rows: list[tuple[uuid.UUID, uuid.UUID, SealedValue]],
    context: Callable[[uuid.UUID, uuid.UUID], RecordContext],
    replace: Callable[[uuid.UUID, SealedValue], None],
) -> int:
    count = 0
    for record_id, workspace_id, sealed in rows:
        if sealed.key_version == keyring.current_version:
            continue
        record = context(workspace_id, record_id)
        replace(record_id, keyring.seal(keyring.open(sealed, record), record))
        count += 1
    return count


def _tables_on_old_versions(tx: Tx, current_version: int) -> list[str]:
    """Every application table with a `key_version` column, so a sealed table added later
    but missing from `reseal` blocks retirement instead of passing silently."""
    tables = tx.execute(
        sa.text(
            "SELECT table_name FROM information_schema.columns "
            "WHERE table_schema = 'careerwright' AND column_name = 'key_version' ORDER BY "
            "table_name"
        )
    ).scalars()
    stale = []
    for table in tables:
        old = tx.execute(
            sa.text(f"SELECT count(*) FROM careerwright.{table} WHERE key_version <> :v"),  # noqa: S608 - names from the catalogue
            {"v": current_version},
        ).scalar_one()
        if old:
            stale.append(f"careerwright.{table}")
    return stale


def reseal(engine: sa.Engine, keyring: Keyring) -> dict[str, int]:
    """Master-key rotation, step 2: re-encrypt everything the master key seals under its
    current version, in one transaction. Succeeds only when no sealed row is left on an
    older version; only then may older key files be retired."""
    with engine.begin() as tx:
        counts = {
            "credentials": _reseal_rows(
                keyring,
                credential_store.all_sealed(tx),
                credential_context,
                lambda record_id, sealed: credential_store.replace_sealed(tx, record_id, sealed),
            ),
            "run_inputs": _reseal_rows(
                keyring,
                run_store.all_sealed_inputs(tx),
                input_context,
                lambda record_id, sealed: run_store.replace_sealed_input(tx, record_id, sealed),
            ),
            "run_outputs": _reseal_rows(
                keyring,
                run_store.all_sealed_outputs(tx),
                output_context,
                lambda record_id, sealed: run_store.replace_sealed_output(tx, record_id, sealed),
            ),
            "run_partials": _reseal_rows(
                keyring,
                run_store.all_sealed_partials(tx),
                partial_context,
                lambda record_id, sealed: run_store.replace_sealed_partial(tx, record_id, sealed),
            ),
            "source_documents": _reseal_rows(
                keyring,
                evidence_store.all_sealed_documents(tx),
                document_context,
                lambda record_id, sealed: evidence_store.replace_sealed_document(
                    tx, record_id, sealed
                ),
            ),
        }
        stale = _tables_on_old_versions(tx, keyring.current_version)
        if stale:
            raise ResealIncompleteError(
                f"still sealed with an older master key: {', '.join(stale)}; keep the old key"
            )
    return counts


def _create_fixture_workspace(
    tx: Tx, settings: OpsSettings, persona: FixturePersona, *, last_event_seq: int
) -> None:
    fixture = fixture_profile(settings.fixtures_dir, persona)
    identity_store.insert_workspace(
        tx,
        workspace_id=persona.workspace_id,
        owner_actor_id=FIXTURE_OWNER.actor_id,
        name=persona.workspace_name,
        data_mode=DataMode.DEMO,
        synthetic=True,
        fixture_key=persona.key,
        last_event_seq=last_event_seq,
    )
    profile_store.insert_source(
        tx,
        source_ref_id=persona.source_id,
        workspace_id=persona.workspace_id,
        kind=SourceKind.FIXTURE,
        label=f"Synthetic fixture persona {persona.key.upper()} (supplied M0 pack)",
        locator=fixture.persona_locator,
        content_sha256=fixture.persona_sha256,
        observed_at=fixture.observed_at,
    )
    profile_store.insert_profile_version(tx, persona.workspace_id, 1, fixture.document, None)
    profile_store.link_sources(tx, persona.workspace_id, 1, cited_sources(fixture.document))
    created = EventKind.WORKSPACE_RESET if last_event_seq else EventKind.WORKSPACE_CREATED
    identity_store.append_event(tx, persona.workspace_id, created, str(persona.workspace_id))
    identity_store.append_event(
        tx, persona.workspace_id, EventKind.PROFILE_VERSION_CREATED, "1", detail={"version": 1}
    )


def _record_fixture_targets(tx: Tx, persona: FixturePersona) -> None:
    """Store each persona's target records against the held taxonomy and committed pack."""
    latest = profile_store.current_profile(tx, persona.workspace_id)
    if latest is not None:
        pack = pack_targets(committed_data())
        record_targets(tx, None, persona.workspace_id, latest.document, pack)


def _record_fixture_planning(tx: Tx, settings: OpsSettings, persona: FixturePersona) -> None:
    """Seed stated planning figures only if the persona has no planning version yet."""
    if planning_store.current_inputs(tx, persona.workspace_id) is not None:
        return
    fixture = fixture_profile(settings.fixtures_dir, persona)
    profile = profile_store.current_profile(tx, persona.workspace_id)
    if profile is None or profile.document != fixture.document:
        return  # an edited profile must not receive assumptions from the original persona
    inputs = fixture.planning_inputs
    if inputs is None:
        return
    planning_store.insert_inputs(tx, persona.workspace_id, 1, inputs, FIXTURE_OWNER.actor_id)
    identity_store.append_event(
        tx,
        persona.workspace_id,
        EventKind.PLANNING_INPUTS_UPDATED,
        str(persona.workspace_id),
        detail={"version": 1},
    )


def seed_fixture(engine: sa.Engine, settings: OpsSettings) -> None:
    """The invited actors and persona profiles. Idempotent, preserving edited workspaces."""
    with engine.begin() as tx:
        for actor in INVITED_ACTORS:
            identity_store.upsert_actor(tx, actor.actor_id, actor.email, actor.display_name)
        for persona in FIXTURE_PERSONAS:
            if identity_store.fixture_workspace(tx, persona.key) is None:
                _create_fixture_workspace(tx, settings, persona, last_event_seq=0)


def seed(engine: sa.Engine, settings: OpsSettings) -> None:
    """Seed persona profiles and their target records. Idempotent."""
    seed_fixture(engine, settings)
    with engine.begin() as tx:
        for persona in FIXTURE_PERSONAS:
            _record_fixture_targets(tx, persona)
            _record_fixture_planning(tx, settings, persona)


def import_taxonomy(engine: sa.Engine, path: Path, pin: ReleasePin = ESCO_RELEASE) -> str:
    """Import the pinned ESCO release at `path` unless it is imported already. The file is
    verified against the pin before it is parsed; a different release is refused."""
    with engine.begin() as tx:
        held = taxonomy_store.release(tx)
    if held is not None and is_held(held, pin):
        return "already imported"
    catalogue = parse_release(read_verified(path, pin), pin)
    with engine.begin() as tx:
        return import_release(tx, catalogue)


def import_reference_data(
    engine: sa.Engine, files: Iterable[tuple[Dataset, Path]]
) -> dict[str, str]:
    """Import each pinned reference dataset at its path unless it is held already, each in
    its own transaction, in `reference.DATASETS` order. Each file is verified against its
    pin before it is parsed; another release is refused."""
    outcomes: dict[str, str] = {}
    for dataset, path in files:
        with engine.begin() as tx:
            held = reference_store.held(tx, dataset.name)
        if held is not None and is_reference_held(held, dataset):
            outcomes[dataset.name] = "already imported"
            continue
        data = read_verified(path, dataset.pin)
        with engine.begin() as tx:
            outcomes[dataset.name] = import_dataset(tx, dataset, data)
    return outcomes


def reset_demo(engine: sa.Engine, settings: OpsSettings) -> None:
    with engine.begin() as tx:
        for persona in FIXTURE_PERSONAS:
            existing = identity_store.fixture_workspace(tx, persona.key)
            # Event numbers continue, so a client resuming from Last-Event-ID sees the reset.
            last_seq = existing[1] if existing else 0
            identity_store.delete_fixture_workspace(tx, persona.key)
            _create_fixture_workspace(tx, settings, persona, last_event_seq=last_seq)
            _record_fixture_targets(tx, persona)
            _record_fixture_planning(tx, settings, persona)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup-database")
    migrate = sub.add_parser("migrate")
    migrate.add_argument("--revision", default="head")
    sub.add_parser("seed")
    sub.add_parser("reset-demo")
    sub.add_parser("reseal")
    args = parser.parse_args(argv)

    configure_logging("setup")
    settings = OpsSettings()
    engine = create_engine(
        settings.migrator_database, application_name="careerwright-setup", pool_size=1
    )
    try:
        match args.command:
            case "setup-database":
                migrate_app(engine)
                migrate_dbos(settings)
                if settings.datasets_dir is None:
                    raise SystemExit("CAREERWRIGHT_DATASETS_DIR is required to import the taxonomy")
                outcome = import_taxonomy(engine, settings.datasets_dir / ESCO_RELEASE.file_name)
                _log.info(
                    "taxonomy", extra={"dataset": ESCO_RELEASE.dataset_id, "outcome": outcome}
                )
                directory = settings.datasets_dir
                imported = import_reference_data(
                    engine, ((d, directory / d.pin.file_name) for d in DATASETS)
                )
                _log.info("reference data", extra=imported)
                # After the taxonomy and the UK job-title index: the fixture's target is stored
                # with what it names in them.
                seed(engine, settings)
            case "migrate":
                migrate_app(engine, args.revision)
            case "seed":
                seed(engine, settings)
            case "reset-demo":
                reset_demo(engine, settings)
            case "reseal":
                if settings.master_key_dir is None:
                    raise SystemExit("CAREERWRIGHT_MASTER_KEY_DIR is required to reseal")
                keyring = load_keyring(settings.master_key_dir)
                counts = reseal(engine, keyring)
                _log.info(
                    "sealed records resealed",
                    extra={**counts, "current_key_version": keyring.current_version},
                )
        _log.info("setup command finished", extra={"command": args.command})
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
