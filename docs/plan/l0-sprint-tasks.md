# L0 sprint tasks (execution breakdown)

This file breaks `docs/plan/development-plan.md` (the local development plan, v1.6) into
implementation tasks for agent execution. Authority order: product specification
(`Careerwright_Product_Specification.md`, v1.3) → development plan local overrides → this file.
The remaining tasks follow the order, dependency rules and dispatch preconditions (ADR
0008), as Task A1 amended them with the product owner's approval of 2026-10-31, and as plan
v1.6 amended them with the product owner's school-leaver decisions of 2026-11-01. The
controller keeps them, with what is done and what comes next, in
`planning/controller-state.md` (cards cite them as "rule N"); the live ledger is
`planning/progress.md`. This file adds task slicing, environment facts and standing rulings only; it never
relaxes the plan or the specification.

Each task names its sprint card. Read that card in `docs/plan/development-plan.md`
in full (deliverables, acceptance, coherence review) and the plan's shared sections
listed under "Always read". Then read the specification sections the card cites
(`grep -n '^#' Careerwright_Product_Specification.md` lists them; read only what you need).

## Always read

- `docs/plan/development-plan.md` sections 1 (boundary), 3 (architecture), 4 (the
  experience) and 7 (testing), plus your sprint card. Add section 5 (visual and usability
  acceptance) for screen work, and sections 8–10 (regression register, evidence
  qualification, sprint completion procedure) for the task that closes a sprint. Read any
  other section your card names.
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
    WCAG 2.2 AA target. Practical first: "The visuals are important, but they must be
    subservient to having a practical, useful product" (the product owner, 2026-10-31).
    Where the world and the decision path compete, the path comes first: a chapter's
    working view (its words, choices and numbers) ships before its moment, and the world
    never pushes a decision off the first screen. Until the decision path works end to end,
    chapters are built to the world's design references with exact states and words; their
    moments follow in Task M. A screen that works but is bland fails the moments review
    (Task M) and the release review.
12. Tests assert contracts and invariants, not implementation shape or exact LLM prose.
    Never soften assertions to get green. SQLite is not a substitute for PostgreSQL.
    A test that could not start or collected nothing is not evidence.
13. Every sprint's last task writes `docs/reviews/sprint-N.md` following plan
    section 10 (six questions + the card's coherence question), distinguishing
    passed / failed / blocked / not run.

## Environment facts (a Linux cloud container, from 2026-11-01)

The product is Careerwright (called Nessa until 2026-10-30). The build moved from the product
owner's Mac to a Claude Code cloud container on 2026-11-01. The machine note,
`planning/env-cloud.md`, has the details; where an older file names a Mac path or branch,
read it as below.
- Main tree: `/home/user/careerwright`. Worktrees: `/home/user/careerwright-wt/<id>`, branch
  `wt-<id>`.
- Integration branch: `claude/confident-ramanujan-ux3saw` (the controller's;
  `l0-local-release` was merged into `main` on GitHub). Only the controller moves it.
- Node 24 is at `/opt/node24/bin`, with pnpm 10.33.2 through corepack. Start every shell
  command that runs node or pnpm (including `make check`) with
  `export PATH=/opt/node24/bin:$PATH;`. The `/opt/node22` on the default PATH is the wrong
  version.
- Python 3.12 for the backend: `backend/.venv` (built with `uv sync --locked`). Never use
  another Python for the backend.
- Fast checks: `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`. The container
  exports both Adzuna variables, and one test reads the process environment. Never print
  either value.
- Docker: PostgreSQL 16 and the Firebase Auth emulator run only in containers. The
  controller starts `dockerd` and builds the images with `planning/cloud-build-images.sh`
  (the build shim: the session proxy and its CA, at build time only). Implementers never
  start Docker, pull or build images. The controller runs `make acceptance` once per batch,
  under the lock `/home/user/careerwright/.superpowers/acceptance.lock`; report it as "not
  run: the controller runs acceptance". A focused stack or integration test runs only when
  your dispatch asks for it, under the same lock.
- Chromium for the acceptance journeys: `CAREERWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium`
  (opt-in in `apps/web/playwright.config.ts`) runs them on the machine's own Chromium. Never
  reinstall Playwright's browsers here.
- Web requests and live calls: the controller makes every web fetch and every live call.
  Implementers and reviewers make none.
- `META_API_KEY` and the Adzuna credentials are in `/home/user/careerwright/.env`
  (gitignored). Never read it, print a key, echo it, pass it as a command argument, write it
  elsewhere, or commit it; code and tooling load it themselves.
- Git: commit on the branch your dispatch names, with messages ending
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push. Never commit
  `.env`, key material or private evidence.
- Workspace conventions: pnpm only (never npm); make code changes with the Edit/Write
  tools, not sed/awk.

## Standing rulings (apply to every task)

- R1 Fixture pack: `Careerwright_M0_Fixtures.zip` (named `Nessa_M0_Fixtures.zip` until
  2026-11-01) *is* now supplied. Use the original pack
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
- R4 Adzuna (corrected in plan v1.5): the developer credentials exist (`ADZUNA_APPLICATION_ID`
  and `ADZUNA_API_KEY` in `.env`), and the live qualification passed in Task 7: two
  free-tier requests through the adapter's own code, both answered, ledgered at $0 (ledger
  rows 32–33; ADR 0009 decision 11). `make setup` copies the credentials into
  `CAREERWRIGHT_HOME/adzuna/` for the restricted acquisition worker alone. Adzuna stays
  optional (plan v1.1, Sprint 3 S3.3), external data, still a local run; never put the
  credentials in a command argument, log or commit.
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
- R10 Human review sessions (plan section 10; ADR 0008, amended 2026-10-31). Each session
  below is a dispatch precondition for the work after it. The controller does not dispatch a
  task whose precondition session has not happened; it records "blocked: awaiting session N"
  in the progress ledger instead. An agent prepares each session's package under R2. Only the
  product owner's own record of a session establishes its outcome; an agent may transcribe
  that record, never supply it. The product owner may rule that an AI's check of rote items
  counts as their own review, as they did at session 2; an agent never assumes it. Each
  session asks about five questions, about outcomes rather than settings, each in one
  sentence that says what "yes" does.
  - **Held:** session 1 (2026-10-28: the rights policy, H-06, and the support policy, H-12;
    `docs/reviews/session-1.md`), session 2 (2026-10-29 to 30: the option pack's review,
    H-07; the comprehension session, H-13; the Sprint 2 design review, H-01;
    `docs/reviews/session-2-answers.md`) and session W1 (2026-10-30: the world's direction;
    `docs/reviews/session-w1-answers.md`).
  - **Session W2, short** (about 30 minutes, live, on Muse Wonder). After Tasks W2E, 6d, 3b,
    6f and 6e. The product owner uses the You chapter in the app, roles included, and answers
    about five questions: is the You chapter right enough to build the other chapters on
    (yes: the chapters follow its references); are the suggestions sensible for two or three
    named people, one whose role is on no list and, from plan v1.6, the synthetic school
    leaver, and is anything missing; keep Source Sans 3 for body text; keep leaf green for
    "accept", since words and a glyph carry it; any words they didn't understand (the
    opening question's words among them, plan v1.6). No score threshold: any score is
    formative. The slate's word-search rules are frozen (R11) and judged through the second
    question's examples, not item by item. Task 6e prepares the package. Precondition for the
    chapter interfaces (Tasks 10, 12b, 14, 15, 8 and M), never for backend tasks.
  - **The school-leaver pack session, short** (plan v1.6). After Task 7f's first half (the
    school-leaver pages curated and labelled). The product owner answers yes or no on each new
    or changed record's consequential fields, each beside its span, the consequential ones
    first (H-07 for the new pack version). Task 7f prepares the package. Precondition for Task
    7f's second half (publishing the reviewed version), and through it Task 12b.
  - **The end-to-end session** (about 1 hour; it replaces session 3). After Task 15. The
    product owner goes from You to a printed plan. It asks session 2's three route questions
    again on the real Routes chapter (the cost, the condition, what is uncertain); records
    formative scores for Skills, Options, Routes and Plan (H-01); orders the moments, or
    skips some; asks whether the results for a role outside ESCO are honest and useful,
    whether anything blocks a release, and whether the release uses Muse Wonder. Task 15
    prepares the package. Precondition for Tasks 8 and M.
  - **Release checks,** during Task 16; none is a dispatch precondition: every rubric
    category at least 4 (H-01); VoiceOver (H-03); Safari and print (H-04); five task
    sessions with other people (H-05; five participants are available, the product owner,
    2026-10-31); the privacy decision before anyone else's data is processed (H-08); the
    check of the rules for young people's data before any real student uses Careerwright
    (H-15, plan v1.6); the review of committed excerpts for names before any push (session
    1's delegated decision); and the counterfactual comparison's pass rule (H-12, still
    open).
- R11 Language rules have a boundary (plan v1.2; widened in plan v1.5). The support screen's
  stems, the explanation validation's word lists, redaction's patterns, the pay, date and
  work-mode readers, the agency words, and from v1.5 the slate's notes and its matching
  rules (one-word work style, "too general", main names only, hyphens) grow only for a
  reproduced defect or an evaluation failure:
  - a reproduced defect is a probe, fixture or corpus page that shows the wrong result;
  - a hypothetical form is recorded as a known limit, not fixed.
  Prefer a fail-safe outcome (unknown, unclear, body not kept) to a new pattern. Keep every
  required safeguard and every accepted limitation as recorded. A reproduced leak of a third
  party's contact detail, or a pay value approved wrong, is a defect and is fixed. More
  exceptions do not make a rule understand language.
  - **The sentence rule** (the product owner's approval, 2026-10-31; `CLAUDE.md`): a
    sentence the person reads says what Careerwright did or checked, never what a source or
    list contains. When exact and plain conflict, say less: a shorter true sentence, not a
    longer exact one. It covers the slate's notes, the matching lines, "none found", the
    readiness and route verdicts and every new chapter's words.
  - **Facts, not sentences** (the audit's code appendix B, findings F3 and F7). New or
    changed API responses carry codes and numbers, never sentences the person reads. The web
    words them from `src/lib/vocabulary.ts`, with exhaustive maps (`Record<Code, string>`),
    so a new code fails the type check. Tests check the facts; one test per fixed sentence
    checks its words. Task 6d's first slice converts discovery's search notes and title-idea
    lines.
  - A second fix round on the same kind of wording gets a rule, not another rewording (R14).
- R12–R17 How we build and review (current). One ruling for the whole process, merged on
  1 November 2026 from R12 to R17 (the lean review; the product owner's yes). Every clause
  that still holds is kept word for word under its old number, so citations still resolve.
  R12 (evidence before polish, Tasks 7b to session 2) became permanent as R13. The
  superseded wording is under "Superseded rulings" in `planning/controller-state.md`.
  - **Today's rules, in short:**
    - Up to four implementers at once, on disjoint files: one in the main tree
      (`/home/user/careerwright`), the rest in git worktrees
      (`/home/user/careerwright-wt/<id>`, branch `wt-<id>`).
    - One reviewer per piece, or per half, covering both the experience and the code.
    - One fix round at most. Only safety, truth and lost-input problems are fixed inside a
      piece; everything else goes on a list.
    - Full checks once per batch: implementers run `make check` after each change; the
      controller runs `make acceptance` once per batch of integrated pieces or halves.
    - A task with a screen splits into a backend half and a screens half.
    - The controller makes every web fetch and every live call (Environment facts).
    - One paper file per piece: the implementer's report, with its review and fix round
      appended to it; no separate review-dispatch, re-review or proposal files (the product
      owner's yes to the lean review, 1 November 2026).
    - The infrastructure is frozen for L0: no new services, workflows or run kinds; new pure
      computation runs in-process; a genuine need goes to the product owner as one question
      (the same yes).
  - **R13 Path before polish** (plan v1.5; permanent, for every remaining task, Sprint W
    included). A refactor, a hardening, or a world or visual refinement that no failing check,
    reproduced defect, truth rule, accessibility rule or Global Constraint requires goes to the
    final-review list in the progress ledger (a world refinement to Task M's list), never into
    the task. A Minor finding waits for the final review, unless it is of a kind R14 keeps in
    the task, comes from the product owner's own session, or is a failing check. Reviews of
    the path tasks (W2E, 6d, 6e, 10, 12b, 14, 15, 7e and 8) judge correctness, words,
    accessibility and fidelity to Sprint W's references; Global Constraint 11's "bland fails"
    is judged at Task M and at release. This is how they meet `CLAUDE.md`'s "A bland,
    form-like or corporate screen fails review": during a path task, a chapter built to Sprint
    W's design references, with its words, states and choices exact, meets that bar; its
    moment, judged at Task M and at release, completes it. Once a chapter is built, its
    Storybook stories become its reference, and its place in `docs/design/compositions` is
    retired (with the mirror in `apps/web/src/design`).
  - **R14 Review rules** (the product owner's approval, 2026-10-31; the audit report, section
    6). The controller and every reviewer follow them:
    - Keep reviewing hard, and fix within the task: anything that changes a decision (ready
      or not, feasible or not, unknown versus none, money, eligibility), lost input, fetch
      safety, the support panel, the first ten seconds.
    - Small things always wait for the final review (R13). The exceptions: a finding from the
      product owner's session, or a failing check.
    - The sentence rule (R11) for every sentence a person reads.
    - The product owner judges suggestion quality on a fixed set of real examples. Reviewers
      don't loop on it: at most one matching round per task.
    - Ask the product owner before round 2 of any policy question (for example, empty versus
      noisy suggestions, or strict versus relaxed rules).
    - Every review of a screen starts from the product owner's own session comments. Each is
      listed as done or not done, and a comment can't be carried forward twice without asking
      them.
    - Severity is graded by its effect on the person: high, they would act on it, lose work
      or be harmed; medium, they would notice; low, only a reviewer would. Register, document
      and code-tidiness findings are batched, once per sprint and at the final review.
    - Smaller slices: one chapter view or one backend contract each, keeping implementers
      well under their context limits.
    - The product owner's own commands join the acceptance run (`make demo`, opening each
      session package), and the recurring worker-shutdown hang is fixed: Task 3b.
  - **R15 Parallel work** (the product owner, 2026-10-31: "Where subagent work can be done
    cleanly in parallel, do so but coordinate well to avoid them causing conflicts").
    - Each task card's **Parallel** line says which tasks it may overlap; a card whose line
      says none runs alone.
    - In the main tree, commit with a pathspec only, never `git add -A` or `git commit -a`.
    - Shared documents (`docs/requirements-register.md`, `docs/plan/*`) change only in a
      task's last commit, after its rebase, and only the rows or lines its work closes.
    - One `make acceptance` at a time, under the lock `.superpowers/acceptance.lock` (take it
      with `mkdir`, remove it with `rmdir` the moment the run ends, pass or fail).
    - The controller integrates a worktree by fast-forwarding
      `claude/confident-ramanujan-ux3saw` after the implementer rebases onto it; an
      implementer never moves `claude/confident-ramanujan-ux3saw`. On a conflict in the
      generated client, regenerate it; a migration whose revision number another task took
      is renumbered to the next free one.
  - **R16 Speed** (the product owner, 1 November 2026: "I'm finding this development process
    too slow"; they chose all four of these).
    - **One reviewer per piece,** covering both the experience and the code, instead of two
      halves.
    - **One fix round at most.** Inside a piece, only safety, truth (a false statement, a
      failure shown as an empty success, a false evidence record) and lost-input problems are
      fixed. Everything else goes on a list: the product owner's session sheet, Task M or the
      final review. After the fix round the controller checks the diff and the tests itself; a
      second review runs only for a Critical finding.
    - A flaky failure is re-run once; a second failure is a finding.
  - **R17 Pipelining** (the product owner, 1 November 2026: "Use your best judgement in
    enhancing the dev process", after the controller proposed it).
    - **A task with a screen splits into a backend half and a screens half.** The backend half
      (domain code, API facts and codes, migrations, the generated client, tests) may start
      before its card's human-session precondition when that session judges words or looks
      only (session W2, the end-to-end session for its experience findings); the screens half
      waits for it. A session that decides scope or data (the school-leaver pack session, a
      rights or domain review) still gates both halves.
    - **Up to four implementers at once** (widens R16's three): one in the main tree, up to
      three in worktrees, on disjoint files. Card **Parallel** lines are read per half: a
      backend half may overlap another task's screens half when their files are disjoint.
    - Each half gets its own reviewer and its own fix round (R16); `make acceptance` runs once
      per batch of integrated halves.

## Task 1: Sprint 0 — technical spike and contracts (S0.1–S0.4)

**Preconditions:** none (complete before plan v1.1 introduced this line).

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

**Preconditions:** Task 1 (complete before plan v1.1 introduced this line).

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

**Preconditions:** Task 2 (complete before plan v1.1 introduced this line).

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

## Task 3b: Sprint 1 addition — live sessions ready on Muse Wonder (S1.6, plan v1.5)

**Preconditions:** Task A1 approved (2026-10-31; decision 5: Muse Wonder in the product
owner's live sessions). No task dependency and no human session. The controller makes every
live call itself (the qualification calls and the first live run below); this task's
implementer makes none.
**Parallel:** may overlap Task 6d, 12a, 13a or 13b. Not W2E: both change the account menu.

Sprint card: "Sprint 1 Build a polished local walking skeleton", S1.6 (plan v1.5). ADR 0003
(amendment of 2026-10-31); spec section 16 (spend controls); rulings R5 and R14; the audit
report, section 5, and its Muse Wonder notes (appendix G).

Deliver:
- **Muse Wonder ready to qualify.** The live commands (`make live-smoke`, `make live-eval`)
  accept `muse-wonder-1.0` as the production model behind an explicit flag, with a
  Wonder-sized cap per invocation (today's production cap, at most $0.10, is sized for
  Spark). When they are ready, the controller runs the qualification: two calls on
  synthetic input (schema output with usage; streaming, web search and schema output in one
  call), then at most six evaluation cases, under $0.50 in all, every call ledgered (R5).
  The controller resumes the implementer with the ledger rows, and the implementer records
  the capabilities they establish in the model registry (a model listed but never called
  has none).
- **A session command** (its name is this task's call) that starts the app with
  `muse-wonder-1.0` as the production model and sets the session's workspace caps: about
  $0.75 a run and about $5 per workspace (the product owner's ruling, 31 October 2026: the cap
  holds per workspace, and the session prints its total ceiling when it starts). It never
  runs in `make check` or `make acceptance`.
  Synthetic workspaces keep the test model, and the test model's safeguards (in code and the
  database CHECK) don't change.
- **Each session's calls in the cost ledger.** After a session, one command copies each
  attempt's model, run kind, tokens, cost and state, never its content, from the product's
  run records into `docs/evidence/live-usage.jsonl` and `.md`, under the session's scope. A
  cost the provider didn't report counts its full reservation (R5).
- **A spending line in the app,** in the account menu's preferences for the workspace:
  spent this month, the limit, and Change, through the existing spend endpoints. The words
  shown when a budget is reached point to it. Also one way to show a paid run's estimated
  cost before it starts, which Tasks 6e, 7e and 8 use where a person starts research
  (spec section 16).
- **The first live run of the real-data path.** Once Wonder is qualified, the controller
  runs one budget-capped interview turn, discovery and written note through the app, in a
  workspace not marked synthetic (so the production model runs) with a synthetic persona's
  words, before session W2. Ledgered.
- **The product owner's own commands join the acceptance run** (R14): `make demo`, and
  opening each session package's files. The recurring DBOS worker-shutdown hang is fixed,
  with a regression test.
- The runbook's live-commands section gains the session command and the ledger copy.

Acceptance: with Wonder configured, the API and worker start, and a synthetic workspace
still runs the test model; the session command's caps hold in an offline test; the ledger
copy writes model, kind, tokens and cost and no message text (a test checks); the spending
line shows what was spent and the limit, and changes the limit; `make demo` and the session
packages are part of `make acceptance`; the shutdown hang's regression test passes; `make
check` and `make acceptance` pass. The controller's live calls, with their costs, are in the
task report. The product owner's own details in their own sessions are their choice; the
privacy decision (H-08) stays a release check before anyone else's data.

Register: closes MODEL-10 and MODEL-11; the Task 3b parts of MODEL-03, MODEL-04, MODEL-08
and TEST1-10.

## Task 4: Sprint 1 — designed shell connected to the real API (S1.4–S1.5) + Sprint 1 review

**Preconditions:** Task 3 (complete before plan v1.1 introduced this line).

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

**Preconditions:** Task 4 (complete before plan v1.1 introduced this line).

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

**Preconditions:** Task 5 (complete before plan v1.1 introduced this line).

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

## Task 6d: Sprint 2 — your title, recognised (S2.8, the role space's first step, plan v1.5)

**Preconditions:** Task W2E complete. ADR 0015, the amended ADRs 0006, 0007 and 0012 and the
`CLAUDE.md` discovery invariant are in place (Task A1, applied). No human session: session
W2 judges the result.
**Parallel:** may overlap Task 3b, and Task 13a, 12a or 13b in the worktree. Task 12a may
also change the profile's schema: the one integrated second rebases, renumbers its
migration and regenerates the client (R15). Not 6e.

Sprint card: "Sprint 2 Deliver conversation and career discovery", S2.8 (plan v1.5). ADR
0015 (the role space); ADR 0007 decisions 4, 5, 13 and 14, ADR 0006 decision 5 and ADR 0012
decision 10, as amended; spec section 4 (REC-1, DIV-1) and section 3 (minimum inputs); the
audit's role-space appendix (F), section 6, "The smallest first slice", and its code
appendix (B), finding F5.

Loop guard (R14): the sentence rule applies from the start; the product owner judges
suggestion quality at session W2; at most one matching round. The slate's word rules don't
change (R11).

Deliver:
- **First, facts instead of sentences** (R11; the audit's code appendix B, findings F3 and
  F7), ahead of the role-space work below. Discovery's search notes and its title-idea lines
  become structured facts in the API: found work, found none or not searched, with the
  reason code. The web words them from `src/lib/vocabulary.ts`, with exhaustive maps, and
  the backend composes no sentence the person reads. What each note reports doesn't change
  (R11 freezes the notes); only where its words live does. Tests check the facts; one test
  per fixed sentence checks its words. The role space's new notes below (the UK title list,
  the person's own words, "None of these is my job") are born as facts.
- **The first question finds any UK title.** As the person types, titles come from the
  pinned ESCO release and the pinned ONS SOC 2020 coding index (already imported for pay
  codes), ESCO first on ties; an ONS title is marked "UK job title (ONS)". "Use my own
  words: '…'" is always offered, and choosing it keeps the title exactly as typed (a
  provisional concept). Nothing typed is refused. The first answer still changes the world
  within a second, with no model call, without a key and in the demo; a browser test
  proves the world answers within ten seconds of the first answer.
- **"Which of these is closest?"** After an ONS title or the person's own words, the person
  sees the ESCO occupations in that title's ISCO-08 group, as the ONS index codes it, and
  "None of these is my job". With none, the role has no ESCO seed, and the words say what
  isn't known yet without asking anyone to pick another job. A title the ONS index codes to
  more than one ISCO-08 group shows every group, none picked. The type-ahead's partial
  results ask "Careerwright couldn't match that title in ESCO. Is it one of these?", and
  "None of these is my job" leads to the person's own words.
- **Title ideas the ONS index lists become suggestions.** A discovery's title idea that the
  ONS index lists is shown in its own short list beside the slate, "found in the UK
  job-title index", with the answers it came from. An idea in no list is shown as not yet
  found, never as a suggestion.
- **Each target is stored once** (finding F5): when a target is chosen or saved, its
  occupation (or none), the source of that link and how far Careerwright can cover it (one
  of the option pack's targets or not) are stored with it. The slate, the sketch, the
  strength, Skills and the world read that one record, so the four title resolvers become
  one. The coverage is shown where a target is chosen.
- **Optional seniority and industry** beside a role or a target title. Matching ignores
  them; display and search keep them.
- **The ESCO research's three fixes:** skills ESCO lists for a role are described as "ESCO
  lists these for this kind of work"; the person can mark one "not part of my job" (a
  display state, never evidence); and no revelation rests on ESCO's essential skills alone.
  How the unexpected connection meets the last rule is to be settled by Task 6d, asking the
  product owner before a second round (R14). Settled on 1 November 2026: "Always a plain
  line", never a revelation.
- **Pasted CV text, if it stays small.** The person pastes a CV, and its facts come back as
  proposals through the same review tray; nothing commits unconfirmed. Whether it is small
  enough is to be settled by Task 6d; if not, it is recorded as an L0 deferral (plan
  section 1) with its reason.
- Design inputs: the parked `concept_key` gap ("&" and accented titles don't match their
  plain spelling).
- The lines that say a title isn't in ESCO change to say what Careerwright did with the
  person's title (R11), worded in the web from facts like the notes above. The evaluation
  cases for unsupported-title rejection change so that a title the ONS index lists passes
  (spec DIV-1). Regenerate the client after the API changes.

Acceptance, in the demo workspace with no key and no network (the role-space appendix's
test, in plain words):
1. Type "Registered nurse", "Data quality analyst", "Prompt engineer" and "Doula" at the
   first question. Each appears as a title to pick, marked as a UK job title from ONS.
2. Picking one keeps the exact words. The world answers within a second and offers the
   ESCO occupations in its ISCO-08 group, as the ONS index codes it, and "None of these is my
   job".
3. Type "Bookkeeping assistant", which neither list holds. "Use my own words" is offered and
   kept, and the world still answers. It says what isn't known yet and asks no one to pick a
   different job.
4. A discovery's title idea that the ONS index lists shows as a suggestion, with the answers
   it came from and "found in the UK job-title index". An idea in no list shows as not yet
   found, never as a suggestion.
5. No screen states skills, pay, readiness or openings for these titles beyond what their
   sources hold.
6. Discovery's search notes and title-idea lines, and the new notes above, arrive as facts
   with a reason code and carry no sentence; the web words them, and one test per fixed
   sentence checks its words.

Also: a plural or punctuated title resolves the same in every consumer of the stored target
record; `make check` and `make acceptance` pass.

Register: closes DIV1-13, DIV1-14, PROF-10, PROF-11 and MAP1-09, and the ONS part of
DIV1-04; updates DIV1-03, DIV1-10, REC1-06 and PROF-08 (seniority); closes PROF-12 or
records it as deferred; the Task 6d parts of PROF-07 (pasted CV text through the same
commands as a direct edit) and TEST1-15 (the unsupported-title evaluation cases).

## Task 6e: Sprint 2 — research this role (S2.9, the role space's second step, plan v1.5)

**Preconditions:** Tasks 6d, 6f (plan v1.6) and 3b complete. No human session; this task
prepares session W2's package.
**Parallel:** may overlap Task 12a or 13b, and from plan v1.6 Task 12c or 7f in the
worktree. Not 6d or 7e: they change the same title and evidence records. Not 6f: its
evaluation cases and first question come first.

Sprint card: "Sprint 2 Deliver conversation and career discovery", S2.9 (plan v1.5). ADR
0015; ADR 0009 decision 12 as amended (the role-research purpose); spec sections 4 (DIV-1),
6 and 11; rulings R5, R9 and R11; the role-space appendix (F), section 6, "Second slice".

Deliver:
- **"Research this role"** for a title no list holds: the person's own words, or a title
  idea not yet found. Before it starts, the person sees its estimated cost (Task 3b). One
  bounded web search, a new purpose of the existing source search, sends only the title and
  "England", never the person's answers (SEC-05). The restricted acquisition worker reads up
  to five of the candidate pages through the guarded fetcher, and the source manifest
  decides each page's class.
- **Corroboration by code** (ADR 0015): the title is checked word for word as a span of each
  page's visible text. The role counts as found when the title is verified on pages from at
  least two independent hosts or employers (copies of one advert count once, ADR 0009
  decision 6), or on one page of an official class. Otherwise it stays "not yet found in
  independent sources": visible, never hidden, never a suggestion. A found role is a
  provisional concept with its source claims; the quotes and dates are one step away.
- Optional, when a found role's card is opened: its duties and entry requirements quoted as
  verified spans through the `page_extraction` pattern (the model quotes; code approves).
  Whether this fits L0's per-role spend bounds is to be settled by Task 6e (ADR 0015).
- Records are private to the workspace, `review_state: proposed` and dated (R9). A page that
  tells the model to do something changes nothing. A run can be cancelled. Every call is
  ledgered (R5).
- The person's own title stays choosable without research; a model's title idea becomes
  choosable once it is corroborated.
- Spend: worst case at most $0.045 per research run on Spark; the session command's run
  limit (about $0.75, Task 3b) lets three attempts fit on Wonder.
- Regenerate the client.
- **A synthetic school leaver** (plan v1.6; the product owner's decision of 1 November
  2026): 17, in Year 13 with A-levels in progress, has never had a job, helps at a youth
  club, unsure what she wants, Leeds. She is labelled synthetic wherever she appears and
  kept apart from the supplied pack (`fixtures/m0` never changes; she never fills a live
  field). Four to six evaluation cases: an interview in her words ("I'm in Year 13 doing
  biology, chemistry and psychology. I've never had a job but I help run a Brownies
  group"), which records what she enjoys and has done and invents no job title and no
  income; a discovery from her school subjects and volunteering, grounded, with nothing
  called close to what she does now; a strength proposal from her words, with a target
  chosen from her slate; and the no-job first answer in the browser (Task 6f). One capped
  live run of Task 6f's interview prompt on her cases (R5; the controller makes the call).
- Finish: **session W2's package** (R10, R2), in plain words: how to start the session
  command, the five questions, two or three named personas (one whose role is on no list,
  and from plan v1.6 the synthetic school leaver), one yes/no line on Childline in the calm
  support panel (Task 6f; H-12), and a record sheet. Each item "not run — requires human".

Acceptance (the role-space appendix's test): one live run on the test model with a synthetic
title, capped and ledgered (R5). Pages from two different hosts that both contain the title
make it found, with both quotes and dates one step away. One page, or two copies of one
advert, leaves it "not yet found in independent sources". A page telling the model to do
something changes nothing. Offline fixtures cover each of those cases. From plan v1.6 the
school leaver's cases pass offline, she is labelled synthetic on every surface that shows
her, nothing under `fixtures/m0` changes (its hashes still match), and her live run is
ledgered. `make check` and `make acceptance` pass.

Register: closes DIV1-15 and the independent-source part of DIV1-04; the Task 6e parts of
DIV1-03 and REC1-06 (a found role as a provisional concept, grounded by its pages), DIV1-10
(user-proposed titles corroborated outside ESCO), MODEL-08, SEC-05 and TEST1-10. From plan
v1.6: closes TEST1-16 (the synthetic school leaver and her cases).

## Task 6f: Sprint 2 — no job yet (S2.10, plan v1.6)

**Preconditions:** Task 6d complete (its last slice reviewed): this task changes the same
first question, What we know and support screen. The product owner's school-leaver decisions
of 1 November 2026 (decisions 2, 3, 4 and 9: yes). No human session: session W2 judges the
result, and the opening question's final words are the product owner's there. The
controller checks Childline's details on Childline's own website and passes them in the
dispatch; this task's implementer makes no web request.
**Parallel:** may overlap Task 12c or 7f in the worktree. It changes the saved answers'
schema and adds a migration: if Task 12c also adds one, the one integrated second rebases,
renumbers its migration and regenerates the client (R15). Not 6d or 6e: they change the same
first question, profile and evaluation cases.

Sprint card: "Sprint 2 Deliver conversation and career discovery", S2.10 (plan v1.6). Spec
section 3 (minimum inputs: "Collect work status, current role/level, experience, relevant
qualifications and commitments"), section 4 (the structured profile's "Work/study status …
credentials"; the adaptive conversational policy's opening question) and section 22 (the
rows of 1 November 2026); ADR 0006 (the saved answers and the interview contract) and ADR
0007 (the support policy); rulings R5, R11 and R14. The school-leaver walk
(`planning/audit-no-job-yet.md`): findings 1, 3, 4 and 8, and its
section 2, rows 1, 3, 4 and 8.

Who it serves: a final-year school student who has never had a job, and anyone between jobs,
caring or returning to work. It adds no separate student mode: the same answers serve
everyone. Nothing asks for or infers the person's age.

Loop guard (R14): the sentence rule applies from the start; the product owner judges the
words at session W2; at most one wording round.

Deliver:
- **"I haven't had a job yet"** beside "Skip for now" at the first question (the product
  owner's words). It saves an answer about the person's current role, never a job title,
  Skipped or Unknown, so the person's light comes on, and the start goes on to how to start.
  Neither the demo nor the live interview asks the job question again, and the next
  question asks what they enjoy. The person can change the answer in What we know. A browser
  test proves the world answers within ten seconds of choosing it, in the demo, with no key.
- **Two optional answers** (spec section 3's work status and qualifications): "What you're
  doing now" (working, in education or training, looking for work, caring, other) and
  "Qualifications, including ones you're taking", each marked achieved or expected. Both
  take Skip, Unknown and Prefer not to say, and neither is asked twice. They go through the
  one profile write path and the interview contract like every other answer (the model
  proposes, the person confirms, ADR 0006): the saved answers' next schema version with a
  forward-only migration (an existing profile gets both as not yet asked), the demo
  interviewer's patterns, What we know and the generated client. An expected qualification
  is shown as expected everywhere, never as achieved. Skills (Task 10) and Options (Task
  12b) read both as entry facts later.
- **The opening works without a job.** "Help me explore" opens with a question that asks
  for no job, for example "What would you like your working life to be like?" (the product
  owner settles the words at session W2). The walk's word pass:
  - "this change" becomes "your next step";
  - one example reply that isn't a job ("I help run a youth football team");
  - the demo asks an unsure person "What do you enjoy doing, at school, at work or in your
    own time?";
  - the live interview's instructions gain one line, "Someone may not have had a job yet:
    ask about school or college, volunteering, caring, clubs and hobbies; never treat no
    job as a gap", and its prompt version goes up;
  - the conversation's "Show me suggestions" no longer waits for a current-role answer;
  - "Closer to what I do" is not offered when no work is known;
  - the note for unknown work loses its "yet", and never tells someone who said they
    haven't had a job that their work isn't known.
  Every new sentence is worded in the web from facts (R11).
- **Childline in the calm support panel,** for anyone under 19, beside the panel's other UK
  services, with the details the controller checked on Childline's own website. The support
  policy's version goes up (ADR 0007, amendment). Its review joins the support policy's
  (H-12): Task 6e puts one yes/no line for it in session W2's package.
- The evaluation cases' expectations follow the new answers and the no-job answer, offline,
  on the demo interviewer. The capped live run of the new interview prompt is Task 6e's, on
  the synthetic school leaver's cases (R5).
- ADR 0006 and ADR 0007 gain amendment lines for the new answers, the opening and Childline.

Acceptance, in the demo workspace with no key and no network:
1. At the first question, "I haven't had a job yet" sits beside "Skip for now". Choosing it
   lights the person's light within ten seconds (a browser test) and moves on to how to
   start.
2. Nothing asks for a job again. The demo's next question for an unsure person asks what
   they enjoy, at school, at work or in their own time, and one example reply isn't a job. A
   test shows the live interview's instructions carry the no-job line.
3. "Show me suggestions" is offered with no current role. With no work known, no suggestion
   is called close to what they do now, and "Closer to what I do" isn't offered.
4. What you're doing now and a qualification marked expected round-trip through the same
   command as a direct edit, show in What we know and are never asked twice; an expected
   qualification never reads as achieved. An existing profile migrates forward with both not
   yet asked.
5. A risk word still shows the calm support panel, and it now lists Childline for anyone
   under 19.

Also: `make check` and `make acceptance` pass. The visual part is an agent pre-review only
(R2); session W2 judges the words.

Register: closes PROF-14 and PROF-15 (Childline's review stays "not run — requires human"
until H-12 records it); the Task 6f parts of STATE-11 and PROF-13; the rows its work changes
(PROF-07, PROF-08 and STATE-08: the new answers through the same commands, never asked
again, with Skip, Unknown and Prefer not to say) gain a Task 6f part.

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

## Task 7e: Sprint 3 — find options for this role (S3.7, plan v1.5)

**Preconditions:** Tasks 15 and 12b complete: the decision path works end to end, and the
Options chapter holds workspace option records. It may start while the end-to-end session
is awaited.
**Parallel:** none: Task 8 shares `careerwright/evidence`, and Task 12b's Options chapter is
done by then.

Sprint card: "Sprint 3 Make the evidence and opportunity map real", S3.7 (plan v1.5); plan
section 9 ("The England option pack": live research writes the same record contract,
`proposed`, inside its own workspace). ADRs 0009, 0011 and 0013 as amended; spec sections 6,
10 and 11; rulings R5, R9 and R11. It restores what Task 7's card and plan section 9 promised
and was not built.

Deliver:
- **"Find options for this role"** in Options, for any target. Before it starts, the person
  sees its estimated cost (Task 3b). A bounded search, an option-research purpose of the
  existing source search, sends only the target title and one of the person's cities
  (SEC-05). The restricted acquisition worker reads the candidate course and funding pages
  through the guarded fetcher; the source manifest decides each page's class.
- **Apprenticeships and degrees too** (plan v1.6; the school-leaver walk): the
  option-research purpose names apprenticeships, degrees and their funding beside courses,
  so a school leaver's target finds its usual routes. It still sends only the target title
  and one city.
- **Values from verified spans only.** Structured data first; then the `page_extraction`
  pattern with a course and funding schema (the model quotes, deterministic code approves
  values read from verified spans; at most five pages per acquisition; the model's input is
  erased when its run ends).
- **Stored as workspace records** in the pack's record shapes (LearningOption and Offering,
  FundingInstrument), `review_state: proposed`, dated, never in the pack. The planning
  catalogue reads them beside the pack, and a route built on one is qualified, never an
  unqualified "affordable and feasible" (R9). They show as not reviewed, in plain words.
- A blocked, failed or unread page is never "none found". A run can be cancelled. Course and
  funding ages are enforced on access (fees and intakes 7 days, funding availability 48
  hours, funding rules 30 days). Every call is ledgered (R5).
- **The live path scored on courses and funding** (moved here from Tasks 10 and 12b in plan
  v1.5, because this task builds the course and funding extractor): pointed at the pack's
  ten course pages and three funding pages, field by field against the reviewed values:
  correct, incorrect, missing and unsupported, with denominators (TEST1-13; test model,
  public inputs, capped).

Acceptance: an option found by research round-trips as a not-reviewed record with its
spans, and a route built on it reads qualified in Routes, in plain words; a page that tells
the model to do something changes nothing; offline fixtures cover structured data,
extraction and a refused page; the live scores are reported with their denominators; `make
check` and `make acceptance` pass.

Register: closes OPTN-12 and, from plan v1.6, OPTN-16 (apprenticeships, degrees and their
funding); the courses and funding parts of TEST1-13; FRESH-02's course and
funding ages on workspace records; the Task 7e parts of ACQ-03, ACQ-07, API-06, MODEL-08,
OPTN-09 (researched records `proposed`, never in the pack), SEC-05, TEST1-09 (the pack's
course and funding pages run live) and TEST1-10.

## Task 7f: Sprints 3–5 — the school-leaver option pack (plan v1.6)

**Preconditions:** Task 12c complete (the tuition fee loan the new loan records load into);
Tasks 7b and 7c complete (the pack's format and its reviewed version 0.2.0); session 1 held
(the rights policy, H-06). Its second half (publishing) waits for the school-leaver pack
session (R10); until then the controller records "blocked: awaiting the school-leaver pack
session". The controller makes every fetch; this task's implementer makes no web request.
**Parallel:** in the worktree, it may overlap the main-tree Tasks 6f, 6e and 10. Not 12b,
which reads the version it publishes, or 12c, which comes before it in the worktree track.
Not 7e or 8: they share `careerwright/evidence`.

Sprint cards: the corpus items of "Sprint 3", "Sprint 4" and "Sprint 5", and plan section 9
("The England option pack", v1.6). Spec sections 10 (funding and finance discovery: the
scheme's "residency and age rules", repayment terms), 11 (the M0 option pack) and 18; ADR
0011 (a committed version never changes; a correction or a review is a new version with its
own pin, loaded only through `load_pack`); rulings R3, R7, R9, R10 and R11. The school-leaver
walk (`planning/audit-no-job-yet.md`), findings 2 and 6.

In two halves, as Tasks 7b and 7c ran: curate and label, then publish after the session.

Deliver, first half:
- **The pages:** the official page saying apprentices don't pay for their
  training; Student Finance England's tuition fee loan and maintenance loan pages; the 16 to
  19 Bursary Fund; one T Level or Level 3 course page; and the page that states the UCAS
  deadline for the pack's nursing degree. This task proposes each address; the controller
  fetches each through the Task 7 pipeline's guarded fetcher (`tools.corpus`, pacing within
  one process) and passes the result. Each page is classed against the session 1 rights
  policy, recording the class and the terms relied on; a page outside it stays "pending
  human rights review" (R10). A page that can't be fetched is recorded with its failure,
  never as "none found".
- **Labels and records,** as Task 7b did: values with units or currency, spans as offsets or
  stable selectors with minimal excerpts, missingness and expected unknowns; each page's
  template family and holdout split assigned before any use. Records in the pack's shapes
  (FundingInstrument for the two loans and the bursary, each with its age and residency
  rules and, for the loans, how they are paid and repaid; LearningOption and Offering for
  the course), every one `proposed`, dated and span-cited, or unknown with its reason. A
  value the new pages support in an existing record (the apprenticeship's training fee,
  from the no-fee page; the nursing degree's UCAS deadline) is a corrected value with its
  span, in the new version only.
- **A new pack version** that the Task 7b validator passes, distributed under the same rule
  (R7, or committed if small and its rights permit); the earlier versions stay readable and
  unchanged, each with its own pin. Nothing synthetic enters it, the synthetic school leaver
  included. Update `corpus/manifest.json` and `corpus/README.md`.
- **The school-leaver pack session's package** (R10, R2), in plain words: each new or
  changed record's consequential fields (fees, the no-fee rule, the loans' payment and
  repayment terms, age and residency rules, deadlines, dates) beside its span, as yes/no
  questions, the consequential ones first, so the session stays short. The product owner
  may rule that an AI's check of rote items counts as their review, as at session 2; an
  agent never assumes it. Each item "not run — requires human".

Deliver, second half (after the session):
- Publish the reviewed version from the product owner's own record only, as Task 7c did: an
  accepted record becomes `reviewed`, naming the reviewer, the decision date and the session;
  a rejected record is left out, its reason kept in the review record; a corrected value is
  changed with its span cited and the decision named; an undecided record stays `proposed`
  (R9). Update `corpus/manifest.json` and `corpus/README.md` from the record.
- Hand the reviewed version to Task 12b: its version and hash, which it pins.
- No live call.

Acceptance: every new page is in the manifest with its address, retrieval date, hash,
rights status, template family, split and labels; the new version validates, and every new
record is `proposed`, dated and span-cited or unknown with its reason; nothing synthetic is
in the pack; no unpermitted body is in git; the session package is ready. After the session:
the reviewed version validates; every `reviewed` record traces to a decision in the product
owner's record; no rejected record is in it; every changed value is span-cited; the earlier
versions are unchanged. `make check` passes after each half.

Register: closes OPTN-14; the Task 7f parts of OPTN-10 (the versioned pack, now with
school-leaver sources) and TEST1-09 (the new pages labelled); H-07 for the new version, from
the product owner's own record.

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
From plan v1.5 it ends with Task W2E, which closes Sprint W at the world shell, the You
chapter and the deterministic sources. Session W2 is then a short first look with no score
threshold, held after Tasks W2E, 6d, 3b and 6e (R10); Tasks 10, 12b, 14, 15, 8 and M wait
for it.

**Status (plan v1.5):** slices W2A, W2B and W2C part 1 are done (W2C part 1's re-review runs
now). W2C part 2 and W2D are replaced by Task W2E and by moves to Tasks 6d, 10, 8, M and 16
("Where the remaining Task W2 work went", above). The text below is the task as dispatched.

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
and the five personas (amending ADR 0007; from 1 November 2026 a plain line, never a
revelation), and the overlooked strength as a new bounded run
kind whose quotation is span-verified and confirmed by the person (live calls R5; tests use
the test model or fixtures only); the new requirement family in the register
(SW.6). Prepare session W2's package: captures at the three viewports, motion on and off,
and the rubric with the three v1.4 questions. `docs/reviews/sprint-w.md`, completed with
session W2's outcome from the product owner's own record.

Acceptance: the plan's Sprint W acceptance; `make check` and `make acceptance` pass; the
design references' contrast and screenshot checks pass.

## Task W2E: Sprint W — finish the You chapter, and the Sprint W review (plan v1.5)

**Preconditions:** Task A1 approved (2026-10-31) and its changes applied; the scoped
re-review of W2C part 1's fix round 1 reported (the controller passes its open findings in
the dispatch). No human session: session W2 follows Tasks 6d, 3b and 6e.
**Parallel:** may overlap Task 13a, 12a or 13b in the worktree (Task 12a under R15's
rebase rules: it may also change the profile). Not 6d or 3b: they change the same screens
or the account menu.

Sprint card: "Sprint W Build the world": SW.4 and SW.6, the acceptance as plan v1.5 reshapes
it, and the coherence review. Plan section 4 ("practical first", and on a phone the decision
first); the audit report, section 4, step 1; the person's-path appendix (E), findings F1,
F2, F5, F7, F8, F10, F14 and F17. Build to Task W2's design references (R13).

Deliver, each as something the person sees:
- **The re-review's open findings, fixed** (the controller lists them), with fix round 1's
  own concerns: "Help me explore instead" keeps keyboard focus, and the moving-and-still
  identical-words test also runs on a workspace that isn't the fixture's.
- **The demo conversation never loops** (F1). Each demo question offers one-tap example
  replies. The demo interviewer understands a target ("I want to be a …") and the words
  Skip, Unknown and Prefer not to say. "Do you have a role in mind, or would you like to
  explore?" offers two buttons: "Show me suggestions" (it opens Suggestions and starts one)
  and "Name a role" (it opens target entry). The live interview offers the same two.
- **Each dead end is marked before it is clicked** (F2): the rail marks every chapter that
  isn't built yet.
- **A chosen target is confirmed, never "out of date"** (F5). A profile version that changed
  only the targets chosen from this slate doesn't make the slate stale, and "Suggest again"
  doesn't become the bright action. The person sees that the target is saved, and what it
  usually asks for, in place.
- **Shared skills named, and the unexpected connection shown.** Each suggestion names the
  skills it shares (the first few, the rest one step away), not only their count. The
  slate's computed connection is shown in words, its skills one step away; its light in the
  world is Task M's. (Superseded on 1 November 2026, "Always a plain line": the computed
  connection is removed and nothing is lit for it; Task 6d slice C.)
- **On a phone the decision comes first** (F7, F8). At 390 × 844, any view with a pending
  decision shows its first decision in the first screen, and the world band takes no more
  room than what it shows. The key button never covers a tab: an "on top" check covers the
  three tabs at 390 and 768.
- **On a tablet the person's facts come first** (F14): the strip keeps work area and budget
  at 768, and the motion and sound switches move into the account menu below desktop width.
- **One bright action, and two pauses that can't be confused** (F17). Until the first
  answer, the start screen's bright action is the entry choice, never Send on an empty
  field. The world's pause and the interview's pause can't be mistaken for each other.
- **A reached budget points nowhere false** (F10's words): its words name no control the app
  doesn't have yet. Task 3b adds the spending line and words that point to it.
- **"England only"** (BND1-02): before detailed collection, one plain line says Careerwright
  covers England for now.
- **The demo route preview leaves the person's path** (the audit's ruling): Routes shows its
  "not built yet" place in every workspace, and the preview stays in Storybook and the
  design review. Task 14 replaces it.
- **The world's requirement family in the register,** with its tests tagged (SW.6). Its
  moments' rows are owned by Task M, and its frame-budget rows by Tasks M and 16.
- ADR 0014 decision 7's strip wording, corrected to what the strip shows after this task.
- `docs/reviews/sprint-w.md`: Sprint W closes at the world shell, the You chapter and the
  deterministic sources (plan v1.5). The first task after session W2 adds its outcome from
  the product owner's own record (R10).

Acceptance: each item has a test that reads what the person sees (words, order, focus, what
is in the first screen). At 390 × 844 the first decision of the reply-to-review,
Suggestions and What-we-know views is in the first screen. In the demo, a person who
answers "I want to be a nurse" or "Skip", or taps an example reply, never gets the same
question twice. `make check` and `make acceptance` pass. The visual part is an agent
pre-review only (R2).

Register: closes BND1-02, STATE-09, STATE-10 and UI-12; the Task W2E parts of STATE-08 and
UI-09; adds the world's requirement family.

## Task 8: Sprint 3 — living opportunity map and the job corpus (S3.5) + Sprint 3 review

**Preconditions:** Task 7c complete (the reviewed job values this task scores against;
Task 11 and session 2 come before it); session 1 held (H-06 rights policy; R10); session W2
held; Task 15 complete and the end-to-end session held (plan v1.5: Roles comes after the
decision path, and the end-to-end session may still reshape L0).
**Parallel:** none: Task 7e shares `careerwright/evidence`.

Sprint card: "Sprint 3 Make the evidence and opportunity map real". Slice: S3.5, the
20-job corpus portion, remaining acceptance, the coherence review. Spec sections 5, 7
(VIS-1), 13, 14.

Scope notes (plan v1.1, ADR 0008): the Roles chapter runs after the Sprint 4–5 backends.
It consumes the option pack's 20 job postings, curated and labelled by Task 7b, in the
reviewed version Task 7c published; it does not curate pages. Plan v1.5 corrects the
reason: live vacancy data exists (the Adzuna credentials are set and the free-tier
integration was qualified live, R4). Roles comes after the decision path because routes
don't need it. Every role is still unscored, and no reviewed pay mapping exists (H-10).

Deliver the Roles chapter as its place in the world, the horizon, to Task W2's design
references (plan section 4; R13); its moment is Task M's to choose. Shared skills are a plain
line on each suggestion, and no suggestion is singled out (the product owner, 1 November
2026: "Always a plain line"). Keep
VIS-1's hierarchy and industry shown by glyph and label (ADR 0014): SVG/D3 dendrite with
stable anchors, company expansion, up to 100 visible job nodes, explicit aggregation
counts; a pay lens of each listing's own advertised or predicted pay, labelled as such;
mobile-first list; one shared selection and filter contract across list, map and pay lens;
focus retention and keyboard actions; graph distance never implies commute feasibility.
From plan v1.5 (the audit's rulings and findings):
- **One plain line instead of the numeric salary and AI-range filters,** saying pay and AI
  evidence aren't reviewed for this release (plan section 1, L0 deferrals). The salary
  floor already applies to listings (ADR 0010 decision 8), and the pay lens keeps its lanes
  of advertised, predicted and unknown pay (VIS1-06).
- **Roles outside ESCO** (Tasks 6d and 6e) and titles from live postings appear on the map.
  How they are grouped where no ESCO occupation joins them is to be settled by Task 8.
- **The role card** (spec section 5): the role, its other names, the workday, pay as its
  sources hold it (an ONS-coded title's ASHE figures for its SOC 2020 unit group, labelled
  the group's; ADR 0010, amendment), AI evidence by its ISCO-08 group, evidence quality and
  dates, and an outlook of "not enough evidence yet" (trend history isn't available in L0).
  Job relevance shows its parts, and "matches your preferences" only where they were
  assessed.
- **Live listings** through Adzuna and the source search, in a live workspace. Before a
  research run starts, the person sees its estimated cost (Task 3b's estimate), and a run
  they started can be cancelled.
- **Apprenticeships** (plan v1.6; the school-leaver walk): a listing that is an
  apprenticeship is marked as one, and the person can paste an apprenticeship advert as one
  of their own examples (MAP1-01). How a listing is known to be one is to be settled by Task
  8; one it can't tell stays unmarked, never guessed.
- The phone openings list one area per line, with its stale and unknown states captured
  (from Task W2's slice W2D).
- The controller's carried items for this task come in the dispatch. Apply the Roles findings of
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

Acceptance (plan v1.5, beside the sprint card's): one plain line stands where the salary and
AI-range filters were, and the pay lens keeps its lanes; a role card's outlook reads "not
enough evidence yet"; an ONS-coded title's pay is its SOC 2020 unit group's ASHE figures,
labelled as the group's, never as the title's or the person's; `make check` and `make
acceptance` pass.

Register (plan v1.5): the VIS1 rows, AIR1-01, AIR1-08, AIR1-10 and AIR1-13; JOB-01, JOB-04,
JOB-06 and JOB-07, and from plan v1.6 JOB-09 (apprenticeships); the Task 8 parts of ACQ-03,
ACQ-07, DUR-03, FRESH-02, MODEL-08, UI-09 and TEST1-13 (jobs). The salary and AI-range filters (parts of VIS1-03, VIS1-07, VIS1-11 and
AIR1-05) are recorded as an L0 deferral.

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
course outcomes; Task 11 comes before it); Task 6d complete (the stored target record, plan
v1.5); Task 6f complete (the person's qualifications, plan v1.6); session W2 held (R10). No
dependency on Task 12b or Task 8.
**Parallel:** may overlap Task 13b in the worktree. Not 12a (the worktree track runs it
beside Tasks W2E, 6d, 3b and 6e only) or 12b, which follows it.

Session 2's Sprint 2 design findings are applied by Task W2 (plan v1.4). Build the Skills
chapter as its place in the world, to Task W2's design references (plan section 4; R13):
initial presentation short, evidence one step away. Its moment, the overlooked strength, is
Task M's (plan v1.5).

First (plan v1.5): delete the world spike, `spikes/world` (the audit's ruling: it is
deleted after session W2 and stays in git history), and add session W2's outcome to
`docs/reviews/sprint-w.md` from the product owner's own record (R10).

**Skills for any target** (plan v1.5; the audit report, section 4, step 8):
- what the target's occupation lists, labelled as ESCO's ("ESCO lists these for this kind
  of work"), with the skills the person marked "not part of my job" (Task 6d) shown as such;
  a target outside ESCO uses the person's chosen closest occupation, or none (ADR 0012,
  amendment);
- what the person's chosen adverts ask for: their own examples (up to three per target,
  MAP1-01), read by the person's own selection of spans, with no new model run;
- the evidence questions;
- readiness where a reviewed rubric exists, and elsewhere "not assessed yet, here's what it
  asks", never a readiness result;
- "usual in your role, not confirmed yet" as a display state for the skills ESCO lists for
  the person's own role (from Task W2's slice W2C part 2); wherever something is computed it
  stays unresolved (ADR 0014 decision 4). From plan v1.6, a person with no role (no job yet,
  or none given) sees no such panel, never an empty one;
- from plan v1.6 (Task 6f), the person's qualifications as entry facts beside the
  requirements that name them: one marked expected is never counted as met, and one marked
  achieved follows the gate rules as they stand (ADR 0012: held but unverified stays
  unresolved for a protected gate; nothing finds a person ineligible).
The controller's carried items for this task come in the dispatch.

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
review states wherever its records appear (R9). The live path's scoring on the course pages
moves to Task 7e, which builds the course extractor (plan v1.5; TEST1-13). Record H-07's
Sprint 4 part from the product owner's own session 2 record. `docs/reviews/sprint-4.md`.

Acceptance (plan v1.5, beside the sprint card's): a target outside the option pack, or one
whose closest occupation is "None of these is my job", shows "not assessed yet, here's what
it asks" and never a readiness result; a skill the person marked "not part of my job" is
shown as such and is never evidence; from plan v1.6, a qualification marked expected is
never met, and a person with no role sees no "usual in your role" panel; `make check` and
`make acceptance` pass.

Register (plan v1.5): MAP1-01, MAP1-06, ASSESS-02, ASSESS-03 and RDY1-03; the Task 10 parts
of MAP1-09, STATE-08, PROF-07, OPTN-08 and SEC-09; from plan v1.6, the Task 10 parts of
PROF-13 (entry facts) and STATE-11 (no empty panel without a role).

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

## Task 12a: Sprint 5 — the person's planning inputs, stored and confirmed (backend; split from Task 12, plan v1.5)

**Preconditions:** Task 7c complete (the reviewed pack 0.2.0, and session 2's answers to
D12–D17); Task 11 complete; Task 13a integrated (the worktree track: 13a, then 12a, then
13b, each after the last is integrated; this task changes the planning rules that 13a's
oracle and 13b's solver read). No human session, and it never waits for one: in the
suggested order it runs while session W2 is awaited.
**Parallel:** in the worktree, it may overlap the main-tree Tasks W2E, 6d, 3b and 6e, under
R15's rebase rules: it adds API, migrations and the generated client, so it rebases onto
`l0-local-release`, renumbers a migration whose number another task took and regenerates
the client. Not 13a or 13b (the same track), 10 or 12b.

Sprint card: "Sprint 5 Compile real options into an honest monthly model": the
person-supplied inputs of S5.3 and S5.4, stored first as a backend slice (plan v1.5). ADR
0013 decision 11 and ADR 0012 decision 11, as amended; spec sections 1 and 3 (the minimum
inputs, work rights and remote work), 10 and 12; Global Constraint 7. Before Task 12 was
split, these items were carried to it by Tasks 9 and 11.

Deliver, as backend and API with the client regenerated, and no interface:
1. **Every planning input the person supplies,** stored and confirmed as validated commands
   (an expected version and an `Idempotency-Key`, through `run_idempotent`): ADR 0013
   decision 11's list. That is the baseline, the continuation scenario, opening cash, living
   costs, the reserve, the three hard limits and the deficit cap, weekly availability,
   commitments, existing debts, the objective basis, the delay months, and per variant the
   work pattern, wage, funding statuses and entry confirmation. The model never fills them.
   An unasked direct-spend cap, payment cap or reserve leaves a route unresolved; unknown
   money is null, never 0.
2. **Outcome accept and override,** persisted (ADR 0012 decision 11): an accepted
   provisional mapping is the person's assumption, never a provider claim.
3. **Session 2's D12–D17,** applied as the product owner answered them (yes to each: ADR
   0013's planning rules stand).
4. **Stacked funding stays unresolved:** when a person confirms more than one support on a
   variant, the route is unresolved until stacking is confirmed. Exclusivity and
   eligible-cost caps follow the same rule.
5. **The monthly payment cap:** a cap broken by existing debt repayments alone gets a finding
   that names the repayments. (The question's words are Task 12b's.)
6. **An explicit "doesn't meet the entry requirements"** gets its own finding, still
   unresolved, with "check whether the provider accepts equivalent experience" as its next
   action.
7. **Ledger month rows:** a month row that depends on an unknown amount carries null or its
   own completeness flag, never a partial figure shown as a known one.
8. **Work rights and remote working** (BND1-04, BND1-05): the person's right to work in
   England, and whether they work remotely (with the employment country and timezone;
   remote never takes a city slot). Neither is inferred from a city. Unknown work rights
   leave a route unresolved, never ineligible. Whether these live in the profile or in the
   planning inputs is to be settled by Task 12a.

A forward-only migration, row-level security, and CHECKs that repeat the domain rules.

Acceptance: each input round-trips through its command, and a stale version is refused; an
unasked cap leaves a route unresolved; two supports on one variant leave it unresolved; a
cap broken by repayments alone names them; a month row resting on an unknown amount is
null, never a partial figure; unknown work rights never read as ineligible; `make check`
and `make acceptance` pass.

Register: closes PLN-11, BND1-04 and BND1-05; the Task 12a parts of OUT1-03 (overrides
stored), OPTN-03 (the inputs the checkpoint confirms), PLN-06 (stacking) and API-05 (the
confirmed inputs a solve needs).

## Task 12b: Sprint 5 — the Options chapter: review checkpoint, "add an option yourself" and the funding corpus + Sprint 5 review (split from Task 12, plan v1.5)

**Preconditions:** Tasks 12a and 10 complete; Task 7c complete (the reviewed pack; session
2, with its H-07 and H-13 records, and Task 11 come before it); session W2 held (R10). From
plan v1.6: Task 12c complete (the tuition fee loan), and Task 7f complete (the reviewed
school-leaver option pack, after the school-leaver pack session; R10). No dependency on Task
8.
**Parallel:** none. Tasks 13b and 12c change `careerwright/planning`, as this task's planning
catalogue does (rules 10 and 19); Tasks 10, 14 and 7e share the Options chapter or the
planning catalogue.

Build the Options chapter as its place in the world, to Task W2's design references (plan
section 4; R13). Its moment, a gap's first credible bridge, is Task M's (plan v1.5).

Sprint card: "Sprint 5 Compile real options into an honest monthly model". Slice: S5.3,
S5.7 (plan v1.5), the Options chapter UI, the three-funding-page corpus, remaining
acceptance, the coherence review. Spec sections 10, 13, 14; ADRs 0011 and 0013 as amended.

From plan v1.5:
- **The checkpoint collects and confirms the planning inputs** Task 12a stores, in one
  place, each with its meaning in plain words; the payment cap's question says what session
  2's answer to D15 means. Accepting or overriding a provisional outcome mapping uses Task
  12a's commands.
- **"Add an option yourself"** (S5.7): the person pastes a course or funding page's text, or
  types its details. It is saved as their own workspace record, `review_state: proposed`,
  dated, with its source, and shown as not reviewed. The planning catalogue reads it beside
  the pack, and a route built on it is qualified, never an unqualified "affordable and
  feasible" (ADRs 0011 and 0013, amendments). How values are read from pasted text (typed by
  the person, chosen by them as spans of the text, or the model-quotes pattern that Task 7e
  builds for live research) is to be settled by Task 12b; no new run kind unless the
  settled way needs one.
- **A target with no reviewed options** says so in plain words, and offers "add an option
  yourself".
- **The facts the route search lacks** (Task 13a's measurement, its report's "The answer
  for Task 13b"). In the reviewed option pack 0.2.0 every offering lacks at least one fact
  the route search needs (a start date, a cost, weekly hours or an entry confirmation), so
  today every reviewed target's search says "unresolved", never a route. The checkpoint
  shows, for each option, which fact is missing, in plain words. The person can supply it as
  their own figure, labelled as theirs and not reviewed, or choose a stated intake. Entry
  confirmations come from Skills (Task 10) where they are readiness facts. The search then
  runs on what they supplied. Where a supplied figure is stored is to be settled by Task
  12b.
- The live path's scoring on the funding pages moves to Task 7e, which builds the funding
  extractor (TEST1-13).
- From plan v1.6 (the product owner's school-leaver decisions; the school-leaver walk):
  - **Someone not working:** the checkpoint's words work for a person with no job. The
    baseline can be "staying in education", and "not working: 0 hours, £0" is said plainly.
  - **The entry confirmation reads qualifications** (Task 6f): it names the qualification an
    entry requirement asks for, and one the person expects reads "if you get your grades":
    unresolved until confirmed, never met.
  - **Each scheme's age rule beside it** (the pack holds it): shown, and never applied to an
    age Careerwright doesn't know.
  - **A tuition fee loan** (Task 12c): the checkpoint asks whether a tuition fee loan pays a
    degree's fee straight to the university, and its status, through Task 12c's command,
    and says in plain words that it is a loan to repay later, not the person's own money.
  - The reviewed school-leaver pack version (Task 7f) is the one this task pins.
- The controller's carried items for this task come in the dispatch.

Deliver the Options chapter per the design: curated comparison by gap, pin/exclude,
provider provenance, conditional funding, missing critical fields, scope bounds,
removed-candidate counts, explicit review checkpoint; when limits are exceeded ask the
user to retain variants — never silently truncate to the first 24 options or two intakes.
Show why a route may fail workload, payment or cash constraints using the Task 11 model.
Show the pack's date and each record's review state, and keep `proposed` records
explorable but out of any unqualified "affordable and feasible" result (R9, OPTN-08,
OPTN-09). The three funding pages are the option pack's (Task 7b, in the reviewed version
Task 7c published), consumed, not curated. Record session 2's outcomes from the product
owner's own record: H-07's Sprint 5 part and TEST1-14. (H-13 is already transcribed in the
register, plan v1.5; its misunderstandings are Task 14's scope inputs.)
`docs/reviews/sprint-5.md`.

Acceptance (plan v1.5, beside the sprint card's): an added option round-trips as a
not-reviewed record with its source, and a route resting on it reads qualified; a target
outside the pack shows the plain line and the add action; the checkpoint never truncates
silently; for each option the checkpoint names the fact the search lacks; P01, with the
missing facts supplied at the checkpoint, gets computed routes from the route search (shown
in Routes from Task 14), each qualified where it rests on a figure the person supplied, and
without them the result names what is missing, never "no route"; from plan v1.6, a person
not working reads "staying in education" and "not working: 0 hours, £0", an expected
qualification reads "if you get your grades" and is never met, each scheme shows its age
rule, and a tuition fee loan reads as a loan to repay; `make check` and `make acceptance`
pass; the visual review package per R2.

Register: closes OPTN-11, OPTN-03, OPTN-06, OUT1-09 and BND1-07, and from plan v1.6 OPTN-15;
the Task 12b parts of OPTN-05, OPTN-07, OPTN-08, OPTN-09, OPTN-13 (the missing facts at the
checkpoint), OUT1-04, FUNDING-04, FUNDING-05, FRESH-02, FRESH-06, ACQ-07, API-06, STATE-06 (a
changed constraint shows the options it affects before invalidating them), TEST1-09 (the
pack's funding pages consumed) and TEST1-14, and from plan v1.6 of PROF-13 (the entry
confirmation) and FUNDING-06 (the checkpoint asks about the loan).

## Task 12c: Sprint 5 — a tuition fee loan is a loan to repay (backend, plan v1.6)

**Preconditions:** Tasks 12a and 13b complete and integrated (the planning inputs and the
search this task changes). The product owner's school-leaver decision 6 of 1 November 2026
(yes) and the specification's section 22 row that records it. No human session, and it
never waits for one.
**Parallel:** in the worktree, it may overlap the main-tree Tasks 6f, 6e and 10, which
don't change `careerwright/planning`. It may add API, a migration and the generated client,
so it follows R15's rebase rules: it rebases onto `l0-local-release`, renumbers a migration
whose number another task took and regenerates the client. Not 12b or 14: they change
`careerwright/planning` too (rule 19). Task 7f follows it in the worktree track. It runs
before Tasks 7f, 12b and 14.

Sprint cards: "Sprint 5 Compile real options into an honest monthly model" (S5.2 as plan
v1.6 amends it) and "Sprint 6a Prove the optimiser and layers on instances that complete"
(the independent check). Spec sections 10 ("Funding and finance discovery"), 12 (FIN-1:
"Third-party payments made directly to a provider are represented consistently on both
sides or excluded from both; never count them twice") and 22 (the tuition fee loan row);
ADR 0013 decisions 5 and 11 and ADR 0016 (the pruning rules and the oracle), as amended;
Global Constraint 1. The school-leaver walk
(`planning/audit-no-job-yet.md`), finding 2.

Why: a loan is never support today, so a degree's fee counts as the student's own spending
and cash, and against a student's limits a degree would read "not feasible in this monthly
model" (the walk's reading of the rules; the checker's verdict was not traced). The product
owner's decision: a tuition fee loan paid straight to the university is not cash out of the
student's pocket; it is shown as a loan to repay later.

Deliver, as backend and API with the client regenerated, and no interface:
- **A tuition fee loan paid straight to the provider** is something the person can state on
  an option, beside its supports, through Task 12a's command (an expected version and an
  `Idempotency-Key`): the amount it pays and its status (the funding statuses, ADR 0013). The
  fee it pays is not the person's own money: it is in neither their cash ledger nor the
  direct spending the direct-spend cap reads, nor the monthly payment cap's payments. It is
  never support, a grant, income or a receipt.
- **Shown as a loan to repay later:** the route's result carries the amount borrowed and
  when, as a loan to repay. What Careerwright doesn't know about its repayment stays
  unknown, never 0. The result carries facts and codes, never a sentence (R11); Tasks 12b
  and 14 word it.
- **Its status:** only a loan the person confirms is approved takes the fee out of their own
  spending unconditionally. One not yet approved makes the route conditional on it, beside
  the route where they pay the fee themselves, with a blocking verification (the funded and
  unfunded rule, FUNDING-05). An unknown amount leaves the route unresolved, never £0.
- **How it enters the economic cost** (the cost over the horizon) is to be settled by Task
  12c and stated in plain words in ADR 0013's amendment. If it changes which routes are best
  trade-offs, it goes to the product owner first, as one question (R14).
- **Nothing else changes:** every other loan, a maintenance loan paid to the student
  included, is still refused as support and stays information to verify (spec section 10).
  Careerwright chooses no borrowing. Existing debt stays a fixed commitment. TRACE-01, the
  A–I fixture and every regression family keep their expected values.
- **The search and its independent check:** each new or changed checker finding is classed
  for the search's pruning rules (ADR 0016: is it the variant's own, repeated in every route
  containing it? rule 2 then sets the option aside), and the pruning version goes up if a
  rule changes. The independent oracle writes the rule again from its own reading of the
  specification, its section 22 row and ADR 0013, sharing no code with the checker. Its
  generated instances include the loan in every status, and the search must give exactly
  the oracle's archive, objectives, layers and outcome.
- A forward-only migration with CHECKs that repeat the domain rules, if the stored inputs
  change.
- ADR 0013 and ADR 0016 amendments. Propose the matching `CLAUDE.md` planning line ("a loan
  is never support") with its exact words, for the product owner's approval.

Acceptance: a constructed degree route whose fee a confirmed tuition fee loan pays: the fee
is in neither the cash ledger nor the direct-spend or payment-cap figures, and the result
carries the loan to repay with its amount; the same loan not yet approved gives a
conditional route beside the self-paid one; an unknown amount leaves the route unresolved,
never £0; a maintenance loan stated as support is still refused; the oracle agrees with the
search on generated instances with the loan; a stale version is refused; TRACE-01, the A–I
fixture and the existing regression families keep their values; `make check` and `make
acceptance` pass.

Register: the Task 12c parts of FUNDING-06 (the checker, the oracle and the search; Tasks
12b and 14 show it) and FUNDING-04 (its L0 change).

## Task 13a: Sprint 6a — enumerator, checker, oracle and layers on instances that complete (S6.1, S6.2, S6.5–S6.7)

**Preconditions:** Task 7c complete (the reviewed option pack it solves on; Task 11 and
session 2, with the reviewed TRACE-01 checker, come before it; R10).
**Order (plan v1.5):** dispatched on 2026-10-31 in the worktree `wt-13a`, beside Task A1's
documents (R15), before the Skills, Options and Routes tasks; its measured sizes decide
Task 13b's scope. Its scope is unchanged. It is the first of the worktree track (13a, then
12a, then 13b, each after the last is integrated; dependency rule 10).
**Parallel:** may overlap any task outside `careerwright/planning` and the optimiser: Task
A1's documents, W2E, 6d or 3b. Not 12a or 13b: they follow it in the worktree track, because
Task 12a changes the planning rules this task's oracle reads.

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

## Task 13b: Sprint 6b — archive, caps, cancellation and ranking benchmark (S6.3, S6.4, S6.8) + Sprint 6 review

**Preconditions:** Task 13a complete, with its measured sizes; Task 12a integrated (the
worktree track: 13a, then 12a, then 13b, each after the last is integrated; Task 12a changes
the planning rules this task's solver reads). No human session.
**Parallel:** may overlap any task outside `careerwright/planning` and the optimiser: W2E,
6d, 3b, 6e or 10. Not 12a (the same track), 12b or 14: they change `careerwright/planning`
too (Task 12b's planning catalogue reads the person's own options).

Sprint card: "Sprint 6b Make the search durable and bounded at full scale". Whole sprint.
Spec section 12 (OPT-1, ROU-1), 17 (the cancellable solver process), 20 (TEST-1).

**Scope, sized from Task 13a's measurements** (plan v1.5; the audit's ruling). L0 solves
over four targets and ten learning options, so its instances may complete in seconds. These
stay whatever the measurements show: the 30 s, 1,000,000-state and 50,000-feasible caps,
their exact stop reasons, the separate rank stage and the truncation wording ("Best
trade-offs found", the instance size and the narrowing), and a solve the person can start as
a run. The disk-backed archive with its checkpoints and resume, the cancellable child
process and the 50,000-point ranking benchmark are sized to what the measurements show. They
are specification M0 requirements (OPT-1; ARC-1's stack), so leaving any of them out of L0
needs the product owner's yes and a note in the specification's revision record; which of
them L0 needs is to be settled by Task 13b, put to the product owner as one question (R14).
**Settled, 31 October 2026:** the product owner said yes to leaving out the disk-backed
archive with its checkpoints and resume, and the separate child process, on Task 13a's
measurement (the largest realistic L0 search, a pack-sized catalogue at 24 months, takes
about 26 s). The specification's revision record says so (section 22, "L0 deferrals"). The
50,000-point ranking benchmark stays.

Deliver the archive of every distinct feasible schedule encountered, dominated ones included,
kept in memory under the caps (no checkpoints or resume: a crashed solve is a failed run,
started again under a new attempt ID, never a truncated result), with an idempotent solve
identity; 30 s / 1,000,000 states / 50,000 feasible caps with exact stop reasons; separate
rank stage; an efficient two-objective layering qualified against Task 13a's iterative
peeling, equal to it on every instance that completes; the solve run durably via DBOS in the
worker, with cancellation reaching the search at its next check.
A truncated result leads with "Best trade-offs found", states the instance size and names
the narrowing (fewer concepts, one start, a shorter horizon) that Task 13a's measured sizes
suggest (OPT1-15). Regression family LIMITS (caps, cancellation, truncated empty).
Benchmark 50,000-point ranking. `docs/reviews/sprint-6.md`, covering 6a and 6b.

Register (plan v1.5): the OPT1 and LIMITS rows it owns, as sized (the archive, the caps and
their stop reasons, cancellation, the rank stage and the benchmark; OPT1-03's disk archive
and OPT1-09's child process recorded as L0 deferrals), STATE-03 and
DUR-05; the Task 13b part of API-02 (`SOLVE_LIMIT_REACHED`).

## Task 14: Sprint 7 — coordinated route comparison (S7.1–S7.6) + Sprint 7 review

**Preconditions:** Tasks 13b and 12b complete (plan v1.5), and Task 12c (plan v1.6);
session 2's findings exist (the H-13 record, read as scope input); session W2 held. It
closes on its own checks (plan v1.5: session 3 is merged into the end-to-end session, after
Task 15).
**Parallel:** none: it joins the solver, the planning catalogue and the Options chapter.

Sprint card: "Sprint 7 Make route comparison the signature experience". Whole sprint.
Spec sections 12–14 (VIS-2, ROU-1, AIR-1).

Scope inputs (plan v1.1): every dangerous misunderstanding recorded at session 2 (H-13)
is addressed or explicitly carried with a reason. From plan v1.5 the named input is plain
words for every cost and condition: at session 2 the product owner answered "No idea. Sounds
like psychobabble." and "don't understand "conditional", or "fixture" or the difference
between economic cost and direct cost. Don't understand "once its assessed report is passed"
or "Its print snapshot states" - frankly, the language is inaccessible.", and added
"Confusion can make one indecisive and give up." TRACE-01 and DIRECTAI keep their separate
labels. Also from plan v1.5:
- A route built on an option that isn't reviewed (one the person added, or one research
  found) says so in plain words and is qualified, never an unqualified "affordable and
  feasible".
- The real Routes chapter replaces the demo route preview, which Task W2E took out of the
  person's path.
- **Routes on the facts the person supplied** (Task 13a's measurement, its report's "The
  answer for Task 13b"). In the reviewed option pack 0.2.0 every offering lacks at least one
  fact the route search needs (a start date, a cost, weekly hours or an entry confirmation),
  so today every reviewed target's search says "unresolved", never a route. Task 12b's
  checkpoint names each missing fact and lets the person supply it, as their own figure
  labelled theirs and not reviewed, or choose a stated intake; the search runs on what they
  supplied. A route resting on a figure the person supplied is qualified, and says so in
  plain words. Without the facts, Routes names what is missing, never "no route".
- The solve's stage checks (API-05): a budget-qualified solve needs the person's confirmed
  limits, and an economic solve a horizon and a baseline (Task 12a's inputs).
- Four planning-model gaps carried from the completed backend tasks: information-gathering
  and waiting actions (PLN-01), the search and review step before an offer gate (OPTN-04),
  a verification milestone after an assessed completion and experience beyond an offering's
  own outcomes (PLN-04, OUT1-08). Each is to be settled by Task 14: modelled, or recorded as
  an L0 deferral with the product owner's yes. Truncated coverage is the expected case
near the bound (OPT1-15): lead with "Best trade-offs found", state the instance size and
name the narrowing that would let the search complete, using Task 13a's measured sizes. Show
the option pack's date and review states wherever pack records appear in a route (R9).
- From plan v1.6 (the product owner's school-leaver decisions of 1 November 2026):
  - **A route longer than the model,** such as a three-year degree: Routes says plainly
    that it is longer than Careerwright can plan yet, never "no route", "not feasible" or
    impossible. Words only, no planning change (spec section 1's explanatory
    sketch and unsupported-model state; specification section 22).
  - **A fee a tuition fee loan pays** (Task 12c) shows as a loan to repay later, with its
    amount, never as support or the person's own spending; a route resting on a loan not yet
    approved reads as conditional on it, beside the route without it.

Deliver the Routes chapter as its place in the world, to Task W2's design references (plan
section 4; R13); its moment, the credible route, is Task M's (plan v1.5). Using real solver
output:
per-target discrete time–cost scatter with cost definition/baseline/horizon/currency/
bounds/coverage beside the chart; readable F1–F3 with family grouping and named dominance
explanations; one documented deterministic comparator rule; stress scenarios shown
separately; exact numeric inputs + keyboard sliders; view filtering preserves ranks;
explicit reranking; linked Gantt, step cards, monthly financial table, evidence drawer;
section 4's motion with its still version; paginated archive and bounded projection
with shown/total counts. Property and browser tests for selection/filter consistency;
TRACE-01 renders A/B/C F1, D F2, E F3; A–I fixture uses direct-spending labels; measure
interaction budgets. Third visual review package (R2), checked against what session 2
showed; from plan v1.5 its human part is the end-to-end session, formative.
`docs/reviews/sprint-7.md`, closed on this task's checks; the end-to-end session's outcome
is added later from the product owner's own record.

Acceptance (plan v1.5, beside the sprint card's): a route built on an option the person
added (Task 12b) reads qualified on screen, in plain words, never an unqualified
"affordable and feasible"; P01, with the missing facts supplied at the checkpoint, gets
computed routes in Routes, each qualified where it rests on a figure the person supplied,
and without them Routes names what is missing, never "no route"; from plan v1.6, a route
longer than 24 months says it is longer than Careerwright can plan yet, and a fee a tuition
fee loan pays reads as a loan to repay; `make check` and `make acceptance` pass.

Register (plan v1.5): the VIS2 rows, ROU1-04, PARETO-04, DIRECTAI-02 and TRACE01-05; the
Task 14 parts of OUT1-04, OPTN-13 (routes on the supplied facts), RDY1-02, API-02
(`NO_ROUTE_IN_BOUNDED_MODEL`), API-04, API-05, API-06 (a route locates its supporting
spans), DUR-03, STATE-06 (a changed constraint shows the routes it affects before
invalidating them), UI-09 and FRESH-06; PLN-01, PLN-04, OPTN-04 and OUT1-08, as settled.
From plan v1.6: closes PLN-12; the Task 14 part of FUNDING-06 (Routes shows the loan).

## Task 15: Sprint 8 — chosen plan, progress, revision and exports (S8.1–S8.6) + Sprint 8 review

**Preconditions:** Task 14 complete (plan v1.5: it closes on its own checks; session W2
came before it). No further session before this task; H-04 (Safari, print) is recorded "not
run — requires human" with its checklist (R2) and is not a dispatch precondition.
**Parallel:** none.

**Two slices** (plan v1.5): **15A** first: S8.1, S8.2, S8.5 and S8.6 (the snapshot, the
Plan chapter, print, JSON and calendar), with the workspace's data export, already in the
API, given its button beside the plan's exports. Then **15B**: S8.3 and S8.4 (revise and
replan), with the revision history of the person's answers: a small view over the profile's
saved versions, which the API already lists (`GET .../profile/versions`), and from which undo
already works. It is an M0 promise (spec section 3: "Undo and revision history are always
available"; STATE-06), so it is not an L0 deferral (the controller's ruling, 2026-10-31).
Both slices are M0 and both stay in L0. Finish: the end-to-end session's package (R10,
R2), in plain words, with its questions and a record sheet, each item "not run — requires
human".

Build the Plan chapter as its place in the world, to Task W2's design references (plan
section 4; R13); its moment, committing to the chosen path, is Task M's (plan v1.5). Print
stays light and ink-efficient.

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

Register (plan v1.5): the PLAN and EXP rows, AIR1-09, VERSIONS-02, TRACE01-04, FRESH-05 and
SEC-10; the Task 15 parts of MODEL-04 (a saved plan prints with the key revoked), API-06,
DUR-06, SEC-06, OPT1-15 and STATE-06 (the answers' revision history on screen, 15B).

## Task M: Sprint M — the chapters' moments (plan v1.5)

**Preconditions:** the end-to-end session held, with the product owner's own order of the
moments (R10); Task 8 complete.
**Parallel:** none.

Sprint card: "Sprint M Give each chapter its moment". Plan section 4; ADR 0014 (amended
2026-10-31: the moments' sprint).

Deliver, in the product owner's order, each within the budget the controller states in the
dispatch (agent hours and the frame budget). A moment they chose to skip is not built.
- The first answer's ignition.
- Not a candidate: the unexpected connection. Shared skills are "Always a plain line" (the
  product owner, 1 November 2026); nothing is lit or played for them.
- Decisions previewed in the world: suggestions drawn as rings, the open one singled out;
  "Make this a target" previewing its destination before it is saved.
- The overlooked strength: its proposal and confirm step (the `strength_proposal` run, built
  in Task W2's slice W2B), never asked for on a support turn (`held_back`, a 422
  `INSUFFICIENT_EVIDENCE`, whose words never sit beside the support panel), and its
  destinations on the horizon, aligned with the first slate's. Its provisional rules (ADR
  0014 decision 3) are put to the product owner with its interface, one line each (R14).
- A gap's first bridge (Options), the credible route (Routes), committing (Plan) and
  progress landmarks.
- **Without a job, the world still answers** (plan v1.6; the school-leaver walk): when the
  role names no ESCO occupation, the overlooked strength's horizon is the latest slate's
  suggestions, not only the role's first destinations, so a person still exploring can
  earn it; and the first answer's ignition also answers a first saved "what
  you enjoy" (its first destinations from the skill search), so the world responds to a
  person who has never had a job.
- Sprint W's revelation acceptance: every revelation's sentence and evidence are in the DOM,
  the still world says the same, and a risk word holds every revelation back.
- The frame re-measure on the busiest real scene and a scene with a name that cannot be
  placed. Warn the product owner first: the measurement opens a window on their screen.

Every moment keys off a state the backend computed; none changes a number, a state or a word
in the exact layer, and none pushes a decision off the first screen (Global Constraint 11).

Acceptance: the plan's Sprint M acceptance; frame times reported with device, browser and
scene; the existing journeys pass with motion on and off; `make check` and `make
acceptance` pass. `docs/reviews/sprint-m.md`, with an agent pre-review only (R2).

Register: the moments' rows of the world family (owned here), WLD-12 among them (plan
v1.6); the frame-budget rows with Task 16.

## Task 16: Sprint 9 — local release qualification and handover (S9.1–S9.6)

**Preconditions:** every remaining task complete (plan v1.5): W2E, 6d, 3b, 6e, 12a, 13a,
13b, 10, 12b, 14, 15, 7e, 8 and M, and from plan v1.6 6f, 12c and 7f, after the earlier ones
(6b, 6c, 7, 7d, 7b, 7c, 9, 11, W1 and W2); release qualification needs all six chapters.
Sessions 1, 2, W1, W2, the school-leaver pack session and the end-to-end session held
(R10). The Sprint 9 human gates (H-01, H-03, H-04, H-05, H-08, and from plan v1.6 H-15) are
prepared as checklists and recorded "not run — requires human" (R2); none is a dispatch
precondition. Five participants are available for the task sessions (H-05; the product
owner, 2026-10-31).
**Parallel:** none.

From plan v1.5: every rubric category must reach at least 4 (H-01, the release bar); the
world's frame budgets are measured again on the release candidate, with the product owner
warned first; the live journey includes a persona whose target is outside ESCO (TEST1-15);
the discovery evaluation adds its relevance-only and common-careers baselines (DIV1-08),
and its release report states that L0 measures no language or region disparities because
it has one language and one region (the plan's own note, plan section 1); and the release
checks of R10 are prepared, including the name review of committed excerpts before any push.

From plan v1.6 (the product owner's school-leaver decision 1 of 1 November 2026): school
students aged 17 and 18 are in scope, so before any real student uses Careerwright a person
checks the rules for young people's data, and the release report carries a privacy note on
it beside the privacy decision (H-08). Its checklist is prepared here, and it is recorded
"not run — requires human" (H-15) until a person records it; no engineering check stands in
for it.

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

Register (plan v1.5): the Task 16 parts of DIV1-08 (the baselines, exposure concentration and
long-tail coverage; its language and region part as the plan's note), REC1-09 (the powered
comparison, its pass rule decided first), TEST1-15 (the live journey), PLN-09, MODEL-03
(every adapter's contract tests on the final candidate) and API-02 (every error code on the
final candidate); the frame-budget rows with Task M; the human gates H-01, H-03, H-04, H-05
and H-08, and from plan v1.6 H-15, prepared and recorded "not run — requires human".

## Task 17: Sprint 10 — operator's manual and friction pass (S10.1–S10.5)

**Preconditions:** Task 16 complete (plan v1.5: it follows Task M). No human session. H-14,
a person following the manual, is prepared as a checklist and recorded "not run — requires
human" (R2); it is not a dispatch precondition.
**Parallel:** none.

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
