"""Encrypted credentials, runs with a transactional outbox, model attempts and spend limits.

The worker role (`careerwright_worker`) gets its own row-level security, scoped by the run it is
executing (`careerwright.run_id`), so a worker can never read another workspace's rows:
- the run itself, its workspace row (for event numbering), its attempts and events are
  visible while the run exists;
- private material (the sealed credential and sealed outputs) is visible only while the
  run's requester still owns the workspace and is still invited
  (`careerwright.authorised_run_workspace()`), so revoking access stops the next call.
The outbox holds identifiers only and is the one table the dispatcher reads unscoped.

Forward-only (see `docs/runbook.md`: backup and restore are not implemented yet).

Revision ID: 0002
"""

from careerwright.migrations.sql import run_script

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE FUNCTION careerwright.current_run_id() RETURNS uuid
    LANGUAGE sql STABLE PARALLEL SAFE
    AS $$ SELECT nullif(current_setting('careerwright.run_id', true), '')::uuid $$;

-- A run records its workspace's data mode and synthetic label; this key makes the database
-- guarantee the copy matches (both are immutable on the workspace).
ALTER TABLE careerwright.workspaces
    ADD CONSTRAINT workspaces_mode_label_key UNIQUE (workspace_id, data_mode, synthetic);

CREATE TABLE careerwright.credentials (
    credential_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    provider text NOT NULL CHECK (provider = 'meta'),
    key_version integer NOT NULL CHECK (key_version >= 1),
    nonce bytea NOT NULL CHECK (octet_length(nonce) = 12),
    ciphertext bytea NOT NULL,
    consented_at timestamptz NOT NULL,
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revoked_by uuid REFERENCES careerwright.actors (actor_id),
    replaced_by uuid REFERENCES careerwright.credentials (credential_id),
    CONSTRAINT revocations_name_their_actor CHECK ((revoked_at IS NULL) = (revoked_by IS NULL))
);
CREATE UNIQUE INDEX credentials_one_active_per_provider
    ON careerwright.credentials (workspace_id, provider) WHERE revoked_at IS NULL;
COMMENT ON TABLE careerwright.credentials IS
    'AES-256-GCM under a versioned master key held outside the database; associated data '
    'binds kind, workspace and credential ID. The API role cannot read nonce or ciphertext.';

CREATE TABLE careerwright.spend_limits (
    workspace_id uuid PRIMARY KEY REFERENCES careerwright.workspaces ON DELETE CASCADE,
    run_limit_nano_usd bigint NOT NULL CHECK (run_limit_nano_usd >= 0),
    period_limit_nano_usd bigint NOT NULL CHECK (period_limit_nano_usd >= 0),
    version integer NOT NULL DEFAULT 1 CHECK (version >= 1),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE careerwright.runs (
    run_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    data_mode text NOT NULL,
    synthetic boolean NOT NULL,
    kind text NOT NULL CHECK (kind IN ('connection_check')),
    requested_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    model_id text NOT NULL,
    model_mode text NOT NULL CHECK (model_mode IN ('standard', 'contributor')),
    status text NOT NULL CHECK (
        status IN ('queued', 'running', 'complete', 'failed', 'provider_unavailable', 'cancelled')
    ),
    failure_class text,
    output_id uuid,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    started_at timestamptz,
    finished_at timestamptz,
    UNIQUE (workspace_id, run_id),
    FOREIGN KEY (workspace_id, data_mode, synthetic)
        REFERENCES careerwright.workspaces (workspace_id, data_mode, synthetic) ON DELETE CASCADE,
    CONSTRAINT contributor_models_only_for_synthetic_data
        CHECK (model_mode <> 'contributor' OR synthetic),
    CONSTRAINT demo_workspaces_never_call_a_model
        CHECK (data_mode <> 'demo' OR kind <> 'connection_check'),
    CONSTRAINT complete_runs_have_an_output CHECK ((status = 'complete') = (output_id IS NOT NULL)),
    CONSTRAINT failures_are_classified
        CHECK ((status IN ('failed', 'provider_unavailable')) = (failure_class IS NOT NULL)),
    CONSTRAINT terminal_runs_are_finished CHECK (
        (status IN ('complete', 'failed', 'provider_unavailable', 'cancelled'))
        = (finished_at IS NOT NULL)
    )
);

CREATE TABLE careerwright.run_outputs (
    output_id uuid PRIMARY KEY,
    run_id uuid NOT NULL UNIQUE,
    workspace_id uuid NOT NULL,
    key_version integer NOT NULL CHECK (key_version >= 1),
    nonce bytea NOT NULL CHECK (octet_length(nonce) = 12),
    ciphertext bytea NOT NULL,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.run_outputs IS
    'One accepted output per run (the first validated one). A re-executed activity reuses it.';
-- Deferred, so deleting a workspace (both rows in one cascade) checks only at commit.
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_output_fkey FOREIGN KEY (output_id)
    REFERENCES careerwright.run_outputs (output_id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE careerwright.outbox (
    outbox_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id uuid NOT NULL,
    run_id uuid NOT NULL UNIQUE,
    workflow_id text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    dispatched_at timestamptz,
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.outbox IS
    'Written in the same transaction as its run. Dispatch is at least once; the workflow ID '
    'makes the workflow start exactly once.';

CREATE TABLE careerwright.model_attempts (
    attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    model_id text NOT NULL,
    credential_id uuid,
    period_start date NOT NULL,
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    outcome text,
    reserved_nano_usd bigint NOT NULL DEFAULT 0 CHECK (reserved_nano_usd >= 0),
    cost_nano_usd bigint CHECK (cost_nano_usd >= 0),
    spend_state text NOT NULL CHECK (spend_state IN ('none', 'held', 'reconciled', 'unknown')),
    input_tokens integer CHECK (input_tokens >= 0),
    cached_input_tokens integer CHECK (cached_input_tokens >= 0),
    output_tokens integer CHECK (output_tokens >= 0),
    reasoning_tokens integer CHECK (reasoning_tokens >= 0),
    web_search_queries integer CHECK (web_search_queries >= 0),
    provider_response_id text,
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE,
    CONSTRAINT known_cost_only_when_reconciled
        CHECK ((spend_state = 'reconciled') = (cost_nano_usd IS NOT NULL)),
    CONSTRAINT held_spend_is_unfinished CHECK (spend_state <> 'held' OR finished_at IS NULL)
);
COMMENT ON TABLE careerwright.model_attempts IS
    'One row per provider call attempt, written before the call: the spend reservation and '
    'reconciliation record. Unknown cost stays unknown and keeps its reservation committed.';
CREATE INDEX model_attempts_period ON careerwright.model_attempts (workspace_id, period_start);

-- The run's workspace while the run exists, and only while its requester may still act.
CREATE FUNCTION careerwright.run_workspace() RETURNS uuid
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $$ SELECT r.workspace_id FROM careerwright.runs r WHERE r.run_id =
        careerwright.current_run_id() $$;
CREATE FUNCTION careerwright.authorised_run_workspace() RETURNS uuid
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $$
        SELECT r.workspace_id
        FROM careerwright.runs r
        JOIN careerwright.workspaces w ON w.workspace_id = r.workspace_id
        JOIN careerwright.actors a ON a.actor_id = r.requested_by
        WHERE r.run_id = careerwright.current_run_id()
          AND w.owner_actor_id = r.requested_by
          AND a.access = 'active'
    $$;
REVOKE ALL ON FUNCTION careerwright.current_run_id(), careerwright.run_workspace(),
    careerwright.authorised_run_workspace() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION careerwright.current_run_id(), careerwright.run_workspace(),
    careerwright.authorised_run_workspace() TO careerwright_worker;

ALTER TABLE careerwright.credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.spend_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.run_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.model_attempts ENABLE ROW LEVEL SECURITY;

-- API role: the owner's workspaces, as for every workspace-scoped table.
CREATE POLICY api_workspace ON careerwright.credentials TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.spend_limits TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.runs TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.run_outputs TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.outbox TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.model_attempts TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));

-- The API seals keys but never reads them back: no nonce or ciphertext.
GRANT SELECT (credential_id, workspace_id, provider, key_version, consented_at, created_by,
              created_at, revoked_at, revoked_by, replaced_by)
    ON careerwright.credentials TO careerwright_api;
GRANT INSERT ON careerwright.credentials TO careerwright_api;
GRANT UPDATE (revoked_at, revoked_by, replaced_by) ON careerwright.credentials TO careerwright_api;
GRANT SELECT, INSERT ON careerwright.spend_limits TO careerwright_api;
GRANT UPDATE (run_limit_nano_usd, period_limit_nano_usd, version, updated_at)
    ON careerwright.spend_limits TO careerwright_api;
GRANT SELECT, INSERT ON careerwright.runs, careerwright.outbox TO careerwright_api;
GRANT SELECT ON careerwright.run_outputs, careerwright.model_attempts TO careerwright_api;

-- Worker role: scoped by the run it executes.
CREATE POLICY worker_run ON careerwright.runs TO careerwright_worker
    USING (run_id = careerwright.current_run_id());
CREATE POLICY worker_run ON careerwright.workspaces TO careerwright_worker
    USING (workspace_id = careerwright.run_workspace());
CREATE POLICY worker_run ON careerwright.workspace_events TO careerwright_worker
    USING (workspace_id = careerwright.run_workspace())
    WITH CHECK (workspace_id = careerwright.run_workspace());
-- Reading the workspace's other attempts lets the reservation sum the period's spend;
-- writing is limited to the run being executed.
CREATE POLICY worker_read ON careerwright.model_attempts FOR SELECT TO careerwright_worker
    USING (run_id = careerwright.current_run_id() OR workspace_id =
        careerwright.authorised_run_workspace());
CREATE POLICY worker_insert ON careerwright.model_attempts FOR INSERT TO careerwright_worker
    WITH CHECK (run_id = careerwright.current_run_id());
CREATE POLICY worker_update ON careerwright.model_attempts FOR UPDATE TO careerwright_worker
    USING (run_id = careerwright.current_run_id());
CREATE POLICY worker_authorised ON careerwright.credentials FOR SELECT TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace());
CREATE POLICY worker_authorised ON careerwright.spend_limits TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace());
CREATE POLICY worker_authorised ON careerwright.run_outputs TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (workspace_id = careerwright.authorised_run_workspace());
CREATE POLICY worker_dispatch ON careerwright.outbox TO careerwright_worker USING (true);

GRANT SELECT (workspace_id, last_event_seq) ON careerwright.workspaces TO careerwright_worker;
GRANT UPDATE (last_event_seq) ON careerwright.workspaces TO careerwright_worker;
GRANT INSERT ON careerwright.workspace_events TO careerwright_worker;
GRANT SELECT ON careerwright.runs TO careerwright_worker;
GRANT UPDATE (status, failure_class, output_id, started_at, finished_at) ON careerwright.runs
    TO careerwright_worker;
GRANT SELECT ON careerwright.credentials, careerwright.spend_limits TO careerwright_worker;
GRANT SELECT, INSERT ON careerwright.run_outputs TO careerwright_worker;
GRANT SELECT, INSERT ON careerwright.model_attempts TO careerwright_worker;
GRANT UPDATE (finished_at, outcome, cost_nano_usd, spend_state, input_tokens,
              cached_input_tokens, output_tokens, reasoning_tokens, web_search_queries,
              provider_response_id) ON careerwright.model_attempts TO careerwright_worker;
GRANT SELECT (outbox_id, workflow_id, run_id, dispatched_at) ON careerwright.outbox TO
    careerwright_worker;
GRANT UPDATE (dispatched_at) ON careerwright.outbox TO careerwright_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; restore a backup instead")
