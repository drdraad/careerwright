# Task 10A report: the Skills chapter's facts (backend half)

Worktree `/home/user/careerwright-wt/10a`, branch `wt-10a`, rebased onto
`claude/confident-ramanujan-ux3saw` (e1faff8). Commits:
- `dbc1bd1` Task 10A: the Skills chapter's facts and the person's chosen advert spans
- `d011472` Task 10A: ADR 0012 and 0009 amendment lines; register rows (backend; screens in 10B)

Status: DONE_WITH_CONCERNS (see Concerns).

## What I built
- **`GET /v1/workspaces/{id}/capability/skills`** (`SkillsOut`). Codes and numbers only. For each target:
  - **What ESCO lists.** The seed comes from the target's record. `seed` is `esco_occupation`, `none_of_these` or `no_occupation`. Each listed skill carries its `not_part_of_job` mark, which nothing computed reads. `details_version` is the expected version for saving marks through the existing `PUT .../profile/titles`.
  - **The person's own examples.** Each example comes back with its kept text and the spans they chose. A chosen span is read back as the advert's own words.
  - **`requirements`.** These are the target's required rows. Each row carries its review state, its pack records' date (`as_of`), its protected gate, its rubric and review state, and `entry_facts`.
  - **Readiness.** `assessment_state` is `assessed` or `not_assessed`. `not_assessed_reason` is `no_rubric`, `insufficient_coverage` or `rubrics_not_reviewed`. `readiness` is filled only when assessed.
  - **Versions.** `matrix_version` and `definition_version` are on every target.
  - **Shown once for the whole response:** the shared question graph, `usual_in_role` (null with no role, never empty), the person's `qualifications`, and the pack and reference labels.
- **`POST .../capability/advert-spans`** (`SelectAdvertSpans`). It takes an expected capability version and an Idempotency-Key, and makes no model run.
  - It only accepts one of the person's own examples for that target.
  - Spans are checked against the kept text: inside the text, not empty, not blank, at most 600 characters each, at most 12, no overlap.
  - An empty list clears the selection.
- **Migration 0045:**
  - `advert_span_selections`: append-only for the API role, row-level security, CHECKs on the spans' shape. It stores offsets and the text's hash only, never advert text.
  - `careerwright.pasted_example_document(attempt)`: a SECURITY DEFINER function. It returns a sealed body only for a `pasted_text` attempt in a workspace the calling actor owns, while their access is active.
- **Modules:**
  - New: `capability/adverts.py` (pure), `capability/skills.py` (pure), `capability/skills_commands.py`.
  - Store additions: `capability/store.py` (selections), `evidence/store.py` (`exemplar_copies`, `pasted_document`), `evidence/acquisition.py` (`examples`, which opens pasted text only), `profile/title_details.py` (`target_details`).
  - `capability/commands.py`: the private helpers are now public (`advance_version`, `capability_event`, `VersionedCommand`), and `CapabilityView.records` was added.
- **Course outcome review** (`tests/domain/test_course_outcomes_review.py`). All 18 outcomes on the ten course pages are in a table, each with its reason. This covers pack 0.2.0 and 0.1.0; the five mappings session 2 changed are listed.
  - For every outcome, completing its course (as stated, and as accepted by the person) never raises its row, never meets or satisfies it, and never makes the target ready or conditionally ready.
  - So a route resting on it gets the checker's "readiness not reached in this model".
- **Documents:**
  - ADR 0012 amendment line (Task 10A).
  - ADR 0009 amendment line (the API opens a pasted body).
  - Register rows MAP1-01, MAP1-09, RDY1-03, STATE-08, STATE-11, PROF-07, PROF-13, ASSESS-02 (no change), ASSESS-03 and OPTN-08, each marked "backend; screens in 10B".
  - MAP1-06 and SEC-09 are unchanged: no backend part.

## Rulings
1. **"Readiness where a reviewed rubric exists" is read strictly** (fail-safe; marked provisional, R6, in the ADR line).
   - A target is assessed only if at least one required row has a rubric, every such rubric is `reviewed`, and the result is not `insufficient_coverage`.
   - Reference 0.1.0 is `proposed`, and session 2 said no to every anchor set. So **today no target is assessed in Skills**; P05's apply-now result does not show there.
   - `GET .../readiness` and planning are unchanged.
2. **Entry facts match by whole words.** A qualification names a requirement when its concept key (`careerwright.concept_key`) appears as whole words in the requirement's label or in a posting's wording of it.
   - Facts only: they never feed readiness.
   - Achieved beside a protected gate is `achieved_unverified`. Achieved beside any other row is `achieved_stated`.
3. **The API reads the person's own pasted text** through the narrow definer function above. Without it, spans can't be checked or shown. Fetched page bodies stay the worker's alone.
4. **Chosen spans are shown, not yet read into matrix rows** (`exemplar_rows_read` stays false). Turning them into rows needs the person's confirmation step, which is 10B's flow.
5. **Chat proposals:** none exists for Skills in L0. Every Skills write is a single command that any future proposal must go through (PROF-07).
6. **The app still pins pack and reference 0.1.0.** Moving the capability model to 0.2.0 or 0.3.0 would touch planning, target records and migrations, so I left it out.

## Checks
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` on the final tree (after the rebase and the docs commit): exit 0. Backend 2,151 passed, 8 skipped; Biome, `tsc` and client drift clean; Vitest 471 passed.
- New domain tests: `test_skills_chapter.py` (21) and `test_course_outcomes_review.py` (74), all passing.
- **TDD:** the code came before most domain tests.
  - The tests did catch real faults: a missing early return for entry facts, a wrong reason for the nurse target (which led to the third reason `insufficient_coverage`), and the five mappings that differ between packs.
  - The course-outcome tests describe data the code already handled correctly. I checked they are meaningful with a mutation: giving C06.1 an accepted level 2 makes `planned_level` 2, which the test would fail on.
- **SQL check:** I checked migration 0045 in a throwaway local PostgreSQL 16.15 (stub tables, removed afterwards):
  - the CHECK accepts and rejects the right span shapes;
  - the function opens the owner's own pasted body, and refuses a fetched body and another actor.
- **Integration:** `tests/integration/test_skills.py` (8 tests) is written but **not run**; the controller runs integration and acceptance.
- **Acceptance:** not run; the controller runs it.
- No live calls: $0.

## Concerns
- **Ruling 1 means Skills shows no readiness result anywhere today.** One-line question for the product owner: "Should Skills show readiness on the proposed rubrics, labelled as proposed? Yes would show P05's 'apply now' result again."
- **Integration tests are unrun.** They depend on the ESCO sample and pack facts I read but could not exercise: IT support "ITIL Practitioner" text, "nurse responsible for general care" having essential skills, and "Doula" having no occupation.
- **Rule deviation.** Two mechanical renames went through a script instead of Edit: the `Qualification` to `PersonQualification` rename in `skills.py` (python), and one enum rename in a test (sed). Everything else used Edit or Write.
- **Wider read access.** The API's read of pasted bodies is security-relevant (ADR 0009 line). A reviewer should look at the definer function.

## Skip when reviewing
`apps/web/src/generated/**` (regenerated client).
