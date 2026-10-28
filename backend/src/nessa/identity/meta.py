"""The Meta Model API through Pydantic AI's native Meta provider (ADR 0003; adapter).

Nothing retries behind the DBOS step's back: the OpenAI client has `max_retries=0`, the agent
has no output retries and one request at most. Structured output is `NativeOutput` (strict
JSON schema), because Meta accepts no forced tool choice. The base URL is fixed: a key is
only ever sent to Meta.
"""

from typing import Literal

import httpx2
from openai import AsyncOpenAI
from pydantic import SecretStr
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.meta import MetaProvider

META_BASE_URL = "https://api.meta.ai/v1"
REQUEST_TIMEOUT_S = 120.0
ReasoningEffort = Literal["minimal", "low"]


def meta_model(
    model_id: str,
    api_key: SecretStr,
    *,
    max_output_tokens: int,
    effort: ReasoningEffort,
    http_client: httpx2.AsyncClient | None = None,
) -> Model:
    client = AsyncOpenAI(
        base_url=META_BASE_URL,
        api_key=api_key.get_secret_value(),
        max_retries=0,
        http_client=http_client or httpx2.AsyncClient(timeout=REQUEST_TIMEOUT_S),
    )
    return OpenAIResponsesModel(
        model_id,
        provider=MetaProvider(openai_client=client),
        settings=OpenAIResponsesModelSettings(
            max_tokens=max_output_tokens, openai_reasoning_effort=effort
        ),
    )
