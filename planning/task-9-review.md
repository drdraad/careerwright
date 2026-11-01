# Task 9 review: capability model, protected gates and outcomes (4516de8..23d081b)

Reviewer: one task reviewer, read-only, no subagents, no live calls; `.env` and NESSA_HOME not
read. I read the brief, the dispatch, the report, then the whole 6,685-line package in five
passes (API and commands; evidence, matrix and outcomes; questions and readiness; reference,
store and migration; tests, ADR and register). I did not re-run the implementer's suites. Four
focused domain probes (pure functions, no database, no network) settled the doubts the code
raised. They are in
`/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/t9/`
(`probe_ready.py`, `probe_answers.py`, `probe_answers2.py`, `probe_conditional.py`), run with
`cd backend && uv run --locked python <probe>`. The working tree stayed clean.

### Spec Compliance

- ❌ Issues found:
  - **A target with no modelled requirements reads "ready now", and the product's own way of
    choosing a target loses the protected gate.** This is Critical C1.
    - Where: `backend/src/nessa/capability/commands.py:122`,
      `backend/src/nessa/capability/readiness.py:303-308`.
    - Why it fails the spec: RDY-1 ("Unknown does not pass"), spec section 8 ("the system
      cannot declare a regulated role attainable…"; "Unsupported roles … cannot receive a
      falsely definitive regulated-career plan"), the card's "protects regulated gates" and
      Global Constraint 6.
  - **"Not ready" is shown where the truth is "not yet assessed" (concern 5).** OUT-1's
    "partial sketch" has no representation in a readiness result (I1).
  - **The five interview answers are not distinguished in what is derived from them.** This
    misses spec section 9's interview pattern (I2).
  - **The pack's date and each record's review state do not reach every derived result**
    (R9, named risk 4; I4).
- Accepted by controller ruling and recorded honestly:
  - **MAP1-01 is partly met.** Requirement rows are not read from the person's examples
    (`exemplar_rows_read: false`). The register row stays `planned` with "T9 part verified"
    and an "Open:" clause that names the missing piece (`docs/requirements-register.md:172`).
    It does not name Task 10 as the owner or the confirmation requirement from the ruling
    (M2).
  - **Outcome accept and override persistence** is Task 12's (ADR 0012 decision 11).
  - **The capability reference is not in the session 2 package.** Task 11 adds it (ADR
    0012, consequences).
- ⚠️ Cannot verify from diff:
  - the `make check` and `make acceptance` results, and the RED logs in the implementer's
    scratchpad;
  - `test_every_crosswalk_names_an_esco_concept_of_the_full_pinned_release`, which needs the
    fetched ESCO release;
  - the domain review of the capability reference: correctly recorded as "not run — requires
    human".

  For the generated client, I compared the two OpenAPI documents myself:
  - no schema or path was removed;
  - 7 paths were added;
  - `ErrorCode` gained `PROTECTED_GATE`, `ErrorStage` gained `capability` and `EventKind`
    gained `capability.updated`, with nothing removed from any of the three.

**Named risks, one focused check each**

1. **Protected gates.**
   - What holds:
     - Gates are typed in the pinned reference (`legal_practice`, `eligibility`).
     - `check_edit` refuses any non-essential importance on a gate (`PROTECTED_GATE`, 409,
       before any write; `matrix.py:760-778`), and `_edited` ignores a stored demotion
       (`matrix.py:740-741`).
     - The challenge path (`commands.py:439-448`, `matrix.py:732-739`) only appends a
       `Challenge` and the `challenged` uncertainty. Nothing in readiness or questions reads
       it, so a challenge never weakens the gate.
     - No chat path reaches these commands yet.
   - **Fails on "a new target version":** see C1. Choosing a nursing occupation from the
     slate gives a target with no gate, and readiness reads ready now.
2. **No adding into competence.**
   - Holds:
     - Planned levels and demonstrated levels both take the maximum (`outcomes.py:292-313`,
       `evidence.py:164-166`).
     - Topic mention and practice give a null level (validator at `outcomes.py:135-157`).
     - An `unsupported` provider claim has no level.
     - A completed offering never changes `RowAssessment.evidence`.
   - Caveat: a reviewed demonstration below a concrete self-report lowers the current level
     (M4).
3. **Unknown is never level 0, never ready and never ineligible.**
   - Holds: unknown is never level 0 (`no_usable_evidence` against level 0's
     `below_required`), and nothing ever finds a person ineligible.
   - Fails on "never ready": C1.
   - Self-report against demonstration is nominal when the person enters both (I3).
   - Recency is carried; confirmation holds by construction (every write is the person's
     own).
   - ESCO-only rows are unknown.
   - No percentage appears anywhere: I searched for "percent", "employab", "probabil" and
     "score".
4. **Proposed records and labelling.**
   - Holds:
     - `PROVISIONAL_MATRIX` is always present, so no result is unqualified.
     - Pack rows are never counted as exemplars (`coverage.exemplars` counts only the
       person's pasted examples).
     - Nothing claims a full-description employer sample.
   - Fails: per-record review state and the pack date are missing from parts of the
     readiness and question results (I4).
5. **Versioning.**
   - `definition_version` digests the required rows' ID, kind, level, rubric and gate kind
     (`matrix.py:687-708`).
   - The tests prove each claim, not just call it:
     - an essential→preferred edit changes `definition_version` and `ensure_current` raises
       `STALE_INPUT_VERSION`;
     - an edit outside the definition keeps it;
     - the evidence-change test compares the full gap sets before and after, in the domain
       and through the API.
   - Ranks do not exist yet. The report says so and hands the rank keying to Task 11 and
     Task 13a.
6. **The question graph.**
   - Requirements and gates sort first (`questions.py:165-168`).
   - `INITIAL_PROMPTS`, `ENOUGH_COVERED/ENOUGH_OF`, `IMPORTANCE_WEIGHT`, `UNCERTAINTY_WEIGHT`
     and `QUESTION_BURDEN` are named constants. Holds.
   - Caveat: "enough" is reached vacuously for an unmodelled target (C1).
7. **Persistence and API.**
   - Migration 0029 is forward-only (`downgrade` raises).
   - CHECKs constrain every state column (answer, method, holding, action, importance,
     levels, month pattern) and the cross-column rules.
   - RLS is enabled with the existing `workspace_id IN (SELECT … nessa.workspaces)` policy
     on all four tables.
   - Grants are least privilege: SELECT and INSERT, plus a column-limited UPDATE on
     `capability_states`; no worker grant.
   - All four writes go through `run_idempotent` with an expected version and an
     `Idempotency-Key`.
   - Errors are `NessaError` codes whose details hold identifiers only.
   - Receipts are versions and IDs, never model output.
   - `PROTECTED_GATE` has its words and tone in `vocabulary.ts`.
   - Holds.
8. **The capability reference.**
   - Pinned by SHA-256: I recomputed it and it matches `906b4e96…`.
   - It is loaded with `load_pack("0.1.0")` and checked against the pack, including the
     Task 7b M3 references.
   - `funding_instruments.source_ids` is left to Task 11, as the report says.
   - The pack file and its pin are untouched: no commit in the range touches
     `catalogue/packs`.
   - Holds.
9. **The demo workspace.**
   - P01's typed target "Data quality analyst" gets the real pack matrix. The matrix is
     labelled with the pack's date and review states and carries no fixture content.
   - No capability data is seeded and nothing fills a live field.
   - Minor: derived results do not carry the workspace's synthetic label (M8).
10. **The module boundary.**
    - `nessa/capability` holds no empty layers.
    - Only `capability.store` imports SQL, and it is listed in `test_boundaries.py`.
    - Identity does not import capability.
    - There is no new run kind, no model call, and no change to `worker.py` or the DBOS
      `application_version`.
    - CLAUDE.md is not edited: the wording is proposed in the report, as ruled.
    - Holds.

### Strengths

- **Clean, pure domain modules.**
  - Matrix, evidence, outcomes, readiness and questions are pure and deterministic.
  - SQL is confined to one listed adapter.
  - Nothing derived is stored: every read recomputes from versioned inputs.
- **Typed gates, two layers of defence.** Gate typing lives in pinned data, not in code
  heuristics. The command refuses a demotion, and a stored demotion is ignored if it ever
  exists.
- **OUT-1 rules live in the record's own validator.** A level needs an assessed kind and
  the row's rubric, credential outcomes never carry a level, and an override is never
  `reviewed`. So these rules bind every future proposer, not only today's loader.
- **Readiness keeps its findings apart.**
  - Blocker kinds stay distinct: below the required level, no usable evidence, not
    modelled, not held, unresolved, and a pathway outside the model.
  - `MODEL_SCOPE_EXCEEDED` sits beside `not_held`, never in place of it.
  - C03's misleading "Adult Nursing" never addresses the gate.
- **Real behaviour is tested on real data.**
  - Most tests run on the frozen pack's own records (C01/C04, C06, C08, J05–J20) and on the
    M0 fixtures' own expected values (P04's requested edit, P05's `expected` block).
  - Integration tests check RLS as the API role and append-only grants.
- **An honest report.**
  - It discloses the horizontal test-first order and the `ruff --unsafe-fixes` use.
  - It lists its R12 items for the final review.
  - It records the human gate as "not run — requires human".

### Issues

#### Critical

**C1. A target with no modelled requirements is "ready now", and choosing a nursing
occupation from the slate gives a regulated target with no protected gate.**

- **Where:** `backend/src/nessa/capability/commands.py:122`,
  `backend/src/nessa/capability/readiness.py:303-308`,
  `backend/src/nessa/capability/questions.py:169`.
- **What:**
  - A target's pack target is found only by exact folded title (`commands.py:122`).
  - Gates come only from pack postings and pack rows (`matrix.py` `_PackRows`).
  - ESCO-only rows are unknown and never required.
  - So any target that is not one of the four pack titles has zero required rows. `assess`
    then has no blockers and returns `ready_now_for_modelled_requirements` with
    `review_current_postings_and_apply`, no route chart, and only `provisional_matrix` as a
    qualification (`readiness.py:303-308`).
  - The question graph reports `enough` with zero prompts (`questions.py:169`).
  - The matrix already carries `sources.occupation.regulated`, but nothing reads it.
- **Reproduced:** `probe_ready.py`.
  - "Adult nurse" with an ESCO seed marked `regulated: True`, no evidence and no statements
    gives `state: ready_now_for_modelled_requirements`, `actions:
    ['review_postings_and_apply']`, questions `enough` and 0 prompts.
  - "Marine biologist" with no seed gives the same.
- **This is the main path, not an edge case:**
  - Choosing an occupation from the slate or from ESCO search stores the ESCO preferred
    label as the target (`backend/src/nessa/profile/exploration.py:839`). For nursing that
    is "nurse responsible for general care", which is not "Registered nurse".
  - The reference crosswalks `registered-nurse-manchester` to exactly that occupation, but
    `_matrix` never looks a pack target up by its crosswalked occupation.
  - So P04-like users who choose their target in the product get no NMC gate and an
    apply-now lead.
- **Why it matters:**
  - It breaks named risks 1 (the "new target version" path) and 3 (unknown is never ready),
    and RDY-1 ("Unknown does not pass").
  - It breaks spec section 8: "the system cannot declare a regulated role attainable…", and
    "Unsupported roles remain explorable but cannot receive a falsely definitive
    regulated-career plan".
  - It breaks the Sprint 4 card ("protects regulated gates") and Global Constraint 6
    (unknown presented as complete).
  - The existing test `test_a_target_with_no_pack_target_and_no_seed_has_no_rows_and_says_why`
    (`backend/tests/domain/test_capability_matrix.py:349`) builds exactly this matrix and
    never assesses it.
- **Fix:**
  - (a) Readiness is never `ready_now` when the target definition has no modelled required
    row. Give it its own state, for example `not_assessable` or `insufficient_coverage`,
    with a blocker naming the not-modelled coverage. Make questions `enough` require at
    least one modelled row or gate.
  - (b) Also find a pack target whose reference crosswalk names the target's ESCO
    occupation, so the slate's label reaches the pack's rows and gates.
  - (c) Make a `regulated: true` occupation with no typed gate an unresolved protected-gate
    blocker ("registration requirement not yet modelled"), never silence.
  - Add a domain test and an API test for a slate-chosen nursing label.

#### Important

**I1. "Not ready" is shown where the truth is "not yet assessed", and a conditional scenario
on a null-level outcome gives no partial sketch (concern 5).**

- **Where:** `backend/src/nessa/capability/readiness.py:94-97`, `:303-308`.
- **What:**
  - `ReadinessState` has only `ready_now…`, `conditional…` and `not_ready`.
  - A person who has answered nothing gets `not_ready`, with `no_usable_evidence` and
    `unresolved` blockers. The test asserts this outright
    (`backend/tests/domain/test_capability_readiness.py:112`).
  - In a conditional scenario on a pack option whose level is null only because it is not
    yet assessed, the result is identical to the current scenario: `not_ready`,
    `below_required`, with no qualification or marker for the missing outcome level.
    `probe_conditional.py` shows this with C06, an exam outcome, `provisional`, level null,
    accepted and completed. Only the per-candidate `numeric_use:
    "excluded_missing_level"` says so.
- **Why it matters:**
  - The controller asked that no surface show "not ready" where the truth is "not yet
    assessed".
  - OUT-1 says missing critical outcome levels "leave a partial sketch".
  - Global Constraint 6 says unknown states stay distinct from results.
  - With pack 0.1.0, every pack-based conditional result is in this case until Task 7c.
- **Fix:**
  - Add a state such as `not_yet_assessed` when every mandatory blocker is
    `no_usable_evidence`, `unresolved` or `not_modelled`. Keep `not_ready` for
    `below_required`, `not_held` and `pathway_outside_model`.
  - Add a `partial_sketch` flag or qualification, for example `missing_outcome_level`, on
    any conditional result where a completed offering maps to a required row with a null
    level.
  - Update the test at line 112 to assert the new state, not `not_ready`.

**I2. The interview answers carry no meaning in what is derived.**

- **Where:** `backend/src/nessa/capability/evidence.py:97-110`, `:151-194`;
  `backend/src/nessa/capability/readiness.py:374-387`;
  `backend/src/nessa/capability/questions.py:210-221`.
- **What:** `row_evidence` and readiness never read `answer`. `SkillEvidence._consistent`
  checks only that `unsure` has no level. Shown by `probe_answers.py` and
  `probe_answers2.py`:
  - "I have not learned this" or "I understand it but have not tried" without a level is
    indistinguishable from no answer. The row is `no_usable_evidence` with an `information`
    ("verify") gap, never `learn`, and the same question is asked again with reason
    `no_evidence`, as if unanswered.
  - "I am unsure" is likewise re-asked as `no_evidence`, though spec section 9 lets the
    person mark it unresolved.
  - An answer contradicting its level is accepted and counts. For example, `not_learned`
    with `self_assessed_level: 4`, an example and a month gives `met`, and the result is
    ready now.
- **Why it matters:**
  - Spec section 9 requires the five answers to be distinguished ("I have done it
    independently" … "I am unsure").
  - The question budget should not re-ask what was answered.
  - A validated command should not commit a self-contradictory record that then passes
    readiness (Global Constraint 1: validated commands commit).
- **Fix:**
  - Validate answer against level. `not_learned` and `understand_not_tried` take level 0 or
    no level; `done_with_help` cannot exceed level 1 under the spec's anchors, or at least
    cannot claim an independent level. Refuse other combinations with `VALIDATION_FAILED`
    / `inconsistent_evidence`.
  - Map `not_learned` and `understand_not_tried` to a known level-0 finding (gap `learn`,
    not re-asked).
  - Map `unsure` to an unresolved assumption (not re-asked, listed in `unresolved`), as
    gates already do with "don't know".

**I3. A person's own entry of a demonstration or a gate verification is presented as
corroborated, with no qualification.**

- **Where:** `backend/src/nessa/capability/evidence.py:159`, `:172-173`;
  `backend/src/nessa/capability/readiness.py:412-415`, `:534-553`.
- **What:**
  - In L0 the person alone enters `method: work_sample` or `assessment`,
    `demonstrated_level`, `assessed_by` and `reviewed_on`. ADR 0012 decision 6 records the
    review as "the person's confirmation".
  - Such a record becomes `basis: "demonstrated"` and `confidence: "corroborated"`, and the
    result loses `self_reported_evidence`. `probe_answers.py` shows a self-entered work
    sample at level 3 giving `corroborated` and ready now with only the provisional and
    proposed qualifications.
  - A gate the person marks `verified: true` is `satisfied` (ADR decision 4), and nothing
    in the result says the verification is the person's own statement.
- **Why it matters:**
  - Named risk 3: self-report and demonstration must stay distinct.
  - "Corroborated" claims an external check that L0 does not have.
  - Spec section 9 says an unsupported claim "remains self-reported".
  - Both decisions are disclosed as R6. But the result itself hides them, which is what
    OPTN-09 and R9's qualification model exists to prevent.
- **Fix:**
  - Until a reviewer exists, give a person-entered demonstration `provisional`
    confidence, or add a qualification such as `person_confirmed_demonstration`.
  - Add `person_confirmed_verification` whenever a protected gate is satisfied only by the
    person's statement.
  - Assert both in the P04 and P05 tests.
  - The product owner may still confirm the R6 decisions. The labels must say what they
    rest on either way.

**I4. The pack's date and each record's review state do not reach every derived result
(R9, named risk 4).**

- **Where:** `backend/src/nessa/api/capability_schemas.py:70-73`;
  `backend/src/nessa/capability/questions.py:76-85`;
  `backend/src/nessa/capability/readiness.py:151-196`.
- **What:**
  - `QuestionsOut` has no `PackLabel` and no `ReferenceLabel`, though its prompts show pack
    row labels and the proposed reference's anchors. `PromptRow` has no `review_state`.
  - In `ReadinessOut`, `RowAssessment` and `Gap` carry no `review_state`, and
    `CandidateOption` carries `review_state` but not the outcome's `as_of` date.
  - The only per-record review state is in `/matrices`. Readiness has only the aggregate
    `proposed_records` qualification.
- **Why it matters:**
  - R9 says every surface using the pack "shows the pack's date and each record's review
    state".
  - The Skills chapter (Task 10) renders prompts and gaps from these responses.
  - The named risk asks that this reach every derived result, not a separate join.
- **Fix:**
  - Add `pack` and `reference` labels to `QuestionsOut`.
  - Add `review_state` to `PromptRow`, `RowAssessment` and `Gap`, copied from the matrix
    row.
  - Add `as_of` to `CandidateOption`.
  - Assert them in the integration tests, then regenerate the client.

#### Minor

- **M1. The report's OpenAPI line is wrong** (`task-9-report.md:96`). It says "0 schemas
  removed or changed except `EventKind`", but `ErrorCode` (+`PROTECTED_GATE`) and
  `ErrorStage` (+`capability`) also changed. Both changes are additive. Correct the line.
- **M2. The MAP1-01 register row** (`docs/requirements-register.md:172`) says what is
  missing. It does not say that Task 10's Skills chapter owns reading the examples, or that
  extracted rows need the person's confirmation (the controller's ruling on concern 1). Add
  both to its "Open:" clause.
- **M3. A row set back to essential keeps the `relaxed_by_person` uncertainty**
  (`backend/src/nessa/capability/matrix.py:730-747`). `_edited` starts from the
  already-edited row's uncertainty set. Clear `RELAXED_BY_PERSON` when the new importance
  is required.
- **M4. A reviewed demonstration below a concrete self-report lowers the current level**
  (`backend/src/nessa/capability/evidence.py:172-173`). In `probe_answers2.py`, a
  self-report of 3 and a reviewed course assessment of 1 give level 1 with `conflict:
  true`. An introductory course's assessment shows "at least 1", not "at most 1".
  `conflict` triggers a clarification, so this is a provisional R6 item for the final
  review, not a defect today.
- **M5. A test name claims more than it checks:**
  `test_a_target_with_no_pack_target_and_no_seed_has_no_rows_and_says_why`
  (`backend/tests/domain/test_capability_matrix.py:349`). It passes no `occupation_note`,
  so it never checks the "why". Assert the note, and assert readiness (see C1).
- **M6. `_seed`'s `release is None` branch is unreachable**
  (`backend/src/nessa/capability/commands.py:144-145`). `held_release` raises
  `TAXONOMY_UNAVAILABLE` instead of returning `None`, and `_matrix` runs only when there
  are targets. Remove it, or type `release` as non-optional.
- **M7. `pack_matrix` is repeated in three test files**
  (`tests/domain/test_capability_questions.py:24`, `test_capability_readiness.py:64`, and
  `test_capability_matrix.py` as `matrix_for`). Already on the report's final-review list:
  move it to `tests/support/capability.py`.
- **M8. Capability results do not carry the workspace's synthetic or data-mode label.** In
  the P01 fixture workspace, a readiness result over the synthetic persona's targets says
  `synthetic: false`, because `Assessment.synthetic` copies only the matrix's flag. The
  workspace itself is labelled "P01 demo (synthetic)". Final-review item: carry the
  workspace label on capability responses.

### Assessment

**Spec compliance:** ❌ Issues found.
**Task quality:** Needs fixes.
**Reasoning:** The gate mechanics, OUT-1 rules, versioning and persistence are solid and
well tested. But readiness reads "ready now" for any target outside the four pack titles,
and that includes the nursing label the product itself stores when a person chooses an
occupation. So a regulated role reaches apply-now with no gate and no evidence (C1). Unknown
also shows as "not ready", the interview answers are not used, and person-entered
corroboration and the pack labels are incomplete in results (I1–I4). All of these must be
fixed before Task 11 builds on the readiness contract.

Counts: Critical 1, Important 4, Minor 8.
