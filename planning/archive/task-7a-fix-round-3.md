# Task 7A — fix round 3 (FIX_BASE 1132cf0)

Three reviews of round 2:
- `task-7a-rereview-2-B.md`: 8 of 8 fixed; new Minor M1–M3.
- `task-7a-rereview-3-A.md`: 4 of 4 fixed; new Minor R3-1 and R3-2.
- `task-7a-review-C.md`: part 2, Spec ❌; Important I1 and I2, Minor M1–M7.

Read all three in full. The items below are the controller's rulings, and every one is fixed
now. Order: security and rights first, then money, then honesty, then the rest. One commit per
coherent group. Tests RED first where practical.

## Rights: no third party's details in a body or a model input

1. **C-I1 with R3-2. Ruling:** for the model input, normalise first, then redact, then cut to
   bytes.
   - Normalise means: decode, collapse every whitespace form (NBSP, newlines, tabs), and drop
     non-printing characters (zero-width space, soft hyphen).
   - Phone separators also match horizontal Unicode spaces, never line breaks, so kept
     bodies are covered too.
   - For kept bodies, fail safe: after a body is redacted, check its normalised visible text
     for details. A detail found there means the body is not kept: excerpts only, with a
     typed `body_not_kept` reason.
   - Tests on the model input and on a kept body: the four forms in C-I1 (NBSP, a phone split
     by newlines, a zero-width space, a soft hyphen).
2. **R3-1. Ruling:** for detection only, decode JavaScript escape forms (`\xNN`, `\u{…}`,
   octal) as well as JSON's. A hit means `block_unredactable`, so the body is not kept. Do
   not write a JavaScript parser.
   - Correct the "JSON-LD block" wording in `BodyNotKept`'s comments and in ADR decision 4.
   - For 0020, note the correction in the new migration or the ADR. Never edit 0020.
   - Test: probe case 15, plus a `\u{…}` and an octal case.

## Money: unknown beats wrong

3. **C-I2. Ruling:** the span pay reader refuses what it cannot read exactly. Each refusal is
   `salary_invalid`, so pay stays unknown with the issue.
   - A range where only one side carries a multiplier (`£30-35k`, `£25-30K`, `£30 - £35k`)
     is refused.
   - A number followed directly by a letter other than `k`/`K` (`£1.2m`) is refused.
   - A trailing `max`, `maximum` or `up to` reads like a leading "up to": a maximum only, with
     the minimum unknown.
   - Add these cases to the existing exact-reading and unknown-with-issue tests.
4. **Cancellation cascade.** This was ruled in round 2 and is fixed here: cancelling an
   acquisition cancels its extraction runs that have not yet settled. Each cancel goes in its
   own `try`, as B-M8 did.
   - Test: cancel an acquisition whose extraction runs are queued; they end cancelled and make
     no provider request.
5. **MODEL-08's estimate. Ruling:** the spec says to "display estimated incremental cost
   before deep research". An acquisition now starts up to 5 model runs on the person's key.
   - Expose the acquisition's worst-case model spend before submission: `MAX_EXTRACTIONS_PER_ACQUISITION`
     × one extraction run's reservation, for the workspace's model.
   - Compute it in deterministic Python and put it on a read the UI makes before it starts
     an acquisition. Choose the smallest place and say which.
   - Task 8 shows it on screen. Update the MODEL-08 row.
6. **C-M3:** the budget pre-check counts only this acquisition's started runs that have no
   reservation yet, so a run is never refused as `budget_exceeded` when the budget allows it.
   Add a `budget_exceeded` test and a `model_not_permitted` test.
7. **C-M4:** add a UTF-8 byte-length validator to `ExtractionInput.text`. Test it with
   multi-byte text at the bound.

## Honesty of state

8. **C-M1:** a negator (`not`, `no`, `non-`) before a work-mode word gives
   `work_mode_unclear`, never the word. Test "Not remote" and "This role is not hybrid".
9. **C-M2. Ruling:** follow DUR-05, so a cancelled run's accepted result is kept. Coverage and
   `model_extraction.state` must agree with what was recorded. A recorded posting reads as
   read and is counted. Test the in-flight cancel.
10. **C-M5:** a model-read page whose every posting conflicts gets its own state, for example
    `postings_conflicting`, with words in `vocabulary.ts`. It is never `postings_read`.
11. **B M1. Ruling:** read side only. An attempt counts as pending only while its run is
    `queued` or `running`. Otherwise it reads as failed/interrupted in coverage and the
    listing, never `sources_pending` or "none found".
    - Test: a recording that rolls back, and a crash followed by a cancel.
12. **B M2:** `set_favourite` takes `lock_workspace_records`. Test a favourite set across a
    merge.

## The rest

13. **C-M6:** "ADR 0009 decision 13" becomes decision 15 in the five files named.
14. **C-M7:**
    - Exercise the SQL cap's refusal at 5, and the refusal of another run's attempt, in the
      guard test.
    - Replace the private `_empty_reason` import with the public listing.
15. **B M3:** drop the old test name from ACQ-03.

## Also

- Update ADR 0009 (decisions 4 and 15), the register (ACQ-03, ACQ-06, MODEL-08 and any row
  these change) and the proposed CLAUDE.md wording in your report if it changes. Do not edit
  CLAUDE.md.
- Say whether DBOS `application_version` changes. It must change if a workflow's step
  sequence does.
- No live calls in this round.
- Run `make check`, then `make acceptance` once at the end, and name each covering test.
- File changes use the Edit and Write tools only: no sed, heredocs, one-liners, `touch`, or
  `rm` of tracked files.
- Never read `.env` or NESSA_HOME. Never commit `~$ssa_Local_Development_Plan.docx`. Never
  touch the agentsolve-* or eigenprompt-* Docker projects. No subagents.
- Append the report to `task-7a-report.md` under "Fix round 3", then reply with the short
  contract: status, commits, a one-line test summary, and concerns.
