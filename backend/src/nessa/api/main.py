"""Production entry point: `uvicorn --factory nessa.api.main:build_app`. Fails closed on any
unsafe configuration, a missing master key or an unreachable database password file."""

from fastapi import FastAPI

from nessa.api.app import create_app
from nessa.api.deps import ApiDependencies
from nessa.config import ApiSettings
from nessa.db import create_engine
from nessa.identity.firebase import FirebaseTokenVerifier
from nessa.identity.keyring import load_keyring
from nessa.logs import configure_logging


def build_app() -> FastAPI:
    configure_logging("api")
    settings = ApiSettings()
    return create_app(
        ApiDependencies(
            settings=settings,
            engine=create_engine(settings.app_database, application_name="nessa-api"),
            verifier=FirebaseTokenVerifier(settings.firebase_project_id),
            keyring=load_keyring(settings.master_key_dir),
        )
    )
