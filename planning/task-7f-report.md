# Task 7f report: the school-leaver option pack

## First half (2026-11-01)

**Status: done, waiting for the school-leaver pack session.** Branch `wt-7f` (worktree
`/home/user/careerwright-wt/7f`), rebased onto `claude/confident-ramanujan-ux3saw` (e364ded).

### Commits

1. `da2c8e3` A batch mode for `tools.corpus` (`--batch PLAN`): one fetcher and one pacer
   per run, every entry checked before the first request, a failed page recorded and the run
   going on. `--context N` (at most 100) prints each located span with its neighbourhood.
   `--proxy`/`--proxy-ca` apply to every page of a batch, and each record says `via_proxy`.
2. `d53d4d1` The school-leaver pages labelled; option pack 0.3.0; its session package.
3. `fc5b8f5` The follow-up pages folded into 0.3.0 before any publication (re-pinned in
   place, as the controller allowed).

### What was delivered

- **Pages.** The controller ran three batch fetches through the proxy. 11 GOV.UK pages are
  used, all class `govuk`, bodies kept only in `var/evidence/corpus/`:
  - F04: funding for apprenticeship training (written for employers);
  - F05 to F07: student finance for courses starting before 1 January 2027, and how much
    you repay;
  - F08, F09: the Advanced Learner Loan's other pages;
  - F10, F11: the 16 to 19 Bursary Fund;
  - F12: student finance from 1 January 2027 (the Lifelong Learning Entitlement);
  - F13: which repayment plan applies;
  - C11: the Department for Education's introduction of T Levels.
- **Not used:**
  - The first F04 capture ("Become an apprentice") did not say who pays for training. It is
    recorded in F04's `why`.
  - C12, UCAS's dates page. The first address answered 404; the finder gave the real one.
    It is class `other`, so only the hash and excerpts are kept, and it is pending rights
    review (OI-07). Its located excerpts name "(18:00 UK time) Equal consideration date for
    applications for most undergraduate courses", but not the date. "January 2027" occurs
    nowhere on it. So it adds no claim (`pending_slots`). A re-fetch to locate the date is
    `planning/task-7f-fetch-plan-c12-date.json`.
- **Pack 0.3.0**, pinned `47f968bbad257d854a7636dc4aa4c39533f91d864735233e6fbe36b684334e77`.
  It is 0.2.0 plus 109 span-cited claims, 8 new records and 1 changed record, all
  `proposed`:
  - `funding:F05` and `funding:F05.maintenance`: the two loans for courses starting before
    2027. Each says how it is paid (straight to the university; into the student's bank
    each term), how it is repaid (9% over the threshold, Plan 5), its caps for 2026 to 2027
    and its age and residency rules.
  - `funding:F12` and `funding:F12.maintenance`: the same loans through the Lifelong
    Learning Entitlement. Up to £9,790 per 120 credits and £39,160 in total; up to £15,415
    per course year; repaid over £25,000 a year; written off after 40 years; residency
    counted to the first day of the month the course starts.
  - `funding:F10`: the bursary (at least 16 and under 19 on 31 August 2026; up to £1,200 for
    vulnerable groups; whether it is repaid is unknown).
  - `funding:F04`: apprenticeship training funding (the government pays 100% for ages 16 to
    24 where the employer pays no levy, otherwise 95%, paid to the provider).
  - `option:C11` and `offering:C11`: a T Level (2 years, a placement of at least 315 hours,
    typically 1,100 to 1,300 classroom hours; no provider, start or fee named, each unknown).
  - `funding:F02` gains how the Advanced Learner Loan is paid (to the provider), what it
    covers (fees only), how it is repaid (over a threshold) and its plan (Plan 5). It keeps
    session 2's review record and stays `proposed`.
- **The January 2027 finding, settled:**
  - A course starting on or after 1 January 2027 takes the Lifelong Learning Entitlement's
    loans (F12), which the page says cover "most undergraduate" courses.
  - The nursing degree starts in September 2027, so it falls there if it is one of those
    courses. The page names none, so the pack doesn't assert it.
  - F05's 2026 to 2027 caps are kept for earlier starts. Both regimes have their own
    records, and the session package explains which is which.
- **Still unknown, never guessed (OI-14):**
  - The apprentice's training fee (`offering:C09`): F04 names the government and the
    employer as payers, never the apprentice.
  - The nursing degree's UCAS deadline (`offering:C08`).
  - Both records are unchanged from 0.2.0.
- **Format:**
  - A cap has its own value shape, `limit`, because "up to £9,790" is neither an exact
    amount nor a rate. `format_version` stays 1, since the change only adds to the format.
  - New claim field names take existing shapes.
  - Recorded in an ADR 0011 amendment; the schema is regenerated.
- **Tools:**
  - `tools.school_leaver_pack` builds 0.3.0 from `backend/tools/school_leaver_labels.json`
    and writes the package.
  - The session 2 package is unchanged.
- **Manifest and docs:**
  - `corpus/manifest.json` 0.6.0: 11 new slots, each with `fetch_route` (via_proxy true,
    address_checked false), plus `pending_slots` (C12) and OI-14. Counts are now 11 course
    pages and 13 funding pages.
  - `corpus/README.md`, the OPTN-14 register row and ADR 0011 are updated.
- **Session package:** `docs/reviews/school-leaver-pack-questions.md`, 136 yes/no rows,
  about 34 minutes. Part 1 (112 rows) is everything that changes a route, loans first.
  Rows session 2 already asked are left out. Review: not run - requires human (H-07).

### Checks

- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`, Node 24 on PATH, on the
  final rebased code (fc5b8f5): passed. Backend 2,045 passed, 8 skipped; Vitest 471
  passed; ruff, mypy, Biome, `tsc`, the fixture validator and the client-drift check
  passed.
- The 109 label-against-body checks run where `var` is linked (this machine), and skip in CI
  (R3).
- `make acceptance`: not run (the controller runs it).

### Rulings I made

1. The first F04 capture and C12 add no claim: a page that does not state the value adds
   nothing. Both are recorded in the manifest.
2. Two student-finance regimes, two records each. No record links a loan to a course.
3. The T Level is linked to the bookkeeping target in Leeds only. The page names an
   accounting T Level, and Leeds is where the synthetic school leaver lives.
4. The session package asks every fact of a new record, not only consequential shapes. The
   session is short, and every fact is a value the person will see.

### Gaps

- 0.3.0 has no capability reference of its own. Task 12b needs one, or a check that 0.2.0's
  fits, before it pins the reviewed version.
- No consumer has yet run planning or route search on 0.3.0.
- C12's rights (class `other`) are the product owner's to decide at the session.
