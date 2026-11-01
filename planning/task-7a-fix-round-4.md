# Task 7A — fix round 4 (FIX_BASE dcaac22)

You are a fresh implementer joining slice 7A (evidence acquisition) of Nessa L0 at its fourth
fix round. Three earlier rounds were done by another implementer. Their work is committed on
branch `l0-local-release`, from 8276485 to dcaac22.

Read first, in this order:
1. `implementer-contract.md`, which applies in full.
2. `task-7-brief.md`, slice 7A's card and the Global Constraints.
3. `task-7a-report.md`. Skim 7A and rounds 1–2. Read "Fix round 3" in full, and the proposed
   CLAUDE.md wording.
4. The two re-reviews these items come from: `task-7a-rereview-1-C.md` and
   `task-7a-rereview-4-A.md`.

All paths are in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`.

Every item below is a controller ruling and is fixed now. Tests go RED first. One commit per
coherent group.

## Rights

1. **Obfuscated mailto (round 3 concern). Ruling:** detection decodes HTML entities in
   attribute values, `mailto:` hrefs among them. A detail found there means the body is not
   kept, under a typed `body_not_kept` reason.
   - Test an entity-encoded `mailto:` with no visible address.
   - Remove the limit from ADR decision 4.
2. **R4-1. Ruling:** in normalised text, detection, and the model input's redaction, accept
   optional whitespace around `@` and around the domain's dots. The TLD is letters only. Do
   not guess which elements are inline and which are block.
   - A hit in a kept body means the body is not kept.
   - Test `jane<span>@</span>recruit.example` and `jane@<b>recruit</b>.example`, in a kept
     body and in the model input.
   - Test that an ordinary sentence with " @ " and no domain is left unchanged.

## Money

3. **Pay period suffixes (round 3 concern). Ruling:** a period suffix attached to a number
   reads as that period, never as a refusal. The suffixes are `pa`, `p.a.`, `ph`, `p/h`, and
   the attached per-annum and per-hour forms the reader already knows as words.
   - Magnitude letters (`m`, `bn`) and unknown letters stay refused (`salary_invalid`).
   - Tests: `£30,000pa` and `£14.50ph` read exactly. `£1.2m` and `£30-35k` stay unknown with
     their issue.
4. **The estimate understates (round 3 concern). Ruling:** `acquisition_model_spend` is the
   true ceiling. It is `MAX_EXTRACTIONS_PER_ACQUISITION` × one run's worst case across every
   attempt its retry owner may make, not × one reservation.
   - Compute it with the same functions the reservation uses, so the two cannot drift.
   - The field's description says it is a maximum.
   - Test it against the default run limit on both models.

## Durability and contract

5. **C-1 N1. Ruling:** whenever a recording transaction's result is model-readable, take
   `lock_started_runs` first, before `lock_workspace_records` and before any insert.
   - Correct ADR decision 15's lock-order sentence and the `lock_started_runs` docstring, so
     they say exactly what holds.
   - Add one sentence to the ADR's open items about the pre-existing pattern: `cancel_run`
     locks the workspace row `FOR UPDATE` and then the run's key share. That pattern is
     **not** fixed in this round; it is carried to the final review.
   - Test: a cancel concurrent with recording a kept-body, model-readable page ends without
     a store error. Use an integration test with two connections, as N2's overlapping-runs
     test does.
6. **C-1 N2. Ruling:** the 202 answer of a cancel lists the run IDs whose cancellation it
   requested: the run itself, the started runs, or both.
   - Correct the route's docstring for the finished-acquisition case.
   - Regenerate the client (`cd apps/web && pnpm run generate`) and commit it.
   - Test both shapes.

## Honesty

7. **C-M1's residual. Ruling:** a negator (`not`, `no`, `non-`) up to two words before a
   work-mode word gives `work_mode_unclear`.
   - Test "Not fully remote" and "This is not a remote role".
   - The four round 3 cases still pass.

## Also

- Update ADR 0009, the register rows these change (ACQ-06, MODEL-08, DUR-05 and any
  other), and the proposed CLAUDE.md wording in your report if it changes. Do not edit
  CLAUDE.md.
- Say whether DBOS `application_version` (`nessa-l0-1`) changes. It must change if a
  workflow's step sequence does.
- No live calls.
- Run `make check`, then `make acceptance` once at the end, and name each covering test.
- File changes use the Edit and Write tools only: no sed, heredocs, one-liners, `touch`, or
  `rm` of tracked files.
- Never read `.env` or NESSA_HOME. Never commit `~$ssa_Local_Development_Plan.docx`. Never
  touch the agentsolve-* or eigenprompt-* Docker projects. Never push. No subagents.
- Append your report to `task-7a-report.md` under "Fix round 4". Then reply with the short
  contract: status, commits, a one-line test summary, and concerns.
