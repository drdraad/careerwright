# This machine: a cloud session (from 2026-11-01)

The build moved from the product owner's Mac to a Claude Code cloud container. Where any
planning file, contract or dispatch names a Mac path or branch, read it as below.

| In the files | On this machine |
|---|---|
| `/Users/darianraad/Code/careerwright` (main tree) | `/home/user/careerwright` |
| `/Users/darianraad/Code/careerwright-wt/<id>` | `/home/user/careerwright-wt/<id>` |
| branch `l0-local-release` | branch `claude/confident-ramanujan-ux3saw` (the controller's integration branch; `l0-local-release` was merged into `main` on GitHub) |
| acceptance lock `<main tree>/.superpowers/acceptance.lock` | `/home/user/careerwright/.superpowers/acceptance.lock` |

## Tooling
- Node 24 is at `/opt/node24/bin`, with pnpm 10.33.2 through corepack. Start every shell
  command that runs node or pnpm (including `make check`) with
  `export PATH=/opt/node24/bin:$PATH;`. The `/opt/node22` on the default PATH is the wrong
  version.
- Python 3.12 for the backend: `backend/.venv` (built with `uv sync --locked`).
- The container exports `ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY`. One test
  (`test_absent_credentials_list_the_adzuna_names_found_never_a_value`) reads the process
  environment, so run checks as `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`.
  Never print either value.
- No `var/` datasets (not fetched here). `make check` passes without them (controller's run,
  2026-11-01: backend 1,739 passed, Vitest 442).

## Docker
The Docker daemon is not running and no images are cached. Integration tests and
`make acceptance` cannot run until the product owner decides. Never start Docker and never
pull an image yourself. Report "integration and acceptance not run: Docker down".
