# Task 7f review (first half): option pack 0.3.0, its labels, the batch mode, the session package

Reviewer: the one independent reviewer (R16), 2026-11-01. Package `review-e364ded..fc5b8f5.diff`
(4,829 lines, read in passes: option_pack.py, the 0.3.0 file and schema, tests, corpus.py,
option_pack_files.py, the labels, school_leaver_pack.py, README, manifest, ADR, register,
package). Code read in `/home/user/careerwright-wt/7f` at fc5b8f5; kept bodies read in
`var/evidence/corpus/<slot>/`. Read-only; no web request, no suite re-run.

**Verdict: Needs fixes.** Critical 0, Important 4, Minor 7.

## Spec compliance

- ❌ Issues found:
  - The Lifelong Learning Entitlement loans leave out the age rule their own page states
    (Important 1).
  - Two key rules carry their deciding words outside their cited excerpt (Important 2).
  - The bursary is labelled "grant", which planning treats as never repaid, while the record
    says repayment is unknown (Important 3).
  - Some session rows can't be answered from the page and use internal words (Important 4).
- ⚠️ Cannot verify from the diff: the `make check` result (not re-run; the report's claim);
  `make acceptance` (the controller runs it); human review of every row: not run — requires
  human (H-07).

## The named risks, checked

1. **Every value is a claim whose excerpt sits exactly at its span.** A script read every
   one of the 109 new claims against its kept body. The SHA-256 of each body matches its
   source, and `body[start:end] == excerpt` holds for all 109; none fails. Beyond that,
   26 claims were read in context for meaning:
   - loans: F05 tuition and three maintenance caps, F05.timing×2, F12.loan_maximum ×3,
     F12.repayment, F12.rule_tuition_left, F08.timing, F09.repayment, F13.plan_5 ×2,
     F07 threshold;
   - age and residency rules: F04.rule_age, F04.employer_share, F04.timing,
     F06.rule_residency.three_years, F06.rule_age_limit.maintenance, F06.rule_course,
     F12.rule_residency.three_years, F10.rule_age_exception, F10.bursary_maximum,
     F11.rule_age;
   - other: F09.alternative_if_eligible, C11.subject_accounting, C11.classroom_hours.

   The values are true to the pages. The caps are in the 2026 to 2027 column. Plan 5 is
   £25,000 a year. F04 says 100% for ages 16 to 24 at an employer that pays no levy.
   Nothing unknown is shown as £0: C11's fee, F10's repayment and C09's fee are each
   unknown with a reason. The exceptions are Important 1 to 3.
2. **Two disagreeing values on one page.** None found. F05's two year columns are labelled
   years, not a conflict. F10 ("aged 16 to 19") and F11 ("under 19 on 31 August 2026") are
   different pages, each kept as its own words.
3. **The January 2027 split.** It is stated truthfully. F05 and F05.maintenance hold the
   2026 to 2027 caps, and F05.rules_change quotes "If your course starts on or after
   1 January 2027". F12 and F12.maintenance hold the Lifelong Learning Entitlement amounts,
   with "most undergraduate" kept as the page's word. `offering:C08` is unchanged, no
   record links a loan to it, and the notes say "if it is one of those courses". The
   nursing degree's loans are not claimed either way. (One gap in F12: Important 1.)
4. **The `limit` shape.**
   - It is needed: `rate` is an exact amount, and has no "up to".
   - It is checked strictly through `SHAPES` (option_pack.py:430, 576–587). A test refuses
     text and a negative cap.
   - The change only adds: the schema diff adds `limit` and five field names and removes
     nothing.
   - 0.1.0 and 0.2.0 still check. The only product readers pin 0.1.0 or 0.2.0
     (capability/commands.py:75).
   - `planning/pack.py` passes funding facts on as plain values and reads `minor_units`
     only for fees and instalments (`_minor`, pack.py:392), so a `limit` is never read as
     money.
   - Keeping `format_version` 1 is honest: older code would refuse a 0.3.0 file, but no
     older reader exists outside the repository.
5. **Pins.** `sha256sum` matches PINS for 0.1.0 (d7ff…), 0.2.0 (162d…) and 0.3.0 (47f9…).
   `git diff e364ded fc5b8f5` touches only the 0.3.0 file and the schema in `packs/`.
   0.3.0 loads through `load_pack`. A test checks that the committed file is exactly the
   tool's output and matches its pin, so the disclosed `sed` edit of the pin line left
   the right value.
6. **Synthetic content, bodies and rights.**
   - Nothing synthetic is in the pack: `synthetic: false`, and no fixture or school-leaver
     wording appears.
   - No page body is in the diff. The labels hold excerpts only; no string is over 400
     characters.
   - C12 (UCAS) has no body directory, its retention is `excerpts`, and it is "pending
     human rights review".
   - The 11 used pages are class `govuk`, with the session 1 terms quoted.
   - Every slot records `fetch_route` with via_proxy true and address_checked false; the
     pack's notes say the same.
   - Split: the new pages join the existing families. `govuk-mainstream-guide` is holdout,
     as F02 already was.
7. **The session package.**
   - Every item is "not run — requires human", and the file says so up front.
   - The rows that change a route come first (Q1–Q112).
   - Session 2's F02 rows are not asked again (a test checks this).
   - Its wording is not plain enough, and some rows can't be answered from the page
     (Important 4).
8. **Batch mode.**
   - `main` builds one fetcher (`fetcher_from`) and `corpus_batch` one `Pacer`, and every
     entry goes through the unchanged `acquire_for_corpus` → `acquire_page` path, so
     robots.txt, the manifest class, redirects and size limits are still checked.
   - Every entry is checked before any fetch (`load_batch`, `extra="forbid"`; a class
     needs its terms).
   - Single-page options are refused with `--batch`.
   - `--context` is capped at 100 characters each side.
   - Tests cover proxy mode with one pacer, pacing per host, failures recorded, and a bad
     plan refused before any fetch.

## Strengths

- All 109 spans match their bodies exactly, and a test re-checks them where the bodies are
  kept.
- The pages that don't state a value (the first F04 capture, C12) add nothing, and the
  manifest says why. The apprentice's fee and the UCAS deadline stay unknown, never £0.
- The two student-finance regimes have separate records, and no course is linked to a
  regime the page doesn't name.
- F02 keeps session 2's review exactly as given, and stays `proposed`.

## Issues

### Critical
None.

### Important

1. **The Lifelong Learning Entitlement loans leave out the age rule their page states**
   (truth). backend/tools/school_leaver_pack.py:181–197 and 210–228.
   - The F12 body states "You must be under 60 on the first day of your course to apply
     for a Tuition Fee Loan." (offsets 55234–55319, once). It goes on: "If you're 60 or
     above, you may be able to apply for an additional loan to help cover your living
     costs." (55330–55433).
   - Neither `funding:F12` nor `funding:F12.maintenance` has an age rule, or an unknown
     with a reason.
   - The brief asks for each loan "with its age and residency rules". This rule also
     differs from the earlier regime, where F06 says "no upper age limit for Tuition Fee
     Loans" (F05).
   - So a 60-year-old starting in 2027 would see no age condition on the new tuition loan.
   - Fix: add `F12.rule_age_limit.tuition` and `.maintenance` claims, cite them in the two
     records' rules, add their rows to Part 1 and regenerate. Also extend
     `test_the_loans_say_how_they_are_paid_and_repaid_and_who_qualifies` to cover them.

2. **Two key rules have their deciding words outside the cited excerpt** (truth).
   backend/tools/school_leaver_labels.json:431 (F04.rule_age) and :778
   (F06.rule_residency.three_years).
   - F04.rule_age's value is "…for an apprentice aged 16 to 24". Its excerpt ends "…if
     they are:", and "aged 16 to 24" is only in the note.
   - F06.rule_residency.three_years's value ends "before the first day of the first
     academic year". Its excerpt stops at "for 3 years before the". This date is exactly
     what tells the pre-2027 rule from F12's ("the first day of the month the course
     starts").
   - The package tells the reviewer to "answer from the excerpt", and code checks only the
     quoted words. So the one number that matters in each row can't be confirmed (Q101,
     Q16, Q33).
   - Both fit within the 200-character limit: the F04 list item is about 40 characters
     further on, and F06's sentence ends about 80 characters later.
   - Fix: widen each span to take in the deciding words (in F04, the list's first item),
     then regenerate the pack, the pin and the package.
   - The same pattern, smaller in effect, is in Minor 1.

3. **The bursary is labelled "grant", which planning treats as never repaid, while the
   record says repayment is unknown** (truth). backend/tools/school_leaver_pack.py:154.
   - `funding:F10` has `instrument_kind: "grant"` and `repayment: {unknown: "the pages do
     not say whether a bursary is repaid"}`.
   - planning/pack.py:77 maps "grant" to `InstrumentKind.GRANT`, which is in
     `NON_REPAYABLE` (planning/catalogue.py:216). That makes the bursary eligible as
     non-repayable support in a route.
   - So the record's kind says it is never repaid, with no span, while its own repayment
     field says that is unknown.
   - Q47 asks the reviewer to confirm "grant" against an excerpt that says only "A bursary
     is money that you… can use". The row doesn't explain that "grant" means it is never
     repaid.
   - Fix (either):
     - (a) cite a span that says it is not repaid, if one exists, or say plainly in Q47
       that yes means "never repaid";
     - (b) use a kind that plans no money (`programme`) until the session decides.
   - Note that the format's kinds have no "bursary", although planning's enum does.

4. **Some session rows can't be answered from the page and use internal words** (list).
   docs/reviews/school-leaver-pack-questions.md:68, 85, 106, 121, 138, 156 (generator:
   school_leaver_pack.py:414).
   - Each funding record has a row "instrument kind and award state: loan, award state
     not_assessed", and Q62 and Q79 have "(no claim)". No page states an award state, so
     "Right as the page states it?" has no right answer, and these rows invite a "no" or a
     blank, which would block the whole record.
   - The table uses field names (`rule_age_band`, `fact: loan_minimum`, `eligible_costs`),
     record IDs, character offsets and codes (H-07, R2, OI-14). The brief asks for "plain
     words", and CLAUDE.md asks for no internal codes unless the reader needs them to act.
   - Fix:
     - ask only "Is this a loan (repaid) / a grant (not repaid)?" beside a span, and drop
       award state (it is never the page's);
     - name each field in plain words ("Who it is paid to", "Age rule", "Most you can
       borrow");
     - move offsets and claim IDs to a footnote column, or drop them.

### Minor

1. Values that go a little beyond their excerpt (truth, low effect; the notes give the
   rest):
   - F12.repayment ("after finishing or leaving the course");
   - F12.interest ("from the first payment");
   - F12.loan_maximum.maintenance and `.tuition_total` (their `applies_to` reasons);
   - F09.alternative_if_eligible ("which is not repaid": the next sentence on the page);
   - F10.rule_age_exception ("only if", "EHC plan");
   - F10.timing;
   - F11.rule_vulnerable_group;
   - F05.rules_change (the years come from the table headers).

   Widen the spans where the limit allows when Important 2 is fixed.
2. The pack's notes say "Its seven new records" (school_leaver_pack.py:66, so in the pinned
   0.3.0 file). There are eight, as the ADR, manifest and report say. Fix it with the
   regeneration above.
3. `limit.repayable` is null on F05's loan caps, although F05 says "You have to pay it
   back". This is cautious rather than wrong, and the record's kind is `loan`. Consider
   `true`, cited.
4. The C12 re-fetch (planning/task-7f-fetch-output-c12-date.json, 18:51, after the head)
   found "13 Jan" in the step-by-step item just before "(18:00 UK time) Equal
   consideration date…", in the "2027 entry application deadlines" section. The
   package's "Still unknown" paragraph (questions.md:16–25) and the manifest's
   `why_not_used` say the date wasn't found. Before the session, either fold this in (the
   year comes from the section heading; C12's rights are still pending) or say it was
   found but not used.
5. The rights of the context fragments (outside the diff; the controller's commits
   e364ded and b2b6782): `planning/task-7f-fetch-output-c12*.json` are tracked and hold 39
   neighbourhoods of the UCAS page (class other, pending rights). Each is up to 226
   characters, more than the 200-character excerpt limit. Consider keeping context output
   for excerpt-only pages out of git, or capping excerpt plus context at 200.
6. `option:C11` is linked to `bookkeeping-assistant-leeds` because "Leeds is where the
   synthetic school leaver lives" (report ruling 3). The pack holds nothing synthetic, but
   the T Level (for 16 to 19 year olds) now appears in that target's options for fixture
   person P05 as well. This is a question for the product owner's session, not a defect.
7. The manifest's `option_pack` now points at the unreviewed 0.3.0. 7c pointed at a
   reviewed version. No product code reads it, so this is only a bookkeeping note for the
   second half.

## Assessment

**Task quality:** Needs fixes.
**Reasoning:** Every span is exact, and the January 2027 split, the unknowns, the pins and
the batch guards are sound. But the new tuition loan leaves out the age rule its page states,
two deciding rules can't be checked from their excerpts, and the bursary's kind says "never
repaid" against its own unknown. All three must be fixed (with the session rows made
answerable) before the school-leaver pack session.
