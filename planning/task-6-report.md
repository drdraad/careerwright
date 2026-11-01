# Task 6 report: Sprint 2 S2.3-S2.6 (conversation, grounded discovery, sketch, support policy, evaluation) and the Sprint 2 review

Branch `l0-local-release`, BASE `8a817f6`. Implementer agent, no subagents dispatched.

## Commits (mine only; the controller's b958de8, 19ebbe6, 00e4933, b59dfe3, 88aaad3, 04d6ba0 landed in between)

| SHA | Subject |
|---|---|
| `b51d2b7` | Run grounded discovery, interview preferences and the support policy |
| `5f7fca3` | Add the capped live evaluation and ledger its first run (rows 15-20) |
| `3cf48e6` | Build the You chapter: conversation, review tray, directions and key consent |
| `9564be9` | Test the You chapter in the browser and in Storybook; put What we know before directions |
| `96259d7` | Keep the phone reply field from covering Try again |
| `dec43e6` | Record Sprint 2: ADR 0007, the register, the runbook and the review |

## What was implemented

### Backend (`backend/src/nessa`)
- **Interview preferences** (`profile/preferences.py`, table `interview_preferences` with RLS,
  migration `r0010`): entry mode (sure/unsure), conversation mode (practical/gentle/challenge),
  paused; expected-version command, event `interview.preferences_updated`; `GET/PUT
  .../interview/preferences`. The prompt carries entry and mode (`interview-turn-2`).
- **Profile schema 3** (`profile/document.py`): optional `work_style` (REC1-01) and the
  product owner's **salary floor** `minimum_salary` = `SalaryFloor{amount: Money (integer
  GBP minor units), period: year|month|week|hour, basis: "gross"}`; a hard constraint
  (confirmation by name, PROF-04); Unknown/Skipped/Prefer not to say allowed, never 0;
  never annualised; schema 1/2 documents read both fields as not asked. The interviewer may
  propose it; the fixture interviewer reads stated pay with its period.
- **Support policy** (`profile/safety.py`, `support-policy-1`, provisional H-12): explicit
  acute-distress phrases get a fixed UK support response (999/A&E, NHS 111 mental-health
  option, Samaritans 116 123, Shout 85258; checked 2026-10-28) **before** any model call;
  nothing is sent or stored; `send_after_support: true` sends it anyway. Model output that
  infers a health condition, a type (MBTI etc.), a protected characteristic or a percentage
  the person never used is a validation problem (repaired, then refused); a named condition
  leads to an adjustments question and is never recorded in a career field.
- **Discovery** (`profile/discovery.py`, `discovery_agent.py`, `fixture_discovery.py`,
  `exploration.py`): a `discovery` run kind on the one activity, input sealed and pinned to
  the profile version; the model proposes up to 8 searches by channel, each quoting the
  person's confirmed answers (refused otherwise), never names a suggestion. ESCO full-text
  search (every-word, then any-word at weight 0.5) over the pinned release.
  `INSUFFICIENT_EVIDENCE` when no answer describes work.
- **Slate** (`profile/slate.py`, pure): pool by concept, near-identical folding (union-find
  over shared labels), pool cap 120, relevance floor 0.35, constrained greedy selection with
  channel weights, family limit 2, bonuses for new family/sector/less-familiar, soft target
  6; fewer with reasons; no percentage or score field; emphasis and exclusions are view
  parameters (`GET .../slate?emphasis=&exclude_concept=&exclude_family=`), never stored;
  "not included" counts. Explanations are deterministic text from facts.
- **Targets from suggestions** (`POST .../targets`): the only way a suggestion becomes a
  target, through the one write path with an `occupation_choice` source (ESCO URI,
  discovery ID, optional `replaces`).
- **Early sketch** (`profile/sketch.py`, `GET .../sketch`): calls `visible_workspace` first
  (security note); ESCO essential skills for a resolved target, choices for an ambiguous
  title, nearest occupations for a title ESCO lacks; every step `unresolved`; no provider,
  price or date.
- Export format 3 (discoveries, interview preferences); seed; worker fixture models;
  architecture adapter list. Client regenerated (`apps/web/src/generated/`).

### Evaluation and live tooling (`backend/tools`)
- `evaluation.py` + `evaluation_cases.json`: **39 reviewed synthetic cases** (INT-01..14,
  SUP-01..09, GRD-01..07, DSC-01..09) with semantic expectations and failure types; 25 run
  offline (unit + full-ESCO integration), 6 marked live.
- `live_eval.py` (`make live-eval`): test model only, synthetic only, at most 6 cases, one
  attempt per case, own ledger scope `live-eval` (24 requests, 0 production, $0.05 worst
  case), worker stopped before reading attempts, leak scan, results to
  `docs/evidence/live-eval.md` and outputs to `live-eval.jsonl`.

### Web (`apps/web`)
- **You chapter** (`YouChapter`, `Conversation`, `ReviewTray`, `WhatWeKnow`, `Directions`,
  `SketchCard`, `KeySetup`): sure/unsure entry, tone choice, pause/resume, one question
  displayed, streamed reply marked "not checked yet" until the checked reply replaces it
  (MODEL-03 UI), every completeness state mapped; review tray accept/edit/skip with limits
  confirmed by name; stale tray offers to resend; save and undo; What we know (facts vs
  inferences styled apart); "Edit answers directly" opens the form; Unknown/Skipped/Prefer
  answers; the salary floor input with period; the support response; directions with
  emphasis/exclusions as a view; "Make this a target"; the early sketch.
- **MODEL-07 consent** (`KeySetup`): what is stored, where, what for, revoke/rotate,
  `CREDENTIAL_REVOKED` handling; editing stays usable without a key.
- One filled primary per view (tested), `lastSeen` scoped per session and workspace.
- V-02 (Try again on failed profile load; strip names profile vs updates), V-07 (You leads
  with the first task), V-08 (strip states on their own row from 1180 px, height tested).
- S0-V01 (phone keeps a way into What we know: summary link at the top of the thread and the
  panel stacked after the conversation), S0-V02 (composer rides above the sheet's peek;
  scroll padding keeps scrolled/focused content above the sticky composer; Playwright
  `elementFromPoint` check at 390×844 for reply field, Send and Try again, sheet closed and
  open),
  S0-V05 (unknown-work heading claims no closeness), S0-V08 (one primary on You in every
  state).
- Playwright `conversation.spec.ts` (journey, support, V-08, phone), visual package
  (`review-screenshots` now writes `docs/reviews/sprint-2/screenshots/`, Sprint 2 states and
  the critique's coverage gaps), Storybook `Conversation.stories.tsx`.

### Docs
- New ADR 0007 (decisions 1-10, H-12 checklist); ADR 0006 status/decision 6/H-11 item
  updated for the salary floor; register rows (REC1-01..10, DIV1-02/04-12, TEST1-10,
  STATE-05/06/08, PROF-04/07/08/09, MODEL-03/07/09, UI-06, H-11, new H-12); runbook;
  CLAUDE.md (live-eval, layout, invariants); `sprint-1.md` dispositions for V-02/V-07/V-08
  only; `docs/reviews/sprint-2.md` (agent pre-review, six questions, coherence question,
  dispositions, human checklist); live evidence.

## Rulings (simplest reading that keeps every constraint)
1. **Model proposes searches, never suggestions.** A title reaches the slate only if ESCO
   holds it; this makes REC1-06/DIV1-04 structural rather than checked after the fact.
2. **Slate controls are view parameters, never profile state** (REC1-08, coherence
   question): recomputed per read; excluding a title keeps its family.
3. **Salary floor**: amount + period + gross, never annualised; discovery records but does
   not apply it (no pay evidence until T7) and says so (`SALARY_FLOOR_NOT_APPLIED`); unknown
   pay is never below the floor. Carried to T7 (carry-forward-task-7.md already lists it).
4. **Support response stores nothing** (no turn, no message) and offers "Send my message
   anyway": the least intrusive reading of "separately reviewed safety flow"; provisional,
   H-12.
5. **Live eval has its own scope and cap** (24 requests / $0.05) rather than spending the
   `live-smoke` scope, so the release task's production qualification keeps its budget.
6. **The sketch's "four practical inputs"**: the sketch is shown after a target and lists
   which minimum inputs are not asked yet instead of withholding itself, since the
   requirements part needs only the target.
7. **Roles (S0-V07 Roles part, S0-V08 failed Roles) are T8's**: no Roles map in Sprint 2.
8. **One-question check counts distinct questions** after the live run showed the reply
   repeating its question; the live failures stay recorded as they were counted.

## Checks run (final candidate)

All on the final code (`96259d7`; `dec43e6` changes docs only), run in sequence:
- `make check` → exit 0. Backend: `ruff format --check` 175 files already formatted; `ruff
  check` All checks passed; `mypy` no issues in 175 source files; `pytest` 373 passed, 178
  deselected; fixture validator `"status": "passed"`. Web (`pnpm run check`): client drift
  clean; Biome checked 108 files, no fixes; `tsc` clean; Vitest 24 files, 176 tests passed.
- `make acceptance` → exit 0. `pytest -m "integration or stack"` 178 passed, 373 deselected
  (4m30s) on PostgreSQL 16.15 + DBOS (incl. full ESCO import + offline evaluation,
  `test_discovery.py` 404 test for another account and a missing workspace); Storybook build
  completed; Playwright 21 passed (access ×5, conversation ×4, journey, keyboard ×4, session
  ×3, storybook axe, visual ×3).
  - The first `make acceptance` on the previous candidate (`9564be9`) failed 1 of 21:
    `visual 390x844: you--reply-failed--390x844.png: axe target-size` (the sticky composer
    covered Try again). Fixed in `96259d7` (RED/GREEN below), then the full sequence was
    rerun clean.
- `cd apps/web && pnpm run review-screenshots` → exit 0, 3 passed; 78 captures + 3
  `checks-*.json` in `docs/reviews/sprint-2/screenshots/`, 26 per viewport, 0 entries with
  axe violations, overflow, overprint, console errors or font failures (parsed).
- Agent pre-review of captures (`you`, `you--reply-failed`, `you--source-drawer`,
  `you--slate` at 390×844): findings 1-6 in `docs/reviews/sprint-2.md`.
- Stacks: every test stack is removed by its command; the `nessa-l0` dev stack is stopped
  (containers exited); no other project's containers touched.

## TDD evidence (RED then GREEN)
Written test-first, RED observed, then GREEN:
- `tests/domain/test_safety.py`, `test_slate.py`, `test_discovery_contract.py`: RED
  `ERROR tests/domain/test_<name>.py` at collection (modules absent) → GREEN.
- `tests/domain/test_interview_contract.py` inference guard: RED `8 failed, 29 passed`
  (`test_output_inferring_a_diagnosis_type_or_match_percentage_is_repaired[0-3]`,
  `test_a_named_condition_is_acknowledged_but_never_recorded_in_a_career_field`,
  `test_a_reason_or_value_inferring_a_trait_is_repaired_too`, prompt bounds, entry/mode
  prompt) → GREEN.
- `tests/domain/test_profile_document.py`: RED `ImportError: cannot import name
  'VERSION_3_FIELDS'`, then `3 failed, 26 passed` (version-2 document reads work style as not
  asked; salary floor gross with period, unknown never zero; hard-constraint set
  `[cities, target_titles, …(4)]` vs 3) → GREEN.
- `tests/domain/test_interview_agent.py::test_the_fixture_reads_an_amount_about_pay_as_a_salary_floor_with_its_period`: RED → GREEN.
- Phone composer covering Try again (found by the first final `make acceptance`: axe
  `target-size` on `you--reply-failed--390x844`): added `expectReachable(Try again)` with the
  sheet closed to `e2e/conversation.spec.ts`; RED `Expected: true, Received: false` at
  `conversation.spec.ts:225` (`elementFromPoint` hit the composer); fix: `scroll-padding-bottom`
  reserving the sticky composer (plus the sheet's peek when open) in `globals.css`; GREEN
  `7 passed` (conversation + visual specs).
- `tests/eval/test_evaluation.py::test_one_question_repeated_in_the_reply_counts_once_and_two_count_twice`: RED `1 failed` → GREEN.
- `src/lib/queries.test.tsx` lastSeen per session: RED `expected [ '2', '9' ] to deeply
  equal [ '2', '3' ]` (Ben resumed Ada's event 9) → GREEN.
- `src/lib/conversation.test.ts`: RED import (module absent) → GREEN.
- `src/components/Directions.test.tsx` no percentage: RED (`expected 'Directions to
  explore…' not to match`) → GREEN.

Written alongside or after the code (disclosed; not TDD): the integration tests (`test_discovery.py` incl. the 404 test for another account and a
missing workspace, `test_interview_choices.py`, `test_evaluation.py`,
`test_live_eval_ledger.py`), `tests/tools/test_live_eval.py`, most component tests
(`YouChapter`, `KeySetup`, `WorkspaceStrip`), the e2e and visual specs, Storybook stories.
Two integration tests failed on first run and caught real bugs: the salary floor missing
from `ProposedChangeOut.value`, and slate query parameters dropped by an empty `params={}`.

## Live calls (R5)
- `make live-eval` once, 2026-10-28 12:26 UTC, `muse-spark-1.3-contributor`, synthetic
  cases only, no production call: 6 cases, **7 requests** (INT-01 used its one validation
  repair), **$0.001574**; ledger rows 15-20. Running total of all live calls: **$0.021774**.
  Key leak scan clean.
- Results: DSC-01 pass; INT-01..03 fail `question` (as then counted); INT-04/05 fail
  `counterfactual_drift` (one sample per arm). Every other expectation of INT-01..03 passed.

## Blocked / not run
- **`next` 16.4.1 `minimumReleaseAgeExclude` removal: not done, blocked by time.** It
  becomes 14 days old at 2026-10-28T17:43Z; the task ended at 13:12Z. Steps for the next
  task: remove the exclusion from `apps/web/pnpm-workspace.yaml`; `cd apps/web && pnpm
  install --frozen-lockfile` (must succeed with an unchanged lock); update ADR 0005
  decision 1, `docs/dependencies.md` and the CLAUDE.md compatibility line. Listed in the
  Sprint 2 review's open items.
- Not run — requires human: H-01 Sprint 2 design scores, H-03 VoiceOver, H-04 Safari, H-05
  five-minute sketch target, H-12 support policy / inference lists / slate weights / eval
  cases. 200 % zoom not run.
- Live: INT-06..14, SUP, GRD and DSC-02..09 not run live (cap of 6); the counterfactual and
  one-question checks need a further budgeted run.
- Production model: not called (release task).
- Not taken (coordinator): V-01, V-03-V-06, V-09, V-10; H-01 "phone sheet peek lacks route
  name and figures" is V-04 in the visual batch.

## Concerns
1. **Live model quality unproven** on one-question (outputs of the failing run were not
   retained, so repeated vs. two questions is unknown) and on demographic counterfactuals
   (REC1-09 recorded `failed`). Needs a larger live budget.
2. **DIV1-08** baselines (relevance-only, common careers), exposure concentration and
   long-tail coverage are not measured yet (row left open).
3. Phone slate cards are long (one per screen); ESCO skills shown alphabetically (review
   findings 1-2).
4. **Process slips** (against the Edit/Write-only rule): one empty heredoc append to
   `interview_store.py` (no content change, verified with `git diff`), two no-op `sed …
   /dev/null` commands, `touch tests/eval/__init__.py` (empty file), commit messages passed
   by heredoc. No source content was changed by shell.
5. Sprint 2 review is an agent pre-review by the implementer, not independent.
6. The composer's scroll reserve is a fixed 96px; a reply field the person resizes taller
   (`resize: vertical`) can again cover the last item scrolled into view.

## Generated or vendored paths to skip
- `apps/web/src/generated/` (hey-api client and `openapi.json`)
- `docs/reviews/sprint-2/screenshots/` (PNGs and `checks-*.json`)
- `docs/evidence/live-usage.jsonl` (ledger data; `live-eval.jsonl` is written by the next
  live run, none exists yet)
- `backend/tools/evaluation_cases.json` is data but reviewed content (H-12): do read it.

---

# Fix round 1 (FIX_BASE dec43e6)

Fix list: `task-6-fix-round-1.md`; findings `task-6-review-A.md` (backend) and
`task-6-review-B.md` (web and docs). Every must-fix and cheap item is addressed below,
except A-M4 (recorded, not changed: see its row).

## Commits

| SHA | Subject |
|---|---|
| `e713992` | Fix the Task 6 backend findings: support screen, slate, sketch, salary, eval |
| `c774cf3` | Fix the Task 6 web findings: tray edits, resend, undo, announcements, keys |
| `7527c0d` | Test recovery in place, keyboard reach on a phone and the salary captures |
| `5651c23` | Ledger the fix-round live evaluation (rows 21-24) and keep home paths out |
| `7f2a45b` | Test that "send anyway" sends the screened message, and format the capture |
| `cfdae68` | Record fix round 1: ADR 0007, the register, the runbook and the review |

## Per finding: change, covering test, RED then GREEN

Commands: backend `cd backend && uv run --locked pytest <file> -q` (integration with
`-m integration`); web `cd apps/web && pnpm exec vitest run <file>`; e2e `pnpm exec
playwright test <spec>`.

### Backend, Important
- **A-I-1 distress false positives.** `safety.py`: each phrase needs its meaning (an object
  that is the person's life, or the end of the clause; career-context words after
  "suicide"/"self-harm"; "kill myself with/over…" is a figure of speech). Added the
  reviewer's 5 sentences plus 3 more as negatives, 5 more positives ("wanna die", "hurt
  myself" with intent, "live anymore", "no reason to go on.", "end it all");
  SUP-09 now expects no support; SUP-10..13 added (43 cases). Test
  `tests/domain/test_safety.py`: RED `9 failed, 22 passed` → GREEN `31 passed`.
- **A-I-2 transitive folding.** `slate.py`: fold only when one occupation's preferred key is
  a label of the other (or equal label sets), comparing each candidate with group leads
  only; `Occupation`/`OccupationFacts` gain `preferred_key` (SQL `nessa.concept_key`).
  Test `test_slate.py::test_folding_never_chains_unrelated_work_through_shared_labels`
  (ESCO's own quarry engineer/quarry manager/mine manager/building caretaker/building
  cleaner labels): RED (all five in one group) → GREEN.
- **A-I-3 sketch re-resolution.** `sketch.py` resolves a target first by the person's
  `occupation_choice` (ESCO URI → concept in the held release: `store.chosen_occupation_uris`,
  `taxonomy_store.concepts_by_uri`), then by labels. Test
  `test_discovery.py::test_the_sketch_uses_the_occupation_the_person_chose_even_when_its_title_is_shared`
  (adds a shared alternative label to the sample and removes it, as `test_taxonomy.py`
  does): RED `assert 'ambiguous' == 'esco'` → GREEN `2 passed` (with the existing sketch test).
- **A-I-4 salary period.** `interview.py::_basis`: `stated` only if the proposal names a
  period and a cited message has that period's words (`_PERIOD_WORDS`); a bare amount is
  `inferred`. Fixture: `_PAY` no longer counts "a year"/"pay"; `_SPEND` words make it a
  limit; week added. Tests `test_interview_contract.py::test_a_salary_floor_is_stated_only_when_the_cited_words_give_its_period`,
  `test_interview_agent.py::test_the_fixture_reads_an_amount_about_pay_as_a_salary_floor_with_its_period`
  (£500 a week; £1,500 a year on courses): RED (`STATED is INFERRED`, `500 per year`) → GREEN.
- **A-I-5 family sampling.** `slate.py::_across_families`: the 120-pool is filled
  round-robin across ISCO minor groups in relevance order. Test
  `test_slate.py::test_the_bounded_pool_samples_across_families_before_relevance_cuts_it`:
  RED `{'723'} == {'621','723','752'}` → GREEN. Oversampling recorded as not done
  (DIV1-10 row now "planned for oversampling").
- **A-I-6 eval robustness.** Contract: the question lives only in `next_question` (one `?`),
  the reply has none (`interview-turn-3`; instructions say so; the demo interviewer no longer
  repeats it). Checker: `one_question` per field (plus a joined second ask), `_has` matches
  word starts (`whole_words` for INT-04/05), `same_fields_as` compares only listed
  unambiguous fields; INT-04/05 out of the default live set; outputs to the private
  evidence directory (`NESSA_HOME/evidence/live-eval.jsonl`, 0700). REC1-09 →
  "inconclusive (one sample per arm)". Tests: `test_interview_contract.py::test_the_one_question_lives_only_in_next_question_never_in_the_reply`,
  `tests/eval/test_evaluation.py` (3 new tests): RED `4 failed, 63 passed` → GREEN;
  `test_live_eval_ledger.py` (private path, not committed, 0700): written with the code, no
  RED observed (disclosed).

### Backend, Minor
- **A-M1** 404 test now posts a real `concept_id` from the slate (test-only; passed, code was right).
- **A-M2** `test_discovery.py::test_a_discovery_invalid_after_its_repair_fails_typed_and_has_no_slate`
  (2 requests, `invalid_model_output`, slate 409 `PROPOSAL_NOT_AVAILABLE`, no leak): passed
  first run (coverage). No non-synthetic Standard-only discovery test added (the mechanism
  is kind-independent; noted).
- **A-M3** `test_evaluation.py` asserts P02's pool is exactly `POOL_LIMIT` with overflow:
  passed (`DSC-01: pool 120`).
- **A-M4** not changed: an absolute rank floor needs calibration on the full release;
  recorded in ADR 0007 decision 5, the H-12 checklist and the review's open items.
- **A-M5** `sketch.py` re-raises any search error but `no_search_terms` (covered by the
  existing sketch tests; no new test).
- **A-M6** an unsearchable current role goes to `unsearchable_queries`. Test
  `test_a_current_role_with_no_searchable_word_is_reported_never_a_search_that_found_nothing`:
  RED (`'Of the'` listed as a query) → GREEN.
- **A-M7** `SalaryFloor.amount` must be > 0; the contract refuses "0 per year". Tests in
  `test_profile_document.py` (`DID NOT RAISE` → raises) and
  `test_interview_contract.py::test_a_proposed_salary_floor_of_nothing_is_refused`: RED → GREEN.
- **A-M8** the support response leaves no idempotency receipt (`CommandResult.record=False`),
  so "nothing has been saved" is true. Test `test_interview_choices.py` (receipt count
  unchanged): RED `{'count': 4} != {'count': 3}` → GREEN.
- **A-M9** `DiscoveryInput.release`/`DiscoveryProposal.release` record the held release;
  `release_note` says when a slate is read against another. Test
  `test_discovery_contract.py::test_the_searches_record_the_release_they_were_chosen_for_and_a_change_is_said`:
  RED (import error) → GREEN.
- **A-M10** `SCOPE_MAX_CALLS = 9` (controller's per-scope cap); the default live run is 4
  cases (8 requests) so one fits a scope; the re-run used its own scope. Tests
  `tests/tools/test_live_eval.py` (2 new): RED (import error) → GREEN `45 passed`.
- **A-M11** $0.001575 (rounded; $0.00157486) in register and review.
- **A-M12** ADR 0007 H-12 checklist: 20 of 43 cases are deterministic; model behaviour rests
  on single live samples.
- **A-M13** kindred words (`_KINDRED`) and plurals count as the person's own words. Test
  `test_safety.py::test_a_group_the_person_named_may_be_named_in_their_own_or_a_kindred_word`:
  RED `['women'] == []` → GREEN.
- **A-M14** `with_article` ("an administrative assistant"). Test in
  `test_discovery_contract.py`: RED (import error) → GREEN.
- **A-M15** `preferences.py` docstring matches decision 1.

### Backend for B-I1 and B-I3
- `DecideTurn.edits: [FieldEdit{field, answer}]`: each a proposed field, once, not also
  accepted, validated like a direct edit (`invalid_answer`), saved as one direct-entry
  source in the same version as the accepted proposals. `POST .../profile/revert`
  (`RevertProfile{expected_version, to_version}`) restores an earlier version citing each
  answer's own source (`ExistingSource`; `commit_profile_version` records only new
  sources). Client regenerated. Tests `test_interview_turns.py::test_a_decision_saves_the_person_s_edits_with_the_accepted_ones_as_one_version`,
  `test_undo_restores_the_earlier_answers_with_their_own_sources_as_a_new_version`: RED
  (`KeyError: 'reason'`; revert `404`) → GREEN `3 passed`.

### Web
- **B-I1** tray edits validated before the decision (`readField`), errors shown with
  `FieldError`, a state selector, an Unknown proposal starts answerable, edits sent in the
  one decision, an unchanged edit sent as an acceptance; a failed save keeps the drafts.
- **B-I2** one send path (`useSendMessage`): errors and support shown; "Send it again"
  disabled while paused, without a key, sending or replying; a stale tray hides once a
  newer message exists.
- **B-I3** undo uses `useRevertProfile` (`to_version = saved - 1`).
- **B-I4** one mounted live region (`you-announcer`): each new checked reply ("Nessa
  replied: N changes to review."), not on load; save and undo announced; focus to the first
  question after the entry and to "What we know" after save/undo.
- **B-I5** MODEL-03: the latest failed turn shows its streamed text marked "Stopped: not
  checked, nothing saved"; register rows MODEL-03/STATE-06/MODEL-07/UI-06/S0-V08 now cite
  existing tests (or narrowed).
- Tests: `src/components/YouChapter.test.tsx`: RED `10 failed | 5 passed` → GREEN `15
  passed`; `src/lib/conversation.test.ts`: RED `4 failed | 5 passed` → GREEN `9 passed`;
  `src/components/KeySetup.test.tsx`: RED `3 failed | 1 passed` → GREEN `4 passed`. Of the
  YouChapter REDs, "keeps the edit and says why when saving fails" first failed on a wrong
  error code in the test itself; with the old code it would likely have passed (the old
  tray also kept drafts when the decision failed): it is a regression guard, not a RED.
  The B-M9 "send anyway sends the screened message" assertions were added after the code
  (no RED).
- **B-M1** superseded labelled "Replaced by the checked reply"; `tone` removed; an older
  failed turn says "No reply: <reason>. Nothing was saved." in words; ended turns stop
  fetching replies (only running turns and the latest failed one); limits keep the
  stated/inferred wording.
- **B-M2** every send path blocked while paused; ADR 0007 decision 1 corrected (composer
  stays, Send disabled).
- **B-M3** "Choose a tone" until chosen; "You can change this later" removed; "Help me
  explore instead" saves `entry_mode: unsure`.
- **B-M4** period select named "Lowest pay you'd accept, per"; hint says recorded, not applied.
- **B-M5** `you` waits for the sketch; `you--answer-states` shows the three states side by
  side; new `you--salary-floor`.
- **B-M6** e2e: V-02 recovers in place; "Add the details yourself" hit-tested, sheet open
  and closed; focus alone brings Try again into view and Enter sends it (written with the
  feature in place; passed first run).
- **B-M7** revoked key → store form + credentials invalidated; key cleared only on success;
  revoke confirmation; `autocomplete=new-password` + password-manager ignore hints + copy.
- **B-M8** `stillRunning`/`turnRunning`/`turnFailed` over the generated `WorkState`; no
  hand-written status sets remain.
- **B-M9** support: question hidden while shown; screened message sent anyway; date
  formatted.
- **B-M10** `reviewable` looks only at the newest turn with proposals.
- **B-M11** review names the reviewed commits.

## Live calls (R5)
- One re-run, as allowed: `NESSA_LIVE_EVAL_SCOPE=live-eval-fix1 make live-eval`, 2026-10-28
  14:08 UTC, `muse-spark-1.3-contributor`, synthetic, no production call. 4 cases
  (INT-01..03, DSC-01), 4 attempts, 5 requests (INT-01 used its repair), **$0.001324**
  (rows 21-24). **All four passed.** Running total of all live calls **$0.023098**. Leak
  scan clean. Outputs in `NESSA_HOME/evidence/live-eval.jsonl` (private). The run wrote my
  absolute home path into `live-eval.md`; I changed the tool to write `NESSA_HOME/...` and
  edited that one line of the results file to match (disclosed).
- Observation: two of three live questions came back without a "?" (allowed by the
  contract; shown as written). Noted for H-12.
- Powered counterfactual comparison (deferred to the release task): e.g. 10 samples per
  arm × 2 arms = 20 interview attempts, ≤ 40 requests; expected ≈ 20 × $0.0003-0.0006 ≈
  $0.006-0.012, worst case 20 × $0.0035 = **$0.07**; it needs a scope cap above 9 requests
  (a controller decision).

## Checks (final code)

- Backend integration suite while fixing: `uv run --locked pytest -m integration -q` →
  `167 passed, 416 deselected` (before the last integration tests were added).
- `make check` (after `5651c23` plus the format fix) → exit 0: ruff format 175 files
  formatted, ruff check passed, mypy clean (175), pytest `400 passed, 183 deselected`,
  fixture validator passed; web client drift clean, Biome 108 files, `tsc`, Vitest `24
  files, 190 tests passed`. (The first `make check` attempt failed Biome formatting of
  `e2e/visual.spec.ts`; fixed, rerun clean.) After the test-only commit `7f2a45b`: Biome,
  `tsc` and Vitest rerun → `190 passed`.
- `make acceptance` → exit 0: `183 passed, 400 deselected` integration and stack tests
  (5m09s), Storybook build completed, Playwright `22 passed` (incl. V-02 recovery, the phone
  reachability and keyboard checks, visual ×3).
- `cd apps/web && pnpm run review-screenshots` → exit 0, `3 passed`; 81 captures + 3
  `checks-*.json`, 27 per viewport, 0 entries with axe, overflow, overprint, console or font
  failures (parsed).
- Stacks: test stacks removed by their commands; the live smoke stack, volumes and keys
  removed; no `nessa` container running; no other project's containers touched.

## Not done / concerns
- `next` 16.4.1 age exception: still time-blocked (fix round ended about 14:20Z; allowed
  after 17:43Z). Steps unchanged (above).
- Process: commit messages again went to git by stdin heredoc (no file written); every
  source change used Edit/Write, and formatting used the project's formatters (`ruff
  format`, `biome format --write` on my files only).
- A-M4 absolute relevance floor: not set (calibration needed; H-12).
- No non-synthetic, Standard-only discovery test (A-M2 second half).
- The composer's 96px scroll reserve is fixed (a person who enlarges the field can again
  cover the last item scrolled into view).
- Human gates unchanged: H-01 (Sprint 2), H-03, H-04, H-05, H-12 not run — requires human.

---

# Fix round 2 (FIX_BASE cfdae68)

Re-review: `task-6-rereview-1.md` (35 fixed, A-M4 deferral accepted, A-I-1 partial; new
N-M1..N-M9). Controller ruling for A-I-1: a two-tier screen.

## Commits

| SHA | Subject |
|---|---|
| `e777cf3` | Screen distress in two tiers and fix the re-review's backend findings |
| `8dde3e6` | Show the support note beside a sent message; keep focus on a failed choice |
| `0d1dd75` | Record fix round 2: the two-tier support screen and the re-review fixes |

## Per finding: change, covering test, RED then GREEN

- **A-I-1 two-tier screen** (`safety.py`, `support-policy-2`). Tier 1 (`_ACUTE`): an intent
  phrase + an act; "I feel/I'm/I've been suicidal"; "I self-harm", "I've been/keep
  harming myself"; "I've been/keep hurting|cutting myself"; "take my own life"; "wish I
  was dead"; "better off dead/without me"; "don't want to be alive"; "don't want to live
  (like this)(any more)", "no reason to live/go on" and "can't go on" at a clause end.
  Positive evidence only: no word-after exclusions remain. Tier 2 (`_RISK`): any risk word
  or phrase, whatever follows. `submit_turn` blocks tier 1 only (200 support response, not
  sent, no receipt); otherwise 202 `TurnSubmittedOut` with `support_note` (tier 2, or tier
  1 sent anyway), never stored. Web shows the note beside the conversation, dismissible.
  Tests:
  - `tests/domain/test_safety.py` (ACUTE 18 incl. the 6 missed shapes, MENTION 11 incl. the
    8 earlier career false positives and 3 missed shapes, ORDINARY 6): RED collection
    error (`SupportTier` absent) → GREEN `41 passed`.
  - `test_interview_choices.py::test_any_other_risk_word_is_sent_as_usual_with_a_support_note`:
    RED `assert 200 == 202` (blocked) → GREEN `4 passed`.
  - `tests/eval`: SUP-06/09..13 gain `support_note` expectations; RED `5 failed, 21 passed`
    → GREEN.
  - `YouChapter.test.tsx` "any other risk word is sent as usual…": RED (no note region) →
    GREEN.
  - Known limits listed in ADR 0007 decision 7 and the H-12 checklist.
- **N-M1** revert added to the cross-account/missing-workspace 404 sweep (test-only; passed:
  the code was right).
- **N-M2** `> 0` moved from `SalaryFloor` to `SalaryInput`; revert of a stored £0 floor
  refuses with `VALIDATION_FAILED`/`no_longer_valid` instead of a 500. Test
  `test_profile_document.py::test_a_stored_floor_of_nothing_from_before_the_rule_still_reads`:
  RED (ValidationError on read) → GREEN. The revert refusal path is not tested (needs a
  hand-inserted legacy version).
- **N-M3** `_aliases` requires the same `family_code`. Test
  `test_slate.py::test_an_alias_from_another_kind_of_work_is_not_a_duplicate`: RED
  (biochemist folded into chemist) → GREEN; the chain test now expects no cross-family fold
  (quarry manager still folds into mine manager, both ISCO 132, per ESCO's labels) and
  adds a within-family chain case. H-12 count, from a scratch probe over ESCO v1.2.1
  `occupations_en.csv` with a Python approximation of `nessa.concept_key` (preferred and
  alternative labels): 319 alias pairs, 155 across minor groups (no longer fold), 164
  within one (still fold, e.g. physiotherapist ↔ occupational therapist).
- **N-M4** `inferred_sensitive_terms(..., kindred=False)` by default; discovery passes
  `kindred=True`. Test `test_safety.py::test_a_search_may_name_who_the_work_serves_in_a_kindred_word_but_a_reply_may_not`:
  RED (TypeError: no `kindred`) → GREEN; `test_discovery_contract.py::test_a_search_may_name_who_the_work_serves_in_a_kindred_word`
  passed both before and after (guard).
- **N-M5** `write_results` header names the scope. Test: `test_live_eval_ledger.py`
  asserts ``scope `eval-test` ``; written with the code, RED not observed.
- **N-M6** `save(..., onError)` resets `focusQuestion`. Test `YouChapter.test.tsx` "does not
  move focus later if saving the choice failed": RED (`not.toHaveFocus` failed) → GREEN.
- **N-M7** the reply "?" rule applies only beside a `next_question`; the checker lets a
  reply with no next question hold one question. Tests: `test_interview_contract.py`
  (reply "?" with `next_question=None` → no problems): RED → GREEN; eval test additions
  pass. Repair rate added to the H-12 checklist.
- **N-M8** "U" + capital is said "you". `test_discovery_contract.py`: RED → GREEN.
- **N-M9** `observe_discovery_offline(..., release=...)`;
  `test_discovery.py::test_a_slate_read_against_another_release_than_its_searches_says_so`
  over the sample release: written with the change, RED not observed; passed.
- Visual: new `you--support-note` capture (its own browser context; the send is answered
  in the browser so the scratch conversation is unchanged).

## Live calls
None this round.

## Checks (final code)

Run once, after the last code commit (`8dde3e6`):
- `make check` → exit 0: ruff format 175 files formatted, ruff check passed, mypy clean
  (175), pytest `412 passed, 185 deselected`, fixture validator passed; client drift clean,
  Biome 108 files, `tsc`, Vitest `24 files, 192 tests passed`.
- `make acceptance` → exit 0: `185 passed, 412 deselected` integration and stack (4m49s),
  Storybook build completed, Playwright `22 passed`.
- `cd apps/web && pnpm run review-screenshots` → exit 0, `3 passed`; 84 captures + 3
  `checks-*.json` (28 per viewport), 0 entries with axe, overflow, overprint, console or
  font failures (parsed).
- While fixing: backend integration suite `169 passed` (before the last integration-test
  additions were counted in acceptance); conversation + visual e2e `8 passed`.
- Stacks: all test stacks removed; no `nessa` container running; no other project's
  containers touched.

## Not done / concerns
- `next` 16.4.1 age exception: still time-blocked (round ended before 17:43Z).
- The tier lists are provisional (H-12); tier 2 shows the note on some career phrases.
- N-M2's revert refusal and a legacy £0 version are not exercised by a test.
- Process: the N-M3 count probe was a scratch script written by shell heredoc into the
  scratchpad (not a source file); commit messages went to git on stdin.

---

# Fix round 3 (FIX_BASE 0d1dd75)

Re-review 2: `task-6-rereview-2.md` (N-M1..N-M9 fixed; A-I-1 partial with I-1..I-4; minors
M-1..M-4). Controller ruling: tier 2 a broad stem screen (every inflection; nothing with
a stem reaches no tier); tier 1 narrow (first-person present intent only); one
table-driven corpus; the receipt without the note; the note announced politely.

## Commits

| SHA | Subject |
|---|---|
| `561c97f` | Narrow tier 1, widen tier 2, and keep the support note out of storage |
| `6b1d3b9` | Record fix round 3: the narrowed screen, the never-stored note |

## Per finding: change, covering test, RED then GREEN

- **Corpus** (`tests/domain/test_safety.py::CORPUS`, one parametrised test, 56 rows: shape,
  example, expected tier). Rows: every earlier tier-1 case; the reviewer's I-1 career
  phrasings (helpline, youth worker, "going to die" about a high street or print, "die of
  boredom", "die on this hill", "thinking about/of suicide prevention", "I have self-harm
  awareness training", "kept/have been cutting/hurting myself" at work) as tier 2; the
  I-2 inflections ("was cutting myself", "cannot"/"can not go on", "taken my life
  savings", "wanting to die") as tier 2; M-2 pairs; the ordinary cases as none. Example
  text is minimal and workplace-framed (56 rows: 21 tier 1, 29 tier 2, 6 none). RED:
  `18 failed, 42 passed` (12 reached tier 1 wrongly, 5 reached no tier, 1 reached tier 2
  instead of 1). GREEN after the change: `62 passed` (two more rows added for SUP-02 and
  SUP-04 shapes, "I've felt suicidal" and "I keep thinking about", which the narrowed
  tier 1 first missed: caught by `tests/eval`, RED `2 failed`, then GREEN).
- **I-1 tier 1 narrow** (`safety.py::_ACUTE`): each branch starts from "I" (or "me");
  intent + act needs the subject; `die` only at a clause end; `suicide`/`dying` removed
  from the acts; "suicidal" needs "I feel/I'm/I've been/I've felt"; self-harm needs "I
  self-harm" or a present/progressive form; hurting/cutting myself only in a present form
  at a clause end; "no reason to go on" and "can't go on" need "I". "There's no reason to
  go on." (no subject) moved from tier 1 to tier 2 by the ruling.
- **I-2 tier 2 broad** (`_RISK`): `cut(?:s|ting)?`, `cannot|can not|couldn't`, `taken`,
  `wanting/wants/going/ready/plan…/tempted/try…/intend… to die`, `doesn't/didn't want to`.
- **M-2** "don't" and "do not" share one branch; "be here" in tier 1 needs "any more" (the
  bare "I don't want to be here" is tier 2, listed for H-12).
- **I-3 receipt** (`routes_interview.py`, `conversation.support_note_for`): the receipt
  records `TurnOut` only; the route adds `support_note` from `screen_message(body.message)`
  on every 202, fresh or replayed. Test `test_interview_choices.py::test_any_other_risk_word_is_sent_as_usual_with_a_support_note`
  now asserts no receipt row for the workspace contains "risk_mention" or "support", and
  that a replay with the same key returns the same turn and the same note. RED: the
  receipt held `"support_note"` → GREEN `4 passed`. (A first RED was the policy version
  assertion, bumped to `support-policy-3`.)
- **I-4 announcement** (`Conversation.tsx`): a new note calls `announce("Your message was
  sent. Support information is shown above the reply field.")` once per note (the polite
  `role="status"` region); focus is not moved. **M-1**: dismiss focuses the reply field.
  Test `YouChapter.test.tsx` "any other risk word…": RED (announcer text missing) →
  GREEN; it also asserts focus stays on Send after sending and moves to the reply field on
  dismiss.
- **M-3** `commands.restored_answers` (extracted from `revert_profile`) refuses a stored
  £0 floor with `no_longer_valid`. Test in
  `test_profile_document.py::test_a_stored_floor_of_nothing_from_before_the_rule_still_reads`:
  RED (import error) → GREEN `30 passed`.
- **M-4** `Conversation.tsx` header describes the two tiers.
- Docs: ADR 0007 decision 7 rewritten from the corpus (tiers, the never-stored note,
  announcement, known limits); H-12 checklist; register PROF-09; runbook; Sprint 2 review.
  Client regenerated (a schema description changed).

## Live calls
None this round.

## Checks (final code)

Run once, after the last code commit (`561c97f`):
- `make check` → exit 0: ruff format 175 files formatted, ruff check passed, mypy clean
  (175), pytest `433 passed, 185 deselected`, fixture validator passed; client drift clean,
  Biome 108 files, `tsc`, Vitest `24 files, 192 tests passed`.
- `make acceptance` → exit 0: `185 passed, 433 deselected` integration and stack (4m40s),
  Storybook build completed, Playwright `22 passed`.
- `cd apps/web && pnpm run review-screenshots` → exit 0, `3 passed`; 84 captures + 3
  `checks-*.json` (28 per viewport), 0 entries with axe, overflow, overprint, console or
  font failures (parsed).
- Stacks: all test stacks removed; no `nessa` container running; no other project's
  containers touched.

## Not done / concerns
- `next` 16.4.1 age exception: still time-blocked (round ended at 15:25Z; allowed after
  17:43Z).
- The stem list is finite and English (H-12); tier 2 shows the note on some career phrases.

# Fix round 4 (FIX_BASE 6b1d3b9): support screen redesign

Requirements: `task-6-fix-round-4.md` (controller ruling: remove the intent classifier;
one recall-first screen). Re-review 3 (C-1, N-I1, N-I2, M-a, M-b, M-c) is answered by the
redesign rather than by patching the tiers.

## Commits

| SHA | Subject |
|---|---|
| `16ee339` | Replace the two-tier support screen with one recall-first screen |
| `b608e7d` | Record the one-screen support policy: ADR 0007, register, runbook, review |

## Rulings

- **R4-1 Where the per-turn instruction goes.** In the turn's *instructions*
  (`interview.instructions(context)`), not in the context JSON: the context the model
  reads is byte-for-byte the same shape for a flagged and an ordinary turn (no key, no
  label), and it is recomputed from the sealed current message for every request (first
  and repair), so nothing about the screen is sealed or stored. pydantic-ai strips
  trailing whitespace from instructions, so the constant is bare text and is appended with
  newlines. The fixture interviewer and the test fake read it from `AgentInfo.instructions`
  (what the model receives), never by re-running the screen.
- **R4-2 Instruction wording.** Required parts: acknowledge briefly, offer a smaller next
  step, ask no career question (`next_question` null). Added: "Give no phone numbers and
  name no services", because the panel carries the checked services and spec section 4
  forbids fabricated emergency details. It names neither the screen nor the stem (tested).
  The model's reply is not validated for a career question (as for the existing overwhelm
  instruction); listed for H-12.
- **R4-3 Stem list.** The union of the round-3 vocabularies (both tiers) plus the C-1
  shapes (gerund `dying` after think/thought(s) about/of; intents decide, urge, try in all
  forms; an adverb slot), with every person (reflexives, possessives, pronouns, per the
  ruling's "any person") and every negation (contracted, uncontracted, apostrophe-less,
  curly, never, no longer). No new families were added: wording such as "end it", "carry
  on", "not exist" or method words is listed in H-12 for the reviewer to decide.
- **R4-4 The panel.** One panel replaces both tier-1 response and tier-2 note, with the
  existing reviewed note wording and resources; it now also shows the date the services
  were checked (carried over from the removed tier-1 alert). API field name `support_note`
  and schema `SupportNoteOut` kept (contract continuity); its `policy` field is removed
  (one flow, nothing to distinguish). `POLICY_VERSION` is `support-policy-4`, the prompt
  `interview-turn-4`.
- **R4-5 The question steps aside while the panel is shown** (as the tier-1 alert did):
  the web app's reading of "no career question this turn" for the earlier turn's question
  still on screen. Dismissing the panel brings it back if the reply has not replaced it.
- **R4-6 Old receipts (item 7).** Removing `send_after_support` changes every
  `submit_turn` fingerprint, so a receipt stored by any earlier round can never match a
  request again: the same key is refused with the existing `422 IDEMPOTENCY_KEY_REUSED`, and
  an old client still sending the field gets `422 VALIDATION_FAILED`. Neither is a 500
  (tested), so no tolerant read (it would be unreachable) and no migration. Residue: round
  0-2 receipts on a developer's local database may still hold old support text
  (pre-release local data; deleted with their workspace).
- **R4-7 `CommandResult.record` removed.** It was added in fix round 1 only for the
  tier-1 response (`git log -S`), so it is orphaned by removing tier 1.

## Per required-design item: change, covering test, command, output

1. **One recall-first screen.** `safety.py`: `_ACUTE`, `SupportTier`, `SupportConcern`,
   `screen_message`, `SUPPORT_MESSAGE` removed; `_RISK` rebuilt as one alternation per stem
   family with its own `\b` (so "lifeguard", "lifelong", "lifestyle", "meetings" never
   match, and "self-esteem" is excluded from the reflexive); `has_risk_stem(message)`.
   Test `tests/domain/test_safety.py::test_any_listed_stem_triggers_the_support_flow_and_nothing_else_does`
   (one table, 692 rows: 636 generated stem × inflection/person/tense/negation forms, 36
   sentences with a stem (the round 1-3 corpus rows and the re-review 3 career probes), 20
   no-stem career and figurative messages; each row also checked inside surrounding text).
   - RED (the new table against the round-3 screen, "any tier" counted as the flow, in a
     scratch copy): `537 failed, 155 passed`. By family: end/take + a life 234 (other
     persons, "lives"), reflexive 126 (other persons), intent + die 62 (C-1: decide, urge,
     tries/tried, adverb slot), wish + dead 46, not want to live 36 (N-I2: does not / did
     not / won't / never / no longer), thinking about/of + dying 20 (C-1), better off without
     + other persons 5, "could not go on" (N-I2), the three N-I2 career probes, and four
     rows flagged with no stem (N-I1: lifeguard, lifelong, lifestyle, without meetings).
     In-repo RED: `ImportError: cannot import name 'has_risk_stem'`.
   - GREEN: `cd backend && uv run --locked pytest tests/domain/test_safety.py -q` →
     `698 passed`.
2. **The support flow, message proceeds.** `conversation.submit_turn` always creates the
   turn (`SupportShown`, `send_after_support`, `support_note_for` removed); the route always
   answers 202 and adds `TurnSubmittedOut.sent(turn, support=has_risk_stem(body.message))`
   (the 200 response and `SupportResponseOut` removed). Web: `useSendMessage` keeps only the
   panel; `SupportNotice` and "Send my message to Nessa anyway" removed; `SupportNote`
   shows the checked date; the question hides while the panel shows.
   - Tests: `YouChapter.test.tsx` "[PROF-09] a message with a risk stem is sent as usual,
     with the support panel" (one POST with exactly `{expected_profile_version, message}`,
     reply field cleared, panel is a region not an alert, services and checked date shown,
     question steps aside, polite announcement, focus stays on Send, dismiss returns focus
     to the reply field); the stale-tray "Send it again" test now shows the panel the API
     sends; `e2e/conversation.spec.ts` "[PROF-09] a message with a risk stem is sent as
     usual, with the support panel and a smaller step" (demo stack: the message appears as
     sent, the panel shows the services, the demo interviewer's reply is the smaller step,
     no question after dismissing, focus on the reply field).
   - RED (new Vitest file against the HEAD web code, `queries.ts` stashed): `1 failed | 15
     passed` (`expected [ { …(3) } ] to deeply equal [ { …(2) } ]`: HEAD still sent
     `send_after_support`). GREEN: `pnpm exec vitest run src/components/YouChapter.test.tsx`
     → `16 passed`.
3. **The turn instruction, that turn only, no label.** `safety.SUPPORT_TURN_INSTRUCTION`;
   `interview.instructions(context)` appends it only when the *current* message has a stem;
   `prompt_bytes` counts it; `run_interview_turn` passes it as the agent's instructions; the
   fixture interviewer follows it (`fixture_turn(..., smaller_step=...)`: no question, a
   smaller-step reply, proposals as usual); `PROMPT_VERSION = "interview-turn-4"`.
   - Tests: `test_interview_contract.py::test_the_smaller_step_instruction_is_added_only_for_a_turn_whose_message_has_a_risk_stem`
     (flagged → instructions + sentence; plain → unchanged; stem only in an earlier
     message → unchanged; prompt context keys identical; the sentence contains none of
     support/screen/flag/risk/safety/distress/crisis/life and no stem);
     `test_interview_agent.py::test_every_request_of_a_turn_with_a_risk_stem_carries_the_smaller_step_instruction`
     (fake provider with one repair: both requests carry it when flagged, neither when
     not); `test_interview_agent.py::test_the_fixture_follows_the_smaller_step_instruction_and_asks_no_career_question`;
     the prompt-bounds test now also fits a 2,000-character flagged message.
   - RED (the names added with the old behaviour first): `4 failed` (prompt version 3;
     instructions unchanged; the instruction absent from both requests; the fixture asked
     "What do you do now…"). A second RED after the first implementation: `2 failed`
     (pydantic-ai strips the trailing newline, so the constant became bare text, R4-1).
     GREEN: `pytest tests/domain/test_interview_contract.py tests/domain/test_interview_agent.py tests/domain/test_safety.py -q`
     → `758 passed`.
4. **Never stored.** Nothing new is written; the panel and the instruction are derived per
   response and per request.
   - Test `tests/integration/test_interview_choices.py::test_a_message_with_a_risk_stem_is_sent_with_the_support_panel_and_none_of_it_is_stored`:
     a flagged and an ordinary message through the real API and a durable worker (fake
     provider honouring the instruction): 202 for both, the panel only on the flagged one,
     a replay with the same key returns the same turn and the same panel; the flagged
     turn's stored proposal has no next question and the ordinary one has one (the
     instruction reached the worker's model for that turn only); a leak scan of every
     `nessa_app` and `nessa_dbos` row, the worker log, the captured API log and the export
     finds none of the panel wording, "116 123", the policy version or the instruction;
     no receipt for the workspace contains "support".
   - RED (the new test file against HEAD 6b1d3b9, in a scratch worktree): `KeyError:
     'turn_id'` (HEAD answered 200 and withheld the message). GREEN:
     `cd backend && uv run --locked pytest -m integration tests/integration/test_interview_choices.py -q`
     → `4 passed in 19.68s`.
5. **Old tier 1 removed** (code, tests, ADR text, register claims, send-anyway): the
   tier-1 classifier and response (backend), `CommandResult.record` (R4-7), the web
   alert, its Vitest and e2e tests, the `you--support` capture and its three PNGs, the
   ADR's tier text and pause list, the register's PROF-09/UI-06/H-12 claims, the runbook
   and the Sprint 2 review's current-state text (the history of rounds 1-3 is kept as
   history). Not CLAUDE.md: see concerns. Evaluation: `observe_support` reports `support_shown` only; SUP-09..13
   now expect the panel (career phrasing with a stem). Check: `git grep` for
   `SupportTier|screen_message|SupportShown|send_after_support|acute_distress|risk_mention`
   finds only the old-receipt test and the spec's own words.
6. **Tests** — the table (item 1), the instruction (item 3), the never-stored scan (item
   4), the panel announced and dismissible (item 2).
7. **Old receipts** (M-b). Test
   `test_interview_choices.py::test_a_turn_receipt_stored_before_the_redesign_is_refused_never_a_500`
   plants a round-2-shaped receipt (response with `support_note`, fingerprint over a
   request with `send_after_support`) and replays it with today's request and with an old
   client's body. RED against HEAD: `assert (500, 'INTERNAL_ERROR') == (422,
   'IDEMPOTENCY_KEY_REUSED')` (the re-review's 500 reproduced). GREEN: `422
   IDEMPOTENCY_KEY_REUSED` and `422 VALIDATION_FAILED` (in the `4 passed` run above). The
   planted row is deleted in `finally`.
8. **ADR 0007** decision 7 rewritten: why one screen (the three rounds' failures), the
   exact stem list, the flow, never stored, the old-receipt behaviour, and the known limits
   (finite English stem list, false positives show the panel with examples, no intent
   judgement, the reply not checked for a question); Status, Consequences and the H-12
   checklist updated; provisional (R6, H-12).

## Live calls
None this round.

## Checks (final code)

Run once, after the last code commit (`16ee339`); `b608e7d` changes docs and captures only:
- `make check` → exit 0: ruff format 175 files formatted, ruff check passed, mypy clean
  (175), pytest `1072 passed, 185 deselected`, fixture validator passed; "generated API
  client matches the backend's OpenAPI document", Biome 108 files, `tsc`, Vitest `24
  files, 191 tests passed`. No warnings.
- `make acceptance` → exit 0: `185 passed, 1072 deselected` integration and stack (4m35s),
  Storybook build completed, Playwright `22 passed` (including `[PROF-09] a message with a
  risk stem is sent as usual, with the support panel and a smaller step`). One Node
  warning (`NO_COLOR` ignored because `FORCE_COLOR` is set), from the environment.
- `cd apps/web && pnpm run review-screenshots` → exit 0, `3 passed`; 81 captures + 3
  `checks-*.json` (27 per viewport), every entry fonts loaded, overflow 0, no overprint,
  no axe, no console errors (parsed). Committed: the three `you--support-note` PNGs and
  the checks files; the three `you--support` PNGs removed (capture gone with the blocking
  response). Other recaptured PNGs differed only by run-to-run churn (message timestamps)
  and were left as they were.
- Stacks: all test stacks removed (no `nessa` container running); the scratch worktree
  for the HEAD RED runs removed; no other project's containers touched. Dev stack not
  started.

## Generated paths to skip
`apps/web/src/generated/` (regenerated: `send_after_support`, `SupportResponseOut`, the 200
response and `SupportNoteOut.policy` removed), `docs/reviews/sprint-2/screenshots/`.

## Not done / concerns
- **CLAUDE.md is stale and not edited by me**: lines 66-69 still describe the removed two
  tiers ("First-person acute distress gets the fixed support response before any model
  call ... two tiers"). It is an agent-instruction file, which an agent's brief cannot
  authorise changing, so it needs the user (or the controller with the user's consent) to
  update it to the one-screen design.
- Accepted false positives now show the panel on career, workplace and figurative phrases
  with a stem (listed in ADR decision 7 and H-12). The stem list is finite and English;
  candidate additions ("end it", "carry on", "not exist", method words) are left to H-12.
- The model's flagged-turn reply is instructed, not validated, to ask no career question;
  the live model has not been run on a flagged turn (no live calls this round).
- Old local receipts from rounds 0-2 may still hold support text (pre-release local
  data); they can no longer be replayed (422).
- `next` 16.4.1 age exception: unchanged from round 3.

# Fix round 5 (FIX_BASE b608e7d): normalised words by proximity; the panel on a refusal

Re-review 4 (`task-6-rereview-4.md`): items 2-5, 7, 8 met; item 1 partial (I-1), I-2 a
regression, minors M-1..M-6. Controller ruling: match normalised tokens by proximity; a
hand-written table from every reported shape; screen before every refusal; the server
drops `next_question` on flagged turns; claims say exactly what is covered; fix the 422's
reason; CLAUDE.md left to the controller.

## Commits

| SHA | Subject |
|---|---|
| `3289169` | Screen normalised words by proximity, and show the panel on a refused send |
| `48c5b4d` | Record fix round 5: the word-proximity screen and the refused-send panel |

## Rulings

- **R5-1 Constructions and windows.** Each construction anchors on a core word and looks
  for its marker within a stated window (3 or 4 words; listed in `safety.py` docstrings and
  ADR decision 7). Markers are positive evidence only (a negation, a reflexive, a
  possessive, an intent or wish); no excusing word lists. Possessors now include any word
  ending 's and "own" (re-review 4 item 4), and the wish rule takes any subject (noun
  subjects included), since proximity no longer needs a pronoun.
- **R5-2 Where a window adds a false positive.** "end my working life" (end … my … life,
  within 3) now triggers the panel; "the end of my working life" (4 words apart) does not.
  "I cut costs myself" and "the meeting would die" trigger it too. All listed in H-12.
- **R5-3 The refusal panel.** The route screens before `run_idempotent`; any `NessaError`
  the command raises for a flagged message is answered with the usual envelope plus a
  top-level `support_note` (`TurnRefusedOut`, documented as this route's 4XX/5XX model),
  worded "Your message was not sent; the reason is shown below." (`SUPPORT_NOTE_NOT_SENT`).
  Refusals raised before the route reads the message (authentication, a missing
  idempotency key, a body outside the schema such as an empty or 2,001-character message)
  cannot carry it; the web app does not send those. **Paused has no server refusal**: the
  API never refuses a message while paused (ADR 0007 decision 1), and the web app disables
  Send, so a message typed while paused (or with no key, or while a reply is on its way)
  is never sent and never screened. Listed in H-12; not changed, since sending while paused
  would change agreed behaviour.
- **R5-4 Dropping the question.** In `check_turn`, recomputed from the current message:
  the next question is treated as absent before the one-question checks, so a dropped
  question costs no paid repair, and the proposal keeps everything else. The test fake
  now keeps its question under the instruction (as a model ignoring it would) and marks
  its reply, so the integration test shows both that the instruction reached the worker's
  model and that the server dropped the question.
- **R5-5 M-5.** The key-reuse refusal is shared by every command, and the fingerprint
  covers the request's format, so the accurate reason is general: "already used for a
  different request, or for this request in an earlier request format. Send it again with
  a new key." No legacy-fingerprint shim. The round-4 claim is corrected: receipts from
  before Task 6 (no `send_after_support`) have today's fingerprint and replay as a 202.

## Per item: change, covering test, command, output

1. **I-1, normalised words by proximity.** `safety.py`: `words_of` (NFKC; apostrophe
   variants U+2018/2019/201B/02BB/02BC/0060/00B4 to `'`; hyphen and dash variants
   U+2010-2014/2212/FE63 to `-`; soft hyphen and zero-width characters removed; casefold;
   "n't" and the apostrophe-less forms to "not"; 'm/'re/'ve/'ll/'d; wanna, gonna, gotta,
   tryna), `_risk_word`, and nine construction rules in `_RULES`; `has_risk_stem` runs them
   over the words. The regex `_RISK` is gone. `POLICY_VERSION = "support-policy-5"`.
   - Test `tests/domain/test_safety.py::test_every_reported_shape_triggers_the_support_flow_and_career_text_without_one_does_not`:
     a hand-written table: the reported shapes that must flag, each naming its source (rr1
     corpus, rr2 I-1/I-2/M-2, rr3 C-1/N-I1/N-I2/M-a/M-c, rr4 I-1/M-3), and no-stem career
     rows that must not (the reviewers'
     lifeguard, lifelong, life sciences, life savings, workplace cuts, without meetings, and
     window guards such as "I didn't go on to university", "I don't want to work here");
     each row also checked inside other text and in capitals. The generated cross-products
     are gone.
   - RED (the new table against the round-4 screen): `29 failed, 103 passed` — every
     re-review 4 probe (contracted perfect/progressive negations, `wanna live`, stacked
     adverbs, "no longer go on", adverbs in go-on, "isn't any reason", plural and adjective
     reasons, `'d` and past-perfect wish, noun subject, noun possessor and bare "own") and
     all three M-3 Unicode rows. GREEN: `pytest tests/domain/test_safety.py -q` → `138
     passed`.
   - Extra check (not committed): the whole round-4 table (692 rows, generated forms
     included) against the new screen: `1 failed, 691 passed` — the one change is "I want to
     end my working life in teaching", now flagged by the window (R5-2).
2. **I-2, a refused send shows the panel.** `routes_interview.submit` screens first and
   answers a refusal of a flagged message with `TurnRefusedOut` (envelope + `support_note`,
   `sent=False` wording); `envelope.error_body` / `error_status` extracted for it. Web:
   `ApiError.supportNote` (from the refusal body), `useSendMessage` keeps `{note, sent}`
   for success or refusal, `Conversation` announces "Your message was not sent. Support
   information is shown above the reply field." for a refusal.
   - Tests: `test_interview_choices.py::test_every_refused_send_of_a_message_with_a_risk_stem_still_shows_the_support_panel`
     (stale version 409, too long 422, key reused 422, no key 422 `CREDENTIAL_REQUIRED`,
     another account 404, over budget 402: each carries the not-sent panel and the four
     services; an ordinary message refused over budget has no `support_note`; no extra turn
     is stored); `YouChapter.test.tsx` "shows the panel with a refused send too, and says the
     message was not sent" (402 with the panel: panel shown, refusal shown, reply field
     kept, polite announcement).
   - RED: integration `KeyError: 'support_note'` (the six refusal codes already as
     asserted); Vitest `Unable to find role="region" and name "Support is available"`.
     GREEN: `pytest -m integration tests/integration/test_interview_choices.py -q` → `5
     passed`; `vitest run src/components/YouChapter.test.tsx` → `17 passed`.
3. **Career question dropped by the server.** `interview.check_turn` (R5-4).
   - Test `test_interview_contract.py::test_a_turn_whose_message_has_a_risk_stem_never_keeps_a_next_question`
     (a flagged output with a question and a "?" in its reply: no problems, question
     dropped, changes and missing fields kept; a stem only in an earlier message keeps the
     question); the integration never-stored test now asserts the flagged turn's stored
     proposal has no question although the fake asked one, and its reply carries the
     instruction's mark.
   - RED: `assert ['reply: no question here; ask the one question only in next_question'] == []`
     (a paid repair, and the question kept). GREEN: `pytest tests/domain -q` → `418 passed`.
4. **Minors.** M-1: "any inflection/form" claims removed from `safety.py`, `test_safety.py`,
   the register, the Sprint 2 review and the ADR; each now lists what is matched, and the
   table is described as covering the reported shapes, not every wording. M-2: the row
   count is no longer cited (register, review, report). M-3: Unicode normalisation, with
   rows. M-4: item 3. M-5: R5-5, asserted in the old-receipt integration test
   (`"earlier request format" in message`, and the replayed refusal carries the panel).
   M-6: CLAUDE.md left to the controller (still stale at lines 66-69).
5. **Docs.** ADR 0007 decision 7 (normalisation, listed words, constructions and windows,
   the flow including refusals and the dropped question, never stored, the corrected
   receipt claim, H-12 limits incl. windows and unsent messages), Status, Consequences and
   the H-12 checklist; register PROF-09 and H-12; runbook; Sprint 2 review (round 5
   paragraph, wording, checklist item 5, checks).

## Live calls
None this round.

## Checks (final code)

Run once, after the last code commit (`3289169`):
- `make check` → exit 0: ruff format 175 files formatted, ruff check passed, mypy clean
  (175), pytest `513 passed, 186 deselected`, fixture validator passed; "generated API
  client matches the backend's OpenAPI document", Biome 108 files, `tsc`, Vitest `24
  files, 192 tests passed`. No warnings.
- `make acceptance` → exit 0: `186 passed, 513 deselected` integration and stack (4m40s),
  Storybook build completed, Playwright `22 passed` (including the PROF-09 journey). One
  Node warning from the environment (`NO_COLOR` ignored because `FORCE_COLOR` is set).
- After acceptance, `48c5b4d` reworded one docstring in `safety.py` (no code change);
  re-checked with ruff format --check, ruff check, mypy and `pytest -q` → `513 passed`.
- Screenshots not recaptured: the panel's look and wording beside a sent message are
  unchanged; the refused-send panel state has no capture in the visual package.
- Stacks: no `nessa` container running; dev stack not started; no other project's
  containers touched.

## Generated paths to skip
`apps/web/src/generated/` (regenerated: `TurnRefusedOut`, the 4XX/5XX model of
`submit_turn`, and `SupportNoteOut.message`'s description).

## Not done / concerns
- CLAUDE.md lines 66-69 still describe the removed two tiers (left to the controller, as
  ruled).
- Accepted false positives show the panel (listed in ADR decision 7 and H-12), now
  including "end my working life" and "I cut costs myself" from the windows; wording
  outside the lists or windows still gets nothing (H-12 decides extensions).
- Messages never sent are never screened: while paused, with no key, or with a reply on
  its way the web app disables sending, and the API has no paused refusal to attach a
  panel to (R5-3; H-12). Requests refused before the message is read get no panel.
- Only the next question is dropped; the reply text itself is not checked for a career
  question. No live model has been run on a flagged turn.
- `next` 16.4.1 age exception: unchanged.
