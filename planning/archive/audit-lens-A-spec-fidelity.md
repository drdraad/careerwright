# Audit lens A: specification fidelity (Task A1)

HEAD 8e78060, branch `l0-local-release`, read-only. Question: does the solution as built and as
planned still deliver the specification's intended functionality?

Sources read: spec v1.3 (all M0 sections, sections 2, 3, 22), plan v1.4 (sections 1, 4, 6, 9,
10, 11 and every sprint card), `docs/plan/l0-sprint-tasks.md` (current position and every
remaining card), the requirements register (every row, condensed), ADRs 0001, 0007 (decision 13),
0008, 0010, 0012 (decisions 10–11), 0013, 0014, the ledger (rulings and parked items), the
carry-forward files for Tasks 8, 10, 12 and W2D, the web app (`src/app`, `src/components`,
`src/lib`, `e2e`), the backend API routers, and two captures from the last acceptance run.

Method for "reachable": a capability counts as usable only if `apps/web/src` (non-test,
non-story) calls the endpoint behind it. Of the 70 operations in the generated client
(`apps/web/src/generated/api/sdk.gen.ts`), **46 have no caller in the web app**; the 24 that do
are all You-chapter, key and workspace operations (counted with `grep -lw` per operation).

---

## 0 Headline findings

1. **Only the You chapter is usable today.** A person can sign in, choose sure or unsure, talk,
   review and undo proposed facts, get a grounded slate, choose up to three targets and see an
   early sketch. Roles, Skills, Options and Plan are "Not built yet" places; Routes shows a
   fixture preview in the fixture workspace only (`apps/web/src/components/ChapterView.tsx:35-65`,
   `:220-246`; capture `apps/web/test-results/visual-1440x900-…/screenshots/options--1440x900.png`).
   Confidence high.
2. **Options, routes and plans exist only for the option pack's four targets.** Live research
   extracts job postings only (`backend/src/careerwright/evidence/pages.py:151`); the planning
   catalogue reads the pack only (`backend/src/careerwright/planning/pack.py:107-112`); no
   workspace catalogue table exists (migrations r0001–r0032). Task 7's card promised "Live
   research writes the catalogue contract" (`docs/plan/l0-sprint-tasks.md:618`; plan section 9,
   `docs/plan/development-plan.md:823`), but it was not built and no remaining card or
   carry-forward owns it. For any other target, the person meets a dead end after Skills.
   Unrecorded. Confidence high.
3. **The money and time inputs every route needs have nowhere to live yet** (baseline income,
   opening cash, living costs, reserve, commitments, debts, availability). ADR 0013 decision 11
   and `carry-forward-task-12.md:3-11` give them to Task 12, but Task 12's card does not name
   them (`l0-sprint-tasks.md:927-953`). Work rights, residence, remote working and target
   seniority have no field and no owner at all. Confidence high.
4. **Several M0 promises are on no card:** spend limits and the cost estimate before research
   (spec line 975; API built, no UI, no card), CV paste (spec line 156; chat messages are capped
   at 2,000 characters, `backend/src/careerwright/profile/interview.py:62`), the supported-region
   statement (spec line 38; BND1-02 orphaned), role-card outlook labels and hiring signal (spec
   lines 309-311), session-length modes (spec line 237), optional work samples (spec line 546).
5. **Discovery drifted, by decision:** titles are resolved, never searched; every other search
   runs over essential-skill names only; one-word work style is not searched; generic answers find
   nothing; the pool target is soft (ADR 0007 decision 13; W2B rulings, ledger lines 682-697).
   This answers the product owner's "arbitrary matching on keywords" complaint, but it shrinks
   slates and sits uneasily with REC-1 and DIV-1. It is provisional, and on session W2's sheet.

---

## 1 Capability table

Status key: **Usable** (Built, usable), **Unreached** (Built, not reachable), **Planned**,
**Drifted-D** (drifted, decided), **Drifted-U** (drifted, unrecorded), **Missing**.
Spec refs are line numbers in `Careerwright_Product_Specification.md`.

### Section 1 and BND-1 (build boundary)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 1 | England/en-GB/GBP; ≤3 cities, ≤3 targets, cities resolved to a finite list | 38, 69 | Usable | BND1-03 verified; `profile/document.py:322-327` resolves cities | — |
| 2 | Supported slice stated before detailed collection; unsupported-region state | 38 | Missing | BND1-02 `planned`, owner T6 (complete), no evidence; no "England only" wording in `apps/web/src` | Orphaned register row |
| 3 | Residence and eligibility never inferred; work-rights and residence collected | 38, 159 | Missing | BND1-04: "no residence or work-rights field exists yet; the task that adds them owns the rest"; no task named | Hard feasibility input (spec 751) with no owner |
| 4 | Remote-only user with employment country and timezone; remote takes no city slot | 38, 157 | Missing | BND1-05 owner T7 (complete); no remote field in `profile/document.py:162-199` | Orphaned |
| 5 | A complete session: entry → shortlist → matrix → evidence questions → real option review → route comparison → printable plan | 40 | Planned (Tasks 10, 12, 8, 13a, 13b, 14, 15, 16) | `l0-sprint-tasks.md:269-273` | Real option review only for pack targets (row 52) |
| 6 | Non-deferrable invariants | 61 | Usable where reached | BND1-09 rows (STATE-02/03, PROF-04/06, SEC-01, AIR1-02…) mostly verified in backend | — |
| 7 | At a hard bound, ask to pin/exclude; persist removed count | 71 | Planned (Task 12) | BND1-07 | — |
| 8 | Regulated pathway beyond 24 months: sketch + unsupported-model state | 71 | Unreached | BND1-08 verified (`MODEL_SCOPE_EXCEEDED`); words are Task 10's | — |
| 9 | Hosted M0 replaced by local L0 (emulator auth, loopback, local secrets, local smoke) | 34-59 | Drifted-D | ADR 0001 table rows 25-35 | Decided |

### Section 2 (press release and FAQ, M1 narrative, read as headline promises)

| # | Promise | Spec | Status | Evidence | Note |
|---|---|---|---|---|---|
| 10 | Start sure or unsure; guided conversation | 97, 117-119 | Usable | rows 13, 18 | — |
| 11 | Varied, researched directions incl. less familiar roles | 97 | Usable, Drifted-D | row 26 | Skill-join rules (row 26) |
| 12 | Up to three careers and three places "potentially across countries" | 97 | Usable for England | row 1 | Cross-country is M1 (GLO-1) |
| 13 | Living map grouped by company, coloured by industry; pay, demand, AI filter | 99 | Planned (Task 8); colour Drifted-D | VIS1 rows; ADR 0014 d5 | Industry by glyph |
| 14 | Recognise existing skills | 101 | Unreached (Task 9, W2B); Planned (Task 10, W2C2) | rows 41-44 | — |
| 15 | "Researches the missing pieces: courses, qualifications, apprenticeships, funding and stepping-stone roles" | 101 | Drifted-U | row 52 | Pack's four targets only |
| 16 | Compare combinations within budget, cash limits, hours | 101-103 | Unreached (checker); Planned (13a, 13b, 14) | rows 58-66 | Inputs unstored (row 14) |
| 17 | Printable plan; return and revise | 109 | Planned (Task 15) | rows 72-74 | — |
| 18 | Own Meta key "with clear usage controls" | 111 | Key Usable; usage controls Missing | rows 76-78 | Spend UI on no card |
| 19 | "Why are some paths grey?" with a named better route | 123 | Planned (Task 14) | VIS2-04 | — |

### Section 3 (customer experience)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 20 | Six persistent chapters, navigable, not a wizard | 141 | Usable as a shell | `ChapterView.tsx`; `e2e/world.spec.ts:440` ("a chapter not built yet shows its place") | Four are empty places |
| 21 | Sure/unsure entry | 145 | Usable | REC1-10; `lib/vocabulary.ts:207-210` | — |
| 22 | Import a CV (M0: paste text), facts need confirmation | 145, 156 | Missing | no CV path in UI or API; `MAX_MESSAGE = 2_000` (`profile/interview.py:62`); no card | Unrecorded |
| 23 | Minimum inputs: work status, experience, qualifications, commitments, work mode, relocation, right to work, sponsorship, language, accommodations, contract, hours, travel, industries, values, pay-cut willingness, calendar windows, funds, reserve, take-home income, outgoings, borrowing, debt | 154-163 | Partly Usable; money/time subset Planned (Task 12 carry-forward); rest Missing | profile schema 3 has 12 fields (`profile/document.py:162-199`); ADR 0013 d11 lists the unstored planning inputs | Task 12 card silent; rest unrecorded |
| 24 | Unknown/skip/prefer not to say, with what becomes less precise | 163 | Usable | STATE-08 (T5, T6 parts); `ChapterView.tsx` "Less precise without" | — |
| 25 | Labelled route sketch within five minutes | 187 | Usable | STATE-05 verified; `SketchCard.tsx`; behind a disclosure since the W2C1 ruling (ledger line 733) | 5-minute target is H-05 |
| 26 | Rail, work surface, evidence drawer, strip (targets, cities, budget, saved) | 193 | Usable | UI-09 T4 part; `e2e/keyboard.spec.ts:26-68`; capture shows strip | Tablet strip drops work areas and budget (parked, session W2) |
| 27 | Long processes continue and resume after closing the tab | 193 | Usable | STATE-07; `e2e/session.spec.ts:46` | — |
| 28 | "What we know": proposals, fact vs inference styling, undo | 195 | Usable | STATE-06; `e2e/conversation.spec.ts:60` | — |
| 29 | Revision history always available | 195 | Unreached | `GET .../profile/versions` exists; `listProfileVersions` has no web caller | No card |
| 30 | A changed constraint shows affected results first | 195 | Planned | plan section 4 "Act, see the consequence, then confirm" (`development-plan.md:180`) | — |
| 31 | What-if workspace without overwriting the chosen plan | 195 | Missing | several workspaces allowed; no copy-of-plan path; no card | Low impact before plans exist |
| 32 | One state vocabulary | 199 | Usable | STATE-01 verified; `lib/vocabulary.ts:34-55` | — |
| 33 | "No matching listings found in the sources checked"; failed scrape ≠ no jobs | 199 | Unreached | STATE-02 backend verified; UI Task 8 | — |
| 34 | No feasible route: smallest conflict where proved, relaxations offered | 201 | Planned (13a, 14) | STATE-04 | — |

### Section 4 (exploration and interview)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 35 | Structured profile; every field with state, source, date, provenance | 215-229 | Usable | PROF-01 verified | Only 12 fields (row 23) |
| 36 | Target hypothesis carries seniority; sure user confirms seniority | 225, 236, 1109 | Missing | no `seniority` in `backend/src/careerwright/profile` or `capability` (grep); level asked in the opening question but stored only inside the title text | Unrecorded; AI assessment unit is occupation + seniority (368) |
| 37 | One question at a time, typed patches, no re-asking | 233-239 | Usable | PROF-08 (UI and contract done; live sampled once per case) | — |
| 38 | Two-minute, five-minute and deeper modes | 237 | Missing | no code (grep), no card | Unrecorded, low |
| 39 | Practical/gentle/challenge, pause/resume, distress support | 291-293 | Usable | PROF-09; `e2e/conversation.spec.ts:158`; `e2e/world.spec.ts:224` | — |
| 40 | Enjoy / believe / evidence kept apart | 245 | Usable | REC1-04 | — |
| 41 | REC-1: work-style profile as one source of hypotheses | 245-247 | Drifted-D (provisional) | REC1-03: one-word work style not searched; ADR 0007 d13; on session W2's sheet (`carry-forward-task-W2D.md:8`) | Sits "uneasily with REC1-03" (W2D sheet) |
| 42 | CareerSuggestion fields; why / might not / try it; broaden, less familiar, exclude, show why not | 251-253 | Usable | REC1-05, REC1-08; capture `you--slate--1440x900.png` | — |
| 43 | Model-written "Why this could suit you", span-verified | 255 | Usable | REC1-11 | — |
| 44 | Demographic counterfactual evaluation | 257 | Planned (Task 16) | REC1-09 inconclusive; pass rule still open | — |
| 45 | DIV-1: full-catalogue FTS + alias retrieval, multiple task/interest/skill queries, pool of 60–120 | 261-265 | Drifted-D (provisional) | ADR 0007 d13 (`0007…md:511`): titles resolved not searched; others over essential-skill names; >50-occupation or >5-skill searches find nothing alone; DIV1-02 target made soft (ledger line 689) | Smaller slates; P01 empty offline at one point (ledger line 688) |
| 46 | DIV-1 slate shape 2/2/2, family limit, relevance floor | 275-281 | Usable | DIV1-11 verified | — |
| 47 | DIV-1 evaluation against relevance-only and common-careers baselines | 285 | Missing (partial) | DIV1-08 `planned (partial)`, owner T6 (complete) | Orphaned |
| 48 | Native structured output, commit only after validation, bounded repair | 299-301 | Usable | PROF-02, PROF-03, PROF-05 | — |

### Section 5 (labour-market intelligence)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 49 | Role card (role, synonyms, workday, pay, AI score, evidence quality, dates) | 309 | Unreached (data); Planned (Task 8) | `api/routes_reference.py:18-38` (SOC candidates, regional ASHE, trend unavailable, AI evidence); AIR1-13 T8 | Task 8 card lists map, list and pay lens, not the card itself |
| 50 | Hiring signal and outlook labels (Growing … Insufficient evidence) | 309-311 | Missing | no code (grep), no register row, Task 8 card silent | In L0 every label would be "Insufficient evidence"; still unstated |
| 51 | Evidence hierarchy: ASHE regional, never city; trend unavailable from one snapshot | 315-324, 346 | Unreached | TAX1-03 verified; TAX1-05/06 Planned T8 | — |
| 52 | TAX-1 ISCO pivot, distinct namespaces, import manifests | 340-346 | Usable (backend data) | TAX1-01, 02, 04, 07 verified | — |
| 53 | Reviewed UK-SOC mappings (M0 data identity) | 46, 342 | Drifted-D | ADR 0010 decision ~91: reviewed only by an accountable reviewer; none in L0 (H-10) → no modelled pay anywhere | Decided; costs the person pay figures on role cards |
| 54 | AIR-1 record model, publication checks, lower-bound filter, unscored state | 348-394 | Unreached; no real records (Drifted-D) | AIR1-02/03/04/07/11/12 verified; slate API takes `min_ai_resilience` but `SlateControls` (`lib/queries.ts:89-93`) never sends it; H-10 | Spec 362 permits an all-unscored beta |
| 55 | "Use this limit in my plan" | 390 | Planned (13a) | AIR1-06 | — |

### Sections 6–7 (acquisition, jobs, opportunity map)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 56 | Scrapling HTTP fetch, SSRF, manifest, SourceAttempt, injection safety | 400-455 | Unreached | ACQ-01/02/04/05/06/08/09/10 verified; `submitAcquisition`, `submitSearch` no web caller | — |
| 57 | Meta search finds URLs; model extraction only for the residual | 451 | Unreached | ACQ-03 (page_extraction run kind, ≤5 pages) | — |
| 58 | Live bounded Adzuna search | 44 | Unreached; live-qualified | ledger line 398; `docs/evidence/live-usage.md` row 32 | Plan's "no live vacancy data in L0" premise (`development-plan.md:290`) is now stale |
| 59 | Paste text where a page cannot be read | 406 | Unreached | ACQ-10 verified; `pasteText` no caller | — |
| 60 | Search, dedupe, canonical employer, agencies apart, multi-city counted once | 463-465 | Unreached | JOB-02, JOB-08 verified; JOB-01 orphaned partial | — |
| 61 | Job relevance score with inspectable parts; "matches your preferences" | 467-469 | Planned (implicit) | JOB-04 T8; plan order "job scoring" (`development-plan.md:298`); no code; not in Task 8's deliverables | Make explicit |
| 62 | Favourite, exclude, report error, compare | 469 | Unreached (favourites); Planned (T8, T15) | JOB-07, SEC-10 | — |
| 63 | VIS-1 static SVG dendrite, ≤100 nodes, filters, pay lens, list | 471-485 | Planned (Task 8) | VIS1-01…11 all `planned` | — |
| 64 | VIS-1/AIR-1 industry colour | 388, 473 | Drifted-D | ADR 0014 d5 (`0014…md:93-96`) moves industry to glyph and label | Register VIS1-02, AIR1-08, UI-02 still say colour |
| 65 | 0–3 exemplars per target; never live vacancies | 489 | Unreached; Planned (T8) | JOB-06 (pasted route verified; URL exemplars and labels T8) | — |

### Sections 8–10 (skills, assessment, gaps and options)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 66 | MAP-1 provisional matrix from ESCO, labelled with versions and counts | 497 | Unreached; Planned (T10) | MAP1-01 T9 part; `listCapabilityMatrices` no caller | Works for any ESCO target |
| 67 | Matrix enriched by the person's exemplars | 497 | Planned (carry-forward) | ADR 0012 decision 11 (`exemplar_rows_read: false`); `carry-forward-task-10.md:4` | Not on Task 10's card |
| 68 | Row edits make a new definition; protected gates cannot be demoted | 499-501 | Unreached | MAP1-04, MAP1-05, RDY1-04 verified | — |
| 69 | Matrix contract; levels 0–4; unknown ≠ 0 | 518-524 | Unreached | MAP1-07, MAP1-08 verified | Anchor 0 reworded to "assessed cannot yet" (ledger 7c ruling) |
| 70 | Interview pattern: five answers, rubric visible, neutral tone | 540-548 | Unreached; Planned (T10) | ASSESS-01/04 verified; ASSESS-02 T10 | — |
| 71 | Optional work samples / artifact review | 546 | Missing | no card; ADR 0012 mentions only as a remaining option | Unrecorded, low |
| 72 | Question budget: gates first, decision-impact order, 8–12 prompts, stop | 550-560 | Unreached; Planned (T10) | ASSESS-03 T9 part | — |
| 73 | Gap classes and abstract plan | 566-570 | Unreached | ASSESS-06 verified | — |
| 74 | Concrete option types researched for the person's targets (courses, apprenticeships, bridge jobs, funding) | 572-584, 630 | Drifted-U / Missing | live research extracts `JobPosting` only (`evidence/pages.py:151`); `pack_catalogue` reads the pack only (`planning/pack.py:107-112`); pack targets: Data quality analyst, IT support technician, Registered nurse, Bookkeeping assistant (`england-option-pack-0.2.0.json`); Task 7 card line 618 promised it | No remaining card or carry-forward owns it |
| 75 | Funding statuses; grants before debt; no credit advice | 584-596 | Unreached (statuses); Planned (T12) | Task 11; OPTN-06 T12 | Stacking carried to T12 |
| 76 | OUT-1 row mappings, confidence, spans, review state | 598-608 | Unreached; review UI Planned (T12) | OUT1-01…07, 11 verified; OUT1-09 T12; accept/override persistence carried to T12 | — |
| 77 | RDY-1 readiness and apply-now lead | 610-616 | Unreached; Planned (T10) | RDY1-01/04/05 verified; RDY1-03 T9 part | — |
| 78 | Option review checkpoint: pin, exclude, correct, provisional holes | 618-622 | Planned (T12) | OPTN-03 | — |

### Sections 11–12 (lifecycle and optimisation)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 79 | Workspace-private cache; ages enforced on access; failed refresh never extends | 628, 636-652 | Usable (jobs, backend); course/funding ages Missing | FRESH-01/03/04 verified; FRESH-02 owners T7, T11 (complete) | Orphaned part |
| 80 | Option pack: immutable, dated, reviewed | 630 | Usable (backend data) | OPTN-10 verified, pack 0.2.0 | Surface labels Planned (OPTN-08) |
| 81 | Dependency invalidation of computed objects | 654 | Planned (T15) | FRESH-05 | — |
| 82 | TIME-1 monthly grid, workload envelope, prefunding | 682-701 | Unreached | TIME1-02…06 verified (checker) | — |
| 83 | Decision variables, prerequisites, offer gate | 703-713 | Unreached | PLN-02, PLN-05 verified | Information-gathering and waiting actions orphaned (PLN-01) |
| 84 | FIN-1 economic and direct cost, baseline, scenarios | 723-745 | Unreached; display Planned (T14) | FIN1-01…04, 06, 10, 11 verified | Baseline has no store (row 23) |
| 85 | Hard feasibility constraints incl. work permission, borrowing consent, debt limits, AI threshold | 747-773 | Partly Unreached | PLN-06 T11 part | Work-permission and borrowing inputs have no field (rows 3, 23) |
| 86 | Scenarios: base, delay, no award, no offer | 775-783 | Unreached; display Planned (T14) | PLN-08 verified | — |
| 87 | ROU-1 families and variants | 715-721 | Planned (13a, 14) | ROU1-01…04 | — |
| 88 | OPT-1 DFS, sound pruning, archive, caps, coverage, oracle | 785-803 | Planned (13a, 13b) | OPT1-01…16 all `planned` | — |
| 89 | F1–F3 layers over the full archive | 805-837 | Planned (13a) | PARETO family | — |

### Sections 13–15 (comparison, visuals, plan)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 90 | VIS-2 scatter, layers, whiskers, sliders, Gantt, route cards | 843-871 | Planned (T14); fixture preview only today | VIS2-01…11; `ChapterView.tsx:220-226`, `RoutePreview.tsx` | — |
| 91 | Art direction (calm observatory) | 877-895 | Drifted-D | ADR 0014; plan section 4 | Override, not counted |
| 92 | WCAG 2.2 AA, keyboard, reduced motion, calm mode, pause | 897-903 | Usable for the shell and You | UI-06 T4 part; `e2e/world.spec.ts:193`; VoiceOver is human | — |
| 93 | Graph capped at 100 visible job nodes | 903 | Planned (T8) | VIS1-04 | — |
| 94 | Progress without pressure; one next action; Today card; readiness bands | 911-919 | Planned (T15) | PLAN-01…03 | Celebrations pulled in from M1 (plan line 184) |
| 95 | Select, confirm assumptions, pin a versioned plan, replan | 921-925 | Planned (T15) | PLAN-04…07 | — |
| 96 | Print, JSON, ICS from one snapshot | 927-943 | Planned (T15) | EXP-01…05 | — |

### Sections 16–20 (models, architecture, data, security, acceptance)

| # | Capability | Spec | Status | Evidence | Drift note |
|---|---|---|---|---|---|
| 97 | One pinned Spark model; registry; Standard mode; no escalation | 949-961 | Usable | MODEL-01, MODEL-02 verified | Muse Wonder for human testing is A1 question 4 |
| 98 | Key failure keeps work; manual editing still works | 963 | Usable (editing); printing Planned | MODEL-04 parts (orphaned row) | — |
| 99 | Key storage, consent, rotate, revoke | 965-971 | Usable | MODEL-05, MODEL-07 verified; `KeySetup.tsx` calls store/rotate/revoke | — |
| 100 | Per-run and per-period spend limits; estimate before deep research | 975 | Unreached (limits); Missing (estimate) | `GET /spend`, `PUT /spend/limits` (`api/routes_credentials.py`) have no web caller; no card; only the manual assumes them (`development-plan.md:714`) | Unrecorded |
| 101 | Modular monolith, DBOS, outbox, restricted acquisition worker | 983-1046 | Usable (platform) | ARC1-01…10 verified | WebGL layer added (ADR 0014 d2), decided |
| 102 | 202 + SSE with reconnect; partial results with completeness | 1046 | Usable (SSE); partial results open | DUR-03 (orphaned row) | — |
| 103 | Core records: SolveRun, RouteFamily, Route, PlanVersion | 1070-1073 | Planned (13a, 13b, 15) | — | — |
| 104 | RegionCapability record | 1059 | Missing | no code (grep) | Low in a one-region L0 |
| 105 | Required error codes | 1168-1175 | Usable (backend) | `backend/src/careerwright/errors.py:13-24` | — |
| 106 | Isolation, RLS, invitation checks | 1188 | Usable | SEC-01, SEC-02 verified | — |
| 107 | Data export, correction, deletion | 1190 | Unreached (export); Planned (deletion, T15/T16) | `routes_export.py` `GET /export`; `exportWorkspace` no caller | — |
| 108 | DPIA decision before real people | 1184 | Not run — requires human | H-08 | — |
| 109 | Fixture pack, worked trace, A–I | 1206-1230 | Usable (tests) | TEST1-01…03 verified | — |
| 110 | Five personas end to end | 1210-1214 | Planned (T16) | TEST1-04…08 | P02 has no options by product-owner ruling (ledger line 567, D8) |
| 111 | Real-source corpus 20/10/3 | 1234 | Usable (pack 0.2.0) | OPTN-10, TEST1-09 | Live scoring of course and funding pages (TEST1-13) needs an extractor nobody is building (row 74) |
| 112 | Real-provider smoke with restart and print | 1236 | Planned (T16) | TEST1-11; ADR 0001 replaces "deployed" | — |

---

## 2 The section 3 journey today

| Step (spec lines 143-152) | Can a person do it today? | Evidence |
|---|---|---|
| Sign in, open or create a workspace (demo or live) | Yes | `e2e/access.spec.ts`, `e2e/journey.spec.ts:22` |
| You: say "I know my direction" or "Help me explore" | Yes | REC1-10 |
| You: import a CV or start fresh | Partly: start fresh only; a pasted CV is cut at 2,000 characters | `profile/interview.py:62` |
| You: give the minimum practical inputs | Partly: target, cities, current role, study hours, two caps, salary floor; no income, cash, outgoings, work rights, remote, work mode or level | `profile/document.py:162-199` |
| You: talk; review, edit and undo proposed facts | Yes (live needs a key; demo uses the fixture interviewer) | `e2e/conversation.spec.ts:60` |
| You: get a diverse discovery shortlist with reasons and controls | Yes, under provisional matching rules | capture `you--slate--1440x900.png`; ADR 0007 d13 |
| You: choose one to three targets as hypotheses | Yes | REC1-07; `e2e/keyboard.spec.ts:126` |
| You: see an early, labelled sketch | Yes (behind a disclosure) | STATE-05 |
| Plan section 4: first answer ignites the world; type-ahead; unexpected connection; overlooked strength | No: backend only; the world draws targets and nothing else | `lib/world/model.ts:42-56` (`skills: []`, `openings: 0`); `matchTitles`, `getOrigin`, `submitStrength` have no caller |
| Roles: role cards, company/job map, favourites, exemplars | No | `ChapterView.tsx:36-42`; Task 8 |
| Skills: matrix, evidence prompts, protected gates, apply-now | No | `ChapterView.tsx:43-49`; Task 10 |
| Options: review, pin or exclude, correct costs, funding, confirm budget assumptions | No | `ChapterView.tsx:50-56`; Task 12 |
| Routes: adjust ranges, inspect efficient and dominated routes | No (TRACE-01 fixture preview, fixture workspace only) | `ChapterView.tsx:220-226` |
| Plan: confirm, print or export, record a next action | No | `ChapterView.tsx:57-65`; Task 15 |
| Throughout: set spend limits, see a cost before research | No | row 100 |

The You chapter's completion condition ("minimum practical inputs known; selected targets
confirmed") is partly met: targets yes, minimum inputs only in part. The other five chapters'
completion conditions are not reachable. Even when Tasks 10–15 land as carded, a person whose
target is not one of the pack's four reaches Skills and then finds no options, no routes and no
plan.

---

## 3 Drifts that matter most to a person, ranked

**1. Real options exist only for four pack targets (Drifted-U, high confidence).**
- Found: no live research of courses, apprenticeships or funding; no workspace option catalogue;
  the planning catalogue is the pack (`planning/pack.py:107-112`; `evidence/pages.py:151`;
  migrations r0001–r0032). Task 7's card scope note (`l0-sprint-tasks.md:618`) and plan section 9
  (`development-plan.md:823`) say live research writes the same catalogue as `proposed`; it was
  not delivered, and no ruling, carry-forward or remaining card covers it. Tasks 10 and 12 must
  "score the live path" on course and funding pages (TEST1-13), which needs an extractor that is
  unscoped.
- Why it matters: Options, Routes and Plan, the product's core value ("which achievable route
  makes the best use of my time and money", spec line 17), work only for Data quality analyst, IT
  support technician, Registered nurse and Bookkeeping assistant.
- Recommendation: a product-owner decision, one of:
  (a) **restore the spec, smallest first:** let the person add an option themselves, by pasting
  a course or funding page's text or typing its fields, stored as a `proposed` workspace record
  through the existing pasted-text route (spec 455: "provide manual URL/text import"; GLO-1's
  "user-assisted research" state); then live course and funding extraction through the existing
  fetcher and `page_extraction` pattern. Give it its own task card before Task 12.
  (b) **change the spec for L0:** routes only for reviewed pack targets, and the Options place
  says so in plain words for any other target.
  I recommend (a)'s first half: it is spec-authorised, reuses built parts and turns a dead end
  into a usable path.

**2. The inputs every route needs have no home; several practical constraints have no field
(partly decided, high confidence).**
- Found: baseline income, opening cash, living costs, reserve, commitments, debts, availability,
  delay months and per-variant work patterns: ADR 0013 decision 11 and `carry-forward-task-12.md:3-11`
  give them to Task 12, but Task 12's card (`l0-sprint-tasks.md:940-953`) does not list them.
  Right to work and residence (BND1-04), remote working (BND1-05) and target seniority (row 36)
  have no field and no owner. Spec places these among the minimum inputs (lines 154-163).
- Why it matters: without them no route can be checked for a real person, and an unasked cap
  leaves every route unresolved. Work rights is a hard feasibility gate (spec 751).
- Recommendation: write ADR 0013 decision 11's list into Task 12's card. Collect money and time
  where the person already gives limits (You) or at the checkpoint, but in one place. Give work
  rights, remote and seniority an owner (W2C part 2 or Task 12), or record their deferral in the
  plan's L0 boundary.

**3. Spend limits and the pre-research cost estimate are not on any card (Missing, high).**
- Found: `GET /spend`, `PUT /spend/limits` built and tested (MODEL-08 T3 part), no web caller,
  no card; Task 17's manual assumes "spend limits … and the estimates shown before work starts"
  (`development-plan.md:714`).
- Why it matters: the person pays with their own key (spec 975; press release "clear usage
  controls"). Deep research in Roles (Task 8) starts paid runs.
- Recommendation: restore the spec. Add both to Task 8's card (the first paid research a person
  starts) or to W2C part 2's key panel. Small.

**4. Discovery matching narrowed (Drifted-D, provisional, high).**
- Found: ADR 0007 decision 13 and W2B rulings (ledger lines 682-697): titles resolved, never
  searched; other searches over essential-skill names only; >50-occupation or >5-skill searches
  find nothing alone; one-word work style not searched; DIV-1's 60–120 pool made soft. P01's
  slate was empty offline at one point (ledger line 688); common answers such as "writing
  reports" or "working in a team" find nothing (`carry-forward-task-W2D.md:9`).
- Why it matters: it fixes the product owner's "arbitrary matching on keywords" (session 2,
  `docs/reviews/session-2-answers.md`), but a person with general answers can get a small or empty
  slate, against DIV-1's "full qualified occupation indexes" (261) and REC-1's work-style source
  (245).
- Recommendation: keep it for session W2, where the product owner decides with P01 and P02
  before/after slates (already on the sheet). If kept, record an L0 note in spec DIV-1 and REC-1
  (section 22 style) so the spec and the build agree.

**5. No real pay figures and no AI scores anywhere (Drifted-D, high).**
- Found: modelled pay needs a reviewed UK-SOC mapping and AI scores a reviewed record; L0 has no
  accountable reviewer, so both packs are empty (ADR 0010; H-10). The slate API's AI filter is not
  even sent by the UI (`lib/queries.ts:89-93`).
- Why it matters: the role card and the AI filter, both headline promises, will show "unscored"
  and "no modelled pay" for every real role.
- Recommendation: keep, and say so on the role card. Optionally, the product owner acts as the
  accountable reviewer for the four pack targets' SOC mappings: they already ruled at session 2
  that an AI-checked review counts as theirs (ledger line 572). Their call.

**6. CV paste is missing (Missing, unrecorded, high).**
- Spec 145 and 156 make "paste CV text" the M0 way to start; the chat caps a message at 2,000
  characters (`profile/interview.py:62`). Recommendation: restore with a paste box whose facts
  come back as proposals through the same InterviewTurn contract, or record the deferral.

**7. Role card is thin on the card (Missing parts, medium).**
- Task 8's card lists the map, list and pay lens; the role card itself (spec 309) is only in
  AIR1-13, and hiring signal and outlook labels (311) appear nowhere. Job relevance scoring
  (467) is in the plan's order text only (`development-plan.md:298`). Recommendation: name the
  role card, its "Insufficient evidence / trend history not available" outlook in L0, and the
  "matches your preferences" scoring in Task 8's card.

**8. Supported-region statement missing (Missing, small, high).** BND1-02 orphaned. One plain
line before detailed collection ("Careerwright covers England for now"). Give it to W2C part 2.

**9. Industry colour replaced by glyph and label (Drifted-D).** Keep. Fix register rows VIS1-02,
AIR1-08 and UI-02, which still require colour (register rule: "where a row and the specification
differ, … the row is a defect").

**10. Low-impact omissions (Missing, unrecorded):** session-length modes (237), optional work
samples (546), what-if workspace (195), revision history in the UI (195), run cancellation in the
UI (463), RegionCapability (1059). Recommendation: record them as L0 deferrals in the plan's
boundary table, rather than leaving them silent.

---

## 4 Built but not reachable, and what it takes

| Built (task) | API | What is missing before a person can use it |
|---|---|---|
| Capability model: matrices, questions, readiness, evidence, statements, edits (Task 9) | `/v1/workspaces/{id}/capability/*` (`routes_capability.py`) | Task 10's Skills chapter. Works for any ESCO target, so it is the widest-reaching unreached part. |
| Evidence acquisition: searches, page acquisitions, pasted examples, jobs, favourites, cancel (Task 7) | `/research/*`, `/jobs*`, `/runs/{id}/cancel` | Task 8's Roles chapter, plus a start-research action with a cost estimate (row 100) and cancel (not on Task 8's card). Adzuna is live-qualified, so real listings are possible now. |
| Role evidence: SOC candidates, regional ASHE, AI evidence (Task 7B) | `/occupations/{id}/evidence` | A role card in Task 8 (name it in the card). |
| Planning options and route checker (Task 11) | `/planning/options` (read only) | Task 12: an inputs store and checkpoint; then 13a/13b/14 for routes. Only pack targets have options (drift 1). |
| First moments: type-ahead, origin role, usual skills, connection, overlooked strength (W2B) | `/taxonomy/titles`, `/origin`, `/origin/role`, `/interview/turns/{id}/strength*` | W2C part 2 (already scoped). |
| Spend view and limits (Task 3) | `/spend`, `/spend/limits` | A small panel; on no card (drift 3). |
| Profile version history (Task 5) | `/profile/versions*` | A small history view; on no card. |
| Workspace data export, format 4 (Tasks 3–6b) | `/export` | A button (Task 15 or 16). |
| AI-resilience slate filter (Task 7B) | slate params `min_ai_resilience`, `include_unscored` | Controls in the slate or Task 8's filters; low value while every role is unscored. |
| Provisional concepts for titles outside ESCO (Task 5, DIV1-03) | `/occupations/provisional` | A path from an unmatched title to "keep it as my own title" (W2C part 2's unmatched-title step). |
| Fixture-only demo of a strength (W2B) | `careerwright-fixture-strength-1` | W2C part 2. |

---

## 5 Register findings met along the way

- **28 rows are `planned` or `implemented` with every owner task complete** (computed from the
  Owner column against completed Tasks 1–7d, 9, 11, W1): BND1-02, BND1-04, BND1-05, DIV1-08,
  OUT1-04, OUT1-08, RDY1-02, TEST1-10, STATE-08, PROF-07, PROF-08, ACQ-03, ACQ-07, JOB-01,
  OPTN-04, FRESH-02, PLN-01, PLN-04, PLN-09, MODEL-03, MODEL-04, DUR-03, API-02, API-04, API-05,
  API-06, SEC-05, UI-09. Many have an open UI part a later task will meet; BND1-02, BND1-04,
  BND1-05, FRESH-02 (course and funding ages), PLN-01 and API-05 (stage invariants for a solve)
  have no later owner. Recommendation: reassign each open part to a remaining task or record it.
- **Rows stale against decisions:** VIS1-02, AIR1-08, UI-02 (industry colour, ADR 0014 d5);
  H-13 says "not run — requires human" though session 2 Part 1 holds the product owner's answers
  to the comprehension questions (`docs/reviews/session-2-answers.md:5-17`); the header names plan
  v1.1 as authority (`requirements-register.md:5-6`), the plan is v1.4.
- **No register row** for role-card outlook labels, hiring signal, CV paste, seniority, session
  modes, spend-limit UI or the pre-research estimate (MODEL-08 covers the backend only).

---

## 6 M1 items (out of the L0 boundary unless pulled in)

Not counted as drift: section 2's narrative and FAQ (read as promises above), GLO-1 and the three
contrasting jurisdictions, the research method (326-336), regional adapters such as Skills
England and the apprenticeship API (408-423), the 500-URL qualification (425-433), browser
rendering and PDF acquisition, the reproducible research protocol (505-516), the reference
library (526-530), Muse Wonder escalation and image generation (953, 867-869), the session-only
key, the shared cross-tenant cache, scheduled refresh and AIR-1 monitoring, semantic zoom,
mini-map, halo and organic layout (477-479), the draggable range box (857), tagged PDF and adviser
handoff (939-941), SLOs, SBOM, Terraform, and section 21's business decisions.

**Pulled into L0 by the plan (decided, ADR 0014 and plan section 4):** motion and travel,
staged revelations, celebrations of real progress (spec 915's M1 celebrations,
`development-plan.md:184`), three sound cues (ADR 0014 d8, session W1), and a WebGL renderer
(ADR 0014 d2, against spec 903's "No alternative GPU renderer"). Semantic zoom, the mini-map and
generated illustrations stay deferred (`development-plan.md:59`).

---

## 7 What I could not check

- I did not run the app, the tests or a browser (shared rules). "Usable" rests on code paths, test
  titles and two captures in `apps/web/test-results/` from an earlier acceptance run; I did not
  confirm those captures match f179d0f exactly.
- I trusted the register's Evidence column for "verified" rows; I spot-checked code, not every
  named test.
- Live behaviour (model interview, discovery, Adzuna, page extraction) was not exercised; slate
  sizes for the five personas today are taken from the ledger, not measured.
- I did not read ADRs 0002–0006, 0009 or 0011 in full, nor spec section 23's sources.
- Whether pack 0.2.0's four targets match P01–P05's targets one for one, beyond the ledger's
  "P02 no options", was not checked against `fixtures/m0`.
- Other lenses' coherence, plan-order and Muse Wonder questions are out of scope here.
