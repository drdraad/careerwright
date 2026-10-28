# Sprint 0 compositions: agent pre-review and human review checklist

## Agent pre-review — not the required human review

Written by the implementing agent (Task 2), 2026-10-27, from the 18 screenshots in
`screenshots/` and full-page renders. Ruling R2: this is not a design-review score, and no
score is given. The categories follow the plan's rubric (section 5) so that the human
review can use the same frame. The automated checks behind it are in
`screenshots/checks.md` (18 of 18 captures pass) and `tokens/contrast-report.md` (64 of 64
pairs pass).

**Fix round 1 (2026-10-28), from the independent review:**

- A dominated route on the comparison line contradicted the key. The key was rewritten,
  dominated marks got a halo, and a generated equal-time-tie note was added.
- Layers 2 and 3 were indistinguishable. They are now a disc and a ring, with layer labels.
- The phone sheets hid the main task. They now open at a peek height.
- AI Resilience displays lacked the Experimental marker.
- Dashes carried six meanings; now there are two.
- The failure state had two filled "Try again" buttons.
- Slider bounds and some prose numbers were hard-coded; they now come from the data.

**Defects found and fixed while iterating (first pass).** These are recorded because each was found by
looking at a render, not by a passing check:

- State switching failed twice:
  - Component `display` rules overrode `[hidden]`, so all three states rendered at once.
  - `element.hidden` does nothing on SVG elements, which left an empty Gantt in the unknown
    state.
- Map labels collided with job nodes, with each other and with the canvas edge. That led
  to a label-collision check in `screenshots.mjs` and to area names moving inside their
  anchors.
- The route chart was small and its labels were struck through by the boundary line.
- A grid area name reused by a nested element widened the page by 23 px.
- A chart-wide `svg { width: 100% }` rule inflated the 16 px status glyphs.
- The light-surface control border measured 2.95:1.
- Lens bars dimmed to 60% fell to 2.97:1 for the "Other" hue.
- Several copy faults:
  - "on the right" was wrong on a phone.
  - One action had two names.
  - A review count was wrong.
  - A route margin read clumsily.
  - The unknown-state question ran under the mobile sheet.
- The route comparison exposed an error in the fixture hand check: incomplete dominator
  lists for DIRECTAI G and H. It is corrected in `docs/evidence/fixture-hand-check.md`.

| Category | Strengths the agent sees | Remaining weaknesses the agent sees |
|---|---|---|
| Hierarchy | One display-serif hero per page: the current question, the page title, the selected route. One filled action per view. The workspace strip stays quiet | The map's default view has three strong regions (filters, canvas, card) of similar weight. The card could recede until a node is selected |
| Typography | Newsreader at light weight beside Source Sans 3 gives a calm editorial voice. Tabular figures line up in the ledger. Line lengths stay under about 66 characters | The 13 px SVG labels are near the lower comfortable limit at 1440 px. They scale down further on narrower desktops because the SVGs scale with their containers |
| Spacing | Consistent 4/8/12/16/24/32 rhythm. Radius follows hierarchy | The conversation's review tray is dense at 1440×900. The Roles filter bar is one line at 1366 px but wraps to two at 1300 px (measured) |
| Visual identity | The open-circle anchors, fine branches and route staircase make one recognisable motif across pages without decoration | The map's background glow is faint enough that the ink can look flat on low-quality displays. It is not tested on other screens |
| Chart legibility | Discrete points; a staircase labelled "comparison boundary"; the bettered region shaded and explained; front 1 values on the chart; layers 2 and 3 as a grey disc and a grey ring, each labelled with its layer, their figures on cards; a halo lifting a dominated point off the line, with a note for the equal-time tie (D and B); greedy label placement with no collisions | No scenario whiskers are shown, because no scenario data exists in the fixtures. The unknown-scenario line is the only treatment. A cluttered real archive (hundreds of points) is not composed |
| Uncertainty communication | "Not confirmed, not £0"; a dashed inference with "not a fact until you accept it"; snippet-only and pay-not-stated stated plainly; failed, stale and conditional drawn differently; synthetic labels everywhere | The conversation's early sketch is a text card. It may read as more settled than it is. Spec section 3 wants it visibly provisional, and a human should judge whether the dashed edge is enough |
| Responsive composition | Phones lead with the question, the list or the cards. The evidence becomes a bottom sheet. No horizontal overflow at 390 px | The phone's focused chart view and map overview are not composed (entry points only). The sheet opens at a 212 px peek with a "More" control; the expanded height and swipe behaviour are not designed |
| Interaction continuity | Selection is shown the same way everywhere: a sea-glass edge on cards and rows, a ring on marks. Selected marks use `aria-pressed`. Filters state that they never change ranks | Static references: no hover, focus-return, keyboard path or transitions are demonstrated. axe passing does not establish keyboard usability |

## Human review checklist (not run — requires human)

To be completed by the product owner and a design reviewer (plan section 5; register
H-02). Record a 1–5 score per category with concrete defects, against the screenshots and
the live pages (`compositions/index.html`), in `docs/reviews/sprint-0.md` or a follow-up
review note.

| Category | Score (1–5) | Defects |
|---|---|---|
| Hierarchy | | |
| Typography | | |
| Spacing | | |
| Visual identity | | |
| Chart legibility | | |
| Uncertainty communication | | |
| Responsive composition | | |
| Interaction continuity | | |

Questions the reviewers should answer explicitly:

- [ ] Can a reader say, from the route view alone, which cost is plotted, over what
      horizon and baseline, and whether the search was complete? (Sprint 7 coherence
      question.)
- [ ] Do failed, stale, unknown and conditional states look distinct at a glance, on
      desktop and phone?
- [ ] Does anything look more certain than the data allows: the early sketch, the
      "Matches your preferences" list, the AI Resilience badge?
- [ ] Is the synthetic-data label noticeable without being alarming?
- [ ] Are the long labels (employer names, course names) still readable at 390 px?
- [ ] Is the industry palette distinguishable for common colour-vision deficiencies? Only
      contrast was measured, not colour-vision deficiency, and every industry is also
      named in text.
- [ ] Approve, or list the changes required before Task 4 implements the shell.
