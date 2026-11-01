# Task 6f: no job yet — report

Main tree `/home/user/careerwright`, branch `claude/confident-ramanujan-ux3saw`, on 0118ea0.
Migration **0040** (`r0040_work_status_and_qualifications.py`, `down_revision = "0039"`). DBOS
`application_version` unchanged (`careerwright-l0-1`): no workflow or run kind changed.
Interview prompt `interview-turn-4` → `interview-turn-5`. Support policy unchanged
(`support-policy-11`).

## Commits
- `cb75949` Backend: the `no_job_yet` answer, saved answers v4 (`work_status`,
  `qualifications`), migration 0040, `POST .../origin/role/no-job-yet`, the interview contract
  and `interview-turn-5`, the demo interviewer, INT-15 offline, regenerated client.
- `7b06083` Web: the first question's button, What we know, the opening, Directions' words,
  "Show me suggestions" without a role, ESCO named at the start (design I1), the browser test.
- `0355ec8` ADR 0006 and ADR 0007 amendment lines.
- last commit: the register rows and this report.

## What was built, by the card's bullets

### "I haven't had a job yet" (decision 1; STATE-11)
- **Ruling: a field state, not a value.** `FieldState.NO_JOB_YET = "no_job_yet"`, valid for the
  current role only (`checked_input` refuses it elsewhere: `VALIDATION_FAILED`,
  `not_this_field`). It carries no value, so it is never a job title, and it is distinct from
  Skipped and Unknown. Any non-"unasked" state is an answer, so the world's light comes on
  (`world/model.ts` unchanged) and the demo's role question (asked only while "unasked") is
  never asked again.
- First question: "I haven't had a job yet" beside "Skip for now" (same row), hidden only while
  the person is fixing a title they gave. It calls `POST /v1/workspaces/{id}/origin/role/no-job-yet`
  (`NoJobYet{expected_version}`, Idempotency-Key, `run_idempotent`, the one write path
  `commit_profile_version`, a direct-entry source; 201 new, 200 unchanged, 409 stale). The start
  then goes to "How would you like to start?" with focus there; no origin is fetched.
- What we know: the current role's state control offers it (straight after "Answered"); no
  other field does. It reads "I haven't had a job yet", is styled as an answer, and never gets a
  "less precise without it" line (also not in the Skills place's "Uses these answers").
- Interview contract: `AnsweredState.NO_JOB_YET`; the model may propose it for the role only.
- Demo: "I haven't had a job yet", "I've never had a job", "I have never worked" propose it;
  "I'm a student/pupil/carer" is read as what they are doing now, never as a role.

### Two optional answers (decision 2; PROF-13)
- `work_status` (working, in_education_or_training, looking_for_work, caring, other) and
  `qualifications` (list of `QualificationAnswer{name, status: achieved|expected}`, at most 8,
  duplicates by name refused). Skip, Unknown and Prefer not to say as for every field; neither
  is a hard constraint. Saved answers schema **version 4**; older documents read as v4 with both
  unasked.
- **Migration 0040** rewrites every stored `profile_versions` document to v4, adding both (and
  any older version's later fields) as `{"state": "unasked"}`; every other answer, value and
  source is kept exactly. Ruling: an in-place rewrite of history rows, because the dispatch asks
  for a migration and the rewrite only adds fields that read the same as before (see concerns).
- Interview contract: `ProfileField.WORK_STATUS`/`QUALIFICATIONS`; the model writes a work status
  as its code (always shown as a reading, "inferred") and a qualification as
  `"achieved: …"`/`"expected: …"` (its name "stated" only when quoted in the cited messages).
- Demo patterns: education/looking/caring phrases → work status; "doing/taking/studying …
  A-levels/GCSEs/BTEC/…" → expected, "I've got/passed …" → achieved; "I help/volunteer …" →
  evidenced tasks. The demo never asks either question (so neither is asked twice); the live
  instructions ask for each at most once, a skip accepted, and never the person's age.
- What we know: "What you're doing now" (a select, "Choose one" until chosen) and
  "Qualifications" (name + "Achieved or expected?" select; **neither status is picked for the
  person**, and an unmarked one is refused with "Mark each qualification achieved or
  expected."). An expected qualification reads "A-level biology (expected, not achieved yet)" in
  What we know, the review tray, the source drawer and the stale notice.
- The support screen reads a new qualification's name as typed words (What we know and the
  review step); a work status is a choice, with no words. Ruling: same place, same screen, so
  `support-policy-11` is unchanged.

### The opening works without a job (decision 4; PROF-14)
- Explore opening (web `OPENING_QUESTION.unsure` = demo `UNSURE_QUESTION`): "What would you like
  your working life to be like?" (a proposal for session W2).
- "this change" → "your next step" (demo spend question; the spending-limit hint; the live
  instructions say "their next step").
- Example replies: opening "I help run a youth football team" (not a job; the demo notes it as
  something they've done), enjoy question "I enjoy helping people", role question adds "I haven't
  had a job yet".
- Demo: an unsure person is asked next "What do you enjoy doing, at school, at work or in your
  own time?" (before the practical questions). Entry not chosen keeps the old order.
- Live instructions gain the brief's line verbatim, plus the field formats; `interview-turn-5`.
- "Show me suggestions" (live) no longer waits for a current role.
- Suggestions: with no role, "Closer to what I do" isn't offered; the close group (made only by
  named roles then) is "Close to the roles you named", never "Close to what you do now"; the
  unknown-work note loses "yet" and is never shown after "I haven't had a job yet".
- Every new sentence is worded in the web (R11): the API carries the state and codes only.

### Design I1 (ESCO at the first question)
- The type-ahead's partial question: "Careerwright couldn't match that title in ESCO, the EU's
  list of jobs and skills. Is it one of these?"; the closest step: "…looked up the occupations in
  the group it's in, in ESCO, the EU's list of jobs and skills."; the role list's summary in What
  we know: "The 24 skills that ESCO, the EU's list of jobs and skills, lists for this kind of
  work" (its intro no longer repeats the naming).
- Not changed: the type-ahead's per-option mark "In ESCO as …" (shown only when a picked label
  differs from ESCO's title) and the kept-role line. Both appear after or beside one of the named
  places in most paths; a person who presses Enter on own words before any partial list sees ESCO
  only in "It couldn't match it in ESCO or the UK job-title index…" unexplained. I kept the
  phone's first screen in mind (each naming adds about one line); UI-12's phone checks couldn't
  run here.

### Childline (decision 9; PROF-15)
Held back by the dispatch: nothing added, no placeholder, no policy line, version unchanged.
PROF-15 stays open: its details must come from Childline's own website, which the controller
couldn't reach from this machine.

### Evaluation
INT-15 (new, `demo: true`, not live): "I haven't had a job yet. I'm in Year 13 doing biology and
chemistry A-levels." on the unsure entry: role `no_job_yet`, work status, an expected
qualification, no invented money, current role not missing, one question about what they enjoy,
none about a job. A new `Case.demo` flag and `observe_interview_demo` run it offline on the demo
interviewer through the same check (`tests/eval/test_evaluation.py`); a new `state_is` check.
The school leaver's 4–6 cases and the live run are Task 6e's.

## Rulings
1. `no_job_yet` is a field state for the role only (not a value, not a separate field).
2. A dedicated first-answer endpoint (`origin/role/no-job-yet`) beside the other first-answer
   commands; What we know and proposals use the same `commit_profile_version`.
3. Migration 0040 rewrites stored documents in place (additive, values unchanged).
4. The demo never asks the two new questions; it notes them from phrases (never asked twice).
5. The enjoy question only for the "Help me explore" entry; an entry not chosen keeps the old
   order (so existing None-entry behaviour stands).
6. A qualification's status is never defaulted in the form.
7. "Close to the roles you named" for the close group without a role (the slate's rules
   unchanged; web words only).
8. Support policy version unchanged (no new screened place; Childline held back).
9. Python class `QualificationAnswer` (not `Qualification`): `capability.readiness` already has a
   `Qualification`, and the OpenAPI names must stay unique.

## Checks (on the final code)
- `export PATH=/opt/node24/bin:$PATH; env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`:
  **rc 0**. ruff format (370 files) and lint clean; mypy clean (370 files); pytest **1,773
  passed**, 8 skipped, 421 deselected; fixture validator passed; generated client current; Biome
  clean (153 files); `tsc` clean; Vitest **43 files, 456 passed**.
- `make acceptance`: **not run, Docker down** (never started).
- Integration tests written, **not run (Docker down)**: `test_migrations.py::test_0040_…`,
  `test_origin.py::test_i_havent_had_a_job_yet_is_saved_…`,
  `test_origin.py::test_what_the_person_is_doing_now_and_an_expected_qualification_round_trip_both_ways`,
  and the changed pin in `test_interview_choices.py`.
- Browser test written, **not run (Docker down)**: `e2e/role-space.spec.ts` "[STATE-11][PROF-14]
  “I haven't had a job yet” lights the world within ten seconds…" (the light within 10 s, how to
  start focused, the explore opening, the enjoy question, What we know's answer, no external
  request). Other e2e specs' words updated, also not run.
- `pnpm run review-screenshots`, Storybook build, design-reference screenshots: not run (need the
  stack or were not needed: no design reference changed).
- Human-only: session W2's judgement of every new sentence, the opening and the button: not run —
  requires human. VoiceOver, Safari: not run — requires human.

## RED then GREEN
- `test_profile_document.py`: RED as an import error (no `VERSION_4_FIELDS`), then 49 passed.
- `test_interview_contract.py`: RED 45 failed (`'work_status' is not a valid ProfileField`), then
  47 passed (after the two pin updates below).
- `test_interview_agent.py`: with only `ENJOY_QUESTION` defined, 6 failed (the entry, the open
  question, the example walk, the no-job, the opening and the phrases tests); then GREEN (after
  the `EARLY_ANSWERS` setup change below).
- `test_entered_words.py`: RED against the old `commands.py` (a `QualificationAnswer` and a
  `WorkStatus` returned as words), GREEN after.
- `readiness.test.ts`: RED (1 failed) with the old `readiness.ts`, GREEN after.
- `conversation.test.ts` (live "Show me suggestions" without a role): RED 1 failed, GREEN after.
- `Directions.test.tsx`: RED 2 failed (the note's words; "Close to the roles you named"), GREEN.
- `ProfileEditor.test.tsx`: written after the components; RED shown by running them against the
  committed `fields.tsx` and `ProfileEditor.tsx` (2 failed), GREEN with the new ones.
- `FirstQuestion.test.tsx`: the two button tests RED (no button), GREEN after. The I1 wording was
  changed in `vocabulary.ts` before its tests, so its RED is only the old-words test failing.
- `profile.test.ts` and `YouChapter.test.tsx`'s new start test: written after the code; not
  shown RED.
- The browser test: written, not run.

## Changed test inputs and assertions (disclosure)
- Every web document fixture (12 files): `schema_version` "3" → "4", plus `work_status` and
  `qualifications` unasked (the type requires them).
- `test_profile_document.py`: the v1 and v2 read tests expect `schema_version == "4"` (was "3").
- `test_interview_contract.py:503` and `test_interview_choices.py:91`: pinned prompt version
  `interview-turn-5` (was 4).
- `test_interview_agent.py`: the unsure-entry tests expect the enjoy question after the opening
  (was the role question); the None-entry line now checks the role question directly (it was
  "None equals unsure"); `EARLY_ANSWERS` includes `enjoyed_tasks` (an unsure person is now asked
  it first); the example-reply mirror and walk follow the new examples (three picks).
- `test_openapi.py`: the published list bounds include `qualifications`.
- `profile.test.ts`: the round trip includes the two new fields; the list-bound test includes
  `qualifications`.
- Words: `FirstQuestion.test.tsx` and `discoveryWords.test.ts` (partial question, closest line,
  role list summary and intro), `Directions.test.tsx` (the note without "yet"), `YouChapter.test.tsx`
  (opening words, "your next step", the opening's examples), `TitleDetails.test.tsx` and the
  `Conversation` story (summary), e2e `conversation`, `keyboard`, `role-space`, `visual` (opening,
  partial question, summary regex, "your next step"; `conversation.spec.ts` now expects 6
  questions before the role question, the enjoy question added).
- New tests are listed in the register rows. Support-screen inputs: none new (no distress text).

## Live calls
None. No web request, no model call, no Docker.

## Incidents
- One shell heredoc (`cat >>`) appended the first draft of the document tests. I reverted it at
  once (`git checkout --` on that file) and re-added the same tests with Edit. Every other source
  change used Edit or Write; Biome (`biome format --write`) and the client generator formatted or
  wrote files as the project's tools.
- `git stash push -- <file>` / `pop` was used three times to show RED against committed code; each
  pop restored the working file (checked with `git status`).

## Concerns
- **Migration 0040 rewrites history rows in place** (the table is append-only by convention). It
  adds unasked fields only, but a reviewer may prefer read-time defaults alone.
- A stored receipt of an older profile write (replayed with the same Idempotency-Key) returns the
  v3-shaped document without the two new fields; the web would meet it only on a replay.
- The phone's first screen at the partial question now has one more line (I1); UI-12's phone
  checks couldn't run.
- The live prompt is changed but unqualified until Task 6e's capped run; its instructions grew by
  about 600 bytes (the bound test passes).
- If the person had chosen "Closer to what I do" and then their role stops being known, the
  emphasis stays applied while its button is hidden (edge case; not fixed).

## Questions for the product owner (plain words)
1. Is "I haven't had a job yet" the right label for the button? (The words are yours; yes keeps
   them.)
2. Is "What would you like your working life to be like?" a good first question when someone
   wants to explore? Yes keeps it.
3. Is "Close to the roles you named" clear for suggestions near a role someone wants, when they
   haven't had a job? Yes keeps it.

## Paths a reviewer can skip
`apps/web/src/generated/**` (regenerated client).

# Fix round 1 (the only one, R16)

Commits on `claude/confident-ramanujan-ux3saw` (from 9ef9e51):
- `935b04b` a status is always a reading; the demo never reads a retake or a fail as achieved;
  ADR 0006 records 0040's in-place exception (I1, I2, M1)
- `29727f5` Closer to what I do resets to Balanced once it isn't offered (M3)
- `3d136e3` Register: PROF-13 and PROF-14 name the new tests (last commit)

Every source change used Edit; no heredoc, no stash, no generator was needed (no API change).

## I1: a status the person never said is never "You said"
- Fix: `profile/interview.py` `_basis` returns `inferred` for every `qualifications` and every
  `work_status` change (the status is always Careerwright's reading). The qualification-name
  quoting branch and its helper `_held_name` (now unused) are removed.
- ADR 0006's amendment now says: a qualification's status and a work status are always shown
  as Careerwright's reading, never as "You said", even where the words appear in the cited
  messages.
- Test (new): `test_interview_contract.py::test_a_status_the_person_never_said_is_never_shown_as_their_words`,
  the review's two reproductions ("I am taking A-level biology this year." with `achieved:
  A-level biology`; "working" from "I am working towards my A-levels.").
- RED: `basis` was `stated` for both (pytest: `<Basis.STATED> is <Basis.INFERRED>`; the work
  status checked directly through `check_turn`, `stated`).
- GREEN: both `inferred`.
- **Changed assertion (disclosed):** `test_a_qualification_is_proposed_achieved_or_expected_stated_only_from_their_words`
  asserted `Basis.STATED`; it now asserts `Basis.INFERRED` (the status is a reading, the
  review's fix). Its name is unchanged; the rest of the test is unchanged.
- Ruling: in the model path, code doesn't decide whether a status is achieved (that would be a
  new language rule). "Never achieved without their words" is met by never vouching for the
  status: the person sees it as Careerwright's reading and confirms or changes it. The demo
  path's patterns are fixed under I2.

## I2: the demo never reads a retake or a fail as achieved
- Fix: `profile/fixture_interviewer.py` `_ACHIEVED` takes only an explicit verb ("I got",
  "I've got", "I have got", "I passed", "I've passed", "I have passed"), never a bare "have",
  and never "got to …". A message mentioning a retake, a resit or a fail (`_NOT_ACHIEVED`) is
  never read as achieved; an expected qualification ("I'm taking …") is still read as
  expected. Nothing newly matches (the patterns only narrowed).
- Test (new): `test_interview_agent.py::test_the_demo_never_reads_a_retake_or_a_fail_as_achieved`,
  four sentences: the review's two ("I have to retake my GCSE maths.", "I have failed my GCSE
  maths.") and two of mine ("I've got to resit my GCSE maths.", "I got a U in GCSE maths, so I
  failed it.").
- RED: all four gave `achieved: …` (`to retake my GCSE maths`, `failed my GCSE maths`,
  `to resit my GCSE maths`, `a U in GCSE maths`).
- GREEN: no achieved proposal for any. The existing demo test ("I've got GCSE maths and
  English." achieved) still passes unchanged.

## M3: "Closer to what I do" goes back to Balanced once it isn't offered
- Fix: `Directions.tsx` `Slate` computes whether work is known before the slate query; if the
  emphasis is "practical" and work isn't known, it sets the emphasis back to Balanced during
  render, so the next slate request asks for `emphasis=balanced` and Balanced shows pressed.
- Test (new): `Directions.test.tsx` "[PROF-14] resets Closer to what I do to Balanced once it
  isn't offered, so no hidden view stays applied": choose it with a role given, then re-render
  with "I haven't had a job yet".
- RED: Balanced's `aria-pressed` stayed "false".
- GREEN: Balanced pressed, the button gone, the last slate request `emphasis=balanced`.

## M1: the append-only record
- ADR 0006's amendment gains one line: migration 0040 adds the two not-yet-asked answers to
  stored documents in place, the one exception to append-only saved answers. No code change.

## Listed, not fixed now
- M2: a replayed receipt from before migration 0040 returns a document without `work_status`
  and `qualifications`; the web reads `document[name].state` for every field, so that replay,
  put into the cache, would throw. It needs the same Idempotency-Key retried across an
  upgrade, very unlikely locally. For the final review.
- M4, M5, M6, M7: for the final review and session W2's sheet.

## Commands and results (final code)
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` after each change; the last run,
  after the register commit: exit 0; backend 1,794 passed, 8 skipped; Vitest 43 files, 457
  tests passed; ruff, mypy, Biome, `tsc`, client drift and the fixture validator clean. (One
  earlier run failed on ruff PT018 in my new test; split the assertion and re-ran.)
- Focused: `backend/.venv/bin/python -m pytest -q tests/domain/test_interview_contract.py
  tests/domain/test_interview_agent.py` (79 passed); `pnpm exec vitest run
  src/components/Directions.test.tsx` (34 passed).
- Not run: integration, `make acceptance`, Playwright and captures (Docker down). No live
  calls (no cost). Session W2's words: not run — requires human.

---

## Follow-up: Childline

Worktree `/home/user/careerwright-wt/childline`, branch `wt-childline`, rebased onto
`claude/confident-ramanujan-ux3saw` (58c8f99). Commits: `69828b9` (Childline in the panel)
and `6104a86` (register, last).

### What I built
- `careerwright/profile/safety.py`: a fifth service after Shout, `support-policy-12`:
  "Childline: Call 0800 1111 or use the 1-2-1 chat online (free, 24 hours a day, 7 days a
  week). For children and young people." Source URL
  `https://www.childline.org.uk/get-support/contacting-childline/` (the page checked);
  `checked_on` is `CHILDLINE_CHECKED_ON = "2026-11-01"`, its own date. `REVIEW_STATUS` names
  Childline's line as added on 2026-11-01, not yet reviewed as built. Every detail is one the
  checked file marks verified; no age limit (not verified), and no other Childline detail
  (message service, BSL, languages, 999, NSPCC) was added, to keep the line as short as the
  others.
- Every place the panel shows builds it from `SupportNoteOut` over `SUPPORT_RESOURCES`, so
  Childline shows in all of them; no API shape change, so the generated client is unchanged
  (drift check clean).
- `SupportNote.tsx`: the footnote used the first service's date for all. With Childline
  checked on another day that would have been untrue, so it now names any service checked on
  another day: "These services were checked on their own websites on 28 October 2026, and
  Childline on 1 November 2026." One date still reads as before.
- ADR 0007: an amendment line for `support-policy-12`, naming the checked file.
- Session W2: item 7 and record row S7 are one yes/no line showing the panel's new words,
  not run — requires human.
- Register: PROF-15 implemented; its review not run — requires human.

### Rulings
1. **No link is drawn in the panel.** The panel shows no links for any service today (only
   words); "its https link" is met as the resource's `source_url`, https, which tests check.
   I used the page the details were checked on (the field's meaning for every other
   service), not the 1-2-1 chat page. Making the chat a tap-through link would add an API
   field and change the panel's design for one service: a question for the controller or
   session W2, not taken here.
2. **"Free" covers both call and chat** in the line's bracket, from the verified "You can
   call us for free on 0800 1111 or speak online using the 1-2-1 chats" and the "We're free
   and confidential" heading. If the controller reads "free" as verified for calls only, the
   bracket can move to after "0800 1111".
3. **Order:** Childline last, after the four existing services.

### Checks
- RED first: the new and updated tests in `tests/domain/test_safety.py` and
  `tests/api/test_support_note.py` failed (7 failed) before the change; GREEN after (167
  passed). `SupportNote.test.tsx`: the two-dates footnote test failed first, then passed.
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH), before and
  after the rebase, and after the register edit: exit 0; backend 1,866 passed, 8 skipped;
  Vitest 45 files, 471 tests; ruff, mypy, Biome, `tsc`, client drift and the fixture
  validator clean.
- Tests added: `test_safety.py::test_childline_is_listed_for_children_and_young_people_in_its_own_checked_words`
  (policy version pinned, no age), the resources test updated; `tests/api/test_support_note.py`
  (every `SupportNoteOut` place: sent, refused, title, entry saved and refused; five services,
  Childline's words, https link, version 12); `SupportNote.test.tsx` (three).
- Written, not run (the controller runs integration and acceptance):
  `test_interview_choices.py` (SERVICES has Childline, version 12, every link https; reused by
  `test_role_space.py` and `test_workspaces_and_profiles.py`), `conversation.spec.ts` and
  `role-space.spec.ts` (the panel contains "Childline: Call 0800 1111"), and the visual
  review's panel fixture (`visual.spec.ts`).
- No web requests, no live calls (no cost), no Docker.

### Concerns
- The visual review fixture's other fields were already stale (policy 7); I only added
  Childline to it.
- Review status: not run — requires human (H-12, session W2, S7).
