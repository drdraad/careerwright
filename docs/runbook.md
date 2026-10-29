# Nessa L0 runbook

Everything runs on this machine (ADR 0001). Run commands from the repository root.

## Commands

| Command | What it does |
|---|---|
| `make setup` | Checks Docker (Compose v2), uv, pnpm 10.33.2 and Node 24; installs the locked backend, web-app and design-tooling dependencies and Playwright's Chromium; creates `NESSA_HOME` (default `~/.nessa/l0`) with generated database passwords and master key `v1`, all owner-only; downloads the pinned ESCO release (10 MB) into `var/datasets/` and keeps it only if its size and SHA-256 match; builds the images (backend, Auth emulator, web). Network is needed here only. Safe to re-run: it never replaces an existing password or key, and re-verifies a dataset already present instead of fetching it again. |
| `make dev` | Starts the stack in **live** mode and waits until healthy: migrates, seeds, imports the ESCO release on the first start (about 6 s; later starts find it imported), starts the web app, prints the URLs. Only the worker (for Meta) and the restricted acquisition worker (for permitted pages and Adzuna) can reach the internet. Live-vacancy workspaces are offered only if setup placed Adzuna credentials. |
| `make demo` | Same, in **demo** mode: no Nessa service has a route out of the machine. Calls to Meta are refused; a demo workspace's interview turns are answered by the offline fixture interviewer, labelled as such. |
| `make stop` | Stops every service within a bound (SIGTERM, then SIGKILL after the grace period). Volumes and `NESSA_HOME` are kept; DBOS recovers in-flight runs on the next start. |
| `make reset-demo` | Recreates the fixture workspace "P01 demo (synthetic)" only. Event numbers continue, so a resumed stream sees the reset. |
| `make check` | Backend: formatting, lint, types, fast tests and the fixture validator. Web (`apps/web`, `pnpm run check`): generated-client drift, Biome, `tsc`, Vitest. No Docker, no network. |
| `make acceptance` | Integration and stack tests against real PostgreSQL 16, DBOS and the emulator, in separate Compose projects (`nessa-l0-test`, `nessa-l0-stacktest`) and ports; then the Storybook build and the Playwright suite on its own demo stack (`nessa-l0-webtest`, web on `127.0.0.1:57600`): the browser journey with a full restart, keyboard, access and visual checks. Removes them afterwards. |
| `make live-smoke` | One real connection-check run on the test model through an isolated stack (`nessa-l0-smoke`), at most 3 calls, within the `live-smoke` scope's cumulative cap (9 calls, 3 production, $0.30 worst case by default; `NESSA_LIVE_SMOKE_*` changes it). `INTERVIEW=1` runs one interview turn instead, with a fixed synthetic message, checks that its reply streamed and was superseded by the validated output, and confirms its proposals into the profile: one attempt, at most 2 calls (the call and one validation repair). One invocation at a time: a second refuses while the ledger is held. The worker is stopped before the attempts are read, and every attempt is ledgered in `docs/evidence/live-usage.*` with its request count; if the worker cannot be confirmed stopped, every further call it could make is ledgered with an unknown cost and the command fails. Only `PRODUCTION=1` uses the production model. Reads `META_API_KEY` from `.env`. |
| `make live-eval` | The representative evaluation cases (those marked `live` in `backend/tools/evaluation_cases.json`: INT-01..03 and DSC-01; at most 6 per invocation; `CASES=INT-01,DSC-01` runs a chosen subset) through the isolated live stack on the test model only: one synthetic workspace per case whose run limit allows exactly one attempt (at most 2 requests), within the budget scope's cumulative cap (the controller's 9 requests, no production request, $0.05 worst case; `NESSA_LIVE_EVAL_*` changes it). A scope holds one default run; a further authorised run gets its own scope (`NESSA_LIVE_EVAL_SCOPE=...`). The slate-explanation case EXP-01 is not in the default run: `CASES=EXP-01` runs a discovery and then its slate's explanation in one workspace, each run limited to one attempt (at most 4 requests), checking each quotation against ESCO's record as the taxonomy serves it. Every attempt is ledgered in `docs/evidence/live-usage.*` after the worker stops; results with failures by type are appended to `docs/evidence/live-eval.md`, and each case's output to the private evidence directory (`NESSA_HOME/evidence/live-eval.jsonl`, owner-only, never committed); the key is leak-scanned. Reads `META_API_KEY` from `.env`. Never part of `make check` or `make acceptance`. |
| `make live-smoke SEARCH=1` | One source search (Meta web search) on the test model through the isolated stack, for the synthetic target "Data analyst" in Manchester: one attempt of one request (at most 2 searches; worst case $0.008), in its own scope `live-search` (at most 9 requests and $0.30). Prints the candidates, how many the search really returned, what was excluded and the searches run; ledgered like any smoke, its notes recording the exclusions with their reasons, the hosts its pages came from (hosts only) and why it proposed nothing, if it did not. |
| `make live-smoke SEARCH_BOUND=1` | One source search in this process (no stack), through the product's task code, asked for at most one tool call (`max_tool_calls` 1), to qualify that Meta keeps to the bound: one request (worst case $0.0043 on the test model) in the scope `live-search`, ledgered with the searches Meta reported; an overrun fails `bound_exceeded:web_searches`. |
| `make live-extract` | One page extraction in this process (no stack), through the product's task code and check, of the synthetic fixture page `fixtures/acquisition/extraction-page.html` only (never a real page, OI-09): its visible text to the test model, one attempt of at most 2 requests (the call and one schema repair; worst case $0.0034), in its own scope `live-extract` (at most 3 requests and $0.30). Each request is its own ledger row with its tokens and cost; the last row's notes record the postings, the claims by validation, what was dropped and why, and whether the page's own instruction to report another salary was followed. The result, the rows and the requests sent are then scanned for the key; any finding fails the command. Never part of `make check` or `make acceptance`. |
| `make live-adzuna` | Two real Adzuna search requests (free tier) through the acquisition adapter's own code, in the `live-adzuna` scope (at most 10 requests). Reads `ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY` from `.env` in code, never printed; if either is absent or empty it says "blocked: Adzuna credentials not found", names which is missing and lists the names (never the values) of the variables in `.env` whose name holds "ADZUNA", and sends nothing. Each request is ledgered in `docs/evidence/live-usage.*` at $0 with its endpoint recorded without the credentials; the summary is counts only. Never part of `make check` or `make acceptance`. |
| `make rotate-master-key` | With the stack running: adds master key `v<N+1>` to `NESSA_HOME/keys`, then runs `make reseal`. The only way to rotate the master key. |
| `make reseal` | Restarts a running API and worker so they load every key version (their mode is kept), then reseals every sealed record (stored keys, run inputs, run outputs, partial replies and kept source bodies) under the newest key, and fails if any record is left on an older version. Run it again if a rotation was interrupted. Restarting the worker recovers an in-flight run, whose model call may then be made again, within its spend reservation. |
| `make status` | `docker compose ps` for the stack. |

## Addresses (127.0.0.1 only)

| Service | URL |
|---|---|
| API | `http://127.0.0.1:58000` (`/openapi.json`, `/healthz`, `/readyz`) |
| Firebase Auth emulator | `http://127.0.0.1:59099` (project `demo-nessa`) |
| PostgreSQL | `127.0.0.1:56432` (`nessa_app`, `nessa_dbos`; passwords in `NESSA_HOME/secrets`) |
| **Nessa (web app)** | `http://127.0.0.1:53000` (open this). It answers only to `127.0.0.1:53000` and `localhost:53000` as Host, and forwards `/api/v1/*` to the API |

Seeded identities (emulator, password `nessa-demo-<name>`): `ada@nessa.test` (invited;
owns the fixture workspace), `ben@nessa.test` (invited), `uninvited@nessa.test` (can sign
in, is refused). These are local test credentials, not secrets.

## Using the web app

1. `make demo` (or `make dev`), then open `http://127.0.0.1:53000`.
2. Sign in: the page offers the three seeded identities. Ada owns "P01 demo (synthetic)".
3. **You** starts with "I know my direction" or "Help me explore", then the conversation:
   one question at a time, a tone you choose, Pause and Resume. In a demo workspace the
   replies come from the deterministic demo interviewer, labelled as such; a live workspace
   first asks for your Meta key, with consent to encrypted storage. A reply streams, marked
   "not checked yet", until the checked reply replaces it. Its proposed changes wait in
   **What we know** to accept, confirm (limits and targets, by name), edit or skip; nothing
   is saved until you save, and the last save can be undone. "Edit answers directly" opens
   the form: each answer is Answered, Unknown, Skipped, Prefer not to say or Not asked yet,
   never a blank standing in for zero; **Source** shows where it came from. **Directions to
   explore** suggests up to six ESCO occupations from your answers (no score or
   percentage), with view-only controls; "Make this a target" is the only way one becomes
   a target. The early sketch lists what a target usually asks for, every step unresolved.
   A message that uses listed words about dying, suicide or self-harm is sent as usual,
   with a calm note of UK support services beside it (also if the send is refused), and
   Nessa's reply that turn offers a smaller step and asks no career question. The note is
   shown for such words whatever they are about, and is never stored.
4. **Routes** in the fixture workspace shows the TRACE-01 fixture preview, labelled as such.
   Select a route to inspect it. The route search itself is not built yet, so the other
   chapters show what they will hold and which answers they need.
5. The strip shows the saved version and the live-update state. After `make stop` and
   `make demo` the open page reconnects by itself, and a reload reopens the same work.
6. Calm mode (account menu) turns off motion; `prefers-reduced-motion` does the same.

For UI work without Docker: `cd apps/web && pnpm storybook` (component states on
`127.0.0.1:6006`). After an API change, run `pnpm run generate` in `apps/web` and commit the
regenerated client.

`cd apps/web && pnpm run review-screenshots` regenerates the visual review package in
`docs/reviews/sprint-2/screenshots/` (Sprint 1's package stays as it was reviewed). It needs Docker: like `make acceptance`, it builds and
starts its own stack (`nessa-l0-webtest`) and removes it afterwards.

## Calling the API (what the web app does)

The web app calls these through its own origin (`/api/v1/...`). Its server forwards them
with the browser's Origin unchanged.

- `Authorization: Bearer <emulator ID token>` on every `/v1` request.
- State-changing requests need `Origin: http://127.0.0.1:53000` (or `localhost`) and an
  `Idempotency-Key: <uuid>`; reuse the key only to retry the same request.
- Writes carry `expected_version`; a `409 STALE_INPUT_VERSION` means reload and reapply.
- Errors are `{"error": {code, message, retryable, stage, correlation_id, details}}`.
- `POST /v1/workspaces/{id}/runs` returns `202` and a `Location`; `GET` that location for the
  authoritative state. `GET /v1/workspaces/{id}/events/stream` is a server-sent-event stream
  (`id` = event sequence); reconnect with `Last-Event-ID`. It ends with an `event:
  reauthenticate` when the token expires. `GET .../events?after=N` is the same as a page.
- Interview (ADR 0006): `POST /v1/workspaces/{id}/interview/turns` with
  `{expected_profile_version, message}` returns `202` and the turn; `GET .../interview/turns/
  {turn_id}` shows its run and, once complete, its validated proposals (`proposal.changes`,
  each with a `change_id`, the messages it cites and `hard_constraint`). Nothing is saved
  until `POST .../interview/turns/{turn_id}/decision` with `{expected_version, accept:
  [change IDs], confirm_hard_constraints: [fields], edits: [{field, answer}]}`: every
  accepted limit or target must be named in `confirm_hard_constraints`; an edit is the
  person's own answer for a proposed field not also accepted, saved as a direct entry in the
  same version; and the profile must still be the version the message was sent with (`409
  STALE_INPUT_VERSION` otherwise: send the message again). `POST .../profile/revert` with
  `{expected_version, to_version}` restores an earlier version's answers with their own
  sources (undo).
- Interview preferences (ADR 0007): `GET`/`PUT .../interview/preferences` with
  `{expected_version, entry_mode: sure|unsure|null, conversation_mode:
  practical|gentle|challenge|null, paused}`. `POST .../interview/turns` answers `202` with
  the turn. When the message triggers the support screen (ADR 0007 decision 7),
  `support_note` carries the support panel (`policy_version`, wording, the UK resources and
  when they were checked) to show beside it, that turn's interviewer gets the smaller-step
  instruction, and any next question is dropped; otherwise `support_note` is null. A
  refusal of such a message (any error envelope the command raises: stale version, too
  long, over budget, no key, key reused, ...) carries the same panel as a top-level
  `support_note` beside `error`, worded as not sent. All of it is derived from the message
  every time (a replay with the same idempotency key gets the panel too) and never stored.
  A request still carrying the removed `send_after_support` is refused as invalid (`422
  VALIDATION_FAILED`) before the message is read, so with no panel.
- Discovery (ADR 0007): `POST .../discoveries` with `{expected_profile_version}` returns `202`
  (`INSUFFICIENT_EVIDENCE` if no answer describes work yet); `GET .../discoveries` (newest
  first), `GET .../discoveries/{id}`; `GET .../discoveries/{id}/slate?emphasis=&exclude_concept=
  &exclude_family=` recomputes the slate (view only, nothing stored). `POST .../targets` with
  `{expected_version, concept_id, discovery_id?, replaces?}` makes an ESCO occupation a
  target. `GET .../sketch` is the early requirement sketch.
- The slate's written "Why this could suit you" (ADR 0007 decision 12): `POST
  .../discoveries/{id}/explanation` with `{expected_profile_version}` returns `202` and the
  run (`ExplanationRunOut`), or `200` and the same run if it was asked for before, from any
  view (one call per discovery). `can_retry` is true when the run failed before any
  request reached a model; only then does `{..., "retry_failed": true}` (the person's Try
  again) start a new run that replaces it (`202`); for a run that sent a request it is
  refused with `SLATE_ALREADY_EXPLAINED` (Suggest again makes a new slate). Refused before
  any run with `STALE_INPUT_VERSION` when the answers changed after the discovery,
  `PROPOSAL_NOT_AVAILABLE` for a discovery without validated searches,
  `INSUFFICIENT_EVIDENCE` when no answer has a word to quote or the slate is empty, and
  `LIMIT_EXCEEDED` (`answers_too_long`) when the answers do not fit the prompt in bytes.
  The written text is read with the discovery (`explanation.written`), never in the
  command's answer. The web app asks once when a slate first shows. Demo workspaces use
  the fixture explainer.
- Cancelling a run (DUR-05): `POST .../runs/{run_id}/cancel` answers `202` with the run and
  its `cancel_requested_at`; the worker stops its workflow and the run ends `cancelled`
  (never a failure). A queued run is never started and reserves nothing; a model call
  already sent completes and is booked at its cost, and its result is not used. A finished
  run answers `409 RUN_FINISHED`.
- Research (ADR 0009). `POST .../research/acquisitions` with `{urls: [...]}` (at most 10) or,
  in a live-vacancy workspace, `{adzuna: {what, where, page?, results_per_page?}}` returns
  `202` and the acquisition (its run, targets and attempts). A URL another run is already
  fetching is joined and one that failed recently waits out its back-off (both listed in
  `skipped`; `200` with no acquisition if nothing was started). A URL with a user name,
  password or `app_key` in it is refused (`422`, `credentials_in_url`); any other refusal
  (private address, scheme, port, a denied source, robots.txt) is recorded as a blocked
  attempt. A URL refused for its scheme, host or address is never kept as a URL: its target
  shows the `refusal` and the host as plain text (`refused_host`). `GET
  .../research/acquisitions/{run_id}` shows each target's attempts (status,
  reason, retries, rights class, what was kept), the jobs found so far and, once complete,
  the summary. A run whose every source failed is `failed/retrieval_failed`, or
  `source_blocked` when every source was refused: never "no vacancies".
- Pasted text: `POST .../research/pasted` with `{target, title, text, employer?, city?,
  source_url?}` (a `source_url` that fails the URL checks is a `422`) returns `201` and the
  job: the person's own example of a target (at most 3
  per target; `422 LIMIT_EXCEEDED` after that), never fetched, never a live vacancy
  (`exemplar: true`, freshness `never_verified`).
- Jobs: `GET .../jobs?favourites=&cursor=&limit=` (each job's values, every source copy,
  freshness from its last successful retrieval, `total_jobs` counting a multi-city job once,
  `city_counts`, `coverage` by latest attempt status and, when empty, `empty_reason`);
  `GET .../jobs/{job_id}` adds every claim with its span; `PUT`/`DELETE
  .../jobs/{job_id}/favourite`.
- Source search: `POST .../research/searches` with `{expected_profile_version, target,
  city}` (a confirmed target and one of your cities; `409 CONFIRMATION_REQUIRED` otherwise)
  returns `202`; `GET .../research/searches/{id}` shows the candidate pages (each marked
  grounded when the search returned it) and what was excluded. Candidates are never
  claims: acquire the ones you choose.
- Corpus pages (Task 7b): from `backend/`, `uv run --locked python -m tools.corpus --slot
  <slot> --url <url>` (`corpus/README.md`).
- Taxonomy: `GET /v1/taxonomy` (the ESCO release and its attribution), `GET
  /v1/taxonomy/occupations?q=...&match=all|any`, `GET /v1/taxonomy/occupations/{concept_id}`;
  English cities: `GET /v1/places`. A title ESCO lacks: `POST
  /v1/workspaces/{id}/occupations/provisional` with `{title}`.

## Keys and secrets

- A user's Meta key: `POST /v1/workspaces/{id}/credentials` with
  `consent_to_encrypted_storage: true`; rotate with `.../credentials/{cid}/rotate`, revoke
  with `.../revoke`. The key is never returned. Queued runs use the active key at call time.
- Master-key rotation: `make rotate-master-key` while the stack runs. When it reports
  success, nothing is sealed under the old version any more, so the old `v<N>.key` may be
  removed from `NESSA_HOME/keys`; until then keep every key file. If it was interrupted,
  run `make reseal` (it refuses to report success while any record is on an old version).
- `NESSA_HOME` holds the only copy of the master keys and database passwords; keep it
  private.
- Adzuna (live-vacancy mode, optional, ruling R4): `make setup` copies
  `ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY` from the repository `.env` into
  `NESSA_HOME/adzuna/` (files `adzuna_application_id`, `adzuna_api_key`; owner-only, never
  printed; it reports "blocked: Adzuna credentials not found" when either is absent). Only
  the restricted acquisition worker's container mounts that directory. To change them, edit
  `.env` and run `make setup` again; the next `make dev` uses them.

## Upgrades and backups

- Migrations are forward-only: an upgrade cannot be rolled back by a downgrade migration.
- Backup and restore are not implemented yet (SEC-07 is open). Until they are, an upgrade
  that goes wrong cannot be undone, and losing the Docker volumes or `NESSA_HOME` loses the
  data.

## Troubleshooting

- "run make setup": `NESSA_HOME` is missing or incomplete.
- The `migrate` service fails with `esco-v1.2.1-en-csv is not at /datasets/...`, or the API
  answers `TAXONOMY_UNAVAILABLE`: the ESCO release was not fetched. Run `make setup`. If its
  download fails (the publisher moved the file), the **manual step** (ruling R7): open
  https://esco.ec.europa.eu/en/use-esco/download, choose version "ESCO dataset - v1.2.1",
  content "classification", language "en", file type "csv", download the zip and save it as
  `var/datasets/esco-v1.2.1-classification-en-csv.zip`, then run `make setup` again. Its
  SHA-256 must be `f9761b0b52be1828b38a3e5e0ae59a93a7b0ce358bc800f52f57a8b002adeb3e`;
  any other file is refused.
- Saving the profile is refused with `VALIDATION_FAILED` (`unknown_city`): a work area must
  be one of the 55 English cities (`GET /v1/places`), such as Leeds or Kingston-upon-Hull.
- A service refuses to start with a `ValidationError`: the configuration is unsafe by
  design (non-local host, non-`demo-` project, missing emulator host). Fix the variable.
- Code changes not visible in containers: `make setup` (or `cd backend && uv run --locked
  python -m tools.stack build`) rebuilds the images; the tests rebuild them automatically.
- Port already in use: another local project holds 58000/59099/56432/53000; stop it or set
  `NESSA_API_PORT`, `NESSA_AUTH_PORT`, `NESSA_PG_PORT` or `NESSA_WEB_PORT` for every
  `make` command (the API and the web app then allow that port as their Host and origin).
- Asked to sign in again after `make stop` and `make demo`: the Auth emulator re-imports its
  seed on start, which ends sessions issued before. A page that stayed open refreshes its
  token by itself and reconnects; a page loaded before that asks you to sign in, then returns
  to the same address.
- The page says "This server answers only on its local address": the browser used another
  name for the web app. Open `http://127.0.0.1:53000` or `http://localhost:53000`.
- The strip says "Couldn't refresh: showing what was last loaded" or "Reconnecting": the API
  is restarting or stopped. Nothing is lost; the page catches up when it is back. "Updates
  stopped: sign in again" means the session ended; sign in again.
- The web container refuses to serve and its log says "refuses to serve": a `NESSA_*`
  variable is unsafe (a non-loopback host or emulator, or a non-`demo-` project).
- The client is out of date (`make check` says so): run `pnpm run generate` in `apps/web`.
- Linux hosts are unverified: Compose file secrets are bind mounts, and owner-only files
  may not be readable by the container users there (Docker Desktop maps ownership).
