"""Real PostgreSQL 16 and the Firebase Auth emulator for integration tests, in their own
Compose project (`nessa-l0-test`) on their own loopback ports. SQLite is not a substitute.

The test process plays the API and the worker (host processes, so failures can be injected);
`tests/stack` drives the containers themselves.
"""

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import psycopg
import sqlalchemy as sa
from psycopg import sql
from psycopg.rows import dict_row

from nessa.config import ApiSettings, OpsSettings, WorkerSettings
from tools.localenv import REPO_ROOT, ensure_local_home
from tools.stack import Ports, Stack

TEST_PROJECT = "nessa-l0-test"
TEST_PORTS = Ports(api=57000, auth=57099, postgres=57432, web=57300)
HOST = "127.0.0.1"
WEB_ORIGIN = f"http://{HOST}:{TEST_PORTS.web}"
API_BASE = f"http://{HOST}:{TEST_PORTS.api}"
PROJECT_ID = "demo-nessa"


@dataclass(frozen=True)
class Infra:
    stack: Stack
    home: Path

    def password(self, role: str) -> str:
        return (self.home / "secrets" / role).read_text().strip()

    def url(self, role: str, database: str) -> str:
        user = "postgres" if role == "pg_superuser" else f"nessa_{role.removeprefix('pg_')}"
        return f"postgresql://{user}:{self.password(role)}@{HOST}:{TEST_PORTS.postgres}/{database}"

    def env(self, database: str = "nessa_app") -> dict[str, str]:
        """Environment for settings objects: the same names the containers use."""
        secrets = self.home / "secrets"
        base = f"postgresql+psycopg://{{user}}@{HOST}:{TEST_PORTS.postgres}/{{db}}"
        return {
            "NESSA_ENVIRONMENT": "local",
            "NESSA_RUNTIME_MODE": "live",
            "NESSA_ALLOWED_HOSTS": f"{HOST}:{TEST_PORTS.api}",
            "NESSA_ALLOWED_ORIGINS": WEB_ORIGIN,
            "NESSA_FIREBASE_PROJECT_ID": PROJECT_ID,
            "FIREBASE_AUTH_EMULATOR_HOST": f"{HOST}:{TEST_PORTS.auth}",
            "NESSA_APP_DATABASE_URL": base.format(user="nessa_api", db=database),
            "NESSA_APP_DATABASE_PASSWORD_FILE": str(secrets / "pg_api"),
            "NESSA_MASTER_KEY_DIR": str(self.home / "keys"),
            "NESSA_MIGRATOR_DATABASE_URL": base.format(user="nessa_migrator", db=database),
            "NESSA_MIGRATOR_DATABASE_PASSWORD_FILE": str(secrets / "pg_migrator"),
            "NESSA_DBOS_OWNER_DATABASE_URL": base.format(user="nessa_dbos_owner", db="nessa_dbos"),
            "NESSA_DBOS_OWNER_DATABASE_PASSWORD_FILE": str(secrets / "pg_dbos_owner"),
            "NESSA_FIXTURES_DIR": str(REPO_ROOT / "fixtures" / "m0"),
        }

    def worker_env(self) -> dict[str, str]:
        secrets = self.home / "secrets"
        base = f"postgresql+psycopg://{{user}}@{HOST}:{TEST_PORTS.postgres}/{{db}}"
        return {
            **self.env(),
            "NESSA_APP_DATABASE_URL": base.format(user="nessa_worker", db="nessa_app"),
            "NESSA_APP_DATABASE_PASSWORD_FILE": str(secrets / "pg_worker"),
            "NESSA_DBOS_DATABASE_URL": base.format(user="nessa_dbos_runtime", db="nessa_dbos"),
            "NESSA_DBOS_DATABASE_PASSWORD_FILE": str(secrets / "pg_dbos_runtime"),
        }

    @contextmanager
    def settings_env(self, env: dict[str, str]) -> Iterator[None]:
        saved = {name: os.environ.get(name) for name in env}
        os.environ.update(env)
        try:
            yield
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def api_settings(self, database: str = "nessa_app") -> ApiSettings:
        with self.settings_env(self.env(database)):
            return ApiSettings(_env_file=None)

    def ops_settings(self, database: str = "nessa_app") -> OpsSettings:
        with self.settings_env(self.env(database)):
            return OpsSettings(_env_file=None)

    def worker_settings(self) -> WorkerSettings:
        with self.settings_env(self.worker_env()):
            return WorkerSettings(_env_file=None)

    def query(
        self, statement: str, params: tuple[object, ...] = (), *, database: str = "nessa_app"
    ) -> list[dict[str, object]]:
        """Inspect as the superuser (tests only; runtime never connects this way)."""
        with psycopg.connect(self.url("pg_superuser", database), row_factory=dict_row) as conn:
            cur = conn.execute(statement.encode(), params)
            return cur.fetchall() if cur.description else []

    def as_role(
        self,
        role: str,
        statement: str,
        params: tuple[object, ...] = (),
        *,
        actor: str | None = None,
        run: str | None = None,
    ) -> list[dict[str, object]]:
        """Run one statement as a runtime role with an optional actor/run context."""
        with psycopg.connect(self.url(role, "nessa_app"), row_factory=dict_row) as conn:
            if actor:
                conn.execute("SELECT set_config('nessa.actor_id', %s, true)", (actor,))
            if run:
                conn.execute("SELECT set_config('nessa.run_id', %s, true)", (run,))
            cur = conn.execute(statement.encode(), params)
            return cur.fetchall() if cur.description else []

    def create_database(self, name: str) -> None:
        with psycopg.connect(self.url("pg_superuser", "postgres"), autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
            )
            conn.execute(
                sql.SQL("CREATE DATABASE {} OWNER nessa_migrator").format(sql.Identifier(name))
            )
            conn.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO nessa_api, nessa_worker").format(
                    sql.Identifier(name)
                )
            )
        with psycopg.connect(self.url("pg_superuser", name), autocommit=True) as conn:
            conn.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")

    def database_cells(self, database: str) -> list[tuple[str, str]]:
        """Every row of every user table, as (schema.table, row JSON), for leak scanning."""
        tables = self.query(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE' "
            "AND table_schema NOT IN ('pg_catalog', 'information_schema')",
            database=database,
        )
        cells: list[tuple[str, str]] = []
        with psycopg.connect(self.url("pg_superuser", database), row_factory=dict_row) as conn:
            for table in tables:
                name = f"{table['table_schema']}.{table['table_name']}"
                rows = conn.execute(
                    sql.SQL("SELECT row_to_json(t)::text AS row FROM {}.{} t").format(
                        sql.Identifier(str(table["table_schema"])),
                        sql.Identifier(str(table["table_name"])),
                    )
                ).fetchall()
                cells.extend((name, str(row["row"])) for row in rows)
        return cells


def start_infra(home: Path) -> Infra:
    ensure_local_home(home)
    stack = Stack(project=TEST_PROJECT, home=home, ports=TEST_PORTS, live=False)
    stack.down()  # a previous interrupted run must not leak state into this one
    stack.build()
    stack.up("postgres", "auth", "edge")
    return Infra(stack=stack, home=home)


def migrator_engine(infra: Infra, database: str = "nessa_app") -> sa.Engine:
    return sa.create_engine(
        infra.url("pg_migrator", database).replace("postgresql://", "postgresql+psycopg://")
    )


# --- Auth emulator helpers -------------------------------------------------------------


def _emulator(path: str, body: dict[str, object], *, owner: bool = False) -> dict[str, object]:
    headers = {"Content-Type": "application/json"}
    if owner:
        headers["Authorization"] = "Bearer owner"
    request = urllib.request.Request(
        f"http://{HOST}:{TEST_PORTS.auth}{path}", data=json.dumps(body).encode(), headers=headers
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        result: dict[str, object] = json.loads(response.read())
        return result


def sign_in(email: str, password: str) -> str:
    """A fresh emulator ID token (the emulator accepts any API key)."""
    body = _emulator(
        "/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=emulator",
        {"email": email, "password": password, "returnSecureToken": True},
    )
    return str(body["idToken"])


def sign_in_seeded(handle: str) -> str:
    return sign_in(f"{handle}@nessa.test", f"nessa-demo-{handle}")


def create_emulator_user(uid: str, email: str, password: str, *, verified: bool = True) -> None:
    _emulator(
        f"/identitytoolkit.googleapis.com/v1/projects/{PROJECT_ID}/accounts",
        {"localId": uid, "email": email, "password": password, "emailVerified": verified},
        owner=True,
    )


def delete_emulator_user(uid: str) -> None:
    _emulator(
        f"/identitytoolkit.googleapis.com/v1/projects/{PROJECT_ID}/accounts:delete",
        {"localId": uid},
        owner=True,
    )


def revoke_tokens(uid: str) -> None:
    """What the Admin SDK's revoke_refresh_tokens does: move validSince to now. Tokens are
    revoked when issued strictly before it (second resolution), so wait out the current
    second first."""
    time.sleep(1.1)
    _emulator(
        f"/identitytoolkit.googleapis.com/v1/projects/{PROJECT_ID}/accounts:update",
        {"localId": uid, "validSince": str(int(time.time()))},
        owner=True,
    )


def emulator_reachable() -> bool:
    try:
        urllib.request.urlopen(f"http://{HOST}:{TEST_PORTS.auth}/", timeout=2).close()
    except (urllib.error.URLError, OSError):
        return False
    return True
