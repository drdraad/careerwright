# Repository contract

Careerwright L0: a local career-planning app (FastAPI, Pydantic AI, DBOS and PostgreSQL 16
backend; Next.js web app in `apps/web`). Authority order: `Careerwright_Product_Specification.md`
(v1.3), then `docs/plan/development-plan.md` (v1.4), then `docs/plan/l0-sprint-tasks.md`. For the
experience and the interface, the plan's section 4 (ADR 0014) overrides the specification's art
direction. Decisions live in `docs/adr/`; the latest sprint review is in `docs/reviews/`.

## Talking to the user
Anything the user reads must be easy: chat replies, review packages, questions, decision
sheets and reports. Keep their effort as low as you can.
- Write like a helpful colleague talking: plain everyday words, short sentences, one idea
  per line.
- Start with what they need to do or know. Cut everything they don't need.
- No internal codes (task numbers, ruling, gate, requirement or ADR IDs) unless they need one
  to act. Put references in a footnote.
- Explain a technical word in a few plain words the first time, or pick a simpler word.
- Ask a question in one sentence, and say what "yes" does.
- Show money in pounds (£2,995), never minor units or JSON.
- Before sending, reread it as someone who has never seen the code. If a sentence needs
  our context to make sense, rewrite it.

## The experience: a world, not a tool
The product owner's ambition governs every interface change. In their words, Careerwright
must be "revolutionary, not the current bland corporate borefest". It should "verge on
computer game rather than typical tool, conveying a sense of travelling through a brave new
world, and progression towards your destiny", "feel organic and cybernetic", "thrum with
power and possibility" and "leave users astonished and breathless and excite them with
revealed insight". The feeling to leave: "My future is larger than I realised—and I can start
moving towards it." The contract is the plan's section 4 (ADR 0014).
- One living world, not pages. The person is the light at its origin, destinations are warm
  lights ahead, and trails of light grow between them. Each chapter is a place in that world
  with its own moment.
- Within ten seconds the person has changed something and the world has answered.
- Progress visibly transforms the world. Evidence unlocks understanding. Decisions show
  their consequences before they are confirmed.
- Revelations (an overlooked strength, an unexpected connection, a credible route) are
  earned: built from deterministic results and verified spans, each with its reason one step
  away. The model never decides one; it may only propose a strength as a quotation of the
  person's words, which code verifies and the person confirms (ADR 0014).
- The world never shows more than the evidence. Everything that varies has a computed
  meaning; unknown is shadow, never zero; a condition is a gate in plain words; nothing
  implies a job offer. Distress stills the world and shows the calm support panel.
- Plain words carry the wonder. Reduced motion and calm mode draw a still world with the
  same states and words.
- A bland, form-like or corporate screen fails review even if it works. Ask of every
  interface change: does this feel like a world answering the person?

## Commands
Run from the repository root (details: `docs/runbook.md`).
- Setup: `make setup` (prerequisites, `uv sync --locked` on uv-managed Python 3.12, the
  web app and design tooling with Playwright's Chromium, local secrets and master key in
  `CAREERWRIGHT_HOME`, default `~/.careerwright/l0`, the pinned ESCO release and reference datasets (ONS
  ASHE and the SOC 2020 coding index, the ILO and Anthropic AI evidence, the ESCO to O*NET
  crosswalk) fetched into the gitignored `var/datasets/` and hash-checked, and the Docker
  images). The host Python is 3.14;
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
- Live calls run only through explicit, budget-capped commands, never from the checks
  above: `make live-smoke` (test model; `PRODUCTION=1` qualifies the production model;
  `INTERVIEW=1` runs one interview turn instead of a connection check), `make live-eval`
  (the representative evaluation cases, at most 6, test model only), `make live-smoke
  SEARCH=1` (one source search, scope `live-search`), `make live-extract` (one page
  extraction of the synthetic fixture page, scope `live-extract`) and `make live-adzuna`
  (two free-tier Adzuna requests, ledgered at $0). Every call is appended to
  `docs/evidence/live-usage.jsonl` and `.md` with its cost (R5).
- Corpus runs (`tools.corpus`) pace within one process only: leave a host's rate limit
  between runs.
- Generated review files (from `backend/`): `uv run --locked python -m tools.session_2_files`
  rewrites session 2's T and R question sets.

## Repository facts
- The product was called Nessa until 2026-10-30 (the product owner's rename). The old name
  stays only where changing it would rewrite a record or a pinned file: the supplied pack
  (`fixtures/m0`, `Nessa_M0_Fixtures.zip`, `Nessa_Local_Development_Plan.docx`), the pinned
  format names `nessa-england-option-pack` and `nessa-capability-reference`, corpus case
  X01's fetched address, and past reviews and evidence (`docs/reviews`, `docs/evidence`).
  Setups made before the rename (`~/.nessa/l0`, the `nessa-l0` Docker volumes) are not used.
- Requirement IDs and test IDs: `docs/requirements-register.md`. Tag each test with its
  register ID, and update the rows your work closes.
- Representative implementation: `backend/src/careerwright/identity/activity.py` with
  `workflow.py` beside it: the pinned durable-activity pattern (ADR 0002, ADR 0004), one
  `RunTask` per run kind (composed in `careerwright/worker.py`; a new model-backed kind is a task,
  never a second call path, ADR 0006). Workflows carry IDs only; one bounded activity
  re-checks access, model, key and budget, opens the sealed input and key just in time and
  stores the output sealed with its usage; failures
  are classified from type and status with the message discarded; each transient failure
  class has one retry owner: the DBOS step for provider failures, the activity's store
  budget for store failures. `careerwright/profile/commands.py` shows an expected-version command.
- Layout: `careerwright/identity` (identity and execution: access, workspaces, keys, runs,
  spend), `careerwright/profile` (profile, interview contract, turns and preferences, the support
  policy, discovery, the slate and the early sketch, provisional concepts),
  `careerwright/catalogue` (the ESCO taxonomy, the English city list, the pinned reference data,
  the UK SOC mapping, modelled pay and the salary floor, and the AI Resilience record model
  with its packs in `catalogue/packs/`, ADR 0010; and the England option pack,
  `option_pack.py` and `packs/england_option_pack/`, ADR 0011, whose version files, schema
  and session 2 package only `tools.option_pack_files` writes), `careerwright/capability`
  (capability assessment: the pinned capability reference with rubrics, ESCO crosswalks and
  gate types; matrices, evidence, protected gates, OUT-1 outcomes, readiness, gaps and the
  question graph; `capability.store` is its only SQL), `careerwright/planning` (the monthly
  planning model, pure: the planning catalogue and its pack adapter, the immutable monthly
  input, the direct-spend, income-difference, liquidity and debt ledgers, and the route
  checker), `careerwright/evidence`
  (acquisition: the guarded fetcher, the source manifest `sources.json`, pages, Adzuna,
  jobs, freshness, claims, model extraction), `careerwright/acquisition.py` (the restricted
  acquisition worker: no database, master key or model key), `careerwright/api` (HTTP only),
  `careerwright/migrations` (forward-only SQL), `careerwright/worker.py` (worker entry point). Identity
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
    A slate's written "Why this could suit you" is one bounded `slate_explanation` call per
    discovery, over its first view; every quotation is verified as a span of the pinned
    answers or that occupation's ESCO record (only the quoted words are checked, and the UI
    says so); only a run refused before any request may be tried again, by the person's
    click; the note changes no suggestion (ADR 0007 decision 12).
  - Any listed risk word, in any form, shows a calm support panel with UK resources beside
    the conversation. The message is still sent; that turn's reply only acknowledges and
    offers a smaller next step, and nothing about the panel is stored or used for
    suitability (one recall-first screen, ADR 0007). Model output may not infer a health
    condition, type, protected characteristic or percentage the person never used
    (`careerwright/profile/safety.py`).
  - Money is integer minor units (GBP). Use `Money` (≥ 0) for payments and `SignedMoney`
    for economic cost. Unknown money is `null`, never 0.
  - Unknown is never zero or ineligible. Failure is never an empty success. A truncated
    search is never "no route": `NO_ROUTE_IN_BOUNDED_MODEL` needs complete coverage.
  - Evidence (ADR 0009): every fetch goes through `careerwright.evidence.fetcher` (address,
    robots.txt, pacing and every redirect checked); a page's class comes from the manifest,
    never from the page; a body is kept only where the session 1 class permits. Third
    parties' emails, phone numbers and contact fields are removed before anything is
    hashed, sealed or sent to a model, and a body that still shows one is not kept. Apply
    links are https only. A blocked, failed or unread source is never "none found"; only an
    API's own empty answer is. Model extraction is the `page_extraction` run kind, started
    for at most five pages without structured data: the model only quotes, deterministic
    code approves values read from verified spans, and its input is erased when the run
    ends. Lock order (ADR 0009 decision 15): a run's cancellation lock first (the cancel; a
    model-readable recording, before `lock_workspace_records`). Only the worker locks a
    run's row `FOR UPDATE`, and only as its transaction's first lock; a cancel records its
    requests (key shares on the runs' rows) before it locks the workspace's row.
  - Pay and AI evidence (ADR 0010): ASHE is regional, never a city's; modelled pay exists
    only through an accountable reviewer's UK SOC mapping (none in L0). The salary floor
    leaves out only pay whose stated top, in its own period, is below it, never unknown,
    predicted, open-ended or other-period pay, and says what it left out. The AI Resilience
    Score is a reviewed range or unscored, never computed; exposure evidence alone never
    publishes one, and a model's proposal never publishes.
  - Option pack (ADR 0011): a committed version never changes; a correction or a review is
    a new version with its own pin in `PINS`, loaded only through `load_pack`. Every field
    cites a claim (value, span, excerpt) in its field's declared shape, or says why it is
    unknown; where a page states two disagreeing values, the field stays unknown with both
    kept. Session 2's question numbers are stable (Task 7c applies answers by number), and a
    record becomes `reviewed` only when every one of its rows is answered yes. The accuracy
    read reads development-split pages only.
  - Capability (ADR 0012): a protected gate (legal practice, recognition, admission,
    eligibility) is always required and never demoted (`PROTECTED_GATE`); held but
    unverified is unresolved, and nothing finds a person ineligible. A level counts only
    against the rubric it was chosen for; unknown is never level 0; ordinal levels take the
    maximum, never a sum. A target with nothing modelled, or with eligibility alone, is
    `insufficient_coverage`, never ready. A planned outcome counts only in a conditional
    scenario and never changes current evidence. Every L0 readiness result is qualified,
    and every derived result carries its `matrix_version` and `definition_version`.
  - The monthly model (TIME-1) reserves every touched month. A prerequisite is usable
    only from the next month boundary. Cash is prefunded: a receipt counts only if proven
    available before the outflow. Fixture wages arrive late in the month.
  - Planning (ADR 0013): the checker lists every violation, each limit named apart
    (direct-spend cap, monthly payment cap, reserve, deficit cap; an economic-cost cap is
    only a preference), and a violation is "not feasible in this monthly model", never
    "cannot afford". Unknown dates, cost, timetable or a hard limit leave a route
    unresolved, never passed. Every readiness qualification qualifies the route. Only an
    approved award counts unconditionally; a loan is never support. Readiness milestones
    come from `careerwright.capability.readiness.assess`, never from planning code, and Task 13a's
    oracle shares no code with `careerwright.planning.checker`.
  - Pareto layers are computed over the full archive, dominated schedules included.
    Equal points do not dominate each other.
  - TRACE-01 (economic cost) and DIRECTAI (direct spending) never share route IDs or
    labels. `fixtures/m0` is the byte-identical supplied pack (hashes in
    `fixtures/README.md`): never edit it. Fixtures never fill live fields; synthetic data
    is always labelled. ESCO comes only from the pinned, hash-checked release;
    `fixtures/esco-sample` is a labelled test subset, rebuilt only by `tools.esco_sample`.
  - Secrets: `.env` holds `META_API_KEY` for the live commands only, and
    `ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY` for `make live-adzuna` and for `make
    setup`, which copies them into `CAREERWRIGHT_HOME/adzuna/` for the restricted acquisition
    worker alone; the product takes user keys through the API and seals them. Never print a key, pass it as an argument,
    log it or journal it. Database passwords and master keys live in `CAREERWRIGHT_HOME`, never in
    the repository. The test model `muse-spark-1.3-contributor` takes synthetic data only,
    enforced in code and by a database CHECK; production is `muse-spark-1.3` (ADR 0003).
    Demo workspaces run only the offline fixture interviewer, never a provider model.
  - Ownership is row-level security: run API SQL inside `actor_transaction` and worker
    SQL inside `run_transaction` (`careerwright/db.py`). Never connect at runtime as an owner role.
  - Every consequential write takes an expected version and an `Idempotency-Key` and goes
    through `run_idempotent`. Errors are `CareerwrightError` codes; never echo request input.
    A command's answer is kept as its receipt in plaintext: never put model output in it.
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
  `apps/web/package.json` and its lockfile (at least 14 days old, enforced by pnpm, with no
  exception; record each in `docs/dependencies.md`), pnpm 10.33.2, Node 24, Python
  3.12, PostgreSQL 16, and the DBOS `application_version` `careerwright-l0-1` (change it when the
  workflow's step sequence changes). Code goes in `backend/src/careerwright/<domain module>` (plan
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
