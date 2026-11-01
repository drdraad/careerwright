# Task 6d slice B, fix round 2 of 5

You fix Task 6d slice B once more (Careerwright L0, branch `l0-local-release`, main tree
`/Users/darianraad/Code/careerpathoptimizer`). FIX_BASE 667426e. Fix round 1 was 2e05426..667426e;
its re-review approved the app half and found two new Important items in the design half. You
are a fresh implementer.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`, all of it, including the acceptance lock.
2. `task-6dB-rereview-1-design.md` and `task-6dB-rereview-1-app.md`, in full.
3. `task-6dB-fix-round-1.md` (its rulings still bind) and the "Fix round 1" section of
   `task-6dB-report.md`. Background as needed: `task-6dB-dispatch.md`, `task-6d-brief.md`.

## Fix now (each behaviour change with a test that fails before the fix)
1. **Design, Important R-I1: the title field's support panel renders below the field.** On a
   phone it likely sits under the keyboard. Show it above the field, where the message panel
   sits above the reply field. Test its position at 390 × 844 (layout, not a real keyboard).
2. **Design, Important R-I2: "None of these is my job" is below a phone's first screen** on the
   partial list, so a person may tap a guess that isn't their job. Keep "None of these is my
   job" (and "Use my own words") inside the first screen on a phone, for example by placing
   them first or showing fewer options on a narrow screen. Extend the UI-12 phone test to the
   partial list.
3. **A real job title that trips the support screen (re-review R-M3).** Today the panel says the
   title wasn't kept and names no way forward. That conflicts with the card's "nothing typed is
   refused".
   - **Ruling:** the panel shows and the world stills, as now. The title is still not kept
     automatically. The panel offers a plain way forward: keep the words as the job title, by
     the person's explicit choice, or type again, or skip.
   - Keeping it saves the title exactly as typed (as "Use my own words" does), through the same
     command. Nothing about the panel is stored or used for suitability.
   - Tests use the existing risk-word fixtures only. **Never compose new distress or self-harm
     text.** The panel's words stay "not yet reviewed as built" (session W2 reviews them).
4. **The product owner's decision (31 October 2026): What we know's direct entries go through
   the support screen too.**
   - A direct entry with a listed risk word, in any form, shows the same calm support panel and
     stills the world. Like a message, the entry is still saved: it is the person's own direct
     edit. Nothing about the panel is stored or used for suitability.
   - Use the one support policy (`careerwright/profile/safety.py`); record the change in its
     version and review status, and in ADR 0007.
   - Tests use the existing risk-word fixtures only.
5. **App note: the screened type-ahead response returns the typed words.** `CLAUDE.md`: never
   echo request input. When the screen triggers, the response carries no typed text, only the
   fact. Test it.
6. **Design, Minor R-M1:** keep the arrowed option by its key, or reset it when the list
   changes, so Enter never picks an option that moved under the person. Test it.
7. **Design, Minor R-M2:** the title panel stays until the person dismisses it, as the message
   panel does, even after "Skip for now" or a different saved title. Test it.
8. **Design, Minor R-M4:** while fixing a title, the button that returns to "Which of these is
   closest?" is labelled for what it does, not "Skip for now". Test it.
9. **App, new Minor 2:** a test that the conversation's change of the role keeps the role's
   record (the same write path as What we know).

## Not now (the controller has it)
- App new Minor 1 (a role chosen from ESCO before round 1 can be overridden by another saved
  record of the same title; old data only): the final review.

## Then
- `make check`, then `make acceptance` once, whole, under the lock (one guarded command). If a
  test fails, re-run the whole `make acceptance` and report both runs.
- Review captures for the places you change: `cd apps/web && pnpm run review-screenshots`;
  design references only if a reference place changes.

## Hard rules
- Edit/Write for every source change: no heredocs or scripts that rewrite files, not even to
  append. Formatters on your own files and the project's generators are fine.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser. Never start Docker or open
  an app or window.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`. No subagents. Never push.
- Migrations are forward-only. DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion.
- Never write distress or self-harm text.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append a "Fix round 2" section to `task-6dB-report.md`: each finding with its test, the RED and
GREEN evidence, and the commands with their output. Reply with only the short contract.
