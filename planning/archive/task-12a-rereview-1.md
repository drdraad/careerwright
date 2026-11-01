# Task 12a, re-review 1 (fix round 1)

Scope: the fix diff `review-db0b7f4..86d7ead.diff` (commits a3ca211, cca3eca and 86d7ead; the
replayed first-round commits are unchanged), the fix list, and the report's "Fix round 1"
section.

How I checked it:
- I read the diff in full.
- I re-ran my first-round probe, extended, against `wt-12a` at 86d7ead. It is a scratchpad
  script run read-only with `python -I -B`, and it left the worktree unchanged.
- I checked that both packs' funding instruments have empty `exclusions` lists.
- I did not re-run any suite.

### Verdicts

| Item | Verdict | Evidence |
|---|---|---|
| I1: a receipt that may not come is shown as known | **ADDRESSED** | See I1 below |
| I2: one scheme pays for two courses | **ADDRESSED** | See I2 below |
| I3: "unresolved" where the truth is no route | **ADDRESSED** | See I3 below |
| C09: an application-gated course is conditional | **ADDRESSED** | See C09 below |

**I1: a receipt that may not come is shown as known.**
- The fix: `receipts_shown` is set false by `_unknown_support` (`checker.py:387`, `:707-712`)
  and passed to the cash ledger (`:438`).
- The probe: two supports paid to the person, stacking not confirmed. Cash receipts,
  lower bounds and closings are all null, and so is the direct ledger's support.
- The reserve check still counts both supports, which is sound: that is the most cash the
  person could have, so a breach there is real.
- The test covers the cash, direct and income ledgers, and the shared-scheme case too
  (`test_planning_checks.py:1059`).

**I2: one scheme pays for two courses.** All three parts of the controller's ruling are in.
- **The same scheme on two options:**
  - `scheme_shared_unconfirmed` leaves the route unresolved (`checker.py:714-731`).
  - It clears only when the person confirms the scheme in the new input `shared_schemes`,
    which must name one of their stated supports (`inputs.py:248-262`).
  - The probe: unresolved until confirmed, then feasible. Assumed awards are unresolved in
    the base, delay and no-offer cases and feasible in the no-award case.
- **Schemes recorded as exclusive:** `exclusive_schemes` is a violation (`checker.py:737`),
  read from the new `FundingInstrument.exclusive_with`, whichever side names the other.
- **Different schemes with nothing recorded:** an L0 limit, stated honestly in ADR 0013
  item 16 (`docs/adr/0013-...md:325-339`). Both packs' `exclusions` lists are empty.
- **The oracle** writes both rules again (`route_oracle.py:135`, `:418`), and the generator
  draws two schemes, `shared_schemes`, and a catalogue that records exclusivity.
- **The search:**
  - `exclusive_schemes` is one option's own violation when both schemes are on it
    (`search.py:138`), and is cut as it persists across options (`:558-559`).
  - The shared-scheme finding is never pruned and never one option's own.
  - Rule 3 now sums each option's spend from that option checked alone (`search.py:521`), so
    a null row is never read. This is sound, because rule 2 sets aside every option whose
    amounts are unknown.

**I3: "unresolved" where the truth is no route.**
- The fix: a starting breach in `_FIXED_BY_INPUTS` (`search.py:146`) gives
  `no_route_in_bounded_model` on a complete run, before any unknown is weighed (`:659`).
- The oracle has its own independent reading (`route_oracle.py:74`, `:130`).
- The property test now asserts equality in both directions (`test_route_oracle.py:378`),
  and the probe instance is pinned as an `@example` (`:359`).
- The probe: search and oracle both say no route. With the reserve also unstated, it is still
  no route.

**C09: a course behind an application with no admission recorded.**
- The fix: with no application in the route and no admission recorded, the route carries
  an `application` condition with `confirm_admission` and is qualified
  `conditional_application` (`checker.py:550`, `:1122`). The oracle matches
  (`route_oracle.py:443`).
- The probe:
  - A deadline in the planning start month, or in the course's own start month, gives a
    feasible, qualified route. The checker, the search and the oracle all agree.
  - A deadline already passed is still `application_too_late`.
- The search no longer sets C09 aside for its admission. Its pack test now names only the
  workload breach.

### New issues in the fix diff

#### Critical
None.

#### Important
None.

#### Minor
1. **One confirmation of a shared scheme covers any number of options.** `shared_schemes`
   names a scheme, not the options it covers. In the probe, one confirmation passes a route
   that uses the scheme on three courses, including one the scheme was added to after the
   confirmation. The ruling says "covers both". Either store the options each confirmation
   covers, or Task 12b's question must say "for every option you've named it on". This needs
   a one-line ruling.
2. **`shared_schemes` has no database CHECK.** The domain rules are that each scheme is
   named once and is one of the person's stated supports. Today they are enforced only in
   Pydantic, on write and on read. This is the same class as the deferred Minor 4 of the
   first review (the migration's omitted CHECKs), so batch it with that.
3. **No stress case has the application fail.** All four fixed scenarios show an
   application-gated course feasible, qualified `conditional_application`. An offer has
   `no_offer` for that; an admission has nothing. No result claims more than the evidence,
   because the verdict is always qualified with a blocking verification. Task 14, or a
   one-line ruling, should decide whether a "not admitted" case is shown.

### Out of scope (one line each)
- I3's rule is general by kind of breach, not by instance. A starting reserve shortfall that
  no option in the catalogue could cover, beside an unknown, still reads "unresolved". The
  oracle agrees, so it is conservative and consistent.
- A route whose deadline has passed lists both `application_too_late` and an `application`
  condition. This is harmless: recording a place already held would clear it.
- The first review's other Minors stay deferred to the final review, as the fix list rules.

### Assessment
**Task quality:** Approved

**Reasoning:** All four items are fixed in the checker, the oracle and the search alike. The
outcome is now checked in both directions, and the re-run probe confirms each fix. What
remains is three Minors: the reach of one confirmation, a missing database CHECK, and a
missing stress case.
