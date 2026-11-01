# Task 7b — the England option pack: dispatch notes (BASE: HEAD at dispatch)

The brief, `task-7b-brief.md`, is your requirements. Its "Task 7b" section is the task; its
preamble holds the Global Constraints, Environment facts and Standing rulings. These notes
add what the brief cannot know. Plan v1.2 made this task the next proof of progress: real
evidence, now, ahead of polish (R12).

## What earlier tasks left you

- **The acquisition pipeline** (Task 7A, ADR 0009) is `backend/src/nessa/evidence/` and
  the restricted worker `nessa/acquisition.py`, with `backend/tools/corpus.py` (including
  `--rights-class`, an agent's dated classification).
  - Every fetch goes through `nessa.evidence.fetcher`, which checks the address, robots.txt
    and pacing.
  - Redaction removes emails, phones and contact fields before hashing.
  - Model extraction exists, but no model call is made in this task (below).
- **Reference data** (Task 7 slice 7B, ADR 0010): ASHE, the UK SOC 2020 coding index and
  the AI-evidence files. No UK SOC mapping is reviewed (H-10).
- **Task 7d** fixed the cancellation lock order. CLAUDE.md's Evidence invariant and lock
  order apply.

## Rights (the product owner's own records)

- **The session 1 rights policy**, lines A1–A7 in `docs/reviews/session-1.md` Part A and
  `corpus/README.md`. Classify each page against it and record its class and the terms you
  relied on. A page outside every class, or not clearly within one, stays "pending human
  rights review". Job boards (A6) are reference only: hash and excerpts, never the body.
- **Names**, from the two addenda dated 2026-10-29 in `docs/reviews/session-1.md`.
  - A name in a page's running text may stay in a privately kept body. That is the product
    owner's own answer.
  - A name may also stay in excerpts and claim values on this machine. That one is the
    controller's decision, under the product owner's delegation.
  - Excerpts committed to git are reviewed for names before any push.
  - So list every committed excerpt that holds a person's name in your report, by slot and
    field, so that the pre-push review can find them.
  - Structured contact names, emails and phone numbers are still removed everywhere.

## Rules for this task

- **Live calls:**
  - No Meta call: model extraction on a real page is not run in this task.
  - Real page fetches are allowed under R3 and the policy, through the product's own
    fetcher only.
  - Adzuna requests are allowed only through `make live-adzuna` or the product's adapter,
    within the `live-adzuna` scope's remaining cap (2 of 10 used), each one ledgered. Use as
    few as the slots need.
  - Finding candidate pages with a web search is allowed. Record each page's URL and why it
    fills its slot. Nothing from a search result is evidence until it is fetched.
- **The early accuracy read** (new in the brief) covers the deterministic path only. Label it
  "unreviewed labels, development split". Assign the template families and splits before
  you run it, and never tune on holdout pages (OI-09).
- **R11:** fix a pipeline defect only when a page you fetched reproduces it. Record a form
  you only imagine as a known limit.
- **R12:** a refactor or hardening that no failing check, reproduced defect or Global
  Constraint requires goes in your report for the final review, not into this task.
- **The pack format** is yours to define: a schema and a validator in `make check`. Later
  tasks (9 and 11) load it through their domain models, so keep it boring and versioned.
- **Human gates are never self-certified (R2):** `label_review`, H-07 and rights review
  stay "not run — requires human". The session 2 package is an agent's preparation.
- **Never commit** an unpermitted page body, a synthetic value in the pack, or
  `~$ssa_Local_Development_Plan.docx`.

## Report

Write the full report to `task-7b-report.md` in this directory. Then reply with only:
status, commits, a one-line test summary, and concerns.
