# L0 sprint tasks (execution breakdown)

This file breaks `docs/plan/development-plan.md` (the local development plan, v1.4) into
implementation tasks for agent execution. Authority order: product specification
(`Careerwright_Product_Specification.md`, v1.3) → development plan local overrides → this file.
What is done and what comes next is in "Current position and next tasks" below. The
remaining tasks follow the order, dependency rules and dispatch preconditions below (ADR
0008), as Task A1 amends them once the product owner approves.
This file adds task slicing, environment facts and standing rulings only; it never
relaxes the plan or the specification.

Each task names its sprint card. Read that card in `docs/plan/development-plan.md`
in full (deliverables, acceptance, coherence review) and the plan's shared sections
listed under "Always read". Then read the specification sections the card cites
(`grep -n '^#' Careerwright_Product_Specification.md` lists them; read only what you need).

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
3. Repository shape: `apps/web` and `backend/src/careerwright`, Python organised by domain
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
11. The experience: the living world of plan section 4 (v1.4, ADR 0014), which replaces
    the calm observatory. One persistent world in which chapters are places; everything
    that varies has a computed meaning; revelations come only from deterministic sources
    and verified spans; a still version (reduced motion, calm mode, no WebGL) carries
    every state and word; an exact DOM and SVG layer over a WebGL world that holds nothing
    unique. Semantic tokens with measured contrast; one colour, one meaning; industry is
    shown by glyph and label, never by colour or as status.
    WCAG 2.2 AA target. A screen that works but is bland fails review.
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
  sessions and source rights review cannot be performed by an agent (after session 1, agents
  classify pages against the person's rights policy; a page outside it stays with a person;
  R10). Do the automatable part (screenshots at the required viewports, axe, keyboard
  tests, an agent critique explicitly labelled "agent pre-review — not the required human
  review") and record the human step as "not run — requires human" with a ready-to-use
  checklist. Never record an agent critique as a design-review score.
- R3 Real source corpus: agents may fetch publicly accessible pages (respect robots.txt
  and terms; nothing behind a login). Full bodies live only in the gitignored private
  evidence directory; git holds the manifest (URL, retrieval date, hash, labelled spans as
  minimal excerpts, missingness, rights status). Rights status is "pending human rights
  review" unless terms clearly permit retention.
- R4 Adzuna: no credentials exist (still true on 2026-10-28). Implement the adapter and its
  fixture contract; record the live integration as "unverified — no credentials". Adzuna
  stays optional (plan v1.1, Sprint 3 S3.3): if developer credentials are registered and
  stored under `CAREERWRIGHT_HOME` before Task 7 is dispatched, Task 7 qualifies the live
  integration instead. It is external data, still a local run; never put the credentials
  in a command argument, log or commit.
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
- R9 England option pack labelling (D1; spec section 11; plan section 9; ADR 0008):
  - Every surface that uses the pack (Roles, Skills, Options, Routes, Plan and every
    export) shows the pack's date and each record's review state.
  - A `proposed` record, whether from the pack before review or from live research, is
    explorable but never enters an unqualified "affordable and feasible" recommendation.
  - A pack record never fills a live field and is never shown as current.
  - Synthetic data stays labelled synthetic and never enters the pack.
  - Live research writes the same catalogue contract, `review_state: proposed`, inside its
    own workspace, never into the pack.
- R10 Human review sessions (plan section 10; ADR 0008). Three fixed sessions, each a
  dispatch precondition. The controller does not dispatch a task whose precondition session
  has not happened; it records "blocked: awaiting session N" in the progress ledger instead.
  An agent prepares each session's package under R2. Only the product owner's own record of
  a session establishes its outcome; an agent may transcribe that record, never supply it.
  - Session 1 (about 2 h). Before Task 8, and before any page body is retained beyond the
    source classes it permits (until then R3 governs retention). Closes H-06 as a rights
    policy for the permitted source classes of the corpus and the option pack, so agents can
    classify pages themselves (a page outside those classes, or not clearly within one,
    stays "pending human rights review"), and the H-12 checklist in ADR 0007. D1–D3 were
    confirmed by the product owner on 2026-10-28 and need no session time. The first task
    dispatched after session 1 transcribes its outcome: H-06 into the register and
    `corpus/README.md`, H-12 into ADR 0007's checklist and the register. Task 8 does it at
    the latest.
  - Session 2 (about 2½ h). After Task 11. Closes H-07 for Sprints 4–5 on the option pack
    and the TRACE-01 checker run on P01's real option set, and H-13, the formative
    comprehension session. Task 7c applies the H-07 record to the pack and publishes the
    reviewed version that later tasks use. From plan v1.2 it also closes H-01 for Sprint 2:
    the design review of the You chapter and the slate at 1440 px and 390 px, using the
    Sprint 2 checklist (`docs/reviews/sprint-2.md`). It tests scanning, understanding and
    choosing (one suggestion explained, one chosen) and records where the first screen
    hides the decision controls. Task 10 applies its findings first, and Tasks 10, 12 and 8
    build their chapters to them.
- R11 Language rules have a boundary (plan v1.2). The support screen's stems, the
  explanation validation's word lists, redaction's patterns, the pay, date and work-mode
  readers and the agency words grow only for a reproduced defect or an evaluation failure:
  - a reproduced defect is a probe, fixture or corpus page that shows the wrong result;
  - a hypothetical form is recorded as a known limit, not fixed.
  Prefer a fail-safe outcome (unknown, unclear, body not kept) to a new pattern. Keep every
  required safeguard and every accepted limitation as recorded. A reproduced leak of a third
  party's contact detail, or a pay value approved wrong, is a defect and is fixed. More
  exceptions do not make a rule understand language.
- R12 Evidence before polish (plan v1.2). From Task 7b to session 2 (Tasks 7b, 9 and 11)
  the critical chain takes priority. A refactor or hardening that no failing check, reproduced
  defect or Global Constraint requires goes to the final-review list in the progress ledger,
  never into these tasks.
  - Session 3 (about 1 h). Before Task 14 closes. Closes H-01 for Sprint 7, the design
    review, against what session 2 showed.

## Order, dependencies and dispatch preconditions (plan v1.1, ADR 0008)

Execution is sequential: the controller runs one implementer at a time. Where the
assessment handover (`docs/plan/l0-assessment-handover.md`) marks tasks as parallel (∥),
they have no dependency on each other and run one after the other, in either order; they
never run at once.

Dependency rules:

1. Task 6b after Task 6 (it extends Task 6's discovery). By controller ruling, Task 6c
   follows 6b and Task 7 follows 6c; neither depends on 6b's code.
2. Task 7d after Task 7, and Task 7b after Task 7d. Task 7b uses the Task 7 acquisition
   pipeline; Task 7d fixes its cancellation lock order before the pipeline runs further
   (plan v1.2).
3. Task 9 after Tasks 7 and 7b: its outcome mappings cite Task 7's SourceClaim spans, and it
   loads the pack in the format Task 7b defines. The handover's "7b ∥ 9" therefore runs 7b
   first.
4. Task 11 after Tasks 9 and 7b (its acceptance runs on the pack's P01 option set).
5. Session 2 after Task 11.
6. Task 7c after session 2 (it applies the product owner's H-07 record to the pack).
7. Tasks 10 and 12 after Task 7c (they score the live path against the reviewed pack);
   they have no dependency on each other or on Task 8.
8. Session 1 before Task 8, and before any page body is retained beyond the classes it
   permits.
9. Task 8 after Task 7c and session 1 (Task 11 and session 2 come before Task 7c).
10. Task 13a after Task 7c (the reviewed pack's instances). Task 13b after Task 13a.
11. Task 14 starts after Task 13b and after session 2's findings exist (the H-13 record),
    and closes only after session 3.
12. Task 15 after Task 14 has closed.
13. Task 16 after every remaining task (6b, 6c, 7, 7d, 7b, 7c, 8, 9, 10, 11, 12, 13a, 13b,
    14 and 15) and after sessions 1, 2 and 3: release qualification needs all six chapters.
14. Task 17 after Task 16 (plan v1.3): the manual describes the qualified candidate, and its
    small fixes are re-qualified on top of it.
15. The world (plan v1.4): Task W1 has no dependency (synthetic data only). Session W1
    after Task W1. Task W2 after session W1. Session W2 after Task W2. Tasks 10, 12, 8, 14
    and 15 also wait for session W2. Task 16 also waits for Tasks W1 and W2 and sessions
    W1 and W2.

Suggested order (plan v1.4, after session 2): W1 → session W1 → 7c → W2 → session W2 → 10
→ 12 → 8 → 13a → 13b → 14 (closes after session 3) → 15 → 16 → 17. Backend tasks (7c,
13a, 13b) may run while a session is awaited; interface tasks wait for session W2. The
v1.1 order was 6b → 6c → 7 → 7d → 7b → 9 → 11 → session 2 → 7c → 10 → 12 → 8 → 13a →
13b → 14 (closes after session 3) → 15 → 16 → 17. Session 1 can be held at any point before Task 8;
holding it before Task 7b lets 7b classify the pack's rights itself instead of leaving
every page "pending human rights review".

Dispatch preconditions: every remaining task card starts with a **Preconditions** line
naming the tasks and the human sessions it waits for (R10). A session that has not happened
blocks dispatch; it is never assumed, worked around or self-certified (R2).

Sprint reviews follow the order: the task that finishes a sprint writes its review, so
`docs/reviews/sprint-3.md` (Task 8) comes after `sprint-4.md` (Task 10) and `sprint-5.md`
(Task 12), and `sprint-6.md` (Task 13b) covers 6a and 6b. Each review states the order it
ran in.

## Current position and next tasks (2026-10-31)

**Complete and reviewed:** Tasks 1–6, 6b, 6c, 7, 7d, 7b, 9, 11, 7c and W1; Task W2's slices
W2A (the world layer and its design references) and W2B (the deterministic sources: the
type-ahead, usual skills, the skill-joined slate, the unexpected connection, the overlooked
strength run). **Held:** sessions 1, 2 and W1. The ledger
(`.superpowers/sdd/l0-sprint-tasks/progress.md`) has every commit range and ruling.

**In progress:** Task W2, slice W2C part 1 (the You chapter in the world): built
(166e4ef..6af1097), reviewed in two halves (design and experience; app, truth and tests), fix
round 1 committed (6af1097..f179d0f; `make check` and `make acceptance` pass on f179d0f). Its
scoped re-review has not run.

**The product owner's direction (2026-10-31), in their words:**
- "The visuals are important, but they must be subservient to having a practical, useful
  product."
- "I want to check that the development plan is still sensible, and get us back on track
  with the sprints, even if we have to refactor some of them to ensure coherency and
  pragmatism."
- "We can also start being a bit more generous with token use in human testing - I would
  like to use muse wonder for this."

**Next, in order:**
1. Task A1, the whole-solution audit (card below). No other task is dispatched until the
   product owner has approved the plan changes it proposes.
2. Then, unless A1 changes them: the W2C part 1 re-review, W2C part 2, W2D, session W2, and
   the suggested order above.

**Remaining Task W2 work** (A1 may cut, merge or reshape it):
- *W2C part 1:* a scoped re-review of fix round 1 against both reviews. Fix round 1's own
  concerns go with it:
  - On a phone, the band of world above the console (about 300 px) puts a long view's first
    decision a scroll away.
  - "Help me explore instead" still drops keyboard focus. This is older than W2C.
  - The moving-and-still identical-words test covers only the fixture workspace.
- *W2C part 2:*
  - The first answer's ignition, and the type-ahead's closest titles asked as "Careerwright
    couldn't match that title in ESCO. Is it one of these?"
  - The unexpected connection lit in the world (light and a joining trail), its shared
    skills one step away.
  - The overlooked strength's proposal and confirm step, and "usual in your role, not
    confirmed yet". A support turn holds back revelations: `held_back` (422
    `INSUFFICIENT_EVIDENCE`) is never asked for on a support turn, and its words never sit
    beside the support panel.
  - The strength's destinations come from the first slate only: align them with the
    horizon.
  - The world answers the chapter's decisions: suggestions drawn as rings with the open one
    singled out, and "Make this a target" previewing its destination before it is saved.
- *W2D:*
  - The world's requirement family in the register, and the Sprint W acceptance.
  - The frame re-measure on the busiest real scene and an unplaceable-name scene. Warn the
    product owner first: it opens a window.
  - Plain phrases for the route preview's "Economic cost" and "Direct spending", with the
    selected route's name placed first.
  - ADR 0014 decision 7's strip wording.
  - The phone openings list one per line, with stale and unknown captures.
  - Session W2's package and sheet, and `docs/reviews/sprint-w.md`.
- *Session W2's sheet (the product owner's decisions):*
  - The slate's provisional rules: at least 3 shared essential skills, Jaccard, best 30, the
    connection rule, the strength gate, the quotable fields and the "used" answer.
  - Work style: one word is not searched (REC1-03).
  - The too-general thresholds (more than 50 occupations, or more than 5 skills not named
    exactly) and the common answers they leave empty ("writing reports", "working in a
    team").
  - Searches read only a skill's main name ("operating farm machinery"); hyphens are read as
    spaces.
  - The specificity order, and each note's words ("main name", "added weight").
  - The discovery prompts, untested live.
  - Typography and colour: the Source Sans 3 body face, and leaf green (accept) beside
    destination orange under colour-blind simulation.
  - Layout: the tablet strip without work areas and budget; the helper lines cut or kept;
    the early sketch behind a disclosure; the tabs; Send as the bright action.
- *Parked for the final review:* titles that ESCO writes with "&" or accents don't match
  their plain spelling (`concept_key`, a migration-defined key). This sits with the three
  chosen-occupation normalisations and the earlier parked items (ledger lines starting
  "Parked").

## Task A1: whole-solution audit, coherence and pragmatism (the product owner's request, 2026-10-31)

**Preconditions:** none. Read-only on product code. It writes a report and proposes changes
to the development plan, this file and, where needed, the specification and `CLAUDE.md`. Each
change waits for the product owner's approval.

Answer four questions, with evidence:
1. **Intent:** does the solution as built and planned still deliver the original design's
   intended functionality? Map each specification capability, end to end, to built, planned
   or drifted, and name each drift.
2. **Coherence and pragmatism:** is it one clear product? Check that complexity earns its
   keep, that the honesty invariants are applied in proportion, and that the world serves the
   work, not the other way round (the product owner's direction above). Use the review
   history as evidence: where fix rounds went, and what they bought the person.
3. **The plan:** is the development plan still sensible? Propose re-ordering, merging,
   cutting or refactoring sprints and tasks so the practical, useful product comes first.
   Include the Sprint W gate (session W2 before Tasks 10, 12, 8, 14 and 15) and the remaining
   W2 work above.
4. **Muse Wonder for human testing:** `muse-wonder-1.0` is in
   `identity/model_registry.py`, and ADR 0003 left it unselected. Say where it is used, the
   budget per session, how each call is ledgered (R5), and what ADR 0003, the plan, the
   register and the test-model safeguards need.

Deliver:
- `docs/reviews/l0-audit-2026-10-31.md`: findings, each with evidence and a recommendation.
- The proposed plan changes.
- A one-page plain-words summary for the product owner. List only the decisions that are
  theirs, one sentence each, saying what "yes" does.

Nothing in the plan changes until they approve.

Acceptance: every specification capability is mapped. Every recommendation cites evidence.
The product owner has the summary.

---

## Task 1: Sprint 0 — technical spike and contracts (S0.1–S0.4)

Sprint card: "Sprint 0 Resolve the expensive uncertainties". Slice: S0.1, S0.2, S0.3,
S0.4. Spec sections 1 (BND-1), 16, 17 (ARC-1), 19.

Deliver:
- Minimal real scaffolding the spike needs (uv project under `backend/` with
  `backend/src/careerwright`, Python 3.12, Ruff, the chosen type checker, pytest) — no feature
  modules yet. A spike may live in `backend/spikes/` if it is not production code.
- `docs/adr/0001-l0-scope.md` recording the plan section 1 overrides (L0 vs M0).
- `docs/dependencies.md`: dependency matrix with exact versions to pin, checked against
  arm64 Docker images (PostgreSQL 16, Firebase Auth emulator container, Python 3.12, Node,
  pnpm).
- S0.2: check the current docs (plan section 12 links) and Meta's model catalogue and
  pricing first; record every Meta model the key can use with its capabilities, price and
  restrictions, and choose the test model and production model per R5. With the real key
  and a hard cap (≤ 15 live calls total for this task, of which ≤ 5 on the production
  model), prove through Pydantic AI's native Meta provider: structured (schema) output,
  search, streaming and usage reporting on the test model first, then confirm
  Standard-mode `muse-spark-1.3` (or the production model you qualified) access, schema
  output and streaming with the minimum calls. An invalid key must fail visibly (this
  costs nothing — do it first). Start `docs/evidence/live-usage.md` with per-call cost
  rows and a running total. If entitlement/model is blocked, say so (R5).
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

## Task 6b: Sprint 2 addition — span-cited "Why this could suit you" (S2.7, D3)

**Preconditions:** Task 6 complete. No human session.

Sprint card: "Sprint 2 Deliver conversation and career discovery", deliverable S2.7 (added
in plan v1.1). Spec sections 4 (REC-1, the model-written explanation paragraph) and 16
(privacy mode, spend); ADR 0007 decisions 4–7 and 10; ADR 0008 decision 4.

Deliver a model-written "Why this could suit you" beside each suggestion in a slate:
- At most one bounded model call per slate, never one per suggestion, as a run kind on the
  one bounded activity (ADR 0002), like discovery. Decide and record when a changed view
  (emphasis, exclusions) counts as a new slate; a view change never multiplies calls.
- The model may quote only the person's confirmed answers that the discovery pinned and the
  grounded ESCO occupation record. Every quotation is verified server-side as an exact span
  of its source. A quotation that does not verify, a claim that rests on no quotation, or
  a readiness, affordability or hiring claim is a validation problem: one repair, then
  `invalid_model_output`, with nothing stored as checked. The guards of ADR 0007 decision 7
  (no health condition, type, protected characteristic or percentage the person never used)
  apply, and the prompt carries the minimum subset (no name, place, money or hours; SEC-05).
- The deterministic provenance of ADR 0007 decision 6 (the answers and the search that found
  the occupation) stays underneath, is shown in every case and is what exports cite. The
  written text never changes a suggestion, its grounding, its place in the slate or the
  profile. A failed or invalid explanation is shown as unavailable, with its failure, never
  hidden or replaced silently.
- Model choice per MODEL-02: the Standard production model for non-synthetic workspaces,
  the test model for synthetic ones only; demo workspaces use a deterministic fixture
  explainer under the same contract, confined to demo like the other fixture models. Spend
  is reserved and reconciled like other runs (MODEL-08); nothing private enters a journal
  (ARC1-06).
- Live (R5): the fewest test-model calls on synthetic data that establish the contract, as
  a capped case in `make live-eval` or an explicit capped command, every call ledgered;
  never in `make check` or `make acceptance`.

Acceptance: REC1-11. Fake-provider tests for a misquotation, an invented answer, an
occupation fact ESCO lacks, a readiness claim, invalid JSON and a truncated response (one
repair, then a typed failure, with the deterministic provenance still shown); one call per
slate; exports cite the deterministic provenance; demo makes no outbound request (BND1-11).
Finish: amend ADR 0007 decision 6, both its title ("A suggestion's words come from facts,
not model prose") and its last sentence ("Model-written explanations are not used in L0:
grounding by construction was preferred to a second paid call whose prose would need its
own checks."), to point at ADR 0008 and this task; keep the `replaces` sentence before it,
which still holds. Update REC1-11 and add an addendum to `docs/reviews/sprint-2.md`.

## Task 6c: Sprint 0–1 visual corrections and the `next` age-exception removal

**Preconditions:** Task 6b complete (order). No human session. The `next` 16.4.1 exception
became removable at 2026-10-28T17:43Z (ADR 0005 decision 1).

Sprint cards: "Sprint 1 Build a polished local walking skeleton" (its review findings, plan
section 10) and "Sprint 0 Resolve the expensive uncertainties" (the signature compositions).
Spec sections 13 and 14.

Deliver:
- Sprint 1 findings (`docs/reviews/sprint-1.md`, "Open findings"):
  - V-01: each route card keeps "Conditional" beside its readiness, with the assessed-report
    requirement available there; never an unqualified "Ready in …". Do not carry this
    wording into computed routes.
  - V-03: phone Routes shows the first route card in the initial viewport; the synthetic
    warning stays unmistakable and secondary context moves behind disclosure; check that
    tablet route C is visible.
  - V-04: the phone route-sheet peek shows the route name, its condition, readiness and both
    cost figures, keeping the fixture label; capture peek and expanded states.
  - V-05: the data-mode select has a short option label and the full explanation in
    wrapping helper text; verify at 390 px and 200 % zoom.
  - V-06: Plan says plan selection is not in this build and makes its action's purpose
    explicit; it never implies that a fixture preview creates a plan.
  - V-09: visited rail marks are distinguished or explained so they cannot read as
    completed work.
  - V-10: the refused-account page has one headline; the recovery instruction is supporting
    copy.
- Sprint 0 findings (`docs/design/pre-review-sprint-0.md`, "Open findings"), in the app:
  - S0-V03: individual route cards keep their readiness condition (with V-01).
  - S0-V04: the selected stale route journey carries its old version and stale status into
    the phone peek.
  - S0-V06: unknown Routes keeps route B's known figures (9 months, £2,400 direct spending)
    and the More affordance.
  - S0-V07, Routes part: failure and unknown copy never push the first route behind the
    phone sheet. (The Roles app parts of S0-V05, S0-V07 and S0-V08 are Task 8's.)
- Correct the Sprint 0 compositions in `docs/design/compositions/` for S0-V01–S0-V08
  (Task 6 fixed the app for S0-V01, S0-V02 and S0-V08 in You and applied S0-V05's lesson to
  the slate; the Roles parts are Task 8's; the compositions still show all eight),
  recapture `docs/design/screenshots/` and re-run `pnpm run contrast` and
  `pnpm run screenshots`. Any new colour pairing goes into `contrast-pairs.json` and is
  measured.
- Recapture the affected app views at 1440×900, 768×1024 and 390×844, including route D/E
  cards and the layer 3 glyph (the Sprint 1 coverage gap Task 6 left). Update the
  dispositions in `docs/reviews/sprint-1.md`, `docs/reviews/sprint-0.md` and
  `docs/design/pre-review-sprint-0.md`. Agent pre-review only (R2): the human check stays
  "not run — requires human".
- Remove the `next` 16.4.1 `minimumReleaseAgeExclude` exception (ADR 0005 decision 1,
  removal step): delete it from `apps/web/pnpm-workspace.yaml`; `cd apps/web && pnpm install
  --frozen-lockfile` must pass with no lockfile change; then remove the exception from ADR
  0005, `docs/dependencies.md` and ARC1-03, and propose the matching `CLAUDE.md` edit for
  the user's approval.

Acceptance: each finding's disposition names its capture or test; axe and overflow checks
clean at the three viewports; the composition screenshots and contrast checks pass; the
frozen install passes with no lockfile change.

## Task 7: Sprint 3 — evidence acquisition backend (S3.1–S3.4, reduced S3.6)

**Preconditions:** Task 6c complete (order). No human session. Adzuna credentials under
`CAREERWRIGHT_HOME` at dispatch decide S3.3's live qualification (R4).

Sprint card: "Sprint 3 Make the evidence and opportunity map real". Slice: S3.1, S3.2,
S3.3, S3.4, S3.6 and their acceptance items. Spec sections 5, 6, 7, 11 (TAX-1, AIR-1).

Scope notes (plan v1.1, ADR 0008):
- S3.6 is reduced: deliver the AI-resilience assessment record model, its publication-state
  checks, the lower-bound filter and the unscored state, qualified with one conspicuously
  labelled fixture record. Keep the pinned AI-evidence and mapping imports (AIR1-03,
  AIR1-07, AIR1-11, TAX1-07), so exposure-only evidence shows with resilience unscored. The
  review pipeline is data entry through the record model: a model proposal can only be a
  proposed record (AIR1-04), and a record publishes only when an accountable reviewer's
  recorded decision passes the publication checks (AIR1-02). L0 publishes no reviewed real
  record unless an accountable reviewer exists (H-10); until one does, every real role stays
  unscored.
- S3.5 (the Roles chapter) is Task 8, which runs after Task 11.
- The corpus is curated in Task 7b, not here. This task still owns the attempt cases X01 and
  X02 and the source permission manifest (OI-11) in `corpus/manifest.json`, and must leave a
  pipeline Task 7b can run the 33 pages through. No extraction is tuned on a real page
  before Task 7b assigns its template family and split (OI-09 moves to Task 7b).
- Live research writes the catalogue contract, `review_state: proposed`, inside its own
  workspace (R9).

Deliver SourceAttempt/SourceClaim records (permitted retention, field spans, hashes,
publication/retrieval/effective dates); pinned ASHE imports (R7) and reviewed UK-SOC
mappings with explicit unresolved crosswalks; bounded Meta search discovery; keyless
Scrapling HTTP fetch/parse in the restricted acquisition worker (scheme, resolved IP,
redirects, content type, size, time checks; structured fields first, model extraction
only where needed); manual pasted text as a separate input route; Adzuna adapter + fixture
contract (R4); syndicated-job dedupe, agency vs employer, multi-city counted once;
closure/freshness (jobs 24 h, fees/intakes 7 d, funding 48 h; failed refresh never extends
validity), favourites, cancellation, resumable incremental results; AI evidence/mapping
packs and the reduced publication-state machinery above (reviewed ranges only, otherwise
unscored; lower-bound filtering; unscored visible by default in exploration). SSRF tests
with a controlled server incl. IPv6/encoded addresses; prove the fetcher has neither user
secrets nor private profile access; failed fetch never becomes "no vacancies".

## Task 7d: Sprint 3 — cancellation lock order (plan v1.2)

**Preconditions:** Task 7 complete. No human session.

Source: the intermediate code review (`docs/reviews/intermediate-code-review-2026-10-29.md`,
point 1) and ADR 0009's open item on the existing lock pattern. Cancelling a run and a
worker publishing progress can take database locks in opposite orders:
- `cancel_run` locks the workspace row `FOR UPDATE`, then takes a key share on the run's
  row through the `run_cancellations` foreign key;
- a worker transaction can hold the run's row `FOR UPDATE`, then write an event that
  updates the workspace row.

PostgreSQL then aborts one transaction, and the person has to cancel again. The acquisition
cascade (ADR 0009 decision 15) can do this for up to five more runs.

Deliver:
- First, a concurrent regression test that reproduces the deadlock, run red: two connections,
  a cancel against a worker publishing an event, for an ordinary run and for an acquisition
  with started extraction runs.
- One lock order for every transaction that can meet a cancel, with the cancellation lock
  first (ADR 0009 decision 15). Do not add a retry loop in place of the order.
- Correct ADR 0009's open item and decision 15 to say exactly what holds. Update the
  register rows it closes (DUR-05 and any other).
- Keep `application_version` unless a workflow's step sequence changes.

Acceptance: the regression test fails before the change and passes after it, repeated
enough times to show the race, and no other test changes its expectation. `make check` and
`make acceptance` pass.

## Task 7b: Sprints 3–5 — the England option pack (curation and labels)

**Preconditions:** Tasks 7 and 7d complete (the acquisition pipeline, with its lock order
fixed). No session is required to start. Until session 1 has happened, R3 governs retention: page bodies only in the private
evidence directory, rights "pending human rights review" unless the terms clearly permit
retention. After session 1, classify each page against its permitted source classes,
recording the class and the terms relied on; a page outside them stays pending (R10).

Sprint cards: the corpus items of "Sprint 3", "Sprint 4" and "Sprint 5", and plan section 9
("Required corpus", "The England option pack", "Evaluation outputs"). Spec sections 6, 10,
11 (the M0 option pack), 18 and 20 ("M0 source corpus and acceptance").

Deliver:
- Choose the 20 job postings, 10 course pages and three funding pages for the targets of
  P01–P05 (`fixtures/m0`), filling slots J01–J20, C01–C10 and F01–F03 of
  `corpus/manifest.json` and keeping the case types each slot intends (duplicates, closed
  jobs, predicted or missing pay, snippets, drift, hostile page instructions, misleading
  course titles, teaching without assessment, conditional grants; OI-04, OI-05). Fetch them
  under R3 through the Task 7 pipeline. Take the first capture of the drift case (J10, OI-06);
  Task 8, the last consuming task, takes the second.
- Label every page: values with units or currency, spans as offsets or stable selectors
  with minimal excerpts, missingness, expected unknowns and expected failure states. Assign
  each page's template family and holdout split before any tuning uses it (OI-09).
- Build the pack (R9): versioned and dated catalogue records in the spec section 18 shapes
  (LearningOption and Offering, FundingInstrument, SkillRequirement rows,
  `PlanAction.outcomes` per OUT-1) with SourceClaims, rights status, `review_state` and
  dates, every record `review_state: proposed`. Define its file format with a schema and a validator in the fast
  checks, like the fixture validator. Tasks 9 and 11 load it through their domain models; a
  format change needs a pack version bump. It is an immutable public evidence pack:
  fetched and hash-checked like ESCO (R7), or committed only if it is small and its rights
  permit. No page body enters git unless its class permits it; no synthetic value enters
  the pack.
- Early accuracy read (plan v1.2: real evidence is the next proof of progress). Once labels
  and splits are assigned, run the Task 7 pipeline's deterministic path once over the
  development-split pages. That path is structured data and Adzuna, with no model call; the
  live model path is scored later, in Tasks 8, 10 and 12 (R5). Report field by
  field: correct, incorrect, missing and unsupported, with denominators, against the labels.
  Label the report "unreviewed labels, development split". Never tune on holdout pages
  (OI-09). A pipeline defect it reproduces is fixed under R11; anything else is reported.
- Hand the review to session 2: a package listing each record by persona target with every
  consequential field (salary basis, fees, dates, deadlines, award status, outcome levels)
  beside its span, as yes/no questions for the H-07 reviewer. Task 7c applies the answers.
- Update `corpus/manifest.json`, `corpus/README.md` (owners, counts, open items) and the
  register rows TEST1-09, OUT1-10 (labels), OPTN-08 and OPTN-10.
- No live Meta call is needed. Any that is used is test-model, capped and ledgered (R5).

Acceptance: 33 pages in the manifest with URL, retrieval date, hash, rights status, template
family, split and labels; the pack validates against its schema; every record is `proposed`
and dated; nothing synthetic in the pack; no unpermitted body in git; the early accuracy
read is reported with its denominators; the session 2 package is ready. `label_review` and rights review stay "not run — requires human" until a person
records them.

## Task 7c: Sprints 3–5 — publish the reviewed option pack

**Preconditions:** session 2 held, with the product owner's own H-07 record (R10); Task 11
therefore complete. Runs before Tasks 10, 12, 8 and 13a, which use the version it publishes.

Sprint cards: the corpus items of "Sprint 3", "Sprint 4" and "Sprint 5", and plan section 9
("The England option pack"). Spec sections 10, 11 (the M0 option pack) and 18.

Deliver:
- Apply session 2's recorded decisions to the Task 7b records, transcribing the product
  owner's own H-07 record only (R10); the agent decides nothing.
  - An accepted record becomes `review_state: reviewed`, naming the reviewer, the decision
    date and session 2.
  - A rejected record is excluded from the published version; its reason stays in the
    review record.
  - A value the reviewer corrected is changed with its span cited and the decision named.
  - A record the reviewer did not decide stays `proposed`: explorable, never in an
    unqualified result (R9).
- Publish a new dated, versioned pack (a version bump), validated by the Task 7b validator
  and distributed under the same rule as Task 7b (R7, or committed if small and its rights
  permit). The earlier `proposed` version stays readable and unchanged.
- Update `corpus/manifest.json` and `corpus/README.md` from the record: OI-08 and each
  page's `label_review`, plus any rights decision taken at the session. Update the register
  rows OPTN-10, TEST1-09 and OUT1-10.
- Hand the reviewed version to Tasks 10, 12, 8 and 13a: its version and hash, which each
  pins and scores or solves against (TEST1-13, OPT1-16).
- No live call.

Acceptance: the published version validates; every `reviewed` record traces to a decision in
the product owner's record; no rejected record is in it; every changed value is span-cited;
undecided records stay `proposed`; the earlier version is unchanged.

## Task W1: Sprint W — the spike of three directions (SW.1)

**Preconditions:** none (plan v1.4). Synthetic data only. Ends at session W1, held by the
product owner: until they have chosen, Task W2 is not dispatched.

Sprint card: "Sprint W Build the world". Slice: SW.1. Read plan section 4 in full first;
the product owner's words there are the brief.

Deliver section 4's three directions (Growth, Horizon and Circuit). Each shows the same
first ten seconds (one light, one plain question, the first answer igniting the origin and
growing the first trails) and one revelation on synthetic data, labelled as such. Each has
its still version (reduced motion and calm mode) and a visible pause control. Measure each
direction's frame times on this Mac in Chrome (p50 and p95, busiest scene: 100 job nodes,
their trails and ambient particles) and its first-frame time, against the plan's headroom
budget for this faster Mac (p95 within 8 ms). Compare the WebGL library
candidates and two or three licensed display faces, and recommend one of each. The spike is
throwaway: it starts with one command, makes no external request, lives outside the product
code (its location is the implementer's call) and is labelled as a spike. Any dependency it
pins is at least 14 days old. Prepare session W1's package in plain words (CLAUDE.md
"Talking to the user"): how to open each direction, what to try in two minutes, and the
questions to answer (which direction, or which mix, in their words; whether sound is
wanted). Agent pre-review only (R2).

Acceptance: the three directions open from one command; each shows the same first ten
seconds and revelation, and the same words with motion off; frame and first-frame times
reported with device, browser and scene; no external request; the package is ready.

## Task W2: Sprint W — the world in the app (SW.2–SW.6) + Sprint W review

**Preconditions:** session W1 held, with the product owner's own choice recorded (R10).
Ends at session W2 (H-01 for Sprint W): until it is held, and every rubric category has
reached at least 4 (plan section 5), Tasks 10, 12, 8, 14 and 15 are not dispatched.

Sprint card: "Sprint W Build the world". Slices: SW.2–SW.6, the acceptance and the
coherence review. Plan section 4; spec sections 3, 7, 13, 14 and 15 as section 4 overrides
them; ADR 0014 (record the spike's choices there).

Deliver, in this order: the design references for the chosen direction (SW.2), replacing
the Sprint 0 compositions, with every new pairing in `contrast-pairs.json` and the mirror
in `apps/web/src/design` updated; the world layer and the still world in the app, behind
all six chapters (SW.3); the You chapter rebuilt in the world with session 2's design
findings applied (SW.4), transcribing the product owner's record and deciding nothing on
their behalf (R2); the first moments and the two revelations (SW.5): the unexpected
connection from the slate, joined by shared essential skills and checked on "data analyst"
and the five personas (amending ADR 0007), and the overlooked strength as a new bounded run
kind whose quotation is span-verified and confirmed by the person (live calls R5; tests use
the test model or fixtures only); the new requirement family in the register
(SW.6). Prepare session W2's package: captures at the three viewports, motion on and off,
and the rubric with the three v1.4 questions. `docs/reviews/sprint-w.md`, completed with
session W2's outcome from the product owner's own record.

Acceptance: the plan's Sprint W acceptance; `make check` and `make acceptance` pass; the
design references' contrast and screenshot checks pass.

## Task 8: Sprint 3 — living opportunity map and the job corpus (S3.5) + Sprint 3 review

**Preconditions:** Task 7c complete (the reviewed job values this task scores against;
Task 11 and session 2 come before it); session 1 held (H-06 rights policy; R10); session W2
held (plan v1.4). In the suggested order it runs after Task 12.

Sprint card: "Sprint 3 Make the evidence and opportunity map real". Slice: S3.5, the
20-job corpus portion, remaining acceptance, the coherence review. Spec sections 5, 7
(VIS-1), 13, 14.

Scope notes (plan v1.1, ADR 0008): the Roles chapter runs after the Sprint 4–5 backends
because, in L0, it has no live vacancy data and every role is unscored; its deliverable is
unchanged. It consumes the option pack's 20 job postings, curated and labelled by Task 7b,
in the reviewed version Task 7c published; it does not curate pages.

Deliver the Roles chapter as its place in the world, the horizon, with its moment, the
unexpected connection (plan section 4; Task W2's design references), keeping VIS-1's
hierarchy and industry shown by glyph and label (ADR 0014): SVG/D3 dendrite with stable
anchors, company expansion, up to 100 visible job nodes, explicit aggregation counts;
numeric salary and AI-range filters; pay lanes / pay lens; mobile-first list; one shared
selection and filter contract across list, map and pay lens; focus retention and keyboard
actions; graph distance never implies commute feasibility. Apply the Roles findings of
the Sprint 0 critique (`docs/design/pre-review-sprint-0.md`, "Open findings"):
- S0-V05: an unknown card's heading says that preference fit is not assessed, never
  "Matches your preferences".
- S0-V07, Roles part: failure and unknown copy never push the first listing behind the
  phone sheet.
- S0-V08, failed Roles: one filled primary action per view.

Show the pack's date and review states wherever its postings appear (R9). Run the pack's 20
job postings (closed jobs, missing/predicted pay, snippets, duplicates, drift and hostile
page instructions) through the pipeline, taking the drift case's second capture (J10). Score the live path, pointed at
the same pages, field by field against the reviewed values: correct, incorrect, missing and
unsupported, with denominators (TEST1-13; live calls R5). If no earlier task has done it,
transcribe session 1's outcome from the product owner's own record (R10): H-06 into the
register and `corpus/README.md`, and H-12 into ADR 0007's checklist and the register.
Second visual review package (sparse and dense data) per R2. `docs/reviews/sprint-3.md`.

## Task 9: Sprint 4 — capability model, protected gates and outcomes (S4.1–S4.6 backend)

**Preconditions:** Tasks 7 and 7b complete (Task 7's SourceClaim spans; the pack format
Task 7b defines, which this task loads). No human session.

Sprint card: "Sprint 4 Build trustworthy skills and outcome assessment". Slice: the domain
and API for S4.1–S4.6 and their acceptance items. Spec sections 8, 9, 10 (MAP-1, OUT-1,
RDY-1).

The option pack's SkillRequirement rows and `PlanAction.outcomes` load through this task's
domain models in the Task 7b format. Outcome and requirement records carry `review_state`,
and a `proposed` record never supports an unqualified readiness result (OPTN-09, R9).

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

**Preconditions:** Task 7c complete (the reviewed pack, after session 2's H-07 on its
course outcomes; Task 11 comes before it); session W2 held (plan v1.4, R10). No dependency
on Task 12 or Task 8.

Session 2's Sprint 2 design findings are applied by Task W2 (plan v1.4). Build the Skills
chapter as its place in the world, with its moment, the overlooked strength (plan section
4; Task W2's design references): initial presentation short, evidence one step away.

Sprint card: "Sprint 4 Build trustworthy skills and outcome assessment". Slice: the Skills
chapter UI, the question flow UI, the ten-course corpus labels, remaining acceptance, the
coherence review. Spec sections 8, 9, 13, 14.

Deliver the Skills chapter: demonstrated / self-reported / planned / unresolved
requirements, behavioural anchors, inspectable evidence, shared questions across targets,
visibly protected gates, pause/stop, unresolved coverage without an employability
percentage; direct edits and chat proposals through the same contract. The ten course pages
and their outcome labels are the option pack's (Task 7b, in the reviewed version Task 7c
published), including misleading titles and teaching without assessment; this task
consumes them and curates nothing. Review false-positive readiness mappings individually (any unsupported
consequential outcome blocks publication of the affected route). Show the pack's date and
review states wherever its records appear (R9). Score the live path, pointed at the same
course pages, field by field against the reviewed values: correct, incorrect, missing and
unsupported, with denominators (TEST1-13; live calls R5). Record H-07's Sprint 4 part from
the product owner's own session 2 record. `docs/reviews/sprint-4.md`.

## Task 11: Sprint 5 — offerings, funding, monthly compiler and ledgers (S5.1, S5.2, S5.4–S5.6)

**Preconditions:** Tasks 9 and 7b complete. No human session; this task prepares the
session 2 package.

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

The option pack's LearningOption, Offering and FundingInstrument records load through this
task's domain models in the Task 7b format, with `review_state` kept: a `proposed` record
never enters an unqualified "affordable and feasible" result (OPTN-09, R9). Acceptance
gains the real option set (plan v1.1, P2; TEST1-14): the same checker runs on at least one
real option set for P01's target from the pack, every consequential field span-cited, with
its human review left to session 2 (H-07).

Finish: the session 2 package (R10, R2), ready for the product owner. For H-07, yes/no
questions on the pack records (from Task 7b) and on the checker's result for P01's real
option set, each field beside its span. For H-13, the formative session's surfaces (the
fixture route comparison and the TRACE-01 ledger as existing captures or Storybook
stories), its three questions (the cost shown, what "conditional readiness" means, what is
uncertain) and a record sheet. Record each item as "not run — requires human".

## Task 12: Sprint 5 — option review checkpoint and funding corpus + Sprint 5 review

**Preconditions:** Task 7c complete (the reviewed pack; session 2, with its H-07 and H-13
records, and Task 11 come before it); session W2 held (plan v1.4, R10). No dependency on
Task 10 or Task 8.

Build the Options chapter as its place in the world, with its moment, a gap's first
credible bridge (plan section 4; Task W2's design references).

Sprint card: "Sprint 5 Compile real options into an honest monthly model". Slice: S5.3,
the Options chapter UI, the three-funding-page corpus, remaining acceptance, the
coherence review. Spec sections 10, 13, 14.

Deliver the Options chapter per the design: curated comparison by gap, pin/exclude,
provider provenance, conditional funding, missing critical fields, scope bounds,
removed-candidate counts, explicit review checkpoint; when limits are exceeded ask the
user to retain variants — never silently truncate to the first 24 options or two intakes.
Show why a route may fail workload, payment or cash constraints using the Task 11 model.
Show the pack's date and each record's review state, and keep `proposed` records
explorable but out of any unqualified "affordable and feasible" result (R9, OPTN-08,
OPTN-09). The three funding pages are the option pack's (Task 7b, in the reviewed version
Task 7c published), consumed, not curated. Score the live path, pointed at the pack's
funding pages, field by field against the
reviewed values: correct, incorrect, missing and unsupported, with denominators (TEST1-13;
live calls R5). Record session 2's outcomes from the product owner's own record: H-07's
Sprint 5 part, TEST1-14, and H-13, whose dangerous misunderstandings become Task 14 scope
inputs. `docs/reviews/sprint-5.md`.

## Task 13a: Sprint 6a — enumerator, checker, oracle and layers on instances that complete (S6.1, S6.2, S6.5–S6.7)

**Preconditions:** Task 7c complete (the reviewed option pack it solves on; Task 11 and
session 2, with the reviewed TRACE-01 checker, come before it; R10).

Sprint card: "Sprint 6a Prove the optimiser and layers on instances that complete". Whole
sprint. Spec section 12 (OPT-1, including "Consequence of the M0 limits", ROU-1, FIN-1,
RDY-1), 20 (TEST-1).

Deliver canonical DFS (skip or one reviewed offering per concept, ≤ 6 selected actions,
DAGs/dates without equivalent permutations, all gates/timetable/cash/workload checks through
the Task 11 rules); only provably sound pruning with documented proofs; every distinct
feasible schedule encountered kept, dominated ones included, and F1–F3 computed over that
archive by simple iterative nondominated peeling; family grouping for presentation only;
search coverage (`complete` only after exhausting the declared tree, else
`budget_truncated`, never infeasible); candidate evaluation with no network, LLM or ORM
access; independent Cartesian oracle and independent route checker sharing no code with the
candidate implementation. Reach complete coverage on TRACE-01, the A–I fixture and
pack-scale instances built from the reviewed pack version Task 7c published. Regression
families TRACE01 (layers), DIRECTAI, PARETO, FAMILY and the complete-coverage parts of
LIMITS.

Report (in the task report, for Task 13b and Task 14): the measured instance sizes
(concepts, starts per concept, months) at which complete coverage is reached with the
implemented sound pruning, with expanded-state counts and times, and the largest sizes that
complete within the M0 limits (1,000,000 states, 30 s). A measurement run stopped before
completion is "not complete at that size", never infeasible (OPT1-16).

## Task 13b: Sprint 6b — durable archive, caps, child process and ranking benchmark (S6.3, S6.4, S6.8) + Sprint 6 review

**Preconditions:** Task 13a complete. No human session.

Sprint card: "Sprint 6b Make the search durable and bounded at full scale". Whole sprint.
Spec section 12 (OPT-1, ROU-1), 17 (the cancellable solver process), 20 (TEST-1).

Deliver the versioned disk-backed archive of every distinct feasible schedule (atomic
checkpoints, idempotent solve identity, resume-or-restart under a new attempt ID); 30 s /
1,000,000 states / 50,000 feasible caps with exact stop reasons, archive persistence
counted in the budget; separate rank stage; an efficient two-objective layering qualified
against Task 13a's iterative peeling, equal to it on every instance that completes;
cancellable optimiser child process run durably via DBOS, with cancellation reaching it.
A truncated result leads with "Best trade-offs found", states the instance size and names
the narrowing (fewer concepts, one start, a shorter horizon) that Task 13a's measured sizes
suggest (OPT1-15). Regression family LIMITS (caps, cancellation, truncated empty).
Benchmark 50,000-point ranking. `docs/reviews/sprint-6.md`, covering 6a and 6b.

## Task 14: Sprint 7 — coordinated route comparison (S7.1–S7.6) + Sprint 7 review

**Preconditions:** Task 13b complete; session 2's findings exist (the H-13 record, read as
scope input); session W2 held (plan v1.4). Closes only after session 3 (H-01 for Sprint 7; R10): until the product owner
has held it, the task stays open with its review package ready, and Task 15 is not
dispatched.

Sprint card: "Sprint 7 Make route comparison the signature experience". Whole sprint.
Spec sections 12–14 (VIS-2, ROU-1, AIR-1).

Scope inputs (plan v1.1): every dangerous misunderstanding recorded at session 2 (H-13)
is addressed or explicitly carried with a reason. Truncated coverage is the expected case
near the bound (OPT1-15): lead with "Best trade-offs found", state the instance size and
name the narrowing that would let the search complete, using Task 13a's measured sizes. Show
the option pack's date and review states wherever pack records appear in a route (R9).

Deliver the Routes chapter as its place in the world, with its moment, the credible route
(plan section 4; Task W2's design references), using real solver output:
per-target discrete time–cost scatter with cost definition/baseline/horizon/currency/
bounds/coverage beside the chart; readable F1–F3 with family grouping and named dominance
explanations; one documented deterministic comparator rule; stress scenarios shown
separately; exact numeric inputs + keyboard sliders; view filtering preserves ranks;
explicit reranking; linked Gantt, step cards, monthly financial table, evidence drawer;
section 4's motion with its still version; paginated archive and bounded projection
with shown/total counts. Property and browser tests for selection/filter consistency;
TRACE-01 renders A/B/C F1, D F2, E F3; A–I fixture uses direct-spending labels; measure
interaction budgets. Third visual review package (R2), prepared for session 3 and checked
against what session 2 showed. `docs/reviews/sprint-7.md`, completed with session 3's
outcome from the product owner's own record.

## Task 15: Sprint 8 — chosen plan, progress, revision and exports (S8.1–S8.6) + Sprint 8 review

**Preconditions:** Task 14 closed (after session 3, and so after session W2). No further
session; H-04 (Safari, print) is recorded "not run — requires human" with its checklist (R2)
and is not a dispatch precondition.

Build the Plan chapter as its place in the world, with its moment, committing to the chosen
path (plan section 4; Task W2's design references). Print stays light and ink-efficient.

Sprint card: "Sprint 8 Turn a selected route into a durable plan". Whole sprint. Spec
sections 11, 15 (FIN-1, AIR-1).

Exports also carry the search coverage with its instance size and truncation disclosure
(OPT1-15) and the option pack's date and review states (R9).

Deliver immutable PlanVersion snapshots; Plan chapter (overview, one next action,
progress bands, rest/reschedule; planning progress vs evidence vs real-world activity);
dependency invalidation and proposed revisions with old/new diff; replanning the remaining
horizon with explicit accounting bases; browser print CSS, JSON and ICS from one
serialisable snapshot with sensitive-detail omission; ICS semantics (stable UID, sequence,
proposed conditional events, DST and all-day correctness verified with an independent
parser). TRACE-01 route B agrees across screen, print and JSON. Workspace deletion across
snapshots, exports, cache and workflow references. `docs/reviews/sprint-8.md`.

## Task 16: Sprint 9 — local release qualification and handover (S9.1–S9.6)

**Preconditions:** every remaining task complete: 6b, 6c, 7, 7d, 7b, 7c, 8, 9, 10, 11, 12,
13a, 13b, 14, 15, W1 and W2 (release qualification needs all six chapters); sessions 1, 2,
3, W1 and W2 held (R10). The Sprint 9 human gates (H-01, H-03, H-04, H-05, H-08) are prepared as
checklists and recorded "not run — requires human" (R2); none is a dispatch precondition.

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

## Task 17: Sprint 10 — operator's manual and friction pass (S10.1–S10.5)

**Preconditions:** Task 16 complete. No human session. H-14, a person following the manual,
is prepared as a checklist and recorded "not run — requires human" (R2); it is not a
dispatch precondition.

Sprint card: "Sprint 10 Write the operator's manual and smooth the friction it finds" (plan
v1.3, added at the product owner's request on 2026-10-29). Spec sections 1 (the local
boundary), 15 and 19 as the operator meets them; plan sections 2 and 5.

Deliver:
- The manual in `docs/manual/`, covering what S10.1 lists, written for the operator, not a
  developer. Every command and on-screen word in it is the build's own: commands from the
  command contract, words from `src/lib/vocabulary.ts`. Screenshots use synthetic data only,
  labelled, at 1440 px and 390 px.
- Write it by doing. Follow every procedure from a fresh checkout and a blank workspace, in
  the real browser, in demo mode and in a capped live mode (test model, synthetic persona,
  a new scope within R5's per-scope cap, every call ledgered; no production model). Log
  every friction point in `docs/reviews/sprint-10-friction-log.md` with its steps, evidence,
  severity (blocks, slows, annoys) and disposition.
- Fix each friction point that a small change smooths. A small change alters no API
  contract, schema, migration, workflow step sequence, deterministic computation or
  verified requirement's behaviour. Each fix gets a test or an updated capture, and the
  manual describes the fixed behaviour. Rulings R11 and R12 still apply: copy and
  wording fixes are in scope, and new linguistic rules are not.
- For a friction point that needs more, write a proposal only when conviction is high that
  its benefit outweighs its cost. It names whom it affects and how often, what it removes,
  the change, its risk and effort, and the manual's workaround until it is built. The
  controller brings each proposal to the product owner as a yes/no decision. Nothing
  larger is built in this task without that decision; an approved proposal becomes its own
  task. Every other point is logged as known friction with its workaround.
- A docs check in `make check` fails when:
  - a `make` target named in the manual is missing;
  - an error code in `vocabulary.ts` is missing from the troubleshooting chapter;
  - a referenced screenshot is missing.
- Add register rows for the manual and for H-14. Correct the runbook where the walkthrough
  shows it is wrong.
- Re-qualify: run `make check`, `make acceptance` and Task 16's automatable checks on the
  final commit, and add a manual-and-friction addendum to
  `docs/release/L0-release-report.md`. A new candidate tag only with the product owner's
  approval. `docs/reviews/sprint-10.md`.

Acceptance: the manual covers every S10.1 topic. The docs check passes. Every friction point
has a disposition (fixed, proposed or known) and every fix has its test. Each proposal states
its cost and benefit. The fast and full checks pass on the final commit. H-14 stays "not run —
requires human" until a person records it.
