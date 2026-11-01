# Task 6b — fix round 1 (FIX_BASE a751c7b)

Review 1 verdict: Spec ❌, Needs fixes. The core design holds (one sealed run per slate,
receipt leak fixed, exact spans, typed failures, provenance always shown). Fix all items
below. Name the covering tests, the command and the output in your fix report.

## Important

I1. Answer words exempt readiness, pay and hiring claims
(`backend/src/nessa/profile/slate_explanation.py:358`, `:365`). The allow-list for the
readiness, affordability and hiring words includes every pinned answer: with the answer
"qualified first aider" the checker accepted "You are already qualified to start work as a
bicycle mechanic"; "ready for a change" or "paid carer" unlock "ready" / "paid".
Fix: a screened word is allowed only when that occupation's ESCO record uses it, never
because an answer does. Regression tests for the "qualified", "ready" and "paid" cases.

I2. Function words count as quotations (`slate_explanation.py:49`, `:331`, `:262`).
Quotes `and` (answer) + `and` (ESCO) let "Employers are crying out for people like you in
this trade." pass; trimming apostrophes lets "s work" pass as a whole-word span of
"ESCO's work".
Fix (controller ruling):
- every quotation must contain at least one content word (four or more letters, not a
  stopword; reuse the existing `_WORD` / `_COMMON` idea from `fixture_explainer.py` in one
  place rather than duplicating it);
- do not trim a leading apostrophe;
- the claim-shares-a-content-word check is NOT required (it would turn paraphrase into
  paid repairs); instead the UI and API wording must say exactly what was checked: the
  quoted words were checked against the person's answers and the ESCO record, and the
  sentence around them is the model's own. Replace "Each quotation was checked word for
  word" wherever it implies the claim itself was checked. Keep the ADR 0007 decision 12
  known limit, worded to match.
Tests for "and"/"and", "s work", and a valid content-word quotation still passing.

I3. A failed note can never be recovered, and the person is not told
(`apps/web/src/components/Directions.tsx:145`, `:511`; `profile/exploration.py:567`; ADR
0007:314-317). Controller ruling:
- A failed explanation run whose attempts sent zero provider requests (refused inside the
  activity: `budget_exceeded`, `credential_unavailable`, `model_not_permitted`, or any
  other failure before a request) does not use up the slate's note: an explicit "Try again"
  action (never automatic) may start a new run that replaces that failed link, in the same
  locked transaction, still at most one live run per slate and still idempotent. Decide
  from the recorded attempts (request count), not from the failure class alone.
- A failed run that sent a request (provider failure, `invalid_model_output`,
  `output_truncated`) stays the slate's one note (one call per slate). The unavailable
  note then says what the person can do and offers "Suggest again" on the current
  discovery, saying that it makes a new set of suggestions.
- The words come from `vocabulary.ts` per error code; never the API message.
- Correct ADR 0007 decision 12 and the Sprint 2 addendum to describe exactly this.
Tests: server-side (zero-request failure → retry allowed and replaces; request-sent
failure → retry refused with a typed error; concurrent retries → one run), and web (each
unavailable state shows its action). Update the Storybook states and recapture the
unavailable note at the three viewports.

## Minor (upgraded to fix now: honesty, cost and typed-failure rules)

M1. Word lists miss common phrasings (`slate_explanation.py:175-238`): "in high demand",
"strong candidate", "already have the experience", "lucrative", "plenty of jobs", "crying
out for" all passed. Add them, or match "in … demand" with a small gap. Tests for each.

M2. The repair message can outgrow its budget (`slate_explanation.py:414-420`, `:60`):
every claim past `MAX_CLAIMS` and quotation past `MAX_QUOTES` is still checked, so the
repair message grows with the output; nothing enforces `REPAIR_ALLOWANCE_TOKENS`. Stop
checking past the count bounds (report "too many") or cap the listed problems so the
repair prompt provably fits its reservation. Test the bound.

M3. The prompt-size proof holds only for ASCII (`slate_explanation.py:520-521`): 36 answers
of 120 multi-byte characters can pass 8,500 bytes and raise a bare `ValueError` (a 500).
Bound in bytes or turn it into a typed `NessaError` refusal before any reservation; test
with multi-byte answers.

M4. "One sentence" is not checked (`slate_explanation.py:359-360`). Either check it or make
the problem text and API description say only what is checked.

## Also
- Re-run `make check`; run `make acceptance` once at the end (the API and UI change).
  `cd apps/web && pnpm run generate` and commit the client if the API changes.
- No live calls this round.
- Revise the proposed CLAUDE.md wording in your report if these fixes change it.
- Edit/Write tools only for source changes; no sed, awk, perl, heredocs or redirection.
- Append the fix report to task-6b-report.md and reply with the short contract.
