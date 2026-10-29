"""Reference-data use cases: import the pinned datasets, and assemble one occupation's pay
and AI evidence (spec section 5; TAX-1, AIR-1; ADR 0010).

Each dataset is imported once, from its verified pinned file, in its own transaction, and
refused if another release of it is held (changing a release needs a reviewed migration,
as for ESCO). The ESCO to O*NET crosswalk is imported after ESCO and the O*NET tasks, so the
version bridge it records is counted against what is held.
"""

import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from nessa.catalogue import ai_evidence, ashe, reference_store, soc
from nessa.catalogue.ai_resilience import Assessment, CheckedPack, assessment
from nessa.catalogue.pay import (
    MappingReviewPack,
    ModelledPay,
    ModelledPayUnavailable,
    PayBenchmark,
    TrendReason,
    TrendState,
    UkSocMapping,
    modelled_pay,
    uk_soc_mapping,
)
from nessa.catalogue.places import resolve_city
from nessa.catalogue.reference_store import ObservedUse, ReferenceRelease
from nessa.catalogue.releases import ReleasePin
from nessa.db import Tx
from nessa.errors import ErrorCode, ErrorStage, NessaError


class ReferenceMismatchError(RuntimeError):
    """Another release of a dataset, or one built by another transformation, is held."""


@dataclass(frozen=True)
class Dataset:
    name: str  # `reference_releases.dataset`
    pin: ReleasePin
    transformation: str
    licence: str
    attribution: str
    load: Callable[[Tx, bytes, ReleasePin], tuple[int, dict[str, int]]]


def _ashe(tx: Tx, data: bytes, pin: ReleasePin) -> tuple[int, dict[str, int]]:
    release = ashe.parse_release(data, pin)
    reference_store.insert_ashe(tx, release)
    withheld = sum(1 for e in release.estimates if e.figures["median"] is None)
    return len(release.estimates), {"median_withheld": withheld}


def _soc(tx: Tx, data: bytes, pin: ReleasePin) -> tuple[int, dict[str, int]]:
    index = soc.parse_index(data, pin)
    reference_store.insert_soc_index(tx, index)
    return len(index.entries), {"unit_groups": len(index.unit_groups), "uncoded": index.uncoded}


def _ilo(tx: Tx, data: bytes, pin: ReleasePin) -> tuple[int, dict[str, int]]:
    exposures = ai_evidence.parse_ilo(data)
    reference_store.insert_ilo(tx, exposures)
    return len(exposures), {"tasks": sum(e.tasks for e in exposures)}


def _onet(tx: Tx, data: bytes, pin: ReleasePin) -> tuple[int, dict[str, int]]:
    tasks = ai_evidence.parse_onet_tasks(data)
    reference_store.insert_onet_tasks(tx, tasks)
    return len(tasks), {"occupations": len({t.onet_code for t in tasks})}


def _usage(tx: Tx, data: bytes, pin: ReleasePin) -> tuple[int, dict[str, int]]:
    usage = ai_evidence.parse_task_usage(data)
    reference_store.insert_task_usage(tx, usage)
    return len(usage), {}


def _crosswalk(tx: Tx, data: bytes, pin: ReleasePin) -> tuple[int, dict[str, int]]:
    rows = ai_evidence.parse_crosswalk(data)
    reference_store.insert_crosswalk(tx, rows)
    return len(rows), reference_store.crosswalk_bridge(tx)


# In import order: the crosswalk's bridge is counted against the O*NET tasks.
DATASETS = (
    Dataset(
        "ashe",
        ashe.ASHE_RELEASE,
        ashe.TRANSFORMATION_VERSION,
        ashe.LICENCE,
        ashe.ATTRIBUTION,
        _ashe,
    ),
    Dataset(
        "soc_index",
        soc.SOC_INDEX_RELEASE,
        soc.TRANSFORMATION_VERSION,
        soc.LICENCE,
        soc.ATTRIBUTION,
        _soc,
    ),
    Dataset(
        "ilo_exposure",
        ai_evidence.ILO_RELEASE,
        ai_evidence.TRANSFORMATION_VERSION,
        ai_evidence.ILO_LICENCE,
        ai_evidence.ILO_ATTRIBUTION,
        _ilo,
    ),
    Dataset(
        "onet_tasks",
        ai_evidence.ONET_TASKS_RELEASE,
        ai_evidence.TRANSFORMATION_VERSION,
        ai_evidence.ANTHROPIC_LICENCE,
        ai_evidence.ANTHROPIC_ATTRIBUTION,
        _onet,
    ),
    Dataset(
        "task_usage",
        ai_evidence.TASK_USAGE_RELEASE,
        ai_evidence.TRANSFORMATION_VERSION,
        ai_evidence.ANTHROPIC_LICENCE,
        ai_evidence.ANTHROPIC_ATTRIBUTION,
        _usage,
    ),
    Dataset(
        "crosswalk",
        ai_evidence.CROSSWALK_RELEASE,
        ai_evidence.TRANSFORMATION_VERSION,
        ai_evidence.CROSSWALK_LICENCE,
        ai_evidence.CROSSWALK_ATTRIBUTION,
        _crosswalk,
    ),
)


def is_held(held: ReferenceRelease, dataset: Dataset) -> bool:
    return (held.dataset_id, held.sha256, held.transformation_version) == (
        dataset.pin.dataset_id,
        dataset.pin.sha256,
        dataset.transformation,
    )


def import_dataset(tx: Tx, dataset: Dataset, data: bytes) -> str:
    """Setup only. `data` must already be verified against `dataset.pin`."""
    reference_store.lock(tx)
    held = reference_store.held(tx, dataset.name)
    if held is not None:
        if is_held(held, dataset):
            return "already imported"
        raise ReferenceMismatchError(
            f"{held.dataset_id} (transformation {held.transformation_version}) is imported; "
            f"{dataset.pin.dataset_id} (transformation {dataset.transformation}) cannot "
            "replace it without a reviewed migration (docs/runbook.md)"
        )
    records, counts = dataset.load(tx, data, dataset.pin)
    reference_store.insert_release(
        tx,
        dataset.name,
        dataset.pin,
        transformation=dataset.transformation,
        licence=dataset.licence,
        attribution=dataset.attribution,
        record_count=records,
        counts=counts,
    )
    return "imported"


def held_releases(tx: Tx) -> list[ReferenceRelease]:
    found = reference_store.releases(tx)
    if {r.dataset for r in found} != {d.name for d in DATASETS}:
        raise NessaError(
            ErrorCode.REFERENCE_DATA_UNAVAILABLE,
            "Pay and AI evidence have not been imported. Run `make setup`, then start Nessa.",
            stage=ErrorStage.CATALOGUE,
        )
    return found


def region_codes(cities: Iterable[str]) -> list[str]:
    """The ONS regions of the person's cities (ASHE is regional: never a city's pay)."""
    places = (resolve_city(city) for city in cities)
    return sorted({p.region_code for p in places if p is not None})


def mapping_of(
    tx: Tx, identity: reference_store.OccupationIdentity, reviews: MappingReviewPack
) -> UkSocMapping:
    return uk_soc_mapping(
        identity.isco_code,
        reference_store.soc_links(tx, identity.isco_code),
        reference_store.soc_title_matches(tx, identity.isco_code, identity.labels),
        reviews.review_of(identity.esco_uri),
    )


def modelled_pay_of(
    tx: Tx,
    concept_ids: Iterable[uuid.UUID],
    regions: list[str],
    reviews: MappingReviewPack,
) -> dict[uuid.UUID, ModelledPay | ModelledPayUnavailable]:
    """Each occupation's modelled pay for the regions, or why there is none. Only an
    occupation with a recorded review needs its mapping read."""
    identities = reference_store.occupation_identities(tx, concept_ids)
    found: dict[uuid.UUID, ModelledPay | ModelledPayUnavailable] = {}
    for concept, identity in identities.items():
        if reviews.review_of(identity.esco_uri) is None:
            found[concept] = ModelledPayUnavailable.NO_REVIEWED_MAPPING
            continue
        mapping = mapping_of(tx, identity, reviews)
        codes = [mapping.reviewed_soc_code] if mapping.reviewed_soc_code else []
        found[concept] = modelled_pay(
            mapping, regions, reference_store.ashe_benchmarks(tx, codes, regions)
        )
    return found


@dataclass(frozen=True)
class CandidateEvidence:
    soc_code: str
    title: str
    index_entries: int
    title_match: bool
    benchmarks: tuple[PayBenchmark, ...]  # ASHE for this unit group in the person's regions


@dataclass(frozen=True)
class OnetMatch:
    onet_code: str
    onet_title: str
    match_type: ai_evidence.MatchType
    observed: ObservedUse | None  # None: the release holds no task for this O*NET code


@dataclass(frozen=True)
class OccupationEvidence:
    identity: reference_store.OccupationIdentity
    regions: list[str]
    mapping: UkSocMapping
    candidates: tuple[CandidateEvidence, ...]
    modelled: ModelledPay | ModelledPayUnavailable
    trend: tuple[TrendState, TrendReason]
    ilo: ai_evidence.IloExposure | None  # None: the index does not score the ISCO group
    onet_matches: tuple[OnetMatch, ...]
    assessment: Assessment
    releases: list[ReferenceRelease]


def occupation_evidence(
    tx: Tx,
    concept_id: uuid.UUID,
    cities: Iterable[str],
    reviews: MappingReviewPack,
    pack: CheckedPack,
) -> OccupationEvidence:
    releases = held_releases(tx)
    identity = reference_store.occupation_identities(tx, [concept_id]).get(concept_id)
    if identity is None:
        raise NessaError(
            ErrorCode.NOT_FOUND, "No such ESCO occupation.", stage=ErrorStage.CATALOGUE
        )
    regions = region_codes(cities)
    mapping = mapping_of(tx, identity, reviews)
    benchmarks = reference_store.ashe_benchmarks(
        tx, [c.soc_code for c in mapping.candidates], regions
    )
    candidates = tuple(
        CandidateEvidence(
            c.soc_code,
            c.title,
            c.index_entries,
            c.title_match,
            tuple(b for b in benchmarks if b.soc_code == c.soc_code),
        )
        for c in mapping.candidates
    )
    matches = reference_store.crosswalk_matches(tx, identity.esco_uri)
    used = reference_store.observed_use(tx, [m.onet_code for m in matches])
    return OccupationEvidence(
        identity=identity,
        regions=regions,
        mapping=mapping,
        candidates=candidates,
        modelled=modelled_pay(mapping, regions, benchmarks),
        trend=(TrendState.UNAVAILABLE, TrendReason.SINGLE_SNAPSHOT),
        ilo=reference_store.ilo_exposure(tx, identity.isco_code),
        onet_matches=tuple(
            OnetMatch(m.onet_code, m.onet_title, m.match_type, used.get(m.onet_code))
            for m in matches
        ),
        assessment=assessment(pack, identity.esco_uri),
        releases=releases,
    )
