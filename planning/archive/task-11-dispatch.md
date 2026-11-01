# Task 11 — offerings, funding, monthly compiler and ledgers: dispatch notes (BASE: HEAD at dispatch)

The brief, `task-11-brief.md`, is your requirements. Its "Task 11" section is the task; its
preamble holds the Global Constraints, Environment facts and Standing rulings. These notes
add what the brief cannot know. This is the last task before review session 2, so its
finish, the session 2 package, matters as much as its code.

## What earlier tasks left you

- **The option pack** (Task 7b, ADR 0011): `nessa.catalogue.option_pack`. Load it with
  `load_pack("0.1.0")` only. It is frozen: never edit its file or its pin.
  - **Shapes (decision 13):** money; rates with `repayable` true, false or null; pay; ISO
    dates and months; deadlines; durations, where `typical` is never bounds and `unbounded`
    means a stated "no end"; schedules; instalments.
  - **Records:** LearningOption, Offering and FundingInstrument records carry
    `review_state` (all `proposed`) and their claims. Options carry `entry_requirements`.
    Two disagreeing statements leave a field unknown (decision 9).
  - **The partial-record rule** is in decision 14.
  - **The package generator** is `tools.option_pack_files`, with drift tests. Question
    numbers Q1–Q344 are stable, because Task 7c applies answers by number.
- **The capability model** (Task 9, ADR 0012): `nessa/capability`.
  - **Readiness states** include `not_yet_assessed` and `insufficient_coverage`, with the
    partial-sketch qualification `missing_outcome_level`.
  - **Every pack outcome level is null in 0.1.0**, so no pack option counts towards
    numeric readiness until Task 7c. P01's real option set is a partial sketch on that axis:
    say so wherever it shows.
- **Carry-forward:** read `carry-forward-task-11.md` in this directory.

## Rulings for this task

1. **The module.** Put the compiler, ledgers and checker in a planning domain module
   (Global Constraint 3, for example `nessa/planning`). Money is integer GBP minor units
   (`Money` ≥ 0, `SignedMoney` for economic cost). Unknown money is null, never 0. Propose
   the CLAUDE.md layout wording in your report.
2. **No live call.** Scoring the live path on the funding pages is Task 12's (TEST1-13).
   DBOS `application_version` changes only if a workflow's step sequence changes; say
   whether it does.
3. **The session 2 package** is agent preparation (R2, R10). Assemble one agenda,
   `docs/reviews/session-2.md`, that fits about 2½ hours (150 minutes), with each part's
   minutes and a record sheet. Every item is "not run — requires human". In order:
   1. **H-13, the formative comprehension session (30 minutes).** Use existing captures or
      Storybook stories of the fixture route comparison and the TRACE-01 ledger, the three
      questions (the cost shown, what "conditional readiness" means, what is uncertain) and
      a record sheet. Any dangerous misunderstanding becomes a Sprint 7 scope input.
   2. **H-01 for Sprint 2 (about 25 minutes).** The You chapter and the slate at 1440 px and
      390 px, as screenshots from `pnpm run review-screenshots`. Test scanning,
      understanding and choosing, with questions and a record sheet. Follow the earlier
      visual packages in `docs/reviews/sprint-2/`.
   3. **H-07, the existing pack package's parts 1 and 2 (about 55 minutes).** Part 3, the
      job rows, is optional and marked "Task 8 may take these".
   4. **H-07, the checker's result on P01's real option set (about 10 minutes):** yes/no
      questions, each field beside its span.
   5. **The capability reference and proposed outcome levels (about 20 minutes).**
      - The reference: rubrics, required levels, crosswalks and gate types.
      - The levels: proposed for the pack's outcomes under Task 9's rubrics, each beside its
        span. They are an agent's proposals in the package only, never written into pack
        0.1.0. Task 7c publishes the reviewed levels.
   6. **A decision sheet (about 10 minutes):** the provisional R6 decisions as plain yes/no
      questions. Include ADR 0012's, among them the "with help" cap, N6 and M4, and any of
      your own. The controller adds any it still holds.

   Generate the new question sets with `tools.option_pack_files` or a sibling tool, with
   drift tests. Give each new set its own numbering (for example `T` and `R` prefixes), so
   Q1–Q344 never move. If the parts cannot fit 150 minutes, say which you cut and why.
4. **R11 and R12 still apply** until session 2.

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
- **Human gates** stay "not run — requires human".

## Report

Write the full report to `task-11-report.md` in this directory. Then reply with only:
status, commits, a one-line test summary, and concerns.
