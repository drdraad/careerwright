"""The InterviewTurn contract: deterministic validation of model output against the turn's
context (PROF-02, PROF-04, PROF-05, PROF-06, STATE-08, TEST1-10). Semantic checks only:
no assertion depends on model prose."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from nessa.identity.model_registry import ModelMode
from nessa.money import Money
from nessa.profile.document import (
    FIELD_NAMES,
    HARD_CONSTRAINTS,
    ProfileInput,
    apply_profile_input,
    empty_profile,
)
from nessa.profile.interview import (
    INSTRUCTIONS,
    MAX_PROMPT_BYTES,
    SCHEMA_ALLOWANCE_TOKENS,
    ContextMessage,
    InterviewTurnOutput,
    ProfileField,
    ProposalOrigin,
    TurnInput,
    check_turn,
    context_profile,
    prompt_bytes,
    render_prompt,
    worst_case_nano_usd,
)
from nessa.profile.records import Basis

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


@pytest.mark.req("PROF-04")
def test_every_proposed_limit_or_target_is_marked_as_needing_explicit_confirmation() -> None:
    ctx = context("Leeds, 6 hours a week, £100 a month, £900 in total; I want to be a plumber.")
    out = output(
        *(
            update(name, text=text, items=items)
            for name, text, items in (
                ("cities", None, ["Leeds"]),
                ("weekly_study_hours", "6", None),
                ("monthly_payment_cap", "100", None),
                ("direct_spend_cap", "900", None),
                ("target_titles", None, ["Plumber"]),
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


def test_the_prompt_and_schema_fit_the_bounds_the_reservation_assumes() -> None:
    long_message = "I have worked in warehouses for years. " * 50  # about 2,000 characters
    assert prompt_bytes(context(long_message[:2000])) <= MAX_PROMPT_BYTES
    schema = json.dumps(InterviewTurnOutput.model_json_schema())
    assert len(schema.encode()) <= SCHEMA_ALLOWANCE_TOKENS  # bytes bound tokens
    assert len(INSTRUCTIONS.encode()) < MAX_PROMPT_BYTES // 2


def test_the_output_schema_stays_within_strict_mode() -> None:
    schema = json.dumps(InterviewTurnOutput.model_json_schema())

    for keyword in ("minLength", "maxLength", "maxItems", "minItems", "pattern", "format"):
        assert keyword not in schema


@pytest.mark.req("MODEL-08")
def test_an_attempt_reserves_both_requests_at_their_bounds_within_the_default_run_limit() -> None:
    # Input bound 8,500 + 2,500 + 1,500 + 2,000 = 14,500 tokens, output 1,500, two requests.
    # Contributor: (14,500 x 100 + 1,500 x 200) x 2 = 3,500,000 nano-USD ($0.0035).
    # Standard: (14,500 x 1,250 + 1,500 x 4,250) x 2 = 49,000,000 nano-USD ($0.049).
    assert worst_case_nano_usd("muse-spark-1.3-contributor") == 3_500_000
    assert worst_case_nano_usd("muse-spark-1.3") == 49_000_000
    assert 2 * worst_case_nano_usd("muse-spark-1.3") <= 100_000_000  # two attempts fit $0.10
    assert ModelMode.FIXTURE.value == "fixture"
    assert worst_case_nano_usd("nessa-fixture-interviewer-1") == 0
