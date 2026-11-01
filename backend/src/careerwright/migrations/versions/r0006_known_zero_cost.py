"""An attempt that made no provider call records a known zero cost.

`none` attempts (refused before the call, reusing a recorded result, or answered by the
fixture interviewer) cost nothing, and that is known: they record 0, never null. Null stays
reserved for an unknown cost. Existing `none` rows are set to 0.

Forward-only (see `docs/runbook.md`).

Revision ID: 0006
"""

from careerwright.migrations.sql import run_script

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.model_attempts DROP CONSTRAINT known_cost_only_when_reconciled;
UPDATE careerwright.model_attempts SET cost_nano_usd = 0 WHERE spend_state = 'none';
ALTER TABLE careerwright.model_attempts ADD CONSTRAINT known_cost_only_when_reconciled_or_none
    CHECK ((spend_state IN ('reconciled', 'none')) = (cost_nano_usd IS NOT NULL));
ALTER TABLE careerwright.model_attempts ADD CONSTRAINT no_call_costs_zero
    CHECK (spend_state <> 'none' OR cost_nano_usd = 0);
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
