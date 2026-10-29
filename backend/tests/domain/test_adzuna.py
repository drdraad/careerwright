"""The Adzuna adapter's fixture contract (ruling R4; spec section 6; JOB-05, JOB-01). The
fixture is synthetic and labelled (`fixtures/acquisition/README.md`)."""

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from nessa.evidence.adzuna import (
    AdzunaQuery,
    parse_search,
    recorded_url,
    redact,
    transport_url,
)
from nessa.evidence.jobs import group_copies
from nessa.evidence.records import (
    AdvertiserKind,
    ClaimField,
    DescriptionKind,
    PayBasis,
    ValidationState,
)
from tests.domain.test_pages import POSTING, UNSAFE_LINKS, page, parse

FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "acquisition" / "adzuna-search-gb.json"
APP_ID = SecretStr("id-0123456789")
APP_KEY = SecretStr("key-abcdefabcdefabcdef")


def body() -> bytes:
    return FIXTURE.read_bytes()


def search() -> object:
    raw = body()
    return parse_search(raw, sha256=hashlib.sha256(raw).hexdigest())


@pytest.mark.req("JOB-05")
def test_the_fixture_is_labelled_synthetic() -> None:
    assert "Synthetic fixture" in json.loads(body())["_synthetic"]


@pytest.mark.req("JOB-05")
def test_advertised_predicted_and_unknown_pay_stay_distinct() -> None:
    copies = {c.source_job_id: c for c in parse_search(body(), sha256="0" * 64).copies}

    advertised, predicted, unflagged, none = (copies[f"500000000{n}"] for n in (1, 2, 3, 4))
    assert advertised.salary is not None
    assert advertised.salary.basis is PayBasis.ADVERTISED
    assert advertised.salary.maximum_minor_units == 3_650_050
    assert advertised.salary.period is None  # Adzuna does not document a period
    assert predicted.salary is not None
    assert predicted.salary.basis is PayBasis.PREDICTED
    assert unflagged.salary is not None
    assert unflagged.salary.basis is PayBasis.UNKNOWN  # no flag: never confirmed advertised pay
    assert none.salary is None  # missing, never zero


@pytest.mark.req("JOB-05")
def test_descriptions_are_snippets_and_never_full_descriptions() -> None:
    result = parse_search(body(), sha256="0" * 64)

    assert {c.description_kind for c in result.copies} == {DescriptionKind.SNIPPET}
    assert all(c.description_fingerprint is None for c in result.copies)
    assert result.total == 6


@pytest.mark.req("JOB-05", "API-06")
def test_every_value_has_a_claim_pointing_into_the_hashed_response() -> None:
    raw = body()
    digest = hashlib.sha256(raw).hexdigest()
    first = parse_search(raw, sha256=digest).copies[0]
    data = json.loads(raw)

    assert first.title == "Data Quality Analyst"  # markup removed
    for claim in first.claims:
        assert claim.span.source_sha256 == digest
        assert claim.span.pointer is not None
        assert claim.span.pointer == "/results/0" or claim.span.pointer.startswith("/results/0/")
        assert claim.validation is ValidationState.STRUCTURED
    salary = next(c for c in first.claims if c.field is ClaimField.SALARY)
    assert salary.span.pointer == "/results/0"
    assert str(data["results"][0]["salary_min"]) in salary.span.excerpt


@pytest.mark.req("JOB-01")
def test_an_agency_advert_does_not_name_the_agency_as_the_employer() -> None:
    copies = {c.source_job_id: c for c in parse_search(body(), sha256="0" * 64).copies}

    assert copies["5000000005"].advertiser is AdvertiserKind.AGENCY
    assert copies["5000000001"].advertiser is AdvertiserKind.UNKNOWN  # a board, not its site


@pytest.mark.req("JOB-02")
def test_a_board_snippet_and_the_employer_page_of_one_advert_count_once() -> None:
    employer_page = parse(page(POSTING)).postings[0]
    board = parse_search(body(), sha256="0" * 64).copies

    grouped = group_copies(
        [("careers.northwind.example", employer_page), *(("adzuna", c) for c in board)]
    )

    assert len(grouped) == 6  # seven copies, six jobs: the snippet joins its employer page
    joined = next(g for g in grouped if len(g.copies) == 2)
    assert {p for p, _ in joined.copies} == {"careers.northwind.example", "adzuna"}


@pytest.mark.req("SEC-05")
def test_the_recorded_request_never_carries_the_credentials() -> None:
    query = AdzunaQuery(what="data quality analyst", where="Manchester")
    sent = transport_url(query, APP_ID, APP_KEY)
    kept = recorded_url(query)

    assert APP_ID.get_secret_value() in sent
    assert APP_KEY.get_secret_value() in sent
    assert "app_id" not in kept
    assert "app_key" not in kept
    assert kept == (
        "https://api.adzuna.com/v1/api/jobs/gb/search/1"
        "?what=data+quality+analyst&where=Manchester&results_per_page=20"
    )
    assert redact(sent) == kept


@pytest.mark.req("SEC-05")
def test_redaction_removes_credentials_from_any_url_however_they_are_written() -> None:
    url = "https://api.adzuna.com/x?APP_KEY=k1&what=a&App_Id=i1&app_key=k2#frag"

    assert redact(url) == "https://api.adzuna.com/x?what=a"


@pytest.mark.req("SEC-05")
@pytest.mark.parametrize(
    "fields",
    [
        {"what": "", "where": "Leeds"},
        {"what": "x" * 101, "where": "Leeds"},
        {"what": "analyst", "where": "Leeds", "page": 11},
        {"what": "analyst", "where": "Leeds", "results_per_page": 51},
    ],
)
def test_queries_are_bounded(fields: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AdzunaQuery.model_validate(fields)


def with_redirect(link: str) -> bytes:
    data = json.loads(body())
    data["results"] = [{**data["results"][0], "redirect_url": link}]
    return json.dumps(data).encode()


@pytest.mark.req("ACQ-04")
@pytest.mark.parametrize("link", UNSAFE_LINKS)
def test_an_adzuna_link_that_is_not_plain_https_is_no_claim_at_all(link: str) -> None:
    [copy] = parse_search(with_redirect(link), sha256="0" * 64).copies

    assert copy.apply_url is None
    assert ClaimField.APPLY_URL not in {c.field for c in copy.claims}


@pytest.mark.req("ACQ-04")
def test_a_valid_adzuna_https_link_is_kept_without_its_surrounding_space() -> None:
    link = " https://www.adzuna.co.uk/jobs/land/ad/5000000001?se=synthetic"
    [copy] = parse_search(with_redirect(link), sha256="0" * 64).copies

    assert copy.apply_url == link.strip()
    assert ClaimField.APPLY_URL in {c.field for c in copy.claims}


@pytest.mark.req("JOB-05")
@pytest.mark.parametrize(
    "broken",
    [b"not json", b'{"results": "nope"}', b'{"count": 1}', b"[]"],
)
def test_a_malformed_response_is_an_error_never_an_empty_page(broken: bytes) -> None:
    result = parse_search(broken, sha256="0" * 64)

    assert result.error == "response_invalid"
    assert result.copies == []
