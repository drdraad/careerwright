# Requirements register: requirement → test

Canonical map from every specification requirement to the test that will prove it, its
owning sprint and task, and its current status. Authority: product specification v1.2
(`Nessa_Product_Specification.md`), then the local development plan v1.0
(`docs/plan/development-plan.md`), then `docs/plan/l0-sprint-tasks.md`. This register adds
test IDs and ownership only; it never relaxes a requirement. Requirement text is a short
paraphrase. Where a row and the specification differ, the specification wins and the row
is a defect to fix.

Created 2026-10-27 (Task 2, Sprint 0). Every task updates the rows it closes (implementer
contract, step 4).

## 1 How to use this register

**Test IDs** are `<AREA>-<NN>` and never reused or renumbered:

- `AREA` is a spec requirement ID without its hyphen (`RDY1-03` tests RDY-1), a plan
  section 8 regression family (`TRACE01-02`, `PAYCAP-01`), or a **register anchor** for an
  untagged M0 section (`STATE`, `PROF`, `ACQ`, `JOB`, `ASSESS`, `OPTN`, `FRESH`, `PLAN`,
  `EXP`, `MODEL`, `DUR`, `API`, `SEC`, `UI`). Anchors are this register's labels, not
  specification IDs.
- Tag each test with its ID so the register can be checked mechanically. Proposed: a pytest
  marker `@pytest.mark.req("RDY1-03")` (Task 3 registers it, since pytest runs with
  `--strict-markers`), and a `[RDY1-03]` prefix in Vitest and Playwright test titles.
- One test may carry several IDs; one ID may need several tests. A row is closed only when
  every assertion it names is tested.

**Status** (the only allowed values):

| Status | Meaning |
|---|---|
| `planned` | No test yet. |
| `implemented` | A test exists but has not passed on the final candidate of its task. |
| `verified` | Passed on a named commit; the Evidence column says where. |
| `spike-verified` | Established by Sprint 0 spike code under `backend/spikes/`. The product module must re-establish it with its own test before the row becomes `verified`. |
| `blocked` | Cannot be tested now; the Evidence column gives the reason and owner. |
| `not run — requires human` | A human-only gate (ruling R2). Agents never mark these passed. |

**Layer:** D domain (pytest, Hypothesis) · A algorithm (independent oracle) · P persistence
(real PostgreSQL 16, DBOS) · AD adapter (recorded inputs, failure servers) · API (FastAPI
contract) · UI (Vitest, Testing Library, Playwright) · A11Y (axe, keyboard) · V visual
(screenshots) · M model quality (reviewed cases; live runs explicit and capped) · S security
and recovery · DOC document or ADR evidence · H human.

**Owners:**

| Task | Sprint | Slice |
|---|---|---|
| T1 | 0 | Spike: scope, dependencies, Meta qualification, DBOS durability |
| T2 | 0 | Fixtures, corpus manifest, this register, design references, Sprint 0 review |
| T3 | 1 | Platform: commands, Compose, persistence, identity, secrets, spend |
| T4 | 1 | Designed shell, generated client, fixture journey |
| T5 | 2 | ESCO import, InterviewTurn contract, model port |
| T6 | 2 | You chapter, grounded diverse discovery, early sketch |
| T7 | 3 | Acquisition backend, ASHE, AI-evidence packs, freshness |
| T8 | 3 | Roles chapter (map, list, pay lens), job corpus |
| T9 | 4 | Matrices, evidence, protected gates, OUT-1, apply-now (backend) |
| T10 | 4 | Skills chapter, evidence questions, course corpus |
| T11 | 5 | Offerings, funding, monthly compiler, ledgers |
| T12 | 5 | Options checkpoint UI, funding corpus |
| T13 | 6 | DFS, archive, layers, oracle |
| T14 | 7 | Route comparison |
| T15 | 8 | Plan, progress, revision, exports |
| T16 | 9 | Release qualification |

## 2 Specification requirement IDs (M0)

### BND-1 Build boundary and precedence (spec §1; plan §§1–2)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| BND1-01 | L0 local overrides of M0 recorded; nothing else relaxed | DOC | T1 | verified | `docs/adr/0001-l0-scope.md` (2bb36e5) |
| BND1-02 | Supported slice (England, en-GB, GBP) stated before detailed collection; other regions get an explicit unsupported-region state, never a silent fallback | UI, API | T6 | planned | |
| BND1-03 | At most three cities and three active targets; a fourth is rejected with a typed error, never added silently | D, API | T3 | planned | |
| BND1-04 | Residence and eligibility are never inferred from a chosen English city | D | T5 | planned | |
| BND1-05 | Remote work only where England-compatible; remote never consumes a city slot | D | T7 | planned | |
| BND1-06 | Planning bounds enforced and disclosed in every result: ≤ 24 action concepts, ≤ 2 starts each, ≤ 6 selected actions, ≤ 24 months, ≤ 1 conditional bridge-role transition | D | T11, T13 | planned | |
| BND1-07 | At a hard bound, never keep the first 24 actions or first two intakes silently; ask the user to pin, exclude or choose; persist the removed-candidate count and scope restriction | D, UI | T12 | planned | |
| BND1-08 | A regulated pathway beyond 24 months gets an explanatory sketch and an unsupported-model state (`MODEL_SCOPE_EXCEEDED`), never "impossible" (P04) | D, API | T9 | planned | |
| BND1-09 | Non-deferrable M0 invariants hold everywhere. Covered by STATE-02/03, LIMITS-04/05, AIR1-02, FUNDING-01, PROF-04/06, SEC-01, MODEL-06, PLAN-04, READINESS-01, FIN1-06 | (rows named) | all | planned | |
| BND1-10 | Data mode (demo, live-assisted, live-vacancy) recorded on every workspace and run (L0, GC5) | P | T3 | planned | |
| BND1-11 | Demo mode makes no outbound request after setup, including the DBOS worker and the auth emulator (L0) | S | T3, T4 | planned | |
| BND1-12 | Fixtures never fill missing live fields or appear as real evidence; synthetic data persistently labelled; switching to demo creates a separate workspace (L0, GC5) | D, UI | T3, T4 | planned | |
| BND1-13 | Published ports bind 127.0.0.1; non-local Host and Origin rejected (L0, GC9) | S | T3 | planned | |
| BND1-14 | Command contract: `make setup/dev/demo/check/acceptance/live-smoke/stop/reset-demo` behave as plan §2 states; `make stop` is bounded and never hangs | S, P | T3 | planned | |
| BND1-15 | A fresh checkout installs, starts and passes acceptance using the documented commands only | S | T16 | planned | |

### REC-1 Personality-informed career suggestions (spec §4)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| REC1-01 | Personality and work style are optional; no forced personality test (P02) | UI, D | T6 | planned | |
| REC1-02 | No categorical type assignment; no inference of aptitude, intelligence, mental illness or sensitive traits from wording, names, accent or photos | M | T6 | planned | |
| REC1-03 | A preference informs hypotheses but never excludes a career category | M, D | T6 | planned | |
| REC1-04 | "I enjoy this", "I believe I can" and "I have evidence" are separate fields | D | T5 | planned | |
| REC1-05 | `CareerSuggestion` carries title, concept ID, mappings, source IDs, linked profile evidence, tasks, fit, mismatch, entry gates, evidence gaps, a low-cost test, discovery channel and family; it has no match-percentage field | D, API | T6 | planned | |
| REC1-06 | Every named suggestion passes grounding (occupation ID plus supporting source) | M, D | T6 | planned | |
| REC1-07 | A suggestion becomes a `TargetRole` only by explicit user selection | API | T6 | planned | |
| REC1-08 | Broaden, more practical, less familiar, exclude this kind of work, change my profile and "show why this wasn't included" work; rejecting a title does not reject its industry | UI | T6 | planned | |
| REC1-09 | Demographic counterfactuals: varying irrelevant demographic cues does not change suggestions beyond the reviewed tolerance; work rights and accommodations held fixed | M | T6 | planned | |
| REC1-10 | A sure user can skip suggestions and enter their own titles | UI | T6 | planned | |

### DIV-1 Diverse discovery beyond common careers (spec §4)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| DIV1-01 | Retrieval covers the full pinned English ESCO catalogue through PostgreSQL full-text search and alias lookup; no embeddings | P | T5 | planned | |
| DIV1-02 | Several task, interest and skill queries; combined pool reranked; working pool 60–120 concepts where evidence permits (soft) | D, M | T6 | planned | |
| DIV1-03 | Verified user titles outside ESCO become provisional internal concepts, never fabricated ESCO records | D | T5 | planned | |
| DIV1-04 | LLM-generated titles stay hypotheses until corroborated; duplicated adverts are not independent support | D | T6 | planned | |
| DIV1-05 | Aliases and near-identical roles deduplicated before diversity is counted | D | T6 | planned | |
| DIV1-06 | Slate respects a relevance floor and confirmed constraints; soft limit of two per family in six; fewer suggestions with a stated reason when evidence is thin; no implausible filler | D | T6 | planned | |
| DIV1-07 | Salary, popularity and sparse AI evidence never silently remove long-tail careers; hard filters show counts | D, UI | T6 | planned | |
| DIV1-08 | Evaluation reports grounded relevance, alias duplication, family/task coverage, exposure concentration and long-tail coverage against relevance-only and common-careers baselines on the same pool | M | T6 | planned | |
| DIV1-09 | No live vacancies is shown as a demand signal, not proof the occupation does not exist | UI | T6 | planned | |

### TAX-1 Taxonomy and evidence packs (spec §5)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| TAX1-01 | ISCO-08 is the grouping pivot; internal concept IDs and ESCO URIs keep specialist occupations distinct | P, D | T5 | planned | |
| TAX1-02 | UK SOC 2020, US SOC versions and O*NET-SOC are distinct namespaces; unresolved mapping alternatives retained | D | T7 | planned | |
| TAX1-03 | No precise ASHE salary for every ESCO descendant of one ISCO group; no averaging of medians across many-to-many mappings | D | T7 | planned | |
| TAX1-04 | Import manifest records release, URL, licence and attribution, hash, native code version, import date and transformation version; `make setup` fetches and verifies (R7) | P, S | T5 (ESCO), T7 (ASHE) | planned | |
| TAX1-05 | Trend shown as unavailable unless comparable history exists; one snapshot is never a trend | D, UI | T7, T8 | planned | |
| TAX1-06 | A regional or broad-SOC estimate is never relabelled as city-level | D, UI | T7, T8 | planned | |
| TAX1-07 | AI-evidence records pin their O*NET-SOC version and a validated bridge; insufficient matches stay unscored | D | T7 | planned | |

### AIR-1 AI Resilience Score (spec §5)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| AIR1-01 | Labelled "AI Resilience Score", 0–10, higher is more resilient, five-year outlook; range first; experimental badge; synthetic scores conspicuously labelled | UI | T8 | planned | |
| AIR1-02 | Only reviewed range records with a reliable mapping, stated scope, ≥ 2 independent evidence families and recorded contradictions publish; otherwise null | D | T7 | planned | |
| AIR1-03 | No automatic formula (for example 10 − exposure, products of indices, absence of AI usage read as protection) exists in code | D | T7 | planned | |
| AIR1-04 | The LLM proposes a cited assessment record; it never publishes one | D | T7 | planned | |
| AIR1-05 | Default filter "Any"; lower-bound filtering; unscored included by default in exploration; basis and excluded/unscored counts shown; unknown never becomes 0 or 10 | D, UI | T7, T8 | planned | |
| AIR1-06 | A discovery filter never constrains optimisation; "Use this limit in my plan" creates an explicit, scoped constraint that excludes unscored, invalidated and out-of-horizon records; an accepted exception stays conditional | D | T11, T13 | planned | |
| AIR1-07 | Reviewed pack pinned and dated per run; a known material correction invalidates affected records; a misleading record can be withdrawn | P | T7 | planned | |
| AIR1-08 | Company clusters show their role distribution, never an average company score | UI | T8 | planned | |
| AIR1-09 | Chosen plan and printout include the assessment snapshot and any unresolved review flag | D, UI | T15 | planned | |

### MAP-1 Provisional skills matrix (spec §8)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| MAP1-01 | Matrix from ESCO essential/optional relations plus ≤ 3 user full-text exemplars; snippets a weak signal; shows "Provisional - no specialist review", source versions, full-text and snippet counts, date | D, UI | T9, T10 | planned | |
| MAP1-02 | A term missing from a snippet is not evidence of absence; snippet prevalence is labelled as such | D | T9 | planned | |
| MAP1-03 | Essential, preferred, disputed and unknown rows are distinct; levels are task-specific | D | T9 | planned | |
| MAP1-04 | Editing an essential row creates a new target definition, keeps source claim, actor, reason and old/new versions, and invalidates earlier ranks | P, D | T9 | planned | |
| MAP1-05 | Protected gates (right to practise, credential recognition, confirmed admission/eligibility) are typed and cannot be toggled away; unverified stays unresolved (P04) | D | T9 | planned | |
| MAP1-06 | Employer-specific non-statutory requirements relax only with an explicit warning | D, UI | T9, T10 | planned | |
| MAP1-07 | Each row carries skill/credential ID, observable task, proficiency, type, importance, prevalence with denominator, prerequisites, proof, spans, uncertainty, jurisdiction and rubric | D | T9 | planned | |
| MAP1-08 | Levels 0–4 are behaviourally anchored; unknown ≠ 0; ordinal levels never summed; time in a job never adds a level automatically | D | T9 | planned | |

### OUT-1 Course-to-requirement outcome contract (spec §10)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| OUT1-01 | `PlanAction.outcomes` carries skill ID, nullable level, evidence kind, categorical confidence (unsupported, provisional, corroborated), source span (ID, hash, offsets, date, excerpt), rubric version, claim state, review state and provenance | D | T9 | planned | |
| OUT1-02 | Topic mention, practice and assessed demonstration are distinct; "introduction to SQL" never yields level 2; an unsupported level stays null | D, M | T9 | planned | |
| OUT1-03 | A user override is recorded as an assumption, never as a provider claim or expert validation | D | T9 | planned | |
| OUT1-04 | An accepted provisional mapping supports only a conditional route; missing critical levels give a partial sketch or exclude the action from the numeric solve | D | T9, T11 | planned | |
| OUT1-05 | Skill evidence changes only after an assessed completion event and evidence review, never on enrolment or completion alone | D, P | T9 | planned | |
| OUT1-06 | Credentials and supervised experience are separate outcome types with issuer, jurisdiction and verification; course levels never satisfy a statutory gate | D | T9 | planned | |
| OUT1-07 | Overlapping courses never award the same competency twice; two introductory courses never sum to competence | D | T9 | planned | |
| OUT1-08 | Work-based actions need task/evidence mappings; wages alone give no experience credit | D | T11 | planned | |
| OUT1-09 | Review shows "this option is expected to address these rows", assessment evidence, uncertain outcomes and omitted gaps | UI | T12 | planned | |
| OUT1-10 | ≥ 10 real course pages labelled; false-positive readiness mappings reviewed individually; an unsupported consequential outcome blocks the affected route | M, H | T10 | planned | corpus slots C01–C10 |

### RDY-1 Readiness and apply-now (spec §10)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| RDY1-01 | Ready iff every essential row's evidenced level ≥ required and every gate is satisfied, for a fixed target/matrix version; unknown does not pass | D | T9 | planned | |
| RDY1-02 | A planned outcome counts only in a conditional scenario after its completion gate; the current profile is unchanged | D | T9, T11 | planned | |
| RDY1-03 | When ready, lead with "You meet the modelled requirements - review current postings and apply."; no forced training; no degenerate frontier; recency, provisional-matrix and employer checks shown (P05) | UI, D | T9, T10 | planned | |
| RDY1-04 | Demoting a statutory gate is refused; an unresolved gate and an out-of-model pathway are distinct from ineligibility (P04) | D | T9 | planned | |
| RDY1-05 | Readiness results carry their target and matrix versions | D | T9 | planned | |

### TIME-1 Monthly decision contract (spec §12)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| TIME1-01 | A month is a named calendar month in the work area's timezone; actual dates kept on cards and exports beside model months | D, UI | T11, T14, T15 | planned | |
| TIME1-02 | Every touched month reserved; a prerequisite is usable only from the next month boundary after completion; no snapping earlier or rounding down | D | T11 | planned | see TIME family |
| TIME1-03 | An application completes in a month strictly before the deadline month unless admission is verified in the initial state; otherwise `COARSE_MODEL_UNRESOLVED` ("not resolved by this monthly model"), never "ineligible" | D | T11 | planned | |
| TIME1-04 | Workload envelope per active month: Σ maximum weekly loads ≤ minimum weekly availability, including work, study, commute and care; unknown timetable needs a confirmed assumption; a session clash fails separately | D | T11 | planned | see WORKLOAD |
| TIME1-05 | Conservative prefunding each month: opening + early receipts − outflows ≥ reserve; later receipts roll to next month; no borrowing against unaccepted offers or unconfirmed grants; a conservative rejection is flagged for review, not "cannot afford" | D | T11 | planned | see PREFUND |
| TIME1-06 | One common horizon; nominal integer GBP minor units; user-confirmed net incomes; no tax or benefit inference from gross pay | D | T11 | planned | see ECON |

### FIN-1 Objective definitions (spec §12)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| FIN1-01 | Default objectives: months to the modelled application-readiness milestone and economic cost against a confirmed baseline over a common horizon; time to a job is a separate conditional result | D | T11 | planned | |
| FIN1-02 | Direct cost covers tuition, assessment, materials, equipment, extra travel or childcare, relocation and financing charges, less confirmed non-repayable support; post-horizon contractual liabilities included with timing; loan principal is liquidity, not a discount | D | T11 | planned | |
| FIN1-03 | Economic cost = direct + Σ (baseline − route income); wages counted once | D | T11 | planned | TRACE01-01 |
| FIN1-04 | Offer earnings start only at the offer gate; delay and no-offer change both time and income; unaccepted offers and possible funding are labelled conditions | D | T11 | planned | |
| FIN1-05 | Negative economic cost supported (`SignedMoney`) and never shown as cash available today; no fee-churning or artificial job switches | D, UI | T11, T14 | planned | |
| FIN1-06 | Direct-spend and monthly-payment caps are hard; an economic-cost cap is optional and distinct; a deficit cap is separately named | D | T11 | planned | see PAYCAP |
| FIN1-07 | Missing baseline gives an unresolved economic comparison; "Compare direct spending only" is an explicit, labelled mode; never a silent switch (P02) | D, UI | T11, T14 | planned | |
| FIN1-08 | Direct expenditure, income change, peak payments, cash reserve and debt always shown separately | UI | T14, T15 | planned | |
| FIN1-09 | Scenarios carry no probabilities; scenario-wise dominance only if no worse in every scenario; base-case dominance labelled "better in the base scenario" | D | T11, T14 | planned | |
| FIN1-10 | Liquid-balance ledger with income, grants, loan draws, living, payments and repayments; B ≥ reserve; payments + repayments ≤ monthly cap; provider-paid support counted once; debt balance tracked separately | D | T11 | planned | |

### ROU-1 Route families and schedule identity (spec §12)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| ROU1-01 | Family identity from the canonical action/prerequisite DAG, provider choices, delivery mode, job-role sequence and financing/conditional gates; part-time vs full-time is a different family; a later intake is a schedule variant | D | T13 | planned | |
| ROU1-02 | A family keeps every efficient schedule; no fixed cost per structure | D | T13 | planned | see FAMILY |
| ROU1-03 | A family's displayed best rank is the lowest rank among its retained variants, labelled so; no invented grey families or relabelled ranks | D, UI | T13, T14 | planned | |
| ROU1-04 | Overview shows distinct families first; suppresses repeat cards, never evidence | UI | T14 | planned | |

### OPT-1 Solver architecture (spec §12)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| OPT1-01 | Deterministic exhaustive DFS in canonical action order: skip or one reviewed start per concept; each selected offering set visited once; no equivalent permutations | A | T13 | planned | |
| OPT1-02 | Prune only irreparable violations or certified bounds, each documented with its proof; never on first-front dominance, dominator count, current readiness or accumulated economic cost | A, DOC | T13 | planned | |
| OPT1-03 | Every distinct feasible schedule encountered, dominated ones included, is persisted to a versioned disk-backed archive with atomic checkpoints and an idempotent solve identity; recovery resumes a proven checkpoint or restarts under a new attempt ID | P | T13 | planned | |
| OPT1-04 | Caps: 30 s, 1,000,000 expanded states, 50,000 archived feasible schedules per target; archive persistence counts in the budget; exact stop reason recorded | A, P | T13 | planned | see LIMITS |
| OPT1-05 | `search_coverage` is `complete` only after exhausting the declared tree with sound pruning, else `budget_truncated`; operational states queued, running, succeeded, failed, cancelled, invalid-input stay distinct; a crash is failed | P | T13 | planned | |
| OPT1-06 | Runs record expanded states, feasible count, remaining-work indicator, limits, pruning-rule version, truncation reason, canonical order and model/data versions | P | T13 | planned | |
| OPT1-07 | `NO_ROUTE_IN_BOUNDED_MODEL` only with complete coverage; a truncated empty archive means none found before the limit | API | T13 | planned | |
| OPT1-08 | DFS agrees with an independent Cartesian-product oracle on tiny instances (feasible sets, objectives, layers); oracle and route checker share no code with the candidate | A | T13 | planned | |
| OPT1-09 | Candidate evaluation has no network, LLM or ORM access; the optimiser is a cancellable child process | S | T13 | planned | |
| OPT1-10 | A complete run on the same immutable input reproduces the same result; state-limited replay is reproducible; wall-time truncation is not promised bit-identical | A | T13 | planned | |
| OPT1-11 | Ranking is a separate observable stage finished before ranked completion is claimed; efficient two-objective ranking qualified against simple peeling; 50,000-point benchmark recorded | A | T13 | planned | |
| OPT1-12 | Profile or input changes cannot alter an in-flight solve snapshot | P | T13 | planned | |

### VIS-1 Dendrite graph (spec §7)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| VIS1-01 | Up to three work areas are stable anchors; companies cluster within them; branches end in jobs; remote is its own area labelled with jurisdiction and timezone | UI | T8 | planned | |
| VIS1-02 | Industry sets node/branch colour; role family and work mode use shape, icon and label; colour is never the only channel | UI, A11Y | T8 | planned | |
| VIS1-03 | Static SVG hierarchy with expand/select, source counts, favourites and the list's filters, including numeric salary and AI range | UI | T8 | planned | |
| VIS1-04 | At most 100 visible job nodes with explicit aggregation counts; the list keeps the full result set | UI | T8 | planned | |
| VIS1-05 | Result count, deduplication count and coverage status shown outside the canvas | UI | T8 | planned | |
| VIS1-06 | Pay and location lens: area rows, a declared common pay basis, predicted-pay styling, a separate unknown-pay lane, currencies and contract bases kept apart; focus highlights same-company jobs | UI | T8 | planned | |
| VIS1-07 | Graph, list and pay lens share one selection and filter contract | UI | T8 | planned | |
| VIS1-08 | Graph distance never implies commute feasibility or hiring probability | UI | T8 | planned | |
| VIS1-09 | Mobile defaults to the list, with an optional graph overview | UI | T8 | planned | |
| VIS1-10 | Missing values remain selectable as "not specified" in filters | UI | T8 | planned | |

### VIS-2 Coordinated comparison and journey (spec §13)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| VIS2-01 | One panel per target and level; shared axes only when currency, horizon, baseline and objective agree; no cross-target dominance; each target keeps its own filters and selection | UI, D | T14 | planned | |
| VIS2-02 | Time horizontal, selected cost vertical, discrete points; nondominated points highlighted; any boundary labelled "comparison boundary"; no smooth interpolated frontier | UI | T14 | planned | |
| VIS2-03 | Whiskers only for supported scenario estimates; missing scenario evidence shown as unknown, never zero width; no probabilities | UI | T14 | planned | |
| VIS2-04 | F2 and F3 readable grey; cards lead with a concrete margin naming currency and cost basis; one declared comparator rule; extra dominators exposed; layer and family in accessible text | UI, A11Y | T14 | planned | |
| VIS2-05 | Static selected-route Gantt: work/study bands, overlapping parallel bands, waits, gates, actual dates beside model months | UI | T14 | planned | |
| VIS2-06 | Time and cost sliders with exact numeric inputs and keyboard control; economic cost labelled with baseline and horizon; direct-spend budget is a separate control | UI, A11Y | T14 | planned | |
| VIS2-07 | View filters never change recorded ranks; explicit reranking uses the eligible retained archive; changed constraints create a new solve version; a hidden dominator never makes a route optimal; pinned out-of-range routes keep a badge | D, UI | T14 | planned | |
| VIS2-08 | Step cards show action, provider or role class, dates, workload, outlay and payment timing, income effect, funding status, requirements gained, evidence to produce, prerequisites, freshness and action link; job steps separate search/travel cost from net pay after an accepted offer; fixed licensed icons | UI | T14 | planned | |
| VIS2-09 | Paginated archive and bounded projection with shown/total counts; extremes and selection preserved; a sample is never labelled the full frontier | UI, API | T14 | planned | |
| VIS2-10 | Earlier results stay readable during recomputation; an inspected route is never replaced silently | UI | T14 | planned | |
| VIS2-11 | A "balanced route" is a declared preference rule, never a universal knee point | UI | T14 | planned | |

### ARC-1 Concrete stack (spec §17)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| ARC1-01 | Stack fixed; CP-SAT, Rust solvers, PyO3, PixiJS, Temporal, Redis, PostGIS, embeddings and vector databases absent (dependency allowlist check in `make check`) | S | T3 | planned | |
| ARC1-02 | Python dependencies pinned exactly and locked; arm64 executed | DOC | T1 | verified | `docs/dependencies.md`, `backend/uv.lock` (2bb36e5) |
| ARC1-03 | JavaScript dependencies pinned and locked with pnpm | DOC | T4 | planned | |
| ARC1-04 | Pydantic AI's native Meta provider qualified on the pinned model: schema output, streaming, search, usage | M | T1 | verified | ADR 0003; `docs/evidence/sprint-0-spike.md` S0.2; ledger calls 3–7. Test-model choice provisional (H-09) |
| ARC1-05 | Worker killed mid-call or after persistence recovers to exactly one accepted output; outbox replay starts one workflow | P | T1, T3 | spike-verified | ADR 0002; `backend/spikes/durable/test_durability.py` |
| ARC1-06 | Workflow journals and logs hold identifiers only: no credential and no private payload (leak scan with a negative control) | P, S | T1, T3 | spike-verified | ADR 0002, S0.4 |
| ARC1-07 | One retry owner (the DBOS step); typed message-free failures; exhausted retries end failed, never empty success | P | T1, T3 | spike-verified | ADR 0002 decisions 6–7 |
| ARC1-08 | Runtime connects with non-owner roles; migration owners used only by setup | P, S | T3 | planned | ADR 0002 decision 2 |
| ARC1-09 | Architecture checks reject circular imports and raw vendor/SQL access from domain code (GC3) | S | T3 | planned | |
| ARC1-10 | TypeScript client generated from OpenAPI; money, state and error enums never duplicated by hand (GC10) | API | T3, T4 | planned | |
| ARC1-11 | An LLM cannot alter a selected plan and a browser worker cannot write a skill profile; verified outputs return only through domain commands | S | T3 onward | planned | |

### TEST-1 Fixture pack and worked trace (spec §20)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| TEST1-01 | Fixture pack placed unchanged; its validator passes | DOC | T2 | verified | `fixtures/m0/`, `fixtures/README.md`; validator run in `docs/evidence/fixture-hand-check.md` §1 |
| TEST1-02 | TRACE-01 arithmetic and the five persona expectations independently hand-checked | DOC | T2 | verified | `docs/evidence/fixture-hand-check.md` (domain-reviewer sign-off is H-07) |
| TEST1-03 | A–I direct-spend fixture reconstructed, labelled and namespaced | DOC | T2 | verified | `fixtures/reconstructed/directai.json` |
| TEST1-04 | P01 end to end (browser, API, PostgreSQL, DBOS, solver): TRACE-01 ledger, three fronts, route B print snapshot | UI | T16 | planned | |
| TEST1-05 | P02 end to end: grounded diverse shortlist, no forced personality test, no economic solve on an invented baseline | UI | T16 | planned | |
| TEST1-06 | P03 end to end: payment-cap rejection; grant and offer income not spent before their gates | UI | T16 | planned | |
| TEST1-07 | P04 end to end: gate demotion refused; unresolved and out-of-model distinct from ineligible | UI | T16 | planned | |
| TEST1-08 | P05 end to end: apply-now first; no forced training or degenerate frontier | UI | T16 | planned | |
| TEST1-09 | Real-source corpus labelled: 20 job postings, 10 course pages, 3 funding pages | M, H | T8, T10, T12 | planned | `corpus/manifest.json` (0/33 collected) |
| TEST1-10 | LLM steps evaluated by schema, grounding and accepted semantic sets, never exact prose | M | T5, T6 | planned | |
| TEST1-11 | Real-provider smoke (L0: local, budget-capped, with durable restart and browser print) | M | T16 | planned | |
| TEST1-12 | Fixtures and core checks run in `make check` after each meaningful change | S | T3 | planned | |

## 3 Plan section 8 regression families

Expected values are independent: they come from the specification and the hand check
(`docs/evidence/fixture-hand-check.md`), never from the code under test. Namespace the two
route fixtures separately.

| ID | Assertion and expected value | Requirements | Fixture | Owner | Status |
|---|---|---|---|---|---|
| TRACE01-01 | Ledgers: A £1,200 direct, £4,000 loss, £5,200 economic; B £600, £0, £600; C £700, £1,500, £2,200; D £1,100, £0, £1,100; E £1,300, £0, £1,300 | FIN1-03 | TRACE-01 | T11 | planned |
| TRACE01-02 | Prefunding with late wages: B minimum £4,850 (Jan); A minimum £1,800 (Mar); C £4,700, D £4,725, E £4,740; all ≥ £500; payments ≤ £1,500; direct ≤ £1,500 | TIME1-05 | TRACE-01 | T11 | planned |
| TRACE01-03 | Economic mode: A, B, C in F1; D in F2; E in F3. E's dominators are B and D | OPT1-08 | TRACE-01 | T13 | planned |
| TRACE01-04 | Route B snapshot agrees on screen, print and JSON: 4 months, £600 direct and economic, £150 peak, six-month basis, conditional readiness after assessment, ID `fixture-plan-01` | EXP-01 | TRACE-01 | T15 | planned |
| TRACE01-05 | Routes view renders A/B/C F1, D F2, E F3 with economic labels (baseline £2,000/month, six-month horizon) | VIS2-02 | TRACE-01 | T14 | planned |
| TRACE01-06 | Planned outcomes never overwrite current evidence: query-data and validate-data stay level 1 until an assessed completion is reviewed | OUT1-05 | TRACE-01 | T9 | planned |
| TRACE01-07 | Workload: A at 40 h of 40 h passes; the same with 41 h fails | TIME1-04 | TRACE-01 | T11 | planned |
| TRACE01-08 | Actual dates preserved; B's readiness milestone is 2027-05-01 (next month boundary) | TIME1-02 | TRACE-01 | T11 | planned |
| DIRECTAI-01 | Direct-spending mode: A/B/C, D/E/F, G/H/I form F1, F2, F3 | OPT1-08 | DIRECTAI | T13 | planned |
| DIRECTAI-02 | Charts and dominance text use direct-spending labels ("Compare direct spending only", "Total direct transition cost"), never economic ones | FIN1-07, VIS2-04 | DIRECTAI | T14 | planned |
| DIRECTAI-03 | Loading both fixtures causes no route-ID collision | — | both | T13 | planned |
| PREFUND-01 | £100 opening, £200 day-one fee, £300 pay on day 28, reserve £0: fails; the +£200 month end does not rescue it | TIME1-05 | spec §12 | T11 | planned |
| PREFUND-02 | Same month with the £300 proven available before the fee: passes (100 + 300 − 200 ≥ 0) | TIME1-05 | spec §12 | T11 | planned |
| PREFUND-03 | An unconfirmed grant or unaccepted offer never funds an earlier payment (P03) | TIME1-05, FIN1-04 | P03 | T11 | planned |
| PAYCAP-01 | £2,400 option with £1,800 due immediately fails a £250 monthly cap despite a £3,000 direct budget | FIN1-06 | spec §12 | T11 | planned |
| PAYCAP-02 | P03's £300 option with £200 upfront is rejected; the violations include `monthly_payment_cap` and also the reserve (hand check H1); the test asserts membership, not a single reason | FIN1-06 | P03 | T11 | planned |
| PAYCAP-03 | Equality passes, one penny over fails: payment = cap; direct spend = cap (P03 £300) | FIN1-06 | P03 | T11 | planned |
| TIME-01 | Mid-month start and finish reserve every touched month | TIME1-02 | constructed | T11 | planned |
| TIME-02 | A prerequisite is usable only from the next month boundary after completion | TIME1-02 | constructed | T11 | planned |
| TIME-03 | A same-month application before the deadline is `COARSE_MODEL_UNRESOLVED`, not ineligible; verified completed admission in the initial state is exempt | TIME1-03 | constructed; TRACE-01 admission | T11 | planned |
| TIME-04 | Original dates preserved; no snapping earlier, no rounding duration down | TIME1-02 | constructed | T11 | planned |
| WORKLOAD-01 | Two 20 h courses in one week with 20 h available fail; a naive monthly sum (40 ≤ 80) would pass | TIME1-04 | spec §12 | T11 | planned |
| WORKLOAD-02 | A known session clash fails separately | TIME1-04 | constructed | T11 | planned |
| WORKLOAD-03 | Total hours without a timetable leave the envelope unknown until an assumption is confirmed; never a pass | TIME1-04 | constructed | T11 | planned |
| WORKLOAD-04 | Employment, commute and care count in the envelope consistently | TIME1-04 | constructed | T11 | planned |
| ECON-01 | One horizon and baseline for every route in a panel; bridge, apprentice or target wages counted once | FIN1-03 | constructed | T11 | planned |
| ECON-02 | FIN-1 example: 12-month horizon, £2,000 baseline; six months out of work + £3,000 = £15,000; part-time route keeping pay, £5,000 direct = £5,000 | FIN1-03 | spec §12 | T11 | planned |
| ECON-03 | Negative economic cost is representable and displayed, and never treated as cash available today | FIN1-05 | constructed | T11, T14 | planned |
| ECON-04 | Contractual liabilities beyond the horizon are retained with their timing | FIN1-02 | constructed | T11 | planned |
| ECON-05 | No invented target wage after readiness; the continuation scenario is explicit | FIN1-01 | constructed | T11 | planned |
| ECON-06 | Missing baseline (P02, even with `current_net_income_minor` 0): no economic solve; a question or an explicit direct-spending mode | FIN1-07 | P02 | T11 | planned |
| FUNDING-01 | Potential eligibility is not an award: P03's unconfirmed £800 grant contributes £0 to unconditional figures | spec §10 | P03 | T11 | planned |
| FUNDING-02 | Bridge wages before an accepted offer contribute £0 (P03) | FIN1-04 | P03 | T11 | planned |
| FUNDING-03 | A grant paid directly to a provider appears on both sides or neither, never twice | FIN1-10 | constructed | T11 | planned |
| FUNDING-04 | New borrowing is never optimised or recommended; loans are information; existing debt is a fixed commitment (P03) | spec §10 | P03 | T11, T12 | planned |
| FUNDING-05 | Confirmed, potentially eligible, ineligible and insufficient information stay distinct; a funded scenario sits beside the unfunded one with a blocking verification action | spec §10 | constructed | T11, T12 | planned |
| READINESS-01 | All essential evidence and protected gates required; unknown is not level 0 and does not pass | RDY1-01 | constructed | T9 | planned |
| READINESS-02 | Planned outcomes count only conditionally | RDY1-02 | TRACE-01 | T9 | planned |
| READINESS-03 | Apply-now with zero selected training (P05: both rows evidenced 2 ≥ 2, gates confirmed) | RDY1-03 | P05 | T9 | planned |
| READINESS-04 | P04: setting the registration gate non-essential is refused | RDY1-04, MAP1-05 | P04 | T9 | planned |
| PARETO-01 | (1,3), (2,2), (3,1) all dominate (4,4), which is F2 | OPT1-08 | spec §12 | T13 | planned |
| PARETO-02 | Equal objective pairs do not dominate each other | OPT1-08 | spec §12 | T13 | planned |
| PARETO-03 | No dominance across targets | VIS2-01 | constructed | T13, T14 | planned |
| FAMILY-01 | Schedules in one family can hold different ranks; the family shows its lowest rank, labelled | ROU1-03 | constructed | T13 | planned |
| FAMILY-02 | Grouping, pagination and display filters never change the archive or proof scope | ROU1-04, VIS2-07 | constructed | T13, T14 | planned |
| LIMITS-01 | State cap: stops with the exact reason, keeps every encountered record, coverage `budget_truncated` | OPT1-04 | constructed | T13 | planned |
| LIMITS-02 | Wall-time cap: same, without comparing prefixes bit for bit | OPT1-04, OPT1-10 | constructed | T13 | planned |
| LIMITS-03 | Archive cap: stops before an unrecorded candidate is lost | OPT1-04 | constructed | T13 | planned |
| LIMITS-04 | Failed, cancelled and invalid-input runs never appear as succeeded, empty or complete | OPT1-05 | constructed | T13 | planned |
| LIMITS-05 | Complete empty archive → `NO_ROUTE_IN_BOUNDED_MODEL`; truncated empty → none found before the limit | OPT1-07 | constructed | T13 | planned |
| LIMITS-06 | Cancellation reaches the optimiser child process | OPT1-09 | constructed | T13 | planned |
| VERSIONS-01 | Confirmed edits create new input versions; a stale expected version is rejected (`STALE_INPUT_VERSION`) | PROF-05 | constructed | T3 | planned |
| VERSIONS-02 | Old plan versions stay immutable after a revision | PLAN-05 | constructed | T15 | planned |
| VERSIONS-03 | A stale worker cannot overwrite a newer profile or catalogue version | DUR-04 | constructed | T3 | planned |
| VERSIONS-04 | Editing an essential non-protected row creates a new target definition and invalidates earlier ranks | MAP1-04 | constructed | T9 | planned |
| AI_RANGE-01 | [5, 8] fails a minimum of 6 under lower-bound filtering | AIR1-05 | TRACE-01 `score_record` | T7, T8 | planned |
| AI_RANGE-02 | Unscored roles are included by default in exploration and counted | AIR1-05 | constructed | T7, T8 | planned |
| AI_RANGE-03 | A strict planning threshold needs an explicit scoped command and excludes unscored roles | AIR1-06 | constructed | T11, T13 | planned |

Generated properties (plan section 8):

| ID | Property | Owner | Status |
|---|---|---|---|
| PROP-01 | Complete search: permuting the input catalogue preserves feasible sets and ranks | T13 | planned |
| PROP-02 | Duplicate source copies preserve canonical job counts | T7 | planned |
| PROP-03 | Relaxing a resource bound preserves feasibility in the mathematical model | T11, T13 | planned |
| PROP-04 | Review rule, not a test: no false monotonicity is encoded (truncated prefixes may differ; adding options can change ranks) | T13 | planned |

## 4 Untagged M0 requirements (register anchors)

### STATE States, navigation and early value (spec §3)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| STATE-01 | One state vocabulary across chapters, API, database and exports: draft, running, partial, complete, cancelled, blocked by missing information, insufficient coverage, stale, provider unavailable, failed | API, UI | T3, T4 | planned |
| STATE-02 | No hits reads "No matching listings found in the sources checked" with coverage and filters; a failed fetch never becomes "no jobs" | D, UI | T7, T8 | planned |
| STATE-03 | A solver timeout never becomes "no feasible route" | D | T13 | planned |
| STATE-04 | No feasible route: the smallest conflicting set only where proven, otherwise observed bottlenecks; relaxations offered, never applied silently | D, UI | T13, T14 | planned |
| STATE-05 | Labelled route sketch after a target and four practical inputs; never labelled feasible or Pareto; unresolved steps stay unresolved; no fabricated providers, prices or dates | UI | T6 | planned |
| STATE-06 | "What we know": proposed changes in a review tray (accept, edit, undo); facts and inferences styled differently; revision history; a changed constraint shows affected results before invalidating them | UI | T6 | planned |
| STATE-07 | Long processes continue in the background and resume after the tab closes | UI, P | T3, T4 | planned |
| STATE-08 | "Unknown", "skip" and "prefer not to say" accepted, with the result they make less precise; unknown salary is never zero; missing skills are never absence | D, UI | T5, T6 | planned |

### PROF Structured profile and conversational integrity (spec §4)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| PROF-01 | Every field has value, epistemic status, source reference, observation date, verification state and provenance; "no preference" ≠ "not yet asked" | D | T5 | planned |
| PROF-02 | Native structured output then server-side validation; never a silent switch to prose parsing | AD | T5 | planned |
| PROF-03 | Changes commit only after complete validation; partial streamed JSON never commits | D, P | T5 | planned |
| PROF-04 | Only explicit user confirmation establishes a hard constraint | D | T5 | planned |
| PROF-05 | Versioned patches with optimistic concurrency cite supporting message IDs; bounded repair ends in a visible validation failure with the old profile intact | D, P | T5 | planned |
| PROF-06 | Secret fields and plan commitments are never patchable by model output; only allowlisted fields apply | D | T5 | planned |
| PROF-07 | Direct edits and chat proposals use the same application commands | D, API | T5, T6 | planned |
| PROF-08 | One useful question at a time; supplied information is never asked again; a sure user confirms title and seniority and skips personality | M, UI | T6 | planned |
| PROF-09 | Practical, gentle and challenge modes; pause and resume; no anxiety score; acute distress goes to a separately reviewed safety flow; a health condition prompts for accommodations, not history | M, UI | T6 | planned |

### ACQ Web acquisition and its security boundary (spec §6)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| ACQ-01 | Scheme, host, DNS and redirect validation; private, loopback, link-local and metadata addresses blocked, including IPv6 and encoded forms; rechecked after redirects (controlled test server) | S | T7 | planned |
| ACQ-02 | Response size, depth, time and content types bounded; HTML and pasted text only | S | T7 | planned |
| ACQ-03 | Structured fields first (JSON-LD JobPosting, official JSON, stable selectors); model extraction only for residual ambiguity; deterministic code approves records | AD | T7 | planned |
| ACQ-04 | Page text cannot change the interview, reach keys, request files or widen tools (prompt-injection cases) | S, M | T7 | planned |
| ACQ-05 | The acquisition worker has no user profile, model key or master key | S | T7 | planned |
| ACQ-06 | Policy-denied requests create `SourceAttempt` records; a user-supplied URL never overrides permissions; no sign-in or paywall bypass | AD, S | T7 | planned |
| ACQ-07 | No crawler, recursion or browser rendering; an unsupported page returns an explicit limitation and the paste-text option | AD | T7 | planned |
| ACQ-08 | A critical-field disagreement blocks publication with a visible extraction error; adaptive relocation is only a candidate match | AD | T7 | planned |
| ACQ-09 | Scrapling pinned, HTTP fetch and parse only | DOC | T7 | planned |
| ACQ-10 | Manual pasted text is a separately recorded input route with its own provenance | D | T7 | planned |

### JOB Search, canonicalisation and exemplars (spec §7)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| JOB-01 | Canonical employer, occupation and source IDs; agencies distinct from employers; an undisclosed employer stays undisclosed | D | T7 | planned |
| JOB-02 | Syndicated postings deduplicated with every source copy kept; a multi-city job counts once; different levels, contracts or locations never collapse | D | T7 | planned |
| JOB-03 | Missing salary is never the lowest salary; strict "salary confirmed" filter; unknown work rights read "needs checking" | D, UI | T7, T8 | planned |
| JOB-04 | No "probability of getting hired"; "matches your preferences" before assessment | UI | T8 | planned |
| JOB-05 | Advertised, provider-predicted, modelled and unknown pay stay distinct (`salary_is_predicted` kept); snippets never become full descriptions | AD | T7 | planned |
| JOB-06 | Zero to three exemplars per target, as permitted URLs or pasted text; labelled statements of interest; expired exemplars are history, never live vacancies | D, UI | T7, T8 | planned |
| JOB-07 | Favourite, exclude, report error and compare; no automatic application | UI | T8 | planned |
| JOB-08 | Bounded searches with cancellation, cost limits and resumable incremental results | P | T7 | planned |

### ASSESS Capability assessment (spec §9)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| ASSESS-01 | Self-assessed level, demonstrated level and evidence confidence stored separately; an unsupported claim stays self-reported, not false | D | T9 | planned |
| ASSESS-02 | The five answer types are distinguished in a neutral tone; no honesty scoring from speed, vocabulary, accent or sentiment | M, UI | T10 | planned |
| ASSESS-03 | One question graph across targets; shared answers reused; gates first; decision-impact ordering; 8–12 initial prompts; pause and stop; coverage reported, never an employability percentage | D, UI | T9, T10 | planned |
| ASSESS-04 | Evidence records recency, complexity, independence and permitted tool use; AI-assisted work is never presented as unaided | D | T9 | planned |
| ASSESS-05 | An evidence change recomputes only the affected gaps | D | T9 | planned |
| ASSESS-06 | Gaps classified as learn, demonstrate, credential, experience, eligibility, information or preference conflict; no course for a gap a small assessment closes, nor for a work-rights issue | D | T9 | planned |

### OPTN Options, funding and the review checkpoint (spec §10)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| OPTN-01 | Stable action concepts separate from dated offerings and intakes, with the captured fields of spec §10 | D | T11 | planned |
| OPTN-02 | An apprenticeship's time, wages, training and credential are modelled once, as one composite action | D | T11 | planned |
| OPTN-03 | Checkpoint before optimisation: grouped by gap; pin, exclude, correct; pinned is not enrolment; missing tuition, entry or timetable keeps an option provisional and out of unqualified recommendations; incomplete research gives a partial plan with labelled holes | UI, D | T12 | planned |
| OPTN-04 | A future job is a role class plus a search/review gate, never a named vacancy presumed open | D | T11 | planned |
| OPTN-05 | Provider employment-outcome marketing stays an unverified claim | D | T11, T12 | planned |
| OPTN-06 | No finance applications, creditworthiness checks or regulated credit recommendations; grants and employer support shown before debt, with total charges | UI | T12 | planned |

### FRESH Cache, freshness and evidence lifecycle (spec §11)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| FRESH-01 | Research and cache stay inside their workspace in PostgreSQL with ownership checks; only immutable public packs are shared | S, P | T7 | planned |
| FRESH-02 | Maximum age enforced on access: jobs 24 h; fees and intakes 7 days; funding availability 48 h; funding rules 30 days with a stale warning; syllabus 90 days; official datasets by vintage | D | T7, T11 | planned |
| FRESH-03 | A failed refresh never extends freshness; last attempt, last success, publication, valid-from and valid-until are separate timestamps | D | T7 | planned |
| FRESH-04 | Concurrent refreshes deduplicated; errors back off | P | T7 | planned |
| FRESH-05 | Computed objects store dependency versions; a changed price marks dependants stale; a closed job changes status; a revised requirement flags routes | D, P | T11, T15 | planned |
| FRESH-06 | Stale data used anywhere is visibly labelled with its date | UI | T8, T12, T14 | planned |

### PLAN Progress and the chosen plan (spec §15)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| PLAN-01 | Planning progress, evidence acquired and real-world action stay distinct; completing a task never awards a skill or credential | D, UI | T15 | planned |
| PLAN-02 | One next-action card with an alternative and rest/reschedule; no streaks, shame or scarcity | UI | T15 | planned |
| PLAN-03 | Readiness bands evidenced, planned, conditional, unresolved; no comparison with other users | UI | T15 | planned |
| PLAN-04 | Selecting a route summarises target, trade-offs, costs with basis, peak payment, reserve, workload, conditions and source dates, and asks for confirmation of consequential assumptions; it never enrols, applies or resigns | UI, D | T15 | planned |
| PLAN-05 | Immutable `PlanVersion` holds target/matrix, route, profile, evidence, scenario, model, assessment and source versions | P | T15 | planned |
| PLAN-06 | A closed intake or changed fee yields a comparison of affected steps; the old version stays readable until the user accepts a revision | D, UI | T15 | planned |
| PLAN-07 | Replanning uses completed evidence, sunk costs and remaining commitments; never repeats completed learning; accounting bases stated | D | T15 | planned |

### EXP Printable and portable plan (spec §15)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| EXP-01 | Print, JSON and ICS come from one immutable snapshot and agree on numeric fields and snapshot ID | UI, D | T15 | planned |
| EXP-02 | The print contains the seven parts of spec §15 (overview through source register and optimisation limits) | UI | T15 | planned |
| EXP-03 | ICS: proposed/conditional labels, original timezone and date semantics, stable UID, revision sequence, a UK DST boundary and all-day dates, parsed by an independent library; no external events created | D | T15 | planned |
| EXP-04 | Sensitive notes and financial detail can be omitted; QR codes never hold secrets or private-plan links | UI | T15 | planned |
| EXP-05 | Monochrome legible; no step card split across pages; no clipped tables (Chromium automated; Safari is H-04) | UI | T15 | planned |

### MODEL Model strategy and API keys (spec §16)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| MODEL-01 | One pinned approved Spark model; no automatic escalation or provider substitution; registry stores ID, mode, price version, capabilities, evaluation status | D | T5 | planned | first entry: ADR 0003 |
| MODEL-02 | Standard IDs for personal data; Contributor never selected silently; a `-contributor` production model rejected at startup; the test model refused for any non-synthetic workspace | D | T3, T5 | planned | spike rejects `-contributor` production IDs (ADR 0003) |
| MODEL-03 | Contract tests for streaming, schemas, refusals, truncation, timeouts and usage reporting | AD | T5 | planned | |
| MODEL-04 | An invalid, over-budget or unavailable key preserves work and states the exact limitation; editing, demo, saved comparison and printing still work | UI, S | T3, T5 | planned | invalid key 401 observed (spike calls 1, 9, 11) |
| MODEL-05 | Key stored with AES-GCM, unique nonce, workspace/record IDs as associated data, versioned runtime key outside database, code and backups; ownership checked before decryption; rotation and revocation tested | S | T3 | planned | sealing pattern spike-verified (ADR 0002) |
| MODEL-06 | No key in browser storage, URLs, analytics, errors, exports, prompts, journals, logs or command arguments | S | T3, T16 | planned | |
| MODEL-07 | Background work requires explicit consent to encrypted key storage; declining keeps editing and saved plans usable | UI | T3, T4 | planned | |
| MODEL-08 | Per-run and per-period spend caps; estimate shown before deep research; concurrent reservation; usage reconciled; ambiguous charges recorded as unknown | S, P | T3, T16 | planned | |
| MODEL-09 | Live calls only through explicit budget-capped commands, never in `make check` or `make acceptance`; every call ledgered with cost (R5) | S | T1, T3 | spike-verified | `docs/evidence/live-usage.md`; product command `make live-smoke` is T3 |

### DUR Durable execution (spec §17)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| DUR-01 | Domain write and outbox row commit together; dispatch is at-least-once with a stable workflow ID | P | T3 | spike-verified | ADR 0002 decision 8 |
| DUR-02 | Activities idempotent (keys, fingerprints, unique constraints); duplicate model spend reconciled; no exactly-once claim; accepted output checked before re-calling the model (carry-forward M4) | P | T3 | planned | |
| DUR-03 | Long operations return 202 and a run ID; server-sent events with IDs allow reconnect; the terminal API state is authoritative; partial results carry completeness and freshness | API, UI | T3, T4 | planned | |
| DUR-04 | A stale profile version cannot overwrite a newer one | P | T3 | planned | |
| DUR-05 | Cancellation reaches model calls and compute processes, not just the spinner | P, S | T3, T13 | planned | |
| DUR-06 | Workspace deletion removes private payloads, object copies and workflow histories (or their payload keys) | P, S | T15, T16 | planned | |
| DUR-07 | Research snapshots its inputs; solves consume a frozen snapshot, never a moving catalogue | D, P | T11, T13 | planned | |
| DUR-08 | An app-database outage during an activity ends in a typed terminal state, never a run stuck queued (carry-forward, ADR 0002 decision 7) | P | T3 | planned | |

### API Data contracts and errors (spec §18)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| API-01 | Versioned endpoints; writes separate from reads; authentication and ownership on every object; cursor pagination | API | T3 | planned |
| API-02 | Error envelope: stable code, message, retryability, affected stage, correlation ID; codes `SOURCE_BLOCKED`, `RETRIEVAL_FAILED`, `INSUFFICIENT_EVIDENCE`, `SCHEMA_INVALID`, `MODEL_UNAVAILABLE`, `BUDGET_EXCEEDED`, `SOLVE_LIMIT_REACHED`, `STALE_INPUT_VERSION`, `FEATURE_NOT_IN_M0`, `MODEL_SCOPE_EXCEEDED`, `COARSE_MODEL_UNRESOLVED`, `NO_ROUTE_IN_BOUNDED_MODEL` | API | T3 (envelope); each code's owning task | planned |
| API-03 | No fabricated empty success payloads | API | T3 onward | planned |
| API-04 | `Money` (≥ 0) for payments, `SignedMoney` for economic values; minor-unit exponent is metadata, never an assumed /100; unknown money is null, not zero; a field-state wrapper keeps skipped, unasked and unresolved apart | D, API | T3, T11 | planned |
| API-05 | Stage invariants: local search needs a confirmed target and work area; a budget-qualified solve needs confirmed budget semantics; an economic solve needs a horizon and baseline | D | T5, T11 | planned |
| API-06 | Every derived object keeps referential integrity and provenance that locates its supporting span | P | T7 | planned |

### SEC Security, privacy and operations (spec §19; L0 identity)

| ID | Requirement | Layer | Owner | Status |
|---|---|---|---|---|
| SEC-01 | Invitation and ownership checked for API, cache, objects, stream, workflow and key use; uninvited and cross-workspace requests fail | S | T3 | planned |
| SEC-02 | Row-level controls enforced in the database with non-owner roles, including the worker | S, P | T3 | planned |
| SEC-03 | Emulator tokens accepted only under explicit local configuration; unsafe environment or host fails closed | S | T3 | planned |
| SEC-04 | No advertising or session replay; logs hold record IDs and error classes; telemetry redacted | S | T3, T4 | planned |
| SEC-05 | The model receives the minimum profile subset; search queries never carry names, finances or CV text | M, S | T6, T7 | planned |
| SEC-06 | Data export, correction, deletion and revocation work | S | T15, T16 | planned |
| SEC-07 | Dependency locks and licence notes; secret, dependency and migration checks; PostgreSQL and blob backup/restore with keys handled separately | S | T3, T16 | planned |
| SEC-08 | A provider outage degrades to dated saved data or an explicit unavailable state; no alternate provider; manual text is a user-selected mode | S | T7, T16 | planned |
| SEC-09 | Model-output evaluations cover hallucinated course names, fabricated citations, altered constraints, unsafe financial assumptions, demographic stereotyping, excessive reassurance and prompt injection | M | T6, T7, T10 | planned |
| SEC-10 | Users can report an error, and corrections keep provenance | UI | T8, T15 | planned |

### UI Visual system and accessibility (spec §14; plan §§4–5)

| ID | Requirement | Layer | Owner | Status | Evidence |
|---|---|---|---|---|---|
| UI-01 | Semantic token set (surfaces, text, focus, selection, industry, status) with WCAG contrast measured by script, not assumed | DOC | T2 | planned | |
| UI-02 | Design rule: industry colour never means status; sea-glass reserved for selection and action; ≤ 5 named industries plus Other with a stable mapping (implementation: UI-04, VIS1-02) | DOC | T2 | planned | |
| UI-03 | Licensed self-hosted fonts with licence texts beside the files; tabular numerals for money and time | DOC | T2 | planned | |
| UI-04 | Tokens, fonts and the status vocabulary implemented in `apps/web` and Storybook (loading, empty, unknown, conditional, stale, error, disabled) | UI | T4 | planned | |
| UI-05 | Motion: 120–180 ms controls, 220–320 ms panels, ≤ 450 ms graph reveal, no continuous force motion; reduced-motion and calm mode remove spatial animation, not information | UI | T4, T14 | planned | |
| UI-06 | WCAG 2.2 AA: axe clean; keyboard-only completion; visible focus; headings and names; focus return from drawers; 200 % zoom; no horizontal overflow at 390 px; announced errors | A11Y | T4 onward | planned | |
| UI-07 | SVG surfaces have DOM equivalents; every action works through a list; tooltips hold no unique information; filtering never drops keyboard focus | A11Y, UI | T8, T14 | planned | |
| UI-08 | Measured budgets: input feedback ≤ 100 ms; p95 linked filter/selection ≤ 150 ms at 100 visible jobs and a 1,000-mark projection; device, browser and dataset reported | UI | T8, T14 | planned | |
| UI-09 | Desktop: slim chapter rail, central work area, evidence drawer. Mobile: chapter menu, cards and lists, bottom evidence sheet, focused graph views (never a shrunken desktop graph) | UI | T4 | planned | |
| UI-10 | Three signature compositions with real fixture numbers, long labels, mobile variants, unknown-data and failure states; screenshots at 1440×900 and 390×844 (human approval is H-02) | V | T2 | planned | |
| UI-11 | Screenshot approval of all six chapters at 1440×900, 390×844 and 768×1024 across default, selected, empty, partial, stale, unavailable and failed states, with long names, three targets, negative economic cost, zero results and the 100-job limit | V, H | T4, T8, T14, T16 | planned | |

## 5 Specification section 20 non-deferrable checks

| Check | M0 pass condition | Covered by |
|---|---|---|
| Readiness/outcomes | Inspectable OUT-1 spans and rubrics; planned ≠ demonstrated; statutory gates cannot be demoted | OUT1-01–07, RDY1-01–04, MAP1-05, READINESS-01–04 |
| Money/time | TRACE-01 and FIN-1 arithmetic; prefunding counterexample; workload envelope; original dates | TRACE01-01/02/07/08, FIN1-01–10, PREFUND-01–03, WORKLOAD-01–04, TIME-01–04 |
| Search correctness | DFS agrees with oracle; F1–F3, equal points, family variants, three-dominator case | OPT1-08, PARETO-01–03, FAMILY-01/02, TRACE01-03, DIRECTAI-01 |
| Failure semantics | Limits, failed source, cancellation, crash and true empty complete archive distinct | LIMITS-01–06, STATE-02/03, OPT1-05 |
| Permissions | Uninvited and cross-workspace access fail everywhere | SEC-01, SEC-02 |
| Secrets/spend | No key in logs, history, prompts or exports; revocation stops future calls; concurrent reservation and duplicate-spend ambiguity | MODEL-05/06/08, ARC1-06, DUR-02 |
| Untrusted input | SSRF/redirect blocks, access policy, prompt injection | ACQ-01, ACQ-04, ACQ-06 |
| Research | Snippets never full descriptions; missing data and unscored roles visible; nothing invented | JOB-05, AIR1-05, AI_RANGE-02, FUNDING-01, OPTN-03 |
| Recovery | Restart without corrupting accepted records; stale writes fail; cancellation reaches children | ARC1-05, DUR-02/04/05, VERSIONS-03, LIMITS-06 |
| UI/export | List, dendrite, scatter, sliders and Gantt share selection and filters; keyboard; print/JSON/ICS agree | VIS1-07, VIS2-01–10, EXP-01, UI-06 |
| Privacy/operations | Privacy/DPIA decision, notice and consent, deletion, basic restore | H-08, SEC-06, SEC-07, DUR-06 |

## 6 Human-only gates (ruling R2)

Agents do the automatable part and record these as **not run — requires human**, with a
checklist. An agent critique is never a review score.

| ID | Gate | When | Status | Checklist |
|---|---|---|---|---|
| H-01 | Design-review scores (1–5 per category, every category ≥ 4 before release) | Sprints 1, 3, 7, 9 | not run — requires human | sprint review packages |
| H-02 | Approval of the three Sprint 0 signature compositions | Sprint 0 | not run — requires human | `docs/reviews/sprint-0.md` |
| H-03 | VoiceOver walkthrough on the target Mac | Sprint 9 | not run — requires human | T16 |
| H-04 | Real Safari checks, including print | Sprints 8, 9 | not run — requires human | T15, T16 |
| H-05 | Five formative task sessions (4 of 5 complete unaided; any dangerous misunderstanding blocks) | Sprint 9 | not run — requires human | T16 |
| H-06 | Source rights review of every retained corpus page | Sprints 3–5 | not run — requires human | `corpus/README.md` |
| H-07 | Domain reviewer sign-off on consequential requirement/outcome mappings and the financial worked examples, including the fixture hand check | Sprints 0, 4, 5 | not run — requires human | `docs/evidence/fixture-hand-check.md` |
| H-08 | Privacy assessment or DPIA decision before any real person's data is processed | before real data | not run — requires human | spec §19 |
| H-09 | Product-owner confirmation of ADR 0003 (Contributor test model for synthetic data) | open | not run — requires human | ADR 0003 |
| H-10 | Accountable review of each published AI Resilience range record | Sprint 3 onward | not run — requires human | AIR-1 step 3 |

## 7 Not tested in L0, by decision

Recorded so their absence is visible, not forgotten (ADR 0001; spec BND-1 M1 column).

| Item | Why | Reference |
|---|---|---|
| GLO-1 global regional-capability contract and three-jurisdiction qualification | M1 | spec §3 |
| Hosted M0 infrastructure (Cloud Run, GCE, Cloud SQL, Cloud Storage, Secret Manager), TLS, real Google sign-in, deployed smoke test | L0 local override | ADR 0001 |
| Motion halos, semantic zoom, mini-map, generated illustrations, animated journey overlays | M1 or deferred | ADR 0001; spec §§7, 13, 14 |
| Muse Wonder escalation, image generation, tagged accessible PDF, shared research cache, session-only keys, new-loan optimisation, adaptive scenario policies | M1 | spec §§10, 12, 15, 16 |
| Live Adzuna integration | no credentials; the adapter's fixture contract is tested; live is "unverified" | ruling R4 |
