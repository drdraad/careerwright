"""Model extraction of a page's job advert (Task 7A fix round 2, rulings 9-12; ADR 0009
decision 15).

- `page_extraction` runs are model-backed runs on the one bounded activity. They read one
  retrieved, permitted page whose structured data gave no posting, never in a demo
  workspace, never with the fixture models, and pin no profile version (they read none).
- `page_extractions`: for each page an acquisition could hand to model extraction, the run
  it started, or why none was started (`not_run`), the hash of the text the run read (its
  claims' spans index into that text), and once the run's output is accepted, what it
  recorded (`outcome`).
- `nessa.submit_page_extraction`: how an acquisition run's worker starts one, for an
  attempt of its own run that model extraction may read, at most five per acquisition (the
  run, its sealed input, its outbox entry and the link, in the acquisition's transaction).
  It is the worker's only way to start a run; the run's requester is the acquisition's.
- `nessa.erase_run_input`: an extraction run's sealed input (the page's text) is erased
  once the run is terminal, whatever its outcome and whether or not its requester may still
  act. The hash, the claims' spans and their excerpts remain.
- `source_claims.validation` gains `model`: a value a model read from the page's text and
  deterministic code approved; it always cites offsets into that text.

Forward-only (see `docs/runbook.md`).

Revision ID: 0021
"""

from nessa.migrations.sql import run_script

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.runs DROP CONSTRAINT runs_kind_check;
ALTER TABLE nessa.runs ADD CONSTRAINT runs_kind_check CHECK (
    kind IN ('connection_check', 'interview_turn', 'discovery', 'slate_explanation',
             'acquisition', 'source_search', 'page_extraction')
);
ALTER TABLE nessa.runs DROP CONSTRAINT demo_workspaces_never_acquire_or_search;
ALTER TABLE nessa.runs ADD CONSTRAINT demo_workspaces_never_acquire_or_search
    CHECK (data_mode <> 'demo' OR kind NOT IN ('acquisition', 'source_search', 'page_extraction'));

ALTER TABLE nessa.source_claims DROP CONSTRAINT source_claims_validation_check;
ALTER TABLE nessa.source_claims ADD CONSTRAINT source_claims_validation_check
    CHECK (validation IN ('structured', 'user_supplied', 'model', 'quarantined'));
ALTER TABLE nessa.source_claims ADD CONSTRAINT model_claims_cite_their_span
    CHECK (validation <> 'model' OR jsonb_typeof(span -> 'start') = 'number');

CREATE TABLE nessa.page_extractions (
    attempt_id uuid PRIMARY KEY REFERENCES nessa.source_attempts ON DELETE CASCADE,
    workspace_id uuid NOT NULL REFERENCES nessa.workspaces ON DELETE CASCADE,
    acquisition_run_id uuid NOT NULL,
    run_id uuid UNIQUE,
    not_run text CHECK (not_run IN ('cap_reached', 'budget_exceeded', 'no_model_key',
        'model_not_permitted', 'demo_workspace', 'no_visible_text')),
    text_sha256 text CHECK (text_sha256 ~ '^[0-9a-f]{64}$'),
    outcome text
        CHECK (outcome IN ('postings_recorded', 'no_posting_found', 'postings_unverified')),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT an_extraction_ran_or_says_why_not
        CHECK ((run_id IS NULL) = (not_run IS NOT NULL)
               AND (run_id IS NULL) = (text_sha256 IS NULL)),
    CONSTRAINT only_a_run_has_an_outcome CHECK (outcome IS NULL OR run_id IS NOT NULL),
    FOREIGN KEY (workspace_id, acquisition_run_id)
        REFERENCES nessa.runs (workspace_id, run_id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES nessa.runs (workspace_id, run_id) ON DELETE CASCADE
);
CREATE INDEX page_extractions_by_acquisition ON nessa.page_extractions (acquisition_run_id);
COMMENT ON TABLE nessa.page_extractions IS
    'A page an acquisition could hand to model extraction: the run it started, or why none '
    'was (never "none found"); the hash of the text the run read; what its output recorded.';

ALTER TABLE nessa.page_extractions ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON nessa.page_extractions FOR SELECT TO nessa_api
    USING (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w));
GRANT SELECT ON nessa.page_extractions TO nessa_api;
CREATE POLICY worker_authorised ON nessa.page_extractions FOR SELECT TO nessa_worker
    USING (workspace_id = nessa.authorised_run_workspace());
CREATE POLICY worker_records_not_run ON nessa.page_extractions FOR INSERT TO nessa_worker
    WITH CHECK (
        workspace_id = nessa.authorised_run_workspace()
        AND acquisition_run_id = nessa.current_run_id()
        AND run_id IS NULL
        AND attempt_id IN (SELECT a.attempt_id FROM nessa.source_attempts a
                           WHERE a.run_id = nessa.current_run_id())
    );
CREATE POLICY worker_records_outcome ON nessa.page_extractions FOR UPDATE TO nessa_worker
    USING (run_id = nessa.current_run_id() AND workspace_id = nessa.authorised_run_workspace())
    WITH CHECK (run_id = nessa.current_run_id());
GRANT SELECT, INSERT ON nessa.page_extractions TO nessa_worker;
GRANT UPDATE (outcome) ON nessa.page_extractions TO nessa_worker;

CREATE FUNCTION nessa.submit_page_extraction(
    p_attempt uuid, p_run uuid, p_model_id text, p_model_mode text, p_key_version integer,
    p_nonce bytea, p_ciphertext bytea, p_text_sha256 text
) RETURNS void
    LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $$
DECLARE
    acquisition nessa.runs%ROWTYPE;
BEGIN
    SELECT r.* INTO acquisition FROM nessa.runs r
        WHERE r.run_id = nessa.current_run_id() AND r.kind = 'acquisition'
          AND r.workspace_id = nessa.authorised_run_workspace();
    IF NOT FOUND THEN
        RAISE EXCEPTION 'only an authorised acquisition run starts an extraction'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM nessa.source_attempts a
        WHERE a.attempt_id = p_attempt AND a.run_id = acquisition.run_id
          AND a.route = 'fetch' AND a.status = 'succeeded'
          AND a.extraction IN ('no_structured_data', 'no_job_posting')
    ) THEN
        RAISE EXCEPTION 'extraction reads only a fetched page whose structured data gave no posting'
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    -- MAX_EXTRACTIONS_PER_ACQUISITION (`nessa.evidence.extraction_runs`).
    IF (SELECT count(*) FROM nessa.page_extractions e
        WHERE e.acquisition_run_id = acquisition.run_id AND e.run_id IS NOT NULL) >= 5 THEN
        RAISE EXCEPTION 'an acquisition starts at most 5 extraction runs'
            USING ERRCODE = 'check_violation';
    END IF;
    INSERT INTO nessa.runs (run_id, workspace_id, data_mode, synthetic, kind, requested_by,
                            model_id, model_mode, status)
        VALUES (p_run, acquisition.workspace_id, acquisition.data_mode, acquisition.synthetic,
                'page_extraction', acquisition.requested_by, p_model_id, p_model_mode, 'queued');
    INSERT INTO nessa.run_inputs (run_id, workspace_id, key_version, nonce, ciphertext)
        VALUES (p_run, acquisition.workspace_id, p_key_version, p_nonce, p_ciphertext);
    INSERT INTO nessa.outbox (workspace_id, run_id, workflow_id, workflow_name)
        VALUES (acquisition.workspace_id, p_run, 'nessa-run-' || p_run::text, 'nessa.model_run');
    INSERT INTO nessa.page_extractions (attempt_id, workspace_id, acquisition_run_id, run_id,
                                        text_sha256)
        VALUES (p_attempt, acquisition.workspace_id, acquisition.run_id, p_run, p_text_sha256);
END
$$;

CREATE FUNCTION nessa.erase_run_input() RETURNS boolean
    LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $$
        WITH erased AS (
            DELETE FROM nessa.run_inputs i
            USING nessa.runs r
            WHERE i.run_id = nessa.current_run_id() AND r.run_id = i.run_id
              AND r.kind = 'page_extraction'
              AND r.status IN ('complete', 'failed', 'provider_unavailable', 'cancelled')
            RETURNING i.run_id
        )
        SELECT EXISTS (SELECT 1 FROM erased)
    $$;

REVOKE ALL ON FUNCTION
    nessa.submit_page_extraction(uuid, uuid, text, text, integer, bytea, bytea, text),
    nessa.erase_run_input() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION
    nessa.submit_page_extraction(uuid, uuid, text, text, integer, bytea, bytea, text),
    nessa.erase_run_input() TO nessa_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
