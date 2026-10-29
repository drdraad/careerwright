"""The hash of a source as retrieved, beside the hash of what was kept (Task 7A fix round 1;
ADR 0009 decision 4).

Third parties' personal details (emails, telephone numbers, JSON-LD contacts) are removed
before a source is hashed for spans, parsed or sealed, so `content_sha256` is the hash of
what was kept. `retrieved_sha256` is the hash of the bytes as they arrived, kept for change
detection only. Rows recorded before this revision have none.

Forward-only (see `docs/runbook.md`).

Revision ID: 0015
"""

from nessa.migrations.sql import run_script

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.source_attempts
    ADD COLUMN retrieved_sha256 text CHECK (retrieved_sha256 ~ '^[0-9a-f]{64}$');
COMMENT ON COLUMN nessa.source_attempts.retrieved_sha256 IS
    'The hash of the bytes as retrieved (change detection). content_sha256 is the hash of '
    'what was kept, with third parties'' personal details removed.';
GRANT UPDATE (retrieved_sha256) ON nessa.source_attempts TO nessa_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
