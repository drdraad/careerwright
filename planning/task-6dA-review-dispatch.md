# Review: Task 6d slice A, facts instead of sentences, and each target stored once (two halves)

Careerwright L0, branch `l0-local-release`, commits 86d7ead..8ad36a6 (1577db2, 8ad36a6).
Two reviewers split this slice by focus. Your dispatch line names your half.

- **Facts half:** discovery's notes and title-idea lines (and any other composed line)
  turned into structured facts in the API, worded in the web.
  - Does every note still report what it reported before?
  - Does the backend now compose no sentence the person reads?
  - Is every new or reworded sentence true under the sentence rule ("says what Careerwright
    did or checked, never what a source or list contains")? Is it plain?
  - Are the `vocabulary.ts` maps exhaustive, so that a new code fails the type check?
  - Is the slate unchanged for the existing evaluation cases (ranking, rules and thresholds
    are frozen, R11)?
  - Was the article and plural regex removal done well?
  - Is the API free of prose (R11)?
- **Target-record half:**
  - migration 0034 and its CHECKs and row-level security;
  - `resolve_target` replacing four resolvers;
  - every consumer (the slate, the sketch, the strength, Skills, the world) reading the stored
    record;
  - existing profiles migrated forward;
  - the `concept_key` change ("&" as "and", accents folded) by a forward migration, with
    re-keying;
  - the coverage line where a target is chosen;
  - Skills' seed from the stored record. Note that ADR 0012's step 3 was dropped, so "bookkeeper"
    is now ambiguous in Skills until the person picks one. Is that correct and honest, or a
    regression?
  - room for slice B's kinds (an ONS title, the person's own words) without a second migration.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration. Grade by
   the effect on the person. The sentence rule binds; don't propose new wording for a rare edge
   case of a sentence that keeps it. Suggestion quality is the product owner's call.
2. The brief, `.superpowers/sdd/l0-sprint-tasks/task-6d-brief.md` (the whole Task 6d card), and
   the dispatch, `task-6dA-dispatch.md`, which says exactly what slice A delivers. The rest of
   the card is slice B's: don't report it missing.
3. The implementer's report (unverified claims), `task-6dA-report.md`. Its concerns include:
   - a heredoc source edit (`profile/records.py`);
   - one `npx tsc` run;
   - the "bookkeeper" change, with one changed capability assertion;
   - two reworded sentences;
   - removing and recreating another agent's acceptance lock (the controller has handled it).
4. The diff, `.superpowers/sdd/l0-sprint-tasks/review-86d7ead..8ad36a6.diff` (11,330 lines).
   Read your half's files in full. Skim the rest for anything that crosses into your half.
5. As needed:
   - ADR 0015, and ADRs 0007 and 0012 (amended in the diff);
   - the audit's code appendix, `docs/reviews/l0-audit-2026-10-31/B-code-coherence.md` (F3, F5,
     F7: the "before");
   - `CLAUDE.md`'s discovery invariant and the sentence rule.

## Rules
- Read-only. Never modify the working tree, index, HEAD or branches. Another implementer works
  in a worktree.
- `make check` and `make acceptance` passed (the implementer's runs). Don't re-run suites. One
  focused test is fine for a specific doubt, if it needs no stack.
- No web requests, no live calls, no Docker, no browser tools, no headed browser. No
  subagents. Never read `.env`, `~/.careerwright` or `~/.nessa`.

## Output
- Facts half: `.superpowers/sdd/l0-sprint-tasks/task-6dA-review-facts.md`.
- Target-record half: `.superpowers/sdd/l0-sprint-tasks/task-6dA-review-targets.md`.

Use the contract's format. Then reply with at most 10 lines: counts by severity, each Critical
or Important item in one line, and the path.
