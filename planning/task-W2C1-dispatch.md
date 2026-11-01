# Task W2, slice W2C part 1 dispatch: the You chapter in the world

Where this fits: Careerwright L0 is mid-build (branch `l0-local-release`, HEAD 166e4ef). Task
W2 builds the product owner's chosen "living world" into the app in slices. W2A (the world
layer) and W2B (the deterministic sources: type-ahead, usual skills, the skill-joined slate,
the unexpected connection, the overlooked strength run) are done and reviewed. W2C is split in
two (controller ruling): you own **part 1, the You chapter rebuilt in the world (SW.4)**, plus
the truth fixes carried from W2B's final review and the strip work carried from W2A. Part 2,
after you, builds the first moments and the two revelations on top of your chapter. W2D then
closes acceptance, the register and session W2's package.

## Read first, in this order
1. Your contract: `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`
2. The brief (Global Constraints, standing rulings, the Task W2 card):
   `.superpowers/sdd/l0-sprint-tasks/task-W2-brief.md`
3. The slice plan, its W2C paragraph and the rulings that bind every slice:
   `.superpowers/sdd/l0-sprint-tasks/task-W2-slices.md`
4. The carried items: `.superpowers/sdd/l0-sprint-tasks/carry-forward-task-W2C.md`, all of it.
   Which part owns which item is below.
5. `docs/plan/development-plan.md` section 4 in full and the Sprint W card (SW.4 is the line
   starting "SW.4 The You chapter rebuilt"); `docs/adr/0014-the-living-world.md`.
6. The product owner's own records: `docs/reviews/session-2-answers.md` ("Part 2: score the
   first screens" and "Decisions the product owner added at the end") and
   `docs/reviews/session-w1-answers.md`.
7. What was built: `task-W2A-report.md` (the world layer: `apps/web/src/lib/world/*`,
   `World.tsx`, `StillWorld.tsx`, `WorldControls.tsx`) and `task-W2B-report.md` (the APIs;
   read its first section and skim the fix rounds for the notes' final wording rule).
8. The code: `apps/web/src/components/YouChapter.tsx`, `Conversation.tsx`, `ProfileEditor.tsx`,
   `Directions.tsx`, `SketchCard.tsx`, `WorkspaceShell.tsx`, `WorkspaceStrip.tsx`,
   `src/lib/vocabulary.ts`, the tokens in `docs/design/tokens/tokens.css`, and the e2e journeys.

## What part 1 delivers
1. **The truth fixes carried from W2B, first** (the "must-fix, first" section of the
   carry-forward file): every listed line says what the search or match did, never what ESCO
   contains, each with a test that reads its words; the hyphen check and, if confirmed, its fix;
   the OpenAPI descriptions with the client regenerated (`pnpm run generate`). Commit these on
   their own before the chapter work.
2. **The You chapter rebuilt in the world (SW.4)**, applying session 2's findings as the
   product owner recorded them: chat first and immediate; the tone setting moved to
   preferences; one idea per view; suggestions in their own view; a bright primary action;
   accept and undo colour coded; the limits ("total spending limit", "monthly payment limit")
   explained in plain words. The chapter is a place in the world (ADR 0014), not a form over a
   backdrop: ask of every view "does this feel like a world answering the person?"
3. **The strip and the key** (carried from W2A): the strip's plain words, two rows at tablet,
   the key check tested against destination names or a data attribute with the empty-key case,
   and the flaky phone strip test (`e2e/world.spec.ts:273`) stabilised by waiting for fonts and
   layout, not by loosening it.
4. **The "Your world" DOM list** names skills and openings, with a count line for openings,
   so the canvas holds nothing unique.

Part 2 owns (leave these): the first-answer ignition and the type-ahead's `partial` question
in the interface; the unexpected connection lit in the world; the overlooked strength's
proposal and confirm step; "usual in your role, not confirmed yet"; `held_back` and the
strength's destinations on the horizon; a risk word holding back revelations. Where your
chapter needs a place for one of these, leave an honest, labelled slot and say so in the
report.

## Decisions the brief cannot know (the controller's)
- **Transcribe, don't decide (R2):** apply session 2's findings as written. Where the record
  is unclear, take the reading that changes least, and list it in your report for session W2.
- **"Never overwhelming"** binds this chapter. The product owner, on a busy test scene: "Wow,
  the scene looked too busy. was overwhelming". They judged the real screens at 1440 × 900
  OK. Calm first; one idea per view.
- **Colour:** orange means destinations only. Sea-glass teal means selection, the chosen path
  and the one primary action only; quiet actions are never teal. Accept and undo colours come
  from the tokens; any new pairing goes in `contrast-pairs.json` and is measured
  (`cd docs/design && pnpm run contrast`).
- **The still world** (reduced motion, calm mode) shows the same states and words. Pause stays
  visible. Sound stays off by default.
- **Screens:** design references in `docs/design` for the rebuilt chapter at 1440 × 900,
  768 × 1024 and 390 × 844, mirrored byte-identical to `apps/web/src/design`. Headless
  screenshots only.
- **Tests:** Vitest for components, Storybook stories for the new states, Playwright journeys
  for the chapter in moving and still modes with identical text, axe and overflow clean at the
  three viewports, keyboard-only completion and focus return. Tag tests with existing register
  IDs; list new requirement candidates for W2D.
- **Backend:** only the carried truth fixes and the hyphen fix. No new endpoint unless the
  chapter cannot work without one; if so, it is a contract change: test, regenerate, report.

## Hard rules
- Change source files with Edit and Write only: never `sed`, `awk`, heredocs, or scripts that
  rewrite files (generated outputs from the project's own tools are fine).
- Stage explicit paths only; never `git add -A` or `git add .`. Never stage or commit
  `answers-2.md`. Never push.
- Never read `.env` or anything under `~/.nessa` or `~/.careerwright`. No web requests. No
  live model call. No Docker pull of an image that isn't cached.
- No headed browser, no `open`, nothing that puts a window on the product owner's screen. No
  frame measurement (W2D runs it, after warning the product owner).
- Leave `spikes/world` and the running `careerwright-l0-*` stack alone. Do not dispatch
  subagents.
- DBOS `application_version` stays `careerwright-l0-1`.
- `make check` and `make acceptance` pass before your final commit (check `pgrep -fl "make
  acceptance"` first). If a known flake recurs (the durable-runs shutdown hang), re-run once
  and report both runs exactly.

## Report
Write your full report to `.superpowers/sdd/l0-sprint-tasks/task-W2C1-report.md`: each
carried item and what closed it (with the test), each SW.4 finding and how the chapter applies
it, the readings you chose where session 2's record was unclear, the slots left for part 2,
contrast pairs added, requirement candidates for W2D, and the paths a reviewer can skip. Then
reply with only the short contract.
