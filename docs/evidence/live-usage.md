# Live Meta usage log

Every HTTP call to the Meta Model API made by Nessa tooling, including failures and
free calls (ruling R5). Generated from `live-usage.jsonl` by
`backend/tools/usage_ledger.py`; do not edit the table by hand.

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
  `backend/tools/live_smoke.py` before the stack starts.
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
