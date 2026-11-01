# Task W2A, fix round 1: scoped re-review

Reviewer: scoped re-reviewer, read-only. Package `review-65aed2f..7ac80dc.diff` (commits
`8b0cdf9` design, `7ac80dc` app), read in passes: docs and tools, then `world.js` and `world.css`,
then the app's world modules, components, CSS and tests. I opened 17 of the 31 reference PNGs and
6 of the app's latest acceptance captures (`apps/web/test-results/visual-*`, 21:10–21:14, the run
the report cites).

Checks I ran (read-only, nothing headed, no network): `git show 8b0cdf9 -- …/world.js` read in
full; `cmp` of the tokens and font mirror (identical); `git diff --stat 65aed2f..7ac80dc --
docs/evidence/` (empty); a scratch script recomputing the app still world's trail contrast with
the contrast tool's formula; image crops of `roles--stale--1440x900.png`. Not run: `make check`,
`make acceptance`, the screenshot or contrast tools (they rewrite tracked files), any browser.

### Spec Compliance

- ❌ Issues found: the app's still world still draws its trails at the old, unmeasured strengths,
  and the docs say it doesn't (see Important 1). Calm mode loses its words on a phone (Minor,
  under A-M1).
- ⚠️ Cannot verify from the diff: the moving world's look after the atmosphere cut (human,
  session W2); whether an open menu ever meets the key in practice (no browser run, Minor 3).

## Verdict per finding and ruling

"Can fail" means: if the fix were undone, the named test or check would go red (break-it
reasoning, not just presence).

### Design half, Important

| ID | Verdict | Evidence | Can its check fail? |
|---|---|---|---|
| D-I1 synthetic label | **Fixed** | Label left `.optional` for `.synthetic-slot` (`world.js:471`), hidden only at ≤760 px where the top bar carries it (`world.css:853-854`). Seen in every 768 capture I opened. | Yes. `screenshots.mjs:94` needs a visible box; a label inside a hidden parent is 0×0 and fails. |
| D-I2 openings | **Fixed** | Clusters ±0.9 units under the chosen destination only (`world.js:255`); "Manchester: 8 openings, 4 sources, today", stale ends "2 days ago" (`world.js:268-269`). `roles--default`, `--stale`, `--three-targets` agree. | Yes. Each dot is a light named by its area; an unnamed one fails `screenshots.mjs:115`. (New Minor 4 on the stale wording.) |
| D-I3 trail contrast | **Partly fixed** | References: strengths are tokens (`tokens.css` `--trail-opacity-*`), drawn from them (`world.js:356-401`), measured as drawn (`contrast-report.md:113-121`, tightest 3.19:1). Moving world: each core at `TRAIL_OPACITY`, additive, glow on top (`gl.ts:211-238`). **App still world: not changed** (`StillWorld.tsx:12-17` still usual 0.55, shadow 0.8, opening 0.4). | References: yes (the tool fails under 3:1). Moving world: yes (`tokens.test.ts:44-46` holds `TRAIL_OPACITY` to the tokens). Still world: **no**; nothing reads `TRAIL_OPACITY` there, so no test can catch it. See Important 1. |
| D-I4 Skills | **Fixed** | Skill fan drawn at You only (`world.js:232`); Skills, Options, Plan views raised (`geometry.ts` restingView, same values in `world.js`); gate where the last stretch begins (`world.js:292-295`). `skills--default` at 1440/768/390: gate clear of the light, one name per skill. | Yes. `screenshots.mjs:123-124` compare DOM boxes and gates against the drawing's own light list, independent of the placer. |
| D-I5 names and key | **Fixed** (gap in Minor 7) | `<details>` "What the lights mean", open above 1100 px; only kinds drawn; keys drawn as the world draws them (`world.js:659-679`, `world.css` `.key-*`). Statistician and Manchester's count now named at 768 and 390. | Yes. An unplaced name loses `.world-label`, so `nameOf` is null and `screenshots.mjs:115` fails; `:116` fails an unseen revelation; `:120` fails a name for a hidden light. |
| D-I6 Routes key | **Fixed** | "Teal: the route you're looking at" vs "the path you chose" (`world.js:675-676`); failed: sand at 0.6, no ring in world or instrument (`world.js:330-335`, `instrument(failed)`). Confirmed in `routes--failed--1440x900.png`. | Capture review only (no machine check asked). |
| D-I7 cost words | **Fixed** | "Total cost, including pay you'd give up" and "What you'd pay out" (`world.js:503-504`); upright axis named (`world.js:530`). DIRECTAI labels untouched. | Capture review only. |

### Design half, Minor (fix now)

| ID | Verdict | Evidence |
|---|---|---|
| D-M2 | **Fixed** (strip rows carried to W2C, as ruled) | "from version 14" gone; Teal/Grey/Sand; "isn't ready yet"; "Use this course"; "Tell me about a skill"; distress mechanics line removed. |
| D-M3 | **Fixed** | Own glyphs for said, support, set aside (`world.js:43-45`); app `Glyph.tsx` gains `support`. |
| D-M6 | **Fixed** | "Look for a course", "Kept from your last search", "Search again" (`world.js:623, 632, 641`). |
| D-M7 | **Fixed** | `--motion-breathe: 0ms` under reduced motion (`tokens.css:260`); rail and glows tokenised; pairs added (`contrast-report.md:48-61, 96-101`). |
| D-M8 | **Fixed** | Rail 96 px in both trees; `screenshots.mjs:92` fails a wordmark outside the rail (can fail). |
| D-M10 | **Fixed** | Three long targets at all three sizes; industry glyph under "Not covered"; "Pay not stated on N" from `DESIGN_LISTINGS` (`world.js:536`). |
| D-M11 | **Fixed** | Outfit commit date and age; licence tally re-run; Source Sans 3 **provisional** in ADR 0014:70, `dependencies.md:147`, `fonts/README.md:38`. |
| D-M9 | **Fixed** | `.link` and gallery links white, underlined (`world.css` `.link`, `index.html`). |
| D-M12 / A-M5 | **Fixed, not run (as ruled)** | Script records commit and dirty state, marks the scene synthetic, says "WebGL GPU time" (`measure-world.mjs:98-112`); `frames.ts` pairs by frame number and counts `over16_7`. `world-frames.json` untouched (empty diff). ADR 0014:90-93 says W2D re-measures with the product owner warned. `frames.test.ts` "pairs … by frame number" uses a dropped GPU sample, so recency pairing would fail it. |

### App half, Important

| ID | Verdict | Evidence | Can its test fail? |
|---|---|---|---|
| A-I1 typing hold | **Fixed** | A timer wakes the loop when the hold ends (`World.tsx:435-442`). | Yes. Without the timer the loop stops at ~1.2 s and nothing wakes it, so the test's last `running` assertion fails (matches the reported mutation run). |
| A-I2 failure paths | **Fixed** (no restore to moving, implementer ruling 2, acceptable) | `failed` ORed into `still` (`World.tsx:318-319`); constructor wrapped, `webglcontextlost` handled (`:374-384`); listener removed **before** `dispose()` forces loss (`:392`), so calm/distress toggles don't mark failure; probe context released and `dispose()` skips a lost context (`gl.ts`). | Yes. Both tests assert `data-world-mode="still"` and the still SVG; without the listener or the try/catch they fail. |
| A-I3 parity | **Fixed** | `world.spec.ts:55-66` collects the sorted names in sight plus "key placed"; `:240-270` compares moving, reduced motion, calm and paused, per chapter, at three viewports, in a new three-long-target workspace. | Yes. A name in sight in one mode only changes the sorted array and fails `:261`. Not vacuous at Roles: `:265-268` require "You" and a long target. (At You on a phone all modes show no names, so that cell compares empty sets; acceptable.) |
| A-I4 tablet and phone | **Fixed** | `clearArea`/`placeView` stand the place above the card (`geometry.ts`); a light under a panel hides its name (`labels.ts:58`); phone header two rows. App captures `roles--768x1024` and `roles--390x844` show You and the target above a short card. | Yes. Geometry tests put every node between the bars and the card; labels test hides a name under a sheet; e2e `:305-308` requires "You" and "Data quality analyst" in sight at all three sizes, still and moving. |
| A-I5 not-built card | **Fixed** | Five elements, the rest under "More about this place" (`ChapterView.tsx` `NotBuiltYet`). | Yes. The new test asserts one heading, one link, and "Uses these answers from You" not visible. |
| A-I6 quiet actions | **Fixed** | `.btn-quiet` text colour + underline, `.btn-icon` text colour (`globals.css:602-616`). No other text use of `--action` in the app besides `.btn-primary` (`:589`); links were never teal in the app. Capture `you--support-note--1440x900`: Skip, Source, Keep none, Dismiss white. | Capture review only. |

### App half, Minor (fix now)

| ID | Verdict | Evidence |
|---|---|---|
| A-M1 calm mode | **Partly fixed** | In the account menu with the same wiring, persistence and device override (`WorkspaceShell.tsx:207`, `WorldControls.tsx:80-90`); e2e toggles it there and checks the strip has none. **But on a phone it loses its words**: the account popover has no `Popover.Portal`, so it renders inside `<header class="strip">` (`WorkspaceStrip.tsx:186-206`), and the phone rules `.strip .world-toggle-label` (sr-only, `globals.css:1089`) and `.strip .world-switch {display:none}` (`:989`) apply to it. Calm mode shows as the bare two-wave glyph. The ruling asked for "the same … words". Fix: scope the phone rules to `.world-controls` (or portal the popover). |
| A-M4 | **Fixed** | Reused view and frame, uniforms in place, `sameView`, all reads before writes in `placeLabels`. |
| A-M6 | **Fixed** | `Sound.close()` on unmount (tested), density `matchMedia`, re-place on font load. |
| A-M7 | **Fixed** | `sound.ts` and the story say chime and tick have no trigger until W2C. |
| A-M8 | **Fixed** | `Place.moment`, `PALETTE.chosen` removed; shader colours written from `palette.ts`. |
| A-M9 | **Fixed** | Marks `canvas[data-testid=moving-world]`; a recreated canvas loses the mark and fails. |
| A-M10 | **Partly fixed** | `hasAnswered` iterates `PROFILE_FIELD_ORDER`; "Pause the interview". The calm glyph point is not moot on a phone (see A-M1). |

### Rulings

| Ruling | Verdict |
|---|---|
| Trail contrast as drawn, nothing decorative | **Partly met**: references and moving world yes; app still world no (Important 1). The distress dim is an undeclared exception (Minor 5). |
| Calm mode in the account menu; Pause and Sound visible | **Partly met**: Pause and Sound visible at every width; calm wordless on a phone (A-M1). |
| Distress stills (and dims) the world; Pause shows the person's choice | **Met**: reference `world.js:461`; app `World.tsx:319`, `WorldControls.tsx:63-68`, `WorkspaceShell.tsx:220`. Tests: unit (still under the panel, moving after), controls (status, Pause unchanged and still clickable), e2e (risk message → still, `data-distress`, status, Pause off → dismiss → moving). All can fail. The added dim is plan-mandated ("stills and dims", plan section 4). |
| Atmosphere cut | **Met**: shimmer and sway gone, motes 360 (`gl.ts:34`); breath (`:71, :105`), aurora (`:112`) and flow along known trails (`:228-236`) kept; still world untouched by it. |
| Body face provisional | **Met** (ADR 0014:70, `dependencies.md:147`, `fonts/README.md:38`). |
| Frame evidence | **Met**: script fixed, not run, `world-frames.json` untouched, ADR says so. |
| Strip words, D-M5, A-M3 | Correctly left for W2C. |
| Known and accepted (route preview words, 768 strip rows, strip words) | Not re-raised. |

### The Python-script edit to `world.js` (`8b0cdf9`)

I read the whole `world.js` diff of `8b0cdf9`. No stray or broken edits: every hunk belongs to a
named finding, the page renders (31 captures), and the legend kinds, the Routes gate index and
the next-step key read as intended. Two changes are not mentioned in the report; neither looks
like one of the six described replacements, and both look deliberate (Minor 9):
- Plan's month-by-month teal landmarks along route B are gone; only the next step remains.
  Arguably right (plan section 4 lights landmarks from real progress), but unreported.
- Unselected routes are now drawn with the "said" state (`world.js:335`): full strength and the
  bright glow of "you said you've done it". The key's words are right ("Blue to violet: a whole
  route"), but the code reuses a meaning to get a strength.

## Strengths

- The new screenshot checks are real: they take lights and gates from the drawing and measure
  names in the page, so they test the placer rather than restate it.
- The parity test is now the test the review asked for, and it cannot pass by construction.
- The failure path is careful: the listener comes off before `dispose()` forces a context loss,
  so a calm or distress toggle never looks like a failure.
- The not-built card and the references now match, and the phone shows the place above it.
- Records are honest: the frame evidence, the provisional face and the script slip are stated.

## Issues

### Critical

None.

### Important

**1. The app's still world still draws trails below 3:1, and four records say it doesn't
(D-I3, partly fixed).**
- Where: `apps/web/src/components/StillWorld.tsx:12-17` keeps its own table: usual 0.55,
  shadow 0.8, opening 0.4. It was not touched in this round. `TRAIL_OPACITY` is read only by
  `gl.ts`.
- As drawn (contrast tool's formula): the grey "not known yet" trail, the only trail the app draws
  today, is **2.82:1** where it meets the horizon's glow. Usual is 2.24–2.53:1; an opening's
  trail 1.77:1. All need 3:1. This is the world drawn for reduced motion, calm mode, distress
  and a failed WebGL context.
- The records claim the opposite: `docs/design/README.md:118` ("The app's still world draws the
  same strengths"), ADR 0014:88 ("in both of the app's worlds"), `palette.ts:2-3` ("The still
  SVG world draws with them") and the report (`task-W2A-report.md:276`).
- No test can catch it: `tokens.test.ts:44-46` checks `TRAIL_OPACITY`, which the still world
  never reads.
- Fix: draw `StillWorld`'s trail strokes from `TRAIL_OPACITY` and delete its `OPACITY` table;
  add a test that renders `StillWorld` and asserts each trail's `stroke-opacity` equals its
  `TRAIL_OPACITY` value.

### Minor

1. **Leader lines cross other names and lights.** The rule checks a leader only against panels
   (`world.js:767`, `labels.ts:76-85`). In `roles--stale--1440x900.png` the Leeds and Remote
   leaders run through the "Data quality analyst" name and its teal ring. In
   `you--distress--1440x900.png` the "Keep accurate records" leader runs straight through the
   destination's light. In `options--default--390x844.png` a bridge leader crosses the
   destination's name. A line can join a name to the wrong light, the same risk class as D-I2.
   Fix: reject a spot whose leader meets another light's centre or a placed name, and add that
   to `screenshots.mjs`.
2. **A long wrapped name leaves its marker on a line of its own.** `flex-wrap: wrap` on
   `.world-label` (`world.css:101`, `globals.css:178`) puts the `::before` disc on row one and the
   name on row two: see the lone orange dots above both long names in
   `roles--three-targets--1440x900.png` and `--390x844.png`. The app uses the same CSS, and its
   parity workspace has these names. Fix: keep the disc and the name on one flex line and let the
   name's own text wrap.
3. **The key now sits above every menu.** `.world-key` is `position: fixed; z-index: 5` outside
   `.app` (`globals.css:239-243`), while `.app` is its own stacking context at `z-index: 1`
   (`:313-315`). The account, chapter and workspace popovers (`z-index: 30` inside `.app`, no
   portal) therefore paint under the key wherever they meet. The re-placement avoids only
   `[data-covers-world]`. Not seen in the captures; not checked in a browser. Fix: give the key a
   z-index under the menus within the same context, or mark open popovers as covers.
4. **The stale reference overstates coverage.** "Remote: 3 openings, 4 sources, today" sits
   beside "The job board didn't answer today" (`world.js:268-269` uses `sourcesChecked` for every
   area). Today's coverage for Remote is at most 3 sources. Fix: count only the sources that
   answered.
5. **The distress dim is an unrecorded exception to "3:1 as drawn".** The dim (plan-mandated)
   takes trails below 3:1. That is stated only in the report. README:112-119, ADR 0014:88 and
   the pairs file claim every trail passes. The ruling said "do not declare them decorative".
   Fix: record the exception where the claim is made, and get the controller's word on it.
6. **On a phone in distress the header grows to three rows and shows an empty key.** In
   `you--distress--390x844.png` the status pushes Sound and the menu to a third row, and "What
   the lights mean" shows with no light in view. Fix: put the status where it doesn't add a row,
   and show the key only when a light it explains is in view.
7. **The key can vanish without any check failing.** With no room it is hidden (`world.js`
   layout; `World.tsx` `data-placed="false"`). Neither `screenshots.mjs` nor `world.spec.ts`
   fails when lights are in view but the key is not. Fix: fail when a light is in view and the
   key is unplaced.
8. **The three-targets reference strip names one target.** "Target Data quality analyst"
   (`world.js:472` reads `F.p01.targetTitles`) beside "Three places you chose to head for."
   Fix: name the three in that state.
9. **Two unreported `world.js` changes** (month landmarks removed; unselected routes drawn as
   "said"). See the script section. Fix: record them, and give routes their own state rather
   than borrowing "said".

## Assessment

**Task quality:** Needs fixes

**Reasoning:** Nearly every finding is fixed, with checks that can fail, and the references, the
moving world, distress, the parity test and the phone layout all hold up. But the app's still
world was not changed for trail contrast, a controller ruling, while four records say it was;
that one fix and its test are small.

Counts: not fixed 0; partly fixed 3 (D-I3, A-M1, A-M10); regressed 0. New issues: Critical 0,
Important 0, Minor 9 (Important 1 is D-I3's unfixed part, not new).
