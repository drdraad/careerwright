# Task 9 — fix round 3 (FIX_BASE b8bd1fc)

Re-review 2 (`task-9-rereview-2.md`) found 9 of 9 fixed and two new Minors. Fix both now:
Task 11 builds on the readiness contract next, and R2-2 is reachable in 0.1.0 through the
demonstration case.

1. **R2-1: a known shortfall keeps `not_ready`.**
   - Where any mandatory row is `below_required` or `not_held`, the state is `not_ready`,
     with the coverage gap carried as a blocker.
   - `insufficient_coverage` applies only when no known shortfall exists.
   - Base `show_route_chart` on the plannable gaps, not on the state.
   - Test: P01's data quality target with "statistics" set to essential, as in
     `probe_round2`.
2. **R2-2: add the qualification `open_conflict`** whenever a met mandatory row has
   `conflict: true`, including the case where a demonstration conflicts with a self-report.
   A ready result with an open conflict says so. Test both cases.

Each test fails first. Record it in ADR 0012 decision 7, the readiness states.

The same rules as before:
- Edit and Write only;
- never read `.env` or NESSA_HOME;
- no live calls, never push, no subagents, never edit CLAUDE.md;
- pack 0.1.0 untouched.

Run `make check`, then `make acceptance` once. Append under "Fix round 3" in
`task-9-report.md`. Reply with the short contract.
