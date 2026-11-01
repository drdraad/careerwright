"""The England option pack 0.3.0: 0.2.0 with the school-leaver pages (Task 7f). The committed
version and the session's package are the tool's output; every new or changed record is
proposed and span-cited; nothing else changed; and nothing is guessed for the two pages that
did not state their value."""

import hashlib
import json
from datetime import date
from typing import Any

import pytest

from careerwright.catalogue.option_pack import (
    PINS,
    FundingInstrument,
    ReviewState,
    Unknown,
    dump_pack,
    load_pack,
    pack_path,
)
from tools.corpus import locate
from tools.localenv import REPO_ROOT
from tools.school_leaver_pack import (
    PACKAGE_PATH,
    SOURCE_VERSION,
    VERSION,
    changed_records,
    labels,
    package_rows,
    review_package,
    school_leaver_pack,
)

BEFORE = load_pack(SOURCE_VERSION)
PACK = load_pack(VERSION)
LABELS = labels()
NEW_SOURCES = {s["source_id"] for s in LABELS["sources"]}
EVIDENCE = REPO_ROOT / "var" / "evidence" / "corpus"
MANIFEST = REPO_ROOT / "corpus" / "manifest.json"
NEW_RECORDS = {
    "funding:F04",
    "funding:F05",
    "funding:F05.maintenance",
    "funding:F10",
    "funding:F12",
    "funding:F12.maintenance",
    "option:C11",
    "offering:C11",
}


@pytest.mark.req("OPTN-14", "OPTN-10")
def test_the_committed_version_is_the_tool_s_output_and_pinned() -> None:
    text = pack_path(VERSION).read_text(encoding="utf-8")

    assert dump_pack(school_leaver_pack()) == text
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == PINS[VERSION]


@pytest.mark.req("OPTN-14", "OPTN-10")
def test_only_the_school_leaver_records_are_new_or_changed_and_each_is_proposed() -> None:
    before = {r.record_id: r for r in BEFORE.records()}
    after = {r.record_id: r for r in PACK.records()}

    assert set(changed_records(PACK, BEFORE)) == NEW_RECORDS | {"funding:F02"}
    assert set(before) < set(after)  # nothing left out
    for record_id in NEW_RECORDS:
        record = after[record_id]
        assert record.review_state is ReviewState.PROPOSED
        assert record.review is None  # nobody has decided it
        assert record.as_of == date(2026, 11, 1)
    learner_loan = after["funding:F02"]
    assert learner_loan.review_state is ReviewState.PROPOSED
    assert learner_loan.review == before["funding:F02"].review  # session 2's, as given
    assert {s.source_id for s in BEFORE.sources} | NEW_SOURCES == {
        s.source_id for s in PACK.sources
    }


@pytest.mark.req("OPTN-14")
def test_the_loans_say_how_they_are_paid_and_repaid_and_who_qualifies() -> None:
    funds = {f.record_id: f for f in PACK.funding_instruments}
    tuition, living = funds["funding:F05"], funds["funding:F05.maintenance"]
    learner_loan, bursary = funds["funding:F02"], funds["funding:F10"]

    assert "paid directly to the university or college" in str(PACK.value(tuition.timing))
    assert "bank account at the start of each term" in str(PACK.value(living.timing))
    assert "paid directly to the college or training provider" in str(
        PACK.value(learner_loan.timing)
    )
    assert "threshold" in str(PACK.value(learner_loan.repayment))
    for loan in (tuition, living):
        assert loan.instrument_kind == "loan"
        assert "9% of income" in str(PACK.value(loan.repayment))
        fields = {PACK.claim(c).field for c in loan.rules}
        assert {"rule_age_limit", "rule_residency"} <= fields
    assert bursary.instrument_kind == "grant"
    assert PACK.value("F11.rule_age") == {"minimum_age": 16, "on": "31 August 2026"}
    assert isinstance(bursary.repayment, Unknown)  # the pages do not say: never assumed


@pytest.mark.req("OPTN-14")
def test_a_loan_or_bursary_amount_is_a_cap_for_the_year_its_page_names() -> None:
    cap: Any = PACK.value("F05.loan_maximum.tuition")

    assert cap["maximum_minor_units"] == 979000
    assert cap["period"] == "year"
    assert "2026 to 2027 academic year" in cap["applies_to"]
    bursary: Any = PACK.value("F10.bursary_maximum")
    assert (bursary["maximum_minor_units"], bursary["period"]) == (120000, None)
    # The change for courses from 1 January 2027 is kept beside every student-finance cap.
    funds = {f.record_id: f for f in PACK.funding_instruments}
    assert "F05.rules_change" in funds["funding:F05"].facts
    assert "F05.rules_change" in funds["funding:F05.maintenance"].facts


@pytest.mark.req("OPTN-14")
def test_a_course_starting_from_january_2027_has_its_own_loans_never_the_earlier_caps() -> None:
    funds = {f.record_id: f for f in PACK.funding_instruments}

    for record_id in ("funding:F12", "funding:F12.maintenance"):
        fund = funds[record_id]
        assert "F12.rule_start" in fund.rules  # courses starting on or after 1 January 2027
        assert "F12.rule_course" in fund.rules  # 'most undergraduate': no course is named
        assert "£25,000 a year" in str(PACK.value(fund.repayment))
        assert "F13.plan_5.lifelong" in fund.facts
    per_credits: Any = PACK.value("F12.loan_maximum.tuition")
    assert (per_credits["maximum_minor_units"], per_credits["period"]) == (979000, None)
    assert "120 credits" in per_credits["applies_to"]
    assert "F12.loan_maximum.tuition" not in funds["funding:F05"].facts
    assert "F13.plan_5.undergraduate" in funds["funding:F05"].facts
    assert "F13.plan_5.learner_loan" in funds["funding:F02"].facts


@pytest.mark.req("OPTN-14", "OPT1-16")
def test_nothing_is_guessed_for_the_pages_that_did_not_state_their_value() -> None:
    offerings = {o.record_id: o for o in PACK.offerings}
    before = {o.record_id: o for o in BEFORE.offerings}

    # F04 names who else pays, not what the apprentice pays; C12's excerpts hold no date.
    assert isinstance(offerings["offering:C09"].fee_total, Unknown)
    assert isinstance(offerings["offering:C08"].application_deadline, Unknown)
    assert offerings["offering:C09"] == before["offering:C09"]
    assert offerings["offering:C08"] == before["offering:C08"]
    assert "C12" not in {s.source_id for s in PACK.sources}
    apprenticeship = next(f for f in PACK.funding_instruments if f.record_id == "funding:F04")
    assert apprenticeship.instrument_kind == "programme"  # never read as a fee of £0
    assert "does not say what the apprentice pays" in str(PACK.claim("F04.instrument_kind").note)
    t_level = offerings["offering:C11"]
    assert isinstance(t_level.fee_total, Unknown)  # never 0
    assert "never 0" in t_level.fee_total.unknown


@pytest.mark.req("OPTN-14", "TEST1-09")
@pytest.mark.parametrize("claim", LABELS["claims"], ids=lambda c: c["claim_id"])
def test_each_label_is_exactly_its_text_in_the_kept_body(claim: dict[str, Any]) -> None:
    source = next(s for s in LABELS["sources"] if s["source_id"] == claim["source_id"])
    body = EVIDENCE / source["source_id"] / f"{source['sha256']}.html"
    if not body.is_file():
        pytest.skip(f"{source['source_id']}'s body is kept only on the curating machine (R3)")
    data = body.read_bytes()
    assert hashlib.sha256(data).hexdigest() == source["sha256"]
    page = data.decode()
    span = claim["span"]
    [found] = locate(page, [claim["excerpt"]])
    offsets: Any = found["offsets"]

    assert page[span["start"] : span["end"]] == claim["excerpt"]
    assert found["count"] == claim["occurrences"]
    assert offsets[0] == [span["start"], span["end"]]  # the first occurrence


@pytest.mark.req("OPTN-14")
def test_the_pages_are_govuk_kept_privately_and_fetched_through_the_proxy() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    slots = {s["id"]: s for s in manifest["slots"]}
    pending = {s["id"]: s for s in manifest["pending_slots"]}

    for source in (s for s in PACK.sources if s.source_id in NEW_SOURCES):
        assert source.rights_class.value == "govuk"
        assert source.retention.value == "body"  # never in git: var/evidence/corpus only
        assert "via_proxy true, address_checked false" in slots[source.source_id]["fetch_route"]
    assert set(pending) == {"C12"}
    assert pending["C12"]["attempt"] == {"status": "succeeded", "reason": None}
    assert pending["C12"]["rights_status"] == "pending human rights review"
    assert pending["C12"]["retention"] == "excerpts"
    assert pending["C12"]["earlier_attempt"]["http_status"] == 404
    assert pending["C12"]["status"].startswith("fetched, not used")
    assert manifest["collected_samples"] == {
        "full_job_postings": 20,
        "course_pages": 11,
        "funding_pages": 13,
    }


@pytest.mark.req("OPTN-14")
def test_the_session_package_is_the_tool_s_output_with_the_route_rows_first() -> None:
    first, rest = package_rows(PACK, BEFORE)
    text = PACKAGE_PATH.read_text(encoding="utf-8")

    assert text == review_package(PACK, BEFORE)
    assert {r.record_id for r in first + rest} == NEW_RECORDS | {"funding:F02"}
    assert {r.field for r in first} >= {"timing", "repayment", "eligible_costs", "rule_residency"}
    assert "published_on" not in {r.field for r in first}
    # A changed record's rows session 2 already asked are not asked again.
    assert not [r for r in first + rest if r.record_id == "funding:F02" and r.field == "rule_age"]
    assert text.count("| yes / no |") == len(first) + len(rest)


def test_every_new_funding_record_cites_only_its_own_pages() -> None:
    for fund in PACK.funding_instruments:
        if fund.record_id in NEW_RECORDS:
            assert isinstance(fund, FundingInstrument)
            cited = {PACK.claim(c).source_id for c in [*fund.rules, *fund.facts]}
            assert cited <= set(fund.source_ids)
