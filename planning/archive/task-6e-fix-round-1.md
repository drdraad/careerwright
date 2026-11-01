# Task 6e, fix round 1 (the only one, R16)

You are a fresh implementer fixing Task 6e (research this role, the synthetic school leaver,
session W2's package). Main tree `/home/user/careerwright`, branch
`claude/confident-ramanujan-ux3saw` (head after 8d0191d). Nothing else runs beside you.

## Read first (all in `/home/user/careerwright/planning/`)
1. `env-cloud.md` (Node 24 on PATH, checks with the Adzuna variables unset, Docker down).
2. `implementer-contract.md`.
3. The review: `task-6e-review.md`, all of it.
4. `task-6e-dispatch.md` (still binds: no live calls, no web requests) and `task-6e-report.md`.

## Fix now (each with a test that fails before the fix, except the documents)
1. **I1 (truth):** copies of one advert must count once. The copy fingerprint must not rest
   on the title's first occurrence; page headers and navigation must not make two copies
   differ (compare the advert's body text around the title, or another rule you justify in
   ADR 0009/0015). Two subdomains of one registrable domain are one source. Pin the
   reviewer's probe (identical bodies on two boards → not found).
2. **I2 (truth):** pages read for role research never count as job sources in the Jobs
   chapter (`evidence/store.py:476-478`, `acquisition.py:723`); its empty-state reason stays
   true when no job search ran.
3. **I3 (truth, R5):** `make live-role-research` ledgers the paid model call as soon as it
   returns, before any page read, so a failed read never leaves a paid call unrecorded.
4. **I4 (truth):** session W2's "on no list" persona must hold a title that is on no list:
   not an ESCO label, not in the ONS coding index, not an option pack target. Check it
   against the pinned data in code or a test, and say how in the package.
5. **M1 (truth):** hidden text (`display:none`, `hidden`, `<noscript>`, `<template>`) never
   counts as visible; tests for those, the left word boundary, punctuation and apostrophes.
6. **M2, M3 (truth):** "Titles no list holds" lists only titles no list holds; a model's idea
   made a target keeps its origin's words, never "Your target, in your words".
7. **M6 (CLAUDE.md: receipts never carry model output):** `read_role_pages`'s plaintext
   receipt holds no model-proposed URL or page quote.
8. **M7 (truth):** "nothing else about you".
9. **M8 (synthetic always labelled; no internal codes):** Maya named as made up in the
   package; drop "P02 from the test pack".
10. **M9 (a true evidence record):** say in the live tool's notes and the report that the live
    run reads pages in-process, not through the restricted worker's boundary; quote the
    Makefile's `TITLE` safely.

## List (not now)
M4, M5 (a session W2 question: should research sit beside the role in the You chapter?),
M10, M11 (Task M).

## Then
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` after each change. Docker down:
integration, acceptance, Playwright not run; say so.

## Hard rules
Edit/Write for every source change (no heredocs or one-off scripts that write files; the
generators are fine). Explicit pathspecs. No web requests, no live calls, no subagents, never
start Docker, never read `.env` or print an environment value, never push, never write
distress or self-harm text, pnpm only. Disclose every changed test input or assertion. The
register last. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
Append "Fix round 1" to `task-6e-report.md`; reply with only the short contract.
