# Task 13a, fix round 2: scoped re-review

Fix range 589119a..8ff5100 on `wt-13a` (3e564f5, 8ff5100). I read the report's "Fix round 2"
section and the 316-line diff, and read the code on the branch. I ran no suites and no
probes: the two new tests are my two probe cases.

## Verdicts

**I2 (the rest of it): ADDRESSED.**
- **An option is no longer blamed for the person's own position.** Its "rules it out" list
  now leaves out any breach the empty route already has in the same month, matched by code
  and month (`search.py:454-465`, used at `369`).
- **The person's own breaches are told once, on the result,** as `starting_violations`
  (`search.py:240`, `325`, `600`).
- **The outcome is unchanged.** `codes`, `kind` and `_outcome` are untouched
  (`search.py:615`).
- **Both probe cases are now tests:**
  - the undated reduced-hours option now has an empty `violations` list, and the result
    reports the workload breach in March and April once (`test_route_search.py:541`);
  - the course with an unknown cost no longer picks up the reserve the person was already
    short of in January (`test_route_search.py:559`).
- **C09's record is unchanged:** P01's figures break nothing at the start, so its two
  breaches stay.
- **ADR 0016 is updated:** decision 4 (line 68) and the Task 14 note (line 180).
- **The register's OPT1-07 row** names the two new tests.

**The Minor on the extra unknown-hours change: ADDRESSED.**
- I said the change could stay once the empty route's breaches appear on the result. They
  now do.
- In the 38-of-36-hours case, the option reads "to confirm: weekly hours" with nothing ruled
  out against it. Beside it, the result says the person's own hours are already over in every
  month (`test_route_search.py:522`).

## New breakage
None.
- `starting_violations` is filled before rule 1's early return, so it is reported in every
  path.
- The empty route has no breach without a month, so matching on code and month cannot hide
  one of the option's own breaches that has no month, such as a direct-spend cap.
- `SearchResult` is not stored or served yet, so the new required field breaks no contract.

One note, not a finding: an option that makes an existing breach worse in the same month (for
example a fee in a January already below the reserve) is not blamed for it. That is the
intended reading, and the next search after the person changes their inputs would show it.

Counts: Critical 0, Important 0, Minor 0 open in this scope.
**Task quality:** Approved (for the scoped findings).
