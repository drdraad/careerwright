"""Research records preserve checked source claims and expire before planning uses them."""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

import pytest

from careerwright.capability.commands import CapabilityData
from careerwright.db import Tx
from careerwright.evidence import option_store
from careerwright.evidence.option_extraction import (
    FoundCourse,
    ModelCourse,
    ModelScheme,
    OptionExtractionInput,
    OptionExtractionOutput,
    OptionExtractionProposal,
    VerifiedText,
    check_extraction,
)
from careerwright.evidence.option_records import (
    course_catalogue,
    record_catalogues,
    record_proposal,
)
from careerwright.identity import store as identity_store
from careerwright.identity.keyring import Keyring
from careerwright.identity.records import Run
from careerwright.money import Money
from careerwright.planning import commands
from careerwright.planning.catalogue import (
    ActionKind,
    Catalogue,
    Citation,
    CitationBasis,
    InstrumentKind,
    RecordState,
)
from careerwright.planning.figures import OfferingFigures, with_figures
from careerwright.planning.pack import TargetOptions
from tests.support.planning import trace_catalogue, trace_readiness


def test_research_refresh_and_expiry_change_catalogue_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    matrix = trace_readiness().matrix
    base = trace_catalogue()
    at = datetime(2026, 11, 3, tzinfo=UTC)
    rows = []
    for number in (1, 2):
        record_id = uuid.UUID(f"00000000-0000-4000-8000-{number:012d}")
        title = f"Research course {number}"
        quote = VerifiedText(text=title, source_sha256="a" * 64, start=0, end=len(title))
        catalogue = course_catalogue(
            FoundCourse(kind=ActionKind.LEARNING, title=quote),
            record_id,
            uuid.uuid4(),
            at,
            synthetic=True,
        )
        rows.append(
            SimpleNamespace(
                record_id=record_id,
                expires_at=at + timedelta(days=7),
                catalogue=catalogue,
            )
        )
    active = [(matrix.target_title, row) for row in rows]
    monkeypatch.setattr(commands, "pasted_texts", lambda *_: {})
    monkeypatch.setattr(commands, "active_records", lambda *_: active)
    monkeypatch.setattr(
        commands,
        "target_options",
        lambda *_: TargetOptions(
            target_title=matrix.target_title, pack_target_id=None, note=None, catalogue=base
        ),
    )

    def current_catalogue() -> Catalogue:
        [(_, options)] = commands.target_catalogues(
            cast(Tx, None),
            cast(Keyring, None),
            uuid.uuid4(),
            [matrix],
            [],
            cast(CapabilityData, SimpleNamespace(pack=None)),
        )
        assert options.catalogue is not None
        return options.catalogue

    both = current_catalogue()
    assert len(both.variants) == len(base.variants) + 2
    active.reverse()
    assert current_catalogue().label == both.label
    rows[0].expires_at = at + timedelta(days=8)
    assert current_catalogue().label != both.label
    active.pop()
    assert current_catalogue().label != both.label
    active.clear()
    assert current_catalogue().label == base.label


def test_checked_course_and_funding_become_proposed_records_with_short_lives() -> None:
    text = (
        "Nursing apprenticeship from City Hospital. Start 2027-09-01. "
        "Training 37 hours per week. Total fee £9,250. "
        "The 16 to 19 Bursary Fund is open. Aged 16 to 19."
    )
    context = OptionExtractionInput(text=text)
    proposal = check_extraction(
        OptionExtractionOutput(
            courses=[
                ModelCourse(
                    title="Nursing apprenticeship",
                    provider="City Hospital",
                    start="2027-09-01",
                    finish=None,
                    weekly_hours="37 hours per week",
                    total_cost="£9,250",
                )
            ],
            schemes=[
                ModelScheme(
                    programme="16 to 19 Bursary Fund",
                    kind="Bursary",
                    age_rule="Aged 16 to 19",
                )
            ],
        ),
        context,
    )
    attempt = uuid.uuid4()
    at = datetime(2026, 11, 3, tzinfo=UTC)

    records = record_catalogues(
        proposal, attempt, at, synthetic=False, source_url="https://example.org/course"
    )

    assert len(records) == 2
    _, kind, course, course_expires = records[0]
    assert kind == "course"
    assert course_expires == at + timedelta(days=7)
    [concept] = course.concepts
    [offering] = course.offerings
    assert concept.kind is ActionKind.APPRENTICESHIP
    assert concept.review_state is RecordState.PROPOSED
    [provider_fact] = concept.facts
    assert provider_fact.field == "provider"
    assert provider_fact.value == "City Hospital"
    assert provider_fact.cited is not None
    assert provider_fact.cited.source_hash == context.sha256
    assert provider_fact.cited.excerpt == "City Hospital"
    assert concept.cited is not None
    assert concept.cited.source_url == "https://example.org/course"
    unsafe = record_catalogues(proposal, attempt, at, synthetic=False, source_url="javascript:go()")
    unsafe_cited = unsafe[0][2].concepts[0].cited
    assert unsafe_cited is not None
    assert unsafe_cited.source_url is None
    assert offering.review_state is RecordState.PROPOSED
    assert offering.start is not None
    assert offering.start.isoformat() == "2027-09-01"
    assert offering.weekly_hours == 37
    assert offering.finish is None
    assert offering.unknown["finish"]
    [plan] = offering.payment_plans
    assert plan.payments == []
    assert plan.unknown is not None
    [quote] = [fact for fact in offering.facts if fact.field == "quoted_cost"]
    assert quote.value == "£9,250"
    assert quote.cited is not None
    assert quote.cited.source_id == str(attempt)
    assert quote.cited.source_hash == context.sha256
    assert quote.cited.excerpt == text[text.index("£9,250") : text.index("£9,250") + 6]
    answered = with_figures(
        offering,
        OfferingFigures(
            offering_id=offering.offering_id,
            cost=Money(minor_units=925_000, currency="GBP"),
        ),
        Citation(basis=CitationBasis.PERSON),
    )
    [payment] = answered.payment_plans[0].payments
    assert payment.amount.minor_units == 925_000
    assert answered.payment_plans[0].supplied_cost
    _, kind, funding, funding_expires = records[1]
    assert kind == "funding"
    assert funding_expires == at + timedelta(hours=48)
    assert funding_expires < at + timedelta(days=30)
    [instrument] = funding.instruments
    assert instrument.review_state is RecordState.PROPOSED
    assert instrument.kind is InstrumentKind.BURSARY
    assert instrument.rules[0].value == "Aged 16 to 19"


def test_unverified_claims_never_create_catalogue_records() -> None:
    context = OptionExtractionInput(text="A page with no stated course or funding scheme.")
    proposal = check_extraction(
        OptionExtractionOutput(
            courses=[
                ModelCourse(
                    title="Invented course",
                    provider=None,
                    start=None,
                    finish=None,
                    weekly_hours=None,
                    total_cost=None,
                )
            ],
            schemes=[],
        ),
        context,
    )

    assert record_catalogues(proposal, uuid.uuid4(), datetime.now(UTC), synthetic=False) == []


def test_two_courses_from_one_page_have_distinct_persistent_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = OptionExtractionInput(text="Nursing degree. Engineering degree.")
    courses = []
    for title in ("Nursing degree", "Engineering degree"):
        [course] = check_extraction(
            OptionExtractionOutput(
                courses=[
                    ModelCourse(
                        title=title,
                        provider=None,
                        start=None,
                        finish=None,
                        weekly_hours=None,
                        total_cost=None,
                    )
                ],
                schemes=[],
            ),
            context,
        ).courses
        courses.append(course)
    proposal = OptionExtractionProposal(
        prompt_version=context.prompt_version,
        text_sha256=context.sha256,
        courses=courses,
        schemes=[],
        dropped=0,
    )
    inserted: list[dict[str, object]] = []
    monkeypatch.setattr(
        option_store,
        "insert_record",
        lambda _tx, **kw: inserted.append(kw),
    )
    monkeypatch.setattr(identity_store, "append_event", lambda *_args, **_kw: None)
    workspace_id = uuid.uuid4()
    attempt_id = uuid.uuid4()

    count = record_proposal(
        cast(Tx, object()),
        cast(Run, SimpleNamespace(workspace_id=workspace_id, synthetic=False)),
        uuid.uuid4(),
        attempt_id,
        "https://example.org/courses",
        datetime.now(UTC),
        proposal,
    )

    assert count == 2
    assert [record["position"] for record in inserted] == [0, 1]
    assert [record["kind"] for record in inserted] == ["course", "course"]
    assert all(record["attempt_id"] == attempt_id for record in inserted)
    assert inserted[0]["record_id"] != inserted[1]["record_id"]
    assert [cast(Catalogue, record["catalogue"]).concepts[0].title for record in inserted] == [
        "Nursing degree",
        "Engineering degree",
    ]
