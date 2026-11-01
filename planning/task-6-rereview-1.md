# Task 6 re-review 1 (fix diff dec43e6..cfdae68)

Scoped re-review: I checked each fix-list finding and looked for regressions in the fix diff. This is not a fresh full review.

## Method

**Reading.** I read the contract, the fix list, both reviews, the report's "Fix round 1" section and the 6.7k-line diff, in six passes:
1. backend source;
2. backend tests and tools;
3. ADR, register, review and runbook;
4. web components;
5. web lib and tests;
6. e2e.

I treated the report as unverified claims.

**Focused checks.** Each check answers one named doubt:
- `cd backend && uv run --locked pytest tests/domain/test_safety.py -q` gave **32 passed**. This covers the A-I-1 positives and negatives.
- `cd backend && uv run --locked pytest tests/eval/test_evaluation.py -q` gave **26 passed**. SUP-01..05 still expect support; SUP-06..13 expect none.
- `cd apps/web` checks of commit 7f2a45b:
  - `pnpm exec biome check e2e/visual.spec.ts src/components/YouChapter.test.tsx` found no fixes needed;
  - `pnpm exec tsc --noEmit` exited 0;
  - `pnpm exec vitest run src/components/YouChapter.test.tsx` gave **15 passed**.
- Ledger: I recomputed `docs/evidence/live-usage.jsonl` with Python, using `-I` (isolated mode, read-only).
- A-I-2: I ran an offline probe of the alias rule over ESCO v1.2.1 `occupations_en.csv`, extracted from `var/datasets/` into my scratch directory. It uses my Python re-implementation of `nessa.concept_key` (r0008), so it approximates the database rather than querying it.

**Not done.** No Docker, no live calls, no `.env`, no full suites, no edits to the repository.

## Per finding

37 findings in the fix list: **35 Fixed, 1 Partially fixed (A-I-1), 1 Not fixed (A-M4, deferral accepted).**

### Backend, Important

**A-I-1 (distress screen false positives): Partially fixed.**

What is fixed:
- The reviewer's five sentences, plus three more, are now negative cases: `tests/domain/test_safety.py` and SUP-09..13 in `evaluation_cases.json`.
- All 7 existing positives, and 5 new ones, still match; I ran the file (32 passed).
- SUP-09 changing from "support shown" to "not shown" is the intended policy change. It is recorded in ADR 0007 decision 7.
- The RED claim fits: under the old bare-prefix patterns, every new negative would match.

The matcher's structure:
- It still matches first-person phrase forms. Most new "meaning" rules are blacklists of the word that follows, not a requirement for intent context. In `backend/src/nessa/profile/safety.py`:
  - `kill myself` (:42), `take my life` (:44-45), and `suicide`/`self-harm` via `_CAREER_CONTEXT` (:36-39) use negative lookaheads;
  - only `live`/`go on` (clause end, :35, :51-52) and `hurt myself` (intent words, :48-49) need positive context.
- So the fix keeps the *tested* true positives but turns some untested categories of explicit statements into misses that nobody is told about. The ruling said "keep true positives".

The new misses:
1. `kill(?:ing)? myself(?!\s+(?:with|over|at|for|…))` (:42). This excludes a statement whose next word gives a means or a reason ("with", "for", "over").
   - The alternatives have no trailing `\b`, so any next word that merely *starts* with those letters is excluded too ("for…", "at…", "with…").
   - Compare `take my life(…)\b` at :45, which does have the boundary.
2. `hurt(?:ing)? myself` now needs one of eight preceding intent words (:48-49). A disclosure of ongoing or past self-injury phrased with "hurt(ing) myself" alone no longer matches. Only `harm(ing|ed) myself` and `self-harm` still cover that.
3. `don't want to live` now fires only at a clause end, or before "anymore"/"now" (:51). Any trailing qualifier suppresses it, not just a place ("in London").
4. `_CAREER_CONTEXT` (:36-39) ignores who is speaking. "support", "services", "risk", "lines" and "helpline" after the word suppress the match even when the person is talking about themselves. `services?`, `lines?` and `risk` also lack a trailing `\b`.

These misses are not disclosed:
- ADR 0007 decision 7, the H-12 checklist and `docs/reviews/sprint-2.md` list only "I can't go on" and indirect wording as known misses.
- The checklist mentions the career-context words, but not items 1-3 or the missing boundaries.

Fix:
- Narrow each exclusion to the career figure it targets (for example "killing myself with/over" followed by a work noun; "hurt myself" excluded only before an accident context such as lifting, at work or playing; "live in/near/with …").
- Add `\b` to every exclusion alternative.
- Have the implementer add matched positive and negative pairs for each exclusion.
- List any remaining deliberate misses in the H-12 checklist.

**A-I-2 (transitive folding): Fixed.**
- `slate.py:231-253`: `_aliases` uses the preferred label or equal label sets. A candidate is compared with group leads only, so chaining is impossible by construction.
- Test: `test_slate.py::test_folding_never_chains_unrelated_work_through_shared_labels`.
  - My probe confirms its label sets are faithful subsets of ESCO's real labels for quarry engineer, quarry manager, mine manager, building caretaker and building cleaner.
  - It would fail on the old union-find, which put all five in one group.
- The reviewer's other clusters are not tests, but none of them folds under the new rule:
  - ISCO 26: actor/actress, singer, composer, music producer, animation director;
  - ISCO 34: ski instructor, swimming teacher, sports coach;
  - judge and puppet designer.
- The one exception is composer ↔ music producer: ESCO itself lists "music producer" as a label of composer.
- Residual: see N-M3.

**A-I-3 (sketch re-resolution): Fixed.**
- The sketch resolves by the person's choice first:
  - `sketch.py:93-104,122-131`;
  - `store.chosen_occupation_uris` (`store.py:130`);
  - `taxonomy_store.concepts_by_uri` (`taxonomy_store.py:271`).
- Test: `test_discovery.py::test_the_sketch_uses_the_occupation_the_person_chose_even_when_its_title_is_shared`. It gives a sampled occupation a shared alternative label, and the old code would return `ambiguous`.
- Note: the fix list said "concept ID"; the implementation resolves through the source's ESCO URI. That is the reviewer's suggested route and is equivalent within a release.

**A-I-4 (salary period): Fixed.**
- `interview.py:75-84`, `:303-310`: a `stated` floor needs the proposal's period words in a cited message; a bare amount is `inferred`.
- The fixture has week, pay and spend words (`fixture_interviewer.py`).
- Tests:
  - `test_interview_contract.py::test_a_salary_floor_is_stated_only_when_the_cited_words_give_its_period`, which fails on the old code: "12 per year" was `stated`;
  - the £500 a week and £1,500-on-courses assertions in `test_interview_agent.py`.

**A-I-5 (family sampling): Fixed.**
- `slate.py:256-271`, used at `:303`: the pool is filled round-robin across ISCO minor groups in relevance order.
- Test: `test_the_bounded_pool_samples_across_families_before_relevance_cuts_it`. The old cut gave `{723}`.
- DIV1-10 now reads "verified for the channels and family sampling; planned for oversampling".

**A-I-6 (eval robustness): Fixed.**
- Contract `interview-turn-3`: the reply holds no "?" and `next_question` at most one (`interview.py:355-358`). The instructions say so, the fixture no longer repeats the question, and the web shows each field once.
- The checker:
  - counts per field, plus a joined second ask;
  - `_has` matches word starts, or whole words (`whole_words`) for INT-04/05;
  - `same_fields_as` compares only the listed unambiguous fields.
- Outputs go to `NESSA_HOME/evidence/live-eval.jsonl` (directory 0700; `live_eval.py:315-316`).
- REC1-09 is now "inconclusive (one sample per arm)".
- The tests would fail on the old code: the paraphrase, two-asks and `contest` cases.

### Web and docs, Important

**B-I1 (tray edits): Fixed.**
- `ReviewTray.tsx:104-123`: edits are checked by `readField` before anything is sent, and an error stops the send (`:115`). The error is shown with `FieldError`.
- A state selector is shown, and an Unknown proposal starts as provided.
- Edits travel in the one decision: `DecideTurn.edits` is checked by `_checked_edits` (`conversation.py:271-305`) and committed in the same version.
- Covering tests:
  - backend `test_interview_turns.py::test_a_decision_saves_the_person_s_edits_with_the_accepted_ones_as_one_version`, which checks the refusal reasons, that nothing is saved on refusal, and one version with a `direct_entry` source;
  - web `YouChapter.test.tsx`, the "an edit in the tray…" cases.
- The report says the "saving fails" case is a regression guard rather than a RED test; that is correct.

**B-I2 ("Send it again"): Fixed.**
- One send path (`useSendMessage`, `queries.ts:334`): its errors and the support response render in `Conversation`.
- `sendBlocked` (`YouChapter.tsx:107`) covers paused, no key, a running turn and a pending send, and reaches the resend button.
- A stale tray hides once a newer turn exists (`conversation.ts:120`).
- Duplicates are prevented end to end:
  - `ChangeKeys` reuses the key for an identical request until it settles;
  - `run_idempotent` serialises same-key duplicates through the workspace lock (`submit_turn` locks) and the unique receipt, then replays (`receipts.py`). This was already tested for concurrent duplicates in `test_workspaces_and_profiles.py`.
  - After a success, TanStack v5 waits for `onSuccess`'s `invalidateQueries`, so `isPending` lasts until the new running turn is listed. A second key cannot be minted in between.
- Test: "sends once, says when it can't, and shows a support response". The old code would send two POSTs and drop the support response.
- Residual, outside the finding: the API does not refuse a second turn under a *new* key while one is running (for example from two tabs).

**B-I3 (undo provenance): Fixed.**
- `POST .../profile/revert`:
  - `routes_profile.py:74-108` runs it through `run_idempotent`;
  - `commands.py:186-217` calls `visible_workspace(lock=True)`, applies the expected-version rule (`stale_version`, `:195`), and refuses a `to_version` that is not earlier (`:201`);
  - every field is re-checked by `input_type`;
  - it commits through the one `commit_profile_version`. `ExistingSource` cites the original `source_ref_id` without re-recording it (`:130`), so source, basis, fixture or synthetic label, and turn citation are kept by construction.
- It is not a second write path, and RLS applies through `actor_transaction`.
- Tests:
  - `test_undo_restores_the_earlier_answers_with_their_own_sources_as_a_new_version` covers 409 stale, 422 not-earlier, the field identical including `source_ref_id`, and the sources list unchanged;
  - web: the revert body is `{expected_version: 2, to_version: 1}`, with no PUT.
- Gap: no cross-account 404 test for the new endpoint (N-M1).

**B-I4 (announcements and focus): Fixed.**
- One mounted region (`YouChapter.tsx:130`). A repeated text is still re-read.
- Each new checked turn is announced by its turn ID and never on load (`Conversation.tsx:223-229`).
- Save and undo are announced, and focus moves to "What we know" (`:62-64`, `:171`). After the entry choice, focus moves to the question.
- Tests: the `[UI-06]` cases and the undo case in `YouChapter.test.tsx`.

**B-I5 (register honesty): Fixed.**
- MODEL-03: the latest failed turn now renders what streamed, labelled "Stopped: not checked, nothing saved". This is tested in "offers Try again…".
- STATE-06 cites tests that exist (I checked the names with grep).
- MODEL-07: the `CREDENTIAL_REVOKED` test was added (`KeySetup.test.tsx:86`).
- S0-V08 is narrowed to the four states that are tested.

### Minor

| ID | Status | Evidence |
|---|---|---|
| A-M1 | Fixed | The 404 write uses a real slate `concept_id` (`test_discovery.py`). |
| A-M2 | Fixed | `test_a_discovery_invalid_after_its_repair_fails_typed_and_has_no_slate`: 2 requests, then `PROPOSAL_NOT_AVAILABLE`, and no leak. The Standard-only test was not in the fix list. |
| A-M3 | Fixed | Asserts `(pool_size, beyond>0) == (POOL_LIMIT, True)`. |
| A-M4 | Not fixed: deferral acceptable | See below. |
| A-M5 | Fixed | `sketch.py:154` re-raises every error except `no_search_terms`. The re-raise path is untested; acceptable for a narrowing. |
| A-M6 | Fixed | Test `test_a_current_role_with_no_searchable_word_is_reported…`. |
| A-M7 | Fixed | `document.py:136` and `interview._salary`, with tests. See N-M2 for the read-side effect. |
| A-M8 | Fixed | See below. |
| A-M9 | Fixed | The release is recorded and `release_note` added (`exploration.py:384,469`). Only the pure function is tested (N-M9). |
| A-M10 | Fixed | See below. |
| A-M11 | Fixed | $0.001575 in the register and the review. |
| A-M12 | Fixed | The H-12 checklist says 20 of 43 cases are deterministic. |
| A-M13 | Fixed | `_KINDRED` and plurals, tested. See N-M4. |
| A-M14 | Fixed | `with_article`, tested. See N-M8. |
| A-M15 | Fixed | The docstring matches decision 1. |
| B-M1 | Fixed | "Replaced by the checked reply"; `tone` removed; older failed turns explained in words; ended turns stop fetching; limits keep their basis. |
| B-M2 | Fixed | Every send path is blocked while paused (`sendBlocked`, also passed to `SupportNotice`), and the ADR is corrected. |
| B-M3 | Fixed | "Choose a tone"; the false claim removed; "Help me explore instead" saves `unsure`. |
| B-M4 | Fixed | The select is named "…, per", and the hint says the floor is not applied yet. |
| B-M5 | Fixed | The capture waits for the sketch; three states side by side; the new `you--salary-floor` capture. |
| B-M6 | Fixed | e2e: V-02 recovers in place; "Add the details yourself" is hit-tested; focus plus Enter on Try again. |
| B-M7 | Fixed | Revoked key leads to the store form plus invalidation; the field is cleared only on success; revoke asks for confirmation; `new-password` plus ignore hints. Each is tested. |
| B-M8 | Fixed | `stillRunning`/`turnRunning`/`turnFailed` over `WorkState`. grep finds no hand-written status sets left. |
| B-M9 | Fixed | The question is hidden while support shows; the screened message is sent anyway (7f2a45b test); the date is formatted. |
| B-M10 | Fixed | `reviewable` looks at the newest turn with proposals only. Tested. |
| B-M11 | Fixed | The review names the commits. |

**A-M4 deferral.** Deferring is acceptable under H-12:
- The weakness is disclosed in ADR 0007 decision 5, the H-12 checklist and `sprint-2.md:247`.
- A weak query still gets one or more suggestions over the floor, because the floor is relative.
- Each suggestion shows the query that found it, so the person can see why it was suggested.
- An absolute `ts_rank` floor set without full-release calibration would be an unmeasured guess. The owner and next step are recorded, so this is not an untracked defect.

**A-M8 (what is saved).** The statement is literally true:
- The support path returns before `submit_run` and before any insert (`conversation.py:submit_turn`).
- `CommandResult(record=False)` (`routes_interview.py:86`, `receipts.py:68`) skips the receipt, so no message fingerprint is stored.
- No turn, run or event row is written.
- The integration test asserts the receipt count, event sequence, turn and run rows unchanged, and a leak scan of the database and logs for the message text.

**A-M10 (live-eval caps).** Per-scope caps:
- `SCOPE_MAX_CALLS = 9` (`live_eval.py:74`) is the settings default. It is tested by `test_a_scope_holds_one_default_run_within_the_controller_s_nine_requests`: a second default run in the same scope is refused.
- Requests per scope:

  | Scope | Rows | Requests | Cap |
  |---|---|---|---|
  | `live-eval` | 15-20 | 7 | 9 |
  | `live-eval-fix1` | 21-24 | 5 | 9 |

- The run used the named explicit command `NESSA_LIVE_EVAL_SCOPE=live-eval-fix1 make live-eval`, recorded in `sprint-2.md:165-167` and the report. The ledger markdown shows the scope column and the running totals.

Ledger arithmetic, recomputed from the jsonl:

| Row | Cost (nano-USD) |
|---|---|
| 21 | 607,100 |
| 22 | 234,200 |
| 23 | 303,700 |
| 24 | 178,800 |
| **Rows 21-24** | **1,323,800 = $0.0013238** (reported $0.001324) |
| **Running total** | **23,098,174 = $0.023098** |

- Each row equals tokens × the Contributor price (100 / 2 / 200 nano-USD per input / cached / output token, from `model_registry.py:56`). Example, row 21: 3,801 × 100 + 1,135 × 200 = 607,100.
- `live-eval.md` gives the worst case as $0.013500, which equals 3 × $0.0035 + $0.003.

**Commit 7f2a45b** is test-only (`e2e/visual.spec.ts`, `YouChapter.test.tsx`). Biome is clean, `tsc` exits 0 and the focused Vitest gives 15 passed. Commit cfdae68 touches docs only.

## New issues in the fix diff

### Critical
None.

### Important
None beyond the A-I-1 residual above. Those new misses are regressions introduced by this fix; I count them under A-I-1 so they are not listed twice.

### Minor
- **N-M1** (`routes_profile.py:74`, `commands.py:192`): `POST .../profile/revert` has no cross-account 404 test.
  - Every other new Task 6 write has one (`test_discovery.py`), and `test_isolation.py` lists none for it.
  - The code is correct: `visible_workspace` comes first, and RLS applies.
  - Fix: add it to the 404 sweep.
- **N-M2** (`document.py:136`, `SalaryField` `:162`, `store.py:36`): the new `> 0` validator also runs when stored documents are read.
  - A version saved with a £0 floor before this fix would no longer parse. Schema 3 accepted 0, and it is pre-release, so this affects dev or demo databases only.
  - Profile read, history, export and revert of that workspace would then fail with a 500.
  - Fix: validate on input only (`SalaryInput`), or state that no such data exists, or migrate it.
- **N-M3** (`slate.py:231-239`): alias-only folding still folds in one step pairs that ESCO links by an alternative label across ISCO minor groups.
  - My probe finds 154 such pairs, for example:
    - biologist ↔ bacteriology technician;
    - chemist ↔ biochemist;
    - baker ↔ pastry chef;
    - software developer ↔ application engineer.
  - This is the rule the reviewer proposed, and H-12 lists "alias-only folding". Consider also requiring the same ISCO minor group, or give H-12 the count.
- **N-M4** (`safety.py:185-200`, `_said` `:226-228`): kindred words relax the inference guard for every model text, interview replies included, not only discovery queries.
  - So a person who mentions clients ("mothers") lets a reply name "women" or "female" about the person.
  - Consider applying kindred words to discovery queries only.
- **N-M5** (`live_eval.py` `write_results`): the run header in `docs/evidence/live-eval.md` does not name the budget scope. The review and the ledger do. Print `scope` in the header.
- **N-M6** (`Conversation.tsx:203,237,305`): `focusQuestion` stays set if saving the entry choice fails, so focus can jump to the question heading at a later render. Reset it on error.
- **N-M7** (`interview.py:355`): the reply "?" rule applies even when `next_question` is null. Any "?" in a reply, rhetorical or quoted, costs a paid repair, and a second one fails the turn. Track the repair rate in the H-12 or release evaluation. INT-01 used its repair in the fix run; the cause is in the private outputs only.
- **N-M8** (`exploration.py:291-297`): `with_article("UX designer")` gives "an UX designer", because a leading "U" plus a capital is missing from `_VOWEL_SOUND`'s exceptions.
- **N-M9** (`exploration.py:469`): only the pure `release_note` is tested. The note's insertion into a computed slate is not.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** 35 of 37 findings are fixed with tests that would fail on the old behaviour, and the A-M4 deferral is acceptable. The ledger is exact, and undo, edits and resend now go through validated commands.

A-I-1 is only partly fixed. Tightening the distress screen also turned some explicit statements into misses: the exclusions are subject-blind and some lack word boundaries, and none of these misses is disclosed to the H-12 reviewer. That needs one targeted change, plus disclosure, before Sprint 2 closes.
