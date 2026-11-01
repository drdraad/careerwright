"""A title with nothing to keep details by (Task 6d slice C, fix round 1): a role or target
typed as punctuation or emoji alone has no concept key (`careerwright.concept_key` gives ""),
so it can't take seniority, industry or marks. It is left out of the titles that can, never
a failed save (a 500 before this fix). No database: the store's reads are replaced by stand-ins.
The end-to-end refusal is `tests/integration/test_title_details.py`."""

import uuid
from types import SimpleNamespace
from typing import Any

import pytest

from careerwright.catalogue import taxonomy_store
from careerwright.profile import store, title_details
from careerwright.profile.document import (
    FIELD_NAMES,
    ProfileInput,
    apply_profile_input,
    empty_profile,
)
from careerwright.profile.records import TitleUse

SOURCE = uuid.UUID("00000000-0000-4000-8000-000000000001")
WORKSPACE = uuid.UUID("00000000-0000-4000-8000-000000000002")


def concept_key(text: str) -> str:
    """A stand-in for the SQL function's one rule that matters here: no letter or digit, no
    key."""
    return " ".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


@pytest.fixture
def no_database(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    asked: list[list[str]] = []

    def held(_tx: Any, _ws: uuid.UUID, _use: TitleUse, keys: Any) -> dict[str, Any]:
        asked.append(list(keys))
        return {}

    monkeypatch.setattr(
        taxonomy_store, "concept_keys", lambda _tx, texts: {t: concept_key(t) for t in texts}
    )
    monkeypatch.setattr(store, "title_details", held)
    monkeypatch.setattr(title_details, "visible_workspace", lambda _tx, _ws: None)
    return asked


def answers(**fields: object) -> Any:
    values: dict[str, object] = {name: {"state": "unasked"} for name in FIELD_NAMES}
    values.update({name: {"state": "provided", "value": v} for name, v in fields.items()})
    return apply_profile_input(empty_profile(), ProfileInput.model_validate(values), SOURCE)


@pytest.mark.req("PROF-11")
@pytest.mark.parametrize("nothing", ["-", "…", "\N{SLIGHTLY SMILING FACE}"])
def test_a_title_with_no_letters_or_digits_takes_no_details(
    monkeypatch: pytest.MonkeyPatch, no_database: list[list[str]], nothing: str
) -> None:
    document = answers(current_role=nothing, target_titles=[nothing, "Doula"])
    monkeypatch.setattr(
        store, "current_profile", lambda _tx, _ws: SimpleNamespace(version=3, document=document)
    )

    version, views = title_details.current_title_details(None, WORKSPACE)  # type: ignore[arg-type]

    assert version == 3
    assert [(v.details.title_use, v.title, v.details.title_key) for v in views] == [
        (TitleUse.TARGET, "Doula", "doula")
    ]
    assert all("" not in keys for keys in no_database)
