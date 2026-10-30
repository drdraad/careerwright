"""Reference data: the ESCO release, occupation search and detail, and the English cities.

Signed-in, invited callers only (the taxonomy is public data, but the API serves invited
accounts and nothing else). No workspace data is read or written here.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from careerwright.api.catalogue_schemas import (
    OccupationOut,
    OccupationSearchOut,
    PlaceList,
    PlaceOut,
    SearchMatch,
    TaxonomyReleaseOut,
)
from careerwright.api.deps import CallerDep, Deps
from careerwright.api.envelope import ERROR_RESPONSES
from careerwright.catalogue.places import ENGLISH_CITIES
from careerwright.catalogue.taxonomy import (
    MAX_LIMIT,
    MAX_QUERY,
    held_release,
    occupation_detail,
    search_occupations,
)
from careerwright.db import system_transaction

router = APIRouter(prefix="/v1", responses=ERROR_RESPONSES, tags=["taxonomy"])
DEFAULT_SEARCH_LIMIT = 20


@router.get("/taxonomy", response_model=TaxonomyReleaseOut, operation_id="get_taxonomy")
def get_taxonomy(caller: CallerDep, deps: Deps) -> TaxonomyReleaseOut:
    with system_transaction(deps.engine) as tx:
        return TaxonomyReleaseOut.of(held_release(tx))


@router.get(
    "/taxonomy/occupations", response_model=OccupationSearchOut, operation_id="search_occupations"
)
def search(
    caller: CallerDep,
    deps: Deps,
    q: Annotated[str, Query(min_length=1, max_length=MAX_QUERY)],
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_SEARCH_LIMIT,
    match: SearchMatch = SearchMatch.ALL,
) -> OccupationSearchOut:
    with system_transaction(deps.engine) as tx:
        found = search_occupations(tx, q, limit, any_word=match is SearchMatch.ANY)
        return OccupationSearchOut.of(found)


@router.get(
    "/taxonomy/occupations/{concept_id}",
    response_model=OccupationOut,
    operation_id="get_occupation",
)
def get_occupation(concept_id: uuid.UUID, caller: CallerDep, deps: Deps) -> OccupationOut:
    with system_transaction(deps.engine) as tx:
        detail = occupation_detail(tx, concept_id)
        return OccupationOut.of(detail, held_release(tx))


@router.get("/places", response_model=PlaceList, operation_id="list_places")
def list_places(caller: CallerDep) -> PlaceList:
    return PlaceList(items=[PlaceOut.of(place) for place in ENGLISH_CITIES])
