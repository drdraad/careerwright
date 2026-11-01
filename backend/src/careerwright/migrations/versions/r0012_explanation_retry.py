"""A slate's written explanation may be started again when its run failed before any request
reached a model (Task 6b fix round 1; ADR 0007 decision 12).

- `replaced_at` marks a link that a new run replaced. At most one current link per
  discovery (a partial unique index) replaces the plain unique key, so a slate still has
  one live note, and the failed run stays in `runs` with its attempts.
- The API may set `replaced_at` and nothing else: the table stays otherwise append-only.

Forward-only (see `docs/runbook.md`).

Revision ID: 0012
"""

from careerwright.migrations.sql import run_script

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.slate_explanations ADD COLUMN replaced_at timestamptz;
ALTER TABLE careerwright.slate_explanations DROP CONSTRAINT slate_explanations_discovery_id_key;
CREATE UNIQUE INDEX one_current_explanation_per_discovery
    ON careerwright.slate_explanations (discovery_id) WHERE replaced_at IS NULL;
COMMENT ON TABLE careerwright.slate_explanations IS
    'The written explanation of a discovery''s slate: explanation_id is the explanation run. '
    'At most one current link per discovery; a link is replaced (replaced_at) only when its '
    'run failed before any request reached a model.';
GRANT UPDATE (replaced_at) ON careerwright.slate_explanations TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
