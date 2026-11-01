# Task W2, slice W2B: re-review of fix round 2 (e8c0bfb..267a83f)

Reviewer: Claude (Opus 5.5), scoped re-reviewer. Read-only on the repository: no edits, commits
or staging; the working tree is unchanged at `267a83f` (only the untracked `answers-2.md`). No
subagents, no live model call, no web request, no image pulled.

## How I checked

- Read the reviewer contract, the fix-round-2 dispatch, re-review 1, the report's "Fix round 2"
  section and the whole package diff (28 files) in eight passes. Outside the diff I read only
  for named risks: `build_pool` and `_across_families`, `first_slate`, `titles.targets`,
  `SuggestionOut.of`, the web's `Directions.tsx` (what it shows of counts, notes and
  searches), the fake discovery model, `list_profile_versions`, the interview's field words.
- `make check` on `267a83f`: exit 0. Ruff format and lint, mypy, pytest 1,539 passed and 319
  deselected, the fixture validator, the generated client matching OpenAPI, Biome, `tsc`,
  Vitest 299 passed.
- A throwaway PostgreSQL 16.15 container from the **cached** `postgres:16.15-bookworm` image
  (checked with `docker image ls` first; no pull), synthetic roles and passwords, a random
  loopback port; removed afterwards. The pinned ESCO v1.2.1 loaded through the repo's own
  `migrate_app` and `import_taxonomy` (3,039 occupations, 13,939 skills). Then, with scratch
  scripts outside the repo:
  - every discovery case through `observe_discovery_offline` and `evaluate`: 17 cases, 0
    failures; P01–P05, DSC-16 and DSC-17 match the report's after-slates;
  - the four example phrases and 25 everyday answers through the same path;
  - each fix undone in-process (I-A, rule 2, M-A, the share order), to see which case or test
    fails;
  - SQL over the release for ties at both cuts, how many skills and occupations a phrase
    reaches, and the prompt's example counts (all six are right: 58, 1, 16, 47, 6, 0);
  - the type-ahead for eight typed titles; the heaviest slate (eight broad searches) timed at
    0.24 s.
- Not run: `make acceptance` and the integration suites (the report's two runs are claims I
  did not repeat), any live call, and every human item ("not run — requires human").

## The question that matters: does any suggestion still read as arbitrary?

**For the named cases, no.** Read as the product owner would:

- **P01**: empty, with two plain reasons ("None of your answers matched…", "“Data quality
  analyst” isn't a title ESCO lists… Choose the ESCO occupation closest to it") and the
  work-style note. The type-ahead offers the data quality specialist first, and choosing it
  gives a skill-joined slate.
- **P02**: six outdoor jobs, each through "work in outdoor conditions". Each is defensible.
  The slate is thin, and it does not say why "repairing physical objects" found nothing (see
  "honest emptiness" below).
- **P03**: the role join, unchanged and defensible. **P04, P05**: empty with the reason; P04's
  type-ahead now starts with five nurses.
- **"Looking after people"** and **"teaching children, writing stories"**: empty, with "None
  of your answers matched an occupation in ESCO yet."
- **"Caring for patients, giving injections"**: two nurses, with the family-limit reason.
  **"Designing websites, writing code"**: three web roles.

**For common everyday answers, yes.** Rule 1 (every word of the phrase in one skill) is
necessary but not enough. A short, generic phrase still reaches dozens or hundreds of
occupations through skills that add a domain to it, and the slate's variety bonus then
spreads its six picks across unrelated kinds of work:

| Answer | Reaches | The slate offers |
|---|---|---|
| "solving problems" | 77 occupations through 10 skills | gambling quality assurance engineer, lottery operator ("solve problems in gambling through digital means"), public administration manager, ground lighting officer, webmaster, nurse assistant |
| "writing reports" | 217 through 17 | emergency ambulance driver, chiropractor ("write reports on neurological tests"), city councillor, aquaculture mooring manager ("write technical reports"), consumer goods inspector, lieutenant |
| "working in a team" | 242 through 23 | leisure attendant ("work in fitness teams"), derrickhand ("work in drilling teams"), chief fire officer, firefighter, emergency medical dispatcher, firefighter instructor |
| "training staff" | 17 through 10 | ground lighting officer, air traffic manager, call centre quality auditor, recycling specialist, quality services manager, kitchen and bathroom shop manager ("train staff to reduce food waste") |
| "analysing data" | 92 through 13 | aeronautical information service officer, product development manager, customer experience manager, retail entrepreneur, talent agent, trade regional manager |

The aquaculture mooring manager that re-review 1 found for "writing stories" is back for
"writing reports". The known limit recorded for session W2 ("a one-word task answer
still matches on its stem") understates this: it is any short, generic answer, of one word or
two. See new issue N-I2.

## Each ruling and item

| Item | Status | Evidence | Can its test fail? |
|---|---|---|---|
| Rule 1, whole phrase in one skill | **Fixed** | `plainto_tsquery` only, every word required (`taxonomy_store.py:242-270`); the any-word pass and its weight are gone (`exploration.py:473`). `_every_word_in` needs every content word (`tools/evaluation.py:102`). | Yes. The unit test refuses one shared word ("looking after people" → "entertain people") and a partial phrase (`tests/eval/test_evaluation.py`, the `one_word`, `one_shared` cases). |
| Rule 2, work style finds no work | **Fixed as ruled** | `_work_style_only` (`exploration.py:518`), applied to queries and title ideas (`:730`, `:773`), with the note (`:872`). No flag. ADR records it as provisional. | Yes. Undone in-process, DSC-01, DSC-07 and DSC-12 fail `work_style_not_searched`. See N-I3 for a consequence. |
| Rule 3, no tie cut by the alphabet | **Fixed as ruled** | A search keeps up to 120 (`exploration.py:473`, `taxonomy.py:138`); equal ranks go to the larger share, in the search (`taxonomy_store.py:268-270`), the pool and the slate (`slate.py:293`, `:312`). | Yes. Undone in-process, the unit test fails (`test_slate.py`, the share test); the full-release test fails on the old 30-by-title cut (the report's RED, consistent with the SQL). No evaluation case catches it, so the unit test carries it. Residue at the 120 cut: N-M1. |
| The prompt (`discovery-queries-2`) | **Fixed** | `discovery.py:236`. Every example count is right on the release. Untested live, as accepted. | The contract test's size bound only. |
| Honest emptiness | **Partly fixed** (Important) | Empty and short slates give reasons; the small-pool note exists; DIV1-02's assertion, the row and DSC-12 are updated as ruled. **But no slate ever says which of the person's answers found nothing.** P02's first answer, "repairing physical objects", reaches no skill; the slate gives the work-style note and "chose these from 12 occupations…", never that. The same silence for DSC-03 ("training new starters", "planning shift rotas"), "giving injections", "writing code", "recording songs". Rule 1 makes this common. The web shows a slate's searches only per suggestion, so a search that found nothing is never shown (`Directions.tsx:72`). | No check covers it. |
| I-A, a folded role's skill | **Fixed** | `Match.concept_id`, `own_matches` (`slate.py:229`), used in `explain` (`exploration.py:586`) and the connection (`slate.py:581`). | Yes. Undone in-process, DSC-17 fails ("sound editor: … mix multi-track recordings") and so does the unit test. |
| I-B, alphabetical ties | **Fixed** | As rule 3. "Planning shifts" keeps all 58; the warehouse worker comes first with both answers. | Yes (above). |
| M-A, a shared title | **Fixed** | `_joinable` (`exploration.py:511`) for the role, a target and a title query; `ambiguous_titles` and the reason (`:807`, `:864`). The first slate already asked which. | Yes. Undone in-process, DSC-16 fails (tram driver, private chauffeur, taxi driver joined). |
| M-B, closest titles | **Fixed** | Whole words first and status words not counted (`taxonomy_store.py:404`, `taxonomy.py:162`, `:206`). "Registered nurse" now gives nurse assistant, specialist nurse, veterinary nurse, advanced nurse practitioner and nurse responsible for general care, then "dry nurse", "foetal nurse", "nursery nurse". The bookkeeper stays first for P05. "Registered senior" gives an honest empty answer. | Yes (`test_first_answer.py`, its whole-before-prefix assertion). |
| M-C, the pool bound | **Fixed** | A full-release test fills the pool to 120 from two searches (`tests/integration/test_evaluation.py:114`). DIV1-02's row is rewritten. | Yes. The count beyond it is wrong for a single search: N-M2. |
| M-D | **Fixed** | With rule 1. | Yes. |
| M-E, a moved or re-added answer | **Fixed** | Words compared across every earlier version and all three fields (`strengths.py:128-150`). | Yes. On e8c0bfb's code the re-added "reconciling accounting entries" is in v4 and not v3, so a new run starts; the test wants 422 `no_new_answers`. |

Counts: **0 not fixed, 1 partly fixed (honest emptiness), 0 regressed.**

## The changed tests

- **DIV1-02's P02 assertion** (`tests/integration/test_evaluation.py:75`): as ruled. Its bound
  half still cannot fail (`build_pool` never exceeds its limit; same as before). Its reason
  half is real but repeats DSC-01's `small_pool_has_reason`. The bound is really exercised by
  the new two-search test. Not weakened beyond the ruled softening.
- **DSC-12, `fewer_has_reason`**: real; it fails if the reasons go. With an empty slate,
  `searched_through_skills`, `grounded` and `distinct` are now empty passes, so DSC-12 guards
  the unmatched title, the reason and `work_style_not_searched`. That is the ruled trade.
- **Sample-release inputs** ("tuning bicycles", "applying restoration techniques",
  "maintaining plant growth"): each holds every word of a sample skill, so the durable run,
  grounding and explanation tests still exercise real retrieval. Their phrasing is ESCO's,
  not a person's, but those tests are about the pipeline. Not weakened.
- **`test_live_eval_ledger`'s EXP-01**: the extra answer is added for this test only
  (`model_copy`), and the assertions are unchanged; "explanation complete" still needs a
  suggestion. Not weakened. The real `make live-eval` is unchanged: EXP-01 on the full release
  still has six suggestions.
- **Two assertions now pass by construction**, neither disclosed: DSC-07's
  `pool_includes_pool_of`, and `test_discovery.py:172`. See N-M3.

## The implementer's own calls

1. **`work_style_not_searched`**: right, and needed. Rule 1's check cannot catch a one-word
   style matching on its stem ("structured" agrees with "structures"). It fails when rule 2 is
   undone.
2. **Rule 2 on title hypotheses**: consistent with the rule's reason, and recorded in ADR 0007.
   It sits inside the accepted "rule 2 against REC1-03" question, since REC1-03 literally
   says "a preference informs hypotheses". Fine for session W2 to confirm.
3. **`SlateOut.ambiguous_titles`**: regenerated and committed (`schemas.gen.ts`,
   `types.gen.ts`, `openapi.json` in 267a83f; `make check`'s drift check passes). Only the
   evaluation's `titles_ambiguous` reads it. The web reads neither it nor `unmatched_titles`,
   so it mirrors an existing pattern. Note: the reason says "until you choose which one you
   mean". For the role the origin's chooser does that. For a target there is no direct step
   (`titles.targets` resolves a choice only by the occupation's own title), which was already
   true of `unmatched_titles`.

## The title join's best-30 cut (asked to judge)

**Yes, a person can see it, though rarely on the six.** Over the release:

- 1,796 roles join more than 30 occupations. For 744 of them the 30th place falls inside an
  exact tie (equal share and equal shared count, so equal skill counts too), and 1,570
  occupations are cut by concept ID, which is effectively random.
- **DSC-03's own role** (the warehouse manager): places 23 to 47 are a 25-way tie, 24 of them
  "wholesale merchant in …" plus the contact centre manager. The cut keeps 8 wholesale
  merchants ("tobacco products", "watches and jewellery", …) by ID, and drops the contact
  centre manager, another kind of work, for the same reason.
- Where it shows: "Show why this wasn't included" lists the kept variants, and the variety
  bonus can put one on the slate. In DSC-03 none reached the six.

**Smallest fix:** never cut inside a tie. After sorting, extend the cut to the end of the
tied group (at most 29 more on this release). In `skill_join_hits` that is a short loop after
`slate.py:162`. The search's 120 cut has the same residue (N-M1); in SQL it is `FETCH FIRST
:limit ROWS WITH TIES` ordered by rank and share, with the title used only to order what is
kept. One unit test each: two occupations tied across the cut are both kept.

## New issues

### Critical

None.

### Important

**N-I1 = honest emptiness, partly fixed** (above). Counted once, as the partly fixed item.
- **What:** an answer that finds nothing is never named while another answer finds work.
- **Fix:** a note for each answer that every search resting on it reached nothing. For
  example: "“Repairing physical objects” isn't how ESCO names any skill, so it found no work."
  Leave out work style, which has its own note. Show it on full and short slates. Add a check,
  for example `missed_answers_named`, to DSC-01 (P02), DSC-03 and the patients case. On the
  live path an answer may be cited by several queries; name it only when all of them found
  nothing.

**N-I2. Short, generic answers still give scattered slates** (ruling needed; not an
implementation defect). Figures are in the table above.
- **What:** a common task phrase ("solving problems", "writing reports", "working in a team",
  "training staff", "analysing data") reaches dozens or hundreds of occupations, through skills
  that add a domain to it. Each line is literally true ("ESCO lists ‘work in drilling teams’"),
  but the set reads as the keyword matching the product owner rejected.
- **Why it matters:** these are among the most common things people say. On the live path
  the model is asked for ESCO's wording, and "solve problems" reaches the same set. The
  recorded known limit (one-word stems) is narrower than what remains.
- **Fix, for the controller:** one deterministic candidate follows ADR 0007's own reasoning
  for the join ("one shared skill joins 337; three are needed"). A search that reaches more
  than about 50 occupations, or more than about 5 different skills with none naming exactly
  its words, is too general to find work on its own. The slate says so in plain words ("“Writing
  reports” is part of 217 kinds of work in ESCO, too many to choose from. Say what the reports
  are about."), and the search can still add to work another answer found.
  - On the release this rule also covers the accepted one-word cases ("driving" 71,
    "cleaning" 191, "drawing" 317).
  - It keeps "handling complaints" (47, 2 skills), "caring for children" (16), "working
    outdoors" (12), "selling products" (exact "sell products") and "leading a team" (exact).
  - It would also stop "planning shifts" (58), the prompt's example and the I-B test's input,
    so the thresholds are the product owner's to set at session W2.
  - Otherwise, record the wider limit, with these examples, in ADR 0007 decision 13 and on
    session W2's sheet.

**N-I3. Rule 2 also drops where someone likes to work, and the note then says something
untrue** (ruling needed).
- **Where:** `exploration.py:518`, `:872`; `fixture_discovery.py:30` (work style is the
  environment channel's source); `interview.py:464-465` ("work_style: how they say they like to
  work"); register DIV1-10 (`docs/requirements-register.md:134`).
- **What:** with `work_style: ["working outdoors"]` and "repairing bicycles", the slate is the
  bicycle mechanic alone and says "How you like to work (“working outdoors”) isn't used to find
  work: it describes how you work, not the work itself." As an enjoyed task, the same words
  reach 12 occupations through ESCO's own skill "work in outdoor conditions".
  `test_discovery.py` itself holds "working outdoors" as work style, and an interview model
  could well put "I like working outdoors" there.
- **Why it matters:** the note is false for a setting answer, since ESCO lists it as part of
  the work. DIV1-10's work-environment channel now has no source of its own, and its register
  row still says verified. This is separate from the accepted "rule 2 against REC1-03".
- **Fix, for the controller:** narrow rule 2 to how someone works, not where. One deterministic
  form: a one-word work-style answer ("structured", "collaborative", "practical") is not
  searched, and a longer one is searched under rule 1 like any other. On the release,
  "working outdoors" reaches 12 occupations, while "small team" and "quiet concentration"
  reach none. Otherwise, record the consequence in the DIV1-10 row and on session W2's sheet,
  and reword the note so it does not claim the answer is not about the work.

### Minor

**N-M1. Both cuts can still fall inside an exact tie.** See "The title join's best-30 cut"
above. At the search's 120 cut, the title still decides between 2 and 7 tied occupations per
broad search. Examples: "writing reports" keeps 2 of 9 tied, "meeting deadlines" 5 of 12,
"managing budgets" 1 of 4. The ruling allows the title as the last tie-break, so this is
residue, not a defect. It can still cost an occupation a second search's bonus, which was the
I-B scenario. Fix: never cut inside a tie (above).

**N-M2. The counts ignore what a search or join reached past its own cut.**
`taxonomy_store.py:270` (`total` is computed, then dropped in `_search_hits`), `slate.py:162`,
`exploration.py:804`, `Directions.tsx:520-524`.
- "Managing budgets" alone reaches 212 occupations. The slate reads "from 115 occupations
  found by 1 searches" and never "more were found than the pool holds" (`beyond_pool_limit`
  is 0).
- The small-pool note now sits on every join-only slate, including the "data analyst" slate
  the product owner reviewed (DSC-10, where `small_pool_has_reason` now requires it). It says
  "It aims for at least 60, but doesn't add weaker matches". Yet 47 occupations meet the
  join's own three-skill rule for the data analyst (117 for the warehouse manager), and the
  join keeps 30 by design.
- DIV1-02's row says "with the rest counted", which holds only for the two-search test.
- **Fix:** carry each search's and join's reach into `beyond_pool_limit`, as "at least" if IDs
  are not kept. For a join-limited pool, say the join keeps the 30 sharing the most skills, or
  raise the join to the pool bound as searches now are.

**N-M3. Two assertions now pass by construction.**
- **DSC-07's `pool_includes_pool_of`** (`tools/evaluation_cases.json:467`,
  `tools/evaluation.py:507`): DSC-07's and DSC-08's pools are both empty, so it checks
  nothing. REC1-03's row cites it as evidence that work style "still removes nothing".
  **Fix:** give DSC-07 and DSC-08 a task that reaches work under rule 1 (for example "caring
  for animals", 13 occupations).
- **`tests/integration/test_discovery.py:172`**, `assert deeper["notes"]`: the work-style note
  is now always present ("working outdoors" is work style in `ANSWERS`), so it no longer shows
  that "more depth" adds its note. **Fix:** assert the deeper note's words.

**N-M4. The share tie-break favours occupations ESCO lists few skills for** (ruled; for
session W2).
- P02's slate now leads with the leaflet distributor (6 essential skills) and the fruit
  picker (7).
- The landscape gardener (33) shows as "Matched less closely than the ones shown", though it
  matched the same skill at the same rank.
- With "repairing bicycles" and "working outdoors", the leaflet distributor comes before the
  bicycle mechanic, the only occupation the specific answer reached. Each search's best scores
  1, so nothing prefers a specific answer to a generic one.
- **Fix, for session W2:** order by how specific the search was (fewer occupations reached)
  before the share. Or put this example on the sheet.

### Other observations (not counted)

- **"Found by these searches"** for a folded lead still lists the folded role's search (the
  sound editor: "mixing recordings", `discovery_schemas.py:266`). That is DIV1-05 as
  accepted, and the fold is named under "show why". The I-A fix covers the stated skill only.
- **Connection grammar** in DSC-03: "A warehouse manager and a warehouse operators for
  clothing share 6 essential skills." This is `with_article` on a plural ESCO title, not this
  round's change.
- **Register DIV1-08**: still says "39 cases". The report discloses it; not this round's.

## Spec compliance

- ❌ Honest emptiness, partly: no slate names an answer that found nothing (N-I1).
- ✅ Everything else ruled:
  - the three rules and the prompt, with no flag;
  - I-A with its regression test and DSC-17; I-B with tests that fail on alphabetical cuts;
  - M-A, M-B, M-C, M-D and M-E;
  - DIV1-02's assertion and register row, DSC-12, and each changed assertion disclosed
    (except N-M3's two);
  - ADR 0007 amended; the client regenerated; `careerwright-l0-1` unchanged; no migration;
    `identity/` untouched.
- ⚠️ Cannot verify here: the report's two `make acceptance` runs (I ran `make check` only),
  `discovery-queries-2` on a live model (untested live), and every human item ("not run —
  requires human").

## Strengths

- Each ruling is implemented as written, small and readable.
  - `plainto_tsquery` closes the "or" loophole that web-search syntax would have left open.
  - `own_matches` fixes I-A at one point, for both the why-line and the connection.
- The tests are real: every fix I undid in-process made a case or test fail.
- The report is candid: it names the empty slates, the untested prompt, the join's ID
  tie-break and the stale DIV1-08 row. Its before and after slates reproduce exactly.
- The named cases now read as defensible. Where they are empty, they say so plainly.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** The rulings are faithfully done and the named slates are now defensible.

Two things stand against approval:
- **One implementation gap.** A slate never says which answers found nothing, which leaves
  P02's main cause unstated.
- **Two consequences of the ruled rules that need the controller's decision.** Common generic
  answers still give scattered, keyword-like slates. Rule 2 also drops where someone likes to
  work, and the note then says something untrue about it.

If the controller records the last two for session W2, with the DIV1-10 row and the note's
words corrected, then N-I1 and the four Minors are small fixes.
