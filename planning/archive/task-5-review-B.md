# Task 5 review, half B: InterviewTurn contract, interview run kind, decisions, live smoke

Reviewer: independent task reviewer (half B of `10afdbf..56db48f`). I read the brief, the
carry-forward items, the implementer's report (as unverified claims) and the 9.1k-line diff
in four passes: web and API, identity and execution, profile and migration, then tests,
tools and docs. I checked code outside the diff only for named risks. I re-ran no suites. I
ran three in-process probes (no network, no database, scripts kept in my scratchpad, the
working tree untouched): partial usage when the repair request fails, the prompt budget with
a full profile, and how many requests a truncated output costs.

### Spec Compliance
- ❌ Issues found:
  - **Streaming of natural conversation now has no owner.** Spec §4 (M0) says "Stream
    natural conversation for responsiveness", and spec §16 says "Contract-test streaming".
    ADR 0006 decision 13 defers it (`docs/adr/0006-taxonomy-and-interview-contract.md:161`).
    Register row MODEL-03 still names T5 as owner and lists streaming as open
    (`docs/requirements-register.md:532`). Task 6's brief (`docs/plan/l0-sprint-tasks.md:257-271`)
    does not mention streaming, and ADR 0001 does not descope it. See Important #3. The
    brief and the S2.2 card ask only for "never commit partial streamed JSON", and that holds
    trivially because nothing is streamed. Deferring streaming is defensible. Leaving it with
    no owner is not.
- Named risks, one focused check each:
  - *The model proposes; commands commit.* I traced `decide_turn` to `commit_profile_version`
    (`backend/src/nessa/profile/conversation.py:298`) and grepped every caller of
    `insert_profile_version` and `apply_updates`. The only other path is the setup-only seed
    (`backend/src/nessa/cli.py:164`). `hard_constraint` is set on the server from
    `FIELD_SPECS` and never by the model (`backend/src/nessa/profile/interview.py`,
    `check_turn`). Cited messages map from server refs to IDs. `checked_input` runs again at
    commit. ✅
  - *Repair, partial JSON, old profile survives.* The agent has `retries={"output": 1}` and
    `request_limit=2` (`backend/src/nessa/profile/interview_agent.py:47,65`). Each attempt
    reserves both requests (Standard $0.049 and test $0.0035, which I recomputed). Each
    failure has an integration test that leaves the profile unchanged: invalid, refusal,
    truncation, unavailable, budget before and after queueing, and a stale profile. ✅,
    except partial usage (Important #1) and truncation spending the repair (Minor #1).
  - *ADR 0004 decision 7.* Submission refuses a stale `expected_profile_version`. The run
    pins `profile_version`, and a CHECK requires it for this run kind. A decision refuses to
    apply a proposal to a newer profile and names both versions. ✅ The worker cannot see the
    profile, so a turn queued against an older version still makes its model call; the
    decision is what refuses it. That costs money but never misapplies a proposal.
  - *Durable pattern.* The workflow carries only IDs. Run inputs are sealed with kind,
    workspace and run as associated data, and opened inside `_call` just in time. A message
    sentinel is leak-scanned in DBOS and in the logs. Exception messages are discarded.
    Messages sit under row-level security (RLS) in `interview_turns`, like profile
    documents, and their replies go into the sealed input. The live smoke drives the product
    path, so there is no second call path. ✅
  - *MODEL-02.* The layers are model choice, `_provider_model`, the activity's
    `_model_refusal` (`backend/src/nessa/identity/activity.py:177`) and the database CHECK.
    `test_a_non_synthetic_workspace_s_turns_use_the_standard_model_only` covers the API, the
    CHECK and the activity for the new run kind. Demo workspaces cannot reach a provider: the
    fixture model is a `FunctionModel`, needs no key and reserves nothing, and the stack test
    runs it in the demo stack, which has no egress route. ✅ The fixture CHECKs themselves
    are untested (Minor #4).
  - *Fixture adapter contract.* It goes through the same agent, `check_turn`, truncation
    check and failure classification. It is labelled with origin `fixture`, the fixture
    model ID and a reply prefix. ✅ It is not a happy-path stub, although it cannot simulate
    provider failures (by design).
  - *Ledger row 13.* 1,128 × 100 + 693 × 200 = 251,400 nano-USD, which is $0.000251. The
    recomputed running total over every row is 19,958,414 nano-USD, which is $0.019958. The
    `live-smoke` scope has used 2 of its 9 requests. `authorise` counts requests, and
    `ledger.exclusive()` holds the lock from the cap check to the last row. ✅
  - *Declared behaviour changes.* An unknown city is `VALIDATION_FAILED` (422) with
    `{field, reason: unknown_city}`, not a 500. The export is `format_version: 2`; there is
    no importer and ADR 0006 decision 15 documents the change. Every launcher uses the
    worker entry `nessa.worker` (`compose.yaml:104,120`, the stack test, test support), and
    no doc mentions the old module. The hard-constraint set does not contradict spec §4
    ("target or budget"; cities and hours are conservative additions). ✅
  - *CLAUDE.md.* The retry-owner sentence is byte-identical to 10afdbf once whitespace is
    normalised, and still true: it speaks of transient classes, and the repair is a separate
    validation class owned by the agent (ADR 0006 decision 9). The other new sentences
    (INTERVIEW=1, RunTask, the layout, identity never importing profile or catalogue, demo
    fixture only) match the code. ✅
- ⚠️ Cannot verify from diff (half A or out of scope): the ESCO release pin, fetch, hash,
  import, manifest and attribution (`nessa/catalogue/esco.py`, `taxonomy.py`, `tools/datasets.py`,
  `tools/setup.py`, the `compose.yaml` datasets mount, `docs/dependencies.md`); FTS and alias
  retrieval with its `TAXONOMY_UNAVAILABLE` and `no_search_terms` refusals; the city list's
  contents, aliases and ONS regions (`nessa/catalogue/places.py`); the provisional-concept
  trigger and `taxonomy_store`; `fixtures/esco-sample`; the regenerated TS client
  (excluded). Human gates (the city-region review and the hard-constraint set) are correctly
  recorded as "not run — requires human". The production model has not run the interview
  schema live; this is acknowledged, not claimed.

### Strengths
- One write path, `commit_profile_version`, behind both `PUT /profile` and decisions. Each
  accepted change gets its own conversation source (turn, cited messages, basis, confirmer),
  enforced by `conversation_sources_are_complete`.
- Hard constraints are confirmed field by field. `CONFIRMATION_REQUIRED` names the
  unconfirmed fields, stray confirmations are refused, and the integration test proves
  nothing is saved until every accepted limit is confirmed.
- The truncation check is conservative: an output whose last response stopped at `length`
  is never accepted, even if it parses.
- The leak scans are strong. The refusal and truncation fakes carry the output sentinel, and
  the scan checks it never reaches the app database, DBOS or the logs.
- The DB CHECKs pin the semantics (`interview_turns_pin_the_profile_version`, fixture-only
  demo runs). Reseal covers `run_inputs`, and `_tables_on_old_versions` catches any sealed
  table that is missed.
- The live-smoke extension counts requests in the caps, ledgers `requests_sent`, allows one
  attempt in the smoke workspace and is tested offline.

### Issues

#### Critical
None.

#### Important
1. **A repair request that fails without usage is booked as known cost.**
   `backend/src/nessa/identity/activity.py:320` counts requests, `:341` derives the cost
   from the responses only, and `:337` marks it `RECONCILED` whenever any response reported
   usage. My probe sent an invalid first output, then a 503 on the repair. The attempt
   records `requests_sent=2`, one response and a "reconciled" cost of 9,650,000 nano-USD for
   the first request only. The rest of the 49,000,000 reservation is released, and the DBOS
   step retries. This breaks MODEL-08 ("ambiguous charges recorded as unknown") and ADR 0004
   decision 10 ("a failed or interrupted call without reported usage stays unknown and keeps
   its full reservation"): a request that may have been billed now counts as zero. The
   interview's two-request attempts are what create this case.
   **Fix:** if the attempt sent more requests than it got responses with usage, set
   `spend_state=UNKNOWN` and keep the full reservation, or reconcile known plus the
   per-request bound. Add a domain test (fake: invalid once, then 503) and one integration
   assertion on `spend_state`.
2. **On the production path, a provider outage ends `budget_exceeded`, not
   `provider_unavailable`.** One Standard attempt reserves $0.049
   (`backend/src/nessa/profile/interview.py:378`). The default run limit is $0.10
   (`backend/src/nessa/config.py:118-120`). The DBOS step allows 3 attempts
   (`backend/src/nessa/identity/workflow.py:27`). Two transient failures with no usage stay
   `unknown` and hold 98M, so `_prepare` refuses the third with `BUDGET_EXCEEDED`
   (`backend/src/nessa/identity/activity.py:255`). Every non-synthetic workspace with
   default limits therefore reports "over budget" during a Meta outage, contrary to spec
   §16 ("explain the exact limitation") and the distinct provider-unavailable state (spec
   §3, GC6). ADR 0006 decision 9 records this arithmetic (`docs/adr/0006-taxonomy-and-interview-contract.md:121`) but not
   the misreported cause. The only outage test uses the test model, where three attempts
   fit (`backend/tests/integration/test_interview_turns.py:233`).
   **Fix:** either make the kind's attempt budget fit the default run limit (size the
   default, or cap the step's attempts per kind), or, when a reservation is refused after
   transient failures, end the run with the last transient class (`provider_unavailable`).
   Test it on the Standard model.
3. **Spec miss: streaming deferred with no owner.**
   `docs/adr/0006-taxonomy-and-interview-contract.md:161-167` and
   `docs/requirements-register.md:532` leave "Stream natural conversation" (spec §4, M0) and
   the streaming contract test (spec §16, MODEL-03) open. The owner is still T5 and no
   later task picks them up. Decision 13 effectively decides a product-visible behaviour but
   is not marked "provisional — needs product owner confirmation" (R6).
   **Fix:** reassign the streaming part of MODEL-03 to the task that builds the You-chapter
   conversation (T6), adding it to that task's scope. Or record an R6 provisional decision
   that L0 does not stream and mark it for product owner confirmation.

#### Minor
1. **A truncated output spends the repair request and is parsed.** My probe confirms 2
   requests for a truncated output. Pydantic AI attempts to parse the cut-off text and sends
   a repair before the activity classifies `output_truncated`. This contradicts "never
   parsed" in `backend/src/nessa/identity/activity.py:24` and
   `docs/adr/0006-taxonomy-and-interview-contract.md:123`. **Fix:** fail fast on
   `finish_reason == "length"` (an `after_model_request` hook or output-validator check
   that raises a non-retry error), or correct the documentation and accept the cost.
2. **`backend/src/nessa/identity/meta.py:3-5` is now stale.** It says "the agent has no
   output retries and one request at most". That is no longer true for interview turns.
3. **`docs/runbook.md:18` omits run inputs.** It still describes `make reseal` as
   resealing "(stored keys and run outputs)". The CLI docstring was updated; this line was
   not.
4. **The fixture-model DB CHECKs and the activity's fixture refusal branch have no test.**
   These are `demo_workspaces_use_only_the_fixture_model` and
   `the_fixture_model_only_interviews`
   (`backend/src/nessa/migrations/versions/r0005_interview_turns.py:37,39`), and
   `_model_refusal`'s fixture branch (`backend/src/nessa/identity/activity.py:177`). The
   Contributor CHECK has one (`backend/tests/integration/test_worker_boundaries.py:114`). **Fix:** add CheckViolation
   tests for a provider-model run in a demo workspace and for a fixture run of another kind.
5. **A test comment claims more than the test proves.**
   `backend/tests/integration/test_interview_turns.py:431` says "the worker sees only its
   own run's sealed input". The `worker_authorised` policy is scoped to the workspace,
   matching `run_outputs` and credentials, and the test has a single run. **Fix:** reword
   the comment, or add a second run and assert the policy's real scope.
6. **List proposals replace the whole list, but nothing says so.** The instructions
   (`backend/src/nessa/profile/interview.py:317-340`) and `ProposedChangeOut.value`
   (`backend/src/nessa/api/interview_schemas.py:26`) never state it. The fixture merges
   existing items; a live model may propose only the new city, and accepting that drops
   confirmed ones. **Fix:** say "items is the complete list after the change" in the
   instructions and the field description. The T6 review tray should show a diff.
7. **The person never confirms `basis`.** The model asserts stated or inferred, and it is
   stored as provenance (`backend/src/nessa/profile/conversation.py:290,295`) without
   confirmation. Consider recording it as the model's claim, or letting the decision
   override it.
8. **Fixture attempts report "unknown" cost.** They record `cost_nano_usd = null`, which
   the API documents as "null: unknown, never zero" (`backend/src/nessa/api/schemas.py:259`),
   although a fixture's cost is known to be zero (`spend_state` is `none`). **Fix:** record
   0 with `spend_state=none`, or document that the pair means "no provider call".
9. **The web hand-codes list bounds the API does not publish.** `apps/web/src/lib/vocabulary.ts:89,97,123,131,139`
   sets 3/3/8/8/8, and `ProfileInput` has no `maxItems`, so they can drift. Consider
   exposing `maxItems` on the API input schema (not the Meta schema), so the bounds are
   generated.
10. **The test worker duplicates the production builder's fixture dispatch.**
    `backend/tests/support/worker_entry.py:50` duplicates `nessa.worker.model_builder`
    (`backend/src/nessa/worker.py:40`). Only the stack test exercises the real builder.
11. **The fixture `_MONEY` pattern accepts amounts the check refuses.**
    `backend/src/nessa/profile/fixture_interviewer.py:45` accepts any number of comma
    groups. £1,000,000,000 yields an update `check_turn` refuses, so a demo turn
    deterministically ends `invalid_model_output`. **Fix:** cap the digits at the
    `MONEY_PATTERN` bound.
12. **A complete but schema-invalid JSON output is not tested through the agent.**
    "Invalid schema" through the agent is covered only by truncated JSON and by
    `check_turn`-level problems. Add one fake that returns a wrong type or a missing key
    and expects one repair, then `invalid_model_output`.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The contract, the single write path, hard-constraint confirmation,
version pinning and the durable-pattern reuse are sound and well tested. But multi-request
attempts can book a possibly billed request as zero (#1), and real users see
`budget_exceeded` during a provider outage (#2). The streaming requirement also needs an
owner, or an R6 decision, before the register can be trusted (#3).
