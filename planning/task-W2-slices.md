# Task W2 slices (controller's split)

Task W2 (Sprint W, SW.2–SW.6) is 7–10 engineering days. It runs as four slices, one
implementer at a time, each reviewed before the next. The brief (`task-W2-brief.md`) and the
plan's "Sprint W Build the world" card stay the requirements; this file only says which part
each slice owns. Each slice carries its own tests; W2D closes the cross-cutting acceptance.

## Session W1's outcome (the product owner's own record, `docs/reviews/session-w1-answers.md`)
- Direction: **Horizon, made livelier.** Keep Horizon's calm, lined-up layout; give it
  animation as alive as Growth and Circuit; swap the dashed lines for quieter solid trails.
  Their words on the spike: Growth and Circuit "a bit too chaotic"; Horizon "the most logical,
  but not quite right yet. The animations aren't as good as the others, and its a bit too
  [noisy] with the dashed lines."
- Sound: **all three cues** (swell when the light comes on, chime when a connection lights up,
  tick when a skill is picked), off until the person turns sound on. In their words: "subtle
  and evocative, not cheesy!"
- Lettering: **Outfit** (display). WebGL library: three.js (the spike's recommendation, not
  contested at the session; pin per the 14-day rule).

## W2A — the world layer and its design references (SW.2, SW.3, ADR 0014's spike choices)
Design references for Horizon-made-livelier in `docs/design` (tokens with measured contrast
including panels over the brightest light, type, motion vocabulary and timings, the six
places at the three viewports, every honest state drawn), replacing the Sprint 0
compositions, mirror updated, `check-data` still checking fixture values. The world layer in
`apps/web`: one persistent world behind all six chapters, travel between places, the exact
DOM/SVG layer on top, the still world, the pause control, calm mode, frame-time
instrumentation, and the three sound cues (off by default, a visible control). A chapter not
yet built shows its place with an honest "not built yet" state. Record the spike's choices in
ADR 0014 (decisions 2, 6 and 8) and the library in `docs/dependencies.md`. Existing journeys
keep passing.

## W2B — the deterministic sources (SW.5 backend)
The first answer's ignition: "What do you do now, or what did you do last?" with ESCO
type-ahead over the pinned release, deterministic, no model call, working before a key and in
the demo. The slate joined by shared essential skills, never by shared words in a title:
check "data analyst" and the five personas, fix where it matches on words, amend ADR 0007.
The overlooked strength as a new bounded run kind (ADR 0006): one proposal per conversation
turn with new answers, its quotation span-verified and the skill checked as essential to one
of the person's destinations before the person is asked to confirm it; live only with the
person's key within their spend limit; the demo's example scripted and labelled; tests use
the test model or fixtures only; change DBOS `application_version` if the step sequence
changes. API, generated client regenerated.

## W2C — the You chapter in the world and the first moments (SW.4, SW.5 interface)
The You chapter rebuilt in the world with session 2's design findings (the SW.4 list). The
first ten seconds on W2B's ignition; the unexpected-connection revelation from the slate; the
overlooked-strength proposal and its confirm step; "usual in your role, not confirmed yet";
a risk word stills the world and holds back revelations, with the calm support panel.

## W2D — acceptance, register and session W2's package (SW.6)
The world's requirement family in the register with tagged tests; the Sprint W acceptance
(journeys pass in the world and again under reduced motion and calm mode with identical
text; a first answer changes the world within ten seconds; every revelation's sentence and
evidence in the DOM; axe, overflow and contrast clean at the three viewports; keyboard-only
completion and focus return; frame times against the budgets with device, browser and scene;
demo makes no external request); the coherence review; session W2's package (captures at the
three viewports, motion on and off, the rubric with the three v1.4 questions);
`docs/reviews/sprint-w.md` ready for session W2's outcome.

## Rulings that bind every slice
- Frame budget: the 8 ms M4 headroom and the 16.7 ms M1 budget are per-frame cost
  (main-thread work + GPU time), not the raw requestAnimationFrame interval, which a 120 Hz
  display floors at 8.33 ms. Report both, plus a 60 Hz run where possible, with device,
  browser and the WebGL renderer string.
- The spike (`spikes/world`) is reference: port what serves, to product standards (tests,
  Biome, `tsc`); leave the spike unchanged.
- Spike lessons carried (W1 deferred minors): a click made while the hovered light changes
  must not be lost in the still world; label layout checks in moving and still modes across
  roles; a hovered label must not cover its neighbour; phone width designed (390 × 844);
  Horizon's horizon must not crowd.
- Horizon depth means nothing (ADR 0014 decision 4): destinations at one depth; the
  revelation singled out by light, never by distance.
