"""Keep multiple checked options of the same kind from one source page.

Revision ID: 0051
"""

from careerwright.migrations.sql import run_script

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.researched_option_records
    ADD COLUMN record_position smallint NOT NULL DEFAULT 0 CHECK (record_position >= 0);
ALTER TABLE careerwright.researched_option_records
    DROP CONSTRAINT researched_option_records_attempt_id_record_kind_key;
ALTER TABLE careerwright.researched_option_records
    ADD CONSTRAINT researched_option_record_slot
    UNIQUE (attempt_id, record_kind, record_position);
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
