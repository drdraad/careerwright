# Dependency matrix (L0)

Checked 2026-10-27 on the development machine: macOS arm64 (Apple silicon), Docker 29.1.2
with an aarch64 engine. "Verified" means executed on this machine as described. "Manifest
only" means the registry lists the platform but nothing ran on it. Change a pin only by
re-running the check named in its row.

## Runtimes and containers

| Component | Pin | Where | arm64 evidence | amd64 |
|---|---|---|---|---|
| Python | 3.12 (`requires-python >=3.12,<3.13`; `backend/.python-version`) | Host: uv-managed CPython 3.12.12. Container: `python:3.12.16-slim-bookworm@sha256:6dd8b6dab6b3adc7812bab69eca5dbdc1a5cc690ad28306d234ffb4ef8ac9753` (arm64 manifest `sha256:04b6d37c…c752`) | Verified: `uv sync --frozen --no-dev` inside the container on aarch64 installed the lock and imported the stack; psycopg used its binary implementation | Manifest only |
| PostgreSQL server | 16.15 (`postgres:16.15-bookworm@sha256:d81f7b51697014367236d07ec58b54153fc28f828b72bf247fe5c7487520bcb0`; arm64 manifest `sha256:2b429c90…e8a9`) | Container only. The host has a PostgreSQL 18.4 *client*, used only for ad hoc inspection | Verified: `postgres --version` gave 16.15 (Debian 16.15-1.pgdg12+2) on aarch64; the full DBOS integration suite ran against it | Manifest only |
| Node.js | 24.22.1 LTS (Krypton). Engine range for the web app: `>=24.11 <25` | Container: `node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205` (arm64 manifest `sha256:294d33a9…1ea2`). Host: v24.11.1 | Verified: the Firebase emulator image built and ran on it (aarch64, `node --version` v24.22.1) | Manifest only |
| pnpm | 10.33.2 | Host 10.33.2; containers use `corepack prepare pnpm@10.33.2` | Verified: installed `firebase-tools` in the arm64 image build | n/a |
| Firebase CLI / Auth emulator | `firebase-tools@15.34.1`, Auth emulator only, `demo-nessa` project | Container built from the Node image above (`backend/spikes/firebase_emulator/Dockerfile`); no Java | Verified: `{"authEmulator":{"ready":true}}`; `accounts:signUp` returned an unsigned ID token (`alg: none`, `iss: https://securetoken.google.com/demo-nessa`); `command -v java` found nothing | Not built |
| uv | 0.9.18 (host) | Host; container checks install `uv==0.9.18` | Verified | n/a |
| Docker / Compose | Docker 29.1.2, Compose v2 (`docker compose up --wait`) | Host | Verified | n/a |

Notes:

- Host Python (3.12.12) and the container (3.12.16) differ at patch level. uv 0.9.18 cannot
  download newer 3.12 builds, and upgrading uv was not in scope. Patch releases are
  ABI-compatible; the locked wheels installed on both.
- The host Node (24.11.1) is older than the container pin (24.22.1) but on the same LTS
  line. Aligning the host is optional; the engine range accepts both.
- pnpm 12.15.0 is the current upstream release (seen when corepack fetched it for a non-root
  user in the emulator image). Staying on 10.33.2 avoids an unrequested package-manager
  upgrade. The web-app task should set `packageManager: "pnpm@10.33.2"` and give the
  container user a shared `COREPACK_HOME`.

## Python packages (backend, `backend/uv.lock`, 56 packages)

Direct dependencies, pinned exactly in `backend/pyproject.toml`:

| Package | Version | Why |
|---|---|---|
| `pydantic` | 2.14.1 | validation (ARC-1) |
| `pydantic-settings` | 2.16.1 | configuration from `.env` or the environment, `SecretStr` key |
| `pydantic-ai-slim[openai,dbos]` | 2.62.0 | native Meta provider (`MetaProvider`, `OpenAIResponsesModel`), `NativeOutput`, DBOS extra |
| `dbos` | 3.3.0 | workflow engine (ADR 0002) |
| `cryptography` | 50.0.2 | AES-256-GCM sealing |
| `psycopg[binary]` | 3.3.6 | PostgreSQL driver (DBOS always uses psycopg 3) |
| `httpx2` | 2.16.0 | HTTP client used by `openai` and Pydantic AI; the spike lists models with it |
| dev: `ruff` | 0.17.3 | lint and format |
| dev: `mypy` | 2.4.0 | the single Python type checker (strict, pydantic plugin) |
| dev: `pytest` | 9.2.0 | tests |
| build: `hatchling` | 1.32.4 | build backend |

Notable transitive versions: `openai` 3.40.0, `pydantic-core` 2.50.1, `pydantic-graph`
2.62.0, `sqlalchemy` 2.1.6 (via `dbos`), `psycopg-binary` 3.3.6, `genai-prices` 0.1.13,
`tiktoken` 0.14.0, `anyio` 4.15.1, `opentelemetry-api` 1.45.1.

Release cadence risk: Pydantic AI shipped 2.59.0 to 2.62.0 between 2026-10-21 and
2026-10-27, and 2.62.0 was published on the check date. The ADR 0002 suite is the gate for
any bump. `pytest` 9.2.0 was also published that day; it is tooling only, and the suite
ran clean on it.

## Not yet introduced (owner and disposition)

These belong to the fixed stack but no task has installed them yet. Each introducing task
pins the exact version, updates the lockfile and this table, and verifies arm64. The
versions shown are the registry's latest on 2026-10-27, as candidates only. They are not
qualified pins.

| Dependency | Candidate | Owner (task / sprint) | Disposition |
|---|---|---|---|
| FastAPI | 0.162.0 | Task 3 / Sprint 1 | pin with Uvicorn 0.54.0; OpenAPI contract feeds the TS client |
| SQLAlchemy / Alembic | 2.1.6 (already locked via DBOS) / 1.20.1 | Task 3 / Sprint 1 | the SQLAlchemy pin must remain compatible with `dbos==3.3.0` |
| firebase-admin | 7.7.0 | Task 3 / Sprint 1 | token verification against the emulator; emulator acceptance only in local config |
| Hypothesis | 6.170.12 | first domain-logic task (Sprint 1+) | property tests (plan section 7) |
| Scrapling (HTTP fetch only) | 0.5 | Sprint 3 acquisition task | restricted worker without model or master key; verify licence and arm64 |
| Next.js / React / TypeScript | 16.4.3 / 19.3.1 / 7.0.2 | Task 4 / Sprint 1 | TypeScript 7 is a major release; confirm Next.js support before pinning |
| D3 | 7.9.0 | Sprint 3 map task | SVG rendering only |
| TanStack Query, Tailwind CSS, Radix | 5.105.0, 4.3.3, 1.8.1 (`radix-ui`) | Task 4 / Sprint 1 | per spec section 17 |
| Vitest, Testing Library, Playwright, axe | 5.0.5, 16.3.3, 1.64.1, 4.14.0 | Task 4 / Sprint 1 | Playwright browsers pinned per environment |
| Storybook | 10.6.5 | Task 4 / Sprint 1 | design-system states |
| JS lint/format (one toolchain) | Biome 2.6.3 or ESLint 10.13.0 | Task 4 / Sprint 1 | choose one; record in an ADR |
| OpenAPI TS generator | `openapi-typescript` 7.13.0 or `@hey-api/openapi-ts` 0.99.0 | Task 3/4 / Sprint 1 | choose one; enums must come from the contract (constraint 10) |
| ESCO / ASHE data releases | n/a | Sprint 2 / 5 data tasks | pinned URL and hash; fetched by `make setup` (R7) |
| Adzuna API | n/a | Sprint 3 | unverified: no credentials (R4) |

## How these were checked

```bash
docker buildx imagetools inspect postgres:16.15-bookworm      # also python, node (digests)
docker run --rm postgres:16.15-bookworm@sha256:d81f… sh -c 'postgres --version; uname -m'
docker run --rm -v "$PWD/backend":/src:ro python:3.12.16-slim-bookworm@sha256:6dd8… \
  sh -c 'pip install uv==0.9.18 && cp -r /src /tmp/b && cd /tmp/b && uv sync --frozen --no-dev && …'
docker build -t nessa-spike/firebase-auth-emulator:15.34.1 backend/spikes/firebase_emulator
uv run pytest -m integration spikes/durable -v                # PostgreSQL 16.15 + DBOS 3.3.0
```

The spike's containers, volume and emulator image were removed after the checks. The
pulled base images remain in the local Docker cache.
