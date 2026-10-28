"""Taxonomy use cases: import the pinned release and search it (spec sections 4-5: TAX-1,
DIV1-01).

Retrieval is PostgreSQL English full-text search plus exact alias lookup over the full
release; no embedding service or taxonomy API is involved. Alias matches are returned
before full-text matches, and a label several occupations share returns all of them: the
ambiguity is the caller's to resolve, never silently decided here. A search without a
release, or without a searchable term, is an error, never an empty result.
"""

import uuid
from dataclasses import dataclass

from nessa.catalogue import taxonomy_store
from nessa.catalogue.esco import EscoCatalogue, normalise_label
from nessa.catalogue.records import LabelMatch, OccupationDetail, OccupationHit, TaxonomyRelease
from nessa.db import Tx
from nessa.errors import ErrorCode, ErrorStage, NessaError

MAX_QUERY = 200
MAX_LIMIT = 50


class TaxonomyMismatchError(RuntimeError):
    """A different release is already imported; changing it needs a reviewed migration."""


def import_release(tx: Tx, catalogue: EscoCatalogue) -> str:
    """Setup only. Imports the release unless it is already held; refuses a different one."""
    taxonomy_store.lock_releases(tx)
    held = taxonomy_store.release(tx)
    if held is not None:
        if (held.dataset_id, held.sha256) == (catalogue.pin.dataset_id, catalogue.pin.sha256):
            return "already imported"
        raise TaxonomyMismatchError(
            f"{held.dataset_id} is imported; {catalogue.pin.dataset_id} cannot replace it"
        )
    taxonomy_store.import_catalogue(tx, catalogue)
    return "imported"


def held_release(tx: Tx) -> TaxonomyRelease:
    found = taxonomy_store.release(tx)
    if found is None:
        raise NessaError(
            ErrorCode.TAXONOMY_UNAVAILABLE,
            "The occupation taxonomy has not been imported. Run `make setup`, then start Nessa.",
            stage=ErrorStage.CATALOGUE,
        )
    return found


@dataclass(frozen=True)
class OccupationSearch:
    release: TaxonomyRelease
    any_word: bool
    label_matches: list[LabelMatch]  # exact preferred, alternative or hidden label
    full_text: list[OccupationHit]  # ranked; excludes the label matches
    full_text_total: int  # every other occupation the full-text query matches
    limit: int


def search_occupations(
    tx: Tx, query: str, limit: int, *, any_word: bool = False
) -> OccupationSearch:
    """`any_word=False` needs every word (web-search syntax); `True` ranks occupations by
    how many of the words they match, for broad task and interest queries."""
    release = held_release(tx)
    text = query.strip()
    if not text or len(text) > MAX_QUERY or not 1 <= limit <= MAX_LIMIT:
        raise NessaError(
            ErrorCode.VALIDATION_FAILED,
            f"Search with 1-{MAX_QUERY} characters and a limit of 1-{MAX_LIMIT}.",
            stage=ErrorStage.CATALOGUE,
            details={"field": "q", "reason": "length"},
        )
    labels = taxonomy_store.label_matches(tx, normalise_label(text))
    if taxonomy_store.search_terms(tx, text) == 0:
        if labels:
            return OccupationSearch(release, any_word, labels, [], 0, limit)
        raise NessaError(
            ErrorCode.VALIDATION_FAILED,
            "The search has no searchable words (only common words or punctuation).",
            stage=ErrorStage.CATALOGUE,
            details={"field": "q", "reason": "no_search_terms"},
        )
    hits, total = taxonomy_store.full_text(
        tx, text, limit, any_word=any_word, exclude={m.concept_id for m in labels}
    )
    return OccupationSearch(release, any_word, labels, hits, total, limit)


def occupation_detail(tx: Tx, concept_id: uuid.UUID) -> OccupationDetail:
    held_release(tx)
    found = taxonomy_store.occupation(tx, concept_id)
    if found is None:
        raise NessaError(
            ErrorCode.NOT_FOUND, "No such ESCO occupation.", stage=ErrorStage.CATALOGUE
        )
    return found
