"""The connection check: the first model run a workspace can make (spec section 16: check
availability at key setup).

It sends a fixed synthetic prompt and no workspace data, so it proves the key, the
entitlement to the pinned model and schema-validated output without exposing anyone's
profile. Its worst case is bounded by the call limits below, which the spend reservation
uses.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, field_validator

from careerwright.identity.model_registry import worst_case_cost_nano_usd

MAX_TEXT = 400


class ConnectionCheckResult(BaseModel):
    """What the model proposes for the synthetic persona. Structurally valid is not true.

    Lengths are checked by a validator rather than schema keywords, so the JSON schema sent
    to Meta stays within strict mode (Meta then enforces the structure itself)."""

    model_config = ConfigDict(extra="forbid")

    suggested_title: str
    reason: str

    @field_validator("suggested_title", "reason")
    @classmethod
    def _bounded(cls, value: str) -> str:
        if not 1 <= len(value.strip()) <= MAX_TEXT:
            raise ValueError(f"must be 1-{MAX_TEXT} characters")
        return value.strip()


@dataclass(frozen=True)
class CallLimits:
    max_input_tokens: int
    max_output_tokens: int
    max_web_searches: int


LIMITS = CallLimits(max_input_tokens=4_000, max_output_tokens=2_048, max_web_searches=0)
INSTRUCTIONS = "Answer only with the requested JSON. Keep every string short."
PROMPT = (
    "Synthetic test persona (not a real person): a warehouse shift supervisor in Leeds who "
    "enjoys training new starters and solving rota problems. Suggest one adjacent career "
    "and give a one-sentence reason."
)


def worst_case_nano_usd(model_id: str) -> int:
    return worst_case_cost_nano_usd(
        model_id,
        max_input_tokens=LIMITS.max_input_tokens,
        max_output_tokens=LIMITS.max_output_tokens,
        max_web_searches=LIMITS.max_web_searches,
    )
