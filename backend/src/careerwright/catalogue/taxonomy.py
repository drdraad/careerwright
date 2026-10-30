"""Taxonomy use cases: import the pinned release and search it (spec sections 4-5: TAX-1,
DIV1-01).

Retrieval is PostgreSQL English full-text search plus exact alias lookup over the full
release; no embedding service or taxonomy API is involved. Alias matches are returned
before full-text matches, and a label several occupations share returns all of them: the
ambiguity is the caller's to resolve, never silently decided here. A search without a
release, or without a searchable term, is an error, never an empty result.
"""

import re
import uuid
from dataclasses import dataclass

from careerwright.catalogue import taxonomy_store
from careerwright.catalogue.esco import TRANSFORMATION_VERSION, EscoCatalogue, normalise_label
from careerwright.catalogue.records import (
    LabelMatch,
    OccupationDetail,
    OccupationHit,
    TaxonomyRelease,
    TitleMatch,
)
from careerwright.catalogue.releases import ReleasePin
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage

MAX_QUERY = 200
MAX_LIMIT = 50


class TaxonomyMismatchError(RuntimeError):
    """A different release, or the same one built by another transformation, is already
    imported; changing it needs a reviewed migration."""


def is_held(held: TaxonomyRelease, pin: ReleasePin) -> bool:
    """The held import is exactly this release, built by this code's transformation (an
    older transformation's stored labels and search vectors would be stale)."""
    return (held.dataset_id, held.sha256, held.transformation_version) == (
        pin.dataset_id,
        pin.sha256,
        TRANSFORMATION_VERSION,
    )


def import_release(tx: Tx, catalogue: EscoCatalogue) -> str:
    """Setup only. Imports the release unless it is already held; refuses anything else."""
    taxonomy_store.lock_releases(tx)
    held = taxonomy_store.release(tx)
    if held is not None:
        if is_held(held, catalogue.pin):
            return "already imported"
        raise TaxonomyMismatchError(
            f"{held.dataset_id} (transformation {held.transformation_version}) is imported; "
            f"{catalogue.pin.dataset_id} (transformation {TRANSFORMATION_VERSION}) cannot "
            "replace it without a reviewed migration (docs/runbook.md)"
        )
    taxonomy_store.import_catalogue(tx, catalogue)
    return "imported"


def held_release(tx: Tx) -> TaxonomyRelease:
    found = taxonomy_store.release(tx)
    if found is None:
        raise CareerwrightError(
            ErrorCode.TAXONOMY_UNAVAILABLE,
            "The occupation taxonomy has not been imported. Run `make setup`, then start "
            "Careerwright.",
            stage=ErrorStage.CATALOGUE,
        )
    return found


@dataclass(frozen=True)
class OccupationSearch:
    release: TaxonomyRelease
    any_word: bool
    label_matches: list[LabelMatch]  # exact preferred, alternative or hidden label
    full_text: list[OccupationHit]  # ranked; excludes the label matches
    # Every other occupation the full-text query matches; None when it did not run (the
    # query has no searchable word but matched a label): not searched is never zero.
    full_text_total: int | None
    limit: int


def search_occupations(
    tx: Tx, query: str, limit: int, *, any_word: bool = False, titles: bool = True
) -> OccupationSearch:
    """`any_word=False` needs every word (web-search syntax); `True` ranks occupations by
    how many of the words they match, for broad task and interest queries. `titles=False`
    (discovery's task searches): a match on the words of an occupation's preferred or
    alternative labels alone is no match, so work is never found by a shared word in a
    title."""
    release = held_release(tx)
    text = query.strip()
    if not text or len(text) > MAX_QUERY or not 1 <= limit <= MAX_LIMIT:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            f"Search with 1-{MAX_QUERY} characters and a limit of 1-{MAX_LIMIT}.",
            stage=ErrorStage.CATALOGUE,
            details={"field": "q", "reason": "length"},
        )
    labels = taxonomy_store.label_matches(tx, normalise_label(text))
    if taxonomy_store.search_terms(tx, text) == 0:
        if labels:
            return OccupationSearch(release, any_word, labels, [], None, limit)
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "The search has no searchable words (only common words or punctuation).",
            stage=ErrorStage.CATALOGUE,
            details={"field": "q", "reason": "no_search_terms"},
        )
    hits, total = taxonomy_store.full_text(
        tx, text, limit, any_word=any_word, exclude={m.concept_id for m in labels}, titles=titles
    )
    return OccupationSearch(release, any_word, labels, hits, total, limit)


TITLE_LIMIT = 20
_WORD = re.compile(r"[^\W_]+")


@dataclass(frozen=True)
class TitleMatches:
    release: TaxonomyRelease
    query: str
    matches: list[TitleMatch]
    total: int  # every occupation that matches, of which `matches` are the best
    limit: int


def match_titles(tx: Tx, typed: str, limit: int) -> TitleMatches:
    """The type-ahead for "What do you do now, or what did you do last?": occupations whose
    preferred or alternative labels have a word beginning with each word typed, best first.
    Deterministic and offline (no model, no key). Nothing matching is an honest empty
    answer, never an invented match; a query with no letter or digit is refused."""
    release = held_release(tx)
    text = " ".join(typed.split())
    words = list(dict.fromkeys(_WORD.findall(text.casefold())))
    if len(text) > MAX_QUERY or not 1 <= limit <= TITLE_LIMIT:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            f"Type at most {MAX_QUERY} characters, with a limit of 1-{TITLE_LIMIT}.",
            stage=ErrorStage.CATALOGUE,
            details={"field": "q", "reason": "length"},
        )
    if not words:
        raise CareerwrightError(
            ErrorCode.VALIDATION_FAILED,
            "Type a word of the job title.",
            stage=ErrorStage.CATALOGUE,
            details={"field": "q", "reason": "no_search_terms"},
        )
    matches, total = taxonomy_store.title_matches(tx, words, normalise_label(text), limit)
    return TitleMatches(release, text, matches, total, limit)


def occupation_detail(tx: Tx, concept_id: uuid.UUID) -> OccupationDetail:
    held_release(tx)
    found = taxonomy_store.occupation(tx, concept_id)
    if found is None:
        raise CareerwrightError(
            ErrorCode.NOT_FOUND, "No such ESCO occupation.", stage=ErrorStage.CATALOGUE
        )
    return found
