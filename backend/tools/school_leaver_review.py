"""The England option pack 0.4.0: the school-leaver pack session's review (H-07, 2026-11-01)
of version 0.3.0, applied from the product owner's record
(`docs/reviews/school-leaver-pack-session.md`; Task 7f's second half; ADR 0011). The agent
decides nothing: each answer is applied as written, and every answer other than yes is listed
here with what it does, so the published version traces to the record line by line.

- **Why a new version.** 0.3.0 is committed, merged and named by the session's question
  sheet, so it never changes (ADR 0011): its review is a new version, as session 2's review
  of 0.1.0 was 0.2.0.
- **Whose answers.** An AI checked all 139 rows; the product owner ruled that its check
  counts as their review ("AI check counts as my review"). They answered the six rows sent
  back themselves: "yes, fix 1-3, 4. no not fair, 5 yes, 6 yes".
- **A record's rows** are the 0.3.0 sheet's rows about it (`tools.school_leaver_pack`'s
  package): Q115, the UCAS row, is the nursing degree's offering (`offering:C08`).
- **Reviewed** when every row is yes, or is a correction or decision the product owner gave
  (Q75, Q95, Q104, Q110, Q115). A record with an undecided row stays `proposed` (Q101's,
  `funding:F04`), its approved correction applied all the same. `funding:F02` keeps session
  2's state and review, and its decision notes this session's rows.
- **Corrections** are span-cited claims from the same page, each note naming the question
  and the product owner's decision; a value the review left unconfirmed is unknown with the
  review's reason, and a claim no record cites any more is left out.
- **UCAS's page (C12)** joins the pack, class `other`, excerpts only, under the product
  owner's rights decision (short quotes as evidence; its body is never kept).

Run from `backend/`: `uv run --locked python -m tools.school_leaver_review --out FILE`, then
publish FILE with `uv run --locked python -m tools.option_pack_files --pack FILE` and pin the
SHA-256 it prints. A fast test checks the committed version is exactly this tool's output.
"""

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal, cast

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
from tools.school_leaver_pack import package_rows
from tools.session_2_pack import Cite, Drop, MarkUnknown, NewClaim, _cited, _ranges

SOURCE_VERSION = "0.3.0"  # the version the school-leaver pack session reviewed
EARLIER_VERSION = "0.2.0"  # the version 0.3.0 added to: its sheet asks what changed since
VERSION = "0.4.0"
DATED = date(2026, 11, 1)
DECIDED_ON = date(2026, 11, 1)
RECORD_PATH = REPO_ROOT / "docs" / "reviews" / "school-leaver-pack-session.md"
SESSION = "the school-leaver pack session (2026-11-01)"
AI_REVIEWER = "an AI check, counted as the product owner's review by their ruling of 2026-11-01"
WITH_OWNER = f"{AI_REVIEWER}, and the product owner's own answers"
RULING = "AI check counts as my review"
OWNER_ANSWERS = "yes, fix 1-3, 4. no not fair, 5 yes, 6 yes"
UCAS_ROW_RECORD = "offering:C08"
RSQUO = chr(0x2019)

Verdict = Literal["yes", "no", "can't confirm"]
_ANSWER = re.compile(r"^- (Q[0-9]+): (yes|\*\*no\*\*|\*\*can't confirm\*\*)(.*)$")


@dataclass(frozen=True)
class Answer:
    question: str
    verdict: Verdict
    words: str  # the rest of the line, as written


def answers() -> dict[str, Answer]:
    """Every row's answer in the record's "Every row" list, by question."""
    text = RECORD_PATH.read_text(encoding="utf-8")
    for words in (RULING, OWNER_ANSWERS):
        if f'"{words}"' not in text:
            raise OptionPackError(f"the record does not hold the words {words!r}")
    found: dict[str, Answer] = {}
    for line in text.splitlines():
        match = _ANSWER.match(line)
        if match is None:
            continue
        question, verdict, rest = match.groups()
        if question in found:
            raise OptionPackError(f"{question} is answered twice")
        found[question] = Answer(question, cast(Verdict, verdict.strip("*")), rest.strip())
    return found


def record_rows(pack: Pack, before: Pack) -> dict[str, list[str]]:
    """Each record's rows on the 0.3.0 sheet, numbered as the sheet numbers them: Part 1,
    then the UCAS row, then Part 2."""
    first, rest = package_rows(pack, before)
    found: dict[str, list[str]] = {}
    for n, row in enumerate(first, start=1):
        found.setdefault(row.record_id, []).append(f"Q{n}")
    found[UCAS_ROW_RECORD] = [f"Q{len(first) + 1}"]
    for n, row in enumerate(rest, start=len(first) + 2):
        found.setdefault(row.record_id, []).append(f"Q{n}")
    return found


@dataclass(frozen=True)
class AddClaim:
    """A list field gains a span-cited claim."""

    field: str
    claim: NewClaim


@dataclass(frozen=True)
class SetSources:
    """An offering names a further page its new values come from."""

    source_ids: tuple[str, ...]

    @property
    def field(self) -> str:
        return "source_ids"


Edit = Cite | Drop | MarkUnknown | AddClaim | SetSources


@dataclass(frozen=True)
class Decision:
    """What one answer other than yes does to one record. `owner`: the product owner's own
    answer to the row (None: not sent back, so undecided)."""

    question: str
    record_id: str
    owner: str | None
    note: str
    edits: tuple[Edit, ...] = ()


def _session(question: str, owner: str) -> str:
    return (
        f"The school-leaver pack session, {question}: corrected by the product owner's answer "
        f"of 2026-11-01 ('{owner}')"
    )


F12_TOTAL_MAY_CHANGE = NewClaim(
    "F12.rates_change.tuition_total",
    "rules_change",
    "the £39,160 total is based on current rates and may change over time",
    56626,
    56820,
    "you can apply for Tuition Fee Loans up to a total amount of £39,160. This can be for a "
    "full course or split over multiple courses. This amount is based on current rates and may "
    "change over time.",
    1,
    f"{_session('Q75', 'yes, fix')}: the page says this only of the £39,160 Tuition Fee Loan "
    "total, not of every amount. In the page's own structured data (its FAQ holds the guide's "
    f"'What you{RSQUO}ll get' part).",
)
F04_NON_LEVY = NewClaim(
    "F04.employer_share.non_levy",
    "employer_share",
    "an employer that does not pay the apprenticeship levy pays 5% of training and assessment "
    "for all other apprentices",
    6006,
    6103,
    "For all other apprentices, you pay 5% towards the cost of training and assessing your "
    "apprentice.",
    2,
    f"{_session('Q104', 'yes, fix')}: 5% only under the heading 'If you do not pay the "
    "apprenticeship levy' (offsets 5570-5611); 'all other apprentices' are those outside the "
    "government's 100% (aged 16 to 24, or 15 with a late-summer birthday).",
)
F04_LEVY = NewClaim(
    "F04.employer_share.levy",
    "employer_share",
    "an employer that pays the apprenticeship levy and has used all its funds pays 25% towards "
    "the cost for all other apprentices",
    9187,
    9243,
    "For all other apprentices, you pay 25% towards the cost.",
    2,
    f"{_session('Q104', 'yes, fix')}: under the heading 'If you pay the apprenticeship levy' "
    f"(offsets 8652-8686), after 'If you{RSQUO}ve already used all your funds, the government "
    "will pay 100% of the cost of training and assessing an apprentice if they are:' (offsets "
    "8818-8950).",
)
C11_STARTED = NewClaim(
    "C11.started",
    "started",
    "T Levels started in September 2020",
    5245,
    5279,
    "T Levels started in September 2020",
    2,
    f"{_session('Q110', 'no, not fair')}: a past start, never a provider's next intake. In the "
    "page's own structured data (its FAQ, 'starting dates').",
)
C11_PROVIDERS = NewClaim(
    "C11.providers_listed",
    "providers_listed",
    "a published list of the providers offering T Level courses from September 2025",
    5454,
    5508,
    "providers offering T Level courses from September 2025",
    2,
    f"{_session('Q110', 'no, not fair')}: the page links 'a list of the providers offering T "
    "Level courses from September 2025'; it names none of them, and no provider's next start. "
    "In the page's own structured data (its FAQ, 'starting dates').",
)
# UCAS's dates page: its class, terms and fetch as the manifest records them (C12).
UCAS_SOURCE: dict[str, Any] = {
    "source_id": "C12",
    "kind": "course_page",
    "route": "fetch",
    "url": "https://www.ucas.com/applying/applying-to-university/dates-and-deadlines-for-uni-applications",
    "final_url": "https://www.ucas.com/applying/applying-to-university/dates-and-deadlines-for-uni-applications",
    "retrieved_at": "2026-11-01T18:42:21.152037Z",
    "http_status": 200,
    "content_type": "text/html",
    "sha256": "7f9d2e045146f204949de8e8d8c2bd1651921d639ac0ce8008019c36c103b996",
    "rights_class": "other",
    "rights_status": (
        "permitted: short quotes as evidence, never the body (the product owner's rights "
        "decision, 2026-11-01, the school-leaver pack session: 'Careerwright may keep short "
        "quotes from UCAS's page as evidence', answered '6 yes')"
    ),
    "retention": "excerpts",
    # Course group 8 by the split rule (C01 1, C02 2, C03 3, C07 4, C08 5, C09 6, C11 7).
    "template_family": "ucas-dates-and-deadlines",
    "split": "holdout",
}
C12_DEADLINE = NewClaim(
    "C12.application_deadline",
    "application_deadline",
    "2027-01-13",
    119808,
    120006,
    "13 Jan\n              </div>\n                                <h4 "
    'class="step-by-step-item__title">\n            (18:00 UK time) Equal consideration date '
    "for applications for most undergraduate courses",
    1,
    "The school-leaver pack session, Q115: 13 January 2027 by the product owner's answer of "
    "2026-11-01 ('5 yes'). The page shows '13 Jan' with no year, in its '2027 entry "
    "application deadlines' section (offsets 114524-114556), at 18:00 UK time; GOV.UK's "
    "student finance page (F12) names nursing among the full courses that can get priority "
    "additional entitlement (offsets 66326-66395 and 66458-66465).",
)
F04_TIMING_UNKNOWN = (
    "the school-leaver pack session, Q101 (can't confirm; not sent back): the page says the "
    "government pays the training provider directly only for the 95% share; it does not say "
    "who receives the 100% payment for an apprentice aged 16 to 24, or a levy payer's share"
)
C11_INTAKE_UNKNOWN = (
    "the school-leaver pack session, Q110 (the product owner: 'no, not fair'): no provider's "
    "next start is stated; the page states 'T Levels started in September 2020' (C11.started) "
    "and links a list of providers offering T Level courses 'from September 2025' "
    "(C11.providers_listed)"
)

DECISIONS: tuple[Decision, ...] = (
    Decision(
        "Q75",
        "funding:F12",
        "yes, fix",
        "only the £39,160 total may change: corrected",
        (Cite("facts", F12_TOTAL_MAY_CHANGE, replaces="F12.rates_change"),),
    ),
    Decision(
        "Q95",
        "funding:F12.maintenance",
        "yes, fix",
        "the page does not say the £15,415 may change: left out",
        (Drop("facts", "F12.rates_change"),),
    ),
    Decision(
        "Q101",
        "funding:F04",
        None,
        "not sent back: who the government pays beyond the 95% share stays unknown",
        (MarkUnknown("timing", F04_TIMING_UNKNOWN),),
    ),
    Decision(
        "Q104",
        "funding:F04",
        "yes, fix",
        "5% for an employer not paying the levy, 25% for a levy payer: corrected",
        (
            Cite("facts", F04_NON_LEVY, replaces="F04.employer_share"),
            AddClaim("facts", F04_LEVY),
        ),
    ),
    Decision(
        "Q110",
        "offering:C11",
        "no, not fair",
        "the start dates the page states are recorded; a provider's next start stays unknown",
        (
            MarkUnknown("intake", C11_INTAKE_UNKNOWN),
            AddClaim("facts", C11_STARTED),
            AddClaim("facts", C11_PROVIDERS),
        ),
    ),
    Decision(
        "Q115",
        "offering:C08",
        "yes",
        "applying by 13 January 2027 (UCAS's equal consideration date): recorded",
        (SetSources(("C12",)), Cite("application_deadline", C12_DEADLINE)),
    ),
)

NOTES = [
    "Version 0.4.0 publishes the school-leaver pack session's review (H-07, 2026-11-01) of "
    "version 0.3.0, applied by Task 7f with tools.school_leaver_review from the product owner's "
    "record (docs/reviews/school-leaver-pack-session.md). An AI checked all 139 rows, and the "
    "product owner ruled that its check counts as their review ('AI check counts as my "
    "review'); they answered the six rows sent back themselves ('yes, fix 1-3, 4. no not "
    "fair, 5 yes, 6 yes'). Versions 0.1.0, 0.2.0 and 0.3.0 are unchanged.",
    "A record new or changed in 0.3.0 is reviewed when every one of its rows was answered yes "
    "or corrected by the product owner's own answer. funding:F04 stays proposed: Q101 (who the "
    "government pays beyond the 95% share) was not decided, so its timing is unknown. "
    "funding:F02 keeps session 2's state and review. offering:C08 gains its UCAS deadline by "
    "the product owner's answer to Q115.",
    "UCAS's dates page (C12) is class other: the product owner allowed short quotes from it as "
    "evidence on 2026-11-01, so it keeps its hash and one excerpt; its body is never kept. "
    "Its '13 Jan' shows no year: 13 January 2027 is the product owner's reading, named in the "
    "claim's note.",
    "Still not in the pack, so no value is guessed: the apprentice's training fee "
    "(offering:C09) stays unknown, since the funding page (F04) names the government and the "
    "employer as payers but not what the apprentice pays.",
]
LABEL_REVIEW = (
    "the school-leaver pack session (H-07), 2026-11-01: the product owner's record, applied by "
    "Task 7f, for the records new or changed in 0.3.0 and offering:C08's deadline; the other "
    "records keep session 2's review (2026-10-29 to 2026-10-30); each record states its "
    "review_state and review"
)
RECORD_GROUPS = ("learning_options", "offerings", "funding_instruments")


def new_claims() -> list[NewClaim]:
    """Every corrected claim, once each, in decision order."""
    found: dict[str, NewClaim] = {}
    for decision in DECISIONS:
        for edit in decision.edits:
            if isinstance(edit, Cite | AddClaim):
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
    elif isinstance(edit, AddClaim):
        record[edit.field].append(edit.claim.claim_id)
    else:
        record["source_ids"] = list(edit.source_ids)


def _decision_text(rows: list[str], decisions: list[Decision], accepted: bool) -> str:
    if not accepted:
        head = "Stays proposed"
    elif decisions:
        head = "Accepted: every row yes or decided by the product owner"
    else:
        head = "Accepted: every row answered yes"
    found = [f"{head} ({_ranges(rows)})"]
    for d in decisions:
        said = f"the product owner: '{d.owner}'" if d.owner else "undecided"
        found.append(f"{d.question} ({said}): {d.note}")
    others = "The other rows" if decisions else "Rows"
    return "; ".join(found) + f". {others} checked by an AI, counted as their review."


def reviewed_pack(source: Pack | None = None, before: Pack | None = None) -> Pack:
    """Version 0.4.0: the record applied to 0.3.0, parsed and checked like any version."""
    pack = load_pack(SOURCE_VERSION) if source is None else source
    earlier = load_pack(EARLIER_VERSION) if before is None else before
    answered = answers()
    rows = record_rows(pack, earlier)
    asked = sorted({q for qs in rows.values() for q in qs}, key=lambda q: int(q[1:]))
    if asked != sorted(answered, key=lambda q: int(q[1:])):
        raise OptionPackError("the record's rows are not the sheet's rows")
    decided = {d.question for d in DECISIONS}
    open_rows = {q for q, a in answered.items() if a.verdict != "yes"}
    if open_rows != decided:
        raise OptionPackError(f"answers other than yes without a decision: {open_rows ^ decided}")
    data = pack.model_dump(mode="json")
    by_id = {r["record_id"]: r for group in RECORD_GROUPS for r in data[group]}
    on_record: dict[str, list[Decision]] = {}
    for decision in DECISIONS:
        on_record.setdefault(decision.record_id, []).append(decision)
        for edit in decision.edits:
            _apply(by_id[decision.record_id], edit)
    after_c11 = max(i for i, s in enumerate(data["sources"]) if s["source_id"][0] == "C")
    data["sources"].insert(after_c11 + 1, UCAS_SOURCE)
    claims: list[dict[str, Any]] = data["claims"]
    for claim in new_claims():
        source_id = claim.claim_id.split(".")[0]
        kind = source_id if source_id in {c["source_id"] for c in claims} else source_id[0]
        last = max(i for i, c in enumerate(claims) if c["source_id"].startswith(kind))
        claims.insert(last + 1, claim.as_claim())
    groups = ("job_postings", "skill_requirements", "outcomes", *RECORD_GROUPS)
    cited = {v for group in groups for r in data[group] for v in _cited(r)}
    data["claims"] = [c for c in claims if c["claim_id"] in cited]
    for record_id, questions in rows.items():
        record = by_id[record_id]
        decisions = on_record.get(record_id, [])
        if record_id == "funding:F02":  # session 2 left it proposed; it keeps that review
            review = record["review"]
            review["decision"] += (
                f" The school-leaver pack session (2026-11-01): {_ranges(questions)} yes."
            )
            continue
        accepted = all(d.owner is not None for d in decisions)
        owner_rows = any(d.owner for d in decisions)
        record["review_state"] = (ReviewState.REVIEWED if accepted else ReviewState.PROPOSED).value
        if record_id == UCAS_ROW_RECORD:
            record["review"] = {
                "reviewer": "the product owner",
                "decided_on": DECIDED_ON.isoformat(),
                "session": "session 2; the school-leaver pack session (2026-11-01)",
                "decision": (
                    "Accepted: session 2's rows (Q119-Q126) yes, checked by an AI, adopted by the "
                    "product owner's ruling of 2026-10-30; the school-leaver pack session, Q115 "
                    "(the product owner: '5 yes'): applying by 13 January 2027 (UCAS's equal "
                    "consideration date for most undergraduate courses), recorded."
                ),
            }
            continue
        record["review"] = {
            "reviewer": WITH_OWNER if owner_rows else AI_REVIEWER,
            "decided_on": DECIDED_ON.isoformat(),
            "session": SESSION,
            "decision": _decision_text(questions, decisions, accepted),
        }
    data.update(
        pack_version=VERSION,
        dated=DATED.isoformat(),
        label_review=LABEL_REVIEW,
        # 0.3.0's notes but its first (now history) and its "not in 0.3.0" (now settled).
        notes=[*NOTES, *pack.notes[1:3], *pack.notes[4:]],
    )
    reviewed = parse_pack(data)
    problems = check_pack(reviewed)
    if problems:
        raise OptionPackError(f"the reviewed pack fails its checks: {'; '.join(problems)}")
    return reviewed


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="where to write the candidate")
    args = parser.parse_args(argv)
    args.out.write_text(dump_pack(reviewed_pack()), encoding="utf-8")
    print(f"wrote {args.out}\npublish it with: python -m tools.option_pack_files --pack {args.out}")


if __name__ == "__main__":
    main()
