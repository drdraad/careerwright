# L0 sprint tasks (execution breakdown)

This file breaks `docs/plan/development-plan.md` (the local development plan, v1.0) into
implementation tasks for agent execution. Authority order: product specification
(`Nessa_Product_Specification.md`, v1.2) → development plan local overrides → this file.
This file adds task slicing, environment facts and standing rulings only; it never
relaxes the plan or the specification.

Each task names its sprint card. Read that card in `docs/plan/development-plan.md`
in full (deliverables, acceptance, coherence review) and the plan's shared sections
listed under "Always read". Then read the specification sections the card cites
(`grep -n '^#' Nessa_Product_Specification.md` lists them; read only what you need).

## Always read

- `docs/plan/development-plan.md` sections 1–5 (boundary, run modes, architecture,
  design contract, visual/usability acceptance) and 7–10 (testing, regression register,
  evidence qualification, sprint completion procedure). Skim section 11 (traceability).
- Your sprint card in `docs/plan/development-plan.md`.
- From Task 2 onward: repository `CLAUDE.md`, `docs/adr/`, the latest
  `docs/reviews/sprint-*.md`, and `docs/requirements-register.md`.

## Global Constraints

These bind every task and every review.

1. Product integrity is structural: the language model proposes facts and
   interpretations; validated application commands commit them. Deterministic Python
   computes readiness, affordability and route rankings.
2. Stack is fixed: React/Next.js, SVG/D3, FastAPI/Pydantic AI, DBOS, PostgreSQL 16.
   Do not introduce another solver, workflow engine, renderer, scraper vendor, vector
   database or general agent platform. uv + pnpm lockfiles, Ruff, one Python type
   checker, TypeScript strict, one JS lint/format toolchain.
3. Repository shape: `apps/web` and `backend/src/nessa`, Python organised by domain
   module (profile/exploration, evidence/acquisition, capability/catalogue,
   planning/optimisation, plan/progress, identity/execution). No empty layer
   scaffolding. Narrow ports only at real I/O boundaries. Automated architecture
   checks reject circular imports and raw vendor/SQL access from domain code.
4. Money is integer GBP minor units. Dates/months follow spec section 12 (TIME-1).
   Never use floats for money.
5. Data mode (demo / live-assisted / live-vacancy) is recorded on every workspace and
   run. Fixtures never fill missing live fields or appear as real evidence. Synthetic
   data is persistently labelled.
6. Failure is never an empty success. Failed/cancelled/truncated/unknown states stay
   distinct from complete/zero results everywhere (API, DB, UI, exports).
7. Consequential commands carry workspace ID, actor, expected version and idempotency
   key. Ownership/revocation is checked before every call, including worker access,
   enforced in the database with non-owner application roles — not only by a browser
   supplied user ID.
8. Secrets: runtime master key outside the repository and database; user keys stored
   with authenticated encryption; no credential in workflow journals, logs, errors,
   exports, command arguments or git. The acquisition worker receives no model key,
   master key or private profile store.
9. Loopback only: published ports bind 127.0.0.1; reject non-local Host/Origin.
10. Generate the TypeScript client from FastAPI's OpenAPI contract; do not duplicate
    money/state/error enums by hand.
11. Visual language: calm observatory — ink #09121F, raised ink #142338, light canvas
    #F5F7FA, sea-glass accent #5DE0C1 as starting tokens (contrast validated, not
    assumed). Semantic tokens; industry colour never means success/error. Motion:
    120–180 ms controls, 220–320 ms panels, ≤450 ms staged graph reveal, no continuous
    force motion; reduced-motion/calm mode removes spatial animation, not information.
    WCAG 2.2 AA target.
12. Tests assert contracts and invariants, not implementation shape or exact LLM prose.
    Never soften assertions to get green. SQLite is not a substitute for PostgreSQL.
    A test that could not start or collected nothing is not evidence.
13. Every sprint's last task writes `docs/reviews/sprint-N.md` following plan
    section 10 (six questions + the card's coherence question), distinguishing
    passed / failed / blocked / not run.

## Environment facts (verified 2026-10-27)

- macOS arm64. Docker 29.1.2 (aarch64 engine). uv 0.9.18. pnpm 10.33.2. Node v24.11.1.
- Host Python is 3.14 only: use a uv-managed Python 3.12 (`uv python install 3.12`).
- Host has a PostgreSQL 18 *client* only; the server must be PostgreSQL 16 in Docker.
- No Java and no firebase CLI on the host: the Firebase Auth emulator must run in a
  container.
- `META_API_KEY` is in `/Users/darianraad/Code/careerpathoptimizer/.env` (gitignored).
  Load it from that file in code/tooling. Never print it, echo it, pass it as a command
  argument, write it elsewhere, or commit it.
- Git: work on branch `l0-local-release`. Commit coherent increments with messages ending
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push. Never commit
  `.env`, key material or private evidence.
- Workspace conventions: pnpm only (never npm); make code changes with the Edit/Write
  tools, not sed/awk.

## Standing rulings (apply to every task)

- R1 Fixture pack: `Nessa_M0_Fixtures.zip` *is* now supplied. Use the original pack
  (P01–P05, worked_trace.json, source_corpus_manifest.json, validate_fixtures.py) instead
  of reconstructing it, and still independently check its expected values by hand.
  The A–I direct-spend fixture: use it if present in the pack; otherwise reconstruct it
  from spec sections 12 and 20 and label it reconstructed.
- R2 Human-only gates: design-review scoring by a product owner/design reviewer, domain
  reviewer sign-off, VoiceOver and real-Safari manual checks, the five formative task
  sessions and source rights review cannot be performed by an agent. Do the automatable
  part (screenshots at the required viewports, axe, keyboard tests, an agent critique
  explicitly labelled "agent pre-review — not the required human review") and record the
  human step as "not run — requires human" with a ready-to-use checklist. Never record an
  agent critique as a design-review score.
- R3 Real source corpus: agents may fetch publicly accessible pages (respect robots.txt
  and terms; nothing behind a login). Full bodies live only in the gitignored private
  evidence directory; git holds the manifest (URL, retrieval date, hash, labelled spans as
  minimal excerpts, missingness, rights status). Rights status is "pending human rights
  review" unless terms clearly permit retention.
- R4 Adzuna: no credentials exist. Implement the adapter and its fixture contract; record
  the live integration as "unverified — no credentials".
- R5 Live Meta usage (user instruction, 2026-10-27: "keep careful track of meta LLM
  credits and costs during testing. Use sparingly, use cheaper models to confirm working,
  and the most performant model only in production"):
  - Live calls are explicit and budget-capped (call count, tokens and estimated cost,
    enforced in code), never part of `make check` or `make acceptance`. Use as few calls
    as will establish the fact; prefer recorded/fixture runs for everything else.
  - Model choice is configuration, not code: a *test* model (the cheapest Meta model that
    supports the needed capability) for smoke/eval/confirmation runs, and a *production*
    model (the most performant qualified Meta model — `muse-spark-1.3` per the plan unless
    Sprint 0 finds otherwise) for the real live-assisted product path. Default dev/test
    commands use the test model. Run the production model only for the minimum calls
    needed to qualify it (entitlement, schema output, streaming, search), behind an
    explicit flag.
  - Every live call is cost-tracked: model ID, input/output tokens, search/tool usage,
    estimated cost from Meta's published pricing (cite the page and date), and remaining
    credit if the API exposes it. Append each run to `docs/evidence/live-usage.md` with a
    running total. Record charges you cannot determine as "unknown", never as zero.
  - If the key, entitlement or a needed model is unavailable, record the item as blocked;
    never substitute a non-Meta provider.
- R6 Decisions the plan assigns to the product owner are taken by the controller (or by
  you, if trivial) and recorded in an ADR marked "provisional — needs product owner
  confirmation".
- R7 Large third-party datasets (ESCO, ASHE) are not committed. Pin version, URL and hash
  in a manifest; `make setup` (network allowed) fetches and verifies them. If a download
  cannot be automated, document the exact manual step in the runbook and record it.
- R8 Fonts: OFL (or equivalently permissive) self-hosted files, with licence texts
  committed beside them.

---

## Task 3: Sprint 1 — local platform, persistence, identity and secrets (S1.1–S1.3)

Sprint card: "Sprint 1 Build a polished local walking skeleton". Slice: S1.1, S1.2,
S1.3 and the backend acceptance items. Spec sections 3, 16, 17, 18, 19.

Deliver the command contract (plan section 2: `make setup/dev/demo/check/acceptance/
live-smoke/stop/reset-demo`), Docker Compose (PostgreSQL 16, Firebase Auth emulator
container, FastAPI, DBOS worker, restricted acquisition worker placeholder only if it is
genuinely exercised, Next.js service slot), health checks, Alembic migrations,
deterministic seeding (demo Firebase project, two invited identities, one uninvited),
workspace/profile versions with expected-version writes, source references, typed error
envelopes, run IDs, outbox, database ownership enforcement with non-owner roles
(including the worker role), encrypted key storage with revoke/rotate, runtime master key
outside git/DB with restrictive permissions, server-side budget reservation, redacted
logging, host/origin rejection. `make demo` must block outbound traffic in demo mode.

Acceptance (backend part of the card): fresh DB migrates; populated DB upgrades without
losing data; profile updates survive reload and restart; stale version rejected;
API/stream/worker requests for another workspace fail, uninvited fails; key redaction
across errors, DB history and exports; unauthorised local origin cannot trigger
authenticated changes. `make check` runs fast checks; `make acceptance` runs against real
PostgreSQL + DBOS.

