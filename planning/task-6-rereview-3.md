# Task 6 re-review 3 (fix diff 0d1dd75..6b1d3b9)

This is a scoped re-review. I checked I-1..I-4 and M-1..M-4 from re-review 2 against the controller's ruling, and looked for regressions in the 1.2k-line fix diff. It is not a fresh full review. I treated the report's "Fix round 3" section as unverified claims.

## Method

- **Read:** the contract, `task-6-rereview-2.md`, the report's "Fix round 3" section and the whole diff. Then `safety.py` at HEAD (`6b1d3b9`) and the round-2 matcher (`git show 0d1dd75:backend/src/nessa/profile/safety.py`), side by side.
- **Ran:** `cd backend && uv run --locked pytest tests/domain/test_safety.py -q` gave **62 passed**.
- **Structural check** (`python -c` over the compiled patterns; no example text):
  - `"dying"` appears in neither `_ACUTE` nor `_RISK`.
  - `decided`, `urge`, `thought(s)`, `does\s+not`, `did\s+not`, `could\s+not`, `tries` and `tried` appear in neither pattern.
  - `_ACUTE` no longer ends with `)\b`. `_RISK` still does.
- **Probes** of `screen_message`, with career and workplace phrasing only. I ran each at HEAD and, where useful, against the round-2 module, loaded from a scratch copy at `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/215e3a32-af56-4146-900e-11d9bbf0dae9/scratchpad/safety_r2.py`. I wrote no distress or self-harm text. Results are quoted under the findings.
- **Named-risk reads outside the diff:**
  - `ResponseModel` (`api/schemas.py:31-34`, `extra="forbid"`): can the receipt be read back as a `TurnOut`?
  - `TurnSubmittedOut.sent` (`interview_schemas.py:199-208`).
  - `run_idempotent` (`identity/receipts.py:54-80`): receipts have no expiry.
  - grep for logging of API response bodies (none) and for web storage of the note (none; it lives only in `useState`, `queries.ts:343-344`).
  - The announcer (`YouChapter.tsx:56-63,130`): a repeated announcement is read again.
- **Not done:** Docker or integration runs, Vitest, live calls, `.env`, full suites, edits to the repository.

## Per finding

| ID | Verdict | Evidence |
|---|---|---|
| I-1 | **Partially fixed** | The three subject-blind branches named in round 2 are fixed: the intent branch now requires `_I` (`safety.py:54-57,69`); `suicidal` requires "I …" (`:70-72`); self-harm needs a verb form (`:73-75`); hurting or cutting needs a clause end (`:76-77`). Every I-1 phrasing is now a CORPUS row and is MENTION. But tier 1 still takes object and third-party frames, and dropping the outer `\b` (`:68,85`) made it fire on messages with no risk stem at all. See N-I1. |
| I-2 | **Partially fixed** | The named gaps are closed: `cut(?:s\|ting)?`, `cannot\|can not`, `taken` and `wanting` (`:93,95,96,48`), each with a row. Still missing: uncontracted `does not`/`did not` (`:99`), `could not` (`:100`) and `tries/tried to die` (`:96`), so those reach no tier (N-I2). Worse, the round-3 narrowing removed round-2 tier-1 shapes without adding them to tier 2 (C-1). |
| I-3 | **Fixed** | The receipt now records `TurnOut` only (`routes_interview.py:90-92`); the 200 support path keeps `record=False` (`:88`). The note is recomputed by `support_note_for(body)` on every 202, fresh or replayed (`:106-111`, `conversation.py:91-95`), and the replay has the same body because of the fingerprint check. The integration test asserts that no receipt row contains `risk_mention` or `support`, and that a replay returns the same turn and note (`test_interview_choices.py:175-188`; integration test, not run by me). No API code logs response bodies, and the web keeps the note only in React state. Every "never stored" claim (`interview_schemas.py:178-180`, `conversation.py:91-95`, `queries.ts:343-344`, ADR `:180-182`, runbook, register, `safety.py:19-21`) is literally true. |
| I-4 | **Fixed** | `Conversation.tsx:263-271` announces each new note object once, through the chapter's polite `role="status"` region (`YouChapter.tsx:130`; repeats are re-read, `:59-63`). Focus is not moved. `YouChapter.test.tsx:676-679` asserts the announcer text and that focus stays on Send. |
| M-1 | Fixed | Dismiss focuses the reply field (`Conversation.tsx:436`); test `YouChapter.test.tsx:682`. |
| M-2 | Fixed | "don't" and "do not" share `_NOT` (`safety.py:47,81`). Tier 1 needs "be here any more" (`:81`), and the bare form is listed for H-12 (ADR `:184-191`, checklist). New asymmetries of the same kind are in N-I2 and M-a. |
| M-3 | Fixed | `restored_answers` is extracted (`commands.py:211-231`). The refusal is asserted in `test_profile_document.py::test_a_stored_floor_of_nothing_from_before_the_rule_still_reads` (not run by me). |
| M-4 | Fixed | The `Conversation.tsx:5-8` header describes both tiers. |

## New issues

### Critical

**C-1. The round-3 narrowing drops round-2 tier-1 shapes to no tier** (`safety.py:58-66,96-97`). This is a regression in the safety screen.

The round-2 matcher (`0d1dd75`, `_INTENT`/`_ACT`) gave tier 1 to:
- an intent phrase + `dying`, where the intent was `thinking/thought/think about|of` or `thoughts of`;
- an intent phrase + `die`, including the intents `decided to` and `urge(s) to`;
- an optional `just` between the intent and the act (`{_INTENT}\s+(?:just\s+)?{_ACT}`).

Round 3:
- removed `dying` from `_ACT`, so `die{_END}` is the only form of the act. That leaves the gerund that "thinking about" grammatically takes uncovered, although every other act keeps its `-ing` form (`ending`, `killing`, `taking`, `hurting`, `harming`);
- removed the `just` slot;
- removed those intents.

`_RISK` has no `dying`. Its "to die" family requires `…to\s+die` with nothing in between, and has no `decided`, `urge`, `thought(s)`, `tries` or `tried` (structural check above).

So a first-person present ideation statement of these shapes now gets **neither** the support response **nor** the note. Its message goes to the model with nothing beside it. This contradicts the controller's ruling ("every risk stem in every inflection … nothing containing a risk stem reaches no tier"). It also contradicts the claims at `safety.py:19-20,88-89` and ADR `:182-183`, and the ADR's own tier-1 list, which names "am thinking about + … die". The CORPUS has no row for any of these shapes, so the 62 green tests cannot see the gap. I judged this from the patterns' structure and wrote no example text.

*Fix:*
1. Tier 1, first-person: add `dying` after the `thinking|think about|of` intents in `_ACT`, at a clause end like `die`. Restore an optional adverb slot between the intent and the act.
2. Tier 2: add the gerund after `(?:thinking|thought|think|thoughts)\s+(?:about|of)`; add `decided`, `urges?`, `tries` and `tried` to the "to die" intents; allow an optional adverb before `die`.
3. Add one CORPUS row per shape.

`I'm dying to try woodwork` stays NONE: none of these intent phrases precede it.

### Important

**N-I1. Tier 1 still reaches object and third-party frames, and now fires on messages with no risk stem** (`safety.py:63-66,78,80,85`).

*Regression from the dropped `\b`.* Round 2 wrapped `_ACUTE` in `\b(?:…)\b`. Round 3 keeps a leading `\b` on each branch, but the closing `r")"` (`:85`) has none. So any branch that ends without `_END` or an explicit `\b` matches the start of a longer word:
- `my life` matches "lifeguard", "lifelong" and "lifestyle";
- `without me` matches "meetings" and "mentoring".

`_RISK` keeps its `\b` and does not match these words, so tier 1 is no longer a subset of tier 2.

*Object frames.*
- `end … my life` has no clause-end guard, unlike `die{_END}` (`:64`), so a compound such as "life sciences" or "life coaching" is taken as the act.
- The new branch `better off if I (took|take|ended|end) my (own)? life` (`:80`) makes "own" optional and has no boundary, so "life savings" is taken as the act. In round 2 this was MENTION.

*No first-person subject.* `better\s+off\s+without\s+me` (`:80`) and `wish(?:ed)?\s+I\s+(?:was|were)\s+dead` (`:78`) do not start from "I". The subject of the main clause can be a team or an employer. That makes the claim "Every branch starts from 'I' (or 'me')" (`safety.py:50-51`, ADR `:155`) false, and also "an object frame never reaches it" (`safety.py:12-15,52`, ADR `:163-164`).

*A workplace continuation.* After an intent phrase, `hurt(?:ing)?\s+myself` (`:65`) has no clause-end guard. The same words after `keep`/`have been` do have one (`:76-77`), and the corpus treats the "lifting boxes" frame as MENTION.

Probes at HEAD are all ACUTE. The bracket gives the round-2 result where I checked it.

| Probe | Round 2 | Cause |
|---|---|---|
| "I am planning to end my lifeguard job this summer." | NONE | regression, `\b` |
| "I want to end my lifelong career in retail." | NONE | regression, `\b` |
| "The team would be better off without meetings on Fridays." | NONE | regression, `\b` |
| "I would be better off if I took my life savings and retrained." | MENTION | regression, new branch |
| "I am thinking about ending my life sciences career." | ACUTE | pre-existing |
| "I want to end my life coaching business and teach." | not run | pre-existing |
| "My old team is better off without me, so I want a new role." | ACUTE | pre-existing |
| "I am going to hurt myself lifting these boxes at the depot." | ACUTE | pre-existing |

The controller's ruling says that professional, third-party, figurative and object frames get tier 2 at most.

*Fix:*
1. Restore the closing `\b` on `_ACUTE`.
2. Require `life{_END}` (or a following conjunction) in `_ACT` and in the `better off if I … my life` branch.
3. Give intent + `hurt|harm myself` the same `_END` as `:76-77`.
4. For `better off without me` and `wish … I was dead` with a non-first-person subject, either require a first-person or universal subject, or have the controller keep them as deliberate exceptions and say so in the docstring, the ADR and H-12.
5. Add the career probes above as MENTION or NONE rows.

**N-I2. Tier-2 inflection gaps remain** (`safety.py:96,99-100`).
- Only the contracted negatives are covered: `doesn't`/`didn't` (`:99`) and `couldn't` (`:100`). There is no `does not`, `did not` or `could not`. This is the same contracted/uncontracted asymmetry as M-2.
- `try(?:ing)?` has no `tries` or `tried` (`:96`).
- The ADR's tier-2 list (`:172-177`) and the `_RISK` comment (`:88-89`) claim "every inflection".

Probes (career phrasing), all NONE, while the contracted equivalents are MENTION:
- "He did not want to live in London."
- "She does not want to live in Leeds."
- "I could not go on with the accounting course."

*Fix:* add `does\s+not`, `did\s+not`, `could\s+not`, `tries` and `tried`, and pin each with a workplace row.

### Minor

**M-a. H-12 known limits are incomplete.** The ruling requires that H-12 lists the known limits. These tier-2-only or tier-1 outcomes are listed neither in ADR `:184-191` nor in the checklist `:257-266`:
1. The first-person present "thinking about suicide" shape is tier 2 only, because `suicide` was removed from `_ACT`. Re-review 2 proposed `suicide{_END}`, which would have kept it in tier 1. Its gerund sibling "thinking about ending my life" is tier 1.
2. The uncontracted `I am feeling` + `suicidal` falls to tier 2 (`:70` has `{_A}m\s+feeling` but no `\s+am\s+feeling`).
3. Adverbs outside `_I`'s list, or outside `so|really|very`, fall to tier 2.
4. "I keep cutting myself" at a clause end in a workplace sentence reaches tier 1. The probe "The tape is sharp and I keep cutting myself." gives ACUTE. Re-review 2 fix item 5 asked for this overlap to be listed for H-12.
5. "I see no reason to go on" at a clause end about a course is tier 1.
6. `better off without me` with a team subject is tier 1, unless N-I1 changes it.

**M-b. A replayed receipt recorded by the round-2 code returns a 500** (`routes_interview.py:107`). Such a receipt holds `support_note`, and `TurnOut` forbids extra keys (`schemas.py:34`), so `TurnOut.model_validate` raises an unhandled `ValidationError`. Receipts do not expire (`receipts.py:54-80`). This affects only pre-release local data. Say so in the report, or clear local receipts; no compatibility path is needed.

**M-c. The CORPUS does not pin every stem and inflection.** It is one table, as ruled, but whole families have no row:
- `overdos-`;
- `harm(s|ing|ed) myself` at tier 2;
- `cut`/`cuts myself`;
- `ends`/`ended my life`;
- `end it all` at tier 2;
- `takes`/`taking my life`;
- `wish… dead` at tier 2;
- `better off dead/without me` at tier 2;
- `doesn't`/`didn't`;
- `couldn't go on`;
- `plan/tempted/try/intend/wanna/gonna … die`;
- `no reason to live`.

A row per stem × inflection (workplace wording) would have caught C-1 and N-I2.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** I-3 and I-4 are fixed, with real tests, and every "never stored" claim is now true. I-1 and I-2 are only partly fixed:
- C-1: the narrowing silently removed round-2 tier-1 shapes. The gerund of "die", the adverb slot and three intents now reach no tier at all.
- N-I1: dropping `_ACUTE`'s closing `\b` makes tier 1 block messages with no risk stem, and object and third-party frames still reach tier 1.
- N-I2: the uncontracted negatives reach no tier.

Each fix is small and table-checkable.
