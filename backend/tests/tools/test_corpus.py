"""The corpus pipeline offline, against the controlled server (Task 7A; for Task 7b's pages):
it keeps a body only where the rights policy permits, and its record carries every claim's
span. Pages are synthetic."""

import hashlib
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from nessa.evidence.fetcher import Fetcher
from nessa.evidence.records import Retention, RightsClass
from tests.domain.test_pages import POSTING, page
from tests.support.acquisition_service import LOOPBACK, scripted_resolver
from tests.support.source_server import Scripted, SourceServer, source_server
from tools.corpus import acquire_for_corpus, agent_classification

EMPLOYER_TERMS = '"Apply on our careers site" (careers page footer, read 2026-10-29)'


def fetcher(server: SourceServer) -> Fetcher:
    return Fetcher(
        resolve=scripted_resolver(
            {
                "careers.northwind.example": [LOOPBACK],
                "jobs.board.example": [LOOPBACK],
                "www.gov.uk": [LOOPBACK],
            }
        ),
        user_agent="NessaL0/test",
        extra_allowed=frozenset({("127.0.0.1", server.port)}),
    )


@pytest.mark.req("ACQ-06")
def test_an_unlisted_page_keeps_only_its_hash_even_when_it_names_itself(tmp_path: Path) -> None:
    body = page(POSTING).encode()  # its JSON-LD names the hiring organisation's own site
    with source_server({"/jobs/1": Scripted(body=body)}) as server:
        out = acquire_for_corpus(
            "J12",
            f"http://careers.northwind.example:{server.port}/jobs/1",
            fetcher=fetcher(server),
            evidence_dir=tmp_path,
        )

    assert out["sha256"] == hashlib.sha256(body).hexdigest()
    assert out["rights_status"] == "pending human rights review"
    assert out["kept_body"] is None
    assert not list(tmp_path.iterdir())
    postings: Any = out["postings"]
    [posting] = postings
    assert {c["field"] for c in posting["claims"]} >= {"title", "salary", "employer"}


@pytest.mark.req("ACQ-06")
def test_an_agent_s_dated_classification_raises_an_unlisted_page_before_anything_is_kept(
    tmp_path: Path,
) -> None:
    body = page(POSTING).encode()
    with source_server({"/jobs/1": Scripted(body=body)}) as server:
        out = acquire_for_corpus(
            "J12",
            f"http://careers.northwind.example:{server.port}/jobs/1",
            fetcher=fetcher(server),
            rights_class=RightsClass.EMPLOYER_POSTING,
            terms=EMPLOYER_TERMS,
            evidence_dir=tmp_path,
        )

    status = str(out["rights_status"])
    assert status.startswith("employer-posting: ")
    assert "classified by the curating agent on 20" in status  # dated
    assert (tmp_path / "J12" / f"{out['sha256']}.html").read_bytes() == body


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    ("rights_class", "terms", "status"),
    [
        (RightsClass.JOB_BOARD, '"Reference only" (terms page, read 2026-10-29)', "job-board: "),
        (RightsClass.OTHER, None, "pending human rights review"),
    ],
    ids=["to a reference-only class", "to other"],
)
def test_an_agent_s_classification_lowers_a_listed_page_s_class_too(
    tmp_path: Path, rights_class: RightsClass, terms: str | None, status: str
) -> None:
    body = page(POSTING).encode()
    with source_server({"/guidance/1": Scripted(body=body)}) as server:
        url = f"http://www.gov.uk:{server.port}/guidance/1"
        listed = acquire_for_corpus("J1", url, fetcher=fetcher(server), evidence_dir=tmp_path)
        lowered = acquire_for_corpus(
            "J2",
            url,
            fetcher=fetcher(server),
            rights_class=rights_class,
            terms=terms,
            evidence_dir=tmp_path,
        )

    assert str(listed["rights_status"]).startswith("govuk: ")
    assert listed["kept_body"] is not None
    assert str(lowered["rights_status"]).startswith(status)
    assert lowered["kept_body"] is None
    assert not (tmp_path / "J2").exists()


@pytest.mark.req("ACQ-06")
def test_an_agent_s_classification_never_keeps_more_of_a_listed_host_than_its_entry() -> None:
    classify = agent_classification(RightsClass.EMPLOYER_POSTING, EMPLOYER_TERMS, date(2026, 1, 1))

    board = classify("www.adzuna.co.uk")  # listed: a job board, reference only
    unlisted = classify("careers.northwind.example")

    assert (board.rights_class, board.retention) == (RightsClass.JOB_BOARD, Retention.EXCERPTS)
    assert (unlisted.rights_class, unlisted.retention) == (
        RightsClass.EMPLOYER_POSTING,
        Retention.BODY,
    )


def test_a_class_other_than_other_without_its_terms_is_refused() -> None:
    with pytest.raises(SystemExit, match="needs --terms"):
        agent_classification(RightsClass.EMPLOYER_POSTING, None, date(2026, 1, 1))
