# Task W2F, slice B: the conversation and its review card (worktree)

Careerwright L0. Session W2 (2 November 2026) was stopped early by the product owner; Task W2F
fixes the You chapter before the Skills, Options and Routes screens. Three slices run at once on
disjoint files: A (Muse's turns, backend, worktree w2fa, adds a "Tasks you don't enjoy" answer
and a new prompt version), B (you), C (What we know, targets and suggestions, the main tree).

## Your tree
Worktree `/Users/darianraad/Code/careerwright-wt/w2fb`, branch `wt-w2fb` (from fc9435a; `var`
linked; dependencies installed). Work and commit only there. Rebase onto
`claude/confident-ramanujan-ux3saw` at the end, as the contract says.

## Read first
`/Users/darianraad/Code/careerwright/planning/implementer-contract.md`, your brief
`planning/task-W2F-brief.md` (all of it: the card is "Task W2F" at its end),
`planning/session-w2-findings.md` (items 3, 5's and 6's review-card parts, and 9's
conversation parts are yours), `CLAUDE.md` ("The experience" and the UI invariants), plan
section 4, `docs/design/README.md` (the You place's states). Then
`apps/web/src/components/Conversation.tsx`, `YouChapter.tsx`, `ReviewTray.tsx`,
`src/lib/conversation.ts`, `src/lib/profile.ts`, their tests and stories.

## Deliver (web only; each as something the person sees)
1. **Nothing is lost by typing early.** While "How would you like to start?" is showing, Send
   waits for that choice, with one plain line saying so. While a reply's review card waits,
   Send waits until it is saved or "Keep none" is chosen, also with one plain line. A typed
   message is kept in the box meanwhile (never wiped). The demo workspace behaves the same.
2. **The review card shows what a list change does**: against what is saved, what it adds and
   what it removes (an item taken back reads as removed), and the hint line for the three task
   answers (enjoyed, confident, done) so two similar items read as different answers.
3. **The card's Save stays in the first screen** with three or more changes, at 1280 × 800 and
   390 × 844.
4. **The Meta key card leaves the conversation**: one quiet line or the account menu, wherever
   the existing design keeps settings; its Rotate and Revoke still reachable. Say where in
   your report.
Your words go in `apps/web/src/lib/vocabulary.ts`'s conversation and review-card sections
only. Slice A adds a new answer to the field-label section; slice C changes What we know,
targets and suggestions: don't touch those.

## Rules
`make check` after each change. No integration or acceptance runs (web only; the controller
runs acceptance). Update the Storybook stories and Vitest tests your change touches; journeys in
`apps/web/e2e` may need updating: change only the steps your change intends (e.g. a journey that
sent a message before deciding a card), and list each in your report. RED before GREEN.
Edit/Write only, explicit pathspecs, no web requests, no live calls, no subagents, never start
Docker, never read `.env`, never push. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-W2F-B-report.md`; reply with the short
contract and head SHA.
