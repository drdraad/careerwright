"""One job per vacancy whatever order its copies arrive in, and claims tied to their copies
(Task 7A fix round 1; ADR 0009 decisions 5 and 6).

- The worker may merge jobs that a new copy shows are one (`store.merge_jobs`): it moves
  their copies (`job_copies.job_id`) and favourites to the oldest job and removes the
  others, still only in a workspace whose requester may act.
- `source_claims`: `field` is one of the claim fields, `span` has the shape the code writes
  (a 64-hex `source_sha256`, an excerpt, and offsets or a JSON pointer, never both), and a
  claim's attempt is its copy's attempt (`(copy_id, attempt_id)` references the copy).

Forward-only (see `docs/runbook.md`).

Revision ID: 0017
"""

from careerwright.migrations.sql import run_script

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

SCHEMA = """
GRANT UPDATE (job_id) ON careerwright.job_copies TO careerwright_worker;
GRANT DELETE ON careerwright.jobs TO careerwright_worker;
CREATE POLICY worker_authorised ON careerwright.job_favourites TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (workspace_id = careerwright.authorised_run_workspace());
GRANT SELECT, INSERT ON careerwright.job_favourites TO careerwright_worker;

ALTER TABLE careerwright.source_claims ADD CONSTRAINT claim_fields_are_known CHECK (field IN (
    'title', 'employer', 'location', 'work_mode', 'salary', 'date_posted', 'valid_through',
    'employment_type', 'description', 'apply_url', 'source_job_id'));
ALTER TABLE careerwright.source_claims ADD CONSTRAINT claim_spans_have_their_shape CHECK (
    jsonb_typeof(span) = 'object'
    AND span ->> 'source_sha256' ~ '^[0-9a-f]{64}$'
    AND jsonb_typeof(span -> 'excerpt') = 'string'
    AND (
        (jsonb_typeof(span -> 'start') = 'number' AND jsonb_typeof(span -> 'end') = 'number'
         AND coalesce(jsonb_typeof(span -> 'pointer'), 'null') = 'null')
        OR (jsonb_typeof(span -> 'pointer') = 'string'
            AND coalesce(jsonb_typeof(span -> 'start'), 'null') = 'null'
            AND coalesce(jsonb_typeof(span -> 'end'), 'null') = 'null')
    )
);
ALTER TABLE careerwright.job_copies
    ADD CONSTRAINT job_copies_copy_attempt_key UNIQUE (copy_id, attempt_id);
ALTER TABLE careerwright.source_claims ADD CONSTRAINT claims_are_their_copy_s_attempt
    FOREIGN KEY (copy_id, attempt_id) REFERENCES careerwright.job_copies (copy_id, attempt_id)
    ON DELETE CASCADE;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
