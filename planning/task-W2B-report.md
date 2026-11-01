# Task W2, slice W2B report: the deterministic sources

Branch `l0-local-release`, from HEAD `c84729e`. Implementer: Claude (Opus 5.5). No subagents,
no live model call, no web request, no headed browser, `spikes/world` untouched,
`answers-2.md` not staged.

## Status

DONE_WITH_CONCERNS (concerns at the end: P01's slate still rests on work-style words; P04
and P05 now show no suggestions; provisional rules need the product owner; one known
intermittent worker-shutdown hang failed once in acceptance and passed on re-run).
Commit: `f70f88d`.

## The seven deliverables

1. **The first question's type-ahead.** `GET /v1/taxonomy/titles?q=&limit=` (operation
   `match_titles`; `careerwright.catalogue.taxonomy.match_titles`,
   `taxonomy_store.title_matches`). Matches ESCO's preferred and alternative labels (never
   hidden ones): each word typed must begin a word of the label (`'word':*` on a `simple`
   tsvector, migration 0031's GIN index `occupation_labels_words`). One entry per
   occupation, by its best label; order: the label is what was typed, then begins with it,
   then a preferred label, then the shorter label. Returns the occupation's ESCO title, the
   label that matched, its ISCO-08 unit group and `total` (every occupation that matched).
   No match is `matches: []`, `total: 0` with 200 (honest empty, never invented); a query
   with no letter or digit is `422 VALIDATION_FAILED`, reason `no_search_terms`. No model,
   no key, no workspace: works before a key and in the demo.
2. **The first answer, recorded.** `POST /v1/workspaces/{id}/origin/role`
   (`choose_role`; `exploration.choose_role`), body `{expected_version, concept_id}`,
   `Idempotency-Key`, through `run_idempotent` and `commit_profile_version`. It uses the
   existing field `current_role` (no new field, no profile schema change): its value becomes
   the occupation's ESCO title, citing an `occupation_choice` source whose locator is the
   ESCO URI (an existing source kind; its label is "Chosen from the ESCO occupations as your
   current or last role"). 201 changed, 200 already the role, stale refused. One small change
   to the one write path: `commit_profile_version(..., recite=...)` lets a field cite a new
   source when its words are unchanged, so choosing the occupation for words the person had
   already typed (an ESCO title several occupations share) records the choice instead of
   leaving the role ambiguous.
3. **"Usual in your role, not confirmed yet".** `GET /v1/workspaces/{id}/origin`
   (`get_origin`) serves `usual_skills`: the essential skills of the occupation the role
   names (only when it names exactly one), each `usual_in_role` or `self_reported`
   (`careerwright.capability.usual`), with the person's latest answer and its record. Display
   only: nothing computed reads it. "I've used this" is the existing capability evidence
   command, `POST .../capability/evidence` with `subject: "esco:<skill ID>"` and
   `answer: "used"`, a new sixth answer (ADR 0012 amendment): a self-report with no level
   (migration 0031 constraint), read as self-reported, `unsupported`, level unknown, so it
   counts for nothing towards readiness and the row is still asked for its level. The
   command now also accepts the role's essential skills as subjects; with no rubric there,
   a level is refused (`level_without_rubric`). No parallel store.
4. **The slate joined by shared essential skills.** `careerwright.profile.titles` resolves
   the person's own titles (role, targets) to ESCO occupations (chosen, else by label;
   never guessed); `slate.skill_join_hits` joins work to them (at least 3 shared essential
   skills, ranked by Jaccard over the best, best 30; channel `shared_skills`, query `j1`);
   `compute_slate` never searches a title's words (a model or fixture search whose text is
   one of the person's titles is answered by the same join under its own channel), lists
   titles ESCO does not hold (`SlateOut.unmatched_titles`, plus a fewer-reason), and task
   and work-style searches rank skills and descriptions only (label weights 0;
   `taxonomy_store.full_text(..., titles=False)`; the public search is unchanged). ADR 0007
   decision 13. The first scatter (`GET .../origin` `destinations`) is the role's join alone
   through the same slate rules and the confirmed salary floor; the role is the origin,
   never a destination.
5. **The unexpected connection.** `slate.unexpected_connection`, served as
   `SlateOut.connection` and `OriginOut.connection` (`ConnectionOut`: sentence, the shared
   skills, their count, "These are the skills ESCO lists for both roles. They aren't
   compared with your own experience yet."). ADR 0007 decision 14 (rule and why below).
6. **The overlooked strength.** New run kind `strength_proposal` (`RunKind`, migration
   0031): contract `careerwright.capability.strength` (prompt `overlooked-strength-1`,
   strict schema, `check_strength`, bounds, worst case), task
   `capability.strength_agent.STRENGTH_PROPOSAL_TASK` composed in `worker.py`, fixture model
   `careerwright-fixture-strength-1` (demo only, `FIXTURE_MODELS`, registry), use cases
   `capability.strengths`. Endpoints: `POST .../interview/turns/{turn_id}/strength`
   (`submit_strength`, 202 started or 200 already asked; the answer never holds the
   proposal), `GET .../interview/turns/{turn_id}/strength` (`get_strength`: run, `found`,
   proposal, decision), `POST .../interview/turns/{turn_id}/strength/decision`
   (`decide_strength`: `{expected_version (capability), confirm}`, Idempotency-Key; once).
   Tables `strength_proposals` (one per turn, `UNIQUE turn_id`) and `strength_decisions`
   (one per strength; a confirmation names its evidence, a decline none). It runs on the one
   model-run workflow as its own run: the DBOS step sequence and `careerwright-l0-1` are
   unchanged. ADR 0014 decision 3 records it.
7. **Within one second, measured.** `tests/integration/test_first_answer.py` runs the real
   API against real PostgreSQL 16 (the test stack's container, this machine: an M4 MacBook
   Pro) with the full pinned ESCO v1.2.1 imported: type-ahead for "d", "da", "data",
   "data an", "data analyst" 87, 16, 10, 10, 11 ms; the first answer saved 19 ms; the
   world's response (`GET .../origin`: 36 usual skills, six destinations, the connection)
   24 ms (25 ms again). The test asserts every type-ahead under 1 s and save plus response
   under 1 s. In-process TestClient, so no browser or network hop is included.

## "data analyst" and the five personas, before and after

Full pinned release, offline evaluation path (fixture proposer, each answer a query).
Numbers in brackets: essential skills shared with the data analyst.

| Case | Before (HEAD c84729e) | After |
|---|---|---|
| "data analyst" (current role) | call centre analyst (1), data analyst (36), data entry clerk (5), chief data officer (7), data protection officer (2), material stress analyst (1) | data scientist (22), chief data officer (7), big data archive librarian (7), data quality specialist (12), data entry clerk (5), knowledge engineer (7); connection: "A data analyst and a chief data officer share 7 essential skills." |
| P01 (target "Data quality analyst", not an ESCO title; tasks; work style "structured", "collaborative") | call centre analyst, data analyst, branch manager, structural ironworker, bridge inspector, water quality analyst | ICT information and knowledge manager, house builder, online community manager, bridge inspector, branch manager, chief operating officer; the target listed as not an ESCO title |
| P02 (tasks and work style only) | art restorer, fruit and vegetable picker, vineyard supervisor, fisheries observer, pesticides sprayer, street sweeper | the same less art restorer, plus consultant social worker |
| P03 (target "IT support technician" = ESCO's ICT help desk agent) | ICT help desk agent, after-sales service technician, refurbishing technician, production plant crane operator, aquaculture cage technician, solar energy technician | ICT help desk agent, after-sales service technician, call centre agent, ICT help desk manager, customer service representative, specialised seller (all joined by shared skills) |
| P04 (target "Registered nurse", not an ESCO title) | specialist nurse, nurse assistant, veterinary nurse, nursing lecturer, auxiliary nursing and midwifery vocational teacher, advanced nurse practitioner | none, with "“Registered nurse” isn't a title ESCO lists, so Careerwright can't join other work to it by shared skills. Choose the ESCO occupation closest to it." |
| P05 (target "Bookkeeping assistant", not an ESCO title) | sales support assistant, assistant lecturer, physiotherapy assistant, shop assistant, parliamentary assistant, editorial assistant | none, with the same sentence for "Bookkeeping assistant" |

Where it matched on words, and the fix: the role and every target title were searched as
text (all words, then any word at half weight), and the demo proposer searched them again;
"analyst", "assistant", "technician" and "nurse" in titles carried the slate. Work-style
words matched titles too ("structured" found the structural ironworker). Now titles join
only by shared essential skills, and task searches ignore title words. Pinned as evaluation
cases DSC-10 (data analyst), DSC-11 (P04), DSC-12 (P01), DSC-13 (P03), DSC-14 (P05), with
new checks `joined_by_skills`, `connection` and `titles_unmatched`; DSC-01 is P02.

## The unexpected-connection rule

Of the slate's suggestions that the role's skill join found, outside the role's own kind of
work (ISCO-08 minor group) and never a title the person named: the one sharing the most
essential skills with the role; ties to the larger share of both roles' skills (Jaccard),
then slate order. None qualifies: no connection. Why: the plan defines it as "a destination
the person never named ... joined to their own role by the essential skills the two
share", so another kind of work and never a named title; the most shared skills makes it
the most substantial fact the slate holds, which is exactly what its sentence states. The
sentence is built from computed facts only ("A data analyst and a chief data officer share
7 essential skills."), about two roles, never about the person, with the skills one step
away. Recorded in ADR 0007 decision 14.

## Rulings I made

1. **Titles resolve, never search.** A title ESCO does not list joins nothing (no word
   search, no nearest guess); the slate lists it and asks for the closest ESCO title. This
   empties P04's and P05's slates, deliberately: honest emptiness over keyword matches.
2. **Task and work-style searches drop title words** (label weights 0). Otherwise "structured"
   kept finding work by its title. Known limit: hidden labels share the skills part of the
   vector and still count.
3. **Join measure:** at least 3 shared essential skills, Jaccard over the best, best 30;
   provisional (R6). The decision 5 relative floor then applies unchanged (the statistician,
   7 shared of its 50, falls below it for "data analyst").
4. **The role's own occupation** stays a close candidate of a discovery (unchanged
   behaviour) but is never a destination in the first slate (it is the origin).
5. **The first answer uses `current_role`** with an `occupation_choice` source, no new
   field; `chosen_occupation_uris` now also returns the role's choice (its consumers key by
   title, and ESCO preferred labels are unique, so a target with the role's title resolves
   to the same occupation).
6. **`recite`** on the one write path (deliverable 2): without it, choosing an occupation
   for unchanged words recorded nothing and an ambiguous role could never be resolved.
7. **"I've used this" is a sixth capability answer, `used`**, level-free and self-reported,
   rather than "done independently" with no level (that would claim independence the person
   never stated). It counts for nothing towards readiness and changes a claimed row's
   question reason to `unsupported_claim` (still asked for its level).
8. **The strength's trigger:** the client asks after a turn's decision; the server refuses
   unless that decision changed what the person enjoys, can do or has done
   (`no_new_answers`), the turn's message passed the support screen (`held_back`, recomputed,
   nothing stored), and those answers are still current. Codes reused:
   `INSUFFICIENT_EVIDENCE` with reasons `no_new_answers`, `held_back`, `no_quotable_answer`,
   `no_destinations`; `STALE_INPUT_VERSION`; `LIMIT_EXCEEDED` `answers_too_long`;
   `ALREADY_DECIDED`; `PROPOSAL_NOT_AVAILABLE`. No new error code.
9. **What a strength may quote:** only enjoyed, confident and evidenced tasks (never a title,
   a name, a place or money); the model writes no prose, only refs and a quotation, so the
   only checks needed are the destination, the skill's listing and the span.
10. **Destinations of a strength:** the targets that name one ESCO occupation, then the
    first slate's destinations, each with the essential skills not yet claimed (latest
    answer used or done); skills cut 24/16/10/6/3 per destination to fit 9,000 bytes.
11. **Declining** records only the decision row (no evidence, no capability version
    change); it still checks the capability version shown.
12. **The demo's scripted example** is a fixture model (like the other demo stand-ins): the
    first quotable answer sharing a content word with a destination's essential skill,
    quoted whole, labelled "Demo example (synthetic)"; none when nothing shares a word.

## Checks run

- TDD: `tests/domain/test_skill_joins.py` written first (RED: `ImportError` on
  `MIN_SHARED_SKILLS`), then `slate.py` (GREEN, 7 tests). `test_strength.py` and the
  `used` readiness test written beside their code.
- `make check` on the committed tree (`f70f88d`), exit 0: ruff format and lint clean, mypy
  clean (322 files), pytest 1,532 passed / 308 deselected, fixture validator passed; web:
  client matches the OpenAPI document, Biome clean, `tsc` clean, Vitest 299 passed.
- Focused integration runs (real PostgreSQL 16, DBOS, workers, the fake provider):
  `tests/integration/test_origin.py` 7 passed; `test_first_answer.py` 1 passed (timings
  above); `test_discovery.py` + `test_evaluation.py` 17 passed (all DSC cases on the full
  release); `test_slate_explanations.py`, `test_capability.py`, `test_migrations.py` passed.
- `make acceptance`: see "Acceptance" below.
- Before and after slates: a scratch integration test (not committed, deleted) printed the
  six slates over the full release at HEAD `c84729e` and again after the change.

## Acceptance

Commit `f70f88d` (one commit for the slice: migration 0031's run kind, the code naming it
and the regenerated client must land together).

- `make acceptance`, first run (before the last fix): pytest `-m "integration or stack"`
  1 failed, 307 passed. The failure was mine: the parametrised constraint name in
  `test_interview_turns.py::test_the_database_keeps_the_fixture_interviewer_...`; migration
  0031 renamed `the_fixture_models_only_interview_discover_or_explain` to
  `the_fixture_models_only_profile_runs` (it now also admits strength proposals). Fixed in
  the test (the constraint name is a schema detail, not a contract).
- `make acceptance`, second run, on the final tree: pytest 307 passed, 1 failed:
  `test_durable_runs.py::test_a_crash_after_acceptance_never_calls_the_model_again_and_keeps_the_usage`
  with `WorkerShutdownTimeoutError` ("worker ignored SIGTERM for 20.0s"): the second worker
  had finished its run (`reused_accepted`) and then hung in shutdown, the intermittent
  DBOS shutdown hang Task 1 recorded (`task-1-report.md`: `DBOS.destroy()` blocking). It
  passed in the first run, and passed again on the final tree in isolation with its two
  crash siblings (`3 passed in 21.80s`). Make stopped there, so:
- the acceptance's web half, run separately on the final tree:
  `pnpm run build-storybook && pnpm run e2e`: Storybook built; Playwright 42 passed
  (5.7 min), including the conversation journey (explore, slate, written note, choose a
  target, sketch) on the stack's full release.

So every acceptance check passed on the final tree except one pre-existing intermittent
shutdown hang, which passed on re-run. Not claimed: a single clean `make acceptance` pass in
one invocation.

## Live calls

None. Cost $0. Tests use the fake provider (`tests/support/fake_models.py`, extended with a
strength answer and an "I enjoy" interview proposal) and the fixture models.

## Not run / blocked

- No live strength run on the test or production model (R5; not asked).
- Interface work is W2C's: nothing in `apps/web` uses the new endpoints yet (two type
  fixtures gained the new `SlateOut` fields).
- Requirement register rows are W2D's (below).
- Human: the product owner has not seen the join rule, the connection rule, the strength's
  rules or the empty P04/P05 slates (not run — requires human).

## Requirement candidates for W2D

- WORLD-xx: the first question's type-ahead offers ESCO preferred and alternative titles as
  typed, deterministic and offline; no match is an empty answer (`test_origin.py::
  test_the_type_ahead_offers_esco_titles_as_typed_and_never_invents_one`).
- WORLD-xx: the first answer is saved through the one profile write path with its ESCO
  occupation (`test_the_first_answer_is_saved_through_the_profile_with_its_esco_occupation`).
- WORLD-xx: the first answer's response (save + origin) within 1 s on the pinned release,
  no model call (`test_first_answer.py`).
- WORLD-xx: usual skills are display-only and unresolved wherever computed; "I've used this"
  is self-reported and counts for nothing (`test_the_origin_shows_usual_skills_...`,
  `test_capability_readiness.py::test_i_ve_used_this_...`).
- WORLD-xx: destinations and connections join by shared essential skills, never by words in
  a title (DSC-10 to DSC-14, `test_skill_joins.py`,
  `test_discovery.py::test_a_role_esco_lists_joins_...`, `..._does_not_list_...`).
- WORLD-xx: the unexpected connection's rule and sentence (`test_skill_joins.py`, DSC-10).
- WORLD-xx: the overlooked strength: one per turn that added answers, never on a support
  turn, verified span and essential skill, confirmed by the person, self-reported, declining
  stores nothing, demo scripted and labelled with no provider (`test_strength.py`,
  `test_origin.py` strength tests).

## Files

New: `backend/src/careerwright/profile/titles.py`, `capability/usual.py`,
`capability/strength.py`, `capability/strength_agent.py`, `capability/strengths.py`,
`api/origin_schemas.py`, `api/routes_origin.py`,
`migrations/versions/r0031_first_moments.py`; tests `tests/domain/test_skill_joins.py`,
`tests/domain/test_strength.py`, `tests/integration/test_origin.py`,
`tests/integration/test_first_answer.py`.
Changed: `profile/slate.py`, `profile/exploration.py`, `profile/store.py`,
`profile/commands.py`, `profile/document.py`, `catalogue/records.py`,
`catalogue/taxonomy.py`, `catalogue/taxonomy_store.py`, `capability/evidence.py`,
`capability/commands.py`, `capability/store.py`, `identity/records.py`,
`identity/model_registry.py`, `identity/model_choice.py`, `worker.py`, `api/app.py`,
`api/catalogue_schemas.py`, `api/discovery_schemas.py`, `api/routes_taxonomy.py`;
`tools/evaluation.py`, `tools/evaluation_cases.json`; tests `test_boundaries.py` (adapter),
`test_extraction.py` (latest run-kind migration), `test_capability_readiness.py`,
`test_discovery.py`, `tests/support/fake_models.py`; web `Directions.test.tsx`,
`Conversation.stories.tsx` (new `SlateOut` fields); ADRs 0007 (decisions 13, 14), 0012
(the `used` answer), 0014 (decision 3 in the app).

Reviewer can skip (generated): `apps/web/src/generated/**` (regenerated by
`pnpm run generate`).

## Concerns

1. P01's slate still rests on its tasks and work style matched against ESCO's skills and
   descriptions ("structured" now finds house builder through its description). That is
   ADR 0007 decision 5's task channel, not a title, and its target is not an ESCO title, so
   nothing joins by skills until the person picks the closest ESCO title. Session W2 should
   see it.
2. P04 and P05 now show no suggestions: honest, but stark. W2C should turn
   `unmatched_titles` into the sharper question (the type-ahead for the closest ESCO title).
3. Provisional (R6) and not yet seen by the product owner: 3 shared skills and the Jaccard
   ranking, the connection rule, the strength's trigger and quotable fields, the `used`
   answer.
4. The same strength may be proposed again on a later turn after a decline (declining
   stores nothing about the skill, as ruled); the client can choose not to show it twice.
5. Pre-existing duplication: three "chosen occupation" lookups now exist
   (`profile.sketch._chosen`, `capability.commands._chosen`, `profile.titles.targets`); left
   for the final-review list rather than refactored here.
6. `test_durable_runs.py`'s crash test hit the known worker-shutdown hang once in the second
   acceptance run (passed in the first and on re-run). Not caused by this slice as far as I
   can tell (the stuck worker had finished a connection-check run), but it does make a clean
   single `make acceptance` pass luck-dependent.

# Fix round 1

From `f70f88d`; dispatch `task-W2B-fix-round-1.md`, review `task-W2B-review.md`. Implementer:
Claude (Opus 5.5), fresh. No subagents, no live model call, no web request, no headed
browser, `spikes/world` untouched, `answers-2.md` not staged, DBOS `application_version`
still `careerwright-l0-1`. Commit: `e8c0bfb` (code, tests, ADRs, regenerated client).

## Status

DONE_WITH_CONCERNS: every finding is fixed as ruled and tested; the concerns are the slates
themselves (work-style and task words still match skill labels on their words, as the
ruling's design does; for session W2).

## Each finding

**I1 and I2 (one change): work is found only through its essential skills.**
- Migration 0032 adds `skills.search_vector`: English full-text over each skill's preferred
  label alone, a stored generated column, so the migration fills it for the held release and
  every later import fills it as each skill is written (same expression, no second code
  path). GIN index.
- `taxonomy_store.essential_skill_reach` / `taxonomy.search_essential_skills`: a search
  matches skill labels (every word, or any word ranked by how many), reaches an occupation
  only through a skill it lists as essential, and returns, per occupation, the best-ranked
  such skill. No title, hidden label, ISCO group label or description is searched.
  `exploration._search_hits` uses it for every query that is not the person's own title (task,
  environment, transferable, cross-industry, less familiar); it no longer takes exact label
  matches either (those were title words too). The old `titles=False` weights are removed.
- The why-line names the skill: "What you enjoy: “working outdoors”. Careerwright searched for
  “working outdoors”, and ESCO lists “work in outdoor conditions” as an essential skill for
  this work." A named title's own occupation now says "ESCO lists it as this occupation."
  (the old line claimed a search that no longer happens).
- A model query is one of the person's titles when its `careerwright.concept_key` equals the
  title's (`taxonomy_store.concept_keys`, the SQL function, so one definition).
- Evaluation: `discovery_output` on a discovery case stands in for the fixture proposer (the
  searches a model might propose). New DSC-15 ("Data analysts" proposed for the role "data
  analyst": joined by skills, with the connection). New check `searched_through_skills`:
  every "searched for" line names a skill that is one of the suggestion's essential skills
  (as the taxonomy holds them, now part of the observation offline and in `tools.live_eval`)
  and holds a word of the search (an independent, deliberately loose word fold); added to
  DSC-01, 03 to 09 and 12. Unit test of the check's failures
  (`tests/eval/test_evaluation.py::test_a_search_must_reach_work_through_an_essential_skill_that_holds_its_words`).
- Migration test: `test_migrations.py::test_0032_fills_the_essential_skill_search_for_the_release_already_held`
  (sample imported at 0031, migrated: every skill filled; "accounting entries" reaches the
  bookkeeper and the accounting assistant through that skill).
- ADR 0007 decision 13 amended (and the header: every provisional rule tied to session W2).

P01 (DSC-12) and P02 (DSC-01), full pinned release, offline evaluation path, before (`f70f88d`)
and after (`e8c0bfb`):

| | Before | After (each through the named essential skill) |
|---|---|---|
| P01 | ICT information and knowledge manager ("structured"), house builder ("structured"), online community manager ("collaborative"), bridge inspector ("finding inconsistencies", "structured"), branch manager ("collaborative"), chief operating officer ("collaborative"); every line "ESCO's record for this occupation matched" | dental practitioner ("finding inconsistencies": interpret findings from medical examinations; "structured": diagnose abnormalities of dental-facial structures), ICT information and knowledge manager ("structured": information structure), advertising installer ("structured": risks of elevated advertising structures), agronomic crop production team leader ("structured": soil structure), artistic coach ("collaborative": collaborate with coaching team), carpenter ("structured": install wood elements in structures) |
| P02 | fruit and vegetable picker, vineyard supervisor, fisheries observer, pesticides sprayer, consultant social worker ("working outdoors", "practical"), street sweeper; pool 120, 1 or more past the bound | deep-sea fishery worker, fisheries observer, fruit and vegetable picker, pesticides sprayer, landscape gardener, leaflet distributor, all through "working outdoors": work in outdoor conditions; pool 109 |

For session W2's sheet (W2D), not decided here: P01's work-style word "structured" still
matches skill labels about physical structures, and "finding inconsistencies" matches
"interpret findings" (stemming: "finding" and "findings"); P02's slate is all one skill,
"repairing physical objects", "practical" and "small team" placing nothing above the
relevance floor; DSC-07/08's "looking after people" reaches skills naming "people"
("entertain people", "interview people"). Whether work-style words should retrieve at all is
the product owner's question. Other cases after: "data analyst" unchanged (DSC-10, DSC-15),
P03 unchanged (DSC-13), P04 and P05 still empty with the reason, DSC-09 ("repairing
bicycles") the bicycle mechanic through "perform repairs on bicycles".

**I3: the strength reads only the turn's new answers.** `strengths._added_answers` now
returns the work answers present in the turn's profile version and absent from the one
before (field and text); empty is `no_new_answers` (so a removal no longer passes: M9),
and none quotable is `no_quotable_answer`. Only those answers go into the run's input.
Nothing new stored. Test:
`test_origin.py::test_a_strength_reads_only_the_turn_s_new_answers_so_a_declined_one_is_not_offered_again`
(demo workspace: turn 1 adds "reconciling accounting entries", proposed, declined; turn 2
adds "planning budgets" with the first answer still saved: complete, `found: false`; turn 3
adds only "it all": `no_quotable_answer`). RED shown on the committed module: with
`f70f88d`'s `strengths.py` restored (git stash) and everything else of this round, the test
failed at the later turn (it proposed again); GREEN after.

**I4: the demo's strength is scripted.** `strength.SCRIPTED_STRENGTHS`, a fixed table of the
demo journey's known answers with the ESCO skill each shows (URI and ESCO's label, which is
how the prompt names it): "reconciling accounting entries" → accounting entries; "fixing
bikes" → perform repairs on bicycles; "finding inconsistencies" → perform data cleansing;
"working outdoors" → work in outdoor conditions. `fixture_strength` proposes one only when
the answer is exactly a script's (case and spaces folded) and a destination lists that
skill; it passes `check_strength` like any output; anything else is none. No word overlap.
Tests: `test_strength.py::test_the_demo_proposes_only_its_scripted_strengths_and_passes_the_same_check`
("Fixing bikes" with no shared word; none for an unscripted answer sharing a word),
`::test_every_scripted_strength_is_a_quotable_answer_and_an_esco_skill`,
`test_evaluation.py::test_the_demo_s_scripted_strengths_are_essential_esco_skills_named_as_esco_names_them`
(full release: each URI is an essential skill with exactly that label), and the existing demo
integration test (accounting entries on the sample) still passes. ADR 0014 decision 3
amended.

**I5: closest titles.** When the type-ahead's every-word match finds nothing and two to
eight words were typed, `taxonomy_store.partial_title_matches` returns the occupations
whose preferred or alternative titles hold the most typed words (each a word beginning),
one per occupation by its best title, rarer words first (a word's count is how many of
those occupations hold it), then preferred, shorter, by label; `TitleMatchesOut.partial` is
true. Nine or more words: no fallback (97% of ESCO's titles have eight or fewer, and the
cost grows per word). Client regenerated. Test on the full release
(`test_first_answer.py::test_a_title_esco_does_not_list_offers_the_titles_holding_most_of_its_words`):
- P01 "Data quality analyst": data quality specialist, data analyst, call centre analyst,
  meter reader, statistician, water quality analyst, ... (16).
- P04 "Registered nurse": sales support assistant and dental hygienist first ("registered"
  is the rarer word), then nurse assistant, specialist nurse, veterinary nurse, advanced
  nurse practitioner, nursery school head teacher, nurse responsible for general care, ...
- P05 "Bookkeeping assistant": bookkeeper first, then the assistants.
- "data analyst" is not partial; "zqxj wvuy" and a nine-word query are an empty list.

**M1: timings** (`test_first_answer.py`, in-process API, real PostgreSQL 16 in the test
stack's container, full ESCO v1.2.1, Apple M4, 16 GB; one run each): type-ahead "a" 55 ms,
"s" 24, "c" 17, "d" 13, "da" 9, "data" 8, "data an" 9, "data analyst" 8; "data analyst"
chosen 19 ms, origin 23 ms; the clinical psychologist (99 essential skills, the most)
chosen 16 ms, origin 30 ms; the spa manager (shares 3 or more with 305 occupations, the
most) chosen 17 ms, origin 27 ms; the widest closest-titles fallback (eight single letters)
171 ms. Each asserted under 1 s. Recorded in ADR 0007 decision 14 for W2D to cite.

**M2: no connection unless the role names one occupation.** `exploration._connection`
returns none for an ambiguous role. New DSC-16 (role "bus operator", two occupations):
joined by skills, `no_connection` (before, the private chauffeur, family 832, would have been
"A bus operator and a private chauffeur share 17 essential skills"). ADR 0007 decision 14.

**M3:** `strengths._view` raises `INTERNAL_ERROR` for a complete strength run with no
readable output. Not tested: the database requires every complete run to have an output
(`complete_runs_have_an_output`), so only corruption reaches it.

**M4: tests added** (`test_origin.py`): the strength kind's own failure path (invalid
twice: `failed`/`invalid_model_output`, two requests, no proposal) and a decision on that
failed run (`409 PROPOSAL_NOT_AVAILABLE`, nothing recorded):
`test_a_strength_invalid_after_its_repair_fails_typed_and_has_nothing_to_decide`; a
confirmation against a stale capability version (`STALE_INPUT_VERSION`, then the right
version is accepted) and a strength asked for after the turn's answers changed
(`STALE_INPUT_VERSION`, `turn_version` 4, no run): `test_a_strength_is_confirmed_against_the_versions_the_person_saw`;
the `recite` path (a typed "bus operator", then the bus driver chosen for those same words:
a new version, the words kept, resolved to the bus driver; again: 200):
`test_a_role_esco_does_not_hold_joins_nothing_and_a_shared_title_asks_which`.

**M5: the person's title stays theirs.** `ChooseRole.label` (optional): the title the
person picked, which must be the occupation's ESCO title or one of its alternative titles
(else `422 VALIDATION_FAILED`, `not_its_title`); the role resolves by the `occupation_choice`
source's URI as before. Test:
`test_origin.py::test_the_role_keeps_the_title_the_person_picked_and_resolves_by_its_occupation`
("IT support technician" stays the role's words; its occupation is the ICT help desk agent).

**M6 (now):** ADR 0007 decision 13 states why the minimum is 3 (from the release: one shared
skill joins a median occupation to 337 others, two to 105, three to 45 with 50 occupations
joining none, four leaves 142 joining none; three is the fewest essential skills any
occupation lists), and the header ties every provisional rule to session W2. The sheet
itself stays W2D's. M7 and M8 not touched (W2C, final review).

## Rulings I made

1. **The skills vector is per skill, not per occupation.** An occupation-level concatenation
   of skill labels would let two skills' words make one every-word match, so no single skill
   would "hold the person's words" or be nameable. A per-skill vector joined through the
   essential relation makes every match one skill's. Only preferred labels, so the named
   label is the one that matched.
2. **A generated column** builds the vector at import and backfills the held release with one
   expression; `TRANSFORMATION_VERSION` unchanged (the import's rows are the same).
3. **Ranking inside a search:** the best skill's rank; equal ranks go to the occupation with
   more of its essential skills matching, then its title. Scores and floors as before.
4. **Closest titles:** only the occupations holding the most typed words; rarer words first
   (P05's bookkeeper first; P04's two "registered" titles before the nurses); two to eight
   words.
5. **`ChooseRole.label` is exact** (one of ESCO's titles for that occupation, as the
   type-ahead returns them), and the connection sentence keeps ESCO's title (a fact about two
   ESCO occupations).
6. **Changed assertion, disclosed:** `test_evaluation.py` asserted P02's pool overflows the
   120 bound. Four searches of at most 30 occupations each cannot pass 120 any more, so it
   now asserts the pool is within the soft 60 to 120 (109); the bound's cut is still tested in
   `test_slate.py::test_the_bounded_pool_samples_across_families_before_relevance_cuts_it`.
7. **The Storybook slate story** shows the new why-line form (fixture text only).

## Checks run

- `make check` on the final tree, exit 0: ruff format (323 files) and lint clean, mypy clean
  (323 files), pytest 1,534 passed / 316 deselected, fixture validator passed; web: client
  matches the OpenAPI document, Biome clean, `tsc` clean, Vitest 299 passed.
- Focused integration runs (real PostgreSQL 16, DBOS, workers, fake provider and fixtures):
  `test_origin.py` 11 passed; `test_first_answer.py`, `test_evaluation.py` (all 16
  discovery cases and EXP-01 on the full release, no failures), `test_migrations.py`,
  `test_discovery.py`, `test_taxonomy.py`, `test_slate_explanations.py`: 53 passed.
- RED/GREEN for I3 as above; the evaluation check's failures shown by its unit test.
- Not executed as RED: DSC-15 and DSC-16 against `f70f88d` (the old search code no longer
  fits the round's other changes); their before states are from the review (I1c) and the
  scratch slate above.

## Acceptance (on `e8c0bfb`)

- `make acceptance`, one run (no other acceptance running, checked with `pgrep`): pytest
  `-m "integration or stack"` **316 passed** in 8 min 39 s (the crash-recovery test in
  `test_durable_runs.py` passed; no shutdown hang). Storybook built. Playwright **41 passed,
  1 failed**: `e2e/world.spec.ts:273` "phone › the support status sits in the top bar and adds
  no row to the strip" (W2A's test): the strip measured 105 px before the message and 57 px
  after, so its first measurement caught a two-row strip before the page settled. Make
  stopped with exit 2.
- That test alone, `--repeat-each 3`: 3 passed. The web half again in full
  (`pnpm run build-storybook && pnpm run e2e`): **42 passed** (5.6 min), exit 0.
- Not caused by this round as far as I can tell: this round changes no web component (only
  the regenerated client's types and one Storybook story's text), and the failing test reads
  the world strip, which nothing here touches. Not claimed: a single clean `make acceptance`
  in one invocation. Not changed: W2A's test (out of scope); it measures `before` without
  waiting for the strip to settle, which W2C or W2D may want to look at.

## Live calls

None. Cost $0.

## Not run / for others

- `tools.live_eval`'s new essential-skills fetch for discovery cases is not exercised (live
  only, R5).
- Human: the product owner has not seen any of this round's slates, the closest-titles
  order or the scripted strengths (not run — requires human; session W2).
- Register rows: W2D's.

## Reviewer can skip

`apps/web/src/generated/**` (regenerated by `pnpm run generate`).

## Concerns

1. The slates still rest on words, now skill-label words: P01's "structured" finds
   structures, P02's six all come from one skill, "looking after people" finds any skill
   naming people. That is the ruled design, honestly labelled per suggestion; whether
   work-style (and loose task) words should retrieve is session W2's.
2. A role several occupations share is still joined over their skills together ("ESCO
   lists 26 of the same essential skills for both" for "bus operator"); only the connection
   was ruled out (M2).
3. P04's closest titles begin with two "registered" titles before the nurses.

# Fix round 2

From `e8c0bfb`; dispatch `task-W2B-fix-round-2.md`, re-review `task-W2B-rereview-1.md`.
Implementer: Claude (Opus 5.5), fresh. No subagents, no live model call, no web request, no
Docker pull (only the cached `postgres:16.15-bookworm`), no headed browser, `spikes/world`
untouched, `answers-2.md` not staged, DBOS `application_version` still `careerwright-l0-1`.
Commit: `267a83f` (code, tests, ADR 0007, register rows DIV1-02 and REC1-03, regenerated
client). No migration.

## Status

DONE_WITH_CONCERNS: the three rules, the prompt, I-A, I-B and the Minors are done and
tested; `make check` and one full `make acceptance` pass on the committed tree. Concerns:
many slates are now small or empty (the ruled trade), and the new prompt is untested live.

## What changed

**Rule 1, whole phrase, one skill** (`taxonomy_store.essential_skill_reach`,
`taxonomy.search_essential_skills`, `exploration._search_hits`). A search reaches a skill only
when that one skill's preferred label holds every content word of it (`plainto_tsquery`:
English stems, stop words dropped, every word required, no search operators). The any-word
pass, `PARTIAL_MATCH_WEIGHT` and the `any_word` parameter are gone. `searched_through_skills`
now needs every content word of the search (three or more letters, not one of a written-out
list of English function words) to agree with a word of the named skill, which must be one
of the suggestion's own essential skills.

**Rule 2, work style finds no work** (`exploration._work_style_only`, `compute_slate`). A
query, and a title hypothesis (ruling 2), whose `based_on` answers are all work style is not
run. No setting or flag. The slate says so in a note: "How you like to work (“structured”,
“collaborative”) isn't used to find work: it describes how you work, not the work itself." A
query resting on a task and a work style together still runs. New check
`work_style_not_searched` (DSC-01, DSC-07, DSC-12). ADR 0007 records it as provisional, for
session W2 to confirm or reverse.

**Rule 3, never cut ties alphabetically** (I-B). A search keeps every occupation it reaches
up to the pool bound (`POOL_LIMIT`, 120; `taxonomy.MAX_REACH` guards the internal call)
instead of its first 30. In the search, equal ranks order by the share of the occupation's
essential skills the search matched, then title, then ID. In the pool and on the slate,
`slate._order` is relevance, then `Candidate.share` (the share of the occupation's own
essential skills reached by any of the person's answers: skills a search matched or a join
shares; a folded role's never count), then title, then ID. `Occupation` carries
`essential_skills`; `Hit` and `Match` carry the reached skill IDs; `skill_neighbours`
returns each neighbour's shared skill IDs.

**The prompt.** `discovery-queries-2` asks for short phrases of 2-4 words in ESCO's skill
wording, with examples that reach work on the full release ("plan shifts" 58 occupations,
"repair bicycles" 1, "care for children" 16, "handle complaints" 47, "perform data
cleansing" 6) and one that reaches none ("look after children"); never a sentence or a word
alone; a query may be one of the person's own titles exactly as given (ruling 8); never work
style alone. **Untested live** (R5). It fits the prompt bound (the contract test's busiest
context passes).

**I-A, a folded role's skill is never this occupation's** (`Match.concept_id`,
`Candidate.own_matches`, `explain`, `unexpected_connection`). Why-lines come only from the
matches that reached the suggestion itself. A near-identical role folded into it still adds
to its relevance and its linked evidence (DIV1-05), but its skill is never named. The
connection ranks only the suggestion's own join.

**M-A, a shared title joins nothing until the person chooses** (`exploration._joinable`). A
role, target or title-query that several occupations hold gets no skill join; its
occupations stay the person's own close candidates. New `SlateOut.ambiguous_titles` (like
`unmatched_titles`) and, when the slate is short, "ESCO lists “bus operator” as the title of
2 occupations, so Careerwright can't join other work to it by shared skills until you choose
which one you mean." New check `titles_ambiguous`.

**M-B, closest titles** (`taxonomy_store.partial_title_matches`, `taxonomy.STATUS_WORDS`).
Labels holding more typed words whole come first ("nurse" before "nursery"), then rarer
words; "registered", "senior", "junior", "trainee", "qualified", "chartered", "certified"
and "licensed" are not counted (all status words: an empty answer).

**M-C, the pool bound and DIV1-02.** Two new full-release tests (below). P02's assertion
checks the bound and, below 60, the reason. A full discovery slate chosen from fewer than 60
says so: "Careerwright chose these from 12 occupations that match your answers closely. It
aims for at least 60, but doesn't add weaker matches to get there." New check
`small_pool_has_reason` (DSC-01, DSC-10). Register rows DIV1-02 (rewritten) and REC1-03
(rule 2).

**M-D:** done with rule 1. **M-E, a moved or re-added answer is not new**
(`strengths._added_answers`): an answer counts as new only if no earlier profile version
held its words (case and spacing aside) in what the person enjoys, can do or has done.

## Before and after

Full pinned release, offline evaluation path, fixture proposer (each answer a query).
Before is `e8c0bfb`, after is `267a83f`. Every "searched for" line after names an essential
skill holding every word of the answer.

| Case | Before | After |
|---|---|---|
| P01 (DSC-12) | dental practitioner ("finding inconsistencies": interpret findings from medical examinations), ICT information and knowledge manager ("structured": information structure), advertising installer ("structured": risks of elevated advertising structures), agronomic crop production team leader ("structured": soil structure), artistic coach ("collaborative": collaborate with coaching team), carpenter ("structured": install wood elements in structures) | None, with "None of your answers matched an occupation in ESCO yet.", "“Data quality analyst” isn't a title ESCO lists ... Choose the ESCO occupation closest to it." and the work-style note. The type-ahead offers the data quality specialist first; choosing it gives DSC-02's slate: data quality specialist, data entry clerk, big data archive librarian, data analyst, database designer, chief data officer |
| P02 (DSC-01) | deep-sea fishery worker, fisheries observer, fruit and vegetable picker, pesticides sprayer, landscape gardener, leaflet distributor; pool 109 | leaflet distributor, deep-sea fishery worker, pesticides sprayer, fisheries observer, fruit and vegetable picker, offshore renewable energy plant operator, all through "work in outdoor conditions"; pool 12, with the work-style and small-pool notes |
| P03 (DSC-13) | ICT help desk agent, after-sales service technician, call centre agent, ICT help desk manager, customer service representative, specialised seller | the same, plus the small-pool note (pool 31) |
| P04 (DSC-11) | none, with the reason; type-ahead: sales support assistant and dental hygienist first, six "nursery" titles in the 20 | none, with the reason; type-ahead: nurse assistant, specialist nurse, veterinary nurse, advanced nurse practitioner, nurse responsible for general care first, every "nursery" title last |
| P05 (DSC-14) | none, with the reason; type-ahead bookkeeper first | unchanged |
| "looking after people" (DSC-07, DSC-08) | activity leader ("entertain people"), animal behaviourist ("deal with challenging people"), animal shelter worker ("interview people"), child care coordinator, secretary ("communicate schedules to the people concerned"), administrative assistant ("disseminate messages to people") | none: no skill's label holds both "look" and "people"; "None of your answers matched an occupation in ESCO yet." |
| "caring for patients", "giving injections" | advanced nurse practitioner, activity leader ("give feedback on changing circumstances"), advertising manager ("give interviews to media"), aesthetician ("give massages"), air force officer ("give instructions to staff"), injection moulding operator | advanced nurse practitioner and specialist nurse, through "provide comprehensive care for patients with surgical conditions"; the third (nurse responsible for general care) is held by the family limit, with both reasons |
| "teaching children", "writing stories" | aquaculture mooring manager ("write technical reports"), aquatic animal health professional, corrosion technician, audio describer, behavioural scientist, blogger | none, with the reason |
| "designing websites", "writing code", style "collaborative" | webmaster, web designer, web developer, aquaculture harvesting manager ("collaborate with animal related professionals"), aquaculture mooring manager ("write technical reports"), acupuncturist ("develop a collaborative therapeutic relationship") | web designer, webmaster, web developer, through "implement front-end website design"; "Only 3 occupations matched ..."; the work-style note |
| "bus operator" (DSC-16) | tram driver, private chauffeur, bus driver, taxi driver, joined over both occupations' skills (the taxi driver: "14 of the same essential skills for both") | bus driver, trolley bus driver (the person's own title), nothing joined; `ambiguous_titles` and the choose-which reason |
| "mixing recordings", "attending recording sessions" (new DSC-17) | passed only because the any-word pass gave the sound designer its own "attend rehearsals" | sound editor, disc jockey, music director, sound operator, each through its own skill. With the I-A fix undone in-process, the sound editor claimed the sound designer's "mix multi-track recordings" and DSC-17 failed |

"data analyst" (DSC-10, DSC-15), DSC-02, DSC-03 and DSC-09 are unchanged, plus the
small-pool note where the slate is full.

**The tightened checks catch what was rejected.** HEAD's `backend/src` (extracted with `git
archive` to the scratchpad) run against this round's `tools/evaluation.py` and cases: DSC-01
fails (`work_style_not_searched`: "practical", "small team"), DSC-07 and DSC-08 fail
(`searched_through_skills`: "entertain people", "deal with challenging people", ...), DSC-10
fails (`small_pool_has_reason`, pool 31), DSC-12 fails ("interpret findings from medical
examinations", and "structured" and "collaborative" searched), DSC-16 fails
(`titles_ambiguous`: tram driver, private chauffeur, taxi driver joined) and DSC-17 fails
("edit recorded sound"). After: all 17 discovery cases pass.

## Rulings I made

1. **`plainto_tsquery` for the essential-skill search**, not web-search syntax, which turned
   "fixing or building things" into `'fix' | 'build' & 'thing'` (one word could still reach
   a skill). The public taxonomy search keeps its syntax.
2. **Rule 2 covers title hypotheses too**: a title the model thought of from work style
   alone is not checked against ESCO (the same leap from "creative" to a destination). Its
   words join the work-style note.
3. **The share** counts the occupation's own essential skills reached by any answer (a
   search's matched skills or a join's shared skills, each skill once); named hits add none.
   Inside one search, that search's own matched share.
4. **I-A: name only the suggestion's own matches** (the re-review's first option). A line
   naming the folded role would need that role's skills in the evaluation's observation to
   stay checkable; the not-included list already names the duplicate.
5. **M-A: a structured `ambiguous_titles` field** beside `unmatched_titles`, so the interface
   can ask which; the fewer reason only when short, like `unmatched_titles`.
6. **The small-pool note** only on a full discovery slate: a short slate already gives its
   reason, and the first slate (the role's join alone) is not DIV1-02's multi-channel pool.
7. **`work_style_not_searched`**, a check not asked for: rule 1's check cannot catch a
   one-word work-style answer matching on its stem ("structured" agrees with "structures"),
   so without it nothing evaluable guards rule 2, live included.
8. **The prompt lets the person's own title be a query**, so a target is still joined by
   skills on the live path, as on the fixture path.

## Changed assertions and test inputs (disclosed)

- `tests/integration/test_evaluation.py`, P02's pool: was `60 <= pool <= 120`; now
  `pool <= 120` and, below 60, a note naming the count (ruled: DIV1-02 is soft; P02's
  evidence reaches 12). The bound is exercised by the new bound test.
- DSC-12: `size_at_least 3` became `fewer_has_reason` (ruled). DSC-16: `joined_by_skills`
  became `titles_ambiguous` and `fewer_has_reason` (M-A; it would otherwise pass
  vacuously). DSC-07's title "adds candidates and removes none" became "removes no work"
  (rule 2: it adds none); its `pool_includes_pool_of` is unchanged. Added: `fewer_has_reason`
  to DSC-07 and DSC-08, `small_pool_has_reason` to DSC-01 and DSC-10,
  `work_style_not_searched` to DSC-01, DSC-07 and DSC-12; new case DSC-17.
- `tests/eval/test_evaluation.py`: the passing example ("repairing physical objects" through
  "perform repairs on bicycles") is exactly the one-word match now refused, so it moved to the
  failing examples and "repairing bicycles" passes. The fixture slate gained the fields the
  new checks read.
- Test inputs only, no assertion changed:
  - `test_discovery.py` and `test_slate_explanations.py`: "repairing bicycles", "restoring
    old furniture", "looking after gardens" became "tuning bicycles", "applying restoration
    techniques", "maintaining plant growth". The labelled sample keeps 6 essential skills per
    occupation, and the old phrases reached it only through one shared word; the new ones
    each hold every word of a sample skill.
  - `test_live_eval_ledger.py`: EXP-01's copy gains the answer "tuning bicycles" for this
    test only. On the sample P02's answers now reach nothing, so the explanation was refused
    (`no_suggestions`); the test is about the ledger. Found by acceptance run 1 (below).
  - `test_migrations.py` drops the removed `any_word=False`; the domain helpers pass the new
    `essential_skills`; the Storybook story's why-line ("machinery repair" reaching "repair
    equipment on site", now impossible) became "repair equipment".
- Strengthened: `test_first_answer.py` asserts P04's five nurses first, no sales support
  assistant, and every whole "nurse" before any "nursery".

## Tests and checks

TDD (RED on the unchanged code, then GREEN):
- `test_slate.py::test_a_why_line_never_names_a_near_identical_role_s_skill_as_this_one_s`
  (I-A): RED by assertion (the sound designer's line named "attend music recording
  sessions"); GREEN.
- `test_slate.py::test_equal_matches_go_to_the_larger_share_of_essential_skills_never_to_the_title`
  (I-B): RED as a collection error (`Occupation` had no `essential_skills`); GREEN.
- `test_evaluation.py::test_a_search_keeps_all_the_work_one_skill_reaches_so_no_tie_is_cut_by_title`
  (full release): RED `assert 41 == 58` (30 every-word hits by title plus 11 any-word; the
  warehouse worker, which "stacking goods" also reaches, was cut); GREEN (58; the warehouse
  worker first, with both answers).
- `test_evaluation.py::test_the_working_pool_keeps_its_bound_and_counts_the_work_beyond_it`
  (full release): RED `assert 59 == 120`; GREEN (120 kept, the rest counted).
- `test_origin.py::test_an_answer_moved_or_added_back_is_not_new_so_a_declined_strength_stays_declined`
  (M-E): RED (HEAD's `strengths.py` started a new run, so no error); GREEN (422
  `no_new_answers`).
- Not run RED: M-B's new assertions (HEAD's order is in fix round 1's report) and the
  evaluation checks' unit tests (written with the checks).

Focused runs (real PostgreSQL 16.15 in the test stack): `test_origin.py` 12 passed;
`test_evaluation.py`, `test_first_answer.py`, `test_migrations.py` 14 passed (the widest
closest-titles fallback 0.305 s, under the 1 s budget); `test_discovery.py`,
`test_slate_explanations.py`, `test_taxonomy.py` 41 passed; `test_live_eval_ledger.py` and
`test_live_smoke_ledger.py` 6 passed.

`make check` on the committed tree, exit 0: ruff format and lint clean, mypy clean (323
files), pytest 1,539 passed / 319 deselected, fixture validator passed; web: client matches
the OpenAPI document, Biome clean, `tsc` clean, Vitest 299 passed.

`make acceptance` (no other run going, checked with `pgrep`):
- Run 1 (before the last test fix): pytest `-m "integration or stack"` 318 passed, 1
  failed: `test_live_eval_ledger.py::test_every_case_attempt_is_ledgered_and_the_results_are_written`,
  `INSUFFICIENT_EVIDENCE` on EXP-01's explanation. Mine (above). Make stopped before the
  web half.
- Run 2, on the committed tree: pytest 319 passed (8 min 27 s), Storybook built, Playwright
  42 passed (5.6 min), exit 0. Neither known flake occurred.

## Live calls

None. Cost $0.

## Not run / for others

- `discovery-queries-2` is untested live (R5): whether a live model writes ESCO's skill
  wording is unknown.
- Human: the product owner has not seen these slates, the empty P01 and "looking after
  people" slates, the notes' wording or rule 2 (not run — requires human; session W2).

## Reviewer can skip

`apps/web/src/generated/**` (regenerated by `pnpm run generate`).

## Concerns

1. Many slates are now small or empty (P01, "looking after people", "teaching children,
   writing stories"; P02 from 12 occupations): the ruled trade, stated in plain reasons. The
   live path now depends on the model writing ESCO's skill wording, which is untested.
2. A one-word task answer still matches its stem ("driving" reaches "comply with policies
   for trolley bus driving"): session W2's.
3. The title join's best 30 (`skill_join_hits`) still breaks exact ties (equal share of both
   roles and equal shared count) by concept ID: not the alphabet, but arbitrary. Unchanged.
4. Rule 2 against REC1-03 ("a preference informs hypotheses"): work style still reaches the
   model and can support a task's search, but finds nothing alone. The product owner may
   reverse it at session W2.
5. Register row DIV1-08 still says "39 cases" (stale since earlier rounds); not changed.

# Fix round 3

From `267a83f`; dispatch `task-W2B-fix-round-3.md`, re-review `task-W2B-rereview-2.md`.
Implementer: Claude (Opus 5.5), fresh. No subagents, no live model call, no web request, no
Docker pull (a throwaway container from the cached `postgres:16.15-bookworm`, synthetic
passwords, random loopback port, removed afterwards; the test stack as `make acceptance`
builds it), no headed browser, `spikes/world` untouched, `answers-2.md` not staged, DBOS
`application_version` still `careerwright-l0-1`. Commit: `392bc64` (code, tests, ADR 0007,
register rows DIV1-02, DIV1-06, DIV1-08, DIV1-10, REC1-03, regenerated client). No migration.

## Status

DONE_WITH_CONCERNS. Every ruled item and every "Fix now" item is done and tested; `make
check` and one full `make acceptance` pass on the committed tree. Concerns: common general answers now
give empty slates (the ruled trade, said in words), the thresholds are provisional, and the
new prompt is untested live.

## What changed

**N-I1, honest emptiness** (`exploration._missed_notes`). An answer whose every search
found nothing is named in the notes, on full and short slates: "“Repairing physical
objects” isn't how ESCO names any skill, so it found no work." Where the searches were not
the answer's own words (a model's), the note names them instead of claiming the answer's
words were searched: "The search “repair machinery” (from “fixing things”) isn't how ESCO
names any skill, so “fixing things” found no work." An answer several searches rest on is
named only when none of them reached anything (a search too general to find work alone did
reach work, so its answer is not "found nothing"). The person's own titles keep their own
reasons; a one-word work style keeps its own note. New check `missed_answers_named` (DSC-01,
DSC-03, DSC-07 and the new patients case DSC-18).

**N-I2, general answers** (`slate.too_general`, `TOO_GENERAL_OCCUPATIONS = 50`,
`TOO_GENERAL_SKILLS = 5`, both provisional in ADR 0007). A search that reaches more than 50
occupations, or more than 5 different essential skills none of which is named by exactly
its words (stems and stop words aside; `taxonomy_store.essential_skill_reach` now returns
the skill count and an `exact` flag), finds no work by itself. It only adds weight to work
another search or join found: the 0.2 a further query adds, never its own score (so it never
lifts a weak match over the relevance floor), and on every such occupation it reaches, past
its own cut too (it is searched again among them, `essential_skill_reach_among`; see "Found
on the way" below). The slate says so: "“Writing reports” is part of 217 occupations in
ESCO, too many to choose from on its own. Say more about it, such as what it's about or who
it's for." and, for the skills half, "“Training staff” is part of 10 different ESCO skills,
none of them just that, so it's too general to choose work from on its own. ..."
`PoolQueryOut` gains `reach` and `too_general`. New check `general_searches_add_only` and
case DSC-19 ("caring for children", "writing reports"). The empty slate's reason became
"None of your answers found work to suggest yet." (it said "matched an occupation", untrue
for a general answer).

**N-I3, rule 2 narrowed** (`exploration._one_word_style`). Only a search or title idea resting
on one-word work-style answers alone ("structured", "practical": one whitespace-separated
word) is not run; a longer one is searched under rules 1 and N-I2 like any other answer
(environment channel, weight 0.6). The note no longer says the answer isn't about the work:
"How you like to work (“structured”, “collaborative”) isn't searched on its own, because a
single word matches too loosely. Careerwright searches a longer answer, such as “working
outdoors”." `work_style_not_searched` checks one-word answers only. Rows DIV1-10 and REC1-03
brought up to date.

**N-M4, order** (`Candidate.reach`, `slate._order`). Equal relevance goes first to work a more
specific search found (the smallest reach among the searches and joins that found it
itself; a general search never counts), then the share of essential skills, then the title.

**N-M1, no cut inside a tie.** The join's best 30 runs on to the end of its tied group (equal
share and equal shared count; `skill_join_hits`). The search's 120 cut is `FETCH FIRST
(:limit) ROWS WITH TIES` ordered by rank and share, the title ordering only what is kept.

**N-M2, counts** (`slate.skill_join`, `PoolQuery.total`/`unkept`, `build_pool`).
`beyond_pool_limit` now counts, once each, every occupation a search or join that can find
work reached and the pool doesn't keep: past a join's best 30 or past the pool's bound. A
search that can find work reaches at most 50, under the search's 120 cut, so it keeps all it
reaches and a join's cut IDs are known: the count is exact, never "at least" (a domain test
pins `TOO_GENERAL_OCCUPATIONS < POOL_LIMIT`). The slate says what a join keeps: "“Data
analyst” shares 3 or more essential skills with 47 other occupations in ESCO. Careerwright
keeps the 30 that share the most." The web line became "17 more were found but not kept."
(was "... than the pool holds", untrue for a join's cut).

**N-M3.** DSC-07 and DSC-08 search "caring for animals" (13 occupations, 5 skills), so the
pair compares two pools of 13. `test_discovery.py` asserts the deeper note's words ("because
you asked for more depth") and that the balanced view has none.

**The connection's article** (`with_article`): a title whose head (its last word before the
first "for", "in", "of", "on", "with", "at" or "to") ends in "s" but not "ss" or "us" takes
no article. Over all 3,039 ESCO preferred labels it matches only "warehouse operators for
clothing": "A warehouse manager and warehouse operators for clothing share 6 essential
skills."

**Register DIV1-08**: 54 cases (19 discovery, 14 interview, 13 support, 7 guard, 1
explanation). Rows DIV1-02, DIV1-06, DIV1-10 and REC1-03 updated.

**Prompt `discovery-queries-3`**: "plan shifts" (58 occupations, now too general) left the
examples for "stack goods" (13); a phrase many kinds of work share ("write reports", "solve
problems", "work in a team") is too general, say what it is about ("write inspection
reports", 29, exact); only a one-word work style is never searched alone, where someone
likes to work may be ("work in outdoor conditions"). **Untested live** (R5).

## Found on the way (fixed, beyond the re-review's list)

- DSC-19 first showed the general answer's weight lost: "writing reports" keeps its best 127
  (120 and the tied), which leave out the nursery school head teacher, the one occupation
  "caring for children" also reaches. So a general search's weight depended on its own rank
  cut. It is now searched again among what the other searches found, with no cut. RED:
  `test_a_general_answer_adds_weight_to_all_the_work_another_answer_found` (first suggestion
  was the primary school teaching assistant); GREEN.
- A general match's own score became the candidate's best score, so a general search could
  lift a weak match (0.3) to 1.2 and over the floor. Now it adds only the 0.2. RED: the domain
  test (`assert 1.2 == 0.3 + 0.2`); GREEN.

## Before and after

Full pinned release, offline path, fixture proposer (each answer a query). Before is
`267a83f`, after is this round.

| Case | Before | After |
|---|---|---|
| P01 (DSC-12) | none; "None of your answers matched an occupation in ESCO yet.", the unmatched-title reason; work-style note "isn't used to find work: it describes how you work, not the work itself" | none; "None of your answers found work to suggest yet.", the unmatched-title reason; the reworded work-style note ("structured", "collaborative"); "“Finding inconsistencies” isn't how ESCO names any skill, so it found no work." and the same for "Explaining evidence". Type-ahead unchanged |
| P02 (DSC-01) | leaflet distributor, deep-sea fishery worker, pesticides sprayer, fisheries observer, fruit and vegetable picker, offshore renewable energy plant operator (all "work in outdoor conditions"), pool 12; work-style note ("practical", "small team") and small-pool note | the same six in the same order, pool 12; "small team" is now searched (finds nothing); notes: work style ("practical"), "“Repairing physical objects” isn't how ESCO names any skill, so it found no work.", "“Small team” isn't how ESCO names any skill, so it found no work.", small pool |
| P03 (DSC-13) | ICT help desk agent, after-sales service technician, call centre agent, ICT help desk manager, customer service representative, specialised seller; pool 31; beyond 0 | the same six; pool 31; beyond 79; "“IT support technician” shares 3 or more essential skills with 109 other occupations in ESCO. Careerwright keeps the 30 that share the most." |
| P04 (DSC-11) | none, with the reason | none, with the reason (empty reason reworded); type-ahead unchanged |
| P05 (DSC-14) | none, with the reason | the same (empty reason reworded) |
| "solving problems" | gambling quality assurance engineer, lottery operator, public administration manager, ground lighting officer, webmaster, nurse assistant (pool 74) | none; "“Solving problems” is part of 77 occupations in ESCO, too many to choose from on its own. Say more about it, ..." |
| "writing reports" | emergency ambulance driver, chiropractor, city councillor, aquaculture mooring manager, consumer goods inspector, lieutenant (pool 118) | none; "... part of 217 occupations ..." |
| "working in a team" | leisure attendant, derrickhand, chief fire officer, firefighter, emergency medical dispatcher, firefighter instructor (pool 117) | none; "... part of 242 occupations ..." |
| "training staff" | ground lighting officer, air traffic manager, call centre quality auditor, recycling specialist, quality services manager, kitchen and bathroom shop manager (pool 17) | none; "“Training staff” is part of 10 different ESCO skills, none of them just that, so it's too general to choose work from on its own. ..." |
| "analysing data" | aeronautical information service officer, product development manager, customer experience manager, retail entrepreneur, talent agent, trade regional manager (pool 90) | none; "... part of 92 occupations ..." |
| "repairing bicycles", style "working outdoors" | bicycle mechanic only; "How you like to work (“working outdoors”) isn't used to find work: it describes how you work, not the work itself." | bicycle mechanic first, then leaflet distributor, deep-sea fishery worker, fisheries observer, fruit and vegetable picker, pesticides sprayer, each through "work in outdoor conditions"; pool 13 with the small-pool note; no work-style note |
| "caring for patients", "giving injections" (new DSC-18) | advanced nurse practitioner, specialist nurse, the family-limit reason; silent on "giving injections" | the same, plus "“Giving injections” isn't how ESCO names any skill, so it found no work." |
| DSC-03 | the same six; pool 31; "A warehouse manager and a warehouse operators for clothing share 6 essential skills." | the same six; pool 48 (the join's tie at 30 runs to 47); beyond 70; both tasks named as having found no work; the join note ("keeps the 47"); "A warehouse manager and warehouse operators for clothing share 6 essential skills." |
| "data analyst" (DSC-10, DSC-15) | data scientist, chief data officer, big data archive librarian, data quality specialist, data entry clerk, knowledge engineer; pool 31; beyond 0 | the same six; beyond 17; "“Data analyst” shares 3 or more essential skills with 47 other occupations in ESCO. Careerwright keeps the 30 that share the most." |
| DSC-07, DSC-08 | "looking after people": none, both | "caring for animals": animal shelter worker, veterinary nurse, poultry breeder, kennel supervisor, bee breeder (8 more held by the family limit); DSC-07 adds "“Quiet concentration” isn't how ESCO names any skill, so it found no work." |
| DSC-17 | sound editor, disc jockey, music director, sound operator | sound editor, music director, disc jockey, sound operator (N-M4: "attending recording sessions" reaches 2, "mixing recordings" 4) |
| "caring for children", "writing reports" (new DSC-19) | (not a case) | nursery school head teacher first, with both answers ("implement care programmes for children", "write work-related reports"), then primary school teaching assistant, Steiner school teacher, special educational needs teacher, child care coordinator, early years teaching assistant; "writing reports" named as too general |

**The new checks catch the old code.** HEAD's `backend/src` (`git archive 267a83f`) run with
this round's `tools/evaluation.py` and cases (the old API has no `too_general`, read as
false): DSC-01 fails `missed_answers_named` (repairing physical objects), DSC-03 (training
new starters, planning shift rotas) and DSC-18 (giving injections). After: all 19 discovery
cases pass. `general_searches_add_only` reads the product's own flag, so it cannot catch the
old code; the independent guard is the full-release test that the five general answers
give no suggestion.

## Rulings I made

1. **"occupations", not "kinds of work"**, in the general note: the slate already uses "kinds
   of work" for ISCO families ("in kinds of work already shown 2 times"), so the ruled
   example's words would name two things the same. The advice is generic ("Say more about
   it, such as what it's about or who it's for."): code can't write "Say what the reports are
   about" for any answer.
2. **Two wordings** for the missed and general notes: the answer's own words when the search
   was them (the demo's proposer), else the search named with the answer it came from (a
   model's), so the live path never claims the person's words were searched.
3. **Exact counts, no "at least"**: with 50 below the search's 120 cut, a search that can find
   work keeps everything it reaches, and a join's cut is known by ID. `beyond_pool_limit`
   counts ESCO occupations (a folded near-identical role counts), not folded roles.
4. **A general search adds the further-query 0.2 only**, never its own score, and is searched
   again among the other searches' occupations so its weight doesn't depend on its own cut
   (see "Found on the way").
5. **"One word" is one whitespace-separated word** ("hands-on" is one word).
6. **The specificity order** uses only the searches and joins that found the occupation
   itself; a general search or a folded role's match never counts.
7. **The person's own titles** are never named by the missed note: they have their reasons
   (`_unmatched`, `_ambiguous`).
8. **`PoolQueryOut.reach` and `too_general`** are new API fields (the general check needs the
   flag; `missed_answers_named` reads `reach`, since a general search may add weight nowhere
   yet still found work). Client regenerated.
9. **DSC-07** keeps its style "quiet concentration" (now searched; it finds nothing and is
   named); its `work_style_not_searched` would pass by construction, so it was replaced by
   `missed_answers_named`.
10. **The join note** shows on discovery slates only; the origin's first slate shows no notes.
11. **New prompt version** `discovery-queries-3` (its words changed).

## Changed assertions and test inputs (disclosed)

- `tests/integration/test_evaluation.py`:
  - `test_a_search_keeps_all_the_work_one_skill_reaches_so_no_tie_is_cut_by_title`: "planning
    shifts" + "stacking goods" became "stocking shelves" + "upselling products" ("planning
    shifts", 58, is now too general); `== 58` became `== 44`, and the first suggestion the
    ticket issuing clerk (42nd by title, the one both reach) instead of the warehouse worker.
  - `test_the_working_pool_keeps_its_bound_and_counts_the_work_beyond_it`: "maintaining
    equipment" + "planning shifts" (both now too general) became four specific searches
    reaching 178; `hits["maintaining equipment"] == POOL_LIMIT` became each search's hits
    and `hits == reach`; `beyond_pool_limit > 0` became `== 178 - 120` (stronger).
  - New: `test_a_search_never_cuts_inside_a_tie`, the five general answers (parametrized),
    `test_a_general_answer_adds_weight_to_all_the_work_another_answer_found`,
    `test_where_someone_likes_to_work_is_searched_and_a_specific_answer_s_work_comes_first`.
- `tests/integration/test_discovery.py`: `assert deeper["notes"]` became the deeper note's
  words, and none on the balanced view (N-M3).
- `tests/domain/test_slate.py`: the share test's input "planning shifts" (bricklaying
  supervisor, rescue centre manager, tool pusher) became "stocking shelves" (shelf filler,
  merchandiser, ticket issuing clerk, ESCO's counts); the assertions keep their shape. New:
  the specificity order, the general rule (with the floor), the pool's count.
- `tests/domain/test_skill_joins.py`: new tie and `skill_join` tests; unchanged otherwise.
- `tests/domain/test_discovery_contract.py`: `with_article` cases added.
- `tests/eval/test_evaluation.py`: the work-style test was renamed and now passes a longer
  work-style answer (ruled N-I3; the one-word case still fails). New tests for
  `missed_answers_named` and `general_searches_add_only`.
- `tools/evaluation_cases.json`: DSC-01 and DSC-03 gain `missed_answers_named`; DSC-07's task
  "looking after people" became "caring for animals", it lost `work_style_not_searched` and
  gained `missed_answers_named` and `small_pool_has_reason`; DSC-08's task likewise, plus
  `small_pool_has_reason`; new DSC-18 and DSC-19. `work_style_not_searched` now checks
  one-word answers only (ruled).
- Web: `Directions.test.tsx` and the Storybook story's slate fixtures gain `reach` and
  `too_general`; a new Vitest test for "17 more were found but not kept." and the join note.
- No test asserted the old empty-slate sentence or the old work-style note's words.

## Tests and checks

TDD (RED on the unchanged code, then GREEN):
- `test_skill_joins.py::test_a_join_never_cuts_inside_a_tie`: RED (the 3-cut kept 3 of a
  4-way tie); GREEN.
- `tests/integration/test_evaluation.py::test_a_search_never_cuts_inside_a_tie` (full
  release): RED (`[3 IDs] == [4 IDs]`, the 3rd and 4th tie at 1 of 27); GREEN.
- `test_slate.py`: the three new tests RED as a collection error (no `TOO_GENERAL_*`); GREEN.
  Undone in-process, the order test fails with the old `_order` (leaflet distributor first)
  and the share test fails without the share key (merchandiser first); my first version of
  the order test passed under the old order (its hits had no skills, then its channel
  weight separated them) and was corrected before it counted.
- `test_discovery_contract.py` (article): RED ("a warehouse operators for clothing"); GREEN.
- The general search's weight past its cut and its score: RED as above; GREEN.
- Not run RED: `skill_join` (written just before its test), the evaluation checks (written
  with their unit tests), the notes' words (checked through the cases and integration tests).

Focused integration runs (test stack, real PostgreSQL 16.15): `test_evaluation.py`,
`test_discovery.py`, `test_slate_explanations.py`, `test_first_answer.py`,
`test_origin.py`, `test_taxonomy.py`, `test_migrations.py`, `test_live_eval_ledger.py`: 76
passed (1 min 50 s).

Timing on the full release (scratch database): the heaviest searches 6-53 ms; a slate of
eight general and broad answers with a role, 97 ms.

`make check` on the final tree, exit 0: ruff format and lint clean, mypy clean (323 files),
pytest 1,546 passed / 327 deselected, fixture validator passed; web: client matches the
OpenAPI document, Biome clean, `tsc` clean, Vitest 300 passed.

`make acceptance` (no other run going, checked with `pgrep`):
- A first run was stopped by me during its pytest half (all passing so far) when DSC-19
  showed the general search's lost weight; the tree then changed, so it counts for nothing.
- Run 2, on the final tree (committed unchanged as `392bc64`): pytest `-m "integration or
  stack"` 327 passed (8 min 45 s), Storybook build completed, Playwright 42 passed
  (5.9 min), exit 0. Neither known flake occurred.

## Live calls

None. Cost $0.

## Not run / for others

- `discovery-queries-3` is untested live (R5).
- Human (not run — requires human; session W2): the thresholds 50 and 5, the one-word work
  style rule, the specificity order, every note's words, and the empty slates common general
  answers now give.

## Reviewer can skip

`apps/web/src/generated/**` (regenerated by `pnpm run generate`).

## Concerns

1. Common general answers ("solving problems", "writing reports", "analysing data", "managing
   budgets", "meeting deadlines", "planning shifts", "driving") now find no work on their own;
   each slate says so and asks for more. That is the ruled trade, provisional for session W2.
2. On the live path, a model's general query from a specific answer would ask the person to
   "say more" about an answer that was specific. Untested live.
3. A general search's weight is searched again among the found occupations: one more query
   per general search (cheap on the release, timed above).
4. `beyond_pool_limit` counts ESCO occupations, so a near-identical role the join cut counts
   as one more, though it would have folded into a kept one.

# Fix round 4

From `392bc64`; dispatch `task-W2B-fix-round-4.md`, re-review `task-W2B-rereview-3.md`.
Implementer: Claude (Opus 5.5), fresh. No subagents, no live model call, no web request, no
Docker pull (the test stack `make acceptance` builds, from cached images), no headed browser,
`spikes/world` and the running `careerwright-l0-*` stack untouched, `answers-2.md` not staged,
DBOS `application_version` still `careerwright-l0-1`. Commit: `b2aa090`. Words, labels and
tests only: no matching rule, threshold, rank, API field or migration changed; the generated
client is unchanged.

## Status

DONE. Every "Fix now" item is done with a test that fails without it; `make check` and one
`make acceptance` pass on the committed tree.

## What changed

**I1, what was checked** (`exploration._missed`, `_general_note`). The notes now say the
search was checked against skills ESCO lists as essential for an occupation:
- own words: "“Taking pictures” isn't part of any skill ESCO lists as essential for an
  occupation, so it found no work." (was "isn't how ESCO names any skill")
- a model's: "The search “repair machinery” (from “fixing things”) isn't part of any skill
  ESCO lists as essential for an occupation, so “fixing things” found no work."
- general, occupations: "“Writing reports” is part of the essential skills of 217
  occupations in ESCO, too many to choose from on its own. ..." (was "is part of 217
  occupations")
- general, skills: "“Training staff” is part of 10 different essential skills in ESCO, none
  of them just that, ..." (was "10 different ESCO skills")

**I2, the join's measure** (`_join_note`): "“Data analyst” shares 3 or more essential skills
with 47 other occupations in ESCO. Careerwright keeps the 30 with the largest share of
essential skills in common." (was "the 30 that share the most"). Vitest string, ADR quote and
register row DIV1-02 updated.

**M1, a model's general search** (`_general_note`). Where the search is not the answer's own
words, the note no longer asks the person to say more: "The search “write reports” (from
“writing inspection reports for bridges”) is part of the essential skills of 217 occupations
in ESCO, too many to choose from on its own. Careerwright would need a narrower search to find
work from “writing inspection reports for bridges”." The own-words note still asks "Say more
about it, such as what it's about or who it's for."

**M2, the live-path rules tested, and the edge fixed** (`_missed_notes`). The re-review's
edge: a model's search resting on a task and a one-word style that found nothing named the
style as "found no work", though ADR 0007 says a one-word style keeps its own note. Now
`_missed_notes(queries, unsearchable, styles)` puts such a style in the work-style note
(beside the one-word styles never searched, which `compute_slate` used to add itself), and
names only the task. `missed_answers_named` (`tools/evaluation.py`) leaves one-word work
styles to their own note, so a live evaluation would not fault the product for it.

**M3** (`tests/integration/test_evaluation.py`,
`test_where_someone_likes_to_work_is_searched_and_a_specific_answer_s_work_comes_first`): both
answers are now how someone likes to work, so both search in one channel and score alike;
only the specificity order puts the bicycle mechanic (1 of 13 essential skills) before the
leaflet distributor (1 of 6).

**M4, the web** (`Directions.tsx`, `vocabulary.ts`). Under "Found by these searches", a
`too_general` search reads "“writing reports”, from “writing reports” (too general to find
work on its own, so it only added weight to what another search found)". The new words are
`ADDED_WEIGHT_ONLY` in `vocabulary.ts`. "found by N searches of ESCO" counts only searches
that can find work, and says "1 search" in the singular. No new colour.

**The plural title in "Try it"** (`explain`): "Talk to people who work as warehouse
operators for clothing about a typical week (an informational interview)." The plural test
the connection's article uses is now `_plural`, shared by `with_article` and `explain`.

ADR 0007 (decision 6, decision 13's join, rule 4 and honest emptiness, Consequences) and
register rows DIV1-02 and DIV1-06 updated.

## Rulings I made

1. **Both halves of the general note** say "essential skills": the occupation count is
   reached through essential skills too, so "part of 217 occupations" was the same root as
   I1.
2. **M1's words** name the search as the cause and ask nothing of the person. They promise
   nothing about Suggest again, since a new model run may search the same way.
3. **The one-word style beside a task** joins the work-style note ("isn't searched on its
   own, because a single word matches too loosely" is true of it), rather than getting no
   note at all, so an answer that found nothing is never silent.
4. **"1 search"**: leaving general searches out of the count makes a count of one common
   (DSC-19 reads "found by 1 search of ESCO"; before this round it read "2 searches"), so I
   fixed the singular in the same sentence.
5. **The "taking pictures" test runs on the full release**, so it also checks that ESCO
   really reaches nothing for it (reach 0), not just the words.
6. **The join note's words**: "the largest share of essential skills in common" (the
   dispatch's own words), short enough for the slate.

## Changed tests and inputs (disclosed)

- `tests/integration/test_evaluation.py`:
  - `test_an_answer_too_general_to_find_work_alone_finds_none_and_says_why`: the expected
    reach words became "the essential skills of 77 occupations" (and 217, 242, 92) and "10
    different essential skills": the intended new wording (I1). Same assertion shape.
  - M3's test: the profile `enjoyed_tasks: ["repairing bicycles"]`, `work_style: ["working
    outdoors", "structured"]` became `work_style: ["repairing bicycles", "working outdoors",
    "structured"]`, so the order half is a real check. Assertions unchanged.
  - New: `test_an_answer_naming_a_skill_no_occupation_lists_as_essential_is_named_for_what_was_checked`.
- `tests/eval/test_evaluation.py`: the synthetic note strings fed to the checks now use the
  new words (the checks read only "found no work" and the quoted answer, so the strings were
  only stale). The `shown` helper gained `more` for an extra query. New assertion: a
  one-word style searched beside a task, named only in its own note, passes
  `missed_answers_named`.
- `tests/domain/test_slate.py`: new `test_the_notes_say_what_a_model_s_searches_checked_and_which_answers_found_no_work`
  and `test_a_small_test_of_work_with_a_plural_title_talks_to_people_who_do_it`; one new
  assertion of `_join_note`'s words in `test_the_pool_counts_what_a_join_reached_past_its_cut_and_its_own_bound`.
- `Directions.test.tsx`: the join note string (I2); `renderDirections` now also renders
  `EvidenceDrawer` (closed until opened, as `WorkspaceShell` renders it) so a test can open
  the Source drawer; new test for M4.

## Tests and checks

RED on the unchanged code, then GREEN:
- `test_slate.py`: the notes test RED (`_missed_notes()` takes 2 arguments; called in
  process, the old code named "practical" as "found no work", said "isn't how ESCO names any
  skill", and asked "Say more about “writing inspection reports for bridges”"); the plural
  test RED ("someone who works as warehouse operators for clothing"); the join assertion RED
  ("that share the most"). All GREEN.
- `tests/eval/test_evaluation.py`, the style assertion: RED against the old
  `tools/evaluation.py` (`git stash` of that one file, THIN_EVIDENCE "not named"), GREEN.
- `Directions.test.tsx`, the M4 test: RED against the old `Directions.tsx` ("found by 1
  search of ESCO" not found; it read "2 searches"), GREEN.
- M3's test with round 3's order patched in (a scratch pytest plugin outside the repository
  replacing `slate._order` with the order before N-M4): RED, `'leaflet distributor' ==
  'bicycle mechanic'`. GREEN with the real order.
- The "taking pictures" test: GREEN on the full release (reach 0, the new sentence, no "names
  any skill"); the old sentence is the in-process output above.

Focused integration run (test stack, real PostgreSQL 16.15, full release):
`tests/integration/test_evaluation.py`, 14 passed (31 s), all 19 discovery cases included.

`make check`, exit 0: ruff format (323 files) and lint clean, mypy clean, pytest 1,548
passed / 328 deselected, fixture validator passed; web: client matches the OpenAPI document,
Biome clean, `tsc` clean, Vitest 301 passed.

`make acceptance` (none running, checked with `pgrep`), one run on the committed tree: pytest
`-m "integration or stack"` 328 passed (8 min 32 s), Storybook build completed, Playwright 42
passed (5.7 min), exit 0. Neither known flake occurred.

## Live calls

None. Cost $0.

## Not run / for others

- `discovery-queries-3` is still untested live (R5), so M1's wording has not met a real
  model's search.
- Human (not run — requires human; session W2): the words of every note changed here and
  the web mark. The re-review asks for M1's case and the other round 3 items on the W2D
  carry-forward sheet; that sheet is the controller's, and I did not edit it.

## Reviewer can skip

Nothing generated changed.

## Concerns

None new. "“Small team” isn't part of any skill ESCO lists as essential for an occupation,
so it found no work." is true but odd for how someone likes to work (the re-review's session
W2 item, unchanged).

# Fix round 5

From `b2aa090`; dispatch `task-W2B-fix-round-5.md`, re-review `task-W2B-rereview-4.md`.
Implementer: Claude (Opus 5.5), fresh. No subagents, no live model call, no web request, no
Docker pull (the test stack from cached images, torn down after), no headed browser,
`spikes/world` and the running `careerwright-l0-*` stack untouched, `answers-2.md` not staged,
DBOS `application_version` still `careerwright-l0-1`. Commit: `166e4ef`. Words, the web
count and tests only: no matching rule, threshold, rank, API field or migration changed; the
generated client is unchanged.

## Status

DONE. Every "Fix now" item is done with a test that fails without it; the controller's
ruling is applied to every slate note and reason in this slice (list below); `make check`
and one `make acceptance` pass on the committed code.

## What changed

**I1, as ruled: a note says what the search did, never what ESCO contains**
(`exploration._missed`, `_missed_notes`). A search reads the main name of each skill an
occupation lists as essential, never its other names, so:
- own words: "No main name of a skill ESCO lists as essential holds all the words of
  “operating farm machinery”, so it found no work." (the controller's example, with the
  person's words as written)
- a model's searches: "“Fixing things” found no work: no main name of a skill ESCO lists as
  essential holds all the words of its search “repair machinery”." (several: "any of its
  searches “repair machinery” and “fix equipment”")
- two cases the old sentence also covered, where it was untrue because nothing read a skill
  name: a search of only common words ("“All of it” has only common words, which
  Careerwright doesn't search for, so it found no work.") and a model's search naming the
  person's own title, answered by its skill join ("... Careerwright found no other occupation
  in ESCO that shares 3 or more essential skills with its search “warehouse manager”, your
  own title"). `compute_slate` now passes the join query IDs (`joins`).
- too general, occupations: "“Writing reports” reached 217 occupations in ESCO through the
  main names of their essential skills, too many to choose from on its own. ..."
- too general, skills: "“Training staff” matched the main names of 10 different essential
  skills in ESCO, none of them just those words, so it's too general ..."

**M1** (`_general_note(query, skills, queries)`): a model's too-general note adds
"Careerwright would need a narrower search to find work from ..." only for the answers no
other search (not too general, reaching something) found work from.

**M2** (`Directions.tsx`): "found by N searches of ESCO" counts `!too_general && reach > 0`.

**M3** (`tools/evaluation.py`, `missed_answers_named`): a one-word work style among the
case's answers named in a "found no work" note is `wrong`.

## Every note and web line checked against the ruling

Changed (each claimed something about ESCO's contents beyond what was read):

| Where | Before | After |
|---|---|---|
| missed note | "isn't part of any skill ESCO lists as essential for an occupation" | what the search read (above) |
| too-general note | "is part of the essential skills of 217 occupations in ESCO"; "is part of 10 different essential skills in ESCO, none of them just that" | "reached ... through the main names of their essential skills"; "matched the main names of 10 different essential skills in ESCO, none of them just those words" |
| join note (`_join_note`) | "“Data analyst” shares 3 or more essential skills with 47 other occupations in ESCO. Careerwright keeps the 30 ..." | "Careerwright found 47 other occupations in ESCO that share 3 or more essential skills with “data analyst”, and keeps the 30 with the largest share of essential skills in common." |
| first slate, empty join | "No other occupation in ESCO shares 3 or more essential skills with ..." | "Careerwright found no other occupation in ESCO that shares 3 or more essential skills with ..." |
| unmatched title (`_unmatched`) | "“X” isn't a title ESCO lists, so ..." | "Careerwright couldn't match “X” to an occupation in ESCO, so it can't join other work to that title by shared skills. ..." (the match folds case, punctuation and plurals) |
| ambiguous title (`_ambiguous`) | "ESCO lists “X” as the title of 2 occupations, so ..." | "Careerwright matched “X” to 2 occupations in ESCO, so ..." |
| "Why this could suit you", the person's own title | "ESCO lists it as this occupation." ("it" is the person's words, matched folded) | "Careerwright matched it to this occupation in ESCO." |
| web, unsupported title ideas | "Titles Careerwright thought of that ESCO doesn't list, so not suggested:" | "Titles Careerwright thought of but couldn't match to an occupation in ESCO, so not suggested:" |

Checked and kept, each true by construction (it reads a value from the record or relation it
names, or speaks of the search or slate):
- why lines: "ESCO lists N of the same essential skills for both, so Careerwright joined them
  by those skills." (that pair's relations); "Careerwright searched for “q”, and ESCO lists
  “skill” as an essential skill for this work." (the hit's own relation); "Careerwright
  thought of this title from it, and ESCO lists it." ("it" is the card's title, ESCO's own
  main name for the record)
- might not suit: "ESCO lists N essential skills ..." and "ESCO marks this as a regulated
  profession ..." (the record's count and flag)
- the connection: "These are the skills ESCO lists for both roles." (read from both records)
- the release note (about releases, hedged: "may have changed")
- the work-style, small-pool, empty-slate, "Only N occupations matched ...", family-limit,
  exclusions and emphasis notes (about the search or slate)
- web: "found by N searches of ESCO", the too-general mark, "Searching ESCO for occupations
  that fit your answers", "Ranking the occupations ESCO returned", "Up to six occupations from
  ESCO, found from your own answers ..."

Not in this slice, not changed (for the controller): the early sketch's resolution words in
`vocabulary.ts` ("Your own title, not in ESCO", "Several ESCO occupations have this title"),
the provisional concept's source label ("A title you confirmed that ESCO does not list",
`profile/concepts.py`), and the OpenAPI field descriptions in `discovery_schemas.py` ("Titles
Careerwright thought of that ESCO does not list"), which are developer docs, not shown to the
person. The type-ahead's "ESCO doesn't list that title. Is it one of these?" is only in the
ADR and a code comment; nothing renders it yet.

## Rulings I made

1. **Scope of the rule**: every slate note and reason, and the one why line whose claim was
   about the person's words. A why line that cites a value read from the record it shows is
   evidence, true by construction, and stays.
2. **A model's wording leads with the answer** ("“Fixing things” found no work: ...") so
   each kind of search says what it did in one clause; own words keep the controller's form.
   The person's words are quoted as written mid-sentence ("“operating farm machinery”"), not
   capitalised as in the example.
3. **Common-words and join searches** get their own clauses rather than the main-name claim,
   which would be untrue of them.
4. **M1 applies to the model wording only.** The own-words "Say more about it" is advice,
   not a claim, and is unchanged. "Found work" means a search not too general that reached
   something (a join or title idea included).
5. **M3 reads one-word styles from the case's answers**, so it also covers a style the
   product never searched.

## Changed tests and inputs (disclosed)

- `tests/domain/test_slate.py`:
  - `test_the_notes_say_what_a_model_s_searches_checked_and_which_answers_found_no_work`:
    expected words are the new wording (I1); calls take the new arguments (`joins`,
    `queries`); new M1 case ("write inspection reports" from the same answer found work, so
    no narrower search). Same assertion shape.
  - `test_the_pool_counts_what_a_join_reached_past_its_cut_and_its_own_bound`: the join
    note's expected words (the ruling).
  - New: `test_an_answer_whose_searches_read_no_skill_name_is_named_for_what_they_did`,
    `test_a_title_of_the_person_s_own_says_careerwright_matched_it`.
- `tests/eval/test_evaluation.py`: the synthetic note strings fed to `missed_answers_named`
  and `general_searches_add_only`, and the synthetic why line and reason in the
  ambiguous-title test, use the new words; those checks read only "found no work", the
  quoted text and `ambiguous_titles`, so the old strings were only stale. New assertion
  (M3): "“Practical” found no work: ..." fails as THIN_EVIDENCE.
- `tests/integration/test_evaluation.py`: the five general answers' expected words (the
  parameter `reach` became `did`; same assertion); "taking pictures"'s expected sentence;
  new `test_an_answer_that_is_another_name_of_an_essential_skill_is_named_for_what_was_read`
  (full release: the other name is essential for 8 occupations; no essential skill's main
  name holds words starting "oper", "farm" and "machin", checked independently of the
  search; reach 0; the note's exact words).
- `Directions.test.tsx`: the join note string; new `it.each` for M2 ("1 search" with a
  search that reached nothing and a too-general one beside the finding one; "2 searches"
  with one more finding search).

## Tests and checks

RED on the unchanged code, then GREEN:
- `test_slate.py`: 4 RED (`_missed_notes() takes 3 positional arguments but 4 were given`
  twice; "ESCO lists it as this occupation."; the old join note), then all 54 of
  `test_slate.py` and `tests/eval/test_evaluation.py` GREEN.
- `tests/eval/test_evaluation.py`, M3: RED (`[] == [THIN_EVIDENCE]`: the old check passed a
  style named as "found no work"), GREEN.
- `Directions.test.tsx`, M2: both cases RED on the old count (the search that reached
  nothing counted), GREEN; the test file was unchanged between the two runs.
- The "operating farm machinery" full-release test: GREEN only; the old sentence for it is
  the re-review's `_missed_notes` output, and the domain RED covers the wording.
- Checked outside the repository with the backend's Python: in the pinned ESCO v1.2.1 CSV,
  "operating farm machinery" is an other name of "operate agricultural machinery", essential
  for 8 occupations (the ADR states it).

Focused integration run (test stack, real PostgreSQL 16.15, full release):
`tests/integration/test_evaluation.py`, 15 passed (30 s), all 19 discovery cases included
(so `missed_answers_named`'s new style rule passes DSC-01, DSC-03, DSC-07 and DSC-18).

`make check`, exit 0: ruff format (323 files) and lint clean, mypy clean, pytest 1,550
passed / 329 deselected, fixture validator passed; web: client matches the OpenAPI document,
Biome clean (after one formatting fix in `Directions.tsx`), `tsc` clean, Vitest 303 passed
(34 files).

`make acceptance` (none running, checked with `pgrep`), one run on the committed code:
pytest `-m "integration or stack"` 329 passed (8 min 46 s), Storybook build completed,
Playwright 42 passed (5.7 min), exit 0. Neither known flake occurred. One ADR sentence was
edited during the run (an unverified "(6 occupations)" removed); no code or test changed
after it started.

## Live calls

None. Cost $0.

## Not run / for others

- `discovery-queries-3` is still untested live (R5), so the model wording of every note has
  not met a real model's searches.
- Human (not run — requires human; session W2): the words of every note changed here.
- The re-review's session W2 items stand: searches read only main names (searching other
  names would be a matching change), and "added weight" on the web.

## Reviewer can skip

Nothing generated changed.

## Concerns

1. A note for an answer whose searches did several kinds of thing at once (a main-name
   search, a common-words search and a title join) is one long sentence. It is rare: it
   needs a model to write all three from one answer.
2. `missed_answers_named` would fault a model search whose text is itself a one-word style
   quoted alone (a search "practical" from a task). The product never writes one; a model
   could.
