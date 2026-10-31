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
| `tokens/tokens.css` | Canonical tokens, v0.2.3: primitives, semantic tokens (with the two decision colours, accept and undo, and a chosen Accept's faint leaf tint), the `.on-space` and `.on-reading` contexts, type, space, radius, each trail's drawn strength and the motion vocabulary |
| `tokens/contrast-pairs.json` | Every text and meaningful non-text pairing: glass panels measured over the darkest ground and over the brightest light in the world, and each trail measured as drawn, at its strength |
| `tokens/contrast-report.md` | Generated measurements: **132 of 132 pass** (100 pairs), with the status and decision hues' distance from every meaning hue |
| `fonts/` | Outfit (display) and Source Sans 3 (body), with licence texts and provenance (`fonts/README.md`) |
| `compositions/index.html` | Gallery: every place and state |
| `compositions/world.html` | One place in one state: `?place=you\|roles\|skills\|options\|routes\|plan&state=…` |
| `compositions/world.js`, `world.css` | The still world in Horizon's geometry, and the exact layer over it |
| `compositions/data.js` | Fixture values (checked) and invented listings (labelled synthetic) |
| `screenshots/` | 46 PNGs (the six places at 1440×900, 768×1024 and 390×844, each honest state, three long targets at all three sizes, the You console's review, saved, what-we-know and suggestions views at all three sizes, and Routes not built yet at all three sizes, as the app shows it until Routes is built) and `checks.md` |
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
loaded, the wordmark inside the rail, a visible "Synthetic demo" label, every name in the world
inside the window and clear of the panels, the key and each other, every light and gate in view
named (and no name left for a light out of view or under a panel), the revelation's subject in
view and named, no name, gate or key over a light's centre, every line from a name to its
light (as drawn) clear of the other lights, gates and names and of the key, the key clear of
the panels, shown whenever a light it explains is in view and only while something it explains
is, the time and cost instrument's labels clear of each other and its marks, no words clipped
in a panel (a text's box inside every box that clips it, up to its panel; a row that scrolls
sideways, a phone's view controls, clips nothing for good: its words are reached by
scrolling), the person's light
named above the You console in every view at 768 and 390 px with the band above it never under
MIN_BAND, and at most one action filled with a bright colour in view (by its computed fill: the
primary's sea-glass or a decision colour). The lights, gates and trails come from the drawing
(`window.__worldCheck`); whether a name, a line or the key can be seen is measured in the page,
so the check can fail. The captures are the
still world (reduced motion), which is what calm mode and reduced motion draw; the moving world
is in the app.

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
- **Livelier light, never overwhelming.** The horizon breathes; an aurora of blue and violet
  drifts above it; mist drifts towards you across the plain; a few hundred motes travel past;
  stars twinkle; light flows outward along what is known; destinations breathe, each in its own
  phase, with a shimmering reflection on the plain. All of it is atmosphere: the same for every
  item, low in amplitude, held still while the person reads or types, and stopped by Pause
  motion. After the product owner saw the busiest scene ("too busy … overwhelming"), the
  travelling shimmer along the horizon and the trails' sway were taken out, and the motes cut
  from 2,400 to 360: nothing moves without meaning, one idea at a time.
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
| Grey, the slate (`--trail-shadow` `#6F7EA3`) | Not known yet: shadow, never absence, never zero | Kept or failed results |
| White | The person's light; focus rings; type; links and quiet actions (underlined) | |
| Crimson (`--crimson-300`) and sand (`--sand-300`) | Failed and stale, always after a glyph and words; sand also draws what is kept from an earlier search (openings, routes) | Any world meaning (ΔE76 ≥ 53 from every meaning hue) |
| Leaf green (`--decision-accept` `#A6E25A`) | Accepting a proposed change, or confirming a limit, after its words and a tick; on a faint leaf tint with a doubled edge once chosen, never a second bright fill beside the one primary (session 2, C3: "colour coded buttons"; W2C fix round 1) | The primary action, selection, success in general (ΔE76 ≥ 56 from every other hue) |
| Orchid (`--decision-undo` `#FFAAFF`) | Undoing the last save, after its words and a turn-back glyph | Anything else (ΔE76 ≥ 44 from every other hue; nearest the journey's violet) |

The key to the lights lists only the kinds drawn at that place, each mark drawn as the world
draws it (a warm disc for a chosen destination, a warm ring for a suggested one, the diamond
only for a gate). Its words are plain: "Teal", "Grey", "Sand", never a token's name. At Routes
teal is "the route you're looking at"; only at Plan is it "the path you chose". On a wide
screen the key is open where the world beside the panels has room for it (360 px or more);
at 1100 px and below, or with less room, it is a "What the lights mean" control, placed
where the world is clear: at the right, low down, just above a panel or just below the bars,
and failing those at the left, taking the first spot from which every light can still be
named. It shows only while something it explains is in view (a light other than the person's,
a gate or a trail), and the menus open over it.

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
- Trails are measured as drawn: each state's strength is a token (`--trail-opacity-usual`
  0.85, `--trail-opacity-shadow` 0.9, `--trail-opacity-stale` 0.6; said, chosen, bridges and
  whole routes at full strength), composited over the ground and over the horizon's glow. The
  tightest: a grey "not known yet" stretch where it meets the horizon's glow, 3.19:1; a usual
  trail there, 3.43:1 (violet end; along the blue to violet grade, worked out by hand, never
  below 3.38:1); a control boundary on glass over the brightest light, 3.59:1 (all against
  3:1). The app's still world draws the same strengths (`TRAIL_OPACITY`, and a test holds its
  strokes to it), and the moving world draws each trail's core at least at them (its glow and
  the light flowing along it only add).
- One recorded exception: while the calm support panel shows, the world is a dimmed, still
  backdrop (plan section 4: distress "stills and dims"), and its trails may then fall below
  3:1. Every name and state stays in the list beside it, and the person is not reading the
  world then. Nothing else is exempt.
- A destination's orange on the horizon's glow: 6.64:1.
- The rail: solid (94%) where its landmarks sit and 80% at its outer edge, where a chapter's
  name is still 7.39:1 over the brightest light.

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
| You | The origin: the person's light, skills around it, and the console: three views as tabs, one idea each (Conversation, What we know, Suggestions; session 2's findings, SW.4) | The first answer lights it and grows the first trails | default; review (a reply's proposals: Confirm in leaf green, on a faint tint once chosen; a limit explained in plain words; saving them the one bright action; the next question waits until they are decided); saved (what the decision did, where it was made, Undo in orchid, then the next question); known (What we know, both limits explained, the early sketch one step away); suggestions (a real slate's shape, "data analyst": the view's controls, the count line and the search notes one step away; one open, edged as the selection, its "Make this a target" the bright action right after its title; the rest titles to scan). On a tablet and a phone the person's light stands in a band of world above the console in every view (never under MIN_BAND), and on a phone the top bar names the chapter, so the console's own title is for assistive tech only; distress (the world stills and dims, the calm support panel); failed (the message kept, the reply missing) |
| Roles | The horizon: suggested and chosen destinations; the chosen one's openings clustered below it by area, each count with its sources and date (on a phone, listed in the sheet) | An unexpected connection, joined by shared essential skills | default; stale (sand, a clock, the age on each count); unknown ("none found in the 4 sources checked", never "no jobs"); three long targets; not built yet (and, in the gallery, the key opened on a narrow screen) |
| Skills | The ground between the person and a destination, stretch by stretch (the skills around the person belong to You) | An answer lights a stretch already covered | default, with a gate ("Ready if you pass the assessed report"); unknown (all shadow); not built yet |
| Options | Bridges across the dark stretches | A gap gets its first bridge | default; unknown ("No bridge found yet. That doesn't mean there are none."); not built yet |
| Routes | Whole journeys, compared on an exact time and cost instrument | A credible, checked route burns through | default (route B, conditional); failed (the last comparison kept in sand, marked "Kept from your last search", "Search again"); not built yet |
| Plan | The chosen path made solid, the next move glowing at its start | Committing | default; not built yet |

Seen from above, the ground's stretches spread across the clear part of the window: each is cut
at an equal length on screen (where a stretch begins means nothing), and a gate stands where the
last stretch begins, clear of the destination's light.

The cost words are plain and kept apart: TRACE-01's economic cost is "Total cost, including pay
you'd give up" (the instrument's upright axis), its direct spending "What you'd pay out"; the
DIRECTAI routes' direct spending keeps its own label.

The view stands the place where the panels leave the world clear: beside the panel on a wide
screen (moved only where its usual place would be too near the panel), and above (or below) the
panels on a tablet or a phone, made smaller only if it must be; where the panels leave no room
at all (a tall You console on a tablet) the world is a backdrop standing behind them, so no
light peeks out beside a panel where its name has no room. The app does the same
(`apps/web/src/lib/world/geometry.ts`). A light that is still under a panel hides its name.

The strip speaks plainly: "Answers saved" (never a version number), and nothing about live
updates while they work; a state that isn't live names itself ("Updates: Reconnecting"). On a
tablet it is two rows (the synthetic label and the target; then the states and controls); a wide
screen adds the work area. On a phone the header is two rows (the chapter and the synthetic
label; then the saved state, any update state, Pause motion and Sound as glyph buttons, ringed
in white when on, and the account menu, where calm mode and how Careerwright talks with you keep
their words); the target is named in the world. While the calm support panel shows, "Still
while support is shown" sits in the strip, or on a phone in the top bar beside the chapter,
where it adds no row.

A name sits beside its light; a crowded one steps out a row with a fine line back to its light.
That line never crosses another light, gate or name, or the key, and no name sits on a line
already drawn: a line joins a name to its own light only. A name left without a spot chooses
first on the next try, and the try that leaves the fewest lights unnamed is kept. A long name
wraps, its mark staying on its first line; on a phone a name shows without its caption (the
key explains each look, and the caption stays in the list for assistive tech). At Roles the
chosen destination's openings stand just in front of it, by area, their names stepping down
from the rightmost so each line passes the names above it; the Roles card is narrower (480 px)
so they have room beside it. On a phone the areas would stand a few pixels apart, too close to
name apart, so the sheet lists each area's openings in the same words instead.

A chapter not built yet shows its place with a short card: "Not built yet", the place, where it
is in the world, one sentence on why it is empty and the one action; what it will hold is one
step away ("More about this place").

## Honest states (glyph first)

| State | Glyph | In the world | Words in the references |
|---|---|---|---|
| Unknown | circle with a question mark | Solid slate trail, quieter than any known one | "Not known yet", "No bridge found yet", "none found in the 4 sources checked" |
| Conditional | diamond gate | A gate across the trail | "Ready if you pass the assessed report" |
| Stale | clock | Openings in sand, with their age on each count | "Last checked 2 days ago", "…, 2 days ago" |
| Failed | triangle with a mark | Earlier results kept, in sand, marked as kept | "The route search failed", "Kept from your last search", "Careerwright's reply didn't arrive" |
| Synthetic | flask | Labelled in the strip at every width, and in the phone's top bar | "Synthetic demo"; invented examples say "an example" |
| Distress | lifebuoy (support) | The world stills and dims; nothing glows. Pause motion keeps showing the person's own choice; the strip (on a phone, the top bar) says "Still while support is shown" | "Support is here, any time", with UK resources |
| Not built yet | circle with a bar | The place, with nothing drawn that is not known | "Not built yet" |

"You said so" has its own glyph (a speech bubble), never the tick that means complete, and "Set
aside" its own (down into a tray), never "not built yet".

## Kept from Sprint 0

Semantic token names, glyph-first status, unknown drawn rather than omitted, failure, stale and
conditional looking different, Pareto layers told apart without colour (an open ring, a grey
disc, a grey ring), one primary action per view, chapters never numbered (visited is a ring,
never a fill), synthetic data always labelled, and fixture values checked by `check-data`.

## Not covered here (owners)

- Motion itself: these references are still. The moving world is in the app
  (`apps/web/src/lib/world/`, `src/components/World.tsx`) and its Storybook stories.
- The first ten seconds (the first question's type-ahead and the ignition) and the
  revelations: the second part of Sprint W's You slice. Their words here are illustrative. The
  unexpected connection is named in the world but not yet singled out by light.
- Industry shown by glyph and label: no reference draws an industry yet (Sprint 3, Roles).
- The map at 100 openings, measured label placement and aggregation: Sprint 3 (Roles).
- The route instrument's full design (all nine DIRECTAI routes, the Gantt and the ledger):
  Sprint 7.
- WebKit and Safari, VoiceOver, an M1-class Mac: human checks (R2).
