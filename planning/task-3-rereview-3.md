# Task 3 re-review 3 (a56c206..eb70b6a), scope: backend/tools/live_smoke.py + tests

## Per ID
- M1: Fixed. live_smoke.py:408-415 catches BaseException, sets worker_stopped=False, ledgers (417-427), then
  `raise interrupted` (429-430). KeyboardInterrupt/SystemExit are re-raised, not swallowed; smoke_stack still tears down.
  Test parametrized over KeyboardInterrupt (test_live_smoke_ledger.py).
- M2: Fixed. leak_findings runs and prints after the ledger on failed stop (live_smoke.py:432-434); the
  WorkerNotStoppedError message carries the findings (436-439).
- M3: Fixed. assert_attempt_bound (live_smoke.py:271-280) runs on the stored limits returned by the API (line 380),
  before the credentials PUT; possible-call rows use the product reservation (line 298). Unit tests cover the
  binding limit and the 4-attempt refusal.

## Specific checks
- Production path: smoke_stack sets NESSA_SYNTHETIC_MODEL_ROLE=production when --production-model (live_smoke.py:475-486);
  config.py:94 / api main.py:29 / worker.py:165 pick the run model from that role, and authorise() returns
  models.production.model_id. So submitted["model_id"] equals the priced model on both paths; the check cannot block
  the production path unless the stack and CLI disagree (the intended refusal).
- Second Ctrl-C: a second interrupt during ledger_workspace_calls / write_markdown would skip remaining rows and replace
  the first interrupt. Not signal-masked (not demanded); see Minor.

## New issues
### Critical
None.
### Important
None.
### Minor
- m1: If leak_findings (live_smoke.py:433) itself raises (e.g. docker down, the very reason the stop failed), the
  WorkerNotStoppedError is replaced by that error. The ledger is already written, so no data is lost; the failure is
  still loud. Optionally wrap and report "leak scan did not run".
- m2: On the interrupt path the leak scan is skipped (raise at 430 precedes it); acceptable, but the user is not told.
- m3: The ledger-then-raise window is a few seconds of DB reads; a second Ctrl-C there loses possible-call rows
  (rows appended so far persist). Noted only.
- m4: The model-mismatch RuntimeError is raised after the run was submitted; finally handles it correctly, but the
  message does not say a run may already have been submitted. Cosmetic.

## Assessment
**Task quality:** Approved
**Reasoning:** All three Minors are fixed with RED-first tests; the BaseException handling re-raises after ledgering and the model check is consistent with the production path. Remaining items are cosmetic.
