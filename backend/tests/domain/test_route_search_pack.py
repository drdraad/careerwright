"""The route search on the reviewed option pack, version 0.2.0 (Task 7c; ADR 0011 decision 15),
for each of its four targets (OPT1-16). Each instance completes in-process far inside the M0
limits. With the person's own confirmations still to come (Task 12), every pack offering lacks
a date, a cost, a timetable or an entry confirmation the search needs, so each is set aside
with its reasons and the result is unresolved, never "no route" (R9: a proposed record stays
explorable, never an unqualified result)."""

import pytest

from careerwright.capability.matrix import build_matrix
from careerwright.capability.outcomes import pack_outcomes
from careerwright.capability.reference import load_reference
from careerwright.catalogue.option_pack import PINS, load_pack
from careerwright.planning.checker import FindingCode, FindingKind
from careerwright.planning.compiler import ReadinessBasis, compile_input
from careerwright.planning.pack import pack_catalogue
from careerwright.planning.search import (
    Coverage,
    M0SearchLimits,
    Outcome,
    SearchResult,
    search_routes,
)
from tests.support.planning import pack_person

VERSION = "0.2.0"
PACK = load_pack(VERSION)
REFERENCE = load_reference(VERSION, PACK)
OUTCOMES = pack_outcomes(PACK, REFERENCE)
# Each offering's own kind of reason, as the reviewed pack states it (ADR 0013 consequences).
EXPECTED = {
    "data-quality-analyst-manchester": {
        "offering:C01#full_time": FindingKind.UNRESOLVED,
        "offering:C01#part_time": FindingKind.UNRESOLVED,
        "offering:C04~instalments": FindingKind.UNRESOLVED,
        "offering:C04~pay-in-full": FindingKind.VIOLATION,  # £2,995 above P01's £1,500 caps
    },
    "it-support-technician-bristol": {
        "offering:C07": FindingKind.UNRESOLVED,
        "offering:C10": FindingKind.UNRESOLVED,
    },
    "registered-nurse-manchester": {
        "offering:C03": FindingKind.UNRESOLVED,
        "offering:C08": FindingKind.UNRESOLVED,
    },
    "bookkeeping-assistant-leeds": {
        "offering:C02": FindingKind.UNRESOLVED,
        "offering:C05": FindingKind.UNRESOLVED,
        "offering:C06": FindingKind.UNRESOLVED,
        "offering:C09": FindingKind.UNRESOLVED,
    },
}


def search(target_id: str) -> SearchResult:
    """The target's pack options for P01's figures, with nothing yet said about evidence."""
    target = next(t for t in PACK.targets if t.target_id == target_id)
    matrix = build_matrix(
        target.title,
        pack=PACK,
        reference=REFERENCE,
        pack_target=target,
        occupation=None,
        exemplars=0,
        synthetic=False,
    )
    basis = ReadinessBasis(
        matrix=matrix, evidence=[], statements=[], outcomes=OUTCOMES, evidence_version=1
    )
    catalogue = pack_catalogue(PACK, target_id)
    return search_routes(compile_input(pack_person(), catalogue, readiness=basis))


@pytest.mark.req("OPT1-16", "OPT1-07", "LIMITS-05")
@pytest.mark.parametrize("target_id", sorted(EXPECTED))
def test_each_reviewed_pack_target_completes_within_the_m0_limits_and_says_what_is_unknown(
    target_id: str,
) -> None:
    result = search(target_id)
    limits = M0SearchLimits()

    assert VERSION in PINS
    assert sorted(EXPECTED) == sorted(t.target_id for t in PACK.targets)
    assert result.label.name == f"nessa-england-option-pack {VERSION}"
    assert result.coverage is Coverage.COMPLETE
    assert result.expanded_states <= limits.max_states
    assert result.elapsed_ms < limits.wall_seconds * 1000
    assert result.instance.concepts <= 4
    assert result.instance.months == limits.max_months
    assert {s.variant_id: s.kind for s in result.set_aside} == EXPECTED[target_id]
    assert all(s.codes for s in result.set_aside)
    assert result.schedules == []
    assert result.outcome is Outcome.UNRESOLVED  # never "no route"
    # Only the empty route and each option alone were checked: no route can be feasible.
    assert result.expanded_states == 1 + result.instance.variants


@pytest.mark.req("OPT1-16")
def test_a_dated_free_pack_course_without_weekly_hours_waits_for_a_timetable() -> None:
    result = search("it-support-technician-bristol")
    [c07] = [s for s in result.set_aside if s.variant_id == "offering:C07"]

    # C07 runs from 16 November 2026 for 12 weeks and states a £0 fee, but no weekly hours.
    assert c07.codes == [FindingCode.WORKLOAD_UNKNOWN]
