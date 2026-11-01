"""Slate explanations: the written "Why this could suit you" (Task 6b, S2.7; ADR 0007
decision 12, ADR 0008 decision 4).

- A `slate_explanation` run writes, in one bounded call, a short span-cited explanation for
  each suggestion of a discovery's slate. Like a discovery it pins the profile version it
  read (the discovery's) and carries a sealed input (the pinned answers and ESCO's records),
  so the worker still never reads profile or taxonomy tables. A demo workspace's explanation
  uses the deterministic fixture explainer, never a provider model.
- `slate_explanations` links the explanation run to its discovery: at most one per
  discovery (a changed view of the slate is never a new slate, so it never makes a call).

Forward-only (see `docs/runbook.md`).

Revision ID: 0011
"""

from careerwright.migrations.sql import run_script

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.runs DROP CONSTRAINT runs_kind_check;
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_kind_check
    CHECK (kind IN ('connection_check', 'interview_turn', 'discovery', 'slate_explanation'));
ALTER TABLE careerwright.runs DROP CONSTRAINT the_fixture_models_only_interview_or_discover;
ALTER TABLE careerwright.runs ADD CONSTRAINT the_fixture_models_only_interview_discover_or_explain
    CHECK (model_mode <> 'fixture' OR kind IN ('interview_turn', 'discovery', 'slate_explanation'));
ALTER TABLE careerwright.runs DROP CONSTRAINT profile_reading_runs_pin_the_profile_version;
ALTER TABLE careerwright.runs ADD CONSTRAINT profile_reading_runs_pin_the_profile_version
    CHECK (
        (kind IN ('interview_turn', 'discovery', 'slate_explanation'))
        = (profile_version IS NOT NULL)
    );

CREATE TABLE careerwright.slate_explanations (
    explanation_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    discovery_id uuid NOT NULL UNIQUE,
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT an_explanation_is_not_its_discovery CHECK (explanation_id <> discovery_id),
    FOREIGN KEY (workspace_id, explanation_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, discovery_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.slate_explanations IS
    'The written explanation of a discovery''s slate: explanation_id is the explanation run. '
    'At most one per discovery. Append-only.';
ALTER TABLE careerwright.slate_explanations ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.slate_explanations TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.slate_explanations TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
