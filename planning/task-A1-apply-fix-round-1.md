# Task A1 apply, fix round 1 of 5 (documents only)

You fix the documents change fde8e7d..ec4d060 (Careerwright L0, branch `l0-local-release`,
main tree `/Users/darianraad/Code/careerpathoptimizer`). You are a fresh implementer. The
original instructions are `task-A1-apply-dispatch.md`, the report is `task-A1-apply-report.md`,
and the review is `task-A1-apply-review.md`, all in `.superpowers/sdd/l0-sprint-tasks/`. Read
the review in full, then the dispatch's rules: they still bind you (documents only, the
listed files, pathspec commits, never `answers-2.md` or `esco_research.txt`).

Another implementer works in this same tree on product code (Task W2E). It changes
`docs/requirements-register.md` and `docs/plan/*` only in its last commit. Before you edit
either, check `git status --short`: if either shows uncommitted changes that aren't yours,
stop and report NEEDS_CONTEXT instead of committing over them.

## Fix now (the controller's rulings)
Minor findings in documents that later briefs are cut from are fixed now: a card defect
becomes wrong code.

1. **Important 1, the parallel lines.** Task 12a never overlaps 13a or 13b: it changes the
   planning rules that 13a's oracle and 13b's solver read.
   - The order becomes 13a, then 12a, then 13b, all in the worktree track, each after the
     last is integrated.
   - 12a may overlap the main-tree interface tasks (W2E, 6d, 3b, 6e), in a worktree, under
     R15's rebase rules (it adds API, migrations and the generated client).
   - Make every Parallel line, the dependency rules and the suggested order agree.
2. **Important 2, facts and not sentences.** Add to R11 (or R14):
   - New or changed API responses carry codes and numbers, never sentences the person reads.
   - The web words them from `src/lib/vocabulary.ts`, with exhaustive maps, so a new code
     fails the type check.
   - Give Task 6d a first slice, ahead of its role-space work: discovery's search notes and
     title-idea lines become structured facts (found work, found none, not searched, and the
     reason code), worded in the web. Tests check the facts; one test per fixed sentence
     checks its words. The role space's new notes (UK title list, own words, "None of these is
     my job") are born as facts.
   - Cite appendix B F3 and F7.
3. **Minor 1.** Take "language and region disparities in discovery's evaluation" out of the
   specification's 2026-10-31 approval record. Keep it in the plan and the register as the
   plan's own note ("L0 has one language and one region"), owned by Task 16.
4. **Minor 2.** In that subsection, say plainly that L0 widens DIV-1's corroboration clause
   as the product owner approved. A title counts on two independent permitted sources, or
   one official source, not only an authoritative or employer source. Remove "no requirement
   is relaxed" where it would contradict that. Every other invariant still holds.
5. **Minor 3.** The plan's total: "the rows sum to about 89–168 agent hours (the report
   quoted 80–150)".
6. **Minor 4.** Add the missing acceptance lines to Tasks 10, 8 and 14, with their
   equivalents in 12b and 7e, as the review lists them.
7. **Minor 5.**
   - Name every reassigned register row on its owner's card.
   - Add a Register line to Tasks 13b and 16.
   - Add PROF-07 and TEST1-15 to 6d's line.
   - Name API-02 on 13b, 14 and 16.
8. **Minor 6.** "ONS group" becomes "its ISCO-08 group, as the ONS index codes it" wherever
   the ESCO candidates are meant. Pay stays the SOC unit group, so say that where pay is
   meant.
9. **Minor 7.** In H-08, the product owner's own details in their own live sessions are
   their choice (decision 5). The privacy check stands before anyone else's data.
10. **Minor 8.** Remove or correct the stale "one implementer at a time" line
    (`development-plan.md:365`).
11. **Minor 9.** ADR 0014's status: "Accepted 2026-10-30; amended 2026-10-31".
12. **Minor 10.** R13 says how it meets `CLAUDE.md`'s "a bland screen fails review":
    - During path tasks, a chapter built to Sprint W's design references, its words, states
      and choices exact, meets that bar.
    - Its moment, judged at Task M and at release, completes it.
    - Don't edit `CLAUDE.md`.
13. **The controller's ruling on the revision history of answers.** It is an M0 promise
    (spec section 3, "revision history always available") with its API already built. Assign
    its small view to Task 15B (revise and replan), and remove it from the L0 deferrals.

14. **A finding from Task 13a's measurement.** Write it into Task 12b's and Task 14's cards
    and their register rows, and into the plan's Sprint 5 and 7 cards.
    - The finding: in the reviewed option pack 0.2.0, every offering lacks at least one fact
      the route search needs (a start date, a cost, weekly hours or an entry confirmation).
      So today every reviewed target's search says "unresolved", never a route (report
      `.superpowers/sdd/l0-sprint-tasks/task-13a-report.md`, "The answer for Task 13b").
    - Task 12b's checkpoint shows, for each option, which fact is missing, in plain words.
      The person can supply it as their own figure, labelled as theirs and not reviewed, or
      choose a stated intake. Entry confirmations come from Skills where they are readiness
      facts.
    - The search then runs on what they supplied.
    - Acceptance (12b and 14): P01, with the missing facts supplied at the checkpoint, gets
      computed routes in Routes, each qualified where it rests on a figure the person
      supplied. Without them, Routes names what is missing, never "no route".

## Checks
- `bash .superpowers/sdd/l0-sprint-tasks/make-brief.sh <id>` succeeds for every card you
  touched. Delete the brief files it writes, **except** `task-13a-brief.md` and
  `task-W2E-brief.md`, which are in use: never overwrite or delete those two.
- Every `## Task` heading is unique.
- `make check` passes.

## Report
Append a "Fix round 1" section to `task-A1-apply-report.md`: each item with what changed
(`file:line`), and the checks with their output. Reply with only the short contract.
