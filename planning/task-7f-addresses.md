# Task 7f, step 1: the school-leaver pages to fetch

Proposed by the Task 7f implementer, 2026-11-01. No page was fetched. Every address below
comes from the pinned pack's sources (F02's GOV.UK guide family) and my
knowledge of the sites; **the controller checks each before the run**. Where an address
is wrong or a page doesn't say what its row needs, swap in the address that does (the
alternates column gives my next guesses) and edit the plan file to match.

## The command (one process, one fetcher, one pacer, through the session proxy)

From the worktree's `backend/` (wt-7f, rebased on the integration branch, with the proxy mode):

```
cd /home/user/careerwright-wt/7f/backend && \
  uv run --locked python -m tools.corpus \
    --batch /home/user/careerwright/planning/task-7f-fetch-plan.json \
    --proxy "$HTTPS_PROXY" --proxy-ca /root/.ccr/ca-bundle.crt \
  > /home/user/careerwright/planning/task-7f-fetch-output.json
```

- The plan: `/home/user/careerwright/planning/task-7f-fetch-plan.json` (10 pages, checked
  offline by `load_batch`; every entry is validated before the first request).
- The proxy flags apply to every page; each page's record says `"via_proxy": true,
  "address_checked": false`. All pages are on `www.gov.uk` (9, paced 5 seconds apart) or
  `www.ucas.com` (1): about a minute. Run it once; if a page must be re-fetched, wait at
  least 5 seconds after the last run.
- Kept bodies go to `var/evidence/corpus/<slot>/` (the worktree's `var` is the main tree's).
  GOV.UK bodies are kept; UCAS keeps hash and excerpts only.
- The output holds each page's record (URL, final URL, time, status, hash, rights status,
  retention, route) and the `locate` hints' counts and offsets. For C12 (UCAS, body not
  kept), each hit also carries up to 100 characters either side, so step 2 can cut the
  deadline's minimal excerpt without a second fetch. Nothing in it is a page body. A page
  that fails is recorded with its failure; please pass the whole output back as it is.
- The `locate` strings are hints, not labels: a count of 0 says the page probably lacks
  that wording, not that it lacks the fact.
- After the fetch, I propose new addresses for any page that fails (your answer, 2026-11-01).

## The pages

Rights: `www.gov.uk` is listed in `sources.json` as class `govuk` (session 1 line A1), with
the OGL footer terms read 2026-10-28, so its pages need no `rights_class`: the pipeline
records "govuk: \"All content is available under the Open Government Licence v3.0, except
where otherwise stated\" (page footer, read on https://www.gov.uk/guidance/free-courses-for-jobs)
(read 2026-10-28)". Step 2 confirms the footer on each kept body.

Splits follow the pinned rule (`policy.holdout_split`): a family keeps the split it first
got; a new family is numbered among its class's groups by its lowest slot, and groups 2, 5,
8, ... are holdout. Funding groups so far: 1 govuk-detailed-guide (development), 2
govuk-mainstream-guide (holdout), 3 skills-for-careers-page (development). Course groups:
1 netcom, 2 leeds-city-college (holdout), 3 reed-course-details, 4 ncs-find-a-course, 5
uom-undergraduate-course (holdout), 6 find-an-apprenticeship-vacancy; reed-job-details
keeps the job class's development split. So the next new course family is group 7
(development) and the one after it group 8 (holdout). Every split below is assigned now, before any read.

| Slot | Address (proposed) | What it must state | Class and terms relied on | Family, split | Alternates if wrong |
|---|---|---|---|---|---|
| F04 | https://www.gov.uk/become-apprentice | That an apprentice doesn't pay for their training (fixes `offering:C09`'s unknown fee) | `govuk`, the manifest's OGL terms | govuk-mainstream-guide, holdout | https://www.gov.uk/become-apprentice/pay-and-conditions; the GOV.UK apprenticeship funding rules page that says an apprentice must not be asked to pay towards their training (a `/guidance/` page is govuk-detailed-guide, development) |
| F05 | https://www.gov.uk/student-finance/new-fulltime-students | Tuition Fee Loan: the most it lends a year and that it is paid straight to the university or college. Maintenance Loan: the amounts (living with parents, away, London) and that it is paid into the student's bank account each term | `govuk` | govuk-mainstream-guide, holdout | — |
| F06 | https://www.gov.uk/student-finance/who-qualifies | Residency (UK national or settled status, living in the UK for 3 years before the course) and any age rule (none for the Tuition Fee Loan; the Maintenance Loan's age 60 rule) | `govuk` | govuk-mainstream-guide, holdout | https://www.gov.uk/student-finance (overview) |
| F07 | https://www.gov.uk/repaying-your-student-loan/what-you-pay | How the loans are repaid: the plan for courses starting from 1 August 2023 (Plan 5), 9% over its threshold, when it is written off | `govuk` | govuk-mainstream-guide, holdout | https://www.gov.uk/repaying-your-student-loan/which-repayment-plan-you-are-on |
| F08 | https://www.gov.uk/advanced-learner-loan/what-youll-get | That the Advanced Learner Loan is paid straight to the college or training provider (the rule the loan now follows), and how much it lends | `govuk` | govuk-mainstream-guide, holdout | — |
| F09 | https://www.gov.uk/advanced-learner-loan | How the Advanced Learner Loan is repaid (from earnings over a threshold), which F02's eligibility part doesn't state | `govuk` | govuk-mainstream-guide, holdout | https://www.gov.uk/advanced-learner-loan/repaying-your-loan (if that part exists) |
| F10 | https://www.gov.uk/1619-bursary-fund | The 16 to 19 Bursary Fund: what it pays (the vulnerable-group bursary of up to £1,200 a year; discretionary bursaries), that it is not repaid, and who pays it (the school, college or provider) | `govuk` | govuk-mainstream-guide, holdout | https://www.gov.uk/1619-bursary-fund/what-you-could-get |
| F11 | https://www.gov.uk/1619-bursary-fund/eligibility | Its age rule (16 to 19 on 31 August of the year the course starts; the 19+ continuing-learner case) and residency rule | `govuk` | govuk-mainstream-guide, holdout | — |
| C11 | https://www.gov.uk/government/publications/introduction-of-t-levels/introduction-of-t-levels | One T Level, as a Level 3 option for a school leaver: what it is (a 2-year course for 16 to 19 year olds, equivalent to 3 A levels), its industry placement (at least 45 days), its hours, entry and what it leads to. Replaces the Leeds City College page (that host is blocked; your answer, 2026-11-01). No provider, start date or fee is expected on it: those stay unknown with their reason, never 0 | `govuk`, the manifest's OGL terms | govuk-html-publication (new), development (course group 7) | https://www.gov.uk/guidance/t-levels-resources-for-teachers-and-careers-advisers (govuk-detailed-guide, which keeps its development split) |
| C12 | https://www.ucas.com/undergraduate/applying-to-university/undergraduate-key-dates-and-deadlines | The UCAS deadline that applies to the pack's nursing degree (`offering:C08`, The University of Manchester, BNurs Adult Nursing, from September 2027): the equal-consideration date for 2027 entry (most courses, nursing among them) | `other`: UCAS is neither GOV.UK, the public sector, a course provider nor a regulator under session 1, so it stays "pending human rights review" (the policy's line 7), keeping hash and minimal excerpts only; its rights item joins OI-07, not run, requires human; the product owner classes it at the school-leaver session (your answer, 2026-11-01) | ucas-guide (new), holdout (course group 8, since C11's new family is group 7; if C11 moves to an existing family, ucas-guide becomes group 7, development) | https://www.ucas.com/undergraduate/applying-university/ucas-undergraduate-when-apply; UCAS's "key dates" page for 2027 entry, wherever it now lives |

## What step 2 does with them (for the controller's check, not now)

- Records, all `proposed`, dated and span-cited or unknown with a reason: FundingInstrument
  for the Tuition Fee Loan and Maintenance Loan (F05 to F07), the 16 to 19 Bursary Fund
  (F10, F11), and new facts on the Advanced Learner Loan's payment and repayment (F08, F09)
  in the new version only; LearningOption and Offering for the T Level (C11; provider, start, fee unknown with their reason); corrected
  values for `offering:C09`'s training fee (F04) and `offering:C08`'s application deadline
  (C12), each with its span, in the new version only.
- Expected unknowns: student finance amounts for 2027 to 2028 may not be published yet
  (the pages may state 2026 to 2027 only); the T Level page states no provider or fee (then
  unknown, never 0); UCAS may state a date without the year's entry named.
