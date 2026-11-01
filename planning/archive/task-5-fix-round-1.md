# Task 5 — fix round 1 (FIX_BASE 56db48f)

Findings: A- = task-5-review-A.md (taxonomy), B- = task-5-review-B.md (interview). Read
each finding's full text there. Fix ALL items listed.

## Must-fix
- B-I3 / spec §4 "Stream natural conversation for responsiveness, but commit changes only
  after complete validation" — controller ruling: streaming is in scope now, backend side.
  Stream the natural-language reply text of an interview turn (not the structured
  proposals) from the activity to an owner-checked, RLS-protected, sealed partial store;
  status events carry IDs + sequence only; an API read path returns the partial reply for
  the run's owner; the partial is superseded by (and never mistaken for) the validated
  output; nothing partial ever commits to the profile; failure mid-stream ends in an
  observable failure with the partial marked incomplete. Fixture interviewer streams too.
  Contract tests with the fixture adapter (no live call needed; Task 1 already proved Meta
  streaming). Amend ADR 0006 decision 13 accordingly; MODEL-03 row updated (UI rendering of
  the stream is Task 6's part — keep the row `planned` with the T5 part recorded).
  If you judge a design point needs the product owner, record it per R6 ("provisional —
  needs product owner confirmation"). One optional live call (test model, synthetic,
  `make live-smoke INTERVIEW=1`) to confirm streaming end to end is allowed; ledger it.
- B-I1  A repair request that fails without usage must not under-book the attempt: keep the
        unknown portion reserved/unknown, never release it as if known (MODEL-08, ADR 0004
        decision 10). Failing test first (the reviewer's probe).
- B-I2  A Standard-model interview during a Meta outage ends `provider_unavailable`, not
        `budget_exceeded`: size the default run limit or the per-attempt reservation so
        the retry budget fits, and add a Standard-model outage test.
- B-M1  A truncated output is a truncation failure: never parsed, and it does not trigger
        a repair request that spends again unless the contract says so; test.
- B-M7  `basis` (stated/inferred) must not be a bare model assertion: derive or verify it
        server-side from the referenced message(s), or present it to the person for
        confirmation; test.
- B-M8  Fixture attempts record a known zero cost (no call made), not unknown.
- B-M9  List bounds the web uses are published in the OpenAPI schema and consumed from the
        generated client; no hand-coded bounds.
- A-M1  The "not in ESCO" guard for provisional titles normalises plurals/punctuation/
        hyphenation (or matches through the full-text index) so near-duplicates of ESCO
        labels are refused; tests with the reviewer's examples.
- A-M2  ESCO reuse condition "mark adapted versions" applied to the reduced product import
        (and anywhere the data is shown), recorded in docs/dependencies.md.
- A-M4  Search reports full-text coverage honestly: not run ≠ 0 results (unknown is never
        zero).
- A-M6  Role-level (pg_api) isolation test for `provisional_concepts`.
- A-M11 Provisional concepts carry an explicit provisional/non-ESCO marker in API output.

## Cheap fixes
- A-M3 re-import keys on the transformation version too; A-M5 test import atomicity and the
  post-lock "already imported" branch; A-M7 replace shape/tautology tests; A-M8 correct
  "byte-for-byte"; A-M9 move test-only code out of `places.py`; A-M10 resolve the ambiguous
  "Newcastle" alias (Newcastle upon Tyne vs Newcastle-under-Lyme) explicitly.
- B-M2, B-M3, B-M4, B-M5, B-M6, B-M10, B-M11, B-M12 as described in the review.

## Rules
- Failing test first for every behavioural fix; show RED then GREEN in the report.
- Edit/Write tools only for source changes (no sed -i, awk, or heredocs into files).
- Live calls: at most the one optional streaming confirmation above; ledger it with cost.
- Regenerate the TS client if the API changes (drift check green).
- Run `make check` and `make acceptance` once at the end; leave the dev stack stopped.
- Append "Fix round 1" to task-5-report.md: per ID, the change, covering test, command, output.
