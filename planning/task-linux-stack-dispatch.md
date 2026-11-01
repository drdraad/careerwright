# The local stack on a Linux Docker host (main tree)

The product owner's yes (1 November 2026). `make acceptance` has only ever passed on Docker
Desktop for Mac. On a Linux Docker host (this cloud machine, and any future CI) every
integration and stack test fails at setup: "password authentication failed for user
careerwright_migrator".

Cause, verified by the controller: compose file secrets (`compose.yaml:212-217`) are bind
mounts of `CAREERWRIGHT_HOME/secrets/*`, created root-owned (or owner-owned) mode 0600 by
`tools/localenv.py`, which `check_permissions` enforces. On Linux the mount keeps the host
owner and mode, so the postgres init script (`docker/postgres/initdb/10-roles-and-databases.sh`,
running as uid 999) can't `cat /run/secrets/pg_migrator`; the api (uid 10001), worker, migrate
and acquisition containers would fail the same way for their own secrets and `keys/`. Docker
Desktop hides host ownership, so the Mac never saw it.

## Your tree
Main tree `/home/user/careerwright`, branch `claude/confident-ramanujan-ux3saw` (head
185894d). Explicit pathspecs. Beside you in a worktree: the fetch-proxy task
(`careerwright/evidence/fetcher.py`, `tools/`): never touch those files.

## Read first
`planning/env-cloud.md`, `planning/implementer-contract.md`, `compose.yaml`,
`compose.live.yaml`, `docker/postgres/initdb/`, `backend/Dockerfile`, `apps/web/Dockerfile`,
`docker/auth/Dockerfile`, `backend/tools/localenv.py`, `backend/tools/stack.py`,
`backend/tests/support/infra.py`, the stack tests (`backend/tests/stack/`), ADR 0004.

## Build
The smallest change that lets every container read exactly its own secrets and keys on a
Linux host, while:
1. On the host, secrets and keys stay owner-only (0600 files, 0700 directories);
   `check_permissions` keeps its meaning. Nothing becomes world-readable anywhere.
2. Each container still sees only the secrets it is given today (the stack tests that check
   the acquisition worker holds no database secret, master key or model key must still pass).
3. Docker Desktop on the Mac keeps working unchanged.
4. No secret value is printed, logged, passed as an argument or put in an image layer.
Your call how (for example: a root-run entrypoint step that copies a secret to a
container-private tmpfs owned by the service user and then drops privileges; compose's
secret `uid`/`gid`/`mode` if this Compose version honours them for file secrets — prove it;
or another way). State the choice and why in an ADR 0004 amendment.

## Checks (Docker is running; the controller started it)
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH).
- You may run integration and stack tests and `make acceptance` here, but only under the
  lock, in one guarded command, with the controller's build shim on PATH (it builds images
  through the session proxy):
  `export PATH=/tmp/ccr-shim:/opt/node24/bin:$PATH; L=/home/user/careerwright/.superpowers/acceptance.lock; mkdir $L && { env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make acceptance > /tmp/acc-linux.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
  Run it once at the end; a flaky failure is re-run once. Report the counts and every failure
  that is not about secrets (those are findings for the controller, not yours to fix).
- Never `docker system prune`, never remove volumes or containers of other projects.

## Hard rules
Edit/Write for every source change. No web requests, no live calls, no subagents, never read
`.env` or print an environment value or secret, never push, pnpm only. The register last.
Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/home/user/careerwright/planning/task-linux-stack-report.md`; reply with the short contract.
