# Task 7b — fix round 3 (FIX_BASE 8f61821)

Re-review 2 (`task-7b-rereview-2.md`): 8 of 8 fixed, one new Minor, R2-1. Read R2-1.

## Ruling: fix R2-1 with a declared "no end"

- Give the duration shape one declared way to say "no end" (for example `unbounded: true`).
  Declare it in ADR 0011 decision 13's table, and say that null still means only "the page
  withholds or lacks the value".
- Set `C03.access_period` from its excerpt ("Lifetime access").
- Have the generator show it as "no end (lifetime)", so Q99 can be answered yes.
- Re-cut 0.1.0 in place under the same ruling, recorded in decision 3 as part of the last
  re-cut. Regenerate the pack, schema and package with `tools.option_pack_files`.

Why now: 0.1.0 freezes when this task ends. Left as it is, Q99 forces a "no" that keeps
`option:C03` `proposed` because of a format limit, not a label error.

## Also

- The same rules as rounds 1 and 2.
- Run `make check`.
- Append under "Fix round 3" in `task-7b-report.md`. Reply with the short contract.
