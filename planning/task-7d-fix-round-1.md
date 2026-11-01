# Task 7d — fix round 1 (FIX_BASE 37b2eeb)

The review (`task-7d-review.md`) is Spec ✅, Approved, with 3 Minors. Read it in full. These
are the controller's rulings.

1. **Minor 1: the 202-for-409 race. Ruling:** keep the published contract, taking the
   reviewer's first option.
   - After `visible_workspace(tx, workspace_id, lock=True)`, re-read the asked runs. If the
     run and every started run have settled, raise `RUN_FINISHED`; the transaction rolls
     back its requests and writes no receipt.
   - Otherwise, name and write events only for the runs that are still unsettled.
   - Test the race deterministically with two connections: hold a run's row `FOR UPDATE`
     as the worker's terminal publish does, start the cancel, commit the terminal state, and
     assert 409 `RUN_FINISHED` with no request or receipt left.
   - Contract preservation outranks the smaller diff here: the route, the field and decision
     15 all publish this behaviour.
2. **Minor 2: correct ADR 0009's wording to exactly what holds**, using the reviewer's
   wording for (a), (b) and (c). Add (d), one clause saying that a DELETE of a run's row
   takes the same lock, so T15's workspace deletion keeps the order.
3. **Minor 3: parked for the final review** (R12, a hardening with no failing check). Do not
   do it.

Also put the reviewer's corrected CLAUDE.md lock-order sentence in your report as the
proposal, replacing yours. Do not edit CLAUDE.md.

The same rules apply as before:
- Edit and Write only.
- Never read `.env` or NESSA_HOME.
- No live calls. Never push. No subagents.
- Run `make check`, then `make acceptance` once.
- Append your report under "Fix round 1" in `task-7d-report.md`, then reply with the short
  contract.
