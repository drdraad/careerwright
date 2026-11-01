# Task 7b review: the England option pack (BASE 5b33f6b, HEAD 1c4bc07)

One reviewer, read-only. I made no live calls (no page fetch, no Adzuna, no Meta), dispatched
no subagents and did not re-run the suites. I read the brief, the dispatch notes, the report
and the diff in passes: code and tests first, then ADR 0011, the docs, the manifest and the
package, then the pack JSON (spot-checked, as the skip list asks). The checks outside the diff
were these:

- the kept bodies in `var/evidence/corpus/` (read-only), to check spans;
- `git log --name-status` and `git ls-files` over the range;
- the implementer's scratch outputs (`scratchpad/out/read-*.json`, `out/questions.md`,
  `out/pack.json`, `notes/split-rule.md`, `scripts/build.py`), only to check the report's
  numbers and its timeline.

## Spec Compliance

- ❌ **Issues found:**
  - **The session 2 package is incomplete** against the brief ("every consequential field ...
    beside its span") and against its own definition (`docs/reviews/session-2-option-pack-questions.md:6-10`).
    It never asks J06's first pay range, any course entry requirement or prerequisite, or the
    essential credential and eligibility requirements left ungated (Important I1).
  - **The "Answer these first" list is not a sound cut** for the gates session 2 must close
    (Important I2).
  - **The pack format is not yet "boring" for Tasks 9 and 11.** Claim values are untyped
    beyond money, pay and dates. The shape check keys on the claim's own field name, so a
    record field can cite a claim the check never sees (Important I3).
- ✅ **Met:**
  - 33 slots, each with URL, retrieval time, hash, rights status, template family, split
    and labels (`corpus/manifest.json`, cross-checked by a fast test).
  - The pack parses and `check_pack` passes. Every record is `proposed` and dated.
  - No synthetic marker is in the pack, and no page body is in git.
  - The early accuracy read is reported field by field, with denominators, and labelled
    "unreviewed labels, development split".
  - The register rows TEST1-09, OUT1-10, OPTN-08 and OPTN-10 are updated and stay "planned".
  - `label_review`, H-07, OI-07 (C08's rights review) and the pre-push name review stay
    "not run - requires human".
  - Ledger rows 34 and 35 were added, and no Meta call was made.
- ⚠️ **Cannot verify from diff:**
  - **Spans on the 24 excerpt-only pages.** These are the job-board pages, C03, C04, C08,
    C10 and the Adzuna response. Their offsets come from captures that are not kept, so only
    each value against its own excerpt can be checked.
  - **Robots.txt and terms beyond what was recorded.** I cannot see whether Reed's or NHS
    Jobs' robots.txt sets a crawl delay, or whether their terms restrict automated access
    beyond the copying clause recorded. Checking would need a live fetch.
  - **The RED runs claimed for the TDD steps.** I confirmed `7ede59e`'s RED by reading the
    pre-fix `_hiring`: both new cases would have read `EMPLOYER`.
  - **The `make check` and `make acceptance` results.** I did not re-run them.
  - **The split timing.** Git cannot prove when the splits were set, because the pack and
    its splits were first committed in `cbf5de0`, after the fix `7ede59e`. The timing is
    corroborated outside git:
    - `notes/split-rule.md` was created at 10:31:42 UTC, before F01's capture at 10:31:48;
    - `out/read-before-fix.json` (11:41:05) lists development slots only.

### Named risks: what I checked and found

1. **Rights per page.** I read every source's `rights_status` in the pack and listed
   `var/evidence/corpus/`.
   - **Job boards:** all 20 job slots and C03, C04 and C10 are `job-board` with
     `retention: excerpts`. No body is kept for any of them.
   - **C08:** `other`, "pending human rights review", excerpts only.
   - **Kept bodies:** exactly C01, C02, C05, C06 (A3), C07, C09, F03 (A2), F01 and F02 (A1),
     each hash-matched to its file.
   - **Terms:** each record quotes the terms it relied on, with a date. Find an
     Apprenticeship and the National Careers Service are named in A2, and F03 states the OGL.
   - **Open points:** two Minors, both rights-review questions rather than breaches (M11).
     - ADR 0011's wording about which excerpts the policy allows.
     - The C01 "all rights reserved" versus C08 "may not be reproduced" distinction.
2. **No unpermitted body in git.** I checked every commit in the range (A/M only), and
   `git ls-files` shows no HTML body.
   - **Excerpt lengths:** the longest of 479 is 157 characters, under the 200 limit. The
     longest note is 259 characters and quotes no page.
   - **The docx:** `~$ssa_Local_Development_Plan.docx` is untracked. Only the pre-existing
     `Nessa_Local_Development_Plan.docx` is tracked.
3. **Names.** I scanned the committed pack, the manifest, the package, the evidence doc, the
   ADR and the README.
   - **Emails and phone numbers:** none. The only phone-shaped strings are NHS job
     references.
   - **Personal names:** the only one is "Martin Hirst" in C09.employer. It is in OI-13 and
     in neither the package nor the evidence doc.
   - **OI-13 is incomplete:** see M2.
4. **Labels with spans.** All 132 kept-body claims match their bodies at their offsets
   (whitespace-normalised), confirming the report's count. I checked about 25 values in
   context or against their excerpts. All were right:
   - **Course pages:** C01.fee_total (null, "fully funded"), C02's 14 weeks against 12
     weeks, C02 £900, C05.fee_total (null), C06 £1,265 and its condition, C06's 1 year,
     C06's assessment, C07 £0.00, its 16 November 2026 start and its residency list.
   - **Apprenticeship (C09):** the £14,560 wage, 35 hours, the 4 January 2027 start, the
     closing date of 30 November 2026 and the 18 months.
   - **Funding pages:** F01's £25,750 earnings rule, F02's age, levels and LLE rule, and
     F03's null cost.
   - **Job pages:** J01 "Up to £28,000", J03 predicted 3427531, J05, J09's pence-exact
     range, J14 £16.37 an hour, J17's contract end and J19's hourly and annual figures.
   - **Excerpt-only courses:** C04 £2,995 and "from £69.52/month", C08 £10,050 a year, and
     C10 £295 with no exam fee.

   **Two statements of one value** stay unknown for J06's pay, C02's duration and J19's
   place. Two inconsistencies remain (M7).
5. **Split before the read (OI-09).** `read()` skips every non-development source
   (`backend/tools/accuracy_read.py:178`).
   - **All three read outputs** list only the 20 development slots.
   - **`7ede59e`** was reproduced on J01 and J12, Reed pages. Reed is the first job family,
     so it is development under any reading of the rule.
   - **No holdout page was tuned on.** The rule as recorded, however, has a cross-class
     clause the pre-fetch note lacks (M1).
6. **The pack format.**
   - **Checks in `make check`:**
     - pytest loads the committed version through its pin (`load_pack`), parses it strictly
       and runs `check_pack`;
     - the manifest and the pack are cross-checked;
     - a JSON Schema is exported but not committed (M4).
   - **Versioning:** `format_version` and `pack_version` are present, and each version is
     pinned by the SHA-256 of its file.
   - **The `b38e462` change** to the committed 0.1.0 is recorded honestly. ADR 0011 decision
     3 says so, and the commit message states that the pin moved in the same commit. It is
     harmless: nothing was pushed and nothing consumes the pack. No new version is needed for
     that change.
   - **Typing:** the value typing is the real gap (I3).
7. **Nothing synthetic.**
   - **The committed pack:** no `fixture:` mark, no example host, no "synthetic" outside the
     `synthetic: false` header.
   - **The validator** refuses `synthetic: true`, `fixture:` in claim values and `.example`,
     `.test`, `.invalid` and localhost hosts. Its coverage is narrower than the report
     implies (M3, R12).
8. **The accuracy read.**
   - **Path:** deterministic only (structured data), with no model call. The doc is labelled
     "unreviewed labels, development split" and gives denominators.
   - **Counts:** every number in `docs/evidence/option-pack-accuracy-read.md` matches the
     tool's own outputs: the totals, all 11 per-field rows, the pre-fix advertiser row, and
     the course 84 and funding 28.
   - **Run sequence:** before the fix 75/3/8/8/5, after the fix and in the final run
     74/2/10/9/4. The after-fix and final runs agree page by page.
   - **J19:** its advertiser went from `correct` to `missing`, honestly reported.
   - **`7ede59e`** is fail-safe (unknown), carries a regression test, and its ADR 0009 rule
     is updated.
   - **Adzuna:** the J02, J03 and J07 adverts are not scored, which is disclosed (M8).
9. **The session 2 package.** It has 314 rows, identical to the generated `out/questions.md`.
   They are grouped by persona target, each beside its span, and are usable by a person.
   - **Gaps:** it is not complete (I1).
   - **The cut:** "Answer these first" is about 37 rows, or 10 minutes, including the 10
     provisional outcome rows. It is a list of the agent's judgement calls, not a cut that
     closes session 2's gates (I2).
10. **Live calls and pacing.**
    - **Ledger rows.** Both purposes say "corpus J03". That is the slot each request was made
      for, so it is right as intent.
      - **Row 34** (bookkeeping assistant, Leeds) filled nothing.
      - **Row 35** (IT support technician, Bristol) filled J02, J03 and J07.
      - **The manifest traces it.** J03's `why` names both rows, and J02 and J07 carry
        `shares_response_with`.
      - **What to do:** leave the append-only ledger as it is (M10).
    - **Pacing** falls under R12 and belongs on the final-review list. It is not a fix for
      this task (M9):
      - no Global Constraint covers per-host pacing, and robots.txt was read and obeyed on
        every visit;
      - the product worker path is unaffected;
      - the 5-second figure is the product's own default for hosts it does not list, not a
        limit a site stated;
      - the accuracy read now uses one pacer, tested, and the README and runbook warn.

## Strengths

- **An honest report.** Its rule incidents, the pacing breach, J19's regression and the
  post-commit change to 0.1.0 are all stated plainly, and each checked out.
- **Rights handled conservatively.** Bodies are kept only where the class permits. Job
  boards and the doubtful page (C08) stay excerpt-only, and every page records the terms it
  relied on, quoted and dated.
- **Precise spans.** All 132 kept-body spans match exactly.
- **`--locate` checks its own text.** It re-derives the redacted text and checks its hash
  before locating anything (`backend/tools/corpus.py:200-204`). For excerpt-only pages the
  offsets therefore come from the very capture that was hashed.
- **A strict format with real cross-checks.**
  - Strict Pydantic models refuse unknown keys.
  - A field is either a cited claim or an `Unknown` with a reason.
  - Every claim must be cited, and a record may cite only its own sources.
  - One template family may not span both splits.
  - A level is refused without a rubric.
  - The manifest and the pack are cross-checked field by field in the fast checks.
- **The one pipeline fix is fail-safe and covered.** It is reproduced, has a regression
  test, and its rule is written into ADR 0009 decision 6.
- **The Adzuna corpus path reuses `live-adzuna`'s guards.** `search()` keeps the cap under
  the ledger lock, the $0 ledger row and the leak scan. The refactor preserves behaviour:
  the locations are `result n`, so the new `split(":")` count is equivalent.

## Issues

### Critical

None.

### Important

**I1. The session 2 package leaves out consequential labels**
(`docs/reviews/session-2-option-pack-questions.md:6-10, 49-51, 59, 211`).

The package says it covers "every consequential field of every record". It defines that as
including "pay and its basis, ... gates, eligibility rules and the conflicts a page leaves
open". The generator, though, asks only a fixed list of fact names (`scripts/build.py`,
`FACTS_ASKED`), and the options' `entry_requirements` are never asked.

What is never shown beside its span:

- **J06's first pay range.** `J06.salary` is £17.50–£20.23 an hour, "£17.50 to £20.23 an
  hour" (pack line 140). It moved to facts in `b38e462`, and `salary` is not in
  `FACTS_ASKED`.
  - Q129 asks only that the record's pay is unknown, with no span.
  - "Answer these first" still says Q129 and Q135 are "J06's two pay ranges".
- **Course entry gates.** These are every course entry requirement and prerequisite:
  - `C02.entry_requirement`, `C06.entry_requirement`, `C08.entry_requirement` (A levels
    BBC) and `C09.entry_requirement` (GCSE grade 4);
  - `C05.prerequisite` (the AAT level 2 certificate with merit or distinction, pack line
    423).

  These are the options' prerequisites, the inputs a route's feasibility turns on.
- **Ungated essential requirements.** Five requirement rows of kind credential or
  eligibility carry `gate: null`:
  - `req:J05.5` (a degree);
  - `req:J10.2` (travel between sites);
  - `req:J14.1` (NVQ level 3);
  - `req:J15.4` ("Valid UK driving license", pack line 559);
  - `req:J15.5` (A level).

  The package skips unmapped, ungated rows, so the reviewer never sees the "no gate"
  judgement on any of them.
- **The kind of instrument.** Q275 and Q291 show the record's instrument kind as "(record)",
  never beside `F01.instrument_kind` or `F02.instrument_kind`.

**Why it matters.** H-07 is the only review these labels get before Task 7c publishes the
reviewed version. A value never shown cannot be accepted or corrected. A wrong entry gate,
or a missing one, changes a route.

**Fix:**

- Ask every fact whose field is a pay, money or date field, including `salary`.
- Ask each option's `entry_requirements`.
- Ask every essential requirement of kind credential or eligibility, gated or not.
- Show the instrument-kind claims beside their spans.
- Regenerate, and update the count, the time and "Answer these first". It adds about 13
  rows, or 3 minutes.

**I2. "Answer these first" is not a sound cut for session 2's gates**
(`docs/reviews/session-2-option-pack-questions.md:13-14, 54-67`; report, "Session time").

Session 2 is 2½ hours. Besides H-07 it holds H-13 (30 minutes), H-01 for Sprint 2, and the
TRACE-01 checker on P01's real option set (plan section 10). That leaves the 80-minute
package no slack, and the report proposes the cut as the fallback.

**What the cut is.** About 37 rows: the agent's judgement calls (conflicts, bounds, unknown
fees, gates, award states) and the 10 provisional outcomes.

**What it leaves out:**

- **Pay:** every stated pay value and basis except J01's and J19's bounds. That includes
  J03's predicted basis (Q76), the corpus's one real predicted-pay case (OI-04).
- **Fees:** every stated fee, with its instalments:
  - C02 £900, C03 £19, C06 £1,265, C07 £0, C10 £295;
  - C04 £2,995 and its "from £69.52/month" instalment;
  - C08 £10,050 a year.
- **Wages:** C09's apprenticeship wage.
- **Dates:** every intake, deadline and duration but C02's. That includes C06's two past
  intakes (Q256) and C04's "6-8 months".
- **Funding rules:** every one but F01's earnings rule, among them F02's repayment (Q296,
  which cites an F01 claim).
- **Outcomes:** the eight `unsupported` outcomes, seven of them topic mentions. OUT1-10 says
  these are reviewed one by one, and they are the rows Task 10 blocks on.

**Why it matters:**

- **No record would finish review.** The cut cuts across records, so answering only it
  leaves every record part-answered.
- **Partial answers are undefined.** The package never says what Task 7c does with a
  part-answered record.
- **The gates would go unclosed.** A session that answers only the cut would close neither
  H-07 for Sprints 4–5 nor the TRACE-01 review of P01's option set.

**Fix:** order the package by the gates it closes.

1. **P01's section in full** (Q1–Q63, about 16 minutes): TRACE-01's real option set.
2. **P03–P05's course and funding rows:** the option, offering and outcome rows, then the 40
   funding rows. That is Sprints 4–5, about 35 minutes.
3. **P03–P05's job and requirement rows last** (109 rows, about 27 minutes). Task 8 can take
   up any that are left.
4. **State the partial-record rule:** a record becomes `reviewed` only when every one of its
   rows is answered yes, and otherwise stays `proposed`.

**I3. Claim values are untyped beyond money, pay and dates, and the shape check can be
bypassed** (`backend/src/nessa/catalogue/option_pack.py:155, 362-371, 410-424`;
pack lines 410, 431, 482, 644, 646).

**How the check works.** `Claim.value` is `JsonValue`, and `_claim_values` checks a shape
only by the claim's own `field` name. A record field can therefore cite a claim the check
never sees. This is reproduced in the committed pack:

- **`offering:C06.intake`** cites `C06.intakes_stated`, whose value is `["2026-02",
  "2026-03"]`. That is a list, never date-checked, of two months before the retrieval
  date. The claim's note says so, yet the record presents them as the offering's intake.
- **Deadlines:** `valid_through` (16 claims) is not in `DATE_FIELDS`, so no deadline is
  shape-checked.
- **Durations** take six ad hoc shapes:
  - `{"weeks": 14}`, `{"years": 1}`, `{"months": 18}`;
  - `{"hours": 60, "self_paced": true}`;
  - `{"full_time_weeks": 10, "part_time_weeks": 17}`;
  - `{"typical_months": "6-8", "access_months": 12}`: a string range, on C04, in P01's
    option set.
- **Schedules** are `"part time"`, a sentence, or the integer `35`.
- **Instalments** take two shapes, and neither is checked as money.

ADR 0011 documents no per-field value shapes. The exported JSON Schema says nothing about
values.

**Why it matters.** Tasks 9 and 11 "load it through their domain models". Task 11's
TRACE-01 checker runs next, on P01's option set, which holds the string range. Each consumer
would have to reverse-engineer the shapes. A past intake could be scheduled as the
offering's intake. Typing values later is a format change, which means a format bump under
a reviewed version.

**Fix:**

- **Document the shapes** in ADR 0011, one value shape per citing record field: money, pay,
  ISO date or month, datetime, duration, schedule and instalment.
- **Validate by the record field** that cites a claim, not only by the claim's own name.
- **Normalise C04's duration** to numbers.
- **Make C06's intake unknown** ("no future intake stated"), keeping the claim as a fact.
- **Publish before Task 9.** Either re-cut 0.1.0 under the same "unpushed, no consumer"
  ruling as `b38e462`, recorded the same way, or publish 0.1.1. The controller decides
  which.

### Minor

**M1. The split and tuning records overstate the rule**
(`docs/adr/0011-england-option-pack-format.md:73-80`; `corpus/manifest.json:52, 179`;
`docs/requirements-register.md:325`).

- **"No extraction was tuned on any page"** (ADR decision 7, OI-09) contradicts `7ede59e`,
  a fix made from J01 and J12, both development pages.
- **TEST1-09's register row** says the splits were "assigned ... before the first fetch".
  Only the rule was written before the first fetch.
- **The pre-fetch note lacks a clause.** `notes/split-rule.md` (10:31:42) does not have
  "A family keeps the split it first got in every class". Under the literal pre-fetch rule,
  C04's family would be course group 4, so C07 would be holdout and C08 development. The
  pack has them the other way round.
- **No harm followed.** No course page was tuned on, and the path has no course reader.

**Fix:** say "no extraction was tuned on a holdout page". Then record that the cross-class
clause was added when assigning, and what it changed.

**M2. OI-13 is incomplete** (`corpus/manifest.json:183`). It lists C09 only and says no
other committed excerpt or value holds a personal name. The report itself flags J16's
"PRATAP PARTNERSHIP LTD" (pack line 284, package Q216–Q217), and the same reasoning covers
`C09.training_provider` "KAPLAN FINANCIAL LIMITED" (pack line 478). The pre-push review reads
OI-13. **Fix:** list both, with where each appears.

**M3. The validator's coverage is narrower than the report says** (R12; for the final
review) (`option_pack.py:50, 388-397, 528-537`).

- **Hosts it lets through:**
  - `example.org` and `example.com`, which the repository's own tests use;
  - IP-literal hosts such as 127.0.0.1, the controlled test server's address.
- **`fixture:` is scanned in claim values only.** Excerpts, notes and record text are not
  scanned.
- **Unchecked references:**
  - `LearningOption.target_ids`, `Skill.target_id` and records' `source_id` and
    `source_ids` are never checked against the pack.
  - A wrong source shows up only indirectly, through "not from its own source".

None of these forms is in the pack.

**M4. `schema()` claims a committed schema file** (`option_pack.py:635-637`). It names
`england-option-pack.schema.json` "committed beside the packs", but no such file exists. **Fix:**
commit the export with a drift test, or correct the docstring.

**M5. `Claim.occurrences` caps at 5** (`option_pack.py:158`; `backend/tools/corpus.py:64,
160`). It is documented as the excerpt's count in the text. The tool lists at most 5, so
eight claims say 5 where the text holds 8–29: C01.title has 8, C02.provider and C05.provider
29, F02.programme 11. **Fix:** document the field as "at least" past the cap, or record the
real count.

**M6. NHS Jobs location claims cite only the postcode.** The value holds the full site or
street: J05 is `"Estuary Point/Middlebrook/Parkway, M14 7LU"` against an excerpt of
`M14 7LU` (pack line 123). J06, J09, J10, J11, J13, J15 and J17 do the same. These pages keep
no body, so the committed excerpt does not prove the label. **Fix:** cite the address span,
which fits within 200 characters, or reduce the value to what the excerpt shows.

**M7. ADR 0011 decision 9 is applied unevenly.**

- **J19's place** is a null-valued claim (pack line 331). The board's "Greater Manchester"
  is not kept as a value, unlike J06 and C02, where both statements are valued facts and the
  field is `Unknown`.
- **J01's pay.** The header's "£28,000 per annum" against the advert's "Up to £28,000" is
  resolved as an upper bound, not left unknown, and the header statement is not kept as a
  claim (pack line 67, asked at Q64).

**Fix:** represent J19 the way J06 is represented. Then either keep J01's header statement
as a fact, or state in ADR 0011 the rule that a bound subsumes a point value.

**M8. Accuracy-read coverage** (`backend/tools/accuracy_read.py:178`;
`backend/tests/tools/test_accuracy_read.py:143-161`).

- **No test pins the holdout skip.** The pacing test would still pass if holdout pages were
  read.
- **The pacing test reads private bodies.** When the gitignored bodies are present it reads
  them, so it behaves differently in a clean clone.
- **The Adzuna path is unscored.** The brief names "structured data and Adzuna". The labels
  for J02, J03 and J07 are the adapter's own readings, so their only independent check is
  H-07 (Q70–Q85). This is disclosed.

**Fix:**

- Add a test that `read()` over a pack with a holdout source touches no holdout page.
- Inject the evidence directory.

**M9. Pacing (R12; for the final review).** `tools.corpus` paces within one process. The
capture loops sent same-host requests about a second apart: eight to reed.co.uk, and three to
leedscitycollege.ac.uk within 0.7 seconds. The first two accuracy reads had no cross-page
pacing.

- **What was done:** the read is fixed with a test, and the README and runbook warn.
- **What is not counted:** the labelling probes in scratch (`probe.py`, `raw.py` and
  `jsonld.py`, each one `acquire_page` in its own process) are further same-host fetches.
  The report's fetch account leaves them out.
- **Why R12:** no Global Constraint or failing check requires a fix here. **Fix (final
  review):** a batch mode with one pacer, or a pacer shared across processes, plus a full
  account of the probes.

**M10. Ledger traceability.** The purpose of rows 34 and 35 names the requested slot, J03,
which is right. J02's and J07's slot records name no ledger row
(`corpus/manifest.json:127`). **Fix (optional):** name row 35 in J02's and J07's `why`. Never
edit the ledger.

**M11. Rights wording and one consistency question** (`docs/adr/0011-england-option-pack-format.md:44-47, 100-104`).

- **Decision 3 overstates the policy.** It says the session 1 policy "lets every class's
  excerpts be committed". Class `other` permits nothing under A7 (manifest `permitted:
  []`).
- **C08's excerpts rest on R3, not the policy.** Its 18 committed excerpts (1,322
  characters, the most of any page) stand on R3's default for pending pages. Yet the page is
  pending precisely because its notice forbids reproduction.
- **Decision 12 leaves a distinction unexplained.** C01's "©Copyright 2026 all rights
  reserved" gets its body kept under A3, while C08's "may not be reproduced without
  permission" goes pending.

**Fix:**

- Correct the wording.
- Add two questions to the OI-07 rights checklist, both before any push: may C08's committed
  excerpts stay, and should C01 and C08 be treated alike?

**M12. Process incidents.** Both were disclosed, and neither has a code consequence. One
`curl` read robots.txt outside the product's fetcher, and one `sed -i` edited an import
line. **Fix:** none. Record them in the ledger.

## Assessment

**Spec compliance:** ❌ Issues found (I1, I3)

**Task quality:** Needs fixes

**Reasoning:** The corpus, rights handling, spans, pin and accuracy read are sound, honestly
reported, and match the tool's own outputs. Three things need fixing before Task 9 and the
human session:

- The session 2 package leaves out labels that change routes: J06's first pay range and the
  courses' entry gates.
- Its fallback cut would close none of session 2's gates.
- The format's claim values are too loosely typed for Tasks 9 and 11. One record field
  already slips past the date check.

**Counts:** Critical 0, Important 3, Minor 12.
