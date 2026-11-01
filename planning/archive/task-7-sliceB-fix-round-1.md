# Task 7 slice 7B — fix round 1 (FIX_BASE 04f95cf)

Two reviews, both Spec ❌, Needs fixes:
- `task-7-sliceB-review-A.md`: pay, the salary floor, UK SOC, datasets, R6-1 and web.
  Important I1, Minor M1–M8.
- `task-7-sliceB-review-B.md`: AI evidence, AI Resilience records, the reference store and
  the API. Important I1–I2, Minor M1–M10.

Read both in full. The items below are the controller's rulings. "A-" and "B-" name the
review. Order: Importants first, then Minors, one commit per coherent group, with tests RED
first. Since your slice, plan v1.2 added rulings R11 and R12 (`docs/plan/l0-sprint-tasks.md`).
Every item below meets them: each is reproduced, spec-required or a GC6 honesty defect.

## Pay and the salary floor

1. **A-I1.** A salary whose `maximum_minor_units` is `None` is open-ended. It gives
   `UNKNOWN`, with a new reason such as `no_upper_amount`, unless its minimum already meets
   the floor, in which case it gives `meets`.
   - Only a stated maximum, or a single amount (`minimum == maximum`), can put a job below
     the floor.
   - In `salary_from`, read a trailing `+` after an amount (`£24,000+`) as a minimum.
   - Correct the test row that locks in the old reading. Add cases for "From £24,000",
     "Minimum £24,000", a JSON-LD `minValue` with no `maxValue`, and `£24,000+`.
2. **A-M6.** Compare modelled ASHE figures with the floor directly, never through
   `StatedPay("advertised", …)`. This way item 1 cannot change the occupation rule. Add a
   test that holds the occupation rule unchanged.
3. **A-M5.** Pay with an unknown basis gets its own reason, `basis_unknown`, not `no_pay`.
4. **A-M4.** Keep each statistic's CV and reliability band from the ASHE "b" tables (the
   median, the percentiles and P90 among them). Expose each beside its own statistic.
5. **A-M3.** `_empty_reason` checks `sources_pending` before `all_below_salary_floor`. Test
   an empty page that is filtered by the floor while sources are pending.

## Honest words

6. **A-M1.** The You chapter's hint says what L0 does. Vacancies whose advertised pay in
   the floor's period is below it are left out; so are suggestions whose reviewed official
   pay is. Nessa says how many, and why the rest were kept. Use the reviewer's wording or
   equivalent.
7. **A-M7.** The slate's floor sentence includes the `meets` count, so its counts add up to
   the pool considered.
8. **A-M8.** Add a Storybook state with a salary floor set. Session 2's design review looks
   at the You chapter.
9. **A-M2.** Correct the stale text:
   - register row DIV1-06;
   - ADR 0007 decision 2: add an amendment note pointing to ADR 0010 decision 8 and
     `salary_floor`; do not rewrite history;
   - `backend/tools/setup.py`'s docstring.

## AI Resilience records

10. **B-I1.** Add a deterministic publication failure, for example
    `exposure_only_evidence`, for a record whose observed families are all exposure types
    (`task_exposure`, `observed_use`).
    - Give the fixture record a third synthetic, labelled family that bears `protection`,
      so it still qualifies the machinery under the rule.
    - `ai_evidence.state` never says `exposure_only` beside a published range: derive it
      from the assessment, or rename it to describe the imported evidence.
    - Add the parametrised case. Correct the AIR1-02 and AIR1-03 text.
11. **B-I2.** Make `origin` load-bearing.
    - A `model_proposal` never publishes, whatever its decision.
    - A reviewer who accepts one enters a `reviewer_entry` record.
    - Test that a `model_proposal` carrying a full decision stays `proposed`.
    - Drop the shape assertions (`"published"`/`"state"` not in `model_fields`). Correct ADR
      0010 decision 7 and AIR1-04 to say exactly what holds.
12. **B-M1.** The reviewer's decision records the bounds it approved. A record whose bounds
    differ from them does not publish. Test it.
13. **B-M2.** A reviewed `null` decision skips the evidence-sufficiency checks and reports
    `reviewed_null`. Test a null with one family.
14. **B-M3 and B-M8.** Synthetic labelling:
    - `synthetic` describes the record, and is false when the role has no record;
    - the slate's AI filter output carries `synthetic`;
    - its summary says "synthetic fixture range" when the fixture applies.
15. **B-M6.** Spec section 18's `AIResilienceAssessment` has an evidence-quality field; add
    it. Require a widening reason for a range that spans more than one band; the fixture
    needs one.
16. **B-M7.** Add an integration case that runs a published synthetic range through the
    slate, at a minimum below its lower end and one above it, with the `scored` and
    `below_ai_resilience_minimum` counts asserted.
17. **B-M9.** Add integration cases for the evidence endpoint's `REFERENCE_DATA_UNAVAILABLE`
    (503) and its unknown concept (`NOT_FOUND`).
18. **B-M10.** Correct ADR 0010's provisional-decision numbering, at `:4` and `:161`.

Parked for the final review (R12, hypothetical in L0; do not do these): B-M4 (one record per
`esco_uri`) and B-M5 (tying `mapping_reviewed` to a mapping version).

## Also

- Run `pnpm run generate` after any API change, and commit the client.
- Say whether DBOS `application_version` changes.
- No live calls.
- Run `make check`, then `make acceptance` once at the end, and name each covering test.
- File changes use the Edit and Write tools only: no sed, heredocs, one-liners, `touch`, or
  `rm` of tracked files.
- Never read `.env` or NESSA_HOME. Never commit `~$ssa_Local_Development_Plan.docx`. Never
  push. No subagents. Do not edit CLAUDE.md; update the proposed wording in your report
  instead.
- Append your report under "Fix round 1" in `task-7-sliceB-report.md`. Then reply with the
  short contract.
