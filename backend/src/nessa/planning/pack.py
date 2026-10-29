"""The England option pack's records as planning records (ADR 0011 consequences; S5.1, S5.2).
Pure: no SQL, no network, no model.

The pack is read only through its pinned records and `Pack.value`: every consequential field
cites its claim (the span and the exact excerpt) or keeps the pack's reason it is unknown,
and every record keeps its review state and the date of its evidence (R9). Where the monthly
model needs more than a page states, the field stays unknown rather than guessed:

- an intake given as a month only stands on the grid as that month's first day, and says so;
- a finish comes only from one exact duration in weeks, months or years: a typical duration
  is never a bound, hours give no calendar length and a range gives no single finish;
- each way of taking a course (full time, part time) is its own offering, carrying the
  course's planned outcomes;
- a total fee with no stated schedule is one payment in the offering's first month
  (provisional, R6), and an instalment plan without its count or exact amount has no total;
- an apprenticeship is one composite action: its weekly hours, its offer gate and its
  application deadline, with its advertised wage kept as information, because a gross wage
  is never a confirmed take-home income;
- a funding page is an instrument's rules, and a course's funding conditions are facts: a
  person's status needs the person, so no variant here carries support.
"""

from calendar import monthrange
from datetime import date, timedelta

from pydantic import JsonValue

from nessa.catalogue.option_pack import (
    Claim,
    LearningOption,
    Pack,
    Ref,
    Unknown,
)
from nessa.catalogue.option_pack import (
    FundingInstrument as PackInstrument,
)
from nessa.catalogue.option_pack import (
    Offering as PackOffering,
)
from nessa.planning.catalogue import (
    ActionConcept,
    ActionKind,
    Basis,
    Catalogue,
    CatalogueLabel,
    Citation,
    Fact,
    FundingInstrument,
    InstrumentKind,
    OfferGate,
    Offering,
    Payment,
    PaymentPlan,
    RecordState,
    Recurring,
    Variant,
)

DAYS_PER_WEEK = 7
MONTHS_PER_YEAR = 12
WHOLE_FEE_DUE = 0  # month offset of a total fee with no stated schedule (provisional, R6)
PROVIDER_OUTCOME_NOTE = (
    "a provider's employment-outcome claim: unverified, since no method or denominator is "
    "given (spec section 10)"
)
_INSTRUMENT_KINDS = {
    "fee_waiver": InstrumentKind.FEE_WAIVER,
    "grant": InstrumentKind.GRANT,
    "loan": InstrumentKind.LOAN,
    "programme": InstrumentKind.PROGRAMME,
}


def pack_catalogue(pack: Pack, target_id: str) -> Catalogue:
    """One pack target's options, every funding instrument, and a variant per payment plan
    with no assumption of the person's."""
    reader = _Reader(pack)
    concepts, offerings, variants = [], [], []
    for option in (o for o in pack.learning_options if target_id in o.target_ids):
        source = next(o for o in pack.offerings if o.option_id == option.record_id)
        apprenticeship = isinstance(source.wage, str)  # a stated wage: a job with its training
        concepts.append(reader.concept(option, apprenticeship))
        for dated in reader.offerings(source, apprenticeship):
            offerings.append(dated)
            several = len(dated.payment_plans) > 1
            variants += [
                Variant(
                    variant_id=f"{dated.offering_id}~{plan.plan_id}"
                    if several
                    else dated.offering_id,
                    offering_id=dated.offering_id,
                    plan_id=plan.plan_id,
                )
                for plan in dated.payment_plans
            ]
    return Catalogue(
        label=CatalogueLabel(
            name=f"{pack.pack} {pack.pack_version}", dated=pack.dated, synthetic=False
        ),
        concepts=concepts,
        offerings=offerings,
        instruments=[reader.instrument(f) for f in pack.funding_instruments],
        variants=variants,
    )


class _Reader:
    def __init__(self, pack: Pack) -> None:
        self.pack = pack
        self.claims = {c.claim_id: c for c in pack.claims}
        self.sources = {s.source_id: s for s in pack.sources}

    def cite(self, claim: Claim) -> Citation:
        source = self.sources[claim.source_id]
        span = claim.span
        locator = (
            f"offsets {span.start}-{span.end}"
            if span.pointer is None
            else f"pointer {span.pointer}"
        )
        return Citation(
            basis=Basis.SOURCE,
            claim_id=claim.claim_id,
            source_id=claim.source_id,
            source_hash=source.sha256,
            locator=locator,
            excerpt=claim.excerpt,
            retrieved_on=source.retrieved_at.date(),
        )

    def fact(
        self, field: str, ref: Ref, *, value: JsonValue = None, note: str | None = None
    ) -> Fact:
        if isinstance(ref, Unknown):
            return Fact(field=field, unknown=ref.unknown, note=note)
        claim = self.claims[ref]
        shown = claim.value if value is None else value
        if shown is None:
            why = claim.note or "the page withholds or lacks the value"
            return Fact(field=field, unknown=why, cited=self.cite(claim), note=note)
        return Fact(field=field, value=shown, cited=self.cite(claim), note=note)

    def facts(self, claim_ids: list[str]) -> list[Fact]:
        found = []
        for claim_id in claim_ids:
            field = self.claims[claim_id].field
            note = PROVIDER_OUTCOME_NOTE if field == "provider_outcome_claim" else None
            found.append(self.fact(field, claim_id, note=note))
        return found

    def concept(self, option: LearningOption, apprenticeship: bool) -> ActionConcept:
        named = ("credential", "level", "awarding_body", "recognising_body", "delivery_mode")
        facts = [self.fact(name, getattr(option, name)) for name in (*named, "assessment")]
        return ActionConcept(
            concept_id=option.record_id,
            kind=ActionKind.APPRENTICESHIP if apprenticeship else ActionKind.LEARNING,
            title=_text(self.pack.value(option.title)),
            provider=_text(self.pack.value(option.provider)),
            review_state=RecordState(option.review_state.value),
            as_of=option.as_of,
            synthetic=False,
            cited=self.cite(self.claims[option.title]) if isinstance(option.title, str) else None,
            facts=[*facts, *self.facts(option.facts)],
            entry_requirements=self.facts(option.entry_requirements),
        )

    def offerings(self, source: PackOffering, apprenticeship: bool) -> list[Offering]:
        start, start_why, start_note = self._start(source.intake)
        parts = self.pack.value(source.duration)
        ways = parts if isinstance(parts, list) and len(parts) > 1 else [None]
        found: list[Offering] = []
        for way in ways:
            if way is None:
                duration = self.fact("duration", source.duration)
                part = parts[0] if isinstance(parts, list) and len(parts) == 1 else None
                offering_id = source.record_id
            else:
                duration = self.fact("duration", source.duration, value=[way])
                part = way
                mode = way.get("mode") if isinstance(way, dict) else None
                offering_id = f"{source.record_id}#{mode or len(found) + 1}"
            finish, finish_why = _finish(start, start_why, part, duration)
            hours, hours_why = self._hours(source.schedule)
            unknown = {
                name: why
                for name, why in (
                    ("start", start_why),
                    ("finish", finish_why),
                    ("weekly_hours", hours_why),
                )
                if why is not None
            }
            deadline = self._date(source.application_deadline)
            found.append(
                Offering(
                    offering_id=offering_id,
                    concept_id=source.option_id,
                    review_state=RecordState(source.review_state.value),
                    as_of=source.as_of,
                    start=start,
                    finish=finish,
                    unknown=unknown,
                    weekly_hours=hours,
                    payment_plans=self._plans(source),
                    application_deadline=deadline,
                    application_gate=f"admission:{offering_id}" if deadline else None,
                    offer_gate=OfferGate(accepted=False) if apprenticeship else None,
                    outcomes_from=None if offering_id == source.record_id else source.record_id,
                    synthetic=False,
                    facts=[
                        self.fact("intake", source.intake, note=start_note),
                        self.fact("application_deadline", source.application_deadline),
                        duration,
                        self.fact("schedule", source.schedule),
                        self.fact("fee_total", source.fee_total),
                        self.fact("instalment", source.instalment),
                        self.fact("wage", source.wage),
                        self.fact("location", source.location),
                        *self.facts(source.extra_costs),
                        *self.facts(source.funding_conditions),
                    ],
                )
            )
        return found

    def _start(self, ref: Ref) -> tuple[date | None, str | None, str | None]:
        if isinstance(ref, Unknown):
            return None, ref.unknown, None
        value = self.claims[ref].value
        if not isinstance(value, str):
            return None, self.claims[ref].note or "no start date is stated", None
        if len(value) == len("YYYY-MM"):
            note = "the month only: its first day stands for it on the monthly grid"
            return date.fromisoformat(f"{value}-01"), None, note
        return date.fromisoformat(value), None, None

    def _date(self, ref: Ref) -> date | None:
        value = self.pack.value(ref)
        return date.fromisoformat(value) if isinstance(value, str) and len(value) == 10 else None

    def _hours(self, ref: Ref) -> tuple[int | None, str | None]:
        value = self.pack.value(ref)
        hours = value.get("hours_per_week") if isinstance(value, dict) else None
        if isinstance(hours, int):
            return hours, None
        if isinstance(ref, Unknown):
            return None, ref.unknown
        return None, "no weekly hours are stated"

    def _plans(self, source: PackOffering) -> list[PaymentPlan]:
        extras, missing = [], []
        for claim_id in source.extra_costs:
            claim = self.claims[claim_id]
            amount = _minor(claim.value)
            if amount is None:
                missing.append(f"{claim_id}: {claim.note or 'its amount is not stated'}")
            else:
                extras.append(
                    Payment(
                        kind="extra",
                        amount_minor=amount,
                        month_offset=WHOLE_FEE_DUE,
                        cited=self.cite(claim),
                    )
                )
        fee = self.claims.get(source.fee_total) if isinstance(source.fee_total, str) else None
        fee_minor = _minor(fee.value) if fee is not None else None
        if fee is None or fee_minor is None:
            why = (
                source.fee_total.unknown
                if isinstance(source.fee_total, Unknown)
                else (fee.note if fee is not None else None) or "no fee is stated"
            )
            unknown = "; ".join([why, *missing])
            return [PaymentPlan(plan_id="as-stated", payments=extras, unknown=unknown)]
        whole = Payment(
            kind="fee", amount_minor=fee_minor, month_offset=WHOLE_FEE_DUE, cited=self.cite(fee)
        )
        known = "; ".join(missing) or None
        plans = [PaymentPlan(plan_id="pay-in-full", payments=[whole, *extras], unknown=known)]
        instalment = (
            self.claims.get(source.instalment) if isinstance(source.instalment, str) else None
        )
        value = instalment.value if instalment is not None else None
        amount = _minor(value)
        if instalment is not None and isinstance(value, dict) and amount is not None:
            count = value.get("count")
            plans.append(
                PaymentPlan(
                    plan_id="instalments",
                    payments=extras,
                    recurring=Recurring(
                        amount_minor=amount,
                        at_least=value.get("at_least") is True,
                        count=count if isinstance(count, int) else None,
                        cited=self.cite(instalment),
                    ),
                    unknown=known,
                )
            )
        return plans

    def instrument(self, record: PackInstrument) -> FundingInstrument:
        named = ("eligible_costs", "timing", "repayment", "published_on", "rules_updated_on")
        return FundingInstrument(
            instrument_id=record.record_id,
            programme=_text(self.pack.value(record.programme)),
            kind=_INSTRUMENT_KINDS[record.instrument_kind],
            jurisdiction=record.jurisdiction,
            review_state=RecordState(record.review_state.value),
            as_of=record.as_of,
            rules=self.facts(record.rules),
            facts=[
                *(self.fact(name, getattr(record, name)) for name in named),
                *self.facts(record.exclusions),
                *self.facts(record.facts),
            ],
        )


def _finish(
    start: date | None, start_why: str | None, part: object, duration: Fact
) -> tuple[date | None, str | None]:
    if duration.unknown is not None:
        return None, duration.unknown
    if not isinstance(part, dict):
        return None, "no single duration is stated"
    low, high, unit = part.get("minimum"), part.get("maximum"), part.get("unit")
    if part.get("typical"):
        return None, "a typical duration, never a bound"
    if part.get("unbounded"):
        return None, "no end is stated"
    if unit == "hours":
        return None, "a length in hours gives no calendar length"
    if not isinstance(low, int) or low != high:
        return None, "a range of durations, not one finish"
    if start is None:
        return None, start_why
    if unit == "weeks":
        return start + timedelta(days=DAYS_PER_WEEK * low - 1), None
    months = low * MONTHS_PER_YEAR if unit == "years" else low
    return _plus_months(start, months) - timedelta(days=1), None


def _plus_months(day: date, months: int) -> date:
    year, month = divmod(day.month - 1 + months, MONTHS_PER_YEAR)
    target_year, target_month = day.year + year, month + 1
    return date(target_year, target_month, min(day.day, monthrange(target_year, target_month)[1]))


def _minor(value: JsonValue) -> int | None:
    amount = value.get("minor_units") if isinstance(value, dict) else None
    return amount if isinstance(amount, int) else None


def _text(value: JsonValue) -> str | None:
    return value if isinstance(value, str) else None
