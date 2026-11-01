# Task 6e: research this role, the synthetic school leaver, session W2's package — report

Main tree `/home/user/careerwright`, branch `claude/confident-ramanujan-ux3saw`, from 7ebb214.
Migration **0042** (`r0042_role_research.py`, `down_revision = "0041"`). DBOS
`application_version` unchanged (`careerwright-l0-1`): no run kind, workflow or step sequence
changed. No live call, no web request, no Docker.

## Commits
- `ec208ff` Research this role: backend (search purpose, reading, corroboration, migration 0042,
  API), the web's "Titles no list holds", regenerated client.
- `918359f` The synthetic school leaver (card) and her five evaluation cases; a `strength` case
  kind and a `nothing_close_to_now` check.
- `4315ab5` `make live-role-research` (capped, ledgered), runbook row.
- `b2d9399` ADR 0015 and ADR 0009 amendment lines (duties deferred with reasons).
- `77c1c10` Session W2's package, `docs/reviews/session-w2.md`.
- last commit: the register rows and this report.

## For the controller: the live runs (R5), after the product owner's yes
1. **The synthetic title's research run** (the card's acceptance test):
   `make live-role-research` (optional `TITLE="..."`; default "Biodiversity net gain officer").
   - In process, no stack. Test model only. One request, no repair, at most 2 tool calls:
     worst case **$0.008**. Own scope `live-role-research`: at most **3 requests and $0.10** in all.
   - Then up to five candidate pages are fetched from the real web through the guarded fetcher's
     own code (robots.txt, pacing, the manifest; no model reads them, cost $0). So it needs the
     network as well as the key.
   - One ledger row; notes hold hosts, classes, outcomes, whether each page uses the title, the
     verdict. Key scan on requests, result and row.
   - The tool doesn't check the title against ESCO or the ONS index (the product does, at
     `POST .../role-research`). Pick a title no list holds.
2. **The school leaver's interview cases on prompt version 5** (and her discovery):
   `make live-eval CASES=INT-16,INT-17,DSC-21`.
   - Test model. Worst case about **$0.010** (two interview attempts at $0.0035, one discovery at
     $0.003), under live-eval's per-invocation cap ($0.05).
   - The `live-eval` scope's cumulative $0.05 may already be used by earlier runs; if refused,
     run it in a fresh scope: `CAREERWRIGHT_LIVE_EVAL_SCOPE=live-eval-6e make live-eval CASES=...`.
   - Or drop DSC-21 to keep to the brief's "interview cases": `CASES=INT-16,INT-17`.

## What was built

### Research this role (DIV1-15; ADR 0015 decision 2; ADR 0009 decision 12, amendment)
- **The search** is the existing `source_search` run kind with a sealed `RoleSearchInput` (the
  title only) and its own instructions (`role-search-1`). The prompt is exactly
  `{"role": title, "country": "England"}` (SEC-05). Same task, bound check and reservation
  ($0.008 test, $0.045 Spark, $0.143 Wonder; three attempts fit the session's $0.75). The
  proposal records `purpose`; older sealed proposals read as job searches. Candidates are checked
  by code as before.
- **Refused:** a title ESCO holds as a label or the ONS index lists (`VALIDATION_FAILED`,
  `title_already_listed`), a stale profile version, a demo workspace (as every model run).
- **The reading** is an ordinary acquisition of up to five candidates (grounded first), started
  by `POST .../role-research/{id}/reading`. Each target carries `role_title`. The restricted
  worker is asked for the page's whole visible text (`FetchRequest.read_text`, `pages.role_text`:
  normalised, personal details removed, cut at 200,000 bytes; never told the title). The DBOS
  worker checks the title (`span_offsets`, whole words, case aside) and records only the text's
  hash, the span, an excerpt of at most 200 characters, a passage fingerprint and the page's
  structured postings' canonical facts (`role_page_checks`). No job is recorded, no extraction is
  started, no job is marked attempted; a kept body only where the class permits.
- **The rule** (`evidence/corroboration.py`, pure), decided on read: found on two independent
  sources, or one official page (`govuk`, `public-sector`, `professional-body`, by the manifest).
  Copies fold first (`jobs.same_job` across postings, or the title and the next 24 words the same).
  One host is one source unless both pages name employers and they differ.
- **States** (`ResearchState`): searching, search_stopped, no_pages, ready_to_read, reading,
  reading_stopped, found, not_yet_found (with `one_source_only` or `not_on_any_page`). A reading
  that failed or was cancelled is `reading_stopped`, never "not yet found"; unread pages are
  counted apart.
- **API:** `POST/GET .../role-research`, `GET .../role-research/{id}`,
  `POST .../role-research/{id}/reading`. Codes and counts only; each write takes an
  Idempotency-Key through `run_idempotent`; the start takes `expected_profile_version`.
- **Records:** `role_researches` (title, title key, search and reading runs, `review_state`
  CHECKed `proposed`, dated, workspace-private by RLS). CHECKs on all three changes in 0042.
- **Web** (`RoleResearch.tsx`, in Directions under the slate, live workspaces only): "Titles no
  list holds" lists the role and targets kept in the person's own words and the title ideas not
  yet found. Each shows the estimated cost (`RunEstimate`, source_search) before "Research this
  role", reads the pages as soon as the search is done, offers "Stop" while running, words each
  state, and puts every page's quote and read date one step away (a disclosure). A found title
  idea gets "Make this a target" (the profile's one write path, `PUT .../profile`).

### Duties and entry requirements (dispatch decision 3)
**Deferred with reasons in ADR 0015's Task 6e line.** One page's quotes would more than double a
role's worst case ($0.045 + $0.048 on Spark); five pages up to $0.24 ($0.72 with every attempt);
on Wonder one page (about $0.16) already passes the default $0.15 run limit.

### The synthetic school leaver (TEST1-16)
- Card `fixtures/synthetic/school-leaver.json` (SL01, "Maya (synthetic)"), labelled synthetic,
  outside `fixtures/m0` (untouched; its validator passes in `make check`). Role `no_job_yet`, no
  job title, no income.
- Cases: **INT-16** (her card's words: no job yet, in education, the Brownies group as something
  she has done, no money, one question about enjoyment) and **INT-17** (what she enjoys), both
  `demo: true` and passing offline on the demo interviewer; **DSC-21** (her subjects and
  volunteering: grounded, distinct, no percentage, no unsupported title, nothing close to now);
  **STR-01/STR-02** (a strength quoting her words for chemistry technician's "laboratory
  techniques" is accepted; a paraphrase is refused). With Task 6f's browser test, six.

### Session W2's package (`docs/reviews/session-w2.md`)
How to start (`make session`, a Live-assisted workspace not marked synthetic, the key pasted,
`make session-ledger`, `make stop`); three made-up people (Maya, Sam the bookkeeping assistant
whose title is on no list, Jo = P02); the five questions; seven saved questions from the ledger's
"Session W2" lines and 6f's review M4/M5, Childline's as "to add when Childline's details are
checked"; a record sheet. Every item "not run — requires human". It passes
`test_session_packages.py`.

## Rulings
1. **No new run kind.** Role research is a sealed input of its own on `source_search`; the
   reading is an ordinary acquisition. So no workflow changes and `application_version` stays.
2. **The reading is its own command**, which the web calls as soon as the search is done. The
   worker can't start an acquisition (its only way to start a run is the extraction SQL
   function), and adding one wasn't worth a new privileged path. Asked again, it returns the
   same reading (200). It takes no expected version: the research isn't a versioned record; its
   state is the guard.
3. **No join, no back-off** for role pages: each needs its own title check; per-host pacing holds.
4. **The verdict is computed on read**, never stored, from the recorded checks.
5. **Copies** fold by `same_job` or the same passage (title + 24 words); **one host is one
   source** unless two different named employers.
6. **Found stays found** if the reading is stopped later; "not yet found" needs a complete reading.
7. **The research section lives under the slate** (Directions), so it needs a discovery first.
8. **A found idea made a target** keeps the record kind `own_words`; the research is its evidence.
9. **Research only for a title no list holds** (refused otherwise).
10. **Duties deferred** (above).
11. **Strength case kind**: STR-01's destination stands for a target chosen from her slate (the
    slate itself is DSC-21's, live); the skill labels and URIs are ESCO v1.2.1's, checked in the
    labelled sample.

## Checks (on the final code)
- `export PATH=/opt/node24/bin:$PATH; env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`:
  **rc 0**. ruff format and lint clean; mypy clean (380 files); pytest **1,819 passed**, 8
  skipped, 432 deselected; fixture validator passed; generated client current; Biome clean; `tsc`
  clean; Vitest **44 files, 466 passed**. (Run after the package commit; the register and report
  commit changes no code.)
- Focused: `tests/domain/test_role_research.py` 15 passed; `tests/eval/test_evaluation.py` 43
  passed; `tests/tools/test_live_role_research.py` 1 passed; `RoleResearch.test.tsx` and
  `Directions.test.tsx` 43 passed.
- **Not run, Docker down:** `make acceptance`; `tests/integration/test_role_research.py` (8 tests:
  two hosts found with quotes and dates, the three one-source cases, the official page, the
  search's bound and leak scan, refusals, read once and cancel, 0042's CHECKs); DSC-21 on the
  full release; Playwright, Storybook, captures.
- **Not run, requires the controller:** both live runs above. **Not run — requires human:**
  session W2, every item.

## RED then GREEN
- `tests/domain/test_role_research.py`: RED as a collection error (`cannot import name
  'role_text'`), then 14 passed and 1 failed (my own excerpt assertion was too strict; fixed to
  check word boundaries), then 15 passed. **Disclosed:** `corroboration.py` was written just
  before this test file, so its rule wasn't shown RED on its own.
- `tests/eval/test_evaluation.py`: RED as a collection error (no `SCHOOL_LEAVER`,
  `observe_strength`), GREEN after (43 passed).
- `RoleResearch.test.tsx` and `tests/tools/test_live_role_research.py`: written after the code;
  not shown RED.

## Changed test inputs and assertions (disclosure)
- `tests/support/fake_models.py::search_parts`: the query reads `city`, or `country` for a role
  search (no assertion changed).
- `tests/architecture/test_boundaries.py`: `careerwright.evidence.role_store` added to the SQL
  adapters.
- No existing assertion changed. `test_there_are_at_least_thirty…` still requires every
  `CaseKind`; the new strength cases satisfy it.

## Incidents
- One Python one-off (`python3 - <<EOF`) added two import lines to `api/research_schemas.py`
  instead of Edit. Every other source change used Edit or Write; ruff (format, import sort),
  Biome (`--write` on my new test) and the client generator wrote as the project's tools.
- A throwaway script in `/tmp` (not in the repository) ran the demo interviewer on her words.

## Concerns
- The live search's quality for role pages is unqualified until the controller's run.
- A title that appears only in a page's navigation counts; a copy reworded around the title on
  another host counts twice unless its structured data says it's the same job (recorded limits).
- Research shows only after suggestions exist (it lives under the slate). A person with an
  own-words role who never asks for suggestions can't research it yet.
- The web compares titles case- and space-insensitively to pick a research to show; the API's
  title key is finer (plurals, accents). Two spellings may show as unresearched.
- `role_researches` isn't in the workspace export yet.
- CLAUDE.md not changed. Proposal, for the controller: in Commands, add "`make live-role-research`
  (one in-process role research on the test model with a synthetic title, scope
  `live-role-research`)"; in Layout's `careerwright/evidence`, add "role research
  (`role_research`, `corroboration`, `role_store`)".
- `docs/plan/*` not changed (no line of mine to close there).

## Paths a reviewer can skip
`apps/web/src/generated/**` (regenerated client).

## Fix round 1

Main tree, branch `claude/confident-ramanujan-ux3saw`, from 8d0191d. No live call, no web
request, no Docker. Migration **0043** (`r0043_role_page_passages.py`, `down_revision =
"0042"`; Task 12c's follow-up renumbered itself to 0044). DBOS `application_version` unchanged.

### Commits
- `5480e16` I1 and M1: copies by any passage, one site is one source, hidden text left out
  (migration 0043).
- `c1128d0` I2, I3 and M9: role pages never job sources; the live tool ledgers first; its
  in-process reading said; `TITLE` quoted safely.
- `217974a` M2, M3, M6, M7: `on_a_list`; ideas stay ideas; ID-only receipts; "nothing else
  about you"; client regenerated.
- `1cd6b26` I4, M8: Sam's new title checked in code; Maya named as made up; P02 dropped from
  the person's text; ADR 0015 and ADR 0009 fix round lines.
- last commit: the register row (DIV1-15) and this section.

### What changed, finding by finding
- **I1** (`evidence/corroboration.py`). At each of the title's first 16 places, the title with
  the 24 words after it, and the 24 words before it with the title, are fingerprinted
  (`passages`). A side with fewer than 8 words (the text ends) isn't; a place with neither side
  stands for the whole text. Two pages sharing any fingerprint are copies. Sources are compared
  by registrable domain (`site`: last two labels, or three under the UK's two-level suffixes,
  four under `service.gov.uk`). `TitleCheck.passage_sha256` became `passages`; migration 0043
  replaces the column with `passages text[]` (backfilled; CHECKs: non-empty exactly when
  verified, at most 32, each a SHA-256 in hex). The reviewer's probe is pinned:
  `test_one_advert_on_two_boards_counts_once_whatever_each_board_puts_around_it` (identical
  body, each board with its own `<title>`, navigation and footer naming the title first →
  not found, one group). Also: the advert naming the title only at its end; two boards with
  their own adverts stay two sources; four subdomain pairs are one source; three pairs under a
  public suffix (`co.uk`, `gov.uk`, `.example`) stay two.
- **I2** (`evidence/store.py`). `coverage`, `url_history` and `urls_in_flight` leave out
  attempts (or targets) carrying a role title (`_not_a_role_page`). So the Jobs chapter's
  coverage and empty reason ignore role pages, a job request never joins a role reading, and
  a role page's failures never back off a job fetch. Integration assertions added:
  coverage `{}` and `no_sources_checked` after a reading; a job request for a page a reading
  is waiting on starts its own run.
- **I3** (`tools/live_role_research.py`). The ledger row (search notes only) is written and the
  markdown rendered as soon as the call returns, and the key scan runs, before any page is
  read. The pages' results (hosts, classes, verified, the verdict; never a URL) are printed as
  one line with the row's number, key-scanned too; they are no provider call, so no ledger row.
  **Changed for the controller:** the verdict is in the command's output, not the row's notes.
- **I4** (`docs/reviews/session-w2.md`). Sam is now a client onboarding assistant ("Client
  onboarding assistant"). `tests/eval/test_titles_on_no_list.py` (in `make check`) checks it and
  the live tool's default ("Biodiversity net gain officer") against every pinned option pack
  version (it fails for "Bookkeeping assistant": shown by calling it, `('Bookkeeping
  assistant', '0.1.0')`), and that the package names it. A new integration test in
  `tests/integration/test_evaluation.py` runs the product's own refusal (`no_list_holds`, made
  public from `_no_list_holds`), `label_match_uris` and `uk_titles.listed` on the full ESCO
  release and the UK index. **Not run: no datasets here**, so whether ESCO or the ONS index
  holds either title is still unchecked. The package's notes say so and ask for it before the
  session.
- **M1** (`evidence/pages.py`). `role_text` now reads only text nodes with no `script`, `style`,
  `noscript`, `template`, `[hidden]`, or inline `display:none` / `visibility:hidden` ancestor
  (an XPath through Scrapling; no new import). `visible_text` (model extraction) and the
  body-keeping checks are unchanged. Tests: seven hidden forms; text after a hidden span still
  read; the left boundary and hyphen; punctuation; either apostrophe form folds alike.
  **Ruling:** a possessive ("technician's") is not the title: the shared quotation rule
  (`span_offsets`) treats an inner apostrophe as part of the word. Kept, pinned by a test
  (errs towards "not yet found").
- **M2, M3** (`profile/records.py`, `api/*_schemas.py`, `Directions.tsx`, `vocabulary.ts`).
  `TargetRecord.on_a_list` (not own words, any ESCO label match, or a pack target by its
  title); served as `on_a_list` on `TargetRecordOut` and `RoleOut`. `researchable` requires it
  false, and takes ideas before targets, so an idea made a target keeps "A title Careerwright
  thought of" and shows "Saved as one of your targets". That line no longer says "not yet
  found" (it contradicted a found result). **Ruling:** the pack counts as a list in the web
  (as I4 counts it); the API still refuses only ESCO and UK index titles.
- **M6** (`api/routes_research.py`). Both role research commands' receipts are
  `{"research_id": ...}`; the answer is read again after `run_idempotent`, so a replay answers
  with the research as it is now. Integration assertion added on `command_receipts`.
- **M7**: "It sends only the title and “England”, nothing else about you."
- **M8**: workspaces named "Maya (made up)" and so on; "This is P02 from the test pack" moved to
  the notes for Claude.
- **M9**: the tool's docstring, its ledger purpose and ADR 0009's line say the live run reads
  pages in its own process (holding the Meta key), not through the restricted worker's
  service. The Makefile passes `--title "$$TITLE"` (make exports a command-line variable, so
  the shell expands it as a word; checked with a throwaway makefile: quotes, backquotes and
  `; ls` stay in the title).

### Checks (on the final code)
- `export PATH=/opt/node24/bin:$PATH; env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`
  after each change; last run **rc 0**: ruff and mypy clean; pytest **1,854 passed**, 8
  skipped, 434 deselected; fixture validator passed; client current; Biome, `tsc` clean; Vitest
  **44 files, 467 passed**.
- RED then GREEN: the I1 tests (6 failed, then pass); M1 (9 failed, then pass after one test
  input was corrected, below); `on_a_list` (1 failed, then pass); the web `researchable` tests
  (3 failed, then pass); M7 (1 failed, then pass); I3 (collection error on `PAGES_PRINTED`,
  then 2 pass); I4 (the package test failed, then pass).
- **Not run: the controller runs acceptance:** `tests/integration/test_role_research.py`
  (with the new I2 and M6 assertions), the new `test_evaluation.py` test (also needs the
  datasets), `make acceptance`, Playwright, Storybook. **Not run, the controller's:** both live
  runs. **Not run — requires human:** session W2.

### Changed test inputs and assertions (disclosure)
- `tests/domain/test_role_research.py`: `inside.passage_sha256 is None` became
  `inside.passages == ()` (plus `found.passages` non-empty); the `TitleCheck` field set
  names `passages`. My own first possessive case expected the title verified; corrected to
  "not verified" (the shared rule), with the reason.
- `tests/tools/test_live_role_research.py`: the verdict and pages are asserted from the printed
  line, not the row's notes (the row now holds the search's notes only).
- `RoleResearch.test.tsx`: the "which titles" cases now pass `on_a_list`; the expected order is
  role, ideas, targets; the role example's title is "Client onboarding assistant"; the sends
  text expects "nothing else about you".
- `on_a_list` added to fixtures: `Directions.test.tsx` (true, an ESCO title),
  `YouChapter.test.tsx` and `Conversation.stories.tsx` (true for `ons`), `model.test.ts` and
  `stories/data.ts` (false).
- `tests/integration/test_role_research.py`: the cancel test now also starts and cancels a job
  acquisition of the same page (new assertions); no existing assertion changed.

### Concerns
- Whether ESCO or the ONS index holds "Client onboarding assistant" (or the default live
  title) is unchecked until the new integration test runs with the datasets.
- Style-sheet hiding (a class with `display: none`) still counts as visible (recorded in ADR
  0015).
- On a replay, the research commands answer with today's state, not the first answer's.
- The API's refusal doesn't include option pack titles; the web's list does.
- Listed for later (not done): M4, M5 (a session W2 question), M10, M11.

## Follow-up: unread pages

Worktree `/home/user/careerwright-wt/6e-unread`, branch `wt-6e-unread`, rebased onto
`claude/confident-ramanujan-ux3saw` (0179b65). Commits: 081f514 (the fix), 4480d12 (ADR 0015
line and register row, last).

### The trace (step 1)
- The product: `role_research._pages` gave `corroborate` only the pages with a recorded title
  check. Only a successful read records one (`acquisition._record_role_page`). Blocked, failed
  and untried pages were dropped silently.
- The acquisition workflow carries on past a failed page and publishes, so the reading run
  ends `complete` even when every page failed. The view then said `not_yet_found` with
  `not_on_any_page`, the same bug as ledger row 44. The web showed "None of the pages
  Careerwright read uses the title word for word" next to "5 pages couldn't be read": a
  contradiction.
- Some failed: the same wrong reason, plus the unread count.
- None proposed: the product says `no_pages` (and `start_reading` refuses), so `corroborate` is
  never reached. The live tool, though, called `corroborate([])` and printed `not_on_any_page`
  for an empty list.
- A failed or cancelled reading with nothing verified was already `reading_stopped`, with no
  reason. That is unchanged.

### What changed
- `evidence/corroboration.py`: `corroborate(pages, *, unread=0)`. `Corroboration.unread` is new.
  A new reason, `pages_unread`: no page read shows the title, and at least one page couldn't be
  read. `not_on_any_page` now needs every page read. One verified source with unread pages
  stays `one_source_only`, and the count is kept. No pages and no unread raises `ValueError`:
  that isn't a result.
- `evidence/role_research.py`: `unread` is the number of targets with no check. The state
  comment no longer says "every page read".
- `tools/live_role_research.py`: the printed notes carry `unread`. With no page to read, the
  verdict is `null` with reason `no_pages`.
- API: the enum gains `pages_unread` and the field description says what each reason means.
  The client was regenerated (`pnpm run generate`): only an enum value and a description.
- Web: `ROLE_RESEARCH.notYetFound.pages_unread` = "Careerwright couldn't read every page the
  search found, so it can't say yet." It shows above the existing unread count ("5 pages
  couldn't be read, so they aren't counted either way.").
- ADR 0015: one line under "The rule". Register: the DIV1-15 row's evidence column.
- No migration: the reason is computed when read, and no stored CHECK lists it.

### Rulings
- One reason code covers both "none read" and "some read". The count (the API's pages with
  `title_verified` null, which the web already counts) says how many. Separate codes would add
  nothing the count doesn't already show.
- `unread` defaults to 0 so the existing domain tests keep their meaning. Both product callers
  pass it.

### Checks
- RED: the four new or changed domain tests failed before the fix (`4 failed, 45 passed`). The
  live-tool and web tests were written beside the fix and not run before it (not shown RED).
  GREEN after:
  `tests/domain/test_role_research.py tests/tools/test_live_role_research.py`, 52 passed.
- Web: `RoleResearch.test.tsx`, 11 passed (new: "never says the pages lack the title when it
  couldn't read them").
- `env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (final code, after the rebase):
  ruff and mypy clean, backend 1,860 passed and 8 skipped, fixture validator passed, the client
  matches, Biome and `tsc` clean, Vitest 468 passed.
- Integration (new parametrized
  `test_a_page_that_could_not_be_read_is_never_a_page_without_the_title`: every page read, none
  read, one of two read, with 404 pages as the failures) and acceptance: not run, because the
  controller runs them.
- Live calls: none ($0).

### Concerns
- The integration test assumes a 404 page is a non-transient `http_error` and the run still
  completes. That is what `fetcher.py` and `evidence/workflow.py` do, but it hasn't been run
  here.
- Generated paths to skip: `apps/web/src/generated/`.
