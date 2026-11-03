"""Two horizons, Next step and Aim higher (Task 6g): the person's reference level, from their
role only, and where work is placed against it, by its job group's usual ISCO skill level."""

import pytest

from careerwright.profile.horizons import (
    UNKNOWN_REFERENCE,
    Horizon,
    Reference,
    ReferenceBasis,
    place,
    place_title,
    reference_level,
)

NEXT, AIM = Horizon.NEXT_STEP, Horizon.AIM_HIGHER


@pytest.mark.req("DIV1-16")
def test_the_reference_is_the_role_s_one_esco_occupation_s_job_group() -> None:
    # A warehouse manager's unit group, 1324: managers in production and specialised services.
    assert reference_level(["1324"], []) == Reference(
        ReferenceBasis.ROLE_OCCUPATION, 4, frozenset({"1"})
    )
    # The occupation decides even where the title is a UK title too (a closest one chosen).
    assert reference_level(["4321"], ["2141"]).basis is ReferenceBasis.ROLE_OCCUPATION


@pytest.mark.req("DIV1-16")
def test_without_one_occupation_the_uk_title_s_groups_decide_only_when_they_agree() -> None:
    # 4311 bookkeeping clerks and 4313 payroll clerks: both level 2.
    assert reference_level([], ["4311", "4313"]) == Reference(
        ReferenceBasis.UK_TITLE_GROUPS, 2, frozenset({"4"})
    )
    # 2411 accountants (4) and 3313 accounting associate professionals (3) disagree: unknown,
    # never a number between them.
    assert reference_level([], ["2411", "3313"]) == UNKNOWN_REFERENCE
    assert UNKNOWN_REFERENCE.level is None


@pytest.mark.req("DIV1-16")
@pytest.mark.parametrize(
    ("occupations", "uk_groups"),
    [
        ([], []),  # no job yet, a skipped role, or a title in the person's own words
        (["4311", "2411"], []),  # several ESCO occupations hold the title: none is chosen
    ],
)
def test_otherwise_the_reference_is_unknown(occupations: list[str], uk_groups: list[str]) -> None:
    assert reference_level(occupations, uk_groups) == UNKNOWN_REFERENCE


@pytest.mark.req("DIV1-16")
@pytest.mark.parametrize(
    ("code", "horizon"),
    [("9629", NEXT), ("5131", NEXT), ("4211", NEXT), ("3434", AIM), ("2131", AIM), ("1411", AIM)],
)
def test_with_the_reference_unknown_isco_s_bands_decide(code: str, horizon: Horizon) -> None:
    # Levels 1 and 2 are Next step, 3 and 4 Aim higher.
    assert place(code, UNKNOWN_REFERENCE) is horizon


@pytest.mark.req("DIV1-16")
@pytest.mark.parametrize(
    ("level", "code", "horizon"),
    [
        (2, "9629", NEXT),  # below
        (2, "5131", NEXT),  # at the level
        (2, "3434", AIM),  # above
        (3, "4211", NEXT),
        (3, "3434", NEXT),
        (3, "2131", AIM),
        (1, "5131", AIM),
    ],
)
def test_next_step_is_at_or_below_the_reference_and_aim_higher_above_it(
    level: int, code: str, horizon: Horizon
) -> None:
    reference = reference_level([{1: "9629", 2: "5223", 3: "3343"}[level]], [])

    assert reference.level == level
    assert place(code, reference) is horizon


@pytest.mark.req("DIV1-16")
def test_for_a_level_4_role_aim_higher_is_level_4_work_in_another_major_group() -> None:
    teacher = reference_level(["2330"], [])  # secondary education teachers: professionals

    assert place("2310", teacher) is NEXT  # level 4, the same major group
    assert place("3434", teacher) is NEXT  # level 3
    assert place("1345", teacher) is AIM  # level 4, managers: another major group
    assert place("1411", teacher) is NEXT  # level 3 managers: below, whatever the group


@pytest.mark.req("DIV1-16")
def test_a_uk_title_is_placed_only_when_every_group_ons_codes_it_to_agrees() -> None:
    # Task 6g slice B: a title idea the UK job-title index lists is placed by its ISCO-08
    # groups, as any work is; one whose groups disagree goes in neither set.
    teacher = reference_level(["2330"], [])
    assert place_title(["3339"], UNKNOWN_REFERENCE) is AIM  # customer success manager
    assert place_title(["2424", "2423"], UNKNOWN_REFERENCE) is AIM  # both level 4
    assert place_title(["4313"], UNKNOWN_REFERENCE) is NEXT
    # Account manager: managers and professionals (4) and associate professionals (3).
    assert place_title(["1330", "2431", "3313"], UNKNOWN_REFERENCE) is None
    # Children's nurse: nurses (4) and child care workers (2), whichever set each would be in.
    assert place_title(["2221", "5311"], teacher) is None
    # Level 4 in the role's major group and in another: one level, but two sets.
    assert place_title(["2310", "1345"], teacher) is None
    assert place_title([], UNKNOWN_REFERENCE) is None
