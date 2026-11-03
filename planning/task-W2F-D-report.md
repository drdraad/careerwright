# Task W2F, slice D: report (implementer)

Status: DONE_WITH_CONCERNS. Main tree, branch `claude/confident-ramanujan-ux3saw`.
Commits: `94902f2` (code, tests, migration, generated client), `833660a` (ADR lines, runbook,
register; last).

## What changed

Scope as dispatched, widened by the coordinator's two messages on 3 November 2026: up to 20
pages, 30 candidates, up to 8 tool calls, better search instructions, grounding; then the
product owner's yes to the higher run caps and to migrating untouched limits.

- **The role search** (`backend/src/careerwright/evidence/search.py`, `search_agent.py`):
  - The loose job-search constants became one `SearchBounds` per purpose.
    `JOB_SEARCH` is unchanged: `low`, 2 tool calls, 8 candidates, 2,500 prompt bytes,
    1,500 output tokens. Its prompt is byte-identical, still `source-search-3` (checked
    against HEAD).
  - `ROLE_SEARCH` is new: `medium`, 8 tool calls, 30 candidates, 2,500 prompt bytes,
    4,000 output tokens. `run_search` asks Meta for the purpose's context, tool calls and
    output bound.
  - The new prompt version is `role-search-2`. It asks for several searches (the exact title
    in quotes with "job" and "England"; with "careers" or "role profile"; "professional
    body" or "gov.uk"). It says never to return a home page, a results page or a list of
    many jobs, and to give each page's own address exactly as the search returned it.
    The bound of 30 is in the prompt.
- **Never a home page; only pages the search returned** (`check_search`, role purpose only):
  - A candidate whose path is empty or "/" (any query) is excluded as `site_root`.
  - A candidate the search never returned or opened is excluded as
    `not_returned_by_search`. Both are new `ExclusionReason` values, so the client was
    regenerated. The web words no exclusion reason, so it needs no new words.
  - `role_research.pages_to_read` reads only grounded, non-root candidates. That covers
    proposals sealed before this change too.
  - All roots, or nothing grounded, gives the existing `no_pages` state ("The search found
    no page Careerwright could read"), never "not yet found".
- **Up to 20 pages read:** `MAX_PAGES = 20`, the most `acquisition_targets.position`
  (0 to 19) holds. The found rule is unchanged.
- **Reservation:** one per run kind (see ruling 1). `worst_case_nano_usd` and
  `exceeded_bound` use `RESERVED = ROLE_SEARCH`. The estimate route (`ESTIMATED_KINDS`) and
  the worker task share that function, so the web's `RunEstimate` cost line for "Research
  this role" covers the deeper search with no web change.
- **Caps** (the product owner's yes):
  - Default run limit $0.15 → $0.50 (`config.py`, `compose.yaml`).
  - Session run cap $0.75 → $1.60 (`tools/session.py`).
  - Migration `r0047_role_search_default_run_limit.py`: version-1 rows at exactly
    150,000,000 become 500,000,000; any limit the person set is kept.
- **Tools:**
  - `tools/live_smoke.py`: the `max_tool_calls` 1 qualification uses
    `BOUND_SEARCH = replace(JOB_SEARCH, max_tool_calls=1)`, so its numbers are unchanged.
  - `tools/live_role_research.py`: wording says up to twenty pages.
- **Docs:**
  - ADR 0003 amendment line: medium is unqualified; one price per search; the caps and
    migration 0047 with the product owner's yes; a run's hard maximum rises with its limit.
  - ADR 0009 amendment line: 5 → 20 pages, the grounding finding, no home pages, the reading
    time bound.
  - ADR 0015 line, the runbook (session caps, live-role-research, default limits), and
    register rows DIV1-15, MODEL-08 and MODEL-11.

Files: `backend/src/careerwright/{config.py, api/routes_research.py (docstring only),
evidence/search.py, evidence/search_agent.py, evidence/role_research.py,
migrations/versions/r0047_role_search_default_run_limit.py}`, `backend/tools/{session.py,
live_smoke.py, live_role_research.py}`, `compose.yaml`, tests (below),
`apps/web/src/components/RoleResearch.tsx` (comment only), the generated client, and the docs
above.

## Rulings

1. **One reservation for the `source_search` kind**, at role research's bounds, for both
   purposes.
   - Why: the activity reserves (`task.worst_case_nano_usd(model_id)`) before it opens the
     sealed input, so it can't tell a job search from role research. Infrastructure is frozen
     (no new run kind), and opening the input earlier would change the pinned activity
     pattern.
   - Cost to the job search: it reserves $0.031 (test) / $0.161 (Spark) instead of
     $0.008 / $0.045, and its after-call bound check now fails at a 9th search, not a 3rd.
     Its request to Meta is unchanged (`low`, 2 tool calls).
   - Tests changed to match: the fake `SEARCH_OVERRUN` reports 9 searches (was 3); the job
     search integration test reserves 30,700,000; the domain overrun case is "a ninth search".
2. **Price of `medium`:** the registry has one per-search price ($2.50 per 1,000, from Meta's
   page as recorded in ADR 0003), not tiered by context. So `medium` is priced from the
   registry and nothing was invented. What is not known: the tokens a `medium` search injects.
   The bound stays at `low`'s measured 12,000 a call (about 10,000 seen). At 8 calls this is
   also the most Wonder's $1.60 cap leaves room for. A search past it fails `bound_exceeded`,
   visibly, booked at its actual cost.
3. **Grounding is strict for role research** (the coordinator's confirmation): a candidate is
   kept only if the search returned or opened that exact address (normalised: trimmed,
   trailing "/" removed, lower-cased). A search that returned no address grounds nothing, so
   nothing is read: "the search found no page Careerwright could read". Never a "not yet
   found" from ungrounded guesses.
4. **Role prompt bound 2,500 bytes, not the 4,000 I first proposed to the coordinator.** The
   new prompt is at most 2,010 bytes (a 120-character title of 4-byte characters), so the
   job search's bound fits.
   - Per attempt: $0.031 test model, $0.161 Spark, $0.496 Wonder (I quoted $0.502 and $0.163).
   - Three attempts: $0.482 against the $0.50 default, $1.488 against the $1.60 cap.
5. **Migration 0009's own test now stops at 0009**, and 0047 has its own test. Taken to
   head, 0009's untouched row would move on to $0.50 by 0047's rule.

## Checks run

- **TDD:**
  - RED 1: `uv run --locked pytest tests/domain/test_role_research.py
    tests/domain/test_source_search.py`. Collection error: `ROLE_SEARCH` can't be imported.
  - RED 2 (bounds in place, rules not yet): 5 failed, 64 passed. Home pages were kept, an
    ungrounded page was read, `MAX_PAGES` was 5, and the role request asked for 2 tool calls.
  - GREEN: the same files, 69 passed.
- **Focused fast tests:** `pytest tests/domain/test_role_research.py
  tests/domain/test_source_search.py tests/domain/test_spend.py tests/domain/test_extraction.py
  tests/tools/test_session.py tests/tools/test_live_role_research.py
  tests/tools/test_live_smoke.py`: 255 passed.
- **`make check`** (final code, after the last source edit): exit 0. Ruff format and lint
  clean, mypy clean; pytest 2144 passed, 123 skipped; client drift, Biome and tsc clean;
  Vitest 46 files, 494 tests passed. The first two runs failed for reasons since fixed: a
  stale generated client, then one line over 100 characters.
- **Focused integration under the lock** (the dispatch's guarded command), run twice. The
  second run was on commit `94902f2`; both gave 23 passed, and the lock was released each
  time. Tests:
  - `tests/integration/test_role_research.py` (12, including the new
    `test_a_search_that_proposed_only_home_pages_reads_nothing_and_says_so`)
  - `test_migrations.py::{test_a_fresh_database_migrates_to_head_and_seeds,
    test_an_untouched_old_default_run_limit_upgrades_to_the_new_default,
    test_0047_moves_an_untouched_15_cent_run_limit_to_the_new_50_cent_default}`
  - `test_acquisition.py::{test_a_source_search_proposes_candidates_for_a_confirmed_target_and_city,
    test_a_search_past_its_reserved_bounds_is_booked_at_cost_and_its_output_never_used}` (2)
  - `test_page_extraction.py::test_the_job_list_states_what_an_acquisition_may_spend_before_it_starts`
  - `tests/integration/test_live_session.py` (4)
- `make acceptance`: not run (the controller runs acceptance).

New or changed tests that assert behaviour, in `tests/domain/test_role_research.py`:
- `test_a_role_search_is_one_deeper_request_whose_candidates_are_checked_by_code` checks
  `medium`, `max_tool_calls` 8, `max_tokens` 4,000, and that only the page the search
  returned is kept.
- `test_a_site_s_home_page_is_never_a_page_to_read` uses the product owner's five home pages,
  and an old sealed proposal too.
- `test_when_every_candidate_is_a_home_page_no_page_is_read`
- `test_only_pages_the_search_really_returned_are_read` (and none when the search returned
  no address)
- `test_twenty_pages_are_read_after_home_pages_and_refused_hosts_are_dropped`
- `test_the_role_search_is_told_how_to_search_and_what_never_to_return`

The job search test now also asserts `low` and 1,500 output tokens. The reservation test holds
the hand-computed numbers.

## Live calls

None (R5). The controller and the product owner run the live check.

## What the native search tool returns (asked by the coordinator)

- **From the code:** Pydantic AI 2.62.0 maps each `web_search_call` item to a
  `NativeToolCallPart` and a `NativeToolReturnPart` (`models/openai.py`,
  `_map_web_search_tool_call`).
  - The return part's `sources` is `action.sources`, which the request asks for through
    `include=["web_search_call.action.sources"]` (`openai_include_web_search_sources=True`).
  - In the OpenAI schema each source is `{"type": "url", "url": str}`, "the URL of the
    source".
  - An `open_page` action carries its `url` in the call's args. `search_agent.searched`
    grounds on both.
- **From the recorded evidence:** the ledger notes record hosts only, never the addresses.
  But they show Meta's sources are page addresses, not only sites: role rows 44-46 saw 21, 22
  and 22 distinct sources over 9, 13 and 18 hosts, so one site came back under several
  addresses.
  - In those rows, 0 of 5 and 0 of 8 role candidates matched a returned address.
  - In the job rows, one candidate matched (row 30, 1 of 1) and four did not (row 29).
  - So the model has been returning addresses the search didn't return, such as the home
    pages in the product owner's run.
- **Not knowable offline:** whether every source is a page address; whether Meta adds
  tracking parameters that the model drops, which would defeat exact grounding; and what
  `medium` changes. The controller's live check shows it. If grounding then leaves nothing
  to read, the run says "no page Careerwright could read" (honest, but empty).

## How long reading 20 pages can take

Reading calls no model and costs nothing. Each page keeps the guarded fetcher's checks,
robots.txt and per-host pacing.
- One try of a page is bounded by one 20-second deadline, robots.txt included. Before that
  comes its host's pacing slot: at most 5 seconds (the manifest's longest rate limit) for one
  reading alone.
- A transient failure is retried by the DBOS step at most three tries, 2 and 4 seconds apart.
- So one page takes at most about 81 seconds, and 20 pages at most about 27 minutes.
- Hard ceiling: the DBOS worker's 90-second client timeout per try gives 20 × (3 × 90 + 6)
  seconds, about 92 minutes.
- Typical pages take a second or two (about a minute for 20). The person can stop the
  reading at any time.

## Concerns

1. **`medium` is unmeasured:** its tokens per call, and whether Meta honours the context
   size at all. A search past 99,000 input tokens fails `bound_exceeded`, booked at its
   actual cost.
2. **Tool-call bound:** Wonder keeping to `max_tool_calls` was never shown (ADR 0003 row 37).
   A search past 8 billed searches fails the same way.
3. **Strict grounding may read nothing** if the model keeps editing addresses. The new prompt
   asks for addresses exactly as returned; the live check will tell. One option if it fails,
   not built: read the search's own returned addresses directly, which would need them kept
   in the proposal.
4. **`searched()` records only a search action's `query`**, not a `queries` list. Row 37's
   response carried three queries. The queries shown may under-count; billing is unaffected.
   Pre-existing, not changed.
5. **A run's hard maximum (after a worker crash) is its run limit,** so it rises for every
   kind with the default. A job acquisition's five extractions now state at most $2.50
   (was $0.75). This is recorded in ADR 0003's line.
6. **The live tool's budget is spent:** `make live-role-research`'s scope
   (`live-role-research`) has used its 3 requests (rows 44-46). A live run through it needs a
   new scope or cap, which is the controller's call.
7. **The session stack runs images built before this change** (as instructed, not restarted).
   The new search, caps and migration apply only after a rebuild, and `make session` sets
   $1.60 a run only when next started.
8. **Two process slips against "Edit/Write only":**
   - One Python exact-string replacement script on `backend/tests/domain/test_source_search.py`
     (eight unique replacements, each asserted to match once).
   - One shell heredoc append for ADR 0003's amendment line.
   Everything else was made with Edit and Write. Both results were reviewed in the diff.

## Generated paths a reviewer can skip

`apps/web/src/generated/api/{schemas.gen.ts, sdk.gen.ts, types.gen.ts}` and
`apps/web/src/generated/openapi.json`. They hold the two new exclusion reasons and the reading
route's docstring.

## Review

Independent reviewer, 3 November 2026. Read the dispatch, the ledger from "PO answer (3
November 2026): widen role research" on, the brief's Global Constraints, this report, then the
whole diff in five passes (2,068 lines; generated client skipped as listed). Read-only; no
suites re-run. Three focused in-process checks, named below where used.

### Spec Compliance
- ✅ Spec compliant, with the product owner's later changes (20 pages, 30 candidates, eight
  tool calls, directed queries, grounding, $0.50 and $1.60 caps, migration 0047).
  - Never a home page: `check_search` excludes a root as `site_root` for role research
    (`backend/src/careerwright/evidence/search.py:295`, `:330`), and `pages_to_read` drops
    roots and ungrounded candidates even from proposals sealed before the rule
    (`backend/src/careerwright/evidence/role_research.py:197-213`). Only home pages, or nothing
    grounded, gives `no_pages`: the web says "The search found no page Careerwright could
    read." with "Every page the search suggested is one Careerwright can't use." and "This
    isn't a sign the role doesn't exist." (`apps/web/src/lib/vocabulary.ts:714`, `:687`,
    `:721`). Never "not yet found". The integration test proves it at the API (409,
    `no_pages`) with grounded home pages, so the root rule itself is what is exercised.
  - The found rule is unchanged: `corroboration.py` and `check_title` are not in the diff.
  - Every page still goes through the restricted worker and the guarded fetcher (robots,
    pacing, 20 s page deadline): the reading path is unchanged; it only gets up to 20 targets,
    which `acquisition_targets.position` (0 to 19) holds. Role pages still never reach a model
    (`acquisition.py:1010-1012`).
  - Reservation from the registry: one price per query ($2.50 per 1,000,
    `model_registry.py:20`); the arithmetic in the tests is right ($0.031, $0.161, $0.496 an
    attempt; 3 x $0.161 <= $0.50; 3 x $0.496 <= $1.60). The estimate route and the worker
    share `search.worst_case_nano_usd`, so the cost line before "Research this role" covers
    the deeper search.
  - A breach is observable and booked at actual cost: the activity holds measured usage to
    `exceeded_bound` on every path and reconciles at `estimate_cost_nano_usd(usage)`
    (`identity/activity.py:576`, `_spend`).
  - The job search's request is unchanged. Checked by importing the old `search.py` from
    `834b1b1` beside the new one: `INSTRUCTIONS` byte-identical, still `source-search-3`;
    the tests pin `low`, two tool calls and 1,500 tokens.
  - Migration 0047 mirrors 0009: only `version = 1 AND run_limit_nano_usd = 150000000`,
    `downgrade` raises. Rows are created only from the defaults (`credential_store.py:161`), so
    version 1 is "never changed by the person". Its test covers untouched, chosen $0.15,
    session $0.75 and lower rows.
- ⚠️ Cannot verify from diff: how often the live search returns addresses the model copies
  exactly (rows 44-46: 0 of 13 grounded); `medium`'s tokens and the request's duration; the
  implementer's `make check` and integration runs (not re-run). No human-only gate is claimed.

### Strengths
- One `SearchBounds` per purpose replaces loose constants; the request, the reservation and
  the bound check read from it, so they cannot drift apart.
- Strict grounding is the honest choice: a guessed address is never read, and nothing read is
  never "not yet found".
- Legacy sealed proposals are filtered at read time too, so the product owner's old research
  cannot read a home page after the upgrade.
- The shared reservation is disclosed in ADR 0003, the register and the report, with its cost
  to the job search stated.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. **Grounding compares Meta's source addresses raw.** `search.py:313` normalises sources
   with `_normal` only, while candidates pass `check_url`, which drops the fragment. Probed:
   source `https://a.example/p#:~:text=...`, candidate `https://a.example/p` -> excluded
   `not_returned_by_search`. Grounding is now a gate on what is read, and rows 44-46 grounded
   0 of 13, so a mismatch here means role research reads nothing. Fix: put each source through
   `check_url` (same normal form) before comparing; it widens nothing, the page is the same.
   Worth doing before, or as soon as, the live check shows a mismatch.
2. **Results and listing pages are kept out by the prompt only** (`search.py:147`). Code drops
   only an empty or "/" path; `/index.html` and `/en-gb/` pass (probed), and a board's own
   results page (`?q=`, `?keywords=`, `/search`) is read if the search returned it. Such a page
   often repeats the title in its heading, and two boards meet the found rule. This is ADR
   0015's recorded known limit (a title in a list still counts), but the new query "the exact
   title in quotes with job" makes such pages likelier. Question for the live check: are the
   found pages postings or lists? A cheap partial fix, if wanted: exclude addresses with a
   search parameter or a `/search` path. (A WordPress page at `/?page_id=12` is excluded as a
   root, as the dispatch asked.)
3. **The deeper request is unmeasured on three axes; list them for the live check.** (a)
   Input per call at `medium` is held to `low`'s 12,000 (`search.py:53`); an overrun fails
   `bound_exceeded`, booked at cost (fine). (b) 30 candidates plus eight searches' reasoning
   within 4,000 output tokens (`search.py:92`); a cut-off fails `output_truncated`, booked
   (fine). (c) Eight searches in one request against the 120 s client timeout
   (`identity/meta.py:21`), not raised in the report: a timeout is transient
   (`failures.py:114-119`), so DBOS tries three times, each with unknown cost and the whole
   reservation committed: up to $1.49 on Wonder with only "The search stopped before it
   found any pages." shown. Record duration, input and output tokens in the live check.
4. **The shared reservation is acceptable, but it is a change to the job search** the
   dispatch called unchanged. It is forced by the frozen infrastructure (the activity reserves
   at `activity.py:472`, before the sealed input is opened at `:539`; no new run kind). Money
   stays bounded: measured usage is still held to what was reserved. Two effects: a job search
   reserves $0.161 on Spark (was $0.045), and its bound check now lets up to eight searches
   through, not two, if Meta ignores `max_tool_calls` (unproven, ADR 0003 row 37). No person
   sees it: the web never starts a job search (only the API and `make live-smoke`), and the
   `live-search` scope still fits (9 x $0.031 <= $0.30). For the controller to acknowledge.
5. **The reading can take minutes and the person isn't told.** They can stop it (Stop is
   shown; DBOS cancels before the next page), but the line stays "Reading the pages the search
   found…" (`vocabulary.ts:716`) with no count, and pages not yet tried say "Not read"
   (`vocabulary.ts:742`) while reading. Typical about a minute; 27 minutes worst case by the
   report's arithmetic (20 s page deadline, 5 s pacing, three tries; checked against
   `FetchLimits` and `workflow.py`). For the final list: "Read 3 of 20 pages".
6. **Two edits outside Edit/Write** (process). Checked the results: the ADR 0003 append is
   intact (every `$` amount present, no shell expansion, no em dash), and the eight test
   replacements read correctly in the diff.
7. **Pre-existing, not from this slice:** in role research's `no_pages` state with
   `no_candidate_proposed`, the web says "The search returned pages, but none was a single job
   posting" (`vocabulary.ts:681-683`): a job-search sentence, and a claim about what pages
   contain rather than what Careerwright checked. For the final list.

### Assessment
**Task quality:** Approved
**Reasoning:** Every asked-for rule holds in code with tests at the boundary: no home page
read, only grounded pages read, "no page Careerwright could read" never "not yet found", the
found rule and the guarded fetch unchanged, the reservation priced from the registry with
overruns visible and booked, and the migration limited to untouched rows. What remains is live
behaviour, so the live check should record grounding, duration and tokens, and finding 1 is
the cheapest way to keep strict grounding from reading nothing.

## Fix report (implementer, 3 November 2026): grounding compares canonical addresses

Commit `a63c812` (pathspec, main tree).
- **What was wrong:** grounding compared the search's own addresses only trimmed, without a
  trailing "/" and lower-cased. A candidate went through `check_url` first. So a returned
  address with a fragment ("#apply") or a default port (":443") never matched its own page,
  and role research rejected it as `not_returned_by_search`.
- **Change** (`backend/src/careerwright/evidence/search.py`): `_normal` became
  `_grounding_key`.
  - Every returned address goes through `check_url`'s canonical form first: scheme and host
    case, the default port, the fragment dropped. Then the trailing "/" and case are folded,
    as before.
  - A candidate is compared by its checked address's key.
  - A returned address the checks refuse keeps its own text, and no checked candidate can
    match it.
  - Side effect: `sources_seen` now counts canonical addresses, so one page returned with two
    fragments counts once.
- **Test, failing first**
  (`tests/domain/test_role_research.py::test_a_page_the_search_returned_is_grounded_however_its_address_is_written`):
  - Cases: "a fragment", "a trailing slash", "the host's case", and "scheme, port and
    fragment".
  - RED: `uv run --locked pytest tests/domain/test_role_research.py -k however_its_address`
    gave 2 failed (the fragment, and scheme/port/fragment), 2 passed. The trailing-slash and
    host-case cases already passed and are kept as guards.
  - GREEN: the role research, source search, live role research and live smoke tests,
    115 passed.
- **`make check`:** exit 0 (pytest 2148 passed, 123 skipped; Vitest 494 passed; ruff, mypy,
  client drift, Biome and tsc clean).
- **Integration:** not re-run. The change is pure code inside `check_search`, covered by the
  domain test. The controller's acceptance covers the rest.
- **Not changed:** everything else in the slice, including the shared reservation.

## Round 2 report (implementer, 3 November 2026): read what the search found

The product owner's live try: Muse ran 2 searches, kept 2 grounded pages, and both returned
404, so the result was "stopped before it could read enough pages to say".

Commits (pathspec, main tree): `424082f` (code, tests, migration 0048, generated client, web)
and `2bcd739` (ADR 0009 and 0015 round 2 lines, runbook, register DIV1-15; last).

### What changed

1. **Read what the search found** (`search.check_search`, `_other_returned_pages`).
   - Role candidates are Muse's picks first, then every other page address the native search
     tool returned, in its own order. `searched()` now returns its sources as an ordered,
     de-duplicated list instead of a set.
   - Every candidate goes through the same checks: `check_url`, the manifest (refused hosts
     dropped), never a site's home page, never a page of search results for the title.
     There are up to 40 in all (`search.ROLE_CANDIDATES`).
   - Muse's list is a ranking hint, never the limit. Only Muse's own picks are listed as
     `excluded`; returned pages that fail a check are just not taken.
   - With no address returned, nothing is grounded and nothing is read
     (`test_when_the_search_tool_returns_no_page_nothing_is_read`). The research shows
     `no_pages`: `all_excluded` if Muse picked something, `search_returned_nothing` if not.
     It never shows "not yet found".
   - **Search-results page, where code can tell:** a page whose query has a value holding the
     title's words (`?q=Biodiversity+net+gain+officer`, `?keywords=...-...`, encoded, any case).
     Such a page repeats the search's own words, so the title would be on it whatever it
     lists. This rule (`role_page_refusal`, reason `search_results_page`) covers Muse's picks
     and the returned pages alike. A posting whose address names the title is still read.
     Listings without the title in the query can't be told apart by code; the prompt asks
     Muse not to return them.
2. **Prompt `role-search-3`:** at least four different searches before answering (up to
   eight): the exact title in quotes with "job" and "England"; with "role profile" or
   "careers"; with "professional body" or "gov.uk"; the title alone. The best pages first,
   since Careerwright also tries the rest. The prompt is at most 2,209 bytes, within the
   2,500 bound, so the reservation is unchanged. `max_tool_calls` stays 8.
3. **Expired pages, and reading on to the next.**
   - A page whose site answered 404 or 410 is `gone` (`PageView.gone`, `RolePageOut.gone`).
     The web says "No longer there" for it, never "Doesn't use the title" or "Not read".
     It was already never counted as a page without the title (no check is recorded).
   - The reading's targets are all the candidates (up to 40; migration 0048 lets
     `acquisition_targets.position` hold 0 to 39). It tries them in order.
   - In `acquisition.acquire_target`, once 20 role pages are read (`MAX_ROLE_PAGES`), each
     remaining target is set `not_needed` (new status; migration 0048 adds it, and only for a
     role target) and never fetched. `_pages` leaves them out: never read, never unread.
     `publish_acquisition` doesn't count them as failed.
   - **How "stopped before it could read enough pages to say" is decided:** `research_view`
     returns `reading_stopped` when the reading settled without `found` and its run is not
     `complete`. That happens when the person stopped it (`cancelled`), access was revoked,
     or `publish_acquisition` failed it (`retrieval_failed` or `source_blocked`) because no
     target was read. Every candidate is now a target and every target is tried, so a reading
     fails only after trying all its candidates; one with readable candidates left never ends
     that way.
   - What remains: if every candidate is tried and none can be read, the words are still
     "Careerwright stopped before it could read enough pages to say". That case is now
     unlikely (up to 40 candidates), but the words could be more exact; for the final list.
4. **Recorded per research:** `GET .../role-research/{id}` now states `sources_returned`
   (distinct pages the search returned), `candidates` (kept to try), `pages_read` and
   `pages_gone`. Reading straight from the live database:
   - `acquisition_targets` (one row per candidate tried or `not_needed`) and
     `source_attempts` (`status`, `http_status` 404/410) give candidates, read and gone.
   - Sources returned is only in the sealed proposal, so read it from the API.
   - `make live-role-research` reads the same way (`read_until_enough`) and prints `read` and
     `gone` beside `unread`. Its ledger notes already hold `sources_seen` and `candidates`.

### Checks

- **Domain TDD.** RED 1 at import (`ROLE_CANDIDATES`). RED 2 with the constant only:
  7 failed, 58 passed (picks then sources, results pages ×3, 40 kept, every page tried in
  order, the prompt). GREEN: role research, source search, live role research and live smoke
  tests, 121 passed, then 122 with the tool test.
  - `test_when_the_search_tool_returns_no_page_nothing_is_read` passed on the old code too:
    it states existing behaviour, as asked.
- **The tool's `read_until_enough` test** was written after the helper, not run red first.
- **Integration tests** were written before the code but first run after it. Under the lock:
  - `pytest -m integration tests/integration/test_role_research.py tests/integration/test_acquisition.py`
    plus three `test_migrations.py` tests (fresh to head, populated to head, 0047): 55
    passed, 1 failed.
  - The failure was my new stop-at-20 test asserting `found`, but its 22 identical pages fold
    to one source (copies of one advert count once). I changed it to assert the reading (run
    complete, 20 read, 1 gone, 21 pages listed, the last two sites never asked for).
  - Re-run: `test_role_research.py` 14 passed. The lock was released each time.
- **Web.** RED: `vitest run src/components/RoleResearch.test.tsx` gave 1 failed ("says a page
  is no longer there"). GREEN: 12 passed.
- **`make check`** on the final code: exit 0. Pytest 2155 passed, 123 skipped; Vitest 495
  passed; ruff, mypy, client drift, Biome and tsc clean.
- No live calls. Acceptance not run (the controller's).

### Concerns

1. **Pages read may be off topic.** The returned pages Muse didn't pick are read in the
   search's order, not checked as being about the role: Careerwright reads up to 20 of them
   for the exact title. The found rule is unchanged (exact title, two independent sources or
   one official page). The results-page rule guards against a page that only echoes the
   query.
2. **A reading can take longer.** It tries up to 40 pages. A page no longer there is one
   quick try (404 and 410 aren't retried). If every page timed out three times it would take
   about 54 minutes, and never more than about three hours (the worker's 90 seconds a try).
   It's usually a minute or two, and the person can stop it.
3. **Sources returned is readable only through the API**, since the proposal is sealed.
4. **Unread searches.** Queries recorded on the proposal still read only a search action's
   `query`, not a `queries` list. "At least four searches" may show fewer queries than Meta
   ran; the billed count (`web_search_queries`) is Meta's own.
