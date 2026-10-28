"""The request guard and the error envelope at the HTTP boundary (fast: the real app with
stub dependencies; every request here is answered before any database work).

A-M4 non-HTTP scopes fail closed; A-M5 status-derived codes; A-M6 a 500 keeps its envelope
and correlation ID; A-M11 clients outside loopback and the internal network are refused."""

import logging
import os
from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from nessa.api.app import create_app
from nessa.api.deps import ApiDependencies
from nessa.config import ApiSettings
from nessa.identity.access import VerifiedIdentity, unauthenticated
from nessa.identity.keyring import KEY_BYTES, Keyring
from nessa.identity.model_choice import ModelChoice

HOST = "127.0.0.1:57000"
ENV = {
    "NESSA_ENVIRONMENT": "local",
    "NESSA_RUNTIME_MODE": "demo",
    "NESSA_ALLOWED_HOSTS": HOST,
    "NESSA_ALLOWED_ORIGINS": "http://127.0.0.1:57300",
    "NESSA_FIREBASE_PROJECT_ID": "demo-nessa",
    "FIREBASE_AUTH_EMULATOR_HOST": "127.0.0.1:57099",
    "NESSA_APP_DATABASE_URL": "postgresql+psycopg://nessa_api@127.0.0.1:1/nessa_app",
    "NESSA_APP_DATABASE_PASSWORD_FILE": "/nonexistent",
    "NESSA_MASTER_KEY_DIR": "/nonexistent",
}


class RefusingVerifier:
    def verify(self, token: str) -> VerifiedIdentity:
        raise unauthenticated()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    settings = ApiSettings(_env_file=None)
    built = create_app(
        ApiDependencies(
            settings=settings,
            engine=sa.create_engine("postgresql+psycopg://nobody@127.0.0.1:1/none"),
            verifier=RefusingVerifier(),
            keyring=Keyring({1: os.urandom(KEY_BYTES)}, current_version=1),
            models=ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test"),
        )
    )

    @built.get("/boom")
    def boom() -> None:
        raise RuntimeError("an unexpected bug that quotes sk-secret-material")

    return built


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(
        app, base_url=f"http://{HOST}", raise_server_exceptions=False, client=("127.0.0.1", 50001)
    ) as test_client:
        yield test_client


@pytest.mark.req("BND1-13")
@pytest.mark.parametrize("address", ["192.168.1.20", "10.1.2.3", "8.8.8.8", "testclient"])
def test_a_client_outside_loopback_and_the_internal_network_is_refused(
    app: FastAPI, address: str
) -> None:
    with TestClient(
        app, base_url=f"http://{HOST}", raise_server_exceptions=False, client=(address, 5000)
    ) as lan_client:
        response = lan_client.get("/healthz", headers={"Host": HOST})

    assert (response.status_code, response.json()["error"]["code"]) == (403, "CLIENT_NOT_ALLOWED")


def test_a_loopback_client_is_served(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_websocket_scopes_fail_closed(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as closed, client.websocket_connect("/v1/me"):
        pass

    assert closed.value.code == 1008


@pytest.mark.parametrize(
    ("method", "path", "status", "code"),
    [
        ("GET", "/no/such/route", 404, "NOT_FOUND"),
        ("DELETE", "/healthz", 405, "METHOD_NOT_ALLOWED"),
    ],
)
def test_framework_errors_carry_a_code_that_matches_their_status(
    client: TestClient, method: str, path: str, status: int, code: str
) -> None:
    response = client.request(method, path, headers={"Origin": "http://127.0.0.1:57300"})

    assert (response.status_code, response.json()["error"]["code"]) == (status, code)


def test_an_unexpected_error_keeps_the_envelope_correlation_id_and_real_status(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="nessa.api.access"):
        response = client.get("/boom")

    body = response.json()["error"]
    assert (response.status_code, body["code"]) == (500, "INTERNAL_ERROR")
    assert response.headers["x-correlation-id"] == body["correlation_id"]
    assert "sk-secret-material" not in response.text
    [access] = [r for r in caplog.records if r.name == "nessa.api.access"]
    assert access.status == 500  # type: ignore[attr-defined]
