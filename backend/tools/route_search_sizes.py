"""Measure the instance sizes at which the route search reaches complete coverage within the M0
limits (plan Sprint 6a, S6.7; OPT1-16; spec section 12, "Consequence of the M0 limits").

The reviewed option pack has four targets and at most four options each, and every one of its
offerings lacks a date, a cost or a timetable a search needs
(`tests/domain/test_route_search_pack.py`). So the growth is measured on **synthetic
pack-shaped instances**, labelled synthetic and never product data. Each has `concepts` courses
like TRACE-01's and the pack's:

- course c lasts 1 to 6 months (cycling), takes 4 to 10 hours a week and costs £300 to £1,500,
  paid in full in its first month (even c) or in equal monthly instalments (odd c);
- its first intake is spread across the horizon, in month 5c mod months + 1 (`spread`, the
  default: every month of the horizon holds an intake once there are enough courses); a
  second start, if any, three months later (one that falls after the horizon is still a start
  the search must consider). The first measurement used `early`, month c mod min(months, 6) +
  1, which keeps every intake in months 1 to 9 whatever the horizon, so a longer horizon there
  grows only the cost of each check, never the tree (review 13a, Important 3);
- every fourth course runs with a reduced-hours work pattern (20 hours at £1,500 a month);
- the target has three skill rows at level 2, the person is at level 1 in each, and course c
  brings one row (odd c) or two rows (even c) to level 2, so a route needs two or three
  courses.

Three people (families) share the courses, with TRACE-01's £2,000 a month take-home pay over 30
hours, £1,000 living costs and an economic comparison against staying put:

- `p01`: P01's limits: £1,500 direct-spend and monthly payment caps, a £500 reserve, £6,000
  opening cash, 40 hours a week available;
- `relaxed`: a £5,000 direct-spend cap, the same monthly cap, 45 hours a week;
- `unbounded`: no limit binds (a cap of £1,000,000, every hour of the week, a large balance),
  so nothing can be pruned: the search checks the whole selection space, the worst case.

Each run uses the M0 limits (1,000,000 expanded states, 30 seconds, 50,000 archived
schedules). A sweep grows the number of concepts for each family, starts per concept and
horizon, and stops growing it after the first run that does not complete: the instances are
nested, so a larger one only adds to the tree. A run stopped by a limit is reported as "not
complete at that size", never as infeasible. Times are wall-clock times on the machine named.

Run from `backend/`: `uv run --locked python -m tools.route_search_sizes`.
"""

import argparse
import platform
import sys
import time
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict

from careerwright.capability.evidence import Answer, SkillEvidence
from careerwright.capability.matrix import (
    Importance,
    Matrix,
    MatrixCoverage,
    MatrixRow,
    MatrixSources,
    RowKind,
    RubricView,
    apply_edits,
)
from careerwright.capability.outcomes import (
    Confidence,
    EvidenceKind,
    OutcomeReview,
    OutcomeSpan,
    OutcomeType,
    PlannedOutcome,
    Provenance,
)
from careerwright.money import Money
from careerwright.planning.catalogue import (
    ActionConcept,
    ActionKind,
    Catalogue,
    CatalogueLabel,
    Citation,
    CitationBasis,
    Offering,
    Payment,
    PaymentPlan,
    RecordState,
    Variant,
    WorkPattern,
    WorkPatternKind,
)
from careerwright.planning.compiler import (
    Baseline,
    Continuation,
    MonthlyInput,
    PlanningInputs,
    ReadinessBasis,
    compile_input,
)
from careerwright.planning.search import M0SearchLimits, search_routes

Family = Literal["p01", "relaxed", "unbounded"]
FAMILIES: tuple[Family, ...] = ("p01", "relaxed", "unbounded")
Intakes = Literal["spread", "early"]
SPREAD_STEP = 5  # months between successive courses' first intakes, wrapping round the horizon
CONCEPTS = (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24)
STARTS = (1, 2)
HORIZONS = (6, 12, 24)
START = date(2027, 1, 1)
SECOND_START_AFTER = 3  # months between a course's two intakes
PAY = 200_000  # TRACE-01's take-home pay a month
JOB_HOURS = 30
LIVING = 100_000
REDUCED = (20, 150_000)  # every fourth course's work pattern: hours a week, pay a month
ROWS = ("synthetic:skill-a", "synthetic:skill-b", "synthetic:skill-c")
RUBRIC = "synthetic-rubric-1"
REQUIRED = 2
UNBOUNDED = 100_000_000
SYNTHETIC = Citation(basis=CitationBasis.FIXTURE, locator="tools.route_search_sizes")
RECORDED_AT = datetime(2027, 1, 1, tzinfo=UTC)
PERSON_ID = "00000000-0000-4000-8000-0000000000a1"


class Measurement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family: Family
    intakes: Intakes
    concepts: int
    starts: int
    months: int
    selection_space: int
    complete: bool
    stop_reason: str | None
    expanded_states: int
    archived: int
    elapsed_ms: int  # the search's own clock, which its 30-second limit reads
    total_ms: int  # the whole call: the search, then the layers, families and points


def instance(
    concepts: int, starts: int, months: int, family: Family, intakes: Intakes = "spread"
) -> MonthlyInput:
    """A synthetic pack-shaped instance (the module docstring describes it)."""
    options = [_course(c, s, months, intakes) for c in range(concepts) for s in range(starts)]
    catalogue = Catalogue(
        label=CatalogueLabel(name="synthetic pack-shaped instance", dated=START, synthetic=True),
        concepts=[_concept(c) for c in range(concepts)],
        offerings=[o for o, _ in options],
        variants=[v for _, v in options],
    )
    teaches = {o.offering_id: _rows(int(o.concept_id.rsplit("-", 1)[1])) for o, _ in options}
    return compile_input(_person(months, family), catalogue, readiness=_readiness(teaches))


def measure(
    concepts: int, starts: int, months: int, family: Family, intakes: Intakes = "spread"
) -> Measurement:
    monthly = instance(concepts, starts, months, family, intakes)
    began = time.perf_counter()
    result = search_routes(monthly, limits=M0SearchLimits())
    total_ms = round((time.perf_counter() - began) * 1000)
    return Measurement(
        family=family,
        intakes=intakes,
        concepts=concepts,
        starts=starts,
        months=months,
        selection_space=result.instance.selection_space,
        complete=result.coverage.value == "complete",
        stop_reason=result.stop_reason.value if result.stop_reason is not None else None,
        expanded_states=result.expanded_states,
        archived=len(result.schedules),
        elapsed_ms=result.elapsed_ms,
        total_ms=total_ms,
    )


def sweep(
    families: tuple[Family, ...] = FAMILIES,
    concepts: tuple[int, ...] = CONCEPTS,
    starts: tuple[int, ...] = STARTS,
    horizons: tuple[int, ...] = HORIZONS,
    intakes: Intakes = "spread",
) -> list[Measurement]:
    found = []
    for family in families:
        for start_count in starts:
            for months in horizons:
                for size in concepts:
                    run = measure(size, start_count, months, family, intakes)
                    found.append(run)
                    print(_row(run), file=sys.stderr, flush=True)
                    if not run.complete:
                        break
    return found


def table(runs: list[Measurement]) -> str:
    lines = [
        f"Measured {datetime.now(UTC):%Y-%m-%d} on {platform.machine()} "
        f"({platform.system()}), Python {platform.python_version()}, M0 limits "
        "(1,000,000 states, 30 s, 50,000 schedules).",
        "",
        "| Family | Intakes | Concepts | Starts | Months | Selection space | Coverage "
        "| Expanded states | Archived | Search (s) | Total (s) | ms per state |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|",
        *(_row(run) for run in runs),
    ]
    return "\n".join(lines)


def _row(run: Measurement) -> str:
    coverage = "complete" if run.complete else f"not complete at that size ({run.stop_reason})"
    per_state = run.elapsed_ms / run.expanded_states if run.expanded_states else 0
    return (
        f"| {run.family} | {run.intakes} | {run.concepts} | {run.starts} | {run.months} | "
        f"{run.selection_space:,} | {coverage} | {run.expanded_states:,} | {run.archived:,} | "
        f"{run.elapsed_ms / 1000:.2f} | {run.total_ms / 1000:.2f} | {per_state:.3f} |"
    )


def _concept(c: int) -> ActionConcept:
    return ActionConcept(
        concept_id=f"synthetic:course-{c}",
        kind=ActionKind.LEARNING,
        title=f"Synthetic course {c}",
        provider="synthetic provider",
        review_state=RecordState.ACCEPTED_ASSUMPTION,
        synthetic=True,
        cited=SYNTHETIC,
    )


def _course(c: int, start: int, months: int, intakes: Intakes) -> tuple[Offering, Variant]:
    length = 1 + c % 6
    month = (SPREAD_STEP * c) % months if intakes == "spread" else c % min(months, 6)
    first = month + start * SECOND_START_AFTER
    begins = _month(START, first)
    fee = 30_000 + 30_000 * (c % 5)
    if c % 2 == 0:
        amounts = [fee]
    else:
        amounts = [fee // length + fee % length] + [fee // length] * (length - 1)
    offering = Offering(
        offering_id=f"synthetic:intake-{c}-{start}",
        concept_id=f"synthetic:course-{c}",
        review_state=RecordState.ACCEPTED_ASSUMPTION,
        start=begins,
        finish=_month(begins, length) - timedelta(days=1),
        weekly_hours=4 + 2 * (c % 4),
        payment_plans=[
            PaymentPlan(
                plan_id="as-stated",
                payments=[
                    Payment(kind="fee", amount=_gbp(a), month_offset=n, cited=SYNTHETIC)
                    for n, a in enumerate(amounts)
                ],
            )
        ],
        synthetic=True,
        cited=SYNTHETIC,
    )
    hours, pay = REDUCED
    pattern = (
        WorkPattern(
            kind=WorkPatternKind.REDUCED_HOURS,
            hours_per_week=hours,
            net_income=_gbp(pay),
            cited=SYNTHETIC,
        )
        if c % 4 == 3
        else None
    )
    variant = Variant(
        variant_id=offering.offering_id,
        offering_id=offering.offering_id,
        plan_id="as-stated",
        work_pattern=pattern,
    )
    return offering, variant


def _rows(c: int) -> tuple[str, ...]:
    if c % 2:
        return (ROWS[c % 3],)
    return (ROWS[c % 3], ROWS[(c + 1) % 3])


def _person(months: int, family: Family) -> PlanningInputs:
    limits = {
        "p01": (150_000, 150_000, 50_000, 600_000, 40),
        "relaxed": (500_000, 150_000, 50_000, 600_000, 45),
        "unbounded": (UNBOUNDED, UNBOUNDED, 0, UNBOUNDED, 168),
    }[family]
    direct_cap, monthly_cap, reserve, opening, available = limits
    return PlanningInputs(
        planning_start=START,
        horizon_months=months,
        objective_basis="economic",
        baseline=Baseline(
            label="staying in the current role", net_income_by_month=[PAY] * months, cited=SYNTHETIC
        ),
        continuation=Continuation(
            label="the current role, unchanged",
            hours_per_week=JOB_HOURS,
            net_income_by_month=[PAY] * months,
            cited=SYNTHETIC,
        ),
        opening_cash_minor=opening,
        living_outgoings_by_month=[LIVING] * months,
        reserve_minor=reserve,
        direct_spend_cap_minor=direct_cap,
        monthly_payment_cap_minor=monthly_cap,
        weekly_availability_by_month=[available] * months,
        scenario_delay_months=2,
        synthetic=True,
    )


def _readiness(teaches: dict[str, tuple[str, ...]]) -> ReadinessBasis:
    return ReadinessBasis(
        matrix=_matrix(),
        evidence=[_self_report(row) for row in ROWS],
        statements=[],
        outcomes=[_outcome(o, row) for o, rows in teaches.items() for row in rows],
        evidence_version=1,
    )


def _matrix() -> Matrix:
    rows = [
        MatrixRow(
            row_id=row,
            subject=row,
            label=row.removeprefix("synthetic:"),
            kind=RowKind.SKILL,
            importance=Importance.ESSENTIAL,
            source_importance=Importance.ESSENTIAL,
            observable_task=f"a synthetic task for {row}",
            required_level=REQUIRED,
            rubric=RubricView(version_id=RUBRIC, anchors={}, review_state="proposed"),
        )
        for row in ROWS
    ]
    matrix = Matrix(
        target_key="synthetic pack-shaped target",
        target_title="Synthetic pack-shaped target",
        synthetic=True,
        sources=MatrixSources(
            pack_version="synthetic",
            pack_dated=START,
            reference_version="synthetic",
            reference_dated=START,
            reference_review_state="proposed",
            esco_release=None,
            occupation=None,
            occupation_note=None,
            pack_target=None,
        ),
        coverage=MatrixCoverage(
            exemplars=0,
            full_text_vacancies=0,
            snippet_vacancies=0,
            unknown_description_vacancies=0,
            posting_copies=0,
            esco_essential=0,
            esco_optional=0,
            modelled_rows=len(rows),
            not_modelled_rows=0,
        ),
        rows=rows,
    )
    return apply_edits(matrix, [])


def _self_report(row: str) -> SkillEvidence:
    return SkillEvidence.model_validate(
        {
            "evidence_id": f"00000000-0000-4000-8000-{ROWS.index(row):012d}",
            "subject": row,
            "rubric_version": RUBRIC,
            "answer": Answer.DONE_INDEPENDENTLY,
            "self_assessed_level": REQUIRED - 1,
            "example": "a synthetic piece of work",
            "last_done": "2026-09",
            "independence": "independent",
            "recorded_by": PERSON_ID,
            "recorded_at": RECORDED_AT,
        }
    )


def _outcome(offering_id: str, row: str) -> PlannedOutcome:
    return PlannedOutcome(
        outcome_id=f"{offering_id}:{row}",
        offering_id=offering_id,
        option_id=offering_id,
        option_title=offering_id,
        skill_id=row,
        outcome_type=OutcomeType.SKILL_LEVEL,
        level_on_completion=REQUIRED,
        evidence_kind=EvidenceKind.ASSESSED_WORK_SAMPLE,
        confidence=Confidence.PROVISIONAL,
        source_span=OutcomeSpan(
            claim_id=None,
            source_id="synthetic",
            source_hash="0" * 64,
            start=0,
            end=1,
            pointer=None,
            retrieved_at=None,
            excerpt="synthetic",
        ),
        rubric_version=RUBRIC,
        review_state=OutcomeReview.ACCEPTED_ASSUMPTION,
        provenance=Provenance.PROVIDER_CLAIM,
        as_of=START,
    )


def _month(first: date, months: int) -> date:
    """The first day of the month `months` after `first`'s month."""
    year, month = divmod(first.month - 1 + months, 12)
    return date(first.year + year, month + 1, 1)


def _gbp(minor: int) -> Money:
    return Money(minor_units=minor, currency="GBP")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--family", choices=FAMILIES, action="append")
    parser.add_argument("--max-concepts", type=int, default=max(CONCEPTS))
    parser.add_argument("--intakes", choices=("spread", "early"), default="spread")
    arguments = parser.parse_args(argv)
    families = tuple(arguments.family) if arguments.family else FAMILIES
    sizes = tuple(n for n in CONCEPTS if n <= arguments.max_concepts)
    print(table(sweep(families, sizes, intakes=arguments.intakes)))


if __name__ == "__main__":
    main()
