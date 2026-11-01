# Review: Task A1, apply (fde8e7d..ec4d060)

Read-only review. Inputs: the reviewer contract; the audit report (all of it) and the
decisions page; the implementer's dispatch and report; the 3,744-line diff, read in passes
(CLAUDE.md and the specification, then the ADRs, the plan, the task file and the register);
appendices A §3 and §5, B F5 to F10, D §3 and §4, E §2, F §5 and §6, and G. Focused checks
outside the diff: ADR 0003's bytes after the heredoc; the register's cell counts; every
card's Preconditions and Parallel lines; the session 2 record against H-13 and H-01; the
code names the ADRs cite (`occupation_choice`, the manifest classes); ledger rows 32 and 33;
the spec's freshness table and DIV-1 text. `make check` and `make-brief.sh` were not re-run
(the dispatch says so for the first; the second writes files).

### Spec Compliance
- ❌ Issues found:
  - The Parallel lines of Tasks 12a, 13a and 13b contradict each other and the suggested
    order (`docs/plan/l0-sprint-tasks.md:1398-1399`, `:1510-1511`, `:1539-1540`, `:324`,
    `:384`). Important 1.
  - The report's remedy for the costliest review loop (the backend returns facts and the
    web words them from a small fixed set; appendix B F7, "keep every new chapter's API
    prose-free") is on no card and in no ruling, though the implementer's dispatch named
    it. Important 2.
  - The specification's 2026-10-31 record lists one deferral the product owner never saw
    (`Careerwright_Product_Specification.md:1303`). Minor 1.
- ✅ What matches:
  - `CLAUDE.md`: the four edits are word for word the report's section 7, in the right
    places, and nothing else changed (+17 −2).
  - Order and dependencies match the report's table: W2E, 6d, 3b and 6e come before a short
    session W2; 12a and 13b fill the wait, and 13a already runs; "add an option yourself" is
    in 12b; 7e waits for Plan (15) and 12b; Roles (8) waits for the end-to-end session; M
    waits for the end-to-end session and 8, and 16 waits for M. Every Preconditions line
    agrees with dependency rules 7 to 18. There is no circular wait.
  - Every new or revised card has a Preconditions and a Parallel line. W2E holds E's F1,
    F2, F5, F7, F8, F10's words, F14 and F17, the report's step 1 items, and a slot for the
    re-review's findings. 6d holds F's first step, its five-part acceptance test word for
    word, the target stored once (B F5), seniority and industry, the research's three
    fixes and CV paste if small. 3b has the controller making every live call, the caps
    ($0.75 a run, $5 a session), the cost-log copy without content, the spending line and
    the cost estimate before research (the report's drift 4). 12b holds "add an option
    yourself". 7e holds option research. Routes built on records that aren't reviewed are
    qualified in 12b, 7e, 14, ADRs 0011 and 0013, plan S3.7, S5.7 and section 9, and the
    spec record.
  - R4, R10, R11, R13, R14 and R15 match the report's section 6 point by point. The
    product owner's approval and parallel-work words are quoted verbatim, as are their four
    directions. All of these were checked across every added line.
  - ADRs 0003 and 0006 to 0014 and the new ADR 0015 follow the report and appendices F and
    G. I found no invented decision. Each open point names the task that settles it.
    ADR 0003 reads cleanly after the heredoc: one final newline, no carriage returns, no
    stray bytes.
  - Register: all 28 orphaned rows are reassigned or deferred. VIS1-02, AIR1-08 and UI-02
    now say glyph and label. H-13 matches `docs/reviews/session-2-answers.md` part 1 word
    for word, marks included. DIV1-04 is corrected. The sessions table, H-01 and H-05 are
    updated, and the 16 new rows each have an owner.
  - The specification has one new dated subsection in section 22, and no other line
    changed.
  - Honesty: no human gate is claimed passed. Sessions W2 and the end-to-end session read
    "not run — requires human". Only sessions 1, 2 and W1 are called held, which is true.
- ⚠️ Cannot verify from diff:
  - Brief extraction per card (`make-brief.sh`), not re-run.
  - `make check` on ec4d060, not re-run, as the dispatch says.
  - The W2C part 1 re-review's findings: W2E only leaves room for them.

**The implementer's rulings (check 9).** None contradicts the report or the
specification:
- **Pay lanes kept.** The report's ruling removes the pay and AI *filters*, and listings'
  own pay is VIS1-06.
- **Revision history deferred.** Appendix A §3 item 10 recommends this.
- **Export in 15A.** Appendix A §4 allows it.
- **The product owner's commands and the shutdown hang in 3b.** The report gives them no
  owner.
- **13b's durable parts stay M0 unless the product owner says yes and the spec gets a
  note.** This is the conservative reading of "sized from the measurements", because
  OPT-1 and ARC-1 are M0.
- **TEST1-13's course and funding scoring moved to 7e.** Appendix A row 111: only 7e
  builds that extractor.
- **The 80–150 total.** The plan quotes it as "its own range, not the sum of the rows".
  That is true, but it leaves out that the rows add up to more. See Minor 3.

### Strengths
- Following the report where appendix D differs is done carefully and disclosed. Examples:
  the end-to-end session after Task 15, not 15A; Roles after it; the demo route preview
  taken out of the path rather than reworded.
- Undecided points are never filled in. Each says "to be settled by Task <id>", and the
  report's table of them matches the documents.
- ADR 0015 is a faithful, compact record of appendix F: the four layers, the corroboration
  rule with "official" tied to real manifest classes, the role record, the spend bounds,
  and what later chapters show.
- The 12a card turns carry-forward items 1 to 7 into observable acceptance, adds work rights
  and remote working, and keeps "unknown work rights are never ineligible".
- The 13b ruling protects the specification's M0 requirements without blocking the report's
  sizing ruling.

### Issues

#### Critical
None.

#### Important
1. **The Parallel lines contradict each other, so two implementers could change the same
   planning rules at once.**
   - Where: `docs/plan/l0-sprint-tasks.md:1398-1399` (12a), `:1510-1511` (13a),
     `:1539-1540` (13b), `:1452-1453` (12b), `:324` and `:384` (suggested order), and
     `docs/plan/development-plan.md:346-347`.
   - What:
     - Task 12a's line says it "may overlap Task 3b, 6e, 10, 13a or 13b".
     - Task 13a's line allows only tasks "outside `careerwright/planning` and the optimiser",
       and its list leaves out 12a.
     - Task 13b's line says "Not 12a (planning)". It also lists 12b as allowed, but 12b
       changes the planning catalogue (its own line, `:1452-1453`), which 13b's rule
       excludes.
     - The suggested order says "session W2, with 12a and 13b meanwhile". Under R15's cap
       of two implementers, that reads as running them together.
   - Why it matters:
     - 12a changes the checker's and ledgers' rules in `careerwright/planning`: stacked
       supports unresolved, the repayments finding, the entry-requirement finding, null
       month rows.
     - 13a's independent oracle and 13b's solver must agree with those rules.
     - Running them side by side is the conflict the product owner asked us to avoid
       ("coordinate well to avoid them causing conflicts"). R15 says the Parallel line
       decides, and these lines cannot all be followed.
   - Fix: decide whether 12a may overlap 13a and 13b. Then make all three lines and the
     order sentence agree. For example: 12a says "Not 13a or 13b (planning)", and the order
     reads "session W2, with 12a then 13b meanwhile". Then check 13b ∥ 12b against 13b's own
     rule.
2. **The report's fix for wording loops is approved but owned by no task.**
   - Where: R11 (`docs/plan/l0-sprint-tasks.md:198-218`) and Global Constraint 10 (`:58`).
     The new chapter cards (6d, 10, 12b, 14 and 15) say nothing about it.
   - What:
     - The report's section 2 says, about the slate's notes: "the backend returns facts
       (found work, found none, not searched, and why). The web shows them from a small
       fixed set of plain sentences. Tests check the facts, not the words."
     - Appendix B F7 adds: "Keep every new chapter's API prose-free: codes and numbers out,
       words in `vocabulary.ts`, with exhaustive `Record<Enum, …>` maps."
     - The implementer's dispatch listed "prose-free APIs (F7)". The implementer's report
       doesn't mention it, and it appears nowhere in the change. R11 freezes the notes and
       adds the sentence rule, but says nothing about where words live or what tests check.
   - Why it matters:
     - This is the loop the audit found most costly: about 3,750 lines and five rounds on
       note wording.
     - 6d rewrites the slate's title lines next, and 10, 12b, 14 and 15 each add a chapter's
       words. Without the rule they can compose English in the backend again.
     - It is the audit's own drift pattern: approved, and owned by no task.
   - Fix:
     - Add one bullet to R11 or Global Constraint 10: new chapter APIs return codes and
       numbers, never sentences. Words live in `vocabulary.ts` with exhaustive maps, and
       tests check the facts.
     - Either give the conversion of the slate's notes to 6d, which already changes those
       lines, or put it on the final-review list by name.

#### Minor
1. **A deferral is recorded as the product owner's decision, but they never saw it.**
   - Where: `Careerwright_Product_Specification.md:1303`, also `docs/plan/development-plan.md:80`
     and `docs/requirements-register.md:717`.
   - What: the "approved by the product owner" table lists "language and region disparities
     in discovery's evaluation" as an L0 deferral. Neither the report nor any appendix
     proposes it. It is the implementer's reading of DIV1-08 and is not listed among its
     rulings.
   - Why it matters: the specification is the top authority, and section 22 records the
     product owner's decisions.
   - Fix: take it out of the section 22 row. Keep it in the plan and the register as the
     plan's note ("L0 has one language and one region"), or ask the product owner one line.
2. **"No requirement is relaxed" sits beside a wider corroboration rule.**
   - Where: `Careerwright_Product_Specification.md:1296, 1300`.
   - What: the subsection says no requirement is relaxed. But its corroboration rule
     accepts any two independent *permitted* sources, which is wider than DIV-1's
     "authoritative … source or independent employer evidence". For example, two
     training-provider pages would count.
   - This is faithful to the report and to the approved `CLAUDE.md` wording, so it is not
     the implementer's error.
   - Fix: say plainly that L0 widens DIV-1's employer-evidence clause, as the product owner
     approved. Or narrow 6e to employer and official pages, with their yes.
3. **The plan's total hides that the rows add up to more.**
   - Where: `docs/plan/development-plan.md:23` and `:358`.
   - What: the rows add up to about 87–160 agent hours, or 89–168 with 13b's add-ons. The
     plan quotes the report's 80–150 as "its own range, not the sum of the rows" but doesn't
     say which way the difference goes.
   - Fix: add "the rows sum to about 89–168".
4. **Three revised cards have no acceptance for their new work.**
   - Where: Tasks 10 (`:1310-1358`), 8 (`:1218-1281`) and 14 (`:1568-1620`).
   - What is missing:
     - Task 10: a target outside the pack, or with "None of these is my job", shows "not
       assessed yet" and never a readiness result; "not part of my job" is never evidence.
     - Task 8: the plain line replaces the filters; the role card's outlook reads "not
       enough evidence yet"; ONS-group pay is labelled as the group's.
     - Task 14: a route on a proposed option reads qualified on screen.
   - 12b and 7e have equivalent lines.
5. **Some reassigned register rows are not named on their task's card.**
   - API-02 is now owned by T13b, T14 and T16, and none of those cards names it.
   - PLN-09, REC1-09 and MODEL-03 name T16, but the Task 16 card has no Register line.
   - PROF-07 and TEST1-15 name T6d, but 6d's Register line (`:841`) leaves them out.
   - Task 13b has no Register line at all.
6. **"ONS group" is ambiguous.**
   - Where: `docs/plan/l0-sprint-tasks.md:789`, ADR 0007 `:947`, plan `:455`, register
     DIV1-14 (`:156`).
   - What: these say "the ESCO occupations in that title's ONS group". Appendix F's design
     says the ISCO group (`F-role-space.md:191-192, 197-198`). "ONS group" reads as the SOC
     unit group, which has no ESCO link in L0.
   - Fix: say "its ISCO-08 group, as the ONS index codes it".
7. **H-08 doesn't match R10 and Task 3b.**
   - Where: `docs/requirements-register.md:673`, against `docs/plan/l0-sprint-tasks.md:195`
     and `:600`.
   - What: H-08 still says "before any real person's data". R10 and 3b say "before anyone
     else's data", with the product owner's own details their choice (decision 5).
   - Fix: add that note to H-08, so a controller doesn't read session W2 as blocked.
8. **A stale line about one implementer.**
   - Where: `docs/plan/development-plan.md:365`.
   - What: "With one implementer at a time, slices … run one after the other" still stands,
     a few lines below v1.5's "up to two implementers".
9. **ADR 0014's acceptance date is credited to the wrong approval.**
   - Where: `docs/adr/0014-the-living-world.md:3-6`.
   - What: the status credits acceptance to the audit. The product owner approved plan
     v1.4, and with it this ADR, on 2026-10-30 ("commit", progress ledger line 575).
   - Fix: "Accepted 2026-10-30; amended 2026-10-31".
10. **Two rules on bland screens can disagree.**
    - Where: `CLAUDE.md:53` and `docs/plan/l0-sprint-tasks.md:226`.
    - What: `CLAUDE.md` still says "A bland, form-like or corporate screen fails review even
      if it works". R13 says that judgement happens only at Task M and at release. The new
      "Practical first" paragraph partly settles it, but a reviewer of a path task may apply
      both.
    - Fix: only the product owner can change `CLAUDE.md`, so either put one line to them, or
      have R13 say how the two meet.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The change is faithful to the approved audit on every point the dispatch
names: `CLAUDE.md`, the order, the cards' scope, the rulings, the ADRs, the register and
honesty. Two fixes are needed before implementers rely on it. The Parallel lines for 12a,
13a and 13b contradict each other and the order, on shared planning rules. And the
backend-returns-facts rule, which the report approved, has no owner.
