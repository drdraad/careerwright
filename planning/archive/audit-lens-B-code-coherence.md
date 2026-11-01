# Audit lens B: code and architecture coherence

- Scope: is the code one clear product? Read-only, at HEAD 8e78060 (branch `l0-local-release`).
- Method: measured lines per module and area (`wc`, `find`); traced the interview, discovery and
  slate, evidence acquisition, capability, planning and the world from route to store or pixel;
  read the ledger and `git log main..HEAD` (294 commits); no tests run (the brief says
  `make check` and `make acceptance` passed on f179d0f).
- Line counts include docstrings and blank lines. Test lines per module are assigned by test
  file name, so they are approximate.

## The answer in brief

1. **The backend core is sound and earns its keep.** One model-run path, versioned and
   idempotent writes, row-level security, pure readiness and planning code, a pinned and cited
   option pack. The earlier review's verdict ("no reason for a broad refactor") still holds
   for the backend.
2. **The product a person can use is one chapter wide.** The web app calls 24 of the 70 API
   operations. Only You (conversation, what we know, suggestions) is built. Skills, Options,
   Roles, export and the W2B first-moment endpoints exist only in the backend.
3. **The chapters after You cover four targets; the front of the journey covers all of ESCO.**
   The option pack and capability reference cover 4 target titles. Any other target a person
   picks from the slate will read "can't be assessed" in Skills and be empty in Options and
   Routes. Building those chapters' world moments on top of that means building for shadow.
4. **The costliest rules protect the least.** Sentence-level truth wording for discovery notes
   (W2B: 5 fix rounds, about 3,750 inserted lines after the first commit) and word-matching
   rules for the slate's search grow like the language lists R11 already fences in. The rules
   that protect people from real harm (support screen, redaction, money, protected gates,
   ownership, secrets) are mostly structural or already frozen.
5. **Today the world shows two facts.** Has the person answered anything, and what are their
   target titles? That costs about 3,000 lines of production code, 1,100 lines of unit tests,
   a hand-mirrored copy in the design references (2,236 lines) and phone and tablet layout. On a
   phone, the design reference puts the first suggestion below the first screen.
6. **Before the next chapters, fix one seam.** A target is a title string, resolved to an
   ESCO occupation in four places with different rules. Store each target's occupation once
   (with a "covered by the pack" flag), then build each chapter's working view (lists, forms,
   numbers) first and its world moment second.

---

## 1. Size and shape

### Backend (`backend/src/careerwright`, 40,758 lines incl. migrations; tests 32,582)

| Module | Lines (files) | Test lines (≈) | What it does for the person today |
|---|---|---|---|
| `profile` | 7,158 (25) | 8,475 | The You chapter: interview turns, what we know, discovery, the slate, the written "why", support screen. **Shown.** |
| `evidence` | 7,140 (22) | 6,583 | Fetching pages and Adzuna, extraction, jobs, freshness. Built the option pack's corpus (via `tools.corpus`). **Not shown** (Roles chapter unbuilt). |
| `api` | 5,825 (31) | in integration | 70 HTTP operations; the web uses 24 (plus the event stream). |
| `catalogue` | 5,188 (16) | 2,409 | ESCO search and titles (**shown via the slate**); option pack loader (feeds Skills and Options, **not shown**); pay, SOC, ASHE, AI evidence and AI resilience (about 2,500 lines; **no L0 data**, see F8). |
| `capability` | 4,606 (13) | 3,033 | Skills matrices, evidence, readiness, questions, overlooked strength. **Not shown.** |
| `identity` | 3,875 (22) | ≈4,850 (platform) | Sign-in, sealed keys, durable runs, spend caps. **Shown** (key setup, run states). |
| `migrations` | 2,959 (33 revisions) | 372 | Schema, 283 CHECK constraints, 101 row-security statements. |
| `planning` | 2,413 (7) | 1,960 | Monthly compiler, ledgers, route checker (pure). **Not shown**; no store for the person's planning inputs yet (`api/routes_planning.py:1-10`). |
| top level | 1,594 | — | Worker, CLI, config, edge relay, restricted acquisition worker. |
| `backend/tools` | 6,353 | 2,250 | Live smoke and eval, corpus, setup, the session 2 generators (1,705 lines). |

Largest backend files: `profile/exploration.py` 1,428 (60 top-level definitions, 29 internal
imports), `evidence/store.py` 1,135, `evidence/acquisition.py` 1,064, `planning/checker.py` 990,
`capability/matrix.py` 907, `catalogue/option_pack.py` 896.

### Web (`apps/web`) and design

| Area | Prod lines | Test lines | What it does for the person |
|---|---|---|---|
| World layer (`World`, `StillWorld`, `WorldControls`, `lib/world/*`) | 2,992 | 1,105 unit + 558 e2e (`world.spec.ts`) + 232 stories | Draws the lit origin and target titles as lights; motion, still version, sound. |
| Chapters and shell (other `components/*`) | 5,207 | 3,211 | You chapter about 2,950 of it (YouChapter, Conversation, Directions, ReviewTray, ProfileEditor, WhatWeKnow, SketchCard, fields, KeySetup); placeholder cards for Roles, Skills, Options and Plan (`ChapterView.tsx:35-63`); fixture route preview (`RoutePreview.tsx`, 337). |
| `lib` (non-world) | 2,923 | 1,526 | Queries (`queries.ts` 632), words (`vocabulary.ts` 720), events, profile forms, auth, config. |
| `app` | 1,957 | — | Routes and `globals.css` (1,796). |
| Stories / e2e | 1,310 / 2,786 | — | Storybook states; Playwright journeys, visual captures, world checks. |
| `src/generated` | 27,403 | — | Generated client (not reviewed). |
| `docs/design/compositions` | 2,364 (`world.js` 1,028, `world.css` 1,208, `data.js` 128) + tools 519 | 44 PNG references | A second, hand-mirrored drawing of the world for all six places (F6). |
| `spikes/world` | 6,250 | — | Session W1's throwaway spike, still in the tree. |

`WorkspaceShell.tsx` is small (234 lines) and clean. It owns the session, queries and events,
and passes `worldFromProfile(profile)` to the world (`WorkspaceShell.tsx:132-135`).

### History

- 294 commits on the branch; 102 are fix rounds.
- Language-rule areas took the most rounds:
  - Task 6, the support screen: 5 rounds plus a follow-up (ledger 150-191).
  - Task 7A, acquisition: 5 rounds.
  - W2B, the slate's search and its notes: 5 rounds (ledger 698-725).
- Sprint W so far (spike, W1, W2A-W2C1): 33 commits and about 32,000 inserted lines, excluding
  images, generated code and lockfiles.
- ADR 0007 is 917 lines after 29 commits; it grew in every W2B fix round.

---

## 2. Findings, ranked by what they cost the product

### F1. The chain after You covers 4 targets; You and the world cover all of ESCO
- **What:** the option pack 0.2.0 and capability reference 0.2.0 each have 4 targets (data
  quality analyst, IT support technician, registered nurse, bookkeeping assistant; 8 rubrics,
  10 learning options). A target finds its pack target by title, or by the pack's ESCO crosswalk
  (`capability/matrix.py:747-768`). Anything else gets only ESCO seed rows, and readiness is
  `insufficient_coverage`, which is never ready (`capability/readiness.py:13-15`). The slate and
  the world offer any of about 3,000 ESCO occupations.
- **Cost:** for nearly any target a live person picks, Skills will say it can't be assessed,
  Options will be empty and Routes impossible. Tasks 10, 12 and 14 would build world moments
  ("a stretch of trail lit by evidence", "a gap's first bridge") that mostly draw shadow. The
  person meets a broad, inviting front and a dead end behind it.
- **Recommendation:** decide this before the next chapter. Either (a) show coverage where the
  choice is made: a "Careerwright can check skills and options for this" mark on slate
  suggestions and targets, computed from the pack; build the next chapters against covered
  targets and say plainly when one isn't. Or (b) plan more pack curation. Option (a) is small
  in code (a flag on the target, see F5).
- **Confidence:** high on the facts; medium on how often live people pick uncovered targets.
  This overlaps the intent lens.

### F2. Today the world shows two facts, and the work bends to fit it
- **What:** the app's world input is `lit` plus the person's target titles. `skills` is always
  `[]` and `openings` always `0` (`lib/world/model.ts:42-55`). Behind those two facts sit:
  - 2,992 production lines and 1,105 unit-test lines;
  - a 558-line e2e spec and a frame-measurement tool;
  - two renderers (WebGL and still SVG), plus the design references' third (F6);
  - per-light labels with leader lines;
  - a 3:1 contrast rule for every trail "as drawn".
- **Evidence that the work bends:**
  - Below 968 px the console is pushed down by `padding-top: max(300px, 34vh)` so the person's
    light stays in view (`app/globals.css:1677-1690`). Plan section 4 says the opposite: "On a
    phone the world is the backdrop behind focused views, with the console and cards in
    sheets" (`docs/plan/development-plan.md:208`).
  - In the phone design reference, the world takes the top half of the screen and the first
    suggestion starts below the first screen
    (`docs/design/screenshots/you--suggestions--390x844.png`).
  - The W2C review treated a hidden light as a defect ("I2 … phone band under MIN_BAND hides
    the person's light", ledger 731). The same review found "'Make this a target' below the fold
    at 1440" (ledger 731). The fix round's own concern: "phone world band ~300 px puts a long
    view's first decision a scroll away" (ledger 741).
  - The Skills reference (`docs/design/screenshots/skills--default--1440x900.png`) draws the
    same four rows twice: once in the panel and once as trail labels.
- **Cost:** the person's first decision moves down the screen. Every chapter carries layout
  work around the light. This runs against the product owner's ruling that the visuals must be
  subservient.
- **Recommendation:**
  - On phones and tablets, return to plan section 4's backdrop-behind-sheets rule.
  - Keep the world as the ambient layer it is (it is cheap to keep).
  - Give it a new state only when a chapter computes one. Build each chapter's working view
    first and its world moment as a later, optional slice.
  - Don't extend frame or contrast measurement per chapter: measure once in Sprint 9 (see F12).
- **Confidence:** high on the facts; medium on the judgment (the product owner scores "feels
  like a world").

### F3. Sentence-level truth wording for the slate's notes costs a lot and protects little
- **What:** the backend writes English notes describing what each search did, for example
  `f"No {_MAIN_NAME} “{answer}”, so it found no work."`, where `_MAIN_NAME` is "main name of a
  skill ESCO lists as essential holds all the words of" (`profile/exploration.py:1000-1083`).
  Ruling (ledger 714): "every note describes what the search did … never what ESCO contains —
  three rounds have found a new case where a claim about ESCO's contents was false".
- **Evidence of cost:**
  - W2B's first commit was 6,654 inserted lines. Its five fix rounds added about 3,750 more
    (e8c0bfb 1,068; 267a83f 907; 392bc64 1,095; b2aa090 310; 166e4ef 375), mostly notes,
    their tests and ADR 0007.
  - W2C part 1 carried more of the same: d3a9164 rewrote three API descriptions and the
    sketch's line.
  - The notes sit behind a disclosure, "How Careerwright searched (n notes)"
    (`Directions.tsx:379-386`).
  - The result is technical wording that the plain-words contract then has to fight.
- **Harm protected:** low. They are notes about search mechanics on a list of ideas to explore,
  and no decision rests on them.
- **Recommendation:**
  - Replace the sentences with structured facts per answer: found work, found none, or not
    searched, plus a reason code.
  - Render them as a small fixed set of plain sentences in `vocabulary.ts`, and test the facts,
    not the words.
  - Until that is done, extend R11 to these notes. A note changes only for a reproduced false
    statement on an evaluation case.
- **Confidence:** high.

### F4. The slate's word search grows exception rules outside R11's fence
- **What:** non-title answers reach work only through "an essential skill whose label holds
  every word" of the search (`exploration.py:1-20`). Rules added since:
  - a one-word work style is never searched (`exploration.py:546-554`);
  - "too general" means more than 50 occupations or more than 5 inexact skills
    (`slate.py:78-82`);
  - the whole phrase must sit in one skill label;
  - only a skill's main name is read;
  - a hyphen is read as a space (92ea74f);
  - common words are left out.
  The slate also has 14 tuning constants (`slate.py:55-82`). Ruling (ledger 698): "reviews keep
  finding new generic-phrase classes".
- **Cost:** each new answer shape brings a new rule, a note (F3) and a review round. Session W2's
  sheet already lists six of these rules for the product owner to judge
  (`l0-sprint-tasks.md:305-313`).
- **Recommendation:**
  - Freeze the rules at session W2 and treat them as R11 lists.
  - A structural option for later: let the person pick ESCO skills by type-ahead, as titles
    already work (W2B's title type-ahead). With "I've used this" on usual skills
    (`capability/usual.py`), the slate joins by skill ID with no word rules, and free-text
    search becomes a secondary channel.
- **Confidence:** medium. The structural option changes ADR 0007 and needs the product owner's
  view.

### F5. A target is a title string, resolved to an occupation in four places
- **What:** the profile stores `target_titles` as strings (`profile/document.py:172`). Each
  consumer re-resolves the occupation:

  | Where | Rule |
  |---|---|
  | `profile/titles.py:53-72` (slate, strength) | chosen if its preferred label matches the title by `casefold`; else every `concept_key_matches` hit (plurals and punctuation folded), several kept as ambiguous |
  | `profile/sketch.py:94-130` | same as titles.py, written again |
  | `capability/commands.py:169-180` + `matrix.py:771-793` (Skills) | chosen keyed by `evidence.jobs.title_key`; else `label_matches` on the exact normalised label; several broken by preferred label; then the pack crosswalk |
  | `profile/exploration.py:1254-1268` (choose target) | `casefold` comparison |

  Parked in the ledger as "M8 three chosen-occupation normalisations -> final review"
  (ledger 681). In the web, `lib/world/model.ts:48-50` keys destinations as
  `target:${title}`. The backend strength's "destinations" (targets plus the first slate) are a
  different set from the web world's (targets only) (`capability/strengths.py:14-16`;
  `l0-sprint-tasks.md:291-292`).
- **Cost:** You, Skills and the world can disagree about the same target. For example, a plural
  or punctuated title resolves in You but gets "no exact label" in Skills. Each new chapter
  (Roles, Options, Routes, Plan) would add a fifth resolver.
- **Recommendation:** resolve once, when a target is chosen or saved. Store its ESCO concept ID
  (and pack coverage, F1) with the target. Every module calls one `resolve_target`. Do this
  before Skills.
- **Confidence:** high that the rules differ; medium on how often people would see it.

### F6. The design references are a hand-mirrored second implementation of the world
- **What:** `docs/design/compositions/world.js` (1,028) and `world.css` (1,208) redraw all six
  places in SVG. Their geometry "mirrors apps/web/src/lib/world/geometry.ts" by hand
  (`world.js:58`).
- **Evidence of cost:**
  - Every W2 slice changed both: d989d15, 8b0cdf9, 70d95e6, 5c14792, c798ea4. W2C part 1
    alone added 581 reference lines.
  - The W2C design review: "I1 duplicate .facts rule breaks What we know reference + regresses
    7 Routes/Plan captures" (ledger 731).
- **Recommendation:** once a place is built, the app's own Storybook stories with fixture data
  become its reference. Delete each place from `world.js` when its chapter lands. Keep the
  static references only for places not yet built.
- **Confidence:** high.

### F7. Words a person reads are written in three layers
- **What:** English is composed in the domain (`exploration.py` notes and explanations,
  including English article and plural rules at `exploration.py:596-618`), in API schemas
  (`api/discovery_schemas.py:381`, a summary sentence), and in the web (`lib/vocabulary.ts`, 720
  lines). CLAUDE.md's "words from vocabulary.ts" rule covers error codes only.
- **Mitigating fact:** capability and planning return enums and numbers, with no prose; capitalised
  sentence f-strings sit almost all in `profile/`. So this is confined to discovery today.
- **Cost:** a plain-language fix crosses Python, the OpenAPI text, TypeScript and both test
  suites (d3a9164 touched 10 files for three lines).
- **Recommendation:** fold this into F3's change. Keep every new chapter's API prose-free:
  codes and numbers out, words in `vocabulary.ts`, with exhaustive `Record<Enum, …>` maps so a
  new code fails the type check.
- **Confidence:** high.

### F8. Built, but nothing to show in L0
- **What:**
  - The web calls 24 of 70 generated operations. Unused: all capability, planning, research,
    jobs, export, origin and strength operations.
  - The pay and AI stack has no L0 data. `catalogue/packs/uk_soc_mapping_reviews.json:4` has
    `"reviews": []`, so modelled pay never exists. `catalogue/packs/ai_resilience.json:6` has
    `"records": []`, so every role is unscored. About 2,500 lines (`pay.py`, `ashe.py`, `soc.py`,
    `reference.py`, `reference_store.py`, `ai_resilience.py`, `ai_evidence.py`, `xlsx.py`), every
    fetched dataset except ESCO (ASHE, the SOC index, ILO, O*NET, Anthropic usage, the
    crosswalk; `catalogue/reference.py:48-79`), their migrations and tests produce only
    "unavailable" or "unscored" on screen. The occupation-evidence endpoint that would show SOC
    candidates and exposure is not called by the web.
- **Cost:** the backend-first order (plan v1.1) explains most of this, and it is not a defect.
  But plan item S3.5 still asks the Roles chapter for "numeric salary and AI-range filters, pay
  lanes" (`development-plan.md:428`), and every one of those values is unknown in L0.
- **Recommendation:** leave the code and record it. For L0, cut the salary and AI-range filters
  and pay lanes from Roles. Show one plain line ("Pay and AI evidence aren't reviewed for this
  release").
- **Confidence:** high on the facts; the cut is the product owner's decision.

### F9. Options (Task 12) is not just a screen
- **What:** the planning API is read-only. "What has no store yet is every input the person
  supplies (ADR 0013 decision 11): the baseline, … opening cash, living costs, the reserve,
  the three hard limits and the deficit cap, weekly availability, commitments, existing debts …"
  (`api/routes_planning.py:1-10`).
- **Cost:** Task 12 hides a backend slice: a store, commands, versions and migrations for about
  15 inputs. Without it Routes (Task 14) has no input.
- **Recommendation:** split Task 12 into a backend slice (planning inputs: store and commands)
  and the Options chapter. Size it as such.
- **Confidence:** high.

### F10. Scale machinery planned for the solver may be more than L0 needs
- **What:** Task 13b asks for a disk-backed archive with atomic checkpoints and resume, a
  cancellable solver child process under DBOS, and a 50,000-point ranking benchmark
  (`l0-sprint-tasks.md:983-999`). L0 solves over 4 targets and 10 learning options, with at
  most 6 actions.
- **Cost:** several engineering days of durability for searches that may finish in-process in
  seconds.
- **Recommendation:** make 13b depend on 13a's measured sizes. If every pack-scale instance
  completes within the 30 s cap, keep the caps and the honest truncation wording, and move the
  durable archive and child process to M1.
- **Confidence:** medium. It depends on 13a's measurements.

### F11. `exploration.py` holds six use cases in 1,428 lines
- **What:** one module covers starting a discovery, the slate with hard filters and notes, the
  written explanation, choosing a target, choosing a role and the first slate. It imports from
  29 internal modules, and its 30-line opening docstring is a single sentence
  (`exploration.py:1-33`).
- **Recommendation:** split it as a side effect of F3 (notes leave) and F5 (target resolution
  leaves), not as a refactor of its own.
- **Confidence:** medium.

### F12. Throwaway work kept, and polish aimed at things being replaced
- **What:**
  - `spikes/world` (6,250 lines). Plan section 4 calls the spike "throwaway".
  - The session 2 generators (`tools/session_2_pack.py` 901, `tools/session_2_files.py` 804,
    tests 617), after session 2 and Task 7c have closed.
  - W2D still lists plain phrases for the fixture route preview (`l0-sprint-tasks.md:299-300`),
    which Task 14 replaces.
  - World accessibility and measurement rules applied to atmosphere: 3:1 contrast for every
    trail as drawn, and frame budgets on a 100-job scene the app cannot produce yet (ADR 0014
    decision 7).
  - 168 task, fix-round and re-review references in backend docstrings and comments, and 31
    session or fix-round references in web components. For example, `exploration.py:971-975`
    and `1036-1040` cite "re-review 2, N-I1; re-review 4, I1".
- **Recommendation:**
  - Delete the spike after session W2.
  - Leave the session 2 tools (CLAUDE.md names them, and a pack re-review may need them), but
    don't extend them.
  - Drop the route-preview wording item.
  - Hold the world at today's bar and measure once in Sprint 9.
  - Keep the "why" in comments and drop review IDs as files are next touched.
- **Confidence:** high.

### F13 (low). Every status event refetches everything
- **What:** every status event invalidates every workspace query (`lib/queries.ts:546-558`).
  The slate is recomputed on each read (`exploration.py:739-747`), and matrices and readiness are
  computed on each read ("nothing derived is stored", `capability/commands.py:5-9`).
- **Cost:** none today. As chapters accumulate, one capability write will refetch the slate and
  every matrix.
- **Recommendation:** leave it. Split `queries.ts` per chapter when Skills lands; narrow the
  invalidation only if it measurably lags.
- **Confidence:** medium.

---

## 3. Honesty invariants: how each is enforced, and is it in proportion?

S = structural (types, database constraint, one code path, generated contract).
L = a list or pattern set that grows with exceptions. W = a sentence-level wording rule checked
in review.

| Invariant (CLAUDE.md) | How enforced | Harm it prevents | Cost to keep true | Verdict |
|---|---|---|---|---|
| Model proposes; one validated command commits, against an expected version | S: one command path, `run_idempotent`, versions (`profile/commands.py`) | Model silently changing a profile | Low | Keep |
| One model-run path; access, key and budget re-checked per run | S: `RunTask` per kind (`worker.py:53-61`), one activity | Spend, key misuse | Low; strength was added without changing the DBOS steps | Keep |
| Money in minor units; unknown money is null | S: `Money`/`SignedMoney` (`money.py`) | Wrong sums, £0 read as known | Low | Keep |
| Ownership by row security | S: 101 policy statements; `actor_transaction` / `run_transaction` | Data leak across workspaces | Low | Keep |
| Test model takes synthetic data only | S: code and a database CHECK (`r0002`) | Real data reaching a training-eligible model | Low | Keep |
| Fetch only through the guarded fetcher; class from the manifest; https apply links | S: one path plus the boundary test (`test_boundaries.py:47-90`) | Request forgery, robots and rights breaches | Low | Keep |
| Failure is never empty success; unknown is never zero; truncated is never "no route" | S: enums (`WorkState`, `FieldState`, coverage) | False "nothing found" | Low | Keep |
| Protected gates never demoted; nothing finds a person ineligible; unknown is never level 0 | S: pure checks in `capability/readiness.py`, `PROTECTED_GATE` | Telling someone a legal requirement is optional | Low | Keep |
| Option pack versions immutable; every field cites a span | S: pins, hashes, schema, `load_pack` | Unsourced course and fee facts | Low after 7c | Keep |
| Lock order | S: one documented order plus a concurrency test | Deadlocked cancel | Low | Keep |
| UI takes enums, money and errors from the generated client | S: drift check plus exhaustive maps | Drift between API and screen | Low | Keep |
| Support panel on any risk word | L: `profile/safety.py` (505 lines, `support-policy-7`, `safety.py:42`) | Missing acute distress | High once (Task 6: 5 rounds); now accepted at session 1 and frozen | Keep, frozen |
| Model output may not infer health, type or percentage | L: health, type, demographic, MBTI and percent lists (`safety.py:373-459`) | Inferring protected characteristics | Moderate | Keep, frozen |
| Third parties' contact details removed | L: `evidence/redaction.py` (216) | A privacy breach | Moderate | Keep, frozen (R11 already) |
| Written "why" makes no readiness, pay or hiring claim | S: span check (exact; keep) plus L: about 70 terms and 7 patterns (`slate_explanation.py:209-315`) | A model implying a job or pay | Moderate | Keep the span check; freeze the list |
| Extraction approves only values read from verified spans | S: span check plus L: pay, date and work-mode regexes (`evidence/extraction.py:245-430`) | A wrong fee or salary marked verified | Moderate; Roles doesn't feed the chain in L0 | Keep, frozen; don't extend for L0 |
| Agency told apart from employer | L: `AGENCY_MARKERS` (`evidence/jobs.py:33`) | A misnamed employer | Low | Keep |
| Discovery notes say what the search did, never what ESCO contains | W: per sentence (`exploration.py:910-1083`); ruling at ledger 714 | Low (search mechanics behind a disclosure) | **High** (W2B rounds 1-5, W2C carry-over) | **Simplify** (F3) |
| Slate search rules (one-word style, too general, main name, hyphen) | L: new, outside R11 | Arbitrary suggestions (quality, not safety) | **High** | **Freeze at session W2**; structural option (F4) |
| Article and plural grammar for ESCO titles | L: regexes (`exploration.py:596-618`) | None (cosmetic) | Low but pointless | Simplify: templates that need no article |
| Every trail at 3:1 contrast as drawn; every light named beside it | W/L: measured per scene (ADR 0014 decision 7) | Readability of atmosphere; the DOM list already carries every word | Moderate (W2A's two rounds) | Hold at today's level (F12) |
| Revelations only from deterministic sources or verified spans | S: verifier reused (`capability/strength.py` imports `slate_explanation.accepted_quotation`) | A model deciding an insight | Low | Keep |

The pattern: invariants enforced by types, the database or one code path cost little and
protect a lot. The expensive ones are word lists and sentence rules. Of those, the support
screen, inference lists and redaction protect people from real harm, and R11 already freezes
them. The discovery notes and slate search rules are the live cost centre, and they protect the
least.

---

## 4. Does the world serve the work?

| Question | Finding |
|---|---|
| What does the world show from real data today? | Two facts: answered or not, and target titles (`model.ts:42-55`). Skills, openings, gates and routes arrive "with the chapters that compute them". |
| Does it hold anything unique? | No. Every light has its words in the DOM ("canvas holds nothing unique"). The Skills reference draws its four rows twice. |
| Is its architecture sound? | Yes: one `Scene` (`lib/world/scene.ts`) feeds both renderers, so the still version and accessibility come for free once a state exists. Keep. |
| Does the work bend to it? | Yes, on phone and tablet (F2): a 300 px+ band for the light, the first decision below the screen, a review defect raised for a hidden light. That contradicts plan section 4's backdrop rule. |
| Does it cost each chapter? | Yes. A new chapter touches `model.ts`, `geometry.ts`, `gl.ts`, `StillWorld.tsx`, `labels.ts`, `palette.ts`, tokens and contrast pairs, `world.js`/`world.css`, references, `world.spec.ts` and the frame measurement. That is about 10 touch points, against about 5 for the chapter's working view. |

Judgment: the world is a well-built atmosphere carrying little meaning so far. It earns its
place only when a chapter computes something the world can show at a glance better than a list
can: several destinations, which skills they share, and which gates block them. Until then it
should cost each chapter nothing and never push a decision down the screen.

---

## 5. Keep list: complexity that earns its keep

| Keep | Why |
|---|---|
| One model-run activity, one `RunTask` per kind (`identity/activity.py`, `worker.py:53-61`) | A new model-backed feature is a task, not a new call path; access, key and budget are checked in one place. |
| `run_idempotent` plus expected version on every write (`api/routes_capability.py:113-205`) | Routes stay thin and uniform; double clicks and retries are harmless. |
| Row security plus `actor_transaction` / `run_transaction` | Ownership is enforced by the database, not by remembering. |
| 283 CHECK constraints | Invalid states can't be stored, whatever the code does. |
| Architecture boundary test (`tests/architecture/test_boundaries.py`) | Vendor and SQL imports stay in listed adapters; no import cycles. |
| Generated client, drift check and exhaustive `vocabulary.ts` maps | An API change breaks the build, not the person's screen. |
| `Money` / `SignedMoney` (33 lines) | Small type, large protection. |
| Pure `capability/readiness.py` and `planning/checker.py` | The chain's core rules, testable without a database; property tests. |
| Option pack format (immutable versions, pins, claims with spans) | The evidence base every later chapter stands on. |
| Guarded fetcher plus restricted acquisition worker | A real security boundary; one path. |
| Support screen and redaction (frozen) | Real harm; accepted by the product owner. |
| One span verifier reused for the "why" and the strength | Every model quotation is checked the same way. |
| One `Scene`, two renderers, DOM list | Stillness and accessibility come free once a state exists. |
| Fixture models through the same task and validation | The demo runs offline through the real path. |
| Whole-workspace refresh on any event (`queries.ts:546-558`) | Every chapter is fresh without wiring. |
| `WorkspaceShell.tsx` (234 lines) | A small, clear shell; not the problem the brief suspected. |

---

## 6. Cost of the remaining chapters on the current shape

| Chapter | Backend today | Still to build | Extra cost from the current shape |
|---|---|---|---|
| Skills (Task 10) | Done: matrices, questions, readiness, three commands (`routes_capability.py`) | Chapter UI, question flow, chat proposals through the same contract, live scoring | F1: uncovered targets show "can't be assessed". F5: a fifth title resolver. World: new states (evidenced, self-reported, planned, unresolved, gate) in the Scene, both renderers and the references (F6). |
| Options (Task 12) | Read-only options (`routes_planning.py`) | **A planning-inputs store and commands** (F9), the checkpoint UI, live scoring | F1, F5, F6. The checkpoint's inputs are the biggest hidden backend piece left. |
| Roles (Task 8) | Research, jobs, sources, occupation evidence | Map and list UI, job scoring | F8: pay and AI filters have no L0 data. F6. |
| Routes (Task 14) | Checker only | Solver (13a; 13b, see F10), archive, comparison UI | F10: possible over-build in 13b. F1: routes exist only for covered targets. |
| Plan (Task 15) | Export endpoint, partly | Snapshots, progress, revision, print | Low; depends on Routes. |

**Yardstick:** W2C part 1 (the You chapter rebuilt in the world, 166e4ef..f179d0f) took:
- about 1,670 component lines, 580 reference lines, 460 e2e lines and 230 CSS lines;
- two review halves, eight Important findings and one fix round;
- an implementer context of about 762k tokens (ledger 738), which made the controller split
  W2C (ledger 726).

Expect about that per chapter, plus the backend gaps above.

**Smallest changes that lower the cost, in order:**
1. **Store each target's ESCO occupation, with a pack-coverage flag, and one resolver** (F5, F1).
   It is one migration and one function; every later chapter keys on the concept ID, and the
   person sees coverage before choosing.
2. **Decide the coverage story for L0** (F1): covered targets only for Skills, Options and Routes,
   said plainly, or more curation. This is the product owner's call.
3. **Working view first, world moment second, in every chapter.** A chapter is done when its
   DOM view works. The world moment is a later slice, only where a computed state supports it.
   On phones and tablets the world is the backdrop (F2).
4. **Extend the Scene's states once** for every remaining computed state (evidenced,
   self-reported, planned, unresolved, gate, ready, ready if, not feasible), with tokens and
   contrast pairs, in one slice. After that a chapter only maps API values to states.
5. **Make the app's Storybook the reference for built places**; retire `world.js` places as
   chapters land (F6).
6. **Keep new APIs prose-free** (F7), and freeze the discovery notes and search rules at session
   W2 (F3, F4), so the Skills and W2C part 2 reviews don't reopen them.
7. **Split Task 12** (planning-inputs backend, then UI) (F9), and **gate Task 13b on 13a's
   measurements** (F10).
8. Cut L0's Roles pay and AI filters (F8). Delete the spike after session W2 (F12).

---

## 7. What I could not check

- I ran nothing: no tests, app or stack. Pass counts come from the brief.
- I saw no capture of the world in the running app. The committed app captures predate Sprint
  W (`docs/reviews/sprint-2/screenshots`, 28-29 October). The phone-layout evidence is the CSS
  rule plus the design references, which the app follows.
- I did not measure how often live people pick targets outside the 4 covered ones (F1), or
  whether 13a's instances complete in-process (F10).
- I did not read the specification in full. Requirement fit is another lens's job, so where a
  recommendation cuts scope (F8, F10) it needs the product owner and the intent lens.
- Test-line attribution per module is by file name and approximate. Docstring and comment
  share was measured only roughly (about 10% of backend lines).
- I did not check `src/generated`, `src/design` or `fixtures/m0` line by line (generated or
  pinned).
