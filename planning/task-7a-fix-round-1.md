# Task 7A — fix round 1 (FIX_BASE 5c5e5bb)

Reviews: `task-7a-review-A.md` (security: C1, I1–I5, M1–M9) and `task-7a-review-B.md`
(runs/data: C1, I1–I6, M1–M12). Both: Spec ❌, Needs fixes. Read both reviews in full; the
items below are the controller's rulings on them. "A-" and "B-" name the review.

Scope: this round fixes the review findings only. **Do not build model extraction (ACQ-03
residual, ACQ-04's model part) in this round**: it is fix round 2, dispatched after this
round is re-reviewed, so each re-review stays small. Order: security first, then data, then
minors; one commit per coherent group; tests RED first where practical.

## Security (package A)

1. **A-C1, retention from a page's self-claim. Ruling:** retention never follows a page's own
   claims. An unlisted page is `other` (excerpts only) unless the manifest lists its host as
   an employer careers or ATS host, or an agent's dated classification is recorded. The
   agent's classification (`tools/corpus.py --rights-class`) overrides a page-derived class
   in both directions. A page's `hiringOrganization` may still give a cited
   `advertiser` claim, but it never changes retention. Add hostile-page tests: a self-naming
   page, a public suffix (`co.uk`, `github.io`), an agency on its own board (Reed/Totaljobs
   host naming itself). Correct ADR 0009 decision 4.
2. **A-I1, cross-host redirects.** For every cross-origin hop, apply `rule_for` (record a
   blocked `source_denied`/`source_api_only` attempt with the redirects so far), robots.txt
   for that origin, and the pacer, all before the request. Tests: a redirect to a denied host
   (the `lnkd.in` → linkedin shape, against the controlled server), to an `api_only` host, and
   to an origin whose robots.txt disallows. Correct ACQ-06.
3. **A-I2, robots.txt. Ruling:** implement RFC 9309 group selection and longest-match with
   `*` and `$` as a small pure function in the fetcher module (no new dependency), replacing
   `urllib.robotparser`. Tests: the reviewer's four cases, plus allow-beats-disallow at equal
   length and user-agent group selection.
4. **A-I3, total time bound.** Enforce the deadline in every phase: bound the resolve, cap the
   number of addresses tried, wrap the stream so every read, write and TLS start uses
   `min(per-op timeout, deadline − now)`. Tests with the controlled server: trickled status
   line and headers, an endless 1xx stream. Correct ACQ-02 and ADR decision 3.
5. **A-I4, the live-mode relay.** Put `acquisition` on its own internal network shared only
   with `worker`, off `internal`. Stack probe: `api` and `web` cannot reach
   `acquisition:8100` (must fail), and `worker` can. Correct ACQ-05 and ADR decision 1.
6. **A-I5, unchecked URLs in URL fields.** Only http(s)-checked URLs go in URL-named fields
   (`redirects`, target `url`, `requested_url`, `source_url`). A refused or unchecked target
   is recorded as labelled text (for example `refused_target`), never as a URL. Check a
   pasted text's `source_url` with the URL checks or drop it. Fix the fetcher test that
   asserts `file:///etc/passwd` is recorded. Tests for each field.
7. **A-M6, third parties' personal details. Ruling:** session 1's "always true" clause ("a
   third party's personal details (recruiter names, phone numbers) never kept") binds
   everything kept: bodies, excerpts and claim values. Deterministically redact email
   addresses and phone numbers (UK and international forms), and structured contact fields
   (JSON-LD `applicationContact`, `contactPoint` names, emails, phones), before anything is
   hashed for spans or sealed. Keep the retrieved bytes' own hash separately for change
   detection. Personal names in running text cannot be detected deterministically: record
   that as a known limit in ADR 0009, for the product owner. Do not try to detect names.
   Tests: bodies, excerpts and claims with emails, phones and contact fields.
8. **Minors, all fixed:** A-M1 (refuse `%` in IP literals, add `is_site_local`, test the
   https→http refusal); A-M2 (correct the docstring, or refuse non-ASCII digits before IDNA,
   and make the test say which refusal); A-M3 (in the acquisition worker, strip any query
   parameter whose value equals the app id from `redirect_url` before parsing; the live
   qualification scans stored claims for the app id); A-M4 (bound every `Claim` string
   value; reference-only classes never exceed the 200-character excerpt bound); A-M5 (an
   unreachable robots.txt is a transient failure, still with no page request); A-M8 (400 for
   a `Content-Length` that is not a non-negative integer); A-M9 (scan the running
   container's environment values and readable files for the stack's actual database
   passwords and master key, never printing them). A-M7: no action (the reviewer checked
   every final expectation).

## Runs and data (package B)

9. **B-C1, an unreadable page is "none found".** Persist the parse issue on the attempt (a
   label column with a CHECK). Count "retrieved, no readable posting" separately in the run
   summary and coverage. Add `empty_reason` `no_posting_readable` when any retrieved source
   had a parse issue; only a page whose structured data was read and holds no posting may
   support `none_found_in_sources_checked`. Assert the label in the `/plain` test; correct
   ACQ-03 and ACQ-07. (Round 2's extraction will then turn some of these readable.)
10. **B-I1, stored dedupe. Ruling:** one rule. The stored path computes membership with the
    same pure rule the property tests cover (`group_copies`), over the candidate set, and
    merges jobs when a new copy bridges two: copies, claims and favourites move to the oldest
    job, the others are removed. Integration test: the reviewer's three-copy case in every
    arrival order gives one job. Correct PROP-02 and JOB-02.
11. **B-I2, exemplars in counts.** Exclude exemplars from `total_jobs`, `city_counts` and the
    `empty_reason` decision (report `exemplars` as their own count); exclude the
    `pasted_text` route from `coverage`. Test the combined case (every fetch failed plus one
    pasted example).
12. **B-I3, Adzuna truncation.** Store Adzuna's `count` on the attempt, expose "retrieved n of
    total" in `AcquisitionOut` and the listing coverage, and make `total > retrieved` an
    explicit partial result. The fixture's `count` exceeds its results; test it.
13. **B-I4, search bound. Ruling:** after the call, compare `usage.web_search_queries` with
    `MAX_TOOL_CALLS` and input tokens with their bound. An overrun books the actual cost,
    records an attempt outcome label, and fails the run with a typed reason: the output is
    not used. Qualify enforcement once, live (item 15). Reword JOB-08 until then.
14. **B-I5, zero candidates.** Add an `empty_reason` to the search result
    (`no_candidate_proposed`, `all_excluded`, `search_returned_nothing`), with words in
    `vocabulary.ts` that say zero candidates is not evidence there are no vacancies. The live
    smoke's ledger notes record `excluded` with reasons and the source hosts (hosts only).
15. **Zero-candidate cause (your concern 2). Ruling:** take reviewer B's cause analysis
    (`search.py:53`): replace the open-ended "Indeed, LinkedIn and other sites that need a
    sign-in" with the refused hosts named from the manifest, and keep the individual posting
    as the aim. Then live, in scope `live-search`, test model only, synthetic target:
    - one call with `max_tool_calls: 1`, expecting one search (qualifies B-I4);
    - at most two calls with the revised prompt.

    That is at most 3 requests (scope total then 5 of 9). If both still propose nothing, stop:
    record "candidate quality not established" with the excluded reasons and hosts, and tune
    no further.
16. **B-I6, free strings.** `empty_reason`, target `status`, the skipped, attempt and
    exclusion reasons, and the coverage keys become `StrEnum`s in the domain modules, used in
    the schemas; regenerate the client (`pnpm run generate`) and commit it.
17. **Minors, all fixed:** B-M1 (no model output in the cancel receipt; show the output only
    for `COMPLETE` runs); B-M2 (a search proposal and `summary_of` only for `COMPLETE` runs);
    B-M3 (CHECK `field IN (...)`, a CHECK on the span's shape, a composite foreign key
    `(copy_id, attempt_id)`, in a new forward migration, never by editing 0013); B-M4
    (publish `access_revoked`, no `pending` attempt left); B-M5 (count robots.txt requests in
    `http_requests`); B-M6 (a hash mismatch on a kept body fails the attempt with a label);
    B-M7 (no silent 10,000 cap: a capped total is marked partial; compute totals once per
    listing, not per page, without one lookup per copy); B-M8 (each cancellation in its own
    `try`, so one failure never blocks dispatch); B-M9 (remove `store.job_count` and
    `store.document_kept`); B-M10 (record ruling 11 and the other no-expected-version writes
    in ADR 0009); B-M11 (a step re-run after a crash skips a target that failed for good).
    B-M12 (split or rename `evidence/acquisition.py`): deferred to the final review; do not
    refactor in this round.

## Also

- Run `make check`, then `make acceptance` once at the end, and name each covering test.
- **Live calls:** only item 15's, at most 3 requests, ledgered. No production model. No Adzuna
  call: the credential names are still unresolved, and that is for the product owner.
- Use the Edit and Write tools only for file changes: no sed, heredocs, one-liners or
  `touch`. Never read `.env` or NESSA_HOME, never commit `~$ssa_Local_Development_Plan.docx`,
  never touch the agentsolve-* or eigenprompt-* Docker projects. No subagents.
- Say whether DBOS `application_version` changes; it must change if a workflow's step
  sequence does.
- Update the proposed CLAUDE.md wording in your report if these fixes change it. Do not edit
  CLAUDE.md.
- Append the fix report to `task-7a-report.md` under "Fix round 1", then reply with the short
  contract: status, commits, a one-line test summary and concerns.
