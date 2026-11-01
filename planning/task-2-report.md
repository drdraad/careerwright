# Task 2 report: Sprint 0, fixtures, registers and design references (S0.5–S0.6) and the Sprint 0 review

Status: **DONE_WITH_CONCERNS**. Every deliverable is implemented and machine-verified. The
concerns are human-only gates (R2), which are open by design, and one evidence error I
made and corrected inside the task (hand check §8, see "Concerns").

Commits on `l0-local-release` (base `2bb36e5`):

| SHA | Subject |
|---|---|
| `e925c57` | Place the M0 fixture pack and hand-check TRACE-01, A-I and personas |
| `a5045a4` | Scaffold the real-source corpus manifest with owners and dispositions |
| `44298a1` | Add the canonical requirement-to-test register |
| `f5b73d1` | Correct DIRECTAI dominator lists in the fixture hand check |
| `f2e55fa` | Add Sprint 0 design references: tokens, fonts and three compositions |
| `943663c` | Add the repository CLAUDE.md from the starter kit |
| `2903e0e` | Record the Sprint 0 review and close Task 2 register rows |
| `d1bd23a` | Point the Sprint 0 review at committed carry-forward sources |
| `fd76820` | State which work areas the map composition adds beyond P01 |

## What I implemented

### S0.5 Fixtures and the independent hand check

- **`fixtures/m0/`**: the supplied `Nessa_M0_Fixtures.zip`, extracted unchanged. Every file
  is byte-identical to the archive member. Its SHA-256 is recorded in
  `fixtures/README.md`, and a git blob check confirms the committed bytes match.
- **`fixtures/reconstructed/directai.json`**: the A–I direct-spend fixture, which the pack
  does not contain. It is rebuilt from spec §12 and §20 (R1) and marked
  `"reconstructed": true`. It uses `fixture:directai:route:*` IDs and holds only what the
  specification states (months, direct cost, layer). Schedules, dates and ledgers are
  listed as not specified rather than invented.
- **`docs/evidence/fixture-hand-check.md`** covers:
  - P01 against TRACE-01 against spec §20 inputs.
  - Every route's direct, loss and economic arithmetic.
  - Full monthly prefunding ledgers (B: £4,850 in January; A: £1,800 in March).
  - Date and TIME-1 consistency.
  - Dominance tables for TRACE-01 and A–I.
  - OUT-1 span and hash.
  - The AI range.
  - Every plan §8 counterexample.
  - All five persona expectations.
  - Nine findings (H1–H9) that later tests must encode.

  The most consequential findings:
  - H1: P03's option breaks two hard constraints, the reserve as well as the payment cap.
  - H2: P02 has `current_net_income_minor: 0` next to an unconfirmed baseline.
  - H5: £4,850 depends on late-month wages, an assumption the JSON does not state.
- `docs/evidence/sprint-0-spike.md`: the TRACE-01 exit-evidence row now points to the
  hand check.

### S0.6 Source-corpus manifest

- **`corpus/manifest.json`** is derived from the pack manifest (hash recorded). It has 20
  job, 10 course and 3 funding slots plus 2 failure-only attempt cases. Every required
  case type maps to a slot, checked by script. The rights default is "pending human
  rights review", the split is "unassigned" until tuning, and `open_items` OI-01 to OI-11
  each name an owner and a disposition. The human ones (rights, label review) are "not
  run - requires human".
- **`corpus/README.md`**: the R3 split between git and private storage, how to fill a slot,
  and the human rights-review checklist.

### S0.6 Requirement-to-test register

**`docs/requirements-register.md`** holds 330 stable IDs.

What it covers:
- All 16 `[M0, XXX-1]` IDs, split into atomic rows.
- All 14 plan §8 regression families, with independent expected values.
- Plan §8 generated properties.
- Register anchors for the untagged M0 sections: STATE, PROF, ACQ, JOB, ASSESS, OPTN,
  FRESH, PLAN, EXP, MODEL, DUR, API, SEC and UI.
- A spec §20 non-deferrable-check map.
- 10 human gates.
- An "L0 does not test" table (GLO-1, hosted M0 and M1 items).

How it works:
- Each row has a layer, an owning task (T1–T16) and a status from a fixed vocabulary.
- A script checked for duplicate IDs, invalid statuses, and spec IDs or families missing.

Current counts: 305 planned, 10 verified, 5 spike-verified, 10 not run (human).

### S0.6 Design references (`docs/design/`, frontend-design skill used)

**Tokens.** `tokens/tokens.css` defines primitives, semantic tokens and the `.on-space` /
`.on-reading` contexts, plus type, space, radius and motion. The spec's starting values
are kept.
- `tools/contrast.mjs` measures every pairing in `tokens/contrast-pairs.json` and writes
  `tokens/contrast-report.md`. **64 of 64 pass.** The maths was sanity-checked against
  known ratios (21:1, 4.48:1, 4.54:1, 8.59:1).
- It caught one failure on the first run (light control border at 2.95:1), which I
  fixed.
- Composited colours were checked separately. Lens bars dimmed to 60% failed at 2.97:1,
  so they are now 75%.
- Spec sea-glass `#5DE0C1` measures only 1.62:1 on white. The light variant is
  `#0A7360` (5.77:1).

**Fonts.** Source Sans 3 (body; humanist; tabular figures by default, measured) and
Newsreader (display). They are unmodified upstream TTFs from `google/fonts` at pinned
commits, with OFL texts beside them, and the provenance and hashes are in
`fonts/README.md`. A `.gitattributes` keeps vendored files byte-exact, because the global
`core.autocrlf=input` had normalised the Source Sans licence.

**Compositions.** Three static HTML, CSS and SVG pages, each in `default`, `unknown` and
`failure` states (`?state=`). Each has a desktop layout and a phone layout with a bottom
sheet:
- **You.** P01: review tray, a dashed inference, a hard limit needing confirmation, and
  an evidence drawer quoting the exact span. P02 unknown state: "Not confirmed, not £0".
  Failure state: `SCHEMA_INVALID`, profile unchanged.
- **Roles.** Deterministic dendrite with open-circle area anchors. The selected role card
  shows the AI range 5–8 and the min-6 filter from TRACE-01, and benchmark and trend as
  unavailable. Also a pay and location lens and the full list. The listings are invented
  and labelled synthetic, because the pack has no jobs. Unknown state: sparse,
  pay not stated, snippet-only listings, "none found". Failure state: one source failed,
  with its listings kept and shown as stale.
- **Routes.** TRACE-01 economic chart: discrete points, a labelled comparison boundary, a
  shaded bettered region, and greedy collision-free labels. Cards lead with concrete
  margins under one declared comparator rule (cheapest dominator). Route B's journey:
  Gantt with actual dates, parallel bands, payments, gate, and "ready from 1 May 2027"
  conditional. Its monthly ledger is recomputed in the browser and matches the hand
  check. Unknown state: DIRECTAI in explicit direct-spending mode. Failure state: search
  failed, with version 14 kept and marked stale.

**Fixture fidelity.** All numbers in prose bind to `compositions/data.js`.
`tools/check-fixture-data.mjs` asserts 59 values against `fixtures/`; mutations of 3
values each failed it. The route page re-peels the layers and recomputes the ledger, and
any mismatch is a console error, which fails the screenshot run.

**Screenshots.** `tools/screenshots.mjs` serves the pages on a 127.0.0.1 ephemeral port
and captures 18 PNGs (3 compositions × 3 states × 1440×900 and 390×844). Per capture it
runs:
- axe-core 4.14.0 (WCAG 2.0, 2.1 and 2.2 A/AA);
- a horizontal-overflow check;
- a console-error check;
- a font-loading check;
- a new chart label-collision check.

**18 of 18 pass.** axe caught two real issues during iteration (label in name, a
scrollable region that keyboards could not reach), and both were fixed.

**Iteration.** I read the PNGs and full-page renders back and fixed about 20 visual and
structural defects. They are listed in `pre-review-sprint-0.md`.

**Review files.**
- `pre-review-sprint-0.md`: "Agent pre-review — not the required human review", with no
  scores, plus the human checklist.
- `README.md`: the rules implementations must keep, and what is not covered, with owners.
- Tooling: `package.json` and `pnpm-lock.yaml` (dev-only: `playwright` 1.64.1 and
  `axe-core` 4.14.0), also recorded in `docs/dependencies.md`.

### Repository `CLAUDE.md`

Adapted from the starter-kit template:
- Real commands for setup, fast checks, the full integration suite, the design tooling
  and capped live calls. "TODO(Task 3)" markers appear only where make targets will
  replace them.
- Facts that change implementation decisions.
- The kit's scope, correctness and completion sections, plus the R2 rule.

### Sprint 0 review

**`docs/reviews/sprint-0.md`** follows plan §10:
- Exit evidence and S0.1–S0.6, each passed, done or not run.
- Checks run on the final candidate.
- The six questions.
- The card's coherence question, answered as partly established: the durable run is
  shown, but there is no command or version layer until Task 3 and Task 5.
- Visual findings.
- Limitations with owners.
- The H-02 checklist.

## Rulings (and why)

1. **Original pack kept pristine; A–I fixture placed outside it** (`fixtures/reconstructed/`).
   The brief said to place the pack under `fixtures/m0/`, and mixing a reconstructed file
   in would break the byte-identity claim. Cost if wrong: one file move.
2. **The A–I fixture contains only spec values.** Inventing schedules would make a
   fixture fill data the source never gave (GC5). Cost if wrong: Task 13 adds schedules
   with a ruling.
3. **Corpus manifest at `corpus/manifest.json`; private bodies at `var/evidence/corpus/`**
   (already gitignored through `/var/`), with Task 3 to confirm. No path existed yet.
   Cost if wrong: a rename.
4. **Failure-only attempts (dead URL, blocked fetch) do not count toward the 20/10/3 page
   minimums.** They hold no page content to label.
5. **Register anchors for untagged M0 sections** (`STATE-`, `SEC-` and the others), labelled
   as register labels, not spec IDs. The brief asked for every spec ID, but §§3, 11 and
   16–19 hold consequential requirements without IDs. Without anchors those would have
   no test owner.
6. **Proposed test tagging: `@pytest.mark.req("<ID>")` and a `[<ID>]` title prefix.**
   Task 3 must register the marker under `--strict-markers`. This is a proposal, not
   implemented.
7. **A `spike-verified` status.** Task 1 evidence comes from spike code; marking it
   `verified` would overclaim for the product.
8. **Design tooling in Node and pnpm under `docs/design`, with its own lockfile and a
   loopback HTTP server.** `file://` blocked axe's stylesheet reads. axe-core was added,
   because the R2 automatable part names axe.
9. **Fonts kept as unmodified TTFs, not converted to WOFF2.** Source Sans 3 carries the
   Reserved Font Name "Source"; converting or subsetting would create a modified
   version. Task 4 can use upstream WOFF2 builds.
10. **The map listings are invented and labelled synthetic.** The pack has no jobs, and
    the spec numbers that exist (target, city, AI range and filter, null benchmark and
    trend) are used and checked. The default state adds Leeds and remote to show three
    areas; this is stated in the README.
11. **The route comparison's unknown state uses DIRECTAI in direct-spending mode.** It
    demonstrates both the missing-baseline path (FIN-1, P02) and the DIRECTAI labels
    without pairing P02 with P01's trace.
12. **Comparator rule shown: cheapest dominator, ties to shorter time then ID, others
    listed.** Spec §13 requires a declared deterministic rule; Sprint 7 may replace it.
13. **Status glyphs drawn for the reference** (simple SVG paths, no third-party licence).
    Task 4 picks the licensed icon set.
14. **`.gitattributes`** marks `fixtures/m0/**` and `docs/design/fonts/**` as `-text`, so
    git keeps vendored bytes exact under the user's global `core.autocrlf=input`.

## Tests and checks (exact commands, final tree `fd76820`)

No domain logic was written in this task, so there was no TDD cycle. For the tools and
checks I did write, the RED evidence is that each check rejects known-bad input:

| Command | Result |
|---|---|
| `cd backend && uv run --locked python -I ../fixtures/m0/validate_fixtures.py` | `"status": "passed"` (also host `python3 -I`, 3.14.6: exit 0) |
| Scratch mutation run: 9 single-value mutations of copies of the pack | all 9 rejected (exit 1, `AssertionError`) |
| Scratch independent ledger and front recomputation | matched every hand figure; DIRECTAI and TRACE-01 dominator sets rechecked mechanically after the correction |
| `shasum -a 256` of the syllabus bytes | `96a22436…c783fb`, matching `source_hash` |
| Register lint (scratch script) | 330 IDs, no duplicates, statuses valid, 16/16 spec IDs, 14/14 families |
| Corpus coverage (scratch script) | every required and additional case type covered; pack labels and sources preserved |
| `cd backend && uv sync --locked` | Audited 54 packages |
| `uv run --locked ruff format --check .` | 29 files already formatted |
| `uv run --locked ruff check .` | All checks passed |
| `uv run --locked mypy` | no issues in 29 source files |
| `uv run --locked pytest` | 63 passed, 12 deselected |
| `uv run --locked pytest -m integration spikes/durable` (Docker, PostgreSQL 16.15) | 12 passed in 31.87 s |
| `cd docs/design && pnpm install --frozen-lockfile` | up to date |
| `pnpm run contrast` | 64/64 pairs pass (the first run failed 1 pair, now fixed) |
| `pnpm run check-data` | 59 assertions pass; 3 mutations each exit 1 |
| `pnpm run screenshots` | 18/18 captures pass; re-running produced byte-identical PNGs |
| Secret scan of `git diff 2bb36e5..HEAD` against 12-character fragments of the `.env` key (value never printed) | no fragment found |

## Live calls (R5)

**None.** No Meta call was made in Task 2: $0.00. The ledger is unchanged at 11 calls,
about $0.0197.

## Blocked, not run, or limited

- **Not run — requires human (R2):**
  - H-02: approval of the compositions. A checklist is in `docs/reviews/sprint-0.md` and
    `docs/design/pre-review-sprint-0.md`.
  - H-07: domain-reviewer sign-off on the hand check.
  - H-09: ADR 0003, the Contributor test model.
  - Later gates: H-06 (rights) and H-08 (DPIA).
- **Corpus pages:** 0 of 33 collected, by design (Tasks 8, 10, 12).
- **Design references do not cover:**
  - the 768×1024 tablet layout;
  - the phone's focused chart view and map overview (entry points only);
  - the sheet's peek height;
  - keyboard flows and focus return (axe is not a keyboard test);
  - WebKit and Safari (Chromium only);
  - motion (static references).

  Owners: Tasks 4, 8 and 14, and the humans.
- **amd64:** not executed (as in Task 1).
- **No application UI exists yet.** Sprint 0 review question 1 is "not run (no UI yet)".

## Concerns

1. **Evidence error, found and corrected in-task.** The first committed hand check
   (`e925c57`) gave incomplete dominator lists for DIRECTAI G (missing B) and H (missing
   C), and wrongly said G is faster than B. The layers were correct. The route
   composition exposed it: its comparator named B for G. The fix is in `f5b73d1`, with a
   correction note in the document, and every dominator set is now checked mechanically.
   A reviewer should give the hand check's other tables the same scrutiny.
2. The register is large: 330 rows of paraphrase. I checked it mechanically for structure
   (IDs, statuses, coverage), not row by row against the specification's wording. A
   reviewer spot-check of the paraphrases is worthwhile.
3. The compositions' map layout uses fixed angles that were checked only for this data
   set. A real map needs measured label placement (Task 8). The README says so.

## Paths a reviewer can skip

- Vendored and generated:
  - `fixtures/m0/**` (supplied pack, byte-identical);
  - `docs/design/pnpm-lock.yaml`;
  - `docs/design/fonts/**/*.ttf` and the `OFL.txt` files;
  - `docs/design/screenshots/*.png` (look at a few);
  - `docs/design/tokens/contrast-report.md` and `docs/design/screenshots/checks.md`
    (generated).
- `docs/design/node_modules/` is gitignored.

---

# Fix round 1 (2026-10-28)

Commits (base `fd76820`):

| SHA | Subject |
|---|---|
| `35aece6` | Mark the fixture hand check as agent-performed and fix E's reasoning |
| `5f6d587` | Correct register drift against the spec and add missing rows |
| `25bdb1b` | Fix design-reference review findings: layers, ties, sheets, encodings |
| `6ff1dd7` | Update the Sprint 0 review after fix round 1 |
| `ff449da` | Refresh register evidence for the re-run design checks |

`25bdb1b` is the last commit that changes code or data, and every check below ran on it.
The two later commits change only `docs/reviews/sprint-0.md` and register evidence cells.

## Changes per finding

### I1. A dominated route sits on the comparison boundary

The key now reads:

> Every layer 2 and layer 3 route is bettered by at least one other route, even when it
> sits on the dashed line. The dashed line and the shading are a reading aid: there are no
> routes between the points.

Changes:
- Every dominated mark gets a halo in the panel colour, which visibly breaks the dashed
  line around D.
- `route-comparison.js` `onBoundary()` and `renderTieNote()` detect dominated routes lying
  on the line. It generates: "Route D sits on the line at 4 months, but route B is as fast
  and costs £500 less, so D is layer 2." This is the equal-time tie case, from data. In
  DIRECTAI no route lies on the line and the note stays hidden.
- New register row PARETO-04 hands the case to Task 14.
- The README documents the rule.

### I2. F2 and F3 cannot be told apart

- Layer 2 is a filled grey disc and layer 3 a grey ring, on the chart, in the legend and
  on the card letters.
- Point labels read "D layer 2" and "E layer 3". Cards keep "Layer N".
- New contrast pair: the route letter on the layer-2 disc. Contrast: 65/65 pass.

### I3. Register fidelity

The four named rows were amended: AIR1-01, VIS2-03, FIN1-09 and TIME1-03.

Rows added:
- OPT1-13: information-gathering and work actions stay eligible; minimal skill covers are
  insufficient.
- PLN-01: information-gathering, application and waiting actions.
- OPTN-07: "remain in the current job while studying" and "apply now while building
  evidence".
- DIV1-11: the slate shape (two close, two transferable, two less-familiar), P02
  `include_less_familiar_grounded_role`, and the visible relaxation.

`docs/reviews/sprint-0.md:19` now states true coverage: rows paraphrase the spec, ten
families are fidelity-checked, the rest structurally only.

### Second fidelity pass

Every row of FIN1, TIME1, OPT1, ROU1, RDY1, OUT1, VIS1, VIS2, AIR1 and DIV1 was compared
with the spec text (§§4, 5, 7, 10, 12 and 13). Further drift corrected:

- **FIN1**
  - 01: readiness includes evidence, credentials, experience and waits; not an employment
    guarantee.
  - 02: "necessary" equipment, "applicable" support, and loan principal is not "an
    additional copy of tuition cost".
  - 07: the direct-spending wording appears on charts and dominance explanations; only
    economic mode addresses lost earnings.
  - 09: the calibration qualifier, reversals marked, worst-case-vector dominance, no
    invented percentiles.
  - 10: ledger terms and interest accrual.
  - Added 11: the baseline is a user-confirmed counterfactual, not "staying put".
  - Added 12: identical panel definitions, no per-route earnings window, nominal by
    default.
- **TIME1**
  - 01: application and payment dates.
  - 03: completed application or admission.
  - 04: evaluated once per month, no weekly variables, fixed care.
  - 05: outflows include living, transition payments and debt service.
  - 06: the horizon covers the whole planning horizon; deferral cannot manufacture an
    advantage; continuation scenario.
- **OPT1**
  - 01: the enforced constraints and the reviewed finite monthly catalogue.
  - 02: "under the actual model", future funding in bounds, stop-at-readiness only with a
    proof.
  - 06: the stored route fields from the A–I paragraph.
  - 07: scope of proof (declared model and catalogue, never global optimality).
  - Added 14: exact or approximate layer scope; lead with "Best trade-offs found" or a
    margin.
- **ROU1**
  - 01: a bridge role makes a family; an unordered set is not an identity.
  - 02: family card with expandable variants.
  - 03: a layer may hold no new family.
- **RDY1**
  - 01: credential, experience and eligibility gates explicit.
  - 03: optional development is a separate goal; not a hiring guarantee.
- **OUT1**
  - 01: confidence is never an LLM probability; full span and provenance.
  - 02: row-level; the assessment must support the anchor.
  - 06: never manufacture a licence.
  - Added 11: module ownership; the LLM only proposes.
- **VIS1**
  - 03: M0 exclusions.
  - 04: "a few dozen" nodes; aggregation by company or role.
  - 06: labelled-conversion exception; every same-company job.
  - 07: identical ranking and comparison.
  - 08: geographic distance.
  - Added 11: the full filter list.
- **VIS2**
  - 04: focus raises contrast without hiding dominance.
  - 05: branches are alternatives or conditional events; archive in a grouped list.
  - 06: practical-limits panel.
  - 08: dimming others; gate markers.
  - 09: lowest-cost, shortest-time and structurally distinct alternatives; every route
    reachable.
- **AIR1**
  - 02: explicit scope, decision record, deterministic checks.
  - 03: exposure-only evidence stays unscored.
  - 05: the exact filter label.
  - 06: an exception does not satisfy the limit; the plan keeps its assessment version;
    reassessment beyond the horizon.
  - 07: corrections checked before a session.
  - 08: numbered badge; one contract across views.
  - Added 10: meaning (not a job-loss probability; 0 and 10 limits).
  - Added 11: pinned ILO and Anthropic imports, missingness.
  - Added 12: ordinal rubric semantics.
  - Added 13: role-card content.
- **DIV1**
  - 01: template library as cache only; no Career Causeways or extra taxonomy API.
  - 02: "initially" 60–120.
  - 04: corroboration sources.
  - 05: translated synonyms; rare versus unsupported.
  - 06: information gain, greedy without optimality, no ineligible filler.
  - 07: hard filters precede, with counts.
  - 08: useful unfamiliar discoveries and language/region disparities.
  - Added 10: the five channels and sampling.
  - Added 12: novelty relative to familiarity.
- **New anchor PLN-01 to PLN-10** covers the untagged §12 planning model:
  - information, application and waiting actions;
  - the initial state, with resignation never a side effect;
  - entry predicates and precedence;
  - threshold outcomes and experience accrual;
  - the intermediate job as a conditional event;
  - the §12 hard-feasibility list;
  - verified, modelled and condition states;
  - stress cases, with no adaptive policy;
  - no learned hiring probabilities;
  - per-target feasible sets.

The other rows in these ten families were read against the spec and left unchanged, for
example VIS1-01/02/05/09/10, VIS2-01/02/07/10/11, OPT1-03/04/05/08–12, RDY1-02/04/05 and
FIN1-03–06/08.

The register states the fidelity scope in its header. It now has **355 IDs**: 330
planned, 10 verified, 5 spike-verified, 10 not run (human). The structural lint passes:
no duplicates, statuses valid, 16/16 spec IDs, 14/14 families.

### Controller must-fix items

- **M1.** `fixture-hand-check.md` §8 now reads: "D (8 months) and G (10 months) are faster
  than E (11 months), but both cost more". The status line's pointer to section 8 was
  also corrected to section 11.
- **M2.** Both `fixture-hand-check.md` (Status) and `sprint-0-spike.md` (exit table) now
  say: agent-performed; domain-reviewer sign-off (H-07) not run — requires human.
- **M4.** Every AI Resilience display on the map has an "Experimental" badge:
  - all three role cards;
  - the list column header "AI Resilience (experimental)";
  - phone cards, as ", experimental" on published ranges only (unscored roles have no
    record to mark).

  Each card also has an `ai-provenance` slot. It says "Synthetic test record" now; for a
  real record it carries the review date, method version and inherited geography (README).
- **M5.** Phone sheets open at `--sheet-peek: 212px`, a new token in `tokens.css`, with a
  "More" control (`aria-expanded`). Re-shot 390×844 and inspected:
  - You: the question and all three answer choices are visible.
  - Roles: the listing list is visible.
  - Routes: a one-line basis summary replaces the four-row basis on phones, so the route
    cards are visible on the first screen.

### Cheap fixes

- **M3.** The time and cost sliders and number inputs take their max and value from the
  data: 6 months and £6,000 for TRACE-01; 16 months and £7,000 for DIRECTAI. Every plotted
  route, including the selected B (9 months), is inside the default range.
- **M6.** Dashes now mean only "provisional" (the inference edge, the early sketch) or
  "reading aid" (the comparison boundary). The new encodings:
  - stale map nodes: a solid sand ring;
  - Remote: a double ring;
  - an area with none found: a solid ring in the unknown colour;
  - the unknown glyph: a solid circle with a question mark;
  - the unknown alert and the "Schedule not available" block: solid borders;
  - estimated pay: a hollow bar;
  - the synthetic label: a solid pill;
  - the Gantt readiness line: solid.

  The README legend and rules are updated. `grep dash` leaves only the boundary, the
  inference and the sketch.
- **M7.** The failure-state drawer's "Try again" is secondary; the alert's is the single
  primary.
- **M8.** Every check was re-run on `25bdb1b`, and `docs/reviews/sprint-0.md` now records
  that revision, the counts and the review's findings.
- **M9.** The Gantt `aria-label` is generated from the checked route data (hours, actual
  dates, payment pattern, readiness date). The same applies to the other prose that
  stated fixture numbers:
  - the horizon sentence;
  - "5 schedules in 5 route families" (`familyId` added to `data.js` and asserted);
  - the DIRECTAI route count;
  - the phone basis summary;
  - the journey title.

  `check-fixture-data.mjs` now asserts 64 values.

### Found while looking at the re-shot PNGs

- The "More" control showed on desktop: same specificity as `.btn`, which came later.
  Fixed with `.btn.sheet-expand`.
- On phones the "More" control wrapped under the route title; the sheet header is now a
  grid.
- The list read "Remote, remote"; it now reads "Remote, employed in England".

## Checks on `25bdb1b`

| Command | Result |
|---|---|
| `cd backend && uv sync --locked` | Audited 54 packages |
| `uv run --locked ruff format --check .` | 29 files already formatted |
| `uv run --locked ruff check .` | All checks passed |
| `uv run --locked mypy` | no issues in 29 source files |
| `uv run --locked pytest` | 63 passed, 12 deselected |
| `uv run --locked python -I ../fixtures/m0/validate_fixtures.py` | `"status": "passed"` |
| `uv run --locked pytest -m integration spikes/durable` | 12 passed in 31.61 s; no container left |
| `cd docs/design && pnpm install --frozen-lockfile` | up to date |
| `pnpm run contrast` | 65/65 pairs pass |
| `pnpm run screenshots` (runs `check-data` first) | 64 fixture assertions pass; 18/18 captures pass (axe, overflow, console, fonts, label collisions); PNGs byte-identical to the committed set |
| Register lint (scratch script) | 355 IDs, no duplicates, statuses valid, 16/16 spec IDs, 14/14 families |

Re-shot PNGs I inspected:
- route default at 1440 and 390, the DIRECTAI full page, route failure at 390;
- map failure at 1440, the map default full page, map default at 390;
- conversation default at 390, conversation failure at 1440.

No live Meta calls ($0).

## Remaining notes

- On a phone, the Routes failure state leads with the failure and stale notices, and the
  route cards start below the fold. This is deliberate for that state, and noted in the
  review.
- The conversation composer's "Send" stays a filled button in every state. It belongs to
  the composer, not to the view's decision, and the reviewer did not flag it.
- Layers 2 and 3 share one grey (`--mark-front-later`) and differ by shape and label, not
  colour. That satisfies "distinct without colour". A human reviewer may still want a
  second grey (H-02).
