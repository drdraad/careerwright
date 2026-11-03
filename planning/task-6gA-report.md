# Task 6g slice A: report (implementer, worktree 6ga, branch wt-6ga)

Status: DONE_WITH_CONCERNS. Head fd864f0, rebased onto `claude/confident-ramanujan-ux3saw`
(ec059b3).

Commits:
- a6cbb92 the pinned skill-level table by ISCO-08 sub-major group, checked against the pinned ESCO release
- de068c3 the slate in two sets, Next step and Aim higher, placed by each job group's usual training
- fd864f0 the spec's section 22 row, ADR 0007's amendment, ADR 0015's line and the register rows

## What I built

1. **The skill-level table** (`backend/src/careerwright/catalogue/skill_levels.py`): ISCO-08's
   usual skill level for each of its 43 sub-major groups (managers 4 except group 14 at 3,
   professionals 4, technicians 3, groups 4 to 8 at 2, elementary 1, armed forces 4/2/1), and
   `skill_level(code)` for any sub-major, minor or unit code (a major group alone is refused).
   `tests/integration/test_skill_levels.py` reads `ISCOGroups_en.csv` from the pinned release
   file (hash-checked), derives each sub-major group's level from its own description, or its
   major group's where it states none (only 25, ICT professionals), and compares.
2. **The reference level and the placing** (`backend/src/careerwright/profile/horizons.py`):
   from the role alone, its one ESCO occupation's group, else the ONS groups of its title when
   they are all at one level; otherwise unknown (no job yet, skipped, own words, several ESCO
   occupations with none chosen, groups that disagree), never a number. Next step is at or
   below it, Aim higher above it; for level 4, level-4 work in another major group; unknown
   uses ISCO's bands (1-2 Next step, 3-4 Aim higher). `exploration._reference` reads it from
   the role's resolved title and record.
3. **Two sets** (`backend/src/careerwright/profile/slate.py`): `choose_slate(..., reference=)`
   splits the eligible candidates by set and runs the same reranker (`_rerank`) on each, three
   each, Next step first. Balances per set: Next step 2 close / 1 transferable / 0 less
   familiar; Aim higher 1/1/1. A set short of three says so: `FewMatched` gains `horizon`.
   The world's first scatter (origin) is unchanged in what it chooses: `choose_first_scatter`,
   one set of six, 2/2/2 (its `FewMatched.horizon` is null).
4. **API facts** (`discovery_schemas.py`): `SuggestionOut.horizon`, `SuggestionOut.skill_level`
   (1 to 4), `SlateOut.reference` (`basis`, `level` null when unknown). Generated client
   regenerated with `pnpm run generate`.
5. **Web** (`Directions.tsx`, `vocabulary.ts` suggestions section): the slate is headed "Next
   step" and "Aim higher", never by direction (no "Directions to consider", no "Close to what
   you do now" for anyone). An Aim higher card's kind-of-work line adds what Careerwright
   checked: level 4 "Most work in this job group usually needs a degree or equivalent
   training.", level 3 "... one to three years of study after A-levels or similar.", level 2
   "... GCSEs or similar, sometimes A-levels or a vocational course." A Next step card says
   nothing of training. One note under "How Careerwright searched" says how the sets were
   placed (by basis; the unknown one names no work, so it holds for Maya). `few_matched` words
   name the set. Removed, orphaned by the change: `DIRECTION`, `CLOSE_WITHOUT_WORK`,
   `WORK_NOT_KNOWN`. Stories and e2e/api.ts updated to the new facts and order.
6. **Evaluation**: new checks `reference_is`, `horizons_by_level` (an independent level oracle
   from ISCO's major-group statements, plus order and at most three per set) and
   `both_horizons`. Sam is DSC-22 (new); Maya is DSC-21, now with the searches a model might
   propose offline. Added the checks to DSC-01, DSC-03 (role_occupation, level 4) and DSC-16
   (ambiguous role: unknown).
7. **Docs** (last commit, after the rebase): spec section 22 row (the 2/2/2 balance replaced
   for L0; placed by a job group's usual training, never pay or status, beside section 4's
   prestige rule), ADR 0007 amendment, an ADR 0015 line, register rows DIV1-06 (renamed test),
   DIV1-11, DIV1-12, DIV1-16 (new) and TEST1-16.

On the full release (focused integration run): Sam (DSC-22) Next step: tourist information
officer, ticket issuing clerk, post office counter clerk; Aim higher: equine dental
technician, customer experience manager, ICT help desk agent. Maya (DSC-21) Next step: school
bus attendant, pulp grader, babysitter; Aim higher: chemistry technician, child care
coordinator, microelectronics materials engineer. DSC-03 (warehouse supervisor, level 4): Aim
higher holds two engineering professionals.

## Rulings (the simplest reading; each recorded in ADR 0007's amendment)

- **The origin keeps one set of six.** The world's first scatter isn't split: its near and far
  lines are a later slice, and splitting would change what the world shows at the first
  answer. Each destination still carries its `horizon` fact. Easy to switch later.
- **Aim higher's balance is one of each direction;** "Closer to what I do": Next 3/0/0, Aim
  2/1/0; "Less familiar": Next 1/1/1, Aim 0/1/2; "Broader" and "More depth" use the balanced
  sets. Provisional (R6).
- **After "None of these is my job"** the title's ONS groups still give the level: the person
  declined ESCO's occupations, not ONS's coding of their title.
- **An ambiguous role** (several ESCO occupations, none chosen) is unknown.
- **No direction headings at all.** The two horizon headings replace the three direction ones
  (fewer headings); each card's lines still say how it was found, and "different kind of work"
  still shows where the API knows it.
- **Maya's case is DSC-21, not a new case.** Plan v1.6 caps her cases at four to six (five plus
  the browser test now). Her answers searched as written find no work on the full release, so
  DSC-21 had passed on an empty slate; a new integration test proves that, and the case now
  gives a model's searches offline (live is unchanged: the model proposes).
- **The pre-6d slate recording** (`test_every_evaluation_case_s_slate_is_the_one_before...`) now
  compares what the searches found (pool, every pooled occupation, searches, titles), not what
  the slate chose from it, which changes by design. Name kept so ADR and register citations
  still resolve; the comment says so.
- **The training sentence** sits in the kind-of-work line, not a new line, so lines per card
  stay as before.

## Checks run (all on the final code unless said)

- TDD: `test_skill_levels.py` RED (ModuleNotFoundError) then GREEN; `test_slate.py` RED
  (ImportError on `HORIZON_SIZE`) then GREEN (23 passed). `test_horizons.py` was written
  before `horizons.py`, but I didn't capture its RED run before writing the module.
- `make check`, after each change and after the rebase: exit 0. Backend 2193 passed, 123
  skipped (pre-existing: bodies kept only on the curating machine), Vitest 502 passed, Biome,
  tsc, client drift check clean.
- Focused integration, under the lock, one guarded command each (`mkdir` lock, `rmdir` after,
  lock confirmed released each time). Final run on the rebased branch:
  `pytest -m integration tests/integration/test_evaluation.py test_discovery.py test_origin.py
  test_slate_explanations.py test_role_space.py test_skill_levels.py test_first_answer.py`:
  95 passed in 124 s. "discovery cases: 22, failures by type: {}".
- Journey walk (contract item 6), in Storybook with telemetry and the update check off (port
  6116, stopped afterwards): story You / Slate of six at 1280 and 390 wide. Headings: two
  ("Next step", "Aim higher"), before up to three. Each closed card: a title and one line. The
  open card's sections and actions are unchanged; one bright action ("Make this a target"),
  quiet actions teal; the notes stay one step away. No em dash in any words I added. These are
  agent observations, not the human design review.
- `make acceptance`: not run, the controller runs acceptance (Playwright e2e and the
  Storybook build included; I changed `e2e/api.ts` and the stories, neither run end to end).

## Live calls

None. Cost $0.

## Not run, and concerns

- **Sam's Aim higher can still hold odd work.** Approach A re-sorts the same pool: the equine
  dental technician is still there, now in Aim higher (it lists "assist customers", and the
  too-general "communicate with customers" adds weight). The design note expected this; slice
  B (Muse's checked Aim higher ideas) is the answer. The product owner's live look at Maya and
  Sam: not run, requires human.
- The level-3 and level-2 training sentences are mine (the brief gave level 4's); they turn
  ISCO's education levels into UK terms. They need the product owner's eye.
- `horizons_by_level` can't check level-4 work for a level-4 role (the slate doesn't serve the
  role's major group); the domain tests cover that rule.
- Merge risk with slice E (worktree w2fe, not yet integrated): it edits `vocabulary.ts`,
  `YouChapter.test.tsx`, `Conversation.stories.tsx`, `test_discovery_contract.py` and appends
  to ADR 0007. My hunks are in different places, but whoever lands second may need to rebase.
  Both add an ADR 0007 section at the end: keep both.
- Two screenshots I took landed under the main tree (the root, then `.playwright-mcp/`). I
  moved both into my scratchpad at once; nothing of mine is left in the main tree. The
  Playwright tool's snapshot and console logs sit in the main tree's gitignored
  `.playwright-mcp/`.

## Paths a reviewer can skip

`apps/web/src/generated/**` (generated client and openapi.json).
