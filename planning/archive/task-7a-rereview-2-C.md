# Task 7A re-review 2-C: fix round 4, items 3–7

**What I reviewed.** Items 3–7 of `task-7a-fix-round-4.md`, the "Fix round 4" section of
`task-7a-report.md` (treated as claims) and `review-dcaac22..8eceb3b.diff` (6 commits, 1.9k
lines). I also checked the coordinator's two questions: whether the N1 lock order holds on
every path that can meet a cancel, and whether the ceiling matches what the activity can
reserve.

**State of the repository.** HEAD is 6bf6f4e, one commit past 8eceb3b. That commit changes
documentation only (`docs/adr/0009`, `docs/reviews/session-1.md`), so the code I read and
probed is the code at 8eceb3b.

**How I checked.** Read-only, with a clean tree apart from the untracked docx. I ran no
suites. I ran one offline probe (`uv run --locked --offline python -c ...`, no bytecode
written) on the pay reader, the work-mode reader and `acquisition_model_spend`. To answer
the ceiling question I read the installed DBOS (3.3.0) step and recovery code. I did not
read `.env` or NESSA_HOME, made no live calls and dispatched no subagents.

**Not re-raised (already accepted):** `per_run_nano_usd` as a ceiling over 3 attempts, `£30kpa`
reading as £30,000 a year, the negator rule leaning towards unclear, and the pre-existing
`cancel_run` lock pattern.

## Verdicts

| Item | Verdict | Evidence |
|---|---|---|
| 3. Attached pay periods | **Fixed** | See item 3 below. |
| 4. `acquisition_model_spend` is the true ceiling | **Fixed** (new Minor N1) | See item 4 below. |
| 5. C-1 N1: cancellation lock first | **Fixed** | See item 5 below. |
| 6. C-1 N2: the 202 names what it cancelled | **Fixed** | See item 6 below. |
| 7. C-M1 residual: negator up to two words before | **Fixed** | See item 7 below. |

Totals: 5 fixed, 0 partly fixed, 0 not fixed.

### Item 3: attached pay periods (fixed)

- **Code:** `evidence/extraction.py:235-241` (`_ATTACHED_PERIOD_WORDS`, `_THOUSANDS`),
  `:263-266` (`_PERIODS` also matches after `\d[kK]`) and `:281-297` (`_misreadable` lets
  only an attached period follow a number or its `k`).
- **Read as exact amounts with their period:** `£30,000pa`, `£30,000p.a.`, `£14.50ph`,
  `£14.50p/h`, `£30,000annually`, `£14.50hourly`, `£30kpa`, `£30,000-£35,000pa`, and the
  spaced `£14.50 ph`.
- **Still `salary_invalid`:** `£1.2m`, `£2bn`, `£30-35k`, `£30,000ish`, `£30,000pay` and
  `£14.50phr`.
- **Unchanged reading:** `£32,000 to £36,000 per year`.

### Item 4: the true ceiling (fixed, with new Minor N1)

- **Code:** `extraction_runs.py:73` computes `run_worst_case_nano_usd(extraction.worst_case_nano_usd, …)`.
  `identity/activity.py:128-133` defines it as `ACTIVITY_MAX_ATTEMPTS` × the task's
  per-attempt worst case. `workflow.py:52` uses the same `ACTIVITY_MAX_ATTEMPTS` for the
  step's `max_attempts`. The activity reserves `task.worst_case_nano_usd(model_id)`
  (`activity.py:462`), and `PAGE_EXTRACTION_TASK` is built on that same function.
- **Values (probe):**
  - Test model: 10,200,000 per run and 51,000,000 per acquisition.
  - Production model: 143,250,000 per run and 716,250,000 per acquisition.
  - Both per-run figures are within the default 150,000,000 run limit.
- **Descriptions:** they now say "maximum".
- **Does it match what the activity can reserve?** Within one execution of the DBOS step,
  yes. After a worker crash, not quite (N1).

### Item 5: cancellation lock first (fixed)

- **Code:** `evidence/acquisition.py:892-897` takes `lock_started_runs` as the recording
  transaction's first statement whenever `model_readable(result)`
  (`extraction_runs.py:115-118`, the same predicate `start_extraction` returns on). That is
  before `lock_workspace_records` (`:900`) and before any insert.
- **Docs:** the ADR decision 15 sentence and the `run_store.lock_started_runs:565` docstring
  are corrected. The pre-existing pattern is recorded in the open items.
- **Test:** `test_a_cancel_while_a_kept_page_for_extraction_is_recorded_ends_without_a_store_error`
  reproduces the old cycle properly. The blocker's `FOR NO KEY UPDATE` lets the document's
  key-share lock through but holds the cancel's `FOR UPDATE` back. The test then checks a
  202, one attempt left `succeeded`/`body`, and `acquisition_cancelled`.
- **Every path that can meet a cancel.** A cancel is `lock_started_runs`, then the workspace
  row `FOR UPDATE`. `run_idempotent` only reads a receipt before `execute`, so the advisory
  lock really is the API's first lock. These are the only places that take the advisory lock:
  `cancel_run`, the model-readable recording, and `submit_page_extraction` inside that same
  recording. So the remaining question is whether anything waits for it while holding a
  workspace-row lock:
  - **A model-readable page,** body kept or not: no. It takes the advisory lock first.
  - **A page that is not model-readable** (JSON-LD postings, `jsonld_invalid`,
    `conflicting_job_postings`): no. It never takes the advisory lock (`start_extraction`
    returns before any lock), so its key-share and event locks are released at commit, and a
    waiting cancel simply proceeds.
  - **Adzuna:** no. Its `extraction` is `no_matching_adverts` or None, so it is never
    model-readable and never takes the lock.
  - **A failed or blocked result:** no. It is not `SUCCEEDED`, so it never takes the lock.
  - **The extraction run's own transactions** (`_settle`/`record_extraction`, `publish`):
    no. They never take the advisory lock.
  - **`set_favourite`** takes `lock_workspace_records` and then the workspace row, the same
    order as the recording, so there is no new cycle.
  - **Remaining:** only the accepted, pre-existing row-lock pattern (the workspace row
    `FOR UPDATE`, then a run row's key share).

### Item 6: the 202 names what it cancelled (fixed)

- **Code:** `identity/runs.py:316-362` (`Cancellation`; `asked` is the run while it is
  unsettled plus its unsettled started runs), `api/schemas.py:341` (`RunCancelOut`) and
  `api/routes_runs.py:76-90` (response model and corrected docstring). The regenerated client
  carries `cancellation_requested` (`openapi.json`, `types.gen.ts`).
- **Receipt:** it holds IDs only.
- **Tests:** all three shapes are tested (the run alone, started runs only, and both).

### Item 7: negator up to two words before (fixed)

- **Code:** `evidence/extraction.py:413-418`.
- **Unclear (probe):** "Not fully remote", "This is not a remote role", the four round 3
  cases, and the control "Not in the office every day".
- **Unchanged:** "Fully remote" and "Hybrid, two days a week in the office".

## New issues in the delta

#### Critical
None.

#### Important
None.

#### Minor

**N1. After a worker crash, DBOS gives the activity step a fresh set of attempts, so a run can
reserve more than the stated ceiling. The key's run limit is the only hard bound.**
`identity/activity.py:128-133`, `evidence/extraction_runs.py:73`, `api/research_schemas.py`
(`ModelSpendOut`: "The most one run may spend").

*Evidence, read in the installed DBOS 3.3.0:*
- A step's retries are an in-memory loop. `dbos/_core.py:2269` sets
  `attempts = max_attempts if retries_allowed else 1`, and the outcome is recorded only when
  the step ends.
- So a step interrupted by a crash is run again on recovery with a full `max_attempts`.
- `model_run_workflow` sets no `max_recovery_attempts`, so the default of 100 applies
  (`dbos/_registrations.py:10`).
- Across recoveries, `_prepare` keeps reserving while
  `run_committed + worst ≤ run limit` (`activity.py:449-462`).
- `_recorded_failure` stops a new attempt only after a terminal failure. Attempts reconciled
  below their reservation (`_COMMITTED` counts actual cost) leave room under the limit.

*What the gap is:*
- With the default limit, a production run can reach 150,000,000 against the stated
  143,250,000.
- A test-model run can reach 150,000,000 against the stated 10,200,000.
- Both need crashes in the middle of the step. The implementer flagged this as unverified
  (concern 5).

*Why it matters:* MODEL-08's figure is described as a maximum, "never an expected cost", and
the ruling asked for the true ceiling. This does not change the accepted per-run meaning: it
is a crash-recovery hole in it.

*Fix:* make the stated figure true by construction. In `_prepare`, refuse a reserving attempt
(`spend_state` not `none`) once the run already has `ACTIVITY_MAX_ATTEMPTS` of them, ending
the run `provider_unavailable`. Alternatively, state the run limit as the hard bound beside
the estimate.

## Summary

All five items are fixed. The N1 lock order now holds on every path that can meet a cancel:
model-readable pages, other pages, Adzuna, failed or blocked results, and the extraction
run's own transactions. The only cycle left is the accepted pre-existing row pattern. The
ceiling is computed with the reservation's own functions and is right for one execution of
the DBOS step. DBOS's fresh attempt budget after a crash can exceed it, within the key's run
limit (new Minor N1).
