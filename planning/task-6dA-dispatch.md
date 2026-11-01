# Task 6d, slice A: facts instead of sentences, and each target stored once

Careerwright L0. Task 6d opens the role space, so that a person's job can be recognised even
when no standard list holds it. It runs as two slices, and this is the first. It lays the
foundation, so that slice B (the UK title search, "None of these is my job" and ONS-backed
title ideas) is built on facts and one target record, never on more English sentences or a
fifth title resolver.

## Your tree
The **main tree**, `/Users/darianraad/Code/careerpathoptimizer`, branch `l0-local-release`
(HEAD 60c8516 or later).
- Another implementer (Task 12a's fix round) works in a worktree on the planning code. It
  never touches the main tree, but when it integrates, it brings a migration (0033), the
  generated client and the register. If you add a migration, take the next free number when
  you start, and say so in your report: the controller sequences the integration.
- Commit with explicit pathspecs. `docs/requirements-register.md` and `docs/plan/*` change
  only in your last commit.

## Read first
1. `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`, all of it.
2. Your brief, `.superpowers/sdd/l0-sprint-tasks/task-6d-brief.md` (the whole Task 6d card,
   the Global Constraints and standing rulings R1–R15). It is your requirements, with the
   exact values to use verbatim. **This slice delivers only:**
   - the card's first bullet ("First, facts instead of sentences");
   - the card's "Each target is stored once" bullet;
   - the parts of "Also" and acceptance item 6 that belong to them.

   Everything else in the card is slice B. Don't build it.
3. The audit's code appendix, `docs/reviews/l0-audit-2026-10-31/B-code-coherence.md`, findings
   F3 (the notes), F5 (four title resolvers, with `file:line` for each) and F7 (words in three
   layers).
4. ADR 0015 (the role space), and ADR 0007 and ADR 0012 as amended on 2026-10-31.
   `CLAUDE.md`'s discovery invariant and the sentence rule.
5. Background: `docs/reviews/l0-audit-2026-10-31/F-role-space.md`, sections 4 to 6.

## What "done" means for this slice
1. **Facts, not sentences (R11).**
   - Discovery's search notes, its title-idea lines and its other person-facing composed
     lines become structured facts in the API: what the search or match did (found work,
     found none, not searched, matched, matched several, not matched), with a reason code and
     the values the words need.
   - The backend composes no sentence the person reads.
   - The web words each fact from `src/lib/vocabulary.ts`, with exhaustive maps, so a new code
     fails the type check.
   - **What each note reports doesn't change:** R11 freezes the notes and their matching
     rules. Only where the words live changes. Keep each sentence's meaning, and make it
     plainer only where the sentence rule requires.
   - Tests check the facts; one test per fixed sentence checks its words.
   - Remove the article and plural regexes for ESCO titles (B, F7) by using templates that
     need none.
   - Regenerate the client.
   - The slate's ranking, rules and thresholds don't change. A test shows the same slate for
     the existing evaluation cases.
2. **Each target stored once (B, F5).**
   - When a target is chosen or saved, store with it:
     - its occupation, or none;
     - the source of that link (the person's ESCO choice, an exact ESCO label, the option
       pack's crosswalk, or none yet);
     - its coverage: one of the option pack's targets, or not.
   - One `resolve_target`, with one set of normalisation rules, replaces the four resolvers in
     `profile/titles.py`, `profile/sketch.py`, `capability/commands.py` plus `matrix.py`, and
     `profile/exploration.py`.
   - The slate, the sketch, the strength, Skills and the world read the stored record.
   - The record leaves room for slice B's kinds (a UK title from the ONS index, the person's
     own words) without a second migration. The kinds themselves are slice B's.
   - Fix the parked `concept_key` gap here: "&" against "and", and accented titles against
     their plain spelling. A migration-defined key changes only by a new forward migration,
     and existing rows are re-keyed in it. Test it with a real ESCO title of each kind.
   - Existing profiles migrate forward: a stored target title gets its record.
   - Show the coverage where a target is chosen, as one plain line from a fact. For example,
     for a pack target: "Careerwright can check skills, options and routes for this role".
     For any other: say plainly what it can do now. Session W2 judges the words.
3. **Acceptance for this slice:**
   - a plural or punctuated title, an "&" title and an accented title each resolve the same
     in every consumer;
   - the slate for the existing evaluation cases is unchanged;
   - every discovery note and title-idea line arrives as a fact with a reason code, carrying
     no sentence;
   - `make check` and `make acceptance` pass.

## Hard rules
- Edit/Write for every source change: no scripts that rewrite files, not even one-token
  replacements. Formatters on your own files and the project's generators are fine.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser or window.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`, and leave every running stack alone.
- No subagents. Never push.
- DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion, with why.
- Never write distress or self-harm text.

## Checks
- `make check`.
- `make acceptance` once before your final commit, **under the lock**.
- Design references, only if this slice changes what a place shows (the coverage line):
  `cd docs/design && pnpm run contrast && pnpm run screenshots`, mirrored byte for byte.

## Report
Write the full report to `.superpowers/sdd/l0-sprint-tasks/task-6dA-report.md`. Include:
- the old sentence and the new fact and words for each note;
- each resolver replaced;
- the migration;
- RED then GREEN evidence.

Then reply with only the short contract.
