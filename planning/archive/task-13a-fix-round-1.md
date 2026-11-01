# Task 13a, fix round 1 of 5

The review is `.superpowers/sdd/l0-sprint-tasks/task-13a-review.md`. Read its three Important
findings in full. Fix them in your worktree (`/Users/darianraad/Code/careerpathoptimizer-wt/13a`,
branch `wt-13a`). Each fix gets a test that fails on today's code: show RED, then GREEN.

1. **Important 1: a false "no route".** When the empty route already breaks the workload
   limit, the search cuts it before recording which options it set aside. A complete run can
   then say `no_route_in_bounded_model` when the only option that lowers the hours just lacks
   its dates.
   - Run the set-aside screen before the empty route's cut (`search.py:317-321`), so any
     set-aside option makes the result `unresolved`.
   - Add the reviewer's probe as a regression test, in both the search's tests and the
     oracle's.
   - Check every other early return the same way. No exit may reach
     `no_route_in_bounded_model` while an option was set aside for an unknown.
2. **Important 2: an option set aside keeps only part of the truth.** It keeps only the codes
   that set it aside, and drops its other breaches. C09 shows "entry requirements, cost", but
   its admission gate and its workload also fail. ADR 0016 tells Task 14 to show these codes
   as "what to confirm", so the person would be told the wrong things to check.
   - Keep every finding the option has (the unknowns that set it aside, and the rules it
     already breaks), each marked as one or the other.
   - Correct ADR 0016 so Task 14 shows "what to confirm" (the unknowns) apart from "what
     already rules it out as stated" (the breaches).
   - Test it on C09.
3. **Important 3: the measurement's horizon.** The measurement puts every intake in months 1
   to 9, whatever the horizon. So the 12- and 24-month rows measure only the cost of a check.
   - Re-run with intakes spread across each horizon. Report both runs in your report's
     measurement section, replacing the overstated lines, and in ADR 0016 if it quotes them.
   - The headline for Task 13b must say which intake spread it holds for.

Minors wait for the final review (R13); the controller has ledgered them. Don't fix them,
except where a fix above touches the same lines anyway.

The reviewer's notes for Task 12a are carried by the controller; they are not yours: C07's
£0 fee depends on eligibility conditions nothing checks, C09 needs an application action or
a recorded admission, and two conditional job transitions are possible.

## When done
- Run the covering tests, then `make check`.
- Rebase onto the current `l0-local-release` (it has moved: Task W2E's code and the
  documents' fix round). Run `make check` again.
- Append a "Fix round 1" section to `task-13a-report.md`: each finding, its tests, the
  command and output, the RED and GREEN evidence, and the new measurements.
- Reply with the short contract and your new branch head SHA.
