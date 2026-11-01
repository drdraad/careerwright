# Plan update: school leavers (documents only), in a worktree

Careerwright L0. On 1 November 2026 the product owner said: "NB: I don't want to over-rely on
existing skills in the process. Many users will be final year school students who have never
had a job before." A read-only walk of the whole path as a Year 13 student with no job found 8
problems and 10 decisions. The product owner answered: decisions 1–9 yes, decision 10 no
("A and B, not #10"), and approved where each fits ("go"). You write those approved changes into
the plan documents. **No code.**

## Your tree
- Worktree `/Users/darianraad/Code/careerpathoptimizer-wt/plan`, branch `wt-plan`, from
  `l0-local-release` at dc68d79. Work and commit only there.
- In the main tree, Task 6d slice C is finishing; its last commit edits
  `docs/requirements-register.md` (its own rows). The controller rebases your branch after it
  lands; keep your register edits to new rows and the rows named below, so a merge stays simple.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `CLAUDE.md` ("Talking to the user" binds the plan's plain words too, where the product owner
   reads them).
2. The walk: `.superpowers/sdd/l0-sprint-tasks/audit-no-job-yet.md`, all of it. Section 2's table
   gives each change, its owner and size; section 4 the 10 decisions.
3. `docs/plan/l0-sprint-tasks.md`: the header, Global Constraints, standing rulings R1–R15, the
   order section ("Order, dependencies and dispatch preconditions", "Current position and next
   tasks") and the cards it names below. Match the existing card format exactly (title line,
   **Preconditions:**, **Parallel:**, Sprint card, Deliver, Acceptance, Register).
4. `docs/plan/development-plan.md` section 1 (the local delivery boundary and L0 deferrals) and
   section 6 (the roadmap and "Order from here").
5. `Careerwright_Product_Specification.md` section 22, "L0 build decisions, 2026-10-31": the
   table you add to.
6. `docs/requirements-register.md`: the header (how rows are added for new behaviour).

## The approved decisions
1. **Who it's for:** school students aged 17 and 18 are in scope. The specification's "adult"
   lines (section 1 "Primary customer", the FAQ at line 111) are applied for L0 through a new
   section 22 row (don't edit those sections: section 22 records how L0 applies the
   specification). Before any real student uses Careerwright, the release checks the rules for
   young people's data (Task 16's privacy note).
2. **"I haven't had a job yet"** beside "Skip for now" at the first question: the answer is
   saved, the person's light comes on, and the conversation asks what they enjoy instead of
   their job; it is never asked again.
3. **Two optional answers:** what you're doing now (working, in education or training, looking
   for work, caring, other: the specification's work status) and qualifications you have or are
   taking (each achieved or expected). Skills and Options later read them as entry facts; an
   expected grade is never counted as met.
4. **The opening question** works without a job (for example "What would you like your working
   life to be like?"; the wording is session W2's), with the word pass in the walk's section 2
   row 3.
5. **A synthetic school leaver** (17, Year 13, A-levels in progress, no job, helps at a youth
   club, unsure, Leeds), labelled synthetic and kept apart from the supplied pack
   (`fixtures/m0` never changes), with 4–6 evaluation cases; she is one of session W2's personas.
6. **A tuition fee loan paid straight to the university** is not cash out of the student's
   pocket; it is shown as a loan to repay later. This changes, for L0, the rule that a loan is
   information only (spec section 10, FUNDING-04; `CLAUDE.md` "a loan is never support"): say so
   in the section 22 row. The checker and Task 13a's separate oracle both change.
7. **Degrees longer than the 24-month model:** Routes says plainly that the route is longer than
   Careerwright can plan yet. Words only, no planning change.
8. **A new reviewed option-pack version** with school-leaver sources (the official page that
   apprentices don't pay for training; Student Finance England's tuition fee and maintenance loan
   pages; the 16 to 19 Bursary Fund; a T Level or Level 3 course; the UCAS deadline), curated and
   reviewed like Tasks 7b and 7c with one short review session. The controller makes every fetch
   (subagents make no web requests).
9. **Childline** (for anyone under 19) in the calm support panel, checked on its own website and
   reviewed with the support policy.
10. **No:** hours that change on a date ("free from September") is a known L0 limit, recorded in
    the plan's section 1 deferrals and the section 22 row.

## The approved placement
- **Main tree:** Task 6d slice C (finishing) → **new Task 6f, "No job yet"** (decisions 2, 3, 4,
  9; the walk's rows 1, 3, 4 and 8's Childline; about 15–20 hours) → Task 6e (adds decision 5:
  the synthetic school leaver and her evaluation cases, for session W2) → session W2 → Task 10 →
  Task 12b → Task 14 → … as today.
- **Worktree track:** **new Task 12c, "A tuition fee loan is a loan to repay"** (decision 6; the
  checker, the oracle written fresh, the search's classing per ADR 0016 rule 2; about 8–12
  hours; may start beside 6f; before Task 14; not beside 12b or 14, which change
  `careerwright/planning`) → **new Task 7f, "The school-leaver option pack"** (decision 8; like
  7b and 7c; its review session is the product owner's; before Task 12b, which reads the pack).
- **Lines on existing cards** (the walk's section 2):
  - Task 6e: the synthetic school leaver and 4–6 evaluation cases; she is a session W2 persona.
  - Task 10: qualifications as entry facts (expected never met); no empty "usual in your role"
    panel without a role.
  - Task 12b: checkpoint words for someone not working ("staying in education"; "not working:
    0 hours, £0"); the entry confirmation reads qualifications ("if you get your grades"); each
    scheme's age rule shown beside it.
  - Task 14: decision 7's words for a route longer than the model.
  - Task M: the walk's row 5 (the strength's horizon and the first answer's ignition without a
    job).
  - Task 7e: the research purpose names apprenticeships, degrees and their funding.
  - Task 8: apprenticeship listings marked as such; a pasted apprenticeship advert.
  - Task 16: the privacy note on young people's data (decision 1).
- Update the order section, "Current position and next tasks" (what's complete since plan v1.5:
  Tasks 3b, 6d slices A–C, 12a, 13a, 13b, and W2E per the ledger; what runs next), and the plan's
  section 6 "Order from here" with a short v1.6 note (dated 2026-11-01, the product owner's
  school-leaver decisions). `make-brief.sh` must extract each new card (`## Task 6f:`,
  `## Task 12c:`, `## Task 7f:` exactly).
- **Register:** add rows for the new behaviour, each owned by its new task (follow how plan v1.5
  added rows), and mark FUNDING-04's row with decision 6's L0 change. Don't touch other rows.

Also fix two stale paths in `docs/plan/l0-sprint-tasks.md` (lines naming
`/Users/darianraad/Code/careerpathoptimizer`): the root folder is being renamed to
`/Users/darianraad/Code/careerwright` and the worktree folder to
`/Users/darianraad/Code/careerwright-wt/<id>`. Leave past reviews and evidence as they are.

## Rules
- Documents only: the specification's section 22, `docs/plan/development-plan.md`,
  `docs/plan/l0-sprint-tasks.md`, `docs/requirements-register.md`. No code, no `CLAUDE.md` (its
  changes need the product owner's explicit approval: if one is needed, propose exact wording in
  your report instead).
- Edit/Write for every change; no scripts that rewrite files.
- Plain words where the product owner reads them; no internal codes in Deliver lines beyond the
  requirement IDs the cards already use.
- Stage explicit paths; never stage `answers-2.md` or `esco_research.txt`. Never push. No
  subagents, no web requests, no live calls, no Docker. Never read `.env`, `~/.careerwright` or
  `~/.nessa`.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Check: `make-brief.sh 6f`, `12c` and `7f` each extract one card
  (`.superpowers/sdd/l0-sprint-tasks/make-brief.sh <id>` runs from the main tree's path: run the
  same awk on your worktree's file instead, and report the line counts).

## Report
Write `.superpowers/sdd/l0-sprint-tasks/task-plan-school-leavers-report.md` (what changed, where,
and any CLAUDE.md wording you propose). Reply with at most 10 lines and your branch head SHA.
