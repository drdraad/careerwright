# Task W2, slice W2A dispatch: the world layer and its design references

Where this fits: Careerwright L0 is mid-build (branch `l0-local-release`). The product owner
rejected the first interface as bland (plan v1.4 section 4, ADR 0014). A throwaway spike
(`spikes/world`) let them choose a direction at session W1: **Horizon, made livelier**. Task
W2 builds that world into the real app in four slices; you own the first, W2A: the world
layer under every chapter, and its design references. Later slices add the deterministic
sources (W2B), the You chapter and the first moments (W2C), and acceptance (W2D).

## Read first, in this order
1. Your brief (requirements, Global Constraints, standing rulings; exact values verbatim):
   `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-W2-brief.md`
2. The slice plan: what W2A owns, session W1's outcome, and the rulings that bind every slice:
   `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-W2-slices.md`
3. Your contract: `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`
4. `docs/plan/development-plan.md` section 4 in full and the "Sprint W Build the world" card;
   `docs/adr/0014-the-living-world.md`; CLAUDE.md ("The experience", "Talking to the user",
   the web layout and invariants).
5. The session W1 record `docs/reviews/session-w1-answers.md`; the spike's README
   `spikes/world/README.md` (measurements, library and typeface comparison) and its Horizon
   direction (`spikes/world/src/directions/horizon.ts`, `src/gl.ts`, `src/still.ts`,
   `src/sound.ts`); the reference image `docs/design/reference/luminous-path-forward.png`.
6. The current web app (`apps/web`, `WorkspaceShell.tsx`) and design system (`docs/design`).

## The bar
In the product owner's words: "revolutionary, not the current bland corporate borefest";
"verge on computer game rather than typical tool"; "organic and cybernetic"; "thrum with power
and possibility"; "leave users astonished and breathless". On the spike: Horizon was "the most
logical, but not quite right yet. The animations aren't as good as the others, and its a bit
too [noisy] with the dashed lines." Make Horizon as alive as Growth and Circuit were, without
their chaos: calm, ordered, and thrumming. Sound: "subtle and evocative, not cheesy!" You may
load the `frontend-design:frontend-design` skill. A bland, form-like or corporate screen
fails review even if it works.

## Decisions the brief cannot know (the controller's)
- W2A's scope is the slice plan's W2A paragraph. Do not build W2B's backend, W2C's You
  chapter rebuild or W2D's register and package. Today's chapters keep working: they render
  in the DOM layer over the world, and a chapter not built yet shows its place with an honest
  "not built yet" state. Retire the old shell's look; keep its session, queries and events
  wiring (`WorkspaceShell.tsx` owns them).
- three.js: pin the exact version the spike recommends (0.186.1) if it is at least 14 days
  old on the day you install (pnpm enforces it), record it in `docs/dependencies.md` and ADR
  0014. Outfit: self-hosted from a licensed source, recorded the same way.
- The design references live in `docs/design`, with `apps/web/src/design` mirroring only what
  it mirrors today (fonts, tokens); never edit the mirror by hand if a tool writes it. Every
  new colour pairing goes into `contrast-pairs.json` and is measured. One colour, one meaning
  (orange destinations; sea-glass teal selection, the chosen path and the primary action;
  blue and violet atmosphere; industry by glyph and label).
- Frame instrumentation: per-frame cost (main-thread work + GPU time) against section 4's
  budgets, reported with device, browser and renderer; the rAF interval reported too.
- Never claim a human-only gate (design scores, Safari, VoiceOver, M1): "not run — requires
  human" (R2).

## Hard rules
- Change source files with Edit and Write only: never `sed`, `awk`, heredocs or scripts that
  rewrite files (generated outputs from the project's own tools are fine).
- Stage explicit paths only; never `git add -A` or `git add .`. Never stage or commit
  `answers-2.md`. Never push.
- Never read `.env` or anything under `~/.nessa` or `~/.careerwright`. No live model calls.
- Leave `spikes/world` unchanged. Do not dispatch subagents.
- `make check` and `make acceptance` pass before your final commit.

## Report
Write your full report to
`/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-W2A-report.md`
(include the frame table, the contrast results, what each chapter shows now, every ruling you
made, and the paths a reviewer should skip). Then reply with only the short contract.
