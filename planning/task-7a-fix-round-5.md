# Task 7A — fix round 5, the last (FIX_BASE 23d6337)

Round 4 was re-reviewed. `task-7a-rereview-2-C.md` found items 3–7 fixed and a new Minor
N1. `task-7a-rereview-5-A.md` found items 1–2 fixed and new Minor items R5-1 and R5-2. Read
both re-reviews in full.

Since round 4, the controller has committed two docs-only changes: 6bf6f4e and 23d6337, to
session 1's record and ADR 0009. Read ADR 0009's status line, decision 2 and decision 4's
known limits as they now stand, and keep them.

Every item below is a ruling and is fixed now. Tests go RED first.

1. **R5-2, with percent-encoding.** Ruling:
   - In `redact_value`, also redact each string's `html.unescape` form. JSON is re-serialised
     whenever it changes, so spans stay consistent.
   - For `NOT_TEXT` URL values (JSON-LD `url` and the like), and for HTML attribute values,
     only detect: decode entities **and** percent-encoding, then look. A hit means the body
     is not kept, with a typed reason.
   - Tests:
     - a JSON-LD `"url": "mailto:jane@recruit.example"`;
     - a `mailto:jane%40recruit.example` in an `href`;
     - an entity-encoded email inside a JSON-LD description, checked in the body and in that
       description claim's excerpt.
   - Remove the percent-encoded limit from ADR decision 4.
2. **R5-1.** Ruling: adopt the reviewer's rule. The label after a dot and whitespace must
   start lowercase, and no word character may follow the TLD.
   - Test "Follow @GOVUK. Sign up" and "Drop in @ 10am. Bring photo ID." as non-matches,
     beside R4-1's forms, which must still match.
   - Correct the ADR's over-match sentence.
3. **2-C N1.** Ruling: state both truths. Do not change the activity in this round.
   - `acquisition_model_spend` keeps the 3-attempt figure, described as "without a worker
     crash".
   - It also gives a hard maximum: `MAX_EXTRACTIONS_PER_ACQUISITION` × the workspace's
     per-run limit. The activity never reserves past that limit.
   - Fix the field descriptions, regenerate the client and commit it, then update MODEL-08
     and ADR decision 15.
   - Test both figures.
4. **Adzuna credential names.** The product owner says the credentials are in `.env`, but
   `make live-adzuna` finds no `ADZUNA_APP_ID`/`ADZUNA_APP_KEY`. Ruling: when the expected
   names are absent, the tool lists the names of the variables it found in `.env` whose name
   contains `ADZUNA` (case-insensitive).
   - It lists names only: never a value, never any other variable's name, and it makes no
     request.
   - Unit-test it with a temporary env file that holds synthetic values, and assert that no
     value appears in the output.
   - Then run `make live-adzuna` once. Put its blocked line, names only, in your report. If
     the expected names are present after all, the run makes its capped, ledgered free-tier
     requests. Report them.
   - You never open or print `.env` yourself. The tool's own code reads it.

## Also

- This is the last fix round. Anything you cannot fix, report as a concern with the reason;
  do not leave it silent.
- Say whether DBOS `application_version` changes.
- Run `make check`, then `make acceptance` once at the end, and name each covering test.
- No live Meta calls. The only live call allowed is item 4's.
- File changes use the Edit and Write tools only: no sed, heredocs, one-liners, `touch`, or
  `rm` of tracked files.
- Never read `.env` or NESSA_HOME. Never commit `~$ssa_Local_Development_Plan.docx`. Never
  touch the agentsolve-* or eigenprompt-* Docker projects. Never push. No subagents.
- Append your report under "Fix round 5" in `task-7a-report.md`, including any change to the
  proposed CLAUDE.md wording. Then reply with the short contract.
