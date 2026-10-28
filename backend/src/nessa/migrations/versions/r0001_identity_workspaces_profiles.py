"""Identity, workspaces, versioned profiles, source references, events and command receipts.

Ownership is enforced by PostgreSQL row-level security for the non-owner runtime role
`nessa_api` (Global Constraint 7, ADR 0002 decision 2): a transaction sets `nessa.actor_id`
and sees only the workspaces that actor owns, and only while the actor's invitation is
active. Every workspace-scoped table filters through the `workspaces` policy, so a missing
WHERE clause in application code cannot reach another workspace. The migration owner
(`nessa_migrator`) owns every object and is used only by setup.

Forward-only (see `docs/runbook.md`: backup and restore are not implemented yet).

Revision ID: 0001
"""

from nessa.migrations.sql import run_script

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = """
CREATE SCHEMA nessa;
REVOKE ALL ON SCHEMA nessa FROM PUBLIC;
GRANT USAGE ON SCHEMA nessa TO nessa_api, nessa_worker;

CREATE FUNCTION nessa.current_actor_id() RETURNS uuid
    LANGUAGE sql STABLE PARALLEL SAFE
    AS $$ SELECT nullif(current_setting('nessa.actor_id', true), '')::uuid $$;

CREATE TABLE nessa.actors (
    actor_id uuid PRIMARY KEY,
    email text NOT NULL UNIQUE CHECK (email = lower(email) AND email LIKE '%_@_%'),
    firebase_uid text UNIQUE,
    display_name text NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120),
    access text NOT NULL CHECK (access IN ('active', 'revoked')),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
COMMENT ON TABLE nessa.actors IS
    'The invitation allowlist. firebase_uid is bound at the first verified sign-in.';

CREATE TABLE nessa.workspaces (
    workspace_id uuid PRIMARY KEY,
    owner_actor_id uuid NOT NULL REFERENCES nessa.actors (actor_id),
    name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
    data_mode text NOT NULL CHECK (data_mode IN ('demo', 'live_assisted', 'live_vacancy')),
    synthetic boolean NOT NULL,
    fixture_key text UNIQUE,
    version integer NOT NULL DEFAULT 1 CHECK (version >= 1),
    last_event_seq bigint NOT NULL DEFAULT 0 CHECK (last_event_seq >= 0),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT demo_is_synthetic CHECK (data_mode <> 'demo' OR synthetic),
    CONSTRAINT fixture_is_demo CHECK (fixture_key IS NULL OR data_mode = 'demo')
);
COMMENT ON COLUMN nessa.workspaces.synthetic IS
    'Persistent synthetic-data label (GC5); immutable after creation.';

CREATE TABLE nessa.source_references (
    source_ref_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES nessa.workspaces ON DELETE CASCADE,
    kind text NOT NULL CHECK (kind IN ('direct_entry', 'fixture')),
    label text NOT NULL CHECK (char_length(label) BETWEEN 1 AND 200),
    locator text,
    content_sha256 text CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    recorded_by uuid REFERENCES nessa.actors (actor_id),
    observed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (workspace_id, source_ref_id),
    CONSTRAINT fixture_sources_are_pinned
        CHECK ((kind = 'fixture') = (locator IS NOT NULL AND content_sha256 IS NOT NULL)),
    CONSTRAINT direct_entries_name_their_actor
        CHECK (kind <> 'direct_entry' OR recorded_by IS NOT NULL)
);

CREATE TABLE nessa.profile_versions (
    workspace_id uuid NOT NULL REFERENCES nessa.workspaces ON DELETE CASCADE,
    version integer NOT NULL CHECK (version >= 1),
    schema_version text NOT NULL,
    document jsonb NOT NULL,
    created_by uuid REFERENCES nessa.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, version)
);
COMMENT ON TABLE nessa.profile_versions IS
    'Append-only. A write inserts expected_version + 1; the primary key rejects a stale write.';

CREATE TABLE nessa.profile_version_sources (
    workspace_id uuid NOT NULL,
    version integer NOT NULL,
    source_ref_id uuid NOT NULL,
    PRIMARY KEY (workspace_id, version, source_ref_id),
    FOREIGN KEY (workspace_id, version)
        REFERENCES nessa.profile_versions (workspace_id, version) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, source_ref_id)
        REFERENCES nessa.source_references (workspace_id, source_ref_id) ON DELETE CASCADE
);

CREATE TABLE nessa.workspace_events (
    workspace_id uuid NOT NULL REFERENCES nessa.workspaces ON DELETE CASCADE,
    seq bigint NOT NULL CHECK (seq >= 1),
    kind text NOT NULL,
    subject_id text NOT NULL,
    state text,
    detail jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, seq)
);
COMMENT ON TABLE nessa.workspace_events IS
    'Status stream. seq comes from workspaces.last_event_seq under the row lock, so it '
    'increases in commit order and a reconnect from Last-Event-ID misses nothing.';

CREATE TABLE nessa.command_receipts (
    actor_id uuid NOT NULL REFERENCES nessa.actors (actor_id),
    idempotency_key uuid NOT NULL,
    command text NOT NULL,
    request_sha256 text NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
    status_code integer NOT NULL,
    response jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (actor_id, idempotency_key)
);

-- Row-level security for the API role.
ALTER TABLE nessa.actors ENABLE ROW LEVEL SECURITY;
ALTER TABLE nessa.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE nessa.source_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE nessa.profile_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE nessa.profile_version_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE nessa.workspace_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE nessa.command_receipts ENABLE ROW LEVEL SECURITY;

CREATE POLICY api_self ON nessa.actors FOR SELECT TO nessa_api
    USING (actor_id = nessa.current_actor_id());

CREATE POLICY api_owner ON nessa.workspaces TO nessa_api
    USING (
        owner_actor_id = nessa.current_actor_id()
        AND EXISTS (SELECT 1 FROM nessa.actors a
                    WHERE a.actor_id = nessa.current_actor_id() AND a.access = 'active')
    )
    WITH CHECK (
        owner_actor_id = nessa.current_actor_id()
        AND EXISTS (SELECT 1 FROM nessa.actors a
                    WHERE a.actor_id = nessa.current_actor_id() AND a.access = 'active')
    );

CREATE POLICY api_workspace ON nessa.source_references TO nessa_api
    USING (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w));
CREATE POLICY api_workspace ON nessa.profile_versions TO nessa_api
    USING (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w));
CREATE POLICY api_workspace ON nessa.profile_version_sources TO nessa_api
    USING (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w));
CREATE POLICY api_workspace ON nessa.workspace_events TO nessa_api
    USING (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM nessa.workspaces w));
CREATE POLICY api_self ON nessa.command_receipts TO nessa_api
    USING (actor_id = nessa.current_actor_id())
    WITH CHECK (actor_id = nessa.current_actor_id());

-- Least-privilege grants. Profile versions, sources and events are append-only.
GRANT SELECT ON nessa.actors TO nessa_api;
GRANT SELECT, INSERT ON nessa.workspaces TO nessa_api;
GRANT UPDATE (name, version, updated_at, last_event_seq) ON nessa.workspaces TO nessa_api;
GRANT SELECT, INSERT ON nessa.source_references, nessa.profile_versions,
    nessa.profile_version_sources, nessa.workspace_events, nessa.command_receipts
    TO nessa_api;

-- Sign-in: map a verified Firebase identity to an invited actor. SECURITY DEFINER, because
-- the API cannot read the allowlist before it knows who is asking. Binding happens once;
-- afterwards a different Firebase account with the same email is refused.
CREATE FUNCTION nessa.resolve_actor(p_firebase_uid text, p_email text)
    RETURNS TABLE (actor_id uuid, access text, display_name text)
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp
    AS $$
DECLARE
    invited nessa.actors%ROWTYPE;
BEGIN
    SELECT * INTO invited FROM nessa.actors a WHERE a.email = lower(p_email) FOR UPDATE;
    IF NOT FOUND THEN
        RETURN;
    END IF;
    IF invited.firebase_uid IS NULL THEN
        IF EXISTS (SELECT 1 FROM nessa.actors a WHERE a.firebase_uid = p_firebase_uid) THEN
            RETURN;
        END IF;
        UPDATE nessa.actors SET firebase_uid = p_firebase_uid
            WHERE nessa.actors.actor_id = invited.actor_id;
    ELSIF invited.firebase_uid <> p_firebase_uid THEN
        RETURN;
    END IF;
    RETURN QUERY SELECT invited.actor_id, invited.access, invited.display_name;
END
$$;
REVOKE ALL ON FUNCTION nessa.resolve_actor(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION nessa.resolve_actor(text, text) TO nessa_api;
REVOKE ALL ON FUNCTION nessa.current_actor_id() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION nessa.current_actor_id() TO nessa_api, nessa_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; restore a backup instead")
