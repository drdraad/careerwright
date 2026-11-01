# Task 13b review, half A: the search, the rank stage and the truth of the result

Reviewed `wt-13b` at `070aa89` against `6c9e0a8`. I read `planning/layers.py` and
`planning/search.py` in full at the branch head, with their diffs, and the tests and the tool
in my half: `test_route_layers.py`, `test_route_oracle.py`, `test_route_search.py`,
`test_rank_benchmark.py` and `tools/rank_benchmark.py`. I also read what the half A questions
reach into: `solve_runs.py` (the cancel poll and how each kind of stop ends),
`solves.py` and `routes_planning.py` (`result_code`), migration 0036's result CHECKs, the
integration tests' truncation, cancel and rank-limit cases, `worker_entry.py`'s solve faults,
ADR 0016's amendment and the register rows. I ran nothing: no question here needed a test run
to settle it. Line numbers are at `wt-13b`.

### Spec Compliance
- ❌ Issues found: a stopped result lists every narrowing that applies. It never picks the one
  Task 13a's measured sizes suggest, and never the one that would let the search finish
  (`planning/search.py:844-852`). Important 1.
- Everything else in half A is compliant:
  - The efficient layering equals Task 13a's peeling.
  - The caps and their exact stop reasons are unchanged and right.
  - The rank stage is separate and observable, with its own clock and limit.
  - A cancel stops the search at its next check and leaves no result.
  - A stopped search never reads as "no route". The search code, the API's `code` and the
    database CHECKs all hold this.
  - The 50,000-point benchmark exists and is recorded.
- ⚠️ Cannot verify from diff:
  - the benchmark's timings (0.99 s for the rank stage at the cap; under 0.07 s for both
    layerings): not re-run;
  - that the Hypothesis properties and `make check` / `make acceptance` pass: the
    implementer's runs, not repeated.

### Answers to half A's questions
1. **Does the efficient layering equal peeling, over the full archive, with equal points apart?**
   Yes, and the argument holds (`layers.py:43-60`):
   - Points are sorted by time, then cost. So anything that dominates a point comes earlier.
   - Within one layer, cost never rises as time rises. So the layer's last point (its tail) is
     its cheapest. A point is dominated by some member of that layer exactly when the tail
     dominates it.
   - If layer k dominates a point, so does layer k−1 (dominance is transitive). So the first
     layer whose tail does not dominate a point is one more than the deepest layer that
     dominates it. That is peeling's answer.
   - Equal points sit next to each other in the sort. A copy meets its twin as that layer's
     tail, and `dominates` is false for equal points, so copies share a layer.
   - Points beyond F3 are skipped. They can never dominate anything in F1 to F3.
   - The rank stage feeds it the whole archive, dominated schedules included
     (`search.py:355-357`).

   **Are the tests strong enough to catch a wrong layer?** Yes:
   - 400 Hypothesis cases of up to 60 points on a 7×11 grid, with many ties, compared with
     peeling (`test_route_layers.py:109`);
   - peeling itself is checked against the longest-chain definition;
   - the search's layers are still compared with the oracle's own layering on every
     generated instance, and now also with peeling over the whole archive
     (`test_route_oracle.py`);
   - the 50,000-point shapes (`test_route_layers.py:114`).
2. **Caps and stop reasons.**
   - Before each candidate, the search checks, in order: cancel, then the state cap, then
     the clock (`search.py:560-566`).
   - The archive cap is checked after a check finds a new schedule that reaches the
     milestone. It stops the run there, so nothing is dropped while the search carries on.
     A tree that runs out at exactly 50,000 stays complete.
   - Pending children are counted as unexplored.
   - A cancel never turns into a limit: it is its own error, never `_LimitError`.
3. **Truncation and "no route".**
   - `_outcome` gives `no_route_in_bounded_model` and `unresolved` only when the search is
     complete (`search.py:755-771`).
   - `result_code` gives `SOLVE_LIMIT_REACHED` for any stopped search
     (`routes_planning.py`, `result_code`).
   - Migration 0036 refuses "no route" or "unresolved" on a stopped search. It refuses
     "routes found" with nothing archived, and "none found before the limit" on a complete
     search.
   - Only feasible checks that reach the milestone are archived. Unknown inputs stay
     `unresolved`; nothing in this diff changes how they are read.
4. **The rank stage's time (13a's deferred M3).** Accounted honestly.
   - `elapsed_ms` is the search alone. `rank_ms` covers all four rank passes on the stage's
     own clock. Both are stored (`search_ms`, `rank_ms`).
   - The 30 seconds stay the search's, as Task 13a measured them. The rank stage gets its
     own 5 seconds.
   - The last pass has no check after it, so a stored result can run over by one pass. ADR
     0016 and the sprint review disclose this. The ranks are still complete when that
     happens.
5. **Does a cancel stop the search promptly, and never become a truncated success?** Yes.
   - The worker reads the request at most every 0.2 s, checked before each candidate and
     before each rank pass.
   - A cancel raises `SearchCancelledError`. The attempt ends `cancelled` and nothing is
     stored (`solve_runs.py:179-192`).
   - A cancel that lands after the last check: the worker loop still publishes the run
     `cancelled` within about 0.2 s. The GET shows a result only for a complete run. So a
     late cancel at worst loses the race to a genuine success, as for every other run kind.
     It is never a truncated result filed as complete.

**The implementer's rulings in my half:**
- The rank stage's own limit and the `rank_limit_reached` class: agreed.
- `SOLVE_LIMIT_REACHED` and `NO_ROUTE_IN_BOUNDED_MODEL` as facts on the result: agreed. A
  stopped result carries real counts and a stop reason, so it is not a fabricated empty
  success, and the spec says truncation is not infeasibility.
- The new words in `vocabulary.ts`: agreed. They say what Careerwright did ("couldn't finish
  putting the routes in order in time"; "Nothing was saved from this search").

The run-side rulings are half B's: the workflow and `application_version`, the 86 MB result,
and the snapshot only the worker can open.

### Strengths
- The new layering is short, proved in its docstring, and checked three ways. Peeling stays
  beside it as the reference.
- The two stages split cleanly: `search_archive`, then `rank_archive`, each on its own clock.
  `search_routes` keeps 13a's callers working. A rank stage that hits its limit raises
  instead of returning ranks it lacks.
- The cancel is a separate error from every limit, all the way down, so a cancelled search
  cannot become a stopped one.
- The database repeats the result's truth rules as CHECKs. The integration test tries to
  break each one.
- The benchmark covers the worst shapes for ranking: one front, one chain, all points equal,
  a grid of ties. It also times the whole rank stage on an archive really filled to its cap,
  and its own test checks that it reports agreement.

### Issues
#### Critical
None.

#### Important
1. **A stopped result names every narrowing, not the one that would let the search finish**
   (`planning/search.py:844-852`, used at `:749`).
   - **What:** `_narrowings` returns each dimension greater than 1: fewer concepts, one
     start, a shorter horizon. Any instance big enough to stop has several concepts, usually
     two starts, and always more than one month. So in practice every stopped result lists
     all three, whatever stopped it.
   - **Why it matters:** the brief and the controller's decision 5 ask for "the narrowing
     Task 13a's sizes suggest". The spec (section 12) asks which narrowing "would let the
     search complete".
     - A shorter horizon does not shrink the tree of option sets, so it cannot lift a state
       or archive stop. Task 13a measured that the horizon only changes the time each check
       takes.
     - So a person told "a shorter horizon would let this finish" after a state-limit or
       archive-limit stop would narrow, wait, and be stopped again.
     - The web may not compute this itself (the UI computes no rank or result), so the API
       has to carry the right narrowing.
     - Effect: medium (they would notice and lose a retry). It breaks the brief, hence
       Important.
   - **Fix:** choose the narrowing from the stop reason and the instance size.
     - State limit or archive limit: name "one start" or "fewer concepts" only where
       `_selection_space` of the narrowed instance falls to the cap or below. Each allowed
       set is visited at most once, so that is a proof the cap cannot bind.
     - Wall-time limit: name a shorter horizon (Task 13a measured the per-check cost growing
       with the months) and any narrowing whose selection space falls under the measured
       26,000 to 110,000 checks per 30 s. Mark that one as an estimate.
     - Or, if the controller rules the plain list enough: record that in ADR 0016 decision 8,
       and have Task 14 word it as "could help", never "would let the search finish".

#### Minor
1. **The cancel check opens a database transaction inside the search loop**
   (`planning/solve_runs.py:111-127`, called from `planning/search.py:561`).
   - Decision 2 says "no network, model or database access inside the search". The
     candidate check stays pure, so the decision is met only in that narrower sense.
   - Each read (pool checkout with a pre-ping, the role settings, a select) runs on the
     search's own 30-second clock, about every 0.2 s. That is roughly 1 to 2% today.
   - A store that is slow but not down would be charged to the search. The result would then
     read as stopped by its time limit, with narrowings that wouldn't help.
   - **Fix:** poll from a small background thread that sets a `threading.Event`, and let
     `cancelled` read the event. Or state the narrower reading in ADR 0016 decision 19.
2. **Two test gaps beside high-effect claims:**
   - The replay test (`test_route_search.py:866`) runs on the A–I fixture. Every A–I option
     is in one exclusive group, so the tree has only the root and nine single options. With
     `max_states=5` it stops after the root and four of them. The claim it backs ("the
     complete run's archive up to where it stopped", LIMITS-01, OPT1-10) is never tested on
     a stop deep in the tree, where the unexplored count is worked out. Use an instance with
     pairs, such as the `c0..c3` courses at `:813`, stopped after the singles.
   - `test_planning_contract.py:103` checks `SOLVE_LIMIT_REACHED` only on a stopped search
     that found nothing. The case Task 14 will lead with "Best trade-offs found" is a stopped
     search that found routes (`routes_found` with the code). No test pairs that outcome with
     the code.
3. **The benchmark's "best of three" covers less than it says** (`tools/rank_benchmark.py:17`,
   `:127`). It applies to the layering shapes. The rank stage at the cap
   (`stage_at_the_cap`, `:109`) runs once, and the printed table puts it under the same
   heading. ADR 0016 rightly reports two separate runs (988 ms and 1,115 ms). Say "one run"
   for the stage row.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** Half A is sound where it matters most. The layers are exact. Caps, cancels and
truncation are honest from the search through to the database, and a stopped search can't
read as "no route". The one fix is that a stopped result has to name the narrowing that
would actually let the search finish, as the brief and the spec ask. Today it lists all three
regardless.

Counts: Critical 0, Important 1, Minor 3.
