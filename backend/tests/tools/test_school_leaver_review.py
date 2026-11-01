"""The England option pack 0.4.0: the school-leaver pack session's review of 0.3.0 (Task 7f's
second half). The committed version is the tool's output from the product owner's record;
every reviewed record traces to its rows; each correction is span-cited with the decision
named; an undecided row keeps its record proposed; the earlier versions are unchanged."""

import hashlib
import json
from typing import Any

import pytest

from careerwright.catalogue.option_pack import (
    PINS,
    Offering,
    ReviewState,
    Unknown,
    dump_pack,
    load_pack,
    pack_path,
)
from tools.corpus import locate
from tools.localenv import REPO_ROOT
from tools.school_leaver_review import (
    AI_REVIEWER,
    DECISIONS,
    EARLIER_VERSION,
    SOURCE_VERSION,
    VERSION,
    answers,
    new_claims,
    record_rows,
    reviewed_pack,
)

PACK = load_pack(VERSION)
REVIEWED = load_pack(SOURCE_VERSION)
EARLIER = load_pack(EARLIER_VERSION)
ROWS = record_rows(REVIEWED, EARLIER)
ANSWERS = answers()
EVIDENCE = REPO_ROOT / "var" / "evidence" / "corpus"
MANIFEST = REPO_ROOT / "corpus" / "manifest.json"
C12_FETCHES = [
    REPO_ROOT / "planning" / "task-7f-fetch-output-c12.json",
    REPO_ROOT / "planning" / "task-7f-fetch-output-c12-date.json",
]
SESSION_RECORDS = {
    "funding:F04",
    "funding:F05",
    "funding:F05.maintenance",
    "funding:F10",
    "funding:F12",
    "funding:F12.maintenance",
    "option:C11",
    "offering:C11",
}


def _records(pack: Any) -> dict[str, Any]:
    return {r.record_id: r for r in pack.records()}


@pytest.mark.req("OPTN-14", "OPTN-10")
def test_the_committed_version_is_the_tool_s_output_and_pinned() -> None:
    text = pack_path(VERSION).read_text(encoding="utf-8")

    assert dump_pack(reviewed_pack()) == text
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == PINS[VERSION]


@pytest.mark.req("OPTN-14", "OPTN-10")
def test_the_earlier_versions_are_unchanged() -> None:
    assert PINS["0.1.0"] == "d7ff17d73a9b17b43529b5cbbe4349ef016f7268c4ac4c2a6a53a13f97e6a3d3"
    assert PINS["0.2.0"] == "162d2773e295c7832ff3b311738bdd20d111538b15f1df49932fecfc82702a56"
    assert PINS["0.3.0"] == "b1167ff506c00b59821dfc8d122d66e3767c3e59e41a0e58c3d151329169f284"
    for version in ("0.1.0", "0.2.0", "0.3.0"):
        load_pack(version)  # its bytes are its pin


@pytest.mark.req("OPTN-14")
def test_the_record_answers_every_row_of_the_sheet_once() -> None:
    asked = sorted((q for qs in ROWS.values() for q in qs), key=lambda q: int(q[1:]))

    assert asked == [f"Q{n}" for n in range(1, 140)]
    assert sorted(ANSWERS, key=lambda q: int(q[1:])) == asked
    open_rows = {q: a.verdict for q, a in ANSWERS.items() if a.verdict != "yes"}
    assert open_rows == {
        "Q75": "no",
        "Q95": "no",
        "Q101": "can't confirm",
        "Q104": "no",
        "Q110": "can't confirm",
        "Q115": "can't confirm",
    }
    assert {d.question for d in DECISIONS} == set(open_rows)
    assert ROWS["offering:C08"] == ["Q115"]  # the UCAS row
    # Only Q101 was not sent back; the other five are the product owner's own answers.
    assert {d.question for d in DECISIONS if d.owner is None} == {"Q101"}


@pytest.mark.req("OPTN-14")
def test_a_record_is_reviewed_only_when_every_row_is_yes_or_decided_by_the_product_owner() -> None:
    records = _records(PACK)
    undecided = {d.record_id for d in DECISIONS if d.owner is None}

    for record_id in SESSION_RECORDS:
        record = records[record_id]
        assert record.review is not None
        assert record.review.session == "the school-leaver pack session (2026-11-01)"
        assert record.review.decided_on.isoformat() == "2026-11-01"
        assert record.review.reviewer.startswith(AI_REVIEWER)
        reviewed = record_id not in undecided
        assert (record.review_state is ReviewState.REVIEWED) == reviewed, record_id
        for question in ROWS[record_id]:
            decided = [d for d in DECISIONS if d.question == question]
            assert ANSWERS[question].verdict == "yes" or decided, question
            assert all(d.record_id == record_id for d in decided)
    assert records["funding:F04"].review_state is ReviewState.PROPOSED  # Q101 undecided
    assert "Q101 (undecided)" in records["funding:F04"].review.decision
    # No answer rejected a whole record: every record of 0.3.0 is still in it.
    assert set(records) == set(_records(REVIEWED))


@pytest.mark.req("OPTN-14")
def test_the_learner_loan_keeps_session_2_s_state_and_notes_this_session_s_rows() -> None:
    before = _records(REVIEWED)["funding:F02"]
    after = _records(PACK)["funding:F02"]

    assert after.review_state is ReviewState.PROPOSED
    assert after.review is not None
    assert before.review is not None
    assert after.review.decision.startswith(before.review.decision)
    assert after.review.decision.endswith(
        "The school-leaver pack session (2026-11-01): Q1-Q8, Q116 yes."
    )
    assert all(ANSWERS[q].verdict == "yes" for q in ROWS["funding:F02"])
    assert after.model_dump(exclude={"review"}) == before.model_dump(exclude={"review"})


@pytest.mark.req("OPTN-14", "OPTN-10")
def test_nothing_else_changed() -> None:
    before = _records(REVIEWED)
    changed = {rid for rid, r in _records(PACK).items() if before[rid] != r}

    assert changed == SESSION_RECORDS | {"funding:F02", "offering:C08"}
    sources = {s.source_id: s for s in REVIEWED.sources}
    assert all(sources[s.source_id] == s for s in PACK.sources if s.source_id in sources)
    assert {s.source_id for s in PACK.sources} - set(sources) == {"C12"}


@pytest.mark.req("OPTN-14")
def test_the_corrections_say_what_the_product_owner_approved() -> None:
    funds = {f.record_id: f for f in PACK.funding_instruments}
    offerings = {o.record_id: o for o in PACK.offerings}

    # Q75: only the £39,160 total may change; Q95: nothing says the £15,415 may.
    assert "F12.rates_change.tuition_total" in funds["funding:F12"].facts
    total_may_change = PACK.claim("F12.rates_change.tuition_total")
    assert "£39,160" in total_may_change.excerpt
    assert "may change over time" in total_may_change.excerpt
    assert not [c for c in funds["funding:F12.maintenance"].facts if "rates_change" in c]
    assert "F12.rates_change" not in {c.claim_id for c in PACK.claims}
    # Q104: 5% for an employer that does not pay the levy, 25% for one that does.
    apprenticeship = funds["funding:F04"]
    shares = [PACK.claim(c) for c in apprenticeship.facts if c.startswith("F04.employer_share")]
    assert [s.claim_id for s in shares] == [
        "F04.employer_share.non_levy",
        "F04.employer_share.levy",
    ]
    assert "does not pay the apprenticeship levy pays 5%" in str(shares[0].value)
    assert "pays the apprenticeship levy and has used all its funds pays 25%" in str(
        shares[1].value
    )
    assert "25%" in shares[1].excerpt
    # Q101 (undecided): who the government pays beyond the 95% share is unknown.
    assert isinstance(apprenticeship.timing, Unknown)
    assert "Q101" in apprenticeship.timing.unknown
    assert "95%" in apprenticeship.timing.unknown
    # Q110: the start dates the page states; a provider's next start stays unknown.
    t_level = offerings["offering:C11"]
    assert isinstance(t_level.intake, Unknown)
    assert "next start is stated" in t_level.intake.unknown
    assert t_level.facts == ["C11.started", "C11.providers_listed"]
    assert PACK.claim("C11.started").value == "T Levels started in September 2020"
    assert "from September 2025" in PACK.claim("C11.providers_listed").excerpt
    # Each correction's note names its question and the product owner's answer.
    for claim in new_claims():
        assert "The school-leaver pack session, Q" in claim.note
        assert "the product owner's answer of 2026-11-01" in claim.note


@pytest.mark.req("OPTN-14")
def test_the_nursing_degree_applies_by_13_january_2027_citing_ucas() -> None:
    offering = next(o for o in PACK.offerings if o.record_id == "offering:C08")
    assert isinstance(offering, Offering)
    deadline = PACK.claim("C12.application_deadline")
    ucas = next(s for s in PACK.sources if s.source_id == "C12")

    assert offering.application_deadline == "C12.application_deadline"
    assert offering.source_ids == ["C12"]
    assert offering.review_state is ReviewState.REVIEWED
    assert offering.review is not None
    assert "Q115" in offering.review.decision
    assert deadline.value == "2027-01-13"
    assert deadline.excerpt.startswith("13 Jan")
    assert deadline.excerpt.endswith(
        "Equal consideration date for applications for most undergraduate courses"
    )
    assert (deadline.span.start, deadline.span.end) == (119808, 119808 + len(deadline.excerpt))
    assert "'5 yes'" in str(deadline.note)
    assert "nursing" in str(deadline.note)
    # UCAS's rights: class other, short quotes by the product owner's decision, no body.
    assert ucas.rights_class.value == "other"
    assert ucas.retention.value == "excerpts"
    assert ucas.rights_status.startswith("permitted: short quotes as evidence, never the body")
    assert [c.claim_id for c in PACK.claims if c.source_id == "C12"] == [deadline.claim_id]


def _located_text(paths: list[Any]) -> dict[int, str]:
    """The hashed page's characters the controller's C12 fetches located, by offset."""
    text: dict[int, str] = {}
    for path in paths:
        for fetch in json.loads(path.read_text(encoding="utf-8")):
            assert (
                fetch["sha256"]
                == "7f9d2e045146f204949de8e8d8c2bd1651921d639ac0ce8008019c36c103b996"
            )
            for located in fetch["located"]:
                for start, end, context in located["contexts"]:
                    assert end - start == len(context)
                    for i, ch in enumerate(context):
                        assert text.setdefault(start + i, ch) == ch
    return text


@pytest.mark.req("OPTN-14", "TEST1-09")
def test_the_ucas_excerpt_and_its_section_are_the_page_s_located_text() -> None:
    if not all(p.is_file() for p in C12_FETCHES):
        pytest.skip("the controller's C12 fetch records have moved")
    text = _located_text(C12_FETCHES)
    deadline = PACK.claim("C12.application_deadline")
    start, end = deadline.span.start, deadline.span.end
    assert start is not None
    assert end is not None

    assert "".join(text[i] for i in range(start, end)) == deadline.excerpt
    assert "".join(text[i] for i in range(114524, 114556)) == "2027 entry application deadlines"


@pytest.mark.req("OPTN-14", "TEST1-09")
@pytest.mark.parametrize("claim", new_claims(), ids=lambda c: c.claim_id)
def test_a_correction_is_exactly_its_text_in_the_kept_body(claim: Any) -> None:
    source = next(s for s in PACK.sources if s.source_id == claim.claim_id.split(".")[0])
    if source.retention.value != "body":
        pytest.skip(f"{source.source_id} keeps no body (checked against its located text)")
    body = EVIDENCE / source.source_id / f"{source.sha256}.html"
    if not body.is_file():
        pytest.skip(f"{source.source_id}'s body is kept only on the curating machine (R3)")
    page = body.read_text(encoding="utf-8")
    [found] = locate(page, [claim.excerpt])

    assert page[claim.start : claim.end] == claim.excerpt
    assert found["count"] == claim.occurrences
    assert found["offsets"][0] == [claim.start, claim.end]  # type: ignore[index]


# The words each note cites by offset, on the same page or (for C12's) on F12.
NOTE_SPANS = [
    ("F04", 5570, 5611, "If you do not pay the apprenticeship levy"),
    ("F04", 8652, 8686, "If you pay the apprenticeship levy"),
    ("F04", 8818, 8950, f"If you{chr(0x2019)}ve already used all your funds, the government will"),
    ("F12", 66326, 66395, "You can only get priority additional entitlement for full courses in:"),
    ("F12", 66458, 66465, "nursing"),
]


@pytest.mark.req("OPTN-14")
@pytest.mark.parametrize(("source_id", "start", "end", "words"), NOTE_SPANS)
def test_the_spans_a_note_cites_hold_its_words(
    source_id: str, start: int, end: int, words: str
) -> None:
    source = next(s for s in PACK.sources if s.source_id == source_id)
    body = EVIDENCE / source_id / f"{source.sha256}.html"
    if not body.is_file():
        pytest.skip(f"{source_id}'s body is kept only on the curating machine (R3)")

    assert body.read_text(encoding="utf-8")[start:end].startswith(words)


@pytest.mark.req("OPTN-14", "TEST1-09")
def test_the_manifest_records_the_reviewed_version_and_ucas_s_rights() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    slots = {s["id"]: s for s in manifest["slots"]}
    items = {i["id"]: i for i in manifest["open_items"]}

    assert manifest["option_pack"]["version"] == VERSION
    assert manifest["option_pack"]["sha256"] == PINS[VERSION]
    assert manifest["pending_slots"] == []
    assert slots["C12"]["rights_status"] == next(
        s.rights_status for s in PACK.sources if s.source_id == "C12"
    )
    assert slots["C12"]["pack_records"] == ["offering:C08"]
    assert "C12 (UCAS's dates page, class other) is decided" in items["OI-07"]["disposition"]
    assert "UCAS deadline settled" in items["OI-14"]["status"]
