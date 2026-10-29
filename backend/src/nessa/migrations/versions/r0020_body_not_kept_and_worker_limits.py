"""Why a body was not kept, typed; and what the worker may never do to a person's examples
(Task 7A fix round 2, review B N5 and N6; ADR 0009 decisions 4 and 6).

- `source_attempts.body_not_kept`: why a body its class may keep was not kept, because
  personal details in it could not be removed (`contact_unlocated`: a JSON-LD block with
  them could not be found to rewrite; `block_unredactable`: a JSON-LD block that is not
  JSON held them). `rights_status` is the rights statement only.
- Restrictive policies: the worker never deletes an exemplar job, and never moves a pasted
  copy or moves any copy onto an exemplar, whatever its grants allow (0017 gave it
  `DELETE` on jobs and `UPDATE (job_id)` on copies, for merging).

Forward-only (see `docs/runbook.md`).

Revision ID: 0020
"""

from nessa.migrations.sql import run_script

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.source_attempts
    ADD COLUMN body_not_kept text
        CHECK (body_not_kept IN ('contact_unlocated', 'block_unredactable')),
    ADD CONSTRAINT a_body_not_kept_is_not_kept
        CHECK (body_not_kept IS NULL OR retention = 'excerpts');
GRANT UPDATE (body_not_kept) ON nessa.source_attempts TO nessa_worker;
UPDATE nessa.source_attempts
    SET body_not_kept = 'contact_unlocated',
        rights_status = replace(rights_status, ' [body_not_kept:contact_unlocated]', '')
    WHERE rights_status LIKE '% [body\\_not\\_kept:contact\\_unlocated]';

CREATE POLICY worker_keeps_exemplars ON nessa.jobs AS RESTRICTIVE FOR DELETE TO nessa_worker
    USING (NOT exemplar);
CREATE POLICY worker_leaves_pasted_copies ON nessa.job_copies AS RESTRICTIVE FOR UPDATE
    TO nessa_worker
    USING (provider <> 'pasted_text')
    WITH CHECK (provider <> 'pasted_text'
                AND job_id IN (SELECT j.job_id FROM nessa.jobs j WHERE NOT j.exemplar));
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
