# Task 6 re-review 4 (fix diff 6b1d3b9..b608e7d)

This is a scoped re-review of fix round 4, the support-screen redesign. I checked it against required-design items 1–8 (`task-6-fix-round-4.md`) and looked for regressions in the 3.3k-line diff. It is not a fresh full review. I treated the report's "Fix round 4" section as unverified claims.

## Method

- **Read:** the contract, the round-4 brief, re-review 3, the report's "Fix round 4" section and the whole diff. I read it in two passes: backend source and tests, then web and docs.
- **Ran:**
  - `cd backend && uv run --locked pytest tests/domain/test_safety.py -q` gave **698 passed** (692 table rows plus 6 other tests).
- **Probes** of `has_risk_stem` (`python -I`, one-off scripts, nothing written to the repository).
  - Each probe is an *existing* career-phrased table row, changed only in the one form under test. I wrote no distress or self-harm text.
  - Controls (the unchanged rows) stayed `True`.
  - I also timed pathological whitespace inputs at the 2,000-character bound: each took 0.1 ms or less, so there is no backtracking risk.
- **Structural reading** of every `_RISK` branch (`safety.py:36-66`), axis by axis: inflection, negation, contraction, person, tense and adverb.
- **Named-risk reads outside the diff:**
  - The refusals `submit_turn` can raise before the panel is derived (`conversation.py:191-230`, `identity/runs.py:168-205`).
  - The base `INSTRUCTIONS` (`interview.py:441-480`), checked for any wording that names the screen. There is none.
  - The pre-Task-6 `SubmitTurn` and `TurnOut` shapes (`git show b51d2b7^:…`), for item 7.
  - `git grep` at HEAD for remnants of the tier design.
- **Not done:** Docker or integration runs (so `test_interview_choices.py` was not run by me), Vitest, Playwright, full suites, live calls, `.env`, edits to the repository.

## Per required-design item

| # | Verdict | Evidence |
|---|---|---|
| 1 | **Partially met** | The design is right. There is one deterministic screen (`safety.py:49-68`, `has_risk_stem` `:125-127`) with no tier, no intent judgement and no blocking. Each stem branch has its own leading `\b`, so the re-review 3 no-stem rows (lifeguard, lifelong, lifestyle, without meetings) are now NO_FLOW (`test_safety.py:257-266`). But inputs holding a listed stem still pass unflagged: negation, contraction, tense and adverb forms are each handled per family, and several families lack forms that other families accept. See **I-1**. |
| 2 | **Met, with I-2** | Every accepted send is a 202 with the turn. The 200 path, `SupportShown` and `send_after_support` are gone (`routes_interview.py:54-91`, `conversation.py:191-230`). The panel is a named `<section>` region, not an alert. It shows the services and the checked date (`Conversation.tsx:113-145`), is announced politely without moving focus (`:234-241`), is dismissible with focus returned to the reply field (`:390-397`) and sits beside the conversation. The question steps aside while the panel shows (`:376`). Tests: `YouChapter.test.tsx` "[PROF-09] a message with a risk stem…", `e2e/conversation.spec.ts:117-148`. But a *refused* send never shows the panel (I-2). |
| 3 | **Met** | `interview.instructions()` (`interview.py:517-523`) appends `SUPPORT_TURN_INSTRUCTION` only when `messages[-1]` (the current message) has a stem. It is recomputed from the sealed input on every request, the repair included (`interview_agent.py:113`). The context JSON has the same keys either way. Neither the instruction (`safety.py:77-81`) nor the base `INSTRUCTIONS` names the screen or the stem. Tests: `test_interview_contract.py` (only on flagged turns, not when the stem is only in an earlier message, the label scan) and `test_interview_agent.py` (both requests carry it). The model's reply is not checked for a question (M-4). |
| 4 | **Met** (by reading; integration test not run by me) | Nothing new is written. The receipt records `TurnOut` only (`routes_interview.py:70-72`), and the panel is derived after `run_idempotent` (`:84-86`). The sealed `TurnInput` has no flag, and `prompt_version` is the same for every turn. The instruction is computed inside the activity, never passed as an argument or journalled. Nothing logs the flag. The integration test claims a scan of both databases, the worker log, the API log and the export. The model's *response* to the instruction (no `next_question`, the acknowledging reply) is stored like any reply. That is inherent to item 3, not a flag. Residue: rounds 0–2 receipts on developers' local databases still hold the old note text. It is documented (ADR decision 7, "Never stored") and pre-release. |
| 5 | **Met, except `CLAUDE.md`** | The tier-1 classifier and response, `CommandResult.record`, the web alert, its tests, the `you--support` capture, the ADR tier text and the register claims are removed. `git grep` at HEAD finds one stale *current-state* description, **`CLAUDE.md:66-69`** ("fixed support response before any model call … two tiers"). The other hits are fine: `docs/reviews/sprint-2.md:222,245-265` is labelled history; ADR `:197,268` and `runbook.md:104` name `send_after_support` only as removed; the old-receipt test plants the old shape on purpose. |
| 6 | **Partially met** | The one table has all three row groups: stem forms → flow; the reviewers' no-stem career examples → no flow; stems in career phrasing → flow, listed in H-12. The instruction, never-stored and announced/dismissible tests exist. But the "every stem × inflection/negation/tense" rows mirror each family's own regex alternations, so they cannot see the gaps in I-1. See "The 692-row table" below. |
| 7 | **Met** | Dropping `send_after_support` changes the fingerprint of every round 0–3 receipt, so `_replay` refuses it with `422 IDEMPOTENCY_KEY_REUSED` (`receipts.py:40-47`) before the response is read. A tolerant read would never be reached, so leaving it out is justified. An old client body gets `422 VALIDATION_FAILED` (`extra="forbid"`). Test: `test_a_turn_receipt_stored_before_the_redesign_is_refused_never_a_500`. Its RED (500) and GREEN were claimed; I did not run them. It literally meets "must not 500". **Is a 422 for a legitimate retry acceptable pre-release? Yes:** there is no deployed client or data, and the window is a retry that straddles an upgrade on a local machine. The error's *reason* is wrong for that client, though (M-5). |
| 8 | **Met** | ADR 0007 decision 7 (`:148-207`) records: why one screen (the three rounds' failures, C-1/N-I1/N-I2), the exact stem list, the flow, never stored, the old-receipt behaviour, the known limits and provisional status. The H-12 checklist (`:275-284`) and the register H-12 row (`requirements-register.md:629`) list the three required limits: a finite English stem list, false positives that show the panel, no intent judgement. Minor: some coverage claims are too strong (M-1), and the refused-send gap is not listed (I-2). |

### Item 1 in detail: what passes unflagged

From the code, then confirmed where career phrasing allows. Each probe below is an existing row changed in one form. All returned `False`.

| Family (`safety.py`) | Form the family lacks | Accepted elsewhere? | Probe (from row) |
|---|---|---|---|
| not want to live / be alive / be here (`:63`, `_NOT` `:43`) | Contracted perfect or progressive negation: `hadn't`, `hasn't`, `haven't`, `wasn't`, `isn't`, `aren't`, `weren't`, `ain't`. `_NOT` lists only `do/does/did/wo/would/could/should` + n't. The uncontracted `had not` passes only through `\bnot`. | Uncontracted, yes | "He hadn't wanted to live in London." / "She hasn't wanted to live in Leeds." / "I haven't wanted to live in London for years." / "I wasn't wanting to live in London." |
| same | `wanna` in place of "want to" | Yes, in `_INTENT` (`:39-42`) | "I don't wanna live in London." |
| same | More than one adverb, or an adverb outside the closed list of eight (`_ADVERB` `:36` is one optional word) | — | "I don't even really want to live in London." / "I never ever want to live in London." |
| cannot go on (`:65`, `_CANNOT` `:44`) | `no longer`: "can / could no longer go on" | Yes, `no longer` is in `_NOT` | "I can no longer go on with the accounting course." / "I could no longer go on with the accounting course." |
| same | Any adverb (no `_ADVERB` slot) | Yes, in 4 other families | "I can't really go on with this course." / "I can't just go on with this course." |
| no reason to live / go on (`:64`) | Any negation but the determiner `no`: `not / n't … any / a reason`; the plural `reasons`; an adjective between ("no real reason") | — | "There isn't any reason to go on with the course." / "There are no reasons to go on with the course." |
| wish … dead / die (`:60-61`) | (1) Contracted `'d`: `{_WHO}\s+(?:could\|would)` needs whitespace and the full modal. (2) Past perfect: no `had` (or `'d`) + participle, nor `had been dead`. (3) No adverb before `dead`. (4) Subjects are pronouns only, so a named or noun subject never matches. | Adverb before `die`, yes | From the code only; no probe written |
| end / take + life (`:56-57`, `_LIFE` `:38`) | Possessive pronouns only, so a noun possessor or a bare "own life" fails | — | "He took own life savings out." (False) |

These are the same contracted/uncontracted and adverb-slot asymmetries that were found in rounds 2 and 3 (M-2, N-I2, C-1), now spread across families. The table cannot catch them because each axis is applied only to the family that already has it (next section).

### The 692-row table

The count checks out: 636 generated + 36 sentences + 20 no-stem = 692. It contains two intentional case variants ("Suicide", "SELF-HARM") and no other duplicates. The rows are real forms, not padding by repetition. But the count overstates the coverage:

- **392 of the 636 generated rows are full cross-products of independent alternations:**
  - verb × reflexive: 140 rows (14 × 10);
  - verb × possessive × life: 252 rows (9 × 7 × 4).

  Each alternative fails or matches independently, so about 30 rows (each alternative once) would cover exactly the same branches. The cross-product adds count, not coverage.
- **Every axis is local to one family:**
  - `NOT_WANTING` feeds only the live / alive / here family;
  - `CANNOT` feeds only go-on;
  - adverbs feed only intent + die, thinking + dying and one wish row.

  The table therefore checks the regex against the implementer's own enumeration of the same alternations. It cannot reveal a form one family accepts and another lacks, which is every gap in I-1.
- **The 36 sentence rows and 20 no-stem rows are meaningful.** They are the round 1–3 corpus, the re-review 3 probes and the reviewers' career examples. They are the part of the table that found real regressions.

## New issues

### Critical

None.

### Important

**I-1. The screen still lets listed stems through in common negation, contraction, tense and adverb forms** (`safety.py:36,43-44,60-65`). The required design's acceptance line is "Nothing containing a listed stem may pass unflagged", in any inflection, contracted or uncontracted negation, person or tense. The table above shows systematic classes that fail it:

- contracted perfect and progressive negations in the not-want family;
- `wanna` before "live";
- `no longer`, and any adverb, in the go-on family;
- every negation other than `no`, and the plural, in the no-reason family;
- the `'d` contraction and the past perfect in the wish family.

Several are first-person present or perfect statements of exactly the kind the flow exists for. In those cases the person sees no panel, and the interviewer gets no smaller-step instruction, so it asks a career question as usual. None of these was covered in round 3 either, so this is a missed requirement, not a regression.

*Fix:* stop hand-picking forms per family.

1. Define each axis once and apply it to every family where it can occur:
   - NEGATION: every auxiliary + n't, including `had/has/have/was/is/are/were/ai`; plus `not`, `never`, `no longer`;
   - ADVERBS: zero or more, `(?:\s+(?:…))*`;
   - the `want to` contraction `wanna`;
   - modal contraction: `'d` / `would` / `could`;
   - perfect: `had` / `'d` + `died` / `been dead`.
2. In the test, generate each shared axis × every family that admits it, not per-family lists, so a family that lacks an axis fails a row.
3. Extend the no-reason family to `(?:no|n't … any|not … any|n't … a) reasons?`, with an optional adjective.
4. Record noun subjects and possessors (wish, end/take) in H-12, or add them.

**I-2. A refused send shows no support panel: a regression for the round-3 tier-1 shapes** (`routes_interview.py:75-86`, `conversation.py:207-230`, `Conversation.tsx:399`). The panel is derived only after `run_idempotent` returns a 202. Any refusal inside `submit_turn` raises first and the web shows only `RequestFailure`. These refusals are:

- the stale profile version (`conversation.py:209`, 409);
- "too long" (`_context`, 422; the instruction adds 246 bytes, so a long flagged message reaches the bound slightly sooner: 6,194 of 8,500 bytes for 2,000 characters with an empty profile);
- the budget, a missing key, or the offline/demo mode refusals (`identity/runs.py:183-195`, `_provider_model`).

Round 3 screened tier 1 *before* the stale check and before any budget or key check, so those messages always got support. Now, a person whose send is refused for an ordinary reason (spend cap reached, no key) never sees the services. That contradicts item 1 ("triggers the support flow") on that path. The 409 path only delays the panel until "Send it again"; budget and key refusals never show it.

*Fix:* compute `has_risk_stem(body.message)` before `run_idempotent`, and carry the panel on a refused `submit_turn` as well. For example, add `support_note` to the error envelope's `details` for this command, and have `useSendMessage` set the note from it. Test it with a refused flagged send (stale version, or a budget refusal). Alternatively, the controller accepts the gap and it is listed in decision 7 and H-12. Pause is a separate, pre-existing case: the web disables Send, so nothing is screened while paused. It is worth one line in H-12.

### Minor

- **M-1. Coverage claims overstate the screen.** Until I-1 is fixed these are false:
  - `safety.py:8-9` ("in any inflection, person or tense, with contracted or uncontracted negation");
  - `test_safety.py:1-3`;
  - `docs/reviews/sprint-2.md:270` ("any listed stem in any form").

  The register (`:425`, "every listed … form") and ADR `:163-178` (an explicit list) are accurate. Reword the overstated claims, or fix I-1.
- **M-2. The "692 rows" figure** (register `:425`, sprint-2 review, report) reads as coverage. Most of it is cross-product count (see above). Either cut the products to one row per alternative, or keep them and stop citing the count as evidence.
- **M-3. Unicode forms of the apostrophe and hyphen are missed.**
  - `_A = [^\w\s]?` cannot match U+02BC (modifier-letter apostrophe), which Python's `\w` treats as a letter. "I donʼt want to live in London." gives `False`.
  - `self[- ]?harm` misses U+2010/U+2011 and the en dash. "self‑harm support services" gives `False`.

  *Fix:* normalise the message (NFKC, and map apostrophe and hyphen variants) before matching, and add one row each.
- **M-4. "Ask no career question this turn" is only instructed.** The rule "the model proposes; validated commands commit" makes a deterministic check cheap. On a flagged turn (recomputed from `messages[-1]`, so still never stored), `check_turn` could treat a non-null `next_question` as a validation problem for the one repair, or the server could drop it. Without that, a live model that ignores the instruction gets its question shown after the panel is dismissed. The implementer listed this for H-12. I recommend enforcing it instead.
- **M-5. Item 7's 422 gives a retrying client the wrong reason.** `IDEMPOTENCY_KEY_REUSED` says the key was used for a *different* request, but this is the same logical request. That is acceptable pre-release, as noted in the ADR and the report. Separately, R4-6's claim that "a receipt stored by any earlier round can never match" is not true of *pre-Task-6* receipts: at `b51d2b7^`, `SubmitTurn` had only `expected_profile_version` and `message`, so their fingerprint equals today's. They are harmless, though: `TurnOut` and its nested fields are unchanged apart from the widened `ProposedChangeOut.value`, so they replay as a 202 with no 500. Correct the claim.
- **M-6. `CLAUDE.md:66-69` is stale.** It still describes two tiers and a fixed response before any model call. It is the only stale current-state description. The user needs to update it; the implementer rightly did not edit it.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** The redesign is the right shape and items 2–5, 7 and 8 are met. There is one recall-first screen with no intent judgement and no blocking; the message proceeds; the smaller-step instruction is applied to that turn only and is unlabelled; and nothing of the flow is stored. Item 1 is not yet met, because forms are still handled per family (I-1), and a refused send loses the support panel that tier 1 used to give before any check (I-2). Both fixes are small and table-checkable.
