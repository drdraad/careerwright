# Task W2F, slice C: What we know, targets and suggestions (main tree)

Careerwright L0. Session W2 (2 November 2026) was stopped early by the product owner; Task W2F
fixes the You chapter before the Skills, Options and Routes screens. Three slices run at once on
disjoint files: A (Muse's turns, backend, worktree w2fa), B (the conversation and its review
card, worktree w2fb), C (you).

## Your tree
The main tree, `/Users/darianraad/Code/careerwright`, branch
`claude/confident-ramanujan-ux3saw`. Commit with a pathspec only (`git commit -- <paths>`);
the controller also commits ledger lines here.

## Read first
`planning/implementer-contract.md`, your brief `planning/task-W2F-brief.md` (all of it: the
card is "Task W2F" at its end), `planning/session-w2-findings.md` (items 1, 2, 8 and the
answers form's part of 9 are yours; its screenshots are in
`/private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/known-*.png`),
`CLAUDE.md` ("The experience" and the UI invariants), plan section 4, `docs/design/README.md`,
ADR 0007 and ADR 0015, Task W2E's card (its "A chosen target is confirmed, never out of date").
Then `apps/web/src/components/WhatWeKnow.tsx`, `ProfileEditor.tsx`, `fields.tsx`,
`Directions.tsx`, `src/app/globals.css`, `careerwright/profile/exploration.py`.

## Deliver (each as something the person sees)
1. **No label printed over its value**, at any width, in What we know (the `.fact` grid). Add a
   long-values state (three long targets, an expected qualification, long task answers) to the
   visual checks so this is caught from now on.
2. **Removing a target**: a Remove beside each target in What we know (a short "Your targets"
   list near its top) and in a suggestion's "Saved as one of your targets" box, through the
   existing profile save, with Undo. Removing a target alone leaves the suggestions current
   ("Suggest again" stays quiet, "Make this a target" stays the bright action): extend the rule
   W2E made for adding a target, in `profile/exploration.py`, with a test. The full-targets line
   ("You have 3 targets…") says where to remove one. Decide what removing the last target
   leaves, and record it as a ruling.
3. **The answers form's Save stays in reach** (e.g. kept in view while the form is open).
4. **A suggestion's title, what the work is, and its kind of work are easy to tell apart**: a
   short "What the work is" heading or a lead line under the title for the description, and
   "Kind of work" no longer read as a second title. Keep the recorded actions-first order unless
   you can show it is what makes the card hard to read; say which in your report.
Your words go in `apps/web/src/lib/vocabulary.ts`'s What we know, targets and suggestions
sections only. Slice A adds a new answer to the field-label section; slice B changes the
conversation and review card: don't touch those.

## Rules
`make check` after each change. One focused integration run for the slate rule, under the lock
(wait and retry if held; never remove a lock you didn't take):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/w2fc-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. Update the stories, Vitest tests and journeys your change touches (list
each changed journey step). RED before GREEN. Edit/Write only, explicit pathspecs, no web
requests, no live calls, no subagents, never read `.env`, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-W2F-C-report.md`; reply with the short
contract and head SHA.
