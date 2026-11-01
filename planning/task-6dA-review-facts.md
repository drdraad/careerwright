# Task 6d slice A review: the facts half

Commits 86d7ead..8ad36a6 (1577db2, 8ad36a6). Read in passes: the brief's Task 6d card and
R11/R13/R14, the slice A dispatch, the implementer's report, then the diff. I read the facts
files in full: `slate_facts.py`, the `exploration.py`, `slate.py`, `sketch.py` and API schema
hunks, `vocabulary.ts`, `discoveryWords.test.ts`, `Directions.tsx`, `SketchCard.tsx` and their
tests, `tools/evaluation.py` and the changed backend tests. I compared each old Python template
with its new web template, line by line. I skimmed the target-record files only where they
cross into words.

Focused checks outside the diff, one per named risk:
- **The web may still read a removed field.** `git grep` at 86d7ead and at HEAD. The web never
  read `ConnectionOut.sentence` or `.still_uncertain`. Nothing reads `OriginOut`, so the
  reworded "… with “cook”" line is not shown anywhere yet.
- **A pack title the person types may show contradicting lines.** I read the pinned option
  pack's four target titles and searched the local ESCO v1.2.1 `occupations_en.csv` for each
  one as an exact label. Only "IT support technician" is one (an alternative label of ICT help
  desk agent). See I-1.
- **The recorded slates may be thin.** `slates_before_task_6d.json` has all 19 discovery cases:
  73 suggestions, 177 not included, 3 connections, 4 unmatched or ambiguous titles.
- **The salary floor's period cast may fail on some value.** `PayPeriod` and the profile
  floor's period have the same four values, so `PayPeriod(floor.period)` cannot raise.

No suite was re-run.

### Spec Compliance
- ❌ Issues found:
  - One new line contradicts an existing one on the same card, for three of the four roles
    Careerwright covers (I-1; the sentence rule).
  - Title ideas carry an `outcome` but no `reason` code, and three value sets inside facts
    are worded by branching, not by exhaustive maps (M-1). The dispatch's acceptance asks for
    "a fact with a reason code", and R11 asks for exhaustive maps.
- What each note reports is unchanged. I checked every template against the one it replaces:
  - release changed, one-word work style, the three found-no-work forms and their joins, too
    general (both kinds, own words, narrower), join kept best, small pool, casting wider, more
    depth;
  - nothing found, few matched, kinds of work shown, exclusions, a title not matched or matched
    to several;
  - the four "Why this could suit you" lines, might-not, entry gate, try-it, the evidence gap;
  - the floor (money format, period words, reason order) and the AI filter (when it is active);
  - the title-idea line, which filters `not_matched` only, so one-word-style ideas stay out as
    before;
  - the sketch's label, research statuses and step details.

  Order and de-duplication are kept: `_distinct` is equality on facts, where it used to be
  `dict.fromkeys` on strings, and the two give the same result on every reachable input. Only
  the two disclosed sentences changed, and both are true and plain.
- The backend composes no new sentence the person reads. What's left: error messages (never
  shown), frozen support text, the demo interviewer and explainer (model-reply equivalents),
  and the persisted source labels (M-4).
- The slate is unchanged for every evaluation case. `slate_shape` covers suggestions in order,
  pool, not included and why, unmatched and ambiguous titles, the connection and every search.
  The ranking, rules and thresholds were not touched, apart from the brief-mandated
  `concept_key` change.
- The article and plural regexes are gone from the backend and the web. No template needs
  them, `count()` pluralises counts only, and the tests of the removed helpers were removed
  with them.
- The API is free of composed prose. The facts' strings are the person's words, model search
  texts, ESCO titles and labels, or release IDs.
- ⚠️ Cannot verify from diff:
  - that `slates_before_task_6d.json` really came from 86d7ead's code (the report says it was
    generated there);
  - that `tsc` fails on a missing reason key (`Worded<U>` is a mapped type over the generated
    literal unions, which I read; `tsc` was not re-run);
  - `make check` and `make acceptance` (the implementer's runs);
  - the coverage line's words and the two reworded sentences: not run, requires human
    (session W2).

### Strengths
- One clean fact module (`slate_facts.py`). Discriminated unions use `reason` and required
  defaults, so the generated client has exact literal unions. `Worded<U>` makes each reason's
  words a type error until written, and `vocabulary.ts:611`, `:629` and `:645` cover every
  reason.
- The words moved faithfully. The web templates reproduce the Python ones character for
  character, including `_opening`'s capital letter, `_quoted`'s "and", has/have and
  "your own title(s)".
- The evaluation checks now read facts instead of regexes over sentences. That is stricter
  and more exact: `work_style_not_searched` and `general_searches_add_only` no longer pass on a
  search text quoted in another answer's note.
- `discoveryWords.test.ts` holds one test per fixed sentence, each copied from the old backend
  assertions, and its comments mark the two sentence-rule changes.
- `regulated: null` still reads as "Entry requirements aren't researched yet", never as
  regulated, and that is tested.

### Issues

#### Critical
None.

#### Important
- **I-1. A typed pack title says Careerwright can check it and that it isn't researched, on
  the same card.**
  - **Where:** `apps/web/src/components/SketchCard.tsx:91` (the new coverage line) and `:122`;
    `apps/web/src/lib/vocabulary.ts:763`, `:765` and `:792`.
  - **What:** for a target whose record has `coverage: pack_target` but which ESCO itself
    doesn't name (`resolution` `not_found` or `provisional`), the You chapter's sketch now
    shows:
    - "Registered nurse: Careerwright couldn't match it in ESCO"
    - "Careerwright can check skills, options and routes for this role."
    - "Closest in ESCO: Use …"
    - "Careerwright couldn't match this title to an occupation in ESCO, so there's no
      requirement list yet. Not researched."

    `SketchCard.test.tsx:107` renders exactly this case, and
    `backend/tests/integration/test_targets.py:164` shows the API produces it.
  - **How often:** on the full release, three of the pack's four titles (Registered nurse,
    Data quality analyst, Bookkeeping assistant) are no ESCO label, so this is the main path
    for most covered roles, not a rare edge case.
  - **Why it matters:**
    - "Not researched" and "no requirement list yet" are untrue for a pack target. The option
      pack researched it, and Skills builds its matrix through the crosswalk.
    - The new line makes the contradiction visible. The person may doubt the coverage, or
      press "Use …" for an ESCO occupation they don't need. That replaces the record with
      their choice and moves Skills' seed off the reviewed crosswalk (a question for the
      target-record half).
    - R14 keeps sentence-rule findings in the task.
  - **Fix:** word the research status from the resolution and the coverage. Under "say
    less", leave out "so there's no requirement list yet. Not researched." when the coverage
    is `pack_target`, and add a words test for that case.

#### Minor
- **M-1. Not every value the words branch on is an exhaustive map, and title ideas carry no
  reason code.**
  - **Where:** `vocabulary.ts:563-567` (`SearchDid`), `vocabulary.ts:597` (`TooGeneralBy`),
    `vocabulary.ts:745-747` (`TitleIdea.outcome`); `slate_facts.py:268-277`.
  - **What:**
    - `answerFoundNoWork` filters three `SearchDid` literals, so a fourth value would silently
      drop that search from the sentence.
    - `tooGeneral` falls through to the "skills" wording for any new `by` value.
    - `titleIdeasWords` reads only `not_matched`, so any other outcome is silently not shown.
    - `TitleIdea` has an `outcome` but no `reason`.
  - **Why it matters:** slice B adds title-idea outcomes ("found in the UK job-title index",
    "not yet found"). As built, nothing fails `tsc` if one has no words.
  - **Fix (best done first in slice B):** a `Record<SearchDid, …>` and a
    `Record<TooGeneralBy, …>`, plus a `Record<TitleIdea["outcome"], string | null>` for which
    outcomes are listed and how. Optionally give `TitleIdea` a reason.
- **M-2. A not-searched title idea reports 0 matching occupations.**
  - **Where:** `exploration.py:820-821`; `slate_facts.py:277`.
  - **What:** a one-word-style idea that was never searched has `occupations: 0`, and the
    field's description is "Occupations matching it in ESCO".
  - **Why it matters:** unknown should be null, never zero (`CLAUDE.md`). The outcome tells
    the two apart and the web doesn't show the count, so the person sees nothing wrong today.
  - **Fix:** `occupations: int | None`, null when not searched.
- **M-3. The same-slate check proves the ranking, not the notes.**
  - **Where:** `tests/integration/test_evaluation.py:92`.
  - **What:** `slate_shape` leaves out `notes`, `fewer_reasons`, `title_ideas` and each
    suggestion's `reasons`. That R11's freeze holds for the notes rests on the unit fact tests
    and on code reading; I confirmed equivalence by reading.
  - **Fix (final review):** record the old per-case notes' kinds and counts and compare them
    with the facts' reasons.
- **M-4. Some backend sentences remain and are shown as source labels.**
  - **Where:** `exploration.py:168-170` and `profile/concepts.py:37`.
  - **What:** "Chosen from Careerwright's suggestions", "A title you confirmed that
    Careerwright couldn't match in ESCO" and two more are persisted in `source_references` and
    shown in the source drawer.
  - **Why it's Minor:** they are fixed labels, not composed with values. They are outside
    "new or changed responses", and the report discloses them (ruling 9).
  - **Fix (final review):** word them from `SourceKind`.
- **M-5. Some new or moved fixed sentences have no words test.**
  - **Where:** `vocabulary.ts:706-717`, `:769-789` and `:797`.
  - **What:**
    - six new `FLOOR_UNKNOWN` words (not reachable in discovery today);
    - two `SKETCH_STEP` branches ("Your weekly hours aren't known…" and "Uses your spending
      limit.");
    - `TARGET_COVERAGE.several_pack_targets`.
  - **Fix:** add them to `discoveryWords.test.ts`.
- **M-6. Two test-text slips.**
  - `backend/tests/api/test_floor_words.py:3` points at `apps/web/src/lib/vocabulary.test.ts`,
    which doesn't exist; the words test is `discoveryWords.test.ts`.
  - `backend/tests/integration/test_discovery.py:238` replaced the floor's sentence check with
    `left_out + meets + kept_pay_unknown >= 1  # they add up`, which asserts almost nothing.
    The real add-up check is `test_floor_words.py` (== 10).
  - **Fix:** correct the path, and drop the comment or assert the sum.

Cross-half notes for the target-record reviewer (not graded here):
- `Directions.tsx:668`: while `GET .../targets` loads, `targets` is `[]`. For that moment,
  `already` (`:385`) and `full` (`:386`) are false.
- `full` counts records (one per concept), not the profile's titles.

### Assessment
**Task quality:** Needs fixes

**Reasoning:** The conversion is faithful. Every note, reason and line reports what it did
before, the slate is unchanged, and the API carries no composed prose. One small web fix is
needed first: on the main path for covered roles, the new coverage line sits beside a "Not
researched" line that is untrue for a pack target (I-1). The Minors can wait, but M-1 is best
done at the start of slice B.
