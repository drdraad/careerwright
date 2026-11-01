# Re-review 1: Task A1 apply, fix round 1 (8410eff..0931cbb, documents only)

Scoped re-review. Inputs: the reviewer contract; the fix list (14 items); the original
review; the report's "Fix round 1" section, read as unverified claims; the 1,261-line
diff, read in three passes (the spec and the ADRs, then the plan, then the task file and the
register). The approved audit and its appendices B, F and A were the authority.

Focused checks outside the diff, each for a named risk:
- **Parallel lines agree:** every Parallel line, the dependency rules and both order
  sentences, read at 0931cbb. I built the overlap table by hand: every pair is symmetric.
- **Reassigned rows named on cards:** a scratchpad script compared each register row's owners
  at fde8e7d with 0931cbb, and checked each new owner's card for the row ID. None is missing.
  The cell counts match their tables, except PROF-08 and PROF-09, which were already wrong.
- **Hours sum:** I added up the plan's rows myself: 87–160, plus 2–8 for 13b's add-ons.
- **Briefs:** I ran `make-brief.sh`'s awk to stdout only, on a copy of the task file. All 14
  touched cards extract, at 509–570 lines. No brief file was written.
- **Headings:** 33 `## Task` headings, none repeated.
- **ADR 0014's date:** ledger line 575 reads "approved by the product owner ("commit",
  2026-10-30)".
- **ONS index codes:** ADR 0010:88 confirms the index codes each title to a SOC 2020 unit group
  and an ISCO-08 group.
- **DIV-1's status:** the spec's non-deferrable invariants (S:61) don't include DIV-1's
  corroboration clause.
- **Revision history:** the audit allowed "assigned, or recorded as deferred"
  (`l0-audit-2026-10-31.md:93`).
- **13a's oracle:** `backend/tests/support/route_oracle.py` in the `wt-13a` worktree has its
  own support, debt and entry rules. See new Minor 1.

`make check` was not re-run (it passed at 0931cbb, as the dispatch says).

Line references are at 0931cbb. T = `docs/plan/l0-sprint-tasks.md`, P =
`docs/plan/development-plan.md`, R = `docs/requirements-register.md`, S =
`Careerwright_Product_Specification.md`.

## Verdicts

| # | Item | Verdict | Where |
|---|---|---|---|
| 1 | Important 1: the Parallel lines | **ADDRESSED** | T:303-305 (rule 7), T:310-314 (rule 10), T:334-341 (order, two tracks), T:400-402 (next), T:784-786 (6d), T:1191-1193 (W2E), T:1356-1357 (10), T:1442-1450 (12a), T:1504-1506 (12b), T:1575-1581 (13a), T:1608-1613 (13b); P:346-347, P:362; ADR 0008:247-255 |
| 2 | Important 2: facts, not sentences | **ADDRESSED** | T:214-219 (R11, cites F3 and F7), T:799-806 (6d's first slice), T:863-865 (acceptance 6), T:844; P:456 |
| 3 | Minor 1: language and region out of the approval record | **ADDRESSED** | S:1303; P:80; R:151, R:718; T:1809-1811, T:1829-1830 |
| 4 | Minor 2: DIV-1 widened, said plainly | **ADDRESSED** | S:1296, S:1300; ADR 0006:334-336; ADR 0015:138-142; R:147 |
| 5 | Minor 3: the hours' sum | **ADDRESSED** | P:23, P:358 |
| 6 | Minor 4: acceptance lines | **ADDRESSED** | T:1313-1317 (8), T:1399-1402 (10), T:1703-1708 (14), T:1116 (7e), T:1556-1563 (12b) |
| 7 | Minor 5: register rows on their cards | **ADDRESSED** | T:872-873 (6d), T:922-923 (6e), T:1123-1124 (7e), T:1496 (12a), T:1565-1569 (12b), T:1641-1643 (13b, new), T:1710-1714 (14), T:1755 (15), T:1829-1834 (16, new) |
| 8 | Minor 6: "ONS group" | **ADDRESSED** | T:815, T:818, T:853, T:1286-1287, T:1315; P:456; ADR 0007:948; ADR 0010:235-239; R:157 |
| 9 | Minor 7: H-08 | **ADDRESSED** | R:675 |
| 10 | Minor 8: the one-implementer line | **ADDRESSED** | P:366 |
| 11 | Minor 9: ADR 0014's status | **ADDRESSED** | ADR 0014:3-7 |
| 12 | Minor 10: R13 and `CLAUDE.md`'s bland rule | **ADDRESSED** | T:233-236; `CLAUDE.md` is not in the diff |
| 13 | The revision history, to 15B | **ADDRESSED** | T:1725-1730, T:1755; P:351, P:734, P:80; S:1303; R:444; section 7's row removed |
| 14 | Task 13a's finding | **ADDRESSED** | T:1530-1538, T:1556-1563 (12b); T:1668-1675, T:1703-1708 (14); R:19-20, R:522 (OPTN-13); P:566, P:576 (Sprint 5), P:702 (Sprint 7) |

Notes on the verdicts:
1. **Parallel lines.** The track is 13a, then 12a, then 13b, each after the last is
   integrated. It reads the same way in:
   - rules 7 and 10;
   - both order sentences;
   - the plan's Waits-for cells and the new bullet;
   - ADR 0008's amendment;
   - every card's Preconditions and Parallel lines.

   The overlap table:
   - 3b: 6d, 12a, 13a, 13b.
   - 6d: 3b, 13a, 12a, 13b.
   - 6e: 12a, 13b.
   - W2E: 13a, 12a, 13b.
   - 10: 13b.
   - 12a: W2E, 6d, 3b, 6e.
   - 13a: A1, W2E, 6d, 3b.
   - 13b: W2E, 6d, 3b, 6e, 10.
   - 12b, 14, 15, 7e, 8 and M: none.

   Every pair is symmetric. Where 12a may overlap the main tree, R15's rebase rules are
   named (T:1447-1450, T:784-786, T:1191-1193). No stale "12a and 13b meanwhile" is left in
   the plan, the task file or the ADRs.
2. **Facts, not sentences.** R11 holds the three parts of the ruling:
   - codes and numbers, never sentences;
   - `vocabulary.ts` with exhaustive maps, so a new code fails the type check;
   - tests check the facts, with one test per fixed sentence.

   6d's first slice runs ahead of the role-space work. Its new notes are born as facts, and
   acceptance item 6 checks them. See new Minor 2 for one wording risk.
4. **DIV-1 widened.** "No requirement is relaxed" is gone from S:1296. ADR 0015:142 keeps "No
   invariant is relaxed", and that is true: DIV-1's corroboration clause isn't one of the
   spec's non-deferrable invariants (S:61).
5. **Hours.** Checked: the rows sum to 87–160, and 13b's add-ons bring it to 89–168.
7. **Register rows.** The script found no new owner whose card leaves out the row. API-02 is
   named on 13b, 14 and 16. PROF-07 and TEST1-15 are on 6d's line.
13. **Revision history.** It is out of every deferral list (S:1303, P:80, register section
    7). The approved audit allowed either assigning it or deferring it, so the controller's
    ruling stays within the approval.

## New breakage in the fix diff

### Critical
None.

### Important
None.

### Minor
1. **Task 12a's card names the reason for the track but not what follows from it.**
   - Where: T:1442-1446 (Preconditions), with Deliver items 4–7 at T:1471-1480.
   - What: the fix put 12a after 13a "because this task changes the planning rules that
     13a's oracle … read[s]". Nothing on the card says 12a must give the oracle the same
     rules.
   - The oracle is written apart from the checker. It holds its own support, debt and entry
     rules (`wt-13a` `backend/tests/support/route_oracle.py:193-201, 230-260, 271-292, 294-361`), and
     `CLAUDE.md` says it "shares no code with `careerwright.planning.checker`".
   - Why it matters: 12a changes four of those rules:
     - two supports on one variant stay unresolved;
     - the repayments-alone finding;
     - the entry-requirement finding;
     - null month rows.

     If the oracle isn't changed with them, one of two things happens. Its
     Hypothesis properties fail, and the quick fix is to import the checker, which breaks the
     invariant. Or the generators never build those cases, and the independent check quietly
     stops covering them. Either way the search's main safety net weakens on feasible versus
     unresolved.
   - It is a gap in the card, not wrong behaviour today, so it is Minor. The fix list's own
     rule still applies, "a card defect becomes wrong code", so fix it before 12a's brief is
     cut.
   - Fix: add one Deliver line to 12a. Task 13a's independent oracle gets each changed rule,
     written separately (no shared code). Its agreement properties then include stacked
     supports, a cap broken by repayments alone, an unmet entry requirement and an unknown
     month amount.
2. **R11's new rule has no carve-out for text that is data.**
   - Where: T:214-216, "New or changed API responses carry codes and numbers, never sentences
     the person reads". It echoes 6d at T:803-804.
   - What: taken literally, this also covers text the backend passes through but doesn't
     write:
     - quotations verified as spans (6e's found-role quotes, 7e's research);
     - the person's own words and pasted text (12b's "add an option yourself");
     - model replies in the interview;
     - the "Why this could suit you" explanation.
   - Appendix B F7 is about English the backend composes (`B-code-coherence.md:233-243`).
   - Why it matters: a reviewer of 6e, 12b or 7e could read the rule as a ban on returning
     quotes. That would start the kind of wording loop the rule exists to stop.
   - Fix: add a few words to R11, for example "sentences the backend composes; quotations,
     the person's own words and model output stay data".

## The implementer's readings (the dispatch asked for a judgement)
- **12a's Parallel line leaves out 10.** Sound. The ruling lists exactly four tasks: W2E, 6d,
  3b and 6e. 10's line agrees (T:1356-1357). The cost is a wait, not a conflict, and 10 may
  still overlap 13b.
- **12b's Parallel line is "none".** Correct. 12b's planning catalogue is in
  `careerwright/planning` (`CLAUDE.md`'s layout), and 13b's own rule excludes that module.
  The order sentence (T:341) and the plan (P:362) say the same.
- **12b's acceptance wording.** Sound: the Routes chapter doesn't exist until 14, and 14
  keeps the ruling's words. Note for 12b's brief: 13a built no API or run kind (its report,
  "What I built"). So at 12b, "computed routes from the route search" is a backend test over
  13a's in-process search, not something on screen.
- **The new register row OPTN-13.** A fair reading of "their register rows":
  - it is owned by T12b and T14;
  - both cards name it;
  - the header note lists it (R:19-20);
  - it points to OPTN-03;
  - its 5 cells match the OPTN table.
- **STATE-06's owners (T6, T12b, T14, T15).** Correct. The row's own text has given the
  changed-constraint part to T12b and T14 since ec4d060, and the revision history to T15 now
  (R:444). The owner column was the stale part.

## Out-of-scope notes
- 13a's Parallel line (T:1579-1581) says "any task outside `careerwright/planning`", then
  lists A1, W2E, 6d and 3b only. 6e meets the rule but isn't on the list, and 6e's line
  doesn't list 13a. This was already there, and it matters only if 13a runs past 6d.
- 6d's "only where its words live does" (T:805) could be read as keeping today's notes word
  for word. Plan S2.8 (P:456) and appendix B F3 say "a fixed set of plain sentences". 6d's
  brief should say which.
- Plan step 11 (P:351) gains the revision-history view, but its 6–10 hours are unchanged.
  The view is small, so this is probably fine.

## Assessment
**Task quality:** Approved.
**Reasoning:** All 14 items are addressed, and the readings the implementer flagged hold up.
No new Critical or Important issue. The two new Minors are one line each. The first, the
12a-oracle line, should go onto 12a's card before its brief is cut.
