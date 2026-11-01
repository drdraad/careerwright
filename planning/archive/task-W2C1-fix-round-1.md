# Task W2C part 1, fix round 1 of 5

You fix Task W2, slice W2C part 1 (Careerwright L0, branch `l0-local-release`, HEAD 6af1097;
part 1 is 166e4ef..6af1097). You are a fresh implementer: the original report tells you what
was built and why. Two reviewers split the work: design and experience, and app, truth and
tests. Finding IDs below are prefixed D (design review) or A (app review).

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`
2. `task-W2C1-review-design.md` and `task-W2C1-review-app.md`, both in full
3. `task-W2C1-dispatch.md` (the controller's decisions that still bind) and
   `task-W2C1-report.md`
4. As needed: `carry-forward-task-W2C.md`, `task-W2-slices.md`, CLAUDE.md ("The experience",
   invariants), `docs/plan/development-plan.md` section 4 and SW.4, ADR 0007 and 0014,
   `docs/reviews/session-2-answers.md` (Part 2 and the closing decisions)

## Controller rulings
- **D-I5, helper text:** apply plan section 4 ("Helper text appears only where it helps"),
  which records session 2's finding. Go through each helper line in the chapter: keep a line an
  invariant needs (a truth statement, a gate in plain words, "usual in your role, not
  confirmed yet", synthetic labels, a reason one step away), cut or fold procedural ones. List
  every line cut or kept, with why, in the report: session W2 judges the result.
- **D-I3, the suggestions view:** the bright "Make this a target" is in view at 1440 × 900
  with a real slate. Fold the slate's notes into one disclosure, move the actions up the card,
  and redraw the reference with a real slate (P03's or "data analyst"), not a tidy one.
- **D-I4, one decision at a time:** hold the next question back until the tray is decided.
- **D-I2, the world on tablet and phone:** the person's light is visible in every view at
  768 × 1024 and 390 × 844, in the app and the references, with a test that would fail if a
  band fell under `MIN_BAND`.
- **A-I1, nothing typed is lost:** keep the three views mounted and hide the inactive ones;
  a test switches views mid-task (a typed reply, tray choices, form edits, "Not for me"
  picks). This also covers A-M2 on tabs; keep the "asked" state per discovery outside the
  component so a chapter change can't re-send a refused note request either (ADR 0007
  decision 12: only by the person's click), with a test.
- **D-M6, the early sketch:** it is a second idea in What we know; put it behind a disclosure
  there. Session W2 can move it.
- **D-M7, the world answering decisions:** not this part. Carried to part 2 (the controller
  records it).
- **To session W2's sheet, not fixed:** D-M3 (leaf green near destination orange under
  simulated deuteranopia; words and glyph carry the meaning), A-M6 (the tablet strip drops
  work areas and budget). The controller records them.

## Fix now
D-I1 (the duplicate `.facts` rule: rename, recapture every affected reference, and add a
clipped-text check to `screenshots.mjs` so `checks.md` can't pass a clipped capture), D-I2,
D-I3, D-I4, D-I5 as ruled; A-I1 with A-M2 as ruled; A-I2 (focus to the form's heading or first
field after "Add the details yourself", with a test); A-I3 (the three API descriptions say what
the match did; `pnpm run generate`) and the sketch's `not_found` words (`vocabulary.ts`, "Not
found in ESCO") under the same rule.
Minors: D-M1 (a chosen accept is not a second bright fill; count it in the one-primary check),
D-M2 (drop the teal edge on a chosen proposal), D-M4 (the tone shows "Practical (the default)"
while unset, a saved confirmation, and a "Preferences for this workspace" heading), D-M5 (no
"version" on screen), D-M6 as ruled, A-M1 (the phone strip stays one row in every update
state, reconnecting case tested), A-M3 (the open suggestion's header follows the ARIA
accordion pattern), A-M4 (one assertion each, or narrow the register's words to what is
tested), A-M5 (say in the docstring and ADR 0007 that a hyphenated skill name typed with its
hyphen no longer counts as exact; ranking unchanged), A-M7 (while paused, Resume is the view's
primary and Send is secondary).

## Then
- Design references: `cd docs/design && pnpm run contrast && pnpm run screenshots` (headless),
  mirror byte-identical to `apps/web/src/design`. Every new pairing in `contrast-pairs.json`.
- `make check`; then `make acceptance` once before the final commit (check `pgrep -fl "make
  acceptance"` first). If a known flake recurs (the durable-runs shutdown hang), re-run once and
  report both runs exactly; do not change that test.
- Hard rules: Edit/Write only for source changes (no scripts that rewrite files; the project's
  own generators are fine); stage explicit paths; never `answers-2.md`; never `.env`,
  `~/.nessa`, `~/.careerwright`; no live model call; no web request; no Docker pull of an
  uncached image; no headed browser or window on the product owner's screen; no frame
  measurement; leave `spikes/world` and the running `careerwright-l0-*` stack alone; no
  subagents; never push. DBOS `application_version` stays `careerwright-l0-1`. Disclose every
  changed test input or assertion, with why.
- Append a "Fix round 1" section to `task-W2C1-report.md`. Reply with only the short contract.
