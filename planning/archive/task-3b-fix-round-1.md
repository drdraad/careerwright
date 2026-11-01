# Task 3b, fix round 1 of 5

You fix Task 3b (Careerwright L0, worktree `/Users/darianraad/Code/careerpathoptimizer-wt/3b`,
branch `wt-3b`, commits 4c9b72d..11e2914 on 8ad36a6). You are a fresh implementer: the original's
report (`task-3b-report.md`) tells you what was built and why. FIX_BASE 11e2914.

## Read first (all in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`, all of it, including the acceptance lock rule.
2. `task-3b-review.md`, in full.
3. `task-3b-dispatch.md` (decisions that still bind), `task-3b-brief.md` and `task-3b-report.md`.

## Fix now (each behaviour change with a test that fails before the fix)
1. **Important I1: the session cap is per workspace. The product owner's ruling (31 October
   2026): keep "$5 per workspace", and say so everywhere.**
   - Keep the code's behaviour: each live workspace gets $0.75 a run and $5 on top of what it
     has spent this month.
   - Make every place say "per workspace", never "a session": the Makefile help, the session
     command's help, docstring and start message, the runbook, ADR 0003's qualification
     result, and register rows MODEL-08 and MODEL-11.
   - At start, print the session's total ceiling: the number of live workspaces it capped
     times $5, and that each workspace keyed during the session adds $5. Test the printed
     summary.
2. **M1: the spending line counts in-flight calls as unreported.** Say what Careerwright does,
   never what Meta did. For example: "Careerwright counts 1 call at its most until its cost is
   known." Test it.
3. **M2: the words name a menu sighted people can't see.** Name what they see ("the menu at the
   top right"), or give the trigger a visible label or tooltip. Your call; test it.
4. **M3: the estimate's cost line is wrong when the run limit refuses the run.** When the run is
   refused, show the full worst case or drop the cost sentence. Never state the clipped limit
   as the cost. Test it.
5. **M4, the documentation only:** the session command recreates the API and worker
   containers when the model setting changes. Where the help, docstring or runbook say
   "nothing is stopped", say it restarts the API and worker, and that a run in flight restarts
   (counted at its full reservation). Letting in-flight calls settle before exit waits for the
   final review.
6. **M5: `make session-ledger`.** Say in the runbook and the start message that the stack must
   be up. Make its label say what it copies (every attempt in this database, by date), or copy
   only the session's attempts, your call.
7. **M6: ADR 0003 overstates the input-token bound.** It is checked after the call (the attempt
   fails `bound_exceeded`); it doesn't stop the spend. One wording change.
8. **M7: `CAREERWRIGHT_PROJECT`.** Read it in one place, so `make session` and `make stop` can't
   act on different stacks. Or limit it to `demo`. Your call; test it.
9. **M8: report gaps.** Add the missing "Acceptance" section to your report (the controller's
   run on 11e2914 is in the ledger; your own run is after these fixes). Disclose the
   `test_model_registry.py` assertion change (Wonder moved from "listed only" to qualified).

## Not now
- M4's code (settle in-flight calls before `os._exit`) waits for the final review.

## Rebase
`l0-local-release` has moved on since 8ad36a6 (at least 38f9998, documents only; possibly Task
6d slice A's fix round with migration 0035). Rebase onto its head at the end. Follow R15:
regenerate the client, merge `vocabulary.ts` by hand keeping both sides' words, edit the
register only in your last commit.

## Then
- `make check`, then `make acceptance` once under the lock (one guarded command), after the
  rebase.

## Hard rules
- Edit/Write for every source change: no heredocs or scripts that rewrite files. The project's
  own generators are fine.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `var`, `.env`, `answers-2.md` or `esco_research.txt`.
- No live calls, no `make session`, no web requests, no Docker pull, no headed browser. Never
  start Docker or open an app or window.
- Never read `.env`, `~/.careerwright` or `~/.nessa`. The `.env` in the worktree is the
  controller's symlink: never read, stage or remove it.
- Never run `make stop`. No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append a "Fix round 1" section to `task-3b-report.md`: each finding with its test, the RED and
GREEN evidence, and the commands with their output. Reply with only the short contract and your
branch head SHA.
