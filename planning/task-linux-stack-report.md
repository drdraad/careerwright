# Task report: the local stack on a Linux Docker host

Status: DONE_WITH_CONCERNS. The change is in, and the fast checks pass. I could not run
acceptance: the Docker daemon was not running (details below).

## What changed (commit 578b0fe)
The containers that get secrets or a host folder (postgres, migrate, api, worker,
acquisition) now start as root. They copy exactly what they were given into a private
in-memory folder (tmpfs) owned by the service user, then drop to that user. The services
read only those copies.

- `backend/src/careerwright/entrypoint.py` (new, standard library only). It refuses to run
  unless it is root and `/run/careerwright/private` is a mount. It copies each regular file
  of `/run/secrets`, `/run/careerwright/keys` and `/run/careerwright/adzuna` (whichever the
  container has) to `/run/careerwright/private/<name>/`: files 0400, folders 0500, owned by
  `careerwright`. It replaces any earlier copy, so a restart after a key rotation copies
  afresh. Then it clears supplementary groups, sets gid, then uid, sets `HOME` the way Docker
  would, and `exec`s the command.
- `docker/postgres/entrypoint.sh` (new, mounted read-only). It does the same for the postgres
  user, then `exec`s the image's own `docker-entrypoint.sh`.
  `docker/postgres/initdb/10-roles-and-databases.sh` and `POSTGRES_PASSWORD_FILE` read the
  copies.
- `compose.yaml`: a new `x-private-files` anchor (`user: root`, the entrypoint, and a tmpfs
  at `/run/careerwright/private` with `mode=0700,size=1m,noexec,nosuid,nodev`) is merged
  into migrate, api, worker and acquisition. Postgres gets its own entrypoint, an explicit
  `command: ["postgres"]` and the same tmpfs. Every `*_PASSWORD_FILE`, `MASTER_KEY_DIR` and
  `ADZUNA_CREDENTIALS_DIR` now points at the copy. Unchanged: the bind mounts, the Compose
  secrets, which container gets which, `edge`, `web` and `auth`.
- `docs/adr/0004-…md`: the 2026-11-01 amendment (problem, decision, why, rejected options,
  consequences). The open item about Linux now points to it.
- `docs/runbook.md`: the Linux note now says how it works and what the two refusal messages
  mean.
- Tests: see below.

## Rulings
1. **Copy into memory, then drop privileges, over Compose's `uid`/`gid`/`mode` on secrets.**
   I could not prove those options work for file secrets on this Compose (v5.6.1) because
   the daemon was down. Even if they did, they cannot cover the `keys/` folder: its number
   of key versions varies, so it can't be a fixed list of secrets. So that option fixes only
   half the problem.
2. **Health checks and `docker compose exec` in the four backend containers now run as
   root.** PID 1 (Compose's init) does too. Postgres has always worked this way. The service
   process itself runs as uid 10001 with no supplementary groups. To run checks
   unprivileged, every healthcheck command would need wrapping. I judged that out of scope
   for "the smallest change". It is recorded in the ADR as a consequence.
3. **Two stack-test expectations changed, because the intended behaviour changed.**
   - The acquisition mount check now ignores tmpfs mounts. It still requires the Adzuna
     folder to be the only host mount, and read-only.
   - The worker's secret-scan positive control now also expects the private copies.
4. **Register: no row closed.** I added no rows. MODEL-05 and ACQ-05 already exist; the new
   tests carry those tags. Acceptance has not run, so nothing is marked verified.

## Checks
- TDD: `tests/domain/test_container_entrypoint.py`. RED: the module did not exist
  (ImportError). GREEN: 6 passed. It covers:
  - copies are exact, 0400 files and 0500 folders, owned by the target user
  - the keyring's owner-only check accepts the copies
  - a missing location is skipped
  - a restart drops a removed key
  - the drop order is groups, then gid, then uid, then exec, with `HOME` set
  - it refuses when not root, when the private folder is not a mount, or when no command is
    given
- New stack test: `test_each_service_runs_as_its_own_user_holding_read_only_copies_of_its_own_files`.
  For api, worker and acquisition it checks:
  - the service process (the child of PID 1) has uid 10001 and no groups
  - the private folder holds exactly that container's files, each with the right owner and
    mode
  - the host files are still owner-only

  It collects; it has not run.
- `docker compose -f compose.yaml -f compose.live.yaml config` renders offline. The anchors
  merge, with `user: root` on exactly the four backend services.
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`: rc 0. Backend 1,866 passed,
  8 skipped, 439 deselected. Vitest 468 passed (44 files). ruff, mypy, Biome, tsc and client
  drift are clean.
- **`make acceptance`, integration and stack tests: not run.** `dockerd` was not running
  (`pgrep dockerd` returned nothing, and `docker info` could not connect to the socket). I
  was not allowed to start it, so I did not take the lock. The controller needs to run
  acceptance with the build shim.

## Concerns for the controller
- Nothing here has run on Docker yet. Watch for these when acceptance runs:
  - The tmpfs option string (`mode=0700,size=1m,noexec,nosuid,nodev`) is accepted.
  - Docker's `Mounts` does not list the tmpfs, or the filtered test copes if it does.
  - Postgres's first init reads the copies.
  - Rotation restarts copy the new key.
  - `bash` exists in the postgres image. It does in Debian images, and the init script
    already uses bash.
- I left alone the unrelated change to `planning/task-6f-report.md` that I found in the
  working tree. Not mine.
- No live calls, no web requests, no secret printed. Cost $0.

## Paths a reviewer can skip
None generated or vendored.
