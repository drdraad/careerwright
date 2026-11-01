# Task 12a: the person's planning inputs, stored and confirmed (backend), in a worktree

Careerwright L0. A computed route needs the person's own money and time. That means their
income, cash, living costs, reserve, limits, availability, commitments and debts, and their
work rights. Today none of these has a store, so no route can be checked for a real person.
This task stores them as validated commands, with the API and the generated client. It has
no interface: the Options chapter (Task 12b) collects them.

## Your tree
- Worktree: `/Users/darianraad/Code/careerpathoptimizer-wt/12a`, branch `wt-12a`. It
  branches from `wt-13a`'s approved head (8ff5100), so the route search core (Task 13a, ADR
  0016) is already in your tree. Task 13a is approved but not yet integrated into
  `l0-local-release`. When you rebase at the end, rebase onto `l0-local-release`:
  - if it already contains 13a, your branch simply replays on top;
  - if not, tell the controller in your report, and they sequence it.

  Work and commit only in your worktree. Never touch `l0-local-release` or the main tree.
- It is set up: `backend/.venv`, `apps/web/node_modules`, the `docs/design` dependencies,
  and `var` (a link to the main tree's datasets, excluded from git).
- In the main tree, Task W2E (the You chapter, web and the demo interviewer) is running now.
  After it come Task 6d (titles and the role record, in the profile and catalogue) and Task
  3b (live sessions). You may meet them at the rebase: migrations, the generated client and
  the register. Follow R15's rebase rules: renumber your migration if another landed with
  your number, regenerate the client, and edit the register only in your last commit.

## Read first
1. `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`,
   all of it, especially "Parallel work".
2. Your brief, `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-12a-brief.md`.
   It is your requirements, with the exact values to use verbatim.
3. The controller's carried notes from earlier tasks (read only):
   `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/carry-forward-task-12.md`,
   items 1–7.
4. What you build on:
   - ADR 0013 (as amended 2026-10-31), ADR 0016 (the route search) and ADR 0012 decision 11;
   - `backend/src/careerwright/planning` (the checker, the compiler and the new search);
   - `backend/tests/support/route_oracle.py` (the independent oracle);
   - `careerwright/profile/commands.py` (the expected-version command pattern);
   - `careerwright/identity/activity.py` (the representative pattern).

## Decisions that bind you (the controller's rulings, from Task 13a's review)
1. **Write every rule this task adds or changes into the oracle too.** That covers stacked
   support unresolved, the repayments finding, the entry-requirements finding, unknown work
   rights unresolved and the job-transition rule below. The oracle is
   `tests/support/route_oracle.py`, written fresh from the rule, never imported from the
   checker. Also class each new finding kind for the search's set-aside screen and pruning,
   per ADR 0016's rule 2: three of its pruning rules read the checker's finding kinds. The
   oracle's property tests must still pass, with your new rules in their generated cases.
2. **C07** (a £0 fee that rests on eligibility conditions nothing checks, including living
   outside the Bristol target's area). An eligibility condition the person hasn't confirmed
   leaves that funding's effect unresolved, never assumed. Make each such condition an
   input the person confirms, through the variant's funding statuses.
3. **C09** (it can never be feasible without an application or an admission). Store the
   person's recorded admission or offer as an input, so a route can depend on it. Without
   it, the route stays conditional on the application, never feasible as stated.
4. **One conditional job transition per route** (spec: one bridge-role transition). A route
   holding both an apprenticeship's offer gate and a bridge job is two transitions. It is not
   feasible in this monthly model, with its own named finding and a test, in the checker and
   in the oracle. (Today the bridge-role rule counts only `work` actions.)
5. **Where work rights and remote working live** is yours to settle (the card says so).
   Record it in ADR 0013's amendment section, with why.
6. **Storage of the facts the person supplies for an option** (a start date, a cost, weekly
   hours) is Task 12b's, with "add an option yourself". Don't build it here.
7. **R11, facts not sentences:** the API returns codes and numbers, never sentences the
   person reads. The web words them later.

## Hard rules
- Edit/Write for source changes. The project's own generators are fine (`pnpm run
  generate`); no scripts that rewrite files.
- Stage explicit paths. Never stage `var`, `answers-2.md` or `esco_research.txt`.
- No live model calls, no web requests, no Docker pull of an uncached image, no headed
  browser.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`, and leave every running stack alone.
- No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`.
- Migrations are forward-only, with row-level security and CHECKs that repeat the domain
  rules. Use the next free revision number at your rebase.
- Disclose every changed test input or assertion, with why.

## Checks
- `make check` before your final commit, and again after the rebase.
- `make acceptance` once at the end, **under the lock** (contract, "Parallel work"): this
  task adds a migration and API routes that integration tests cover.

## Report
Write the full report to
`/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-12a-report.md`.
Then reply with only the short contract and your branch head SHA.
