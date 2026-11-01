# Review: Task 6d slice B, any UK title recognised as the person types

You review one slice of Careerwright L0, in one of two halves (your half is named in your
prompt). It was built in the main tree on `l0-local-release`: commits f7f0e4d..21a397d (dff9c2e
code, 2317e19 review captures, 21a397d documents and register). It makes the first question
find any UK job title as the person types (the pinned ESCO release and the pinned ONS SOC 2020
coding index), always offers "Use my own words", asks "Which of these is closest?" with "None
of these is my job", lists ONS-indexed title ideas beside the slate, words the "isn't in ESCO"
lines from facts, and adds a nursing-field rule to the one `resolve_target`. The product owner
judges the words and the suggestions at session W2; you judge truth, the contract and the
experience bar.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration and the
   R11 carve-out for quotes, the person's words and model replies.
2. The brief, `task-6d-brief.md` (the whole Task 6d card), and the dispatch,
   `task-6dB-dispatch.md`: what this slice delivers, the carried items and the decisions that
   bind. Slice C (seniority and industry, the ESCO research's three fixes, the pasted CV) is
   not this slice: don't report its absence.
3. The implementer's report (unverified claims), `task-6dB-report.md`. Judge its concerns:
   - RED before GREEN only for the record's domain rules; the other tests were written
     alongside the code. Would each test fail without its code?
   - The first question now leads the start, before the entry choice, with "Skip for now",
     and tests that opened at the entry choice skip it first. Is this within the card, and
     does it keep the decision on the first screen on a phone?
   - Seeding a database now needs the UK index loaded first.
   - Not built: making a UK title idea a target from its list, and asking "which do you mean"
     in the start for own words that several ESCO occupations hold. Does the card or
     acceptance require either?
   - One heredoc append to a test file, restored and redone with Edit.
4. The diff, `.superpowers/sdd/l0-sprint-tasks/review-f7f0e4d..21a397d.diff` (6,768 lines;
   the generated client, lockfiles and images excluded). Read your half's files in full, the
   rest as needed.
5. As needed: ADR 0015, ADR 0007 and ADR 0012 (amended in the diff), slice A's reviews
   (`task-6dA-review-facts.md`, `task-6dA-review-targets.md`), the audit's role-space appendix
   (`docs/reviews/l0-audit-2026-10-31/F-role-space.md`, section 6), and `CLAUDE.md`'s
   discovery invariant, the sentence rule and "The experience".

## Half A: design and the person's experience (`design`)
- The web: the type-ahead, "Use my own words", "Which of these is closest?", "None of these is
  my job", the ONS title-idea list, the reordered start, and their words in `vocabulary.ts`.
- Does each sentence say what Careerwright did or checked, never what a list contains? Is
  any sentence false for a case the tests don't cover (an ONS title in several ISCO-08 groups,
  a title in neither list, a typo)? Plain words only, no internal terms.
- Does the first answer change the world within a second, with no model call, without a key
  and in the demo? Does the decision stay on the first screen on a phone? Keyboard focus and
  screen-reader names for the new controls.
- Is it a world answering the person, not a form (`CLAUDE.md`, "The experience")? Practical
  first.
- Acceptance items 1–5, in the demo workspace with no key and no network.

## Half B: the app, the truth and the tests (`app`)
- The backend: the type-ahead's reading of ESCO and the ONS index, ISCO-08 group lookup, the
  title record's new kinds and CHECKs, migration 0036, the nursing-field rule, the title-idea
  corroboration, the facts in the API, the evaluation cases, setup and seed changes.
- A title idea becomes a suggestion only when deterministic code corroborates it; a person's
  own title is kept in their words; nothing typed is refused.
- The pinned data only: the ONS index and ESCO from `var/datasets/`, hash-checked; no network.
- Migration 0036: forward-only, idempotent, row-level security and CHECKs that repeat the
  domain rules, safe on a database that applied 0035; does re-deciding records for the nursing
  rule rewrite anything a person chose or a pinned discovery depends on?
- R11: every new note is a fact with a reason code, worded by exhaustive maps; the carried
  items from slice A (title-idea reason code; the source-citing CHECK against the new kinds).
- Unknown is never zero; a blocked or unread source is never "none found".
- Tests: would each fail without its code? Disclosed test changes.

## Rules
- Read-only. Don't edit or commit. The main tree may change under you only at the controller's
  integration of another task (the route search); read slice B's code with
  `git show 21a397d:<path>`.
- `make check` and `make acceptance` passed (the implementer's runs); don't re-run suites. One
  focused fast test is fine for a specific doubt. No integration tests: they need the shared
  lock.
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`.

## Output
Write your review to `.superpowers/sdd/l0-sprint-tasks/task-6dB-review-<half>.md` (`design` or
`app`), in the contract's format. Then reply with at most 10 lines: counts by severity, each
Critical or Important item in one line, and the path.
