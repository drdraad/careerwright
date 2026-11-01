# Task 3b: live sessions ready on Muse Wonder, in a worktree

Careerwright L0. The product owner approved using Muse Wonder (Meta's more capable model) in
their own live sessions. Their first session is about 30 minutes in the real app, soon. This
task makes that safe, capped and fully costed:
- Wonder ready to qualify;
- a session command with spend caps;
- every session call copied into the cost ledger;
- a spending line in the app;
- the product owner's own commands in the acceptance run;
- the recurring worker-shutdown hang fixed.

**You make no live call.** The controller runs every live call itself.

## Your tree
- Worktree: `/Users/darianraad/Code/careerpathoptimizer-wt/3b`, branch `wt-3b` (from 60c8516).
  Work and commit only there. Never touch `l0-local-release` or the main tree.
- It is set up: `backend/.venv`, `apps/web/node_modules`, the `docs/design` dependencies, and
  `var` (a link to the main tree's datasets, excluded from git).
- In the main tree, Task 6d slice A is running. It changes discovery's notes into facts (the
  API, `vocabulary.ts`) and stores each target once (a migration, the generated client). Task
  12a's planning inputs (migration 0033, the client, the register) will be integrated too. At
  your rebase:
  - renumber a migration whose number another task took;
  - regenerate the client;
  - merge `vocabulary.ts` by hand where needed, keeping both sides' words;
  - edit the register only in your last commit.

## Read first
1. `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`,
   all of it, especially "Parallel work".
2. Your brief, `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-3b-brief.md`.
   It is your requirements, with the exact values to use verbatim.
3. ADR 0003, with its 2026-10-31 amendment; the audit's Muse Wonder notes
   (`docs/reviews/l0-audit-2026-10-31/G-muse-wonder.md`); `docs/evidence/live-usage.md` (the
   ledger's format and budgets).
4. What you build on:
   - `backend/tools/live_smoke.py`, `live_eval.py` and `usage_ledger.py`;
   - `backend/tools/stack.py` and the `Makefile`;
   - `careerwright/config.py` (the model and spend-cap settings);
   - `identity/model_registry.py`, `model_choice.py`, `spend.py` and `spend_limits.py`;
   - `api/routes_credentials.py` (the spend endpoints);
   - the web's account menu and workspace preferences.

## Decisions that bind you
- **The order of work.**
  1. Build the qualification path first: Wonder accepted behind an explicit flag, with a
     Wonder-sized cap.
  2. Commit it, then report to the controller with status NEEDS_CONTEXT, giving:
     - the exact commands the controller should run (two calls; then at most six evaluation
       cases);
     - the worst-case cost of each command, from your caps.
  3. The controller runs them and resumes you with the ledger rows.
  4. You record the capabilities in the registry and finish the rest.

  You may build the remaining items while you wait, if you report first.
- **The caps** come from the card: Wonder qualification under $0.50 in all; session caps of
  about $0.75 a run and $5 a session. Name them as constants. A cap is checked in code before
  any call, as today's live commands do. Unknown cost counts its full reservation.
- **The session command** starts the stack in live mode with
  `CAREERWRIGHT_META_PRODUCTION_MODEL=muse-wonder-1.0` and sets the session's caps on the
  workspace the product owner uses. Choose its name, and document it in the runbook.
  - It never changes the test model. A synthetic workspace still runs
    `muse-spark-1.3-contributor`.
  - The Contributor-model safeguards (in code and the database CHECK) don't change.
  - It must not stop or reset the product owner's existing data. It reuses the normal live
    stack's project and `CAREERWRIGHT_HOME`. Starting it is the controller's or the product
    owner's act, never a test's.
- **The ledger copy** reads only model, run kind, token counts, cost, state and time from
  the product's run records. It reads no message, answer, prompt or output text. A test
  proves no text field is read or written. It appends to `docs/evidence/live-usage.jsonl`
  under a session scope and regenerates the `.md` through `usage_ledger.py`.
- **The spending line** comes from the existing spend endpoints, with words from
  `vocabulary.ts`. Money is shown in dollars, because that's what Meta bills. Add an
  approximate pounds figure only if a pinned rate already exists; otherwise dollars only.
  Also add one estimate-before-start helper for Tasks 6e, 7e and 8 to use.
- **The shutdown hang:** reproduce it first, with a test that hangs or fails today (with a
  timeout), then fix the cause. Never skip or loosen the durable-runs test.
- **R11:** new API responses carry codes and numbers, never sentences.

## Hard rules
- No live model calls, no web requests, no Docker pull of an uncached image, no headed
  browser.
- Never read, print or pass `.env` or `META_API_KEY`. Never read `~/.careerwright` or
  `~/.nessa`.
- Edit/Write for every source change: no scripts that rewrite files, not even one-token
  replacements. Formatters on your own files and the project's generators are fine.
- Stage explicit paths. Never stage `var`, `answers-2.md` or `esco_research.txt`.
- Never run `make stop`, `make dev`, `make demo` or the session command yourself. The
  acceptance run's own test stack is fine, under the lock.
- No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`, unless the shutdown fix changes the
  workflow's step sequence. If it does, stop and report NEEDS_CONTEXT.
- Disclose every changed test input or assertion.

## Checks
`make check`; `make acceptance` once at the end, under the lock; and again after your rebase
if the rebase changed anything the acceptance run covers.

## Report
Write to `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-3b-report.md`.
Reply with the short contract (NEEDS_CONTEXT at the qualification step, as above), with your
branch head SHA.
