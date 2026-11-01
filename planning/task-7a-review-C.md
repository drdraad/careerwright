# Task 7A review C: model extraction (fix round 2, part 2)

Reviewer: task reviewer C, full review of new work. Inputs: `task-7a-fix-round-2.md` part 2
(rulings 9–16), `task-7-brief.md` and `task-7-slices.md` (slice 7A), the "Fix round 2" section
of `task-7a-report.md`, and `review-dc8dd4d..1132cf0.diff` (4 commits, 4.6k lines, read in five
passes: API and acquisition; extraction and agent; runs, store, activity and migration 0021;
tests and fakes; tools, ADR, register and fixtures). Read-only. I ran no suites. I ran three
offline Python probes against the final code (`uv run --locked --offline python -c ...`, no
bytecode written), each one to settle a specific doubt the code raised (below). I did not read
`.env` or NESSA_HOME, made no live calls and dispatched no subagents. `git status` is unchanged.

### Spec Compliance
- ❌ Issues found:
  - Ruling 11 ("the sealed input is the page's redacted visible text"): the text is redacted
    *before* it is normalised, and the normalisation can produce an email address or phone
    number that the redaction would have caught. The resulting text is hashed, sealed and sent
    to Meta (`backend/src/nessa/evidence/pages.py:510-513`). See Important I1.
  - Ruling 12 ("the same rules as the JSON-LD path: pay exactness"): the span pay reader
    approves wrong amounts as `validation: model` for common UK forms
    (`backend/src/nessa/evidence/extraction.py:221-224`, `:276-281`). See Important I2.
- ⚠️ Cannot verify from diff:
  - MODEL-08 ("estimate shown before deep research"): an acquisition now automatically starts
    up to 5 model runs on the person's key. That is a worst case of 5 × 3 × $0.048 on the
    production model. The acquisition's submission response states no model-spend estimate.
    Ruling 10 mandates the automatic start; whether the spec wants an estimate here is a
    question for the controller, not a finding.
  - The register's "verified" status for ACQ-04 and the acceptance run (`make acceptance`
    passed on 1132cf0) are the implementer's claims. I did not re-run them.

**Named risks: one focused check each**

1. **GC8.** Checked the import closure of `nessa.acquisition`, which reaches
   `nessa.evidence.acquire`. The new imports there are only `pages.visible_text`,
   `pages.EXTRACTION_TEXT_BYTES` and `records.MODEL_READABLE`. `pages`, `records` and
   `redaction` import no store, keyring, Meta, profile or extraction module. The boundary test
   (`tests/architecture/test_boundaries.py:323-347`) still limits vendors to httpcore2,
   certifi and scrapling and settings to three fields. No Compose or network file is in the
   diff. `PAGE_EXTRACTION_TASK` is registered only in `nessa/worker.py:TASKS`. **Holds.**
2. **One call path.** Checked `extraction_agent.py` and `identity/activity.py`. The kind is one
   `RunTask` on the generic activity. `_prepare` (activity.py:395-470) re-checks access,
   `model_refusal`, the sealed input, the key and `refused_scope` for it like any other kind.
   It reserves the task's worst case and opens the input and key just in time. Failures go
   through `classify_failure`. The agent uses `NativeOutput`, no tools,
   `retries={"tools": 0, "output": 1}`, `RepairBound` and `TruncationGuard`. The tests confirm
   `function_tools == output_tools == []`. The API cannot submit the kind
   (`identity/runs.py` accepts `Literal[RunKind.CONNECTION_CHECK]` only). No second provider
   path: `live_smoke.qualify_extraction` calls the same `run_extraction`. **Holds.**
3. **Eligibility and cap.** Checked `start_extraction`/`_not_run` and
   `nessa.submit_page_extraction`. The Python gate is `SUCCEEDED` plus `MODEL_READABLE`. The
   SQL gate is `route = 'fetch'`, `status = 'succeeded'`, an extraction value in
   (`no_structured_data`, `no_job_posting`) and an attempt of the current authorised
   acquisition run. Pasted, Adzuna, refused, failed and parsed sources are excluded. The cap is
   5 in both places, serialised by the acquisition run's row lock. Not-run reasons are typed,
   with a CHECK. Demo is refused in code and by a CHECK. Contributor-only-synthetic is enforced
   in code, by `model_refusal` and by r0002's `model_mode <> 'contributor' OR synthetic`.
   **Holds.** A pre-check imprecision is listed as M3.
4. **Spans and approval.** Checked `check_extraction`. Each quote is unwrapped and bounded,
   `span_offsets` finds it in the hashed text, the value is the page's own characters, and a
   span holding a personal detail is dropped. Pay, dates, `apply_link`, the claim bounds
   (`Claim` cuts text to 200) and `mark_conflicts` all apply. Drops carry a `DropReason`.
   Approved claims are `model`, with the `model_claims_cite_their_span` CHECK. The run output
   is the checked proposal. The events carry IDs and a position only. **The structure holds.**
   The pay reader is wrong for some inputs (I2).
5. **Retention.** Checked `publish` → `nessa.erase_run_input()` on every terminal path. That
   covers normal publication, worker cancellation (`identity/worker.py:85`), reconciliation
   (`activity.py:694`) and access revoked. The integration tests prove erasure on complete,
   `provider_unavailable` and after revocation, in an excerpts-class workspace, with a body
   sentinel absent from both databases. Redaction runs before hashing and sealing, but not
   after the final normalisation (I1).
6. **Honesty.** Checked `_empty_reason`, the `coverage` SQL and `extraction_state`.
   `no_posting_found_by_model` never yields `none_found_in_sources_checked`, even beside an
   API's empty answer. Failed, cancelled and unverified runs stay `no_posting_readable`, and
   in-flight runs show `pending`. The words in `vocabulary.ts:323-327` say what happened.
   **Holds.** A small state mismatch is listed as M5.
7. **Prompt injection.** Checked the tests. Each named case is covered: an unquoted value, a
   quote not in the text, a `javascript:` link and a non-https link
   (`test_output_that_follows_the_page_s_instructions_is_dropped`); an extra field, refused
   after one repair; the key and the profile; and changes outside the run (no other run,
   profile version unchanged, `/collect` never requested, one attempt, no copy). **Holds.**
8. **Live cap and cost.** Checked `qualify_extraction` and the ledger row. It uses
   `authorise(..., production=False, budget=ScopeBudget("live-extract", 3, 0, 300_000_000))`
   under `ledger.exclusive()` and reads the labelled synthetic fixture only. It writes one row
   per request, unknown when unmeasured, with the reservation counted. The leak scan covers
   the requests, the result and the rows. Row 31: 700 × 100 + 460 × 200 = 162,000 nano-USD =
   $0.000162, which matches. The Makefile target is separate from `check` and `acceptance`.
   **Holds.**
9. **Workflows.** Checked the stat: neither `identity/workflow.py` nor `evidence/workflow.py`
   changed. `RunTask.record` runs inside the activity's settle transaction and the erasure
   runs inside the publish step, so no step was added. `APPLICATION_VERSION` is still
   `"nessa-l0-1"` (`identity/worker.py:30`). The report states the choice (ordinary runs).
   **Holds.**
10. **Migrations.** Checked r0021. It is a new file and forward-only (`downgrade` raises).
    CHECKs cover `not_run`, `outcome`, `text_sha256`, the run-or-reason pairing, the run kind
    and the validation states. RLS is on for `page_extractions`: API SELECT only; worker
    SELECT by authorised workspace; worker INSERT only `not_run` rows for its own run's
    attempts; `UPDATE (outcome)` only where `run_id = current_run_id()`. There is no DELETE.
    Both SECURITY DEFINER functions pin `search_path`, revoke PUBLIC and are granted to
    `nessa_worker` only. **Holds.**

### Strengths
- One call path: extraction is a `RunTask` with two small, well-documented extension points
  (`record`, `erases_input`) rather than a new mechanism. The worker cannot insert runs except
  through one SECURITY DEFINER function, which checks run kind, ownership, attempt
  eligibility and the cap.
- Erasure is keyed by `current_run_id()` alone, so it holds after revocation, and the test
  proves exactly that (`test_the_worker_starts_an_extraction_only_for_its_own_run_s_unread_page_and_erases_it`).
- Values are always the page's own characters at verified offsets, never the model's string.
  The span hash is tied end to end to `page_extractions.text_sha256`.
- Honest coverage: the `coverage` SQL distinguishes pending, read with none found, unread and
  succeeded, and the "never none found" rule is tested in the domain and end to end.
- Good live discipline: a separate scope, the synthetic page only, per-request rows, unknown
  usage kept as unknown, and a leak scan of everything sent.
- The DB label and cap drift tests against migration 0021 keep code and schema in step.

### Issues

#### Critical
None.

#### Important

**I1. The extraction text can contain third parties' emails and phone numbers. It is hashed,
sealed and sent to Meta.** `backend/src/nessa/evidence/pages.py:510-513`
(`visible_text`).
- What: `redact_text` runs on `_plain(text)`. After that the code collapses whitespace
  (`split()` treats NBSP, newlines and tabs as spaces) and drops characters that do not print
  (zero-width space, soft hyphen). Either step can turn an unredacted form into a plain one.
  The text is not redacted again after these steps. Verified on the final code with
  `visible_text(redact_page(html).text)`:
  - `0161&nbsp;496&nbsp;0000` gives `0161 496 0000`.
  - A phone number split by newlines gives `0161 496 0000`.
  - `ada&#8203;@northwind.example` gives `ada@northwind.example`.
  - `ada@north&shy;wind.example` gives `ada@northwind.example`.

  In all four cases `redact_text` on the output *would* remove the detail. NBSP between the
  digit groups of a phone number is a very common form on real pages.
- Why it matters: ruling 11 says the sealed input is the page's *redacted* visible text. The
  session 1 policy says a third party's details are never kept. The ADR and register say
  "personal details removed again". The detail goes to an external provider and into the
  sealed input until the run settles. The span check stops it becoming a claim
  (`extraction.py:391`), but not the exposure. The existing test
  (`test_the_text_read_is_the_page_s_visible_text_without_scripts_or_personal_details`) uses
  an entity-encoded email and plain spaces, so it misses these forms.
- Fix: normalise first (decode, collapse whitespace, drop non-printing characters), then run
  `redact_text`, then cut to bytes. Add the four forms above to the domain test. Separately, a
  note for the part 1 reviewers: the same NBSP and newline forms also pass `redact_page` for
  kept bodies. That is pre-existing and outside this diff.

**I2. The span pay reader approves wrong amounts as `model` claims.**
`backend/src/nessa/evidence/extraction.py:221-224` (`_NUMBER`, `_THOUSANDS`, `_MONEY`) and
`:276-281` (`salary_from`).
- What, verified on the final code:
  - `"£30-35k per annum"` gives a minimum of 3,000 and a maximum of 3,500,000 minor units per
    year, that is £30 to £35,000. `"£25-30K a year"` and `"£30 - £35k"` read the same way.
    "£30-35k" is a common UK way of writing £30,000–£35,000.
  - `"£1.2m"` gives 120 minor units (£1.20), because nothing stops a letter directly after
    the number.
  - `"£40,000 max"` and `"£40,000 maximum per year"` give minimum = maximum = £40,000,
    because "up to" words are only searched for *before* the amount.

  All of these return `issue=None`, so the claim is approved, not quarantined.
- Why it matters: ruling 12 requires pay exactness by the JSON-LD path's rules. A JSON-LD
  value can never be misread this way, because its numbers are fields. Pay feeds
  affordability (GC1, GC4), and a wrong value marked approved is worse than an unknown one
  ("unknown is never zero"; quarantine exists for this). The existing parametrised tests
  cover only symmetric `k` (`£30k–£35k`) and leading "Up to".
- Fix: refuse (`salary_invalid`) a range where only one side carries `k`, or apply the
  multiplier to both sides only under an explicit, tested rule. Require a non-letter after
  each number unless it is `k`. Treat a trailing `max`/`maximum`/`up to` the same as a
  leading one, or refuse it. Add these cases to
  `test_pay_that_cannot_be_read_exactly_stays_unknown_with_its_issue` or the exact-reading
  test.

#### Minor

**M1. The work-mode reader ignores negation.** `extraction.py:349-366`. `work_mode_from("Not
remote")` returns `remote`, and `"This role is not hybrid"` returns `hybrid` (verified).
Either is approved as a `model` claim. The word lists are provisional (R6), but approving the
opposite of the span is worse than leaving it unclear. Fix: quarantine (`work_mode_unclear`)
when a negator (`not`, `no`, `non-`) comes before the matched word.

**M2. A cancelled extraction run can still publish jobs.** `identity/activity.py:592-594`.
If the model call is already in flight when the run is cancelled, `_settle` still accepts the
output (the established DUR-05 rule: "its result is kept"). It then calls `RunTask.record`,
which writes job copies with job IDs. The result: the listing counts a vacancy from that page
while `coverage` says `no_posting_readable` (`store.py:444`, `r.status <> 'complete'`) and the
attempt's `model_extraction.state` says `not_read`. This differs from the already-ruled
acquisition-cancel cascade, which covers only runs not yet settled. Fix: in
`record_extraction`, skip recording when the run is cancelled or has a cancellation request
(lock the run row and re-read it), or let `coverage` and `extraction_state` agree with
whatever was recorded.

**M3. The budget pre-check can count a run twice.** `extraction_runs.py:63-70`.
`committed + started * worst_case` assumes this acquisition's earlier extraction runs have not
reserved yet. But they are dispatched at once, and by the time a later target is recorded they
may already have reserved or settled. Under a tight period limit this refuses with
`budget_exceeded` when the budget would allow the run. That is conservative but mislabelled.
Fix: count only this acquisition's started runs that have no attempt yet, or accept and
document the over-count.

**M4. The input bound is in characters, but the reservation assumes bytes.**
`extraction.py:84`. `ExtractionInput.text` has `max_length=EXTRACTION_TEXT_BYTES`, which
pydantic counts in characters. The reservation (`MAX_PROMPT_BYTES`, "bytes bound tokens")
holds only because `visible_text` cuts to bytes, and
`test_an_attempt_reserves_both_requests_at_their_bounds` uses ASCII only. Fix: add a UTF-8
byte-length validator to `ExtractionInput.text`.

**M5. `postings_read` can show for a page with no published posting.**
`evidence/acquisition.py:440-450`. When every model-read posting conflicts
(`conflicting_job_postings`, no job), the outcome is still `postings_recorded`, so the state
is `postings_read`, while `coverage` counts the page `no_posting_readable`. Fix: give it a
distinct state or outcome (for example `postings_conflicting`), or map it to `not_read`.

**M6. The code cites the wrong ADR decision.** Five files refer to "ADR 0009 decision 13"
for extraction, which is decision 15 (13 is the repair bound):
- `extraction.py:3`
- `extraction_agent.py:1`
- `extraction_runs.py:2`
- `r0021_page_extraction.py:2`
- `tests/integration/test_page_extraction.py:2`

**M7. Test gaps.**
- The SQL cap in `submit_page_extraction` is checked only by a regex drift test. Its refusal
  (`check_violation` at 5) and the refusal of another run's attempt are not exercised.
- The `budget_exceeded` and `model_not_permitted` reasons have no test, so M3's arithmetic is
  untested.
- `tests/domain/test_extraction.py` imports the private `_empty_reason`. The integration
  tests already cover the public listing.
- Fix: add the SQL refusal cases to the `test_page_extraction.py` guard test, and add one
  budget case.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The architecture meets every named risk: one call path, GC8 intact, a tightly
guarded SQL entry point, erasure on every terminal path, honest coverage, a capped live
qualification and an unchanged workflow version. Two deterministic checks the rulings rely
on are wrong for realistic input. The redaction misses details that the text's own
normalisation reveals (I1), and the pay reader approves misread amounts (I2). Both are small,
local fixes with a regression test each.
