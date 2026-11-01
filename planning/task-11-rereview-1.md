# Task 11 — scoped re-review 1 (fix round 1)

I checked the fix commits (`45e5839`, `e9417fb`, `594843c`; FIX_BASE `5b00d13`, HEAD `594843c`) against the controller's rulings in `task-11-fix-round-1.md`. Where a ruling differs from my first-round suggestion, I judged against the ruling. That applies to I1, which now includes `provisional_matrix`, and to I5, where the code was changed for D17 and the spec's inequality is the default for D15.

The repository stayed read-only: the probes and mutations ran from scratch scripts in memory, and `git status` is clean.

**Result:** 15 fixed, 0 partly fixed, 0 not fixed. New issues: Critical 0, Important 0, Minor 3.

## The Important findings

| # | Status | Evidence |
|---|---|---|
| I1 | **Fixed (as ruled)** | See I1 below. |
| I2 | **Fixed** | See I2 below. |
| I3 | **Fixed** | See I3 below. |
| I4 | **Fixed** | See I4 below. |
| I5 | **Fixed (as ruled)** | See I5 below. |
| I6 | **Fixed** | See I6 below. |

**I1: a qualified readiness no longer gives an unqualified verdict.**
- **Probe re-run.** With an accepted-assumption outcome and every record reviewed, the result is `verdict=affordable_and_feasible_with_qualifications`. The route's qualifications are `provisional_matrix, proposed_records, proposed_rubrics, self_reported_evidence, planned_outcome_assumption`, the same names as `readiness_qualifications`. Before the fix it was `affordable_and_feasible` with `[]`.
- **Code:** `checker._qualifications` appends every readiness qualification by name and removes the duplicate `proposed_records`.
- **Test:** the OPTN-09 test is corrected and now asserts that the verdict is qualified.
- **Mutation:** dropping the readiness qualifications again makes that test fail.
- **Records:** ADR 0013 decision 10 records this as a ruling, not as R6.

**I2: an unknown hard limit is unresolved, never a pass.**
- **Probe:** with all three limits null, the result is `unresolved`, with three `limit_unknown` findings naming `direct_spend_cap`, `monthly_payment_cap` and `reserve`.
- **A known breach still wins:** an unknown cap together with a reserve breach reads `not_feasible_in_this_model`.
- **Code:** `reserve_minor` may now be null, and the reserve check is skipped only when the reserve is null.
- **Optional limits stay optional:** an absent deficit cap gives no finding, and the economic-cost cap is still a preference.
- **Tests:** one parametrised test covers each of the three limits.

**I3: a payment due before the planning start is named, never dropped.**
- **Probe re-run.** The £500 deposit due 2026-12-15 now gives `unresolved`, `direct=None` and `payment_before_start` with an amount of 50000. The payment is listed in `DirectLedger.before_start`.
- **Test:** the probe is now a regression test.

**I4: every amount on the API is `Money`.**
- **Records:** `Payment.amount`, `Recurring.amount`, `Support.amount`, `WorkPattern.net_income` and `Wage.net_income` are `Money`.
- **`Minor`** is defined once, in `nessa/money.py`.
- **OpenAPI, checked by my own script against `f6e9bfb`:**
  - no schema or path removed, and no path changed;
  - one path added, `/v1/workspaces/{workspace_id}/planning/options`;
  - 26 schemas added;
  - the only schema changed is `ErrorStage`;
  - no new schema has a `*minor*` property.
- **Tests:** `tests/api/test_planning_contract.py` guards this. The integration test asserts that C04's payment is `{"currency": "GBP", "minor_units": 299500}`.

**I5 (D17): a conditional award paid to the provider now moves in `delay`.**
- **Probe re-run (the assumed fee waiver):** payments `base [0,0,0]`, `delay [30000,0,0]`, `no_award [30000,0,0]`.
- **An award with a stated amount:** delay covers only the payment due after it arrives (`delay` direct cost £100 against £50 in `base`).
- **A full waiver on an unknown fee:** when delayed, the fee reads `cost_unknown`, not known.
- **Mutation:** turning the delay off for provider-paid awards makes the new test fail.

**I5 (D15): repayments now count inside the monthly payment cap.**
- **Code:** `P_m + R_m ≤ M_m` is the default. An unscheduled single payment adds the smallest monthly repayment.
- **Mutation:** taking the repayments out of the cap makes the FIN1-10 test fail.
- **Decision sheet:** D15 is reworded as the question, citing the inequality.
- **ADR and register:** ADR 0013 decisions 6 and 9 match the code. FIN1-10 rests on a test of the inequality.

**I6: the planning enum is renamed `CitationBasis`.**
- No schema name contains `__`.
- `Basis` is `["stated", "inferred"]` again and is exported by `index.ts`.
- `NessaProfileRecordsBasis` is gone.

## The Minors marked "Fix"

| # | Status | Evidence |
|---|---|---|
| M1 | Fixed | The compiler builds `active` from `months.touched` and `usable_index` from `months.usable_from`. `_Timeline.usable` reads `usable_index`. A mutation of `touched` is now caught by `test_actual_dates_stay_beside_the_model_months`. TIME-01's register evidence is true. |
| M3 | Fixed | D12 (`session-2.md`) and ADR 0013 decision 4 say extra costs also fall in month 0, citing C03's £13.99. |
| M4 | Fixed | All seven Sprint 2 checklist items are on the sheet, each with captures. Every named capture exists, and so does the Storybook story `You / Reply Streaming`. The items that need the live app are named. One new usability gap: see N3. |
| M5 | Fixed | The sheet says why ADR 0011's decisions 10 and 12 are absent: 10 was superseded by ADR 0012, and 12 belongs to the rights review (OI-07). |
| M6 | Fixed | The T set shows pounds (`earns below £32,400.00 a year before tax`, `aged 19 or over`). Findings and evidence kinds are in words, and T14 no longer says "unknown" twice. The full partial-sketch reason is on every result row and in the header. `test_the_checker_questions_read_plainly` guards it. |
| M7 | Fixed | One list of what has no store, the same in ADR 0013 decision 11, in its Consequences (by reference) and in the endpoint's docstring, now complete. `entry_requirements_met` is `bool \| None`, served as null and described "not yet confirmed, never ineligible". The description of `supports` reads "none confirmed yet" in the OpenAPI document. |
| M9 | Fixed | Stacking, exclusivity and eligible-cost caps are in ADR 0013's "Not modelled here" and in PLN-06's open list. |
| M10 (part) | Fixed | `limit_text(None)` renders "unknown", and T5 uses it. |
| M11 | Fixed | `tools.option_pack_files.pounds` uses integer `divmod`, and `session_2_files` imports that same object. The Q package is byte-identical to `f6e9bfb` (SHA-256 `a7212a46…` on both). |

**Parked as ruled:**
- M2 is recorded as ADR 0013 decision 13, the known limits.
- M8 is corrected by the controller in `carry-forward-task-12.md`.
- M10's month rows and M12 are on the final-review list.

## The implementer's concerns 3 and 4

- **Concern 3 (`person()` states both caps at £1,000,000): sound.**
  - Tests about caps state their own, and the new I2 test leaves one unknown on purpose.
  - The Hypothesis cases still draw null caps. Those now add `limit_unknown`. The relaxation property compares violations only, and the identity property's direct cost stays known, so neither weakens.
  - No existing case spends anywhere near £1,000,000.
- **Concern 4 (a person's "no" on entry requirements reads unresolved): sound as a fail-safe, but mislabelled.**
  - A stated `false` gives `entry_requirements_unconfirmed`, the same finding as null (probe).
  - The route is never passed, and the spec allows a route that "verifies whether the provider accepts equivalent" entry, so unresolved is defensible.
  - The finding's name says "unconfirmed" when the person did answer. Nothing sets `false` today. See N2.

## Session 2 package

- **Minutes:** 30 + 25 + 55 + 10 + 20 + 10 = 150, unchanged.
- **Human gates:** every part and record sheet still says "not run - requires human", and nothing reads as passed.
- **Question sets:**
  - T1-T36 keep the same 36 rows, with new wording.
  - R1-R58 are unchanged (the file is not in the fix diff).
  - Q1-Q344 are byte-identical.
- **Drift and contract tests:** `cd backend && uv run --locked pytest tests/tools/test_session_2_files.py tests/tools/test_option_pack_files.py tests/api/test_planning_contract.py -q` gave 20 passed.
- **TRACE-01:** `tests/domain/test_planning_trace.py` gave 20 passed after the compiler's month change.
- **Mutation families:** the first round's five mutations are still all caught.

## New issues

### Critical

None.

### Important

None.

### Minor

**N1. A person whose debt repayments exceed their monthly cap now fails every route, and D15 does not say so.**
- **What happens:** under the ruled default `P_m + R_m ≤ M_m`, a £300 existing repayment against a £250 cap gives `monthly_payment_cap` violations in every month (probe), even for a route with no transition payment and a direct cost of £0.
- **Why it matters:**
  - The profile asks for the cap as "the most in any one month" spent on the change (`backend/src/nessa/profile/interview.py:458`), so the stored answer and the checker's cap now mean different things.
  - The T set's finding words, "one month's payments above the monthly payment limit", would misdescribe that case.
  - Nothing stores debts yet, so no product path reaches this.
- **Fix:** state the consequence in the D15 row. Carry the cap's question wording, and a finding that names repayments, to Task 12.

**N2. An explicit "does not meet the entry requirements" reads as `entry_requirements_unconfirmed`** (`compiler.py`, `entry_requirements_met is not True`). This is fail-safe, but the name misreports the person's answer. Carry it to Task 12 with its own finding. That finding can stay unresolved, with "verify whether the provider accepts equivalent experience" as the next action.

**N3. The H-01 checklist sends the product owner to the live app with no time or setup for it.**
- Items 2, 3, 5 and 7 need the live app (`make demo`, which starts the Docker stack) inside the same 7-minute step. The sheet has no setup minutes and no note to start the stack before the session.
- One item, the panel beside a refused send, has no capture at all.
- **Fix:** add "start `make demo` before the session" to the package, or mark those sub-items optional.
