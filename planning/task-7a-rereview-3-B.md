# Task 7A, fix round 3: scoped re-review of package B (M1 to M3 from re-review 2-B)

Reviewer B.
- **Diff:** `review-1132cf0..dcaac22.diff` (HEAD dcaac22).
- **Rulings:** items 11, 12 and 15 of `task-7a-fix-round-3.md`.
- **Claims:** the report's "Fix round 3" section, treated as unverified.

I also checked the delta for regressions in my area: coverage, `empty_reason`, the merge and recording lock, and `runs.started_by_run` with its lock (8ce5d2a, migration 0023). This was a read-only review: no tests run (the code and the tests settled every point), no live calls.

## Per-item results

| Item | Verdict | Where | Covering test |
|---|---|---|---|
| **11. B M1**: an attempt counts as pending only while its run is going (read side) | **Fixed** | **Coverage:** `store.coverage` joins each attempt's own run. A `pending` attempt counts as `pending` only while that run is `queued` or `running`, otherwise as `failed` (`store.py:448-449`). Nothing is written, as ruled. **Acquisition view:** once the run has ended, `_left_behind` shows such an attempt as `failed/interrupted` (`evidence/acquisition.py:498-519`). A queued target with an attempt reads `failed` (`:528`), or `cancelled` when the run was cancelled. **Accepted display change:** a target tried in an ended run now shows `failed`, not `not_attempted`. I checked that it is never `sources_pending` or "none found": its URL's coverage is `failed`, which `_empty_reason` never treats as retrieved, so the listing gives `no_source_retrieved`. | `test_acquisition.py:316` (a recording that rolls back via the new `recording_fails` fault point: run `failed`, attempt still `pending` in the database, read as coverage `{failed: 1}`, `no_source_retrieved`, attempt `failed/interrupted`, target `failed`); `:342` (a SIGKILL mid-request, then a cancel: run `cancelled`, attempt still `pending`, read the same way) |
| **12. B M2**: `set_favourite` takes the recording lock | **Fixed** | `lock_workspace_records` is taken first, then the workspace row (`evidence/acquisition.py:694-701`). That matches the worker's order: recording lock, then the cancellation lock, then the workspace row through `append_event`. `run_idempotent` locks nothing before `execute`. | `test_acquisition.py:381` (the merge's lock is held on another connection; the PUT waits, then answers 404 with no favourite row, instead of the earlier 500 or a silently lost mark) |
| **15. B M3**: ACQ-03 cites the renamed test | **Fixed** | `docs/requirements-register.md:444` cites only `test_a_page_whose_structured_data_holds_no_posting_is_unread_never_none_found`; the old name is gone from the register. | n/a |

## Regression check in my area

- **Coverage and `empty_reason` with fix round 3's C-M2 change.** A recorded outcome now decides first, even for a cancelled extraction run (DUR-05):
  - a published posting is `succeeded`;
  - `no_posting_found` is `no_posting_found_by_model`;
  - any other recorded outcome, conflicting postings included, is `no_posting_readable`.

  With nothing recorded, a queued or running run is `pending` and any other state is `no_posting_readable` (`store.py:450-458`). `no_posting_found_by_model` still never becomes "none found", and nothing left behind can become `sources_pending`. **No regression.**
- **Merge and recording lock.** These are unchanged: `acquire_target` still takes the lock first in its recording transaction, and so does the extraction's recording. **No regression.**
- **`runs.started_by_run` and `lock_started_runs` (8ce5d2a, migration 0023).**
  - **The migration:** forward-only. The backfill from `page_extractions` runs before the CHECK `only_extractions_are_started_by_a_run` and the composite foreign key are added, so existing rows pass. No new grant is needed: only the SECURITY DEFINER `submit_page_extraction` writes the column, and no runtime role may update it.
  - **Lock order:**
    - API cancel: cancellation lock, then the workspace row (`identity/runs.py:327`).
    - Worker recording: recording lock, then (in `start_extraction`) the cancellation lock (`extraction_runs.py:125`), then the workspace row through events.
    - `set_favourite`: recording lock, then the workspace row.

    No transaction takes the workspace row before either advisory lock, so I found no deadlock cycle.
  - **The cancel cascade:** each started run gets its own cancellation request; cancelling a finished acquisition with nothing unsettled still answers `409 RUN_FINISHED`; the receipt still has no output. A cancel after the acquisition finished answers 202 with the finished run, which was ruled acceptable. **No regression.**

## New issues

### Critical
None.

### Important
None.

### Minor
None.

## Counts
3 items checked: 3 fixed, 0 partly fixed, 0 not fixed. New issues: Critical 0, Important 0, Minor 0.
