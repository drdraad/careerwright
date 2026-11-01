"""Production entry point: `uvicorn --factory careerwright.api.main:build_app`. Fails closed on any
unsafe configuration, a missing master key or an unreachable database password file."""

from fastapi import FastAPI

from careerwright.api.app import create_app
from careerwright.api.deps import ApiDependencies
from careerwright.config import ApiSettings
from careerwright.db import create_engine
from careerwright.identity.firebase import FirebaseTokenVerifier
from careerwright.identity.keyring import load_keyring
from careerwright.identity.model_choice import ModelChoice
from careerwright.localnet import client_networks
from careerwright.logs import configure_logging


def build_app() -> FastAPI:
    configure_logging("api")
    settings = ApiSettings()
    return create_app(
        ApiDependencies(
            settings=settings,
            engine=create_engine(settings.app_database, application_name="careerwright-api"),
            verifier=FirebaseTokenVerifier(settings.firebase_project_id),
            keyring=load_keyring(settings.master_key_dir),
            models=ModelChoice.configure(
                settings.meta_test_model,
                settings.meta_production_model,
                settings.synthetic_model_role,
            ),
            client_networks=client_networks(internal=settings.internal_network_clients),
        )
    )
