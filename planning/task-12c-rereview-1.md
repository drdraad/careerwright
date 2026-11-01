# Task 12c re-review 1 (the fix round)

Reviewer: independent (R16), read-only. Package `review-775c2a6..b0f7715.diff` (649 lines),
read whole. Fix list `task-12c-fix-round-1.md`; the implementer's "Fix round 1" claims treated
as unverified. Worktree head checked: b0f7715, clean.

Checks I ran (scripts in `/tmp/r12c`, outside the tree, no bytecode written):
- `repro.py`, the Critical's reproducer, in both readiness set-ups.
- `probe.py`, a new probe:
  - several grants paid to the person, beside support at the provider and a loan paying part
    of the fee;
  - a fee beyond the horizon;
  - three cap and objective set-ups;
  - a loan not yet approved beside a grant.
- Not run: the implementer's suites (per the contract). **Integration and acceptance not
  run: Docker down.**

### Spec Compliance
- ✅ The fix list's two items are done, and nothing else changed.
- ⚠️ Cannot verify from diff: migration 0040 on PostgreSQL (unchanged since the first review;
  Docker down).

### The five checks

1. **The Critical is closed.**
   - The change, in `checker.py`:
     - `fees` is again only the tuition the person pays (`fees += paid`), so a grant paid to
       the person (`_receipt`: `applied = min(amount, fees)`, then
       `fees = max(0, fees - amount)`) never lowers more than that option's own payments;
     - its `gross` is used only for the economic cost.
   - Each path:
     - **Several grants:** each applies against what's left, so in total they lower at most
       what the person pays.
     - **Support at the provider:** `paid` already excludes what it covers.
     - **Beyond the horizon, or no month yet:** in both `fees` and `_net_paid`.
     - **Before the start:** a grant can apply against a fee due before the start, which
       `_net_paid` leaves out. This is how it worked before Task 12c, and that option's
       cost is unknown anyway: the search sets it aside under rule 2, and `_spend` reads 0.
       So no search effect.
   - So no searched option's own direct spending goes below £0, and rule 3's sums hold.
   - The pruning rule itself didn't change, so keeping `sound-pruning-5` is right.
   - The oracle reaches the same rule its own way (`fees` beside `whole`,
     `grant_on_loan_part`). It imports nothing new.
   - `repro.py` now:
     - both options teaching the row: search and oracle archive `[[degree]]`;
     - only the course teaching the row: both say `no_route_in_bounded_model`.
     - `[course, degree]` is correctly not feasible at £1,200, because the grant can't pay
       for the course.
   - `probe.py`: search equals oracle in all four set-ups, and each option alone is never
     below £0. Hand check of the multi-grant case:
     - fees £7,000, of which £500 is covered at the provider and £5,000 by the loan; the
       person pays £1,500 (beyond the horizon);
     - two grants (£800 and £900) take the direct cost to £0;
     - economic cost: £7,000 − £500 − £1,700 = £4,800, which matches the checker.
   - `grant_beside_loan` is pinned as an `@example` on both oracle properties.
2. **Minor 1 is closed.**
   - The `loan` condition moved from `_loan` to `_to_repay`. It is added only when
     `loan.conditional and (left is None or loan.lent)`; `lent` records only non-zero
     amounts.
   - The oracle's `rests_on_loan` gives the same test (used, not approved, unknown or
     `lent_here > 0`). The checker-vs-oracle property compares it on every candidate.
   - Conditions still come in the same order (award, offer, then loan for each option).
   - The new test covers no fee and a full waiver, and keeps an unknown amount conditional.
3. **The economic cost** is the whole fee once, less the grant once.
   - `economic = max(0, _net_paid + lent − support_beside_loans)`, with
     `support_beside_loans = Σ[min(G, gross) − min(G, fees)]`. That works out to every
     payment + lent − Σ min(G, gross).
   - So the grant is set against the whole tuition once, the loan's part included.
   - Confirmed by the test (fee + £50 − £500) and by the probe (£4,800; £3,000 − £1,000 =
     £2,000 for the conditional case).
4. **No expected value outside the loan changed.**
   - With no loan, `gross == fees`, so `support_beside_loans` is 0, and `fees += paid` is the
     rule from before Task 12c.
   - The only changed assertion is the 12c test's direct cost, £0 → £50. That is the correct
     effect: a grant paid to the person never lowered an extra cost before Task 12c either.
   - It also now asserts the support row is £0.
   - No TRACE-01, A–I or regression-family file is in the diff.
5. **The ADR lines are true.**
   - ADR 0016's rule 3 line now gives the reason it holds, and it is true for every searched
     option.
   - ADR 0013's ruling 2 and ruling 4 addition match the code.
   - One phrase is loose (Minor 1 below).

### Issues

#### Critical
None.

#### Important
None.

#### Minor (final review list)
1. **One ADR phrase is too broad.**
   - Where: `docs/adr/0013-planning-input-ledgers-and-checker.md`, ruling 2: "a grant beside
     a loan can't pay for something else".
   - Why: it is true for direct spending and the direct-spend cap. But the grant is still a
     cash receipt in the cash ledger, where it helps the reserve for any outflow.
   - Fix: "…can't lower what you spend on something else".
   - This is a document finding, not a sentence the person reads.
2. Carried from the first review, unchanged and already listed: Minors 2 (a before-start fee
   the loan pays shows as £0), 3 (0040's CHECKs let through a missing status) and 4 (the loan
   can be stated on any option).

### Assessment
**Task quality:** Approved

**Reasoning:** The fix restores the rule from before Task 12c for direct spending. It keeps
the grant against the whole fee for the economic cost, and the oracle checks both its own
way. The reproducer and a multi-grant probe now give identical answers from the search and the
oracle, and no expected value outside the loan moved. Integration and acceptance are still
not run: Docker down.
