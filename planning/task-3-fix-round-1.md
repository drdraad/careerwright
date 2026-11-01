# Task 3 — fix round 1 (FIX_BASE d4f8728)

Findings are in two review files; IDs below are prefixed A- (task-3-review-A.md) or
B- (task-3-review-B.md). Read each finding's full text there. Fix ALL items listed.

## Must-fix
- A-I1  Master-key rotation must re-seal run outputs (everything the master key seals),
        not only credentials. Add outputs to the rotation test so it would have failed.
        Provide the real `make reseal-credentials` (or rename consistently) and make the
        runbook command work as written (B-M7 overlaps).
- B-I1  live-smoke: stop the worker before reading attempt rows; set the smoke run deadline
        and workspace run limit from the worst case (3 attempts × timeout + backoff).
        Restore an end-to-end test proving every attempt is ledgered (fake model, no live call).
- B-M1  Reconciler: publish succeeded(output) when an accepted output exists; skip terminal
        runs; advance next_reconcile in finally; add a test (simulate the ERROR state; no
        30-min outage needed). Correct ADR 0002's wording.
- B-M2  PRODUCTION=1 is the only opt-in for the production model.
- B-M3  execute() never raises: usage construction inside the guarded path; test it.
- B-M4  Crash after a terminal failure is recorded returns that failure, no second paid call; test.
- B-M5  Separate, longer retry budget for transient_store so a short DB restart does not
        fail runs whose paid call succeeded; test.
- B-M6  BND1-11 and MODEL-02 back to `planned` with the Task 3 part recorded.
- B-M7  Fix stale references (model_registry docstring, localenv, runbook NESSA_HOME).
- B-M8  Leak scan after rotation searches for both old and new keys.
- B-M12 Restore a cumulative per-budget-scope live-call cap in the usage ledger's authorise
        step (refuses once the scope's cap is reached; cap is configuration with a
        conservative default; tested without live calls).
- A-M1  Edge: never resolve targets via outside DNS (pin internal IPs or refuse resolved
        addresses outside the internal subnet). Add a stack probe with a target absent.
- A-M2  DB trigger (or definer function) so a revocation cannot be undone and replaced_by
        cannot change once set; test as pg_api role.
- A-M3  Role-level isolation test parametrized over the 0002 tables.
- A-M8  Distinct error code (409) for rotating/revoking an already-revoked key.
- A-M9  Validation error details never echo client-supplied keys.
- A-M10 Receipts carry workspace_id with cascade (or a minimal response) so workspace
        deletion and reset-demo leave no copies; new forward migration is fine.
- A-M11 Guard rejects clients outside loopback/the internal network (or the equivalent
        documented, enforced launch check) — the unsigned-token path must not be reachable
        from the LAN.
- A-M12 Auth emulator image installs from a committed package.json + pnpm-lock.yaml with
        --frozen-lockfile (GC2).

## Cheap fixes (do them; small)
- A-M4 websocket scopes fail closed; A-M5 status-derived error codes; A-M6 correlation id
  and real status on 500s; A-M7 SSE stream ends at token expiry and re-checks revocation
  (or documented bound); A-M13 dedupe the ProfileOut/RunOut conversions, no private import;
  A-M14 record the expected-version rule in ADR 0004; A-M15 runbook says upgrades are
  forward-only and backup/restore is not yet implemented (SEC-07 open).
- B-M9 make the test assert what its name says; B-M10 delete the dead helper; B-M11 drop the
  public-internet probes from offline acceptance (use TEST-NET where a target is needed).
- Implementer concern: write the firebase-admin licence/transitive-dependency notes in
  docs/dependencies.md.

## Rules
- No live Meta calls in this round (none needed; every fix is testable with fakes).
- Re-run `make check` and `make acceptance` once at the end. Leave the dev stack stopped.
- Append a fix report to task-3-report.md: per ID, the change, the covering test, command, output.
