# Task W2E, fix round 1 of 5

You fix Task W2E (Careerwright L0, branch `l0-local-release`, main tree
`/Users/darianraad/Code/careerpathoptimizer`). W2E is commits 8410eff, 7c3a72b, c64b636 and
4dcc2ca. HEAD is now 98fd0a9, because Task 13a's route search was integrated on top: backend
planning only, nothing of yours. You are a fresh implementer. The original's report tells you
what was built and why.

Another implementer (Task 12a) works in a worktree on planning inputs. It never touches the
main tree. Commit with explicit pathspecs. Take the acceptance lock before `make acceptance`.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`, all of it.
2. `task-W2E-review-design.md` and `task-W2E-review-app.md`, both in full. IDs below are D-…
   (design half) and A-… (app half).
3. `task-W2E-dispatch.md` (decisions that still bind), `task-W2E-brief.md` (the card) and
   `task-W2E-report.md`.
4. As needed: `docs/reviews/session-2-answers.md` (the product owner's comments), `CLAUDE.md`
   ("Practical first", the sentence rule), and the audit's
   `docs/reviews/l0-audit-2026-10-31/E-person-path.md`.

## Fix now (each with a test that reads what the person sees, failing before the fix)
- **D-I1:** on a tablet (768) the strip cuts all three facts mid-word although there is
  room. Give each fact the width it needs, not equal shares. The test reads each fact's
  rendered text whole, not just its label.
- **D-I2, with A-M1 (the connection's words):**
  - Each suggestion card and the connection card state the join once.
  - The connection never calls an ESCO title "your role". It names the person's own title as
    they gave it, or says plainly that it is ESCO's occupation.
  - Replace "These are the skills ESCO lists for both roles" with a line that says what
    Careerwright did (the sentence rule).
  - Cut helper lines the product owner would call "not actually helpful". List each line cut
    or kept in the report.
- **D-I3:** on a phone (390), "Edit answers directly" is in the first screen of What we know
  in the fixture workspace. The test uses the fixture workspace (or a long one), not three
  short answers. Correct `docs/reviews/sprint-w.md` where it says "tested".
- **A-I1:** the demo's "couldn't note" reply must never point to a control that isn't shown.
  - Where the example replies are shown, it may name them.
  - At the role-or-explore question, it names the two buttons.
  - After the last question, it says what to do next and never loops: "Skip" there must not
    repeat the same reply.

  Add tests for both of the reviewer's probes.
- **A-I2:** tapping an example reply keeps keyboard focus. It moves to the reply field, or to
  the message just sent, never to the page. Test it.
- **A-I3:** "Name a role" opens target entry once, when tapped. Opening the answer form later
  doesn't re-fire it or change any field's state, and saving isn't refused. Test the reviewer's
  sequence.
- **The product owner's start-page comment** ("It's for inputing information about yourself
  and your job preferences, not sure", session 2). Before the entry choice, the start screen
  says in one plain line what Careerwright is for, for example: "Careerwright helps you find
  work that could suit you, see what it would take, and plan a route you can afford." Keep it
  to one line, and no helper text beyond it. Session W2 judges the words.
- **A minor fixed now (a record that cites removed tests):** UI-09 in the register no longer
  cites the route preview's removed tests.

Every other Minor waits for the final review (R13). The controller has ledgered them.

## Then
- Design references, where these change what a place shows: `cd docs/design && pnpm run
  contrast && pnpm run screenshots` (headless). Mirror byte for byte to
  `apps/web/src/design`.
- `make check`, then `make acceptance` once, under the lock.
- If the durable-runs shutdown hang recurs, re-run once and report both runs; don't change
  that test.

## Hard rules
- Edit/Write for every source change: no scripts that rewrite files, not even one-token
  replacements. Formatters on your own files are fine.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser or window, no frame
  measurement.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Leave `spikes/world` and every running stack alone, and never run `make stop`.
- No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion.
- Never write distress or self-harm text.

## Report
Append a "Fix round 1" section to `task-W2E-report.md`: each finding, its test, the RED and
GREEN evidence, and the commands with their output. Reply with only the short contract.
