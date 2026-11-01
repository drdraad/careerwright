# Task 13a: the route search core (Sprint 6a), in a worktree

Careerwright L0. This task builds the route search that every computed route will come from:
the riskiest technical link in the chain from a person's options to a printable plan. It is
pure backend and waits for no session.

## Your tree
- Worktree: `/Users/darianraad/Code/careerpathoptimizer-wt/13a`, branch `wt-13a` (from fde8e7d).
  Work and commit **only there**. Never check out, commit to or reset `l0-local-release`; the
  controller integrates your branch.
- It is set up: `backend/.venv` (uv sync done), `apps/web/node_modules`, `docs/design`
  dependencies, and `var` (a link to the main tree's datasets, excluded from git). `make check`
  passes there at fde8e7d (backend 1,552, Vitest 319).
- While you work, another implementer edits documents in the main tree (`docs/plan`,
  `docs/adr`, `docs/requirements-register.md`, `CLAUDE.md`, the specification's section 22),
  and a reviewer reads it. Their work and yours must not touch the same files.

## Read first
1. `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`:
   all of it, especially "Parallel work" (worktree rules, rebase, the acceptance lock).
2. Your brief: `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-13a-brief.md`.
   It is your requirements, with the exact values to use verbatim (Global Constraints,
   standing rulings, the card).
3. The plan's Sprint 6a card in `docs/plan/development-plan.md`, and spec section 12 (OPT-1,
   including "Consequence of the M0 limits", ROU-1, FIN-1, RDY-1) and section 20 (TEST-1).
4. What you build on: `backend/src/careerwright/planning` (the monthly compiler, ledgers and
   route checker from Task 11; ADR 0013) and the reviewed option pack 0.2.0 (`load_pack`,
   ADR 0011). Readiness milestones come from `careerwright.capability.readiness.assess`,
   never from planning code (`CLAUDE.md`).

## Decisions that bind you
- **The independent oracle shares no code with the candidate search or with
  `careerwright.planning.checker`.** That includes no shared helpers and no shared
  constants beyond the input data types. This is `CLAUDE.md`'s rule, and the reviewer checks
  it.
- **The measurements are a deliverable.** The approved audit sizes Task 13b's durable add-ons
  (disk archive, child process) from them: L0 has four reviewed targets and ten learning
  options.
  - Report the measured sizes with expanded-state counts and times, exactly as the card asks.
  - Report whether every pack-scale instance completes in-process within the M0 limits
    (1,000,000 states, 30 s).
  - A run stopped early is "not complete at that size", never infeasible.
- **Scope is the card.** No persistence of solve runs, no API, no UI, no migration: those are
  Task 13b and Task 14. If you find you need one, stop and report NEEDS_CONTEXT.
- **The register:** update only the rows this work closes (OPT1, PARETO, TRACE01, DIRECTAI,
  FAMILY, the complete-coverage parts of LIMITS). Do it in your last commit, after rebasing
  onto the current `l0-local-release`. The register is being re-edited in the main tree:
  rebase first, then edit the rows on top.
- **Review rules from the approved audit:** small issues wait for the final review, and
  severity follows the effect on the person. Keep the code plain: pure functions,
  documented pruning proofs, property tests where they prove soundness.

## Hard rules
- Edit/Write for source changes. The project's own generators are fine; no scripts that
  rewrite files.
- Stage explicit paths. Never stage `var`, `answers-2.md` or `esco_research.txt`.
- No live model calls, no web requests, no Docker pull of an uncached image, no headed
  browser or window.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Leave every running stack alone, and never run `make stop`.
- No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion, with why.

## Checks
- `make check` in your worktree before your final commit, and again after the rebase.
- This task adds no stack behaviour. Run `make acceptance` only if you touch anything an
  integration or stack test covers. If you do, take the lock exactly as the contract says.

## Report
Write the full report to
`/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-13a-report.md`
(the contract's report shape, plus the measurements section the card asks for). Then reply
with only the short contract, and add your branch head SHA.
