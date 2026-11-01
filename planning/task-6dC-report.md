# Task 6d, slice C: report

The real role beside ESCO, and the rest of the card. Main tree, branch `l0-local-release`, on
51ca593. Migration **0039** (`r0039_title_details.py`, `down_revision = "0038"`). DBOS
`application_version` unchanged (`careerwright-l0-1`): no workflow or run kind changed.

## The card's bullets, each with its tests

### 1. The unexpected connection: "Always a plain line" (the product owner, 1 November 2026)
- **Ruling: the rule that picked the connection is removed.** A plain line about the two roles
  is already on every suggestion the role's join found ("Your current role: “…”. ESCO lists 12
  of the same essential skills for both, so Careerwright joined them by those skills." and the
  skills named under it). A plain line needs no rule that singles one suggestion out, and that
  singling-out was what made it a moment. So `slate.unexpected_connection`, `Connection`,
  `exploration.ConnectionView`/`_connection`, `ConnectionOut`, `SlateOut.connection`,
  `OriginOut.connection`, the web's "An unexpected connection" kicker and its "hasn't compared"
  line, `.suggestion-kicker`, and the evaluation checks `connection` and `no_connection` are gone.
  `taxonomy_store.shared_essential_skills` was used only by the connection; its query moved into
  the one test that used it as an oracle.
- The slate is unchanged: the comparison against the slates recorded before Task 6d still passes
  with the recording's `connection` key left out (the JSON file is unchanged).
- The Roles chapter's moment: not invented. The design reference's Roles panel keeps the plain
  fact without the kicker, and `docs/design/README.md` says Task M chooses the moment again.
- Recorded in ADR 0015 (slice C line, decision 4) and ADR 0007 (slice C line, decision 14).
- Tests: `test_origin.py::test_the_origin_shows_usual_skills_and_destinations_joined_by_shared_skills`,
  `test_discovery.py::test_a_role_esco_does_not_list_is_reported_never_searched_by_its_words`,
  `test_first_answer.py::test_the_first_answer_changes_the_world_within_one_second_on_the_pinned_release`
  (each: `"connection" not in` the response);
  `Directions.test.tsx` "[MAP1-09] states the skills a suggestion shares with the role as a plain
  line, never as a discovery…" (no "unexpected" or "connection" on the card).

### 2. The other two ESCO fixes
- **ESCO's list is ESCO's.** "ESCO lists these for this kind of work:" (`ESCO_LISTS`) in the
  sketch and a chosen target's card; the coverage line "Careerwright can show the skills ESCO
  lists for this kind of work…"; the loading line; the world's caption "ESCO lists it, not
  confirmed yet" and key "Faint ring: ESCO lists it for this kind of work, not confirmed yet"
  (was "usual in your role"); the role's list in What we know. Backend docstrings and the API
  description of `UsualSkillOut` say whose list it is; the code `usual_in_role` keeps its name
  (a code, not words; renaming it would break the contract for no reader).
- **ESCO named plainly** where a view first shows its list: `ESCO_NAMED` = "ESCO, the EU's list
  of jobs and skills", in the suggestions' header line ("Occupations from ESCO, the EU's list of
  jobs and skills, found from your answers. Ideas to test, not a judgement of fit."), once at
  the top of the sketch ("Careerwright looked up each target in ESCO, the EU's list of jobs and
  skills."), and in the role's list ("ESCO, …, lists these as essential for this kind of work.
  Careerwright hasn't compared them with your own experience."). My first, longer naming ("the
  European Union's public list of occupations and skills") pushed the suggestions' first
  decision 10 px out of a phone's first screen (acceptance run 1, UI-12), so it is shorter, and
  the header lost "no score or percentage" (it keeps "not a judgement of fit"). Not explained:
  the start's type-ahead and closest step, which name ESCO but list no skills.
- **"Not part of my job"** (display state, per role): beside the person's own role only, in What
  we know, one step away ("The 70 skills ESCO lists for this kind of work"), each skill with a
  toggle button (`aria-pressed`), and "You said this isn't part of your job. Careerwright
  doesn't use it to check anything." Stored in `title_details.not_part_of_job` (below); the
  origin's `usual_skills[].not_part_of_job` carries it; the state stays `usual_in_role`; nothing
  else reads it (no evidence, readiness, slate, strength). Only a skill ESCO lists as essential
  for the title's one occupation can be marked (`not_listed` otherwise); only a newly marked
  skill is checked, so a mark made for an occupation the person later let go never blocks a
  later save (found in self-review: RED, then fixed).
- **No revelation rests on ESCO's essential skills alone** — checked:
  - the unexpected connection: now a plain line (above);
  - the overlooked strength (`capability/strength.py`): the model quotes the person's own answer,
    code verifies the quotation as a span of their answers and the skill as essential to a
    destination, and the person confirms it; it rests on their verified words, so it passes;
  - the slate's suggestions are suggestions, not revelations (ADR 0007 decision 5, R11 frozen);
  - no other revelation is built (routes, Task 14; moments, Task M).
- Tests: `SketchCard.test.tsx` "[MAP1-09] calls a target's skills ESCO's list…" (RED then GREEN),
  `Directions.test.tsx` "[PROF-10] says a chosen target is saved…" (RED then GREEN, words and no
  "usually"), `World.test.tsx` (RED then GREEN, no "usual"), `discoveryWords.test.ts` (words),
  `TitleDetails.test.tsx` (marks), `test_title_details.py::test_a_skill_marked_not_part_of_my_job_is_a_display_state_never_evidence`
  (no `skill_evidence` row, capability version and destinations unchanged, an unlisted skill
  refused, unmark), `e2e/role-space.spec.ts` "[PROF-11] seniority and industry beside the role,
  and a skill ESCO lists marked not part of my job, in the demo", `e2e/conversation.spec.ts`
  (ESCO's list words and the sketch's plain naming).

### 3. Optional seniority and industry
- **Where they live (ruling):** a new append-only table, `title_details` (migration 0039), one
  version per save, keyed by workspace, use (`role` or `target`) and the title as a concept
  (`careerwright.concept_key`). Not the title's record (`target_records`): a role and a target can
  share a record (one per title as a concept), but a person may target their own title at another
  seniority. Not the profile document: targets are a list of strings, and per-target fields would
  change the document's shape, the interview contract's field list and its prompt (which can't be
  qualified live here).
- **API:** `GET .../profile/titles` (`TitleDetailsListOut`: the role first, then the targets, each
  with `seniority`, `industry`, `not_part_of_job`, `version`, 0 while none saved) and
  `PUT .../profile/titles` (`SetTitleDetails`, expected version and Idempotency-Key through
  `run_idempotent`; 201 a new version, 200 unchanged; 409 stale; 422 `not_your_title` for a title
  that isn't the person's role or one of their targets, `not_listed` for a mark ESCO doesn't list).
  New event kind `profile.title_details_updated`. Codes and values only (R11): the web words them
  (`TITLE_DETAILS`, `TITLE_USE: Record<TitleUse, string>`).
- **Unknown is shadow, never a default:** null when not given; the web says "Seniority and
  industry: not given." / "Seniority: Band 6. Industry: not given.".
- **Matching ignores them:** nothing in the slate, sketch, records, Skills or the strength reads
  the table. Test: the origin's role and destinations are identical before and after a save.
- **Display keeps them:** What we know, "Seniority and industry", beside each title the person
  gave, with "Add (or Change) seniority or industry for …" opening two optional fields.
- **Search keeps them (ruling):** they are kept beside the title for the job search that takes a
  target title (Task 8, the Roles chapter). Today's source search (`evidence/search.py`,
  API-only, no web caller) still sends a target title and a city only (ADR 0009 decision 12);
  widening what it sends is a search-contract change I left to Task 8.
- **The interviewer doesn't propose them yet:** recorded in PROF-08 (a prompt change needs a
  live qualification).
- Tests: `test_title_details.py` (five tests: kept beside each title, matching ignores them,
  stale, unchanged 200, per title as a concept, `not_your_title`, marks as a display state, a
  kept mark never blocking a later save, the support screen), `TitleDetails.test.tsx` (five
  tests, focus after a save included), `discoveryWords.test.ts`, `e2e/role-space.spec.ts`, the
  story `You › What We Know Title Details`, the review capture `you--title-details`.

### 4. Pasted CV text: deferred (PROF-12)
Not small, so it is an L0 deferral (plan section 1, ADR 0015's slice C line, PROF-12 deferred,
PROF-07's Task 6d part closed as deferred). Each "small" condition, checked against the code:
- *Reuses the proposal path and review tray, no new run kind:* only by putting a CV through an
  interview turn, whose message is at most 2,000 characters (`interview.MAX_MESSAGE`) and whose
  prompt is at most 8,500 bytes with five earlier messages kept (`MAX_PROMPT_BYTES`,
  `HISTORY_MESSAGES`). A CV is longer, so every turn's bounds and spend reservation would grow,
  the CV would ride in the next five turns' context, and the prompt would need new instructions
  that can't be qualified without live calls (none allowed here).
- *Third parties' contact fields removed before anything is sealed:* a message is sealed as typed.
  Removing a CV's referees' emails, phone numbers and contact fields needs a separate pasted-CV
  input (it must not rewrite an ordinary message), with its own redaction tests.
- *Works in the demo:* the fixture interviewer reads a few fixed sentence shapes ("I am a …",
  "I enjoy …"), so it would find almost nothing in a CV; a demo CV reader is new code.
- *The product owner's direction (1 November 2026):* many people will be final-year school
  students who have never had a job and often have no CV. That weighs toward deferral too.

### 5. Carried from slice B's reviews
- **"Every place a person types":** the answers typed in the conversation's review step (a
  decision's `edits`) go through the same screen as What we know's direct entries: the route
  screens the words the edits add against the version the decision was made against
  (`commands.entered_words`, generalised to any answers by field), saves as usual, and answers
  `DecisionSavedOut` (with `support_note`) or `DecisionRefusedOut` (the panel beside any
  refusal), derived from the request every time, never stored. The web keeps the panel beside
  the save notice until dismissed (focus to the notice, or the tray). The new seniority and
  industry fields are screened the same way. `support-policy-10`, `REVIEW_STATUS` naming both
  as not yet reviewed as built; the panel's words are the existing `SUPPORT_NOTE_ENTRY` pair.
  Tests: `test_origin.py::test_an_answer_typed_in_the_review_step_goes_through_the_support_screen`
  (demo interviewer; stale 409 with the not-saved panel; saved 201 as typed with the panel;
  receipts hold no support), `YouChapter.test.tsx` "[PROF-09] shows the calm support panel beside
  the save when an answer typed in the review step triggers the screen", `test_title_details.py`
  (screened details: saved with the panel; unchanged words don't bring it back; a replay the same
  answer; a stale save with the not-saved panel), `TitleDetails.test.tsx`.
- **R2-M1, the phone's first screen:** `SupportNote` renders its `actions` right after its line,
  before the services (Dismiss stays last), so "Keep it as my job title" is next to the line that
  names it. Tests: `FirstQuestion.test.tsx` (document order: line, then Keep, then the services
  list), `e2e/role-space.spec.ts` phone test at 390 × 844 (Keep below the line, above the
  services, inside 844 px). The review capture `you--title-support--390x844.png` shows it.

## The world's words and the design references
- `docs/design/compositions/world.js`: the You console's skills line "ESCO lists these skills for
  records officer work. …" (was "Records officers usually need these skills"), the Skills place's
  "ESCO lists it for this kind of work, not confirmed yet", the key's two lines, the caption
  "ESCO lists it, not confirmed yet" (the longer caption made one label unplaceable at
  768 × 1024: "the light skill:s4 is in view without a name"; the short caption fixed it), the
  Roles panel's plain line with no kicker, the sketch's summary line.

## Commits
- `bb5045f` Shared skills as a plain line, and ESCO's list named as ESCO's (the connection
  removed; wording; design references' words).
- `0cedc22` Seniority and industry beside a title, "not part of my job", and every typed answer
  screened (migration 0039, API, web, R2-M1).
- `65750d8` support-policy-10 and the design references' ESCO words (captures 46/46).
- `3055e92` The world's label for a skill ESCO lists, short.
- `e40a846` Review captures (title details, title panel, slate shots) and the new visual shot.
- `dc68d79` ADRs 0015, 0007 and 0012.
- `561f9f2` Fixes after acceptance run 1 and self-review (shorter ESCO naming, kept marks,
  focus).
- `39d142c` Design reference and review captures for the shorter naming.
- `a9dbe67` ADR 0015's words.
- `8292c6a` The register and the plan (last).

## Checks (on the final code, a9dbe67; the last commit is documents only)
- **`make check`** (after the fixes): exit 0, no warnings. ruff format (367 files) and lint clean;
  mypy clean (367 files); fast pytest **1747 passed**, 416 deselected (4 connection tests
  removed); fixture validator passed; the generated client matches; Biome clean (153 files);
  `tsc` clean; Vitest **442 passed** (43 files).
- **`make acceptance`**, each one guarded command under the lock, the whole run each time:
  - **Run 1** (07:59–08:20, on dc68d79): backend integration and stack **432 passed**; Storybook
    built; Playwright **58 passed, 3 failed**: UI-12's phone first screen ("Make this a target"
    at 854 > 844, caused by my longer ESCO naming: fixed in 561f9f2) and two WLD-03 still-world
    names checks (Routes at 768 × 1024, You at 390 × 844: the moving world named nothing where the
    still one named the person and the targets). They passed in runs 3 and before this slice;
    nothing in this slice touches the world's names or the Routes chapter, so I read them as
    timing under load, not a defect.
  - **Run 2** (08:39–08:51, on a9dbe67): backend **413 passed, 20 errors**, all at the setup of
    the stack and owner-command fixtures: `docker compose up --wait` reported the test stack's
    acquisition container unhealthy. Nothing in this slice touches the acquisition worker (it
    can't import profile code: the architecture test); the containers were torn down, so no log
    was left. Make stopped before Storybook and Playwright.
  - **Run 3** (08:51–09:10, on a9dbe67): **exit 0**. Backend integration and stack **433
    passed** (11 m 48 s); Storybook built; Playwright **61 passed** (7.4 m), the new role-space
    journey and phone check, UI-12 and both WLD-03 checks included.
- **Focused runs under the lock** while building: the RED run (7 failed), the GREEN run (102
  passed), the kept-mark RED (1 failed, 4 passed) and GREEN (5 passed), two e2e runs of
  `conversation.spec.ts` and `role-space.spec.ts` (15 of 16, then the phone first screen 2 of 2).
- **Design references**: `pnpm run contrast` 132/132 pass (no new colour pairing: the new view
  uses the existing text, field and button tokens); `pnpm run screenshots` 46/46 pass (the first
  run failed one label, "the light skill:s4 is in view without a name", from my longer caption,
  fixed with the short caption). I kept the captures my composition changes touch (the world's
  key and captions appear across the You, Skills, Roles and Options places, and the Roles panel
  and the suggestions' header changed); the mirror `apps/web/src/design` is unchanged and
  byte-identical (`diff -rq`: only the unmirrored files differ, as before).
- **Review captures** (`pnpm run review-screenshots`, under the lock, run three times: the first
  failed on my own shot's toggle name, which a browser reads as "Not part of my job : …"; then 4
  passed twice). Kept: the new `you--title-details` (3 sizes), `you--title-support` (3; the Keep
  choice above the services), the slate shots and the source drawer shots (the suggestions'
  header names ESCO). Restored every other capture the runs rewrote (rendering noise) and the
  four `checks-*.json` files, as slice B did, and removed the uncommitted ones the run writes.

## Rulings I made
1. The connection rule is removed, not kept (bullet 1).
2. Seniority, industry and the marks live in one new append-only table, per use and title as a
   concept (bullet 3).
3. "Not part of my job" is offered only beside the person's own role (in What we know); the
   record can hold marks for a target, which the Skills chapter (Task 10) offers. So a person
   with no job title never meets "my job" here.
4. "Search keeps them" means kept beside the title for Task 8's job search; today's source
   search is unchanged (bullet 3).
5. The support screen reads only the words a save adds against the version it was made
   against, for both new places, as What we know does (a replay derives the same panel).
6. `support-policy-10`: the two new screened places change the policy's coverage, so its
   version moves and `REVIEW_STATUS` names them; the panel's words are unchanged.
7. The CV is deferred (bullet 4).
8. The world's label for a skill is short ("ESCO lists it, not confirmed yet"); the key carries
   "for this kind of work".
9. ESCO is named in few words ("the EU's list of jobs and skills") because the decision path
   comes first: the longer naming pushed a decision off a phone's first screen.
10. A mark made before stays a display state when the title's occupation changes; only new
    marks are checked against ESCO's list.

## RED then GREEN
- **Backend (one RED run, then one GREEN run, both under the lock):** with `backend/src` checked
  out at the commit before the connection change, the seven new or changed integration tests
  failed: the four `test_title_details.py` tests (no endpoint), the origin and discovery tests
  (`AssertionError: assert 'connection' not in {...}`), and the review-step screening test (no
  `support_note`). Then on the new code: 102 passed (title details, origin, discovery, migrations,
  workspaces and profiles, interview turns, role space).
  - Incident: that RED command ended with `exit $rc` inside `{ … }`, so the `git checkout HEAD --
    backend/src` after it never ran; I then wrote two edits (origin schemas, origin route) on top
    of the old files. I found it when the stack's web build failed (the client had the
    connection again), restored the six files to the committed versions with `git checkout HEAD
    --`, re-applied my two edits with the Edit tool and regenerated the client. Nothing from the
    old versions reached a commit (checked: no `connection` in `discovery_schemas.py`).
- **Web:** the wording tests failed first (3: `SketchCard`, `Directions`, `World`), then passed;
  the review-step panel test failed ("Unable to find role=region … Support is available"), then
  passed; the keep-placement test failed (`expected +0 to be truthy`), then passed.
  `TitleDetails.test.tsx` was written before the component but not run before it existed (its
  RED would have been the missing import), so its RED is not shown.
- **After acceptance run 1 and self-review:**
  - UI-12 (phone first screen) failed in run 1 at 854 > 844; my first shortening (146
    characters) still failed at 854 in a focused e2e run under the lock; the 118-character header
    passed (2 passed, the phone first-screen tests).
  - The shorter ESCO words: 5 web tests failed first (words, the header, and the details form's
    focus test, which failed for the missing focus), then 87 passed.
  - The kept-mark fix: `test_a_mark_kept_from_an_earlier_closest_choice_never_blocks_a_later_save`
    failed (`assert 422 == 201`, "Only a skill ESCO lists for this kind of work can be marked."),
    then the file's 5 passed, with `conversation.spec.ts` and `role-space.spec.ts` (15 of 16;
    the one failure was the phone header above, fixed after).

## Tests and inputs changed (disclosure)
- Removed (the connection rule is gone): `test_skill_joins.py`'s four connection tests;
  `evaluation.py`'s `connection` and `no_connection` checks; those checks in DSC-10, DSC-15 and
  DSC-16, and the words "with an unexpected connection" / "and no connection states a fact about
  it" in DSC-10's and DSC-16's titles (their other checks unchanged).
- Changed assertions: `test_origin.py`, `test_discovery.py` (`connection is None` → not in the
  response); `test_first_answer.py` (the connection's three assertions → not in the response; a
  print line removed); `test_evaluation.py::slate_shape` no longer reads the connection, and the
  comparison leaves the recording's `connection` key out (`slates_before_task_6d.json`
  unchanged); `test_discovery.py`'s shared-skills oracle is now its own SQL (the store function
  went).
- Words: `Directions.test.tsx` (coverage and ESCO list words; the connection test now checks the
  plain line), `discoveryWords.test.ts` (coverage words), `World.test.tsx` (caption and key),
  `e2e/conversation.spec.ts` (ESCO list words, and the sketch's plain naming added).
- `test_interview_choices.py`: policy literal `support-policy-10` (was 9), comment updated.
- Fixtures: `connection: null` removed from `Directions.test.tsx`, `YouChapter.test.tsx` and the
  stories' slate and origin; the story `SlateJoinedBySkillsWithAConnection` is now
  `SlateJoinedBySkills`; `YouChapter.test.tsx`'s `decided` route takes an optional panel; the
  stories' chapter routes answer `GET .../profile/titles` with no titles.
- New: `test_title_details.py`, `test_origin.py::test_an_answer_typed_in_the_review_step_…`,
  `TitleDetails.test.tsx`, new tests in `SketchCard.test.tsx`, `YouChapter.test.tsx`,
  `FirstQuestion.test.tsx` (an added placement check), `discoveryWords.test.ts`,
  `e2e/role-space.spec.ts` (a journey and the phone check), `e2e/visual.spec.ts` (the
  `you--title-details` shot and its workspace).
- Support-screen inputs are the existing fixtures only: `test_interview_choices.DISTRESS`
  (backend) and "I volunteer on a suicide prevention helpline." (web).
- After acceptance run 1: the ESCO naming expectations in `discoveryWords.test.ts`,
  `SketchCard.test.tsx`, `TitleDetails.test.tsx` and `e2e/conversation.spec.ts` follow the
  shorter words; `Directions.test.tsx` pins the suggestions' header; the e2e toggle names are
  matched as `/^Not part of my job\s*:/` (a browser reads the hidden part with a space).
- Test tags: the ESCO-list tests carry MAP1-09 (the row for the three ESCO fixes).

## Incidents
- The RED command's `exit $rc` inside `{ … }` ended the shell before my restore ran (see RED then
  GREEN); fixed by restoring the six files from the commit and re-applying my two edits with
  Edit. No old version reached a commit.
- One stray `python3 - <<'EOF'` that only printed a line ran while I listed connection
  references; it read and wrote nothing.
- `git checkout` and `rm` were used only on captures the runs rewrote or created, and on the six
  files above. Every source change went through Edit or Write (Biome and ruff formatting my own
  files, and the client generator, aside). Commit messages were passed to `git commit -F -` from
  a heredoc; no file was written that way.

## Live calls
None: no Meta, Adzuna or web request, no Docker pull. Docker was already running; test stacks
were started only by the test tooling, each time under the lock.

## Places the app presumes a job (for the controller's no-job check; not changed here)
- The first question and its type-ahead: "What do you do now, or what did you do last?", the
  field "Your job title", "None of these is my job", and the title panel's "Keep it as my job
  title" (`vocabulary.ts` around 913–942). "Skip for now" exists.
- What we know's field "Current role", hint "Your current job title, or what you do now."
  (`vocabulary.ts:177`).
- The demo interviewer's first critical question, "What do you do now, or what did you do most
  recently?" (`fixture_interviewer.py:50`; `CRITICAL` includes the role).
- The kept-role lines "Careerwright keeps “…” as your role…" (`vocabulary.ts` around 762 and 952)
  and the slate's reason source "Your current role" (`vocabulary.ts:648`).
- The sketch's step "Compare these requirements with what you have done" (`vocabulary.ts:987`).
- "Careerwright doesn't know your current work yet…" on the suggestions without a role
  (`Directions.tsx:736`).
- What this slice adds is shown only for a title the person gave: nothing for someone with no
  job title (test: `TitleDetails.test.tsx` "shows nothing for a person who gave no title").

## Not run, open, concerns
- Session W2 judges the new words (not run, requires human); both new screened places and their
  use of the existing lines are not yet reviewed as built (`support-policy-10`).
- A real phone's keyboard over the title panel, VoiceOver and Safari: not run, requires human.
- The workspace export (format 4) doesn't carry title details yet.
- `CLAUDE.md` still lists "an unexpected connection" among the earned revelations; I didn't edit
  `CLAUDE.md` (the controller's). The plan's section 4 names it the Roles chapter's moment
  (the controller has carried that to Task M).
- The world's sound cue "a chime when a connection lights up" (`lib/world/sound.ts`) now has no
  trigger to come; Task M's.
- The start's type-ahead and closest step still name ESCO without explaining it.
- The interviewer doesn't ask for or propose seniority (PROF-08).
- Two WLD-03 still-world checks failed once (acceptance run 1) and passed in run 3; the test
  stack's acquisition container came up unhealthy once (run 2). Both look environmental (the
  machine was slow: the same review-capture run took 1.7 m, then 7.1 m), but I couldn't prove it.
- The role's ESCO list can be long (70 skills for the specialist nurse), one step away in a
  disclosure; session W2 may want it shorter.

## Paths a reviewer can skip
`apps/web/src/generated/**` (regenerated client), `docs/design/screenshots/**`,
`docs/reviews/sprint-2/screenshots/**` (captures).
