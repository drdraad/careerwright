# Task W2A review dispatch (two reviewers, split by path)

You review one half of Task W2, slice W2A (Careerwright L0, branch `l0-local-release`,
commits c1bc2f3..65aed2f). Another reviewer takes the other half at the same time; stay in
yours, but read across the line where a finding needs it.

## Read first
1. Your contract: `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`
2. The brief (requirements, exact values): `.superpowers/sdd/l0-sprint-tasks/task-W2-brief.md`
3. The slice plan (what W2A owns, the rulings binding every slice): `.superpowers/sdd/l0-sprint-tasks/task-W2-slices.md`
4. The dispatch the implementer worked from: `.superpowers/sdd/l0-sprint-tasks/task-W2A-dispatch.md`
5. The implementer's report (its rulings 1–12 need your verdict too): `.superpowers/sdd/l0-sprint-tasks/task-W2A-report.md`
6. Your half's package (named in your prompt). Images, fonts and lockfiles are excluded;
   open any PNG in `docs/design/screenshots/` with the Read tool to judge it.
7. CLAUDE.md ("The experience", invariants, web layout), `docs/adr/0014-the-living-world.md`,
   `docs/plan/development-plan.md` section 4.

## New since the dispatch: the product owner's reaction
While W2A was finishing, a headed Chrome window opened on the product owner's screen running
the frame measurement's synthetic "Busiest scene" (100 openings, 12 skills, 5 destinations,
travel every 3 s, ignition every 4 s). Their words, verbatim: "Wow, the scene looked too busy.
was overwhelming". That scene is a stress test, not what a person sees, but the controller has
ruled that "never overwhelming" binds every W2 slice: one idea at a time, and the busiest
*real* scene must read calm. Judge the real screens against it: how many labels, lights,
moving things and controls compete at once; whether anything moves without meaning; whether
the strip, rail, legend and panel together crowd the world. Name concrete reductions, each
with what it keeps (truth, states, words must survive in the still world).

## Binding constraints to check
- One colour, one meaning: orange is destinations only; sea-glass teal is selection, the
  chosen path and the one primary action only; blue and violet are atmosphere; industry by
  glyph and label. Every new colour pairing is in `contrast-pairs.json` and measured,
  including panels and labels over the brightest light.
- Truth: the world never shows more than the evidence. Unknown is shadow, never zero; nothing
  implies a job offer; "usual in your role, not confirmed yet" is display-only; position is
  layout only; Horizon depth means nothing (destinations at one depth, a revelation singled
  out by light, never distance). Synthetic or fixture content is labelled and never appears
  in a live workspace.
- Still world: reduced motion, calm mode and pause draw the same states and words. A visible
  pause control (WCAG 2.2.2). Sound off by default, a visible control, nothing plays on arrival.
- Frame budget ruling: per-frame cost (main-thread work + GPU time) against 8 ms (M4) and
  16.7 ms (M1); the rAF interval reported beside it, with device, browser and renderer.
- Human-only gates (design scores, the moving world's feel, sound, Safari, VoiceOver, M1)
  are "not run — requires human", never claimed (R2).
- Dependencies: exact pins, at least 14 days old, recorded in `docs/dependencies.md`; no test
  or architecture check weakened to admit them.

## Hard rules for you
- Read-only on the repository: no edits, no commits, no `git add`.
- **No headed browser, ever.** Do not run `scripts/measure-world.mjs`, `make spike-world`,
  `open`, or anything that puts a window on the product owner's screen. Headless test runs
  are fine if you need one (`make check` is fine; skip `make acceptance`, the controller has
  the implementer's run).
- Never read `.env`, `~/.nessa` or `~/.careerwright`. No live model or web calls. No subagents.

## Output
Write your full review to the file named in your prompt: spec compliance verdict, quality
verdict, findings ranked Critical / Important / Minor, each with `file:line`, the failure it
causes, and a concrete fix; then your verdict on each implementer ruling in your half. Reply
with only: both verdicts, the count per severity, and the review file path.
