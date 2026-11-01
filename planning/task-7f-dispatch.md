# Task 7f: the school-leaver option pack, first half (worktree)

Careerwright L0. Plan v1.6, the product owner's school-leaver decision 8 (yes). Tasks 12c (and
its Advanced Learner Loan follow-up), 7b and 7c are complete.

## This machine
Read `/home/user/careerwright/planning/env-cloud.md`. The dataset hosts, `www.gov.uk` and
`www.ucas.com` are now reachable from this machine, but **you make no web request**: the
controller makes every fetch (the card). `var` in your tree is a link to the main tree's
`var` (the pinned datasets, verified).

## Your tree
Worktree `/home/user/careerwright-wt/7f`, branch `wt-7f`, from 4dd88f8. Work and commit only
there. The main tree is running `make acceptance`: never touch it, except writing your
planning files in `/home/user/careerwright/planning/`.

## Read first
1. `/home/user/careerwright/planning/implementer-contract.md`.
2. Your brief, `/home/user/careerwright/planning/task-7f-brief.md` (its walk path is now
   `planning/audit-no-job-yet.md`, findings 2 and 6).
3. How Tasks 7b and 7c curated and published: `planning/task-7b-report.md`,
   `planning/task-7c-report.md`, ADR 0011, `tools/corpus.py`, `corpus/manifest.json`, the
   session 1 rights policy and its classes.

## This dispatch has two steps; do step 1 only, then stop
**Step 1 (now):** propose the pages. Write
`/home/user/careerwright/planning/task-7f-addresses.md`: for each page the card names (the
official no-fee page for apprentices' training; Student Finance England's tuition fee loan and
maintenance loan pages; the Advanced Learner Loan page, since it now follows the same rule;
the 16 to 19 Bursary Fund; one T Level or Level 3 course page; the page stating the UCAS
deadline for the pack's nursing degree), give: the exact https address you propose (from
the pinned pack's existing sources and your knowledge; the controller checks them), what
the page must state, the session 1 class you expect and the terms that class relies on, its
template family and split, and the exact `tools.corpus` invocation (or the smallest addition
to `tools.corpus` it needs, built and tested now, with no fetch) that the controller runs to
fetch them through the guarded fetcher in one process. Then report and stop.

**Step 2 (after the controller's fetch, by a follow-up message):** labels, records, the new
pack version, `corpus/manifest.json` and `README.md`, and the school-leaver pack session's
package, as the card's first half says. The second half (publishing) waits for the product
owner's session.

## Hard rules
No web requests, no live calls, no subagents. Edit/Write for source changes (generators
fine). Explicit pathspecs. Never stage `var`, `answers-2.md` or `esco_research.txt`. No
unpermitted page body in git. Never start Docker, never read `.env` or print an environment
value, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report (step 1)
Reply with only: the addresses file's path, the command for the controller, any
`tools.corpus` change (commit SHA, `make check` result), and questions.
