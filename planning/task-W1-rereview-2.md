# Task W1 re-review 2 (fix round 2: 1d0a4b3..fa40db5)

Method: I read the round 2 fix list, the "# Fix round 2 report" section of `task-W1-report.md`,
and the full 2,133-line fix diff. I opened the updated screenshots (Horizon revelation and still,
the chooser) and cross-checked the frame tables against `spikes/world/measurements.json`; every
row matches.

I ran focused checks on the round-2 build (`dist/` built 16:30:19, after the last source edit at
16:24:25). I served it with `vite preview` on 127.0.0.1:53300 and drove it with headless system
Chrome from scratch scripts outside the repository
(`/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/24e22135-26a4-4575-bfe4-e8182a70f9b1/scratchpad/rereview2.mjs`,
`revclick.mjs`, `revclick2.mjs`). I stopped the server afterwards. The working tree is
unchanged.

What I checked, beyond what `tools/check.mjs` already covers:
- **Label layout, all three looks, after the answer and after the revelation.** The same rule as
  `tools/check.mjs`: inside the window, visible, not covered, by its own light or joined by a
  leader. I added the "Not known yet" label and ran it in cases the tool does not:
  - four more roles (care worker, electrician, data analyst, bus driver) at 1440 × 900;
  - two more window sizes (1366 × 768, 1920 × 1080);
  - Calm mode at 1440 × 900.

  Result: all 21 cases are clean.
- **Pointing, all three looks, moving and Calm mode.** I pointed at a destination's light, then
  clicked it, moved away, focused its name, and clicked it again.
  - Pointing at a light shows that destination and sets a pointer cursor, without pressing it.
  - A click presses it.
  - Moving away keeps it showing while it is pinned.
  - A second click releases it.
- **Clicking the revealed light.** In moving mode it focuses "Keep … in view". In Calm mode it
  does too, after a normal hover. See Minor 1 for the exception.
- **The chooser.** With motion on, 4 animations run. After pressing "Pause motion" all 4 are
  paused. Pressing it again resumes them.

## The 7 items

1. **ADDRESSED.** Every label sits by its own light.
   - Each placement is scored on its anchor, the point of the label nearest its own light. A
     place whose anchor is as near another light (within 6 px) gets a heavy penalty
     (`spikes/world/src/app.ts:512-545`).
   - Any label not right beside its light now gets a leader line, not only those at reach > 1
     (`app.ts:557`).
   - A label left of its light ends with its glyph (`src/styles.css:550-560`).
   - In `2-horizon-b-revelation.png` and `2-horizon-c-still.png`, "Warehouse supervisor ◆" ends
     beside its own light. "Check work against standards" has a leader.
   - `tools/check.mjs:198-277` enforces this at 1440 × 900, 1280 × 800 and 1728 × 1080. My wider
     run is clean.

2. **ADDRESSED.** No skill goes off screen.
   - Horizon's skill arc is ±50° with a lateral factor of 1.15 (`src/directions/horizon.ts:29-31`).
     The right-hand destinations end at x = 9.5 (`:45`).
   - In the committed Horizon screenshots all eight skills are on screen, including "Prepare
     food hygienically".
   - The new check requires each skill and destination to be inside the window, visible, not
     covered and focusable (`tools/check.mjs:204-246`, run at `:248-277`). The report shows it failing first on the
     round-1 build (`skill:hygiene: hidden`).
   - Independently, the five roles that hid a skill last round are clean in all three looks.

3. **ADDRESSED.** The lights answer pointing.
   - A window `pointermove` hit-tests destination lights in the world layer (`app.ts:759-774`,
     `:876-881`).
   - A click pins a light, and a click on the revealed light focuses Keep (`app.ts:882-890`).
   - Names and focus still work.
   - The package now says "Point at a few of the orange lights, or at their names … Click one to
     keep them showing" (`docs/reviews/session-w1.md:45-46`).
   - Covered at 1440 × 900 (`tools/check.mjs:263-273`). I reproduced it in moving and Calm mode.

4. **ADDRESSED.** The chooser has a pause control.
   - A visible "Pause motion" switch, with a fixed label and `aria-pressed`, sits top right
     (`src/main.ts:25-27`, `:109-114`; `0-chooser.png`).
   - It pauses every chooser animation (`styles.css:1121-1123`); reduced motion still stops
     them.
   - `tools/check.mjs:279-294` covers it. I reproduced pause and resume.

5. **ADDRESSED.** The destination buttons' `aria-pressed` follows the pin only.
   - It is now `pinned === key` (`app.ts:387`).
   - Hovering or focusing shows without pressing; a click presses; a second click releases
     (`tools/check.mjs:142-161`). Reproduced.

6. **ADDRESSED.** The unbacked claim is gone.
   - The "24 repeat samples" claim is removed. The README now says the 82.6 ms keystroke "did
     not recur in these 33 samples" (`README.md:144`).
   - All 33 keystroke samples per look are committed, with median, p95, max and count
     (`measurements.json` `first.*.keystrokeToFrameMs`; `tools/measure.mjs:97-105`).

7. **ADDRESSED.** The measurement ran last, on the committed build.
   - Last source edit: `app.ts` at 16:24:25 (`tools/measure.mjs` at 16:27:52 is the tool).
   - Build: 16:30:19. `measurements.json` written: 16:32:22, about two minutes of runs.
   - After that only `README.md` changed (16:32:43). Both commits are at 16:32:57.
   - The README states the window (`README.md:114`).

## New breakage in the fix diff

### Critical

None.
- **Truth rules:** unchanged; no new word, state or source.
- **Colour meanings:** leader lines are white at 40%, the pressed switch uses ink, and there is
  no new teal.
- **Still-version word parity:** no word changed; the glyph reversal is visual only.
- **No external request:** CSP and assets unchanged.
- **Measurement labels:** honest and traced to the raw data.

### Important

None.

### Minor

1. **Calm mode drops one kind of click.** In Calm mode, a click lands on nothing when the same
   motion that brings the pointer onto a light also changes which destination is pointed at.
   - Pointing in the still world redraws the whole SVG (`rebuild(false)` → `drawStillWorld`, via
     `point()`, `app.ts:745-749`).
   - A move-and-click with no pause (Playwright's `mouse.click` straight onto the revealed
     light) produced no click event at all in Growth, Horizon and Circuit Calm. The element
     under the pointer was replaced between hit-tests.
   - With a normal hover first (move, pause, click) it works in every look, so a person will
     rarely meet it.
   - Fix if wanted: keep the still SVG's nodes stable and change only their attributes, or
     resolve clicks from coordinates on `pointerdown`.

2. **The layout check covers moving mode only.** `tools/check.mjs` layout runs only in moving
   mode and only for chef. My wider run covered Calm mode, four more roles and two more sizes,
   and is clean. Adding Calm mode to the tool would hold that.

## Out of scope (outside the fix diff, or not a defect)

- The window `pointermove` handler (`app.ts:876`) sets the pointed destination on every move. So
  a mouse movement anywhere ends a keyboard-focus "show" (focus stays on the name, but its skills
  stop showing until it is pinned). This is harmless for the session.
- The report attributes round 2's lower vsync GPU times (Growth p50 2.89 → 1.32 ms) to
  "clock-speed variance". That is plausible, since unthrottled GPU p50 is unchanged at 1.21 ms,
  but it is unproven. The README does not repeat it.
