# Task W2C part 1 review dispatch (two reviewers, split by focus)

You review one half of Task W2, slice W2C part 1 (Careerwright L0, branch `l0-local-release`,
commits 166e4ef..6af1097: 92ea74f, 5c14792, 68c8b2f, 6af1097). Another reviewer takes the other
half at the same time; stay in yours, but read across the line where a finding needs it.

## Read first
1. Your contract: `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`
2. The dispatch the implementer worked from: `.superpowers/sdd/l0-sprint-tasks/task-W2C1-dispatch.md`
   (what part 1 owns, what part 2 owns, the controller's decisions)
3. The carried items: `.superpowers/sdd/l0-sprint-tasks/carry-forward-task-W2C.md`
4. The implementer's report (its readings of session 2's record and its rulings need your
   verdict): `.superpowers/sdd/l0-sprint-tasks/task-W2C1-report.md`
5. The package: `.superpowers/sdd/l0-sprint-tasks/review-166e4ef..6af1097.diff` (6,278 lines;
   read it in parts). Images and lockfiles are excluded; open any PNG in
   `docs/design/screenshots/` with the Read tool to judge it.
6. As needed: the brief `task-W2-brief.md` and `task-W2-slices.md`; CLAUDE.md ("The
   experience", invariants, web layout); `docs/plan/development-plan.md` section 4 and SW.4;
   `docs/adr/0014-the-living-world.md`; the product owner's records
   `docs/reviews/session-2-answers.md` (Part 2 and "Decisions the product owner added at the
   end") and `docs/reviews/session-w1-answers.md`.

## Half A: design and experience
Owns `docs/design/**`, the screenshots, ADR 0014's changes and the experience of the rebuilt
You chapter in the app.
- SW.4, each finding: chat first and immediate; the tone setting in preferences; one idea per
  view; suggestions in their own view; a bright primary action; accept and undo colour coded;
  the two limits explained in plain words. Applied as the product owner recorded it, deciding
  nothing on their behalf (R2)? Judge each of the implementer's readings.
- Does the chapter feel like a place in a world answering the person, or a form over a
  backdrop (CLAUDE.md: "A bland, form-like or corporate screen fails review even if it
  works")?
- "Never overwhelming": the product owner, on a busy test scene, "Wow, the scene looked too
  busy. was overwhelming"; they judged the real screens at 1440 × 900 OK. Count what competes
  at once in each view at the three viewports.
- The implementer's own concerns: the person's light under the console on a phone; counts and
  notes pushing the first suggestion down; the reply field moved under the question. Severity
  and a concrete fix for each.
- Colour: orange destinations only; sea-glass teal for selection, the chosen path and the one
  primary action only. The two new colours (leaf green for accept, orchid for undo): do they
  collide with an existing meaning, and is every new pairing in `contrast-pairs.json` and
  measured?
- References at 1440 × 900, 768 × 1024, 390 × 844, mirrored byte-identical to
  `apps/web/src/design`.

## Half B: app, truth and tests
Owns `backend/**`, `apps/web/src/**` (except the design mirror), `apps/web/e2e/**`, ADR 0007,
the register and the generated client.
- The carried truth fixes (the "must-fix, first" section of the carry-forward file): each line
  now says what the search or match did, never what ESCO contains, true in every case,
  including the nearest unnamed ones; each with a test that reads its words. The hyphen: was
  it confirmed on the test stack before the fix, and is the change disclosed and tested?
- The strip and key items, the flaky phone test (stabilised by waiting, not by loosening), the
  "Your world" DOM list.
- Invariants: the still world shows the same states and words; pause visible; sound off by
  default; nothing implies a job offer; unknown is never zero; the UI takes enums, money and
  error codes from the generated client, shows an error code's words, never the API's message,
  and computes no rank; fixture content labelled. DBOS `application_version` still
  `careerwright-l0-1`.
- Tests: real checks, none passing by construction; every changed assertion justified;
  keyboard-only completion, focus return, axe and overflow at the three viewports; journeys in
  moving and still modes with identical text.
- Scope: part 2's items left as honest, labelled slots, not half-built.

## Hard rules for you
- Read-only on the repository: no edits, no commits, no `git add`.
- No headed browser, ever: nothing that puts a window on the product owner's screen. `make
  check` and a focused headless test run are fine; skip `make acceptance` (the implementer's
  run on 6af1097 passed).
- No Docker pulls or new containers; leave the running `careerwright-l0-*` stack alone.
- Never read `.env`, `~/.nessa` or `~/.careerwright`. No live model or web calls. No subagents.

## Output
Write your full review to the file named in your prompt: spec compliance verdict, quality
verdict, findings ranked Critical / Important / Minor, each with `file:line`, the failure it
causes, and a concrete fix; then your verdict on each implementer reading or ruling in your
half. Reply with only: both verdicts, the count per severity, and one line per Critical or
Important.
