"""The pinned ESCO release: integrity before parsing, structure checks, stable concept IDs
(TAX1-01, TAX1-04). Runs on the committed sample; the full release is imported in
acceptance (`tests/integration/test_taxonomy.py`)."""

import csv
import io
import zipfile
from pathlib import Path

import pytest

from nessa.catalogue.esco import (
    LabelKind,
    ReleaseIntegrityError,
    concept_id,
    normalise_label,
    parse_release,
    read_verified,
)
from tests.support.esco import SAMPLE_PATH, SAMPLE_RELEASE


@pytest.fixture(scope="module")
def sample_bytes() -> bytes:
    return read_verified(SAMPLE_PATH, SAMPLE_RELEASE)


def rezip(data: bytes, replace: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(out, "w") as dst:
        for name in src.namelist():
            dst.writestr(name, replace.get(name, src.read(name)))
    return out.getvalue()


@pytest.mark.req("TAX1-04")
def test_a_file_with_other_bytes_is_refused_before_it_is_parsed(tmp_path: Path) -> None:
    good = SAMPLE_PATH.read_bytes()
    altered = tmp_path / SAMPLE_RELEASE.file_name
    altered.write_bytes(good[:-1] + bytes([good[-1] ^ 1]))  # same size, one bit flipped

    with pytest.raises(ReleaseIntegrityError, match="SHA-256"):
        read_verified(altered, SAMPLE_RELEASE)
    truncated = tmp_path / "short.zip"
    truncated.write_bytes(good[:100])
    with pytest.raises(ReleaseIntegrityError, match="bytes"):
        read_verified(truncated, SAMPLE_RELEASE)
    with pytest.raises(ReleaseIntegrityError, match="make setup"):
        read_verified(tmp_path / "missing.zip", SAMPLE_RELEASE)


@pytest.mark.req("TAX1-01")
def test_the_sample_parses_into_distinct_concepts_grouped_by_isco(sample_bytes: bytes) -> None:
    catalogue = parse_release(sample_bytes, SAMPLE_RELEASE)

    assert len(catalogue.occupations) == 30
    by_label = {o.preferred_label: o for o in catalogue.occupations}
    agent, manager = by_label["ICT help desk agent"], by_label["ICT help desk manager"]
    # Two specialist occupations in one ISCO-08 unit group stay two concepts.
    assert agent.isco_code == manager.isco_code == "3512"
    assert agent.concept_id != manager.concept_id
    assert agent.concept_id == concept_id(agent.uri)  # stable: derived from the ESCO URI
    groups = {g.code for g in catalogue.isco_groups}
    for occupation in catalogue.occupations:  # every ancestor group is present
        assert {occupation.isco_code[:n] for n in range(1, 5)} <= groups


def test_aliases_and_hidden_labels_are_kept_apart_and_never_duplicated(sample_bytes: bytes) -> None:
    catalogue = parse_release(sample_bytes, SAMPLE_RELEASE)

    for occupation in catalogue.occupations:
        kinds = [label.kind for label in occupation.labels]
        assert kinds.count(LabelKind.PREFERRED) == 1
        normalised = [label.normalised for label in occupation.labels]
        assert len(normalised) == len(set(normalised))
    assert sum(len(o.labels) for o in catalogue.occupations) == 367
    hidden = [
        label for o in catalogue.occupations for label in o.labels if label.kind is LabelKind.HIDDEN
    ]
    assert hidden  # the sample keeps search-only labels (general practitioner)


def test_skill_relations_link_only_concepts_in_the_release(sample_bytes: bytes) -> None:
    catalogue = parse_release(sample_bytes, SAMPLE_RELEASE)

    occupations = {o.concept_id for o in catalogue.occupations}
    skills = {s.skill_id for s in catalogue.skills}
    assert {r.relation.value for r in catalogue.occupation_skills} == {"essential", "optional"}
    assert all(
        r.concept_id in occupations and r.skill_id in skills for r in catalogue.occupation_skills
    )
    assert all(
        r.skill_id in skills and r.related_skill_id in skills for r in catalogue.skill_relations
    )
    for parent in catalogue.broader:
        assert (parent.broader_concept_id is None) != (parent.broader_isco_code is None)


def test_a_relation_naming_an_unknown_concept_is_a_structure_error(sample_bytes: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(sample_bytes)) as archive:
        relations = archive.read("occupationSkillRelations_en.csv").decode()
    bogus = relations.replace(
        "http://data.europa.eu/esco/skill/", "http://data.europa.eu/esco/skill/0", 1
    )
    broken = rezip(sample_bytes, {"occupationSkillRelations_en.csv": bogus.encode()})

    with pytest.raises(ReleaseIntegrityError, match="unknown concept"):
        parse_release(broken, SAMPLE_RELEASE)


def test_a_missing_file_or_column_is_a_structure_error(sample_bytes: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(sample_bytes)) as archive:
        occupations = archive.read("occupations_en.csv").decode()
    renamed = occupations.replace("iscoGroup", "iscoGrp", 1)
    with pytest.raises(ReleaseIntegrityError, match="lacks columns"):
        parse_release(rezip(sample_bytes, {"occupations_en.csv": renamed.encode()}), SAMPLE_RELEASE)
    with pytest.raises(ReleaseIntegrityError, match="not a zip"):
        parse_release(b"not a zip", SAMPLE_RELEASE)


def test_a_concept_repeated_with_only_a_new_date_is_kept_once_and_counted(
    sample_bytes: bytes,
) -> None:
    catalogue = parse_release(sample_bytes, SAMPLE_RELEASE)

    assert catalogue.repeated_rows_collapsed == 1  # one skill the release lists twice
    assert len({s.uri for s in catalogue.skills}) == len(catalogue.skills) == 200


def test_a_concept_repeated_with_different_content_is_refused(sample_bytes: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(sample_bytes)) as archive:
        reader = csv.DictReader(io.StringIO(archive.read("occupations_en.csv").decode()))
        rows = list(reader)
    rows.append({**rows[0], "description": "A different description."})
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(reader.fieldnames or ()))
    writer.writeheader()
    writer.writerows(rows)

    with pytest.raises(ReleaseIntegrityError, match="different content"):
        parse_release(
            rezip(sample_bytes, {"occupations_en.csv": out.getvalue().encode()}), SAMPLE_RELEASE
        )


def test_labels_normalise_case_and_spacing_only() -> None:
    assert normalise_label("  ICT   Help desk AGENT ") == "ict help desk agent"
    assert normalise_label("Kingston-upon-Hull") == "kingston-upon-hull"
