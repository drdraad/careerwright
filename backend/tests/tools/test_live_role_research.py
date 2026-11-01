"""`make live-role-research` offline (Task 6e; R5): Meta's place and the fetcher's are taken
by fakes, so the command's own bounds, ledger row and notes are checked without a call. The
title and pages are synthetic."""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import SecretStr
from pydantic_ai.messages import ModelMessage, ModelResponse, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from careerwright.evidence.acquire import AcquisitionResult
from careerwright.evidence.records import AttemptStatus, InputRoute, RightsClass
from tests.support.fake_models import SEARCHED, search_parts
from tools.live_role_research import ROLE_SCOPE, research_role
from tools.live_smoke import SmokeSettings
from tools.usage_ledger import CallOutcome, Ledger

TITLE = "Orbital hydroponics technician"


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
            asked: dict[str, object] = {"role": TITLE, "country": "England"}
            return ModelResponse(parts=search_parts(asked, ""), usage=usage)

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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
    assert read == [SEARCHED, "https://jobs.board.example/ad/9"]  # grounded first, at most 5
    assert (row.budget_scope, row.outcome, row.is_production_model) == (
        ROLE_SCOPE,
        CallOutcome.OK,
        False,
    )
    assert row.estimated_cost_nano_usd is not None
    notes = json.loads(row.notes)
    assert (notes["verdict"], notes["sources"]) == ("found", 2)
    assert [p["title_verified"] for p in notes["pages"]] == [True, True]
    assert "https://" not in row.notes  # hosts only, never a URL
