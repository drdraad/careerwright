# Task 9 report: capability model, protected gates and outcomes (S4.1–S4.6 backend)

BASE 4516de8, final candidate 23d081b, branch `l0-local-release`. Nothing pushed, merged or
tagged. No live call (no page fetch, Adzuna or Meta). `.env` and NESSA_HOME were not read.
Pack 0.1.0 and its pin are unchanged. No subagent was used.

## Status

DONE_WITH_CONCERNS. The domain, persistence and API for S4.1–S4.6 are in place and tested,
including all six tests the brief names. The concerns are scope cuts and provisional
decisions the controller should rule on (see "Concerns"), chiefly that requirement rows are
not yet read from the person's own examples.

## Commits

| Commit | What |
|---|---|
| 09e820b | The capability reference: rubrics (anchors 0–4, required level, proof, ESCO skill crosswalk) for the 8 pack skill rows, 2 typed gates, 4 target→ESCO occupation crosswalks; pinned JSON; loader checks it against the pack, plus the pack references Task 7b's validator leaves (M3) |
| 0c8d690 | Versioned provisional matrices (pack rows, gates, one posting's own rows, ESCO seed rows), prevalence over vacancies, derived importance, protected gates (`PROTECTED_GATE`), warning to relax, edits with old/new versions; web vocabulary words for the new code; client regenerated |
| 43c668c | Evidence, OUT-1 outcomes, readiness (current and conditional), gaps, abstract actions, apply-now, qualifications |
| bbee032 | The combined question graph |
| b8fc015 | Migration 0029, `capability.store`, `capability.commands`, seven endpoints, `capability.updated` event; client regenerated (additive) |
| 96b9696 | Tests: challenging a gate's source (domain and API); every crosswalk against the full ESCO release |
| 684042e | Test: the person's examples count for their target, never as postings |
| 23d081b | ADR 0012; requirements register rows |

## Acceptance criteria and their state

From the brief's Task 9 section and the Sprint 4 card's backend acceptance.

| Criterion | State | Evidence |
|---|---|---|
| Versioned provisional matrices from ESCO + up to three permitted full-text exemplars per target; labelled provisional; snippet/full-text coverage; essential/preferred/disputed/unknown distinct | **Partly met** | ESCO seed, pack rows, labels, counts, versions: met (`test_capability_matrix.py`, `test_capability.py`). The person's examples are **counted only**: their requirement rows are not read (`exemplar_rows_read: false`). Concern 1 |
| Pack job-board rows enter as pack rows with claim, source, date and review state, never as exemplars or a full-description sample (ruling 1) | Met | `test_a_matrix_is_labelled_provisional_with_its_sources_counts_and_date`, `test_the_person_s_own_examples_are_counted_for_their_target_and_never_as_postings` |
| Behaviourally anchored levels; unknown ≠ 0; self-report vs demonstration; recency; confirmation; evidence shared across targets without assuming the same rubric | Met | `test_capability_reference.py`, `test_capability_readiness.py` (unknown vs 0, unsupported claim, AI assistance, shared evidence across rubrics). Confirmation: a recorded answer is the person's own write; chat proposals reach it through the same command (T10) |
| Combined question graph, gate-first, decision-impact heuristic, 8–12 prompts, pause/stop, coverage without a percentage | Met (backend) | `test_capability_questions.py` (7), `test_questions_ask_gates_first_and_can_be_stopped_and_resumed` |
| Typed immutable protected gates (legal practice, recognition, admission, eligibility); challenge or change target; no toggle removes one | Met | `test_a_protected_gate_cannot_be_demoted`, `test_challenging_a_gate_s_source_records_the_challenge_and_keeps_the_gate`, `test_the_registration_gate_cannot_be_demoted_through_the_api`, `test_a_gate_s_source_can_be_challenged_and_the_gate_stays` |
| OUT-1 row mappings from syllabus/assessment spans to observable tasks; topic mention vs practice vs assessed demonstration; user acceptance is an assumption | Met (domain) | `test_a_pack_outcome_carries_the_out_1_record`, `test_an_unsupported_outcome_level_stays_null_and_leaves_a_partial_sketch`, `test_a_user_override_is_an_assumption_never_a_provider_claim`. Storing accept/override decisions is left to the checkpoint (T12). Concern 4 |
| Gap classification and abstract action graph | Met | `test_gaps_are_classified_and_work_rights_never_get_a_course`, `test_no_course_is_offered_before_the_person_has_said_where_they_are` |
| P05 apply-now path ahead of course recommendations | Met (backend) | `test_p05_leads_with_apply_now_and_no_forced_training` (P05's own expected values), `test_apply_now_on_the_pack_is_qualified_and_lists_employer_checks` |
| Target/matrix version on all derived results | Met | `test_results_carry_their_versions_and_an_essential_edit_makes_them_stale`, the question graph's `targets`, API responses |
| Test: P04 cannot become ready by demoting registration | **Met** | `test_p04_cannot_become_ready_by_demoting_registration` (P04's own requested edit), API test |
| Test: an unresolved gate and an out-of-model pathway stay distinct from ineligibility | **Met** | `test_a_registration_pathway_longer_than_the_model_is_outside_it_not_impossible` (C08, 36 months, `MODEL_SCOPE_EXCEEDED`), API test |
| Test: two introductory courses cannot add into competence | **Met** | `test_two_introductory_courses_never_add_up_to_competence`, `test_topic_mentions_and_practice_in_the_pack_add_no_level_even_together` |
| Test: enrolment/completion never overwrites current evidence | **Met** | `test_enrolment_or_completion_never_overwrites_current_evidence` (TRACE01-06) |
| Test: unsupported outcome level stays null | **Met** | `test_an_unsupported_outcome_level_stays_null_and_leaves_a_partial_sketch` |
| Test: evidence changes recompute only affected gaps | **Met** | `test_an_evidence_change_recomputes_only_the_gaps_it_affects`, and through the API |
| Test: changing an essential non-protected row creates a new target definition and invalidates earlier ranks | **Met for derived results** | `test_changing_an_essential_row_creates_a_new_target_definition_and_keeps_its_history`, `test_results_carry_their_versions_...`, API test. Ranks do not exist yet: T11/T13a must key them by `definition_version` |
| A `proposed` record never supports an unqualified readiness result (OPTN-09, R9) | Met | every result names its qualifications; `test_only_reviewed_records_lift_the_proposed_qualification` |
| Pack references checked at load (ruling 4, Task 7b M3) | Met | `test_the_loader_checks_the_pack_references_it_relies_on`. **Ledger pointer:** Task 7b M3 is now covered for the fields the capability loader reads (`learning_options.target_ids`, `skills.target_id`, a requirement's `target_id` against its posting's, `job_postings.source_id`, `learning_options.source_id`); `funding_instruments.source_ids` is not read here and stays Task 11's |
| Human gates | **not run — requires human** | the capability reference's domain review (rubrics, required levels, crosswalks, gate types); the Sprint 4 design review and live scoring are T10's |

## Decisions

All in ADR 0012. Those marked R6 are provisional and need product owner confirmation.

1. Module `nessa/capability` (dispatch ruling 2), SQL only in `capability.store` (listed in
   `tests/architecture/test_boundaries.py`).
2. A pinned capability reference beside the module carries the rubrics, crosswalks and gate
   types; everything in it is `proposed`. Required level 2 for every row (entry-level
   postings).
3. **(R6)** Importance comes from the postings: all essential is essential, all preferred is
   preferred, a mix is disputed, none is unknown. ESCO-only rows are unknown and not
   modelled, so they never enter readiness (otherwise a nurse target needs evidence on 92
   ESCO rows). One posting's own requirement is unknown for the target and listed as that
   posting's check. **A disputed row counts as required** until the person relaxes it.
   On pack 0.1.0 this makes P01's SQL and communication rows disputed (J12 prefers them).
4. **(R6)** A protected gate is satisfied only when held and verified at its source, as the
   person's confirmation. New error code `PROTECTED_GATE` (409); a challenge records the
   reason and keeps the gate; relaxing an employer's requirement needs the warning
   (`CONFIRMATION_REQUIRED`).
5. **(R6)** Counts towards readiness: a reviewed demonstration's level, else the latest
   self-report with an example and a "last done" month; a level with no example is
   `unsupported` and counts for nothing.
6. **(R6)** An assessed completion counts once its review date is recorded, and in L0 that
   review is the person's own confirmation (no third-party reviewer exists).
7. Readiness never finds a person ineligible. Out of model means every supporting
   pathway's shortest stated duration is beyond 24 months. Options are offered only for
   learn, credential and experience gaps.
8. **(R6)** The question weights (3/2/1 importance, 4/3/2/0 uncertainty), the 80% stop and
   twelve initial prompts.
9. Versions: content digests `matrix_version` and `definition_version`, plus a workspace
   capability version for writes.
10. **(R6)** A target's pack target is the one with the same title (folded); its ESCO seed is
    the exact ESCO label, else the pack target's crosswalk.
11. **No run kind, no model call:** DBOS `application_version` does not change (no workflow
    step sequence changed). No spend scope added.

## Verification

| Command | Result |
|---|---|
| `make check` (on 23d081b) | exit 0: ruff format and lint clean, mypy clean (289 files), pytest **1358 passed**, 292 deselected (baseline 1305), fixture validator passed, client drift none, Biome clean, `tsc` clean, Vitest **212 passed** |
| `cd backend && uv run pytest tests/integration/test_capability.py -m integration` | 13 passed (during development; also inside `make acceptance`) |
| `make acceptance` (once, on 23d081b) | exit 0: integration and stack **292 passed** (baseline 279, 13 new) in 7 min 52 s; Storybook build passed; Playwright **28 passed** |
| OpenAPI before/after comparison | no schema or path removed; three existing enums changed, additively: `ErrorCode` (+`PROTECTED_GATE`), `ErrorStage` (+`capability`), `EventKind` (+`capability.updated`); 60 schemas added; 7 paths added (corrected in fix round 1, review M1) |

## TDD evidence

RED runs are kept in the scratchpad (`tdd/*.log`).

- Each test file was written before its module and run first:
  - reference, matrix and readiness: `ModuleNotFoundError`;
  - question graph: collection error;
  - API: 404 from the missing route, an assertion failure.
- First GREEN runs:
  - reference 10/10 and matrix 14/14;
  - readiness 19/20, where the one failure was the test's own setup (it expected course
    candidates for an `information` gap), corrected and joined by a new test for that rule;
  - question graph 6/7, where the one failure was a real bug: a gate the person marked
    "don't know" was left out of `unresolved`, fixed in code;
  - API 10/10.
- Tests per module were written as one file, then the module. That is closer to
  "horizontal" than one test then one implementation; each module was small enough to
  review whole.
- Written after their code:
  - the domain challenge test, shown able to fail by temporarily mutating the challenge
    branch (RED logged), then restored;
  - the API challenge test;
  - the full-release crosswalk test;
  - the exemplar-count test.

## Not verified

- The domain review of the capability reference (rubrics, anchors, required levels,
  crosswalks, gate types): **not run — requires human**.
- Requirement rows from the person's own examples: not implemented (concern 1).
- Persisting outcome accept/override decisions: not implemented (T12's checkpoint).
- The live path (model proposals for outcome mappings or evidence answers): none exists;
  TEST1-13 is T10's.
- The Skills chapter UI, the apply-now and warning words, the design review: T10's.
- Ranks' invalidation: no ranks exist; only derived results are shown stale.

## Items for the final review (R12: not required by a failing check)

- `minimum_months` rounds weeks up to months; only the 24-month comparison uses it.
- `capability_view` rebuilds every target's matrix on each read and each write (at most 3
  targets; ESCO reads per target). Fine at L0 scale; a cache keyed by the inputs' versions
  would be the next step if it is ever slow.
- An ESCO-only row (no rubric) can take an example-only answer, never a level.
- `_ordered` would place a pack row with no mapped requirement among the ESCO rows (none in
  0.1.0).
- The `pack_matrix` test helper is repeated in three test files.
- The demo (P01) workspace shows the real pack's "Data quality analyst" matrix, as it shows
  real ESCO data, rather than TRACE-01's synthetic matrix; Task 10 may prefer the synthetic
  one there.

## Concerns

1. **The person's examples are counted, not read (MAP1-01 partial).** The brief asks for
   matrices from "ESCO + up to three permitted full-text exemplars per target". Reading an
   example's requirements needs a model proposal over the sealed text (a new `RunTask`) or the
   person's own selection of spans with an endpoint that shows the text; neither exists. I
   proposed that Task 10 own it with the Skills chapter. The controller should rule.
2. **Provisional decisions 3–6, 8, 10 (R6)** change what readiness means. The most
   consequential: ESCO-only rows are not modelled; disputed rows count as required; a
   self-report with an example counts; gate verification and assessment review are the
   person's own confirmation.
3. **Session 2's package** (generated from the pack by Task 7b's tool) does not ask about the
   capability reference. Its rubrics, required levels, crosswalks and gate types need the same
   H-07-style review; I propose Task 11 adds them to the package.
4. **Outcome decisions** (accept, reject, override) are domain functions only: no table, no
   endpoint. The checkpoint (T12) owns their acceptance (OUT1-11).
5. **Pack 0.1.0's outcome levels are all null**, so every pack option is excluded from a
   numeric readiness solve. Task 11's real option set on P01's target can check finances,
   but its readiness stays a partial sketch until Task 7c's reviewed version or an accepted
   assumption gives a level.
6. **Two small changes outside the backend:** the new code's words in
   `apps/web/src/lib/vocabulary.ts` (required by its exhaustive `Record<ErrorCode, …>`), and
   the regenerated client.
7. **Tool use, for transparency:**
   - I ran `ruff check --fix --unsafe-fixes` for two rules (import order, splitting
     `assert a and b`) on my new files, and inspected the result.
   - One read-only `python3 -` heredoc checked the register's cited test names. It changed no
     file.

## Proposed CLAUDE.md wording

Under "Layout", after the `nessa/catalogue` entry:

> `nessa/capability` (capability assessment: the pinned capability reference with rubrics,
> ESCO crosswalks and gate types; matrices, evidence, protected gates, OUT-1 outcomes,
> readiness, gaps and the question graph; `capability.store` is its only SQL),

Under "Non-obvious invariants", a new bullet:

> - Capability (ADR 0012): a protected gate (legal practice, recognition, admission,
>   eligibility) is always required and never demoted (`PROTECTED_GATE`); held but unverified
>   is unresolved, and nothing finds a person ineligible. A level counts only against the
>   rubric it was chosen for; unknown is never level 0; ordinal levels take the maximum, never
>   a sum. A planned outcome counts only in a conditional scenario and never changes current
>   evidence; credential outcomes lead only to eligibility to apply. Every L0 readiness
>   result is qualified (provisional matrix, proposed records), and every derived result
>   carries its `matrix_version` and `definition_version`.

---

## Fix round 1

FIX_BASE 23d081b, final candidate dffd08c. This round follows the review (`task-9-review.md`)
and the controller's rulings (`task-9-fix-round-1.md`). Nothing pushed. No live call; `.env`
and NESSA_HOME not read; pack 0.1.0 and its pin untouched; no subagent; CLAUDE.md not edited.

### Status

DONE_WITH_CONCERNS: every item ruled for fixing is fixed and tested; the concerns are below.

### Commits

| Commit | What |
|---|---|
| e52f44a | All code fixes: C1 (a, b, c), I1–I4, M3, M5, M6, M8; migration 0030; client regenerated |
| dffd08c | ADR 0012 (decisions 4, 5, 7, 8, 9, 10; M4 parked as R6) and the register (M2 and the round's tests) |

The code is one commit because the fixes change the same functions in `readiness.py`,
`questions.py`, `matrix.py` and `commands.py`, and hunks cannot be staged apart without
interactive staging. The commit message lists each item.

### Items

| Item | Fix | Tests |
|---|---|---|
| **C1(a)** | New state `insufficient_coverage`, never ready, when no required row or gate is modelled; blocker `no_modelled_requirements` (row ID null). Questions are `insufficient_coverage`, never "enough", with nothing modelled | `test_a_target_with_no_modelled_requirement_is_never_ready_now` ("Marine biologist"; "Data analyst" with ESCO seed rows only); `test_nothing_modelled_is_never_enough_and_an_unmodelled_regulation_is_listed`; API `test_an_unmodelled_target_or_a_regulated_one_without_a_typed_gate_is_never_ready_now` |
| **C1(b)** | `find_pack_target`: by title, else the one pack target whose crosswalk names the target's ESCO occupation (several: none). Recorded as `pack_target.basis` | `test_a_slate_chosen_nursing_label_reaches_the_pack_s_registration_gate`; API `test_a_nursing_occupation_chosen_in_the_product_keeps_the_registration_gate` (through `POST /targets`, the product's own choice path) |
| **C1(c)** | A regulated ESCO occupation with no typed practice gate gets the unmodelled protected gate `gate:occupation-regulation` (`modelled: false`): required, never demoted, not asked, listed unresolved, never satisfied; a statement on it is refused (`not_modelled`) | `test_a_regulated_occupation_with_no_typed_gate_has_an_unresolved_protected_gate`; API test on ESCO's "general practitioner" (regulated, in the sample) |
| **I1** | `not_yet_assessed` when only unknowns block; `not_ready` keeps known shortfalls. Qualification `missing_outcome_level` on a conditional scenario whose completed offering has an assessed, supported outcome with no level for a required row (not for a topic mention) | the READINESS-01 test now asserts `not_yet_assessed` for an unanswered person (`not_ready` for level 0); P04's unverified gate is `not_yet_assessed`; `test_a_conditional_scenario_on_an_outcome_with_no_level_is_a_partial_sketch` (C06 flagged, C02's topic mention not) |
| **I2** | Answer-level contradictions refused (`inconsistent_evidence`); not learned / understood-not-tried = known level 0 (learn gap, not re-asked); unsure = unresolved (listed, not re-asked); these answers hold under any rubric. "With help" ≤ 1, recorded R6 (see decisions). Migration 0030: the two CHECKs | `test_an_answer_that_contradicts_its_level_is_refused`, `test_not_learned_is_a_known_level_zero_and_is_not_asked_again` (both answers), `test_unsure_is_an_unresolved_assumption_and_is_not_asked_again`; API 422 for `not_learned` with level 3; `test_the_database_refuses_an_answer_that_contradicts_its_level` |
| **I3** | A demonstration is `provisional`, never `corroborated`; qualifications `person_confirmed_demonstration` and `person_confirmed_verification` | P05: `test_p05_with_a_work_sample_the_person_entered_is_never_corroborated`; P04: verified gate satisfied with `person_confirmed_verification` (in `test_p04_cannot_become_ready_by_demoting_registration`); pack bookkeeping apply-now test |
| **I4** | `QuestionsOut` gains `pack` and `reference`; `PromptRow`, `RowAssessment` and `Gap` gain `review_state`; `CandidateOption` gains `as_of`; `ReadinessOut` also gains `reference` | API `test_questions_and_readiness_carry_the_pack_labels_and_the_workspace_s_synthetic_label` |
| **M1** | The original report's OpenAPI line corrected (ErrorCode and ErrorStage changed too, additively) | — |
| **M2** | MAP1-01's open clause names T10's Skills chapter as owner and requires the person's confirmation of rows read from an example | — |
| **M3** | `relaxed_by_person` cleared when a row is set back to required | `test_a_row_set_back_to_required_is_no_longer_marked_relaxed` |
| **M5** | The no-row test passes and asserts its `occupation_note`, and asserts `insufficient_coverage` | `test_a_target_with_no_pack_target_and_no_seed_has_no_rows_and_says_why` |
| **M6** | `_seed`'s unreachable `release is None` branch removed; `release` is required | (covered by the API tests) |
| **M8** | Every capability response carries the workspace's `synthetic` and `data_mode`; a synthetic workspace's matrix (`build_matrix(..., synthetic=)` is now required), readiness and questions say `synthetic: true` | `test_a_synthetic_workspace_s_results_say_so`; the API labels test (synthetic and non-synthetic workspaces) |
| M4 | Parked: recorded in ADR 0012 decision 5 as a provisional R6 item for session 2's decision sheet and the final review | — |
| M7 | Parked (R12, final review) | — |

### Decisions

- **C1's state is not I1's.** `insufficient_coverage` (nothing modelled: no answer can
  settle it) and `not_yet_assessed` (only unknowns: answers settle it) differ in meaning,
  so they are separate states (ruling 2 asked me to say which).
- **The "with help" ceiling.** Spec section 8's anchors define level 1 as "performs with
  guidance" and levels 2 to 4 by independence. They do not state the cap in so many words,
  so the cap is applied and recorded as provisional R6 (ADR 0012 decision 5), per ruling 3.
- **Level-free answers** (unsure, not learned, understood-not-tried) apply to the subject
  under every target's rubric. Without this, an "unsure" sent without a rubric version
  would be re-asked as "another rubric's answer".
- **Migration 0030's CHECKs are `NOT VALID`.** 0029 accepted such answers, so a database
  that ran it may hold one. It is kept as written, never dropped. 0029 has run only on this
  branch's test databases.
- **The unmodelled gate refuses statements.** A statement could never satisfy it, so
  recording one would commit a meaningless record.

### Verification

| Command | Result |
|---|---|
| `make check` (on dffd08c) | exit 0: ruff, mypy (290 files), pytest **1370 passed** (from 1358), fixture validator, client drift none, Biome, `tsc`, Vitest **212 passed** |
| `uv run pytest tests/integration/test_capability.py -m integration` | 17 passed (from 13) |
| `make acceptance` (once, on dffd08c) | exit 0: integration and stack **296 passed** (from 292) in 7 min 51 s; Storybook build passed; Playwright **28 passed** |
| OpenAPI 23d081b → dffd08c | no schema or path removed. New fields: `as_of`, `review_state` (×3), `modelled` (×2), `basis`, `answer`, `synthetic`, `data_mode`, `pack`, `reference`. New enum values: `ReadinessState` +2, `Qualification` +3, `RowStatus` +1, `Uncertainty` +1, `QuestionGraph.state` +1. Three fields **widened to nullable**: `Blocker.row_id`, `GateInfo.issuing_body`, `GateInfo.verification`. No web code reads these yet |

### TDD evidence

RED logs in the scratchpad: `tdd/fr1-01-domain-red.log`, `fr1-02-behaviour-red.log`,
`fr1-03-api-red.log`.

- Every domain and API test of this round was written before its fix.
- **First run, domain:**
  - the readiness file failed to import `find_pack_target`;
  - in the matrix and questions files, 18 tests failed on the new required `synthetic`
    argument.
- **Behaviour-specific RED:** I added only that argument, then reran. Three tests failed
  for the behaviours under test:
  - the no-row target not reading `insufficient_coverage` (C1, M5);
  - `relaxed_by_person` surviving a restore (M3);
  - questions reporting `enough` with nothing modelled (C1).
- **API RED:** I stashed only `backend/src` (`git stash push -- backend/src`), ran the API
  suite against the old code, then popped it. Five new or changed tests failed: labels and
  synthetic, contradictory answer, nursing chosen in the product, unmodelled and regulated
  targets, and the matrices labels.
- **GREEN:** 65 domain tests after the domain fixes, then 17 API tests after the client was
  regenerated.
- **Written after its code:** `test_the_database_refuses_an_answer_that_contradicts_its_level`
  tests migration 0030. That file is untracked, so it stayed in place during the stash and
  the test passed in the API RED run.

### Not verified

- The reviewer's probe scripts were not re-run. They call `build_matrix` without the now
  required `synthetic`. Their cases are covered by the new tests.
- The domain review of the capability reference: **not run — requires human**, unchanged.

### Concerns

1. **Three fields widened to nullable** (`Blocker.row_id`, and `GateInfo.issuing_body` and
   `verification` for the unmodelled gate). They are additive for a reader that handles
   null. Task 10 is the first consumer.
2. **ESCO's `regulated` flag covers 16 occupations only.** A UK-regulated role ESCO does not
   flag gets no placeholder gate. If it also lacks any modelled row, it still reads
   `insufficient_coverage`, never ready.
3. **Residual migration case.** A row 0029 accepted that contradicts its level would be
   refused when read back by the domain validator (an internal error, not silence). It can
   only exist in a database that ran this unpushed branch's 0029 and recorded such an
   answer.
4. **The pack target is found by ESCO occupation only when exactly one pack target
   crosswalks to it.** True in 0.1.0. A later pack with two targets for one occupation
   (two cities) would find none by occupation; the controller may want city preference
   then.

---

## Fix round 2

FIX_BASE dffd08c, final candidate b8bd1fc. This round follows re-review 1
(`task-9-rereview-1.md`) and the controller's rulings (`task-9-fix-round-2.md`). Nothing
pushed. No live call; `.env` and NESSA_HOME not read; pack 0.1.0 and its pin untouched; no
subagent; CLAUDE.md not edited.

### Status

DONE_WITH_CONCERNS: every item ruled for fixing is fixed and tested; the concerns are below.

### Commits

| Commit | What |
|---|---|
| 6c6a99f | Code: C1(b), N1, N2–N6, N8 (migration 0030 docstring only); client regenerated |
| b8bd1fc | ADR 0012 (decisions 5, 7, 8, 10, consequences; N6 added to R6) and the register |

### Items

| Item | Fix | Tests |
|---|---|---|
| **C1(b)**, the bookkeeper | `pick_occupation`, in order: the person's choice, read from its occupation-choice source (the ESCO URI, via `profile.store.chosen_occupation_uris`, keyed by the occupation's preferred label as `nessa.profile.sketch` does; a later choice wins); else the one occupation ESCO labels with the title; else the one whose *preferred* label is the title; two equal matches stay ambiguous. `occupation.basis` gains `occupation_choice` | `test_a_chosen_occupation_or_its_own_preferred_label_resolves_a_shared_label` (choice wins, preferred label disambiguates, two preferred stay ambiguous, none is no label); `test_a_bookkeeper_chosen_in_the_product_reaches_p05_s_pack_target_and_can_apply_now`; API `test_a_bookkeeper_chosen_in_the_product_reaches_p05_s_pack_target_despite_a_shared_label`. The sample lacks accountant, so this test gives "accounting assistant" the alternative label "bookkeeper" for its duration, reproducing the release's ambiguity. It checks a choice through `POST /targets` (`occupation_choice`) and a typed title (`esco_label`), both reaching `bookkeeping-assistant-leeds` and its right-to-work gate |
| **N1** | `row_evidence` reads a row's own answer first. Another rubric's level-free answer fills only a row with no answer of its own. A later "not yet done" against an own level above 0 sets `conflict`. A later levelled answer under another rubric reopens a level-free reading (`other_rubric`) | the three orders: `test_a_level_free_answer_under_another_rubric_never_supersedes_a_row_s_own`, `test_a_disagreeing_answer_under_another_rubric_asks_a_clarification` (prompt `conflict`), `test_a_later_level_under_another_rubric_reopens_a_level_free_answer` (prompt `other_rubric`, reusing B's answer); and the fill, `test_a_level_free_answer_under_another_rubric_fills_a_row_with_no_answer_of_its_own` |
| **N2** | Questions read `only_unresolved` when coverage is short and only the person's own "unsure" or "don't know" remain | `test_only_unresolved_rows_left_is_its_own_state_never_asking_with_nothing_to_ask` |
| **N3** | `show_route_chart` only when a mandatory gap an option can address exists, and not when insufficient coverage or ready now | `test_a_route_chart_is_shown_only_when_there_is_something_to_plan` (Marine biologist, unanswered TRACE-01 false; TRACE-01 below its levels true; P05 false) |
| **N4** | `find_pack_target` returns a third value; `MatrixSources.pack_target_note: ambiguous_crosswalk` | `test_two_pack_targets_for_one_occupation_record_why_neither_is_used` |
| **N5** | A required row with no rubric, or the unmodelled regulation gate, beside modelled rows: `insufficient_coverage`. `NOT_YET_KNOWN` is now only what answers settle | `test_a_requirement_answers_cannot_settle_is_a_coverage_gap_beside_modelled_rows` |
| **N6** (R6) | Coverage needs a modelled skill row or a modelled practice or recognition gate; the right to work alone is `insufficient_coverage` | `test_an_eligibility_gate_alone_is_not_coverage` (and a practice gate alone can still be ready) |
| **N7** | ADR 0012 consequences: the forward risk, for Task 7c and live research | — |
| **N8** | ADR 0012 consequences and migration 0030's docstring: 0029 ran only on test databases on this unpushed branch; a legacy contradictory row makes every capability read of its workspace `INTERNAL_ERROR` (observable). Populated-upgrade test: R12, final review | — |

### Decisions

- **Mapping a choice to its title.** The choice's concept is matched to a target through the
  occupation's preferred label (title key), the same rule as the sketch. A choice made in
  another release, or later renamed by hand, falls back to the label rules.
- **"Disagree" for N1.** Only "not yet done" against an own level above 0 is a conflict.
  "Unsure" under another rubric is not a disagreement, so it neither sets `conflict` nor
  changes the row.
- **"Reopen" for N1.** A later levelled answer under another rubric clears the level-free
  reading to unknown, so the row is asked against its own rubric with the other answer
  offered for reuse.

### Verification

| Command | Result |
|---|---|
| `make check` (on 6c6a99f's tree; b8bd1fc changes only docs) | exit 0: ruff, mypy (290 files), pytest **1381 passed** (from 1370), fixture validator, client drift none, Biome, `tsc`, Vitest **212 passed** |
| `uv run pytest tests/integration/test_capability.py -m integration` | 18 passed (from 17) |
| `make acceptance` (once, on b8bd1fc) | exit 0: integration and stack **297 passed** (from 296) in 7 min 49 s; Storybook build passed; Playwright **28 passed** |
| OpenAPI dffd08c → b8bd1fc | no schema, property or path removed. Added: the schema `PackTargetNote` and `MatrixSources.pack_target_note`. Enums widened: `OccupationLink.basis` (+`occupation_choice`), `QuestionGraph.state` (+`only_unresolved`) |

### TDD evidence

RED logs: `tdd/fr2-01-api-red.log` and `tdd/fr2-02-domain-red.log`.

- **API RED,** run before any source change: the bookkeeper test failed, because the chosen
  bookkeeper had no occupation (`TypeError: 'NoneType' object is not subscriptable`).
- **Domain RED:**
  - I first added the new names, keeping the old behaviour: `PackTargetNote`, a
    three-part `find_pack_target` with no note, and `pick_occupation` with the old label
    rule.
  - Then 9 new tests failed on behaviour: shared label, ambiguous crosswalk, the three N1
    orders, N2, N3, N5 and N6.
  - Two new tests passed at once, as expected:
    - the bookkeeper domain test, because given the right seed the crosswalk already
      works (the defect was in label resolution, which the `pick_occupation` test covers);
    - the "fill" test, because that behaviour existed and is preserved.
- **GREEN:** 76 domain tests, then 18 API tests.

### Not verified

- The reviewer's probe scripts in `t9/head/` were not re-run; their cases are covered by
  the named tests.
- The populated-upgrade test for 0030's `NOT VALID` path (R12, final review).
- The capability reference's domain review: **not run — requires human**.

### Concerns

1. **N6 is a provisional R6 rule** that blocks "ready" for a target whose only modelled
   requirements are eligibility or non-protected credential statements. It is fail-safe,
   but a person who relaxes every skill row with the warning gets `insufficient_coverage`,
   not "ready".
2. **The "with help" CHECK** (re-review point 6): migration 0030 enforces the R6 cap in the
   database, so reversing that decision needs a new migration. Left as is for the
   controller to confirm.
3. **The API bookkeeper test briefly adds an alternative label** to a sample occupation in
   the shared test database, removed in `finally`. This is the same pattern as
   `test_discovery.py`'s shared-title test.
4. **A choice is matched to its target by preferred label.** If the person later edits the
   title by hand, the choice no longer applies, and the label rules decide.

---

## Fix round 3

FIX_BASE b8bd1fc, final candidate f6e9bfb. This round follows re-review 2
(`task-9-rereview-2.md`, 9 of 9 fixed, two new Minors) and `task-9-fix-round-3.md`. Nothing
pushed. No live call; `.env` and NESSA_HOME not read; pack 0.1.0 and its pin untouched; no
subagent; CLAUDE.md not edited.

### Status

DONE.

### Commits

| Commit | What |
|---|---|
| 707d6cc | Code: R2-1 and R2-2; client regenerated (`Qualification` + `open_conflict`) |
| f6e9bfb | ADR 0012 decision 7 and the register |

### Items

| Item | Fix | Tests |
|---|---|---|
| **R2-1** | State ladder: a known shortfall (`below_required`, `not_held`, `pathway_outside_model`; `KNOWN_SHORTFALL`) gives `not_ready` first. The coverage gap stays its own blocker: a row with no rubric (`not_modelled`), the unmodelled regulation gate (`unresolved`), or `no_modelled_requirements`. `insufficient_coverage` applies only with no known shortfall. `show_route_chart` is now the plannable gaps alone (a mandatory learn, credential or experience gap), not the state | `test_a_known_shortfall_stays_not_ready_beside_a_requirement_no_answer_can_settle`: P01's data quality target with every modelled row at level 1, then the ESCO row "statistics" set to essential. Before and after the edit: `not_ready` with the route chart, and afterwards a `not_modelled` blocker for "statistics" beside `below_required` |
| **R2-2** | Qualification `open_conflict` when a met required row's evidence has `conflict: true` | case 1 (a later "not yet done" under another rubric against an own level 2): `test_a_ready_result_with_an_open_conflict_says_so`, which is ready now with `open_conflict`, and not without the later answer. Case 2 (reachable on pack 0.1.0): `test_a_demonstration_that_disagrees_with_a_self_report_is_an_open_conflict_on_the_pack`, on P05's bookkeeping target with a self-report of 3 and a work sample of 2, which is ready now with `open_conflict` |

Both are recorded in ADR 0012 decision 7 (the readiness states), with the register's RDY1-01
and RDY1-03 rows.

### Verification

| Command | Result |
|---|---|
| `make check` (on 707d6cc's tree; f6e9bfb changes only docs) | exit 0: ruff, mypy (290 files), pytest **1384 passed** (from 1381), fixture validator, client drift none, Biome, `tsc`, Vitest **212 passed** |
| `uv run pytest tests/integration/test_capability.py -m integration` | 18 passed |
| `make acceptance` (once, on f6e9bfb) | exit 0: integration and stack **297 passed** in 7 min 52 s; Storybook build passed; Playwright **28 passed** |
| OpenAPI b8bd1fc → f6e9bfb | `Qualification` gains `open_conflict`; nothing else changed |

### TDD evidence

RED log: `tdd/fr3-01-red.log`. The three new tests failed before the fix:
- R2-1 read `insufficient_coverage` with no route chart, against the expected `not_ready`
  with a chart;
- both R2-2 tests failed on the missing `Qualification.OPEN_CONFLICT`.

After the fix, 79 domain tests and 18 API tests pass.

### Concerns

None new. The concerns of rounds 1 and 2 stand.
