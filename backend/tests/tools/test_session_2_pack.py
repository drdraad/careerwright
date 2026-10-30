"""The reviewed England option pack (Task 7c; ADR 0011 decision 15): session 2's record (H-07)
applied to version 0.1.0 under the partial-record rule. Every reviewed record traces to rows
the record answered yes, every other answer is applied or recorded, every changed value is
span-cited, nothing is left out, and 0.1.0 is unchanged."""

import hashlib
import json
from datetime import date
from typing import Any

import pytest

from careerwright.capability.matrix import build_matrix
from careerwright.capability.outcomes import pack_outcomes
from careerwright.capability.reference import GateKind, load_reference
from careerwright.catalogue.option_pack import (
    PINS,
    ReviewState,
    Unknown,
    check_pack,
    dump_pack,
    load_pack,
    pack_path,
)
from careerwright.planning.pack import pack_catalogue
from tools.corpus import locate
from tools.localenv import REPO_ROOT
from tools.session_2_pack import (
    DECISIONS,
    REVIEWER,
    SOURCE_VERSION,
    VERSION,
    Assign,
    Cite,
    Drop,
    MarkUnknown,
    answers,
    new_claims,
    outcome_rubrics,
    record_rows,
    reviewed_pack,
)

SOURCE = load_pack(SOURCE_VERSION)
REVIEWED = load_pack(VERSION)
ANSWERS = answers()
ROWS = record_rows(SOURCE)
EVIDENCE = REPO_ROOT / "var" / "evidence" / "corpus"
MANIFEST = REPO_ROOT / "corpus" / "manifest.json"
FROZEN_0_1_0 = "d7ff17d73a9b17b43529b5cbbe4349ef016f7268c4ac4c2a6a53a13f97e6a3d3"
# UK-regulated roles among the pack's targets, with the gate that types each (the regulated
# professions register; R37), whatever ESCO's own flag says (Task 9 re-review 1, N7).
REGULATED = {"registered-nurse-manchester": "nmc-registration"}


def records() -> dict[str, Any]:
    return {r.record_id: r for r in REVIEWED.records()}


def changed() -> set[str]:
    return {d.record_id for d in DECISIONS if d.edits}


@pytest.mark.req("OPTN-10")
def test_the_record_holds_one_answer_for_every_question_with_its_provenance() -> None:
    expected = {
        *(f"Q{n}" for n in range(1, 345)),
        *(f"T{n}" for n in range(1, 37)),
        *(f"R{n}" for n in range(1, 59)),
    }

    assert set(ANSWERS) == expected
    assert {a.verdict for a in ANSWERS.values()} == {"yes", "no", "?"}
    # Q1-Q15 are the product owner's own; the rest an AI's check, adopted by their ruling.
    assert {q for q, a in ANSWERS.items() if not a.by_ai} == {f"Q{n}" for n in range(1, 16)}
    assert ANSWERS["Q23"].verdict == "no"
    assert "isAgency" in ANSWERS["Q23"].words
    assert ANSWERS["Q227"].verdict == "?"
    assert ANSWERS["Q227"].words == ""  # a bare "?": undecided
    assert ANSWERS["Q290"].verdict == "?"
    assert "current UK professional" in ANSWERS["Q290"].words


@pytest.mark.req("OPTN-10", "TEST1-09")
def test_every_row_that_states_a_record_s_value_names_that_record() -> None:
    named = {q for rows in ROWS.values() for q in rows}
    ids = {r.record_id for r in SOURCE.records()}

    assert set(ROWS) <= ids
    assert {f"Q{n}" for n in range(1, 345)} <= named  # every fact row is a record's
    assert {f"R{n}" for n in range(41, 59)} <= named  # the proposed outcome levels
    assert {f"T{n}" for n in (*range(11, 28), *range(32, 37))} <= named
    # The fixture person (T1-T10), the checker's conclusions (T28-T31) and the capability
    # reference (R1-R40) are not pack records.
    assert not named & {f"T{n}" for n in (*range(1, 11), *range(28, 32))}
    assert not named & {f"R{n}" for n in range(1, 41)}
    assert ROWS["offering:C01"][:2] == ["Q39", "Q40"]
    assert "T12" in ROWS["offering:C01"]  # the full-time variant's duration


@pytest.mark.req("OPTN-10")
def test_the_committed_version_is_the_record_applied_to_0_1_0() -> None:
    assert pack_path(VERSION).read_text(encoding="utf-8") == dump_pack(reviewed_pack(SOURCE))
    assert check_pack(REVIEWED) == []
    assert REVIEWED.dated == date(2026, 10, 30)
    assert REVIEWED.label_review.startswith("session 2 (H-07)")


@pytest.mark.req("OPTN-10")
def test_version_0_1_0_is_unchanged_and_keeps_its_pin() -> None:
    data = pack_path(SOURCE_VERSION).read_bytes()

    assert hashlib.sha256(data).hexdigest() == PINS[SOURCE_VERSION] == FROZEN_0_1_0
    assert {r.review_state for r in SOURCE.records()} == {ReviewState.PROPOSED}


@pytest.mark.req("OPTN-10")
def test_no_record_is_left_out() -> None:
    # Every row asked whether a value is right as the page states it; no answer rejects a
    # whole record, so the reviewed version keeps every record.
    assert [r.record_id for r in REVIEWED.records()] == [r.record_id for r in SOURCE.records()]


@pytest.mark.req("OPTN-10", "TEST1-09", "OUT1-10")
def test_a_record_is_reviewed_only_when_every_row_about_it_is_yes_and_nothing_changed() -> None:
    edited = changed()
    for record in REVIEWED.records():
        rows = ROWS.get(record.record_id, [])
        if record.review_state is ReviewState.REVIEWED:
            assert rows, record.record_id
            assert all(ANSWERS[q].verdict == "yes" for q in rows), record.record_id
            assert record.record_id not in edited
        elif rows:
            undecided = any(ANSWERS[q].verdict != "yes" for q in rows)
            assert undecided or record.record_id in edited, record.record_id
        if not rows:
            assert record.review_state is ReviewState.PROPOSED
            assert record.review is None, record.record_id  # nobody decided it
            continue
        assert record.review is not None
        assert record.review.reviewer == REVIEWER
        assert record.review.session.startswith("session 2")
        own = all(not ANSWERS[q].by_ai for q in rows)
        assert record.review.decided_on == date(2026, 10, 29 if own else 30)
        decision = record.review.decision
        assert all(q in decision for q in rows if ANSWERS[q].verdict != "yes"), decision
        assert ("checked by an AI" in decision) != own, decision


@pytest.mark.req("OPTN-10")
def test_every_answer_other_than_yes_is_applied_or_recorded_and_none_is_invented() -> None:
    named = {q for rows in ROWS.values() for q in rows}
    decided = {d.question for d in DECISIONS}
    needs_decision = {
        q
        for q in named
        if ANSWERS[q].verdict == "no" or (ANSWERS[q].verdict == "?" and ANSWERS[q].words)
    }
    undecided = {q for q in named if ANSWERS[q].verdict == "?" and not ANSWERS[q].words}

    assert decided == needs_decision
    assert not decided & undecided  # a bare "?" leaves its record undecided, values as they were
    for decision in DECISIONS:
        own = [r for r, rows in ROWS.items() if decision.question in rows]
        assert own, decision.question
        source = decision.record_id.split(":")[1][:3]
        # A decision changes the record its row names, or a record of the same page.
        assert decision.record_id in own or any(source in r for r in own), decision


@pytest.mark.req("OPTN-10", "OUT1-10")
def test_every_changed_value_cites_its_span_on_the_same_page() -> None:
    added = {c.claim_id for c in REVIEWED.claims} - {c.claim_id for c in SOURCE.claims}
    corrections = new_claims()

    assert added == {c.claim_id for c in corrections}
    for claim in corrections:
        cited = REVIEWED.claim(claim.claim_id)
        assert cited.note is not None
        assert "Session 2 correction" in cited.note
        assert (cited.span.start, cited.span.end) == (claim.start, claim.end)
        assert cited.excerpt == claim.excerpt
        if claim.within is not None:
            stored = SOURCE.claim(claim.within)
            assert stored.source_id == cited.source_id
            assert stored.span.start is not None
            assert stored.span.end is not None
            offset = claim.start - stored.span.start
            assert stored.excerpt[offset : offset + len(claim.excerpt)] == claim.excerpt
            assert claim.end <= stored.span.end


@pytest.mark.req("OPTN-10", "OUT1-10")
@pytest.mark.parametrize("claim", [c for c in new_claims() if c.within is None], ids=str)
def test_a_correction_located_in_a_kept_body_is_exactly_its_text_there(claim: object) -> None:
    from tools.session_2_pack import NewClaim

    assert isinstance(claim, NewClaim)
    source = next(s for s in SOURCE.sources if s.source_id == claim.claim_id[:3])
    body = EVIDENCE / source.source_id / f"{source.sha256}.html"
    if not body.is_file():
        pytest.skip(f"{source.source_id}'s body is kept only on the curating machine")
    text = body.read_bytes()
    assert hashlib.sha256(text).hexdigest() == source.sha256
    page = text.decode()
    [found] = locate(page, [claim.excerpt])

    offsets = found["offsets"]
    assert page[claim.start : claim.end] == claim.excerpt
    assert found["count"] == claim.occurrences
    assert isinstance(offsets, list)
    assert offsets[0] == [claim.start, claim.end]  # the first occurrence, as Task 7b's spans


@pytest.mark.req("OPTN-10")
def test_a_value_the_reviewer_called_wrong_is_no_longer_served() -> None:
    by_id = records()
    claims = {c.claim_id for c in REVIEWED.claims}
    for decision in DECISIONS:
        record = by_id[decision.record_id]
        for edit in decision.edits:
            value = getattr(record, edit.field)
            if isinstance(edit, MarkUnknown):
                assert isinstance(value, Unknown)
                assert value.unknown.startswith(f"session 2, {decision.question}")
            elif isinstance(edit, Drop):
                assert edit.claim_id not in value
                assert edit.claim_id not in claims  # never kept as a fact either
            elif isinstance(edit, Cite):
                assert edit.claim.claim_id == value or edit.claim.claim_id in value
                if edit.replaces is not None:
                    assert edit.replaces not in claims
            elif isinstance(edit, Assign):
                assert value == edit.value


@pytest.mark.req("OPTN-10", "OUT1-10")
def test_the_reviewed_values_read_as_the_reviewer_stated_them() -> None:
    by_id = records()
    pack = REVIEWED

    # Q56: one year of access, not "up to" a year.
    assert pack.claim("C04.access_period.corrected").value == [
        {"unit": "years", "minimum": 1, "maximum": 1, "mode": None}
        | {"typical": False, "unbounded": False}
    ]
    # Q198, Q199: the page's own metadata dates.
    assert pack.value(by_id["funding:F02"].published_on) == "2016-05-16"
    assert pack.value(by_id["funding:F02"].rules_updated_on) == "2024-10-14"
    # Q23, Q223, Q224: an agency the stored excerpts cannot cite stays unknown, never guessed.
    assert isinstance(by_id["job:J18"].advertiser, Unknown)
    assert isinstance(by_id["job:J01"].employer, Unknown)
    # Q25: querying is one of several alternatives, so its importance is not known.
    assert by_id["req:J18.1"].importance == "unknown"
    # Q53 and Q153: the kinds the pages state; Q95-Q96 and Q167: support not established.
    assert by_id["outcome:C01.3"].evidence_kind == "practice"
    assert by_id["outcome:C05.1"].evidence_kind == "exam"
    for outcome_id in ("outcome:C10.1", "outcome:C10.2", "outcome:C06.2"):
        assert by_id[outcome_id].confidence == "unsupported"
    # Q187, Q38, Q269, Q298: a reading the field's shape cannot hold is left out.
    assert "F01.rule_earnings" not in by_id["funding:F01"].rules
    assert "C01.guided_hours" not in by_id["option:C01"].facts
    assert "J06.occupation_crosswalk" not in by_id["job:J06"].facts


@pytest.mark.req("OUT1-10")
def test_no_outcome_has_a_level_and_each_reviewed_one_names_its_rubric() -> None:
    # Session 2 accepted no proposed level: the only two numbers, C06's (R50, R51), were no.
    rubrics = outcome_rubrics()

    assert ANSWERS["R50"].verdict == ANSWERS["R51"].verdict == "no"
    assert all(o.level_on_completion is None for o in REVIEWED.outcomes)
    reviewed = [o for o in REVIEWED.outcomes if o.review_state is ReviewState.REVIEWED]
    assert {o.record_id for o in reviewed} == {
        "outcome:C02.1",
        "outcome:C04.1",
        "outcome:C04.2",
        "outcome:C09.1",
        "outcome:C09.2",
    }
    for outcome in REVIEWED.outcomes:
        expected = rubrics[outcome.record_id] if outcome in reviewed else None
        assert outcome.rubric_version == expected, outcome.record_id


@pytest.mark.req("TEST1-09", "OPTN-10")
def test_the_corpus_manifest_records_the_reviewed_version_and_each_page_s_review() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    slots = {s["id"]: s for s in manifest["slots"]}
    by_slot: dict[str, list[str]] = {}
    for c in REVIEWED.claims:
        by_slot.setdefault(c.source_id, []).append(c.claim_id)
    states = {r.record_id: r.review_state for r in REVIEWED.records()}

    assert manifest["option_pack"]["version"] == VERSION
    assert manifest["option_pack"]["sha256"] == PINS[VERSION]
    assert manifest["option_pack"]["path"].endswith(pack_path(VERSION).name)
    for source in REVIEWED.sources:
        slot = slots[source.source_id]
        assert slot["labels"]["in"] == pack_path(VERSION).name
        assert slot["labels"]["claims"] == by_slot[source.source_id], source.source_id
        reviewed = sum(states[r] is ReviewState.REVIEWED for r in slot["pack_records"])
        words = f"{reviewed} of {len(slot['pack_records'])} records reviewed"
        assert slot["label_review"].startswith("session 2"), source.source_id
        assert words in slot["label_review"], (source.source_id, words)


@pytest.mark.req("OPTN-10", "TEST1-13", "OPT1-16")
def test_the_reviewed_version_loads_with_its_capability_reference_for_every_consumer() -> None:
    reference = load_reference(VERSION, REVIEWED)

    assert reference.pack_version == VERSION
    assert reference.review_state == "proposed"  # its no and ? answers (R6-R38) are open
    assert len(pack_outcomes(REVIEWED, reference)) == len(REVIEWED.outcomes)
    for target in REVIEWED.targets:
        matrix = build_matrix(
            target.title,
            pack=REVIEWED,
            reference=reference,
            pack_target=target,
            occupation=None,
            exemplars=0,
            synthetic=False,
        )
        assert matrix.rows, target.target_id
        catalogue = pack_catalogue(REVIEWED, target.target_id)
        assert catalogue.label.name == f"nessa-england-option-pack {VERSION}"


@pytest.mark.req("OPTN-10")
def test_every_uk_regulated_role_in_the_reviewed_pack_has_its_protected_gate_typed() -> None:
    reference = load_reference(VERSION, REVIEWED)
    for target_id, gate_key in REGULATED.items():
        rows = [s.skill_id for s in REVIEWED.skills if s.target_id == target_id]
        gates = [reference.gate_for_row(row) for row in rows]
        typed = [g for g in gates if g is not None and g.gate_key == gate_key]

        assert typed, target_id
        assert typed[0].kind is GateKind.LEGAL_PRACTICE


@pytest.mark.req("OPTN-10")
def test_each_decision_answers_a_question_in_a_few_words_a_review_record_can_hold() -> None:
    for decision in DECISIONS:
        assert decision.question in ANSWERS
        assert 0 < len(decision.note) <= 160, decision.question
