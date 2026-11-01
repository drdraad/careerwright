# Task W1 fix round 2 of 5

Re-review: `.superpowers/sdd/l0-sprint-tasks/task-W1-rereview-1.md` (read it in full). Eleven
of twelve items are addressed. Fix these:

## Open from round 1
1. (item 5) Horizon: a label must never sit away from its own light. In
   `2-horizon-b-revelation.png`, "Warehouse supervisor" sits about 20 px from Shop supervisor's
   light and about 180 px from its own, with no leader (leaders are drawn only at reach > 1,
   `app.ts:526`). Every label must read as belonging to its light in every look, at 1440×900
   and the other viewports you screenshot.

## New Important (from the re-review)
2. Horizon hides one of the person's skills after the revelation: the wider arc plus the
   revealed view pushes the leftmost skill off-screen at 1440×900, so it cannot be seen,
   picked or reached by keyboard (all five roles tried). Every skill and destination must stay
   on screen and reachable in every look and state. Add a check to `tools/check.mjs` that
   every skill and destination is inside the viewport, visible and focusable in each state
   (it compares text and opacity today, not visibility), and confirm it fails on the current
   build first.
3. Pointing at an orange light does nothing; only its name responds, but the package says
   "Point at a few of the orange lights". Make the lights themselves respond to pointing (the
   natural action in a world), keeping the names working, and keep the package's words true.

## Upgraded by the controller (Important)
4. The chooser's flowing animation runs forever with no pause control. Plan section 4 and
   WCAG 2.2.2 require a visible pause control for any ambient motion; add one to the chooser
   (reduced motion already stops it).

## Minor, fix now (cheap; honesty and accessibility)
5. A destination button's `aria-pressed` follows hover and focus; make it follow the
   click-to-pin state only.
6. The README's "24 repeat samples peaked at 8.4 ms" claim has no committed data: commit the
   data beside the other measurements, or remove the claim.
7. Re-run the measurements as the last step, after your final source edit, so
   `measurements.json` measures the committed build; say so in the report with the times.

## Then
Update the screenshots and `docs/reviews/session-w1.md` if anything visible changed. Re-run
`pnpm test`, `typecheck`, `tools/check.mjs` (with the new visibility check) and the
measurements; run `make check` once. Do not use `osascript` or anything that drives Chrome
through macOS automation. Same hard rules as the dispatch. Append a fix report to
`task-W1-report.md` and reply with the short contract.
