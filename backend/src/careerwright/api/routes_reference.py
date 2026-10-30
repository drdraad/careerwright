"""An occupation's pay and AI evidence for a workspace (ADR 0010): reads only."""

import uuid

from fastapi import APIRouter

from careerwright.api.deps import CallerDep, Deps
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.api.reference_schemas import OccupationEvidenceOut
from careerwright.db import actor_transaction
from careerwright.profile.role_evidence import role_evidence

router = APIRouter(
    prefix="/v1/workspaces/{workspace_id}", responses=ERROR_RESPONSES, tags=["reference"]
)


@router.get(
    "/occupations/{concept_id}/evidence",
    response_model=OccupationEvidenceOut,
    operation_id="get_occupation_evidence",
)
def get_occupation_evidence(
    workspace_id: uuid.UUID, concept_id: uuid.UUID, caller: CallerDep, deps: Deps
) -> OccupationEvidenceOut:
    """The occupation's UK SOC 2020 candidates with ASHE for your cities' regions, its
    modelled pay (only through a reviewed mapping), its trend (unavailable from one
    snapshot), its AI exposure and observed use, and its AI Resilience Score (a reviewed
    range, or unscored), each with the release it comes from."""
    with actor_transaction(deps.engine, caller.actor.actor_id) as tx:
        evidence = role_evidence(
            tx,
            workspace_id,
            concept_id,
            reviews=deps.mapping_reviews,
            packs=deps.assessment_packs,
        )
        return OccupationEvidenceOut.of(evidence)
