# Nessa L0 runbook

Everything runs on this machine (ADR 0001). Run commands from the repository root.

## Commands

| Command | What it does |
|---|---|
| `make setup` | Checks Docker (Compose v2), uv, pnpm 10.33.2 and Node 24; installs the locked backend and design-tooling dependencies; creates `NESSA_HOME` (default `~/.nessa/l0`) with generated database passwords and master key `v1`, all owner-only; builds the images. Network is needed here only. Safe to re-run: it never replaces an existing password or key. |
| `make dev` | Starts the stack in **live** mode and waits until healthy: migrates, seeds, prints the URLs. Only the worker can reach the internet (for Meta). |
| `make demo` | Same, in **demo** mode: no Nessa service has a route out of the machine. Model runs are refused. |
| `make stop` | Stops every service within a bound (SIGTERM, then SIGKILL after the grace period). Volumes and `NESSA_HOME` are kept; DBOS recovers in-flight runs on the next start. |
| `make reset-demo` | Recreates the fixture workspace "P01 demo (synthetic)" only. Event numbers continue, so a resumed stream sees the reset. |
| `make check` | Formatting, lint, types, fast tests and the fixture validator. No Docker. |
| `make acceptance` | Integration and stack tests against real PostgreSQL 16, DBOS and the emulator, in separate Compose projects (`nessa-l0-test`, `nessa-l0-stacktest`) and ports. Removes them afterwards. |
| `make live-smoke` | One real connection-check run on the test model through an isolated stack (`nessa-l0-smoke`), at most 3 calls, within the `live-smoke` scope's cumulative cap (9 calls, 3 production, $0.30 worst case by default; `NESSA_LIVE_SMOKE_*` changes it). The worker is stopped before the attempts are read, and every attempt is ledgered in `docs/evidence/live-usage.*`. Only `PRODUCTION=1` uses the production model. Reads `META_API_KEY` from `.env`. |
| `make status` | `docker compose ps` for the stack. |

## Addresses (127.0.0.1 only)

| Service | URL |
|---|---|
| API | `http://127.0.0.1:58000` (`/openapi.json`, `/healthz`, `/readyz`) |
| Firebase Auth emulator | `http://127.0.0.1:59099` (project `demo-nessa`) |
| PostgreSQL | `127.0.0.1:56432` (`nessa_app`, `nessa_dbos`; passwords in `NESSA_HOME/secrets`) |
| Web (Task 4) | `http://127.0.0.1:53000`; the API accepts this origin only |

Seeded identities (emulator, password `nessa-demo-<name>`): `ada@nessa.test` (invited;
owns the fixture workspace), `ben@nessa.test` (invited), `uninvited@nessa.test` (can sign
in, is refused). These are local test credentials, not secrets.

## Calling the API (what the web app must do)

- `Authorization: Bearer <emulator ID token>` on every `/v1` request.
- State-changing requests need `Origin: http://127.0.0.1:53000` (or `localhost`) and an
  `Idempotency-Key: <uuid>`; reuse the key only to retry the same request.
- Writes carry `expected_version`; a `409 STALE_INPUT_VERSION` means reload and reapply.
- Errors are `{"error": {code, message, retryable, stage, correlation_id, details}}`.
- `POST /v1/workspaces/{id}/runs` returns `202` and a `Location`; `GET` that location for the
  authoritative state. `GET /v1/workspaces/{id}/events/stream` is a server-sent-event stream
  (`id` = event sequence); reconnect with `Last-Event-ID`. It ends with an `event:
  reauthenticate` when the token expires. `GET .../events?after=N` is the same as a page.

## Keys and secrets

- A user's Meta key: `POST /v1/workspaces/{id}/credentials` with
  `consent_to_encrypted_storage: true`; rotate with `.../credentials/{cid}/rotate`, revoke
  with `.../revoke`. The key is never returned. Queued runs use the active key at call time.
- Master-key rotation: `cd backend && uv run --locked python -m tools.localenv
  --rotate-master-key`, restart (`make dev`), then `docker compose -p nessa-l0 run --rm
  migrate python -m nessa.cli reseal-credentials`; afterwards the old `v<N>.key` can be
  removed from `NESSA_HOME/keys`. Never delete a key file before resealing.
- `NESSA_HOME` is not in database backups; back it up separately and keep it private.

## Troubleshooting

- "run make setup": `NESSA_HOME` is missing or incomplete.
- A service refuses to start with a `ValidationError`: the configuration is unsafe by
  design (non-local host, non-`demo-` project, missing emulator host). Fix the variable.
- Code changes not visible in containers: `make setup` (or `cd backend && uv run --locked
  python -m tools.stack build`) rebuilds the images; the tests rebuild them automatically.
- Port already in use: another local project holds 58000/59099/56432/53000; stop it or set
  `NESSA_API_PORT`, `NESSA_AUTH_PORT`, `NESSA_PG_PORT` or `NESSA_WEB_PORT` for every
  `make` command (the API then allows that port as its Host and origin).
- Linux hosts are unverified: Compose file secrets are bind mounts, and owner-only files
  may not be readable by the container users there (Docker Desktop maps ownership).
