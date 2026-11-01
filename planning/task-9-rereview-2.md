# Task 9 re-review 2: fix round 2 (dffd08c..b8bd1fc)

Fix round 2 fixes all nine items in scope: C1(b), N1 and N2 to N8. It leaves no new
Critical or Important issue and two new Minor ones.

## How I checked

- **Mode:** a scoped re-review, read-only. No live calls and no subagents; I did not read
  `.env` or NESSA_HOME.
- **Inputs:** `task-9-fix-round-2.md`, the report's "Fix round 2" section, and the whole
  1,450-line package.
- **Generated client:** I compared the two OpenAPI documents rather than reading the
  generated code.
- **Probes:** I re-ran my probes against HEAD b8bd1fc:
  - `probe_ready`, `probe_answers`, `probe_conditional`, `probe_fr1`, `probe_labels`,
    `probe_states` and `probe_regulated`, in
    `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/t9/head/`;
  - `probe_twice`, with the new three-part return, and the new `probe_round2`, in
    `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/t9/head2/`.
- **How they ran:** from `backend/`, with the backend directory on the path. The ones that
  read ESCO use the pinned, fetched release in `var/datasets`.
- **Working tree:** still clean.

## Probe results at HEAD

| Probe | Result at b8bd1fc |
|---|---|
| `probe_ready` | "Adult nurse" (regulated) and "Marine biologist" are both `insufficient_coverage` with `address_gaps`. Questions are `insufficient_coverage`. The route chart is now **false** for both (N3). |
| `probe_answers` | Unchanged from round 1, and correct: not learned and understood-not-tried give a `learn` gap and are not asked again; unsure is not asked again; a work sample the person entered is `provisional` with `person_confirmed_demonstration`. |
| `probe_conditional` | Unchanged: `not_ready` (known below), plus `missing_outcome_level` on the conditional result. |
| `probe_fr1`, order 1 | A has a concrete level 2, then "unsure" under B. A stays at **level 2** and reads ready. |
| `probe_fr1`, order 2 | A has level 2, then "not learned" under B. A stays at **level 2**. The test asserts `conflict: true` and a `conflict` prompt. |
| `probe_fr1`, order 3 | "Not learned" under A, then level 3 under B. A goes back to **unknown** and is asked again with reason `other_rubric`. |
| `probe_fr1`, M4 | Unchanged: level 1 with a conflict (parked). |
| `probe_labels` | "bookkeeper" is still the preferred label of bookkeeper and an alternative label of accountant in ESCO v1.2.1. |
| `probe_states` | When every remaining row is "unsure", the questions read **`only_unresolved`** with 0 prompts (N2). A verified right to work alone reads **`insufficient_coverage`** (N6). |
| `probe_regulated` | Unchanged: 16 flagged occupations; social worker, physiotherapist, occupational therapist and diagnostic radiographer are not flagged. |
| `probe_twice` | With two pack targets for one occupation: no pack target, `pack_target_note: ambiguous_crosswalk`, `insufficient_coverage` (N4). |
| `probe_round2` | Bookkeeper path and later title edits, N5 precedence, N1 order 2 readiness: see named checks 1 and 2 and issues R2-1 and R2-2. |

## Items

| Item | Status |
|---|---|
| **C1(b)** | Fixed |
| **N1** | Fixed |
| N2 | Fixed |
| N3 | Fixed |
| N4 | Fixed |
| N5 | Fixed as ruled (one new Minor, R2-1) |
| N6 | Fixed, recorded as R6 |
| N7 | Fixed |
| N8 | Fixed |

**C1(b): fixed.** A choice is read from its own source.
- `_chosen` reads the choice's ESCO URI (`commands.py:169-180`), using the existing
  `profile_store.chosen_occupation_uris`, and keys it by the occupation's preferred-label
  title key. `capability_view` passes it to each target (`commands.py:120`).
- `pick_occupation` (`matrix.py:771-793`) tries, in order:
  1. the person's choice;
  2. the one occupation ESCO labels with the title;
  3. the one whose *preferred* label is the title;
  4. otherwise, two equal matches stay ambiguous.
- Tests:
  - domain: `test_a_chosen_occupation_or_its_own_preferred_label_resolves_a_shared_label`
    covers all four outcomes, and
    `test_a_bookkeeper_chosen_in_the_product_reaches_p05_s_pack_target_and_can_apply_now`
    reaches `bookkeeping-assistant-leeds` with its right-to-work gate and reads ready now;
  - API: `test_a_bookkeeper_chosen_in_the_product_reaches_p05_s_pack_target_despite_a_shared_label`
    covers both a choice (`occupation_choice`) and a typed "bookkeeper" (`esco_label`).

**N1: fixed.**
- `_reading` (`evidence.py:239-266`) puts a row's own answer first. Another rubric's
  level-free answer fills a row only when it has none of its own.
- A later "not yet done" against an own level above 0 is a `conflict`. A later levelled
  answer under another rubric reopens the row (`evidence.py:258-259`).
- There are four domain tests: the three orders and the fill.

**N2: fixed.**
- When coverage is short and nothing is left to ask, the state is `only_unresolved`, never
  `asking` (`questions.py:186-194`).
- Test: `test_only_unresolved_rows_left_is_its_own_state_never_asking_with_nothing_to_ask`.
- "No prompts but not enough" can only mean that every remaining row is unsure. An
  unanswered gate always leaves a `not_stated` prompt.

**N3: fixed.**
- `show_route_chart` needs a mandatory learn, credential or experience gap, and is false
  for `insufficient_coverage` and for ready now (`readiness.py:389-391`).
- Test: `test_a_route_chart_is_shown_only_when_there_is_something_to_plan`.

**N4: fixed.**
- `find_pack_target` now returns `PackTargetNote.AMBIGUOUS_CROSSWALK` (`matrix.py:764-765`),
  and the matrix records it in `MatrixSources.pack_target_note` (`matrix.py:284`).
- Shown by the test and by `probe_twice`.

**N5: fixed as ruled.**
- A required row with no rubric, or the unmodelled regulation gate, now reads
  `insufficient_coverage` (`readiness.py:346-349`).
- `NOT_YET_KNOWN` now holds only what answers settle (`readiness.py:102`).
- ADR 0012 decision 7's table is reworded to match.
- Test: `test_a_requirement_answers_cannot_settle_is_a_coverage_gap_beside_modelled_rows`.

**N6: fixed, recorded as R6.**
- `_covers` (`readiness.py:599-605`): only a skill row a rubric models, or a modelled
  legal-practice or recognition gate, counts as coverage. The right to work alone gives
  `insufficient_coverage` (`readiness.py:343-345`).
- A practice gate alone can still be ready.
- R6 is recorded in ADR 0012's status (decision 7, line 14) and in decision 7's "What
  counts as coverage" (line 201).
- Test: `test_an_eligibility_gate_alone_is_not_coverage`.

**N7: fixed.** ADR 0012's consequences (line 296) record the forward risk for Task 7c and
live research.

**N8: fixed.**
- Migration 0030's docstring (lines 13-17) and ADR 0012's consequences (line 301) say that
  0029 ran only on test databases, and what a legacy row would do.
- The populated-upgrade test is left for the final review (R12), as ruled.
- The claim "never `make dev`" cannot be verified without NESSA_HOME.

**Generated client: additive.**
- New schema `PackTargetNote` and new optional property `MatrixSources.pack_target_note`.
- Enums gained values only: `OccupationLink.basis` gains `occupation_choice`, and
  `QuestionGraph.state` gains `only_unresolved`.
- Nothing was removed, and no path changed.

## Named checks

1. **The bookkeeper path.** Holds, and is fail-safe under later title edits.
   - **A choice:** a choice of "bookkeeper" reaches `bookkeeping-assistant-leeds` and
     `gate:uk-right-to-work`.
     - In the domain: `probe_round2` uses the release's own label matches;
       `pick_occupation` gives `occupation_choice`, and `find_pack_target` gives
       `esco_crosswalk`.
     - Through the API: the test above.
   - **Edits that keep the title key keep the choice.** `title_key` folds case,
     punctuation and bracketed notes (`evidence/jobs.py:73-75`). So "Bookkeeper" and
     "Bookkeeper (Leeds)" still name the chosen occupation, which is right.
   - **Edits that change the key fall back to the label rules.** These can only:
     - reach a pack target by exact title, a unique label, the preferred-label tie-break
       or the crosswalk;
     - or reach nothing, which gives `insufficient_coverage`.

     For example, "accountant" resolves to ESCO's accountant: no pack target,
     `insufficient_coverage`. "Bookkeeping assistant" reaches the pack by title.
   - **A stale choice applies only to the same folded text.** It can only apply to a title
     whose folded text is the chosen occupation's own preferred label, so it never lends a
     different occupation's rows or gates.
   - **A regulated choice edited away keeps its protection.** It falls back to the label
     rules or to nothing. With no seed there is no gate, but nothing is modelled either,
     so it is never ready.
2. **N1.** Holds. All three orders are correct (`probe_fr1`, and the three tests), and the
   `other_rubric` prompt returns in order 3 with B's answer offered for reuse
   (`test_a_later_level_under_another_rubric_reopens_a_level_free_answer`). See R2-2 for
   readiness while the order-2 conflict is open.
3. **N6.** Holds. Eligibility alone is never coverage (`probe_states`, the test), and it is
   recorded as provisional R6 in ADR 0012.
4. **The API test's mutation of the shared database.** It is isolation-safe.
   - **Tests run one at a time:** there is no pytest-xdist or `-n` in `pyproject.toml` or
     the Makefile.
   - **Nothing to collide with:** the sample's "accounting assistant" has no "bookkeeper"
     label. I checked `fixtures/esco-sample`.
   - **A clash cannot be silent:** `occupation_labels`' primary key is
     `(concept_id, normalised)` (`r0004_taxonomy.py:81-87`). A clash would fail the
     `INSERT` before `try`, deleting nothing.
   - **The clean-up is exact:** `finally` deletes only the row inserted, by concept and
     normalised label.
   - **It follows the existing pattern:** it is the same as `test_discovery.py`'s
     shared-title test.
   - **Residual risk:** a process killed inside the `try` would leave the label behind,
     the same as that precedent.

## New issues

### Minor

**R2-1. A requirement that can't be modelled hides a known shortfall and the route chart.**

- **Where:** `backend/src/nessa/capability/readiness.py:346-349`, `:389-391`.
- **What:**
  - The N5 branch comes before the `not_ready` branch.
  - So one edit makes the whole target `insufficient_coverage`: setting an ESCO row with no
    rubric to essential, which needs no warning.
  - Before that edit the result was `not_ready` (below the required level) with a route
    chart. After it, the route chart is also turned off. `probe_round2`, P01's data quality
    target with every modelled row at level 1, shows this:

    | | State | Route chart |
    |---|---|---|
    | as given | `not_ready` | true |
    | "statistics" set to essential | `insufficient_coverage` | false |

  - Blockers still list `below_required`, so this is never a false success, and the ruling
    is met literally.
- **Fix:** let a known shortfall keep `not_ready`, carrying the coverage gap as its blocker
  or a qualification. Or keep the state but base `show_route_chart` on the plannable gaps.

**R2-2. "Ready now" can rest on evidence the person has contradicted.**

- **Where:** `backend/src/nessa/capability/readiness.py:343-356`, `:630-657`.
- **What:**
  - In N1's order 2, A has its own level 2, then "not learned" under B. A stays at level 2
    with `conflict: true`, and the questions ask a `conflict` clarification. That is
    correct.
  - But readiness reads `ready_now_for_modelled_requirements`, and its qualifications say
    nothing of the open conflict (`probe_round2`).
  - The same holds for a demonstration that conflicts with a self-report at or above the
    required level.
- **Why it matters:**
  - Spec section 9 says conflicting evidence triggers a clarification.
  - A ready-now lead resting on evidence the person has since contradicted should say so.
  - This cannot happen with pack 0.1.0, where no subject is shared across rubrics, except
    through the demonstration case.
- **Fix:** add a qualification, for example `open_conflict`, when a met mandatory row has
  `conflict: true`. Or hold the result at `not_yet_assessed` until the person clarifies.

## Counts

- Items: fixed 9 (C1(b), N1, N2, N3, N4, N5, N6, N7, N8); partly fixed 0; not fixed 0.
- New issues: Critical 0, Important 0, Minor 2 (R2-1, R2-2).
