# Carry-forward for Task 12

- **Planning assumptions, stored and confirmed (from Task 11, ADR 0013 decision 11).** Task 11
  built `careerwright/planning` and one read endpoint, `GET /v1/workspaces/{id}/planning/options`.
  Nothing stores the person's planning inputs: see ADR 0013 decision 11's list, which covers
  baseline, cash, living costs, reserve, availability, commitments, existing debts, the
  limits, work patterns, funding statuses, entry confirmations, the continuation scenario,
  the objective basis and the delay months. Task 12's Options chapter collects and confirms
  them, and persists them as validated commands (an expected version and an
  `Idempotency-Key`, through `run_idempotent`). The model never fills them. An unasked
  direct-spend cap, payment cap or reserve leaves a route unresolved (Task 11 fix round 1, I2).
- **Outcome accept and override persistence** (from Task 9, concern 4): at this task's
  checkpoint.
- **Session 2's D12–D17** (Task 11's provisional planning decisions): apply the product
  owner's answers before the Options chapter shows a result that rests on them. C04 paid in
  full breaks P01's £1,500 direct-spend cap whatever D12 says. What matters for C04 is
  whether the fee falls as a single payment.
- **Funding stacking** (Task 11 review M9): supports are summed today. When a person
  confirms more than one support on a variant, leave the route unresolved until stacking
  is confirmed (spec: "never assume … two schemes can be stacked"). Exclusivity and
  eligible-cost caps follow the same rule.
- **The monthly payment cap's meaning** (Task 11 re-review 1, N1): the checker applies
  `P_m + R_m ≤ M_m`, with existing debt repayments inside the cap (the spec's default,
  pending session 2's D15). The You chapter asks for the cap as "the most in any one month"
  spent on the change. Align the question's words with D15's answer, and give a cap broken by
  repayments alone a finding that names the repayments.
- **"Does not meet the entry requirements"** (Task 11 re-review 1, N2): today it reads as
  `entry_requirements_unconfirmed`. Give the person's explicit "no" its own finding, still
  unresolved, with "verify whether the provider accepts equivalent experience" as the next
  action.
- **Ledger month rows** (Task 11 review M10): when ledgers are served, a month row that
  depends on an unknown amount carries null or its own `complete` flag, never a partial
  figure shown as a known one.

## From Task 7c (pack 0.2.0)
- Pin option pack 0.2.0 (hash in PINS). D12–D17 yes confirm ADR 0013's planning rules (D16, D17 also Task 13a).
- T5: P01's debt repayments are not stated, so "none" is an assumption — unknown is never zero (also Task 13a's P01 inputs). T9: TRACE-01's levels cannot move to other rubrics. T28, T29: C01's outcomes assessed per its overview (with Task 10).
