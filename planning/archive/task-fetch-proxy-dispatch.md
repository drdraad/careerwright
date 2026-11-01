# The controller's fetching tools through the session proxy (worktree)

The product owner's yes (1 November 2026). In this cloud container the guarded fetcher can't
reach any page: it resolves names itself (`evidence/fetcher.py:188`, `socket.getaddrinfo`)
and connects directly to the checked public address (the address guard, ADR 0009), but the
container has no DNS and reaches the internet only through the session's HTTPS proxy
(`HTTPS_PROXY`, CA bundle `/root/.ccr/ca-bundle.crt`). Evidence: the controller's
`tools.corpus --batch` run of Task 7f's ten pages and the live role-research run, all
`robots_unreachable`.

## Your tree
Worktree `/home/user/careerwright-wt/proxy`, branch `wt-proxy`, from 185894d (`var` linked).
Beside you in the main tree: the Linux-stack task (compose, Dockerfiles, `tools/localenv.py`,
`tools/stack.py`, test infra): never touch those. Rebase onto
`claude/confident-ramanujan-ux3saw` at the end (R15).

## Read first
`/home/user/careerwright/planning/env-cloud.md`, `implementer-contract.md`, ADR 0009,
`careerwright/evidence/fetcher.py` and `addresses.py`, `careerwright/acquisition.py`,
`tools/corpus.py`, `tools/live_role_research.py`, `tools/live_smoke.py` (SEARCH, extract),
and their tests.

## Build: an explicit proxy mode, for the controller's tools only
1. **Opt-in, never default, never the product.** A fetcher option that sends each request
   through an explicit HTTPS proxy (CONNECT), with a CA bundle, chosen only by an explicit
   flag or argument on `tools.corpus` and the live tools that read pages
   (`live_role_research`; any other tool that reads pages). The restricted acquisition
   worker and every product path can't select it: test that the worker's settings refuse it
   and that the product's fetcher construction never passes it.
2. **Every other guard stays:** https only (except what already allows http), robots.txt
   checked through the same mode, pacing, every redirect checked (same rules), size and time
   limits, the source manifest's class, redaction. Host names are still refused when they are
   IP literals in private or reserved ranges, `localhost`, single-label or otherwise refused
   by the address rules that can be applied to a name. Record in ADR 0009 an amendment, in
   plain words: in proxy mode the proxy, not Careerwright, picks the address it connects to,
   so the resolved-address check doesn't run; it is for the controller's tools in an
   environment whose egress is an allowlisting proxy, never the product.
3. **The CA:** read from a path the flag gives (default none: proxy mode needs it); never
   disable TLS verification.
4. **Visible in evidence:** a page fetched in proxy mode says so in its corpus record and in
   the live tool's printed result (a field, not a sentence), so no evidence pretends the
   address check ran.
5. Tests offline: a fake proxy (local) proves requests go through CONNECT with the guard's
   checks; the product's worker refuses the mode. No real network in tests.

## Rules
`env -u ADZUNA_APPLICATION_ID -u ADZUNA_API_KEY make check` (Node 24 on PATH) after each
change. No web requests (the controller runs the real fetch after), no live calls, no
subagents, Edit/Write only, explicit pathspecs, never start Docker or run acceptance, never
read `.env` or print an environment value, never push. The register last. Commit messages end
with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Report
`/home/user/careerwright/planning/task-fetch-proxy-report.md` with the exact flags for the
controller's re-run of Task 7f's fetch and the live role-research run; reply with the short
contract and your head SHA.
