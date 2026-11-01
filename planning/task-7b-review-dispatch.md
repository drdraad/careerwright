# Task 7b — task review (one reviewer)

You review Task 7b for Nessa L0: the England option pack, curated and labelled from 33 real
pages, with an early accuracy read and the session 2 package. Follow `reviewer-contract.md`
in this directory exactly: its method, calibration and output.

All inputs are in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`.
- **Requirements:** `task-7b-brief.md` (the task card, Global Constraints, standing rulings)
  and `task-7b-dispatch.md` (the controller's dispatch notes: rights, names, live-call rules).
- **The implementer's report:** `task-7b-report.md` (unverified claims, including its rule
  incidents and its reviewer skip list).
- **Your package:** `review-5b33f6b..1c4bc07.diff` (BASE 5b33f6b, HEAD 1c4bc07, 4,092 lines).
- **Rulings that apply to your calibration** (`docs/plan/l0-sprint-tasks.md`):
  - **R11:** a pipeline or linguistic finding is a defect only when a fetched page, probe or
    fixture reproduces it; a hypothetical form is a Minor known limit.
  - **R12:** a hardening that no failing check, reproduced defect or Global Constraint
    requires is a Minor for the final review.
- **You may read** the privately kept bodies in the gitignored `var/evidence/corpus/`
  (read-only) to check spans. Never read `.env` or NESSA_HOME.

## Named risks, one focused check each

1. **Rights per page.** Each slot's class and the terms it relied on match the session 1
   policy (A1–A7 in `docs/reviews/session-1.md` Part A and `corpus/README.md`). Job boards
   (A6) are hash and excerpts only. A page not clearly within a class stays "pending human
   rights review" (C08). A body is kept only where its class permits.
2. **No unpermitted body in git.** Check `git ls-files` at HEAD and the whole range, not
   only the diff: no page body, no excerpt over the stated limit, no
   `~$ssa_Local_Development_Plan.docx`.
3. **Names.** Check the implementer's OI-13 list (C09, J16) for completeness across the pack,
   `corpus/manifest.json` and `docs/reviews/session-2-option-pack-questions.md`. Structured
   contact names, emails and phone numbers appear nowhere committed.
4. **Labels with spans.** Every labelled value cites a claim with value, span and excerpt, or
   says why it is unknown. Spot-check at least 10 claims across job, course and funding pages
   against the kept bodies or the excerpts' own located text. Two statements of one value
   stay unknown (ADR 0011 decision 9).
5. **Split before the read (OI-09).** Template families and splits were assigned before the
   accuracy read ran, the read refuses holdout pages, and no fix (including `7ede59e`) was
   made from a holdout page. Use the commit order and the code, not the report's word.
6. **The pack format.** A schema, a validator and the pin check run in `make check`. The
   format is boring and versioned enough for Tasks 9 and 11 to load through domain models.
   Pack 0.1.0 was changed after its first commit (`b38e462`), while ADR 0011 says a committed
   version never changes. Judge whether that is honestly recorded and harmless (unpushed, no
   consumer), or needs a new version.
7. **Nothing synthetic in the pack**, and the validator refuses it.
8. **The accuracy read.** It covers the deterministic path only, is labelled "unreviewed
   labels, development split", and gives its denominators. Its counts match what the tool
   computes. `7ede59e` is a reproduced fix (J01, J12) with a test that failed first. J19
   changing from correct to missing is honestly reported.
9. **The session 2 package.** It is complete for the H-07 label review (every labelled value
   asked beside its span) and usable by a person. It has 314 questions (about 80 minutes)
   inside a session of about 2½ hours that also holds the H-01 Sprint 2 design review. Judge
   whether its "Answer these first" list is a sound cut, and say what it leaves out.
10. **Live calls and pacing.**
    - **Ledger rows 34 and 35:** do the purposes name the right slots? Row 35 says "corpus J03"
      but filled J02, J03 and J07. Row 34 says J03 and filled none.
    - **Pacing:** the report says same-host fetches ran faster than the manifest's 5-second
      limit, because `tools.corpus` paces within one process only. Judge whether a Global
      Constraint or a reproduced defect requires a fix in this task, or whether it is R12.

## Rules

- Read-only.
- No live calls: no page fetch, no Adzuna, no Meta.
- No subagents.
- Do not compose self-harm or distress text.

Write your full report to `task-7b-review.md` in this directory. Then reply with only your
two verdicts and your counts of Critical, Important and Minor issues.
