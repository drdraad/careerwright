# Task 10, screens half (10B): the Skills chapter (worktree)

Careerwright L0. The backend half (10A) is integrated. Session W2 and its fixes are done (Task
W2F, Task 6g); the product owner's word on 3 November 2026: build the screens now. Beside you:
12bB (the Options chapter, worktree wt-12bb) and a You chapter tidy-up (the main tree,
`Directions.tsx`). Routes (14B) starts later. Keep to the Skills chapter's files; shared files
(`vocabulary.ts`, `globals.css`) only in your own sections.

## Your tree
Worktree `/Users/darianraad/Code/careerwright-wt/10b`, branch `wt-10b` (from 203ee40; `var`
linked; dependencies installed). Rebase onto `claude/confident-ramanujan-ux3saw` at the end.

## Read first
`/Users/darianraad/Code/careerwright/planning/implementer-contract.md` (item 6: walk the journey
for load), your brief `planning/task-10-brief.md` (all of it; the card "Task 10" is at its
end, including the 2 November line: an expected qualification reads "if you get your grades"),
`planning/carry-forward-task-10.md`, `planning/task-10A-report.md` (what the API gives you),
`docs/demo/demo-video-script.md` scene 7 (the Skills cut), `CLAUDE.md` ("The experience", the UI
invariants), plan section 4, `docs/design/README.md` (the Skills place: "the ground between the
person and a destination, stretch by stretch"; a gate is "Ready if you pass ..."), and the You
chapter's code as the pattern to follow (`apps/web/src/components/YouChapter.tsx`,
`Conversation.tsx`, `ReviewTray.tsx`, `WhatWeKnow.tsx`).

## Deliver
The Skills chapter's working view and its place in the world, as the card says, from real API
facts only (never computing readiness, a rank or a level in the web). The product owner's rules
for every screen (3 November 2026): one place to type and one clear next action per step;
nothing shown before it is needed; no line that doesn't change the next action (they found the
You chapter "WAY too much text"); actions teal, information never looks like an action; no em
dash; plain words, a technical word explained in a few words or replaced. For the demo: what a
target asks for, what the person can already show, and an entry requirement the person expects
to meet reading "if you get your grades". Stories for every state, Vitest tests that read what
the person sees, journeys for the main path; the register rows it closes (last commit).

## Rules
`make check` after each change. Focused integration runs only if you touch the backend, under
the lock (one guarded command; wait and retry if held; never remove a lock you didn't take):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright-wt/10b/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/10b-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN for logic. Edit/Write only (generators fine; no sed,
Python or heredoc edits of files), explicit pathspecs, no web requests (Storybook with
`STORYBOOK_DISABLE_TELEMETRY=1` and its update check off), no live calls, no subagents, never
read `.env`, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-10B-report.md`; reply with the short
contract and head SHA.
