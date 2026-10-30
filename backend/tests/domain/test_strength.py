"""The overlooked strength's contract (plan section 4; ADR 0014 decision 3; Sprint W SW.5): the
model may propose at most one strength, a quotation of the person's own words against an
essential skill of one of their destinations; code verifies the span and the skill before
anyone is asked to confirm it. Finding none is an answer. Hand-built inputs; no database."""

import uuid

import pytest

from careerwright.capability.strength import (
    MAX_PROMPT_BYTES,
    DestinationKind,
    DestinationSkills,
    ModelStrength,
    StrengthOutput,
    build_input,
    check_strength,
    fixture_strength,
    prompt_context,
    render_prompt,
)
from careerwright.catalogue.records import SkillRef
from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.profile.discovery import EvidenceItem
from careerwright.profile.interview import ProfileField, ProposalOrigin

TURN = uuid.UUID("00000000-0000-4000-8000-0000000000e1")
ANSWERS = [
    EvidenceItem(field=ProfileField.CURRENT_ROLE, text="data analyst"),
    EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="tidying messy data"),
    EvidenceItem(
        field=ProfileField.EVIDENCED_TASKS, text="I explained the monthly figures to the board"
    ),
]


def skill(label: str) -> SkillRef:
    return SkillRef(uuid.uuid5(uuid.NAMESPACE_URL, f"skill:{label}"), label, None, "essential")


STATISTICIAN = DestinationSkills(
    uuid.uuid5(uuid.NAMESPACE_URL, "statistician"),
    "statistician",
    DestinationKind.HORIZON,
    [skill("communicate with a non-scientific audience"), skill("statistics")],
)
DATA_SCIENTIST = DestinationSkills(
    uuid.uuid5(uuid.NAMESPACE_URL, "data scientist"),
    "data scientist",
    DestinationKind.TARGET,
    [skill("statistics"), skill("deliver visual presentation of data")],
)


def context(destinations: list[DestinationSkills] | None = None):  # type: ignore[no-untyped-def]
    return build_input(
        turn_id=TURN,
        profile_version=3,
        release="esco-v1.2.1-en-csv",
        answers=ANSWERS,
        destinations=destinations or [STATISTICIAN, DATA_SCIENTIST],
    )


def proposal(destination: str, skill_ref: str, quotation: str) -> StrengthOutput:
    return StrengthOutput(
        strengths=[ModelStrength(destination=destination, skill=skill_ref, quotation=quotation)]
    )


def test_a_shared_skill_has_one_ref_and_the_model_reads_no_id_and_no_title() -> None:
    built = context()

    # A title (the role "data analyst") is never quoted as a strength of itself.
    assert [a.text for a in built.answers] == [
        "tidying messy data",
        "I explained the monthly figures to the board",
    ]
    assert [s.label for s in built.skills] == [
        "communicate with a non-scientific audience",
        "statistics",
        "deliver visual presentation of data",
    ]
    assert built.destinations[1].skills == ["s2", "s3"]  # "statistics" keeps its ref, s2
    prompt = render_prompt(built)
    assert str(TURN) not in prompt
    assert not any(str(s.skill_id) in prompt for s in built.skills)
    assert not any(str(d.concept_id) in prompt for d in built.destinations)


@pytest.mark.req("REC1-06")
def test_a_verified_quotation_against_a_listed_essential_skill_is_proposed() -> None:
    built = context()

    checked, problems = check_strength(
        proposal("d1", "s1", "explained the monthly figures"), built, ProposalOrigin.MODEL
    )

    assert problems == []
    assert checked is not None
    found = checked.strength
    assert found is not None
    assert (found.destination.title, found.destination.kind) == ("statistician", "horizon")
    assert found.skill.label == "communicate with a non-scientific audience"
    assert (found.quotation.answer_field, found.quotation.text) == (
        ProfileField.EVIDENCED_TASKS,
        "explained the monthly figures",
    )
    assert (checked.turn_id, checked.profile_version) == (TURN, 3)


def test_finding_none_is_an_answer_never_a_failure() -> None:
    checked, problems = check_strength(
        StrengthOutput(strengths=[]), context(), ProposalOrigin.MODEL
    )

    assert problems == []
    assert checked is not None
    assert checked.strength is None


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (proposal("d9", "s1", "explained the monthly figures"), "destination"),
        # "deliver visual presentation of data" is the data scientist's, not the statistician's.
        (proposal("d1", "s3", "explained the monthly figures"), "skill"),
        (proposal("d1", "s1", "explained the annual figures"), "quotation"),  # never said
        (proposal("d1", "s1", "to the"), "quotation"),  # no content word
        (proposal("d1", "s1", "xplained the monthly"), "quotation"),  # not whole words
        (proposal("d1", "s1", "data analyst"), "quotation"),  # a title, not a quotable answer
        (
            StrengthOutput(
                strengths=[
                    ModelStrength(destination="d1", skill="s1", quotation="monthly figures"),
                    ModelStrength(destination="d2", skill="s2", quotation="monthly figures"),
                ]
            ),
            "strengths",
        ),
    ],
)
def test_anything_unverified_is_refused_for_repair(output: StrengthOutput, problem: str) -> None:
    checked, problems = check_strength(output, context(), ProposalOrigin.MODEL)

    assert checked is None
    assert any(p.startswith(f"{problem}:") for p in problems)


def test_the_input_steps_down_skills_to_fit_and_refuses_answers_too_long() -> None:
    many = DestinationSkills(
        uuid.uuid4(),
        "many skills",
        DestinationKind.HORIZON,
        [skill(f"a fairly long essential skill label number {n}") for n in range(60)],
    )

    built = context([many] * 9)

    assert len(built.destinations[0].skills) < 60
    assert len(render_prompt(built).encode()) <= MAX_PROMPT_BYTES
    long_answers = [EvidenceItem(field=ProfileField.ENJOYED_TASKS, text="é" * 120)] * 80
    with pytest.raises(CareerwrightError) as refused:
        build_input(
            turn_id=TURN,
            profile_version=3,
            release="r",
            answers=long_answers,
            destinations=[STATISTICIAN],
        )
    assert refused.value.code is ErrorCode.LIMIT_EXCEEDED
    assert refused.value.details["reason"] == "answers_too_long"


def test_the_demo_fixture_proposes_a_shared_word_or_nothing_and_passes_the_check() -> None:
    built = context()

    found = fixture_strength(prompt_context(built))

    # "tidying messy data" shares "data" with the data scientist's "... presentation of data".
    checked, problems = check_strength(found, built, ProposalOrigin.FIXTURE)
    assert problems == []
    assert checked is not None
    shown = checked.strength
    assert shown is not None
    assert shown.quotation.text == "tidying messy data"
    assert shown.skill.label == "deliver visual presentation of data"
    none = context([STATISTICIAN])
    assert fixture_strength(prompt_context(none)) == StrengthOutput(strengths=[])
