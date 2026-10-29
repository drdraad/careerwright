# Live Meta usage log

Every HTTP call to the Meta Model API made by Nessa tooling, including failures and
free calls (ruling R5), and every Adzuna API request of `make live-adzuna` (scope
`live-adzuna`, free tier, model column `adzuna-jobs-api`). Generated from
`live-usage.jsonl` by `backend/tools/usage_ledger.py`; do not edit the table by
hand.

- Prices: https://dev.meta.ai/docs/pricing-rate-limits (checked 2026-10-27); costs are estimates from
  reported usage, in USD before tax. `unknown` means the charge could not be
  determined; the budget then counts the call's full reservation.
- `In` includes cached tokens; `Out` includes reasoning tokens (Meta usage
  semantics).
- `Searches` is Pydantic AI's billed count: Meta's `tool_usage` count if present,
  else `search` actions. Whether Meta reports `tool_usage` for search calls was not
  captured, and Meta does not document whether other actions (`open_page`,
  `find_in_page`) are billed. An upper bound adds $0.0025 per uncounted
  `web_search_call` item (calls 5 and 7: one each; see the JSONL `notes`). Rows 3-5
  predate raw-usage and action-type capture in the tool; their request path was
  otherwise the same.
- Remaining credit: not exposed by any documented Meta API endpoint; check the
  developer dashboard.
- Budgets: `task-1-sprint-0` (Sprint 0 spike): at most 15 calls, 5 on the production
  model, $0.30 worst case. `live-smoke` (`make live-smoke`): each invocation at most
  3 calls (a connection check) or 2 (`INTERVIEW=1`: one interview attempt and at
  most one validation repair), none on the production model unless
  `PRODUCTION=1`, and a worst-case cost cap; cumulatively at most 9 calls, 3 on the
  production model and $0.30 worst case (unknown costs count their full
  reservation; `NESSA_LIVE_SMOKE_*` changes them). Both are enforced in
  `backend/tools/live_smoke.py` before the stack starts. `live-eval` (`make
  live-eval`): at most 6 evaluation cases per invocation, each one attempt of at
  most 2 requests on the test model, never the production model; cumulatively at
  most 24 requests and $0.05 worst case (`NESSA_LIVE_EVAL_*`), enforced in
  `backend/tools/live_eval.py`. `live-adzuna` (`make live-adzuna`, Task 7A):
  Adzuna's free tier, not Meta: at most 2 requests per invocation and 10
  cumulatively, each at $0, enforced in `backend/tools/live_adzuna.py`; the
  endpoint is recorded without the credentials.
- A row for an activity attempt that sent more than one request (the call and its
  validation repair) shows `x N` after the endpoint; its tokens and cost are the
  attempt's total, and the caps count every request.

| # | UTC time | Scope | Purpose | Model | Endpoint | Outcome | In (cached) | Out (reasoning) | Searches | Est. cost | Running total | Response ID |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-10-27 22:18:51 | task-1-sprint-0 | invalid key fails visibly | `muse-spark-1.3-contributor` | POST /v1/responses | failed (401 invalid_api_key) | - (-) | - (-) | - | $0.000000 | $0.000000 | - |
| 2 | 2026-10-27 22:19:06 | task-1-sprint-0 | list entitled models | `(none)` | GET /v1/models | ok | - (-) | - (-) | - | $0.000000 | $0.000000 | - |
| 3 | 2026-10-27 22:19:23 | task-1-sprint-0 | schema output | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 157 (0) | 254 (208) | 0 | $0.000067 | $0.000067 | resp_6ae1236785b9eea8d283407f |
| 4 | 2026-10-27 22:19:32 | task-1-sprint-0 | schema output + streaming | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 157 (0) | 194 (137) | 0 | $0.000055 | $0.000121 | resp_6ae1236ef16e9f605f1a45f1 |
| 5 | 2026-10-27 22:19:47 | task-1-sprint-0 | schema output + web search | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 9,993 (1,107) | 737 (488) | 1 | $0.003538 | $0.003659 | resp_6ae123773c50371abe684266 |
| 6 | 2026-10-27 22:21:31 | task-1-sprint-0 | schema output | `muse-spark-1.3` (production) | POST /v1/responses | ok | 157 (0) | 145 (89) | 0 | $0.000813 | $0.004472 | resp_6ae123e7859dcc32766745d5 |
| 7 | 2026-10-27 22:21:48 | task-1-sprint-0 | schema output + streaming + web search | `muse-spark-1.3` (production) | POST /v1/responses | ok | 9,434 (1,107) | 482 (250) | 1 | $0.015123 | $0.019595 | resp_6ae123f50b40ed475967493f |
| 8 | 2026-10-27 22:34:15 | task-1-sprint-0 | schema output inside DBOS activity (key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 131 (0) | 158 (124) | 0 | $0.000045 | $0.019640 | resp_6ae126e3b80ecd1fcda54d10 |
| 9 | 2026-10-27 22:34:15 | task-1-sprint-0 | invalid key inside DBOS activity | `muse-spark-1.3-contributor` | POST /v1/responses | failed (401 provider_authentication) | - (-) | - (-) | - | $0.000000 | $0.019640 | - |
| 10 | 2026-10-27 22:34:58 | task-1-sprint-0 | schema output inside DBOS activity (key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 133 (0) | 120 (83) | 0 | $0.000037 | $0.019677 | resp_6ae1270e13a2fda9d2124b7d |
| 11 | 2026-10-27 22:34:58 | task-1-sprint-0 | invalid key inside DBOS activity | `muse-spark-1.3-contributor` | POST /v1/responses | failed (401 provider_authentication) | - (-) | - (-) | - | $0.000000 | $0.019677 | - |
| 12 | 2026-10-28 02:26:04 | live-smoke | connection check via API, outbox and DBOS worker (key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 114 (0) | 93 (62) | 0 | $0.000030 | $0.019707 | resp_6ae15d3804014aecb04a4853 |
| 13 | 2026-10-28 09:04:55 | live-smoke | interview turn via API, outbox and DBOS worker; proposals confirmed into the profile (synthetic message; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,128 (0) | 693 (323) | 0 | $0.000251 | $0.019958 | resp_6ae1bab2516734dafa354c6b |
| 14 | 2026-10-28 10:34:03 | live-smoke | interview turn via API, outbox and DBOS worker; proposals confirmed into the profile (synthetic message; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,147 (0) | 632 (255) | 0 | $0.000241 | $0.020200 | resp_6ae1cf90584e6f20314c4422 |
| 15 | 2026-10-28 12:26:28 | live-eval | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses x 2 | ok | 3,705 (1,393) | 1,125 (495) | 0 | $0.000459 | $0.020659 | resp_6ae1e9a3ebdaec9a49544558 |
| 16 | 2026-10-28 12:26:28 | live-eval | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,416 (1,137) | 413 (188) | 0 | $0.000113 | $0.020771 | resp_6ae1e9a73df4dc5972e047ef |
| 17 | 2026-10-28 12:26:28 | live-eval | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,419 (0) | 635 (443) | 0 | $0.000269 | $0.021040 | resp_6ae1e9d378252cd4d68c40ac |
| 18 | 2026-10-28 12:26:28 | live-eval | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,430 (0) | 589 (300) | 0 | $0.000261 | $0.021301 | resp_6ae1e9db3deba61886444cd1 |
| 19 | 2026-10-28 12:26:28 | live-eval | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,430 (0) | 819 (585) | 0 | $0.000307 | $0.021608 | resp_6ae1e9e12792daf1955f452e |
| 20 | 2026-10-28 12:26:28 | live-eval | live evaluation: one discovery case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 530 (0) | 568 (361) | 0 | $0.000167 | $0.021774 | resp_6ae1e9ee105f7f0e75e5494e |
| 21 | 2026-10-28 14:08:04 | live-eval-fix1 | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses x 2 | ok | 3,801 (0) | 1,135 (635) | 0 | $0.000607 | $0.022381 | resp_6ae201a7cbf9975ef89849c4 |
| 22 | 2026-10-28 14:08:04 | live-eval-fix1 | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,428 (0) | 457 (262) | 0 | $0.000234 | $0.022616 | resp_6ae201abe6b24c64e27244b4 |
| 23 | 2026-10-28 14:08:04 | live-eval-fix1 | live evaluation: one interview case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 1,431 (0) | 803 (626) | 0 | $0.000304 | $0.022919 | resp_6ae201b1672c6d4673ed41ea |
| 24 | 2026-10-28 14:08:04 | live-eval-fix1 | live evaluation: one discovery case via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 530 (0) | 629 (382) | 0 | $0.000179 | $0.023098 | resp_6ae201bf43e4d022e31445a3 |
| 25 | 2026-10-28 18:54:26 | live-eval-6b | live evaluation: one discovery and its slate's written explanation via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 530 (0) | 761 (524) | 0 | $0.000205 | $0.023303 | resp_6ae244cee5ec84de50944024 |
| 26 | 2026-10-28 18:54:26 | live-eval-6b | live evaluation: one discovery and its slate's written explanation via API and DBOS worker (synthetic case; key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses x 2 | ok | 2,747 (881) | 1,323 (359) | 0 | $0.000453 | $0.023756 | resp_6ae244dd7a9ec3f7584344ad |
| 27 | 2026-10-29 00:10:16 | live-search | source search via API, outbox and DBOS worker: Meta web search for a synthetic target and city, candidates checked (key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 4,800 (0) | 411 (258) | 2 | $0.005562 | $0.029319 | resp_6ae28edf74bd96b650df49d5 |
| 28 | 2026-10-29 00:11:19 | live-search | source search via API, outbox and DBOS worker: Meta web search for a synthetic target and city, candidates checked (key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 5,100 (0) | 384 (171) | 2 | $0.005587 | $0.034905 | resp_6ae28f1cba3230844dcc4bce |
| 29 | 2026-10-29 02:15:42 | live-search | source search in process with max_tool_calls 1, to qualify that Meta keeps to the bound (synthetic target and city; the product's own task code and bound check) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 3,430 (0) | 909 (597) | 1 | $0.003025 | $0.037930 | resp_6ae2ac3f5f5a419b85b740c4 |
| 30 | 2026-10-29 02:16:30 | live-search | source search via API, outbox and DBOS worker: Meta web search for a synthetic target and city, candidates checked (key opened just in time) | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 9,053 (2,771) | 641 (204) | 1 | $0.003262 | $0.041192 | resp_6ae2ac70476e4a0a10bf49cf |
| 31 | 2026-10-29 03:58:04 | live-extract | page extraction in process of the synthetic fixture page's visible text (the product's own task code and check; never a real page); request 1 of 1 | `muse-spark-1.3-contributor` | POST /v1/responses | ok | 700 (0) | 460 (339) | - | $0.000162 | $0.041354 | resp_6ae2c4496a510afe52ed4d91 |
| 32 | 2026-10-29 06:46:35 | live-adzuna | Adzuna search page 1 through the acquisition adapter (free tier) | `adzuna-jobs-api` | GET https://api.adzuna.com/v1/api/jobs/gb/search/1?what=data+analyst&where=Manchester&results_per_page=20 | ok | - (-) | - (-) | - | $0.000000 | $0.041354 | - |
| 33 | 2026-10-29 06:46:37 | live-adzuna | Adzuna search page 2 through the acquisition adapter (free tier) | `adzuna-jobs-api` | GET https://api.adzuna.com/v1/api/jobs/gb/search/2?what=data+analyst&where=Manchester&results_per_page=20 | ok | - (-) | - (-) | - | $0.000000 | $0.041354 | - |
