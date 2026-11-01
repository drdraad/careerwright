"""The titles Careerwright's own material says no list holds (Task 6e fix round 1, review I4):
session W2's made-up person Sam, whose job is on no list, and `make live-role-research`'s
default synthetic title. Research this role is for such a title only, so each must be on no
list, or Sam's walkthrough and the live run would find nothing to research.

Here, offline: neither is a target of any pinned option pack version, and the package names
Sam's. Against ESCO's full release and the UK job-title index (the datasets `make setup`
fetches), the product's own check refuses neither: `tests/integration/test_evaluation.py`."""

import re

import pytest

from careerwright.catalogue.option_pack import PINS, load_pack
from tools.live_role_research import DEFAULT_TITLE
from tools.localenv import REPO_ROOT

SAM = "Client onboarding assistant"  # session W2's made-up person whose job is on no list
ON_NO_LIST = (SAM, DEFAULT_TITLE)
PACKAGE = REPO_ROOT / "docs" / "reviews" / "session-w2.md"


def _concept(title: str) -> str:
    """The title as a concept, roughly as `careerwright.concept_key` folds it (case,
    punctuation and a final "s" aside): looser than the product's, so it errs towards "a list
    holds it"."""
    return " ".join(w.removesuffix("s") for w in re.findall(r"[a-z0-9]+", title.casefold()))


@pytest.mark.req("DIV1-15", "TEST1-16")
@pytest.mark.parametrize("title", ON_NO_LIST)
def test_the_title_is_no_option_pack_target(title: str) -> None:
    for version in PINS:
        held = {_concept(t.title) for t in load_pack(version).targets}
        assert _concept(title) not in held, (title, version)


@pytest.mark.req("TEST1-16")
def test_session_w2_names_sams_title_and_says_how_it_was_checked() -> None:
    package = PACKAGE.read_text(encoding="utf-8")

    assert f'"{SAM}"' in package
    assert "tests/eval/test_titles_on_no_list.py" in package
