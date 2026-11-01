# Task 9 — task review (one reviewer)

You review Task 9 for Nessa L0: Sprint 4's backend. It covers the capability model, typed
protected gates, OUT-1 course outcomes, readiness, gaps and actions, and the combined
question graph. Follow `reviewer-contract.md` in this directory exactly: its method,
calibration and output.

All inputs are in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`.
- **Requirements:** `task-9-brief.md` (the task card, Global Constraints, standing rulings)
  and `task-9-dispatch.md` (the controller's dispatch notes and rulings 1–5).
- **The implementer's report:** `task-9-report.md` (unverified claims).
- **Your package:** `review-4516de8..23d081b.diff` (BASE 4516de8, HEAD 23d081b, 6,685
  lines).
  - **Excluded:** the generated client (`apps/web/src/generated/**`). The controller
    compared the OpenAPI documents. No operation or schema was removed, 7 operations were
    added, and only the enums `ErrorCode`, `ErrorStage` and `EventKind` changed. Check
    those three are additions only. The rest of that file's diff is reordering.
- **Calibration:** R11 and R12 (`docs/plan/l0-sprint-tasks.md`) apply. A hardening that no
  failing check, reproduced defect or Global Constraint requires is a Minor for the final
  review.

## The controller's rulings on the report's concerns (judge honesty, not scope)

- **Concern 1, the person's own examples are counted, not read.** Ruling: reading them moves
  to Task 10's Skills chapter. Extracted facts always need the person's confirmation (spec
  line ~156), whether they come from a model proposal through a `RunTask` or from span
  selection. Check that MAP1-01 is recorded as partly met, saying exactly what is missing.
- **Concern 3, the capability reference is not in the session 2 package.** Ruling: Task 11
  adds it. That means the rubrics, required levels, crosswalks and gate types, and proposed
  outcome levels for the pack's outcomes under those rubrics. Task 7c publishes the reviewed
  levels.
- **Concern 4.** Outcome accept and override get their persistence at Task 12's checkpoint.
- **Concern 5.** Every pack outcome level stays null in frozen 0.1.0, so no pack option
  counts towards numeric readiness until Task 7c. Check that every surface says so, and
  never shows "not ready" where the truth is "not yet assessed".

## Named risks, one focused check each

1. **Protected gates.** They are typed and immutable (legal practice, recognition,
   admission, eligibility). P04 cannot become ready by demoting registration, through any
   path: an edit, a chat proposal, a new target version or a gate "challenge". Read the
   challenge path closely.
2. **No adding into competence.**
   - Two introductory courses never add up to competence.
   - A topic mention is never practice, and practice is never an assessed demonstration.
   - An `unsupported` outcome's level stays null.
   - Enrolment or completion never overwrites current evidence.
3. **Unknown is never level 0, never ready and never ineligible.**
   - Self-report and demonstration stay distinct.
   - Recency and confirmation are carried.
   - ESCO-only rows are "unknown" (provisional decision).
   - No employability percentage anywhere.
4. **Proposed records never give an unqualified readiness result** (OPTN-09, R9). The
   pack's date and each record's review state reach every derived result. Pack job-board
   rows are never counted as the person's exemplars, and nothing claims a full-description
   employer sample (dispatch ruling 1).
5. **Versioning and recomputation.**
   - Every derived result carries the target and matrix version.
   - Changing an essential non-protected row creates a new target definition and
     invalidates earlier ranks.
   - Evidence changes recompute only the affected gaps.
   - Check the tests prove these, not just call them.
6. **The question graph.** Gates come first, then decision-impact order. The weights, the
   80% stop and the 12 initial prompts are named constants, not buried literals.
7. **Persistence and API.** Check migration r0029 and the 7 endpoints:
   - the migration is forward-only;
   - CHECKs on state columns;
   - RLS on every new table, with least-privilege grants;
   - consequential writes take an expected version and an `Idempotency-Key` through
     `run_idempotent`;
   - errors are `NessaError` codes that never echo input;
   - receipts hold no model output;
   - `PROTECTED_GATE`'s web words are in `vocabulary.ts`.
8. **The capability reference** (`capability-reference-0.1.0.json`). It is pinned and loaded
   like the pack. It checks the pack references that Task 7b's M3 left. Pack 0.1.0 and its
   pin are untouched.
9. **The demo workspace.** It shows the real pack's matrix, not TRACE-01's synthetic one.
   - Fixture content stays labelled and only in the fixture workspace.
   - Pack content shows its date and review states.
   - Nothing fills a live field.
10. **The module boundary.** `nessa/capability` respects the import rules, with
    `test_boundaries.py` updated, and holds no empty layers. No live call was made, and DBOS
    `application_version` is unchanged with no new run kind.

## Rules

- Read-only.
- No live calls.
- No subagents.
- Never read `.env` or NESSA_HOME.
- Do not compose self-harm or distress text.

Write your full report to `task-9-review.md` in this directory. Then reply with only your
two verdicts and your counts of Critical, Important and Minor issues.
