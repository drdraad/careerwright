"""Process configuration from the environment. Unsafe configuration fails closed at startup.

L0 runs only on one machine (ADR 0001): the environment must be explicitly `local`, Firebase
tokens come only from the Auth emulator of a `demo-` project, and every host and origin the
API accepts is loopback (or, for container-to-container traffic, a single-label Compose
service name, which never resolves on a public network). Passwords and keys are read from
files, never from variables or URLs.
"""

import ipaddress
import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "[::1]"})
_HOST_PORT = re.compile(r"^(?P<host>\[::1\]|[^:\[\]]+):(?P<port>[0-9]{1,5})$")
_SERVICE_NAME = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_ORIGIN = re.compile(r"^http://(?P<host>127\.0\.0\.1|localhost|\[::1\]):(?P<port>[0-9]{1,5})$")
_DEMO_PROJECT = re.compile(r"^demo-[a-z0-9-]{1,40}$")


class RuntimeMode(StrEnum):
    """`demo`: no service has a route out of the machine. `live`: the worker may reach Meta."""

    DEMO = "demo"
    LIVE = "live"


def is_local_host(value: str) -> bool:
    """`host:port` where host is a loopback name or a single-label service name."""
    match = _HOST_PORT.match(value)
    if match is None or not 0 < int(match.group("port")) < 65536:
        return False
    host = match.group("host")
    if host in LOOPBACK_HOSTS:
        return True
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return _SERVICE_NAME.match(host) is not None
    return False  # any other IP literal, including 0.0.0.0 and 127.0.0.2


def _split(value: object) -> object:
    if isinstance(value, str):
        return frozenset(part.strip() for part in value.split(",") if part.strip())
    return value


class DatabaseConfig(BaseModel):
    """A database URL without a password, plus the file that holds the password."""

    model_config = ConfigDict(frozen=True)

    url: str
    password_file: Path

    def password(self) -> SecretStr:
        return SecretStr(self.password_file.read_text(encoding="utf-8").strip())


def _passwordless(url: str) -> str:
    authority = url.split("://", 1)[-1].split("@", 1)
    if len(authority) == 2 and ":" in authority[0]:
        raise ValueError("database URLs must not embed a password; use the password file")
    return url


class _LocalSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    environment: Literal["local"] = Field(validation_alias="NESSA_ENVIRONMENT")
    runtime_mode: RuntimeMode = Field(validation_alias="NESSA_RUNTIME_MODE")


class _ModelSettings(BaseSettings):
    """Model choice is configuration (ruling R5, ADR 0003). `ModelChoice.configure` checks
    these IDs against the model registry when a process starts."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    meta_test_model: str = Field(
        default="muse-spark-1.3-contributor", validation_alias="NESSA_META_TEST_MODEL"
    )
    meta_production_model: str = Field(
        default="muse-spark-1.3", validation_alias="NESSA_META_PRODUCTION_MODEL"
    )
    # Which configured model a synthetic workspace's runs use. Non-synthetic workspaces always
    # use the production model.
    synthetic_model_role: Literal["test", "production"] = Field(
        default="test", validation_alias="NESSA_SYNTHETIC_MODEL_ROLE"
    )


class ApiSettings(_LocalSettings, _ModelSettings):
    allowed_hosts: Annotated[frozenset[str], NoDecode] = Field(
        validation_alias="NESSA_ALLOWED_HOSTS"
    )
    allowed_origins: Annotated[frozenset[str], NoDecode] = Field(
        validation_alias="NESSA_ALLOWED_ORIGINS"
    )
    firebase_project_id: str = Field(validation_alias="NESSA_FIREBASE_PROJECT_ID")
    # The variable firebase-admin itself reads; without it tokens would be checked against
    # Google's public keys, which L0 never contacts.
    auth_emulator_host: str = Field(validation_alias="FIREBASE_AUTH_EMULATOR_HOST")
    app_database_url: str = Field(validation_alias="NESSA_APP_DATABASE_URL")
    app_database_password_file: Path = Field(validation_alias="NESSA_APP_DATABASE_PASSWORD_FILE")
    master_key_dir: Path = Field(validation_alias="NESSA_MASTER_KEY_DIR")
    # Set only by the API container (compose.yaml): also serve clients on its own internal
    # Compose subnet, where the edge relay connects from. Unset, the API is loopback-only.
    internal_network_clients: bool = Field(
        default=False, validation_alias="NESSA_API_INTERNAL_NETWORK_CLIENTS"
    )
    default_run_spend_limit_nano_usd: int = Field(
        default=100_000_000, ge=0, validation_alias="NESSA_DEFAULT_RUN_SPEND_LIMIT_NANO_USD"
    )
    default_period_spend_limit_nano_usd: int = Field(
        default=1_000_000_000, ge=0, validation_alias="NESSA_DEFAULT_PERIOD_SPEND_LIMIT_NANO_USD"
    )

    _split_hosts = field_validator("allowed_hosts", "allowed_origins", mode="before")(_split)

    @field_validator("allowed_hosts")
    @classmethod
    def _hosts_are_local(cls, value: frozenset[str]) -> frozenset[str]:
        bad = sorted(host for host in value if not is_local_host(host))
        if bad or not value:
            raise ValueError(f"allowed hosts must be local host:port values, not {bad}")
        return value

    @field_validator("allowed_origins")
    @classmethod
    def _origins_are_loopback(cls, value: frozenset[str]) -> frozenset[str]:
        bad = sorted(origin for origin in value if _ORIGIN.match(origin) is None)
        if bad or not value:
            raise ValueError(f"allowed origins must be exact http loopback origins, not {bad}")
        return value

    @field_validator("firebase_project_id")
    @classmethod
    def _demo_project(cls, value: str) -> str:
        if _DEMO_PROJECT.match(value) is None:
            raise ValueError("the Firebase project must be a demo- project (emulator only)")
        return value

    @field_validator("auth_emulator_host")
    @classmethod
    def _emulator_is_local(cls, value: str) -> str:
        if not is_local_host(value):
            raise ValueError("the Auth emulator host must be a local host:port")
        return value

    _no_inline_password = field_validator("app_database_url")(_passwordless)

    @property
    def app_database(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.app_database_url, password_file=self.app_database_password_file
        )


class WorkerSettings(_LocalSettings, _ModelSettings):
    app_database_url: str = Field(validation_alias="NESSA_APP_DATABASE_URL")
    app_database_password_file: Path = Field(validation_alias="NESSA_APP_DATABASE_PASSWORD_FILE")
    dbos_database_url: str = Field(validation_alias="NESSA_DBOS_DATABASE_URL")
    dbos_database_password_file: Path = Field(validation_alias="NESSA_DBOS_DATABASE_PASSWORD_FILE")
    master_key_dir: Path = Field(validation_alias="NESSA_MASTER_KEY_DIR")

    _no_inline_password = field_validator("app_database_url", "dbos_database_url")(_passwordless)

    @property
    def app_database(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.app_database_url, password_file=self.app_database_password_file
        )

    @property
    def dbos_database(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.dbos_database_url, password_file=self.dbos_database_password_file
        )


class OpsSettings(BaseSettings):
    """Setup-only commands (migrate, seed, reset-demo, reseal) with the owner roles."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    environment: Literal["local"] = Field(validation_alias="NESSA_ENVIRONMENT")
    migrator_database_url: str = Field(validation_alias="NESSA_MIGRATOR_DATABASE_URL")
    migrator_database_password_file: Path = Field(
        validation_alias="NESSA_MIGRATOR_DATABASE_PASSWORD_FILE"
    )
    dbos_owner_database_url: str = Field(validation_alias="NESSA_DBOS_OWNER_DATABASE_URL")
    dbos_owner_database_password_file: Path = Field(
        validation_alias="NESSA_DBOS_OWNER_DATABASE_PASSWORD_FILE"
    )
    fixtures_dir: Path = Field(validation_alias="NESSA_FIXTURES_DIR")
    master_key_dir: Path | None = Field(default=None, validation_alias="NESSA_MASTER_KEY_DIR")

    _no_inline_password = field_validator("migrator_database_url", "dbos_owner_database_url")(
        _passwordless
    )

    @property
    def migrator_database(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.migrator_database_url, password_file=self.migrator_database_password_file
        )

    @property
    def dbos_owner_database(self) -> DatabaseConfig:
        return DatabaseConfig(
            url=self.dbos_owner_database_url, password_file=self.dbos_owner_database_password_file
        )
