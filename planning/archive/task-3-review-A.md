# Task 3 review, half A (security boundary, data isolation, API, persistence, profiles)

Reviewer: independent task reviewer. Scope: `review-ff449da..d4f8728-A-security.diff` (7,346 lines,
71 files), read in eleven passes. The working tree was at `d4f8728`. Files outside the diff were
opened only for a named risk; each is listed with the check it served. No suites were re-run, no
focused test was run, no live call was made and `.env` was not read. Every finding below comes
from reading the code. None was reproduced by execution.

### Spec Compliance
- ❌ Issues found: one requirement is only partly met.
  - **Master-key rotation (spec §16 "test nonce/key rotation"; MODEL-05 marked verified)** covers
    credentials only. The same master key also seals run outputs, which are never resealed, and
    the documented procedure then retires the old key (Important 1:
    `backend/src/nessa/cli.py:60-72`, `docs/adr/0004-local-runtime-and-security-boundary.md:81-83`).
  - Everything else this half implements matches the brief and the Sprint 1 card:
    - S1.1: Compose with PostgreSQL 16.15 by digest, the emulator container, migrate, API,
      worker, edge and the `web` profile slot; health checks; Alembic migrations; deterministic
      seeding with two invited identities and one uninvited.
    - S1.2: workspace and profile versions with expected-version writes; source references;
      the typed envelope; the run and outbox schema; non-owner roles including the worker.
    - S1.3: sealed keys with store, rotate and revoke; owner-only master key files; redacted
      logging; Host and Origin rejection; the internal-network egress block.
    - Acceptance (this half): fresh migrate; populated 0001 to head; stale version rejected;
      cross-workspace and uninvited requests fail; key redaction across errors, database cells
      and the export; an unauthorised origin cannot change anything.
- Named-risk checks (one focused check each):
  - **RLS.**
    - Roles: `docker/postgres/initdb/10-roles-and-databases.sh:15-24` creates the runtime roles
      NOSUPERUSER NOBYPASSRLS NOINHERIT, and all tables belong to `nessa_migrator`, which only
      setup uses. Tested in `tests/integration/test_isolation.py::test_runtime_roles_are_not_owners_and_cannot_bypass_row_security`.
    - Coverage: all 13 `nessa` tables enable RLS. FORCE is not needed, because no runtime path
      connects as the owner. The only owner-privileged runtime code is three SECURITY DEFINER
      functions with a pinned `search_path` (`pg_catalog, pg_temp`).
    - Settings: policies read `nullif(current_setting(..., true), '')::uuid`, and
      `backend/src/nessa/db.py:62` sets the value with `is_local => true`. A grep of `src/` and
      `tests/support` finds no session-level `set_config`, so nothing leaks across pooled
      connections.
    - API policies: every workspace-scoped table filters through the `workspaces` policy, which
      checks the owner and an active invitation.
    - Worker policies: scoped by `nessa.run_id`. Sealed material is visible only through
      `authorised_run_workspace()`, which requires that the requester still owns the workspace
      and is still invited.
    - Result: I found no policy that lets either role read another workspace's rows by a
      guessed ID. The worker can set any run ID it finds in the outbox, which is by design: it
      executes any run.
  - **Ownership, 404 vs 403, IDOR.**
    - Every route under `/v1/workspaces/{id}` reaches `visible_workspace` before any read or
      write. That includes spend: I opened `identity/spend_limits.py:33-50` to confirm, since
      the route does not call it itself.
    - `visible_run` checks `found.workspace_id == workspace_id` (`identity/runs.py:120-125`).
    - Credential lookups filter on workspace and credential ID before revoke or rotate.
    - Status codes: uninvited is 403 `NOT_INVITED` on every path; another actor's workspace,
      run or credential is 404. Tested for every GET, the stream, rename, profile PUT, key
      store and revoke, and run submit.
  - **Auth.**
    - firebase-admin skips signature checks only when `FIREBASE_AUTH_EMULATOR_HOST` is set.
      `ApiSettings` makes that variable mandatory and loopback or a single-label service name
      (`backend/src/nessa/config.py:147`), and requires a `demo-` project (`config.py:140`) and
      `NESSA_ENVIRONMENT=local` (`config.py:76`). Without it, startup fails. Domain tests cover the refusals.
    - Gap: the remaining safety rests on the bind address, which the app does not check
      (Minor 11).
  - **Key encryption.**
    - Nonces: 96-bit random nonce per seal; a DB CHECK enforces 12 bytes.
    - Associated data: `nessa:{kind}:{workspace}:{record}` binds the ciphertext to its record.
    - Visibility: the API role has no SELECT on `nonce`/`ciphertext` (column grants, tested).
    - Revocation: the worker reads only `revoked_at IS NULL`, and RLS ends access when the
      invitation is revoked.
    - Leaks: a scan with 12-character key fragments covers responses, errors, the export and
      every `nessa_app` cell.
    - Gaps: master-key rotation is incomplete (Important 1), and the API role can undo a
      revocation (Minor 2).
  - **Host, Origin, CORS, binds, project name, ports.**
    - Host must exactly match an allowlist of loopback `host:port` values plus single-label
      Compose names. This defeats DNS rebinding.
    - Any Origin must be the web origin, and state-changing requests require one. No CORS
      headers are sent.
    - Only the edge publishes, four ports, all on `127.0.0.1` (architecture test). Project
      `nessa-l0` uses ports 58000, 59099, 56432 and 53000. `compose.live.yaml` publishes
      nothing.
  - **Demo egress.**
    - Every service sits only on an `internal: true` network; the worker gets `egress` only in
      `compose.live.yaml`.
    - I opened `backend/tests/stack/test_local_stack.py:110-200` (half B). It probes the API,
      worker, emulator and PostgreSQL toward 1.1.1.1 and a host listener, and runs a positive
      control from the edge. The test proves the block. I did not run it.
    - One unverified edge-relay path is listed (Minor 1).
  - **Error envelope.**
    - Messages come from code only. Validation details hold location and type, never input.
    - `db._transaction` drops driver text (`from None`); Firebase errors do the same.
    - Unexpected exceptions return a fixed `INTERNAL_ERROR`, and logs keep the class and frames
      only.
    - Failure is never an empty success: every list or get on an invisible workspace raises 404
      rather than returning `[]`.
  - **Migrations.**
    - Both revisions are documented as forward-only, and `downgrade()` raises.
    - Grants are column-level and append-only for history. Exceptions: Minor 2 (revocation can
      be undone) and Minor 15 (no restore path exists).
  - **Profile versioning.**
    - Writes take a `FOR UPDATE` lock on the workspace row, compare the expected version, then
      insert `expected+1`. The `(workspace_id, version)` primary key backstops this.
    - The API role has no UPDATE or DELETE on versions, sources or events (tested).
    - Concurrent writes from one version commit exactly one (tested 4-way).
    - No-change writes create no version.
- ⚠️ Cannot verify from diff (they live in half B):
  - The `make` targets and bounded `make stop` (Makefile, `tools/stack.py`).
  - `NESSA_HOME` creation with 0700/0600 permissions, refusal inside the repository, and master
    key generation (`tools/localenv.py`, `tools/setup.py`).
  - DBOS runtime-role grants and `setup-database` / `reset-demo` scoping (`nessa/cli.py`); I
    read only `reseal_credentials`.
  - The worker: outbox dispatch, durable runs, retry ownership, the store-outage terminal state
    and the shutdown watchdog (`identity/worker.py`, `workflow.py`, `activity.py`).
  - Worker-side RLS tests (`test_the_worker_role_sees_only_the_run_it_executes`, revoked access
    hides the key).
  - Server-side budget reservation and the spend policy (`identity/spend.py`, `run_store.py`).
  - Code enforcement of the Contributor ruling (`identity/model_choice.py`, `runs.submit_run`).
    The database CHECK and composite FK in this half are correct.
  - The R5 live-smoke ledger, and register and runbook accuracy.
  - The profile surviving stop and start, and the unsafe-config refusal in the real container
    (stack tests).
  - Carry-forward M4, M7, ADR 0002 decision 7 and the shutdown hang.

### Strengths
- **Isolation in the database, per role.**
  - Separate API and worker policy sets.
  - Definer functions instead of broad grants.
  - Column grants that keep ciphertext from the API role.
  - A no-actor test (`with_no_actor`) proving the empty-setting path sees nothing.
  - Forged-insert refusals tested as `nessa_api`.
- **Commands are correct under concurrency.** Receipts are written in the command's
  transaction, a duplicate is resolved through the unique index, and stale writers fall back to
  the receipt. There are real concurrent tests for both workspace creation and profile writes.
- **Fail-closed configuration.** It targets the actual firebase-admin trigger (the emulator
  variable), not a project-name convention, and refuses inline DB passwords.
- **The egress design is measured, not assumed.** The stack test runs a positive control from
  the edge, so a broken probe cannot pass as a block.
- **Tests run against real infrastructure.** The real app, the real verifier, PostgreSQL 16 and
  the non-owner role (`tests/integration/conftest.py:42-62`), with no mocks of Nessa modules.
- **Field states keep unknown apart from zero.** `unasked`, `unknown`, `skipped` and
  `prefer_not_to_say` are structurally distinct. Sources are server-assigned, and
  client-supplied `source_ref_id` is rejected.

### Issues
#### Critical
None.

#### Important
1. **Master-key rotation leaves run outputs on the retired key.**
   - Location: `backend/src/nessa/cli.py:60-72`, `backend/src/nessa/identity/runs.py:128-136`,
     `backend/src/nessa/migrations/versions/r0002_credentials_runs_spend.py:96`,
     `docs/adr/0004-local-runtime-and-security-boundary.md:81-83`, `docs/runbook.md:50-52`.
   - What: `reseal_credentials` re-encrypts `nessa.credentials` only. But `nessa.run_outputs`
     is sealed with the same keyring (`identity/activity.py:230`) and has its own `key_version`
     column. ADR 0004 decision 8, the runbook and the command's docstring all say the old
     `v<N>.key` can then be removed.
   - Effect: once it is removed, `open_output` raises `MasterKeyError`. Every complete run has
     an output (`complete_runs_have_an_output`), so `GET /runs`, `GET /runs/{id}` and `GET
     /export` return 500 for any workspace with a completed run, and those outputs can never be
     decrypted again.
   - Why the test misses it: `test_master_key_rotation.py:24` seeds only credentials, so it
     passes. `tools/localenv.py:75` also names a `make reseal-credentials` target that does not
     exist.
   - Why it matters: following the documented procedure loses sealed data and breaks run
     listing and export (portability). Later sprints will seal private outputs through the same
     path.
   - Fix:
     - Reseal `run_outputs` (and every future sealed table) in the same transaction, under a
       command named for what it does.
     - Have the command refuse to report success while any sealed row is still on a
       non-current version.
     - Add a sealed run output to the rotation test, and assert that every run opens after `v1`
       is deleted.
     - Until then, change the ADR and runbook to say "do not retire old key files".

#### Minor
1. **The edge resolves targets by name on a container that has an external route.**
   - Location: `backend/src/nessa/edge.py:56-61`, `compose.yaml:124`.
   - What: `open_connection("api"|"web"|...)` runs on the one container that is also on a
     normal bridge. When a target container is absent, Docker's DNS forwards the name upstream.
     In Task 3, `web` is always absent. With a host search domain that resolves `web.<domain>`,
     the relay could carry local request bytes off the machine in demo mode, including bearer
     tokens and keys in `POST /credentials`.
   - Status: unverified hypothesis. I did not inspect a running edge's `resolv.conf`.
   - Fix: pin targets to internal IPs (static `ipv4_address` on the internal network), or have
     the edge refuse a resolved address outside the internal subnet. Add a stack probe with the
     target stopped.
2. **The API role can undo a key revocation.**
   - Location: `r0002_credentials_runs_spend.py:208`.
   - What: `nessa_api` has UPDATE on `revoked_at`, `revoked_by` and `replaced_by`. Setting both
     revocation columns back to NULL satisfies the CHECK. The application never does this, but
     RLS here exists to survive application bugs.
   - Fix: add a BEFORE UPDATE trigger that rejects `revoked_at` going from non-null to null and
     any change to `replaced_by` once set. Alternatively, drop the UPDATE grant and revoke
     through a narrow definer function.
3. **The database isolation test for the API role covers only the 0001 tables.**
   - Location: `backend/tests/integration/test_isolation.py:16`.
   - What: credentials, spend_limits, runs, run_outputs, model_attempts and outbox have no
     `as_role("pg_api", ..., actor=BEN)` check. The API-level tests cannot catch an
     over-permissive policy on them, because application SQL already filters by workspace after
     `visible_workspace`. SEC-02 "verified" rests on reading the policies for these tables.
   - Fix: parametrize the role test over the 0002 tables, using a workspace that holds a
     credential, a run and an output.
4. **Non-HTTP scopes pass through the guard unchecked.**
   - Location: `backend/src/nessa/api/guard.py:66`.
   - What: a `websocket` scope skips the Host and Origin checks. No WebSocket routes exist
     today, so nothing is exposed.
   - Fix: fail closed for `websocket` (pass only `lifespan`).
5. **Every Starlette HTTP exception becomes code `NOT_FOUND`.**
   - Location: `backend/src/nessa/api/envelope.py:106-112`.
   - What: a 405 returns code `NOT_FOUND` with message "No such resource." and status 405, so
     the typed code contradicts the status.
   - Fix: derive the code from the status, or add a method-not-allowed code.
6. **500 responses lack `x-correlation-id`, and the access log records status 0.**
   - Location: `envelope.py:115`, `guard.py:82-95`.
   - What: Starlette runs the `Exception` handler in `ServerErrorMiddleware`, outside
     `RequestGuard`, so the guard never sees the response. Established by reading Starlette's
     middleware order; not executed.
   - Fix: catch unexpected exceptions inside the guard and send the `INTERNAL_ERROR` envelope
     through `send_with_id` when no response has started.
7. **The SSE stream does not re-check Firebase token revocation.**
   - Location: `backend/src/nessa/api/routes_events.py:103`.
   - What: a revoked invitation ends the stream through RLS on the next poll, but a token
     revoked or disabled in Firebase keeps streaming until it expires (up to an hour).
   - Fix: re-verify with `check_revoked` periodically, or document the gap.
8. **Rotating an already-revoked key returns `NOT_FOUND`.**
   - Location: `backend/src/nessa/identity/credentials.py:137-141`.
   - What: "absent" and "revoked" share one code (GC6 asks for distinct states).
   - Fix: use a distinct code with 409.
9. **Validation details can echo client JSON keys.**
   - Location: `envelope.py:79-84`.
   - What: `loc` carries client-supplied keys for `extra_forbidden` errors. That contradicts
     the module's "request input never appears" claim.
   - Fix: replace path segments that are not schema fields with a placeholder.
10. **Receipts keep full response bodies, including profile documents, keyed only by actor.**
    - Location: `r0001_identity_workspaces_profiles.py:113-121`.
    - What: receipts are absent from the export and are not removed with the workspace;
      `reset-demo` leaves copies behind.
    - Fix: before deletion work (DUR-06, spec §19), add a cascading `workspace_id` FK or store a
      minimal response.
11. **The unsigned-token safety depends on the bind address, which nothing checks.**
    - Location: `compose.yaml:74`, `guard.py:30-53`.
    - What: the Host allowlist stops browsers (rebinding) but not a LAN client that forges
      `Host:`. If the API were started on the host with `--host 0.0.0.0`, LAN clients could
      mint emulator tokens.
    - Fix: reject `scope["client"]` outside loopback and the internal network, or state in
      ADR 0004 decision 2 that loopback exposure relies on the Compose/edge launch only.
12. **The auth emulator image is not lockfile-pinned.**
    - Location: `docker/auth/Dockerfile:10`.
    - What: `pnpm add --global firebase-tools@15.34.1` resolves transitive dependencies at
      build time with no lockfile (GC2), so rebuilds can drift.
    - Fix: install from a committed `package.json` and `pnpm-lock.yaml` with
      `--frozen-lockfile`.
13. **Conversions are duplicated.**
    - Location: `backend/src/nessa/api/routes_profile.py:79,98`,
      `backend/src/nessa/api/routes_export.py:21,65,116`, `backend/src/nessa/api/routes_runs.py:26`.
    - What: the ProfileVersion to ProfileView to ProfileOut conversion appears three times, and
      RunOut assembly twice. The export module also imports the private `_Out`.
    - Fix: a `ProfileOut.of_version` classmethod and one shared run-out helper.
14. **GC7 partly met: some commands carry no expected version.**
    - Location: `backend/src/nessa/identity/runs.py:30-33`, `routes_credentials.py`.
    - What: credential store, rotate and revoke, and run submission, carry no expected version.
      This is acceptable today: rotate's `credential_id` is the precondition, and
      `connection_check` reads no inputs.
    - Fix: record the rule so the first run kind that reads the profile pins the input version.
15. **The forward-only migrations point at a backup path that does not exist.**
    - Location: `r0001...py:10`, `r0002...py:12`.
    - What: both say "restore from a backup instead", but backup and restore are not
      implemented (SEC-07 open), and the runbook does not say upgrades are irreversible.
    - Fix: add one runbook line.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The isolation, identity, envelope and versioning work in this half is careful and
tested against real PostgreSQL with non-owner roles, and I found no cross-workspace path. But the
documented master-key rotation procedure makes sealed run outputs permanently unreadable and
breaks run listing and export, so that one item must be fixed before rotation can be trusted.
