# Task 6f, the held-back part: Childline in the calm support panel (worktree)

Task 6f held Childline back until its details were checked on Childline's own website. The
product owner checked them by eye on 1 November 2026: `planning/childline-checked-2026-11-01.md`.
Use only what that file marks verified. Never add a detail from memory.

## Your tree
Worktree `/home/user/careerwright-wt/childline`, branch `wt-childline`, from 8c66b59 (`var`
linked). Work and commit only there. Beside you: the Linux-stack task in the main tree
(compose, Dockerfiles, tools/localenv, test infra) and the fetch-proxy task in another worktree
(evidence/fetcher, tools). Never touch their files. Rebase onto
`claude/confident-ramanujan-ux3saw` at the end (R15; regenerate the client if needed).

## Read first
`/home/user/careerwright/planning/env-cloud.md`, `implementer-contract.md`, `task-6f-brief.md`
(the Childline bullet and acceptance 5), `task-6f-dispatch.md` (scope change 1), ADR 0007 and
its support-policy amendments, `careerwright/profile/safety.py`, the web's support panel
(`SupportNote` and its vocabulary), and `docs/reviews/session-w2.md` (its Childline item).

## Build
1. Childline beside the panel's other UK services, for children and young people. Nothing asks
   for or infers age (the 6f card), so the line is shown with the others and says who it is
   for in Childline's own verified words ("children and young people"). Don't state an age
   limit: the age range is not verified (the file says so).
2. Its details: free, 24 hours a day, 7 days a week, 0800 1111, 1-2-1 chat online (its https
   link). Keep it as short as the panel's other lines; the calm tone of the existing lines.
3. The support policy's version goes up (ADR 0007 amendment line, with the source file named);
   its review status "not yet reviewed as built" (human gate H-12, session W2).
4. Session W2's package: its Childline item becomes one yes/no line showing the panel's new
   words, "not run — requires human".
5. Tests: the panel lists Childline wherever it shows (every place a person types), with its
   link https; the policy version pinned. Use the existing risk-word fixtures only.
6. Register: PROF-15 implemented, its review "not run — requires human". Last commit.

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH). Don't run
integration or acceptance. Edit/Write only, explicit pathspecs, no web requests, no live
calls, no subagents, never start Docker, never read `.env` or print an environment value, never
push, pnpm only. Never write distress or self-harm text. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append "Follow-up: Childline" to `/home/user/careerwright/planning/task-6f-report.md`; reply
with the short contract and your head SHA.
