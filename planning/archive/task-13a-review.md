# Task 13a review: the route search core

Branch `wt-13a`, ec4d060..0eb11b5 (3 commits). I read the brief, the dispatch and the report,
then the diff in passes: `search.py`, `layers.py`, `families.py`, the oracle and its tests,
the search and pack tests, the measurement tool, ADR 0016 and the register rows.

Outside the diff, I read only what a named risk needed: `checker.py`, `compiler.py`,
`catalogue.py` (Support, Recurring), the readiness states in `capability/readiness.py`,
`planning/pack.py` and pack 0.2.0's offering records.

I re-ran no suites. I ran four small probes in the worktree's environment; the worktree
stayed clean at 0eb11b5. The scripts are in
`/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/e3bcee60-3128-4a91-bb65-a14bf9244c20/scratchpad/`
(`probe_13a.py`, `probe_13a_p01.py`, `probe_13a_pack.py`, `probe_13a_cost.py`).

### Spec Compliance
- ❌ Issues found:
  - **"No route" while something is unknown.** The search can cut the empty route before it
    records the options it sets aside. A complete run can then say
    `no_route_in_bounded_model` even though an option with unknown dates exists. This breaks
    ADR 0016 decision 8 and "unknown is never a no" in that case (Important 1;
    `search.py:317-321`, `573-585`).
  - **What a set-aside option lacks.** `SetAside.codes` keeps only the codes that justified
    setting the option aside, and drops every other finding from its own check. So C09 reads
    "entry requirements, cost", but its own check also fails on its admission gate and on
    workload (Important 2; `search.py:183-188`, `437-452`; ADR 0016 line 158; report line 207).
  - **S6.7's months dimension.** Whatever the horizon, the measurement puts every intake in
    months 1 to 9. So the 12-month and 24-month rows measure only the cost of each check, not
    a larger tree (Important 3; `tools/route_search_sizes.py:218`).
- ⚠️ Cannot verify from diff:
  - **C07's £0 fee.** The pack adapter treats it as a known fee. It keeps the fee's
    conditions as plain facts that nothing checks: aged 19+, living in London, North
    Yorkshire, the West Midlands or the North East, and the right to work
    (`planning/pack.py` docstring: "a course's funding conditions are facts").
    - C07's only missing fact is its weekly hours. Once those are confirmed, it is searched
      for the Bristol target at £0.
    - ADR 0013's amendment makes unknown work rights unresolved. It does not name residency
      or age.
    - For Task 12a: a fee that holds only for eligible learners should leave the cost
      unresolved until the person confirms eligibility.
  - **C09's admission.** Nothing in the pack grants `admission:offering:C09`, and the pack
    has no application action. So C09 can never be feasible unless Task 12a records a
    completed application in the starting state or adds an application action (spec section
    12: "Include information-gathering, application and waiting actions").
  - **Undated work patterns in the checker (Task 11).** The checker treats a variant with
    unknown dates and a work pattern as absent in every month (`checker.py:245-246`,
    `671-676`, `710-721`). A month's workload breach then becomes a violation that rests on
    unknown dates. The fix for Important 1 makes the search's outcome honest, but the
    checker's verdict on that one route is unchanged.
  - **Later tasks.** The data mode on the run record (Global Constraint 5), persistence, the
    API and the instance from P01's stored inputs belong to Tasks 13b, 14 and 12a.
  - **`make check`.** The report says exit 0 with 1,602 backend tests passed. Not re-run, per
    the dispatch.

### Strengths
- **Every pruning rule is sound against the checker's actual code.** I traced each one:
  - Rule 1: the empty route's unresolved findings come only from the inputs (an unstated
    limit, unstated availability, or a missing baseline).
  - Rule 2: each code that sets an option aside is computed from the variant alone in the
    base scenario. Unknown weekly hours give "workload unknown" or a breach in every month
    the option is active.
  - Rule 3: support paid to the person is capped at that option's own fees, so each option's
    net cost is at least zero. The pre-check therefore gives exactly the child's own cap
    test.
  - Rule 4: active work patterns and clashing session pairs only grow as options are added.
  - Rule 5: a subtree only appends later options, so a month's first work pattern, once set,
    never changes.
  - Rule 6: every option without dates is set aside, so no later option can silence the
    finding.
  - The search never prunes on the reserve, the deficit cap, applications, readiness or the
    objectives.
- **Coverage is honest.** It is `complete` only when no limit fired. Every stop keeps what it
  found and gives its reason, and a stopped run with nothing found is
  `none_found_before_limit`. Inputs beyond the M0 bounds are refused, never searched in part.
- **The layers are right.** Peeling is correct: a point is in the layer when it is cheaper
  than everything sooner, and ties share a layer. It runs over the whole archive, dominated
  schedules included. Two checks back it: a property test, and the oracle's own
  longest-chain rule.
- **Money is whole pence throughout** (`Money`, `SignedMoney`, integer points).
- **The measurements reproduce.**
  - Relaxed, 10 concepts × 2 starts × 24 months: 7,455 states in 3.8 s (reported 4.15 s).
  - Relaxed, 12 × 1 × 24: 945 states in 0.41 s (reported 0.43 s).
  - P01, 24 × 2 × 24: 2,487 states in 1.95 s (reported 1.66 s).
  - A check costs the same on a real pack matrix (13 rows) as on the synthetic one (0.18 to
    0.19 ms for the empty route), so the per-check cost is representative.
  - Runs that stopped early are reported as "not complete at that size", never as
    infeasible.
- **The pack reading matches pack 0.2.0.** I checked each offering's dates, fee,
  instalments, schedule and entry requirements against its record. All four targets come out
  `unresolved`, never "no route". That holds twice over: each target's empty route is also
  not yet assessed.
- **The code and report are clean.** The modules are pure and plain, with an injected clock.
  Tests use fixture values and hand-worked cases. The report names its own weak spots
  honestly.

### Issues

#### Critical
None.

#### Important

**1. The empty route's cut skips the screen, so "no route" can hide an option with unknown
dates** (`search.py:317-321`, `503-507` with `667-670`, `573-585`)
- **What happens:** the search runs the cut for rules 3 to 6 on the empty route (lines
  317-320) before the screen that sets options aside (line 321).
  - `_load_stays` counts an undated option as never active, so the cut fires.
  - Nothing is set aside, nothing is counted as unresolved, and `_outcome` returns
    `no_route_in_bounded_model`.
- **Probe 1 reproduces it:**
  - The person works 37 hours a week. Their availability is 40, 40, 25 and 25 hours over
    four months. The only option is a reduced-hours work pattern (20 hours) with no dates.
  - Result: `complete`, `no_route_in_bounded_model`, set aside `[]`, pruned `{workload: 1}`,
    1 check.
  - The same option with 40 hours available every month gives `unresolved`, set aside as
    unresolved. The two paths disagree on the same evidence.
  - The oracle agrees with "no route" (`something_unknown` is False) because it copies the
    checker. `check_route(["reduced-undated"])` is `not_feasible` (dates unknown, plus a
    workload breach). So the property test cannot catch this.
- **Why it matters:** the person is told the model has no route, when the one option that
  could work is only missing its dates. That is unknown shown as none, a kind R14 keeps in
  the task. The input is plausible: someone who can manage fewer hours from some month, and
  whose reduced-hours option has no confirmed intake.
- **Fix:**
  - Run `_screen` before the empty route's rule 3 to 6 cut. Rule 1 can stay first. Ruling 5
    then applies on every path.
  - Add probe 1's instance as a regression test.

**2. A set-aside option's record drops the other breaches its own check found**
(`search.py:183-188`, `341-353`, `437-452`; ADR 0016 line 158; report line 207)
- **What happens:** `_own_findings` keeps only the codes that justify setting the option
  aside. Every other finding from that option's own check is lost.
- **Probe 3 shows it** (pack 0.2.0, P01's figures):
  - C09 checked alone is `not_feasible`. Its cost is unknown, its entry requirements are
    unconfirmed, and it has two breaches:
    - `prerequisite_not_usable`: its admission gate, which nothing in the catalogue grants;
    - `workload`: 35 hours on top of P01's 30-hour job, with 40 hours available.
  - The result keeps only `[cost_unknown, entry_requirements_unconfirmed]`, kind unresolved.
    The report's table says "C09: entry requirements, cost".
- **Why it matters:** ADR 0016 tells Task 14 to show these reasons as "what to confirm".
  - A person told to confirm C09's entry requirements and cost would do it. They would
    still get no route through C09, and no reason why.
  - The report's reading for Task 13b ("every pack offering lacks a fact the search needs")
    is true but incomplete. C09 also breaks two rules, and C04 paid in full breaks both caps.
  - The outcome word stays honest (`unresolved`). The reasons do not.
- **Fix:**
  - Keep `codes` as the reasons the option was set aside.
  - Add the option's other findings to the record, for example `also: list[FindingCode]`
    (the findings another option might repair).
  - Correct the report's pack table.
  - Reword ADR 0016's Task 14 note so that "what to confirm" shows both lists.

**3. The measurement's months axis does not grow the tree** (`tools/route_search_sizes.py:218`;
report lines 21 and 172-174; ADR 0016 lines 138-146)
- **What happens:** `first = c % min(months, 6) + start * 3` puts every first intake in
  months 1 to 6 and every second intake in months 4 to 9. Courses last at most six months.
  - At 12 and 24 months, the tree, the pruning and the archive are the same as at about 9
    months. Only the cost of each check grows.
  - The report's own table shows this: expanded states are identical at 12 and 24 months in
    every family.
  - S6.7 asks for growth in concepts, starts per concept **and months**. ADR 0016 says "at
    every horizon".
- **Probe 2, with intakes spread over 24 months** (`first = 5c mod 24`):
  - Relaxed, 10 × 2 × 24: 12,451 states in 6.1 s, against 7,455 as measured.
  - Relaxed, 12 × 1 × 24: 1,387 states, against 945.
  - P01's headline still holds: 24 × 2 × 24 needs 2,233 states spread against 2,487, because
    the £1,500 direct-spend cap prunes whatever the dates.
  - The no-limit family checks the whole selection space, so dates do not affect it.
- **Why it matters:** Task 13b sizes its durable add-ons from these tables.
  - The answers 13b decides on still stand: every pack target completes at once; a
    catalogue the size of the whole pack completes in about 14 s with nothing pruned; and
    the per-check cost.
  - The relaxed family's "largest sizes" at 12 and 24 months are optimistic by roughly half
    again in states.
- **Fix:** spread intakes across the horizon in the tool and re-run the relaxed sweep at 12
  and 24 months. At the least, say in the report and ADR 0016's consequences that the horizon
  changes only the per-check cost in these instances. No change to the search.

#### Minor
1. **The property test would miss a duplicated route** (`test_route_oracle.py:235`, `252`).
   It builds `found` as a dict keyed by route, so a route archived twice would still pass,
   and `expanded_states` is only checked with `<=`. Uniqueness holds by construction today.
   Adding `len(found) == len(result.schedules)` would guard it.
2. **How independent the oracle is** (this answers the dispatch's question).
   - It is independent of the search's own logic, which is where this task's risk lies. It
     enumerates the Cartesian product, checks routes in ID order rather than canonical order
     (`route_oracle.py:105`), and ranks with its own longest-chain layer rule.
   - It is not independent of the checker's rules. It is a transcription of them, as report
     concern 1 says.
   - It also reads the compiler's month indexes (`start_index`, `finish_index`,
     `usable_index`: `route_oracle.py:181`, `260`, `325`, `468`, `484`). So TIME-1's
     touched-month and next-boundary rules are not worked out again.
   - So it cannot catch a rule defect that the checker and the compiler share. The checker
     line in Important 1 is one.
   - Fix: derive the months from the dates in the oracle, and state this scope in OPT1-08's
     register row.
3. **Ranking runs outside the 30-second clock.** Ranking and result assembly happen after
   the search's clock stops (`search.py:305-306`, `521-571`). They took under 1 s in every
   measured run. Disclosed as concern 3; Task 13b owns it.
4. **Two conditional job transitions are allowed.** The bridge-role ruling counts only
   `work` actions, so a route may hold an apprenticeship (with its own offer gate) and a
   bridge job, where the spec allows one bridge-role transition. No pack record combines
   them today. This needs a one-line question to the product owner, or a Task 12a note.
5. **Process.** One string replacement in a new test file was made by a Python one-off
   rather than the Edit tool. Disclosed as concern 5; it has no effect on the result.
6. **`CLAUDE.md` is out of date.** Its layout line for `careerwright/planning` does not name
   the search, the layers or the families. The controller can add it in the main tree.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** the search core is sound and its layers are correct. But two parts of the
result can mislead the person: it can say "no route" when the dates are unknown, and it can
say "confirm X" when the model also knows of a breach. And the measurement's months axis
needs a stated limit or a re-run before Task 13b sizes from it.

Counts: Critical 0, Important 3, Minor 6.
