# Careerwright design references (Sprint 0)

**Superseded direction (2026-10-30).** The "calm observatory" below is replaced by the living
world: the plan's section 4 (v1.4) and ADR 0014. These references stay as the record of
Sprint 0, and their fixture checks keep running, until Sprint W's references replace them.
Do not polish them or build new work on their look.

Versioned visual reference for L0: semantic tokens with measured contrast, two licensed
fonts, and three signature compositions built as static HTML, CSS and SVG. Each
composition has a desktop and mobile layout, an unknown-data state and a failure state.
Task 4 implements the shell and components from these files; Tasks 8 and 14 implement the
map and the route comparison.

**Status:** reference built and checked by machine. **Human design approval: not run,
requires a human** (ruling R2). The agent's own critique is in `pre-review-sprint-0.md`,
labelled as an agent pre-review. It is not a review score.

## What is here

| Path | What it is |
|---|---|
| `tokens/tokens.css` | Canonical tokens: primitives, semantic tokens, the `.on-space` / `.on-reading` contexts, type, space, radius, motion |
| `tokens/contrast-pairs.json` | Every text and meaningful non-text pairing the pages use, with its WCAG threshold |
| `tokens/contrast-report.md` | Generated measurements: **68 of 68 pairs pass** (three added by Task 4 for the web shell) |
| `fonts/` | Source Sans 3 and Newsreader, with licence texts and provenance (`fonts/README.md`) |
| `compositions/index.html` | Gallery: every composition and state |
| `compositions/conversation.html` | You: conversation, What we know, evidence drawer |
| `compositions/opportunity-map.html` | Roles: map, selected role, pay and location lens, list |
| `compositions/route-comparison.html` | Routes: time-cost comparison, route cards, selected journey, monthly ledger |
| `compositions/data.js` | Fixture values (checked) and synthetic map listings (labelled) |
| `screenshots/` | 18 PNGs (3 compositions × 3 states × 1440×900 and 390×844) and `checks.md` |
| `tools/` | `contrast.mjs`, `check-fixture-data.mjs`, `screenshots.mjs` |

Open `compositions/index.html` in a browser, or a composition with `?state=unknown` or
`?state=failure`.

## Reproduce

```bash
cd docs/design
pnpm install --frozen-lockfile
pnpm exec playwright install chromium   # once per machine; Playwright 1.64.1's pinned Chromium
pnpm run contrast        # rewrites tokens/contrast-report.md; exits 1 on any failing pair
pnpm run check-data      # asserts every fixture value in compositions/data.js equals fixtures/
pnpm run screenshots     # runs check-data, then captures all states and writes screenshots/checks.md
```

`screenshots` serves the folder on an ephemeral 127.0.0.1 port, never on a public
interface. Its checks per capture: axe-core 4.14.0 (WCAG 2.0, 2.1 and 2.2, A and AA
tags), no horizontal overflow, no console errors, both fonts loaded, no chart label
leaving its chart or overlapping another label or a data mark, and at most one filled
primary action in view. Where a phone sheet is open it also checks that the first list
card starts at least 40 px above the sheet, and that no control brought into view by
focus is covered at its centre (by the sheet or the reply field).

## Visual direction: a calm observatory

Exploration happens on ink (the "space" context). Structure is drawn there in fine pale
lines: map branches, the route staircase, the open-circle anchors. Reading and decisions
happen on light canvas and white cards (the "reading" context). The conversation stays on
the light surface, quiet and human. The map and the route comparison carry the visual
spectacle (spec section 14). The one bold element on each page is its structure drawing.
Everything around it stays plain.

Rules the compositions follow, which implementations must keep:

- **One primary action per view.** Filled buttons are reserved for the decision in focus
  (for example, Accept in the evidence drawer). Repeated actions in lists are secondary.
- **Sea-glass means selection, focus or the primary action, and nothing else.** On light
  surfaces it is `#0A7360`, because the spec's `#5DE0C1` reaches only 1.62:1 on white and
  1.51:1 on the canvas.
- **Industry colour is categorical only.** It is never status. Status is carried by a
  glyph and words first, and only error and stale add a hue. Neither hue is an industry
  hue: the closest pair is error against coral on light, ΔE76 20.9.
- **Unknown is drawn, not omitted.** The question-mark glyph, the words, and solid lines
  in the unknown colour mark unknown values ("Not confirmed, not £0", "Pay not stated",
  "none found"). A missing value is never a zero, a blank or a lowest rank.
- **Dashes mean only "provisional" or "reading aid".** A dashed edge marks a proposal or a
  sketch that is not yet a fact (Careerwright's inference, the early sketch). A dashed line in a
  chart is a reading aid (the comparison boundary). Unknown, stale, remote, estimated and
  synthetic never use dashes:
  - stale map nodes: a solid sand ring;
  - the remote area: a double ring;
  - an area with none found: a solid ring in the unknown colour;
  - estimated pay: a hollow bar;
  - the synthetic label: a solid pill with the flask glyph.
- **Failure, stale and conditional look different.** Failure has a red edge and a cause
  and keeps earlier results. Stale is sand, with a clock and an age. Conditional is a gate
  diamond with its condition in words.
- **Synthetic data is always labelled.** A "Synthetic demo" label with the flask glyph
  sits in every workspace strip and mobile top bar.
- **Layers are told apart without colour.** Layer 1 is a bright open ring, layer 2 a grey
  disc and layer 3 a grey ring, and later layers are labelled "layer 2" and "layer 3" on
  the chart and the cards. A dominated point drawn on the comparison line gets a halo that
  breaks the line around it. A generated note names the equal-time tie: TRACE-01 D sits
  on the line at 4 months, and B is as fast and £500 cheaper.
- **Phone sheets open at a peek** (`--sheet-peek`, 212 px) with a "More" control, so the
  main task stays in view: the question and its answer choices, the listing list, or the
  route cards. "More" raises the sheet to the viewport less 72 px and becomes "Less";
  dragging the handle does the same. Designed and built in Task 4 (ADR 0005 decision 8);
  these static references show the peek only. The content keeps room below for the sheet
  and the reply field rides above it, so anything brought into view stops above both. The
  peek leads with what the selection is: the route's or field's name, its condition or
  freshness, and its key figures, in every state (Task 6c, S0-V04, S0-V06).
- **A notice leads with its label and a one-line summary;** its explanation is one tap
  away, so on a phone the first card of the list stays above the sheet (S0-V07).
- **A card keeps its own qualification.** A conditional route says "Conditional" beside
  its readiness on the card itself, not only in a note above the list that can scroll
  away (S0-V03). Computed routes (Task 14) take that qualification from their own
  computed readiness state, never from the fixture adapter's words, and never show an
  unqualified "Ready in …" when that state carries a condition.
- **AI Resilience is always marked Experimental** (spec AIR-1). Each display has a badge and
  a provenance line. Synthetic records say so. For a real record, the same line carries
  the review date, method version and inherited geography.
- **Chapters are not numbered.** The rail marks each chapter as visited, current or not
  started. Chapters are navigable states, not a wizard (spec section 3). A filled landmark
  means the chapter's decisions are recorded (spec section 15), as these references show
  for earlier chapters; a chapter that was only opened has a brighter ring, never a fill,
  so visiting cannot read as finishing (Sprint 1 V-09).

### Tokens

Use the semantic names (`--text-on-space`, `--surface-card`, `--status-error-on-reading`,
…) or the context aliases inside `.on-space` and `.on-reading` (`--fg`, `--fg-muted`,
`--action`, `--focus`, `--status-*`, `--industry-*`). Primitives are for `tokens.css`
only. The spec's starting values are kept: ink `#09121F`, raised ink `#142338`, canvas
`#F5F7FA`, cards `#FFFFFF`, text `#EEF4FC` / `#B1C1D6` on dark and `#142338` on light, and
sea-glass `#5DE0C1` on dark.

Measured highlights (`tokens/contrast-report.md`):

- Primary text on ink: 16.97:1. Secondary text `#B1C1D6` on raised ink: 8.64:1.
- Body text `#142338` on the canvas: 14.74:1.
- Sea-glass on ink: 11.53:1. Its light variant `#0A7360` on cards: 5.77:1.
- The tightest pairs are the control borders: 3.26:1 on raised ink and 3.31:1 on the
  light canvas, against a 3:1 requirement.

One pairing failed on the first run and was fixed. The light-surface control border
`#8392A6` measured 2.95:1 and is now `#7A899E`.

Composited colours are checked separately, because the report covers opaque tokens only:

- Map branches are drawn at 75% opacity over ink. The lowest is 4.32:1.
- Lens bars for other companies are dimmed to 75%. The lowest is 3.86:1. At 60% the
  "Other" hue fell to 2.97:1, so 75% was chosen.

### Type

| Use | Face | Size and weight |
|---|---|---|
| Page titles, the current question, card titles | Newsreader | 31 px (25 px on phones), weight about 340 |
| Body and interface | Source Sans 3 | 16 px body, 14 px secondary, 12 px floor |
| Numbers | Source Sans 3 tabular figures (its default) | as surrounding text |

The scale is modular (ratio 1.25 from 16 px): 12, 14, 16, 20, 25, 31, 39, 49. Line
length is held to about 62–66 characters in reading columns.

### Space, radius, motion

- Space: 4, 8, 12, 16, 24, 32 and 48 px.
- Radius follows hierarchy rather than one value everywhere: 12 px controls, 16 px cards,
  24 px sheets and drawers.
- Motion tokens: 150 ms controls, 260 ms panels, 420 ms graph reveal. All become 0 ms under
  `prefers-reduced-motion`. The references are static, so they show no motion.

### Status vocabulary (glyph first)

| State | Glyph | Words in the references |
|---|---|---|
| Complete | circle with a check | defined, not used on these three pages |
| Conditional | diamond gate | "Conditional: ready only if the assessed report passes" |
| Stale | clock | "Last checked 2 days ago; may have closed" |
| Failed | triangle with a mark | "Failed: reply didn't pass validation" |
| Unknown | circle with a question mark | "Not confirmed, not £0" |
| Synthetic | flask | "Synthetic demo", "Synthetic test record" |

The glyphs were drawn for this reference as simple SVG paths, so no third-party icon
licence is involved. Task 4 chooses the product's licensed icon set and maps these six
meanings onto it.

## The compositions and their data

All numbers in the conversation and route comparison come from the fixtures. The prose
binds them through `data-gbp` / `data-value`, and `check-fixture-data.mjs` asserts 59
values against `fixtures/m0` and `fixtures/reconstructed`. The route page also re-peels
the layers in the browser and recomputes route B's monthly ledger; a mismatch with the
fixture is a console error, which fails the screenshot run.

| Composition | Default | Unknown data | Failure |
|---|---|---|---|
| You | P01 (sure entry). Review tray with facts, a hard limit needing confirmation and a dashed inference. Evidence drawer quoting the exact span behind "£2,000 a month". Early requirement sketch from the TRACE-01 target rows, labelled "not a checked route" | P02. Baseline pay "Not confirmed, not £0", with the explicit "Compare direct spending only" choice; personality skipped; budget "prefer not to say"; no sketch until a target exists | The last reply failed validation twice (`SCHEMA_INVALID`). The message is kept and marked not processed; What we know is unchanged at version 7 |
| Roles | Target from P01. P01 lists only Manchester; the default and failure states add Leeds and a remote area to show the three-area maximum, and the unknown state uses P02's Leeds and Manchester. AI range 5–8 with minimum 6 from the TRACE-01 score record, explained as failing the lower-bound filter. Pay benchmark and trend shown as not available (`role_card` nulls). **Listings, employers and salaries are invented for design review** (the pack has none) and labelled synthetic | Three listings, pay not stated, a snippet-only listing, Leeds "none found in the 4 sources checked", unresolved occupation mapping | The job-board source failed. Its four listings are kept from 2 days ago, ringed in sand and labelled stale; coverage says 3 of 4 sources responded |
| Routes | TRACE-01, economic cost: A, B, C in front 1, D in 2 (on the line, an equal-time tie with B), E in 3; staircase and shaded bettered region; route B selected, with the Gantt (actual dates, parallel work and study, four £150 payments, gate, ready from 1 May 2027) and its ledger (lowest point £4,850 in January) | DIRECTAI in explicit direct-spending mode, with direct-spending labels throughout. Nine routes in three layers. The schedule is shown as not available, because the fixture defines months and cost only | The search failed (run 7). The previous comparison stays readable as version 14, with a stale label |

Comparator rule shown on the cards (a proposal for Sprint 7): a bettered route names its
**cheapest dominator**, with ties going to the shorter time and then the route ID; any
other dominators are listed. Under this rule DIRECTAI G names B, not A. The rule is
declared on the page.

## Not covered here (owners)

- The tablet layout (768×1024) and the other three chapters: built in `apps/web` by Task 4
  (Sprint 1; screenshots in `docs/reviews/sprint-1/`), not added to these references.
- The phone's focused chart view and map overview are only entry points here (an "Open
  the time and cost chart" button and a Map/List toggle). Their layouts are not composed:
  Tasks 8 and 14.
- Keyboard flows, focus return, live announcements and DOM equivalents for the Gantt and
  the lens beyond their text alternatives: Tasks 4, 8 and 14. axe passing is not a
  keyboard test.
- WebKit and Safari rendering: these captures use Chromium only. Safari is a human check
  (R2).
- Motion and calm mode: static references, so no motion is shown.
- Map label layout uses fixed angles that were checked by machine for this data set. The
  real map needs measured label placement (the route chart already does this greedily),
  stable anchors and aggregation at 100 nodes: Task 8.
- Industry assignment (finance is blue, and so on) is illustrative. Task 8 fixes the
  mapping from a reviewed classification.
