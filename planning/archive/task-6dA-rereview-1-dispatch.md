# Scoped re-review: Task 6d slice A, fix round 1

You re-review one fix round of Careerwright L0, Task 6d slice A. The slice was reviewed in two
halves (facts and targets); both reviewers' sessions ended in a machine restart, so you take
both halves. Fix round 1 is commits 38f9998..6c9e0a8 on `l0-local-release` (main tree
`/Users/darianraad/Code/careerpathoptimizer`).

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `reviewer-contract.md`, including its calibration and the R11 carve-out.
2. The two reviews: `task-6dA-review-facts.md` and `task-6dA-review-targets.md`.
3. The fix list, `task-6dA-fix-round-1.md` (the controller's rulings bind: a new forward
   migration 0035, never an edit to 0034; the bracket rule restored inside the one
   `resolve_target`; unknown counts null). The resume note, `task-6dA-fix-round-1-resume.md`:
   a first implementer died mid-round; a second kept part of its draft.
4. The implementer's report, `task-6dA-report.md`, section "Fix round 1" (unverified claims).
   Judge its two rulings:
   - 0035 also re-decides stored records that the restored bracket rule now reaches;
   - a title with no record reads as naming nothing, so the slate lists it as "couldn't
     match".
5. The diff, `review-38f9998..6c9e0a8.diff` (1,282 lines; generated client excluded).

## What to check
- Each of the four fixes: is it addressed at its cause, with a test that would fail without
  it? Say "addressed", "partly" or "not addressed", citing `file:line`.
- Migration 0035: forward-only, idempotent, safe on a database that already applied 0034,
  row-level security and CHECKs intact. Does re-deciding stored records rewrite anything a
  person chose or a pinned discovery depends on? Could it change a past discovery's slate?
- No path left that turns a missing record into `INTERNAL_ERROR`, and "not resolved" never
  reads as "no match exists" where the search wasn't run.
- The sketch for each of the three pack roles: no sentence contradicts the coverage line.
- New breakage only inside the changed code. Don't re-review the slice.

## Rules
- Read-only. No edits, no commits. Another implementer works in a worktree.
- `make check` passed (the implementer's run). The controller is re-running `make
  acceptance` whole. Don't re-run suites; one focused fast test is fine for a specific doubt.
  Integration tests need the acceptance lock: don't run them.
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`.

## Output
Write `.superpowers/sdd/l0-sprint-tasks/task-6dA-rereview-1.md` in the contract's format, with
each finding's status. Then reply with at most 10 lines: each finding's status, any new
Critical or Important item, and the path.
