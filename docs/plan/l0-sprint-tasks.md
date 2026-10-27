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
- R5 Live Meta usage is explicit and budget-capped (by call count and tokens, enforced in
  code), never part of `make check` or `make acceptance`. Log every live run's model ID,
  usage and outcome in `docs/evidence/live-usage.md`. If the key, entitlement or model is
  unavailable, record the item as blocked; never substitute another provider or model.
- R6 Decisions the plan assigns to the product owner are taken by the controller (or by
  you, if trivial) and recorded in an ADR marked "provisional — needs product owner
  confirmation".
- R7 Large third-party datasets (ESCO, ASHE) are not committed. Pin version, URL and hash
  in a manifest; `make setup` (network allowed) fetches and verifies them. If a download
  cannot be automated, document the exact manual step in the runbook and record it.
- R8 Fonts: OFL (or equivalently permissive) self-hosted files, with licence texts
  committed beside them.

---

## Task 1: Sprint 0 — technical spike and contracts (S0.1–S0.4)

Sprint card: "Sprint 0 Resolve the expensive uncertainties". Slice: S0.1, S0.2, S0.3,
S0.4. Spec sections 1 (BND-1), 16, 17 (ARC-1), 19.

Deliver:
- Minimal real scaffolding the spike needs (uv project under `backend/` with
  `backend/src/nessa`, Python 3.12, Ruff, the chosen type checker, pytest) — no feature
  modules yet. A spike may live in `backend/spikes/` if it is not production code.
- `docs/adr/0001-l0-scope.md` recording the plan section 1 overrides (L0 vs M0).
- `docs/dependencies.md`: dependency matrix with exact versions to pin, checked against
  arm64 Docker images (PostgreSQL 16, Firebase Auth emulator container, Python 3.12, Node,
  pnpm).
- S0.2: with the real key and a hard cap (≤ 15 live calls total for this task), prove
  Standard-mode `muse-spark-1.3` access, structured (schema) output, search, streaming and
  usage reporting through Pydantic AI's native Meta provider. Check the current docs
  (plan section 12 links) first. Record model ID, capabilities and restrictions. An
  invalid key must fail visibly. If entitlement/model is blocked, say so (R5).
- S0.3/S0.4: DBOS workflow against local PostgreSQL 16 (Docker). Kill and restart a
  worker mid-workflow; exercise an outbox replay; inspect persisted workflow
  arguments/results and prove no credential or private payload is journalled (workflows
  carry IDs; a bounded activity resolves the encrypted payload and credential just in
  time, persists validated output, returns references). ADR pinning the Pydantic AI/DBOS
  composition (`docs/adr/0002-durable-execution.md`).
- `docs/evidence/sprint-0-spike.md`: exit evidence (commands run, outputs, what is
  blocked) and the live-usage log entry.

Acceptance: the card's "Exit evidence" items that belong to S0.1–S0.4.

## Task 2: Sprint 0 — fixtures, registers and design references (S0.5–S0.6) + Sprint 0 review

Sprint card: "Sprint 0 Resolve the expensive uncertainties". Slice: S0.5, S0.6, the
remaining exit evidence and the Sprint 0 coherence review. Spec sections 4, 12, 14, 20.

Deliver:
- Fixture pack placed under `fixtures/m0/` (R1), `validate_fixtures.py` run, plus an
  independent hand-check document (`docs/evidence/fixture-hand-check.md`) of TRACE-01
  arithmetic, the A–I direct-spend fixture and the five persona expectations.
- Source-corpus manifest scaffold (from the pack's `source_corpus_manifest.json`) with
  owners/dispositions for unresolved access and reviewer needs.
- `docs/requirements-register.md`: canonical requirement-to-test register covering every
  spec requirement ID ([M0, XXX-1] tags) and the plan section 8 regression families,
  with planned test IDs and owning sprint.
- Design references in `docs/design/` (use the frontend-design skill): semantic token set
  with measured contrast results; chosen fonts with licences (R8); three high-fidelity
  signature compositions — conversation with evidence drawer, opportunity map with
  selected role, route comparison with selected journey — using actual fixture numbers
  and realistic long labels, each with a mobile variant, an unknown-data state and one
  failure state. Build them as static, versioned HTML/CSS/SVG and capture PNG screenshots
  at 1440×900 and 390×844.
- Repository `CLAUDE.md` adapted from the starter kit (`claude_code_starter_kit.zip` →
  `CLAUDE.md` template); fill in what exists, leave a clearly marked TODO only for
  commands Task 3 will create.
- `docs/reviews/sprint-0.md` per plan section 10 (R2 for the human design approval).

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

## Task 4: Sprint 1 — designed shell connected to the real API (S1.4–S1.5) + Sprint 1 review

Sprint card: "Sprint 1 Build a polished local walking skeleton". Slice: S1.4, S1.5, the
UI acceptance items, the coherence review. Spec sections 3, 13, 14.

Deliver `apps/web` (Next.js, TypeScript strict) implementing the Task 2 design
references: tokens, self-hosted fonts, chapter rail (You, Roles, Skills, Options, Routes,
Plan), workspace strip, evidence drawer, cards, buttons, form controls, status vocabulary,
mobile layouts; Storybook stories for loading, empty, unknown, conditional, stale, error
and disabled states. Generated TS client from OpenAPI. Sign-in via the Firebase Auth
emulator with seeded identities. A fixture adapter supplies labelled content for the
end-to-end shell (no component hard-codes financial examples); the route preview is
clearly fixture-driven. Resumable status events with a reconnect path. API/events routed
through the web origin. Playwright journey: sign in, edit profile, inspect fixture route,
restart services, reopen same work. Keyboard reaches every chapter and the drawer with
focus return. Fixture mode makes no external request after setup.

Finish: complete repository `CLAUDE.md` commands; `docs/reviews/sprint-1.md` including the
first visual review package (screenshots at 1440×900, 390×844, 768×1024; agent pre-review;
human review checklist per R2).

## Task 5: Sprint 2 — ESCO taxonomy and the interview contract (S2.1–S2.2)

Sprint card: "Sprint 2 Deliver conversation and career discovery". Slice: S2.1, S2.2 and
their acceptance items. Spec sections 3–5, 16 (REC-1, TAX-1).

Deliver: pinned full English ESCO import (R7) with aliases, skill relationships, hashes,
versions, attribution; PostgreSQL full-text retrieval; reviewed finite English-city list;
provisional internal concepts for corroborated titles outside ESCO. Structured
InterviewTurn contract via the Meta model port (Pydantic AI), bounded validation repair,
proposed patches with source message references, explicit confirmation of hard
constraints, direct edits and chat sharing the same application commands, never
committing partial streamed JSON. Deterministic fixture model adapter satisfying the same
failure/provenance contract. Tests for invalid schemas, refusals, truncation, unavailable
model, budget exhaustion, stale concurrent profile writes; the old profile survives every
failed proposal.

## Task 6: Sprint 2 — conversation experience and grounded discovery (S2.3–S2.6) + Sprint 2 review

Sprint card: "Sprint 2 Deliver conversation and career discovery". Slice: S2.3–S2.6, the
remaining acceptance items, the coherence review. Spec sections 3, 4 (REC-1, DIV-1), 13.

Deliver the You chapter per the conversation composition: sure/unsure entry,
practical/gentle/challenge preferences, pause/resume, skip/unknown, editable "What we
know", review tray (accept/edit/undo), one useful question at a time; bounded multi-query
retrieval, dedupe, greedy qualified diverse slate (soft six-suggestion / 60–120 candidate
targets; no fabricated match percentage); labelled early route/requirement sketch; minimal
reviewed response policy for acute distress and diagnostic inference. At least 30 reviewed
synthetic interview/discovery eval cases (semantic expectations), an explicit
budget-capped live eval command, and a capped live run of representative cases (R5).
P02 explores without invented income baseline or forced personality test; sure users
bypass exploration. `docs/reviews/sprint-2.md`.

## Task 7: Sprint 3 — evidence acquisition backend (S3.1–S3.4, S3.6)

Sprint card: "Sprint 3 Make the evidence and opportunity map real". Slice: S3.1, S3.2,
S3.3, S3.4, S3.6 and their acceptance items. Spec sections 5, 6, 7, 11 (TAX-1, AIR-1).

Deliver SourceAttempt/SourceClaim records (permitted retention, field spans, hashes,
publication/retrieval/effective dates); pinned ASHE imports (R7) and reviewed UK-SOC
mappings with explicit unresolved crosswalks; bounded Meta search discovery; keyless
Scrapling HTTP fetch/parse in the restricted acquisition worker (scheme, resolved IP,
redirects, content type, size, time checks; structured fields first, model extraction
only where needed); manual pasted text as a separate input route; Adzuna adapter + fixture
contract (R4); syndicated-job dedupe, agency vs employer, multi-city counted once;
closure/freshness (jobs 24 h, fees/intakes 7 d, funding 48 h; failed refresh never extends
validity), favourites, cancellation, resumable incremental results; AI evidence/mapping
packs and publication-state machinery (reviewed ranges only, otherwise unscored;
lower-bound filtering; unscored visible by default in exploration). SSRF tests with a
controlled server incl. IPv6/encoded addresses; prove the fetcher has neither user
secrets nor private profile access; failed fetch never becomes "no vacancies".

## Task 8: Sprint 3 — living opportunity map and the job corpus (S3.5) + Sprint 3 review

Sprint card: "Sprint 3 Make the evidence and opportunity map real". Slice: S3.5, the
20-job corpus portion, remaining acceptance, the coherence review. Spec sections 5, 7
(VIS-1), 13, 14.

Deliver the Roles chapter per the opportunity-map composition: SVG/D3 dendrite with stable
anchors, company expansion, up to 100 visible job nodes, explicit aggregation counts;
numeric salary and AI-range filters; pay lanes / pay lens; mobile-first list; one shared
selection and filter contract across list, map and pay lens; focus retention and keyboard
actions; graph distance never implies commute feasibility. Curate the 20 real job postings
(R3) incl. closed jobs, missing/predicted pay, snippets, duplicates, drift and hostile page
instructions, and run them through the pipeline. Second visual review package (sparse and
dense data) per R2. `docs/reviews/sprint-3.md`.

## Task 9: Sprint 4 — capability model, protected gates and outcomes (S4.1–S4.6 backend)

Sprint card: "Sprint 4 Build trustworthy skills and outcome assessment". Slice: the domain
and API for S4.1–S4.6 and their acceptance items. Spec sections 8, 9, 10 (MAP-1, OUT-1,
RDY-1).

Deliver versioned provisional matrices (ESCO + up to three permitted full-text exemplars
per target; essential/preferred/disputed/unknown distinct); behaviourally anchored levels
(unknown ≠ level 0, self-report vs demonstration, recency, confirmation; evidence shared
across targets without assuming same rubric); combined question graph with gate-first
ordering and decision-impact heuristic; typed immutable protected gates (legal practice,
recognition, admission, eligibility); OUT-1 row mappings from syllabus/assessment spans to
observable tasks (topic mention vs practice vs assessed demonstration); gap classification
and abstract action graph; P05 apply-now path; target/matrix version on all derived
results. Tests: P04 cannot become ready by demoting registration; two introductory courses
cannot add into competence; enrolment/completion never overwrites current evidence;
unsupported outcome level stays null; evidence changes recompute only affected gaps;
changing an essential non-protected row creates a new target definition and invalidates
earlier ranks.

## Task 10: Sprint 4 — Skills chapter, evidence questions and course corpus + Sprint 4 review

Sprint card: "Sprint 4 Build trustworthy skills and outcome assessment". Slice: the Skills
chapter UI, the question flow UI, the ten-course corpus labels, remaining acceptance, the
coherence review. Spec sections 8, 9, 13, 14.

Deliver the Skills chapter: demonstrated / self-reported / planned / unresolved
requirements, behavioural anchors, inspectable evidence, shared questions across targets,
visibly protected gates, pause/stop, unresolved coverage without an employability
percentage; direct edits and chat proposals through the same contract. Label outcome
fields for at least ten real course pages (R3) incl. misleading titles and teaching
without assessment; review false-positive readiness mappings individually (any unsupported
consequential outcome blocks publication of the affected route). `docs/reviews/sprint-4.md`.

## Task 11: Sprint 5 — offerings, funding, monthly compiler and ledgers (S5.1, S5.2, S5.4–S5.6)

Sprint card: "Sprint 5 Compile real options into an honest monthly model". Slice: the
domain/API for S5.1, S5.2, S5.4, S5.5, S5.6 and the numeric acceptance items. Spec
sections 10, 11, 12 (OUT-1, TIME-1, FIN-1).

Deliver action concepts vs dated offerings/intakes; composite apprenticeship action;
funding statuses (confirmed / potentially eligible / ineligible / insufficient
information) separate from award approval; immutable monthly input compiler; separate
direct-spend, income-difference and liquidity ledgers in integer GBP minor units; direct
budget vs payment cap vs deficit cap vs reserve; post-horizon liabilities; common
post-readiness income scenario; fixed base/delay/no-award/no-offer scenarios. A pure
Python checker reproduces TRACE-01 exactly before any optimiser exists. Regression
families TRACE01 (ledger parts), PREFUND, PAYCAP, TIME, WORKLOAD, ECON, FUNDING with
explicit test IDs, plus Hypothesis properties for money/dates.

## Task 12: Sprint 5 — option review checkpoint and funding corpus + Sprint 5 review

Sprint card: "Sprint 5 Compile real options into an honest monthly model". Slice: S5.3,
the Options chapter UI, the three-funding-page corpus, remaining acceptance, the
coherence review. Spec sections 10, 13, 14.

Deliver the Options chapter per the design: curated comparison by gap, pin/exclude,
provider provenance, conditional funding, missing critical fields, scope bounds,
removed-candidate counts, explicit review checkpoint; when limits are exceeded ask the
user to retain variants — never silently truncate to the first 24 options or two intakes.
Show why a route may fail workload, payment or cash constraints using the Task 11 model.
Finish the three real funding pages (R3). `docs/reviews/sprint-5.md`.

## Task 13: Sprint 6 — optimiser, archive and Pareto layers (S6.1–S6.6) + Sprint 6 review

Sprint card: "Sprint 6 Prove the optimiser and archive semantics". Whole sprint. Spec
section 12 (OPT-1, ROU-1, FIN-1, RDY-1), 20 (TEST-1).

Deliver canonical DFS (skip or one reviewed offering per concept, ≤ 6 selected actions,
DAGs/dates without equivalent permutations, all gates/timetable/cash/workload checks);
only provably sound pruning with documented proofs; versioned disk-backed archive of every
distinct feasible schedule (atomic checkpoints, idempotent solve identity, resume-or-restart
under a new attempt ID); 30 s / 1,000,000 states / 50,000 feasible caps with exact stop
reasons; separate rank stage; efficient two-objective layering qualified against simple
iterative peeling; family grouping for presentation only; cancellable optimiser child
process with no network/LLM/ORM access, run durably via DBOS; independent Cartesian oracle
and independent route checker sharing no code with the candidate implementation.
Regression families TRACE01 (layers), DIRECTAI, PARETO, FAMILY, LIMITS. Benchmark
50,000-point ranking. `docs/reviews/sprint-6.md`.

## Task 14: Sprint 7 — coordinated route comparison (S7.1–S7.6) + Sprint 7 review

Sprint card: "Sprint 7 Make route comparison the signature experience". Whole sprint.
Spec sections 12–14 (VIS-2, ROU-1, AIR-1).

Deliver the Routes chapter per the route-comparison composition using real solver output:
per-target discrete time–cost scatter with cost definition/baseline/horizon/currency/
bounds/coverage beside the chart; readable F1–F3 with family grouping and named dominance
explanations; one documented deterministic comparator rule; stress scenarios shown
separately; exact numeric inputs + keyboard sliders; view filtering preserves ranks;
explicit reranking; linked Gantt, step cards, monthly financial table, evidence drawer;
purposeful transitions and calm/reduced motion; paginated archive and bounded projection
with shown/total counts. Property and browser tests for selection/filter consistency;
TRACE-01 renders A/B/C F1, D F2, E F3; A–I fixture uses direct-spending labels; measure
interaction budgets. Third visual review package (R2). `docs/reviews/sprint-7.md`.

## Task 15: Sprint 8 — chosen plan, progress, revision and exports (S8.1–S8.6) + Sprint 8 review

Sprint card: "Sprint 8 Turn a selected route into a durable plan". Whole sprint. Spec
sections 11, 15 (FIN-1, AIR-1).

Deliver immutable PlanVersion snapshots; Plan chapter (overview, one next action,
progress bands, rest/reschedule; planning progress vs evidence vs real-world activity);
dependency invalidation and proposed revisions with old/new diff; replanning the remaining
horizon with explicit accounting bases; browser print CSS, JSON and ICS from one
serialisable snapshot with sensitive-detail omission; ICS semantics (stable UID, sequence,
proposed conditional events, DST and all-day correctness verified with an independent
parser). TRACE-01 route B agrees across screen, print and JSON. Workspace deletion across
snapshots, exports, cache and workflow references. `docs/reviews/sprint-8.md`.

## Task 16: Sprint 9 — local release qualification and handover (S9.1–S9.6)

Sprint card: "Sprint 9 Qualify and hand over the local release". Whole sprint plus the
plan section 11 final reviewer demonstration (automatable parts).

Deliver P01–P05 end to end in a real browser against the full stack; a real budget-capped
Meta journey with a synthetic persona (interview → discovery → extraction → checkpoint →
solve → selection → export) with browser reconnect and worker restart mid-run (R5);
key/spend/provider/cancellation/drift/stale-write/crash fault injection with leak
inspection; fresh install and migration from the previous candidate; PostgreSQL + blob
backup/restore with keys handled separately; full workspace deletion; automatable
accessibility and visual checks with human checklists (R2); packaging (lockfiles,
manifests, licence notices, ADRs, runbook with quickstart/troubleshooting/reset/backup/
restore, release evidence). Release report `docs/release/L0-release-report.md`
distinguishing passed / failed / blocked / not run. Tag the tested local release
(`l0-rc1`); never publish a service. `docs/reviews/sprint-9.md`.
