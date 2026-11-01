# Task 6d, slice B: any UK title, recognised as the person types

Careerwright L0. Task 6d opens the role space, so a person's job is recognised even when no
standard list holds it. Slice A (complete, 1577db2..59095b8) laid the foundation: discovery's
notes as facts the web words, and each target stored once with its occupation, the source of
that link and its coverage, decided by one `resolve_target`. This slice builds the title flow on
that foundation. Slice C (later) takes the rest of the card: optional seniority and industry,
the ESCO research's three fixes and the pasted-CV decision. Don't build those.

## Your tree
The **main tree**, `/Users/darianraad/Code/careerpathoptimizer`, branch `l0-local-release`
(HEAD f7f0e4d or later).
- Another implementer (Task 13b's fix round) works in the worktree
  `careerpathoptimizer-wt/13b` on the planning code. Its branch holds migration **0036**
  (`r0036_route_solves.py`) and will likely integrate before you finish. If you add a
  migration, check `backend/src/careerwright/migrations/versions/` on `l0-local-release`
  just before you commit it and take the next free number then (0036 if 13b hasn't
  integrated, else 0037); say which in your report. Regenerate the client after any API
  change, again after 13b integrates if it lands mid-task.
- Commit with explicit pathspecs. `docs/requirements-register.md` and `docs/plan/*` change
  only in your last commit.

## Read first
1. `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`, all of it, including the
   acceptance lock.
2. Your brief, `.superpowers/sdd/l0-sprint-tasks/task-6d-brief.md` (the whole Task 6d card,
   the Global Constraints and standing rulings R1–R15). It is your requirements, with the
   exact values to use verbatim. **This slice delivers only these card bullets:**
   - "The first question finds any UK title";
   - "Which of these is closest?";
   - "Title ideas the ONS index lists become suggestions";
   - the last bullet: the lines that say a title isn't in ESCO, and the evaluation cases for
     unsupported-title rejection;
   - acceptance items 1–4 and 6, and item 5 for what this slice shows.
3. Slice A's report, `task-6dA-report.md` (all three sections), and its dispatch,
   `task-6dA-dispatch.md`: what the stored record holds, and the room it left for this
   slice's kinds (a UK title from the ONS index, the person's own words).
4. The audit's role-space appendix, `docs/reviews/l0-audit-2026-10-31/F-role-space.md`,
   section 6 ("The smallest first slice") and section 4 (existing parts that can carry it).
5. ADR 0015 (the role space), ADR 0007 and ADR 0012 as amended. `CLAUDE.md`'s discovery
   invariant (a title idea becomes a suggestion only when deterministic code corroborates it;
   a person's own title is always kept in their words) and the sentence rule.

## Carried to this slice (the controller's rulings from slice A's reviews)
1. **Title ideas carry a reason code,** and the three values slice A worded by branching are
   worded by exhaustive maps in `vocabulary.ts`, so a new code fails the type check
   (`task-6dA-review-facts.md`, its Minors on the title ideas and on branching).
2. **The source-citing rule against your new kinds:** check whether "only a choice may cite a
   source" (the target record's CHECKs, `task-6dA-review-targets.md`) fits a UK title from the
   ONS index and the person's own words. If a CHECK must change, do it in your one migration.
3. **A qualifier that names a different nursing field never reaches the pack's adult
   "Registered nurse".** "Registered nurse (mental health)", "(children's)" and "(learning
   disabilities)" are other registered fields; the pack's evidence is adult nursing. A
   neutral qualifier ("(adult)", "[2nd line]") still reaches it. Keep it inside the one
   `resolve_target`, as a named constant with its reason, and re-decide the stored records
   it reaches in your migration (never edit 0034 or 0035). Test each field.

## Decisions that bind you
- **Nothing typed is refused.** "Use my own words: '…'" is always offered and keeps the title
  exactly as typed.
- **The first answer changes the world within a second, with no model call,** without a key
  and in the demo; a browser test proves the world answers within ten seconds of the first
  answer. The type-ahead reads only the pinned ESCO release and the pinned ONS SOC 2020
  coding index (already in `var/datasets/`, hash-checked).
- **ISCO-08 groups come from the ONS index's own coding.** A title coded to more than one
  group shows every group, none picked. "None of these is my job" leaves the role with no
  ESCO seed, and the words say what isn't known yet without asking anyone to pick another
  job.
- **R11, facts not sentences:** every new note (the UK title list, the person's own words,
  "None of these is my job", the closest-occupation offer) is born as a fact with a reason
  code; the web words it from `vocabulary.ts` with exhaustive maps.
- **A sentence the person reads says what Careerwright did or checked, never what a list
  contains** (`CLAUDE.md`). When exact and plain conflict, say less.
- **No screen states skills, pay, readiness or openings for an ONS-only or own-words title
  beyond what its sources hold.** Unknown is shadow, never zero.
- **The slate's ranking, rules and thresholds don't change** (R11 freezes them) except where
  the card says: an ONS-listed title idea becomes a suggestion in its own short list beside
  the slate.
- **The experience.** The type-ahead and "Which of these is closest?" are part of the world
  answering the person (`CLAUDE.md`, "The experience"); practical first: the decision stays
  on the first screen on a phone.

## Hard rules
- Edit/Write for every source change: no scripts that rewrite files, not even one-token
  replacements. Formatters on your own files and the project's generators are fine.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt`.
- No live calls, no web requests, no Docker pull, no headed browser or window. Never start
  Docker.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`, and leave every running stack alone.
- No subagents. Never push.
- Migrations are forward-only. DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion, with why.
- Never write distress or self-harm text.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Checks
- RED before GREEN for each behaviour.
- `make check`.
- `make acceptance` once before your final commit, under the lock, in one guarded command. If
  a test fails, re-run the whole `make acceptance` and report both runs.
- Design references, since this slice changes what places show:
  `cd docs/design && pnpm run contrast && pnpm run screenshots`, mirrored byte for byte; and
  `cd apps/web && pnpm run review-screenshots` for the places you change.

## Report
Write the full report to `.superpowers/sdd/l0-sprint-tasks/task-6dB-report.md`. Include each
new fact with its words, each acceptance item with its test, the migration, the carried items,
and RED then GREEN evidence. Then reply with only the short contract.
