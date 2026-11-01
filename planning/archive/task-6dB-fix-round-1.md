# Task 6d slice B, fix round 1 of 5

You fix Task 6d slice B (Careerwright L0, branch `l0-local-release`, main tree
`/Users/darianraad/Code/careerpathoptimizer`; slice B's commits dff9c2e, 2317e19, 21a397d). You
are a fresh implementer: the original's report (`task-6dB-report.md`) tells you what was built
and why. Task 13b (the route search as a run) was integrated just before you started, with its
migration 0037: your next migration, if any, is the next free number then.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`, all of it, including the acceptance lock.
2. Both review halves, in full: `task-6dB-review-design.md` and `task-6dB-review-app.md`.
3. `task-6dB-dispatch.md` (decisions that still bind), `task-6d-brief.md` (the card) and
   `task-6dB-report.md`.

## Fix now (each behaviour change with a test that fails before the fix)
1. **Design, Important 1: Enter on a partial list saves ESCO's first guess.** Enter never picks
   a partial match the person didn't select; their typed words are never lost. Results from an
   earlier search never stand as the answer for new text while new results load. Test both.
2. **Design, Important 2, with app Minor 5: "None of these is my job" in the type-ahead isn't
   recorded.** Record the refusal through a versioned command (expected version and
   `Idempotency-Key`, like every consequential write), from every place it is offered, so no
   view then says "Choose the ESCO occupation closest to it". Acceptance item 3 must pass in
   full. Test it, including a stale expected version.
3. **Design, Important 3: the first question's title field skips the support screen.**
   - **Ruling:** the title field goes through the same support policy as interview messages
     (`careerwright/profile/safety.py`). A listed risk word, in any form, shows the calm support
     panel and stills the world. The title is not kept as a role and never echoed back as
     "your role"; the person can type again or skip. Nothing about the panel is stored or used
     for suitability.
   - Check every other free-text input this slice added ("Use my own words", the closest step)
     the same way.
   - Tests use the existing risk-word fixtures from the support policy's tests. **Never compose
     new distress or self-harm text.**
4. **App, Important 1, with app Minor 1: the role's closest occupation is stored in two places.**
   Make the title record the role's one truth, as slice A made it each target's. An edit to the
   role's words (in What we know or the conversation, capitals included, or away and back)
   keeps or re-decides the record by the one `resolve_target`, never loses the person's choice
   silently, and never leaves the origin saying "chosen" for an occupation it no longer names.
   `choose_role` stores the role's record, so `RoleOut.kind` is right for a role chosen by one
   of ESCO's other titles. Test: edit the role and check the origin, the skills and a
   same-titled target.
5. **App, Minor 4: the CHECKs repeat this slice's rules.** An ONS record has at least one SOC
   and one ISCO-08 code; `none_of_these` is set only on an ONS title, with `recorded_by`. In a
   new forward migration (never edit 0034, 0035 or 0036). Test each CHECK refuses.
6. **App, Minor 2:** a test that the type-ahead, "Use my own words" and the slate answer 503
   `REFERENCE_DATA_UNAVAILABLE` without the index.
7. **App, Minors 6 and 7, words only:** record the known limits in ADR 0015 and ADR 0012
   (exact spelling against the concept key; an index title whose ESCO twin has "&" or an
   accent; importance edits on re-decided pack rows; own-words records on a database that got
   the index later; `lower()` against `casefold()`).
8. **App, Minor 8:** tests for a closest choice for the role becoming a same-titled target's
   occupation, a "Use my own words" title of only punctuation, and the failure path of the
   `title_idea_reasons` check.
9. **Design, Minor 1 (WCAG 2.2 4.1.3):** the combobox, not the listbox, is described; the
   partial and none-found lines and the result count are in a polite status region. Test it.
10. **Design, Minor 2:** "Something different" only where the API's own fact says the role's
    families are known; for a role kept in the person's words or after "None of these is my
    job", say less. Test it.
11. **Design, Minor 3:** stories and review captures of the type-ahead open (UK title, partial
    question, none found) and the closest step at 390 × 844, and the closest step and the entry
    choice with its kept-words line checked on a phone. The real phone keyboard stays a human
    check.
12. **Design, Minor 4, the first part:** a way back from "Which of these is closest?" to the
    title field, to fix a wrongly picked title. Test it.
13. **Design, Minor 5, two parts:** no "(ISCO-08 2221)" code in what the person reads (plain
    words only); and a title whose groups hold no ESCO occupation never asks "Which of these
    is closest?" with nothing to pick. Test both.
14. **Design, Minor 6:** replace the e2e assertion that can't fail with one that can, or remove
    it and say so.
15. **Design, Minor 8:** while a closest choice saves, only the chosen button says "Saving…";
    `leaving` is cleared when a save fails, so focus never moves unasked. Test both.

## Not now (the controller has them)
- App Minor 3 (the nursing-field rule blocks named fields instead of allowing neutral ones):
  recorded as a known L0 limit in ADR 0012 (part of item 7). The card allows one matching round.
- Design Minor 4's second part (a role named later never sees the type-ahead or the closest
  question): the final review.
- Design Minor 5's third part ("None of these is my job" edged in the action colour), Minor 7
  (an index title idea can't be made a target where it's shown) and Minor 9 (two free-text
  fields at the start): questions for session W2.

## Then
- `make check`, then `make acceptance` once, whole, under the lock (one guarded command). If a
  test fails, re-run the whole `make acceptance` and report both runs.
- Design references and review captures for the places you change:
  `cd docs/design && pnpm run contrast && pnpm run screenshots` (mirrored byte for byte), and
  `cd apps/web && pnpm run review-screenshots`.

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
Append a "Fix round 1" section to `task-6dB-report.md`: each finding with its test, the RED and
GREEN evidence, and the commands with their output. Reply with only the short contract.
