# ADR 0009: Evidence acquisition, the restricted acquisition worker and run cancellation

- Status: Accepted for Task 7A (Sprint 3, S3.1–S3.4 acquisition core). Decision 2, the
  agency word list in decision 6 and decision 15's word lists and date forms are
  **provisional, need product owner confirmation (R6)**.
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
   is a small standard-library HTTP service on its own internal Compose network,
   `acquisition`, which it shares with the DBOS worker alone: it listens without
   authentication, so no other container (the API, the web app, Auth, the edge, PostgreSQL)
   can reach it, and its route out in live mode is never a relay for them (fix round 1,
   review A I4; `test_only_the_dbos_worker_can_reach_the_acquisition_worker`, and the same
   check in live mode). It fetches one
   page, or runs one Adzuna search, per request and returns the result; it records nothing.
   Its configuration has no database, master-key or model setting; Compose gives it no
   secret and one read-only mount, the Adzuna credentials (decision 11). The DBOS worker,
   which holds the database role and the master key, calls it and records the result. In
   live mode (`compose.live.yaml`) the acquisition worker and the DBOS worker alone have a
   route out; in demo mode neither does. Proven four ways: the import closure of
   `nessa.acquisition` reaches no store, keyring, Meta, profile or API module
   (`test_the_acquisition_worker_cannot_reach_a_database_key_model_or_profile`), its
   settings have three fields, on the running container its only mount is the Adzuna
   directory, `/run/secrets` does not exist and no environment name mentions a database,
   master key or Meta (`test_the_acquisition_worker_holds_no_database_secret_master_key_or_model_key`),
   and by value: none of the stack's database passwords or master keys (as text, raw, hex
   or base64) is in any of its processes' environments or any file it can read, with the
   DBOS worker as the positive control
   (`test_no_database_password_or_master_key_value_is_anywhere_in_the_acquisition_worker`).
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
   percent-encoding, any digit outside ASCII, a full stop IDNA folds to "." (U+3002,
   U+FF0E, U+FF61), any other non-ASCII character whose NFKC form holds an ASCII digit or
   "." (U+2024, U+FE52 and the like), an IPv6 zone ID, IPv4-compatible IPv6) are refused,
   never decoded (fix round 1, review A M1 and M2, addendum M-3, fix round 2 N-2: before,
   Unicode digits and dots were folded by IDNA or nameprep and a zone ID parsed); one
   trailing ASCII dot is removed before the check.
   `address_refusal` refuses every non-global, multicast or reserved address, the
   deprecated site-local `fec0::/10` (which `is_global` passes) and every IPv6
   form embedding IPv4 (mapped, 6to4, Teredo, NAT64). The fetcher resolves at connect time,
   refuses a host if any answer fails, and connects to an answer that passed (at most 4
   tried), so DNS rebinding cannot change the address; each redirect (at most 5) is checked
   before it is recorded or followed and is a new hop with the same checks, and https never
   redirects to http. Only checked http(s) URLs are recorded in a URL field (`url`,
   `requested_url`, `final_url`, `redirects`, a pasted text's `source_url`), enforced by
   CHECKs in migration 0014 (fix round 1, review A I5): a submitted URL refused for its
   scheme, host or address is a target with its `refusal` and its host as plain text
   (`refused_host`), never its URL, and its blocked attempt has no `requested_url`; a
   redirect target is checked before it is recorded; a pasted `source_url` that fails the
   checks is refused with 422. A port other than 80 or 443 is the fetch policy's refusal,
   not the record's: such a URL is still an http(s) URL to a public name, kept on its
   blocked attempt. Migration 0014 removes any other scheme recorded earlier. Every new
   host a page fetch reaches, a redirect's or a robots.txt redirect's included, is admitted
   before any request to it: the manifest's access (a denied or API-only host ends the
   attempt `source_denied` or `source_api_only`, with the redirects so far) and then its
   rate limit; and every hop's URL is checked against its own origin's robots.txt (fix
   round 1, review A I1). Bounds: 2 MB (also after gzip or deflate, so a decompression bomb
   is cut); 20 s for the whole page fetch, its robots.txt requests and later hosts' pacing
   included, enforced in every phase (the name lookup, on a thread it does not wait past;
   each connect; every read, write and TLS start; so a trickled status line or an endless
   run of 1xx responses ends at the bound), with at most 5 s per connect and 10 s per
   read. The first host's pacing comes before the bound starts; a later host is admitted
   with what is left of the bound, and if its next slot is further away the hop fails as a
   transient `timeout` at once, with no wait and no slot taken (addendum, re-review A M-2). HTML only for pages, JSON
   for Adzuna. robots.txt is read first for each origin and obeyed for the token
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
   anything is kept, but never keeps more of a listed host's page than its entry permits,
   and holds only for the host it was given for: a page a redirect took to another host
   gets the manifest's class, its rights status naming both hosts (addendum, re-review A
   M-6).
   The product's runtime never takes one: there, unlisted is `other`. A person
   supplying a URL never overrides an entry. The body is kept, sealed to the workspace in
   `source_documents`, only for the classes that may keep it privately (lines A1–A5); job
   boards and `other` keep the hash and the claims' minimal excerpts (at most 200
   characters each). A test holds the code's classes to the corpus manifest's.
   Session 1's "always true" clause ("a third party's personal details (recruiter names,
   phone numbers) never kept") binds everything kept: bodies, excerpts and claim values
   (controller ruling, fix round 1, review A M6). So before a page, an API response or a
   pasted text is hashed for spans, parsed or sealed, `nessa.evidence.redaction` removes,
   deterministically, email addresses written as plain addresses and telephone numbers in
   UK national (10 or 11 digits from a leading 0) or international (`+`, 8 to 15 digits)
   form, their groups separated by any horizontal space (no-break, narrow and thin spaces
   included, fix round 3), a dot or a hyphen but never a line break, not inside a URL, a
   word or a longer number; and in JSON every name, email,
   telephone and fax number of an `applicationContact` or `contactPoint`. How (addendum,
   re-review A C-1, I-1 to I-3, M-1; fix round 2, re-review A N-1): a page's line endings
   are normalised first; every script whose content is JSON (JSON-LD, an app's state) and
   Adzuna's response are redacted in their decoded values and written again when that, or a
   repeated key (whose earlier, shadowed value then goes), changes them, with every `</`
   escaped, so a detail right after an escape (`\n`, `\t`, `>`) is found and the JSON
   stays valid; IDs and URLs (`identifier`, `url`, `sameAs`, Adzuna's `id` and
   `redirect_url`) are never redacted; a script that is not JSON, and the HTML around the
   scripts, are redacted as text. The body is never kept, whatever its class (only its hash
   and the claims' excerpts), when any script (JSON-LD or not) holding such a detail
   cannot be found in the page's text to be rewritten (`body_not_kept: contact_unlocated`)
   or is not JSON, so its escapes could hide one (`block_unredactable`, looked for with
   JSON's escapes and, since fix round 3 (re-review 3 A R3-1), JavaScript's `\xNN`,
   `\u{...}` and octal escapes decoded, for detection only: no JavaScript is parsed); or,
   since fix round 3 (review C I1), when the redacted page's visible text, normalised
   (entities decoded, every whitespace form one space, characters that do not print such as
   a zero-width space or a soft hyphen dropped), still shows one, because its markup hid it
   from the text patterns (`visible_text_detail`, migration 0022). Since fix round 4
   (re-review 4 A R4-1), normalised text (a page's visible text, an attribute's value, the
   model's input) is redacted and looked at with `redaction.redact_shown`, which also takes
   an email address with whitespace around its "@" or its domain's dots, the TLD letters
   only, since joining the text of `jane<span>@</span>recruit.example` gives `jane @
   recruit.example`; no element is guessed to be inline or block, and such a hit in a kept
   body is `visible_text_detail` too. And since fix round 4 (item 1), every attribute's
   value is decoded (its entities, as the parser decodes them) and normalised, and a detail
   found there, such as an obfuscated `mailto:` link with no visible address, means the
   body is not kept (`attribute_detail`, migration 0025). Migration 0020's
   description said "a JSON-LD block" for the first two; they apply to any script (0022
   records the correction). The reason is its own typed column (migration 0020), the rights
   status the rights statement only (review B N5). Claims and excerpts come from decoded,
   redacted values, also for a block cited by pointer. `content_sha256` is the hash of what was
   kept; `retrieved_sha256` (migration 0015) is the hash of the bytes as retrieved, for
   change detection only. Kept bodies are UTF-8 with LF line endings.
   **Known limits, for the product owner:** a personal name in running text (for example
   "ask for Jane in HR") cannot be told apart from other words deterministically and is
   not removed; nor is a detail written in another form (an email with "at" for "@", a
   number spelt out or split by other characters, an address percent-encoded in a link
   such as `mailto:jane%40recruit.example`). A detail hidden by markup (entities, line
   breaks, invisible characters, inline elements, an attribute's entities) is not removed
   from a kept body, which is then not kept (above). The spaced form errs towards removal:
   an "@" between two words with a full stop after the second (a handle that ends a
   sentence, "Follow @GOVUK. Sign up") reads as an address, so such a body is not kept and
   those words leave the model's input.

5. **Records (spec section 18).** `source_attempts`: every try by any route, blocked and
   failed ones included, written before the request and settled after, a retry naming the
   attempt it repeats, with the provider, requested and final URL, redirects, status and
   reason, HTTP status, content type, connected address, SHA-256, rights class and status,
   retention, request count and charge ($0 for fetches and Adzuna's free tier). Claims hold
   field, typed value, validation state (structured, user-supplied or quarantined with its
   issue), a span (offsets into the decoded text that was hashed, or a JSON pointer for an
   API response, with an excerpt), retrieval, publication and expiry dates. A claim's text
   value, and a copy's title and employer, keep at most 200 characters, the excerpt bound,
   so a reference-only page's records never hold more of it; a location's parts are cut to
   their own bounds (120, 120, 20 and 60 characters) so no page fails on their length; a
   source ID longer than 200 is left unknown rather than cut (fix round 1, review A M4;
   addendum M-7). An apply link is exempt from the cut, because a cut URL is a wrong URL
   (controller ruling, addendum item 10): it is a checked https link kept whole only up to
   the URL bound, 2,048 characters (`addresses.MAX_URL_CHARS`), and past it there is no
   apply claim at all
   (`test_an_apply_link_is_kept_whole_up_to_the_url_bound_and_past_it_is_no_claim`). The database holds claims to that shape (migration 0017, review
   B M3): `field` is a claim field, `span` has a 64-hex `source_sha256`, an excerpt and
   offsets or a pointer, and a claim's attempt is its copy's (`(copy_id, attempt_id)`
   references the copy). Structured fields
   come first: JSON-LD `JobPosting` (also in `@graph` and type lists); a salary that is not
   whole pence, another currency or a malformed date is quarantined, never guessed; postings
   on one page that disagree on salary, expiry, contract or employer are all marked
   `conflicting_job_postings` and belong to no job (ACQ-08). Page text is data only.

6. **Canonical jobs (JOB-01, JOB-02).** Copies are one job when they share a provider's
   source ID, or when nothing material differs (title with its level words, a contract
   dimension both state, disjoint cities, employers) and they share an application URL or,
   for one named employer, the description (whole, or the 16-word opening a board snippet
   keeps). Every copy is kept; a multi-city job is one job under each city. The stored
   path uses the same rule the property tests cover (fix round 1, review B I1): a new copy
   is grouped with its candidates by `jobs.groups_of`, the union-find `group_copies` uses,
   and every stored job in its group is one job, so a copy that bridges two (the employer's
   page joining a Leeds board copy and a Manchester snippet) merges them: their copies,
   with their claims, and favourites move to the oldest job and the others are removed
   (`store.merge_jobs`; migration 0017 lets the worker do it). Recording is serialised per
   workspace (`pg_advisory_xact_lock`, `store.lock_workspace_records`, from reading the
   candidates to the merge; fix round 2, review B N2), so a merge never deletes a job
   another run is recording onto. Restrictive policies (migration 0020, review B N6) keep
   the merge's grants to merging: the worker never deletes an exemplar job, never moves a
   pasted copy, and never moves a copy onto an exemplar. The count no longer depends
   on arrival order (`test_three_copies_of_one_vacancy_are_one_job_in_every_arrival_order`,
   and a property test of the stored rule against the grouping). An advertiser
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
   (`test_a_worker_killed_after_a_target_resumes_at_the_next_one`); a step re-run after a
   crash also skips a target whose last attempt failed for good, such as a 404
   (`test_a_target_that_failed_for_good_is_not_fetched_again_after_a_crash`). A complete
   run's output is a sealed summary, shown only while the run is `complete`; a run with no
   source retrieved ends `failed/retrieval_failed`, or `source_blocked` when every source
   was refused, or `access_revoked` when the requester lost access (its in-flight attempt
   is then settled `access_revoked`, recording nothing it returned, through a narrow worker
   policy in migration 0016), never an empty success (STATE-02).
   Fix round 1 (review B C1, I2, I3, I6, M7): an attempt's `reason` is one of a fixed set
   (`records.AttemptReason`, held by a CHECK; a defect in the acquisition worker is
   `internal_error`, not transient, never a 422 the client would take for the worker
   being unavailable (addendum, re-review A M-7; migration 0018); an HTTP error is
   `http_error` with its
   `http_status`), and a retrieved source with no publishable posting records why
   (`extraction`): `no_structured_data`, `jsonld_invalid`, `conflicting_job_postings` and,
   since fix round 2 (review B N1), `no_job_posting` (a fetched page's structured data held
   no posting, which says nothing about its HTML) all mean it was not read. Only an API's
   own empty answer (`no_matching_adverts`: Adzuna's count of 0; migration 0019) may count
   as none found. The summary and the listing's `coverage` count
   `no_posting_readable` apart; `coverage` leaves out pasted text, which is not a source
   tried. An attempt still `pending` counts as pending only while its run is queued or
   running; one its run left behind (a recording that rolled back, a crash and then a
   cancel) reads as failed, `interrupted`, in coverage, the listing and the acquisition
   view, its target `failed` (fix round 3, review B M1; read side only). The job list says
   why it is empty (`no_sources_checked`, `sources_pending` while
   a source is still being fetched or read (review B N7), `no_source_retrieved`,
   `no_posting_readable`, `no_posting_found_by_model` (decision 15),
   `none_found_in_sources_checked`); its `total_jobs` and
   `city_counts` count vacancies only (`exemplars` apart) and are counted in the database,
   without a cap. An Adzuna search keeps Adzuna's `count` (`total_matching`), so retrieved
   n of total is shown on each attempt, in the listing's `adverts` and as `partial`, never
   as a complete result.

9. **Cancellation (DUR-05).** `POST .../runs/{id}/cancel` records a request
   (`run_cancellations`, identifiers only, read unscoped by the worker like the outbox). The
   worker loop then calls `DBOS.cancel_workflow`, so no further step starts, and publishes
   the run `cancelled`, distinct from a failure. A run cancelled before dispatch is never
   started and reserves nothing; the model activity also refuses a cancelled run before any
   reservation; a request already sent completes, is booked at its cost and its accepted
   result is kept, though a cancelled run's output is never shown as its answer (a
   proposal, a summary); an extraction's postings, recorded with that result, are evidence
   and are shown, and its page reads as what was recorded (decision 15). A finished run
   answers `RUN_FINISHED`, unless runs it started have not
   settled: then those are cancelled (decision 15, fix round 3), with 202 and the run's own
   status. Every 202 names the runs whose cancellation it asked for
   (`cancellation_requested`, fix round 4). The model workflow's step sequence is
   unchanged and the acquisition workflow is new, so the DBOS `application_version` stays
   `nessa-l0-1`.

    **Writes without an expected version (controller ruling 11; fix round 1, review B
    M10).** Every write here goes through `run_idempotent` with an `Idempotency-Key`, but
    four take no expected version, because none changes versioned state: a cancel (a
    request recorded once, `ON CONFLICT DO NOTHING`, then `409 RUN_FINISHED` once the run is
    terminal), a favourite mark or unmark (an idempotent flag on a job), pasted text (a new
    attempt, copy and job each time, bounded by three per target) and an acquisition
    submission (a new run; a URL in flight is joined, one that failed backs off). A source
    search takes `expected_profile_version`, since it reads the profile. The cancel's
    answer, kept as its receipt, never carries model output (review B M1), and a run's
    output (a connection check's, a search's proposal, an acquisition's summary) is shown
    only once the run is `complete` (review B M1, M2). The worker handles each cancellation
    on its own, so one that fails never holds up the rest or dispatch (review B M8).

10. **Pasted text is its own route (ACQ-10, JOB-06).** Recorded at once by the API (no run,
    no fetch) as a finished attempt of route `pasted_text`, its body sealed, its claims
    `user_supplied`, its job an `exemplar`: the person's example of a target, at most three
    per target, never a live vacancy (freshness `never_verified`).

11. **Adzuna (R4; controller ruling).** The adapter (`nessa.evidence.adzuna`) records the
    request without `app_id` and `app_key` and builds the credentialed URL only for the one
    HTTP call; `redact` strips them from any URL. Adzuna's landing links may carry the app
    id as a parameter's value (`utm_source`), so the acquisition worker, which holds it,
    removes every such parameter from each `redirect_url`, and any other occurrence, before
    the response is parsed or hashed (`adzuna.without_app_id`); `make live-adzuna` fails
    if any result it would store still holds either credential (fix round 1, review A M3).
    Its HTTP endpoint answers a `Content-Length` that is not a non-negative integer with
    400 before reading (review A M8). Pay keeps its basis (`salary_is_predicted`
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
    Fix round 1 (review B I4, I5, I6): Meta runs the searches inside the one request, so
    `request_limit` cannot bound them; the activity holds the call's measured usage to the
    reservation's bounds on every path, a reply that also failed or was cut off included
    (`RunTask.exceeded_bound`; fix round 2, review B N4) (`web_search_requests` at most
    `max_tool_calls`, input tokens
    at most the reserved input), and an overrun fails the run `bound_exceeded` with the
    bound named in the attempt's outcome (`bound_exceeded:web_searches`), booked at its
    actual cost, its output never used. Whether Meta keeps to `max_tool_calls` is qualified
    live by `make live-smoke SEARCH_BOUND=1` (one in-process search asked for one tool
    call). A proposal with no candidate says why (`empty_reason`: `search_returned_nothing`,
    `no_candidate_proposed`, `all_excluded`), none of which is evidence that there is no
    vacancy, and records the hosts its pages came from (`source_hosts`). An exclusion's
    reason is an enum, and a proposed URL the checks refuse is kept as its host in plain
    text, never as a URL (addendum, re-review A I-4). The prompt (`source-search-3`) names
    exactly the hosts the manifest refuses (`search.refused_hosts`) instead of "sites that
    need a sign-in", and asks for individual postings.

13. **The validation repair stays within its reservation (MODEL-08).** `RepairBound`, on
    every task's agent, rewrites Pydantic AI's schema feedback as each problem's location and
    message, never its input (the rejected output), and cuts any feedback to the kind's
    repair allowance.

14. **Apply links are https only.** One check (`addresses.apply_link`) for every source of a
    view-or-apply link (pages and Adzuna): an `https` URL with a host after surrounding space
    is removed; `javascript:`, `data:`, hostless or unparsable links are no claim at all.

15. **Model extraction reads what structured data could not (fix round 2, controller
    rulings 9-15; ACQ-03, ACQ-04).** Spec section 6: "Use model extraction only for
    remaining ambiguity ... deterministic code approves records".
    - *What it reads.* Only a retrieved, permitted page whose structured data gave no
      posting (`no_structured_data`, `no_job_posting`): never a refused, failed, pasted or
      already parsed source. The restricted acquisition worker returns that page's visible
      text (`pages.visible_text`: scripts and styles left out; then normalised (entities
      decoded, every whitespace form one space, characters that do not print dropped), then
      redacted (`redact_shown`, an email split by inline markup included: fix round 4), then
      cut to 8,000 bytes of UTF-8, in that order, since normalising can reveal a detail (fix
      round 3, review C I1)); it still holds no model key (GC8).
    - *Where it runs.* `page_extraction`, a model-backed run kind on the one bounded activity
      (`PAGE_EXTRACTION_TASK`; one `RunTask`, no second call path), started by the
      acquisition in the transaction that records the page, at most
      `MAX_EXTRACTIONS_PER_ACQUISITION` (5) per acquisition, through
      `nessa.submit_page_extraction` (migration 0021), the worker's only way to start a run:
      it checks that the attempt is its own run's page that extraction may read and holds
      the same cap. Each is an ordinary model run (its own outbox entry, `nessa.model_run`
      workflow, reservation, the requester's own model and key, two requests at most with
      `RepairBound`): worst case $0.0034 on the test model and $0.048 on the production
      model, so three attempts fit the default $0.15 run limit. A page not handed over keeps
      a typed reason (`page_extractions.not_run`: `cap_reached`, `budget_exceeded`,
      `no_model_key`, `model_not_permitted`, `demo_workspace`, `no_visible_text`, and since
      fix round 3 `acquisition_cancelled`) and stays `no_posting_readable`. Demo workspaces
      never extract (a database CHECK as well). The budget check before a start counts the
      committed spend plus only this acquisition's started runs that have not reserved yet
      (no attempt, no cancellation), so a run that has reserved is never counted twice (fix
      round 3, review C M3); the activity's reservation remains the enforcement.
    - *Spend shown first (MODEL-08, fix round 3 item 5).* The job list (`GET .../jobs`, the
      read the research view makes before an acquisition starts) carries
      `acquisition_model_spend`, the true ceiling since fix round 4 (item 4):
      `MAX_EXTRACTIONS_PER_ACQUISITION` times one extraction run's worst case across every
      attempt its retry owner, the DBOS step, may make (`ACTIVITY_MAX_ATTEMPTS`, 3), each at
      the reservation the activity takes (`extraction_runs.acquisition_model_spend`, through
      `activity.run_worst_case_nano_usd` and the task's own `worst_case_nano_usd`, so the
      estimate and the reservation cannot drift): $0.051 on the test model, $0.716 on the
      production model, each run's three attempts within the default $0.15 run limit; none
      for a demo workspace. The field says it is a maximum. Task 8 shows it on screen.
    - *Cancellation (DUR-05, fix round 3 item 4).* Each extraction run records the
      acquisition that started it (`runs.started_by_run`, migration 0023). Cancelling a run
      also requests the cancellation of every run it started that has not settled (queued or
      running), even once the run itself has finished, when only those are cancelled; the
      worker acts on each request on its own, so a queued one is never dispatched and makes
      no provider request. The cancel and the start hold the same advisory lock on the
      acquisition (`run_store.lock_started_runs`), each as its first lock: the cancel
      before the workspace's row; the acquisition's recording transaction, whenever its
      page is model-readable, before the workspace's recording lock and before any insert
      (fix round 4, review C-1 N1: a kept body's document takes a key-share lock on the
      workspace's row, which the cancel's row lock waits for, so a later lock could
      deadlock;
      `test_a_cancel_while_a_kept_page_for_extraction_is_recorded_ends_without_a_store_error`).
      So a page recorded after a cancel is `acquisition_cancelled` and the SQL function
      refuses it too. The cancel's 202 lists the runs whose cancellation it asked for
      (`cancellation_requested`: the run itself while unsettled, the started runs, or both;
      fix round 4, review C-1 N2). A run cancelled while its call is out keeps its accepted
      result, as every run does.
    - *Input and retention.* The sealed input is that text, marked in the prompt as
      untrusted data. It is erased once the run is terminal, whatever its outcome, by
      `nessa.erase_run_input` (`RunTask.erases_input`), even after the requester's access
      ends; for every class, not only those whose body may not be kept, since a kept class
      keeps its body anyway. What remains is the text's hash (`page_extractions.text_sha256`,
      which every claim's span cites), the verified spans and their excerpts of at most 200
      characters.
    - *Output and approval.* The agent has no tools, only the output schema: for each advert
      (at most 3) each field is a verbatim quote, never a value of the model's own.
      `extraction.check_extraction` approves deterministically: a quote must be a span of
      the hashed text at word boundaries (the 6b `span_offsets`), and its value is read from
      that span by the JSON-LD path's rules (pay exact to the penny and in GBP, its period
      only as stated; dates as they parse; `apply_link`; no personal details; the claim
      bounds). Pay that cannot be read without a guess is refused, `salary_invalid` (fix
      round 3, review C I2): a range with a multiplier on one side only (`£30-35k`), a
      letter straight after a number, or after its `k`, that is not an attached period
      (`£1.2m`, `£2bn`, `£30,000ish`); "up to", "max" or "maximum" after the amount gives a
      maximum, as before it. Since fix round 4 (item 3) a period attached to the number
      reads as that period, never as a refusal: `pa`, `p.a.`, `ph`, `p/h` and the attached
      year and hour words the reader knows (`annual`, `annually`, `yearly`, `hourly`), so
      `£30,000pa`, `£14.50ph` and `£30kpa` are read exactly; an attached month, week or day
      form (`£2,000pcm`) is still refused. A negated work
      mode ("not remote", "non-remote") is `work_mode_unclear` (review C M1), also with up
      to two words between the negator and the mode word ("not fully remote", "this is not
      a remote role"; fix round 4, item 7), which errs towards unclear ("no commute, fully
      remote" is unclear too). The input is
      held to 8,000 bytes of UTF-8, as its reservation assumes (review C M4). A field
      without a verified span is dropped with its reason; a span whose
      value cannot be read is a quarantined claim; postings for one title that disagree on
      a critical field are all marked (`pages.mark_conflicts`); a posting without a verified
      title is dropped whole. Approved claims are `validation: model` and cite offsets (a
      CHECK). The run's output is this checked proposal; `RunTask.record` records its
      postings, through the acquisition's own recording path and lock, in the transaction
      that accepts it, and nothing goes into a receipt.
    - *What the listing says.* What the run recorded decides first, whatever the run's
      state (fix round 3, review C M2: a run cancelled while its call was out keeps its
      result, so its posting reads as read and is counted): a published posting is
      `succeeded` (`postings_read`); one read with no advert found is its own
      `no_posting_found_by_model` (and the list's `empty_reason` of that name, with words
      saying it is not evidence of no vacancies), never `none_found_in_sources_checked`;
      postings that all conflict are `postings_conflicting` (migration 0024, review C M5) and
      nothing verified is `not_read`, both `no_posting_readable`. With nothing recorded, a
      page whose run is queued or running is `pending`; one whose run failed or was
      cancelled first stays `no_posting_readable`. Each attempt says how its extraction went
      (`model_extraction`; words for each state in `MODEL_EXTRACTION_STATE`).
    - *What a page can still do.* It can lead the model to pick the wrong span of its own
      text as a field; it cannot put a value, a link or a field there that its text does
      not hold, start a run, reach the profile, a key or a tool, or have a URL fetched
      (`test_page_extraction.py::test_page_text_that_instructs_the_model_changes_nothing_outside_its_run`).
    - *Workflows.* Extraction runs are ordinary model runs and the acquisition step does more
      inside itself, so no workflow's step sequence changes: DBOS `application_version`
      stays `nessa-l0-1`.

## Evidence

`make check`; `make acceptance` (`test_acquisition.py`, `test_page_extraction.py`, the
cancellation cases in `test_durable_runs.py`, the stack's container checks); live: `make
live-smoke SEARCH=1` twice on the test model (ledger rows 27–28: one request each, two
searches, 21 and 14 sources returned, $0.005562 and $0.005587, leak scans clean, but no
candidate proposed); `make live-extract` once on the test model (ledger row 31: one request
on the synthetic fixture page, 700 input and 460 output tokens, $0.000162; one posting, all
nine fields approved as `model`, none dropped, the page's own instruction not followed;
leak scan clean); `make live-adzuna` blocked: no `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` in `.env`.

## Consequences and open items

- Not done in Task 7A: source-specific selectors and tuning extraction on real pages (Task
  7b assigns template families first, OI-09; the live extraction read one synthetic page);
  the Roles chapter and every UI over these endpoints (Task 8); research data in the
  workspace export (T15); ASHE, UK-SOC and the AI evidence (Task 7B).
- Model extraction (decision 15): the budget check before starting one counts the
  committed spend and this acquisition's unreserved runs only, so a run elsewhere in the
  workspace that reserves later can still refuse one at its own reservation
  (`budget_exceeded`, the page stays unread). A page can lead the model to the wrong span
  of its own text; the pay, period and work-mode words and the date forms read are
  provisional (R6). The model-spend estimate is shown by Task 8.
- Fix round 3 migrations: 0022 (`visible_text_detail`), 0023 (`runs.started_by_run`, the
  cancellation lock, `acquisition_cancelled`), 0024 (`postings_conflicting`). Fix round 4:
  0025 (`attribute_detail`).
- Pre-existing lock pattern, not fixed in fix round 4 and carried to the final review:
  `cancel_run` locks the workspace's row `FOR UPDATE` and then takes a key-share lock on
  the run's row (the `run_cancellations` foreign key), while a worker transaction can hold
  the run's row `FOR UPDATE` and then write an event, which updates the workspace's row;
  the two can deadlock, and PostgreSQL then ends one with a store error (the worker's step
  retries; the person repeats the cancel). The cascade makes this possible for up to five
  more runs.
- The live search proposed no candidate in two tries; candidate quality is unqualified.
- The Adzuna live integration is unverified until credentials are in `.env` under those two
  names.
- A new error code (`RUN_FINISHED`), failure classes (`retrieval_failed`,
  `source_blocked`), event kinds (`run.cancel_requested`, `research.updated`) and run kinds
  (`acquisition`, `source_search`, and in fix round 2 `page_extraction`); migrations 0013
  and, for extraction, 0021 (also the `model` validation state and `page_extractions`).
