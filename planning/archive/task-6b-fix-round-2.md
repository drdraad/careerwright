# Task 6b — fix round 2 (FIX_BASE d16ffe3)

Re-review 1: I1, I3, M1–M4 ADDRESSED. I2 NOT ADDRESSED in part. Fix the items below; name
the covering tests, the command and the output in your fix report.

## Important

R2-I1 (I2 residual). `slate_explanation.py:71-77`: `COMMON_WORDS` misses common 4+-letter
function words and contraction stems, so "Employers are short of staff in this trade right
now." passed quoting "about" (answer) and "about" (ESCO); also "being"/"being",
"could"/"should". Fix:
- extend `COMMON_WORDS` with the 4+-letter entries of a standard English stopword list and
  the contraction stems (about, above, after, again, against, because, before, being,
  below, between, could, does, doing, during, every, further, having, once, should,
  through, under, until, upon, were, whom, whose, within, without, aren, couldn, doesn,
  hadn, hasn, haven, shouldn, wasn, weren, wouldn, and the others of that list);
- run the content-word check on the verified source span (the source's own characters,
  folded as the matcher folds them), not on the model's raw text, so fullwidth or other
  compatibility forms cannot count as content ("ｗｉｔｈ" folds to "with");
- parametrised test: "about"/"about", "being"/"being", "could"/"should", fullwidth "with".

## Minor (fix now)

R2-M1. `slate_explanation.py:357`: "s" fragments still verify. `find_span` treats an
apostrophe after a letter as a word boundary, so "s tools" (from "mechanic's tools") and
"s work is to maintain" verify. Count an apostrophe preceded by a letter as part of the
word in the boundary test. Tests.

R2-M2. `slate_explanation.py:306`: quotations wrapped in single quotes ('mending bikes',
‘mending bikes’) are now refused as not exact, costing a paid repair. Strip a leading ' or
‘ only when the text also ends with the matching closing mark. Tests for both forms and
for a leading apostrophe that is part of the word.

R2-M3. `slate_explanation.py:271`, `:211-243`: "an in-demand trade", "high-demand",
"well-paying", "highly sought after", "Employers want people…" pass. Treat `-` as a
separator in the demand pattern; add "paying", "sought after", and an "employers want /
employers need / employers are looking" construction. Tests for each.

R2-M4. `Directions.tsx:137-147`: refusals that will always repeat (`no_quotable_answer`,
`answers_too_long`, `PROPOSAL_NOT_AVAILABLE`) offer a Try again that cannot succeed, with
generic words. Give each its own reason words in `vocabulary.ts` (for example: the answers
are too short to quote; edit your answers, then Suggest again) and the action that can
work (edit answers / Suggest again), never Try again. Web tests per state; update the
Storybook story and recapture that state at the three viewports.

R2-M5. `docs/requirements-register.md:119`: REC1-11 still says "a unique key"; it is now a
partial unique index on the current link. Also correct the `reached_no_model` docstring
(an unfinished fixture attempt counts as no call; only live attempts are held before a
call).

## Also
- `make check`; `make acceptance` once at the end (UI changes). Regenerate the client only
  if the API changes. No live calls.
- Edit/Write tools only for source changes; no sed, awk, perl, heredocs or redirection.
- Append the fix report to task-6b-report.md and reply with the short contract.
