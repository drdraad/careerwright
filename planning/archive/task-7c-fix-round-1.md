# Task 7c fix round 1 of 5

Review: `.superpowers/sdd/l0-sprint-tasks/task-7c-review.md` (read it in full).

## Controller rulings first
- **Where the fix goes:** amend pack 0.2.0 in place (a new commit that rewrites the 0.2.0 file
  through `tools.session_2_pack` and updates its pin), not a 0.2.1. 0.2.0 is this task's own
  output under review: no consumer pins it yet and the branch is unmerged. The "a committed
  version never changes" rule protects versions something has relied on; a published
  version with known-wrong values that a later task could pin by mistake is the worse
  outcome. Say so in ADR 0011's 7c note. Pack 0.1.0 and capability reference 0.1.0 stay
  byte-identical.
- **A bare "?" answer:** the dispatch settles it: where a "no" or "?" gives no value you can
  cite, the field becomes unknown with the review's reason. That covers Q227–Q242 and Q290.
- **Q153 also applied to `option:C05.assessment`:** keep it. Serving "not stated on the page"
  after the record says the page states an exam assessment would serve a value the record
  contradicts. Keep its ADR 0011 note.
- **Labels the format cannot mark unknown** (C08.1, C10.1/.2, C02.2, J15.4): no change here;
  the controller carries them to Task 10.

## Important (from the review)
1. Bare "?" answers (Q227–Q242 on the Adzuna copies J02, J03, J07; Q290): each field becomes
   unknown with the review's reason. 0.2.0 must no longer name "AWD online" as employer on
   J02 or J07.
2. Q187: add F01's earnings rule as a span-cited text rule quoting "earn below £25,750 or are
   unemployed" (F01's kept body, offsets 7233–7269 per the review; verify them), with a note
   naming Q187, instead of dropping the rule.

## Upgraded by the controller (Important: money and honesty)
3. J10's pay (Q284, "retain the pro-rata qualification"): a range served without the basis
   the reviewer said to keep is a value served as if fine. Cite the pro-rata words if the
   kept body or a stored excerpt holds them; otherwise make the salary unknown with the
   review's reason.

## Minor, fix now (cheap)
4. Q38: keep what the page states, a text fact quoting "195 hours" from C01's kept body,
   without the "guided learning hours" label.
5. Restore 0.1.0's notes in 0.2.0: the Task 7b curation provenance and "never fills a live
   field"; "never shown as current" applies to every pack record (R9), reviewed ones
   included.
6. Pin `SOURCE_VERSION = "0.1.0"` literally. Add one test that checks a handful of
   reviewed/proposed outcomes with its own small parse of `session-2-answers.md`, so the
   tests do not share the tool's parser.
7. Your fix report says which correction checks run only where `var/evidence/corpus/`
   exists (locally, not in CI, under R3).
8. Manifest status and the corpus README: say "label review applied, 55 of 121 records
   reviewed" (or the new count), not "labels reviewed".

## Then
Re-run `backend/tests/tools/test_session_2_pack.py`, `test_option_pack.py`,
`test_capability_reference.py`, then `make check`; `make acceptance` once before the final
commit. Report the new 0.2.0 hash and the reviewed/proposed counts. Same hard rules as the
dispatch (Edit/Write only for source; explicit staging; never `answers-2.md`; no `.env`;
don't touch `apps/web` or `spikes/`; no subagents). Append a fix report to
`task-7c-report.md` and reply with the short contract.
