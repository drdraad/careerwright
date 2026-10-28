"""The profile document: practical inputs and interests, each with a field state and a source.

A field state keeps "not yet asked", "unknown", "skipped" and "prefer not to say" apart, so
a missing value is never read as zero (spec section 3, API-04). Every answered field cites
the source reference that established it; the server assigns sources, never the client.
The source carries the rest of the field's provenance: how it was obtained (direct entry,
a confirmed conversation proposal, a fixture), its basis (stated or inferred), when it was
observed and who confirmed it (PROF-01).

Schema version 2 (Task 5) adds three separate interest and capability fields: what the
person enjoys, what they believe they can do and what they have evidence they can do
(spec section 4, REC1-04). Schema version 3 (Task 6) adds the optional work style, how the
person says they like to work (spec section 4's "work style and personality" layer): a
described preference that informs suggestions, never a limit (REC1-03) and never a
personality type; and the salary floor, the lowest gross pay they will accept with its
period, a hard constraint (product owner, H-11). Older documents read as version 3 with
the later fields unasked.
Cities must be on the finite English list and are stored by its name for the city.
"""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from nessa.catalogue.places import resolve_city
from nessa.errors import ErrorCode, ErrorStage, NessaError
from nessa.money import Money

# Spec BND-1: up to three cities and three active targets; a fourth is never added silently.
MAX_CITIES = 3
MAX_TARGETS = 3
MAX_TASKS = 8
PROFILE_SCHEMA_VERSION: Literal["3"] = "3"

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


def _published_bound(limit: int) -> object:
    """A list bound in the published schema (`maxItems`), so clients read it from the
    generated client. `checked_input` enforces it, naming the problem."""
    return Field(json_schema_extra={"maxItems": limit})


class CityListInput(TextListInput):
    value: Annotated[list[TextValue], _published_bound(MAX_CITIES)] | None = None


class TargetListInput(TextListInput):
    value: Annotated[list[TextValue], _published_bound(MAX_TARGETS)] | None = None


class TaskListInput(TextListInput):
    value: Annotated[list[TextValue], _published_bound(MAX_TASKS)] | None = None


class HoursInput(_FieldInput[HoursValue]):
    pass


class MoneyInput(_FieldInput[Money]):
    pass


class PayPeriod(StrEnum):
    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    HOUR = "hour"


class SalaryFloor(BaseModel):
    """The lowest gross pay the person will accept, as they gave it: its period is kept and
    never converted, because annualising needs working hours (spec section 5)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    amount: Money
    period: PayPeriod = Field(description="Annual unless the person says otherwise.")
    basis: Literal["gross"] = "gross"


class SalaryInput(_FieldInput[SalaryFloor]):
    """A new answer: a floor is more than £0. Checked on input only, so a version stored
    before the rule still opens (read, history, export)."""

    @model_validator(mode="after")
    def _more_than_nothing(self) -> Self:
        if self.value is not None and self.value.amount.minor_units == 0:
            raise ValueError("a salary floor is more than £0; no floor is Unknown or Skipped")
        return self


class TextField(_Field[TextValue]):
    pass


class TextListField(_Field[list[TextValue]]):
    pass


class HoursField(_Field[HoursValue]):
    pass


class MoneyField(_Field[Money]):
    pass


class SalaryField(_Field[SalaryFloor]):
    pass


FieldInput = TextInput | TextListInput | HoursInput | MoneyInput | SalaryInput


class ProfileInput(BaseModel):
    """What a client submits: states and values only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    preferred_name: TextInput
    current_role: TextInput
    cities: CityListInput = Field(
        description=f"At most {MAX_CITIES} distinct cities from `GET /v1/places`."
    )
    target_titles: TargetListInput = Field(description=f"At most {MAX_TARGETS} active targets.")
    weekly_study_hours: HoursInput
    direct_spend_cap: MoneyInput
    monthly_payment_cap: MoneyInput
    enjoyed_tasks: TaskListInput = Field(
        description=f"Tasks the person enjoys (interest), at most {MAX_TASKS}."
    )
    confident_tasks: TaskListInput = Field(
        description=f"Tasks the person believes they can do (confidence), at most {MAX_TASKS}."
    )
    evidenced_tasks: TaskListInput = Field(
        description=f"Tasks the person has evidence they can do, at most {MAX_TASKS}."
    )
    work_style: TaskListInput = Field(
        description=(
            f"How the person says they like to work (optional), at most {MAX_TASKS}: it "
            "informs suggestions and never excludes any kind of work."
        )
    )
    minimum_salary: SalaryInput = Field(
        description=(
            "The lowest gross pay the person will accept, with its period: a hard limit, set "
            "only by their confirmation. Recorded, not yet applied: no suggestion is removed "
            "for pay until pay evidence exists, and unknown pay is never below it."
        )
    )


class ProfileDocument(BaseModel):
    """A stored profile version's content: each field with the source that established it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["3"] = PROFILE_SCHEMA_VERSION
    preferred_name: TextField
    current_role: TextField
    cities: TextListField
    target_titles: TextListField
    weekly_study_hours: HoursField
    direct_spend_cap: MoneyField
    monthly_payment_cap: MoneyField
    enjoyed_tasks: TextListField
    confident_tasks: TextListField
    evidenced_tasks: TextListField
    work_style: TextListField
    minimum_salary: SalaryField

    @model_validator(mode="before")
    @classmethod
    def _read_older_versions(cls, data: Any) -> Any:
        """Version 1 had no interest or capability fields and version 2 no work style: they
        were never asked."""
        version = data.get("schema_version") if isinstance(data, dict) else None
        later = _ADDED_AFTER.get(version) if isinstance(version, str) else None
        if later is None:
            return data
        unasked = {"state": FieldState.UNASKED.value}
        return {
            **{name: unasked for name in later},
            **data,
            "schema_version": PROFILE_SCHEMA_VERSION,
        }


FIELD_NAMES = tuple(ProfileInput.model_fields)
VERSION_2_FIELDS = ("enjoyed_tasks", "confident_tasks", "evidenced_tasks")
VERSION_3_FIELDS = ("work_style", "minimum_salary")
_ADDED_AFTER: Mapping[str, tuple[str, ...]] = {
    "1": (*VERSION_2_FIELDS, *VERSION_3_FIELDS),
    "2": VERSION_3_FIELDS,
}


class FieldKind(StrEnum):
    TEXT = "text"
    LIST = "list"
    HOURS = "hours"
    MONEY = "money"
    SALARY = "salary"


@dataclass(frozen=True)
class FieldSpec:
    kind: FieldKind
    max_items: int | None = None
    # Spec section 4: the assistant may propose these, but only the person's explicit
    # confirmation establishes them, because search and planning treat them as limits.
    hard_constraint: bool = False


FIELD_SPECS: Mapping[str, FieldSpec] = {
    "preferred_name": FieldSpec(FieldKind.TEXT),
    "current_role": FieldSpec(FieldKind.TEXT),
    "cities": FieldSpec(FieldKind.LIST, MAX_CITIES, hard_constraint=True),
    "target_titles": FieldSpec(FieldKind.LIST, MAX_TARGETS, hard_constraint=True),
    "weekly_study_hours": FieldSpec(FieldKind.HOURS, hard_constraint=True),
    "direct_spend_cap": FieldSpec(FieldKind.MONEY, hard_constraint=True),
    "monthly_payment_cap": FieldSpec(FieldKind.MONEY, hard_constraint=True),
    "enjoyed_tasks": FieldSpec(FieldKind.LIST, MAX_TASKS),
    "confident_tasks": FieldSpec(FieldKind.LIST, MAX_TASKS),
    "evidenced_tasks": FieldSpec(FieldKind.LIST, MAX_TASKS),
    "work_style": FieldSpec(FieldKind.LIST, MAX_TASKS),
    # Added to the set by the product owner (H-11, 2026-10-28).
    "minimum_salary": FieldSpec(FieldKind.SALARY, hard_constraint=True),
}
HARD_CONSTRAINTS = frozenset(name for name, spec in FIELD_SPECS.items() if spec.hard_constraint)
_INPUT_TYPES: Mapping[FieldKind, type[FieldInput]] = {
    FieldKind.TEXT: TextInput,
    FieldKind.LIST: TextListInput,
    FieldKind.HOURS: HoursInput,
    FieldKind.MONEY: MoneyInput,
    FieldKind.SALARY: SalaryInput,
}


def input_type(name: str) -> type[FieldInput]:
    return _INPUT_TYPES[FIELD_SPECS[name].kind]


def empty_profile() -> ProfileDocument:
    return ProfileDocument.model_validate(
        {name: {"state": FieldState.UNASKED} for name in FIELD_NAMES}
    )


def _invalid(name: str, reason: str, message: str) -> NessaError:
    return NessaError(
        ErrorCode.VALIDATION_FAILED,
        message,
        stage=ErrorStage.PROFILE,
        details={"field": name, "reason": reason},
    )


def checked_input(name: str, field: FieldInput) -> FieldInput:
    """One field's input after the cross-value rules: list bounds and duplicates, and cities
    resolved to the finite English list (stored by the list's own name)."""
    spec = FIELD_SPECS[name]
    if spec.kind is not FieldKind.LIST or not isinstance(field.value, list):
        return field
    values: list[str] = field.value
    if spec.max_items is not None and len(values) > spec.max_items:
        raise NessaError(
            ErrorCode.LIMIT_EXCEEDED,
            f"At most {spec.max_items} {name.replace('_', ' ')} are supported; remove one first.",
            stage=ErrorStage.PROFILE,
            details={"field": name, "limit": spec.max_items},
        )
    if name == "cities":
        places = [resolve_city(value) for value in values]
        if any(place is None for place in places):
            raise _invalid(
                name, "unknown_city", "Each work area must be an English city on the list."
            )
        values = [place.label for place in places if place is not None]
    folded = [value.casefold() for value in values]
    if len(set(folded)) != len(folded):
        raise _invalid(
            name, "duplicate", f"The same entry appears twice in {name.replace('_', ' ')}."
        )
    return TextListInput(state=field.state, value=values)


def apply_updates(
    previous: ProfileDocument, updates: Mapping[str, tuple[FieldInput, uuid.UUID | None]]
) -> tuple[ProfileDocument, list[str]]:
    """The next document and the fields it changes. Each updated field that changes cites
    its update's source; every other field keeps its value and its source."""
    unknown = set(updates) - set(FIELD_NAMES)
    if unknown:
        raise _invalid(sorted(unknown)[0], "not_a_field", "That is not a profile field.")
    fields: dict[str, dict[str, object]] = {}
    changed: list[str] = []
    for name in FIELD_NAMES:
        before = getattr(previous, name)
        if name not in updates:
            fields[name] = before.model_dump()
            continue
        raw, source_ref_id = updates[name]
        after = checked_input(name, input_type(name).model_validate(raw.model_dump()))
        if (before.state, before.value) == (after.state, after.value):
            fields[name] = before.model_dump()
            continue
        changed.append(name)
        source = None if after.state is FieldState.UNASKED else source_ref_id
        fields[name] = {"state": after.state, "value": after.value, "source_ref_id": source}
    return ProfileDocument.model_validate(fields), changed


def apply_profile_input(
    previous: ProfileDocument, new: ProfileInput, source_ref_id: uuid.UUID
) -> ProfileDocument:
    """A whole-profile edit: changed answers cite `source_ref_id`, unchanged ones keep theirs."""
    return apply_updates(previous, whole_input(new, source_ref_id))[0]


def whole_input(
    new: ProfileInput, source_ref_id: uuid.UUID
) -> dict[str, tuple[FieldInput, uuid.UUID]]:
    return {name: (getattr(new, name), source_ref_id) for name in FIELD_NAMES}
