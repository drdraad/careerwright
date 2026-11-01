# Task W2A review: the design half

Reviewer: design half (`docs/`, the mirror in `apps/web/src/design`). Package
`review-W2A-design.diff` (c1bc2f3..65aed2f), read in passes: ADR 0014, `dependencies.md` and the
README first; then `world.js`, `world.css`, `index.html`, `data.js`; then tokens, contrast pairs,
the contrast and screenshot tools, the fonts README and the frame evidence. Deleted Sprint 0
compositions skimmed only. I opened all 28 PNGs in `docs/design/screenshots/`.

Checks I ran (read-only): `cmp` of all five mirrored files (identical); `shasum -a 256` of the
font and licence files (match `fonts/README.md`); `node tools/check-fixture-data.mjs` (64
assertions pass); a scratch script recomputing composited contrast with the contrast tool's
formula (results below). I did not run the screenshot or contrast tools (both rewrite tracked
files), nor anything headed.

The product owner's later word on `you--default--1440x900.png` and `roles--default--1440x900.png`
("no, they look OK") is applied: busyness alone is Minor unless it breaks truth, colour meaning or
contrast, or crowds at 768×1024 or 390×844.

### Spec Compliance

- ❌ Issues found:
  - The "Synthetic demo" label is missing from every 768×1024 capture
    (`docs/design/compositions/world.css:681-684`, `world.js:350`). See I1.
  - Opening counts sit under the wrong destination, with no source or date
    (`world.js:139-153`). See I2.
  - The contrast measurements for the world's trails don't match what is drawn
    (`contrast-pairs.json` trail rows vs `world.js:270-281`). See I3.
  - The Skills place draws one skill twice, with opposite states (`world.js:121-128`,
    `156-180`). See I4.
  - Names and the legend go missing or get covered at 768 and 390, and the screenshot check for
    names can't fail (`world.js:569-578`, `screenshots.mjs:73-84`). See I5.
  - The Routes legend says "the path you chose" before anything is chosen (`world.js:526`).
    See I6.
  - "Economic cost" sits beside "Direct spending", and the cost axis has no name
    (`world.js:401-402`, `497-498`). Plan v1.4 section 4 names this exact pair as one the product
    owner couldn't follow. See I7.
- Met:
  - Six places at three viewports, plus unknown, conditional, stale, failed, synthetic, distress
    and not-built states.
  - Sprint 0 compositions retired.
  - The mirror is byte-identical and still holds only fonts and tokens (Newsreader swapped for
    Outfit; `designMirror.test.ts` enforces the file set).
  - `check-data` still checks fixture values: 64 pass. Every fixture figure the world shows
    comes from checked `FIXTURES`.
  - ADR 0014 decisions 2, 6 and 8 recorded with the product owner's words.
  - three.js 0.186.1 (MIT, 2026-09-24, 36 days old), `@types/three` 0.186.0 and all six
    transitive packages recorded with dates (lockfile `apps/web/pnpm-lock.yaml:3813-3820`
    agrees).
  - Outfit 1.100 recorded with source, licence and hash, and the hashes match.
  - No human-only gate is claimed. The README, `checks.md` and the report all say "not run —
    requires human".
- ⚠️ Cannot verify from the diff:
  - The moving world's look and the character of the sounds: human, session W2.
  - Whether Outfit's file really is from `google/fonts@8b0a1d0`. No network was used; the hash
    is recorded and matches the file on disk.
  - The headed frame runs. I'm not allowed to repeat them; the JSON agrees with the report's
    table.
  - Safari, VoiceOver, an M1.

### Strengths

- The honest states read well:
  - "Leeds: none found in the 4 sources checked … Not 'no jobs'".
  - "Last checked 2 days ago … may have closed".
  - "Careerwright's reply didn't arrive. Your message is kept. Nothing about you changed."
  - "Not built yet" cards say what each place will be and that nothing has been searched.
  - Nothing reads as a job offer, and Roles says "Not a job offer".
  - Unknown is never zero.
- Distress is right in substance. The world dims and stills, the reply only acknowledges and
  offers a smaller step, the support panel carries UK resources, and the panel says "Your
  message was sent as usual".
- Colour meanings are mostly held:
  - Orange appears only on destinations (lights, label markers, keys).
  - Teal is on the selection, the chosen path at Plan and the one filled action.
  - Focus is white, with a dark halo (`world.css:49-53`).
  - The switch "on" is white (`world.css:374-378`).
  - Crimson and sand are ΔE76 ≥ 53 from every meaning colour.
  - The industry colour tokens are gone.
- The contrast tool now composites glass over named backdrops. The 91% glass measurement is
  correct: I get 2.46:1 at 80%, 3.07:1 at 86% and 3.60:1 at 91% (floored to 3.59:1). The
  tool's error when a translucent background has no backdrop is a good guard.
- The fixture link is kept. Route B's months, dates, payments, £600, £4,850 and the fronts all
  come from the checked `FIXTURES`.
- The fonts README is clean and honest about provenance. Newsreader is removed from both trees,
  and the mirror test rejects retired files.

### Issues

#### Critical

None.

#### Important

**I1. No "Synthetic demo" label at 768×1024.**
- Where: `docs/design/compositions/world.css:681-684` hides `.strip .optional` at ≤1100 px.
  `world.js:350` puts the synthetic label inside `.optional`. The `.topbar`, which carries it on
  a phone, is hidden at ≥761 px (`world.css:758`).
- What happens: every `*--768x1024.png` shows invented opening counts and fixture route figures
  with no synthetic label anywhere (see `roles--default--768x1024.png` and
  `routes--default--768x1024.png`). Global Constraint 5 says synthetic data stays labelled, and
  these captures go to session W2.
- The app is right here: `apps/web/src/app/globals.css:925` hides `strip-optional` only at
  ≤760 px, where its top bar shows the label. So the reference contradicts the product it
  specifies.
- Fix: take the synthetic label out of `.optional` (or mirror the app's breakpoint). Add a
  screenshot check that a visible "Synthetic demo" exists in every capture.

**I2. Opening counts sit under the wrong destination, with no source or date.**
- Where: `world.js:144` centres the three area clusters at the target ±2.6 units. "Manchester:
  8 openings" therefore sits under "Business analyst" in `roles--default--1440x900.png` and in
  the 768 capture.
- Why it matters: the world appears to give Business analyst eight Manchester openings. Plan
  section 4 puts openings "around a chosen one", and position must never imply a connection.
- Only the unknown state names its sources. The default counts carry no source or date. In the
  stale state the world labels still read "Manchester: 8 openings" with no age; the age is only
  in the panel.
- Fix:
  - Cluster openings tightly below the chosen destination only, with the area labels attached
    to it.
  - Give each count its coverage and date, e.g. "Manchester: 8 openings, 4 sources, today".
  - In the stale state, put the age on the label too ("…, 2 days ago").

**I3. Trail contrast is measured at full strength, but trails are drawn faded.**
- Where: `contrast-pairs.json` measures `--trail-shadow`, `--trail-near` and `--trail-far` as
  opaque colours. The still world draws them faded:
  - shadow at 0.8, usual at 0.55, stale at 0.45 (`world.js:270-281`);
  - the app's still world uses the same values (`apps/web/src/components/StillWorld.tsx:12-17`,
    other half).
- Measured as drawn (contrast tool's formula):

  | Trail | Opacity | Over the horizon | Over the ground |
  |---|---:|---:|---:|
  | Shadow ("not known yet") | 0.8 | 2.82:1 | 3.56:1 |
  | Usual, blue | 0.55 | 2.34:1 | 2.53:1 |
  | Usual, violet | 0.55 | 2.24:1 | 2.42:1 |
  | Stale route | 0.45 | 1.77:1 | 1.83:1 |

  All need 3:1. So the README's highlight, "a shadow stretch where it meets the horizon's glow,
  3.61:1" (`README.md:98-99`), describes a colour that is never drawn.
- Sprint 0 measured composited opacities explicitly (map branches at 75%). W2A dropped that.
- Fix: either
  - (a) add an `alpha` to these pairs (the tool already composites) and raise the drawn
    opacities until they pass (shadow needs roughly ≥0.9 over the horizon), or
  - (b) declare the trails decorative, because the words in the DOM carry their meaning, and
    remove them from the 3:1 claim.
  Pick one rule and apply it to the app too.

**I4. Skills draws one skill twice with opposite states, and labels or the gate cover the lights
they explain.**
- Where: `world.js:121-128` draws the person's skill fan at Skills as well as You. `156-180`
  also draws the ground's stretches.
- What happens:
  - `skills--default--1440x900.png` shows two different lights both named "Check data for
    errors".
  - `skills--unknown--1440x900.png` shows "Check data for errors — you said so" and "Check data
    for errors — not known yet" at the same time, a direct contradiction.
- The low view (`VIEWS.skills` eye 0.42, `world.js:52`) squashes the ground into about 120 px.
  The stretch labels then pile up on the horizon:
  - "Query related tables" covers the destination's light (Skills 1440).
  - The gate the legend lists isn't visible (Skills 1440).
  - The gate diamond sits on the destination's light (Skills 768, and Plan at all three sizes).
  - "Remote: 3 openings" covers the selected target's teal ring (`roles--default--390x844.png`).
  - Options at 1440 and 768 stacks three labels on the destination.
- The screenshot tool checks names only against panels and each other, never against lights or
  gates (`screenshots.mjs:78-84`).
- Fix:
  - Skills draws the ground only (the fan belongs to You).
  - Raise or tilt the Skills and Options views so the stretches spread across the clear span.
  - Keep a gate clear of the destination's light.
  - Add a check that no label or gate covers a light's centre.

**I5. Names and the legend vanish or are covered at 768 and 390, and the name check can't fail.**
- Names: `world.js:569-578` turns any name that doesn't fit into a screen-reader-only item. The
  tool examines only placed `.world-label`s (`screenshots.mjs:77`), so "clear of the panels and
  of each other" holds by construction.
- What the person loses:
  - At 768, Statistician, the subject of the revelation, has no name.
  - At 390, Manchester, the person's own work area, has no count.
  - Routes at 768 and 390, and Skills and Options at 390, place one name each, with lit marks
    left unexplained.
- The phone legend is also hidden (`world.css:746-756`), on the claim that "each name in the
  world carries its own meaning in words". That claim fails, because the names are hidden too.
  On a phone the bright, ring and slate states have no visible meaning.
- The legend at 768 sits under the panel (legend `z-index: 1`, shell 2, `world.css:158/221`). It
  shows only as clipped "…head for" and "…de it" in the roles, skills, options and plan 768
  captures. No check covers the legend against the panel.
- The legend also lists marks that aren't drawn: Gate at Options (`world.js:196`; no gate is
  drawn there). It omits one that is: the gate at Plan.
- Its keys don't match the world's marks. Destination and suggested keys are diamonds
  (`world.css:124-143`, `world.js:521`, "Warm rings" drawn as a diamond), while the world draws
  discs and rings. The diamond is the gate and conditional shape.
- Fix:
  - Fail the capture when a drawn light in view has no visible name and no visible key, or when
    the revelation's subject is unnamed.
  - On ≤1100 px, make the legend a "What the lights mean" button instead of hiding it or letting
    it sit under the panel.
  - List only the kinds drawn.
  - Draw the keys as the world draws them (disc, ring).

**I6. Routes says "the path you chose" before a choice, and failure reuses the "not known yet"
colour.**
- Where: `world.js:219` and `526`. At Routes, B is only selected: the primary action is still
  "Choose route B". Yet the legend says "Sea-glass: the path you chose". That states a decision
  the person hasn't made, against plan section 4's "act, see the consequence, then confirm".
- In the failed state:
  - The kept routes are drawn in slate (`world.js:275-277`), the colour that means "not known
    yet". They are known but possibly out of date, and the README gives stale the colour sand.
  - The instrument keeps B's teal selection ring (`world.js:398` ignores state) while the world
    drops it.
- Fix:
  - Word the key by state: "the route you're looking at" at Routes, "the path you chose" only
    at Plan.
  - Draw kept routes faded in their own colours or in sand, never slate.
  - Make the instrument's ring follow the same state.

**I7. The cost words the product owner couldn't follow are back.**
- Where: `world.js:497-498` shows "Economic cost £600" beside "Direct spending £600". Plan v1.4
  section 4: "'economic cost' against 'direct cost' … give way to plain phrases on screen".
- The instrument's money axis has no name (`world.js:401-402`: £ ticks and "Months to ready"
  only). A reader can't tell which cost the marks show, and the TRACE-01 and DIRECTAI labels
  must stay distinct.
- This is plan-mandated.
- Fix:
  - Use plain phrases, e.g. "Total cost, including pay you'd give up" and "What you'd pay out".
  - Name the y-axis with the TRACE-01 phrase.

#### Minor

**M1. "Never overwhelming": reductions.**
- Counts at 1440:
  - Skills: about 30 readable items at once (7 names, a 5-row legend, an 8-item strip, the rail
    and the wordmark, a 7-element panel).
  - You and Roles: about 28.
- At 390: two rows of strip plus the top bar take about 155 of 844 px.
- At 768: the strip wraps to two rows and clips the wordmark (M8).
- Reductions, each keeping its truth:
  - (a) Strip:
    - Drop "Saved, version 3" and "Updates: Live" at rest. Show the update state only when it
      isn't live; it stays an alert, so failure stays visible.
    - Drop "Target" and "Work area": the destination is named in the world, and the work area
      belongs to Roles.
    - Keep "Synthetic demo" at every width.
    - Fold Calm mode and Sound into one "Motion and sound" menu, but keep Pause motion as its
      own visible button (WCAG 2.2.2).
    - Eight items become three, plus the account menu.
  - (b) Show a world name's caption ("usual in your role, not confirmed yet") on the selected,
    hovered or focused name only. The DOM list and the legend keep every state.
  - (c) Drop the "Route A–E" names in the world at Routes except the selected one. The
    instrument names every route.
  - (d) The legend shows only drawn kinds (I5).
  Note: the app's strip carries even more (workspace switcher and budget too, about 11 items),
  so the reference understates it. Other half.

**M2. Plain words.**
- Strings to fix:

  | Text | Where | Problem |
  |---|---|---|
  | "Saved, version 3" | `world.js:354` | "version" is internal |
  | "Updates: Live" | `world.js:355` | jargon |
  | "from version 14" | `world.js:493` | "version" is internal |
  | "Sea-glass", "Slate" | `world.js:524`, `526` | design-token names used as product words; say "teal", "grey" |
  | "skills matrix", "isn't part of this build yet" | `world.js:371-375` | jargon; say "isn't ready yet" |
  | "That is not 'none exist'." | `world.js:480` | awkward; say "That doesn't mean there are none." |
  | "Place this bridge", "Tell me about a stretch" | `world.js:485`, `471` | actions named in metaphor; say "Use this course", "Tell me about a skill" |
  | "The world goes quiet while you read: no revelations, no celebrations." | `world.js:430` | explains mechanics to a person in distress; drop it |

- The strip strings also come from the app (`WorkspaceStrip.tsx`), so that's the other half.

**M3. Glyphs used for two meanings.**
- The support panel uses the "unknown" question mark (`world.js:418`).
- "Set aside" uses the "Not built yet" glyph (`world.js:483` vs `363`).
- "You said so" uses the complete tick (`world.js:465`). It reads as verified, but plan
  section 4 separates "self-reported" from "evidenced".
- Fix: give support, set aside and said their own glyphs.

**M4. Distress turns the person's Pause motion switch on** (`world.js:340`). If distress drives
the person's own control, switching it off mid-distress either restarts motion (against "distress
stills the world") or does nothing, so the control misleads. Fix: keep Pause showing the person's
own choice, and show "Still while support is shown" as a separate status. W2C should take note.

**M5. The revelation isn't singled out in the world.** The Roles card states the connection, but
Statistician is an identical ring at the window's edge, with no light and no joining trail
(`roles--default--1440x900.png`). That falls short of decision 4's "singled out by light". The
README defers revelations to later slices (`README.md:136` vs "Not covered"), so this is Minor.
Still, a still capture of the connection lit would give W2C a target.

**M6. Two primary actions don't fit their state.**
- `routes--failed` still offers "Choose route B" on a comparison that "may be out of date", and
  the kept instrument and facts carry no stale mark.
- `options--unknown` offers "Place this bridge" when there is no bridge.
- Fix: "Search again" and "Look for a course" respectively.

**M7. Gaps in tokens and contrast.**
- `--motion-breathe` isn't set to 0 under reduced motion (`tokens.css:187` vs `231-242`), but
  `README.md:113` says every timing is.
- The rail's background is an untokenised literal fading from 94% to 60% (`world.css:235`).
  Muted text over white at the 60% end measures 3.40:1. Text mostly sits in the 94% zone, which
  passes at 11.42:1.
- Not in `contrast-pairs.json`, though all pass:
  - selected label ring on label glass over white: 7.21:1;
  - destination marker on label glass: 4.43:1;
  - instrument marks on glass: 6.59:1;
  - the strip's `--surface-glass`: the same value as `--surface-reading`.
- Fix: add these pairs, and tokenise the rail's background and the teal glows.

**M8. Wordmark clipped at 768.** "Careerwright" overflows the 88 px rail (`world.css:238-252`).
At 768 the two-row strip covers its end ("Careerwrigh"). Overflow checks don't catch it.

**M9. Teal links.** "Why?" (`world.js:455`, `.link` at `world.css:511`) and the gallery's links
(`index.html:20-21`) are teal. That puts a second teal action next to the one primary. Fix: white,
underlined links.

**M10. Coverage gaps.**
- No capture tests three targets or long role names (plan section 5). Roles' label row is
  already tight at five destinations.
- The README says "Industry is shown by glyph and label" (`README.md:81`), but no reference draws
  an industry glyph. List it under "Not covered" (Sprint 3).
- "Pay not stated on 3 openings" is typed by hand (`world.js:454`), not read from
  `DESIGN_LISTINGS`.

**M11. Records.**
- Outfit's pinned commit has no date or age (`fonts/README.md`, `dependencies.md:143`).
- `dependencies.md:147`'s package count and licence tally are from before W2. Re-run
  `pnpm licenses list` (rapier is Apache-2.0).
- ADR 0014 decision 6 said "The spike chooses the faces" (`:67`), and the spike chose Atkinson
  Hyperlegible Next for body text (`spikes/world/README.md:197`). Keeping Source Sans 3 is
  recorded as "Task W2's ruling" (`:70`), not as "provisional — needs product owner
  confirmation" (R6).

**M12. Frame evidence.**
- `world-frames.json` records no commit and doesn't say the scene is invented.
- Its `over16` key counts intervals over 16 ms, not the 16.7 ms budget. The headless 60 Hz run
  therefore shows 210 of 720 "over16" at a steady 16.7 ms (`:125`).
- Fix: add the commit and "synthetic", and use an `over16_7` key.

### Verdicts on the implementer's rulings (design half)

1. **Body face stays Source Sans 3.** Agree on the merits. It is measured, licensed and has
   tabular figures, and plan section 4 asks only for "a highly readable sans". Session W1
   answered heading lettering only. But the ADR had delegated faces to the spike, which chose
   Atkinson, and the product owner judged looks set in it. Mark it provisional and put it on
   session W2's list (M11).
4. **Calm mode moved into the visible controls.** Agree that it must be easy to find. But
   together with Sound it adds to the strip; group them (M1a), with Pause still visible.
5. **No side fibres.** Agree. It fits "quiet solid trails" and the product owner's "too
   chaotic"/"noisy".
6. **White focus and a white switch "on".** Agree. It keeps teal to its meanings, and the dark
   halo is in place (`world.css:49-53`).
9. **Glass at 91%.** Agree. I verified the measurement exactly: 2.46, 3.07 and 3.60 (floored
   3.59). But "every pairing over the brightest light" isn't complete: the trails as drawn fail
   (I3), and the rail and a few label pairings are unmeasured (M7).
11. **Measurement at device scale 2, synthetic scene.** Agree with the method. The JSON needs the
   commit and the synthetic label (M12).

Rulings 2, 3, 7, 8, 10 and 12 are the app's: the other half.

### Assessment

**Spec compliance:** Issues found.
**Task quality:** Needs fixes.
**Reasoning:** The references cover every place and honest state, the fixture link holds and no
human gate is claimed. But the 768 captures drop the synthetic label, the Skills place
contradicts itself, the trails' contrast claim doesn't match what is drawn, and the screenshot
checks for names and the legend can't catch what goes wrong at 768 and 390. All are fixable
within the references and their tools.

Counts: Critical 0, Important 7, Minor 12.
