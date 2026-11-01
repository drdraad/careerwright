# Review: the approved audit changes written into the documents (Task A1, apply)

You review one documents-only change in Careerwright L0 (branch `l0-local-release`, commits
fde8e7d..ec4d060). The product owner approved an audit on 2026-10-31. An implementer wrote
its changes into the plan, the task file, the ADRs, the register, the specification's
revision record and `CLAUDE.md`. Future implementers' briefs are extracted card by card from
`docs/plan/l0-sprint-tasks.md`. So a missing, wrong or invented requirement in a card becomes
wrong code later.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its new calibration.
2. What was approved, which is the authority for this review:
   - `docs/reviews/l0-audit-2026-10-31.md`, the report, all of it;
   - `docs/reviews/l0-audit-2026-10-31-summary.md`, decisions 1–8 (all yes) and question 9
     (yes: five testers).
3. The implementer's instructions, `.superpowers/sdd/l0-sprint-tasks/task-A1-apply-dispatch.md`,
   and its report, `.superpowers/sdd/l0-sprint-tasks/task-A1-apply-report.md` (unverified
   claims; read its rulings and concerns closely).
4. The diff: `.superpowers/sdd/l0-sprint-tasks/review-fde8e7d..ec4d060.diff` (3,744 lines).
   Read it in passes.
5. The appendices the cards draw on, as you need them: `docs/reviews/l0-audit-2026-10-31/`
   (D section 4, F sections 5–6, A sections 3 and 5, E section 2, B sections 2 and 6, G).

## Check
1. **`CLAUDE.md`:** the four edits match the report's section 7 word for word, and nothing
   else changed.
2. **The order and dependencies** in the task file match the report's section 4 table:
   - the role space (6d, 6e) and live sessions (3b) come before a short session W2;
   - 12a and 13a run during it;
   - "add an option yourself" is in 12b;
   - 7e comes after Plan;
   - Roles comes after the end-to-end session;
   - M comes before release.

   Check that no card's Preconditions line contradicts the dependency rules, and that no
   circular wait exists.
3. **Each new or revised card** (W2E, 6d, 3b, 6e, 12a, 12b, 7e, M, 8, 10, 13a, 13b, 14, 15,
   16, 17) has:
   - **Preconditions** and **Parallel** lines;
   - observable scope and acceptance;
   - its register rows.

   Check that it carries what the report and its appendices assign to it, and nothing they
   don't. In particular:
   - W2E holds the appendix E items the dispatch named, and room for the re-review's carried
     findings.
   - 6d holds appendix F's first step, its acceptance test and the target record stored once.
   - 3b holds the Muse Wonder set-up: the controller runs the live calls; caps; the cost-log
     copy; the spending line.
   - 12b holds "add an option yourself".
   - 7e holds option research.
   - Routes built on records that are not reviewed are qualified, never an unqualified
     "affordable and feasible".
4. **The standing rulings** R4 and R10–R15 say what the report's section 6 and the approval
   say, including the product owner's parallel-work words.
5. **The ADR amendments and the new ADR 0015** are faithful to the report and appendix F.
   They invent no decision. Undecided points name who settles them.
   - The ADR 0003 amendment was appended with a shell heredoc (disclosed): check that file
     reads cleanly.
6. **The register:**
   - the orphaned rows are reassigned or deferred;
   - the three industry-colour rows are fixed;
   - H-13 is transcribed faithfully from `docs/reviews/session-2-answers.md`;
   - DIV1-04 is corrected;
   - the sessions table and H-05 are updated;
   - the new rows have owners.
7. **The specification:** only a dated section 22 subsection was added; no invariant is
   relaxed.
8. **Truth and honesty:**
   - nothing claims a human gate passed;
   - nothing says a session happened that didn't;
   - the PO's words are quoted verbatim where quoted.
9. **Known points to verify, not pre-judged:**
   - The implementer reports that the report's total, "80–150 agent hours", isn't the sum of
     its rows (about 89–168). Check what the plan now says.
   - The implementer's rulings (its report's numbered rulings, for example pay lanes kept,
     revision history deferred, export in 15A, the PO's commands in acceptance under 3b,
     13b's durable parts kept as M0 unless the PO says otherwise): flag any that contradicts
     the report or the specification.

## Rules
- Read-only. Never modify the working tree, index, HEAD or branches. Another implementer
  works in a separate worktree; the main tree may change only in files you are not
  reviewing.
- `make check` passed on ec4d060 (the implementer's run); don't re-run it.
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`.

## Output
Write the review to `.superpowers/sdd/l0-sprint-tasks/task-A1-apply-review.md`, in the
contract's format (Spec Compliance, Strengths, Issues by severity with `file:line`,
Assessment). Then reply with at most 10 lines: counts by severity, each Critical or Important
item in one line, and the file path.
