# The lean clean-up: report

Status: DONE_WITH_CONCERNS (documents only; no code, test, migration, register, specification,
ADR, `CLAUDE.md`, evidence, review or fixture file changed).

## Commits (branch `claude/confident-ramanujan-ux3saw`, main tree, pathspecs only)
- f4b129a Items 1-3: briefs stop carrying controller state; one current process ruling; this
  machine's facts.
- 004aaa6 Item 7: the plan's history moves to a "Revision history" appendix; the assessment
  handover moves to `docs/plan/archive/`.
- 56b3f69 Item 4: the ledger is archived; a short live ledger with one final-review list.
- 494d99f Ledger repair (see concern 1).
- 3ff83f5 Item 5: 301 finished files move to `planning/archive/`; review diffs deleted.
- this report.

## Before and after
| What | Before | After |
|---|---|---|
| Brief preamble (what `make-brief.sh` copies before the card) | 42,140 bytes, 570 lines | 26,077 bytes, 346 lines |
| A whole brief (Task 10 / Task 12b) | 46,576 / 48,686 bytes | 30,512 / 32,622 bytes |
| Ledger `planning/progress.md` | 334,017 bytes, 1,165 lines | 8,498 bytes, 124 lines |
| `planning/` entries | 352 | 46 (302 in `planning/archive/`) |
| Plan "How to use this plan" | 8,519 bytes | 508 bytes |
| Plan section 6 (roadmap, before Sprint 0's card) | 15,852 bytes | 9,190 bytes |

## What changed
1. **Brief preamble.** "Order, dependencies and dispatch preconditions", "Current position and
   next tasks" and Task A1's card moved word for word into `planning/controller-state.md`.
   `make-brief.sh` now stops at the first task card (and at the old headings, as a guard).
   The tasks file's opening points to `controller-state.md` for the order and "rule N".
2. **One process ruling.** R12-R17 are now one ruling, "R12–R17 How we build and review
   (current)": a short list of today's rules, then every live clause word for word under its
   old number (R13 whole; R14 except "Bound loops"; R15 except "Up to two"; R16's one reviewer,
   one fix round and the flaky-run line; R17 whole). Superseded wording (R12, "Bound loops",
   R15's "up to two" and old branch, R16's "full checks once per piece" and "up to three")
   is under "Superseded rulings" in `controller-state.md`, each with what replaced it. The one
   wording change in a kept clause: R15's branch name `l0-local-release` became
   `claude/confident-ramanujan-ux3saw` (item 3 asked for the integration branch name).
3. **Facts.** "Environment facts" now describes this Linux container (paths, branch, Node 24,
   the Adzuna unset for checks, Docker and the build shim, the Chromium setting, the
   controller making every fetch and live call, the product's name). Both contracts match
   (four implementers, acceptance by the controller once per batch, the lock path, Chromium in
   the implementer contract, "Careerwright L0" in the reviewer contract). `env-cloud.md` stays
   the machine note; its stale lines (no datasets, blocked hosts) now say what the ledger
   records (datasets fetched and hash-checked; hosts allowed, then network widened).
4. **Ledger.** `planning/progress.md` → `planning/archive/progress-to-2026-11-01.md`. The new
   ledger: one row per task, running now, open questions, open rulings and owed checks, a
   final-review list (one line per ledger entry starting "Parked", "minor (deferred)",
   "Carried to" or "Deferred → final review", and per review whose Minors went to the final
   review, each with its archive line or file), and an "Events" section for new lines.
5. **Archive.** Moved: finished tasks' dispatches, briefs, reports, reviews, re-reviews and fix
   rounds; audit lenses and the Muse Wonder audit; session 1 files; `handover-2026-10-31.md`,
   `next-session-handover.md`; the plan-update files; `plan-path`; carry-forwards for finished
   tasks. Kept: everything the dispatch protects, plus Task 10's brief and Task 10A's files
   (Task 10's screens half is open) and the 7b and 7c reports (7f's second-half dispatch reads
   the 7c report). `carry-forward-task-W2D.md`'s two links now point into `archive/`.
7. **Plan.** The v1.1-v1.6 version notes, the v1.1 and v1.4 orders, the v1.5 table and the old
   "Review session 1" paragraph moved word for word to "# Revision history" at the end. Section
   6 keeps the v1.6 order, plus three v1.5 clauses that still hold (backend never waits for a
   session; why Roles comes after the path; the end-to-end session may offer a smaller L0) and
   the sprint-review order sentence. "Always read" is now sections 1, 3, 4 and 7 plus the card;
   section 5 for screen work; sections 8-10 for a sprint's closing task.

## Checks
- `export PATH=/opt/node24/bin:$PATH; env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`
  on 3ff83f5: exit 0 (backend 2,160 passed, 8 skipped; "All checks passed!"; client drift
  clean; Vitest 472 passed).
- `make-brief.sh 10` and `make-brief.sh 12b`: both work; each brief has "Always read", the
  Global Constraints, Environment facts, the standing rulings and its card, and no "Current
  position". The test outputs were removed (Task 10's tracked brief restored as it was).
- `make acceptance`: not run (documents only; the controller runs acceptance).

## Concerns
1. **A ledger line was briefly lost, and restored.** While I moved the ledger, the controller
   appended its 7f line to a new `planning/progress.md` and committed it (ebc1c1a); my new
   ledger then replaced that file in 56b3f69. 494d99f puts the line back word for word under
   "Events" and updates the rows it changes (the six pack rows answered, 7f's second half
   running).
2. **Two links I may not fix.** The specification (line 1311) and ADR 0008 (line 9) link to
   `docs/plan/l0-assessment-handover.md`, now at `docs/plan/archive/`. ADR 0015 (lines 259,
   303) names `task-6dB-fix-round-1.md` and `-2.md`, now in `planning/archive/`. All four are
   records; change them only if you want.
3. `planning/task-10-brief.md` is still the old brief (old preamble, Mac facts). Regenerate it
   with `make-brief.sh 10` when Task 10's screens half is dispatched.
4. Still yours to record: rulings 6 (one paper file per piece) and 12 (infrastructure frozen)
   in the tasks file. The new ledger lists them as in force. The R11 carve-out from Task A1's
   re-review stays on the open list.
