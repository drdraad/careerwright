# Sprint 6 review: the route search, proved (6a) and made a run (6b)

- Date: 2026-10-31.
- Order this ran in (plan v1.5, the worktree track): Task 13a (Sprint 6a: the search core, its
  oracle and the measured sizes; reviewed, two fix rounds), then Task 12a (the stored planning
  inputs, which the search reads), then Task 13b (Sprint 6b: the search as a durable run, its
  caps, the separate rank stage, cancellation and the 50,000-point benchmark). Sprint 6b was
  sized by the product owner's yes of 31 October 2026: L0 keeps no disk-backed archive,
  checkpoints or resume, and no separate child process (the specification's section 22,
  "L0 deferrals").
- Commits: Task 13a's are in its report (rebased as `ab22f45` to `8ff5100`); Task 13b's are
  listed in the Task 13b report.
- Reviewer: the Task 13b implementing agent, not independent of the work. An independent
  reviewer is dispatched after this task. Sprint 6 has no interface: the Routes chapter is
  Task 14, so questions 1 and 5 are answered through the API.

## Outcome

Sprint 6a's demonstrable outcome, as Task 13a showed it: a deterministic Python search returns
independently checked routes with F1 to F3 and truthful coverage on TRACE-01, the A–I fixture
and the option pack's instances; an intentionally simpler oracle verifies the same tiny
instances; and the measured sizes at which coverage completes are reported (ADR 0016's
consequences).

Sprint 6b's, as plan v1.5 and the L0 deferrals shape it, shown against real PostgreSQL 16 and
DBOS with real worker processes (`tests/integration/test_route_solves.py`):

1. A person with their planning inputs stated asks for one target's routes
   (`POST .../planning/solves`, with the inputs version they saw). The API compiles a snapshot
   of their inputs, their caps, the target's options and its readiness basis, seals it into a
   `route_solve` run and answers 202. A later edit to their inputs never reaches it.
2. A worker runs it: the search stage under the M0 limits, then the rank stage on its own
   clock and limit. The ranked result is stored sealed, its facts beside it, and
   `GET .../planning/solves/{run_id}` serves it, with its stage while it runs.
3. A limit stops a search: the result is `budget_truncated` with its exact stop reason, the
   instance size and the narrowings, carries `SOLVE_LIMIT_REACHED` as a fact, and is never
   "no route". A cancel stops the search at its next check and stores nothing. A crashed
   worker's solve starts again under a new attempt and never yields a truncated result. A rank
   stage past its own limit fails the run and claims no ranks.

With the option pack as it stands, every offering lacks a fact the search needs, so a real
person's solve is `unresolved`, never a route (Task 13a's measurement); routes appear once the
person supplies those facts at the Options checkpoint (Task 12b).

## Card deliverables

| Item | State | Evidence |
|---|---|---|
| S6.1 canonical DFS | done (13a) | `test_route_search.py`; ADR 0016 decision 2 |
| S6.2 sound pruning, each rule proved | done (13a, classes extended by 12a) | `search.py` docstring; ADR 0016 decision 4 and its amendments |
| S6.3 the archive and an idempotent solve identity | done as sized: in memory under the caps, never evicted; `solve_id`; a crash restarts under a new attempt ID. The disk archive, checkpoints and resume: **L0 deferral** | `test_route_search.py::test_a_state_limited_run_replays_exactly_and_keeps_every_schedule_it_met`, `test_route_solves.py::test_a_crashed_solve_starts_again_under_a_new_attempt_never_a_truncated_result`, `::test_asking_twice_is_one_solve_and_what_a_solve_cannot_start_from_is_refused` |
| S6.4 the caps, exact stop reasons, the truncation wording | done: 30 s, 1,000,000 states, 50,000 schedules; the result's facts and `SOLVE_LIMIT_REACHED`; the words are Task 14's | `test_route_search.py` (13a's limit tests), `test_route_solves.py::test_a_search_its_limit_stops_is_stored_truncated_never_no_route` |
| S6.5 the whole encountered archive, peeled layers, families | done (13a); ranked now by the efficient layering | `test_route_layers.py`, `test_route_oracle.py` |
| S6.6 the independent oracle and checker | done (13a) | `tests/support/route_oracle.py`, `test_route_oracle.py` |
| S6.7 coverage and the measured sizes | done (13a) | ADR 0016's consequences; `tools.route_search_sizes` |
| S6.8 the efficient layering and the separate rank stage | done | `test_route_layers.py`, `test_route_oracle.py::test_the_rank_stage_s_layers_equal_iterative_peeling_on_every_complete_search`, `test_route_search.py` (the rank stage's tests), `tools.rank_benchmark` |
| The search as a run, cancellable | done: one keyless run kind with its own workflow; the child process: **L0 deferral** | `test_route_solves.py` |
| The 50,000-point ranking benchmark | done | `tools.rank_benchmark` (ADR 0016's Task 13b consequences) |

## Checks run on the final candidate

On Task 13b's code, commit `0a8095c`, rebased onto `l0-local-release` at `6c9e0a8` (the commits
after it change documents only):

- `make check`: exit 0. Backend: ruff format and lint clean, mypy clean (354 files), 1,687
  fast tests passed (371 deselected), the fixture validator passed. Web: the generated client
  matches the OpenAPI document, Biome clean (139 files), `tsc` clean, Vitest 379 tests in 37
  files passed.
- `make acceptance` (under the acceptance lock, one guarded command): exit 0. 371 integration
  and stack tests passed on PostgreSQL 16 and DBOS (8 min 34 s), `test_route_solves.py`'s ten
  among them; the Storybook build completed; 56 Playwright tests passed (6.8 min).
- The benchmark, `uv run --locked python -m tools.rank_benchmark`: both layerings agree on
  every shape at 50,000 points, each under 0.07 s; the rank stage on a 50,000-schedule
  archive took 988 ms against its 5-second limit (ADR 0016's Task 13b consequences).
- Deliberate defects, each caught: the rank-stage property against a layering that let equal
  points dominate each other; in a real worker, a cancel check that never read the request
  (the attempt ended `succeeded`, not `cancelled`) and a restart that left the crashed
  attempt unmarked (`[None, 'succeeded']`, not `['interrupted', 'succeeded']`).
- Live calls: none (cost $0). Not run: nothing human-only applies to this backend sprint.

## The six questions

1. **Does the journey make sense from entry to the latest outcome?** Through the API, yes:
   stated inputs, then a solve asked for at the version seen, then a stored result read back
   with its stage, coverage and outcome. Failure paths, each tested: a stale version
   (`STALE_INPUT_VERSION`), a target that is not the person's (404), a target with no options,
   a start already past, an input a solve needs (named, and no run is created), a catalogue
   beyond the M0 bounds, a cancel, a crash, a limit and the rank stage's limit. The Routes
   chapter that shows it is Task 14.
2. **Do shared concepts mean the same everywhere?** Search coverage is the spec's
   `search_coverage` (`complete` or `budget_truncated`) in the search, the stored facts (with
   CHECKs), the API and the generated client; the outcome's four values are the search's own,
   and the database refuses "no route" or "unresolved" on a stopped search. Unknown stays
   unknown: a pack offering missing a fact is set aside as unresolved, never as a no. Direct
   and economic cost are the checker's, carried unchanged into each schedule. Cancelled and
   failed runs have no result, distinct from a complete one.
3. **Can a consequential claim be traced?** One example: a solve's `outcome: unresolved` →
   `route_solve_results` (attempt, output, coverage `complete`) → the sealed output's
   `set_aside` list naming each offering and its unknown codes → the snapshot's
   `input_version` (recorded on `route_solves`, with the planning inputs version, the
   capability version and the profile version pinned on the run) → `prepare` and
   `compile_input` over the stored version → the option pack record each variant came from.
   The snapshot reads back exactly what was sealed
   (`test_route_solve_records.py::test_a_sealed_snapshot_reads_back_as_the_same_input_and_searches_the_same`,
   which found and fixed a defect: a matrix row's derived `required` would not read back).
4. **Are module and process boundaries intact?** The search, the layers and the records are
   pure; the snapshot is compiled at the API and the worker reads only the run's sealed input
   (no profile, capability or planning table). Planning's only SQL is still `planning.store`;
   its DBOS workflow is one listed adapter (`planning.workflow`). Identity gains a run kind, a
   workflow name, a failure class and a sealed input for keyless runs, and imports nothing of
   planning. No model is called and no new dependency is added. The DBOS
   `application_version` is unchanged: no existing workflow's steps changed.
5. **Is the interface coherent and polished?** No interface this sprint. The API returns codes
   and numbers only (R11); the one new sentence is the failure class's words in
   `vocabulary.ts`, which the type checker requires of every failure class.
6. **What evidence establishes completion?** The checks above. Not established: how the
   Routes chapter words a truncated result (Task 14), and the search's time on another
   machine.

## Coherence questions

- **Sprint 6a's card** (compare the input assumptions, candidate checker, archived route, rank
  and displayed explanation for one schedule; are the measured sizes and their narrowings
  stated where Sprint 7 can show them?): one schedule keeps its route, family, months,
  objective, direct and economic cost, verdict, qualifications and conditions from the very
  `check_route` call that judged it, and its layer from the rank stage over the whole archive;
  the displayed explanation is Task 14's. The measured sizes are in ADR 0016's consequences,
  and a stopped result names the narrowings that could help, chosen from its stop reason
  (`fewer_concepts` or `one_start` for the state and archive limits, and `shorter_horizon`
  too for the time limit; ADR 0016 decision 21), beside its instance size, which the API
  serves for Task 14.
- **Sprint 6b's card** (at two starts per concept the selection bound alone is 10,161,633
  sets; does a full-scale truncated run report itself as the expected case, with its size and
  narrowing, never as infeasible?): yes. A stopped run is `budget_truncated` with its stop
  reason, `instance.selection_space`, its narrowings and `SOLVE_LIMIT_REACHED`; its outcome is
  `routes_found` or `none_found_before_limit`, and the database refuses `no_route_in_bounded_model`
  or `unresolved` on it. With P01's real limits, Task 13a measured the full M0 bound completing
  in 1.6 s; a relaxed or unbounded person's large catalogue is where truncation is expected.

## Accepted limitations

- **L0 deferrals** (the product owner's yes, 2026-10-31; the specification's section 22): no
  disk-backed archive, checkpoints or resume (a crash restarts the solve), and no separate
  child process (the search runs in the worker; a cancel reaches it at its next check).
- The rank stage's limit is checked between its four passes, so it can run over by at most one
  pass (under a second at the archive cap).
- A result at the archive cap is large (86 MB of JSON on the benchmark's instance); the
  Routes chapter should page it (Task 14).
- A chosen route's full ledgers need the same snapshot, which only the worker opens today.
- A solve whose worker keeps crashing ends after three attempts as `unknown_failure`.
- Wall-time-stopped results can stop at a different place on another machine (as specified).
- Solves run one at a time per worker process (L0 runs one); a second worker process would
  need a DBOS queue (ADR 0016 decision 22).
