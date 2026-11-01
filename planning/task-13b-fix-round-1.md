# Task 13b, fix round 1 of 5

You fix Task 13b (Careerwright L0, worktree `/Users/darianraad/Code/careerpathoptimizer-wt/13b`,
branch `wt-13b`, commits 41f67a3..070aa89 on 6c9e0a8). You are a fresh implementer: the
original's report (`task-13b-report.md`) tells you what was built and why. FIX_BASE 070aa89.

## Read first (all in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`, all of it, including the acceptance lock rule.
2. Both review halves, in full: `task-13b-review-search.md` and `task-13b-review-run.md`.
3. `task-13b-dispatch.md` (decisions that still bind, including the product owner's scope
   decision: no disk archive, no child process), `task-13b-brief.md` and `task-13b-report.md`.

## Fix now (each behaviour change with a test that fails before the fix)
1. **Search half, Important 1: the narrowing.** A stopped result lists every narrowing that
   applies, in practice all three.
   - **Ruling:** name the narrowings from the stop reason. A state cap or an archive cap:
     fewer concepts or one start. The time cap: those two and a shorter horizon (Task 13a
     measured about 13 s at 12 months against 26 s at 24).
   - They are codes, which Task 14 words as "could help", never a promise that the narrowed
     search finishes. Keep the instance size beside them.
   - Record the rule in ADR 0016. Test each stop reason.
2. **Run half, Important 1: two solves at once.** They share the worker's process in an
   unbounded pool, so a search that would finish alone can stop at 30 s and read as truncated.
   - **Ruling:** solves run one at a time: a DBOS queue with concurrency 1, or a lock taken
     before the search's clock starts. Your call; say which in ADR 0016.
   - Test that a second solve waits and its clock starts only when it runs.
   - If the queue changes an existing workflow's step sequence, change DBOS
     `application_version` as `CLAUDE.md` says and tell the controller.
3. **Run half, Minor 1:** a new request must not join a solve that has a recorded
   cancellation. Test: cancel with no worker running, ask again, expect a new run.
4. **Run half, Minor 2:** when the workflow publishes a terminal outcome, settle any open solve
   attempt (for example as `interrupted`). Cover the paths the review lists. Test it.
5. **Run half, Minor 4 (R11):** the served solve result carries no sentence Careerwright
   composed. Leave `Finding.reason` out of the API's solve result. Task 14 words each finding
   from its code, month and amount. Regenerate the client. Test that no `reason` is served.
6. **Run half, Minor 6:** tests for the stored-then-crashed reuse path, the three-attempt
   bound, and access revoked while a solve runs; and one end-to-end test that stores and serves
   a `routes_found` result with its schedules.
7. **Search half, Minor 1:** the cancel poll never charges the search's 30-second clock. Poll
   from a small background thread that sets a `threading.Event`, or time the poll outside the
   clock. A slow store must never turn into a time-limit stop. Test it.
8. **Search half, Minor 2:**
   - the replay test stops deep in a tree that has pairs (for example the `c0..c3` courses),
     after the singles;
   - a test pairs a stopped search that found routes with `SOLVE_LIMIT_REACHED`.
9. **Search half, Minor 3:** the benchmark says "one run" for the rank-stage row, not "best of
   three".

## Not now (the controller has carried them)
- Run half, Minors 3, 5 and 7 go to Task 14: the caps the snapshot read, paging the large
  result, and recomputing a chosen route's ledgers on the same snapshot.
- Run half, Minor 8 (the `CLAUDE.md` line) is the controller's.

## Rebase
`l0-local-release` has moved on since 6c9e0a8 (Task 6d slice A's fix round 2; Task 3b will
integrate soon). Rebase onto its head at the end. Follow R15: renumber your migration if
another took 0036, regenerate the client, merge `vocabulary.ts` by hand keeping both sides'
words, and edit the register only in your last commit.

## Then
- `make check`, then `make acceptance` once under the lock (one guarded command), after the
  rebase. If a test fails, re-run the whole `make acceptance` and report both runs.

## Hard rules
- Edit/Write for every source change: no heredocs or scripts that rewrite files. The project's
  own generators are fine.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `var`, `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser. Never start Docker or open
  an app or window.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`. No subagents. Never push. Never touch the main tree or
  `l0-local-release`.
- Migrations are forward-only. 0036 isn't integrated yet, so you may still change it on this
  branch; say so if you do.
- Disclose every changed test input or assertion.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append a "Fix round 1" section to `task-13b-report.md`: each finding with its test, the RED and
GREEN evidence, and the commands with their output. Reply with only the short contract and your
branch head SHA.
