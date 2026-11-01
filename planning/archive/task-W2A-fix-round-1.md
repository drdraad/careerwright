# Task W2A fix round 1 of 5

You fix Task W2, slice W2A (Careerwright L0, branch `l0-local-release`). The slice was built
in commits c1bc2f3..65aed2f and reviewed in two halves. You are a fresh implementer: the
original implementer's report tells you what was built and why.

## Read first
1. Your contract: `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`
2. The brief and the slice plan: `task-W2-brief.md`, `task-W2-slices.md` (same folder)
3. The original dispatch and report: `task-W2A-dispatch.md`, `task-W2A-report.md`
4. The two reviews, in full: `task-W2A-review-design.md` (design half: `docs/`) and
   `task-W2A-review-app.md` (app half: `apps/web`). Finding numbers below are theirs:
   **D-I1** is design Important 1, **A-M4** is app Minor 4, and so on.
5. CLAUDE.md ("The experience", invariants, web layout), ADR 0014, plan section 4.

## The product owner, since the build
- A headed Chrome window ran the synthetic "Busiest scene" on their screen. Verbatim: "Wow,
  the scene looked too busy. was overwhelming". "Never overwhelming" now binds every slice:
  one idea at a time; nothing moves without meaning.
- Shown the real references `you--default--1440x900.png` and `roles--default--1440x900.png`,
  verbatim: "no, they look OK". So: no layout or strip reduction on taste alone in this round.

## Controller rulings
- **Trail contrast (D-I3):** measure trails as drawn (add `alpha` to their pairs; the tool
  composites) and make every meaning-bearing trail pass 3:1 as drawn, in the references and in
  the app's still and moving world. Do not declare them decorative.
- **Calm mode (A-M1, D-M1 on ruling 4):** move Calm mode back into the account menu, with the
  same `useWorldSettings` wiring, persistence, device override and words. Pause motion and
  Sound stay visible. Plan section 4 keeps settings off the first screen.
- **Distress stills the world now (A-M2 with D-M4):** while the calm support panel shows, the
  world is still (a flag ORed into `still`), in the app and the references. The Pause switch
  keeps showing the person's own choice; a separate status says the world is still while
  support is shown. W2C keeps the revelation hold-back.
- **Atmosphere (A's "never overwhelming" item 4):** drop the travelling horizon shimmer and
  trail sway; cut motes from 2,400 to a few hundred. Keep the breath, the aurora and the flow
  along known trails. The still world is unchanged by this.
- **Body face (D-M11, ruling 1):** Source Sans 3 stays, marked **provisional** in ADR 0014
  decision 6 and `docs/dependencies.md`, "to confirm with the product owner at session W2"
  (the spike had chosen Atkinson Hyperlegible Next).
- **Frame evidence (D-M12, A-M5):** fix `scripts/measure-world.mjs` to record the commit, mark
  the scene synthetic, use an `over16_7` key, pair script and GPU samples by frame index, and
  call it "WebGL GPU time". **Do not run it** (it opens a window on the product owner's
  screen). Leave `docs/evidence/world-frames.json` as the record of 65aed2f's run; W2D
  re-measures with the product owner warned first. Say so in ADR 0014 or the report.
- **Strip words** ("Saved, version 3", "Updates: Live", D-M2 rows 1–2 and D-M1a): not in this
  round; the controller carries them to W2C. The other D-M2 strings are fixed now.
- **Carried, not fixed here:** D-M5 (revelation lit) and A-M3 (skills and openings named in the
  list) go to W2C.

## Fix now
Important, both halves (each with the test or capture check the review asks for):
- D-I1 synthetic label at every width, with a capture check; D-I2 openings clustered under the
  chosen destination only, each count with coverage and date, stale age on the label; D-I3 as
  ruled; D-I4 Skills draws the ground only, views raised so stretches spread, gates clear of
  lights, a check that no label or gate covers a light's centre; D-I5 names and legend at 768
  and 390 (a "What the lights mean" control at ≤1100 px, only drawn kinds, keys drawn as the
  world draws them, a capture check that fails on an unnamed light); D-I6; D-I7 (plain cost
  phrases, the y-axis named; TRACE-01 and DIRECTAI labels stay distinct).
- A-I1 typing hold resumes motion (turn the reviewer's probe into a test in `World.test.tsx`;
  the probe is in the scratchpad path the review names); A-I2 context loss and a failing
  renderer fall back to the still world with the same names, the probe context released;
  A-I3 a parity test that can fail (shown names, legend shown, across moving, reduced motion,
  calm and paused, per chapter, three viewports, a three-long-target workspace); A-I4 tablet
  and phone show the place above a short sheet, as the reference does, with the phone header
  on two rows, a light under a panel hides its name, and the test asserts shown names at every
  viewport; A-I5 the not-built card is the reference's five elements, "Uses these answers"
  one step away; A-I6 quiet and icon actions leave teal (text colour plus underline or glyph),
  and links leave teal too (D-M9).

Minor, fix now: D-M2 (except the strip), D-M3, D-M6, D-M7, D-M8, D-M10, D-M11 records,
A-M4, A-M6, A-M7, A-M8, A-M9, A-M10.

## Then
- Regenerate the references with the project's tools; keep the mirror byte-identical;
  `pnpm run contrast`, `check-data`.
- `make check`, then `make acceptance` once before the final commit (headless only).
- **No headed browser, no `open`, nothing that puts a window on the product owner's screen.**
- Same hard rules as the original dispatch: Edit/Write only for source; stage explicit paths;
  never `answers-2.md`; never `.env`, `~/.nessa`, `~/.careerwright`; no live calls; leave
  `spikes/world` unchanged; no subagents; never push.
- Append a "Fix round 1" section to `task-W2A-report.md`: each finding ID with what changed,
  the test or check that proves it, and anything you could not do. Reply with only the short
  contract.
