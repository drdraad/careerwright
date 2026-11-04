"""The public, bounded option-research status and cost estimate."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from careerwright.api.schemas import ResponseModel, RunOut
from careerwright.evidence.option_research import OptionResearchCoverage, ResearchStatus
from careerwright.evidence.search import SearchEmptyReason
from careerwright.identity.model_registry import ModelMode
from careerwright.identity.spend import BudgetScope
from careerwright.planning.catalogue import Citation


class OptionResearchEstimateOut(ResponseModel):
    model_id: str
    model_mode: ModelMode
    search_maximum_nano_usd: int
    pages_maximum_nano_usd: int
    combined_maximum_nano_usd: int
    hard_maximum_nano_usd: int
    refused_scope: BudgetScope | None


class OptionResearchRecordOut(ResponseModel):
    record_id: uuid.UUID
    kind: Literal["course", "apprenticeship", "funding"]
    title: str
    source_url: str
    retrieved_on: datetime
    expires_on: datetime
    expired: bool
    review_state: Literal["proposed"] = "proposed"
    citations: dict[str, Citation] = Field(
        description="Each accepted field's source hash, verified offset and exact excerpt."
    )


class OptionResearchOut(ResponseModel):
    research_id: uuid.UUID
    target: str
    city: str
    status: ResearchStatus
    coverage: OptionResearchCoverage
    search: RunOut
    reading: RunOut | None
    candidates: int
    empty_reason: SearchEmptyReason | None
    pages_attempted: int
    pages_read: int
    pages_blocked: int
    pages_failed: int
    failure_reason: str | None
    records: list[OptionResearchRecordOut]
