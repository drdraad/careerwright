# Session 1 transcription: implementer report

Base `6acaa71`, branch `l0-local-release`. Three commits, not pushed:

| Commit | Subject |
|---|---|
| `018b38a` | Record session 1: the H-06 rights policy and the H-12 checklist |
| `82e30a4` | Add "carry on", "end it" and "not exist" to the support screen |
| `eb53837` | Read answers for the note's pre-check as the check does |

Not mine: `d6515e4` ("Describe the slate's written note and plaintext receipts in
CLAUDE.md", Darian Raad, 2026-10-28 21:04 UTC, `CLAUDE.md` only) landed on the branch
between `82e30a4` and `eb53837` while I worked. I did not touch `CLAUDE.md`. Both full
checks ran on `eb53837`, so they include it. Review range for this task: `6acaa71..eb53837`
excluding `d6515e4`.

Status: **DONE_WITH_CONCERNS**. The main concern: H-12 cannot be marked fully done. See
ruling 1.

## What I implemented

### 1. The session record (`018b38a`)
- `docs/reviews/session-1.md` (new): date 2026-10-28, held by the product owner. It
  includes a line saying the package was agent-prepared and the answers are the product
  owner's own (R2, R10). It copies the package's questions and answers as given; a script
  compared it line by line with `session-1-package.md`, and all 41 lines match after
  trailing spaces are stripped. The only difference: the two Part headings are one level
  lower, so they sit under the record's own section. A separate section, labelled "agent,
  not part of the record", says where each part was transcribed and what is still open.

### 2. H-06 rights policy (`018b38a`)
- `corpus/README.md`: the "stays pending unless the terms clearly permit" step is replaced
  by a "Rights policy" section with the standing conditions, the two retention definitions
  and a table of the seven classes (Part A lines 1-7) and what each permits. Step 3 of
  "Filling a slot" now says to name the class and the terms relied on, quoted and dated.
  "What lives where" gains the full-text-in-git row (OGL classes only). The OI-07 checklist
  is kept, for pages outside the classes or not clearly within one.
- `corpus/manifest.json`: `policy.rights_policy` holds `set_by`, `always`, the retention
  kinds and seven `classes`. Each class has an id, its package line (A1-A7), its pages, the
  retention it permits and its conditions. `rights_status_values` keeps all four existing
  values and adds `<rights_policy class id>: <the terms relied on, quoted and dated>`. The
  rulings list gains R10. OI-07's disposition now reflects the policy. `manifest_version` is
  0.1.0 → 0.2.0 and `updated` is 2026-10-28. Validated: the JSON parses; every class's
  `permitted` is a subset of `retention_kinds`; `slot_template.rights_status` is still a
  listed value.
- Register H-06: "policy part done 2026-10-28 (session 1) ...; pages outside the classes,
  or not clearly within one, not run — requires human".

### 3. H-12 (`018b38a`, decision 7 detail in `82e30a4`)
- ADR 0007 "Human review checklist": the header names session 1, with a paragraph on how
  the ticks were made. Six items are ticked, each citing its Part B line: support policy
  (line 1), inference rules (line 2), slate policy (line 3: the 164 within-group pairs keep
  folding; the relevance floor as built, so no absolute floor), interview repair rate
  (line 4: tracking only), the 43 evaluation cases (line 5) and counterfactual tolerance
  (line 6). **Not ticked:** "Written explanation" (decision 12), with EXP-01 moved into
  it (ruling 1).
- ADR 0007 body: the status line; decision 3 (repair rate, no target yet); decision 5 (the
  164 pairs confirmed; the provisional paragraph became "accepted for L0 as built"; the
  absolute floor sentence); decision 7 (accepted as built); decision 9 (the REC1-09
  approval: at most $0.07, test model, Task 16, about 10 samples per arm, at most 40
  requests, its own scope above the 9-request cap; not run, no live call); Consequences.
- Register: H-12 is "six of seven checklist items done 2026-10-28 (session 1)". The
  written explanation and EXP-01 are not run — requires human. Session 1 row: held on
  2026-10-28. REC1-09: the approval, with status still `inconclusive`. DIV1-05 and DIV1-06
  (the slate), REC1-02 (inference lists), TEST1-10 (the 43 cases accepted, EXP-01 open)
  and PROF-09 (policy accepted) had stale "provisional (H-12)" wording, now corrected.
  REC1-11 is unchanged in status: decision 12 was not reviewed.

### 4. The three phrases (`82e30a4`, TDD)
- `backend/src/nessa/profile/safety.py`:
  - `_GO_OR_CARRY` replaces `_GO`, so "carry on" (carry, carries, carried, carrying) works
    wherever "go on" does: `_cannot_go_on` and `_no_reason` (helper renamed
    `_go_or_carry_on`).
  - New `_to_end_it`: an intent or wish (`_INTENTS`), then end (-s, -ed, -ing) and "it"
    within 4 words after. It sits beside `_end_it_all`.
  - New `_not_exist`: exist, exists or existed, with an intent or wish and a negation
    (`_negation`: not, never, no longer) within 4 words before it.
  - `POLICY_VERSION` is now `support-policy-6` (ruling 6). The module docstring's review
    status is updated.
- `backend/tests/domain/test_safety.py` `CORPUS`: the brief's 8 rows verbatim (source
  `session1`), plus 4 pinned career false positives (source `session1 limit`):
  - "I can't carry on working nights." (the brief's example)
  - "I'm on a zero-hours contract and I want to end it."
  - "That job is not going to exist in ten years."
  - "I wish commutes didn't exist."
- ADR 0007 decision 7: the version, the CORPUS sentence, and the constructions list (the
  three additions and why they are constructions). In the known limits, "I just want to
  end it" and "can't carry on" are removed from "wording outside it gets nothing", since
  both now trigger. The four new false positives are added. The accepted paragraph says
  the phrases were added after the session and not seen as built. Register PROF-09 is
  updated to match.
- `backend/tests/integration/test_interview_choices.py:137` now expects `support-policy-6`.
  The web mocks `apps/web/src/components/YouChapter.test.tsx:201` and
  `apps/web/e2e/visual.spec.ts:168` carry the same value. The UI never displays it, so no
  pixels change.

### 5. Task 6b carry-over (`eb53837`)
- **Pre-check** (`exploration.py:641`): it now calls
  `accepted_quotation(item.text, item.text)`. The fixture's `_accepted` moved to
  `slate_explanation.accepted_quotation` (`slate_explanation.py:444`): one function, used by
  the pre-check and by every former `_accepted` call in `fixture_explainer.py`. The orphaned
  imports (`quotable` in `exploration.py`; `quotable` and `quoted_span` in the fixture) were
  removed. The docstrings now name the function.
- **Tests:**
  - New integration test
    `test_slate_explanations.py::test_an_answer_the_check_cannot_quote_whole_is_refused_before_any_run`,
    parametrised over straight `'odd jobs'` and curly ‘odd jobs’ as the only answer. It
    asserts 422, `INSUFFICIENT_EVIDENCE`, `no_quotable_answer`, and that the only runs are
    discoveries.
  - The domain test `test_only_an_answer_with_a_content_word_can_be_quoted` is replaced by
    `test_only_an_answer_the_check_accepts_as_a_quotation_of_itself_can_be_quoted`. It uses
    the same predicate, and adds 'odd jobs' in both styles plus a passing 'people person'.
  - The property test's `assume` now uses `accepted_quotation`, and its word strategy gains
    four single-quoted words ('odd, jobs', ‘side, gigs’).
- **ADR 0007 decision 12:**
  - The *When* bullet now reads "no pinned answer is one the note can quote".
  - *Models*: the sentence that said "so its note always passes the check" is rewritten.
    It explains the earlier gap and that the pre-check now uses the same function. It adds
    that every ESCO v1.2.1 title is a quotation of itself: an offline count over all 3,043
    titles, with every description cut step checked as a fallback, found 0 exceptions. It
    states the guarantee as "by construction" (property test).
  - Known limits gain this case, the `odd jobs'` nuance (ruling 8) and the web wording
    mismatch.
- **Register REC1-11:** names the new test.
- **`docs/reviews/sprint-2.md`:** the round-3 recheck caveat now says the full records
  widened three things: quotations beyond the cut, essential skills past the prompt's first
  ones, and the record-only allowance for readiness, pay and hiring words. The round-1
  recheck sentence gets the same caveat, spelt out. I first confirmed from
  `tools/live_eval.py:315-324` that the evidence file stores the taxonomy API's full
  description and every essential skill. The round-1 report also says that recheck read
  the same private file.

## Rulings I made, and why

1. **H-12 is six of seven items, not "done".** Session 1's package (6 lines) was drafted
   before Task 6b added the ADR's "Written explanation" item and EXP-01. Its line 5 says
   "The 43 evaluation cases", while the ADR now has 44. The ledger confirms this: "session
   1 package drafted (... H-12 6 lines)" precedes Task 6b's completion. Under R2 I may tick
   only what the product owner answered. So decision 12's item and EXP-01 stay "not run —
   requires human", and the brief's "register H-12 done" is recorded as partly done.
   Closing it needs those items put to the product owner, for example in session 2's
   package.
2. **Class 2 full text.** Line 2 ("OGL where they say so: same as line 1") gives line 1's
   full-text permission "with the OGL attribution". That attribution needs the OGL, so I
   recorded full-text commits for class 2 only for a page that says it is under the OGL.
   Keep privately and commit excerpts apply to the whole class. This is the narrower
   reading; the product owner may widen it.
3. **Job boards, "unless their terms clearly allow more".** Recorded literally, plus: if it
   is not clear what the terms allow, the page stays reference only. I set no cap on "more";
   the agent keeps what the quoted terms clearly allow.
4. **Manifest shape.** Class ids (`govuk`, `public-sector`, `course-provider`,
   `professional-body`, `employer-posting`, `job-board`, `other`). `rights_status` names the
   class as `<class id>: <terms>`, so no new slot field is needed. I bumped
   `manifest_version`; the schema version is unchanged, because the change only adds keys.
5. **Constructions.**
   - Both new windows are 4 words, the screen's intent window.
   - "exist" forms are exist, exists and existed. "existing" is left out: it is mostly an
     adjective in career text ("existing skills"), and with it, "I don't want to use
     existing skills" would trigger.
   - `_INTENTS` is reused unchanged, including "going". So "That job is not going to exist
     in ten years" triggers (pinned; concern 2).
6. **`support-policy-6`.** Every earlier change to the matching bumped `POLICY_VERSION`
   (`e777cf3` 2, `561c97f` 3, `16ee339` 4, `3289169` 5). The value appears in API responses,
   so the new list gets its own version. The response schema is unchanged, so the generated
   client is unchanged.
7. **Not changed: `REVIEW_STATUS` and the panel's "This note is provisional until it is
   reviewed."** These are user-visible API and UI copy, outside the brief. The three phrases
   have also not been seen as built. Proposed below.
8. **The pre-check predicate is the whole answer, as ruled.** The brief says that for
   'odd jobs' "no quotation of it verifies". That overstates. I ran `quoted_span` on both
   quote styles: `odd jobs`, `jobs` and the whole `'odd jobs'` are all refused, but a
   quotation that drops the opening mark and keeps the closing one (`odd jobs'`, or
   `odd jobs’`) verifies. So the pre-check can refuse an answer set that a model could, in
   principle, still quote. A model would rarely write that form, so the refusal still saves
   a likely-wasted paid run. I kept the controller's ruling and wrote the nuance into
   decision 12's known limits.
9. **The counterfactual tick.** Line 6 asked for approval to run the comparison; it did not
   ask a separate tolerance question. The tick says the approval covers the comparison as
   built: INT-04/05's `current_role` and `weekly_study_hours`, with the samples per arm $0.07
   covers. The Task 6 report's estimate is 10 per arm × 2 arms, at most 40 requests, $0.07
   worst case.
10. **Historical review tables not changed.** `docs/reviews/sprint-2.md` "Open" rows
    (lines 294-295 and 461) still read "Not run — requires human" or "Open" for H-12, as
    they did at that review. Only the caveats the brief named were edited. `session-1.md` is the newer
    record.

## Tests and checks (final code, `eb53837`)

**TDD, the three phrases.** RED after adding the 8 rows, before the code:

```
uv run --locked pytest tests/domain/test_safety.py -q -k session1
FAILED ...[session1: I can't carry on.]
FAILED ...[session1: There's no reason to carry on.]
FAILED ...[session1: I want to end it.]
FAILED ...[session1: Sometimes I want to not exist.]
FAILED ...[session1: I wish I didn't exist.]
5 failed, 3 passed, 148 deselected in 0.14s
```

The 3 must-not-flow rows passed before and after. GREEN after the code:
`test_safety.py`: 156 passed, then 160 with the 4 pinned limit rows.

**TDD, the carry-over.** RED before the fix:

```
uv run --locked pytest -m integration tests/integration/test_slate_explanations.py -k cannot_quote_whole -q
E       KeyError: 'error'      (the request was accepted: no error envelope)
FAILED ...[straight quotes]
FAILED ...[curly quotes]
2 failed, 8 deselected in 20.82s
```

GREEN after it: `uv run --locked pytest -m integration tests/integration/test_slate_explanations.py -q`,
10 passed in 40.79s (the 8 existing and the 2 new).

**Safety and slate-explanation tests** (as asked):

```
uv run --locked pytest tests/domain/test_safety.py tests/domain/test_slate_explanation.py tests/domain/test_slate_explanation_agent.py -q
242 passed in 0.65s

uv run --locked pytest tests/domain/test_safety.py -k session1 -v
[session1: I can't carry on.] PASSED
[session1: There's no reason to carry on.] PASSED
[session1: I want to end it.] PASSED
[session1: Sometimes I want to not exist.] PASSED
[session1: I wish I didn't exist.] PASSED
[session1: I'd like to carry on working in healthcare.] PASSED
[session1: Jobs like that don't exist here.] PASSED
[session1: The course ended and I want to start a new one.] PASSED
[session1 limit: I can't carry on working nights.] PASSED
[session1 limit: I'm on a zero-hours contract and I want to end it.] PASSED
[session1 limit: That job is not going to exist in ten years.] PASSED
[session1 limit: I wish commutes didn't exist.] PASSED
12 passed, 148 deselected in 0.06s
```

Each row is also checked wrapped in other text and in capitals.

**`make check`** on `eb53837`: **exit 0**.
- Backend: ruff format (184 files already formatted), ruff check (All checks passed),
  mypy (no issues in 184 source files), pytest 620 passed and 197 deselected in 3.51s
  (608 at base + 12 CORPUS rows), and the fixture validator passed.
- Web: the generated client matches, Biome checked 108 files with no fixes, `tsc` passed,
  and Vitest ran 24 files with 204 tests passed.
- No warnings in the log.

**`make acceptance`** on `eb53837`: **exit 0**.
- `pytest -m "integration or stack"`: 197 passed, 620 deselected in 312.59s (195 at base +
  the 2 new 'odd jobs' cases).
- The Storybook build completed.
- Playwright: 22 passed (2.0m).
- The only warning is Node's `NO_COLOR` ignored because `FORCE_COLOR` is set, a harness
  environment note. No skips or retries.

**Probes** (scratchpad only, not committed):
- `probe_titles.py`: over all 3,043 ESCO v1.2.1 occupations in the pinned zip, read in
  place. 0 titles fail `accepted_quotation(title, title)`. 0 lack a fallback description
  quote at any cut step (600/400/250/150/100).
- `probe_screen_diff.py`: the screen at `HEAD` before commit 2 against the new one, over
  6,727 strings already in the repository. These were the backend's Python string
  literals, the JSON under `fixtures/` and `backend/tools/` (the evaluation cases and
  persona fixtures included), and the quoted strings of the web app's sources, tests,
  stories and journeys. Only the 5 new must-flow rows (and my docstring) change result. No
  existing career text in fixtures, cases or tests newly triggers.
- `probe_fixture_property.py`: the fixture property at 5,000 examples, with the new
  strategy. No counterexample.
- A check of 8 career sentences that reach the new constructions found the 4 false
  positives pinned above. The other 4 did not trigger: "I'd like to carry on with my
  apprenticeship.", "Could I carry on part-time?", "My role won't exist in five years." and
  "I wish that rule did not exist at my depot." I composed no distress or self-harm wording
  in tests, docs or probes. The must-flow rows are the brief's verbatim.

## Live calls (R5)

None. No Meta call, and `.env` was not read. Cost $0.00. The REC1-09 comparison is
approved for Task 16, not run.

## Not run, blocked, concerns

1. **H-12 decision 12 and EXP-01: not run — requires human** (ruling 1). They need the
   product owner's answer. This is the main deviation from the brief.
2. **A false positive the AI-resilience domain will hit.** "That job is not going to exist
   in ten years" (and "isn't going to exist") shows the panel, because "going" is a listed
   intent. Talk about jobs disappearing is ordinary here. It is pinned and listed in the
   ADR. Narrowing it would mean dropping "going" from `_not_exist` only, which is a policy
   change for the controller or H-12 to decide.
3. **The three phrases are not reviewed as built.** The product owner said "yes" to adding
   them; their form (constructions, windows) is the controller's ruling and my
   implementation. The ADR, register, docstring and session record all say so.
4. **Stale user-visible "provisional" wording** (ruling 7). If the controller wants it, the
   exact proposal:
   - `safety.py:43`: `REVIEW_STATUS = "accepted for L0 at session 1 (human gate H-12)"`.
   - `Conversation.tsx:133-134`: drop "This note is provisional until it is reviewed."
   This needs the Vitest and visual mocks updated and the support-panel captures checked.
   The three new phrases would then need the product owner's look first.
5. **The 'odd jobs' refusal's words.** The web shows "Your answers are too short to quote"
   (`vocabulary.ts:547`) for `no_quotable_answer`, which misdescribes this rare case. I did
   not change it (UI copy outside the brief). It is noted in decision 12.
6. **Process disclosures.**
   - Commit `018b38a`'s message was passed to `git commit -F -` through a heredoc on stdin;
     no file was written. The later commits used message files written with the Write tool.
   - `make check` and `make acceptance` output was redirected into log files in the
     scratchpad, outside the repository.
   - Every repository file change was made with Edit or Write.

## CLAUDE.md

No change needed for the support screen ("any listed risk word, in any form" still holds).
Optional, for Task 7b and later, one line under "Non-obvious invariants":

> - Corpus pages are kept only as the session 1 rights policy permits (`corpus/README.md`,
>   `corpus/manifest.json` `policy.rights_policy`): name the class and the terms relied on
>   in `rights_status`; a page outside the classes stays `pending human rights review`.

## Paths a reviewer can skip

None generated or vendored. The diff is docs, the safety module and its tests, three
explanation modules and their tests, and two web test mocks (a single version string).

---

# Fix round 1 (FIX_BASE `eb53837`)

Commits, not pushed:
- `9d804f1` Fix round 1: "not exist" takes want or wish; the panel drops "provisional"
- `e5365e1` Fix round 1: recapture the support panel and the unquotable-answers note

Status: **DONE**. All six Minors are fixed as ruled.

## Changes, finding by finding

1. **"going" false positive.**
   - `safety.py`: `_not_exist` now counts `_WANT_OR_WISH` (`_WANT` plus wish, wishes,
     wished, wishing) instead of `_INTENTS`.
   - `CORPUS` pins "That job is not going to exist in ten years." and "Those roles aren't
     going to exist." as must-not-flow rows (source `session1 fix1`, the controller's
     rows verbatim). The first was a `session1 limit` must-flow row and has moved. All five
     `session1` must-flow rows still flow.
   - ADR 0007 decision 7: the constructions now say "want or wish (any of their forms)",
     and why. The known limits add the recall given up: another listed intent word before a
     negation and "exist" gets nothing. The "going" false positive is removed from the
     false-positive list, and "Two known gaps" is now "Known gaps" (three are listed).
     PROF-09 matches.
   - `POLICY_VERSION` is now `support-policy-7`. This is my addition, by ruling 6 of the
     main report: the matching changed, and every earlier change bumped the version. The
     integration-test literal, the two web mocks, the ADR and PROF-09 follow.
2. **Stale "provisional" wording.**
   - `Conversation.tsx`: the panel ends at "These services were checked on their own
     websites on 28 October 2026." `YouChapter.test.tsx` asserts the panel holds neither
     "provisional" nor "reviewed".
   - `safety.REVIEW_STATUS` is now "accepted for L0 at session 1 (human gate H-12); the
     three phrasings added on 2026-10-28 are not yet reviewed as built".
   - These now agree with it: the module docstring, the H-12 row, the PROF-09 row (status
     cell and evidence) and `test_interview_choices.py:139-141`. The test asserts equality
     with `REVIEW_STATUS`, the "accepted for L0 at session 1" prefix and "not yet reviewed
     as built". The web mocks carry the same value.
   - Also stale and changed: the API field description `SupportNoteOut.review_status`
     ("The policy is provisional until reviewed.") is now "How far the policy is reviewed
     (gate H-12)." The client was regenerated with `pnpm run generate`; the diff is that
     one description in `openapi.json`, `schemas.gen.ts` and `types.gen.ts`.
3. **Neutral refusal title.** `vocabulary.ts` `no_quotable_answer` is now "Your answers
   can't be quoted on their own"; the action and recovery are unchanged.
   `Directions.test.tsx` and the `you--slate-note-too-short` matcher in `visual.spec.ts`
   follow. Decision 12's known limit now quotes the new title. The capture name is kept, to
   avoid renaming files.
4. **Class-2 OGL reading.** `session-1.md`'s transcription notes (the agent section)
   name "full text only for a page that says it is under the OGL" as the transcriber's
   reading of "OGL where they say so", which the product owner may widen. The record
   itself is unchanged.
5. **REC1-09 wording.** Decision 9, its checklist item ("Run approved") and REC1-09 quote
   the approval as the package gave it: "run the powered comparison at release, estimated
   at most $0.07 on the test model". They label as derived from the Task 6 report, not
   asked at the session: about 10 samples per arm, at most 40 requests, its own scope above
   the 9-request cap, and INT-04/05's fields as built. They state that the pass rule across
   several samples per arm is still open and must be decided before Task 16 runs it. The
   ADR status line now says "approved to run at release (its pass rule is still open)"
   instead of "accepted ... as built". `session-1.md`'s Part B line 6 note says the same.
6. **Manifest.**
   - The generic value is now `<rights_policy class id other than other>: <the terms relied
     on, quoted and dated> (a page of class other stays 'pending human rights review')`.
   - Class `other`'s conditions say it is never named in `rights_status`.
   - `git_holds` adds the OGL classes' full text committed for the option pack, with the
     OGL attribution.
   - `corpus/README.md` step 3 says "for any class but `other`".
   - Validated: the JSON parses, and the slot template's status is still a listed value.

## Covering tests (RED, then GREEN)

- **Item 1:**
  - `uv run --locked pytest tests/domain/test_safety.py -q -k session1`, RED: 2 failed
    ("session1 fix1: That job is not going to exist in ten years.", "session1 fix1: Those
    roles aren't going to exist."), 11 passed.
  - GREEN: `test_safety.py` 161 passed. `-k session1 -v`: all 13 rows PASSED (5 must-flow,
    3 must-not-flow, 2 fix1 must-not-flow, 3 limit rows).
- **Item 2, API:**
  - `uv run --locked pytest -m integration tests/integration/test_interview_choices.py -k is_sent_with_the_support_panel_and_none_of_it_is_stored -q`,
    RED: `AssertionError` on `.startswith("accepted for L0 at session 1")`.
  - GREEN: 1 passed in 11.32s.
- **Item 2, UI:**
  - `pnpm exec vitest run src/components/YouChapter.test.tsx -t "risk stem"`, RED: 1
    failed. The panel text contained "This note is provisional until it is reviewed."
  - GREEN: `YouChapter.test.tsx` 17 passed.
- **Item 3:**
  - `pnpm exec vitest run src/components/Directions.test.tsx`, RED: 1 failed (the
    INSUFFICIENT_EVIDENCE refusal case).
  - GREEN: 14 passed.
- **Items 4-6:** docs and data. The manifest was checked by parsing it (above).
- Focused, as before:
  `uv run --locked pytest tests/domain/test_safety.py tests/domain/test_slate_explanation.py tests/domain/test_slate_explanation_agent.py -q`:
  243 passed.

## Checks (final code, `e5365e1`)

- **`make check`: exit 0.**
  - Backend: ruff format (184 files already formatted), ruff check (All checks passed),
    mypy (no issues), pytest 621 passed and 197 deselected, and the fixture validator
    passed.
  - Web: the generated client matches, Biome checked 108 files, `tsc` passed, and Vitest
    ran 24 files with 204 tests passed.
  - No warnings. A first run failed on Biome's line length in `visual.spec.ts`; I wrapped
    the line with Edit and re-ran.
- **`pnpm run review-screenshots`** (on the UI as committed): 3 passed (1440x900,
  768x1024, 390x844). The `checks-*.json` files are byte-identical to before: every shot's
  axe, overflow, overprint, console and font checks are clean.
  - Kept: `you--support-note` (no "provisional" sentence) and `you--slate-note-too-short`
    (the new title), at the three sizes. I looked at the 1440x900 and 390x844 captures.
  - Restored with `git restore` as noise: `not-found`, `not-invited` and
    `you--reply-to-review` at three sizes, and `you--slate-note-unavailable` at two. Each
    differed by 3 to 12 bytes (timestamps and correlation references), as in earlier rounds.
- **`make acceptance`** on `e5365e1`: **exit 0**.
  - `pytest -m "integration or stack"`: 197 passed, 621 deselected in 309.82s.
  - The Storybook build completed.
  - Playwright: 22 passed (2.1m).
  - The only warning is Node's `NO_COLOR`/`FORCE_COLOR` environment note. No skips or
    retries.

## Live calls

None. Cost $0.00. `.env` was not read.

## Notes

- `support-policy-7` is my addition beyond the rulings (reason above). If you would rather
  keep `-6` for the whole transcription, it is a five-place revert.
- The `SupportNoteOut.review_status` description change was not named in the ruling. It
  was the same stale claim, and changing it regenerated the client (three generated
  files; skip them in review beyond that one string).
- Process: every repository file change was made with Edit or Write. The noise-only PNG
  captures were restored with `git restore`. Check output was redirected into scratchpad
  logs, and commit messages were passed from files written with Write.
