# Review: Task 12a, the person's planning inputs (backend)

You review one task of Careerwright L0. It was built in the worktree branch `wt-12a`,
rebased onto `l0-local-release` at 98fd0a9: commits 98fd0a9..edfebc7. Every computed route
for a real person will rest on these inputs and rules. So grade first what would tell a
person something false: feasible when it isn't, ineligible when it's only unknown, a known
figure where one is unknown.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration.
2. The brief, `.superpowers/sdd/l0-sprint-tasks/task-12a-brief.md`, and the dispatch,
   `task-12a-dispatch.md`. The dispatch carries the controller's binding rulings:
   - every new rule is also written fresh into the oracle, and classed for the search;
   - C07: unconfirmed eligibility conditions leave funding unresolved;
   - C09: a recorded admission is an input;
   - one conditional job transition per route;
   - where work rights live is the implementer's call;
   - option facts are 12b's;
   - R11: facts, not sentences.
3. The implementer's report (unverified claims), `task-12a-report.md`. Judge its concerns:
   - the right to work is stored in two places (the planning inputs and the capability
     model's row);
   - **exclusivity between two funded options in one route is not checked.** The card's item 4
     says "Exclusivity and eligible-cost caps follow the same rule", so check it against the
     card;
   - the planning inputs are not in the workspace export;
   - `CLAUDE.md` still calls `planning` pure;
   - one scripted edit, reverted and redone;
   - no failing-first run for the input-model and integration tests;
   - an unexplained Playwright console-error flake on a page that calls no planning endpoint.
4. The diff, `.superpowers/sdd/l0-sprint-tasks/review-98fd0a9..edfebc7.diff` (4,828 lines).
   Read it in passes.
5. As needed:
   - ADR 0013, 0016 and 0012 (amended in the diff);
   - Task 13a's search and oracle (`backend/src/careerwright/planning/search.py`,
     `backend/tests/support/route_oracle.py`, now on `l0-local-release`);
   - `CLAUDE.md`'s invariants: money in minor units and unknown money null; an unknown cap, date
     or limit leaves a route unresolved, never passed; a violation is "not feasible in this
     monthly model"; only an approved award counts unconditionally; a loan is never support;
     readiness milestones come only from `capability.readiness.assess`; the oracle shares no
     code with the checker; row-level security; expected version and `Idempotency-Key`
     through `run_idempotent`; migrations forward-only.

## What matters most
- Can any input, missing or unconfirmed, make a route pass when it should be unresolved? Can
  an unknown work right read as ineligible?
- Is each new rule the same in the checker, the oracle (written fresh, not copied) and the
  search's classing? Would the oracle catch a checker mistake in a new rule?
- Do the commands keep the expected-version, idempotency and ownership contracts, and does the
  migration's CHECK repeat the domain rules?
- Is null used for unknown money everywhere, with no partial month figure shown as known?
- Does the API return codes and numbers only (R11)?

## Rules
- Read the branch with `git show wt-12a:<path>`. The worktree is at
  `/Users/darianraad/Code/careerpathoptimizer-wt/12a`; read only.
- Read-only everywhere. Another implementer works in the main tree.
- `make check` and `make acceptance` passed (the implementer's runs); don't re-run suites.
  One focused test is fine for a specific doubt, run in the worktree's environment
  (`cd /Users/darianraad/Code/careerpathoptimizer-wt/12a/backend && uv run --locked pytest <path>`).
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`.

## Output
Write the review to `.superpowers/sdd/l0-sprint-tasks/task-12a-review.md`, in the contract's
format. Then reply with at most 10 lines: counts by severity, each Critical or Important item in
one line, and the path.
