# Task 6f, fix round 1 (the only one, R16)

You are a fresh implementer fixing Task 6f ("no job yet"). The original implementer's report,
`task-6f-report.md`, tells you what was built and why; its dispatch, `task-6f-dispatch.md`,
still binds (Childline held back). Main tree `/home/user/careerwright`, branch
`claude/confident-ramanujan-ux3saw` (head 9ef9e51; Task 12c landed after 6f with migration
0041, planning only). Nothing else runs beside you.

## Read first (all in `/home/user/careerwright/planning/`)
1. `env-cloud.md` (Node 24 on PATH, checks with the Adzuna variables unset, Docker down).
2. `implementer-contract.md`.
3. The review: `task-6f-review.md`, all of it.
4. `task-6f-dispatch.md` and `task-6f-report.md`.

## Fix now (each with a test that fails before the fix)
1. **I1 (truth):** a qualification's status and a work status are labelled "You said" when
   the person never said them (`profile/interview.py:344-348`, `:360`). "I am taking A-level
   biology" can show as achieved with "You said this". A status the person didn't state in
   their own words is shown as Careerwright's reading (the existing reading/inference label),
   never as "You said"; a qualification whose status isn't stated is never achieved. Correct
   ADR 0006:365 to say what is true.
2. **I2 (truth):** the demo interviewer reads "I have to retake my GCSE maths" and "I have
   failed my GCSE maths" as achieved (`profile/fixture_interviewer.py:115-119`). A retake, a
   fail, or anything not plainly achieved is never achieved: expected, or not proposed. Don't
   widen the patterns otherwise (R11: known limits are recorded, M7).
3. **M3 (truth, the brief's acceptance 3):** if "Closer to what I do" was chosen and then
   isn't offered (no work known), the emphasis resets to balanced, so no hidden view calls
   suggestions close to what the person does (`Directions.tsx:689-691`).
4. **M1 (a true record):** add one line to ADR 0006's amendment recording migration 0040's
   in-place addition of not-yet-asked answers as the one exception to the saved answers'
   append-only rule. No code change.

## List (not now)
M2 (note it in your report section), M4, M5, M6, M7: the final review and session W2's sheet.

## Then
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` after each change.
- Docker is down: integration, acceptance, browser tests, captures not run; say so.

## Hard rules
Edit/Write for every source change (no heredocs or scripts that write files; the generators
are fine). Explicit pathspecs. No web requests, no live calls, no subagents, never start
Docker, never read `.env` or print an environment value, never push, never write distress or
self-harm text, pnpm only. Disclose every changed test input or assertion. The register last.
Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append "Fix round 1" to `task-6f-report.md` (each item: test, RED, GREEN, commands); reply
with only the short contract.
