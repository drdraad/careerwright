# Task 7b — fix round 1 (FIX_BASE 1c4bc07)

The review (`task-7b-review.md`) is Spec ❌, Needs fixes: Important 3, Minor 12. Read it in
full. These are the controller's rulings.

## Important

1. **I1: the package leaves out consequential labels. Ruling: fix as the reviewer says.**
   - Ask every fact whose field is pay, money or a date, including J06's `salary`.
   - Ask every option's `entry_requirements` and prerequisites.
   - Ask every essential requirement of kind credential or eligibility, gated or not.
   - Show the instrument-kind claims beside their spans.
   - **Move the generator into the repository** as a tool beside `tools.corpus` (you name
     it). It writes the whole package deterministically from the pinned pack, including the
     ordering and the "start here" text, so question numbers are stable. Add a fast test that
     the committed package equals the tool's output.
   - Why: the drift is reproduced. "Answer these first" still calls Q129 and Q135 "J06's two
     pay ranges" after `b38e462`. This round regenerates the package again, and Task 7c will
     apply answers by question number.
2. **I2: the cut does not close session 2's gates. Ruling: fix as the reviewer says.**
   - Order the package by the gates it closes:
     1. P01's section in full (TRACE-01's real option set);
     2. P03–P05's option, offering, outcome and funding rows (H-07 for Sprints 4–5);
     3. P03–P05's job and requirement rows last (Task 8 may take any left over).
   - Give each part its count and minutes. Replace "Answer these first" with "stop at the
     end of any part".
   - State the partial-record rule in the package and in ADR 0011, as the rule Task 7c
     applies: a record becomes `reviewed` only when every one of its rows is answered yes;
     otherwise it stays `proposed`, and a "no" records the correction for a later version.
3. **I3: claim values are loosely typed. Ruling: fix as the reviewer says.**
   - Document one value shape per citing record field in ADR 0011: money, pay, ISO date or
     month, datetime, duration, schedule and instalment. Keep them boring: numbers and ISO
     strings, never a string range.
   - Validate each value by the record field that cites it, not only by the claim's own
     field name. Include `valid_through` among the date fields.
   - Normalise C04's duration to numbers. Make `offering:C06.intake` unknown ("no future
     intake stated"), and keep its claim as a fact.
   - **Version: re-cut 0.1.0 in place.** Record it in ADR 0011 decision 3 the same way as
     `b38e462`. Why: nothing is pushed, nothing consumes it, and Tasks 9 and 11 should start
     from a single version. From the end of this task 0.1.0 is frozen: any later change is a
     new version. Keep `format_version` unchanged, because no consumer has ever read the
     untyped form. Cost if wrong: one more re-pin.

## Minor

- **Fix in this round:**
  - **M1:** the wording only. Say "no extraction was tuned on a holdout page", and record
    that the cross-class clause was added when the splits were assigned, and what it changed
    (C07 and C08).
  - **M2:** add J16 ("PRATAP PARTNERSHIP LTD") and `C09.training_provider` ("KAPLAN
    FINANCIAL LIMITED") to OI-13, each with where it appears.
  - **M4:** commit the JSON Schema export beside the packs, with a drift test. After I3 it
    should state the value shapes.
  - **M5:** record the real occurrence count. Offsets may stay capped at 5.
  - **M6:** reduce each NHS Jobs location value to what its committed excerpt shows. Then
    check every other excerpt-only claim for a value that its excerpt does not show, and
    report what you found and what you changed.
  - **M7:** represent J19's place the way J06 is represented. Keep J01's header statement as
    a fact. State the rule in ADR 0011: where one statement is a bound and another is a point
    at the same amount, the bound is the label.
  - **M8:** a test that `read()` over a pack with a holdout source touches no holdout page.
    Inject the evidence directory, so the test behaves the same in a clean clone.
  - **M10:** name ledger row 35 in J02's and J07's `why`. Never edit the ledger.
  - **M11:** correct decision 3's wording. Add the reviewer's two questions to the OI-07
    rights checklist, both to be answered before any push: may C08's committed excerpts
    stay, and should C01 and C08 be treated alike?
- **Parked for the final review (R12):**
  - **M3:** the validator's host, `fixture:` and reference coverage.
  - **M9:** batch-mode pacing in `tools.corpus`. Still add a full account of every same-host
    fetch to your report, including the scratch probes (`probe.py`, `raw.py`, `jsonld.py`).
- **M12:** already ledgered. Nothing to do.

## Also

- **No page fetch, no Adzuna, no Meta call in this round.** Everything above works from
  committed data, the kept bodies and your existing captures.
- Edit and Write for every repository change. A repository tool may write the generated pack
  and package. No `sed`, `awk` or heredoc edits.
- Never read `.env` or NESSA_HOME. Never push. No subagents. Never edit CLAUDE.md.
- Run `make check`. Run `make acceptance` once at the end only if you touch anything beyond
  `tools/`, the pack, its tests and docs, and say which.
- **Update your CLAUDE.md proposal** to match the new shapes and the generator.
- Append your report under "Fix round 1" in `task-7b-report.md`. Then reply with the short
  contract.
