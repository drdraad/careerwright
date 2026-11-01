# Task 11 — fix round 1 (FIX_BASE 5b00d13)

The review (`task-11-review.md`) is Spec ❌, Needs fixes: Critical 0, Important 6, Minor 12.
Read it in full, including its probes. These are the controller's rulings. Each fix that
changes behaviour gets a test that fails first; record the RED run.

## Important

1. **I1: a qualified readiness never gives an unqualified verdict. Ruling: carry every
   readiness qualification into the route's qualifications, by name.** That includes
   `provisional_matrix`, so in L0 every route that rests on the pack reads qualified until
   Task 7c reviews it. Why: R9 and spec line ~606 ("cannot support an unqualified
   guaranteed-readiness claim"), applied fail-safe. Record this in ADR 0013 decision 10 as
   a ruling, not as R6. Correct the OPTN-09 test so that it fails against the current code.
2. **I2: an unknown hard limit is unresolved, never a pass. Ruling:** an unknown direct-spend
   cap, monthly payment cap or reserve gives an unresolved finding (for example
   `limit_unknown`) that names the limit. The deficit cap stays optional, because the spec
   applies it only when the person specifies one. The economic-cost cap stays a preference.
   Add a test for each of the three limits.
3. **I3: a payment due before the planning start. Ruling:** raise a named unresolved
   finding (for example `payment_before_start`). Never drop it, and never guess whether it
   was paid. Add the reviewer's probe as a regression test.
4. **I4: every money amount on the API is `Money`. Ruling:** take the smaller coherent
   option. Either use `Money` in the catalogue's payment, recurring, support, work-pattern
   and wage fields, or convert to `Money` at the API boundary as `api/reference_schemas.py`
   does. Either way, no bare minor-unit integer reaches the generated client. Ledger
   arithmetic may stay in integers. Define the `Minor` alias once. Regenerate the client.
5. **I5, D17 and D15.**
   - **D17. Ruling: make the code do what D17 says.** In `delay`, a conditional award moves
     later whoever it is paid to. A provider-paid award that moves past the payment it
     covers does not reduce that payment: the person pays it. Why: a stress scenario must
     stress, and spec section 12 names disbursement delays. Add the reviewer's probe (an
     assumed fee waiver) as a test.
   - **D15. Ruling: the default follows the spec's text.** Spec section 12 states
     `P_m + R_m ≤ M_m` (line ~769). Count every repayment in the debt ledger, existing debt
     included, inside the monthly payment cap. Then reword D15 as the question "should
     existing debt repayments sit outside the monthly payment cap instead?", citing the
     spec's inequality. FIN1-10 is verified only if its test checks the inequality.
   - Update ADR 0013 decisions 6 and 9 to match.
6. **I6: the `Basis` rename. Ruling: fix as the reviewer says.** Give the planning enum a
   distinct name (for example `CitationBasis`) and regenerate. Then confirm that the
   OpenAPI diff against `f6e9bfb` is additive apart from `ErrorStage.planning`, and say so
   in the report.

## Minor

- **Fix:**
  - **M1:** make the compiler and the checker use `months.touched` and `months.usable_from`,
    so the properties test production code. Keep TIME-01's register evidence true.
  - **M3:** say in D12 and ADR 0013 decision 4 that extra costs also fall in month 0.
  - **M4:** the H-01 record sheet covers all seven Sprint 2 checklist items, and names a
    capture for each item it can, including `you--support-note--*` and
    `you--reply-failed--*`. Say which items need the live app instead.
  - **M5:** add ADR 0011's decisions 10 and 12 to the decision sheet, or say on the sheet why
    each is absent (10 is superseded by ADR 0012; 12 belongs to the rights review, OI-07).
  - **M6: make the T set plain.**
    - Show money as pounds (£32,400.00), never JSON or minor units.
    - Use plain words for codes, and fix T14.
    - Give the partial-sketch reason fully: no variant has dates, so no completion boundary
      is assessed; and P01's outcomes are topic mentions or unassessed practice.
  - **M7:**
    - Use one list of what has no store, the same in ADR 0013 decision 11, its Consequences
      and the endpoint's docstring. Include every person-supplied input: the reserve,
      availability, commitments, existing debts, the deficit cap, the continuation
      scenario, the objective basis and the delay months.
    - Serve `entry_requirements_met` as unknown (null) until the person confirms it, because
      unknown is never ineligible (CLAUDE.md). Label `supports: []` as "none confirmed yet",
      in the schema's description at least.
  - **M9:** add stacking, exclusivity and eligible-cost caps to ADR 0013's "Not modelled
    here" and to PLN-06's open list. Supports are summed today. The controller carries the
    rule to Task 12.
  - **M10 (part):** the tool never renders an absent cap as £0.00 (`or 0`). Show "unknown".
  - **M11:** format money with integer arithmetic in one shared helper, used by both
    `tools.option_pack_files` and `tools.session_2_files`. The Q package's output must stay
    byte-identical: its drift test proves it.
- **Parked:**
  - **M2:** state both shapes as known limits in ADR 0013 (R11). Final-review list (R12).
  - **M10 (month rows):** the controller carries this to Task 12. When ledgers are served, a
    month row that depends on an unknown amount carries null or its own `complete` flag.
  - **M12:** final-review list (R12).
  - **M8:** the controller corrects `carry-forward-task-12.md`.

## Also

- Regenerate the T and R sets and the decision sheet after these changes. Session 2 must
  still fit 150 minutes, with every item "not run — requires human", Q1–Q344 unmoved, and
  the drift tests passing.
- The same rules as before:
  - Edit and Write only, for every source change. Never use sed, awk or heredocs to change
    a file;
  - never read `.env` or NESSA_HOME;
  - no live calls, never push, no subagents, never edit CLAUDE.md;
  - `fixtures/m0`, pack 0.1.0 and its pin are untouched.
- Run `make check`, then `make acceptance` once at the end, because this round changes the
  API.
- Append your report under "Fix round 1" in `task-11-report.md`. Then reply with the short
  contract: status, commits, a one-line test summary and concerns.
