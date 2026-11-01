"""The person's planning inputs, stored and confirmed (Task 12a; ADR 0013 decision 11 and its
amendment of 2026-10-31).

- `planning_input_versions`: append-only versions of one document per workspace, the person's
  money and time (the baseline, the continuation, opening cash, living costs, the reserve, the
  deficit cap, availability, commitments, existing debts, the objective basis, the delay
  months), their work rights and remote working, their answers about each option (work
  pattern, wage, supports and their stacking, eligibility conditions, entry confirmation),
  the places and offers they hold, and their outcome decisions. A write inserts
  `expected_version + 1`; the primary key refuses a stale write.

The CHECKs repeat the domain rules (`careerwright.planning.inputs`): money is GBP and never
negative, hours stay within a week, the delay is one to 24 months, work rights take one of
their three answers, remote work names an England employer and its zone and nothing
otherwise, a support is never a loan or a programme and an approval needs confirmed
eligibility, and an outcome decision is an acceptance or an override. Under row-level security
by workspace; append-only for the API role.

Forward-only (see `docs/runbook.md`).

Revision ID: 0033
"""

from careerwright.migrations.sql import run_script

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

SCHEMA = """
CREATE TABLE careerwright.planning_input_versions (
    workspace_id uuid NOT NULL REFERENCES careerwright.workspaces ON DELETE CASCADE,
    version integer NOT NULL CHECK (version >= 1),
    schema_version text NOT NULL CHECK (schema_version = '1'),
    document jsonb NOT NULL CHECK (jsonb_typeof(document) = 'object'),
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (workspace_id, version),
    CONSTRAINT the_document_names_its_schema CHECK (document->>'schema_version' = schema_version),
    CONSTRAINT money_is_gbp_and_never_negative CHECK (
        NOT jsonb_path_exists(document, 'lax $.** ? (@.minor_units < 0)')
        AND NOT jsonb_path_exists(
            document, 'lax $.** ? (exists(@.minor_units) && @.currency != "GBP")'
        )
    ),
    CONSTRAINT hours_fit_in_a_week CHECK (
        NOT jsonb_path_exists(
            document, 'lax $.** ? (@.hours_per_week < 0 || @.hours_per_week > 168)'
        )
        AND NOT jsonb_path_exists(document, '$.weekly_availability ? (@ < 0 || @ > 168)')
    ),
    CONSTRAINT the_delay_is_within_the_horizon CHECK (
        NOT jsonb_path_exists(document, '$.scenario_delay_months ? (@ < 1 || @ > 24)')
    ),
    CONSTRAINT work_rights_are_one_answer CHECK (
        coalesce(document->>'work_rights', 'held') IN ('held', 'not_held', 'unknown')
    ),
    CONSTRAINT remote_work_is_england_based CHECK (
        jsonb_typeof(document->'remote_work') IS DISTINCT FROM 'object'
        OR (
            (document->'remote_work'->>'works_remotely')::boolean
            AND document->'remote_work'->>'employment_country' = 'GB-ENG'
            AND document->'remote_work'->>'timezone' = 'Europe/London'
        )
        OR (
            NOT (document->'remote_work'->>'works_remotely')::boolean
            AND document->'remote_work'->>'employment_country' IS NULL
            AND document->'remote_work'->>'timezone' IS NULL
        )
    ),
    CONSTRAINT supports_are_non_repayable_and_approved_only_if_eligible CHECK (
        NOT jsonb_path_exists(
            document,
            'lax $.variants[*].supports[*] ? (@.kind == "loan" || @.kind == "programme"'
            ' || (@.award == "approved" && @.eligibility != "confirmed"))'
        )
    ),
    CONSTRAINT an_outcome_decision_accepts_or_overrides CHECK (
        NOT jsonb_path_exists(
            document,
            'lax $.outcome_decisions[*] ? (@.decision != "accept" && @.decision != "override")'
        )
    )
);
COMMENT ON TABLE careerwright.planning_input_versions IS
    'The person''s planning inputs. Append-only: a write inserts expected_version + 1, so the '
    'primary key refuses a stale write. Not yet stated is null, never 0.';
"""

POLICIES = """
ALTER TABLE careerwright.planning_input_versions ENABLE ROW LEVEL SECURITY;
CREATE POLICY api_workspace ON careerwright.planning_input_versions TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.planning_input_versions TO careerwright_api;
"""


def upgrade() -> None:
    run_script(SCHEMA + POLICIES)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
