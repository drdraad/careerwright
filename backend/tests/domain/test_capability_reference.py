"""The capability reference (MAP1-07, MAP1-08, OUT1-11; ADR 0012): the rubrics, ESCO
crosswalks and gate types this module gives the option pack's pack-local rows, committed and
pinned, and the pack references the capability loader itself relies on (Task 7b M3)."""

import json
from typing import Any

import pytest

from nessa.capability.reference import (
    PINS,
    ReferenceError,
    check_reference,
    load_reference,
    parse_reference,
    reference_path,
)
from nessa.catalogue.option_pack import load_pack, pack_path, parse_pack

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
    assert set(PINS) == {REFERENCE}


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
