# Task 5 re-review 2 (38c2fce..8a817f6), scoped

Read the diff in full for the backend, migration and queries.ts; generated client and tests read selectively. Ran `tests/domain/test_interview_agent.py`: 14 passed. Integration tests not re-run (Docker out of scope); judged from code.

## Verdicts
- **N1 Fixed.** `identity/activity.py` `PartialWriter.__call__` writes on first piece, on any later event once the interval has elapsed, and always when `complete=True`. `interview_agent.py` `_reply_so_far`/`ReplyStream.on_event` detect the close with a strict partial parse (`reply` present only once its string closes), so the flush does not wait for another event beyond the one that closes the string. Stall case: a stall inside the window mid-reply leaves the store at the last written piece until the next event, or until settlement writes `latest` via `end_partial` on failure. That is the stalled provider's own state, not lost data; no timer exists (Minor, below). The integration test (`pause_after_reply`) exercises the post-close pause.
- **N2 Fixed.** `activity.py:368-377` `_measured` drops `state == "interrupted"`. `_spend` (`:458`) is `UNKNOWN` when `usage is None` or `responses < requests_sent`, so a mix of a good and an interrupted request is also unknown. No path books partial usage as reconciled. Test asserts `("unknown", None)` x3 and reserved 3.5M.
- **M1 Fixed.** `db.py` `in_savepoint` uses `begin_nested`; a DBAPI refusal (RLS WITH CHECK is ProgrammingError) rolls back to the savepoint only; Operational/Interface errors propagate (connection lost). `_settle` still calls `finish_attempt` in the same transaction, so settlement commits with the run's state. `publish` uses the same helper. Test covers revoked-mid-call.
- **M2 Fixed.** Fake reply starts with the sentinel; the cut-stream test asserts the sentinel is in the partial, leak scan is clean sealed, and positive when unsealed.
- **M3 Fixed.** `PartialCompleteness.STOPPED` (`records.py`), `mark_partial_stopped`, `partial_reply` maps to `incomplete` only when the run has failed (`runs.py`). `stopped` is in `openapi.json:3665`, `types.gen.ts:775` and the schema description. No UI vocabulary maps completeness yet: nothing in `apps/web/src` outside `generated/` consumes it (the view is T6), so there is nothing to map.
- **M4 Fixed.** `queries.ts` routes `run.partial_updated` only to `keys.turnReply(id, subject_id)`; the subject is the run (turn) id.
- **M5 Fixed.** `runs.py` `partial_reply` checks `accepted_output` last when the partial is missing. The race test uses `crash_at="after_settle"` on a succeeding worker, which gives output committed and run still `running`, and asserts `superseded`. This is the real gap, not a simulation.
- **M6 / r0009 Fixed with one caveat.** The migration moves `run_limit = 100000000 AND version = 1`. `update_spend_limits` always bumps `version`, so version 1 means no PUT edit on an existing row. Caveat: `set_spend_limits` with no row (`stored is None`, only before any key is stored) inserts at version 1 via `ensure_spend_limits`, so a person who first chose exactly $0.10 before storing a key would be raised to $0.15 (Minor). The data move `incomplete`→`stopped` happens before the new CHECK is added, and the constraint name matches the r0007 inline check (`run_partials_completeness_check`; applied in the migration tests per the report). Safe on existing rows. The `incomplete`→`stopped` rename itself has no upgrade test (report discloses it; the table is new in this branch). ADR decision 9 records the residual cases.
- **M7 Fixed.** ADR status line and decisions 4 and 5 carry the provisional/R6 label.
- **M9 Fixed** (`bounds.ts`; hints read the bound). Not examined in depth.

## New issues
### Critical
None.
### Important
None.
### Minor
- `activity.py` `PartialWriter`: no timer, so a mid-reply stall inside the throttle window leaves the stored text stale until the next event. Acceptable; note for T6 polling.
- `interview_agent.py` `_reply_so_far`: two `from_json` parses per text event (quadratic in output length). Fine at current output sizes.
- r0009: a limit deliberately set to exactly $0.10 before any key was stored is indistinguishable from an untouched default (version 1) and is raised to $0.15. Mention in ADR 0006 decision 9 if desired.
- No upgrade test for the r0009 `incomplete`→`stopped` row move.

## Assessment
**Task quality:** Approved
**Reasoning:** All targeted findings are fixed with tests that exercise the real gaps; no new Critical or Important issues found in the diff.
