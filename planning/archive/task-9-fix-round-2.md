# Task 9 — fix round 2 (FIX_BASE dffd08c)

Re-review 1 (`task-9-rereview-1.md`): 10 fixed, C1(b) partly fixed, new Important N1 and
Minors N2–N8. Read it in full, including its probes. These are the controller's rulings.

## Important

1. **C1(b), the bookkeeper. Ruling: read the chosen concept, not the label.** When a target
   came from an occupation choice, take its ESCO concept from that choice's source (its
   locator is the ESCO URI). Re-derive from the label only when no choice exists, and then
   prefer the occupation whose preferred label is the title. Two or more equal matches
   stay ambiguous, which is fail-safe. Add the bookkeeper case to the domain and API tests,
   reaching P05's pack target and its right-to-work gate.
2. **N1, the regression. Ruling: fix as the reviewer says.** A level-free answer given
   under another rubric fills a row only when the row has no answer under its own rubric.
   It never supersedes one, and the `other_rubric` prompt comes back. Test all three
   orders in the probe. Each test fails first.

## Minor

- **Fix:**
  - **N2:** give "only unresolved rows remain" its own reason or state, never `asking` with
    0 prompts.
  - **N3:** show a route chart only when there is something to plan.
  - **N4:** record a reason when a crosswalk is ambiguous.
  - **N5: count them as coverage gaps.** An unmodelled regulation gate beside modelled rows,
    or a required row with no rubric, is `insufficient_coverage`, because answers cannot
    settle it. Keep ADR 0012 decision 7's wording true.
  - **N6: eligibility alone is not coverage.** "Ready" needs at least one modelled skill row
    or a practice or recognition gate. A target whose only modelled requirement is the
    right to work is `insufficient_coverage`. Record this as provisional R6. Why: it is
    fail-safe, in the spirit of C1.
  - **N7:** add the forward risk to decision 4's consequences. Task 7c's reviewed pack and
    live research must type a UK-regulated role's gate whatever ESCO's flag says. The
    controller carries this to Task 7c.
  - **N8:** state in ADR 0012 and in migration 0030's docstring that 0029 ran only on test
    databases on this unpushed branch, and what a legacy contradictory row would do. A
    populated-upgrade test is R12, for the final review.

## Also

- The same rules as before:
  - Edit and Write only;
  - never read `.env` or NESSA_HOME;
  - no live calls, never push, no subagents, never edit CLAUDE.md;
  - pack 0.1.0 untouched.
- Run `make check`, then `make acceptance` once at the end.
- Append under "Fix round 2" in `task-9-report.md`. Reply with the short contract.
