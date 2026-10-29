"""`make live-adzuna` offline: its caps, its ledger rows and what it never records (ruling
R4; controller ruling for Task 7A). The Adzuna call is replaced by the fixture contract."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr

from nessa.evidence.acquire import AcquisitionResult
from nessa.evidence.adzuna import AdzunaQuery, parse_search, recorded_url
from nessa.evidence.records import AttemptStatus, InputRoute
from tools.live_adzuna import BLOCKED, MAX_SCOPE_REQUESTS, SCOPE, AdzunaSettings, run
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry

FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "acquisition" / "adzuna-search-gb.json"
APP_ID, APP_KEY = "fake-id-0000", "fake-key-0123456789abcdef"


def fake_acquire(
    fetcher: Any, pacer: Any, query: AdzunaQuery, credentials: Any, *, now: datetime
) -> AcquisitionResult:
    body = FIXTURE.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    page = parse_search(body, sha256=digest)
    return AcquisitionResult(
        route=InputRoute.ADZUNA,
        provider="adzuna",
        requested_url=recorded_url(query),
        status=AttemptStatus.SUCCEEDED,
        http_status=200,
        content_sha256=digest,
        copies=page.copies,
        total=page.total,
        fetched_at=now,
    )


def settings(app_id: str | None = APP_ID, app_key: str | None = APP_KEY) -> AdzunaSettings:
    return AdzunaSettings.model_validate(
        {
            "ADZUNA_APP_ID": SecretStr(app_id) if app_id else None,
            "ADZUNA_APP_KEY": SecretStr(app_key) if app_key else None,
        }
    )


@pytest.mark.req("MODEL-09")
def test_each_request_is_ledgered_at_no_cost_without_its_credentials(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "usage.jsonl")

    summary = run(settings(), ledger, acquire=fake_acquire, fetcher=object())  # type: ignore[arg-type]

    rows = ledger.records()
    assert [(r.budget_scope, r.provider, r.http_requests) for r in rows] == [
        (SCOPE, "adzuna", 1),
        (SCOPE, "adzuna", 1),
    ]
    assert {r.estimated_cost_nano_usd for r in rows} == {0}
    assert {r.outcome for r in rows} == {CallOutcome.OK}
    text = (tmp_path / "usage.jsonl").read_text() + (tmp_path / "usage.md").read_text()
    assert APP_ID not in text
    assert APP_KEY not in text
    assert "app_key" not in text
    assert summary["status"] == "complete"
    assert summary["adverts"] == 12
    assert summary["distinct_jobs"] == 6  # the second page repeats the first: deduplicated
    assert summary["results_holding_a_credential"] == 0


@pytest.mark.req("SEC-05")
def test_a_result_that_would_store_a_credential_fails_the_qualification(tmp_path: Path) -> None:
    def echoing(
        fetcher: Any, pacer: Any, query: AdzunaQuery, credentials: Any, *, now: datetime
    ) -> AcquisitionResult:
        result = fake_acquire(fetcher, pacer, query, credentials, now=now)
        [first, *rest] = result.copies
        echoed = first.model_copy(update={"apply_url": f"https://x.example/?utm_source={APP_ID}"})
        return result.model_copy(update={"copies": [echoed, *rest]})

    summary = run(settings(), Ledger(tmp_path / "usage.jsonl"), acquire=echoing, fetcher=object())  # type: ignore[arg-type]

    assert summary["status"] == "failed"
    assert summary["results_holding_a_credential"] == 2  # one per request


@pytest.mark.req("MODEL-09")
def test_the_scope_cap_refuses_before_any_request(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "usage.jsonl")
    for _ in range(MAX_SCOPE_REQUESTS - 1):
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
    called: list[object] = []

    def counting(*args: Any, **kwargs: Any) -> AcquisitionResult:
        called.append(args)
        return fake_acquire(*args, **kwargs)

    with pytest.raises(SystemExit, match="refused"):
        run(settings(), ledger, acquire=counting, fetcher=object())  # type: ignore[arg-type]

    assert called == []


@pytest.mark.parametrize(("app_id", "app_key"), [(None, APP_KEY), (APP_ID, None), (None, None)])
def test_a_missing_credential_is_blocked_and_nothing_is_sent(
    tmp_path: Path, app_id: str | None, app_key: str | None
) -> None:
    ledger = Ledger(tmp_path / "usage.jsonl")

    summary = run(settings(app_id, app_key), ledger, acquire=fake_acquire)

    assert summary == {"status": BLOCKED}
    assert ledger.records() == []
