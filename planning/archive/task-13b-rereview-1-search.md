# Task 13b fix round 1, half A re-review: the search

Scope: the fix round `6eb5fde..99a8992` on `wt-13b`, for my four findings (fix-list items 1, 7,
8 and 9) and the new cancel thread. I also looked for new breakage, in changed code only. I
read every changed source and test file in my half at `wt-13b`, plus `planning/store.py`'s
attempt updates (one check, on the cancel thread). I ran nothing: reading settled each
question, including a hand trace of the new replay test. Line numbers are at `wt-13b`.

### Spec Compliance
- ✅ My half's four findings are all addressed, Important 1 exactly as you ruled it.
- ⚠️ Not verified here: that the new tests pass (the implementer's runs).

### My findings, one by one
1. **Important 1, the narrowings: addressed.**
   - What changed:
     - `_NARROWINGS` (`planning/search.py:226-238`) names, from the stop reason:
       - the state or archive limit: fewer concepts, or one start;
       - the time limit: those two and a shorter horizon.
     - `_narrowings` (`:860-869`) drops any dimension already at one, and returns none for a
       complete search, as before.
     - `Narrowing`'s description calls the codes "what could help, never a promise". The
       instance size stays beside them.
     - ADR 0016 has a new decision 21, and decision 8 points to it.
   - Tests (`test_route_search.py`):
     - both caps (`:849`), each checking the instance size;
     - the time limit (`:862`);
     - a dimension already at one is never named (`:880`).
   - This is your ruling, word for word.
2. **Minor 1, the cancel read on the search's clock: addressed.**
   - What changed:
     - `cancel_watch` (`planning/solve_runs.py:132-164`) reads the request every 0.2 s on a
       daemon thread and sets an event. The search's check reads only the event.
     - `execute` (`:254-265`) holds one watch for the whole execution, the wait for a turn
       included.
     - ADR 0016 decision 19.
   - Tests (`tests/domain/test_route_solve_runs.py`):
     - a 1.5 s store read against a 1 s search limit: the search completes (`:42`);
     - a cancel the watch reads stops the search (`:63`);
     - a failed read is never a cancel, and the watch reads again (`:72`).
   - The slow-store test is the right one. It fails on the inline read, which charged the
     store's time to the search's clock and then to the rank stage's.
3. **Minor 2, the two test gaps: addressed.**
   - The replay test (`test_route_search.py:933`) now runs on four free courses with
     `max_states=9`. I traced it by hand, and its assertions match:
     - the checks: the root, then the four singles, then `c0 c1`, `c0 c1 c2`, `c0 c1 c2 c3`
       and `c0 c1 c3`;
     - it stops on `c0 c2`;
     - unexplored: c0's last two children, plus the other three singles, makes five;
     - its eight schedules are the first eight of the complete run's 15, in order.
   - `test_planning_contract.py:109`: a stopped search that found routes (the £5 course)
     carries `SOLVE_LIMIT_REACHED` with `routes_found`.
4. **Minor 3, the benchmark's "best of three": addressed.**
   - The docstring (`tools/rank_benchmark.py:17-20`) and the table heading (`:127-129`) say
     each layering is the best of three and the rank stage at the cap is one run. ADR 0016's
     consequences say the same.
   - The benchmark's test checks the heading.

### The new cancel thread
- **Can it leak or outlive the solve?** Not past one read.
  - `finally: ended.set()` runs however the execution ends.
  - `ended.wait(CANCEL_POLL_S)` returns at once after that, so the thread ends after at most
    the one read in flight.
  - That read is a plain, lock-free select with a 5 s connect timeout. It cannot wait on the
    run row that `_prepare` locks.
  - The thread is a daemon, so it never holds up the worker's exit. A SIGKILL takes it with
    the process.
  - Threads cannot pile up unless the store itself hangs, and then the solve's own
    transactions hang too.
- **Can it let a cancel go unseen?** No new way.
  - The first read is immediate. The wait for a turn checks the event every 0.2 s, and
    `_prepare` reads the cancel itself.
  - Once a read sees the cancel, the event stays set.
  - A failed read is logged and tried again, never taken as a cancel. That is safe: the worker
    loop still publishes the run `cancelled`, and publication settles the open attempt as
    `cancelled`.
  - A late `finish_solve_attempt(SUCCEEDED)` cannot overwrite that, because it updates only
    where `finished_at IS NULL` (`planning/store.py:260-267`).
  - A result stored after such a cancel is never served (the GET serves only complete runs).
    That matches the existing rule: "its result is kept but the run stays cancelled".
- **Cost:** each solve waiting its turn keeps a watch reading five times a second. That is
  negligible for L0's one person; no action needed.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. **New, in changed code, outside my half: the served result no longer says *which* input is
   unknown** (`planning/checker.py:165-173`, `Finding.reason` now `exclude=True`; the run
   half's Minor 4, fix-list item 5).
   - **What:** dropping `reason` removed sentences, as R11 asks, but it also removed the
     identifiers in the same field:
     - which limit is unknown (`limit_unknown` with `reserve`, `direct_spend_cap` or
       `monthly_payment_cap`);
     - the gate a prerequisite needs;
     - the scheme still to confirm (`scheme_shared_unconfirmed`), and the pair of exclusive
       schemes.
   - **Why it matters:** an unknown reserve or spending cap leaves every route unresolved,
     and still reaches a solve (`inputs.needs`, `LEAVES_EVERY_ROUTE_UNRESOLVED`).
     - The served `blocking_inputs` now lists only `limit_unknown`. With two limits unknown,
       their entries can't be told apart. The new test pins that shape
       (`test_planning_contract.py:132`).
     - Task 13a verified that "an unknown hard limit leaves every route unresolved and says
       which". That still holds in memory, but no longer in what the person's solve shows.
     - The inputs page still names each missing input, so the person has a way round it. That
       is why this is Minor.
     - ADR 0016's known limits record it as Task 14's.
   - **Fix:** identifiers are codes, not sentences. Before Task 14, carry them as typed fields
     (for example the limit's `NeededInput`, the gate ID, the instrument IDs), and keep only
     the composed sentences out.

### Assessment
**Task quality:** Approved (half A)

**Reasoning:** All four of my findings are fixed and tested, the narrowings exactly as ruled.
The cancel thread cannot outlive a solve by more than one read, and it opens no new way to
miss a cancel. One new Minor, outside my half: the served result no longer names which input
or scheme is unknown. It is recorded as Task 14's.

Counts: Critical 0, Important 0, Minor 1 (new).
