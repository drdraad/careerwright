"""Only an API's own empty answer says no vacancy was there (Task 7A fix round 2, review B
N1; ADR 0009 decision 8).

A fetched page whose structured data holds no job posting (`no_job_posting`) says nothing
about its HTML, so it now counts as not read. Adzuna's own count of none gets its own label,
`no_matching_adverts`, the only one that may support "none found in the sources checked";
Adzuna attempts recorded before this revision with a count of 0 are relabelled.

Forward-only (see `docs/runbook.md`).

Revision ID: 0019
"""

from nessa.migrations.sql import run_script

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.source_attempts DROP CONSTRAINT source_attempts_extraction_check;
ALTER TABLE nessa.source_attempts ADD CONSTRAINT source_attempts_extraction_check
    CHECK (extraction IN ('no_structured_data', 'jsonld_invalid', 'conflicting_job_postings',
        'no_job_posting', 'no_matching_adverts'));
UPDATE nessa.source_attempts SET extraction = 'no_matching_adverts'
    WHERE route = 'adzuna' AND extraction = 'no_job_posting' AND total_matching = 0;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
