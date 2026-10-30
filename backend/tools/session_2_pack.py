"""The England option pack 0.2.0: session 2's review (H-07) of version 0.1.0, transcribed from
the product owner's record (`docs/reviews/session-2-answers.md`) and applied under the
partial-record rule (Task 7c; ADR 0011 decisions 14 and 15). The agent decides nothing: each
answer is applied as written, and every answer other than yes is listed here with what it
does, so the published version traces to the record line by line.

- **Which rows are a record's.** Every question that states one of its values: Q1-Q344 (the
  package `tools.option_pack_files` generated from 0.1.0), T11-T27 and T32-T36 (what the
  checker read from an offering or an outcome) and R41-R58 (each outcome's proposed level).
  The fixture person (T1-T10), the checker's conclusions (T28-T31) and the capability
  reference (R1-R40) are not pack records.
- **Reviewed** only when at least one row is a record's, every one was answered yes, and no
  answer changed it. Anything else stays `proposed`; a record no row asks about carries no
  review, since nobody decided it. A bare "?" leaves its record undecided, its values as
  they were.
- **A "no" that states the right value, quoting the same page, in the field's declared
  shape** is applied as a new claim, span-cited (offsets checked against the kept body, or
  inside a stored claim's excerpt), whose note names the question. Its record stays
  `proposed`: the corrected value has not been reviewed.
- **Otherwise** the field becomes unknown with the review's reason; a fact or rule the
  reviewer called wrong is left out; a requirement's importance becomes `unknown`; an
  outcome the reviewer says its page does not support becomes `unsupported`. A "no" whose
  own words keep the value as served (the same range with a qualification the shape cannot
  hold, or evidence from a document outside the corpus) is recorded and the value kept.
  Never a value the reviewer called wrong, and never one they did not state.
- **Provenance.** Q1-Q15 are the product owner's own answers; the rest were checked by an AI
  and count as their review by their ruling of 2026-10-30.

Run from `backend/`: `uv run --locked python -m tools.session_2_pack --out FILE`, then publish
FILE with `uv run --locked python -m tools.option_pack_files --pack FILE` and pin the SHA-256
it prints. A fast test checks the committed version is exactly this tool's output.
"""

import argparse
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import JsonValue

from careerwright.catalogue.option_pack import (
    OptionPackError,
    Pack,
    ReviewState,
    check_pack,
    dump_pack,
    load_pack,
    parse_pack,
)
from tools.localenv import REPO_ROOT
from tools.option_pack_files import PACKAGE_VERSION, parts

SOURCE_VERSION = PACKAGE_VERSION  # the version session 2 reviewed
VERSION = "0.2.0"
DATED = date(2026, 10, 30)
REVIEWS = REPO_ROOT / "docs" / "reviews"
ANSWERS_PATH = REVIEWS / "session-2-answers.md"
CHECKER_PATH = REVIEWS / "session-2-checker-questions.md"
CAPABILITY_PATH = REVIEWS / "session-2-capability-questions.md"
REVIEWER = "the product owner"
SESSION = "session 2 (2026-10-29 to 2026-10-30)"
ANSWERED_ON = date(2026, 10, 29)  # the product owner's own answers, Q1-Q15
ADOPTED_ON = date(2026, 10, 30)  # their ruling that the AI-checked answers count

Verdict = Literal["yes", "no", "?"]
_ANSWER = re.compile(r"^- ([QTR][0-9]+)( \(checked by AI\))?: (yes|no|\?)(.*)$")
_ROW = re.compile(r"^\| ([TR][0-9]+) \| `([^`]+)` \| ([^|]+) \|")


@dataclass(frozen=True)
class Answer:
    question: str
    verdict: Verdict
    words: str  # the rest of the answer, as written
    by_ai: bool


def answers() -> dict[str, Answer]:
    """Every Q, T and R answer in the product owner's record, by question."""
    found: dict[str, Answer] = {}
    for line in ANSWERS_PATH.read_text(encoding="utf-8").splitlines():
        match = _ANSWER.match(line)
        if match is None:
            continue
        question, ai, verdict, rest = match.groups()
        if question in found:
            raise ValueError(f"{question} is answered twice")
        words = rest.strip().lstrip("-—").strip()
        found[question] = Answer(question, cast(Verdict, verdict), words, ai is not None)
    return found


def _question_rows() -> Iterator[tuple[str, str, str]]:
    """(question, record, third column) for each T and R row of the session 2 sheets."""
    for path in (CHECKER_PATH, CAPABILITY_PATH):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _ROW.match(line)
            if match is not None:
                question, record, third = match.groups()
                yield question, re.split(r"[#~]", record)[0], third.strip()


def record_rows(pack: Pack) -> dict[str, list[str]]:
    """Each record's rows: the questions that state one of its values, in package order."""
    ids = {r.record_id for r in pack.records()}
    found: dict[str, list[str]] = {}
    n = 0
    for part in parts(pack):
        for _, rows in part.sections:
            for row in rows:
                n += 1
                found.setdefault(row.record_id, []).append(f"Q{n}")
    for question, record, third in _question_rows():
        if record in ids and third != "result":  # T28-T31 are the checker's conclusions
            found.setdefault(record, []).append(question)
    return found


def outcome_rubrics() -> dict[str, str | None]:
    """The rubric each outcome's proposed level was asked against (R41-R58), or None for a
    credential row, which has no rubric."""
    return {
        record: None if "(no rubric)" in third else third.strip("`")
        for question, record, third in _question_rows()
        if question.startswith("R") and record.startswith("outcome:")
    }


@dataclass(frozen=True)
class NewClaim:
    """A corrected value, span-cited on the same page. `within`: a stored claim whose excerpt
    holds these offsets (a page kept as excerpts only); None: located in the kept body."""

    claim_id: str
    field: str
    value: JsonValue
    start: int
    end: int
    excerpt: str
    occurrences: int | None
    note: str
    within: str | None = None

    def __str__(self) -> str:
        return self.claim_id

    def as_claim(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "source_id": self.claim_id.split(".")[0],
            "field": self.field,
            "value": self.value,
            "span": {"start": self.start, "end": self.end},
            "excerpt": self.excerpt,
            "occurrences": self.occurrences,
            "note": self.note,
        }


@dataclass(frozen=True)
class Cite:
    """The field cites a corrected claim; in a list field, in place of `replaces`."""

    field: str
    claim: NewClaim
    replaces: str | None = None


@dataclass(frozen=True)
class MarkUnknown:
    field: str
    reason: str


@dataclass(frozen=True)
class Drop:
    """A fact or rule the reviewer called wrong, left out (its claim with it)."""

    field: str
    claim_id: str


@dataclass(frozen=True)
class Assign:
    """A record attribute set to the format's own word for what the review leaves."""

    field: str
    value: str


@dataclass(frozen=True)
class AddFact:
    """A claim the record keeps beside a corrected field: still right, no longer its span."""

    claim_id: str

    @property
    def field(self) -> str:
        return "facts"


Edit = Cite | MarkUnknown | Drop | Assign | AddFact


@dataclass(frozen=True)
class Decision:
    """What one answer other than yes does to one record, and why in a few words."""

    question: str
    record_id: str
    note: str
    edits: tuple[Edit, ...] = ()


# The corrections: each a value the reviewer stated, quoting the same page.
C01_PRACTICE = NewClaim(
    "C01.outcome_evidence.4",
    "outcome_evidence",
    "Get hands-on experience with industry leading tools like Tableau and PowerBI.",
    74838,
    74915,
    "Get hands-on experience with industry leading tools like Tableau and PowerBI.",
    1,
    "Session 2 correction (Q53): practice is advertised under the heading 'Communicating and "
    "presenting data'.",
)
C04_ACCESS = NewClaim(
    "C04.access_period.corrected",
    "access_period",
    [
        {
            "unit": "years",
            "minimum": 1,
            "maximum": 1,
            "mode": None,
            "typical": False,
            "unbounded": False,
        }
    ],
    5809,
    5904,
    "one year of 24/7 access to all training material, with an average completion time of 6-8 "
    "months",
    3,
    "Session 2 correction (Q56): access lasts one year ('one year of 24/7 access'), not up to "
    "a year.",
    within="C04.access_period",
)
C05_ASSESSMENT = NewClaim(
    "C05.assessment",
    "assessment",
    "four external exams",
    164231,
    164279,
    "There are four external exams during the course.",
    1,
    "Session 2 correction (Q153, R49): the page states its assessment under 'Assessment types'.",
)
F02_PUBLISHED = NewClaim(
    "F02.published_on",
    "published_on",
    "2016-05-16",
    12162,
    12236,
    '<meta name="govuk:first-published-at" content="2016-05-16T09:00:07+01:00">',
    1,
    "Session 2 correction (Q198): the page's metadata state its first publication; the date "
    "at the page's own offset.",
)
F02_UPDATED = NewClaim(
    "F02.rules_updated_on",
    "rules_updated_on",
    "2024-10-14",
    12308,
    12381,
    '<meta name="govuk:public-updated-at" content="2024-10-14T10:36:04+01:00">',
    1,
    "Session 2 correction (Q199): the page's metadata state its last public update; the date "
    "at the page's own offset.",
)
RSQUO = chr(0x2019)  # a right single quotation mark, as the GOV.UK pages write it
_MAY_NEED = (
    "the list opens 'You may need to apply for a different type of student finance if "
    f"you{RSQUO}re:' (offsets 5311-5383), so the other finance is conditional."
)
F02_LLE = NewClaim(
    "F02.lle_interaction.corrected",
    "lle_interaction",
    {
        "levels": [4, 5, 6],
        "courses_starting_on_or_after": "2027-01-01",
        "use_instead": "may need Lifelong Learning Entitlement funding instead",
    },
    5653,
    5785,
    "studying a level 4, 5 or 6 qualification on a course that starts on or after 1 January "
    "2027 - apply for student finance through your",
    2,
    f"Session 2 correction (Q206): {_MAY_NEED}",
    within="F02.lle_interaction",
)
F02_HTQ = NewClaim(
    "F02.htq_interaction.corrected",
    "htq_interaction",
    "level 4 or 5 Higher Technical Qualifications may need undergraduate funding instead",
    5433,
    5527,
    "studying a level 4 or 5 qualification with Higher Technical Qualification approval - "
    "apply for",
    2,
    f"Session 2 correction (Q207): {_MAY_NEED}",
    within="F02.htq_interaction",
)

_SELF_PACED = "the page states the study pattern as 'Self-paced', and no weekly hours or timetable"
_OVERVIEW = "the course overview, a PDF outside the corpus,"
_PRO_RATA = "the range stands with 'pro rata per annum'"
_NO_SOC = "the page states no SOC code; the crosswalk was an inference: left out"
_PREPARES = (
    "the course prepares for the exams ('prepared to take') and excludes their fees: an exam "
    "outcome is unsupported"
)

DECISIONS: tuple[Decision, ...] = (
    # Part 1: P01 (Q1-Q67)
    Decision(
        "Q23",
        "job:J18",
        "the embedded data mark an agency; no stored excerpt cites it: unknown",
        (
            MarkUnknown(
                "advertiser",
                "session 2, Q23 (no): the page's embedded data name a recruitment consultancy "
                "('\"isAgency\":true'); the stored excerpts do not hold those words, so the kind "
                "is not cited",
            ),
        ),
    ),
    Decision(
        "Q25",
        "req:J18.1",
        "SQL is one of several tools ('at least one tool such as SQL, Power BI or Python'): "
        "importance unknown",
        (Assign("importance", "unknown"),),
    ),
    Decision(
        "Q38",
        "option:C01",
        "'195 hours' is not said to be guided learning hours: left out",
        (Drop("facts", "C01.guided_hours"),),
    ),
    Decision(
        "Q39",
        "offering:C01",
        "£0 only if eligible ('You could train for free'), no price for anyone else: unknown",
        (
            MarkUnknown(
                "fee_total",
                "session 2, Q39 (no): the fee is £0 only for an eligible learner ('You could "
                "train for free'); the page states no price for anyone else",
            ),
        ),
    ),
    Decision(
        "Q44",
        "offering:C01",
        "no timetable is confirmed; the form offers preferred times as choices",
        (
            MarkUnknown(
                "schedule",
                "session 2, Q44 (no): no weekly timetable is confirmed; the enquiry form offers "
                "preferred course times as choices, such as '18:00pm - 21:00pm'",
            ),
        ),
    ),
    Decision(
        "Q53",
        "outcome:C01.3",
        "practice is advertised under this heading: corrected, span-cited",
        (
            Assign("evidence_kind", "practice"),
            Cite("source_span", C01_PRACTICE),
            AddFact("C01.outcome_evidence.3"),
        ),
    ),
    Decision(
        "Q56",
        "option:C04",
        "access lasts one year, not up to a year: corrected, span-cited",
        (Cite("facts", C04_ACCESS, replaces="C04.access_period"),),
    ),
    Decision(
        "Q63",
        "offering:C04",
        "flexible, live online training with no session times",
        (
            MarkUnknown(
                "schedule",
                "session 2, Q63 (no): the page describes 'Flexible learning' and 'Live, "
                "instructor-led online training', but states no session times",
            ),
        ),
    ),
    # Part 2: P03-P05's courses, then the funding (Q68-Q219)
    Decision(
        "Q92",
        "offering:C10",
        "self-paced, which a schedule cannot hold",
        (MarkUnknown("schedule", f"session 2, Q92 (no): {_SELF_PACED}"),),
    ),
    Decision("Q95", "outcome:C10.1", _PREPARES, (Assign("confidence", "unsupported"),)),
    Decision("Q96", "outcome:C10.2", _PREPARES, (Assign("confidence", "unsupported"),)),
    Decision(
        "Q98",
        "option:C03",
        "a 60% quiz comes before later modules; no stored excerpt cites it: unknown",
        (
            MarkUnknown(
                "assessment",
                "session 2, Q98 (no): quizzes need '60% marks on the quiz test' before later "
                "modules, and only further assessments are excluded; the stored excerpts do not "
                "hold the quiz rule",
            ),
        ),
    ),
    Decision(
        "Q102",
        "offering:C03",
        "instalments start at £50, so none for this course alone",
        (
            MarkUnknown(
                "instalment",
                "session 2, Q102 (no): the page offers instalments only for 'course purchases "
                "between £50 and £6000', so this £19 course alone has none",
            ),
        ),
    ),
    Decision(
        "Q106",
        "offering:C03",
        "self-paced, which a schedule cannot hold",
        (MarkUnknown("schedule", f"session 2, Q106 (no): {_SELF_PACED} (C03.delivery_mode)"),),
    ),
    Decision(
        "Q109",
        "outcome:C03.1",
        "'No formal qualification' establishes no outcome for NMC registration: kept unsupported",
    ),
    Decision(
        "Q127",
        "outcome:C08.1",
        "eligibility to register, not a work sample; no evidence kind names a credential outcome, "
        "typed by its row (R54 yes)",
    ),
    Decision(
        "Q142",
        "outcome:C02.2",
        "the page names transaction processing, not reconciliation: kept unsupported",
    ),
    Decision(
        "Q153",
        "outcome:C05.1",
        "the page states 'four external exams': corrected to exam, span-cited",
        (
            Assign("evidence_kind", "exam"),
            Cite("source_span", C05_ASSESSMENT),
            AddFact("C05.outcome_evidence"),
        ),
    ),
    Decision(
        "Q153",
        "option:C05",
        "the page states its assessment ('four external exams'): corrected, span-cited",
        (Cite("assessment", C05_ASSESSMENT),),
    ),
    Decision(
        "Q167",
        "outcome:C06.2",
        "the unit covers 'recording financial transactions', not examined reconciliation: "
        "unsupported",
        (Assign("confidence", "unsupported"),),
    ),
    Decision(
        "Q187",
        "funding:F01",
        "'earn below £25,750' states no period and not gross: the yearly gross cap is left out",
        (Drop("rules", "F01.rule_earnings"),),
    ),
    Decision(
        "Q198",
        "funding:F02",
        "first published 2016-05-16: span-cited",
        (Cite("published_on", F02_PUBLISHED),),
    ),
    Decision(
        "Q199",
        "funding:F02",
        "updated 2024-10-14: span-cited",
        (Cite("rules_updated_on", F02_UPDATED),),
    ),
    Decision(
        "Q201",
        "funding:F02",
        "not stated on this page: unknown",
        (
            MarkUnknown(
                "repayment",
                "session 2, Q201 (no): this eligibility page does not state the repayment rule; "
                f"F01 says the loans are paid back 'when you{RSQUO}re earning over a certain "
                "amount'",
            ),
        ),
    ),
    Decision(
        "Q206",
        "funding:F02",
        "conditional ('may need'): corrected",
        (Cite("rules", F02_LLE, replaces="F02.lle_interaction"),),
    ),
    Decision(
        "Q207",
        "funding:F02",
        "conditional ('may need'): corrected",
        (Cite("rules", F02_HTQ, replaces="F02.htq_interaction"),),
    ),
    # Part 3: P03-P05's job postings and requirements (Q220-Q344)
    Decision(
        "Q223",
        "job:J01",
        "AWD online is an employment agency; no stored excerpt cites it: unknown",
        (
            MarkUnknown(
                "advertiser",
                "session 2, Q223 (no): the page says 'AWD online operates as an employment "
                "agency.'; the stored excerpts do not hold those words, so the kind is not cited",
            ),
        ),
    ),
    Decision(
        "Q224",
        "job:J01",
        "AWD online is the agency; the employer is an unnamed client: unknown",
        (
            MarkUnknown(
                "employer",
                "session 2, Q224 (no): AWD online is the agency; the page names the employer "
                "only as 'our Client'",
            ),
        ),
    ),
    Decision(
        "Q261",
        "req:J15.4",
        "a valid UK driving licence warrants a DVLA-checked gate; a new gate is the capability "
        "model's: carried to Task 10",
    ),
    Decision(
        "Q269",
        "job:J06",
        _NO_SOC,
        (Drop("facts", "J06.occupation_crosswalk"),),
    ),
    Decision(
        "Q284",
        "job:J10",
        f"{_PRO_RATA}, which the pay shape cannot hold and no stored excerpt cites",
    ),
    Decision(
        "Q290",
        "req:J10.1",
        "the page also says 'Applicants must have current UK professional registration.': a "
        "conflict left open",
    ),
    Decision(
        "Q298",
        "job:J11",
        _NO_SOC,
        (Drop("facts", "J11.occupation_crosswalk"),),
    ),
    Decision("Q300", "job:J13", f"{_PRO_RATA}, kept as the fact J13.salary_basis_note"),
    Decision(
        "Q317",
        "job:J04",
        "no pay is shown; the embedded 33000-38000 is not an advertised range: unknown",
        (
            MarkUnknown(
                "salary",
                "session 2, Q317 (no): the page shows no pay; its embedded data hold 33000 to "
                "38000 per annum, which is not an advertised range, and no stored excerpt cites "
                "it",
            ),
        ),
    ),
    Decision(
        "Q333",
        "job:J16",
        "the embedded data mark a recruitment consultancy; no stored excerpt cites it: unknown",
        (
            MarkUnknown(
                "advertiser",
                "session 2, Q333 (no): the page's embedded data name a recruitment consultancy "
                '(\'"jobRecruiterType":"Recruitment consultancy"\'); the stored excerpts do not '
                "hold those words, so the kind is not cited",
            ),
        ),
    ),
    Decision(
        "Q334",
        "job:J16",
        "PRATAP is the recruiter; the employer is an unnamed client: unknown",
        (
            MarkUnknown(
                "employer",
                "session 2, Q334 (no): PRATAP PARTNERSHIP LTD is the recruiter; the page "
                "describes the employer only as 'An exciting business operating across the "
                "renewable energy, utilities and infrastructure sectors'",
            ),
        ),
    ),
    # The checker's readings of P01's outcomes (T32-T34)
    Decision("T32", "outcome:C01.1", f"{_OVERVIEW} assesses work with joins; no level"),
    Decision("T33", "outcome:C01.2", f"{_OVERVIEW} assesses 'apply validation'; no level"),
    Decision("T34", "outcome:C01.3", f"{_OVERVIEW} assesses presentations; no level"),
    # The proposed outcome levels (R41-R58)
    Decision("R41", "outcome:C01.1", f"{_OVERVIEW} permits Excel or SQL; no level"),
    Decision("R42", "outcome:C01.2", f"{_OVERVIEW} assesses 'test integrity'; no level"),
    Decision("R43", "outcome:C01.3", f"{_OVERVIEW} assesses the audience; no level"),
    Decision(
        "R46",
        "outcome:C03.1",
        "'No formal qualification' gives neither registration nor eligibility to apply",
    ),
    Decision("R49", "outcome:C05.1", "exam evidence, applied with Q153; no level is established"),
    Decision(
        "R50",
        "outcome:C06.1",
        "the AAT specification, outside the corpus, puts reconciliation here; exams set no "
        "level 2: no level",
    ),
    Decision(
        "R51",
        "outcome:C06.2",
        "the AAT specification, outside the corpus, maps this unit to records: carried to Task 10",
    ),
    Decision(
        "R52",
        "outcome:C07.1",
        "'the opportunity to achieve' does not show the exam is optional; unclear: no level",
    ),
    Decision(
        "R53",
        "outcome:C07.2",
        "'the opportunity to achieve' does not show the exam is optional; unclear: no level",
    ),
)

NOTES = [
    "Version 0.2.0 publishes session 2's review (H-07, 2026-10-29 to 2026-10-30) of version "
    "0.1.0, applied by Task 7c with tools.session_2_pack from the product owner's record "
    "(docs/reviews/session-2-answers.md). Q1-Q15 were answered by the product owner; "
    "Q16-Q344, T1-T36 and R1-R58 were checked by an AI and count as the product owner's review "
    "by their ruling of 2026-10-30. Version 0.1.0 is unchanged.",
    "A record is reviewed only when at least one session 2 row states one of its values, every "
    "such row was answered yes, and no answer changed it. Any other record stays proposed: "
    "explorable, never shown as current, never in an unqualified affordable-and-feasible or "
    "readiness result (ruling R9). A record no row asks about carries no review.",
    "A no that states the right value, quoting the same page, in the field's declared shape, "
    "is a new span-cited claim whose note names the question. Otherwise the field is unknown "
    "with the review's reason, or a fact or rule the reviewer called wrong is left out, with "
    "its reason in the record's review. No answer rejected a whole record, so none is left "
    "out.",
]
SKILL_ROWS_NOTE = (
    "Skill rows are pack-local (pack:<target>:<row>); the capability reference gives them "
    "rubrics. Session 2 accepted no proposed outcome level (R50 and R51, the only numbers, "
    "were no), so every planned outcome's level is still null; a reviewed outcome names the "
    "rubric its null level was judged against."
)
RECORD_GROUPS = (
    "job_postings",
    "skill_requirements",
    "learning_options",
    "offerings",
    "outcomes",
    "funding_instruments",
)
LABEL_REVIEW = (
    "session 2 (H-07), 2026-10-29 to 2026-10-30: the product owner's record, applied by Task "
    "7c; each record states its review_state and review"
)


def new_claims() -> list[NewClaim]:
    """Every corrected claim, once each, in decision order."""
    found: dict[str, NewClaim] = {}
    for decision in DECISIONS:
        for edit in decision.edits:
            if isinstance(edit, Cite):
                found.setdefault(edit.claim.claim_id, edit.claim)
    return list(found.values())


def _apply(record: dict[str, Any], edit: Edit) -> None:
    if isinstance(edit, MarkUnknown):
        record[edit.field] = {"unknown": edit.reason}
    elif isinstance(edit, Cite):
        if edit.replaces is None:
            record[edit.field] = edit.claim.claim_id
        else:
            listed: list[str] = record[edit.field]
            listed[listed.index(edit.replaces)] = edit.claim.claim_id
    elif isinstance(edit, Drop):
        record[edit.field].remove(edit.claim_id)
    elif isinstance(edit, Assign):
        record[edit.field] = edit.value
    else:
        record["facts"].append(edit.claim_id)


def _ranges(questions: list[str]) -> str:
    """Q39, Q40, Q41, T11 as 'Q39-Q41, T11'."""
    spans: list[list[str]] = []
    for question in questions:
        prefix, number = question[0], int(question[1:])
        last = spans[-1][-1] if spans else ""
        if last and last[0] == prefix and int(last[1:]) == number - 1:
            spans[-1].append(question)
        else:
            spans.append([question])
    return ", ".join(s[0] if len(s) == 1 else f"{s[0]}-{s[-1]}" for s in spans)


def _provenance(rows: list[str], answered: dict[str, Answer]) -> str:
    own = [q for q in rows if not answered[q].by_ai]
    by_ai = [q for q in rows if answered[q].by_ai]
    adopted = "checked by an AI, adopted by the product owner's ruling of 2026-10-30."
    if not by_ai:
        return "Answered by the product owner."
    if not own:
        return f"Rows {adopted}"
    return f"{_ranges(own)} answered by the product owner; {_ranges(by_ai)} {adopted}"


def _decision_text(
    rows: list[str], answered: dict[str, Answer], decisions: list[Decision], accepted: bool
) -> str:
    noted = {d.question: d.note for d in decisions}
    head = "Accepted: every row answered yes" if accepted else "Stays proposed"
    found = [f"{head} ({_ranges(rows)})"]
    for question in [*rows, *(q for q in noted if q not in rows)]:
        answer = answered[question]
        if answer.verdict != "yes":
            found.append(f"{question} {answer.verdict}: {noted.get(question, 'not decided')}")
    return "; ".join(found) + ". " + _provenance(rows, answered)


def reviewed_pack(source: Pack | None = None) -> Pack:
    """Version 0.2.0: the record applied to 0.1.0, parsed and checked like any version."""
    pack = load_pack(SOURCE_VERSION) if source is None else source
    answered = answers()
    rows = record_rows(pack)
    rubrics = outcome_rubrics()
    data = pack.model_dump(mode="json")
    by_id = {r["record_id"]: r for group in RECORD_GROUPS for r in data[group]}
    on_record: dict[str, list[Decision]] = {}
    for decision in DECISIONS:
        on_record.setdefault(decision.record_id, []).append(decision)
        for edit in decision.edits:
            _apply(by_id[decision.record_id], edit)
    claims: list[dict[str, Any]] = data["claims"]
    for claim in new_claims():
        source_id = claim.claim_id.split(".")[0]
        last = max(i for i, c in enumerate(claims) if c["source_id"] == source_id)
        claims.insert(last + 1, claim.as_claim())
    cited = {v for r in by_id.values() for v in _cited(r)}
    data["claims"] = [c for c in claims if c["claim_id"] in cited]
    for record_id, record in by_id.items():
        asked = rows.get(record_id, [])
        if not asked:
            continue  # nobody decided it: proposed, no review
        decisions = on_record.get(record_id, [])
        edited = any(d.edits for d in decisions)
        accepted = not edited and all(answered[q].verdict == "yes" for q in asked)
        own = all(not answered[q].by_ai for q in asked)
        record["review_state"] = (ReviewState.REVIEWED if accepted else ReviewState.PROPOSED).value
        record["review"] = {
            "reviewer": REVIEWER,
            "decided_on": (ANSWERED_ON if own else ADOPTED_ON).isoformat(),
            "session": SESSION,
            "decision": _decision_text(asked, answered, decisions, accepted),
        }
        if accepted and record_id.startswith("outcome:"):
            record["rubric_version"] = rubrics.get(record_id)
    data.update(
        pack_version=VERSION,
        dated=DATED.isoformat(),
        label_review=LABEL_REVIEW,
        # 0.1.0's notes: curation, P02, skill rows, claims, bodies, splits.
        notes=[*NOTES, pack.notes[1], SKILL_ROWS_NOTE, *pack.notes[3:]],
    )
    reviewed = parse_pack(data)
    problems = check_pack(reviewed)
    if problems:
        raise OptionPackError(f"the reviewed pack fails its checks: {'; '.join(problems)}")
    return reviewed


def _cited(record: dict[str, Any]) -> Iterator[str]:
    for name, value in record.items():
        if name in ("record_id", "review", "review_state", "as_of"):
            continue
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            yield from (v for v in value if isinstance(v, str))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="where to write the candidate")
    args = parser.parse_args(argv)
    args.out.write_text(dump_pack(reviewed_pack()), encoding="utf-8")
    print(f"wrote {args.out}\npublish it with: python -m tools.option_pack_files --pack {args.out}")


if __name__ == "__main__":
    main()
