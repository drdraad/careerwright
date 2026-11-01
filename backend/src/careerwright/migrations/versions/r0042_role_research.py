"""Research this role (Task 6e; ADR 0015 decision 2 and its Task 6e amendment line; ADR 0009
decision 12, amendment).

- `role_researches`: one per "Research this role", private to its workspace: the title as the
  person or a title idea gave it, the source search that looked for pages about it, and the
  acquisition that read up to five of them (none until it starts). Always `proposed` and
  dated (ruling R9): the record is research, never a reviewed record.
- `acquisition_targets.role_title`: a target read for role research carries the title, so
  the worker checks it against the page's visible text and records that check instead of
  postings. Only a fetch target may carry one.
- `role_page_checks`: what code found of the title on one read page: the hash of the visible
  text checked, the span and the excerpt around it (at most 200 characters) where the title
  is verified word for word, the passage fingerprint that folds copies of one advert, and
  the page's structured postings' canonical facts. The text itself is never kept.

The worker reads its run's targets (as before), and records a check only for its own run's
attempt while the requester may act; the API reads both in its owner's workspaces and writes
the research records.

Forward-only (see `docs/runbook.md`).

Revision ID: 0042
"""

from careerwright.migrations.sql import run_script

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.acquisition_targets
    ADD COLUMN role_title text,
    ADD CONSTRAINT a_role_title_is_a_fetch_targets_trimmed_title CHECK (
        role_title IS NULL
        OR (route = 'fetch' AND char_length(role_title) BETWEEN 1 AND 120
            AND role_title = btrim(role_title))
    );

CREATE TABLE careerwright.role_researches (
    research_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120 AND title = btrim(title)),
    title_key text NOT NULL CHECK (title_key <> ''),
    search_run_id uuid NOT NULL UNIQUE,
    reading_run_id uuid UNIQUE,
    review_state text NOT NULL DEFAULT 'proposed' CHECK (review_state = 'proposed'),
    requested_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    reading_started_at timestamptz,
    CONSTRAINT a_reading_is_dated CHECK ((reading_run_id IS NULL) = (reading_started_at IS NULL)),
    CONSTRAINT a_research_never_reads_with_its_search CHECK (reading_run_id <> search_run_id),
    FOREIGN KEY (workspace_id, search_run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, reading_run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
CREATE INDEX role_researches_by_title ON careerwright.role_researches
    (workspace_id, title_key, created_at);
COMMENT ON TABLE careerwright.role_researches IS
    'Research this role: a title no list holds, the search for pages about it (only the title '
    'and England were sent) and the acquisition that read them. Workspace-private, proposed '
    'and dated (R9). Whether the role is found is decided on read from role_page_checks.';

CREATE TABLE careerwright.role_page_checks (
    attempt_id uuid PRIMARY KEY REFERENCES careerwright.source_attempts ON DELETE CASCADE,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    text_sha256 text NOT NULL CHECK (text_sha256 ~ '^[0-9a-f]{64}$'),
    span_start integer,
    span_end integer,
    excerpt text,
    passage_sha256 text CHECK (passage_sha256 ~ '^[0-9a-f]{64}$'),
    postings jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(postings) = 'array'),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT a_verified_title_has_its_span_excerpt_and_passage CHECK (
        (span_start IS NULL) = (span_end IS NULL)
        AND (span_start IS NULL) = (excerpt IS NULL)
        AND (span_start IS NULL) = (passage_sha256 IS NULL)
    ),
    CONSTRAINT a_span_is_a_range_of_the_text CHECK (
        span_start IS NULL OR (span_start >= 0 AND span_end > span_start)
    ),
    CONSTRAINT an_excerpt_is_minimal CHECK (
        excerpt IS NULL OR char_length(excerpt) BETWEEN 1 AND 200
    )
);
COMMENT ON TABLE careerwright.role_page_checks IS
    'What code found of a researched title on one page read for it: the visible text''s '
    'hash, and where the title is verified word for word its span, a minimal excerpt and the '
    'passage fingerprint that folds copies of one advert. The text itself is never kept.';

ALTER TABLE careerwright.role_researches ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.role_page_checks ENABLE ROW LEVEL SECURITY;

CREATE POLICY api_workspace ON careerwright.role_researches TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.role_researches TO careerwright_api;
GRANT UPDATE (reading_run_id, reading_started_at) ON careerwright.role_researches
    TO careerwright_api;

CREATE POLICY api_workspace ON careerwright.role_page_checks TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT ON careerwright.role_page_checks TO careerwright_api;

CREATE POLICY worker_authorised ON careerwright.role_page_checks TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (
        workspace_id = careerwright.authorised_run_workspace()
        AND attempt_id IN (
            SELECT a.attempt_id FROM careerwright.source_attempts a
            WHERE a.run_id = careerwright.current_run_id()
        )
    );
GRANT SELECT, INSERT ON careerwright.role_page_checks TO careerwright_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
