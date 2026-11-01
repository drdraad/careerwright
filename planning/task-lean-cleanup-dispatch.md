# The lean clean-up (documents only, main tree)

The product owner approved, on 1 November 2026, the lean review's eight "now" items
(`planning/lean-review-2026-11-01.md`, proposals 1-7 and 12; proposal 6 is a habit and 12 a
ruling the controller records). You do 1, 2, 3, 4, 5 and 7. **Documents only: never change
code, tests, migrations, the register, the specification, ADRs, `CLAUDE.md`, `docs/evidence`,
`docs/reviews` or `fixtures/`.** The controller is running `make acceptance` meanwhile; it
reads code, not these files.

## Rules that bind every item
- Archive = `git mv` into an `archive/` folder (git keeps everything). Never delete a tracked
  file. Never move `planning/answers-2.md` or `planning/esco_research.txt` (the product owner's
  notes), the live contracts, `make-brief.sh`, `review-pkg.sh`, `cloud-build-images.sh`,
  `env-cloud.md`, open dispatches or anything an open task needs (Task 10B's carry-forward
  `carry-forward-task-10.md`, 7f's files until its second half lands, the lean review itself,
  `childline-checked-2026-11-01.md`, the session-W2 inputs).
- Never weaken, reword or drop a live rule. Merging rulings keeps every live clause word for
  word; only superseded numbers and history move.
- Keep every link that matters working (update paths that point into moved files from live
  documents only; history may keep its old links).

## Items
1. **Brief preamble:** move "Order, dependencies and dispatch preconditions", "Current
   position and next tasks" and the finished Task A1 card out of `docs/plan/l0-sprint-tasks.md`
   into `planning/controller-state.md` (the controller reads it; implementers don't). Change
   `make-brief.sh` so a brief carries the preamble up to (not including) the moved sections,
   plus the task's own card. Check: `make-brief.sh 10` produces a brief with "Always read",
   the Global Constraints, the standing rulings and the Task 10 card, and no "Current
   position".
2. **One current process ruling:** replace R12-R17's process clauses with one ruling "How we
   build and review (current)" stating today's rules (up to four implementers, one main tree
   plus worktrees on disjoint files, one reviewer per piece or half, one fix round with only
   safety, truth and lost-input fixed inside, full checks once per batch, backend and screens
   halves, the controller makes every web fetch and live call); keep any R12-R17 clause that
   is still live, word for word; move the superseded wording under "Superseded rulings" in
   `planning/controller-state.md`. Update `planning/implementer-contract.md` and
   `reviewer-contract.md` to match (same numbers).
3. **Contracts and environment facts:** in both contracts and the sprint tasks file's
   "Environment facts", replace Mac paths with `/home/user/careerwright` and
   `/home/user/careerwright-wt/<id>`, the integration branch name, Node 24 on PATH, the Adzuna
   unset for checks, Docker and the build shim and the Chromium setting for acceptance (fold in
   `planning/env-cloud.md`'s live facts; keep env-cloud.md as the machine note and point to
   it). The product's name is Careerwright.
4. **The ledger:** `git mv planning/progress.md planning/archive/progress-to-2026-11-01.md`;
   start a new `planning/progress.md` under 150 lines: one row per task (status, last commit
   range), what is running now, open questions for the product owner (the six school-leaver
   pack answers; anything else open), open rulings, and one **final-review list** gathering
   every line in the archived ledger starting "Parked", "minor (deferred)", "Carried to", and
   every review Minor marked for the final review (search the archived ledger and the review
   files; one line each with its source).
5. **Archive finished work in `planning/`:** move dispatch, report, review, re-review,
   fix-round, brief and carry-forward files of finished tasks, old audits, session 1 files, old
   handovers (`handover-2026-10-31.md`, `next-session-handover.md`; keep
   `handover-2026-11-01.md` until the next handover replaces it) and the plan-update files into
   `planning/archive/`. Delete only the gitignored review diffs (`planning/review-*.diff`), which
   `review-pkg.sh` rebuilds. Keep what the rules above protect.
7. **The plan's history:** in `docs/plan/development-plan.md`, move the v1.1-v1.6 version notes
   and the old "Order from here" lists into a "Revision history" appendix at the end; keep the
   current order. `git mv docs/plan/l0-assessment-handover.md docs/plan/archive/`. In the
   sprint tasks file's "Always read", narrow to plan sections 1, 3, 4 and 7 plus the card;
   section 5 for screen work; sections 8-10 for the task that closes a sprint.

## Checks
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH) must still pass
(some tests read docs). `make-brief.sh 10` and `make-brief.sh 12b` work. Report the before
and after sizes: the brief preamble (bytes), the ledger, `planning/` entries.

## Hard rules
Edit/Write for edits, `git mv` for moves (allowed here), explicit pathspecs, no web, no live
calls, no subagents, never start Docker, never read `.env`, never push. Commit in logical
steps; messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/home/user/careerwright/planning/task-lean-cleanup-report.md`; reply with the short contract
and the before/after numbers.
