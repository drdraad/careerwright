"""Verified page claims as proposed planning records, never as reviewed pack data."""

import uuid
from datetime import datetime, timedelta

from careerwright.catalogue.planning import (
    ActionConcept,
    ActionKind,
    Catalogue,
    CatalogueLabel,
    Citation,
    CitationBasis,
    Fact,
    FundingInstrument,
    OfferGate,
    Offering,
    PaymentPlan,
    RecordState,
    Variant,
)
from careerwright.db import Tx
from careerwright.evidence import option_store
from careerwright.evidence.option_extraction import (
    FoundCourse,
    FoundScheme,
    OptionExtractionProposal,
    VerifiedText,
    date_value,
    hours_value,
)
from careerwright.identity import store as identity_store
from careerwright.identity.records import EventKind, Run

COURSE_AGE = timedelta(days=7)
FUNDING_AVAILABILITY_AGE = timedelta(hours=48)
FUNDING_RULES_AGE = timedelta(days=30)
NOT_STATED = "not stated on the page"
COST_UNCONFIRMED = "the quoted amount does not confirm the total payable or payment timing"


def _citation(
    value: VerifiedText, attempt_id: uuid.UUID, at: datetime, source_url: str | None = None
) -> Citation:
    return Citation(
        basis=CitationBasis.SOURCE,
        source_id=str(attempt_id),
        source_hash=value.source_sha256,
        source_url=source_url
        if source_url and source_url.startswith(("https://", "http://"))
        else None,
        locator=f"offsets {value.start}-{value.end}",
        excerpt=value.text[:200],
        retrieved_on=at.date(),
    )


def _label(at: datetime, synthetic: bool) -> CatalogueLabel:
    return CatalogueLabel(name="researched options", dated=at.date(), synthetic=synthetic)


def course_catalogue(
    course: FoundCourse,
    record_id: uuid.UUID,
    attempt_id: uuid.UUID,
    at: datetime,
    *,
    synthetic: bool,
    source_url: str | None = None,
) -> Catalogue:
    identifier = f"research:{record_id}"
    plan = PaymentPlan(
        plan_id="source",
        unknown=COST_UNCONFIRMED if course.total_cost is not None else NOT_STATED,
    )
    start = date_value(course.start)
    finish = date_value(course.finish)
    hours = hours_value(course.weekly_hours)
    facts = [
        Fact(field=field, value=value, cited=_citation(quote, attempt_id, at, source_url))
        for field, quote, value in (
            ("start", course.start, start.isoformat() if start else None),
            ("finish", course.finish, finish.isoformat() if finish else None),
            ("weekly_hours", course.weekly_hours, hours),
            (
                "quoted_cost",
                course.total_cost,
                course.total_cost.text if course.total_cost else None,
            ),
        )
        if quote is not None and value is not None
    ]
    concept = ActionConcept(
        concept_id=identifier,
        kind=course.kind,
        title=course.title.text,
        provider=course.provider.text if course.provider else None,
        review_state=RecordState.PROPOSED,
        as_of=at.date(),
        synthetic=synthetic,
        cited=_citation(course.title, attempt_id, at, source_url),
        facts=(
            [
                Fact(
                    field="provider",
                    value=course.provider.text,
                    cited=_citation(course.provider, attempt_id, at, source_url),
                )
            ]
            if course.provider
            else []
        ),
    )
    offering = Offering(
        offering_id=identifier,
        concept_id=identifier,
        review_state=RecordState.PROPOSED,
        as_of=at.date(),
        start=start,
        finish=finish,
        weekly_hours=hours,
        unknown={
            field: NOT_STATED
            for field, value in (("start", start), ("finish", finish), ("weekly_hours", hours))
            if value is None
        },
        payment_plans=[plan],
        offer_gate=OfferGate(accepted=False) if course.kind is ActionKind.APPRENTICESHIP else None,
        synthetic=synthetic,
        cited=_citation(course.title, attempt_id, at, source_url),
        facts=facts,
    )
    return Catalogue(
        label=_label(at, synthetic),
        concepts=[concept],
        offerings=[offering],
        variants=[Variant(variant_id=identifier, offering_id=identifier, plan_id="source")],
    )


def funding_catalogue(
    scheme: FoundScheme,
    record_id: uuid.UUID,
    attempt_id: uuid.UUID,
    at: datetime,
    *,
    synthetic: bool,
    source_url: str | None = None,
) -> Catalogue:
    cite = _citation(scheme.programme, attempt_id, at, source_url)
    rules = (
        [
            Fact(
                field="eligibility_age",
                value=scheme.age_rule.text,
                cited=_citation(scheme.age_rule, attempt_id, at, source_url),
            )
        ]
        if scheme.age_rule
        else []
    )
    instrument = FundingInstrument(
        instrument_id=f"research:{record_id}",
        programme=scheme.programme.text,
        kind=scheme.kind,
        jurisdiction="not confirmed",
        review_state=RecordState.PROPOSED,
        as_of=at.date(),
        rules=rules,
        facts=[Fact(field="programme", value=scheme.programme.text, cited=cite)],
    )
    return Catalogue(
        label=_label(at, synthetic),
        concepts=[],
        offerings=[],
        instruments=[instrument],
        variants=[],
    )


def record_catalogues(
    proposal: OptionExtractionProposal,
    attempt_id: uuid.UUID,
    at: datetime,
    *,
    synthetic: bool,
    source_url: str | None = None,
) -> list[tuple[uuid.UUID, str, Catalogue, datetime]]:
    """One course and one scheme at most; funding availability expires before its rules."""
    records = []
    for course in proposal.courses:
        record_id = uuid.uuid4()
        catalogue = course_catalogue(
            course, record_id, attempt_id, at, synthetic=synthetic, source_url=source_url
        )
        records.append((record_id, "course", catalogue, at + COURSE_AGE))
    for scheme in proposal.schemes:
        record_id = uuid.uuid4()
        catalogue = funding_catalogue(
            scheme, record_id, attempt_id, at, synthetic=synthetic, source_url=source_url
        )
        records.append(
            (
                record_id,
                "funding",
                catalogue,
                at + min(FUNDING_AVAILABILITY_AGE, FUNDING_RULES_AGE),
            )
        )
    return records


def record_proposal(
    tx: Tx,
    run: Run,
    research_id: uuid.UUID,
    attempt_id: uuid.UUID,
    source_url: str,
    at: datetime,
    proposal: OptionExtractionProposal,
) -> int:
    """Checked page claims join only this workspace, as proposed records."""
    found = record_catalogues(
        proposal, attempt_id, at, synthetic=run.synthetic, source_url=source_url
    )
    positions: dict[str, int] = {}
    for record_id, kind, catalogue, expires_at in found:
        position = positions.get(kind, 0)
        positions[kind] = position + 1
        option_store.insert_record(
            tx,
            record_id=record_id,
            workspace_id=run.workspace_id,
            research_id=research_id,
            attempt_id=attempt_id,
            kind=kind,
            position=position,
            catalogue=catalogue,
            source_url=source_url,
            retrieved_at=at,
            expires_at=expires_at,
        )
    if found:
        identity_store.append_event(
            tx,
            run.workspace_id,
            EventKind.RESEARCH_UPDATED,
            str(research_id),
            detail={"records": len(found)},
        )
    return len(found)
