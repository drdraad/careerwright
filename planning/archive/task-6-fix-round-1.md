# Task 6 — fix round 1 (FIX_BASE dec43e6)

Findings: A- = task-6-review-A.md (backend), B- = task-6-review-B.md (web + docs). Read
each finding's full text there. Fix ALL items listed. Failing test first for every
behavioural fix (RED then GREEN in the report). Edit/Write tools only for source changes —
no sed, awk, touch-for-content, or heredocs into files.

## Must-fix
- A-I-1 Distress screen false positives on career phrasing ("life savings", "take my life
        in a new direction", "don't want to live in London"): tighten the matcher (phrase
        and context rules, not bare substrings); add the reviewer's phrases as negative
        cases and keep true positives; the policy stays provisional (H-12).
- A-I-2 Dedupe must not chain transitively through shared labels; unrelated occupations
        never fold together (reviewer's ESCO examples as tests).
- A-I-3 The sketch uses the stored target choice (concept ID), never re-resolves by title.
- A-I-4 Salary floor period is verified: the proposed period must match the cited words
        (hour/week/month/year), else not `stated`/refused; fix the demo fixture parsing
        (£500 a week, a course budget is not a floor).
- A-I-5 The 120-candidate pool samples across job families before relevance cut (spec §4
        DIV-1); test that families are represented when the qualified pool supports it.
- A-I-6 Eval robustness: count the question per field (the question lives only in
        `next_question`; the prompt says so; the UI shows it once); semantic checks not bare
        substrings where avoidable; keep each live eval output (synthetic) in the private
        evidence directory so failures are diagnosable. Record REC1-09 as "inconclusive (one
        sample per arm)", not failed.
- B-I1 Tray edits validated before the decision posts; invalid edits show an error; a
        failed edit write is never lost; editing an Unknown/Skipped proposal keeps what was
        typed.
- B-I2 "Send it again": errors and support responses surfaced; guarded against pending,
        no key and paused; disabled while running; no duplicate turn or model call (test).
- B-I3 Undo restores the previous values with their original provenance (source, basis,
        fixture/synthetic label) through an application command — not a plain PUT recorded
        as direct entry. Backend + web, with tests.
- B-I4 Every new checked reply is announced (not just the first, not on load); focus is
        managed after entry choice, tray save and undo; tests.
- B-I5 Register/review claims only what is tested: MODEL-03 failed partial actually shown
        (or claim corrected), STATE-06 citations, MODEL-07 CREDENTIAL_REVOKED handling
        tested, S0-V08 claim matches the states tested.
- A-M1 Make the POST /targets 404 test use a real concept_id from another workspace's view.
- A-M2 Discovery failure-path tests (invalid output twice → invalid_model_output; slate of
        a failed discovery).
- A-M5 Narrow `except NessaError` in sketch to the no-search-terms case.
- A-M7 Salary floor amount must be positive; "no floor" is Unknown/Skipped.
- A-M8 Make "nothing has been saved" true for the support path (or state exactly what is
        kept, e.g. a receipt without the message text).
- A-M10 live-eval scope request cap aligned with the controller's per-scope cap (9).
- A-M13 Demographic words must not cause false refusals in discovery queries (test with
        the reviewer's probe).
- B-M2 Pause enforced as ADR 0007 says, or ADR corrected to match the deliberate behaviour.
- B-M8 One source for run-status sets (generated enums), no diverging hand-written copies.
- B-M10 Stale trays do not resurface.

## Cheap fixes
- A-M3, A-M4, A-M6, A-M9, A-M11, A-M12, A-M14, A-M15 and B-M1, B-M3, B-M4, B-M5, B-M6,
  B-M7, B-M9, B-M11 as described in the reviews.

## Live calls
- After the fixes, ONE re-run of `make live-eval` is allowed (test model, synthetic, ≤ 6
  cases, ledgered with cost and running total). No production-model calls. A properly
  powered counterfactual evaluation (several samples per arm) is deferred to the release
  task with a cost estimate in the report.

## Finish
- Regenerate the client if the API changes. Run `make check` and `make acceptance` once at
  the end; recapture affected screenshots; leave the dev stack stopped.
- Remove the `next` 16.4.1 age exception only if the clock is past 2026-10-28T17:43Z when
  you reach it; otherwise leave the recorded steps.
- Append "Fix round 1" to task-6-report.md: per ID, the change, covering test, command, output.
