"""What a retrieved source could not say (Task 7A fix round 1; ADR 0009 decisions 5 and 8).

- `extraction`: why a retrieved source gave no publishable posting. `no_job_posting` (its
  structured data was read and holds none) is the only one that may count as "none found";
  `no_structured_data`, `jsonld_invalid` and `conflicting_job_postings` say the page could
  not be read, and the listing says so (`no_posting_readable`), never "no vacancies".
- `total_matching`: Adzuna's count of matching adverts, so a search that retrieved fewer
  than matched is a partial result, never a complete one.

Rows recorded before this revision have neither: they stay unknown.

- The worker may settle its own run's pending attempt as `access_revoked` once the
  requester has lost access (and do nothing else to it), so no attempt is left pending.
- An attempt's `reason` is one of a fixed set of labels (`records.AttemptReason`). An HTTP
  error is `http_error` with its status in `http_status`; rows that recorded it as
  `http_<status>` are relabelled.

Forward-only (see `docs/runbook.md`).

Revision ID: 0016
"""

from careerwright.migrations.sql import run_script

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.source_attempts
    ADD COLUMN extraction text CHECK (extraction IN ('no_structured_data', 'jsonld_invalid',
        'conflicting_job_postings', 'no_job_posting')),
    ADD COLUMN total_matching integer CHECK (total_matching >= 0),
    ADD CONSTRAINT only_retrieved_sources_say_what_they_held
        CHECK (status = 'succeeded' OR (extraction IS NULL AND total_matching IS NULL));
GRANT UPDATE (extraction, total_matching) ON careerwright.source_attempts TO careerwright_worker;

UPDATE careerwright.source_attempts SET reason = 'http_error' WHERE reason ~ '^http_[0-9]{3}$';
ALTER TABLE careerwright.source_attempts
    ADD CONSTRAINT attempt_reasons_are_labels CHECK (reason IN (
    'malformed_url', 'url_too_long', 'scheme_not_allowed', 'credentials_in_url',
    'port_not_allowed', 'host_not_allowed', 'address_not_allowed', 'redirect_downgrade',
    'source_denied', 'source_api_only', 'robots_disallowed', 'adzuna_credentials_not_configured',
    'http_error', 'robots_unreachable', 'timeout', 'too_large', 'too_many_redirects',
    'unsupported_content_type', 'unsupported_content_encoding', 'host_not_found', 'tls_failed',
    'connection_failed', 'response_invalid', 'body_hash_mismatch',
    'acquisition_worker_unavailable', 'interrupted', 'access_revoked'));

-- An UPDATE's new row must pass the SELECT policies too, so the settled row stays visible.
CREATE POLICY worker_sees_its_pending ON careerwright.source_attempts FOR SELECT TO
    careerwright_worker
    USING (run_id = careerwright.current_run_id()
           AND (status = 'pending' OR (status = 'failed' AND reason = 'access_revoked')));
CREATE POLICY worker_settles_revoked ON careerwright.source_attempts FOR UPDATE TO
    careerwright_worker
    USING (run_id = careerwright.current_run_id() AND status = 'pending')
    WITH CHECK (run_id = careerwright.current_run_id() AND status = 'failed'
                AND reason = 'access_revoked');
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
