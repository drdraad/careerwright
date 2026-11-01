# Task W2A review: the app half

Reviewer: app half (`apps/web` world layer, shell, chapters, CSS, stories, e2e, measurement
script, `package.json`, `backend/tests/architecture/test_boundaries.py`). Commits
c1bc2f3..65aed2f. Package `review-W2A-app.diff` read in four passes (tests and scripts; world
modules; components and shell; CSS and stories), with focused reads of the files themselves for
line numbers.

**Spec compliance: ❌ Issues found.** **Quality: Needs fixes.**
Critical 0 · Important 6 · Minor 10.

What I checked outside the diff, one check per risk:
- Context loss / error boundary: grep of `apps/web/src` and `e2e` for `contextlost`,
  `loseContext`, `ErrorBoundary`, `error.tsx` (none found).
- The real screens: the implementer's own acceptance captures in `apps/web/test-results/visual-*`
  (run 19:48–19:51, `.last-run.json` "passed"), against the W2A design references in
  `docs/design/screenshots/roles--not-built-*`.
- The typing hold: one focused probe, kept outside the repository (below). Working tree
  unchanged (`git status`: only the user's `answers-2.md`).
- Frame numbers: `docs/evidence/world-frames.json` read and matched against the report's table
  (they match).
- Calm mode before W2A: `git grep -i calm c1bc2f3` (no distress-to-calm link existed, so none
  was lost).

Not run: `make check`, `make acceptance`, the measurement script (no window opened), any
browser.

---

### Spec Compliance

- ✅ One world mounted once by the shell behind all six chapters. The GL renderer effect depends
  only on `[still, ready]` (`World.tsx:293-308`), so a chapter change never makes a new context.
  Travel is a 600 ms tween, or a cut when still (`geometry.ts:321-361`).
- ✅ The exact DOM layer: every name the app's data can produce (the person, the person's own
  targets) is a list item in "Your world" (`World.tsx:521-552`).
- ✅ Still world (SVG) under reduced motion, calm mode or no WebGL2 (`World.tsx:248`). A visible
  Pause control (`WorldControls.tsx:47-53`). Sound is off every visit, and its AudioContext is
  made only from the click (`settings.ts:61-65`, `sound.ts:91-99`).
- ✅ Truth: lit by any answer, destinations are only the person's provided targets in title
  order, no skills or openings drawn from app data (`model.ts:36-61`). No rank, layer or
  affordability is computed. The fixture route preview is still shown only in the fixture
  workspace (`ChapterView.tsx:200`).
- ✅ Busiest scene is invented, labelled and in Storybook only (`World.stories.tsx:108-189`).
  Frame report has device, browser, renderer, per-frame cost and rAF interval.
- ✅ No new external request: three.js bundled, Outfit self-hosted, sound synthesised. No eval.
  The e2e checks requests (`world.spec.ts:223`).
- ❌ **Still world when WebGL2 becomes unavailable.** Context loss and a renderer that can't be
  created have no fallback (Important 2). Plan section 4: "The still world is drawn without WebGL
  when … WebGL2 is unavailable."
- ❌ **Phone width designed.** At 390×844 and 768×1024 the place sits under the chapter card, so
  the app doesn't match W2A's own phone reference (Important 4).
- ❌ **Ambient motion "stills while the person reads or types"** stills but never comes back
  after typing (Important 1, shown by a probe).
- ⚠️ **Cannot verify from the diff (not run, needs a human):** the moving world's look and feel
  ("as alive as Growth and Circuit", "never overwhelming" in motion), the sounds' character,
  Safari, VoiceOver, an M1 frame measurement. The report records all of these as "not run —
  requires human". It claims no human gate as passed.
- ⚠️ **Cannot verify from the diff:** the implementer's `make check` and `make acceptance` results
  (not re-run, per contract; the captures and `.last-run.json` agree with "passed").

### Strengths

- The world cleanly separates what to draw (`scene.ts`, `geometry.ts`, `model.ts`) from how
  (`gl.ts`, `StillWorld.tsx`). Both renderers draw one `Scene`, which makes "same states" true
  by construction.
- "Only what changes now grows" is real and tested. The swell can't fire for what was there on
  arrival (`World.tsx:69-113`; `World.test.tsx:86-109`).
- The model is strict and well tested. A target answered Unknown/Skipped draws no destination,
  and nothing is guessed (`model.test.ts`).
- Calm persistence is preserved exactly: same key, guarded storage, `data-calm` on `<html>`
  (`settings.ts:42-60`). Calm, pause and sound are tested through the controls
  (`WorldControls.test.tsx`).
- The frame loop stops at rest, while paused and while the tab is hidden (`World.tsx:395-398,
  443-444, 362-364`). GL disposal releases the context (`gl.ts:644-652`).
- The architecture change is minimal (see ruling 10).

---

### Issues

#### Critical
None.

#### Important

**1. Ambient motion never resumes after the person types.** (`World.tsx:407`, `World.tsx:443-444`, `World.tsx:346-352`)
- **What fails.** A keystroke sets `typedAt` and holds ambient motion. `live` decays to 0 in about
  1.2 s, and the loop then stops itself (`if (meter || l.live > 0 || animating(t)) … else
  l.running = false`). That happens before the 1.5 s hold ends, and nothing re-arms the loop
  afterwards. The world stays still until an unrelated event wakes it: a pointer crossing a panel
  edge, a DOM mutation, a chapter change, or pause/unpause.
- **Evidence (a probe, not committed).** One keystroke into an `<input>` beside `<World>`, with
  GLWorld mocked and fake rAF/performance timers. The world reads `running` before the keystroke,
  `still` 2.4 s after it, and still `still` 12.4 s after it. Probe:
  `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/24e22135-26a4-4575-bfe4-e8182a70f9b1/scratchpad/w2a-probe/typing-hold.test.tsx`
  (run with `vitest run --config <that folder>/vitest.config.mts --root <that folder>` from
  `apps/web`).
- **Fix.** Keep the loop alive while a typing hold is pending (`|| t - l.typedAt <
  TYPING_HOLD_SECONDS` in the continue condition), or set a timeout to call `wake` when the hold
  ends. Turn the probe into a test in `World.test.tsx`.

**2. The moving world has no failure path.** (`gl.ts:391-397`, `World.tsx:246-248`, `World.tsx:293-308`, `gl.ts:362-368`)
- **Lost context.** Nothing listens for `webglcontextlost`. three.js swallows the loss and draws
  nothing, so the world goes black behind its labels and is never drawn still. If Chrome won't
  restore the context, it stays black. `data-motion` keeps saying "running".
- **Renderer fails to start.** `new GLWorld(...)` runs inside an effect with no try/catch and no
  error boundary under `src/app`. If `WebGLRenderer` throws ("Error creating WebGL context"),
  that takes down the whole workspace shell (chat, chapters, drawer), not only the world.
- **Leaked probe context.** `webgl2Available()` opens a WebGL2 context on a throwaway canvas and
  never releases it, which counts against the browser's small context limit.
- **Fix.** Listen for `webglcontextlost` and `webglcontextrestored` on the canvas and drive a
  `lost` state into `still` (restore goes back to moving). Wrap the `GLWorld` constructor so a
  throw becomes `capable = false`. In the probe, call
  `getExtension("WEBGL_lose_context")?.loseContext()`.
- **Test.** Dispatch `webglcontextlost` with GLWorld mocked, and assert
  `data-world-mode="still"` with the same names.

**3. The "word for word" parity test can't fail for what it claims.** (`e2e/world.spec.ts:254-275`, `globals.css:191-193`)
- **Why it can't fail.** It compares `innerText` of the whole "Your world" list. A name hidden
  from sight is `opacity: 0`, which `innerText` still includes, and so are the sr-only captions.
  Both modes render the same React list by construction. A name shown in the moving world but
  hidden in the still world (or the reverse) passes.
- **What it leaves out.** It covers one chapter (Roles), one target and the default viewport,
  under reduced motion only. Calm mode and pause are never compared.
- **Fix.** Compare the shown set (`.world-label[data-shown='true']` names, and whether the legend
  is shown) across moving, reduced motion, calm mode and paused. Do it per chapter, at the three
  viewports, with a three-long-target workspace (plan section 5: "long role/provider names,
  three targets").

**4. At tablet and phone widths the place is under the card.** (`World.tsx:206-217`, `geometry.ts:59-71`, `labels.ts:27-66`, `e2e/world.spec.ts:285-322`)
- **Tablet (768×1024).** In `roles--768x1024.png` the "Data quality analyst" name sits above the
  card, its light is behind the card and "You" is hidden. The world shows a name tag for a light
  the person can't see.
- **Phone (390×844).** In `roles--390x844.png` and `skills--390x844.png` no light is visible at
  all, only stars.
- **Why.** `clearSpan` only looks for space beside a panel. A phone skips it, and a tablet's
  128 px gap falls under `MIN_CLEAR`, so the default centre (`w*0.62`) puts the focus under the
  card. `layoutLabels` keeps names off panels but doesn't check whether the light itself is
  covered.
- **The app doesn't match its own reference.** W2A's reference for the same state
  (`docs/design/screenshots/roles--not-built--390x844.png`) shows the person and destination
  above a short sheet.
- **The phone label check passes vacuously.** Every name is hidden there, so it checks an empty
  list.
- **Fix.** Find the clear band above the card on tablet and phone, and aim the place's view into
  it. Make the not-built card a short sheet, as in the reference. Treat a light under a panel as
  "no spot", so its name hides. In `world.spec.ts`, assert that at Roles the person's name and at
  least one destination name are shown at every viewport.

**5. Not-built places are heavier than the design reference, with two empty states stacked.** (`ChapterView.tsx:98-108`, `ChapterView.tsx:130-154`, `ChapterView.tsx:207-226`)
- **What the app shows.** Each card has "Not built yet", the title, the where-line, the purpose
  paragraph, a divider, then a second state ("Not started" / "No roles yet"), its paragraph, the
  "Uses these answers from You" table and the action. That is two honest-state headings saying
  one thing.
- **What the reference shows.** The kicker, the title, the where-line, one sentence and one
  action (`roles--not-built--1440x900.png`, `roles--not-built--390x844.png`). This is the
  clearest case of "never overwhelming" in the real screens.
- **Fix.** Render the reference's five elements. Keep the inner state's one sentence ("Role
  research isn't part of this build yet, so no listings have been searched"). Leave "Uses these
  answers" one step away behind "Review what we know". The honest state and its words stay in
  the DOM.

**6. One colour, one meaning: quiet actions glow the primary-action teal.** (`globals.css:553-564`)
- **The rule and what changed.** `.btn-quiet` and `.btn-icon` take `color: var(--action)`. With
  W2A's tokens `--action-reading` is now the brightest sea-glass (`seaglass-300`, other half).
- **What it looks like.** On You, "Skip", "Source", "Keep none", "Dismiss" and the drawer's ×
  all glow teal beside the one primary action (`you--support-note--1440x900.png`,
  `you--source-drawer--1440x900.png`). The primary is no longer unmistakable, and teal no longer
  means only selection, the chosen path and the primary action.
- **Where it comes from.** The CSS rule predates W2A. The v1.4 token change makes it
  non-compliant.
- **Fix.** Quiet and icon actions take the text colour, with an underline or glyph. Teal stays
  on `.btn-primary`, selection and the chosen path. Cross-check with the other half's tokens.

#### Minor

**1. Ruling 4 puts a setting on the first screen.** (`WorldControls.tsx:54-62`, `WorkspaceStrip.tsx:179`)
- Plan section 4 says "Settings such as how Careerwright talks with you live in preferences,
  never on the first screen". The PO's "minimum ideas per page" points the same way.
- Pause (WCAG 2.2.2) and Sound (session W1) must be visible. Calm mode needn't be: the device
  setting already forces still, and Pause stills on demand.
- Fix: move Calm mode back into the account menu, as a toggle with the same `useWorldSettings`
  wiring. It keeps persistence, the device override and its words, and leaves one fewer control
  in the strip.

**2. A risk word doesn't still the world yet.** (CLAUDE.md "Distress stills the world"; slice plan gives this to W2C)
- Nothing was lost: no distress-to-motion link existed before W2A.
- But from W2A until W2C, the moving world keeps moving beside the calm support panel
  (`you--support-note`). It holds only while the pointer is on the panel, or for 1.5 s after
  typing.
- Carry to W2C as a must-close before session W2. The cheapest route is a `distress` flag that
  `World` ORs into `still`.

**3. Skills and openings are drawn without words.** (`World.tsx:124-150`, `model.ts:10`)
- `labelsFor` names only the person and destinations, and `WorldSkill.label` is never used. The
  scene can draw skill and opening lights that the DOM doesn't name; the busiest scene does.
- Latent today, because the model emits none. It breaks "the canvas holds nothing unique" as soon
  as W2C passes skills.
- Fix: name skills in the list, and give openings a count line, before W2C wires them.

**4. Small per-frame allocations, and read-after-write during travel.** (`geometry.ts:347-360`, `World.tsx:413`, `geometry.ts:135-142`, `World.tsx:415-417`, `World.tsx:169`, `World.tsx:178`)
- Each frame allocates a new `View` plus a closure, the `render({...})` object, three
  uniform arrays, and an `Object.keys` array plus a closure.
- During travel, `placeLabels` writes `dataset.shown` on the key, then reads `offsetWidth`, which
  forces style and layout every frame.
- Cost is tiny (script p95 0.4 ms), but the risk list asks for none. Fix: keep a scratch `View`,
  write uniform arrays in place, and read all sizes before any write.

**5. The frame measurement's scope.** (`frames.ts:37-44`, `globals.css:386,426,476`)
- "GPU time" covers the WebGL passes only. It leaves out the compositor re-blurring the app's
  `backdrop-filter` glass over a full-screen moving canvas.
- The app's busiest real scene (You with the drawer open: strip, panel and drawer all blurred)
  was not measured.
- Script and GPU samples are paired by recency, so they are offset by the query lag.
- Fix: call it "WebGL GPU time" in the report. W2D should measure the app scene, and the
  unthrottled interval already captures the whole pipeline. Pair the samples by frame index.

**6. Resource hygiene.** (`settings.ts:39-40`, `World.tsx:54-63`, `gl.ts:469-474`, `World.tsx:460-464`)
- The AudioContext is never closed when the shell unmounts.
- A devicePixelRatio change with no resize (moving between displays) isn't picked up. Use a
  `matchMedia("(resolution: …dppx)")` listener.
- Names aren't re-placed when Outfit finishes loading. Listen to `document.fonts`.

**7. Sound cues are described as wired when they aren't.** (`sound.ts:1-4`, `World.stories.tsx:191-195`)
- They describe the chime and tick triggers as if they exist. Ruling 3 is honest in the report,
  but not in the code.
- Fix: add "no trigger until W2C" beside `CUES`.

**8. Dead and speculative bits, and stale comments.** (`places.ts:9,15`, `palette.ts:2,11`, `motion.ts:2-3`, `gl.ts:47-51`)
- `Place.moment` (`places.ts`) and `PALETTE.chosen` are never used.
- Stale comments: `palette.ts:2` names `palette.test.ts` and `motion.ts:2-3` names
  `motion.test.ts`. The test is `tokens.test.ts`.
- The shader colour constants duplicate the palette with no test holding them. They do match the
  tokens today, by my arithmetic.

**9. The persistence test marks the wrong node.** (`e2e/world.spec.ts:206-219`)
- It marks `.world`, not the canvas. It would still pass if the canvas and its WebGL context were
  recreated on every chapter.
- Fix: mark the `canvas[data-testid=moving-world]` element.

**10. Model and phone-control details.** (`model.ts:37-46`, `globals.css:1013-1020`, `Conversation.tsx:304`)
- `hasAnswered` duck-types `Object.entries(profile.document)`. Iterate the generated field list,
  as `WhatWeKnow.tsx:31` does.
- On a phone the three world controls are glyph and switch only. The calm glyph (two waves)
  doesn't explain itself.
- On You, the interview's "Pause" and the world's "Pause motion" sit on one screen with different
  meanings.

---

### Never overwhelming: the real screens

The controller asked for concrete reductions, each with what it keeps. I judged from the
implementer's captures, which show the still world (headless runs under reduced motion), and from
the shader code. I have not seen the moving world.

What competes at once on Roles at 1440:
- **Strip:** 11 items on two rows, including three labelled switches.
- **Rail:** six landmarks.
- **Card:** 11 text blocks.
- **World:** two lights, two names, one trail and a two-line legend.
- **In motion,** per `gl.ts`: about ten kinds of ambient motion with no meaning. These are the
  breathing horizon, the aurora, the travelling horizon shimmer, two mist layers, 2,400 motes,
  star twinkle, trail sway, a flow along every trail, and the destination reflection shimmer.

Reductions:

1. **Card → the reference's five elements** (Important 5).
   - Keeps: "Not built yet", the place's words and the one action.
2. **Calm mode → the account menu** (Minor 1).
   - Keeps: Pause and Sound visible, calm persistence and the device override.
3. **Phone header: three rows → two, as in the reference.** Saved state, live updates and the
   three switches go on one row, and the not-built card becomes a short sheet so the place shows
   above it (Important 4).
   - Keeps: every strip state word.
4. **Atmosphere: fewer kinds of meaningless motion.**
   - Drop the travelling shimmer (`gl.ts:95-98`). It is a bright spot sweeping across the screen
     at 38 px/s, and the eye follows it for no reason.
   - Drop trail sway (`gl.ts:164-167`): it makes a known trail look unsettled.
   - Cut motes from 2,400 (`gl.ts:30`) to a few hundred.
   - Keep the breath, the aurora, and the outward flow on known trails. The flow is the one
     ambient motion with a meaning, and today's app has no known trail yet.
   - Keeps: all states and words. The still world draws none of these, so nothing in it changes.
5. **A name whose light is covered hides with its light, and the legend shows only when a light
   it explains is in view** (Important 4).
   - Keeps: every name in the "Your world" list for assistive tech.

---

### Verdicts on the implementer's rulings (app half)

1. **Body face Source Sans 3, Outfit display only.** Agree, for what touches my half: the
   visual spec checks Outfit 600 at 39 px and Source Sans 3 (`visual.spec.ts:689`).
2. **What the world may draw.** Agree. Lit by any answer, including Unknown, Skipped or Prefer
   not to say. Destinations are only provided targets. Nothing about skills, connections or
   openings is computed in the UI. See Minor 10 for the duck-typing.
3. **Sound.** Agree. The swell can't fire on arrival (tested), and the AudioContext is made only
   from the click. The chime and tick really have no source event. Make that visible in the code
   (Minor 7) and close the context on unmount (Minor 6).
4. **Calm mode moved to the visible controls.** Nothing lost: persistence, guard and `data-calm`
   are kept, and no distress path existed. But I **disagree with the move**: it puts a setting on
   the first screen against plan section 4 and adds a control (Minor 1). Move it back into the
   account menu.
5. **No side fibres.** Agree.
6. **Focus white, switch "on" white.** Agree. The dark halo (`globals.css:96-101`) keeps focus
   visible over light.
7. **"Reading" holds only over the panel or drawer.** Agree. The typing hold has its own defect
   (Important 1).
8. **View centres in the clear span.** Agree for wide screens (`you--1440x900`: You stands at
   1300 px). It is incomplete for tablet and phone (Important 4).
9. **Glass at 91%.** No objection from the app side; the contrast evidence is the other half's.
10. **Architecture test admits three.js only in the web lockfile.** Agree.
    - `ADMITTED_JS_PACKAGES` names one package in one lockfile, and the assertion subtracts only
      that (`test_boundaries.py:270`, `:309`).
    - Nothing else is loosened: PixiJS and three stay excluded in `docs/design` and
      `docker/auth`, and the scope list is unchanged.
    - `@types/three` brings a physics engine (`@dimforge/rapier3d-compat`) as a dev-only
      transitive. It is recorded in `docs/dependencies.md`, not shipped and not in the
      exclusion list. Noted, not a defect.
11. **Measurement at device scale 2 in the Storybook busiest scene.** Agree, with Minor 5's
    caveats.
    - The scene is invented, labelled and never in the app.
    - The report's table matches `world-frames.json`: 1,440, 9,517/9,512 and 720 frames, cost
      p95 4.91, 4.00 and 4.28 ms, renderer `ANGLE Metal Renderer: Apple M4`.
    - It is honest about M4, Chrome only, and "not M1, not Safari".
12. **Axe wait and the "Less" match.** Agree; neither weakens an assertion.
    - The axe helper retries only on "Axe is already running" and rethrows anything else. It
      gives up after 40 tries (10 s) rather than skipping, and the rule set is unchanged
      (`e2e/helpers.ts`, the new `axe`/`scan`).
    - "Less" is now scoped to its sheet, exactly as `keyboard.spec.ts:92` already does. The
      old page-wide match would also hit the Calm mode control's name, "…less motion…".

---

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The world layer is well structured and truthful. But three things fail now:
ambient motion stays frozen after the first keystroke (shown by a probe), a lost or failed
WebGL context neither falls back to the still world nor stays contained, and tablet and phone
hide the place under the card. The still/moving parity test can't fail for the case it names.
Fix those four, and make the not-built card and quiet-action colour match the reference, before
W2B builds on this.
