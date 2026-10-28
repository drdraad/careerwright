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
| pnpm | 10.33.2 | Host 10.33.2; containers use `corepack prepare pnpm@10.33.2` | Verified: installed `firebase-tools` from the lockfile in the arm64 image build; the image starts healthy with no network (`--network none`) | n/a |
| Firebase CLI / Auth emulator | `firebase-tools@15.34.1`, Auth emulator only, `demo-nessa` project | Container built from the Node image above (`docker/auth/Dockerfile` since Task 3; it imports the committed deterministic seed on every start). `firebase-tools` and its 575 transitive packages install from the committed `docker/auth/package.json` and `pnpm-lock.yaml` with `pnpm install --frozen-lockfile --prod` (GC2; since the Task 3 fix round) | Verified: `{"authEmulator":{"ready":true}}`; `accounts:signUp` returned an unsigned ID token (`alg: none`, `iss: https://securetoken.google.com/demo-nessa`); `command -v java` found nothing. Since Task 3 it runs on the internal Compose network and the edge relays it to `127.0.0.1:59099`; `firebase.json` binds `0.0.0.0` inside the container | Not built |
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
| `httpx2` | 2.16.0 | HTTP client used by `openai`, Pydantic AI and Starlette's test client |
| `sqlalchemy` | 2.1.6 | engines and transactions (Task 3; the version `dbos==3.3.0` already locked) |
| `alembic` | 1.20.1 | forward-only application migrations (Task 3) |
| `fastapi` | 0.162.0 | the API and its OpenAPI contract (Task 3) |
| `uvicorn` | 0.54.0 | ASGI server for the API container (Task 3) |
| `firebase-admin` | 7.7.0 | ID-token verification with the revocation check, against the Auth emulator only (Task 3, ADR 0004) |
| dev: `ruff` | 0.17.3 | lint and format |
| dev: `mypy` | 2.4.0 | the single Python type checker (strict, pydantic plugin) |
| dev: `pytest` | 9.2.0 | tests |
| dev: `hypothesis` | 6.170.12 | property tests (plan section 7; Task 3) |
| build: `hatchling` | 1.32.4 | build backend |

Since Task 3 the lock holds 88 packages. Notable transitive versions: `openai` 3.40.0,
`pydantic-core` 2.50.1, `pydantic-graph` 2.62.0, `psycopg-binary` 3.3.6, `genai-prices`
0.1.13, `tiktoken` 0.14.0, `anyio` 4.15.1, `opentelemetry-api` 1.45.1, `starlette` 1.10.0,
`mako` 1.4.3 (Alembic). `firebase-admin` brings the Google client stack (`google-api-core`
2.43.0, `google-cloud-firestore` 2.34.1, `google-cloud-storage` 3.17.1, `grpcio` 1.85.0,
`pyjwt` 2.15.1, `httpx` 0.28.1); only `firebase_admin.auth` is used, and in emulator mode it
contacts nothing but the emulator. All of it installed and ran in the arm64 backend image
(`make acceptance`, 2026-10-28). `make check` refuses excluded technologies found in the lock
(ARC1-01).

Licences of `firebase-admin` 7.7.0 and the 34 packages in its dependency tree (some shared
with other dependencies), from each installed package's metadata (2026-10-28): Apache-2.0
for `firebase-admin` and the Google stack
(`google-api-core`, `google-auth`, `google-cloud-core`, `google-cloud-firestore`,
`google-cloud-storage`, `google-crc32c`, `google-resumable-media`, `googleapis-common-protos`,
`proto-plus`, `grpcio`, `grpcio-status`), and for `cachecontrol`, `msgpack`, `requests` and
`opentelemetry-api`; BSD-3-Clause for `protobuf`, `httpx`, `httpcore`, `idna` and
`pycparser`; BSD-2-Clause for `pyasn1` (`pyasn1-modules`: BSD); MIT for `pyjwt`, `anyio`,
`charset-normalizer`, `h11`, `h2`, `hpack`, `hyperframe` and `urllib3`; MIT-0 for `cffi`;
Apache-2.0 OR BSD-3-Clause for `cryptography`; PSF-2.0 for `typing-extensions`; MPL-2.0 for
`certifi` (file-level copyleft; used unmodified, so it adds no obligation beyond keeping its
notice). All are permissive or weak copyleft and compatible with local use. Not a legal
review (the rights review is a human gate).

Release cadence risk: Pydantic AI shipped 2.59.0 to 2.62.0 between 2026-10-21 and
2026-10-27, and 2.62.0 was published on the check date. The ADR 0002 suite is the gate for
any bump. `pytest` 9.2.0 was also published that day; it is tooling only, and the suite
ran clean on it.

## Design-reference tooling (`docs/design/pnpm-lock.yaml`, dev only)

Added in Task 2 to measure and capture the Sprint 0 design references. It is not part of
the application and ships nothing.

| Package | Version | Why | arm64 evidence |
|---|---|---|---|
| `playwright` | 1.64.1 (published 2026-10-14), Chromium build 1248 (Chrome for Testing 156.0.8078.4) | screenshots at 1440×900 and 390×844 | Verified: 18 captures (`docs/design/screenshots/checks.md`) |
| `axe-core` | 4.14.0 (published 2026-10-05), MPL-2.0 | automated WCAG A/AA checks on each capture | Verified: same run |

The web app (Task 4) pins its own copies in `apps/web`: axe-core 4.14.0 (the same) and
`@playwright/test` 1.64.0, not 1.64.1, because 1.64.1 was under 14 days old when the web
app was pinned. Both releases use the same Chromium build (1248, 156.0.8078.4, checked in
each package's `browsers.json`), so one browser download serves both.

## Web app (`apps/web/pnpm-lock.yaml`, Task 4)

Installed with pnpm 10.33.2 from the committed lockfile (`pnpm install --frozen-lockfile`).
`apps/web/pnpm-workspace.yaml` enforces `minimumReleaseAge: 20160` (14 days) for every
resolved version, direct or transitive. Decisions: ADR 0005. Publish dates are from the npm
registry, checked 2026-10-28.

| Package | Version | Published | Licence | Why |
|---|---|---|---|---|
| `next` | 16.4.1 | 2026-10-14 | MIT | the web framework (spec ARC-1). **Age exception**, below |
| `react`, `react-dom` | 19.3.0 | 2026-09-09 | MIT | UI |
| `@tanstack/react-query` | 5.104.2 | 2026-10-11 | MIT | server state (spec ARC-1) |
| `@radix-ui/react-dialog`, `@radix-ui/react-popover` | 1.3.1 | 2026-10-12 | MIT | the evidence drawer, chapter menu and account menu (spec: Radix controls). Single primitives rather than the 55-package `radix-ui` bundle |
| `@firebase/app`, `@firebase/auth` | 0.16.3, 1.13.7 | 2026-10-07 | Apache-2.0 | emulator sign-in. These are the versions `firebase` 13.0.0 uses; the umbrella package is not used because it also installs Firestore's gRPC stack |
| dev: `typescript` | 6.0.3 | 2026-04-16 | Apache-2.0 | strict type checking. Not 7.0.2: TypeScript 7 has no JavaScript compiler API, which the client generator needs |
| dev: `@biomejs/biome` | 2.5.15 | 2026-09-30 | MIT OR Apache-2.0 | the one lint and format toolchain (ADR 0005) |
| dev: `@hey-api/openapi-ts` | 0.99.0 | 2026-06-22 | MIT | generates the TypeScript client from the OpenAPI document (ADR 0005) |
| dev: `tailwindcss`, `@tailwindcss/postcss` | 4.3.3 | 2026-07-16 | MIT | utilities on a theme rebuilt from the design tokens |
| dev: `storybook`, `@storybook/nextjs-vite`, `@storybook/addon-a11y` | 10.6.2 | 2026-10-12 | MIT | component states (UI-04) |
| dev: `vite` | 8.3.4 | 2026-10-08 | MIT | build tool for Vitest and Storybook (peer) |
| dev: `vitest` | 5.0.4 | 2026-10-12 | MIT | unit and component tests |
| dev: `jsdom` | 30.1.2 | 2026-10-04 | MIT | the DOM for component tests |
| dev: `@testing-library/react`, `/dom`, `/user-event`, `/jest-dom` | 16.3.3, 10.4.2, 14.6.8, 7.0.1 | 2026-08-27, 09-13, 10-13, 08-09 | MIT | component tests |
| dev: `@playwright/test` | 1.64.0 | 2026-10-07 | Apache-2.0 | browser journeys and visual checks (Chromium 1248) |
| dev: `axe-core` | 4.14.0 | 2026-10-05 | MPL-2.0 | automated WCAG checks, as in the design tooling |
| dev: `@types/node`, `@types/react`, `@types/react-dom` | 24.19.2, 19.3.0, 19.3.0 | 2026-10-09, 09-09, 09-09 | MIT | types (Node 24 runtime) |

Lockfile: 438 packages. Licences across the whole tree (`pnpm licenses list`, 2026-10-28):
MIT (271), Apache-2.0 (16), ISC (11), BlueOak-1.0.0 (6), BSD-2-Clause (5), BSD-3-Clause
(3), MPL-2.0 (3: `axe-core`, `lightningcss` and its arm64 binary, both build or test tools,
used unmodified), MIT OR Apache-2.0 (2), MIT-0 (2), CC-BY-4.0 (1: `caniuse-lite`, browser
data used by the build), CC0-1.0 (1), Python-2.0 (1), 0BSD (1). All are permissive or weak
copyleft and compatible with local use. Not a legal review.

Exceptions and accepted advisories (`pnpm audit`, 2026-10-28):

- **`next` 16.4.1 was 13.5 days old when pinned** (published 2026-10-14T17:43Z). Every 16.x up
  to 16.4.0 is affected by GHSA-2464-fhr4-w9xw and GHSA-673q-mjm6-r5xr (critical, remote
  code execution) and GHSA-p3m5-59mp-jv5r (high). `minimumReleaseAgeExclude` names
  `next@16.4.1` and its `@next/*` 16.4.1 packages only. It reaches 14 days on
  2026-10-28T17:43Z.
- `sharp` (Next.js's optional image optimiser, with LGPL libvips binaries) is not installed
  (`ignoredOptionalDependencies`). The app serves no optimised images (`images.unoptimized`).
- `js-yaml` is overridden from 4.2.0 to 4.3.2 (2026-08-26) for three CPU-exhaustion
  advisories. It is used by the client generator only.
- **Accepted, dev only:** `undici` 8.11.2 through `jsdom` (8 advisories: 4 high and 4
  moderate, fixed in 8.12.2, which was published 2026-10-15 and was under 14 days old). It is
  jsdom's network layer in unit tests, which make no network request, and it is not in the
  web image's runtime. Recheck it when `jsdom` is bumped.
- Install scripts stay off (`ignoredBuiltDependencies`: `esbuild`, whose binary comes as an
  optional platform package, and `@firebase/util`, whose script only probes the environment).

Runtime image: `nessa-l0/web:local`, built from `apps/web/Dockerfile` on
`node:24.22.1-bookworm-slim@sha256:55fb5f5a…d205` (the same digest as the emulator). It runs
the Next.js standalone server as the `node` user. Verified on arm64 by `make acceptance`
(2026-10-28); amd64 is not built.

## Not yet introduced (owner and disposition)

These belong to the fixed stack but no task has installed them yet. Each introducing task
pins the exact version, updates the lockfile and this table, and verifies arm64. The
versions shown are the registry's latest on 2026-10-27, as candidates only. They are not
qualified pins.

| Dependency | Candidate | Owner (task / sprint) | Disposition |
|---|---|---|---|
| Scrapling (HTTP fetch only) | 0.5 | Sprint 3 acquisition task | restricted worker without model or master key; verify licence and arm64 |
| D3 | 7.9.0 | Sprint 3 map task | SVG rendering only; add to `apps/web` with its own ADR note |
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

Since Task 3 (the spike paths above are historical; see git `ff449da`): `make setup` builds
`nessa-l0/backend:local` and `nessa-l0/auth-emulator:15.34.1` from the locked inputs, and
`make acceptance` runs every container on arm64.

The spike's containers, volume and emulator image were removed after the checks. The
pulled base images remain in the local Docker cache.
