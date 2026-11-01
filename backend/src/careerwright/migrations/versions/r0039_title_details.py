"""The person's own details beside a title (Task 6d slice C; ADR 0015 decisions 3 and 4; ADR
0012 as amended on 2026-10-31).

- `title_details`: for the person's current or last role, or a target, by the title as a
  concept (`careerwright.concept_key`): its seniority and its industry, in the person's words,
  each optional (NULL: not given, never a default), and the essential skills ESCO lists for
  its kind of work that the person marked "not part of my job" (ESCO skill IDs). Matching
  ignores all of it; the marks are a display state, never evidence. Append-only: each save is
  the next version of that title's details, so an edit's new words are read against the
  version it was made against (the support screen), as a profile edit's are.

Forward-only (see `docs/runbook.md`).

Revision ID: 0039
"""

from careerwright.migrations.sql import run_script

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE careerwright.title_details (
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    title_use text NOT NULL CHECK (title_use IN ('role', 'target')),
    title_key text NOT NULL CHECK (title_key <> ''),
    version integer NOT NULL CHECK (version >= 1),
    seniority text CHECK (char_length(seniority) BETWEEN 1 AND 120),
    industry text CHECK (char_length(industry) BETWEEN 1 AND 120),
    not_part_of_job uuid[] NOT NULL DEFAULT '{}',
    recorded_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, title_use, title_key, version)
);
COMMENT ON TABLE careerwright.title_details IS
    'The person''s own details beside their role or a target, by the title as a concept: '
    'seniority and industry in their words (NULL: not given), and the skills ESCO lists for '
    'its kind of work they marked not part of their job. Matching ignores them; the marks are '
    'a display state, never evidence. Append-only, one version per save.';

ALTER TABLE careerwright.title_details ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.title_details TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.title_details TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
