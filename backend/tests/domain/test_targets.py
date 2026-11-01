"""Each target is stored once (Task 6d slice A; PROF-10): what a title names is decided by one
set of rules, and the pack's targets the migration backfills with are the committed ones.
No database: `decide` is given what matching found."""

import unicodedata
import uuid

import pytest

from careerwright.capability.commands import committed_data, pack_targets
from careerwright.catalogue.records import UkGroup, UkTitle
from careerwright.migrations.versions import r0034_target_records as migration
from careerwright.migrations.versions import r0035_every_version_s_targets as backfill
from careerwright.migrations.versions import r0036_uk_titles as uk_migration
from careerwright.profile.records import TargetCoverage as Coverage
from careerwright.profile.records import TargetKind, TargetLink, TargetRecord
from careerwright.profile.targets import (
    OTHER_FIELDS,
    QUALIFIER,
    Choice,
    PackTarget,
    PackTargets,
    decide,
    without_qualifiers,
)

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
    return decide(
        key,
        key,
        unqualified=key,
        choice=choice,
        labelled=labelled,
        pack=PACK,
        pack_keys=PACK_KEYS,
    )


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


@pytest.mark.req("PROF-10", "MAP1-05")
def test_a_qualifier_in_brackets_is_left_out_only_to_reach_a_pack_target_by_its_title() -> None:
    # Task 6d slice A fix round 1 (review Minor 2): "Registered nurse (adult)" reached the
    # nursing pack target before targets were stored once (Skills folded bracketed notes) and
    # must again, or the person is told Careerwright can't check a role it covers.
    assert without_qualifiers("Registered nurse (adult)").split() == ["Registered", "nurse"]
    assert without_qualifiers("IT support technician [2nd line]").split() == [
        "IT",
        "support",
        "technician",
    ]
    adult = decide(
        "Registered nurse (adult)",
        "registered nurse adult",
        unqualified="registered nurse",
        choice=None,
        labelled=(),
        pack=PACK,
        pack_keys=PACK_KEYS,
    )

    assert (adult.coverage, adult.pack_target_id, adult.pack_target_basis) == (
        Coverage.PACK_TARGET,
        "registered-nurse-manchester",
        "title",
    )
    assert (adult.link, adult.occupation_uri, adult.esco_occupation) == (
        TargetLink.PACK_CROSSWALK,
        NURSE,
        None,
    )
    # The whole title as a concept still comes first.
    twins = PackTargets(
        "0.1.0", (*PACK.targets, PackTarget("adult", "Registered nurse adult", OTHER))
    )
    exact = decide(
        "Registered nurse (adult)",
        "registered nurse adult",
        unqualified="registered nurse",
        choice=None,
        labelled=(),
        pack=twins,
        pack_keys={**PACK_KEYS, "adult": "registered nurse adult"},
    )
    assert (exact.pack_target_id, exact.occupation_uri) == ("adult", OTHER)


@pytest.mark.req("PROF-10")
def test_the_backfill_leaves_out_the_qualifiers_the_resolver_leaves_out() -> None:
    assert backfill.QUALIFIER == QUALIFIER
    assert (backfill.PACK_VERSION, backfill.PACK_TARGETS) == (
        migration.PACK_VERSION,
        migration.PACK_TARGETS,
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
        unqualified="bookkeeper",
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

    # Migration 0034 backfilled with pack 0.1.0. The app now reads the reviewed pack 0.2.0
    # (Task 10A fix round 1), whose targets and crosswalks are 0.1.0's, so every backfilled
    # record still names a target the committed pack holds.
    assert migration.PACK_VERSION == "0.1.0"
    assert committed.version == "0.2.0"
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


# Task 6d slice B: a UK title from the ONS coding index, the person's own words, the closest
# occupation they chose and "None of these is my job" (ADR 0015 decision 3).

NURSING = (UkGroup("2221", "Nursing professionals"),)
LISTED = UkTitle("Registered nurse", "registered nurse", ("2235", "2237"), NURSING)
SPECIALIST = "http://data.europa.eu/esco/occupation/0000specialist-nurse"


@pytest.mark.req("PROF-10", "DIV1-13", "DIV1-03")
def test_a_title_the_uk_index_lists_is_an_ons_title_with_every_group_ons_codes_it_to() -> None:
    found = decide(
        "Doula",
        "doula",
        unqualified="doula",
        choice=None,
        labelled=(),
        pack=PACK,
        pack_keys=PACK_KEYS,
        listed=UkTitle("Doula", "doula", ("6131",), (UkGroup("5321", None),)),
    )
    own = record("bookkeeping clerk assistant")

    assert (found.kind, found.soc_codes, found.isco_codes) == (
        TargetKind.ONS,
        ("6131",),
        ("5321",),
    )
    assert (found.link, found.occupation_uri) == (TargetLink.NONE, None)
    assert (own.kind, own.soc_codes, own.isco_codes) == (TargetKind.OWN_WORDS, (), ())


@pytest.mark.req("PROF-10", "DIV1-14")
def test_the_closest_occupation_the_person_chose_keeps_their_title_s_kind_and_words() -> None:
    closest = decide(
        "Registered nurse",
        "registered nurse",
        unqualified="registered nurse",
        choice=Choice(SPECIALIST, SOURCE),
        closest=True,
        labelled=(),
        pack=PACK,
        pack_keys=PACK_KEYS,
        listed=LISTED,
    )

    assert (closest.title, closest.kind, closest.isco_codes) == (
        "Registered nurse",
        TargetKind.ONS,
        ("2221",),
    )
    assert (closest.link, closest.occupation_uri, closest.source_ref_id) == (
        TargetLink.OCCUPATION_CHOICE,
        SPECIALIST,
        SOURCE,
    )
    assert closest.esco_occupation == SPECIALIST  # the role's ESCO seed: the person's choice


@pytest.mark.req("PROF-10", "DIV1-14")
def test_none_of_these_leaves_the_title_with_no_esco_occupation_and_keeps_its_coverage() -> None:
    none = decide(
        "Registered nurse",
        "registered nurse",
        unqualified="registered nurse",
        choice=None,
        none_of_these=True,
        labelled=(),
        pack=PACK,
        pack_keys=PACK_KEYS,
        listed=LISTED,
    )

    assert (none.link, none.occupation_uri, none.esco_occupation) == (
        TargetLink.NONE_OF_THESE,
        None,
        None,
    )
    assert (none.kind, none.coverage, none.pack_target_id) == (
        TargetKind.ONS,
        Coverage.PACK_TARGET,
        "registered-nurse-manchester",
    )


@pytest.mark.req("PROF-10", "MAP1-05")
def test_the_migration_decides_again_with_the_resolver_s_qualifiers_and_other_fields() -> None:
    assert uk_migration.QUALIFIER == QUALIFIER
    assert frozenset(uk_migration.OTHER_FIELDS) == OTHER_FIELDS[uk_migration.NURSE_KEY]
    assert set(OTHER_FIELDS) == {uk_migration.NURSE_KEY}
    assert (uk_migration.PACK_VERSION, uk_migration.PACK_TARGETS) == (
        backfill.PACK_VERSION,
        backfill.PACK_TARGETS,
    )
    assert uk_migration.NURSE_TARGET in {target for target, _, _ in uk_migration.PACK_TARGETS}


@pytest.mark.req("PROF-10", "MAP1-05")
@pytest.mark.parametrize(
    ("title", "qualifier", "reaches"),
    [
        ("Registered nurse (mental health)", "mental health", False),
        ("Registered nurse (children's)", "children s", False),
        ("Registered nurse (children)", "children", False),
        ("Registered nurse (learning disabilities)", "learning disability", False),
        ("Registered nurse (adult)", "adult", True),
        ("Registered nurse [2nd line]", "2nd line", True),
    ],
)
def test_a_qualifier_naming_another_nursing_field_never_reaches_the_adult_pack_nurse(
    title: str, qualifier: str, reaches: bool
) -> None:
    # The pack's "Registered nurse" rests on adult nursing evidence; the NMC registers nurses
    # in four fields, so a qualifier naming one of the other three is another registered role.
    found = decide(
        title,
        f"registered nurse {qualifier}",
        unqualified="registered nurse",
        qualifiers=(qualifier,),
        choice=None,
        labelled=(),
        pack=PACK,
        pack_keys=PACK_KEYS,
    )

    covered = (found.coverage, found.pack_target_id, found.link)
    if reaches:
        assert covered == (
            Coverage.PACK_TARGET,
            "registered-nurse-manchester",
            TargetLink.PACK_CROSSWALK,
        )
    else:
        assert covered == (Coverage.NOT_COVERED, None, TargetLink.NONE)
