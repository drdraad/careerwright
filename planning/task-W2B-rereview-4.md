# Task W2, slice W2B: re-review of fix round 4 (392bc64..b2aa090)

Reviewer: Claude (Opus 5.5), scoped re-reviewer. Read-only on the repository: no edits, commits
or staging. The working tree is unchanged at `b2aa090`; only the untracked `answers-2.md` is
there. No subagents, no live model call, no web request, no Docker pull or new container.

## Verdict

**Not approved: 0 Critical, 1 Important, 3 Minor.**

Every "Fix now" item is done, each with a test that fails without it. The cases re-review 3
named now read true. But the nearest case it didn't name is still untrue:

- **I1.** The search reads only a skill's main name in ESCO. Where the person's words are
  ESCO's *other* name for an essential skill, the note "isn't part of any skill ESCO lists as
  essential for an occupation" is false. Example: "operating farm machinery" is ESCO's other
  name for "operate agricultural machinery", essential for 8 occupations.

It is a wording fix ("main name"), not a matching change.

## How I checked

- Read the reviewer contract, the round 4 dispatch, re-review 3's findings, the report's "Fix
  round 4" section and the whole package diff (10 files) in two passes. Outside the diff I
  read only to check named risks: `compute_slate`, `_searched`, `_one_word_style`,
  `essential_skill_reach` and its migration (which label is searched), `skill_join_hits` (the
  join's measure), the web's `Source`, and the W2D carry-forward sheet.
- `make check` on `b2aa090`: exit 0. Ruff format (323 files) and lint clean, mypy clean,
  pytest 1,548 passed and 328 deselected, the fixture validator passed, the generated client
  matches OpenAPI, Biome clean, `tsc` clean, Vitest 301 passed (34 files).
- **The notes called directly** (pure functions, a scratch script outside the repository,
  run with the backend's locked environment): `_missed_notes` and `_general_note` on the
  nearest cases below.
- **The pinned ESCO v1.2.1 CSV** (`var/datasets/`, read with Python, no database):
  - 2,561 of the 13,939 skills in the skills file are essential for no occupation (the ADR's
    figure; correct).
  - "take pictures": essential for 0, optional for 2 (correct).
  - Which essential skills have another name that no essential skill's main name holds.
  - I had no PostgreSQL stemmer. Where I say a search reaches nothing, I checked with a
    word-prefix test, which matches at least everything PostgreSQL's stems would.
- **Not run:**
  - `make acceptance` and the integration suites: a new container isn't allowed, and the
    running stack isn't mine. So the full-release tests ("taking pictures", M3's order, the
    general answers) are the report's claims.
  - Any live call.
  - Every human item: "not run — requires human".

## Each "Fix now" item

| Item | Status | Evidence | Would a test fail without it? |
|---|---|---|---|
| I1, say what was checked | **Done for the named cases; nearest case still untrue (new I1)** | `exploration.py:982` (`_ANY_ESSENTIAL_SKILL`), used in both wordings at `:985-992`; general note `:1001-1010`. ADR quotes at `0007:671-689`. "Taking pictures" is tested on the full release (`tests/integration/test_evaluation.py:189`) and in the domain (`test_slate.py:533`). | Yes. Both assert the new sentence, and the integration test asserts "names any skill" is gone. |
| I2, the join's measure | **Done, true** | `exploration.py:1022-1030`. The join ranks by the share of both roles' essential skills (Jaccard), then by the count (`slate.py:173-177`), so "the 30 with the largest share of essential skills in common" is right. With ties the note says the real number kept (`len(query.hits)`). ADR `0007:559-565`, register DIV1-02. | Yes: `test_slate.py:623` and `Directions.test.tsx:250` assert the new words. |
| M1, point a model's general search at the search | **Done for the named case; a nearer case misleads (new M1)** | `exploration.py:1012-1019`. The model wording asks nothing of the person. The own-words wording still asks "Say more about it". | Yes: `test_slate.py:533` (old code asked "Say more about “writing inspection reports for bridges”"). |
| M2, a domain test with a model's queries | **Done** | `test_slate.py:533-579`: several searches citing one answer, a search citing a task and a one-word style, "named only when none found", and both general wordings. | Yes: it calls the new signature, and the old code named "practical" as "found no work". |
| M3, a real check | **Done** | `tests/integration/test_evaluation.py:239`: both answers are now work style, so both search in the environment channel. Each scores 1.0 at weight 0.6. Only the specificity order puts the bicycle mechanic (reach 1) before the leaflet distributor (1 of 6 essential skills against 1 of 13). | Yes, by the report's run with the old `_order` patched in (RED, "leaflet distributor"). I agree from the code but didn't run it (no database). |
| M4, the web marks a too-general search | **Done; a nearer count is still off (new M2)** | `Directions.tsx:91` (the mark), `:502` and `:525` (the count, singular "1 search" correct); `vocabulary.ts:425` (`ADDED_WEIGHT_ONLY`, the same pattern as `FAILED_REPLY_LABEL`). No new colour or class. | Yes: `Directions.test.tsx:266` (old code: "2 searches", no mark). |
| The plural title in "Try it" | **Done** | `exploration.py:607-610` (`_plural`, same rule as before), `:677-682`. "Talk to people who work as warehouse operators for clothing ...". | Yes: `test_slate.py:274`. |

## The one code fix beyond tests

**Correct and in scope.** A one-word work style that a model searched beside a task now gets
the work-style note, and only the task is named as "found no work" (`exploration.py:946-975`,
`:840`).

- I called it with a search citing a task and two one-word styles ("practical", "calm") that
  found nothing. Result: one work-style note naming both styles, and one note naming only
  the task. With a search that found work, neither is named. Both are right.
- The work-style note's words are true of such a style: it wasn't searched *on its own*.
- The style note still comes before the missed notes, as before, and repeats are removed.
- It is in scope: M2 asked the test to show the style keeps its own note (ADR 0007), and the
  product didn't.
- The matching evaluation change has a gap (new M3).

## Changed tests and inputs

All are disclosed in the report, and each is still a real check:

- The five general answers' expected words (full release): the new wording, same assertion.
- M3's profile: "repairing bicycles" moved to work style. It reads oddly as a work style, but
  it makes the order half a real check, and "structured" is still shown unsearched.
- `tests/eval/test_evaluation.py`: the note strings were stale only (the check reads "found
  no work" and the quoted answer). The new style assertion is real for "not faulted", but
  weak (M3).
- `Directions.test.tsx`: `renderDirections` now also renders `EvidenceDrawer`, as
  `WorkspaceShell` does. All 301 Vitest tests pass with it.
- The domain test imports private functions (`_missed_notes`, `_general_note`,
  `_join_note`). The dispatch asked for exactly that.

## The web change

- **Plain words:** mostly. "too general to find work on its own, so it only added weight to
  what another search found". "Added weight" is the one bit of jargon (session W2 item 2).
- **No new colour:** yes. Text only, in the existing list.
- **Vocabulary pattern:** yes (`vocabulary.ts:425`). "search"/"searches" stays inline in the
  sentence that already held it.
- **Singular:** "1 search" is correct, and so is "0 searches". Only the singular is tested.

## DBOS

`application_version` is still `careerwright-l0-1` (`identity/worker.py:30`). No migration,
and `identity/` is untouched.

## New findings

### Critical

None.

### Important

**I1. "isn't part of any skill ESCO lists as essential" is false when the words are ESCO's
other name for an essential skill.**

- **Where:** `exploration.py:982` (both `_missed` wordings, `:985-992`). The same root is in
  the general note's "none of them just that" (`:1008`).
- **What:** the search reads only each skill's main name (`taxonomy_store.py:245-246`,
  `:261`; migration `r0032_essential_skill_search.py:25-26`). ESCO gives most skills other
  names as well.
  - "Operating farm machinery" (also "operate farm machinery") is ESCO's other name for
    "operate agricultural machinery", essential for 8 occupations. No skill's main name holds
    "operat", "farm" and "machin" together. So the search reaches nothing, and the slate
    says: "“Operating farm machinery” isn't part of any skill ESCO lists as essential for an
    occupation, so it found no work." I got that sentence by calling `_missed_notes`.
  - "Checking drafts" is ESCO's other name for "review drafts", essential for 2.
  - A rough count: about 3,000 "-ing" other names of essential skills (2 or 3 content words)
    are held by no essential skill's main name. My stemmer is rough, so that is an
    over-count, but the two cases above are exact.
  - The general note, probably: "monitoring equipment" is held by the main names of 10
    essential skills (about 35 occupations), so the skills rule makes it too general. The
    note then says "none of them just that", but "monitoring equipment" is ESCO's other name
    for "monitor equipment condition" (essential for 7). I worked this out from the CSV, not
    on PostgreSQL.
- **Why it matters:** this is the false reason I1 set out to remove. The person is told ESCO
  has no such essential skill when it does, under another name.
- **Fix (words only, no matching change):** say what was read. For example: "“Operating farm
  machinery” isn't part of the main name of any skill ESCO lists as essential for an
  occupation, so it found no work." For the general note, say "...is part of the main names
  of 10 different essential skills in ESCO, none of them just that...". Add a full-release
  test on "operating farm machinery", and update the ADR quote. Whether to search other names
  too is a matching question for the session W2 sheet.

### Minor

**M1. A model's too-general note says work is still needed from an answer another search
already found work for.**

- **Where:** `exploration.py:1016-1019`.
- **What:** I called `_general_note` with two model searches from "writing inspection reports
  for bridges": "write reports" (too general, 217) and "write inspection reports" (found 6).
  There is no missed note, which is right. But the general note ends "Careerwright would need
  a narrower search to find work from “writing inspection reports for bridges”." Work was
  found from it. This is the "several searches from one answer" case M2 named.
- **Fix:** add that sentence only when no other search citing the answer found work
  (`_missed_notes` already knows this), or say another search found work from it. Add the
  case to `test_slate.py:533`.

**M2. "found by N searches of ESCO" still counts a search that found nothing.**

- **Where:** `Directions.tsx:502`.
- **What:** only too-general searches are left out. A search that reached nothing still
  counts. For example, P02's "repairing physical objects" is in "from 12 occupations found by
  N searches", while the note below says it found no work.
- **Fix:** count only searches that reached something
  (`!query.too_general && query.reach > 0`), and test the plural branch too.

**M3. `missed_answers_named` can't catch the bug this round fixed.**

- **Where:** `tools/evaluation.py:394-396`.
- **What:** it now leaves one-word work styles out entirely. So a live run that names
  "practical" as "found no work" passes. That is the old behaviour. The new assertion
  (`tests/eval/test_evaluation.py:317-319`) passes with or without the style's own note.
- **Fix:** treat a one-word style named in a "found no work" note as `wrong`, and assert that
  case fails.

## Session W2 sheet items (for the product owner; not fix items)

1. **Searches read only a skill's main name.** ESCO's other names for an essential skill
   find no work: "operating farm machinery" ("operate agricultural machinery", 8
   occupations), "checking drafts" ("review drafts", 2). Searching other names would be a
   matching change.
2. **The web's words for a too-general search:** "too general to find work on its own, so it
   only added weight to what another search found". Is "added weight" plain enough? An
   alternative: "it only helped rank work another search found".
3. **M1's new wording** ("Careerwright would need a narrower search to find work from ...")
   hasn't met a real model's search. `discovery-queries-3` is still untested live.

The W2D carry-forward sheet already has re-review 3's items (`carry-forward-task-W2D.md:9`).

## Spec compliance

- ✅ Every "Fix now" item is implemented, each with a test that fails without it. All test
  changes are disclosed.
- ❌ Truth rule "no note claims something untrue": I1 (another name for an essential skill).
- ⚠️ Cannot verify here:
  - the report's `make acceptance` run;
  - the full-release tests, including "taking pictures" (reach 0) and M3's order;
  - `discovery-queries-3` on a live model;
  - every human item ("not run — requires human").

## Strengths

- Each fix is small and stays in its function. `_plural` removes the article and "Try it"
  duplication cleanly.
- The ADR's new figure (2,561 of 13,939) is exact, and the join's new words match the code's
  measure.
- The report is candid. It discloses every changed input, including M3's odd work-style
  answer, and why.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** Round 4 does everything it was asked, with real tests. But the missed note
still gives a false reason when the person's words are ESCO's other name for an essential
skill ("operating farm machinery"). It's a one-line wording fix ("main name") plus a test.
