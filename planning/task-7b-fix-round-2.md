# Task 7b — fix round 2 (FIX_BASE 46de02d)

Re-review 1 (`task-7b-rereview-1.md`) found 10 items fixed, M6 and M7 partly fixed, and 7 new
Minors. Read it in full.

Pack 0.1.0 freezes when this task ends, so every correction to its data happens now or
needs a new version. That is why this round takes the data Minors rather than parking them.

## Rulings

1. **M6, the leftover:** `J19.working_pattern` takes only what its excerpt shows ("full
   time, 36 hours", in the schedule shape; see N3).
2. **M7, the leftover:** restore the header mention in `J01.salary`'s note. Locating the
   header waits for the next capture (carried to Task 8).
3. **N1:** keep C04's 12-month access as its own duration fact, at most 12 months. Mark the
   6–8 months as typical, never as bounds: either a `typical` flag in the duration shape or a
   separate fact. Your choice; declare it in ADR 0011 decision 13's table.
4. **N2:** add `repayable` to the rate shape, nullable, with null meaning unknown, never
   false. Set C08's support grant from its excerpt.
5. **N3:** map `access_period` to the duration shape and `working_pattern` to the schedule
   shape, or to one declared pattern-plus-hours shape. No duration or hours as free text.
6. **N4:** let `occurrences` be null for "not counted", stated in decision 2 and the `Claim`
   comment. Set `J01.salary_point` to null.
7. **N7:** add the C09 slot's `why` to OI-13's places for "KAPLAN FINANCIAL LIMITED".
8. **Re-cut 0.1.0 in place one last time,** recorded in decision 3 beside the round 1
   re-cut. Regenerate the package and the schema with `tools.option_pack_files`.

## Parked or carried

- **N5** (C03's title with its entity) and locating J01's header go to Task 8's recapture.
  The controller carries both.
- **N6** (`publish()` refusing a pinned version) is parked for the final review under R12.
  The freeze rests on the pin and the ADR until then.

## Also

The same rules as round 1:
- no page fetch, Adzuna or Meta call;
- Edit and Write for every repository change; a repository tool may write the generated
  pack, package and schema;
- never read `.env` or NESSA_HOME;
- never push, no subagents, never edit CLAUDE.md.

Run `make check`. `make acceptance` is not owed while no product module imports
`nessa.catalogue.option_pack`; say if that changes.

Check that the offline accuracy-read comparison still gives the same scored outcomes.

Append your report under "Fix round 2" in `task-7b-report.md`. Then reply with the short
contract.
