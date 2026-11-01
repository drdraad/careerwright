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
- `var/` datasets: fetched and hash-verified by the controller on 2026-11-01, after the
  product owner allowed the dataset hosts (the ledger). `make check` needs none of them.
- Playwright: the acceptance journeys run on the machine's own Chromium,
  `CAREERWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium` (opt-in in
  `apps/web/playwright.config.ts`). Never reinstall Playwright's browsers here.
- The sprint tasks file's "Environment facts" and both contracts carry these facts from
  2026-11-01; this note stays the machine's full record.

## Docker (from 2026-11-01 afternoon, the product owner's yes)
The controller starts `dockerd` in the container and builds the images with
`planning/cloud-build-images.sh` (the session proxy and its CA, build-time only; the
repository's Dockerfiles unchanged). Docker Hub is reachable. Implementers still never start
Docker, pull or build images: the controller runs integration and `make acceptance` once per
batch, under the lock. Report them as "not run: the controller runs acceptance".

## Network access (the product owner's settings, not ours)
At first `www.childline.org.uk`, `www.gov.uk`, `www.ucas.com` and the dataset hosts
(`ec.europa.eu`, `esco.ec.europa.eu`, `www.ons.gov.uk`, `huggingface.co`) were blocked. On
2026-11-01 the product owner allowed them, then widened network access for role research
(the ledger). Fetches go through the session proxy (`tools.corpus` and
`tools.live_role_research` take `--proxy`); only the controller makes them.
