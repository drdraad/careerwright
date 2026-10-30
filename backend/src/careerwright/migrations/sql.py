"""Run a migration's SQL script as written (no bind-parameter or `%` processing)."""

from alembic import op


def run_script(script: str) -> None:
    # psycopg sends a parameterless execute with the simple query protocol, which accepts a
    # multi-statement script and leaves `%`, `:` and `$$` bodies untouched.
    op.get_bind().connection.driver_connection.execute(script)  # type: ignore[union-attr]
