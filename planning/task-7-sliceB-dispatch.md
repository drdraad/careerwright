# Task 7, slice 7B: reference data and AI evidence (BASE df44221)

You implement the second and last slice of Task 7 for Nessa L0. Slice 7A, the acquisition
core, is complete and reviewed, at commits 8276485..df44221.

## Read first, in order

All paths are in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`.

1. `implementer-contract.md`. It applies in full.
2. `task-7-brief.md`. This is Task 7's card, with the Global Constraints, Environment facts
   and Standing rulings. Read the whole Task 7 section.
3. `task-7-slices.md`, section "Slice 7B". That is your scope. Slice 7A's items are done:
   do not rebuild them.
4. `carry-forward-task-7.md`, the salary floor item. Its other two items were closed in 7A.

## What 7A left you (read in the repository; the brief cannot know these)

- ADR 0009 and `backend/src/nessa/evidence/`:
  - claims and their validation states (`structured`, `model`, and the others);
  - pay as claims in `Money` minor units with period and basis (advertised, predicted,
    unknown; Adzuna's `salary_is_predicted`);
  - the job listing, `GET /v1/workspaces/{id}/jobs`, and its coverage and `empty_reason`.
- JOB-05's open part is yours: modelled pay with ASHE. It must stay distinct from advertised
  and predicted pay.
- The salary floor, `minimum_salary`, is a confirmed hard constraint from Task 6, with gross
  pay and a period; Unknown is never £0. DIV1-07 and DSC-09 say it is "recorded but not
  applied". Now apply it as a hard filter, with counts explaining its effect.
  - Unknown or predicted pay is never treated as below the floor.
  - Keep the gross, period and source distinctions.
- ESCO's pinned, hash-checked release pattern (`make setup`, `var/datasets/`,
  `nessa/catalogue`) is the model for ASHE and the AI-evidence imports (R7): pin the version,
  URL and hash, keep the data out of the repository, and fetch it in setup.
- Session 1's rights policy (`docs/reviews/session-1.md`, line A2) puts ONS under the OGL.
  Record each dataset's licence and attribution.

## Also deliver: one small 7A residual, first, as its own commit

**R6-1** (`task-7a-rereview-6-A.md`). Image file names with `@2x` (`logo@2x.png`) read as
email addresses. Controller ruling: never read an image file extension (png, jpg, jpeg, gif,
webp, avif, svg, ico, bmp, tif, tiff) as an email TLD, in both email patterns (the plain one
and the spaced one).
- Tests: a JSON-LD `logo`, a percent-encoded attribute, `src` and `srcset` each keep the body
  and the path.
- Real addresses at real TLDs are still caught.
- Correct ADR 0009 decision 4's limits.

## Rules

- **Live calls.** No Meta calls in this slice. Downloads only from each dataset's official,
  pinned URL, each hash-checked. Record each URL, version, hash, licence and size in your
  report.
- **Change scope.** Ask nothing you can settle from the spec, plan or code. Record rulings in
  your report, and in an ADR if they are architectural; ADR 0010 is the next number. Keep the
  register rows you close up to date (TAX1-07, AIR1-02/03/04/07/11, JOB-05, DIV1-07 and any
  other), and the runbook.
- **Human gates are never self-certified (R2).** Reviewed UK-SOC mappings and AI-resilience
  publication need an accountable reviewer (H-10). Until one exists, record them as "not run
  — requires human", and every real role stays unscored.
- **Workflows.** DBOS `application_version` is `nessa-l0-1`. Change it if a workflow's step
  sequence changes.
- **Checks.** Run `make check` while you iterate, and `make acceptance` once at the end. Name
  each covering test.
- **File changes** use the Edit and Write tools only: no sed, awk, heredocs, one-liners,
  `touch`, or `rm` of tracked files.
- **Never:**
  - read, print or pass `.env`, META_API_KEY or anything in NESSA_HOME;
  - push, merge or tag;
  - commit `~$ssa_Local_Development_Plan.docx`;
  - touch the agentsolve-* or eigenprompt-* Docker projects;
  - dispatch subagents;
  - edit CLAUDE.md (propose wording in your report instead);
  - compose self-harm or distress example text.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report

Write the full report to `task-7-sliceB-report.md` in this directory. Then reply with only:
status, commits, a one-line test summary, and concerns.
