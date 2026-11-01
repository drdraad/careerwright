# L0 sprint tasks (execution breakdown)

This file breaks `docs/plan/development-plan.md` (the local development plan, v1.4) into
implementation tasks for agent execution. Authority order: product specification
(`Careerwright_Product_Specification.md`, v1.3) → development plan local overrides → this file.
Tasks 1–6 (Sprints 0–2) are complete. The remaining tasks follow the order, dependency
rules and dispatch preconditions below (ADR 0008).
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

---

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
