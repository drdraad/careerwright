# Sprint 2 review: conversation and career discovery

- Date: 2026-10-28. Branch `l0-local-release`.
- Reviewed revision: `96259d7` for this pre-review; after the independent review's fix
  rounds 1 to 3, the final code is `561c97f` (the commit that updates this review changes
  docs and screenshots only).
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
(work style is optional and skippable). The minimal support policy is one recall-first
screen (since fix round 4; by normalised words and proximity since round 5): a message with
a listed risk word or construction is sent as usual, with a calm support panel beside it
(beside the refusal, if the send is refused) and a smaller step, no career question, in
that turn's reply.

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
| Grounded IDs, citations, family diversity, duplicate aliases, unsupported titles, counterfactuals | grounded/diversity/aliases/unsupported passed; counterfactual **inconclusive** (one sample per arm; a powered comparison is the release task's) | `live-eval.md`, `test_evaluation.py` |
| At least 30 reviewed synthetic cases, failures by type | 43 cases (fix round 1 added four support false-positive cases); 29 run offline (all pass); live: see "Live evaluation" | `tests/eval/`, `tests/integration/test_evaluation.py`, `docs/evidence/live-eval.md` |
| Budget-capped live run of representative cases | done: first run 6 cases, 7 requests, $0.001575 (rows 15-20); fix-round run below | `docs/evidence/live-usage.md` |
| MODEL-07 consent UI (carried) | implemented and tested | `KeySetup.test.tsx` |
| Streaming UI (carried, MODEL-03) | implemented and tested | `conversation.test.ts`, `YouChapter.test.tsx` |
| Salary floor (product owner, H-11) | implemented and tested; recorded, not applied | `test_profile_document.py`, `test_interview_choices.py`, DSC-09 |

## Checks run on the final candidate

Pre-review candidate (`96259d7`): `make check` and `make acceptance` passed (373 fast
backend tests, 176 Vitest, 178 integration and stack, 21 Playwright); its first acceptance
run caught the sticky composer covering Try again (axe `target-size` at 390×844), fixed and
rerun clean.

After fix round 5 (final code, `3289169`):

- `make check`: exit 0. Backend: ruff format (175 files) and ruff check clean, mypy clean
  (175 files), 513 fast tests passed, fixture validator passed. Web: client drift, Biome
  (108 files), `tsc`, Vitest 192 tests in 24 files passed.
- `make acceptance`: exit 0. 186 integration and stack tests passed on PostgreSQL 16.15 and
  DBOS (including the full ESCO import and offline evaluation), the Storybook build, and 22
  Playwright tests passed (journeys, keyboard, session, recovery in place, Storybook axe,
  the visual package at three viewports).
- `pnpm run review-screenshots` (fix round 4; the panel's look is unchanged since): 3
  passed; 81 captures (the blocking `you--support` capture is gone with the response it
  showed; `you--support-note` recaptured) with axe, overflow, overprint, console and font
  checks clean at every viewport (`checks-*.json`). The panel beside a refused send has no
  capture.
- Live: `make live-eval` twice in all (rows 15-20, then the fix-round 1 run, rows 21-24);
  none in fix rounds 2 to 5. Not run: VoiceOver, Safari, 200 % zoom, the production model.

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
ledger rows 15-20: 6 cases, 7 requests (INT-01 needed its one validation repair), $0.001575
in all ($0.00157486); running total then $0.021774. Results (`docs/evidence/live-eval.md`):

- DSC-01 (P02 discovery): **pass**: grounded, three or more families, no duplicate, no
  percentage, a less-familiar direction, no unsupported title shown.
- INT-01, INT-02, INT-03: **fail, `question`** ("2 questions"). The check then counted the
  question marks in the reply and the next question together, and the model commonly
  repeats its next question in the reply; the outputs were not retained, so whether it
  asked one question twice or two questions is unknown. Every other expectation of these
  cases passed (enjoyed tasks without any money value; target and current role for the sure
  entry; no recorded condition and an adjustment-oriented, non-diagnostic question).
  The failures stand as recorded. Fix round 1 made the question part of the contract
  (only in `next_question`, none in the reply), made the check count per field, and keeps
  each live output in the private evidence directory.
- INT-04/INT-05 (age and sex varied): recorded `counterfactual_drift`, now read as
  **inconclusive**: one arm proposed `enjoyed_tasks` ("something more hands-on", a
  judgement call) and the other did not, while the unambiguous fields matched. One sample
  per arm cannot separate the cue from ordinary run-to-run variation. Neither arm recorded
  the demographic cue. The pair now compares only the unambiguous fields and leaves the
  default live run; a powered comparison is the release task's.

**Fix-round run** (the one re-run the controller allowed): `make live-eval`, 2026-10-28
14:08 UTC, scope `live-eval-fix1` (its own 9-request cap), the default four cases on
`muse-spark-1.3-contributor`, ledger rows 21-24: 4 attempts, 5 requests (INT-01 needed its
one validation repair), $0.001324; running total of all live calls $0.023098; key leak scan
clean. **All four passed**: INT-01..03 now ask one question, only in `next_question`, with
none in the reply; DSC-01 is grounded and varied. One sample each: this shows the
contract can be met, not that it always is. The outputs are in the private evidence
directory. Two of the three questions came back without a question mark, which the
contract allows and the UI shows as written (a quality note for H-12).

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
4. *Fixed in fix round 1:* the demo interviewer repeated its next question in its reply,
   so the question appeared twice (reply and heading). The question now lives only in
   `next_question`, by contract (ADR 0007 decision 3).
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
| S0-V08 (one primary) | Fixed for You: exactly one `btn-primary` with nothing waiting (Send), while reviewing (the tray's Save), after a failed reply (Try again) and with the answer form open (its Save), each tested (`YouChapter.test.tsx`); none at the entry choice, whose two choices are equal by design. Failed Roles is T8's |
| Coverage gaps (expanded sheets, scrolled conflict and Save, answer states) | Captured: `you--source-drawer-expanded`, `routes--route-b-expanded`, `you--stale-conflict`, `you--stale-save`, `you--answer-states` (Unknown, Skipped and Prefer not to say side by side at every size since fix round 1), `you--salary-floor` |

## Independent review and fix round 1

Two independent agent reviewers (backend; web and docs) found 11 Important and 26 Minor
issues in this pre-reviewed candidate, none Critical. Fix round 1 corrected them; the main
behavioural changes, each with a test written first:

- The distress screen fired on career phrasing ("take my life in a new direction", "life
  savings", "live in London"); phrases now need their meaning. The support response no
  longer leaves an idempotency receipt.
- De-duplication chained unrelated occupations through ESCO's shared labels; it now folds
  direct aliases only. The working pool samples every retrieved family before relevance
  cuts it.
- The sketch asked the person to choose again for an occupation they had chosen, whenever
  another occupation shared its title; it now resolves by the choice.
- A salary floor's period was labelled `stated` without being checked; the demo
  interviewer misread a weekly wage and a course budget.
- The review tray could save part of a decision and lose an edit silently; edits are now
  checked first and saved in the same decision. "Send it again" swallowed errors and could
  send twice. Undo re-recorded restored answers as direct entries; it is now a revert that
  keeps each answer's source.
- Only the first reply was ever announced, and focus was dropped after the entry choice, a
  save and an undo.
- Register rows claimed tests that did not exist (MODEL-03's failed partial, STATE-06's
  edit and skip, MODEL-07's revoked key, S0-V08 in every state); the behaviour or the claim
  was corrected and each claim now names its test.

**Re-review and fix round 2.** The re-review found 35 of 37 fixed, accepted the A-M4
deferral, and found A-I-1 only partly fixed: excusing a match by the word after it had
turned some explicit statements into silent misses ("I want to kill myself over this", "I
keep hurting myself", "I don't want to live like this", "I feel suicidal and need
support"). By the controller's ruling the screen now has two tiers: first-person intent or
distress gets the support response and is not sent; any other risk word is sent as usual
with a support note, so none is dropped and no career phrase is blocked. Its remaining
limits are in the H-12 checklist. Nine minor findings were also fixed: undo is in the
cross-account sweep; a stored £0 floor still opens; folding stays within one ISCO minor
group (164 within-group ESCO alias pairs still fold, for H-12); kindred words only in
searches; a "?" in a reply with no next question costs no repair; and smaller ones.

**Re-review 2 and fix round 3.** The second re-review found the nine minor findings fixed
and A-I-1 still partial: three tier-1 branches did not check who was speaking (so "people
feeling suicidal" on a helpline, "print is going to die" and "thinking about suicide
prevention work" were blocked); "cutting myself" and a few inflections reached no tier;
the note was kept in the idempotency receipt; and the note was not announced. By the
controller's second ruling, tier 1 is now first-person present intent only and tier 2 a
broad stem screen over every inflection, both specified by one table of input shapes; the
receipt holds no note (a replay recomputes it, tested); the note is announced politely
and dismissing it returns focus to the reply field. Remaining limits are in the H-12
checklist.

**Re-review 3 and fix round 4.** The third re-review found the receipt and the
announcement fixed, but the narrowed tier 1 had dropped first-person shapes to no tier at
all (Critical), fired on career text with no risk stem ("lifeguard", "without meetings"),
and uncontracted negations reached neither tier. Two failed fixes in one direction showed
that intent cannot be classified precisely by pattern, so by the controller's ruling the
classifier is gone: one recall-first screen sends every message as usual and shows the
support panel for a listed stem, with a smaller-step instruction for that turn only;
nothing of it is stored. Stems inside career phrasing now show the panel, an accepted false
positive listed for H-12. The blocking response and "Send my message anyway" are removed.

**Re-review 4 and fix round 5.** The fourth re-review found the redesign right but the
matching still phrase-by-phrase: forms one family accepted were missing from another
("hadn't wanted to live", "can no longer go on", "isn't any reason to go on", "wish I'd
died"), and a refused send showed no panel. By the controller's ruling the screen now
reads normalised words (Unicode apostrophes and hyphens, case, contractions spelt out) and
flags listed words, or a construction's core word with its marker within a small window;
the table is now hand-written from every shape the reviewers reported, plus their career
examples. The message is screened before anything can refuse it, so a refused send
carries the panel; the server drops any next question on a flagged turn; and a key-reuse
refusal names an earlier request format as a possible reason.

## Accepted limitations and open items

| Item | Owner | State |
|---|---|---|
| H-01 Sprint 2 design scores | Product owner and design reviewer | Not run — requires human (checklist below) |
| H-03 VoiceOver, H-04 Safari | Humans, Sprints 8-9 | Not run — requires human |
| H-12 support policy, inference word lists, slate weights, evaluation cases | Reviewer and product owner | Not run — requires human (ADR 0007 checklist) |
| A powered counterfactual comparison (several samples per arm, against an H-12 tolerance) | Release task (cost estimate in the Task 6 report) | Open: REC1-09 inconclusive |
| An absolute relevance floor for weak queries (A-M4) | H-12 slate review, then evaluation | Open: needs calibration on the full release |
| DIV1-08 baselines (relevance-only, common careers), exposure concentration, long-tail coverage | Later evaluation work | Open |
| Applying the salary floor | T7/T8 with pay evidence | Recorded, not applied |
| Remove the `next` 16.4.1 age exception | First task after 2026-10-28T17:43Z | Open: not yet 14 days old during Task 6 |
| Showing a changed constraint's affected results before invalidating them (STATE-06) | T11 onward | Open: no planning results yet |

## Human design-review checklist (H-01, Sprint 2: not run — requires human)

1. **Start:** does "How would you like to start?" lead clearly on every size, and do both
   choices say what follows (`you--*`)?
2. **Conversation:** is the unchecked reply clearly provisional, and the checked reply
   clearly final? Is a failed reply's kept text clearly not saved? Is one question at a
   time evident?
3. **Review tray:** are facts and Nessa's readings (dashed) distinct; are "Confirm" for
   limits and "Accept" for facts understood; is Undo discoverable?
4. **Slate:** are the cards' three sections helpful or too long on a phone; is "no score or
   percentage" understood; do the controls read as a view, not a filter on the profile?
5. **Support panel:** is the panel beside a sent message, or beside a refused one, calm
   rather than alarming, clear and actionable, and easy to dismiss; does the question
   stepping aside while it shows read well; is it acceptable on a career phrase that only
   shares a stem (also H-12)?
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

## Addendum: Task 6b, the written "Why this could suit you" (S2.7, D3)

- Date: 2026-10-28. Commits `300eb4a`..`a8584a1` and the commit that adds this addendum.
  Reviewer: the Task 6b implementing agent, not independent of the work; an **agent
  pre-review, not the required human review** (R2).
- What changed: plan v1.1 added S2.7 after this review (ADR 0008 decision 4). A slate's
  suggestions may now carry a model-written note beside the deterministic words of ADR 0007
  decision 6, which stay underneath in every case and are what exports cite. ADR 0007
  decision 12 records the design; decision 6's title and last sentence now point to ADR
  0008 and to it.

**Demonstrated journey.** In the demo browser journey (`e2e/conversation.spec.ts`), the
slate appears, asks once for its note, and each card then shows "Why this could suit you"
with the demo explainer's labelled note (a claim, then "You said: “…”" and the part of
ESCO's record it quotes), followed by "How Nessa found it"; the journey records no request
outside the web origin and the Auth emulator. Live, EXP-01 ran a discovery and its note on
the test model with synthetic answers: six suggestions, each with one or two claims whose
quotations are spans of the answers or of that occupation's ESCO description, checked
independently against the taxonomy API (passed after one repair).

**The card's coherence question, for this addition.** The chain from statement to
suggestion is unchanged: the note is computed after the slate, from the answers the
discovery pinned and ESCO's records only, and nothing reads it back. The slate, a
suggestion's grounding, its place, the profile and a target's `occupation_choice` source
are the same with or without it (`test_slate_explanations.py` compares the slate before
and after). A view change never makes a call. A failed note is shown as unavailable: if its
run reached no model (refused for budget, key, access or model, read from its attempts), the
person may try it again by a click, and the new run replaces it; once a request was sent,
the slate has had its one call, and Suggest again (which says it makes a new set of
suggestions) is offered instead (fix round 1). No exploratory filter became a constraint.

**Six questions, briefly.**

1. Journey: as above; the failure path (invalid twice, cut off, refused before a run or
   before any request) is shown in the UI with its words, its one action and the
   provenance kept.
2. Shared concepts: a failed note uses the failure-class words, a refused request the
   error code's words, both from the generated client; "pending" uses the running status.
   The note says only the quoted words were checked; the sentences are the writer's own.
3. Traceability: each quotation names its source (an answer's field, or a part of ESCO's
   record) and is stored in the source's own characters; the export cites the ESCO URI and
   the discovery.
4. Boundaries: a run kind on the one activity (`SLATE_EXPLANATION_TASK`), a new adapter
   (`explanation_store`, listed in the architecture test); identity imports nothing new; the
   workflow's step sequence is unchanged, so the DBOS `application_version` stays
   `nessa-l0-1`. Found and fixed during the work: the submission first answered with the
   written text, which the command receipt then kept unsealed (the leak scan caught it);
   it now answers with the run only.
5. Interface: captures `you--slate` (written), `you--slate-note-pending`,
   `you--slate-note-unavailable` (with Suggest again) and, since fix round 1,
   `you--slate-note-retry` (with Try again) at 1440×900, 768×1024 and 390×844, with axe,
   overflow, console and font checks clean on every shot; no new colour pairing (existing
   text tokens on cards, a hairline rule, the existing error notice).
6. Evidence: see "Checks" below.

**Checks on the final candidate** (`9929707`, plus a comment-only edit and these docs).
`make check`: exit 0 (ruff format and lint, mypy, 567 fast tests, the fixture validator;
web: client matches, Biome, `tsc`, Vitest 199 tests). `make acceptance`: exit 0, 193
integration and stack tests on PostgreSQL 16 and DBOS (among them the six of
`test_slate_explanations.py`, EXP-01 over the full ESCO release and the live-eval
orchestration with EXP-01 on the fake provider), the Storybook build, and 22 Playwright
journeys (the demo journey shows the fixture explainer's note with no outside request;
every story passes axe; the visual package's 29 shots at each size pass its checks).
`pnpm run review-screenshots` wrote the committed captures (before a refinement of the
check that refuses a claim or quotation given twice; the UI did not change).

**Fix round 1 (independent review: three Important, four Minor).** Screened readiness,
pay and hiring words are allowed only by the occupation's ESCO record, never by an answer;
every quotation needs a content word and keeps a leading apostrophe; the note says only
the quoted words were checked; a note whose run reached no model may be tried again by a
click (migration 0012), and otherwise Suggest again is offered; more hiring and demand
phrasings; the repair message is capped to its allowance; answers too long for the prompt
in bytes are a typed refusal; the length, not "one sentence", is what is checked. Checks
on `42ef206`: `make check` exit 0 (581 fast tests; Vitest 201); `make acceptance` exit 0
(195 integration and stack tests, the Storybook build, 22 Playwright journeys); the note's
captures recaptured with every shot's checks clean (30 per size). The live EXP-01 output
(rows 25-26) predates the round; its stored claims and quotations were re-checked offline
after round 1's rules, and again after fix round 3 (below). No new live call.

**Fix round 2 (re-review 1).** The function words are now a standard English stopword
list's (four letters or more, with contraction stems), checked on the verified span as it
was folded for matching, so "about", "being", "could"/"should" and fullwidth "with" quote
nothing; an apostrophe after a letter belongs to its word ("s tools" is no fragment of
"mechanic's tools"); single quotes come off a quotation only as a matching pair; hyphenated
and employer phrasings ("an in-demand trade", "well-paying", "sought after", "employers
want", "short of staff") are refused; and a refusal asking again would only repeat (no
answer to quote, answers too long, no searches) now says why and offers what can work,
never a futile Try again. Checks on `e5714c5`: `make check` exit 0 (596 fast tests; Vitest
204); `make acceptance` exit 0 (195 integration and stack tests, the Storybook build, 22
Playwright journeys); the unavailable and answers-too-short notes captured at three sizes
with every shot's checks clean (31 per size).

**Fix round 3 (re-review 2).** A regression from round 2 is fixed: the demo explainer
quoted "children" out of "children's", which the stricter matcher refused, so a demo note
could fail whole; the explainer now reads each quotation back as the check does and quotes
the whole token ("children's", "students'"), and a property test shows its note always
passes. Also: "paying attention" is a skill, not pay; an apostrophe is part of a word only
inside it or after an "s", so "a 'people person'" can be quoted; quotation marks before
closing punctuation come off; a request refused before any run says so on each card ("Not
started ... Nessa didn't ask the model") instead of "Nothing from it was kept"; "employers
want/need" is kept and listed as a known false positive for careers work (H-12). The
stored live EXP-01 output (rows 25-26) was re-checked offline with the final checker: all
six suggestions, seven claims and 16 quotations accepted. That check read ESCO's full
records as the evidence file keeps them, not the shortened copy the prompt carried, so a
quotation from beyond the cut would also have passed. No live call. Checks on `c937e6f`:
`make check` exit 0 (608 fast tests; Vitest 204); `make acceptance` exit 0 (195
integration and stack tests, the Storybook build, 22 Playwright journeys, the demo
journey's fixture note among them); the answers-too-short note recaptured at three sizes,
every shot's checks clean (31 per size).

**Live (R5).** Scope `live-eval-6b`, test model `muse-spark-1.3-contributor`, synthetic
case EXP-01: ledger rows 25 (discovery, 1 request, $0.000205) and 26 (explanation, 2
requests, one repair, $0.000453); $0.000658 in all, 3 of the scope's 9 requests. The
repair's reason is not recorded (errors are classified, messages discarded). Reading the
output by hand: every claim linked a quoted answer to a quoted span of the description,
but the prose sometimes says more than its quotations ("practical outdoor work" quoting
only "practical"), the known limit in decision 12. No production-model call.

**Open (added).**

| Item | Owner | State |
|---|---|---|
| H-12: the note's word lists and phrasings, the content-word rule, bounds, the first-view slate, Try again only for a run that reached no model, asking without a click | Reviewer and product owner | Not run — requires human (ADR 0007 checklist) |
| H-01: the note's wording, its place above "How Nessa found it", the missing-note notice and its length on a phone | Product owner and design reviewer | Not run — requires human |
| Prose that says more than its quotations | Release evaluation, H-12 | Open: only the quoted words are checked, and the note says so |
| The repair rate of the note on the production model | Release task | Not run: one test-model sample only |
