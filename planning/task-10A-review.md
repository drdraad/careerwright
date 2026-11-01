# Task 10A review: the Skills chapter's facts (backend half)

Reviewer: the one independent reviewer (R16). Package `review-e1faff8..d011472.diff` (2,583
lines, read in three passes: API and domain code, migration and evidence store, tests and
documents). Worktree `/home/user/careerwright-wt/10a` at `d011472`, read only. No suites
re-run, no Docker, no web or live calls, `.env` not read.

## Verdict

**Needs fixes** (one small fix). Critical 0, Important 1, Minor 6, plus 2 questions for
the product owner or controller.

### Spec Compliance
- ✅ The read endpoint, the advert-span command, migration 0045, the "not part of my job"
  display state, entry facts, `usual_in_role` absent without a role, the versions on every
  target, the pack and reference labels, and the course-outcome review are all present and
  match the dispatch's six items.
- ❌ One contract gap: span offsets don't say their unit (I1).
- ⚠️ Cannot verify from diff: `tests/integration/test_skills.py` (8 tests) has not run. The
  controller runs it. The implementer's "throwaway PostgreSQL 16.15" check of 0045 is an
  unverified claim. Acceptance not run.
- ⚠️ Carried items for Task 10 in `planning/carry-forward-task-10.md` were not in 10A's
  dispatch, so they are not counted against 10A. Two matter for the backend: pinning pack
  and reference 0.2.0 (Q2), and the R7–R35 ruling ("no evidence yet" is unknown, never
  level 0; anchor 0 is an assessed "cannot yet"). The second rests on the anchors that the
  questions in Skills offer. 10B or the controller should take both.

### The named risks, one by one

1. **Migration 0045's SECURITY DEFINER function: tight, and the widening is needed.**
   - `careerwright.pasted_example_document` (r0045:57) pins `search_path = pg_catalog,
     pg_temp`, names every object by schema and uses no dynamic SQL, so there is no
     injection path.
   - It is `REVOKE`d from PUBLIC and granted to `careerwright_api` only. Its owner is the
     setup-only migrator, as for r0021 and r0023's definer functions.
   - Its WHERE clause is the `api_owner` policy on workspaces (r0001:136) almost word for
     word: the owner is `current_actor_id()` and the actor's access is `active`. It adds
     `route = 'pasted_text'`.
   - A fetched page can't be `pasted_text`. r0013's CHECK ties `pasted_text` to `run_id IS
     NULL AND created_by IS NOT NULL`, so only the API's paste insert writes it.
   - The worker's update of pasted copies is already blocked (r0020).
   - It trusts the same actor setting that every row-level policy already trusts, so it is
     no weaker than the existing model.
   - Is it needed? Yes. Before this change the API could read only the claim's first 200
     characters. The person can't choose spans in text they can't see, and the server
     can't check spans without the text.
   - Test gap: see M1.
2. **Readiness only where a reviewed rubric exists.**
   - `assessment_state` (skills.py:170) puts `readiness` in the response only when its state
     is `assessed`. Otherwise it gives `not_assessed` with a reason, and `requirements`
     carries what the target asks.
   - Unknown is never level 0: `required_level` is `int | None`, and nothing new computes a
     level.
   - Protected gates: nothing new edits a row. An achieved qualification beside a gate is
     `achieved_unverified`, and the integration test checks that `/readiness` keeps the NMC
     row `unresolved`.
   - Nothing new finds a person ineligible.
   - `matrix_version` and `definition_version` are on every target. The pure function
     refuses an assessment of another matrix.
3. **"Not part of my job", expected qualifications, no role.**
   - The marks are read only by `esco_listed`. A grep shows no computed reader.
   - The domain test compares the whole response with and without a mark. The integration
     test also checks that the capability version doesn't move.
   - Expected is always `expected_not_met`.
   - `_usual_in_role` returns `None` for no role, for "I haven't had a job yet" (its own
     `FieldState`), for a role naming no single occupation, and for an empty skill list. It
     is never empty.
4. **The advert-span command.**
   - It takes an expected capability version through `advance_version`, and an
     Idempotency-Key through `_write` and `run_idempotent`.
   - It refuses a target that isn't in the profile, and an example that isn't the person's
     own for that target (404, no input echoed).
   - At most three examples per target is enforced at paste. At most 12 spans per example
     is checked by the domain and by a CHECK.
   - It makes no model run. Its receipt is `CapabilityChangeOut`: IDs and versions only.
   - Error details hold codes and the current version only.
5. **Facts and codes, no sentences (R11).** The new response models carry codes, numbers,
   the person's own words and the advert's own words, and no composed sentences. The error
   messages follow the existing pattern: the web shows the code's words.
6. **The ten course pages' false-positive mappings.**
   - All 18 outcomes are in a table, each with its reason, for packs 0.1.0 and 0.2.0, and
     the five mappings that changed are listed.
   - For each outcome, completing it as stated, or as accepted by the person, never sets a
     planned level and never changes its row's status to met or satisfied.
   - These assertions run against the real pack and the real `assess`. The target-level
     assertion is weak (M3).
7. **The open question: "no target shows readiness because the reference is proposed".**
   - It is not a misreading of the words. The brief, plan section 4 and the ADR amendment
     all say "readiness where a reviewed rubric exists", and session 2 said no to every
     anchor set, so no reviewed rubric exists.
   - But it is probably not what the authors pictured. ADR 0012's amendment adds "(decision
     7 already makes such a target `insufficient_coverage`)". That equates "no reviewed
     rubric" with "nothing modelled", meaning targets outside the pack. The reference 0.2.0
     line expects results resting on rubrics to stay qualified `proposed_rubrics`, not
     hidden.
   - The strict reading also leaves RDY1-03's Skills part (P05's "apply now") with nowhere
     to show. And Skills will say "not assessed" for a target that `/readiness` and Routes
     treat as ready now.
   - It is fail-safe and marked provisional, so it is not a defect. It is a policy question
     for the product owner (Q1). R14 says to ask before a second round on it.
8. **Tests assert real behaviour.**
   - The domain tests use the real pack, reference and `assess`, plus synthetic matrices
     that are labelled as such. They check facts, not shape.
   - The renames done by script left nothing stray: no `PersonPerson…` and no renamed enum.
     The tree is clean apart from the linked `var`.

### Strengths
- The definer function is small, schema-qualified, and mirrors the existing ownership
  policy instead of inventing one.
- Spans are stored as offsets plus the text's hash, never as advert text. A hash mismatch is
  an internal error, never "no spans".
- A pasted body that can't be read is an internal error, never a missing example (Global
  Constraint 6).
- `usual_in_role` really is absent, never empty, and the schema says so.
- Every course outcome has its own reviewed row and its own reason. A mapping that changes
  in a later pack fails the test until it is reviewed again.

### Issues

#### Critical
None.

#### Important
- **I1 — lost input: the span offsets don't say their unit.**
  `backend/src/careerwright/capability/adverts.py:24-30` (the generated client's
  `AdvertSpan`) says only "character offsets". The server counts in Python code points; a
  browser's selection offsets count in UTF-16 units. In any advert with a character outside
  the Basic Multilingual Plane (emoji, or the "𝗕𝗼𝗹𝗱" letters LinkedIn adverts often use),
  10B's naive offsets would store different words from the ones the person chose. The
  server would accept them, because they are still inside the text, and read them back as
  different words. Fix: state the unit in the field descriptions (Unicode code points), and
  add one domain test with an astral character so 10B converts. Or accept UTF-16 offsets
  and convert on the server. One line plus one test.

#### Minor (list: final review or 10B)
- **M1 — test gap on a security property.** `tests/integration/test_skills.py:256` checks
  the owner and another actor, but not a fetched body (`route = 'fetch'`) or a revoked
  actor. Both are refused by reading the SQL, and the implementer's local check is
  unverified. Add both cases when the controller next touches this file.
- **M2 — matching question for the product owner: entry facts by whole words.**
  `skills.py:183` (`names`). The concept key of "A levels" is `a level`, so it sits beside a
  requirement such as "a level of fitness" or "a level of English". These are display-only
  facts that never feed readiness. 10B's words for `achieved_stated` must not read as "met".
- **M3 — weak target-level assertion.** `tests/domain/test_course_outcomes_review.py:184`.
  `after.state not in READY` can't fail, because every levelled row is seeded below its
  level. The row-level assertions carry the test. A version with only the course's row
  short would test the target.
- **M4 — key spaces.** Examples are keyed by `evidence.jobs.title_key`, with no plural
  folding. Marks and records use `concept_key`. An example pasted under "Data analysts"
  doesn't show under the target "Data analyst". Paste has always behaved this way, and 10B
  should paste with the target's exact title.
- **M5 — process.** Code came before most domain tests (not TDD). Two renames were done by
  script against the Edit/Write rule. Both are disclosed, and I checked they are clean.
- **M6 — two profile reads.** `skills_view` reads the profile twice under READ COMMITTED,
  and a profile save between them could pair marks with older matrices. This needs a race,
  and the result is display only.

### Questions
- **Q1 (for the product owner, R14):** "Should Skills show readiness worked out on rubrics
  that session 2 hasn't approved yet, labelled as not yet reviewed? Yes shows P05's 'apply
  now' in Skills again. No keeps 'not assessed yet' until the rubrics are reviewed."
- **Q2 (for the controller):** the carry-forward to Task 10 pins pack and reference 0.2.0,
  but 10A leaves the app on 0.1.0 (`capability/commands.py:75`; report ruling 6). So Skills
  shows rows whose values session 2 corrected, all labelled `proposed`. That is
  fail-safe, but it is out of date. Either rule which task moves the pin, or move it before
  10B.

### Assessment
**Task quality:** Needs fixes (I1 only).
**Reasoning:** The risky parts are correct and narrow: the definer function, readiness that
never leaks, absent-not-empty, and expected-never-met. The one fix stops 10B storing words
the person didn't choose. The strict readiness reading is a defensible fail-safe that
needs the product owner's answer.
