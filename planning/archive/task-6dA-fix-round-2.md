# Task 6d slice A, fix round 2 of 5

You fix Task 6d slice A once more (Careerwright L0, branch `l0-local-release`, main tree
`/Users/darianraad/Code/careerpathoptimizer`). FIX_BASE 6c9e0a8. Fix round 1 was 1cd1905..6c9e0a8;
its re-review found one new Important and four Minors.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`, all of it, including the acceptance lock rule.
2. `task-6dA-rereview-1.md`, in full.
3. `task-6dA-fix-round-1.md` and your report's "Fix round 1" section in `task-6dA-report.md`.

## Fix now (each with a test that fails before the fix)
1. **Important 1: a target with no record reads "Careerwright couldn't match it" where no
   match was tried.**
   - **Ruling (the re-review's option A):** a profile target title with no stored record is
     decided on read by the one `resolve_target`, with the same rules, and is not stored on
     read. The answer is then true, and nothing errors.
   - Don't add a second matcher, and don't store from a read path.
   - Change the 0034 migration test's assertion (`test_migrations.py:494-497`) to the true
     reading: at 0034, "Saute cooks" is ESCO's "sauté cook". Disclose the change.
   - Keep a guard on "every saved target has a record": a test that each write path records
     its targets (`profile/commands.py`, `cli.py`), so a future path that skips it fails a
     test rather than silently relying on the read-time decision.
2. **Minor 1: the new sketch test hides the steps.** Render the three steps the real API sends
   for a target (`sketch.py:166`), and scope the "Not researched" check to each target's own
   block. Step 2's words ("Not researched yet: no providers, prices or dates") stay as they
   are: session W2 judges them.
3. **Minor 3: one record, two decisions.** Say in ADR 0015's line that "Registered nurse
   adult" and "Registered nurse (adult)" share one record key, and whichever is saved first
   stands. Words only.

## Not now (the controller has them)
- Minor 2 (a qualifier naming a different nursing field, such as "(mental health)", reaches
  the pack's adult "Registered nurse"): carried to slice B, which owns title matching and its
  migration.
- Minor 4 (no test of `QUALIFIED` keeping a choice or an exact-label link): the final review.

## Then
- `make check`, then `make acceptance` once, whole, under the lock (one guarded command). If a
  test fails, re-run the whole `make acceptance`, not only that test, and report both runs.

## Hard rules
- Edit/Write for every source change: no heredocs or scripts that rewrite files.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser. Never start Docker or open
  an app or window.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`. No subagents. Never push.
- Migrations are forward-only: never edit 0034 or 0035.
- DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append a "Fix round 2" section to `task-6dA-report.md`: each finding with its test, the RED and
GREEN evidence, and the commands with their output. Reply with only the short contract.
