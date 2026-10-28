"""The written "Why this could suit you" (S2.7; REC-1, D3): one call per slate writes short
claims, and deterministic code verifies every quotation as an exact span of the person's
pinned answers or of ESCO's record of that occupation, and refuses unsupported claims.
Semantic checks only, never exact prose; no database, no network."""

import json
import uuid
from typing import Any

import pytest

from nessa.catalogue.records import IscoGroupRef, OccupationFacts
from nessa.profile.discovery import evidence_of
from nessa.profile.document import FIELD_NAMES, ProfileInput, apply_profile_input, empty_profile
from nessa.profile.fixture_explainer import fixture_explanation, prompt_context
from nessa.profile.interview import ProfileField, ProposalOrigin
from nessa.profile.safety import SUPPORT_TURN_INSTRUCTION, has_risk_stem
from nessa.profile.slate_explanation import (
    INSTRUCTIONS,
    MAX_CLAIMS,
    MAX_PROMPT_BYTES,
    MAX_QUOTES,
    SCHEMA_ALLOWANCE_TOKENS,
    ExplanationInput,
    ExplanationOutput,
    QuoteSource,
    RecordPart,
    SlateExplanation,
    build_input,
    check_explanation,
    prompt_bytes,
    render_prompt,
    worst_case_nano_usd,
)
from tests.domain.test_safety import CORPUS

SOURCE = uuid.UUID("00000000-0000-4000-8000-0000000000aa")
DISCOVERY = uuid.UUID("00000000-0000-4000-8000-0000000000d1")


def document(**fields: Any) -> Any:
    values: dict[str, Any] = {name: {"state": "unasked"} for name in FIELD_NAMES}
    values.update({k: {"state": "provided", "value": v} for k, v in fields.items()})
    return apply_profile_input(empty_profile(), ProfileInput.model_validate(values), SOURCE)


PERSON = document(
    preferred_name="Sam Synthetic",
    current_role="Warehouse shift supervisor",
    enjoyed_tasks=["repairing bicycles", "working outdoors"],
    work_style=["small team"],
    cities=["Leeds"],
    weekly_study_hours=12,
)


def facts(
    title: str, description: str, *skills: str, concept: str | None = None
) -> OccupationFacts:
    group = IscoGroupRef("7231", "Motor vehicle mechanics")
    return OccupationFacts(
        concept_id=uuid.uuid5(uuid.NAMESPACE_URL, f"test:{concept or title}"),
        preferred_label=title,
        esco_uri=f"http://data.europa.eu/esco/occupation/{(concept or title).replace(' ', '-')}",
        esco_code="7231.1",
        description=description,
        regulated=False,
        unit=group,
        family=IscoGroupRef("723", "Machinery mechanics"),
        sector=IscoGroupRef("7", "Craft and related trades workers"),
        preferred_key=title.casefold(),
        label_keys=frozenset({title.casefold()}),
        essential_skills=skills,
        essential_skill_count=len(skills),
    )


MECHANIC = facts(
    "bicycle mechanic",
    "Bicycle mechanics maintain and repair a variety of bicycle models and componentry.",
    "repair bicycles",
    "use hand tools",
)
GARDENER = facts(
    "landscape gardener",
    "Landscape gardeners plan, build and maintain parks and gardens, working outdoors.",
    "maintain gardens",
)


def context(*occupations: OccupationFacts) -> ExplanationInput:
    return build_input(
        discovery_id=DISCOVERY,
        profile_version=3,
        release="esco-v1.2.1-en-csv",
        answers=evidence_of(PERSON),
        occupations=list(occupations or (MECHANIC, GARDENER)),
    )


def quote(source: str, text: str) -> dict[str, str]:
    return {"source": source, "text": text}


def claim(text: str, *quotes: dict[str, str]) -> dict[str, Any]:
    return {"text": text, "quotes": list(quotes)}


GOOD_MECHANIC = claim(
    "You enjoy fixing bikes, and this work is mostly maintaining and repairing them.",
    quote("answer", "repairing bicycles"),
    quote("esco", "maintain and repair a variety of bicycle models"),
)
GOOD_GARDENER = claim(
    "You like being outside, and this work keeps you outside most days.",
    quote("answer", "working outdoors"),
    quote("esco", "working outdoors"),
)


def output(*explanations: tuple[str, list[dict[str, Any]]]) -> ExplanationOutput:
    chosen = explanations or (("o1", [GOOD_MECHANIC]), ("o2", [GOOD_GARDENER]))
    return ExplanationOutput.model_validate(
        {"explanations": [{"occupation": ref, "claims": claims} for ref, claims in chosen]}
    )


def problems(out: ExplanationOutput, ctx: ExplanationInput | None = None) -> list[str]:
    written, found = check_explanation(out, ctx or context(), ProposalOrigin.MODEL)
    assert (written is None) == bool(found)
    return found


@pytest.mark.req("REC1-11")
def test_a_valid_explanation_keeps_each_quotation_in_its_source_s_own_words() -> None:
    # The model's quotation may differ in case, spacing and apostrophes; what is stored is
    # the source's own characters, never what the model typed.
    loose = claim(
        "You enjoy fixing bikes, and this work is mostly maintaining and repairing them.",
        quote("answer", "Repairing  Bicycles"),
        quote("esco", "“MAINTAIN and repair a variety of bicycle models.”"),
        quote("esco", "Repair bicycles"),
    )

    written, found = check_explanation(
        output(("o1", [loose]), ("o2", [GOOD_GARDENER])), context(), ProposalOrigin.MODEL
    )

    assert found == []
    assert isinstance(written, SlateExplanation)
    assert (written.discovery_id, written.profile_version, written.origin) == (
        DISCOVERY,
        3,
        ProposalOrigin.MODEL,
    )
    mechanic, gardener = written.suggestions
    assert (mechanic.concept_id, mechanic.title) == (MECHANIC.concept_id, "bicycle mechanic")
    [first] = mechanic.claims
    assert [(q.source, q.answer_field, q.record_part, q.text) for q in first.quotations] == [
        (QuoteSource.ANSWER, ProfileField.ENJOYED_TASKS, None, "repairing bicycles"),
        (
            QuoteSource.ESCO,
            None,
            RecordPart.DESCRIPTION,
            "maintain and repair a variety of bicycle models",
        ),
        (QuoteSource.ESCO, None, RecordPart.ESSENTIAL_SKILL, "repair bicycles"),
    ]
    assert gardener.concept_id == GARDENER.concept_id


@pytest.mark.req("REC1-11")
def test_a_misquotation_of_the_occupation_record_is_refused() -> None:
    misquoted = claim(
        "You enjoy fixing bikes, and this work is about repairing them.",
        quote("answer", "repairing bicycles"),
        quote("esco", "repairs bicycle models"),  # ESCO says "repair a variety of bicycle models"
    )

    found = problems(output(("o1", [misquoted]), ("o2", [GOOD_GARDENER])))

    assert any("repairs bicycle models" in p and "ESCO" in p for p in found)


@pytest.mark.req("REC1-11", "REC1-06")
def test_an_invented_answer_is_refused() -> None:
    invented = claim(
        "You love animals, and this work keeps you close to the bikes you care for.",
        quote("answer", "I love animals"),
        quote("esco", "repair bicycles"),
    )

    found = problems(output(("o1", [invented]), ("o2", [GOOD_GARDENER])))

    assert any("I love animals" in p and "your answers" in p for p in found)


@pytest.mark.req("REC1-11", "REC1-06")
def test_an_occupation_fact_esco_lacks_is_refused_even_from_another_suggestion_s_record() -> None:
    lacking = claim(
        "You like being outside, and this work is outdoors in all weathers.",
        quote("answer", "working outdoors"),
        quote("esco", "outdoors in all weathers"),
    )
    borrowed = claim(
        "You like being outside, and this work is outdoors too.",
        quote("answer", "working outdoors"),
        quote("esco", "working outdoors"),  # the gardener's record, not the mechanic's
    )

    assert any("outdoors in all weathers" in p for p in problems(output(("o1", [lacking]))))
    assert any(
        "working outdoors" in p and "bicycle mechanic" in p
        for p in problems(output(("o1", [borrowed]), ("o2", [GOOD_GARDENER])))
    )


@pytest.mark.req("REC1-11")
@pytest.mark.parametrize(
    "quotes",
    [
        [],
        [quote("answer", "repairing bicycles")],
        [quote("esco", "repair bicycles")],
    ],
    ids=["no quotation", "only the person's answer", "only ESCO's record"],
)
def test_a_claim_must_rest_on_the_person_s_answer_and_on_esco_s_record(
    quotes: list[dict[str, str]],
) -> None:
    unsupported = claim("This could suit the way you like to work with your hands.", *quotes)

    assert problems(output(("o1", [unsupported]), ("o2", [GOOD_GARDENER])))


@pytest.mark.req("REC1-11")
@pytest.mark.parametrize(
    "text",
    [
        "You are ready to apply for this role now, given your repair work.",
        "You already meet the requirements for this repair work.",
        "This repair work pays well and the training is cheap.",
        "Employers are hiring bicycle mechanics, so you would get the job.",
        "Bicycle mechanics are in demand, with many vacancies near you.",
        "This work could earn you £28,000 while you repair bikes.",
    ],
)
def test_a_readiness_affordability_or_hiring_claim_is_refused(text: str) -> None:
    risky = claim(text, quote("answer", "repairing bicycles"), quote("esco", "repair bicycles"))

    assert any("readiness" in p for p in problems(output(("o1", [risky]), ("o2", [GOOD_GARDENER]))))


@pytest.mark.req("REC1-11")
def test_a_word_the_occupation_s_own_record_uses_is_not_a_pay_claim() -> None:
    payroll = facts(
        "payroll clerk",
        "Payroll clerks calculate salaries and check that staff are paid on time.",
        "process payroll",
    )
    described = claim(
        "You keep careful records, and this work checks that staff are paid correctly.",
        quote("answer", "Warehouse shift supervisor"),
        quote("esco", "check that staff are paid on time"),
    )

    assert problems(output(("o1", [described])), context(payroll)) == []


@pytest.mark.req("REC1-11")
@pytest.mark.parametrize(
    "text",
    [
        "You said “repairing bicycles”, and this work repairs bicycles.",
        'You said "repairing bicycles", and this work repairs bicycles.',
        "You said 'repairing bicycles', and this work repairs bicycles.",
    ],
)
def test_a_quotation_written_into_the_claim_itself_is_refused(text: str) -> None:
    inline = claim(text, quote("answer", "repairing bicycles"), quote("esco", "repair bicycles"))

    assert any(
        "quotation marks" in p for p in problems(output(("o1", [inline]), ("o2", [GOOD_GARDENER])))
    )


@pytest.mark.req("REC1-11")
def test_an_apostrophe_is_not_a_quotation_mark() -> None:
    plain = claim(
        "You'd enjoy this: the workers' days are spent on ESCO's listed repairs.",
        quote("answer", "repairing bicycles"),
        quote("esco", "repair bicycles"),
    )

    assert problems(output(("o1", [plain]), ("o2", [GOOD_GARDENER]))) == []


@pytest.mark.req("REC1-11")
def test_part_of_a_word_is_not_a_quotation() -> None:
    fragment = claim(
        "You enjoy fixing bikes, and this work is mostly about repairs.",
        quote("answer", "pairing bi"),
        quote("esco", "repair bicycles"),
    )

    assert any("pairing bi" in p for p in problems(output(("o1", [fragment]))))


@pytest.mark.req("REC1-11")
def test_every_suggestion_is_explained_once_and_no_other() -> None:
    assert problems(output(("o1", [GOOD_MECHANIC])))  # o2 is missing
    assert problems(output(("o1", [GOOD_MECHANIC]), ("o1", [GOOD_MECHANIC])))
    assert problems(output(("o1", [GOOD_MECHANIC]), ("o2", [GOOD_GARDENER]), ("o3", [])))
    assert problems(output(("o1", []), ("o2", [GOOD_GARDENER])))  # nothing written for o1


@pytest.mark.req("REC1-11")
def test_claim_and_quotation_counts_and_lengths_are_bounded() -> None:
    many_claims = [GOOD_MECHANIC] * (MAX_CLAIMS + 1)
    many_quotes = claim(
        "You enjoy fixing bikes, and this work is mostly maintaining and repairing them.",
        *([quote("answer", "repairing bicycles")] * MAX_QUOTES),
        quote("esco", "repair bicycles"),
    )
    long_claim = claim(
        "You enjoy fixing bikes " + "and more " * 40,
        quote("answer", "repairing bicycles"),
        quote("esco", "repair bicycles"),
    )

    for bad in (many_claims, [many_quotes], [long_claim]):
        assert problems(output(("o1", bad), ("o2", [GOOD_GARDENER])))


@pytest.mark.req("REC1-02", "REC1-11")
@pytest.mark.parametrize(
    "text",
    [
        "As an introvert you would enjoy repairing bikes alone.",
        "This repair work suits people with ADHD who like hands-on tasks.",
        "This is a 92% match for your love of repairing bicycles.",
        "Many women find this bicycle repair work rewarding.",
    ],
)
def test_a_type_health_condition_characteristic_or_percentage_never_used_is_refused(
    text: str,
) -> None:
    inferred = claim(text, quote("answer", "repairing bicycles"), quote("esco", "repair bicycles"))

    assert any(
        "did not mention" in p
        for p in problems(output(("o1", [inferred]), ("o2", [GOOD_GARDENER])))
    )


@pytest.mark.req("REC1-02", "REC1-11")
def test_a_characteristic_the_occupation_s_record_names_describes_the_work_not_the_person() -> None:
    midwife = facts(
        "midwife",
        "Midwives support women during pregnancy, labour and the weeks after birth.",
        "advise on pregnancy",
    )
    serving = claim(
        "You enjoy working in a small team, and this work supports women through pregnancy.",
        quote("answer", "small team"),
        quote("esco", "support women during pregnancy"),
    )

    assert problems(output(("o1", [serving])), context(midwife)) == []


@pytest.mark.req("SEC-05", "REC1-11")
def test_the_prompt_carries_the_answers_that_describe_work_and_esco_s_records_only() -> None:
    prompt = render_prompt(context())

    assert "repairing bicycles" in prompt
    assert "Bicycle mechanics maintain and repair" in prompt
    for private in ("Sam Synthetic", "Leeds", "12", str(MECHANIC.concept_id), MECHANIC.esco_uri):
        assert private not in prompt  # no name, place, hours, IDs or links (SEC-05)
    assert "ready, qualified or likely to be hired" in " ".join(INSTRUCTIONS.split())


@pytest.mark.req("REC1-11", "PROF-09")
def test_the_explanation_reads_no_support_screen_and_carries_no_support_instruction() -> None:
    # Reused from the support screen's own table (never new distress text): an answer that
    # would trigger the screen is quoted like any other, with the same fixed instructions.
    phrase = next(text for _, text, flow in CORPUS if flow and "career" in text)
    assert has_risk_stem(phrase)
    person = document(enjoyed_tasks=[phrase[:120]])
    ctx = build_input(
        discovery_id=DISCOVERY,
        profile_version=1,
        release="esco-v1.2.1-en-csv",
        answers=evidence_of(person),
        occupations=[MECHANIC],
    )

    assert set(ExplanationInput.model_fields) == {
        "format",
        "prompt_version",
        "discovery_id",
        "profile_version",
        "release",
        "answers",
        "occupations",
    }
    assert SUPPORT_TURN_INSTRUCTION not in INSTRUCTIONS
    assert SUPPORT_TURN_INSTRUCTION not in render_prompt(ctx)


@pytest.mark.req("REC1-11", "TEST1-10")
def test_the_fixture_explainer_reads_the_live_prompt_and_passes_the_same_check() -> None:
    ctx = context()

    out = fixture_explanation(prompt_context(render_prompt(ctx)))
    written, found = check_explanation(out, ctx, ProposalOrigin.FIXTURE)

    assert found == []
    assert written is not None
    assert [s.concept_id for s in written.suggestions] == [MECHANIC.concept_id, GARDENER.concept_id]
    assert all(
        c.text.startswith("Demo explainer (synthetic)") for c in written.suggestions[0].claims
    )
    assert fixture_explanation(prompt_context(render_prompt(ctx))) == out  # deterministic


def test_the_prompt_and_schema_fit_the_bounds_the_reservation_assumes() -> None:
    long_items = [f"{'a' * 115} {n}" for n in range(8)]
    busy = document(
        current_role="r" * 120,
        target_titles=["t" * 120, "u" * 120, "v" * 120],
        enjoyed_tasks=long_items,
        confident_tasks=long_items,
        evidenced_tasks=long_items,
        work_style=long_items,
    )
    records = [
        facts(f"{'occupation ' * 9}{n}", "word " * 300, *[f"{'skill ' * 12}{k}" for k in range(9)])
        for n in range(6)
    ]

    ctx = build_input(
        discovery_id=DISCOVERY,
        profile_version=1,
        release="esco-v1.2.1-en-csv",
        answers=evidence_of(busy),
        occupations=records,
    )

    assert prompt_bytes(ctx) <= MAX_PROMPT_BYTES
    assert len(ctx.answers) == 36  # every answer is kept whole: each is a quotable source
    assert all(o.title == r.preferred_label for o, r in zip(ctx.occupations, records, strict=True))
    schema = json.dumps(ExplanationOutput.model_json_schema())
    assert len(schema.encode()) <= SCHEMA_ALLOWANCE_TOKENS
    for keyword in ("minLength", "maxLength", "maxItems", "minItems", "pattern", "format"):
        assert keyword not in schema


def test_a_record_shortened_to_fit_is_cut_at_a_word_and_is_what_the_model_reads() -> None:
    long = facts("bicycle mechanic", "Bicycle mechanics repair bikes. " + "Extra words here. " * 80)

    ctx = context(long)
    [record] = ctx.occupations

    assert record.description.startswith("Bicycle mechanics repair bikes.")
    assert len(record.description) < len(long.description)
    assert not record.description.endswith(" ")
    assert record.description in render_prompt(ctx)


@pytest.mark.req("MODEL-08")
def test_an_attempt_reserves_both_requests_at_their_bounds() -> None:
    # Input bound 8,500 + 1,500 + 2,000 + 1,000 = 13,000 tokens, output 2,000, two requests.
    # Contributor: (13,000 x 100 + 2,000 x 200) x 2 = 3,400,000 nano-USD ($0.0034).
    # Standard: (13,000 x 1,250 + 2,000 x 4,250) x 2 = 49,500,000 nano-USD ($0.0495).
    assert worst_case_nano_usd("muse-spark-1.3-contributor") == 3_400_000
    assert worst_case_nano_usd("muse-spark-1.3") == 49_500_000
    assert worst_case_nano_usd("nessa-fixture-explainer-1") == 0
