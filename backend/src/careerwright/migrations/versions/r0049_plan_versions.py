"""Immutable chosen plan snapshots, removed with their workspace.

Revision ID: 0049
"""

from careerwright.migrations.sql import run_script

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE careerwright.plan_versions (
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    version integer NOT NULL CHECK (version >= 1),
    plan_id uuid NOT NULL,
    solve_run_id uuid NOT NULL,
    schedule_index integer NOT NULL CHECK (schedule_index >= 0),
    snapshot jsonb NOT NULL CHECK (jsonb_typeof(snapshot) = 'object'),
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL,
    PRIMARY KEY (workspace_id, version),
    CONSTRAINT plan_snapshot_identity CHECK (
        snapshot->>'workspace_id' = workspace_id::text
        AND (snapshot->>'version')::integer = version
        AND snapshot->>'plan_id' = plan_id::text
        AND snapshot->'source'->>'solve_run_id' = solve_run_id::text
        AND (snapshot->'source'->>'schedule_index')::integer = schedule_index
    )
);
CREATE INDEX plan_versions_by_plan ON careerwright.plan_versions (plan_id, version);
ALTER TABLE careerwright.plan_versions ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.plan_versions TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.plan_versions TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
