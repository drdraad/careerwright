### Spec Compliance

- ❌ Issues found (slice 7A, package A: security, fetch, Adzuna, the restricted worker, live tools):
  - **Misunderstood: session 1 line A5.** An unlisted page becomes `employer-posting`, with its body kept, on its own unverified word. Public suffixes match too (C1: `backend/src/nessa/evidence/sources.py:102-121`).
  - **Incomplete: "redirects re-checked".** Only the URL and address are re-checked on a redirect. The source permission manifest (denied or API-only hosts), robots.txt and pacing are applied to the first host only (I1: `backend/src/nessa/evidence/acquire.py:130`, `backend/src/nessa/evidence/fetcher.py:462-474`).
  - **Misunderstood: "robots.txt obeyed (RFC 9309)".** `urllib.robotparser` ignores `*` and `$` and applies the first matching rule instead of the longest one, so disallowed pages are fetched (I2: `backend/src/nessa/evidence/fetcher.py:447-458`).
  - **Missing: the total time bound.** The 20 s deadline is not enforced while resolving, connecting or receiving the status line and headers (I3: `backend/src/nessa/evidence/fetcher.py:351-399`).
  - **Incomplete: "only the two workers have a route out" (live mode).** Every container on `internal`, the API included, can relay through the unauthenticated acquisition service (I4: `compose.yaml:135-148`, `backend/src/nessa/acquisition.py:184`).
  - **Apply-link ruling.** It is met for apply links. Other URL fields that a UI could render as an `href` still hold unchecked URLs, including `javascript:` (I5).
  - **Missing, known to the controller and recorded honestly:**
    - model extraction for pages without structured data (the ACQ-03 residual and ACQ-04's model part);
    - the Adzuna live qualification (blocked: credential names absent).
- Honesty check on the known items: no defect.
  - `docs/requirements-register.md:444` (ACQ-03), `:445` (ACQ-04) and `:461` (JOB-05) are `planned`, with those items named as open.
  - ADR 0009's status line marks decision 2 and the decision 6 word list provisional.
  - The runbook and ADR consequences say Adzuna is unverified.
  - `docs/requirements-register.md:450` (ACQ-09) is "verified with a recorded deviation" and names the pending product owner confirmation. It does not mark that confirmation done.
- Three rows overclaim because of I1, I3 and I4. They should be corrected with the fixes:
  - `docs/requirements-register.md:443` (ACQ-02, "time bounded");
  - `:446` (ACQ-05, "only it and the DBOS worker have a route out");
  - `:447` (ACQ-06, "a user-supplied URL never overrides permissions").
- ⚠️ Cannot verify from diff:
  - Adzuna's live response shape (the `redirect_url` query parameters, see M3; the pay period).
  - Adzuna's terms page text quoted in `sources.json`.
  - That X01's robots.txt was read and the page returned 404 (no network allowed).
  - Whether Meta enforces `max_tool_calls`.
  - Scrapling 0.5's imports: only 0.4.15 is installed.
  - That the running acquisition container can read the 0600 Adzuna files. The stack test runs only `--check`, and the Adzuna integration test runs the service in-process. It works for the master keys by the same mechanism.
- Method: I read the package diff in five passes:
  1. Makefile and pyproject, the worker, acquire, addresses, Adzuna, amounts;
  2. fetcher and pages;
  3. sources and the architecture tests;
  4. the domain, stack and support tests;
  5. tools, compose, corpus, ADR and dependencies.

  I made one focused check per named risk, listed below. My only executions were:
  - two pure-function runs: the URL and address checks on 34 inputs, and the self-attestation case;
  - one pure run of `urllib.robotparser`;
  - one run of `_recordable`;
  - one loopback probe of the deadline, using a controlled server and the fetcher's test-only `extra_allowed`. The script is `/private/tmp/claude-501/-Users-darianraad-Code-careerpathoptimizer/97b1e108-19c9-45e9-9fd3-f372d0f9e9b6/scratchpad/deadline_probe.py`.

  None of these touched the network or used a live call.

**Named risks, with what I checked**

1. **SSRF.** I read `addresses.py` and `fetcher.py` in full and ran `check_url`/`address_refusal` on zone IDs, site-local, NAT64 local-use, IPv4-compatible, Unicode digits, IDNA, userinfo and backslash forms.
   - DNS rebinding: OK. `_GuardedBackend.connect_tcp` (`fetcher.py:138-164`) resolves once at connect time, refuses the host if any answer fails, and connects to `str(address)`. TLS still verifies the name.
   - IPv6 (mapped, 6to4, Teredo, NAT64, `::/96`): refused. Gaps: `fec0::/10` passes, and the zone-ID handling differs from its comment (M1).
   - Decimal, octal, hex, short-form and percent-encoded IPv4, and userinfo: refused.
   - IDNA: the host is checked in its ASCII form.
   - Every redirect re-checks the address and refuses an https→http downgrade (`fetcher.py:295-309`; the downgrade check has no test, M1). The manifest and robots.txt are not re-checked (I1).
   - robots.txt is fetched under the same guard, with its own pool and a 512 KB bound. Its parser is not RFC 9309 (I2).
   - Size is bounded after gzip and deflate decompression, incrementally with `max_length`, and brotli is refused.
   - The content type is checked.
   - Time: bounded per read, not in total (I3).
2. **Adzuna credentials.**
   - `transport_url` has one caller (`acquire.py:206`). The `Fetched`/`FetchFailure` objects that carry the credentialed URL never leave `acquire_adzuna`. Failures carry labels only, and httpcore exceptions are mapped by class with no message kept. The worker logs path and status only (`acquisition.py:154-158`).
   - The DBOS step sends only the query.
   - `live_adzuna.py` ledgers `GET {recorded_url}` with counts in `notes`.
   - The integration test scans both databases, the worker log and the API responses for the app id and the key (with fragments): `backend/tests/integration/test_acquisition.py:471-535`.
   - Setup writes 0600 files with O_EXCL in a 0700 directory, never prints a value and passes nothing as an argument (`backend/tools/localenv.py:41-49,94-111`).
   - The mount is read-only and on the acquisition service only (`compose.yaml:142`).
   - The API gets only a boolean (`compose.yaml:91`, `backend/tools/stack.py:74`).
   - One unverifiable caveat: the app id may appear inside Adzuna's `redirect_url` values (M3).
3. **GC8.** The worker holds no such credentials, and this is shown on the running container, not only asserted.
   - Import closure: `backend/tests/architecture/test_boundaries.py:322-336`.
   - Exact settings fields: `:339-347`.
   - `docker inspect`: the only mount is `/run/nessa/adzuna` (read-only), there is no `/run/secrets`, and no environment name contains `DATABASE`, `MASTER_KEY` or `META` (`backend/tests/stack/test_local_stack.py:238-258`). This environment check is by name only (M9).
   - Demo mode includes acquisition in the no-route probe: OK.
   - Live mode: direct egress is limited to the two workers, but the API and web can reach the internet indirectly through the acquisition service (I4).
4. **Apply links.** One validator, `addresses.apply_link`, used at `pages.py:349` and `adzuna.py:247-250`. A rejected link becomes no claim, and both paths are tested. Other unchecked URLs reach API fields: I5.
5. **Rights and retention.**
   - `_KEEP_PRIVATELY` is exactly classes A1–A5 (`sources.py:26-34`). A test ties the code's classes to the corpus manifest.
   - Every excerpt site cuts at 200 characters (`pages.py`, `adzuna.py`).
   - Adzuna is `job-board`, `api_only`, excerpts only.
   - "Whose site it is on" is self-attested and accepts public suffixes. A hostile page, or an ordinary agency page on Reed, raises itself to body retention (C1).
   - Claim values are not length-bounded (M4).
6. **Live tools.**
   - `make live-adzuna` and `SEARCH=1` are separate explicit targets. Neither `make check` (unit marker) nor `make acceptance` (integration and stack markers) reaches them.
   - Adzuna: 10 per scope and 2 per run, checked under the ledger lock before any request (`backend/tools/live_adzuna.py:41,104-117`).
   - Search scope: 9 calls, 0 production calls, $0.30 (`backend/tools/live_smoke.py:708`). `--search` refuses `--production-model`.
   - Ledger rows 27–28 carry tokens, searches and cost (search priced at `model_registry.py:20`).
   - The blocked path returns at `live_adzuna.py:98` before any `Fetcher` exists, so nothing is sent. The test proves it by the empty ledger.
7. **Scrapling.** The claim is verified for 0.4.15 in `backend/.venv`:
   - `scrapling/engines/static.py` imports `toolbelt/convertor.py` (Playwright, Patchright, curl_cffi) and `toolbelt/fingerprints.py` (browserforge).
   - `scrapling/__init__.py` is lazy.
   - `scrapling/parser.py` imports only lxml, cssselect and Scrapling core (orjson, w3lib).
   - With `adaptive` off (the default; `pages.py` never sets it), neither the SQLite storage nor `tld` is touched. lxml's `HTMLParser` keeps `no_network=True`.
   - None of playwright, patchright, browserforge, curl-cffi or mcp is in `backend/uv.lock`.
   - `scrapling==0.4.15` is pinned (`backend/pyproject.toml:24`) and recorded with its transitive dependencies in `docs/dependencies.md`.
   - The parser adds no network path.
8. **Process breach.** See M7. The pre-edit content was never committed, so the four changes cannot be identified. Every final expectation is correct and none is weakened.
9. **Corpus.**
   - X01 and X02 are recorded honestly. X01's constructed path is obvious from its URL. X02 records `request_sent: false`.
   - The OI-11 manifest agrees with session 1 for every host it lists.
   - Hosts the policy names but the manifest omits (Skills England, ONS, Find an Apprenticeship, course providers, professional bodies) fall to `other`, which is conservative.
   - Reed and Totaljobs are unlisted, which is what exposes them to C1.

### Strengths

- The SSRF core is careful. Connecting to the checked address closes the DNS rebinding window by construction. Only canonical dotted-quad IPv4 is accepted. Every IPv6 form that embeds IPv4 is refused outright. Decompression is bounded per call with `max_length`, so a bomb can never be held in memory. The controlled source server records every request, so tests can prove that nothing was requested.
- The Adzuna credential boundary is real. The credentials exist only inside the acquisition container. The recorded URL is built separately from the transport URL, and no object that carries the credentials leaves `acquire_adzuna`. The integration test scans persisted cells, logs and responses for both values.
- The restricted worker is small and has no database. Its GC8 evidence includes inspection of the running container, not just naming conventions in code.
- The live tools enforce their caps in code before any request, under the ledger's exclusive lock. The blocked path cannot send.
- I verified the Scrapling deviation against the installed package. It is recorded as provisional (R6) rather than silently assumed.
- The known gaps are honestly recorded in the register, the ADR and the report.

### Issues

#### Critical

**C1. A page raises its own retention class by naming itself as the hiring organisation; "whose site it is on" is never actually checked.**
Code: `backend/src/nessa/evidence/sources.py:102-121`, `backend/src/nessa/evidence/pages.py:220-231,421`, `backend/src/nessa/evidence/acquire.py:148-157`, `backend/tools/corpus.py:42`.

- **What.** `classify_page` compares the final host with hosts taken from the same page's JSON-LD: `hiringOrganization.sameAs` and `.url`, merged across every posting on the page. Nothing outside the page corroborates "their own careers site".
- **Public suffixes.** The only guard is `"." in hiring_host`, so public suffixes match every host under them.
- **Focused run.**
  - `classify_page("www.totaljobs.co.uk", hiring_hosts=("co.uk",))` gives `employer-posting`, retention `body`.
  - The full `parse_page` path for a Totaljobs-host page whose JSON-LD says `"sameAs": ["https://co.uk"]` gives `body`.
  - `www.reed.co.uk` naming `reed.co.uk` gives `body`.
  - `someone.github.io` naming `github.io` gives `body`.
- **Realistic without hostility.** Agencies post their own vacancies on their own boards naming themselves as `hiringOrganization`. Reed is one, and session 1 line 6 names Reed and Totaljobs as reference only.
- **The agent cannot correct it.** `tools/corpus.py:42` applies an agent's `--rights-class` only when the page came out `other`. So `--rights-class job-board` still writes the body to `var/evidence/corpus/` for Task 7b.
- **Side effect.** The same self-claim sets `advertiser=employer` (`pages.py:289`).
- **Tests.** Only the bare label `example` is tested (`backend/tests/domain/test_sources.py:111`).

**Why it matters.** Untrusted input decides the retention class. Pages that session 1 makes reference only, or that are "not clearly within one class" and must "stay with you", get their full bodies retained. That breaks the session 1 policy and R10 ("before any page body is retained beyond the source classes it permits"). ADR 0009 decision 4 presents this as a check.

**Fix.**
- Do not derive A5 from the page's own claims. An unlisted page stays `other` (excerpts only) unless one of these holds:
  - the manifest lists the employer's careers or ATS host;
  - an agent's dated classification is recorded.
- Let the agent's classification override a page-derived class in both directions.
- If any page-derived signal is kept, compare registrable domains using the public suffix list (`tld` is now in the lock) and exclude agency and board markers.
- Add hostile-page tests: a self-naming page, a public suffix, and an agency on its own board.

#### Important

**I1. The source permission manifest, robots.txt and pacing are not applied to redirect targets on another host.**
Code: `backend/src/nessa/evidence/acquire.py:130-142`, `backend/src/nessa/evidence/fetcher.py:295-309,462-474`.

- **What.**
  - `rule_for` runs for the requested host only.
  - `fetch_page` reads robots.txt for the first origin only.
  - `fetch` then follows up to 5 redirects to any host, re-checking only the URL and address.
- **Effect.** A permitted or unlisted host can redirect to a `denied` host (linkedin.com, indeed), to an `api_only` host (adzuna.co.uk), or to a page whose robots.txt disallows Nessa, and the fetch goes ahead. `_page_result` classifies by the final host only after the request was made.
- **Realistic case.** `lnkd.in` short links redirect to `www.linkedin.com`, which is denied and whose robots.txt disallows unknown agents.
- **Tests.** No test covers a cross-host redirect to a denied host or to a disallowing robots.txt.

**Why it matters.** ACQ-06 ("a user-supplied URL never overrides permissions") is marked verified but can be bypassed by one hop. This contradicts R3 and the session 1 "robots.txt respected" clause.

**Fix.** For each cross-origin hop:
- apply `rule_for`, and record a blocked `source_denied` or `source_api_only` attempt with the redirects so far;
- apply robots.txt for that origin;
- apply the pacer.

Add tests for each case.

**I2. robots.txt is not parsed per RFC 9309, so disallowed pages are fetched.**
Code: `backend/src/nessa/evidence/fetcher.py:447-458`.

- **What.** `urllib.robotparser.RobotFileParser` ignores the `*` and `$` wildcards and uses the first matching rule rather than the longest. Pure check on the backend's Python 3.12.12: `can_fetch` returns True for the URL each rule disallows in all four cases:
  - `Disallow: /*/apply` against `/jobs/apply`;
  - `Disallow: /*?` against `/jobs?id=1`;
  - `Disallow: /*.pdf$` against `/a.pdf`;
  - `Allow: /` followed by `Disallow: /private` against `/private/job`.
- **Where it is claimed.** The module docstring, the `sources.json` "robots" text and ADR 0009 decision 3 all claim RFC 9309.

**Why it matters.** Wildcard rules are common on job and ATS sites. R3 and session 1 require robots.txt to be respected.

**Fix.** Either implement RFC 9309 group selection and longest-match with `*` and `$` (small, pure and testable), or disallow on doubt when a rule uses them. Add the four cases above as tests.

**I3. The total time bound is not enforced during resolve, connect, TLS or header reception.**
Code: `backend/src/nessa/evidence/fetcher.py:112-125,150-164,351-399`.

- **What.** The deadline is checked before each request and between body chunks only. Three phases are not covered:
  - `getaddrinfo` has no timeout;
  - each resolved address may take up to `connect_s`, with no cap on the number of addresses;
  - httpcore2 receives the status line and headers with the per-read timeout only, looping over unlimited 1xx responses and up to 100 KiB of header bytes (`httpcore2/_sync/http11.py:160-172,194-210`).
- **Loopback probe** with `total_s=1.0, read_s=1.0`:
  - a server sending `102 Processing` every 0.4 s took 3.2 s;
  - a server trickling the status line at one byte per 0.2 s took 6.4 s;
  - both ended only because the server stopped, and an endless 1xx stream never ends.
- **Knock-on effect.** Each hung request holds a thread in the acquisition worker (`ThreadingHTTPServer`, unbounded). After the client's 90 s timeout (`service_client.py` `REQUEST_TIMEOUT_S`) the DBOS step retries, which starts another hung request.
- **Docs.** ACQ-02's row and ADR decision 3 ("20 s in all") overclaim.

**Why it matters.** "Time checks" is a named card requirement. A hostile or broken source can tie up the acquisition worker indefinitely.

**Fix.**
- Wrap the stream returned by `_GuardedBackend.connect_tcp` so that every `read`, `write` and `start_tls` uses `min(per-op timeout, deadline − now)` and raises once the deadline has passed.
- Cap the number of addresses tried.
- Bound the resolve.
- Add tests for trickled headers and repeated 1xx responses.

**I4. In live mode the unauthenticated acquisition service gives every internal container an indirect route out.**
Code: `compose.yaml:22-25,135-148`, `backend/src/nessa/acquisition.py:184`, `backend/tests/stack/test_local_stack.py:198-245`.

- **What.**
  - `acquisition` inherits `networks: [internal]` from `x-backend`.
  - It listens on `0.0.0.0:8100` without authentication.
  - The API (which holds the database password and the master key), web, auth and edge can all POST `/v1/fetch` or `/v1/adzuna`.
  - In live mode that relays to any public host, with data in the URL, and to the Adzuna credential.
- **Regression.** Before 7A the API had no egress at all (BND1-11). The live-mode stack test probes only direct connections.

**Why it matters.** ACQ-05 and ADR decision 1 ("only it and the DBOS worker have a route out") are not established. A compromised API or web container gains an egress and exfiltration channel.

**Fix.**
- Put `acquisition` on a dedicated internal network shared only with `worker`, and take it off `internal`.
- Add a stack probe from `api` and `web` to `acquisition:8100` that must fail.

**I5. Unchecked URLs, including third-party `javascript:` ones, are stored in API fields that a UI will render as links.**
Code: `backend/src/nessa/evidence/fetcher.py:307-308`, `backend/src/nessa/evidence/acquisition.py:133-143`, `backend/src/nessa/api/research_schemas.py:38-40,65,196`.

- **Redirects.** Every `Location` target is appended to `redirects` before it is checked. A hostile server's `javascript:…`, `data:…` or `file:///…` is therefore stored and served as `AttemptOut.redirects`. The fetcher test even asserts that `file:///etc/passwd` is recorded (`backend/tests/domain/test_fetcher.py:98,114`).
- **Refused submissions.** `_recordable` returns the raw string for every refusal except malformed, too long and credentials. I ran it: `javascript:alert(1)` comes back unchanged. That string becomes the target `url` and the attempt's `requested_url`.
- **Pasted text.** The same raw string becomes the attempt's `requested_url` and therefore `JobCopyOut.source_url` of an exemplar job.
- No web code reads these fields yet, so the risk is latent.

**Why it matters.** The controller asked that no other path store an unchecked URL as something a UI could render as an `href`. `source_url` and `redirects` are exactly such fields, and Task 8 is about to render them.

**Fix.**
- Keep only http(s)-checked URLs in URL-named fields.
- Record refused or unchecked targets as labelled text, for example `refused_target`, never as a URL.
- Check a pasted text's `source_url` with the URL checks, or drop it.
- Add tests.

#### Minor

**M1. Gaps in the address checks, and missing tests.**
- The https→http downgrade refusal (`fetcher.py:299`) is correct but has no test.
- The `_ip_literal` comment says a zone ID is refused (`addresses.py:79`), but Python 3.12 parses scoped IPv6. As a result:
  - `[fe80::1%25eth0]` is refused only because it is link-local;
  - `[2606:4700::1111%25eth0]` passes `check_url`. This is harmless, since it fails at resolution.

  Fix: refuse `%` in literals as `_name` already does, and add tests.
- `fec0::/10` (deprecated site-local) passes, because `is_global` is True for it in 3.12.12. Fix: add `is_site_local`.

**M2. An inaccurate docstring** (`backend/src/nessa/evidence/addresses.py:5-8`).
- It says encoded forms are "refused rather than decoded". In fact a trailing dot and Unicode digits are decoded by IDNA and then refused by the address check, and a public address written in Unicode digits is decoded and fetched.
- `test_encoded_address_forms_are_refused` accepts either refusal, which hides this.
- Fix: correct the text, or refuse non-ASCII digits before IDNA.

**M3. Unverified: Adzuna's `redirect_url` may carry the app id** (`backend/src/nessa/evidence/adzuna.py:247-250`).
- Public Adzuna response examples I recall show landing links with `utm_source=<app_id>`. I could not verify this here, and the synthetic fixture uses `?se=synthetic`.
- The adapter stores `redirect_url` verbatim as the apply-link claim and its excerpt. `redact` matches parameter names only.
- Fix: in the acquisition worker, which knows the value, strip any query parameter whose value equals the app id before parsing. Have the live qualification scan stored claims for it.

**M4. Claim values are unbounded** (`backend/src/nessa/evidence/pages.py:272`, `backend/src/nessa/evidence/records.py:164-171`).
- The title claim's value is the untruncated title (the copy's title is cut to 300). The same holds for employer, employment type, source ID and location parts.
- For reference-only classes this keeps page text beyond the 200-character excerpt bound.
- Fix: bound `Claim` string values.

**M5. A robots.txt outage is recorded as a policy refusal** (`backend/src/nessa/evidence/fetcher.py:450-453`).
- When robots.txt is unreachable (5xx or a timeout), the page becomes a non-transient BLOCKED `robots_unreachable`, cached for 10 minutes.
- So a temporary outage is never retried and can end a run as `source_blocked`.
- Fix: keep "no page request", but make it a transient failure.

**M6. Needs a controller ruling: personal details in kept bodies.**
- Session 1's "always true" clause says "a third party's personal details (recruiter names, phone numbers) never kept".
- Bodies for classes A1–A5 are kept verbatim, with no redaction.
- Decide whether that clause binds kept bodies.

**M7. Process breach** (one-liner edit of `backend/tests/domain/test_addresses.py`, `touch` for `__init__.py`), disclosed by the implementer.
- The file first appears in `6fda2c2` already edited and is unchanged after that, so the pre-edit expectations cannot be recovered.
- I ran every final refusal and address expectation. Each matches the code and is the correct, safe outcome:
  - `\\@` gives `malformed_url`;
  - `postgres:5432` gives `port_not_allowed`;
  - `not a url` gives `malformed_url`;
  - `https:///no-host` gives `host_not_allowed`;
  - `::ffff:93.184.215.14` is refused, which is stricter and matches the docstring.
- No assertion was weakened into accepting a non-refusal. The only two-valued assertion still requires a refusal.

**M8. Malformed Content-Length on the worker's own endpoint** (`backend/src/nessa/acquisition.py:146-150`).
- A negative `Content-Length` makes `rfile.read(-n)` read to EOF, which blocks the thread on a keep-alive connection.
- A non-numeric one escapes `do_POST`, and socketserver prints a traceback.
- Only internal callers can reach it.
- Fix: refuse a value that is not a non-negative integer with 400.

**M9. The GC8 environment check is by name only** (`backend/tests/stack/test_local_stack.py:250-251`).
- It checks environment variable names (`DATABASE`, `MASTER_KEY`, `META`).
- A value-based scan of the container's environment and filesystem for the stack's actual database passwords and master key would prove absence rather than a naming convention.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The SSRF address core, the Adzuna credential boundary, the restricted worker's isolation from secrets and the live-tool caps are sound and well evidenced. However, four policy controls fail against inputs a hostile or ordinary page can supply:
- retention follows a page's self-declared employer (C1);
- manifest and robots.txt decisions stop at the first hop (I1);
- robots.txt matching is not RFC 9309 (I2);
- the total time bound does not cover headers (I3).

The live-mode egress isolation (I4) and the URL fields that a UI could render as an `href` (I5) also need closing before Task 7b runs real pages through the pipeline.
