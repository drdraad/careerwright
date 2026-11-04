"""Workspace-private option research and proposed source records.

Revision ID: 0050
"""

from careerwright.migrations.sql import run_script

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE careerwright.option_researches (
    research_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    target text NOT NULL CHECK (char_length(target) BETWEEN 1 AND 120 AND target = btrim(target)),
    city text NOT NULL CHECK (char_length(city) BETWEEN 1 AND 120 AND city = btrim(city)),
    search_run_id uuid NOT NULL UNIQUE,
    reading_run_id uuid UNIQUE,
    review_state text NOT NULL DEFAULT 'proposed' CHECK (review_state = 'proposed'),
    created_at timestamptz NOT NULL,
    reading_started_at timestamptz,
    UNIQUE (workspace_id, research_id),
    CONSTRAINT reading_is_dated CHECK ((reading_run_id IS NULL) = (reading_started_at IS NULL)),
    FOREIGN KEY (workspace_id, search_run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, reading_run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
CREATE INDEX option_researches_recent ON careerwright.option_researches
    (workspace_id, created_at DESC);

ALTER TABLE careerwright.acquisition_targets
    ADD COLUMN option_research_id uuid REFERENCES careerwright.option_researches (research_id),
    ADD CONSTRAINT option_research_targets_are_fetches CHECK (
        option_research_id IS NULL OR (route = 'fetch' AND role_title IS NULL)
    );

CREATE TABLE careerwright.researched_option_records (
    record_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    research_id uuid NOT NULL,
    attempt_id uuid NOT NULL REFERENCES careerwright.source_attempts ON DELETE CASCADE,
    record_kind text NOT NULL CHECK (record_kind IN ('course', 'funding')),
    catalogue jsonb NOT NULL CHECK (jsonb_typeof(catalogue) = 'object'),
    source_url text NOT NULL,
    retrieved_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL CHECK (expires_at > retrieved_at),
    UNIQUE (attempt_id, record_kind),
    FOREIGN KEY (workspace_id, research_id)
        REFERENCES careerwright.option_researches (workspace_id, research_id) ON DELETE CASCADE
);
CREATE INDEX researched_options_by_target ON careerwright.researched_option_records
    (workspace_id, research_id, expires_at);

ALTER TABLE careerwright.page_extractions DROP CONSTRAINT page_extractions_outcome_check;
ALTER TABLE careerwright.page_extractions ADD CONSTRAINT page_extractions_outcome_check
    CHECK (outcome IN ('postings_recorded', 'no_posting_found', 'postings_unverified',
                      'postings_conflicting', 'options_recorded', 'no_option_found',
                      'options_unverified'));

CREATE OR REPLACE FUNCTION careerwright.submit_page_extraction(
    p_attempt uuid, p_run uuid, p_model_id text, p_model_mode text, p_key_version integer,
    p_nonce bytea, p_ciphertext bytea, p_text_sha256 text
) RETURNS void
    LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $$
DECLARE
    acquisition careerwright.runs%ROWTYPE;
BEGIN
    SELECT r.* INTO acquisition FROM careerwright.runs r
        WHERE r.run_id = careerwright.current_run_id() AND r.kind = 'acquisition'
          AND r.workspace_id = careerwright.authorised_run_workspace();
    IF NOT FOUND THEN
        RAISE EXCEPTION 'only an authorised acquisition run starts an extraction'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(acquisition.run_id::text, 8237));
    IF EXISTS (SELECT 1 FROM careerwright.run_cancellations c WHERE c.run_id = acquisition.run_id)
        THEN
        RAISE EXCEPTION 'a cancelled acquisition starts no extraction'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM careerwright.source_attempts a
        LEFT JOIN careerwright.acquisition_targets t
            ON t.run_id = a.run_id AND t.position = a.position
        WHERE a.attempt_id = p_attempt AND a.run_id = acquisition.run_id
          AND a.route = 'fetch' AND a.status = 'succeeded'
          AND (a.extraction IN ('no_structured_data', 'no_job_posting')
               OR t.option_research_id IS NOT NULL)
    ) THEN
        RAISE EXCEPTION 'extraction reads only an authorised fetched page'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF (SELECT count(*) FROM careerwright.page_extractions e
        WHERE e.acquisition_run_id = acquisition.run_id AND e.run_id IS NOT NULL) >= 5 THEN
        RAISE EXCEPTION 'an acquisition starts at most 5 extraction runs'
            USING ERRCODE = 'check_violation';
    END IF;
    INSERT INTO careerwright.runs (run_id, workspace_id, data_mode, synthetic, kind, requested_by,
                            model_id, model_mode, status, started_by_run)
        VALUES (p_run, acquisition.workspace_id, acquisition.data_mode, acquisition.synthetic,
                'page_extraction', acquisition.requested_by, p_model_id, p_model_mode, 'queued',
                acquisition.run_id);
    INSERT INTO careerwright.run_inputs (run_id, workspace_id, key_version, nonce, ciphertext)
        VALUES (p_run, acquisition.workspace_id, p_key_version, p_nonce, p_ciphertext);
    INSERT INTO careerwright.outbox (workspace_id, run_id, workflow_id, workflow_name)
        VALUES (acquisition.workspace_id, p_run, 'careerwright-run-' || p_run::text,
            'careerwright.model_run');
    INSERT INTO careerwright.page_extractions (attempt_id, workspace_id, acquisition_run_id, run_id,
                                        text_sha256)
        VALUES (p_attempt, acquisition.workspace_id, acquisition.run_id, p_run, p_text_sha256);
END
$$;

ALTER TABLE careerwright.option_researches ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.option_researches TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.option_researches TO careerwright_api;
GRANT UPDATE (reading_run_id, reading_started_at) ON careerwright.option_researches
    TO careerwright_api;
CREATE POLICY worker_authorised ON careerwright.option_researches FOR SELECT
    TO careerwright_worker USING (workspace_id = careerwright.authorised_run_workspace());
GRANT SELECT ON careerwright.option_researches TO careerwright_worker;

ALTER TABLE careerwright.researched_option_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.researched_option_records FOR SELECT
    TO careerwright_api USING (
        workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w)
    );
GRANT SELECT ON careerwright.researched_option_records TO careerwright_api;
CREATE POLICY worker_authorised ON careerwright.researched_option_records
    FOR SELECT TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace());
CREATE POLICY worker_records_source ON careerwright.researched_option_records
    FOR INSERT TO careerwright_worker
    WITH CHECK (
        workspace_id = careerwright.authorised_run_workspace()
        AND (
            attempt_id IN (SELECT a.attempt_id FROM careerwright.source_attempts a
                           WHERE a.run_id = careerwright.current_run_id())
            OR attempt_id IN (SELECT e.attempt_id FROM careerwright.page_extractions e
                              WHERE e.run_id = careerwright.current_run_id())
        )
    );
GRANT SELECT, INSERT ON careerwright.researched_option_records TO careerwright_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
