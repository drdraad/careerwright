# Fetch proxy mode: report

Status: DONE. Branch `wt-proxy` (worktree `/home/user/careerwright-wt/proxy`), rebased onto
`claude/confident-ramanujan-ux3saw` (d7c5ac7).

Commits:
- a05855f Proxy mode for the controller's page-reading tools: CONNECT through an explicit proxy, never the product
- 8c58dfc Register: ACQ-01 records the controller's proxy mode and its tests

## The controller's commands

Run from `backend/` in the cloud container. Pass the proxy as the shell's own variable, so
its value is never printed or pasted.

Task 7f's fetch, one slot per run (the plan's `slot`, `url` and `locate` entries;
`planning/task-7f-fetch-plan.json`):

```
cd /home/user/careerwright/backend && uv run --locked python -m tools.corpus \
  --slot F04 --url https://www.gov.uk/become-apprentice \
  --locate "pay for" --locate "training costs" --locate "do not have to pay" \
  --proxy "$HTTPS_PROXY" --proxy-ca /root/.ccr/ca-bundle.crt
```

Repeat per slot. Each record now carries `"via_proxy": true, "address_checked": false`.
Pacing holds within one process only: leave a host's rate limit between runs.
`www.gov.uk` is still on the blocked list in `env-cloud.md`. Until the product owner adds it,
expect `robots_unreachable` with the proxy's refusal behind it (see "A proxy's refusal" below).

The live role-research run (one paid test-model call, as before; only the page reads change):

```
cd /home/user/careerwright/backend && uv run --locked python -m tools.live_role_research \
  --proxy "$HTTPS_PROXY" --proxy-ca /root/.ccr/ca-bundle.crt
```

Add `--title "..."` for another synthetic title. `make live-role-research` does not pass the
flags (I left the Makefile alone, since the Linux-stack task works beside it), so run the module
directly. A bad or half-given flag stops before the paid call. The printed pages line has
`"via_proxy": true, "address_checked": false`.

The same flags work on `tools.corpus --adzuna` and `tools.accuracy_read`.

## What I built

- `backend/src/careerwright/evidence/fetcher.py`: `FetchProxy`, `fetch_proxy(url, ca_file)`
  (checked: `http://host:port` only, with no credentials, path or query; the CA bundle must be a
  file; error messages never repeat the URL), `Fetcher(proxy=...)` and `Fetcher.via_proxy`.
  In proxy mode, `_GuardedBackend` opens a CONNECT tunnel to `host:port` through the proxy.
  It looks no name up and records no address (`Fetched.address` is None). It accepts only a
  2xx reply with nothing after the headers. TLS uses `ssl.create_default_context(cafile=bundle)`,
  so verification stays on.
- Everything above the network layer is unchanged and still runs: the URL checks, every
  redirect, robots.txt (through the same tunnel), admission and pacing, size and time limits,
  content type and redaction.
- `backend/src/careerwright/acquisition.py`: `AcquisitionSettings.fetch_proxy: None` (alias
  `CAREERWRIGHT_FETCH_PROXY`). Any value fails validation, so the worker refuses to start
  rather than ignore it. `main()` still builds `Fetcher(user_agent=...)` with no proxy.
- `backend/tools/fetch_proxy.py`: the shared flags (`--proxy`, `--proxy-ca`; both or neither),
  `fetcher_from(args, parser)` and `route_fields(fetcher)`. The latter gives
  `{"via_proxy", "address_checked"}`.
- `tools/corpus.py` (both modes), `tools/live_role_research.py` and `tools/accuracy_read.py`
  take the flags and print the two fields.
- `docs/adr/0009-evidence-acquisition.md`: the 2026-11-01 amendment, in plain words.
- `docs/requirements-register.md`: the ACQ-01 row.
- Tests: `backend/tests/domain/test_fetch_proxy.py` (new), `tests/support/fake_proxy.py` (a
  local CONNECT-only fake proxy that answers 405 to anything else, like the session's),
  `tests/support/certificates.py` (a throwaway CA and leaf), plus additions to
  `tests/tools/test_corpus.py`, `tests/tools/test_live_role_research.py` and
  `tests/architecture/test_boundaries.py`.

## Rulings

1. **A proxy's refusal is `connection_failed`, not transient, with no `http_status`.** I added
   no new attempt reason: that would need a migration (the reasons are a database CHECK) and a
   regenerated client, for a mode the product never uses. A refused robots.txt is therefore
   `robots_unreachable`, never a 4xx that would allow everything. The reason for a refusal is
   in the proxy's status endpoint (`$HTTPS_PROXY/__agentproxy/status`).
2. **CONNECT for every target, http included.** The session proxy answers plain-HTTP
   forwarding with a 405.
3. **The worker's refusal is a field typed `None`.** The settings ignore unknown variables
   (`extra="ignore"`), so a setting that was merely absent would be silently ignored. The
   boundary test's list of worker settings now names `fetch_proxy`, with its type pinned to
   `None`.
4. **`tools.accuracy_read` takes the flags too.** It reads pages. `tools.live_adzuna` does not:
   it reads an API, not pages. (`tools.corpus --adzuna` does take them.)
5. **Two output fields, `via_proxy` and `address_checked`**, so the missing check is stated
   directly rather than left to be inferred.

## Checks

- RED: the new test module failed to collect without the source change (no `FetchProxy`).
  GREEN after: 34 passed.
- Focused: `pytest tests/domain/test_fetch_proxy.py tests/tools tests/domain/test_fetcher.py
  tests/domain/test_acquisition_endpoint.py tests/architecture`: all pass, apart from the known
  Adzuna environment test when the variables are set.
- `export PATH=/opt/node24/bin:$PATH; env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check`
  after the rebase: exit 0. Backend: ruff and mypy clean, 1,905 passed, 8 skipped. Web:
  client drift none, Biome, tsc, Vitest 468 passed.
- `make acceptance`: not run. The controller runs acceptance.
- No web requests, no live calls: every test uses loopback only. The fake proxy tunnels only to
  the test's own servers, and the role-research proxy test has the fake proxy refuse every host.

## Concerns

- In proxy mode, a site is only as safe as the proxy's allowlist. The URL checks still refuse
  private and local names and literals, but a public name that resolves privately is no longer
  caught by Careerwright. That is the amendment's stated trade, for the controller's tools only.
- The real fetch through the session proxy has not been tried (no web requests). The first
  real run will show whether the proxy's TLS re-termination verifies against
  `/root/.ccr/ca-bundle.crt` for each host. A `tls_failed` result would point there.

## Paths a reviewer can skim

None generated. The `tests/support/certificates.py` keys are made fresh for each test and
never stored.
