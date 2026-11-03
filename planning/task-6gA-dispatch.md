# Task 6g, slice A: two horizons placed by code (worktree)

Careerwright L0. The product owner's re-test (3 November 2026) found the suggestions basic and
"Directions to consider" odd, and asked for "Next step" and "Aim higher". Read the card and the
design first. Beside you: Task W2F's slice D (the main tree: `careerwright/evidence`, role
research) and slice E (worktree w2fe: the conversation, the review card, `RoleResearch.tsx`).
Don't touch their files.

## Your tree
Worktree `/Users/darianraad/Code/careerwright-wt/6ga`, branch `wt-6ga` (from 48750e6; `var`
linked; dependencies installed). Rebase onto `claude/confident-ramanujan-ux3saw` at the end.

## Read first
`/Users/darianraad/Code/careerwright/planning/implementer-contract.md` (item 6: walk the journey
for load), your brief `planning/task-6g-brief.md` (all of it; the card "Task 6g" is at its end),
`planning/two-horizons-design.md` (the causes with file:line, the common ground and approach
A), `CLAUDE.md`, ADR 0007, ADR 0015, ADR 0014 decision 4, the spec's discovery sections and its
section 22. Then `careerwright/profile/slate.py`, `exploration.py`, `slate_facts.py`,
`careerwright/catalogue/taxonomy_store.py`, `careerwright/api/discovery_schemas.py`,
`apps/web/src/components/Directions.tsx`.

## Deliver (slice A only; Muse's ideas are slice B, later)
1. The pinned skill-level table by ISCO sub-major group (`careerwright/catalogue`), with a test
   that checks it against the pinned ESCO release's group descriptions.
2. The person's reference level: from their role's ESCO occupation, or the ISCO groups the ONS
   index codes their title to when those agree; otherwise unknown, never a number, and ISCO's
   bands decide (1-2 Next step, 3-4 Aim higher). A person with no job yet, or a skipped role,
   is "unknown".
3. The slate in two sets, each through the same deterministic reranker, about three each:
   "Next step" at or below the reference level, "Aim higher" above it (for a level-4 role,
   level-4 work in another major group). Next step drops the forced "less familiar" slot
   (quotas close 2, transferable 1); no "Directions to consider" heading anywhere for a person
   whose work isn't known. Facts and codes from the API (the generated client regenerated);
   words in the web (`vocabulary.ts`'s suggestions section only).
4. An Aim higher card says, in one plain line, what Careerwright checked about its job group's
   usual training (e.g. "Most work in this job group usually needs a degree or equivalent
   training."), never that the person suits it, is ready, or that it pays more. Next step's work
   is never called basic. Walk the Suggestions journey for load (implementer item 6): headings,
   lines and actions per card stay as few as now or fewer.
5. Evaluation cases for Sam (client onboarding assistant, own words) and Maya (no job yet,
   A-levels expected) showing both sets as the rules say; existing slate tests updated only where
   the rule intends.
6. The spec's section 22 entry (the first slate's 2/2/2 balance replaced; Aim higher placed by a
   job group's usual training level, never pay or status, beside line 283's prestige rule), ADR
   0007's amendment, ADR 0015's line if titles are touched, the register rows (last commit).
   The world's near and far lines are not this slice.

## Rules
`make check` after each change. Focused integration runs (discovery, the evaluation on the full
release) under the lock, one guarded command each (wait and retry if held; never remove a lock
you didn't take):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright-wt/6ga/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/6ga-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN. Edit/Write only (generators fine; no sed, Python or
heredoc edits of files), explicit pathspecs, no web requests (Storybook with its update check
off: `STORYBOOK_DISABLE_TELEMETRY=1` and `--no-version-updates`), no live calls, no subagents,
never read `.env`, never push. No em dash in anything a person reads, your report included.
Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-6gA-report.md`; reply with the short
contract and head SHA.
