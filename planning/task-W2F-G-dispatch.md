# Task W2F, slice G: the Suggestions view, tidied (main tree)

Careerwright L0. The product owner's look at Sam's suggestions (3 November 2026), verbatim:
"the groups are not nicely distinguished. There is WAY too much text in the open card. Also,
these buttons at the top don't seem to do anything: Balanced, Closer to what I do, Less
familiar, Broader." Beside you: 10B (Skills, worktree wt-10b) and 12bB (Options, worktree
wt-12bb). Keep to the Suggestions view's files; shared files (`vocabulary.ts`, `globals.css`)
only in the suggestions sections.

## Your tree
The main tree, `/Users/darianraad/Code/careerwright`, branch
`claude/confident-ramanujan-ux3saw`. Commit with a pathspec only; the controller also commits
ledger lines here.

## Read first
`planning/implementer-contract.md` (item 6), `planning/task-W2F-brief.md` (its preamble),
`planning/task-6gA-report.md` and `planning/task-6gB-report.md` (the two sets and their reviews),
`CLAUDE.md` (the slate invariants: the controls are view parameters, never limits; ADR 0007
decision 12, the written note's quotations), `apps/web/src/components/Directions.tsx` and its
tests and stories. The open card today (Sam 2, live) shows: the title, four actions, "What the
work is" with up to 360 characters, "Kind of work", "Why this could suit you" with a sentence,
three quotations and a disclaimer, "How Careerwright found it" with one line per search, "What
might not suit you", "Try it before committing", and a pay and demand line.

## Deliver
1. **The two sets read as two groups at a glance**: "Next step" and "Aim higher" clearly
   separated (heading, spacing and one plain line each saying what the set is), never by
   industry colour or a status colour; sea-glass stays for selection and action only.
2. **The open card at about a third of today's text**: the title, the one bright action ("Make
   this a target") and the other actions; one or two plain lines of what the work is; "Why this
   could suit you" as its sentence with the quotations one step away (the checked-quotes rule
   unchanged: the quotes and the "only the quoted words were checked" line stay, one step away);
   everything else (how it was found, what might not suit, try it first, pay and demand) one
   step away under a single "More about this role". Nothing removed from the product: moved one
   step away.
3. **The direction buttons**: with the two sets, "Balanced", "Closer to what I do", "Less
   familiar" and "Broader" no longer change what is shown in a way the person can see. Remove
   them from the screen (and "More depth" too if it no longer changes anything visible);
   remove now-dead web code they leave; leave the API's view parameters unless nothing calls
   them, and say which in your report.
4. Walk the Suggestions journey for load (count lines and actions on the closed and the open
   card, before and after, in your report). Stories, Vitest tests that read what the person
   sees, the journeys this changes (list each changed step).

## Rules
`make check` after each change. No integration or acceptance runs (web only). RED before GREEN
for logic. Edit/Write only, explicit pathspecs, no web requests (Storybook with
`STORYBOOK_DISABLE_TELEMETRY=1` and its update check off), no live calls, no subagents, never
read `.env`, never push. No em dash. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-W2F-G-report.md`; reply with the short
contract and head SHA.
