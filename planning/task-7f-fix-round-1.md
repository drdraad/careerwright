# Task 7f first half, fix round 1 (the only one, R16)

You are a fresh implementer fixing Task 7f's first half (the school-leaver option pack 0.3.0,
unpublished, and its session package). Worktree `/home/user/careerwright-wt/7f`, branch
`wt-7f`, head fc5b8f5. Work and commit only there.

## Read first (all in `/home/user/careerwright/planning/`)
`env-cloud.md`, `implementer-contract.md`, the review `task-7f-review.md` (all of it),
`task-7f-report.md` (what was built), `task-7f-dispatch.md`, ADR 0011. Kept page bodies:
`/home/user/careerwright/var/evidence/corpus/<slot>/` (via the `var` link). The UCAS re-fetch:
`task-7f-fetch-output-c12-date.json`.

## Fix now (pack 0.3.0 is unpublished: change it in place and re-pin; 0.1.0 and 0.2.0 never change)
1. **I1 (truth):** the Lifelong Learning Entitlement loans (`funding:F12`,
   `funding:F12.maintenance`) carry their page's age rule ("You must be under 60 on the first
   day of your course to apply for a Tuition Fee Loan", offsets 55234–55319 of F12's body), or
   say it is unknown with its reason for the maintenance loan if the page states it only for
   the Tuition Fee Loan.
2. **I2 (truth):** every claim's excerpt holds its deciding words: `F04.rule_age` must include
   "aged 16 to 24"; `F06.rule_residency.three_years` must include the date that separates the
   two regimes. Widen each excerpt minimally (still a span of the kept body). Check every
   other claim the same way by script: a rule's deciding number, date or age inside its own
   excerpt.
3. **I3 (truth):** the 16 to 19 Bursary Fund is not a "grant" unless a page says it is never
   repaid. Use the instrument kind that matches what the page states, or keep it out of
   support until a page says so; planning must never count it as support on an assumption.
4. **I4 (the product owner's session package):** rewrite the package in plain words
   (CLAUDE.md "Talking to the user"): no field names, offsets or internal codes in what they
   read (put references in a footnote column if needed); drop or rephrase rows a page can't
   answer (the "not_assessed" award-state rows, Q62 and Q79 "(no claim)"), so no row invites a
   "no" that blocks a record for a reason no page could settle. Keep question numbers stable
   only within this unpublished version (session 2's numbers are untouched).
5. **The UCAS date (truth):** the re-fetch located "13 Jan" in the 2027-entry section beside
   the step headings. Say exactly that in the manifest and the package (found beside the
   steps; which step it belongs to and its year not shown in the excerpts), and add one row
   asking the product owner to read the date on UCAS's page at the session. Don't enter a
   value.

## List (not now)
The review's Minors except the UCAS one: the final review.

## Then
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH). Rebase onto
`claude/confident-ramanujan-ux3saw` at the end (another implementer is fixing acceptance in the
main tree; resolve as R15 says). Append "Fix round 1" to `task-7f-report.md`.

## Hard rules
Edit/Write for every source change (no sed, no heredocs that write files; the project's own
generators like `tools.school_leaver_pack` are fine). No web requests, no live calls, no
subagents, never start Docker, never read `.env` or print an environment value, never push.
Never stage `var` or a page body. Commit messages end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

Reply with the short contract and your head SHA.
