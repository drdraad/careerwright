# Task 12c: a tuition fee loan is a loan to repay (backend), in a worktree

Careerwright L0. The product owner's school-leaver decision 6 (yes, 1 November 2026): a tuition
fee loan paid straight to the university is not cash out of the student's pocket; it is shown
as a loan to repay later. Today a loan is never support, so a degree's fee counts as the
student's own spending and cash, and a degree reads "not feasible in this monthly model" against
a student's limits. This task changes the checker, its independent oracle and the search. It
has no interface: Tasks 12b and 14 word it.

## This machine first
Read `/home/user/careerwright/planning/env-cloud.md` before anything else. It maps every Mac
path and branch name in the planning files to this cloud machine, and covers Node 24, the
Adzuna variables and Docker (down: integration and acceptance can't run; report them as not
run).

## Your tree
- Worktree: `/home/user/careerwright-wt/12c`, branch `wt-12c`, from
  `claude/confident-ramanujan-ux3saw` at b47cac2. Work and commit only there. Never touch the
  main tree or its branch.
- It is set up: `backend/.venv`, `apps/web/node_modules`, the `docs/design` dependencies. No
  `var/` (no datasets on this machine).
- Running beside you: in the main tree, Task 6d slice C's fix round (profile, catalogue, the
  web's title details, the workspace name's support screen; it may add migration 0040 and
  regenerate the client). At your rebase follow R15: rebase onto
  `claude/confident-ramanujan-ux3saw`, renumber your migration if another took the number,
  regenerate the client, and edit the register and `docs/plan/*` only in your last commit.

## Read first
1. `/home/user/careerwright/planning/implementer-contract.md`, all of it ("Parallel work" and
   R16's checks especially).
2. Your brief, `/home/user/careerwright/planning/task-12c-brief.md`: it is your requirements.
   Its walk path `.superpowers/sdd/l0-sprint-tasks/audit-no-job-yet.md` is now
   `/home/user/careerwright/planning/audit-no-job-yet.md` (finding 2).
3. Specification sections 10, 12 (FIN-1) and 22 (the tuition fee loan row); ADR 0013
   (decisions 5 and 11, as amended) and ADR 0016 (pruning rules, the oracle).
4. What you build on: `backend/src/careerwright/planning/` (`inputs.py`, `compiler.py`, the
   ledgers, `checker.py`, `search.py`, `commands.py`, `store.py`, `solves.py`),
   `backend/tests/support/route_oracle.py`, and Task 12a's and 13b's reports in `planning/`.

## Decisions that bind you
1. **Only the tuition fee loan paid straight to the provider changes.** A maintenance loan,
   the Advanced Learner Loan and every other loan stay refused as support (the card: "every
   other loan ... is still refused"). If you find a reason the Advanced Learner Loan should
   follow the same rule, write it as one plain yes/no question for the product owner in your
   report, and don't build it.
2. **The fee it pays is not the person's money:** in neither the cash ledger, the direct
   spending the direct-spend cap reads, nor the monthly payment cap's payments. Never
   support, a grant, income or a receipt. FIN-1: represented consistently or excluded from
   both sides, never counted twice.
3. **Status:** only a loan the person confirms approved counts unconditionally; otherwise the
   route is conditional on it, beside the self-paid route, with a blocking verification
   (FUNDING-05). An unknown amount leaves the route unresolved, never £0.
4. **Facts and codes, never sentences (R11).** The route result carries the amount borrowed
   and when, as a loan to repay; unknown repayment stays unknown (`null`), never 0.
5. **Economic cost:** settle how the loan enters it and state it in plain words in ADR 0013's
   amendment. If your choice changes which routes are best trade-offs on any existing
   fixture or regression family, don't ship that choice: keep the reading that changes
   nothing, and put the alternative to the product owner as one yes/no question (R14).
6. **The oracle is written again** from the spec's section 22 row and ADR 0013, sharing no
   code with the checker; generated instances include the loan in every status; the search
   gives exactly the oracle's archive, objectives, layers and outcome. Raise the pruning
   version if a rule changes.
7. TRACE-01, the A–I fixture and every regression family keep their expected values.
8. Every consequential write takes an expected version and an `Idempotency-Key` through
   `run_idempotent`; row-level security via `actor_transaction`/`run_transaction`. A
   migration, if needed, is forward-only with CHECKs that repeat the domain rules. DBOS
   `application_version` stays `careerwright-l0-1` unless the solve workflow's step sequence
   changes (say so if it does).
9. **CLAUDE.md:** don't edit it. Propose the exact new words for its planning line ("a loan
   is never support") in `planning/task-12c-claude-md-proposal.md`.

## R16 (the product owner's speed rules)
One reviewer after you report, one fix round at most. Get it right the first time: RED before
GREEN for each behaviour, tests that assert real behaviour.

## Hard rules
- Edit/Write for source changes. The project's own generators are fine (`pnpm run
  generate`); no scripts that rewrite files.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live model calls, no web requests, no Docker pull, no headed browser. Never start Docker.
- Never read `.env`, `~/.careerwright` or `~/.nessa`. Never print an environment value.
- Never run `make stop`. No subagents. Never push. pnpm only, never npm or npx.
- Disclose every changed test input or assertion, with why.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Checks
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (with Node 24 on PATH) after
  each change, before your final commit, and again after the rebase.
- Integration tests and `make acceptance`: only if Docker is up, once at the end, under the
  lock in one guarded command. Otherwise report "integration and acceptance not run: Docker
  down", and list the integration tests you wrote or changed that didn't run.

## Report
Write the full report to `/home/user/careerwright/planning/task-12c-report.md` (the contract's
sections, the product owner's questions in plain words, the economic-cost reading). Then reply
with only the short contract and your branch head SHA.
