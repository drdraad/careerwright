# Task 7c report: the reviewed England option pack

Implementer: Task 7c (fresh Opus implementer), branch `l0-local-release`, BASE `fa40db5`.

## The short version

- **Published:** England option pack **0.2.0**, dated 2026-10-30, SHA-256
  `b4afe250f47813032c9df70e9d43c88eefd60e75e60574b4413c5b7d6ccf9cc4`, pinned in
  `option_pack.PINS`. It is session 2's review of 0.1.0, built by a new tool
  (`backend/tools/session_2_pack.py`) from the product owner's record and written by the
  existing `tools.option_pack_files --pack`. A fast test proves the committed file is exactly
  that tool's output, so every change traces to an answer.
- **0.1.0 is unchanged** (bytes and pin `d7ff17d7…a6a3d3`).
- **Capability reference 0.2.0** (SHA-256
  `2df1c70d156ee036c990be688b9722dea496a6a699d76ce0e16ac82b01c72e86`): 0.1.0's rubrics and
  gates unchanged, re-targeted at pack 0.2.0 (a reference fits exactly one pack version, so
  without it no consumer could load 0.2.0), with R1-R40's answers recorded. It stays
  `proposed`.
- **Result:** 55 of 121 records `reviewed`, 66 `proposed`, 0 left out. 7 corrections added
  as span-cited claims; 15 claims the review called wrong (or no longer cited) left out.
- **Not switched:** the app (capability and planning) still pins 0.1.0. The brief hands the
  version to Tasks 10, 12, 8 and 13a to pin; a test proves 0.2.0 + reference 0.2.0 load and
  build every target's matrix and planning catalogue.
- `make check` passed (backend 1504, web 212); `make acceptance` passed (integration and
  stack 299, Storybook, Playwright 28).

## Hand-off to Tasks 10, 12, 8 and 13a

| What | Version | SHA-256 |
|---|---|---|
| England option pack | `0.2.0` | `b4afe250f47813032c9df70e9d43c88eefd60e75e60574b4413c5b7d6ccf9cc4` |
| Capability reference | `0.2.0` | `2df1c70d156ee036c990be688b9722dea496a6a699d76ce0e16ac82b01c72e86` |

To pin: `PACK_VERSION = "0.2.0"` and `REFERENCE_VERSION = "0.2.0"` in
`careerwright/capability/commands.py` (and the planning/integration tests that assert
`"0.1.0"`). Only `reviewed` records hold reviewed values for TEST1-13's scoring; a `proposed`
record's value is not a reviewed one.

## Records: reviewed, still proposed, excluded

| Kind | Reviewed | Proposed (asked: a non-yes answer or a correction) | Proposed (no row asked) | Excluded |
|---|---|---|---|---|
| Job postings | 9 | 11 | 0 | 0 |
| Skill requirements | 28 | 3 | 29 | 0 |
| Learning options | 6 | 4 | 0 | 0 |
| Offerings | 6 | 4 | 0 | 0 |
| Outcomes | 5 | 13 | 0 | 0 |
| Funding instruments | 1 | 2 | 0 | 0 |
| **Total (121)** | **55** | **37** | **29** | **0** |

Reviewed: funding:F03; job:J05, J08, J09, J12, J14, J15, J17, J19, J20; offering:C02, C05,
C06, C07, C08, C09; option:C02, C06, C07, C08, C09, C10; outcome:C02.1, C04.1, C04.2, C09.1,
C09.2; req:J01.4, J04.2, J05.1, J05.2, J05.5, J05.6, J06.1, J06.2, J08.2, J09.1, J09.2,
J10.2, J11.1, J12.1, J12.3, J14.1, J14.3, J14.4, J15.2, J15.3, J15.5, J15.6, J17.1, J18.2,
J18.3, J19.1, J20.1, J20.3.

Each record's `review` names the reviewer ("the product owner"), the decision date
(2026-10-29 when every row was one of the product owner's own Q1-Q15, else 2026-10-30, the
ruling's date), the session ("session 2 (2026-10-29 to 2026-10-30)") and a decision that
lists its rows, every non-yes answer with what it did, and whose answers they were ("Answered
by the product owner", or "checked by an AI, adopted by the product owner's ruling of
2026-10-30", or both by row range). The 29 never-asked requirement rows carry no review.

Answer counts in the record: Q 295 yes / 35 no / 14 "?"; T 29 yes / 7 no; R 32 yes / 18 no /
8 "?".

## Corrections applied (span-cited, record stays proposed)

| Question | Record and field | New claim | Span (offsets) and how it was checked | Value |
|---|---|---|---|---|
| Q53 | outcome:C01.3 evidence kind and span (old span kept as a fact) | `C01.outcome_evidence.4` | 74838-74915 "Get hands-on experience with industry leading tools like Tableau and PowerBI." — located in C01's kept body (count 1) | practice (confidence unchanged: unsupported; level null) |
| Q56 | option:C04 fact access period | `C04.access_period.corrected` (replaces `C04.access_period`) | 5809-5904, the stored claim's own excerpt ("one year of 24/7 access to all training material, …") | exactly 1 year (was "up to 12 months") |
| Q153 (with R49) | outcome:C05.1 evidence kind and span (old topic span kept as a fact); option:C05 assessment | `C05.assessment` | 164231-164279 "There are four external exams during the course." — kept body (count 1) | exam (confidence unchanged: unsupported; level null); assessment "four external exams" (was unknown "not stated on the page") |
| Q198 | funding:F02 published_on | `F02.published_on` | 12162-12236 `<meta name="govuk:first-published-at" content="2016-05-16T09:00:07+01:00">` — kept body (count 1) | 2016-05-16 (was unknown) |
| Q199 | funding:F02 rules_updated_on | `F02.rules_updated_on` | 12308-12381 `<meta name="govuk:public-updated-at" content="2024-10-14T10:36:04+01:00">` — kept body (count 1) | 2024-10-14 (was unknown) |
| Q206 | funding:F02 rule lle_interaction | `F02.lle_interaction.corrected` (replaces) | 5653-5785, the stored claim's excerpt; the note cites the lead-in "You may need to apply for a different type of student finance if you’re:" (5311-5383, kept body) | use_instead "may need Lifelong Learning Entitlement funding instead" |
| Q207 | funding:F02 rule htq_interaction | `F02.htq_interaction.corrected` (replaces) | 5433-5527, the stored claim's excerpt; same lead-in | "level 4 or 5 Higher Technical Qualifications may need undergraduate funding instead" |

Verification: `test_every_changed_value_cites_its_span_on_the_same_page` (offsets inside a
stored claim's excerpt) and `test_a_correction_located_in_a_kept_body_is_exactly_its_text_there`
(4 cases: exact text at the offsets in the hash-checked kept body, `tools.corpus.locate`
count equal to `occurrences`, first occurrence at the span). The four kept-body cases ran
here (bodies present); on a machine without `var/evidence/corpus/` they skip with a reason.

## Fields made unknown, values left out, attributes changed

Unknown with the review's reason (each reason starts "session 2, Qn (no): …"):

| Question | Field | Why |
|---|---|---|
| Q23 | job:J18 advertiser (was "unknown" as a value) | Page's embedded data mark an agency ("isAgency":true); job-board page kept as excerpts only, no stored excerpt holds the words, so "agency" cannot be cited |
| Q39 | offering:C01 fee_total (was a null claim) | £0 only for an eligible learner ("You could train for free"); no price for anyone else |
| Q44 | offering:C01 schedule (already unknown; reason updated) | No timetable confirmed; the form offers preferred times as choices ("18:00pm - 21:00pm") |
| Q63 | offering:C04 schedule (reason updated) | "Flexible learning", "Live, instructor-led online training", no session times |
| Q92 | offering:C10 schedule (reason updated) | "Self-paced", which the schedule shape cannot hold |
| Q98 | option:C03 assessment (was "no other assessment") | A 60% quiz before later modules; not in any stored excerpt |
| Q102 | offering:C03 instalment (reason updated) | Instalments only for purchases of £50-£6000, so none for this £19 course alone |
| Q106 | offering:C03 schedule (reason updated) | "Self-paced" (C03.delivery_mode); no weekly hours |
| Q201 | funding:F02 repayment (was F01's sentence) | This eligibility page does not state the repayment rule |
| Q223 | job:J01 advertiser | "AWD online operates as an employment agency." — not in a stored excerpt |
| Q224 | job:J01 employer (was "AWD online") | AWD online is the agency; the employer is "our Client" |
| Q317 | job:J04 salary (was a null claim) | No pay shown; embedded 33000-38000 per annum is not an advertised range, and not citable |
| Q333 | job:J16 advertiser | Embedded data: "Recruitment consultancy"; not citable |
| Q334 | job:J16 employer (was "PRATAP PARTNERSHIP LTD") | PRATAP is the recruiter; the client is unnamed |

Left out (the reading does not fit the field's declared shape; reason in the record's review):
Q38 `C01.guided_hours` ("195 hours" not said to be guided learning hours); Q187
`F01.rule_earnings` (the page states no period and not gross, but the earnings-rule shape is
a yearly gross cap); Q269 `J06.occupation_crosswalk` and Q298 `J11.occupation_crosswalk`
(the page states no SOC code: the crosswalk was an inference).

Attributes: Q25 req:J18.1 importance → `unknown` (SQL is one of several alternative tools);
Q95, Q96 outcome:C10.1/.2 confidence → `unsupported` (the course prepares for exams it does
not include); Q167 outcome:C06.2 confidence → `unsupported` (the unit covers "recording
financial transactions", not examined reconciliation).

Claims left out of 0.2.0 (15): the 4 above; the 8 that the now-unknown fields cited
(`C01.fee_total`, `C03.assessment`, `J01.advertiser`, `J01.employer`, `J04.salary`,
`J16.advertiser`, `J16.employer`, `J18.advertiser`); and the 3 replaced
(`C04.access_period`, `F02.lle_interaction`, `F02.htq_interaction`). 481 − 15 + 7 = 473.

## Answers recorded but not applied (the value stays; record stays proposed)

| Question | Record | Why kept |
|---|---|---|
| Q109, R46 | outcome:C03.1 | "No formal qualification" establishes no NMC outcome: already `unsupported`, topic mention, no level |
| Q127 | outcome:C08.1 | Eligibility to register, not an assessed work sample; no evidence kind names a credential outcome, and capability types it a credential outcome by its row (R54 yes). Making it `unsupported` would contradict R54 |
| Q142 | outcome:C02.2 | Transaction processing, not reconciliation: already `unsupported`, no level |
| Q261 | req:J15.4 | "Valid UK driving license" warrants a DVLA-checked gate; adding a typed gate is the capability model's (and would make a protected, target-wide gate from one posting) |
| Q284, Q300 | job:J10, job:J13 | The range is right "with its pro-rata qualification"; the pay shape cannot hold it. J13 keeps it as its fact; J10's words are in no stored excerpt |
| Q290 ("?" with words) | req:J10.1 | The page also says "Applicants must have current UK professional registration.": a conflict left open (both gate words map to the same NMC gate, so no behaviour rests on it) |
| T32-T34, R41-R43 | outcome:C01.1-.3 | C01's course overview, a PDF outside the corpus, shows assessed work; no level is established. Not citable from C01's page |
| R50, R51 | outcome:C06.1, C06.2 | The AAT specification (outside the corpus) swaps the units' rows; level 2 rejected, so null stays |
| R52, R53 | outcome:C07.1, C07.2 | "The opportunity to achieve" does not show the exam is optional; unclear, no level |
| Q227, Q228, Q230-Q234, Q236-Q239, Q241, Q242 (bare "?") | job:J02, J03, J07 (Adzuna) | Undecided: values unchanged |

## Rulings I made (the brief and dispatch did not settle these)

1. **Which rows are a record's:** every question that states one of its values — Q1-Q344,
   T11-T27, T32-T36 and R41-R58. T1-T10 (the fixture person), T28-T31 (the checker's
   conclusions, field "result") and R1-R40 (the capability reference) are not pack records.
   Counting the T and R rows is the fail-safe reading: without it five outcomes (C01.1,
   C01.2, C06.1, C07.1, C07.2) whose Q row was yes but whose R or T row was no would have
   read `reviewed`. Cost if wrong: those records re-labelled; no data lost.
2. **A record no row asks about stays `proposed` with no review** (29 requirement rows):
   "every row yes" is vacuous there, and nothing in the record traces to a decision.
3. **A bare "?" is undecided** (the package's own meaning of a blank), so its values stay
   as they were; a "?" with words (Q290) is recorded like a no.
4. **"Cite that way" means in the field's declared shape** (CLAUDE.md, ADR 0011 decision
   13). A correct reading the shape cannot hold makes the field unknown or leaves the fact
   out: never text smuggled into a structured field. This is why Q38 and Q187 are left out
   rather than kept as text.
5. **For enums with no "unknown":** importance uses its own `unknown`; an outcome whose
   page, per the reviewer, does not support it uses the format's `unsupported` (no level,
   never "missing level", never a pathway). Where that would contradict another accepted
   answer (C08.1, R54 yes), the label stays and the answer is recorded.
6. **Answers resting on documents outside the corpus** (C01's overview PDF, the AAT
   specification, NMC guidance) cannot change a value cited from a corpus page; they keep
   their records proposed and are carried to Task 10.
7. **No record is excluded:** every row asked "right as the page states it?"; no answer
   rejects a whole record.
8. **An answer about a page applies to that page's record that holds the value** (Q153's
   "exam assessment is stated" also corrects option:C05's assessment, which said "not stated
   on the page"; option:C05 therefore stays proposed though Q143-Q145 were yes).
9. **Reviewed outcomes name the rubric** their null level was judged against (from their R
   row); proposed outcomes keep `rubric_version` null.
10. **Capability reference 0.2.0** (not in the brief): needed so 0.2.0 is loadable by the
    capability model; content unchanged, R1-R40 recorded, still `proposed`. Applying its
    no/? answers would change ADR 0012's rules (level 0's meaning, required levels, the NMC
    check), which is not 7c's to decide.
11. **The app is not switched to 0.2.0** — the brief gives the pin to Tasks 10, 12, 8 and 13a.
12. **No rights decision** was taken at session 2, so rights statuses and OI-07 are unchanged.
    option:C08 is `reviewed` for its labels while its page stays pending rights review.

## Carried forward

**D-answers (decision sheet) — none concerns the pack's records, levels or rights, so none
is applied here:**

| Answer | What it changes | Task |
|---|---|---|
| D3 yes (with the product owner's comment: a skill-frequency analysis across many similar-level jobs would be more sensible) | Confirms ADR 0012 decision 3 (importance from the ads); the comment is a later idea | Task 10 (record the confirmation; comment to the backlog) |
| D4, D5, D6, D7 yes | Confirm ADR 0012 decisions 4-5 (verified gates; "with help" ≤ 1; an assessment below a self-report wins, flagged — review M4; a level needs an example) | Task 10 |
| D8 no — "Accept it" | Replaces "a test result counts once you confirm the result and who assessed you"; the words are ambiguous (accept the result without that confirmation?) — the controller should confirm the meaning | Task 10 (evidence; ADR 0012 decision 6) |
| D9 yes, "unless it's an apprenticeship" | Right to work alone never makes "ready", except for an apprenticeship (ADR 0012 decision 7) | Task 10 |
| D10 no — "the lower of 14 questions or 100% of the must haves" | Replaces "start with 12 questions, stop at 80% of must-haves" (ADR 0012 decision 8) | Task 10 |
| D11 yes | Confirms pack-target matching (ADR 0012 decision 10) | Task 10 |
| D12, D13, D14, D15, D16, D17 yes | Confirm ADR 0013's planning rules (undated fee in month 1; month-only start on the 1st; shortfall limit; debts inside the payment limit; ready in the last month counts; the delay scenario) | Task 12 (and Task 13a for D16, D17) |

**T and R answers outside the pack:** T5 (P01's debt repayments are not stated, so "none" is
an assumption: unknown is never zero) and T9 (TRACE-01's levels cannot move to other
rubrics) → Task 12 / 13a (the checker's P01 inputs). T28, T29 (C01's routes: its outcomes
are assessed per the overview) → Task 10 and 12. R6, R10, R14, R18, R22, R26, R30, R34 ("?":
required level 2 not established), R7, R11, R15, R19, R23, R27, R31, R35 (no: "No evidence
yet" must be unknown, not level 0 — this conflicts with spec section 8's anchor 0, so it
needs the controller), R38 (no: the NMC check needs status, entry and restrictions) →
Task 10.

**Values the format cannot hold yet** (for a later format version or Task 10/8): an evidence
kind for a credential outcome (Q127); a pro-rata qualification on pay (Q284); an earnings
rule with no stated period or basis (Q187); hours of an unstated kind (Q38); a self-paced
schedule (Q92, Q106); a driving-licence gate (Q261). Documents outside the corpus the
reviewer relied on (C01's overview PDF, the AAT Level 2 Bookkeeping specification) could be
added to the corpus so a later version can cite them (Task 10).

**Task 8:** the Adzuna copies J02, J03, J07 are undecided ("?"); J02 and J07 still name
"AWD online" as employer although Q224 says AWD is the agency for the same vacancy (J01).
J10's pro-rata note is not citable from its stored excerpts.

**Carry-forward from Task 9 (N7):** done for the pack — the only UK-regulated role among its
targets (registered nurse) has its gate typed as legal practice (R37 yes), tested by
`test_every_uk_regulated_role_in_the_reviewed_pack_has_its_protected_gate_typed`; "in live
research" stays with Tasks 8, 10 and 12. "Publish the reviewed outcome levels under Task 9's
rubrics": done — every level is null (no level was accepted) and each reviewed outcome names
its rubric.

## Files

New:
- `backend/tools/session_2_pack.py` — the transcription and its decisions (one entry per
  non-yes answer).
- `backend/tests/tools/test_session_2_pack.py` — 19 tests.
- `backend/src/careerwright/catalogue/packs/england_option_pack/england-option-pack-0.2.0.json`
  (generated; reviewers can skip it — the test proves it equals the tool's output).
- `backend/src/careerwright/capability/reference/capability-reference-0.2.0.json`.

Changed:
- `backend/src/careerwright/catalogue/option_pack.py` (PINS), `capability/reference.py` (PINS).
- `backend/tests/domain/test_option_pack.py` (the manifest test now checks the latest
  version, 0.2.0, and that the review changed no page), `test_capability_reference.py` (two
  pins; a reference refuses another pack version).
- `corpus/manifest.json` (0.2.0 recorded; each slot's claims and `label_review`; OI-08;
  status, version and date), `corpus/README.md`.
- `docs/adr/0011-england-option-pack-format.md` (decision 15), `docs/adr/0012-capability-model.md`
  (R1-R40, N7), `docs/requirements-register.md` (OPTN-10 verified; TEST1-09 and OUT1-10 T7c
  parts verified; TEST1-13 and OPT1-16 name the version and hash; H-07 and the session 2
  row), `docs/runbook.md`.

Not touched: `apps/web`, `spikes/`, `answers-2.md`, CLAUDE.md (it needs no change; the
controller may add the new tool to the "Commands" list).

## Checks

TDD: the test module was written first. RED 1: collection error, `No module named
'tools.session_2_pack'`. RED 2 (tool written, 0.2.0 not yet published): `OptionPackError: no
committed option pack version 0.2.0`. RED 3 (pack published, manifest not yet updated):
`test_the_corpus_manifest_records_the_reviewed_version_and_each_page_s_review` failed
(`'0.1.0' == '0.2.0'`), 28 passed. GREEN after the manifest edits.

Mutation checks (each decision removed in memory, the test module re-run): dropping Q23's
decision fails `test_the_committed_version_is_the_record_applied_to_0_1_0` and
`test_every_answer_other_than_yes_is_applied_or_recorded_and_none_is_invented`; dropping
Q153's option:C05 decision fails the committed-version test and
`test_a_record_is_reviewed_only_when_every_row_about_it_is_yes_and_nothing_changed`; dropping
R50's decision fails the committed-version and coverage tests.

- `cd backend && uv run --locked pytest tests/tools/test_session_2_pack.py tests/domain/test_option_pack.py tests/domain/test_capability_reference.py -q`: 78 passed.
- `make check`: passed — ruff format (310 files), ruff lint, mypy (310 files, no issues),
  backend `1504 passed, 299 deselected`, fixture validator passed, web: generated client
  matches, Biome, tsc, Vitest `212 passed`.
- `make acceptance` (once, on the final tree, before the commits): passed, exit 0 —
  backend integration and stack `299 passed, 1504 deselected in 565.96s`, Storybook build,
  Playwright `28 passed (3.2m)`.

Commits: `0eae441` Publish the reviewed option pack 0.2.0 from session 2's record (Task 7c);
`3b2fd87` Record the reviewed pack in ADRs 0011 and 0012, the register and the runbook
(Task 7c). `answers-2.md` was not staged.

Process note: every source file was changed with Edit or Write. Heredocs were used only for
throwaway read-only scripts in the scratchpad (outside the repository) and for the two
commit messages; pack 0.2.0 was written by the project's own tools.

No live call was made (no model, Adzuna or page fetch). Reading the kept bodies under
`var/evidence/corpus/` was local only.

## Concerns

1. **The AI-checked answers are often opinions about labels, not values** (e.g., "the
   crosswalk is an inference", "the replacement is conditional"). I applied each as the
   rules above say, and recorded every one, but a human reading of Q25, Q127, Q142, Q167
   and Q261 could reasonably differ. Each is one decision entry to change and re-run.
2. **D8's replacement ("Accept it") is ambiguous** — needs the controller's reading before
   Task 10.
3. **R7-R35's anchor answers conflict with spec section 8** (level 0 = "no evidence of
   performance"); not applied, needs a ruling.
4. **option:C08 is `reviewed` for its labels while its page is still pending rights review
   (OI-07).** Those are separate gates; noting it so nobody reads "reviewed" as "rights
   cleared".

---

# Fix round 1 (task-7c-fix-round-1.md)

**This round supersedes the figures above:** pack 0.2.0 is now SHA-256
`162d2773e295c7832ff3b311738bdd20d111538b15f1df49932fecfc82702a56` (was `b4afe250…`), with
464 claims (26 left out, 9 added). Review states are unchanged: **55 of 121 reviewed, 66
proposed, 0 left out.** Capability reference 0.2.0 is unchanged
(`2df1c70d…`). Pack 0.1.0 (`d7ff17d7…`) and reference 0.1.0 (`906b4e96…`) are
byte-identical. Ruling 3 above ("a bare '?' is undecided") is withdrawn: the dispatch did
settle it, as the controller ruled.

## What changed, item by item

0. **Amended 0.2.0 in place** (controller ruling): rebuilt by `tools.session_2_pack`,
   republished by `tools.option_pack_files --pack`, pin moved in `option_pack.PINS`, the
   manifest, ADR 0011 decision 15 and the register (OPTN-10, TEST1-13, OPT1-16). ADR 0011's
   decision 15 now says why it was amended in place and that 0.2.0 is frozen from here.
1. **Every "?" makes its field unknown with the review's reason.** Q227, Q230, Q231, Q233,
   Q236, Q237, Q238, Q241, Q242: J02, J03 and J07's salary, advertiser and employer are
   unknown ("session 2, Qn (?): the reviewer could not confirm it from the API's advert, so
   it is not served"). The employer reasons on J02 and J07 add "for the same vacancy (J01),
   Q224 says AWD online is the agency, not the employer". Q228, Q234, Q239: the three
   closing dates were already unknown; their reasons now record the "?". Q232: the fact
   `J02.duplicate_of` is left out. Q290: `req:J10.1`'s gate is now "statutory registration"
   (was "statutory registration (pending allowed within two months)"); the requirement's
   text claim and the gate itself have no unknown form, so the gate keeps only what both of
   the page's statements require, and the reason is in the record's review. Both gate
   words map to the same typed NMC gate, so no readiness result changes. No copy of the
   AWD vacancy (J01, J02, J07) names AWD online as employer any more.
   - Note for Task 8: `job:J02`'s `vacancy_id` still groups it with J01. It is a record
     attribute, not a claim, so it has no unknown; the cited fact behind it is gone. J03's
     predicted salary (the corpus's real predicted-pay case, OI-04) is no longer served in
     0.2.0; 0.1.0 still holds it.
2. **Q187:** F01's earnings condition is back as a span-cited text rule,
   `F01.rule_earnings_stated` = "earn below £25,750 or are unemployed", offsets 7233-7269,
   occurrences 2, note naming Q187. Verified in F01's hash-checked kept body (exact text at
   the offsets, `locate` count 2, first occurrence) and inside the 0.1.0 claim it replaces.
3. **Q284:** "pro rata per annum" is in no stored J10 excerpt and J10's body is not kept
   (job board), so J10's salary is unknown with the review's reason (the range and its
   pro-rata basis are in the reason, so nothing is lost to a reader). `J10.salary` is left
   out. J13 keeps its range, since its pro-rata basis is a reviewed fact (Q305 yes).
4. **Q38:** `C01.stated_hours` = "195 hours" (offsets 57939-57948, count 1), a text fact
   with no "guided learning hours" label, replacing `C01.guided_hours`.
5. **Notes restored:** 0.2.0's notes again say the records were curated by an agent (Task
   7b) from 33 real pages retrieved on 2026-10-29, and that every record, reviewed or
   proposed, is never shown as current and never fills a live field (R9). "Explorable only,
   never in an unqualified result" stays scoped to proposed records.
6. `SOURCE_VERSION = "0.1.0"` is literal (no longer tied to
   `option_pack_files.PACKAGE_VERSION`). New test
   `test_outcomes_follow_the_record_read_without_the_tool_s_parser` reads
   `session-2-answers.md` with its own regex and hard-coded row numbers, and checks seven
   outcomes' review states (C04.1, C02.1, C09.2 reviewed; C06.1, C07.1, C10.1, C01.1
   proposed).
7. **Checks that run only on the curating machine (R3):**
   `test_a_correction_located_in_a_kept_body_is_exactly_its_text_there` now covers every
   correction on a page whose body is kept: 8 cases (C01.stated_hours,
   C01.outcome_evidence.4, C05.assessment, F01.rule_earnings_stated, F02.published_on,
   F02.rules_updated_on, F02.lle_interaction.corrected, F02.htq_interaction.corrected). They
   need `var/evidence/corpus/`, which is gitignored, so on CI or any other machine they
   skip. All 8 ran and passed here. Everywhere, `test_every_changed_value_cites_its_span_on_the_same_page`
   checks the six corrections that reuse a stored claim's span inside that excerpt; C04's
   correction (a job-board page, excerpts only) is checked only that way.
8. **Wording:** the manifest's status is now "collected; label review applied (55 of 121
   records reviewed, 66 still proposed)", OI-08's status "label review applied (session 2,
   …): 55 of 121 records reviewed", and the corpus README says "label review applied, 55 of
   121 records reviewed".

Kept as ruled: Q153's correction of `option:C05.assessment`; the labels the format cannot
mark unknown (C08.1, C10.1/.2, C02.2, J15.4), carried by the controller to Task 10.

## Counts in 0.2.0 now

- 9 corrections (new span-cited claims): the 7 of round 0 plus `C01.stated_hours` and
  `F01.rule_earnings_stated`.
- 27 fields unknown with the review's reason: 19 newly unknown, 8 already unknown whose
  reason now records the review.
- 3 facts left out (`J02.duplicate_of`, `J06.occupation_crosswalk`,
  `J11.occupation_crosswalk`); 7 attributes set (Q25 importance, Q53 and Q153 evidence kind,
  Q95, Q96 and Q167 confidence, Q290 gate).
- Claims: 481 − 26 + 9 = 464.

## Files

`backend/tools/session_2_pack.py`, `backend/tests/tools/test_session_2_pack.py`,
`.../england-option-pack-0.2.0.json` (regenerated), `catalogue/option_pack.py` (pin),
`corpus/manifest.json` (claims of J02, J03, J07, J10, C01, F01; status; OI-08; pin),
`corpus/README.md`, `docs/adr/0011-england-option-pack-format.md`,
`docs/requirements-register.md`.

## Checks (fix round 1)

- RED first: with the tests changed and 0.2.0 not yet rebuilt, 6 failed, 16 passed
  (`test_the_committed_version…`, `test_every_changed_value…`, `test_a_value_the_reviewer_called_wrong…`,
  `test_the_reviewed_values…` with `KeyError: 'rule_earnings_stated'`,
  `test_a_value_the_reviewer_could_not_decide…` at `('job:J02', 'salary')`, `test_the_notes…`).
- Mutations: dropping the Q231, Q187 or Q284 decision each fails the committed-version and
  coverage tests (Q187 also fails the span test).
- `uv run --locked pytest tests/tools/test_session_2_pack.py tests/domain/test_option_pack.py tests/domain/test_capability_reference.py -q`:
  all passed (26 in the new module, 8 kept-body cases ran, none skipped).
- `make check`: exit 0 — ruff format and lint, mypy (310 files), backend `1511 passed, 299
  deselected`, fixture validator passed, web: client matches, Biome, tsc, Vitest `212 passed`.
- `make acceptance` (once, on the final tree, before the commit): exit 0 — integration and
  stack `299 passed, 1511 deselected in 619.71s`, Storybook build, Playwright `28 passed
  (2.8m)`.

Commit: `8e3d2ee` Amend option pack 0.2.0: every "?" unknown, F01's earnings rule kept
(Task 7c fix round 1). Explicit paths only; `answers-2.md` not staged. No live call.

## Hand-off (updated)

| What | Version | SHA-256 |
|---|---|---|
| England option pack | `0.2.0` | `162d2773e295c7832ff3b311738bdd20d111538b15f1df49932fecfc82702a56` |
| Capability reference | `0.2.0` | `2df1c70d156ee036c990be688b9722dea496a6a699d76ce0e16ac82b01c72e86` |

55 of 121 records reviewed, 66 proposed, 0 left out.
