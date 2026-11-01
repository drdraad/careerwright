# Task 12c review: a tuition fee loan is a loan to repay (backend)

Reviewer: independent (R16), read-only. Worktree `/home/user/careerwright-wt/12c`, branch
`wt-12c`, 0118ea0..b2b4eeb. I read the brief, the binding dispatch, the report, the CLAUDE.md
proposal and the whole 2,548-line package in three passes (sources; tests and oracle; ADRs and
register). The implementer's report was treated as unverified claims.

Checks I ran (scripts in `/tmp/r12c`, outside the tree, no bytecode written; nothing in the
worktree changed):
- `repro.py`: two constructed options through `check_route`, `search_routes` and the oracle
  (the reproducer for Critical 1). Run twice, with two readiness set-ups.
- `before.py`: a loan paying a fee due before the planning start (Minor 2).
- Not run: the implementer's suites, `make check` (not re-run, per the contract).
  **Integration and acceptance not run: Docker down.** Migration 0040 has never run on
  PostgreSQL; I read it closely instead.

### Spec Compliance
- ❌ Issues found: the search no longer gives exactly the oracle's archive and outcome when a
  grant paid to the person sits beside a tuition fee loan. It can say "no route in this
  bounded model", with complete coverage, while a feasible route exists (Critical 1;
  `backend/src/careerwright/planning/checker.py:744`, `:927`;
  `backend/src/careerwright/planning/search.py:895-901`). ADR 0016's amendment says rule 3
  "still holds" (`docs/adr/0016-route-search-core.md:405`); it doesn't.
- Otherwise compliant against the brief and the dispatch's nine decisions:
  - Only the tuition fee loan changes. A support of kind `loan` (maintenance loan included) is
    still refused, in the domain and by 0033's CHECK.
  - The fee the loan pays is in no payment row, no cash row, no support or provider-support
    row, and no receipt. The economic cost adds it back once.
  - Approved counts in every scenario. Not yet approved and not refused, with confirmed or
    potential eligibility, it counts in `base` and `delay` with a `loan` condition
    (`confirm_loan_approved`) and `conditional_loan`; `no_award` is the self-paid route.
    Refused, ineligible or insufficient information doesn't count.
  - An unknown amount is `loan_amount_unknown`: unresolved, with direct cost and month rows
    null, never £0.
  - `LoanToRepay` carries facts only (amount, month, `repayment: null`, conditional). No new
    sentences (R11).
  - The write goes through Task 12a's unchanged command (expected version, `Idempotency-Key`,
    `run_idempotent`, `actor_transaction`).
  - The pruning version was raised to `sound-pruning-5`; `loan_amount_unknown` is correctly a
    variant's own finding for rule 2. DBOS `application_version` is unchanged, which is right:
    no step sequence changed.
  - No expected value changed in TRACE-01, the A–I fixture or any regression family. The only
    changed test inputs are the oracle generator and the integration `everything()` document,
    both disclosed.
  - CLAUDE.md not edited; a proposal was written.
- ⚠️ Cannot verify from diff:
  - Migration 0040 on PostgreSQL 16 (Docker down). Reading it:
    - It is forward-only (downgrade raises) and chains 0039 → 0040. Number 0040 is still free
      on `claude/confident-ramanujan-ux3saw`: only planning files changed there since 0118ea0.
    - It only adds CHECKs to an existing table, so row-level security is untouched.
    - Its jsonpath copies 0033's `lax … != …` form. 0033's recursive `$.**` money CHECK covers
      the loan's amount.
    - Like 0033, it lets through a missing or non-string `eligibility`/`application` (in lax
      mode a missing key never compares true). Pydantic refuses those first, so this is a
      list item (Minor 3).
  - The stale-version refusal with a loan in the document, and the three new CHECK cases: only
    in `tests/integration/test_planning_inputs.py`, not run.

### Strengths
- The checker change is small and well placed. The loan sits after provider support and
  before the person, never on extras, and the unknown-amount case is a sound lower bound (the
  loan takes every fee, so any cap broken then is really broken).
- The oracle's rule reads only the loan's raw fields and imports nothing from the checker. A
  fixed `loan_statuses` instance is pinned as an `@example`, so every status runs on every run.
- Old sealed snapshots and stored results still read (defaults on `CompiledVariant` and
  `Schedule`). `RouteCheck` is never persisted, so its new required field is safe.
- The tests use hand-worked values. They cover all three scenarios, the delay, the
  family key, and the maintenance loan still being refused.

### Issues

#### Critical

1. **A bursary paid to the student beside a tuition fee loan breaks the search's spend-cap
   pruning. The search can then miss feasible routes, or say "no route" when one exists.**
   [truth]
   - Where:
     - `backend/src/careerwright/planning/checker.py:744`
       (`fees += paid + lent`), with `:927` (`applied = min(amount, fees)`);
     - mirrored in `backend/tests/support/route_oracle.py:447`;
     - `backend/src/careerwright/planning/search.py:895-901` (`_spend` sums each option's
       *clamped* direct cost) and its rule-2/rule-3 use;
     - `docs/adr/0016-route-search-core.md:405` (claims rule 3 still holds).
   - What: ruling 5 sets a grant paid to the person against the whole fee, including the part
     the loan paid. On a loan-funded option the person pays £0, so that option's own net
     direct spending becomes negative (−grant). The checker and the oracle sum the route's
     net and clamp only the total. So the grant now lowers *other* options' costs. But the
     search prunes on the sum of each option's own direct cost, each clamped at £0 (rule 3),
     and sets aside an option whose own cost alone breaks the cap (rule 2). "Adding a variant
     never lowers the direct cost" is no longer true, so the pruning is unsound.
   - Reproduced (`/tmp/r12c/repro.py`):
     - Setup: a degree with a £9,000 fee paid in full by an approved loan, plus a £1,000
       grant paid to the student; a £1,200 course; direct-spend cap £1,000.
     - `check_route`:
       - `[degree]`: feasible, £0;
       - `[course]`: not feasible (direct-spend cap);
       - `[course, degree]`: **feasible, £200**.
     - Both options teaching the row: the search archives `[[degree]]` only, while the oracle
       archives `[[course, degree], [degree]]`.
     - Only the course teaching the row: the search says
       **`no_route_in_bounded_model`, coverage `complete`**, while the oracle says
       `routes_found` with `[course, degree]`.
   - Why it matters:
     - A false "no route" is a decision the person acts on.
     - The case is the ordinary school-leaver case: a university bursary paid to the student
       beside a tuition fee loan.
     - It breaks the brief's acceptance line "the search must give exactly the oracle's
       archive, objectives, layers and outcome". The Hypothesis properties didn't happen to
       generate it.
   - Fix (one of these; the first keeps every existing rule):
     - **(a)** A grant paid to the person lowers the person's *direct spending* only up to
       what they pay for that option (`min(grant, paid)`). It still lowers the *economic
       cost* against the whole fee (`min(grant, paid + lent)`), and its cash receipt is
       unchanged. Apply the same rule in the oracle, written fresh.
     - **(b)** Change rule 3 and rule 2's own-cap screen to work on unclamped net costs. That
       loses the pruning's monotonicity, so (a) is the simpler choice.
   - Either way: add this two-option instance as a fixed `@example` on both oracle
     properties, and correct ADR 0013 ruling 5's wording and ADR 0016's rule 3 line.

#### Important

None.

#### Minor (wait for the final review unless the fix round touches them)

1. **A loan that pays nothing still makes the route conditional.** [list]
   `checker.py:780`. A not-yet-approved loan on an option with no fee due, or with every fee
   covered by provider support, still adds `confirm_loan_approved` and `conditional_loan`.
   `loans_to_repay` is empty, so the route rests on approval of a loan that pays £0. Fix: add
   the condition only when the loan lends something (or its amount is unknown).
2. **A fee due before the planning start that the loan pays shows as a £0 payment.** [list]
   `checker.py:758`. `before.py` gives `payment_before_start` with `amount 0` and a £0
   `before_start` liability. `loans_to_repay` still lists a December loan, though whether
   that fee was paid is unknown. The route is unresolved and set aside, so no decision
   changes. Fix: pass the fee before the loan to `_before_start`, or leave a before-start fee
   out of `loans_to_repay`.
3. **Migration 0040's CHECKs, like 0033's, let through a loan with a missing or non-string
   status.** [list] `r0040_tuition_fee_loans.py:69-85`. The domain refuses these first. A
   stricter form (`!exists(@.eligibility) || …`) would repeat the rule fully. Batch it with
   0033's at the final review.
4. **A "tuition fee loan" can be stated on any option.** [list] Ruling 7 places no limit by
   option kind, so at the API level an Advanced Learner Loan (also paid to the provider)
   could be entered as one. Decision 1 keeps that loan refused until the product owner
   answers. Since there is no interface yet, it's enough that Task 12b asks about the loan
   only on degree options. The report's yes/no question is correctly put.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The loan rule itself is right and well tested: the statuses, an unknown
amount, nothing counted twice in cash or the caps, and the economic cost counted once. But the
grant-against-the-whole-fee choice makes one option's direct spending negative. That breaks
the search's spend-cap pruning: it can report "no route" with complete coverage while the
checker and the oracle find a feasible route, in a common student case. One focused fix in
the checker and the oracle, plus a pinned example, closes it.
