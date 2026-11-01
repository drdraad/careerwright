"""The England option pack 0.3.0: version 0.2.0 with the school-leaver pages (Task 7f, plan
v1.6; ADR 0011), every new or changed record `proposed` for the school-leaver pack session.

- **The pages and their labels** are `tools/school_leaver_labels.json`: each page as the
  controller's fetch recorded it (through the guarded fetcher, `tools.corpus --batch`, via the
  session's HTTPS proxy), and each claim with its span in the kept body (the first occurrence
  and the exact count). The bodies stay in the gitignored `var/evidence/corpus/`.
- **New records:** the Tuition Fee Loan and the Maintenance Loan for courses starting before
  1 January 2027, and the same two loans through the Lifelong Learning Entitlement for courses
  starting on or after it (each with its payment, repayment, age and residency rules); the
  16 to 19 Bursary Fund; the government's funding of apprenticeship training; and a T Level
  (an option and its offering). Every one `proposed`, dated by its pages' retrieval.
- **One changed record:** the Advanced Learner Loan (`funding:F02`) gains how it is paid and
  repaid, its repayment plan and what it covers, from three more pages. Its session 2 review
  stays as it was given; it was and stays `proposed`.
- **Unchanged:** every other record, and versions 0.1.0 and 0.2.0 with their pins.
- **Not in it** (no value is guessed): the apprentice's training fee (the funding page names
  the government and the employer as payers, not what the apprentice pays) and the nursing
  degree's UCAS deadline (the UCAS page's located excerpts name the date's heading, not the
  date). Both fields keep their 0.2.0 unknowns.

It also writes the school-leaver pack session's package (`docs/reviews/`): every row of the
new and changed records beside its span, the ones that change a route first.

Run from `backend/`: `uv run --locked python -m tools.school_leaver_pack --out FILE`, then
publish FILE with `uv run --locked python -m tools.option_pack_files --pack FILE` and pin the
SHA-256 it prints; `--package` writes the package. Fast tests check both committed files are
exactly this tool's output.
"""

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from careerwright.catalogue.option_pack import (
    CLAIM_FIELD_SHAPES,
    Claim,
    OptionPackError,
    Pack,
    Ref,
    check_pack,
    dump_pack,
    load_pack,
    parse_pack,
)
from tools.localenv import REPO_ROOT
from tools.option_pack_files import DASH, TABLE, Row, _Rows

SOURCE_VERSION = "0.2.0"  # the reviewed version this one adds to
VERSION = "0.3.0"
DATED = date(2026, 11, 1)
AS_OF = "2026-11-01"  # the pages' retrieval date
LABELS = Path(__file__).with_name("school_leaver_labels.json")
PACKAGE_PATH = REPO_ROOT / "docs" / "reviews" / "school-leaver-pack-questions.md"
SECONDS_PER_ROW = 15
LABEL_REVIEW = (
    "0.2.0's records keep session 2's review (H-07, 2026-10-29 to 2026-10-30); the records "
    "new or changed in 0.3.0 are not run - requires human (the school-leaver pack session, H-07)"
)
NOTES = [
    "Version 0.3.0 adds the school-leaver pages (Task 7f, plan v1.6) to version 0.2.0: ten "
    "GOV.UK pages on student finance, its repayment plans, the Advanced Learner Loan, the 16 to "
    "19 Bursary Fund and apprenticeship training funding (F04-F13) and the Department for "
    "Education's introduction of T Levels (C11), retrieved on 2026-11-01. Its seven new "
    "records and one changed record (funding:F02) are proposed for the school-leaver pack "
    "session; versions 0.1.0 and 0.2.0 are unchanged.",
    "The 2026-11-01 pages were fetched by the controller through the guarded fetcher via the "
    "session's HTTPS proxy: every check ran except the address check, which the proxy makes "
    "(each record: via_proxy true, address_checked false; corpus/manifest.json).",
    "Which student loans apply depends on the course's start: funding:F05 and "
    "funding:F05.maintenance hold the caps for courses starting before 1 January 2027 (the 2025 "
    "to 2026 and 2026 to 2027 academic years); funding:F12 and funding:F12.maintenance hold the "
    "Lifelong Learning Entitlement's for courses starting on or after it, 'most undergraduate' "
    "courses among them. A course starting in September 2027, such as offering:C08, falls in "
    "the second, if it is one of those courses: the page does not name courses. A cap is never "
    "what a student gets.",
    "Not in 0.3.0, so no value is guessed: the apprentice's training fee (offering:C09) stays "
    "unknown, since the funding page (F04) names the government and the employer as payers "
    "but not what the apprentice pays; the nursing degree's UCAS deadline (offering:C08) stays "
    "unknown, since the UCAS page's located excerpts (C12, class other, not in this pack) name "
    "the equal consideration date's heading but not the date.",
]
NEW_FUNDING: list[dict[str, Any]] = [
    {
        "record_id": "funding:F05",
        "source_ids": ["F05", "F06", "F07", "F13"],
        "programme": "F05.programme.tuition",
        "instrument_kind": "loan",
        "eligible_costs": "F05.eligible_costs.tuition",
        "rules": [
            "F06.rule_age_limit.tuition",
            "F06.rule_residency.status",
            "F06.rule_residency.home",
            "F06.rule_residency.three_years",
            "F06.rule_course",
            "F06.rule_previous_study",
        ],
        "timing": "F05.timing.tuition",
        "repayment": "F07.repayment",
        "exclusions": ["F06.exclusion.degree_apprenticeship"],
        "published_on": "F05.published_on",
        "rules_updated_on": "F05.rules_updated_on",
        "facts": [
            "F05.instrument_kind.tuition",
            "F05.loan_maximum.tuition",
            "F05.rules_change",
            "F07.repayment_threshold.plan_5",
            "F07.repayment_rule",
            "F07.interest.plan_5",
            "F07.interest_rule",
            "F13.plan_5.undergraduate",
        ],
    },
    {
        "record_id": "funding:F05.maintenance",
        "source_ids": ["F05", "F06", "F07", "F13"],
        "programme": "F05.programme.maintenance",
        "instrument_kind": "loan",
        "eligible_costs": "F05.eligible_costs.maintenance",
        "rules": [
            "F06.rule_age_limit.maintenance",
            "F06.rule_residency.status",
            "F06.rule_residency.home",
            "F06.rule_residency.three_years",
            "F06.rule_course",
            "F06.rule_previous_study",
        ],
        "timing": "F05.timing.maintenance",
        "repayment": "F07.repayment",
        "exclusions": ["F06.exclusion.degree_apprenticeship"],
        "published_on": "F05.published_on",
        "rules_updated_on": "F05.rules_updated_on",
        "facts": [
            "F05.instrument_kind.maintenance",
            "F05.loan_maximum.with_parents",
            "F05.loan_maximum.away",
            "F05.loan_maximum.london",
            "F05.means_test",
            "F05.amount_rule",
            "F05.rules_change",
            "F07.repayment_threshold.plan_5",
            "F07.repayment_rule",
            "F07.interest.plan_5",
            "F07.interest_rule",
            "F13.plan_5.undergraduate",
        ],
    },
    {
        "record_id": "funding:F10",
        "source_ids": ["F10", "F11"],
        "programme": "F10.programme",
        "instrument_kind": "grant",
        "eligible_costs": "F10.eligible_costs",
        "rules": [
            "F11.rule_age",
            "F11.rule_age_band",
            "F10.rule_provider",
            "F11.rule_provider",
            "F11.rule_residency",
            "F10.rule_age_exception",
        ],
        "timing": "F10.timing",
        "repayment": {"unknown": "the pages do not say whether a bursary is repaid"},
        "exclusions": [],
        "published_on": "F10.published_on",
        "rules_updated_on": "F10.rules_updated_on",
        "facts": [
            "F10.instrument_kind",
            "F10.rule_age_band",
            "F10.bursary_maximum",
            "F10.amount_rule",
            "F10.over_19",
            "F10.eligible_costs_travel",
            "F11.rule_vulnerable_group",
            "F11.discretionary_criteria",
        ],
    },
    {
        "record_id": "funding:F12",
        "source_ids": ["F12", "F13"],
        "programme": "F12.programme.tuition",
        "instrument_kind": "loan",
        "eligible_costs": "F12.eligible_costs.tuition",
        "rules": [
            "F12.rule_start",
            "F12.rule_course",
            "F12.rule_residency.status",
            "F12.rule_residency.home",
            "F12.rule_residency.three_years",
        ],
        "timing": "F12.timing.tuition",
        "repayment": "F12.repayment",
        "exclusions": [],
        "published_on": "F12.published_on",
        "rules_updated_on": "F12.rules_updated_on",
        "facts": [
            "F12.loan_maximum.tuition",
            "F12.loan_maximum.tuition_total",
            "F12.credits",
            "F12.rates_change",
            "F12.write_off",
            "F12.interest",
            "F12.nhs_funding",
            "F13.plan_5.lifelong",
        ],
    },
    {
        "record_id": "funding:F12.maintenance",
        "source_ids": ["F12", "F13"],
        "programme": "F12.programme.maintenance",
        "instrument_kind": "loan",
        "eligible_costs": "F12.eligible_costs.maintenance",
        "rules": [
            "F12.rule_start",
            "F12.rule_course",
            "F12.rule_residency.status",
            "F12.rule_residency.home",
            "F12.rule_residency.three_years",
            "F12.rule_tuition_left",
            "F12.rule_in_person",
        ],
        "timing": "F12.timing.maintenance",
        "repayment": "F12.repayment",
        "exclusions": [],
        "published_on": "F12.published_on",
        "rules_updated_on": "F12.rules_updated_on",
        "facts": [
            "F12.loan_maximum.maintenance",
            "F12.first_payment",
            "F12.payment_schedule",
            "F12.rates_change",
            "F12.write_off",
            "F12.interest",
            "F13.plan_5.lifelong",
        ],
    },
    {
        "record_id": "funding:F04",
        "source_ids": ["F04"],
        "programme": "F04.programme",
        "instrument_kind": "programme",
        "eligible_costs": "F04.eligible_costs",
        "rules": ["F04.rule_age"],
        "timing": "F04.timing",
        "repayment": {"unknown": "not a loan"},
        "exclusions": [],
        "published_on": "F04.published_on",
        "rules_updated_on": "F04.rules_updated_on",
        "facts": ["F04.instrument_kind", "F04.employer_share"],
    },
]
T_LEVEL_OPTION: dict[str, Any] = {
    "record_id": "option:C11",
    "source_id": "C11",
    # Leeds, where the bookkeeping target is: the page names an accounting T Level.
    "target_ids": ["bookkeeping-assistant-leeds"],
    "title": "C11.title",
    "provider": {"unknown": "no provider is named; the page points to a list of providers"},
    "credential": "C11.credential",
    "awarding_body": {"unknown": "not stated on the page"},
    "recognising_body": {"unknown": "not stated on the page"},
    "level": {
        "unknown": "the page names no qualification level: a T Level is 'broadly equivalent in "
        "size to 3 A Levels' (C11.size_equivalence)"
    },
    "delivery_mode": "C11.delivery_mode",
    "assessment": "C11.assessment",
    "entry_requirements": ["C11.entry_requirement"],
    "facts": [
        "C11.size_equivalence",
        "C11.placement_duration",
        "C11.classroom_hours",
        "C11.pass_rule",
        "C11.availability",
        "C11.subject_accounting",
        "C11.progression",
        "C11.published_on",
        "C11.rules_updated_on",
    ],
}
T_LEVEL_OFFERING: dict[str, Any] = {
    "record_id": "offering:C11",
    "option_id": "option:C11",
    "intake": {"unknown": "no provider or start date is stated"},
    "application_deadline": {"unknown": "not stated on the page"},
    "duration": "C11.duration",
    "schedule": {
        "unknown": "the page states typical classroom hours over the 2 years "
        "(C11.classroom_hours), not a weekly pattern"
    },
    "fee_total": {
        "unknown": "the page states no fee to the student (it describes funding for "
        "providers): unknown, never 0"
    },
    "instalment": {"unknown": "not stated on the page"},
    "wage": {"unknown": "not stated on the page (nor whether the industry placement is paid)"},
    "location": {
        "unknown": "no provider is named: 'available at selected colleges, schools and other "
        "providers across England' (C11.availability)"
    },
    "extra_costs": [],
    "funding_conditions": [],
}
# funding:F02, the Advanced Learner Loan: what two more pages of its guide state.
ALL_CHANGE: dict[str, Any] = {
    "source_ids": ["F02", "F01", "F08", "F09", "F13"],
    "eligible_costs": "F08.eligible_costs",
    "timing": "F08.timing",
    "repayment": "F09.repayment",
    "as_of": AS_OF,
}
ALL_FACTS = [
    "F08.loan_minimum",
    "F08.amount_rule",
    "F09.interest",
    "F09.alternative_if_eligible",
    "F09.write_off",
    "F13.plan_5.learner_loan",
]


def labels() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(LABELS.read_text(encoding="utf-8"))
    return data


def school_leaver_pack(source: Pack | None = None) -> Pack:
    """Version 0.3.0: 0.2.0 with the school-leaver pages, parsed and checked like any version."""
    pack = load_pack(SOURCE_VERSION) if source is None else source
    data = pack.model_dump(mode="json")
    added = labels()
    pages = {s["source_id"]: s for s in added["sources"]}
    for page in added["sources"]:
        after = max(
            i for i, s in enumerate(data["sources"]) if s["source_id"][0] == page["source_id"][0]
        )
        data["sources"].insert(after + 1, page)
    for claim in added["claims"]:
        Claim.model_validate(claim)
        same = [
            i for i, c in enumerate(data["claims"]) if c["source_id"][0] == claim["source_id"][0]
        ]
        data["claims"].insert(max(same) + 1, claim)
    proposed = {"review_state": "proposed", "as_of": AS_OF}
    data["funding_instruments"] += [
        {**proposed, "jurisdiction": "GB-ENG", "award_state": "not_assessed", **record}
        for record in NEW_FUNDING
    ]
    data["learning_options"].append({**proposed, **T_LEVEL_OPTION})
    data["offerings"].append({**proposed, "facts": [], **T_LEVEL_OFFERING})
    [learner_loan] = [r for r in data["funding_instruments"] if r["record_id"] == "funding:F02"]
    learner_loan.update(ALL_CHANGE)
    learner_loan["facts"] = [*learner_loan["facts"], *ALL_FACTS]
    if set(pages) & {s.source_id for s in pack.sources}:
        raise OptionPackError("a school-leaver page reuses a slot")
    data.update(
        pack_version=VERSION,
        dated=DATED.isoformat(),
        label_review=LABEL_REVIEW,
        notes=[*NOTES, *pack.notes],
    )
    built = parse_pack(data)
    problems = check_pack(built)
    if problems:
        raise OptionPackError(f"the school-leaver pack fails its checks: {'; '.join(problems)}")
    return built


def changed_records(pack: Pack, before: Pack) -> list[str]:
    """The ids of the records new in `pack` or different from `before`: the funding first
    (the loans decide most routes), then the rest, each in pack order."""
    earlier = {r.record_id: r for r in before.records()}
    changed = [r.record_id for r in pack.records() if earlier.get(r.record_id) != r]
    return sorted(changed, key=lambda record_id: not record_id.startswith("funding:"))


class _EveryFact(_Rows):
    """Session 2's rows, with every fact asked: the session is short, and a fact a route does
    not read is still a value the person will see."""

    def ask(self, record_id: str, field: str, ref: Ref, shown: str | None = None) -> None:
        if shown is None and isinstance(ref, str):
            value = self._pack.claim(ref).value
            shape = CLAIM_FIELD_SHAPES.get(self._pack.claim(ref).field)
            if shape == "age_rule" and isinstance(value, dict):
                on = f" on {value['on']}" if value.get("on") else ""
                shown = f"at least {value['minimum_age']}{on}"
        super().ask(record_id, field, ref, shown)

    def facts(self, record_id: str, facts: list[str]) -> None:
        for claim_id in facts:
            field = self._pack.claim(claim_id).field
            if field != "instrument_kind":  # asked with the record's kind
                self.ask(record_id, f"fact: {field}", claim_id)


def _record_rows(pack: Pack, record_id: str) -> list[Row]:
    rows = _EveryFact(pack)
    funding = {f.record_id: f for f in pack.funding_instruments}
    options = {o.record_id: o for o in pack.learning_options}
    if record_id in funding:
        rows.funding(funding[record_id])
    elif record_id in options:
        rows.option(options[record_id])
    return rows.rows


# A row changes a route or a person's reading of one: money, payment and repayment, who
# qualifies, length and hours. The rest (titles, dates of publication, descriptions) come after.
FIRST_FIELDS = (
    *("timing", "repayment", "eligible_costs", "fee_total", "duration", "schedule", "wage"),
    *("intake", "application_deadline", "entry requirement", "instrument kind and award state"),
)
FIRST_PREFIXES = ("rule_", "exclusion", "fact: loan_", "fact: bursary_", "fact: repayment_")
FIRST_FACTS = (
    *("fact: rules_change", "fact: means_test", "fact: amount_rule", "fact: rule_"),
    *("fact: interest", "fact: placement_duration", "fact: classroom_hours", "fact: pass_rule"),
    *("fact: write_off", "fact: payment_schedule", "fact: employer_share", "fact: other_funding"),
)


def _first(row: Row) -> bool:
    return row.field in FIRST_FIELDS or row.field.startswith(FIRST_PREFIXES + FIRST_FACTS)


def package_rows(pack: Pack, before: Pack) -> tuple[list[Row], list[Row]]:
    """Every row of the records new or changed since `before`, a changed record's unchanged
    rows left out (session 2 asked them): the rows that change a route, then the rest."""
    first: list[Row] = []
    rest: list[Row] = []
    for record_id in changed_records(pack, before):
        asked_before = set(_record_rows(before, record_id))
        for row in _record_rows(pack, record_id):
            if row not in asked_before:
                (first if _first(row) else rest).append(row)
    return first, rest


WAITING = """\
## Still unknown (not asked)

- **The apprentice's training fee** (`offering:C09`). GOV.UK's funding page for employers
  (F04) says the government and the employer pay for the training (asked below), but not
  what the apprentice pays. The fee stays unknown, never £0.
- **The nursing degree's UCAS deadline** (`offering:C08`). UCAS's dates page (C12) was
  fetched, but the parts located on it name the "Equal consideration date for applications
  for most undergraduate courses" without the date itself. The deadline stays unknown. The
  page is not GOV.UK, so its rights wait for you at this session.

## Which loans a September 2027 start gets

Student finance changes for courses starting on or after 1 January 2027. The pack keeps both
sets of rules, each with its own record:

- **Courses starting before then:** `funding:F05` and `funding:F05.maintenance` (the 2026 to
  2027 caps).
- **Courses starting on or after then:** `funding:F12` and `funding:F12.maintenance`, the
  Lifelong Learning Entitlement. The page says it covers "most undergraduate" courses but
  names none, so the nursing degree (from September 2027) falls here only if it is one of
  them.
"""

HOW = """\
## How to answer

1. Read the row's excerpt. Open the page if you need its context: each page's address is in
   `corpus/manifest.json` (slots F04 to F13 and C11).
2. Write **yes** if the page states the value as shown. For an "unknown" row, yes means the
   page does not state it.
3. Write **no** otherwise, with the right reading.
4. Leave a row blank if you cannot decide.

A record becomes reviewed only when every one of its rows is answered yes. Otherwise it stays
proposed, and a "no" is applied as a correction with its span. Version {version} is not
changed: the decisions are published as a new version. The rows ask no rights question: every
page they cite is GOV.UK, under the Open Government Licence.

Money is shown in pounds. "up to" is a cap the page states, never what a person gets.
Excerpts are the page's own text, HTML included, with runs of whitespace collapsed. The live
page may have changed since {dated}: answer from the excerpt.
"""


def _minutes(rows: int) -> int:
    return -(-rows * SECONDS_PER_ROW // 60)


def review_package(pack: Pack, before: Pack) -> str:
    """The school-leaver pack session's package, as Markdown: the same text for the same
    packs, so its question numbers are stable."""
    first, rest = package_rows(pack, before)
    total = len(first) + len(rest)
    records = changed_records(pack, before)
    lines = [
        f"# The school-leaver pack session: option pack {pack.pack_version} (H-07)",
        "",
        "Generated by `tools.school_leaver_pack --package` (from `backend/`). Do not edit it by",
        "hand: a fast test checks it against the tool's output, so its numbers stay stable.",
        "",
        "- **Status:** agent preparation (Task 7f). The review is not run - requires human",
        "  (H-07, ruling R2). Nothing in this file is an answer. The product owner may rule",
        "  that an AI's check of the rote rows counts as their review, as at session 2; an",
        "  agent never assumes it.",
        f"- **What:** {total} yes/no questions on the {len(records)} records new or changed in",
        f"  {pack.pack_version}: {', '.join(f'`{r}`' for r in records)}.",
        f"- **Time:** about {_minutes(total)} minutes at {SECONDS_PER_ROW} seconds a row. Part 1"
        f" ({len(first)} rows) holds",
        "  everything that changes a route: money, how each loan is paid and repaid, who",
        "  qualifies, length and hours. Stop after it if time is short.",
        "",
        WAITING,
        HOW.format(version=pack.pack_version, dated=pack.dated.isoformat()),
    ]
    n = 0
    for title, rows in (
        (f"Part 1: what changes a route (Q1{DASH}Q{len(first)})", first),
        (f"Part 2: the rest (Q{len(first) + 1}{DASH}Q{total})", rest),
    ):
        lines += [f"## {title}", "", *TABLE]
        for row in rows:
            n += 1
            cells = [f"Q{n}", f"`{row.record_id}`", row.field, row.value, row.span]
            lines.append(f"| {' | '.join(cells)} | yes / no |")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the candidate version here")
    parser.add_argument("--package", action="store_true", help="write the session's package")
    args = parser.parse_args(argv)
    if args.out:
        args.out.write_text(dump_pack(school_leaver_pack()), encoding="utf-8")
        print(f"wrote {args.out}\npublish it: python -m tools.option_pack_files --pack {args.out}")
    if args.package:
        text = review_package(load_pack(VERSION), load_pack(SOURCE_VERSION))
        PACKAGE_PATH.write_text(text, encoding="utf-8")
        print(f"wrote {PACKAGE_PATH}")


if __name__ == "__main__":
    main()
