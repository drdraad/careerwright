"""Interview turns: a run kind that reads the profile, sealed run inputs, conversation
sources, and the person's decisions on proposals.

- `interview_turn` runs pin the profile version they read (ADR 0004 decision 7) and carry a
  sealed input (the minimum profile subset and the recent messages), so the worker still
  never reads profile or conversation tables. The input is visible to the worker only while
  the requester may act, like keys and outputs.
- A demo workspace's run uses the fixture interviewer and nothing else, and the fixture
  interviewer answers demo workspaces only (`(data_mode = 'demo') = (model_mode =
  'fixture')`); it replaces the rule that demo workspaces never run.
- An attempt records how many provider requests it sent (a validation repair is a second).
- A conversation source names the turn that proposed the answer, the person's messages it
  cites, its basis (stated or inferred) and who confirmed it (PROF-01, PROF-05).
- `interview_turns` holds each message with the version it was written against;
  `interview_decisions` holds at most one decision per turn. Both are append-only.

Forward-only (see `docs/runbook.md`).

Revision ID: 0005
"""

from careerwright.migrations.sql import run_script

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.runs DROP CONSTRAINT runs_kind_check;
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_kind_check
    CHECK (kind IN ('connection_check', 'interview_turn'));
ALTER TABLE careerwright.runs DROP CONSTRAINT runs_model_mode_check;
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_model_mode_check
    CHECK (model_mode IN ('standard', 'contributor', 'fixture'));
ALTER TABLE careerwright.runs DROP CONSTRAINT demo_workspaces_never_call_a_model;
ALTER TABLE careerwright.runs ADD CONSTRAINT demo_workspaces_use_only_the_fixture_model
    CHECK ((data_mode = 'demo') = (model_mode = 'fixture'));
ALTER TABLE careerwright.runs ADD CONSTRAINT the_fixture_model_only_interviews
    CHECK (model_mode <> 'fixture' OR kind = 'interview_turn');
ALTER TABLE careerwright.runs ADD COLUMN profile_version integer CHECK (profile_version >= 0);
ALTER TABLE careerwright.runs ADD CONSTRAINT interview_turns_pin_the_profile_version
    CHECK ((kind = 'interview_turn') = (profile_version IS NOT NULL));

ALTER TABLE careerwright.model_attempts ADD COLUMN requests_sent integer CHECK (requests_sent >= 0);
GRANT UPDATE (requests_sent) ON careerwright.model_attempts TO careerwright_worker;

CREATE TABLE careerwright.run_inputs (
    run_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    key_version integer NOT NULL CHECK (key_version >= 1),
    nonce bytea NOT NULL CHECK (octet_length(nonce) = 12),
    ciphertext bytea NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.run_inputs IS
    'A run''s private input, sealed by the API at submission with the run as associated '
    'data and opened only inside the worker''s activity.';
ALTER TABLE careerwright.run_inputs ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.run_inputs TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY worker_authorised ON careerwright.run_inputs FOR SELECT TO careerwright_worker
    USING (workspace_id = careerwright.authorised_run_workspace());
GRANT INSERT ON careerwright.run_inputs TO careerwright_api;
GRANT SELECT ON careerwright.run_inputs TO careerwright_worker;

ALTER TABLE careerwright.source_references DROP CONSTRAINT source_references_kind_check;
ALTER TABLE careerwright.source_references ADD CONSTRAINT source_references_kind_check
    CHECK (kind IN ('direct_entry', 'fixture', 'conversation'));
ALTER TABLE careerwright.source_references
    ADD COLUMN run_id uuid,
    ADD COLUMN message_ids uuid[],
    ADD COLUMN basis text CHECK (basis IN ('stated', 'inferred')),
    ADD CONSTRAINT source_runs_belong_to_the_workspace FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE,
    ADD CONSTRAINT conversation_sources_are_complete CHECK (
        kind <> 'conversation' OR (
            run_id IS NOT NULL AND cardinality(message_ids) >= 1 AND basis IS NOT NULL
            AND recorded_by IS NOT NULL
        )
    ),
    ADD CONSTRAINT only_conversation_sources_cite_messages CHECK (
        kind = 'conversation' OR (run_id IS NULL AND message_ids IS NULL AND basis IS NULL)
    );

CREATE TABLE careerwright.interview_turns (
    turn_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    message_id uuid NOT NULL UNIQUE,
    message text NOT NULL CHECK (char_length(message) BETWEEN 1 AND 2000),
    profile_version integer NOT NULL CHECK (profile_version >= 0),
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (workspace_id, turn_id),
    FOREIGN KEY (workspace_id, turn_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.interview_turns IS
    'One person message per turn; turn_id is the interview run. Append-only.';
CREATE INDEX interview_turns_by_time ON careerwright.interview_turns (workspace_id, created_at);

CREATE TABLE careerwright.interview_decisions (
    turn_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    decided_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    accepted_change_ids text[] NOT NULL,
    rejected_change_ids text[] NOT NULL,
    confirmed_hard_constraints text[] NOT NULL,
    profile_version integer,
    FOREIGN KEY (workspace_id, turn_id)
        REFERENCES careerwright.interview_turns (workspace_id, turn_id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, profile_version)
        REFERENCES careerwright.profile_versions (workspace_id, version) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.interview_decisions IS
    'The person''s decision on a turn''s proposals: which they accepted and confirmed, and '
    'the profile version that created (NULL when it changed nothing). At most one per turn.';

ALTER TABLE careerwright.interview_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.interview_decisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.interview_turns TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.interview_decisions TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.interview_turns, careerwright.interview_decisions TO
    careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
