"""Untouched run limits move to the new default, $0.50 (the product owner, 3 November 2026).

Role research's search is now deeper (search context `medium`, up to eight tool calls, ADR
0009 amendment line of 2026-11-03), so a source search's worst case is $0.161 on the Standard
model, the costliest run kind. The default run spend limit becomes $0.50 (500,000,000
nano-USD), so the DBOS step's three attempts of it fit and an outage is never reported as an
exceeded budget. A workspace's limits are stored when its key is, so rows created with the
old default ($0.15) and never changed by the person (`version` 1) move to the new default, as
migration 0009 moved the one before. A limit the person set is kept, whatever it is.

Forward-only (see `docs/runbook.md`).

Revision ID: 0047
"""

from careerwright.migrations.sql import run_script

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None

SCHEMA = """
UPDATE careerwright.spend_limits SET run_limit_nano_usd = 500000000, updated_at = clock_timestamp()
    WHERE version = 1 AND run_limit_nano_usd = 150000000;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
