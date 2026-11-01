# Task W2A fix round 2 of 5

You fix what remains of Task W2, slice W2A (Careerwright L0, branch `l0-local-release`, HEAD
7ac80dc). Fix round 1 landed in 8b0cdf9 and 7ac80dc; its scoped re-review approved everything
except the items below. This round is small: stay inside it.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`
2. `task-W2A-rereview-1.md` in full: the findings you fix (its Important 1, the partly fixed
   A-M1/A-M10, and its Minors 1–9)
3. `task-W2A-fix-round-1.md` (the rulings that still bind, especially trail contrast and calm
   mode) and the "Fix round 1" section of `task-W2A-report.md`
4. For background only, as needed: `task-W2A-review-design.md`, `task-W2A-review-app.md`,
   CLAUDE.md ("The experience", invariants), ADR 0014

## Controller rulings
- **Re-review Minor 5, the distress dim:** accepted as a recorded exception. While the calm
  support panel shows, the world is a dimmed, still backdrop; its trails may fall below 3:1
  then, because every name and state stays in the DOM list and the person is not reading the
  world. Record the exception everywhere the "3:1 as drawn" claim is made (design README, ADR
  0014, the contrast pairs or report). Nothing else is exempt.
- **Re-review Minor 9:** record both `world.js` changes in the report; give unselected routes
  their own drawn state instead of borrowing "said" (one state, one meaning).

## Fix now
1. **Important (D-I3's unfixed part):** `apps/web/src/components/StillWorld.tsx` draws its trails
   from `TRAIL_OPACITY` (delete its own table). Add a test that renders `StillWorld` and asserts
   each trail's `stroke-opacity` equals its `TRAIL_OPACITY` value, and confirm it fails against
   the old values. Make the records (`docs/design/README.md`, ADR 0014, `palette.ts`, the report)
   true afterwards.
2. **A-M1 / A-M10 on phones:** Calm mode in the account menu shows its words and its switch at
   390 px (the strip's phone rules must not hide the menu's text). Add a check at 390 px.
3. Re-review Minors 1–4 and 6–8, each as the re-review's "Fix" says, with a check where it asks
   for one (leader lines that meet another light or name are rejected and checked in
   `screenshots.mjs`; the key fails a check when lights are in view and it is unplaced; the key
   sits under the menus).

## Then
- Regenerate the references with the project's tools; mirror byte-identical; `pnpm run
  contrast`; `check-data`.
- `make check`, then `make acceptance` once before the final commit (headless only).
- **No headed browser, no `open`, nothing that puts a window on the product owner's screen.**
  Do not run `scripts/measure-world.mjs`.
- Hard rules: Edit/Write only for source changes (no scripts that rewrite files, not even for
  string replacements); stage explicit paths; never `answers-2.md`; never `.env`, `~/.nessa`,
  `~/.careerwright`; no web or model calls of any kind; leave `spikes/world` unchanged; no
  subagents; never push.
- Append a "Fix round 2" section to `task-W2A-report.md` (each item: what changed, the check
  that proves it). Reply with only the short contract.
