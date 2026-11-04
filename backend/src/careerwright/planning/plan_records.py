"""The immutable facts saved when a person chooses a computed route."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careerwright.planning.comparison import RouteDetail
from careerwright.planning.search import InstanceSize, M0SearchLimits, SearchCoverage, StopReason


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ChoosePlan(StrictModel):
    expected_version: int = Field(ge=0)
    solve_run_id: uuid.UUID
    schedule_index: int = Field(ge=0)
    assumptions_confirmed: Literal[True] = Field(
        description="The person reviewed the route's consequential assumptions. "
        "This does not apply, enrol or resign."
    )
    full_horizon_accounting_acknowledged: bool = Field(
        default=False,
        description="Required when completed steps exist: this solve has not recalculated "
        "sunk costs.",
    )


class PlanSource(StrictModel):
    solve_run_id: uuid.UUID
    solve_id: str
    schedule_index: int
    profile_version: int
    inputs_version: int
    capability_version: int
    input_version: str
    matrix_version: str
    definition_version: str
    algorithm_version: str
    pruning_version: str


class PlanSearch(StrictModel):
    coverage: SearchCoverage
    stop_reason: StopReason | None
    instance: InstanceSize
    limits: M0SearchLimits


class PlanEvent(StrictModel):
    key: str
    kind: Literal["start", "finish", "application_deadline", "review"]
    variant_id: str
    title: str
    on: date
    conditional: bool
    proposed: Literal[True] = True


class ProgressUpdate(StrictModel):
    """A user's action report or pause; dates never rewrite the route's modelled timetable."""

    expected_version: int = Field(ge=1)
    kind: Literal[
        "step_completed",
        "step_retracted",
        "commitment_accepted",
        "commitment_retracted",
        "rest",
        "resume",
        "review_rescheduled",
    ]
    variant_id: str | None = None
    until: date | None = None

    @model_validator(mode="after")
    def matching_fields(self) -> "ProgressUpdate":
        if (self.variant_id is not None) != (
            self.kind
            in (
                "step_completed",
                "step_retracted",
                "commitment_accepted",
                "commitment_retracted",
            )
        ):
            raise ValueError("step and commitment reports need their variant ID")
        if (self.until is not None) != (self.kind in ("rest", "review_rescheduled")):
            raise ValueError("rest and review dates need an until date")
        return self


class PlanActivity(StrictModel):
    kind: Literal[
        "step_completed",
        "step_retracted",
        "commitment_accepted",
        "commitment_retracted",
        "rest",
        "resume",
        "review_rescheduled",
    ]
    variant_id: str | None
    until: date | None
    recorded_at: datetime
    step_title: str | None = Field(
        default=None,
        description="The step's title when this report was made; null for earlier records.",
    )


class PlanProgress(StrictModel):
    """Planning activity is self-reported, never new skill or credential evidence."""

    completed_steps: list[str] = Field(default_factory=list)
    rest_until: date | None = None
    review_on: date | None = None
    activity: list[PlanActivity] = Field(default_factory=list)


class PlanSnapshot(StrictModel):
    plan_id: uuid.UUID
    version: int = Field(ge=1)
    workspace_id: uuid.UUID
    selected_at: datetime
    selected_by: uuid.UUID
    assumptions_confirmed: Literal[True] = True
    commitments: list[str] = Field(
        default_factory=list,
        description="Accepted commitments on unchanged current steps; prior reports remain "
        "in activity.",
    )
    target_title: str
    source: PlanSource
    search: PlanSearch
    route: RouteDetail
    events: list[PlanEvent]
    next_action: PlanEvent | None
    progress: PlanProgress = Field(default_factory=PlanProgress)


def review_event(progress: PlanProgress) -> PlanEvent | None:
    if progress.review_on is None:
        return None
    return PlanEvent(
        key="plan:review",
        kind="review",
        variant_id="plan:review",
        title="this plan",
        on=progress.review_on,
        conditional=False,
    )


def events_for(route: RouteDetail) -> list[PlanEvent]:
    """Only actual dates become events. A model month alone is never an appointment."""
    gated = {gate.variant_id for gate in route.gates}
    found: list[PlanEvent] = []
    for step in route.steps:
        title = step.title or step.concept_id
        for kind, on in (
            ("application_deadline", step.application_deadline),
            ("start", step.start_date),
            ("finish", step.finish_date),
        ):
            if on is not None:
                found.append(
                    PlanEvent(
                        key=f"{step.variant_id}:{kind}",
                        kind=kind,
                        variant_id=step.variant_id,
                        title=title,
                        on=on,
                        conditional=step.variant_id in gated,
                    )
                )
    return sorted(found, key=lambda event: (event.on, event.key))
