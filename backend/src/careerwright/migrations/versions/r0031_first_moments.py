"""The first moments in the world (Task W2, slice W2B; plan section 4, Sprint W SW.5; ADR 0007
decision 13, ADR 0012 decision 5, ADR 0014 decision 3).

- `occupation_labels_words`: the first question's type-ahead matches the words of ESCO's
  preferred and alternative labels as typed (each word a prefix), so it answers at once.
- `skill_evidence.answer` gains `used`: "I've used this", the person's own claim about a
  skill, with no level (a level is chosen against a rubric). Self-reported, never evidenced:
  it counts for nothing towards readiness.
- `strength_proposal` runs are model-backed runs on the one bounded activity: from the
  answers a conversation turn added, the model may propose one overlooked strength (a
  quotation of the person's own words against an essential skill of one of their
  destinations), which code verifies. Like a slate explanation it pins the profile version
  it read and carries a sealed input, so the worker never reads profile or taxonomy tables;
  a demo workspace's uses the deterministic fixture model.
- `strength_proposals` links the run to its turn: at most one per turn.
  `strength_decisions` holds the person's decision on it, at most one: a confirmation names
  the self-report it recorded; declining records nothing about the skill.

Forward-only (see `docs/runbook.md`).

Revision ID: 0031
"""

from careerwright.migrations.sql import run_script

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE INDEX occupation_labels_words ON careerwright.occupation_labels
    USING gin (to_tsvector('simple', label)) WHERE kind <> 'hidden';

ALTER TABLE careerwright.skill_evidence DROP CONSTRAINT skill_evidence_answer_check;
ALTER TABLE careerwright.skill_evidence ADD CONSTRAINT skill_evidence_answer_check CHECK (
    answer IN ('done_independently', 'done_with_help', 'understand_not_tried', 'not_learned',
               'unsure', 'used')
);
ALTER TABLE careerwright.skill_evidence ADD CONSTRAINT used_is_a_claim_without_a_level CHECK (
    answer <> 'used' OR (self_assessed_level IS NULL AND method = 'self_report')
);

ALTER TABLE careerwright.runs DROP CONSTRAINT runs_kind_check;
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_kind_check CHECK (
    kind IN ('connection_check', 'interview_turn', 'discovery', 'slate_explanation',
             'acquisition', 'source_search', 'page_extraction', 'strength_proposal')
);
ALTER TABLE careerwright.runs DROP CONSTRAINT the_fixture_models_only_interview_discover_or_explain;
ALTER TABLE careerwright.runs ADD CONSTRAINT the_fixture_models_only_profile_runs CHECK (
    model_mode <> 'fixture'
    OR kind IN ('interview_turn', 'discovery', 'slate_explanation', 'strength_proposal')
);
ALTER TABLE careerwright.runs DROP CONSTRAINT profile_reading_runs_pin_the_profile_version;
ALTER TABLE careerwright.runs ADD CONSTRAINT profile_reading_runs_pin_the_profile_version CHECK (
    (kind IN ('interview_turn', 'discovery', 'slate_explanation', 'source_search',
              'strength_proposal'))
    = (profile_version IS NOT NULL)
);

CREATE TABLE careerwright.strength_proposals (
    strength_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    turn_id uuid NOT NULL UNIQUE,
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT a_strength_is_not_its_turn CHECK (strength_id <> turn_id),
    FOREIGN KEY (workspace_id, strength_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id, turn_id)
        REFERENCES careerwright.interview_turns (workspace_id, turn_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.strength_proposals IS
    'An overlooked-strength run and the conversation turn whose added answers it read: '
    'strength_id is the run. At most one per turn. Append-only.';

CREATE TABLE careerwright.strength_decisions (
    strength_id uuid PRIMARY KEY REFERENCES careerwright.strength_proposals ON DELETE CASCADE,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    decision text NOT NULL CHECK (decision IN ('confirmed', 'declined')),
    evidence_id uuid REFERENCES careerwright.skill_evidence ON DELETE CASCADE,
    decided_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT only_a_confirmation_records_the_skill CHECK (
        (evidence_id IS NOT NULL) = (decision = 'confirmed')
    )
);
COMMENT ON TABLE careerwright.strength_decisions IS
    'The person''s decision on a proposed strength, at most one: a confirmation names the '
    'self-report it recorded; declining records nothing about the skill. Append-only.';

ALTER TABLE careerwright.strength_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.strength_decisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.strength_proposals TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.strength_decisions TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.strength_proposals, careerwright.strength_decisions TO
    careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
