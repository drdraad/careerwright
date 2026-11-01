# Task 12a review: the person's planning inputs (backend)

Branch `wt-12a`, commits 98fd0a9..edfebc7 (four commits). I read the brief, the dispatch, the
report and the 4,828-line diff in four passes: the rules (checker, compiler, ledgers, pack,
search, oracle), the store (inputs, commands, store, migration, API), the tests, then the ADRs
and the register. I read code outside the diff for four named risks only, and ran one read-only
probe script (a scratchpad file, `python -I -B`, in the worktree's environment; nothing was
written to the worktree) to confirm three of the findings below.

### Spec Compliance
- ❌ Issues found:
  - Deliverable 7 (month rows): while two supports paid to the person wait for stacking, the
    cash ledger still shows their sum as each month's receipts. The direct ledger nulls the
    same support (Important 1; `planning/checker.py:635-637`, `:363`, `:421`;
    `planning/ledgers.py:160`, `:165`).
  - Deliverable 4 (stacking, "exclusivity and eligible-cost caps follow the same rule"):
    only supports on one option are checked. The same scheme counted on two options of one
    route passes as feasible (Important 2; `checker.py:635`).
  - Deliverable 5 with ruling 1 (classing for the search): when existing repayments alone
    break the payment cap, the search says `unresolved` if any option is set aside for an
    unknown. The oracle says "no route", and nothing can repair that. Before this task the
    search said "no route" (Important 3; `planning/search.py:369-372`, `:628-640`).
  - Deliverable 3 (D12-D17) is applied in code and in ADR 0013's status line. The decision
    bodies and three register rows still call them provisional (Minor 1).
- ⚠️ Cannot verify from diff:
  - `make check` and `make acceptance` (the implementer's runs; not re-run, as instructed).
  - The Playwright console-error failure on Ben's empty home page at 1440x900. The page calls
    no planning endpoint, and the second full run passed. Its cause is unknown.
  - Integration: `l0-local-release` has moved to ba0846e (W2E fix round 1) since this
    branch's base, 98fd0a9. Those commits touch the web, the fixture interviewer and design
    screenshots, not this branch's files, and no migration 0033 has landed there. A rebase
    should replay cleanly, but `make check` must run again after it.
  - The checkpoint's words and the next actions (Task 12b), and the solve's stage checks
    (Task 14).

### Strengths
- The unknown-versus-unresolved discipline holds at every input. Not stated is null. "No
  debts" is `[]`. Seven inputs block a solve and are named. An unstated cap, reserve,
  availability, baseline or work right leaves every route unresolved. `not_held` is
  unresolved, never ineligible. Nothing reads a city.
- The C07 rule is careful. It applies only to a *stated* fee, and the stated payments stay a
  lower bound, so a breach on them is genuine. An approved full waiver makes it moot. The
  real pack test shows C07 set aside for `eligibility_unconfirmed` and `workload_unknown`.
- Repayments alone above the cap are named in the checker. An undated payment is no longer
  blamed. The search reports them once, as the starting position, and never on an option.
- The new rules are written again in the oracle, with their own constants and their own
  `_counted`. The generator now holds apprenticeships, zero to two supports, conditions,
  entry yes/no/none, large repayments and work rights. Each rule is classed for the search
  with a sound argument (rule 1 for work rights; rule 2 for the variant-own codes; rule 3
  for repayments; rule 4 for job transitions). `PRUNING_VERSION` is bumped.
- The command contract is right. Every write takes an expected version and an
  Idempotency-Key, through `run_idempotent`, with the workspace row locked. A unique
  violation maps to `STALE_INPUT_VERSION`. Nothing changed gives 200 and no version. One
  event carries the version only. Errors carry codes only and never echo input.
- The migration is append-only under row-level security, follows the existing policy
  pattern, and has CHECKs for money, hours, delay, work rights, remote work, loans and
  approvals. All of these are tested against the database, with isolation from another
  actor.
- R11 is kept: the API returns codes (`needs`), numbers and money. The only free text is
  the person's own override reason.
- The ADR 0013 settlement records each ruling with its reason and its known limits.

### Issues

#### Critical
None.

#### Important

1. **A receipt that may not come is shown as a known month figure.**
   - Where: `planning/checker.py:635-637` (the stacking branch calls `_unknown_payments()`
     but leaves `receipts_known` true), `:363`, `:421`; `planning/ledgers.py:160`, `:165`.
   - What the probe showed: a £600 course with a £300 grant and a £200 bursary, both paid to
     the person, stacking not confirmed.
     - The route is unresolved (`stacking_unconfirmed`).
     - The direct ledger's `support_minor` is `[None, None]`.
     - The cash ledger's `later_receipts_minor` is `[50000, 0]`: £500 in January, shown as
       known.
   - Why it matters: this breaks the brief's acceptance ("a month row resting on an unknown
     amount is null, never a partial figure") and the ledger's own docstring ("a figure
     resting on an unknown payment or receipt ... is null"). The person would read £500
     arriving in January when only one of the two supports may apply.
   - Fix: add a display-only flag for the receipt rows, false while a variant with a
     support paid to the person waits on stacking. Keep `receipts_known` as it is for the
     reserve check: with every support counted, the cash is the most the person could
     have, so a reserve breach there is still sound. Add the case to
     `test_a_month_row_resting_on_an_unknown_amount_is_null_never_a_partial_figure`.

2. **One scheme counted on two options in one route passes as feasible.**
   - Where: `checker.py:635` checks only supports on one variant. The oracle mirrors it
     (`tests/support/route_oracle.py:333`). ADR 0013's settlement item 7 records cross-option
     exclusivity as a known limit, and PLN-06 still lists it as open.
   - What the probe showed: the F01 fee waiver, approved, on two £500 courses in one route.
     The route is `feasible` and `affordable_and_feasible_with_qualifications`, with no
     finding and a direct cost of £0.
   - Against the card: item 4 says "Exclusivity and eligible-cost caps follow the same
     rule". The carry-forward places that sentence under "supports summed on a variant", so
     the per-option reading is defensible. But spec section 12 lists "funding exclusivity"
     as a hard feasibility check, and section 10 says never assume schemes stack.
   - Who it affects: a person who says "if I get Free Courses for Jobs" on two courses gets
     a route that assumes one scheme pays for both. The pack alone cannot produce this today
     (C01's fee is unknown in 0.2.0). Supports the person states can.
   - Fix, in the checker and written again in the oracle:
     - Fail-safe: the same instrument counted on more than one variant of a route is
       unresolved. Use a new code or `stacking_unconfirmed` with the instrument as its
       reason.
     - It is not any one variant's own finding, so rule 2 is unchanged, and an unresolved
       route is never pruned.
   - Needs a ruling: cross-scheme exclusivity across options (C01's "not undertaking any
     other government-funded training"). A one-line ruling decides whether it becomes an
     input or a recorded known limit that the web states.

3. **The search says "unresolved" when the person's own repayments already rule out every
   route.**
   - Where: `search.py:369-372` (a set-aside option is a violation only for
     `_OWN_VIOLATIONS`, which does not hold `repayments_above_payment_cap`) and
     `search.py:628-640` (`_outcome`). The oracle counts the repayments as the option's own
     breach (`route_oracle.py:164`), so its `something_unknown` is false.
   - What the probe showed: a £15 monthly repayment against a £10 cap, with options "fine"
     (£2) and "unpriced" (cost unknown).
     - The search: `unresolved`, with complete coverage.
     - The oracle: no archive and nothing unknown, so "no route".
   - Why it is new: before this task the single check's `monthly_payment_cap` set the option
     aside as a violation, so the outcome was "no route". Renaming the code changed the
     outcome.
   - Who it affects: the person is asked to confirm a cost that cannot change the answer.
     The truth is: no route while repayments alone exceed the cap.
   - Why the tests miss it: the property test checks one direction only
     (`tests/domain/test_route_oracle.py:292-296`).
   - Fix:
     - In `_outcome`, after the blocking-input check, return `NO_ROUTE_IN_BOUNDED_MODEL`
       when complete coverage has a starting violation no route can repair (repayments
       above the cap, rule 3), whatever is set aside.
     - Add the converse assertion: if the oracle has no archive and nothing unknown, the
       search says no route. It may surface other conservative gaps; each would need a
       ruling.

#### Minor

1. **D12-D17 are still called provisional in documents.** ADR 0013's decision bodies still
   read "Provisional (R6)" (`docs/adr/0013-planning-input-ledgers-and-checker.md:85`,
   `:114-115`, `:120-121`, `:143`, `:149`), as do the register's FIN1-06, FIN1-10 and
   PLN-08 (`docs/requirements-register.md:251`, `:255`, `:547`).
2. **Register tidiness.**
   - BND1-04 is marked verified but keeps "Open: no residence or work-rights field exists
     yet" (`requirements-register.md:112`).
   - PLN-11's row has six cells in a five-column table (`:550`, header `:538`).
3. **How debts are named.**
   - The repayments finding names debts by position (`debt:1, debt:2`,
     `planning/inputs.py:472`) in one comma-joined `reason` (`checker.py:974`). A list of
     IDs would be cleaner facts (R11). `DebtInput` has no label, so Task 12b must show
     debts in stored order.
   - `monthly_repayment` is required (`inputs.py:110`). A person who knows of a debt but not
     its repayment can only leave every debt unstated, which blocks the solve, or enter a
     figure. This is a question for Task 12b.
4. **The migration does not repeat every domain rule.** Its CHECKs leave out the
   `objective_basis` values, the interest range, "in full or an amount", "paid to the person
   needs a month" and "an override names its kind and reason"
   (`migrations/versions/r0033_planning_inputs.py:40-84`). The money, loan, approval and
   work-rights rules are there.
5. **A job with no offer gate would not count as a transition.** The catalogue allows a
   `work` offering with no offer gate, although `ActionKind.WORK` says "behind an offer
   gate" (`planning/catalogue.py:83`, `:187`). Such a job would not count as a conditional
   job transition (`checker.py:491`). No source makes one today; Task 12b's "add an option
   yourself" could. A validator would close it.
6. **Generator reach is not guarded.** The report's probe that the generator reaches every
   new code is not committed, so a later change to the generator could silently drop that
   coverage. Pinned `@example`s or a reach check would guard it.
7. **The right to work can be asked three times** (concern 1, judged): the planning input,
   the capability row, and C07's `eligibility_work_rights` condition. Each can only
   withhold a result, never give one, so it is safe. Task 12b should prefill them or show
   them together.
8. **The export leaves out the planning inputs** (concern, judged). Capability evidence is
   missing too (`api/routes_export.py`), while the export's events list
   `planning.inputs_updated`. SEC-06's owner (Tasks 15 and 16) should add both. Carry it in
   the ledger.
9. **`CLAUDE.md` still calls `careerwright/planning` pure.** It now has `store.py` and
   `commands.py`. The controller updates it in the main tree.
10. **Question for the controller (C09; it changes feasible or not).** Without a recorded
    admission, an option behind an application gate stays `prerequisite_not_usable`, a
    violation that rule 6 prunes. The person never sees a route through it. The ledger's
    ruling said "else the route stays conditional". The implementer read the dispatch's
    "never feasible as stated" as the existing violation, which is defensible. Confirm it in
    one line, or make it a condition, as an offer gate is.
11. **Process** (the report's own concerns). The input-model and integration tests had no
    failing-first run. One heredoc edit was reverted and redone with the Edit tool, with no
    lasting effect. Record the 1440x900 console-error failure as an unexplained flake to
    watch.
12. **Pre-existing, outside the diff, for Task 14.** A job or apprenticeship with no
    confirmed take-home wage counts as no pay (`checker.py:775-777`). Its income rows and
    economic cost then read as known figures that rest on that unconfirmed wage. Task 14
    should decide whether to qualify them or leave them null.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The store, the commands and most of the new rules are correct and well
tested. But three narrow cases tell a person something false: a receipt shown as known, one
scheme paying for two courses, and "unresolved" where the truth is no route. Each fix is
small and local, in the checker or search with the oracle beside it.
