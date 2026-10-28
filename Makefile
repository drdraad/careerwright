# Nessa L0 command contract (development plan section 2). Run from the repository root.
#   make setup        check prerequisites, install locked dependencies, create local config, build images
#   make dev          start the live stack (the worker may reach Meta), migrate, seed, print URLs
#   make demo         start the stack with no route out of the machine (fixture workspace)
#   make check        format, lint, types and fast deterministic tests (no Docker)
#   make acceptance   full offline suite against real PostgreSQL 16, DBOS and the Auth emulator
#   make stop        stop every service, bounded; persisted work is kept
#   make reset-demo   recreate the named fixture workspace only
# Local secrets and master keys live in NESSA_HOME (default ~/.nessa/l0), never in the repository.

UV := uv run --locked
BACKEND := cd backend &&

.PHONY: setup dev demo check acceptance stop reset-demo status

setup:
	$(BACKEND) uv python install 3.12 && uv sync --locked
	cd docs/design && pnpm install --frozen-lockfile && pnpm exec playwright install chromium
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

acceptance:
	$(BACKEND) $(UV) pytest -m "integration or stack"

stop:
	$(BACKEND) $(UV) python -m tools.stack stop

reset-demo:
	$(BACKEND) $(UV) python -m tools.stack reset-demo

status:
	$(BACKEND) $(UV) python -m tools.stack status
