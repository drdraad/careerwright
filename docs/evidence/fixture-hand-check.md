# Fixture hand check: TRACE-01, the A–I direct-spend fixture and P01–P05

- Date: 2026-10-27. Plan S0.5, ruling R1. Requirements: TEST-1, FIN-1, TIME-1, OPT-1,
  RDY-1, OUT-1, AIR-1 (spec v1.2 sections 12 and 20).
- Inputs: `fixtures/m0/` (the supplied pack, byte-identical to `Nessa_M0_Fixtures.zip`;
  hashes in `fixtures/README.md`) and `fixtures/reconstructed/directai.json`.
- Status: **passed, with findings for implementers** (section 11). Nothing in the pack
  contradicts the specification. Several expectations are under-specified in ways that
  would let a wrong implementation pass a naive test; section 8 says how to test them.

## 1 Method

1. Every figure below was derived by hand from the specification text and the fixture
   values, without reading the result from the pack's validator.
2. Then three mechanical checks:
   - `uv run python -I ../fixtures/m0/validate_fixtures.py` (from `backend/`, Python
     3.12.12) and `python3 -I fixtures/m0/validate_fixtures.py` (host Python 3.14.6): both
     print `"status": "passed"` and exit 0.
   - A mutation run against copies of the pack in a scratch directory. Each of nine
     single-value mutations made the validator fail (exit 1, `AssertionError`): B's
     economic cost +1p; B's first payment £150 → £160 (route and catalogue); D moved into
     front 1; the printed minimum prefunded cash +1p; opening cash £6,000 → £1,500; the AI
     filter flag flipped; one space added to the syllabus text; P05 evidence level 2 → 1;
     P04's gate kind changed from statutory. So the validator is not vacuous.
   - A separately written scratch script (not committed) that rebuilt every monthly ledger
     and front. Its output matched every hand figure in sections 3–8.
3. The syllabus hash was recomputed with `shasum -a 256` over the exact UTF-8 bytes of
   `syllabus_text`, not with the validator's `hashlib` call.

## 2 Inputs agree across the specification, P01 and TRACE-01

| Quantity | Spec section 20 | `P01.json` | `worked_trace.json` | Agree |
|---|---|---|---|---|
| Baseline net income | £2,000/month | `current_net_income_minor` 200000 | `baseline_income_by_month_minor` 6 × 200000 | yes |
| Opening cash | £6,000 | 600000 | `opening_cash_minor` 600000 | yes |
| Living costs | £1,000/month | `living_outgoings_minor` 100000 | 6 × 100000 | yes |
| Reserve | £500 | `reserve_minor` 50000 | `minimum_reserve_minor` 50000 | yes |
| Direct-spend cap | £1,500 | 150000 | (not repeated) | yes |
| Monthly transition-payment cap | £1,500 | 150000 | (not repeated) | yes |
| Horizon | common six months | n/a | `comparison_horizon_months` 6 | yes |
| Weekly availability | not stated | 40 h | `available_weekly_hours_envelope` 40 | yes |
| Grants, new borrowing, immediate target salary | none assumed | `borrowing_allowed` false | none present | yes |
| Admission | completed in initial state | n/a | `completed_on` 2026-12-15, before `planning_start` 2027-01-01; `initial_completed_gates` has it | yes |
| City / target | Manchester; data-quality target | Manchester; "Data quality analyst" | `region` "Manchester, England"; same title | yes |

## 3 TRACE-01 route arithmetic (economic-cost mode)

Baseline over the horizon: 6 × £2,000 = **£12,000**. Economic cost (FIN-1):
C_econ = C_direct + Σ (baseline − route income).

| Route | Payments by month | Direct spend | Route income over 6 months | Income loss | Economic cost | Peak payment |
|---|---|---:|---:|---:|---:|---:|
| A | £1,200, 0, 0, 0, 0, 0 | £1,200 | 0 + 0 + 4 × £2,000 = £8,000 | £4,000 | £1,200 + £4,000 = **£5,200** | £1,200 |
| B | £150 × 4, 0, 0 | £600 | 6 × £2,000 = £12,000 | £0 | **£600** | £150 |
| C | £300, £200, £200, 0, 0, 0 | £700 | 3 × £1,500 + 3 × £2,000 = £10,500 | £1,500 | £700 + £1,500 = **£2,200** | £300 |
| D | £275 × 4, 0, 0 | £1,100 | £12,000 | £0 | **£1,100** | £275 |
| E | £260 × 5, 0 | £1,300 | £12,000 | £0 | **£1,300** | £260 |

All five match the specification's table (section 20) and the JSON `direct_spend_minor`
and `economic_cost_minor` fields. In every route the catalogue action's
`fees_by_month_minor` equals the route's payments, and its `scenario_net_income_by_month_minor`
equals the route's income.

Hard caps (spec section 12, "Hard feasibility constraints"):

- Direct spend ≤ £1,500: largest is E at £1,300. All pass.
- Monthly payment ≤ £1,500: largest is A's £1,200 in month 1. All pass.
- Weekly workload envelope ≤ 40 h, study plus work while active: A 40 + 0 = **40** (equal
  to the limit, so it passes only under ≤); B 6 + 30 = 36; C 16 + 20 = 36; D 6 + 30 = 36;
  E 4 + 30 = 34. After completion every route works 30 h ≤ 40 h.

## 4 Conservative prefunding (TIME-1)

Rule: opening cash + early receipts − outflows ≥ reserve, every month. Every fixture wage
arrives late in the month (the pack's validator states this assumption; the JSON has no
timing field), so no wage counts toward the month it is earned. Lower bound = opening −
payment − living; closing = lower bound + income.

Route B in full:

| Month (2027) | Opening | Payment | Living | Lower bound | Income (late) | Closing |
|---|---:|---:|---:|---:|---:|---:|
| 1 Jan | £6,000 | £150 | £1,000 | **£4,850** | £2,000 | £6,850 |
| 2 Feb | £6,850 | £150 | £1,000 | £5,700 | £2,000 | £7,700 |
| 3 Mar | £7,700 | £150 | £1,000 | £6,550 | £2,000 | £8,550 |
| 4 Apr | £8,550 | £150 | £1,000 | £7,400 | £2,000 | £9,400 |
| 5 May | £9,400 | £0 | £1,000 | £8,400 | £2,000 | £10,400 |
| 6 Jun | £10,400 | £0 | £1,000 | £9,400 | £2,000 | £11,400 |

Minimum lower bound **£4,850 in January**, above the £500 reserve. This matches the spec
and `print_snapshot.minimum_prefunded_cash_minor` 485000.

The other routes (lower bounds by month, then the minimum):

| Route | M1 | M2 | M3 | M4 | M5 | M6 | Minimum (month) |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | £3,800 | £2,800 | £1,800 | £2,800 | £3,800 | £4,800 | **£1,800 (Mar)** |
| C | £4,700 | £5,000 | £5,300 | £5,800 | £6,800 | £7,800 | £4,700 (Jan) |
| D | £4,725 | £5,450 | £6,175 | £6,900 | £7,900 | £8,900 | £4,725 (Jan) |
| E | £4,740 | £5,480 | £6,220 | £6,960 | £7,700 | £8,700 | £4,740 (Jan) |

All are above £500, so all five routes are feasible. Route A's minimum falls in March,
after two unpaid months, not in the month of its £1,200 fee: a checker that tests only the
payment month would get A wrong.

## 5 Dates and the monthly grid (TIME-1)

| Route | Actual start | Actual finish | Active months (JSON) | Months touched | `time_months` |
|---|---|---|---|---|---:|
| A | 2027-01-01 | 2027-02-28 | 1, 2 | Jan–Feb | 2 |
| B | 2027-01-01 | 2027-04-30 | 1–4 | Jan–Apr | 4 |
| C | 2027-01-01 | 2027-03-31 | 1–3 | Jan–Mar | 3 |
| D | 2027-01-01 | 2027-04-30 | 1–4 | Jan–Apr | 4 |
| E | 2027-01-01 | 2027-05-31 | 1–5 | Jan–May | 5 |

Each finish date is the last day of its final active month (2027 is not a leap year, so
February ends on the 28th). Under TIME-1 the assessed outcome becomes usable at the next
month boundary, so B's readiness milestone is 1 May 2027, four months after the start. The
pack's validator does not check dates; this table is the only check of them.

## 6 Pareto layers by hand

TRACE-01 points (months, economic £): A (2, 5200), B (4, 600), C (3, 2200), D (4, 1100),
E (5, 1300). p dominates q iff p is no worse on both and differs on at least one.

| Route | Dominated by | Reason |
|---|---|---|
| A | none | fastest (2 months) |
| B | none | cheapest (£600) |
| C | none | only A is faster, and A costs more |
| D | B | same 4 months, £600 ≤ £1,100 |
| E | B, D | B: 4 ≤ 5 and £600 ≤ £1,300; D: 4 ≤ 5 and £1,100 ≤ £1,300 |

F1 = {A, B, C}. Without F1, D dominates E, so F2 = {D} and F3 = {E}. This matches the
spec, `P01.expected` and `worked_trace.expected.fronts`. E has **two** dominators, B and D.
The comparator rule in Sprint 7 must therefore choose between them deterministically and
expose the other (spec section 13).

## 7 Outcomes, readiness and the AI range record

- Target rows: query-data needs 2 and has 1; validate-data needs 2 and has 1;
  explain-results needs 2 and has 2. So exactly the two missing outcomes from the spec
  ("lacks independent querying and validation, while communication already meets its
  row"), and readiness is false now (`P01.expected.ready_now` false).
- The span [0, 138) covers the whole syllabus text, which is 138 bytes (UTF-8). Its SHA-256
  `96a22436…c783fb` matches `source_hash` (shasum). The text, "Learners independently query
  two related tables, validate keys and missing values, and submit an assessed report with
  reproducible checks.", supports both outcomes as **assessed** independent work
  (`evidence_kind` `assessed_work_sample`, level 2 = "independently handles routine tasks").
  Confidence `provisional`, `claim_state` `planned_conditional`, `review_state`
  `accepted_assumption`: consistent with OUT-1 (an accepted provisional mapping supports
  only a conditional route).
- Every route has `readiness_status` `conditional_on_assessed_completion`, and
  `completed_course_does_not_automatically_update_skill_evidence` is true (RDY-1, OUT-1).
- The AI range [5, 8] against a minimum of 6: the lower bound is 5 and 5 < 6, so the
  role **fails** the lower-bound filter (`lower_bound_filter_passes` false). This is the
  AI_RANGE regression case.
- Feasible non-empty action sets: the five courses share the exclusive group
  `fixture:core-training` (`at_most_one`), so only the five singletons are non-empty
  selections, as `expected.feasible_nonempty_action_sets` lists. The empty selection is
  also a valid search node but does not reach readiness.

## 8 A–I direct-spend fixture (reconstructed)

Source: spec section 12, "The three Pareto layers". It is in direct-spending-only mode;
all routes are stated feasible and reach the same target. Rebuilt as
`fixtures/reconstructed/directai.json`. It holds only what the table states.

| Route | Months | Direct cost | Dominated by (hand) | Layer |
|---|---:|---:|---|---:|
| A | 6 | £4,800 | none (fastest) | 1 |
| B | 9 | £2,400 | none: only A and D are faster, and both cost more | 1 |
| C | 12 | £900 | none (cheapest) | 1 |
| D | 8 | £5,400 | A (6, £4,800) | 2 |
| E | 11 | £3,000 | B (9, £2,400) | 2 |
| F | 14 | £1,200 | C (12, £900) | 2 |
| G | 10 | £6,200 | A (6, £4,800), B (9, £2,400), D (8, £5,400) | 3 |
| H | 13 | £3,600 | B (9, £2,400), C (12, £900), E (11, £3,000) | 3 |
| I | 16 | £1,600 | C (12, £900), F (14, £1,200) | 3 |

The column lists every dominator in the full set. Peeling: F1 = {A, B, C}. Among the
rest, D is fastest and F is cheapest. Only D is faster than E, and it costs more, so E is
not dominated. Within the remainder G, H and I are dominated by D, E and F respectively.
F2 = {D, E, F}. F3 = {G, H, I}: nothing remains to dominate them.

Correction (2026-10-27, same task): the first version of this table listed only A and D
for G and only B and E for H, and said G is faster than B. Those dominator lists were
incomplete; the layers were right. The error surfaced when the route-comparison
composition named B as G's comparator, and the arithmetic above was rechecked. This matches the
spec table and the nine values hard-coded in the pack's validator. The JSON values equal
both (checked by a one-off assertion over the file, 2026-10-27).

## 9 Plan section 8 counterexamples

| Family | Hand check | Result |
|---|---|---|
| PREFUND | Opening £100, fee £200 on day one, pay £300 on day 28, reserve £0. Prefunded: 100 − 200 = −£100 < 0. Month end: 100 − 200 + 300 = +£200 | fails prefunding although the month ends positive |
| PAYCAP | £2,400 option, £1,800 due immediately, cap £250/month, direct budget £3,000. £1,800 > £250; £2,400 ≤ £3,000 | fails the payment cap, passes the direct budget |
| WORKLOAD | Two courses of 20 h in the same week, 20 h available. Envelope: 20 + 20 = 40 > 20. Naive monthly test: 40 ≤ 4 × 20 = 80 | envelope rejects; the naive monthly sum wrongly accepts |
| PARETO | (1,3), (2,2), (3,1) are mutually nondominated; each is ≤ (4,4) on both axes | (4,4) is in F2, beaten three times; "beaten three times" is no exclusion rule |
| PARETO ties | (1,1) and (1,1) | both F1; equal points do not dominate each other |
| ECON (FIN-1 example) | 12-month horizon, £2,000 baseline. Six months out of work: 6 × £2,000 = £12,000 lost, plus £3,000 direct = £15,000. Part-time route keeping pay, £5,000 direct: £5,000 | the shorter route is not "cheaper" economically |
| AI_RANGE | [5, 8] against minimum 6: 5 < 6 | excluded under lower-bound filtering |

## 10 Persona expectations

| Persona | Expectation | Basis (spec) | Hand check |
|---|---|---|---|
| P01 | Fronts A/B/C, D, E; selected B; not ready now; print shows 4 months, £600 direct and economic, £150 peak, six-month basis, conditional readiness, £4,850 minimum | §20 TEST-1, FIN-1, TIME-1 | Sections 2–7: all hold |
| P02 | Personality skippable; slate ≤ 6; active targets ≤ 3; ≥ 3 occupation families *when the qualified pool supports it*; includes a less-familiar grounded role; no exact wording asserted; economic solve blocked until a baseline is confirmed | §4 REC-1, DIV-1; §12 FIN-1 ("When income/baseline assumptions are missing, show the unresolved economic comparison") | Consistent. Two cities (≤ 3), no targets (drafts may have none, §18), 12 study h/week. See finding H2 |
| P03 | Unconfirmed £800 grant contributes 0 to the unconditional ledger; bridge wages before an offer = 0; reject the £300 option with £200 upfront for the payment cap; never recommend borrowing | §10 funding statuses; §12 TIME-1 ("Do not borrow against an unaccepted job offer or an unconfirmed grant"), hard constraints | £200 upfront > £100 cap: rejected. £300 ≤ £300 direct cap: passes at equality. Also fails the reserve; see finding H1 |
| P04 | Refuse demoting the statutory registration gate; not verified ready; the pathway *may* exceed the 24-month model; unverified is not ineligible | §8 MAP-1 protected gates; §10 RDY-1; §1 BND-1 (beyond 24 months: explanatory sketch and unsupported-model state) | Gate `kind` statutory, `state` unverified; the requested edit sets `essential` false on it. Expectations follow directly. See finding H4 |
| P05 | `READY_NOW_FOR_MODELLED_REQUIREMENTS`; lead with "review current postings and apply"; no forced training; no degenerate Pareto chart; show evidence-recency limits | §10 RDY-1 apply-now | Both rows evidenced 2 ≥ required 2 and other gates confirmed, so R_g = true with zero selected actions |

## 11 Findings for implementers

None is a pack error. Each is a way a test written straight from the JSON could pass a
wrong implementation.

- **H1. P03 fails two hard constraints, not one.** Opening £200 − £200 upfront = £0,
  below the £100 reserve, before any living cost (P03 has no living or income data). So
  the option also fails the reserve and prefunding check. `expected.reject_reason`
  names only `monthly_payment_cap`. Test: the feasibility report lists *every* violated
  hard constraint, and the test asserts that `monthly_payment_cap` is among them. Do not
  assert that it is the only one, or the result depends on check order.
- **H2. P02's `current_net_income_minor: 0` is not a confirmed baseline.** It sits beside
  `income_baseline_status: "unconfirmed"`. A loader that reads the integer and ignores the
  status turns unknown into zero, and then an economic solve becomes possible.
  `economic_solve_blocked_until_baseline_confirmed` must hold whatever the integer says,
  until a baseline is confirmed or direct-spending mode is chosen explicitly.
- **H3. Boundary equalities.** Route A's workload is exactly 40 h of 40 h, and P03's
  direct spend is exactly the £300 cap. Both pass only under ≤ (the spec writes ≤). Keep
  both equalities in the TRACE01, WORKLOAD and PAYCAP tests, with a one-unit-over
  counterpart that fails.
- **H4. P04 is three distinct states.** "May be outside the 24-month model" is
  conditional. Test that the gate stays unresolved and cannot be demoted, that the result
  is never "ineligible", and that a pathway longer than 24 months yields the out-of-model
  state (`MODEL_SCOPE_EXCEEDED`, spec §18). These are separate assertions, not one
  "not ready" check.
- **H5. TRACE-01's £4,850 assumes late wages.** The JSON has no income-timing field. The
  fixture adapter must declare late-month receipt explicitly. With early receipt, January
  would be £6,850 and the printed figure would be wrong.
- **H6. Route A's cash minimum is in March, not January** (section 4). A checker must
  evaluate every month of the horizon.
- **H7. Several routes have more than one dominator**: TRACE-01 E (B and D); DIRECTAI G
  (A, B, D), H (B, C, E) and I (C, F). The Sprint 7 comparator rule must choose one
  deterministically and expose the others. A dominator need not sit in the layer just
  above: B (F1) dominates G (F3).
- **H8. Namespacing.** TRACE-01 routes use bare IDs `A`–`E`. Any store holding both
  fixtures must qualify them by trace (for example `TRACE-01/B`). DIRECTAI IDs are already
  qualified.
- **H9. The validator does not check** dates, P01 versus the trace's cash inputs,
  post-completion workload, P02 or P04 beyond gate kind, or the A–I values against the
  spec. Sections 2, 5, 8 and 10 check those by hand. The validator certifies fixture
  arithmetic only. It does not certify any application gate (pack README; spec §20).
