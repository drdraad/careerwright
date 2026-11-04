"""The demo personas retain their stated answers and their missingness."""

import hashlib
from pathlib import Path

from careerwright.profile.document import FieldState
from careerwright.seed import FIXTURE_PERSONAS, fixture_profile

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "m0"


def test_every_persona_has_a_distinct_cited_synthetic_profile() -> None:
    assert [persona.key for persona in FIXTURE_PERSONAS] == [
        "p01",
        "p02",
        "p03",
        "p04",
        "p05",
    ]
    assert len({persona.workspace_id for persona in FIXTURE_PERSONAS}) == 5
    for persona in FIXTURE_PERSONAS:
        profile = fixture_profile(FIXTURES, persona)
        assert profile.persona_locator == f"fixtures/m0/{persona.path}"
        assert (
            profile.persona_sha256
            == hashlib.sha256((FIXTURES / persona.path).read_bytes()).hexdigest()
        )
        assert profile.document.cities.state is FieldState.PROVIDED
        assert profile.document.cities.source_ref_id == persona.source_id
        assert profile.document.target_titles.source_ref_id == persona.source_id


def test_demo_answers_expose_distinct_usable_paths_without_inventing_missing_facts() -> None:
    p01, p02, p03, p04, p05 = (fixture_profile(FIXTURES, persona) for persona in FIXTURE_PERSONAS)
    assert p01.document.target_titles.value == ["Data quality analyst"]
    assert p01.planning_inputs is not None
    assert p01.planning_inputs.baseline is not None
    assert p01.planning_inputs.baseline.net_income.minor_units == 200000
    assert p01.planning_inputs.weekly_availability == 40

    assert p02.document.target_titles.value == []
    assert p02.document.weekly_study_hours.value == 12
    assert p02.document.enjoyed_tasks.value == ["repairing physical objects", "working outdoors"]
    assert p02.planning_inputs is None  # £0 is unconfirmed, not a confirmed baseline.

    assert p03.document.target_titles.value == ["IT support technician"]
    assert p03.document.monthly_payment_cap.value is not None
    assert p03.document.monthly_payment_cap.value.minor_units == 10000
    assert p03.planning_inputs is not None
    assert p03.planning_inputs.opening_cash is not None
    assert p03.planning_inputs.opening_cash.minor_units == 20000
    assert p03.planning_inputs.baseline is None

    assert p04.document.target_titles.value == ["Registered nurse"]
    assert p04.planning_inputs is None
    assert p05.document.target_titles.value == ["Bookkeeping assistant"]
    assert p05.planning_inputs is None
