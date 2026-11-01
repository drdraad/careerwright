# Task 7A review, package B (runs, cancellation, repair bound, persistence, API, jobs, freshness, pasted text, source search)

Reviewer B, `8276485..5c5e5bb`. I read the 7,382-line package in five passes: API and schemas; `evidence/acquisition.py`, `freshness.py`, `jobs.py`, `records.py`, `search*.py`, `store.py`, `workflow.py`; identity (activity, runs, run_store, worker, workflow) and migration 0013; the three profile agents and the tests; then the register and runbook. I treated the report as unverified claims. Outside the diff I made one focused check per named risk; each is listed below with what I checked. I ran one focused check: a pure simulation of `_record_copies`'s matching rule against `jobs.group_copies`, run with `uv run --no-sync python` and a script in the scratchpad (result under I1). I ran no pytest suite and made no live calls, and the working tree is unchanged.

### Spec Compliance
- ❌ Issues found:
  - **Missing (acknowledged by the implementer).** Slice 7A asks for "structured fields first, model extraction only where needed". ACQ-03 model extraction, and with it the model part of ACQ-04, is not built. The register states this honestly (`docs/requirements-register.md:444`), but because it is missing, a real posting page without JSON-LD becomes an empty success (C1).
  - **Misunderstood: "a failed fetch is never no vacancies".** This is met for fetch failures and refusals. It is not met for a page that is retrieved but cannot be read: that page counts as "none found" (C1).
  - **Misunderstood: "multi-city counted once" and syndicated dedupe.** The rule is met by the pure `group_copies`, but persistence never calls it. The stored path matches on first fit, depends on arrival order and never merges jobs (I1).
  - **Misunderstood: ruling 8, pasted text kept apart.** The kept-apart rule holds in the database and in matching, but not in the job listing's counts (I2).
  - **Missing: a truncated result is never presented as complete.** Adzuna's total match count is computed and then dropped (I3).
  - **Missing: a bounded search cost.** Nothing in code bounds or detects the number of searches. The reservation depends on Meta enforcing `max_tool_calls` (I4).
- ⚠️ Cannot verify from diff:
  - The regenerated client (`apps/web/src/generated/**` is excluded from the package). For drift I rely on the report's `make check`.
  - What the two live searches printed in `excluded`. The ledger and the report record only "0 candidates" (see risk 4).
  - Whether `ADZUNA_APP_*` exist in `.env`. I may not read it.
  - The `make acceptance` and `make check` results. The report claims both passed; I did not re-run them.
  - Whether Meta enforces `max_tool_calls`.

**Named risks: what I checked**

1. **Cancellation.** I traced `runs.cancel_run`, `run_store.request_cancellation`/`pending_cancellations`/`pending_outbox`, `worker.act_on_cancellations`, `activity._prepare`/`_settle`/`publish`, `run_store.interrupt_unfinished_attempts`/`finish_attempt`/`finish_run`, and the worker RLS on `model_attempts` (migration 0002, lines 225-230). Case by case:
   - **Cancel before dispatch.** The outbox entry is never dispatched, and the run is published `cancelled`.
   - **Queued but dispatched.** `_prepare` returns `cancelled` before any reservation (`activity.py:383`).
   - **Between the reservation and the request.** Nothing re-checks, so the request is sent and booked. This is documented.
   - **During a request.** `publish(cancelled)` marks the held attempt `interrupted/unknown`. `_settle` then overwrites it with the reconciled cost, because `finish_attempt` has no `finished_at` guard and the worker's RLS ignores run status. The integration test asserts `reconciled`.
   - **After completion.** The API answers `409 RUN_FINISHED`. In the race where the run finishes after the API check, `finish_run` changes only queued or running runs, so nothing changes.

   No reservation is ever leaked: in the worst case it stays committed as `unknown`. The DBOS workflow is cancelled, and `publish` emits `run.state_changed` with state `cancelled`. RLS and grants on `run_cancellations`: the API has SELECT and INSERT scoped by workspace; the worker reads unscoped (identifiers only) and may update only `signalled_at`. Ruling 11 is safe under repeats: `ON CONFLICT DO NOTHING`, one event, `run_idempotent`, and `409` after the run is terminal.
2. **Repair bound.**
   - **Coverage.** `RepairBound` is on discovery, interview and slate_explanation. `source_search` cannot repair (output retries 0, `request_limit=1`), and the connection check uses `retries=0`.
   - **Unit.** The allowance in tokens is applied as a byte count. That is conservative, because one token is at least one byte.
   - **Reservation.** It covers the whole repair input. Each request reserves prompt, schema, the maximum output (the rejected output that is sent back) and the allowance, times `MAX_REQUESTS` (`profile/discovery.py:286-297`; the same in `interview.py:533` and `slate_explanation.py:713`).
   - **Regressions.** I found none. A `ModelRetry` text that fits is sent unchanged (tested), and the cause is rewritten only on feedback that was cut.
3. **Empty success.** A failed or blocked fetch ends `failed/retrieval_failed` or `failed/source_blocked`, and the listing says `no_source_retrieved` (tested). Two gaps remain: an unreadable page becomes `none_found_in_sources_checked` (C1), and Adzuna truncation is invisible (I3). A complete search with no candidates carries no reason (I5).
4. **Zero candidates in the source search.**
   - **What the code rules out.** The candidate filter, the permission check and URL normalisation cannot explain an empty result with nothing excluded:
     - The manifest default is `permitted` (`evidence/sources.json`, `sources.rule_for`), so only LinkedIn, Indeed and Adzuna are refused.
     - `_normal` changes only `grounded`.
     - `check_search` lists every dropped candidate in `excluded` with a reason, and the smoke prints that list (`tools/live_smoke.py:540-545`).
   - **What the output size shows.** Non-reasoning output was 153 and 213 tokens, including the two query strings. That is too little for a list of URL and title pairs, so the model itself returned an empty or almost empty list.
   - **Most likely cause: the prompt (`search.py:53`).** It asks for "an individual job posting … preferably on the employer's own careers site". It bans "Indeed, LinkedIn and other sites that need a sign-in", an open-ended phrase the model can read as every board. And it allows an empty list. Meanwhile the tool is two low-context searches (`search_context_size="low"`, `search_agent.py:82`), whose sources for a query like "<role> jobs <city>" are mostly board listing pages, not individual postings. The schema is not the cause: `NativeOutput` parsed and both runs were `complete`.
   - **Not proven.** The `excluded` list and the source hosts were not ledgered.
   - **Prompt injection.** Every candidate is re-checked by `check_url` and the manifest, and is marked `grounded` only if the search returned it. The fetch path re-checks everything, and the person chooses what to acquire. Ungrounded candidates are still offered, labelled as such.
   - **Run kind.** The search is a run kind on the one bounded activity (`worker.TASKS`, `submit_run`).
   - **Reservation.** It is not sound without Meta's enforcement (I4).
   - **Synthetic-only rule.** The test model's synthetic-only rule is kept by `submit_run` and `model_refusal` and by the database CHECK; a further CHECK keeps demo workspaces from searching.
5. **Persistence.**
   - Migration 0013 is forward-only (`downgrade` raises), and RLS is enabled on all eight new tables.
   - Column-level grants keep sealed nonces and ciphertext from both runtime roles.
   - API SQL runs in `actor_transaction` (routes and `run_idempotent`), worker SQL in `run_transaction`, and the dispatcher reads in `system_transaction`.
   - Reseal covers `source_documents`, and the stale check is generic over every `key_version` column (`cli.py:91-105`).
   - Money is in integer units. `cost_nano_usd` is 0 only where it is known to be free, and unknown values are null.
   - Claim spans and fields have no database constraints (M3).
6. **Jobs and freshness.** Dedupe and the agency rule are correct pairwise. Multi-city counting fails across copies (I1). The maximum ages are 24 h, 7 d and 48 h, as required (`freshness.py:30-36`). A failed refresh moves `last_attempt_at` only (`store.job_attempted`, tested in the database). The timestamps are kept separately. Pasted text is kept apart in the database (CHECK `live_jobs_were_retrieved`, and exemplars are excluded from `candidate_copies` and `job_verified`) but not in the listing's counts (I2).
7. **Workflows.** `identity/workflow.py` changes only the constant behind `WORKFLOW_NAME`, so the model workflow's step names and order are unchanged and `nessa-l0-1` can stay. The acquisition workflow carries the run ID and positions only; its errors are labels or type names, and the journal is asserted free of host names. Each failure class has one retry owner: the DBOS step owns both source and store failures, the fetcher uses `retries=0`, and the client does not retry. `DBOS.list_workflows(name=[...])` accepts a list in the locked DBOS release.
8. **API.**
   - Every write goes through `run_idempotent` with an `Idempotency-Key`. The search takes `expected_profile_version`. Ruling 11's exception is sound for cancel and for favourites (an idempotent mark with no versioned state), but it is not recorded (M10).
   - Errors are `NessaError` codes with label-only details.
   - Live-vacancy mode is gated on `adzuna_configured` (`workspaces.create_workspace`), and Adzuna searches are allowed only in live-vacancy workspaces.
   - `vocabulary.ts` uses only generated enums. The new state fields, however, are free strings (I6).
   - One receipt race can store model output (M1).
9. **Register honesty.** No row marks ACQ-03, the model part of ACQ-04, the live Adzuna qualification or source-search candidate quality as done. ACQ-03, ACQ-04 and JOB-05 stay `planned` with their open items, and DUR-05 stays `planned`. Some rows do overclaim:
   - PROP-02 and JOB-02 (I1).
   - JOB-08's "two searches" (I4).
   - ACQ-03 and ACQ-07 say a page "says `no_structured_job_posting`", but that label never reaches an attempt, the API or the database (C1).

### Strengths
- **Cancellation is well layered.** It has an identifiers-only request table read like the outbox, a dispatch filter so a run cancelled while queued never starts, an activity check before reservation, and one terminal publication. Interrupted attempts are booked conservatively and then corrected to the real cost. The integration tests assert the attempts, the journal status and the missing publish step, which tests the contract rather than the code's shape.
- **`RepairBound` is correct and well tested.** It removes the rejected-output quote at the source and cuts at whole problems. The tests drive the real agents with a fake provider and measure exactly what the provider receives, per kind. The reservation formulas already counted the resent output, so the fix closes the overrun without loosening any bound.
- **Migration 0013 encodes its invariants in the database.** The CHECKs include `only_acquisitions_name_no_model`, `demo_workspaces_never_acquire_or_search`, `refusals_and_failures_say_why`, `only_clean_copies_are_published`, `live_jobs_were_retrieved` and `pasted_text_is_its_own_route`. Grants are column-level, and the worker writes only for its own run while the requester is authorised.
- **Acquisition failures follow the failure-is-never-empty rule for fetches.** An all-failed run is `retrieval_failed`, an all-refused run is `source_blocked`, and `empty_reason: no_source_retrieved` is tested end to end, including the retry chain with `retry_of`.
- **Freshness is pure, small and complete** against spec section 11, with a test at each bound and one just past it.
- **The source search gives the model only the role and the city.** One request, no repair, candidates re-validated deterministically, and a `grounded` flag.

### Issues

#### Critical
**C1. A page that is retrieved but cannot be read becomes "none found"; the parse issue is discarded (GC6).**
- **Where:** `backend/src/nessa/evidence/acquire.py:73,175` (`issues` computed); `backend/src/nessa/evidence/store.py:270` (`finish_attempt` has no field for it); `backend/src/nessa/evidence/acquisition.py:469-476`; `backend/tests/integration/test_acquisition.py:48,118,135`; `docs/requirements-register.md:444,448`.
- **What happens:** `pages.parse` returns `no_structured_job_posting` (or `jsonld_invalid`), and `AcquisitionResult` carries it. No code in `acquisition.py` or `store.py` reads `result.issues`, so the attempt is stored `succeeded` with `reason` null. The run ends `complete` with `summary.succeeded` counting the page and `job_ids: []`. If the workspace has no jobs, the listing then says `empty_reason: none_found_in_sources_checked`.
- **Why it matters:**
  - Model extraction is not built, and no extraction is tuned before Task 7b. So every real posting page without JSON-LD produces this state, an unknown presented as a zero result ("no matching listings in the sources checked").
  - The integration test makes it the expected behaviour. `/plain` is an advert ("Gardener … Apply by email.") and is asserted `("succeeded", None)`.
  - The register's 7A parts of ACQ-03 and ACQ-07 claim the page "says `no_structured_job_posting`". That holds only for the in-memory parse result, not for any attempt, API response or database row.
- **Fix:**
  - Persist the parse issues on the attempt, for example an `extraction` label column with a CHECK.
  - Count "retrieved, no readable posting" separately in the summary and the coverage.
  - Add an `empty_reason` such as `no_posting_readable` for the case where any retrieved source had a parse issue. Only a page whose structured data was read and holds no posting may support `none_found_in_sources_checked`.
  - Assert the label in the `/plain` test and correct the two register rows.

#### Important
**I1. In production, a multi-city job can be counted twice: stored dedupe matches on first fit, depends on arrival order and never merges.**
- **Where:** `backend/src/nessa/evidence/acquisition.py:593-609`; `backend/src/nessa/evidence/jobs.py:258,286`; `backend/tests/domain/test_jobs.py:130,190`; `docs/requirements-register.md:405,458`.
- **What happens:** `_record_copies` attaches each copy to the first stored job it matches, oldest first, and creates a new job otherwise. It never joins two existing jobs. The order-independent `group_copies` and `city_views`, the functions the JOB-02 and PROP-02 tests exercise, are used by persistence nowhere (only by `tools/live_adzuna.py` and tests).
- **Reproduction (scratchpad simulation of `_record_copies`'s rule):** three copies of one vacancy, arriving board first:
  - a board copy for Leeds with the apply URL;
  - a board snippet for Manchester naming the employer;
  - the employer's own page for Leeds and Manchester.

  The stored path gives **2 jobs** (`[1, 2, 1]`); `group_copies` gives 1. `total_jobs` then counts one vacancy twice. PROP-02 and JOB-02 are marked "verified" on a function production does not call.
- **Fix:**
  - When a new copy matches several jobs, merge them: re-point their copies to the oldest job and drop the rest.
  - Or compute canonical membership with `group_copies` over the candidate set.
  - Test the stored path with several arrival orders (integration), or move the stored rule into a pure function that the property test covers.
  - Correct PROP-02 and JOB-02.

**I2. The listing counts exemplars as jobs and pasted text as a retrieved source (ruling 8, JOB-06, GC6).**
- **Where:** `backend/src/nessa/evidence/acquisition.py:460-476`; `backend/src/nessa/evidence/store.py:354` (`coverage`), `:668` (`jobs` has no exemplar filter).
- **What happens:**
  - `total_jobs` and `city_counts` include the person's pasted examples.
  - `coverage` counts each pasted attempt as `succeeded`.
  - Any exemplar suppresses `empty_reason`.
- **Example:** a person whose every fetch failed but who pasted one example gets `total_jobs: 1`, `city_counts: {Manchester: 1}`, `coverage: {succeeded: 1, failed: N}` and no `empty_reason`. The failed retrieval is now hidden behind an example that "is never a live vacancy".
- **Fix:** exclude exemplars from `total_jobs`, `city_counts` and the `empty_reason` decision (report `exemplars` as their own count), and exclude the `pasted_text` route from `coverage`. Test the combined case.

**I3. Adzuna's total match count is dropped, so a truncated search looks complete (GC6, spec section 7 coverage).**
- **Where:** `backend/src/nessa/evidence/acquire.py:74,230`; `backend/src/nessa/evidence/store.py:270`; `backend/src/nessa/api/research_schemas.py:286-320`.
- **What happens:** `AcquisitionResult.total` (Adzuna's `count`) is never stored or exposed. One page of at most 50 results is the run's whole `complete` result, and the listing gives no sign that more exist.
- **Fix:** store `total` on the attempt, expose "retrieved n of total" in `AcquisitionOut` and the listing coverage, and treat `total > retrieved` as an explicit partial result. Test it with the fixture, whose `count` should exceed its results.

**I4. The source search's reservation depends on Meta enforcing `max_tool_calls`; nothing in code bounds or detects extra searches (MODEL-08, R5).**
- **Where:** `backend/src/nessa/evidence/search.py:48,161`; `backend/src/nessa/evidence/search_agent.py:99`; `docs/requirements-register.md:464`.
- **What happens:**
  - Searches run on Meta's side inside the one request, so `request_limit=1` does not limit them.
  - On the test model, a third search (a $0.0025 fee plus its tokens) takes the actual cost (about $0.0056 for two) past the $0.008 reservation.
  - Nothing compares `usage.web_search_queries` with `MAX_TOOL_CALLS` after the call.
  - JOB-08 records "bounded to one request and two searches" as verified, but the test only asserts that the setting is sent.
- **Fix:**
  - After the call, treat `web_search_queries > MAX_TOOL_CALLS`, or input tokens above the bound, as a recorded overrun: an attempt outcome label, and the output refused.
  - Qualify enforcement once, with a capped live call that sends `max_tool_calls: 1` and expects one search.
  - Reword JOB-08 until then.

**I5. A complete source search with zero candidates gives no reason (GC6, STATE-02 by analogy).**
- **Where:** `backend/src/nessa/api/research_schemas.py:286-292`; `backend/src/nessa/evidence/search.py:120`; `backend/tests/domain/test_source_search.py:88`.
- **What happens:** live rows 27 and 28 were `complete`, with 14 and 21 sources and no candidates. The contract cannot tell three cases apart: "the model proposed none from N pages", "every proposal was excluded" and "the search returned nothing". The test calls this result "a valid search that found nothing", so Task 8 has no words for it except "nothing found".
- **Fix:** add an `empty_reason` enum to `SearchProposal` (`no_candidate_proposed`, `all_excluded`, `search_returned_nothing`). Describe zero candidates as "not evidence there are no vacancies", give each reason words in `vocabulary.ts`, and record `excluded` and the source hosts in the live smoke's ledger notes (risk 4).

**I6. The new state values are free strings in the OpenAPI contract (GC10, ARC1-10).**
- **Where:** `backend/src/nessa/api/research_schemas.py:42,89,112,314`; the `coverage` keys; `SearchExcluded.reason` in `backend/src/nessa/evidence/search.py`; `Skipped.reason` in `backend/src/nessa/evidence/acquisition.py`.
- **What happens:** `empty_reason`, target `status` (including `not_attempted`), the skipped reason, the attempt reason and the exclusion reason are typed `str`. The generated client therefore has no enums for them, and Task 8 must copy them by hand to give each one words. That includes STATE-02's own carrier, `empty_reason`.
- **Fix:** define them as `StrEnum`s in the domain modules, use them in the schemas, and regenerate the client.

#### Minor
- **M1. The cancel receipt can hold model output.** `backend/src/nessa/api/routes_runs.py:76` stores `run_out`, whose `connection_check_output` (`backend/src/nessa/identity/runs.py:360`) opens an accepted output without checking the run's status. A cancel that lands between `_settle` and publication would put a connection check's model output into the plaintext receipt, against CLAUDE.md's receipt rule. **Fix:** leave the output out of the cancel receipt, or show it only for `COMPLETE` runs.
- **M2. A cancelled search shows its proposal.** `backend/src/nessa/evidence/search.py:253-258` does not require `COMPLETE`, unlike the profile readers (`profile/conversation.py:119`, `profile/exploration.py:206`). This contradicts `SearchOut.proposal` ("None until the run is complete") and the runbook ("its result is not used"). The same race affects `summary_of` (`evidence/acquisition.py:764`). **Fix:** show both only for `COMPLETE` runs.
- **M3. Claims have no database constraints on their field or span.** `backend/src/nessa/migrations/versions/r0013_evidence_acquisition.py:199,203`: `field` is only length-checked and `span` accepts any JSON. Nothing ties a claim's `attempt_id` to its copy's attempt or workspace. **Fix:** add a CHECK for `field IN (...)`, a CHECK on the span's shape (a 64-hex `source_sha256`; offsets or a pointer), and a composite foreign key `(copy_id, attempt_id)`.
- **M4. Revoked access mid-acquisition is reported as a retrieval failure.** `backend/src/nessa/evidence/acquisition.py:655-660,688-693` then `:727`: the run is published `failed/retrieval_failed`, whose words say "try again later", and the attempt can stay `pending`. **Fix:** publish `access_revoked`.
- **M5. `http_requests` undercounts.** `backend/src/nessa/evidence/acquisition.py:682` does not count robots.txt requests, and an attempt refused by robots.txt records 0 although one request was made.
- **M6. A kept body can be dropped silently.** `backend/src/nessa/evidence/acquisition.py:581`: on a hash mismatch, the attempt says `retention: body` but no document is kept and nothing is recorded. **Fix:** fail the attempt, or record the mismatch.
- **M7. Listing totals are capped and recomputed on every page.** `backend/src/nessa/evidence/acquisition.py:460,422`: totals and city counts are silently capped at 10,000 jobs and recomputed for every page, with one attempt lookup per copy.
- **M8. A failing cancellation blocks dispatch.** `backend/src/nessa/identity/worker.py:127`: cancellations are handled ahead of dispatch inside one `try`, so a cancellation whose publication keeps failing stops every dispatch pass. **Fix:** give each its own `try`, or handle each item separately.
- **M9. Dead code.** `store.job_count` (`backend/src/nessa/evidence/store.py:706`) and `store.document_kept` (`:392`) have no callers.
- **M10. Ruling 11 is not recorded.** ADR 0009 does not record ruling 11 (cancel and favourites take no expected version). Pasted text and acquisition submission also take none, with no recorded ruling.
- **M11. A failed target is fetched again after a crash.** `backend/src/nessa/evidence/acquisition.py:645` skips only `succeeded` or `blocked` targets. A step re-executed after a crash for a target that failed for good (for example a 404) fetches it again, contradicting the workflow docstring's "completed steps are not repeated".
- **M12. One file, several responsibilities.** `backend/src/nessa/evidence/acquisition.py` (766 lines) mixes API commands, read models, pasted text and worker steps, and shares its name with the restricted worker `nessa/acquisition.py`. Polish.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** Cancellation, the repair bound, the workflows, RLS and freshness are sound and well tested. But the persisted acquisition path breaks GC6 in three ways:
- An unreadable page becomes "none found" (C1).
- Exemplars and Adzuna truncation distort the counts (I2, I3).
- Dedupe in production depends on arrival order and can count a multi-city job twice (I1), while PROP-02 and JOB-02 are marked verified on a function production does not use.
