# Task 3b report

Implementer: Claude (Opus 5.5), in the worktree `/Users/darianraad/Code/careerpathoptimizer-wt/3b`
(branch `wt-3b`). Rebased onto `l0-local-release` at 8ad36a6. No subagents, no live model call,
no web request, no Docker pull, no headed browser. `.env`, `~/.careerwright` and `~/.nessa` not
read; the `.env` symlink the controller added is ignored and never staged. DBOS
`application_version` is still `careerwright-l0-1`: the shutdown fix doesn't change the
workflow's step sequence.

## Commits (on 8ad36a6)

| SHA | What |
|---|---|
| 4c9b72d | Muse Wonder ready to qualify: `WONDER=1` for `live-smoke` and `live-eval`, Wonder-sized caps, one $0.50 scope |
| b145c7e | The qualification's ledger rows 36-43, Wonder's capabilities and evaluation in the registry, ADR 0003's "Qualification result" |
| 36b164a | The worker-shutdown hang, reproduced and fixed |
| 2fa6f30 | `make session`, `make session-ledger`, the spending line, and the estimate before a paid run |
| c78e784 | The product owner's own commands in `make acceptance`: `make demo`, and the session packages |
| 11e2914 | Register: MODEL-10 and MODEL-11 closed; the Task 3b parts of MODEL-03, MODEL-04, MODEL-08, TEST1-10 and BND1-14 |

## 1. Muse Wonder qualified

What was built:
- `make live-smoke WONDER=1` makes two calls in this process, through the product's task code.
  The first is the connection check: schema output with usage. The second is the source
  search, streamed by a probe capability with one tool call asked: streaming, web search and
  schema output in one call. The only product change is `run_search(..., observe=...)`, which
  is empty in the product.
- `make live-eval WONDER=1 CASES=...` runs the chosen cases on Wonder as the production model,
  in synthetic workspaces.
- Caps, all named constants: $0.20 per `live-smoke` run and $0.40 per `live-eval` run. Both
  commands share the scope `wonder-qualification`: 14 requests and $0.50 in all. Without the
  flag, Wonder is still refused by the Spark-sized cap.

The controller's run: rows 36-43, $0.115534 (running total $0.156888). The registry now records
schema output, streaming and web search for `muse-wonder-1.0`. ADR 0003 has a new section,
"Qualification result".

**"searches 3" against 1 billed search (row 37).** The two numbers count different things.
- The ledger's `Searches` (1) is Pydantic AI's billed count. That is Meta's own
  `tool_usage.web_search.num_requests` when Meta reports it. Otherwise it is the number of
  `search` actions in the final response.
- The printed "searches 3" is `len(proposal.queries)`: the queries carried by the response's
  search-call parts, as the product's `searched()` collects them.
- Only `search` actions carry a `query`. With no `tool_usage`, three search actions would have
  counted as 3. So the 1 is most likely Meta's own reported count.
- Which is right for billing: Meta's count is right if Meta bills per request. If it bills per
  search action, two more searches cost $0.005, so row 37's upper bound is $0.037396.
- So Wonder keeping to `max_tool_calls` 1 is not shown. The product asks for at most two, and
  the activity's input-token bound still holds each search's token cost to its reservation.
- This is recorded in the ledger header (`usage_ledger.py`, regenerated), in ADR 0003 and in the
  registry's evaluation text.

**INT-01's failure.** This is a model result, not a tool fault. I read the committed eval record
in `docs/evidence/live-eval.md`; I did not read the private observations, which live under
`~/.careerwright`.
- Wonder asked: "What other hands-on tasks have you enjoyed, and what kinds of tasks drain you
  most?"
- The `one_question` check counts each "?" plus each further ask joined by ", and what". So it
  correctly counted two asks in one question.
- The interview prompt is unchanged. The product owner judges the questions in session W2.
  Spark's first run also had one-question failures.

**Also found, recorded only:** row 37's search excluded all six candidates for their URL scheme
(`scheme_not_allowed`, `all_excluded`). That is one synthetic search, noted in ADR 0003 for
Task 8 to watch on Wonder.

## 2. The worker-shutdown hang

- **RED first.** A new test stops a worker with SIGTERM while a model call is in flight. Before
  the fix it failed with `WorkerShutdownTimeoutError: worker ignored SIGTERM for 15.0s`, the
  same error Task 1 and W2B saw.
- **Cause.** The worker's log showed "worker stopping", "DBOS successfully shut down" and
  "worker stopped". So `DBOS.destroy()` had returned, and the watchdog had been cancelled. The
  interpreter's exit then joined the DBOS executor's non-daemon thread with no bound
  (`concurrent.futures`' exit join).
- **Fix** (`identity/worker.py`). The process ends at once with `os._exit(0)` after DBOS is
  destroyed and logging is flushed. The in-flight workflow is left as a crash leaves it, and
  DBOS recovers it on the next start. The watchdog is now armed by the signal, so a pass that
  never returns is bounded too.
- **GREEN.** The new test passes: exit 0 within the deadline, the run recovers, and the
  interrupted attempt keeps its unknown cost. All 19 durable-runs tests pass, and 133 tests in
  the other worker-using integration files.
- **Disclosed test change.** `test_a_run_cancelled_mid_call_settles_that_call_and_makes_no_other`
  waited for the attempt's `finished_at`. Publishing `cancelled` sets that at once
  (interrupted, unknown), so the test passed only because `stop()` hung until the call
  settled. It now waits for the call's own settle (`outcome` not interrupted). Its assertions
  are unchanged; nothing was loosened.

## 3. The session command and the ledger copy (`backend/tools/session.py`)

- **`make session`** runs `make dev`'s stack: project `careerwright-l0`, the same
  `CAREERWRIGHT_HOME` and ports, `--no-build`, and nothing stopped or reset.
  - It sets `CAREERWRIGHT_META_PRODUCTION_MODEL=muse-wonder-1.0`, pins the synthetic role to the
    test model, and sets the API's default limits to the caps. `compose.yaml` now passes
    those two defaults through to the API; a fast test keeps the compose defaults equal to
    `config.py`'s.
  - It then signs in as each invited person (Ada, Ben; the emulator's local test identities)
    and sets each live workspace not marked synthetic to $0.75 a run and this month's
    committed spend plus $5. It does this through the API's own expected-version command.
  - The caps are `SESSION_RUN_LIMIT_NANO_USD` and `SESSION_SPEND_NANO_USD`.
- **`make session-ledger`** copies each settled attempt with `spend_state` other than `none`.
  - It goes into `docs/evidence/live-usage.*` under `live-session-<UTC date>`, and the `.md` is
    regenerated through `usage_ledger.py`.
  - It reads only identifiers, model, kind, token and search counts, cost, reservation, state
    and time (`COPIED_COLUMNS`).
  - Unknown costs count their reservation. Nothing is copied twice, keyed on run ID and
    attempt ID.
  - Held attempts aren't copied, and the command exits 1 until they settle.
- **Ruling: who the session caps.** Every live workspace not marked synthetic, not one named
  workspace. Those are exactly where Wonder can spend, and the product owner's first session
  may start in a new workspace. A workspace whose key is stored during the session gets the
  caps from the API's defaults.

## 4. The spending line and the estimate

- **Model spending** sits in the account menu, under "Preferences for this workspace".
  - It shows "$0.42 of $5.12 spent this month", the most one run can use, how many calls had no
    reported cost, and Change. Change is an expected-version PUT, in dollars.
  - It is in US dollars only: there is no pinned exchange rate, so no pounds figure.
  - A demo workspace says it spends nothing.
  - The words for a reached limit (`FAILURE_CLASS.budget_exceeded`, `BUDGET_EXCEEDED`) now point
    to it.
  - Words live in `vocabulary.ts` (`SPENDING`, `USD_INPUT_PROBLEM`, `RUN_ESTIMATE`,
    `RAISE_THE_LIMIT`). Integer-only dollar handling is in `lib/usd.ts`.
- **The estimate helper.** `GET /v1/workspaces/{id}/spend/estimate?kind=` returns
  `RunEstimateOut`, codes and numbers only (R11):
  - `per_run_nano_usd`: without a crash, every attempt at its reservation, never past the run
    limit;
  - `hard_maximum_nano_usd`: the run limit;
  - `refused_scope`: run, period or null, by the submission's own rule.
  - A demo fixture costs 0; a kind no person starts is `422 no_estimate_for_kind`.
  - Its kinds map to the same worst-case functions as `worker.TASKS`; a fast test keeps them
    equal.
  - The web side is the `RunEstimate` component with `useRunEstimate`, for Tasks 6e, 7e and 8.
    It is on no screen yet.
- **Disclosed test change.** `Directions.test.tsx` asserted the interim F10 words that named no
  control. It now asserts the words that point to the spending line, an intended change.

## 5. The product owner's own commands in `make acceptance`

- **`make demo`.** `tests/stack/test_owner_commands.py` runs the literal `make demo` on project
  `careerwright-l0-democheck` (web 57500) and a fresh home. To make that possible,
  `tools.stack` reads `CAREERWRIGHT_PROJECT` when set; the default is unchanged.
  - It checks every service is running and the web app answers at the address printed.
  - It then writes live-eval's private evidence into that home and runs `make demo` again (the
    ledger 569 refusal).
- **The session packages.** `tests/tools/test_session_packages.py` has the new marker
  `owner_commands`, so it runs in both `make check` and `make acceptance`. `make acceptance`
  now selects `-m "integration or stack or owner_commands"`.
  - Every file each `docs/reviews/session-*.md` names must exist and open: a PNG header and
    size, JSON that parses, or text.
  - Every folder a package points to must hold what it names, and every `make` command it
    gives must exist.
  - It found one real gap. Session 2's package names
    `docs/design/screenshots/route-comparison--default--1440x900.png`, removed in W2A
    (d989d15). A held session's package is a record and is not rewritten, so the test lists it
    as retired, with its reason.
  - Task 6e's session W2 package will be checked automatically.

## Checks

- `make check` on the rebased tree passed: backend ruff, mypy, 1,706 fast tests and the
  fixture validator; web client drift, Biome, tsc, and Vitest 387 tests in 40 files.
- Integration runs under the lock, before the rebase:
  - the durable-runs file, 19 passed;
  - the worker-using files, 133 passed;
  - `test_live_session.py`, 4 passed.
- `make acceptance`, once, under the lock, on 11e2914: see "Acceptance" below.

## Live calls

I made none. The controller made rows 36-43 ($0.115534), listed above.

## Not run / concerns

- `make session` and `make session-ledger` were not run against the real stack. That is the
  controller's or the product owner's act. `set_session_caps` and the ledger copy were run
  offline against the real API and database schema.
- The first live run of the real-data path is the controller's (the command is below).
- Human-only: keyboard and VoiceOver review of the spending line (H-03). Not run, requires a
  human.
- Wonder's `max_tool_calls` keeping is not shown (row 37), and Wonder's one search excluded all
  of its candidates for their URL scheme. Both are for Task 8 to watch.
- The ledger's Markdown header now reads "Careerwright tooling". The generator already said
  this; regenerating rewrote the old "Nessa" wording.

## The first live run (the controller's)

1. Rebuild the images from the integrated code: `cd backend && uv run --locked python -m
   tools.stack build`. The acceptance run above built them from this branch.
2. Run `make session` from a tree with `.env`.
3. In the app (`http://127.0.0.1:53000`), sign in as Ada and create a workspace not marked
   synthetic. Store the key, send one interview turn in a synthetic persona's words, then
   Help me explore (a discovery) and its written note.
4. Run `make session-ledger`.

Caps: $0.75 a run and $5 for the session. A new workspace gets them from the API's defaults when
its key is stored.

Worst cases on Wonder, with all three attempts of each run:

| Run | Worst case (all three attempts) |
|---|---|
| Interview turn | $0.528 |
| Discovery | $0.468 |
| Written note | $0.552 |
| All three | $1.548 |

A worker crash can never take one run past $0.75. From rows 38-43 the expected cost is about
$0.05 in all.

## Paths a reviewer can skip

`apps/web/src/generated/` (regenerated client), `docs/evidence/live-usage.md` (generated),
`docs/evidence/live-usage.jsonl` and `live-eval.md` (the controller's rows).

## Acceptance (added in fix round 1; review M8)

- On 11e2914 (the original head): the controller's run, recorded in the progress ledger.
  `make acceptance` under the lock, 15:47:30-16:04:02, exit 0: pytest integration and stack
  381 passed (1,689 deselected), the Storybook build, Playwright 56 passed. My own run on
  11e2914 was killed by the machine's reboot and never recorded.
- After fix round 1, on c2af6b1: exit 0 (details under "Fix round 1", below).

# Fix round 1

Implementer: a fresh Claude (Opus 5.5), in the worktree `wt-3b`. FIX_BASE 11e2914; rebased
onto `l0-local-release` at 6c9e0a8. No subagents, no live call, no `make session`, no web
request, no Docker pull, no headed browser, no `make stop`. `.env`, `~/.careerwright` and
`~/.nessa` not read; the `.env` symlink not read or staged. DBOS `application_version` is
still `careerwright-l0-1`.

## Commits (after the rebase onto 6c9e0a8)

| SHA | What |
|---|---|
| 3a208ea | I1, M4 (documents), M5, M6, M7: `make session`'s caps per workspace with its total ceiling printed; restarts said; the ledger copy's label; one project; ADR 0003's bound |
| bc49ad6 | M1, M2, M3: the spending words, the menu's name, the estimate refused by the run limit |
| c2af6b1 | Register: MODEL-08, MODEL-10, MODEL-11 and BND1-14 (last commit, after the rebase) |

The rebase moved the six original commits to 4c9b72d..b54a993 with no conflict.
`pnpm run generate` after it changed nothing (the merged client equals the backend's
document); `vocabulary.ts` merged cleanly, with Task 6d's words and mine both kept.

## Each finding

**I1. The caps are per workspace (the product owner's ruling, 31 October 2026).**
- The code's behaviour is unchanged: $0.75 a run, and $5 on top of what each live
  workspace has committed this month.
- `make session` now prints its total ceiling. `session_summary` (new, `tools/session.py`)
  says the caps are per workspace and gives the total: $5 for each workspace capped now, and
  $5 more for each workspace whose key is stored during the session.
  - For example, with two workspaces: "So this session can spend at most $10.000000 in all:
    $5.000000 for each of the 2 workspaces capped now. Each workspace whose key is stored
    during the session adds $5.000000."
- The constant is renamed `SESSION_SPEND_PER_WORKSPACE_NANO_USD` (was
  `SESSION_SPEND_NANO_USD`), so the code says it too.
- "Per workspace" is now said in: the Makefile help, the command's docstring and start
  summary, the runbook, the ledger's generated header (`usage_ledger.py`, `.md`
  regenerated: header only, no row changed), ADR 0003's "Qualification result" (a new
  paragraph: the ruling settles the amendment's "about $5 a session"), and register rows
  MODEL-08 and MODEL-11.
- Test: `tests/tools/test_session.py::test_the_start_summary_says_the_caps_are_per_workspace_with_the_session_s_ceiling`
  (two, one and no workspaces).

**M1. The spending line's words.** `SPENDING.unknown` now says what Careerwright does: "Careerwright
counts 1 call at its most until its cost is known." / "Careerwright counts 3 calls at their
most until their costs are known." True for calls in flight and for costs Meta never
reported. Tests: `ModelSpending.test.tsx` (the existing case's words, and a new plural case).

**M2. The menu's name.** I named what sighted people see: "You can raise the limit under Model
spending, in the menu at the top." Why not "top right": on a phone the account menu sits
in the strip's second row, left of centre, beside "Answers saved"; "at the top" is true on
every layout. On a tablet or desktop it is the only menu glyph at the top. I gave the trigger
no visible label: it would widen the phone strip, which the browser journeys hold to one
height. Tests: `ModelSpending.test.tsx` (the words, and that the failure words carry them),
`RunEstimate.test.tsx`, `Directions.test.tsx`.

**M3. The estimate refused by the run limit.** When `refused_scope` is `run`, the API's maxima
are clipped to the run limit, so `RunEstimate` shows only the refusal and no cost sentence.
The API is unchanged. Test: `RunEstimate.test.tsx`, "when the run limit refuses it, never
states that limit as its cost". New story `Spending/EstimateRefusedByTheRunLimit`.

**M4, documents only.** The Makefile help, the docstring, the start message and the runbook
now say: a running API and worker restart with the session's settings (Compose recreates the
two services that take the model settings); a run in flight restarts, its interrupted call
counted at its full reservation; nothing else is stopped and no data is reset. `make dev`
afterwards restarts them again. Settling in-flight calls before `os._exit` waits for the
final review, as the fix list says.

**M5. `make session-ledger`.**
- The runbook, the Makefile help, the docstring and the start summary say the stack must be
  up (before `make stop`).
- I relabelled it rather than filtering by session: no record marks a session's start.
  - Scope `live-app-<date>` (was `live-session-<date>`).
  - Purpose "live app: one interview turn attempt from the live stack's database (`make
    session-ledger` copies every attempt there, by its UTC date: model, kind, counts, cost
    and state only)".
  - No row had used the old scope, so nothing in the ledger changes. The duplicate check
    reads the new prefix, with its hyphen, so `live-adzuna` can never match it.
- Tests: `test_session.py::test_a_copied_attempt_keeps_its_counts_and_an_unknown_cost_counts_its_reservation`
  (scope and purpose), `test_live_session.py::test_the_ledger_copy_reads_counts_cost_and_state_only_and_writes_no_text`
  (scope).

**M6. ADR 0003's bound.** It now says the activity checks a search's measured searches and
input tokens against its reservation's bounds only after the call. An attempt past them
fails `bound_exceeded`, but its spend has already happened and is counted. (The original
report's section 1 has the same overstatement: "the activity's input-token bound still
holds each search's token cost to its reservation". This correction applies there too.)

**M7. `CAREERWRIGHT_PROJECT`.** It is read in one place now, `tools.stack.project_from_env()`.
`tools.stack`'s CLI (`make dev`, `demo`, `stop`, `reset-demo`, `status`) and
`session_stack()` (`make session`, `make session-ledger`) both use it. So `make session`
and `make stop` always act on the same stack. Test:
`test_session.py::test_make_session_and_make_stop_act_on_the_same_project`. It runs
`tools.stack.main(["stop"])` with Docker's `Stack.stop` replaced, unset and set.

**M8.** The "Acceptance" section is added above. The original's undisclosed test change:
`tests/domain/test_model_registry.py::test_the_registry_records_capabilities_and_evaluation_only_where_a_call_established_them`
moved `muse-wonder-1.0` from the "listed only" list (no capabilities, "not evaluated") to the
qualified list (all three capabilities, "ADR 0003" and "rows 36-37" in its evaluation). It
was intended: the controller's qualification calls established them (rows 36-43).

## Changed test inputs and assertions (disclosed)

- `tests/tools/test_session.py`:
  - `test_the_session_is_the_normal_live_stack_with_wonder_and_the_session_s_caps` now unsets
    `CAREERWRIGHT_PROJECT` first: the project now follows it.
  - `test_the_session_adds_five_dollars_to_what_the_month_has_committed` is renamed
    `..._to_what_the_workspace_s_month_has_committed`. Same assertion.
  - The copied-attempt test's scope changed from `live-session-2026-11-02` to
    `live-app-2026-11-02` (M5), and a purpose assertion was added.
  - The old constant's uses are renamed, and one docstring reads "a workspace's $5".
- `tests/integration/test_live_session.py`: the constant renamed, the scope assertion
  `live-session-` → `live-app-`, comments "per workspace". No assertion was loosened.
- `ModelSpending.test.tsx`: the unknown-cost words (M1) and the menu words (M2) changed, a test
  title changed, one test added.
- `RunEstimate.test.tsx`: the refusal's menu words (M2) changed, one test added (M3).
- `Directions.test.tsx`: the budget-exceeded words (M2) changed.

## RED, then GREEN

Backend, `cd backend && uv run --locked pytest tests/tools/test_session.py -q`:
- RED 1 (the tests, before any fix): collection failed, `ImportError: cannot import name
  'SESSION_SPEND_PER_WORKSPACE_NANO_USD'` (and `session_summary` did not exist).
- RED 2 (after I1's fix, before M5 and M7): `2 failed, 14 passed`:
  - `test_make_session_and_make_stop_act_on_the_same_project`: `assert 'careerwright-l0' ==
    'careerwright-l0-elsewhere'`;
  - `test_a_copied_attempt_keeps_its_counts_and_an_unknown_cost_counts_its_reservation`:
    `assert 'live-session-2026-11-02' == 'live-app-2026-11-02'`.
- GREEN: `16 passed`. All tool tests: `uv run --locked pytest tests/tools -q`, `181 passed`.

Web, `cd apps/web && pnpm exec vitest run src/components/ModelSpending.test.tsx src/components/RunEstimate.test.tsx src/components/Directions.test.tsx`:
- RED 1 (the tests, before any fix): `6 failed | 34 passed`. Every changed or new word was not
  found (Directions 1, ModelSpending 3, RunEstimate 2).
- RED 2 (after M1 and M2, before M3): `1 failed | 39 passed`. "when the run limit refuses it,
  never states that limit as its cost": `expected <p class="small"></p> to be null` (the
  cost sentence with $0.15 was shown).
- GREEN: `40 passed`.

## Checks on the final head (c2af6b1)

- `make check`: exit 0.
  - Backend: ruff format (350 files) and lint clean, mypy clean (350 files), 1,710 fast
    tests passed (367 deselected), and the fixture validator passed.
  - Web: the generated client matches the backend's document; Biome, tsc, and Vitest 391
    tests in 40 files passed.
  - No warnings.
- `make acceptance`, once, under the lock (one guarded command that waited for the lock;
  taken 17:42:00, released 17:56:59), exit 0:
  - pytest integration, stack and owner commands: 384 passed (1,693 deselected), including
    `test_live_session.py` with the renamed constant and the `live-app-` scope;
  - the Storybook build, with the new story;
  - Playwright: 56 passed.
  - Log: `scratchpad/acceptance-3b-fix1.log` (this session's scratchpad).

## Not run / concerns

- No live call made: $0 this round. `make session` and `make session-ledger` were not run
  against the real stack. That is the controller's or the product owner's act.
- Left as records, not rewritten:
  - ADR 0003's amendment ("about $5 a session"): the new paragraph settles it.
  - Task 3b's card in `docs/plan/l0-sprint-tasks.md` ("about $5 a session").
  - The audit (`docs/reviews/l0-audit-2026-10-31.md`).
  - The controller may want the card to say "per workspace" too. It wasn't in my list.
- `make session-ledger` still fails with a connection traceback when the stack is down. The
  documents and the start summary now say the stack must be up; the code is unchanged, as
  the fix list asked.
- Amounts in the start summary use `format_usd`'s six decimals ("$5.000000"), as before.
- M2's words were not judged on a real screen; that is human review (H-03, not run,
  requires a human).
