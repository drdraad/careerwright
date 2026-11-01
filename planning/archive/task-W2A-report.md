# Task W2, slice W2A: the world layer and its design references (report)

Implementer's report. Branch `l0-local-release`, from `c1bc2f3`. Scope: the controller's W2A
paragraph (`task-W2-slices.md`): SW.2 design references, SW.3 the world layer in the app,
ADR 0014's spike choices and the library in `docs/dependencies.md`. Not built here, by the
slice plan: W2B's deterministic sources (ESCO ignition, the slate by shared skills, the
overlooked-strength run kind), W2C's You chapter in the world and its first moments, W2D's
register family, Sprint W acceptance and session W2's package.

## Commits

| SHA | Subject |
|---|---|
| `d989d15` | Design references for the living world: Horizon made livelier (Task W2, slice W2A) |
| `cb7fdbd` | The world in the app: one living world behind all six chapters (Task W2, slice W2A) |
| `65aed2f` | Record W2A's frame measurements of the world's busiest scene (evidence only, no code) |

`make check` and `make acceptance` ran on `cb7fdbd`; `65aed2f` adds only the measurement
JSON. This report is in the gitignored `.superpowers/` folder, so it is not committed.

## What I built

### SW.2 Design references (`docs/design`, replacing the Sprint 0 compositions)

- **Tokens v0.2.0** (`tokens/tokens.css`): the world's palette with one colour, one meaning
  (orange destinations; sea-glass selection, chosen path and the primary action; blue to violet
  the journey; slate "not known yet"; crimson and sand for failed and stale after a glyph);
  dark glass tokens carrying their opacity (`#070B17E8`, 91%); white focus rings; world light
  tokens; Outfit as display face; and the motion vocabulary as tokens (`--motion-feedback`
  90 ms, `-control` 150, `-panel` 260, `-travel` 600, `-grow` 650, `-dim` 400, `-ignite` 1400,
  `-reveal` 1800, `-settle` 320, `-breathe` 7000; all 0 ms under reduced motion). Semantic
  token names kept; industry tokens removed (no component used them; industry is glyph and
  label now).
- **Contrast tool** (`tools/contrast.mjs`): now composites a translucent background over each
  backdrop a pair names (`"over"`), so panels are measured over the darkest ground and over
  pure white, the brightest any light in the world reaches; the distinctness table now
  compares status hues with the world's meaning hues. `contrast-pairs.json`: 67 pairs, every
  new pairing included (glass, labels, world lights on the ground and on the horizon's glow).
- **Fonts**: Outfit 1.100 (OFL) from `google/fonts` at a pinned commit, unmodified, hashed;
  Newsreader retired from `docs/design` and the app's mirror. `fonts/README.md` rewritten.
- **Compositions**: `world.html?place=…&state=…` draws each place as the still world in
  Horizon's geometry (the app's views) with the exact layer over it; `world.css`,
  `world.js`, `index.html` gallery. Six places at 1440×900, 768×1024 and 390×844, and every
  honest state: unknown (Roles, Skills, Options), conditional (Skills and Routes gates), stale
  (Roles), failed (You, Routes), synthetic (always labelled), distress (You, desktop and
  phone: the world stills and dims beside the calm support panel) and "not built yet" (Roles,
  desktop and phone). `data.js` keeps its checked fixture values; Routes uses TRACE-01's five
  routes and B's figures, Plan uses B's dates and payments.
- **Screenshot tool** rewritten for the world: axe, overflow, console, both fonts, every name
  inside the window and clear of the panels and of each other, the instrument's labels clear
  of each other and its marks, at most one filled primary action.
- **README** rewritten: the direction, colour meanings, contrast highlights, type, the motion
  vocabulary table (meaning, motion, timing token, still version), the six places, the honest
  states, what was kept from Sprint 0, and what is not covered.

### SW.3 The world layer in the app (`apps/web`)

- `src/lib/world/`: `model.ts` (what the world shows, from the profile only), `geometry.ts`
  (Horizon's layout, the six places' views, projection, travel tween, the clear-span centre),
  `scene.ts`, `gl.ts` (three.js renderer: raw GLSL 3 backdrop, trails, lights and motes; GPU
  timer queries), `labels.ts` (names beside their lights), `palette.ts` and `motion.ts` (token
  values, held to the tokens by a test), `frames.ts` (instrumentation), `sound.ts` (three
  cues), `settings.ts` (calm, pause, sound, reduced motion), `places.ts` (each place's words).
- `src/components/World.tsx`: one persistent world, mounted once by `WorkspaceShell` behind
  `.app`, so it survives chapter navigation (checked in the browser by marking its node).
  Moving (WebGL2) or still (`StillWorld.tsx`, SVG, same scene); the frame loop runs only while
  something moves and stops when paused, at rest or hidden; ambient motion eases to still
  while the person types (1.5 s) or points at the chapter's panel or the drawer. Every light's
  name is a DOM list item ("Your world"), placed beside its light, clear of the panels and of
  each other, with a second row and a leader line before hiding; the key to the lights is
  shown only where no panel covers it.
- `src/components/WorldControls.tsx`: Pause motion, Calm mode and Sound as toggle buttons in
  the strip (visible on every size; words collapse to glyphs on a phone).
- The old shell's look retired: glass strip, the rail as a journey (a fine trail joins the six
  landmarks; the current place has the sea-glass lock-on ring), chapters on dark glass,
  chapters not built yet as a small "Not built yet" card low in the world, the bright primary
  action with its glow, Outfit headings, the body's horizon background on sign-in and the
  workspace list, the icon in the world's colours. Session, queries and events wiring in
  `WorkspaceShell.tsx` unchanged.
- Storybook `World` stories: the waiting world, each place with targets, calm, travel between
  places, the busiest scene (measurement) and the three sounds.
- `scripts/measure-world.mjs` (`pnpm run measure-world`): the busiest scene in Google Chrome,
  three ways, with device, browser and renderer.

### What each chapter shows now

| Chapter | In the world | Over it |
|---|---|---|
| You | Close to the person's light (lit once any answer is saved), standing in the span right of the panel; their targets on the horizon, joined by slate "not known yet" trails | Today's You chapter unchanged in behaviour, on a glass panel (W2C rebuilds it in the world) |
| Roles | Looking out to the horizon: the person's targets, named, with the person below | "Not built yet" card: the horizon, what it will hold, the answers it uses, Review what we know |
| Skills | Low along the ground between the person and the targets, in shadow | "Not built yet" card |
| Options | Raised over the middle ground | "Not built yet" card |
| Routes | High and wide: whole journeys | Fixture workspace: the labelled fixture route preview on a glass panel (unchanged); elsewhere "Not built yet" |
| Plan | Behind the person, looking down the path | "Not built yet" card |

On a phone the world is the backdrop; chapters are sheets over it.

## Rulings I made (and why)

1. **Body face stays Source Sans 3**; Outfit is display only. Session W1 chose only heading
   lettering; Source Sans 3 is licensed, measured and has tabular figures by default. The
   spike's Atkinson Hyperlegible Next is not adopted. Recorded in ADR 0014 decision 6.
2. **What the world may draw in W2A**: the person's light is lit once the profile holds any
   answer (Answered, Unknown, Skipped or Prefer not to say; only "Not asked yet" is not an
   answer); destinations are the person's own provided targets, deduplicated, in title order;
   the ground between is a shadow trail. No skills, connections or openings are drawn from
   the app's data until W2B/W2C compute them (the scene supports them, and a skill joins a
   destination only where the input says they share it, never by a guessed rule).
3. **Sound**: the swell is wired to ignition (the light comes on during a visit, never for
   what was there on arrival). The chime and tick exist, are tested and are playable from the
   `World / Three sounds` story, but have no source event in W2A: a connection lighting up and
   picking a skill arrive in W2C. Sound is off every visit until turned on; calm mode is kept
   between visits (local storage, as before); pause is per visit.
4. **Calm mode moved** from the account menu to the visible controls, so the three world
   controls sit together.
5. **No side fibres**: the busiest scene showed them as scattered strokes, the "chaos" and
   noise the product owner did not want. Life comes from sway, breathing, the aurora, the
   horizon shimmer, mist, motes and light flowing along known trails.
6. **Focus is white and a switch's "on" is white**: sea-glass stays for selection, the chosen
   path and the one primary action. Focus rings carry a dark halo so they stay visible over any
   light.
7. **"Reading" holds ambient motion** only over the chapter's panel or the drawer (marked
   `data-world-panel`), not the strip: pointing at Pause and un-pausing must restart motion
   (a browser test caught this).
8. **The view centres in the clear span**: where the chapter's panel (left) and an open drawer
   (right) leave at least 240 px of world, the place's focus stands in the middle of it, so the
   person's light is not under the You panel on wide screens. Phones keep their views.
9. **Glass at 91%**: over pure white, a control boundary on glass falls below 3:1 under about
   86% opacity (2.46:1 at 80%, 3.07:1 at 86%); 91% keeps a margin (3.59:1) while the world
   still shows faintly through, blurred.
10. **Architecture test** (`backend/tests/architecture/test_boundaries.py`): three.js admitted
    in `apps/web/pnpm-lock.yaml` only (ADR 0014 decision 2); PixiJS and three.js stay excluded
    everywhere else.
11. **Measurement**: at device scale 2 (a Retina canvas, 2880×1800), in the Storybook busiest
    scene, synthetic and labelled; a synthetic busy scene never appears in the app.
12. **Test fixes outside the world's own specs**: `e2e/helpers.ts` axe now waits for a scan
    already running (the Storybook a11y addon scans after each render, and the larger world
    stories made the race visible); `e2e/visual.spec.ts` finds "Less" inside its sheet (a
    loose name match also found the Calm mode control's reason, "…less motion…") and checks
    Outfit, not the retired Newsreader. No assertion was weakened.

## Checks run

All on the final code (`cb7fdbd`; the last commit adds only `docs/evidence/world-frames.json`).

| Command | Result |
|---|---|
| `make check` | exit 0: ruff format and lint clean, mypy clean, backend fast pytest **1511 passed**, fixture validator passed; web: client drift none, Biome clean (135 files), `tsc` clean, Vitest **33 files, 275 tests passed**, no warnings |
| `make acceptance` | exit 0: integration and stack pytest **299 passed** (10 min 8 s, real PostgreSQL 16.15, DBOS, Auth emulator, Compose); Storybook build; Playwright **35 passed** (journey, access, conversation, session, keyboard, layout, Storybook axe on all 51 stories, the visual package at three viewports and 200 % zoom, and the 7 new world tests) |
| `pnpm --dir docs/design run contrast` | **81 of 81 measurements pass** (67 pairs); smallest status-to-meaning ΔE76 53.0 |
| `pnpm --dir docs/design run screenshots` (runs `check-data` first) | check-data: **64 fixture assertions pass**; **28 of 28 captures pass** (axe, overflow, console, fonts, name and label collisions, one primary action) |
| `pnpm run measure-world` | below |

Earlier runs on the way (fixed before the final runs): the first acceptance run failed 2 of
35 (the Storybook axe race and the visual spec's loose "Less" match, ruling 12); a first
targeted world run failed 1 of 16 (un-pausing while pointing at the strip, ruling 7). After
the fixes a targeted run of the world, visual, Storybook and conversation specs passed 17 of
17, then the full acceptance above.

### TDD evidence

The world's pure modules (model, geometry, scene, frames, sound) were drafted with their tests
in the same sitting, not strictly test-first. Strictly test-first (RED then GREEN, by run):
- `labels.test.ts`: RED (module missing) → GREEN 3/3; then the second-row rule: RED (1 failed,
  "a crowded one steps out a row") → GREEN 3/3.
- `geometry.test.ts`, "centres the place in the part of the world the chapter's panel leaves
  clear": RED (1 failed) → GREEN 14/14.
- Browser findings reproduced before the fix: pause then un-pause stayed "still" (world spec,
  1 failed) → fixed → passed; the person's light under the You panel at 1440 (seen in the
  visual capture) → the clear-span test above.

### Frame times (busiest scene)

Apple M4, 16 GB (`Mac16,1`), macOS 27.0, Google Chrome 156.0.8078.76, WebGL renderer
`ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)`. Window 1440×900 at
device scale 2 (canvas 2880×1800). Scene: Storybook `World / Busiest scene` (invented,
labelled): 100 openings and their trails, 12 skills, 5 destinations with shared-skill trails,
2,400 motes, travel to another place every 3 s and the ignition replayed every 4 s; warm-up
3 s, then 12 s. Measured 2026-10-30 19:52 UTC (`docs/evidence/world-frames.json`).

Per-frame cost = the frame callback's main-thread time + that frame's GPU time (timer
queries), per the Sprint W ruling. The rAF interval is beside it.

| Run | Frames | Per-frame cost p50 / p95 / p99 / max | Cost > 8 ms | GPU p95 | Script p95 | rAF interval p50 / p95 / max | First frame |
|---|---:|---|---:|---:|---:|---|---:|
| headed, vsync (120 Hz display) | 1,440 | 3.09 / **4.91** / 5.56 / 6.43 ms | 0 | 4.74 ms | 0.4 ms | 8.3 / 9.3 / 9.4 ms | 693 ms |
| headed, unthrottled | 9,512 | 1.75 / **4.00** / 4.21 / 10.29 ms | 5 | 1.82 ms | 2.3 ms | 1.9 / 2.5 / 16.2 ms | 369 ms |
| headless, 60 Hz frame clock | 720 | 2.60 / **4.28** / 4.71 / 4.99 ms | 0 | 4.00 ms | 0.6 ms | 16.7 / 16.7 / 16.8 ms | 195 ms |

Against plan section 4's budgets (8 ms on this M4 as headroom for the M1's 16.7 ms): the
per-frame cost p95 is 4.0–4.9 ms in every run; no frame's cost reached 16.7 ms; in the
unthrottled run 5 of 9,512 exceeded 8 ms (max 10.29 ms). The vsync interval never reached
16.7 ms (p95 9.3 ms is a 120 Hz display's floor plus jitter); the unthrottled interval p95,
2.5 ms, is the whole pipeline's cost of a frame including compositing the DOM layer. First
frame 195–693 ms after navigation, including Storybook's own start-up (budget 1 s). Lab
numbers on an M4 in Chrome: not the M1 target and not Safari.

## Live calls (R5)

None. No model was called; nothing was ledgered.

## Not run, blocked or open

- **Not run — requires human**: the design review scores (session W2), whether the world is
  now "as alive as Growth and Circuit", the three sounds' character ("subtle and evocative"),
  Safari, VoiceOver, a frame measurement on an M1-class Mac.
- The moving world is tested functionally in headless Chromium (SwiftShader WebGL2) and
  measured in Chrome on the M4; its look in motion has been judged only from still captures.
- The You chapter is today's chapter on glass: on a wide screen its panel still covers most of
  the world (W2C rebuilds it). The busiest scene's fifth destination sits at the window's edge
  at Roles; the app has at most three targets today.
- The first frame in the busiest-scene story includes Storybook's own start-up; the app's
  first frame after sign-in was not measured separately.
- Input-to-frame latency was not measured: W2A has no world response to typing (W2C's
  ignition).

## Paths a reviewer can skip

- `apps/web/pnpm-lock.yaml` (three and @types/three only)
- `apps/web/src/design/**` (byte-identical mirror, checked by `designMirror.test.ts`)
- `docs/design/fonts/outfit/*` (upstream binary and licence)
- `docs/design/screenshots/*.png` and `checks.md`, `docs/design/tokens/contrast-report.md`
  (generated by the tools)
- `docs/evidence/world-frames.json` (generated by `pnpm run measure-world`)
- Deleted Sprint 0 compositions and captures (`docs/design/compositions/{conversation,
  opportunity-map,route-comparison,shell}.*`, old PNGs)

---

# Fix round 1

Implementer: fresh, from `65aed2f`, per `task-W2A-fix-round-1.md` and both reviews.

## Commits

| SHA | Subject |
|---|---|
| `8b0cdf9` | Design references, fix round 1: trails measured as drawn, every light named |
| `7ac80dc` | The world in the app, fix round 1: never stuck, never black, never overwhelming |

`make check` and `make acceptance` ran on the working tree that became these two commits (no
edit after acceptance started).

## Checks run (final code)

| Command | Result |
|---|---|
| `pnpm --dir docs/design run contrast` | **120 of 120 measurements pass** (91 pairs); smallest status/meaning ΔE76 53.0 |
| `pnpm --dir docs/design run screenshots` (runs `check-data`) | check-data **64 assertions pass**; **31 of 31 captures pass** with the new checks |
| `make check` | exit 0: ruff, mypy, backend fast pytest **1511 passed**, fixture validator passed; web: client drift none, Biome clean (135 files), `tsc` clean, Vitest **33 files, 292 tests passed**, no warnings |
| `pnpm exec playwright test e2e/world.spec.ts` (targeted, before acceptance) | **10 of 10 passed** (4.1 min) |
| `make acceptance` | exit 0: integration and stack pytest **299 passed** (8 min 22 s); Storybook build; Playwright **38 passed** (5.9 min), including the 10 world tests |
| `cmp` docs/design and apps/web/src/design tokens | identical (and `designMirror.test.ts` passes) |

Mutation checks (RED shown by breaking the fix, then restored): the typing-hold test fails when
the hold's wake-up timer does nothing (1 failed); the context-loss test fails when the listener
is not attached (1 failed). Both pass with the fix.

## Each finding

### Design half (`docs/design`)

- **D-I1 synthetic label.** It left `.optional`: the strip shows it at every width above 760 px
  and the top bar below. Check: `screenshots.mjs` fails a capture without a visible "Synthetic
  demo" label (all 31 pass).
- **D-I2 openings.** Clustered tightly under the chosen destination only, one row per area; each
  count says "Manchester: 8 openings, 4 sources, today", stale counts end "…, 2 days ago", and
  an area with none says "none found in the 4 sources checked". Check: every opening dot is a
  light named by its area label (unnamed-light check).
- **D-I3 trail contrast, as ruled.** Each trail state's strength is a token
  (`--trail-opacity-usual` 0.85, `-shadow` 0.9, `-stale` 0.6; said, chosen and bridges at 1).
  `contrast.mjs` takes `alpha` (a number or an opacity token) and composites the foreground over
  the background before measuring; pairs added for usual, shadow, stale and full-strength trails
  over the ground and the horizon's glow. Tightest: shadow on the horizon 3.19:1, usual violet
  3.43:1 (the blue to violet grade, by hand, never below 3.38:1). The references read the
  tokens; the app's still world draws `TRAIL_OPACITY` (held to the tokens by `tokens.test.ts`);
  the moving world's shader draws each core at that level, with glow, flow and pulse added on
  top (additive, so at least as bright as the measured composite). Kept routes are sand, not
  slate. Known limit: in distress the world is dimmed on purpose (plan section 4), so trails
  then fall under 3:1; the words carry them.
- **D-I4 Skills.** Skills draws the ground only (the skill fan is You's). Skills, Options and
  Plan views are raised (same values in `geometry.ts`); the ground is a long S, its stretches cut
  at equal lengths on screen (position means nothing), stretch labels beside it; the gate stands
  where the last stretch begins. Check: no name, gate or key may cover any light's centre, from
  the drawing's own light list (`window.__worldCheck`).
- **D-I5 names and the key at 768 and 390.** The key is a `<details>` "What the lights mean",
  open above 1100 px, closed at or below, placed where the world is clear (above the card or
  sheet), lists only the kinds drawn, keys drawn as the world draws them (disc, ring, line,
  diamond only for a gate). Names slide along their row inside the window, step out up to 8
  rows with a leader line that never crosses a panel, avoid every light's centre, wrap when long,
  and drop their caption on a phone (the key explains it; the caption stays in the list). Check:
  every light and gate in view must have a visible name, no name may be left for a light out of
  view or under a panel, the revelation's subject must be in view and named; the key may not
  sit under a panel.
- **D-I6** Routes' key says "Teal: the route you're looking at"; "the path you chose" only at
  Plan. Failed: kept routes in sand at 0.6, no selection ring in the world or the instrument.
- **D-I7** "Total cost, including pay you'd give up" (TRACE-01's economic cost, also the
  instrument's upright axis) and "What you'd pay out" (its direct spending). DIRECTAI is not
  shown in the references; its labels are untouched.
- **D-M2** (strip rows left for W2C): "from version 14" gone; "Teal", "Grey", "Sand" in the key;
  "isn't ready yet"; "Skills checking"; "That doesn't mean there are none."; "Use this course";
  "Tell me about a skill"; the distress mechanics sentence dropped.
- **D-M3** New glyphs: support (lifebuoy), said (speech bubble), set aside (down into a tray).
- **D-M6** Failed routes: "Search again" and a "Kept from your last search" stale status;
  unknown options: "Look for a course".
- **D-M7** `--motion-breathe` 0 ms under reduced motion; the rail's fade tokenised
  (`--surface-rail` 94%, `--surface-rail-edge` 80%, raised from 60% so a chapter name at the
  edge is 7.39:1 over white); teal glows tokenised (`--glow-selection`, `--glow-action`, used in
  both trees); pairs added for the label ring and marker, the key's marks, the strip's glass and
  the rail. Tokens v0.2.1.
- **D-M8** The wordmark was forced to the 72 px link width; it now takes its own width, and the
  rail is 96 px (reference and app). Check: the wordmark must stay inside the rail.
- **D-M10** Roles "three long targets" captured at all three sizes; "Industry … by glyph" listed
  under "Not covered" (Sprint 3); "Pay not stated on N openings" read from `DESIGN_LISTINGS`.
- **D-M11** `fonts/README.md` and `dependencies.md`: Outfit's `google/fonts@8b0a1d0` committed
  2026-03-12, 232 days old when taken. Licences re-run (`pnpm licenses list`, 331 packages:
  MIT 278, Apache-2.0 17 …); lockfile 482 packages, 8 from Task W2. ADR 0014 decision 6 and
  both records: Source Sans 3 **provisional, to confirm with the product owner at session W2**.
- **D-M4 / A-M2 / ruling (distress).** Reference: Pause shows the person's own choice (off) and
  the strip says "Still while support is shown". App: see A-M2.
- **D-M9** "Why?" and the gallery's links are white and underlined.
- **D-M12 / A-M5 (frame evidence).** `measure-world.mjs` records the commit (and whether the
  tree was dirty), marks the scene synthetic, reports "WebGL GPU time" (`webglGpu`), and
  `frames.ts` pairs script and GPU samples by frame number and counts `over16_7`. **Not run**
  (its headed runs open a window on the product owner's screen). `docs/evidence/world-frames.json`
  stays the record of `65aed2f`'s run (2,400 motes); ADR 0014 decision 7 says W2D re-measures
  with the product owner warned first.

### App half (`apps/web`)

- **A-I1 typing hold.** A keystroke sets a timer that wakes the loop when the hold ends. Test:
  `World.test.tsx` "holds ambient motion while the person types, then moves again on its own"
  (the reviewer's probe, fake rAF/performance/timers): running → still at 1.4 s → running with
  nothing else happening.
- **A-I2 failure paths.** `webglcontextlost` (default prevented) and a throwing `GLWorld`
  constructor both set `failed`, ORed into `still` for the rest of the visit; the shell stays.
  `webgl2Available()` releases its probe context; `dispose()` skips `forceContextLoss()` on a
  lost context. Tests: context loss gives the still world with the same names; a renderer that
  throws gives the still world. Not done: going back to moving on `webglcontextrestored` (the
  canvas is unmounted once still).
- **A-I3 parity that can fail.** `e2e/world.spec.ts` compares, per chapter, the set of names in
  sight (`data-shown='true'`) and whether the key is in sight, across moving, reduced motion,
  calm and paused, at 1440, 768 and 390, in a new synthetic workspace with three long targets;
  at Roles it also requires "You" and a destination named.
- **A-I4 tablet and phone.** `clearArea` (pure, in `geometry.ts`) finds the span beside the
  panels on a wide screen, otherwise the taller band above or below them; `placeView` moves the
  centre only when it would sit too near the panel, and fits the place between the bars and the
  panel (smaller only if it must be). The rail is now marked `data-covers-world`. A light under a
  panel hides its name (`labels.ts`). Phone header two rows: Target and the workspace switcher
  hide below 760 px (the account menu now links "All workspaces" and names the workspace); Pause
  and Sound become glyph buttons ringed in white when on; the saved state stays. Tests:
  geometry tests for the desktop span, the resting Roles view, the tablet and phone bands and the
  no-room case; labels test for a light under a sheet; e2e asserts "You" and "Data quality
  analyst" shown at Roles at all three sizes, moving and still.
- **A-I5 not-built card.** Kicker, title, where-line, one sentence, one action; "More about this
  place" (a closed `<details>`) holds what it will hold, the starting-answer note and "Uses these
  answers from You". The second empty-state heading is gone. Tests updated on purpose: the
  "No options yet"/"No plan yet" headings no longer exist; "Less precise…" and "nothing to start
  from" are asserted visible after opening "More"; a new test asserts one heading, one link and
  the details closed. `visual.spec.ts` routes--empty now checks "Not built yet" and the
  sentence instead of "No routes yet".
- **A-I6** `.btn-quiet` is the text colour, underlined; `.btn-icon` the text colour. Links
  were not teal in the app (only in the references, D-M9).
- **A-M1** Calm mode is `CalmMode` in the account menu (same `useWorldSettings`, persistence,
  device override and words); e2e opens the account menu to toggle it and checks it is not in
  the strip.
- **A-M2** `SupportNote` reports itself through `SupportShown` (context, no-op outside a shell);
  `WorkspaceShell` passes `distress` to `World` (ORed into `still`, `data-distress`, and the same
  dim as the reference) and `supportShown` to `WorldControls` (status "Still while support is
  shown"; Pause untouched). Tests: unit (still under the panel, moving again after) and e2e
  (moving world, risk message, still + status + Pause off, dismiss, moving).
- **Atmosphere (ruling).** Horizon shimmer and trail sway removed from the shaders; motes 360.
  Breath, aurora, flow kept. Still world unchanged apart from trail strengths.
- **A-M4** `ViewTween.current` writes a reused view; uniforms written in place
  (`writeViewUniforms`); `sameView` instead of `Object.keys`; the frame object reused;
  `placeLabels` reads every size and box before writing.
- **A-M6** The `AudioContext` closes with the shell (`Sound.close()`; tested); a display-density
  change re-measures (`matchMedia` resolution); names re-place on `document.fonts` load.
- **A-M7** `sound.ts` and the Sounds story say the chime and tick have no trigger until W2C.
- **A-M8** `Place.moment` and `PALETTE.chosen` removed; comments point at `tokens.test.ts`; the
  shader colours and strengths are generated from `palette.ts`.
- **A-M9** The persistence test marks the canvas.
- **A-M10** `hasAnswered` iterates `PROFILE_FIELD_ORDER`; the calm glyph question is moot (calm
  is in the menu with its words); the interview's button is "Pause the interview" / "Resume the
  interview".

## Rulings I made

1. Distress also dims the app's world (`saturate(0.35) brightness(0.45)`), matching the
   reference and plan section 4 ("stills and dims"); the ruling asked only for still.
2. A failed moving world stays still for the rest of the visit (no restore to moving).
3. Phone strip: the saved state stays (the visual spec checks it at 390), so Pause and Sound
   lose their switch tracks on a phone and show "on" as a white ring. Target and the workspace
   switcher hide on a phone; "All workspaces" is in the account menu on every size.
4. Name placement is the same in the app and the references: centred, then slid along the row,
   up to 8 rows out each side, clear of every other light's centre, never across a panel.
5. The references' key-opened view is in the gallery only (`key=open`), not a capture: opened,
   it is a popover over names by design, which the strict checks would rightly flag.
6. Rail 96 px in both trees (the wordmark needs it).

## Not done, or done differently

- **Hard-rule slip:** one early edit to `docs/design/compositions/world.js` (six small string
  replacements: legend kinds, the Routes gate index, the next-step key) was made with a Python
  script instead of the Edit tool. Every other source change used Edit or Write; Biome's own
  `--write` formatted 7 changed files; the mirror was copied with `cp`.
- One read-only network request: the GitHub API for Outfit's commit date (no model call, no
  key). No live calls; nothing ledgered.
- `docs/evidence/world-frames.json` not re-measured (by ruling).
- The app's fixture `RoutePreview` (Sprint 1) still says "Economic cost" and "Direct spending":
  D-I7 was fixed in the references; the Routes chapter is rebuilt in Sprint 7.
- At 768 px the app's strip is still four rows (only the phone was asked for).
- At You on a wide screen one skill light can sit under the (old) You panel; its name hides.
  W2C rebuilds You.
- Requirements register not touched (W2D owns the world's family).
- Not run, requires human: design scores, the moving world's look, the sounds, Safari,
  VoiceOver, an M1.

## Paths a reviewer can skip

- `docs/design/screenshots/*.png`, `checks.md`, `docs/design/tokens/contrast-report.md`
  (generated)
- `apps/web/src/design/tokens/tokens.css` (byte-identical mirror)

# Fix round 2

Implementer: fresh, from `7ac80dc`, per `task-W2A-fix-round-2.md` and `task-W2A-rereview-1.md`.

## Commits

| SHA | Subject |
|---|---|
| `70d95e6` | Design references, fix round 2: lines join a name to its own light only |
| `c84729e` | The world in the app, fix round 2: measured trails, words on a phone, menus over the key |

`make check` and `make acceptance` ran on the working tree that became these two commits (no
edit after acceptance started).

## Checks run (final code)

| Command | Result |
|---|---|
| `pnpm --dir docs/design run screenshots` (runs `check-data`) | check-data **64 assertions pass**; **31 of 31 captures pass** with the new checks |
| `pnpm --dir docs/design run contrast` | **120 of 120 measurements pass** (91 pairs); smallest status/meaning ΔE76 53.0 |
| `cmp` docs/design and apps/web/src/design tokens | identical |
| `pnpm exec playwright test e2e/world.spec.ts` (targeted, headless) | first run 13 of 14 (the new key check failed at You, 1440: see Minor 7); after the fix **14 of 14 passed** (4.1 min) |
| `make check` | exit 0: ruff format and lint, mypy (310 files), backend fast pytest **1511 passed**, fixture validator passed; web: client drift none, Biome clean (136 files), `tsc` clean, Vitest **34 files, 299 tests passed** |
| `make acceptance` | exit 0: integration and stack pytest **299 passed** (8 min 39 s); Storybook build; Playwright **42 passed** (6.1 min), including the 14 world tests |

RED first (each new check shown failing before its fix):

- `StillWorld.test.tsx` against the old table: 3 of 4 failed (usual 0.55, shadow 0.8, opening
  0.4 against 0.85, 0.9, 0.85); all 4 pass now.
- `labels.test.ts`, the new line test: both cases failed against the old rule ("second's line
  crosses first's name", "a's line crosses b's light"); pass now. The two rewritten scenarios
  were run against the committed `labels.ts` (scratch copy, Node type stripping): the old rule
  puts `beside` three rows up with its line through `first`'s name, and `boxed in` with its
  line through the key, so both new assertions fail on it.
- `screenshots.mjs`'s new checks against the committed reference (a scratch copy of `HEAD`'s
  compositions): 22 of 31 captures fail, 77 lines crossing a light, gate or name, and the empty
  key at `you--distress--390x844`. Mutation (the key never placed): all 10 Roles captures fail
  "lights are in view but the key to the lights is not".
- `world.spec.ts`'s new key check failed on real code in the first targeted run (You,
  1440×900); fixed, and the rerun passes.
- Not shown failing first (break-it reasoning only): calm mode's words and switch at 390, the
  menus over the key, the phone's support status, marks on long names. Undo the CSS scope and
  the portal, and the calm test reads a 1×1 hidden label and a `display: none` switch. Undo the
  portal, and `elementFromPoint` returns the key (z-index 5 at the root, the menus inside
  `.app`'s z-index 1). Keep the status in the strip, and the strip grows a row. Put the disc
  back on the label's flex line, and a wrapped name's label is a line taller than the name.

## Each item

### Important: the app's still world draws trails at their measured strengths
- `StillWorld.tsx` draws each trail's core from `TRAIL_OPACITY`; its own `OPACITY` table is gone.
  Test: `StillWorld.test.tsx` renders `StillWorld` with one trail per state and asserts every
  core stroke's `stroke-opacity` equals that state's `TRAIL_OPACITY`.
- Records now true: `docs/design/README.md` (Tokens and contrast), ADR 0014 decision 7,
  `palette.ts`; each also carries the distress exception (Minor 5).

### A-M1 / A-M10: calm mode on a phone
- The phone rules that make the strip's world controls glyph buttons are scoped to
  `.world-controls` (`globals.css`), so calm mode in the account menu keeps its words and its
  switch. The menus also open through a portal now (Minor 3), so the account menu is no longer
  inside the strip.
- Check: `world.spec.ts` "phone › calm mode in the account menu keeps its words and its switch"
  (390×844: the words wider than 40 px, the switch visible).

### Minor 1: lines from names never cross another light or name
- Both trees: a spot is rejected when the line it would draw (a name more than 20 px from its
  light) meets another light's centre, a gate, a name already placed or the key; no name may sit
  on a line already drawn. `LEADER_FROM` moved into `labels.ts`; `World.tsx` imports it.
- Checks: `screenshots.mjs` measures each drawn line from the page (the label's `::after`) and
  fails it across another light, gate, name or the key; `labels.test.ts` "never draws a line
  from a name across another light or name" (two cases).
- What it took. The strict rule left crowded scenes with no legal spot, so the existing "every
  light in view is named" check failed until these were added, in both trees:
  - more spots along a row (the light at the name's very end, 8 px in);
  - names are measured, then placed, then written; a name left without a spot chooses first
    on the next try (up to 6), and the try leaving the fewest lights unnamed is kept;
  - the key tries more spots (right: low, above a panel, just below the bars; then the same at
    the left) and takes the first from which every light can still be named.
- References only, at Roles:
  - The openings stand just in front of the chosen destination, under it as Roles sees it.
    Before, perspective pulled them left, over the card.
  - They sit tighter (0.5 apart). Their names step down from the rightmost, each starting just
    left of its own lights, so each line passes the names above it.
  - The Roles card is 480 px (ruling 2).
  - On a phone the three areas stood a few pixels apart, with no legal spot for their names.
    The phone's sheet now lists each area's openings in the world's words (ruling 1).
- `labels.test.ts`: two tests changed on purpose.
  - "Never lets two names overlap" had five lights at almost one point, all named by stacking
    rows above. That needs lines through the names below. It now has four lights that exercise
    sliding, stepping out with a clear line and taking the other side, with exact spots.
  - "Never covers another light's centre, or the key" moved its second light so the first has
    a legal spot, and now asserts both are placed.
  - A new test asserts a name boxed in by the key and a light is hidden rather than drawn
    across.

### Minor 2: a long name keeps its mark on its first line
- Both trees: the destination's disc (and the suggested ring) is the name's own `::before`,
  inline before its text, not a flex item of the label (`world.css`, `globals.css`).
- Check: `world.spec.ts`'s parity test at Roles (three long targets, three sizes) fails any
  shown name whose label is taller than the name (a mark on a line of its own). Captures
  `roles--three-targets--*` show it.

### Minor 3: the key sits under the menus
- The workspace, account and chapter menus render through `Popover.Portal`. Its wrapper takes
  the menu's z-index 30 at the root, over the key's 5.
- Checks: `world.spec.ts` "the menus open over the key to the lights" (1440: workspace and
  account) and "phone › the chapter menu opens over the key" (390). The key is stood where the
  menu is, and `elementFromPoint` must land in the menu.

### Minor 4: stale coverage
- `world.js`: in the stale state today's counts say the sources that answered ("Remote: 3
  openings, 3 sources, today"). The kept counts say the search of two days ago ("4 sources, 2
  days ago"). Counts and words live in one place (`AREAS`), used by the world and the phone's
  sheet.

### Minor 5: the distress dim (controller ruling)
- Recorded as the one exception wherever "3:1 as drawn" is claimed:
  - `docs/design/README.md` and ADR 0014 decision 7;
  - `contrast-pairs.json` ("about") and the contrast report's method (`contrast.mjs`);
  - `tokens.css` (both copies, comment only) and `palette.ts`.

### Minor 6: distress on a phone
- Both trees: "Still while support is shown" sits in the strip, or on a phone in the top bar
  beside the chapter. It wraps there; the other copy is `display: none`. In the app,
  `StillWhileSupport` (`WorldControls.tsx`) is used by the strip and by `WorkspaceShell`'s top
  bar.
- Check: `world.spec.ts` "phone › the support status sits in the top bar and adds no row to the
  strip" (the strip keeps its height). Capture `you--distress--390x844`.
- Both trees: the key shows only while something it explains is in view. In the references
  that is a light other than the person's, a gate or a trail; in the app, a destination's light
  or a grey trail.
- Check: `screenshots.mjs` fails a key shown with nothing it explains in view.

### Minor 7: the key cannot vanish unnoticed
- `screenshots.mjs` fails a capture where a light the key explains (or a gate) is in view and
  the key is not seen. `world.spec.ts`'s layout test fails when names are in view and the key
  is not placed.
- The check found a real gap in the app. At You, 1440×900, the world beside the wide panel is
  about 270 px, too narrow for the open key, so the key was always hidden. It is now open only
  where the world beside the panels has room for it (360 px or more), and otherwise is "What the
  lights mean", closed (ruling 3; both trees).

### Minor 8: three targets in the strip
- `world.js`: in the three-targets state the strip names P01's target and the two long invented
  ones, as the app's strip names every target.

### Minor 9: the two unreported `world.js` changes of round 1, and routes' own state
- Recorded:
  1. Round 1 removed Plan's month-by-month teal landmarks along route B; only the next step
     stays lit. Plan section 4 lights landmarks from "real-world progress", so teal marks for
     months not yet reached would show progress that has not happened.
  2. Round 1 drew unselected routes in the "said" state, to get full strength.
- Fixed: unselected routes have their own state, `route`. Its core is full strength (measured
  by the full-strength pairs, whose words now name whole routes) with the quiet glow of a
  usual trail, not said's bright one.

## Rulings I made

1. **Openings on a phone go in the sheet.** At Roles the phone lists the chosen destination's
   openings by area, in the world's own words (count, sources, date), instead of drawing them.
   The three areas stood a few pixels apart, and no placement could name them without a line
   across another name or light. Wider screens still draw them.
2. **The Roles card is 480 px wide** (was 560), so the openings' names fit beside it at 1440 when
   the card is tall (stale, unknown).
3. **The key opens only where there is room.** On a wide screen it is open only where the world
   beside the panels has 360 px or more, in both trees; otherwise it is "What the lights mean",
   closed.
4. **One placement rule in both trees.** The name retries and the key's wider set of spots are
   in both, so the app and the references still place names by one rule.
5. **A whole route glows quietly.** Its core is full strength with a quiet glow; only said,
   chosen and bridges glow brightly.
6. **The phone's support status may wrap** to three short lines in the top bar at 390 px; it
   adds no row.

## Not done, or done differently

- Every source edit used Edit or Write. Scratch-only copies of the reference (in the session
  scratchpad) were patched with `python3` and `sed` to log why a name was rejected and to run
  mutations. Nothing there is committed.
- Not run, requires human: design scores, the moving world's look, the sounds, Safari,
  VoiceOver, an M1, and the product owner's view of the narrower Roles card and the phone's
  openings list (session W2).
- `scripts/measure-world.mjs` not run (as ruled). No web requests and no model or live calls;
  nothing ledgered.
- Requirements register not touched (W2D owns the world's family).

## Paths a reviewer can skip

- `docs/design/screenshots/*.png`, `checks.md`, `docs/design/tokens/contrast-report.md`
  (generated)
- `apps/web/src/design/tokens/tokens.css` (byte-identical mirror)
