"""Unsafe environment or host configuration fails closed at startup (S1.1, SEC-03, BND1-13)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from nessa.config import ApiSettings, RuntimeMode, is_local_host

BASE = {
    "NESSA_ENVIRONMENT": "local",
    "NESSA_RUNTIME_MODE": "live",
    "NESSA_ALLOWED_HOSTS": "127.0.0.1:58000,localhost:58000,api:8000",
    "NESSA_ALLOWED_ORIGINS": "http://127.0.0.1:53000,http://localhost:53000",
    "NESSA_FIREBASE_PROJECT_ID": "demo-nessa",
    "FIREBASE_AUTH_EMULATOR_HOST": "auth:9099",
    "NESSA_APP_DATABASE_URL": "postgresql+psycopg://nessa_api@postgres:5432/nessa_app",
    "NESSA_APP_DATABASE_PASSWORD_FILE": "/run/secrets/pg_api",
    "NESSA_MASTER_KEY_DIR": "/run/nessa/keys",
}


def settings(monkeypatch: pytest.MonkeyPatch, **overrides: str | None) -> ApiSettings:
    for name, value in {**BASE, **overrides}.items():
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    return ApiSettings(_env_file=None)


def test_valid_local_configuration_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    loaded = settings(monkeypatch)

    assert loaded.runtime_mode is RuntimeMode.LIVE
    assert loaded.allowed_hosts == frozenset({"127.0.0.1:58000", "localhost:58000", "api:8000"})
    assert loaded.master_key_dir == Path("/run/nessa/keys")


@pytest.mark.req("SEC-03")
@pytest.mark.parametrize("environment", [None, "production", "staging", "LOCAL "])
def test_anything_but_an_explicit_local_environment_is_refused(
    monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    with pytest.raises(ValidationError):
        settings(monkeypatch, NESSA_ENVIRONMENT=environment)


@pytest.mark.req("SEC-03")
@pytest.mark.parametrize("project", ["nessa-prod", "my-project", "demo"])
def test_a_firebase_project_that_could_be_real_is_refused(
    monkeypatch: pytest.MonkeyPatch, project: str
) -> None:
    with pytest.raises(ValidationError, match="demo-"):
        settings(monkeypatch, NESSA_FIREBASE_PROJECT_ID=project)


@pytest.mark.req("SEC-03")
def test_without_the_emulator_host_tokens_would_be_verified_against_google_so_it_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValidationError):
        settings(monkeypatch, FIREBASE_AUTH_EMULATOR_HOST=None)


@pytest.mark.req("SEC-03")
@pytest.mark.parametrize(
    "host", ["auth.example.com:9099", "192.168.1.20:9099", "0.0.0.0:9099", "auth", "10.0.0.2:9099"]
)
def test_a_non_local_emulator_host_is_refused(monkeypatch: pytest.MonkeyPatch, host: str) -> None:
    with pytest.raises(ValidationError, match="local"):
        settings(monkeypatch, FIREBASE_AUTH_EMULATOR_HOST=host)


@pytest.mark.req("BND1-13")
@pytest.mark.parametrize(
    "hosts", ["0.0.0.0:58000", "nessa.example.com:58000", "192.168.0.4:58000", "127.0.0.1"]
)
def test_allowed_hosts_must_be_loopback_or_internal_service_names_with_ports(
    monkeypatch: pytest.MonkeyPatch, hosts: str
) -> None:
    with pytest.raises(ValidationError, match="local"):
        settings(monkeypatch, NESSA_ALLOWED_HOSTS=hosts)


@pytest.mark.req("BND1-13")
@pytest.mark.parametrize(
    "origin",
    [
        "https://nessa.example.com",
        "http://192.168.0.4:53000",
        "http://web:3000",
        "http://127.0.0.1:53000/",
        "*",
        "null",
    ],
)
def test_allowed_origins_must_be_exact_loopback_http_origins(
    monkeypatch: pytest.MonkeyPatch, origin: str
) -> None:
    with pytest.raises(ValidationError, match="loopback"):
        settings(monkeypatch, NESSA_ALLOWED_ORIGINS=origin)


@pytest.mark.parametrize(
    ("value", "local"),
    [
        ("127.0.0.1:1", True),
        ("localhost:58000", True),
        ("[::1]:8000", True),
        ("api:8000", True),
        ("api", False),
        ("api.internal:8000", False),
        ("127.0.0.2:8000", False),
        ("0.0.0.0:8000", False),
        ("LOCALHOST:58000", False),
    ],
)
def test_is_local_host(value: str, local: bool) -> None:
    assert is_local_host(value) is local


def test_database_password_is_read_from_its_file_and_hidden_from_repr(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    password_file = tmp_path / "pg_api"
    password_file.write_text("s3cret-password\n")

    loaded = settings(monkeypatch, NESSA_APP_DATABASE_PASSWORD_FILE=str(password_file))

    password = loaded.app_database.password()
    assert password.get_secret_value() == "s3cret-password"
    assert "s3cret-password" not in repr(loaded)
    assert "s3cret-password" not in repr(loaded.app_database)


def test_a_database_url_that_embeds_a_password_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError, match="password file"):
        settings(
            monkeypatch,
            NESSA_APP_DATABASE_URL="postgresql+psycopg://nessa_api:inline@postgres:5432/nessa_app",
        )
