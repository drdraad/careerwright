"""Lifecycle and inspection of the spike's PostgreSQL 16 container and worker processes.

Passwords are generated per run and handed to Docker and the workers through environment
variables; URLs that embed them are never printed. `stop()` removes the container and its
volume, which also destroys the sealed credentials stored during the run.
"""

import os
import secrets
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

COMPOSE_FILE = Path(__file__).with_name("compose.yaml")
BACKEND_DIR = Path(__file__).resolve().parents[2]
PORT = 55432


@dataclass(frozen=True)
class SpikeStack:
    superuser_url: str = field(repr=False)
    app_url: str = field(repr=False)
    dbos_url: str = field(repr=False)
    master_key_file: Path

    def superuser_url_for(self, database: str) -> str:
        return self.superuser_url.rsplit("/", 1)[0] + f"/{database}"


def _compose(*args: str, env: dict[str, str]) -> None:
    result = subprocess.run(  # noqa: S603 - fixed docker compose invocation, no shell
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],  # noqa: S607
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Passwords travel in the environment, so compose's stderr cannot contain them.
        raise RuntimeError(f"docker compose {args[0]} failed: {result.stderr.strip()}")


def _compose_env(passwords: dict[str, str]) -> dict[str, str]:
    return {**os.environ, **passwords, "NESSA_SPIKE_PG_PORT": str(PORT)}


def stop() -> None:
    # Compose interpolates the required password variables even for `down`.
    placeholders = {
        name: "unused"
        for name in (
            "NESSA_SPIKE_PG_SUPERUSER_PASSWORD",
            "NESSA_SPIKE_APP_PASSWORD",
            "NESSA_SPIKE_DBOS_PASSWORD",
        )
    }
    _compose("down", "--volumes", "--remove-orphans", env=_compose_env(placeholders))


def start(master_key_file: Path) -> SpikeStack:
    """Start a fresh PostgreSQL 16 (any previous spike volume is removed first)."""
    passwords = {
        "NESSA_SPIKE_PG_SUPERUSER_PASSWORD": secrets.token_urlsafe(24),
        "NESSA_SPIKE_APP_PASSWORD": secrets.token_urlsafe(24),
        "NESSA_SPIKE_DBOS_PASSWORD": secrets.token_urlsafe(24),
    }
    stop()
    _compose("up", "--detach", "--wait", env=_compose_env(passwords))
    master_key_file.write_bytes(secrets.token_bytes(32))
    master_key_file.chmod(0o600)
    host = f"127.0.0.1:{PORT}"
    return SpikeStack(
        superuser_url=(
            f"postgresql://postgres:{passwords['NESSA_SPIKE_PG_SUPERUSER_PASSWORD']}"
            f"@{host}/postgres"
        ),
        app_url=(
            f"postgresql://nessa_spike_app:{passwords['NESSA_SPIKE_APP_PASSWORD']}"
            f"@{host}/nessa_spike_app"
        ),
        dbos_url=(
            f"postgresql://nessa_spike_dbos:{passwords['NESSA_SPIKE_DBOS_PASSWORD']}"
            f"@{host}/nessa_spike_dbos"
        ),
        master_key_file=master_key_file,
    )


@dataclass
class Worker:
    process: subprocess.Popen[bytes]
    log_path: Path
    _log: IO[bytes] = field(repr=False)

    def kill(self) -> None:
        self.process.kill()
        self.process.wait(timeout=10)
        self._log.close()

    def stop(self) -> int:
        self.process.terminate()
        code = self.process.wait(timeout=30)
        self._log.close()
        return code

    def wait_exit(self, timeout_s: float) -> int:
        code = self.process.wait(timeout=timeout_s)
        self._log.close()
        return code


def start_worker(stack: SpikeStack, log_path: Path, **settings: str) -> Worker:
    env = {
        **os.environ,
        "NESSA_SPIKE_APP_URL": stack.app_url,
        "NESSA_SPIKE_DBOS_URL": stack.dbos_url,
        "NESSA_SPIKE_MASTER_KEY_FILE": str(stack.master_key_file),
        "PYDANTIC_AI_NO_BANNER": "1",
        **{f"NESSA_SPIKE_{name.upper()}": value for name, value in settings.items()},
    }
    log = log_path.open("ab")
    process = subprocess.Popen(
        [sys.executable, "-m", "spikes.durable.worker"],
        cwd=BACKEND_DIR,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    return Worker(process, log_path, log)


def wait_for(predicate: Callable[[], bool], *, timeout_s: float, what: str) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise TimeoutError(f"timed out after {timeout_s}s waiting for {what}")


@contextmanager
def _rows(conninfo: str) -> Iterator[psycopg.Cursor[dict[str, Any]]]:
    with psycopg.connect(conninfo, row_factory=dict_row) as conn, conn.cursor() as cur:
        yield cur


def query(conninfo: str, statement: str, params: tuple[object, ...] = ()) -> list[dict[str, Any]]:
    with _rows(conninfo) as cur:
        cur.execute(statement.encode(), params)
        return cur.fetchall()


def database_cells(conninfo: str) -> list[tuple[str, str]]:
    """Every row of every user table, as (schema.table, row JSON), for leak scanning."""
    with _rows(conninfo) as cur:
        cur.execute(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE' "
            "AND table_schema NOT IN ('pg_catalog', 'information_schema')"
        )
        tables = [(r["table_schema"], r["table_name"]) for r in cur.fetchall()]
        cells: list[tuple[str, str]] = []
        for schema, table in tables:
            cur.execute(
                sql.SQL("SELECT row_to_json(t)::text AS row FROM {}.{} t").format(
                    sql.Identifier(schema), sql.Identifier(table)
                )
            )
            cells.extend((f"{schema}.{table}", r["row"]) for r in cur.fetchall())
    return cells
