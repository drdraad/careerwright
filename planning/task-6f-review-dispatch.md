# Review: Task 6f, no job yet

You are the one reviewer for this piece (R16: experience and code together).

## This machine
Read `/home/user/careerwright/planning/env-cloud.md` first. The code is in the main tree
`/home/user/careerwright`, range 7b3a41e..8f13dfd. Read only. The controller may fast-forward
the branch with Task 12c (planning only) while you work: for code outside the diff, read it
as of 8f13dfd (`git show 8f13dfd:<path>`).

## Inputs (all in `/home/user/careerwright/planning/`)
1. `reviewer-contract.md`: method and output (its Mac path means the path above).
2. `task-6f-brief.md` (requirements) and `task-6f-dispatch.md` (binding: Childline held back;
   design I1 added).
3. `task-6f-report.md` (the implementer's claims, unverified).
4. `audit-no-job-yet.md` (findings 1, 3, 4 and 8) and `task-6dC-review-design.md` I1.
5. The package: `review-7b3a41e..8f13dfd.diff` (6,425 lines; generated client excluded). Read
   in passes and say so.

## Risks to check by name
1. "I haven't had a job yet" saves an answer about the current role, never a job title,
   Skipped or Unknown; lights the light; never asked again (demo and live); changeable in
   What we know.
2. The two new answers go through the one write path and the interview contract (model
   proposes, person confirms); Skip, Unknown, Prefer not to say; never asked twice; an
   expected qualification never reads as achieved anywhere.
3. Migration 0040 rewrites stored saved answers in place (the implementer's concern): is the
   table append-only by contract or by convention, is the rewrite safe under row-level
   security, forward-only, and does it keep every earlier version's meaning? Also the
   idempotent replay of an old save returning a receipt without the new answers: harmless or
   a truth problem?
4. Nothing presumes a job: the opening, "your next step", the example reply, the demo's
   enjoy question, the live prompt line and its version bump, "Show me suggestions" with no
   role, "Closer to what I do" hidden with no work, the unknown-work note.
5. The support screen unchanged everywhere (no Childline, no placeholder for it).
6. The experience: a world, not a form (CLAUDE.md "The experience"); the first ten seconds; a
   phone's first screen still holding the first decision with ESCO now named (390x844; the
   phone checks couldn't run, so read the layout closely); plain words, R11 (no sentences
   from the API).
7. Expected version and `Idempotency-Key` on every write; no input echoed in errors.

## R16 rulings you inform
Mark each finding safety, truth (false statement, failure shown as empty success, false
evidence record) or lost input, or "list". Only the first three get fixed now.

## Rules
Read-only. No web requests, no live calls, no subagents, never start Docker, never read
`.env` or print an environment value. Never compose distress or self-harm text.

## Output
Write `/home/user/careerwright/planning/task-6f-review.md`; reply with only the verdict,
counts by severity, and one line per Critical or Important finding with file:line.
