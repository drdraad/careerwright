"""The early accuracy read's scoring (Task 7b, plan v1.2): the deterministic path's job copy
against a page's labels, field by field. Values are synthetic."""

from datetime import UTC, date, datetime
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Any

import pytest

from nessa.catalogue.option_pack import Split, load_pack
from nessa.evidence.acquire import Pacer
from nessa.evidence.fetcher import Admit, Fetched, Fetcher, FetchFailure, HostNotFoundError
from nessa.evidence.records import (
    AdvertiserKind,
    DescriptionKind,
    JobCopy,
    Location,
    PayBasis,
    Salary,
    SalaryPeriod,
)
from tools.accuracy_read import PACK_VERSION, Outcome, read, score_job

IPAddress = IPv4Address | IPv6Address

LABELS: dict[str, object] = {
    "title": "Data Analyst",
    "employer": None,  # an agency's unnamed client
    "advertiser": "agency",
    "location": {"label": "Greater Manchester", "locality": "Manchester"},
    "salary": {
        "currency": "GBP",
        "minimum_minor_units": 3800000,
        "maximum_minor_units": 4500000,
        "period": "year",
        "basis": "advertised",
    },
    "date_posted": "2026-09-22",
    "valid_through": "2026-11-03T23:55:00+00:00",
    "employment_type": "permanent, full-time",
    "work_mode": "hybrid",
    "description_kind": "full",
    "source_job_id": "57376369",
}


def copy(**changes: object) -> JobCopy:
    base: dict[str, object] = {
        "source_job_id": "57376369",
        "title": "Data Analyst",
        "employer": "Cathcart Technology",
        "advertiser": AdvertiserKind.AGENCY,
        "locations": [Location(label="Manchester, North West England", locality="Manchester")],
        "salary": Salary(
            currency="GBP",
            minimum_minor_units=3800000,
            maximum_minor_units=4500000,
            period=SalaryPeriod.YEAR,
            basis=PayBasis.ADVERTISED,
        ),
        "date_posted": date(2026, 9, 22),
        "valid_through": datetime(2026, 11, 3, 23, 55, tzinfo=UTC),
        "employment_type": "FULL_TIME",
        "description_kind": DescriptionKind.FULL,
    }
    return JobCopy.model_validate({**base, **changes})


@pytest.mark.req("TEST1-09")
def test_a_copy_that_reads_every_field_the_page_states_scores_correct_and_keeps_unknowns() -> None:
    scores = score_job(copy(), LABELS)

    assert scores["title"] is Outcome.CORRECT
    assert scores["salary"] is Outcome.CORRECT
    assert scores["valid_through"] is Outcome.CORRECT
    assert scores["employment_type"] is Outcome.CORRECT
    # An agency's own name is never the hiring employer: the unnamed client stays unknown.
    assert scores["employer"] is Outcome.KEPT_UNKNOWN
    assert scores["advertiser"] is Outcome.CORRECT
    assert scores["work_mode"] is Outcome.MISSING  # hybrid is stated; the path reads none


@pytest.mark.req("TEST1-09")
def test_a_copy_calling_an_agency_the_employer_scores_incorrect_and_unsupported() -> None:
    scores = score_job(copy(advertiser=AdvertiserKind.EMPLOYER), LABELS)

    assert scores["advertiser"] is Outcome.INCORRECT
    # It now names the agency as the hiring employer, which the page does not support.
    assert scores["employer"] is Outcome.UNSUPPORTED


@pytest.mark.req("TEST1-09")
@pytest.mark.parametrize(
    ("salary", "outcome"),
    [
        (None, Outcome.MISSING),
        (
            Salary(
                currency="GBP",
                minimum_minor_units=4500000,
                maximum_minor_units=4500000,
                period=SalaryPeriod.YEAR,
                basis=PayBasis.ADVERTISED,
            ),
            Outcome.INCORRECT,
        ),
    ],
    ids=["none read", "a different minimum"],
)
def test_pay_is_correct_only_when_every_part_matches(
    salary: Salary | None, outcome: Outcome
) -> None:
    assert score_job(copy(salary=salary), LABELS)["salary"] is outcome


@pytest.mark.req("TEST1-09")
def test_pay_the_page_leaves_unknown_but_the_path_reads_is_unsupported() -> None:
    labels = {**LABELS, "salary": None}

    assert score_job(copy(), labels)["salary"] is Outcome.UNSUPPORTED
    assert score_job(copy(salary=None), labels)["salary"] is Outcome.KEPT_UNKNOWN


@pytest.mark.req("TEST1-09")
def test_a_contract_word_the_label_does_not_state_is_incorrect() -> None:
    scores = score_job(copy(employment_type="FULL_TIME,CONTRACTOR"), LABELS)

    assert scores["employment_type"] is Outcome.INCORRECT


@pytest.mark.req("TEST1-09")
def test_no_copy_at_all_leaves_every_stated_field_missing() -> None:
    scores = score_job(None, LABELS)

    assert scores["title"] is Outcome.MISSING
    assert scores["employer"] is Outcome.KEPT_UNKNOWN
    assert set(scores) == set(LABELS)


def _no_such_host(host: str, port: int) -> list[IPAddress]:
    raise HostNotFoundError


def _paced() -> tuple[Pacer, list[float]]:
    now = [0.0]
    waits: list[float] = []

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        now[0] += seconds

    return Pacer(clock=lambda: now[0], sleep=sleep), waits


@pytest.mark.req("TEST1-09", "ACQ-06")
def test_one_read_paces_every_page_of_a_host_to_its_rate_limit(tmp_path: Path) -> None:
    """With no kept body (`tmp_path`), the read fetches every development page again, twelve
    of them on one job board: each after that host's first waits its rate limit (spec
    section 6), across the whole read. No request leaves: no name resolves."""
    pacer, waits = _paced()
    fetcher = Fetcher(user_agent="NessaL0/test", resolve=_no_such_host)

    read(load_pack(PACK_VERSION), fetcher=fetcher, pacer=pacer, evidence_dir=tmp_path)

    assert waits == [5.0] * 11


class _Recording(Fetcher):
    """The network edge, recording each page asked for; no name resolves."""

    def __init__(self) -> None:
        super().__init__(user_agent="NessaL0/test", resolve=_no_such_host)
        self.asked: list[str] = []

    def fetch_page(self, url: str, admit: Admit | None = None) -> Fetched | FetchFailure:
        self.asked.append(url)
        return super().fetch_page(url, admit)


@pytest.mark.req("TEST1-09")
def test_the_read_never_touches_a_holdout_page(tmp_path: Path) -> None:
    pack = load_pack(PACK_VERSION)
    holdout = {s.source_id: s.url for s in pack.sources if s.split is Split.HOLDOUT}
    fetcher = _Recording()

    result = read(pack, fetcher=fetcher, pacer=_paced()[0], evidence_dir=tmp_path)

    pages: Any = result["pages"]
    assert holdout
    assert not set(holdout) & {p["slot"] for p in pages}
    assert len(fetcher.asked) == 17  # the development pages, Adzuna's three left out
    assert not set(holdout.values()) & set(fetcher.asked)
