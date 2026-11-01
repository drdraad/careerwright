# Task 6b — fix round 3 (FIX_BASE 748dd6d)

Re-review 2: R2-I1 and R2-M1..M5 all ADDRESSED; every round-1 bypass refused. One new
Important regression and small items. Fix all below; name covering tests, command, output.

## Important

R3-I1. The demo fixture explainer now writes quotations the checker refuses
(`fixture_explainer.py:46-48`, `:51`, with `slate_explanation.py:373-379`).
`content_words` splits at the apostrophe, so "children's" yields "children"; the fixture
quotes "children" and `find_span` (which now keeps "children's" whole) refuses it. The
fixture is deterministic, its repair repeats, the run ends `invalid_model_output`, and the
demo slate's whole note is unavailable. Reproduced: answer "looking after children",
description "Nursery workers supervise children's play and meals.", skill "plan
activities"; and answer "helping students learn" with "…monitor the students' learning
progress.". Fix: in `_link`, take a description word only when `find_span(word,
description)` verifies (both the shared-word path and the last fallback); otherwise quote
the whole token, possessive included. Add a property-style test: for a set of
answer/record pairs including "children's" and "students'", the fixture's output always
passes `check_explanation`.

## Minor (fix now: each costs a paid repair or is an honesty wording)

R3-M1. `slate_explanation.py:255`: "paying" screens "paying attention to detail" (a common
self-description and the ESCO skill "pay attention to detail"). Exclude pay/paying before
"attention". Test.

R3-M2. `:373-379`: a closing single quotation mark after a word is read as a possessive,
so with the answer "I am a 'people person' at heart" (straight or curly) neither "people
person" nor "'people person'" verifies. Treat an apostrophe as part of a word when a
letter follows it, or when it follows an "s" (plural possessive); otherwise as a closing
mark. Tests for both quote styles, plus "students' learning" and "mechanic's tools" still
behaving as now.

R3-M3. `:331`: `_unwrapped` misses a double quote before closing punctuation:
`"mending bikes".` unwraps to `mending bikes"`. Strip until nothing changes (or rstrip the
edge set plus closing marks). Test.

R3-M4. `:294`: "employers want/need" refuses natural claims for careers and recruitment
occupations ("…explains what employers need" for a careers adviser). Keep the rule; list
it as a known false positive in ADR 0007 decision 12's known limits for the H-12 review.

R3-M5. Sprint 2 addendum: the round-1 paragraph says the stored live EXP-01 output "also
pass[es] the final rules", not rechecked after round 2's stopword and apostrophe rules.
Re-check it offline against the final checker if the stored output is available locally
without a live call (and without printing private text); otherwise reword the sentence to
say which rules it was checked against. No live call.

R3-M6. The per-card line for a refusal made before any run reads "Failed: no written note
… Nothing from it was kept". No run existed; word it as a refusal before any run (words in
`vocabulary.ts`). Web test.

## Also
- `make check`; `make acceptance` once at the end. Recapture only states whose pixels
  change. No live calls.
- Edit/Write tools only for source changes; no sed, awk, perl, heredocs or redirection.
- Append the fix report to task-6b-report.md and reply with the short contract.
