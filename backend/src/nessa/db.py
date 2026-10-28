"""SQLAlchemy engines and transactions scoped to an actor or a run, for row-level security.

Runtime roles are not table owners, so PostgreSQL row-level security applies to every
statement they run. A transaction sets `nessa.actor_id` (API) or `nessa.run_id` (worker)
with `set_config(..., is_local => true)`: the value lasts only until commit or rollback, so
a pooled connection never carries one request's identity into the next.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy import exc

from nessa.config import DatabaseConfig
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.logs import register_secret

Tx = sa.Connection
Engine = sa.Engine


class StoreUnavailableError(NessaError):
    def __init__(self) -> None:
        super().__init__(
            ErrorCode.STORE_UNAVAILABLE,
            "The database is unavailable or busy. Your work is kept; try again shortly.",
            stage=ErrorStage.INTERNAL,
            retryable=True,
        )


def url_with_password(config: DatabaseConfig) -> str:
    """For libraries that take a URL string (DBOS). The password is registered for redaction."""
    password = config.password().get_secret_value()
    register_secret(password)
    return sa.make_url(config.url).set(password=password).render_as_string(hide_password=False)


def create_engine(
    config: DatabaseConfig, *, application_name: str, pool_size: int = 5
) -> sa.Engine:
    password = config.password().get_secret_value()
    register_secret(password)
    url = sa.make_url(config.url).set(password=password)
    return sa.create_engine(
        url,
        pool_size=pool_size,
        max_overflow=pool_size,
        pool_pre_ping=True,
        connect_args={"application_name": application_name, "connect_timeout": 5},
    )


@contextmanager
def _transaction(engine: sa.Engine, setting: str | None, value: str | None) -> Iterator[Tx]:
    try:
        with engine.begin() as conn:
            if setting is not None:
                conn.execute(
                    sa.text("SELECT set_config(:setting, :value, true)"),
                    {"setting": setting, "value": value},
                )
            yield conn
    except (exc.OperationalError, exc.InterfaceError):
        # Connection loss, shutdown, deadlock or serialisation failure: retryable. The
        # driver's message can quote SQL parameters, so it is not chained.
        raise StoreUnavailableError() from None


@contextmanager
def actor_transaction(engine: sa.Engine, actor_id: uuid.UUID) -> Iterator[Tx]:
    with _transaction(engine, "nessa.actor_id", str(actor_id)) as conn:
        yield conn


@contextmanager
def run_transaction(engine: sa.Engine, run_id: uuid.UUID) -> Iterator[Tx]:
    with _transaction(engine, "nessa.run_id", str(run_id)) as conn:
        yield conn


@contextmanager
def system_transaction(engine: sa.Engine) -> Iterator[Tx]:
    """No actor or run: only what a role may see without one (the outbox, definer functions)."""
    with _transaction(engine, None, None) as conn:
        yield conn


def ping(engine: sa.Engine) -> None:
    """Raises StoreUnavailableError unless the database answers."""
    with system_transaction(engine) as tx:
        tx.execute(sa.text("SELECT 1"))


def is_unique_violation(error: exc.IntegrityError) -> bool:
    return getattr(error.orig, "sqlstate", None) == "23505"
