# Review: fetch proxy mode (d7c5ac7..8c58dfc, worktree `careerwright-wt/proxy`, head 8c58dfc)

Reviewer: the one independent reviewer (R16). Read-only; no web requests, no live calls, no
Docker, `.env` not read. The package diff (1,625 lines) was read in three passes. The
implementer's suites were not re-run (no concrete doubt needed one); their `make check` claim
is the implementer's, not verified here.

### Spec Compliance
- ✅ Spec compliant on items 1-5 of the dispatch, with one truth gap in the amendment (I1).
- ⚠️ Cannot verify from diff: the real fetch through the session proxy (controller's run;
  no web requests here); `make check` and acceptance on the final code.

Named risks, what I checked, and the result:
1. **No product path can select proxy mode.** `grep Fetcher` over `backend/src/careerwright`:
   the only construction is `acquisition.py:224`, `Fetcher(user_agent=...)`, no proxy. The
   API and DBOS worker construct none. `AcquisitionSettings.fetch_proxy: None`
   (`acquisition.py:63`) makes any `CAREERWRIGHT_FETCH_PROXY` value fail validation, so the
   worker refuses to start rather than ignore it (needed, since the settings ignore extra
   variables); the boundary test pins the field's type to `None`. httpcore reads no proxy
   variables; `test_the_default_fetcher_ignores_a_proxy_in_the_environment` proves it
   against the fake proxy. The AST test refuses any product import of `FetchProxy` /
   `fetch_proxy` or any `proxy=` keyword. Holds.
2. **Every other guard still applies.** Proxy mode changes only `_GuardedBackend.connect_tcp`
   (fetcher.py:290-291); everything above it (`check_url` on the request and every redirect,
   robots through the same backend, admission and pacing in `acquire_page`, the deadline via
   `_BoundedStream`, size limits, content type, manifest class, redaction) is unchanged code.
   `check_url` still refuses localhost, single-label, local suffixes, encoded forms and
   private or reserved literals before any connect (tested: no CONNECT line reaches the fake
   proxy). Holds.
3. **TLS.** `ssl.create_default_context(cafile=proxy.ca_file)` (fetcher.py ~332): verification
   and hostname checks stay on; the CA comes only from the given path; `fetch_proxy` refuses a
   missing bundle and the flags must come together. A wrong CA gives `tls_failed` (tested).
   Holds. (The session bundle exists, 123 certificates.)
4. **CONNECT.** The authority is httpcore's origin host and port, which come from the
   canonical `CheckedUrl` (lower-cased, normalised; `check_url` refuses any whitespace or
   control character, so no CR/LF can reach the request line). IPv6 is bracketed. Only a 2xx
   with nothing after its headers is accepted; the reply is bounded. A refusal is
   `connection_failed`, not transient, with no `http_status`, so a refused robots.txt is
   `robots_unreachable`, never "4xx allows all". The proxy URL is refused if it holds
   credentials, a path or a query, and `ProxyConfigError` messages never repeat it; nothing
   writes the proxy's host or port into a record or the tools' output. Checked as booleans
   only: the session's proxy URL has the accepted shape (http, a port, no userinfo), so the
   reported commands can work. Holds.
5. **Visible in evidence.** `route_fields` adds `via_proxy` / `address_checked` to the corpus
   record (page and Adzuna modes), the live role-research printed line and the accuracy read.
   Tested for corpus and role research. Holds (see M2 for a nuance).
6. **ADR amendment.** True about the address check and the scope. Overstates "every other
   guard" for TLS through a re-terminating proxy (I1).
7. **Tests against the local fake proxy.** Real sockets: a CONNECT-only fake proxy that
   tunnels to the test's own loopback servers, a real TLS server with throwaway CAs. They
   assert the CONNECT lines, the server's paths, the Host header, no lookup (a resolver that
   raises), robots refusal, redirect refusal before any tunnel, size limit, refusal mapping
   and TLS verification. Real behaviour, not mocks. Gaps are Minor (M3, M4).

### Strengths
- The worker's refusal is a typed `None` field, not an absence that `extra="ignore"` would
  swallow; pinned by the boundary test.
- Change confined to the network layer; no guard was duplicated or bypassed.
- The proxy's refusal is never taken for the site's status, which keeps robots fail-closed.
- `via_proxy` and `address_checked` are fields, so the missing check is stated, not inferred.
- Bad or half-given flags stop before the paid call in `live_role_research`.

### Issues

#### Critical
None.

#### Important
- **I1 (truth).** `docs/adr/0009-evidence-acquisition.md:673-679` (and the module docstring,
  `backend/src/careerwright/evidence/fetcher.py:24`). The amendment says the only thing given
  up is the resolved-address check and that "every other guard" still runs. But where the
  proxy re-terminates TLS (as the session proxy does; that is why it needs its own CA bundle,
  and the report's own concern names it), Careerwright verifies the proxy's certificate, not
  the site's. The check that the page really came from that site is then the proxy's, not
  Careerwright's. A security record that understates its trade cannot be trusted as written,
  and corpus evidence fetched this way rests on it. Fix: add to "What it gives up", in plain
  words: "Where the proxy decrypts and re-encrypts traffic, Careerwright checks the proxy's
  certificate, not the site's own; the proxy checks the site." Mirror it in the module
  docstring. No code change needed; optionally state it in `route_fields`' docstring too.

#### Minor (list)
- **M1 (list).** `backend/tools/corpus.py:233` with `fetcher=fetcher`: in proxy mode
  `--adzuna` sends the Adzuna app ID and key (in the request's query) through the proxy,
  which, if it re-terminates TLS, can read them. No worse than the Meta key, which already
  goes through the session proxy, and it is the only way Adzuna works in the cloud. Note it in
  the report's commands or the amendment so the controller chooses it knowingly. The report's
  ruling 4 ("live_adzuna reads an API, not pages") sits oddly beside `corpus --adzuna` taking
  the flags.
- **M2 (list).** `backend/tools/fetch_proxy.py:49-54`: `address_checked: true` describes the
  mode, not an event. A direct-mode record whose URL was refused before any connect, or a
  test stand-in that is not a `Fetcher`, still says `true`. Acceptable as a mode flag; say so
  in the docstring ("true: the fetcher checks each address it connects to").
- **M3 (list).** No test that the deadline holds during CONNECT (a proxy that accepts and
  never answers, or trickles its reply). The code bounds it through `_BoundedStream`; a test
  would guard ACQ-02 in this mode.
- **M4 (list).** `tools/accuracy_read.py` takes the flags and prints the fields, but no test
  covers either.
- **M5 (list).** `backend/src/careerwright/evidence/fetcher.py:300-312`: the reply bound is
  checked before each read, so a reply can reach about 16 KB before refusal, and a status
  like `2000` reads as `200`. Harmless; tidy if touched.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The safety design holds on every named risk: no product path can select the
mode, every guard above the socket still runs, TLS stays verified from the given bundle, and
evidence says `via_proxy`. One truth fix is needed before merge: the ADR amendment (and the
fetcher docstring) must say that through a re-terminating proxy the site's certificate is
checked by the proxy, not Careerwright.
