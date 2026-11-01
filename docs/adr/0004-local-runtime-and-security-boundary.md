# ADR 0004: Local runtime, identity and the database security boundary

- Status: Accepted (Task 3, Sprint 1; evidence: `make check`, `make acceptance`, `make live-smoke`)
- Date: 2026-10-28
- Requirements: BND1-11/13/14, SEC-01/02/03/04, ARC1-08/09, MODEL-02/05/06/07/08,
  DUR-01/02/03/08, API-01/02, Global Constraints 7, 8 and 9

## Context

Sprint 1 builds the platform every later sprint relies on: the command contract, the
Compose stack, identity, versioned writes, the outbox and runs, encrypted keys and spend.
ADR 0001 fixes the local boundary and ADR 0002 the durable-execution composition. This ADR
records how they are realised, and the choices a later task must not undo silently.

## Decisions

1. **No route out, by network, not by convention.** Every service (PostgreSQL, the Auth
   emulator, the API, the DBOS worker, the setup job) is attached only to a Compose network
   with `internal: true`. On Docker Desktop that is the only setting that blocks egress
   (a bridge without masquerading still reaches the internet: checked on this machine), and
   it also stops Docker publishing ports. So a small standard-library TCP relay
   (`careerwright.edge`) is the one container also on a normal bridge: it publishes the API, the
   emulator, PostgreSQL and the web slot on `127.0.0.1` only, forwarding each port to one
   fixed internal target and opening no other connection. It resolves a target by name but
   connects only to an address inside the internal subnet (read from its route table), so
   an absent target such as Task 3's `web`, which Docker's DNS would forward upstream, is
   refused rather than followed off the machine. `compose.live.yaml` (`make dev`)
   adds an egress network to the worker alone, because only its model activity calls Meta.
   `make demo` omits it. The acceptance suite proves both: probes from the API, worker,
   emulator and database fail, and the same probe from the edge (positive control) reaches
   a listener on the host; in live mode the worker reaches it and the API still cannot.

2. **Loopback requests only.** The API serves loopback clients only. Its container's
   configuration (`CAREERWRIGHT_API_INTERNAL_NETWORK_CLIENTS`, set in `compose.yaml`) adds its own
   internal Compose subnet, where the edge relays from; on a host the API stays
   loopback-only, because docker0, a VPN or a second NIC would look internal by route
   alone. The client address is the socket peer (`--no-proxy-headers`), so no header can
   change it. The emulator's unsigned tokens are therefore unusable from the LAN even if
   the API listens on every interface. It rejects any Host header
   outside a configured list of local `host:port` values (defeats DNS rebinding), any
   request carrying an Origin other than the Careerwright web origin, any state-changing request
   without an Origin, and every WebSocket (close code 1008; the API has none). A different
   app on `127.0.0.1` therefore cannot trigger an authenticated change even with a token.
   No CORS headers are ever sent; the web app reaches the API through its own origin. The
   event stream re-verifies its token with the emulator every minute and ends when the
   account is revoked or disabled, or when the token expires.

3. **Fail closed at startup.** Configuration is refused unless `CAREERWRIGHT_ENVIRONMENT=local`,
   the Firebase project is a `demo-` project, the emulator host and every allowed host are
   loopback or single-label Compose names, origins are exact `http` loopback origins,
   database URLs carry no password (passwords come from files) and the master key directory
   and files are owner-only. Without `FIREBASE_AUTH_EMULATOR_HOST` the Admin SDK would
   verify against Google's keys, which L0 never contacts, so its absence is an error.

4. **Identity: the Admin SDK against the emulator, then an invitation.** The API verifies
   each ID token with `firebase_admin.auth.verify_id_token(check_revoked=True)` (project,
   issuer, expiry, disabled account, revoked tokens). Emulator tokens are unsigned: this is
   local-only identity, never evidence of production security (ADR 0001). A verified token
   must then match an active invitation by verified email; the first sign-in binds the
   Firebase UID, and a different account later presenting the same email is refused. The
   lookup is one `SECURITY DEFINER` function, so the API role cannot read the allowlist.

5. **Ownership enforced by PostgreSQL row-level security, per role.** Tables are owned by
   `careerwright_migrator`, used only by setup (migrations, seeding, demo reset, master-key reseal).
   The API connects as `careerwright_api` and sets `careerwright.actor_id` per transaction
   (`set_config(..., is_local => true)`, so a pooled connection never carries it into the
   next request); it sees only workspaces that actor owns while the actor is invited, and
   every workspace-scoped table filters through that policy. The worker connects as
   `careerwright_worker` and sets `careerwright.run_id`: it sees the run it executes, and the sealed key
   and outputs only while the run's requester still owns the workspace and is invited
   (`careerwright.authorised_run_workspace()`). It has no access to profile tables. DBOS uses
   `careerwright_dbos_runtime`; `careerwright_dbos_owner` runs DBOS's migrations. No runtime role is an
   owner, superuser or `BYPASSRLS` (tested). Least-privilege column grants: the API can seal
   and revoke keys but cannot select a nonce or ciphertext; history tables are append-only.

6. **Versioned writes and commit-ordered events.** Profiles are immutable versions; a write
   names the version it read and inserts the next one under a workspace row lock, so a stale
   write gets `STALE_INPUT_VERSION` and never merges. A workspace starts at version 0 (no
   profile saved), never a fabricated version 1. Answers cite source references the server
   assigns (direct entry by an actor, or a fixture pinned by path and SHA-256). Status
   events take their sequence number from the workspace row under the same lock, so numbers
   increase in commit order and a stream resumed from `Last-Event-ID` misses nothing.

7. **Idempotent consequential commands.** Every write carries an `Idempotency-Key`; the
   response is stored as a receipt in the same transaction. A retry returns the stored
   response, a concurrent duplicate is resolved to the first, and reusing a key for a
   different request is refused. Receipts never fingerprint a key value. Each receipt
   belongs to its workspace and is deleted with it, so a deleted or reset workspace leaves
   no copy of its responses.

   Expected versions (GC7): a command that changes state derived from user input carries
   the version it was based on (profile writes carry `expected_version`; a stale one is
   `STALE_INPUT_VERSION`). Credential store, rotate and revoke carry none: the credential
   ID is their precondition and a revoked key is `CREDENTIAL_REVOKED`. Run submission
   carries none only because the connection check reads no workspace input. The first run
   kind that reads the profile must take the profile version as an expected version and
   pin it on the run, so a run never silently uses inputs newer or older than the client
   saw. (Done by the interview turn, ADR 0006 decisions 10 and 11.)

8. **Keys: consent, sealing, rotation, revocation.** Storing a key needs explicit consent
   to encrypted storage. It is sealed at once with AES-256-GCM under the current master-key
   version, with kind, workspace and credential ID as associated data. Master keys are
   `v<N>.key` files in `CAREERWRIGHT_HOME/keys` (default `~/.careerwright/l0`, outside the repository and
   the database), owner-only; the highest version seals. Rotation (`make rotate-master-key`):
   add a version, then reseal (`make reseal`), which first restarts a running API and
   worker so they hold every version, then reseals every sealed record, stored keys and run
   outputs alike. It is the only rotation path. Reseal finds every table with a key version
   and fails while any row is left on an older one, so the old file may be retired only
   after it succeeds. The worker resolves the workspace's active key just before each call,
   so a revocation or user-key rotation applies to every queued run. A revocation and a
   replacement are final: a database trigger refuses any update that clears or changes
   them, so an application bug cannot undo one.

9. **Runs: the first model run is a connection check.** It sends a fixed synthetic prompt
   and no workspace data (spec section 16: check availability at key setup), so it proves
   the key, entitlement and strict schema output end to end without exposing a profile.
   Submission pins the model: non-synthetic workspaces always get the Standard production
   model; synthetic ones get the configured role (test by default). The database refuses a
   Contributor model on a non-synthetic run (a CHECK over the run's copy of the workspace
   label, held equal to the workspace by a composite foreign key), and the activity checks
   again. Demo workspaces and the demo runtime never call a model. (Amended by ADR 0006
   decision 12: they never call a *provider* model; a demo workspace's interview turns use
   the offline fixture interviewer, which a CHECK confines to demo workspaces.)

10. **Spend is reserved in the database before every call.** Each provider attempt is a row
    written before the call with its worst-case cost reserved, under a per-workspace
    advisory lock, against a per-run and a per-calendar-month (UTC) limit. Reported usage
    reconciles it; a failed or interrupted call without reported usage stays `unknown` and
    keeps its full reservation committed. The same rows are the reconciliation record.

11. **Database outage during a run ends typed.** The activity retries its own database
    work (the attempt row, then the result) for up to 60 seconds, keeping a paid call's
    result in memory, so a short restart costs nothing and the run completes on that call.
    Past that budget the store failure is terminal (a step retry would call the model
    again): the run is published `failed/app_store_unavailable` by a step that keeps
    retrying for about 34 minutes, and an attempt whose result could not be stored is
    settled as an unknown charge. A workflow that still ends in DBOS `ERROR` is reconciled
    on the worker's next reconciliation pass (every 60 seconds, even after a failed pass):
    a run that has an accepted output is published `complete` with it, otherwise its
    recorded failure or `unknown_failure`; runs already terminal are left alone. Tested by
    simulating the `ERROR` state, since reaching it for real takes over half an hour.

12. **Logs.** JSON lines with identifiers and error classes; exception messages are dropped
    (class and frames kept); bearer tokens, JWTs, URL passwords and every process secret are
    scrubbed; DBOS and uvicorn log through the same formatter. The access log has paths only.

## Rejected alternatives

- Disabling NAT on a bridge network (egress still worked on Docker Desktop), or blocking
  egress with proxy variables (not a block).
- Verifying emulator tokens with our own JWT code: the Admin SDK path is the one a hosted
  milestone would keep, and hand-written verification of unsigned tokens adds no safety.
- Application-only ownership checks: one missing `WHERE` would leak a workspace.
- Pinning the credential on the run: a revoked or rotated key would still be used.

## Consequences and open items

- Not done in Task 3: run cancellation (DUR-05, with the solver in T13), workflow-history
  deletion (DUR-06), backup and restore (SEC-07), the web app and generated TypeScript client
  (Task 4). Linux hosts: see the amendment of 2026-11-01.
- Changing the activity's step sequence needs a new DBOS `application_version`
  (`careerwright-l0-1`) and a drain of in-flight runs (ADR 0002 decision 9).
- A later run kind that handles profile data must keep the minimum-data rule (spec section
  19) and extend the leak scans with that data's sentinels.

## Amendment, 2026-11-01 (the stack on a Linux Docker host; the product owner's yes)

**Problem.** Compose file secrets and the `keys/` and `adzuna/` directories are bind mounts
of `CAREERWRIGHT_HOME`, which `make setup` makes owner-only (0600 files, 0700 directories).
On Linux a bind mount keeps the host owner and mode, so the service users (postgres, uid
999; the backend's `careerwright`, uid 10001) could not read them, and every integration and
stack test failed at setup. Docker Desktop for Mac hides host ownership, so it never showed.

**Decision.** Each container that is given secrets or a host directory starts as root just
long enough to copy exactly what it was given into a container-private in-memory directory
owned by its service user, then drops to that user:

- The backend services that need it (`migrate`, `api`, `worker`, `acquisition`) run as
  `user: root` with `python -m careerwright.entrypoint` as their entrypoint and a tmpfs at
  `/run/careerwright/private` (mode 0700, 1 MiB, `noexec,nosuid,nodev`). The entrypoint
  refuses to run unless it is root and that path is a mount. It copies each regular file of
  `/run/secrets`, `/run/careerwright/keys` and `/run/careerwright/adzuna`, whichever the
  container has, to `/run/careerwright/private/<name>/` (files 0400, directories 0500,
  owned by `careerwright`), clears supplementary groups, sets the group, then the user,
  sets `HOME` as Docker would, and `exec`s the service's command. Standard library only.
- PostgreSQL runs `docker/postgres/entrypoint.sh` (mounted read-only) as root first. It
  copies the secrets for the postgres user the same way, then `exec`s the image's own
  `docker-entrypoint.sh`, which drops to postgres as before. `POSTGRES_PASSWORD_FILE` and
  the init script read the copies.
- Every `*_PASSWORD_FILE`, `CAREERWRIGHT_MASTER_KEY_DIR` and
  `CAREERWRIGHT_ADZUNA_CREDENTIALS_DIR` points at the copy. The bind mounts, the Compose
  secrets and which container gets which are unchanged. `edge` and `web` are unchanged.

**Why this way.** The host keeps its meaning: owner-only files, and `check_permissions`
unchanged; nothing becomes group- or world-readable. Each container still holds only its
own files, because it copies only what Compose gave it. The copies live in memory and go
with the container: no value is printed, passed as an argument, put in the environment, an
image layer or on disk. A restart (`make rotate-master-key` restarts the API and worker)
copies afresh, so a new key version arrives as before. Root inside the container reads the
bind mounts on Linux, under rootless Docker (where it is the host user) and on Docker
Desktop, so the Mac keeps working.

**Rejected.** Compose's `uid`, `gid` and `mode` on a secret: for a file secret Compose has
bind-mounted the file and ignored them, and they cannot cover the `keys/` directory, whose
versions vary, so it would fix only half. Not proven on this Compose (v5.6.1): the Docker
daemon was not running for this task. Making the host files group-readable, or `chown`ing
them to the container uids: that weakens the host's owner-only rule. Running the services
as the host user's uid: on a root host that is root. A one-shot copy into a shared volume:
a volume is on disk, and a tmpfs volume empties when its writer exits.

**Consequences.** Compose's init (PID 1) and any `docker compose exec` or health check in
those four containers now run as root, as PostgreSQL's always have; the service itself runs
as `careerwright` with no supplementary group. `test_each_service_runs_as_its_own_user_holding_read_only_copies_of_its_own_files`
checks the service's user, its groups and every copy's owner and mode;
`tests/domain/test_container_entrypoint.py` checks the copy and the privilege drop.
