# Implementer contract (applies to every Careerwright L0 task)

## Before you begin
Read your task brief in full (it holds the Global Constraints, Environment facts and
Standing rulings), then the plan/spec sections it names. Inspect the existing repository
(`git log --oneline`, `CLAUDE.md`, `docs/adr/`, latest `docs/reviews/`) before editing.
If something in the brief is ambiguous in a way that changes behaviour, scope or
acceptance, and the spec/plan do not settle it, decide the simplest reading that keeps
every Global Constraint, record it as a ruling in your report (and an ADR if it is
architectural), and continue. Stop and report BLOCKED only for a genuine blocker
(missing access, a contradiction every path through which is a guess).

## Your job
1. Implement the slice the brief names, completely, to a production standard. Use TDD
   for domain logic (failing test first). Keep files focused; one responsibility each.
2. Verify by execution. Run the focused tests while iterating, and `make check` after each
   change and once before your final commit. The controller runs `make acceptance` once per batch; report it as "not run: the
   controller runs acceptance". Test output should be clean (no stray warnings).
3. Commit coherent increments on the branch your dispatch names (messages end with
   `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`). Never push.
4. Update `docs/requirements-register.md` rows your work closes (once it exists).
5. Self-review your own diff (completeness, names, YAGNI, tests that assert real
   behaviour, no secrets, no masked failures) and fix what you find.
6. For anything a person sees, walk the journey step by step before you report: one place to
   type and one clear next action per step, nothing shown before it is needed, no line that
   doesn't change the person's next action, actions teal, no em dash (the product owner, 3
   November 2026). The reviewer checks this as its Part 3.

## This machine and parallel work (from 2026-10-31, the product owner: "Where subagent work can be done
## cleanly in parallel, do so but coordinate well to avoid them causing conflicts")
Up to four implementers may run at once (R12–R17 in the sprint tasks file, today's rules):
one in the main tree, up to three in worktrees, on disjoint files. This machine is the
product owner's Mac (Environment facts in the sprint tasks file). Your dispatch says which
tree is yours:
- **The main tree** (`/Users/darianraad/Code/careerwright`, integration branch
  `claude/confident-ramanujan-ux3saw`): commit with a pathspec (`git commit -- <paths>`),
  never `git add -A` or `git commit -a`; another agent's files may be changing beside yours.
- **A worktree** (`/Users/darianraad/Code/careerwright-wt/<id>`, branch `wt-<id>`; both are in your
  dispatch): work and commit only there. Before your final report, rebase your branch onto
  the current `claude/confident-ramanujan-ux3saw`
  (`git rebase claude/confident-ramanujan-ux3saw`; the worktree shares the repository). On a
  conflict in `apps/web/src/generated`, regenerate (`pnpm run generate`) instead of
  hand-merging. If you added a migration and another landed with the same revision number,
  renumber yours to the next free one. Re-run `make check` after the rebase. The controller
  fast-forwards `claude/confident-ramanujan-ux3saw` to your branch; you never touch it
  yourself.
- **Shared files:** `docs/requirements-register.md` and `docs/plan/*` change only in your
  last commit, after the rebase, and only the rows or lines your work closes.
- **Checks (R16 and R17, the product owner's speed rules):** run `make check` after each
  change. The controller runs `make acceptance` once per batch of integrated
  pieces or halves. A flaky failure is re-run once; a second failure is reported as a
  finding.
- **Docker and the network:** never start Docker, pull or build images; the controller does.
  Make no web requests and no live calls: the controller
  makes every one.
- **One full acceptance run at a time** (its Compose projects and ports are fixed). If your
  dispatch asks you for a focused stack or integration test run, or for `make acceptance`,
  take the lock first: `mkdir /Users/darianraad/Code/careerwright/.superpowers/acceptance.lock`
  (it fails if another agent holds it). Remove it with `rmdir` the moment your run ends,
  pass or fail. Take and release it in one guarded command, so you can only ever remove a
  lock you took: `mkdir <lock> && { make acceptance; rc=$?; rmdir <lock>; exit $rc; }`.
  Never chain a run after a failed `mkdir` with `;`. Never remove a lock you didn't take,
  and never recreate one. The same applies to any focused stack or integration test run. If the lock is held, do other work and try again later; if it is still
  held at the end, report "make acceptance not run: lock held" and the controller runs it.
- Never stop, reset or remove another project's containers or volumes, and never run
  `make stop` (it stops the product owner's stack).

## You do not dispatch subagents
Do all of this task's work yourself. Never spawn a subagent to implement part of the
task, and never spawn a reviewer: the controller dispatches an independent reviewer after
you report.

## Honesty rules
- Evidence before assertion. Distinguish implemented / verified / blocked / not run.
- Never fake a live result with a fixture, never soften an assertion to get green, never
  claim a human-only gate (R2).
- Never print or commit the Meta key or any key material. Track every live call's cost
  (R5).

## Report
Write your full report to the report file named in your dispatch:
- what you implemented (or attempted), files changed
- rulings you made and why
- tests/checks run: exact commands and summarised output; TDD evidence (RED then GREEN)
  for domain logic
- live calls made with cost (R5)
- what is blocked / not run and why; concerns
- generated or vendored paths a reviewer should skip (lockfiles, generated clients, data)

Then reply with ONLY (under 15 lines):
- Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- Commits (short SHA + subject; first..last if many)
- One-line test summary
- Concerns, if any
- Report file path

## After review findings
If resumed with findings: fix them, re-run the covering tests, append a fix report
(changes, covering tests, command, output) to the same report file, and reply with the
same short contract.
