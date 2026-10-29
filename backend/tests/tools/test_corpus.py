"""The corpus pipeline offline, against the controlled server (Task 7A; for Task 7b's pages):
it keeps a body only where the rights policy permits, and its record carries every claim's
span. Pages are synthetic."""

import hashlib
from pathlib import Path
from typing import Any

import pytest

from nessa.evidence.fetcher import Fetcher
from nessa.evidence.records import RightsClass
from tests.domain.test_pages import POSTING, page
from tests.support.acquisition_service import LOOPBACK, scripted_resolver
from tests.support.source_server import Scripted, SourceServer, source_server
from tools.corpus import acquire_for_corpus


def fetcher(server: SourceServer) -> Fetcher:
    return Fetcher(
        resolve=scripted_resolver(
            {"careers.northwind.example": [LOOPBACK], "jobs.board.example": [LOOPBACK]}
        ),
        user_agent="NessaL0/test",
        extra_allowed=frozenset({("127.0.0.1", server.port)}),
    )


@pytest.mark.req("ACQ-06")
def test_an_employer_posting_is_kept_privately_with_its_spans(tmp_path: Path) -> None:
    body = page(POSTING).encode()
    with source_server({"/jobs/1": Scripted(body=body)}) as server:
        out = acquire_for_corpus(
            "J12",
            f"http://careers.northwind.example:{server.port}/jobs/1",
            fetcher=fetcher(server),
            evidence_dir=tmp_path,
        )

    assert out["sha256"] == hashlib.sha256(body).hexdigest()
    assert str(out["rights_status"]).startswith("employer-posting: ")
    assert (tmp_path / "J12" / f"{out['sha256']}.html").read_bytes() == body
    postings: Any = out["postings"]
    [posting] = postings
    assert {c["field"] for c in posting["claims"]} >= {"title", "salary", "employer"}


@pytest.mark.req("ACQ-06")
def test_a_page_outside_the_classes_keeps_only_its_hash_unless_an_agent_classifies_it(
    tmp_path: Path,
) -> None:
    body = page({"@type": "JobPosting", "title": "Gardener"}).encode()
    with source_server({"/ad/1": Scripted(body=body)}) as server:
        url = f"http://jobs.board.example:{server.port}/ad/1"
        pending = acquire_for_corpus("J13", url, fetcher=fetcher(server), evidence_dir=tmp_path)
        board = acquire_for_corpus(
            "J14",
            url,
            fetcher=fetcher(server),
            rights_class=RightsClass.JOB_BOARD,
            terms='"Reference only" (terms page, read 2026-10-29)',
            evidence_dir=tmp_path,
        )

    assert pending["rights_status"] == "pending human rights review"
    assert pending["kept_body"] is None
    assert str(board["rights_status"]).startswith("job-board: ")
    assert board["kept_body"] is None  # a job board is reference only
    assert not list(tmp_path.iterdir())


def test_naming_class_other_or_omitting_the_terms_is_refused(tmp_path: Path) -> None:
    with source_server({"/ad/1": Scripted(body=page(POSTING).encode())}) as server:
        url = f"http://jobs.board.example:{server.port}/ad/1"
        with pytest.raises(SystemExit, match="needs --terms"):
            acquire_for_corpus(
                "J1",
                url,
                fetcher=fetcher(server),
                rights_class=RightsClass.OTHER,
                evidence_dir=tmp_path,
            )
