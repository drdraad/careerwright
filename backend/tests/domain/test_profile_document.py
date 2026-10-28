import uuid

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from nessa.errors import ErrorCode, NessaError
from nessa.money import Money
from nessa.profile.document import (
    MAX_CITIES,
    MAX_TARGETS,
    FieldState,
    ProfileInput,
    apply_profile_input,
    empty_profile,
)

SOURCE = uuid.UUID("00000000-0000-4000-8000-000000000001")
LATER_SOURCE = uuid.UUID("00000000-0000-4000-8000-000000000002")


def profile_input(**fields: object) -> ProfileInput:
    unasked = {"state": "unasked"}
    values: dict[str, object] = {
        "preferred_name": unasked,
        "current_role": unasked,
        "cities": unasked,
        "target_titles": unasked,
        "weekly_study_hours": unasked,
        "direct_spend_cap": unasked,
        "monthly_payment_cap": unasked,
    }
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

    with pytest.raises(NessaError) as raised:
        apply_profile_input(empty_profile(), new, SOURCE)

    assert raised.value.code is ErrorCode.LIMIT_EXCEEDED
    assert raised.value.details == {"field": "cities", "limit": MAX_CITIES}


@pytest.mark.req("BND1-03")
def test_a_fourth_target_is_rejected_with_a_typed_error() -> None:
    new = profile_input(target_titles=provided(["A", "B", "C", "D"]))

    with pytest.raises(NessaError) as raised:
        apply_profile_input(empty_profile(), new, SOURCE)

    assert raised.value.code is ErrorCode.LIMIT_EXCEEDED
    assert raised.value.details == {"field": "target_titles", "limit": MAX_TARGETS}


@pytest.mark.req("BND1-03")
def test_three_cities_and_three_targets_are_accepted() -> None:
    new = profile_input(
        cities=provided(["Leeds", "York", "Hull"]), target_titles=provided(["A", "B", "C"])
    )

    document = apply_profile_input(empty_profile(), new, SOURCE)

    assert document.cities.value == ["Leeds", "York", "Hull"]


def test_duplicate_cities_differing_only_in_case_are_rejected() -> None:
    new = profile_input(cities=provided(["Leeds", " leeds"]))

    with pytest.raises(NessaError) as raised:
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


@given(st.lists(st.sampled_from(["Leeds", "York", "Hull", "Bath", "Ely"]), unique=True))
def test_city_count_property_accepts_at_most_three(cities: list[str]) -> None:
    new = profile_input(cities=provided(cities))

    if len(cities) <= MAX_CITIES:
        assert apply_profile_input(empty_profile(), new, SOURCE).cities.value == cities
    else:
        with pytest.raises(NessaError):
            apply_profile_input(empty_profile(), new, SOURCE)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ProfileInput.model_validate({"preferred_name": {"state": "unasked"}, "api_key": "x"})
