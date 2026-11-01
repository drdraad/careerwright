# Careerwright L0 command contract (development plan section 2). Run from the repository root.
#   make setup              check prerequisites, install locked dependencies, create local config,
#                           fetch and verify the pinned ESCO release, build images
#   make dev                start the live stack (the worker may reach Meta), migrate, seed, print URLs
#   make demo               start the stack with no route out of the machine (fixture workspace)
#   make check              format, lint, types and fast deterministic tests, backend and web (no Docker)
#   make acceptance         full offline suite against real PostgreSQL 16, DBOS and the Auth emulator,
#                           then the Storybook build and the browser journeys on their own stack
#   make live-smoke         budget-capped real Meta smoke on the test model; PRODUCTION=1 (exactly)
#                           qualifies the production model; INTERVIEW=1 (exactly) runs one
#                           interview turn and confirms its proposals instead of a connection check;
#                           SEARCH=1 runs one source search (Meta web search; scope live-search);
#                           SEARCH_BOUND=1 asks one in-process search for max_tool_calls 1;
#                           WONDER=1 makes Muse Wonder's two qualification calls in process
#                           (scope wonder-qualification, $0.50 in all with live-eval WONDER=1)
#   make live-eval          budget-capped live run of the representative evaluation cases (at most
#                           6) on the test model; CASES=INT-01,DSC-01 runs a chosen subset;
#                           WONDER=1 runs them on Muse Wonder (scope wonder-qualification)
#   make live-adzuna        two real Adzuna search requests (free tier; at most 10 in its scope),
#                           credentials read from .env in code, each request ledgered at $0
#   make live-extract       one in-process page extraction of the synthetic fixture page on the
#                           test model (scope live-extract: at most 3 requests, $0.30), ledgered
#   make live-role-research one in-process "Research this role" on the test model: one search
#                           told only a synthetic title (TITLE=...) and England, then up to five
#                           of its pages read through the guarded fetcher and checked by code
#                           (scope live-role-research: at most 3 requests, $0.10), ledgered
#   make session           the product owner's live session: `make dev`'s stack with Muse Wonder
#                           as the production model (synthetic workspaces keep the test model),
#                           and caps per workspace on each live workspace not marked synthetic
#                           ($0.75 a run, $5 per workspace; it prints the session's total);
#                           a running API and worker restart, and a run in flight restarts (its
#                           call counted at its full reservation); no data is reset
#   make session-ledger     with the stack up: copy every model attempt in its database (counts,
#                           cost and state, never content) into docs/evidence/live-usage.*,
#                           scope live-app-<date>
#   make stop               stop every service, bounded; persisted work is kept
#   make reset-demo         recreate the named fixture workspace only
#   make rotate-master-key  add a master key version, reload it, reseal every sealed record
#   make reseal             reseal every sealed record under the current master key
#   make spike-world        the throwaway spike of three world directions (session W1), opened in
#                           Google Chrome at http://127.0.0.1:53300; made-up data, not the product
# Local secrets and master keys live in CAREERWRIGHT_HOME (default ~/.careerwright/l0), never in the repository.

UV := uv run --locked
BACKEND := cd backend &&
WEB := cd apps/web &&
# Next.js and Storybook send anonymous usage data unless told not to (SEC-04: no telemetry).
export NEXT_TELEMETRY_DISABLED := 1
export STORYBOOK_DISABLE_TELEMETRY := 1

.PHONY: setup dev demo check acceptance live-smoke live-eval live-adzuna live-extract live-role-research session session-ledger stop reset-demo status rotate-master-key reseal spike-world

setup:
	$(BACKEND) uv python install 3.12 && uv sync --locked
	cd docs/design && pnpm install --frozen-lockfile && pnpm exec playwright install chromium
	$(WEB) pnpm install --frozen-lockfile && pnpm exec playwright install chromium
	$(BACKEND) $(UV) python -m tools.setup

dev:
	$(BACKEND) $(UV) python -m tools.stack dev

demo:
	$(BACKEND) $(UV) python -m tools.stack demo

check:
	$(BACKEND) $(UV) ruff format --check src tests tools
	$(BACKEND) $(UV) ruff check src tests tools
	$(BACKEND) $(UV) mypy
	$(BACKEND) $(UV) pytest
	$(BACKEND) $(UV) python -I ../fixtures/m0/validate_fixtures.py
	$(WEB) pnpm run check

acceptance:
	$(BACKEND) $(UV) pytest -m "integration or stack or owner_commands"
	$(WEB) pnpm run build-storybook && pnpm run e2e

# Only PRODUCTION=1 opts in to the production model; any other value (0, false, no) does not.
live-smoke:
	$(BACKEND) $(UV) python -m tools.live_smoke $(if $(filter 1,$(PRODUCTION)),--production-model,) $(if $(filter 1,$(INTERVIEW)),--interview,) $(if $(filter 1,$(SEARCH)),--search,) $(if $(filter 1,$(SEARCH_BOUND)),--search-bound,) $(if $(filter 1,$(WONDER)),--wonder,)

live-eval:
	$(BACKEND) $(UV) python -m tools.live_eval $(if $(CASES),--cases $(CASES),) $(if $(filter 1,$(WONDER)),--wonder,)

live-adzuna:
	$(BACKEND) $(UV) python -m tools.live_adzuna

live-extract:
	$(BACKEND) $(UV) python -m tools.live_smoke --extract

live-role-research:
	$(BACKEND) $(UV) python -m tools.live_role_research $(if $(TITLE),--title "$(TITLE)",)

session:
	$(BACKEND) $(UV) python -m tools.session start

session-ledger:
	$(BACKEND) $(UV) python -m tools.session ledger

stop:
	$(BACKEND) $(UV) python -m tools.stack stop

reset-demo:
	$(BACKEND) $(UV) python -m tools.stack reset-demo

rotate-master-key:
	$(BACKEND) $(UV) python -m tools.stack rotate-master-key

reseal:
	$(BACKEND) $(UV) python -m tools.stack reseal

status:
	$(BACKEND) $(UV) python -m tools.stack status

# Spike (throwaway, session W1): builds and serves the three directions on loopback only and
# opens the chooser. Its own package and lockfile (spikes/world); no product check touches it.
spike-world:
	cd spikes/world && pnpm install --frozen-lockfile && pnpm run start
