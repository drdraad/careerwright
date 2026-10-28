"""The profile document: practical inputs, each with an explicit field state and its source.

A field state keeps "not yet asked", "unknown", "skipped" and "prefer not to say" apart, so
a missing value is never read as zero (spec section 3, API-04). Every answered field cites
the source reference that established it; the server assigns sources, never the client.
This is the Sprint 1 subset of the profile; the interview contract (Task 5) extends it
through a new schema version.
"""

import uuid
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.money import Money

# Spec BND-1: up to three cities and three active targets; a fourth is never added silently.
MAX_CITIES = 3
MAX_TARGETS = 3
PROFILE_SCHEMA_VERSION: Literal["1"] = "1"

TextValue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
HoursValue = Annotated[float, Field(ge=0, le=168)]


class FieldState(StrEnum):
    UNASKED = "unasked"
    PROVIDED = "provided"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class _FieldInput[V](BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: FieldState
    value: V | None = None

    @model_validator(mode="after")
    def _value_matches_state(self) -> Self:
        if self.state is FieldState.PROVIDED and self.value is None:
            raise ValueError("a provided field needs a value")
        if self.state is not FieldState.PROVIDED and self.value is not None:
            raise ValueError("only a provided field has a value")
        return self


class _Field[V](_FieldInput[V]):
    source_ref_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _answered_fields_cite_a_source(self) -> Self:
        if (self.state is FieldState.UNASKED) != (self.source_ref_id is None):
            raise ValueError("an answered field cites a source; an unasked field cites none")
        return self


class TextInput(_FieldInput[TextValue]):
    pass


class TextListInput(_FieldInput[list[TextValue]]):
    pass


class HoursInput(_FieldInput[HoursValue]):
    pass


class MoneyInput(_FieldInput[Money]):
    pass


class TextField(_Field[TextValue]):
    pass


class TextListField(_Field[list[TextValue]]):
    pass


class HoursField(_Field[HoursValue]):
    pass


class MoneyField(_Field[Money]):
    pass


class ProfileInput(BaseModel):
    """What a client submits: states and values only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    preferred_name: TextInput
    current_role: TextInput
    cities: TextListInput = Field(description=f"At most {MAX_CITIES} distinct cities.")
    target_titles: TextListInput = Field(description=f"At most {MAX_TARGETS} active targets.")
    weekly_study_hours: HoursInput
    direct_spend_cap: MoneyInput
    monthly_payment_cap: MoneyInput


class ProfileDocument(BaseModel):
    """A stored profile version's content: each field with the source that established it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"] = PROFILE_SCHEMA_VERSION
    preferred_name: TextField
    current_role: TextField
    cities: TextListField
    target_titles: TextListField
    weekly_study_hours: HoursField
    direct_spend_cap: MoneyField
    monthly_payment_cap: MoneyField


FIELD_NAMES = tuple(ProfileInput.model_fields)


def empty_profile() -> ProfileDocument:
    return ProfileDocument.model_validate(
        {name: {"state": FieldState.UNASKED} for name in FIELD_NAMES}
    )


def _check_bounds(new: ProfileInput) -> None:
    for name, limit in (("cities", MAX_CITIES), ("target_titles", MAX_TARGETS)):
        values: list[str] = getattr(new, name).value or []
        if len(values) > limit:
            raise NessaError(
                ErrorCode.LIMIT_EXCEEDED,
                f"At most {limit} {name.replace('_', ' ')} are supported; remove one first.",
                stage=ErrorStage.PROFILE,
                details={"field": name, "limit": limit},
            )
        folded = [value.casefold() for value in values]
        if len(set(folded)) != len(folded):
            raise NessaError(
                ErrorCode.VALIDATION_FAILED,
                f"The same entry appears twice in {name.replace('_', ' ')}.",
                stage=ErrorStage.PROFILE,
                details={"field": name, "reason": "duplicate"},
            )


def apply_profile_input(
    previous: ProfileDocument, new: ProfileInput, source_ref_id: uuid.UUID
) -> ProfileDocument:
    """The next document: changed answers cite `source_ref_id`, unchanged ones keep theirs."""
    _check_bounds(new)
    fields: dict[str, dict[str, object]] = {}
    for name in FIELD_NAMES:
        before = getattr(previous, name)
        after = getattr(new, name)
        if after.state is FieldState.UNASKED:
            source = None
        elif (before.state, before.value) == (after.state, after.value):
            source = before.source_ref_id
        else:
            source = source_ref_id
        fields[name] = {"state": after.state, "value": after.value, "source_ref_id": source}
    return ProfileDocument.model_validate(fields)


def changed_fields(previous: ProfileDocument, new: ProfileInput) -> list[str]:
    return [
        name
        for name in FIELD_NAMES
        if (getattr(previous, name).state, getattr(previous, name).value)
        != (getattr(new, name).state, getattr(new, name).value)
    ]
