"""One occupation's pay and AI evidence for a workspace, and the person's salary floor as the
rule pay is held to (ADR 0010; spec sections 4 and 5).

The evidence is reference data (`careerwright.catalogue.reference`); the workspace supplies only
the regions of the person's cities (ASHE is regional) and which assessment pack applies:
the synthetic fixture pack in the fixture workspace, the product pack everywhere else.
"""

import uuid

from careerwright.catalogue.ai_resilience import AssessmentPacks
from careerwright.catalogue.pay import MappingReviewPack, SalaryFloorRule
from careerwright.catalogue.reference import OccupationEvidence, occupation_evidence
from careerwright.db import Tx
from careerwright.identity.workspaces import visible_workspace
from careerwright.profile.commands import current_profile
from careerwright.profile.document import FieldState, ProfileDocument


def cities_of(document: ProfileDocument) -> list[str]:
    field = document.cities
    if field.state is not FieldState.PROVIDED or field.value is None:
        return []
    return [str(city) for city in field.value]


def salary_floor(document: ProfileDocument) -> SalaryFloorRule | None:
    """The confirmed floor (a hard constraint, H-11 item 4), gross per its period; None when
    the person gave none (unknown is never £0)."""
    field = document.minimum_salary
    if field.state is not FieldState.PROVIDED or field.value is None:
        return None
    return SalaryFloorRule(field.value.amount.minor_units, field.value.period.value)


def role_evidence(
    tx: Tx,
    workspace_id: uuid.UUID,
    concept_id: uuid.UUID,
    *,
    reviews: MappingReviewPack,
    packs: AssessmentPacks,
) -> OccupationEvidence:
    workspace = visible_workspace(tx, workspace_id)
    document = current_profile(tx, workspace_id).document
    pack = packs.for_workspace(fixture_workspace=workspace.fixture_key is not None)
    return occupation_evidence(tx, concept_id, cities_of(document), reviews, pack)
