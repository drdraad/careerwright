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
  degree's UCAS deadline (the UCAS page shows "13 Jan" beside the steps of its 2027 entry
  section, but its located excerpts do not show which step the date belongs to, or its
  year). Both fields keep their 0.2.0 unknowns.
- **The bursary is a programme, not a grant:** its pages do not say whether it is repaid,
  so no plan counts it as money (a grant is never repaid).

It also writes the school-leaver pack session's package (`docs/reviews/`): every row of the
new and changed records beside its span, the ones that change a route first.

Run from `backend/`: `uv run --locked python -m tools.school_leaver_pack --out FILE`, then
publish FILE with `uv run --locked python -m tools.option_pack_files --pack FILE` and pin the
SHA-256 it prints; `--package` writes the package. Fast tests check both committed files are
exactly this tool's output.
"""

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from careerwright.catalogue.option_pack import (
    CLAIM_FIELD_SHAPES,
    Claim,
    FundingInstrument,
    OptionPackError,
    Pack,
    Ref,
    check_pack,
    dump_pack,
    load_pack,
    parse_pack,
)
from tools.localenv import REPO_ROOT
from tools.option_pack_files import DASH, Row, _cited, _Rows

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
    "Education's introduction of T Levels (C11), retrieved on 2026-11-01. Its eight new "
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
    "unknown: the UCAS page (C12, class other, not in this pack) shows '13 Jan' beside the "
    "step headings of its '2027 entry application deadlines' section, but its located "
    "excerpts do not show which step the date belongs to, or its year.",
    "The 16 to 19 Bursary Fund (funding:F10) is a programme, not a grant: its pages do not "
    "say whether a bursary is repaid, so no plan counts it as money. The Lifelong Learning "
    "Entitlement's Tuition Fee Loan carries its page's age rule (under 60 on the first day "
    "of the course), and its Maintenance Loan the page's rule for those 60 or above.",
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
        # Not "grant" (never repaid): no page says whether a bursary is repaid, and a
        # programme plans no money by itself (planning/catalogue.py: NON_REPAYABLE).
        "instrument_kind": "programme",
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
        "repayment": {
            "unknown": "the pages do not say whether a bursary is repaid, so no plan counts "
            "it as money"
        },
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
            "F12.rule_age_limit.tuition",
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
            "F12.instrument_kind",
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
            "F12.rule_age_limit.maintenance",
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
            "F12.instrument_kind",
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

    def funding(self, fund: FundingInstrument) -> None:
        """Session 2's funding rows, but the kind is asked only beside a span that states it,
        in words a page can settle; the award state is never asked (no page states one)."""
        kinds = [c for c in fund.facts if self._pack.claim(c).field == "instrument_kind"]
        if kinds:
            stated = self._pack.claim(kinds[0]).value
            shown = KIND_WORDS.get(fund.instrument_kind) or str(stated)
            self.ask(fund.record_id, "kind", kinds[0], shown)
        for name in ("eligible_costs", "published_on", "rules_updated_on", "timing", "repayment"):
            self.ask(fund.record_id, name, getattr(fund, name))
        for claim_id in fund.rules:
            self.ask(fund.record_id, self._pack.claim(claim_id).field, claim_id)
        self.facts(fund.record_id, fund.facts)


# A kind as the person reads it. A programme has no words of its own: its row shows what the
# page says the scheme is.
KIND_WORDS = {
    "loan": "a loan: it is paid back",
    "grant": "a grant: it is never paid back",
    "fee_waiver": "a fee waiver: the fee is not charged",
}


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
    *("intake", "application_deadline", "entry requirement", "kind"),
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


# The package's words (CLAUDE.md, "Talking to the user"): each record, field and page in plain
# words; the claim and its place on the page go in the reference column only.
RECORD_NAMES = {
    "funding:F02": "The Advanced Learner Loan",
    "funding:F05": "Tuition Fee Loan, for courses starting before 1 January 2027",
    "funding:F05.maintenance": "Maintenance Loan, for courses starting before 1 January 2027",
    "funding:F10": "The 16 to 19 Bursary Fund",
    "funding:F12": "Tuition Fee Loan, for courses starting from 1 January 2027",
    "funding:F12.maintenance": "Maintenance Loan, for courses starting from 1 January 2027",
    "funding:F04": "Government funding for apprenticeship training",
    "option:C11": "A T Level",
    "offering:C11": "A T Level",
}
WHO_CAN_GET_IT = "Who can get it"
FIELD_WORDS = {
    "kind": "What it is",
    "eligible_costs": "What it pays for",
    "eligible_costs_travel": "What else it pays for",
    "timing": "How it is paid",
    "repayment": "How it is paid back",
    "published_on": "First published",
    "rules_updated_on": "Last updated",
    "rule_age": "Age rule",
    "rule_age_band": "Age rule",
    "rule_age_limit": "Age rule",
    "rule_age_exception": "Age rule: the exceptions",
    "rule_residency": "Where you live",
    "rule_course": WHO_CAN_GET_IT,
    "rule_previous_study": WHO_CAN_GET_IT,
    "rule_provider": WHO_CAN_GET_IT,
    "rule_vulnerable_group": "Who can get the larger bursary",
    "loan_minimum": "Least you can borrow",
    "loan_maximum": "Most you can borrow",
    "bursary_maximum": "Most you can get",
    "amount_rule": "How much you get",
    "means_test": "What you must tell them",
    "interest": "Interest",
    "interest_rule": "When interest is added",
    "write_off": "When what is left is cancelled",
    "repayment_plan": "Repayment plan",
    "repayment_threshold": "Paid back only on income over",
    "repayment_rule": "What sets each repayment",
    "rules_change": "When the rules change",
    "payment_schedule": "When payments arrive",
    "other_funding": "Other money",
    "employer_share": "What the employer pays",
    "alternative_if_eligible": "Something to get instead",
    "discretionary_criteria": "Who decides",
    "entry requirement": "Who can start",
    "credential": "What you get at the end",
    "assessment": "Grades",
    "size_equivalence": "How big it is",
    "placement_duration": "Work placement",
    "classroom_hours": "Classroom hours",
    "pass_rule": "To pass",
    "availability": "Where it is taught",
    "subject": "Subjects",
    "progression": "What it leads to",
    "fee_total": "Fee",
    "instalment": "Paying the fee in parts",
    "intake": "Start date",
    "application_deadline": "Apply by",
    "duration": "Length",
    "schedule": "Hours each week",
    "wage": "Pay while training",
}
PAGE_NAMES = {
    "C11": "Introduction of T Levels (Department for Education)",
    "F04": "Employing an apprentice: get funding (written for employers)",
    "F05": "Student finance for new full-time students (courses before 2027)",
    "F06": "Student finance: who qualifies (courses before 2027)",
    "F07": "Repaying your student loan: what you pay",
    "F08": "Advanced Learner Loan: what you'll get",
    "F09": "Advanced Learner Loan",
    "F10": "16 to 19 Bursary Fund",
    "F11": "16 to 19 Bursary Fund: eligibility",
    "F12": "Student finance for courses starting on or after 1 January 2027",
    "F13": "Repaying your student loan: which repayment plan you are on",
}
UCAS_PAGE = (  # C12, pending its rights review: not in the pack
    "https://www.ucas.com/applying/applying-to-university/dates-and-deadlines-for-uni-applications"
)
UCAS_ROW = (
    "The nursing degree: when to apply (UCAS)",
    "Apply by (UCAS's equal consideration date, 2027 entry)",
    "Not known yet. Please open UCAS's page and read the date beside “Equal consideration date"
    " for applications for most undergraduate courses”",
    "Careerwright found “13 Jan” beside the steps of the “2027 entry application deadlines”"
    " section. The words it kept don't show which step the date belongs to, or its year",
    "C12 (UCAS)",
    "the date: ______",
)

KNOW_FIRST = """\
## Good to know first

- **Which loans a September 2027 start gets.** Student finance changes for courses starting
  on or after 1 January 2027. Careerwright keeps both sets of rules: the older loans for
  courses starting before then, and the new loans (the "Lifelong Learning Entitlement")
  from then on. The new page says they cover "most undergraduate" courses, but it names
  none. So the nursing degree, starting in September 2027, gets the new loans only if it is
  one of those courses.
- **The bursary is not counted as money in a plan.** A grant is never paid back. The
  bursary's pages don't say whether a bursary is paid back, so Careerwright doesn't call it
  a grant, and no plan counts it as money. If you know a page that says it is never paid
  back, tell us at the session.
- **Still not known:**
  - What an apprentice pays for training. The funding page is written for employers. It
    says the government and the employer pay, but not what the apprentice pays. It stays
    unknown, never £0.
  - The nursing degree's UCAS date. On UCAS's dates page, Careerwright found "13 Jan" in
    the "2027 entry application deadlines" section, beside the steps. The words it kept
    don't show which step the date belongs to, or its year. So the date stays unknown.
    Question Q{ucas} asks you to read it on the page. UCAS is not GOV.UK, so whether
    Careerwright may keep words from its page is also yours to decide.
"""

HOW = """\
## How to answer

1. Read the page's words in the row. If they aren't enough, open the page (the list of
   pages is at the end).
2. Write **yes** if the page says what Careerwright read. For a "Not stated" row, yes means
   the page really doesn't say it.
3. Write **no** if it doesn't, and what the page says instead.
4. Leave it blank if you can't tell.

Each thing (a loan, the bursary, the T Level) counts as checked only when all its rows are
yes. A "no" is put right in a new version, from the page's words.

Money is in pounds. "Up to" is the most a scheme gives, never what a person gets. The page's
words are shown without the web page's markup. The pages may have changed since {dated}:
answer from the words shown.

Every page the yes/no rows quote is GOV.UK, free to use under the Open Government Licence, so
none of them asks about rights.
"""


def _minutes(rows: int) -> int:
    return -(-rows * SECONDS_PER_ROW // 60)


TABLE = [
    "| # | Question | What Careerwright read | The page's words | Reference¹ | Right? |",
    "|---|---|---|---|---|---|",
]
DATED_FIELDS = ("published_on", "rules_updated_on")
NOT_STATED = "not stated on the page"


def _long_date(day: date) -> str:
    return f"{day.day} {day:%B %Y}"


def _plain_value(row: Row) -> str:
    """What Careerwright read, in the person's words: pounds without empty pence, dates in
    words, an unknown as "Not stated", and no claim ids."""
    value = row.value
    if value.startswith("unknown: "):
        reason = value.removeprefix("unknown: ")
        if reason.startswith(NOT_STATED):
            value = "Not stated on the page" + reason.removeprefix(NOT_STATED)
        else:
            value = f"Not stated on the page: {reason}"
    elif row.field.removeprefix("fact: ") in DATED_FIELDS:
        value = _long_date(date.fromisoformat(value))
    value = re.sub(r"£([\d,]+)\.00\b", r"£\1", value)
    value = re.sub(r" \([A-Z]\d+\.[\w.]+\)", "", value)  # a claim's id
    return value[:1].upper() + value[1:]


def _claim_of(pack: Pack, row: Row) -> Claim | None:
    """The claim a row cites (its span is `_cited`'s "`excerpt` (claim id, place)")."""
    if row.span == "(no span)":
        return None
    claim = pack.claim(row.span.rsplit(" (", 1)[1].split(",", 1)[0])
    if _cited(claim) != row.span:
        raise OptionPackError(f"a row's span is not {claim.claim_id}'s")
    return claim


def _page_words(claim: Claim | None) -> str:
    """The excerpt without its markup; a page's hidden detail (a meta tag) by name."""
    if claim is None:
        return "(none)"
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", claim.excerpt)).split())
    text = re.sub(r"\s+([).,:;])", r"\1", re.sub(r"\(\s+", "(", text))  # a tag's spaces
    if not text:
        meta = re.fullmatch(r'<meta name="([^"]+)" content="([^"]+)">', claim.excerpt.strip())
        if meta is None:
            raise OptionPackError(f"{claim.claim_id}'s excerpt has no words")
        return f"(the page's hidden details) {meta[1]}: {meta[2]}"
    return f"“{text.replace('|', '/')}”"


def _reference(claim: Claim | None) -> str:
    if claim is None:
        return ""
    span = claim.span
    if span.pointer is not None:
        return f"{claim.claim_id}, {span.pointer}"
    return f"{claim.claim_id}, characters {span.start}{DASH}{span.end}"


def _question(row: Row) -> str:
    return FIELD_WORDS[row.field.removeprefix("fact: ")]


def _table(pack: Pack, rows: list[Row], number: int) -> tuple[list[str], int]:
    """One part's rows, under a heading for each record, numbered from `number`."""
    lines: list[str] = []
    heading = None
    for row in rows:
        if RECORD_NAMES[row.record_id] != heading:
            heading = RECORD_NAMES[row.record_id]
            lines += ["", f"### {heading}", "", *TABLE]
        number += 1
        claim = _claim_of(pack, row)
        cells = [_question(row), _plain_value(row), _page_words(claim), _reference(claim)]
        lines.append(f"| Q{number} | {' | '.join(cells)} | yes / no |")
    return lines, number


def _pages(pack: Pack, rows: list[Row]) -> list[str]:
    cited = {c.source_id for r in rows if (c := _claim_of(pack, r)) is not None}
    sources = [s for s in pack.sources if s.source_id in cited]
    lines = ["## The pages", "", "| Reference | Page | Address |", "|---|---|---|"]
    lines += [f"| {s.source_id} | {PAGE_NAMES[s.source_id]} | {s.url} |" for s in sources]
    lines.append(f"| C12 | UCAS: dates and deadlines for uni applications | {UCAS_PAGE} |")
    return lines


def review_package(pack: Pack, before: Pack) -> str:
    """The school-leaver pack session's package, as Markdown in plain words: the same text
    for the same packs, so its question numbers are stable."""
    first, rest = package_rows(pack, before)
    ucas = len(first) + 1
    total = ucas + len(rest)
    things = list(dict.fromkeys(RECORD_NAMES[r] for r in changed_records(pack, before)))
    lines = [
        f"# Checking the school-leaver facts (option pack {pack.pack_version})",
        "",
        "Careerwright read eleven GOV.UK pages on money and courses for school leavers. Each",
        "row below is one thing it read, beside the page's own words. Please check each one.",
        "",
        "- **Status:** not run — requires human. Nothing here is answered yet. You may decide",
        "  that an AI's check of the simple rows counts as yours, as you did last time;",
        "  Careerwright never assumes it.",
        "- **What it covers:**",
        *(f"  - {thing}" for thing in things),
        f"- **Time:** about {_minutes(total)} minutes for {total} questions. Part 1 (Q1{DASH}"
        f"Q{ucas}) is",
        "  everything that changes a plan: money, how each loan is paid and paid back, who can",
        "  get it, length and hours. If time is short, stop after Part 1.",
        "",
        KNOW_FIRST.format(ucas=ucas),
        HOW.format(dated=_long_date(pack.dated)),
    ]
    part_1, n = _table(pack, first, 0)
    lines += [f"## Part 1: what changes a plan (Q1{DASH}Q{ucas})", *part_1]
    heading, *cells = UCAS_ROW
    lines += ["", f"### {heading}", "", *TABLE, f"| Q{ucas} | {' | '.join(cells)} |", ""]
    part_2, _ = _table(pack, rest, n + 1)
    lines += [f"## Part 2: the rest (Q{ucas + 1}{DASH}Q{total})", *part_2, ""]
    lines += [*_pages(pack, first + rest), ""]
    lines += [
        "¹ The reference names the claim and where its words sit on the saved page (characters",
        "from the start). You don't need it to answer.",
        "",
        "Generated by `tools.school_leaver_pack --package` (from `backend/`). Don't edit it by",
        "hand: a test checks it against the tool.",
    ]
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
