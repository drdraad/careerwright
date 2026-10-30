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
| Firebase CLI / Auth emulator | `firebase-tools@15.34.1`, Auth emulator only, `demo-careerwright` project | Container built from the Node image above (`docker/auth/Dockerfile` since Task 3; it imports the committed deterministic seed on every start). `firebase-tools` and its 575 transitive packages install from the committed `docker/auth/package.json` and `pnpm-lock.yaml` with `pnpm install --frozen-lockfile --prod` (GC2; since the Task 3 fix round) | Verified: `{"authEmulator":{"ready":true}}`; `accounts:signUp` returned an unsigned ID token (`alg: none`, `iss: https://securetoken.google.com/demo-careerwright`); `command -v java` found nothing. Since Task 3 it runs on the internal Compose network and the edge relays it to `127.0.0.1:59099`; `firebase.json` binds `0.0.0.0` inside the container | Not built |
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
| `scrapling` | 0.4.15 (2026-08-23) | the one scraper (spec section 6), used as a parser only: `scrapling.parser.Selector` reads pages' JSON-LD. Its HTTP fetcher imports Playwright, Patchright and browserforge, which the backend excludes, so the `fetchers` extra is not installed and retrieval is Careerwright's own guarded client on `httpcore2` (Task 7A, ADR 0009 decision 2). 0.5 (2026-10-17) was under 14 days old and imports the same browser stack |
| dev: `ruff` | 0.17.3 | lint and format |
| dev: `mypy` | 2.4.0 | the single Python type checker (strict, pydantic plugin) |
| dev: `pytest` | 9.2.0 | tests |
| dev: `hypothesis` | 6.170.12 | property tests (plan section 7; Task 3) |
| build: `hatchling` | 1.32.4 | build backend |

Task 7A added `scrapling` 0.4.15 and its five dependencies, each published more than 14 days
before 2026-10-28: `lxml` 6.1.3 (2026-09-02, BSD-3-Clause), `cssselect` 1.6.0 (2026-10-09,
BSD-3-Clause), `orjson` 3.13.0 (2026-10-07, MPL-2.0 AND (Apache-2.0 OR MIT)), `tld` 0.13.2
(2026-03-06, MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later, used under MPL-1.1) and `w3lib`
2.5.0 (2026-09-30, BSD-3-Clause); the lock now holds 94 packages. `scrapling` is BSD-3-Clause.
MPL files are used unmodified, so they add no obligation beyond keeping their notices (not a
legal review). lxml 6.1 deprecates an `HTMLParser` option Scrapling 0.4.15 still passes as a
no-op; `backend/pyproject.toml` ignores that one `DeprecationWarning` in tests, which
otherwise turn warnings into errors. `httpcore2` and `certifi` were already locked (through
`httpx2` and `httpx`) and are now imported directly by `careerwright.evidence.fetcher`.

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
| `playwright` | 1.64.1 (published 2026-10-14), Chromium build 1248 (Chrome for Testing 156.0.8078.4) | screenshots at 1440×900, 768×1024 and 390×844 | Verified: 28 captures of the world's references (Task W2, `docs/design/screenshots/checks.md`) |
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
| `next` | 16.4.1 | 2026-10-14 | MIT | the web framework (spec ARC-1). Fixes GHSA-2464-fhr4-w9xw and GHSA-673q-mjm6-r5xr (critical) and GHSA-p3m5-59mp-jv5r (high), which affect every older 16.x |
| `react`, `react-dom` | 19.3.0 | 2026-09-09 | MIT | UI |
| `@tanstack/react-query` | 5.104.2 | 2026-10-11 | MIT | server state (spec ARC-1) |
| `@radix-ui/react-dialog`, `@radix-ui/react-popover` | 1.3.1 | 2026-10-12 | MIT | the evidence drawer, chapter menu and account menu (spec: Radix controls). Single primitives rather than the 55-package `radix-ui` bundle |
| `@firebase/app`, `@firebase/auth` | 0.16.3, 1.13.7 | 2026-10-07 | Apache-2.0 | emulator sign-in. These are the versions `firebase` 13.0.0 uses; the umbrella package is not used because it also installs Firestore's gRPC stack |
| `three` | 0.186.1 | 2026-09-24 | MIT | the world layer: one WebGL2 canvas behind every chapter (Task W2; ADR 0014 decision 2, chosen by the world spike's library comparison). No dependencies of its own |
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
| dev: `@types/three` | 0.186.0 | 2026-09-11 | MIT | three.js's types (Task W2). It brings six type-only or unused transitive packages: `@types/webxr` 0.5.24 (2025-09-29, MIT), `@types/stats.js` 0.17.4 (2025-05-05, MIT), `@tweenjs/tween.js` 23.1.3 (2024-07-25, MIT), `fflate` 0.8.3 (2026-05-16, MIT), `meshoptimizer` 1.1.1 (2026-04-15, MIT) and `@dimforge/rapier3d-compat` 0.12.0 (2024-01-28, Apache-2.0); none is imported by the app or shipped |

Task W2 (2026-10-30) added `three` and `@types/three` with its six transitive packages, each
published more than 14 days before (pnpm's `minimumReleaseAge` enforced it on install). The
display face Outfit 1.100 (OFL-1.1) is a font file, not a package: it is pinned to a
`google/fonts` commit and hashed in `docs/design/fonts/README.md`, and mirrored byte for byte
in `apps/web/src/design/fonts/`.

Lockfile: 438 packages before Task W2. Licences across the whole tree (`pnpm licenses list`, 2026-10-28):
MIT (271), Apache-2.0 (16), ISC (11), BlueOak-1.0.0 (6), BSD-2-Clause (5), BSD-3-Clause
(3), MPL-2.0 (3: `axe-core`, `lightningcss` and its arm64 binary, both build or test tools,
used unmodified), MIT OR Apache-2.0 (2), MIT-0 (2), CC-BY-4.0 (1: `caniuse-lite`, browser
data used by the build), CC0-1.0 (1), Python-2.0 (1), 0BSD (1). All are permissive or weak
copyleft and compatible with local use. Not a legal review.

Exceptions and accepted advisories (`pnpm audit`, 2026-10-28). No age exception remains: the
provisional one for `next` 16.4.1 (pinned at 13.5 days old) was removed in Task 6c once it
was 14 days old (ADR 0005 decision 1).

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

Runtime image: `careerwright-l0/web:local`, built from `apps/web/Dockerfile` on
`node:24.22.1-bookworm-slim@sha256:55fb5f5a…d205` (the same digest as the emulator). It runs
the Next.js standalone server as the `node` user. Verified on arm64 by `make acceptance`
(2026-10-28); amd64 is not built.

## Reference data (Task 5)

Large third-party datasets are not committed (ruling R7): `make setup` fetches each one into
the gitignored `var/datasets/` and refuses it unless its size and SHA-256 match the pin
(`backend/tools/datasets.py`); `setup-database` checks the file again before it imports it.

| Dataset | Pin | Source | Licence and attribution | Import |
|---|---|---|---|---|
| ESCO v1.2.1, classification, English, CSV | `esco-v1.2.1-classification-en-csv.zip`, 10,045,670 bytes, SHA-256 `f9761b0b52be1828b38a3e5e0ae59a93a7b0ce358bc800f52f57a8b002adeb3e` (`careerwright.catalogue.esco.ESCO_RELEASE`; server `Last-Modified` 2025-12-16) | https://ec.europa.eu/esco/download/ESCO%20dataset%20-%20v1.2.1%20-%20classification%20-%20en%20-%20csv.zip, the file the ESCO download page (https://esco.ec.europa.eu/en/use-esco/download) links for that choice; fetched 2026-10-28 | Commission Decision 2011/833/EU on the reuse of Commission documents: free reuse on two conditions (https://esco.ec.europa.eu/en/about-esco/faq, checked 2026-10-28): the service shows "This service uses the ESCO classification of the European Commission." (the API returns it with every release and occupation), and any modified or adapted version is marked as such: the product import is one (6 of the 19 CSV files, labels de-duplicated, repeated rows merged; transformation `careerwright-esco-import-1`), and its manifest, every release in the API and every occupation detail carry an `adaptation` statement saying so (`careerwright.catalogue.esco.ADAPTATION`); the test sample is marked too. This reading is not settled: it is on the human rights-review checklist (H-11) | 3,039 occupations (33,498 labels), 13,939 skills (100,886 labels), 619 ISCO-08 groups, 126,051 occupation-skill and 5,818 skill-skill relations, 3,039 broader links. 25 concept rows the release repeats with only `modifiedDate` changed are imported once and counted in the manifest. About 6 s on this machine |
| ESCO test sample | `fixtures/esco-sample/esco-v1.2.1-en-csv-sample.zip`, 76,049 bytes, SHA-256 `747c5638653e0594c0ae4210db1ee0c90eccb5c872f356fdfa36116bb56f955d` (committed) | Built from the release above by `backend/tools/esco_sample.py` (deterministic) | As above; a modified (reduced) version, labelled `sample` in the database and the API | 30 occupations, 200 skills; tests only |
| English cities | 55 cities in `careerwright.catalogue.places` | GOV.UK "List of cities" (Cabinet Office), https://www.gov.uk/government/publications/list-of-cities/list-of-cities-html, retrieved 2026-10-28, page SHA-256 `7da9d661…7afe` | Open Government Licence v3.0 | Committed as code (55 names, aliases, ONS regions) |

If the ESCO download cannot be automated (the publisher changes its URLs), the manual step
is in `docs/runbook.md`; the hash check still applies. A different release needs a new pin,
a re-run of `make acceptance` (the full-release test checks counts) and a reviewed migration:
the import refuses to replace a release already held.

## Reference data (Task 7, slice B; ADR 0010)

Pinned, fetched and verified the same way (`careerwright.catalogue.reference.DATASETS`), imported
by `setup-database` after ESCO into native-code tables (migration 0027), each recorded in
`reference_releases`. All were fetched from these URLs on 2026-10-29. Licence readings are
the implementing agent's, recorded for the product owner (R6); ONS's falls under session 1's
policy (line A2). The tests import labelled synthetic samples in the same layouts
(`backend/tests/support/reference_data.py`), never these files.

| Dataset | Pin | Source | Licence and attribution | Import |
|---|---|---|---|---|
| ONS ASHE Table 15 (region by occupation, four-digit SOC 2020), 2026 provisional | `ons-ashe-table15-2026-provisional.zip`, 67,460,310 bytes, SHA-256 `fefd20c5a746a9ad6a563a0edf6c3ac204b093c9d23a500b7d4234122595f081` (`careerwright.catalogue.ashe.ASHE_RELEASE`) | https://www.ons.gov.uk/file?uri=/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/regionbyoccupation4digitsoc2010ashetable15/2026provisional/ashetable152026provisional.zip (the dataset page's 2026 provisional edition) | Open Government Licence v3.0; "Source: Office for National Statistics, Annual Survey of Hours and Earnings, licensed under the Open Government Licence v3.0." | Tables 15.1, 15.5 and 15.7 with their CV tables, the Full-Time sheet: 13,596 estimates (412 unit groups, 11 work regions, 3 periods); 8,505 with the median withheld (null with ONS's marker) |
| ONS SOC 2020 Volume 2: the coding index, version 14 | `ons-soc2020-volume2-coding-index-v14.xlsx`, 3,717,451 bytes, SHA-256 `59d3ec71d0e9eef2a27d7d0f4720f5c4bd584b61dc6902cc33dd8ee2ced40b9a` (`careerwright.catalogue.soc.SOC_INDEX_RELEASE`) | https://www.ons.gov.uk/file?uri=/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume2codingrulesandconventions/soc2020volume2thecodingindexexcel20260827v2.xlsx | Open Government Licence v3.0 (the page footer); ONS attribution | 412 unit groups; 32,435 coded index entries with their ISCO-08 codes; 235 without a code counted |
| ILO-NASK refined global index of occupational exposure to generative AI (ILO Working Paper 140, 2025), occupation scores | `ilo-genai-exposure-2025-final-scores.xlsx`, 2,598,951 bytes, SHA-256 `c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a` (`careerwright.catalogue.ai_evidence.ILO_RELEASE`) | https://raw.githubusercontent.com/pgmyrek/2025_GenAI_scores_ISCO08/ce5fc25c2a0db2757c5bfa797c4cfc8b408431ea/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx, the lead author's repository (the ILO page, https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure, offers only the paper) | CC BY 4.0 (the repository's LICENSE and README): cite Gmyrek et al. 2025, © ILO, doi 10.54394/HETP0387, with the ILO's adaptation disclaimer (`ILO_ATTRIBUTION`) | 427 ISCO-08 unit groups (3,265 task rows): mean and SD of the 2025 task scores and the gradient |
| Anthropic Economic Index, release 2025-03-27, `task_pct_v2.csv` | `anthropic-economic-index-2025-03-27-task-pct-v2.csv`, 435,372 bytes, SHA-256 `0c20f184cd4a1e3d8ef3d77f500b32b62431ce61a3c2f133c3af7fa8429f97db` | https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/4e5f69fab13a9c3f7d0dcc31a6f893a9818738f6/release_2025_03_27/task_pct_v2.csv (dataset commit `4e5f69f`) | "Data released under CC-BY" (the dataset README; no version stated); attribution to the release and Handa et al. 2025 (arXiv:2503.04761) | 3,364 tasks' shares (the release's "none" row is not a task) |
| Anthropic Economic Index, release 2025-03-27, `onet_task_statements.csv` | `anthropic-economic-index-2025-03-27-onet-task-statements.csv`, 3,592,256 bytes, SHA-256 `82e4c418dc08475ef1263ad1e8c66ffa3357291370cd35ee1065ecea590597ec` | the same release | As above; O*NET content of USDOL/ETA under CC BY 4.0, "O*NET is a trademark of USDOL/ETA" | 19,530 tasks of 974 O*NET-SOC 2019 occupations |
| ESCO to O*NET crosswalk, version 1 (September 2022) | `esco-onet-crosswalk-v1-2022-09.csv`, 2,986,823 bytes, SHA-256 `82179a0a3340da97b63df90134d8d941ec3c2c478334d855b69e4dd57a91b620` | https://esco.ec.europa.eu/system/files/2023-08/ONET_%28Occupations%29_0_updated.csv (linked from https://esco.ec.europa.eu/en/use-esco/other-crosswalks) | Commission Decision 2011/833/EU with the ESCO acknowledgement; its O*NET titles under CC BY 4.0 | 4,253 rows (O*NET-SOC 2019 to ESCO v1.1.0); bridge to v1.2.1 by URI: 3 rows name occupations v1.2.1 lacks, 235 O*NET codes have no task in the release, 43 rows name an ISCO group |

The import was not timed on its own; the whole `test_reference_data.py` run, which also
starts its database and imports the full ESCO release, took 38 s on this machine.

## Not yet introduced (owner and disposition)

These belong to the fixed stack but no task has installed them yet. Each introducing task
pins the exact version, updates the lockfile and this table, and verifies arm64. The
versions shown are the registry's latest on 2026-10-27, as candidates only. They are not
qualified pins.

| Dependency | Candidate | Owner (task / sprint) | Disposition |
|---|---|---|---|
| Scrapling (HTTP fetch only) | 0.5 | Sprint 3 acquisition task | restricted worker without model or master key; verify licence and arm64 |
| D3 | 7.9.0 | Sprint 3 map task | SVG rendering only; add to `apps/web` with its own ADR note |
| Adzuna API | n/a | Sprint 3 | qualified on the free tier on 2026-10-29 by `make live-adzuna` (two requests, both 200; ledger rows 32–33, $0), credentials read from `.env` as `ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY` (R4; ADR 0009) |

## How these were checked

```bash
docker buildx imagetools inspect postgres:16.15-bookworm      # also python, node (digests)
docker run --rm postgres:16.15-bookworm@sha256:d81f… sh -c 'postgres --version; uname -m'
docker run --rm -v "$PWD/backend":/src:ro python:3.12.16-slim-bookworm@sha256:6dd8… \
  sh -c 'pip install uv==0.9.18 && cp -r /src /tmp/b && cd /tmp/b && uv sync --frozen --no-dev && …'
docker build -t careerwright-spike/firebase-auth-emulator:15.34.1 backend/spikes/firebase_emulator
uv run pytest -m integration spikes/durable -v                # PostgreSQL 16.15 + DBOS 3.3.0
```

Since Task 3 (the spike paths above are historical; see git `ff449da`): `make setup` builds
`careerwright-l0/backend:local` and `careerwright-l0/auth-emulator:15.34.1` from the locked inputs, and
`make acceptance` runs every container on arm64.

The spike's containers, volume and emulator image were removed after the checks. The
pulled base images remain in the local Docker cache.
