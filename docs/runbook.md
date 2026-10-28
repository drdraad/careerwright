# Nessa L0 runbook

Everything runs on this machine (ADR 0001). Run commands from the repository root.

## Commands

| Command | What it does |
|---|---|
| `make setup` | Checks Docker (Compose v2), uv, pnpm 10.33.2 and Node 24; installs the locked backend, web-app and design-tooling dependencies and Playwright's Chromium; creates `NESSA_HOME` (default `~/.nessa/l0`) with generated database passwords and master key `v1`, all owner-only; downloads the pinned ESCO release (10 MB) into `var/datasets/` and keeps it only if its size and SHA-256 match; builds the images (backend, Auth emulator, web). Network is needed here only. Safe to re-run: it never replaces an existing password or key, and re-verifies a dataset already present instead of fetching it again. |
| `make dev` | Starts the stack in **live** mode and waits until healthy: migrates, seeds, imports the ESCO release on the first start (about 6 s; later starts find it imported), starts the web app, prints the URLs. Only the worker can reach the internet (for Meta). |
| `make demo` | Same, in **demo** mode: no Nessa service has a route out of the machine. Calls to Meta are refused; a demo workspace's interview turns are answered by the offline fixture interviewer, labelled as such. |
| `make stop` | Stops every service within a bound (SIGTERM, then SIGKILL after the grace period). Volumes and `NESSA_HOME` are kept; DBOS recovers in-flight runs on the next start. |
| `make reset-demo` | Recreates the fixture workspace "P01 demo (synthetic)" only. Event numbers continue, so a resumed stream sees the reset. |
| `make check` | Backend: formatting, lint, types, fast tests and the fixture validator. Web (`apps/web`, `pnpm run check`): generated-client drift, Biome, `tsc`, Vitest. No Docker, no network. |
| `make acceptance` | Integration and stack tests against real PostgreSQL 16, DBOS and the emulator, in separate Compose projects (`nessa-l0-test`, `nessa-l0-stacktest`) and ports; then the Storybook build and the Playwright suite on its own demo stack (`nessa-l0-webtest`, web on `127.0.0.1:57600`): the browser journey with a full restart, keyboard, access and visual checks. Removes them afterwards. |
| `make live-smoke` | One real connection-check run on the test model through an isolated stack (`nessa-l0-smoke`), at most 3 calls, within the `live-smoke` scope's cumulative cap (9 calls, 3 production, $0.30 worst case by default; `NESSA_LIVE_SMOKE_*` changes it). `INTERVIEW=1` runs one interview turn instead, with a fixed synthetic message, and confirms its proposals into the profile: one attempt, at most 2 calls (the call and one validation repair). One invocation at a time: a second refuses while the ledger is held. The worker is stopped before the attempts are read, and every attempt is ledgered in `docs/evidence/live-usage.*` with its request count; if the worker cannot be confirmed stopped, every further call it could make is ledgered with an unknown cost and the command fails. Only `PRODUCTION=1` uses the production model. Reads `META_API_KEY` from `.env`. |
| `make rotate-master-key` | With the stack running: adds master key `v<N+1>` to `NESSA_HOME/keys`, then runs `make reseal`. The only way to rotate the master key. |
| `make reseal` | Restarts a running API and worker so they load every key version (their mode is kept), then reseals every sealed record (stored keys, run inputs and run outputs) under the newest key, and fails if any record is left on an older version. Run it again if a rotation was interrupted. Restarting the worker recovers an in-flight run, whose model call may then be made again, within its spend reservation. |
| `make status` | `docker compose ps` for the stack. |

## Addresses (127.0.0.1 only)

| Service | URL |
|---|---|
| API | `http://127.0.0.1:58000` (`/openapi.json`, `/healthz`, `/readyz`) |
| Firebase Auth emulator | `http://127.0.0.1:59099` (project `demo-nessa`) |
| PostgreSQL | `127.0.0.1:56432` (`nessa_app`, `nessa_dbos`; passwords in `NESSA_HOME/secrets`) |
| **Nessa (web app)** | `http://127.0.0.1:53000` (open this). It answers only to `127.0.0.1:53000` and `localhost:53000` as Host, and forwards `/api/v1/*` to the API |

Seeded identities (emulator, password `nessa-demo-<name>`): `ada@nessa.test` (invited;
owns the fixture workspace), `ben@nessa.test` (invited), `uninvited@nessa.test` (can sign
in, is refused). These are local test credentials, not secrets.

## Using the web app

1. `make demo` (or `make dev`), then open `http://127.0.0.1:53000`.
2. Sign in: the page offers the three seeded identities. Ada owns "P01 demo (synthetic)".
3. **You** edits what Nessa knows. Each answer is Answered, Unknown, Skipped, Prefer not to
   say or Not asked yet, never a blank standing in for zero. Saving makes a new version;
   **Source** shows where an answer came from.
4. **Routes** in the fixture workspace shows the TRACE-01 fixture preview, labelled as such.
   Select a route to inspect it. The route search itself is not built yet, so the other
   chapters show what they will hold and which answers they need.
5. The strip shows the saved version and the live-update state. After `make stop` and
   `make demo` the open page reconnects by itself, and a reload reopens the same work.
6. Calm mode (account menu) turns off motion; `prefers-reduced-motion` does the same.

For UI work without Docker: `cd apps/web && pnpm storybook` (component states on
`127.0.0.1:6006`). After an API change, run `pnpm run generate` in `apps/web` and commit the
regenerated client.

`cd apps/web && pnpm run review-screenshots` regenerates the visual review package in
`docs/reviews/sprint-1/screenshots/`. It needs Docker: like `make acceptance`, it builds and
starts its own stack (`nessa-l0-webtest`) and removes it afterwards.

## Calling the API (what the web app does)

The web app calls these through its own origin (`/api/v1/...`). Its server forwards them
with the browser's Origin unchanged.

- `Authorization: Bearer <emulator ID token>` on every `/v1` request.
- State-changing requests need `Origin: http://127.0.0.1:53000` (or `localhost`) and an
  `Idempotency-Key: <uuid>`; reuse the key only to retry the same request.
- Writes carry `expected_version`; a `409 STALE_INPUT_VERSION` means reload and reapply.
- Errors are `{"error": {code, message, retryable, stage, correlation_id, details}}`.
- `POST /v1/workspaces/{id}/runs` returns `202` and a `Location`; `GET` that location for the
  authoritative state. `GET /v1/workspaces/{id}/events/stream` is a server-sent-event stream
  (`id` = event sequence); reconnect with `Last-Event-ID`. It ends with an `event:
  reauthenticate` when the token expires. `GET .../events?after=N` is the same as a page.
- Interview (ADR 0006): `POST /v1/workspaces/{id}/interview/turns` with
  `{expected_profile_version, message}` returns `202` and the turn; `GET .../interview/turns/
  {turn_id}` shows its run and, once complete, its validated proposals (`proposal.changes`,
  each with a `change_id`, the messages it cites and `hard_constraint`). Nothing is saved
  until `POST .../interview/turns/{turn_id}/decision` with `{expected_version, accept:
  [change IDs], confirm_hard_constraints: [fields]}`: every accepted limit or target must be
  named in `confirm_hard_constraints`, and the profile must still be the version the message
  was sent with (`409 STALE_INPUT_VERSION` otherwise: send the message again).
- Taxonomy: `GET /v1/taxonomy` (the ESCO release and its attribution), `GET
  /v1/taxonomy/occupations?q=...&match=all|any`, `GET /v1/taxonomy/occupations/{concept_id}`;
  English cities: `GET /v1/places`. A title ESCO lacks: `POST
  /v1/workspaces/{id}/occupations/provisional` with `{title}`.

## Keys and secrets

- A user's Meta key: `POST /v1/workspaces/{id}/credentials` with
  `consent_to_encrypted_storage: true`; rotate with `.../credentials/{cid}/rotate`, revoke
  with `.../revoke`. The key is never returned. Queued runs use the active key at call time.
- Master-key rotation: `make rotate-master-key` while the stack runs. When it reports
  success, nothing is sealed under the old version any more, so the old `v<N>.key` may be
  removed from `NESSA_HOME/keys`; until then keep every key file. If it was interrupted,
  run `make reseal` (it refuses to report success while any record is on an old version).
- `NESSA_HOME` holds the only copy of the master keys and database passwords; keep it
  private.

## Upgrades and backups

- Migrations are forward-only: an upgrade cannot be rolled back by a downgrade migration.
- Backup and restore are not implemented yet (SEC-07 is open). Until they are, an upgrade
  that goes wrong cannot be undone, and losing the Docker volumes or `NESSA_HOME` loses the
  data.

## Troubleshooting

- "run make setup": `NESSA_HOME` is missing or incomplete.
- The `migrate` service fails with `esco-v1.2.1-en-csv is not at /datasets/...`, or the API
  answers `TAXONOMY_UNAVAILABLE`: the ESCO release was not fetched. Run `make setup`. If its
  download fails (the publisher moved the file), the **manual step** (ruling R7): open
  https://esco.ec.europa.eu/en/use-esco/download, choose version "ESCO dataset - v1.2.1",
  content "classification", language "en", file type "csv", download the zip and save it as
  `var/datasets/esco-v1.2.1-classification-en-csv.zip`, then run `make setup` again. Its
  SHA-256 must be `f9761b0b52be1828b38a3e5e0ae59a93a7b0ce358bc800f52f57a8b002adeb3e`;
  any other file is refused.
- Saving the profile is refused with `VALIDATION_FAILED` (`unknown_city`): a work area must
  be one of the 55 English cities (`GET /v1/places`), such as Leeds or Kingston-upon-Hull.
- A service refuses to start with a `ValidationError`: the configuration is unsafe by
  design (non-local host, non-`demo-` project, missing emulator host). Fix the variable.
- Code changes not visible in containers: `make setup` (or `cd backend && uv run --locked
  python -m tools.stack build`) rebuilds the images; the tests rebuild them automatically.
- Port already in use: another local project holds 58000/59099/56432/53000; stop it or set
  `NESSA_API_PORT`, `NESSA_AUTH_PORT`, `NESSA_PG_PORT` or `NESSA_WEB_PORT` for every
  `make` command (the API and the web app then allow that port as their Host and origin).
- Asked to sign in again after `make stop` and `make demo`: the Auth emulator re-imports its
  seed on start, which ends sessions issued before. A page that stayed open refreshes its
  token by itself and reconnects; a page loaded before that asks you to sign in, then returns
  to the same address.
- The page says "This server answers only on its local address": the browser used another
  name for the web app. Open `http://127.0.0.1:53000` or `http://localhost:53000`.
- The strip says "Couldn't refresh: showing what was last loaded" or "Reconnecting": the API
  is restarting or stopped. Nothing is lost; the page catches up when it is back. "Updates
  stopped: sign in again" means the session ended; sign in again.
- The web container refuses to serve and its log says "refuses to serve": a `NESSA_*`
  variable is unsafe (a non-loopback host or emulator, or a non-`demo-` project).
- The client is out of date (`make check` says so): run `pnpm run generate` in `apps/web`.
- Linux hosts are unverified: Compose file secrets are bind mounts, and owner-only files
  may not be readable by the container users there (Docker Desktop maps ownership).
