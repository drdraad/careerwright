# Task 12a report: the person's planning inputs, stored and confirmed (backend)

Branch `wt-12a` in `/Users/darianraad/Code/careerpathoptimizer-wt/12a`, rebased onto
`l0-local-release` at 98fd0a9 (Task 13a and Task W2E integrated). `git log
l0-local-release..wt-12a` shows only this task's four commits.

## Commits

- `dc1e96f` The planning rules the person's inputs need (checker, oracle, search classing,
  pack adapter, null month rows; generated client).
- `875c860` The person's planning inputs stored and confirmed (pure model, store, commands,
  migration 0033, `GET`/`PUT planning/inputs`, generated client).
- `b174355` ADRs 0013, 0016 and 0012.
- `edfebc7` Register (last commit, after the rebase).

## What was implemented

### The planning rules (checker, oracle, search)
New checker finding codes, each written again in `tests/support/route_oracle.py` and classed
for the search (ruling 1; ADR 0016 amendment; `PRUNING_VERSION = "sound-pruning-3"`):

| Code | Kind | Rule | Search class |
|---|---|---|---|
| `work_rights_unknown` | unresolved | work rights not stated or `unknown` | rule 1 (input-level) |
| `work_rights_not_held` | unresolved | `not_held`: no visa or sponsorship check, never ineligible | rule 1 |
| `stacking_unconfirmed` | unresolved | more than one counted support on a variant, stacking not confirmed (covers exclusivity and eligible-cost caps between them) | rule 2 (own) |
| `eligibility_unconfirmed` | unresolved | a stated fee's eligibility condition not `confirmed` (C07), one per condition | rule 2 (own) |
| `entry_requirements_not_met` | unresolved | the person's explicit "no" (next action, worded by the web: check equivalent experience) | rule 2 (own) |
| `repayments_above_payment_cap` | violation | existing repayments alone above the monthly cap, `reason` names the debts; replaces `monthly_payment_cap` that month; an undated payment is no longer blamed | rule 3 (cut as monthly payment cap) |
| `job_transitions` | violation | more than one selected variant behind an offer not yet accepted (ruling 4) | rule 4 (persists; new `PruningRule.JOB_TRANSITIONS`) |

- Month rows (deliverable 7): `DirectMonth`, `IncomeMonth` and `LiquidityMonth` figures that
  rest on an unknown amount are null. Living costs and repayments stay known. The checker
  still tests its limits on the known part (`ledgers.balances`), so no verdict changed.
- Pack adapter: an offering's `eligibility_` funding conditions are served as
  `Offering.eligibility_conditions`; `Variant` gains `stacking_confirmed` and
  `condition_statuses`; `CompiledVariant` gains `stacking_confirmed`, `unconfirmed_conditions`
  and `entry_not_met` (`entry_unconfirmed` now means "not yet answered" only).
- `PlanningInputs.work_rights` is required (no default), so every caller states it.
- D12–D17 applied: the provisional (R6) marks are gone from `pack.py`, `compiler.py` and ADR
  0013's status; the rules themselves were already as answered.

### The stored inputs
- `planning/inputs.py` (pure): `PlanningInputsIn` (client), `PlanningInputsDocument` (stored),
  `needs()` (what a solve still needs, as codes with an effect), `prepare()` (the document read
  as `PlanningInputs` plus the catalogue with the person's answers in it; refused, naming the
  missing inputs, while one that blocks a solve is unstated), `stamped()` (outcome decisions keep
  who and when while unchanged), `decided_outcomes()` and `refused_decision()`.
- `planning/store.py` (planning's only SQL, added to the architecture test's adapters) and
  `planning/commands.py` (expected-version write; new or changed answers checked against the
  workspace's own options; event `planning.inputs_updated`).
- Migration `r0033_planning_inputs.py`: `planning_input_versions`, append-only, row-level
  security, CHECKs on money (GBP, never negative), hours, delay months, work rights, remote
  work, supports (no loan or programme; approval needs confirmed eligibility) and decisions.
- API: `GET /v1/workspaces/{id}/planning/inputs` and `PUT` (expected version,
  `Idempotency-Key`, `run_idempotent`; 201 new version, 200 nothing changed, 409 stale). The
  response carries the profile's two caps read-only and `needs` as codes.
- Generated client regenerated (`pnpm run generate`).

## Rulings made (recorded in ADR 0013, "Task 12a's settlement")
1. **Work rights and remote working live in the planning inputs**, not the profile (ruling 5):
   they are the plan's hard check; keeping them away from the city list makes "never from a
   city" and "remote never takes a city slot" structural; and a profile schema change would
   collide with Task 6d in the main tree.
2. **The direct-spend and monthly payment caps stay the profile's** (they already exist there,
   set only by the person); the planning inputs hold the reserve and deficit cap. No duplicate
   record.
3. **One figure a month or a week**, laid on the solve's horizon by `prepare` (known limit).
4. **What blocks a solve vs what leaves every route unresolved**: objective basis,
   continuation, opening cash, living costs, commitments, existing debts and delay months block
   (named); caps, reserve, availability, the baseline the economic comparison reads and work
   rights leave every route unresolved (ADR 0013 decision 6). "No debts" is `[]`, not asked is
   null (session 2's T5).
5. **C07** (ruling 2): conditions apply only to a *stated* fee; where no fee is stated (C01) the
   cost is already the unknown, so session 2's committed package stays byte-identical.
6. **C09** (ruling 3): `admissions` (offering IDs where the person holds a place or an
   accepted offer) put the application gate in the initial gates and accept the offer gate.
   Without one the route stays as stated (`prerequisite_not_usable`, offer a condition), never
   feasible. I read "stays conditional on the application" as "never feasible as stated", which
   the existing violation already gives; I did not turn it into an unresolved finding.
7. **One conditional job transition** counts variants with an offer gate not yet accepted,
   whatever their kind; an accepted offer is the starting position. ADR 0016's tree bound (one
   `work` action) stays beside it.
8. **Remote work**: `GB-ENG` and `Europe/London` only; another country is refused as outside
   L0's slice.
9. **A person-stated support is `accepted_assumption`**, so a route resting on it is
   qualified; a scheme the catalogue names keeps its kind (a loan never passes as a grant).
10. **Stored answers kept unchanged are not re-validated** (an option that disappeared never
    blocks the next write); new or changed ones must fit a current option.

## Tests and checks (commands and results)
- RED first (domain logic): the ten new checker tests failed (`10 failed, 39 passed`) before
  the checker change; after it the oracle's two property tests failed (`2 failed, 1 passed`)
  until the oracle was updated; two new search tests failed (set-aside of the new own codes,
  and the job-transition cut); the C07 pack test failed. All GREEN after.
- Not RED first: `tests/domain/test_planning_inputs.py` was written before `inputs.py`, but
  its first run was after the module existed (it would only have failed on import); the
  integration tests were written after the commands. Both passed on their first run. The
  repayments search test passed at once (rule 3's pre-check already prunes it); it stays as
  coverage.
- A probe (scratchpad, not committed) confirmed the oracle's generated cases reach every new
  code, `repayments_above_payment_cap` included after raising its odds.
- `make check` before the rebase: pass (backend 1,650 passed; web 319). After the rebase:
  pass (backend 1,650 passed, 351 deselected; web 337).
- Focused integration runs under the acceptance lock: `test_planning_inputs.py`,
  `test_planning_options.py`, `test_migrations.py`, `test_isolation.py`: 43 passed; then
  `test_planning_inputs.py` again after adding the event assertion: 18 passed.
- `make acceptance` (under the lock, on `edfebc7`):
  - First run (11:53–12:12): the integration and stack tests passed (351 passed). Playwright
    had 1 failure out of 55: `visual.spec.ts` at 1440x900, `home--empty--1440x900.png: console
    errors`, with one browser line `Failed to load resource: net::ERR_FAILED` on Ben's empty
    home page. That page calls no planning endpoint. The same check passed at the other
    viewports.
  - Another agent held the lock next. I waited for it, took it at 12:33 and ran the full
    command again on the same commit.
  - Second run (12:33–12:51): **pass, exit 0**. Integration and stack: 351 passed. Storybook
    built. Playwright: 55 passed. I take the first failure to be a flake, and I have not
    found its cause.

## Changed test inputs or assertions (disclosed)
- `tests/support/planning.py`: `person()` and `trace_inputs()` state `work_rights=HELD` (the
  synthetic employed persona; unknown would make every case unresolved); `option()` gains
  `stacking_confirmed` and `condition_statuses`.
- `tools/session_2_files.py` and `tools/route_search_sizes.py`: their synthetic persons state
  `work_rights=HELD`, so session 2's committed questions stay identical (the drift test passes).
- `test_route_search_pack.py`: C07's test renamed; its expected codes changed from
  `[workload_unknown]` to `[eligibility_unconfirmed, workload_unknown]` (ruling 2), with kind
  and violations asserted.
- `test_planning_checks.py`: two `sum(...) == 0` assertions became per-month list equalities
  (stronger; needed for nullable rows); a helper's return type became `list[int | None]`.
- `test_planning_properties.py` and `test_planning_trace.py`: ledger identities read through a
  non-null assertion (stronger), for the nullable row types.
- `test_route_oracle.py` generator: apprenticeships, zero to two supports with a stacking flag,
  eligibility conditions with statuses, entry answers yes, no or none, large repayments, work
  rights unknown or not held; debts one in five (was one in six).
- `test_planning_contract.py`: the "money, never bare" check now also covers
  `PlanningInputsOut` and `WriteInputs`.

## Live calls
None. £0.

## Not done, blocked or for others
- The checkpoint UI, an option's own facts and "add an option yourself" (Task 12b); the solve's
  stage checks (Task 14); building a solve's readiness basis with `decided_outcomes` (13b/14).
- Planning inputs are not in the workspace export (capability evidence is not either).
- `CLAUDE.md`'s layout line still calls `careerwright/planning` pure; it now has `store.py`
  and `commands.py`. The controller can update it in the main tree.
- The app still reads pack 0.1.0 (the 7c carry-forward "pin 0.2.0" was outside items 1–7);
  variant IDs are validated against what the app reads.

## Concerns
1. **Two records about the right to work:** the planning input (the person's status for the
   whole plan) and the capability model's requirement statement on a target's right-to-work row
   (the employer's check). A route needs both, so a disagreement can only withhold a result,
   never give one; 12b should show or prefill them together. C07's own "right to work"
   condition is also confirmed per option, never inferred.
2. **Exclusivity across two funded options in one route** is not checked (only between the
   supports of one option); C01's "no other government-funded training" is a condition the
   person confirms per option.
3. **Process:** one edit to `tools/session_2_files.py` was first made with a Python heredoc
   by mistake; I reverted it at once with `git checkout` and redid it with the Edit tool. No
   lasting effect.

## Paths a reviewer can skip
`apps/web/src/generated/` (regenerated client and `openapi.json`).

---

# Fix round 1

Branch `wt-12a` now sits on `l0-local-release` at 60c8516 (Task W2E's fix round). Six
commits, the register last:

| Commit | What |
|---|---|
| 16ca9b0 | The planning rules (replayed unchanged) |
| d7ec4c0 | The stored inputs and API (replayed unchanged) |
| db0b7f4 | ADRs 0013, 0016, 0012 (replayed unchanged) |
| a3ca211 | **Fix round 1, the planning rules** (checker, compiler, inputs, search, oracle, tests, client) |
| cca3eca | **Fix round 1, ADRs 0013 and 0016** |
| 86d7ead | Register: the rows from the first round plus this round's (amended, so the register stays in one last commit) |

I replayed my commits with `git cherry-pick` onto `l0-local-release` in that order, so the
register commit stays last. `git log l0-local-release..wt-12a` shows only these six.

## The fixes

1. **A receipt that may not come is never shown as known** (Important 1).
   - A support paid to the person whose stacking is not confirmed now leaves every cash month's
     early and later receipts null. So does a support whose scheme pays for two options.
   - The direct ledger's figures were already null. The income ledger never rested on a
     support, and it stays known.
   - The reserve check still counts the support. With it counted, the cash is the most the
     person could have, so a breach there is real.
   - How: a display-only flag (`receipts_shown`), set through one helper, `_unknown_support`.
2. **One scheme on two options; recorded exclusivity** (Important 2, the controller's ruling).
   - The same scheme counted on more than one option of a route is
     `scheme_shared_unconfirmed` (its reason is the instrument). The route is unresolved, and
     its cost and month rows are unknown.
   - That lasts until the person confirms the scheme pays for each option. This is a new input,
     `shared_schemes`, on `PlanningInputsIn` and `PlanningInputs`. It must name one of the
     person's stated supports.
   - Two schemes a record states as exclusive are `exclusive_schemes`, a violation. The
     record is the new `FundingInstrument.exclusive_with`, read either way. It is carried as
     `MonthlyInput.scheme_exclusions` and is part of the input version.
   - The pack records no machine-readable exclusivity. Its `exclusions` are text that names no
     scheme, and every list is empty in 0.1.0 and 0.2.0. So different schemes are an L0 limit,
     recorded in ADR 0013 (settlement item 16). No rule is invented.
   - Search classing:
     - `exclusive_schemes` is a variant's own violation when both schemes are on one option.
     - Across two options it persists, so it gets a new cut, `PruningRule.EXCLUSIVE_SCHEMES`.
     - `scheme_shared_unconfirmed` is never pruned and never one option's own.
     - `PRUNING_VERSION = "sound-pruning-4"`.
   - Rule 3 now sums each variant's own spend, from its check alone. A node whose own rows are
     null is therefore summed the same way, and pruning never relies on a null row.
3. **"No route" when the person's repayments rule it out** (Important 3).
   - New `_FIXED_BY_INPUTS = {repayments_above_payment_cap}`. A complete run whose starting
     position breaks one of these says `no_route_in_bounded_model`, naming the breach as its
     starting violations. That holds whatever is set aside or unstated.
   - Any other starting breach (the reserve, the deficit cap, the workload) could be relieved
     by some option. It keeps today's behaviour, and `undated_relief` still gives `unresolved`.
   - The oracle's `Solved` gains `repayments_rule_out_every_route` and `outcome`, both worked
     out independently.
   - The property test now asserts `result.outcome.value == oracle.outcome`, which checks both
     directions. The reviewer's probe is a pinned `@example`.
4. **C09: conditional on the application** (the Minor that contradicted the ruling).
   - With no application in the route and no admission recorded, an option behind an
     application gate gives a `Condition` of kind `application` (`confirm_admission`) and the
     qualification `conditional_application`. The route can be feasible, qualified, and is
     never "not feasible".
   - This holds in the checker, the oracle and the search. A deadline already passed is still
     `application_too_late`. An application inside the route keeps TIME-1's timing rules.

## Tests and checks
- **Failing first:** I wrote the tests below before the fixes and ran them on the code as it
  was: `16 failed, 107 passed`. All of them now pass.
  - Checker: the extended month-row test, one scheme on two options, exclusive schemes, and
    the TIME-03 case "no application → conditional".
  - Search: no route beside an unknown, one scheme and exclusive schemes in the search, and an
    application as a conditional route.
  - Oracle:
    - three oracle-only tests: no route on repayments, one scheme and exclusive schemes, and
      an application as conditional;
    - both property tests, run with the extended generator and the two-way outcome check.
  - Pack: C09's violations.
  - Inputs: `shared_schemes`, and the admission test.
- **Oracle reach:** the generator now draws two schemes, `shared_schemes`, and a catalogue
  with recorded exclusivity. A probe (scratchpad, not committed) compared the search's
  outcome with the oracle's on 1,500 generated instances and found no disagreement:
  - 247 "no route" both ways;
  - 426 routes found;
  - 827 unresolved.
  The probe also saw every new code: `exclusive_schemes` was set aside 67 times and pruned 6
  times, and `repayments_above_payment_cap` was a starting violation 63 times.
- **`make check`:** passed before the rebase (backend 1,659; web 337) and after it (backend
  1,661; web 343).
- **`make acceptance`:** passed (exit 0) on 86d7ead, run once under the lock from 13:29 to
  13:47. Integration and stack: 351 passed. Storybook built. Playwright: 56 passed. The
  earlier console-error flake on the empty home page did not come back.

## Changed test expectations (disclosed)
- `test_planning_checks.py::test_an_application_in_its_deadline_month_is_unresolved_never_ineligible`:
  "unapplied" was `{prerequisite_not_usable}` and is now no finding, an `application`
  condition, `feasible` and `conditional_application`. This follows the C09 ruling.
- `test_route_search_pack.py` (C09): its violations went from `[prerequisite_not_usable,
  workload]` to `[workload]`. Same ruling.
- `test_planning_inputs.py` (the admission test): without an admission it now expects no
  finding, the conditions `offer` and `application`, and `feasible`. Same ruling.
- `test_route_oracle.py`:
  - the property test's two one-way outcome checks became one equality with the oracle;
  - the generator's supports now name one of two schemes;
  - the person sometimes confirms the first scheme as shared;
  - one catalogue in three records the two schemes as exclusive.
- `tests/integration/test_planning_inputs.py`: the round-trip document now holds
  `shared_schemes: ["funding:employer"]`.
- `tests/support/planning.py`: gains `repayments_beside_an_unknown()`, the reviewer's probe.
  The search test and the oracle test share it.

## Not done (R13, and why)
- The other Minors of the review wait for the final review, as the fix list says. They are:
  D12–D17 still called provisional in ADR bodies and three register rows; register tidiness;
  how debts are named; the migration's omitted CHECKs; a `work` offering with no offer gate;
  guarding the generator's reach; asking three times about the right to work; the export; and
  CLAUDE.md.
- The new `shared_schemes` input has no CHECK in migration 0033, and none was added.
