"""A model-read page whose every posting conflicts says so (Task 7A fix round 3, review C
M5; ADR 0009 decision 15).

- `page_extractions.outcome` gains `postings_conflicting`: the run recorded postings that
  all disagree on a critical field, so none is published. Such a page was counted
  `no_posting_readable` before and still is; only its own state (never `postings_read`)
  is new.

Forward-only (see `docs/runbook.md`).

Revision ID: 0024
"""

from careerwright.migrations.sql import run_script

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.page_extractions DROP CONSTRAINT page_extractions_outcome_check;
ALTER TABLE careerwright.page_extractions ADD CONSTRAINT page_extractions_outcome_check
    CHECK (outcome IN ('postings_recorded', 'no_posting_found', 'postings_unverified',
                       'postings_conflicting'));
UPDATE careerwright.page_extractions e SET outcome = 'postings_conflicting'
    WHERE e.outcome = 'postings_recorded'
      AND NOT EXISTS (SELECT 1 FROM careerwright.job_copies c
                      WHERE c.attempt_id = e.attempt_id AND c.job_id IS NOT NULL);
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
