# Task 7c dispatch: publish the reviewed option pack

Where this fits: Careerwright L0 is mid-build (branch `l0-local-release`). Session 2 (the
product owner's review) is recorded. This task turns its answers into a new, reviewed version
of the England option pack, which Tasks 10, 12, 8 and 13a will pin. It is backend and data
only: no interface work (the interface is being redesigned separately and must not be touched).

## Read first, in this order
1. Your brief (your requirements, with the exact values to use verbatim):
   `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-7c-brief.md`
2. Your contract: `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`
3. Carry-forward from Task 9 (include it in this task):
   `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/carry-forward-task-7c.md`
4. The product owner's record: `docs/reviews/session-2-answers.md` (all of it, including
   "Decisions the product owner added at the end"), with the question sets it answers:
   `docs/reviews/session-2-option-pack-questions.md`, `session-2-capability-questions.md`,
   `session-2-checker-questions.md`, and `docs/reviews/session-2.md`.
5. `docs/adr/0011-england-option-pack-format.md` (the partial-record rule in decision on the
   review order), `docs/adr/0012*` (capability levels), CLAUDE.md "Option pack (ADR 0011)".

## Rulings the brief cannot know (the controller's)
- **The AI-checked answers count.** On 2026-10-30 the product owner ruled: "Yes, make the AI
  count. I overrule the previous requirement." Every answer labelled "checked by AI"
  (Q16–Q344, T1–T36, R1–R58) counts as their own review, the same as Q1–Q15. You still
  decide nothing (R10): you transcribe their record. Keep the provenance honest in each
  record's review note: Q1–Q15 answered by the product owner; the rest checked by an AI and
  adopted by the product owner's ruling of 2026-10-30. Name the product owner as reviewer
  and session 2 (2026-10-29 to 2026-10-30) as the session.
- **Partial records (ADR 0011 governs):** a record becomes `reviewed` only when every one of
  its rows is answered yes. Any "no" or "?" leaves it `proposed`.
- **A "no" answer's value:** where the answer states the correct value and quotes words from
  that same source page, apply it in the new version as a correction, span-cited (verify the
  span against the stored claim or retained body the same way Task 7b's validator does) and
  naming the decision; the record stays `proposed`, because the corrected value itself has
  not been reviewed. Where a "no" or "?" gives no value you can cite that way, the field
  becomes unknown with the review's reason recorded: never keep serving a value the
  reviewer said is wrong, and never invent one.
- **Rule answers (D3–D17):** this task applies only what concerns the pack's records, their
  outcome levels and rights. D-answers that change behaviour elsewhere (for example D8's
  and D10's replacements) are not implemented here: list each, with the task it belongs
  to, in your report.
- Pinned format names stay as written (`nessa-england-option-pack`,
  `nessa-capability-reference`): see CLAUDE.md "Repository facts".
- The earlier version and its pin stay byte-identical; the new version gets its own pin in
  `PINS`, written only through the existing tooling (`tools.option_pack_files`).

## Hard rules
- Change source files with Edit and Write only: never `sed`, `awk`, heredocs or scripts
  that rewrite files (generated outputs written by the project's own tools are fine).
- Stage explicit paths only; never `git add -A` or `git add .`. Never stage or commit
  `answers-2.md`. Never push.
- Never read `.env` or anything under `~/.nessa` or `~/.careerwright`. No live calls.
- Do not touch `apps/web` or `spikes/`. Do not dispatch subagents.
- Run `make check`, and `make acceptance` once before your final commit.

## Report
Write your full report to
`/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/task-7c-report.md`
(include a table: records reviewed / still proposed / excluded, with counts; each
correction applied with its question number and span; every field made unknown and why;
the D-answers carried to other tasks; the new version and its hash). Then reply with only the
short contract.
