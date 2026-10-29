"""The source permission manifest (OI-11) and the session 1 rights policy (H-06) as code:
what may be fetched, from where, and what a workspace keeps of it (ACQ-06, FRESH-01)."""

import base64
import json
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from nessa.evidence.acquire import AcquisitionResult, Pacer, acquire_page
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.records import AttemptStatus, ClaimField, Retention, RightsClass
from nessa.evidence.sources import (
    MANIFEST_PATH,
    PENDING_REVIEW,
    Access,
    classify_page,
    load_manifest,
    retention,
    rule_for,
)
from tests.domain.test_pages import POSTING, page
from tests.support.acquisition_service import LOOPBACK, scripted_resolver
from tests.support.source_server import Scripted, SourceServer, source_server

REPO = Path(__file__).resolve().parents[3]
ON = date(2026, 10, 28)
PAGE_BODY = page(POSTING).encode()


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
    page_rights = classify_page("www.gov.uk")

    assert page_rights.rights_class is RightsClass.GOVUK
    assert page_rights.rights_status.startswith("govuk: ")
    assert "Open Government Licence v3.0" in page_rights.rights_status


def _acquired(host: str, body: bytes) -> AcquisitionResult:
    with source_server({"/robots.txt": Scripted(404), "/jobs/1": Scripted(body=body)}) as server:
        fetcher = Fetcher(
            resolve=scripted_resolver({host: [LOOPBACK]}),
            user_agent="NessaL0/test",
            extra_allowed=frozenset({("127.0.0.1", server.port)}),
        )
        return acquire_page(
            fetcher,
            Pacer(sleep=lambda seconds: None),
            f"http://{host}:{server.port}/jobs/1",
            now=datetime(2026, 10, 29, tzinfo=UTC),
        )


def _naming(host_links: list[str], name: str = "Northwind Analytics Ltd") -> bytes:
    organisation = {"@type": "Organization", "name": name, "sameAs": host_links}
    return page({**POSTING, "hiringOrganization": organisation, "url": host_links[0]}).encode()


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    ("host", "links", "name"),
    [
        (
            "careers.northwind.example",
            ["https://careers.northwind.example", "https://northwind.example"],
            "Northwind Analytics Ltd",
        ),
        ("www.totaljobs.co.uk", ["https://co.uk"], "Northwind Analytics Ltd"),
        ("someone.github.io", ["https://github.io"], "Northwind Analytics Ltd"),
        ("www.reed.co.uk", ["https://www.reed.co.uk", "https://reed.co.uk"], "Reed"),
    ],
    ids=[
        "a page naming its own host",
        "a public suffix (co.uk)",
        "a public suffix (github.io)",
        "an agency on its own board",
    ],
)
def test_a_page_naming_itself_as_the_hiring_organisation_never_raises_its_retention(
    host: str, links: list[str], name: str
) -> None:
    result = _acquired(host, _naming(links, name))

    assert result.status is AttemptStatus.SUCCEEDED
    assert result.rights_class is RightsClass.OTHER
    assert result.rights_status == PENDING_REVIEW == "pending human rights review"
    assert result.retention is Retention.EXCERPTS
    assert result.body_b64 is None
    [copy] = result.copies  # the posting is still read, and its employer still cited
    assert copy.employer == name
    assert ClaimField.EMPLOYER in {c.field for c in copy.claims}


@pytest.mark.req("ACQ-06")
def test_a_listed_keep_privately_host_keeps_its_body_by_its_manifest_entry() -> None:
    # The controlled server stands in for www.gov.uk through the scripted DNS: the class
    # comes from the manifest's entry for the host, not from anything on the page.
    body = page(POSTING).encode()

    result = _acquired("www.gov.uk", body)

    assert (result.rights_class, result.retention) == (RightsClass.GOVUK, Retention.BODY)
    assert result.body_b64 is not None
    assert base64.b64decode(result.body_b64) == body


CROSS_HOST_NAMES = {
    "lnkd.in": [LOOPBACK],
    "www.linkedin.com": [LOOPBACK],
    "www.adzuna.co.uk": [LOOPBACK],
    "jobs.board.example": [LOOPBACK],
    "jobs.other.example": [LOOPBACK],
}


def _cross_host(
    server: SourceServer, pacer: Pacer | None = None, *, other: SourceServer | None = None
) -> Callable[[str], AcquisitionResult]:
    ports = {server.port} | ({other.port} if other else set())
    fetcher = Fetcher(
        resolve=scripted_resolver(CROSS_HOST_NAMES),
        user_agent="NessaL0/test",
        extra_allowed=frozenset(("127.0.0.1", port) for port in ports),
    )
    return lambda url: acquire_page(
        fetcher,
        pacer or Pacer(sleep=lambda seconds: None),
        url,
        now=datetime(2026, 10, 29, tzinfo=UTC),
    )


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    ("host", "reason"),
    [("www.linkedin.com", "source_denied"), ("www.adzuna.co.uk", "source_api_only")],
    ids=["a denied host (the lnkd.in shape)", "an API-only host"],
)
def test_a_redirect_to_a_host_the_manifest_refuses_is_blocked_before_any_request_to_it(
    host: str, reason: str
) -> None:
    with source_server() as server:
        target = f"http://{host}:{server.port}/jobs/view/1"
        server.routes["/abc"] = Scripted(301, headers=(("Location", target),))
        result = _cross_host(server)(f"http://lnkd.in:{server.port}/abc")

    assert (result.status, result.reason) == (AttemptStatus.BLOCKED, reason)
    assert result.redirects == [target]  # the redirects so far, each a checked URL
    assert result.requested_url == f"http://lnkd.in:{server.port}/abc"
    assert [s.host for s in server.seen] == [f"lnkd.in:{server.port}"] * 2  # robots, /abc
    assert server.paths() == ["/robots.txt", "/abc"]


@pytest.mark.req("ACQ-06")
def test_a_redirect_to_an_origin_whose_robots_txt_disallows_is_never_requested() -> None:
    disallow = Scripted(
        body=b"User-agent: *\nDisallow: /job\n", headers=(("Content-Type", "text/plain"),)
    )
    with source_server() as first, source_server({"/robots.txt": disallow}) as other:
        target = f"http://jobs.other.example:{other.port}/job"
        first.routes["/go"] = Scripted(302, headers=(("Location", target),))
        result = _cross_host(first, other=other)(f"http://jobs.board.example:{first.port}/go")

    assert (result.status, result.reason) == (AttemptStatus.BLOCKED, "robots_disallowed")
    assert result.redirects == [target]
    assert first.paths() == ["/robots.txt", "/go"]
    assert other.paths() == ["/robots.txt"]  # the page itself never
    assert result.http_requests == 3


@pytest.mark.req("ACQ-06")
def test_a_redirect_to_another_host_waits_for_that_host_s_rate_limit() -> None:
    now = [100.0]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    pacer = Pacer(clock=lambda: now[0], sleep=sleep)
    with source_server() as first, source_server({"/job": Scripted(body=PAGE_BODY)}) as other:
        acquire = _cross_host(first, pacer, other=other)
        target = f"http://jobs.other.example:{other.port}/job"
        first.routes["/go"] = Scripted(302, headers=(("Location", target),))
        acquire(target)  # the other host was visited a moment ago
        result = acquire(f"http://jobs.board.example:{first.port}/go")

    assert result.status is AttemptStatus.SUCCEEDED
    assert result.final_url == target
    assert slept == [5.0]  # the default rate limit, waited before the redirect's request


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    "host", ["jobs.board.example", "careers.unknown-employer.example", "www.reed.co.uk"]
)
def test_an_unlisted_page_stays_pending_human_rights_review(host: str) -> None:
    page_rights = classify_page(host)

    assert page_rights.rights_class is RightsClass.OTHER
    assert page_rights.rights_status == PENDING_REVIEW
    assert page_rights.retention is Retention.EXCERPTS


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
