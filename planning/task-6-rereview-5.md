# Task 6 re-review 5 (fix diff b608e7d..48c5b4d), the final fix round

This is a scoped re-review of fix round 5. I checked re-review 4's I-1, I-2 and M-1..M-6 against the controller's round-5 ruling, and looked for regressions in the 2.3k-line diff. It is not a fresh full review. I treated the report's "Fix round 5" section as unverified claims.

## Method

- **Read:**
  - the contract, re-reviews 2, 3 and 4, and the round-4 design;
  - the report's "Fix round 5" section and the whole diff, in two passes: backend source and tests, then web and docs;
  - `safety.py` at HEAD beside the round-4 matcher (`git show b608e7d:…`).
- **Ran:**
  - `cd backend && uv run --locked pytest tests/domain/test_safety.py -q` gave **138 passed**;
  - `uv run --locked pytest tests/domain/test_interview_contract.py -q` gave **43 passed**.
- **Probes** (`python -I`, scripts in the session scratchpad, nothing written to the repository).
  - Each probe is an *existing* table row changed in one form only (a punctuation mark or an apostrophe character), or a neutral word fragment, or filler words passed to a rule.
  - I wrote no distress or self-harm text.
  - The round-4 module was loaded from a scratch copy, so every probe was run against both screens.
- **Named-risk reads outside the diff:**
  - `identity/receipts.py`: whether refusals are recorded. Only successes are, `:5-6`.
  - `api/envelope.py:106-131` and `api/guard.py:128`: what answers a non-`NessaError`.
  - `api/deps.py:67-100`: the auth and idempotency-key refusals, which happen before the handler.
  - `Conversation.tsx:412,422` and `YouChapter.tsx:101-112`: what the web app can send.
  - Every web send path: the composer and the review-tray resend both call `sender.send` (`YouChapter.tsx:184`).
  - `CLAUDE.md`.
- **Not done:** Docker or integration runs (so the integration tests' claims rest on the report's `make acceptance`), Vitest, Playwright, full suites, live calls, `.env`, edits to the repository.

## Per finding

| ID | Verdict | Evidence |
|---|---|---|
| I-1 | **Fixed** | See the cross-check below. A new regression comes from the normaliser: N-I1. |
| I-2 | **Fixed** | Details below this table. |
| M-1 | **Fixed** | The "any inflection / form" claims are gone from `safety.py`, `test_safety.py:1-8`, the register (`:425`) and the Sprint 2 review. New over-claims of the same kind are in N-M4. |
| M-2 | **Fixed** | The row count is no longer cited (register `:425`, Sprint 2 review, report). The generated cross-products are gone. |
| M-3 | **Fixed** | `_CHARACTERS` (`safety.py:43-49`) is applied after NFKC (`:97`). Rows for U+02BC, U+2019, U+2011 and the en dash (`test_safety.py:141-144`) all pass. U+FF07 is covered by NFKC (probe). A residual is in N-M2. |
| M-4 | **Fixed** | Details below this table. |
| M-5 | **Fixed** | The message now names an earlier request format (`receipts.py:43-48`), and the integration test asserts it. ADR `:215-219` corrects the round-4 claim: receipts from before Task 6 replay normally. |
| M-6 | **Not fixed** (owned by the controller or user) | `CLAUDE.md:66-67` still describes "two tiers" and "the fixed support response before any model call". The implementer rightly left it alone. |

**I-1, the cross-check.**
- Every shape that re-reviews 2, 3 and 4 reported has a `CORPUS` row naming its source, and every one passes:
  - rr2: the I-1 tier-1 career phrasings, the I-2 inflections and the M-2 forms;
  - rr3: C-1 (the gerund, decided/urge, the adverb slot), the eight N-I1 probes, N-I2 (does/did/could not, tries/tried), M-a 1-6 and the M-c families;
  - rr4: every I-1 probe, the forms read from the code, and M-3.
- The design matches the ruling:
  - `words_of` normalises first (`safety.py:93-98`);
  - one listed-word rule and nine proximity rules use stated windows (`:146-248`);
  - there are no excusing word lists.
- Three behaviours checked by probe hold:
  - a negation the table has no row for ("isn't **a** reason to go on", from the `:130` row) flags;
  - line breaks and blank lines never split a window;
  - 2,000-character pathological inputs take at most 0.8 ms.

**I-2, the details.**
- The route screens before `run_idempotent` (`routes_interview.py:75`).
- Any `NessaError` from the command or the replay is answered with the envelope plus `support_note` (`:104-111`, `TurnRefusedOut` `interview_schemas.py:225`).
- Refusals are not recorded as receipts (`receipts.py:5-6`), so the panel is never stored.
- The integration test covers six refusal codes, an ordinary refusal with no panel and no extra turn (`test_interview_choices.py`, not run by me).
- On the web, `ApiError.supportNote` and `useSendMessage` (`queries.ts:338-347`) show the panel on refusal. The Vitest case covers a 402.
- Both web send paths go through `sender.send`.
- My judgement of the paths the panel cannot reach is in the next section.

**M-4, the details.**
- `check_turn` sets `question = None` when `messages[-1]` has a stem, before the one-question checks (`interview.py:358`). That is deterministic, and spends no repair.
- `test_a_turn_whose_message_has_a_risk_stem_never_keeps_a_next_question` covers both cases: the question is dropped with "?" in the reply and no problems; a stem only in an earlier message keeps the question.
- The fake model now keeps its question under the instruction (`fake_models.py`). So the integration test proves both that the instruction arrived and that the server dropped the question.

## The unscreened paths: my judgement

| Path | Reachable from the web app? | Judgement |
|---|---|---|
| No or invalid token, or invitation revoked (401/403 from the `caller` dependency, `deps.py:67-78`, before the body is parsed) | Only if a token cannot be refreshed or the invitation is withdrawn mid-session | **Acceptable, listed** ("signed out", ADR `:234`; checklist `:315`) |
| No idempotency key (`deps.py:85-100`) | No: the web always sends one | **Acceptable, listed** |
| Empty message | No: it is trimmed and must be non-empty (`Conversation.tsx:412`), and an empty message has no stem anyway | **Acceptable, listed** |
| Over 2,000 characters (schema) | No: `maxLength={2000}` (`:422`) counts UTF-16 units, which are never fewer than code points | **Acceptable, listed** |
| An old client still sending `send_after_support` | No deployed client | **Acceptable, listed** (runbook) |
| Paused / no key stored (Send disabled, `YouChapter.tsx:101-112`) | The field stays editable, but nothing is sent | **Acceptable as a product decision, listed for H-12** (ADR `:231-233`, checklist `:314`). There is no server refusal to attach a panel to, and adding one would change decision 1. Whether a paused person should still see support is for the H-12 reviewer. |
| A reply in flight | The message stays in the field and is screened when it is sent | **Acceptable** (delayed, not lost) |
| An unexpected server failure (non-`NessaError`, e.g. the database unreachable), answered 500 by `RequestGuard` (`guard.py:128`) | Yes | **A gap, not listed.** See N-M3. |

## New issues

### Critical

None.

### Important

**N-I1. A dash typed without spaces, or a hyphenated compound, now hides a listed word or construction. This is a regression from round 4** (`safety.py:46,50`, `_risk_word` `:146-152`).

*Cause.* Round 5 maps every dash (U+2012-2014, U+2212) to `-` (`:46`), and `_WORD` keeps a hyphenated run as one word (`:50`). So a dash glued between two words fuses them into one token, and that token matches no rule:
- "die—so" becomes `die-so`;
- "me—so" becomes `me-so`;
- "on—not" becomes `on-not`;
- "psychology—suicide" becomes `psychology-suicide`.

`_risk_word` tests only the start of a token, so a listed word that is not the first part of a compound is missed too: `anti-suicide`, `non-suicidal`, `drug-overdose`, `anti-self-harm`. The round-4 regex anchored each branch on `\b` and matched all of these.

*Probes* (existing rows, one change each):

| Probe | Round 4 | Round 5 |
|---|---|---|
| "Print is going to die—so I want to retrain." (`, ` → `—`) | True | **False** |
| "My old team is better off without me—so I want a new role." | True | **False** |
| "I am thinking of anti-suicide work as a career." | True | **False** |
| "I have anti-self-harm awareness training from my NHS role." | True | **False** |

*Breadth.*
- Of the 83 `FLOW` rows that the round-4 regex matched, **65 stop flagging when an em dash is glued directly after the match** (the clause-boundary position). 76 stop flagging when it is glued directly before.
- Gluing the en dash or the ASCII hyphen into any one space flips 50 of the 112 `FLOW` rows.
- A spaced dash (" — ") and a double hyphen ("--") are fine.

*Why it matters.* macOS and iOS smart punctuation turns "--" into an unspaced "—", and many writers set dashes closed up. This is a mechanical normaliser defect, not a list-or-window limit, so the H-12 reviewer, who reviews the lists and windows, would not see it. The ADR describes its cause as a feature: "every hyphen and dash variant to `-`" (`:168`).

*Fix* (small):
1. In `_CHARACTERS`, map the dashes (U+2012-2015, U+2212) to a space. Keep only the hyphens (U+2010, U+2011, and U+FE63 through NFKC) as `-`. "self–harm" with an en dash still flags, through "self" followed by "harm…" (`:152`).
2. In `_risk_word`, test each hyphen-separated part of the token. "self-esteem" is unaffected.
3. An ASCII hyphen used as a dash ("die-so"): either split hyphenated tokens for the construction rules (keeping a compound's first-part "self" out of `_reflexive`, so "hurt my self-esteem" stays `NO_FLOW`), or list it in H-12.
4. Add the probes above as rows.

### Minor

**N-M1. One round-4 shape now falls outside the intent/wish window; the windows count spelt-out words, and the docs do not say so** (`safety.py:176-179`).
- `_to_die` looks 4 words past the anchor; probe with filler words: 4 → True, 5 → False.
- Round 4's wish branch (`b608e7d:safety.py:60-61`) matched wish + `that` + pronoun + `could|would` + one adverb + die. That is 5 words past "wish", so it no longer flags. I reasoned this from the patterns and wrote no example.
- Contractions spelt out add words: "I'd" counts as 2 words. So "wish that I'd …" forms and two-word noun subjects with "that" (from the `:137-138` rows) also fall outside the window. Report R5-1 ("the wish rule takes any subject") does not say so.
- *Fix:* widen `_to_die` to 5 (or skip a leading "that") and add a row. Have ADR `:176` say that windows count words after contractions are spelt out.

**N-M2. Two small recall regressions from round 4.**
- (a) Round 4's `_A = [^\w\s]?` (`b608e7d:safety.py:35`) accepted *any* punctuation mark as the apostrophe. Round 5 accepts only the listed characters. So "I don′t want to live in London." (U+2032 PRIME in the `:141` row) gives `words_of` → `don`, `t`. Round 4 True, round 5 False.
- (b) Round 4's `_SELF` (`:37`) matched "our selves", "them selves" and "ourself"; `_reflexive` (`safety.py:136-139`) matches none of them (probe).
- Both are rare.
- *Fix:* map any remaining `[^\w\s]` between a word and `t` / `s` / `d` / `m` / `re` / `ve` / `ll` to `'`, or list them for H-12. Add `ourself` and plural "selves" after an owner.

**N-M3. An unexpected server failure carries no panel, and the docs say every outcome does** (ADR `:190-191`).
- A non-`NessaError` raised inside `run_idempotent`, such as a database or queue error, propagates past `except NessaError` (`routes_interview.py:104`). `RequestGuard` (`guard.py:128`) then answers 500 with no panel.
- ADR `:190-191` says "every outcome of `POST .../interview/turns` carries the panel". That contradicts its own `:233-235`, which says refusals before the message is read get none, and it does not mention 500s at all.
- *Fix:* say "every refusal the command raises". List the pre-read refusals and unexpected failures in one place, and add "a server failure" to the H-12 checklist line `:314-315`. A broad `except` in the route is not needed.

**N-M4. Other claims that are not exact** (ruling: "claims say exactly what is covered").
- "Every apostrophe variant … every hyphen and dash variant" is not true:
  - where it appears: ADR `:167-168`, `safety.py:8,41`;
  - what is left out: U+2032 is not mapped (N-M2), and U+2015 is not mapped to `-`;
  - why it matters: mapping dashes to `-` is the cause of N-I1. State the exact list.
- "The panel, the instruction and the dropped question are recomputed from the message wherever they are needed… so the flag reaches no … proposal" (ADR `:210-213`) is not exact. The question is dropped once, in `check_turn`, and the *stored* proposal holds `next_question: null`. No field records why, and a null question is ordinary, so no flag is stored. Say that, as the ADR already does for the model's reply.
- ADR `:244` still says "the phrase lists" (now "word lists and windows").

## Open items: load-bearing for synthetic-data local use pending H-12?

| Item | Load-bearing | Reason / ruling |
|---|---|---|
| N-I1 dash/compound glue | **No** | No real person in distress uses the app before H-12. But it is a regression in round-4 recall that the H-12 review would not see. Recommend the small fix (steps 1, 2 and 4 are about 5 lines). Otherwise, park it with a ruling that lists it explicitly in decision 7 and the H-12 checklist, and correct ADR `:168`. |
| N-M1 window | No | Park: it is a window-size policy question for H-12. Add one sentence that windows count spelt-out words. |
| N-M2 apostrophe / reflexive residue | No | Park: rare characters and spellings; list them for H-12. |
| N-M3 500 without panel | No | Park: list it in H-12 and fix the "every outcome" wording. |
| N-M4 claim wording | No | Docs-only correction; should be made before the H-12 review relies on them. |
| M-6 `CLAUDE.md:66-67` | No | Controller or user to edit. |

## Assessment

**Task quality:** Needs fixes

**Reasoning:** I-1, I-2 and M-1..M-5 are fixed with real tests:
- every reported shape is a passing row;
- the panel reaches every refusal the command raises;
- the next question is dropped deterministically;
- nothing new is stored.

One Important regression remains (N-I1). The normaliser turns an unspaced dash or a hyphenated compound into one token, which hides listed words and constructions that round 4 caught. It is small to fix. Nothing open is load-bearing for synthetic-data local use, so the controller may park N-I1 and the Minors with a ruling, provided each is listed in decision 7 and the H-12 checklist.
