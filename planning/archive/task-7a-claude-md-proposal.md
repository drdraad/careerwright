# Task 7A: proposed CLAUDE.md wording (consolidated by the controller)

This condenses the implementers' six rounds of proposals (`task-7a-report.md`). The detail
stays in ADR 0009; CLAUDE.md keeps only what a future agent could break without knowing it.

## 1. Commands: the live-calls bullet

Replace "Live Meta calls run only" with "Live calls run only", and replace "and `make
live-eval` (the representative evaluation cases, at most 6, test model only)." with:

> `make live-eval` (the representative evaluation cases, at most 6, test model only), `make
> live-smoke SEARCH=1` (one source search, scope `live-search`), `make live-extract` (one
> page extraction of the synthetic fixture page, scope `live-extract`) and `make
> live-adzuna` (two free-tier Adzuna requests, ledgered at $0).

## 2. Layout: after `nessa/catalogue` (...)

> `nessa/evidence` (acquisition: the guarded fetcher, the source manifest `sources.json`,
> pages, Adzuna, jobs, freshness, claims, model extraction), `nessa/acquisition.py` (the
> restricted acquisition worker: no database, master key or model key),

## 3. Secrets: replace the first sentence

> Secrets: `.env` holds `META_API_KEY` for the live commands only, and
> `ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY` for `make live-adzuna` and for `make setup`,
> which copies them into `NESSA_HOME/adzuna/` for the restricted acquisition worker alone;
> the product takes user keys through the API and seals them.

## 4. Invariants: a new bullet after "Unknown is never zero …"

> Evidence (ADR 0009): every fetch goes through `nessa.evidence.fetcher` (address, robots.txt,
> pacing and every redirect checked); a page's class comes from the manifest, never from the
> page; a body is kept only where the session 1 class permits. Third parties' emails, phone
> numbers and contact fields are removed before anything is hashed, sealed or sent to a
> model, and a body that still shows one is not kept. Apply links are https only. A blocked,
> failed or unread source is never "none found"; only an API's own empty answer is. Model
> extraction is the `page_extraction` run kind, started for at most five pages without
> structured data: the model only quotes, deterministic code approves values read from
> verified spans, and its input is erased when the run ends. Lock order: a run's cancellation
> lock first, then `lock_workspace_records`, then rows.
