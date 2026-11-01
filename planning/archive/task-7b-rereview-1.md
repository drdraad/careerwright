# Task 7b re-review 1 (FIX_BASE 1c4bc07, HEAD 46de02d)

Scoped to I1, I2 and I3 and to M1, M2, M4, M5, M6, M7, M8, M10 and M11. M3 and M9 are parked;
for M9 I checked only that the fetch account is present.

How I checked:

- **Read-only, offline.** No page fetch, no Adzuna call, no Meta call, no subagent. I did not
  read `.env` or `NESSA_HOME`, and I did not re-run the suites.
- **What I read:** the diff, the committed pack, schema and package, the J01 capture in
  scratch, and the kept bodies.
- **What I ran:** three read-only scripts in scratch (`rr/`), through the backend's own
  environment.
  - The new `check_pack` over the pre-fix pack (`1c4bc07`) gives exactly 28 problems; over
    HEAD it gives none.
  - `accuracy_read.job_labels` over both versions of the pack.
  - A comparison of the two versions, claim by claim.

**Counts:** 10 items fixed, 2 partly fixed, 0 not fixed. New issues: Critical 0, Important
0, Minor 7.

## Verdicts by item

### I1: the package's gaps. Fixed

**The package is generated and checked.**

- `backend/tools/option_pack_files.py:371-425` writes it from the pinned pack, text and
  order included.
- `backend/tests/tools/test_option_pack_files.py:25-26` holds the committed file
  byte-for-byte to the tool's output, so the drift test is real.

**Every row the ruling asked for is present** in `docs/reviews/session-2-option-pack-questions.md`:

| What | Question |
|---|---|
| J06's first pay range | Q264, beside Q258's "unknown" |
| Entry requirements: C08, C02, C05's prerequisite, C06, C09 | Q109, Q126, Q141, Q152, Q165 |
| Essential credential or eligibility rows marked "no gate": `req:J05.5`, `req:J14.1`, `req:J15.4`, `req:J15.5`, `req:J10.2` | Q10, Q245, Q255, Q256, Q282 |
| Instrument kinds beside their claims: F01, F02 | Q176, Q192 |
| F03, which has no instrument-kind claim | Q204, shown as "(no claim)" |

- **A regression test pins these rows** (`test_option_pack_files.py:35-54`).
- **My coverage script, re-run, confirms it.** Every pay, money, date, duration and schedule
  claim is asked. So is every entry requirement and every essential credential or
  eligibility requirement.
- **Not asked, outside the ruling:** offering places (C02, C04 and C09's on-site address in
  Leeds), although job places are asked. This is optional and not counted as an issue.

### I2: the cut. Fixed

- **Three parts, in gate order** (`option_pack_files.py:279-303`):
  1. P01's section in full;
  2. P03–P05's options, offerings and outcomes, then the funding;
  3. P03–P05's jobs and requirements.
- **Each part gives its count and minutes:** Q1–Q65 (17 minutes), Q66–Q215 (38 minutes),
  Q216–Q331 (29 minutes), 331 rows in all. The minutes are `ceil(rows × 15 s)`, and they
  check out.
- **"Stop at the end of any part"** replaces "Answer these first" (package lines 19–30).
- **The partial-record rule** is stated in the package (lines 41–48) and in ADR 0011
  decision 14.
- **A test pins the parts** (`test_option_pack_files.py:57-75`): each record's rows lie in
  one part, part 1 is P01 only, part 2 holds no job row, and part 3 holds only jobs and
  requirements.
- **Funding sits in part 2, which is sound.** Part 1 does not include F01 to F03, but P01's
  own funding conditions are on `offering:C01`, which part 1 holds. TRACE-01's fixture uses
  no funding instrument.

### I3: value shapes. Fixed

**Declared once.** `_BY_SHAPE` builds `CLAIM_FIELD_SHAPES`, and `RECORD_FIELD_SHAPES` sits
beside it (`backend/src/nessa/catalogue/option_pack.py:543-613`). Both are validated
strictly (`_fits`, `_claim_values`, `:641-671`).

**The citing record field is checked whatever the claim's own field is called**
(`:660-670`). That closes all three of my original cases, each with its test:

| Case | Test (`backend/tests/domain/test_option_pack.py`) |
|---|---|
| C06's intake citing a list of past months | lines 300-310 |
| `valid_through`, now the "deadline" shape | lines 313-331 |
| A string range ("6-8") | lines 275-297 |

**The documentation is in place.** ADR 0011 decision 13 has the shape table, and the
committed schema states every shape and both maps (`x-value-shapes`, `x-claim-field-shapes`,
`x-record-field-shapes`).

**C04's duration** is now numbers, and **`offering:C06.intake`** is unknown, "no future
intake stated", with `C06.intakes_stated` kept as a fact on `option:C06`.

**The 28 problems** are exactly those the new checks report on `1c4bc07`. Each fix is
either a value change (the same information in its shape) or a reduction (information
dropped from the value):

- **18 value changes:**
  - the durations J05.contract_duration, J17.contract_duration, C01, C02,
    C02.duration_conflict, C05, C06, C07, C09 and F03.duration_limit;
  - the schedules C02.study_type, C06.study_type and C09.weekly_hours;
  - the rates C08.fee_per_year_home and international (`at_least: false` added);
  - C04.instalment ("from" became `at_least`);
  - C10.access_period, a dict made into the text "12 months" (see N3);
  - `offering:C06.intake`, made unknown with its claim kept as a fact.
- **10 reductions:**
  - **Legitimate, nothing proven lost:**
    - C02.location (Leeds and "delivered online" moved to the note and delivery mode);
    - C03.extra_cost ("hard copy" was never in its excerpt; the note keeps "certificate of
      completion");
    - C03.duration and C10.duration (their self-paced flags were not in "18 hours" or "60
      hours");
    - C04.location ("Remote");
    - C10.instalment ("interest_free" was never proven by "evenly with 3 Easy Payments");
    - C08.duration (the MNurs's 4 years belong to a different award; the note keeps them).
  - **Lost a label the committed excerpt proves:**
    - **C08.support_grant** dropped `repayable: false`. Its excerpt says "which they will
      not need to pay back", and neither the value nor the note now says so (N2).
    - **C04.duration** dropped the 12-month access, which its excerpt proves ("one year of
      24/7 access"). It is now only in the note (N1).
    - **C05.schedule** dropped "morning AND afternoon", which its excerpt shows. It is now
      only in the note.

  None of these is a scored label.

### M1: the split and tuning wording. Fixed

- ADR 0011 decision 7 says "no extraction was tuned on a holdout page", and records that the
  cross-class clause was added at assignment and moved C07 to development and C08 to
  holdout (`docs/adr/0011-england-option-pack-format.md:98-111`).
- The same is in `policy.holdout_split`, OI-09 (`corpus/manifest.json:52, 179`) and
  TEST1-09 (`docs/requirements-register.md:325`).

### M2: OI-13's names. Fixed (one nit, N7)

OI-13 (`corpus/manifest.json:183`) now lists C09.employer, J16's employer and advertiser
(pack, and package Q321–Q322), and C09.training_provider, each with where it appears.

### M4: the schema file. Fixed

- `england-option-pack.schema.json` is committed.
- `test_option_pack_files.py:29-31` holds it to `schema_text()`.
- It states the value shapes (`option_pack.py:845-853`).

### M5: occurrence counts. Fixed (exception: N4)

- **The locator** reports the real `count` (`backend/tools/corpus.py:152-170`, with a test
  at `test_corpus.py:196-205`).
- **Kept-body counts are exact** and match my own counts from the first review: C01.title
  8, C01.provider 13, C02.provider 29, F02.programme 11 and the rest.
- **Excerpt-only pages:** the 21 fetched ones record `occurrence_cap: 5`, as ADR decision 2
  documents.

### M6: excerpt-only values. Partly fixed

**The NHS Jobs places are reduced to postcodes.** J05, J06, J09, J10, J11, J13, J15 and J17
now hold only their postcode, with notes saying the address line names the site. The other
reductions the report lists (J12's place, contract types, pay bands, J10's pattern, J06 and
J19's requirements, J09's apply route, C03, C04, C08 and C10) check out against their
excerpts.

**One leftover the sweep missed:** `J19.working_pattern` is
`"36 hours; days or nights"`. Its excerpt on an excerpt-only page is
`Full time (36 hours) vacancies available`. "Days or nights" is not in the excerpt, and the
excerpt's "Full time" is not in the value.

**What it found otherwise:** my word-level sweep of every text value on the 21 excerpt-only
pages found nothing else that goes beyond its excerpt. The remaining hits are readings:
ISO dates for written dates, "+00:00" for "Z", "may close early" and the like.

**Fix:** set the value to "full time, 36 hours", or to what the excerpt shows.

### M7: two statements of one value. Partly fixed

**Done:**

- **J19's place** now matches J06. The record is `Unknown`, naming both claims, and
  `J19.location` holds the board's place as a valued fact.
- **The rule** "a bound is the label over a point at the same amount" is ADR 0011 decision 9
  (`:116-123`).
- **J01's pay** keeps the bound.

**Not done:** "Keep J01's header statement as a fact" was not met as ruled.

- **The new fact is a different statement.** `J01.salary_point` is the JSON-LD's single
  value, not the header's words, because the header was never located and cannot be without
  a fetch. The report discloses this.
- **The header is no longer mentioned.** The pack's own note on `J01.salary` no longer says
  the header shows "£28,000 per annum", although the old note did. So the header statement
  is now recorded nowhere in the pack.
- **The fact itself is honest** (named check 4 below).

**Fix:** restore the header mention in `J01.salary`'s note. Leave locating the header to
the next capture (Task 8 or 7c).

### M8: accuracy-read coverage. Fixed

- `read(..., evidence_dir=...)` takes the evidence directory
  (`backend/tools/accuracy_read.py:167-188`).
- **The holdout test is real** (`test_accuracy_read.py:170-187`). A recording fetcher
  shows that exactly 17 development pages are asked for, and no holdout URL.
- **The pacing test is now deterministic** on an empty directory, with exactly eleven
  5-second waits (`:156-166`).

### M10: ledger traceability. Fixed

J02's and J07's `why` name "ledger row 35". The ledger itself is unchanged.

### M11: rights wording. Fixed

- ADR 0011 decision 3 now says class `other` permits nothing and that C08's excerpts rest on
  R3 (`:52-58`).
- Decision 12 explains the C01 and C08 readings (`:135-144`).
- Both questions are in the OI-07 checklist, before any push (`corpus/README.md:134-142`),
  and in OI-07.

### M9 (parked): the fetch account is present

The report's "M9 (parked)" section covers the 255 fetches over 41 hosts, the scratch probes,
the loop bursts per host and the `curl`.

## Named checks

1. **Value shapes.** Declared once, and validated by the citing record field. All three
   original cases are caught, each by its own test. The 28 problems split into 18 value
   changes and 10 reductions, as listed under I3. Two reductions moved an excerpt-proven
   label into the note (C04's 12-month access, C05's "morning and afternoon"). One lost an
   excerpt-proven label entirely (C08.support_grant's "not repayable", N2).
2. **The package.** Generated by `tools.option_pack_files`, with a byte-exact drift test.
   It is ordered by gate (P01 in full, then P03–P05's options and funding, then jobs), asks
   every I1 field, and states the partial-record rule in the package and in ADR decision 14.
   ✅
3. **The re-cut.**
   - **Recorded honestly:** ADR 0011 decision 3 sets it beside `b38e462` and lists what it
     changed.
   - **The pin matches the file:** `PINS["0.1.0"]`, `corpus/manifest.json`
     `option_pack.sha256` and the file's SHA-256 are all `fe1f6669…cb328`.
   - **Frozen:** 0.1.0 is declared frozen in the ADR and the runbook. The freeze rests on the
     pin alone, because `publish()` will overwrite any version file (N6).
   - **One harmless change, unrecorded:** the canonical dump also changed `retrieved_at`
     from "+00:00" to "Z". The manifest test compares parsed datetimes, so this is
     harmless and needs no fix.
4. **J01.salary_point.**
   - **Its provenance is honest.** Its span (9842–9955), excerpt and value are verbatim the
     pipeline's own salary claim in the J01 capture (`captures/J01.json`). That capture's
     SHA-256 is the J01 source's hash, so the offsets index the hashed text, and the note
     calls the value "the structured data's single value".
   - **Its occurrence count is not honest by the format's own rule.** `occurrences` is left
     at its default of 1. Under ADR decision 2 and the `Claim` comment, a count below the
     source's `occurrence_cap` is exact, so the pack asserts exactly one occurrence while
     the note says the count was not taken (N4).
5. **The accuracy-read claim.** Confirmed offline from committed data, with the scorer's own
   `job_labels` over both pack versions.
   - **Only one scored label changed:** J12's place. Its old and new labels both score the
     capture's "manchester" reading as `correct` under `_same`.
   - **J19's place** is unknown in both versions, and **J01's pay** is unchanged.
   - **Course and funding counts** are identical: C01 16, C03 11, C04 13, C07 16, C09 17,
     C10 11, F01 19, F03 9.
   - **The evidence doc** says the read was not re-run.

## New issues introduced by the fixes

### Critical

None.

### Important

None.

### Minor

**N1. C04's duration is an average stored as bounds** (pack line 410, `C04.duration`). The
page gives "an average completion time of 6-8 months" with "one year of 24/7 access". The
value is now `{months, minimum 6, maximum 8}`, while its own note says "not a bound". The
proven 12-month access survives only in the note. C04 is in P01's option set, the one
TRACE-01 runs on.

**Fix:** keep the access period as its own duration fact, maximum 12 months. Mark the
typical range as typical: a `typical` flag on `DurationPart`, or a separate fact.

**N2. C08.support_grant lost "not repayable"**, which its excerpt proves ("which they will
not need to pay back"). `Rate` has no field for it, and the note does not say it. Grant
against loan is consequential for Task 12 (OPTN-06).

**Fix:** add `repayable: bool` to the rate shape, or say it in the note.

**N3. Duration and schedule facts left as text, outside the shapes.**

- **C10.access_period** was turned from `{"months": 12}` into the text `"12 months"` to pass
  the checks.
- **Working patterns** in text: `J14.working_pattern` "37 hours a week, Monday to Friday"
  and `J19.working_pattern` "36 hours; …" hold weekly hours as text.

**Fix:** map `access_period` to the duration shape and `working_pattern` to the schedule
shape (or a pattern-plus-hours shape).

**N4. `J01.salary_point.occurrences` reads as an exact 1.** The count was not taken, but the
format cannot say "not counted", and decision 2 treats counts below the cap as exact.

**Fix:** let `occurrences` be null for "not counted", or state the exception in decision 2
and the `Claim` comment.

**N5. The misleading-title case now rests on the note alone** (C03). The value became
"Safeguarding Level 3 Course", which drops "Adult Nursing &", the misleading words. The
`misleading_course_title` case now rests on the note and the URL, not on a span. This is
disclosed as a concern.

**Fix (Task 8 or 7c recapture):** locate the title with its entity written out
(`Adult Nursing &amp; Safeguarding Level 3 Course`), as other excerpts keep entities.

**N6. `publish()` will overwrite a frozen version** (`backend/tools/option_pack_files.py:432-442`).
It writes `england-option-pack-<version>.json` for any version, 0.1.0 included. The freeze
holds only so long as `PINS` is not edited.

**Fix:** refuse to write a version already in `PINS`.

**N7. OI-13 says "KAPLAN FINANCIAL LIMITED" is in the option pack only**
(`corpus/manifest.json:183`). The C09 slot's `why` (`corpus/manifest.json:154`) also names
"Kaplan".

**Fix:** add that place.

## Not verified

- **The `make check` and `make acceptance` runs.** I did not re-run them.
  - The report runs `make check` green and skips `make acceptance` on the ruling's
    condition.
  - I confirmed that no product module imports `nessa.catalogue.option_pack`: only its
    tests and the tools do. So the skip is defensible, and the controller decides.
- **Spans on excerpt-only pages** still cannot be checked against text. Their bodies are not
  kept.
