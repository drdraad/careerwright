# Task W1 fix round 1 of 5

Review: `.superpowers/sdd/l0-sprint-tasks/task-W1-review.md` (read it in full, including the
agent design pre-review). The controller has upgraded several of its Minor and design points:
this spike is what the product owner will judge the whole redesign by, and CLAUDE.md says "a
bland, form-like or corporate screen fails review even if it works". Fix everything below.

## Important (from the review)
1. Words vanish for about 2 s after leaving calm mode or reduced motion (label entry animation
   restarts with its birth delay). Words must stay readable through every toggle. Add the
   toggle-back case (calm on then off; reduced motion on then off) to `tools/check.mjs`.
2. Circuit's teal corner brackets on the console and the revelation card: remove. Teal is
   selection, the chosen path and the primary action only. Check all three looks for any other
   decorative teal.

## Upgraded by the controller (Important)
3. **One idea at a time after the first answer** (plan section 4, and the product owner's own
   session 2 complaints: "minimum ideas per page", "Don't even know where to start"). The
   screen after the first answer shows eight captioned skills, five captioned destinations,
   a shadow label, a console, a 70-word card, a legend, footers and six pills at once. Stage
   it: what just changed is the one thing that speaks; the rest stays quiet until asked
   (hover, focus or a next step). "Usual in your role, not confirmed yet" must stay visibly
   distinct from confirmed and reachable in words (a glyph plus one legend line, with the full
   words on hover and focus, satisfies the truth rule). Keep the still version's words equal
   to the moving version's.
4. **The first screen and the chooser must already be the world.** Today all three open on the
   same centred headline and teal pill search box over a different backdrop, and the chooser
   is a tidy product page with flat icons. Put the question in the world, by the light, with
   the light answering each keystroke; make each direction distinct before the first
   keystroke; make the chooser itself feel like entering a world. The words and the
   interaction stay the same in all three (the brief's "same first ten seconds").
5. **Strengthen each direction against the bar** (the review's per-look notes):
   - Growth: trails must grow like something living, not tangle into a network graph;
     destination lights must read orange (warm cores, as in the reference image), not
     near-white.
   - Horizon: lose the ruled 80s grid plain for a ground closer to the reference image; labels
     must never crowd or detach from their light; the revealed destination must stand out
     after the revelation settles.
   - Circuit: it reads as a flowchart (two columns and mono captions). Make it a living
     circuit world (organic and cybernetic), still exact and readable.
6. **Horizon depth must mean nothing** (ADR 0014 decision 4: position is layout only; unknown
   is shadow). Depth alternates by title index and the revelation sits deeper, which reads as
   "further to go". Give destinations no varying depth, or a depth that varies by nothing the
   person could read as distance or difficulty; single out the revelation by light, not by
   distance.

## Minor, fix now (cheap)
7. The one command must open Chrome, not the default browser (which may be Safari); the
   package says Chrome up front.
8. One heading face for all three looks by default (your recommendation), so the comparison
   is of worlds, not lettering. Lettering stays its own question in the package.
9. Measurement labels: say exactly what each number covers (script time inside the frame
   callback is not "main thread"; cite the unthrottled frame interval as the whole-pipeline
   figure; label which scene each first-frame time is from; mention Growth's GPU p99 if it
   persists). Re-run the measurements after these changes and update the table, since the
   design changes may change frame cost.
10. Remove the dead `Story.onChange` and its listeners.
11. Toggle buttons: a fixed label with `aria-pressed`, or a changing label without it, not both.
12. The package's sound question names every cue that exists, including the touch cue.

## Then
Update the screenshots and `docs/reviews/session-w1.md` to match. Re-run `pnpm test`,
`typecheck`, `tools/check.mjs` (with the new toggle-back cases) and the measurements; run
`make check` once. Same hard rules as the dispatch (Edit/Write only, explicit staging, never
`answers-2.md`, no `.env`, no subagents). Append a fix report to `task-W1-report.md` (changes,
covering tests, commands, output) and reply with the short contract.
