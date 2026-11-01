# Task W2, slice W2B: re-review of fix round 3 (267a83f..392bc64)

Reviewer: Claude (Opus 5.5), scoped re-reviewer. Read-only on the repository: no edits, commits
or staging. The working tree is unchanged at `392bc64`; only the untracked `answers-2.md` is
there. No subagents, no live model call, no web request, no Docker pull or new container.

## Verdict

**Not approved: 0 Critical, 2 Important, 4 Minor.**

Every ruling and every "Fix now" item is done as ruled. The two extra fixes are correct and in
scope. Two of the new notes still say something untrue in cases that really happen:

- **I1.** "isn't how ESCO names any skill" is false when ESCO names exactly that skill but
  lists it as essential for no occupation (for example "taking pictures").
- **I2.** "Careerwright keeps the 30 that share the most" is false on P03's slate. 39 of the
  occupations it leaves out share more essential skills with the role than one it keeps.

Each is a wording fix of a line or two. Neither reopens matching.

## How I checked

- Read the reviewer contract, the round 3 dispatch, re-review 2, the report's "Fix round 3"
  section and the whole package diff (23 files) in ten passes. Outside the diff, I read only
  to check named risks: `first_slate`, `explain`, `choose_slate`, `skill_neighbours`, the
  web's `Source` and `Slate`, the fixture proposer's channels, and the W2D carry-forward
  sheet.
- `make check` on `392bc64`: exit 0. Ruff format (323 files) and lint clean, mypy clean,
  pytest 1,546 passed and 327 deselected, the fixture validator passed, the generated client
  matches OpenAPI, Biome clean, `tsc` clean, Vitest 300 passed.
- **Each fix undone in-process** (a scratch pytest plugin outside the repo that monkeypatches
  the old code; the domain tests only):
  - old `_order` without `reach`: `test_work_a_specific_answer_found_comes_before_work_a_general_one_found` fails;
  - old join cut at exactly 30: `test_a_join_never_cuts_inside_a_tie` fails;
  - a general match's own score counting as best: `test_a_search_too_general_to_find_work_alone_only_adds_weight_to_work_another_found` fails;
  - old `with_article`: `test_an_occupation_gets_the_article_its_sound_needs` fails;
  - old `beyond_limit`: two pool-count tests fail.
- **The new notes called directly** (pure functions, scratch script): `_missed_notes`,
  `_general_note`, `_join_note` and `_work_style_note` with the demo's queries and a model's.
  Also `with_article` over all 3,043 preferred labels in the pinned ESCO CSV.
- **The pinned ESCO v1.2.1 CSV** (`var/datasets/`, read with Python, no database). Used to
  check which skills are essential to no occupation, which answers no skill label holds, and
  the join's cut by share against its cut by count. My join reach figures match the report:
  data analyst 47 joined and 30 kept, warehouse manager 117 and 47, ICT help desk agent 109
  and 30. I had no PostgreSQL stemmer, so the full-text figures (217, 77, 13, 29 and so on)
  are the report's. I did not recompute them.
- **Not run:**
  - `make acceptance` and the integration suites: a new container isn't allowed, and the
    running stack isn't mine. So the full-release tests, the DSC cases and the report's
    before and after slates are its claims, which I didn't repeat.
  - Any live call.
  - Every human item: "not run — requires human".

## Each ruling and "Fix now" item

| Item | Status | Evidence | Would a test fail without it? |
|---|---|---|---|
| N-I1, honest emptiness | **Done as ruled; wording defect (I1)** | `exploration.py:942-973`: the answer is named only when every query citing it, unsearchable ones included, reached nothing. Titles are left out (`:925`), and so is a one-word style (it never reaches `queries`). The note is on full and short slates (`:836`). `missed_answers_named` is on DSC-01, DSC-03, DSC-07 and DSC-18 (`tools/evaluation.py:386`; `evaluation_cases.json:388`, `:425`, `:469`, `:627`). | **Yes for the demo path.** The report ran the old `src` with the new cases, and DSC-01, DSC-03 and DSC-18 failed; I didn't repeat that. **No for the live-path clause** ("every query citing it", and the model wording). The fixture proposer makes one query per answer, and no product test calls `_missed_notes` with a model's queries (M2). I checked both by calling them: right. |
| N-I2, generic answers | **Done as ruled** | `too_general` with the named constants (`slate.py:78`, `:82`, `:195`). `exact` and the skill spread are in SQL (`taxonomy_store.py:260`, `:272`). The search finds nothing alone (`slate.py:459`, `exploration.py:823-824`). The note (`exploration.py:976-991`) and the thresholds are recorded in ADR 0007 decision 13, rule 4, as provisional. "Plan shifts" became "stack goods" in the prompt (`discovery.py:34`, `:247`), and each test input change is disclosed. | Yes. Undone, the domain test fails. The full-release parametrized test covers the five answers (`tests/integration/test_evaluation.py:173`; not run by me). |
| N-I3, rule 2 narrowed | **Done as ruled** | `_one_word_style` (`exploration.py:546`, used at `:769` and `:807`). The note no longer says the answer isn't about the work (`:914`). DIV1-10 and REC1-03 rows updated (`docs/requirements-register.md:134`, `:111`). | Yes. The eval unit test (`tests/eval/test_evaluation.py:255`) has the longer answer passing and the one-word one failing. The full-release test is at `tests/integration/test_evaluation.py:209`. |
| N-M4, order by specificity | **Done as ruled** | `Candidate.reach` and `_reach` (`slate.py:357`), first in `_order` after relevance (`:385-391`). A general search never counts. | Yes: the domain test (`test_slate.py:383`) fails under the old order. The full-release test's "bicycle mechanic first" half passes either way (M3). |
| N-M1, no cut inside a tie | **Done** | The join's loop is at `slate.py:179`. The search uses `FETCH FIRST (:limit) ROWS WITH TIES` on rank and share, and the title orders only what is kept (`taxonomy_store.py:277`). | Yes: `test_skill_joins.py:113` (I undid it and it failed). The full-release `test_a_search_never_cuts_inside_a_tie` (`tests/integration/test_evaluation.py:120`) has a reported RED; not run by me. |
| N-M2, counts | **Done** | `skill_join` keeps `total` and `unkept` (`slate.py:223`). `build_pool` counts once what a finding search or join reached and the pool doesn't keep (`:489-490`). The join note is at `exploration.py:994`. The web says "N more were found but not kept" (`Directions.tsx:521`). "Exact, not at least" holds: a finding search reaches 50 or fewer, under the 120 cut, and that is pinned by `assert TOO_GENERAL_OCCUPATIONS < POOL_LIMIT`. | Yes: `test_slate.py:490` and `test_skill_joins.py:128`; both failed with the old count. The join note's words are wrong (I2). |
| N-M3 | **Done** | DSC-07 and DSC-08 search "caring for animals", so `pool_includes_pool_of` compares two pools of 13. The deeper note's words are asserted, and the balanced view has none (`tests/integration/test_discovery.py:174-175`). | Yes, both are real checks now. |
| Plural article | **Done** | `exploration.py:604-614`. Over 3,043 preferred labels in the CSV, only "warehouse operators for clothing" loses its article. "actress", "boss", "waitress" and the rest keep theirs. | Yes (undone, it fails). |
| DIV1-08's case count | **Done** | 54 cases: 19 discovery, 14 interview, 13 support, 7 guard and 1 explanation, counted from `evaluation_cases.json` (`docs/requirements-register.md:132`). | Not applicable. |
| Before and after, P01–P05 and the examples | **Reported** | The report's table covers all of them plus "working outdoors". | Not reproduced (no database). |

## Changed tests and inputs

All are disclosed in the report, and each is still a real check, except the one below.

- Real checks:
  - "Planning shifts" became "stocking shelves" (44 occupations, through one skill) in the
    I-B test and the share test. It still tests the tie and the share.
  - The pool-bound test now uses four specific searches reaching 178, with
    `beyond == 178 - 120`. That is stronger than before.
  - DSC-07's `work_style_not_searched` was dropped, because "quiet concentration" is now
    searched, so the check would pass by construction. `missed_answers_named` replaces it.
  - The deeper-note assertion is stronger.
- **Not disclosed, passes by construction (M3):**
  `test_where_someone_likes_to_work_is_searched_and_a_specific_answer_s_work_comes_first`.
  Its "bicycle mechanic first" half is meant to show N-M4. But the demo puts work style in
  the environment channel (`fixture_discovery.py:30`), weighted 0.6 (`slate.py:113`). The
  bicycle mechanic's 1.0 puts it first under the old order too. The domain test carries
  N-M4.

## The two fixes beyond the list

Both are correct and in scope. Each follows from N-I2's "it may still add weight to work
another answer found".

1. **Searched again among the other searches' work.** Without this, a general search's
   weight depended on where its own 120-and-ties cut fell, which is arbitrary for the person.
   `essential_skill_reach_among` (`taxonomy_store.py:301`) matches exactly as
   `essential_skill_reach` does: the same `plainto_tsquery`, essential relations only, the
   best skill per occupation, no cut. It adds one bounded query per general search.
2. **A general search adds only the 0.2.** `_found_by` (`slate.py:344`) leaves general
   matches out of the best score and the floor, and `_relevance` still counts them as a
   further query (`:350`). Undone, the domain test fails. Every candidate keeps at least one
   non-general match, because a general hit is pooled only where another query already
   found that occupation (`:459`), so `max` and `min` are never empty.

One side effect for the record (not counted): a general search's channel joins the
candidate's channels. A general "transferable" search can therefore make found work
"building on skills you could carry over". That is true, since the essential skill holds the
answer's words.

## The live path, with `discovery-queries-3`

**Yes, it can do both.** Suppose a person says "writing inspection reports for bridges" and
the model writes only "write reports". That search is too general (217 occupations), so it
finds no work alone, and the answer's real work (the inspectors that "write inspection
reports" would reach) is hidden. The slate then says:

> The search “write reports” (from “writing inspection reports for bridges”) is part of 217
> occupations in ESCO, too many to choose from on its own. Say more about “writing inspection
> reports for bridges”, such as what it's about or who it's for.

I checked this output by calling `_general_note` directly.

- **Is it honest?** Its facts are true. It names the model's search, not the person's words,
  as the general one, and the answer is not wrongly named as "found no work".
- **But the advice is wrong.** It asks the person to say more about an answer that already
  says what the reports are about. The code knows this case: it is the branch where the
  search isn't the answer's own words (`exploration.py:980-982`). That branch could say the
  search was too general without asking the person for more (M1).
- **Is it recorded for session W2?** Only in the report (Concerns, item 2). ADR 0007 records
  the prompt as untested live, but not this consequence. The W2D carry-forward sheet
  (`carry-forward-task-W2D.md`) has no round 3 items yet. It belongs on the sheet (below).

## Truth rules

- **No suggestion without a named essential skill:** holds. A general search finds nothing
  alone, and its added line names the essential skill that holds its words. Joins, the role,
  targets and hypotheses are unchanged.
- **Unknown is never zero:** holds. `reach` is `total` or the exact number of hits, and
  `beyond_pool_limit` is exact. A general search's `hits` of 0 means it added weight nowhere,
  and the API description says so.
- **An empty or small slate says why in plain words:** holds. "None of your answers found
  work to suggest yet." comes with the missed, general and work-style notes. A small full
  slate gets the small-pool note.
- **No note claims something untrue:** **broken twice** (I1, I2).
- **Nothing implies a job offer:** holds.
- **DBOS `application_version`:** still `careerwright-l0-1` (`identity/worker.py:30`). No
  migration, and `identity/` is untouched.

## New findings

### Critical

None.

### Important

**I1. "isn't how ESCO names any skill" is false for skills ESCO lists as essential to no
occupation.** This is the ruled wording: re-review 2 suggested it, and the controller adopted
it.

- **Where:** `exploration.py:968` and `:971-972` (both wordings), and the skill half of
  `_general_note` (`:987-988`).
- **What:** the search reaches a skill only through occupations it is essential to
  (`taxonomy_store.py:266-267`). In the pinned CSV, 2,582 of 13,960 skills are essential to
  no occupation, and 1,027 of them are short competences.
  - "Taking pictures" finds only ESCO's skill "take pictures", which is essential to 0
    occupations (optional for 2). So it reaches nothing, and the slate says "“Taking
    pictures” isn't how ESCO names any skill, so it found no work." ESCO names exactly that
    skill.
  - The same happens with "making reservations" ("make reservations"), "meeting commitments"
    and "maintaining physical fitness".
  - A weaker case: "training new staff" is ESCO's own alternative name for "train crew
    members".
  - The same root shows in the general note. "“Training staff” is part of 10 different ESCO
    skills" counts only essential skills, but ESCO has 14 skills holding both words.
- **Why it matters:** it gives the person a false reason. Rewording won't help them, because
  no occupation lists that skill as essential.
- **Fix:** say what was checked. For example: "“Taking pictures” isn't in any skill ESCO
  lists as essential for an occupation, so it found no work." and "...is part of 10
  different essential skills in ESCO...". The slate already says "essential skill" in its
  lines. `missed_answers_named` matches "found no work", so it needs no change.
- I worked this out from the CSV and the code, not on PostgreSQL. The search's own stem
  rules can only make it match fewer of these labels, not more.
- The named cases are true as worded: P01's two tasks, P02's "repairing physical objects"
  and "small team", DSC-03's two tasks, "giving injections" and "quiet concentration". No
  skill label holds those words.

**I2. The join note's "keeps the 30 that share the most" is false on P03's slate.**

- **Where:** `exploration.py:994-999`.
- **What:** the sentence before it counts shared essential skills, so "share the most" reads
  as the most shared skills. But the join ranks by the share of both roles' skills
  (Jaccard). For the ICT help desk agent (P03's "IT support technician"), the kept live chat
  operator shares 5 essential skills. 39 occupations it left out share more: the ticket
  issuing clerk shares 7. For the data analyst, the bioinformatics scientist (4 shared) is
  cut while the business economics researcher (3) is kept.
- **Fix:** name the measure. For example: "Careerwright keeps the 30 that have the largest
  part of their essential skills in common with it." Or "the 30 most alike in their
  essential skills". Update the Vitest string and the ADR quote with it.

### Minor

**M1. The live path asks the person to say more about an answer that was specific**
(above).
- **Where:** `exploration.py:980-991`.
- **Fix:** in the model-search branch, drop "Say more about…" or point it at the search.
  Either way, put the case on the session W2 sheet.

**M2. The live-path rules have no product test.**
- **What:** nothing tests "named only when every query citing it found nothing" (a ruled
  clause of N-I1), or the two model-search wordings. The DSC cases run the fixture proposer,
  which makes one query per answer. The eval test (`tests/eval/test_evaluation.py:275`) tests
  the evaluation's check, not `_missed_notes`.
- **What I found by calling them:** both are right. One edge: a model query resting on a
  task and a one-word style that finds nothing names the style as "found no work". But ADR
  0007 says a one-word style keeps its own note.
- **Fix:** one domain test of `_missed_notes` and `_general_note` with a model's queries.
  These are pure functions and need no database.

**M3. One full-release assertion passes by construction, not disclosed.** See "Changed tests
and inputs" (`tests/integration/test_evaluation.py:209`).
- **Fix:** disclose it, or give the specific and the general answer the same channel.

**M4. The web still calls a too-general search one that found work.**
- **What:** "Found by these searches" lists a search that only added weight
  (`Directions.tsx:73-91`). DSC-19's head teacher lists "writing reports". "found by N
  searches of ESCO" counts it too (`:521`). The API now flags `too_general`, and the web
  doesn't read it.
- **Fix:** mark it, for example "(added weight only)". Or put it on the session W2 sheet.

### Other observations (not counted)

- "Talk to someone who works as warehouse operators for clothing" (`explain`'s `try_it`):
  the plural title is still awkward there.
- `beyond_pool_limit` counts ESCO occupations, so a near-identical role a join cut counts
  once more. The report states this (Concern 4).
- The P02 slate now says "“Small team” isn't how ESCO names any skill". That is true, but
  odd for how someone likes to work. It's a wording item for the session W2 sheet.

## Session W2 sheet items (for the product owner; not fix items)

1. The too-general thresholds: more than 50 occupations, or more than 5 different skills
   none named exactly. Common answers now give empty slates that say why: "solving
   problems", "writing reports", "working in a team", "training staff", "analysing data",
   "managing budgets", "meeting deadlines", "planning shifts", "driving", "cleaning" and
   "drawing".
2. The general note's advice is generic ("Say more about it, such as what it's about or who
   it's for."). On the live path it can ask about an answer that was already specific, and
   hide that answer's work if the model searched it too generally (M1). The prompt
   `discovery-queries-3` is untested live.
3. One-word work style left unsearched. Longer ones are searched, and named when they find
   nothing ("small team", "quiet concentration").
4. The specificity order. P02's order is unchanged; DSC-17's changed (music director before
   disc jockey).
5. The words of every new note: missed, general, join and work style. The web line "N more
   were found but not kept."
6. The general search's line under "Found by these searches" (M4), if it isn't fixed.

The W2D carry-forward sheet has no round 3 entries yet.

## Spec compliance

- ✅ Every ruling and every "Fix now" item is implemented as ruled, with a test that fails
  without it. The exception is the live-path clause of N-I1 (M2).
- ❌ Truth rule "no note claims something untrue": I1 and I2.
- ⚠️ Cannot verify here:
  - the report's `make acceptance` run;
  - the full-release tests and the 19 DSC cases;
  - the before and after slates and the full-text counts;
  - the old code failing the new cases;
  - `discovery-queries-3` on a live model;
  - every human item ("not run — requires human").

## Strengths

- Each fix is small and in one place: the threshold in `too_general`, the floor in
  `_found_by`, the order in `_order`, the counts in `build_pool`. SQL `WITH TIES` closes the
  search's tie cleanly.
- Two wordings keep the live path from claiming that the person's own words were searched.
- The tests are real. Every fix I undid made a domain test fail, and the changed inputs keep
  their purpose.
- The report is candid. It names the live-path consequence, the empty slates and the count's
  folding caveat, and the join counts I could check match it exactly.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** Round 3 does what was ruled, and both extra fixes are sound. But two new notes
state something untrue in real cases: P03's join note, and any answer that names a skill
ESCO lists as essential nowhere. Each is a wording fix of a line or two, and neither reopens
matching.
