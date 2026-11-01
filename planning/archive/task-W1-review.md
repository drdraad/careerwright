# Task W1 review: the spike of three directions (da25020..62b060d)

Reviewer method: read the contract, brief, dispatch, report, then the 6,749-line diff in three
passes (docs and README; model, story, scene, app and still layer; directions, GL, tools and raw
measurements). Screenshots in `docs/reviews/session-w1/` and the reference image opened and
judged. Focused checks, each for a named risk:

- Calm mode on, then off (the session's scripted step 6, which `tools/check.mjs` does not cover):
  served the existing `dist/` (built 15:18:23, 1.5 min before commit cec21cd) with
  `vite preview` on 127.0.0.1:53300, ran a headless system-Chrome script
  (`/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/24e22135-26a4-4575-bfe4-e8182a70f9b1/scratchpad/calm-toggle.mjs`),
  then stopped the server. Result in Important 1.
- Measurement honesty: every row of the README and report frame and library tables compared
  with `measurements.json` and `bench-results.json`: all match (rounding only).
- Library claims: npm downloads for 2026-09-30..2026-10-29 from the npm API: three 88,435,172,
  pixi.js 5,387,168, ogl 3,022,002, as reported.
- Dependency age: registry publish dates for playwright 1.64.1 (2026-10-14), vite 8.3.4
  (2026-10-08) and three 0.186.1 (2026-09-24) match the README and are at least 14 days old.
- No external URL in `src/`, `bench/` or `index.html` (grep), CSP `'self'` only.

Not re-run: `pnpm test`, `tools/check.mjs`, `tools/measure.mjs`, `tools/bench.mjs`, `make check`,
`make spike-world` end to end.

### Spec Compliance

- ❌ Issues found:
  - One colour, one meaning (Global Constraint 11; ADR 0014 decision 5): Circuit draws teal
    corner brackets on the console and the revelation card, which are neither a selection, the
    chosen path nor the primary action (`spikes/world/src/styles.css:810-818`). Important 2.
  - Everything else in the brief, the SW.1 slice and the dispatch rulings is delivered: three
    directions from `make spike-world`; the same first ten seconds and one revelation on labelled
    made-up data; still versions for reduced motion, calm mode and no WebGL2; a visible pause;
    frame times with device, browser, renderer and scene; library and typeface comparison with a
    recommendation each; no runtime request beyond 127.0.0.1; exact pins at least 14 days old;
    spike outside product code and labelled; session package in plain words with no scores.
  - Controller ruling (8 ms = per-frame cost, main thread plus GPU): met on the reported numbers
    (GPU p95 2.5–5.5 ms, script p95 0.2 ms), and corroborated by the unthrottled rAF p95 of
    2.8 ms, which covers the whole pipeline. See Minor 1 on what "main thread" measured.
- ⚠️ Cannot verify from diff:
  - Human-only (R2), correctly recorded as not run: the product owner's choice and any design
    score, Safari, VoiceOver, an M1-class Mac.
  - `make check` exit 0 (product untouched), the 14 model tests, `tools/check.mjs` passing, and
    publish dates for all 71 locked packages: claimed in the report, not re-run (three direct
    pins spot-checked).
  - The frame numbers themselves (not re-measured; they trace exactly to the committed raw data).
  - Whether the committed screenshots, taken in headless Chrome (`tools/screenshots.mjs:12`),
    match what headed Chrome shows the product owner.

### Strengths

- One scene model and one DOM layer drive all three directions and both renderers, so the words
  are the same by construction, and `tools/check.mjs` proves it in a real browser for moving,
  reduced motion and calm mode. This is the right architecture to carry into W2.
- The truth rules are encoded, not just styled. The revelation comes from a deterministic,
  tested function (`src/model.ts`, `src/model.test.ts`): another field, no shared title word,
  most shared essential skills, at least 4, ties by title, none means no revelation. The
  sentence is about the two roles, never the person. The card says why, what is not known yet
  (drawn as dashed slate shadow), "Not a job offer", and puts the five skills and the source one
  step away behind Why?. The first scatter is chosen by count but placed by title. "Usual in your
  role, not confirmed yet" (ring) is visibly apart from "you said so" (filled, bright).
- The still versions are first-class: the SVG still world draws every state, reduced motion
  overrides calm (with a reason on the disabled button), and Pause really stops the loop.
- Measurement is honest and well documented: headed system Chrome on the real GPU, renderer
  string, device and browser recorded, raw JSON committed, the 120 Hz floor named instead of
  hidden, GPU timer queries and an unthrottled run added to show cost rather than cadence.
- The library comparison uses an identical workload across three.js, PixiJS and OGL; the
  download figures check out; the three.js back-face trap is recorded for W2.
- Sound is off by default; the AudioContext is created only from the Sound button's click, so
  nothing plays unasked (ADR 0014 decision 8 respected; the session asks the question).
- The session package is plain, action-first, has a time estimate, uses no internal codes and
  gives no scores.

### Issues

#### Critical

None.

#### Important

1. **Words vanish for about two seconds after leaving Calm mode, on the session's own scripted
   path.** `spikes/world/src/styles.css:833-838` sets `animation: none` on everything while
   still; removing `.is-still` restarts each label's `label-in` animation
   (`styles.css:467`, `fill-mode: both`) with the birth delay it was given when first created
   (`src/app.ts:314-316`, up to about 2 s). Focused check, all three directions, after Calm on
   then off: 10 of 16 world labels visible at 1.5 s, 16 of 16 at 4.5 s; the screenshots show
   every destination label but Firefighter gone, and skill labels fading back in. Why it
   matters: `docs/reviews/session-w1.md:45` tells the product owner to do exactly this ("Click
   it again to go back"), and words disappearing is what the still-version contract exists to
   prevent; it will read as broken in the one hour that decides the redesign. The same happens
   when the system's reduced-motion setting is switched off. Fix: let each label's entry
   animation play once (drop it after `animationend`, or clear `--delay` and the animation for
   labels already shown when leaving still mode), and add the toggle-back case to
   `tools/check.mjs`.

2. **Circuit uses teal as panel decoration.** `spikes/world/src/styles.css:810-818` paints teal
   corner brackets on `.dir-circuit .card` and `.dir-circuit .is-answered .console` (visible in
   `3-circuit-b-revelation.png` and `3-circuit-c-still.png`). Teal is reserved for selection, the
   chosen path and the primary action (Global Constraint 11, ADR 0014 decision 5, CLAUDE.md);
   here it marks the console, which is not selected, and competes with the teal lock-on that
   "Keep firefighter in view" draws. Why it matters: if the product owner picks Circuit, they
   pick a look whose meaning W2 must then quietly change. Rated Important rather than Critical:
   it is a literal breach of a Global Constraint, but only in throwaway spike CSS, it changes no
   state or word, and it is a four-line fix. Fix: draw the corners in blue or white; keep teal
   for the kept destination's brackets. (The chooser's Circuit emblem, `src/main.ts`, shows teal
   brackets as the lock-on itself, which is defensible.)

#### Minor

1. **"Main thread" and two table labels overstate what was measured.** The main-thread figure
   is the script time inside the rAF callback only (`src/app.ts:495`, `:528`); it leaves out
   style, layout, paint and compositing of the DOM layer (labels move every frame during
   Horizon's replayed travel), and the GPU timer covers only the WebGL draw. Under the ruling,
   the whole-pipeline evidence is the unthrottled rAF p95 (2.8 ms), which the README should
   cite as such. Also: the README frame table's "First frame" column (`spikes/world/README.md:90`)
   is the normal entry (91–95 ms), not the busiest scene its caption names (129–258 ms in
   `measurements.json`); "Keystroke to frame" ends at the end of the rAF callback and was sampled
   only before the first answer, the lightest scene (`src/app.ts:518`); Growth's GPU p99 of
   8.55 ms (42 frames over 8 ms) is not mentioned. No conclusion changes; all stay inside budget.

2. **The browser that opens may not be Chrome.** `package.json:12` uses `vite preview --open`,
   which opens the default browser; `docs/reviews/session-w1.md:23-24` names Chrome only as a
   fallback. If the product owner's default is Safari, they judge the looks in a browser nothing
   was checked or measured in. Fix: say "open it in Chrome" up front.

3. **Each look has a different heading face by default** (Growth Outfit, Horizon Unbounded,
   Circuit Sora), so the product owner's comparison mixes world and lettering; the session doc
   asks about lettering only via a PNG (`docs/reviews/session-w1.md:66`). Fix: use one face for
   all three by default, or tell them it differs and where to switch it (Spike tools).

4. **Horizon's depth can read as distance to reach.** Destinations alternate depth by title
   index (`src/directions/horizon.ts:43`: 16 vs 18.2) and the revelation sits at depth 30
   (`:56`). On a journey plain, near and far mean "closer" and "further to go", which section 4
   says position must never mean. Barely visible at 1440 px because the horizon compresses
   depth, but if Horizon is chosen, W2 must decide what depth means. Worth one line in the W2
   brief.

5. **Dead code:** `Story.onChange` and its listeners are never subscribed (`src/story.ts:38-46`).

6. **Toggle buttons change their label and also carry `aria-pressed`** ("Pause motion" / "Play
   motion", "Sound off" / "Sound on": `src/app.ts:66-68`, `:240`, `:764`), so a screen reader
   hears "Sound off, toggle button, not pressed". Use a fixed label with `aria-pressed`, or a
   changing label without it. A W2 concern.

7. **A third sound cue.** `src/sound.ts:46` adds a "touch" cue on every skill click, beyond the
   plan's "ignition and revelations". Off by default, so harmless; the session's sound question
   should know it exists.

### Agent pre-review of the design (agent pre-review, not the required human review; no scores)

Against the product owner's words and the reference image, from the screenshots:

- **Not bland.** Growth's and Horizon's revelation states glow, have depth and read as a world
  being lit, not a form. Circuit's lock-on is the crispest single moment. The still versions
  look like the same world, not a degraded fallback.
- **The first screen is the same in all three, and it is a search page.** A centred headline,
  a teal pill input with placeholder and hint, one dot of light; only the backdrop changes
  (starfield, grid plain, dot grid) and the lettering. In the first two seconds the product owner
  sees "dark landing page with a search box", three times. The plan wants one light and one
  question, but the question could live in the world (near the light, the light answering each
  keystroke more visibly) and each direction could already feel different before typing.
- **After the first answer, too many words at once.** Eight skill labels each captioned "not
  confirmed yet", five destinations captioned "N shared skills", a shadow label, a console panel,
  a 70-word card, a four-line legend, two footer labels, and six pills across the top. That is
  their own session 2 complaint ("minimum ideas per page", "Don't even know where to start").
  The ring glyph plus the legend already carries "usual"; the per-label caption could appear on
  hover or focus without breaking the truth rule.
- **Growth:** the reach trails cross into a tangle and read as a network graph; destination
  cores render near-white, so "orange" is weaker than the reference image's warm end points.
- **Horizon:** the closest to the reference's journey, but the ruled grid plain is the familiar
  80s "Tron" trope rather than the image's smooth dark ground; labels crowd the horizon and some
  detach from their lights ("Warehouse supervisor" floats among trails away from its light at the
  right end); once settled, the revealed Firefighter sits in the same row as the others and is
  not singled out.
- **Circuit:** a column of skills, a column of destinations and mono captions: closest to a
  flowchart or a tool, as the implementer also says.
- **The chooser** is a tidy product page with flat line icons; it is the very first thing the
  product owner sees, so it sets the tone more than its role suggests.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The spike meets the brief with honest, traceable measurements and truth rules
encoded in tested code, but two things the product owner will meet in their first minutes should
be fixed before session W1: words vanish for about two seconds when they leave Calm mode exactly
as the package instructs, and Circuit spends teal on decoration.
