Continue orchestrating the Careerwright L0 build as the SDD controller. Use the
superpowers:subagent-driven-development skill. Implementers are Opus 5.5 subagents (the
user's mandate). Work autonomously; stop only for the four SDD stop conditions or for
decisions that belong to the user.

## Recover state first (in this order)
1. Read the ledger in full: /Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/progress.md
   Its first line names the plan file (docs/plan/l0-sprint-tasks.md). Every task with a
   "Task <id>: complete" line is done. Never re-dispatch a completed task.
2. `cd /Users/darianraad/Code/careerpathoptimizer && git log --oneline -30` on branch
   `l0-local-release`. Trust the ledger and git over memory.
3. Read `CLAUDE.md`, `docs/plan/l0-sprint-tasks.md` (Global Constraints, standing rulings
   R1–R10, dependency rules and suggested order), and `docs/adr/0008-option-pack-order-and-review-schedule.md`.
4. Memory files: ~/.claude/projects/-Users-darianraad-Code-careerpathoptimizer/memory/
   (meta-llm-cost-discipline.md, careerwright-l0-build.md).

## Where things stand
- Sprints 0–2 complete (Tasks 1–6). The PM assessment
  (docs/plan/l0-assessment-handover.md) is applied: spec v1.3, plan v1.1, task file with
  Tasks 6b, 6c, 7b, 7c, 13a, 13b, ADR 0008, register rows (commits 3d2f377..f360a86,
  reviewed, ledgered "Plan update: complete"). HEAD at handover: f360a86.
- Next task: the first in the suggested order without a "complete" line. Expected:
  **Task 6b** (span-cited "Why this could suit you", D3), then 6c (visual corrections),
  7, 7b, 9, 11, session 2, 7c, 10, 12, 8, 13a, 13b, 14 (closes after session 3), 15, 16.
  Run tasks one at a time, never two implementers at once (the plan's "∥" is sequential).
- Do not dispatch a task whose precondition session has not happened; ledger
  "Task <id>: blocked: awaiting session N" and tell the user.

## Workspace (gitignored): /Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/
- `make-brief.sh <id>` writes task-<id>-brief.md (preamble + the exact `## Task <id>:`
  section; letter ids like 6b/13a work). `review-pkg.sh BASE HEAD` writes the review diff
  (lockfiles, generated client, images excluded).
- `implementer-contract.md`, `reviewer-contract.md`: pass their paths in every dispatch.
- Carry-forward notes to include in the matching dispatch: carry-forward-task-7.md (DUR-05
  cancellation; salary-floor filter once pay data exists), carry-forward-task-8.md (S0-V07
  Roles, S0-V08), carry-forward-visual-batch.md (the Task 6c list).
- Past briefs, reports, reviews and fix lists are there for reference.

## The loop (what has worked)
1. BASE = `git rev-parse --short HEAD`; `make-brief.sh <id>`; dispatch one Opus implementer
   in the background with: one line of context, the brief path ("read first; your
   requirements"), the contract path, carry-forward paths, decisions the brief can't know,
   the report path task-<id>-report.md, and the short reply contract. Ledger the dispatch
   and the agent id.
2. On report: `review-pkg.sh BASE HEAD`. Diffs over ~8k lines: split into two packages by
   path and run two Opus reviewers in parallel (reviewers are read-only, so parallel is
   fine). Name the concrete risks for each half.
3. Rule on findings (upgrade Minors that touch invariants, security, money, cost or
   honesty), write task-<id>-fix-round-N.md, resume the implementer with SendMessage
   (rounds 1–3); rounds 4–5 use a fresh implementer. Scoped re-review: Sonnet for small
   diffs, Opus for security, safety or money. At round 5, adjudicate and rule; don't loop.
4. Two failed fixes in one direction = wrong hypothesis: change the design, don't patch
   again (the Task 6 support screen needed this).
5. Ledger every step and every ruling as "Ruling: what — why — cost if wrong".
6. While waiting, use ScheduleWakeup (25–50 min fallback); completion notifications are
   primary. Check progress with `git log`/`git status` and the last timestamp in the
   agent's output file (tail -c 3000 | grep timestamp); never read the transcript.

## Hard rules
- Never read, print or pass `.env` / META_API_KEY. Never push, merge or tag without the
  user. Never touch other Docker projects on this machine (agentsolve-*, eigenprompt-*).
- Cost (R5, the user's explicit instruction): live Meta calls only through explicit,
  budget-capped commands (`make live-smoke`, `make live-eval`), never in check/acceptance;
  test model `muse-spark-1.3-contributor` with synthetic data only; per-scope cap 9
  requests / 3 production / $0.30; every call ledgered in docs/evidence/live-usage.*.
  Production model `muse-spark-1.3` only for the minimal release qualification in Task 16.
  Ask the user before the powered REC1-09 counterfactual evaluation (≤ $0.07).
  Spend so far: 24 calls, $0.023098.
- `CLAUDE.md` changes only with the user's explicit approval (offer exact wording).
- Human gates are never self-certified (R2). A user-supplied agent critique is not an
  approval; record approval only when the user says so.
- Subagents must use Edit/Write for source changes (they have breached this with sed and
  heredocs; restate it in every dispatch).
- When the controller commits docs while an implementer is running, commit with a
  pathspec (`git commit -- <paths>`) so its staged work is never swept in.
- Never ask a subagent to compose self-harm or distress example text (an API content
  filter killed a reviewer); point it at the existing tests instead.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## The user
- ADHD mode is on (a session hook loads it): lead with the action or result, numbered
  steps, restate state every turn, concrete time estimates, ≤ 5 items per list, end with
  one concrete next action, no preamble or closers.
- Bring human gates as short yes/no lists in plain language (this worked for H-07).
- Decisions already given (recorded in the docs): H-01 Sprint 1, H-02, H-07 Sprint 0,
  H-09, H-11 (plus a salary floor), D1–D3, two CLAUDE.md edits.
- Open for the user: **Session 1** (H-06 rights policy for permitted source classes, and
  the H-12 checklist in ADR 0007: support policy, its known limits, slate weights, the
  relevance floor). Needed before Task 8 and before any page body is retained outside
  R3's private directory. Prepare its materials (yes/no lists) before Task 7b ends.
  Later: session 2 after Task 11, session 3 before Task 14 closes, H-01 Sprint 2, H-03,
  H-04, H-05, H-08, H-10, H-13. Optional: Adzuna developer credentials before Task 7.

## Finish
After Task 16: final whole-branch review on the most capable model, one fix dispatch, then
superpowers:finishing-a-development-branch. The release report must include a "Rulings I
made" list collected from the ledger, and the "minor (deferred → final review)" items
(grep the ledger) must each be resolved or explicitly carried.
