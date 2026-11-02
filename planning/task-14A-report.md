# Task 14A report: the Routes chapter's facts in the API (backend half)

Worktree `/home/user/careerwright-wt/14a`, branch `wt-14a`, rebased onto
`claude/confident-ramanujan-ux3saw` (f5356e3). Commits 85ce831, 150c2cc, bd4aaf2 (head).

## What I built

Backend and API only. No screens, no migration, no new run kind or workflow; the DBOS
`application_version` stays `careerwright-l0-1` (the solve's step sequence is unchanged).

- `backend/src/careerwright/planning/comparison.py` (new, pure): the Routes chapter's facts
  from a stored solve.
  - **Comparison:** `lead` code (`best_trade_offs_found`, `none_found_before_limit`,
    `unresolved`, `longer_than_model`, `no_route_in_bounded_model`), spec section 18's `code`,
    coverage, stop reason, instance size, narrowings, and when stopped Task 13a's measured
    sizes (`completes_at`); the cost basis (objective, first month, horizon, currency, scenario,
    baseline kind and monthly pay); limits; pack label; `longer_than_model` and
    `beyond_horizon` options; set-aside options, starting violations, blocking inputs.
  - **Points:** a bounded projection (every F1-F3 point, the extremes, pinned points, then
    evenly spaced beyond F3, up to 200) with shown/total counts; each point's comparator under
    one declared rule and every other dominator.
  - **Families:** best layer first, at most 100 listed, with totals.
  - **Archive pages:** archive order, opaque cursor, view filters (months, cost, layer,
    family) that never change a recorded layer; explicit `rerank` gives `view_layer` beside
    it; pins come back with `in_view`.
  - **A chosen route:** cost parts kept apart (direct spending, pay difference, economic cost,
    peak payment, lowest prefunded cash, reserve, loans to repay); monthly table; liabilities;
    debts; step facts (dates and model months, hours, payments by month, supports, fee loan,
    work pattern, net pay after an offer, role class, prerequisites, grants, each record's
    review state, evidence date, supplied facts, `qualified_by`, cited spans); gates at their
    months; waits; milestones; stress cases apart (null where they fail or are unknown,
    `same_as_base`); `self_paid` beside a route resting on a loan not yet approved.
  - The base check is re-run on the solve's own input and must match what was archived, or
    the solve is refused as out of date (`STALE_INPUT_VERSION`, `solve_outdated`).
- `backend/src/careerwright/api/routes_comparison.py` (new): `GET .../planning/solves/{run_id}/comparison`
  (with `changed_since`: newer planning inputs or profile, STATE-06), `.../schedules`
  (paged) and `.../schedules/{index}` (a chosen route). An unfinished solve is refused naming
  its state (`solve_not_complete`), never an empty success. Registered in `api/app.py`.
- `planning/solve_records.py`, `solve_runs.py`, `solves.py`: the worker now seals the
  result together with the monthly input it was computed from (`SolveOutput`), so the API
  can recheck a chosen route without reading the sealed input (the API role still has no
  SELECT on `run_inputs`). Older outputs read as the bare result and the new endpoints refuse
  them as out of date.
- `planning/compiler.py`: a compiled option also carries its title, provider and evidence
  date (defaults keep older snapshots readable).
- `planning/inputs.py`: the solve's stage checks (API-05): both limits, and the baseline for
  an economic solve, now block a solve (refused naming them).
- `api/routes_planning.py`: `result_code` moved into `comparison.py` (same behaviour).
- Generated client regenerated (`apps/web/src/generated/`).
- ADR 0016 amendment (decisions 23 to 27, the comparator rule among them); ADR 0013
  amendment (the stage checks). Register rows updated, marked "backend; screens in 14B".

## Rulings (each costs little if wrong)

1. **Comparator rule** (ADR 0016 decision 23): the soonest dominator in the layer just above,
   then the cheapest; the others listed. It never measures distance across months and pounds.
2. **Stage checks:** an unstated limit, or a missing baseline for an economic comparison,
   now blocks a solve instead of letting it run and come back "unresolved". The reserve,
   weekly hours and work rights still leave routes unresolved.
3. **Longer than the model:** when a complete search finds no route and an option takes
   longer than 24 months, the lead is `longer_than_model` and `code` is null, so the screen
   never says "no route". If something is also unknown, the lead stays `unresolved`, with the
   long option listed beside it.
4. **The output keeps its input** instead of the API reading the sealed input. This needed
   no migration and leaves the security boundary as it was.
5. `GET .../solves/{run_id}` still serves the whole result (Task 13b's contract). The Routes
   chapter should read the new bounded endpoints instead.

## Four planning-model gaps: proposed L0 deferrals, awaiting the product owner's yes

None is recorded as approved.
- Information-gathering and waiting as actions of their own (PLN-01): defer. It needs
  catalogue data no pack record has. Months spent waiting are already counted and now shown.
- The search and review step before a job offer (OPTN-04): defer. It needs search-time and
  cost assumptions no source supports yet. The offer gate, role class and net pay are shown.
- Experience beyond a course's own outcomes (OUT1-08): defer. It needs new capability rules
  and changes the search's input and the oracle.
- A check of the result after an assessed course (PLN-04): **modelled** as a milestone fact at
  readiness, with no planning change.

## Session 2's misunderstandings (H-13)

- "Economic cost" versus "direct cost": every cost part is served apart, with a code
  (direct spending, pay difference, economic cost), so the web can say "£600 you pay, £0 less
  pay, £600 in all". Addressed in the API; the words are 14B's.
- "Conditional": each condition is a gate with what to confirm (`verification`) and its
  month. A route resting on a loan not yet approved also carries the self-paid route.
- "Fixture": `synthetic` on the basis, the label and each step.
- "Once its assessed report is passed": a verification milestone plus the readiness state as
  codes. The plain words are 14B's.
- "Print snapshot states": a print screen, not the API. Carried to Task 15.
- TRACE-01 and DIRECTAI stay apart through the basis code (`economic` against
  `direct_spending`); tested.

## Checks run

- TDD: the stage-check test failed first (`test_nothing_stated_needs_every_input...` RED at
  index 7: the cap still read `leaves_every_route_unresolved`), then passed. The comparison
  tests were written right after the module rather than before it. Two of them failed first
  and drove fixes: `same_as_base` now compares the whole check (a no-offer case changes pay
  but not the plotted cost), and a schema-name clash was fixed (`Step` became `RouteStep`).
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24): passed. Backend 2229
  passed, 9 skipped; generated client matches; Biome, tsc and Vitest 472 passed; re-run on the final rebased head: backend 2229 passed, Vitest 473 passed.
- New tests: `tests/domain/test_route_comparison.py` (14 tests),
  `tests/api/test_planning_contract.py` (Money/SignedMoney and no `reason` field on the three
  new responses), `tests/domain/test_planning_inputs.py` (stage checks).
- Integration (focused, under the lock): see "Integration" below.
- `make acceptance`: not run; the controller runs acceptance.
- Live calls: none. Cost: $0.

## Integration

Run under the lock, one guarded command each, with the build shim:
- `pytest -m integration tests/integration/test_route_solves.py tests/integration/test_planning_inputs.py`:
  44 passed, 1 failed. The new test failed because of the test itself, not the code: httpx
  drops a query string written into the path once `params` is passed, so `limit` and
  `cursor` never reached the API. I fixed the test to pass them as `params`.
- Re-run of the new test plus the P01 test (`-k "routes_chapter or p01"`): 2 passed.
- So every test in both files has passed on the final code: 43 in the first run, the 2
  changed ones in the re-run. Every changed planning-inputs expectation passed in the first
  run.

## Concerns and gaps

- Whiskers on every point are not computed (only a chosen route's stress cases). 14B should
  show scenarios on focus.
- Each request parses the whole stored output. That is fine for realistic sizes, but slow at
  the 50,000 cap (about 2.4 s).
- `changed_since` compares planning inputs and profile versions. It does not compare the
  evidence (capability) version.
- Process note: one one-word source tweak (`if following` to `if following is not None` in
  `routes_comparison.py`) was made with `sed`, not Edit. Ruff `--fix` also split some test
  assertions.

## Paths a reviewer can skip

`apps/web/src/generated/**` (generated client).
