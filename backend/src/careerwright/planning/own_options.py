"""Options the person adds themselves (S5.7, Task 12b; ADR 0011's and ADR 0013's Task 12b
amendments). Pure: no SQL, no network, no model.

The person pastes a course or funding page's text, or types its details. The option is saved
as their own workspace record, `review_state: proposed`, dated, with its source, and is never
reviewed: the planning catalogue reads it beside the pack, and a route through it is always
qualified (OPTN-09). No run kind reads it and no model fills it (the infrastructure is frozen
for L0).

Every value comes from the person:

- **Words** (a title, a provider, an entry requirement): typed, or chosen as a span of their
  pasted text, in UTF-16 code units as a browser's selection counts them (Task 10A's span
  rule, `capability.adverts`). A chosen span's words are read back from the kept text.
- **Figures** (a start, a finish, weekly hours, a cost): typed, never read from the text by
  Careerwright; each may cite the span of their pasted text it comes from, checked the same
  way. Turning words into a date or an amount would be a new language rule (R11), so it is
  left to the person.

An unknown figure stays unknown with its reason, never zero: an option with no cost leaves its
routes unresolved.
"""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from careerwright.capability.adverts import AdvertSpan, check_spans, read_spans
from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage
from careerwright.money import Money
from careerwright.planning.catalogue import (
    ActionConcept,
    ActionKind,
    Catalogue,
    CatalogueLabel,
    Citation,
    CitationBasis,
    Fact,
    Hours,
    OfferGate,
    Offering,
    Payment,
    PaymentPlan,
    RecordState,
    Variant,
)
from careerwright.planning.pack import WHOLE_FEE_DUE

OWN_PREFIX = "own:"  # every own concept, offering and variant ID starts with it
OWN_LABEL = "own options"  # the catalogue label of a target with only the person's options
MAX_ENTRY_REQUIREMENTS = 5
NOT_GIVEN = "not given yet"  # why an own option's fact is unknown: never zero
Text = Annotated[str, Field(min_length=1, max_length=300)]
OptionId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,59}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OwnWords(StrictModel):
    """Words the person typed, or a span they chose in their pasted text: exactly one."""

    typed: Text | None = None
    span: AdvertSpan | None = None

    @model_validator(mode="after")
    def _one(self) -> Self:
        if (self.typed is None) == (self.span is None):
            raise ValueError("words are typed or chosen as a span of the text, one of them")
        return self


class CitedFigure(StrEnum):
    START = "start"
    FINISH = "finish"
    WEEKLY_HOURS = "weekly_hours"
    COST = "cost"


class OwnOptionInput(StrictModel):
    """An option as the person adds it: every value theirs. Null: not given yet."""

    option_id: OptionId = Field(description="The person's own short name for it, unique.")
    target: Text = Field(description="The target role it is for: one of the profile's.")
    kind: Literal[ActionKind.LEARNING, ActionKind.APPRENTICESHIP] = ActionKind.LEARNING
    text_id: uuid.UUID | None = Field(
        default=None, description="The text they pasted for it, if any: its source."
    )
    title: OwnWords
    provider: OwnWords | None = None
    start: date | None = None
    finish: date | None = None
    weekly_hours: Hours | None = None
    cost: Money | None = Field(
        default=None, description="The whole of what they will pay, due in its first month."
    )
    entry_requirements: list[OwnWords] = Field(
        default_factory=list, max_length=MAX_ENTRY_REQUIREMENTS
    )
    cited: dict[CitedFigure, AdvertSpan] = Field(
        default_factory=dict,
        description="For a typed figure, the span of the pasted text it comes from.",
    )

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.start is not None and self.finish is not None and self.finish < self.start:
            raise ValueError("a finish is not before its start")
        if self.text_id is None and self.spans():
            raise ValueError("a span is chosen in the pasted text: name the text")
        given = {
            CitedFigure.START: self.start,
            CitedFigure.FINISH: self.finish,
            CitedFigure.WEEKLY_HOURS: self.weekly_hours,
            CitedFigure.COST: self.cost,
        }
        if any(given[figure] is None for figure in self.cited):
            raise ValueError("a cited figure is given")
        return self

    def spans(self) -> list[AdvertSpan]:
        """Every span the option chooses in its text."""
        words = [self.title, self.provider, *self.entry_requirements]
        return [
            *(w.span for w in words if w is not None and w.span is not None),
            *self.cited.values(),
        ]

    @property
    def concept_id(self) -> str:
        return f"{OWN_PREFIX}{self.option_id}"


class OwnOption(OwnOptionInput):
    """A stored option: who added it and when (its date), kept while it is unchanged."""

    recorded_by: uuid.UUID
    recorded_at: datetime


@dataclass(frozen=True)
class PastedText:
    """A pasted text as it was kept (third parties' contact details removed), with its hash."""

    text: str
    sha256: str


def check_option(option: OwnOptionInput, text: PastedText | None) -> str | None:
    """Why an option's spans do not fit its text, or None. Each span is checked as its own
    selection (`capability.adverts.check_spans`): inside the text, on character boundaries,
    not empty, blank or too long."""
    spans = option.spans()
    if not spans:
        return None
    if text is None:
        return "text_not_found"
    for span in spans:
        try:
            check_spans(text.text, [span])
        except CareerwrightError as error:  # it names the rule broken
            return str(error.details.get("reason", "span_not_in_text"))
    return None


def _words(words: OwnWords, text: PastedText | None, cite: "_Cite") -> tuple[str, Citation]:
    if words.typed is not None:
        return words.typed, cite.typed()
    if words.span is None or text is None:
        raise CareerwrightError(  # a stored option's text is never removed: a failure, said
            ErrorCode.INTERNAL_ERROR,
            "An option's pasted text could not be read.",
            stage=ErrorStage.PLANNING,
        )
    [selected] = read_spans(text.text, [words.span])
    return selected.excerpt, cite.span(words.span, selected.excerpt)


@dataclass(frozen=True)
class _Cite:
    option: OwnOption
    text: PastedText | None

    def typed(self) -> Citation:
        return Citation(
            basis=CitationBasis.PERSON,
            source_id=str(self.option.text_id) if self.option.text_id else None,
            source_hash=self.text.sha256 if self.text else None,
            locator="typed by the person",
            retrieved_on=self.option.recorded_at.date(),
        )

    def span(self, span: AdvertSpan, excerpt: str) -> Citation:
        return Citation(
            basis=CitationBasis.PERSON,
            source_id=str(self.option.text_id),
            source_hash=self.text.sha256 if self.text else None,
            locator=f"utf-16 offsets {span.start}-{span.end}",
            excerpt=excerpt,
            retrieved_on=self.option.recorded_at.date(),
        )

    def figure(self, figure: CitedFigure) -> Citation:
        span = self.option.cited.get(figure)
        if span is None or self.text is None:
            return self.typed()
        [selected] = read_spans(self.text.text, [span])
        return self.span(span, selected.excerpt)


def own_records(
    option: OwnOption, text: PastedText | None
) -> tuple[ActionConcept, Offering, Variant]:
    """One own option as planning records: a concept, one dated offering and its variant, all
    `proposed` and dated by when the person added it."""
    cite = _Cite(option, text)
    title, title_cited = _words(option.title, text, cite)
    provider = _words(option.provider, text, cite)[0] if option.provider else None
    entry = []
    for words in option.entry_requirements:
        value, cited = _words(words, text, cite)
        entry.append(Fact(field="entry_requirement", value=value, cited=cited))
    as_of = option.recorded_at.date()
    concept = ActionConcept(
        concept_id=option.concept_id,
        kind=option.kind,
        title=title,
        provider=provider,
        review_state=RecordState.PROPOSED,
        as_of=as_of,
        synthetic=False,
        added_by_person=True,
        cited=title_cited,
        entry_requirements=entry,
    )
    unknown = {
        name: NOT_GIVEN
        for name, value in (
            ("start", option.start),
            ("finish", option.finish),
            ("weekly_hours", option.weekly_hours),
        )
        if value is None
    }
    plan = (
        PaymentPlan(
            plan_id="own",
            payments=[
                Payment(
                    kind="fee",
                    amount=option.cost,
                    month_offset=WHOLE_FEE_DUE,
                    cited=cite.figure(CitedFigure.COST),
                )
            ],
        )
        if option.cost is not None
        else PaymentPlan(plan_id="own", unknown=NOT_GIVEN)
    )
    facts = [
        Fact(field=f.value, value=str(v), cited=cite.figure(f))
        for f, v in (
            (CitedFigure.START, option.start),
            (CitedFigure.FINISH, option.finish),
            (CitedFigure.WEEKLY_HOURS, option.weekly_hours),
        )
        if v is not None
    ]
    offering = Offering(
        offering_id=option.concept_id,
        concept_id=option.concept_id,
        review_state=RecordState.PROPOSED,
        as_of=as_of,
        start=option.start,
        finish=option.finish,
        unknown=unknown,
        weekly_hours=option.weekly_hours,
        payment_plans=[plan],
        offer_gate=OfferGate(accepted=False) if option.kind is ActionKind.APPRENTICESHIP else None,
        synthetic=False,
        cited=title_cited,
        facts=facts,
    )
    variant = Variant(variant_id=option.concept_id, offering_id=option.concept_id, plan_id="own")
    return concept, offering, variant


def beside(
    pack: Catalogue | None,
    options: Sequence[OwnOption],
    texts: Mapping[uuid.UUID, PastedText],
) -> Catalogue | None:
    """A target's catalogue: the pack's options, then the person's own for that target. With
    neither, None (never an empty catalogue). With only their own, it is labelled as theirs,
    dated by the latest one added."""
    if not options:
        return pack
    records = [own_records(o, texts.get(o.text_id) if o.text_id else None) for o in options]
    label = (
        pack.label
        if pack is not None
        else CatalogueLabel(
            name=OWN_LABEL, dated=max(o.recorded_at.date() for o in options), synthetic=False
        )
    )
    return Catalogue(
        label=label,
        concepts=[*(pack.concepts if pack else []), *(c for c, _, _ in records)],
        offerings=[*(pack.offerings if pack else []), *(o for _, o, _ in records)],
        instruments=list(pack.instruments) if pack else [],
        variants=[*(pack.variants if pack else []), *(v for _, _, v in records)],
    )


def stamped_options(
    new: Sequence[OwnOptionInput],
    previous: Sequence[OwnOption],
    *,
    by: uuid.UUID,
    at: datetime,
) -> list[OwnOption]:
    """An option unchanged since `previous` keeps who added it and when; a new or changed one
    is this actor's, now (its date moves: the record changed)."""
    before = {o.option_id: o for o in previous}
    found = []
    for option in new:
        kept = before.get(option.option_id)
        if kept is not None and as_input(kept) == option:
            found.append(kept)
        else:
            found.append(OwnOption(**option.model_dump(), recorded_by=by, recorded_at=at))
    return found


def as_input(option: OwnOption) -> OwnOptionInput:
    return OwnOptionInput.model_validate(option.model_dump(exclude={"recorded_by", "recorded_at"}))


def is_own(identifier: str) -> bool:
    return identifier.startswith(OWN_PREFIX)
