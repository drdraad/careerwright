# Task 6f: no job yet (main tree)

Careerwright L0. The product owner (1 November 2026): "Many users will be final year school
students who have never had a job before." Their decisions 2, 3, 4 and 9 are yes. This task
makes the start of the app work for someone who has never had a job, with no separate student
mode: the same answers serve everyone, and nothing asks for or infers age.

## This machine first
Read `/home/user/careerwright/planning/env-cloud.md` first (paths, Node 24 on PATH, checks
with the Adzuna variables unset, Docker down: integration tests, `make acceptance` and review
screenshots can't run; report them as not run, never start Docker).

## Your tree
- Main tree `/home/user/careerwright`, branch `claude/confident-ramanujan-ux3saw`. Commit with
  explicit pathspecs only (`git commit -- <paths>`).
- Running beside you: Task 12c in worktree `/home/user/careerwright-wt/12c` (planning only;
  it may add migration 0040 and regenerate the client). Take migration 0040 yourself if you
  need one; the worktree renumbers at its rebase. Never touch the worktree.

## Read first (all in `/home/user/careerwright/planning/`)
1. `implementer-contract.md`, all of it.
2. Your brief, `task-6f-brief.md`: it is your requirements. Its walk path
   `.superpowers/sdd/l0-sprint-tasks/audit-no-job-yet.md` is now `planning/audit-no-job-yet.md`
   (findings 1, 3, 4 and 8; section 2, rows 1, 3, 4 and 8).
3. `task-6dC-review-design.md`, item I1 (ESCO unexplained at the first question): yours.
4. `task-6dC-report.md` (both sections) for what slice C and its fix round built on the same
   first question, What we know and support screen.

## Scope changes from the brief (binding)
1. **Childline is held back.** The controller couldn't reach Childline's website from this
   machine, and its details must come from that website, never from memory. Build everything
   else. Don't add Childline, a placeholder for it, or a support-policy line about it; don't
   raise the policy version for it. The controller sends the checked details later as a
   follow-up message, or as a separate small task. Leave PROF-15 open and say why in your
   report.
2. **Add design I1:** explain ESCO in a few plain words where a person first meets it, at
   the first question (and the What we know disclosure's summary), or name it plainly there.
   You're rewriting the first question's words anyway; keep the phone's first screen holding
   the first decision (slice C's fix kept it there).

## Decisions that bind you
1. "I haven't had a job yet" saves an answer about the current role, never a job title,
   Skipped or Unknown, lights the person's light, and is never asked again (demo and live).
2. The two new answers go through the one profile write path and the interview contract (the
   model proposes, the person confirms, ADR 0006): the saved answers' next schema version, a
   forward-only migration with both "not yet asked" on existing profiles, the demo
   interviewer, What we know and the generated client. An expected qualification is never
   shown as achieved.
3. R11: the API carries facts and codes; every new sentence is worded in the web.
4. Opening words are proposals; the product owner settles them at session W2 (at most one
   wording round). Keep the sentence rule from the start.
5. The live interview's prompt gains the brief's one line and its prompt version goes up. No
   live call: Task 6e runs the capped live check.
6. A risk word still shows the calm panel everywhere it did (tests use existing risk-word
   fixtures only).
7. Every consequential write takes an expected version and an `Idempotency-Key` through
   `run_idempotent`. DBOS `application_version` stays `careerwright-l0-1`.

## R16
One reviewer after you report, one fix round at most. RED before GREEN for each behaviour,
including the browser test for "the world answers within ten seconds" (write it; it runs only
when Docker is up, so report it as written, not run).

## Hard rules
- Edit/Write for source changes; the project's generators are fine (`pnpm run generate`).
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser. Never start Docker.
- Never read `.env`, `~/.careerwright` or `~/.nessa`. Never print an environment value.
- Never run `make stop`. No subagents. Never push. pnpm only.
- Never write distress or self-harm text.
- Disclose every changed test input or assertion, with why.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The register and `docs/plan/*` change only in your last commit.

## Report
Write `/home/user/careerwright/planning/task-6f-report.md`, then reply with only the short
contract (status, commit range, checks and results, not run and why, concerns, product owner
questions in plain words).
