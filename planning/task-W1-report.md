# Task W1 report: the spike of three directions

Status: DONE_WITH_CONCERNS (concerns at the end; none blocks session W1).
Branch `l0-local-release`, base da25020. Commits:

- `cec21cd` Add the world spike: three directions (Growth, Horizon, Circuit) for session W1
- `62b060d` Add session W1's package: how to try the three looks, and the questions to answer

## What was built

A throwaway, playable spike in `spikes/world/`, started from the repository root with
`make spike-world` (installs the locked packages, builds, serves on `http://127.0.0.1:53300`
on loopback only, opens the chooser). Labelled a spike in its README, on the chooser and in every
direction's footer; the made-up data is labelled on every screen.

- **Chooser** (`/`): the three directions, one line each, plus the spike label.
- **Growth** (`?d=growth`): organic first. Tapered, wobbling roots and nerves grown from the
  person, fine side fibres (atmosphere), an ambient pulse that beats outward through the whole
  network, spores drifting up, an ignition shockwave.
- **Horizon** (`?d=horizon`): journey first. A perspective plain (ground grid computed per pixel)
  under a glowing horizon and stars, like the reference image; trails run on the ground and rise
  into the destination lights, which are reflected on the plain; the first answer travels from a
  close view of the person to the overview, the revelation travels a short way out and a column
  of light rises from the newly lit destination; motes drift towards the viewer.
- **Circuit** (`?d=circuit`): cybernetic first. Orthogonal traces with rounded corners on an
  instrument dot grid with a slow scan band; light travels as packets; square vias, diamond
  terminals; the revelation locks on with closing brackets; readouts in JetBrains Mono.

All three share one story, one scene model and one DOM layer, so the words are identical:

1. Dark world, one light, the question "What do you do now, or what did you do last?" with
   type-ahead over the labelled made-up list (combobox, keyboard and pointer). Each keystroke
   brightens the light at once. No match: "Nothing in this example list matches … Try a shorter
   job title", never an invented match.
2. The first answer ignites the origin and grows the 8 skills that job usually needs ("usual in
   your role, not confirmed yet": faint ring) and a first scatter of up to 5 destinations
   (orange), joined by the skills they share. No model call.
3. 2.4 s later the revelation is staged over 1.8 s (ambient motion holds; any input completes
   it): a destination in another field lights up, joined by the shared essential skills; the
   destination's other skills appear in shadow (dashed slate, "Not known yet"). Card: "Chefs and
   firefighters share 5 essential skills." / different field, you didn't name it, linked by
   skills not title words / Not known yet: 3 more skills … / "A place you could head for. Not a
   job offer." / **Why?** (one step away: the five shared skills with the person's state for each,
   and the source: "the made-up example list in this preview. Code counted the skills both jobs
   list. Nothing was guessed.") / primary action **Keep firefighter in view** (teal path, lock-on
   ring) with **Undo** (white outline, worded and coloured differently).
4. Clicking a skill marks it "you said so" (bright, filled); its trails brighten everywhere.

Also: still version (SVG, no WebGL) for the OS reduced-motion setting, the Calm mode button and
browsers without WebGL2; a visible Pause control; off-by-default synthesised sound (WebAudio, no
files); Spike tools (heading typeface switcher, busiest scene); measurement mode (`&measure=1`);
the busiest scene (`&scene=busy`: 100 made-up openings with their trails); the library comparison
bench (`/bench/?lib=three|pixi|ogl`).

Session package: `docs/reviews/session-w1.md` (plain words, action first, time estimate, how to
start, two minutes in each look, six questions including which look or mix in their own words
and whether sound is wanted; no scores) with 11 screenshots in `docs/reviews/session-w1/`.

### Files

- `Makefile`: `spike-world` target, header line, `.PHONY`.
- `spikes/world/`: `package.json`, `pnpm-workspace.yaml` (`minimumReleaseAge: 20160`),
  `pnpm-lock.yaml`, `tsconfig.json`, `vite.config.ts`, `index.html` (CSP `'self'` only),
  `.gitignore` (`dist/`), `README.md` (how to run, truth rules, checks, frame table, library and
  typeface comparison, dependency table with publish dates, known limits).
- `spikes/world/src/`: `data.ts` (made-up list, labelled), `model.ts` + `model.test.ts` (the
  deterministic source of the revelation), `story.ts` (what happened and when), `scene.ts` and
  `direction.ts` (shared scene model and builder), `directions/growth.ts`, `horizon.ts`,
  `circuit.ts` (geometry, view, GLSL, still backdrop), `gl.ts` (three.js world layer), `still.ts`
  (SVG still world), `app.ts` (DOM layer, loop, modes, label placement, measurement), `sound.ts`,
  `frames.ts`, `main.ts` (chooser), `styles.css`.
- `spikes/world/bench/`: `scene.ts` (identical workload), `three.ts`, `pixi.ts`, `ogl.ts`,
  `main.ts`, `index.html`.
- `spikes/world/tools/`: `check.mjs` (acceptance), `measure.mjs` (frames), `bench.mjs` (library
  comparison), `screenshots.mjs` (session package).
- Evidence: `spikes/world/measurements.json`, `spikes/world/bench-results.json`.
- `docs/reviews/session-w1.md`, `docs/reviews/session-w1/*.png` (11 files, 4.0 MB).

Paths a reviewer can skip: `spikes/world/pnpm-lock.yaml`, `spikes/world/measurements.json`,
`spikes/world/bench-results.json`, `docs/reviews/session-w1/*.png`.

## Rulings I made, and why

1. **Location and command.** `spikes/world/` (outside `apps/web/src`, `docs/design`, `backend`;
   no product check globs it); `make spike-world` = `pnpm install --frozen-lockfile && pnpm run
   start` (`vite build && vite preview --host 127.0.0.1 --port 53300 --strictPort --open`). A
   production build is served, not the dev server, so what the product owner sees is what was
   measured.
2. **Made-up list, not the ESCO sample.** The labelled `fixtures/esco-sample` keeps only the
   first 6 essential skills per occupation; across its 30 occupations the only overlaps of 4 or
   more are near-twins (bookkeeper/accounting assistant, bus/trolley bus driver, help desk
   agent/manager), so it cannot support an honest unexpected connection. I wrote a 31-job,
   51-skill list in plain words (`src/data.ts`), labelled "Made-up example data: a small invented
   list of jobs and skills." on every screen and in the file header.
3. **The revelation's rule** (`src/model.ts`, tested): a job in a different field, sharing no
   word with the person's title, with the most shared essential skills, at least 4, ties broken
   by title; none qualifies, no revelation. First scatter: up to 5 other jobs with at least 3
   shared skills, chosen by count, then placed in title order so position never means rank. The
   sentence is built from computed facts and never mentions the person ("Chefs and firefighters
   share 5 essential skills.").
4. **Unexpected = held back.** The revealed destination is excluded from the first scatter and
   lights up at the revelation ("a destination the person never named lights up").
5. **The revelation arrives on its own**, 2.4 s after the first answer (so the first ten seconds
   include it), staged over 1.8 s, ambient held; any key or pointer input completes it at once.
6. **States drawn**: usual (faint ring), said (bright fill), shadow (dashed slate), chosen (teal
   path and lock-on ring, only after "Keep … in view"). Teal appears only as selection, the kept
   path and the primary action; orange only for destinations; blue to violet is graded by distance
   from the person along every trail.
7. **The shadowed skills share one label** ("Not known yet / 3 more skills firefighters need"),
   with their names in the card, in all three directions. Per-skill labels crowded Horizon's far
   field; one group label keeps the words identical across directions.
8. **Still version** is SVG with no WebGL (also the fallback without WebGL2). The OS
   reduced-motion setting always wins (the Calm button then shows pressed and disabled, with a
   reason). Travel becomes a cut; the card appears with the revelation, without its delay.
9. **Pause** stops ambient motion (and the render loop once nothing animates); responses to the
   person's input (under 2 s) still play. Ambient motion also stills while typing, while the
   pointer is over the console or card, and during the revelation; it stops when the tab is
   hidden (requestAnimationFrame).
10. **Announcements** go to a screen-reader-only live region; the same words are on screen in the
    console ("Chefs usually need these 8 skills.") and the card.
11. **Labels** are DOM buttons and list items over the world (the exact layer), placed by a small
    heuristic that scores 16 offsets per label against panels, lights and placed labels, only
    while the view is at rest.
12. **Measurement** (dispatch method, plus two additions explained below): headed system Chrome,
    real GPU, renderer string recorded; busiest scene = 100 made-up openings with their trails,
    all destinations, the kept path and ambient particles, with the revelation (and Horizon's
    travel) replayed every 4 s; 3 s warm-up, 12 s of rAF deltas. Added: GPU time per frame via
    `EXT_disjoint_timer_query_webgl2` (available in this Chrome by default) and main-thread time
    per frame, because a vsync-locked delta cannot go below 8.33 ms on this 120 Hz display; and an
    unthrottled run (`--disable-gpu-vsync --disable-frame-rate-limit`).
13. **WebGL library**: the spike is built on three.js; three.js, PixiJS and OGL were compared on an
    identical workload (same shaders and geometry). Recommendation: three.js (below).
14. **Typefaces**: Fontsource variable packages (OFL-1.1, licence text in each package, served
    from 127.0.0.1); candidates Outfit, Sora, Unbounded; each direction defaults to one (Growth
    Outfit, Horizon Unbounded, Circuit Sora) and Spike tools switches any face onto any direction.
    Body Atkinson Hyperlegible Next, readouts JetBrains Mono. Recommendation: Outfit.
15. **Sound**: synthesised WebAudio cues for the first answer, the revelation and a skill touch;
    off until the Sound button is pressed (which also satisfies the browser's gesture rule).
16. **Phone width** made usable (no horizontal overflow at 390 px, panels as sheets) but not
    designed: phones get their own layout in W2.
17. **Evidence committed**: `measurements.json` and `bench-results.json` in the spike, so the
    numbers in the README trace to raw data. Dependencies are listed in the spike's README, not
    `docs/dependencies.md` (dispatch ruling).
18. **Browser tooling** uses system Google Chrome through Playwright's `channel: "chrome"`, so the
    spike downloads no browser. `playwright` 1.64.1 is the version `docs/design` already pins.
19. **No ADR or register change.** ADR 0014's status line says Sprint W adds the spike's choices
    once session W1 has made them; the register has no world family yet (SW.6, Task W2).
20. Removed a copied `ignoredBuiltDependencies: esbuild` rule: esbuild is only Vite's optional
    peer here and is never installed.

## Checks run (on the final code)

| Command | Result |
|---|---|
| `cd spikes/world && pnpm test` | 14 tests, 14 pass, 0 fail (Node test runner, no warnings) |
| `pnpm typecheck` (strict, `noUncheckedIndexedAccess`) | clean |
| `pnpm exec tsc --noEmit --noUnusedLocals --noUnusedParameters` | clean |
| `pnpm build` | clean (chunk-size warning limit raised to 800 kB with a comment; three.js is 525 kB) |
| `node tools/check.mjs` (against the server started by `make spike-world`) | all passed: for each direction, moving / reduced motion / calm modes; world answered the first answer after 285–311 ms (typing included); card shown after about 4.6 s; revelation sentence in the DOM; its evidence (five shared skills and source) in the DOM behind Why?; card states uncertainty and "Not a job offer"; data and spike labelled; words identical with reduced motion and with calm mode (console, labels, card, legend, footer); skill toggle, keep in view and undo from the keyboard; pause works; no request left 127.0.0.1 (all modes, chooser, busiest scenes); no page errors |
| `node tools/measure.mjs` | table below |
| `node tools/bench.mjs` | table below |
| `make spike-world` | installs (frozen lockfile), builds, serves, opens the chooser; `/` and `/?d=growth` return 200; stopped afterwards |
| `make check` (repository root) | exit 0: ruff format (308 files), ruff lint, mypy (308 files), pytest 1485 passed / 299 deselected, fixture validator passed, web client drift check, Biome (110 files), `tsc`, Vitest 25 files / 212 tests passed. The product is untouched. |
| Lockfile publish dates | every resolved version (71 packages incl. platform binaries) checked against the npm registry: all published on or before 2026-10-16 |

TDD evidence for the domain logic (`src/model.ts`):

- RED: `pnpm test` with `model.test.ts` written and no `model.ts`: 1 failing (module missing).
  Before implementing I corrected one expectation of my own that contradicted the ranking rule
  stated in the next test ("Nursery worker" starts with "nurse", so it ranks before "Dental
  nurse").
- First GREEN run: 11 of 14 pass; the 3 failures were the data-coverage test (Secondary school
  teacher, Plumber, Carpenter, Delivery driver, Barista and Events coordinator had no connection
  of at least 4). I tuned five rows of the made-up list (not the rule); then 14 of 14.

Live calls: none. No Meta key read, no model call, no `.env` or `~/.careerwright` access.

## Frame times (busiest scene, final code)

Apple M4, 16 GB (Mac16,1), macOS 27.0, Google Chrome 156.0.8078.76, headed, WebGL renderer
`ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)`. 1440×900 window (1440×809
CSS px inside), DPR 2, canvas 2880×1618. 3 s warm-up, 12 s sample.

| Direction | Run | Frames | rAF p50 | rAF p95 | Frames ≥ 16.7 ms | Main thread p95 | GPU p50 | GPU p95 | First frame | Keystroke to frame (max) |
|---|---|---|---|---|---|---|---|---|---|---|
| Growth | vsync | 1441 | 8.3 ms | 10.0 ms | 0 | 0.2 ms | 2.5 ms | 5.5 ms | 95 ms | 9.5 ms |
| Horizon | vsync | 1439 | 8.3 ms | 10.1 ms | 0 | 0.2 ms | 2.1 ms | 3.2 ms | 91 ms | 8.1 ms |
| Circuit | vsync | 1439 | 8.3 ms | 10.1 ms | 0 | 0.2 ms | 1.1 ms | 2.5 ms | 91 ms | 7.5 ms |
| Growth | unthrottled | 10147 | 0.2 ms | 2.8 ms | 5 | 2.5 ms | 1.2 ms | 1.9 ms | | |
| Horizon | unthrottled | 10309 | 0.2 ms | 2.8 ms | 5 | 2.5 ms | 1.3 ms | 1.9 ms | | |
| Circuit | unthrottled | 10374 | 0.2 ms | 2.8 ms | 5 | 2.6 ms | 1.2 ms | 1.9 ms | | |

Against the budgets (plan section 4): first frame 91–95 ms (budget 1 s): met. Input feedback at
most 9.5 ms (budget 100 ms): met. p95 within 8 ms: the per-frame cost (GPU p95 2.5–5.5 ms,
main thread 0.2 ms) is within 8 ms; the vsync rAF-delta p95 is 10.0–10.1 ms, which is above 8 ms
only because this display refreshes at 120 Hz (8.33 ms floor) and presentation jitters around
it; no frame reached 16.7 ms, so none was dropped. An earlier run on slightly earlier code gave
rAF p95 9.2–9.3 ms and GPU p95 2.2–3.9 ms (variance in GPU clocks between runs). Unthrottled maxima
(23–31 ms) are stalls of the unthrottled browser. Safari and an M1: not measured.

## The WebGL library comparison

Identical workload (backdrop, 140 glowing trails, 130 instanced lights, 2,400 particles, all
additive; same GLSL, geometry and draw order), same machine and browser; first frame is the
median of 3 runs in rotation.

| Library | Version (published) | Licence | JS shipped (gzip) | First frame | rAF p95 (vsync) | Main thread p95 | GPU p95 | Monthly npm downloads |
|---|---|---|---|---|---|---|---|---|
| three.js | 0.186.1 (2026-09-24) | MIT | 131 KB (523 KB raw) | 95 ms | 10.3 ms | 0.2 ms | 3.1 ms | 88.4 M |
| PixiJS | 8.22.0 (2026-10-01) | MIT | 131 KB (446 KB raw) | 102 ms | 10.2 ms | 0.2 ms | 2.9 ms | 5.4 M |
| OGL | 1.0.11 (2025-01-27) | Unlicense | 17 KB (53 KB raw) | 73 ms | 10.2 ms | 0.2 ms | 3.9 ms | 3.0 M |

Frame cost is the same within noise; the choice rests on fit and risk. **Recommendation:
three.js 0.186.1.** Raw GLSL 3 works as written (`RawShaderMaterial`); a real 3D camera is there
for depth and travel; by far the most used and steadily released (13 releases in the past year,
two npm maintainers); a WebGPU path. Costs found: the largest bundle (its built-in shader library
ships even unused), and its default back-face culling silently hid half the screen-space geometry
(y-down projection flips winding) until both faces were drawn: W2 should keep `DoubleSide`.
PixiJS: fails under a CSP without `unsafe-eval` until `pixi.js/unsafe-eval` is imported, and
compiled shaders without a `#version` line as WebGL1 GLSL; built for 2D sprites. OGL: smallest
and closest to raw WebGL, but one npm maintainer and no release since January 2025.

## The display typeface comparison

All OFL-1.1, self-hosted (Fontsource 5.3.0, published 2026-07-19). Sheet:
`docs/reviews/session-w1/4-typefaces.png`.

| Face | Character | Long job names in the card |
|---|---|---|
| **Outfit (recommended)** | Round geometric, closest to the bold white type in the reference image | Narrowest: the longest sentence takes 4 lines |
| Sora | Wider, technical; suits Circuit | 5 lines |
| Unbounded | Wide, game-title feel | Needs a smaller size (22 px vs 27 px) and still 5 lines |

Body: Atkinson Hyperlegible Next. Readouts: JetBrains Mono. The question asked at session W1
offers Outfit for the product owner's yes or no.

## Agent pre-review (not the required human review; no scores)

- Growth reads most "organic"; the outward pulse gives the network a heartbeat. With five
  destinations the reach trails cross a lot, which can look tangled rather than grown.
- Horizon is closest to the reference image and has the strongest sense of travel; perspective
  squeezes the far field, so labels along the horizon are the most crowded of the three, and the
  revealed light, being farthest, is small once settled.
- Circuit is the most legible and orderly, and the lock-on is the clearest single moment; it is
  the least organic and the most at risk of reading as a technical diagram.
- All three: the first screen is one question and one light; the card is long (about 70 words
  before Why?).

## Not run, blocked or out of scope

- Not run — requires human: the product owner's choice and any design scoring (session W1),
  VoiceOver, real Safari, an M1-class Mac.
- Not run: axe and contrast measurement on the spike (W2 measures the chosen direction's tokens,
  including panels over the brightest light, per SW.2).
- Out of the spike: the distress response, returning visits, the overlooked-strength revelation,
  every chapter beyond the first moments, a designed phone layout.

## Concerns

1. **The 8 ms budget on a 120 Hz display.** Read literally as "p95 rAF delta ≤ 8 ms" it cannot
   be met on this Mac by any scene (floor 8.33 ms); measured p95 is 10.0–10.1 ms with no dropped
   frame, and the frame cost is 2.5–5.5 ms (GPU p95). I report it as met on cost, not on the
   literal delta; the controller should rule which reading the plan intends.
2. Label placement is a heuristic; in Horizon, labels near the horizon still sit close together
   at 1440×900, and other window sizes were only spot-checked.
3. The measurements opened visible Chrome windows on this Mac, and testing `make spike-world`
   opened a browser tab at `http://127.0.0.1:53300` (the server is now stopped, so that tab
   shows an error until the spike is started again).
4. Scratch scripts for my own visual review lived in the session scratchpad (outside the
   repository) and were written with shell heredocs; no repository file was written that way
   (repository files were changed with Write and Edit only). Commit messages were passed to git
   on standard input.

---

# Fix round 1 report

Commits: `1c375b3` World spike, fix round 1: one idea at a time, the question in the world,
stronger looks; `1d0a4b3` Update session W1's package for fix round 1: Chrome up front, every
sound named. Repository files changed with Write and Edit only; explicit staging; `answers-2.md`
untouched.

## Changes, item by item

1. **Words no longer vanish after a toggle.** Each label's entry animation now plays once
   (`data-shown` set on `animationend`, at creation when already born or still, and on every
   change of mode); CSS animates only `.node-label:not([data-shown])` (`src/app.ts` `ensureLabel`,
   `applyMode`; `src/styles.css`). Labels are created once and updated in place, so focus and
   hover also survive rebuilds. Covering test: `tools/check.mjs` now turns Calm mode on and off,
   and the system's reduced motion on and off (`page.emulateMedia`), then requires every world
   label to have no running animation and opacity at least 0.59. **Red first:** run against the
   old build (commit 62b060d, built in a scratch worktree outside the repository and served on
   the same port) it printed `FAIL words vanished after calm mode was turned off` and `FAIL words
   vanished after reduced motion was turned off`; on the new build both pass in all three looks.
2. **No decorative teal.** Circuit's panel corner ticks are blue; focus rings are white (not
   teal); the input caret and underline are white or blue. Teal remains on the primary button,
   the selected type-ahead option, the kept destination's label border and lock-on ring, and the
   kept path. Covering test: `tools/check.mjs` scans every element and its `::before`/`::after`
   in the revealed state and requires teal on the primary button only (passes in all three).
3. **One idea at a time.** After the first answer the skills speak and destinations are quiet
   (60% opacity, names only); after the revelation only the revealed destination, the shared
   skills and the one shadow label speak. Captions ("usual in your role, not confirmed yet", "N
   shared skills") are visually hidden and appear on hover and focus (still in each control's
   accessible name); the ring glyph plus one legend line carries "usual"; legend lines appear when
   their state first appears (usual, then said, then dashed; the orange line is gone). Each
   destination grows one quiet trail from its nearest shared skill; pointing at it or focusing it
   (destination labels are now buttons; click pins it for touch) lights all its shared skills
   (`src/direction.ts` `buildScene`, `src/story.ts` `point`). The card is shorter (about 50 words
   before Why?; the unknown skills' names moved behind Why?). The question is hidden visually
   once answered; the header is quiet text; the footer is smaller. Words stay equal in moving and
   still (checked). Covering test: `tools/check.mjs` focuses a destination and requires
   `aria-pressed="true"` and its caption shown; words-equality checks still pass.
4. **The first screen and the chooser are the world.** The question sits in the world beside
   the person's light (`--ox/--oy` from the projected origin): Growth beside a seed whose
   tendrils reach further with every keystroke; Horizon floating above the light on the plain,
   each keystroke sending a ripple across the ground; Circuit as a prompt (`>`, monospace) beside
   a core in a socket whose stub traces carry a packet per keystroke (new `uTyped` uniform; the
   keystroke flash stays). No pill box: each look draws its own line under the answer, which
   brightens and thickens on focus. The chooser (`src/main.ts`) is a world: the person's light
   below, a trail rising to each look's lit doorway drawn in that look's way (root, plain,
   circuit trace), the pointed trail brightening; flowing dashes stop under reduced motion. Same
   words and interaction in all three.
5. **Each look strengthened.** Growth: one quiet trail per destination (no tangle), gentle sway
   along every trail (zero at both ends, atmosphere), warm orange cores (no near-white), the
   revealed light keeps a wider steady glow. Horizon: the ruled grid is gone for a smooth dark
   plain with mist, a horizon band and reflections; labels never float free: the label pass
   (`settleLabels`) draws a fine leader line from any label placed away from its light; the
   revealed destination keeps a steady column of light (moving and still). Circuit: rebuilt as a
   living board: the core with skills as pads on a ring around it, destinations as terminals on
   one outer arc, traces at right angles and 45°, faint micro-traces across the board lit by the
   scan, packets on the traces, the lock-on kept.
6. **Horizon depth means nothing.** Every destination, the revealed one included, stands at
   depth 17; the revelation takes the centre of the horizon (a fixed layout slot) and is singled
   out by its column of light; every skill sits on one arc at the same distance from the person.
   Circuit likewise: pads on one ring, terminals on one arc.
7. **Chrome, not the default browser.** `pnpm start` sets `BROWSER=tools/open-chrome.js`; Vite
   runs it with the address and it calls `open -a "Google Chrome"` (no AppleScript, so no
   permission prompt), printing a plain fallback if Chrome is missing. Verified: after
   `make spike-world`, `lsof` showed Google Chrome processes connected to 127.0.0.1:53300. The
   package says Chrome up front, and why.
8. **One heading face by default** (`DEFAULT_FONT = "outfit"`; the per-direction `font` field is
   removed). Spike tools still switches; the package keeps lettering as its own question.
9. **Measurement labels.** `cpu` is renamed `script` and documented as time inside the frame
   callback; the README cites the unthrottled interval as the whole-pipeline figure; GPU p99 and
   GPU frames over 8 ms are reported; first frame is given for the normal entry and the busiest
   scene; input to frame is measured for keystrokes on the normal entry and for skills picked in
   the busiest scene. Re-measured on the round-1 build (table below). The library bench was not
   re-run: its workload and code did not change.
10. **Dead code**: `Story.onChange`, `emit` and the listener set are removed.
11. **Toggles**: fixed labels ("Pause motion", "Calm mode", "Sound") with `aria-pressed` and a
    switch drawn in CSS; labels no longer change. `tools/check.mjs` checks pause's fixed label and
    pressed state.
12. **Sound question** names all three cues: the swell (light on), the chime (connection), the
    tick (skill picked).

Also: the measurement readout no longer takes pointer events (it blocked the new busiest-scene
clicks); a destination being pointed at redraws the world without re-placing the words (avoids a
hover feedback loop).

## Commands and output (final code)

| Command | Result |
|---|---|
| `pnpm test` | 14 tests, 14 pass, 0 fail |
| `pnpm typecheck`; `pnpm exec tsc --noEmit --noUnusedLocals --noUnusedParameters` | clean; clean |
| `pnpm build` | clean |
| `node tools/check.mjs` against the old build (62b060d) | `FAIL words vanished after calm mode was turned off`, `FAIL words vanished after reduced motion was turned off` (then it stopped at the new destination buttons, which the old build lacks) |
| `node tools/check.mjs` against the server started by `make spike-world` | all passed, 55 checks (18 per look plus the chooser and busiest scenes), run twice |
| `make spike-world` | installs, builds, serves, opens Google Chrome (Chrome processes connected to 127.0.0.1:53300); stopped afterwards |
| `node tools/measure.mjs` | table below |
| `node tools/screenshots.mjs` | 11 PNGs rewritten in `docs/reviews/session-w1/` (3.6 MB) |
| `make check` | exit 0: 308 files formatted, ruff clean, mypy clean (308 files), pytest 1485 passed / 299 deselected, fixture validator passed, web client drift, Biome, `tsc`, Vitest 212 passed |

## Frame times, round-1 build

Apple M4, 16 GB (Mac16,1), macOS 27.0, Google Chrome 156.0.8078.76, headed, ANGLE Metal on the
Apple M4; 1440×809 CSS px at DPR 2 (canvas 2880×1618); busiest scene; 3 s warm-up, 12 s.

| Look | Run | Frames | Interval p50 | Interval p95 | Intervals ≥ 16.7 ms | Script p95 | GPU p50 | GPU p95 | GPU p99 | GPU frames > 8 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Growth | vsync | 1440 | 8.3 | 10.1 | 0 | 0.2 | 2.89 | 3.91 | 4.36 | 0 |
| Horizon | vsync | 1440 | 8.3 | 10.1 | 0 | 0.2 | 2.34 | 3.23 | 3.73 | 0 |
| Circuit | vsync | 1440 | 8.3 | 10.0 | 0 | 0.2 | 1.22 | 2.57 | 3.63 | 0 |
| Growth | unthrottled | 10254 | 0.2 | 2.8 | 4 | 2.5 | 1.21 | 1.83 | 1.96 | 0 |
| Horizon | unthrottled | 10262 | 0.2 | 2.8 | 0 | 2.5 | 1.25 | 1.86 | 2.06 | 0 |
| Circuit | unthrottled | 10317 | 0.2 | 2.8 | 0 | 2.6 | 1.17 | 1.88 | 2.12 | 0 |

| Look | First frame, normal entry (median of 3) | First frame, busiest scene | Keystroke to frame, normal entry (max) | Skill picked to frame, busiest scene (max of 5) |
|---|---|---|---|---|
| Growth | 110 ms | 182 ms | 8.0 ms | 5.5 ms |
| Horizon | 80 ms | 113 ms | 9.1 ms | 4.5 ms |
| Circuit | 96 ms | 103 ms | 82.6 ms (max of 11; median 5.8 ms) | 8.7 ms |

Under the controller's ruling (8 ms = per-frame cost): met. Whole-pipeline unthrottled interval
p95 2.8 ms; GPU p99 at most 4.4 ms with no GPU frame over 8 ms (the earlier Growth p99 of
8.55 ms did not persist); script p95 0.2 ms. First frame within 1 s; input feedback within
100 ms. Circuit's single 82.6 ms keystroke did not recur: a repeat of 24 keystrokes in headed
Chrome (scratch script) peaked at 8.4 ms.

## Concerns after round 1

1. While verifying item 7 I first ran `osascript` to read Chrome's active tab; it waited,
   probably on a macOS automation permission prompt ("… wants to control Google Chrome"). I
   stopped it and verified with `lsof` instead. If that prompt is on screen, it can be denied;
   the spike itself never uses AppleScript.
2. Captions now appear on hover and focus; a hovered label grows and can briefly overlap a
   neighbour (it rises above it). Dense corners (Horizon's horizon, Circuit's ring) can still sit
   close at 1440×900; other window sizes were spot-checked only.
3. Phone width remains usable but not designed (W2).
4. Not run — requires human: the product owner's choice and scores, Safari, VoiceOver, an M1.
   Not run on the spike: axe and contrast measurement (W2's tokens).

---

# Fix round 2 report

Commits: `07dfb8a` World spike, fix round 2: every name by its own light and on screen; lights
answer pointing; `fa40db5` Update session W1's package for fix round 2: lights or names, click to
keep. Write and Edit only; explicit staging; `answers-2.md` untouched. No `osascript` or any
macOS automation of Chrome was used in this round.

## Red first

The new checks in `tools/check.mjs` were run against the committed round-1 build (`dist/` built
16:04:20, unchanged) before any rebuild. They failed:

- Horizon after the revelation: `skill:hygiene: hidden` at 1440×900, 1280×800 and 1728×1080.
- Every look: `the page does not expose where its lights are` (so the light-association and
  pointing-at-a-light checks could not pass).
- `the chooser has no visible pause control`.
- 13 failures in all.

## Changes, item by item

1. **Every label by its own light** (`src/app.ts` `settleLabels`, `src/styles.css`).
   - Each label's anchor is the point of the label nearest its own light. A candidate place whose
     anchor is as near to another light (within 6 px) gets a heavy penalty.
   - Any label not right beside its light (anchor more than its gap plus 6 px away) gets a fine
     leader line back to it. Before, only labels placed at reach > 1 got one.
   - A label left of its light ends with its glyph, so the glyph sits beside its own light
     (`[data-align="end"] .name` reversed).
   - The case from the re-review ("Warehouse supervisor") now ends with its diamond beside its
     own light (`2-horizon-b-revelation.png`).
   - Covering check, at 1440×900, 1280×800 and 1728×1080, in all three looks, after the first
     answer and after the revelation. Each skill and destination name's anchor must be within
     30 px of its own light and nearer to it than to any other light, unless a leader joins them.
2. **No skill off screen.**
   - Horizon's skill arc is ±50° at a lateral factor of 1.15 (was ±62° at 1.3). The right-hand
     destinations end at x = 9.5 (was 11), clear of the card at 1280 px.
   - Covering check (new; it failed first on the round-1 build): every skill and destination
     name is inside the window, not hidden, not covered at its centre (`elementFromPoint`) and
     focusable. Every light is inside the window too.
   - The check runs in each look, after the answer and after the revelation, at the three window
     sizes. It passes for all.
3. **The lights answer pointing.**
   - A window `pointermove` handler hit-tests the destination and revealed lights in the world
     layer (`lightAt`, a radius of the larger of 22 px and 3 light radii). It points at a light
     exactly as hovering its name does, and shows a pointer cursor.
   - A click on a light pins it, like a click on its name; a click on the revealed light opens
     its card.
   - The names still work, and focus still points.
   - The page exposes `window.__spike.pointing` and `window.__spike.layout` for the checks.
   - Covering check: moving the mouse to a destination's light shows its skills, in all three
     looks. The package's step 4 now reads "Point at a few of the orange lights, or at their
     names (or press Tab to reach them) … Click one to keep them showing."
4. **The chooser's pause control.** A visible "Pause motion" switch (same style and fixed label
   with `aria-pressed`) pauses the flowing trails and the breathing light
   (`animation-play-state: paused`); reduced motion still stops them. Covering check: after
   clicking it, every running animation on the chooser is paused and the control is pressed.
5. **`aria-pressed` follows the pin only.** The destination buttons' pressed state is now
   `pinned === key`; pointing and focus only show. Covering check: focusing a destination shows
   its skills without pressing it; a click presses it; a second click releases it.
6. **The keystroke claim.** The uncommitted "24 repeat samples" claim is removed.
   `tools/measure.mjs` now types "care worker" on three loads per look (33 keystrokes) and keeps
   every sample in `measurements.json` (median, p95, max, count, samples). The earlier 82.6 ms
   outlier did not recur: the maximum is 9.0 ms.
7. **Measured last, on the committed build.**
   - The newest source edit was `src/app.ts` at 16:24:25. The build was made at 16:30:19 and the
     measurement ran from 16:30:21 to 16:32:22 (`measurements.json` written 16:32:22).
   - No source changed afterwards; only `README.md` was updated with the numbers.

## Commands and output (final code)

| Command | Result |
|---|---|
| `pnpm test` | 14 tests, 14 pass, 0 fail |
| `pnpm typecheck`; `pnpm exec tsc --noEmit --noUnusedLocals --noUnusedParameters` | clean; clean |
| `pnpm build` | clean |
| `node tools/check.mjs` on the round-1 build | 13 failed (above) |
| `node tools/check.mjs` on the round-2 build | all passed, 71 checks, run twice |
| `node tools/screenshots.mjs` | 11 PNGs retaken (3.6 MB): all eight Horizon skills on screen, glyphs facing their lights, leaders, the chooser's pause control |
| `make check` | exit 0: 308 files formatted, ruff clean, mypy clean, pytest 1485 passed / 299 deselected, fixture validator passed, web client drift, Biome, `tsc`, Vitest 212 passed |
| `node tools/measure.mjs` (last step) | table below |

## Frame times, round-2 build (measured last)

Apple M4, 16 GB (Mac16,1), macOS 27.0, Google Chrome 156.0.8078.76, headed, ANGLE Metal on the
Apple M4; 1440×809 CSS px at DPR 2; busiest scene; 3 s warm-up, 12 s.

| Look | Run | Frames | Interval p50 | Interval p95 | Intervals ≥ 16.7 ms | Script p95 | GPU p50 | GPU p95 | GPU p99 | GPU frames > 8 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Growth | vsync | 1440 | 8.3 | 9.9 | 0 | 0.2 | 1.32 | 1.73 | 2.16 | 0 |
| Horizon | vsync | 1439 | 8.3 | 10.0 | 0 | 0.3 | 1.10 | 1.73 | 2.10 | 0 |
| Circuit | vsync | 1440 | 8.3 | 10.0 | 0 | 0.3 | 0.94 | 1.48 | 1.90 | 0 |
| Growth | unthrottled | 9524 | 0.2 | 2.8 | 1 | 2.6 | 1.21 | 2.09 | 2.45 | 0 |
| Horizon | unthrottled | 10152 | 0.2 | 2.7 | 2 | 2.6 | 1.00 | 1.72 | 2.19 | 0 |
| Circuit | unthrottled | 10062 | 0.2 | 2.7 | 5 | 2.6 | 0.90 | 1.75 | 2.19 | 0 |

| Look | First frame, normal entry (median of 3) | First frame, busiest scene | Keystroke to frame (median / p95 / max of 33) | Skill picked to frame, busiest scene (max of 5) |
|---|---|---|---|---|
| Growth | 73 ms | 410 ms (first page of a fresh browser) | 4.2 / 8.1 / 9.0 ms | 10.6 ms |
| Horizon | 67 ms | 112 ms | 4.8 / 7.1 / 7.7 ms | 11.0 ms |
| Circuit | 72 ms | 81 ms | 3.3 / 8.4 / 8.9 ms | 17.1 ms |

All within budget under the per-frame-cost ruling: whole-pipeline unthrottled interval p95 at
most 2.8 ms; GPU p99 at most 2.5 ms; no GPU frame over 8 ms; first frame at most 410 ms; input
to frame at most 17.1 ms. GPU times are lower than round 1's, in line with clock-speed variance
between runs (the scene is unchanged).

## Concerns after round 2

1. The label rules are held by `tools/check.mjs` at three desktop window sizes; other sizes and
   phone width were not checked (phone layout is W2's).
2. A hovered label grows over its neighbour until the pointer leaves.
3. Not run — requires human: the product owner's choice and scores, Safari, VoiceOver, an M1.
   Not run on the spike: axe and contrast measurement.
