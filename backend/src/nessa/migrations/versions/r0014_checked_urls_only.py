"""Only checked URLs in URL fields (Task 7A fix round 1; ADR 0009 decision 3).

- A submitted URL that the checks refuse (a `javascript:` or `file:` scheme, a port, a local
  name, a private address) is never recorded as a URL: its target holds the refusal and its
  host as plain text (`refusal`, `refused_host`) and no `url`, and its attempt no
  `requested_url`.
- URL-named columns hold `http` or `https` URLs only (`url`, `requested_url`, `final_url`,
  each of `redirects`), so a UI may render them as links. Rows recorded before this
  revision with any other scheme there lose that value: a target becomes a
  `scheme_not_allowed` refusal, an attempt keeps its outcome without the URL, and a
  redirect list keeps its http(s) entries.

Forward-only (see `docs/runbook.md`).

Revision ID: 0014
"""

from nessa.migrations.sql import run_script

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

SCHEMA = r"""
ALTER TABLE nessa.acquisition_targets
    ADD COLUMN refusal text CHECK (refusal IN ('scheme_not_allowed', 'port_not_allowed',
        'host_not_allowed', 'address_not_allowed')),
    ADD COLUMN refused_host text CHECK (char_length(refused_host) <= 253);
COMMENT ON COLUMN nessa.acquisition_targets.refused_host IS
    'The host of a refused URL as plain text, never a link; the URL itself is not kept.';
ALTER TABLE nessa.acquisition_targets DROP CONSTRAINT a_target_is_a_url_or_a_query;

UPDATE nessa.acquisition_targets SET url = NULL, refusal = 'scheme_not_allowed'
    WHERE url IS NOT NULL AND url !~* '^https?://';
UPDATE nessa.source_attempts SET requested_url = NULL
    WHERE requested_url IS NOT NULL AND requested_url !~* '^https?://';
UPDATE nessa.source_attempts SET final_url = NULL
    WHERE final_url IS NOT NULL AND final_url !~* '^https?://';
UPDATE nessa.source_attempts SET redirects = COALESCE(
        (SELECT jsonb_agg(r) FROM jsonb_array_elements_text(redirects) AS r
         WHERE r ~* '^https?://'), '[]'::jsonb)
    WHERE jsonb_path_exists(redirects, '$[*] ? (!(@ like_regex "^https?://" flag "i"))');

ALTER TABLE nessa.acquisition_targets ADD CONSTRAINT a_target_is_a_url_a_refusal_or_a_query
    CHECK ((route = 'adzuna') = (query IS NOT NULL)
           AND (route = 'fetch') = ((url IS NOT NULL) <> (refusal IS NOT NULL))
           AND (refused_host IS NULL OR refusal IS NOT NULL));
ALTER TABLE nessa.acquisition_targets ADD CONSTRAINT target_urls_are_http
    CHECK (url ~* '^https?://');
ALTER TABLE nessa.source_attempts ADD CONSTRAINT attempt_urls_are_http
    CHECK (requested_url ~* '^https?://' AND final_url ~* '^https?://'
           AND NOT jsonb_path_exists(redirects, '$[*] ? (!(@ like_regex "^https?://" flag "i"))'));
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
