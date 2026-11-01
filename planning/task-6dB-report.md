# Task 6d, slice B: report

Your title, recognised. Main tree, branch `l0-local-release`, on f7f0e4d. Migration **0036**
(`r0036_uk_titles.py`, `down_revision = "0035"`): Task 13b had not integrated when I committed
(its worktree still holds its own 0036), so 0036 was the next free number on the branch.

## What I built

### 1. The first question finds any UK title (card bullet 2; acceptance 1)
- **Type-ahead** (`GET /v1/taxonomy/titles`, `catalogue/taxonomy.py::match_titles`,
  `catalogue/uk_titles.py`, `reference_store.uk_title_matches`): ESCO's titles and the pinned
  ONS SOC 2020 coding index's, as one list, best first: what was typed, then a title beginning
  with it, then the rest, **ESCO first on ties**. An index title is one per normalised title
  however many entries ONS gives it, with every SOC 2020 unit group and ISCO-08 group it is
  coded to, none picked. A title ESCO itself offers (a preferred or alternative label, as a
  concept) is offered as ESCO's only. ESCO's closest titles (`partial`) only when neither list
  holds every word. The index is read only once imported: otherwise `REFERENCE_DATA_UNAVAILABLE`,
  never "not listed". A word index on the index's titles (migration 0036) mirrors ESCO's.
- **API**: `TitleMatchesOut.matches` is a discriminated list of `TitleMatchOut`
  (`source: "esco"`) and the new `UkTitleOut` (`source: "uk_title_index"`, `title`,
  `soc_codes`, `isco_groups`), plus `uk_total`.
- **"Use my own words"**: `POST /v1/workspaces/{id}/origin/role/title` (`name_role`) keeps any
  title exactly as given (1-120 characters, outer spaces trimmed) as the current role, citing
  the person's direct entry, through the one profile write path; the same title again is 200,
  unchanged. Nothing is refused and no model is called.
- **The web** (`components/FirstQuestion.tsx`, `Conversation.tsx`'s `Start`): the first
  question, "What do you do now, or what did you do last?", now leads the conversation view
  (before "How would you like to start?", as plan section 4 says). The field is an ARIA
  combobox: each ESCO option shows the label typed for ("In ESCO as …" when ESCO's own title
  differs), each index option "UK job title (ONS)", and the last option is always "Use my own
  words: “…”". When only part matched, the card's question shows above the list and the last
  option reads "None of these is my job", with "Use my own words: “…”" under it. Arrow keys,
  Enter, Escape and a click work; "Skip for now" goes on to how to start, saving nothing.
  Focus follows each decision to the next step's heading.
- **The world answers**: any answer lights the person's light (the world's existing `lit`);
  a browser test proves it within ten seconds of the pick, in the demo with no key.

### 2. "Which of these is closest?" (card bullet 3; acceptance 2, 3)
- **Origin** (`GET .../origin`, `RoleOut`): new `kind` (`esco` / `ons` / `own_words`),
  `uk_groups` (every ISCO-08 group the index codes the title to) and `closest`
  (`decision`: `not_yet` / `chosen` / `none_of_these`; every group with its ESCO occupations,
  by group then ESCO title; `chosen`). Asked when the index lists the role's title and no ESCO
  occupation holds it as a label.
- **Command** `POST .../origin/role/closest` (`choose_closest`): an offered occupation becomes
  the role's ESCO occupation with the person's words kept (a new profile version citing an
  `occupation_choice`, as `choose_role` does), so the origin's usual skills and destinations
  follow; `null` is "None of these is my job": the role names no ESCO occupation, and a
  closest occupation chosen before is let go (the role cites a direct entry again). An
  occupation outside the groups, or a role with no closest question, is `VALIDATION_FAILED`
  (`not_offered`).
- **The web** (`ClosestQuestion`): the card's heading, one line saying what Careerwright
  looked up, "None of these is my job" first (so it stays in the first screen), then each
  group under its ESCO name and ISCO-08 code, 12 occupations at a time ("Show N more"); a
  group the held release has none in says so. After "None of these is my job", or for a title
  no list holds, how to start is led by one line saying what Careerwright did and what isn't
  known yet (`ROLE_KEPT`), asking for no other job.

### 3. Title ideas the ONS index lists become suggestions (card bullet 4; acceptance 4)
- `TitleIdea.reason` (carried item 1): `in_esco`, `in_uk_title_index`, `not_yet_found`,
  `not_searched`. An idea ESCO doesn't hold is a suggestion only where the index lists it
  exactly (ADR 0015 decision 2), shown in its own list beside the slate ("Title ideas found in
  the UK job-title index", each with "Found in the UK job-title index (ONS). Not compared with
  your experience yet." and the answers it came from), never in the slate's pool. An idea no
  list holds is named as not yet found in the notes and never suggested.
- Evaluation: `unsupported_not_suggested` reads `reason`, and the new `title_idea_reasons`
  check; new case **DSC-20** ("data analyst" in ESCO, "Prompt engineer" in the index, "Orbital
  gardener" in neither) runs on the full release.
- Not built: making such an idea a target from the list (it can be named as a target in What
  we know). Recorded in REC1-06 and ADR 0015's line.

### 4. The lines that said a title isn't in ESCO (card's last bullet)
- The sketch: new resolution `uk_title`, "Found in the UK job-title index; Careerwright
  couldn't match it in ESCO" (its research status follows its coverage, as `not_found` does);
  a title kept as the person's own offers no "Closest in ESCO".
- The slate: new fewer reason `title_kept_as_own` for a title the person said "None of these
  is my job" for (never "Choose the ESCO occupation closest to it").
- Title ideas: "Titles Careerwright thought of but hasn't found in ESCO or the UK job-title
  index yet, so not suggested: …" (was "… couldn't match to an occupation in ESCO, so not
  suggested: …").

### 5. Each title's record knows the index (carried items 2 and 3)
- `TargetKind.ONS` and `TargetLink.NONE_OF_THESE` (the CHECKs of 0034 already allowed both);
  `TargetRecord.soc_codes`, `isco_codes`. `resolve_target` looks the title up in the index
  (exactly, on its normalised title) and records an ONS title with its codes; a choice made as
  the closest to the person's own title (`closest=True`) keeps the title's own kind;
  `none_of_these=True` names no occupation. The role named at the first question is recorded
  in the same table (one record per title as a concept, `targets.title_record`), so a target
  with the same title reads the same record.
- `OTHER_FIELDS` (in `targets.py`, with its reason): a qualifier naming another nursing field
  never reaches the pack's adult "Registered nurse" by the bracket rule.
- Setup imports the reference data before the seed (`cli setup-database`), since the seed now
  decides the fixture's target against the index too.

### Migration 0036 (`r0036_uk_titles.py`)
- A GIN word index on `soc2020_index_entries` titles (the type-ahead).
- Every stored own-words record whose title the index lists exactly becomes an ONS title with
  its codes.
- Every stored record the bracket rule took to the pack's adult nurse though a qualifier names
  another nursing field is decided again: no pack target by title, a crosswalk link it held by
  that title goes, and its coverage follows the occupation it still names.
- The table's comment says it holds the role's title too. No CHECK changed (ruling 2 below).
- 0034 and 0035 are untouched. A domain test keeps 0036's constants equal to 0035's and to
  `resolve_target`'s.

## Each new fact and its words

| Fact | Words (web, `vocabulary.ts`) |
|---|---|
| `TitleMatchesOut` UK option | "UK job title (ONS)"; ESCO option whose title differs: "In ESCO as {title}" |
| `partial` | "Careerwright couldn't match that title in ESCO. Is it one of these?" (the card's words); last option "None of these is my job" + "Use my own words: “{typed}”" |
| always-offered option | "Use my own words: “{typed}”" |
| no match | "Careerwright found no job title holding those words." |
| `RoleOut.closest` | heading "Which of these is closest?"; "Careerwright found “{title}” in the UK job-title index and looked up the ESCO occupations in the group/groups it's in."; group "{label} (ISCO-08 {code})" or "ISCO-08 group {code}"; empty group "Careerwright found no ESCO occupation in this group."; "Show {n} more"; "None of these is my job" |
| `RoleOut.kind` = `ons`, not in ESCO, none of these | "Careerwright found “{title}” in the UK job-title index and keeps it as your role, in your words. What this work asks for isn't known yet." |
| `RoleOut.kind` = `own_words`, not in ESCO | "Careerwright keeps “{title}” as your role, in your words. It couldn't match it in ESCO or the UK job-title index, so what this work asks for isn't known yet." |
| `title_kept_as_own` (fewer reason) | "Careerwright keeps “{title}” in your words and joins no other work to it by shared skills, because you said none of the ESCO occupations it offered is your job." |
| `TitleIdea.reason` = `in_uk_title_index` | list "Title ideas found in the UK job-title index"; "Found in the UK job-title index (ONS). Not compared with your experience yet."; "Careerwright thought of it from {answer source}: “{answer}”" |
| `TitleIdea.reason` = `not_yet_found` | "Titles Careerwright thought of but hasn't found in ESCO or the UK job-title index yet, so not suggested: {titles}." |
| `Resolution.uk_title` | "Found in the UK job-title index; Careerwright couldn't match it in ESCO" |
| first question | "What do you do now, or what did you do last?" (the plan's words); "Skip for now" |

Every map is exhaustive (`Record<…>`), so a new code fails `tsc`. One words test per fixed
sentence: `src/lib/discoveryWords.test.ts`. Session W2 judges the words (not run, requires
human).

## Carried items

1. **Reason codes and exhaustive maps** (slice A's facts review, M-1): `TitleIdea.reason`
   with `TITLE_IDEA_SHOWN: Record<TitleIdeaReason, …>`; `FOUND_NO_WORK: Record<SearchDid, …>`
   (fixed order) and `TOO_GENERAL_BY: Record<TooGeneralBy, …>` replace the branching. The
   reachable sentences are unchanged (their tests pass unchanged). One unreachable case now
   has its own words: an answer that is its own one search and found no shared occupation
   (before, it would have fallen to the "only common words" sentence).
2. **"Only a choice may cite a source"** fits both new kinds, so no CHECK changed (ruling 2).
3. **Another nursing field**: `OTHER_FIELDS` in `resolve_target`; one domain test per field
   ("(mental health)", "(children's)", "(children)", "(learning disabilities)" never reach;
   "(adult)" and "[2nd line]" still do); 0036 decides the stored records again
   (`test_0036_…`).

## Rulings I made

1. **The role's record lives in `target_records`**, one per title as a concept, shared with a
   target of the same title. Its kinds were built for it (ADR 0015 decision 3; slice A's
   dispatch). Consequence: a closest occupation chosen for the role is also that title's
   occupation as a target (Skills' seed by choice, decision 10's first step). The table keeps
   its name; its comment says so.
2. **No CHECK changed.** A closest choice is an `occupation_choice` and cites its source; an ONS
   title's codes are in its own row (`only_an_ons_title_has_ons_codes`); "None of these is my
   job" names no occupation (`a_link_names_its_occupation` already allowed it) and is the
   person's decision, recorded with `recorded_by` and `recorded_at`.
3. **The record is the provisional concept** ADR 0015 decision 3 describes. `name_role` does
   not also write `provisional_concepts` (that table keeps its own API, DIV1-03).
4. **The resolver is strict about the index**: without it, `resolve_target` and the type-ahead
   refuse (`REFERENCE_DATA_UNAVAILABLE`) rather than store "own words" for a title that may be
   listed. So setup imports the reference data before the seed, and so do the tests that seed
   a fresh database (disclosed below).
5. **The closest step is the role's.** The acceptance and the plan put it after the first
   question. Targets keep the sketch's existing "Closest in ESCO: Use …" (which replaces the
   title), now labelled `uk_title` where the index lists them; none is offered for a title kept
   as the person's own.
6. **"Use my own words" is one command for any title** (`name_role`): the server decides from
   the title itself whether the index lists it, so the same words picked from the list or typed
   give the same record.
7. **The first question comes before the entry choice**, as plan section 4 orders it, and can
   be skipped. Its first screen also carries the purpose line.
8. **Merging the two lists**: three tiers (what was typed; beginning with it; the rest), ESCO's
   then the index's within a tier, each list in its own order; cut to the limit.

## Acceptance items and their tests

1. Each of the four titles appears as a UK job title from ONS: `e2e/role-space.spec.ts`
   (demo, full release, no key, no external request); `test_first_answer.py::test_the_acceptance_titles_…`
   (API, full release, timed); `test_role_space.py::test_the_type_ahead_offers_uk_job_titles_…`.
2. Picking one keeps the exact words, the world answers within ten seconds (browser) and the
   API within a second, and the ESCO occupations in its ISCO-08 group with "None of these is my
   job" are offered: `e2e/role-space.spec.ts` (first test), `test_first_answer.py`,
   `test_role_space.py::test_a_uk_title_keeps_the_person_s_words_…`, `FirstQuestion.test.tsx`,
   `YouChapter.test.tsx` (the start's flow).
3. "Bookkeeping assistant": "Use my own words" offered and kept, the world answers, says what
   isn't known yet, asks no one to pick another job: `e2e/role-space.spec.ts` (second test),
   `test_role_space.py::test_a_title_neither_list_holds_…`, `YouChapter.test.tsx`.
4. A title idea the index lists is a suggestion with its answers and "found in the UK job-title
   index"; one in no list is not yet found: `test_role_space.py::test_a_title_idea_the_uk_index_lists_…`,
   DSC-20 (`test_evaluation.py`, full release), `Directions.test.tsx`. In the demo the fixture
   proposer never invents a title, so no browser test shows it.
5. No screen states skills, pay, readiness or openings beyond the sources: the origin of an ONS
   or own-words role has no usual skills or destinations (`test_role_space.py`); the world
   draws no skills (`e2e/role-space.spec.ts`); the title idea list says "Not compared with your
   experience yet" and nothing else about the work.
6. Facts with reason codes, no sentence, worded in the web, one test per fixed sentence:
   `slate_facts.py`, `origin_schemas.py`; `discoveryWords.test.ts`.

Also: a plural or punctuated title resolves the same in every consumer (slice A's tests,
unchanged and passing).

## Commits

- `dff9c2e` the code: backend, migration 0036, the evaluation case, the regenerated client, the
  web (first question, closest step, title ideas list, words), tests, stories and e2e.
- `2317e19` the review captures of the You start (`you--{1440x900,768x1024,390x844}.png`).
- `21a397d` ADRs 0015, 0007 and 0012, the runbook line, the register (last).

## Checks (on the final code)

- **`make check`** (on 21a397d): exit 0. ruff format (353 files) and lint clean; mypy clean
  (353 files); fast pytest **1721 passed**, 378 deselected; fixture validator passed; the
  generated client matches; Biome clean; `tsc` clean; Vitest **408 passed** (41 files).
- **`make acceptance`** (one guarded command under the lock, 19:16:02 to 19:31:44, on
  dff9c2e): exit 0. Backend integration and stack **395 passed** (8 m 28 s); Storybook built;
  Playwright **58 passed** (7.2 m), including the two new role-space journeys (1.7 s and
  0.8 s: the first covers four type-aheads, the pick with the world answering, the closest
  step, What we know and "None of these is my job"). No test failed, so no second run.
- **Focused integration runs** before that, under the lock: 12 files, 109 passed, 5 failed
  and 2 errors, all in my new or changed tests (listed under RED below), then the four files
  again, 18 passed.
- **Full-release timings** (`test_first_answer.py -s`, one run, under the lock): type-ahead
  18-22 ms for each acceptance title; save 22-37 ms; origin 20-24 ms; the widest partial
  type-ahead 0.233 s.
- **Design references**: `pnpm run contrast` 132/132 measurements pass (no new colour pairing:
  the type-ahead uses `--fg`, `--fg-muted`, `--selection` and `--line-control`, as the tabs and
  fields do); `pnpm run screenshots` 46/46 captures pass. One capture,
  `you--suggestions--768x1024.png`, came out different with no composition or token changed
  (rendering noise; slice A saw the same one move), so I restored it. The mirror
  `apps/web/src/design` (tokens.css and the fonts) is byte-identical (`cmp`, `diff -r`).
- **Review screenshots** (`pnpm run review-screenshots`, under the lock): 4 passed (1.6 m). It
  rewrites every capture (the moving world renders differently each run); I kept only the three
  You captures, whose start this slice changes (axe, overflow, clipping and fonts clean), and
  restored the rest. It also wrote 12 captures that were never committed (role or explore,
  saved, target chosen, what we know); I removed them, as they show places this slice doesn't
  change. The 200 % zoom check of the empty home page reports overflow (51 committed, 80 this
  run): pre-existing, a page this slice doesn't touch.
- **Words and design**: not run, requires human (session W2).

## RED then GREEN

- **Domain, the record's rules** (`tests/domain/test_targets.py`): written first; **9 failed**
  (`TypeError: decide() got an unexpected keyword argument 'qualifiers'` / `listed`), then 18
  passed after `decide` learned the ONS kind, the closest choice, `none_of_these` and
  `OTHER_FIELDS`. The migration-constants test was added with 0036 and passed.
- **The rest** (type-ahead, commands, origin, title ideas, web, e2e) was written alongside the
  code, not strictly before it. Their first runs failed on my own test mistakes, which I fixed:
  a missing directory for the reference samples (rotation test, 2 errors); "Registered nurse"
  links to the pack's crosswalk, not `none` (my expectation); a fourth target over the limit of
  three; two existing sketch expectations that the index now changes (below); and a full-release
  type-ahead returning more than one UK title for "Registered nurse". The web tests' first runs
  failed on the option's accessible name (fixed with a visually hidden comma) and on the
  YouChapter tests that met the first question (below).
- Concern: RED-before-GREEN holds for the domain rules only.

## Tests and inputs changed (disclosure)

- **The first question now leads the start**, so every test that opened a new workspace at the
  entry choice takes the person's "Skip for now" first: `YouChapter.test.tsx` (six tests; the
  purpose-line test now also checks the line leads the first question; the focus test also
  checks focus moves to how to start), `e2e/conversation.spec.ts` (four journeys; the phone
  first-screen test checks the title field, then skips and checks the entry choice;
  the sideways test checks the title field), `e2e/keyboard.spec.ts` (skips by keyboard and
  checks focus), `e2e/world.spec.ts` (two support tests), `e2e/visual.spec.ts` (the "you"
  capture now waits for the first question and its field).
- **Seeding a fresh database now needs the UK index** (ruling 4): the integration `conftest.py`
  imports the reference samples before the seed (was after); `test_master_key_rotation.py`,
  `test_receipts.py`, `test_targets.py` (seed test) and `test_migrations.py` (fresh, 0034,
  0035) import the synthetic samples before seeding or migrating; `test_reference_data.py`'s
  no-reference-data test seeds with `seed_fixture` (accounts and the fixture workspace without
  its target's record) instead of `seed`, since that database holds no index by design; its
  assertion is unchanged. `test_evaluation.py` and `test_first_answer.py` import the pinned
  index into their full-release databases (and `test_first_answer.py` now seeds after the
  taxonomy and the index, as setup does).
- **Synthetic SOC sample** (`tests/support/reference_data.py`): five unit groups and eight
  entries added (Registered nurse x2, Nurse x2, Prompt engineer, Doula, Data quality analyst, IT
  support technician), labelled synthetic; the links to 5322 stand in for the real 5321, which
  the ESCO sample lacks. The parser test's assertions are unchanged.
- **Expectations the index changes, intended**: `test_targets.py`: the sketch resolution of
  "Registered nurse" and "Data quality analyst" is `uk_title` (was `not_found`).
  `test_first_answer.py::test_a_title_esco_does_not_list_…`: "Data quality analyst" and
  "Registered nurse" are no longer partial (the index lists them); the nurses-before-nursery
  and status-word checks move to "Registered nurse (NHS)", which neither list holds and whose
  partial list is the old P04 list (same assertions); its helper's bound is now `total +
  uk_total`.
- **Fact shapes**: `TitleIdea` gained `reason`, so the fixtures in `tests/eval/test_evaluation.py`,
  `Directions.test.tsx` and `discoveryWords.test.ts` carry it; the title-idea line's expected
  words changed to the new sentence (the card's last bullet).
- **The same-slate test** (`test_every_evaluation_case_s_slate_is_the_one_before_…`) now compares
  every case recorded before Task 6d and skips cases added since (DSC-20); it asserts the
  recorded cases are all still present. Its comparison is unchanged and passes.
- `test_role_space.py`, `FirstQuestion.test.tsx`, `e2e/role-space.spec.ts` and the 0036
  migration test are new.

## Live calls

None: no Meta, Adzuna or web request, no Docker pull. Docker was already running; the test
stacks were started only by the test tooling under the lock.

## Incidents (please read)

1. **One heredoc append to a test file** (`cat >> tests/domain/test_targets.py`), against the
   Edit/Write-only rule. I restored the file from git at once and re-applied the same content
   with the Edit tool, so the committed content came through Edit; the slip happened.
2. Scripts in the scratchpad only read the pinned datasets (`var/datasets/`) to choose test
   titles; none wrote a source file. `git checkout` and `rm` were used only to restore review
   and design captures this slice's runs had rewritten or created.
3. Every lock use was `mkdir … && { …; rmdir …; }`; the lock was held by another agent once,
   and I waited.

## Not run, open, concerns

- Session W2 judges every new sentence and the start's layout (not run, requires human).
- **Making a UK title idea a target** from its list is not built (REC1-06 says so).
- **An own-words role that several ESCO occupations hold as a label** (typed "bookkeeper", then
  "Use my own words") resolves as ambiguous, as a conversation answer does, but the start
  doesn't ask "which do you mean" (the type-ahead offered each one first).
- **Targets** keep the sketch's "Closest in ESCO: Use …", which replaces the title (ruling 5).
- The record's ONS match is exact on the index's normalised title (ADR 0015 decision 2): "Registered
  nurses" is not listed, though it resolves the same in every consumer.
- 0036's SQL folds case with `lower()` where the index used Python's `casefold()`; they differ
  only for letters such as "ß", which no index title holds.
- Pre-existing: the empty home page overflows at 200 % zoom (above).
- Task 13b's worktree holds its own 0036: whichever integrates second renumbers (R15).

## Paths a reviewer can skip

`apps/web/src/generated/**` (regenerated client), `docs/reviews/sprint-2/screenshots/you--*.png`
(captures).

---

# Fix round 1

Main tree, branch `l0-local-release`, on 81c3695 (Task 13b integrated with 0037). My migration
is **0038** (`r0038_record_checks.py`, `down_revision = "0037"`). The fix list is
`task-6dB-fix-round-1.md`; every item is done. Commits: 2e05426..667426e (11 commits; the
register is the last).

## Each finding, its fix and its test

1. **Design I-1, Enter saves ESCO's first guess; an earlier search stands for new words.** No
   option is active until the person moves to one (`active = -1`); Enter with none keeps the
   typed words through `name_role`, never a partial match and never a refusal they didn't make.
   The type-ahead hook keeps no placeholder list, and the field accepts only the answer for the
   very words typed; meanwhile only "Use my own words" and "Looking for job titles…" show.
   Tests (`FirstQuestion.test.tsx`): "keeps the typed words on Enter…" (no `aria-activedescendant`,
   every option `aria-selected=false`, Enter posts `{title: "Bookkeeping assistant"}` to
   `/origin/role/title` only) and "never lets an earlier search's titles stand for new words…"
   (types "Nurse", then " specialist" with the new search held open: the UK option goes, Enter
   posts "Nurse specialist").
2. **Design I-2 with app M-5, the type-ahead's "None of these is my job" not recorded.**
   `NameRole.none_of_these` (the partial list's own-words option sends it); `name_role` stores the
   refusal as the title's record (`none_of_these`) through the one write path, with expected
   version and Idempotency-Key; the same answer again is 200 unchanged. `choose_closest` now makes
   a profile version for every answer, so a stale tab conflicts. No view asks for the closest
   occupation after it: the slate's fact for the role is `title_kept_as_own` after a refusal and
   the new `role_not_matched` otherwise (no "Choose the ESCO occupation closest to it"; that
   sentence stays for targets only, which the sketch can still give a closest occupation).
   Tests: `test_role_space.py::test_none_of_these_in_the_type_ahead_is_the_person_s_refusal_recorded_by_a_versioned_command`
   (stale 409, 201 v1, 200 again, record own_words/none_of_these; a later refusal for the same
   words is v2), `::test_none_of_these_at_the_closest_question_is_a_new_version_so_a_stale_tab_conflicts`,
   `test_discovery.py::test_after_none_of_these_the_slate_keeps_the_role_in_the_person_s_words_and_says_less`,
   `FirstQuestion.test.tsx` (body carries `none_of_these: true`), `discoveryWords.test.ts`
   (`role_not_matched` words). Acceptance 3 now holds in full: e2e second journey, plus the slate.
3. **Design I-3, the first question skips the support screen** (the controller's ruling).
   - The type-ahead screens what is typed (`has_risk_stem`): no match, nothing offered in those
     words, and `TitleMatchesOut.support_note`. `name_role` refuses a title that triggers it
     (`VALIDATION_FAILED`, `reason: support_screen`, after the access and version checks), and the
     route adds the panel to every refusal of such a title (`TitleRefusedOut`, as turns do).
     Nothing is stored. The web shows the calm panel below the question (the panel moved, unchanged,
     to `SupportNote.tsx`), which stills the world; a refused save shows the panel, not a failure;
     the person can dismiss it, type again or skip.
   - Other free text this slice added: "Use my own words" goes through `name_role` (screened);
     the closest step has no free text (buttons only). `choose_role` takes an ESCO label only; no
     ESCO occupation label in the pinned release holds a risk stem (checked: 0 hits), and the
     type-ahead offers nothing for screened words.
   - Tests: `test_role_space.py::test_the_first_question_goes_through_the_support_screen_and_keeps_nothing_of_it`
     (type-ahead panel, 422 refusals with the panel, a stale 409 with the panel, and no profile
     version, source, record or `name_role` receipt); `FirstQuestion.test.tsx` (panel, world still,
     no option, words never repeated, Enter sends nothing, dismiss returns focus; a refused save
     shows the panel and no alert); `e2e/role-space.spec.ts` "a risk phrase at the first question…"
     (demo: panel, `data-distress`, nothing kept). Inputs are existing fixtures only:
     `test_interview_choices.DISTRESS`, the web chapter tests' "I volunteer on a suicide prevention
     helpline.", and the e2e's "Some days I just want to die.".
4. **App I-1 with M-1, the role's closest occupation in two places.** `titles.current_role` reads
   the role's record (`targets.role_record`), never the role's source; every write that changes
   the role stores it (`record_role` in `commit_profile_version`): a decision replaces the
   record of that title, any other change keeps the record of its title as a concept.
   `choose_role` stores the role's record with the choice (kind `esco`). `compute_slate` takes the
   role's record like the targets'. Tests:
   `test_role_space.py::test_the_role_s_record_is_its_one_truth_so_an_edit_of_its_words_keeps_the_closest_choice`
   (closest choice, then What we know edits "Registered Nurse", "Doula" and back: state, occupation,
   `closest.chosen`, `chosen` and the usual skills agree; a same-titled target names the choice)
   and `::test_a_role_chosen_by_one_of_esco_s_other_titles_is_stored_as_an_esco_title`.
5. **App M-4, the CHECKs.** Migration 0038: `an_ons_title_has_its_codes` and
   `none_of_these_is_the_person_s_own`. Test: `::test_the_record_checks_repeat_the_role_space_rules`
   (each refuses: no SOC, no ISCO, no `recorded_by`, an ESCO kind).
6. **App M-2.** `test_reference_data.py::test_without_reference_data_the_evidence_is_unavailable_never_empty`
   now also expects 503 `REFERENCE_DATA_UNAVAILABLE` from the type-ahead, "Use my own words" and a
   role typed in What we know, and the slate's computation (`observe_discovery_offline`, the
   function every slate route uses) raising that code.
7. **App M-6 and M-7 (and M-3, from "Not now"), words only.** ADR 0015's fix round 1 line lists
   the concept-key, "&"/accent, later-index and `lower()`/`casefold()` limits; ADR 0012's lists the
   other-field rule's named fields (a policy question for the product owner) and importance edits
   on re-decided pack rows. ADR 0007 has a line for the first question's screen.
8. **App M-8.** The same-titled target in item 4's test;
   `::test_own_words_of_only_punctuation_are_kept_as_given` ("--": kept, own words, empty concept
   key); `tests/eval/test_evaluation.py::test_a_title_idea_s_reason_must_be_what_careerwright_did_with_it`
   (a wrong, an extra and a missing reason each fail as `unsupported_title`).
9. **Design M-1 (WCAG 2.2 4.1.3).** The combobox is described by the partial question; one polite
   status region holds the partial question, none found, looking, the count ("2 job titles to
   choose from.") and "Support information is shown below.". Test: `FirstQuestion.test.tsx`
   "[UI-06] describes the combobox…".
10. **Design M-2.** `SlateOut.familiarity_known` (the slate's own fact); the web says "Something
    different" only when it is true, "Directions to consider" otherwise, and the "doesn't know
    your current work yet" line only when no title is given. Tests: `Directions.test.tsx`
    "says Something different only when the API knows…", `test_discovery.py` (false after the
    refusal, true for an ESCO role).
11. **Design M-3.** Stories `StartTypeAheadUkTitle`, `StartTypeAheadPartial`,
    `StartTypeAheadNoneFound` (play functions type into the field; `StartWhichIsClosest` existed).
    Review captures `you--type-ahead-uk-title`, `-partial`, `-none-found` and `you--closest` at
    1440x900, 768x1024 and 390x844. The phone e2e (`conversation.spec.ts`, UI-12) now checks the
    closest step's "None of these is my job" and first occupation, then the kept-words line and
    "Help me explore", each wholly in the first screen and on top. The real phone keyboard: not
    run, requires human.
12. **Design M-4, first part.** "Change my job title" on the closest step goes back to the first
    question with the title in the field; a new title asks its own closest question, the same
    one goes back to it, "Skip for now" there returns to it. Tests: `YouChapter.test.tsx`
    "goes back from which is closest to the title field…", `FirstQuestion.test.tsx`.
13. **Design M-5, two parts.** Group headings are the group's name only ("A group ESCO doesn't
    name" when ESCO has none); `closest_offer` asks nothing when no group holds an ESCO
    occupation. Tests: `FirstQuestion.test.tsx` (no "ISCO" or code in the page),
    `discoveryWords.test.ts`, `test_role_space.py::test_a_title_coded_to_several_groups_…`.
14. **Design M-6.** The e2e's "no skill labels in the world" (which could not fail) is replaced in
    both journeys by `statesNoSkills`: the origin the page reads has no usual skills, no
    destinations and no occupation.
15. **Design M-8.** Only the chosen answer says "Saving…", and no second answer is sent while it
    saves; `leaving` is cleared when a save fails (first question or closest step, `onFailed`).
    Tests: `FirstQuestion.test.tsx` "says Saving… beside the chosen answer only…",
    `YouChapter.test.tsx` "never moves focus later when saving the first answer failed (N-M6)".

## Rulings I made

1. **The support panel's line for a title lives in the policy** (`safety.SUPPORT_NOTE_TITLE`),
   served whole in `SupportNoteOut` as the message panel is, not worded in `vocabulary.ts`: the
   panel's words are the support policy's (H-12) and the web's `SupportNote` renders them
   unchanged. The policy's version moves to `support-policy-8` and `REVIEW_STATUS` says the
   first question's screen and line are not yet reviewed as built. The screen's words and
   windows are unchanged.
2. **0038's refusal rule allows own words**, not only ONS titles as the fix list worded it: item
   2 records the type-ahead's refusal on a title neither list holds (`own_words`). The CHECK
   forbids it on an ESCO title and without `recorded_by`.
3. **A role saved before its record was kept** is decided as it would be stored (the role's own
   source's choice, if it cites one), as `stored_targets` does for a target; no migration.
   Consequence: a role write on a database without the UK job-title index is now refused 503, as
   a target write already was (ruling 4 of the slice).
4. **Enter in a partial list with nothing chosen keeps the words without a refusal**; only the
   "None of these is my job" option records one.
5. **The support panel is kept until dismissed** (like the message panel) and reappears only for
   a new screened answer; a screened answer offers nothing, so Enter does nothing.
6. **"Change my job title" keeps the title in the field**, so the person fixes it rather than
   retypes it.

## Tests and inputs changed (disclosure)

- `test_discovery.py` (AI-filter test): the role's fewer reason is `role_not_matched` (was
  `title_not_matched`), intended (item 2).
- `test_interview_choices.py`: the policy version literal is `support-policy-8` (was 7).
- `test_role_space.py::test_a_title_coded_to_several_groups_…`: "Data quality analyst" (group
  2421, empty in the ESCO sample) now has no closest question and `choose_closest` is refused
  `not_offered` (was asked, with an empty group), intended (item 13).
- `FirstQuestion.test.tsx`: the ESCO keyboard test presses Down then Enter (it pressed Down then
  Up while the first option started active); the partial "None of these" test expects
  `none_of_these: true`; region names lose "(ISCO-08 …)"; fixtures carry `support_note: null`.
- `discoveryWords.test.ts`: group headings in plain words; new words tests.
- `e2e/role-space.spec.ts`: the group region is found by "Nursing professionals"; the skill-label
  count is replaced (item 14).
- Slate fixtures carry `familiarity_known` (`YouChapter.test.tsx` false, the stories true).
- My own new test expectation corrected before commit: "Bookkeeping assistant" is a pack target,
  so its record links to the pack's crosswalk, not `none`.

## RED then GREEN

- Item 4: both new tests failed (`not_in_esco` after the capitals edit; kind `ons` for an ESCO
  other title), then passed with 8 others.
- Item 2: the type-ahead refusal test failed (422: `none_of_these` not accepted) and the closest
  test failed (version 1, no new version), then passed.
- Item 3 backend: `KeyError: 'support_note'`, then 32 passed (role space, interview choices,
  taxonomy). Web: both support tests failed, then passed.
- Items 1 and 9 (web): the three tests failed, then passed.
- Item 13 backend: with the fix removed for one run, the several-groups test failed (the empty
  offer accepted an answer, so the next save was stale); restored, it passed.
- Items 12, 13 (web), 15: six tests failed; the focus test's first failure was on my wrong
  assertion (the stale notice is not an alert), so I removed the `onFailed` wiring for one run to
  see it fail on `not.toHaveFocus()`, then restored it.
- Item 5: `DID NOT RAISE CheckViolation`, then passed with 0038.
- Items 6, 8 and 14 are coverage of behaviour that existed (or of a check), so they passed first.
- Item 10: the web test failed ("Something different" shown), then passed.

## Checks (on the final code, 30c1606; the register commit after it is docs only)

- **`make check`**: exit 0. ruff format (364 files) and lint clean; mypy clean (364 files);
  fast pytest **1751 passed**, 407 deselected; fixture validator passed; the generated client
  matches; Biome clean (150 files); `tsc` clean; Vitest **420 passed** (41 files).
- **`make acceptance`**: one guarded command under the lock, 21:10:29 to 21:27:00, exit 0.
  Backend integration and stack **424 passed** (9 m 25 s); Storybook built; Playwright **59
  passed** (7.0 m). No test failed, so no second run.
- **Focused runs while fixing**, each under the lock: the role-space, discovery, origin,
  targets, reference-data, capability, profile, slate-explanation, interview, evaluation,
  first-answer, taxonomy and migration files (all passing at the end), and four e2e journeys
  (the phone first screen, both role-space journeys, the support journey: 4 passed).
- **Design references**: `pnpm run contrast` 132/132 pass (no new colour pairing);
  `pnpm run screenshots` 46/46 pass. `you--suggestions--768x1024.png` came out different with no
  composition or token changed (the same rendering noise slice A and B saw), so I restored it.
  The mirror `apps/web/src/design` is unchanged and its files are byte-identical to
  `docs/design` (`diff -rq`: only the unmirrored `contrast-pairs.json`, `contrast-report.md` and
  the fonts README differ, as before).
- **Review captures** (`pnpm run review-screenshots`, under the lock): the first run failed on
  my new shots' ready check (it expected "Answers saved"; a new workspace says "Nothing saved
  yet"); fixed, the second run passed (4 passed, 1.8 m). I kept the twelve new captures
  (`you--type-ahead-uk-title`, `-partial`, `-none-found` and `you--closest` at 1440x900,
  768x1024 and 390x844; axe, overflow, clipping, overprinting, console errors and fonts clean for
  each) and restored the rest, which only rendering noise changed, and the checks files (they
  come from an older run that lists a different set of captures). I removed the twelve captures
  the run writes that were never committed (role or explore, saved, target chosen, what we know).
- **Human checks**: the words and layout (session W2), the real phone keyboard over the options,
  VoiceOver and Safari: not run, requires human.

## Not run, open, concerns

- **Policy question for the product owner (R14):** should What we know's direct entries (the
  role and target fields) go through the support screen too? Not changed here.
- The panel's new line and the first question's screen are not yet reviewed as built
  (`support-policy-8`, `REVIEW_STATUS`); the policy's words and windows are unchanged.
- A title that the screen answers as an accepted false positive ("suicide prevention worker")
  can't be named at the first question; the person can skip and name it in What we know.
- An ambiguous own-words role still has no "which do you mean" in the start (Design M-4's second
  part: the final review's).
- Design M-5's third part, M-7 and M-9: questions for session W2 (not touched).

## Live calls

None: no Meta, Adzuna or web request, no Docker pull. Docker was already running; test stacks
were started only by the test tooling, every time under the lock (`mkdir … && { …; rmdir …; }`).

## Incidents

- Every source change went through Edit or Write (formatters and the client generator aside).
  Commit messages were passed to `git commit -F -` from a heredoc; no file was written that way.
  One stray empty `python3 - <<'EOF'` with no body ran while I checked import lines: it wrote
  nothing.
- `git checkout` and `rm` were used only on captures this round's runs rewrote or created.

## Paths a reviewer can skip (fix round 1)

`apps/web/src/generated/**` (regenerated client), the twelve new
`docs/reviews/sprint-2/screenshots/you--type-ahead-*` and `you--closest--*` captures.

---

# Fix round 2

Main tree, branch `l0-local-release`, on FIX_BASE 667426e. The fix list is
`task-6dB-fix-round-2.md`; items 1 to 9 are done. No migration. Policy version
`support-policy-9`. Commits: aa0e66e..51ca593 (7 commits; the register is the last); see
"Commits" below.

## Each finding, its fix and its test

1. **Design R-I1, the title field's support panel below the field.** The panel now renders as
   the first child of the title field's block, directly above the field (as the message panel
   sits above the reply field), and the polite status says "Support information is shown
   above the job title field." Tests: `FirstQuestion.test.tsx` "shows the panel above the title
   field, where a phone's keyboard can't cover it" (document order + status words);
   `e2e/role-space.spec.ts` "phone › at 390 × 844 the title field's support panel is above the
   field, its heading in view while the field has focus" (bounding boxes: panel bottom ≤ field
   top; heading inside 0..844; the field focused). Layout only; the real keyboard is human.
2. **Design R-I2, "None of these is my job" below a phone's first screen.** The person's own
   words are now the **first** option in every list: "Use my own words" over a list of titles,
   "None of these is my job / Use my own words: “…”" right under the partial question. Tests:
   `FirstQuestion.test.tsx` (own words first; the partial's own option is the first option);
   the UI-12 phone e2e (`e2e/conversation.spec.ts`) now types "Registered nurse" and
   "Bookkeeping assistant" at 390 × 844 and checks "Use my own words: “Registered nurse”" (after
   the UK title has loaded) and "None of these is my job" (after the partial question shows)
   are wholly in the first screen and on top.
3. **R-M3, a real job title that trips the screen (the controller's ruling).**
   - API: `NameRole.keep_as_typed` (default false). `name_role` refuses a screened title
     unless it is set; with it, the title is saved exactly as typed through the same command and
     resolve path as "Use my own words" (a direct-entry source, its record by
     `resolve_target`). The route still adds the panel to every refusal of a screened title.
   - Words (`safety.SUPPORT_NOTE_TITLE`, policy words, not yet reviewed as built): "If anything
     you typed is about how you are feeling, support is available any time, from people
     trained to help. Careerwright keeps it as your job title only if you choose to. You can
     also type again or skip this question." (was "… Careerwright hasn't kept it as your
     role."; see ruling 1).
   - Web: the panel carries "Keep it as my job title" while the words the screen answered are
     in the field (from the type-ahead or a refused save); once the panel is dismissed, the
     same button stays under the field, so the way forward never leaves with the panel.
   - Tests: `test_role_space.py::test_a_title_the_support_screen_answers_is_kept_only_by_the_person_s_explicit_choice`
     (refused 422 with the panel; a stale keep 409 with the panel; kept 201 v1 exactly as typed;
     again 200; origin own words; one source, `direct_entry`, "Direct entry"; no response or
     receipt holds a support note); `FirstQuestion.test.tsx` "keeps the typed words as the job
     title only when the person chooses to" (nothing posted by itself; no button for other
     words; the POST body `{expected_version, title, keep_as_typed: true}`), "still offers the
     choice under the field once the panel is dismissed", "says why when keeping the words was
     refused for another reason", and the refused-save test now also keeps by choice;
     `e2e/role-space.spec.ts` checks the button is offered (not pressed). Inputs: the existing
     fixtures only (backend: `test_interview_choices.py`'s "I volunteer on a suicide prevention
     helpline and want paid work like it."; web: "I volunteer on a suicide prevention
     helpline."; e2e: "Some days I just want to die.").
4. **The product owner's decision: What we know's direct entries go through the screen.**
   - API: `PUT /profile` answers `ProfileSavedOut` (`ProfileOut` + `support_note`) and refuses
     with `ProfileRefusedOut` (envelope + `support_note`). Before anything can refuse it, the
     route reads the edit's new entries (`commands.entered_words`: each answer in words and each
     list item that the version the edit was made against doesn't hold; every one when that
     version can't be read) and screens them with `has_risk_stem`. The panel is derived from
     the request every time (a replay too) and is never stored: the receipt keeps the profile.
   - Policy: `support-policy-9`, `REVIEW_STATUS` names both new screens as not yet reviewed as
     built, new lines `SUPPORT_NOTE_ENTRY` ("… Your answers were saved as usual.") and
     `SUPPORT_NOTE_ENTRY_NOT_SAVED` ("… Your answers were not saved; the reason is shown with
     them."); ADR 0007 amendment line (fix round 2).
   - Web: What we know shows the panel above Save changes, stills the world, and announces
     "Saved. Support information is shown above Save changes."; like a message's, it stays until
     dismissed or the next save; Dismiss returns focus to Save changes. The profile cache never
     holds the note (`useSaveProfile` strips it).
   - Tests: `test_workspaces_and_profiles.py::test_a_direct_entry_with_a_risk_word_is_saved_with_the_calm_panel_and_nothing_of_it_kept`
     (saved 201 as entered with the panel; a replay with the same key the same panel; the same
     words again beside another change, no panel; a stale save 409 with the not-saved panel; the
     two receipts hold no support note); `ProfileEditor.test.tsx` (panel, world still, status
     words, above Save changes, Dismiss focus, world moves again; a refused save's panel beside
     the stale notice). Inputs: `DISTRESS` (the existing backend fixture) and the web fixture.
   - Two panels can now show at once (the title panel outlives the first question, R-M2), so
     the shell counts panels (`useSupportPanels`): the world stays still until the last goes.
     Test: `src/lib/world/settings.test.tsx`.
5. **The screened type-ahead response returned the typed words.** `TitleMatchesOut.query` is
   now `str | null`; null when the screen answered. Test: the role-space support test asserts
   `query is None` and the fixture's text appears nowhere in the response.
6. **R-M1, the arrowed option as an index.** It is kept by its key (`activeKey`); the own
   option under a partial list has its own key, so own words arrowed to never become a refusal.
   Tests: `FirstQuestion.test.tsx` "keeps the option arrowed to by its key, so Enter never picks
   a title that moved under it" and "never turns the arrowed own words into a refusal when a
   partial list arrives" (a type-ahead held open, Down, then the answer arrives, then Enter).
7. **R-M2, the panel taken away undismissed.** The conversation holds the title panel; the
   first question shows it above its field, the start's later steps after their content, and
   once the start is done it sits where the message panel does, above the reply field. Tests:
   `YouChapter.test.tsx` "keeps the first question's support panel until the person dismisses
   it, after another title or a skip" (another title saved, then the entry chosen: still shown,
   above the reply field; Dismiss focuses the reply field) and "… after Skip for now, until
   dismissed" (no keep button once no title is in a field; Dismiss focuses the step's heading).
8. **R-M4, "Skip for now" while fixing a title.** It reads "Back to “Which of these is
   closest?”". Test: `YouChapter.test.tsx` "while fixing a title, names the way back to which
   is closest for what it does"; `discoveryWords.test.ts` pins the words.
9. **App N-M2, the conversation's change of the role.** Test:
   `test_origin.py::test_the_conversation_s_change_of_the_role_keeps_the_role_s_record` (demo
   workspace; "Registered nurse", closest "specialist nurse", then the demo interviewer's
   proposal from "I am a Registered Nurse." decided: version 3, the role "Registered Nurse",
   state `esco`, chosen, kind `ons`, the chosen occupation and usual skills).

## Rulings I made

1. **The title line says what holds whichever way the person goes.** The panel now stays until
   dismissed (R-M2), also after the person keeps the title; "Careerwright hasn't kept it" would
   then be false. "Careerwright keeps it as your job title only if you choose to" stays true.
   Policy words, not yet reviewed as built.
2. **The keep choice lives in the panel, and under the field after a dismissal,** only while the
   words the screen answered are in the field. No second skip button in the panel: its line
   names skipping, and Skip for now is just below.
3. **Only the screen's own refusal is silent.** A refusal of a screened title for another reason
   (stale, unavailable) now shows its notice beside the panel (round 1 hid every refusal that
   carried the panel). Otherwise a stale "Keep it" would fail with nothing said.
4. **What we know screens the edit's new entries only,** compared with the version it was made
   against (immutable, so a replay reads the same), so a word saved before doesn't bring the
   panel back on every later save. Undo (revert) restores earlier answers and is not a direct
   entry: not screened. Numbers and money are not words.
5. **What we know's panel sits above Save changes** and follows the message panel's life (until
   dismissed or the next save), so a stale "not saved" line never outlives a later save.
6. **The world counts panels** (needed now that two can show).
7. **The person's own words come first in every list,** not only the partial one (the fix list
   names both).

## Tests and inputs changed (disclosure)

- `test_role_space.py` support test: two new assertions (`query is None`; the text appears
  nowhere). New test (item 3) with the `HELPLINE` constant, a copy of
  `test_interview_choices.py`'s existing input.
- `test_interview_choices.py`: the version literal is `support-policy-9` (was 8), comment
  updated. Intended.
- `FirstQuestion.test.tsx`: every render goes through a `Held` harness, which holds the panel as
  the start does (the panel is no longer inside the component); the `titlePanel` fixture's
  version and message follow the policy; "own words … last option" is now first; the ESCO
  keyboard test presses Down (own words) then Down (the title), was Up then Down; the partial
  test also checks None of these is the first option; the support test's panel words follow
  the policy and its status check moved to the new placement test; the refused-save test also
  keeps by choice; six new tests.
- `YouChapter.test.tsx`: a `titlePanel` fixture; three new tests.
- `ProfileEditor.test.tsx`: `renderEditor` takes an optional support report and wraps the
  editor in its provider; an `entryPanel` fixture; two new tests.
- `discoveryWords.test.ts`: `supportShown` is "Support information is shown above the job title
  field." (was "… shown below."), intended (R-I1); a new words test.
- `e2e/role-space.spec.ts`: the panel words follow the policy (was "Careerwright hasn't kept it
  as your role."); a new check that the keep button is offered; a new phone test.
- `e2e/conversation.spec.ts` UI-12: extended to the type-ahead's two lists (the field is
  cleared before the existing skip).
- `e2e/visual.spec.ts`: two new shots (`you--title-support`, `you--what-we-know-support`, the
  latter's save answered in the test from the profile the page read).
- New: `src/lib/world/settings.test.tsx`, `test_origin.py`'s and `test_workspaces_and_profiles.py`'s
  new tests.

## RED then GREEN

- Item 5: the support test failed on `query is None` (the response carried the fixture's
  words), then passed (5 type-ahead and support tests).
- Items 3 and 4 (backend): both new tests failed (`KeyError: 'support_note'`: the keep flag was
  refused as an unknown field; the profile write had no panel), then 30 passed (role space and
  profiles).
- Web items 1, 2, 3, 6: 10 FirstQuestion tests failed (own words last, the arrowed index picked
  ESCO's title, no panel above the field, no keep button), then 19 passed. The dismissal test
  (self-review addition) failed (no button), then passed.
- Items 7 and 8: written with the fix in place, so I removed each fix for one run (the label
  always "Skip for now"; the panel not rendered outside the first question): the three tests
  failed (a "Skip for now" button found; no panel region), then I restored the code and all 43
  passed.
- Item 4 web: both ProfileEditor tests failed (no panel region), then 11 passed.
- The panel count: the test failed against a one-flag version (the world moved after the first
  dismissal), then passed with the count.
- The two phone e2e checks: with the two layout fixes undone for one run (own words last; the
  panel drawn after the field with `order: 99`), the e2e run failed exactly those two (panel
  bottom 1099.5 > field top 515.5; "Use my own words" bottom 936 > 844; `.last-run.json` lists
  2 failed). The other tests of that run passed (its output was cut by my pipe, so I can't give
  the count). Restored, the focused run passed: 12 passed (1.8 m): the support, phone,
  role-space and world journeys.
- Item 9 is coverage of behaviour that existed, so it passed first; to show it can fail, I made
  `record_role` re-decide every role change for one run: it failed (`not_in_esco` != `esco`),
  then I restored the code (no diff left).

## Commits

- aa0e66e The screened type-ahead answer returns no typed words (item 5).
- 64c958e support-policy-9: What we know's direct entries screened; a screened title kept by
  the person's choice; the title panel above the field and kept until dismissed; the person's
  own answer first; the arrowed option by key; the way back while fixing (items 1-4, 6-8, and
  the panel count). One commit: `safety.py`, `FirstQuestion.tsx` and the generated client each
  hold several items, and I can't stage parts of a file here.
- adc3080 The conversation's change of the role keeps its record (item 9, test only).
- 4590743 Review shots for the title panel and What we know's panel (`visual.spec.ts`).
- 4bac1c6 ADRs 0007 and 0015, fix round 2's lines.
- 071ea61 Review captures.
- 51ca593 The register (PROF-09, DIV1-13, DIV1-14, PROF-10, UI-12, WLD-08).

## Checks (on the final code, 4bac1c6; the commits after it are captures and the register)

- **`make check`**: exit 0. ruff format (364 files already formatted) and lint clean; mypy
  clean (364 files); fast pytest **1751 passed**, 410 deselected; fixture validator passed; the
  generated client matches; Biome clean (151 files); `tsc` clean; Vitest **433 passed** (42
  files). No warnings in its output.
- **`make acceptance`**: one guarded command under the lock, exit 0. Backend integration and
  stack **427 passed** (9 m 41 s); Storybook built; Playwright **60 passed** (7.2 m). Wall clock
  22:59:48 to 01:21:53 (the image builds and the two suites; I did not time the parts). No test
  failed, so no second run.
- **Focused runs while fixing**, each under the lock: the role-space and profile integration
  files (30 passed), the type-ahead and support tests (5 passed), item 9's test (1 passed, and
  the one-run failure above), the e2e RED run and the GREEN run (12 passed).
- **Review captures** (`pnpm run review-screenshots`, under the lock): 4 passed (1.8 m), every
  capture's checks clean (fonts, overflow, clipping, overprinting, axe, console errors; 39 shots
  at each viewport). I kept the six new captures (`you--title-support`,
  `you--what-we-know-support`, each at 1440x900, 768x1024 and 390x844), the type-ahead lists
  (`you--type-ahead-uk-title`, `-partial`: own answer first) and `you--support-note` (its button
  row's markup changed). I restored every other capture this run rewrote (rendering noise; this
  round changed nothing they show) and the four `checks-*.json` files, as round 1 did, and
  removed the twelve captures the run writes that were never committed (role or explore, saved,
  target chosen, what we know).
- **Design references**: no reference place changed, so not run (the fix list asks for them
  only then). `docs/design` and its mirror are untouched.
- **Human checks**: the panels' words (session W2), a real phone's keyboard over the title
  field and its panel, VoiceOver and Safari: not run, requires human.

## Not run, open, concerns

- **A phone's first screen with the title panel open.** The panel is tall at 390 × 844 (its
  four services wrap), so above the field it pushes the field and "Keep it as my job title" below
  the first screen (`you--title-support--390x844.png`); its heading and words are in view as it
  appears, which is what R-I1 asked. With a real keyboard the browser keeps the focused field in
  view, so the panel's lower part sits just above it. Not run on a phone: requires human. If the
  design review wants the field and the choice in the first screen too, a shorter panel there
  (the services one tap away) is a policy-words decision.
- **Typed edits in the conversation's review tray** (a turn decision's `edits`) are words the
  person types too, and are not screened: the decision named What we know's direct entries.
  A question for the product owner, with the policy's review.
- Undo (revert) restores earlier answers and is not screened (ruling 4).
- A request the API refuses before the route runs (FastAPI's own 422 for a malformed body, such
  as a title over 120 characters) carries no panel, as for messages; the web's fields stop at
  120 characters.
- Both new uses of the screen and their lines are not yet reviewed as built (`REVIEW_STATUS`,
  `support-policy-9`).
- Not now (the controller's): app new Minor 1 (an older ESCO-chosen role overridable by another
  record of the same title), untouched.

## Live calls

None: no Meta, Adzuna or web request, no Docker pull. Docker was already running; test stacks
were started only by the test tooling, every time under the lock (`mkdir … && { …; rmdir …; }`).

## Incidents

- My first e2e command passed `-- … -g "390"` through `pnpm run e2e`, so Playwright ran the whole
  suite (under the lock, with the RED edits in place, as intended for the two phone checks); its
  output was cut at 30 lines by my `head`, so only `.last-run.json` (2 failed: the two new
  checks) and the failure files give its result. The GREEN run used `pnpm exec playwright test
  … -g`.
- Temporary edits made to show RED were made and undone with the Edit tool (a literal
  `"RED"` comparison in `Conversation.tsx`; `order: 99` and the old option order in
  `FirstQuestion.tsx`; a disabled early return in `targets.py`). None is in any commit; the
  final diff of each file was checked.
- Every source change went through Edit or Write (formatters and the client generator aside).
  Commit messages were passed to `git commit -F -` from a heredoc; no file was written that way.
- `git checkout` and `rm` were used only on captures this round's run rewrote or created.

## Paths a reviewer can skip (fix round 2)

`apps/web/src/generated/**` (regenerated client) and the fifteen captures in 071ea61.

