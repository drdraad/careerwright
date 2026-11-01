# Task W2, slice W2B: re-review of fix round 1 (f70f88d..e8c0bfb)

Reviewer: Claude (Opus 5.5), scoped re-reviewer. Read-only on the repository: no edits, commits
or staging, and the working tree is unchanged at `e8c0bfb`. No subagents, live model call or
web request.

**Disclosure:** I ran a throwaway PostgreSQL 16.15 container to load the pinned release. The
`postgres:16.15-bookworm` image was not cached under that tag, so Docker pulled it from Docker
Hub. That is a network fetch I did not intend. No product data or key was involved, the
container used synthetic passwords on a random loopback port, and I removed it afterwards. The
image is still in the local Docker cache.

## How I checked

- Read the reviewer contract, the dispatch, the review (I1–I5, M1–M9), the report's "Fix round
  1" section and the whole package diff (24 files), in six passes. Read the code outside the
  diff only for named risks: the fixture proposer, slate scoring, pool folding and `explain`,
  `compute_slate` and `first_slate`'s `facts`, `open_output` and the run-output constraints,
  `titles.targets`, `test_slate.py`'s bound test, and the register row DIV1-02.
- `make check` on `e8c0bfb`: exit 0. That covers ruff format (323 files) and lint, mypy (323
  files), pytest 1,534 passed and 316 deselected, the fixture validator, and the generated
  client matching OpenAPI. On the web side, Biome, `tsc` and Vitest (299 passed).
- The pinned ESCO v1.2.1 loaded through the repo's own `migrate_app` and `import_taxonomy` into
  that throwaway database (3,039 occupations, 13,939 skills, 67,600 essential links).
  - Every discovery case run through the repo's own `observe_discovery_offline` and `evaluate`.
    This reproduced the report's P01 and P02 after-slates exactly.
  - The diff's own SQL run for matches, ties and the closest-titles list.
  - Sixteen everyday profiles run through the same path.
  - The candidate rules below patched in-process only, in scratch scripts outside the repo.
- Not run: `make acceptance` and the integration suites (the controller's), live calls (none
  allowed), and every human item ("not run — requires human").

## The question that matters: do the after-slates still read as arbitrary?

**Yes.** Read as the product owner would:

- **P01** wants to be a data quality analyst. They enjoy "finding inconsistencies" and
  "explaining evidence", and like work that is "structured" and "collaborative". The slate
  offers a dental practitioner, an ICT information and knowledge manager, an advertising
  installer, an agronomic crop production team leader, an artistic coach and a carpenter. Each
  line now spells out the link: "structured" to "soil structure", "install wood elements in
  structures" and "risks of elevated advertising structures"; "finding inconsistencies" to
  "interpret findings from medical examinations". Naming the skill makes the keyword match
  more obvious, not less.
- **P02** (repairing physical objects, working outdoors): the six are a deep-sea fishery
  worker, fisheries observer, fruit and vegetable picker, pesticides sprayer, landscape
  gardener and leaflet distributor. All six come through "work in outdoor conditions". Each is
  defensible on its own, because that skill says the person's whole phrase. But the slate
  ignores "repairing" and reads as "anything outdoors": thin rather than arbitrary.
- **"Looking after people"** (DSC-07/08) offers an animal behaviourist ("deal with challenging
  people"), an animal shelter worker ("interview people"), a secretary and an administrative
  assistant ("disseminate messages to people"). That is arbitrary.
- **Everyday answers**, beyond the cases, show the same pattern:
  - "caring for patients, giving injections" gives an aesthetician ("give massages"), an
    advertising manager ("give interviews to media"), an air force officer ("give
    instructions to staff") and an injection moulding operator.
  - "teaching children, writing stories" gives an aquaculture mooring manager and a corrosion
    technician ("write technical reports").
  - "designing websites, writing code, collaborative" gives three web roles, then an
    aquaculture harvesting manager, an aquaculture mooring manager and an acupuncturist.

Three mechanisms cause this. I checked each against the release.

1. **Any one word is enough.** `_search_hits` still runs an any-word pass
   (`backend/src/careerwright/profile/exploration.py:479`), scored up to 0.5, above the 0.35
   floor. A phrase therefore reaches a skill through a single word, often its verb (give,
   write, find) or "people". Of the persona and case phrases, only "working outdoors" and
   "repairing bicycles" have a skill label that holds every word. Every other match is
   single-word.
2. **One-word work-style answers match on their English stem.** "structured" matches
   structure, structures and structural (33 skills, 73 occupations). "practical" matches
   "practices" (69 skills). "collaborative" matches "collaborate" (26 skills).
3. **Ties are cut alphabetically.** This is new in this round's SQL. Every occupation reached
   through the same skill, or through any label holding the same number of query words, gets
   the same rank. `essential_skill_reach` then orders by `text_rank, skills, preferred_label`
   and keeps 30 (`backend/src/careerwright/catalogue/taxonomy_store.py:265`, `QUERY_HITS`
   `exploration.py:128`).
   - P01's "structured": all 73 occupations tie on rank. Four are kept for matching two or
     more skills; the other 26 kept run alphabetically from "advertising installer" to
     "dental practitioner", and the 43 cut run from "editorial assistant" to "web content
     manager".
   - "giving injections": 196 occupations tie, and the 30 kept run from "academic advisor" to
     "biology lecturer".
   - The slate then breaks equal relevance by title again (`slate.py:279`, `:460`).

### The smallest rule that makes each suggestion defensible

Three deterministic rules, in order of effect:

1. **A phrase reaches a skill only when every content word of the phrase is in that one
   skill's label** (stemmed, stop words dropped). In practice: drop the any-word pass in
   `_search_hits` (`exploration.py:479`; one line), and tighten `searched_through_skills` to
   every content word.
2. **Work-style answers do not retrieve destinations.** They describe how someone likes to
   work, not a skill. Default this to off until session W2 confirms, rather than on. In
   practice: skip a query whose `based_on` answers are all work style.
3. **Never cut ties alphabetically.** A search keeps every occupation it reaches, up to the
   pool bound (the pool's round-robin across families already bounds it). Equal scores are
   ordered by the share of the occupation's essential skills the person's answers reach, so
   work where the skill is a bigger part comes first, with the title only as the last
   tie-break. I tested the in-search half alone; ties on the slate stayed alphabetical, so the
   share must also reach the slate's ordering (`slate.py:279`).

**Effect, offline, of rules 1 and 2** (the fixture proposer, which repeats answers word for
word):

| Case | At HEAD | With rules 1 and 2 |
|---|---|---|
| P01 (DSC-12) | the six above | nothing from tasks or style. The slate gives both plain reasons: "None of your answers matched…" and "“Data quality analyst” isn't a title ESCO lists… Choose the ESCO occupation closest to it". The type-ahead now offers data quality specialist first; choosing it gives DSC-02's skill-joined slate (data entry clerk, big data archive librarian, data analyst, database designer, chief data officer). DSC-12's `size_at_least 3` must become `fewer_has_reason`. |
| P02 (DSC-01) | the six outdoor roles, pool 109 | the same six, pool 12. The integration assertion `POOL_TARGET <= pool_size` fails; DIV1-02 is soft ("where evidence permits"). |
| P03, P04, P05 | joined by title / none / none | unchanged (titles only, no searches) |
| DSC-07/08 "looking after people" | animal behaviourist, secretary, … | nothing: no ESCO skill label holds both "look" and "people" |
| DSC-03 / DSC-09 | role join / bicycle mechanic | unchanged |
| "caring for patients, giving injections" | aesthetician, air force officer, … | advanced nurse practitioner, nurse responsible for general care |
| "teaching children, writing stories" | aquaculture mooring manager, … | nothing |
| "designing websites, writing code" | 3 web roles plus aquaculture ×2 and acupuncturist | web designer, webmaster, web developer |

- **On the live path**, the model writes the queries. Short phrases in ESCO's skill wording
  reach work under rule 1: "data quality" reaches 35 occupations, "data cleansing" 6, "plan
  shifts" 58 and "present evidence" 3. Paraphrases reach none: "care for people", "explain
  findings", "schedule shifts". So the discovery prompt should ask for short phrases in ESCO's
  skill wording (a new prompt version; the controller's call).
- **Cost:** offline slates for P01 and "looking after people" go empty, with their reasons, and
  P02's pool falls below the soft 60. That is honest emptiness instead of filler, which the
  plan prefers.
- **What remains for session W2:** a one-word *task* answer still matches on its stem.
  "driving" reaches "comply with policies for trolley bus driving", and "drawing" reaches "read
  engineering drawings".
- **Not recommended: a cap per matched skill.** As a per-search cap of 2, it kept the
  alphabetically first two per skill (P02 became ceramicist, automotive battery technician,
  building cleaner, camping ground manager). As a cap on the slate, it cuts P02 to two and
  fails DSC-01's size and families checks. Either way, no suggestion becomes more defensible.

## Each finding in the fix dispatch

| Finding | Status | Evidence | Can its test fail? |
|---|---|---|---|
| I1 (title words reach the slate) | **Fixed** | Non-title searches use `skills.search_vector`, a generated column over each skill's preferred label (migration `r0032_essential_skill_search.py`, filled for the held release by the migration). No title, hidden label, ISCO label or description is searched (`taxonomy_store.py:242-280`). Model queries are matched to the person's titles with `concept_key` (`exploration.py:702-705`). ADR 0007 decision 13 is amended (`docs/adr/0007-…:534-547`). | Yes. DSC-15 (`evaluation_cases.json:570`) fails if "Data analysts" is word-searched: those suggestions carry no shared-skill line, so `joined_by_skills` fails. `test_0032…` (`test_migrations.py:281`). |
| I2 (fix the slate where it matches on words) | **Partly fixed** | Descriptions and group titles are gone, and each suggestion names its skill. But it still matches single words of skill labels (`exploration.py:479`), and ties are cut alphabetically (`taxonomy_store.py:265`; new issue I-B). See the section above. | `searched_through_skills` can fail (unit test `tests/eval/test_evaluation.py:215`), and it caught new issue I-A. But it accepts a single shared word (`tools/evaluation.py:86,345`), so it cannot catch what the product owner rejected. |
| I3 (declined strength returns) | **Fixed** | The run reads only answers that are in the turn's version and not in the one before (`strengths.py:128-145`, `:223`). `no_quotable_answer` when none is quotable. Nothing new is stored. A removal no longer passes (M9). | Yes. `test_origin.py:401`. The report's RED, with the old `strengths.py`, is consistent with the code: the scripted answer would re-enter the input. Minor edge in new issue M-E. |
| I4 (demo strength is a word match) | **Fixed** | A fixed table, `SCRIPTED_STRENGTHS` (`strength.py:409`), matched exactly on the answer; no word overlap. It finds the skill by label (`:446`). I checked that all four labels are unique among ESCO's 13,939 skills, and that no two skills share a label. | Yes. `test_strength.py:196` ("Fixing bikes" has no shared word, so the old fixture would fail it; "repairing bicycles" must find none). Full-release URI and label check at `test_evaluation.py:76`. |
| I5 (closest titles) | **Fixed** (with order caveats, new issue M-B) | `partial_title_matches` (`taxonomy_store.py:365-401`), used for two to eight words with no every-word match (`taxonomy.py:196`). `partial` is in the client, and `make check`'s drift check passes. I reproduced the lists: P05 gets the bookkeeper first and P01 the data quality specialist first. P04 gets a sales support assistant first. | Yes. `test_first_answer.py:168` (before the fix, these returned nothing). |
| M1 (timings) | **Fixed** | "a", "s", "c" and the two heaviest roles are timed and asserted under 1 s (`test_first_answer.py:82,134`). Numbers are in ADR 0007 decision 14. | It asserts under 1 s, so it catches gross regressions only (accepted). |
| M2 (connection on an ambiguous role) | **Fixed as ruled** | No connection unless the role names exactly one occupation (`exploration.py:838`). The unguarded `facts[...]` is safe, because the role's occupation is always in `found` (`compute_slate`, `first_slate`). The union join remains (new issue M-A). | Yes. DSC-16 `no_connection` (`evaluation_cases.json:587`). |
| M3 (complete run with no output) | **Fixed**, untested | `_view` raises `INTERNAL_ERROR` (`strengths.py:104`). See below for why no test is needed. | Not tested (justified). |
| M4 (test gaps) | **Fixed** | The strength's own failure path and a decision on a failed run (`test_origin.py:546`); stale capability version and answers changed after the turn (`:582`); the `recite` path (`:214-228`). | Yes. Each asserts specific codes and that nothing is stored. |
| M5 (person's title kept) | **Fixed** | `ChooseRole.label` must be one of the occupation's ESCO titles, and the role resolves by URI (`exploration.py:1060`). | Yes. `test_origin.py:231` (a foreign title gets 422; the picked title is kept). |
| M6, the ADR part now | **Fixed** | ADR 0007 states why three, from release statistics, and ties every provisional rule, including the closest-titles order, to session W2. | Not applicable |

Counts: **0 not fixed, 1 partly fixed (I2), 0 regressed.**

## New issues

### Critical

None.

### Important

**I-A. A folded near-identical role's skill is shown as this occupation's own.**
`backend/src/careerwright/profile/slate.py:352` (the pool's lead "carries every query that
found any of them"); `backend/src/careerwright/profile/exploration.py:579` (`explain` names
`match.skill` from any merged match).
- **What:** reproduced at HEAD, unpatched, with an everyday profile ("playing music",
  "recording songs", "creative"). The sound designer's line says "ESCO lists ‘attend music
  recording sessions’ as an essential skill for this work". That skill is essential to the
  sound editor, which was folded into the sound designer as a duplicate, and not to the sound
  designer. The round's own `searched_through_skills` check fails on it. A second instance
  appeared under the candidate rules (product development manager, "organise participation in
  local or international events").
- **Why it matters:** a stated fact about an occupation that ESCO does not support ("the world
  never shows more than the evidence"). It is new because this round makes the line name a
  skill; before, it said "ESCO's record for this occupation matched". The shared-skill count
  line has had the same root cause since f70f88d.
- **Fix:** keep the hit's own occupation on `Match`. Name a skill only from the lead's own
  matches, or name the folded role ("ESCO lists ‘…’ for the sound editor, a near-identical
  role"). Test with two aliases, one reached through a skill only it lists. Add this profile as
  a discovery case.

**I-B. Ties among occupations reached through the same skill are cut alphabetically.**
`backend/src/careerwright/catalogue/taxonomy_store.py:265`;
`backend/src/careerwright/profile/exploration.py:128`; `slate.py:279,460`.
- **What:** per-skill ranks are identical for every occupation a skill reaches, so the 30 kept
  are the first 30 by title (figures in the section above). This survives rules 1 and 2:
  "plan shifts" reaches 58, "analyse data" 92 and "maintain equipment" 242.
- **Why it matters:** the selection is decided by the alphabet, which is arbitrary in the most
  literal sense. On P01's slate, advertising, agronomic and artistic all come from it.
- **Fix:** rule 3 above. Add a test with more than 30 occupations through one skill: the kept
  set must not depend on title order, and must include any occupation that meets a second
  answer.

### Minor

**M-A. A title several occupations share is joined over their skills together, and the count
it states can be true of neither.** `exploration.py:507-520` (`_joined`) with
`taxonomy_store.py:416`.
- For "bus operator", the taxi driver's line says "ESCO lists 14 of the same essential skills
  for both". It shares 13 with the bus driver and 9 with the trolley bus driver. ESCO has
  1,051 titles that name two or more occupations.
- The role is asked about at the origin, but a target title gets no "which did you mean?"
  step (`titles.targets`).
- **Fix:** do what the first slate does and ask which, or join each occupation separately and
  name it.

**M-B. The closest-titles order shows P04 the wrong things first.**
`taxonomy_store.py:375,396`.
- "Registered nurse" lists a sales support assistant first ("registered sales assistant") and
  a dental hygienist second; the nurse responsible for general care comes eighth.
- Because a complete word "nurse" is matched as a prefix, it finds "nursery". Six of the 20
  come only from that: nursery school head teacher, diet cook (nursery cook), early years
  teacher (nursery teacher), flower and garden shop manager (nursery shop manager), child care
  worker (nursery school worker) and early years teaching assistant (nursery teaching aide).
- ADR 0007 records this honestly for session W2 (`:513`).
- **Fix:** in the fallback, put whole-word matches before prefix-only ones, and don't count a
  short list of status words ("registered", "senior", "junior", "trainee", "qualified",
  "chartered", "certified", "licensed").

**M-C. The pool bound has no full-release evidence any more, and DIV1-02's register row is
stale.** `backend/tests/integration/test_evaluation.py:71`; `docs/requirements-register.md:126`.
- The assertion's upper half cannot fail, because `build_pool` never exceeds its limit. The
  lower half (at least 60) is real.
- No discovery case now exceeds the bound (all show "beyond 0"). The cut is still unit-tested
  (`backend/tests/domain/test_slate.py:234`).
- The register row still cites "P02 … fills the pool to 120 with more beyond it".
- **Fix:** assert `pool_size >= POOL_TARGET` only, and point the row's evidence at the unit
  test. Rules 1 and 2 would also break the lower bound for P02 (12).

**M-D. `searched_through_skills` accepts any one shared word** (`tools/evaluation.py:86-100,345`).
It guards grounding, not defensibility. If rule 1 lands, require every content word of the
query.

**M-E. A moved or re-added answer counts as new** (`strengths.py:143`, keyed on field and
text). If a declined answer moves from "enjoy" to "can do", or is removed and added back, it
is offered again. Fix: compare by text alone.

## The implementer's other concerns

1. **Slates rest on skill-label words** (concern 1): agreed. That is I2 partly fixed, and new
   issue I-B. The proposal is above.
2. **Union join for a shared role** (concern 2): real, and broader than the role. See M-A.
   Small: the first question already asks which for the role.
3. **P04's closest-titles order** (concern 3): real, and there is a second cause, prefix
   matches on "nurse" finding "nursery". See M-B. It is on session W2's list.
4. **P02's pool assertion** (report ruling 6): the bound's mechanism is still really tested,
   at unit level (`test_slate.py:234`, cut at 4 with 4 left over). The new integration
   assertion's upper half cannot fail, and nothing on the full release exercises the bound any
   more. See M-C.
5. **M3 without a test:** enough.
   - `runs` has `complete_runs_have_an_output` (`status = 'complete'` exactly when `output_id`
     is set) and a foreign key to `run_outputs` (`r0002_credentials_runs_spend.py:87,111`).
   - The output row sits under the same workspace policy as the run.
   - So the branch is reachable only through corruption, and a test would have to break a
     constraint first.

## Spec compliance

- ❌ SW.5, "fix the slate where it matches on words": partly. See I2 and new issues I-A and
  I-B (`exploration.py:479,579`, `taxonomy_store.py:265`).
- ✅ Everything else the dispatch ruled: one essential-skills vector, built at import and
  filled by a forward migration; `concept_key` for model queries; DSC-15 and DSC-16; the
  evaluation check; the before and after slates recorded; ADR 0007 decisions 13 and 14 and ADR
  0014 decision 3 amended; I3, I4 and I5 as ruled; M1–M5; client regenerated;
  `careerwright-l0-1` unchanged; `identity/` untouched.
- ⚠️ Cannot verify from the diff: the report's single `make acceptance` run (316 passed; one
  W2A Playwright flake that passed on re-run); live discovery queries under the new search
  (`tools.live_eval` is live only); every human item ("not run — requires human").

## Strengths

- The ruling was implemented faithfully and cleanly. A per-skill vector makes every match one
  skill's, so it can be named. Using a generated column means no second fill path.
- The report is honest: it published slates that show the problem and named the three
  concerns itself.
- The I3, I4 and M5 fixes are small, exact and well tested. The scripted demo no longer
  matches words.
- The new evaluation check works: it found new issue I-A on its first real exposure.

## Assessment

**Task quality:** Needs fixes

**Reasoning:** Everything ruled is done and tested. But the after-slates still read as
keyword matching, through single shared words, one-word work-style stems and alphabetical
cuts among ties. A why-line can also name another occupation's skill as this one's. Rules 1
to 3 above are deterministic, small and checked against the release. Rule 2 and the prompt
wording need the controller's ruling; new issue I-A and rule 3 are fixes either way.
