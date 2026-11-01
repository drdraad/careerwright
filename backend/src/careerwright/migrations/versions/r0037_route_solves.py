"""The route search as a run (Task 13b; plan Sprint 6b, S6.3, S6.4, S6.8; ADR 0016's Task 13b
amendment; the L0 deferrals in the specification's section 22).

- `route_solve` runs call no model, so they name none, like an acquisition. They read the
  profile's spending caps, so they pin the profile version they read; they carry a sealed
  input, the immutable snapshot the search reads (the person's planning inputs, the target's
  options and its readiness basis, compiled once at submission); and they run in their own
  workflow (`outbox.workflow_name`). They need no route out, so demo workspaces may run them.
- `route_solves`: one per run, the solve as it was asked for. Its identity (`solve_id`) comes
  from the snapshot and the limits, so the same solve asked twice while one is unsettled
  joins it. It names the target, the planning inputs and capability versions read, the
  monthly input's version, the comparison's start and horizon, and every limit: the M0
  search limits (spec section 18, `M0SearchLimits`) and the rank stage's own.
- `route_solve_attempts`: each execution of a solve. L0 keeps no checkpoint (spec section 22),
  so a crashed attempt is `interrupted`, never a truncated result, and the solve starts again
  under a new attempt ID; a run makes at most three. `stage` is where a running attempt is:
  searching, or ranking (the rank stage is its own, observable stage).
- `route_solve_results`: the stored result's facts, once, beside its sealed output (the whole
  ranked archive). The CHECKs repeat the search's rules (`careerwright.planning.search`): a
  stopped search names its limit and is never complete; only a complete search has exact
  layers, proves no route, or is unresolved; a stopped one with nothing found found none
  before its limit; routes are found exactly when something was archived; and the caps bound
  the counts.

The worker writes a solve's attempts and result only for the run it executes (and its result
only while the run's requester may act); the API records the solve and reads the rest.
Forward-only (see `docs/runbook.md`).

Revision ID: 0037
"""

from careerwright.migrations.sql import run_script

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE careerwright.runs DROP CONSTRAINT runs_kind_check;
ALTER TABLE careerwright.runs ADD CONSTRAINT runs_kind_check CHECK (
    kind IN ('connection_check', 'interview_turn', 'discovery', 'slate_explanation',
             'acquisition', 'source_search', 'page_extraction', 'strength_proposal',
             'route_solve')
);
ALTER TABLE careerwright.runs DROP CONSTRAINT only_acquisitions_name_no_model;
ALTER TABLE careerwright.runs ADD CONSTRAINT only_keyless_runs_name_no_model
    CHECK ((model_id IS NULL) = (kind IN ('acquisition', 'route_solve'))
           AND (model_mode IS NULL) = (model_id IS NULL));
ALTER TABLE careerwright.runs DROP CONSTRAINT profile_reading_runs_pin_the_profile_version;
ALTER TABLE careerwright.runs ADD CONSTRAINT profile_reading_runs_pin_the_profile_version CHECK (
    (kind IN ('interview_turn', 'discovery', 'slate_explanation', 'source_search',
              'strength_proposal', 'route_solve'))
    = (profile_version IS NOT NULL)
);
ALTER TABLE careerwright.outbox DROP CONSTRAINT outbox_workflow_name_check;
ALTER TABLE careerwright.outbox ADD CONSTRAINT outbox_workflow_name_check CHECK (
    workflow_name IN ('careerwright.model_run', 'careerwright.acquisition_run',
                      'careerwright.route_solve')
);

CREATE TABLE careerwright.route_solves (
    run_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    solve_id text NOT NULL CHECK (solve_id ~ '^solve:[0-9a-f]{16}$'),
    target_title text NOT NULL CHECK (length(target_title) BETWEEN 1 AND 200),
    inputs_version integer NOT NULL CHECK (inputs_version >= 1),
    capability_version integer NOT NULL CHECK (capability_version >= 0),
    input_version text NOT NULL CHECK (input_version ~ '^monthly-input:[0-9a-f]{16}$'),
    planning_start date NOT NULL CHECK (extract(day FROM planning_start) = 1),
    horizon_months integer NOT NULL CHECK (horizon_months BETWEEN 1 AND 24),
    objective_basis text NOT NULL CHECK (objective_basis IN ('economic', 'direct_spending')),
    max_actions integer NOT NULL CHECK (max_actions BETWEEN 1 AND 24),
    max_starts_per_action integer NOT NULL CHECK (max_starts_per_action BETWEEN 1 AND 2),
    max_selected_actions integer NOT NULL CHECK (max_selected_actions BETWEEN 0 AND 6),
    max_months integer NOT NULL CHECK (max_months BETWEEN 1 AND 24),
    wall_seconds integer NOT NULL CHECK (wall_seconds BETWEEN 1 AND 30),
    max_states integer NOT NULL CHECK (max_states BETWEEN 1 AND 1000000),
    max_feasible_archive integer NOT NULL CHECK (max_feasible_archive BETWEEN 1 AND 50000),
    rank_seconds integer NOT NULL CHECK (rank_seconds >= 1),
    algorithm_version text NOT NULL CHECK (length(algorithm_version) BETWEEN 1 AND 100),
    pruning_version text NOT NULL CHECK (length(pruning_version) BETWEEN 1 AND 100),
    created_by uuid NOT NULL REFERENCES careerwright.actors (actor_id),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (workspace_id, run_id),
    CONSTRAINT the_horizon_is_within_the_declared_model CHECK (horizon_months <= max_months),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.runs (workspace_id, run_id) ON DELETE CASCADE
);
CREATE INDEX route_solves_by_identity ON careerwright.route_solves (workspace_id, solve_id);
COMMENT ON TABLE careerwright.route_solves IS
    'A route solve as asked for: its identity, the versions its sealed snapshot read, the '
    'comparison''s start and horizon, and every limit. One per run; append-only.';

CREATE TABLE careerwright.route_solve_attempts (
    attempt_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    stage text NOT NULL DEFAULT 'searching' CHECK (stage IN ('searching', 'ranking')),
    outcome text CHECK (
        outcome IN ('succeeded', 'interrupted', 'cancelled', 'rank_limit_reached', 'failed')
    ),
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    UNIQUE (run_id, attempt_id),
    CONSTRAINT a_finished_attempt_says_how_it_ended
        CHECK ((outcome IS NULL) = (finished_at IS NULL)),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.route_solves (workspace_id, run_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.route_solve_attempts IS
    'Each execution of a route solve. A crashed one is interrupted, never a truncated result: '
    'the solve starts again under a new attempt ID.';

CREATE TABLE careerwright.route_solve_results (
    run_id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL,
    attempt_id bigint NOT NULL,
    output_id uuid NOT NULL UNIQUE REFERENCES careerwright.run_outputs (output_id)
        ON DELETE CASCADE,
    coverage text NOT NULL CHECK (coverage IN ('complete', 'budget_truncated')),
    stop_reason text CHECK (stop_reason IN ('state_limit', 'wall_time_limit', 'archive_limit')),
    outcome text NOT NULL CHECK (
        outcome IN ('routes_found', 'none_found_before_limit', 'unresolved',
                    'no_route_in_bounded_model')
    ),
    layers_exact boolean NOT NULL,
    expanded_states integer NOT NULL CHECK (expanded_states BETWEEN 0 AND 1000000),
    archived integer NOT NULL CHECK (archived BETWEEN 0 AND 50000),
    unexplored_branches integer NOT NULL CHECK (unexplored_branches >= 0),
    search_ms integer NOT NULL CHECK (search_ms >= 0),
    rank_ms integer NOT NULL CHECK (rank_ms >= 0),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT a_stopped_search_names_its_limit
        CHECK ((coverage = 'complete') = (stop_reason IS NULL)),
    CONSTRAINT layers_are_exact_only_when_complete CHECK (layers_exact = (coverage = 'complete')),
    CONSTRAINT routes_are_found_exactly_when_archived
        CHECK ((outcome = 'routes_found') = (archived > 0)),
    CONSTRAINT only_a_complete_search_proves_no_route_or_is_unresolved CHECK (
        outcome NOT IN ('no_route_in_bounded_model', 'unresolved') OR coverage = 'complete'
    ),
    CONSTRAINT a_stopped_empty_search_found_none_before_its_limit
        CHECK (outcome <> 'none_found_before_limit' OR coverage = 'budget_truncated'),
    CONSTRAINT a_complete_search_left_nothing_unexplored
        CHECK (coverage <> 'complete' OR unexplored_branches = 0),
    FOREIGN KEY (workspace_id, run_id)
        REFERENCES careerwright.route_solves (workspace_id, run_id) ON DELETE CASCADE,
    FOREIGN KEY (run_id, attempt_id)
        REFERENCES careerwright.route_solve_attempts (run_id, attempt_id) ON DELETE CASCADE
);
COMMENT ON TABLE careerwright.route_solve_results IS
    'A route solve''s stored result, once, beside its sealed output (the ranked archive): '
    'its coverage, stop reason, outcome and counts. Append-only.';
"""

POLICIES = """
ALTER TABLE careerwright.route_solves ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.route_solve_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE careerwright.route_solve_results ENABLE ROW LEVEL SECURITY;

-- API role: the owner's workspaces. It records a solve at submission and reads the rest.
CREATE POLICY api_workspace ON careerwright.route_solves TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w))
    WITH CHECK (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.route_solve_attempts TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
CREATE POLICY api_workspace ON careerwright.route_solve_results TO careerwright_api
    USING (workspace_id IN (SELECT w.workspace_id FROM careerwright.workspaces w));
GRANT SELECT, INSERT ON careerwright.route_solves TO careerwright_api;
GRANT SELECT ON careerwright.route_solve_attempts, careerwright.route_solve_results
    TO careerwright_api;

-- Worker role: the run it executes; its result only while the run's requester may act.
CREATE POLICY worker_read ON careerwright.route_solve_attempts FOR SELECT TO careerwright_worker
    USING (run_id = careerwright.current_run_id());
CREATE POLICY worker_insert ON careerwright.route_solve_attempts FOR INSERT
    TO careerwright_worker WITH CHECK (run_id = careerwright.current_run_id());
CREATE POLICY worker_update ON careerwright.route_solve_attempts FOR UPDATE
    TO careerwright_worker USING (run_id = careerwright.current_run_id());
CREATE POLICY worker_authorised ON careerwright.route_solve_results TO careerwright_worker
    USING (run_id = careerwright.current_run_id()
           AND workspace_id = careerwright.authorised_run_workspace())
    WITH CHECK (run_id = careerwright.current_run_id()
                AND workspace_id = careerwright.authorised_run_workspace());
GRANT SELECT, INSERT ON careerwright.route_solve_attempts TO careerwright_worker;
GRANT UPDATE (stage, outcome, finished_at) ON careerwright.route_solve_attempts
    TO careerwright_worker;
GRANT SELECT, INSERT ON careerwright.route_solve_results TO careerwright_worker;
"""


def upgrade() -> None:
    run_script(SCHEMA + POLICIES)


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only; see docs/runbook.md")
