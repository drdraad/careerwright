# ADR 0003: Meta model selection, test and production

- Status: **Provisional, needs product owner confirmation** (ruling R6). The data-use choice
  for the test model is a product decision.
- Date: 2026-10-27
- Requirements: spec section 16 (Current Meta choices, Privacy mode, Spend controls), ARC-1,
  ruling R5

## Context

The specification pins one approved Spark model for every M0 text task, uses Standard model
IDs for personal data, and forbids silently selecting Contributor mode. Ruling R5 (user
instruction, 2026-10-27) makes model choice configuration. A **test** model, the cheapest
Meta model with the needed capability, serves smoke, eval and confirmation runs. A
**production** model, the most performant qualified one, serves the real live-assisted path.
The production model runs only for minimal qualification calls.

What the key can see (`GET /v1/models`, ledger call 2): `muse-wonder-1.0`,
`muse-spark-1.3`, `muse-spark-1.3-contributor`, `muse-spark-1.2`,
`muse-spark-1.2-contributor`, `muse-spark-1.1`, `muse-image-1.0`,
`muse-voice-transcribe-1.0`, `sam-3.1`. Every `created` value is `0`, although the docs
describe it as a Unix timestamp. Seeing a model in the list does not prove it can be
called; the calls below do.

Published text-model prices per million tokens (https://dev.meta.ai/docs/pricing-rate-limits,
checked 2026-10-27; input / cached input / output):

| Model | Mode | Price | Rate limit | Restrictions |
|---|---|---|---|---|
| `muse-spark-1.3` | Standard | $1.25 / $0.15 / $4.25 | 3,000 RPM, 4M TPM | none observed |
| `muse-spark-1.3-contributor` | Contributor | $0.10 / $0.002 / $0.20 | 150 RPM, 3M TPM | Meta may train on prompts, files and responses; no `max` reasoning effort |
| `muse-spark-1.2` / `-1.2-contributor` | Standard / Contributor | as 1.3 / as 1.3-contributor | as above | previous version |
| `muse-spark-1.1` | Standard only | $1.25 / $0.15 / $4.25 | 3,000 RPM | original version |
| `muse-wonder-1.0` | Standard only | $4.00 / $0.20 / $20.00 | 3,000 RPM | Preview; M1 per spec; not available in South Korea |

Web search costs $2.50 per 1,000 queries on top of tokens. All Muse text models have a
1,048,576-token context. Meta's model page states no maximum output tokens or deprecation
dates.

The other models the key lists, from the same pricing page and https://dev.meta.ai/docs/models
(both checked 2026-10-27). None of them was called, so access is listed, not proven:

| Model | Input → output; capability | Published price | Published limits | Restrictions / not published |
|---|---|---|---|---|
| `muse-image-1.0` | text, image → image; generation and editing, with web search and code execution before rendering; Responses API, `/v1/images/generations`, `/v1/images/edits` | $0.01 per generated image, search included; failed or safety-removed images are not billed | 150 RPM | context and output limits not published; image generation is M1 per spec |
| `muse-voice-transcribe-1.0` | audio → text transcript; streaming diarization, endpointing, VAD, keyword biasing, 25 evaluated languages, turn-level timestamps; `wss://api.meta.ai/v1/asr/realtime`, `POST /v1/asr/transcribe` | $0.18 per hour of audio, metered in whole seconds rounded down; streaming costs the same | 256 concurrent streams and 16,000 streams per hour, shared; no RPM/TPM | no word-level timestamps, sound events or emotion detection; not in L0 scope |
| `sam-3.1` | text prompt, image, video → boxes and masks; `POST /v1/responses`, Files API for repeated clips | $2.50 per 1,000 images; $0.20 per 1,000 video frames, minimum 50 frames per video request | 3,000 RPM; no TPM | context limits not published; not in L0 scope |

## Decision

- **Production model: `muse-spark-1.3` (Standard).** Qualified with two live calls. Call 6:
  schema output plus usage reporting. Call 7: streaming, web search and schema output in
  one call. Standard mode excludes model-training use. Contributor mode cannot be configured
  as the production model: the API and worker refuse to start with one (since Task 3,
  `nessa.identity.model_choice.ModelChoice.configure`, using the mode recorded per model in
  `nessa.identity.model_registry`).
- **Test model: `muse-spark-1.3-contributor`.** It is the cheapest Meta model (12.5× cheaper
  input and 21× cheaper output than Standard) and the same Spark 1.3 release as production.
  It passed schema output (call 3), streaming schema output (call 4), web search with schema
  output (call 5), and the durable activity path (calls 8 and 10). Because Meta may train on
  Contributor traffic, the test model is allowed **only for synthetic or public inputs**.
  Since Task 3 this is enforced in code and in the database: a non-synthetic workspace's run
  is always pinned to the production model, the activity refuses a Contributor model for
  non-synthetic data, and a database CHECK rejects such a run row (ADR 0004 decision 9).
- **Not selected:** Muse Wonder (M1 in the specification; no escalation in L0), Spark 1.1 and
  1.2 (older, same price), and image, voice and segmentation models (out of L0 scope). No
  automatic model escalation or provider substitution.
- **Integration pattern (Pydantic AI 2.62.0).** `OpenAIResponsesModel` with
  `MetaProvider(openai_client=AsyncOpenAI(base_url="https://api.meta.ai/v1", max_retries=0))`.
  - Structured output uses `NativeOutput(...)`, which sends `text.format` as `json_schema`
    with `strict: true`. Tool-output mode is not used: Meta accepts only `tool_choice='auto'`,
    so a forced output tool cannot be guaranteed.
  - Search uses `capabilities=[NativeTool(WebSearchTool(...))]`. It must never use the
    `WebSearch` capability, whose local fallback would send queries to a non-Meta provider.
  - Smoke and qualification calls use `openai_reasoning_effort='minimal'`, or `'low'` with
    search, plus an explicit `max_tokens`.
- **Cost discipline.** Live calls run only through explicit commands, never in `make check`
  or `make acceptance`. The hard cap covers call count, production-model calls, and
  worst-case cost in integer nano-USD. A direct call (`live_spike.py`) is checked against the
  cap just before it is sent. The durable worker's calls (`live_run.py`) cannot be checked
  one by one from the CLI. They are pre-authorised as a batch before the worker starts: the
  worst case of every allowed attempt, plus the free invalid-key call. A call counts as a
  production call when its model ID is the configured production model, whatever flag
  selected it. So setting the test model to `muse-spark-1.3` still counts against the
  production cap. Every call, free or failed, is appended to
  `docs/evidence/live-usage.jsonl`. That includes worker attempts interrupted by a failure:
  they are written before the spike stack is removed, and the worst case is written if the
  attempt rows cannot be read. Since Task 3 the spike CLIs are retired; `make live-smoke`
  (`backend/tools/live_smoke.py`) is the explicit command. It caps each invocation in code
  before the stack starts (the run's three attempts, none on the production model unless
  `PRODUCTION=1`, worst case at most $0.10), drives the product path (key stored through the
  API, sealed, opened only in the worker's activity), ledgers every attempt in the smoke
  database even if the run fails, and the product's own spend reservation applies too.

## Observed behaviour and restrictions

- Invalid key: HTTP 401, `authentication_error`/`invalid_api_key`, message `Unauthorized`.
  Pydantic AI raises `ModelAuthenticationError`, a subclass of `ModelHTTPError`. The body did
  not echo any part of the key.
- Usage arrives on both non-streamed and streamed responses: `input_tokens` (cached
  included), `cached_tokens`, `output_tokens` and `reasoning_tokens` (counted within output).
  Pydantic AI's mapping matched Meta's raw `usage` object exactly (call 6).
- Search actions:
  - Call 7 (streamed) made one `search` and one `open_page` action.
  - Call 5 made two `web_search_call` items; their action types were not captured, because
    that call predates action recording. Pydantic AI counted one of them as a billed search.
  - Whether Meta reports a search count (`tool_usage`) is **unknown**. The only raw body
    captured was call 6, a non-search call, where it was absent. Raw bodies of the search
    calls were not captured: call 5 predates raw capture and call 7 was streamed.
  - Pydantic AI counts as billed either Meta's `tool_usage` count, when present, or the
    `search` actions (OpenAI's semantics). Meta does not document whether other actions are
    billed, so the task's cost upper bound adds $0.0025 for each uncounted
    `web_search_call` item (one in call 5 and one in call 7).
- Remaining credit is not exposed by any documented API endpoint. It is visible only in the
  developer dashboard.
- Search results are injected as input tokens: about 9,400–10,000 per search call against
  about 160 without search. Search dominates cost.

## Consequences

- The product owner must confirm, or reject, Contributor mode for synthetic-data testing.
  If rejected, set `NESSA_META_TEST_MODEL=muse-spark-1.3` (Standard, about 12–21× the cost).
  Every test call then counts against the production-call cap, because the cap follows the
  model ID. Budgets for later tasks must allow for that. Nothing else changes.
- Qualification covers only the tested versions and scope: Spark 1.3, Pydantic AI 2.62.0,
  `NativeOutput`, and the `low` search context. Refusal, truncation and timeout contract
  tests (spec section 16) remain for the Sprint 2 interview adapter.
- The model registry in the product (spec section 16) must store per model: exact ID,
  Standard/Contributor mode, price version, capabilities and evaluation status. This table
  is its first entry.
