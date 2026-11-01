# Task 7, slice 7B: report (BASE df44221)

Status: DONE_WITH_CONCERNS (concerns at the end; nothing is blocked).

## Commits (on `l0-local-release`, not pushed)

| SHA | Subject |
|---|---|
| `7c13de2` | Never read an image file extension as an email's TLD (Task 7 slice B, R6-1) |
| `5a94625` | Import pinned pay and AI evidence; apply the salary floor and the AI Resilience filter (Task 7 slice B) |
| `732af52` | Record the reference data, the floor and the AI record model in ADR 0010, the register and the runbook (Task 7 slice B) |
| `04f95cf` | Say the salary floor is applied in the You chapter's hint (Task 7 slice B) |

The controller's own commits `12190cf`, `3ea3a96` and `a781189` (CLAUDE.md, plan v1.2 and
v1.3) landed on the branch between `7c13de2` and `5a94625` while I worked; they touch none
of this slice's files. The code is one commit, not several: the generated client and the
web vocabulary (`Record<...>` types) must match the API at every commit, and splitting the
files needed interactive staging, which is not available.

## What I implemented

### R6-1 (first, its own commit `7c13de2`)
- `backend/src/nessa/evidence/redaction.py`: both email patterns refuse an image file
  extension (png, jpg, jpeg, gif, webp, avif, svg, ico, bmp, tif, tiff, any case) as the TLD
  (`_NOT_IMAGE_EXTENSION`, the reviewer's lookahead).
- Tests (`tests/domain/test_redaction.py`): a JSON-LD `logo`, a percent-encoded `srcset`, a
  plain `src` and a plain `srcset` each keep the body and the path
  (`test_an_image_named_at_2x_keeps_the_body_and_its_path`); five image names are never an
  address (`test_an_image_file_name_is_never_read_as_an_email_address`); `jane@recruit.example`,
  `hr@northwind.co.uk`, `jane@png.example`, `jane@recruit.pngs`, `a@b.jpg.example` are still
  removed (`test_real_addresses_are_still_removed_beside_the_image_rule`).
- ADR 0009 decision 4's limits now state the rule and its fail-safe residue (probed): an
  image name with another dotted part before the extension starting with two letters
  (`logo@2x.retina.png`, a hashed `logo@2x.ab12cd.png`) still reads as an address, so the
  body is not kept or the path rewritten. Recorded, not fixed, which R11 (added to the plan
  concurrently) also asks.
- Register ACQ-06 cites the new tests.

### Reference data (R7, TAX1-04) — `nessa/catalogue`
- `releases.py`: the generic `ReleasePin`, `read_verified`, `ReleaseIntegrityError`
  (moved out of `esco.py`; call sites updated; `MAX_RELEASE_BYTES` raised to 128 MiB for
  ASHE's 67 MB package).
- `xlsx.py`: a standard-library workbook reader (no new dependency): cells as text, refuses a
  document type declaration and any member over 64 MiB inflated.
- `ashe.py`, `soc.py`, `ai_evidence.py`: parsers that refuse anything off the documented
  structure; `reference_store.py` (SQL adapter, added to the architecture test's adapters);
  `reference.py` (import use case, `DATASETS` in import order, an occupation's evidence);
  migration `r0027_reference_data.py` (manifest `reference_releases` and six native-code
  tables, public-read RLS like ESCO's).
- `tools/datasets.py` fetches every pin (ESCO and the six), following a redirect only to
  https on the pinned host (Hugging Face answers 307); `setup-database` imports them after
  ESCO (`cli.import_reference_data`).

Datasets pinned (all fetched on 2026-10-29 from these URLs by `uv run --locked python -m
tools.datasets`, each "downloaded, verified"):

| Dataset | URL | Version | Bytes | SHA-256 | Licence |
|---|---|---|---|---|---|
| ONS ASHE Table 15 | https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/regionbyoccupation4digitsoc2010ashetable15/2026provisional/ashetable152026provisional.zip | 2026 provisional | 67,460,310 | fefd20c5a746a9ad6a563a0edf6c3ac204b093c9d23a500b7d4234122595f081 | OGL v3.0 (session 1, A2) |
| ONS SOC 2020 Volume 2 coding index | https://www.ons.gov.uk/file?uri=/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume2codingrulesandconventions/soc2020volume2thecodingindexexcel20260827v2.xlsx | version 14 (2026-08-27) | 3,717,451 | 59d3ec71d0e9eef2a27d7d0f4720f5c4bd584b61dc6902cc33dd8ee2ced40b9a | OGL v3.0 |
| ILO-NASK GenAI exposure index (WP 140) | https://raw.githubusercontent.com/pgmyrek/2025_GenAI_scores_ISCO08/ce5fc25c2a0db2757c5bfa797c4cfc8b408431ea/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx | 2025, repository commit ce5fc25 | 2,598,951 | c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a | CC BY 4.0, ILO attribution + adaptation disclaimer |
| Anthropic Economic Index task shares | https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2025_03_27/task_pct_v2.csv | release 2025-03-27, dataset commit 4e5f69f | 435,372 | 0c20f184cd4a1e3d8ef3d77f500b32b62431ce61a3c2f133c3af7fa8429f97db | CC BY (version not stated) |
| Anthropic Economic Index O*NET tasks | https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2025_03_27/onet_task_statements.csv | release 2025-03-27 | 3,592,256 | 82e4c418dc08475ef1263ad1e8c66ffa3357291370cd35ee1065ecea590597ec | CC BY; O*NET CC BY 4.0 |
| ESCO to O*NET crosswalk | https://esco.ec.europa.eu/system/files/2023-08/ONET_%28Occupations%29_0_updated.csv | version 1, September 2022 (O*NET-SOC 2019 to ESCO v1.1.0) | 2,986,823 | 82179a0a3340da97b63df90134d8d941ec3c2c478334d855b69e4dd57a91b620 | Commission Decision 2011/833/EU; O*NET CC BY 4.0 |

Counts imported from the pinned files (asserted by
`test_reference_data.py::test_the_pinned_files_import_with_their_documented_counts`, the
ASHE and crosswalk figures counted independently with a scratch standard-library script,
not the product's parsers): ASHE 13,596 estimates (412 SOC 2020 unit groups x 11 work
regions x 3 periods), 8,505 with the median withheld; coding index 32,435 coded entries,
412 unit groups, 235 uncoded; ILO 427 ISCO-08 groups (3,265 tasks); 19,530 O*NET tasks of
974 occupations; 3,364 task shares; crosswalk 4,253 rows (3 rows name ESCO occupations
v1.2.1 lacks, 235 O*NET codes have no task in the release, 43 ISCO rows).

### Pay evidence and the UK SOC mapping (TAX1-02, -03, -05, -06; JOB-05)
- `pay.py`: every SOC 2020 candidate an occupation's ISCO group links to is kept; one exact
  title narrows to `title_resolved`; reviewed only through the committed, dated mapping
  review pack (`catalogue/packs/uk_soc_mapping_reviews.json`, empty: H-10). Modelled pay
  only through a reviewed mapping, for that one code and the person's regions; never a
  blend. Benchmarks are regional (`geography: region`), trend `unavailable`,
  `single_snapshot`.
- API: `GET /v1/workspaces/{id}/occupations/{concept_id}/evidence` (`routes_reference.py`,
  `reference_schemas.py`, `profile/role_evidence.py`).

### AI evidence and the AI Resilience record model (AIR1-02/03/04/05/07/10/11/12, TAX1-07)
- ILO exposure (by ISCO-08 group), observed use (per O*NET-SOC 2019 match from the
  crosswalk: tasks listed, observed, the largest shares as published; never summed or
  averaged; "not observed" is never zero) shown as `exposure_only`.
- `ai_resilience.py`: the record model, 15 publication checks, corrections and withdrawal,
  committed packs loaded and checked at API start (`ApiDependencies.assessment_packs`),
  the lower-bound filter, the unscored state, the score's meaning in words. The product pack
  is empty; `packs/ai_resilience_fixture.json` holds one conspicuously labelled synthetic
  record (data quality specialist, 5-8) applied only in the fixture workspace.

### The salary floor as a hard filter (DIV1-07, carry-forward H-11 item 4)
- Rule (`pay.floor_verdict`): left out only when the highest pay stated, in the floor's
  period and GBP, is below the floor; unknown, predicted, other-period (never converted),
  unpublished pay is kept and counted by reason.
- Slate (`exploration._hard_filters`, `slate.choose_slate(..., left_out=...)`): modelled pay
  via a reviewed mapping, ASHE's 90th percentile in every region of the person's cities.
  `limits_not_applied` and `SALARY_FLOOR_NOT_APPLIED` are replaced by `salary_floor` (counts
  and a sentence) and `ai_resilience_filter`; `NotIncluded` gains `below_salary_floor`,
  `below_ai_resilience_minimum`, `ai_resilience_unscored_excluded`. In L0 no mapping is
  reviewed, so the floor removes no suggestion, and says so.
- Job listing (`acquisition.list_jobs`, `jobs.job_against_floor`, `store.vacancy_pay`,
  `left_out` in `store.jobs` and `city_counts`): a vacancy whose advertised GBP pay in the
  floor's period is below it is left out of the page and the totals; `salary_floor` counts;
  `EmptyReason.all_below_salary_floor`. Examples are never filtered.
- Web: `Directions.tsx` shows the floor's and the AI filter's sentences in place of
  `limits_not_applied`; `vocabulary.ts` gains words for the new error code, empty reason and
  `NotIncluded` reasons; a Vitest case for the floor sentence. Client regenerated.
- Evaluation case DSC-09 now checks the floor is reported with counts and leaves nothing out
  with no reviewed mapping (`tools/evaluation.py`, `evaluation_cases.json`).

### Docs (`732af52`)
ADR 0010 (new); ADR 0007 and 0009 open items point to it; register rows TAX1-02..07,
AIR1-02/03/04/05/07/10/11/12, JOB-05, DIV1-07, JOB-03, H-10 (widened to mapping reviews);
`docs/runbook.md` (setup, API, reviewed packs, manual download steps);
`docs/dependencies.md` (reference-data table).

## Rulings I made (simplest reading that keeps every Global Constraint)

1. **Where the code lives**: `nessa/catalogue` (spec section 17: market intelligence owns
   taxonomies, regions and AI resilience assessments). Profile and evidence both depend on
   it; it imports neither. Architectural: ADR 0010 decision 1.
2. **ILO source**: the ILO publication page offers only the PDF; the score workbook is
   published by the lead author (an ILO researcher) under CC BY 4.0 with the ILO's
   attribution terms. I pinned it by commit SHA and file hash as the "official" file the
   paper's authors publish. If the controller wants only ilo.org URLs, the alternative is
   parsing the PDF's Annex 1 (no PDF library in the lock).
3. **Anthropic release**: 2025-03-27 (`task_pct_v2` + its O*NET task statements), the last
   release with plain task-level observed use. `labor_market_impacts/job_exposure.csv` was
   rejected: it blends a capability measure (Eloundou et al.) with usage, which is not
   "observed use" and would be a formula-like composite. The release names O*NET-SOC 2019
   but not its O*NET database release; recorded so.
4. **ASHE scope** (R6, provisional): tables 15.1, 15.5, 15.7 (gross weekly, hourly, annual),
   Full-Time sheet only; 2026 provisional (the newest; the spec cites "the 2026 ONS
   release"). Binary-float values are rounded to the penny from their decimal text.
5. **"Reviewed" mappings need a human** (dispatch, H-10): no mapping is reviewed, so modelled
   pay never appears for a real occupation; ASHE is still shown per candidate unit group,
   labelled as the unit group's.
6. **Floor on occupations** (R6, provisional): the 90th percentile in every region of the
   person's cities (conservative: a career most of whose jobs pay less but some pay enough
   is kept). Corrected in fix round 2 (re-review 1-A N1): ONS withholds every percentile
   at region x unit group in this release, so this is always "not published", and the
   occupation floor can never remove a suggestion with this release.
7. **Floor on vacancies** (R6, provisional): advertised pay is read as gross (UK adverts
   state gross pay; no source field says so); copies' highest advertised amount in the
   floor's period decides. Adzuna states no period, so its pay is never below a floor.
8. **No conversion between periods**, including year and month (ASHE has no monthly table).
9. **AI filter on the slate** as a counted view parameter (the only occupation list in the
   backend until Task 8's Roles chapter).
10. **H-10 widened** to cover UK SOC mapping reviews (the dispatch names H-10 for both)
    rather than adding a new gate.
11. **Packs as committed JSON**, checked at API start (the "before a session is enabled"
    point of AIR1-07), not a database table: a reviewer's decision is then a reviewed,
    dated commit.

## Tests and checks

TDD evidence:
- R6-1: RED 9 failed / 5 control cases passed (`pytest tests/domain/test_redaction.py -k
  image`), then GREEN (240 passed across redaction, pages, extraction, Adzuna).
- Slate hard filter: RED (`test_a_hard_filter_leaves_out_only_what_it_names_and_says_why_for_each`,
  `AttributeError`: no such reason), then GREEN (12 passed).
- Vacancy floor: RED (collection error: `job_against_floor` absent), then GREEN (37 passed).
- The parsers, `pay.py` and `ai_resilience.py` were written before their tests, not RED
  first. To show the tests detect real faults I ran 7 mutations on a scratch copy of `src`
  (repository untouched): `<` to `<=` in the floor rule; the predicted branch removed; modelled
  pay from an unreviewed proposal; the independence-group check removed; unscored read as
  scored; float pence without rounding; uncoded entries not counted. All 7 were killed
  (script: the scratchpad's `scripts/mutate.py`).

Commands and results:
- `make check` on `04f95cf` (the final code): exit 0; backend 1,206 passed (fast suite),
  Vitest 212 passed, ruff, mypy, Biome, tsc, the client-drift check and the fixture
  validator clean. (Also exit 0 on `7c13de2` for R6-1: 1,132 backend, 211 Vitest.)
- Focused integration runs while iterating: `pytest -m integration
  tests/integration/test_reference_data.py` 8 passed (38 s, includes the pinned files);
  `test_discovery.py -k "salary_floor or ai_resilience_filter or controls"` 3 passed;
  `test_acquisition.py -k "salary_floor or floor_empties"` 2 passed.
- `make acceptance` (once, at the end, started on `732af52`): exit 0; 269 integration and
  stack tests passed (7 min 45 s; real PostgreSQL 16, DBOS, the Auth emulator, the Compose
  stack, whose `setup-database` imported the six pinned files), the Storybook build, and 28
  Playwright journeys passed (2.4 min). The only later change, `04f95cf`, is one web hint
  string; I edited it during the pytest phase, before the Storybook build and the web build
  for the journeys ran, so those ran with it; `make check` ran again after it (above).

Covering tests by requirement are in the register rows (each cites its tests).

## Live calls (R5)
None. No Meta call, no Adzuna call. The only network use was downloading the six pinned
files from their official URLs (each hash-checked) and reading the publishers' pages to find
them.

## Not run, requires a human (R2)
- H-10: every reviewed UK SOC mapping and every published AI Resilience record (no
  accountable reviewer exists; the packs are empty, every real role unscored).
- The licence readings for the six datasets and the provisional decisions (rulings 4, 6, 7)
  for the product owner (R6).

## Concerns
- The floor removes no slate suggestion in L0 (no reviewed mapping can exist without H-10),
  and no Adzuna advert (no period stated); it does remove page adverts with an annual (or
  same-period) salary below it. This is the conservative reading; the controller may judge
  it too weak.
- ILO data from the author's repository, not ilo.org (ruling 2).
- Jobs carry no occupation ID (JOB-01's open part), so no vacancy shows modelled pay; Task 8
  must add the link before the pay lens can show it beside a job.
- `make setup` must be re-run by the user to fetch the six new files before `make dev`;
  without them `setup-database` fails with the file's name (documented in the runbook). I
  fetched them only with `tools.datasets` (not `make setup`, which also writes NESSA_HOME).
- Two harmless stray shell commands while working: an empty heredoc to `python3` and one
  `cat >> /dev/null`; neither touched a file. No file was changed with sed, awk, a heredoc or
  a one-liner; every repository change was made with Edit or Write, except the generated
  client, which `pnpm run generate` rewrote as the runbook requires.

## Generated or vendored paths a reviewer can skip
- `apps/web/src/generated/**` (regenerated client).
- `var/datasets/*` (gitignored, not committed).

## Proposed CLAUDE.md wording (not edited)
- Commands, `make setup`: "... the pinned ESCO release and the pinned reference datasets
  (ONS ASHE, the ONS SOC 2020 coding index, the ILO and Anthropic AI evidence, the ESCO to
  O*NET crosswalk) fetched into the gitignored `var/datasets/` and hash-checked ...".
- Layout, after `nessa/catalogue` (the ESCO taxonomy and the English city list): "..., the
  pinned reference data and its native-code tables, the UK SOC mapping, modelled pay and the
  salary-floor rule, and the AI Resilience record model with its committed packs
  (`catalogue/packs/`, ADR 0010)".
- Non-obvious invariants, a new bullet: "Pay and AI evidence (ADR 0010): ASHE is regional,
  never a city's; modelled pay exists only through an accountable reviewer's UK SOC mapping
  (none in L0); the AI Resilience Score is a reviewed range or unscored, never computed from
  exposure or observed use; the salary floor leaves out only stated pay below it in its own
  period, never unknown, predicted or other-period pay, and says what it left out."

# Fix round 1 (FIX_BASE 04f95cf)

Status: DONE. All 18 items addressed; B-M4 and B-M5 left parked as ruled.

## Commits

| SHA | Subject | Items |
|---|---|---|
| `d1efff5` | Never read open-ended pay as below the floor; compare modelled pay directly; keep each ASHE statistic's CV | 1–5 (A-I1, A-M6, A-M5, A-M4, A-M3) |
| `726686b` | Say exactly what the salary floor does in L0 | 6–9 (A-M1, A-M7, A-M8, A-M2) |
| `ca4cbea` | Keep exposure-only evidence unscored, never publish a model's proposal, bind the decided range | 10–17 (B-I1, B-I2, B-M1, B-M2, B-M3/M8, B-M6, B-M7, B-M9) |
| `044ef12` | Correct ADR 0010, the register and the runbook for fix round 1 | 18 (B-M10) and the text items 10 and 11 asked for |

## What changed, by item

1. **A-I1.** `pay.floor_verdict` now holds minimum and maximum (`StatedPay`). A copy with no
   maximum is open above: `UNKNOWN`, `no_upper_amount`, unless its minimum already meets
   the floor (`MEETS`). Only stated maxima (a range's top, an "up to", one amount with
   min == max) can put a job below it; one copy open above keeps the job. `salary_from`
   reads a `+` attached to the amount or its `k` as a minimum (`extraction.py`). The test row
   that locked in the old reading is corrected; new cases: `pay(2_500_000, None)` →
   `no_upper_amount`, `pay(2_700_000, None)` → meets, a below copy beside an open one →
   unknown; and as the readers give them, "From £24,000 per annum", "Minimum £24,000 a
   year", "£24,000+ per annum" and a JSON-LD `minValue` with no `maxValue`
   (`test_jobs.py::test_open_ended_pay_as_the_readers_give_it_is_never_below_the_floor`),
   plus `£24,000+` and `£24k+` in `test_extraction.py::test_pay_is_read_exactly_as_the_span_states_it`.
2. **A-M6.** `modelled_floor_verdict` compares ASHE's P90 with the floor itself; it no longer
   builds an "advertised" `StatedPay`. Held by
   `test_pay.py::test_the_occupation_rule_compares_ashe_s_90th_percentile_with_the_floor_itself`
   (£25,999.99 below, £26,000 meets) beside the existing occupation-rule test.
3. **A-M5.** Stated pay of unknown basis is `basis_unknown`, not `no_pay` (`test_pay.py`,
   `test_jobs.py` rows).
4. **A-M4.** `AsheEstimate.cvs` keeps every statistic's CV from the "b" table;
   `PayBenchmark.reliability(statistic)`; the API's `PayStatisticOut` carries `cv` and
   `reliability` beside each statistic, replacing the benchmark's `median_cv` and
   `reliability`. Migration `r0028_ashe_statistic_cvs` replaces `median_cv` with `cvs` and
   removes the held ASHE import, so `setup-database` re-imports it as
   `nessa-ashe-import-2`. The synthetic sample now gives P90 its own CV (14.2, "acceptable",
   worse than the median's). Tests: `test_reference_parsers.py::test_ashe_keeps_codes_regions_periods_pence_and_onss_markers`,
   `test_reference_data.py::test_an_occupation_s_pay_keeps_every_uk_soc_candidate_regional_and_unmodelled`.
5. **A-M3.** `_empty_reason` says `sources_pending` before `all_below_salary_floor`
   (`test_acquisition.py::test_a_floor_emptied_page_still_says_an_answer_is_coming_while_sources_are_pending`).
6. **A-M1.** The You chapter's hint: "Before tax, with its period. A firm limit: vacancies
   whose advertised pay in that period is below it, and suggestions whose reviewed official
   pay is, are left out; Nessa says how many, and why the rest were kept."
7. **A-M7.** The slate sentence gives `meets` ("N meet it"), so its counts add up
   (`tests/api/test_floor_words.py::test_the_slate_s_floor_sentence_gives_every_count`; the
   web test's sentence updated).
8. **A-M8.** Storybook `You / SlateWithSalaryFloor` (`Conversation.stories.tsx`); the
   Playwright story run renders it and runs axe.
9. **A-M2.** DIV1-06 row; ADR 0007 decision 2 gains an amendment note pointing to ADR 0010
   decision 8 and `salary_floor` (the history is kept); `tools/setup.py`'s docstring.
10. **B-I1.** New failure `exposure_only_evidence` when every observed item is
    `task_exposure` or `observed_use`. The fixture gains a third, labelled synthetic family
    (`human_accountability`, bearing `protection`, its own independence group) and still
    publishes. `ai_evidence.state` is derived from the assessment: `assessed` beside a
    published range, `exposure_only` only when no range is published. Tests: the new
    parametrised case, `test_the_committed_packs_hold_no_real_record_and_one_labelled_synthetic_one`
    (the fixture is not exposure-only), `test_reference_data.py::test_imported_exposure_is_never_called_exposure_only_beside_a_published_range`.
11. **B-I2.** `origin` is load-bearing: failure `model_proposal`. A reviewer who accepts a
    proposal enters a `reviewer_entry`.
    `test_a_model_s_proposal_carrying_a_full_decision_stays_proposed` builds a proposal that
    passes every other check and asserts its only failure is `model_proposal`; the shape
    assertions are gone.
12. **B-M1.** `ReviewerDecision.lower`/`upper`; `bounds_not_decided` when they differ from the
    record's (two cases: an edited `upper`, a decision without bounds).
13. **B-M2.** A reviewed null skips the evidence-sufficiency checks (supporting evidence, two
    families, exposure-only, evidence quality) and reads `reviewed_null`
    (`test_a_reviewed_null_for_thin_evidence_reports_the_reviewer_s_decision`, one family;
    a null with bounds is still `range_invalid`).
14. **B-M3, B-M8.** `Assessment.synthetic` is the record's, false with no record
    (`test_synthetic_describes_the_record_never_the_pack`, and the fixture-workspace
    integration test now asserts a role without a record is not synthetic). The slate's
    `ai_resilience_filter.synthetic` is true when a scored range is a synthetic record's, and
    its summary then says "synthetic fixture range here, not a real assessment".
15. **B-M6.** `AssessmentRecord.evidence_quality` (`limited`, `moderate`, `strong`; the words
    are provisional, R6), required for a range (`evidence_quality_not_stated`) and exposed as
    `ai_resilience.evidence_quality`; `widening_not_explained` for a range across bands with
    no `widening_reason`. The fixture has both.
16. **B-M7.** `test_discovery.py::test_a_published_range_is_filtered_on_its_lower_end_and_labelled_synthetic`:
    the labelled synthetic record moved onto the bicycle mechanic (test support
    `packs_scoring`), kept at a minimum of 5, left out at 6 with
    `below_ai_resilience_minimum`, `scored` and `below_minimum` asserted, `synthetic` true.
17. **B-M9.** `test_reference_data.py::test_an_unknown_occupation_is_not_found` (404
    `NOT_FOUND`) and `test_without_reference_data_the_evidence_is_unavailable_never_empty`
    (a fresh database with ESCO and no reference data: 503 `REFERENCE_DATA_UNAVAILABLE`
    through the endpoint).
18. **B-M10.** ADR 0010's status line and consequences now name decision 4 (the full-time
    tables), decision 8 (the 90th percentile; advertised pay read as gross) and decision 7's
    evidence-quality words; decisions 4, 6, 7, 8, 9 and 10 carry the round's amendments.
    Register AIR1-02/03/04/05, TAX1-06, DIV1-07 and JOB-03 cite the new tests; the runbook
    notes migration 0028's ASHE re-import.

Rulings I made: none beyond the controller's. Two small readings within them: one copy open
above keeps a job even when another copy of it is below (unknown beats below), and a
`+` counts only when attached to the amount (`£24,000+`), not after a space, under R11 (only
the reproduced form).

## TDD evidence (RED, then GREEN)

- Items 1, 3, 6 (A-I1, A-M5, A-M6): `pytest tests/domain/test_jobs.py tests/domain/test_pay.py
  tests/domain/test_extraction.py`: RED at collection (`FloorUnknown` had no
  `NO_UPPER_AMOUNT`; `StatedPay` had one amount). Before the fix, `salary_from("£24,000+ per
  annum")` read minimum = maximum = £24,000 (probe). After: 1,097 domain tests passed.
- Item 4 (A-M4): `test_reference_parsers.py` RED (`AsheEstimate` had no `cvs`), then GREEN.
- Item 5 (A-M3): the integration test RED (`'all_below_salary_floor' == 'sources_pending'`),
  then GREEN.
- Item 7 (A-M7): `test_floor_words.py` RED ("2 meet it" missing), then GREEN.
- Items 10–15: `test_ai_resilience.py` RED at collection (no new `PublicationFailure`
  members), then 40 passed. Integration RED: `ai_evidence.state` was `exposure_only` beside a
  published range; the filter output had no `synthetic` (`KeyError`). Then GREEN.
- Item 17 (B-M9): both cases passed on first run. They cover behaviour that already held, so
  they were never RED.
- Items 6, 8, 9 and 18 are words, a story and docs: no RED.

## Checks

- `make check` on `044ef12`: exit 0; backend 1,231 passed (fast suite), Vitest 212 passed;
  ruff, mypy, Biome, tsc, client drift and the fixture validator clean.
- `make acceptance` on `044ef12` (once): exit 0; 274 integration and stack tests passed
  (7 min 45 s; the stack's `setup-database` ran migrations 0027 and 0028 and imported the
  six pinned files), the Storybook build, and 28 Playwright journeys passed (2.3 min),
  including `storybook.spec.ts` "every story renders cleanly and passes axe", which covers
  the new `SlateWithSalaryFloor` story.
- Focused runs while iterating: the reference and discovery integration files, 25 passed;
  the floor and reference integration selection, 12 passed.

Client regenerated twice (`d1efff5`, `ca4cbea`). DBOS `application_version` does not change:
no workflow's step sequence changed (`nessa-l0-1`). No live call. Nothing in `.env` or
NESSA_HOME was read. Every file change was made with Edit or Write, except the generated
client (`pnpm run generate`).

## Concerns

- Migration 0028 removes the held ASHE import, and the next `setup-database` re-imports it.
  ASHE is public reference data; no person's data is touched.
- `evidence_quality`'s three words are mine (spec section 18 names the field only):
  provisional, R6.
- Parked as ruled: B-M4 (one record per `esco_uri`), B-M5 (`mapping_reviewed` tied to a
  mapping version).

## Proposed CLAUDE.md wording (updated; not edited)

The invariant bullet proposed above, as: "Pay and AI evidence (ADR 0010): ASHE is regional,
never a city's; modelled pay exists only through an accountable reviewer's UK SOC mapping
(none in L0); the AI Resilience Score is a reviewed range or unscored, never computed from
evidence, and exposure evidence alone never publishes one; a model's proposal never
publishes; the salary floor leaves out only pay whose stated top, in its own period, is
below it, never unknown, predicted, open-ended or other-period pay, and says what it left
out."

# Fix round 2 (FIX_BASE 044ef12)

Status: DONE. Commit `84dc858`. 1-A N2 and 1-B Minor 2 stay parked, as ruled.

## What changed

1. **1-A N1: recorded, rule unchanged.** The pinned 2026 provisional Table 15 (4) publishes
   no percentile at region x four-digit unit group, so the occupation floor (P90 in every
   region) can never remove a suggestion with this release, with or without a reviewed
   mapping.
   - ADR 0010 says so:
     - decision 4 gives the counts. 0 of 135,960 percentile cells are published, in any
       period. The median is published for 5,091 of 13,596 estimates, and the mean too.
       Table 15 (3), the three-digit minor groups, does publish percentiles and is not
       imported.
     - decision 8 says the floor never could remove a suggestion with this release. It
       explains why the rule is not changed here: a median or mean would remove careers
       where many jobs pay more, and a minor-group figure is a broad-SOC estimate.
     - the status line puts the statistic or geography to the product owner (R6), and the
       consequences list says the same.
   - DIV1-07 states the same fact.
   - The slice's ruling 6 in this report now says "always", not "often", unpublished.
   - **Pinned in the full-release test.**
     `test_reference_data.py::test_the_pinned_files_import_with_their_documented_counts`
     counts the pinned import's percentile cells: 135,960 present, 0 published, 5,091
     medians. A release that publishes percentiles fails this test and is noticed. The
     non-zero cell count guards against a vacuous zero.
   - **The synthetic sample** (`tests/support/reference_data.py`) withholds every four-digit
     percentile (`x`), as the real file does, except one labelled synthetic exception:
     `P90_EXCEPTION`, the Yorkshire 5231 annual P90 £24,000 with its own CV of 14.2. A comment
     says the real release never has it. The docstring is corrected.
2. **1-B Minor 1.** ADR 0010's status line now says fix round 1 "amended decisions 4, 7, 8,
   9 and 10" (fix round 2 decisions 4 and 8).

## Expectations that changed, and why

All follow from the sample now withholding percentiles like the real file. No product code
changed, and no behaviour changed.
- `test_reference_parsers.py::test_ashe_keeps_codes_regions_periods_pence_and_onss_markers`:
  - the data analysts' annual P90 is now withheld (`None`, `x`), not £52,000;
  - the P90's own CV is read from the exception row (14.2, beside its median's 8.4);
  - the float-artefact rounding case moves from a P90 to the bookkeepers' median
    (`24000.49999999999` gives 2,400,050 pence).
- `test_reference_data.py::test_an_occupation_s_pay_keeps_every_uk_soc_candidate_regional_and_unmodelled`:
  the data analysts' P90 is withheld, with cv null and band unreliable, as the real release
  shows it.
- `test_discovery.py`'s floor test is unchanged. It uses the labelled exception and still
  leaves the bicycle mechanic out.

## Checks

- `make check` on `84dc858`'s content: exit 0. Backend 1,231 passed, Vitest 212 passed.
- `pytest -m integration tests/integration/test_reference_data.py
  tests/integration/test_discovery.py`: 25 passed. The full-release test alone: 1 passed.
- `make acceptance` once on `84dc858`: exit 0. 274 integration and stack tests passed
  (7 min 35 s), the Storybook build completed, and 28 Playwright journeys passed (2.3 min).
  I ran it because two test files beyond the sample and the full-release test had
  expectations change: the parser test and the evidence integration test.

No live call. Nothing read in `.env` or NESSA_HOME. Every change was made with Edit or
Write. DBOS `application_version` is unchanged.

## For the controller

The R6 question for the product owner, in one line: "Table 15 (4) publishes no
percentile for a region and a four-digit occupation, so a salary floor checked against the
90th percentile can never leave a suggestion out. Keep that (the floor then only ever applies
to vacancies), or use another figure: the median or mean (removes careers where many jobs
pay more), or the three-digit group's 90th percentile from Table 15 (3) (a broader
occupation group, labelled as such)?"
