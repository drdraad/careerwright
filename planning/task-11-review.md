### Spec Compliance

- ❌ **Issues found.** Most of the brief is delivered and works (details below). Five things fall short of the brief, the card's spec sections or a standing ruling:
  - OPTN-09 and R9: the verdict ignores the readiness basis's records (`backend/src/nessa/planning/checker.py:865-905`; the test asserts the defect at `backend/tests/domain/test_planning_checks.py:665-679`).
  - An unknown hard cap counts as a pass (`backend/src/nessa/planning/compiler.py:105,117-118`; `checker.py:788,795-797`; spec section 18, `Nessa_Product_Specification.md:1158`).
  - A dated payment before the planning start is dropped without trace (`checker.py:547`).
  - Payments are not `Money` (spec section 18, line 1158). They are bare integers in `backend/src/nessa/planning/catalogue.py:106,122,256,313,321`, served by `backend/src/nessa/api/routes_planning.py`.
  - D17 says something the code does not do, and D15 departs from the spec's inequality without saying so (`docs/reviews/session-2.md:186,188`; `docs/adr/0013-planning-input-ledgers-and-checker.md:94,122`; `docs/requirements-register.md:231`).
- ❌ **Undisclosed contract change.** The public OpenAPI schema `Basis` was renamed. The report does not mention it.
- ✅ **Delivered as the brief asks:**
  - action concepts apart from dated offerings;
  - the composite apprenticeship;
  - four eligibility statuses apart from `AwardState`;
  - the immutable, content-versioned monthly input;
  - separate direct-spend, income-difference, liquidity and debt ledgers in integer minor units;
  - four distinct limits;
  - liabilities after the horizon;
  - the continuation scenario;
  - the base, delay, no-award and no-offer scenarios;
  - TRACE-01 reproduced exactly;
  - the PREFUND, PAYCAP, TIME, WORKLOAD, ECON and FUNDING families with register IDs;
  - Hypothesis properties;
  - the pack loaded with `review_state` kept;
  - P01's real option set run, span-cited;
  - the session 2 package.
- ⚠️ **Cannot verify from the diff:**
  - `make check`, `make acceptance` and the integration and Hypothesis runs. These are the report's claims; per the contract I did not re-run the suites.
  - The 27 recaptured PNGs and their `checks-*.json` (excluded from the package).
  - C04's excerpts against a body. Reed pages are kept as excerpts only, so T23, T25 and T26 can only be checked against the pack's claims, which match.
  - Every human gate (H-07, H-13, H-01 Sprint 2, D1-D17): not run — requires human.

### Checks against the dispatch

**The Basis rename (classified Important, I6).** The planning module's citation enum `nessa.planning.catalogue.Basis` (`catalogue.py:36`: source, person, fixture) collides with the profile's `Basis`. FastAPI therefore names both schemas by module path, `nessa__planning__catalogue__Basis` and `nessa__profile__records__Basis`, and the public `Basis` is gone. In the generated client, the exported `const Basis` / `type Basis` (STATED, INFERRED) were removed and replaced by `NessaProfileRecordsBasis`. `ProposedChangeOut.basis` and `SourceOut.basis` changed type names. The wire format is unchanged and no web file outside `src/generated` uses the name, so nothing breaks today. It is still a silent, unintended change to a system boundary, it leaks internal module paths into the public contract, and the report omits it.

- **Fix:** rename the planning enum to a distinct name (for example `CitationBasis`), run `pnpm run generate`, and confirm the OpenAPI diff against `f6e9bfb` is purely additive apart from `ErrorStage.planning`.

**Concern 1 (read endpoint only).** The endpoint's docstring and ADR 0013 decision 11 say the person's assumptions have no store and that Task 12 owns them. No surface claims they are stored. Two weak points (M7):

- The lists of what is missing disagree:
  - ADR 0013 decision 11: baseline, cash, work patterns, funding statuses;
  - the ADR's Consequences: adds entry requirements;
  - the report and carry-forward: add living costs.
- All of them omit the reserve, weekly availability, commitments, existing debts, the deficit cap, the continuation scenario, the objective basis and the delay months.
- Each variant is served with `entry_requirements_met: false` and `supports: []` (`catalogue.py:335`). These read as facts about the person, not "not yet confirmed".

**Concern 2 (tests written after the code).** The families do bite. I ran five in-memory mutations from a scratch script (monkeypatching only; the working tree stayed clean):

| Mutation | Tests that failed |
|---|---|
| every wage counted early | PREFUND-01, TRACE01-02 (B) |
| a completion usable in its own month | TIME-02, TRACE01-08 |
| unconfirmed support counted | FUNDING-01, FUNDING-05 (ineligible) |
| weekly allowance multiplied by four | WORKLOAD-01 |
| monthly payment cap dropped | PAYCAP-01, PAYCAP-02 |

One family test asserts the wrong thing: OPTN-09 (I1).

**Concern 3 (the `sed -i`).** Only `backend/tools/session_2_files.py:75` (a comment) and `:155` (a docstring line) read "asked in Part A". Both are prose only, 100 and 99 characters, within ruff's 100-character limit. The file has one commit (`f1386e8`), and nothing else in it looks machine-edited.

**Concern 4 (D12-D17).** All six are on the decision sheet in plain yes/no words (`session-2.md:183-188`) and in ADR 0013 (decisions 4, 6, 8 and 9).

- **Likely to be rejected:**
  - **D13**, a month-only intake taken as its first day. It is the earliest reading, so a finish computed from it can be up to a month early. That contradicts TIME-1's "do not snap an actual intake earlier" and ADR 0013 decision 2's "nothing is snapped earlier". The cautious choice is to compute the finish from the month's last day.
  - **D15**, existing repayments outside the payment cap. Spec section 12 states `P_m + R_m ≤ M_m` (`Nessa_Product_Specification.md:769`), and the sheet does not tell the product owner they would be departing from it.
- **Cannot be answered safely as worded:** **D17** ("moves every conditional offer and award"). An award paid to the provider does not move (I5).
- **Likely to be accepted:** D12, D14 and D16.

**Named risk 1 (TRACE-01 by hand, from `fixtures/m0/worked_trace.json`).**

- **Route B:** £6,000 opening, £1,000 living costs and a £150 fee a month, pay of £2,000 arriving late.
  - January: lower bound 600000 - 115000 = **485000 (£4,850)**, closing 685000.
  - February to April: lower bounds 570000, 655000 and 740000.
  - Peak payment **£150**. Direct cost **£600**, economic cost £600 + 0 = **£600**. Finishes 30 April, so ready from May: **4 months**.
- **Route A:** £1,200 in January and no pay in January or February.
  - Lower bounds 380000, 280000, then **180000 in March**.
  - Economic cost 120000 + 400000 = **£5,200**, time 2 months.
- **Route C:** lowest lower bound 470000, economic cost 70000 + 150000 = £2,200, time 3 months.
- **Routes D and E:** lowest lower bounds 472500 and 474000.
- **Fronts:** {A, B, C}, then {D}, then {E}.

`test_planning_trace.py` compares against the fixture's own values and the hand check's `LOWEST`, never against the checker's output.

**Named risk 2 (money).** The checker's totals use `Money` / `SignedMoney` correctly, and unknown totals are `None`. Payment, support and wage amounts are not `Money` (I4). An unknown cap is treated as no limit (I2). An incomplete ledger's month rows still carry numbers (M10).

**Named risk 3 (TIME-1 and prefunding).**

- Every touched month is reserved (`compiler.py:269-271`).
- A completion is usable from the next month: `usable = finish + 1` (`checker.py:231-232`).
- Unconfirmed support and an unaccepted offer's wage are always counted late.
- The default timing is `LATER`.
- PREFUND (£100, £200 on day one, £300 late) fails the reserve with a closing balance of +£200.

All correct.

**Named risk 4 (four limits).** These are distinct finding codes over distinct quantities:

| Limit | Applies to |
|---|---|
| direct cap | the known total, after-horizon and unscheduled payments included |
| payment cap | each month's transition payments |
| deficit cap | payments - support + lost pay |
| reserve | the prefunded lower bound |

None stands in for another. The PAYCAP-03 and four-limits tests isolate each.

**Named risk 5.** No planning file, tool or document names DIRECTAI. TRACE-01's variants are prefixed `TRACE-01/`.

**Named risk 6 (funding).**

- Only `AwardState.APPROVED`, which requires confirmed eligibility, counts in every scenario.
- An assumed award counts only in base and delay, carries `verify_funding_award` and qualifies the route.
- A loan is refused as support (`catalogue.py` `_consistent`).

Correct, apart from D17's provider-paid case (I5).

**Named risk 7 (proposed records, unknowns).**

- Unknown dates, cost and timetable are `UNRESOLVED` and outrank readiness and qualifications in the verdict.
- The verdict does not read the readiness basis's records (I1).
- An unknown cap passes (I2).
- A pre-start dated payment disappears (I3).

**Named risk 8 (P01's real set).** I checked four C01 excerpts against the private body in `var/evidence/corpus/C01/` (SHA-256 matches the pack). C01.funding_route (59794-59835), C01.fee_total (53424-53468), C01.duration (55850-55888) and C01.eligibility_earnings (62738-62826) are exact spans. C04's T25 and T26 match the pack's claims (the body is not kept). The partial-sketch label is present on every result row. T9 (levels carried to the pack rows) and T10 (C01's route read as F01) ask the agent's mappings as questions. The label's stated reason is incomplete (M6).

**Named risk 9 (properties).** The relaxation property (relaxing a limit never adds a violation) and the order property are real invariants. The identity property mostly restates `liquidity()`'s own formula. The date properties test `months.touched` and `months.usable_from`, which production never calls (M1). The generated cases leave out funding and receipt timing (M12).

**Named risk 11 (untouched).** No change to:

- `fixtures/m0`;
- `backend/src/nessa/catalogue/` (the pack and `PINS`, `d7ff17d7…`);
- `identity/worker.py` (`APPLICATION_VERSION = "nessa-l0-1"`);
- the migrations;
- the live-usage ledger;
- the Q package.

`nessa/planning` imports only pydantic, capability, catalogue, errors and money. The generic boundary tests cover it, so `test_boundaries.py` needs no change. There are no empty layers.

**Named risk 12 (endpoint).**

- `capability_view` runs inside `actor_transaction`.
- Another person gets 404 `NOT_FOUND` (integration test).
- `PackLabel` carries the pack version, `dated`, `label_review` and record counts.
- Every record carries `review_state` and `as_of`.
- Errors come from the existing `NessaError` paths, and no message echoes input.

**Named risk 10 (session 2 package).**

- The parts are in the dispatch's order: 30 + 25 + 55 + 10 + 20 + 10 = **150 minutes**, and the H-13 and H-01 scripts each add up to their minutes.
- Every part and record sheet says "not run - requires human" (the same spelling as Task 7b's Q package), and nothing reads as passed.
- The Q package is untouched. T and R carry their own numbering and have drift tests.
- The decision sheet holds ADR 0012's provisional decisions: D5 the "with help" cap, D9 N6, D6 M4, and D3-D11 overall. It also holds D12-D17.
- All the surfaces it names exist, including the Storybook story `Shell / Route Preview From Fixture`.
- It is usable in one sitting, with friction in the H-01 record sheet and in the T set's wording (M4, M5, M6).

### Strengths

- **The TRACE-01 checker is right.** Every ledger part matches the fixture and an independent hand computation. Prefunding with late wages is correct, B's print snapshot is reproduced, and A's 40-of-40 hours pass while 41 fail.
- **The monthly model is carefully conservative.**
  - It covers touched months, next-boundary prerequisites, the strictly-before application rule with `COARSE_MODEL_UNRESOLVED`, the weekly envelope (not a monthly sum), session clashes, and commitments counted once.
  - A loan can never be support, and conditional income is never proven early.
  - Every violation is listed, and the wording is "not feasible in this monthly model", never "cannot afford".
- **The regression tests are mostly hand-worked** and catch the mutations they name. P02's and P03's values are read from the fixture.
- **Unknown stays unknown.** Unplaced variants keep their date-free checks, and the rest goes to named unresolved findings. Direct cost is `None` when any cost is unknown.
- **The pack adapter is honest.** A typical duration is never a bound, hours give no calendar length, conflicting durations stay unknown, a month-only intake is labelled, and C04 is shown as "from £69.52" with no total.
- **The session 2 package is well organised** and its generators are drift-tested. The agent's own mappings (T9, T10) and proposed levels (R50, R51 with the possible swap) are put as questions, not facts.
- **The report is candid** about the TDD deviation, the `sed` incident and what was not modelled.

### Issues

#### Critical

None.

#### Important

**I1. A route can be "affordable and feasible" unqualified while its readiness rests on accepted-assumption outcomes, proposed rubrics and a synthetic matrix.** (OPTN-09, R9; `checker.py:865-905`, test at `test_planning_checks.py:665-679`)

- **What:** `_qualifications` reads only the catalogue's record states (concept, offering, supports) and `inputs.synthetic`. `_verdict` only asks whether readiness was reached. It never reads `readiness_qualifications` or the readiness basis's own records: the outcomes' `review_state`, `matrix.synthetic`, proposed rubrics.
- **Reproduced:** with `_job_readiness()` (accepted-assumption outcome, synthetic matrix), the result is `verdict=affordable_and_feasible` with `qualifications=[]` and `readiness=conditional_on_assessed_completion`, beside `readiness_qualifications=['provisional_matrix','proposed_records','proposed_rubrics','self_reported_evidence','planned_outcome_assumption']`. The OPTN-09 test asserts exactly this as correct.
- **Why it matters:**
  - It breaks R9's "a proposed record … never enters an unqualified 'affordable and feasible' recommendation" (here a proposed rubric).
  - It breaks the spec: "an accepted provisional mapping … cannot support an unqualified guaranteed-readiness claim" (`Nessa_Product_Specification.md:606`).
  - It breaks ADR 0013 decision 10's own wording: "no synthetic input … accepted assumptions … each named".
  - Task 13a and 12 will build on this verdict.
- **Fix:**
  - Fold the readiness basis into the route's qualifications. At least `proposed_records`, `proposed_rubrics`, `planned_outcome_assumption`, `user_assumption` and a synthetic matrix must qualify the verdict. Whether `provisional_matrix` alone does (it always applies in M0) is a decision to record.
  - Correct the OPTN-09 test so it fails today.

**I2. An unknown direct-spend or monthly-payment cap counts as a pass.** (`compiler.py:105,117-118`; `checker.py:788,795-797`)

- **What:** `PlanningInputs` documents "Unknown is None, never 0". The checker treats a `None` cap as no limit, so with neither hard cap known a route reads feasible. The probe in I1 had both caps `None` and returned `affordable_and_feasible`.
- **Why it matters:**
  - Unknown availability is treated as unresolved (`workload_unknown`), so the two cases are inconsistent.
  - Spec section 18 requires "confirmed budget semantics" for a budget-qualified solve, and an explicit field state for null money (`Nessa_Product_Specification.md:1158`). The profile's `MoneyField` has no "no limit" state, only unasked, unknown, skipped and prefer_not_to_say.
  - Task 12 will map those states into `None` and get passes.
- **Fix:** make a `None` hard cap an unresolved finding (for example `limit_unknown`). If "no limit" is to be a real choice, model it explicitly as a provisional R6 decision. Add a test.

**I3. A dated contractual payment due before the planning start is silently dropped.** (`checker.py:547`)

- **What:** `elif index >= 1:  # before the planning start: refused as starting before it`. That refusal holds only for offset payments on a variant starting before the planning start. A `Payment.due` before the start, on a variant that starts inside the horizon, goes nowhere: no month, no liability, no finding.
- **Reproduced:** a course starting in February with a £500 deposit due 2026-12-15 and a £100 fee gives `feasible`, `direct_cost=10000`, `findings=[]`.
- **Why it matters:** this is a known cost turned into zero. It breaks "failure is never an empty success" and FIN1-02 (contractual liabilities included). Pack 0.1.0 never produces a `due` date, but live research and Task 12 inputs will.
- **Fix:** count it in month 1 (due now, the cautious reading) or raise a named finding. Never drop it. Add a regression test.

**I4. Payments, support and wages are not `Money` on the new public API.** (spec section 18, `Nessa_Product_Specification.md:1158`: "payments/fees use `Money`"; CLAUDE.md invariant)

- **What:**
  - `Payment.amount_minor`, `Recurring.amount_minor`, `Support.amount_minor`, `WorkPattern.net_income_minor` and `Wage.net_income_minor` (`catalogue.py:106,122,256,313,321`) are bare `int`s.
  - The ledger rows (`ledgers.py:31` and on) are bare `int`s too.
  - The `Minor` alias is redefined in three files.
  - `GET /v1/workspaces/{id}/planning/options` serves the catalogue models directly, so the generated client has `amount_minor: number` with no currency.
- **Why it matters:**
  - Earlier API schemas convert to `Money` at the boundary (`api/reference_schemas.py:64`, `api/discovery_schemas.py:359`, `api/research_schemas.py:472`).
  - The UI takes money only from the generated client.
  - Task 12 will consume this contract, and changing it later is a breaking client change.
- **Fix:** use `Money` for these amounts, or convert them at the API boundary, and regenerate the client. Internal ledger arithmetic may stay in integers.

**I5. The decision sheet asks about rules the code does not implement as worded.** (`session-2.md:186,188`; ADR 0013 decisions 6 and 9, `:94,:122`; `requirements-register.md:231`)

- **D17:**
  - **What it says:** "the delay scenario moves every conditional offer and award later".
  - **What the code does:** a conditional award paid to the provider is applied at its original month in `delay` (`checker.py:510,530`). Only awards paid to the person move (`:591`).
  - **Reproduced:** a potentially-eligible, assumed fee waiver gives `delay` the same payments as `base`, `[0, 0, 0]`.
  - Spec section 12 names disbursement delays among the hard constraints and "no funding award" among the stress cases.
- **D15:**
  - **What it says:** existing repayments are outside the monthly payment cap.
  - **What the spec says:** `P_m + R_m ≤ M_m` (`Nessa_Product_Specification.md:769`). The sheet and ADR 0013 decision 6 do not say that D15 departs from it.
  - **The register:** FIN1-10 is marked **verified** although its own requirement text, "payments + repayments ≤ monthly cap", is what the code does not do.
- **Why it matters:** only the product owner's answers settle R6 items. If the words are wrong or incomplete, a "yes" will be applied to a different rule.
- **Fix:**
  - Either move a provider-paid conditional award in `delay` (the person pays first), or reword D17 and decision 9 to say it is not moved.
  - Cite the spec's inequality in the D15 row.
  - Set FIN1-10 to "implemented (pending D15)".

**I6. The public OpenAPI schema `Basis` was renamed, unannounced** (contract; see "The Basis rename" above). Rename the planning enum to a distinct name and regenerate the client.

#### Minor

**M1. The date properties test helpers production never calls.** (`months.py:61,69`, against `compiler.py:269-271` and `checker.py:231-232`)

- `touched` and `usable_from` are used only by tests. The compiler and checker re-implement the same rules inline.
- TIME-01's register evidence (`requirements-register.md:357`) is only `test_planning_months.py`.
- **Fix:** have the compiler call `touched`, and the checker derive `usable` from `usable_from`'s rule, or point the properties at `compile_input` and `check_route`.

**M2. The pack adapter has two unsafe shapes, not reachable with 0.1.0 (R12, for the final-review list).**

- A month-only application deadline is dropped as "no deadline" (`pack.py:269-271`).
- Only the first offering per option is read (`pack.py:112`).

**M3. D12 and ADR 0013 decision 4 do not say that extra costs also fall in month 0** (`pack.py:294`, C03's £13.99).

**M4. The H-01 record sheet does not match the Sprint 2 checklist.**

- It asks "Sprint 2 checklist items 1-6" (`session-2.md:139`), but `docs/reviews/sprint-2.md:305-320` has seven. Item 7, the phone, is missing.
- The listed captures do not cover items 2, 3, 5 and 6 (the conversation states, the review tray, the support panel, key consent). `you--support-note--*` and `you--reply-failed--*` exist but are not named.

**M5. The decision sheet leaves out two of ADR 0011's provisional decisions.** It includes ADR 0011 decisions 8 and 9 but omits decisions 10 and 12, while presenting itself as "the provisional decisions" (`session-2.md:164-188`). Add them, or say why they are absent: 10 is superseded by ADR 0012, and 12 belongs to the rights review OI-07.

**M6. The T set is hard going for a non-technical reader.**

- It shows raw JSON with minor units (T18, T19: `"minor_units": 3240000`).
- It shows raw codes (`dates_unknown; cost_unknown`, `not_ready`, `topic_mention, unsupported`).
- T14 reads "unknown: … : unknown".
- T28-T31 give the partial-sketch reason as "no pack outcome has a level". In fact no variant has dates, so no completion boundary is ever assessed. P01's outcomes are also topic mentions or unassessed practice, which R41-R48 propose stay without a level even after review (`session_2_files.py:463`).

**M7. What has no store is listed inconsistently, and two served fields read like stored facts** (see Concern 1). The lists in ADR 0013 decision 11 (`:135`), its Consequences and the carry-forward disagree, and they omit inputs. `entry_requirements_met: false` and `supports: []` read like stored facts about the person.

**M8. The carry-forward's "D12 decides C04's verdict" is not accurate.** C04 paid in full breaks the £1,500 direct-spend cap whatever D12 says. C04 has no dates, so D12's month is never used. Only the single-payment reading matters. This affects Task 12's priorities.

**M9. Funding stacking, exclusivity and eligible-cost caps are neither modelled nor listed as open.** Supports are summed, and the spec says "never assume … two schemes can be stacked" (`Nessa_Product_Specification.md:594`). The open list in PLN-06 (`requirements-register.md:512`) and ADR 0013's "Not modelled here" (`:164`) omit it.

**M10. Unknown figures can still read as numbers.**

- An incomplete ledger's month rows carry numbers (`IncomeMonth.difference_minor`, `checker.py:736`, and `LiquidityMonth`). Only the ledger-level `complete: false` says otherwise.
- The tool renders an absent cap as £0.00 (`session_2_files.py:330`, `or 0`), which does not affect P01.

**M11. The tool formats money with float division and duplicates an existing helper.**

- `_money` uses `minor / 100` (`session_2_files.py:247-248`). Global Constraint 4 says no floats for money. The output is exact for these amounts and follows Task 7b's precedent.
- It is a verbatim copy of `option_pack_files._money` (`:85-86`), when the module already imports other helpers from there.

**M12. The Hypothesis cases miss the error-prone paths.** The generator (`test_planning_properties.py:20-55`) never draws supports, wages, offers, work patterns, unplaced variants, recurring plans or debts. The identity property largely restates `liquidity()` (`:76`).

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The TRACE-01 checker, the TIME-1 and prefunding rules and the four limits are correct, verified by hand and caught by the mutations. The session 2 package is complete and in order. But the verdict can still read "affordable and feasible" unqualified over assumed outcomes and with unknown hard caps, a known payment can vanish, the new API does not use `Money`, an OpenAPI schema was renamed unannounced, and D15 and D17 do not match the code or the spec as worded. All need fixing before session 2 and Task 12 build on them.
