# Task 6d slice C, fix round 1 (the only one, R16)

You fix Task 6d slice C (Careerwright L0, branch `l0-local-release`, main tree
`/Users/darianraad/Code/careerwright` — the folder was renamed from `careerpathoptimizer` on
1 November 2026). Slice C's commits are 51ca593..8292c6a; the plan update 0fbb69f and the
rename commit came after. FIX_BASE: the head when you start. You are a fresh implementer: the
original's report (`task-6dC-report.md`) tells you what was built and why.

R16 applies (the product owner's speed rules): this is the only fix round. Only the items
below are fixed; the controller checks your diff and tests afterwards.

## Read first (all in `planning/`)
1. `implementer-contract.md`, all of it.
2. Both reviews: `task-6dC-review-design.md` and `task-6dC-review-app.md`.
3. `task-6dC-dispatch.md` (its decisions still bind) and `task-6dC-report.md`.

## Fix now (each with a test that fails before the fix)
1. **Lost input (design I2 = app I1):** marking a skill "not part of my job" saves a new version
   and resets the seniority and industry form, losing what the person typed but hasn't saved
   (`TitleDetails.tsx:236-243`). Reset the form only when the saved seniority or industry
   change. Test it.
2. **A failure shown as an empty success (design I3, with app M7):** if the role's ESCO list
   fails to load, it disappears silently and looks like a role with no list
   (`TitleDetails.tsx:252-257`). Show the failure, worded from its error code. Test it.
3. **Nothing typed is refused (app M1):** a role or target whose title is only punctuation or
   emoji can't take details: a 500. Handle it like any other title, or refuse it with a
   `CareerwrightError` code worded in the web. Test it.
4. **The support screen on every place a person types (design M9; the product owner's yes of
   31 October 2026):** the workspace name is typed but not screened. Screen it with the one
   support policy, as What we know's entries are (the entry still saved, the panel shown,
   nothing stored or used for suitability). Tests use the existing risk-word fixtures only.
5. **False records (app M3, design M2 and app M8):**
   - PROF-11 says "verified" though its "search keeps them" part waits for Task 8: say so in its
     status.
   - Every remaining place that still calls the shared-skills line a revelation, a moment or a
     Task M candidate: the plan's documents and any sound or world cue the app still plays for
     it. The product owner's answer is "always a plain line". (`CLAUDE.md` was changed by the
     controller.)

## Not now (lists)
- Design I1 (ESCO not explained at the first question): Task 6f, which rewrites the first
  question's words.
- Every other Minor in both reviews: the final review or session W2's sheet, as each review
  marks.

## Then
- `make check` after each change; `make acceptance` once at the end, under the lock, in one
  guarded command. A flaky failure is re-run once; report both runs.
- Review captures for the places you change: `cd apps/web && pnpm run review-screenshots`.

## Hard rules
- Edit/Write for every source change: no heredocs or scripts that rewrite files.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser. Never start Docker.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`. No subagents. Never push.
- Migrations are forward-only. DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion.
- Never write distress or self-harm text.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append a "Fix round 1" section to `task-6dC-report.md`: each item with its test, RED and GREEN
evidence, and the commands with their output. Reply with only the short contract.
