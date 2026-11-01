# Task 9 — capability model, protected gates and outcomes: dispatch notes (BASE 4516de8)

The brief, `task-9-brief.md`, is your requirements. Its "Task 9" section is the task; its
preamble holds the Global Constraints, Environment facts and Standing rulings. These notes
add what the brief cannot know.

## What earlier tasks left you

- **The option pack** (Task 7b, ADR 0011) is `nessa.catalogue.option_pack`. Load it only
  through `load_pack("0.1.0")`, which checks the pin.
  - **ADR 0011 is the format contract.** Read decisions 2 (claims and occurrences), 9 (two
    statements of one value), 13 (one declared shape per field) and 14 (the partial-record
    rule).
  - **Every record is `proposed`.** The reviewed version is Task 7c's, after session 2. So
    every readiness result this task can compute from the pack is qualified (OPTN-09, R9).
  - **Skill rows are pack-local** (`pack:<target>:<row>`, decision 10). Every outcome level
    is null until this task's rubrics. Requirement rows carry `kind`, `importance` and
    `gate` (null means judged ungated).
  - **The case types you need are real:** P04's registration gate (C08 nursing, and C03's
    misleading "Adult Nursing" title with "No formal qualification"), introductory courses,
    teaching without assessment, and `unsupported` topic-mention outcomes.
- **Pack 0.1.0 is frozen.** Never edit its file or its pin. If your domain models need a
  field the format lacks, stop and report it as a concern: a format change is a new pack
  version, and the controller rules on it.
- **SourceClaim spans** come from Task 7 (`nessa/evidence`). The pack's claims carry the
  same value, span and excerpt.
- **The ESCO taxonomy** is in `nessa/catalogue`, from the pinned release.

## Rulings for this task

1. **Exemplars.** The pack's job postings are not the user's exemplars. The spec's zero to
   three full-text exemplars per target are user-supplied (spec lines ~489 and ~497).
   - The pack's postings are job-board pages (A6, excerpts only). Their requirement rows
     enter a target's matrix as pack rows, each with its claim, source, date and review
     state.
   - Never count those rows as full-text exemplars, and never claim a full-description
     employer sample.
2. **The module.** Put the capability model in its own domain module (Global Constraint 3,
   plan section 3; for example `nessa/capability`), not inside `nessa/catalogue` and not as
   empty layers.
   - Add any vendor or SQL adapter to `tests/architecture/test_boundaries.py`.
   - Propose the CLAUDE.md layout wording in your report. Do not edit CLAUDE.md.
3. **No live model call.** Any model-backed proposal (for example, mapping an outcome span
   to an observable task) is tested with the offline test double only. Scoring the live path
   on real course pages is Task 10's (TEST1-13). If you add a run kind, it is a `RunTask`
   (ADR 0006) and its spend scope is declared but unused. Say whether DBOS
   `application_version` must change (it changes only when a workflow's step sequence
   changes).
4. **The pack's references.** If your loader relies on `target_ids`, `target_id`,
   `source_id` or `source_ids`, check them at load time, as your loader's own requirement.
   This was parked as Task 7b's M3. Ledger the pointer.
5. **R11 and R12 still apply** (from Task 7b until session 2). A refactor or hardening that
   no failing check, reproduced defect or Global Constraint requires goes in your report for
   the final review.

## Rules

- **Edits:** Edit and Write for every source change. Never use sed, awk or heredocs to
  change a file.
- **Secrets:** never read `.env` or NESSA_HOME.
- **Live calls:** none, no page fetch, Adzuna or Meta.
- **Git:** never push, merge or tag.
- **No subagents.**
- **Test first:** write each test before its code, and record the RED run.
- **After an API change:** run `pnpm run generate` in `apps/web`, then commit the client.
- **Checks:** `make check` must pass. Run `make acceptance` once at the end.
- **Human gates** stay "not run — requires human" (R2).

## Report

Write the full report to `task-9-report.md` in this directory. Then reply with only:
status, commits, a one-line test summary, and concerns.
