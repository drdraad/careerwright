# Task 6d, slice C: the real role beside ESCO, and the rest of the card

Careerwright L0. Task 6d opens the role space. Slice A (facts, one target record) and slice B (any
UK title as the person types, "Which of these is closest?", the support screen on the title
field and in What we know) are complete. This last slice finishes the card: optional seniority
and industry, the product owner's ESCO research's three fixes, and the pasted-CV decision.

## Your tree
The **main tree**, `/Users/darianraad/Code/careerpathoptimizer`, branch `l0-local-release`
(HEAD 51ca593 or later). No other implementer runs now. Your next migration, if any, is 0039
(down_revision "0038"). Commit with explicit pathspecs; `docs/requirements-register.md` and
`docs/plan/*` change only in your last commit.

## Read first
1. `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`, all of it, including the
   acceptance lock.
2. Your brief, `.superpowers/sdd/l0-sprint-tasks/task-6d-brief.md` (the whole Task 6d card, the
   Global Constraints and standing rulings R1–R15). **This slice delivers only these card
   bullets:**
   - "Optional seniority and industry";
   - "The ESCO research's three fixes";
   - "Pasted CV text, if it stays small";
   - the card's register line for the rows these close or update (PROF-08's seniority,
     PROF-12 closed or recorded as deferred, the Task 6d part of PROF-07, and any REC1 or DIV1
     row the three fixes touch).
3. Slice B's reports and reviews, for what the start, the title record and the support screen
   now do: `task-6dB-report.md` (all sections), `task-6dB-rereview-2-design.md`,
   `task-6dB-rereview-2-app.md`.
4. ADR 0015 (decision 4 is this slice's), ADR 0007 decision 14 (the unexpected connection) and
   ADR 0012 decision 10. The audit's role-space appendix,
   `docs/reviews/l0-audit-2026-10-31/F-role-space.md`, section 3 (the research weighed).
   `CLAUDE.md`'s discovery and support invariants and the sentence rule.

## Decisions that bind you
1. **The unexpected connection: the product owner's answer (1 November 2026): "Always a plain
   line".** Shared skills between the role and a suggestion are shown as a plain fact about the
   two roles, never as a discovery moment or a revelation. Keep the deterministic rule that
   picks it (ADR 0007 decision 14) only if a plain line still needs it; drop what made it a
   moment (its place as the Roles chapter's moment, any revelation styling or world event).
   Record the answer in ADR 0015 decision 4 and ADR 0007 decision 14. The Roles chapter's
   moment is Task M's to choose again: don't invent one.
2. **The other two ESCO fixes.**
   - Skills ESCO lists for a role are described as ESCO's list for that kind of work (the
     card's words: "ESCO lists these for this kind of work"), never as the person's skills or
     as "usual" without that source. Explain "ESCO" in plain words the first time it appears
     on a screen, or name it plainly.
   - The person can mark one "not part of my job": a display state, never evidence, never
     used for suitability or readiness, kept per role.
   - No revelation rests on ESCO's essential skills alone. Check the overlooked strength (it
     must rest on the person's verified words) and every other revelation path; fix any that
     doesn't.
3. **Seniority and industry:** optional, beside a role or a target title; matching ignores
   them; display and search keep them; unknown is shadow, never a default.
4. **Pasted CV text: decide "small" honestly, and defer if it isn't.**
   - Small means: it reuses the existing proposal path and the same review tray, so nothing
     commits unconfirmed; no new run kind; no new review screen; pasted text goes through the
     support screen (the product owner's "every place a person types"); third parties'
     emails, phone numbers and contact fields (a CV's references) are removed before anything
     is hashed, sealed or sent to a model (`CLAUDE.md`); the test model takes synthetic data
     only; it works in the demo with the fixture interviewer, or says plainly that it needs a
     key.
   - If any of that needs more than a small change, record it as an L0 deferral (plan section
     1, the specification's section 22 list is the controller's) with its reason, and close
     PROF-12 as deferred. Report which, and why.
5. **Carried from slice B's reviews:**
   - **The product owner's "every place a person types" (31 October 2026):** answers the person
     types in the conversation's review step, saved as a direct entry, go through the same
     support screen as What we know's direct entries (support policy, version and review
     status, ADR 0007). Tests use the existing risk-word fixtures only.
   - On a phone, the title panel's "Keep it as my job title" sits next to the line that names
     it, above the services, so it's on the first screen (`task-6dB-rereview-2-design.md`,
     R2-M1). Test it at 390 × 844.
6. **R11:** new API fields are codes and values, worded in `vocabulary.ts` with exhaustive maps.

## Hard rules
- Edit/Write for every source change: no heredocs or scripts that rewrite files, not even to
  append. Formatters on your own files and the project's generators are fine.
- `pnpm` only, never `npm` or `npx`.
- Stage explicit paths. Never stage `answers-2.md` or `esco_research.txt` (you may read
  `esco_research.txt`, the product owner's research, if useful).
- No live calls, no web requests, no Docker pull, no headed browser or window. Never start
  Docker.
- Never read `.env`, `~/.careerwright` or `~/.nessa`.
- Never run `make stop`, and leave every running stack alone.
- No subagents. Never push.
- Migrations are forward-only. DBOS `application_version` stays `careerwright-l0-1`.
- Disclose every changed test input or assertion, with why.
- Never write distress or self-harm text: tests use the existing risk-word fixtures only.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Checks
- RED before GREEN for each behaviour change.
- `make check`.
- `make acceptance` once before your final commit, under the lock, in one guarded command. If a
  test fails, re-run the whole `make acceptance` and report both runs.
- Design references and review captures for the places you change:
  `cd docs/design && pnpm run contrast && pnpm run screenshots` (mirrored byte for byte), and
  `cd apps/web && pnpm run review-screenshots`.

## Report
Write the full report to `.superpowers/sdd/l0-sprint-tasks/task-6dC-report.md`: each bullet with
its tests, the CV decision and its reason, the connection change, the carried items, and RED
then GREEN evidence. Then reply with only the short contract.
