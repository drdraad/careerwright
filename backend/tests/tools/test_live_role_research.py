"""`make live-role-research` offline (Task 6e; R5): Meta's place and the fetcher's are taken
by fakes, so the command's own bounds, ledger row and notes are checked without a call. The
title and pages are synthetic."""

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    NativeToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from careerwright.evidence.acquire import AcquisitionResult
from careerwright.evidence.fetcher import Fetcher, fetch_proxy
from careerwright.evidence.records import AttemptReason, AttemptStatus, InputRoute, RightsClass
from tests.support.certificates import make_ca
from tests.support.fake_models import SEARCHED, search_parts
from tests.support.fake_proxy import fake_proxy
from tools.live_role_research import (
    PAGES_PRINTED,
    ROLE_SCOPE,
    page_notes,
    read_until_enough,
    research_role,
)
from tools.live_smoke import SmokeSettings
from tools.usage_ledger import CallOutcome, Ledger

TITLE = "Orbital hydroponics technician"
BOARD = "https://jobs.board.example/ad/9"


def _role_search_parts() -> list[Any]:
    """The fake search with both its pages returned by the search: role research reads only
    those (a page it never returned is a guess)."""
    sources = [{"type": "url", "url": url} for url in (SEARCHED, BOARD)]
    returned = {"status": "completed", "sources": sources}
    return [
        replace(part, content=returned) if isinstance(part, NativeToolReturnPart) else part
        for part in search_parts({"role": TITLE, "country": "England"}, "")
    ]


def _meta(sent: list[str]) -> Callable[[str, SecretStr], FunctionModel]:
    def build(model_id: str, api_key: SecretStr) -> FunctionModel:
        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            for message in messages:
                for part in getattr(message, "parts", ()):
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        sent.append(part.content)
            usage = RequestUsage(
                input_tokens=9_000, output_tokens=200, details={"web_search_requests": 1}
            )
            return ModelResponse(parts=_role_search_parts(), usage=usage)

        return FunctionModel(respond)

    return build


def _page(url: str) -> AcquisitionResult:
    host = url.split("/")[2]
    return AcquisitionResult(
        route=InputRoute.FETCH,
        provider=host,
        requested_url=url,
        status=AttemptStatus.SUCCEEDED,
        rights_class=RightsClass.OTHER,
        role_text=f"Synthetic test page. {TITLE}: {host} describes the role in its own words.",
        fetched_at=datetime(2026, 11, 1, tzinfo=UTC),
    )


@pytest.mark.req("DIV1-15", "MODEL-08", "SEC-05")
def test_one_search_is_sent_only_the_title_and_its_pages_are_checked_and_ledgered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key")
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    sent: list[str] = []
    read: list[str] = []

    def reader(url: str) -> AcquisitionResult:
        read.append(url)
        return _page(url)

    code = research_role(
        SmokeSettings(_env_file=None), ledger, title=TITLE, build=_meta(sent), read=reader
    )

    [row] = ledger.records()
    assert code == 0
    assert json.loads(sent[0].partition("\n")[2]) == {"role": TITLE, "country": "England"}
    assert read == [SEARCHED, BOARD]  # only pages the search returned, at most 20
    assert (row.budget_scope, row.outcome, row.is_production_model) == (
        ROLE_SCOPE,
        CallOutcome.OK,
        False,
    )
    assert row.estimated_cost_nano_usd is not None
    assert json.loads(row.notes)["candidates"] == 2
    # What the pages showed is printed with the row's number (the row is written before any
    # page is read, fix round 1, review I3).
    line = next(x for x in capsys.readouterr().out.splitlines() if x.startswith(PAGES_PRINTED))
    pages = json.loads(line.removeprefix(PAGES_PRINTED).partition(": ")[2])
    assert (pages["ledger_row"], pages["verdict"], pages["sources"]) == (row.seq, "found", 2)
    assert [p["title_verified"] for p in pages["pages"]] == [True, True]
    assert (pages["via_proxy"], pages["address_checked"]) == (False, True)
    assert "https://" not in line  # hosts only, never a URL


@pytest.mark.req("DIV1-15", "ACQ-01")
def test_with_proxy_mode_the_pages_go_through_the_proxy_and_the_print_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key")
    bundle = make_ca().bundle(tmp_path / "bundle.pem")
    with fake_proxy() as proxy:  # it refuses every host: nothing leaves loopback
        fetcher = Fetcher(user_agent="CareerwrightL0/test", proxy=fetch_proxy(proxy.url, bundle))
        code = research_role(
            SmokeSettings(_env_file=None),
            Ledger(tmp_path / "live-usage.jsonl"),
            title=TITLE,
            build=_meta([]),
            fetcher=fetcher,
        )

    assert code == 0
    assert proxy.connects() == ["careers.northwind.example:443", "jobs.board.example:443"]
    line = next(x for x in capsys.readouterr().out.splitlines() if x.startswith(PAGES_PRINTED))
    pages = json.loads(line.removeprefix(PAGES_PRINTED).partition(": ")[2])
    assert (pages["via_proxy"], pages["address_checked"]) == (True, False)
    assert [p["reason"] for p in pages["pages"]] == ["robots_unreachable"] * 2
    assert (pages["verdict"], pages["reason"]) == ("not_yet_found", "pages_unread")


@pytest.mark.req("DIV1-15", "MODEL-08")
def test_the_paid_call_is_ledgered_before_any_page_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key")
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    rows_when_read: list[int] = []

    def failing(url: str) -> AcquisitionResult:
        rows_when_read.append(len(ledger.records()))
        raise KeyboardInterrupt  # stopped mid-reading (Ctrl-C), or anything unexpected

    with pytest.raises(KeyboardInterrupt):
        research_role(
            SmokeSettings(_env_file=None), ledger, title=TITLE, build=_meta([]), read=failing
        )

    [row] = ledger.records()
    assert rows_when_read == [1]  # the paid call's row was already written
    assert (row.budget_scope, row.outcome) == (ROLE_SCOPE, CallOutcome.OK)
    assert row.estimated_cost_nano_usd is not None
    assert (tmp_path / "live-usage.md").read_text(encoding="utf-8").count(ROLE_SCOPE) >= 1


def _failed(url: str) -> AcquisitionResult:
    return AcquisitionResult(
        route=InputRoute.FETCH,
        provider=url.split("/")[2],
        requested_url=url,
        status=AttemptStatus.FAILED,
        reason=AttemptReason.ROBOTS_UNREACHABLE,
        fetched_at=datetime(2026, 11, 1, tzinfo=UTC),
    )


@pytest.mark.req("DIV1-15")
def test_pages_that_could_not_be_read_are_printed_as_unread_never_not_on_any_page() -> None:
    # Ledger row 44 (2026-11-01): every page's robots.txt was unreachable.
    urls = [f"https://site{n}.example/role" for n in range(5)]
    none_read = page_notes(TITLE, [_failed(u) for u in urls])
    partly_read = page_notes(
        TITLE,
        [_failed(urls[0]), _page(urls[1]).model_copy(update={"role_text": "Synthetic test page."})],
    )

    for notes, unread in ((none_read, 5), (partly_read, 1)):
        assert (notes["verdict"], notes["reason"], notes["unread"]) == (
            "not_yet_found",
            "pages_unread",
            unread,
        )
    # No page to read is no verdict at all, never "not on any page".
    assert page_notes(TITLE, []) == {
        "pages": [],
        "verdict": None,
        "reason": "no_pages",
        "unread": 0,
        "read": 0,
        "gone": 0,
        "sources": 0,
        "official": False,
    }


@pytest.mark.req("DIV1-15")
def test_the_tool_reads_as_the_product_does_past_pages_gone_until_twenty_are_read() -> None:
    # Round 2 of the product owner's live try (3 November 2026): both pages had expired.
    urls = [f"https://site{n}.example/role" for n in range(24)]
    gone = {urls[0]: 404, urls[1]: 410}
    asked: list[str] = []

    def reader(url: str) -> AcquisitionResult:
        asked.append(url)
        if url in gone:
            return _failed(url).model_copy(
                update={"reason": AttemptReason.HTTP_ERROR, "http_status": gone[url]}
            )
        return _page(url)

    notes = page_notes(TITLE, read_until_enough(urls, reader))

    assert asked == urls[:22]  # two gone, then twenty read; the last two never asked for
    assert (notes["read"], notes["gone"], notes["unread"]) == (20, 2, 2)
    assert notes["verdict"] == "found"  # a page no longer there is never one without the title
