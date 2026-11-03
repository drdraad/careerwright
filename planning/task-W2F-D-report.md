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
