"""What a direct entry enters in words, for the support screen (ADR 0007; Task 6f): a
qualification's name is typed words and is screened like any other; what the person is doing
now is a choice from a fixed list, with no words typed. No database: the stored version is a
stand-in. The end-to-end panel is `tests/integration/test_workspaces_and_profiles.py`."""

import uuid
from types import SimpleNamespace
from typing import Any

import pytest

from careerwright.profile import store
from careerwright.profile.commands import entered_words
from careerwright.profile.document import (
    FIELD_NAMES,
    ProfileInput,
    apply_profile_input,
    empty_profile,
    input_type,
)

SOURCE = uuid.UUID("00000000-0000-4000-8000-000000000001")
WORKSPACE = uuid.UUID("00000000-0000-4000-8000-000000000002")


def answer(name: str, value: object) -> Any:
    return input_type(name).model_validate({"state": "provided", "value": value})


@pytest.mark.req("PROF-13", "PROF-09")
def test_a_new_qualification_s_name_is_screened_and_a_held_one_or_a_status_is_not(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    held = apply_profile_input(
        empty_profile(),
        ProfileInput.model_validate(
            {
                **{name: {"state": "unasked"} for name in FIELD_NAMES},
                "qualifications": {
                    "state": "provided",
                    "value": [{"name": "GCSE maths", "status": "achieved"}],
                },
            }
        ),
        SOURCE,
    )
    monkeypatch.setattr(
        store, "profile_version", lambda _tx, _ws, _v: SimpleNamespace(document=held)
    )

    words = entered_words(
        None,  # type: ignore[arg-type]  # the stand-in store reads no transaction
        WORKSPACE,
        1,
        {
            "qualifications": answer(
                "qualifications",
                [
                    {"name": "GCSE maths", "status": "achieved"},
                    {"name": "A-level biology", "status": "expected"},
                ],
            ),
            "work_status": answer("work_status", "in_education_or_training"),
        },
    )

    assert words == ["A-level biology"]


@pytest.mark.req("PROF-09")
def test_a_new_task_the_person_doesnt_enjoy_is_screened_like_any_typed_words(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Task W2F: what the person doesn't enjoy is typed words, so the support screen reads it.
    monkeypatch.setattr(
        store, "profile_version", lambda _tx, _ws, _v: SimpleNamespace(document=empty_profile())
    )

    words = entered_words(
        None,  # type: ignore[arg-type]  # the stand-in store reads no transaction
        WORKSPACE,
        1,
        {"disliked_tasks": answer("disliked_tasks", ["filling in forms"])},
    )

    assert words == ["filling in forms"]
