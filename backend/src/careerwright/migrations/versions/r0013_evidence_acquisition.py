"""Evidence acquisition, run cancellation and source search (Task 7A, Sprint 3; ADR 0009).

- `acquisition` runs fetch permitted pages or query Adzuna through the restricted
  acquisition worker. They call no model, so they name none (`model_id` and `model_mode`
  are null exactly for them), never run in a demo workspace, and run in their own workflow
  (`outbox.workflow_name`). `source_search` runs are model-backed (Meta search proposes
  candidate URLs) and pin the profile version they read, like a discovery.
- `run_cancellations`: a person's request to cancel a queued or running run (DUR-05). The
  worker reads them unscoped (identifiers only, like the outbox), cancels the DBOS workflow
  and publishes the run `cancelled`.
- `acquisition_targets`: the URLs or Adzuna queries an acquisition run works through.
- `source_attempts` (spec section 18, SourceAttempt): every try by any route, blocked and
  failed ones included; a retry names the attempt it repeats. Pasted text is its own route
  and its attempt belongs to no run. `source_documents` hold a body only where the session 1
  rights policy permits keeping it, sealed to the workspace (reseal covers them).
- `job_copies` are each source's view of a vacancy; `jobs` group them (JOB-02). A copy with
  an extraction error belongs to no job: it is never published. `source_claims` are the
  copies' field values with their spans (spec section 18, SourceClaim). `job_favourites`
  are a person's marks.

The worker writes evidence only for the run it executes and only while the run's requester
may act (`careerwright.authorised_run_workspace()`); the API reads its owner's workspaces and
writes pasted text and favourites. Forward-only (see `docs/runbook.md`).

Revision ID: 0013
"""

from careerwright.migrations.sql import run_script

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.runs DROP CONSTRAINT runs_kind_check;
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_kind_check CHECK (
    kind IN ('connection_check', 'interview_turn', 'discovery', 'slate_explanation',
             'acquisition', 'source_search')
);
ALTER TABLE careerwright.runs ALTER COLUMN model_id DROP NOT NULL;
ALTER TABLE careerwright.runs ALTER COLUMN model_mode DROP NOT NULL;
ALTER TABLE careerwright.runs ADD CONSTRAINT only_acquisitions_name_no_model
    CHECK ((model_id IS NULL) = (kind = 'acquisition')
           AND (model_mode IS NULL) = (model_id IS NULL));
ALTER TABLE careerwright.runs ADD CONSTRAINT demo_workspaces_never_acquire_or_search
    CHECK (data_mode <> 'demo' OR kind NOT IN ('acquisition', 'source_search'));
ALTER TABLE careerwright.runs DROP CONSTRAINT profile_reading_runs_pin_the_profile_version;
ALTER TABLE careerwright.runs ADD CONSTRAINT profile_reading_runs_pin_the_profile_version
    CHECK (
        (kind IN ('interview_turn', 'discovery', 'slate_explanation', 'source_search'))
        = (profile_version IS NOT NULL)
    );

ALTER TABLE careerwright.outbox ADD COLUMN workflow_name text NOT NULL DEFAULT
    'careerwright.model_run'
    CHECK (workflow_name IN ('careerwright.model_run', 'careerwright.acquisition_run'));
GRANT SELECT (workflow_name) ON careerwright.outbox TO careerwright_worker;

CREATE TABLE careerwright.run_cancellations (
    run_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    requested_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    requested_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    signalled_at timestamptz,
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.run_cancellations IS
    'A request to cancel a run (DUR-05). Identifiers only; the worker reads them unscoped, '
    'cancels the workflow and publishes the run cancelled (signalled_at).';
ALTER TABLE careerwright.run_cancellations ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.run_cancellations TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY worker_dispatch ON careerwright.run_cancellations TO careerwright_worker USING (true);
GRANT SELECT, INSERT ON careerwright.run_cancellations TO careerwright_api;
GRANT SELECT ON careerwright.run_cancellations TO careerwright_worker;
GRANT UPDATE (signalled_at) ON careerwright.run_cancellations TO careerwright_worker;

CREATE TABLE careerwright.acquisition_targets (
    run_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    position smallint NOT NULL CHECK (position BETWEEN 0 AND 19),
    route text NOT NULL CHECK (route IN ('fetch', 'adzuna')),
    url text CHECK (char_length(url) <= 2048),
    query jsonb,
    status text NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'succeeded', 'blocked', 'failed', 'cancelled')),
    PRIMARY KEY (run_id, position),
    CONSTRAINT a_target_is_a_url_or_a_query
        CHECK ((route = 'fetch') = (url IS NOT NULL) AND (route = 'adzuna') = (query IS NOT NULL)),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);

CREATE TABLE careerwright.source_attempts (
    attempt_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    run_id uuid,
    position smallint,
    retry_of uuid REFERENCES careerwright.source_attempts (attempt_id) ON DELETE CASCADE,
    route text NOT NULL CHECK (route IN ('fetch', 'adzuna', 'pasted_text')),
    provider text NOT NULL CHECK (char_length(provider) BETWEEN 1 AND 253),
    requested_url text CHECK (char_length(requested_url) <= 2048),
    final_url text CHECK (char_length(final_url) <= 2048),
    redirects jsonb NOT NULL DEFAULT '[]',
    status text NOT NULL CHECK (status IN ('pending', 'succeeded', 'blocked', 'failed')),
    reason text CHECK (char_length(reason) <= 80),
    transient boolean NOT NULL DEFAULT false,
    http_status integer CHECK (http_status BETWEEN 100 AND 599),
    content_type text CHECK (char_length(content_type) <= 120),
    address text CHECK (char_length(address) <= 64),
    content_sha256 text CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    byte_count integer CHECK (byte_count >= 0),
    rights_class text CHECK (rights_class IN ('govuk', 'public-sector', 'course-provider',
        'professional-body', 'employer-posting', 'job-board', 'other')),
    rights_status text CHECK (char_length(rights_status) <= 2000),
    retention text CHECK (retention IN ('body', 'excerpts')),
    http_requests integer NOT NULL DEFAULT 0 CHECK (http_requests >= 0),
    -- Charged usage: Adzuna's free tier and page fetches cost nothing; null would be unknown.
    cost_nano_usd bigint DEFAULT 0 CHECK (cost_nano_usd >= 0),
    created_by uuid REFERENCES careerwright.actors (actor_id),
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    CONSTRAINT pending_attempts_are_unfinished CHECK ((status = 'pending') = (finished_at IS NULL)),
    CONSTRAINT pasted_text_is_its_own_route
        CHECK ((route = 'pasted_text') = (run_id IS NULL) AND (run_id IS NULL) = (position IS NULL)
               AND (route = 'pasted_text') = (created_by IS NOT NULL)),
    CONSTRAINT refusals_and_failures_say_why
        CHECK ((status IN ('blocked', 'failed')) = (reason IS NOT NULL)),
    CONSTRAINT a_success_has_its_hash CHECK (status <> 'succeeded' OR content_sha256 IS NOT NULL),
    CONSTRAINT retrieved_bodies_have_a_class
        CHECK (retention IS NULL OR route = 'pasted_text' OR rights_class IS NOT NULL),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE,
    FOREIGN KEY (run_id, position)
        REFERENCES careerwright.acquisition_targets (run_id, position) ON DELETE CASCADE
);
CREATE INDEX source_attempts_by_run ON careerwright.source_attempts (run_id, position, started_at);
CREATE INDEX source_attempts_by_url ON careerwright.source_attempts (workspace_id, requested_url);
COMMENT ON TABLE careerwright.source_attempts IS
    'Every try to obtain a source (spec section 18, SourceAttempt), blocked and failed ones '
    'included. A requested URL never carries a credential (Adzuna''s are left out).';

CREATE TABLE careerwright.source_documents (
    attempt_id uuid PRIMARY KEY REFERENCES careerwright.source_attempts ON DELETE CASCADE,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    key_version integer NOT NULL CHECK (key_version >= 1),
    nonce bytea NOT NULL CHECK (octet_length(nonce) = 12),
    ciphertext bytea NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
COMMENT ON TABLE careerwright.source_documents IS
    'A source body kept only where its rights class permits keeping it privately (session 1, '
    'H-06), sealed with kind, workspace and attempt as associated data.';

CREATE TABLE careerwright.jobs (
    job_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    -- A person's pasted example: a statement of interest, never a live vacancy (JOB-06).
    exemplar boolean NOT NULL,
    first_seen_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    last_success_at timestamptz,
    last_attempt_at timestamptz NOT NULL,
    closed_at timestamptz,
    UNIQUE (workspace_id, job_id),
    CONSTRAINT live_jobs_were_retrieved CHECK (exemplar = (last_success_at IS NULL))
);
COMMENT ON TABLE careerwright.jobs IS
    'A canonical vacancy: one or more source copies of it (JOB-02). Freshness runs from '
    'last_success_at; a failed refresh moves last_attempt_at only. An exemplar was pasted '
    'by the person and is never verified as live.';

CREATE TABLE careerwright.job_copies (
    copy_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    job_id uuid,
    attempt_id uuid NOT NULL REFERENCES careerwright.source_attempts ON DELETE CASCADE,
    provider text NOT NULL,
    source_job_id text CHECK (char_length(source_job_id) <= 200),
    facts jsonb NOT NULL,
    copy jsonb NOT NULL,
    extraction_error text CHECK (char_length(extraction_error) <= 120),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT only_clean_copies_are_published
        CHECK ((job_id IS NULL) = (extraction_error IS NOT NULL)),
    FOREIGN KEY (workspace_id, job_id)
        REFERENCES careerwright.jobs (workspace_id, job_id) ON DELETE CASCADE
);
CREATE INDEX job_copies_by_job ON careerwright.job_copies (job_id, created_at);
CREATE INDEX job_copies_by_workspace ON careerwright.job_copies (workspace_id);

CREATE TABLE careerwright.source_claims (
    claim_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    attempt_id uuid NOT NULL REFERENCES careerwright.source_attempts ON DELETE CASCADE,
    copy_id uuid NOT NULL REFERENCES careerwright.job_copies ON DELETE CASCADE,
    field text NOT NULL CHECK (char_length(field) <= 40),
    value jsonb,
    validation text NOT NULL CHECK (validation IN ('structured', 'user_supplied', 'quarantined')),
    issue text CHECK (char_length(issue) <= 120),
    span jsonb NOT NULL,
    retrieved_at timestamptz NOT NULL,
    published_on date,
    valid_until timestamptz,
    CONSTRAINT quarantined_claims_say_why CHECK ((validation = 'quarantined') = (issue IS NOT NULL))
);
CREATE INDEX source_claims_by_copy ON careerwright.source_claims (copy_id);
COMMENT ON TABLE careerwright.source_claims IS
    'One field value from one source with the span that supports it (spec section 18, '
    'SourceClaim). Only deterministic code approves a value; a quarantined one is never used.';

CREATE TABLE careerwright.job_favourites (
    workspace_id uuid NOT NULL,
    job_id uuid NOT NULL,
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, job_id),
    FOREIGN KEY (workspace_id, job_id)
        REFERENCES careerwright.jobs (workspace_id, job_id) ON DELETE CASCADE
);

ALTER TABLE careerwright.acquisition_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.source_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.source_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.job_copies ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.source_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.job_favourites ENABLE ROW LEVEL SECURITY;

-- API role: the owner's workspaces. It submits targets, records pasted text (its attempt,
-- sealed body, copy, job and claims) and favourites; it never reads a sealed nonce or body.
CREATE POLICY api_workspace ON careerwright.acquisition_targets TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.source_attempts TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.source_documents TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.jobs TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.job_copies TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.source_claims TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.job_favourites TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.acquisition_targets, careerwright.source_attempts,
    careerwright.jobs,
    careerwright.job_copies, careerwright.source_claims TO careerwright_api;
GRANT SELECT (attempt_id, workspace_id, content_sha256, key_version, created_at)
    ON careerwright.source_documents TO careerwright_api;
GRANT INSERT ON careerwright.source_documents TO careerwright_api;
GRANT SELECT, INSERT, DELETE ON careerwright.job_favourites TO careerwright_api;

-- Worker role: its run's targets; evidence only while the run's requester may act. It
-- reads the workspace's jobs and copies to deduplicate against them.
CREATE POLICY worker_run ON careerwright.acquisition_targets TO careerwright_worker
    USING (run_id = careerwright.current_run_id());
CREATE POLICY worker_authorised ON careerwright.source_attempts TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (workspace_id = careerwright.authorised_run_workspace()
                AND run_id = careerwright.current_run_id());
CREATE POLICY worker_authorised ON careerwright.source_documents TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (workspace_id = careerwright.authorised_run_workspace());
CREATE POLICY worker_authorised ON careerwright.jobs TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (workspace_id = careerwright.authorised_run_workspace());
CREATE POLICY worker_authorised ON careerwright.job_copies TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (workspace_id = careerwright.authorised_run_workspace());
CREATE POLICY worker_authorised ON careerwright.source_claims TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (workspace_id = careerwright.authorised_run_workspace());
GRANT SELECT ON careerwright.acquisition_targets TO careerwright_worker;
GRANT UPDATE (status) ON careerwright.acquisition_targets TO careerwright_worker;
GRANT SELECT, INSERT ON careerwright.source_attempts TO careerwright_worker;
GRANT UPDATE (final_url, redirects, status, reason, transient, http_status, content_type,
              address, content_sha256, byte_count, rights_class, rights_status, retention,
              http_requests, cost_nano_usd, finished_at)
    ON careerwright.source_attempts TO careerwright_worker;
GRANT SELECT (attempt_id, workspace_id, content_sha256, key_version, created_at)
    ON careerwright.source_documents TO careerwright_worker;
GRANT INSERT ON careerwright.source_documents TO careerwright_worker;
GRANT SELECT, INSERT ON careerwright.jobs, careerwright.job_copies, careerwright.source_claims TO
    careerwright_worker;
GRANT UPDATE (last_success_at, last_attempt_at, closed_at) ON careerwright.jobs TO
    careerwright_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
