# Task 7A re-review 1-C: fix round 3 against review C

Scope: rulings 1, 3–10, 13 and 14 of `task-7a-fix-round-3.md` (my C-I1, C-I2, C-M1–C-M7, the
MODEL-08 estimate and the cancel cascade), the "Fix round 3" section of `task-7a-report.md`
(treated as claims), and `review-1132cf0..dcaac22.diff` (5 commits, 3.0k lines, read in four
passes). I also checked the three items the coordinator named: the new 202 cancel, the
`runs.started_by_run` cascade and its lock, and migrations 0022–0024.

The review was read-only, at HEAD dcaac22, with a clean tree apart from the untracked docx. I
ran no suites. I ran one offline probe against the final code
(`uv run --locked --offline python -c ...`, no bytecode written) for the redaction forms, the
pay and work-mode readers and the byte bound. I did not read `.env` or NESSA_HOME, made no
live calls and dispatched no subagents. The three round 4 items (period suffixes, the
across-retries ceiling, attribute entities) are not re-raised.

## Verdicts

| Item | Verdict | Evidence |
|---|---|---|
| 1. C-I1 (with R3-2): normalise, then redact, then cut | **Fixed** | See notes below. |
| 3. C-I2: unknown beats wrong for pay | **Fixed** | See notes below. |
| 4. Cancel cascade (DUR-05) | **Fixed** (lock issue N1) | See notes below. |
| 5. MODEL-08 estimate | **Fixed** | See notes below. |
| 6. C-M3: budget counts unreserved runs only | **Fixed** | See notes below. |
| 7. C-M4: UTF-8 byte bound | **Fixed** | See notes below. |
| 8. C-M1: work-mode negation | **Partly fixed** | See notes below. |
| 9. C-M2: a cancelled run's recorded result | **Fixed** | See notes below. |
| 10. C-M5: `postings_conflicting` | **Fixed** | See notes below. |
| 13. C-M6: decision 15 cited | **Fixed** | See notes below. |
| 14. C-M7: SQL cap, other run's page, public listing | **Fixed** | See notes below. |

Totals: 10 fixed, 1 partly fixed, 0 not fixed.

### Item notes

**1. C-I1, fixed.**
- `pages.py:548-556`: `visible_text` now runs `redact_text(normalised_text(_plain(text)))`,
  then cuts.
- `pages.py:512-513`: a kept body whose normalised visible text shows a detail gets
  `visible_text_detail`.
- `redaction.py:50-53`: `_SEP` takes horizontal spaces only, never a line break.
- Probe: the four C-I1 forms (NBSP, a phone split by newlines, a zero-width space in an email,
  a soft hyphen in an email) and a phone split across `<span>`s all give a clean model input,
  and their bodies are not kept. A literal U+00A0 phone number is now redacted in the raw text,
  and its body is kept.

**3. C-I2, fixed.**
- `extraction.py:269-284` (`_misreadable`) and `salary_from`.
- Probe: `£30-35k per annum`, `£25-30K a year`, `£30 - £35k`, `£30k - £35` and `£1.2m` each
  give `salary_invalid`.
- Probe: `£40,000 max` and `£40,000 maximum per year` give a maximum only, with the minimum
  unknown. Symmetric `k`, plain ranges and `£14.50 an hour` read unchanged.

**4. Cancel cascade, fixed, with lock issue N1.**
- `identity/runs.py:327-350`: `cancel_run` requests the cancellation of each unsettled started
  run.
- `extraction_runs.py:125-131`: `start_extraction` re-reads the cancellation under
  `lock_started_runs` and records `acquisition_cancelled`.
- `r0023`: the SQL function refuses as well.
- The worker's `act_on_cancellations` already handles each run in its own `try`.
- Tests: `test_cancelling_an_acquisition_cancels_its_queued_extractions_before_any_request`
  (no call-log line, no `model_attempts`, inputs erased, a later start refused) and
  `test_a_finished_acquisition_s_cancel_cancels_only_its_unsettled_extractions`.

**5. MODEL-08 estimate, fixed.**
- `extraction_runs.py:60-74` (`acquisition_model_spend`): the cap times one run's reservation
  for `models.for_workspace`, and None in demo.
- It is placed on `GET .../jobs` (`acquisition.py`, `list_jobs`; `research_schemas.py`
  `ModelSpendOut`).
- The MODEL-08 row is updated.
- Tests: `test_an_acquisition_s_model_spend_is_the_cap_times_one_run_s_reservation` and
  `test_the_job_list_states_what_an_acquisition_may_spend_before_it_starts`.

**6. C-M3, fixed.**
- `store.py:521-536` (`extractions_unreserved`): started runs with no `model_attempts` row and
  no cancellation.
- The worker's `worker_read` policy on `model_attempts` (r0002) and `worker_dispatch` on
  `run_cancellations` (r0013) let the acquisition's transaction see other runs' rows, so the
  count is real.
- `test_the_budget_check_counts_only_started_runs_that_have_not_reserved` tells the two counts
  apart: the third start fits only under the new count.
- The `model_not_permitted` test is added.

**7. C-M4, fixed.**
- `extraction.py:86-92` (`_bytes_bounded`).
- Probe: 4,000 two-byte characters are accepted, and 4,001 are refused.

**8. C-M1, partly fixed.**
- `extraction.py:397-402` (`_NEGATED_MODE`) matches only a negator *directly* before a mode
  word. Probe: the four ruled cases ("Not remote", "This role is not hybrid", "Non-remote",
  "No remote working") give None.
- Still wrong (probe): "Not fully remote" and "This is not a remote role" each give `remote`,
  approved as a `model` claim. My finding and the ruling both say "a negator before" the
  word. One intervening word still defeats it.
- Fix: allow up to two words between the negator and the mode word (for example
  `(?:not|no|non)(?:[\s-]+\w+){0,2}?[\s-]+(?:mode words)`), and add both phrases to
  `test_the_work_mode_is_read_only_when_the_span_names_one`.

**9. C-M2, fixed.**
- `acquisition.py:448-466`: `extraction_state` reads the recorded outcome first.
- `store.py:448-466`: the coverage SQL reads the outcome before the run state, and
  `postings_recorded` counts as `succeeded` only with a published copy.
- Test: `test_an_extraction_cancelled_while_its_call_is_out_keeps_and_shows_its_result`
  (`sources_pending` during the call, then `postings_read`, `succeeded` and one job).

**10. C-M5, fixed.**
- `extraction.py:172-173`: the outcome is `POSTINGS_CONFLICTING` when every posting carries an
  error.
- The state mapping and `MODEL_EXTRACTION_STATE` words are in `vocabulary.ts`.
- `r0024` re-labels the old rows. The page is still counted `no_posting_readable`.

**13. C-M6, fixed.**
- `git grep "decision 13"` over the five files at dcaac22 finds nothing. The edit to r0021 is
  its docstring only, and its SQL is unchanged.

**14. C-M7, fixed.**
- The guard test now refuses another acquisition's page (`InsufficientPrivilege`), refuses the
  sixth start (`CheckViolation`) and checks `started_by_run`.
- The private `_empty_reason` import is gone.
- The listing is tested beside an Adzuna count of 0 in
  `test_a_page_the_model_reads_and_finds_no_advert_on_is_never_none_found`.

## Coordinator's checks

- **202 for a finished acquisition with unsettled extractions.** The behaviour is correct and
  tested (`identity/runs.py:336-350`): 409 `RUN_FINISHED` remains when nothing is unsettled,
  and only the started runs get cancellation rows. The contract text did not follow, as
  described in N2.
- **The `started_by_run` cascade and its lock.** The cascade is correct, and the column has a
  CHECK, a composite FK and an index (r0023). The lock is race-free for "start vs cancel"
  (both sides re-read under it), but it can deadlock (N1).
- **Migrations 0022–0024.**
  - All three are new files, forward-only (`downgrade` raises) and change `CHECK`s by drop and
    add: `body_not_kept`, `not_run`, `outcome`, and the new
    `only_extractions_are_started_by_a_run`.
  - No new table, and RLS and grants are untouched. `CREATE OR REPLACE FUNCTION` keeps r0021's
    REVOKE/GRANT, `SECURITY DEFINER` and the pinned `search_path`.
  - 0020 is not edited; its correction lives in 0022's docstring and column comment.
  - r0021's only change is the docstring decision number (C-M6).

## New issues in the delta

#### Critical
None.

#### Important
None.

#### Minor

**N1. The cancellation lock can deadlock with an acquisition's recording, contrary to the "never
deadlocks" claim.** `evidence/acquisition.py:893-907` with `extraction_runs.py:125`, against
`identity/runs.py:327-328`. Found by reading the code; not reproduced.
- The worker's recording transaction runs in this order:
  1. `lock_workspace_records` (advisory).
  2. `finish_attempt`.
  3. `_record_copies`. For a page whose class keeps the body, this is `store.insert_document`
     (`acquisition.py:804`). Its FK to `nessa.workspaces` takes `FOR KEY SHARE` on the
     workspace row.
  4. Only then `start_extraction` → `lock_started_runs`.
- The API's `cancel_run` takes `lock_started_runs` first, then
  `visible_workspace(lock=True)`, which is `SELECT ... FOR UPDATE` on the same workspace row.
  `FOR UPDATE` conflicts with `FOR KEY SHARE`.
- So for a kept-body page whose structured data gave no posting, a cancel arriving in that
  window gives a cycle. The worker holds `KEY SHARE` and waits for the advisory lock. The API
  holds the advisory lock and waits for `FOR UPDATE`.
- PostgreSQL resolves it with 40P01. `db._transaction` maps that to `StoreUnavailableError`.
  The acquisition step then retries as transient and sees the cancel, or the person's cancel
  fails with a store error and must be repeated. No data is lost, but the claim in ADR
  decision 15 ("taken before any row lock, in the same order on both sides") and in
  `run_store.lock_started_runs`'s docstring is false.
- Context, pre-existing and not new: `cancel_run` locks the workspace row `FOR UPDATE` and
  then inserts `run_cancellations`, whose FK takes `KEY SHARE` on a run row. A worker
  transaction holding that run row `FOR UPDATE` and then writing an event (`append_event`
  updates the workspace row) forms the same kind of cycle. The cascade now does this for up
  to five more runs that are often mid-publish.
- Fix: in `acquire_target`'s recording transaction, take `lock_started_runs` first, before
  `lock_workspace_records` and any insert, whenever the result is model-readable. Correct the
  ADR and docstring wording. The pre-existing pattern is worth one sentence in the ADR's
  open items.

**N2. The cancel route's contract text is stale for the new 202, and the answer does not say
what was cancelled.** `api/routes_runs.py:79-80` and the generated `openapi.json` description.
- The text still says the run "ends `cancelled`" and "A finished run is `RUN_FINISHED`". For a
  finished acquisition with unsettled extractions, the answer is now 202 with the
  acquisition's own terminal status (`failed` or `complete`) and no cancellation request on
  it.
- The 202 body names none of the started runs it cancelled, so a client (Task 8) cannot tell
  from the answer whether anything was cancelled.
- Fix: update the docstring and regenerate the client. Either list the started run IDs whose
  cancellation was requested, or say in the description that each attempt's
  `model_extraction` shows it.

## Summary

All my items are fixed except C-M1, which is partly fixed: a negator one word away still reads
as the mode. The cascade, the estimate, the budget count and the honesty fixes are correct and
tested. Two new Minor issues: the cancellation lock is not taken first on the worker side
(N1), and the cancel route's description is stale for the new 202 (N2).
