# Report: plan update for school leavers (plan v1.6), documents only

Branch `wt-plan`, one commit on dc68d79: **656dd64**. Four files, nothing else touched. No
code, no `CLAUDE.md`, no web requests, no live calls, no subagents, no Docker.

## What changed, and where

**Specification, section 22** (`Careerwright_Product_Specification.md`)
- Heading now "L0 build decisions, 2026-10-31 and 2026-11-01". The intro says four rows change
  a section for L0 (each marked in bold): DIV-1's corroboration (existing), who it's for, the
  opening question, the tuition fee loan. Version stays 1.3.
- New rows, placed before "L0 deferrals" so that row stays last:
  - School students aged 17 and 18 (sections 1 and 2): in scope; no age is asked; each
    scheme's age rule is shown beside it; the release checks the rules for young people's data
    before any real student uses Careerwright.
  - The opening question (section 4): one that works without a job; the product owner settles
    the words.
  - A tuition fee loan paid straight to the university (sections 10 and 12): not the student's
    own cash or spending; shown as a loan to repay; never support; an unapproved loan leaves
    the route conditional; every other loan stays information. Names the plan's "a loan is
    never support" rule as changed for this one loan.
  - Routes longer than the planning model: said plainly; no planning change.
- "L0 deferrals" row: adds "free from September" as a known limit.

**Development plan** (`docs/plan/development-plan.md`)
- Header now v1.6 (1 November 2026). New "Version 1.6" note under "How to use this plan".
- Section 1: the Product journey row (17- and 18-year-olds in scope), the Planning model row
  (routes over 24 months in plain words; the tuition fee loan; "free from September" a known
  L0 limit), and the privacy paragraph (young people's data).
- New S2.10 "No job yet". S2.9 gains the synthetic school leaver. Sprint 5 gets a v1.6
  paragraph (the loan, the oracle written fresh, the checkpoint lines). S7.5 and S9.5 each
  get one sentence.
- Section 6: the roadmap rows for Sprints 2 and 5; a new "Order from here (v1.6)" note (two
  tracks, card lines, hours); one sentence on the new short session.
- Section 9: the school-leaver pack version. Section 10: the W2 row (S2.10, the school leaver
  among the people) and a new row for the school-leaver pack session.

**Task file** (`docs/plan/l0-sprint-tasks.md`)
- New cards: `## Task 6f:` (after 6e), `## Task 7f:` (after 7e), `## Task 12c:` (after 12b).
- Lines on existing cards:
  - 6e: preconditions now include 6f; the school leaver and her 4–6 cases; the live run of
    6f's prompt; her place in session W2's package, plus one Childline line.
  - 10: needs 6f; qualifications as entry facts (expected never met); no empty "usual in your
    role" panel.
  - 12b: needs 12c and 7f; words for someone not working; the entry confirmation; age rules;
    the loan question.
  - 14: needs 12c; plain words for a route longer than the model; the loan shown as a loan.
  - M: the world answers someone with no job.
  - 7e: apprenticeships, degrees and their funding.
  - 8: apprenticeship listings marked; a pasted apprenticeship advert.
  - 16: young people's data (H-15); new tasks and session in its preconditions.
- R10: session W2 now waits for 6f and names the school leaver. New session bullet: "the
  school-leaver pack session" (short; it gates 7f's publishing half and, through it, 12b).
  H-15 added to the release checks.
- Order section: rules 7, 11, 13, 15 and 16 amended; new rules 19 (12c) and 20 (7f); the v1.6
  suggested order; v1.5's order moved to History.
- "Current position" rewritten for 2026-11-01:
  - complete: 3b, 6d slices A and B, 12a, 13a, 13b, W2E and A1's documents;
  - finishing: 6d slice C (finishing, not complete, per the ledger);
  - the product owner's decisions since v1.5;
  - a table showing where each of the 10 decisions goes;
  - the walk's other lines;
  - running now and next, in order.
- The two stale paths: `/Users/darianraad/Code/careerwright/.env` and
  `/Users/darianraad/Code/careerwright-wt/<id>`.

**Register** (`docs/requirements-register.md`)
- Header now v1.6, with a "Plan v1.6" paragraph listing the new rows. Owners table: T6f, T12c,
  T7f.
- New rows:
  - STATE-11 (T6f, T10)
  - PROF-13 (T6f, T10, T12b)
  - PROF-14 and PROF-15 (T6f)
  - TEST1-16 (T6e)
  - FUNDING-06 (T12c, T12b, T14)
  - OPTN-14 (T7f), OPTN-15 (T12b), OPTN-16 (T7e)
  - PLN-12 (T14), JOB-09 (T8), WLD-12 (TM), H-15 (T16)
  - a sessions-table row for the school-leaver pack session
  - a section 7 row for "free from September"
- FUNDING-04 now states the L0 change and lists T12c as an owner.
- The sessions intro sentence now includes the new session. No other row changed.

## Checks run

- **make-brief's awk, run on the worktree's file.** It found exactly one heading per card:
  - 6f: card 93 lines, brief 634 lines
  - 12c: card 73 lines, brief 614 lines
  - 7f: card 70 lines, brief 611 lines
  - The preamble is 541 lines. 6d, 6e, 7, 7e, 8, 10, 12a, 12b, 14, M and 16 still extract one
    card each, and Task 7 does not swallow 7b, 7e or 7f.
- **New register rows have the right number of columns.** Each matches its table's header.
  PLN-11 already had one extra cell before this change; I left it alone.
- **Merge check against slice C's uncommitted edits in the main tree.** I ran `git merge-file`
  on copies in the scratchpad; nothing in the main tree was written. The plan, the task file
  and the specification merge cleanly. The register has one conflict (below).

## The merge conflict to expect at rebase

- **Register, end of the PROF table.** Slice C edits PROF-12, and my PROF-13 to PROF-15 go
  straight after it. To resolve: keep slice C's PROF-11 and PROF-12, then my three rows.
- **Plan section 1.** Slice C's uncommitted edit rewrites the "L0 deferrals (v1.5)" row (the
  CV deferral). To avoid a conflict on that one long line, I recorded "free from September" in
  the Planning model row of the same table, as "a known L0 limit, not built". If you want it
  in the deferrals row as well, add this after slice C lands: `; and hours that change on a
  date ("free from September"; the product owner, 1 November 2026: a known limit)`.

## CLAUDE.md wording to propose (needs the product owner's yes)

1. Planning invariant, the line "Only an approved award counts unconditionally; a loan is
   never support." Proposed:
   "Only an approved award counts unconditionally; a loan is never support. One L0 exception
   (spec section 22, 2026-11-01): a tuition fee loan paid straight to the university is not
   the person's own spending or cash; it is shown as a loan to repay later, and one not yet
   approved leaves the route conditional."
   Task 12c's card also asks for this proposal, so it can wait for 12c.
2. Line 5: "`docs/plan/development-plan.md` (v1.4)" → "(v1.6)". This was already stale at
   v1.5.

## Assumptions and open points

- **Childline's review.** I placed it in session W2's package, as one yes/no line counted
  under H-12. The dispatch says "reviewed with the support policy" but not where.
- **The no-job answer** is stored as an answer about the current role: never a job title,
  Skipped or Unknown. The exact storage is 6f's to settle. "Skip for now" still saves nothing,
  so the light stays dark. The walk's interim fix for that was not approved as a separate
  decision, so it is not in 6f.
- **Who pays for what.** Only the university tuition fee loan is changed. An Advanced Learner
  Loan is also paid to the provider, so the product owner may want to say whether it follows.
  12c's card keeps every other loan as information.
- **The economic cost of the loan** is left for 12c to settle, with one question to the
  product owner if it changes which routes are best (R14).
- **7f is one card in two halves**: curate, then the session, then publish. The 7f slot is
  blocked while the session is awaited. 12b now waits for that session.
- **Rows I did not change** (outside "new rows plus FUNDING-04"). The register's sessions-table
  W2 row still says "After Tasks W2E, 6d, 3b and 6e" and doesn't name the school leaver. H-08
  is unchanged (H-15 sits beside it). The rows 6f will extend (PROF-07, PROF-08, STATE-08)
  don't list T6f yet; its card says they gain a 6f part.
- **Where the walk lives.** The cards cite the gitignored
  `.superpowers/sdd/l0-sprint-tasks/audit-no-job-yet.md`. Consider committing a copy under
  `docs/reviews/`, since the repository is now public and the cards point to it.
- **Background facts not checked.** These come from the walk and need no web check in the
  plan: tuition fee loans are paid to the university; apprentices pay no training fee;
  Childline serves people under 19. 7f's pages and the Childline check confirm them.
- **The Nessa file renames** (spec and task-file references to `Nessa_M0_Fixtures.zip`) are
  left for the rename point, as the ledger rules.
