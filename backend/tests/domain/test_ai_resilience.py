"""The AI Resilience Score's record model, publication checks and lower-bound filter (ADR
0010; AIR1-02, AIR1-03, AIR1-04, AIR1-05, AIR1-07, AIR1-10, AIR1-12). Every record here is
synthetic."""

import ast
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from nessa.catalogue import ai_resilience
from nessa.catalogue.ai_resilience import (
    MEANING,
    AssessmentOrigin,
    AssessmentPack,
    AssessmentRecord,
    AssessmentState,
    Band,
    Correction,
    FilterOutcome,
    PublicationFailure,
    RecordState,
    ResilienceFilter,
    UnscoredReason,
    assessment,
    check_pack,
    check_record,
    committed_packs,
    filter_outcome,
    publication_failures,
)
from tests.support.reference_data import DATA_ANALYST, DATA_QUALITY_SPECIALIST

DECISION = {
    "reviewer": "A. Reviewer (synthetic)",
    "role": "accountable reviewer",
    "decided_on": "2026-10-29",
    "outcome": "range",
    "reasons": "Synthetic decision for a test.",
    "assumptions": [],
}
EVIDENCE = [
    {
        "family": "task_exposure",
        "source_id": "ilo-genai-exposure-2025-wp140",
        "independence_group": "ilo",
        "measure": "synthetic",
        "bearing": "mixed",
    },
    {
        "family": "human_accountability",
        "source_id": "a regulator's statement (synthetic)",
        "independence_group": "regulator",
        "measure": "synthetic",
        "bearing": "protection",
    },
]


def record(**changes: Any) -> AssessmentRecord:
    values: dict[str, Any] = {
        "record_id": "r1",
        "esco_uri": DATA_ANALYST,
        "horizon_years": 5,
        "lower": 5,
        "upper": 8,
        "technological_scope": "generative AI tools as of 2026",
        "geographic_scope": "inherited from the occupation",
        "mapping_reviewed": True,
        "evidence": EVIDENCE,
        "contradictions": [],
        "physical_automation_coverage": "not assessed; stated",
        "method_version": ai_resilience.METHOD_VERSION,
        "origin": "reviewer_entry",
        "synthetic": True,
        "label": "Synthetic test record",
        "decision": DECISION,
    }
    values.update(changes)
    return AssessmentRecord.model_validate(values)


def pack(*records: AssessmentRecord, corrections: list[Correction] | None = None) -> AssessmentPack:
    return AssessmentPack(
        pack_version="test-1",
        dated=date(2026, 10, 29),
        method_version=ai_resilience.METHOD_VERSION,
        synthetic=True,
        records=list(records),
        corrections=corrections or [],
    )


@pytest.mark.req("AIR1-02")
def test_a_reviewed_complete_record_publishes() -> None:
    assert publication_failures(record()) == []
    assert check_record(record(), []).state is RecordState.PUBLISHED


@pytest.mark.req("AIR1-02", "AIR1-12")
@pytest.mark.parametrize(
    ("changes", "failure"),
    [
        ({"decision": None}, PublicationFailure.NO_REVIEWER_DECISION),
        ({"mapping_reviewed": False}, PublicationFailure.MAPPING_NOT_REVIEWED),
        ({"geographic_scope": " "}, PublicationFailure.SCOPE_NOT_STATED),
        ({"evidence": []}, PublicationFailure.NO_SUPPORTING_EVIDENCE),
        # Two families from one source are not independent corroboration.
        (
            {"evidence": [EVIDENCE[0], {**EVIDENCE[1], "independence_group": "ilo"}]},
            PublicationFailure.FEWER_THAN_TWO_INDEPENDENT_FAMILIES,
        ),
        # Two independent sources of one family are not two families.
        (
            {"evidence": [EVIDENCE[0], {**EVIDENCE[1], "family": "task_exposure"}]},
            PublicationFailure.FEWER_THAN_TWO_INDEPENDENT_FAMILIES,
        ),
        ({"contradictions": None}, PublicationFailure.CONTRADICTIONS_NOT_RECORDED),
        ({"physical_automation_coverage": None}, PublicationFailure.PHYSICAL_AUTOMATION_NOT_STATED),
        ({"lower": 8, "upper": 5}, PublicationFailure.RANGE_INVALID),
        ({"lower": None}, PublicationFailure.RANGE_INVALID),
        ({"lower": 6}, PublicationFailure.BOUND_WITHOUT_ANCHOR),  # inside the 5-6 band
        ({"reference_point": 7}, PublicationFailure.REFERENCE_POINT_NOT_IN_M0),
        ({"seniority": "junior"}, PublicationFailure.MODIFIER_NOT_IN_M0),
        ({"modifiers": ["London"]}, PublicationFailure.MODIFIER_NOT_IN_M0),
        ({"horizon_years": 10}, PublicationFailure.HORIZON_NOT_FIVE_YEARS),
        ({"method_version": "other"}, PublicationFailure.UNKNOWN_METHOD_VERSION),
        (
            {"evidence": [*EVIDENCE, {**EVIDENCE[0], "family": "observed_use",
                                      "independence_group": "aei", "observed": False,
                                      "bearing": "protection"}]},
            PublicationFailure.MISSING_USE_AS_PROTECTION,
        ),
        ({"label": None}, PublicationFailure.SYNTHETIC_NOT_LABELLED),
    ],
)  # fmt: skip
def test_a_record_missing_any_publication_condition_never_publishes(
    changes: dict[str, Any], failure: PublicationFailure
) -> None:
    checked = check_record(record(**changes), [])

    assert failure in checked.failures
    assert checked.state is RecordState.PROPOSED
    found = assessment(check_pack(pack(record(**changes))), DATA_ANALYST)
    assert found.state is AssessmentState.UNSCORED
    assert found.unscored_reason is UnscoredReason.NOT_PUBLISHABLE
    assert (found.lower, found.upper) == (None, None)


def test_a_documented_anchor_allows_an_integer_inside_a_band() -> None:
    anchored = record(lower=6, anchors=[{"value": 6, "description": "synthetic anchor"}])

    assert publication_failures(anchored) == []


@pytest.mark.req("AIR1-04")
def test_a_model_s_proposal_is_only_ever_a_proposal() -> None:
    proposal = record(origin=AssessmentOrigin.MODEL_PROPOSAL, decision=None)

    checked = check_record(proposal, [])
    assert checked.state is RecordState.PROPOSED
    assert PublicationFailure.NO_REVIEWER_DECISION in checked.failures
    # The record model is the only way in: no field lets a model mark itself reviewed.
    assert "published" not in AssessmentRecord.model_fields
    assert "state" not in AssessmentRecord.model_fields


@pytest.mark.req("AIR1-03")
def test_no_score_is_derived_from_evidence_in_code() -> None:
    # The assessment reads only a pack of reviewed records: the module imports none of the
    # evidence tables, so exposure, observed use or their absence cannot become a score.
    source = Path(ai_resilience.__file__).read_text(encoding="utf-8")
    imported = {
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not {m for m in imported if m.startswith("nessa.")}
    assert assessment(check_pack(pack()), DATA_ANALYST).state is AssessmentState.UNSCORED


@pytest.mark.req("AIR1-07")
def test_a_known_correction_invalidates_what_it_affects_at_once_and_withdrawal_holds() -> None:
    correction = Correction(
        correction_id="c1",
        noted_on=date(2026, 10, 29),
        description="Synthetic: the source was corrected.",
        affects_sources=["ilo-genai-exposure-2025-wp140"],
    )
    invalidated = check_pack(pack(record(), corrections=[correction]))
    withdrawn = check_pack(
        pack(record(withdrawal={"withdrawn_on": "2026-10-29", "reason": "Synthetic: misleading."}))
    )

    assert invalidated.records[0].state is RecordState.INVALIDATED
    assert invalidated.records[0].corrections == ("c1",)
    assert assessment(invalidated, DATA_ANALYST).unscored_reason is UnscoredReason.INVALIDATED
    assert assessment(withdrawn, DATA_ANALYST).unscored_reason is UnscoredReason.WITHDRAWN
    found = assessment(check_pack(pack(record())), DATA_ANALYST)
    assert (found.pack_version, found.pack_dated) == ("test-1", date(2026, 10, 29))


def test_a_reviewed_null_assessment_is_unscored_with_its_reason() -> None:
    null = record(lower=None, upper=None, decision={**DECISION, "outcome": "null"})

    found = assessment(check_pack(pack(null)), DATA_ANALYST)
    assert found.state is AssessmentState.PUBLISHED_NULL
    assert found.unscored_reason is UnscoredReason.REVIEWED_NULL


@pytest.mark.req("AIR1-05")
@pytest.mark.parametrize(
    ("lower_upper", "chosen", "outcome"),
    [
        ((5, 8), ResilienceFilter(), FilterOutcome.KEPT),
        ((5, 8), ResilienceFilter(minimum=5), FilterOutcome.KEPT),
        ((5, 8), ResilienceFilter(minimum=6), FilterOutcome.BELOW_MINIMUM),  # lower end decides
        (None, ResilienceFilter(minimum=0), FilterOutcome.UNSCORED_KEPT),  # never read as 0
        (None, ResilienceFilter(minimum=10), FilterOutcome.UNSCORED_KEPT),  # nor as 10
        (
            None,
            ResilienceFilter(minimum=3, include_unscored=False),
            FilterOutcome.UNSCORED_EXCLUDED,
        ),
    ],
)
def test_the_filter_reads_the_lower_end_and_keeps_unscored_roles_by_default(
    lower_upper: tuple[int, int] | None, chosen: ResilienceFilter, outcome: FilterOutcome
) -> None:
    records = [] if lower_upper is None else [record(lower=lower_upper[0], upper=lower_upper[1])]
    found = assessment(check_pack(pack(*records)), DATA_ANALYST)

    assert filter_outcome(found, chosen) is outcome


@pytest.mark.req("AIR1-10", "AIR1-12")
def test_the_score_s_words_and_bands_follow_the_rubric() -> None:
    assert "not a probability" in MEANING
    assert "pressure on demand for human work" in MEANING.casefold()
    assert "0 is not certain elimination" in MEANING
    assert "10 is not a guarantee" in MEANING
    assert [b.bounds for b in Band] == [(0, 2), (3, 4), (5, 6), (7, 8), (9, 10)]
    found = assessment(check_pack(pack(record())), DATA_ANALYST)
    assert found.bands == (Band.MIXED, Band.COMPARATIVELY_RESILIENT)


@pytest.mark.req("AIR1-02", "AIR1-07")
def test_the_committed_packs_hold_no_real_record_and_one_labelled_synthetic_one() -> None:
    packs = committed_packs()

    assert packs.product.records == ()  # no accountable reviewer exists (H-10)
    assert assessment(packs.product, DATA_QUALITY_SPECIALIST).unscored_reason is (
        UnscoredReason.NO_RECORD
    )
    [fixture] = packs.fixture.records
    assert fixture.state is RecordState.PUBLISHED
    assert fixture.record.synthetic
    assert "synthetic" in (fixture.record.label or "").casefold()
    assert packs.for_workspace(fixture_workspace=False) is packs.product
    mixed = {**pack(record()).model_dump(mode="json"), "synthetic": False}
    with pytest.raises(ValueError, match="synthetic"):
        AssessmentPack.model_validate(mixed)
