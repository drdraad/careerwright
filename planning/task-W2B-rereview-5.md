# Task W2, slice W2B: re-review of fix round 5 (b2aa090..166e4ef)

Reviewer: Claude (Opus 5.5), scoped re-reviewer. Read-only on the repository: no edits,
commits or staging. The tree is unchanged at `166e4ef` (only the untracked `answers-2.md`).
No subagents, no live model call, no web request, no Docker pull or new container, and I
didn't connect to the running stack.

## Verdict

**Not approved: 0 Critical, 1 Important, 2 Minor.**

All four "Fix now" items are done, each with a test that fails without it. The notes the
ruling named now say what the search did, and each is true in the nearest cases (another
name of a skill, a skill essential for nothing, common words only, a model's search naming
the person's own title).

One line the ruling covers is still untrue, and the report kept it on purpose:

- **I1.** A title idea's "Why this could suit you" line says "Careerwright thought of this
  title from it, and ESCO lists it." It isn't true when the idea matched another name of the
  occupation. That happens often: a model's "dog groomer" becomes the card "animal groomer".

The fix is words only, plus one domain test.

## How I checked

- Read the reviewer contract, the round 5 dispatch, re-review 4's findings, the report's
  "Fix round 5" section and the whole package diff (9 files) in three passes. Outside the
  diff I read only to check named risks: `_searched`, `search_essential_skills` and
  `essential_skill_reach` (what a search reads), `concept_key` (`r0008`) and
  `concept_key_matches` (how titles and title ideas match), `titles.py`, the sketch's
  `_target`, the web's count and lines, and `DiscoveryQuery` validation.
- `make check` on `166e4ef`: exit 0. Ruff format (323 files) and lint clean, mypy clean,
  pytest 1,550 passed and 329 deselected, the fixture validator passed, the generated client
  matches OpenAPI, Biome clean, `tsc` clean, Vitest 303 passed (34 files). The tree was
  unchanged afterwards.
- **The note functions, called directly** (a scratch script outside the repository, run in
  the backend's locked environment): `_missed_notes`, `_general_note` and `explain` on the
  nearest cases below.
- **The pinned ESCO v1.2.1 CSV** (`var/datasets/`, read with Python, no database): how
  titles and title ideas fold onto labels (a Python copy of `concept_key`), and hyphenated
  forms in the main names of essential skills.
- **Not run:**
  - `make acceptance` and the integration suites: a new container isn't allowed, and the
    running stack isn't mine. The full-release tests ("operating farm machinery" and the
    others) are the report's claims.
  - Any PostgreSQL text-search call. I had no database, so M1 rests on PostgreSQL's
    documented handling of hyphenated words.
  - Any live call.
  - Every human item: "not run — requires human".

## The ruling: every note and web line in this slice

| Line | Where | Says what was done? | True in every case? |
|---|---|---|---|
| Missed, own words: "No main name of a skill ESCO lists as essential holds all the words of “…”, so it found no work." | `exploration.py:1001`, `:1009-1011` | Yes | Yes for "operating farm machinery" (I got that sentence) and "taking pictures". The search reads only main names, all words, stems, and only skills essential for some occupation (`taxonomy_store.py:242-298`). If nothing is reached, no such name holds the literal words either. One exception, likely but not checked: a hyphenated word (M1). |
| Missed, a model's searches: "“X” found no work: no main name … its search “…”" | `:1017-1029` | Yes | Yes |
| Common words only: "… has only common words, which Careerwright doesn't search for" | `:1002`, `:1012`, `:1021-1023` | Yes | Yes for any text with a word. A model search made only of punctuation ("...") passes the 3 to 80 character check (`discovery.py:39`, `:177`) and would be called "common words". Unrealistic, so not a finding. |
| A model's search naming the person's own title: "Careerwright found no other occupation in ESCO that shares 3 or more essential skills with its search “…”, your own title" | `:1025-1029`, `joins` at `:785`, `:805` | Yes | Yes. The join's total counts neighbours sharing 3 or more (`slate.py:234-236`). The quoted text is the person's title (`_joined` passes `title.text`), which suits "your own title". |
| Too general, occupations: "reached 217 occupations in ESCO through the main names of their essential skills" | `:1039-1042` | Yes | Yes (`total` is every occupation reached) |
| Too general, skills: "matched the main names of 10 different essential skills in ESCO, none of them just those words" | `:1043-1047` | Yes | Yes (`spread.skills` counts different essential skills; `exact` compares stems) |
| A model's search too general: "Careerwright would need a narrower search …" only for answers no other search found work from | `:1054-1061` | Yes | Yes. With two answers, it names only the one still waiting. |
| Join keeps: "Careerwright found 47 other occupations in ESCO that share …" | `:1064-1073` | Yes | Yes |
| First slate, empty join | `:1409` | Yes | Yes |
| A title it couldn't match, or matched to several | `_unmatched` `:910`, `_ambiguous` `:917` | Yes | Yes. The match folds case, punctuation and plurals. |
| Why, the person's own title: "Careerwright matched it to this occupation in ESCO." | `:654` | Yes | Yes (a chosen occupation is the person's pick from ESCO's titles) |
| **Why, a title idea: "Careerwright thought of this title from it, and ESCO lists it."** | `:648-650` | **No** | **No: I1** |
| Why, a search: "Careerwright searched for “q”, and ESCO lists “skill” as an essential skill for this work." | `:640-645` | Reads the hit's own relation | Yes |
| Why, a join: "ESCO lists N of the same essential skills for both …" | `:634-638` | Reads the pair's relations | Yes |
| Might not suit, connection, release, work style, small pool | `:658-667` (`ESCO lists N essential skills`, the regulated flag), `:261`, `:742`, `_work_style_note`, `_small_pool_note` | Records or the slate | Yes |
| Web: "found by N searches of ESCO" | `Directions.tsx:503`, `:526` | Yes | Yes |
| Web: "Titles Careerwright thought of but couldn't match to an occupation in ESCO …" | `Directions.tsx:614` | Yes | Yes |
| Web: the too-general mark, loading lines, "Up to six occupations from ESCO …" | `Directions.tsx:91`, `:495`, `:655`, `:676` | About the search | Yes |

## Each "Fix now" item

| Item | Status | Evidence | Would a test fail without it? |
|---|---|---|---|
| I1, say what the search did; a full-release test; ADR quotes | **Done** | `exploration.py:1001-1029`. Test on the full release: `tests/integration/test_evaluation.py:209`. It checks the case (the other name is essential for 8 occupations) and checks, separately from the search, that no essential skill's main name has words starting "oper", "farm" and "machin". ADR quotes: `0007:684-` and `:564`, `:645-649`. | Yes. The domain test (`test_slate.py:536`) asserts the new words; the old code fails on its signature and words (RED in the report). |
| M1, a narrower search only where no other search found work | **Done** | `exploration.py:1054-1061` | Yes: `test_slate.py:584-590` (the old code always added the sentence, and takes 2 arguments) |
| M2, count only searches that reached work | **Done** | `Directions.tsx:503` | Yes: `Directions.test.tsx:321`, singular and plural. The old count gives "2" and "3". |
| M3, a one-word style named "found no work" is wrong | **Done** | `tools/evaluation.py:391-393`, `:407` | Yes: `tests/eval/test_evaluation.py:320-327`. The old check returned `[]`. |

## The two extra cases

Both are **correct and in scope**. The old sentence ("isn't part of any skill ESCO lists as
essential") was untrue of each, because in neither case did anything read a skill's name.
The ruling covers the missed note in every case.

- **Common words only:** an unsearchable query now goes to `common` (`:981-983`) with its
  own clause.
- **A model's search naming the person's own title:** the query now goes to `joined`
  through `joins`, with the join's clause.
- Both are tested in the domain (`test_slate.py:600`), including all three clauses in one
  sentence. Neither has a full-release test, which is fine for wording.

## The out-of-slice lines (for the controller)

Most of these share one cause. The title match (`concept_key`, `r0008:38-50`) keeps "and"
but drops "&", and keeps accents. So a title ESCO writes as "ballet & modern dance
performer" or "façade cleaner" doesn't match "ballet and modern dance performer" or "facade
cleaner". In v1.2.1 there are 46 such "&" labels and 8 such accented ones.

| Line | Verdict | The case |
|---|---|---|
| Sketch "Your own title, not in ESCO" (`vocabulary.ts:439`) | **False** | The person confirms "facade cleaner" as their own title. The provisional trigger accepts it (the keys differ). But ESCO lists "façade cleaner" as another name for building exterior cleaner. Same for "ballet and modern dance performer" (ESCO: "ballet & modern dance performer", dancer). |
| Confirmed-title label "A title you confirmed that ESCO does not list" (`profile/concepts.py:34`) | **False** | Same case. |
| Sketch "Several ESCO occupations have this title" (`vocabulary.ts:438`, `sketch.py:142`) | **False, narrow case** | "physician" is only a hidden label (a search term ESCO doesn't show) of "general practitioner" and "specialised doctor". The code itself says hidden labels exist "for search, not display" (`taxonomy_store.py:351`). Ten titles are ambiguous only through a hidden label, such as "youth worker" and "neurologist". Otherwise true. |
| OpenAPI "Titles Careerwright thought of that ESCO does not list" (`discovery_schemas.py:511`) | **False (developer docs only)** | A model's idea "facade cleaner". The report didn't list `:515` ("Titles of the person's own that ESCO does not list"), which is false in the same case. Both are mirrored in the generated client. |
| Type-ahead "ESCO doesn't list that title. Is it one of these?" (`taxonomy.py:181`, ADR `0007:541`, the OpenAPI `partial` description) | **False, not shown** | Typed "ballet and modern dance performer": no title has a word starting "and", so `partial` is set. Nothing renders it today. The field's own claim, "ESCO lists no title with every word typed", is true. |
| Also seen: sketch "No ESCO record, so no requirement list yet." (`sketch.py:165`) | **False** | Same case as the first row. "Not found in ESCO" (`vocabulary.ts:440`) is about the search, so it's true. |

The fix for all of them is the slate's pattern: say what the match did ("Careerwright
couldn't match …").

## Changed tests and inputs

All are disclosed, and each is still a real check:

- `test_slate.py`: the new expected words, the new arguments and the M1 case. The join
  note's words. Two new tests.
- `tests/eval/test_evaluation.py`: synthetic note strings (the checks read only "found no
  work", the quoted text and `ambiguous_titles`), plus the new M3 assertion.
- `tests/integration/test_evaluation.py`: the general answers' parameter is renamed with the
  same assertion. The "taking pictures" sentence is updated. Its old `not any("names any
  skill" …)` line now checks wording two rounds old, but the exact sentence above it covers
  the change. There's one new test.
- `Directions.test.tsx`: the join note string, and the new M2 cases.

## Plain words

Short enough, and readable. Wording taste is for session W2 (sheet items 2 and 3).

## DBOS

`application_version` is still `careerwright-l0-1` (`identity/worker.py:30`). No migration.
Nothing in `identity/` changed.

## New findings

### Critical

None.

### Important

**I1. A title idea's why line is untrue when the idea matched another name of the
occupation.**

- **Where:** `exploration.py:646-650`. The report's "Checked and kept" list keeps it ("'it'
  is the card's title").
- **What:** a title idea finds occupations through `concept_key_matches` (`:529-532`). That
  matches preferred, alternative and hidden labels. So the card often shows a different title
  from the one Careerwright thought of. In v1.2.1:
  - "dog groomer" → animal groomer
  - "software engineer" → software developer
  - "delivery driver" → cargo vehicle driver
  - "plumber" → pipe welder (as well as plumber)
  - "receptionist" → telephone switchboard operator
  - "physician" → general practitioner, through a hidden label only

  I called `explain` for the "animal groomer" card with the idea "dog groomer". It says:
  "What you enjoy: “caring for dogs”. Careerwright thought of this title from it, and ESCO
  lists it."
  - If "this title" means the card's title, as the report says, the first half is false:
    Careerwright thought of "dog groomer".
  - If "it" means the idea, "ESCO lists it" is the claim about ESCO that this round removed
    from the person's own title line, which goes through the same match. For a
    hidden-label match it's false.
- **Why it matters:** the ruling binds every reason on the slate. This is the "another name"
  case again, and it happens often, not only at the edges. What it gets right: the
  occupation really was reached through ESCO's own other name, and the idea is shown one step
  away under "Found by these searches". The line dates from Task 6, so it isn't a
  regression. Nothing tests it.
- **Fix (words only):** name the idea and say what the match did. For example: "What you
  enjoy: “caring for dogs”. Careerwright thought of the title “dog groomer” from it and
  matched it to this occupation in ESCO." (`match.query.text`). Add a domain test with an idea
  matched through another label.

### Minor

**M1. A hyphenated answer may get an untrue missed note (likely, not verified).**

- **Where:** `exploration.py:1009-1011`; the search at `taxonomy_store.py:256-262`.
- **What:** PostgreSQL reads "first-aid" as the whole word "first-aid" as well as "first"
  and "aid". So `plainto_tsquery` needs a main name containing "first-aid". No essential
  skill's main name has the hyphen. But "provide first aid" (essential for 35 occupations)
  and "first aid" (28) hold both words. With reach 0, the note would say "No main name of a
  skill ESCO lists as essential holds all the words of “first-aid”, so it found no work." I
  got that sentence by calling `_missed_notes` with reach 0. A reader would call it false.
  - I couldn't run the search, so reach 0 comes from PostgreSQL's documented parser.
  - "problem-solving" and "decision-making" are safe: a main name has each with the hyphen.
- **Fix:** first check with one query on the test stack (`SELECT plainto_tsquery('english',
  'first-aid')`). If it's confirmed, the clean fix is to read hyphens as spaces before the
  search. That is a matching change, so it's for session W2 (sheet item 3).

**M2. Four lines reworded this round have no test that reads their words.**

- **Where:** `_unmatched` (`:910`), `_ambiguous` (`:917`), the first slate's empty join
  (`:1409`), and the web's title-ideas line (`Directions.tsx:614`).
- **What:** nothing asserts their words, before or after this round. The ambiguous reason in
  `tests/eval/test_evaluation.py:377` is a synthetic input. So a return to the old wording,
  which claimed something about ESCO, would pass.
- **Fix:** one assertion each, in `test_slate.py` and `Directions.test.tsx`.

## Session W2 sheet items (for the product owner; not fix items)

1. **The own-words too-general note asks "Say more about it" even when another search from
   the same answer found work.** That happens when a model writes the answer word for word
   and also a narrower search. I got: "“Training staff” matched the main names of 10
   different essential skills … Say more about it, …" beside a search that found 4. It isn't
   false, but is it needed?
2. **"Main name"** is new to the person. Is it plain enough? The alternative is "the name
   ESCO gives a skill".
3. **"holds all the words of any of its searches “A” and “B”"** reads awkwardly. An
   alternative: "either of its searches".
4. **Hyphenated words** (if M1 is confirmed): search a hyphenated word as its parts?
5. **Carried from re-review 4:** searches read only main names, and the web's "added
   weight". `discovery-queries-3` hasn't met a live model, so the model wordings are
   untested live.

## Spec compliance

- ✅ Every "Fix now" item is implemented, with a test that fails without it. Every changed
  test is disclosed.
- ❌ The ruling ("binds every note and label in this slice"): I1.
- ⚠️ Cannot verify here: the report's `make acceptance` run, the full-release tests, M1 on
  PostgreSQL, and every human item ("not run — requires human").

## Strengths

- Splitting each answer's searches by what they did (`_Searched`) makes each clause true by
  construction. It also caught two cases the old sentence got wrong.
- The full-release test checks the note's claim on its own, without trusting the search.
- The report lists every line it checked, which made this review quick to do.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** Round 5 does everything it was asked, with real tests, and the notes it
rewrote are true. But one reason line the ruling covers still names the wrong title whenever
a title idea matched another name of the occupation, which is common. It's a words-only fix
plus one test.
