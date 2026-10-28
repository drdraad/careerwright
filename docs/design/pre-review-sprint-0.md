# Sprint 0 compositions: agent pre-review and human review checklist

## Agent pre-review — not the required human review

Reviewed by Codex from all 18 committed screenshots, the composition HTML/CSS/JavaScript,
five additional desktop section captures and targeted Chromium layout checks. The
implementing agent's earlier critique and correction history are retained below. Under
[ruling R2](../plan/l0-sprint-tasks.md), this is an **agent pre-review — not the required
human review**; no numeric design score or human approval is assigned.

**Assessment:** the three compositions share a coherent visual language, and the desktop
financial trace is clear. The phone conversation is not a usable reference for its full
task yet: its profile-review entry point is hidden, and its reply field remains covered
by the sheet. Fix S0-V01 and S0-V02 before reusing that layout. Conditional readiness,
stale selection and the unknown-data views also need the corrections below.

**Checks run for this review:**

- `pnpm --dir docs/design run check-data`: 64 fixture assertions pass.
- The existing screenshot checker, with only its input/output paths redirected to a
  temporary folder: 18 of 18 captures pass font loading, horizontal overflow, axe,
  console-error and SVG-label collision checks. All 18 PNGs and `checks.md` match the
  committed files byte for byte. The checked viewports are 1440×900 and 390×844.
- The existing contrast checker, with its report redirected to the temporary folder:
  68 of 68 pairs pass; the report matches `tokens/contrast-report.md` byte for byte.
- Independent January ledger spot check: £6,000 opening cash − £150 course payment −
  £1,000 living costs = £4,850 before pay, then £2,000 pay gives £6,850 closing cash,
  matching the displayed row. This is a check of the synthetic example, not a financial
  model qualification.
- Targeted Chromium probes reproduce hidden profile-review controls, reply-field
  occlusion after attempting to scroll, and the absent expansion control in unknown
  Routes. These are findings despite the baseline checks passing, not accessibility or
  usability passes. Additional captures of the review tray, pay lens, listing table,
  Gantt and ledger were inspected; generated artifacts remain outside the repository.

The checks use the installed Playwright 1.64.1 Chromium on macOS arm64 with reduced motion.
They do not establish keyboard usability, VoiceOver or Safari behaviour.

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

### Screenshot coverage

Each linked image was inspected. Default views include a selected item; unknown and failure
are separate compositions, not evidence that transitions between them work.

| Composition and state | Desktop, 1440×900 | Phone, 390×844 |
|---|---|---|
| You: default | [Desktop](screenshots/conversation--default--1440x900.png) | [Phone](screenshots/conversation--default--390x844.png) |
| You: unknown | [Desktop](screenshots/conversation--unknown--1440x900.png) | [Phone](screenshots/conversation--unknown--390x844.png) |
| You: failure | [Desktop](screenshots/conversation--failure--1440x900.png) | [Phone](screenshots/conversation--failure--390x844.png) |
| Roles: default | [Desktop](screenshots/opportunity-map--default--1440x900.png) | [Phone](screenshots/opportunity-map--default--390x844.png) |
| Roles: unknown | [Desktop](screenshots/opportunity-map--unknown--1440x900.png) | [Phone](screenshots/opportunity-map--unknown--390x844.png) |
| Roles: failure | [Desktop](screenshots/opportunity-map--failure--1440x900.png) | [Phone](screenshots/opportunity-map--failure--390x844.png) |
| Routes: default | [Desktop](screenshots/route-comparison--default--1440x900.png) | [Phone](screenshots/route-comparison--default--390x844.png) |
| Routes: unknown | [Desktop](screenshots/route-comparison--unknown--1440x900.png) | [Phone](screenshots/route-comparison--unknown--390x844.png) |
| Routes: failure | [Desktop](screenshots/route-comparison--failure--1440x900.png) | [Phone](screenshots/route-comparison--failure--390x844.png) |

### Open findings

S0-V01 and S0-V02 block reuse of the phone conversation layout. S0-V03–S0-V07 concern
clarity or access to the main task; S0-V08 is hierarchy polish. These findings concern the
design references, not a qualification of the current application. No composition code
was changed in this review.

1. **S0-V01 — Phone You hides both profile-review views (all states).** The desktop
   proposal tray disappears on the phone, but its intended "What we know" summary and
   Open button disappear too. Chromium reports `display: none` and zero geometry for
   both `.known` and `.known-summary` at 390×844 in default, unknown and failure. In
   [conversation.css](compositions/conversation.css), the final `.known-summary` rule
   overrides the earlier mobile `display: flex` rule. Make the mobile summary visible
   and specify its review destination. Recheck that the phone can reach pending changes,
   confirmed answers and manual entry without relying on the selected evidence drawer.
2. **S0-V02 — The phone sheet covers replying and failure recovery.** In every You state,
   the reply field occupies y=775–819 while the fixed sheet starts at y=632. A centre-point
   hit test reaches the sheet, not the composer; scrolling to the end leaves it covered
   because the work area has no scroll range (737 px content in a 737 px area). The phone
   `.you` padding shorthand also overrides the shared sheet-clearance padding to 0 px.
   In [failure](screenshots/conversation--failure--390x844.png), the main Try again button
   at y=633–673 is covered as well. Reserve space for the open sheet in both the content
   and sticky composer, or dismiss/collapse the sheet when replying. Verify the reply
   field, Send, Try again and manual-entry action by hit testing and keyboard use;
   scrolling alone does not resolve this layout.
3. **S0-V03 — Individual route cards lose the readiness condition.** TRACE-01 cards in
   [default](screenshots/route-comparison--default--1440x900.png) and failure say "Ready
   in … months", while the assessed-report condition sits above the whole group. It can
   scroll away independently of a card. Keep Conditional beside each card's readiness
   and make the requirement available with it. The selected journey already does this
   well. This presentation risk also appears in Sprint 1's V-01; correct the reference
   before carrying it into computed routes.
4. **S0-V04 — The stale route journey looks current in the phone peek.** The
   [failure sheet](screenshots/route-comparison--failure--390x844.png) repeats default
   route B's 4 months and £600 figures without a stale/version marker of its own. The
   main page correctly says version 14 predates the weekly-hours edit, while the strip
   says version 15. Once the page is scrolled, the fixed sheet can outlive that warning.
   Carry "Previous comparison, version 14" and its stale status into the selected
   journey, including the peek; do not imply that its readiness is checked against the
   newer profile.
5. **S0-V05 — The unknown Roles heading asserts a match it cannot support.** The
   [desktop unknown card](screenshots/opportunity-map--unknown--1440x900.png) is headed
   "Matches your preferences", immediately followed by "there's too little to compare".
   Change the heading to state that preference fit is not assessed; preserve the
   snippet-only explanation and full-listing action. The default card's distinction
   between preference fit and unchecked skills is useful and should remain.
6. **S0-V06 — Unknown Routes drops known figures and the expansion affordance.** The
   [phone unknown sheet](screenshots/route-comparison--unknown--390x844.png) says only
   "Route B, selected" and "Schedule not available" with a long explanation. It omits
   the known 9 months and £2,400 direct spending, and has no visible More control; the
   source places that control inside the default/failure-only header. Keep the known
   objective values in the selected summary, state which schedule details are missing,
   and retain a consistent expansion affordance. Unknown dates and cash flow should not
   erase the comparison values that do exist.
7. **S0-V07 — Failure and unknown copy push phone lists behind the sheet.** With the peek
   starting at y=632, the first listing in
   [Roles failure](screenshots/opportunity-map--failure--390x844.png) starts at y=649.
   The first route starts at y=673 in unknown Routes and y=818 in failure Routes. These
   initial views therefore show no comparison/list card outside the selected sheet.
   Default Roles and Routes do show a first card. Keep failure, freshness and cost-basis
   labels, but shorten their initial summaries and disclose secondary explanation so
   the retained list remains discoverable. Recapture all three affected states.
8. **S0-V08 — More than one filled action competes for attention.** Desktop default You
   shows filled Send and Accept buttons. Roles failure offers both a filled global
   "Try the search again" and a filled selected-listing "Check again". This contradicts
   the reference's stated one-primary-action convention. Choose the primary action for
   the active task and use secondary styling for the other; the action labels and
   distinct recovery scopes should remain clear.

### Rubric observations

| Category | Strengths observed | Remaining defects or evidence gaps |
|---|---|---|
| Hierarchy | A clear current question, page title or selected route; quiet workspace strip. Default phone Roles and Routes expose a first card | Unknown/failure stacks hide the first card (S0-V07). Default You and failed Roles compete with two filled actions (S0-V08) |
| Typography | Newsreader and Source Sans 3 retain a calm editorial voice. Long role/employer names wrap; the desktop ledger's tabular figures align | The small SVG labels need narrow-desktop and zoom review. The dense desktop proposal tray and long phone explanations need human reading checks |
| Spacing | Consistent card gutters, readable desktop tables and a compact route summary | The phone composer and failure recovery are physically covered (S0-V02). A fixed 212 px sheet does not by itself guarantee usable remaining space |
| Visual identity | Ink exploration surfaces, light reading panels, open-circle anchors, branches and sea-glass selection are consistent. Industry is named as well as coloured | Colour-vision differentiation and display variation are untested; contrast passing does not establish either |
| Chart legibility | Desktop route points are discrete; D and B's equal-time tie is explained, and grey layers differ by disc/ring and labels. The inspected Gantt separates work, study, payment and assessment; the ledger explains the pre-pay low point | No phone focused chart or map overview, tablet, negative economic cost, scenario ranges or dense archive is composed. The lens has a table equivalent, but its selection/keyboard behaviour is not demonstrated |
| Uncertainty communication | "Not confirmed, not £0", pay-not-stated and reduced source coverage are explicit. The early sketch has both a provisional title and a research disclaimer. Experimental AI scores carry a synthetic provenance line | Card readiness (S0-V03), selected-route freshness (S0-V04), the unsupported preference heading (S0-V05) and the missing known figures in unknown Routes (S0-V06) need correction |
| Responsive composition | Phone layouts use cards/lists and bottom sheets rather than shrinking desktop charts. Long labels wrap without horizontal page overflow | Phone profile review is hidden (S0-V01), replying is covered (S0-V02), the unknown sheet lacks More (S0-V06), and failure/unknown lists are buried (S0-V07) |
| Interaction continuity | Selection has a consistent edge/ring; failure preserves previous data, and cost-mode labels distinguish direct spending from economic cost | Phone review and input access fail (S0-V01/S0-V02). Stale context must follow the selection (S0-V04). These are static references: navigation, filtering, expansion, focus return and transitions are not implemented journeys |

### Coverage limits

The 18 committed images show only the viewport. The additional section captures extend
the default desktop inspection to the proposal tray, pay lens/table and route Gantt/ledger;
they do not cover every lower section in unknown and failure states. Phone expanded
sheets, focused charts, map overview and filter editing remain uncomposed; no tablet,
200 % zoom, keyboard journey, VoiceOver or Safari check was run. Area-level "none found"
is shown for Leeds; a wholly empty search, incremental partial results, dense 100-job
views, negative economic cost and evaluated scenario ranges are not demonstrated. Static
button styling and a passing axe run do not establish working interactions.

## Human review checklist (not run — requires human)

Scoring and approval are **not run — requires human** (plan section 5; H-02; R2). The
agent's evidence is complete within the scope above. The product owner and design
reviewer should record 1–5 scores against the screenshots and live pages
(`compositions/index.html`); every category must reach at least 4 before final local
release. A pending score does not establish a pass.

| Category | Score (1–5) | Defects |
|---|---|---|
| Hierarchy | Not run — requires human | S0-V07, S0-V08: list discoverability and competing primary actions |
| Typography | Not run — requires human | Small SVG labels, dense review tray, long phone copy and zoom legibility |
| Spacing | Not run — requires human | S0-V02: sheet clearance and usable space for replying/recovery |
| Visual identity | Not run — requires human | Coherent surfaces and selection; colour-vision and display checks remain |
| Chart legibility | Not run — requires human | Desktop chart/Gantt/ledger inspected; focused phone views, tablet and dense/negative/scenario cases absent |
| Uncertainty communication | Not run — requires human | S0-V03–S0-V06: conditional readiness, stale selection, unsupported match and known figures |
| Responsive composition | Not run — requires human | S0-V01, S0-V02, S0-V06, S0-V07: review entry, covered controls, unknown sheet and buried lists |
| Interaction continuity | Not run — requires human | S0-V01, S0-V02, S0-V04; live keyboard, selection, expansion and focus-return checks remain |

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
- [ ] At 390×844, reach What we know and edit/confirm a proposal, then reply with the
      sheet open; reach both failure-recovery actions (S0-V01/S0-V02).
- [ ] Scroll the failed route comparison and confirm the selected journey retains its
      old version and stale status (S0-V04).
- [ ] In unknown Routes, identify B's known time/cost and a consistent way to expand its
      details (S0-V06); distinguish this from an absent schedule.
- [ ] Approve, or list the corrections required before reusing these references in the
      remaining map/route implementation (Tasks 8 and 14).

Approval: **not given — requires human (H-02)**. Approver and approval date: not recorded.
