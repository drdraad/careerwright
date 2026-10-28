"""Alembic environment. Migrations run only as the migration owner, from `nessa.cli`.

The connection arrives through `config.attributes["connection"]`, already inside one
transaction, so an upgrade applies completely or not at all, and no URL (or password) is ever
written to an ini file or printed.
"""

from alembic import context

context.configure(connection=context.config.attributes["connection"])
with context.begin_transaction():
    context.run_migrations()
