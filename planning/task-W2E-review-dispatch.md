# Review: Task W2E, finish the You chapter (two halves)

Careerwright L0, branch `l0-local-release`. Task W2E's commits are 8410eff, 7c3a72b, c64b636
and 4dcc2ca (base ec4d060). The documents commits between them (694a10d..0931cbb) were
reviewed separately; they are not yours. Two reviewers split this task by focus. Your
dispatch line names your half.

- **Design and experience half:** what the person sees and does:
  - the demo conversation;
  - the confirmed target;
  - named shared skills;
  - the phone and tablet layouts;
  - the rail's marks;
  - one bright action;
  - the pauses;
  - the "England only" line;
  - Routes "not built yet";
  - the world placed again after a view change;
  - the design references and their checks;
  - the Sprint W review (`docs/reviews/sprint-w.md`).

  Start from the product owner's own session comments (R14): `docs/reviews/session-2-answers.md`
  and `docs/reviews/session-w1-answers.md`. For each comment this task touches, say done or
  not done.
- **App, truth and tests half:**
  - the backend: the demo interviewer's new patterns, and the rule that keeps a slate current
    after a target is chosen;
  - the API and the regenerated client;
  - the web's state and words (`vocabulary.ts`; the sentence rule; R11's facts-not-sentences
    rule for any API response this task adds or changes);
  - focus and keyboard;
  - tests that prove what they claim;
  - the register rows and the ADR lines.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration (grade
   by the effect on the person; minors wait for the final review).
2. The brief, `.superpowers/sdd/l0-sprint-tasks/task-W2E-brief.md`, and the dispatch,
   `task-W2E-dispatch.md`. The dispatch carries the re-review's findings N1, N2 and N3, which
   must be fixed here.
3. The implementer's report (unverified claims), `task-W2E-report.md`. Judge its concerns:
   - a one-token edit made with a Python replace;
   - the ten-second bar is not met, and is moved by plan v1.5 to Task 6d and Sprint M;
   - a rare demo case is recorded as a limit;
   - the N1 browser test was not run against the old build;
   - **the design check now treats rows that scroll sideways as not clipping.** Is that
     check now weaker than what it guarded?
   - the route preview's layout tests were removed along with the preview.
4. The package, `.superpowers/sdd/l0-sprint-tasks/review-W2E.diff` (7,430 lines). Read your
   half's files in full, and skim the rest for anything that crosses into your half.
5. Evidence:
   - the audit's person-path appendix, `docs/reviews/l0-audit-2026-10-31/E-person-path.md`
     (F1, F2, F5, F7, F8, F10, F14, F17: the "before" this task fixes);
   - the last acceptance run's captures, `apps/web/test-results/visual-*/screenshots/` (from
     W2E's run on c64b636; check their times);
   - the design references, `docs/design/screenshots/`.

   Read images with the Read tool.

## Rules
- Read-only. Never modify the working tree, index, HEAD or branches. Other agents work in
  worktrees, and the main tree may change outside these files.
- `make check` and `make acceptance` passed (the implementer's runs). Don't re-run suites.
  One focused test is fine for a specific doubt.
- No web requests, no live calls, no Docker, no browser tools, no headed browser, no `open`.
  No subagents. Never read `.env`, `~/.careerwright` or `~/.nessa`.

## Output
- Design half: `.superpowers/sdd/l0-sprint-tasks/task-W2E-review-design.md`.
- App half: `.superpowers/sdd/l0-sprint-tasks/task-W2E-review-app.md`.

Use the contract's format. Then reply with at most 10 lines: counts by severity, each Critical
or Important item in one line, and the path.
