# Task W2E: finish the You chapter, and the Sprint W review

Careerwright L0. This task finishes the first chapter so that a person (and the product owner,
at a short live session soon) can use it without dead ends: the demo stops looping, a chosen
target is confirmed, the skills a suggestion shares are named, and on a phone the decision
comes first. It closes Sprint W.

## Your tree
The **main tree**, `/Users/darianraad/Code/careerpathoptimizer`, branch `l0-local-release`
(HEAD ec4d060 or later).
- Another implementer works in a worktree on the route search (backend planning only).
- A reviewer reads the documents in this tree, and a documents fix may follow it.
- Commit with explicit pathspecs only. `docs/requirements-register.md` and `docs/plan/*`
  change only in your last commit.

## Read first
1. `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`, all of it, including
   "Parallel work".
2. Your brief: `.superpowers/sdd/l0-sprint-tasks/task-W2E-brief.md`. It is your
   requirements, with the exact values to use verbatim (Global Constraints, standing rulings
   R1–R15, the card). Read R13 and R14 closely: path before polish, and the review rules.
3. The audit report `docs/reviews/l0-audit-2026-10-31.md` (sections 2 and 4) and appendix
   `docs/reviews/l0-audit-2026-10-31/E-person-path.md`. Its findings F1, F2, F5, F7, F8, F10,
   F14 and F17 carry the evidence (`file:line`, captures) for the card's items.
4. The last review of this chapter, for context:
   - `.superpowers/sdd/l0-sprint-tasks/task-W2C1-rereview-1.md` (open findings below);
   - `task-W2C1-report.md` (what W2C part 1 built and its fix round);
   - `task-W2C1-dispatch.md` (decisions that still bind).

## The re-review's open findings (fix first, each with a test that would fail today)
- **N1 (Important), with D-I2's unfinished app part.** Views now switch by the `hidden`
  attribute, and the world's observer doesn't watch attributes (`YouChapter.tsx:250`,
  `World.tsx:682-683`). So after a view change on a tablet or phone, the world isn't placed
  again:
  - the person's light sits under the console in What we know at 768 and 390;
  - the key button lands over the console's edge (768) or over the Suggestions tab (390).

  This is the cause of the audit's F8, so moving the button alone won't fix it. The current
  world test passes because it reads a `data-shown` value left over from the previous view
  (`e2e/world.spec.ts:379-403`). Replace it with a test that compares the light's, the key
  button's and the console's boxes after each view change, at 768 and 390.
- **N2 (Minor, with F7):** on a phone the strip's ellipsis also cuts the stopped state's
  reason. The reason must stay readable.
- **N3 (Minor, with F7):** the band's 300 px floor pushes the console off the first screen
  in a short window, for example a phone turned sideways. Size the band to what it shows,
  per the card.
- D-M5 (one line, "Review the latest version, then save again.", `vocabulary.ts:527`) waits
  for the final review. Fix it only if you touch that line anyway.

## Decisions that bind you
- **Build to the design references (R13).** No new spectacle: ignition, rings, the target
  preview and lighting the connection in the world are Task M's.
  - Where the world and a decision compete, the decision wins (`CLAUDE.md`, "Practical
    first").
  - Update the design references only where this task changes what a place shows (the phone
    band, the rail marks, the removed route preview), mirrored byte for byte to
    `apps/web/src/design`.
- **The sentence rule (`CLAUDE.md`):** every new line says what Careerwright did or checked,
  never what a source or list contains. When exact and plain conflict, say less.
  - New words come from `src/lib/vocabulary.ts`, with exhaustive maps.
  - Keep the API free of new prose: codes and numbers out, words in the web.
- **The demo interviewer's new patterns** are offline and deterministic, like its existing
  ones. They are not a language model: a small, named set (a target phrase; Skip, Unknown,
  Prefer not to say), each tested. R11 applies, so add only what the card names.
- **"Show me suggestions" and "Name a role"** are buttons in the conversation that open
  existing views and actions. They commit nothing by themselves. A target is still chosen
  only by the person, through the existing command.
- **A chosen target confirmed, never "out of date":** decide the rule in code, with a test.
  A new profile version whose only change is targets chosen from this slate leaves the slate
  current. Any other change still marks it based on earlier answers. Record the rule in
  ADR 0007 as an amendment line.
- **Routes:** in every workspace, Routes shows its "not built yet" place. The fixture route
  preview stays in Storybook and the design review only.

## Hard rules
- Edit/Write for source changes (the project's own generators are fine: `pnpm run
  generate`, `pnpm run contrast`, `pnpm run screenshots`). No scripts that rewrite files.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live model calls, no web requests, no Docker pull of an uncached image.
- No headed browser, no `open`, no window on the product owner's screen, no frame
  measurement.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Leave `spikes/world` and every running stack alone, and never run `make stop`.
- No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion, with why.
- Never write distress or self-harm text yourself. Reuse the existing fixtures if a support
  test needs one.

## Checks
- Design references: `cd docs/design && pnpm run contrast && pnpm run screenshots`
  (headless). Mirror byte for byte to `apps/web/src/design`. Every new colour pairing goes in
  `contrast-pairs.json`.
- `make check`.
- `make acceptance` once before your final commit, **under the lock** (contract, "Parallel
  work"). If the durable-runs shutdown hang recurs, re-run once and report both runs exactly;
  do not change that test.

## Report
Write the full report to `.superpowers/sdd/l0-sprint-tasks/task-W2E-report.md`. Include:
- each card item, and how a person sees it now (capture paths);
- the re-review findings, each with its test;
- RED then GREEN evidence for each behaviour test;
- every helper line added or cut.

Then reply with only the short contract.
