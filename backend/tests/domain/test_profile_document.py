import uuid

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.money import Money
from careerwright.profile.commands import restored_answers
from careerwright.profile.document import (
    FIELD_NAMES,
    HARD_CONSTRAINTS,
    MAX_CITIES,
    MAX_TARGETS,
    MAX_TASKS,
    VERSION_2_FIELDS,
    VERSION_3_FIELDS,
    FieldState,
    ProfileDocument,
    ProfileInput,
    TextInput,
    TextListInput,
    apply_profile_input,
    apply_updates,
    empty_profile,
)

SOURCE = uuid.UUID("00000000-0000-4000-8000-000000000001")
LATER_SOURCE = uuid.UUID("00000000-0000-4000-8000-000000000002")


def profile_input(**fields: object) -> ProfileInput:
    values: dict[str, object] = {name: {"state": "unasked"} for name in FIELD_NAMES}
    values.update(fields)
    return ProfileInput.model_validate(values)


def provided(value: object) -> dict[str, object]:
    return {"state": "provided", "value": value}


def test_empty_profile_has_every_field_unasked_and_unsourced() -> None:
    document = empty_profile()

    for name in ProfileInput.model_fields:
        field = getattr(document, name)
        assert (field.state, field.value, field.source_ref_id) == (FieldState.UNASKED, None, None)


@pytest.mark.req("API-04")
@pytest.mark.parametrize("state", ["unknown", "skipped", "prefer_not_to_say", "unasked"])
def test_non_provided_states_carry_no_value_so_unknown_is_never_zero(state: str) -> None:
    with pytest.raises(ValidationError, match="only a provided field has a value"):
        profile_input(
            direct_spend_cap={"state": state, "value": {"minor_units": 0, "currency": "GBP"}}
        )


@pytest.mark.req("API-04")
def test_provided_state_requires_a_value() -> None:
    with pytest.raises(ValidationError, match="a provided field needs a value"):
        profile_input(current_role={"state": "provided"})


@pytest.mark.req("API-04")
def test_skipped_unasked_and_unknown_stay_distinct_after_apply() -> None:
    new = profile_input(
        preferred_name={"state": "prefer_not_to_say"},
        current_role={"state": "unknown"},
        cities={"state": "skipped"},
    )

    document = apply_profile_input(empty_profile(), new, SOURCE)

    assert document.preferred_name.state is FieldState.PREFER_NOT_TO_SAY
    assert document.current_role.state is FieldState.UNKNOWN
    assert document.cities.state is FieldState.SKIPPED
    assert document.target_titles.state is FieldState.UNASKED


def test_money_values_are_integer_minor_units() -> None:
    new = profile_input(direct_spend_cap=provided({"minor_units": 150000, "currency": "GBP"}))

    document = apply_profile_input(empty_profile(), new, SOURCE)

    assert document.direct_spend_cap.value == Money(minor_units=150000, currency="GBP")


def test_money_rejects_fractional_or_negative_amounts() -> None:
    for bad in (1500.5, -1):
        with pytest.raises(ValidationError):
            profile_input(direct_spend_cap=provided({"minor_units": bad, "currency": "GBP"}))


@pytest.mark.req("BND1-03")
def test_a_fourth_city_is_rejected_with_a_typed_error_not_dropped() -> None:
    new = profile_input(cities=provided(["Leeds", "York", "Hull", "Bradford"]))

    with pytest.raises(CareerwrightError) as raised:
        apply_profile_input(empty_profile(), new, SOURCE)

    assert raised.value.code is ErrorCode.LIMIT_EXCEEDED
    assert raised.value.details == {"field": "cities", "limit": MAX_CITIES}


@pytest.mark.req("BND1-03")
def test_a_fourth_target_is_rejected_with_a_typed_error() -> None:
    new = profile_input(target_titles=provided(["A", "B", "C", "D"]))

    with pytest.raises(CareerwrightError) as raised:
        apply_profile_input(empty_profile(), new, SOURCE)

    assert raised.value.code is ErrorCode.LIMIT_EXCEEDED
    assert raised.value.details == {"field": "target_titles", "limit": MAX_TARGETS}


@pytest.mark.req("BND1-03")
def test_three_cities_and_three_targets_are_accepted() -> None:
    new = profile_input(
        cities=provided(["Leeds", "York", "Bath"]), target_titles=provided(["A", "B", "C"])
    )

    document = apply_profile_input(empty_profile(), new, SOURCE)

    assert document.cities.value == ["Leeds", "York", "Bath"]


def test_a_city_is_stored_by_the_list_s_own_name_whatever_the_spelling() -> None:
    new = profile_input(cities=provided(["hull", "Newcastle upon Tyne", "stoke-on-trent"]))

    document = apply_profile_input(empty_profile(), new, SOURCE)

    assert document.cities.value == ["Kingston-upon-Hull", "Newcastle-upon-Tyne", "Stoke on Trent"]


def test_a_place_that_is_not_a_listed_english_city_is_refused_never_guessed() -> None:
    for name in ("Atlantis", "Cardiff", "Shoreditch", "Leeds UK"):
        with pytest.raises(CareerwrightError) as raised:
            apply_profile_input(empty_profile(), profile_input(cities=provided([name])), SOURCE)

        assert raised.value.code is ErrorCode.VALIDATION_FAILED
        assert raised.value.details == {"field": "cities", "reason": "unknown_city"}


def test_two_spellings_of_one_city_are_a_duplicate() -> None:
    with pytest.raises(CareerwrightError) as raised:
        apply_profile_input(
            empty_profile(), profile_input(cities=provided(["Hull", "Kingston upon Hull"])), SOURCE
        )

    assert raised.value.details == {"field": "cities", "reason": "duplicate"}


@pytest.mark.req("REC1-04")
def test_enjoying_believing_and_evidencing_a_task_are_three_separate_fields() -> None:
    new = profile_input(
        enjoyed_tasks=provided(["fixing bikes"]),
        confident_tasks=provided(["training new starters"]),
        evidenced_tasks={"state": "unknown"},
    )

    document = apply_profile_input(empty_profile(), new, SOURCE)

    assert document.enjoyed_tasks.value == ["fixing bikes"]
    assert document.confident_tasks.value == ["training new starters"]
    assert document.evidenced_tasks.state is FieldState.UNKNOWN
    assert document.evidenced_tasks.value is None


def test_task_lists_are_bounded_with_a_typed_error() -> None:
    tasks = [f"task {n}" for n in range(MAX_TASKS + 1)]

    with pytest.raises(CareerwrightError) as raised:
        apply_profile_input(empty_profile(), profile_input(enjoyed_tasks=provided(tasks)), SOURCE)

    assert raised.value.details == {"field": "enjoyed_tasks", "limit": MAX_TASKS}


def test_a_version_1_document_reads_with_the_new_fields_not_asked() -> None:
    later = (*VERSION_2_FIELDS, *VERSION_3_FIELDS)
    stored = {
        "schema_version": "1",
        **{name: {"state": "unasked"} for name in FIELD_NAMES if name not in later},
        "cities": {"state": "provided", "value": ["Leeds"], "source_ref_id": str(SOURCE)},
    }

    document = ProfileDocument.model_validate(stored)

    assert document.schema_version == "3"
    assert document.cities.value == ["Leeds"]
    for name in later:
        assert getattr(document, name).state is FieldState.UNASKED


def test_a_version_2_document_reads_with_work_style_not_asked() -> None:
    stored = {
        "schema_version": "2",
        **{name: {"state": "unasked"} for name in FIELD_NAMES if name not in VERSION_3_FIELDS},
        "enjoyed_tasks": {
            "state": "provided",
            "value": ["fixing bikes"],
            "source_ref_id": str(SOURCE),
        },
    }

    document = ProfileDocument.model_validate(stored)

    assert document.schema_version == "3"
    assert document.enjoyed_tasks.value == ["fixing bikes"]
    assert document.work_style.state is FieldState.UNASKED
    assert document.minimum_salary.state is FieldState.UNASKED


@pytest.mark.req("PROF-04", "STATE-08")
def test_the_salary_floor_is_gross_pay_with_its_period_and_unknown_is_never_zero() -> None:
    floor = {"amount": {"minor_units": 2_800_000, "currency": "GBP"}, "period": "year"}

    document = apply_profile_input(
        empty_profile(), profile_input(minimum_salary=provided(floor)), SOURCE
    )
    unknown = apply_profile_input(
        empty_profile(), profile_input(minimum_salary={"state": "unknown"}), SOURCE
    )

    assert document.minimum_salary.value is not None
    assert document.minimum_salary.value.model_dump() == {**floor, "basis": "gross"}
    assert (unknown.minimum_salary.state, unknown.minimum_salary.value) == (
        FieldState.UNKNOWN,
        None,
    )
    hourly = provided({"amount": {"minor_units": 1250, "currency": "GBP"}, "period": "hour"})
    kept = apply_profile_input(empty_profile(), profile_input(minimum_salary=hourly), SOURCE)
    assert kept.minimum_salary.value is not None
    assert kept.minimum_salary.value.period == "hour"  # never annualised without hours
    with pytest.raises(ValidationError):
        profile_input(minimum_salary=provided({**floor, "period": "fortnight"}))
    with pytest.raises(ValidationError):
        profile_input(minimum_salary=provided({**floor, "basis": "net"}))
    # "No floor" is Unknown or Skipped, never a confirmed £0 (Task 6 review A-M7).
    with pytest.raises(ValidationError):
        profile_input(
            minimum_salary=provided({**floor, "amount": {"minor_units": 0, "currency": "GBP"}})
        )


@pytest.mark.req("STATE-08", "VERSIONS-01")
def test_a_stored_floor_of_nothing_from_before_the_rule_still_reads() -> None:
    # Re-review N-M2: "more than £0" is an input rule; a version saved before it still
    # opens (read, history, export and revert would otherwise fail).
    stored = empty_profile().model_dump(mode="json")
    stored["minimum_salary"] = {
        "state": "provided",
        "value": {"amount": {"minor_units": 0, "currency": "GBP"}, "period": "year"},
        "source_ref_id": str(SOURCE),
    }

    document = ProfileDocument.model_validate(stored)

    assert document.minimum_salary.value is not None
    assert document.minimum_salary.value.amount.minor_units == 0
    # Undoing to that version refuses in words, never a 500 (re-review 2, M-3).
    with pytest.raises(CareerwrightError) as refused:
        restored_answers(document)
    assert refused.value.details == {"field": "minimum_salary", "reason": "no_longer_valid"}


@pytest.mark.req("REC1-01", "REC1-03")
def test_work_style_is_an_optional_described_preference_never_a_limit() -> None:
    new = profile_input(work_style=provided(["outdoors", "a small team"]))

    document = apply_profile_input(empty_profile(), new, SOURCE)

    assert document.work_style.value == ["outdoors", "a small team"]
    assert "work_style" not in HARD_CONSTRAINTS  # it informs suggestions, never excludes
    skipped = apply_profile_input(
        empty_profile(), profile_input(work_style={"state": "skipped"}), SOURCE
    )
    assert (skipped.work_style.state, skipped.work_style.value) == (FieldState.SKIPPED, None)
    with pytest.raises(CareerwrightError) as raised:
        apply_profile_input(
            empty_profile(),
            profile_input(work_style=provided([f"style {n}" for n in range(MAX_TASKS + 1)])),
            SOURCE,
        )
    assert raised.value.details == {"field": "work_style", "limit": MAX_TASKS}


@pytest.mark.req("PROF-07")
def test_a_partial_update_changes_only_its_fields_and_cites_only_its_source() -> None:
    first = apply_profile_input(
        empty_profile(),
        profile_input(current_role=provided("Shift supervisor"), cities=provided(["Leeds"])),
        SOURCE,
    )

    second, changed = apply_updates(
        first,
        {
            "cities": (
                TextListInput(state=FieldState.PROVIDED, value=["Leeds", "York"]),
                LATER_SOURCE,
            ),
            # The same answer again.
            "current_role": (
                TextInput(state=FieldState.PROVIDED, value="Shift supervisor"),
                LATER_SOURCE,
            ),
        },
    )

    assert changed == ["cities"]
    assert second.cities.source_ref_id == LATER_SOURCE
    assert second.current_role.source_ref_id == SOURCE  # unchanged answers keep their source
    assert second.target_titles == first.target_titles


def test_an_update_naming_something_that_is_not_a_profile_field_is_refused() -> None:
    with pytest.raises(CareerwrightError) as raised:
        apply_updates(
            empty_profile(),
            {"api_key": (TextListInput(state=FieldState.UNKNOWN), SOURCE)},
        )

    assert raised.value.details == {"field": "api_key", "reason": "not_a_field"}


@pytest.mark.req("PROF-04")
def test_limits_targets_work_areas_and_hours_are_the_hard_constraints() -> None:
    expected = {
        "cities",
        "target_titles",
        "weekly_study_hours",
        "direct_spend_cap",
        "monthly_payment_cap",
        "minimum_salary",  # added by the product owner (H-11, 2026-10-28)
    }
    assert expected == HARD_CONSTRAINTS


def test_duplicate_cities_differing_only_in_case_are_rejected() -> None:
    new = profile_input(cities=provided(["Leeds", " leeds"]))

    with pytest.raises(CareerwrightError) as raised:
        apply_profile_input(empty_profile(), new, SOURCE)

    assert raised.value.code is ErrorCode.VALIDATION_FAILED
    assert raised.value.details["field"] == "cities"


def test_changed_fields_cite_the_new_source_and_unchanged_fields_keep_theirs() -> None:
    first = apply_profile_input(
        empty_profile(),
        profile_input(current_role=provided("Shift supervisor"), cities=provided(["Leeds"])),
        SOURCE,
    )

    second = apply_profile_input(
        first,
        profile_input(current_role=provided("Shift supervisor"), cities=provided(["York"])),
        LATER_SOURCE,
    )

    assert second.current_role.source_ref_id == SOURCE
    assert second.cities.source_ref_id == LATER_SOURCE
    assert second.preferred_name.source_ref_id is None  # still unasked


def test_returning_a_field_to_unasked_drops_its_source() -> None:
    first = apply_profile_input(empty_profile(), profile_input(cities=provided(["Leeds"])), SOURCE)

    second = apply_profile_input(first, profile_input(), LATER_SOURCE)

    assert (second.cities.state, second.cities.source_ref_id) == (FieldState.UNASKED, None)


@given(st.lists(st.sampled_from(["Leeds", "York", "Wells", "Bath", "Ely"]), unique=True))
def test_city_count_property_accepts_at_most_three(cities: list[str]) -> None:
    new = profile_input(cities=provided(cities))

    if len(cities) <= MAX_CITIES:
        assert apply_profile_input(empty_profile(), new, SOURCE).cities.value == cities
    else:
        with pytest.raises(CareerwrightError):
            apply_profile_input(empty_profile(), new, SOURCE)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ProfileInput.model_validate({"preferred_name": {"state": "unasked"}, "api_key": "x"})
