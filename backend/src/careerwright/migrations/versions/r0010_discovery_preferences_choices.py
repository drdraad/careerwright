"""Discovery runs, interview preferences and occupations chosen as targets (Task 6, S2.3-S2.4).

- A `discovery` run asks the model for search queries built from the confirmed profile
  (spec section 4, REC-1, DIV-1). Like an interview turn it pins the profile version it
  read and carries a sealed input, so the worker still never reads profile tables. A demo
  workspace's discovery uses the deterministic fixture proposer, never a provider model.
- `interview_preferences` holds how the person chose to start ("I know my direction" or
  "Help me explore"), the conversation mode (practical, gentle, challenge) and whether the
  interview is paused: one row per workspace, written with an expected version.
- An `occupation_choice` source records a target the person chose from the taxonomy (a
  suggestion or an ESCO occupation for an ambiguous title): its locator is the ESCO URI, and
  the discovery that suggested it, if any, is its run.

Forward-only (see `docs/runbook.md`).

Revision ID: 0010
"""

from careerwright.migrations.sql import run_script

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.runs DROP CONSTRAINT runs_kind_check;
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_kind_check
    CHECK (kind IN ('connection_check', 'interview_turn', 'discovery'));
ALTER TABLE careerwright.runs DROP CONSTRAINT the_fixture_model_only_interviews;
ALTER TABLE careerwright.runs ADD CONSTRAINT the_fixture_models_only_interview_or_discover
    CHECK (model_mode <> 'fixture' OR kind IN ('interview_turn', 'discovery'));
ALTER TABLE careerwright.runs DROP CONSTRAINT interview_turns_pin_the_profile_version;
ALTER TABLE careerwright.runs ADD CONSTRAINT profile_reading_runs_pin_the_profile_version
    CHECK ((kind IN ('interview_turn', 'discovery')) = (profile_version IS NOT NULL));

CREATE TABLE careerwright.interview_preferences (
    workspace_id uuid PRIMARY KEY REFERENCES careerwright.workspaces ON DELETE CASCADE,
    entry_mode text CHECK (entry_mode IN ('sure', 'unsure')),
    conversation_mode text CHECK (conversation_mode IN ('practical', 'gentle', 'challenge')),
    paused boolean NOT NULL,
    version integer NOT NULL CHECK (version >= 1),
    updated_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
COMMENT ON TABLE careerwright.interview_preferences IS
    'How the person chose to start and to be interviewed, and whether the interview is '
    'paused. Preferences, never profile facts or planning limits. NULL: not chosen yet.';
ALTER TABLE careerwright.interview_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.interview_preferences TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.interview_preferences TO careerwright_api;
GRANT UPDATE (entry_mode, conversation_mode, paused, version, updated_by, updated_at)
    ON careerwright.interview_preferences TO careerwright_api;

ALTER TABLE careerwright.source_references DROP CONSTRAINT source_references_kind_check;
ALTER TABLE careerwright.source_references ADD CONSTRAINT source_references_kind_check
    CHECK (kind IN ('direct_entry', 'fixture', 'conversation', 'occupation_choice'));
ALTER TABLE careerwright.source_references DROP CONSTRAINT only_conversation_sources_cite_messages;
ALTER TABLE careerwright.source_references ADD CONSTRAINT only_conversation_sources_cite_messages
    CHECK (
        kind = 'conversation' OR (
            message_ids IS NULL AND basis IS NULL
            AND (run_id IS NULL OR kind = 'occupation_choice')
        )
    );
ALTER TABLE careerwright.source_references ADD CONSTRAINT occupation_choices_name_the_occupation
    CHECK (kind <> 'occupation_choice' OR (locator IS NOT NULL AND recorded_by IS NOT NULL));
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
