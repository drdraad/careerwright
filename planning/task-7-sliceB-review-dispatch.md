# Task 7 slice 7B — task review (two reviewers, split by path)

You review slice 7B of Task 7 for Nessa L0: reference data and AI evidence. Follow
`reviewer-contract.md` in this directory exactly: its method, calibration and output.

All inputs are in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`.
- **Requirements:** `task-7-brief.md` (Task 7's card, Global Constraints and standing rulings),
  `task-7-slices.md` (section "Slice 7B") and `task-7-sliceB-dispatch.md` (the controller's
  dispatch, including R6-1).
- **The implementer's report:** `task-7-sliceB-report.md` (unverified claims).
- **Your package:** named in your dispatch message. The other package covers the rest of the
  slice; inspect it in git only where your named risks depend on it.
- **Plan v1.2 rulings** (`docs/plan/l0-sprint-tasks.md`), which apply to your calibration:
  - **R11:** a linguistic finding is a defect only when a probe, fixture or corpus page
    reproduces it; a hypothetical form is a Minor known limit.
  - **R12:** a hardening that no failing check, reproduced defect or Global Constraint
    requires is a Minor for the final review.
- **Ignore** the controller's docs commits 12190cf, 3ea3a96 and a781189. They are not in your
  package.

## Reviewer A: pay, salary floor, UK SOC, datasets, R6-1, web

Package: `review-df44221..04f95cf-A-pay.diff`. Named risks, one focused check each:

1. **Honesty of "applied".** The You chapter's hint now says the salary floor is applied.
   The implementer says the floor removes no slate suggestion in L0, because only a reviewed
   UK SOC mapping can remove one and none exists before H-10. Do the words, the counts and
   `limits_not_applied` say exactly what happens? A floor shown as applied that removes
   nothing silently is a GC6 honesty defect.
2. **Unknown and predicted pay are never below the floor.** Advertised pay is read as gross.
   Periods are never assumed; Adzuna adverts state no period. Gross, period and source stay
   distinct (spec line ~328). Modelled ASHE pay stays distinct from advertised and predicted
   pay (JOB-05).
3. **ASHE use, against spec section 7 (lines ~324–342):**
   - no regional or broad-SOC estimate is relabelled as city-level;
   - small cells are handled, and reliability is carried;
   - no percentile is averaged across a many-to-many mapping;
   - the rule "below the floor only when P90 is below it in every region of the person's
     cities" is applied as stated.
4. **UK SOC 2020 crosswalks:** unresolved alternatives are explicit, and nothing is assigned
   a precise ASHE salary through an ISCO group (spec line ~342).
5. **Datasets (R7):** each is pinned by URL, version and hash, fetched by `make setup` or
   `tools.datasets` and never committed, and recorded with its licence and attribution. The
   ILO file comes from the lead author's GitHub repository, pinned by commit. Judge only
   whether its pinning and hash check are sound.
6. **R6-1:** image extensions are never read as an email TLD in either pattern, and real
   addresses are still caught.

## Reviewer B: AI evidence, AI Resilience records, reference store and API

Package: `review-df44221..04f95cf-B-ai-evidence.diff`. Named risks, one focused check each:

1. **AIR1-02 and AIR1-04:**
   - a model proposal can only be a `proposed` record;
   - a record publishes only when an accountable reviewer's recorded decision passes the
     publication checks;
   - no agent path can publish one;
   - L0 publishes no real record (H-10), so every real role is unscored.
2. **The labelled fixture record:** it is conspicuously labelled, appears in the fixture
   workspace only, and never fills a live field.
3. **The lower-bound filter and unscored state:** unscored is visible by default in
   exploration. The filter keeps only reviewed ranges whose lower bound passes, and never
   treats unscored as failing or as zero. Exposure-only evidence shows with resilience
   unscored (AIR1-03, AIR1-07, AIR1-11, TAX1-07).
4. **Migration r0027:**
   - forward-only, as a new file;
   - CHECKs on state columns;
   - RLS on every new table;
   - least-privilege grants;
   - the API cannot write a published record.
5. **The reference API:** an error never echoes request input, and the generated client
   matches the API.
6. **ADR 0010 and the register:** each row the slice closes is true of the code, and the
   human gates (H-10, widened to UK SOC mapping reviews) are "not run — requires human",
   never passed.

## Both

- Read-only.
- Never read `.env` or NESSA_HOME.
- No live calls.
- No subagents.
- Do not compose self-harm or distress text.

Write your full report to `task-7-sliceB-review-A.md` or `task-7-sliceB-review-B.md`. Then
reply with only your two verdicts and your counts of Critical, Important and Minor issues.
