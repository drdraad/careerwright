# Task 7 slice 7B: re-review 1-B (fix round 1, items 10-18)

This re-review is scoped to items 10-18 of `task-7-sliceB-fix-round-1.md`, which cover my
findings I1, I2, M1-M3 and M6-M10. B-M4 and B-M5 are parked, as the ruling says.

**Inputs.** I read the rulings, the implementer's "Fix round 1" section (as unverified
claims) and `review-04f95cf..044ef12.diff`. Within the diff I read every file my items
touch:
- `ai_resilience.py`, `reference_schemas.py`, `discovery_schemas.py` and `exploration.py`;
- the fixture pack and migration 0028;
- `reference_store.py`;
- `test_ai_resilience.py`, `test_reference_data.py`, `test_discovery.py` and
  `tests/support/reference_data.py`;
- ADR 0010, the register and the runbook.

**Constraints kept.** HEAD is `044ef12`. I worked read-only: I did not read `.env` or
NESSA_HOME, made no live call and dispatched no subagent.

## Probes re-run on 044ef12

The probe script is
`/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/probes/probe_air_r1.py`.
It runs under `uv run --locked` and changes nothing in the repository.

| Probe | Before (04f95cf) | Now (044ef12) |
|---|---|---|
| 1: `model_proposal` with a full decision by "Muse Spark (model)" | no failures, `published` | `[model_proposal]`, `proposed`; with a null decision it is also `[model_proposal]`, `proposed` |
| 2: record bounds edited to 0-10 after a 5-8 decision | no failures | `[bounds_not_decided]`, `proposed`. Editing both the record and the decision to 0-10 still passes, which is correct: the decision is the reviewer's. |
| 3: a fixture-pack occupation with no record | `synthetic=True`, label `None` | `unscored`, `no_record`, `synthetic=False`, label `None` |
| 5: data quality specialist with the real ILO row (ISCO 2519, Gradient 3) | `ai_evidence.state: exposure_only` beside `published_range` | fixture pack: `assessed` beside `published_range`, `synthetic=True`, quality `limited`. Product pack: `exposure_only` beside `unscored`. |
| Extra: exposure and observed use plus an unobserved accountability item | n/a | `[exposure_only_evidence]`: only observed items count |

The fixture record itself publishes under every new rule (`state published`, no failures).

## Verdicts

| Item | Finding | Verdict | Evidence |
|---|---|---|---|
| 10 | B-I1 exposure-only evidence | **fixed** | See below |
| 11 | B-I2 `origin` load-bearing | **fixed** | See below |
| 12 | B-M1 decision binds bounds | **fixed** | See below |
| 13 | B-M2 reviewed null | **fixed** | See below |
| 14 | B-M3, B-M8 synthetic labelling | **fixed** | See below |
| 15 | B-M6 evidence quality, widening | **fixed** | See below |
| 16 | B-M7 scored range through the slate | **fixed** | See below |
| 17 | B-M9 endpoint failure paths | **fixed** | See below |
| 18 | B-M10 ADR numbering | **fixed** | See below |

### Item 10: B-I1, exposure-only evidence
- **The new check.**
  - `EXPOSURE_FAMILIES` is defined at `backend/src/nessa/catalogue/ai_resilience.py:231`.
  - `exposure_only_evidence` is raised when every observed item is an exposure family
    (`:251`).
- **The fixture.** It gains a labelled synthetic `human_accountability` item that bears
  protection, in its own independence group (`packs/ai_resilience_fixture.json:32`).
- **The evidence state.** `ai_evidence.state` is now derived from the assessment
  (`backend/src/nessa/api/reference_schemas.py:326`, `ASSESSED` at `:214`).
- **Tests.**
  - The parametrised case (`backend/tests/domain/test_ai_resilience.py:137`).
  - The committed-pack test asserts the fixture has a non-exposure family and that every
    measure says "SYNTHETIC".
  - `test_reference_data.py:237` tests `assessed` beside a published range and
    `exposure_only` without one.
- **Register.** The AIR1-02 and AIR1-03 text is corrected (`docs/requirements-register.md:155-156`).

### Item 11: B-I2, `origin` is load-bearing
- **The check.** A `model_proposal` fails at `ai_resilience.py:284`.
- **The test.** `test_ai_resilience.py:188` builds a proposal that passes every other check,
  asserts that `model_proposal` is its only failure and that it stays unscored, then shows the
  same record as a `reviewer_entry` publishing.
- **Shape assertions.** They are gone.
- **Docs.** ADR 0010 decision 7 (`docs/adr/0010-reference-data-and-ai-evidence.md:103-106`)
  and AIR1-04 (`docs/requirements-register.md:157`) now say exactly what holds: no code path
  writes a record, and the product pack is held empty by a test. Probe 1 confirms.

### Item 12: B-M1, the decision binds its bounds
- **The fields.** `ReviewerDecision.lower` and `upper` are at `ai_resilience.py:141-142`.
- **The check.** `bounds_not_decided` is raised at `:263`.
- **Tests.** Two cases at `test_ai_resilience.py:142` and `:144`: an edited `upper`, and a
  decision without bounds.
- **Fixture.** It carries 5-8 in its decision (`ai_resilience_fixture.json:51-52`).
- **Probe.** Probe 2 confirms.

### Item 13: B-M2, a reviewed null
- **The change.** The evidence-sufficiency checks run only for a range, or when there is no
  decision (`ai_resilience.py:292`).
- **The test.** `test_ai_resilience.py:250` gives a null one exposure family and no quality.
  It asserts no failures and `published_null`/`reviewed_null`, and that a null with bounds is
  still `range_invalid`.

### Item 14: B-M3 and B-M8, synthetic labelling
- **No record.** `synthetic=False` when there is no record (`ai_resilience.py:456`). This is
  tested in the domain suite (`test_ai_resilience.py:272`) and in the fixture workspace
  (`test_reference_data.py` adds a no-record role asserted `synthetic: false`).
- **The filter output.**
  - `AiFilterView.synthetic` is set when a scored range comes from a synthetic record
    (`backend/src/nessa/profile/exploration.py:304`).
  - `AiResilienceFilterOut.synthetic` (`backend/src/nessa/api/discovery_schemas.py:381`)
    carries it to the API.
  - The summary then says "a synthetic fixture range here, not a real assessment" (`:401`).

### Item 15: B-M6, evidence quality and widening
- **The field.** `EvidenceQuality` is at `ai_resilience.py:149`. The record field
  `evidence_quality` is required for a range (`:254`) and exposed on
  `ai_resilience.evidence_quality` for a published range only.
- **Widening.** `widening_not_explained` is raised for a range across bands with no reason
  (`:275`).
- **Fixture.** It has both (`ai_resilience_fixture.json:41`, `:55`).
- **Tests.** `test_ai_resilience.py:147`, `:149`.
- **Words.** Consistency of the provisional words is judged separately below.

### Item 16: B-M7, a scored range through the slate
- **The test.** `backend/tests/integration/test_discovery.py:272` puts the labelled synthetic
  5-8 record onto the bicycle mechanic (`tests/support/reference_data.py`, `packs_scoring`).
- **What it asserts.**
  - At a minimum of 5: kept, with `scored` 1 and `below_minimum` 0.
  - At 6: left out as `below_ai_resilience_minimum`, with `scored` 1 and `below_minimum` 1.
  - `synthetic` and the summary words are checked at both.
  - The product pack gives `scored` 0 and `synthetic` false.
- **The gap is closed.** Deleting the `BELOW_MINIMUM` branch would now fail this test.

### Item 17: B-M9, the evidence endpoint's failure paths
- **Unknown occupation.** `test_reference_data.py:263` checks for 404 `NOT_FOUND`.
- **No reference data.** `test_reference_data.py:271` uses a fresh database that holds ESCO
  and no reference data, and checks for 503 `REFERENCE_DATA_UNAVAILABLE` through the endpoint.
- **First run.** Both passed on their first run, as the report says; they cover behaviour
  that already held.

### Item 18: B-M10, the ADR's provisional-decision numbering
- **Status line.** It now reads "Decision 4 (the full-time tables), decision 8 (the 90th
  percentile; advertised pay read as gross), decision 7's evidence-quality words"
  (`docs/adr/0010-reference-data-and-ai-evidence.md:4-5`).
- **Consequences.** They name the same decisions (`:200-202`).
- **Remaining error.** An adjacent error remains in the new sentence at `:7` (New Minor 1).

**Totals:** 9 of 9 items fixed, covering all 10 findings. None partly fixed, none not fixed.

## Also checked

- **Migration 0028** (`backend/src/nessa/migrations/versions/r0028_ashe_statistic_cvs.py`):
  sound.
  - It is a new forward-only file: `down_revision = "0027"` and `downgrade` raises.
  - It deletes the ASHE rows and the `ashe` manifest row (`:24-25`) before
    `ADD COLUMN cvs jsonb NOT NULL` (`:27`). The NOT NULL column is therefore added to an
    empty table, which also works on a database populated at 0027.
  - Table-level RLS and the `SELECT` grant are untouched and cover the new column.
  - With the manifest row gone, `cli.import_reference_data` finds `ashe` not held. It
    re-verifies the unchanged pinned file and imports it with `nessa-ashe-import-2`.
  - Without the deletion, `import_dataset` would raise `ReferenceMismatchError`. So this is
    the reviewed migration ADR 0010 decision 2 requires.
  - Between the migration and the re-import, the evidence endpoint answers 503
    `REFERENCE_DATA_UNAVAILABLE` (the manifest set check), never an empty answer.
  - `reference_store` writes and reads `cvs` as decimal text, so no CV passes through a
    float.
  - The runbook states the re-import.
  - Its upgrade path is untested (New Minor 2).
- **Evidence-quality words** (`limited`, `moderate`, `strong`; provisional, R6): consistent.
  - The enum is the only vocabulary for this concept in the backend and web. ASHE's
    `Reliability` bands are a different, ONS-defined concept and are not conflated with it.
  - All of these agree:
    - the enum's docstring;
    - ADR 0010 decision 7 and its status line;
    - the generated client (`EvidenceQuality`);
    - the fixture (`limited`) and both tests (`limited`).
  - It is required only for a range, never for a null.
  - It is exposed only for a published range: null when unscored or when the record is a
    null decision.
  - What each word means is defined nowhere. That belongs to the R6 confirmation, not to
    consistency.
- **Client.** Spot check of the regenerated client: `AiEvidenceState.ASSESSED`,
  `AiResilienceFilterOut.synthetic`, `AiResilienceOut.evidence_quality` and
  `PayStatisticOut.cv`/`reliability` are present. I did not re-run the drift check: `make
  check` on `044ef12` reports it clean (unverified here).

## Regressions and new issues in the delta

No regressions found in my areas. The record model, the filter, the evidence state and the
fixture-only scope all behave as before, apart from the intended changes.

#### Critical
None.

#### Important
None.

#### Minor

1. **ADR 0010 names the wrong amended decisions.**
   - **Where:** `docs/adr/0010-reference-data-and-ai-evidence.md:7`.
   - **What:** The line says "Fix round 1 (2026-10-29) amended decisions 4, 6, 7, 8 and 10 as
     marked". Decision 6 is unchanged in the delta, and decision 9 was amended (its
     `synthetic` filter output, `:166`).
   - **Fix:** "amended decisions 4, 7, 8, 9 and 10". This is document accuracy only.
2. **Migration 0028 has no upgrade test from a populated 0027.**
   - **Where:** `backend/tests/integration/test_migrations.py`.
   - **What:**
     - The repository tests each data-changing migration from data at its prior revision
       (`test_migrations.py` does this for 0006, 0009 and 0014, migrating to 0005, 0008 and
       0013 first).
     - 0028 deletes data and adds a NOT NULL column, but it ran only on the acceptance
       stack's fresh, empty table.
     - By reading, the SQL is correct for a populated table.
   - **Fix:** migrate to "0027", import the synthetic samples, upgrade, then re-import.
     Assert that `ashe` is re-imported with `nessa-ashe-import-2` and that a statistic
     carries its own CV.
   - **Severity:** R12: coverage, no reproduced defect.

**Counts:** fixed 9 items (10 findings), partly fixed 0, not fixed 0. New issues: Critical 0,
Important 0, Minor 2.
