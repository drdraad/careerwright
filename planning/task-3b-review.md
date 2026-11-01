# Task 3b review: live sessions on Muse Wonder (8ad36a6..11e2914)

Reviewer: Claude (Opus 5.5), read-only. I read the brief, the dispatch, the report and the
whole 4,282-line diff in five passes (web; API and identity; tests; tools; documents and
ledger). Outside the diff I made one focused check per named risk, listed where used. I ran
no tests: no doubt needed one that the code and the existing tests did not answer.

### Spec Compliance

- ❌ Issues found:
  - The "$5 a session" cap holds per workspace, not per session.
    `backend/tools/session.py:59,110,121,145`. See Important I1.
- ⚠️ Cannot verify from diff:
  - The regression test failing before the fix ("RED first"). The test and the fix are one
    commit (36b164a), so the history can't show it. The test itself would catch the hang:
    it needs exit code 0 within `SHUTDOWN_DEADLINE_S + 5`, so neither the watchdog's exit 75
    nor a timeout passes.
  - `make acceptance` on 11e2914. The report says "see 'Acceptance' below", but the report
    has no such section. The controller runs it.
  - `make session` and `make session-ledger` against the real stack, and the first live run
    of the real-data path. Both are the controller's acts.
  - The controller's rows 36-43. They add up to $0.115534 in the JSONL (my sum), and the
    JSONL only gained lines, so nothing earlier was rewritten.

Checked against what matters most:
- **Caps checked before any call.**
  - `make live-smoke WONDER=1`: $0.20 an invocation (`live_smoke.py:264`).
  - `make live-eval WONDER=1`: $0.40 an invocation (`live_eval.py:89`).
  - Both share one scope of 14 requests and $0.50 (`live_smoke.py:259`). Committed spend
    counts unknown costs at their full reservation.
  - Each invocation is authorised under the ledger's lock before its stack or call starts.
  - The run sequence held the $0.50: $0.149, then $0.332, $0.352 and $0.368, each checked
    against what had been committed by then. 14 of 14 requests used.
  - `--wonder` runs alone. `--search`, `--search-bound` and `--extract` stay on the test
    model. Without the flag, Wonder's connection check ($0.171) and interview turn ($0.176)
    pass Spark's $0.10 cap and are refused. I found no path that reaches Wonder past the
    Spark-sized cap.
- **The test model and demo workspaces.**
  - `make session` pins the synthetic role to the test model.
  - The database CHECK is untouched, and `test_live_session.py` proves it still refuses
    personal data on the test model.
  - Demo workspaces still get only fixture stand-ins.
  - The qualification ran Wonder on synthetic workspaces, as the brief asked.
- **The session reuses the product owner's stack and data.**
  - It uses `make dev`'s project, `CAREERWRIGHT_HOME` and ports with `--no-build`. Nothing
    is taken down or reset.
  - No test starts it. `test_session.py` dry-runs `make -n` only, and `check` and
    `acceptance` never name it.
  - The acceptance run's `make demo` uses its own project, home and ports. I checked that
    `tools.stack` reads `CAREERWRIGHT_PROJECT` and `CAREERWRIGHT_HOME`, and that its ports
    (57200/57299/57632/57500) clash with no other test stack.
- **Per-workspace caps reach every live workspace** (focused check: where limits come
  from).
  - The worker refuses any workspace with no stored limits (`activity.py:466-475`).
  - Storing a key writes the API's defaults (`credentials.py:88`).
  - So a workspace keyed during the session gets $0.75 and $5. An existing one gets
    committed spend plus $5 through the expected-version PUT.
  - Spark's defaults can't reach a Wonder run unnoticed. They would refuse it, which is safe.
- **The ledger copy reads no text.**
  - `COPIED_COLUMNS` holds only IDs, model, kind, counts, cost, reservation, state and time.
  - The integration test runs the copy as a database role granted only those columns. It
    also shows that no message, output, profile text or key fragment reaches the files.
- **Keys.** No new code prints, logs or passes a key.
  - `qualify_wonder` scans the requests sent, the results and the rows.
  - The session tool uses only the emulator's documented local passwords and the
    superuser password file, in-process, the same way `live_smoke` already does.
  - `Api.call` raises with the error code only.
- **R11.** `RunEstimateOut` carries codes and numbers. A kind no person starts gets a 422
  with `reason: no_estimate_for_kind`. The web words everything from `vocabulary.ts` with
  exhaustive maps (`USD_INPUT_PROBLEM`, `RUN_ESTIMATE.refused satisfies
  Record<BudgetScope, …>`).

The report's four concerns, judged:
1. **"searches 3" against 1 billed search (row 37).** The reading is sound, and the upper
   bound is stated honestly. I checked Pydantic AI's counter (`openai.py:6788-6810`):
   - It falls back to counting `search` actions only when Meta sends no
     `tool_usage.web_search.num_requests`.
   - In a streamed reply, each web-search call keeps one call part (`openai.py:6025, 6139`).
   - So three `query` parts mean three search actions. A billed count of 1 means Meta
     reported its own count.
   - "max_tool_calls 1 not shown" is the right, cautious conclusion. The $0.005 upper bound
     is in the ledger header, ADR 0003 and the registry.
   - One wording slip is Minor M6.
2. **`make session` and `make session-ledger` never run on the real stack.** Acceptable as
   the controller's act.
   - The parts that matter for money and privacy are covered offline through the real API
     and schema: `set_session_caps`, `session_entry`, `copy_session_calls`.
   - The rest is untested: `start()` (emulator sign-in, compose overrides) and
     `copy_ledger()` (published port, superuser file). Both follow patterns `live_smoke`
     has already shown working.
   - The controller's first live run will exercise both. Record it before session W2.
3. **INT-01 read as a model result.** Agreed. "What other hands-on tasks have you enjoyed,
   and what kinds of tasks drain you most?" asks two things, and the check counted them
   correctly.
   - It is one of three interview cases on Wonder. Task 6e's session W2 package should say
     that Wonder may ask two things at once, so the product owner judges it knowingly.
4. **The ledger header rewording.** Acceptable.
   - Only the generated header changed: "Nessa tooling" became "Careerwright tooling", and
     the env-var names now match the real `CAREERWRIGHT_*` names.
   - No row in either file changed (the JSONL diff has no deletions; the Markdown hunks are
     the header plus rows 36-43). The rename rule protects records, not generator text.

### Strengths

- **The caps are done well.**
  - They are named constants, checked before any call, and unknown cost counts its
    reservation.
  - Wonder can't pass Spark's cap without the flag.
  - One shared scope makes "$0.50 in all" true across the two commands.
- **The no-text test proves something real.** A column-restricted database role makes any
  extra column fail the copy. It does not just check the shape of the code.
- **The shutdown hang is fixed at its cause.**
  - The cause: the interpreter's unbounded join of DBOS executor threads. `os._exit` after
    `DBOS.destroy()` removes it.
  - The watchdog is now armed by the signal, so the whole shutdown is bounded.
  - The deadline stayed at 10 s. The regression test checks exit code 0, recovery to one
    output, and the interrupted attempt kept as `unknown`.
  - The one changed durable-runs test waits for the call to settle, not just finish, and
    keeps every assertion. That is not a loosening.
  - Ending at once loses no committed state: the journal, outbox and records are all in
    PostgreSQL transactions. It does lose an in-flight call's usage (see M4).
- **The spend estimate reuses the product's own rules.**
  - It computes with the same worst-case functions and the same refusal rule as
    submission.
  - A fast test keeps `ESTIMATED_KINDS` equal to `worker.TASKS`.
- **The dollar handling is honest.**
  - It is integer-only (BigInt when reading typed input).
  - A cost above zero never shows as "$0.00".
  - It shows no pounds figure without a pinned rate, and the demo shows no number.
- **The session packages check found a real gap** (a retired screenshot) and records it
  without rewriting a held session's record.

### Issues

#### Critical

None.

#### Important

**I1. "$5 a session" is enforced per workspace, so a session's total has no ceiling.**
- Where: `backend/tools/session.py:110,121,145-165`; the Makefile help at `Makefile:26`;
  register MODEL-08 (`docs/requirements-register.md:585`).
- What it does: `set_session_caps` gives every live workspace not marked synthetic its own
  "committed this month plus $5". The API's session default gives every workspace keyed
  during the session its own $5. So the session can spend $5 for each workspace.
- Why it matters:
  - The brief, ADR 0003 (`:155`, "about $5 a session") and the audit set a session cap.
  - The product owner's new session W2 asks about "two or three named people", which
    invites a workspace each. That makes $10-$20 of headroom, not $5.
  - Real spend will be far lower (about $0.02 a turn). But the stated money cap isn't what
    the code holds.
  - MODEL-08 says "The session's caps ($0.75 a run, $5 a session) hold", and the Makefile
    help repeats "$5 a session". The runbook and the printed summary say "each
    workspace's month", which is correct. The documents disagree with each other.
- Fix (the controller's choice):
  - (a) Accept per-workspace caps as a ruling. Say "at most $5 per workspace" in the
    Makefile help, MODEL-08, MODEL-11 and ADR 0003's result, and print the session's total
    ceiling (workspaces × $5) at start.
  - Or (b) hold one session total. For example, cap only the workspace the person names
    (the dispatch's words), and give workspaces keyed during the session a smaller default.
  - (a) is a one-line question to the product owner.

#### Minor

**M1. The spending line counts in-flight calls as unreported.**
- Where: `apps/web/src/lib/vocabulary.ts:53` with `run_store.py:542`.
- What: `unknown_cost_attempts` also counts `held` attempts. While a run is in flight, the
  line says "Meta didn't report the cost of 1 call, so Careerwright counts it at its most."
  "Spent this month" also includes the in-flight reservation.
- This breaks the sentence rule for a moment (R14 keeps such fixes in the task).
- Fix: say what Careerwright does, not what Meta did. For example, "Careerwright counts 1
  call at its most until its cost is known."

**M2. The words point to a menu name sighted people can't see.**
- Where: `vocabulary.ts:45`; the trigger at `WorkspaceStrip.tsx:217`.
- What: "under Model spending, in the Account and settings menu". "Account and settings"
  is only the trigger's `aria-label`; sighted people see a menu glyph.
- Fix: name what they see (for example "the menu at the top right"), or give the trigger
  a visible label or tooltip. Session W2 also asks which words people didn't understand.

**M3. The estimate's cost line is wrong when the run limit refuses the run.**
- Where: `spend_limits.py:96` with `RunEstimate.tsx:25`.
- What: when one attempt is bigger than the run limit (`refused_scope: run`),
  `per_run_nano_usd` is clipped to the limit. The component then says "This can cost up to
  $<limit>", which understates the need and sits next to "It needs more than this
  workspace's limit for one run".
- It is on no screen yet. Fix it before Tasks 6e, 7e and 8 use it: when the run is
  refused, show the full worst case or drop the cost sentence.

**M4. Ending the worker at once turns every stop during a call into a crash.**
- Where: `identity/worker.py:181-185`.
- What it costs: the call's usage is lost (`unknown`, counted at its full reservation, about
  $0.18 for a Wonder turn), and recovery makes a fresh paid attempt. Before, the call
  could sometimes settle first.
- It is still safe for money and ledgered, and the regression test asserts it.
- Related: `make session` recreates the api and worker containers when the model setting
  changes, so in-flight runs restart this way. Its help, docstring and runbook say
  "nothing is stopped".
- Consider at the final review: let in-flight calls settle within the deadline before
  `os._exit`, and say "restarts the API and worker" in the docs.

**M5. `make session-ledger` copies more than the session, and needs the stack running.**
- Where: `backend/tools/session.py:81,236-241,284`.
- It copies every attempt in the database, including runs made under `make dev` before any
  session, and labels them "live session: … in the app". The dates keep them apart; the
  label is loose.
- It connects to the running stack's published Postgres. After `make stop` it fails with
  a connection traceback, and the runbook doesn't say the stack must be up.
- Fix: say so in the runbook and the start message. Optionally name the purpose without
  "session".

**M6. ADR 0003 overstates what the input-token bound does.**
- Where: `docs/adr/0003-meta-model-selection.md:188`.
- What: it says the bound "still holds each search to its reservation's tokens". The bound
  is checked after the call (the attempt fails `bound_exceeded`). It doesn't stop the
  spend.
- Fix: one wording change.

**M7. `CAREERWRIGHT_PROJECT` now steers some commands but not `make session`.**
- Where: `backend/tools/stack.py:221-224` versus `backend/tools/session.py:102`.
- What: it now steers `make dev`, `stop`, `reset-demo` and `status`. `make session` always
  uses the default project. If the variable were left set in a shell, `make session` and
  `make stop` would act on different stacks.
- Fix: read it in one place, or limit it to `demo`.

**M8. Report and disclosure gaps.**
- The report points to an "Acceptance" section that doesn't exist.
- `test_model_registry.py`'s assertion change (Wonder moved from "listed only" to
  qualified) isn't in the list of disclosed test changes. The change is intended.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** Money, privacy and safety are sound. Every cap is checked before any call,
unknown costs count their reservation, no text or key reaches the ledger, the test model
and demo safeguards are unchanged, nothing touches the product owner's data, and the
shutdown hang is fixed at its cause. The one Important item is the session cap: it holds
per workspace, not per session, and the documents disagree about which. It needs a ruling
and matching words, or a single cap, before session W2.
