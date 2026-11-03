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

## Review

Independent review of ec059b3..fd864f0 (worktree `/Users/darianraad/Code/careerwright-wt/6ga`,
head fd864f0), 2026-11-03. Read the card, the dispatch, the design note, this report and the
3,265-line package in passes (backend, tests, web, docs), then the worktree code around each
named risk below. One read-only check ran with the backend venv (risk 4); no suite re-run, no
Docker, no web requests, no live calls.

### Spec Compliance
- ✅ Spec compliant with the card's slice A and dispatch items 1 to 6:
  1. The table (43 sub-major groups), an offline shape test, and an integration test against
     the pinned, hash-checked release's own group descriptions.
  2. The reference comes from the role alone. Unknown is `level: null`, never a number: no job
     yet, skipped, own words, several occupations with none chosen, or groups at different
     levels. ISCO's bands then decide. Targets never set it.
  3. Two sets through the one `_rerank`, three each, Next step first; Next step's balance is
     2/1/0. No direction heading anywhere in the web (grep of `src` and `e2e`). Facts and codes
     in the API, the client regenerated, words in `vocabulary.ts`.
  4. An Aim higher card carries the training sentence; a Next step card says nothing of
     training; no new word says suits, ready, pay or status (and a test checks it).
  5. Sam (DSC-22) and Maya (DSC-21) carry `reference_is`, `horizons_by_level` (an oracle that
     shares no code with the product's table) and `both_horizons`, so neither can pass on an
     empty or one-set slate.
  6. Spec section 22, ADR 0007, ADR 0015 and the register, in the last commit.
- ⚠️ Cannot verify from diff: `make check` and the focused integration runs (the report's
  claims, not re-run); `make acceptance` (the Playwright journeys with the changed
  `e2e/api.ts`, and the Storybook build; the controller runs it); the 1280 and 390 walk
  (agent observation only); the product owner's live look at Maya and Sam (not run, requires
  human).

### Checks by named risk
1. **Deterministic slate; a target only by choice.** `place` is pure over the job group's code
   and the reference; each set is sorted by `_order` and chosen by the same `_rerank`; sets
   come in the enum's order. A family (ISCO minor group) sits in one sub-major group, so it has
   one level and one major group and always lands in one set: the family limit still holds over
   the whole slate. Making a target is unchanged (the person's click posts the concept). OK.
2. **A job group's level, never the person's, pay or status.** The table is keyed by sub-major
   group only; nothing reads pay, popularity or status; the web never shows a level number or
   the reference level, and its words say "your role's job group". OK.
3. **Unknown is unknown.** `reference_level` returns `UNKNOWN_REFERENCE` (level `None`) on
   every path but one occupation or one agreeing level; `ReferenceOut.level` is null; the web
   words the basis only. The full-release test covers ESCO, ONS, own words, no job yet and
   skipped. OK.
4. **A lookup that could fail the slate read.** `skill_level` raises for a code with no
   sub-major group and now runs on every ONS-coded role. Checked with the product's own parser
   over the pinned `ons-soc2020-volume2-coding-index-v14.xlsx`: 32,435 entries, 425 distinct
   ISCO codes, none without a level. `_reference` (`exploration.py:949`) indexes `facts` by the
   role's occupations without the guard `familiar_families` keeps (`exploration.py:896`), but
   those occupations come from held URIs and are pooled as "r1", so they are always in `facts`.
   No finding.
5. **Words.** No em dash in any added line (grep of the package); no internal codes; Next step
   is never worded by level.
6. **Evaluation.** The unit test shows each new check failing on a wrong set, a wrong order, a
   wrong level and an unknown served as 2. DSC-21's scripted searches are offline only
   (`_offline_slate`); live still lets the model propose. The report is open that DSC-21 had
   passed on an empty slate, and a full-release test records it.
7. **Spec section 22 and ADR 0007 against line 283.** Reads true: line 283 forbids optimising
   for prestige and treating common work as bad work. The change splits by a stated, computed
   training level, ranks within each set by the same relevance reranker and never words Next
   step's level, and the row says so. See the questions below on the level-4 rule.

### Journey and load (Part 3)
Walked in code (`Directions.tsx`, `vocabulary.ts`), before (ec059b3) and after:

| Step | Before | After |
|---|---|---|
| View buttons and count line | 4 or 5 buttons, 1 line, nothing to type | Unchanged |
| "How Careerwright searched" (closed, one step away) | Its lines | One more line for everyone (how the sets were placed); a short slate can give two "found only" lines (one per set) instead of one; "doesn't know your current work" is gone |
| Set headings | Up to 3, by direction ("Directions to consider" for unknown work) | Up to 2: "Next step", "Aim higher" |
| Closed card | Title and one line (kind of work) | Title and one line; on Aim higher the line adds the training sentence, growing from about 55 to 130 to 150 characters |
| Open card | Choice first, one bright action, quiet teal actions | Unchanged; the kind-of-work line gains the training sentence on Aim higher |

No new place to type, no new or competing action, nothing shown before a choice that must
come first, no em dash. Net: one fewer heading, one more note line, longer Aim higher lines in
the scan list (Minor 1).

### Strengths
- Small, deep, pure modules: `skill_levels.py` (one table, one lookup) and `horizons.py`
  (reference and placing). The reranker is extracted (`_eligible`, `_rerank`, `_slate`) and
  shared by both sets and the first scatter, not copied.
- The table is checked against the pinned release's own statements, independently of the
  product's import.
- Unknown stays unknown at every boundary: domain, API null, web words by basis only.
- An honest report: the DSC-21 empty-slate finding, the uncaptured RED run, the odd Aim higher
  pick and the words still needing the product owner.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. **Load in the Aim higher scan list** (`apps/web/src/components/Directions.tsx:455`,
   `apps/web/src/lib/vocabulary.ts:773`). The training sentence is on every closed Aim higher
   card. For a known level-4 role all three say the same sentence, so it can't help choose
   which to open, and at 390 wide each closed card wraps to several lines. Fix: show it only in
   the open card's "What the work is" (still "an Aim higher card says"), or once under the Aim
   higher heading when the set shares one level. For the product owner's session sheet.
2. **The placement note shows with nothing placed** (`Directions.tsx:793`). "Careerwright
   placed each suggestion..." appears when the slate is empty (nothing found, or all filtered).
   Fix: only when `data.suggestions.length > 0`.
3. **The level-4 note is incomplete** (`vocabulary.ts:785`). For a level-4 role, Aim higher's
   level-4 work is placed by its major group, not its training, while the note says each was
   placed by training and the cards then name the same degree-level training as the person's
   own role. It says less, not something false. See the questions below.
4. **"Found no work ... closely enough" when a filter or exclusion emptied a set**
   (`vocabulary.ts:973`, `backend/src/careerwright/profile/slate.py:696`). The count is taken
   after hard filters and exclusions, so with "hide unscored" on the person reads "Careerwright
   found no work for Next step that matches your answers closely enough" although work matched
   and their filter left it out; `backend/tests/integration/test_discovery.py:281` pins it, now
   once per set. Existing behaviour (the old "Only 0 occupations matched" had the same fault),
   and the filter's line beside it gives the count. Fix later: count from the floor alone, or
   say "after your filters".
5. **The "More depth" note overstates** (`slate.py:546`, `vocabulary.ts:965`). A set holds three
   and a family lives in one set, so at most three from one kind of work can show, while the
   note says "Showing up to 4". DIV1-11's relaxation is now two to three. Fix: word the cap the
   slate can reach, or record the limit.
6. **A narrowed regression test keeps its old name**
   (`backend/tests/integration/test_evaluation.py:134`): it now compares only what the searches
   found (`pool_shape`), not the slate. Name kept for citations, and its comment says so. At the
   final review, rename it, or record the two-set slates so a later unintended reranker change
   is caught on the full release.
7. **A known limit asserted as expected** (`test_evaluation.py:499`): Maya's as-written answers
   finding no work. Useful as a record, but a better search would fail it; say in its comment
   that it is a known-limit record to update, not to "fix".
8. **Register and ADR words** (batch for the final review). `docs/requirements-register.md:171`
   (DIV1-12) still says "with no familiarity known the slate says so" (that line was removed)
   and "no rarity, prestige or popularity input exists" (true, but a skill level is now an
   input); `docs/adr/0007-conversation-discovery-and-support.md:1121` says the controls are
   unchanged, then lists their new per-set balances.
9. **Sentence rule, wording from the card** (`vocabulary.ts:764`). "Most work in this job group
   usually needs a degree or equivalent training." is the card's own example and is hedged, but
   it states what ISCO holds rather than what Careerwright checked. For the product owner's
   session, with the level-2 and level-3 words the report already flags.
10. `familiarity_known` is now read by no web code (`Directions.tsx` dropped its only use); the
    API still serves it. Keep or retire at the final review.
11. The `few_matched` words sit in `FEWER_REASON` (`vocabulary.ts:973`), outside the
    suggestions section the dispatch named; the report already flags the merge with slice E.

### Questions for the product owner's session (suggestion quality, not findings)
- Sam's Aim higher holds an equine dental technician (reached through "assist customers") and
  Maya's Next step a pulp grader. Sensible?
- With a degree-level role, Aim higher is degree-level work in another major group (a
  warehouse manager sees engineering professionals; a teacher would see managers). Is that
  "aim higher"?
- With the level unknown, someone whose real role needs a degree still sees levels 1 and 2 as
  their "Next step". And with a known role, Next step holds everything at or below it, so a
  degree-level role's Next step can hold elementary work. Acceptable for L0?
- The level-2 and level-3 training words.

### Assessment
**Task quality:** Approved
**Reasoning:** Slice A is built as the card asks: a pinned table checked against the release,
unknown kept unknown, both sets from the one deterministic reranker, no direction heading left,
and Sam's and Maya's cases can't pass on an empty or one-set slate. The Minors are load, wording
and record tidiness for the list; none changes a decision, hides a failure or loses input.
