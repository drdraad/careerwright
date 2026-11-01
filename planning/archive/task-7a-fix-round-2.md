# Task 7A — fix round 2 (FIX_BASE b24d264)

Two parts, in this order, each its own commits. Part 1 closes the round 1 re-reviews. Part 2
builds the remaining 7A deliverable, model extraction. Read `task-7a-rereview-1-B.md` (N1–N7,
B-M2) and `task-7a-rereview-2-A.md` (M-3/N-2, N-1, N-3, N-4) in full first.

## Part 1 — re-review residuals (all fixed now)

1. **B N1. Ruling:** a fetched page whose structured data held no posting
   (`no_job_posting`) counts as `no_posting_readable`, like any page whose HTML was not read.
   Only an API's own empty answer (Adzuna `count` 0) may support
   `none_found_in_sources_checked`. Part 2 adds the model-read case (item 9). Update ACQ-03 and
   STATE-02, and test it.
2. **B N2.** Take `pg_advisory_xact_lock` on the workspace for the recording transaction
   (`_record_copies` through the merge). Integration case: two overlapping acquisitions in one
   workspace lose no copy or claim and strand no `pending` attempt.
3. **B-M2:** add a dedicated test that a search proposal and an acquisition summary are shown
   only for `COMPLETE` runs (a cancelled or failed run shows neither).
4. **B N3–N7:**
   - N3: remove `store.copy_counts`.
   - N4: check the captured usage in the failure path too, so an overrun reply that is also
     invalid or truncated still carries `bound_exceeded`.
   - N5: move the unlocated-contact reason into a typed column (an enum with a CHECK, for
     example `body_not_kept`). `rights_status` keeps only the rights statement.
   - N6: add restrictive policies, so the worker can never delete an exemplar job or move a
     pasted copy.
   - N7: add `empty_reason` `sources_pending`, with words in `vocabulary.ts`, for a listing
     whose sources are still being fetched.
5. **A N-1. Ruling:** fix the code; do not just narrow the docs.
   - Build claims from `redact_value`'d data.
   - Decode-redact every script whose content parses as JSON.
   - Treat a JSON-LD block that is not valid JSON, and whose text redaction changes it, like an
     unlocated one: the body is not kept.
   - Detect duplicate keys (`object_pairs_hook`) and always re-serialise.
   - Test the probe's four cases (`redaction_probe_3.py` cases 10–13 in the scratchpad named in
     the re-review).
   - Then make ACQ-06 and ADR 0009 decision 4 say exactly what holds.
6. **A N-2:** refuse any non-ASCII host character whose NFKC form contains an ASCII digit or
   "."; test U+2024 and U+FE52.
7. **A N-3:** give `SearchExcluded` a validator that keeps `url` only when it is a checked
   http(s) URL, and otherwise moves the host to `refused_host`. Test a proposal sealed with a
   raw `javascript:` value.
8. **A N-4:** replace the vacuous assertion with the reviewer's
   `pacer.wait("jobs.other.example", 5.0, within_s=5.0)` check (returns True,
   `slept == [5.0]`).

## Part 2 — model extraction (ACQ-03's residual, ACQ-04's model part)

Spec: "Use model extraction only for remaining ambiguity … deterministic code approves
records"; "keyless fetchers return permitted text to the user-scoped extraction workflow";
"field-level provenance, semantic validation and visible extraction failure". The brief adds:
"No extraction is tuned on a real page before Task 7b assigns its template family and split
(OI-09)". Controller rulings:

9. **What it reads:** only a retrieved, permitted page whose structured data gave no posting
   (`no_structured_data` or `no_job_posting`). Never a refused, failed, pasted or already
   parsed source.
   - A model run that finds no posting gets its own label (for example
     `no_posting_found_by_model`), with words saying the page was read and no job advert was
     found. That is not evidence there are no vacancies, and it never supports
     `none_found_in_sources_checked`.
10. **Where it runs:** a new model-backed run kind on the one bounded activity (ADR 0002/0006:
    one `RunTask`, never a second call path), in the DBOS worker with the workspace's own
    model key. The acquisition worker still holds no model key (GC8).
    - It is started automatically by the acquisition for each eligible page, at most
      `MAX_EXTRACTIONS_PER_ACQUISITION = 5` (a named constant).
    - Each run has its own reservation, and the repair bound applies.
    - A run not started (the cap, the budget, no key, a demo workspace, the test model with
      non-synthetic data) leaves the source `no_posting_readable` with a typed
      `extraction_not_run` reason, never "none found".
    - Demo workspaces never call a provider.
11. **Input and retention:**
    - The sealed input is the page's redacted visible text, cut to a named bound and marked as
      untrusted data in the prompt.
    - For classes whose body may not be kept, that sealed input is erased once the run
      settles. The hash, the verified spans and the excerpts of at most 200 characters remain.
      Test the erasure.
    - Kept classes follow their existing retention.
12. **Output and approval:**
    - The model proposes posting fields, each with a verbatim quote.
    - Deterministic code checks each quote is a span of the hashed text (reuse the 6b
      `quoted_span` approach where it fits). It then validates each field with the same rules
      as the JSON-LD path: pay exactness and currency, dates, an https apply link via
      `apply_link`, redaction, and the claim bounds.
    - A field without a verified span is dropped with a reason. A critical-field disagreement
      is quarantined.
    - Approved fields become claims with `method: model` (or the existing equivalent), so
      provenance shows the model read it.
    - No model output goes into a receipt.
13. **Prompt injection (ACQ-04's model part):** the extraction agent has no tools, only the
    output schema. Tests with a fake provider:
    - output following page instructions (an unquoted value, a quote not in the text, a
      `javascript:` link, an extra field, a field claiming the person's profile or key) is
      refused or dropped;
    - page text that instructs the model changes nothing outside this run (no other run, no
      profile write, no tool, no URL fetched).

    Do not compose self-harm or distress text for any case.
14. **Live qualification:**
    - One new capped scope, `live-extract`: test model only, a synthetic, labelled page held
      in a fixture (never a real page, per OI-09), at most 3 requests, $0.30.
    - Each request is ledgered with its tokens and cost, with a leak scan.
    - No production model, no Adzuna.
15. **Workflows:** if any committed workflow's step sequence changes, change DBOS
    `application_version` and record why. Prefer extraction runs submitted as ordinary runs, so
    no existing sequence changes, and say which you chose.
16. Update ADR 0009 (a decision for extraction), the register (ACQ-03, ACQ-04, STATE-02 and
    any row the run kind touches), the runbook (`make live-extract` or the chosen command) and
    the proposed CLAUDE.md wording in your report. Do not edit CLAUDE.md.

## Also

- `make check`, then `make acceptance` once at the end, and name each covering test.
- Use the Edit and Write tools only for file changes (no sed, heredocs, one-liners, `touch` or
  `rm` of tracked files). Never read `.env` or NESSA_HOME. Never commit
  `~$ssa_Local_Development_Plan.docx`. Never touch the agentsolve-* or eigenprompt-* Docker
  projects. No subagents.
- Append the fix report to `task-7a-report.md` under "Fix round 2", then reply with the short
  contract.
