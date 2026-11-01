# Task 6e review: research this role, the synthetic school leaver, session W2's package

Reviewer: independent (R16, experience and code together). Range 7ebb214..394c263, main tree
`/home/user/careerwright`, read only. I read the brief (Global Constraints and the Task 6e
section), the dispatch, the report (treated as unverified claims), and then the diff in passes:
(1) backend role research, corroboration, store, migration, API; (2) the acquisition, page and
search changes; (3) the web (`RoleResearch.tsx`, `Directions.tsx`, `queries.ts`,
`vocabulary.ts`); (4) the evaluation cases, the school leaver card, the live tool and Makefile;
(5) the ADR lines, the register and `docs/reviews/session-w2.md`. I skipped `src/generated/**`.

I did not re-run the suites. I ran one offline probe through the backend venv (no network, no
writes) to settle two named doubts: copy folding with ordinary page chrome (risk 2) and hidden
text (risk 3). Outputs are quoted under I1 and M1.

Not run, Docker down: integration (`tests/integration/test_role_research.py`), `make acceptance`,
DSC-21 on the full release, Playwright, Storybook. Not run, controller's: both live runs. Not run
— requires human: session W2, every item.

### Spec Compliance
- ❌ Issues found:
  - Copies of one advert can count as two sources, and one site's two subdomains as two
    independent sources (I1, `backend/src/careerwright/evidence/corroboration.py:91`, `:145`).
  - Role pages leak into the Jobs chapter's coverage and its empty reason (I2,
    `backend/src/careerwright/evidence/store.py:476`).
  - The live tool can lose the ledger row of a paid call (I3,
    `backend/tools/live_role_research.py:165`).
  - Session W2's persona "whose role is on no list" uses a title the option pack holds (I4,
    `docs/reviews/session-w2.md:62`).
- ✅ SEC-05: the role prompt is exactly `{"role": title, "country": "England"}`
  (`search.py` `render_role_prompt`). Only `RoleSearchInput` is sealed into the run
  (`role_research.py:131-147`). Pages are read by the restricted worker through
  `acquire_page`/the guarded fetcher (`acquisition.py` `acquire_target` → `rt.client.fetch(...,
  read_text=True)`). The class comes from the manifest by final host (`acquire.py`
  `_page_result`). The worker is never told the title.
- ✅ Run kind: no new kind. The search is `SOURCE_SEARCH` through the same `RunTask` and its
  bound. The reading is an ordinary keyless acquisition. Both can be cancelled. No workflow step
  changed, so `application_version` stays `careerwright-l0-1`. Migration 0042 is forward-only,
  with CHECKs and row-level security on both new tables. The worker's insert policy is limited
  to its own run's attempts.
- ✅ Blocked or failed pages are never counted as "none found". An attempt without a check is
  left out of the rule (`role_research.py:319-328`). A failed or cancelled reading is
  `reading_stopped`. A complete reading shows its unread pages separately (`ROLE_RESEARCH.unread`).
- ✅ The school leaver: card `fixtures/synthetic/school-leaver.json`, labelled synthetic, with
  no job title and no income. `fixtures/m0` is unchanged (empty diff). INT-16 and INT-17 run on
  the demo interviewer. STR-01 and STR-02 go through the product's `check_strength`.
- ✅ Duties and entry requirements are deferred, with reasons, in ADR 0015's Task 6e line.
- ✅ Childline is held as "to add when Childline's details are checked". Every record-sheet row
  says "not run — requires human".
- ⚠️ Cannot verify from diff: the integration tests and acceptance (Docker down); DSC-21's
  `nothing_close_to_now` on the full release; whether the ONS index lists "Bookkeeping
  assistant" (`var/datasets` absent); the live search's candidate quality.

### Strengths
- The rule is pure and small (`corroborate`). Each page's class comes from the manifest, never
  from the page. No model reads a role page, so a page's instructions really can change nothing.
- "Found stays found; not yet found needs a complete reading" is the right asymmetry. Unread
  pages are worded as "isn't counted either way".
- The vocabulary keeps to "what Careerwright checked". Neither result says whether a role exists.
- `role_page_checks` keeps only a hash, the span, an excerpt of 200 characters or fewer, and a
  passage fingerprint. CHECKs enforce that these appear together.

### Issues

#### Critical
None.

#### Important

**I1. Copies of one advert on two hosts usually count as two sources. A model's title idea can
then show as "found" and be made a target.** [truth]
`backend/src/careerwright/evidence/corroboration.py:87-92` (passage from the first occurrence
only), `:136-139`, `:145`.
- What: the passage fingerprint covers the title's *first* occurrence plus the next 24 words. On
  real pages, the first occurrence is usually the page's `<title>`, a breadcrumb or a heading,
  and site chrome follows it. So two copies of the same advert get different fingerprints, and
  only structured `JobPosting` data can fold them.
- Probe: one identical advert body on two boards, each with an ordinary `<title>` and nav,
  gave `Corroboration(verdict=FOUND, sources=2, groups=[['a'], ['b']])`.
- Why the test missed it: the fixture `test_two_copies_of_one_advert_on_two_hosts_count_once`
  puts the chrome *before* the title, so it passes.
- Second gap: independence is by exact host. `www.example.org` and `careers.example.org`, one
  organisation, count as two independent sources whenever their passages differ.
- Why it matters: the brief's acceptance says "two copies of one advert leaves it not yet
  found" (ADR 0009 decision 6). A false "found" makes an uncorroborated idea choosable as a
  target. ADR 0015 records only "a copy reworded around the title", a much narrower limit than
  "any page with chrome after its title".
- Fix:
  - Fingerprint the passage at every occurrence of the title (a bounded number), and fold two
    pages when any fingerprint is shared.
  - Compare sources on the registrable domain (or at least strip `www.`) rather than the full
    host.
  - Add tests where the title appears first in `<title>` or nav with different chrome on each
    host, and one for two subdomains of one site.

**I2. Role pages count as job sources in the Jobs chapter.** [truth: failure shown as an
empty success]
`backend/src/careerwright/evidence/store.py:476-478` (`coverage` reads every `source_attempts`
row except pasted text), consumed at `evidence/acquisition.py:723` and in `_empty_reason`.
- What: the role branch in `acquire_target` skips postings and extraction, but its attempts are
  still ordinary `source_attempts`.
- Effect, for a person who never searched for jobs:
  - A role page with no readable posting makes the Jobs chapter say `no_posting_readable`.
  - A role page with a `JobPosting` counts as `succeeded` with no job recorded, which gives
    `none_found_in_sources_checked`. That is "none found" for a search that never ran.
  - A reading in flight shows `sources_pending`.
  - `DISTINCT ON (requested_url)` also lets a role attempt mask a job attempt on the same URL.
- Tests: the integration test checks only `total_jobs == 0`.
- Fix: leave out attempts whose target carries `role_title` (join `acquisition_targets` on
  run and position) from `coverage` and any other per-workspace attempt query. Add an
  integration assertion on `coverage` and `empty_reason` after a reading.

**I3. `make live-role-research` writes the ledger row only after the page reads.** [truth:
false evidence record, R5]
`backend/tools/live_role_research.py:165-167`, before `ledger.append` at `:167-187`.
- What: the model call is already paid. If anything raises while up to five real pages are
  fetched and parsed (an unexpected exception in redaction or parsing, or Ctrl-C during
  pacing), the row is never written. The docstring says it is ledgered "whatever happens".
- Why it matters: this is the controller's next live run.
- Fix: append the row (or a provisional row) before reading, then record the page notes. Or
  wrap the reads so the row is always written, with page failures recorded in the notes. Add a
  test with a reader that raises.

**I4. Session W2's persona "whose job is on no list" uses a title a Careerwright list holds.**
[truth: false statement in the package]
`docs/reviews/session-w2.md:62-79`; the title is the option pack's target
(`backend/src/careerwright/catalogue/packs/england_option_pack/england-option-pack-0.2.0.json:15`,
`bookkeeping-assistant-leeds`, persona P05).
- What: "Sam's job is on no list Careerwright holds" is false. The pack covers it, so the app
  will show pack coverage for it. If the ONS index also lists it (I can't check here: no
  datasets), the role record becomes an ONS title. Then "Research this role" is not offered,
  and the API would refuse it anyway.
- Why it matters: the session's one research walkthrough could fail, live and paid. The brief
  asks for "one whose role is on no list".
- Fix: pick a title checked against ESCO labels, the imported ONS index (`uk_titles.listed`)
  and the pack's targets before the session, and record that check in the package's notes.

#### Minor
- M1 (list) Hidden text counts as visible.
  - Where: `backend/src/careerwright/evidence/pages.py:300-301`, `role_text`.
  - Probe: `display:none`, `hidden`, `<noscript>` and `<template>` content all appear in
    `role_text`.
  - Tests: no test covers hidden text, a title at the start of a longer word (left boundary),
    or punctuation and apostrophe forms. Case and the right boundary are covered.
  - Docs: the docs say "visible text". Either drop hidden elements or record the limit.
- M2 (truth) "Titles no list holds" can list a title ESCO holds.
  - Where: `apps/web/src/components/Directions.tsx` `researchable()`.
  - What: own-words targets with an exact ESCO label keep kind `own_words`
    (`profile/targets.py:338`, `link: exact_label`). Clicking research is then refused with
    `VALIDATION_FAILED`.
  - Fix: filter on `label_matches === 0`, or have the API expose researchability.
- M3 (truth) A model's idea gets relabelled as the person's own words once it is made a target.
  - Where: `Directions.tsx` `researchable()` (targets before ideas); `RoleResearch.tsx:224,245`.
  - What: the label becomes "Your target, in your words", and "Saved as one of your targets"
    is never shown.
- M4 (list) Problems while the state is `ready_to_read`.
  - Where: `RoleResearch.tsx:32,100-109,146-157`.
  - What: "Stop" is offered for the already complete search run. If the read request fails,
    "Reading the pages the search found…" stays with no retry and no "Research again".
- M5 (list) Research needs a discovery first.
  - Where: `Directions.tsx:833`; it lives under the slate.
  - What: a person whose own title is on no list can still choose it, so this is not a dead
    end. But they can't research it without first running a paid discovery.
  - Question for session W2: should research sit beside the role in the You chapter?
- M6 (list) What goes into `read_role_pages`'s plaintext receipt.
  - Where: `backend/src/careerwright/api/routes_research.py` `read_role_pages`.
  - What: the receipt holds the model-proposed candidate URLs (as `pages[].url`), and on a
    repeat call possibly page quotes. CLAUDE.md says receipts never carry model output.
  - Also: the reading takes no expected version (disclosed, ruling 2).
- M7 (list) "It sends only the title and “England”, nothing about you."
  - Where: `apps/web/src/lib/vocabulary.ts` `ROLE_RESEARCH.sends`.
  - What: when the title is the person's own role words, the title itself is about them.
    "nothing else about you" is exact.
- M8 (list) Session package details.
  - Where: `docs/reviews/session-w2.md:28-29,83`.
  - What: Maya is played in a workspace not marked synthetic. Suggest naming it
    "Maya (made up)" so she stays labelled. "This is P02 from the test pack" is an internal
    code the product owner doesn't need.
- M9 (list) The live tool doesn't exercise the restricted worker boundary.
  - Where: `backend/tools/live_role_research.py:77-80`.
  - What: it fetches real pages in the same process that holds the Meta key, not through the
    restricted worker's HTTP boundary. The acceptance evidence covers the code, not the
    deployment boundary. Say so in the evidence.
  - Also: the Makefile's `--title "$(TITLE)"` is unescaped shell.
- M10 (list) Inaccurate or misplaced comments, and misleading counts.
  - `apps/web/src/lib/queries.ts`: the `useTargets` doc comment now sits above
    `useRoleResearch`.
  - `role_research.py:274`: the comment "every page read" is inaccurate.
  - The acquisition summary's `no_posting_readable` counts are meaningless for role runs.
- M11 (list) Experience: "Titles no list holds" is a plain list of cards with buttons. It works
  as a practical working view, but it has no moment yet (for Task M).

### Assessment
**Task quality:** Needs fixes
**Reasoning:**
- The core is sound: SEC-05 holds, no model reads pages, the class comes from the manifest,
  failed pages are never shown as "none found", and the run kind and DBOS version are
  unchanged.
- But copy folding (I1) misses the ordinary case of chrome after the title, so "found" can
  rest on one advert.
- Role pages corrupt the Jobs chapter's coverage (I2).
- The live tool can drop a paid call's ledger row (I3), and session W2's key persona uses a
  listed title (I4).
- All four are truth findings to fix now. The Minors are for the list, apart from M2 and M3,
  which are truth-tagged.
