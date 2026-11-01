# Task 3 re-review 2 (fix round 2, `12a016e..a56c206`)

Scope: N1-N7 only. Read the diff plus `usage_ledger.py`, `stack.py`, `Makefile` and
`compose.yaml` for concrete risks. No tests were run; no Docker was touched.

## Verdicts

| ID | Verdict | Evidence |
|---|---|---|
| N1 | Fixed | `tools/live_smoke.py` `smoke()` finally block: `except Exception` around `target.stop_worker()` sets `worker_stopped=False`. `ledger_workspace_calls` then reads the attempts and adds `MAX_CALLS - len(seqs)` possible calls (unknown cost). The ledger and markdown are written before `WorkerNotStoppedError` and before `smoke_stack` tears down. `StackTarget.stop_worker` now checks `stack.running()` after the unchecked `kill` fallback. The leak scan runs after the stop. Test `test_live_smoke_ledger.py` `test_a_worker_that_cannot_be_stopped_...` asserts `len(records) == MAX_CALLS >= len(made)`. |
| N2 | Fixed, except CLAUDE.md (left for the user, as ruled) | ADR 0002 decision 7 heading, `identity/failures.py` docstring. `CLAUDE.md:31-32` still says "the DBOS step is the only retry owner". |
| N3 | Fixed | `tools/stack.py` `reseal()` restarts a running api/worker and waits healthy before migrating records. `rotate_master_key` is "add version, then reseal". `localenv --rotate-master-key` is removed. The Makefile `reseal` target calls `tools.stack reseal`. Runbook and ADR 0004 decision 8 match, including the in-flight call caveat. Test `test_reseal_after_an_interrupted_rotation_...`. |
| N4 | Fixed | `localnet.client_networks(internal=False)` returns `LOOPBACK`; enabled without an internal network it raises `RuntimeError` (fail closed). `config.py` `internal_network_clients` defaults to false. `compose.yaml` sets `NESSA_API_INTERNAL_NETWORK_CLIENTS: "true"` and `--no-proxy-headers` on the api service only. ADR 0004 decision 2 matches. `local_networks` has no remaining references. |
| N5 | Fixed (docstring corrected, backfill unchanged; acceptable per round 1's "or correct the docstring") | r0003 docstring names the dropped receipt types and the second-run caveat. `test_receipts.py` has the WITH CHECK negative test (coverage only, as the report admits). |
| N6 | Fixed | `Ledger.exclusive()` (`usage_ledger.py`): non-blocking `LOCK_EX` on the jsonl handle, `LOCK_UN` in `finally`. `run_smoke` holds it across `authorise`, the stack, and the final append and markdown write. `LedgerBusyError` is raised before `smoke_stack`. Tests cover both. |
| N7 | Fixed | `getaddrinfo` wrapped in `wait_for(CONNECT_TIMEOUT_S)`, with a test. `RUN_TIMEOUT_S` now includes both store budgets (783 s). The self-referential test and `test_worker_loop.py` are deleted; the register row no longer cites the deleted file. |

## Answers to the specific doubts

- **N1 upper bound.** Honest. The workspace's run and period limits are both `worst_case`
  (`MAX_CALLS` reservations of `worst_case // MAX_CALLS`), so the product's own reservation
  caps the calls at `MAX_CALLS` in total. Padding the attempts read back up to `MAX_CALLS`
  can only over-count. `Ledger.spent` counts every row by call count and by `reserved_nano_usd`
  when the cost is null, so the cumulative per-scope cap includes these rows. The default
  scope cap is 9 calls, so one such failure uses a third of it.
- **N6 release.** Released on every exit path in-process: the `with` block plus the
  `finally` unlock, and closing the handle also drops the flock. `SIGKILL` and an untrapped
  `SIGTERM` end the process, and the OS releases the lock. The fd is non-inheritable, so
  the `docker compose` children cannot keep it. Appends use mode `"a"` on the same inode, so
  the lock is valid (no replace-by-rename). The lock sits on the jsonl only. The markdown
  is written solely by `write_markdown()`, which `smoke()` calls inside the held section, so
  it is covered in practice. Nothing else in the repo writes the ledger.
- **N4 on macOS Docker Desktop.** No regression. The api service is on the `internal`
  network only (`compose.yaml:23`, `networks: [internal]`). Docker Desktop containers run
  Linux, so `/proc/net/route` exists inside the container and shows a connected subnet with
  no default route. The route-table reading is unchanged from the previous version. Only
  the host-side default changed to loopback-only, which is what was ruled. The edge, not
  the API, is published to the host. Host-run uvicorn (tests) never sets the flag.
  `create_app` tests inject their own networks.

## New issues

### Critical
None.

### Important
None.

### Minor
- **M1: Ctrl-C during the worker stop still skips the ledger.**
  - Where: `tools/live_smoke.py`, `smoke()` finally block (`except Exception` around
    `target.stop_worker()`).
  - What: `compose stop` can take up to 90 s, which is a realistic moment to press Ctrl-C.
    `KeyboardInterrupt` is not an `Exception`, so `worker_stopped` stays `True` and the
    exception escapes the finally. No row is written, then `stack.down()` removes the
    volumes. This is the N1 failure through a different door.
  - Fix: `except BaseException`, record `worker_stopped = False`, and re-raise after the
    ledger write. Alternatively, set `worker_stopped = False` before the call and set it
    `True` only after the call returns.
- **M2: the leak scan is skipped when the worker is not confirmed stopped.**
  - Where: `tools/live_smoke.py` (the raise precedes `leak_findings`).
  - What: the command fails with `WorkerNotStoppedError` and the key-leak result for that
    run is never produced. Acceptable (the command fails loudly, the stack is torn down),
    but the message could say the scan did not run.
- **M3: the workspace limits and `MAX_CALLS` are the only link in N1's bound.**
  - Where: `ledger_workspace_calls` assumes `per_call == worst_case // MAX_CALLS` equals
    the product's per-attempt reservation. The integration test confirms the count, not the
    per-row `reserved_nano_usd` against the real reservation. It is conservative in
    practice, and not worth more than a one-line comment.

## Assessment
**Task quality:** Approved

**Reasoning:** All seven findings are fixed, apart from the deliberate `CLAUDE.md` line.
The N1, N4 and N6 doubts check out, and no regression found on the macOS Docker Desktop
path. The remaining items are Minor; M1 is the one worth a one-line fix.
