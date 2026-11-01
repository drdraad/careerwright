# Review: Task 3b, live sessions on Muse Wonder

You review one task of Careerwright L0. It was built in the worktree branch `wt-3b`, rebased onto
`l0-local-release` at 8ad36a6: commits 8ad36a6..11e2914. It lets the product owner run their own
live sessions on Muse Wonder (Meta's more capable, more expensive model) with spend caps, copies
each session's costs into the cost ledger, shows a spending line in the app, puts the product
owner's own commands into the acceptance run, and fixes a worker-shutdown hang.

Grade first what could spend money unbounded or unledgered, leak a key or a person's words, or
touch the product owner's real data. Then what tells the person something false.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration and the
   R11 carve-out for quotes, the person's words and model replies.
2. The brief, `.superpowers/sdd/l0-sprint-tasks/task-3b-brief.md`, and the dispatch,
   `task-3b-dispatch.md` ("Decisions that bind you" are the controller's rulings).
3. The implementer's report (unverified claims), `task-3b-report.md`. Judge its concerns:
   - "searches 3" printed against 1 billed search on ledger row 37, and the upper bound it
     states;
   - `make session` and `make session-ledger` never run against the real stack;
   - the INT-01 evaluation failure read as a model result;
   - the ledger header rewording (Nessa to Careerwright) from regeneration.
4. The diff, `.superpowers/sdd/l0-sprint-tasks/review-8ad36a6..11e2914.diff` (4,282 lines;
   generated client and lockfiles excluded). Read it in passes.
5. As needed: ADR 0003 (with its 2026-10-31 amendment and the new "Qualification result"),
   `docs/evidence/live-usage.md`, `CLAUDE.md`'s secrets, cost and loopback invariants.

## What matters most
- Every cap: checked in code before any call, unknown cost counting its full reservation,
  named constants matching the brief ($0.50 qualification scope; about $0.75 a run and $5 a
  session). Can any path reach Wonder without a cap, or with the Spark-sized cap bypassed?
- The test model still takes synthetic data only, in code and by the database CHECK; a
  synthetic workspace never runs Wonder; demo workspaces run only the fixture interviewer.
- The session command reuses the normal live stack and `CAREERWRIGHT_HOME` without stopping or
  resetting the product owner's data, and no test starts it.
- The ledger copy reads only model, run kind, token counts, cost, state and time, never any
  text; a test proves it.
- No key is printed, passed as an argument, logged or journalled.
- The shutdown fix: reproduced first, the cause fixed (not a skip or a looser timeout), and the
  durable-runs test not weakened. Does ending the process at once lose any durable state?
- The spending line: dollars from the spend endpoints, words from `vocabulary.ts`, error codes
  worded, never the API's message; new API responses carry codes and numbers (R11).

## Rules
- Read the branch with `git show wt-3b:<path>`. The worktree is at
  `/Users/darianraad/Code/careerpathoptimizer-wt/3b`; read only.
- Read-only everywhere. Another implementer works in the main tree.
- `make check` passed (the implementer's run). `make acceptance` has not been recorded yet: the
  controller runs it. Don't re-run suites. One focused fast test is fine for a specific doubt
  (`cd /Users/darianraad/Code/careerpathoptimizer-wt/3b/backend && uv run --locked pytest <path>`);
  Docker may be down, so no integration or stack tests.
- No web requests, no live calls, no `make session`, no Docker, no browser, no subagents. Never
  read `.env`, `~/.careerwright` or `~/.nessa`.

## Output
Write the review to `.superpowers/sdd/l0-sprint-tasks/task-3b-review.md`, in the contract's
format. Then reply with at most 10 lines: counts by severity, each Critical or Important item in
one line, and the path.
