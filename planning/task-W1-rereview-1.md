# Task W1 re-review 1 (fix round 1: 62b060d..1d0a4b3)

Method: read the fix list, the fix report (`task-W1-report.md` from "# Fix round 1 report"),
and the 4,786-line fix diff in three passes (package and README; app, story, direction and the
three looks; styles and tools). Opened all 11 updated screenshots and the reference image.
Cross-checked every frame-table row against `spikes/world/measurements.json`: all match.

Focused checks, each for a named risk, on the round-1 build (`dist/` built 16:04:20, after the
last source edit). Served with `vite preview` on 127.0.0.1:53300 and driven by headless system
Chrome from scratch scripts outside the repository
(`/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/24e22135-26a4-4575-bfe4-e8182a70f9b1/scratchpad/rereview.mjs`,
`hidden.mjs`, `hidden2.mjs`). The server was stopped afterwards. The working tree is unchanged.

- Labels after Calm mode on, then off (item 1). In Growth and Circuit, 15 of 15 labels are
  shown before, at 0.3 s after and at 1.5 s after. In Horizon it is 14 of 15 at all three times:
  the missing one is off-screen (New Important 1).
- Teal everywhere (item 2). There is no teal on the first screen. While typing, teal is only on
  the selected suggestion's dot. After "Keep … in view", teal is only on the kept destination's
  label border, plus the path and lock-on in the world.
- Pointing at a destination's light, then at its name (new step 4). Pointing at the light does
  nothing in all three looks; pointing at the name works (New Important 2).
- The chooser with motion on and with reduced motion: 4 animations run with motion on, none
  with reduced motion. There is no pause control on the chooser.
- Horizon off-screen labels for chef, barista, care worker, electrician and data analyst.
  Before the revelation none are off-screen. After it, one skill is off-screen every time:
  `hygiene`, `hygiene`, `firstaid`, `wiring`, `data`.

## The 12 items

1. **ADDRESSED.** Each label's entry animation now plays once:
   - `data-shown` is set at creation when the label is still or already born, and on
     `animationend` otherwise (`spikes/world/src/app.ts:317-337`).
   - Every label is marked shown on any change of mode (`app.ts:260`).
   - Only unshown labels animate (`src/styles.css:516-519`).
   - Toggle-back tests for Calm mode and for reduced motion are in
     `tools/check.mjs:119-136`.
   - Independently reproduced fixed (counts above).

2. **ADDRESSED.**
   - Circuit's corner ticks are blue (`styles.css:912-921`).
   - Focus rings are white (`styles.css:53-56`).
   - Teal is left only on the selected suggestion (`styles.css:369-372`), the kept label
     border (`styles.css:679-681`) and the primary button (`styles.css:799-808`).
   - The chooser's brackets are violet-blue (`styles.css:1068-1075`).
   - A page-wide teal scan is in `tools/check.mjs:103-116`; my wider scan agrees.

3. **ADDRESSED** (agent pre-review, not a score).
   - Captions are visually hidden until hover or focus (`styles.css:62-70`, `:568-576`).
   - After the revelation, only shared skills, the revealed destination and the shadow label
     speak; the rest is at 60% (`app.ts:343-397, voice at :365, :381, :395`, `styles.css:558-560`).
   - Each destination grows one quiet trail; all its shared trails show only when pointed at
     (`src/direction.ts:195-218`).
   - Legend lines appear as their state appears, and "usual" keeps its line
     (`app.ts:408-416`).
   - The card is about 45 words before Why?; the unknown names moved behind Why?
     (`app.ts:667-677`).
   - "Usual in your role, not confirmed yet" stays distinct: a ring against a fill, its legend
     line, and the full words in each skill's accessible name and on hover or focus. It reaches
     the truth rule.
   - In the screenshots the screen is markedly calmer: in each look, eight named skills, five
     quiet names, one captioned revelation and a short card.

4. **ADDRESSED** (agent pre-review).
   - The question is placed beside the projected light (`--ox/--oy`, `app.ts:430-435`).
   - Each look answers keystrokes in its own way: Growth's seed tendrils
     (`src/directions/growth.ts:189-202`), Horizon's ground ripple (`the keystroke ripple in `horizon.ts`'s background shader), Circuit's socket packets (`the socket stubs in `circuit.ts`'s node shader), driven by `uTyped`
     (`src/gl.ts`).
   - The pill box is gone.
   - The three first screens now differ before any keystroke (`1-growth-a`, `2-horizon-a`,
     `3-circuit-a`), though each is still "big headline plus an input line" over its world.
   - The chooser is a world: your light below, with a trail drawn in each look's way rising to
     each door (`src/main.ts:921-1014`, `0-chooser.png`).

5. **NOT ADDRESSED** (Horizon labels only; the rest is addressed).
   - Addressed:
     - **Growth:** one quiet trail per destination, gentle sway, warm orange cores
       (`src/directions/growth.ts:213-222`; `1-growth-b-revelation.png`).
     - **Horizon:** the grid is gone (`src/directions/horizon.ts:161-167`), and the revealed light
       keeps a steady column (`2-horizon-b-revelation.png`).
     - **Circuit:** rebuilt as a radial board with a core, a pad ring, a terminal arc and
       micro-traces. It is readable and no longer reads as two columns
       (`3-circuit-b-revelation.png`).
   - Not met: "labels must never crowd or detach from their light."
     - In the committed `2-horizon-b-revelation.png`, "◆ Warehouse supervisor" sits between the
       Shop supervisor light and its own light. Its diamond is about 20 px from the *Shop
       supervisor* light and about 180 px from its own, and there is no leader line.
     - Leaders are drawn only for labels placed at reach > 1 (`app.ts:526`). A wide label at
       reach 1 on a diagonal side can still end far from its light.
     - Separately, Horizon now pushes one skill off-screen after the revelation (New
       Important 1).

6. **ADDRESSED.**
   - Every destination and the revealed one stand at `HORIZON_Z = 17`
     (`src/directions/horizon.ts:15`, `:45`, `:47`).
   - The revelation takes the centre slot and is singled out by its column and glow, not by
     depth.
   - Skills sit on one arc at equal distance (`horizon.ts:28-30`).
   - Circuit likewise: pads on one ring, terminals on one arc (`circuit.ts:14-17`).

7. **ADDRESSED.**
   - `pnpm start` sets `BROWSER=tools/open-chrome.js` (`spikes/world/package.json:12`), which
     runs `open -a "Google Chrome"` with a plain fallback message (`tools/open-chrome.js`).
   - The package says Chrome up front, and why (`docs/reviews/session-w1.md:3-4`, `:23-25`).

8. **ADDRESSED.** `DEFAULT_FONT = "outfit"` (`src/direction.ts:18`), and the per-look `font`
   field is removed. The package says all three looks share the lettering and keeps lettering
   as its own question (`session-w1.md:33`, `:73`). The screenshots show Outfit in all three.

9. **ADDRESSED.**
   - "Script" replaces "main thread" and is defined (`README.md:112-120`; `measure.mjs`
     header).
   - The unthrottled interval is cited as the whole-pipeline figure.
   - GPU p99 and the count of GPU frames over 8 ms are reported (Growth's 8.55 ms did not
     persist: p99 now 4.36 ms).
   - First frame is given for the normal entry and for the busiest scene, and input-to-frame
     is defined.
   - The table matches the raw data.
   - The single 82.6 ms Circuit keystroke is reported honestly.
   - Two small caveats are under Minor.

10. **ADDRESSED.** `onChange`, `emit` and the listener set are gone (`src/story.ts`; grep finds
    none).

11. **ADDRESSED** for the three header toggles: fixed labels "Pause motion", "Calm mode" and
    "Sound" with `aria-pressed` (`app.ts:72-74`, `:251`). The check asserts the fixed label
    and the pressed state. See Minor 2 for the new destination buttons.

12. **ADDRESSED.** The package names the swell, the chime and the tick in both the play list
    and question 4 (`session-w1.md:54-56`, `:72`).

## New breakage introduced by the fix diff

### Critical

None. The truth rules hold:
- The revelation's source and sentence are unchanged.
- "Not a job offer" and "Not known yet" are still on the card.
- Unknown is still dashed shadow.
- Usual is still distinct from confirmed.
- The single quiet trail per destination is a real shared skill, chosen by layout.
- Depth and position carry no rank.

Colour meanings hold (above). There is still no external request: the CSP and fonts are
unchanged, and `open-chrome.js` only opens a local address.

### Important

1. **Horizon hides one of the person's skills after the revelation.**
   - **Cause:** the skill arc was widened to ±62° at radius 2.05 × 1.3
     (`src/directions/horizon.ts:28-30`). With the revealed view
     (`horizon.ts:119`: camera x 0.15 kx, z 0.2) the leftmost skill projects more than 40 px
     off the left edge at 1440 × 900. `app.ts:424` then sets its label to
     `visibility: hidden`.
   - **Reproduced:** for chef, barista, care worker, electrician and data analyst, one skill
     label is hidden after the revelation and none before. The committed
     `2-horizon-b-revelation.png` and `2-horizon-c-still.png` show seven skills, and "Prepare
     food hygienically" is missing, though the console says "Chefs usually need these 8 skills."
   - **Why it matters:**
     - That skill can no longer be seen or picked, by pointer or by keyboard (a hidden button
       is not focusable).
     - The DOM list loses an item for assistive technology.
     - Its trail runs off the screen.
     - The words-equality and words-shown checks cannot catch it: they compare `textContent`,
       and check opacity, not visibility (`tools/check.mjs:119-125`).
     - This worked in the previous round.
   - **Fix:** keep the arc inside the revealed view (narrow it, or move the camera). Add a check
     that every skill label is visible after the revelation in each look.

2. **The package's new step 4 does not work as written.**
   - `docs/reviews/session-w1.md:45` says "Point at a few of the orange lights". But only the
     name labels respond (`app.ts:816-819`); the light itself is in the canvas, which has no
     pointer handling.
   - Verified in all three looks: pointing at the light leaves `aria-pressed="false"`;
     pointing at the name sets it to `true`.
   - **Why it matters:** the product owner follows the script, points at a glowing light,
     sees nothing happen, and concludes the feature is missing or broken. This is the same
     class as last round's Calm-mode glitch.
   - **Fix:** either reword ("point at the names beside the orange lights"), or give each light
     a hit area that maps to its destination.

### Minor

1. **The chooser moves with no pause control.** Two infinite CSS animations (the flowing
   dashes, `styles.css:1065`; the breathing glow, `:1100`) run on the chooser, with no pause
   control on the page. Reduced motion stops them; I measured 4 running animations with motion
   on and 0 with reduced motion. This is a literal WCAG 2.2.2 gap on a page that had no motion
   before. It is rated Minor because the chooser is not a look, it is used for seconds, and it
   does not carry into W2. Fix: stop the flow after 5 s, or honour the same Pause.

2. **The destination buttons' `aria-pressed` follows hover and focus**
   (`app.ts:380`: `story.focus === key`), not the click-to-pin state. Moving the mouse over a
   name makes it "pressed". Tie `aria-pressed` to `pinned`, or drop it and use
   `aria-expanded` or `aria-describedby` for the shown skills.

3. **One measurement claim has no committed data.** `README.md:138` says "24 repeat samples in
   headed Chrome peaked at 8.4 ms" from a scratch script, but the 82.6 ms sample is the only
   committed one. Either commit the repeat data or drop the claim and keep the honest 82.6 ms.

4. **The measurement may predate the last style edit.** `measurements.json` was written at
   15:59:02, and `styles.css` was last modified at 15:57:09. A run takes about two minutes, so
   it probably served a build without the final CSS edit. CSS cannot change the GPU or script
   numbers, and the whole-pipeline 2.8 ms is far from the budget. Re-run with the final build,
   or note it.

## Out of scope (outside the fix diff)

- The revelation card keeps its orange edge (top border in Horizon, border in Circuit) from
  round 0. That is defensible, since the card is about a destination, but it is the one orange
  that is not a destination light. Noting it for W2's tokens.

## Agent pre-review of the round-1 looks (not a score)

- **Growth.** It is now the closest to the reference image: one clear trail per warm orange
  light, roots fanning from "You", and fibres. The tangle is gone. Labels on the left (Plan
  stock, Carpenter, Check work) still sit close together.
- **Horizon.** The smooth plain, horizon band and column of light read as the image's journey.
  But the horizon row is still the tightest place for words: see item 5 and New Important 1.
- **Circuit.** The radial board with a powered core reads as a living circuit rather than a
  flowchart. It is the most legible of the three.
- **The chooser and first screens.** They are now worlds, and the three first screens differ
  before typing. Each still leads with a large headline and an input line. That is acceptable
  for "one light, one question", but it is the part most like a page.
