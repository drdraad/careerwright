# ADR 0016: The route search core: the declared tree, sound pruning, the archive, layers and families

- Status: Accepted for Task 13a (Sprint 6a: S6.1, S6.2, S6.5, S6.6, S6.7).
  - **Rulings (not R6; each costs little if wrong):** decisions 2 (one bridge role means one
    `work` action), 3 (the search reads the base scenario only), 7 (a payment plan is a
    schedule variant, not a family) and 10 (proposed records are searched and qualified, not
    left out).
- Date: 2026-10-31
- Requirements: OPT1-01, OPT1-02, OPT1-05 (coverage), OPT1-06 (the run's record, in memory),
  OPT1-07, OPT1-08, OPT1-09 (evaluation), OPT1-10 (complete runs), OPT1-12 (in part), OPT1-13,
  OPT1-14 (in part), OPT1-15 (in part), OPT1-16, ROU1-01 to ROU1-03, and the PARETO, TRACE01
  (layers), DIRECTAI, FAMILY and LIMITS (complete coverage) families; spec sections 12, 18
  and 20; ADR 0013 (the checker it calls), ADR 0011 (pack 0.2.0)

## Context

Every computed route will come from this search. ADR 0013 built the monthly input and the
route checker for one fixed route; the search must find every feasible schedule in the
declared monthly model, keep the dominated ones for the second and third layers, and say
truthfully whether it looked everywhere. The specification fixes the solver (deterministic
exhaustive DFS in Python, OPT-1), forbids pruning on dominance, readiness or accumulated
economic cost, and asks for an independent oracle that shares no code with what it checks.
Durability (a disk archive, a child process, efficient ranking) is Task 13b, sized from the
measurements here.

## Decisions

1. **Three pure modules in `careerwright/planning`:** `search.py` (the tree, the pruning
   rules, coverage, the result), `layers.py` (F1 to F3 by peeling) and `families.py` (route
   families and equal points). Candidate evaluation is `check_route`, so every gate,
   timetable, cash and workload rule is Task 11's, and readiness is the capability model's
   (RDY-1). No SQL, network or model: a test proves the search's import closure loads no
   database, HTTP or model client. Nothing is persisted, served or shown yet (Tasks 13b, 14).

2. **The declared tree.** Concepts in a canonical order (the earliest start among a concept's
   variants, then its ID; a concept's variants by start, then ID). A node is a selected set in
   that order and its children add one variant of a later concept, so each allowed set is
   visited exactly once and order and parallelism come from the variants' dates. Allowed: at
   most six actions, one start per concept, one concept per exclusive group and one bridge role.
   **Ruling:** "at most one bridge-role transition" (spec section 12) is read as at most one
   `work` action; an apprenticeship is a learning action with its own offer gate (ADR 0013
   decision 3). The empty route is the root: zero actions can already reach readiness. A
   catalogue beyond the M0 bounds (more than 24 concepts, more than two starts for a concept,
   more than 24 months) is refused with `MODEL_SCOPE_EXCEEDED`, never searched in part, and a
   search without the target's readiness basis is refused with `VALIDATION_FAILED`.

3. **The base scenario only (ruling).** The layers compare `T` and `C` in the base scenario
   (spec section 12, `ω0`), so candidates are checked there. The delay, no-award and no-offer
   stress cases stay `evaluate_route` on a chosen route (ADR 0013 decision 9).

4. **Sound pruning** (`PRUNING_VERSION = "sound-pruning-1"`). A subtree is cut only when no
   route in it can be feasible. The proofs are in `search.py`'s docstring; in short:
   1. an input-level unknown (an unstated hard limit, availability, or the baseline an
      economic comparison needs) is in every route: nothing further is checked;
   2. a variant whose own finding every route containing it repeats is set aside for the whole
      tree, with its reasons: unknown dates, cost, entry requirements or weekly hours, a
      payment due before the planning start, a start before it, a passed application deadline,
      or, alone, a cost or a month's payments above a cap;
   3. a route's direct cost and each month's payments are sums of each variant's own, never
      below zero, so a child already above the direct-spend or monthly payment cap is never
      checked;
   4. conflicting work patterns and session clashes persist;
   5. a workload breach persists unless a later variant active that month could lower the
      job's hours (the job's hours come from the first variant in route order with a work
      pattern);
   6. a prerequisite stays unusable unless a later variant grants it in time.
   Never pruned: the reserve and the deficit cap (later receipts lift a month), an
   application completing late or in its deadline's month (a later one can be in time),
   readiness, and the objectives (no dominance pruning; economic cost can fall as a route
   grows).

5. **The archive** keeps every distinct feasible schedule that reaches the readiness milestone,
   dominated ones included, in memory under the 50,000 cap (Task 13b moves it to disk). A
   feasible schedule without the milestone is counted, not archived: it is not a route to the
   target. Each schedule keeps its route (variant IDs in canonical order), family, months to
   the milestone and its month, objective, direct and economic cost, verdict, qualifications,
   conditions and unmet preferences, and its layer. The full ledgers are not kept: the check
   is deterministic, so `check_route` recomputes them for a chosen route.

6. **Layers.** F1 to F3 by iterative nondominated peeling over the whole archive; each peel
   finds the nondominated set with one sort (in time order, a point is nondominated when it is
   cheaper than everything sooner and nothing at its time is cheaper). Equal points share a
   layer; a point beyond F3 has none. `layers_exact` is true only with complete coverage, and
   then only over the declared model and catalogue.

7. **Families** (ROU-1) are for presentation only; grouping never changes the archive. A
   family is its canonical action graph: each action's concept, its way of being taken where
   one intake is offered several ways (`outcomes_from`: full or part time is a different
   family), its work pattern, and its financing and conditional gates; and the precedence
   between actions (one finishing in a month before another starts; neither is parallel). A
   later intake of the same sequence is a schedule of the same family. **Ruling:** another
   payment plan for the same action is a schedule variant, not a family; supports and offer
   gates are the "material financing" the spec names. A family's best rank is its lowest layer,
   labelled so. Equal points group the schedules at the same coordinates, every one kept.
   Known limit: a later intake of one "way" offering would count as another family; no pack
   record has one (ADR 0013 decision 13, one offering per option).

8. **What a result says.** Coverage is `complete` only when the declared tree is exhausted
   under these rules, else `budget_truncated` with the exact stop reason (state, wall time or
   archive limit), the branches left unexplored and the narrowings that would help (fewer
   concepts, one start, a shorter horizon). The outcome is one of:
   - `routes_found` (lead with "Best trade-offs found");
   - `none_found_before_limit` (a stopped run with nothing found: never "no route");
   - `unresolved` (complete, nothing proved feasible, and something unknown: a blocking input,
     an unresolved candidate, a feasible route whose readiness the capability model cannot yet
     assess, or an option set aside for an unknown, conservatively);
   - `no_route_in_bounded_model` (complete, and nothing unknown: `NO_ROUTE_IN_BOUNDED_MODEL`).
   The run records its input version, catalogue label, matrix and definition versions,
   objective basis, scenario, algorithm and pruning versions, limits, instance size (with the
   selection space before pruning), canonical order, expanded states, the counts of each kind
   of candidate, what was set aside and pruned, and its time. A complete run on the same input
   reproduces the same result but for its time.

9. **Limits.** `M0SearchLimits` is spec section 18's: the declared bounds, then 30 seconds,
   1,000,000 expanded states and 50,000 archived schedules, checked before each candidate. The
   clock is injected, so the wall-time stop is tested without waiting.

10. **Review states (ruling).** S6.1's "reviewed offering" is read as an offering in the
    catalogue the option checkpoint passes to the search. Proposed records are searched, and
    the checker's qualifications carry them into every schedule's verdict (R9): explorable,
    never unqualified.

11. **The independent oracle** (`tests/support/route_oracle.py`, test code) enumerates the
    Cartesian product of each concept's choices and checks every route with its own
    month-by-month rules, written again from the specification and ADR 0013, and its own layer
    rule (the longest dominance chain). It imports only the input data types and the
    capability model's `assess`: nothing from the search, the checker, the ledgers or the month
    helpers. Generated tiny instances (both caps, work patterns, sessions, workload,
    prerequisites, groups, bridge roles, support, debt, the deficit cap, applications, every
    unknown) must give the search exactly the oracle's archive, objectives, layers and count of
    milestone-less feasible routes, and the independent checker must agree with `check_route`
    on every candidate.

## Consequences

- **Measured sizes** (`tools.route_search_sizes`, synthetic pack-shaped instances, on the
  2026-10-31 arm64 machine; the task report has the table). Each check costs about 0.2 to
  0.7 ms, rising with the horizon, so the 30-second limit binds at about 48,000 to 80,000
  expanded states; the 1,000,000-state limit never bound. Largest sizes that complete:
  - with P01's limits, the whole M0 bound (24 concepts, two starts, 24 months: 10,161,633
    selected sets) in 2,487 states and 1.7 seconds: the caps prune almost everything;
  - with a £5,000 cap and 45 hours, 24 concepts with one start at every horizon (34,956
    states, 19.5 s at 24 months) and 12 with two starts (29,073 states, 17 s); 14 with two
    starts stopped at 30 seconds;
  - with no binding limit (the whole selection space is checked), 18 to 20 concepts with one
    start and 10 with two (26,025 states, 9 to 14 s); the next size stopped, mostly at the
    50,000-schedule archive limit before the clock, because almost every set reaches the
    milestone.
- **The reviewed pack completes at once:** four targets, at most four concepts each, and
  every offering is set aside until the person confirms a date, a cost, a timetable or an
  entry requirement (Task 12). No pack instance needs Task 13b's machinery to complete. Even
  a catalogue the size of the whole pack (ten synthetic pack-shaped courses, two starts each:
  26,025 selected sets) completes in under 15 seconds with no limit binding.
- **For Task 13b:** about 40% of a check is the readiness assessment, repeated for the same
  completed offerings across candidates; memoising `assess` by its completed set would be the
  cheapest speed-up. Peeling sorts once per layer, so a 50,000-point archive ranks in well under
  a second, but ranking still runs inside the search's call and outside its clock.
- **For Task 14:** show the outcome's words, the set-aside reasons ("what to confirm"), the
  narrowings when stopped, families first with their best layer, and equal points with every
  route behind them.
- **For Task 12a:** a new checker finding (stacked funding left unresolved, unknown work
  rights; ADR 0013's 2026-10-31 amendment) must be classed for rule 2 (is it the variant's
  own, repeated in every route containing it?) and written into the oracle too, or the oracle
  tests will disagree. Workspace options read beside the pack are searched like pack records
  and qualified like them (decision 10); a concept ID is an opaque string, so provisional and
  corroborated IDs need nothing here.
- **Not done here:** persistence, API, UI and the child process (Tasks 13b, 14); the stress
  scenarios inside the search (decision 3); the instance from P01's stored inputs, which needs
  Task 12a's store.
