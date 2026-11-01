# Task 12c, fix round 1 (the only one, R16)

Same implementer, same worktree (`/home/user/careerwright-wt/12c`, branch `wt-12c`). Read the
review: `/home/user/careerwright/planning/task-12c-review.md`. The controller reproduced the
Critical with the reviewer's `/tmp/r12c/repro.py` (search: `no_route_in_bounded_model`,
complete; oracle and checker: `[course, degree]` feasible at £200).

## Fix now (each with a test that fails before the fix)
1. **Critical (truth): a grant beside a tuition fee loan breaks the search's spend-cap
   pruning.** Support paid to the person lowers an option's direct spending only up to what
   the person pays for that option (as before Task 12c, when `applied = min(amount, fees)`
   was the person's fees); the economic cost still counts the whole fee once, less the grant
   as today. So no option's own direct spending goes below £0, and rule 3 holds again. The
   same rule in the oracle, written from its own reading. Pin the reviewer's case as an
   explicit example on both properties (checker vs oracle, search vs oracle). Correct ADR
   0016's line (`docs/adr/0016-route-search-core.md:405`) and ADR 0013's amendment to say
   it in plain words. If this changes the pruning rules, raise the pruning version again.
2. **Minor 1 (a false condition): a not-yet-approved loan that lends nothing** (no fee due,
   or every fee covered by provider support) no longer makes the route conditional. The
   condition and its verification come only when the loan lends something or its amount is
   unknown. Oracle too.

## List (not now)
Minors 2, 3 and 4: the final review (3 batched with migration 0033's CHECKs; 4 for Task 12b:
ask about the loan only on degree options).

## Then
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH).
- If `claude/confident-ramanujan-ux3saw` has moved, rebase onto it again (R15: renumber a
  clashing migration, regenerate the client, register last).
- Docker is still down: integration and acceptance not run.
- Append "Fix round 1" to `task-12c-report.md`; reply with the short contract and your head.

Hard rules as in your dispatch (no web, no live calls, no subagents, Edit/Write, never start
Docker, never read `.env`, never push, explicit pathspecs, disclose changed test inputs).
