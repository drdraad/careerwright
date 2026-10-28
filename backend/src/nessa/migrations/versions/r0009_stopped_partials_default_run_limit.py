"""A stopped partial is not called final, and untouched run limits move to the new default.

- `run_partials.completeness` records what the worker knows: `streaming`, or `stopped`
  (that attempt's reply stopped). Whether a stopped reply is final is the run's state: the
  API calls it `incomplete` only once the run has ended without a validated output, because
  between DBOS step retries another attempt may stream again and be superseded. Rows
  recorded as `incomplete` become `stopped`.
- The default run spend limit is $0.15 (150,000,000 nano-USD), so that the DBOS step's three
  attempts of an interview turn fit on the Standard model and an outage is never reported
  as an exceeded budget. Rows created with the old built-in default ($0.10) and never
  changed by the person (`version` 1) move to the new default. A limit the person set is
  kept, whatever it is.

Forward-only (see `docs/runbook.md`).

Revision ID: 0009
"""

from nessa.migrations.sql import run_script

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.run_partials DROP CONSTRAINT run_partials_completeness_check;
UPDATE nessa.run_partials SET completeness = 'stopped' WHERE completeness = 'incomplete';
ALTER TABLE nessa.run_partials ADD CONSTRAINT run_partials_completeness_check
    CHECK (completeness IN ('streaming', 'stopped'));
COMMENT ON TABLE nessa.run_partials IS
    'A run''s streamed reply so far, sealed: never validated, never a result. Deleted when '
    'the validated output is stored; marked stopped when an attempt fails (final only once '
    'the run has ended without an output).';

UPDATE nessa.spend_limits SET run_limit_nano_usd = 150000000, updated_at = clock_timestamp()
    WHERE version = 1 AND run_limit_nano_usd = 100000000;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
