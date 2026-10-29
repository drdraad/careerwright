"""The England option pack's files that are derived, never edited by hand (ADR 0011):

- a version's file, in the format's canonical text (`--pack FILE`: a pack as JSON, parsed
  strictly and checked, then written; pin the printed SHA-256 in `option_pack.PINS`);
- the format's JSON Schema, with its value shapes, beside the packs;
- the session 2 package: yes/no questions for the H-07 reviewer, every consequential field
  of every record beside its span, in the order of the gates the session closes. Its
  question numbers are stable: Task 7c applies the answers by number.

Fast tests check the committed schema and package against this tool's output. Run from
`backend/`: `uv run --locked python -m tools.option_pack_files [--pack FILE]`.
"""

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from nessa.catalogue.option_pack import (
    CLAIM_FIELD_SHAPES,
    PACKS_DIR,
    SCHEMA_PATH,
    Claim,
    FundingInstrument,
    JobPosting,
    LearningOption,
    Offering,
    OptionPackError,
    Pack,
    Ref,
    Target,
    Unknown,
    check_pack,
    dump_pack,
    load_pack,
    parse_pack,
    schema,
)
from tools.localenv import REPO_ROOT

PACKAGE_VERSION = "0.1.0"  # the version session 2 reviews
PACKAGE_PATH = REPO_ROOT / "docs" / "reviews" / "session-2-option-pack-questions.md"
SECONDS_PER_ROW = 15
TRACE_PERSONA = "P01"  # TRACE-01's real option set (plan section 10)

# Facts asked beside their spans: every one whose value is money, pay, a date, a duration
# or a schedule, and these, which change a route or a reading of one. Identity facts
# (source IDs, codes, posting dates) and descriptions are not asked.
ASKED_SHAPES = frozenset(
    {"money", "rate", "pay", "instalment", "date", "dates", "deadline", "duration", "schedule"}
)
ASKED_FIELDS = frozenset(
    {
        *("location", "location_conflict", "occupation_crosswalk", "work_locations"),
        *("duplicate_of", "early_close", "salary_shown", "salary_basis_note", "guided_hours"),
        *("description_inconsistency", "offer_kind", "stated_purpose", "provider_outcome_claim"),
        *("pass_rule", "practice_assessment", "conditions", "standard"),
        *("award_status", "cost_to_learner", "rules_version_note", "eligible_subject_digital"),
        *("eligible_subject_accounting", "universal_credit_interaction", "outcome_offer"),
        "digital_subjects",
    }
)
NOT_ASKED = frozenset(
    {"source_job_id", "apply_url", "course_code", "ucas_code", "date_posted", "instrument_kind"}
    # F01's loan sentence is asked once, as F02's repayment.
    | {"alternative_if_ineligible"}
)
GATE_KINDS = frozenset({"credential", "eligibility"})
DASH = chr(0x2013)  # an en dash, for ranges
RSQUO = chr(0x2019)  # a right single quotation mark


@dataclass(frozen=True)
class Row:
    record_id: str
    field: str
    value: str
    span: str


PENCE = 100  # GBP's minor units a pound


def pounds(minor: int) -> str:
    """GBP minor units as pounds and pence, with whole numbers only (Global Constraint 4)."""
    sign = "-" if minor < 0 else ""
    whole, pence = divmod(abs(minor), PENCE)
    return f"{sign}£{whole:,}.{pence:02d}"


def show(field: str, value: object) -> str:
    """A value as the reviewer reads it: money in pounds and pence, durations in words."""
    if value is None:
        return "unknown (null)"
    shape = CLAIM_FIELD_SHAPES.get(field, "text")
    if isinstance(value, dict) and shape == "money":
        return pounds(value["minor_units"])
    if isinstance(value, dict) and shape == "rate":
        bound = "at least " if value["at_least"] else ""
        repayable = {True: ", repayable", False: ", not repayable"}.get(value["repayable"], "")
        return f"{bound}{pounds(value['minor_units'])} per {value['period']}{repayable}"
    if isinstance(value, dict) and shape == "pay":
        return _pay(value)
    if isinstance(value, dict) and shape == "instalment":
        return _instalment(value)
    if isinstance(value, list) and shape == "duration":
        return "; ".join(_duration(part) for part in value)
    if isinstance(value, dict) and shape == "place":
        label = str(value["label"])
        more = [f"{k.replace('_', ' ')} {v}" for k, v in value.items() if k != "label" and v]
        return f"{label} ({'; '.join(more)})" if more else label
    if isinstance(value, dict) and shape == "schedule":
        parts = [(value["pattern"] or "").replace("_", " ")]
        if value["hours_per_week"]:
            parts.append(f"{value['hours_per_week']} hours a week")
        return ", ".join(p for p in parts if p)
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _pay(value: dict[str, object]) -> str:
    low, high = value["minimum_minor_units"], value["maximum_minor_units"]
    if isinstance(low, int) and isinstance(high, int):
        amount = pounds(low) if low == high else f"{pounds(low)}{DASH}{pounds(high)}"
    elif isinstance(high, int):
        amount = f"up to {pounds(high)}"
    else:
        amount = f"from {pounds(low)}" if isinstance(low, int) else "?"
    period = f"per {value['period']}" if value["period"] else "per unstated period"
    return f"{amount} {period}, {value['basis']}"


def _instalment(value: dict[str, object]) -> str:
    parts = []
    minor, period, count = value["minor_units"], value["period"], value["count"]
    if isinstance(minor, int):
        bound = "from " if value["at_least"] else ""
        parts.append(f"{bound}{pounds(minor)}" + (f" per {period}" if period else ""))
    if count:
        parts.append(f"{count} payments")
    if not isinstance(minor, int):
        parts.append("amount not stated")
    return ", ".join(parts)


def _duration(part: dict[str, object]) -> str:
    low, high, unit = part["minimum"], part["maximum"], part["unit"]
    if part["unbounded"]:
        length = f"at least {low} {unit}, no end" if low is not None else "no end (lifetime)"
    elif low == high:
        length = f"{low} {unit}"
    elif low is None:
        length = f"up to {high} {unit}"
    elif high is None:
        length = f"at least {low} {unit}"
    else:
        length = f"{low}{DASH}{high} {unit}"
    if part["typical"]:
        length = f"typically {length}"
    mode = part["mode"]
    return f"{length} ({str(mode).replace('_', ' ')})" if mode else length


def _cited(claim: Claim) -> str:
    span = claim.span
    where = (
        f"offsets {span.start}{DASH}{span.end}"
        if span.pointer is None
        else f"pointer {span.pointer}"
    )
    excerpt = " ".join(claim.excerpt.split()).replace("|", "/")
    if "`" in excerpt:
        raise OptionPackError(f"{claim.claim_id}'s excerpt holds a backtick")
    return f"`{excerpt}` ({claim.claim_id}, {where})"


class _Rows:
    """The rows of one part, in pack order, each asked once."""

    def __init__(self, pack: Pack) -> None:
        self._pack = pack
        self._claims = {c.claim_id: c for c in pack.claims}
        self.rows: list[Row] = []

    def ask(self, record_id: str, field: str, ref: Ref, shown: str | None = None) -> None:
        if isinstance(ref, Unknown):
            self.rows.append(Row(record_id, field, f"unknown: {ref.unknown}", "(no span)"))
            return
        claim = self._claims[ref]
        value = shown or show(claim.field, claim.value)
        self.rows.append(Row(record_id, field, value, _cited(claim)))

    def facts(self, record_id: str, facts: list[str]) -> None:
        for claim_id in facts:
            claim = self._claims[claim_id]
            if claim.field in NOT_ASKED:
                continue
            if CLAIM_FIELD_SHAPES.get(claim.field) in ASKED_SHAPES or claim.field in ASKED_FIELDS:
                self.ask(record_id, f"fact: {claim.field}", claim_id)

    def job(self, job: JobPosting) -> None:
        for name in ("salary", "valid_through", "location", "status", "advertiser", "employer"):
            ref = getattr(job, name)
            if isinstance(ref, str) or name in ("salary", "valid_through", "location"):
                self.ask(job.record_id, name, ref)
        self.facts(job.record_id, job.facts)
        for req in (r for r in self._pack.skill_requirements if r.job_posting_id == job.record_id):
            essential_gate = req.importance == "essential" and req.kind in GATE_KINDS
            if not (req.gate or req.skill_id or essential_gate):
                continue
            words: list[str] = [req.importance, req.kind]
            words += [f"gate: {req.gate}"] if req.gate else ["no gate"] if essential_gate else []
            words += [f"row {req.skill_id.split(':')[-1]}"] if req.skill_id else []
            self.ask(req.record_id, f"requirement ({', '.join(words)})", req.text)

    def option(self, option: LearningOption) -> None:
        offering = next(o for o in self._pack.offerings if o.option_id == option.record_id)
        for name in ("credential", "recognising_body", "level", "assessment"):
            ref = getattr(option, name)
            if isinstance(ref, str):
                self.ask(option.record_id, name, ref)
        for claim_id in option.entry_requirements:
            self.ask(option.record_id, "entry requirement", claim_id)
        self.facts(option.record_id, option.facts)
        self.offering(offering)

    def offering(self, offering: Offering) -> None:
        names = ("fee_total", "instalment", "intake", "application_deadline", "duration")
        for name in (*names, "schedule", "wage"):
            self.ask(offering.record_id, name, getattr(offering, name))
        for claim_id in (*offering.extra_costs, *offering.funding_conditions):
            self.ask(offering.record_id, self._claims[claim_id].field, claim_id)
        for outcome in (u for u in self._pack.outcomes if u.offering_id == offering.record_id):
            level = outcome.level_on_completion
            level_text = "no level (no rubric yet)" if level is None else f"level {level}"
            shown = f"{outcome.evidence_kind}, {level_text}, {outcome.confidence}"
            skill = outcome.skill_id.split(":")[-1]
            self.ask(outcome.record_id, f"outcome for `{skill}`", outcome.source_span, shown)

    def funding(self, fund: FundingInstrument) -> None:
        kinds = [f for f in fund.facts if self._claims[f].field == "instrument_kind"]
        shown = f"{fund.instrument_kind}, award state {fund.award_state}"
        if kinds:
            self.ask(fund.record_id, "instrument kind and award state", kinds[0], shown)
        else:
            self.rows.append(
                Row(fund.record_id, "instrument kind and award state", shown, "(no claim)")
            )
        for name in ("eligible_costs", "published_on", "rules_updated_on", "timing", "repayment"):
            self.ask(fund.record_id, name, getattr(fund, name))
        for claim_id in fund.rules:
            self.ask(fund.record_id, self._claims[claim_id].field, claim_id)
        self.facts(fund.record_id, fund.facts)


@dataclass(frozen=True)
class Part:
    title: str
    closes: str
    sections: list[tuple[str, list[Row]]]

    @property
    def count(self) -> int:
        return sum(len(rows) for _, rows in self.sections)


def _heading(target: Target) -> str:
    return f"{target.persona}: {target.title}, {target.city} (`{target.target_id}`)"


def _jobs(pack: Pack, target: Target) -> list[Row]:
    rows = _Rows(pack)
    for job in (j for j in pack.job_postings if j.target_id == target.target_id):
        rows.job(job)
    return rows.rows


def _options(pack: Pack, target: Target) -> list[Row]:
    rows = _Rows(pack)
    for option in (o for o in pack.learning_options if target.target_id in o.target_ids):
        rows.option(option)
    return rows.rows


def parts(pack: Pack) -> list[Part]:
    """The package's parts, in the order of the gates they close (ADR 0011 decision 14)."""
    trace = [t for t in pack.targets if t.persona == TRACE_PERSONA]
    others = [t for t in pack.targets if t.persona != TRACE_PERSONA]
    funding = _Rows(pack)
    for fund in pack.funding_instruments:
        funding.funding(fund)
    return [
        Part(
            f"Part 1: {TRACE_PERSONA}, every row",
            "the TRACE-01 review of P01's real option set",
            [(_heading(t), _jobs(pack, t) + _options(pack, t)) for t in trace],
        ),
        Part(
            f"Part 2: P03{DASH}P05's courses, then the funding",
            f"H-07 for Sprints 4{DASH}5 (the options, offerings, outcomes and funding)",
            [(_heading(t), _options(pack, t)) for t in others]
            + [("Funding (P01, P03, P05)", funding.rows)],
        ),
        Part(
            f"Part 3: P03{DASH}P05's job postings and requirements",
            "the job labels; Task 8 may take any rows left over",
            [(_heading(t), _jobs(pack, t)) for t in others],
        ),
    ]


def _minutes(rows: int) -> int:
    return math.ceil(rows * SECONDS_PER_ROW / 60)


def _numbered(all_parts: list[Part]) -> Iterator[tuple[Part, int, int]]:
    first = 1
    for part in all_parts:
        yield part, first, first + part.count - 1
        first += part.count


HOW = """\
## How to answer

1. Read the row's excerpt. Open the page if you need its context: each slot's URL is in
   `corpus/manifest.json`.
2. Write **yes** if the page states the value as shown, with its unit, period and basis. For
   an "unknown" row, yes means the page does not state it.
3. Write **no** otherwise, with the right reading and where it is on the page.
4. Leave a row blank if you cannot decide.

## What Task 7c does with the answers

- **A record becomes `review_state: reviewed`**, with reviewer and date, only when every one
  of its rows is answered yes. Each record's rows are all in one part.
- **Otherwise it stays `proposed`.** A blank row leaves it undecided, and a "no" records the
  correction, with its span, for a later version.
- **The decisions are published as a new dated pack version.** Version {version} is not
  changed.

## Reading the rows

- **Money** is shown in pounds and pence. "up to" and "from" mark a bound the page states.
  "advertised" or "predicted" is the pay basis. "per unstated period" means the source gives
  no period (Adzuna's figures).
- **Durations** say how the course is taken (full time, part time, self-paced) where the
  excerpt does. "typically" marks what is typical (an average), never a bound. "no end"
  is a length the page states as having none (lifetime access), not an unknown.
- **Rates** say "not repayable" or "repayable" only where the page says so.
- **Excerpts** are shown as code, exactly as in the hashed text, with runs of whitespace
  collapsed. So HTML appears as written: `&#163;`, `&pound;` and `&#xA3;` are £, and
  `&#8217;` is {rsquo}. Adzuna excerpts are the API's JSON, cut at 120 characters.
- **Offsets** index the page's text after redaction (third parties' contact details are
  removed before hashing). A pointer is a JSON pointer into the Adzuna response.
- **The live page may have changed** since {dated}. Answer from the excerpt, and note any
  difference you see.
- **Outcome rows** give the evidence kind (topic_mention, practice, exam or
  assessed_work_sample), then the level, then the confidence. No rubric exists yet, so no
  outcome has a level (Task 9 adds them).
- **"fact:" rows** are further span-cited facts a record keeps beside its fields, such as the
  second of two statements that disagree.
- **Requirement rows** are asked when the requirement is mapped to a target's skill row,
  carries a gate, or is an essential credential or eligibility requirement ("no gate" asks
  whether that is right).
- **Not asked:** titles, posting dates and source IDs. Rights are a separate human gate
  (OI-07); C08 is pending rights review.
"""

TABLE = [
    "| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |",
    "|---|---|---|---|---|---|",
]
PACK_FILE = (
    "backend/src/nessa/catalogue/packs/england_option_pack/england-option-pack-{version}.json"
)


def review_package(pack: Pack) -> str:
    """The session 2 package for a pack, as Markdown: the same text for the same pack."""
    all_parts = parts(pack)
    total = sum(p.count for p in all_parts)
    lines = [
        f"# Session 2 package: the England option pack {pack.pack_version} (H-07)",
        "",
        "Generated from the pinned pack by `tools.option_pack_files` (from `backend/`: `uv run",
        "--locked python -m tools.option_pack_files`). Do not edit it by hand: a fast test checks",
        "it against the tool's output, so its question numbers are stable for Task 7c.",
        "",
        "- **Status:** agent preparation (Task 7b). The review is not run - requires human",
        "  (H-07, ruling R2). Nothing in this file is an answer.",
        "- **For:** the H-07 domain reviewer at session 2. Task 7c applies the answers by",
        "  question number.",
        f"- **What:** {total} yes/no questions. They cover every consequential field of every",
        "  record in",
        f"  `{PACK_FILE.format(version=pack.pack_version)}`,",
        "  each beside the span it cites. Consequential means pay and its basis, money, dates and",
        "  deadlines, durations and schedules, entry requirements and gates, eligibility rules,",
        "  award status, outcome levels and the conflicts a page leaves open. P02 has no target in",
        "  the fixture, so it has no records.",
        "",
        "## The three parts",
        "",
        "Answer the parts in order, and stop at the end of any part. Each part closes its gate on",
        "its own; a part left unanswered leaves its records `proposed`.",
        "",
        "| Part | Questions | Rows | About | Closes |",
        "|---|---|---|---|---|",
    ]
    for part, first, last in _numbered(all_parts):
        lines.append(
            f"| {part.title} | Q{first}{DASH}Q{last} | {part.count} "
            f"| {_minutes(part.count)} min | {part.closes} |"
        )
    lines += [
        "",
        f"In all: {total} rows, about {_minutes(total)} minutes at {SECONDS_PER_ROW} seconds "
        "a row.",
        "",
        HOW.format(version=pack.pack_version, dated=pack.dated.isoformat(), rsquo=RSQUO),
    ]
    n = 0
    for part, first, last in _numbered(all_parts):
        span = f"Q{first}{DASH}Q{last}, about {_minutes(part.count)} minutes"
        lines += [f"## {part.title} ({span})", "", f"Closes {part.closes}.", ""]
        for heading, rows in part.sections:
            lines += [f"### {heading}", "", *TABLE]
            for row in rows:
                n += 1
                cells = [f"Q{n}", f"`{row.record_id}`", row.field, row.value, row.span]
                lines.append(f"| {' | '.join(cells)} | yes / no |")
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def schema_text() -> str:
    return json.dumps(schema(), indent=2, ensure_ascii=False) + "\n"


def publish(source: Path, packs_dir: Path = PACKS_DIR) -> tuple[Path, str]:
    """A pack file, parsed strictly and checked, written as its version's canonical text.
    Returns the file and the SHA-256 to pin; a pack with any problem is refused."""
    pack = parse_pack(json.loads(source.read_text(encoding="utf-8")))
    problems = check_pack(pack)
    if problems:
        raise SystemExit("refused: " + "; ".join(problems))
    text = dump_pack(pack)
    target = packs_dir / f"england-option-pack-{pack.pack_version}.json"
    target.write_text(text, encoding="utf-8")
    return target, hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, help="publish this pack file as its version")
    args = parser.parse_args(argv)
    if args.pack:
        path, digest = publish(args.pack)
        print(f"wrote {path}\npin it in option_pack.PINS: {digest}")
        return
    SCHEMA_PATH.write_text(schema_text(), encoding="utf-8")
    PACKAGE_PATH.write_text(review_package(load_pack(PACKAGE_VERSION)), encoding="utf-8")
    print(f"wrote {SCHEMA_PATH}\nwrote {PACKAGE_PATH}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
