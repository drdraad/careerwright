# Task 9 re-review 3: fix round 3 (b8bd1fc..f6e9bfb)

Fix round 3 fixes both items in scope, R2-1 and R2-2. It introduces no regression, and I
found one new Minor issue.

## How I checked

- **Mode:** a scoped re-review of R2-1 and R2-2, read-only. No live calls and no
  subagents; I did not read `.env` or NESSA_HOME.
- **Inputs:** `task-9-fix-round-3.md`, the report's "Fix round 3" section, and the whole
  369-line package.
- **Generated client:** I compared the OpenAPI documents at b8bd1fc and f6e9bfb. The only
  change is that the `Qualification` enum gains `open_conflict`. Nothing was removed, and
  no path changed.
- **Pack:** nothing under `catalogue/` changed.
- **Probes:** all run from `backend/` against HEAD f6e9bfb.
  - Two existing probes, re-run: `head2/probe_round2` and `head/probe_fr1`.
  - Two new probes: `head3/probe_round3` and `head3/probe_conditional_conflict`.
  - All are under
    `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/t9/`.
- **Working tree:** still clean.

## Probe results at HEAD

- **`probe_round2`, R2-1.** This is P01's data quality target with every modelled row at
  level 1.

  | Case | State | Route chart | Blockers |
  |---|---|---|---|
  | As given | `not_ready` | true | `below_required` |
  | After "statistics" is set to essential | **`not_ready`** | **true** | `below_required`, `not_modelled` |

  In re-review 2 the second case read `insufficient_coverage` with no route chart.
- **`probe_round2`, R2-2.** Case 1 (A at level 2, then "not learned" under B) reads ready
  now with **`open_conflict`** among its qualifications.
- **`probe_round2`, other cases.** The bookkeeper resolutions are unchanged from re-review
  2.
- **`probe_fr1`.** All three N1 orders are unchanged and correct:
  - order 1: A keeps level 2;
  - order 2: A keeps level 2, with the conflict;
  - order 3: A goes back to unknown and is asked again as `other_rubric`.

  Its "two crosswalk matches" line is a known artefact of that probe's own setup;
  `probe_twice` is the correct check for that case.
- **`probe_round3`, new.** It runs 4,025 synthetic combinations of:
  - with or without a skill row;
  - no gate, a practice gate, the right to work, or both;
  - nothing extra, an unmodelled row, or the unmodelled regulation gate;
  - seven evidence patterns, including both kinds of conflict;
  - five statement states for each gate.

  For each combination it checks the readiness state, `open_conflict` and the route chart
  against the rules stated in the checks below. It found **0 violations**, and all four
  non-conditional states occurred.
- **`probe_conditional_conflict`, new.** This is TRACE-01 with a self-report of 3 against a
  reviewed assessment of 1, met only by course A's planned level 2. It reads
  `conditional_on_assessed_completion` with `open_conflict`.

## Items

| Item | Status |
|---|---|
| **R2-1** | Fixed |
| **R2-2** | Fixed |

**R2-1: fixed.**
- `KNOWN_SHORTFALL` (`readiness.py:104-106`) holds `below_required`, `not_held` and
  `pathway_outside_model`. Any of these gives `not_ready` first (`readiness.py:359-362`).
- A coverage gap only gives `insufficient_coverage` when no shortfall is known
  (`readiness.py:363-364`). A coverage gap is:
  - nothing covering the target;
  - a required row with no rubric;
  - or the unmodelled regulation gate.

  It is computed at `readiness.py:351-358`. It stays a blocker of its own:
  `no_modelled_requirements`, `not_modelled` or `unresolved`.
- `show_route_chart` is now the plannable gaps alone (`readiness.py:372`, `:403`).
- Test: `test_a_known_shortfall_stays_not_ready_beside_a_requirement_no_answer_can_settle`,
  on P01's target with "statistics" set to essential, as ruled.

**R2-2: fixed.**
- `Qualification.OPEN_CONFLICT` (`readiness.py:157`) is added whenever a met mandatory row
  has `conflict: true` (`readiness.py:663-664`).
- Both cases are tested:
  - the cross-rubric "not yet done", in `test_a_ready_result_with_an_open_conflict_says_so`
    (which also checks that it is absent without the later answer);
  - the demonstration against a self-report on P05's pack target, in
    `test_a_demonstration_that_disagrees_with_a_self_report_is_an_open_conflict_on_the_pack`.
- It is recorded in ADR 0012 decision 7 and the register.

## The checks you asked for

1. **The state precedence.** It holds: `not_ready` (a known shortfall), then
   `insufficient_coverage`, then `not_yet_assessed`, then conditional or ready
   (`readiness.py:359-370`).
   - Every possible blocker kind falls into exactly one branch.
   - Ready needs no blocker at all.
   - In all 4,025 `probe_round3` combinations the computed state equals this ladder.
2. **No path reads ready with an open conflict and no qualification.** It holds, in both the
   current and the conditional scenario. In `probe_round3`, `open_conflict` appears exactly
   when a met mandatory row has a conflict: never missing, never spurious. The conditional
   case was checked separately (`probe_conditional_conflict`).
3. **`show_route_chart` follows the plannable gaps.** It holds.
   - It is true exactly when a mandatory learn, credential or experience gap exists, in
     every combination.
   - Those gaps come only from `below_required` and `not_held`, so in practice the chart
     shows only in `not_ready`, never when ready now, and never when only unknowns or
     coverage gaps remain.
   - It stays on for a known shortfall beside a coverage gap (R2-1).

## New issues

### Minor

**R3-1. A route chart for a gap that cannot be planned within the model.** This is not a
regression: it has been the behaviour since the first candidate, and only came to light
here.

- **Where:** `backend/src/nessa/capability/readiness.py:372`, `:403`.
- **What:** "plannable" is decided by the gap's kind alone. P04's registration, when not
  held, is a mandatory credential gap whose only pathway is beyond the 24-month planning
  model. Its action reads `outside_planning_model` with `MODEL_SCOPE_EXCEEDED`, yet the
  result still sets `show_route_chart: true` and `training_required: true`
  (`probe_round3`'s P04 line).
- **Why it matters:** BND1-08 asks for an explanatory sketch and an unsupported-model state
  for such a pathway, not a route chart. There is nothing within the model to plan.
- **Fix:** exclude gaps whose action is `outside_planning_model` from `show_route_chart`.
  Or leave it to Task 10's words, recorded for the final review. It is not required by any
  failing check (R12).

## Counts

- Items: fixed 2 (R2-1, R2-2); partly fixed 0; not fixed 0.
- New issues: Critical 0, Important 0, Minor 1 (R3-1, which existed before this round).
