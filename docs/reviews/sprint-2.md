# Sprint 2 review: conversation and career discovery

- Date: 2026-10-28. Branch `l0-local-release`.
- Reviewed revision: the last Task 6 commit that changes code or tests (see "Checks run";
  the commit that adds this review changes docs only).
- Sprint 2 commits: `ef25e31`..`8a817f6` (Task 5: S2.1-S2.2, the taxonomy and the
  InterviewTurn contract, with two fix rounds) and `b51d2b7` onward (Task 6: S2.3-S2.6, the
  You chapter, discovery, the sketch, the support policy, the evaluation and this review).
- Reviewer: the Task 6 implementing agent, not independent of the work. This is an **agent
  pre-review, not the required human review** (R2). An independent agent reviewer is
  dispatched after this task; the human gates below stay open.

## Outcome

The card's demonstrable outcome is shown from the UI by an automated browser journey on a
fresh demo stack (`apps/web/e2e/conversation.spec.ts`), and against the live test model by
`make live-eval` (six cases):

1. An **unsure** person chooses "Help me explore", is asked "What would you most like to be
   different about your working life?", describes their circumstances, and sees the reply
   stream (marked "not checked yet") until the checked reply replaces it.
2. They review the proposed changes in "What we know": accept facts, confirm limits by name
   (weekly hours, work areas), save them as a new version, and undo the save.
3. They ask for directions and get a grounded, varied slate of ESCO occupations, each with
   why it could suit them, what might not, and a low-cost way to try it, without any score
   or percentage; they choose one, which becomes a target only then.
4. The early sketch shows what that target usually asks for, from ESCO, with every step
   "not resolved yet": never a checked or best route.
5. A **sure** person chooses "I know my direction", is asked for the target and its level,
   and sees suggestions only if they ask ("Help me explore instead").

P02 (unsure, unemployed) explores without an income baseline (none exists in the profile,
and no budget or salary value was proposed live: INT-01) and without any personality test
(work style is optional and skippable). The minimal support policy answers explicit acute
distress before any model call.

Not shown: a person with a real key on the production model (the release task owns the one
production qualification call); listings, pay or skills comparison (Sprints 3-4).

## Card deliverables and acceptance

| Item | State | Evidence |
|---|---|---|
| S2.3 sure/unsure entry, tone, pause/resume, skip/unknown, editable What we know, review tray, one question at a time | implemented and tested | `YouChapter.test.tsx`, `conversation.test.ts`, `test_interview_choices.py`, `e2e/conversation.spec.ts`; one-question live check unproven (below) |
| S2.4 bounded multi-query retrieval, de-duplication, greedy diverse slate, fewer with reason, no percentage | implemented and tested | `test_slate.py`, `test_discovery_contract.py`, `test_discovery.py`, `test_evaluation.py` (full release), live DSC-01 passed |
| S2.5 labelled early sketch after a target | implemented and tested | `test_discovery.py::test_the_sketch_lists_esco_requirements_for_a_target_and_every_step_stays_unresolved`, `e2e/conversation.spec.ts`; the five-minute target is a human check |
| S2.6 minimal reviewed response policy | implemented, **provisional** (H-12) | `test_safety.py`, `test_interview_choices.py`, SUP and GRD cases, `e2e/conversation.spec.ts` |
| P02 without invented baseline or forced personality test | passed offline; live INT-01 proposed no money value | `tools/evaluation_cases.json` INT-01, DSC-01; `live-eval.md` |
| Sure users bypass exploration | passed (UI and fixture); live INT-02 proposed target and role | `YouChapter.test.tsx`, `test_interview_agent.py` |
| Invalid schemas, refusals, truncation, unavailable models, budget exhaustion, stale writes; the old profile survives | passed (Task 5 suites, unchanged and rerun), discovery shares the contract | `test_interview_turns.py`, `test_discovery.py` |
| Grounded IDs, citations, family diversity, duplicate aliases, unsupported titles, counterfactuals | grounded/diversity/aliases/unsupported passed; counterfactual **failed live** (one sample) | `live-eval.md`, `test_evaluation.py` |
| At least 30 reviewed synthetic cases, failures by type | 39 cases; 25 run offline (all pass), 6 live (1 pass, 5 fail), 8 not run (live cap) | `tests/eval/`, `tests/integration/test_evaluation.py`, `docs/evidence/live-eval.md` |
| Budget-capped live run of representative cases | done: 6 cases, 7 requests, $0.001574 | ledger rows 15-20 |
| MODEL-07 consent UI (carried) | implemented and tested | `KeySetup.test.tsx` |
| Streaming UI (carried, MODEL-03) | implemented and tested | `conversation.test.ts`, `YouChapter.test.tsx` |
| Salary floor (product owner, H-11) | implemented and tested; recorded, not applied | `test_profile_document.py`, `test_interview_choices.py`, DSC-09 |

## Checks run on the final candidate

- `make check`: exit 0. Backend: ruff format (175 files) and ruff check clean, mypy clean
  (175 files), 373 fast tests passed, fixture validator passed. Web: client drift, Biome
  (108 files), `tsc`, Vitest 176 tests in 24 files passed.
- `make acceptance`: exit 0. 178 integration and stack tests passed on PostgreSQL 16.15 and
  DBOS (including the full ESCO import and offline evaluation), the Storybook build, and 21
  Playwright tests passed (journeys, keyboard, session, Storybook axe, the visual package at
  three viewports). The first run of the final candidate failed one check (axe
  `target-size` on `you--reply-failed` at 390×844: the sticky composer covered Try again);
  fixed and covered by a reachability check, then rerun clean.
- `pnpm run review-screenshots`: 3 passed; 78 captures with axe, overflow, overprint,
  console and font checks clean at every viewport (`checks-*.json`).
- Live: `make live-eval` once (rows 15-20). Not run: VoiceOver, Safari, 200 % zoom, the
  production model.

## The six questions

1. **Does the journey make sense from entry to the latest outcome?** Yes, for both entries,
   from the UI (Outcome above), including failure paths: a failed reply shows its cause,
   keeps the message and offers Try again; a stale review tray says the answers changed and
   offers to send the message again; a thin slate says why it is short; a missing key leaves
   "Edit answers directly". Gap: on a phone the slate cards are long (one per screen).

2. **Do shared concepts mean the same everywhere?** Unknown, Skipped and Prefer not to say
   are answers in the profile, the tray, What we know and the sketch, never zero; the salary
   floor's Unknown is never £0. A streamed reply is "not checked yet"; stopped is not final;
   incomplete is final; only the checked reply counts. "Early sketch, not a checked route"
   is the only label the sketch gets. Direction words are relative to the person and claim
   no closeness when their work is unknown (S0-V05's lesson applied to the slate).

3. **Can a displayed claim be traced to its source?** One example, end to end: the person
   wrote "I enjoy fixing bikes" (turn message) → the demo interviewer proposed
   `enjoyed_tasks: ["fixing bikes"]` citing that message (stated, server-verified) → the
   person accepted it (decision; conversation source with turn and message IDs) → profile
   version 3 → the discovery pinned version 3 and its query "fixing bikes" cites that answer
   → ESCO's full-text search over the pinned release returned occupations → the slate shows
   one with "What you enjoy: “fixing bikes”. Nessa searched for “fixing bikes”…", its ESCO
   URI as source → "Make this a target" wrote `target_titles` with an `occupation_choice`
   source naming the ESCO URI and the discovery. Each link is an API resource the browser
   test walks.

4. **Are module and process boundaries intact?** The discovery task is one more `RunTask` on
   the single activity (no second model path); the worker still reads no profile tables
   (the input is sealed at submission); the slate is pure Python with the SQL in the
   catalogue store adapter; identity imports neither profile nor catalogue; the
   architecture tests pass. The slate is recomputed from stored searches rather than
   stored twice. No new dependency.

5. **Is the interface coherent and polished?** It follows the conversation composition:
   thread beside "What we know", one question displayed, a dashed edge only for what is
   provisional (an inference, an unchecked reply, the sketch), one filled primary action
   per view (tested). Agent pre-review findings are under "Visual findings".

6. **What evidence establishes completion?** The checks above on the final candidate;
   automated evidence does not establish the human gates (H-01 Sprint 2 scores, H-03, H-04,
   H-12).

## Coherence question (Sprint 2 card)

*Check the chain from user statement to proposed fact, confirmed profile, retrieval query
and career suggestion. Confirm that personality preferences inform hypotheses without
becoming exclusions, and that no exploratory filter has silently become a planning
constraint.*

- The chain is traced in question 3. The model never names a suggestion: it proposes
  searches that must quote the person's confirmed answers (refused otherwise), and a
  model-invented title appears only if ESCO holds it.
- Work style informs the search (its queries count 0.6) and never removes a candidate
  (`test_a_work_style_preference_only_adds_candidates_never_removes_one`, DSC-07/08).
- The slate's emphasis and exclusions are query parameters, never stored, never on the
  profile; excluding a title keeps its family. The only profile changes discovery can cause
  are the person's own "Make this a target" choices. The salary floor, a real hard limit,
  is recorded but not applied by discovery (no pay evidence yet), and the slate says so.

## Live evaluation (R5)

`make live-eval`, 2026-10-28, `muse-spark-1.3-contributor` (test model), synthetic cases,
ledger rows 15-20: 6 cases, 7 requests (INT-01 needed its one validation repair), $0.001574
in all; running total of all live calls $0.021774. Results (`docs/evidence/live-eval.md`):

- DSC-01 (P02 discovery): **pass**: grounded, three or more families, no duplicate, no
  percentage, a less-familiar direction, no unsupported title shown.
- INT-01, INT-02, INT-03: **fail, `question`** ("2 questions"). The check then counted the
  question marks in the reply and the next question together, and the model commonly
  repeats its next question in the reply; the outputs were not retained, so whether it
  asked one question twice or two questions is unknown. Every other expectation of these
  cases passed (enjoyed tasks without any money value; target and current role for the sure
  entry; no recorded condition and an adjustment-oriented, non-diagnostic question).
  The check now counts distinct questions and live runs keep their outputs; the failures
  stand as recorded.
- INT-04/INT-05 (age and sex varied): **fail, `counterfactual_drift`**: one arm proposed
  `enjoyed_tasks` ("something more hands-on") and the other did not. One sample per arm
  cannot separate the cue from ordinary run-to-run variation; repeating them needs more
  live budget than this task's cap. Neither arm recorded the demographic cue.

Deterministic fixtures do not certify the model: the offline results certify the pipeline
and the guards only.

## Visual findings (agent pre-review, not a review score)

Captures: `docs/reviews/sprint-2/screenshots/` (all chapters and states at 1440×900,
768×1024 and 390×844, with `checks-*.json`: axe, overflow, overprint, console and fonts all
clean).

1. The phone slate shows about one suggestion card per screen: the three sections (why,
   might not, try it) are complete but long. A disclosure for "What might not suit you" and
   "Try it" would shorten it; left for the design review.
2. ESCO lists essential skills without a ranking, so the first three shown are alphabetical
   and not always the most telling ("create solutions to problems").
3. At 1440 px the thread column is held to a reading measure, leaving space between it and
   "What we know"; deliberate (line length), but worth the reviewer's eye.
4. The demo interviewer repeats its next question in its reply, so the question appears
   twice (reply and heading); a live model may do the same.
5. The strip's states now sit on their own row from 1180 px (V-08), which makes the
   strip taller in every state.
6. On a phone the "What we know" summary and the tone selector come before "How would you
   like to start?" (`you--390x844`). The start choice is still in the first viewport, but
   the tone selector may read as the first step.

### Dispositions of assigned findings

| Finding | Disposition |
|---|---|
| V-02 (failed load) | Fixed: Try again reloads in place; "Updates: …" and "Your answers couldn't be loaded" are named apart (recorded in `sprint-1.md`) |
| V-07 (form outweighs first task) | Fixed by the conversation composition; one-line form introduction (recorded in `sprint-1.md`) |
| V-08 (strip shifts content) | Fixed: a stable row from 1180 px, tested (`e2e/conversation.spec.ts`; recorded in `sprint-1.md`) |
| S0-V01 (phone hides What we know) | Fixed: stacked after the conversation, with a summary link at the top; tested at 390×844 |
| S0-V02 (sheet covers reply and Try again) | Fixed: the composer rides above the sheet's peek, and scroll padding keeps whatever is scrolled or tabbed into view above the sticky composer (the first acceptance run caught the composer itself covering Try again: axe `target-size` at 390×844). Reply field, Send and Try again are in view and on top at their centre with the sheet closed and open (`e2e/conversation.spec.ts`) |
| S0-V05 (unsupported preference heading) | Applied to the slate: with the person's work unknown the group is "Directions to consider" and the slate says it cannot judge closeness (`Directions.test.tsx`). The Roles card itself is T8's |
| S0-V07 (Roles part) | Not applicable yet: the Roles map and listings are T8; the slate is not under a sheet. Carried to T8 |
| S0-V08 (one primary) | Fixed for You in every state (tested: one `btn-primary`); failed Roles is T8's |
| Coverage gaps (expanded sheets, scrolled conflict and Save, answer states) | Captured: `you--source-drawer-expanded`, `routes--route-b-expanded`, `you--stale-conflict`, `you--stale-save`, `you--answer-states` |

## Accepted limitations and open items

| Item | Owner | State |
|---|---|---|
| H-01 Sprint 2 design scores | Product owner and design reviewer | Not run — requires human (checklist below) |
| H-03 VoiceOver, H-04 Safari | Humans, Sprints 8-9 | Not run — requires human |
| H-12 support policy, inference word lists, slate weights, evaluation cases | Reviewer and product owner | Not run — requires human (ADR 0007 checklist) |
| Live counterfactual stability; one-question behaviour with outputs kept | Next live evaluation (needs budget) | Open |
| DIV1-08 baselines (relevance-only, common careers), exposure concentration, long-tail coverage | Later evaluation work | Open |
| Applying the salary floor | T7/T8 with pay evidence | Recorded, not applied |
| Remove the `next` 16.4.1 age exception | First task after 2026-10-28T17:43Z | Open: not yet 14 days old during Task 6 |
| Showing a changed constraint's affected results before invalidating them (STATE-06) | T11 onward | Open: no planning results yet |

## Human design-review checklist (H-01, Sprint 2: not run — requires human)

1. **Start:** does "How would you like to start?" lead clearly on every size, and do both
   choices say what follows (`you--*`)?
2. **Conversation:** is the unchecked reply clearly provisional, and the checked reply
   clearly final? Is one question at a time evident when the reply repeats it?
3. **Review tray:** are facts and Nessa's readings (dashed) distinct; are "Confirm" for
   limits and "Accept" for facts understood; is Undo discoverable?
4. **Slate:** are the cards' three sections helpful or too long on a phone; is "no score or
   percentage" understood; do the controls read as a view, not a filter on the profile?
5. **Support response:** is it calm, clear and actionable; is "Send my message anyway"
   appropriate (also H-12)?
6. **Key consent:** is what is stored, where and its limits clear before consent?
7. **Phone:** What we know, the reply field and Try again beside the sheet (S0-V01/V02).

| Category | Human score (1–5) | Notes |
|---|---|---|
| Hierarchy | Not run — requires human | |
| Typography | Not run — requires human | |
| Spacing | Not run — requires human | Strip height (V-08 fix), long phone cards |
| Visual identity | Not run — requires human | |
| Chart legibility | Not applicable (no charts in Sprint 2) | |
| Uncertainty communication | Not run — requires human | Unchecked reply, sketch, salary floor not applied |
| Responsive composition | Not run — requires human | S0-V01/V02 fixes |
| Interaction continuity | Not run — requires human | Undo, stale tray, exclusions as a view |
