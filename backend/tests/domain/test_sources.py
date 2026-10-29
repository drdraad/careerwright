"""The source permission manifest (OI-11) and the session 1 rights policy (H-06) as code:
what may be fetched, from where, and what a workspace keeps of it (ACQ-06, FRESH-01)."""

import json
from datetime import date
from pathlib import Path

import pytest

from nessa.evidence.acquire import Pacer
from nessa.evidence.records import Retention, RightsClass
from nessa.evidence.sources import (
    MANIFEST_PATH,
    PENDING_REVIEW,
    Access,
    classify_page,
    load_manifest,
    retention,
    rule_for,
)

REPO = Path(__file__).resolve().parents[3]
ON = date(2026, 10, 28)


def test_the_manifest_loads_and_names_its_open_item() -> None:
    manifest = load_manifest()

    assert manifest.open_item == "OI-11"
    assert manifest.default.rights_class is RightsClass.OTHER


@pytest.mark.req("ACQ-06")
def test_the_policy_classes_in_code_are_exactly_the_corpus_manifest_s_classes() -> None:
    corpus = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    ids = {c["id"] for c in corpus["policy"]["rights_policy"]["classes"]}

    assert ids == {c.value for c in RightsClass}
    keep = {
        c["id"]
        for c in corpus["policy"]["rights_policy"]["classes"]
        if "keep_privately" in c["permitted"]
    }
    assert keep == {c.value for c in RightsClass if retention(c) is Retention.BODY}


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    ("host", "rights_class", "access"),
    [
        ("www.gov.uk", RightsClass.GOVUK, Access.PERMITTED),
        ("nationalcareers.service.gov.uk", RightsClass.PUBLIC_SECTOR, Access.PERMITTED),
        ("api.adzuna.com", RightsClass.JOB_BOARD, Access.API_ONLY),
        ("www.adzuna.co.uk", RightsClass.JOB_BOARD, Access.API_ONLY),
        ("www.linkedin.com", RightsClass.JOB_BOARD, Access.DENIED),
        ("uk.linkedin.com", RightsClass.JOB_BOARD, Access.DENIED),
        ("uk.indeed.com", RightsClass.JOB_BOARD, Access.DENIED),
        ("careers.unknown-employer.example", RightsClass.OTHER, Access.PERMITTED),
    ],
)
def test_each_host_gets_its_listed_class_and_access_and_any_other_host_is_other(
    host: str, rights_class: RightsClass, access: Access
) -> None:
    rule = rule_for(host)

    assert rule.rights_class is rights_class
    assert rule.access is access


@pytest.mark.req("ACQ-06")
def test_a_denied_source_says_why_and_a_permitted_one_says_what_it_relied_on() -> None:
    denied = rule_for("www.linkedin.com")
    govuk = rule_for("www.gov.uk")

    assert denied.reason
    assert "Open Government Licence v3.0" in govuk.terms
    assert govuk.terms_read_on == ON
    assert govuk.attribution


@pytest.mark.req("ACQ-06")
def test_only_the_keep_privately_classes_retain_a_body() -> None:
    assert retention(RightsClass.GOVUK) is Retention.BODY
    assert retention(RightsClass.EMPLOYER_POSTING) is Retention.BODY
    assert retention(RightsClass.JOB_BOARD) is Retention.EXCERPTS
    assert retention(RightsClass.OTHER) is Retention.EXCERPTS


@pytest.mark.req("ACQ-06")
def test_a_listed_page_is_classified_by_its_host_with_the_terms_it_relied_on() -> None:
    page = classify_page("www.gov.uk", hiring_hosts=(), on=ON)

    assert page.rights_class is RightsClass.GOVUK
    assert page.rights_status.startswith("govuk: ")
    assert "Open Government Licence v3.0" in page.rights_status


@pytest.mark.req("ACQ-06")
def test_an_employer_s_own_careers_site_is_an_employer_posting() -> None:
    page = classify_page("careers.northwind.example", hiring_hosts=("northwind.example",), on=ON)

    assert page.rights_class is RightsClass.EMPLOYER_POSTING
    assert page.rights_status.startswith("employer-posting: ")
    assert "northwind.example" in page.rights_status
    assert page.retention is Retention.BODY


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    "hiring_hosts",
    [(), ("someone-else.example",), ("example",)],
    ids=["no structured employer", "another employer", "a bare suffix"],
)
def test_a_page_not_clearly_within_a_class_stays_pending_human_rights_review(
    hiring_hosts: tuple[str, ...],
) -> None:
    page = classify_page("jobs.board.example", hiring_hosts=hiring_hosts, on=ON)

    assert page.rights_class is RightsClass.OTHER
    assert page.rights_status == PENDING_REVIEW == "pending human rights review"
    assert page.retention is Retention.EXCERPTS


def test_requests_to_one_host_are_paced_to_its_rate_limit_and_other_hosts_are_not() -> None:
    now = [100.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    pacer = Pacer(clock=lambda: now[0], sleep=sleep)
    pacer.wait("www.gov.uk", 5.0)
    pacer.wait("www.gov.uk", 5.0)
    pacer.wait("nationalcareers.service.gov.uk", 5.0)

    assert slept == [5.0]  # only the second request to the same host waited


def test_the_manifest_file_is_inside_the_package() -> None:
    assert MANIFEST_PATH.is_file()
    assert MANIFEST_PATH.parent.name == "evidence"
