# Task W2E report: the You chapter finished, and the Sprint W review

Branch `l0-local-release`, from `ec4d060`. Implementer: Claude (Opus 5.5), main tree. No
subagents, no live model call (cost $0), no web request, no Docker pull, no headed browser or
window, no frame measurement; `.env`, `~/.careerwright`, `~/.nessa`, `spikes/world` and the
running `careerwright-l0-*` stack untouched; `make stop` never run; `answers-2.md` and
`esco_research.txt` never staged. DBOS `application_version` still `careerwright-l0-1` (no
workflow step changed). Docker was used only by the test projects `careerwright-l0-test` and
`careerwright-l0-webtest` (cached images), each time under `.superpowers/acceptance.lock`,
taken with `mkdir` and removed the moment the run ended.

While this task ran, Task A1's documents fix landed in the same tree (`694a10d`..`0931cbb`:
task file, plan, ADRs, register, specification). My commits sit on top of them; nothing
conflicted, and the W2E card's deliverables did not change.

## Status

DONE_WITH_CONCERNS. Every card item and the re-review's open findings (N1, N2, N3, and fix
round 1's two concerns) are implemented with tests; `make check` and one `make acceptance`
(under the lock) pass on `c64b636`, the code of the final candidate (the commit after it
changes documents only). Concerns at the end (one hard-rule slip, the ten-second bar, one
rare demo case).

## Commits

| SHA | Subject (shortened) |
|---|---|
| `8410eff` | The demo interviewer never asks the same question twice, a chosen target keeps its slate current, and each suggestion names the skills it was joined by (backend, client regenerated) |
| `7c3a72b` | The You chapter finished: the demo never loops, a chosen target confirmed in place, shared skills named, the decision first on a phone, the world placed again after every change of view (web, e2e) |
| `c64b636` | Design references: the phone band, the rail marks, Routes not built yet, the strip's controls below a desktop's width |
| `4dcc2ca` | Register, ADRs 0007 and 0014, the Sprint W review (last commit: the register and documents) |

## The re-review's open findings, each with its test

| Finding | Fix | Test (RED, then GREEN) |
|---|---|---|
| **N1** (Important): views switch by `hidden`; the world's observer ignored attributes, so on a tablet or phone the light sat under the console and the key over the console's edge or the Suggestions tab (the audit's F8) | `World.tsx`: the observer also watches `hidden` (and `open`: a disclosure opening grows its panel as much as new children would) | Unit: `World.test.tsx` "measures the panels again when a view is shown or hidden, with nothing added or removed (re-review N1)": RED on the old `World.tsx` ("expected 1 to be greater than 1"), GREEN after. Browser: `e2e/world.spec.ts` "after every change of view the person's light stands above the console, and the key covers neither it nor a tab" at 768 and 390 replaces the test that read a stale `data-shown`: it changes view with no scroll (asserted `scrollY === 0`), then compares the "You" label's box with the console's top, the key's box with the console and each tab, and taps each tab's centre (`elementFromPoint`) for an on-top check. Passed on the new build in both focused runs; not run against the old build (that needs a full stack build of the old tree; the re-review's captures are the defect's evidence) |
| **N2** (Minor, with F7): on a phone the strip's ellipsis cut a stopped state's reason | `globals.css`: only connecting and reconnecting stay on one row with an ellipsis; a stopped state takes its own row under the saved state and the menu (`data-state` on the strip's update item) | `e2e/conversation.spec.ts` "on a phone a stopped update says why in words read whole, not cut off (re-review N2)": the stream answers 404 `NOT_FOUND`, the strip says "Updates: Stopped: access to this workspace ended", its words' `scrollWidth` fits, and the account menu stays. Passed (run 2); not run on the old build |
| **N3** (Minor, with F7): the band's 300 px floor pushed the console off the first screen in a short window | The band is sized to what it shows (144 px, below); a window 560 px tall or less keeps no band and the world stands behind the console | `e2e/conversation.spec.ts` "in a window too short for a band (a phone turned sideways) the console starts in the first screen (re-review N3)" at 844 × 390. Passed (run 2) |
| D-M5 ("Review the latest version, then save again.") | Not touched (that line was not otherwise edited), so it waits for the final review | none |
| Fix round 1's concern 3: "Help me explore instead" dropped keyboard focus | Focus goes to the "Directions to explore" heading that replaces the button | `YouChapter.test.tsx` "moves focus to the suggestions that replace Help me explore instead": RED on the old components, GREEN |
| Fix round 1's concern 4: the moving-and-still identical-words test covered only the fixture workspace | It runs on the fixture workspace and on a talked one (a reply to review, a slate and its written note, waited for before reading) | `e2e/world.spec.ts` "the You chapter says the same in the moving and the still world, in every view" at three sizes. Passed (run 1) |

## Each card item, and how a person sees it now

Captures: the app's from the acceptance run (`apps/web/test-results/visual-<size>-…/screenshots/`,
not committed; written each run) and the design references
(`docs/design/screenshots/`, committed).

1. **The demo conversation never loops (F1).** Under each demo question, one-tap example
   replies the demo reads: the unsure opening "I enjoy working with people" or "Skip"; current
   work "I'm a warehouse supervisor" or "Skip"; cities "Leeds" or "Skip"; hours "5 hours a
   week" or "Unknown"; budget "Up to £600" or "Prefer not to say"; the sure opening "I want to
   be a nurse" or "Skip". The demo interviewer takes "I want to be a …" as a target and a
   message that is only Skip, Unknown or Prefer not to say as that answer to the question in
   front; the open question is only ever the opening; a reply it can't read is answered "Thank
   you. I couldn't note anything from that. Tap an example reply, or say Skip." with the same
   question. "Do you have a role in mind, or would you like to explore?" shows "Show me
   suggestions" (opens Suggestions, asks for a set where none is current, focus there) and
   "Name a role" (opens What we know's answer form at the target roles, ready to type, focus in
   the first box); neither commits anything. The live interview shows the same two at the
   stage it asks about a role (the four early answers given, no target). Captures:
   `you--role-or-explore--*`; reference unchanged (it has no demo state).
2. **Each dead end marked before it is clicked (F2).** The rail and the phone's chapter menu
   show "not built yet" under Roles, Skills, Options, Routes and Plan (names "Roles, not built
   yet, not started"). Captures: every app capture's rail; references, every capture.
3. **A chosen target confirmed, never "out of date" (F5).** After "Make this a target" the
   card says "Saved as one of your targets" (focused) with "What this work usually asks for,
   from ESCO:" and its first essential skills; no "Based on your earlier answers", no Suggest
   again. Any other change still marks the slate. Capture: `you--target-chosen--*`.
4. **Shared skills named, the connection shown.** A skill-joined suggestion says
   "Careerwright joined them by these skills: a, b and c." with "The other N skills" one step
   away. The connected suggestion is marked "An unexpected connection" (open or closed) and
   says "Careerwright joined this to your role, “…”, by N essential skills ESCO lists for
   both.", its skills and "They aren't compared with your own experience yet" one step away.
   Captures: `you--slate--*` (the talked slate's skill-joined cards). Storybook:
   `You/SlateJoinedBySkillsWithAConnection`.
5. **On a phone the decision comes first (F7, F8).** Below 968 px the You band is 144 px (the
   person and the targets), the slate's view controls one sideways row, the suggestions'
   heading and the open title at 20 px on a phone. At 390 × 844 the start's entry choice, the
   tray's first choice, "Edit answers directly" and the open suggestion's "Make this a target"
   are each in the first screen and on top. The key never covers a tab (on-top check at 768 and
   390). Captures: `you--reply-to-review--390x844`, `you--what-we-know--390x844`,
   `you--slate--390x844`; references `you--review/known/suggestions--390x844`.
6. **On a tablet the person's facts come first (F14).** The strip keeps target, work area and
   budget at 768 (each with an ellipsis if it must); "Hold the world still" and Sound are in the
   account menu below 1180 px, with their words and switches. Captures: `*--768x1024`.
7. **One bright action, two pauses not confused (F17).** Until the first answer the entry
   choice is the bright action (edged and lettered in the action colour, never a second fill);
   Send is bright only with something to send. The world's control is "Hold the world still";
   the interview's stays "Pause the interview". Captures: `you--1440x900`.
8. **A reached budget points nowhere false (F10).** "Careerwright stopped before spending more.
   Your work is kept." replaces "Raise the limit or wait for the next month." (both places).
   Capture: `you--slate-note-retry--*`.
9. **"England only" (BND1-02).** "Careerwright covers England for now." under the start and the
   opening question, until the first answer. Capture: `you--1440x900`.
10. **The demo route preview leaves the person's path.** Routes is a place not built yet in
    every workspace; the preview, its fixture loader and the web's `CAREERWRIGHT_FIXTURES_DIR`
    configuration (which only it used) are gone from the app; `RoutePreview` keeps its unit
    tests and its Storybook stories. Captures: `routes--*`; references `routes--not-built--*`.
11. **The world's requirement family (SW.6).** WLD-01 to WLD-11 in the register; tests tagged.
12. **ADR 0014 decision 7's strip wording** corrected (what the strip holds at each width).
    Storybook, the chapter's reference once built (R13), gains four stories:
    `You/DemoQuestionWithExamples`, `You/RoleOrExplore`,
    `You/SlateJoinedBySkillsWithAConnection`, `You/SlateTargetChosen` (axe-checked by
    `e2e/storybook.spec.ts`).
13. **`docs/reviews/sprint-w.md`** written: Sprint W closes at the world shell, the You chapter
    and the deterministic sources.

## Rulings I made (each the simplest reading that keeps every constraint)

1. **What the question asks about.** The API computes `ProposalOut.asks_about` from the demo
   interviewer's own question (`fixture_interviewer.asked_field`), null for a model's: the live
   model's schema and prompt are unchanged, and the web keys example replies by a code, words
   in the web.
2. **The live bridge** shows at the stage the interview asks about a role (not sure, the four
   early answers in any state, no target), because a model's question is never classified.
3. **The demo asks an unanswered question again, with the way on**, rather than moving on:
   moving on would leave the field unanswered and the next turn could not tell which question
   was in front. It recomputes the question in front from what the last answered message said
   (its fixed patterns) and the answers saved since. Known limit, recorded: after Keep none on a
   reply that was only Skip, Unknown or Prefer not to say, the next such word answers that
   earlier question again.
4. **A slate is current** while every later profile version changed only the targets, each
   citing an `occupation_choice` source from that discovery (`changed_only_by_choices`,
   `answers_current`); the note's guard uses the same rule. Recorded as an ADR 0007 amendment
   line.
5. **The saved notice** replaces "Make this a target" on any suggestion that is a target; focus
   moves to it only after the person's own choice.
6. **The connection** is shown on its own suggestion, not above the slate, so a phone's first
   decision stays in the first screen; its line is composed in the web from the role's ESCO
   title and the count (the sentence rule), not the API's `sentence`; the API's
   `still_uncertain` is reused; on that card the plain joined-by line gives way to it.
7. **"Name a role"** opens the form with the target roles set to answered in the draft only
   (saved like any edit), focus in its first box. **"Show me suggestions"** asks for a set only
   when one is wanted and nothing blocks it (`suggestionStart`, shared with the view's own
   button); otherwise it only opens the view.
8. **The band** is 144 px below 968 px (MIN_BAND 128 and a margin); none at 560 px tall or
   less. 152 px left the open suggestion's choice 17.5 px below the fold with a two-line title
   (run 1), so the band went to 144 and the phone headings to 20 px.
9. **The world's controls** move into the account menu below 1180 px (the strip's desktop
   width); "Pause motion" became "Hold the world still". The still status moved out of the
   controls into the strip so a tablet keeps it.
10. **The removed preview's loader and config** were deleted, as orphans of the change.
11. **The design references:** a decision view below 968 px draws the slim band without the
    skills (the start keeps them); Routes not built yet draws no route; the rail marks follow
    the app; the clipped-text check treats a row that scrolls sideways as clipping nothing for
    good (its words are reached by scrolling). That last one changes a check: disclosed.

## TDD evidence (RED, then GREEN)

- Backend `tests/domain/test_interview_agent.py`: with only `asked_field` added, **6 failed,
  19 passed** (the target phrase; Skip, Unknown and Prefer not to say; the question in front
  after Keep none; the open question never twice; an unread answer's way on; the example
  walk). After the change: 24 passed, 1 failed (`test_the_fixture_follows_the_entry_the_person_chose`,
  whose unsure assertion encoded the repeat; changed, below); then **25 passed**.
- Backend `tests/domain/test_discovery_contract.py`: RED, collection error (no
  `changed_only_by_choices`); GREEN, 16 passed.
- Integration on PostgreSQL 16 (`test_discovery.py`, `test_interview_turns.py`,
  `test_slate_explanations.py`, `test_origin.py`, `test_export.py`, under the lock): **66
  passed** (2 min 31 s). The new integration assertions (current rule, shared skills named,
  `asks_about`) were written with the code and not shown failing first (they read new fields).
- Web: `World.test.tsx` N1, RED on the old `World.tsx`, GREEN. `geometry.test.ts` slim band:
  RED on the old geometry (2 failed: backdrop), GREEN. With the old Conversation, YouChapter,
  ProfileEditor, Directions, ChapterNav, chapters, SketchCard and Button: **15 of 62 failed**
  in `YouChapter.test.tsx`, `Directions.test.tsx` and `ChapterNav.test.tsx` (every new or
  changed behaviour test), GREEN after. `conversation.test.ts`' new helpers fail at import on
  the old code.
- Browser: run 1 (focused: world, conversation, layout, keyboard) **32 passed, 7 failed**: two
  were my tests' own faults (a question read before the opening rendered; "Work area" matched
  exactly), two were the rail's new words making `getByText("Not built yet")` ambiguous (now
  `exact`), two were the rail names' space before the comma, and one was real: the open
  suggestion's choice at 861.5 px of 844 (fixed by ruling 8). Run 2 (conversation, layout,
  world, visual, journey, keyboard) **44 passed, 2 failed**: "nurse" also in the strip (scoped to
  What we know), and the F14 test's context inheriting reduced motion (holding still was fixed
  on, so the click waited; the context now allows motion). Both fixed before the final runs.

## Changed tests (inputs and assertions), with why

Backend:
- `test_interview_agent.py::test_the_fixture_follows_the_entry_the_person_chose`: an unsure
  person's "Hello." now gets the first practical question, not the open question again (the open
  question is the opening, never asked twice: F1). Seven new tests.
- `test_discovery.py::test_a_role_esco_lists_joins_other_work_by_shared_essential_skills_only`:
  added assertions (the four shared skills named, equal to the database's shared set; work found
  by a search names none). One new test.
- `test_interview_turns.py`: one added assertion in each of two tests (`asks_about`).

Web unit:
- `Directions.test.tsx`: fixtures gain `current: true` and `shared_skills: []`; the stale-note
  test marks the stale discovery `current: false` (the API decides now, not a version
  compare); the budget words' assertion follows F10's new words and asserts the old ones gone;
  `renderDirections` takes an optional profile. Five new tests.
- `YouChapter.test.tsx`: fixtures gain `asks_about: null`, `current: true`,
  `shared_skills: []`; `renderYou` takes an optional profile and workspace; "makes Resume the
  one primary…" expects Send secondary until text is typed (F17); the start's primary test now
  expects the two `btn-choice` entries, no filled primary, and Send bright once typed (was Send
  bright on an empty field). Eight new tests.
- `ChapterNav.test.tsx`: names now carry "not built yet" for unbuilt chapters; one new test.
- `WorldControls.test.tsx`: "Pause motion" → "Hold the world still"; the support status is
  rendered beside the controls (the shell now places it); one new assertion (no "Pause" button).
- `conversation.test.ts`: fixture `asks_about`; two new tests. `config.test.ts`: the removed
  `CAREERWRIGHT_FIXTURES_DIR`. `World.test.tsx`, `geometry.test.ts`: new tests. Tags only:
  `labels.test.ts`, `model.test.ts`, `StillWorld.test.tsx`.

Browser:
- `world.spec.ts`: the N1 test replaced (the old one read a stale `data-shown` and asserted a
  band of at least 240 px); "Pause motion" → "Hold the world still" with a helper that opens the
  account menu below a desktop's width; the identical-words test also runs a talked workspace
  (timeout 180 → 300 s); "Not built yet" matched `exact` (the rail's marks contain the words);
  one new test (F14); titles tagged WLD.
- `conversation.spec.ts`: the main journey asserts the chosen target confirmed in place; five
  new tests (both no-loop journeys, N2, the phone's first screen, the sideways window).
- `layout.spec.ts`: the route preview's layout tests (V-03's first route cards on a phone and a
  tablet, V-04's route sheet peek, S0-V07's focused card) removed with the preview from the
  page; V-09's names follow the rail marks; three new tests (rail marks, phone menu marks,
  Routes not built in the fixture workspace).
- `journey.spec.ts`: inspecting the fixture route became opening Routes (not built yet),
  during the outage too.
- `keyboard.spec.ts`: the drawer tests use an answer's Source drawer instead of the route
  drawer, with the same assertions (heading focused, Close and Escape return focus; phone peek
  212 px, More/Less above 600 px); the suggestion test asserts focus on the saved notice.
- `visual.spec.ts`: four preview shots removed (`routes--compared`, `--layers`, `--route-b`,
  `--route-b-expanded`); `routes` asserts not built; two new shots (`you--role-or-explore`,
  `you--target-chosen`). `api.ts`: two new set-up helpers.
- No assertion was weakened to pass: each change follows an intended behaviour change above.

## Every helper line added or cut

| Where | Line | Added or cut | Why |
|---|---|---|---|
| Start, opening question | "Careerwright covers England for now." | Added (until the first answer) | BND1-02 |
| Demo reply (fixture) | "Thank you. I couldn't note anything from that. Tap an example reply, or say Skip." | Added, only when the same question comes back | F1: the way on, said once where it is needed |
| Demo questions | Example replies (two per question) | Added | F1 |
| Role-or-explore question | "Show me suggestions", "Name a role" | Added (buttons) | F1, STATE-09 |
| Open suggestion, a target | "Saved as one of your targets" + "What this work usually asks for, from ESCO:" (the sketch's existing words) | Added | F5 |
| Open suggestion | "Already one of your targets." (disabled reason) | Cut | Replaced by the saved notice |
| Slate, after a choice | "Based on your earlier answers" + "Your answers have changed since…" | No longer shown when only targets chosen from it changed | F5 (the rule) |
| Skill-joined suggestion | "Careerwright joined them by these skills: …" + "The other N skills" | Added | F4 |
| Connected suggestion | "An unexpected connection", "Careerwright joined this to your role, “…”, by N essential skills ESCO lists for both.", "The N skills" (+ the API's "These are the skills ESCO lists for both roles. They aren't compared with your own experience yet.") | Added | SW.5's sentence in words |
| Rail and chapter menu | "not built yet" under each unbuilt chapter | Added | F2 |
| Budget reached | "Raise the limit or wait for the next month." | Cut | F10: names a control the app lacks |
| Budget reached | "Careerwright stopped before spending more. Your work is kept." | Added | F10 |
| Strip | "Pause motion" | Renamed "Hold the world still" | F17 |
| Routes (fixture workspace) | Every line of the route preview | Cut from the page | The audit's ruling |

## Checks run on the final candidate

On `c64b636` (the tree unchanged during the runs except uncommitted documents):

| Command | Result |
|---|---|
| `make check` | exit 0: ruff format and lint clean, mypy clean (323 files), backend pytest 1,560 passed / 333 deselected, fixture validator passed; web: generated client matches OpenAPI, Biome clean (138 files), `tsc` clean, Vitest 36 files, 337 tests passed |
| `make acceptance` (lock taken with `mkdir`, removed at the end) | exit 0: integration and stack pytest 333 passed (10 min 28 s); Storybook build completed; Playwright 55 passed (7.9 min). The durable-runs shutdown hang did not occur; one run |
| `cd docs/design && pnpm run contrast` | 132 of 132 measurements pass (100 pairs); no new colour pairing (every new use is an existing measured pair: `--action-reading` text and edge on `--surface-reading`, `--text-on-reading-muted` on `--surface-card`, `--text-on-space-muted` on the rail and popover) |
| `cd docs/design && pnpm run screenshots` | check-data 64 assertions pass; 46 of 46 captures pass |
| `cmp docs/design/tokens/tokens.css apps/web/src/design/tokens/tokens.css`; `designMirror.test.ts` | identical (tokens unchanged, so nothing to mirror) |
| Focused integration (lock): `test_discovery.py`, `test_interview_turns.py`, `test_slate_explanations.py`, `test_origin.py`, `test_export.py` | 66 passed (on the backend commit's tree) |

Logs (scratchpad, not committed): `check-final.log`, `acceptance-1.log`, `e2e-focused-1.log`,
`e2e-focused-2.log`.

## Register (last commit)

- New family **WLD** (anchor added to the usage note): WLD-01 to WLD-08 verified (the world
  shell, names in the DOM, the still world, evidence-only layout, the controls, label
  placement, the band and N1, distress); WLD-09 (the moments) planned, Task M; WLD-10
  (revelation acceptance) planned, Task W2E's part verified (the connection in words, the
  skills named); WLD-11 (frame budgets) planned, Tasks M and 16.
- Verified: BND1-02, STATE-09, STATE-10, UI-12; the Task W2E parts of STATE-08 and UI-09
  (UI-09 notes that the route preview's layout tests left with the preview).
- `docs/plan/*` unchanged.

## Not run, requires human

Session W2's formative scores (H-01); whether "Hold the world still", the example replies and
the two ways on read well to the product owner; the chapter's feel; VoiceOver (H-03); Safari
(H-04); the frame re-measure (Tasks M and 16, with the product owner warned first). No live
calls: the live bridge and a model's handling of the two buttons are untested live (Task 3b).

## Concerns

1. **One hard-rule slip:** early on I removed a redundant `mt-12` class from one line of
   `Conversation.tsx` with a short Python replace instead of the Edit tool. The change was one
   token, is in the committed diff and was reviewed; every other source change used Edit or
   Write. I also ran the project's own formatters (`ruff format`, `biome format --write`) on
   files I had changed (nine web files, three backend tests), which `make check` enforces.
2. **The ten-second bar** (a first answer changes the world within ten seconds) is not met:
   by plan v1.5 it belongs to Task 6d (the type-ahead) and Sprint M (the ignition). Recorded
   in the Sprint W review, not claimed.
3. **The demo's question in front** can be wrong in one rare case (ruling 3); recorded.
4. **The reference's rail** marks Roles to Plan "not built yet" while those places draw their
   future designs (the dispatch asked for the rail marks); a reader could find that mixed.
5. **The browser N1 test** was not run against the old build; the unit test shows the
   mechanism's RED.

## Paths a reviewer can skip

- `apps/web/src/generated/**` (regenerated by `pnpm run generate`)
- `docs/design/screenshots/*.png`, `docs/design/screenshots/checks.md` (generated)
- `apps/web/src/stories/Conversation.stories.tsx` fixture blocks (data only)

---

# Fix round 1

Implementer: Claude (Opus 5.5), a fresh implementer, main tree, branch `l0-local-release`, from
`98fd0a9`. No subagents, no live model call (cost $0), no web request, no Docker pull, no
headed browser or window, no frame measurement. `.env`, `~/.careerwright`, `~/.nessa`,
`spikes/world` and the running `careerwright-l0-*` stack untouched; `make stop` never run;
`answers-2.md` and `esco_research.txt` never staged; every commit by pathspec. DBOS
`application_version` still `careerwright-l0-1` (no workflow step changed). Every source change
by Edit or Write; the only formatters run were `ruff format` and `biome check --write` on my
own files. Docker was used only by the test projects, each run under
`.superpowers/acceptance.lock` (taken with `mkdir`, removed with `rmdir` when the run ended).

## Status

DONE. Every fix-now item is implemented with a test that reads what the person sees, shown
failing on the old code and passing on the new. `make check` and `make acceptance` pass on
`ba0846e`, the final code (the commit after it changes documents only). The first acceptance
run caught one regression of mine (the purpose line pushed a sideways phone's entry choice
15 px below its first screen); fixed in `ba0846e`, and the second run passed.

## Commits

| SHA | Subject (shortened) |
|---|---|
| `c91687f` | The demo interviewer: its way on names only what is in sight (backend, with tests) |
| `c5650b0` | The You chapter: strip facts whole, the join said once, What we know's action first, focus kept, Name a role once, the start's purpose line (web, unit and browser tests) |
| `65f28bf` | Design references: What we know's action under its heading |
| `ba0846e` | In a window too short for a band the console's own title is for assistive tech only, so a sideways phone's entry choice stays in its first screen under the purpose line |
| `60c8516` | The register and the Sprint W review (last commit: documents) |

## Each finding: the fix and its test (RED, then GREEN)

| Finding | Fix | Test | RED (old code) | GREEN |
|---|---|---|---|---|
| **D-I1** tablet strip cuts all three facts | `globals.css` (≤ 1179 px): each fact `flex: 0 1 auto` (its own width, not an equal share); a fact that doesn't fit moves to the next row whole; the label never wraps (`white-space: nowrap`), and only a value wider than the whole row wraps by words (no ellipsis anywhere) | `e2e/world.spec.ts` F14 test, extended: at 768, in the fixture workspace and in a workspace with three long targets and "Not confirmed", each fact's words read in full (`Target Data quality analyst`, `Work area …`, `Budget Up to £…, at most £… a month`; `Target <three long names>`, `Work area Manchester`, `Budget Not confirmed`), its label on one text row, its value not cut (`scrollWidth ≤ clientWidth`) and inside the strip | Failed: "Target Data quality analyst: its value is shown whole, expected false, received true" | Passed (acceptance) |
| **D-I2 + A-M1** the join stated twice; ESCO's title as "your role"; "These are the skills ESCO lists…" | `Directions.tsx`: one `JoinedBy` for every skill-joined card, the connection included: under the API's reason (which states the join and quotes the person's own words) it only names the skills, "Among them: a, b and c." (or "Those skills: …" when all are named), the rest one step away. The connection line ("Careerwright joined this to your role, “…”…") is gone, so ESCO's title is never called "your role". The connection keeps its mark and says "Careerwright hasn't compared them with your own experience yet." (web words, `SUGGESTION_WORDS.notCompared`), replacing the API's `still_uncertain` | `Directions.test.tsx`: "states the join once on each card, and never calls ESCO's title the person's role" (a plain card and the connection, the person's "cycle courier" against ESCO's "bicycle courier": "joined" once per card, no "your role", no ESCO title quoted); "shows the unexpected connection…" (rewritten); "names the first skills…" (changed assertion); "names all the skills… only a few" (new) | 4 failed, among them "expected 2 to be 1" (the join count) | Passed |
| **D-I3** What we know's action off a phone's first screen in the fixture workspace | `WhatWeKnow.tsx`: "Edit answers directly" right under the view's heading, before the answers, and the answer form opens right under it (focus stays on the toggle, the disclosure pattern); `YouChapter.tsx` passes the form in | `e2e/conversation.spec.ts` "at 390 × 844 each view's first decision is in the first screen": What we know now checked in the fixture workspace (four answers, two limits explained, the long "Not asked yet"); `YouChapter.test.tsx` "[UI-12] puts What we know's action under its heading…" (reading order: heading, action, form, answers) | Browser: "expected ≤ 844, received 895.5" (the button's bottom edge); unit: failed | Passed (acceptance; unit) |
| **A-I1** the demo's "couldn't note" reply points at controls that aren't shown | `fixture_interviewer.py`: at the role question of a person who isn't sure, "Thank you. I couldn't note anything from that. Tap Show me suggestions or Name a role."; once nothing is left to ask (nothing in front, nothing after), any message, Skip included, gets "Thank you. I have no more questions. Open Suggestions for work that could suit you, or What we know to change an answer."; under a question with example replies the old words stay. No new pattern (R11) | Backend `test_interview_agent.py`: "at the role question an answer the demo can't read names its two buttons" ("Explore", "I'd like to explore", "yes") and "after the last question any message says what to do next and Skip never loops" ("What next?", Skip, Skip twice: no "Skip", no "example", one reply). Browser `e2e/conversation.spec.ts` "the demo's way on names only what is in sight…": the reviewer's two probes in the app, each reply checked against the controls on screen | Backend: 2 failed, 25 passed. Browser: failed at the first probe ("Tap an example reply, or say Skip." with no examples shown); the run stops at the first failure, so the second probe's RED is the backend test's | Backend 27 passed; browser passed (acceptance) |
| **A-I2** tapping an example reply drops focus | `Conversation.tsx`: the tap moves focus to the reply field (which stays mounted) before sending | `YouChapter.test.tsx` "keeps keyboard focus when an example reply is tapped: it moves to the reply field" | Failed (`toHaveFocus`) | Passed |
| **A-I3** "Name a role" fires again on every later opening of the form | `YouChapter.tsx` / `ProfileEditor.tsx`: the request is a boolean the form clears (`onTargetsOpened`) once applied, so a later mount changes nothing | `YouChapter.test.tsx` "opens target entry once for Name a role…": the reviewer's sequence (Name a role, close the form, Edit answers directly): Target roles still "unasked", no target box, focus on the toggle; weekly hours set to Unknown and saved: the PUT goes through with `target_titles` unasked | Failed: `toHaveValue(unasked)` (the field had been switched to answered) | Passed |
| **The start-page comment** (session 2: "not sure" what it's for) | `Conversation.tsx` / `vocabulary.ts` `PURPOSE`: before the entry choice, one line, "Careerwright helps you find work that could suit you, see what it would take, and plan a route you can afford." Nothing else added | `YouChapter.test.tsx` "says in one line what Careerwright is for, before the entry choice, at the start only"; `e2e/conversation.spec.ts` (the sure journey's start) | Unit and browser: not found | Passed |
| **UI-09 cites removed tests** | Register: the T6c part's V-03 and V-04 `layout.spec.ts` evidence marked retired with the preview; V-03, V-04 and S0-V07 handed to Task 14's open part | — (document) | — | — |

## Every helper line on the suggestion cards, cut or kept

| Line | Cut or kept | Why |
|---|---|---|
| "Careerwright joined them by these skills: a, b and c." | Cut, replaced by "Among them: a, b and c." ("Those skills: …" when all are named) | The reason just above already says how they were joined; this only names the skills |
| "Careerwright joined this to your role, “…”, by N essential skills ESCO lists for both." | Cut | Stated the join a second time and named ESCO's title as "your role" |
| "The N skills" (the connection's own disclosure) | Replaced by the same first three named and "The other N skills" as every skill-joined card | One way of naming the skills |
| "These are the skills ESCO lists for both roles. They aren't compared with your own experience yet." (the API's `still_uncertain`) | Cut, replaced by "Careerwright hasn't compared them with your own experience yet." | Said what a list contains (the sentence rule); the qualifier itself stays with the revelation |
| "How Careerwright found it is below." (a card with no note from a changed view) | Cut | The label "How Careerwright found it" is the next line |
| "…; how Careerwright found this suggestion is below." (a failed or refused note) | Cut (both) | Same: the label follows at once. "Nothing from it was kept." and "Careerwright didn't ask the model, so nothing was sent." stay |
| "An unexpected connection" | Kept | Marks the revelation so it can be found, open or closed |
| "Kind of work: …" | Kept | Says what the work is, in the closed list too |
| "How Careerwright found it" | Kept | Sets Careerwright's own reasons apart from a written note |
| "Written by … Only the quoted words were checked…" | Kept | Required: the UI says only the quotations are checked (ADR 0007 decision 12) |
| "Careerwright wrote notes for your first set of suggestions; this one appeared when you changed the view, so it has none." | Kept | Says why this card alone has no note |
| "The other N skills" | Kept | The rest of the skills, one step away (the brief) |
| The API's reasons, "What might not suit you", "Try it before committing", the gaps line | Kept | API words carrying the suggestion's facts; session W2 judges the helper lines (R10) |

Added elsewhere: the start's purpose line; the demo's two new replies (the role question's, and
"no more questions").

## Rulings (each the simplest reading that keeps every constraint)

1. **The strip wraps, it never cuts.** A fact that doesn't fit moves to the next row whole; the
   states keep their own row above a phone (V-08: a longer state never changes the strip's
   height), so the fixture workspace's strip at 768 is three rows (the synthetic label, target
   and work area; the budget; the states and menu), about one row taller than before. A value
   wider than the whole row (three long targets) wraps by words under its label. No money
   value is shortened: the whole budget always fits a row.
2. **The skills line is a continuation, not a statement**: "Among them: …" when some wait one
   step away, "Those skills: …" when all are named (at least three always exist:
   `MIN_SHARED_SKILLS`).
3. **The connection card names the suggestion's own shared skills**, like every card (a
   superset of the role's when a target also joined it). The web no longer shows
   `ConnectionOut.role_title`, `sentence`, `shared_skill_count`, `shared_skills` or
   `still_uncertain`; they stay in the API, since removing them is a contract change outside
   this fix (a final-review note).
4. **What we know's form opens right under its toggle**, before the answers, so the toggle and
   what it opens stay together and focus stays on the toggle (the disclosure pattern). The
   alternative, moving focus down to a form below the answers, was not taken.
5. **After the last question every message gets the same "no more questions" reply.** A
   deterministic interviewer can't vary its words without state; the loop was the reply sending
   the person back to Skip, and this reply names only the two views that are always there.
6. **At the role question the reply names the two buttons, not Skip** (say less). Typing Skip
   there still works.
7. **The purpose line** sits inside the entry choice, above its heading, in the card's
   suggested words, and shows only while the entry choice does. The design reference's start
   is unchanged: its default state is the future first question after an answer and has no
   entry choice (design Minor 4 waits for the final review); the Storybook start story shows
   the line.
8. **"Name a role" is one request**, a boolean the form clears once applied, not a counter.
9. **A window too short for a band (≤ 967 × 560 px) hides the console's own "You" title
   visually**, as a phone already does (the rail names the chapter there; assistive tech still
   reads it). The purpose line wraps to two lines in the 600 px console and pushed the entry
   choice to 404.8 px in an 844 × 390 window (the N3 test, acceptance run 1); with the title
   hidden it fits. The phone rule and this one now share one media query.

## Changed tests (inputs and assertions), with why

- `Directions.test.tsx`: "names the first skills…" now expects "Among them: adjust brakes, fit
  tyres and replace chains." (was "Careerwright joined them by these skills: …"), the intended
  words change. The connection test is rewritten: its suggestion's reason quotes "cycle courier"
  while ESCO's role title is "bicycle courier" (input changed, to test A-M1), and it expects the
  skills named, the rest one step away, and the new uncertainty line, with the old API line
  absent (was: the connection line and "The 5 skills"). The `connection` fixture moved to
  module scope, unchanged. Two new tests.
- `YouChapter.test.tsx`: four new tests; nothing changed.
- `test_interview_agent.py`: two new tests; the walk test's table comment now says that at an
  unsure person's role question the web shows two buttons, so the walk types there (no
  assertion changed).
- `e2e/conversation.spec.ts`: the first-screen test checks What we know in the fixture
  workspace instead of the three-answer workspace (input changed: the harder case the review
  named); the sure journey also asserts the purpose line; one new test (both probes), with two
  helpers.
- `e2e/world.spec.ts`: the F14 test gains the whole-fact checks at 768, on the fixture and on
  the long-targets workspace (the old label-only assertions stay).
- No assertion was weakened.

## Checks run

TDD evidence (logs in the scratchpad, not committed: `e2e-red.log`, `acceptance-1.log`,
`acceptance-2.log`, `check-1.log`, `check-2.log`):

| Command | On | Result |
|---|---|---|
| `uv run --locked pytest tests/domain/test_interview_agent.py -q` | the old fixture interviewer, new tests | RED: 2 failed, 25 passed (the role question's reply was "…Tap an example reply, or say Skip."; after the last question "What next?" got the same) |
| same | the fix | GREEN: 27 passed |
| `pnpm exec vitest run src/components/YouChapter.test.tsx src/components/Directions.test.tsx` | the old components, new tests | RED: 8 failed, 58 passed (the four D-I2 tests; the purpose line; D-I3's order; A-I2's focus; A-I3's `toHaveValue(unasked)`) |
| `pnpm exec vitest run` | the fix | GREEN: 36 files, 343 tests passed |
| `pnpm exec playwright test e2e/conversation.spec.ts e2e/world.spec.ts -g "names only what is in sight\|first decision is in the first screen\|takes a target in the person's words\|strip keeps the person's facts"` (lock held; the source fixes stashed with `git stash push -- <source paths>`, the tests kept, then `git stash pop`) | the old code, new tests | RED: 4 failed: the purpose line not found; the role-question reply "Tap an example reply, or say Skip." with no examples on screen; "Edit answers directly" bottom at 895.5 px of 844; "Target Data quality analyst: its value is shown whole, expected false, received true" |
| `make acceptance` run 1 (lock) | `65f28bf` | exit 2: integration and stack 333 passed (9 min 56 s); Storybook built; Playwright 55 passed, 1 failed: the N3 sideways-window test ("Help me explore" bottom 404.8 px of 390), caused by the purpose line (ruling 9). The four new browser tests passed |
| `make acceptance` run 2 (lock) | `ba0846e` | **exit 0**: integration and stack 333 passed (9 min 29 s); Storybook built; Playwright **56 passed** (8.0 min). The durable-runs shutdown hang did not occur in either run |
| `make check` | `ba0846e` | **exit 0**: ruff format and lint clean, mypy clean (333 files), backend 1,620 passed / 333 deselected, fixture validator passed; web: generated client matches, Biome clean (138 files), `tsc` clean, Vitest 36 files, 343 tests passed |
| `cd docs/design && pnpm run contrast && pnpm run screenshots` | `65f28bf`'s reference | 132 of 132 measurements pass (100 pairs; no new colour pairing); check-data 64 assertions; 46 of 46 captures pass. Only `you--known--*` committed: `you--suggestions--768x1024.png` changed by rendering noise alone and was restored. No token changed, so nothing to mirror to `apps/web/src/design` (it holds only tokens and fonts) |

Captures read for an agent pre-review (from run 1; ruling 9 changes only windows ≤ 560 px tall,
which no capture uses): `you--768x1024` (strip: synthetic label, target and work area; then
"Budget Up to £1,500, at most £1,500 a month" whole; then the states), `you--role-or-explore--768x1024`
("Budget Not confirmed" whole), `you--slate--1440x900` (the reason, then "Among them: …", then
"The other 6 skills"), `you--what-we-know--390x844` ("Edit answers directly" under the heading,
in the first screen). Agent pre-review only (R2).

## Not run, requires human

Whether the purpose line, "Among them: …" and the demo's new replies read well (session W2
judges the words); VoiceOver (H-03); Safari (H-04). No live call.

## Concerns

1. **The tablet strip is taller in the fixture workspace**: three rows at 768 instead of two,
   because its facts no longer fit one row whole. The console moves down by one row; the world
   tests at 768 (light above the console, key off the tabs) pass.
2. **The browser RED for the second probe** (after the last question) is not shown in the
   browser: on the old code the test stopped at the first probe. Its RED is the backend test's,
   which calls the same function the app does.
3. **Unused API words**: the web no longer shows `ConnectionOut.role_title`, `sentence`,
   `shared_skill_count`, `shared_skills` or `still_uncertain`. Left in the API (a contract
   change was out of scope); for the final review.
4. **The design reference's start** still has no entry choice or purpose line (design Minor 4,
   waiting for the final review); the purpose line lives in the app and its Storybook start.

## Paths a reviewer can skip (fix round 1)

- `docs/design/screenshots/you--known--*.png` (generated)
