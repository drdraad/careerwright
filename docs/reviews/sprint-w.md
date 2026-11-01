# Sprint W review: the world shell, the You chapter and the deterministic sources

- Date: 2026-10-31. Branch `l0-local-release`.
- Order this ran in (plan v1.5): Task W1 (the spike, session W1 held 2026-10-30), Task W2's
  slices W2A (the world layer and its design references), W2B (the deterministic sources) and
  W2C part 1 (the You chapter rebuilt in the world), then Task A1 (the audit, approved
  2026-10-31), then Task W2E (this task: the You chapter finished, the world's requirement
  family, this review). Sprint W closes here, at the world shell, the You chapter and the
  deterministic sources (plan v1.5); the chapters' moments are Sprint M's.
- Sprint W commits: `cec21cd` (the spike) to `f179d0f` (W2C part 1's fix round 1), then Task
  W2E: `8410eff` onward (listed in the Task W2E report).
- Reviewer: the Task W2E implementing agent, not independent of the work. This is an **agent
  pre-review, not the required human review** (R2). An independent agent reviewer is
  dispatched after this task. Session W2's outcome is added by the first task after it, from
  the product owner's own record (R10).

## Outcome

The card's demonstrable outcome, as plan v1.5 reshapes it, shown from the UI by browser
journeys on a fresh demo stack:

1. Someone opens Careerwright in a new demo workspace. One plain line says what Careerwright
   is for, and one that it covers England for now; the entry choice is the bright action. One
   world stands behind every chapter, with their light at its origin (`e2e/world.spec.ts`).
2. They talk with the demo interviewer, by typing or by tapping an example reply under each
   question. It takes a target in their words ("I want to be a nurse") and Skip, Unknown and
   Prefer not to say, and never asks the same question twice
   (`e2e/conversation.spec.ts`, two journeys). They review and save what it noted, and undo a
   save.
3. "Do you have a role in mind, or would you like to explore?" offers "Show me suggestions"
   (it opens the suggestions and asks for them) and "Name a role" (it opens the answer form at
   the target roles). Neither commits anything.
4. The suggestions name the skills each was joined by, under the reason that says so (the
   join said once), and the slate's unexpected connection is marked on its suggestion, its
   skills named the same way (`Directions.test.tsx`).
5. They make one a target: the choice gives way, in place, to "Saved as one of your targets"
   and what the work usually asks for. The slate is not "out of date": the only change since
   it was made is their choice from it (`e2e/conversation.spec.ts`, `test_discovery.py`).
6. Every other chapter is marked "not built yet" in the rail before it is clicked, and shows
   its place with an honest card; Routes does in every workspace, the fixture's too.
7. On a phone each view's first decision is in the first screen; on a tablet the strip keeps
   the person's facts whole, and the world's controls are in the account menu. (The first
   candidate's tests did not establish either: see "Visual findings".)

Not shown, by plan v1.5: the first answer's ignition and the other moments (Sprint M), the
type-ahead first question (Task 6d), the live interview through the app (Task 3b).

## Card deliverables (Sprint W, as plan v1.5 reshapes it)

| Item | State | Evidence |
|---|---|---|
| SW.1 the spike and session W1's choice | done (Task W1) | `docs/reviews/session-w1-answers.md`; ADR 0014 |
| SW.2 design references for the chosen direction | done (W2A, W2C part 1; updated by W2E: the phone band, the rail marks, Routes not built yet, What we know's action first) | `docs/design/screenshots/checks.md`: 46 of 46 captures pass; contrast 132 of 132 |
| SW.3 the world layer in the app | done (W2A; N1 fixed by W2E) | `World.test.tsx`, `e2e/world.spec.ts` |
| SW.4 the You chapter rebuilt, applying session 2's findings | done (W2C part 1, finished by W2E) | `YouChapter.test.tsx`, `Directions.test.tsx`, `e2e/conversation.spec.ts` |
| SW.5 the deterministic sources and the strength's run | done at its sources (W2B); the connection's sentence and skills shown by W2E; the moments moved to Sprint M | `test_slate.py`, `test_origin.py`, `Directions.test.tsx` |
| SW.6 the world's requirements in the register, tests tagged | done by W2E: family WLD (WLD-01 to WLD-11) | `docs/requirements-register.md` |

## Checks run on the final candidate

On Task W2E's code, commit `c64b636` (the commit after it changes documents only):

- `make check`: exit 0. Backend: ruff format and lint clean, mypy clean (323 files), 1,560
  fast tests passed, the fixture validator passed. Web: the generated client matches the
  OpenAPI document, Biome clean (138 files), `tsc` clean, Vitest 337 tests in 36 files passed.
- `make acceptance` (under the acceptance lock): exit 0. 333 integration and stack tests
  passed on PostgreSQL 16 and DBOS (10 min 28 s); the Storybook build completed; 55
  Playwright tests passed (7.9 min), the visual package at three sizes included. The
  durable-runs shutdown hang did not occur.
- Design references: `pnpm run contrast` 132 of 132 measurements pass (100 pairs);
  `pnpm run screenshots` 46 of 46 captures pass (check-data's 64 assertions first). The token
  mirror in `apps/web/src/design` is byte-identical (`cmp`; tokens unchanged).
- Live: none (cost $0). Not run: VoiceOver, Safari, the frame re-measure (human or later
  tasks', below).
- After Task W2E's fix round 1, on `ba0846e`: `make check` exit 0 (1,620 fast backend tests,
  Vitest 343 tests in 36 files); `make acceptance` exit 0 (333 integration and stack tests,
  the Storybook build, 56 Playwright tests); design references 132 of 132 contrast
  measurements and 46 of 46 captures pass.

## The six questions

1. **Does the journey make sense from entry to the latest outcome?** Yes, from a new demo
   workspace to a saved target and what it usually asks for (Outcome above). Failure paths: a
   reply the demo can't read says so and names the way on that is in sight (an example reply
   or Skip; at the role question its two buttons); after the last question any message gets
   what to do next, never a loop back to Skip; a failed reply keeps the message with Try
   again; a stopped update says why in words read whole on a phone; a slate made from earlier
   answers says so with Suggest again. Where the path stops: at You, by plan; every later
   chapter says it is not built yet before it is clicked.

2. **Do shared concepts mean the same everywhere?** Unknown, Skipped and Prefer not to say
   are answers in the demo, the tray, What we know and the form, never zero. "Current" for a
   slate is one rule in one place (the API's `DiscoveryOut.current`), used by the view and by
   the note's guard. "Not built yet" is the place's kicker and the rail's mark. Direct and
   economic cost do not appear on the person's path now: the fixture route preview left it.

3. **Can a displayed claim be traced to its source?** One example: "Saved as one of your
   targets" on the open suggestion → `POST /targets` with the discovery's ID wrote
   `target_titles` with an `occupation_choice` source naming the ESCO URI and the discovery →
   `answers_current` compares every profile version since the one the discovery pinned and
   finds only that change, citing that source → `DiscoveryOut.current` is true → the view shows
   no "based on your earlier answers" → the requirements under it are the sketch's for that
   target, from ESCO's record of the chosen occupation. Each link is tested
   (`test_discovery.py::test_a_target_chosen_from_the_slate_leaves_it_current_and_any_other_change_does_not`).

4. **Are module and process boundaries intact?** The demo interviewer's new patterns are in
   the fixture adapter only; the live prompt and schema are unchanged (`asks_about` is
   computed at the API from the demo's own question, null for a model's). The rule for a
   current slate is pure (`changed_only_by_choices`) with its reads in the profile store; the
   shared skills come from the catalogue store adapter. The web computes no rank: it shows the
   API's skills and connection. No new dependency. The fixture loader and its configuration,
   which only the route preview used, are gone.

5. **Is the interface coherent and polished?** It follows the references, updated where this
   task changed what a place shows (the phone band, the rail marks, Routes not built yet, What
   we know's action first). One bright action per view: the entry choice at the start, Send
   only with something to send. The world's control is named apart from the interview's
   pause. Agent pre-review below.

6. **What evidence establishes completion?** The checks above on the final candidate. They do
   not establish the human gates: session W2's formative scores (H-01), VoiceOver (H-03),
   Safari (H-04), the frame re-measure (Tasks M and 16, with the product owner warned first).

## Coherence question (Sprint W card)

*Pick one revelation and trace it from the screen to its source records and versions; any
glow, gate or shadow without a computed state behind it is a defect. Then: would a first-time
visitor feel, within ten seconds, "My future is larger than I realised"?*

- **The revelation traced:** the unexpected connection on a suggestion (its mark "An
  unexpected connection", the reason quoting the person's own role, and the skills named, with
  "Careerwright hasn't compared them with your own experience yet") →
  `SlateOut.connection`, computed each read by `exploration._connection` over the slate's
  candidates outside the role's own kind of work, never a title the person named → its skills
  from `taxonomy_store.shared_essential_skills` over the held, hash-checked ESCO release → the
  role's occupation from the person's saved answer. The world draws no connection yet (Sprint
  M), so there is no glow to trace; every light it draws (the person, the targets) has its
  words in the DOM list. Every shadow is "not known yet" ground (WLD-04).
- **Ten seconds:** not yet, honestly. Within ten seconds a newcomer has chosen how to start
  and sees the question with example replies; the world answers only once an answer is saved.
  The ten-second answer (the type-ahead first question and the first answer's ignition) is
  Task 6d's and Sprint M's by plan v1.5. Recorded, not claimed.

## Visual findings (agent pre-review, not the required human review)

From the acceptance run's captures (`apps/web/test-results/visual-*/screenshots/`) and the
design references:

- Corrected after the independent review (Task W2E fix round 1). This review first said each
  phone view's first decision was in the first screen "(tested)". The test ran What we know
  only on a workspace with three short answers; in the fixture workspace "Edit answers
  directly" was below the first screen. It also missed two defects in the captures: on a
  tablet the strip cut all three facts mid-word, the budget inside its digits, with room to
  spare; and each skill-joined suggestion stated its join twice in a row. Fix round 1 put What
  we know's action under its heading (tested on the fixture workspace), gave each strip fact
  the width its words need (tested at 768: each fact read whole, in the fixture workspace and
  with three long targets), and states each join once (`Directions.test.tsx`).
- At 390 × 844 the band is a slim strip with the person's light and the target's name; each
  view's first decision is in the first screen (tested since fix round 1, What we know on the
  fixture workspace). In the Suggestions view a two-line title leaves the saved notice or the
  choice near the fold: a three-line title would push it below (not seen in the examples; a
  known edge).
- At 1440 the role-or-explore question's two ways on read as one decision, edged in sea-glass,
  with Send quiet beside an empty field; "Hold the world still" is clearly the world's, apart
  from "Pause the interview".
- The rail's "not built yet" sits under each unbuilt chapter; the rail's trail line passes
  behind those words as it already did behind the chapter names (a polish item for Task M's
  list, not a reading problem: contrast unchanged).
- The world in a slim band is small: the person and one target; whether it still feels like a
  world answering the person is session W2's question, not this review's.

## Accepted limitations

- In the demo, after Keep none, a Skip answers the first question still unanswered, which may
  be an earlier one than the question shown (the demo recomputes the question in front from
  what the last answered message said; it cannot see its own earlier question).
- The bridge in a live interview shows at the stage the interview asks about a role (the four
  early answers given, no target); a model's question is never classified.
- On a phone the view controls scroll sideways in one row.
- The ten-second bar (above) and the moments are later tasks'.
