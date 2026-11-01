# Task 6 re-review 2 (fix diff cfdae68..0d1dd75)

This is a scoped re-review. I checked A-I-1 and N-M1..N-M9 against the controller's ruling and looked for regressions in the fix diff. It is not a fresh full review. Commit 3dcac83 (the planning handover) was skipped as instructed.

## Method

**Reading.** I read the contract, the re-review 1 findings, the report's "Fix round 2" section and the 3k-line diff, in three passes:
1. backend source;
2. tests and tools;
3. web, docs and register.

I treated the report as unverified claims.

**Focused checks.** Each check answers one named doubt.
- `cd backend && uv run --locked pytest tests/domain/test_safety.py -q` gave **41 passed** (ACUTE 18, MENTION 11, ORDINARY 6, plus the rest).
- Probe of `screen_message`, run with `uv run --locked python -c` and no files written. Doubt: does ordinary career phrasing reach tier 1, and does every risk phrase reach a tier? I used career and workplace phrasing only and wrote no distress text. Results are quoted below.
- Probe of `SalaryInput.model_validate` with a stored `SalaryFloor` of £0. Doubt: does the N-M2 revert guard actually catch it? It raises `ValidationError` ("a salary floor is more than £0…"), so `commands.py:209-216` maps it to `no_longer_valid`.
- Named-risk reads outside the diff:
  - `identity/receipts.py` and the `command_receipts` schema, for the risk that the tier-2 note is persisted;
  - `Alert.tsx` and `YouChapter.tsx`, for the risk that the note is not announced;
  - the `SalaryFloor` and `input_type` call sites, for the risk that a £0 floor now gets in through another path;
  - the `inferred_sensitive_terms` callers;
  - `observe_discovery_offline` → `compute_slate`.

**Not done.** No Docker or integration runs, no live calls, no `.env`, no full suites, no edits to the repository.

## Per finding

| ID | Verdict | Evidence |
|---|---|---|
| A-I-1 | **Partially fixed** | See below. The two tiers are wired correctly, but the ruling's "ordinary career phrasing never reaches tier 1" and "no risk term is ever silently dropped" are not met, and the tier-2 note is stored and not announced (I-1..I-4). |
| N-M1 | Fixed | `tests/integration/test_discovery.py:430` adds revert to the cross-account and missing-workspace 404 sweep. |
| N-M2 | Fixed | `document.py:128-136`: the `> 0` rule is on `SalaryInput` only, so a stored £0 `SalaryField` still reads (`test_profile_document.py::test_a_stored_floor_of_nothing_from_before_the_rule_still_reads`). History and export read `ProfileDocument`, so they are fine. Revert refuses at `commands.py:209-216`; I confirmed by probe that the validator fires on a stored instance. Other inputs still refuse £0: `interview.py:276` (`_salary`), `:383` (`input_type`), `conversation.py:306` (edits) and `document.py:351` (PUT). The revert refusal path is untested; I judge that **Minor** (pre-release legacy data only, three lines, and I verified the mechanism), see M-3. |
| N-M3 | Fixed | `slate.py:237`: `a.family_code == b.family_code and (...)`. `family_code` is the ISCO minor group from the database (`taxonomy_store.py:348`). Tests: `test_slate.py:206` (biochemist ↔ chemist across 211/213 does not fold; a within-921 alias folds), and `:144` (the chain is gone; a within-family chain is still not followed). The counts are in ADR decision 5 and the H-12 checklist: 319 pairs, 155 across groups, 164 within, with the example physiotherapist ↔ occupational therapist. That agrees with my round-1 probe of 154 cross-group pairs; the difference of one comes from the approximation. |
| N-M4 | Fixed | `safety.py:280-281`: `kindred=False` by default. Only `discovery.py:191` passes `True`. `interview.py:330` uses the default. Test: `test_safety.py` "a search may name… but a reply may not". |
| N-M5 | Fixed | `live_eval.py:285,290` prints ``Budget scope `…` `` in the header. `test_live_eval_ledger.py` asserts it. |
| N-M6 | Fixed | `Conversation.tsx:270-280,338`: `onError` resets `focusQuestion`. The Vitest case "does not move focus later if saving the choice failed" covers it. |
| N-M7 | Fixed | `interview.py:357-361`: the "?" rule and the one-question count apply only when `next_question` is set, so no paid repair is spent when there is no next question. `evaluation.py` `one_question` checks the reply as the question when there is none, and still fails two asks (`test_evaluation.py`). The repair rate is in the H-12 checklist. |
| N-M8 | Fixed | `exploration.py:297`: `U[A-Z]` is said "you". Test: `with_article("UX designer") == "a UX designer"`. |
| N-M9 | Fixed | `test_discovery.py::test_a_slate_read_against_another_release_than_its_searches_says_so` goes through `observe_discovery_offline` → `compute_slate`, the production function that inserts the note (`exploration.py:470`). It is an integration test, which I did not run. |

### A-I-1 in detail

What is right:
- **Wiring.** `conversation.py:233` blocks only `SupportTier.ACUTE` without `send_after_support`. Everything else returns `TurnSent` with the concern. `routes_interview.py:89-90` gives a 202 `TurnSubmittedOut`.
- **The concern never reaches the model.** I grepped `concern` and `support_note`: neither enters `_context` or the run.
- **Sending is never blocked.** The note renders after a successful send, and the field is cleared.
- **Dismissal works** (`Conversation.tsx:112-137`), and focus is not moved on show.
- **No word-after exclusion lists remain.** Every `_RISK` match reaches at least tier 2 by construction (`safety.py:158-164`).
- **The tests still pass.** All earlier positives remain in ACUTE. The 8 earlier career false positives are MENTION. SUP-09..13 now expect `support_note: true`.

What falls short of the ruling is listed as I-1..I-4 below.

## New issues in the fix diff

### Critical
None.

### Important
All four are in the A-I-1 fix itself, and are listed here so each has its own fix.

**I-1. Ordinary career phrasing still reaches tier 1** (`safety.py:43-59`). The ruling requires that it never does, and every document claims it doesn't: ADR 0007 `:167-170`, register PROF-09, `sprint-2.md:246` ("no career phrase is blocked"), and the module docstring ("first-person"). Three branches don't check who is speaking.
- **The `{_INTENT}\s+(?:just\s+)?{_ACT}` branch (`:54`) has no subject.** `_ACT` holds bare `die`, `dying` and `suicide`, with only `\b` after them (`:49-50`).
  - Probe, all ACUTE:
    - "I have been thinking about suicide prevention work." (this is the ADR's own tier-2 example, with "thinking about" in front);
    - "I am thinking of suicide prevention as a career.";
    - "I think the high street is going to die.";
    - "Print is going to die, so I want to retrain.";
    - "I am going to die of boredom in this job.";
    - "I am ready to die on this hill about remote work.".
  - This also contradicts the documented known limit "third-person wording gets nothing".
- **`feeling\s+…suicidal` (`:56`) has no subject.**
  - Probe, ACUTE: "I answer calls from people feeling suicidal on the helpline." and "I support young people feeling suicidal as a youth worker."
  - This is the helpline and support-work class that SUP-09 exists to protect.
- **`I(?:'ve|\s+have)?\s+…self[- ]?harm` (`:57-58`) reads "I have" as a possessive.**
  - Probe, ACUTE: "I have self-harm awareness training from my NHS role."
- **`(?:been|keep|kept|started)\s+(?:hurting|cutting)\s+myself` (`:59`) catches workplace injuries.**
  - Probe, ACUTE: "I kept cutting myself on the packaging tape at the depot." and "I have been hurting myself lifting boxes at the warehouse."
  - The last one is the A-I-1 warehouse case with "have been" added.

"Send my message anyway" softens the effect, but the ruling is explicit.

*Fix:* add positive evidence of who is speaking and what they mean, not exclusion lists:
1. The intent branch needs a first-person subject before the intent phrase. Allow optional "'m", "'ve been" and adverbs, which keeps every ACUTE case: they all have "I" before the intent.
2. `die`/`suicide` after an intent phrase need `_END` (end of clause) or a conjunction, not a following noun.
3. `feeling suicidal` needs "I'm" or "I've been".
4. The self-harm branch needs a verb form after "have" or "'ve" (`self-harming` or `self-harmed`), keeping bare "I self-harm".
5. Put the been/keep/kept workplace-injury overlap to H-12 explicitly.

Add the career phrasings above to MENTION, and correct the four claims.

**I-2. Some risk phrases reach no tier and are silently dropped** (`safety.py:74`, with `:44`, `:66`, `:76-77`, `:80`).
- **"cutting myself" is the main case.** `(?:kill|hurt|harm|cut)(?:s|ing|ed)?\s+myself` cannot match "cutting" (doubled t). Outside tier 1's narrow "I've been/keep/kept/started" prefix, "cutting myself" therefore matches nothing.
  - Probe: "I was cutting myself on the packaging tape at the depot." → **None**, while "I cut myself on the packaging tape…" → MENTION.
- **The same inflection gaps, read from the code:**
  - "cannot" / "can not go on" (`can{_A}t` only, `:66`, `:80`);
  - "taken my (own) life" (`t(?:ake|akes|aking|ook)`, `:76`);
  - the `-ing` form of "want" before "die" (`want(?:ed)?\s+to` in both `:44` and `:77`; round 1's intent list had `wanting`).
- This breaks "no risk term is ever silently dropped". None of these is in the known limits.

*Fix:* use `cut(?:s|ting)?`; add `cannot|can\s+not`, `taken` and `wanting\s+to`; pin each inflection with a MENTION case written in workplace wording.

**I-3. The tier-2 note is stored** (`routes_interview.py:89-90`, `identity/receipts.py:66-79`).
- The 202 response, including `support_note` (`policy: "risk_mention"`), is recorded in full in `nessa.command_receipts.response` (jsonb) for the life of the workspace, because `CommandResult.record` defaults to True.
- The ruling and five claims say it never is:
  - `interview_schemas.py:179` ("Nothing about it is stored");
  - `conversation.py:94`;
  - `queries.ts:343`;
  - ADR `:167`;
  - the test comment at `test_interview_choices.py:172`.
- That test only checks the turn listing, so it cannot see the receipt.
- It persists a label derived from the person's message, against the module's promise that the screen "scores, labels or remembers" nothing. The message text is already in the turn, so the extra exposure is small, but the documented property is false.

*Fix:* record the receipt without `support_note`, and attach the note in the route from `screen_message(body.message)` for both fresh and replayed responses. A replay has the same request by fingerprint. Then assert in the integration test that the receipt row holds no `support_note`. If the controller instead accepts the receipt copy, correct the five claims.

**I-4. The tier-2 note is not announced** (`Conversation.tsx:112-137,418`).
- `SupportNote` is a plain `<section aria-labelledby>`. It is not a live region, and it does not call the `announce` prop, which exists for exactly this: the one polite `role="status"` region at `YouChapter.tsx:130`.
- After sending, focus stays in the composer, so a screen-reader user is never told that support information appeared above it.
- The tier-1 notice does announce (`Alert … announce`, `:147`).
- The Vitest case only checks that the region exists.
- The controller's check asked for "announced politely".

*Fix:* when a new note arrives, call `announce(...)` with a short polite sentence that says the message was sent and where the note is. Assert the announcer text in `YouChapter.test.tsx`.

### Minor
- **M-1** (`Conversation.tsx:128`): "Dismiss" removes the focused button, so focus falls to `<body>`. Move focus to the reply field on dismiss, and assert it.
- **M-2** (`safety.py:62-64`): "don't" and "do not" are handled differently.
  - "don't want to be here" at the end of a clause is tier 1, but "do not want to be here" is tier 2. "live this way" exists only for "don't".
  - Round 2 also widened tier 1 from "be here any more" to "be here" at any clause end. That is a common job phrase, and it is not in the H-12 known limits.
  - Make the two spellings the same, and list the "be here" line for H-12.
- **M-3** (`commands.py:209-216`): the N-M2 refusal (`no_longer_valid`) has no test.
  - A domain test can build the stored document directly, as `test_profile_document.py` does, and call the input conversion. No hand-inserted database row is needed.
  - Low risk: I verified the validator raises `ValidationError` on a stored instance.
- **M-4** (`Conversation.tsx:5-6`): the header comment still describes one tier ("A message that explicitly expresses acute distress…").

## Assessment

**Task quality:** Needs fixes

**Reasoning:** N-M1..N-M9 are all fixed with real tests, and the two-tier wiring (blocking only ACUTE, never sending the note to the model, never blocking a send) is correct. A-I-1 is still only partly fixed:
- tier 1 still blocks career phrasing in three subject-blind branches;
- an inflection gap silently drops "cutting myself";
- the "never stored" note is persisted in the idempotency receipt;
- the note is not announced.

Each of these contradicts the controller's ruling or a claim in the ADR and the register, and each has a small, targeted fix.
