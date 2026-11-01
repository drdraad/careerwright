# Task 12a, fix round 1 of 5

The review is `.superpowers/sdd/l0-sprint-tasks/task-12a-review.md`. Read its three Important
findings in full. Fix them in your worktree (`/Users/darianraad/Code/careerpathoptimizer-wt/12a`,
branch `wt-12a`), plus one Minor that contradicts the controller's ruling. Each fix needs a
test that fails on today's code, in both the checker's tests and the oracle's where the rule
lives in both. Show RED, then GREEN.

1. **Important 1: a receipt that may not come is shown as known.** Two supports paid to the
   person and not yet confirmed to combine: the cash ledger still shows their sum as a known
   receipt, while the direct ledger shows that support as unknown (`checker.py:635`,
   `ledgers.py:165`). Every ledger month that rests on an unconfirmed stacked support is null
   or carries its incomplete flag, never a partial figure shown as known. Check the cash,
   direct-spend and income ledgers alike.
2. **Important 2: one scheme pays for two courses.** The controller's ruling:
   - The same funding scheme, approved on two options in one route, leaves the route
     unresolved until the person confirms the scheme covers both. That's the same rule as
     stacking: a confirmed input with its own finding and next action.
   - Where the pack records two different schemes as exclusive of each other, combining them
     in one route is not feasible in this monthly model, with a named finding.
   - Where nothing records exclusivity between different schemes, record it as an L0 limit in
     ADR 0013's amendment section. Don't invent a rule.
   - All of this goes in the checker, the oracle and the search's classing.
3. **Important 3: "unresolved" where the truth is no route.** Existing repayments alone can
   break the payment cap, and no option can cure that. The result must then be
   `no_route_in_bounded_model` (with complete coverage), naming the repayments, even when some
   option has an unknown (`search.py:628`). Before this task the search said exactly that.
   - Generalise it: a starting-position breach that no option in the model can reduce rules
     out every route. An unknown elsewhere doesn't turn that into "unresolved".
   - A starting breach some option could cure (for example workload, by a reduced-hours
     pattern) keeps today's behaviour.
   - Make the oracle property test check both directions (`test_route_oracle.py:292`): the
     search's outcome equals the oracle's. It must not merely be no stronger.
4. **The Minor that contradicts the controller's ruling (C09).** Without a recorded admission
   or offer, a route through an option with an application gate is conditional on the
   application. It is never "not feasible", and the ledger already says "conditional". Make
   the checker, the oracle and the search agree, and test it.

Every other Minor waits for the final review (R13).

## When done
- Run the covering tests, then `make check`.
- Rebase onto the current `l0-local-release` (it may have moved: Task W2E's fix round). Run
  `make check` again.
- `make acceptance` once, under the lock. If the earlier console-error flake on the empty home
  page recurs, re-run once and report both runs exactly.
- Append a "Fix round 1" section to `task-12a-report.md`. Reply with the short contract and
  your branch head SHA.
