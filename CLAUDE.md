# Repository contract

Nessa L0: a local career-planning app (FastAPI, Pydantic AI, DBOS and PostgreSQL 16
backend; Next.js web app in `apps/web`). Authority order: `Nessa_Product_Specification.md`
(v1.2), then `docs/plan/development-plan.md` (v1.0), then `docs/plan/l0-sprint-tasks.md`.
Decisions live in `docs/adr/`; the latest sprint review is in `docs/reviews/`.

## Commands
Run from the repository root (details: `docs/runbook.md`).
- Setup: `make setup` (prerequisites, `uv sync --locked` on uv-managed Python 3.12, the
  web app and design tooling with Playwright's Chromium, local secrets and master key in
  `NESSA_HOME`, default `~/.nessa/l0`, the pinned ESCO release fetched into the gitignored
  `var/datasets/` and hash-checked, and the Docker images). The host Python is 3.14;
  never use it for the backend. pnpm only, never npm.
- Run: `make dev` (live: only the worker may reach Meta), `make demo` (no service has a
  route out), then open `http://127.0.0.1:53000`; `make stop` (bounded; keeps data),
  `make reset-demo` (fixture workspace only).
- Fast checks: `make check` (backend: ruff format and lint, mypy, fast pytest, fixture
  validator; web: generated-client drift, Biome, `tsc`, Vitest). No Docker, no network.
- Full acceptance checks: `make acceptance`, the command CI uses: real PostgreSQL 16.15,
  DBOS, the Auth emulator and the Compose stack, then the Storybook build and the Playwright
  journeys, each in their own projects and ports.
- Web app (`cd apps/web`): `pnpm storybook` (component states), `pnpm run generate` after
  any API change (commit the regenerated client), `pnpm run review-screenshots` (visual
  review package).
- Design references: `cd docs/design && pnpm run contrast && pnpm run screenshots`.
- Live Meta calls run only through explicit, budget-capped commands, never from the checks
  above: `make live-smoke` (test model; `PRODUCTION=1` qualifies the production model;
  `INTERVIEW=1` runs one interview turn instead of a connection check) and `make
  live-eval` (the representative evaluation cases, at most 6, test model only). Every call
  is appended to `docs/evidence/live-usage.jsonl` and `.md` with its cost (R5).

## Repository facts
- Requirement IDs and test IDs: `docs/requirements-register.md`. Tag each test with its
  register ID, and update the rows your work closes.
- Representative implementation: `backend/src/nessa/identity/activity.py` with
  `workflow.py` beside it: the pinned durable-activity pattern (ADR 0002, ADR 0004), one
  `RunTask` per run kind (composed in `nessa/worker.py`; a new model-backed kind is a task,
  never a second call path, ADR 0006). Workflows carry IDs only; one bounded activity
  re-checks access, model, key and budget, opens the sealed input and key just in time and
  stores the output sealed with its usage; failures
  are classified from type and status with the message discarded; each transient failure
  class has one retry owner: the DBOS step for provider failures, the activity's store
  budget for store failures. `nessa/profile/commands.py` shows an expected-version command.
- Layout: `nessa/identity` (identity and execution: access, workspaces, keys, runs,
  spend), `nessa/profile` (profile, interview contract, turns and preferences, the support
  policy, discovery, the slate and the early sketch, provisional concepts),
  `nessa/catalogue` (the ESCO taxonomy and the English city list), `nessa/api` (HTTP only),
  `nessa/migrations` (forward-only SQL), `nessa/worker.py` (worker entry point). Identity
  never imports profile or catalogue. Vendor and SQL imports are allowed only in the
  adapters listed in `backend/tests/architecture/test_boundaries.py`; add new ones there.
- Web layout (`apps/web`, ADR 0005): `src/app` (routes; `api/[...path]` forwards `/api/v1`
  to the API), `src/components` (shell and components; `WorkspaceShell.tsx` owns session,
  queries and events), `src/lib` (client wiring, events, vocabulary, the fixture adapter),
  `src/stories` (Storybook), `e2e` (Playwright on its own stack). `src/generated` is the
  generated client and `src/design` a byte-identical mirror of `docs/design`: never edit
  either by hand.
- Non-obvious invariants:
  - The model proposes; validated application commands commit. Readiness, affordability
    and route ranks are computed by deterministic Python, never by the model. A chat
    proposal reaches the profile only through a decision on a complete, validated turn,
    against the version it was made for, with each limit or target confirmed by name, via
    the same command as a direct edit (ADR 0006). In discovery the model proposes searches
    only; the slate is deterministic code over ESCO, its controls are view parameters and
    never limits, and a suggestion becomes a target only by the person's choice (ADR 0007).
  - Any listed risk word, in any form, shows a calm support panel with UK resources beside
    the conversation. The message is still sent; that turn's reply only acknowledges and
    offers a smaller next step, and nothing about the panel is stored or used for
    suitability (one recall-first screen, ADR 0007). Model output may not infer a health
    condition, type, protected characteristic or percentage the person never used
    (`nessa/profile/safety.py`).
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
    is always labelled. ESCO comes only from the pinned, hash-checked release;
    `fixtures/esco-sample` is a labelled test subset, rebuilt only by `tools.esco_sample`.
  - Secrets: `.env` holds `META_API_KEY` for `make live-smoke` only; the product takes
    user keys through the API and seals them. Never print a key, pass it as an argument,
    log it or journal it. Database passwords and master keys live in `NESSA_HOME`, never in
    the repository. The test model `muse-spark-1.3-contributor` takes synthetic data only,
    enforced in code and by a database CHECK; production is `muse-spark-1.3` (ADR 0003).
    Demo workspaces run only the offline fixture interviewer, never a provider model.
  - Ownership is row-level security: run API SQL inside `actor_transaction` and worker
    SQL inside `run_transaction` (`nessa/db.py`). Never connect at runtime as an owner role.
  - Every consequential write takes an expected version and an `Idempotency-Key` and goes
    through `run_idempotent`. Errors are `NessaError` codes; never echo request input.
  - Loopback only: services sit on an internal network; only the edge relay publishes
    ports, on 127.0.0.1. The API rejects foreign Host and Origin headers (ADR 0004).
  - UI uses the semantic tokens in `docs/design/tokens/tokens.css`. Sea-glass means
    selection or action only, and industry colour never means status. Every new colour
    pairing goes into `contrast-pairs.json` and is measured.
  - The UI takes enums, money and error codes only from the generated client, shows an
    error code's words (`src/lib/vocabulary.ts`), never the API's message, and computes no
    rank, layer or affordability. Fixture content is shown only in the fixture workspace,
    labelled. The web server forwards the browser's Origin unchanged and checks Host
    itself; its CSP allows only the web origin and the Auth emulator.
- Compatibility boundary: the exact pins in `backend/pyproject.toml` and
  `backend/uv.lock` (bump only by re-running `make acceptance`), the exact pins in
  `apps/web/package.json` and its lockfile (at least 14 days old, enforced by pnpm; one
  provisional exception, `next` 16.4.1, to remove per ADR 0005 decision 1; record each in
  `docs/dependencies.md`), pnpm 10.33.2, Node 24, Python
  3.12, PostgreSQL 16, and the DBOS `application_version` `nessa-l0-1` (change it when the
  workflow's step sequence changes). Code goes in `backend/src/nessa/<domain module>` (plan
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
