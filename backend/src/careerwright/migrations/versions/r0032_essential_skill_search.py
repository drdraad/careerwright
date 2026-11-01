"""Work is found through its essential skills (Task W2 slice W2B, fix round 1; ADR 0007
decision 13).

- `skills.search_vector`: English full-text search over each skill's preferred label alone.
  Discovery's searches that are not the person's own title (what they enjoy, can do or have
  done, how they like to work) reach an occupation only through an essential skill whose
  label holds the search's words, so the slate can name that skill. Nothing else is in it:
  no occupation title, hidden label, ISCO group label or description. It is generated from
  the label, so this migration fills it for the release already held and every later import
  fills it as each skill is written.

Forward-only (see `docs/runbook.md`).

Revision ID: 0032
"""

from careerwright.migrations.sql import run_script

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.skills ADD COLUMN search_vector tsvector NOT NULL
    GENERATED ALWAYS AS (to_tsvector('english', preferred_label)) STORED;
CREATE INDEX skills_search_vector ON careerwright.skills USING gin (search_vector);
COMMENT ON COLUMN careerwright.skills.search_vector IS
    'English full-text search over the preferred label alone: discovery reaches an occupation '
    'only through an essential skill whose label holds the search''s words.';
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
