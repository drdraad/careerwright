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

## Environment facts (the product owner's Mac, from 2026-11-02)

The product is Careerwright (called Nessa until 2026-10-30). The build ran in a Claude Code
cloud container on 1–2 November 2026 (its note, `planning/env-cloud.md`, is a record) and
came back to the product owner's Mac on 2026-11-02.
- macOS arm64, Docker Desktop (engine 29.1.2), uv 0.9.18, Node 24 through nvm, pnpm
  10.33.2. Host Python is 3.14; the backend uses only `backend/.venv` (uv-managed Python
  3.12, built with `uv sync --locked`).
- Main tree: `/Users/darianraad/Code/careerwright`. Worktrees:
  `/Users/darianraad/Code/careerwright-wt/<id>`, branch `wt-<id>`.
- Integration branch: `claude/confident-ramanujan-ux3saw` (the controller's;
  `l0-local-release` was merged into `main` on GitHub). Only the controller moves it.
- Fast checks: `make check`.
- Docker: PostgreSQL 16 and the Firebase Auth emulator run only in containers.
  Implementers never start Docker, pull or build images. The controller runs
  `make acceptance` once per batch, under the lock
  `/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock`; report it as "not
  run: the controller runs acceptance". A focused stack or integration test runs only when
  your dispatch asks for it, under the same lock.
- Web requests and live calls: the controller makes every web fetch and every live call.
  Implementers and reviewers make none.
- `META_API_KEY` and the Adzuna credentials are in `/Users/darianraad/Code/careerwright/.env`
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
      (`/Users/darianraad/Code/careerwright`), the rest in git worktrees
      (`/Users/darianraad/Code/careerwright-wt/<id>`, branch `wt-<id>`).
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
  unresolved for a protected gate; nothing finds a person ineligible). One marked expected
  reads "if you get your grades", the Options chapter's words (the product owner, 2 November
  2026, for the demo video, `docs/demo/demo-video-script.md`).
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
never met and reads "if you get your grades", and a person with no role sees no "usual in
your role" panel; `make check` and
`make acceptance` pass.

Register (plan v1.5): MAP1-01, MAP1-06, ASSESS-02, ASSESS-03 and RDY1-03; the Task 10 parts
of MAP1-09, STATE-08, PROF-07, OPTN-08 and SEC-09; from plan v1.6, the Task 10 parts of
PROF-13 (entry facts) and STATE-11 (no empty panel without a role).
