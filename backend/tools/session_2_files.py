"""Session 2's two new question sets, derived and never edited by hand (Task 11; ADR 0013):

- the TRACE-01 checker on P01's real option set (H-07, TEST1-14): what the checker read about
  P01 (synthetic, from the M0 fixture pack) and about P01's real options (the pinned option
  pack 0.1.0, every record proposed), each field beside its span, then what it concluded.
  Questions T1, T2 and on;
- the capability reference 0.1.0 (its rubrics, required levels, ESCO crosswalks and gate
  types) and a proposed level for every planned outcome in the pack under those rubrics,
  each beside its span. Questions R1, R2 and on.

The proposed levels are an agent's proposals in the package only: pack 0.1.0 is frozen, and
Task 7c publishes the reviewed levels in the next pack version. Fast tests check the
committed files against this tool's output, so the numbers stay stable for the transcriber.
Run from `backend/`: `uv run --locked python -m tools.session_2_files`.
"""

import json
import math
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from nessa.capability.evidence import Answer, SkillEvidence
from nessa.capability.matrix import build_matrix
from nessa.capability.outcomes import pack_outcomes
from nessa.capability.reference import Reference, load_reference
from nessa.catalogue.option_pack import Pack, load_pack
from nessa.planning.catalogue import (
    AwardState,
    Basis,
    Catalogue,
    Citation,
    EligibilityStatus,
    Fact,
    InstrumentKind,
    RecordState,
    Support,
)
from nessa.planning.checker import (
    FindingKind,
    RouteCheck,
    RouteEvaluation,
    Scenario,
    Verdict,
    evaluate_route,
)
from nessa.planning.compiler import (
    Baseline,
    Continuation,
    MonthlyInput,
    PlanningInputs,
    ReadinessBasis,
    ReceiptTiming,
    compile_input,
)
from nessa.planning.pack import pack_catalogue
from tools.localenv import REPO_ROOT
from tools.option_pack_files import DASH, SECONDS_PER_ROW, show
from tools.option_pack_files import PACKAGE_VERSION as PACK_VERSION

REFERENCE_VERSION = "0.1.0"
REVIEWS = REPO_ROOT / "docs" / "reviews"
CHECKER_PATH = REVIEWS / "session-2-checker-questions.md"
CAPABILITY_PATH = REVIEWS / "session-2-capability-questions.md"
FIXTURES = REPO_ROOT / "fixtures" / "m0"
TRACE = "fixtures/m0/worked_trace.json"
P01_FILE = "fixtures/m0/personas/P01.json"
FIXTURE = Citation(basis=Basis.FIXTURE, locator=TRACE)
P01_TARGET = "data-quality-analyst-manchester"
# No condition in P01's real option set for the delay scenario to move; declared all the same.
DELAY_MONTHS = 2
SECONDS_PER_REFERENCE_ROW = 20  # a rubric row holds five anchors to read
# TRACE-01's synthetic skill rows and the pack rows they name (an agent's mapping, asked in Part A).
TRACE_ROWS = {
    "fixture:query-data": "pack:data-quality-analyst-manchester:independent-querying",
    "fixture:validate-data": "pack:data-quality-analyst-manchester:data-validation",
    "fixture:explain-results": "pack:data-quality-analyst-manchester:communication",
}
SYNTHETIC_PERSON = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
RECORDED = datetime(2027, 1, 1, 9, 0, tzinfo=UTC)
# The agent's proposals for the assessed outcomes; every other outcome's level is ruled out
# by OUT-1 (a topic mention, practice without assessment, an unsupported claim, a credential).
ASSESSED_PROPOSALS: dict[str, tuple[int | None, str]] = {
    "outcome:C06.1": (
        2,
        "the course requires exams ('only exams to be taken in the college'); a pass on this "
        "unit's routine entries reads as anchor 2, not 3. The excerpt names the unit only: "
        "whether the exam covers the anchor, and whether this unit (bookkeeping controls) "
        "belongs to this row or to reconciliation, is the reviewer's check",
    ),
    "outcome:C06.2": (
        2,
        "the same exams; an introductory unit's pass reads as anchor 2 at most. As above, "
        "check the unit belongs to this row",
    ),
    "outcome:C07.1": (
        None,
        "the exam is offered ('the opportunity to achieve'), not required: completing the "
        "course is not an assessed demonstration",
    ),
    "outcome:C07.2": (None, "as C07.1: the exam is optional"),
    "outcome:C10.1": (
        None,
        "the exam is not included in the course: a level needs the exam's pass",
    ),
    "outcome:C10.2": (None, "as C10.1: the exam is bought separately"),
}


def _fixture(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return data


def p01_inputs() -> PlanningInputs:
    """P01's TRACE-01 inputs, unchanged: the person is synthetic, labelled so."""
    trace = _fixture("worked_trace.json")
    p01 = _fixture("personas/P01.json")
    action = trace["catalogue"]["actions"][0]
    horizon = trace["comparison_horizon_months"]
    return PlanningInputs.model_validate(
        {
            "planning_start": trace["planning_start"],
            "horizon_months": horizon,
            "objective_basis": "economic",
            "baseline": Baseline(
                label="staying in the current role",
                net_income_by_month=trace["baseline_income_by_month_minor"],
                cited=FIXTURE,
            ),
            "continuation": Continuation(
                label="returning to the current role at its pay",
                hours_per_week=action["weekly_work_after_completion"],
                net_income_by_month=trace["baseline_income_by_month_minor"],
                cited=FIXTURE,
            ),
            "wage_timing": ReceiptTiming.LATER,
            "opening_cash_minor": trace["opening_cash_minor"],
            "living_outgoings_by_month": trace["living_outgoings_by_month_minor"],
            "reserve_minor": trace["minimum_reserve_minor"],
            "direct_spend_cap_minor": p01["direct_spend_cap_minor"],
            "monthly_payment_cap_minor": p01["monthly_payment_cap_minor"],
            "weekly_availability_by_month": [trace["available_weekly_hours_envelope"]] * horizon,
            "initial_gates": trace["initial_completed_gates"],
            "scenario_delay_months": DELAY_MONTHS,
            "synthetic": True,
        }
    )


def p01_option_set(pack: Pack) -> Catalogue:
    """P01's real options from the pack, with P01's one funding status: C01's route names Free
    Courses for Jobs (read as instrument F01, asked in Part A), and the fixture gives P01 no age or
    gross pay, so the status is insufficient information and nothing is assumed."""
    catalogue = pack_catalogue(pack, P01_TARGET)
    route = pack.claim("C01.funding_route")
    source = next(s for s in pack.sources if s.source_id == route.source_id)
    status = Support(
        instrument_id="funding:F01",
        kind=InstrumentKind.FEE_WAIVER,
        covers_fees_in_full=True,
        paid_to="provider",
        eligibility=EligibilityStatus.INSUFFICIENT_INFORMATION,
        award=AwardState.NOT_APPLIED,
        review_state=RecordState.PROPOSED,
        cited=Citation(
            basis=Basis.SOURCE,
            claim_id=route.claim_id,
            source_id=route.source_id,
            source_hash=source.sha256,
            locator=f"offsets {route.span.start}-{route.span.end}",
            excerpt=route.excerpt,
            retrieved_on=source.retrieved_at.date(),
        ),
    )
    variants = [
        v.model_copy(update={"supports": [status]})
        if v.offering_id.startswith("offering:C01")
        else v
        for v in catalogue.variants
    ]
    return catalogue.model_copy(update={"variants": variants})


def p01_readiness(pack: Pack, reference: Reference) -> ReadinessBasis:
    target = next(t for t in pack.targets if t.target_id == P01_TARGET)
    matrix = build_matrix(
        target.title,
        pack=pack,
        reference=reference,
        pack_target=target,
        occupation=None,
        exemplars=0,
        synthetic=True,
    )
    skills = _fixture("worked_trace.json")["target"]["skills"]
    evidence = []
    for skill in skills:
        row = matrix.row(TRACE_ROWS[skill["skill_id"]])
        if row is None or row.rubric is None:
            raise SystemExit(f"the pack target has no rubric row for {skill['skill_id']}")
        evidence.append(
            SkillEvidence(
                evidence_id=uuid.uuid5(uuid.NAMESPACE_URL, f"nessa:p01:{row.row_id}"),
                subject=row.subject,
                rubric_version=row.rubric.version_id,
                answer=Answer.DONE_INDEPENDENTLY,
                self_assessed_level=skill["current_evidence_level"],
                example="synthetic: P01's TRACE-01 level for this row",
                last_done="2026-09",
                independence="independent",
                recorded_by=SYNTHETIC_PERSON,
                recorded_at=RECORDED,
            )
        )
    offerings = {"offering:C01", "offering:C04"}
    outcomes = [o for o in pack_outcomes(pack, reference) if o.offering_id in offerings]
    return ReadinessBasis(
        matrix=matrix, evidence=evidence, statements=[], outcomes=outcomes, evidence_version=1
    )


@dataclass(frozen=True)
class Run:
    catalogue: Catalogue
    monthly: MonthlyInput
    readiness: ReadinessBasis
    evaluations: list[RouteEvaluation]


def p01_run() -> Run:
    """The TRACE-01 checker on P01's real option set: every variant, every fixed scenario."""
    pack = load_pack(PACK_VERSION)
    reference = load_reference(REFERENCE_VERSION, pack)
    catalogue = p01_option_set(pack)
    readiness = p01_readiness(pack, reference)
    monthly = compile_input(p01_inputs(), catalogue, readiness=readiness)
    evaluations = [evaluate_route(monthly, [v.variant_id]) for v in catalogue.variants]
    return Run(catalogue, monthly, readiness, evaluations)


# Rendering.


def _money(minor: int) -> str:
    return f"£{minor / 100:,.2f}"


def _excerpt(text: str) -> str:
    return " ".join(text.split()).replace("|", "/").replace("`", "'")


def _span(cited: Citation | None) -> str:
    if cited is None or cited.claim_id is None or cited.excerpt is None:
        return "(no span)"
    locator = (cited.locator or "").replace("-", DASH)
    return f"`{_excerpt(cited.excerpt)}` ({cited.claim_id}, {locator})"


def _value(item: Fact) -> str:
    if item.unknown is not None:
        return f"unknown: {item.unknown}"
    return show(item.field, item.value)


def _table(header: list[str], rows: list[list[str]], prefix: str, first: int) -> list[str]:
    lines = [
        "| # | " + " | ".join(header) + " | Right? |",
        "|---" * (len(header) + 2) + "|",
    ]
    for n, row in enumerate(rows, start=first):
        cells = [cell.replace("\n", " ") for cell in row]
        lines.append(f"| {prefix}{n} | " + " | ".join(cells) + " | yes / no |")
    return lines


def _minutes(rows: int, seconds: int) -> int:
    return math.ceil(rows * seconds / 60)


HOW = """\
## How to answer

1. Read the row, and its excerpt where it has one. Each slot's URL is in
   `corpus/manifest.json`.
2. Write **yes** if the row is right as written, **no** with the right reading if it is not,
   and leave it blank if you cannot decide.
3. You may stop at the end of any part. Rows left blank change nothing.
"""


def _input_rows(inputs: PlanningInputs, run: Run) -> list[list[str]]:
    baseline = inputs.baseline.net_income_by_month[0] if inputs.baseline else 0
    label = inputs.baseline.label if inputs.baseline else "none"
    hours = inputs.continuation.hours_per_week
    pay = _money(inputs.continuation.net_income_by_month[0])
    availability = (inputs.weekly_availability_by_month or [0])[0]
    living = _money(inputs.living_outgoings_by_month[0])
    levels = ", ".join(
        f"{TRACE_ROWS[s].rsplit(':', 1)[-1]} {e.self_assessed_level}"
        for s, e in zip(TRACE_ROWS, run.readiness.evidence, strict=True)
    )
    trace, person = f"`{TRACE}`", f"`{P01_FILE}`"
    return [
        [
            "`P01`",
            "start and horizon",
            f"{inputs.planning_start:%Y-%m}, {inputs.horizon_months} months",
            trace,
        ],
        ["`P01`", "baseline", f"{_money(baseline)} a month take-home, {label}", trace],
        [
            "`P01`",
            "continuation",
            f"{hours} hours a week at {pay} a month, {inputs.continuation.label}",
            trace,
        ],
        [
            "`P01`",
            "cash",
            f"opening {_money(inputs.opening_cash_minor)}; living costs {living} a month; "
            f"reserve {_money(inputs.reserve_minor)}",
            trace,
        ],
        [
            "`P01`",
            "limits",
            f"direct-spend cap {_money(inputs.direct_spend_cap_minor or 0)}; monthly payment "
            f"cap {_money(inputs.monthly_payment_cap_minor or 0)}",
            person,
        ],
        ["`P01`", "weekly availability", f"{availability} hours a week in every month", trace],
        [
            "`P01`",
            "when pay arrives",
            "late in the month: it never pays that month's outflows",
            "the fixture validator's assumption (hand check H5)",
        ],
        [
            "`P01`",
            "work while studying",
            f"keeps the current role, {hours} hours a week (`retain_work`, one of P01's "
            "accepted work patterns), because no option states a timetable",
            person,
        ],
        [
            "`P01`",
            "evidence on the pack rows",
            f"TRACE-01's levels carried to the rows they name: {levels} (an agent's mapping; "
            "synthetic)",
            trace,
        ],
        [
            "`P01`",
            "funding status for C01",
            "insufficient information: the fixture gives P01 no age and no gross pay, so the "
            "fee waiver is not counted. C01's route is read as instrument F01 (Free courses "
            "for jobs)",
            _span(_status(run).cited),
        ],
    ]


def _status(run: Run) -> Support:
    return next(s for v in run.catalogue.variants for s in v.supports)


_READINGS = {
    "intake": "no month on the grid: every check that needs a date is unresolved",
    "schedule": "no weekly load: the 40-hour envelope is unresolved",
    "instalment": "no plan by instalments",
    "fee_total": "the cost is unknown, never £0",
}


def _reading(item: Fact) -> str:
    """What the checker does with a field, in words."""
    if item.field == "fee_total" and item.value is not None:
        fee = show("fee_total", item.value)
        return f"paid in full: one payment of {fee} in the first month (no schedule is stated)"
    if item.field == "instalment" and item.value is not None:
        return "monthly payments of at least that amount, their number not stated: no total"
    if item.field == "duration":
        if isinstance(item.value, list) and any(
            p.get("typical") for p in item.value if isinstance(p, dict)
        ):
            return "no finish date: a typical duration is never a bound"
        return "a finish that many weeks after a start, once a start is known"
    if item.field == "funding" and item.value is not None:
        return "no support: the learner pays"
    if item.field.startswith(("funding_route", "eligibility")):
        return (
            "a condition for the provider to confirm: P01's status is insufficient "
            "information, so nothing is counted"
        )
    if item.unknown is not None:
        return _READINGS.get(item.field, "unknown, never 0")
    return "as stated"


ASKED = ("intake", "duration", "schedule", "fee_total", "instalment")


def _option_rows(run: Run) -> list[list[str]]:
    rows: list[list[str]] = []
    seen: set[str] = set()
    for offering in run.catalogue.offerings:
        record = offering.outcomes_from or offering.offering_id
        for item in offering.facts:
            shared = item.field != "duration"
            key = f"{record}:{item.field}:{item.cited.claim_id if item.cited else ''}"
            if item.field not in ASKED and not item.field.startswith(("funding", "eligibility")):
                continue
            if shared and key in seen:
                continue
            seen.add(key)
            name = f"`{record}`" if shared else f"`{offering.offering_id}`"
            rows.append(
                [
                    name,
                    item.field,
                    _value(item),
                    _reading(item),
                    _span(item.cited),
                ]
            )
    return rows


def _verdict(check: RouteCheck) -> str:
    words = {
        Verdict.NOT_FEASIBLE_IN_MODEL: (
            "not feasible in this monthly model (a conservative rejection, never 'cannot afford')"
        ),
        Verdict.UNRESOLVED: "unresolved: unknowns block a decision",
    }
    return words.get(check.verdict, check.verdict.value)


def _findings(check: RouteCheck) -> str:
    parts = []
    for finding in check.findings:
        if finding.kind is FindingKind.VIOLATION and finding.amount is not None:
            amount, limit = _money(finding.amount), _money(finding.limit or 0)
            parts.append(f"{finding.code.value}: {amount} above {limit}")
        else:
            parts.append(finding.code.value)
    return "; ".join(dict.fromkeys(parts))


def _result_rows(run: Run) -> list[list[str]]:
    rows = []
    plans = {o.offering_id: o for o in run.catalogue.offerings}
    for evaluation in run.evaluations:
        check = evaluation.scenario(Scenario.BASE)
        variant = run.monthly.variant(check.route[0])
        offering = plans[variant.offering_id]
        fee = next((f for f in offering.facts if f.field == "fee_total"), None)
        state = check.readiness_state.value if check.readiness_state else "not assessed"
        readiness = (
            f"readiness not reached in this model ({state}): a partial sketch, since no pack "
            "outcome has a level"
            if check.months_to_readiness is None
            else f"ready after {check.months_to_readiness} months"
        )
        rows.append(
            [
                f"`{variant.variant_id}`",
                "result",
                _verdict(check),
                f"{_findings(check)}; {readiness}",
                _span(fee.cited if fee else None),
            ]
        )
    for outcome in run.readiness.outcomes:
        claim = outcome.source_span
        cited = Citation(
            basis=Basis.SOURCE,
            claim_id=claim.claim_id,
            excerpt=claim.excerpt,
            locator=f"offsets {claim.start}-{claim.end}",
        )
        reading = (
            f"{outcome.evidence_kind.value}, {outcome.confidence.value}, no level, proposed: "
            "counts for nothing towards readiness"
        )
        rows.append(
            [
                f"`{outcome.outcome_id}`",
                f"outcome for `{outcome.skill_id.rsplit(':', 1)[-1]}`",
                "no level (pack 0.1.0)",
                reading,
                _span(cited),
            ]
        )
    return rows


def checker_questions() -> str:
    run = p01_run()
    inputs = run.monthly.inputs
    parts = [
        (
            "Part A: what the checker read about P01, a synthetic person",
            ["Record", "Field", "As read", "Source"],
            _input_rows(inputs, run),
        ),
        (
            "Part B: what the checker read about P01's real options",
            ["Record", "Field", "Value on the page", "The checker reads", "Span (claim, location)"],
            _option_rows(run),
        ),
        (
            "Part C: what the checker concluded, in the base scenario",
            ["Record", "Field", "Result", "Findings", "Resting on"],
            _result_rows(run),
        ),
    ]
    total = sum(len(rows) for _, _, rows in parts)
    minutes = _minutes(total, SECONDS_PER_ROW)
    lines = [
        "# Session 2 package: the TRACE-01 checker on P01's real option set (H-07, TEST1-14)",
        "",
        "Generated by `tools.session_2_files` (from `backend/`: `uv run --locked python -m",
        "tools.session_2_files`). Do not edit it by hand: a fast test checks it against the tool's",
        "output, so the T numbers are stable. They are this set's own: Q1-Q344 are unchanged.",
        "",
        "- **Status:** agent preparation (Task 11). The review is not run - requires human",
        "  (H-07, ruling R2). Nothing in this file is an answer.",
        f"- **What:** {total} yes/no questions, T1{DASH}T{total}, about {minutes} minutes. The",
        "  same checker that reproduces TRACE-01 exactly, run on P01's real option set: the",
        f"  courses the England option pack {PACK_VERSION} gives P01's target",
        f"  (`{P01_TARGET}`), every record `proposed`.",
        "- **The person is synthetic:** P01's money, hours and evidence are the M0 fixture's",
        "  (TRACE-01). Only the options are real.",
        "- **Readiness is a partial sketch:** every planned outcome in pack 0.1.0 has no level, so",
        "  no pack option counts towards readiness until Task 7c publishes reviewed levels. Every",
        "  result below says so.",
        f"- **Scenarios:** base, delay ({DELAY_MONTHS} months), no award and no offer. This set",
        "  has no offer and no assumed award, so all four read the same; Part C shows the base",
        "  one.",
        "",
        HOW,
    ]
    first = 1
    for title, header, rows in parts:
        last = first + len(rows) - 1
        lines += [f"## {title} (T{first}{DASH}T{last})", "", *_table(header, rows, "T", first), ""]
        first = last + 1
    return "\n".join(lines).rstrip("\n") + "\n"


# The capability reference and the proposed outcome levels.


def proposed_levels(pack: Pack, reference: Reference) -> dict[str, tuple[int | None, str]]:
    """A proposed level for every planned outcome in the pack, with its reason: a number only
    where OUT-1 allows one (an assessed kind, a supported claim, a skill row with a rubric)."""
    skills = {s.skill_id: s.kind for s in pack.skills}
    found: dict[str, tuple[int | None, str]] = {}
    for outcome in pack.outcomes:
        if skills[outcome.skill_id] != "skill":
            found[outcome.record_id] = (
                None,
                "a credential outcome is eligibility to apply, never a level",
            )
        elif outcome.evidence_kind == "topic_mention":
            found[outcome.record_id] = (None, "a topic mention never gives a level")
        elif outcome.evidence_kind == "practice":
            found[outcome.record_id] = (None, "practice without an assessment gives no level")
        elif outcome.confidence == "unsupported":
            found[outcome.record_id] = (None, "an unsupported claim gives no level")
        elif reference.rubric_for(outcome.skill_id) is None:
            found[outcome.record_id] = (None, "no rubric models the row")
        else:
            found[outcome.record_id] = ASSESSED_PROPOSALS[outcome.record_id]
    return found


def _reference_rows(reference: Reference) -> list[tuple[str, list[list[str]]]]:
    targets = [
        [
            f"`{t.target_id}`",
            "ESCO occupation",
            f"{t.esco_label} ({t.esco_occupation})",
            t.note or "",
        ]
        for t in reference.targets
    ]
    rubrics = []
    for rubric in reference.rubrics:
        name = f"`{rubric.version_id}`"
        anchors = "; ".join(f"{level} {text}" for level, text in sorted(rubric.anchors.items()))
        rubrics += [
            [name, "observable task", rubric.observable_task, ""],
            [
                name,
                "required level",
                f"{rubric.required_level}: {rubric.anchors[rubric.required_level]}",
                "proposed for the entry-level postings",
            ],
            [name, "anchors 0-4", anchors, "levels are ordered, never added"],
            [name, "ESCO skill", f"{rubric.esco_label} ({rubric.esco_skill})", rubric.note or ""],
        ]
    gates = []
    for gate in reference.gates:
        gates += [
            [
                f"`{gate.gate_key}`",
                "gate type",
                f"{gate.label}: {gate.kind.value}, issued by {gate.issuing_body} "
                f"({gate.jurisdiction})",
                "protected: never demoted by a preference",
            ],
            [
                f"`{gate.gate_key}`",
                "verification",
                f"{gate.verification}; proof: {'; '.join(gate.acceptable_proof)}",
                "held but unverified stays unresolved",
            ],
        ]
    return [
        ("Targets' ESCO occupations", targets),
        ("Rubrics and required levels", rubrics),
        ("Protected gates", gates),
    ]


def _level_rows(pack: Pack, reference: Reference) -> list[list[str]]:
    proposals = proposed_levels(pack, reference)
    claims = {c.claim_id: c for c in pack.claims}
    rows = []
    for outcome in pack.outcomes:
        level, why = proposals[outcome.record_id]
        claim = claims[outcome.source_span]
        rubric = reference.rubric_for(outcome.skill_id)
        cited = Citation(
            basis=Basis.SOURCE,
            claim_id=claim.claim_id,
            excerpt=claim.excerpt,
            locator=f"offsets {claim.span.start}-{claim.span.end}",
        )
        rows.append(
            [
                f"`{outcome.record_id}`",
                f"`{rubric.version_id}`" if rubric else f"`{outcome.skill_id}` (no rubric)",
                f"{outcome.evidence_kind}, {outcome.confidence}",
                "none" if level is None else str(level),
                why,
                _span(cited),
            ]
        )
    return rows


def capability_questions() -> str:
    pack = load_pack(PACK_VERSION)
    reference = load_reference(REFERENCE_VERSION, pack)
    sections = _reference_rows(reference)
    levels = _level_rows(pack, reference)
    reference_rows = sum(len(rows) for _, rows in sections)
    total = reference_rows + len(levels)
    minutes = _minutes(reference_rows, SECONDS_PER_REFERENCE_ROW) + _minutes(
        len(levels), SECONDS_PER_ROW
    )
    version = reference.reference_version
    lines = [
        f"# Session 2 package: the capability reference {version} and proposed outcome levels "
        "(H-07)",
        "",
        "Generated by `tools.session_2_files` (from `backend/`: `uv run --locked python -m",
        "tools.session_2_files`). Do not edit it by hand: a fast test checks it against the tool's",
        "output, so the R numbers are stable. They are this set's own: Q1-Q344 are unchanged.",
        "",
        "- **Status:** agent preparation (Task 11). The review is not run - requires human",
        "  (H-07, ruling R2). Nothing in this file is an answer.",
        f"- **What:** {total} yes/no questions, R1{DASH}R{total}, about {minutes} minutes: the",
        f"  reference an agent wrote in Task 9 (`capability-reference-{version}.json`,",
        f"  `{reference.review_state}`), then a proposed level for each of the {len(levels)}",
        f"  planned outcomes in pack {pack.pack_version}.",
        "- **The levels are proposals in this package only.** Pack 0.1.0 is frozen with every",
        "  level null. Task 7c publishes the levels you accept in the next pack version; a level",
        "  you reject stays null.",
        "- **The rule a level follows (OUT-1):** a number only for an assessed kind (an exam or an",
        "  assessed work sample) whose claim is supported, on a skill row with a rubric. A topic",
        "  mention, practice without assessment, an unsupported claim and a credential outcome",
        "  have none.",
        "",
        HOW,
    ]
    n = 1
    lines += ["## Part A: the capability reference", ""]
    for title, rows in sections:
        lines += [
            f"### {title}",
            "",
            *_table(["Record", "Field", "As written", "Note"], rows, "R", n),
            "",
        ]
        n += len(rows)
    header = [
        "Outcome",
        "Row (rubric)",
        "Evidence kind, confidence",
        "Proposed level",
        "Why",
        "Span (claim, location)",
    ]
    lines += [
        f"## Part B: proposed outcome levels (R{n}{DASH}R{n + len(levels) - 1})",
        "",
        *_table(header, levels, "R", n),
        "",
    ]
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> None:
    CHECKER_PATH.write_text(checker_questions(), encoding="utf-8")
    CAPABILITY_PATH.write_text(capability_questions(), encoding="utf-8")
    print(f"wrote {CHECKER_PATH}\nwrote {CAPABILITY_PATH}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
