# Nessa L0 command contract (development plan section 2). Run from the repository root.
#   make setup              check prerequisites, install locked dependencies, create local config,
#                           fetch and verify the pinned ESCO release, build images
#   make dev                start the live stack (the worker may reach Meta), migrate, seed, print URLs
#   make demo               start the stack with no route out of the machine (fixture workspace)
#   make check              format, lint, types and fast deterministic tests, backend and web (no Docker)
#   make acceptance         full offline suite against real PostgreSQL 16, DBOS and the Auth emulator,
#                           then the Storybook build and the browser journeys on their own stack
#   make live-smoke         budget-capped real Meta smoke on the test model; PRODUCTION=1 (exactly)
#                           qualifies the production model; INTERVIEW=1 (exactly) runs one
#                           interview turn and confirms its proposals instead of a connection check
#   make stop               stop every service, bounded; persisted work is kept
#   make reset-demo         recreate the named fixture workspace only
#   make rotate-master-key  add a master key version, reload it, reseal every sealed record
#   make reseal             reseal every sealed record under the current master key
# Local secrets and master keys live in NESSA_HOME (default ~/.nessa/l0), never in the repository.

UV := uv run --locked
BACKEND := cd backend &&
WEB := cd apps/web &&
# Next.js and Storybook send anonymous usage data unless told not to (SEC-04: no telemetry).
export NEXT_TELEMETRY_DISABLED := 1
export STORYBOOK_DISABLE_TELEMETRY := 1

.PHONY: setup dev demo check acceptance live-smoke stop reset-demo status rotate-master-key reseal

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
	$(BACKEND) $(UV) pytest -m "integration or stack"
	$(WEB) pnpm run build-storybook && pnpm run e2e

# Only PRODUCTION=1 opts in to the production model; any other value (0, false, no) does not.
live-smoke:
	$(BACKEND) $(UV) python -m tools.live_smoke $(if $(filter 1,$(PRODUCTION)),--production-model,) $(if $(filter 1,$(INTERVIEW)),--interview,)

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
