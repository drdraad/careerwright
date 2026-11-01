# Task 12c report: a tuition fee loan is a loan to repay (backend, no interface)

- Branch `wt-12c` in `/home/user/careerwright-wt/12c`, rebased onto
  `claude/confident-ramanujan-ux3saw` at 0118ea0. Head: b2b4eeb.
- Status: DONE_WITH_CONCERNS (the concerns: integration and acceptance not run, Docker down;
  migration 0040 not yet run against PostgreSQL; Task 6f may also take number 0040).

## For the product owner, in plain words

What changed: a student can now say "a tuition fee loan pays my university fee straight to the
university". Careerwright then:
- leaves that fee out of their cash, their spending limit and their monthly limit;
- shows it as a loan to repay later, with its amount and the month it is paid;
- if the loan isn't approved yet, shows the route as "if your loan is approved", beside the
  route where they pay the fee themselves;
- if they don't know the amount, says it can't tell yet, never £0.

A maintenance loan, or any other loan, is still not counted as money towards the plan.

How the loan counts in the "cost over the plan": the full fee still counts, once. A loan is
paid back, so it changes when the fee is paid and from whose pocket, not what the change
costs. This changes no result on any existing test example, because none has a loan.

One question for you:
1. Should an Advanced Learner Loan count the same way? As far as I know it is also paid straight
   to the college for the course fee (I could not check this here). Yes would treat a college
   course's fee paid by that loan as a loan to repay, not the person's own spending. Today it
   stays "information to check", as you decided for every loan except the tuition fee loan.

## What I implemented

Files changed (backend, docs, generated client):
- `backend/src/careerwright/planning/catalogue.py`: `TuitionFeeLoan` (amount, null when not
  known; eligibility and application, the funding statuses; an approval needs confirmed
  eligibility), on `Variant.tuition_fee_loan`. Not a `Support`: a support of kind `loan` is
  still refused.
- `planning/inputs.py`: `TuitionFeeLoanInput` on `VariantInputs.tuition_fee_loan`, read into the
  variant as the person's assumption (`accepted_assumption`). It is stored through Task 12a's one
  command (expected version, Idempotency-Key, `run_idempotent`, `actor_transaction`); no new
  command or endpoint.
- `planning/compiler.py`: the compiled variant carries the loan (default null, so a snapshot
  sealed before reads); its review state joins the variant's.
- `planning/ledgers.py`: `LoanToRepay` (option, month due, amount, repayment always null in L0,
  conditional).
- `planning/checker.py`: the loan pays the fees and instalments (never extras) left after
  support to the provider, up to its amount; that money is in no payment row, cash row, support
  row or receipt; `loans_to_repay` on the check; a loan not yet approved adds a `Condition` of
  kind `loan` (`confirm_loan_approved`) and the qualification `conditional_loan`, counts in base
  and delay (delayed like an award), not in `no_award`; an unknown amount is
  `loan_amount_unknown` (unresolved), with the direct cost and month rows null; the economic cost
  adds what the loan paid, once. New helper `_net_paid` replaces two copies of the same sum.
- `planning/search.py`: `loan_amount_unknown` joins rule 2's own findings; `PRUNING_VERSION`
  `sound-pruning-5`; `Schedule.loans_to_repay` (default empty, so an older stored result reads).
- `planning/families.py`: the loan and its application state are material financing.
- `migrations/versions/r0040_tuition_fee_loans.py`: two CHECKs on the inputs document (the
  loan's statuses are among the four of each; approved needs confirmed eligibility). The
  existing CHECKs already keep its money GBP and non-negative and refuse a loan as support.
- `apps/web/src/generated/*`: regenerated (`pnpm run generate`), after the rebase too.
- `docs/adr/0013-...md`: the Task 12c amendment (eight rulings, the economic cost in plain words)
  and a pointer in decision 5. `docs/adr/0016-...md`: the Task 12c amendment (classing, the
  oracle).
- `docs/requirements-register.md` (last commit, after the rebase): FUNDING-06 and FUNDING-04.
- Tests: new `backend/tests/domain/test_planning_tuition_loan.py`; additions to
  `test_planning_inputs.py`, `test_route_oracle.py`, `tests/support/planning.py`,
  `tests/support/route_oracle.py`, `tests/integration/test_planning_inputs.py`.
- Proposed CLAUDE.md words: `/home/user/careerwright/planning/task-12c-claude-md-proposal.md`
  (CLAUDE.md is not edited).

DBOS `application_version` stays `careerwright-l0-1`: no workflow's step sequence changed.

## Rulings (each costs little if wrong)

1. **Statuses count as for an award, without the "assumed" flag.** Approved (needs confirmed
   eligibility) counts everywhere. Not yet approved (not applied or applied), not refused, with
   confirmed or potential eligibility, makes the route conditional. Refused, ineligible or
   insufficient information: it does not count (ADR 0013 decision 5). Why no `assumed` flag: the
   brief says any loan not yet approved makes the route conditional; the person stating the
   loan is already the choice.
2. **"Beside the self-paid route" is the `no_award` scenario** (decision 5's FUNDING-05
   mechanism). The search reads the base scenario only (ADR 0016 decision 3), so its schedule is
   the conditional one; `evaluate_route` gives both.
3. **The economic cost counts the fee the loan pays, once** (spec section 12: "loan principal is
   a liquidity source, not a discount"). Section 22 changes only cash and spending limits. No
   fixture or regression family has a loan, so no best trade-off changes (R14); no question
   needed. Interest and repayment are not modelled: a known limit, null on the loan.
4. **An unknown amount is always unresolved** when the loan counts, even on an option with no
   stated fee (simplest, and never £0). The known part takes the loan to pay every fee, the least
   the person could pay, so a cap broken even then is broken.
5. **Order:** support to the provider first, then the loan, then the person; extras are the
   person's. A grant paid to the person is set against the whole fee once, whoever pays it, and
   the person's direct spending never goes below £0. With no loan, every figure is as before.
6. **For a "from £X a month" plan with no count**, the single-instalment cap check uses what the
   person pays after a loan that pays from the start.
7. **No restriction by option kind**: a loan on an option with no fee pays nothing.
8. **"The oracle is written again"** read as: the loan rule is written fresh into the existing
   independent oracle, from section 22 and FIN-1, reading only the loan's raw fields (not
   `confirmed`/`conditional`), sharing no code with the checker. The rest of the oracle is
   unchanged.
9. **Schema version stays "1"**: the field is optional and null by default, so every stored
   document still reads.

## Checks run

- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` with Node 24 on PATH:
  - before the rebase: passed (backend 1,756 passed, 8 skipped; Vitest 442 passed);
  - after the rebase: passed (backend 1,760 passed, 8 skipped, 421 deselected; Vitest 447);
  - after the register commit: passed (same counts).
  - The 8 skips are pre-existing: `test_session_2_pack.py`, page bodies kept only on the
    curating machine.
- TDD evidence:
  - RED, checker and inputs (types in place, behaviour not):
    `pytest tests/domain/test_planning_tuition_loan.py tests/domain/test_planning_inputs.py`:
    12 failed, 20 passed (the passing ones: the three statuses that must not count, and the
    maintenance loan refusal, which held already). GREEN after the checker: 32 passed.
  - RED, oracle: with loans in the generated instances and no oracle rule,
    `pytest tests/domain/test_route_oracle.py`: 2 failed (search vs oracle; checker vs
    independent checker), 5 passed. GREEN after the oracle rule: 8 passed (one new test).
- Coverage probe (not committed): over 300 generated instances, loans in every application
  state, 32 to 44 options set aside for an unknown loan amount, and archived routes with
  confirmed and conditional loans. The fixed `loan_statuses` instance is an `@example` on the
  two oracle properties, so every state is reached on every run.
- TRACE-01, the A–I fixture and every regression family: unchanged, their tests pass in
  `make check`.

## Not run

- **Integration and acceptance not run: Docker down.** Tests I changed that did not run:
  - `tests/integration/test_planning_inputs.py::test_every_input_round_trips_through_its_command_and_a_stale_version_is_refused`
    (now round-trips a loan and refuses a stale version with it);
  - `::test_a_loan_is_refused_as_support_before_anything_is_stored` (marker and comment only);
  - `::test_the_database_repeats_the_domain_rules` (three new cases: a loan's unknown
    application state, an approval without confirmed eligibility, a negative amount).
- Migration 0040 has not run against PostgreSQL 16. Its jsonpath uses the same `!=` form as
  migration 0033's CHECKs.
- No live calls; cost £0.

## Concerns

- Task 6f (main tree) may add a migration too (its card says so). If it takes 0040 first, mine
  is renumbered at the next rebase.
- The stale-version refusal for this field is only covered by the integration test, which did
  not run. The write path itself is Task 12a's and unchanged.

## Changed test inputs or assertions (disclosed)

- `test_route_oracle.py`: the generator now gives about one option in three a tuition fee loan
  in any state, and an option with a loan always has one or two fees drawn up to £3,000 (others
  as before). This changes which instances Hypothesis explores for the existing properties. The
  search-vs-oracle property also asserts what each archived route's loans pay; the
  checker-vs-oracle property asserts it for every candidate. No assertion was removed or
  softened.
- `tests/integration/test_planning_inputs.py::everything()`: each option's answer now names its
  `tuition_fee_loan` (null on one, a loan not yet approved on the other), so the round trip
  covers it.

## Skip when reviewing

`apps/web/src/generated/` (regenerated client).

## Fix round 1

Branch `wt-12c` rebased onto `claude/confident-ramanujan-ux3saw` at 6a3fef8. Head: b0f7715
(fix 5f20fd6, register b0f7715). Migration 0040 is still free on the integration branch.

### Changes
1. **Critical 1 (a grant beside a loan broke spend-cap pruning).**
   - The bug: ruling 5 set a grant paid to the person against the whole fee, the loan's part
     included. That could make an option's own direct spending negative, and the search's
     spend-cap rule summed a clamped £0. It then cut a feasible route and said "no route"
     with complete coverage.
   - The fix (`checker.py`): a grant paid to the person lowers direct spending only by what the
     person pays of that option's fees, as before Task 12c. So no option's spending goes below
     £0, and rule 3 holds again.
   - The economic cost still sets the grant against the whole fee, once.
   - The oracle reads the same rule its own way (`route_oracle.py`: "the tuition the student
     pays" apart from "the tuition after grants at the provider").
   - The reviewer's case is now `tests/support/planning.py::grant_beside_loan`, an explicit
     example on both properties (search vs oracle, checker vs oracle).
   - The pruning rule itself is unchanged, so the version stays `sound-pruning-5`.
   - ADR 0016's rule 3 line and ADR 0013's ruling 2 now say this in plain words.
2. **Minor 1 (a false condition).** A loan not yet approved now adds the `loan` condition (and
   so `conditional_loan`) only when it pays something or its amount is unknown. The oracle
   gained `rests_on_loan`, and the checker-vs-oracle property compares it on every candidate.

### Tests and checks
- New: `test_planning_tuition_loan.py::test_a_grant_beside_a_loan_never_takes_an_option_s_direct_spending_below_zero`
  and `::test_a_loan_not_yet_approved_that_pays_nothing_makes_nothing_conditional`, plus the
  `grant_beside_loan` examples.
- RED before the fix: 5 failed.
  - The two new tests.
  - The extra-cost test (its changed assertion, below).
  - Search vs oracle: it failed on the reviewer's example (the oracle found
    `[course, degree]` and the search found no route).
  - Checker vs oracle: it failed on the new `rests_on_loan` field.
- GREEN: planning and route domain tests, 225 passed.
- The reviewer's `/tmp/r12c/repro.py` now gives `no_route_in_bounded_model` from both the
  search and the oracle. Under the corrected rule, the £1,000 grant can't pay for the £1,200
  course, so the course breaks the £1,000 cap.
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` after the rebase: passed
  (backend 1,762 passed, 8 skipped (the same skips as before); Vitest 447).
- Integration and acceptance not run: Docker down.

### Changed test assertion (disclosed)
- `test_a_loan_never_pays_an_extra_cost_and_a_grant_to_the_person_counts_once`: direct cost
  £0 → £50. The grant may no longer lower the £50 extra, because it lowers only the tuition the
  person pays (none). It also asserts the support row is £0. The economic cost is unchanged
  (fee + £50 − £500).

### Not done (listed for later)
Minors 2, 3 and 4, as the fix round says.

## Follow-up: the Advanced Learner Loan

You said "I think so" (1 November 2026). An Advanced Learner Loan paid straight to the college
is now a loan to repay, just like a tuition fee loan. This is recorded as your provisional
yes; session W2 asks it again.

Branch `wt-12c`, rebased onto `claude/confident-ramanujan-ux3saw` at 5480e16. Head: ecbdbc1.
- 0434949: the change.
- 3104d0c: the migration renumbered to 0044. Task 6e's fix round took 0043 while I worked.
- ecbdbc1: the register, last.

### What changed
- **Ruling: one statement with a kind, not a second rule.**
  - `TuitionFeeLoan` and `TuitionFeeLoanInput` gained `kind`: `FeeLoanKind`, either
    `tuition_fee_loan` (the default) or `advanced_learner_loan`.
  - The default means every stored document and stored result keeps its meaning.
  - Everything else is shared, not copied: what it pays, its statuses, an unknown amount,
    the economic cost, the search.
  - The field keeps its name `tuition_fee_loan` (the smallest change). Tasks 12b and 14 read
    `kind` to word it.
- `LoanToRepay` carries the kind, defaulting to a tuition fee loan for older results.
- A family's financing says `advanced_learner_loan:<application>`.
- **The oracle:**
  - It reads both loans its own way (a set of the two loans paid to the provider) and
    refuses any other kind.
  - Its generated instances draw either kind in every state.
  - The fixed `loan_statuses` instance gained an Advanced Learner Loan, applied for.
- **Pruning:** rules unchanged, so the version stays `sound-pruning-5`.
- **Migration 0044:** a CHECK that a fee loan is one of the two kinds. It is forward-only; a
  missing kind passes, because it means a tuition fee loan.
- **Other loans:** maintenance loans and every other loan are still refused as support, and a
  fee loan of any other kind is refused.
- **Docs:** one paragraph in ADR 0013's Task 12c amendment (it replaces the old known limit
  that said the Advanced Learner Loan was refused). The CLAUDE.md proposal now names both
  loans.
- **Client:** regenerated.

### Tests and checks
- RED: with the new tests and generator in place, collection failed, because `kind` was not
  yet a field.
- GREEN:
  - `test_planning_tuition_loan.py::test_an_advanced_learner_loan_paid_to_the_college_is_a_loan_to_repay_too`
    (on neither side, conditional beside the self-paid route, unknown amount, family);
  - `::test_the_person_states_which_fee_loan_and_any_other_kind_is_refused`;
  - the oracle's `test_the_oracle_reads_a_tuition_fee_loan_in_every_state` (the new
    Advanced Learner Loan case);
  - all three oracle properties, with both kinds.
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` after the rebase: passed.
  Backend 1,851 passed, 8 skipped (the same skips as before); Vitest 466.
- Not run, as the dispatch says (the controller runs them): integration and acceptance.
  - In `integration/test_planning_inputs.py`, the round trip now uses an Advanced Learner Loan
    for its not-yet-approved loan.
  - The database-rules test gained a case: a `maintenance_loan` kind is refused.

### Changed test inputs (disclosed)
- `everything()` in the integration test: the loan on its second option is now
  `kind: advanced_learner_loan`. The stored document now carries `kind`, so the round trip
  needs it named, and this way it covers the new kind.
- The oracle generator now also draws the kind, so it explores different instances.
- `loan_statuses` gained one option, which grows the combinations the oracle checks.
