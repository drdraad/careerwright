# World spike: three directions (throwaway)

**This is a spike.** It is a throwaway preview for session W1, where the product owner tries
three looks for Careerwright's living world and chooses one, or a mix. It is not product code.
No product check lints or tests it, and nothing in `apps/web` or `backend` uses it. Everything
in it is made up, and the screen says so.

## Run it

From the repository root:

```
make spike-world
```

That installs the locked packages, builds, serves on `http://127.0.0.1:53300` (loopback only)
and opens the chooser in your browser. Stop it with Ctrl-C.

| Page | Address |
|---|---|
| The chooser | `http://127.0.0.1:53300/` |
| Growth | `http://127.0.0.1:53300/?d=growth` |
| Horizon | `http://127.0.0.1:53300/?d=horizon` |
| Circuit | `http://127.0.0.1:53300/?d=circuit` |
| The busiest scene (100 made-up openings) | add `&scene=busy` |
| Calm mode from the start | add `&calm=1` |
| A heading typeface | add `&font=outfit`, `&font=sora` or `&font=unbounded` |
| The library comparison | `http://127.0.0.1:53300/bench/?lib=three` (or `pixi`, `ogl`) |

## What each direction shows

All three ask the same question ("What do you do now, or what did you do last?"), use the same
made-up list and say the same words. The first answer lights the person's light and grows the
skills their job usually needs and a first scatter of destinations. About 2.4 seconds later one
revelation arrives: an unexpected connection to a job in another field, joined by the essential
skills the two share. Its card says why (one step away, behind "Why?"), what is still not
known, and that it is not a job offer. Picking a skill marks it "you said so"; "Keep … in view"
lights the chosen path in teal, with Undo.

- **Growth** (organic first): roots and nerves grown from the person; a pulse beats outward
  through the network; spores drift up.
- **Horizon** (journey first): a dark plain under a horizon like the reference image; the view
  travels a short way out at the revelation, and a column of light rises from the destination.
- **Circuit** (cybernetic first): routed traces on an instrument grid; light travels as packets;
  the revelation locks on with closing brackets.

Each has a still version: the system's reduced-motion setting, or the Calm mode button, draws the
same states and words as SVG with no WebGL and no motion. A visible Pause control stops ambient
motion. Sound is off by default; the Sound button tries a short synthesised cue for the first
answer and the revelation (no audio files).

## How it keeps to the truth rules (plan section 4)

- The revelation comes from deterministic code (`src/model.ts`) over the made-up list
  (`src/data.ts`): the job in a different field, sharing no word with the person's job title,
  that shares the most essential skills (at least 4; ties by title). No source, no revelation.
  Tested in `src/model.test.ts`.
- Its sentence is built from computed facts and is about the two jobs, never the person.
- "Usual in your role, not confirmed yet" (faint, ring) is drawn apart from "you said so"
  (bright, filled). Unknown is shadow (dashed, slate) and says "not known yet".
- Position is layout only: destinations are placed in title order, never by how many skills
  they share. Orange means a destination; teal means the chosen path and the primary action.
- Atmosphere (particles, the pulse, breathing) looks the same for every item.

## Checks

From `spikes/world`, with the preview running (`pnpm preview`) for the browser tools:

| Command | What it does |
|---|---|
| `pnpm test` | The model's truth rules (Node's own test runner) |
| `pnpm typecheck` | TypeScript, strict |
| `node tools/check.mjs` | Plays each direction in Chrome: the world answers the first answer, the revelation's sentence and evidence are in the page, the words match with reduced motion and calm mode, keyboard use, pause, and no request leaves 127.0.0.1 |
| `node tools/measure.mjs` | Frame times in headed Chrome on this Mac; writes `measurements.json` |
| `node tools/bench.mjs` | The library comparison; writes `bench-results.json` |
| `node tools/screenshots.mjs` | Screenshots for `docs/reviews/session-w1/` |

The browser tools use the system's Google Chrome through Playwright (no browser download).

## Frame times (busiest scene)

Apple M4, 16 GB (Mac16,1), macOS 27.0, Google Chrome 156.0.8078.76, headed, GPU
`ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)`. Window 1440 by 900
(1440 by 809 CSS pixels inside), device pixel ratio 2, canvas 2880 by 1618. Scene: 100 made-up
openings and their trails, all destinations, the kept path, ambient particles, with the
revelation (and Horizon's travel) replayed every 4 seconds. Warm-up 3 s, then 12 s of
`requestAnimationFrame` deltas. GPU time per frame from `EXT_disjoint_timer_query_webgl2`.
Measured 2026-10-30; raw numbers in `measurements.json`.

| Direction | Run | Frames | rAF p50 | rAF p95 | Frames over 16.7 ms | Main thread p95 | GPU p50 | GPU p95 | First frame | Keystroke to frame (max) |
|---|---|---|---|---|---|---|---|---|---|---|
| Growth | vsync | 1441 | 8.3 ms | 10.0 ms | 0 | 0.2 ms | 2.5 ms | 5.5 ms | 95 ms | 9.5 ms |
| Horizon | vsync | 1439 | 8.3 ms | 10.1 ms | 0 | 0.2 ms | 2.1 ms | 3.2 ms | 91 ms | 8.1 ms |
| Circuit | vsync | 1439 | 8.3 ms | 10.1 ms | 0 | 0.2 ms | 1.1 ms | 2.5 ms | 91 ms | 7.5 ms |
| Growth | unthrottled | 10147 | 0.2 ms | 2.8 ms | 5 | 2.5 ms | 1.2 ms | 1.9 ms | | |
| Horizon | unthrottled | 10309 | 0.2 ms | 2.8 ms | 5 | 2.5 ms | 1.3 ms | 1.9 ms | | |
| Circuit | unthrottled | 10374 | 0.2 ms | 2.8 ms | 5 | 2.6 ms | 1.2 ms | 1.9 ms | | |

How to read it against the plan's headroom budget (p95 within 8 ms on this Mac):

- This display refreshes at 120 Hz, so a `requestAnimationFrame` delta can never be below
  8.33 ms. The vsync p95 of 10.0 to 10.1 ms is presentation jitter around that interval; no
  frame took 16.7 ms or more, so none was dropped.
- The work each frame costs is well inside 8 ms: GPU p95 2.5 to 5.5 ms and main thread p95
  0.2 ms. The unthrottled run (`--disable-gpu-vsync --disable-frame-rate-limit`) agrees: GPU
  p95 1.9 ms. Its few long frames are stalls of the unthrottled browser, not of the scene.
- First frame (navigation start to the first drawn world frame): 91 to 95 ms, against a
  one-second budget. Input feedback: at most 9.5 ms from a keystroke to the frame that answers
  it, against 100 ms.
- These are lab numbers on an M4, not the M1 target and not Safari.

## The WebGL library comparison

The same workload (identical shaders, geometry and draw order: a backdrop, 140 glowing trails,
130 instanced lights, 2,400 particles, additive) drawn by each library, same machine and
browser, measured 2026-10-30 (`bench-results.json`).

| Library | Version (published) | Licence | JS the page ships (gzip) | First frame (median of 3) | rAF p95 (vsync) | Main thread p95 | GPU p95 |
|---|---|---|---|---|---|---|---|
| three.js | 0.186.1 (2026-09-24) | MIT | 131 KB (523 KB raw) | 95 ms | 10.3 ms | 0.2 ms | 3.1 ms |
| PixiJS | 8.22.0 (2026-10-01) | MIT | 131 KB (446 KB raw) | 102 ms | 10.2 ms | 0.2 ms | 2.9 ms |
| OGL | 1.0.11 (2025-01-27) | Unlicense | 17 KB (53 KB raw) | 73 ms | 10.2 ms | 0.2 ms | 3.9 ms |

Frame cost is the same within noise: the shaders do the work, not the library. The choice rests
on fit and risk:

- **three.js (recommended).** Raw GLSL 3 shaders work as written (`RawShaderMaterial`), a real
  3D camera is there when Horizon-style depth or travel needs it, and it is by far the most used
  (88 million npm downloads in the month to 29 October 2026, against 5.4 million for PixiJS and
  3.0 million for OGL) and steadily maintained (13 releases in the past year). It also has a
  WebGPU path. Costs: the largest bundle, and two traps found here: its default back-face
  culling hid half the screen-space geometry until both faces were drawn, and its built-in
  shader library is shipped even when unused.
- **PixiJS.** Built for 2D sprites and filters. Under a content security policy without
  `unsafe-eval` (the spike's and the product's) it fails until `pixi.js/unsafe-eval` is
  imported, and it compiled shaders without a `#version` line as WebGL1 GLSL. Workable, but its
  strengths are not this world's needs.
- **OGL.** The smallest by far, and the closest to raw WebGL. But one npm maintainer, no
  release since January 2025, and fewer people to help when something breaks.

## The display typeface comparison

All licensed under the SIL Open Font License 1.1 and self-hosted from Fontsource packages (the
licence text is in each package's `LICENSE`). Try them with Spike tools, Heading typeface.

| Face | Character | On long job names |
|---|---|---|
| **Outfit (recommended)** | Round geometric, closest to the bold white type in the reference image | The narrowest: "Customer service advisers and emergency call handlers share 6 essential skills." takes 4 lines in the card |
| Sora | Wider, more technical; suits Circuit | 5 lines |
| Unbounded | Wide, game-title feel | Needs a smaller size and still takes 5 lines |

Body text: Atkinson Hyperlegible Next (OFL), 16 px and up. Instrument readouts (Circuit):
JetBrains Mono (OFL).

## Dependencies

Exact pins, each at least 14 days old (`minimumReleaseAge: 20160` in `pnpm-workspace.yaml`,
the same rule as `apps/web`; every transitive version in the lockfile was checked against the
registry's publish dates). pnpm 10.33.2, Node 24. Installing reaches the npm registry; at run
time the spike makes no request beyond its own origin (checked by `tools/check.mjs`, and its
content security policy allows only `'self'`).

| Package | Version | Published | Licence | Why |
|---|---|---|---|---|
| three | 0.186.1 | 2026-09-24 | MIT | The world layer |
| pixi.js | 8.22.0 | 2026-10-01 | MIT | Library comparison only |
| ogl | 1.0.11 | 2025-01-27 | Unlicense | Library comparison only |
| @fontsource-variable/outfit | 5.3.0 | 2026-07-19 | OFL-1.1 | Display face candidate |
| @fontsource-variable/sora | 5.3.0 | 2026-07-19 | OFL-1.1 | Display face candidate |
| @fontsource-variable/unbounded | 5.3.0 | 2026-07-19 | OFL-1.1 | Display face candidate |
| @fontsource-variable/atkinson-hyperlegible-next | 5.3.0 | 2026-07-19 | OFL-1.1 | Body face |
| @fontsource-variable/jetbrains-mono | 5.3.0 | 2026-07-19 | OFL-1.1 | Readouts |
| vite (dev) | 8.3.4 | 2026-10-08 | MIT | Build and loopback server |
| typescript (dev) | 6.0.3 | 2026-04-16 | Apache-2.0 | Type check |
| @types/three (dev) | 0.186.0 | 2026-09-11 | MIT | Types |
| @types/node (dev) | 24.19.2 | 2026-10-09 | MIT | Types for the tests |
| playwright (dev) | 1.64.1 | 2026-10-14 | Apache-2.0 | Checks, measurement, screenshots (system Chrome) |

`docs/dependencies.md` records only the library W2 adopts, not these.

## Known limits

- Phone width works but is not designed; phones get their own layout in W2.
- Labels are placed by a small heuristic that avoids panels, lights and each other; dense
  corners can still crowd.
- Not built here: the distress response, returning visits, the overlooked-strength revelation
  (model-proposed in the product), and every chapter beyond the first moments.
- Measured on Chrome on an M4 only: Safari and an M1 are not measured.
