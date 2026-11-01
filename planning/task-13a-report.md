# Task 13a report: the route search core (Sprint 6a)

- Status: DONE_WITH_CONCERNS (concerns at the end). Fix round 1 appended at the end.
- Worktree `/Users/darianraad/Code/careerpathoptimizer-wt/13a`, branch `wt-13a`. After fix
  round 1 it is rebased onto `l0-local-release` at 0931cbb, head
  `589119a92ab5b25c55b7d5688053dd477f3444a3`. The commits below are the original ones; the
  rebase gave them new SHAs (fix round 1 lists them).
- Commits (5ddd74e..0eb11b5 before the rebase):
  - 5ddd74e The route search core: canonical depth-first search, sound pruning, the whole
    encountered archive, F1 to F3 by peeling and families, checked against an independent oracle
  - 824e9b5 The route search on the reviewed option pack and the coverage-size measurement,
    with ADR 0016
  - 0eb11b5 Register: the rows the route search core closes

## The answer for Task 13b, in plain words

(Corrected in fix round 1. These figures hold for intakes spread across the horizon. The first
run kept every intake in months 1 to 9, which overstated the 12- and 24-month sizes.)

- Every reviewed-pack instance completes in-process, in milliseconds, far inside the M0 limits.
  Each pack target has at most four concepts. Today every pack offering lacks something the
  search needs (a date, a cost, weekly hours or an entry confirmation), so each is set aside.
  The result says "unresolved", never "no route". Two pack offerings also break a rule as
  stated: C04 paid in full is above both of P01's caps, and nothing grants C09's admission.
- A catalogue the size of the whole pack (ten pack-shaped courses, two starts each) completes
  with no limit binding: 13 seconds over 12 months, 26 seconds over 24 months. That is close
  to the 30-second limit.
- With P01's real limits, the search completes at the full M0 bound (24 concepts, two starts,
  24 months: 10,161,633 selected sets) in 2,233 checks and 1.6 seconds. The caps prune almost
  everything, whatever the dates.
- The 1,000,000-state limit never bound. One check costs 0.2 to 1.2 ms, so the 30-second clock
  binds at about 26,000 to 110,000 checks. With no binding limit and one start over 24
  months, the 50,000-schedule archive limit binds first.

## What I built

Backend only. No persistence, API, UI, migration or run kind. DBOS `application_version`
unchanged.

- `backend/src/careerwright/planning/search.py`: `search_routes(monthly, *, limits, clock)`.
  - The declared tree: concepts in a canonical order (earliest start, then ID), skip or one
    start per concept, at most six actions, one per exclusive group, one bridge role. Each
    allowed set visited once; the empty route is the root (zero-action readiness).
  - Every candidate is checked by Task 11's `check_route` in the base scenario.
  - Six pruning rules, each proved in the module docstring (also ADR 0016 decision 4):
    input-level unknowns; a variant's own findings (set aside with reasons); both spend caps by
    additivity (children over a cap are never checked); conflicting work patterns and session
    clashes; workload unless a later work pattern can lower the job's hours; a prerequisite no
    later variant grants in time. Never pruned: reserve, deficit cap, applications, readiness,
    objectives.
  - The archive keeps every feasible schedule that reaches the milestone, dominated ones
    included, as a compact record (route, family, objectives, verdict, qualifications,
    conditions, preferences, layer). Feasible schedules without the milestone are counted.
  - Coverage `complete` or `budget_truncated` with the exact stop reason (state, wall time,
    archive), unexplored branches and narrowings. Outcomes: `routes_found`,
    `none_found_before_limit`, `unresolved`, `no_route_in_bounded_model`.
  - `M0SearchLimits` is spec section 18's. Beyond-bound input is refused
    (`MODEL_SCOPE_EXCEEDED`); a missing readiness basis is refused (`VALIDATION_FAILED`).
- `backend/src/careerwright/planning/layers.py`: F1 to F3 by iterative nondominated peeling
  (one sort per peel). 50,000 random points peel in 0.06 s.
- `backend/src/careerwright/planning/families.py`: family identity from the canonical action
  graph (concept, way of taking it, work pattern, financing and offer gates, precedence);
  families and equal points for presentation only.
- `backend/tests/support/route_oracle.py`: the independent Cartesian-product oracle and route
  checker. It imports only the input data types and the capability model's `assess`: nothing
  from the search, layers, families, checker, ledgers or months. Its layer rule is the longest
  dominance chain, not peeling.
- `backend/tools/route_search_sizes.py`: the measurement (`uv run --locked python -m
  tools.route_search_sizes`), synthetic pack-shaped instances in three families.
- Tests: `tests/domain/test_route_layers.py` (6), `test_route_search.py` (33),
  `test_route_oracle.py` (2 Hypothesis properties, 150 examples each),
  `test_route_search_pack.py` (5), `tests/tools/test_route_search_sizes.py` (4).
- `docs/adr/0016-route-search-core.md`; `docs/requirements-register.md` rows.

Changed shared test helpers (disclosed; no existing test input or assertion changed):
- `tests/support/planning.py`: `option()` gains `concept=` so two starts can share a concept
  (default unchanged); `catalogue_of()` lists each concept once; new `directai_fixture`,
  `directai_instance`, `readiness_of`, `pack_person`, `month_start`, `month_end`.
- `tests/support/capability.py`: new `planned()` (a constructed planned outcome).

## Rulings (each costs little if wrong)

1. **One bridge role is one `work` action.** An apprenticeship is a learning action with its
   own offer gate (ADR 0013 decision 3).
2. **The search reads the base scenario only.** The layers compare T and C in the base scenario;
   stress cases stay `evaluate_route` on a chosen route.
3. **Another payment plan is a schedule variant, not a family.** Supports and offer gates are
   the "material financing" in family identity.
4. **Proposed records are searched and qualified, not left out.** S6.1's "reviewed offering"
   is read as the catalogue the option checkpoint passes to the search (R9).
5. **"Unresolved" is conservative.** If an option is set aside for an unknown, the result is
   `unresolved`, not `no_route`, even if every route through it might also fail for another
   reason.
6. **The A–I fixture as an instance.** The fixture states months, cost and layer only. Each
   route is built as one course in one exclusive group from the planning start, its cost in its
   first month, every limit far above it; labelled in `tests/support/planning.py`.
7. **The pack person.** P01's figures (TRACE-01's), planning from 2026-11-01 for 24 months so the
   pack's stated intakes fall inside; no evidence entered yet.
8. **ADR number.** The main tree's Task A1 took ADR 0015 (the role space) while I worked, so this
   is ADR 0016.

## Checks run

- `make check` in the worktree before the commits, and again after the rebase onto ec4d060:
  exit 0. ruff format and lint clean, mypy clean (333 files), backend `1602 passed, 332
  deselected`, the fixture validator passed, web check passed (Vitest 36 files, 319 tests). No
  warnings in the output. Baseline at fde8e7d was backend 1,552.
- `make acceptance`: not run. This task adds no stack behaviour and touches nothing an
  integration or stack test covers (the dispatch's rule). The acceptance lock was not taken.
- The oracle properties at 4,000 examples each, on the final code (one-off script): both pass.
- Generator coverage (300 sampled examples): about a quarter have non-empty archives, about 20%
  reach layer 2 and 11% layer 3; every pruning rule fires in some examples. The monthly-cap
  pre-check rarely fires there, so it has its own deterministic test.

TDD evidence:
- Layers: the tests failed first (`ModuleNotFoundError: careerwright.planning.layers`), then
  passed.
- Search: I wrote its tests before the module but first ran them once it existed, so there was
  no RED run. As RED evidence I patched seven deliberate defects into the search (cut workload
  always, cut prerequisites always, cut on the reserve, drop the bridge-role limit, call an
  unknown "no route", keep only F1, treat reaching a cap as exceeding it). On the final code
  each one makes a named test fail. The first round missed "cut prerequisites always", so I
  added `test_a_prerequisite_a_later_concept_can_grant_in_time_is_never_pruned`.
- The oracle found one real defect during development: with an input-level unknown and the
  empty route also failing (its reserve), the search said "no route". Fixed: a blocking input
  always gives `unresolved`.

Live calls: none. Cost £0.

## What is not done, and why

- Persistence, API, UI, the child process, efficient ranking for a 50,000-point stage: Tasks 13b
  and 14. OPT1-07's API layer stays open: no endpoint serves a solve yet.
- The instance from P01's stored inputs (the audit's addition to this card): needs Task 12a's
  store, which does not exist yet.
- Stress scenarios inside the search: ruling 2.
- `CLAUDE.md`'s layout line for `careerwright/planning` does not mention the search. It is a
  main-tree file being edited there, so I left it: the controller may add "the route search,
  layers and families (ADR 0016)".

## Concerns

1. **The oracle is independent in code, not in authorship.** I wrote it after reading the
   checker, so it reproduces the checker's own edge semantics. Examples: no clash check when
   availability is unknown; a recurring plan with amount 0 is unknown. Agreement on 8,000
   generated instances shows the two match each other, not that both match the spec. The
   checker itself was reviewed in Task 11.
2. **Pruning rules 2, 5 and 6 depend on how `check_route` computes findings.** If Task 12a adds
   a finding (stacked funding left unresolved, unknown work rights; ADR 0013's 2026-10-31
   amendment), it must be classed for rule 2 and written into the oracle too (ADR 0016
   consequences).
3. **Ranking and result assembly run after the search's clock stops.** They were under 1 s in
   every measured run. Task 13b's separate rank stage owns this.
4. **The measured times are one machine's** (arm64 macOS, Python 3.12.12), run with nothing else
   active. The 1,000,000-state limit is out of reach in 30 s at this per-check cost. The
   cheapest speed-up for 13b: about 40% of a check is the readiness assessment, repeated for the
   same completed offerings across candidates, so memoising `assess` would help.
5. **Edit discipline.** Once, early on, I used a short Python one-off to replace two strings in
   my own new test file (`test_route_layers.py`) instead of the Edit tool. Every other source
   change used Edit or Write, or the project's formatter.
6. **Known limit.** A later intake of one "way" offering (full or part time) would count as
   another family. No pack record has one.

## Paths a reviewer can skip

- None generated or vendored. `backend/tools/route_search_sizes.py` is a measurement tool. Its
  synthetic builders duplicate a few test helpers, because no tool imports test code.

## Register rows

- Verified: ROU1-01, ROU1-02, OPT1-01, OPT1-02, OPT1-08, OPT1-13, OPT1-16, TRACE01-03,
  DIRECTAI-01, DIRECTAI-03, PARETO-01, PARETO-02, FAMILY-01.
- Task 13a's part recorded, still planned for its other owner: ROU1-03, OPT1-05, OPT1-06,
  OPT1-07 (API), OPT1-09, OPT1-10, OPT1-12, OPT1-14, OPT1-15, PARETO-03, FAMILY-02, LIMITS-04,
  LIMITS-05.

## Measurements (OPT1-16; for Tasks 13b and 14)

How to read this:
- Instances are synthetic pack-shaped courses (`tools/route_search_sizes.py` docstring):
  1–6 months, 4–10 hours a week, £300–£1,500 (paid in full or by monthly instalments), every
  fourth on reduced hours, a target of three skill rows where each course reaches one or two.
- Families: `p01` is P01's limits (£1,500 caps, £500 reserve, £6,000 cash, 40 hours);
  `relaxed` has a £5,000 direct cap and 45 hours; `unbounded` has no binding limit, so the whole
  selection space is checked.
- "Selection space" is the allowed sets before pruning. "Search" is the search's own clock,
  which the 30 s limit reads; "Total" adds the layers, families and points.
- Each sweep grows the number of concepts and stops after the first size that does not complete.

There are two runs (fix round 1, review 13a, Important 3):
- **Spread intakes** (`--intakes spread`, now the default). Course c's first intake is in month
  5c mod months + 1, so intakes cover the whole horizon. **This is the run Task 13b sizes from.**
- **Early intakes** (`--intakes early`, the first run). Every intake falls in months 1 to 9,
  whatever the horizon. Its 12- and 24-month rows grow only the cost of each check, never the
  tree, so its larger-horizon sizes are optimistic.

Largest sizes that complete within the M0 limits (1,000,000 states, 30 s), **spread intakes**,
measured on the fix round 1 code (concepts, then states and search time):

| Family | 1 start, 6 months | 1 start, 12 months | 1 start, 24 months | 2 starts, 6 months | 2 starts, 12 months | 2 starts, 24 months |
|---|---|---|---|---|---|---|
| p01 | 24 (296 states, 0.09 s)* | 24 (289, 0.11 s) | 24 (293, 0.14 s) | 24 (2,423, 0.81 s)* | 24 (2,243, 1.15 s) | 24 (2,233, 1.55 s) |
| relaxed | 24 (21,594, 6.2 s)* | 24 (33,184, 13.5 s) | 22 (44,983, 24.1 s) | 14 (86,236, 28.1 s)* | 12 (31,171, 15.0 s) | 10 (12,451, 6.7 s) |
| unbounded | 22 (110,056, 27.0 s)* | 20 (60,460, 24.5 s) | 18 (31,180, 22.7 s) | 12 (94,449, 28.6 s)* | 10 (26,025, 13.2 s) | 10 (26,025, 25.6 s) |

\* At 6 months no spread instance reaches the milestone: most courses start too late to finish.
These rows size a tree with nothing to find.

The next size was "not complete at that size" (spread intakes):
- relaxed: the 30 s clock, at 24 concepts × 1 × 24 months (50,984 states), 16 × 2 × 6
  (76,931), 14 × 2 × 12 (59,919) and 12 × 2 × 24 (37,990);
- unbounded: the 30 s clock, at 24 × 1 × 6 (110,201 states), 22 × 1 × 12 (58,267), 14 × 2 × 6
  (63,972), 12 × 2 × 12 (32,599) and 12 × 2 × 24 (26,161); the 50,000-schedule archive limit
  at 20 × 1 × 24 (56,958 states).

Largest sizes that complete, **early intakes** (the first run, on the original code; nothing
was set aside or cut at the empty route in these instances, so fix round 1's search changes do
not affect them):

| Family | 1 start, 6 months | 1 start, 12 months | 1 start, 24 months | 2 starts, 6 months | 2 starts, 12 months | 2 starts, 24 months |
|---|---|---|---|---|---|---|
| p01 | 24 (314 states, 0.10 s) | 24 (314, 0.12 s) | 24 (314, 0.14 s) | 24 (2,531, 0.97 s) | 24 (2,487, 1.34 s) | 24 (2,487, 1.66 s) |
| relaxed | 24 (34,956, 12.8 s) | 24 (34,956, 16.1 s) | 24 (34,956, 19.5 s) | 12 (36,409, 13.6 s) | 12 (29,073, 14.4 s) | 12 (29,073, 17.0 s) |
| unbounded | 20 (60,460, 22.5 s) | 18 (31,180, 13.6 s) | 18 (31,180, 16.0 s) | 10 (26,025, 9.0 s) | 10 (26,025, 11.6 s) | 10 (26,025, 13.9 s) |

What differs between the runs:
- At 24 months with spread intakes, the relaxed family completes 22 concepts with one start (not
  24) and 10 with two (not 12). Its trees are larger: 12 × 1 × 24 takes 1,387 states against
  945, and 10 × 2 × 24 takes 12,451 against 7,455.
- A check costs more: 0.2 to 1.2 ms against 0.2 to 0.7. More completion months means more
  readiness assessments.
- P01's limits still complete the whole M0 bound.

None of these stops is an infeasibility.

Reviewed pack 0.2.0, each target (P01's figures, 24 months from 2026-11-01): complete, outcome
`unresolved`, 1 + variants checks, a few ms each. Each set-aside offering now shows what to
confirm apart from what already rules it out as stated (fix round 1, review 13a, Important 2):

| Target | Concepts | Variants | Selection space | Checks | To confirm (unknown) | Already rules it out as stated |
|---|---:|---:|---:|---:|---|---|
| data-quality-analyst-manchester | 2 | 4 | 9 | 5 | C01 full and part time, C04 instalments: dates, cost, weekly hours; C04 in full: dates, weekly hours | C04 in full: £2,995 above both £1,500 caps (direct spend and monthly payment) |
| it-support-technician-bristol | 2 | 2 | 4 | 3 | C07: weekly hours; C10: dates, cost, weekly hours | none |
| registered-nurse-manchester | 2 | 2 | 4 | 3 | C08: entry requirements, cost, weekly hours; C03: dates, weekly hours | none |
| bookkeeping-assistant-leeds | 4 | 4 | 16 | 5 | C09: entry requirements, cost; C05: entry requirements, cost, weekly hours; C02 and C06: dates, entry requirements, weekly hours | C09: its admission gate (nothing grants it), and its 35 hours a week beside P01's 30-hour job (40 available) |

The full early-intake sweep, as the tool printed it (the first run; the tool's rows then had no
intakes column). The full spread sweep is in fix round 1 below.

Measured 2026-10-31 on arm64 (Darwin), Python 3.12.12, M0 limits (1,000,000 states, 30 s, 50,000 schedules).

| Family | Concepts | Starts | Months | Selection space | Coverage | Expanded states | Archived | Search (s) | Total (s) | ms per state |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| p01 | 2 | 1 | 6 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| p01 | 4 | 1 | 6 | 16 | complete | 9 | 1 | 0.00 | 0.00 | 0.222 |
| p01 | 6 | 1 | 6 | 64 | complete | 17 | 2 | 0.00 | 0.00 | 0.176 |
| p01 | 8 | 1 | 6 | 247 | complete | 29 | 3 | 0.01 | 0.01 | 0.207 |
| p01 | 10 | 1 | 6 | 848 | complete | 33 | 4 | 0.01 | 0.01 | 0.212 |
| p01 | 12 | 1 | 6 | 2,510 | complete | 68 | 4 | 0.01 | 0.01 | 0.221 |
| p01 | 14 | 1 | 6 | 6,476 | complete | 82 | 4 | 0.02 | 0.02 | 0.232 |
| p01 | 16 | 1 | 6 | 14,893 | complete | 126 | 5 | 0.03 | 0.03 | 0.246 |
| p01 | 18 | 1 | 6 | 31,180 | complete | 168 | 5 | 0.04 | 0.04 | 0.238 |
| p01 | 20 | 1 | 6 | 60,460 | complete | 174 | 5 | 0.04 | 0.04 | 0.247 |
| p01 | 22 | 1 | 6 | 110,056 | complete | 289 | 46 | 0.08 | 0.08 | 0.287 |
| p01 | 24 | 1 | 6 | 190,051 | complete | 314 | 46 | 0.10 | 0.10 | 0.325 |
| p01 | 2 | 1 | 12 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| p01 | 4 | 1 | 12 | 16 | complete | 9 | 1 | 0.00 | 0.00 | 0.222 |
| p01 | 6 | 1 | 12 | 64 | complete | 17 | 4 | 0.01 | 0.01 | 0.294 |
| p01 | 8 | 1 | 12 | 247 | complete | 29 | 8 | 0.01 | 0.01 | 0.276 |
| p01 | 10 | 1 | 12 | 848 | complete | 33 | 9 | 0.01 | 0.01 | 0.273 |
| p01 | 12 | 1 | 12 | 2,510 | complete | 68 | 22 | 0.02 | 0.02 | 0.294 |
| p01 | 14 | 1 | 12 | 6,476 | complete | 82 | 27 | 0.03 | 0.03 | 0.305 |
| p01 | 16 | 1 | 12 | 14,893 | complete | 126 | 44 | 0.04 | 0.04 | 0.341 |
| p01 | 18 | 1 | 12 | 31,180 | complete | 168 | 60 | 0.06 | 0.06 | 0.345 |
| p01 | 20 | 1 | 12 | 60,460 | complete | 174 | 62 | 0.06 | 0.06 | 0.356 |
| p01 | 22 | 1 | 12 | 110,056 | complete | 289 | 112 | 0.11 | 0.11 | 0.367 |
| p01 | 24 | 1 | 12 | 190,051 | complete | 314 | 117 | 0.12 | 0.12 | 0.379 |
| p01 | 2 | 1 | 24 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| p01 | 4 | 1 | 24 | 16 | complete | 9 | 1 | 0.00 | 0.00 | 0.333 |
| p01 | 6 | 1 | 24 | 64 | complete | 17 | 4 | 0.01 | 0.01 | 0.588 |
| p01 | 8 | 1 | 24 | 247 | complete | 29 | 8 | 0.01 | 0.01 | 0.345 |
| p01 | 10 | 1 | 24 | 848 | complete | 33 | 9 | 0.01 | 0.01 | 0.333 |
| p01 | 12 | 1 | 24 | 2,510 | complete | 68 | 22 | 0.03 | 0.03 | 0.368 |
| p01 | 14 | 1 | 24 | 6,476 | complete | 82 | 27 | 0.03 | 0.03 | 0.366 |
| p01 | 16 | 1 | 24 | 14,893 | complete | 126 | 44 | 0.05 | 0.05 | 0.405 |
| p01 | 18 | 1 | 24 | 31,180 | complete | 168 | 60 | 0.07 | 0.07 | 0.411 |
| p01 | 20 | 1 | 24 | 60,460 | complete | 174 | 62 | 0.07 | 0.07 | 0.414 |
| p01 | 22 | 1 | 24 | 110,056 | complete | 289 | 112 | 0.13 | 0.13 | 0.446 |
| p01 | 24 | 1 | 24 | 190,051 | complete | 314 | 117 | 0.14 | 0.14 | 0.449 |
| p01 | 2 | 2 | 6 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| p01 | 4 | 2 | 6 | 81 | complete | 25 | 1 | 0.01 | 0.01 | 0.200 |
| p01 | 6 | 2 | 6 | 729 | complete | 61 | 3 | 0.01 | 0.01 | 0.213 |
| p01 | 8 | 2 | 6 | 5,281 | complete | 125 | 4 | 0.03 | 0.03 | 0.248 |
| p01 | 10 | 2 | 6 | 26,025 | complete | 137 | 6 | 0.04 | 0.04 | 0.263 |
| p01 | 12 | 2 | 6 | 94,449 | complete | 379 | 7 | 0.11 | 0.11 | 0.290 |
| p01 | 14 | 2 | 6 | 275,577 | complete | 443 | 7 | 0.13 | 0.13 | 0.298 |
| p01 | 16 | 2 | 6 | 686,401 | complete | 827 | 9 | 0.26 | 0.26 | 0.311 |
| p01 | 18 | 2 | 6 | 1,518,409 | complete | 1,141 | 9 | 0.37 | 0.37 | 0.327 |
| p01 | 20 | 2 | 6 | 3,064,209 | complete | 1,161 | 9 | 0.39 | 0.39 | 0.339 |
| p01 | 22 | 2 | 6 | 5,748,249 | complete | 2,389 | 234 | 0.87 | 0.88 | 0.365 |
| p01 | 24 | 2 | 6 | 10,161,633 | complete | 2,531 | 236 | 0.97 | 0.97 | 0.384 |
| p01 | 2 | 2 | 12 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.333 |
| p01 | 4 | 2 | 12 | 81 | complete | 25 | 4 | 0.01 | 0.01 | 0.280 |
| p01 | 6 | 2 | 12 | 729 | complete | 61 | 12 | 0.02 | 0.02 | 0.279 |
| p01 | 8 | 2 | 12 | 5,281 | complete | 125 | 25 | 0.04 | 0.04 | 0.304 |
| p01 | 10 | 2 | 12 | 26,025 | complete | 137 | 29 | 0.04 | 0.04 | 0.321 |
| p01 | 12 | 2 | 12 | 94,449 | complete | 379 | 106 | 0.14 | 0.14 | 0.377 |
| p01 | 14 | 2 | 12 | 275,577 | complete | 443 | 126 | 0.18 | 0.18 | 0.397 |
| p01 | 16 | 2 | 12 | 686,401 | complete | 819 | 244 | 0.36 | 0.36 | 0.435 |
| p01 | 18 | 2 | 12 | 1,518,409 | complete | 1,121 | 356 | 0.59 | 0.59 | 0.530 |
| p01 | 20 | 2 | 12 | 3,064,209 | complete | 1,141 | 362 | 0.56 | 0.56 | 0.490 |
| p01 | 22 | 2 | 12 | 5,748,249 | complete | 2,337 | 836 | 1.18 | 1.18 | 0.503 |
| p01 | 24 | 2 | 12 | 10,161,633 | complete | 2,487 | 864 | 1.34 | 1.35 | 0.540 |
| p01 | 2 | 2 | 24 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.333 |
| p01 | 4 | 2 | 24 | 81 | complete | 25 | 4 | 0.01 | 0.01 | 0.320 |
| p01 | 6 | 2 | 24 | 729 | complete | 61 | 18 | 0.02 | 0.02 | 0.361 |
| p01 | 8 | 2 | 24 | 5,281 | complete | 125 | 43 | 0.05 | 0.05 | 0.400 |
| p01 | 10 | 2 | 24 | 26,025 | complete | 137 | 47 | 0.06 | 0.06 | 0.423 |
| p01 | 12 | 2 | 24 | 94,449 | complete | 379 | 138 | 0.18 | 0.18 | 0.472 |
| p01 | 14 | 2 | 24 | 275,577 | complete | 443 | 166 | 0.22 | 0.23 | 0.506 |
| p01 | 16 | 2 | 24 | 686,401 | complete | 819 | 330 | 0.44 | 0.44 | 0.538 |
| p01 | 18 | 2 | 24 | 1,518,409 | complete | 1,121 | 450 | 0.65 | 0.65 | 0.577 |
| p01 | 20 | 2 | 24 | 3,064,209 | complete | 1,141 | 458 | 0.65 | 0.65 | 0.570 |
| p01 | 22 | 2 | 24 | 5,748,249 | complete | 2,337 | 944 | 1.43 | 1.44 | 0.613 |
| p01 | 24 | 2 | 24 | 10,161,633 | complete | 2,487 | 974 | 1.66 | 1.67 | 0.669 |
| relaxed | 2 | 1 | 6 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| relaxed | 4 | 1 | 6 | 16 | complete | 16 | 6 | 0.00 | 0.00 | 0.188 |
| relaxed | 6 | 1 | 6 | 64 | complete | 48 | 18 | 0.01 | 0.01 | 0.208 |
| relaxed | 8 | 1 | 6 | 247 | complete | 168 | 66 | 0.04 | 0.04 | 0.244 |
| relaxed | 10 | 1 | 6 | 848 | complete | 343 | 166 | 0.10 | 0.10 | 0.277 |
| relaxed | 12 | 1 | 6 | 2,510 | complete | 945 | 326 | 0.26 | 0.26 | 0.274 |
| relaxed | 14 | 1 | 6 | 6,476 | complete | 2,200 | 632 | 0.72 | 0.73 | 0.326 |
| relaxed | 16 | 1 | 6 | 14,893 | complete | 3,562 | 967 | 1.15 | 1.16 | 0.323 |
| relaxed | 18 | 1 | 6 | 31,180 | complete | 7,912 | 1,963 | 2.46 | 2.48 | 0.311 |
| relaxed | 20 | 1 | 6 | 60,460 | complete | 11,602 | 2,450 | 3.73 | 3.77 | 0.322 |
| relaxed | 22 | 1 | 6 | 110,056 | complete | 22,679 | 7,434 | 7.90 | 8.00 | 0.348 |
| relaxed | 24 | 1 | 6 | 190,051 | complete | 34,956 | 10,061 | 12.83 | 12.99 | 0.367 |
| relaxed | 2 | 1 | 12 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| relaxed | 4 | 1 | 12 | 16 | complete | 16 | 6 | 0.00 | 0.00 | 0.250 |
| relaxed | 6 | 1 | 12 | 64 | complete | 48 | 29 | 0.01 | 0.01 | 0.312 |
| relaxed | 8 | 1 | 12 | 247 | complete | 168 | 119 | 0.06 | 0.06 | 0.333 |
| relaxed | 10 | 1 | 12 | 848 | complete | 343 | 249 | 0.12 | 0.12 | 0.338 |
| relaxed | 12 | 1 | 12 | 2,510 | complete | 945 | 633 | 0.34 | 0.35 | 0.365 |
| relaxed | 14 | 1 | 12 | 6,476 | complete | 2,200 | 1,549 | 0.88 | 0.90 | 0.398 |
| relaxed | 16 | 1 | 12 | 14,893 | complete | 3,562 | 2,167 | 1.48 | 1.49 | 0.416 |
| relaxed | 18 | 1 | 12 | 31,180 | complete | 7,912 | 4,763 | 3.44 | 3.50 | 0.435 |
| relaxed | 20 | 1 | 12 | 60,460 | complete | 11,602 | 7,177 | 5.10 | 5.26 | 0.439 |
| relaxed | 22 | 1 | 12 | 110,056 | complete | 22,679 | 13,525 | 10.09 | 10.29 | 0.445 |
| relaxed | 24 | 1 | 12 | 190,051 | complete | 34,956 | 19,219 | 16.08 | 16.33 | 0.460 |
| relaxed | 2 | 1 | 24 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| relaxed | 4 | 1 | 24 | 16 | complete | 16 | 6 | 0.01 | 0.01 | 0.312 |
| relaxed | 6 | 1 | 24 | 64 | complete | 48 | 29 | 0.02 | 0.02 | 0.354 |
| relaxed | 8 | 1 | 24 | 247 | complete | 168 | 119 | 0.07 | 0.07 | 0.393 |
| relaxed | 10 | 1 | 24 | 848 | complete | 343 | 249 | 0.15 | 0.15 | 0.429 |
| relaxed | 12 | 1 | 24 | 2,510 | complete | 945 | 633 | 0.43 | 0.43 | 0.457 |
| relaxed | 14 | 1 | 24 | 6,476 | complete | 2,200 | 1,549 | 1.04 | 1.05 | 0.473 |
| relaxed | 16 | 1 | 24 | 14,893 | complete | 3,562 | 2,167 | 1.73 | 1.75 | 0.485 |
| relaxed | 18 | 1 | 24 | 31,180 | complete | 7,912 | 4,763 | 4.10 | 4.16 | 0.518 |
| relaxed | 20 | 1 | 24 | 60,460 | complete | 11,602 | 7,177 | 6.14 | 6.30 | 0.529 |
| relaxed | 22 | 1 | 24 | 110,056 | complete | 22,679 | 13,525 | 12.21 | 12.40 | 0.538 |
| relaxed | 24 | 1 | 24 | 190,051 | complete | 34,956 | 19,219 | 19.49 | 19.75 | 0.558 |
| relaxed | 2 | 2 | 6 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| relaxed | 4 | 2 | 6 | 81 | complete | 81 | 24 | 0.02 | 0.02 | 0.235 |
| relaxed | 6 | 2 | 6 | 729 | complete | 588 | 174 | 0.16 | 0.16 | 0.265 |
| relaxed | 8 | 2 | 6 | 5,281 | complete | 3,329 | 648 | 1.10 | 1.10 | 0.329 |
| relaxed | 10 | 2 | 6 | 26,025 | complete | 8,491 | 2,504 | 2.92 | 2.94 | 0.344 |
| relaxed | 12 | 2 | 6 | 94,449 | complete | 36,409 | 8,544 | 13.64 | 13.76 | 0.375 |
| relaxed | 14 | 2 | 6 | 275,577 | not complete at that size (wall_time_limit) | 73,512 | 14,203 | 30.00 | 30.18 | 0.408 |
| relaxed | 2 | 2 | 12 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| relaxed | 4 | 2 | 12 | 81 | complete | 81 | 48 | 0.02 | 0.02 | 0.296 |
| relaxed | 6 | 2 | 12 | 729 | complete | 456 | 349 | 0.16 | 0.16 | 0.355 |
| relaxed | 8 | 2 | 12 | 5,281 | complete | 2,780 | 1,978 | 1.16 | 1.17 | 0.417 |
| relaxed | 10 | 2 | 12 | 26,025 | complete | 7,455 | 5,126 | 3.28 | 3.35 | 0.440 |
| relaxed | 12 | 2 | 12 | 94,449 | complete | 29,073 | 16,854 | 14.37 | 14.61 | 0.494 |
| relaxed | 14 | 2 | 12 | 275,577 | not complete at that size (wall_time_limit) | 56,487 | 35,015 | 30.00 | 30.54 | 0.531 |
| relaxed | 2 | 2 | 24 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.333 |
| relaxed | 4 | 2 | 24 | 81 | complete | 81 | 48 | 0.03 | 0.03 | 0.407 |
| relaxed | 6 | 2 | 24 | 729 | complete | 456 | 371 | 0.20 | 0.20 | 0.441 |
| relaxed | 8 | 2 | 24 | 5,281 | complete | 2,780 | 2,201 | 1.42 | 1.43 | 0.511 |
| relaxed | 10 | 2 | 24 | 26,025 | complete | 7,455 | 5,697 | 4.15 | 4.22 | 0.557 |
| relaxed | 12 | 2 | 24 | 94,449 | complete | 29,073 | 18,203 | 17.03 | 17.37 | 0.586 |
| relaxed | 14 | 2 | 24 | 275,577 | not complete at that size (wall_time_limit) | 47,581 | 33,107 | 30.00 | 30.50 | 0.631 |
| unbounded | 2 | 1 | 6 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| unbounded | 4 | 1 | 6 | 16 | complete | 16 | 6 | 0.00 | 0.00 | 0.188 |
| unbounded | 6 | 1 | 6 | 64 | complete | 64 | 24 | 0.02 | 0.02 | 0.250 |
| unbounded | 8 | 1 | 6 | 247 | complete | 247 | 112 | 0.06 | 0.07 | 0.259 |
| unbounded | 10 | 1 | 6 | 848 | complete | 848 | 553 | 0.25 | 0.25 | 0.291 |
| unbounded | 12 | 1 | 6 | 2,510 | complete | 2,510 | 1,479 | 0.75 | 0.76 | 0.300 |
| unbounded | 14 | 1 | 6 | 6,476 | complete | 6,476 | 3,783 | 2.12 | 2.20 | 0.327 |
| unbounded | 16 | 1 | 6 | 14,893 | complete | 14,893 | 10,076 | 5.41 | 5.54 | 0.363 |
| unbounded | 18 | 1 | 6 | 31,180 | complete | 31,180 | 19,187 | 11.13 | 11.40 | 0.357 |
| unbounded | 20 | 1 | 6 | 60,460 | complete | 60,460 | 36,638 | 22.51 | 23.37 | 0.372 |
| unbounded | 22 | 1 | 6 | 110,056 | not complete at that size (archive_limit) | 73,316 | 50,000 | 29.41 | 30.32 | 0.401 |
| unbounded | 2 | 1 | 12 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| unbounded | 4 | 1 | 12 | 16 | complete | 16 | 6 | 0.00 | 0.00 | 0.250 |
| unbounded | 6 | 1 | 12 | 64 | complete | 64 | 45 | 0.02 | 0.02 | 0.297 |
| unbounded | 8 | 1 | 12 | 247 | complete | 247 | 198 | 0.08 | 0.08 | 0.336 |
| unbounded | 10 | 1 | 12 | 848 | complete | 848 | 745 | 0.31 | 0.31 | 0.361 |
| unbounded | 12 | 1 | 12 | 2,510 | complete | 2,510 | 2,329 | 0.95 | 0.96 | 0.378 |
| unbounded | 14 | 1 | 12 | 6,476 | complete | 6,476 | 6,053 | 2.65 | 2.75 | 0.410 |
| unbounded | 16 | 1 | 12 | 14,893 | complete | 14,893 | 14,072 | 6.36 | 6.62 | 0.427 |
| unbounded | 18 | 1 | 12 | 31,180 | complete | 31,180 | 29,805 | 13.61 | 14.17 | 0.436 |
| unbounded | 20 | 1 | 12 | 60,460 | not complete at that size (archive_limit) | 51,927 | 50,000 | 23.10 | 23.77 | 0.445 |
| unbounded | 2 | 1 | 24 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| unbounded | 4 | 1 | 24 | 16 | complete | 16 | 6 | 0.01 | 0.01 | 0.312 |
| unbounded | 6 | 1 | 24 | 64 | complete | 64 | 45 | 0.02 | 0.02 | 0.359 |
| unbounded | 8 | 1 | 24 | 247 | complete | 247 | 198 | 0.11 | 0.11 | 0.437 |
| unbounded | 10 | 1 | 24 | 848 | complete | 848 | 745 | 0.39 | 0.40 | 0.465 |
| unbounded | 12 | 1 | 24 | 2,510 | complete | 2,510 | 2,329 | 1.23 | 1.24 | 0.488 |
| unbounded | 14 | 1 | 24 | 6,476 | complete | 6,476 | 6,053 | 3.23 | 3.30 | 0.498 |
| unbounded | 16 | 1 | 24 | 14,893 | complete | 14,893 | 14,072 | 7.38 | 7.57 | 0.496 |
| unbounded | 18 | 1 | 24 | 31,180 | complete | 31,180 | 29,805 | 16.01 | 16.38 | 0.514 |
| unbounded | 20 | 1 | 24 | 60,460 | not complete at that size (archive_limit) | 51,927 | 50,000 | 27.71 | 28.38 | 0.534 |
| unbounded | 2 | 2 | 6 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| unbounded | 4 | 2 | 6 | 81 | complete | 81 | 24 | 0.02 | 0.02 | 0.222 |
| unbounded | 6 | 2 | 6 | 729 | complete | 729 | 216 | 0.18 | 0.18 | 0.250 |
| unbounded | 8 | 2 | 6 | 5,281 | complete | 5,281 | 1,584 | 1.65 | 1.68 | 0.313 |
| unbounded | 10 | 2 | 6 | 26,025 | complete | 26,025 | 11,664 | 9.04 | 9.18 | 0.347 |
| unbounded | 12 | 2 | 6 | 94,449 | not complete at that size (wall_time_limit) | 79,739 | 32,066 | 30.00 | 30.45 | 0.376 |
| unbounded | 2 | 2 | 12 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| unbounded | 4 | 2 | 12 | 81 | complete | 81 | 48 | 0.02 | 0.02 | 0.296 |
| unbounded | 6 | 2 | 12 | 729 | complete | 729 | 634 | 0.25 | 0.26 | 0.347 |
| unbounded | 8 | 2 | 12 | 5,281 | complete | 5,281 | 4,712 | 2.17 | 2.22 | 0.410 |
| unbounded | 10 | 2 | 12 | 26,025 | complete | 26,025 | 24,344 | 11.57 | 12.00 | 0.445 |
| unbounded | 12 | 2 | 12 | 94,449 | not complete at that size (archive_limit) | 51,853 | 50,000 | 25.09 | 26.18 | 0.484 |
| unbounded | 2 | 2 | 24 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.333 |
| unbounded | 4 | 2 | 24 | 81 | complete | 81 | 48 | 0.03 | 0.03 | 0.358 |
| unbounded | 6 | 2 | 24 | 729 | complete | 729 | 656 | 0.32 | 0.32 | 0.436 |
| unbounded | 8 | 2 | 24 | 5,281 | complete | 5,281 | 4,944 | 2.68 | 2.71 | 0.507 |
| unbounded | 10 | 2 | 24 | 26,025 | complete | 26,025 | 24,992 | 13.91 | 14.21 | 0.535 |
| unbounded | 12 | 2 | 24 | 94,449 | not complete at that size (archive_limit) | 50,573 | 50,000 | 29.36 | 30.05 | 0.580 |

## Fix round 1

The review (`task-13a-review.md`) found 3 Important issues and no Critical ones. All three are fixed, each with a test that failed first. Minors wait for the final review (R13), except where a fix touched the same lines.

Branch `wt-13a` is rebased onto `l0-local-release` at 0931cbb (Task W2E's code and the documents' fix round). Head: `589119a92ab5b25c55b7d5688053dd477f3444a3`.

Commits after the rebase (ab22f45..589119a):
- ab22f45, 11e5e2c, c8a9a5f: the original three, rebased (same content);
- b02b7d2: Fix round 1, the route search (Important 1 and 2);
- 660fec1: Fix round 1, the size measurement (Important 3);
- 589119a: Fix round 1, ADR 0016 and the register.

### Important 1: a false "no route"

- The defect. The search cut the empty route (rule 5, workload) before its screen had set any option aside. A complete run could then say `no_route_in_bounded_model` while the one option that could lower the job's hours only lacked its dates.
- The fix (`planning/search.py`). The screen now runs before every cut, the empty route's included. Every option set aside for an unknown reaches the outcome, which is then `unresolved`.
- I checked every other exit:
  - rule 1 (an unstated input) returns `unresolved`;
  - a limit stop is `budget_truncated`, never "no route";
  - every deeper cut comes after the screen.
- A second gap, found while checking exits. An option with unknown weekly hours whose months the checker reports as over the limit (because the known load already is) was not set aside. The result could then say "no route" while that option's own hours were unknown. Rule 2 now reads unknown weekly hours from the option itself: dated, active in a month of the horizon, no hours stated.
- `PRUNING_VERSION` is now `sound-pruning-2`.
- Tests:
  - `test_route_search.py::test_an_empty_route_over_its_hours_never_hides_an_undated_option_behind_no_route`: the reviewer's probe, built once in `tests/support/planning.py::undated_relief`;
  - `test_route_search.py::test_an_option_without_weekly_hours_is_set_aside_as_unknown_whatever_the_known_load`;
  - `test_route_oracle.py::test_the_oracle_counts_an_option_s_own_unknown_as_something_unknown`;
  - the probe is now an explicit `@example` of `test_route_oracle.py::test_the_search_finds_exactly_the_oracle_s_feasible_schedules_objectives_and_layers`.
- The oracle's `something_unknown` is stronger, read again from raw data. It is now also true when an input is unstated, or when an option has an unknown of its own (dates, cost, weekly hours, entry requirements, a payment before the start) and no breach of its own (its own spend above a cap, a start before the planning start, a passed deadline). This is why the property now catches the defect, where before it agreed with "no route".
- RED, before the fix (`uv run --locked pytest tests/domain/test_route_search.py tests/domain/test_route_oracle.py -q -k "undated_option_behind or own_unknown or oracle_s_feasible"`):
  ```
  E       AssertionError: assert [] == [('reduced-un...unresolved'>)]
  E           AssertionError: assert not True
  FAILED tests/domain/test_route_search.py::test_an_empty_route_over_its_hours_never_hides_an_undated_option_behind_no_route
  FAILED tests/domain/test_route_oracle.py::test_the_search_finds_exactly_the_oracle_s_feasible_schedules_objectives_and_layers
  2 failed, 1 passed, 34 deselected
  ```
- GREEN after the screen moved: `42 passed` (route search, oracle and pack tests).
- The weekly-hours gap: RED `assert [] == [('untimed', ...unresolved'>)]`, `1 failed`; GREEN `47 passed`.

### Important 2: a set-aside option kept only part of the truth

- The fix. `SetAside` keeps `codes` (the findings that set the option aside) and `kind`, and now also:
  - `unresolved`: every unknown its own check found, which is what to confirm;
  - `violations`: every rule it breaks as stated, alone, which is what already rules it out.
- C09 now reads: to confirm, entry requirements and cost; ruled out as stated, `prerequisite_not_usable` (nothing grants its admission) and `workload`.
- ADR 0016 is corrected: decision 4 describes the two lists, and the Task 14 note now says to show "what to confirm" apart from "what already rules it out as stated", with C09 as the example. The pack consequence names C04 paid in full and C09. The report's pack table above is corrected too.
- Tests:
  - `test_route_search_pack.py::test_a_set_aside_course_keeps_what_to_confirm_apart_from_what_already_rules_it_out` (C09);
  - an assertion added to `test_route_search.py::test_an_option_no_route_can_contain_is_set_aside_with_its_reason`. Its existing assertions are unchanged; the new one checks each option's two lists.
- RED: `AttributeError: 'SetAside' object has no attribute 'unresolved'`, 2 failed. GREEN: `48 passed`.

### Important 3: the measurement's horizon

- The fix (`tools/route_search_sizes.py`). Instances spread first intakes across the horizon (month 5c mod months + 1) by default. The first run's shape stays available as `--intakes early`. Every measurement records its spread, and every table row names it.
- Tests:
  - `tests/tools/test_route_search_sizes.py::test_intakes_spread_across_the_horizon_so_a_longer_horizon_grows_the_tree`: 24 courses over 24 months use every month as an intake, where early used only months 1 to 6;
  - `::test_a_measurement_says_which_intake_spread_it_holds_for`.
- Changed test inputs and assertions (disclosed):
  - `test_with_no_binding_limit_the_whole_selection_space_is_checked` and `test_with_p01_s_limits_the_same_courses_are_pruned_and_still_complete` now use a 24-month horizon instead of 6, with their assertions unchanged. With spread intakes, five courses in 6 months start too late for any route to reach the milestone, and these tests are about pruning, not intakes.
  - The sweep test's expected row now carries the new intakes column (`| p01 | spread | 4 | 1 | 6 |`).
- RED: `TypeError: instance() got an unexpected keyword argument 'intakes'`, 3 failed. GREEN: `6 passed`.
- The new run: `uv run --locked python -m tools.route_search_sizes --intakes spread`, on the fix round 1 code after the rebase, with nothing else running. The summary and the comparison with the early run replace the overstated lines in the measurement section above and in ADR 0016's consequences. The headline for Task 13b now says which spread it holds for.

### Checks

- Covering tests after each fix, as above.
- `make check` before the rebase: exit 0, backend `1608 passed, 332 deselected`, Vitest 319, no warnings.
- `make check` after the rebase onto 0931cbb: exit 0, backend `1616 passed, 333 deselected` (W2E added tests), Vitest 36 files and 319 tests, ruff and mypy clean (333 files), the fixture validator passed, no warnings.
- On the final code, one-off:
  - both oracle properties pass at 4,000 examples each;
  - the seven deliberate defects are still each caught by a named test.
- `make acceptance`: not run (no stack behaviour changed; lock not taken). Live calls: none, £0.

### What is still open

- Minors 1, 2, 4 and 6 are ledgered for the final review. Minor 2: the oracle reads the compiler's month indexes, so it shares the compiler's TIME-1 rules.
- Concern 1 still stands: the oracle copies the checker's rules. The reviewer's note on undated work patterns in the checker is Task 11's code. This round makes the search's outcome honest, but the checker's verdict on that one route is unchanged.
- The reviewer's notes for Task 12a (C07's conditional £0 fee, C09's admission, two conditional job transitions) are carried by the controller.

### The full spread-intake sweep, as the tool printed it

Measured 2026-10-31 on arm64 (Darwin), Python 3.12.12, M0 limits (1,000,000 states, 30 s, 50,000 schedules).

| Family | Intakes | Concepts | Starts | Months | Selection space | Coverage | Expanded states | Archived | Search (s) | Total (s) | ms per state |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| p01 | spread | 2 | 1 | 6 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| p01 | spread | 4 | 1 | 6 | 16 | complete | 9 | 0 | 0.00 | 0.00 | 0.111 |
| p01 | spread | 6 | 1 | 6 | 64 | complete | 17 | 0 | 0.00 | 0.00 | 0.176 |
| p01 | spread | 8 | 1 | 6 | 247 | complete | 29 | 0 | 0.01 | 0.01 | 0.172 |
| p01 | spread | 10 | 1 | 6 | 848 | complete | 33 | 0 | 0.01 | 0.01 | 0.182 |
| p01 | spread | 12 | 1 | 6 | 2,510 | complete | 65 | 0 | 0.01 | 0.01 | 0.200 |
| p01 | spread | 14 | 1 | 6 | 6,476 | complete | 79 | 0 | 0.02 | 0.02 | 0.203 |
| p01 | spread | 16 | 1 | 6 | 14,893 | complete | 119 | 0 | 0.03 | 0.03 | 0.210 |
| p01 | spread | 18 | 1 | 6 | 31,180 | complete | 157 | 0 | 0.03 | 0.03 | 0.217 |
| p01 | spread | 20 | 1 | 6 | 60,460 | complete | 163 | 0 | 0.04 | 0.04 | 0.227 |
| p01 | spread | 22 | 1 | 6 | 110,056 | complete | 274 | 0 | 0.07 | 0.07 | 0.237 |
| p01 | spread | 24 | 1 | 6 | 190,051 | complete | 296 | 0 | 0.09 | 0.09 | 0.294 |
| p01 | spread | 2 | 1 | 12 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| p01 | spread | 4 | 1 | 12 | 16 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| p01 | spread | 6 | 1 | 12 | 64 | complete | 17 | 2 | 0.01 | 0.01 | 0.294 |
| p01 | spread | 8 | 1 | 12 | 247 | complete | 30 | 3 | 0.01 | 0.01 | 0.233 |
| p01 | spread | 10 | 1 | 12 | 848 | complete | 34 | 4 | 0.01 | 0.01 | 0.265 |
| p01 | spread | 12 | 1 | 12 | 2,510 | complete | 60 | 10 | 0.01 | 0.02 | 0.250 |
| p01 | spread | 14 | 1 | 12 | 6,476 | complete | 74 | 14 | 0.02 | 0.02 | 0.270 |
| p01 | spread | 16 | 1 | 12 | 14,893 | complete | 117 | 24 | 0.03 | 0.03 | 0.282 |
| p01 | spread | 18 | 1 | 12 | 31,180 | complete | 155 | 31 | 0.04 | 0.04 | 0.290 |
| p01 | spread | 20 | 1 | 12 | 60,460 | complete | 161 | 31 | 0.05 | 0.05 | 0.292 |
| p01 | spread | 22 | 1 | 12 | 110,056 | complete | 267 | 64 | 0.08 | 0.08 | 0.311 |
| p01 | spread | 24 | 1 | 12 | 190,051 | complete | 289 | 67 | 0.11 | 0.11 | 0.374 |
| p01 | spread | 2 | 1 | 24 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| p01 | spread | 4 | 1 | 24 | 16 | complete | 9 | 2 | 0.00 | 0.00 | 0.333 |
| p01 | spread | 6 | 1 | 24 | 64 | complete | 17 | 4 | 0.01 | 0.01 | 0.294 |
| p01 | spread | 8 | 1 | 24 | 247 | complete | 30 | 6 | 0.01 | 0.01 | 0.333 |
| p01 | spread | 10 | 1 | 24 | 848 | complete | 34 | 7 | 0.01 | 0.01 | 0.353 |
| p01 | spread | 12 | 1 | 24 | 2,510 | complete | 60 | 19 | 0.02 | 0.02 | 0.350 |
| p01 | spread | 14 | 1 | 24 | 6,476 | complete | 73 | 24 | 0.03 | 0.03 | 0.438 |
| p01 | spread | 16 | 1 | 24 | 14,893 | complete | 116 | 39 | 0.04 | 0.05 | 0.388 |
| p01 | spread | 18 | 1 | 24 | 31,180 | complete | 156 | 62 | 0.06 | 0.06 | 0.397 |
| p01 | spread | 20 | 1 | 24 | 60,460 | complete | 162 | 64 | 0.07 | 0.07 | 0.420 |
| p01 | spread | 22 | 1 | 24 | 110,056 | complete | 268 | 115 | 0.12 | 0.12 | 0.429 |
| p01 | spread | 24 | 1 | 24 | 190,051 | complete | 293 | 128 | 0.14 | 0.14 | 0.478 |
| p01 | spread | 2 | 2 | 6 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.444 |
| p01 | spread | 4 | 2 | 6 | 81 | complete | 25 | 0 | 0.00 | 0.01 | 0.160 |
| p01 | spread | 6 | 2 | 6 | 729 | complete | 61 | 0 | 0.01 | 0.01 | 0.197 |
| p01 | spread | 8 | 2 | 6 | 5,281 | complete | 125 | 0 | 0.04 | 0.04 | 0.280 |
| p01 | spread | 10 | 2 | 6 | 26,025 | complete | 137 | 0 | 0.04 | 0.04 | 0.270 |
| p01 | spread | 12 | 2 | 6 | 94,449 | complete | 383 | 0 | 0.10 | 0.10 | 0.269 |
| p01 | spread | 14 | 2 | 6 | 275,577 | complete | 447 | 0 | 0.12 | 0.12 | 0.266 |
| p01 | spread | 16 | 2 | 6 | 686,401 | complete | 801 | 0 | 0.23 | 0.23 | 0.285 |
| p01 | spread | 18 | 2 | 6 | 1,518,409 | complete | 1,105 | 0 | 0.33 | 0.33 | 0.301 |
| p01 | spread | 20 | 2 | 6 | 3,064,209 | complete | 1,125 | 0 | 0.35 | 0.35 | 0.312 |
| p01 | spread | 22 | 2 | 6 | 5,748,249 | complete | 2,289 | 0 | 0.72 | 0.72 | 0.315 |
| p01 | spread | 24 | 2 | 6 | 10,161,633 | complete | 2,423 | 0 | 0.81 | 0.81 | 0.333 |
| p01 | spread | 2 | 2 | 12 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| p01 | spread | 4 | 2 | 12 | 81 | complete | 25 | 0 | 0.01 | 0.01 | 0.400 |
| p01 | spread | 6 | 2 | 12 | 729 | complete | 61 | 14 | 0.02 | 0.02 | 0.279 |
| p01 | spread | 8 | 2 | 12 | 5,281 | complete | 123 | 25 | 0.04 | 0.04 | 0.301 |
| p01 | spread | 10 | 2 | 12 | 26,025 | complete | 135 | 29 | 0.04 | 0.04 | 0.326 |
| p01 | spread | 12 | 2 | 12 | 94,449 | complete | 359 | 70 | 0.12 | 0.12 | 0.334 |
| p01 | spread | 14 | 2 | 12 | 275,577 | complete | 423 | 89 | 0.15 | 0.15 | 0.362 |
| p01 | spread | 16 | 2 | 12 | 686,401 | complete | 767 | 188 | 0.33 | 0.33 | 0.428 |
| p01 | spread | 18 | 2 | 12 | 1,518,409 | complete | 1,053 | 245 | 0.45 | 0.46 | 0.431 |
| p01 | spread | 20 | 2 | 12 | 3,064,209 | complete | 1,073 | 247 | 0.56 | 0.56 | 0.523 |
| p01 | spread | 22 | 2 | 12 | 5,748,249 | complete | 2,109 | 631 | 1.13 | 1.13 | 0.534 |
| p01 | spread | 24 | 2 | 12 | 10,161,633 | complete | 2,243 | 649 | 1.15 | 1.15 | 0.513 |
| p01 | spread | 2 | 2 | 24 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.333 |
| p01 | spread | 4 | 2 | 24 | 81 | complete | 25 | 8 | 0.01 | 0.01 | 0.360 |
| p01 | spread | 6 | 2 | 24 | 729 | complete | 61 | 22 | 0.02 | 0.02 | 0.361 |
| p01 | spread | 8 | 2 | 24 | 5,281 | complete | 123 | 37 | 0.05 | 0.05 | 0.382 |
| p01 | spread | 10 | 2 | 24 | 26,025 | complete | 135 | 41 | 0.06 | 0.06 | 0.452 |
| p01 | spread | 12 | 2 | 24 | 94,449 | complete | 283 | 113 | 0.14 | 0.14 | 0.491 |
| p01 | spread | 14 | 2 | 24 | 275,577 | complete | 337 | 139 | 0.16 | 0.16 | 0.463 |
| p01 | spread | 16 | 2 | 24 | 686,401 | complete | 759 | 278 | 0.39 | 0.39 | 0.516 |
| p01 | spread | 18 | 2 | 24 | 1,518,409 | complete | 1,047 | 435 | 0.61 | 0.62 | 0.585 |
| p01 | spread | 20 | 2 | 24 | 3,064,209 | complete | 1,067 | 443 | 0.62 | 0.62 | 0.577 |
| p01 | spread | 22 | 2 | 24 | 5,748,249 | complete | 2,095 | 950 | 1.21 | 1.21 | 0.577 |
| p01 | spread | 24 | 2 | 24 | 10,161,633 | complete | 2,233 | 1,033 | 1.55 | 1.56 | 0.693 |
| relaxed | spread | 2 | 1 | 6 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| relaxed | spread | 4 | 1 | 6 | 16 | complete | 16 | 0 | 0.00 | 0.00 | 0.125 |
| relaxed | spread | 6 | 1 | 6 | 64 | complete | 48 | 0 | 0.01 | 0.01 | 0.208 |
| relaxed | spread | 8 | 1 | 6 | 247 | complete | 180 | 0 | 0.04 | 0.04 | 0.200 |
| relaxed | spread | 10 | 1 | 6 | 848 | complete | 351 | 0 | 0.07 | 0.07 | 0.208 |
| relaxed | spread | 12 | 1 | 6 | 2,510 | complete | 735 | 0 | 0.17 | 0.17 | 0.235 |
| relaxed | spread | 14 | 1 | 6 | 6,476 | complete | 1,881 | 0 | 0.46 | 0.46 | 0.244 |
| relaxed | spread | 16 | 1 | 6 | 14,893 | complete | 2,799 | 0 | 0.66 | 0.66 | 0.235 |
| relaxed | spread | 18 | 1 | 6 | 31,180 | complete | 5,451 | 0 | 1.31 | 1.31 | 0.240 |
| relaxed | spread | 20 | 1 | 6 | 60,460 | complete | 8,490 | 0 | 3.48 | 3.48 | 0.410 |
| relaxed | spread | 22 | 1 | 6 | 110,056 | complete | 15,427 | 0 | 4.32 | 4.32 | 0.280 |
| relaxed | spread | 24 | 1 | 6 | 190,051 | complete | 21,594 | 0 | 6.20 | 6.20 | 0.287 |
| relaxed | spread | 2 | 1 | 12 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| relaxed | spread | 4 | 1 | 12 | 16 | complete | 16 | 0 | 0.00 | 0.00 | 0.250 |
| relaxed | spread | 6 | 1 | 12 | 64 | complete | 64 | 20 | 0.02 | 0.02 | 0.266 |
| relaxed | spread | 8 | 1 | 12 | 247 | complete | 215 | 67 | 0.06 | 0.06 | 0.284 |
| relaxed | spread | 10 | 1 | 12 | 848 | complete | 492 | 199 | 0.14 | 0.15 | 0.293 |
| relaxed | spread | 12 | 1 | 12 | 2,510 | complete | 1,068 | 485 | 0.33 | 0.33 | 0.308 |
| relaxed | spread | 14 | 1 | 12 | 6,476 | complete | 2,353 | 1,115 | 0.86 | 0.87 | 0.365 |
| relaxed | spread | 16 | 1 | 12 | 14,893 | complete | 4,221 | 2,042 | 2.00 | 2.05 | 0.473 |
| relaxed | spread | 18 | 1 | 12 | 31,180 | complete | 8,195 | 4,334 | 3.06 | 3.13 | 0.374 |
| relaxed | spread | 20 | 1 | 12 | 60,460 | complete | 11,839 | 5,965 | 4.89 | 5.07 | 0.413 |
| relaxed | spread | 22 | 1 | 12 | 110,056 | complete | 22,762 | 11,969 | 9.20 | 9.53 | 0.404 |
| relaxed | spread | 24 | 1 | 12 | 190,051 | complete | 33,184 | 17,426 | 13.49 | 13.77 | 0.407 |
| relaxed | spread | 2 | 1 | 24 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| relaxed | spread | 4 | 1 | 24 | 16 | complete | 16 | 6 | 0.01 | 0.01 | 0.312 |
| relaxed | spread | 6 | 1 | 24 | 64 | complete | 64 | 34 | 0.02 | 0.02 | 0.375 |
| relaxed | spread | 8 | 1 | 24 | 247 | complete | 213 | 130 | 0.09 | 0.09 | 0.404 |
| relaxed | spread | 10 | 1 | 24 | 848 | complete | 573 | 401 | 0.24 | 0.24 | 0.421 |
| relaxed | spread | 12 | 1 | 24 | 2,510 | complete | 1,387 | 1,069 | 0.60 | 0.61 | 0.431 |
| relaxed | spread | 14 | 1 | 24 | 6,476 | complete | 3,246 | 2,639 | 1.68 | 1.73 | 0.518 |
| relaxed | spread | 16 | 1 | 24 | 14,893 | complete | 7,059 | 5,695 | 3.51 | 3.65 | 0.497 |
| relaxed | spread | 18 | 1 | 24 | 31,180 | complete | 15,110 | 12,760 | 7.69 | 7.92 | 0.509 |
| relaxed | spread | 20 | 1 | 24 | 60,460 | complete | 22,730 | 19,082 | 11.61 | 11.87 | 0.511 |
| relaxed | spread | 22 | 1 | 24 | 110,056 | complete | 44,983 | 38,450 | 24.06 | 24.62 | 0.535 |
| relaxed | spread | 24 | 1 | 24 | 190,051 | not complete at that size (wall_time_limit) | 50,984 | 44,142 | 30.00 | 30.72 | 0.588 |
| relaxed | spread | 2 | 2 | 6 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| relaxed | spread | 4 | 2 | 6 | 81 | complete | 81 | 0 | 0.01 | 0.01 | 0.173 |
| relaxed | spread | 6 | 2 | 6 | 729 | complete | 423 | 0 | 0.09 | 0.09 | 0.222 |
| relaxed | spread | 8 | 2 | 6 | 5,281 | complete | 2,893 | 0 | 0.87 | 0.87 | 0.302 |
| relaxed | spread | 10 | 2 | 6 | 26,025 | complete | 9,077 | 0 | 2.85 | 2.85 | 0.314 |
| relaxed | spread | 12 | 2 | 6 | 94,449 | complete | 31,269 | 0 | 9.18 | 9.18 | 0.294 |
| relaxed | spread | 14 | 2 | 6 | 275,577 | complete | 86,236 | 0 | 28.09 | 28.09 | 0.326 |
| relaxed | spread | 16 | 2 | 6 | 686,401 | not complete at that size (wall_time_limit) | 76,931 | 0 | 30.00 | 30.00 | 0.390 |
| relaxed | spread | 2 | 2 | 12 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| relaxed | spread | 4 | 2 | 12 | 81 | complete | 81 | 0 | 0.02 | 0.02 | 0.272 |
| relaxed | spread | 6 | 2 | 12 | 729 | complete | 558 | 291 | 0.25 | 0.25 | 0.450 |
| relaxed | spread | 8 | 2 | 12 | 5,281 | complete | 3,203 | 1,680 | 1.30 | 1.31 | 0.406 |
| relaxed | spread | 10 | 2 | 12 | 26,025 | complete | 9,513 | 5,993 | 4.00 | 4.09 | 0.420 |
| relaxed | spread | 12 | 2 | 12 | 94,449 | complete | 31,171 | 19,836 | 15.02 | 15.29 | 0.482 |
| relaxed | spread | 14 | 2 | 12 | 275,577 | not complete at that size (wall_time_limit) | 59,919 | 39,155 | 30.00 | 30.70 | 0.501 |
| relaxed | spread | 2 | 2 | 24 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.333 |
| relaxed | spread | 4 | 2 | 24 | 81 | complete | 81 | 48 | 0.03 | 0.03 | 0.358 |
| relaxed | spread | 6 | 2 | 24 | 729 | complete | 648 | 500 | 0.27 | 0.27 | 0.410 |
| relaxed | spread | 8 | 2 | 24 | 5,281 | complete | 3,943 | 3,160 | 1.79 | 1.80 | 0.453 |
| relaxed | spread | 10 | 2 | 24 | 26,025 | complete | 12,451 | 10,673 | 6.73 | 6.85 | 0.540 |
| relaxed | spread | 12 | 2 | 24 | 94,449 | not complete at that size (wall_time_limit) | 37,990 | 34,282 | 30.00 | 31.75 | 0.790 |
| unbounded | spread | 2 | 1 | 6 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| unbounded | spread | 4 | 1 | 6 | 16 | complete | 16 | 0 | 0.00 | 0.00 | 0.188 |
| unbounded | spread | 6 | 1 | 6 | 64 | complete | 64 | 0 | 0.01 | 0.01 | 0.234 |
| unbounded | spread | 8 | 1 | 6 | 247 | complete | 247 | 0 | 0.08 | 0.08 | 0.320 |
| unbounded | spread | 10 | 1 | 6 | 848 | complete | 848 | 0 | 0.38 | 0.38 | 0.442 |
| unbounded | spread | 12 | 1 | 6 | 2,510 | complete | 2,510 | 0 | 1.20 | 1.20 | 0.479 |
| unbounded | spread | 14 | 1 | 6 | 6,476 | complete | 6,476 | 0 | 3.10 | 3.10 | 0.478 |
| unbounded | spread | 16 | 1 | 6 | 14,893 | complete | 14,893 | 0 | 3.92 | 3.92 | 0.264 |
| unbounded | spread | 18 | 1 | 6 | 31,180 | complete | 31,180 | 0 | 7.40 | 7.40 | 0.237 |
| unbounded | spread | 20 | 1 | 6 | 60,460 | complete | 60,460 | 0 | 15.29 | 15.29 | 0.253 |
| unbounded | spread | 22 | 1 | 6 | 110,056 | complete | 110,056 | 0 | 27.03 | 27.03 | 0.246 |
| unbounded | spread | 24 | 1 | 6 | 190,051 | not complete at that size (wall_time_limit) | 110,201 | 0 | 30.00 | 30.00 | 0.272 |
| unbounded | spread | 2 | 1 | 12 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.500 |
| unbounded | spread | 4 | 1 | 12 | 16 | complete | 16 | 0 | 0.00 | 0.00 | 0.250 |
| unbounded | spread | 6 | 1 | 12 | 64 | complete | 64 | 20 | 0.02 | 0.02 | 0.297 |
| unbounded | spread | 8 | 1 | 12 | 247 | complete | 247 | 96 | 0.13 | 0.13 | 0.522 |
| unbounded | spread | 10 | 1 | 12 | 848 | complete | 848 | 490 | 0.25 | 0.25 | 0.292 |
| unbounded | spread | 12 | 1 | 12 | 2,510 | complete | 2,510 | 1,710 | 0.85 | 0.87 | 0.340 |
| unbounded | spread | 14 | 1 | 12 | 6,476 | complete | 6,476 | 4,500 | 2.09 | 2.15 | 0.322 |
| unbounded | spread | 16 | 1 | 12 | 14,893 | complete | 14,893 | 9,658 | 4.94 | 5.11 | 0.332 |
| unbounded | spread | 18 | 1 | 12 | 31,180 | complete | 31,180 | 20,955 | 10.90 | 11.29 | 0.350 |
| unbounded | spread | 20 | 1 | 12 | 60,460 | complete | 60,460 | 39,672 | 24.46 | 25.49 | 0.405 |
| unbounded | spread | 22 | 1 | 12 | 110,056 | not complete at that size (wall_time_limit) | 58,267 | 43,722 | 30.00 | 30.62 | 0.515 |
| unbounded | spread | 2 | 1 | 24 | 4 | complete | 4 | 0 | 0.00 | 0.00 | 0.250 |
| unbounded | spread | 4 | 1 | 24 | 16 | complete | 16 | 6 | 0.01 | 0.01 | 0.312 |
| unbounded | spread | 6 | 1 | 24 | 64 | complete | 64 | 34 | 0.02 | 0.02 | 0.344 |
| unbounded | spread | 8 | 1 | 24 | 247 | complete | 247 | 165 | 0.09 | 0.09 | 0.364 |
| unbounded | spread | 10 | 1 | 24 | 848 | complete | 848 | 653 | 0.35 | 0.36 | 0.415 |
| unbounded | spread | 12 | 1 | 24 | 2,510 | complete | 2,510 | 2,165 | 1.10 | 1.12 | 0.438 |
| unbounded | spread | 14 | 1 | 24 | 6,476 | complete | 6,476 | 5,688 | 3.89 | 4.05 | 0.601 |
| unbounded | spread | 16 | 1 | 24 | 14,893 | complete | 14,893 | 12,595 | 9.95 | 10.22 | 0.668 |
| unbounded | spread | 18 | 1 | 24 | 31,180 | complete | 31,180 | 27,512 | 22.74 | 23.18 | 0.729 |
| unbounded | spread | 20 | 1 | 24 | 60,460 | not complete at that size (archive_limit) | 56,958 | 50,000 | 29.44 | 30.80 | 0.517 |
| unbounded | spread | 2 | 2 | 6 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.222 |
| unbounded | spread | 4 | 2 | 6 | 81 | complete | 81 | 0 | 0.02 | 0.02 | 0.198 |
| unbounded | spread | 6 | 2 | 6 | 729 | complete | 729 | 0 | 0.15 | 0.15 | 0.209 |
| unbounded | spread | 8 | 2 | 6 | 5,281 | complete | 5,281 | 0 | 2.87 | 2.87 | 0.543 |
| unbounded | spread | 10 | 2 | 6 | 26,025 | complete | 26,025 | 0 | 10.55 | 10.55 | 0.405 |
| unbounded | spread | 12 | 2 | 6 | 94,449 | complete | 94,449 | 0 | 28.63 | 28.63 | 0.303 |
| unbounded | spread | 14 | 2 | 6 | 275,577 | not complete at that size (wall_time_limit) | 63,972 | 0 | 30.00 | 30.01 | 0.469 |
| unbounded | spread | 2 | 2 | 12 | 9 | complete | 9 | 0 | 0.00 | 0.00 | 0.444 |
| unbounded | spread | 4 | 2 | 12 | 81 | complete | 81 | 0 | 0.04 | 0.04 | 0.506 |
| unbounded | spread | 6 | 2 | 12 | 729 | complete | 729 | 396 | 0.52 | 0.53 | 0.719 |
| unbounded | spread | 8 | 2 | 12 | 5,281 | complete | 5,281 | 2,952 | 2.60 | 2.62 | 0.493 |
| unbounded | spread | 10 | 2 | 12 | 26,025 | complete | 26,025 | 18,604 | 13.21 | 13.45 | 0.507 |
| unbounded | spread | 12 | 2 | 12 | 94,449 | not complete at that size (wall_time_limit) | 32,599 | 29,086 | 30.00 | 30.80 | 0.920 |
| unbounded | spread | 2 | 2 | 24 | 9 | complete | 9 | 0 | 0.01 | 0.01 | 0.889 |
| unbounded | spread | 4 | 2 | 24 | 81 | complete | 81 | 48 | 0.06 | 0.06 | 0.679 |
| unbounded | spread | 6 | 2 | 24 | 729 | complete | 729 | 564 | 0.50 | 0.51 | 0.687 |
| unbounded | spread | 8 | 2 | 24 | 5,281 | complete | 5,281 | 4,432 | 6.18 | 6.36 | 1.170 |
| unbounded | spread | 10 | 2 | 24 | 26,025 | complete | 26,025 | 23,120 | 25.60 | 25.98 | 0.984 |
| unbounded | spread | 12 | 2 | 24 | 94,449 | not complete at that size (wall_time_limit) | 26,161 | 25,472 | 30.00 | 30.82 | 1.147 |

## Fix round 2

The re-review (`task-13a-rereview-1.md`) found I1 and I3 addressed. I2 was only partly addressed and is still Important. The extra change (unknown weekly hours set aside) stays; the re-review accepts it once this is fixed.

Head: `8ff5100adac4a5757508a8be07019f44af23c8e0`. `l0-local-release` has not moved since 0931cbb, so there was no rebase.

Commits:
- 3e564f5: Fix round 2, the route search;
- 8ff5100: Fix round 2, the register.

### What remained of I2

A set-aside option's `violations` came from its option-alone check, and that check also carries the person's starting position (the empty route). So options were blamed for breaches they did not cause:
- the undated reduced-hours option read "ruled out: workload", the very breach it would cure once dated;
- a dated course with an unknown cost picked up a reserve the person was already short of.

### The fix (`planning/search.py`)

- Each set-aside option's `violations` leaves out any breach the empty route already has in the same month (same code and month).
- The result reports those breaches once, as the new field `starting_violations` (the empty route's own violations), so Task 14 can say what the person's current position already breaks.
- `codes` and `kind` are unchanged. They stay the proof of why no route can contain the option, so the outcome logic is untouched.
- The pack records do not change: P01's figures break nothing at the start.
- ADR 0016 decision 4 and its Task 14 note now say the same. The register's OPT1-07 row names the two new tests.

### Tests, each failing first

- `test_route_search.py::test_an_option_is_never_blamed_for_a_breach_the_person_s_starting_position_already_has`, the reviewer's I1 instance: `starting_violations` is workload in 2027-03 and 2027-04; the undated option's `unresolved` is `[dates_unknown]` and its `violations` is `[]`.
- `test_route_search.py::test_a_course_with_an_unknown_cost_is_not_blamed_for_a_reserve_already_broken`, the reviewer's reserve case: £600 opening cash and £1,000 living costs, with pay arriving late. `starting_violations` is the reserve in 2027-01; the course's `unresolved` is `[cost_unknown]` and its `violations` is `[]`.
- An added assertion on `test_an_option_without_weekly_hours_is_set_aside_as_unknown_whatever_the_known_load`, which answers the re-review's Minor on the extra change: the 38-of-36-hours breach appears once, in `starting_violations`, and the option's `violations` is `[]`. That record now reads "to confirm: weekly hours", beside the result's statement that the person's own hours are already over.

RED on today's code:
- The tests fail with `AttributeError: 'SearchResult' object has no attribute 'starting_violations'` (3 failed).
- The defect itself, printed on today's code:
  ```
  undated: [('reduced-undated', ['dates_unknown'], ['workload'])]
  unpriced: [('unpriced', ['cost_unknown'], ['reserve'])]
  ```

GREEN after the fix: the route tests give `58 passed` (search, oracle, pack, layers, tool).

### Checks

- `make check`: exit 0, backend `1618 passed, 333 deselected`, Vitest 36 files and 319 tests, ruff and mypy clean (333 files), the fixture validator passed, no warnings.
- `make acceptance`: not run (no stack behaviour changed; lock not taken).
- Live calls: none.
- One test of mine passed `opening` twice through a helper on its first run, a test-code error I fixed before GREEN.
