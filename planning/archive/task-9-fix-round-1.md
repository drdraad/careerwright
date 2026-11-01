# Task 9 — fix round 1 (FIX_BASE 23d081b)

The review (`task-9-review.md`) is Spec ❌, Needs fixes: Critical 1, Important 4, Minor 8.
Read it in full. The reviewer's probes are in the controller's scratchpad (`t9/`), as the
review names them. These are the controller's rulings.

## Critical

1. **C1: a target with no modelled requirements reads "ready now". Ruling: fix all three
   parts as the reviewer says.**
   - (a) Readiness is never `ready_now…` when the target definition has no modelled
     required row. Give it its own state, with a blocker naming the coverage that is not
     modelled. Questions reach `enough` only with at least one modelled row or gate.
   - (b) Find a pack target through the reference crosswalk of the target's ESCO occupation,
     as well as by title. Then the slate's "nurse responsible for general care" reaches the
     pack's rows and the NMC gate.
   - (c) A `regulated: true` occupation with no typed gate is an unresolved protected-gate
     blocker ("registration requirement not yet modelled"), never silence.
   - **Tests:**
     - a domain test and an API test for a slate-chosen nursing label;
     - an unmodelled target ("Marine biologist");
     - a regulated occupation with no typed gate.
   - Each test fails first.

## Important

2. **I1: fix as the reviewer says.**
   - Add a "not yet assessed" state for when every mandatory blocker is no usable evidence,
     unresolved or not modelled. Keep `not_ready` for below required, not held and pathway
     outside the model. C1's state may be this same state, if its meaning is identical; say
     which you chose.
   - Add a partial-sketch qualification on any conditional result where a completed
     offering maps to a required row with a null level.
   - Update the test that asserts `not_ready` for an unanswered person.
3. **I2: fix as the reviewer says, within what the spec states.**
   - Refuse an answer that contradicts its level with `VALIDATION_FAILED`. For example,
     `not_learned` or `understand_not_tried` with a level above 0.
   - Map `not_learned` and `understand_not_tried` to a known level-0 finding: gap `learn`,
     not asked again.
   - Map `unsure` to an unresolved assumption: listed, and not asked again.
   - **A ceiling for `done_with_help`:** apply one only if spec section 9's anchors state
     it. Otherwise record it as a provisional R6 decision in ADR 0012.
4. **I3: fix.** A record the person enters is never `corroborated` while L0 has no
   reviewer.
   - Give a person-entered demonstration `provisional` confidence and the qualification
     `person_confirmed_demonstration`.
   - Add `person_confirmed_verification` whenever a protected gate is satisfied only by the
     person's own statement.
   - Assert both in the P04 and P05 tests.
5. **I4: fix as the reviewer says.**
   - Add the `pack` and `reference` labels to `QuestionsOut`.
   - Add `review_state` to `PromptRow`, `RowAssessment` and `Gap`.
   - Add `as_of` to `CandidateOption`.
   - Assert them in the integration tests, and regenerate the client.

## Minor

- **Fix:**
  - **M1:** correct the report's OpenAPI line.
  - **M2:** the MAP1-01 register row names Task 10's Skills chapter as owner, and says
    extracted rows need the person's confirmation.
  - **M3:** clear `relaxed_by_person` when a row is set back to required.
  - **M5:** assert the note, and assert readiness, with C1.
  - **M6:** remove the unreachable branch.
  - **M8:** carry the workspace's synthetic label on capability results. CLAUDE.md
    invariant: synthetic data is always labelled. A synthetic persona's result that says
    `synthetic: false` is a reproduced breach, not hardening.
- **Parked:**
  - **M4:** a provisional R6 item for session 2's decision sheet and the final review.
    Record it in ADR 0012 beside the other R6 items.
  - **M7:** R12, the final review.

## Also

- The same rules as before:
  - Edit and Write only;
  - never read `.env` or NESSA_HOME;
  - no live calls, never push, no subagents, never edit CLAUDE.md;
  - pack 0.1.0 and its pin are untouched.
- Run `make check`, then `make acceptance` once at the end, because this round changes the
  API and the stack tests.
- Append your report under "Fix round 1" in `task-9-report.md`. Then reply with the short
  contract.
