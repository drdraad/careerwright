"""Cancelling an acquisition cancels the extraction runs it started (Task 7A fix round 3,
item 4; ADR 0009 decision 15; DUR-05).

- `runs.started_by_run`: the run that started this one; exactly the `page_extraction` runs
  have one, their acquisition (existing rows are filled from `page_extractions`). The API's
  cancel of a run also requests the cancellation of every run it started that has not yet
  settled (queued or running), and the worker acts on each request on its own.
- `nessa.submit_page_extraction` takes the acquisition's cancellation lock (an advisory lock
  on its run ID, which the API's cancel takes too) and refuses once a cancellation is
  requested, so an extraction can never start unseen by a cancel; it records the
  acquisition as the run's `started_by_run`.
- `page_extractions.not_run` gains `acquisition_cancelled`: the acquisition was cancelled
  before the page could be handed over.

Forward-only (see `docs/runbook.md`).

Revision ID: 0023
"""

from nessa.migrations.sql import run_script

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE nessa.runs ADD COLUMN started_by_run uuid;
UPDATE nessa.runs r SET started_by_run = e.acquisition_run_id
    FROM nessa.page_extractions e WHERE e.run_id = r.run_id;
ALTER TABLE nessa.runs ADD CONSTRAINT runs_started_by_run_fkey
    FOREIGN KEY (workspace_id, started_by_run)
    REFERENCES nessa.runs (workspace_id, run_id) ON DELETE CASCADE;
ALTER TABLE nessa.runs ADD CONSTRAINT only_extractions_are_started_by_a_run
    CHECK ((started_by_run IS NOT NULL) = (kind = 'page_extraction'));
CREATE INDEX runs_by_starting_run ON nessa.runs (started_by_run)
    WHERE started_by_run IS NOT NULL;

ALTER TABLE nessa.page_extractions DROP CONSTRAINT page_extractions_not_run_check;
ALTER TABLE nessa.page_extractions ADD CONSTRAINT page_extractions_not_run_check
    CHECK (not_run IN ('cap_reached', 'budget_exceeded', 'no_model_key',
        'model_not_permitted', 'demo_workspace', 'no_visible_text', 'acquisition_cancelled'));

CREATE OR REPLACE FUNCTION nessa.submit_page_extraction(
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
    -- The cancellation lock (`run_store.lock_started_runs`): a cancel either sees this run,
    -- or this sees the cancel.
    PERFORM pg_advisory_xact_lock(hashtextextended(acquisition.run_id::text, 8237));
    IF EXISTS (SELECT 1 FROM nessa.run_cancellations c WHERE c.run_id = acquisition.run_id) THEN
        RAISE EXCEPTION 'a cancelled acquisition starts no extraction'
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
                            model_id, model_mode, status, started_by_run)
        VALUES (p_run, acquisition.workspace_id, acquisition.data_mode, acquisition.synthetic,
                'page_extraction', acquisition.requested_by, p_model_id, p_model_mode, 'queued',
                acquisition.run_id);
    INSERT INTO nessa.run_inputs (run_id, workspace_id, key_version, nonce, ciphertext)
        VALUES (p_run, acquisition.workspace_id, p_key_version, p_nonce, p_ciphertext);
    INSERT INTO nessa.outbox (workspace_id, run_id, workflow_id, workflow_name)
        VALUES (acquisition.workspace_id, p_run, 'nessa-run-' || p_run::text, 'nessa.model_run');
    INSERT INTO nessa.page_extractions (attempt_id, workspace_id, acquisition_run_id, run_id,
                                        text_sha256)
        VALUES (p_attempt, acquisition.workspace_id, acquisition.run_id, p_run, p_text_sha256);
END
$$;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
