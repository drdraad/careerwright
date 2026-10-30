# Careerwright design references: the living world (Sprint W)

The design references for the direction the product owner chose at session W1: **Horizon,
made livelier**. Careerwright is one persistent, living world, not a set of pages (plan
section 4, ADR 0014). The person is the light at its origin; destinations are warm lights on
the horizon; trails of light grow between them; each chapter is a place the view travels to.
These references replace the Sprint 0 "calm observatory" compositions, which are in git
history before Sprint W.

**Status:** references built and checked by machine. **Human design approval: not run,
requires a human** (session W2, ruling R2).

## What is here

| Path | What it is |
|---|---|
| `tokens/tokens.css` | Canonical tokens, v0.2.0: primitives, semantic tokens, the `.on-space` and `.on-reading` contexts, type, space, radius and the motion vocabulary |
| `tokens/contrast-pairs.json` | Every text and meaningful non-text pairing, glass panels measured over the darkest ground and over the brightest light in the world |
| `tokens/contrast-report.md` | Generated measurements: **81 of 81 pass** (67 pairs) |
| `fonts/` | Outfit (display) and Source Sans 3 (body), with licence texts and provenance (`fonts/README.md`) |
| `compositions/index.html` | Gallery: every place and state |
| `compositions/world.html` | One place in one state: `?place=you\|roles\|skills\|options\|routes\|plan&state=…` |
| `compositions/world.js`, `world.css` | The still world in Horizon's geometry, and the exact layer over it |
| `compositions/data.js` | Fixture values (checked) and invented listings (labelled synthetic) |
| `screenshots/` | 28 PNGs (the six places at 1440×900, 768×1024 and 390×844, and each honest state) and `checks.md` |
| `tools/` | `contrast.mjs`, `check-fixture-data.mjs`, `screenshots.mjs` |
| `reference/luminous-path-forward.png` | The product owner's image: palette and mood |

## Reproduce

```bash
cd docs/design
pnpm install --frozen-lockfile
pnpm exec playwright install chromium   # once per machine; Playwright 1.64.1's pinned Chromium
pnpm run contrast        # rewrites tokens/contrast-report.md; exits 1 on any failing pair
pnpm run check-data      # asserts every fixture value in compositions/data.js equals fixtures/
pnpm run screenshots     # runs check-data, then captures every place and state, writes screenshots/checks.md
```

`screenshots` serves the folder on an ephemeral 127.0.0.1 port. Its checks per capture: axe
(WCAG 2.0, 2.1 and 2.2, A and AA tags), no horizontal overflow, no console errors, both fonts
loaded, every name in the world inside the window and clear of the panels and of each other,
the time and cost instrument's labels clear of each other and its marks, and at most one
filled primary action in view. The captures are the still world (reduced motion), which is
what calm mode and reduced motion draw; the moving world is in the app.

## The direction: Horizon, made livelier

The product owner's words at session W1: Growth and Circuit were "a bit too chaotic";
Horizon was "the most logical, but not quite right yet. The animations aren't as good as the
others, and its a bit too [noisy] with the dashed lines." So:

- **Keep Horizon's calm, lined-up layout.** A smooth dark plain under a glowing horizon.
  Every destination stands at one depth, in title order: where a light sits never means how
  near, likely or good it is. Every skill sits at one distance from the person.
- **Quiet solid trails.** No dashes anywhere. "Not known yet" is a solid slate trail, quieter
  than any known one, never absent. No side fibres: in the busiest scene they read as
  scattered strokes.
- **Livelier light.** The horizon breathes; an aurora of blue and violet drifts above it; a
  slow shimmer travels along the horizon line; mist drifts towards you across the plain;
  motes travel past; stars twinkle; trails sway a little (never at their ends, so lights never
  move); light flows outward along what is known; destinations breathe, each in its own phase,
  with a shimmering reflection on the plain. All of it is atmosphere: the same for every item,
  low in amplitude, held still while the person reads or types, and stopped by Pause motion.
- **Sound** (session W1: "subtle and evocative, not cheesy!"): a low swell when the person's
  light comes on, a soft two-note chime when a connection lights up, a small glass tick when a
  skill is picked. Off until the person turns sound on.
- **Lettering:** Outfit, the product owner's choice ("Keep Outfit").

## One colour, one meaning

| Colour | Means | Never |
|---|---|---|
| Orange (`--light-destination` `#FF9433`) | A destination: a place the person chose (filled) or one suggested (ring) | Status, a job offer, a rank |
| Sea-glass (`--seaglass-300` `#45F7D4`) | Selection, the chosen path and the one primary action | Focus (white), "on" for a switch (white) |
| Blue to violet (`--trail-near`, `--trail-far`) | The journey, graded the same along every trail from the person (blue) to the horizon (violet) | A category or an industry |
| Slate (`--trail-shadow` `#6F7EA3`) | Not known yet: shadow, never absence, never zero | |
| White | The person's light; focus rings; type | |
| Crimson (`--crimson-300`) and sand (`--sand-300`) | Failed and stale, always after a glyph and words | Any world meaning (ΔE76 ≥ 53 from every meaning hue) |

Industry is shown by glyph and label, never by colour (spec VIS-1's industry colours are
replaced, ADR 0014 decision 5).

## Tokens and contrast

Use the semantic names (`--text-on-reading`, `--surface-glass`, `--status-error-on-reading`,
`--light-destination`, …) or the context aliases inside `.on-space` (text straight on the
world) and `.on-reading` (a dark glass panel over it). Primitives are for `tokens.css` only.
The semantic names of Sprint 0 are kept; their values are now the world's.

Reading happens on dark glass panels opaque enough that nothing glowing behind them can pull
text below WCAG AA. Glass tokens carry their opacity (`#070B17E8`, 91%), and the contrast tool
composites each over the world's darkest ground and over pure white, the brightest any light
in the world can reach. Measured highlights (`tokens/contrast-report.md`):

- Primary text on a glass panel over the brightest light: 14.85:1. Captions there: 6.58:1.
- A light's caption on its label in the world, over the brightest light: 6.05:1.
- The tightest pairs: a control boundary on glass over the brightest light, 3.59:1; a shadow
  stretch where it meets the horizon's glow, 3.61:1 (both against 3:1).
- A destination's orange on the horizon's glow: 6.64:1.

## Type

| Use | Face | Size and weight |
|---|---|---|
| Chapter titles, the current question, names in the world, revelations | Outfit | 39 px titles (31 px on phones and on place cards), weight 650, tracking −0.015em |
| Body and interface | Source Sans 3 | 16 px body, 14 px secondary, 12 px floor |
| Numbers | Source Sans 3 tabular figures (its default) | as surrounding text |

## The motion vocabulary

Motion always means something; atmosphere is the same for every item. Every timing is a token
in `tokens.css`; reduced motion sets each to 0 ms, and calm mode draws the world still.

| Meaning | Motion | Timing (token) | In the still world |
|---|---|---|---|
| Feedback to any input | What was touched answers at once | ≤ 100 ms (`--motion-feedback`, 90 ms) | The control's state |
| Travel between places | The world stays, the view moves | 600 ms (`--motion-travel`), eased in and out | A cut |
| A new possibility | Its trail grows from the person outward | 650 ms (`--motion-grow`) | Drawn whole |
| New evidence | Ignition: the person's light flares and a ring runs across the plain | 1.4 s (`--motion-ignite`) | Lit |
| Ruled out by a decision | Dimming | 400 ms (`--motion-dim`) | Dim |
| A revelation | Ambient motion holds; light is staged; a card settles. Any input completes it | 0.6–1.8 s (`--motion-reveal`) | An instant change with its card |
| A stable fact | Settling | 320 ms (`--motion-settle`) | As drawn |
| Panels | Open and close | 260 ms (`--motion-panel`) | Instant |
| Atmosphere | One slow breath of light | 7 s (`--motion-breathe`) | None |

Nothing flashes more than three times a second. No information exists only in motion. A
visible control pauses ambient motion at any time (WCAG 2.2.2), and ambient motion stops
while the tab is hidden.

## The six places

| Place | Where it is | Its moment | Reference states |
|---|---|---|---|
| You | The origin: the person's light, skills around it, and the conversation's console | The first answer lights it and grows the first trails | default; distress (the world stills and dims, the calm support panel); failed (the message kept, the reply missing) |
| Roles | The horizon: suggested and chosen destinations, openings grouped by city | An unexpected connection, joined by shared essential skills | default; stale (sand, a clock and an age); unknown ("none found in the 4 sources checked", never "no jobs"); not built yet |
| Skills | The ground between the person and a destination, stretch by stretch | An answer lights a stretch already covered | default, with a gate ("Ready if you pass the assessed report"); unknown (all shadow); not built yet |
| Options | Bridges across the dark stretches | A gap gets its first bridge | default; unknown ("No bridge found yet", never "none exist"); not built yet |
| Routes | Whole journeys, compared on an exact time and cost instrument | A credible, checked route burns through | default (route B, conditional); failed (the last comparison kept, labelled); not built yet |
| Plan | The chosen path made solid, the next move glowing at its start | Committing | default; not built yet |

On a phone the world is the backdrop and each place is a sheet over its lower half; the world's
focus rises above the sheet. A chapter not built yet shows its place with a small card: "Not
built yet", where it is in the world, and what to do now.

## Honest states (glyph first)

| State | Glyph | In the world | Words in the references |
|---|---|---|---|
| Unknown | circle with a question mark | Solid slate trail, quieter than any known one | "Not known yet", "No bridge found yet", "none found in the 4 sources checked" |
| Conditional | diamond gate | A gate across the trail | "Ready if you pass the assessed report" |
| Stale | clock | Openings faded to sand | "Last checked 2 days ago" |
| Failed | triangle with a mark | Earlier results kept, faded | "The route search failed", "Careerwright's reply didn't arrive" |
| Synthetic | flask | Labelled in the strip and the top bar | "Synthetic demo"; invented examples say "an example" |
| Distress | (the support panel) | The world stills and dims; nothing glows | "Support is here, any time", with UK resources |
| Not built yet | circle with a bar | The place, with nothing drawn that is not known | "Not built yet" |

## Kept from Sprint 0

Semantic token names, glyph-first status, unknown drawn rather than omitted, failure, stale and
conditional looking different, Pareto layers told apart without colour (an open ring, a grey
disc, a grey ring), one primary action per view, chapters never numbered (visited is a ring,
never a fill), synthetic data always labelled, and fixture values checked by `check-data`.

## Not covered here (owners)

- Motion itself: these references are still. The moving world is in the app
  (`apps/web/src/lib/world/`, `src/components/World.tsx`) and its Storybook stories.
- The You chapter in the world, the first ten seconds and the revelations: Sprint W's next
  slices. Their words here are illustrative.
- The map at 100 openings, measured label placement and aggregation: Sprint 3 (Roles).
- The route instrument's full design (all nine DIRECTAI routes, the Gantt and the ledger):
  Sprint 7.
- WebKit and Safari, VoiceOver, an M1-class Mac: human checks (R2).
