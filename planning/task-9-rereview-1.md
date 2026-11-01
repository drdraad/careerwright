# Task 9 re-review 1: fix round 1 (23d081b..dffd08c)

## How I checked

- **Mode:** a scoped re-review, read-only. No live calls and no subagents; I did not read
  `.env` or NESSA_HOME.
- **Inputs:** `task-9-fix-round-1.md`, the report's "Fix round 1" section, and the whole
  2,586-line package.
- **Client:** I compared the two OpenAPI documents rather than reading the generated code.
- **Probes:** I ran my four t9 probes against HEAD dffd08c. They are in
  `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/t9/head/`.
  Each copy adds only the argument `build_matrix` now requires (`synthetic=False`).
- **New probes:** I wrote six for the named checks: `probe_fr1.py`, `probe_twice.py`,
  `probe_states.py`, `probe_labels.py` and `probe_regulated.py`; `probe_labels.py` and
  `probe_regulated.py` read the pinned, fetched ESCO release in `var/datasets`.
- **How they ran:** all from `backend/` with `uv run --locked python <probe>`.
- **Working tree:** still clean.

## Probe re-runs at HEAD

| Probe | 23d081b | dffd08c |
|---|---|---|
| `probe_ready` ("Adult nurse", ESCO seed, `regulated: true`, no evidence) | `ready_now…`, apply first, questions `enough` | `insufficient_coverage`, `address_gaps`, gate `gate:occupation-regulation` unresolved, questions `insufficient_coverage` with 0 prompts |
| `probe_ready` ("Marine biologist", no seed) | `ready_now…` | `insufficient_coverage`, no apply action |
| `probe_answers`: not learned / understood, not tried, no level | `no_usable_evidence`, `information` gap, asked again | `below_required`, `learn` gap, not asked again |
| `probe_answers`: unsure | asked again as `no_evidence` | `no_usable_evidence`, not asked again, listed as unresolved |
| `probe_answers`: a work sample the person entered (level 3) | `corroborated`, no self-report qualification | `provisional`, `person_confirmed_demonstration` |
| `probe_answers2`: `not_learned` with level 4 | accepted, row met, ready now | refused: `ValueError` "that answer contradicts its level" |
| `probe_answers2`: M4 (self-report 3, reviewed assessment 1) | level 1, conflict | level 1, conflict: unchanged, parked |
| `probe_conditional` (C06 completed, accepted) | `not_ready`, no marker | `not_ready` (records is known to be below), plus `missing_outcome_level` |

## Items

| Item | Status | Evidence |
|---|---|---|
| **C1** | **Partly fixed** | See below. (a) and (c) are fixed; (b) is fixed for three of the four crosswalked occupations. |
| I1 | Fixed | See below. |
| I2 | Fixed, with a regression (N1) | See below. |
| I3 | Fixed | See below. |
| I4 | Fixed | See below. |
| M1 | Fixed | `task-9-report.md:96` now names all three enum changes. |
| M2 | Fixed | `docs/requirements-register.md` MAP1-01 names Task 10's Skills chapter as owner, and says rows read from an example need the person's confirmation. |
| M3 | Fixed | `matrix.py:814` discards `relaxed_by_person` when a row goes back into the definition; test `test_a_row_set_back_to_required_is_no_longer_marked_relaxed`. |
| M5 | Fixed | The test now passes `occupation_note` and asserts it, and asserts `insufficient_coverage` (`test_capability_matrix.py`). |
| M6 | Fixed | `_seed`'s `release is None` branch is gone, and `release` is required (`commands.py:155-160`). |
| M8 | Fixed | See below. |
| M4 (parked) | Recorded as R6 | ADR 0012's status lists it under decision 5. Decision 5 ends with "Parked for session 2's decision sheet and the final review (review M4)". |

**C1(a): fixed.**
- New state `insufficient_coverage` with a target-level blocker `no_modelled_requirements`
  (`readiness.py:340-346`).
- Questions read `insufficient_coverage` and never `enough` (`questions.py:177-185`).

**C1(c): fixed.**
- `matrix.py:698-726` adds the unmodelled protected gate `gate:occupation-regulation`.
- The domain and readiness never satisfy it (`readiness.py`, `_stated`).
- A statement on it is refused (`commands.py:397-399`).
- Domain test and API test ("general practitioner").

**C1(b): fixed for the nurse, not for the bookkeeper.**
- `find_pack_target` (`matrix.py:729-749`) reaches "nurse responsible for general care",
  "data quality specialist" and "ICT help desk agent".
- It does **not** reach "bookkeeper", P05's own occupation, when it is chosen in the
  product. The ESCO occupation is re-derived from the stored label, and "bookkeeper" is
  also an alternative label of "accountant" (`probe_labels.py`). `_seed` sees two matches
  and returns `ambiguous_esco_label` (`commands.py:163-175`), so no seed means no
  crosswalk lookup.
- Result: no pack rows, no right-to-work gate, `insufficient_coverage`. This fails safe,
  never ready. But P05's apply-now path cannot be reached by choosing the occupation in the
  product. Residual severity: **Important**.
- Fix: when several occupations carry the label, prefer the one whose *preferred* label is
  the title. That is how the product stores a choice (`profile/exploration.py:839`), so it
  is not a guess. Or read the chosen concept from the target's occupation-choice source
  (its locator is the ESCO URI). Add the bookkeeper case to the domain and API tests.

**I1: fixed.**
- `not_yet_assessed` when only unknowns block (`readiness.py:100-102`, `:347-350`).
  `not_ready` is kept for known shortfalls.
- `missing_outcome_level` (`readiness.py:590-610`) is raised on C06 but not on C02's topic
  mention.
- The READINESS-01 test now asserts `not_yet_assessed`.

**I2: fixed for the five answers; it introduces regression N1.**
- Contradictions are refused in the domain (`evidence.py:109-116`) and in the database
  (migration 0030); the API returns 422 `inconsistent_evidence`.
- Not learned and understood-not-tried are a known level 0 with a `learn` gap
  (`evidence.py:183-194`). Unsure is unresolved and not asked again (`questions.py:234-235`).

**I3: fixed.**
- A demonstration is `provisional` (`evidence.py:192`).
- `person_confirmed_demonstration` and `person_confirmed_verification` are added
  (`readiness.py:628-633`).
- Asserted in the P05 work-sample test, in the P04 test (verified gives the qualification,
  unverified does not) and in the pack apply-now test.

**I4: fixed.**
- `QuestionsOut` gains `pack` and `reference` (`capability_schemas.py:73-80`).
- `review_state` is added on `PromptRow` (`questions.py:86`), `RowAssessment` and `Gap`
  (`readiness.py:198`, `:218`).
- `as_of` is added on `CandidateOption` (`readiness.py:240`).
- Asserted in the API labels test.

**M8: fixed.**
- `synthetic` and `data_mode` are on every capability envelope.
- `Matrix.synthetic`, `Assessment.synthetic` and `QuestionGraph.synthetic` come from the
  workspace (`commands.py:101-123`).
- Tested in the domain and through the API, for both a synthetic and a non-synthetic
  workspace.

**Generated client.**
- Every enum change is an addition:
  - `ReadinessState` gains 2 values;
  - `Qualification` gains 3;
  - `RowStatus` gains 1;
  - `Uncertainty` gains 1;
  - `QuestionGraph.state` gains 1.
- No schema, property or path was removed. New properties are added on 12 schemas.
- Three response fields were widened to nullable: `Blocker.row_id`, `GateInfo.issuing_body`
  and `GateInfo.verification`. The report discloses this (concern 1), and no web code reads
  them yet. I accept it within this unpushed task.

## Named checks

1. **The two new states are distinct and never ready.** Holds.
   - In the state ladder (`readiness.py:340-355`), only the final branch is
     `ready_now…`. `primary_action` is `address_gaps` for both new states, and no apply
     action is added.
   - The meanings differ: `insufficient_coverage` means nothing required is modelled;
     `not_yet_assessed` means only unknowns block.
   - Edge cases are Minor N5 (an unmodelled gate beside modelled rows) and N6 (an
     eligibility gate as the only coverage).
2. **The slate's "nurse responsible for general care" reaches the NMC gate.** Holds.
   - Domain: `test_a_slate_chosen_nursing_label_reaches_the_pack_s_registration_gate`
     uses the real concept and the real crosswalk.
   - API: `test_a_nursing_occupation_chosen_in_the_product_keeps_the_registration_gate`
     goes through `POST /targets`, the product's own path, and asserts the pack target,
     `esco_crosswalk`, the typed `legal_practice` gate, `not_yet_assessed` and that the
     gate is asked first.
   - I traced `_matrix` to confirm it: no title match, a unique exact label, an
     `esco_label` seed, then the crosswalk.
   - I did not run the integration test myself (the report says `make acceptance` passed:
     296 tests).
   - The same route fails for "bookkeeper" (C1(b) above).
3. **A regulated occupation with no typed gate, and roles ESCO does not flag.**
   - The unresolved gate blocker holds (domain test, API test, `probe_ready`).
   - ESCO v1.2.1 flags 16 of 3,039 occupations (`probe_regulated.py`): nursing,
     midwifery, medicine, dentistry, pharmacy, veterinary roles, architect, and a
     "coating machine operator".
   - "Social worker", "physiotherapist", "occupational therapist" and "diagnostic
     radiographer" are UK-regulated but **not** flagged.
   - With pack 0.1.0, such a role never reads ready. No pack target is reachable for
     them, ESCO rows are never modelled, and a person who sets an ESCO row to essential
     only adds a `not_modelled` row, which does not count as coverage.
   - So the answer is yes today. It holds only because no modelled rows exist for these
     roles: a later pack or live research that models one without typing its gate would
     read ready (Minor N7, forward).
4. **Migration 0030's `NOT VALID` CHECKs.**
   - Sound. The table is append-only for the API role, so no update can trip a legacy row
     later, and every new insert is checked. Forward-only discipline forbids editing 0029,
     and the downgrade raises.
   - Covered for new rows: `test_the_database_refuses_an_answer_that_contradicts_its_level`
     checks three combinations as `CheckViolation`.
   - Not covered: the case that motivates `NOT VALID`. That is a populated upgrade keeping
     a legacy row, which would then make every capability read for its workspace an
     internal error (the report's concern 3: observable, not silent). Minor N8.
   - The claim that "0029 has only ever run on this branch's test databases" cannot be
     verified without NESSA_HOME.
5. **Two matches by ESCO occupation give none: is that fail-safe?** For readiness, yes.
   - `probe_twice.py` crosswalks two pack targets to the nursing occupation. The result is
     no pack target, an ESCO-only matrix, the unmodelled regulation gate when the
     occupation is regulated, and `insufficient_coverage` either way. It is never ready.
   - The matrix records no reason: `occupation_note` and `pack_target` are both null.
     Spec section 8's protocol says to ask the person when a title maps to incompatible
     occupations (Minor N4).
   - This cannot happen in 0.1.0 (four targets, four distinct occupations).
6. **The "with help" cap at level 1.** It is recorded honestly as R6.
   - ADR 0012's status lists it under decision 5. Decision 5 states its basis (spec
     section 8's anchors) and that "the anchors do not state the ceiling in so many
     words". The report says the same.
   - For the record: the controller's ruling read "apply one only if spec section 9's
     anchors state it; otherwise record it as R6". The implementer applied it *and*
     recorded it as provisional. Migration 0030 also enforces it as a CHECK, so reversing
     the decision needs a new migration. The controller may want to confirm that is
     intended.

## New issues and regressions

### Important

**N1. A level-free answer given against one target's rubric now overrides another
rubric's evidence on the same subject.**

- **Where:** `backend/src/nessa/capability/evidence.py:173`, `:221-230`.
- **What:**
  - `_applies` makes unsure, not learned and understood-not-tried hold "under any rubric",
    and `row_evidence` then takes the latest self-report among them.
  - So a later level-free answer about target B replaces target A's own concrete level.
    `probe_fr1.py` shows it:
    - A has a concrete level 2 under `rubric-a`; a later "unsure" under `rubric-b` sets
      A's level to `None` and A's state to `not_yet_assessed`;
    - a later "not learned" under `rubric-b` sets A's level to 0 and A's state to
      `not_ready`;
    - the reverse: "not learned" under A, then level 3 under B, leaves A at level 0 and
      never asks A again. The earlier `other_rubric` prompt is gone.
- **Why it matters:**
  - S4.2 says to share evidence across targets "without assuming the same skill label has
    the same rubric or required level".
  - ADR 0012 decision 5 says "a level counts only against the rubric it was chosen for".
  - The card's coherence review asks that shared answers "reduce effort without losing
    context". Here, an answer about B's anchors silently rewrites A's readiness.
  - It is latent with pack 0.1.0: no subject is shared across two rubrics. But it is the
    designed shared-prompt path (`test_one_graph_across_targets_asks_a_shared_subject_once_against_each_rubric`),
    so any reference or pack that shares a subject makes it live.
- **Fix:**
  - Let a level-free answer from another rubric fill a row only when the row has no answer
    under its own rubric. It should never supersede one.
  - When they disagree, set `conflict`, which asks a clarification.
  - Let a later levelled answer under another rubric reopen a level-free one as
    `other_rubric`.
  - Add the two orderings above as domain tests.

### Minor

- **N2. "Asking" with nothing to ask.** When every remaining required row is "unsure", the
  questions read `asking` with 0 prompts (`questions.py:177-185`; `probe_states.py`). Spec
  section 9 offers a work sample for a consequential uncertainty, or a stop. Give that case
  a state, or a reason such as `only_unresolved`, rather than `asking`.
- **N3. A route chart for a target that cannot be assessed.** `show_route_chart` is `true`
  for `insufficient_coverage` (`readiness.py:382`). "Marine biologist" would show a route
  chart with zero actions. Show it only when there is something to plan.
- **N4. An ambiguous crosswalk records no reason** (`matrix.py:746`). With two pack
  targets for one occupation, the matrix says neither why it has no pack target nor that
  the person should choose. Add an `occupation_note`-style reason.
- **N5. A state that answers can never clear.** An unmodelled regulation gate beside
  modelled rows, or a required row with no rubric, reads `not_yet_assessed` forever
  (`readiness.py:100-102`). Yet ADR 0012 decision 7 says answers "can settle" that state.
  This cannot happen in 0.1.0. Either count such rows as coverage gaps
  (`insufficient_coverage`) or reword the ADR.
- **N6. An eligibility gate alone counts as coverage** (`readiness.py:340-343`). A target
  whose only modelled required row is the right to work reads ready once that gate is
  verified (`probe_states.py`, synthetic). In 0.1.0 this is reachable only after the person
  relaxes every skill row with the warning, which the spec allows. Note it for Task 10's
  words, or require a skill row or a practice gate before readiness can be "ready".
- **N7. The regulation guard rests on ESCO's flag** (forward risk;
  ADR 0012 decision 4). UK-regulated roles ESCO does not flag (social worker,
  physiotherapist, occupational therapist, diagnostic radiographer) are protected today
  only because nothing models them. Task 7c's reviewed pack and live research must type
  their gates, whatever ESCO says. Add this to decision 4's consequences.
- **N8. The `NOT VALID` path is untested**, and a legacy row breaks reads for its
  workspace (migration 0030, the report's concern 3). Either test a populated upgrade
  that keeps such a row, or state in the runbook that 0029 never ran outside test
  databases.

## Counts

- Items: fixed 10 (I1, I2, I3, I4, M1, M2, M3, M5, M6, M8); partly fixed 1 (C1: the
  bookkeeper part of (b), residual Important); not fixed 0. M4 is recorded as R6.
- New issues: Critical 0, Important 1 (N1), Minor 7 (N2–N8).
