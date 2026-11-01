# Task 7c scoped re-review 1 (fix round 1, 3b2fd87..8e3d2ee)

Reviewer: Task 7c task reviewer, read-only. I read the fix list with the controller's rulings,
the "Fix round 1" section of the report, and the diff. I skipped commit b1c26a8 (the
controller's own record) except to check that it cannot change the tool's parse.

I re-ran my independent parser from the first review against 8e3d2ee. I re-checked the new
spans in the hash-checked kept bodies. I loaded the amended pack once:
- `load_pack("0.2.0")` passes its pin and `check_pack` (no problems).
- The committed file equals `dump_pack(reviewed_pack())`.
- Capability reference 0.2.0 loads against it and is `proposed`.

I did not re-run the test suites.

## The 8 items

**Ruling 0: amend 0.2.0 in place, keep both 0.1.0 files as they were. ADDRESSED.**
- The new pin is `162d2773…` (`backend/src/careerwright/catalogue/option_pack.py:59`). It
  matches the file's SHA-256.
- No stale `b4afe250` remains anywhere outside `.superpowers`.
- The ADR note explains the in-place amendment and freezes 0.2.0 from here
  (`docs/adr/0011-england-option-pack-format.md:214-221`).
- `git diff --quiet fa40db5 8e3d2ee` on pack 0.1.0 and capability reference 0.1.0 exits 0.
  Reference 0.2.0 is unchanged in this round.

**1. Every bare "?" makes its field unknown (Q227-Q242, Q290). ADDRESSED.**
- Thirteen decisions cover the "?" answers (`backend/tools/session_2_pack.py:357-361`,
  `:591-608`).
- My parser finds every one of the 13 bare-"?" rows served as `{"unknown": "session 2, Qn
  (?): …"}`. The one exception is Q232, whose fact `J02.duplicate_of` is left out (pack file
  lines 531, 532, 536).
- No copy of the vacancy `awd-junior-it-support-bristol` (J01, J02, J07) names "AWD online"
  as employer any more. The test at `backend/tests/tools/test_session_2_pack.py:280-297`
  checks this.
- Q290's fields cannot be unknown in the format: the requirement's text is a claim id, and
  its gate is a string. So the gate is narrowed to "statutory registration"
  (`session_2_pack.py:635-639`, pack file line 577), with the reason in the record's review.
- Both gate words belong to the same typed NMC gate (capability reference 0.2.0, lines
  212-213), so no readiness result changes. This is within the format's limits and the
  safer direction.
- Counts are unchanged and correct: 55 reviewed, 66 proposed, 29 never asked, 0 left out.
  Every reviewed record has rows that are all yes, and no non-yes row sits on a reviewed
  record. `option:C05` is the only record with all-yes rows that is still proposed, kept as
  ruled.

**2. Q187: F01's earnings rule kept as a span-cited text rule. ADDRESSED.**
- `F01.rule_earnings_stated` reads "earn below £25,750 or are unemployed", with field
  `rule_earnings_stated`, so its shape falls to text (`session_2_pack.py:332-343`; pack file
  line 506).
- It is cited in `funding:F01.rules`, in place of `F01.rule_earnings` (pack file line 658).
- In F01's hash-checked kept body, the text is exactly at 7233-7269, appears twice, and the
  first occurrence is at the span. That equals the stated `occurrences: 2` and the replaced
  0.1.0 claim.
- The note names Q187. The test is at `test_session_2_pack.py:265-267`.

**3. Q284: J10's pay without its pro-rata basis. ADDRESSED.**
- "pro rata per annum" is in no stored J10 excerpt, and J10 is a job-board page kept as
  excerpts only. So `job:J10.salary` is now unknown, and the reason carries the range and
  its basis (`session_2_pack.py:622-632`; pack file line 539; test at `:273-274`).
- `J10.salary` is left out.
- J13, which Q300 answered the same way, keeps its range. Its pro-rata basis is a cited fact
  on the same record (`J13.salary_basis_note`, answered yes at Q305). That fits the
  controller's "cite the pro-rata words if a stored excerpt holds them".

**4. Q38: "195 hours" kept as a text fact. ADDRESSED.**
- `C01.stated_hours` reads "195 hours" (`session_2_pack.py:320-331`; pack file line 355).
- In C01's kept body it is exactly at 57939-57948, appears once, and the first occurrence is
  at the span.
- It replaces `C01.guided_hours` in `option:C01.facts`, with no "guided learning hours"
  label. The test is at `test_session_2_pack.py:268-269`.

**5. The notes restored. ADDRESSED.**
- The new second note restores the Task 7b curation provenance: 33 real pages, retrieved
  2026-10-29 (`session_2_pack.py:734-736`).
- It also says: "Every record, reviewed or proposed, is never shown as current and never
  fills a live field (ruling R9)".
- "Explorable only" stays limited to proposed records, which is right. The test is at
  `test_session_2_pack.py:300-306`.

**6. `SOURCE_VERSION` pinned, and a test that does not use the tool's parser. ADDRESSED.**
- `SOURCE_VERSION = "0.1.0"` (`session_2_pack.py:58`). The import of `PACKAGE_VERSION` is
  removed.
- The new test `test_outcomes_follow_the_record_read_without_the_tool_s_parser` has its own
  regex and hard-coded rows (`test_session_2_pack.py:309-333`).
- I checked its hard-coded rows against the question file: Q66 is C04.1, Q141 C02.1, Q179
  C09.2, Q166 C06.1, Q81 C07.1, Q95 C10.1 and Q51 C01.1. All are correct.

**7. The report says which checks run only where bodies are kept. ADDRESSED.**
- The report's fix round 1, item 7 (`task-7c-report.md:344`) names the 8 kept-body cases.
  It says they skip in CI under R3, and that C04's correction is checked only inside its
  stored excerpt.
- The parametrisation now covers every correction on a kept-body page
  (`test_session_2_pack.py:52`, `:194-198`). That is 8 of the 9 corrections; the ninth,
  C04's, is on an excerpts-only page.

**8. Wording: "label review applied, 55 of 121". ADDRESSED.**
- Manifest status (`corpus/manifest.json:9`): "collected; label review applied (55 of 121
  records reviewed, 66 still proposed)".
- OI-08's status (`corpus/manifest.json:178`).
- The README (`corpus/README.md:10-11`, `:17`).

## New breakage in the fix diff

**Critical:** none.

**Important:** none.

What I checked:
- **Both 0.1.0 files are still byte-identical** to fa40db5.
- **Every changed field is cited or unknown with a reason.** From the previous 0.2.0 to this
  one:
  - 13 J02, J03, J07 fields and J10's pay are now unknown, each with a reason starting
    "session 2, Qn".
  - Two fields gained new span-cited claims, both verified in the body.
  - One fact was left out, with its reason in the review.
  - One gate attribute was narrowed, with its reason in the review.
  - The 455 claims the pack keeps from 0.1.0 are identical to 0.1.0's. 26 were left out and
    9 added (464 in all), as the report says.
- **Nothing a "no" called wrong is still served as fine** where the format can say unknown.
  The only values still served after a "no" are the labels the controller carried to Task
  10 (C08.1, C10.1/.2, C02.2, J15.4), plus records whose "no" rests on documents outside
  the corpus.
- **`_decision_text` now indexes `noted[question]` directly** (`session_2_pack.py:827`). A
  non-yes row without a decision would raise instead of printing "not decided": a loud
  failure, not a masked one.

## Out of scope (observations, no action asked in this task)

- **J02's vacancy grouping is now uncited.**
  - Q232 ("?") removed `J02.duplicate_of`, the only cited evidence that J02 copies J01, but
    `vacancy_id` still groups J01, J02 and J07.
  - J02's and J07's employer reasons still say "for the same vacancy (J01)".
  - This is harmless for counting, but the grouping and those reasons now rest on an
    unconfirmed link. The report flags it for Task 8.
- **J03's predicted salary is gone from 0.2.0.** Q233 was "?", and this was the corpus's real
  predicted-pay case (OI-04). Any later check that wants a predicted-pay example from the
  reviewed pack will not find one. 0.1.0 still holds it.
- **Q290's two readings now sit in different places.** J10.1's text claim still quotes
  "pending registration within two months", while its gate words no longer allow it. This
  is behaviour-neutral (same typed gate), and the conflict is in the review.
- **Commit b1c26a8 clarifies D8** ("it should say who assessed you after all", so D8's
  original rule stands). The first report's "D8 is ambiguous" carry-forward is now resolved
  for Task 10.
  - The clarification is an indented sub-bullet, which the tool's `^- [QTR]` parser ignores.
    The golden equality still holds at 8e3d2ee.
- **The working tree has an uncommitted change to `docs/reviews/session-w1-answers.md`.** It
  is outside this task and outside the reviewed range.

## Assessment

**Task quality:** Approved

**Reasoning:** All 8 items are fixed as the controller ruled, and my independent parse and
body checks confirm them. The fix brings no new Critical or Important problem. Pack 0.1.0
and capability reference 0.1.0 are untouched, and amended 0.2.0 loads, passes its checks and
matches the tool's output.
