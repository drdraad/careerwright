# Repository contract

Nessa L0: a local career-planning app (FastAPI, Pydantic AI, DBOS and PostgreSQL 16
backend; Next.js web app to come). Authority order: `Nessa_Product_Specification.md`
(v1.2), then `docs/plan/development-plan.md` (v1.0), then `docs/plan/l0-sprint-tasks.md`.
Decisions live in `docs/adr/`; the latest sprint review is in `docs/reviews/`.

## Commands
- Setup: `cd backend && uv sync --locked` (uv-managed Python 3.12; the host Python is
  3.14). Design tooling: `cd docs/design && pnpm install --frozen-lockfile && pnpm exec
  playwright install chromium`. TODO(Task 3): replace both with `make setup`.
- Fast checks: `cd backend && uv run --locked ruff format --check . && uv run --locked
  ruff check . && uv run --locked mypy && uv run --locked pytest && uv run --locked
  python -I ../fixtures/m0/validate_fixtures.py`. TODO(Task 3): `make check`.
- Full acceptance checks: `cd backend && uv run --locked pytest -m integration
  spikes/durable` (needs Docker: PostgreSQL 16.15 and DBOS). TODO(Task 3): `make
  acceptance`, the command CI uses.
- Design references: `cd docs/design && pnpm run contrast && pnpm run screenshots`.
- Live Meta calls run only through explicit, budget-capped commands, never from the checks
  above. Today that is `cd backend && uv run python -m spikes.meta.live_spike <check>`.
  TODO(Task 3): `make live-smoke`. Every call is appended to
  `docs/evidence/live-usage.jsonl` with its cost (ruling R5).

## Repository facts
- Requirement IDs and test IDs: `docs/requirements-register.md`. Tag each test with its
  register ID, and update the rows your work closes.
- Representative implementation: `backend/spikes/durable/workflow.py`. It shows the
  pinned durable-activity pattern (ADR 0002): workflows carry IDs only; one bounded
  activity opens the sealed payload and key just in time; failures are classified from
  type and status with the message discarded; the DBOS step is the only retry owner.
- Non-obvious invariants:
  - The model proposes; validated application commands commit. Readiness, affordability
    and route ranks are computed by deterministic Python, never by the model.
  - Money is integer minor units (GBP). Use `Money` (≥ 0) for payments and `SignedMoney`
    for economic cost. Unknown money is `null`, never 0.
  - Unknown is never zero or ineligible. Failure is never an empty success. A truncated
    search is never "no route": `NO_ROUTE_IN_BOUNDED_MODEL` needs complete coverage.
  - The monthly model (TIME-1) reserves every touched month. A prerequisite is usable
    only from the next month boundary. Cash is prefunded: a receipt counts only if proven
    available before the outflow. Fixture wages arrive late in the month.
  - Pareto layers are computed over the full archive, dominated schedules included.
    Equal points do not dominate each other.
  - TRACE-01 (economic cost) and DIRECTAI (direct spending) never share route IDs or
    labels. `fixtures/m0` is the byte-identical supplied pack (hashes in
    `fixtures/README.md`): never edit it. Fixtures never fill live fields; synthetic data
    is always labelled.
  - Secrets: `.env` holds `META_API_KEY`. Never print it, pass it as an argument, log it
    or journal it. The test model `muse-spark-1.3-contributor` takes synthetic or public
    inputs only; production is `muse-spark-1.3` (ADR 0003, provisional).
  - Loopback only: published ports bind 127.0.0.1.
  - UI uses the semantic tokens in `docs/design/tokens/tokens.css`. Sea-glass means
    selection or action only, and industry colour never means status. Every new colour
    pairing goes into `contrast-pairs.json` and is measured.
- Compatibility boundary: the exact pins in `backend/pyproject.toml` and
  `backend/uv.lock` (bump only by re-running the ADR 0002 suite), pnpm 10.33.2, Python
  3.12 and PostgreSQL 16. Code goes in `backend/src/nessa/<domain module>` (plan
  section 3) and `apps/web`. No empty layer scaffolding.

## Change scope
- If ambiguous or conflicting instructions materially affect behavior, scope,
  or acceptance criteria, ask for clarification before implementing the affected part.
- Deliver the requested behavior completely, using the simplest clear design
  that fits the surrounding code.
- Keep unrelated cleanup, new dependencies, and speculative extension points
  out of the change. Include wider changes when the requested result needs them.
- Preserve behavior outside the requested change and identify intentional
  changes to public behavior or compatibility.

## Correctness
- For changed behavior, identify observable acceptance criteria.
- For bug fixes, prefer a focused reproducer that fails for the reported behavior
  before the fix, when practical.
- Treat existing tests as evidence of the contract. Change expectations only
  when the intended behavior changes or an expectation is demonstrably wrong.
- Preserve valid assertions; do not suppress failures to obtain a passing result.
- Keep failure distinguishable from success. Do not mask errors with empty results,
  misleading statuses, or silent behavior changes. Without an authorized fallback,
  use the existing error mechanism to make failure observable to the caller and
  diagnosable with actionable context.
- Use fallbacks only when requirements or an established contract authorize them.
  Obtain approval before introducing a fallback that changes agreed behavior.

## Completion
- Report what changed, checks actually run and their results, and remaining gaps.
- Evidence must apply to the final code; stale or failed-to-start checks are not passes.
- Human-only gates (design scores, VoiceOver, Safari, task sessions, rights and domain
  review) are recorded as "not run — requires human" and never as passed (ruling R2).
- Stop when the requested result is established. Further checking should address
  a concrete unresolved risk.
- If validation is blocked or an unrelated check fails, report that clearly;
  do not silently expand scope or claim the change is verified.
