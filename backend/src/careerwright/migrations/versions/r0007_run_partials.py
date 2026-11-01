"""The partial reply a run streams (spec section 4: stream natural conversation, commit only
after complete validation).

`run_partials` holds at most one row per run: the natural-language reply received so far,
sealed by the worker with the run as associated data, its write sequence and its
completeness (`streaming`, or `incomplete` once that attempt or run failed). The worker
deletes the row in the transaction that stores the run's validated output, so a partial
never outlives the result that supersedes it. The worker may write it only while the run's
requester may still act; the API may only read it, for the workspace's owner.

Forward-only (see `docs/runbook.md`).

Revision ID: 0007
"""

from careerwright.migrations.sql import run_script

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE careerwright.run_partials (
    run_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    seq integer NOT NULL CHECK (seq >= 1),
    completeness text NOT NULL CHECK (completeness IN ('streaming', 'incomplete')),
    key_version integer NOT NULL CHECK (key_version >= 1),
    nonce bytea NOT NULL CHECK (octet_length(nonce) = 12),
    ciphertext bytea NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.run_partials IS
    'A run''s streamed reply so far, sealed: never validated, never a result. Deleted when '
    'the validated output is stored; marked incomplete when the attempt or run fails.';
ALTER TABLE careerwright.run_partials ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.run_partials FOR SELECT TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY worker_authorised ON careerwright.run_partials TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace() AND run_id =
        careerwright.current_run_id())
    WITH CHECK (
        workspace_id = careerwright.authorised_run_workspace() AND run_id =
            careerwright.current_run_id()
    );
GRANT SELECT ON careerwright.run_partials TO careerwright_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON careerwright.run_partials TO careerwright_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
