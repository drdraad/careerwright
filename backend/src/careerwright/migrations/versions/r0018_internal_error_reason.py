"""An attempt may fail `internal_error` (Task 7A fix round 1 addendum; ADR 0009 decision 8).

A defect while the restricted acquisition worker acquires a source is answered as a failed
attempt with this reason, never as the worker being unavailable (re-review A M-7), so the
attempt reasons' CHECK (migration 0016) gains it.

Forward-only (see `docs/runbook.md`).

Revision ID: 0018
"""

from careerwright.migrations.sql import run_script

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.source_attempts DROP CONSTRAINT attempt_reasons_are_labels;
ALTER TABLE careerwright.source_attempts
    ADD CONSTRAINT attempt_reasons_are_labels CHECK (reason IN (
    'malformed_url', 'url_too_long', 'scheme_not_allowed', 'credentials_in_url',
    'port_not_allowed', 'host_not_allowed', 'address_not_allowed', 'redirect_downgrade',
    'source_denied', 'source_api_only', 'robots_disallowed', 'adzuna_credentials_not_configured',
    'http_error', 'robots_unreachable', 'timeout', 'too_large', 'too_many_redirects',
    'unsupported_content_type', 'unsupported_content_encoding', 'host_not_found', 'tls_failed',
    'connection_failed', 'response_invalid', 'body_hash_mismatch',
    'acquisition_worker_unavailable', 'interrupted', 'access_revoked', 'internal_error'));
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
