# ADR 0016: The route search core: the declared tree, sound pruning, the archive, layers and families

- Status: Accepted for Task 13a (Sprint 6a: S6.1, S6.2, S6.5, S6.6, S6.7), and amended for
  Task 13b (Sprint 6b: S6.3, S6.4, S6.8, as the L0 deferrals size them; the amendment at the
  end).
  - **Rulings (not R6; each costs little if wrong):** decisions 2 (one bridge role means one
    `work` action), 3 (the search reads the base scenario only), 7 (a payment plan is a
    schedule variant, not a family) and 10 (proposed records are searched and qualified, not
    left out); Task 13b's are listed in its amendment.
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

4. **Sound pruning** (`PRUNING_VERSION = "sound-pruning-2"`; fix round 1 changed rule 2 and
   the order). A subtree is cut only when no route in it can be feasible. The proofs are in
   `search.py`'s docstring; in short:
   1. an input-level unknown (an unstated hard limit, availability, or the baseline an
      economic comparison needs) is in every route: nothing further is checked;
   2. a variant whose own finding every route containing it repeats is set aside for the whole
      tree, with its reasons: unknown dates, cost, entry requirements or weekly hours, a
      payment due before the planning start, a start before it, a passed application deadline,
      or, alone, a cost or a month's payments above a cap. Unknown weekly hours are read from
      the variant itself (dated, active in the horizon, no hours stated), even where the checker
      reports that month as over the limit. This screen runs before any other cut, the empty
      route's included, so every option set aside for an unknown reaches the outcome (review
      13a, Important 1: the empty route's workload cut once hid an undated option that could
      have lowered the job's hours). Each set-aside record keeps everything its own check found:
      its unknowns (`unresolved`) apart from the rules it breaks as stated, alone
      (`violations`). A breach the empty route already has in the same month is the person's
      starting position, not the option's: it is left out of `violations` and told once, on
      the result (`starting_violations`), so an option is never blamed for a reserve already
      short or hours already over, which it might even cure (fix round 2, re-review 13a, I2).
      `codes` and `kind` stay the proof of why no route can contain the option;
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
   archive limit), the branches left unexplored and the narrowings that could help (fewer
   concepts, one start, a shorter horizon; which ones, decision 21). The outcome is one of:
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
  2026-10-31 arm64 machine; the task report has both tables). These hold for intakes spread
  across the horizon (`spread`, fix round 1). The first run kept every intake in months 1 to
  9 (`early`), so its 12- and 24-month rows grew only the cost of each check (review 13a,
  Important 3). Each check costs about 0.2 to 1.2 ms, rising with the horizon and with the
  number of completion months readiness is assessed at, so the 30-second limit binds at about
  26,000 to 110,000 expanded states; the 1,000,000-state limit never bound. Largest sizes that
  complete, with spread intakes:
  - with P01's limits, the whole M0 bound (24 concepts, two starts, 24 months: 10,161,633
    selected sets) in 2,233 states and 1.6 seconds: the caps prune almost everything, whatever
    the dates;
  - with a £5,000 cap and 45 hours, at 24 months 22 concepts with one start (44,983 states,
    24 s) and 10 with two (12,451 states, 6.7 s); at 12 months 24 and 12;
  - with no binding limit (the whole selection space is checked), at 24 months 18 concepts
    with one start (31,180 states, 23 s) and 10 with two (26,025 states, 26 s); at 12 months
    20 and 10. The next sizes stopped at the clock or, with one start over 24 months, at the
    50,000-schedule archive limit.
  - At 6 months no spread instance reaches the milestone (most courses start too late), so
    those rows size a tree with nothing to find.
- **The reviewed pack completes at once:** four targets, at most four concepts each, and
  every offering is set aside until the person confirms a date, a cost, a timetable or an
  entry requirement (Task 12). Two also break a rule as stated: C04 paid in full (£2,995 above
  both of P01's £1,500 caps) and C09 (no admission in the catalogue; its hours beside P01's
  job). No pack instance needs Task 13b's machinery to complete. Even
  a catalogue the size of the whole pack (ten synthetic pack-shaped courses, two starts each:
  26,025 selected sets) completes with no limit binding: in 13 seconds over 12 months and 26
  over 24 months with spread intakes, close to the 30-second limit.
- **For Task 13b:** about 40% of a check is the readiness assessment, repeated for the same
  completed offerings across candidates; memoising `assess` by its completed set would be the
  cheapest speed-up. Peeling sorts once per layer, so a 50,000-point archive ranks in well under
  a second, but ranking still runs inside the search's call and outside its clock.
- **For Task 14:** show the outcome's words; what the person's starting position already
  breaks (`starting_violations`), once; for each option set aside, "what to confirm" (its
  `unresolved` list) apart from "what already rules it out as stated" (its `violations`), so
  the person is never told to confirm something that would still leave the option ruled out,
  nor that an option is ruled out by their own position (C09: confirm its entry requirements
  and cost; as stated, nothing grants its admission and its 35 hours a week exceed the 40
  available beside P01's job); the narrowings when stopped;
  families first with their best layer; and equal points with every route behind them.
- **For Task 12a:** a new checker finding (stacked funding left unresolved, unknown work
  rights; ADR 0013's 2026-10-31 amendment) must be classed for rule 2 (is it the variant's
  own, repeated in every route containing it?) and written into the oracle too, or the oracle
  tests will disagree. Workspace options read beside the pack are searched like pack records
  and qualified like them (decision 10); a concept ID is an opaque string, so provisional and
  corroborated IDs need nothing here.
- **Not done here:** persistence, API, UI and the child process (Tasks 13b, 14); the stress
  scenarios inside the search (decision 3); the instance from P01's stored inputs, which needs
  Task 12a's store.

## Amendment, 2026-10-31 (Task 12a): the new findings, classed

Task 12a added checker findings (ADR 0013, Task 12a's settlement). Each is classed for the
pruning rules, `PRUNING_VERSION` is now `sound-pruning-4` (fix round 1), and the oracle writes
each rule again from its own reading, its generated cases reaching every one:

- **Rule 1** (input-level, in every route): `work_rights_unknown` and `work_rights_not_held`
  come from the inputs alone.
- **Rule 2** (a variant's own, set aside): `entry_requirements_not_met`,
  `eligibility_unconfirmed` and `stacking_unconfirmed` are computed from the variant alone (its
  answers, its stated fee, its own supports), so every route containing it repeats them.
- **Rule 3** (spend caps): `repayments_above_payment_cap` comes from repayments the inputs fix;
  adding a variant never lowers them, so a node with it is cut as the monthly payment cap.
- **Rule 4** (persists): `job_transitions`. Adding a variant never takes away an offer still to
  be accepted, so a node with two is cut (`PruningRule.JOB_TRANSITIONS`). Decision 2's tree
  bound (one `work` action) stands beside it.
- A month row the checker leaves null never reaches rule 3: its sums come from each variant
  checked alone, whose amounts are all known (rule 2 sets aside an option whose amounts are
  not), so a node whose own rows are null is summed all the same.

Fix round 1 (review 12a):

- **Rule 2 and rule 4:** `exclusive_schemes` is a variant's own violation where its own
  supports hold both schemes, and persists across two variants (adding a variant never takes
  away a counted support), so a node with it is cut (`PruningRule.EXCLUSIVE_SCHEMES`).
- **Never pruned, never a variant's own:** `scheme_shared_unconfirmed` (one scheme on two
  options) needs two variants and is unresolved.
- **A condition, not a finding:** an option behind an application with no admission recorded
  and no application in the route rests on applying in time (ADR 0013 settlement, item 9), so
  rule 6 no longer meets it.
- **The outcome:** a complete run whose starting position breaks a limit no option can lower
  (existing repayments above the monthly payment cap) says `no_route_in_bounded_model`
  whatever is set aside or unstated; decision 8 is otherwise unchanged. The oracle's property
  test now checks the outcome both ways: the search's equals the oracle's.

## Amendment, 2026-10-31 (Task 13b): the search as a run, bounded and ranked

Sprint 6b, sized by the product owner's yes of 31 October 2026 (the specification's section
22, "L0 deferrals"): L0 keeps no disk-backed archive, checkpoints or resume, and no separate
child process. The caps, their exact stop reasons, the separate rank stage, the truncation
wording and the 50,000-point ranking benchmark stay. Requirements: OPT1-03 (as deferred),
OPT1-04, OPT1-05 (run states), OPT1-06 (stored), OPT1-07 (API), OPT1-09 (as deferred),
OPT1-10 (limited runs), OPT1-11, OPT1-12 (in flight), OPT1-15, LIMITS-01 to LIMITS-06,
STATE-03, DUR-05, and API-02's `SOLVE_LIMIT_REACHED`. Task 13b's fix round 1 amended
decisions 8, 14, 15, 19 and 20 and added 21 (the narrowings) and 22 (one solve at a time).

12. **A route solve is a run kind with its own workflow.** `route_solve` calls no model and
    needs no key, so it is no `RunTask` on the model activity (whose every step is a model
    call's: its key, spend and attempt rows). Like an acquisition it is a keyless kind
    (`KEYLESS_KINDS`): the same run record, outbox, status events, cancellation and
    publication (`careerwright.identity.workflow.publish_outcome`), and one bounded activity
    (`careerwright.planning.solve_runs`) run by one DBOS step in its own workflow
    (`careerwright.planning.workflow`, composed in `careerwright.worker`). No second model-call
    path exists. It needs no route out, so demo workspaces and the offline demo may run it
    (`OUTBOUND_KINDS` names the keyless kinds that may not). The existing workflows' step
    sequences are unchanged, so the DBOS `application_version` stays `careerwright-l0-1`.
13. **The snapshot.** `POST /v1/workspaces/{id}/planning/solves` takes the planning inputs
    version the person saw (a newer one is `STALE_INPUT_VERSION`), a target title, the
    comparison's first month (this month or later) and its horizon (1 to 24 months), with an
    Idempotency-Key through `run_idempotent`, under the workspace's lock. It compiles the
    person's stored inputs, the profile's two caps, the target's options with the person's
    answers in them and the target's readiness basis (the matrix, evidence and statements at
    the capability version, with the person's outcome decisions) into one `MonthlyInput`, and
    seals it, with every limit, into the run (`SolveSnapshot`). The run pins the profile
    version it read. A later edit is a new version and never reaches a solve under way
    (OPT1-12). What a solve cannot start from is refused with its code and never run: a stale
    version, a target that is not the person's, a target with no options (**ruling**: never an
    empty catalogue searched into "no route"), a past start, an input a solve needs (named),
    or a catalogue beyond the M0 bounds (`MODEL_SCOPE_EXCEEDED`).
14. **An idempotent solve identity.** `solve_id` hashes the monthly input's version, the
    limits, the rank stage's limit and the algorithm and pruning versions. The same solve
    asked for while one is queued or running joins it (200, the same run), unless the person
    has asked to cancel that one: a cancel only records a request until the worker publishes
    it, so the new request is a new run (202); a replayed Idempotency-Key returns its receipt.
15. **Attempts, and a crash.** Each execution records an attempt
    (`route_solve_attempts`). An execution finds any attempt its predecessor left unfinished
    and marks it `interrupted`: never a truncated result. With no checkpoint (spec section 22)
    the solve starts again from the start under a new attempt ID; a run makes at most three,
    then fails `unknown_failure`. The DBOS step is the one retry owner and retries only a store
    outage (a re-run re-solves; the solve is pure and costs nothing); DBOS recovers a crashed
    worker's workflow the same way. A run whose result was stored before a crash returns it.
    However a run ends, the transaction that publishes its end also settles any attempt still
    unfinished (`solve_runs.settle_attempts`, which the worker composes into the activity
    runtime by kind, so identity imports nothing of planning): `cancelled` on a cancelled run
    (its search stops at its next check, or its worker is gone), else `interrupted` (it never
    finished: its store went away, its result could not be stored, or its worker stopped). So
    no attempt reads as running once its run has ended, whichever of the workflow, the worker
    loop's cancel or the reconciler publishes it.
16. **The archive** stays in memory under the caps, as decision 5 has it, and is never
    evicted to fit memory. A stopped search keeps everything it met: a state-limited run's
    archive is exactly the complete run's archive up to where it stopped, in the order met,
    and replays exactly (OPT1-10); a wall-time-limited one is not promised the same prefix.
17. **Two stages, each with its own time** (S6.8; review 13a, M3). **Ruling: the rank stage
    has its own named limit, not time inside the search's budget.** The search stage
    (`search_archive`) keeps the 30 seconds, 1,000,000 states and 50,000 schedules exactly as
    Task 13a measured them, read before each candidate on its own clock (`elapsed_ms`). The
    rank stage (`rank_archive`) then layers the archive, and groups families and equal points,
    on its own clock (`rank_ms`) under `RANK_SECONDS = 5`, read before each of its four passes;
    the result records both. Reaching it raises `RankLimitReachedError`: the attempt ends
    `rank_limit_reached`, the run fails `rank_limit_reached` (a new failure class), and no
    result claims ranks it lacks. Why a limit of its own: the 30-second limit is the search's
    as the specification states it and as Task 13a measured it; giving the ranking a slice of
    it would stop the search earlier than measured. The bound is far from binding: the whole
    rank stage on an archive the search filled to its 50,000 cap took 0.99 s
    (`tools.rank_benchmark`, below). The attempt's `stage` says `ranking` once the search
    stage has ended, so the stage is observable while it runs.
18. **The efficient two-objective layering** (`layers.rank`): one sort by time then cost, and
    one pass in which each layer keeps its tail (its cheapest point, taken last); a point's
    layer is the first whose tail does not dominate it. That is one more than the deepest
    layer of anything dominating it, which is what peeling gives; Sprint 6a's peeling stays as
    the reference it is qualified against. It equals peeling on 400 generated point sets with
    heavy ties (Hypothesis), on 50,000 points of five shapes, and on the archive of every
    generated oracle instance (all complete). Peeling was never quadratic either (one sort per
    layer); at 50,000 points both take hundredths of a second.
19. **Cancellation.** The search takes a cancel check, read before each candidate and before
    each rank pass. A daemon thread reads the person's request every 0.2 s and sets an event;
    the check reads only the event (`solve_runs.cancel_watch`), so the search never waits on
    the store, and a slow store is never charged to the search's 30 seconds or the rank
    stage's 5 (decision 1's "no SQL" holds for the whole search, its checks included). A
    failed read is
    never a cancel; the thread tries again at its next poll. A cancelled search raises
    `SearchCancelledError`, the attempt ends `cancelled`, and nothing is stored: a cancel is
    never a truncated result. The worker loop also cancels the DBOS workflow and publishes the
    run `cancelled`, as for every run (DUR-05). This replaces the child process's cancellation
    in L0 (LIMITS-06 as deferred).
20. **What is stored, and served.** The ranked `SearchResult` is the run's sealed output; its
    facts go beside it once (`route_solve_results`), with CHECKs that repeat the search's rules:
    a stopped search names its limit and is never complete; only a complete one has exact
    layers, proves no route or is unresolved; a stopped one with nothing found found none
    before its limit; routes are found exactly when something was archived; the caps bound the
    counts. `GET .../planning/solves/{run_id}` serves the solve, its stage while it runs, and
    its result once complete. **Ruling (R11):** the result carries spec section 18's codes as
    facts the web words, never as an error: `code` is `SOLVE_LIMIT_REACHED` for a search a
    limit stopped (beside its stop reason, instance size and narrowings; truncation is the
    normal state) and `NO_ROUTE_IN_BOUNDED_MODEL` for a complete search that proves no route;
    otherwise null. "Best trade-offs found" is the web's words for `routes_found`. The Routes
    chapter (Task 14) words them; pagination of a large archive is Task 14's too. **No
    sentence Careerwright composed is sealed or served** (R11, fix round 1): a finding's
    `reason` (the gate, or why a value is unknown) is the checker's working note, read in
    memory by the search's prerequisite rule and never serialized. A finding goes out as its
    code, kind, month, variant, amount, limit and unit, and Task 14 words it from those.
21. **What could help a stopped search** (OPT1-15; fix round 1). The narrowings are named
    from the stop reason, among those the instance can still take (a dimension already at one
    is never named):
    - the state limit or the archive limit: fewer concepts, or one start. Both shrink the tree
      of selected sets, which those limits count;
    - the time limit: those two and a shorter horizon. A shorter horizon leaves the tree as it
      is and only makes each check quicker (Task 13a measured about 13 s at 12 months against
      26 s at 24), so it can help only a search the clock stopped.
    They are codes, beside the instance size, which the Routes chapter words as what could
    help, never as a promise that the narrowed search finishes.
22. **One solve at a time** (fix round 1). **Ruling: a process-wide lock in the activity, not
    a DBOS queue.** The search is CPU-bound pure Python on a wall clock, and DBOS runs each
    workflow in its own thread of one interpreter, so two solves at once would each get about
    half of it: a search that completes alone in 26 s (Task 13a's largest realistic one)
    would stop at 30 s, truncated, with narrowings it did not need. An execution takes the
    worker's one solve slot before it marks its run running or records an attempt, so its run
    stays `queued` while it waits and its clocks start only when it runs; it polls the cancel
    while it waits and leaves at once if the person cancels. Why a lock: it needs no DBOS
    queue registered in DBOS's system database, no change to the outbox's dispatch or to any
    workflow's step sequence (so the DBOS `application_version` stays `careerwright-l0-1`),
    and L0 runs one worker process. Known limits: a second worker process would need a DBOS
    queue with a concurrency of one; and at shutdown a solve still waiting its turn may start
    once the running one ends, until Compose's stop period (15 s) ends the worker, after
    which DBOS recovers both (decision 15).

### Consequences (Task 13b)

- **The benchmark** (`uv run --locked python -m tools.rank_benchmark`, 2026-10-31, arm64
  macOS, Python 3.12.12): at 50,000 points, each layering timed as the best of three runs,
  the efficient layering took 0.005 s to 0.039 s and peeling 0.005 s to 0.068 s over the five
  shapes, always equal; the whole rank stage on a 50,000-schedule archive (the synthetic
  `unbounded` instance, 20 concepts, one start, 24 months, its search's clock held still so
  the archive cap stopped it, which took 42 s), timed as one run, took 988 ms, inside its
  5-second limit (1,115 ms on a second, separate run).
- **For Task 14:** read a solve through `GET .../planning/solves/{run_id}`; word `code`,
  `outcome`, `coverage`, `stop_reason`, the instance size and the narrowings (as what could
  help, decision 21), and each finding from its code and facts (decision 20); show the stage
  while it runs; a solve waiting its turn is `queued` (decision 22); a failed or cancelled
  solve has no result. A result at the archive cap is
  large: on the benchmark's instance, 86 MB of JSON (50,000 schedules, 50,000 families, 320
  equal points), read back in 2.4 s, so the chapter should page it (realistic L0 results,
  P01's limits included, hold about a thousand schedules or fewer). A chosen route's full
  ledgers are
  `check_route` on the same snapshot, which only the worker can open today (the API seals it,
  never reads it).
- **Known limits:** a search stopped by the clock may stop at a different place on another
  machine; a crash loop ends after three attempts as `unknown_failure`, since what killed the
  worker is not known; the rank stage's limit is checked between its passes, so it can run
  over by at most one pass (under a second at the cap); solves run one at a time per worker
  process, and L0 runs one (decision 22). A finding's `reason` also carried a few
  identifiers (the gate a prerequisite needs, which limit is unknown, a scheme's ID); the
  served result no longer has them, so if the Routes chapter needs one it becomes a typed
  field of its own.
