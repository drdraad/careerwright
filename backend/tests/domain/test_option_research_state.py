"""Unread and unfinished sources keep their research coverage explicit."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pytest

from careerwright.api import routes_option_research
from careerwright.api.deps import ApiDependencies
from careerwright.db import Tx
from careerwright.errors import CareerwrightError, ErrorCode
from careerwright.evidence import option_research, option_store, store
from careerwright.evidence.option_research import (
    OptionResearchCoverage,
    ResearchStatus,
    ResearchView,
)
from careerwright.evidence.records import AttemptStatus, ExtractionOutcome, RightsClass
from careerwright.identity.keyring import Keyring
from careerwright.vocabulary import DataMode, WorkState


def _research(
    monkeypatch: pytest.MonkeyPatch, *, rights: str, extraction: object | None
) -> ResearchView:
    search_id = uuid.uuid4()
    reading_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    research = option_store.ResearchRow(
        research_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        target="Nurse",
        city="Leeds",
        search_run_id=search_id,
        reading_run_id=reading_id,
        review_state="proposed",
        created_at=datetime(2026, 11, 3, tzinfo=UTC),
        reading_started_at=datetime(2026, 11, 3, tzinfo=UTC),
    )
    runs = {
        search_id: SimpleNamespace(run_id=search_id, status=WorkState.COMPLETE, failure_class=None),
        reading_id: SimpleNamespace(
            run_id=reading_id, status=WorkState.COMPLETE, failure_class=None
        ),
    }
    monkeypatch.setattr(option_research, "visible_run", lambda _tx, _ws, run_id: runs[run_id])
    monkeypatch.setattr(
        option_research,
        "_proposal",
        lambda _tx, _keyring, _run: SimpleNamespace(candidates=[object()], empty_reason=None),
    )
    monkeypatch.setattr(option_research, "pages_to_read", lambda _proposal: ["https://x.test/a"])
    monkeypatch.setattr(
        store,
        "targets",
        lambda _tx, _run: [SimpleNamespace(position=0, status="succeeded")],
    )
    monkeypatch.setattr(
        store,
        "attempts_of_run",
        lambda _tx, _run: [
            SimpleNamespace(
                attempt_id=attempt_id,
                position=0,
                status=AttemptStatus.SUCCEEDED,
                rights_class=rights,
            )
        ],
    )
    monkeypatch.setattr(
        store,
        "extractions_of_attempts",
        lambda _tx, _attempts: {attempt_id: extraction} if extraction else {},
    )
    monkeypatch.setattr(option_store, "records", lambda *_args: [])
    return option_research.research_view(
        cast(Tx, object()), cast(Keyring, object()), research.workspace_id, research
    )


def test_rights_refusal_is_never_a_complete_empty_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    view = _research(monkeypatch, rights=RightsClass.OTHER.value, extraction=None)

    assert view.status is ResearchStatus.COMPLETED
    assert view.coverage is OptionResearchCoverage.NONE_READ
    assert view.pages_read == 0
    assert view.pages_blocked == 1


def test_extraction_keeps_research_running_after_fetch_finishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extraction = SimpleNamespace(
        run_id=uuid.uuid4(),
        run_status=WorkState.RUNNING,
        not_run=None,
        failure_class=None,
        outcome=None,
    )

    view = _research(monkeypatch, rights=RightsClass.COURSE_PROVIDER.value, extraction=extraction)

    assert view.status is ResearchStatus.READING
    assert view.coverage is OptionResearchCoverage.PARTIAL
    assert view.pages_read == 1


@pytest.mark.req("STATE-02", "OPTN-16")
@pytest.mark.parametrize(
    ("outcome", "coverage"),
    [
        (ExtractionOutcome.OPTIONS_RECORDED, OptionResearchCoverage.COMPLETE),
        (ExtractionOutcome.NO_OPTION_FOUND, OptionResearchCoverage.COMPLETE),
        (ExtractionOutcome.OPTIONS_UNVERIFIED, OptionResearchCoverage.PARTIAL),
    ],
)
def test_completed_extractions_keep_unverified_option_claims_distinct_from_empty_results(
    monkeypatch: pytest.MonkeyPatch,
    outcome: ExtractionOutcome,
    coverage: OptionResearchCoverage,
) -> None:
    extraction = SimpleNamespace(
        run_id=uuid.uuid4(),
        run_status=WorkState.COMPLETE,
        not_run=None,
        failure_class=None,
        outcome=outcome,
    )

    view = _research(monkeypatch, rights=RightsClass.COURSE_PROVIDER.value, extraction=extraction)

    assert view.status is ResearchStatus.COMPLETED
    assert view.coverage is coverage
    assert view.pages_read == 1


def test_demo_estimate_returns_a_typed_unavailable_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        routes_option_research,
        "run_estimate",
        lambda *_args, **_kwargs: SimpleNamespace(),
    )
    monkeypatch.setattr(
        routes_option_research,
        "spend_summary",
        lambda *_args: SimpleNamespace(limits=SimpleNamespace(run_limit_nano_usd=0)),
    )
    monkeypatch.setattr(
        routes_option_research,
        "visible_workspace",
        lambda *_args: SimpleNamespace(data_mode=DataMode.DEMO, synthetic=True),
    )
    deps = SimpleNamespace(
        clock=lambda: datetime(2026, 11, 3, tzinfo=UTC),
        models=object(),
        spend_defaults=object(),
    )

    with pytest.raises(CareerwrightError) as failure:
        routes_option_research._estimate(
            cast(Tx, object()), uuid.uuid4(), cast(ApiDependencies, deps)
        )

    assert failure.value.code is ErrorCode.MODE_NOT_SUPPORTED
