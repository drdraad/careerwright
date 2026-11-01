# Task 7A, fix round 2, part 1: scoped re-review of package B

Reviewer B. Scope:
- `review-b24d264..dc8dd4d.diff`: part 1's four commits, de6ada8, 48a75e5, 06611ce and dc8dd4d.
- Rulings: items 1–4 of `task-7a-fix-round-2.md`.
- The report's "Fix round 2" section, treated as unverified claims.

Part 2 (`dc8dd4d..1132cf0`, HEAD 1132cf0) I inspected in git only where it touches a part 1 fix: `store.coverage`, `_empty_reason`, the recording lock and the N1 integration test.

Read-only. No tests were run, because the code and the existing tests settled every doubt. No live calls.

## Per-item results

| Item | Verdict | Where | Covering test |
|---|---|---|---|
| **1. B N1** a fetched page whose structured data held no posting | **Fixed** | `UNREADABLE` is now every `Extraction` except `no_matching_adverts` (`records.py:95`), so `no_job_posting` counts as `no_posting_readable` in `store.coverage` and in the run summary. Adzuna is `no_matching_adverts` only when its own `count` is 0; an empty page of a search that matched some, or results it could not read, stay `no_job_posting`, i.e. unread (`acquire.py` `_adzuna_extraction`). Migration 0019 widens the CHECK and relabels only Adzuna rows with `no_job_posting` and `total_matching = 0`, which is safe. ACQ-03 and STATE-02 are updated. **Part 2 keeps it** (checked at HEAD): `store.coverage` (`store.py:429-470`) gives a model-read page with outcome `no_posting_found` its own `no_posting_found_by_model`. A run not started, failed, cancelled or with nothing verified is `no_posting_readable`, and a queued or running run is `pending`. `_empty_reason` (`acquisition.py:593-611`) returns `no_posting_found_by_model` before `none_found_in_sources_checked`. So **`no_posting_found_by_model` is never counted as "none found"**, even beside an Adzuna count of 0. Its words in `vocabulary.ts:325` say "This isn't a sign there are no vacancies". | `test_pages.py:246`; `test_acquisition.py:242` (`/org-only` → `no_posting_readable`, `not_run: no_model_key` at HEAD), `:971` (Adzuna count 0 is the one "none found"); at HEAD `test_extraction.py` (`_empty_reason` with an Adzuna none plus a model none gives `no_posting_found_by_model`) and `test_page_extraction.py:201` |
| **2. B N2** recording lock and overlapping runs | **Fixed** | `store.lock_workspace_records` (`pg_advisory_xact_lock` per workspace) is taken first in the recording transaction, before the authorisation check, the candidate read and the merge (`acquisition.py:842` at dc8dd4d, `:849` at HEAD). Part 2's extraction recording takes it too (`extraction_runs.py:132`). | `test_acquisition.py:558` (three overlapping runs: 9 succeeded attempts, none pending, 1 job, 9 copies each with claims; the report says it was red without the lock, which I did not re-run) |
| **3. B-M2** COMPLETE-only proposal and summary | **Fixed** | Dedicated test, parametrised `cancelled` and `failed`. It seals real outputs for both runs, shows neither while the run is not complete, then shows both once it is complete, so the gate is the only difference. The report notes there is no red proof (the rule already held). | `test_acquisition.py:1160` |
| **4. B N3** `copy_counts` | **Fixed** | Removed; no references remain. | n/a |
| **4. B N4** overrun with an unusable reply | **Fixed** | The check moved into the activity. `RunTask.exceeded_bound` runs after `measured_usage` on every path, an invalid or truncated reply included, and overrides any other classification with `bound_exceeded` (`activity.py:547` at dc8dd4d, `:554` at HEAD). The cost stays booked from the measured usage. | `test_source_search.py:199`; `test_acquisition.py:1111` parametrised with `search_overrun_invalid` |
| **4. B N5** typed reason for an unkept body | **Fixed** | `BodyNotKept` (`contact_unlocated`, `block_unredactable`) in its own column, with a CHECK and the CHECK `a_body_not_kept_is_not_kept` (allowed only with `retention = excerpts`), exposed as `SourceAttemptOut.body_not_kept`. Migration 0020 moves the old marker out of `rights_status`. That data rewrite is safe: the escaped `LIKE` matches only the marker, and every such row already had `excerpts`. | `test_redaction.py:201` (asserts `[` no longer appears in `rights_status`), `:259` |
| **4. B N6** the worker and exemplars | **Fixed** | Restrictive policies in 0020: `worker_keeps_exemplars` (FOR DELETE, `NOT exemplar`) and `worker_leaves_pasted_copies` (FOR UPDATE: never a pasted copy, never onto an exemplar). The merge path is unaffected, since merged and kept jobs are never exemplars. | `test_acquisition.py:598` (as `pg_worker`: the vacancy deleted, the example kept, the pasted copy not moved) |
| **4. B N7** `sources_pending` | **Fixed** (see new issue M1) | `EmptyReason.SOURCES_PENDING` comes first once any coverage entry is `pending` (`acquisition.py:566` at dc8dd4d). Its words are in `EMPTY_REASON` (`vocabulary.ts`). At HEAD, a page whose extraction run is queued or running also counts as `pending`. | `test_acquisition.py:275` |

**Migrations 0019 and 0020.**
- Both are forward-only (`downgrade` raises).
- Neither adds a table. The one new grant is `UPDATE (body_not_kept)` for the worker. The new policies are restrictive, so they only narrow what 0017's grants allow.
- Both data rewrites are scoped and safe (above).

## New issues

### Critical
None.

### Important
None.

### Minor
- **M1. A stranded `pending` attempt now reads as "still checking" forever.**
  - **Where:** `backend/src/nessa/evidence/acquisition.py:593-611`, `backend/src/nessa/evidence/store.py:429-470`.
  - **What happens:** coverage takes each URL's latest attempt, and any `pending` one yields `sources_pending` ("The list updates when it's done"). Two paths can leave an attempt `pending` after its run has ended:
    - a non-transient error in the recording transaction, which rolls the recording back; the step's `except Exception` then raises `LabelledError` and the step is not retried;
    - a worker crash during a request, followed by a cancel, so the step never runs again.

    Part 2 adds more code to that transaction (`start_extraction`), which widens the first path. In both cases the listing promises an update that never comes, a failure shown as in progress (GC6). Before N7 the same row read `no_source_retrieved`.
  - **Fix:** settle the run's remaining `pending` source attempts as `failed/interrupted` in `publish_acquisition` and when a cancellation is published. Or count a `pending` attempt as pending only while its run is `queued` or `running`.
- **M2. A favourite marked during a merge can be lost.**
  - **Where:** `backend/src/nessa/evidence/acquisition.py` `set_favourite`, `backend/src/nessa/evidence/store.py` `merge_jobs`.
  - **What happens:** the API's favourite insert does not take the workspace recording lock. If it commits between the merge's favourite copy and its `DELETE FROM nessa.jobs`, the cascade removes the person's new mark. If the delete commits first, the insert fails its foreign key and the API returns an internal error. The window is narrow.
  - **Fix:** take `lock_workspace_records` in `set_favourite`.
- **M3. ACQ-03 cites a test that no longer exists.** `docs/requirements-register.md:444` still names `test_pages.py::test_only_structured_data_read_with_no_posting_in_it_says_no_posting`, which de6ada8 renamed to `test_a_page_whose_structured_data_holds_no_posting_is_unread_never_none_found`. The row cites both. **Fix:** drop the old name.

## Counts
8 items checked: 8 fixed, 0 partly fixed, 0 not fixed. New issues: Critical 0, Important 0, Minor 3.
