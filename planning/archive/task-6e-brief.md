# L0 sprint tasks (execution breakdown)

This file breaks `docs/plan/development-plan.md` (the local development plan, v1.6) into
implementation tasks for agent execution. Authority order: product specification
(`Careerwright_Product_Specification.md`, v1.3) → development plan local overrides → this file.
What is done and what comes next is in "Current position and next tasks" below. The
remaining tasks follow the order, dependency rules and dispatch preconditions below (ADR
0008), as Task A1 amended them with the product owner's approval of 2026-10-31, and as plan
v1.6 amended them with the product owner's school-leaver decisions of 2026-11-01.
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

## Environment facts (verified 2026-10-27)

- macOS arm64. Docker 29.1.2 (aarch64 engine). uv 0.9.18. pnpm 10.33.2. Node v24.11.1.
- Host Python is 3.14 only: use a uv-managed Python 3.12 (`uv python install 3.12`).
- Host has a PostgreSQL 18 *client* only; the server must be PostgreSQL 16 in Docker.
- No Java and no firebase CLI on the host: the Firebase Auth emulator must run in a
  container.
- `META_API_KEY` is in `/Users/darianraad/Code/careerwright/.env` (gitignored).
  Load it from that file in code/tooling. Never print it, echo it, pass it as a command
  argument, write it elsewhere, or commit it.
- Git: work on branch `l0-local-release`. Commit coherent increments with messages ending
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
- R12 Evidence before polish (plan v1.2). From Task 7b to session 2 (Tasks 7b, 9 and 11)
  the critical chain took priority. A refactor or hardening that no failing check, reproduced
  defect or Global Constraint requires went to the final-review list in the progress ledger,
  never into those tasks. From plan v1.5 it is permanent, as R13.
- R13 Path before polish (plan v1.5; permanent, for every remaining task, Sprint W
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
- R14 Review rules (the product owner's approval, 2026-10-31; the audit report, section 6).
  The controller and every reviewer follow them:
  - Keep reviewing hard, and fix within the task: anything that changes a decision (ready
    or not, feasible or not, unknown versus none, money, eligibility), lost input, fetch
    safety, the support panel, the first ten seconds.
  - Small things always wait for the final review (R13). The exceptions: a finding from the
    product owner's session, or a failing check.
  - The sentence rule (R11) for every sentence a person reads.
  - The product owner judges suggestion quality on a fixed set of real examples. Reviewers
    don't loop on it: at most one matching round per task.
  - Bound loops by kind of finding. When one kind comes back in two re-reviews in a row,
    the next step is a rule, a fail-safe or a one-line question to the product owner, never
    another patch. Wording, matching and visual work stop at three rounds; security, money
    and data keep five.
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
- R15 Parallel work (the product owner, 2026-10-31: "Where subagent work can be done
  cleanly in parallel, do so but coordinate well to avoid them causing conflicts").
  - Up to two implementers at once: one in the main tree, one in a git worktree
    (`/Users/darianraad/Code/careerwright-wt/<id>`, branch `wt-<id>`), on disjoint
    modules. Each task card's **Parallel** line says which tasks it may overlap; a card
    whose line says none runs alone.
  - In the main tree, commit with a pathspec only, never `git add -A` or `git commit -a`.
  - Shared documents (`docs/requirements-register.md`, `docs/plan/*`) change only in a
    task's last commit, after its rebase, and only the rows or lines its work closes.
  - One `make acceptance` at a time, under the lock `.superpowers/acceptance.lock` (take it
    with `mkdir`, remove it with `rmdir` the moment the run ends, pass or fail).
  - The controller integrates a worktree by fast-forwarding `l0-local-release` after the
    implementer rebases onto it; an implementer never moves `l0-local-release`. On a
    conflict in the generated client, regenerate it; a migration whose revision number
    another task took is renumbered to the next free one.
- R16 Speed (the product owner, 1 November 2026: "I'm finding this development process too
  slow"; they chose all four of these).
  - **One reviewer per piece,** covering both the experience and the code, instead of two
    halves.
  - **One fix round at most.** Inside a piece, only safety, truth (a false statement, a
    failure shown as an empty success, a false evidence record) and lost-input problems are
    fixed. Everything else goes on a list: the product owner's session sheet, Task M or the
    final review. After the fix round the controller checks the diff and the tests itself; a
    second review runs only for a Critical finding.
  - **Full checks once per piece.** Implementers run `make check` after each change and
    `make acceptance` once, at the end of the piece (after its fix round, if any). A flaky
    failure is re-run once; a second failure is a finding.
  - **Up to three implementers at once,** on disjoint modules: one in the main tree and up to
    two in worktrees. This widens R15's two; R15's other rules stand. Each card's
    **Parallel** line still decides what may overlap.

## Order, dependencies and dispatch preconditions (plan v1.6, ADR 0008)

Execution: from plan v1.5, up to two implementers at once, on disjoint modules (R15). Each
remaining card's **Parallel** line names the tasks it may overlap. Until v1.5 the
controller ran one implementer at a time; where the assessment handover
(`docs/plan/l0-assessment-handover.md`) marked tasks as parallel (∥), they ran one after the
other.

Dependency rules (rules 1–6 are met; rules 7, 9–13 and 15 are as amended in plan v1.5, and
rules 7, 11, 13, 15 and 16 again in plan v1.6; rules 16–18 came with v1.5, and rules 19 and
20 with v1.6):

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
7. Task 10 after Task 7c, Task 6d and session W2 (and Task 6f, which comes before session W2,
   plan v1.6). Task 12 is split in plan v1.5: Task 12a (the stored planning inputs,
   backend) after Task 7c and after Task 13a is integrated (rule 10); Task 12b (the Options
   chapter) after Tasks 12a and 10 and session W2, and from plan v1.6 after Tasks 12c and 7f
   (the tuition fee loan, and the school-leaver option pack it reads; rules 19 and 20).
8. Session 1 before Task 8, and before any page body is retained beyond the classes it
   permits (held 2026-10-28).
9. Task 8 after Task 7c, session 1, Task 15 and the end-to-end session (plan v1.5: Roles
   comes after the decision path, and the end-to-end session may still reshape L0).
10. Task 13a after Task 7c (the reviewed pack's instances). Task 13b after Task 13a, its
    scope sized from Task 13a's measured sizes, and after Task 12a is integrated. The
    worktree track (plan v1.5): Tasks 13a, then 12a, then 13b, one at a time in the
    worktree, each started after the last is integrated. Task 12a changes the planning
    rules that 13a's oracle and 13b's solver read, so none of the three overlaps another.
11. Task 14 after Tasks 13b, 12b and 12c (plan v1.6) and session W2, with session 2's H-13
    record as a scope input; it closes on its own checks (session 3 is merged into the
    end-to-end session).
12. Task 15 after Task 14: slice 15A first, then 15B.
13. Task 16 after every remaining task (W2E, 6d, 3b, 6e, 12a, 13a, 13b, 10, 12b, 14, 15,
    7e, 8 and M, and from plan v1.6 6f, 12c and 7f) and after sessions 1, 2, W1, W2, the
    school-leaver pack session and the end-to-end session: release qualification needs all
    six chapters.
14. Task 17 after Task 16 (plan v1.3): the manual describes the qualified candidate, and its
    small fixes are re-qualified on top of it.
15. The world (plan v1.4, amended in v1.5 and v1.6): Tasks W1 and W2's slices W2A, W2B and
    W2C part 1 are done; Task W2E closes Task W2 and Sprint W. Session W2 after Tasks W2E,
    6d, 3b, 6f and 6e. The interface tasks (10, 12b, 14, 15, 8 and M) wait for session W2;
    the backend tasks (12a, 13a, 13b, 12c) never wait for a session.
16. The role space and live sessions (plan v1.5, amended in v1.6): Task 6d after Task W2E.
    Task 3b has no task dependency. Task 6f after Task 6d (plan v1.6: it changes the same
    first question). Task 6e after Tasks 6f and 3b.
17. Options for any target (plan v1.5): Task 7e after Tasks 15 and 12b; it may start
    while the end-to-end session is awaited.
18. The end-to-end session after Task 15. Task M after the end-to-end session and Task 8.
19. The tuition fee loan (plan v1.6): Task 12c after Tasks 12a and 13b are integrated. It
    never waits for a session. It runs in the worktree before Tasks 7f, 12b and 14, and
    never beside 12b or 14: all three change `careerwright/planning`.
20. The school-leaver option pack (plan v1.6): Task 7f after Task 12c, in the worktree. Its
    second half (publishing the reviewed version) after the school-leaver pack session.
    Task 12b after Task 7f.

Suggested order (plan v1.6; the plan's section 6 "Order from here (v1.5)" gives each
remaining v1.5 step's scope and agent hours, and "Order from here (v1.6)" the new steps), in
two tracks (R15):
- The main tree: 6d (its last slice) → 6f → 6e → session W2 → 10 → 12b → 14 → 15 (15A,
  then 15B) → the end-to-end session → 7e → 8 → M → 16 → 17 → the final review.
- The worktree, beside it: 12c → 7f (its first half, the school-leaver pack session, then
  its second half), each started after the last is integrated. Task 12c may overlap 6f, 6e
  and 10; Task 7f may overlap 6f, 6e and 10. Tasks 12b and 14 never overlap 12c: all three
  change `careerwright/planning`. Task 12b starts after 7f is integrated.
Backend tasks fill any wait for a session.

History: the v1.5 order was, in the main tree, Task A1's documents and the W2C part 1
re-review → W2E → 6d and 3b → 6e → session W2 → 10 → 12b → 14 → 15 → the end-to-end session
→ 7e → 8 → M → 16 → 17 → the final review, and in the worktree 13a → 12a → 13b (all three
done by plan v1.6). The v1.4 order (after session 2) was W1 → session W1 → 7c → W2 →
session W2 → 10 → 12 → 8 → 13a → 13b → 14 (closes after session 3) → 15 → 16 → 17, with backend tasks (7c,
13a, 13b) running while a session was awaited and interface tasks waiting for session W2.
The v1.1 order was 6b → 6c → 7 → 7d → 7b → 9 → 11 → session 2 → 7c → 10 → 12 → 8 → 13a →
13b → 14 (closes after session 3) → 15 → 16 → 17. Session 1 could be held at any point before
Task 8; holding it before Task 7b let 7b classify the pack's rights itself instead of leaving
every page "pending human rights review".

Dispatch preconditions: every remaining task card starts with a **Preconditions** line
naming the tasks and the human sessions it waits for (R10). A session that has not happened
blocks dispatch; it is never assumed, worked around or self-certified (R2).

Sprint reviews follow the order: the task that finishes a sprint writes its review, so
`docs/reviews/sprint-3.md` (Task 8) comes after `sprint-4.md` (Task 10) and `sprint-5.md`
(Task 12b), and `sprint-6.md` (Task 13b) covers 6a and 6b. From plan v1.5, `sprint-w.md`
is Task W2E's and `sprint-m.md` Task M's. Each review states the order it ran in.

## Current position and next tasks (2026-11-01, plan v1.6)

**Complete and reviewed:** Tasks 1–6, 6b, 6c, 7, 7d, 7b, 9, 11, 7c and W1; Task W2 (slices
W2A, W2B and W2C part 1) and Task W2E, which closed Sprint W (`docs/reviews/sprint-w.md`);
Task A1's approved changes, applied to the documents; the worktree track, Tasks 13a (the
route search core), 12a (the stored planning inputs) and 13b (the search as a bounded run),
each integrated; Task 3b (live sessions ready on Muse Wonder), integrated; and Task 6d's
slices A (facts instead of sentences; each target stored once) and B (the title flow over
ESCO and the ONS index). **Held:** sessions 1, 2 and W1. The ledger
(`planning/progress.md`) has every commit range and ruling.

**Finishing:** Task 6d slice C (seniority and industry, ESCO's list named as ESCO's, "not
part of my job", pasted CV text deferred), in the main tree, built to dc68d79; its last
commit and its review follow. Task 3b's first live run of the real-data path waits for the
product owner to paste their own key into the app; it joins session W2's preparation (Task
6e).

**Approved:** Task A1, the whole-solution audit (`docs/reviews/l0-audit-2026-10-31.md`; the
decisions page `docs/reviews/l0-audit-2026-10-31-summary.md`), by the product owner on
2026-10-31: "Approved - proceed. Where subagent work can be done cleanly in parallel, do so
but coordinate well to avoid them causing conflicts. Yes, I have 5 people who can try the
app before release." Its decisions 1 to 8 are all yes.

**The product owner's direction (2026-10-31), in their words:**
- "The visuals are important, but they must be subservient to having a practical, useful
  product."
- "I want to check that the development plan is still sensible, and get us back on track
  with the sprints, even if we have to refactor some of them to ensure coherency and
  pragmatism."
- "One thing that is really important to me is that we aren't limited to a prefilled list
  of roles - the real world is much more complex than those standardised job lists, and I
  want to avoid the frustration of your ideal job not appearing as an option to select.
  This is where deep research and LLMs have a part to play to fill out the "role space"
  more fully. I want it to feel like you have an omniscient career coach who knows all
  possible jobs that could fit you."
- "We can also start being a bit more generous with token use in human testing - I would
  like to use muse wonder for this."

**The product owner's decisions since plan v1.5:**
- 31 October 2026: leave the route search's disk-backed archive and its separate child
  process out of L0, on Task 13a's measurements (Task 13b's card; specification section 22).
- 1 November 2026: the unexpected connection is "Always a plain line": shared skills are a
  plain fact about two roles, never a discovery moment (ADR 0015). Task M picks or drops the
  Roles chapter's moment.
- 1 November 2026, in their words: "NB: I don't want to over-rely on existing skills in the
  process. Many users will be final year school students who have never had a job before."
  A walk through the whole path as a Year 13 student with no job (the controller's
  `planning/audit-no-job-yet.md`) found eight problems and ten
  decisions. They answered "A and B, not #10" (yes to decisions 1–9, no to 10) and approved
  where each fits ("go"). Plan v1.6 applies them: below, and in the specification's section
  22.
- 1 November 2026: the root folder moves to `/Users/darianraad/Code/careerwright`, and the
  worktrees to `/Users/darianraad/Code/careerwright-wt/<id>`, at a clean point with no agent
  running (the product owner's request; the ledger's ruling).

**Where the school-leaver decisions go** (plan v1.6):

| Decision | Goes to |
|---|---|
| 1. School students aged 17 and 18 are in scope | The specification's section 22; Task 16 checks the rules for young people's data before any real student uses Careerwright (H-15) |
| 2. "I haven't had a job yet" beside "Skip for now" at the first question | New Task 6f |
| 3. Two optional answers: what you're doing now, and qualifications (achieved or expected) | Task 6f; Tasks 10 and 12b read them as entry facts, an expected grade never met |
| 4. An opening question that works without a job | Task 6f, with the walk's word pass; the final words are the product owner's at session W2 |
| 5. A synthetic school leaver and 4–6 evaluation cases | Task 6e; she is one of session W2's people |
| 6. A tuition fee loan paid straight to the university is a loan to repay, not the student's own money | New Task 12c (the checker, the independent oracle written fresh, the search's rules); Tasks 12b and 14 show it |
| 7. A degree longer than the 24-month model | Task 14: words only, no planning change |
| 8. A reviewed school-leaver option pack | New Task 7f, with one short review session (R10); Task 12b reads it |
| 9. Childline in the calm support panel | Task 6f |
| 10. Hours that change on a date ("free from September") | No: a known L0 limit (plan section 1; specification section 22) |

The walk's other lines, approved with the placement: Task 10 shows no empty "usual in your
role" panel without a role; Task 12b's checkpoint works for someone not working and shows
each scheme's age rule; Task M answers a person with no job (the strength's horizon, the
first answer's ignition); Task 7e's research names apprenticeships, degrees and their
funding; Task 8 marks apprenticeship listings and takes a pasted apprenticeship advert.

**Running now** (R15):
- Task 6d slice C, finishing (main tree).
- This plan update, plan v1.6 (documents only, in the worktree `wt-plan`).

**Next, in order** (the suggested order above): in the main tree, 6d slice C's review → 6f →
6e → session W2 → 10 → 12b → 14 → 15 → the end-to-end session → 7e → 8 → M → 16 → 17 → the
final review; in the worktree, 12c (it may start beside 6f) → 7f (its first half, the
school-leaver pack session, then its second half), each after the last is integrated. Tasks
6f and 12c start after the folder rename (the ledger's ruling).

**Where the remaining Task W2 work went** (plan v1.5; all of Task W2E's rows are done):

| Item | Goes to |
|---|---|
| W2C part 1's scoped re-review | Done; its open findings went to Task W2E |
| On a phone, the world band puts a long view's first decision a scroll away | Task W2E: on a phone the decision comes first |
| "Help me explore instead" drops keyboard focus | Task W2E |
| The moving-and-still identical-words test covers only the fixture workspace | Task W2E |
| The first answer's ignition | Task M |
| The type-ahead's closest titles, asked as "Careerwright couldn't match that title in ESCO. Is it one of these?" | Task 6d, with "None of these is my job" leading to the person's own words |
| The unexpected connection lit in the world | Dropped (the product owner, 1 November 2026: "Always a plain line"); shared skills in words on each suggestion → Task W2E, done |
| The overlooked strength's proposal and confirm step; `held_back` on a support turn; its destinations on the horizon | Task M, all together |
| "Usual in your role, not confirmed yet" | Task 10 |
| Suggestions drawn as rings; "Make this a target" previewing its destination | Task M |
| The world's requirement family in the register; the Sprint W acceptance | Task W2E; the frame part → Tasks M and 16 |
| The frame re-measure (warn the product owner first: it opens a window) | Task M, then Task 16 |
| Plain phrases for the route preview's "Economic cost" and "Direct spending" | No longer needed: the demo route preview leaves the person's path (Task W2E); Task 14 writes plain words for real routes |
| ADR 0014 decision 7's strip wording | Task W2E |
| The phone openings list one per line, with stale and unknown captures | Task 8 |
| Session W2's package and sheet; `docs/reviews/sprint-w.md` | The short session's package → Task 6e (R10); `sprint-w.md` → Task W2E |
| Session W2's old sheet: the slate's provisional rules, the work-style and too-general rules, main names and hyphens, the specificity order and each note's words | Replaced by the five questions (R10): the slate's word rules are frozen (R11) and judged on real examples |
| The discovery prompts, untested live | Task 3b's first live run through the app, then session W2 |
| Typography and colour (Source Sans 3; leaf green beside destination orange) | Two of session W2's five questions |
| Layout: the tablet strip; Send as the bright action | Task W2E; the helper lines, the sketch's disclosure and the tabs are judged by session W2's first question |

**Parked for the final review** (unchanged): the earlier parked items (ledger lines starting
"Parked"). Two of them are now Task 6d's design input: titles that ESCO writes with "&" or
accents don't match their plain spelling (`concept_key`, a migration-defined key), and the
three chosen-occupation normalisations, which one stored target record replaces.

## Task A1: whole-solution audit, coherence and pragmatism (the product owner's request, 2026-10-31)

**Status: approved by the product owner on 2026-10-31** ("Approved - proceed"). The report
is `docs/reviews/l0-audit-2026-10-31.md`, with its appendices and the decisions page. Its
approved changes are applied in plan v1.5, this file, ADRs 0003 and 0006–0014, the new ADR
0015, the register, the specification's revision record (section 22) and `CLAUDE.md`.

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
