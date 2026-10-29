# ADR 0009: Evidence acquisition, the restricted acquisition worker and run cancellation

- Status: Accepted for Task 7A (Sprint 3, S3.1–S3.4 acquisition core). Decision 2 and the
  agency word list in decision 6 are **provisional, need product owner confirmation (R6)**.
- Date: 2026-10-29
- Requirements: ACQ-01..10, JOB-01/02/05/06/08, FRESH-01..04, STATE-02, API-06, DUR-05,
  MODEL-08, SEC-05, SEC-08, PROP-02; spec sections 6, 7, 11 and 18; Global Constraint 8;
  rulings R3, R4, R5; the session 1 rights policy (H-06)

## Context

Sprint 3 turns research into inspectable records: pages people or a search propose, Adzuna
results in live-vacancy mode, and text people paste. The specification fixes the stack
(Scrapling for retrieval and parsing, DBOS for durable runs), the security boundary
(acquisition workers have no profile, model key or master key; every URL is checked before
and after redirects and DNS) and the evidence contract (SourceAttempt, SourceClaim, spans,
dates, freshness). Session 1 set the rights policy for what may be kept.

## Decisions

1. **A restricted acquisition worker, without a database.** `python -m nessa.acquisition`
   is a small standard-library HTTP service on the internal Compose network. It fetches one
   page, or runs one Adzuna search, per request and returns the result; it records nothing.
   Its configuration has no database, master-key or model setting; Compose gives it no
   secret and one read-only mount, the Adzuna credentials (decision 11). The DBOS worker,
   which holds the database role and the master key, calls it and records the result. In
   live mode (`compose.live.yaml`) the acquisition worker and the DBOS worker alone have a
   route out; in demo mode neither does. Proven three ways: the import closure of
   `nessa.acquisition` reaches no store, keyring, Meta, profile or API module
   (`test_the_acquisition_worker_cannot_reach_a_database_key_model_or_profile`), its
   settings have three fields, and on the running container its only mount is the Adzuna
   directory, `/run/secrets` does not exist and no environment name mentions a database,
   master key or Meta (`test_the_acquisition_worker_holds_no_database_secret_master_key_or_model_key`).
   A new database role was rejected: the init script that creates roles runs only on a new
   volume, so existing installations would not get it.

2. **Scrapling parses; Nessa's own client retrieves (provisional).** Scrapling 0.4.15 and
   0.5 import Playwright, Patchright and browserforge when their HTTP fetcher is imported
   (`scrapling/engines/toolbelt/convertor.py`, `fingerprints.py`), and `make check` excludes
   Playwright from the backend (spec section 6: no browser rendering). So Scrapling 0.4.15's
   parser (`scrapling.parser.Selector`, BSD-3-Clause; lxml, cssselect, orjson, tld, w3lib) is
   the only scraper code used, adaptive relocation off, and retrieval is
   `nessa.evidence.fetcher` on the HTTP core already in the lock (`httpcore2`). That client
   also does what Scrapling's curl-based fetcher does not expose: it connects to the very
   address it checked. Spec section 6 says M0 "calls its HTTP fetch/parse capability"; this
   keeps Scrapling as the one scraper and parser and replaces only the transport. Needs the
   product owner's confirmation.

3. **Every hop is checked; refusals are attempts.** `addresses.check_url`: http or https,
   no credentials, port 80 or 443, a public IP literal or a multi-label name; local names
   and every encoded address form (one decimal or hex number, octal, short dotted forms,
   percent-encoding, Unicode digits, IPv4-compatible IPv6) are refused, never decoded.
   `address_refusal` refuses every non-global, multicast or reserved address and every IPv6
   form embedding IPv4 (mapped, 6to4, Teredo, NAT64). The fetcher resolves at connect time,
   refuses a host if any answer fails, and connects to an answer that passed, so DNS
   rebinding cannot change the address; each redirect (at most 5) is a new hop with the
   same checks, and https never redirects to http. Bounds: 2 MB (also after gzip or deflate,
   so a decompression bomb is cut), 20 s in all (5 s connect, 10 s read), HTML only for
   pages, JSON for Adzuna. robots.txt is read first for each origin and obeyed for the token
   `NessaL0` by Nessa's own RFC 9309 matcher (`fetcher.parse_robots`; `urllib.robotparser`
   was replaced in fix round 1 because it ignores `*` and `$` and takes the first matching
   rule): the groups naming the token without regard to case, else the `*` groups,
   combined; the matching rule with the most octets decides, an allow rule winning a tie;
   paths and rules are compared after percent-encoding normalisation, by an iterative
   matcher whose cost is bounded by the two lengths. A 4xx robots.txt allows (cached 10
   minutes); an unreachable one disallows as a transient failure, with no page request, and
   is not remembered, so the step's next try reads it again. Each host is paced to its
   manifest rate limit. Tested against a controlled loopback server
   whose one origin is the fetcher's only extra allowance (`test_fetcher.py`, 36 cases).

4. **The source permission manifest and the rights policy as code (OI-11).**
   `backend/src/nessa/evidence/sources.json` lists hosts with their session 1 class, access
   (permitted, API only, denied with the reason), rate limit, retained fields, attribution
   and the terms relied on with the date read (GOV.UK and the National Careers Service:
   the OGL footer; Adzuna: its API terms; LinkedIn and Indeed denied). A page's class comes
   from its final host's manifest entry and nothing else: an employer's careers site or an
   ATS host is an employer posting (line A5) only when the manifest lists it so. What a page
   says about itself never changes its class: its JSON-LD `hiringOrganization` can give a
   cited `employer` claim and the advertiser kind, but any page can name any organisation
   (a board naming itself, a public suffix such as `co.uk` or `github.io`), so it is never
   evidence of whose site the page is on (fix round 1, review A C1). An unlisted page is class
   `other`, "pending human rights review", unless an agent records a dated classification
   with the terms relied on (`tools/corpus.py --rights-class --terms`, dated with the run's
   date). That classification replaces the derived class in either direction before
   anything is kept, but never keeps more of a listed host's page than its entry permits.
   The product's runtime never takes one: there, unlisted is `other`. A person
   supplying a URL never overrides an entry. The body is kept, sealed to the workspace in
   `source_documents`, only for the classes that may keep it privately (lines A1–A5); job
   boards and `other` keep the hash and the claims' minimal excerpts (at most 200
   characters each). A test holds the code's classes to the corpus manifest's.

5. **Records (spec section 18).** `source_attempts`: every try by any route, blocked and
   failed ones included, written before the request and settled after, a retry naming the
   attempt it repeats, with the provider, requested and final URL, redirects, status and
   reason, HTTP status, content type, connected address, SHA-256, rights class and status,
   retention, request count and charge ($0 for fetches and Adzuna's free tier). Claims hold
   field, typed value, validation state (structured, user-supplied or quarantined with its
   issue), a span (offsets into the decoded text that was hashed, or a JSON pointer for an
   API response, with an excerpt), retrieval, publication and expiry dates. Structured fields
   come first: JSON-LD `JobPosting` (also in `@graph` and type lists); a salary that is not
   whole pence, another currency or a malformed date is quarantined, never guessed; postings
   on one page that disagree on salary, expiry, contract or employer are all marked
   `conflicting_job_postings` and belong to no job (ACQ-08). Page text is data only.

6. **Canonical jobs (JOB-01, JOB-02).** Copies are one job when they share a provider's
   source ID, or when nothing material differs (title with its level words, a contract
   dimension both state, disjoint cities, employers) and they share an application URL or,
   for one named employer, the description (whole, or the 16-word opening a board snippet
   keeps). Every copy is kept; a multi-city job is one job under each city. An advertiser
   whose name holds a staffing word (`jobs.AGENCY_MARKERS`, provisional) is an agency, and
   its copy names no employer: the hiring employer stays undisclosed.

7. **Freshness on access (FRESH-02..04).** Maximum ages from the last success: jobs 24 h
   (then "awaiting recheck"), fees and intakes 7 d, funding availability 48 h, funding rules
   30 d with a warning after 7, syllabus 90 d. A failed refresh moves `last_attempt_at` only;
   an expiry date overrides the age and a closure (HTTP 410) both. A URL another run is
   fetching is joined; one that failed recently waits out a back-off of a minute, doubling,
   at most an hour.

8. **The acquisition workflow.** `nessa.acquisition_run` (DBOS): one step per target, then
   publication. The journal holds the run ID, positions and `{status, attempt_id}`
   outcomes; never a URL, page or credential. The target step owns the bounded retries
   (spec section 6): a transient source failure, the acquisition worker unreachable or the
   database busy is retried, three tries at most, each its own attempt row. Completed steps
   are not repeated after a crash, so a resumed run carries on at its next target
   (`test_a_worker_killed_after_a_target_resumes_at_the_next_one`). A complete run's output
   is a sealed summary; a run with no source retrieved ends `failed/retrieval_failed`, or
   `source_blocked` when every source was refused, never an empty success (STATE-02). The
   job list says why it is empty (`no_sources_checked`, `no_source_retrieved`,
   `none_found_in_sources_checked`).

9. **Cancellation (DUR-05).** `POST .../runs/{id}/cancel` records a request
   (`run_cancellations`, identifiers only, read unscoped by the worker like the outbox). The
   worker loop then calls `DBOS.cancel_workflow`, so no further step starts, and publishes
   the run `cancelled`, distinct from a failure. A run cancelled before dispatch is never
   started and reserves nothing; the model activity also refuses a cancelled run before any
   reservation; a request already sent completes, is booked at its cost and its result is
   not used. A finished run answers `RUN_FINISHED`. The model workflow's step sequence is
   unchanged and the acquisition workflow is new, so the DBOS `application_version` stays
   `nessa-l0-1`.

10. **Pasted text is its own route (ACQ-10, JOB-06).** Recorded at once by the API (no run,
    no fetch) as a finished attempt of route `pasted_text`, its body sealed, its claims
    `user_supplied`, its job an `exemplar`: the person's example of a target, at most three
    per target, never a live vacancy (freshness `never_verified`).

11. **Adzuna (R4; controller ruling).** The adapter (`nessa.evidence.adzuna`) records the
    request without `app_id` and `app_key` and builds the credentialed URL only for the one
    HTTP call; `redact` strips them from any URL. Pay keeps its basis (`salary_is_predicted`
    "1" predicted, "0" advertised, absent unknown) and no period, which Adzuna does not
    document; descriptions are snippets. Its terms (read 2026-10-28) allow personal job
    search and require each displayed advert to be labelled "Adzuna" with a link; they do not
    clearly allow keeping more, so it is class `job-board`: hash and excerpts only. `make
    setup` copies the credentials from `.env` into `NESSA_HOME/adzuna/` without printing them;
    the acquisition worker is the only container that mounts them (the one credential it may
    hold, GC8); the API knows only whether they are there, to allow live-vacancy workspaces.

12. **Bounded Meta search discovery.** `source_search` is a run kind on the one bounded
    activity (ADR 0006 decision 10), pinned to the profile version it read, for one confirmed
    target in one of the person's cities: the prompt carries those two words and nothing
    else (SEC-05). One request, Meta's own search (`NativeTool(WebSearchTool)`, context
    `low`, `max_tool_calls` 2, sources included) and no repair, because a repair would pay
    for every search again: worst case $0.008 on the test model, $0.045 on the production
    model, so three attempts fit the default $0.15 run limit. Deterministic code keeps only
    candidates that pass decision 3's checks and the manifest, marks each grounded when the
    search returned it, and lists the rest as excluded with the reason. Candidates are never
    claims; the person chooses what to acquire.

13. **The validation repair stays within its reservation (MODEL-08).** `RepairBound`, on
    every task's agent, rewrites Pydantic AI's schema feedback as each problem's location and
    message, never its input (the rejected output), and cuts any feedback to the kind's
    repair allowance.

14. **Apply links are https only.** One check (`addresses.apply_link`) for every source of a
    view-or-apply link (pages and Adzuna): an `https` URL with a host after surrounding space
    is removed; `javascript:`, `data:`, hostless or unparsable links are no claim at all.

## Evidence

`make check`; `make acceptance` (`test_acquisition.py`, the cancellation cases in
`test_durable_runs.py`, the stack's container checks); live: `make live-smoke SEARCH=1`
twice on the test model (ledger rows 27–28: one request each, two searches, 21 and 14
sources returned, $0.005562 and $0.005587, leak scans clean, but no candidate proposed);
`make live-adzuna` blocked: no `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` in `.env`.

## Consequences and open items

- Not done in Task 7A: model extraction for pages without structured data (ACQ-03's
  residual part: a page without JSON-LD gives no posting and says so; the person can paste
  it); source-specific selectors (Task 7b assigns template families first, OI-09); the
  Roles chapter and every UI over these endpoints (Task 8); research data in the workspace
  export (T15); ASHE, UK-SOC and the AI evidence (Task 7B).
- The live search proposed no candidate in two tries; candidate quality is unqualified.
- The Adzuna live integration is unverified until credentials are in `.env` under those two
  names.
- A new error code (`RUN_FINISHED`), failure classes (`retrieval_failed`,
  `source_blocked`), event kinds (`run.cancel_requested`, `research.updated`) and run kinds
  (`acquisition`, `source_search`); migration 0013.
