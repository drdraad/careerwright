# Task 6b report: span-cited "Why this could suit you" (S2.7, D3)

Branch `l0-local-release`, from `f360a86`. Implementer: Task 6b agent. Not pushed.

## Commits

| SHA | Subject |
|---|---|
| `300eb4a` | Write a span-cited "Why this could suit you" for each slate (S2.7) |
| `ec73823` | Evaluate the written explanation offline and as a capped live case |
| `19b4dad` | Show the slate's written note beside how each suggestion was found |
| `a8584a1` | Ledger the live slate-explanation case (rows 25-26, scope live-eval-6b) |
| `9929707` | Refuse a claim or a quotation given twice; keep the note's state helper private |
| `a751c7b` | Record Task 6b: ADR 0007 decisions 6 and 12, register, runbook, review addendum (also a one-line comment fix in `Directions.tsx`) |

Note: `19b4dad` also carries two test-tag corrections in
`backend/tests/integration/test_slate_explanations.py` (removed `MODEL-02` and `TEST1-11`,
which those tests do not prove).

## What was implemented

**Backend (one run kind on the one bounded activity, ADR 0002/0006 decision 10).**

- `backend/src/nessa/profile/slate_explanation.py` (new): the contract. Input
  (`ExplanationInput`: the discovery's pinned answers that describe work, whole, and ESCO's
  record of each suggestion of the slate's first view, fitted to an 8,500-byte prompt by
  stepping the description cut and skill count down), the model's strict output schema
  (`ExplanationOutput`: per occupation ref, 1-2 claims, each with 1-3 quotes tagged
  `answer` or `esco`), the deterministic check `check_explanation` and the stored
  `SlateExplanation` (each quotation in its source's own characters, with the answer's
  field or the record's part). Refused: a quotation that is not an exact whole-word span
  of its source (case, spacing, apostrophe/dash forms aside), an invented answer, a fact
  the occupation's record lacks (another suggestion's record included), a claim without at
  least one answer and one ESCO quotation, quotation marks inside a claim, readiness,
  affordability or hiring words or a currency sign that neither the record nor the answers
  use, and a health condition / type / protected characteristic / percentage neither the
  answers nor that record name (ADR 0007 decision 7's `inferred_sensitive_terms`). Worst
  case per attempt: 2 requests, $0.0034 test model, $0.0495 production.
- `slate_explanation_agent.py` (new adapter): `SLATE_EXPLANATION_TASK` (one repair via the
  output validator, then `invalid_model_output`; `TruncationGuard`), and the fixture model.
- `fixture_explainer.py` (new): deterministic demo explainer, reads the live prompt,
  labelled "Demo explainer (synthetic)".
- `explanation_store.py` (new SQL adapter, added to `ADAPTERS` in the architecture test).
- `exploration.py`: `submit_explanation` (returns the existing explanation, whatever its
  state, if one exists; otherwise checks expected version, validated searches, that the
  discovery's pinned answers are the current ones, a non-empty first view; seals the
  input; submits the run; links it), `DiscoveryView.explanation`.
- Migration `r0011_slate_explanations.py`: run kind `slate_explanation`; fixture models may
  answer it; it pins the profile version; table `nessa.slate_explanations` (unique
  `discovery_id`, FKs to both runs with cascade, RLS, `SELECT, INSERT` for `nessa_api`).
- `identity/records.py` (`RunKind.SLATE_EXPLANATION`), `model_registry.py`
  (`nessa-fixture-explainer-1`), `model_choice.py` (fixture mapping), `worker.py` (task and
  fixture model).
- API: `POST /v1/workspaces/{ws}/discoveries/{id}/explanation` (`expected_profile_version`,
  Idempotency-Key, `run_idempotent`) answers 202/200 with `ExplanationRunOut` (the run
  only); `DiscoveryOut.explanation: SlateExplanationOut | None` carries the written text;
  export `format_version` 4.
- `tests/support/fake_models.py`: the fake provider answers the explanation schema.

**Evaluation and live tooling.** `tools/evaluation.py` (`CaseKind.EXPLANATION`, checks
`written_for_each`, `both_sources`, `quotations_are_spans` against ESCO records read from
the taxonomy, `provenance_kept`, `no_percentage`; offline subject
`observe_explanation_offline`), case EXP-01 in `evaluation_cases.json` (not in the default
live run), `tools/live_eval.py` (`EVAL_EXPLANATION`: discovery, then spend limits reset to
allow exactly one explanation attempt, then the explanation; per-case worst case now
multiplies by attempts).

**Web.** Regenerated client (`apps/web/src/generated`, skip in review).
`Directions.tsx`: `writtenState`, `WrittenNote` (claim, then each quotation after "You
said" or `RECORD_PART` words, and who wrote it) above "How Nessa found it" (the
deterministic lines, always shown); pending (running status), unavailable (failure-class
title, or the refused request's `ERROR_STATEMENT` title), not-covered; a polite
`role="status"` line; one automatic request per slate (when it first shows for the current
answers with a key or in a demo; a ref guards remounts/view changes). `queries.ts`
(`useSubmitExplanation`), `vocabulary.ts` (`RECORD_PART`), `globals.css` (three rules,
existing tokens only), stories `SlateOfSix` (written), `SlateThin`, `SlateNotePending`,
`SlateNoteUnavailable`, e2e visual shots and the demo journey assertion.

**Docs.** ADR 0007 (decision 6's title and last sentence amended to point at ADR 0008 and
decision 12; the `replaces` sentence kept; new decision 12; status, requirements,
consequences, H-12 checklist), register (REC1-11, SEC-05, MODEL-03, MODEL-08, BND1-11,
TEST1-10, H-12), runbook (endpoint, EXP-01), `docs/reviews/sprint-2.md` addendum, live
evidence (`docs/evidence/live-eval.md`, `live-usage.jsonl`, `live-usage.md`).

## Rulings made (and why)

1. **What a slate is.** A slate is a discovery's first view (balanced, no exclusions),
   computed when the note is asked for. A changed view (emphasis, exclusions) is never a
   new slate and never makes a call; its suggestions that the note covers keep it, others
   say they have none. A new discovery is a new slate. Reason: the slate is recomputed per
   read, so "per slate" needs a stable identity; the first view is deterministic and makes
   "a view change never multiplies calls" structural. Recorded in ADR 0007 decision 12.
2. **At most one run per discovery, no retry** (a unique key). Asking again returns the
   same run whatever its state, so a failed note is shown as unavailable and not retried
   for that slate ("Suggest again" makes a new slate). Reason: the spec's "at most one
   bounded model call per slate", read strictly. Provisional (H-12).
3. **The note quotes only the current answers.** Refused (`STALE_INPUT_VERSION`) when the
   discovery's pinned version is not the current profile version, so a note never quotes
   an answer since changed or removed.
4. **Every claim quotes both sides** (at least one answer and one ESCO quotation): "a claim
   that rests on no quotation" read as a claim that does not link what the person said to
   a fact ESCO holds.
5. **Quotation matching**: exact span at word boundaries, case/spacing/apostrophe/dash
   forms aside, and the stored text is the source's own characters (never the model's).
6. **The words the record or the answers use are allowed** in the readiness/money/hiring
   and sensitive-term screens: they describe the work ("payroll clerks check that staff
   are paid"; a midwife record names women and pregnancy). Provisional (H-12).
7. **Asked for without a click**, once, when the slate first shows with a key stored (or
   in a demo); spend is the person's key, reserved and reconciled like any run.
   Provisional (H-12, H-01).
8. **The submission answers with the run only.** Found by the leak scan during
   implementation: the 200 answer first carried the written text, and `run_idempotent`
   keeps a command's answer as a plaintext receipt, so model output escaped its seal. The
   written text is read with the discovery instead.
9. **Export format 4**: `DiscoveryOut` gains `explanation`, so the export carries the note
   (as every model run's validated output is exported), beside the provenance, which is
   what exports cite (sources and searches unchanged).
10. **DBOS `application_version` unchanged** (`nessa-l0-1`): a new run kind uses the same
    workflow and the same two steps; the step sequence did not change.

## Tests and checks run

TDD: `tests/domain/test_slate_explanation.py` was written first and failed at collection
(`ModuleNotFoundError: nessa.profile.fixture_explainer`; the contract module had been
written alongside it, so its RED was the import, not each assertion); after the modules,
1 failure (a whitespace-sensitive assertion in the test, fixed in the test) then 32
passed. `tests/domain/test_slate_explanation_agent.py` RED
(`ModuleNotFoundError: nessa.profile.slate_explanation_agent`), then 8 passed. The
integration tests first failed on a real defect (model output in a command receipt, found
by `leaks()`), fixed in the API, then 6 passed.

Commands on the final code (results below are from these runs):

- `uv run --locked pytest tests/domain/test_slate_explanation.py tests/domain/test_slate_explanation_agent.py -q`: 40 passed.
- `uv run --locked pytest -m integration tests/integration/test_slate_explanations.py -q`: 6 passed.
- `uv run --locked pytest -m integration tests/integration/test_discovery.py tests/integration/test_export.py tests/integration/test_migrations.py tests/integration/test_isolation.py tests/integration/test_interview_turns.py -q`: 57 passed, 1 failed (an expected constraint name renamed by 0011; updated), then that test 2 passed.
- `uv run --locked pytest -m integration tests/integration/test_live_eval_ledger.py tests/integration/test_evaluation.py -q`: 3 passed.
- `pnpm run generate` (client regenerated and committed); `pnpm run check`: client matches, Biome clean, `tsc` clean, Vitest 24 files / 199 tests passed.
- `pnpm run review-screenshots`: 3 passed (1440×900, 768×1024, 390×844; 29 shots each, axe/overflow/console/font/overprint checks clean). Unrelated captures that changed only by correlation references and timestamps (not-found, not-invited, reply-to-review, support-note) were restored to keep the diff reviewable.
- Duplicate rule (added in `9929707`): `test_a_claim_or_a_quotation_given_twice_is_refused` RED (1 failed), then the domain suites 41 passed.
- `make check` on `9929707`: exit 0 (ruff format 183 files unchanged, ruff clean, mypy clean, pytest 567 passed / 193 deselected, fixture validator passed; web: client matches, Biome clean, `tsc` clean, Vitest 24 files / 199 tests).
- `make acceptance` on `9929707` (plus the comment-only edit, which the e2e image build included): exit 0. Backend `pytest -m "integration or stack"`: 193 passed, 567 deselected (5 min 18 s). Storybook build passed. Playwright: 22 passed (the demo conversation journey with the fixture explainer's note and no outside request; every story renders and passes axe; the visual package at three sizes). An earlier acceptance run was stopped part-way by me before the last code change, so it is not counted.
- The committed captures came from `pnpm run review-screenshots` on `19b4dad`; the later changes (duplicate rule, private helper, comment) do not change the UI, and acceptance re-ran the same visual checks on the final code.

## Live calls (R5)

`NESSA_LIVE_EVAL_SCOPE=live-eval-6b make live-eval CASES=EXP-01` (test model
`muse-spark-1.3-contributor`, synthetic case only; the tool's per-scope caps: 9 requests,
$0.05, tighter than the controller's $0.30; worst case $0.0068):

| Ledger row | Run | Requests | Tokens in (cached) / out (reasoning) | Cost |
|---|---|---|---|---|
| 25 | discovery | 1 | 530 (0) / 761 (524) | $0.000205 |
| 26 | slate explanation | 2 (one repair) | 2,747 (881) / 1,323 (359) | $0.000453 |

Total for the task: 3 requests, $0.000658 (scope: 3 of 9 requests). Running total across
the build: $0.023756 (ledger). Result: EXP-01 passed every check; leak scan clean
(286,988 rows/logs/responses). No production-model call. The repair's reason is not
recorded (by design). By hand: claims are sensible; some prose says more than its
quotations (see concerns). The live run predates the duplicate rule of `9929707`; its
stored output has no repeated claim or quotation, so it also satisfies the final check.

## Not run / blocked

- Human gates (R2): H-12 (the note's word lists, bounds, first-view slate, no retry,
  automatic request) and H-01 (the note's wording and placement): not run — requires
  human. Items added to ADR 0007's H-12 checklist and the review addendum.
- The production model was not exercised for this kind (no production calls in this task).
- A Standard-mode (non-synthetic) explanation run is not tested end to end; model choice is
  the shared `ModelChoice` path already verified for other kinds (MODEL-02 not claimed).
- VoiceOver/Safari: not run — requires human.

## Concerns

- Only quotations are verified; a claim's prose can still say more than its quotations
  support (seen live: "Practical outdoor work..." quoting only "practical"). Word screens
  catch readiness, money, hiring and sensitive terms only. Documented as a known limit in
  ADR 0007 decision 12.
- The live repair rate is unknown beyond one sample (the first live attempt needed its
  repair).
- A failed note is never retried for the same slate (ruling 2); a transient provider
  outage therefore leaves that slate without a note until "Suggest again".

## Proposed CLAUDE.md wording (not edited)

In "Non-obvious invariants", after the first bullet's last sentence ("...a suggestion
becomes a target only by the person's choice (ADR 0007)."), add:

> A slate's written "Why this could suit you" is one bounded `slate_explanation` run per
> discovery, over its first view; every quotation is verified as a span of the pinned
> answers or of that occupation's ESCO record, and the note changes no suggestion (ADR
> 0007 decision 12).

and to the "Every consequential write..." bullet, add:

> A command's answer is kept as its receipt in plaintext: never put model output in it.

## Generated or vendored paths a reviewer can skip

`apps/web/src/generated/**` (regenerated client and `openapi.json`),
`docs/reviews/sprint-2/screenshots/*.png` and `checks-*.json` (captures),
`docs/evidence/live-usage.jsonl` (ledger rows appended by the tool).

---

# Fix round 1 (FIX_BASE `a751c7b`)

Commits: `320aa34` (all code, tests, client and docs for I1–I3, M1–M4), `42ef206`
(captures; the Suggest-again notice no longer repeats the failure's "try again" advice;
the visual spec passes its scroll target into the page), and `d16ffe3` (the review
addendum's record of this round). No live calls this round. The stored live EXP-01
output (rows 25-26) was rechecked against the final rules from the private evidence
file (content words, record-only screened words, claim length and marks, duplicates):
no problems.

## Changes, finding by finding

- **I1** (`backend/src/nessa/profile/slate_explanation.py`, `_checked_claim`): the
  readiness/affordability/hiring screen's allowance is now the occupation's ESCO record
  only (title, description, skills); a pinned answer never unlocks a screened word. The
  sensitive-term guard keeps its decision 7 allowance (the person's own words and the
  record), which the ruling did not change.
- **I2**: one content-word rule in the contract (`content_words`, `quotable`,
  `COMMON_WORDS`: whole words of four or more letters, not a listed function word,
  including "work"); `fixture_explainer.py` now imports it instead of its own copy. Every
  quotation must hold a content word (problem: "has no content word"). The start of a
  quotation is trimmed of spaces and double quotation marks only, never an apostrophe
  (`_LEAD_TRIM`); the end keeps the old trim (`_TAIL_TRIM`). Wording: the note now says
  "Only the quoted words were checked against them; the sentences are Nessa's own" (the
  demo: "...the explainer's own"), and the API's `ClaimOut.text` description says the
  claim is not checked against any source, only its quotations are. "Each quotation was
  checked word for word" is gone. The ADR 0007 decision 12 known limit is reworded to
  match. Added (my ruling, see below): a submission whose pinned answers hold no content
  word is refused before any run (`INSUFFICIENT_EVIDENCE`, `no_quotable_answer`).
- **I3**: `reached_no_model(run, attempts)` in `exploration.py`: a failed or
  provider-unavailable run every one of whose attempts has `spend_state` `none` and no
  requests sent (an unfinished attempt or an unknown charge counts as a call).
  `SubmitExplanation.retry_failed` (default false; only the person's click sends it):
  on a failed run that reached no model, a new run is submitted and the failed link is
  marked replaced in the same workspace-locked transaction
  (`explanation_store.replace`); on one that sent a request it is refused with the new
  error code `SLATE_ALREADY_EXPLAINED` (409). Without the flag, a repeat answers 200 with
  the same run, as before. Migration `r0012_explanation_retry.py`: `replaced_at`, a
  partial unique index (one current link per discovery) instead of the unique key, and
  `GRANT UPDATE (replaced_at)` only. `ExplanationRunOut.can_retry` (so `DiscoveryOut`'s
  explanation carries it too). Web (`Directions.tsx`): one notice above the cards,
  `No written note: <words>`, with the failure class's or the refused request's
  error-code words from `vocabulary.ts` and one action: Try again (a run that reached no
  model, sends `retry_failed: true`; a refused request, sent again plainly), or Suggest
  again (the slate had its call; `NOTE_RECOVERY.suggestAgain` says it makes a new set of
  suggestions and that the ones shown would be replaced). `vocabulary.ts`: words for
  `SLATE_ALREADY_EXPLAINED` and `NOTE_RECOVERY`. Stories `SlateNoteUnavailable` (Suggest
  again) and new `SlateNoteRetry`; captures `you--slate-note-unavailable` and new
  `you--slate-note-retry` at three sizes (and `you--slate` for the new wording). ADR 0007
  decision 12 (new "One call per slate, and a failed note" bullet, When, UI, limits,
  provisional list, consequences, H-12 checklist), the Sprint 2 addendum, the register
  (REC1-11, H-12) and the runbook describe exactly this.
- **M1**: added `lucrative`, `demand for`, `candidate(s)`, `crying out for`, `job market`,
  and patterns `in ... demand` (up to two words between), `already have the|all the|enough
  skills|experience|qualifications|training`, `plenty of jobs|vacancies|openings|roles|work`
  (replacing `in demand` and `already have the skills`).
- **M2**: claims past `MAX_CLAIMS` and quotations past `MAX_QUOTES` are counted, not
  checked; a model's text is echoed at most 60 characters; `repair_message` caps the
  repair at 800 bytes (`REPAIR_MESSAGE_BYTES`), ending "and N more problems", which with
  the agent's fence (measured about 120 bytes) fits `REPAIR_ALLOWANCE_TOKENS` (1,000).
  The agent sends `repair_message(problems)`.
- **M3**: `build_input` raises `NessaError(LIMIT_EXCEEDED, details reason
  answers_too_long)` instead of a bare `ValueError`; it runs before `submit_run`, so before
  any run or reservation. `PromptTooLargeError` removed.
- **M4**: the length problem now reads "a claim of 20-240 characters"; the API
  description says "at most 240 characters"; the ADR says the model is asked for one
  sentence and only the length is checked.

## Rulings made this round

1. **No answer to quote is refused before a run.** The content-word rule (I2) means a
   profile whose only answers are short ("art") can never pass the check; rather than spend
   a call that must fail, the submission is refused (`INSUFFICIENT_EVIDENCE`,
   `no_quotable_answer`). The ruling's "every quotation must contain a content word" is
   applied literally (no exception for a whole short answer); the limit is in ADR 0007.
2. **"work", "works", "working" are function words** for the content rule, as in the
   fixture's former list (one list now serves both).
3. **Try again is an explicit flag** (`retry_failed`), so a stale page's automatic request
   can never retry a failed note; a plain repeat still answers 200 with the same run.
4. **A replaced link is kept** (`replaced_at`) rather than updated in place, so the slate's
   history stays readable and the table stays append-only apart from that one column.
5. **The notice, not each card, holds the action**: one Try again or Suggest again per
   slate, above the cards; each card keeps its short "no written note" line and the
   provenance.

## Covering tests

- `backend/tests/domain/test_slate_explanation.py`:
  `test_an_answer_never_unlocks_a_readiness_pay_or_hiring_word` (qualified, ready, paid;
  I1), `test_a_quotation_needs_a_content_word_and_keeps_its_leading_apostrophe` ("and"/"and",
  "s work", "'s work is to maintain", and a valid content quotation; I2),
  `test_a_readiness_affordability_or_hiring_claim_is_refused` (six new M1 phrasings),
  `test_past_the_count_bounds_nothing_more_is_checked_and_the_repair_fits_its_allowance`
  (M2), `test_answers_too_long_for_the_prompt_in_bytes_are_a_typed_refusal` (M3, 36
  answers of three-byte characters), `test_only_an_answer_with_a_content_word_can_be_quoted`.
- `backend/tests/domain/test_slate_explanation_agent.py`:
  `test_the_repair_sent_for_a_flood_of_problems_stays_within_its_allowance` (the text the
  model is actually sent, fence included, ≤ 1,000 bytes; M2).
- `backend/tests/integration/test_slate_explanations.py`:
  `test_a_note_refused_before_any_request_can_be_tried_again_and_the_new_run_replaces_it`
  (budget lowered after submission so the activity refuses: `budget_exceeded`, spend
  `none`, no requests, `can_retry`; a plain repeat returns it; Try again 202, a new run
  replaces the link and writes the note; the failed run kept), `test_concurrent_tries_again_start_one_run`
  (four threads: one 202, three 200, one new run),
  `test_a_failed_explanation_is_unavailable_with_its_failure_and_the_provenance_stays`
  (now also: `can_retry` false and Try again refused `SLATE_ALREADY_EXPLAINED`, for invalid
  twice and for a cut-off), and the refusal test (now also `no_quotable_answer`).
- `apps/web/src/components/Directions.test.tsx`: the note says only the quoted words were
  checked (I2); a note that failed after a request offers Suggest again (POSTs a
  discovery, never the note; no "try again" advice shown); a note that reached no model
  offers Try again and sends `retry_failed: true` only on the click; a refused request
  offers Try again and re-sends plainly; a refused Try again (`SLATE_ALREADY_EXPLAINED`)
  turns into Suggest again.

RED evidence: the domain tests first failed at import (the new names); I then ran each
reviewed input through the FIX_BASE `check_explanation`/`build_input` from a scratch copy
of `a751c7b`'s module: "qualified", "paid", "and"/"and", "s work" and the four M1
phrasings each returned no problem, and the multi-byte input raised the untyped
`PromptTooLargeError`. After the fix: 46 contract tests passed, then the agent suite.
The web test for the Suggest-again wording failed (RED) before the notice change and
passed after. The integration tests for I3 were written with the server change (at
FIX_BASE the `retry_failed` field is refused as unknown, so they could not pass there);
they passed on first run after it.

## Commands and output

- `uv run --locked pytest tests/domain -q`: 484 passed (after the contract and agent
  changes).
- `uv run --locked pytest -m integration tests/integration/test_slate_explanations.py -q`:
  8 passed.
- `uv run --locked pytest -m integration tests/integration/test_slate_explanations.py tests/integration/test_evaluation.py tests/integration/test_live_eval_ledger.py tests/integration/test_migrations.py tests/integration/test_isolation.py tests/integration/test_discovery.py -q`:
  43 passed.
- `pnpm run generate` (client regenerated, committed in `320aa34`); `pnpm exec vitest run`:
  24 files, 201 tests passed.
- `pnpm run review-screenshots`: first run failed at all three sizes on my own bug (an
  `evaluate` callback using a Node variable; partial captures restored); after the fix,
  3 passed, 30 shots per size with axe/overflow/console/font/overprint checks clean;
  rerun after the notice wording fix, 3 passed, 30 shots per size clean. Unrelated
  captures that changed by noise only (correlation references, timestamps, the
  reconnecting shot's timing) were restored.
- `make check` on `42ef206`: exit 0 (ruff format 184 files unchanged, ruff clean, mypy
  clean, pytest 581 passed / 195 deselected, fixture validator passed; web: client
  matches, Biome clean, `tsc` clean, Vitest 24 files / 201 tests).
- `make acceptance` on `42ef206`: exit 0. Backend `pytest -m "integration or stack"`: 195
  passed, 581 deselected (5 min 0 s), including the 8 explanation tests, EXP-01 over the
  full release with the content-word fixture, the live-eval orchestration and the
  migration and isolation suites with 0012. Storybook build passed. Playwright: 22 passed
  (the demo journey with the fixture explainer's note and no outside request; every story,
  `SlateNoteRetry` included, renders and passes axe; the visual package at three sizes,
  30 shots each).

## Revised proposed CLAUDE.md wording (not edited)

In "Non-obvious invariants", after the first bullet's last sentence, add:

> A slate's written "Why this could suit you" is one bounded `slate_explanation` call per
> discovery, over its first view; every quotation is verified as a span of the pinned
> answers or that occupation's ESCO record (only the quoted words are checked, and the UI
> says so); only a run refused before any request may be tried again, by the person's
> click; the note changes no suggestion (ADR 0007 decision 12).

and to the "Every consequential write..." bullet, add:

> A command's answer is kept as its receipt in plaintext: never put model output in it.

## Remaining concerns

- Only the quoted words are checked (by ruling, no claim-to-quotation word check); the
  note now says so.
- A pydantic-ai schema-validation retry (invalid JSON, wrong types) is worded by the
  library and repeats the rejected output in its message, so that repair can exceed the
  1,000-token allowance by up to the output's size; `repair_message` bounds only the
  check's own repair. The discovery and interview tasks share this pre-existing
  behaviour; not changed here.
- Short answers alone ("art") cannot be quoted; such a profile is refused before a call.

---

# Fix round 2 (FIX_BASE `d16ffe3`)

Commits: `99d4560` (code, tests and docs for R2-I1, R2-M1–M5), `e5714c5` (captures) and
`748dd6d` (this round's checks in the review addendum). No live calls; no
API change (the generated client matched, so it was not regenerated).

## Changes

- **R2-I1** (`slate_explanation.py`): `COMMON_WORDS` now holds every entry of four
  letters or more of NLTK's English stopword list, contraction stems included (about,
  above, after, again, against, aren, because, before, being, below, between, couldn,
  didn, does, doesn, doing, down, during, further, hadn, hasn, haven, having, hers,
  herself, himself, itself, mightn, mustn, myself, needn, once, ours, ourselves, shan,
  should, shouldn, theirs, themselves, through, under, until, wasn, were, weren, whom,
  wouldn, yours, yourself, yourselves, and the earlier ones), plus could, every, might,
  must, ought, shall, upon, whose, within, without. `content_words` folds as the matcher
  folds (`_folded`: compatibility forms, case, apostrophe and dash forms). The content
  check now runs on the verified span (the source's own characters) instead of the
  model's raw text, after verification, so a fullwidth "with" is "with".
- **R2-M1**: `_in_word` in `find_span`'s boundary test: an apostrophe after a letter is
  part of its word, on either side of a span. So "s tools" and "'s tools" are no span of
  "mechanic's tools", and neither is "mechanic" (the word there is "mechanic's").
- **R2-M2**: `_unwrapped` takes spaces and double quotation marks off both ends and
  closing punctuation off the end, and single quotes only as a matching pair (`'…'` or
  `‘…’`); a lone leading or trailing apostrophe stays.
- **R2-M3**: the "in ... demand" pattern treats `-` as a separator; new patterns "high
  demand" (high/great/growing/strong/huge/big/constant followed by demand, hyphen or space), "sought after",
  "employers want/need/are looking/look/seek", "short of staff/short-staffed"; new word
  "paying" ("well-paying").
- **R2-M4** (`Directions.tsx`, `vocabulary.ts`): `NOTE_REFUSAL_REASON` (`no_quotable_answer`,
  `answers_too_long`, `no_suggestions`) and `NOTE_REFUSAL_CODE` (`PROPOSAL_NOT_AVAILABLE`,
  `STALE_INPUT_VERSION`, `SLATE_ALREADY_EXPLAINED`) give each refusal that asking again
  would only repeat its own title and action and its recovery: `edit_answers` (no button;
  the words say to use Edit answers directly, after which the chapter offers Suggest
  again) or `suggest_again` (a Suggest again button and what it does). Never Try again.
  `NOTE_RECOVERY.spent` replaces the failure class's advice once a request was sent. New
  story `SlateNoteAnswersTooShort`; new capture `you--slate-note-too-short`, and
  `you--slate-note-unavailable` recaptured, at three sizes.
- **R2-M5**: the register's REC1-11 now says "at most one current note per discovery (a
  partial unique index on the current link, migration 0012)"; the `reached_no_model`
  docstring says a live attempt holds its reservation before calling (so an unfinished
  or unknown one counts as a call), while a fixture attempt counts only by the requests it
  recorded, so an unfinished one counts as no call.
- ADR 0007 decision 12 (output-and-check and UI bullets) and the Sprint 2 addendum
  describe the above.

## Rulings

1. The apostrophe rule applies on both sides of a span, so a possessive's stem alone
   ("mechanic" from "mechanic's tools") is no longer a quotation either; the whole word
   ("mechanic's") is. Stricter than the finding asked; it is the same rule read
   symmetrically.
2. Added "short of staff" (the finding's example claim "Employers are short of staff"
   passed); it is in the same list as M3's additions.
3. `STALE_INPUT_VERSION` and `SLATE_ALREADY_EXPLAINED` refusals also get fixed words and
   Suggest again (asking again cannot change them either).

## Covering tests (RED, then GREEN)

- `backend/tests/domain/test_slate_explanation.py`:
  `test_a_function_word_quotes_nothing_however_it_is_written` (about/about, being/being,
  could/should, fullwidth with), `test_an_apostrophe_after_a_letter_belongs_to_its_word`
  ("s tools" refused, "careful with a mechanic's tools" accepted, `find_span` cases),
  `test_a_quotation_wrapped_in_single_quotes_is_unwrapped_as_a_pair` (straight, curly, a
  full stop inside), seven new cases in
  `test_a_readiness_affordability_or_hiring_claim_is_refused`. RED: 15 failed before the
  change (`pytest tests/domain/test_slate_explanation.py`: "15 failed, 46 passed"); GREEN
  after. One round-1 expectation changed on purpose: "s work" now fails as "not an exact
  quotation" (it is no longer a span), not as "no content word".
- `apps/web/src/components/Directions.test.tsx`: three cases of "a refusal asking again
  would repeat ... never Try again" (no_quotable_answer and answers_too_long: their words,
  no button, the edit instruction; PROPOSAL_NOT_AVAILABLE: its words and Suggest again);
  each also checks the API's message is not shown and that the request is never
  repeated. The Suggest-again test now checks the two paragraphs separately. RED: with
  `Directions.tsx` and `vocabulary.ts` stashed back to FIX_BASE, 4 failed / 10 passed;
  GREEN after restoring them: 14 passed.

## Commands and output

- `uv run --locked pytest tests/domain -q`: 499 passed.
- `uv run --locked pytest -m integration tests/integration/test_slate_explanations.py tests/integration/test_evaluation.py -q`: 10 passed.
- `pnpm exec vitest run`: 24 files, 204 tests passed.
- `make check`: exit 0 (ruff format 184 files unchanged, ruff clean, mypy clean, pytest
  596 passed / 195 deselected, fixture validator passed; web: client matches, Biome, `tsc`,
  Vitest 204).
- `pnpm run review-screenshots`: 3 passed, 31 shots per size, every check clean; only the
  two note captures above (and the checks files) were kept, noise restored.
- `make acceptance` on `e5714c5`: exit 0. Backend `pytest -m "integration or stack"`: 195
  passed, 596 deselected (5 min 2 s). Storybook build passed. Playwright: 22 passed (the
  demo journey with the fixture explainer's note and no outside request; every story,
  `SlateNoteAnswersTooShort` included, renders and passes axe; the visual package at three
  sizes, 31 shots each).

## Remaining concerns

Unchanged from round 1: only the quoted words are checked (by ruling; the note says so);
pydantic-ai's own schema-error retry can exceed the repair allowance (pre-existing,
shared with discovery and interview); a short answer alone cannot be quoted.

---

# Fix round 3 (FIX_BASE `748dd6d`)

Commits: `35c64a5` (code, tests and docs for R3-I1, R3-M1–M6), `c937e6f` (the
too-short capture and the visual spec's expected wording) and the last commit (this
round's checks in the review addendum). No live calls; no API change (the generated
client matched).

## Changes

- **R3-I1** (`slate_explanation.py`, `fixture_explainer.py`): a new public
  `quoted_span(quote, source)` reads a quotation exactly as the check does (ends unwrapped,
  bounded, whole words); `_verified` now uses it, and so does the fixture explainer, which
  accepts a candidate only if `quoted_span` verifies it and the span has a content word
  (`_accepted`). From a description, the fixture quotes the shared word where it is a
  whole word there, otherwise the whole token holding it with surrounding punctuation
  removed but its apostrophe kept (`_quote_from`: "children's", "students'"); the same for
  its last fallback. Answers are filtered the same way. So the fixture's output passes the
  check by construction.
- **R3-M1**: `pay`, `pays`, `paid`, `paying` are not screened when "attention" follows
  (optionally one word between: "paying close attention").
- **R3-M2** (`_in_word`): an apostrophe belongs to a word only between two letters
  ("mechanic's", "don't") or after an "s" with no letter after it ("students'"); any
  other apostrophe is a quotation mark, so "people person" and "'people person'" (straight
  or curly) verify in "I am a 'people person' at heart".
- **R3-M3** (`_bare`): spaces, double quotation marks and closing punctuation come off
  until nothing changes, before and after taking off a single-quote pair, so
  `"mending bikes".` and `“mending bikes”;` unwrap to `mending bikes`.
- **R3-M4**: ADR 0007 decision 12's known limits list "employers want/need" for careers
  and recruitment work as a known false positive for H-12 (the rule kept), and also the
  closing quote after a word ending in "s" ("'odd jobs'") that reads as a plural possessive.
- **R3-M5**: the stored live EXP-01 output was re-checked offline with the final checker:
  6 suggestions, 7 claims and 16 quotations, accepted with no problem. Only counts and
  problem categories were printed. Caveat recorded in the addendum: that check read ESCO's
  full records as the evidence file keeps them, not the prompt's cut copy, so a quotation
  from beyond the cut would also have passed (none of the claims was refused either way).
  The round-1 sentence now says the output was re-checked after round 1 and again after
  round 3, instead of claiming it passes "the final rules".
- **R3-M6** (`Directions.tsx`, `vocabulary.ts` `NOTE_CARD`): a request refused before any
  run shows on each card "Not started: no written note" and "<reason>. Nessa didn't ask the
  model, so nothing was sent; how Nessa found this suggestion is below." A failed run keeps
  "Failed: no written note ... Nothing from it was kept". The state records whether a run
  existed (`ran`; a refused Try again follows a run that failed, so it counts as ran).

## Covering tests (RED, then GREEN)

- `backend/tests/domain/test_slate_explanation.py`:
  `test_the_fixture_explainer_quotes_a_possessive_as_its_whole_word` (children's, students',
  customer's, furniture's in brackets, don't; the reviewer's two reproductions are the first
  two), `test_whatever_the_answers_and_record_the_fixture_s_note_passes_the_check`
  (Hypothesis, 150 examples over possessives, plural possessives, punctuated tokens and
  function words), `test_a_closing_single_quote_is_not_read_as_a_possessive` (straight and
  curly, plus "students' learning" and "mechanic's tools" unchanged),
  `test_quotation_marks_before_closing_punctuation_come_off_too`,
  `test_paying_attention_is_not_a_pay_claim` (and "paying well" still refused). RED: 9
  failed before the change ("9 failed, 64 passed"), the fixture's children's, students' and
  furniture's cases and the property among them; GREEN after: 73 passed in that file, 511
  in `tests/domain`.
- `apps/web/src/components/Directions.test.tsx`: the refused-request test now also checks
  "Not started", "Nessa didn't ask the model, so nothing was sent", and no "Failed" or
  "Nothing from it was kept". RED: 1 failed; GREEN: 14 passed, 204 in all.

## Commands and output

- `uv run --locked pytest tests/domain -q`: 511 passed.
- `uv run --locked pytest -m integration tests/integration/test_slate_explanations.py tests/integration/test_evaluation.py -q`:
  10 passed (EXP-01 over the full release with the changed fixture included).
- `pnpm exec vitest run`: 24 files, 204 tests passed.
- `make check`: exit 0 (pytest 608 passed / 195 deselected; ruff, mypy, fixture validator;
  web: client matches, Biome, `tsc`, Vitest 204).
- `pnpm run review-screenshots`: the first run failed at all three sizes because the
  too-short shot still waited for the card's old wording (changed on purpose by R3-M6);
  captures restored, the shot's expected text fixed, rerun: 3 passed, 31 shots per size,
  every check clean. Kept only `you--slate-note-too-short` (its card line changed); the
  unavailable shots differed by 132 bytes and `you--reply-failed` only by the slate's
  loading timing below the fold, so they were restored, with the usual noise.
- `make acceptance` on `c937e6f`: exit 0. Backend `pytest -m "integration or stack"`: 195
  passed, 608 deselected (4 min 59 s). Storybook build passed. Playwright: 22 passed (the
  demo journey with the fixture explainer's note and no outside request; every story
  passes axe; the visual package at three sizes).

## Remaining concerns

Unchanged: only the quoted words are checked; pydantic-ai's schema-error retry can exceed
the repair allowance; a short answer alone cannot be quoted. New, recorded as known false
positives for H-12: "employers want/need" for careers work; a closing quote after a word
ending in "s".
