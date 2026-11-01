# Task 7 slice 7B — fix round 2 (FIX_BASE 044ef12)

Both re-reviews found every item of round 1 fixed:
- `task-7-sliceB-rereview-1-A.md`: 9 of 9, a new Important N1 (pre-existing) and Minor N2;
- `task-7-sliceB-rereview-1-B.md`: 9 of 9, new Minors 1 and 2.

Read N1 in 1-A and Minor 1 in 1-B in full. These are the controller's rulings.

1. **1-A N1.** The pinned 2026 provisional Table 15 (4) publishes no percentile at region ×
   four-digit unit group, so the occupation floor rule (P90 in every region) answers
   `not_published` for every occupation. That stays true even after H-10 reviews a mapping.
   **Ruling: record the fact; do not change the rule.** The choice of statistic or geography
   goes to the product owner as an R6 decision, which the controller will put to them.
   - In ADR 0010 decisions 4 and 8, the DIV1-07 row and the R6 list, state it plainly:
     - no percentile is published at region × unit group in this release;
     - Table 15 (3), the three-digit minor groups, does publish percentiles;
     - so in L0 the floor can never remove a suggestion, with or without a reviewed
       mapping.
   - Correct the ruling text that says "often not published": it is always unpublished.
   - Pin the fact in the full-release test: the count of published percentiles in Table 15
     (4) is 0, so a new release that publishes them is noticed, never assumed.
   - Make the synthetic sample's four-digit percentiles withheld (`x`), as in the real file.
     Keep a published P90 only as one labelled synthetic exception, used by the mechanism
     test, with a comment saying the real release never has it. Fix the sample's docstring.
2. **1-B Minor 1.** ADR 0010's line 7 becomes "amended decisions 4, 7, 8, 9 and 10".

Parked for the final review (R12, no reproduced defect): 1-A N2 (a CHECK on the `cvs`
column) and 1-B Minor 2 (an upgrade test for 0028 from a populated 0027).

## Also

- No behaviour change beyond the test data. Say if any expectation changes, and why.
- Run `make check`. Run `make acceptance` only if you touch anything beyond docs, the test
  sample or the full-release test, and say which.
- The same rules apply: Edit and Write only, never read `.env` or NESSA_HOME, no live calls,
  never push, no subagents, never edit CLAUDE.md.
- Append your report under "Fix round 2" in `task-7-sliceB-report.md`. Then reply with the
  short contract.
