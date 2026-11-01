"""The person's capability evidence, requirement statements and matrix edits (Task 9, S4.1-S4.6;
ADR 0012).

- `capability_states`: one row per workspace, the version every capability write takes as
  its expected version, and whether the person stopped (or paused) the questions.
- `skill_evidence`: the person's answers about a skill subject, kept apart: the level they
  give themselves, a level a reviewed demonstration or assessment showed, with recency,
  context, independence, tools and AI assistance. Unsure has no level; a self-report shows
  no demonstrated level; only an assessment closes a planned outcome.
- `requirement_statements`: whether the person holds a credential, experience or
  eligibility requirement, and whether they verified it. Only what is held is verified.
- `matrix_edits`: the person's importance edits and challenges at the checkpoint, with
  actor, reason and the old and new matrix and definition versions (MAP1-04).

The rows other than the state are append-only for the API role: a later answer supersedes
an earlier one, and history is kept. Every table is under row-level security by workspace.

Forward-only (see `docs/runbook.md`).

Revision ID: 0029
"""

from careerwright.migrations.sql import run_script

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE careerwright.capability_states (
    workspace_id uuid PRIMARY KEY REFERENCES careerwright.workspaces ON DELETE CASCADE,
    version integer NOT NULL CHECK (version >= 1),
    questions_stopped boolean NOT NULL,
    updated_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
COMMENT ON TABLE careerwright.capability_states IS
    'The version every capability write is checked against, and whether the person stopped '
    'the questions. No row: version 0, asking.';

CREATE TABLE careerwright.skill_evidence (
    evidence_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    state_version integer NOT NULL CHECK (state_version >= 1),
    subject text NOT NULL CHECK (char_length(subject) BETWEEN 1 AND 200),
    rubric_version text CHECK (char_length(rubric_version) BETWEEN 1 AND 200),
    answer text NOT NULL CHECK (answer IN (
        'done_independently', 'done_with_help', 'understand_not_tried', 'not_learned', 'unsure'
    )),
    self_assessed_level smallint CHECK (self_assessed_level BETWEEN 0 AND 4),
    example text CHECK (char_length(example) <= 1000),
    last_done text CHECK (last_done ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    context text CHECK (context IN ('paid_work', 'study', 'volunteering', 'caring', 'other')),
    independence text CHECK (independence IN ('independent', 'with_help')),
    complexity text CHECK (complexity IN ('routine', 'complex')),
    tools text CHECK (char_length(tools) <= 300),
    ai_assisted boolean,
    method text NOT NULL CHECK (method IN ('self_report', 'work_sample', 'assessment')),
    demonstrated_level smallint CHECK (demonstrated_level BETWEEN 0 AND 4),
    assessed_by text CHECK (char_length(assessed_by) <= 300),
    reviewed_on date,
    outcome_id text CHECK (char_length(outcome_id) <= 200),
    recorded_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unsure_is_not_a_level CHECK (answer <> 'unsure' OR self_assessed_level IS NULL),
    CONSTRAINT a_self_report_shows_nothing_demonstrated CHECK (
        method <> 'self_report'
        OR (demonstrated_level IS NULL AND reviewed_on IS NULL AND outcome_id IS NULL)
    ),
    CONSTRAINT a_demonstration_states_its_level CHECK (
        method = 'self_report' OR demonstrated_level IS NOT NULL
    ),
    CONSTRAINT only_an_assessment_closes_an_outcome CHECK (
        outcome_id IS NULL OR method = 'assessment'
    )
);
CREATE INDEX skill_evidence_by_workspace ON careerwright.skill_evidence (workspace_id, recorded_at);
COMMENT ON TABLE careerwright.skill_evidence IS
    'The person''s answers about a skill subject, shared across targets: a level counts only '
    'against the rubric it was given for. Append-only: a later answer supersedes.';

CREATE TABLE careerwright.requirement_statements (
    statement_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    state_version integer NOT NULL CHECK (state_version >= 1),
    subject text NOT NULL CHECK (char_length(subject) BETWEEN 1 AND 200),
    holding text NOT NULL CHECK (holding IN ('held', 'not_held', 'unknown')),
    verified boolean NOT NULL,
    verification_note text CHECK (char_length(verification_note) <= 300),
    recorded_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT only_what_is_held_is_verified CHECK (NOT verified OR holding = 'held')
);
CREATE INDEX requirement_statements_by_workspace
    ON careerwright.requirement_statements (workspace_id, recorded_at);
COMMENT ON TABLE careerwright.requirement_statements IS
    'Whether the person holds a credential, experience or eligibility requirement, and whether '
    'they verified it. A protected gate held but unverified stays unresolved.';

CREATE TABLE careerwright.matrix_edits (
    edit_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    state_version integer NOT NULL CHECK (state_version >= 1),
    target_key text NOT NULL CHECK (char_length(target_key) BETWEEN 1 AND 200),
    row_id text NOT NULL CHECK (char_length(row_id) BETWEEN 1 AND 300),
    action text NOT NULL CHECK (action IN ('set_importance', 'challenge')),
    importance text CHECK (importance IN ('essential', 'preferred', 'disputed', 'unknown')),
    reason text NOT NULL CHECK (char_length(reason) BETWEEN 1 AND 400),
    warning_acknowledged boolean NOT NULL,
    from_matrix_version text NOT NULL,
    from_definition_version text NOT NULL,
    to_matrix_version text NOT NULL,
    to_definition_version text NOT NULL,
    recorded_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT an_importance_edit_names_its_importance CHECK (
        (action = 'set_importance') = (importance IS NOT NULL)
    )
);
CREATE INDEX matrix_edits_by_target ON careerwright.matrix_edits (workspace_id, target_key,
    recorded_at);
COMMENT ON TABLE careerwright.matrix_edits IS
    'The person''s importance edits and challenges, with actor, reason and the old and new '
    'matrix and definition versions. A protected gate is never demoted (refused before any '
    'row is written).';
"""

POLICIES = """
ALTER TABLE careerwright.capability_states ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.capability_states TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.capability_states TO careerwright_api;
GRANT UPDATE (version, questions_stopped, updated_by, updated_at)
    ON careerwright.capability_states TO careerwright_api;

ALTER TABLE careerwright.skill_evidence ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.skill_evidence TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.skill_evidence TO careerwright_api;

ALTER TABLE careerwright.requirement_statements ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.requirement_statements TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.requirement_statements TO careerwright_api;

ALTER TABLE careerwright.matrix_edits ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.matrix_edits TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.matrix_edits TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA + POLICIES)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
