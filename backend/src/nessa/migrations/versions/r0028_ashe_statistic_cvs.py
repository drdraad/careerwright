"""Each ASHE statistic keeps its own coefficient of variation (Task 7 slice B fix round 1,
review A M4; ADR 0010 decision 4).

- `ashe_estimates.median_cv` is replaced by `cvs`: statistic -> its CV (%) from ONS's "b"
  table as decimal text, null where ONS withholds it, so a P90's quality band is its own,
  never the median's.
- The held ASHE import and its manifest row are removed, so `setup-database` imports the
  pinned release again with the new transformation (`nessa-ashe-import-2`). ASHE is public
  reference data: nothing private is lost, and the pinned file is unchanged.

Forward-only (see `docs/runbook.md`).

Revision ID: 0028
"""

from nessa.migrations.sql import run_script

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

SCHEMA = """
DELETE FROM nessa.ashe_estimates;
DELETE FROM nessa.reference_releases WHERE dataset = 'ashe';
ALTER TABLE nessa.ashe_estimates DROP COLUMN median_cv;
ALTER TABLE nessa.ashe_estimates ADD COLUMN cvs jsonb NOT NULL;
COMMENT ON COLUMN nessa.ashe_estimates.cvs IS
    'Statistic -> its coefficient of variation (%) from ONS''s "b" table, as decimal text; '
    'null where ONS withholds it.';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
