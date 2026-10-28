"""The finite English city list (spec section 3; BND1-04)."""

import dataclasses
import uuid

import pytest

from nessa.catalogue.places import ENGLISH_CITIES, Place, place, resolve_city
from nessa.profile.document import FIELD_NAMES, ProfileInput, apply_profile_input, empty_profile

_SOURCE = uuid.UUID("00000000-0000-4000-8000-0000000000aa")


def test_the_list_is_the_55_english_cities_with_stable_ids_regions_and_timezone() -> None:
    assert len(ENGLISH_CITIES) == 55
    assert len({p.place_id for p in ENGLISH_CITIES}) == 55
    assert {p.region for p in ENGLISH_CITIES} == {
        "North East",
        "North West",
        "Yorkshire and The Humber",
        "East Midlands",
        "West Midlands",
        "East of England",
        "London",
        "South East",
        "South West",
    }
    leeds = resolve_city("Leeds")
    assert leeds is not None
    assert (leeds.place_id, leeds.region_code, leeds.subdivision_code, leeds.timezone) == (
        "gb-eng-leeds",
        "E12000003",
        "GB-ENG",
        "Europe/London",
    )
    assert place("gb-eng-leeds") == leeds


def test_recorded_aliases_resolve_and_unlisted_names_do_not() -> None:
    assert resolve_city("hull") == resolve_city("Kingston-upon-Hull")
    assert resolve_city("Brighton") == resolve_city("Brighton & Hove")
    assert resolve_city("St. Albans") == resolve_city("St Albans")
    for unlisted in ("Cardiff", "Edinburgh", "Shoreditch", "", "Leeds, UK"):
        assert resolve_city(unlisted) is None


@pytest.mark.req("BND1-04")
def test_a_city_is_geography_only_and_choosing_one_sets_nothing_else() -> None:
    fields = {f.name for f in dataclasses.fields(Place)}
    assert fields == {
        "place_id",
        "label",
        "region_code",
        "aliases",
        "country_code",
        "subdivision_code",
        "timezone",
    }  # no residence, nationality, work rights or eligibility
    chosen = ProfileInput.model_validate(
        {
            **{name: {"state": "unasked"} for name in FIELD_NAMES},
            "cities": {"state": "provided", "value": ["Manchester"]},
        }
    )

    document = apply_profile_input(empty_profile(), chosen, source_ref_id=_SOURCE)

    answered = [name for name in FIELD_NAMES if getattr(document, name).state.value != "unasked"]
    assert answered == ["cities"]
