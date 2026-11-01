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
and opens the chooser in Google Chrome (`tools/open-chrome.js`), the browser everything was
checked and measured in, whatever the computer's default browser is. Stop it with Ctrl-C.

| Page | Address |
|---|---|
| The chooser | `http://127.0.0.1:53300/` |
| Growth | `http://127.0.0.1:53300/?d=growth` |
| Horizon | `http://127.0.0.1:53300/?d=horizon` |
| Circuit | `http://127.0.0.1:53300/?d=circuit` |
| The busiest scene (100 made-up openings) | add `&scene=busy` |
| Calm mode from the start | add `&calm=1` |
| Another heading typeface | add `&font=sora` or `&font=unbounded` (all three looks use Outfit by default) |
| The library comparison | `http://127.0.0.1:53300/bench/?lib=three` (or `pixi`, `ogl`) |

## What each direction shows

All three ask the same question ("What do you do now, or what did you do last?"), use the same
made-up list and say the same words. The chooser is already a world: the person's light below,
a trail rising to each look, drawn in that look's way, with a Pause motion control for its
flowing light.

Before the first answer, the question sits in the world beside the person's light, and the
light answers every keystroke. The first answer lights the person's light and grows the skills
their job usually needs and a first scatter of destinations. About 2.4 seconds later one
revelation arrives: an unexpected connection to a job in another field, joined by the essential
skills the two share. Its card says what changed, why (one step away, behind "Why?"), what is
not known yet, and that it is not a job offer. Picking a skill marks it "you said so"; "Keep …
in view" lights the chosen path in teal, with Undo.

One idea at a time: what just changed speaks; the rest stays quiet until asked. Each
destination grows one quiet trail; pointing at its light or its name (or focusing the name with
the keyboard) lights all the skills it shares and shows how many; a click keeps them showing
(the name's pressed state). Captions such as "usual in your role, not confirmed yet" appear on
hover and focus; the ring glyph and one legend line carry the meaning at a glance, and each
legend line appears when its state first appears. Every name sits beside its own light, its
glyph on the side facing the light; a name placed further away gets a fine leader line back to
its light.

- **Growth** (organic first): before the answer, a seed whose tendrils reach further with each
  keystroke. After it, roots and nerves grown from the person, swaying gently, with fine side
  fibres and a pulse that beats outward through them; warm orange destination lights.
- **Horizon** (journey first): a smooth dark plain under a glowing horizon, like the reference
  image; the question floats above the person's light and each keystroke sends a ripple across
  the plain. Every destination stands at the same distance (depth means nothing); the revealed
  one is singled out by a column of light that rises and stays. The view travels a short way
  out at the revelation.
- **Circuit** (cybernetic first): a powered core on a board of faint micro-traces; before the
  answer, packets run out along its stub traces with each keystroke. After it, the skills are
  pads on a ring around the core and destinations are terminals on one outer arc (both at equal
  distance), joined by traces at right angles and 45°, with light travelling as packets; the
  revelation locks on with closing brackets.

Each has a still version: the system's reduced-motion setting, or Calm mode, draws the same
states and words as SVG with no WebGL and no motion. Words never wait for an animation after
a change of mode. Pause motion stops ambient motion. Sound is off by default; turning it on
plays three short synthesised cues (no audio files): a low swell when the light comes on, a
rising chime when the connection lights up, and a small tick when a skill is picked.

## How it keeps to the truth rules (plan section 4)

- The revelation comes from deterministic code (`src/model.ts`) over the made-up list
  (`src/data.ts`): the job in a different field, sharing no word with the person's job title,
  that shares the most essential skills (at least 4; ties by title). No source, no revelation.
  Tested in `src/model.test.ts`.
- Its sentence is built from computed facts and is about the two jobs, never the person.
- "Usual in your role, not confirmed yet" (faint, ring) is drawn apart from "you said so"
  (bright, filled). Unknown is shadow (dashed, slate) and says "not known yet".
- Position is layout only: destinations are placed in title order, never by how many skills
  they share; in Horizon every destination, the revealed one included, stands at the same
  depth, and every skill at the same distance from the person; in Circuit pads share one ring
  and terminals one arc.
- Orange means a destination; teal means selection, the kept path and the primary action, and
  nothing else (checked by `tools/check.mjs`). Focus rings are white.
- Atmosphere (particles, the pulse, sway, tendrils, micro-traces) looks the same for every item.

## Checks

From `spikes/world`, with the preview running (`pnpm preview`) for the browser tools:

| Command | What it does |
|---|---|
| `pnpm test` | The model's truth rules (Node's own test runner) |
| `pnpm typecheck` | TypeScript, strict |
| `node tools/check.mjs` | Plays each look in Chrome: the world answers the first answer; the revelation's sentence and evidence are in the page; the words match with reduced motion and calm mode; every word stays shown after calm mode or reduced motion is turned on and off; teal only on the primary action; focusing a destination shows what it shares and a click pins it; keyboard use; pause. At 1440×900, 1280×800 and 1728×1080, after the first answer and after the revelation: every skill and destination is inside the window, visible, not covered, focusable and anchored beside its own light (or joined by a leader); pointing at an orange light shows what it shares; the chooser's motion pauses; no request leaves 127.0.0.1 |
| `node tools/measure.mjs` | Frame times in headed Chrome on this Mac; writes `measurements.json` |
| `node tools/bench.mjs` | The library comparison; writes `bench-results.json` |
| `node tools/screenshots.mjs` | Screenshots for `docs/reviews/session-w1/` |

The browser tools use the system's Google Chrome through Playwright (no browser download).

## Frame times (busiest scene)

Apple M4, 16 GB (Mac16,1), macOS 27.0, Google Chrome 156.0.8078.76, headed, GPU
`ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)`. Window 1440 by 900
(1440 by 809 CSS pixels inside), device pixel ratio 2, canvas 2880 by 1618. Scene: 100 made-up
openings and their trails, all destinations, the kept path, ambient particles, with the
revelation (and Horizon's travel) replayed every 4 seconds. Warm-up 3 s, then 12 s. Measured
2026-10-30, 16:30 to 16:32, on the round-2 build (built 16:30, after the last source edit);
raw numbers, including every input-to-frame sample, in `measurements.json`.

What each number covers:

- **Frame interval**: `requestAnimationFrame` deltas, the whole pipeline as the page sees it.
- **Script**: time inside the frame callback (our JavaScript and the WebGL calls). It does not
  include style, layout, paint or compositing of the words over the world.
- **GPU**: the WebGL draw of the world (`EXT_disjoint_timer_query_webgl2`), not the compositing.
- **Unthrottled** runs (`--disable-gpu-vsync --disable-frame-rate-limit`): their frame interval
  is the whole-pipeline cost of a frame.

| Look | Run | Frames | Interval p50 | Interval p95 | Intervals ≥ 16.7 ms | Script p95 | GPU p50 | GPU p95 | GPU p99 | GPU frames > 8 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Growth | vsync | 1440 | 8.3 ms | 9.9 ms | 0 | 0.2 ms | 1.3 ms | 1.7 ms | 2.2 ms | 0 |
| Horizon | vsync | 1439 | 8.3 ms | 10.0 ms | 0 | 0.3 ms | 1.1 ms | 1.7 ms | 2.1 ms | 0 |
| Circuit | vsync | 1440 | 8.3 ms | 10.0 ms | 0 | 0.3 ms | 0.9 ms | 1.5 ms | 1.9 ms | 0 |
| Growth | unthrottled | 9524 | 0.2 ms | 2.8 ms | 1 | 2.6 ms | 1.2 ms | 2.1 ms | 2.5 ms | 0 |
| Horizon | unthrottled | 10152 | 0.2 ms | 2.7 ms | 2 | 2.6 ms | 1.0 ms | 1.7 ms | 2.2 ms | 0 |
| Circuit | unthrottled | 10062 | 0.2 ms | 2.7 ms | 5 | 2.6 ms | 0.9 ms | 1.8 ms | 2.2 ms | 0 |

| Look | First frame, normal entry (median of 3) | First frame, busiest scene | Keystroke to frame, normal entry (median / p95 / max of 33) | Skill picked to frame, busiest scene (max of 5) |
|---|---|---|---|---|
| Growth | 73 ms | 410 ms | 4.2 / 8.1 / 9.0 ms | 10.6 ms |
| Horizon | 67 ms | 112 ms | 4.8 / 7.1 / 7.7 ms | 11.0 ms |
| Circuit | 72 ms | 81 ms | 3.3 / 8.4 / 8.9 ms | 17.1 ms |

"First frame" is navigation start to the first drawn world frame; Growth's busiest-scene load
was the first page of a fresh browser. "Input to frame" runs from the input's handler to the
end of the frame callback that answers it (presentation adds up to one refresh, 8.3 ms). The
earlier round's single 82.6 ms keystroke in Circuit did not recur in these 33 samples.

How to read it against the plan's budgets (p95 within 8 ms on this Mac, ruled as per-frame
cost; first frame within 1 s; input feedback within 100 ms):

- The whole-pipeline cost of a frame (unthrottled interval p95) is 2.7 to 2.8 ms; script p95
  at most 0.3 ms and GPU p99 at most 2.5 ms, with no GPU frame over 8 ms. Within budget.
- This display refreshes at 120 Hz, so a vsync interval can never be below 8.33 ms; the vsync
  interval p95 of 9.9 to 10.0 ms is presentation jitter, and no interval reached 16.7 ms.
- First frame 67 to 410 ms; input feedback at most 17.1 ms. Within budget.
- These are lab numbers on an M4, not the M1 target and not Safari.

## The WebGL library comparison

The same workload (identical shaders, geometry and draw order: a backdrop, 140 glowing trails,
130 instanced lights, 2,400 particles, additive) drawn by each library, same machine and
browser, measured 2026-10-30 (`bench-results.json`; the workload did not change in round 1).

| Library | Version (published) | Licence | JS the page ships (gzip) | First frame (median of 3) | Interval p95 (vsync) | Script p95 | GPU p95 |
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
licence text is in each package's `LICENSE`). All three looks use Outfit by default, so the
comparison is of worlds, not lettering; try the others with Spike tools, Heading typeface.

| Face | Character | On long job names |
|---|---|---|
| **Outfit (recommended)** | Round geometric, closest to the bold white type in the reference image | The narrowest: "Customer service advisers and emergency call handlers share 6 essential skills." takes 4 lines in the card |
| Sora | Wider, more technical | 5 lines |
| Unbounded | Wide, game-title feel | Needs a smaller size and still takes 5 lines |

Body text: Atkinson Hyperlegible Next (OFL), 16 px and up. Circuit's prompt: JetBrains Mono (OFL).

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
| @fontsource-variable/outfit | 5.3.0 | 2026-07-19 | OFL-1.1 | Display face |
| @fontsource-variable/sora | 5.3.0 | 2026-07-19 | OFL-1.1 | Display face candidate |
| @fontsource-variable/unbounded | 5.3.0 | 2026-07-19 | OFL-1.1 | Display face candidate |
| @fontsource-variable/atkinson-hyperlegible-next | 5.3.0 | 2026-07-19 | OFL-1.1 | Body face |
| @fontsource-variable/jetbrains-mono | 5.3.0 | 2026-07-19 | OFL-1.1 | Circuit's prompt |
| vite (dev) | 8.3.4 | 2026-10-08 | MIT | Build and loopback server |
| typescript (dev) | 6.0.3 | 2026-04-16 | Apache-2.0 | Type check |
| @types/three (dev) | 0.186.0 | 2026-09-11 | MIT | Types |
| @types/node (dev) | 24.19.2 | 2026-10-09 | MIT | Types for the tests |
| playwright (dev) | 1.64.1 | 2026-10-14 | Apache-2.0 | Checks, measurement, screenshots (system Chrome) |

`docs/dependencies.md` records only the library W2 adopts, not these.

## Known limits

- Phone width works but is not designed; phones get their own layout in W2.
- Labels are placed by a small heuristic that avoids panels, lights and each other and keeps
  each label's anchor nearest its own light; `tools/check.mjs` holds it to that at three window
  sizes. Dense corners can still sit close, and a hovered label grows over its neighbour.
- Not built here: the distress response, returning visits, the overlooked-strength revelation
  (model-proposed in the product), and every chapter beyond the first moments.
- Measured on Chrome on an M4 only: Safari and an M1 are not measured. Screenshots for the
  session package are taken in headless Chrome (also Metal-rendered here).
