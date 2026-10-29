"""The corpus pipeline offline, against the controlled server (Task 7A; for Task 7b's pages):
it keeps a body only where the rights policy permits, and its record carries every claim's
span. Pages are synthetic."""

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr

from nessa.evidence.adzuna import AdzunaQuery, recorded_url
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.records import Retention, RightsClass
from nessa.evidence.sources import PageRights
from tests.domain.test_pages import POSTING, page
from tests.support.acquisition_service import LOOPBACK, scripted_resolver
from tests.support.source_server import Scripted, SourceServer, source_server
from tests.tools.test_live_adzuna import APP_ID, APP_KEY, fake_acquire
from tools.corpus import acquire_for_corpus, adzuna_for_corpus, agent_classification, locate
from tools.live_adzuna import MAX_SCOPE_REQUESTS, SCOPE
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry

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
    def classify(host: str) -> PageRights:
        return agent_classification(
            RightsClass.EMPLOYER_POSTING, EMPLOYER_TERMS, date(2026, 1, 1), requested_host=host
        )(host)

    board = classify("www.adzuna.co.uk")  # listed: a job board, reference only
    unlisted = classify("careers.northwind.example")

    assert (board.rights_class, board.retention) == (RightsClass.JOB_BOARD, Retention.EXCERPTS)
    assert (unlisted.rights_class, unlisted.retention) == (
        RightsClass.EMPLOYER_POSTING,
        Retention.BODY,
    )


@pytest.mark.req("ACQ-06")
def test_an_agent_s_classification_holds_only_for_the_host_it_was_given_for(
    tmp_path: Path,
) -> None:
    # Re-review A M-6: the classified URL redirects to another unlisted host.
    body = page(POSTING).encode()
    with source_server({"/jobs/1": Scripted(body=body)}) as server:
        server.routes["/go"] = Scripted(
            302, headers=(("Location", f"http://jobs.board.example:{server.port}/jobs/1"),)
        )
        out = acquire_for_corpus(
            "J12",
            f"http://careers.northwind.example:{server.port}/go",
            fetcher=fetcher(server),
            rights_class=RightsClass.EMPLOYER_POSTING,
            terms=EMPLOYER_TERMS,
            evidence_dir=tmp_path,
        )

    status = str(out["rights_status"])
    assert status.startswith("pending human rights review")  # the manifest's class
    assert "careers.northwind.example" in status
    assert "jobs.board.example" in status  # both hosts recorded
    assert out["kept_body"] is None
    assert not list(tmp_path.iterdir())


@pytest.mark.req("TEST1-09")
def test_a_label_s_excerpts_are_located_in_the_hashed_text_of_a_page_whose_body_is_not_kept(
    tmp_path: Path,
) -> None:
    body = page(POSTING).encode()
    with source_server({"/jobs/1": Scripted(body=body)}) as server:
        out = acquire_for_corpus(
            "J12",
            f"http://jobs.board.example:{server.port}/jobs/1",
            fetcher=fetcher(server),
            rights_class=RightsClass.JOB_BOARD,
            terms='"Reference only" (terms page, read 2026-10-29)',
            evidence_dir=tmp_path,
            excerpts=["Data Quality Analyst", "not on the page"],
        )

    assert out["kept_body"] is None
    assert not list(tmp_path.iterdir())  # located in memory, never written
    text = body.decode()
    located: Any = out["located"]
    found, missing = located
    assert found["offsets"]
    assert all(text[s:e] == "Data Quality Analyst" for s, e in found["offsets"])
    assert missing == {"excerpt": "not on the page", "count": 0, "offsets": [], "texts": []}


@pytest.mark.req("TEST1-09")
def test_whitespace_in_an_excerpt_matches_a_line_break_in_the_markup_and_nothing_else() -> None:
    text = "<li>Experience of\n      Power BI</li><li>Experience of Power-BI</li>"

    [found] = locate(text, ["Experience of Power BI"])

    assert found["offsets"] == [[4, 32]]
    assert found["texts"] == ["Experience of\n      Power BI"]


@pytest.mark.req("TEST1-09")
def test_a_located_excerpt_s_count_is_its_real_count_though_only_five_spans_are_listed() -> None:
    text = " ".join(["Leeds City College"] * 29)

    [found] = locate(text, ["Leeds City College"])
    offsets: Any = found["offsets"]

    assert found["count"] == 29
    assert len(offsets) == 5


CREDENTIALS = (SecretStr(APP_ID), SecretStr(APP_KEY))


@pytest.mark.req("MODEL-09")
def test_an_adzuna_slot_is_one_capped_ledgered_request_whose_record_cites_pointers(
    tmp_path: Path,
) -> None:
    ledger = Ledger(tmp_path / "usage.jsonl")
    query = AdzunaQuery(what="bookkeeping assistant", where="Leeds", results_per_page=50)

    out = adzuna_for_corpus(
        "J03",
        query,
        CREDENTIALS,
        ledger,
        acquire=fake_acquire,
        fetcher=object(),  # type: ignore[arg-type]
    )

    [row] = ledger.records()
    assert (row.budget_scope, row.http_requests, row.estimated_cost_nano_usd) == (SCOPE, 1, 0)
    assert row.purpose.startswith("corpus J03: ")
    assert out["url"] == recorded_url(query)  # as recorded: never with the credentials
    assert out["total_matching"] is not None
    assert out["kept_body"] is None
    assert out["leak_scan"] == {"cells": 3, "findings": []}
    postings: Any = out["postings"]
    salary = next(c for p in postings for c in p["claims"] if c["field"] == "salary")
    assert salary["pointer"].startswith("/results/")
    assert salary["value"]["basis"] in {"predicted", "advertised", "unknown"}
    text = json.dumps(out) + (tmp_path / "usage.jsonl").read_text()
    assert APP_ID not in text
    assert APP_KEY not in text


@pytest.mark.req("MODEL-09")
def test_an_adzuna_slot_past_the_scope_cap_is_refused_before_any_request(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "usage.jsonl")
    for _ in range(MAX_SCOPE_REQUESTS):
        ledger.append(
            LiveCallEntry(
                budget_scope=SCOPE,
                provider="adzuna",
                purpose="earlier",
                model_id="adzuna-jobs-api",
                is_production_model=False,
                endpoint="GET x",
                outcome=CallOutcome.OK,
                reserved_nano_usd=0,
                estimated_cost_nano_usd=0,
            )
        )
    sent: list[object] = []

    with pytest.raises(SystemExit, match="refused"):
        adzuna_for_corpus(
            "J03",
            AdzunaQuery(what="x", where="Leeds"),
            CREDENTIALS,
            ledger,
            acquire=lambda *args, **kwargs: sent.append(args),  # type: ignore[arg-type]
            fetcher=object(),  # type: ignore[arg-type]
        )

    assert sent == []


def test_a_class_other_than_other_without_its_terms_is_refused() -> None:
    with pytest.raises(SystemExit, match="needs --terms"):
        agent_classification(
            RightsClass.EMPLOYER_POSTING, None, date(2026, 1, 1), requested_host="x"
        )
