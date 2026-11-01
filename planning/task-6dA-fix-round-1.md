# Task 6d slice A, fix round 1 of 5

You fix Task 6d slice A (Careerwright L0, branch `l0-local-release`, main tree
`/Users/darianraad/Code/careerpathoptimizer`, commits 1577db2 and 8ad36a6). You are a fresh
implementer: the original's report tells you what was built and why.

Another implementer (Task 3b) works in a worktree. It will integrate the live-session tooling,
a spending line in the account menu and possibly `vocabulary.ts` changes. Commit with explicit
pathspecs. Take the acceptance lock exactly as the contract says, in one guarded command.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`, all of it, including the tightened lock rule.
2. `task-6dA-review-facts.md` and `task-6dA-review-targets.md`, both in full.
3. `task-6dA-dispatch.md` (what slice A delivers; decisions that still bind),
   `task-6d-brief.md` (the card), and `task-6dA-report.md`.

## Fix now (each with a test that fails before the fix)
1. **Facts half, Important 1: the sketch contradicts itself for a pack role.**
   - For a typed pack role that isn't an ESCO label (Registered nurse, Data quality analyst,
     Bookkeeping assistant), the sketch says both "Careerwright can check skills, options and
     routes for this role" and "…there's no requirement list yet. Not researched."
   - Word the research status from both the match result and the coverage, so a pack role
     never reads "Not researched".
   - Test all three titles.
2. **Targets half, Important 1: the backfill.**
   - Migration 0034 gives a record only to the targets in each workspace's newest profile
     version. So a discovery made from an older version fails with `INTERNAL_ERROR` when one
     of its targets was later removed or replaced.
   - **Ruling:** add a new forward migration, `0035`, with `down_revision = "0034"`. Don't
     edit 0034: a lasting database may already have applied it. 0035 fills in a record for
     every target title in every profile version, idempotently.
   - Add a migration test that reproduces the reviewer's case: a discovery from an older
     version whose target was later removed opens its slate and its note.
   - Also check that no code path can raise `INTERNAL_ERROR` for a title with no record. A
     missing record must degrade to "not resolved", never to an error.
3. **Targets half, Minor fixed now: a pack role lost by title.**
   - "Registered nurse (adult)" no longer reaches the nursing pack target by title. That would
     tell the person Careerwright can't check routes for a role it covers.
   - Restore the earlier match behaviour for qualifiers in brackets, inside the one
     `resolve_target`. Test it.
   - If restoring it is wrong for a reason the original report gives, say why instead, and
     record the change in ADR 0012.
4. **Facts half, Minor fixed now: unknown is never zero (`CLAUDE.md`).** A title idea that
   wasn't searched reports its matching-occupation count as null, never 0. Test it.

## Not now (the controller has them)
- Title ideas' reason code and the three values worded by branching go to slice B's start.
- The source-citing rule's effect on slice B's migration also goes to slice B.
- `pack_version`, which is stored but never read, waits for the final review.
- The other Minors wait for the final review (R13).

## Then
- `make check`, then `make acceptance` once under the lock (guarded).
- Design references only if a place's words change.

## Hard rules
- Edit/Write for every source change: no heredocs or scripts that rewrite files.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`. No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion.
- Never write distress or self-harm text.

## Report
Append a "Fix round 1" section to `task-6dA-report.md`: each finding with its test, the RED and
GREEN evidence, and the commands with their output. Reply with only the short contract.
