# Task W2F, slice A: Muse's turns (worktree)

Careerwright L0. Session W2 (2 November 2026) was stopped early by the product owner; Task W2F
fixes the You chapter before the Skills, Options and Routes screens. Three slices run at once on
disjoint files: A (you: Muse's turns, backend first), B (the conversation and its review card,
worktree w2fb), C (What we know, targets and suggestions, the main tree).

## Your tree
Worktree `/Users/darianraad/Code/careerwright-wt/w2fa`, branch `wt-w2fa` (from fc9435a; `var`
linked; backend and web dependencies installed). Work and commit only there. Rebase onto
`claude/confident-ramanujan-ux3saw` at the end, as the contract says.

## Read first
`/Users/darianraad/Code/careerwright/planning/implementer-contract.md`, your brief
`planning/task-W2F-brief.md` (all of it: the card is "Task W2F" at its end),
`planning/session-w2-findings.md` (items 4–7 are yours), `CLAUDE.md`, ADR 0006 and ADR 0007,
`careerwright/profile/interview.py`, `document.py`, `discovery.py`, the latest migration.

## Deliver
1. **"Tasks you don't enjoy"** (spec section 4's "disliked tasks"): a new list answer,
   `disliked_tasks`, proposed and confirmed like the other task answers, through the same
   command as a direct edit (ADR 0006). It informs only: never a search query, filter or
   ranking input; keep it out of discovery's answers (`profile/discovery.py`'s field set) and
   say so in a test. Profile schema version bump, a forward migration, seed, the generated
   client (`pnpm run generate` in `apps/web`), and its words in `apps/web/src/lib/vocabulary.ts`
   (the field-label section only: label, item label, hint, "less precise" line). Make sure What
   we know and the answers form show it with no other web change if the field lists are
   data-driven; if a component change is needed, keep it to the field's own entry and say so.
2. **One new interview prompt version** (`interview-turn-6`), with tests reading the prompt:
   - one activity in the same words in each task answer it belongs to (enjoyed, confident,
     done);
   - when the person takes something back, the list it proposes leaves it out;
   - a money limit hinted without a figure ("a pay cut", "not too expensive") is asked for in
     pounds as the next question, and never proposed without the person's figure;
   - when the person writes before choosing how to start (no entry mode), what to ask;
   - what the person doesn't enjoy goes in the new answer.
   Keep the existing safety and no-inference rules (`profile/safety.py`) untouched.
3. Offline evaluation cases where they exist for the interview (INT-*): update only what the
   new field and prompt intend; add one case for a dislike and one for a hinted limit.
4. ADR 0006 or 0007 line for the new answer; the register rows your work closes (last
   commit, after the rebase).

## Rules
`make check` after each change. Focused integration runs (the migration, the profile and
interview tests) under the lock, one guarded command each (wait and retry if held; never remove
a lock you didn't take):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright-wt/w2fa/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/w2fa-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN. Edit/Write only (generators fine), explicit pathspecs,
no web requests, no live calls (the controller runs the capped live check of the new prompt),
no subagents, never read `.env` or print an environment value, never push. Commit messages end
with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-W2F-A-report.md`; reply with the short
contract and head SHA.
