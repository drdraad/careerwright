# ADR 0013: The planning catalogue, the monthly input, the ledgers and the route checker

- Status: Accepted for Task 11 (Sprint 5 backend: S5.1, S5.2, S5.4, S5.5, S5.6). Amended in
  fix round 1 (2026-10-29): decisions 4, 6, 7, 9, 10 and 11 and the consequences changed,
  and decision 13 (known limits) was added.
  - **Provisional, need product owner confirmation (R6):** decisions 4 (a whole fee with no
    stated schedule, and its extra costs, are due in the first month; an intake given as a
    month only stands as its first day), 6 (the deficit cap's definition; whether existing
    debt repayments should leave the monthly payment cap, which the spec's inequality keeps
    them inside), 8 (a milestone reached at the boundary that ends the horizon is within it)
    and 9 (what the delay scenario moves). They are D12-D17 of session 2's decision sheet
    (`docs/reviews/session-2.md`).
  - **Not run - requires human:** the review of the checker's run on P01's real option set
    (H-07, TEST1-14) and of the proposed outcome levels, at session 2.
- Date: 2026-10-29
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

1. **Its own module, `nessa/planning`, all pure** (Global Constraint 3; plan section 3,
   "Planning and optimisation"): `months.py` (TIME-1's grid), `catalogue.py` (the records),
   `compiler.py` (the immutable monthly input), `ledgers.py`, `checker.py` and `pack.py` (the
   pack adapter). It reads the capability model (readiness), the catalogue (the pack) and
   money; nothing imports it but the API and tools. No SQL, no run kind, no model call, so
   DBOS `application_version` stays `nessa-l0-1`. One read endpoint,
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
   - A loan is information: a loan as support is refused (FUNDING-04). Existing debt is a fixed
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
