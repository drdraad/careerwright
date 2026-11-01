"""The InterviewTurn contract: deterministic validation of model output against the turn's
context (PROF-02, PROF-04, PROF-05, PROF-06, STATE-08, TEST1-10). Semantic checks only:
no assertion depends on model prose."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from careerwright.money import Money
from careerwright.profile.document import (
    FIELD_NAMES,
    HARD_CONSTRAINTS,
    PayPeriod,
    ProfileInput,
    QualificationAnswer,
    QualificationStatus,
    SalaryFloor,
    apply_profile_input,
    empty_profile,
)
from careerwright.profile.interview import (
    CONTEXT_MARKER,
    INSTRUCTIONS,
    MAX_PROMPT_BYTES,
    PROMPT_VERSION,
    SCHEMA_ALLOWANCE_TOKENS,
    ContextMessage,
    InterviewTurnOutput,
    ProfileField,
    ProposalOrigin,
    TurnInput,
    check_turn,
    context_profile,
    instructions,
    prompt_bytes,
    render_prompt,
    worst_case_nano_usd,
)
from careerwright.profile.records import Basis, ConversationMode, EntryMode
from careerwright.profile.safety import SUPPORT_TURN_INSTRUCTION, has_risk_stem

M1 = uuid.UUID("00000000-0000-4000-8000-000000000001")
M2 = uuid.UUID("00000000-0000-4000-8000-000000000002")
AT = datetime(2027, 1, 1, tzinfo=UTC)


def context(*texts: str) -> TurnInput:
    ids = [M1, M2]
    return TurnInput(
        profile_version=3,
        profile=context_profile(empty_profile()),
        messages=[
            ContextMessage(ref=f"m{i}", message_id=ids[i - 1], text=text, sent_at=AT)
            for i, text in enumerate(texts, start=1)
        ],
        replies={},
    )


def update(field: str, **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "field": field,
        "state": "provided",
        "text": None,
        "items": None,
        "basis": "stated",
        "message_refs": ["m1"],
        "reason": "You said so.",
    }
    return {**base, **overrides}


def output(*updates: dict[str, Any], **overrides: Any) -> InterviewTurnOutput:
    body: dict[str, Any] = {
        "reply": "Thanks, that helps.",
        "proposed_updates": list(updates),
        "next_question": "How many hours a week could you study?",
        "missing_critical_fields": ["weekly_study_hours"],
        "ready_for_review": True,
    }
    return InterviewTurnOutput.model_validate({**body, **overrides})


def problems(out: InterviewTurnOutput, ctx: TurnInput | None = None) -> list[str]:
    proposal, found = check_turn(out, ctx or context("I live near Leeds."), ProposalOrigin.MODEL)
    assert (proposal is None) == bool(found)  # never both, never neither
    return found


@pytest.mark.req("PROF-05", "TEST1-10")
def test_a_valid_output_becomes_a_proposal_citing_message_ids_with_server_assigned_ids() -> None:
    ctx = context("I could work in Leeds or York.", "I'd spend about £1,500.50 at most.")
    out = output(
        update("cities", items=["Leeds", "york"], message_refs=["m1"]),
        update("direct_spend_cap", text="1500.50", basis="inferred", message_refs=["m2", "m2"]),
        update("current_role", text="Warehouse supervisor", message_refs=["m1", "m2"]),
    )

    proposal, found = check_turn(out, ctx, ProposalOrigin.MODEL)

    assert found == []
    assert proposal is not None
    assert proposal.profile_version == 3
    by_field = {c.field: c for c in proposal.changes}
    assert [c.change_id for c in proposal.changes] == ["c1", "c2", "c3"]
    assert by_field[ProfileField.CITIES].value == ["Leeds", "York"]  # the list's own names
    assert by_field[ProfileField.CITIES].message_ids == [M1]
    spend = by_field[ProfileField.DIRECT_SPEND_CAP]
    assert spend.value == Money(minor_units=150_050, currency="GBP")  # integer minor units
    assert spend.message_ids == [M2]  # a repeated ref is cited once
    assert spend.basis is Basis.INFERRED
    assert by_field[ProfileField.CURRENT_ROLE].message_ids == [M1, M2]


def basis_of(out: InterviewTurnOutput, ctx: TurnInput) -> dict[str, Basis]:
    proposal, found = check_turn(out, ctx, ProposalOrigin.MODEL)
    assert proposal is not None, found
    return {c.field.value: c.basis for c in proposal.changes}


@pytest.mark.req("PROF-01", "PROF-05")
def test_stated_is_kept_only_when_the_cited_messages_contain_the_value() -> None:
    ctx = context("I'm a warehouse supervisor in LEEDS; I'd spend £1,500.", "About 6 hours a week.")
    out = output(
        update("cities", items=["Leeds"]),
        update("current_role", text="Warehouse  Supervisor"),
        update("direct_spend_cap", text="1500"),  # "£1,500": digit grouping aside
        update("weekly_study_hours", text="6", message_refs=["m2"]),
        update("target_titles", items=["Plumber"]),  # never said
        update("monthly_payment_cap", text="150"),  # never said: not part of "1500"
        update("enjoyed_tasks", items=["leading a team"], basis="inferred"),
    )

    assert basis_of(out, ctx) == {
        "cities": Basis.STATED,
        "current_role": Basis.STATED,
        "direct_spend_cap": Basis.STATED,
        "weekly_study_hours": Basis.STATED,
        "target_titles": Basis.INFERRED,  # the model's claim alone is not enough
        "monthly_payment_cap": Basis.INFERRED,
        "enjoyed_tasks": Basis.INFERRED,  # an inference stays one
    }


@pytest.mark.req("PROF-01")
def test_a_stated_value_must_appear_in_the_messages_it_cites_not_elsewhere() -> None:
    ctx = context("I could work in York.", "Hello again.")

    cited_elsewhere = output(update("cities", items=["York"], message_refs=["m2"]))

    assert basis_of(cited_elsewhere, ctx) == {"cities": Basis.INFERRED}


@pytest.mark.req("PROF-01")
def test_a_list_is_stated_when_its_new_items_appear_and_held_items_need_no_quote() -> None:
    held = apply_profile_input(
        empty_profile(),
        ProfileInput.model_validate(
            {
                **{name: {"state": "unasked"} for name in FIELD_NAMES},
                "cities": {"state": "provided", "value": ["York"]},
            }
        ),
        uuid.uuid4(),
    )
    ctx = context("Leeds would work too.").model_copy(update={"profile": context_profile(held)})

    complete = output(update("cities", items=["York", "Leeds"]))
    invented = output(update("cities", items=["York", "Leeds", "Bath"]))

    assert basis_of(complete, ctx) == {"cities": Basis.STATED}
    assert basis_of(invented, ctx) == {"cities": Basis.INFERRED}


@pytest.mark.req("PROF-01", "STATE-08")
def test_an_answer_without_a_value_to_quote_is_shown_as_inferred() -> None:
    ctx = context("I'd rather not say what I can spend.")

    declined = output(update("direct_spend_cap", state="prefer_not_to_say"))

    assert basis_of(declined, ctx) == {"direct_spend_cap": Basis.INFERRED}


@pytest.mark.req("PROF-04")
def test_every_proposed_limit_or_target_is_marked_as_needing_explicit_confirmation() -> None:
    ctx = context(
        "Leeds, 6 hours a week, £100 a month, £900 in total; I want to be a plumber "
        "earning at least £26,000 a year."
    )
    out = output(
        *(
            update(name, text=text, items=items)
            for name, text, items in (
                ("cities", None, ["Leeds"]),
                ("weekly_study_hours", "6", None),
                ("monthly_payment_cap", "100", None),
                ("direct_spend_cap", "900", None),
                ("target_titles", None, ["Plumber"]),
                ("minimum_salary", "26000 per year", None),
                ("enjoyed_tasks", None, ["fixing things"]),
            )
        )
    )

    proposal, _ = check_turn(out, ctx, ProposalOrigin.MODEL)

    assert proposal is not None
    assert {c.field.value for c in proposal.changes if c.hard_constraint} == HARD_CONSTRAINTS
    assert [c.field for c in proposal.changes if not c.hard_constraint] == [
        ProfileField.ENJOYED_TASKS
    ]


@pytest.mark.req("PROF-06")
def test_only_profile_fields_can_be_named_so_keys_and_commitments_are_unreachable() -> None:
    assert [f.value for f in ProfileField] == list(FIELD_NAMES)
    schema = json.dumps(InterviewTurnOutput.model_json_schema())
    for forbidden in ("api_key", "credential", "commitment", "plan", "spend_limit"):
        assert forbidden not in schema
    with pytest.raises(ValueError, match="field"):
        output(update("api_key", text="sk-123"))


@pytest.mark.parametrize(
    ("bad", "expected"),
    [
        (update("cities", items=["Leeds"], message_refs=[]), "cite"),
        (update("cities", items=["Leeds"], message_refs=["m7"]), "cite"),
        (update("cities", items=["Atlantis"]), "English city"),
        (update("cities", items=["Leeds", "York", "Bath", "Ely"]), "At most 3"),
        (update("cities", text="Leeds"), "list field"),
        (update("current_role", items=["Analyst"]), "needs text"),
        (update("direct_spend_cap", text="1500.555"), "pounds as digits"),
        (update("direct_spend_cap", text="-5"), "pounds as digits"),
        (update("direct_spend_cap", text="about 1500"), "pounds as digits"),
        (update("weekly_study_hours", text="169"), "0 to 168"),
        (update("weekly_study_hours", state="unknown", text="6"), "no text"),
        (update("current_role", text="x" * 121), "not valid"),
        (update("current_role", text="Analyst", reason=""), "reason"),
    ],
)
def test_an_invalid_update_is_a_problem_the_repair_request_can_name(
    bad: dict[str, Any], expected: str
) -> None:
    found = problems(output(bad))

    assert any(expected in problem for problem in found), found


def test_two_updates_to_one_field_and_out_of_bounds_text_are_problems() -> None:
    assert problems(output(update("current_role", text="A"), update("current_role", text="B")))
    assert problems(output(reply=""))
    assert problems(output(reply="x" * 1_201))
    assert problems(output(next_question=""))
    assert problems(output(missing_critical_fields=["weekly_study_hours", "weekly_study_hours"]))


@pytest.mark.req("STATE-08")
@pytest.mark.parametrize("state", ["unknown", "skipped", "prefer_not_to_say"])
def test_unknown_skip_and_prefer_not_to_say_are_proposable_and_never_zero(state: str) -> None:
    proposal, _ = check_turn(
        output(update("direct_spend_cap", state=state)),
        context("I'd rather not say what I can spend."),
        ProposalOrigin.MODEL,
    )

    assert proposal is not None
    [change] = proposal.changes
    assert (change.state.value, change.value) == (state, None)
    assert change.field_input().value is None


@pytest.mark.req("STATE-11")
def test_i_havent_had_a_job_yet_is_proposable_for_the_role_alone_with_no_value() -> None:
    proposal, found = check_turn(
        output(update("current_role", state="no_job_yet", basis="inferred")),
        context("I haven't had a job yet."),
        ProposalOrigin.MODEL,
    )

    assert found == []
    assert proposal is not None
    [change] = proposal.changes
    assert (change.state.value, change.value, change.basis) == ("no_job_yet", None, Basis.INFERRED)
    assert change.field_input().state.value == "no_job_yet"
    elsewhere = problems(
        output(update("work_status", state="no_job_yet")), context("I haven't had a job yet.")
    )
    assert elsewhere == ["work_status: Only the current role takes that answer."]
    titled = problems(
        output(update("current_role", state="no_job_yet", text="student")),
        context("I haven't had a job yet."),
    )
    assert titled == ["current_role: a no_job_yet answer has no text or items"]


@pytest.mark.req("PROF-13")
def test_what_the_person_is_doing_now_is_proposed_as_a_code_and_read_as_inferred() -> None:
    ctx = context("I'm in Year 13 at school.")
    proposal, found = check_turn(
        output(update("work_status", text="in_education_or_training")), ctx, ProposalOrigin.MODEL
    )

    assert found == []
    assert proposal is not None
    [change] = proposal.changes
    assert change.value == "in_education_or_training"
    assert change.basis is Basis.INFERRED  # a reading of their words, never their words
    assert change.hard_constraint is False
    assert problems(output(update("work_status", text="retired")), ctx) == [
        "work_status: the value is not valid for this field"
    ]


@pytest.mark.req("PROF-13")
def test_a_qualification_is_proposed_achieved_or_expected_stated_only_from_their_words() -> None:
    ctx = context("I got GCSE maths last year and I'm doing A-level biology now.")
    proposal, found = check_turn(
        output(
            update(
                "qualifications",
                items=["achieved: GCSE maths", "expected: A-level biology"],
            )
        ),
        ctx,
        ProposalOrigin.MODEL,
    )

    assert found == []
    assert proposal is not None
    [change] = proposal.changes
    assert change.value == [
        QualificationAnswer(name="GCSE maths", status=QualificationStatus.ACHIEVED),
        QualificationAnswer(name="A-level biology", status=QualificationStatus.EXPECTED),
    ]
    # Each name appears in the message it cites, but each status is a reading (fix round 1).
    assert change.basis is Basis.INFERRED
    assert change.field_input().value == change.value
    unsaid = check_turn(
        output(update("qualifications", items=["achieved: A-level chemistry"])),
        ctx,
        ProposalOrigin.MODEL,
    )[0]
    assert unsaid is not None
    assert unsaid.changes[0].basis is Basis.INFERRED
    assert 'qualifications: give each as "achieved: name" or "expected: name"' in problems(
        output(update("qualifications", items=["A-level biology"])), ctx
    )


@pytest.mark.req("PROF-13")
def test_a_status_the_person_never_said_is_never_shown_as_their_words() -> None:
    # Task 6f review I1: the name is quoted, the status is not; "working" is not a status said.
    taking = check_turn(
        output(update("qualifications", items=["achieved: A-level biology"])),
        context("I am taking A-level biology this year."),
        ProposalOrigin.MODEL,
    )[0]
    working = check_turn(
        output(update("work_status", text="working")),
        context("I am working towards my A-levels."),
        ProposalOrigin.MODEL,
    )[0]

    assert taking is not None
    assert working is not None
    assert taking.changes[0].basis is Basis.INFERRED
    assert working.changes[0].basis is Basis.INFERRED


@pytest.mark.req("STATE-11", "PROF-14")
def test_the_instructions_say_someone_may_not_have_had_a_job_yet_and_the_version_moved() -> None:
    assert PROMPT_VERSION == "interview-turn-5"
    assert (
        "Someone may not have had a job yet: ask about school or college, volunteering, "
        "caring, clubs and hobbies; never treat no job as a gap" in " ".join(INSTRUCTIONS.split())
    )
    assert "no_job_yet" in INSTRUCTIONS
    assert "this change" not in INSTRUCTIONS
    assert "the change" not in INSTRUCTIONS


def test_a_reply_without_proposals_is_valid() -> None:
    proposal, found = check_turn(
        output(next_question=None, missing_critical_fields=[], ready_for_review=False),
        context("Hello."),
        ProposalOrigin.FIXTURE,
    )

    assert found == []
    assert proposal is not None
    assert (proposal.changes, proposal.origin) == ([], ProposalOrigin.FIXTURE)


def test_the_model_sees_the_minimum_profile_subset_without_names_or_source_ids() -> None:
    filled = apply_profile_input(
        empty_profile(),
        ProfileInput.model_validate(
            {
                **{name: {"state": "unasked"} for name in FIELD_NAMES},
                "preferred_name": {"state": "provided", "value": "PRIVATE-NAME"},
                "cities": {"state": "provided", "value": ["Leeds"]},
            }
        ),
        uuid.UUID("00000000-0000-4000-8000-0000000000ff"),
    )
    ctx = TurnInput(
        profile_version=1,
        profile=context_profile(filled),
        messages=[ContextMessage(ref="m1", message_id=M1, text="Hi", sent_at=AT)],
        replies={},
    )

    prompt = render_prompt(ctx)

    assert "PRIVATE-NAME" not in prompt
    assert "0000000000ff" not in prompt  # no source IDs
    assert str(M1) not in prompt  # messages are cited by ref, not by ID
    assert '"Leeds"' in prompt


@pytest.mark.req("PROF-04", "STATE-08")
def test_a_proposed_salary_floor_is_gross_pay_with_its_period_and_a_hard_constraint() -> None:
    ctx = context("I won't take less than £28,000 a year.", "Or £12.50 an hour for shifts.")

    proposal, found = check_turn(
        output(update("minimum_salary", text="28000 per year")), ctx, ProposalOrigin.MODEL
    )
    hourly, _ = check_turn(
        output(update("minimum_salary", text="12.50 per hour", message_refs=["m2"])),
        ctx,
        ProposalOrigin.MODEL,
    )
    bare, _ = check_turn(output(update("minimum_salary", text="28000")), ctx, ProposalOrigin.MODEL)

    assert found == []
    assert proposal is not None
    [change] = proposal.changes
    assert change.hard_constraint
    assert change.basis is Basis.STATED  # the amount is in the cited message
    assert change.value == SalaryFloor(
        amount=Money(minor_units=2_800_000, currency="GBP"), period=PayPeriod.YEAR
    )
    assert hourly is not None
    assert hourly.changes[0].value == SalaryFloor(
        amount=Money(minor_units=1250, currency="GBP"), period=PayPeriod.HOUR
    )
    assert bare is not None
    assert bare.changes[0].value == change.value  # annual unless the person says otherwise
    assert problems(output(update("minimum_salary", text="28k-ish")), ctx)
    declined, _ = check_turn(
        output(update("minimum_salary", state="prefer_not_to_say")), ctx, ProposalOrigin.MODEL
    )
    assert declined is not None
    assert declined.changes[0].value is None  # never zero


@pytest.mark.req("PROF-04", "PROF-01")
def test_a_salary_floor_is_stated_only_when_the_cited_words_give_its_period() -> None:
    # Task 6 review A-I-4: the period is part of the value, so it must be quoted too.
    hourly = context("I will not work for less than £12 an hour.")

    def basis(text: str, ctx: TurnInput = hourly) -> Basis:
        proposal, found = check_turn(
            output(update("minimum_salary", text=text)), ctx, ProposalOrigin.MODEL
        )
        assert found == []
        assert proposal is not None
        return proposal.changes[0].basis

    assert basis("12 per hour") is Basis.STATED
    assert basis("12 per year") is Basis.INFERRED  # the wrong period is never "stated"
    assert basis("12") is Basis.INFERRED  # a defaulted period is not the person's words
    assert basis("26000 per year", context("Anything under £26,000 annually won't work.")) is (
        Basis.STATED
    )
    assert basis("500 per week", context("I get paid £500 weekly now.")) is Basis.STATED
    assert basis("2000 per month", context("I need £2,000 a month.")) is Basis.STATED
    assert basis("0.50 per hour", context("I need 50p more.")) is Basis.INFERRED


@pytest.mark.req("PROF-08")
def test_the_one_question_lives_only_in_next_question_never_in_the_reply() -> None:
    # Task 6 review A-I-6: the web app shows the reply and the question apart, so a question
    # repeated in the reply would be asked twice.
    ctx = context("I could work in York.")

    assert "only in next_question" in INSTRUCTIONS
    assert problems(output(), ctx) == []
    assert problems(output(reply="Thanks. Where could you work?"), ctx) == [
        "reply: no question here; ask the one question only in next_question"
    ]
    assert problems(output(next_question="Where could you work? And when?"), ctx) == [
        "next_question: one question only"
    ]
    # Re-review N-M7: with no next question there is nothing to repeat, so a "?" in the
    # reply (rhetorical or quoted) costs no paid repair.
    assert problems(output(reply="Where next? We'll see.", next_question=None), ctx) == []


@pytest.mark.req("PROF-04", "STATE-08")
def test_a_proposed_salary_floor_of_nothing_is_refused() -> None:
    ctx = context("I don't mind about pay, £0 is fine.")

    assert problems(output(update("minimum_salary", text="0 per year")), ctx)


@pytest.mark.req("PROF-08", "PROF-09")
def test_the_prompt_says_how_the_person_chose_to_start_and_to_be_spoken_to() -> None:
    ctx = TurnInput(
        profile_version=1,
        profile=context_profile(empty_profile()),
        messages=[ContextMessage(ref="m1", message_id=M1, text="Hi", sent_at=AT)],
        replies={},
        entry_mode=EntryMode.SURE,
        conversation_mode=ConversationMode.GENTLE,
    )

    payload = json.loads(render_prompt(ctx).removeprefix(CONTEXT_MARKER))

    assert (payload["entry"], payload["mode"]) == ("sure", "gentle")
    assert ctx.prompt_version == "interview-turn-5"


@pytest.mark.req("PROF-09")
def test_the_smaller_step_instruction_is_added_only_for_a_turn_whose_message_has_a_risk_stem() -> (
    None
):
    flagged = context("I took my life savings out to retrain.")
    plain = context("I could work in Leeds.")
    earlier = context("I took my life savings out to retrain.", "I could work in Leeds.")

    assert instructions(flagged) == f"{INSTRUCTIONS}\n{SUPPORT_TURN_INSTRUCTION}\n"
    assert instructions(plain) == INSTRUCTIONS
    assert instructions(earlier) == INSTRUCTIONS  # that turn only
    assert prompt_bytes(flagged) == len(instructions(flagged).encode()) + len(
        render_prompt(flagged).encode()
    )
    # The model never sees a label naming the screen or what it matched: the context it
    # reads has the same shape either way, and the added words name neither.
    shown = json.loads(render_prompt(flagged).removeprefix(CONTEXT_MARKER))
    assert shown.keys() == json.loads(render_prompt(plain).removeprefix(CONTEXT_MARKER)).keys()
    added = SUPPORT_TURN_INSTRUCTION.casefold()
    assert not has_risk_stem(added)
    for label in ("support", "screen", "flag", "risk", "safety", "distress", "crisis", "life"):
        assert label not in added, label


@pytest.mark.req("PROF-09")
def test_a_turn_whose_message_has_a_risk_stem_never_keeps_a_next_question() -> None:
    # Fix round 5: the server drops it, whatever the model wrote, and spends no repair on
    # it; the rest of the proposal is kept. Only the current message counts.
    asked = output(update("cities", items=["Leeds"]), reply="Thanks. Where next? We'll see.")
    flagged = context("I could work in Leeds. I took my life savings out to retrain.")
    earlier = context("I took my life savings out to retrain.", "I could work in Leeds.")

    dropped, problems_found = check_turn(asked, flagged, ProposalOrigin.MODEL)
    kept, _ = check_turn(
        output(update("cities", items=["Leeds"], message_refs=["m2"])),
        earlier,
        ProposalOrigin.MODEL,
    )

    assert problems_found == []
    assert dropped is not None
    assert dropped.next_question is None
    assert [c.field for c in dropped.changes] == [ProfileField.CITIES]
    assert dropped.missing_critical_fields == [ProfileField.WEEKLY_STUDY_HOURS]
    assert kept is not None
    assert kept.next_question == "How many hours a week could you study?"


def test_an_input_sealed_before_preferences_existed_still_opens() -> None:
    sealed = context("Hi").model_dump(mode="json")
    del sealed["entry_mode"], sealed["conversation_mode"]
    sealed["prompt_version"] = "interview-turn-1"

    opened = TurnInput.model_validate(sealed)

    assert (opened.entry_mode, opened.conversation_mode) == (None, ConversationMode.PRACTICAL)


@pytest.mark.req("REC1-02", "PROF-09")
@pytest.mark.parametrize(
    "overrides",
    [
        {"reply": "It sounds like you might be depressed."},
        {"next_question": "Have you been assessed for ADHD?"},
        {"reply": "As an ISTP you would like hands-on work."},
        {"reply": "You are a 92% match for maintenance work."},
    ],
)
def test_output_inferring_a_diagnosis_type_or_match_percentage_is_repaired(
    overrides: dict[str, Any],
) -> None:
    found = problems(output(**overrides), context("I liked fixing the machines more."))

    assert any("did not mention" in problem for problem in found)


@pytest.mark.req("REC1-02")
def test_a_reason_or_value_inferring_a_trait_is_repaired_too() -> None:
    found = problems(
        output(update("work_style", items=["quiet work"], reason="You seem introverted.")),
        context("I like quiet work."),
    )

    assert any("did not mention" in problem for problem in found)


@pytest.mark.req("PROF-09", "REC1-02")
def test_a_named_condition_is_acknowledged_but_never_recorded_in_a_career_field() -> None:
    ctx = context("I have dyslexia, so long written tests are hard. I'm good at fixing bikes.")

    acknowledged = problems(
        output(
            update("confident_tasks", items=["fixing bikes"]),
            reply="Thanks for telling me about your dyslexia.",
            next_question="Which adjustment would help with written tests?",
        ),
        ctx,
    )
    recorded = problems(output(update("confident_tasks", items=["coping with dyslexia"])), ctx)

    assert acknowledged == []
    assert recorded == [
        "confident_tasks: health conditions are not recorded in career fields; ask which "
        "adjustment would help instead"
    ]


def test_the_prompt_and_schema_fit_the_bounds_the_reservation_assumes() -> None:
    long_message = "I have worked in warehouses for years. " * 50  # about 2,000 characters
    assert prompt_bytes(context(long_message[:2000])) <= MAX_PROMPT_BYTES
    flagged = "I took my life savings out. " + long_message  # with the smaller-step instruction
    assert prompt_bytes(context(flagged[:2000])) <= MAX_PROMPT_BYTES
    schema = json.dumps(InterviewTurnOutput.model_json_schema())
    assert len(schema.encode()) <= SCHEMA_ALLOWANCE_TOKENS  # bytes bound tokens
    assert len(INSTRUCTIONS.encode()) < MAX_PROMPT_BYTES // 2


def test_the_output_schema_stays_within_strict_mode() -> None:
    schema = json.dumps(InterviewTurnOutput.model_json_schema())

    for keyword in ("minLength", "maxLength", "maxItems", "minItems", "pattern", "format"):
        assert keyword not in schema


@pytest.mark.req("MODEL-08")
def test_an_attempt_reserves_both_requests_at_their_bounds() -> None:
    # Input bound 8,500 + 2,500 + 1,500 + 2,000 = 14,500 tokens, output 1,500, two requests.
    # Contributor: (14,500 x 100 + 1,500 x 200) x 2 = 3,500,000 nano-USD ($0.0035).
    # Standard: (14,500 x 1,250 + 1,500 x 4,250) x 2 = 49,000,000 nano-USD ($0.049).
    # (That every step retry fits the default run limit: tests/domain/test_spend.py.)
    assert worst_case_nano_usd("muse-spark-1.3-contributor") == 3_500_000
    assert worst_case_nano_usd("muse-spark-1.3") == 49_000_000
    assert worst_case_nano_usd("careerwright-fixture-interviewer-1") == 0
