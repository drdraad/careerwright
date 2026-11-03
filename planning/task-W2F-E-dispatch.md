# Task W2F, slice E: no em dashes, and a review card with half the words (worktree)

Careerwright L0. The product owner's re-test (3 November 2026), verbatim: "Em-dashes are
outlawed! Muse must never use them in a response. Careerwright is too verbose in the chat
window when selecting which facts to choose. There are unnecessary qualifications that
overload cognitive load." Slice D (role research, the main tree) runs beside you on
`careerwright/evidence`, `tools/session.py` and the run limits: don't touch those.

## Your tree
Worktree `/Users/darianraad/Code/careerwright-wt/w2fe`, branch `wt-w2fe` (from 08382b6; `var`
linked; dependencies installed). Rebase onto `claude/confident-ramanujan-ux3saw` at the end.

## Read first
`planning/implementer-contract.md`, `planning/task-W2F-brief.md` (all of it), `CLAUDE.md`
("Talking to the user", "The experience", the UI invariants, the model-proposes invariants),
`planning/task-W2F-B-report.md` (what slice B added to the card), ADR 0006, ADR 0007 decision
12 (the slate's written note). The card as it reads today, with four changes:
`/private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/you--reply-changes-lists.png`
(Storybook story `you--reply-changes-lists`). Then `profile/interview.py`,
`interview_agent.py`, the slate explanation's and the strength proposal's prompts and checks,
`apps/web/src/components/ReviewTray.tsx`, `Conversation.tsx`, `src/lib/vocabulary.ts`.

## Deliver
1. **No em dash in anything a model writes for the person to read**: the interview's reply and
   next question, the slate's "Why this could suit you" prose, and the strength proposal's
   words (any other person-facing model text you find, too). Each prompt says so in one short
   line, and each output's existing check refuses an em dash (U+2014) and a spaced en dash used
   as one (" – "), so the existing repair asks again; never rewrite the model's words in code.
   The interview prompt's size guard (4,250 bytes; it stands at 4,238) means trimming: cut
   words, never a rule. A quotation the person wrote is quoted as they wrote it (a dash in
   their own words is theirs). New prompt versions; tests. Also check the app's own
   person-facing words (`vocabulary.ts`, components) hold none.
2. **The review card, half the words.** Today each change shows a "You said" or "Careerwright's
   reading, not a fact until you accept it" line, the whole list, separate "Adds"/"Removes"
   lines, an explanation line and four buttons; the tray adds "To review: N changes from your
   last message", "Accept, confirm or edit at least one first." and "Save the changes above or
   choose Keep none, then send. Your words stay here." Make each change read in about two
   lines: the answer's name with only what changes (e.g. "Tasks you enjoy: + fixing machines,
   − helping at Brownies"; a new answer just its value), its origin as a short tag (your words
   or Careerwright's reading) rather than a sentence, and its actions; the explanation line
   (slice B's task-answer hints) goes, or sits one step away; the tray's and Send's instruction
   lines become a few plain words each, or show only when needed. Keep what must stay: a limit
   is confirmed by name (its button's accessible name), its plain-words explanation stays one
   step away at most, every action keeps its accessible name, Save and Keep none stay in the
   first screen, nothing is lost by typing early, and the proposal's origin is never hidden.
   Leaf green for Accept and Confirm, teal for actions (unchanged). Update the stories, tests and
   journeys this touches (list each changed journey step).

## Rules
`make check` after each change. Focused integration runs (interview, slate explanation,
strength) under the lock, one guarded command each (wait and retry if held; never remove a lock
you didn't take):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright-wt/w2fe/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/w2fe-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN. Edit/Write only (generators fine), explicit pathspecs,
no web requests, no live calls, no subagents, never read `.env`, never push. Commit messages end
with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. No em dash in anything you
write for the person to read, your report included.

## Report
`/Users/darianraad/Code/careerwright/planning/task-W2F-E-report.md`; reply with the short
contract and head SHA.
