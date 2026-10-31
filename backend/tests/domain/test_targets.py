"""Each target is stored once (Task 6d slice A; PROF-10): what a title names is decided by one
set of rules, and the pack's targets the migration backfills with are the committed ones.
No database: `decide` is given what matching found."""

import unicodedata
import uuid

import pytest

from careerwright.capability.commands import committed_data, pack_targets
from careerwright.migrations.versions import r0034_target_records as migration
from careerwright.profile.records import TargetCoverage as Coverage
from careerwright.profile.records import TargetKind, TargetLink, TargetRecord
from careerwright.profile.targets import Choice, PackTarget, PackTargets, decide

NURSE = "http://data.europa.eu/esco/occupation/8d3e8aaa-791b-4c75-a465-f3f827028f50"
BOOKKEEPER = "http://data.europa.eu/esco/occupation/c3aae59e-1441-4b3e-bdd1-6da50dc7cf42"
ACCOUNTANT = "http://data.europa.eu/esco/occupation/0000accountant"
OTHER = "http://data.europa.eu/esco/occupation/0000other"
PACK = PackTargets(
    "0.1.0",
    (
        PackTarget("registered-nurse-manchester", "Registered nurse", NURSE),
        PackTarget("bookkeeping-assistant-leeds", "Bookkeeping assistant", BOOKKEEPER),
    ),
)
PACK_KEYS = {
    "registered-nurse-manchester": "registered nurse",
    "bookkeeping-assistant-leeds": "bookkeeping assistant",
}
SOURCE = uuid.uuid4()


def record(
    key: str, *, choice: Choice | None = None, labelled: tuple[str, ...] = ()
) -> TargetRecord:
    return decide(key, key, choice=choice, labelled=labelled, pack=PACK, pack_keys=PACK_KEYS)


@pytest.mark.req("PROF-10")
def test_the_person_s_choice_wins_and_is_cited_by_its_source() -> None:
    found = record(
        "bookkeeper", choice=Choice(ACCOUNTANT, SOURCE), labelled=(BOOKKEEPER, ACCOUNTANT)
    )

    assert (found.link, found.occupation_uri, found.kind) == (
        TargetLink.OCCUPATION_CHOICE,
        ACCOUNTANT,
        TargetKind.ESCO,
    )
    assert found.source_ref_id == SOURCE
    assert found.esco_occupation == ACCOUNTANT
    assert found.label_matches == (ACCOUNTANT, BOOKKEEPER)


@pytest.mark.req("PROF-10")
def test_one_label_is_the_occupation_and_several_are_kept_with_none_picked() -> None:
    one = record("data scientist", labelled=(OTHER,))
    several = record("bookkeeper", labelled=(BOOKKEEPER, ACCOUNTANT))

    assert (one.link, one.occupation_uri, one.kind) == (
        TargetLink.EXACT_LABEL,
        OTHER,
        TargetKind.OWN_WORDS,
    )
    # A typed title two occupations hold names neither: the person chooses which they mean.
    assert (several.link, several.occupation_uri, several.esco_occupation) == (
        TargetLink.NONE,
        None,
        None,
    )
    assert several.label_matches == (ACCOUNTANT, BOOKKEEPER)
    assert several.coverage is Coverage.NOT_COVERED


@pytest.mark.req("PROF-10", "MAP1-05")
def test_a_pack_target_s_title_links_through_its_crosswalk_for_skills_only() -> None:
    nurse = record("registered nurse")
    shared = record("bookkeeping assistant", labelled=(ACCOUNTANT, OTHER))

    assert (nurse.link, nurse.occupation_uri) == (TargetLink.PACK_CROSSWALK, NURSE)
    assert (nurse.coverage, nurse.pack_target_id, nurse.pack_target_basis) == (
        Coverage.PACK_TARGET,
        "registered-nurse-manchester",
        "title",
    )
    # ESCO itself names no occupation for it, so the slate, the sketch and the strength join
    # nothing to it (ADR 0007 decision 13); only Skills reads the crosswalk.
    assert nurse.esco_occupation is None
    assert (shared.link, shared.occupation_uri, shared.label_matches) == (
        TargetLink.PACK_CROSSWALK,
        BOOKKEEPER,
        (ACCOUNTANT, OTHER),
    )


@pytest.mark.req("PROF-10", "MAP1-05", "READINESS-04")
def test_a_chosen_occupation_a_crosswalk_names_is_that_pack_target_s() -> None:
    chosen = record("nurse responsible for general care", choice=Choice(NURSE, SOURCE))

    assert (chosen.coverage, chosen.pack_target_id, chosen.pack_target_basis) == (
        Coverage.PACK_TARGET,
        "registered-nurse-manchester",
        "esco_crosswalk",
    )
    assert record("marine biologist").coverage is Coverage.NOT_COVERED
    assert record("marine biologist").link is TargetLink.NONE


@pytest.mark.req("PROF-10")
def test_several_pack_targets_crosswalked_to_one_occupation_are_never_guessed_between() -> None:
    twins = PackTargets(
        "0.1.0", (PackTarget("a", "Clerk A", BOOKKEEPER), PackTarget("b", "Clerk B", BOOKKEEPER))
    )
    found = decide(
        "bookkeeper",
        "bookkeeper",
        choice=Choice(BOOKKEEPER, SOURCE),
        labelled=(BOOKKEEPER,),
        pack=twins,
        pack_keys={"a": "clerk a", "b": "clerk b"},
    )

    assert (found.coverage, found.pack_target_id, found.pack_target_basis) == (
        Coverage.SEVERAL_PACK_TARGETS,
        None,
        None,
    )


@pytest.mark.req("PROF-10")
def test_the_migration_backfills_with_the_committed_pack_targets_and_crosswalks() -> None:
    committed = pack_targets(committed_data())

    assert committed.version == migration.PACK_VERSION
    assert (
        tuple((t.target_id, t.title, t.esco_uri) for t in committed.targets)
        == migration.PACK_TARGETS
    )


@pytest.mark.req("PROF-10")
def test_the_concept_key_folds_every_letter_that_decomposes_to_one_ascii_letter() -> None:
    # Latin-1 Supplement and Latin Extended-A, both cases, as NFKD decomposes them.
    expected = {}
    for code in range(0xC0, 0x180):
        letter = chr(code)
        base = "".join(
            c for c in unicodedata.normalize("NFKD", letter) if not unicodedata.combining(c)
        )
        if len(base) == 1 and base.isascii() and base.isalpha() and base != letter:
            expected[letter] = base.lower()

    assert len(migration.ACCENTED) == len(migration.PLAIN)
    assert dict(zip(migration.ACCENTED, migration.PLAIN, strict=True)) == expected
