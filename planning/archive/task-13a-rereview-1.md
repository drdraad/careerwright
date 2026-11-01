# Task 13a, fix round 1: scoped re-review

Fix range c8a9a5f..589119a on `wt-13a`. I read the fix list, the report's "Fix round 1"
section and the whole fix diff. I re-ran no suites. I ran one focused probe on 589119a in the
worktree's environment (`probe_13a_r1.py`, in this session's scratchpad); the worktree stayed
clean.

## Verdicts

**I1, a false "no route": ADDRESSED.**
- The screen now runs before the empty route's cut (`search.py:325-326`). The cut is skipped
  when everything is set aside.
- I checked every other exit. Rule 1 returns `unresolved`. Limit stops are
  `budget_truncated`. Every deeper cut comes after the screen.
- Tests: the reviewer's instance is a regression test (`test_route_search.py:524`). It is
  also an explicit example in the oracle property. The oracle now counts an option's own
  unknown as something unknown (`route_oracle.py:124`), so the property would now catch the
  defect.
- The probe agrees: `undated_relief()` gives `unresolved`.

**I2, set-aside records hold only part of the truth: PARTLY ADDRESSED. Still Important.**
- What is fixed: C09 now gives "to confirm: entry requirements, cost" and "ruled out as
  stated: prerequisite_not_usable, workload" (`test_route_search_pack.py:99`). ADR 0016's
  Task 14 note now asks for the two lists apart.
- The new break: `violations` is every breach in the option-alone check
  (`search.py:362`). That check includes the empty route itself, so every option inherits
  the person's own position.
  - In the I1 case, the undated reduced-hours option reads `violations: [workload]`. That is
    the empty route's breach in March and April, and the very breach this option would cure
    once its dates are known.
  - When the empty route already breaks the reserve in January, a dated course with an
    unknown cost reads `violations: [reserve]`. An undated course reads `[]`, because the
    checker skips the reserve when dates are unknown.
- Why it matters: Task 14 would tell the person that the one option that could work is
  "already ruled out", which steers them away from it. This is the feasible-or-not kind of
  finding.
- Fix:
  - Leave out of each option's `violations` any breach the empty route already has (same
    code and month).
  - Report the empty route's own breaches once, on the result, so Task 14 can say what the
    person's current position already breaks.
  - Test both the I1 instance and the reserve case.

**I3, the measurement's horizon: ADDRESSED.**
- Intakes are now spread across each horizon by default (`route_search_sizes.py:231`). The
  first shape is still available as `--intakes early`, and every row names its spread.
- The report and ADR 0016 replace the overstated lines. The headline for Task 13b says it
  holds for spread intakes.
- Spot-checks reproduce my probe exactly: relaxed 10 × 2 × 24 needs 12,451 states, relaxed
  12 × 1 × 24 needs 1,387, and P01 at 24 × 2 × 24 needs 2,233.
- The whole-pack size now takes 25.6 s over 24 months, near the 30 s limit, and the headline
  says so.
- At 6 months no spread instance can reach the milestone, so those rows size a tree with
  nothing to find. Both documents say this.
- Two tests moved from 6 to 24 months. This is disclosed and justified.

## The extra change: an option with unknown weekly hours is set aside even when its months already look over the limit (`search.py:466-472`)
- **It is sound.** In every month such an option is active, every route containing it
  either breaks the workload or has unknown hours, so no feasible schedule is lost. The
  oracle mirrors it (`route_oracle.py:137`).
- **It was not needed.** Unknown hours can only add load. When the known load is already
  over, the breach is certain, which is the same rule the checker applies to the known part
  of a cost. Wherever a relief option exists, the old code already gave `unresolved`.
- **Its one visible effect is to turn a provable "no route" into `unresolved`.** In the new
  test's case (`test_route_search.py:509`), the job and care take 38 of 36 hours, nothing can
  lower them, and the course's hours appear as "to confirm" although they cannot change the
  answer.
- **Grade: Minor.** It errs on the safe side. It can stay, but only once I2's fix reports the
  empty route's breaches on the result. Otherwise this record would read "to confirm: weekly
  hours" with nothing else, for an option nothing can rescue.

## New breakage
- Important: the I2 inheritance described above. It is the only new defect.
- I found nothing else in the fix diff. `_codes`, the new `SetAside` fields, the oracle's
  stronger `something_unknown`, the spread intakes and the two corrected documents are
  consistent with the code.

## Out of scope
- The checker still treats an option with no dates and a work pattern as absent in every
  month. That is Task 11's code, as the first review noted.

Counts: Critical 0, Important 1 (I2, partly addressed), Minor 1 (the extra change).
**Task quality:** Needs fixes (one).
