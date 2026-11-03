# Task 12b, screens half (12bB): the Options chapter (worktree)

Careerwright L0. The backend half (12bA: the checkpoint, supplied figures, added options, pack
0.4.0) and Task 12c (a tuition fee loan is a loan to repay) are integrated. The product owner's
word on 3 November 2026: build the screens now. Beside you: 10B (the Skills chapter, worktree
wt-10b) and a You chapter tidy-up (the main tree). Routes (14B) waits for the parts you and it
share: build those first (see Deliver 1) and say in a short message to the controller when they
are committed, then carry on.

## Your tree
Worktree `/Users/darianraad/Code/careerwright-wt/12bb`, branch `wt-12bb` (from 203ee40; `var`
linked; dependencies installed). Rebase onto `claude/confident-ramanujan-ux3saw` at the end.

## Read first
`/Users/darianraad/Code/careerwright/planning/implementer-contract.md` (item 6: walk the journey
for load), your brief `planning/task-12b-brief.md` (all of it; the card "Task 12b" at its end),
`planning/carry-forward-task-12.md`, `planning/task-12bA-report.md` (what the API gives you),
the Task 14 card in `planning/task-14-brief.md` (what Routes will reuse from you),
`docs/demo/demo-video-script.md` scene 7 (the Options cut), `CLAUDE.md` ("The experience", the UI
invariants, money in pounds, unknown never 0, a loan never support), plan section 4,
`docs/design/README.md` (the Options place: "bridges across the dark stretches"), and the You
chapter's code as the pattern to follow.

## Deliver
1. **First, the parts Routes shares** (money and date display from the generated client, the
   option and funding facts' plain words, the missing-fact line with its box, anything else the
   Task 14 card names as coming from Options): small, tested, committed, then a one-line
   message to the controller.
2. The Options chapter's working view and its place in the world, as the card says, from real
   API facts only (never computing affordability, a rank or feasibility in the web). For the
   demo: a degree whose fee reads as a loan paid straight to the university and repaid later,
   not the person's own money; an apprenticeship and a T Level beside it; a missing fact named
   plainly with a box to fill it in (the person's own figure, labelled as theirs).
   The product owner's rules for every screen (3 November 2026): one place to type and one clear
   next action per step; nothing shown before it is needed; no line that doesn't change the
   next action (they found the You chapter "WAY too much text"); actions teal; no em dash; plain
   words; money in pounds.
3. Stories for every state, Vitest tests that read what the person sees, journeys for the main
   path; the register rows it closes (last commit).

## Rules
`make check` after each change. Focused integration runs only if you touch the backend, under
the lock (one guarded command; wait and retry if held; never remove a lock you didn't take):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright-wt/12bb/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/12bb-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN for logic. Edit/Write only (generators fine; no sed,
Python or heredoc edits of files), explicit pathspecs, no web requests (Storybook with
`STORYBOOK_DISABLE_TELEMETRY=1` and its update check off), no live calls, no subagents, never
read `.env`, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-12bB-report.md`; reply with the short
contract and head SHA.
