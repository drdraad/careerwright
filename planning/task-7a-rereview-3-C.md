# Task 7A re-review 3-C: fix round 5, item 3 (2-C N1)

**Scope.**
- Item 3 of `task-7a-fix-round-5.md`.
- The "Fix round 5" section of `task-7a-report.md`, read as claims.
- `review-23d6337..df44221.diff`, mainly 22c0f30.
- The implementer's concern 4.
- The rest of the delta, checked for regressions in extraction, spend and cancel.

**How I checked.**
- Read-only at HEAD df44221. The tree is clean apart from the untracked docx.
- I ran no suites and no probes. Everything below comes from reading the code, the tests, the
  generated client and the docs at df44221.
- I did not read `.env` or NESSA_HOME, made no live calls and used no subagents.

## Verdict: item 3 is fixed

**Both figures, and the activity untouched.**
- `evidence/extraction_runs.py:67-85`: `acquisition_model_spend` keeps the 3-attempt figures
  (`per_run_nano_usd`, `worst_case_nano_usd`). It adds
  `hard_maximum_nano_usd = MAX_EXTRACTIONS_PER_ACQUISITION × run_limit_nano_usd` (`:84`).
  The ruled activity is unchanged; `identity/` is not in the delta.

**Why the hard maximum is a real bound.**
- `evidence/acquisition.py:665` reads the limit from `spend_summary`, which gives the stored
  `run_limit_nano_usd` or the default until limits are stored.
- Every reservation is refused if `run_committed + worst_case > limits.run_limit_nano_usd`
  (`identity/spend.py:59`, called at `identity/activity.py:466`). That is the same stored
  field.
- `_COMMITTED` counts reconciled attempts at their actual cost and the others at their
  reservation. So, crash or not, a run's committed spend never passes its limit, and the
  acquisition's never passes 5 × the limit.
- With no stored limits the activity refuses every attempt (`limits is None`). The
  default-based figure is then loose, but still true.

**Descriptions.**
- `api/research_schemas.py:413-445` (`ModelSpendOut`): the class says "two maxima, never an
  expected cost". `per_run_nano_usd` and `worst_case_nano_usd` say "without a worker crash".
  `hard_maximum_nano_usd` (`:432`) says "a worker crash included … past which a run never
  reserves".
- `ModelSpendEstimate` (`extraction_runs.py:49-64`) matches.

**Client.** It is regenerated: `hard_maximum_nano_usd` is in `openapi.json`, `types.gen.ts`
and `schemas.gen.ts`.

**Docs.** ADR 0009 decision 15 (the "Spend shown first" paragraph) and the MODEL-08 row state
both figures, the default at $0.75 and the fact that the activity is unchanged.

**Tests.**
- `tests/domain/test_extraction.py::test_an_acquisition_s_model_spend_states_its_ceiling_without_a_crash_and_its_hard_maximum`
  runs on both models. It checks 750,000,000 at the default limit, 100,000,000 at a $0.02
  limit, unchanged no-crash figures, and None in demo.
- `tests/integration/test_page_extraction.py::test_the_job_list_states_what_an_acquisition_may_spend_before_it_starts`
  checks a stored $0.04 limit (200,000,000) and a workspace with no stored limits
  (750,000,000).

**Note, not an issue.** Both figures follow the run limit in force when the job list is read.
A person who raises the limit afterwards can spend more, and the next read shows that.
"Ever" in the field's description is true only under the current limit. One clause in Task 8's
on-screen words would cover it.

## The implementer's concern 4: should the API give the lower of the two as the "without a crash" figure?

**Yes.** Without a crash a run still never commits past its run limit, so
min(3 × reservation, run limit) is the true no-crash bound. Showing a no-crash figure above
the hard maximum contradicts the word "hard" in front of the person.

## Rest of the delta (extraction, spend, cancel)

- **Extraction (8a485ea).** `extraction._checked` (`evidence/extraction.py:548-558`) now also
  drops a quoted apply link that `decoded_holds_detail` flags, with `PERSONAL_DETAILS`. That
  is stricter and fail-safe. Item 2's narrower `_SHOWN_EMAIL` changes what `visible_text` and
  the span check remove. Its R4-1 forms still match, per the report's tests; the rule's
  correctness is reviewer A's area. The model input path, the span check, the bounds and the
  run task are otherwise unchanged.
- **Spend.** The only change is the read above: `list_jobs` makes two more queries through
  `spend_summary`, read-only, inside the same `actor_transaction`. The reservation,
  `refused_scope` and `_not_run` are unchanged.
- **Cancel.** Nothing in `identity/runs.py`, `run_store.py`, `api/routes_runs.py` or the
  recording transaction's lock order changed.
- **Workflows.** DBOS `application_version` is unchanged, and correctly so: no step sequence
  changed.

## New issues
None (0 Critical, 0 Important, 0 Minor).
