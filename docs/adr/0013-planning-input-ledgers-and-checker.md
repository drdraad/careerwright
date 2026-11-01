# ADR 0013: The planning catalogue, the monthly input, the ledgers and the route checker

- Status: Accepted for Task 11 (Sprint 5 backend: S5.1, S5.2, S5.4, S5.5, S5.6). Amended in
  fix round 1 (2026-10-29): decisions 4, 6, 7, 9, 10 and 11 and the consequences changed,
  and decision 13 (known limits) was added.
  - **Were provisional (R6), now confirmed:** decisions 4 (a whole fee with no stated
    schedule, and its extra costs, are due in the first month; an intake given as a month
    only stands as its first day), 6 (the deficit cap's definition; existing debt repayments
    stay inside the monthly payment cap, as the spec's inequality keeps them), 8 (a milestone
    reached at the boundary that ends the horizon is within it) and 9 (what the delay scenario
    moves). They are D12-D17 of session 2's decision sheet (`docs/reviews/session-2.md`); the
    product owner answered yes to each (`docs/reviews/session-2-answers.md`), and Task 12a
    removed the provisional marks from the code.
  - **Not run - requires human:** the review of the checker's run on P01's real option set
    (H-07, TEST1-14) and of the proposed outcome levels, at session 2.
- Date: 2026-10-29
- Amended: 2026-10-31, the product owner's approval of the audit (the last section): the
  stored inputs (Task 12a), and workspace options read beside the pack; then Task 12a's
  settlement (its own section, after it). Amended 2026-11-01 (Task 12c, the last section): a
  tuition fee loan paid straight to the provider is a loan to repay (decision 5).
- Requirements: TIME1-01-TIME1-06, FIN1-01-FIN1-12, OPTN-01, OPTN-02, OPTN-04, OPTN-05,
  OPTN-07, OPTN-09, PLN-01-PLN-09, TEST1-14, and the TRACE01, PREFUND, PAYCAP, TIME, WORKLOAD,
  ECON and FUNDING families; spec sections 10, 11, 12, 18 and 20; rulings R6, R9, R11, R12;
  ADR 0011 (the pack's shapes), ADR 0012 (readiness)

## Context

Sprint 5 compiles real options into an honest monthly model, and a pure checker must
reproduce TRACE-01 before any optimiser exists. Pack 0.1.0 gives the real options (all
`proposed`, every outcome level null), and the capability model (ADR 0012) decides
readiness. The optimiser (Task 13a) will call this checker for every candidate; its
independent oracle must share no code with it. Nothing here is model-backed.

## Decisions

1. **Its own module, `careerwright/planning`, all pure** (Global Constraint 3; plan section 3,
   "Planning and optimisation"): `months.py` (TIME-1's grid), `catalogue.py` (the records),
   `compiler.py` (the immutable monthly input), `ledgers.py`, `checker.py` and `pack.py` (the
   pack adapter). It reads the capability model (readiness), the catalogue (the pack) and
   money; nothing imports it but the API and tools. No SQL, no run kind, no model call, so
   DBOS `application_version` stays `careerwright-l0-1`. One read endpoint,
   `GET /v1/workspaces/{id}/planning/options`, serves each target's pack options (decision 11).

2. **TIME-1's grid.** A month is a named calendar month. Every month a dated activity touches
   is reserved; what a completion grants is usable from the next month boundary (TRACE-01 B
   finishes 30 April, ready from 1 May, four months). The compiler takes both from
   `months.touched` and `months.usable_from`, the functions the date properties test. An
   application must complete in a month strictly before its deadline's month: the
   deadline's own month is `COARSE_MODEL_UNRESOLVED`, never ineligible, a later one or a
   deadline already passed is a violation, and an admission verified in the initial state is
   exempt. Actual dates stay beside the months; nothing is snapped earlier or rounded down.

3. **Concepts, offerings and variants (S5.1).** A concept is the stable thing (a syllabus and
   provider, a role class); an offering is one dated intake with its timetable, payment plans,
   prerequisites, grants, deadline and offer gate. A **variant** is an offering with what the
   person confirmed for it: the payment plan, the work pattern, a take-home wage, support,
   and whether they meet the entry requirements.
   - **The work pattern belongs to the variant,** not to a free-standing action. TRACE-01's
     approved patterns differ by route (A a study break, C reduced hours); as separate actions
     the search would add dominated combinations that change TRACE-01's fronts (C with a study
     break would join F2). Patterns of concurrent variants must agree, or the route is
     refused (`conflicting_work_patterns`).
   - **The continuation scenario** is the common work and pay every route returns to and runs
     on where it changes nothing (FIN-1): never a target wage (ECON-05). The baseline is a
     separate, confirmed counterfactual; missing, the economic comparison is unresolved and
     only an explicit direct-spending mode compares (ECON-06, never a silent switch).
   - **An apprenticeship is one composite action** (OPTN-02): one offering with its weekly
     hours (work and training together), its offer gate and its credential. Its advertised
     wage is information: only a take-home amount the person confirms is income.
   - **A job or apprenticeship behind an offer** earns and accrues experience only from the
     accepted offer: no wage before the gate, and in `no_offer` neither wage nor outcome
     (FIN1-04, PLN-05). A future job is a role class, never a named vacancy (OPTN-04).
   - **Every amount is `Money`** on these records (payments, instalments, support, work
     patterns, wages), so no bare minor-unit integer reaches the API or the generated client
     (spec section 18). The ledgers' arithmetic stays in integers.

4. **The pack adapter (`pack.py`).** Pack 0.1.0's options load through these records with
   their review state and date, every consequential field a `Fact` citing its claim's span
   and exact excerpt or keeping the pack's reason it is unknown. A finish date comes only from
   one exact duration in weeks, months or years: C04's "typically 6-8 months" is never a bound,
   C03's hours give no calendar length and C02's two durations stay unresolved. Each way of
   taking a course is its own offering (C01 full and part time), carrying the course's
   planned outcomes (`outcomes_from`). Payment plans are what the page states (C04: £2,995 in
   full, or "from £69.52 a month" with no total). Stated entry requirements leave a route
   unresolved until the person confirms them; the variant serves that confirmation as null
   until then, never as false. **Provisional (R6):** a whole fee with no stated schedule is
   one payment in the offering's first month, and so is each stated extra cost (C03's
   £13.99 certificate); an intake given only as a month stands on the grid as that month's
   first day, saying so.

5. **Funding (S5.2).** An instrument is a scheme's rules, never a conclusion about a person.
   A person's eligibility has four statuses (confirmed, potentially eligible, ineligible,
   insufficient information), confirmed by the person or provider (M0 builds no eligibility
   engine), and is kept apart from the award (not applied, applied, approved, refused).
   - Only an approved award, which needs confirmed eligibility, counts in every scenario and
     so in unconditional figures.
   - A route may be an explicit conditional award scenario ("if funding is approved"): the
     support counts in `base` and `delay` only, the route carries the condition with a
     blocking verification (`verify_funding_award`), and `no_award` is the unfunded case
     beside it (FUNDING-05). Ineligible and insufficient information never count.
   - Support paid to a provider reduces the fees the person pays and is never a receipt;
     support paid to the person is a receipt in its month and reduces direct cost once
     (FUNDING-03). Unconfirmed support is never proven early, so it never pays for an earlier
     outflow (PREFUND-03).
   - A loan is information: a loan as support is refused (FUNDING-04; from 2026-11-01 one loan
     has its own rule, Task 12c's amendment: a tuition fee loan paid straight to the provider
     is a loan to repay, still never support). Existing debt is a fixed
     commitment: its repayments are outflows, and its balance, integer interest (rounded half
     up) and repayment have their own ledger.

6. **Four limits, each named** (FIN1-06): the direct-spend cap (direct cost, after-horizon
   liabilities included), the monthly payment cap, the reserve (each month's prefunded lower
   bound) and, if the person sets one, the monthly deficit cap. An economic-cost cap is a
   preference, never a violation.
   - **The monthly payment cap** holds each month's transition payments plus every
     repayment in the debt ledger, existing debt included, as spec section 12 states:
     `P_m + R_m ≤ M_m` (fix round 1, review I5). **Provisional (R6):** whether existing debt
     repayments should sit outside the cap instead (session 2 D15).
   - **An unknown hard limit is never a pass** (fix round 1, review I2): an unstated
     direct-spend cap, monthly payment cap or reserve is an unresolved `limit_unknown`
     naming it. The deficit cap stays optional, because the spec applies it only when the
     person sets one.
   - **Provisional (R6):** the deficit cap limits each month's payments less support received
     plus pay lost against the baseline (D14).

7. **The ledgers and unknowns (S5.5).** Direct spend (with liabilities after the horizon and
   payments not yet in a month, each with its timing), income difference (counted once, over
   one horizon) and liquidity (conservative prefunding: opening plus receipts proven before the
   outflows, less living costs, payments and debt service; later receipts open the next
   month). Wages arrive late unless proven early, and an unaccepted offer's wage is always
   late.
   - A variant with no known start or finish is not placed: the checks that hold in every
     month still run (a cost above the direct cap, a single payment above the monthly cap
     with the least month's repayments, a weekly load above every month's availability),
     because an unknown cost can only add to the known part; every other check is unresolved
     and named (`dates_unknown`, `cost_unknown`, `workload_unknown`). A cash month is
     reported as a violation only when every receipt is known.
   - **A payment due before the planning start** is never dropped (fix round 1, review I3):
     it is listed with its date (`before_start`) and named as an unresolved
     `payment_before_start`, and the direct cost is unknown, because whether it was paid is
     never guessed.

8. **Readiness is the capability model's** (RDY-1). The checker asks `assess` at each month
   boundary where a selected offering's outcomes become usable; the first boundary at which the
   target is conditionally ready (or ready now) is the milestone, and the months before it are
   the time objective. It never changes current evidence (TRACE01-06). **Provisional (R6):** a
   milestone reached at the boundary that ends the horizon is within it. With pack 0.1.0 no
   option counts towards readiness (every outcome is proposed and has no level): P01's real
   option set is a partial sketch on that axis.

9. **Scenarios (S5.6).** `base`, `delay`, `no_award` and `no_offer`, the same set for every
   route (PLN-08); no adaptive policy, no invented probability. **Provisional (R6):** `delay`
   moves every conditional offer and every conditional award later by
   `scenario_delay_months`, declared once per comparison with no default, whoever the award
   is paid to (fix round 1, review I5): an award paid to the provider covers only the
   payments that fall due after it arrives, and the person pays those before it.
   Contractual course dates stay fixed.

10. **What a result says.** Every violation is listed, never only the first (hand check H1).
    Feasibility is feasible, not feasible in this monthly model (a conservative rejection,
    never "cannot afford") or unresolved. The verdict adds readiness and qualifications:
    proposed records, accepted assumptions, synthetic data, conditional offers and awards are
    each named. **Ruling (fix round 1, review I1; not R6):** every qualification the
    readiness assessment carries is carried into the route's qualifications by name, the
    provisional matrix included, so a qualified readiness never gives an unqualified verdict
    (R9; spec section 10, "an accepted provisional mapping … cannot support an unqualified
    guaranteed-readiness claim"). M0 matrices are always provisional, so in L0 every route
    that rests on the pack reads "affordable and feasible with qualifications" at best. The
    input is versioned by its content, and every result names that version.

11. **The read endpoint** serves, for each workspace target, the pack options of the pack target
    the capability model matched (ADR 0012 decision 10), or why there are none
    (`no_pack_target`, `ambiguous_crosswalk`), with the pack's date and the workspace's
    synthetic and data-mode labels. **What has no store yet** is every input the person
    supplies: the baseline, the continuation scenario, opening cash, living costs, the
    reserve, the three hard limits and the deficit cap, weekly availability, commitments,
    existing debts, the objective basis, the delay months, and, per variant, the work
    pattern, wage, funding statuses and entry confirmation. The option checkpoint confirms
    them and owns their persistence (Task 12), as ADR 0012 left outcome acceptance to it.
    Until then a variant's support is served as "none confirmed yet" and its entry
    confirmation as null.

12. **Session 2's package** gains two generated sets with their own numbers, so Q1-Q344 never
    move: T1-T36 (the checker on P01's real option set, each field beside its span, in plain
    words) and R1-R58 (the capability reference and a proposed level for every pack outcome).
    Their generator is `tools.session_2_files`, with drift tests; it formats money with the
    same integer helper as `tools.option_pack_files`. P01's inputs are TRACE-01's,
    unchanged; P01's levels are carried to the pack rows they name by an agent's mapping,
    asked as T9. The proposed levels are proposals in the package only: pack 0.1.0 stays
    frozen, and Task 7c publishes the reviewed levels.

13. **Known limits** (R11; fix round 1, review M2; on the final-review list, R12). Neither is
    reachable with pack 0.1.0:
    - an application deadline given as a month only is read as no deadline;
    - only an option's first offering is read.

## Consequences

- **The checker reproduces TRACE-01 exactly** (every ledger part, B's £600 and £150 and
  £4,850, A's 40 of 40 hours) and the plan's regression families, with Hypothesis properties
  for the ledger identities, monotone limits and action order.
- **On P01's real option set** C04 paid in full is not feasible in this model (£2,995 above
  P01's £1,500 caps, in whatever month), and the other three variants are unresolved: no
  intake, no total, no timetable, and C01's fee waiver not counted while P01's status is
  insufficient information. No route there is "affordable and feasible".
- **Task 13a** calls `check_route` per candidate, and its oracle must not reuse this code.
  The search must key its inputs by the matrix `definition_version` the readiness basis
  carries (ADR 0012).
- **Task 12** gives the person a place to confirm every input decision 11 lists, and shows
  why a route fails.
- **Not modelled here:** loan draws and new borrowing (M1); a verification milestone after an
  assessed completion; experience accrual beyond an offering's own outcomes; funding
  stacking, exclusivity and eligible-cost caps (supports on one variant are summed today, and
  the spec says never to assume two schemes stack: carried to Task 12); and S5.3, the
  checkpoint UI.

## Amendment, 2026-10-31 (the product owner's approval of the audit)

The audit found the Options task hid a backend piece (a store for about 15 of the person's
money and time inputs) and that options existed only for the pack's four targets. The
product owner approved it on 2026-10-31, with its decision 4: options and routes for any
job, marked not reviewed.

- **Decision 11's store is Task 12a's.** Task 12 is split: Task 12a stores and confirms
  every input decision 11 lists, as validated commands (an expected version and an
  `Idempotency-Key`), with outcome accept and override; Task 12b's checkpoint collects them
  in one place. Work rights and remote working join the inputs (spec sections 1 and 3);
  where they live is to be settled by Task 12a. Unknown work rights leave a route
  unresolved, never ineligible.
- **Session 2's answers.** The product owner answered yes to D12–D17
  (`docs/reviews/session-2-answers.md`), so decisions 4, 6, 8 and 9 stand as written; Task
  12a applies them.
- **Funding stacking stays unresolved** when a person confirms more than one support on a
  variant, until stacking is confirmed; exclusivity and eligible-cost caps follow the same
  rule (Task 12a).
- **The catalogue reads workspace options beside the pack.** An option the person adds
  (Task 12b) or that option research finds (Task 7e) is a `proposed` workspace record in the
  pack's shapes (ADR 0011, amendment). A route built on one is qualified: "affordable and
  feasible with qualifications" at best (decision 10), never an unqualified "affordable and
  feasible".

## Task 12a's settlement (2026-10-31): the stored inputs and the rules they need

Rulings of this task (not R6; each costs little if wrong), with the controller's rulings on
review 13a (C07, C09 and one job transition) applied.

1. **Where they live.** `careerwright/planning` keeps its pure modules pure; it gains
   `inputs.py` (the stored document, what a solve needs, and how the monthly model reads it),
   `commands.py` (the use cases) and `store.py`, its only SQL (an adapter in the architecture
   test). Migration 0033 adds `planning_input_versions`: append-only versions of one document
   per workspace under row-level security, its CHECKs repeating the rules below.
   `GET /v1/workspaces/{id}/planning/inputs` serves it with what a solve still needs;
   `PUT` replaces the whole document with an expected version and an Idempotency-Key through
   `run_idempotent`, and appends `planning.inputs_updated`. Only the person's direct entry
   writes it: no run kind, no model, so DBOS `application_version` is unchanged.
2. **Work rights and remote working live in the planning inputs, not the profile.** Why:
   they are the person's circumstances for the plan, read by the checker as a hard check
   (spec section 12, "residence/work permissions"); keeping them out of the profile's city
   list makes "never inferred from a city" and "remote never takes a city slot" structural;
   and the profile is changing in the main tree's tasks (6d), so a profile schema change here
   would collide. Work rights are `held`, `not_held` or `unknown`; only `held` lets a route be
   feasible. Not stated or `unknown` is `work_rights_unknown` and `not_held` is
   `work_rights_not_held`: both unresolved, never ineligible, because this model checks no
   visa or sponsorship. Remote work names an England employer (`GB-ENG`) and `Europe/London`;
   another country is outside L0's supported slice and refused (spec section 1). The target's
   own right-to-work row stays the capability model's requirement statement (the employer's
   check, ADR 0012): the two are separate records, and a route needs both, so a disagreement
   can only withhold a result, never give one.
3. **The two spending caps stay the profile's** (one record, set only by the person,
   PROF-04); the planning inputs hold the reserve and the deficit cap. `prepare` reads both.
4. **One figure a month or a week.** Money and hours are stored horizon-free and laid on the
   comparison's grid by `prepare` (known limit: a figure that changes within the horizon is not
   modelled). Not stated is null, never 0; "no debts" and "no commitments" are `[]`, not asked
   is null (session 2, T5: P01's "none" was an assumption).
5. **What a solve needs** (API-05): the objective basis, the continuation, opening cash, living
   costs, commitments, existing debts and the delay months block a solve and are named (a
   refused `prepare` lists them); an unstated cap, reserve, availability, a baseline the
   economic comparison or the deficit cap reads, or work rights not stated leave every route
   unresolved, as decision 6 has it.
6. **Each option's answers** (`VariantInputs`): the work pattern, the take-home wage, each
   support with its status (a loan is refused; an approval needs confirmed eligibility; a
   scheme the catalogue names keeps its kind), whether its supports stack, each eligibility
   condition's status and the entry confirmation. A stated support is the person's assumption
   (`accepted_assumption`), so a route resting on it is qualified. An answer new or changed in
   a write must name one of the workspace's options; one kept unchanged stays.
7. **Stacking** (spec section 10: never assume two schemes stack). More than one support
   counted on one variant without `stacking_confirmed` is `stacking_unconfirmed`, unresolved;
   the one confirmation covers exclusivity and eligible-cost caps between them. The known part
   still counts every support, the least the person could pay, so a limit broken even then is
   a violation. Across the options of one route, see item 16.
8. **A fee for eligible learners (C07).** An offering's `eligibility_` funding conditions are
   served as the conditions its stated fee holds under. While one is not `confirmed`, the
   stated fee is not the person's (`eligibility_unconfirmed`, one per condition, unresolved;
   the cost is unknown, the stated payments its least). Living outside the stated areas is
   `ineligible`: the page states no fee for anyone else, so still unresolved. Where no fee is
   stated (C01), its cost is the unknown and the conditions add nothing.
9. **An admission or an offer held (C09).** `admissions` names the offerings where the person
   holds a place or an accepted offer: the application gate joins the initial gates and the
   offer gate is accepted, so a route can depend on it. Without it, and with no application
   in the route, the route is conditional on the application (fix round 1, the controller's
   C09 ruling): a `Condition` of kind `application` (`confirm_admission`) and the
   qualification `conditional_application`, never "not feasible". A deadline already passed
   is still `application_too_late`, and an application in the route keeps TIME-1's timing
   rules.
10. **"Doesn't meet the entry requirements"** is `entry_requirements_not_met`, apart from
    `entry_requirements_unconfirmed`, still unresolved; its next action, worded by the web, is
    to check whether the provider accepts equivalent experience.
11. **Repayments alone above the payment cap** (D15 yes) are `repayments_above_payment_cap`
    in each such month, naming the debts (`reason`), in place of `monthly_payment_cap`; a
    payment with no month is then not blamed for the cap either.
12. **One conditional job transition** (spec section 12). More than one selected variant
    behind an offer not yet accepted (a bridge job, an apprenticeship) is `job_transitions`, a
    violation, in every scenario. An accepted offer is the starting position. The search's
    tree keeps ADR 0016's one-`work`-action bound beside it.
13. **Month rows** (review M10). A ledger month's figure that rests on an amount not known (a
    payment whose amount or month is not stated, pay from an option with no dates, or an
    earlier month that does) is null; living costs and repayments stay known. The checker
    still tests its limits on the known part. A support paid to the person that may not apply
    (its stacking, or its scheme paying for two options, not confirmed) leaves every month's
    receipts null (fix round 1, review 12a, Important 1), while the reserve check still counts
    it: the most cash the person could have, so a breach there is real.
14. **Outcome decisions** (ADR 0012 decision 11): accept or override, each kept with who made
    it and when while unchanged; `decided_outcomes` makes an accepted mapping the person's
    assumption and puts an override beside the unchanged provider claim. A decision the
    outcome contract refuses (a level for a topic mention) is refused at the write.
15. **The oracle and the search.** Each new rule is written again in the oracle and reached by
    its generated cases; the search classes them (ADR 0016's amendment).
16. **One scheme on several options, and exclusive schemes** (fix round 1, the controller's
    ruling on review 12a, Important 2):
    - The same scheme counted on more than one option of a route is
      `scheme_shared_unconfirmed` (its reason the instrument), unresolved, until the person
      confirms it pays for each: `shared_schemes`, a planning input naming one of their stated
      supports. The cost and its month rows are then unknown, the known part the least.
    - Two schemes a record states may not be combined (`FundingInstrument.exclusive_with`,
      either naming the other) both counted in one route are `exclusive_schemes`, a violation:
      not feasible in this monthly model.
    - **L0 limit:** packs 0.1.0 and 0.2.0 record no exclusivity a model can read (their
      `exclusions` are words naming no scheme, and none is filled in), so two different
      schemes in one route are never checked against each other. A scheme's own condition on
      other funded training (C01's "not undertaking any other government-funded training") is
      one of that option's eligibility conditions, for the person to confirm. No rule is
      invented for it.
17. **"No route" when the person's own repayments rule it out** (fix round 1, review 12a,
    Important 3). Existing repayments above the monthly payment cap are a starting breach no
    option, known or unknown, can lower, so a complete search says
    `no_route_in_bounded_model`, naming them as its starting violations, whatever else is
    unknown, an unstated input included. Every other starting breach (the reserve, the
    deficit cap, the workload) some option could relieve, so an unknown still keeps it open.

Not here: storage of an option's own facts the person supplies (a start date, a cost, weekly
hours) and "add an option yourself" (Task 12b); the planning inputs in the workspace export
(capability evidence is not exported either); the solve's stage checks (Task 14).

## Amendment, 2026-11-01 (Task 12c): a tuition fee loan paid straight to the provider

The product owner's school-leaver decision 6 (yes, 1 November 2026; specification section 22,
the tuition fee loan row): a tuition fee loan paid straight to the university is not cash out
of the student's pocket; it is shown as a loan to repay later. Counted as their own money, a
degree's fee would read "not feasible in this monthly model" against any student's limits.
Requirements: FUNDING-06, FUNDING-04 (its L0 change), FIN1-02, FIN1-10. Rulings of this task
(not R6; each costs little if wrong).

1. **Where it lives.** One answer per option, beside its supports:
   `VariantInputs.tuition_fee_loan` (its amount, null when not known, and the funding statuses:
   eligibility and application, the four of each), stored in the planning inputs document
   through Task 12a's one command (an expected version and an Idempotency-Key through
   `run_idempotent`). Migration 0041 adds two CHECKs repeating its rules. In the planning
   model it is `catalogue.TuitionFeeLoan` on the variant: the person's assumption
   (`accepted_assumption`), so a route resting on it is qualified. It is no `Support` and no
   `InstrumentKind`: a support of kind `loan` is still refused, a maintenance loan included.
2. **What it pays.** The variant's fees and instalments, never its extra costs, after any
   support paid to the provider, up to its amount, in the order they fall due. What it pays
   is in neither the cash ledger, nor the direct spending the direct-spend cap reads, nor the
   monthly payment cap's payments, and it is never support (`paid_to_provider` stays the
   support's), a grant, income or a receipt. FIN-1: a payment straight to a provider is left
   out of both sides, never counted twice. Support paid to the person (a grant or bursary)
   lowers the person's direct spending only by what they pay of that option's fees, as before
   Task 12c, so no option's own spending goes below £0 (fix round 1, review 12c, Critical 1:
   setting it against the fee the loan paid made an option's spending negative, and the
   search's spend-cap rule then said "no route" where one existed). In plain words: a grant
   beside a loan can't pay for something else. The economic cost sets the grant against the
   whole fee once, the loan's part included.
3. **Shown as a loan to repay.** A route's check and every archived schedule carry
   `loans_to_repay`: for each option, what the loan pays by the month each fee falls due (a
   month beyond the horizon included), marked conditional or not. Its repayment is `null`:
   not modelled in L0, never 0. Facts only; Tasks 12b and 14 word them (R11).
4. **Its status** (decision 5's funding rules, as for an award): approved, which needs
   confirmed eligibility, it counts in every scenario. Not yet approved, not refused, and the
   person confirmed or potentially eligible, the route rests on it: it counts in `base` and
   `delay`, with a blocking verification (a `Condition` of kind `loan`,
   `confirm_loan_approved`) and the qualification `conditional_loan`; `no_award` is the route
   where the person pays the fee, beside it (FUNDING-05). In `delay` it pays only the fees
   due `scenario_delay_months` or more after the option starts (decision 9). Refused,
   ineligible or insufficient information: it does not count, as for an award. A loan is
   never an award: the condition and the qualification are its own. A loan not yet approved
   that pays nothing (no fee due, or every fee covered by support at the provider) makes
   nothing conditional; with its amount unknown it still does (fix round 1, review 12c,
   Minor 1).
5. **An unknown amount** of a loan that counts is `loan_amount_unknown`, unresolved, never
   £0: the direct cost and the month rows are unknown, and the route lists one loan to repay
   with neither amount nor month. The known part takes the loan to pay every fee, the least the
   person could pay, so a limit broken even then is broken.
6. **The economic cost** (the cost over the horizon) **still counts the fee the loan pays,
   once.** In plain words: a loan is paid back, so it changes when and from whose pocket the
   fee is paid, not what the change costs. This is section 12's own rule ("loan principal is a
   liquidity source, not a discount or an additional copy of tuition cost"), and section 22
   changes only the person's cash and spending limits. So a loan-funded route and the
   self-paid route have the same economic cost; with the direct-spending objective the loan
   lowers what the person spends. The loan's interest and repayment terms are not modelled
   (unknown, on the loan to repay): a known L0 limit. No existing fixture or regression family
   holds a tuition fee loan, so this reading changes no best trade-off there (R14).
7. **Nothing else changes.** Every other loan stays information; Careerwright chooses no
   borrowing (the person states the loan); existing debt stays a fixed commitment; the
   families of routes count the loan as material financing (`tuition_fee_loan:<application>`).
   TRACE-01, the A–I fixture and every regression family keep their values.
8. **The oracle and the search** (ADR 0016's Task 12c amendment): the oracle writes the rule
   again from section 22 and section 12, its generated instances carry the loan in every
   state, and `loan_amount_unknown` is a variant's own finding for pruning rule 2.

Known limit: the loan is the person's statement of an amount; Careerwright does not compute a
student's entitlement, a fee cap or a maintenance loan, and the Advanced Learner Loan is still
refused as support (a question for the product owner, in Task 12c's report).
