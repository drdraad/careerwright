# Task W1 dispatch: the spike of three directions

Where this fits: Careerwright L0 is mid-build (branch `l0-local-release`). The product owner
rejected the first interface as bland and set a new direction, now plan v1.4 section 4 ("a
world that answers you", ADR 0014). This spike is the first step: three throwaway, playable
directions they will try for an hour at session W1 and choose between. Nothing else in the
interface is built until they choose, so this spike is what they will judge the whole
redesign by.

## Read first, in this order
1. Your brief (your requirements, with the exact values to use verbatim):
   `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-W1-brief.md`
2. Your contract (how to work and report):
   `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`
3. `docs/plan/development-plan.md` section 4 in full, `docs/adr/0014-the-living-world.md`,
   the "Sprint W Build the world" card, and CLAUDE.md's "The experience" and "Talking to the
   user" sections.
4. The reference image: `docs/design/reference/luminous-path-forward.png` (open it).

## The bar
The product owner's words: "revolutionary, not the current bland corporate borefest";
"verge on computer game rather than typical tool"; "organic and cybernetic"; "thrum with
power and possibility"; "leave users astonished and breathless". They said they would fire
whoever put the first prototype in front of them. A tasteful, tidy, form-like spike fails
even if it meets every number. Make three directions that genuinely differ from each other,
each one something they could fall for. You may load the `frontend-design:frontend-design`
skill for aesthetic guidance.

## Decisions the brief cannot know (the controller's rulings)
- Location and command: your call, outside `apps/web/src`, `docs/design` and `backend`, so
  no product check lints or tests it. One command starts it; a `make` target (for example
  `make spike-world`) is the easiest for the product owner, who already runs `make demo`.
  Label it a spike in its README and on screen.
- Dependencies: its own pnpm package with its own `pnpm-workspace.yaml` carrying
  `minimumReleaseAge: 20160` (copy the rule from `apps/web/pnpm-workspace.yaml`), pnpm
  10.33.2, Node 24. Exact pins. List each with its version and publish date in the spike's
  README. `docs/dependencies.md` gets only the library W2 adopts, not spike dependencies.
  Installing from the npm registry is allowed; at runtime the spike makes no external
  request (check it with a request log: only its own 127.0.0.1 origin).
- Fonts: licensed (OFL or similar) and self-hosted, for example Fontsource packages or files
  committed with their licence. No font CDN at runtime.
- Frame measurement: measure in a headed browser with GPU acceleration on this Mac (system
  Google Chrome if installed, else Playwright's Chromium headed). Record the WebGL renderer
  string (`WEBGL_debug_renderer_info`) with each result. A software-rendered (SwiftShader or
  similar) or headless-without-GPU number is not this Mac's number: if you can only get
  that, report it as such and say the real measurement is not run. Warm up, then sample
  `requestAnimationFrame` deltas for at least 10 s in the busiest scene; report p50, p95, the
  frame count and the first-frame time (navigation start to the first drawn world frame).
  Report the device (`sysctl -n machdep.cpu.brand_string`, memory) and browser version.
- Synthetic data only, labelled on screen in plain words. The first question is "What do you
  do now, or what did you do last?" with type-ahead over a small labelled list (the labelled
  `fixtures/esco-sample` is a fine source, or a short synthetic list). The revelation must
  obey section 4's truth rules even as an example: it comes from a stated, deterministic
  source, its reason is one step away, unknown is shadow, nothing implies a job offer, and
  "usual in your role, not confirmed yet" is visibly different from confirmed.
- Still version: reduced motion (the OS setting) and a calm-mode toggle each draw the same
  states and words without motion. A visible pause control stops ambient motion.
- Session W1 package: `docs/reviews/session-w1.md`, in CLAUDE.md's "Talking to the user"
  style (plain words, short lines, no internal codes, action first, a time estimate). How
  to start it, how to open each direction, what to try in two minutes each, and the
  questions: which direction or which mix, in their own words; whether sound is wanted.
  Screenshots of each direction beside it are welcome. You give no design scores (R2): only
  the product owner scores.
- Run `make check` once before your final commit to show the product is untouched.

## Hard rules
- Change source files with Edit and Write only: never `sed`, `awk`, heredocs or scripts
  that rewrite files.
- Stage explicit paths only; never `git add -A` or `git add .`. Never stage or commit
  `answers-2.md` (the product owner's own file). Never push.
- Never read `.env` or anything under `~/.nessa` or `~/.careerwright`. No live model calls.
- Do not dispatch subagents.

## Report
Write your full report to
`/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-W1-report.md`
(the contract lists what goes in it: include the frame table, the library and typeface
comparison with your recommendation, and every ruling you made). Then reply with only the
short contract (status, commits, one-line test summary, concerns, report path).
