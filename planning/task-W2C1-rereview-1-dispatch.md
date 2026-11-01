# Task W2C part 1: scoped re-review of fix round 1

You re-review one fix round of Careerwright L0 (branch `l0-local-release`). It is not a fresh
review. Verdict each finding below, and inspect the fix diff for new breakage. That is all.

## Read first (all in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`)
1. `reviewer-contract.md` (read the calibration section closely: it changed on 2026-10-31,
   when the product owner approved the audit. Grade by effect on the person; minors wait for
   the final review).
2. `task-W2C1-fix-round-1.md`: the findings under verification, with the controller's
   rulings on how each was to be fixed.
3. `task-W2C1-review-design.md` and `task-W2C1-review-app.md`: the original findings (IDs D-…
   and A-…).
4. `task-W2C1-report.md`: read its "Fix round 1" section (the implementer's claims, unverified).
5. The fix diff: `review-6af1097..f179d0f.diff` (4,600 lines; fix base 6af1097, head
   f179d0f). Read it once, in passes if needed.

Context: the product owner has since approved an audit (`docs/reviews/l0-audit-2026-10-31.md`,
committed). Its section 2 ("What a person hits today") and appendix E list problems in the You
chapter that are **not** part of this fix round (the demo interviewer's loops, a chosen target
shown as out of date, shared skills unnamed, the phone band, the key button over the
Suggestions tab). A follow-on task fixes those. Do not re-report them as findings here. If the
fix diff makes one of them worse, that is new breakage: report it.

## Scope
- Verdict every finding in the fix list's "Fix now" section, the minors it lists, and each
  controller ruling that changed what "fixed" means: ADDRESSED, PARTLY ADDRESSED or NOT
  ADDRESSED, with `file:line` evidence.
- Items the fix list sends to session W2 or to part 2 are not findings here.
- New breakage: problems the fix diff itself introduced, graded per the contract.
- Anything outside the fix diff goes under "Out-of-scope observations", one line each. They
  never extend the loop.

## Rules
- Read-only. Never modify the working tree, the index, HEAD or branches. Another agent is
  editing documents (`docs/plan`, `docs/adr`, `docs/requirements-register.md`, `CLAUDE.md`)
  in this tree while you work. To read code exactly as reviewed, use
  `git show f179d0f:<path>`.
- Do not re-run the implementer's suites. Run one focused test only when reading raises a
  specific doubt no existing run answers.
- No web requests, no live model calls, no Docker commands, no browser tools, no headed
  browser, no `open`. Read images with the Read tool. Captures from the last acceptance run on
  f179d0f are in `apps/web/test-results/visual-*/screenshots/`. The design references are in
  `docs/design/screenshots/`.
- Never read `.env`, `~/.careerwright` or `~/.nessa`. No subagents.

## Output
Write the full re-review to `task-W2C1-rereview-1.md` (same directory), in this shape:
- A verdict table: finding | verdict | evidence.
- New breakage, by severity.
- Out-of-scope observations.
- An assessment: Approved, or Needs fixes (list exactly which).

Then reply with at most 10 lines: the counts per verdict, new Critical and Important items in
one line each, and the file path.
