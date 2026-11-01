# Review: Task 6d slice C, the real role beside ESCO

You review the last slice of Careerwright L0's Task 6d, in one of two halves (your half is named
in your prompt). It was built in the main tree on `l0-local-release`: commits 51ca593..8292c6a
(bb5045f, 0cedc22, 65750d8, 3055e92, e40a846, dc68d79, 561f9f2, 39d142c, a9dbe67, 8292c6a;
migration 0039). It adds optional seniority and industry beside a title, the product owner's
ESCO research's three fixes (ESCO's list named as ESCO's; "not part of my job"; the unexpected
connection made "always a plain line", the product owner's answer of 1 November 2026), defers
the pasted CV, screens every typed answer (support-policy-10), and moves the title panel's
"Keep it as my job title" up on a phone.

A new product owner direction binds the review too (1 November 2026): "Many users will be final
year school students who have never had a job before." Nothing this slice adds may presume a
job.

## Read first (paths from `/Users/darianraad/Code/careerpathoptimizer`)
1. `.superpowers/sdd/l0-sprint-tasks/reviewer-contract.md`, including its calibration and the
   R11 carve-out.
2. The brief, `task-6d-brief.md` (the Task 6d card), and the dispatch, `task-6dC-dispatch.md`
   (its "Decisions that bind you" are the controller's rulings; the product owner's answers are
   quoted there).
3. The implementer's report (unverified claims), `task-6dC-report.md`. Judge its decisions and
   concerns:
   - the connection built as a plain line by removing the rule that singled one suggestion
     out, with its API fields, the web's mark and its evaluation checks: is anything left that
     reads as a revelation, and did removing the fields break a consumer?
   - the CV paste deferred, with four reasons: are they sound against the dispatch's bar?
   - acceptance: run 1 failed (a phone first-screen check, fixed; two still-world checks), run 2
     failed at setup (an unhealthy acquisition container), run 3 passed. Do the run 1
     still-world failures point to a real defect the fix didn't touch?
   - the export lacks seniority, industry and the marks; the interviewer doesn't ask for
     seniority; `CLAUDE.md` still lists "an unexpected connection" among revelations.
4. The diff, `.superpowers/sdd/l0-sprint-tasks/review-51ca593..8292c6a.diff` (5,535 lines;
   generated client, lockfiles and images excluded). Read your half's files in full, the rest as
   needed.
5. As needed: ADR 0015 (decision 4), ADR 0007 (decision 14 and the support policy), slice B's
   last re-reviews (`task-6dB-rereview-2-design.md`, `task-6dB-rereview-2-app.md`), the
   school-leaver walk (`audit-no-job-yet.md`), and `CLAUDE.md`'s discovery and support
   invariants, the sentence rule and "The experience".

## Half A: design and the person's experience (`design`)
- The web: seniority and industry fields, "not part of my job", ESCO's list's words, the plain
  line for shared skills, the moved "Keep it as my job title", the support panel on every typed
  answer.
- Does each sentence say what Careerwright did or checked, never what a list contains? Plain
  words, ESCO explained or named plainly the first time.
- Does any new element presume a job, or leave someone who skipped the job title with a dead
  end, "your job" wording or an empty skills panel that reads as a failure?
- Phone first screen: the decision stays on it. Keyboard focus and screen-reader names for the
  new controls. Is it a world answering the person (`CLAUDE.md`, "The experience")?

## Half B: the app, the truth and the tests (`app`)
- The backend: the new fields and their storage (migration 0039: forward-only, row-level
  security, CHECKs that repeat the rules), "not part of my job" as a display state that is never
  evidence and never used for suitability or readiness, matching that ignores seniority and
  industry, the connection's removal, the support policy's change (recomputed, never stored,
  nothing used for suitability; tests use the existing fixtures only), and the CV deferral's
  records.
- Every consequential write takes an expected version and an `Idempotency-Key`; no response
  echoes request input; R11 facts with exhaustive maps.
- Tests: would each fail without its code? Disclosed test changes, including removed
  evaluation checks.

## Rules
- Read-only. Don't edit or commit. Read the slice's code with `git show 8292c6a:<path>`.
- `make check` and `make acceptance` passed (the implementer's runs); don't re-run suites. One
  focused fast test is fine for a specific doubt. No integration tests.
- No web requests, no live calls, no Docker, no browser, no subagents. Never read `.env`,
  `~/.careerwright` or `~/.nessa`. Never write distress or self-harm text.

## Output
Write your review to `.superpowers/sdd/l0-sprint-tasks/task-6dC-review-<half>.md` (`design` or
`app`), in the contract's format. Then reply with at most 10 lines: counts by severity, each
Critical or Important item in one line, and the path.
