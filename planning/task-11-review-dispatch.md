# Task 11 — task review (one reviewer)

You review Task 11 for Nessa L0: Sprint 5's backend. It covers offerings, funding, the
immutable monthly input, the ledgers, the TRACE-01 checker, the pack adapter, one read
endpoint and the session 2 package. Follow `reviewer-contract.md` in this directory exactly:
its method, calibration and output.

All inputs are in `/Users/darianraad/Code/careerpathoptimizer/.superpowers/sdd/l0-sprint-tasks/`.
- **Requirements:** `task-11-brief.md` (the task card, Global Constraints, standing rulings)
  and `task-11-dispatch.md` (the controller's dispatch notes and rulings 1–4).
- **The implementer's report:** `task-11-report.md` (unverified claims).
- **Your package:** `review-f6e9bfb..5b00d13.diff` (BASE f6e9bfb, HEAD 5b00d13, 6,234 lines).
  - **Excluded:** the generated client (`apps/web/src/generated/**`) and the PNGs. The
    controller compared the OpenAPI documents:
    - no operation was removed, and 1 was added;
    - 27 schemas were added, and `ErrorStage` gained only `planning`;
    - **one schema was renamed:** the planning module's own `Basis` enum collided with the
      profile's, so the public schema `Basis` (`stated`, `inferred`) became
      `nessa__profile__records__Basis`. That changed `ProposedChangeOut.basis` and
      `SourceOut.basis`. No web file outside `src/generated` names it.
    - Classify this rename and say what the fix is.
- **Calibration:** R11 and R12 (`docs/plan/l0-sprint-tasks.md`) apply. A hardening that no
  failing check, reproduced defect or Global Constraint requires is a Minor for the final
  review.

## The controller's rulings on the report's concerns (judge honesty, not scope)

- **Concern 1: only a read endpoint; the person's planning assumptions have no store.**
  Ruling: accepted. Task 12's Options chapter confirms and persists them, as it does
  outcome acceptance (`carry-forward-task-12.md`). Check that ADR 0013 and the register say
  exactly what is missing, and that no surface implies stored assumptions.
- **Concern 2: the family tests and properties were written after the code.** Ruling:
  ledgered as a TDD deviation. Judge whether the tests bite: each regression family must
  fail for the defect it names. Spot-check at least two families against the code by
  reasoning, or with a scratch mutation you revert.
- **Concern 3: one `sed -i` on two comment lines in `backend/tools/session_2_files.py`.**
  Ruling: ledgered as a rule incident. Check that the result is only those comment words.
- **Concern 4: D12–D17 are provisional R6.** Check that each is on the decision sheet in
  plain yes/no words and in ADR 0013, and say which, if any, a reasonable product owner
  would reject.

## Named risks, one focused check each

1. **TRACE-01, exactly.** A pure checker reproduces it (B: 4 months, £600 direct and
   economic, £150 peak, £4,850). Recompute B and at least one other route by hand from
   `fixtures/m0`. A test that compares the checker with numbers the checker itself produced
   is not evidence.
2. **Money.** Integer minor units throughout. `Money` (≥ 0) is used for payments and
   `SignedMoney` for economic cost. Unknown money is `null`, never 0, in every ledger and
   API field.
3. **TIME-1 and prefunding.**
   - Every touched month is reserved.
   - A prerequisite is usable only from the next month boundary.
   - A receipt counts only if it is proven available before the outflow, and fixture wages
     arrive late in the month (PREFUND: £100, £200 on day one, £300 late).
4. **Four limits.** The direct budget, the payment cap, the deficit cap and the reserve
   stay distinct. No one stands in for another anywhere in the checker or the ledgers.
5. **TRACE-01 and DIRECTAI** never share route IDs or labels.
6. **Funding status apart from award approval.** Only an approved award counts
   unconditionally. An assumed award is a condition with a blocking verification, and a
   loan is never support.
7. **Proposed records** never reach an unqualified "affordable and feasible" result
   (OPTN-09, R9), and the verdict precedence keeps that true. Unknown dates, cost or
   timetable leave a route unresolved, never passed.
8. **P01's real option set.**
   - Every consequential field is span-cited (claim, hash, offsets, exact excerpt). Spot-check
     three excerpts against the pack.
   - The result is labelled a partial sketch, because no pack outcome has a level.
   - T9 and T10 ask the agent's own mappings as questions.
9. **Hypothesis properties** test real money and date invariants, not tautologies.
10. **The session 2 package (`docs/reviews/session-2.md`).**
    - The six parts are in the dispatch's order and add up to 150 minutes.
    - Every item is "not run — requires human", and nothing reads as passed.
    - Q1–Q344 are unmoved, and T and R are drift-tested.
    - The decision sheet holds ADR 0012's R6 items, among them the "with help" cap, N6 and
      M4, plus D12–D17.
    - It is usable by one non-technical product owner in one sitting.
11. **Untouched.** `fixtures/m0`, pack 0.1.0 and its pin, and `application_version` (no new
    workflow or run kind). `nessa/planning` respects the import rules, with
    `test_boundaries.py` updated if needed, and holds no empty layers. No live call was made.
12. **The read endpoint.** Ownership goes through `actor_transaction`. Errors are
    `NessaError` codes that never echo input. Pack content carries its date and its review
    states.

## Rules

- Read-only, except scratch files in your own scratchpad.
- No live calls.
- No subagents.
- Never read `.env` or NESSA_HOME.
- Do not compose self-harm or distress text.

Write your full report to `task-11-review.md` in this directory. Then reply with only your
two verdicts and your counts of Critical, Important and Minor issues.
