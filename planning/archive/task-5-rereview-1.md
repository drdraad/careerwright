# Task 5 re-review 1 (fix round 1, 56db48f..38c2fce)

Scope: I checked each finding in `task-5-fix-round-1.md` against the fix diff, reviewed the
new streaming design in depth, and looked for regressions. This is not a fresh full review.

Method:
- I read the 5.3k-line diff in six passes: web; API and catalogue; activity, identity and
  migrations; profile and worker; tests; docs.
- Outside the diff I made one focused check per named risk. Each is cited below.
- I re-ran no suites. I made no live calls and started no Docker.
- I ran two in-process probes with `uv run --locked python -I`. They used no database and no
  network. The scripts are in my scratchpad (`probe/cut_stream_probe.py`,
  `probe/throttle_probe.py`). They:
  - ran `run_interview_turn` on the repo's fake and fixture models;
  - passed the messages to `activity._measured`;
  - used the real `_PartialWriter` with its `_write` replaced by a list append.
- The working tree was not modified.

## Finding status

Counts: **25 Fixed, 1 Partially fixed, 0 Not fixed.** "Old?" says whether the covering test
would fail on the old behaviour.

### Must-fix

| ID | Status | Evidence | Covering test | Old? |
|---|---|---|---|---|
| B-I3 | **Partially fixed** | Every structural item in the ruling is in place; see the streaming section below. The stream's content is lossy, though. `_PartialWriter` throttles on the leading edge only (`identity/activity.py:157-172`), and `ReplyStream` stops calling the sink once `reply` stops growing (`profile/interview_agent.py:73-87`). So the store keeps the last throttled prefix while the proposals are generated (new Important N1). The live row-14 run made one write; the fixture writes `'Demo interviewer (synt'`. | Domain: `test_interview_agent.py:125,156,170`. Integration: `test_interview_turns.py:228,268`. | Yes, each RED is reported. None checks what the store holds once the reply is complete. |
| B-I1 | Fixed | `_spend` returns unknown when `responses < requests_sent` (`activity.py:418-426`). `_measured` drops responses with no usage (`:340`). Probe: `invalid_then_unavailable` gives 2 requests and 1 measured response, so `unknown`. | `test_interview_turns.py:352` (3 attempts, `unknown`, cost null, 3.5M each, period 3×3.5M) | Yes (RED `('reconciled', 31800)`) |
| B-I2 | Fixed (per ruling: size the default) | Default is now $0.15 (`config.py:121-123`). The invariant `ACTIVITY_MAX_ATTEMPTS × worst case ≤ default` is checked per task kind. The gaps that remain are in M6. | `test_spend.py:78`; `test_interview_turns.py:334` (non-synthetic, Standard model, 3 × 49M unknown, `provider_unavailable`) | Yes |
| B-M1 | Fixed | `TruncationGuard` (`activity.py:192`) keeps the cut-off response in the history and raises `OutputTruncatedError`, which is classified `output_truncated` (`failures.py`). Probe: 1 request, 1 response, booked once, no double append. | `test_interview_agent.py:213`; `test_interview_turns.py:311` `(1, "reconciled")` | Yes (old sent 2 requests) |
| B-M7 | Fixed | `_basis` and `_quoted` (`profile/interview.py:249-268`) keep `stated` only when the cited messages contain the value. The API description says so (`interview_schemas.py`). | `test_interview_contract.py:117,141,150,171` | Yes |
| B-M8 | Fixed | `insert_attempt` writes 0 for `none`. `_spend` returns `(NONE, 0)`. r0006 adds the CHECKs and backfills old rows. `committed_cost` already treats `none` as 0, so the totals do not change. | `test_migrations.py:190`; demo and budget assertions in `test_interview_turns.py` | Yes |
| B-M9 | Fixed | `_published_bound` puts `maxItems` in the schema only (`profile/document.py:79`). Validation and its error shape are unchanged. The web's `listLimit` reads `schemas.gen` (`apps/web/src/lib/profile.ts:62`), and the hand-coded `limit` is gone. Prose bounds remain (M9). | `test_openapi.py:69`; `profile.test.ts` "takes every list bound…" | Yes |
| A-M1 | Fixed | `nessa.concept_key` is one IMMUTABLE SQL function with a pre-parsed `RETURN` body, so the index is safe from `search_path` changes. It has an expression index. The API (`taxonomy_store.py:251`) and the trigger both use it, and the trigger derives the key from `NEW.title`. | `test_provisional_concepts.py:76` (the reviewer's three examples), `:106` (`Plumbers!` with a false `normalised_title`) | Yes (RED 201≠422, DID NOT RAISE) |
| A-M2 | Fixed | `ADAPTATION` (`esco.py:37`) is in the manifest (r0008 backfills it and sets NOT NULL), in every `TaxonomyReleaseOut`, which every search carries, and in `OccupationOut`. `docs/dependencies.md` records it as "not settled… H-11". | `test_taxonomy.py:61,172` | Yes |
| A-M4 | Fixed | `full_text_total: int \| None`, and `None` on the label-only path (`taxonomy.py:79,100`). The field is documented in the schema. | `test_taxonomy.py:84` | Yes |
| A-M6 | Fixed | A `pg_api` count for owner vs. other account was added. | `test_provisional_concepts.py:90` | Coverage only (passed at once, as declared) |
| A-M11 | Fixed | `concept_kind` is a `Literal` const on label matches, hits, occupation detail and provisional concepts (`catalogue_schemas.py:91,113,…`), and is included in the export. | `test_provisional_concepts.py` (set and value), `test_taxonomy.py:173` and the alias test | Yes |

### Cheap fixes

| ID | Status | Evidence / test |
|---|---|---|
| A-M3 | Fixed | `is_held` (`taxonomy.py:34`) adds the transformation version to the check, in both the CLI and `import_release`. Covered by `test_taxonomy.py:265` (RED: DID NOT RAISE). |
| A-M5 | Fixed | The post-lock branch is called directly (`test_taxonomy.py:232`). `test_taxonomy.py:283` gets a `ForeignKeyViolation` and all 9 tables stay empty. Coverage only. |
| A-M7 | Fixed | The pin-literal test, the no-op `replace` and the `print` are gone. The city contract is now checked through the `GET /v1/places` keys (`test_taxonomy.py:187`). |
| A-M8 | Fixed | The text now says "value-for-value" in `tools/esco_sample.py` and the sample README. |
| A-M9 | Fixed | `place()` and `_BY_ID` are removed. Profiles store the label, so nothing else is affected. |
| A-M10 | Fixed | Plain "Newcastle" is no longer an alias (`places.py:92`), and the change is on H-11. Covered by `test_places.py:45`. Stored documents hold "Newcastle-upon-Tyne", so none breaks. |
| B-M2 | Fixed | The `meta.py` docstring now matches the per-task bounds. |
| B-M3 | Fixed | The runbook reseal line lists keys, inputs, outputs and partials. |
| B-M4 | Fixed | `test_interview_turns.py:564` covers both CHECKs by name. `model_refusal` is tested in `test_model_choice.py:90`. |
| B-M5 | Fixed | The test now has a second run and another workspace, and asserts the real workspace scope (`test_interview_turns.py:589`). |
| B-M6 | Fixed | "the complete list after the change" now appears in both the instructions (`interview.py:362`) and the field description (`interview_schemas.py:30`). |
| B-M10 | Fixed | `model_builder(provider=…)` (`worker.py:54`); the test worker passes the fake. |
| B-M11 | Fixed | The `_MONEY` regex is bounded by a lookahead. I traced both reviewer amounts: neither matches. Covered by `test_interview_agent.py:235`. |
| B-M12 | Fixed | `test_interview_agent.py:225` gives one repair naming `ready_for_review`, then `invalid_model_output`. |

## Streaming design (B-I3), checked point by point

- **Sealed, rotation, RLS: ✅**
  - `record_partial` seals with `partial_context(workspace, run)` (`identity/runs.py`).
  - `make reseal` covers `run_partials` (`cli.py` reseal map). `_tables_on_old_versions` would also catch a miss, and the rotation test includes a partial.
  - r0007 follows the existing policy pattern:
    - the API gets SELECT only, scoped through the workspaces RLS (the same shape as `run_outputs`, r0002:195);
    - the worker is scoped to `authorised_run_workspace()` **and** `current_run_id()`, which is narrower than `run_outputs`.
  - The read path goes through `visible_turn`, which checks the workspace and filters the turn by workspace. A non-owner or another workspace gets the same 404 as a missing turn (`test_interview_turns.py:228`: Ben gets 404, and `pg_api` shows him 0 rows).
- **IDs and sequence only: ✅**
  - The event detail is `{"seq": n}` with `state` null (asserted).
  - The step's journal sees `run_id` and the `Outcome` dict only.
  - The write-failure log has `run_id` and `error_class` only.
  - The leak-scan coverage of the partial is nominal, though (M2).
- **Superseded, incomplete, never final: ✅**
  - On success, `delete_partial` runs in the `_settle` transaction that stores the output (`activity.py:447`).
  - A failed attempt calls `end_partial(latest)` (`:435`), and `publish` marks a crash-left `streaming` row (`:511`).
  - `partial_reply` answers `superseded` with no text once the run is complete, and forces `incomplete` for a failed run.
  - Nothing partial enters a turn's context, a proposal or the profile. The decision on a failed turn is refused with `PROPOSAL_NOT_AVAILABLE` (tested).
  - Small caveats: M3 (wording between retries) and M5 (a read race).
- **Bounded writes, one retry owner: ✅ with N1.**
  - There is at most one write and one event per 0.25 s.
  - The text is bounded by `max_tokens=1500` per request. There is no separate character cap, which I find acceptable.
  - A failed write sets `_stopped` and never raises into the call, so there is no step retry and no second paid call.
  - A crash mid-stream leaves a consistent state:
    - the `streaming` row stays readable by the owner;
    - recovery interrupts the held attempt as `unknown` (the existing ADR 0002 crash semantics);
    - the row is deleted on completion (tested with SIGKILL).
  - But the throttle drops the trailing edge (N1). In `_settle`, the incomplete mark can also abort the settlement (M1).
- **Deletion and reset: ✅ (by schema, untested).**
  - `run_partials (workspace_id, run_id) → runs ON DELETE CASCADE`, and `runs → workspaces ON DELETE CASCADE` (r0002:82).
  - `reset-demo` deletes the fixture workspace, so its partials go with it. No test asserts this for partials.
- **The $0 cost bug: ⚠️ partly.**
  - A request-level failure leaves an `interrupted` response with no usage, and `_measured` excludes it (probe: 0/0 tokens, so `unknown`). ✅
  - **A stream cut part-way is still booked as known** (N2).

## Contract changes

Each change is documented in ADR 0006. I spot-checked the regenerated client in
`apps/web/src/generated/openapi.json`: it has `get_turn_reply` and `PartialReplyOut`, the
`concept_kind` consts, and a nullable `full_text_total`. Nothing in the web outside
`generated/` reads `full_text_total`, `cost_nano_usd` or `concept_kind`, so nothing in the web
breaks.

- **$0.15 default run limit.** Documented in `config.py` and ADR 0006 decision 9. It applies
  only to `spend_limits` rows created after the change (M6).
- **No-call cost is 0.** Migration, CHECKs, API description and upgrade test are all there.
- **`concept_kind`, `adaptation` and the reply endpoint.** Additive. Listed under ADR 0006
  Consequences.
- **Nullable `full_text_total`.** This narrows the type, but it was introduced in this same
  task and has no consumers yet.
- **Export.** `concept_kind` is added at format 2. Format 2 is new in this task and there is
  no importer, so this is sound. Partials are not exported (ADR 0006 decision 15).

## H-11 provisional decisions

H-11 is recorded as "not run — requires human" (register line 628 and ADR 0006 line 270
onward). Nothing is claimed as passed or settled.

The status line labels decisions 4 (regions), 6 (hard constraints) and 8 (no-value basis)
"provisional, need product owner confirmation". The H-11 checklist also lists two items whose
decision text carries no such label (M7):
- the concept-key folding (decision 5);
- the "Newcastle" refusal.

The ESCO licence reading is a rights review (R2). `docs/dependencies.md` says "not settled".

## New issues in the fix diff

### Critical
None.

### Important

**N1. The partial store misses the end of the reply.**
- Where: `backend/src/nessa/identity/activity.py:157-172` and
  `backend/src/nessa/profile/interview_agent.py:73-87`.
- What: the writer writes only the first sink call in each 0.25 s window. `ReplyStream`
  calls the sink only when `reply` grows, and `reply` is the first field. Whatever arrived
  after the last write is never stored until the validated output supersedes the row. That
  is for the whole time the proposals are being generated.
- Evidence:
  - Probe with the real `_PartialWriter` and the fixture: 1 write, `'Demo interviewer (synt'`,
    against the full reply `'Demo interviewer (synthetic): I noted 2 things…'`.
  - Live row 14: "superseded after 1 writes". The report reads this as a small gain on a short
    reply, but the store held the first delta only.
  - The claim that "a longer reply streams in several writes, as the domain tests show" is
    not shown: those tests observe sink calls, not writes.
- Why it matters: the stream exists for responsiveness (spec section 4). As built, a client
  polling `/reply` sees a reply cut off mid-word for most of the turn.
- Fix: add a trailing flush. Hold the pending text, and write it when the interval elapses
  on a later stream event (forward non-growing events, or add a timer), and as soon as the
  reply string closes (when a later key appears).
- Test: a fake that streams the reply quickly, then pauses before the proposals. Assert that
  the stored partial equals the full reply before the output is stored.

**N2. A stream cut part-way is reconciled at a partial cost.**
- Where: `backend/src/nessa/identity/activity.py:340` and `:418-426`.
- What: `_measured` counts any response whose usage has values. An `interrupted` streamed
  response (pydantic-ai `_agent_graph.py:285-302,1888-1905`) keeps whatever usage had
  accumulated when the stream broke.
- Evidence: probe with `cut_mid_stream`: 1 request, 1 measured response
  (`state='interrupted'`, 50 in / 16 out), so `_spend` returns `RECONCILED` at a partial
  cost. The three attempts of
  `test_a_reply_cut_off_mid_stream_ends_observably_with_the_partial_marked_incomplete` are
  booked this way, and the test does not assert `spend_state`.
- In production: Meta's Responses stream records usage on `in_progress`/`queued` events too
  (`pydantic_ai/models/openai.py` around line 6003). Whether this under-books therefore
  depends on what Meta reports before completion. The rule is wrong either way: a cut-off
  call is an ambiguous charge.
- Why it matters: this breaks MODEL-08 ("ambiguous charges recorded as unknown") and ADR
  0004 decision 10. ADR 0006 decision 13's "Cost" bullet (line 224) is inaccurate for this
  case. It is the same class of defect as B-I1, reintroduced by streaming.
- Fix: treat an `interrupted` response as unmeasured, so the attempt is `unknown` with its
  whole reservation. Assert `unknown` and the full reservation in the cut-mid-stream
  integration test.

### Minor

**M1. The incomplete mark can abort the attempt's settlement.**
- Where: `activity.py:435`.
- What: `end_partial(latest)` runs inside the `_settle` transaction. If access is revoked
  mid-call, `upsert_partial` fails the worker policy's WITH CHECK and raises. That aborts
  `finish_attempt` too. `execute` then ends the run `unknown_failure`, not the real class,
  and the attempt's known usage becomes `unknown`. The money side is conservative, but the
  cause is wrong.
- Fix: wrap the call in a savepoint (`begin_nested`), or skip it when
  `authorised_workspace(tx) != run.workspace_id`.

**M2. The leak scans never see partial text that contains a sentinel.**
- Where: `tests/support/fake_models.py:75` (the sentinel ends the reply) and `:193`
  (`break_after=3`).
- What: the crash and cut points store only a prefix of the reply, without the sentinel. At
  `test_interview_turns.py:264`, `leaks(secret)` scans for the message sentinel, which the
  reply never contains. Its comment ("the streamed text is sealed") claims more than the test
  shows. Sealing is proven only indirectly, because the API opens the partial with
  `partial_context`.
- Fix: put the output sentinel at the start of the fake reply.

**M3. `incomplete` is worded as final, but it is not always.**
- Where: `interview_schemas.py:66` and `records.py:90`.
- What: the text says "it stopped and will not complete". Between DBOS step retries, a run
  that is still running shows `incomplete`, then streams again.
- Fix: reword to "this attempt's reply stopped; the run state says whether another
  follows".

**M4. The web will refetch every query on every partial event.**
- Where: `apps/web/src/lib/queries.ts:171-182,232-235`.
- What: the web refetches the whole workspace scope, the workspace list and `me` on every
  event. `run.partial_updated` can arrive up to 4 times a second per streaming turn.
- Fix: T6 should filter partial events to the turn's `/reply` query.

**M5. A poll racing the output commit can answer `none`.**
- Where: `routes_interview.py:89` and `runs.py:109`.
- What: the run status and the partial are separate READ COMMITTED statements. A poll that
  races the output commit can answer `none` for a run that has just completed. No text
  leaks, so this is cosmetic.

**M6. The B-I2 fix does not reach every workspace.**
- Where: `credential_store.py:157` and `credentials.py:88`.
- What: the default is persisted when a key is stored, with `ON CONFLICT DO NOTHING`.
  Existing workspaces keep $0.10 and still report an outage as over budget. So do:
  - any run limit a user sets below $0.147;
  - a crash followed by an outage: one interrupted attempt plus three retries is 196M.
- Fix: say so in ADR 0006 decision 9. Or end such a run with its last transient class.

**M7. H-11 labelling is incomplete.**
- Where: ADR 0006 status line 5 and decisions 4 and 5.
- What: the concept-key heuristic and the "Newcastle" refusal are on the checklist but are
  not labelled "provisional, needs product owner confirmation". The report says they are.

**M8. Task 6's brief does not mention streaming.**
- Where: `docs/plan/l0-sprint-tasks.md` (around lines 257-271).
- What: the brief still does not mention rendering the streamed reply. Only the MODEL-03
  row (owner "T5, T6") and ADR 0006 give T6 that work. This is the controller's to add.

**M9. Some web hint text still states the bounds.**
- Where: `apps/web/src/lib/vocabulary.ts:90,97`.
- What: the hints still say "Up to three…", which can drift from the published `maxItems`.

## Not verified
- I did not re-run `make check` or `make acceptance`. I re-ran no integration test and made
  no live call. The pass counts and the ledger-row-14 outcome are the implementer's claims.
  I did recompute row 14: 1,147×100 + 632×200 = 241,100 nano-USD, and the running total is
  $0.020200 ✅.
- I did not check what Meta reports in its streamed usage before completion. N2 depends on
  it in production.

## Assessment
**Task quality:** Needs fixes

**Reasoning:** Every listed finding except B-I3 is fixed, and the tests would fail on the old
behaviour. The partial store's sealing, RLS, ID-only events, supersession and failure states
are sound. But the stream drops the end of the reply until the validated output arrives (N1),
and a stream cut part-way is booked as a known partial cost instead of unknown (N2). Both are
small fixes with focused tests.
