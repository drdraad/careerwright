# Task 10A follow-up: readiness on a draft checklist, labelled (worktree)

The product owner's answer (1 November 2026), choosing option A of: "show the judgement anyway,
with a note saying it's based on a draft checklist" vs "not assessed yet on every job until a
checklist is signed off". Their reply: "A".

## Your tree
Worktree `/home/user/careerwright-wt/10a`, branch `wt-10a`, reset to the branch head fe17467
(Task 10A and its fixes are integrated). Work and commit only there. The controller may be
running `make acceptance` in the main tree: never touch it. Rebase at the end (R15).

## Read first
`/home/user/careerwright/planning/env-cloud.md`, `implementer-contract.md`,
`task-10A-report.md` (all sections) and `task-10A-review.md` (its point 7 and Q1), ADR 0012.

## Build (backend and API; facts and codes, never sentences, R11)
1. Where a target's rubric exists but isn't reviewed (`proposed`), the Skills facts carry the
   readiness result computed exactly as for a reviewed rubric, plus the rubric's review state
   as a fact (e.g. `rubric_review: proposed`), so the screens half words it "based on a draft
   checklist". A target with nothing modelled or eligibility alone stays
   `insufficient_coverage` / `not_assessed` as today: never ready. Protected gates, unknown
   never level 0, nothing finds a person ineligible, every L0 readiness qualified: all
   unchanged. Readiness and Skills agree for the same target (the review's P05 "apply now"
   case: Skills now shows it, labelled draft).
2. ADR 0012 amendment line with the product owner's answer; register row note.
3. Tests first (RED): a proposed rubric gives a readiness result with its review state; a
   reviewed one gives it with `reviewed`; nothing modelled stays not assessed; P05's case.

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH); a focused
integration run of the Skills tests only under the lock with the build shim if you change SQL:
`export PATH=/tmp/ccr-shim:/opt/node24/bin:$PATH; L=/home/user/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /home/user/careerwright-wt/10a/backend && env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY uv run --locked pytest -m integration tests/integration/test_skills.py > /tmp/skills-draft.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
(if the lock is held, wait and retry later; never remove a lock you didn't take). Edit/Write
only, explicit pathspecs, no web requests, no live calls, no subagents, never start Docker,
never read `.env` or print an environment value, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append "Follow-up: readiness on a draft checklist" to
`/home/user/careerwright/planning/task-10A-report.md`; reply with the short contract and head SHA.
