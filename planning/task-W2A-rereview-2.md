# Task W2A, fix round 2: scoped re-review

Reviewer: scoped re-reviewer, read-only. Package `review-7ac80dc..c84729e.diff` (commits `70d95e6`
design, `c84729e` app), read in passes: the app's e2e, CSS and components; `labels.ts` and its
tests; the docs and tools; then `world.js`. I opened 12 reference PNGs at `c84729e` and the same
scenes at `7ac80dc` (`git show` into the scratchpad), and 3 of the app's final acceptance
captures (`apps/web/test-results/visual-*`, 22:30–22:31).

Checks I ran (read-only, nothing headed, no network): reads of `StillWorld.tsx`, `World.tsx`,
`WorldControls.tsx`, `WorkspaceShell.tsx`, `globals.css` (stacking, the phone block's bounds,
`.world-key`, `.popover`), `geometry.ts` (`Clear` is in screen coordinates), `screenshots.mjs`
and `world.css` (the line check reads `::after` `left` and `height`, both set in px); a grep for
every "3:1 as drawn" claim; a grep for overlays without a portal. I hand-computed the expected
spots in the two rewritten label tests and the new line test from the placement rules. Not run:
`make check`, `make acceptance`, Vitest, Playwright, the screenshot and contrast tools.

### Spec Compliance

- ✅ Spec compliant: every dispatch item is fixed, each with a check that can fail, and both
  controller rulings are met.
- ⚠️ Cannot verify from the diff: that `make check` and `make acceptance` ran on the committed
  tree (the app captures are timestamped 22:30–22:31, before the 22:35 commits, which fits the
  report); the product owner's view of the narrower Roles card and the phone's openings list
  (session W2, recorded as not run).

## Verdict per item

"Can fail" means: if the fix were undone, the named check would go red.

| Item | Verdict | Evidence | Can its check fail? |
|---|---|---|---|
| Important (D-I3): still world's trail strengths | **Fixed** | `StillWorld.tsx` draws each core with `TRAIL_OPACITY[trail.state]` (diff 540); its `OPACITY` table is gone. Records now true and carry the exception: `docs/design/README.md:118-129`, ADR 0014:85-91, `palette.ts:28-34`. | Yes. `StillWorld.test.tsx` selects `:scope > g:not([filter]) > path`, which in `StillWorld` is exactly the core group (the glow group has `filter`, the nodes group holds `g > circle`). Against the old table, usual 0.55, shadow 0.8 and opening 0.4 fail; said 1 passes (3 of 4, as reported). `tokens.test.ts` holds `TRAIL_OPACITY` to the tokens, so the chain is closed. |
| A-M1 / A-M10: calm mode on a phone | **Fixed** | Phone rules scoped to `.world-controls` (`globals.css:995-1010, 1106`); `CalmMode` is a bare `Toggle`, not inside `.world-controls`; the account menu is also portalled. | Yes, but only if both the scope and the portal are undone: either alone keeps calm mode out of the strip's phone rules. The test guards the behaviour, which is what matters. |
| Minor 1: lines cross lights and names | **Fixed** | `labels.ts` `clearLine` (line vs names, key, other lights) and `lines` (no name on a drawn line); `world.js` the same, plus gates. Captures: `roles--default`, `roles--stale`, `you--default`, `you--distress` (1440) and `roles--three-targets--390` have no line through another light or name. | Yes. `screenshots.mjs` measures each drawn `::after` (px `left`/`height` from `world.css:117-133`) against the drawing's own lights, gates and the page's names and key; reported 77 failures on `HEAD`'s compositions. `labels.test.ts` line test: I hand-checked that the old rule puts `second` at row 2 above with its line through `first`'s name, so it fails on the old code. Side effect: route names now drop out (new Minor 1). |
| Minor 2: marker on its own line | **Fixed** | Disc is `.world-label-name::before`, inline (`globals.css:223-233`, `world.css:1682-1698`). `roles--three-targets--1440/390`: disc on the first line. | Plausibly. `marksOnTheirOwn` fails when a label is more than 6 px taller than its name; with the disc back as a flex item, a wrapped ~55-character name (wider than the 336 px the label allows) adds an 8 px line. Not shown failing first, and only if a long name is shown in the moving world at Roles. |
| Minor 3: key over the menus | **Fixed** | The workspace, account and chapter menus use `Popover.Portal`; Radix copies the content's z-index 30 to its wrapper at the root, over the key's 5. No other overlay lacks a portal except the evidence drawer, which the key already avoids as a cover. | Yes. Without the portal the menus sit inside `.app` (its own stacking context at z-index 1, `globals.css:317-319`), the key is a root sibling at 5, so `elementFromPoint` returns the key. The key has no `pointer-events: none`, and the test makes it visible before probing, so the probe can hit it. |
| Minor 4: stale coverage | **Fixed** | `world.js` `AREAS`: "Remote: 3 openings, 3 sources, today"; kept areas "4 sources, 2 days ago". Seen in `roles--stale--1440x900.png`. | Capture review (no check asked). |
| Minor 5: distress dim | **Fixed** (ruling met) | The exception is stated wherever "3:1 as drawn" is claimed: README:125-129, ADR 0014:88-91, `contrast-pairs.json` about, `contrast.mjs`/report method, both `tokens.css` copies, `palette.ts`. My grep found no other claim. Nothing else is exempt: no other filter or opacity applies to `.world-layer`. | Records only. |
| Minor 6: distress on a phone | **Fixed** | `StillWhileSupport` in the top bar, strip copy `display: none`, both inside the `max-width: 760px` block (`globals.css:951-1114`), so exactly one status shows at any width (the top bar is `display: none` above 760). Key shows only while something it explains is in view (`World.tsx` `keyPoints`, `world.js` `explained`). `you--distress--390x844.png`: no third row, no empty key. | Yes. Keep the status in the strip and the top bar locator finds nothing; unhide the strip copy and the strip wraps to a third row (as `7ac80dc`'s capture shows), so the height check fails. The empty-key half is checked in `screenshots.mjs` only (see Minor 3 below). |
| Minor 7: key can vanish unnoticed | **Fixed** | `screenshots.mjs` fails a light or gate in view with no key; `world.spec.ts` fails names in view with the key unplaced. It found a real gap (You at 1440), now handled by opening the key only with 360 px of room. | Yes. Reported mutation: all 10 Roles captures fail with the key never placed; the e2e check failed on real code first. |
| Minor 8: three-targets strip | **Fixed** | Strip names all three (`roles--three-targets--1440x900.png`). | Capture review. |
| Minor 9: two unreported changes; routes' own state | **Fixed** | Both recorded in the report. Unselected routes are `route`: full core, quiet glow 0.12 (`world.js` `bright` covers said, chosen and bridge only). The full-strength pairs now name whole routes. | The full-strength pairs measure the core; capture `routes--default--1440x900.png` shows the quieter glow. |

### Rulings and the controller's questions

- **Distress dim:** recorded everywhere the claim is made; nothing else is exempt. Met.
- **Unselected routes:** their own drawn state, `route`, not "said". Met.
- **Did the product owner's approved captures change materially?** No.
  - `roles--default--1440x900`: same lights, names, card content and key. The card is 80 px
    narrower, so the headline breaks after "and" and the body after "A place". The openings
    stand under the target, tighter, and their names now read Remote, Leeds, Manchester from top
    to bottom (Manchester, the person's own work area, was first before). Lines are shorter and
    pass beside the names above them. Nothing lost; not worse.
  - `you--default--1440x900`: "Work to deadlines" moved below its light instead of above
    (before, its line ran through "Keep accurate records"); "Use spreadsheets" sits lower. It is
    the round 1 defect removed, nothing else.
- **Does the phone's openings list keep the same truth?** Yes. The sheet uses the same `AREAS`
  words as the drawn names: count, sources answered, date, and "none found in the 4 sources
  checked" when empty. "Not job offers" and the synthetic label sit where they did (the card,
  and the phone's top bar). The sand colour of kept openings is lost on a phone, but the words
  say "2 days ago" and the stale alert stays. No phone capture shows the stale or unknown list
  (new Minor 4).
- **The two rewritten label tests:**
  - "Never lets two names overlap" dropped its five-lights-at-one-point case, which the new
    rule makes impossible by design (each name stepping out above would draw its line through
    the names below). The new four lights still cover sliding (`slides` at 784), stepping out a
    row with a clear line (`steps`, its line between `first` and `slides`) and taking the other
    side (`beside`). I derived each exact spot from the rules; none is true by construction.
  - "Never covers another light's centre, or the key" is now stronger: it asserts both names are
    placed, where before `a && overlaps(a, key)` passed vacuously if `a` was hidden. Its old
    scenario lives on as the new "boxed in" test, with the new outcome (hidden, not drawn
    across).
- **Checks not run against the old code first:** calm mode fails only with both fixes undone;
  menus-over-key fails with the portal undone; the phone status fails either way it is undone.
  All three can fail (reasoning in the table).

## Strengths

- The line check reads the line as drawn from the page and the lights from the drawing, so it
  tests the placer rather than restating it, and it found 77 real crossings.
- The key checks found a real gap in the app (You at 1440), and the fix is the honest one.
- The still world now reads its strengths from the same constant the moving world and the
  tokens use, with a test that pins it.
- One status at any width, one live region at a time.
- The report names what went beyond the dispatch and marks the product owner's view as not run.

## Issues

### Critical

None.

### Important

None.

### Minor

1. **Route names drop out under the stricter rule, the selected one included, and the report
   doesn't say so.** `checks.md` shows Routes names falling 8→7 (1440), 7→4 (768) and 4→3
   (390). In `routes--default--768x1024.png` only "Route D" is named, sitting on the teal
   trail of route B, whose ringed name is gone; at 390 only "Route A" remains; at 1440 Route C
   is unnamed. Route names are not lights, so no check counts them, and all routes share one
   priority (`world.js` `PRIORITY.route = 3`). A lone unringed name on the selected trail is the
   wrong-trail risk Minor 1 set out to remove. Fix: place the selected route's name before the
   other routes (the priority of a gate or the next step), and record the drop.
2. **ADR 0014 decision 7 still says "the strip says 'Still while support is shown'"**
   (`docs/adr/0014-the-living-world.md:79-80`); on a phone it is now the top bar. The README
   was updated (`README.md:191`, `:218`). Fix: add "(on a phone, the top bar)".
3. **The app's key check uses a different rule from the code.** `world.spec.ts` requires the key
   whenever any name is in view, "You" included; `World.tsx` shows it when a destination's
   light or a grey trail is in view. It holds for P01, which has a target, but a workspace with
   no target names "You" and renders no key, so the check would fail falsely there; and the
   other half ("no key with nothing it explains in view") has no app check. Fix: test against
   destination names (or a data attribute the world sets), and add the empty-key case.
4. **The phone's openings list is one run-on sentence, and its stale and unknown states are
   never captured.** "Openings for data quality analyst: Manchester: 8 openings, 4 sources,
   today; Leeds: …" (`roles--default--390x844.png`). One area per line would read faster, as
   CLAUDE.md asks. The stale ("3 sources, today" beside "2 days ago") and unknown lists exist
   only in code. Fix: render a short list; add `roles--stale` and `roles--unknown` at 390.
5. **Placing names can now cost far more per frame, unmeasured.** In the moving world
   `placeLabels` runs every frame while the view travels. When any name has no spot it now runs
   a full placement up to seven times for each key spot (two sides times every cover edge), so
   tens of placements per frame. App scenes are small, so this is likely fine, but frames were
   not re-measured (by ruling). Fix: include a scene with an unplaceable name (three long
   targets at 390) in Task W2's frame measurement.

## Assessment

**Task quality:** Approved

**Reasoning:** Every item in the dispatch is fixed with a check that can fail, both rulings are
met, and the product owner's approved scenes are unchanged in substance. The new issues are
small: the most visible is that the selected route can lose its name on narrower screens.

Counts: not fixed 0; partly fixed 0; regressed 0. New issues: Critical 0, Important 0, Minor 5.
