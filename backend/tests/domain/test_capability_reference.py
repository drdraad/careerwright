"""The capability reference (MAP1-07, MAP1-08, OUT1-11; ADR 0012): the rubrics, ESCO
crosswalks and gate types this module gives the option pack's pack-local rows, committed and
pinned, and the pack references the capability loader itself relies on (Task 7b M3)."""

import json
from typing import Any

import pytest

from careerwright.capability.reference import (
    CARRIED_TO,
    PINS,
    ReferenceError,
    carried_changes,
    check_reference,
    load_reference,
    parse_reference,
    reference_path,
)
from careerwright.catalogue.option_pack import load_pack, pack_path, parse_pack

PACK = "0.1.0"
REFERENCE = "0.1.0"


def committed() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(reference_path(REFERENCE).read_text(encoding="utf-8"))
    return data


@pytest.mark.req("MAP1-07", "MAP1-08", "OUT1-11")
def test_the_committed_reference_loads_against_its_pack_and_passes_its_checks() -> None:
    reference = load_reference(REFERENCE, load_pack(PACK))

    assert reference.pack_version == PACK
    assert reference.review_state == "proposed"
    assert check_reference(reference, load_pack(PACK)) == []


@pytest.mark.req("MAP1-08")
def test_every_pack_skill_row_has_one_rubric_with_five_behavioural_anchors() -> None:
    pack = load_pack(PACK)
    reference = load_reference(REFERENCE, pack)
    skill_rows = {s.skill_id for s in pack.skills if s.kind == "skill"}

    assert {r.skill_id for r in reference.rubrics} == skill_rows
    for rubric in reference.rubrics:
        assert sorted(rubric.anchors) == [0, 1, 2, 3, 4]
        assert all(text.strip() for text in rubric.anchors.values())
        assert 1 <= rubric.required_level <= 4
        assert rubric.version_id == f"{rubric.skill_id}@{rubric.version}"


@pytest.mark.req("MAP1-05")
def test_every_gate_word_in_the_pack_has_one_typed_gate() -> None:
    pack = load_pack(PACK)
    reference = load_reference(REFERENCE, pack)
    words = {q.gate for q in pack.skill_requirements if q.gate is not None}

    typed = {word: reference.gate_for_words(word) for word in words}

    assert all(gate is not None for gate in typed.values())
    kinds = {word: gate.kind for word, gate in typed.items() if gate is not None}
    assert kinds["statutory registration"] == "legal_practice"
    assert kinds["work rights"] == "eligibility"


@pytest.mark.req("MAP1-05")
def test_a_credential_row_is_a_gate_and_never_a_rubric_level() -> None:
    pack = load_pack(PACK)
    reference = load_reference(REFERENCE, pack)

    gate = reference.gate_for_row("pack:registered-nurse-manchester:nmc-registration")

    assert gate is not None
    assert gate.kind == "legal_practice"
    assert reference.rubric_for("pack:registered-nurse-manchester:nmc-registration") is None


def test_a_reference_whose_bytes_are_not_its_pin_is_refused(tmp_path: Any) -> None:
    pack = load_pack(PACK)
    with pytest.raises(ReferenceError, match="not its pinned bytes"):
        load_reference(REFERENCE, pack, pins={REFERENCE: "0" * 64})
    with pytest.raises(ReferenceError, match="no committed capability reference"):
        load_reference("9.9.9", pack)
    with pytest.raises(ReferenceError, match=r"written for option pack 0\.2\.0, not 0\.1\.0"):
        load_reference("0.2.0", pack)  # each version fits the pack it was written for
    assert set(PINS) == {REFERENCE, "0.2.0"}


@pytest.mark.req("MAP1-07", "OPTN-08")
def test_reference_0_2_0_is_carried_unchanged_to_the_school_leaver_pack_0_4_0() -> None:
    """Task 12b: pack 0.4.0 adds courses and funding only, so the reference 0.2.0 fits it as
    written: the same targets, skill rows, requirements and postings, every check passing."""
    pack = load_pack("0.4.0")
    reference = load_reference("0.2.0", pack)

    assert (reference.reference_version, reference.pack_version) == ("0.2.0", "0.2.0")
    assert check_reference(reference, pack) == []
    assert carried_changes(load_pack("0.2.0"), pack) == []
    assert CARRIED_TO["0.2.0"] == frozenset({"0.4.0"})  # 0.3.0 was never carried
    assert set(CARRIED_TO) == {"0.2.0"}
    with pytest.raises(ReferenceError, match=r"written for option pack 0\.2\.0, not 0\.3\.0"):
        load_reference("0.2.0", load_pack("0.3.0"))


@pytest.mark.req("MAP1-07")
def test_a_carried_reference_is_refused_where_the_later_pack_changes_its_capability_parts() -> None:
    later = load_pack("0.4.0")
    renamed = later.model_copy(
        update={
            "targets": [
                later.targets[0].model_copy(update={"title": "Another title"}),
                *later.targets[1:],
            ]
        }
    )

    assert carried_changes(load_pack("0.2.0"), renamed) == [
        "option pack 0.4.0 changes the targets of 0.2.0"
    ]


def test_a_rubric_missing_an_anchor_is_named() -> None:
    data = committed()
    del data["rubrics"][0]["anchors"]["3"]

    problems = check_reference(parse_reference(data), load_pack(PACK))

    assert any("anchors for levels 0 to 4" in p for p in problems)


def test_a_pack_row_without_a_rubric_or_a_gate_is_named() -> None:
    data = committed()
    data["rubrics"] = data["rubrics"][1:]

    problems = check_reference(parse_reference(data), load_pack(PACK))

    assert any("has no rubric" in p for p in problems)


def test_a_gate_word_with_no_typed_gate_is_named() -> None:
    data = committed()
    for gate in data["gates"]:
        gate["gate_words"] = [w for w in gate["gate_words"] if w != "work rights"]

    problems = check_reference(parse_reference(data), load_pack(PACK))

    assert any("'work rights'" in p for p in problems)


def test_a_target_crosswalk_to_a_non_pack_target_is_named() -> None:
    data = committed()
    data["targets"][0]["target_id"] = "no-such-target"

    problems = check_reference(parse_reference(data), load_pack(PACK))

    assert any("no-such-target" in p for p in problems)


@pytest.mark.req("OPTN-10")
def test_the_loader_checks_the_pack_references_it_relies_on() -> None:
    # Task 7b's validator does not check these fields; the capability loader reads them, so
    # it checks them itself (dispatch ruling 4).
    data = json.loads(pack_path(PACK).read_text(encoding="utf-8"))
    data["learning_options"][0]["target_ids"] = ["no-such-target"]
    data["skills"][0]["target_id"] = "no-such-target"
    data["skill_requirements"][0]["target_id"] = "registered-nurse-manchester"
    pack = parse_pack(data)

    problems = check_reference(load_reference(REFERENCE, load_pack(PACK)), pack)

    assert any("option:C01 names target no-such-target" in p for p in problems)
    assert any("names target no-such-target" in p and p.startswith("pack:") for p in problems)
    assert any("req:J01.1 is for registered-nurse-manchester" in p for p in problems)
