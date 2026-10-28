"""Session infrastructure for integration tests: real PostgreSQL 16, DBOS schema, emulator."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nessa.api.app import create_app
from nessa.api.deps import ApiDependencies
from nessa.cli import import_taxonomy, migrate_app, migrate_dbos, seed
from nessa.db import create_engine
from nessa.identity.firebase import FirebaseTokenVerifier
from nessa.identity.keyring import load_keyring
from nessa.identity.model_choice import ModelChoice
from tests.support.client import ApiClient
from tests.support.esco import SAMPLE_PATH, SAMPLE_RELEASE
from tests.support.infra import API_BASE, Infra, sign_in_seeded, start_infra

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def infra(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Infra]:
    home = Path(tmp_path_factory.mktemp("nessa-home"))
    started = start_infra(home)
    try:
        settings = started.ops_settings()
        engine = create_engine(settings.migrator_database, application_name="test-setup")
        try:
            migrate_app(engine)
            migrate_dbos(settings)
            seed(engine, settings)
            # The committed, labelled sample: the full release is imported in its own
            # database by `test_taxonomy.py::test_the_full_pinned_release_imports_...`.
            import_taxonomy(engine, SAMPLE_PATH, SAMPLE_RELEASE)
        finally:
            engine.dispose()
        # firebase-admin reads this variable at call time (validated by ApiSettings).
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = started.env()["FIREBASE_AUTH_EMULATOR_HOST"]
        yield started
    finally:
        started.stack.down()


@pytest.fixture(scope="session")
def api_deps(infra: Infra) -> Iterator[ApiDependencies]:
    settings = infra.api_settings()
    engine = create_engine(settings.app_database, application_name="test-api")
    yield ApiDependencies(
        settings=settings,
        engine=engine,
        verifier=FirebaseTokenVerifier(settings.firebase_project_id),
        keyring=load_keyring(settings.master_key_dir),
        models=ModelChoice.configure(
            settings.meta_test_model, settings.meta_production_model, settings.synthetic_model_role
        ),
    )
    engine.dispose()


@pytest.fixture(scope="session")
def api(api_deps: ApiDependencies) -> Iterator[ApiClient]:
    with TestClient(
        create_app(api_deps),
        base_url=API_BASE,
        raise_server_exceptions=False,
        client=("127.0.0.1", 57001),
    ) as client:
        yield ApiClient(client)


@pytest.fixture(scope="session")
def ada(infra: Infra) -> str:
    return sign_in_seeded("ada")


@pytest.fixture(scope="session")
def ben(infra: Infra) -> str:
    return sign_in_seeded("ben")
