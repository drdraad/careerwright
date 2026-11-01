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

## Fix round 1

Rebased onto `claude/confident-ramanujan-ux3saw` at e82a390, which includes the acceptance fix fd4f939 and 61597ee. The rebase was clean, and migration 0045 is still the next free number.

Commits:
- `1b99c40`: the Skills chapter's facts (rebased `dbc1bd1`)
- `2bc364b`: the ADR lines and register rows (rebased `d011472`)
- `b24668e`: this fix round, which is the head

### Fix 1: span offsets now say their unit (review I1)
- **The change:** `AdvertSpan.start` and `.end` are UTF-16 code units, the same unit a browser's selection gives. This is stated in the field descriptions and the OpenAPI document.
- **On the server:** `capability/adverts.py` converts them to characters. An offset past the text is refused as `span_outside_text`. An offset inside an astral character (one that takes two UTF-16 units) is refused as `span_splits_character`.
- **What is stored:** offsets are kept as the person chose them, in UTF-16 units, and read back through the same conversion.
- **Wording updated:** the docstrings of the command, the route and migration 0045.
- **Red first:** I wrote two tests before the fix:
  - `test_offsets_are_utf16_code_units_after_and_inside_astral_characters`: a rocket emoji, then "SQL" written in mathematical bold letters, before and inside the spans.
  - `test_a_span_splitting_an_astral_character_is_refused_with_its_reason`.
  - Before the fix they failed. The excerpt came back as `'yst.\nYo'` instead of `'analyst'`, and the split span was not refused. After the fix both pass.

### Fix 2: the capability model reads pack 0.2.0 and reference 0.2.0
- **The change:** `PACK_VERSION` and `REFERENCE_VERSION` in `capability/commands.py` are now "0.2.0". Both are read through `load_pack` and `load_reference` and their pins.
- **Reference 0.2.0 fits:** it exists, matches its pin and loads against pack 0.2.0. The four targets, their crosswalks, the rubrics and the gates are the same as in 0.1.0.
- **What actually differs:**
  - each record's review state;
  - the `proposed_sources` uncertainty is dropped from rows whose sources are now reviewed;
  - session 2's five corrected outcome mappings.
- **What I checked stays the same:** in the domain, each target's readiness state, gaps and candidates are unchanged, and the planning catalogue's C04 values are unchanged.
- **Scope:** this is app-wide, not Skills only. Planning and the other capability reads use the same `committed_data`, so no two chapters disagree.
- **New test:** `test_skills_reads_the_reviewed_pack_0_2_0_and_its_reference_through_their_pins` checks the versions, and checks both files' SHA-256 against `PINS`.

### Expected values that changed, and why
1. **`tests/domain/test_targets.py::test_the_migration_backfills_with_the_committed_pack_targets_and_crosswalks`.** It said `committed.version == migration.PACK_VERSION`. Migration 0034 is fixed at 0.1.0, while the app now reads 0.2.0. It now asserts both versions explicitly, and still asserts that the targets and crosswalks are identical.
2. **`tests/integration/test_capability.py`, the pack label:** 0.1.0 / 2026-10-29 / `records_reviewed == 0` becomes 0.2.0 / 2026-10-30 / 55 reviewed, 66 proposed.
3. **`tests/integration/test_capability.py`, the NMC gate's citations:** they were all `proposed`. In 0.2.0 some are reviewed and some proposed. It now asserts the set {reviewed, proposed}, and that the row itself stays `proposed`. The `as_of` dates are unchanged: they are retrieval dates.
4. **`tests/integration/test_capability.py`, the questions envelope's `pack.dated`:** 2026-10-29 becomes 2026-10-30.
5. **`tests/integration/test_planning_options.py`:** the pack version and catalogue label change from 0.1.0 / 2026-10-29 to 0.2.0 / 2026-10-30. The C04 fee, its citation and the unknown start are unchanged (computed with `pack_catalogue`).
6. **`tests/integration/test_migrations.py`, three `stored == decided` checks:**
   - Records the migrations backfill carry `pack_version` "0.1.0". The resolver now stamps "0.2.0", and API writes in that test also stamp "0.2.0".
   - A `decisions()` helper now compares the records with the pack version left out. The targets and crosswalks are identical, so the decisions themselves are unchanged.
   - Nothing in the code reads a record's `pack_version`.
7. **`tests/integration/test_skills.py`:** the pack label becomes 0.2.0 / 2026-10-30.
8. **`tests/domain/test_skills_chapter.py`:** it now reads `committed_data()`. Its `as_of` check compares against the records' retrieval date (2026-10-29) instead of the pack's date.

Readiness stays strict, as you asked: the rubrics in reference 0.2.0 are still `proposed`.

### Checks
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24): **exit 0** on the final tree. Backend 2,159 passed, 8 skipped. Vitest 471 passed.
- The first run had one Vitest failure: `FirstQuestion.test.tsx` "shows the calm panel, stills the world…". I didn't touch that file or its code. A re-run passed, so I treated it as flaky (rule R16).
- The client was regenerated: the OpenAPI document now carries the offset descriptions.
- Integration and acceptance were not run; the controller runs them. The integration expectations above are computed from the domain functions, not from a run.
- No live calls.

### Rule note
Every source change in this round used Edit or Write. `ruff format` and `pnpm run generate` are generators.

## Follow-up: the three failing tests in acceptance run 7

**Cause:** the mistake was in the test, not the code. The helper `paste()` in `tests/integration/test_skills.py` read `pasted.json()["job_id"]`. The paste endpoint actually answers with the job's details, `{"job": {"job_id": …}, "claims": […]}`, the same shape `test_acquisition.py` already reads. The helper now reads `["job"]["job_id"]`. No assertion changed.

**Commit:** `81010d3`, in the main tree, committed with an explicit pathspec.

**Checks:**
- Focused run under the lock with the build shim: `pytest -m integration tests/integration/test_skills.py` gave **8 passed** (log `/tmp/skills-int.log`). The lock was removed afterwards.
- `make check` (Adzuna variables unset, Node 24): exit 0. Backend 2,159 passed; Vitest 471 passed.

## Follow-up: readiness on a draft checklist

The product owner chose option A (2026-11-01): show the judgement, labelled as based on a draft checklist.

Worktree `/home/user/careerwright-wt/10a`, branch `wt-10a`, rebased onto `claude/confident-ramanujan-ux3saw` (f2fcb98; the rebase was clean, only docs and planning had moved). Commits:
- `5a4e33c` Task 10A follow-up: Skills shows readiness on a draft checklist, with the rubrics' review state
- `9a31930` Task 10A follow-up: ADR 0012 amendment line and register row (head)

Status: DONE.

### What changed
- **`capability/skills.py`:**
  - A target is `assessed` wherever a required row has a rubric and the result is not `insufficient_coverage`.
  - Its `readiness` is the capability model's result, unchanged. It is the same object `GET .../readiness` gives, and still carries the `proposed_rubrics` qualification.
  - New field on each target: `rubric_review`. It is `reviewed` when every rubric the result rests on is reviewed, `proposed` when any is a draft, and `null` when not assessed.
  - Nothing modelled (`no_rubric`, which covers eligibility alone, such as the nurse target) and `insufficient_coverage` stay `not_assessed`, with no result. Nothing about gates, levels or qualifications changed.
- **Public change:** the reason `rubrics_not_reviewed` is no longer produced, so I removed it from the enum. The web used it only in the generated client. The client is regenerated.
- **`api/capability_schemas.py`:** the `SkillsOut` docstring (it appears in the OpenAPI document) now describes the new rule.
- **Docs:** an ADR 0012 amendment line with the product owner's answer, and a follow-up note on register row RDY1-03.

### Tests (RED, then GREEN)
- Written first in `tests/domain/test_skills_chapter.py`. Before the code change: **9 failed, 16 passed** (`uv run --locked pytest -q tests/domain/test_skills_chapter.py`). After it: **25 passed**.
  - The three pack targets on draft rubrics are assessed, with `rubric_review == "proposed"`. Their readiness equals `assess(...)`, carries `proposed_rubrics`, and with no evidence is neither ready nor `insufficient_coverage`.
  - A reviewed rubric gives `rubric_review == "reviewed"`.
  - One draft rubric beside reviewed ones gives `proposed`.
  - Not assessed, with `rubric_review` null: the nurse target (gate only), a target outside the pack, and insufficient coverage.
  - P05's case on the real bookkeeping target: ready now, apply now, labelled `proposed`, and qualified by both `proposed_rubrics` and `proposed_records`.
- `tests/integration/test_skills.py`: the data target is now `assessed` and `proposed`, and its `readiness` equals `/readiness`'s result for the same target. **Not run:** I changed no SQL, so the dispatch's focused run didn't apply. The controller runs integration.

### Checks
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24) on the final tree, after the rebase and the docs commit: **exit 0**. Backend 2,160 passed, 8 skipped. Vitest 471 passed. Biome, `tsc` and client drift clean.
- Integration and acceptance: not run. The controller runs acceptance.
- No live calls: $0. No web requests, no Docker.

### Rule note
Every source change used Edit or Write. `pnpm run generate` is a generator.

### Skip when reviewing
`apps/web/src/generated/**` (regenerated client).
