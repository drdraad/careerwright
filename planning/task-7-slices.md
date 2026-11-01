# Task 7 — two sequential slices (controller ruling)

Task 7's card is one task; it is delivered as two slices, each implemented, reviewed and
ledgered on its own, one after the other. Together they deliver the whole card; neither
narrows it. Each slice commits its own register rows, runbook and ADR text; slice B writes
`docs/reviews/` addenda only if the card asks (the Sprint 3 review is Task 8's).

## Slice 7A — acquisition core (this dispatch, unless told otherwise)

- SourceAttempt / SourceClaim records: permitted retention per the session 1 rights policy
  (`docs/reviews/session-1.md`, `corpus/README.md`; R3 still governs anything outside its
  classes), field spans, hashes, publication / retrieval / effective dates.
- The restricted acquisition worker with keyless Scrapling HTTP fetch/parse: scheme, resolved
  IP, redirects, content type, size and time checks; structured fields first, model
  extraction only where needed. SSRF tests against a controlled server, IPv6 and encoded
  addresses included. Prove the fetcher holds no user secrets, model key, master key or
  private profile access (GC8).
- Bounded Meta search discovery (model-backed: a run kind on the one bounded activity, ADR
  0002/0006; never a second call path).
- Manual pasted text as a separate input route.
- The Adzuna adapter and its fixture contract, and its live qualification (R4). The product
  owner put free-tier Adzuna developer credentials in the repository `.env` (2026-10-28),
  expected as `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`. Controller rulings:
  - Treat them exactly like `META_API_KEY`: loaded in code from `.env`, never read by you
    with a shell command, never printed, logged, journalled, committed or passed as a
    command argument. If either name is absent, the live step reports "blocked: Adzuna
    credentials not found" and the adapter stays fixture-qualified; do not guess names.
  - The live qualification is an explicit, capped command beside `make live-smoke` (never in
    `make check` or `make acceptance`): free tier only, at most 10 requests in its scope,
    each appended to `docs/evidence/live-usage.jsonl` and `.md` with request count and cost
    recorded as free tier ($0), plus the endpoint and result class, never the credentials.
  - Adzuna passes `app_id` and `app_key` as query parameters: no URL carrying them may reach
    a SourceAttempt, a claim, a log, an error, an event, a journal or the usage ledger. Store
    the request without its credentials, and test that.
  - For the running product (`make dev`, live-vacancy mode), the adapter reads the credential
    from `NESSA_HOME` (R4's location), placed there by setup from `.env` without printing
    it; the acquisition worker may hold this one credential and still no model key, master
    key or private profile store (GC8). Record that in an ADR.
  - Adzuna results are aggregator data: session 1 class 6 ("reference only — hash and
    excerpts, never the body — unless their terms clearly allow more"). Read Adzuna's API
    terms, record the date and what they allow (attribution, retention), and apply them.
  - Propose (do not make) the matching `CLAUDE.md` edit to the ".env holds META_API_KEY for
    make live-smoke only" sentence.
- Syndicated-job dedupe, agency vs employer, multi-city counted once.
- Closure and freshness (jobs 24 h, fees/intakes 7 d, funding 48 h; a failed refresh never
  extends validity), favourites, resumable incremental results; a failed fetch is never
  "no vacancies".
- Cancellation (carry-forward-task-7.md, DUR-05): implement it here.
- The spend-reservation check (carry-forward-task-7.md, pydantic-ai schema retry): here,
  for every model-backed kind.
- Attempt cases X01 and X02 and the source permission manifest (OI-11) in
  `corpus/manifest.json`; a pipeline Task 7b can run its pages through.

## Slice 7B — reference data and AI evidence (a later dispatch)

- Pinned ASHE imports (R7) and reviewed UK-SOC mappings with explicit unresolved crosswalks.
- The salary floor (carry-forward-task-7.md, H-11 item 4) applied once pay data exists.
- The reduced S3.6: the AI-resilience assessment record model, publication-state checks,
  lower-bound filter, unscored state, one conspicuously labelled fixture record, and the
  pinned AI-evidence and mapping imports (AIR1-03, AIR1-07, AIR1-11, TAX1-07).
