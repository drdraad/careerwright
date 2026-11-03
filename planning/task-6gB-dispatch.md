# Task 6g, slice B: Muse widens the horizon (worktree)

Careerwright L0. Slice A (approved, not yet integrated: the main tree is under a full
acceptance run) splits the slate into "Next step" and "Aim higher" by a pinned ISCO skill-level
table. It only re-sorts the pool today's search finds, so Sam's "Aim higher" still holds
"Equine dental technician". Slice B is the product owner's chosen fix (3 November 2026): "Should
Muse add Aim higher job ideas from your answers, each shown only once Careerwright finds that
title on an official job list?" Yes.

## Your tree
Worktree `/Users/darianraad/Code/careerwright-wt/6gb`, branch `wt-6gb`, from slice A's head
fd864f0 (`var` linked; dependencies installed). At the end, rebase onto
`claude/confident-ramanujan-ux3saw` (slice A and Task W2F's slice E will be on it by then; keep
both ADR 0007 sections; regenerate `apps/web/src/generated` on a conflict; renumber a migration
if another took its number) and re-run `make check`.

## Read first
`/Users/darianraad/Code/careerwright/planning/implementer-contract.md` (item 6: walk the journey
for load), `planning/task-6g-brief.md` (all of it; the card "Task 6g" at its end),
`planning/two-horizons-design.md` (approach B and C), slice A's report and its review
(`planning/task-6gA-report.md`), `CLAUDE.md` (the model proposes; code corroborates; a person's
own title in their words), ADR 0007, ADR 0015. Then `careerwright/profile/discovery.py`,
`discovery_agent.py`, `fixture_discovery.py`, `exploration.py`, `slate.py`, `slate_facts.py`,
`careerwright/api/discovery_schemas.py`, `routes_export.py`, `apps/web/src/components/Directions.tsx`.

## Deliver
1. **Muse's Aim higher ideas**: the one discovery call (a new prompt version) also proposes up
   to six "aim higher" title ideas, each citing 1 to 3 of the person's answers (checked as title
   ideas are today); the person's qualifications are among what Muse reads (an expected one is
   never counted as met; say so in the prompt). The discovery's output bound and its cost
   reservation cover the larger output, priced from the registry. The demo proposer proposes
   none.
2. **Code confirms and places**: each idea is confirmed by the existing rule (an ESCO label, the
   ONS UK job-title index; otherwise it stays "not yet found", with Research this role), then
   placed by slice A's level rule. Within Aim higher, confirmed ideas and joins rank before a
   single search's hit (a rule in code, with a test, evaluated on Sam's and Maya's cases); an
   ONS title whose groups disagree on level goes in neither set and stays in the UK-index list.
   An ONS idea placed in a set can be made a target through the profile's one write path. The
   slate stays deterministic given its inputs.
3. **Three Minors from slice A's review, fixed here** (the product owner's load rule): the
   training sentence appears once per set, not on every card; the "placed each suggestion"
   note shows only when a set has suggestions; the "More depth" note's count matches what can
   show.
4. Evaluation cases: Sam (client onboarding assistant, own words, "working with people, not
   spreadsheets; I'd retrain, but not if it means a pay cut for three years") and Maya (no job
   yet, A-levels in biology, chemistry and psychology expected, runs a Brownies group, likes
   science and people) each get an offline case with a fixed model output showing confirmed
   ideas in Aim higher; one live-only case each for the controller's capped check (not in the
   default live set).
5. ADR 0007 and ADR 0015 lines, the export format if a field is added, the register rows (last
   commit).
Walk the Suggestions journey for load before you report.

## Rules
`make check` after each change. Focused integration runs (discovery, the evaluation on the full
release) under the lock, one guarded command each (wait and retry if held; never remove a lock
you didn't take; a full acceptance run holds it now):
`L=/Users/darianraad/Code/careerwright/.superpowers/acceptance.lock; mkdir $L && { cd /Users/darianraad/Code/careerwright-wt/6gb/backend && uv run --locked pytest -m integration <files> > /private/tmp/claude-501/-Users-darianraad-Code-careerwright/51b74d1a-6cb8-4bb3-b832-9054484ac3c7/scratchpad/6gb-int.log 2>&1; rc=$?; rmdir $L; exit $rc; }`
No whole acceptance. RED before GREEN. Edit/Write only (generators fine; no sed, Python or
heredoc edits of files), explicit pathspecs, no web requests (Storybook with
`STORYBOOK_DISABLE_TELEMETRY=1` and its update check off), no live calls, no subagents, never
read `.env`, never push. No em dash in anything a person reads, your report included. Commit
messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/Users/darianraad/Code/careerwright/planning/task-6gB-report.md`; reply with the short
contract and head SHA.
