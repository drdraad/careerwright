"""Third parties' personal details are never kept (session 1, "always true"; ADR 0009
decision 4): emails, telephone numbers and JSON-LD contacts go before anything is hashed,
parsed or sealed. Every name, address and number here is synthetic."""

import base64
import hashlib
import json
from datetime import UTC, datetime

import pytest
from pydantic import SecretStr

from nessa.evidence import adzuna
from nessa.evidence.acquire import Pacer, acquire_adzuna, acquire_page
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.pages import redact_page
from nessa.evidence.redaction import CONTACT_REMOVED, EMAIL_REMOVED, PHONE_REMOVED, redact_text
from tests.domain.test_pages import POSTING, page
from tests.support.acquisition_service import LOOPBACK, scripted_resolver
from tests.support.source_server import Scripted, source_server

PHONES = [
    "020 7946 0958",
    "0161 496 0000",
    "(0161) 496 0000",
    "07700 900123",
    "07700900123",
    "01632 960123",
    "+44 20 7946 0958",
    "+44 (0)20 7946 0958",
    "+44 7700 900123",
    "+1 555 123 4567",
    "+1 (555) 123-4567",
    "+33 1 23 45 67 89",
]
NOT_PHONES = [
    "2026-10-20",
    "32000",
    "36500.50",
    "NW-7781",
    "M1 1AA",
    "https://jobs.example.org/ad/01234567890",
    "ref=07700900123",
    "salary 30000 to 34000",
]


@pytest.mark.parametrize("phone", PHONES)
def test_telephone_numbers_in_uk_and_international_forms_are_removed(phone: str) -> None:
    assert redact_text(f"Call Sam on {phone} today.") == f"Call Sam on {PHONE_REMOVED} today."


@pytest.mark.parametrize("text", NOT_PHONES)
def test_dates_amounts_references_and_urls_are_not_taken_for_numbers(text: str) -> None:
    assert redact_text(text) == text


@pytest.mark.parametrize(
    "email", ["jane.smith@recruit.example", "j+jobs@mail.example.co.uk", "HR@Example.ORG"]
)
def test_email_addresses_are_removed(email: str) -> None:
    assert redact_text(f"Write to {email}, or mailto:{email}") == (
        f"Write to {EMAIL_REMOVED}, or mailto:{EMAIL_REMOVED}"
    )


CONTACT_POSTING = {
    **POSTING,
    "applicationContact": {
        "@type": "ContactPoint",
        "name": "Jane Smith",
        "email": "jane.smith@recruit.example",
        "telephone": "+44 20 7946 0958",
    },
    "hiringOrganization": {
        "@type": "Organization",
        "name": "Northwind Analytics Ltd",
        "contactPoint": [{"@type": "ContactPoint", "name": "Sam Jones", "faxNumber": "x"}],
    },
}
CONTACT_PAGE = page(
    CONTACT_POSTING,
    body="<h1>Data Quality Analyst</h1><p>Questions? Call 0161 496 0000 or write to "
    "careers@northwind.example.</p>",
)
PERSONAL = [
    "Jane Smith",
    "Sam Jones",
    "jane.smith@recruit.example",
    "careers@northwind.example",
    "7946 0958",
    "496 0000",
]


def test_json_ld_contacts_are_removed_and_the_rest_of_the_page_kept() -> None:
    redacted = redact_page(CONTACT_PAGE)

    assert not [p for p in PERSONAL if p in redacted]
    assert CONTACT_REMOVED in redacted
    assert "Northwind Analytics Ltd" in redacted  # the organisation is not a person
    assert "Data Quality Analyst" in redacted
    assert redact_page(page(POSTING)) == page(POSTING)  # nothing to remove: unchanged


@pytest.mark.req("ACQ-06")
def test_a_kept_body_its_excerpts_and_its_claims_hold_no_personal_details() -> None:
    raw = CONTACT_PAGE.encode()
    with source_server({"/jobs/1": Scripted(body=raw)}) as server:
        fetcher = Fetcher(
            resolve=scripted_resolver({"www.gov.uk": [LOOPBACK]}),
            user_agent="NessaL0/test",
            extra_allowed=frozenset({("127.0.0.1", server.port)}),
        )
        result = acquire_page(
            fetcher,
            Pacer(sleep=lambda seconds: None),
            f"http://www.gov.uk:{server.port}/jobs/1",
            now=datetime(2026, 10, 29, tzinfo=UTC),
        )

    assert result.body_b64 is not None  # a keep-privately host: the body is kept
    kept = base64.b64decode(result.body_b64)
    assert not [p for p in PERSONAL if p.encode() in kept]
    assert result.content_sha256 == hashlib.sha256(kept).hexdigest()  # spans index into it
    assert result.retrieved_sha256 == hashlib.sha256(raw).hexdigest()  # change detection
    [copy] = result.copies
    stored = json.dumps([c.model_dump(mode="json") for c in copy.claims])
    assert not [p for p in PERSONAL if p in stored]
    text = kept.decode()
    for claim in copy.claims:
        if claim.span.start is not None and claim.span.end is not None:
            assert text[claim.span.start : claim.span.end].startswith(claim.span.excerpt[:20])


@pytest.mark.req("ACQ-06")
def test_an_api_response_s_claims_hold_no_personal_details() -> None:
    body = json.dumps(
        {
            "count": 1,
            "results": [
                {
                    "id": "1",
                    "title": "Data Quality Analyst",
                    "description": "Call Jane on 07700 900123 or jane@recruit.example.",
                    "redirect_url": "https://www.adzuna.co.uk/jobs/land/ad/1?se=synthetic",
                    "company": {"display_name": "Northwind"},
                }
            ],
        }
    ).encode()
    routes = {
        "/v1/api/jobs/gb/search/1": Scripted(
            headers=(("Content-Type", "application/json"),), body=body
        )
    }
    with source_server(routes) as server:
        fetcher = Fetcher(
            resolve=scripted_resolver({"api.adzuna.test.example": [LOOPBACK]}),
            user_agent="NessaL0/test",
            extra_allowed=frozenset({("127.0.0.1", server.port)}),
        )
        result = acquire_adzuna(
            fetcher,
            Pacer(sleep=lambda seconds: None),
            adzuna.AdzunaQuery(what="data quality analyst", where="Manchester"),
            (SecretStr("synthetic-id"), SecretStr("synthetic-key")),
            now=datetime(2026, 10, 29, tzinfo=UTC),
            search_url=f"http://api.adzuna.test.example:{server.port}/v1/api/jobs/gb/search/{{page}}",
        )

    [copy] = result.copies
    stored = json.dumps([c.model_dump(mode="json") for c in copy.claims])
    assert "07700" not in stored
    assert "jane@" not in stored
    assert copy.apply_url == "https://www.adzuna.co.uk/jobs/land/ad/1?se=synthetic"
    assert result.retrieved_sha256 == hashlib.sha256(body).hexdigest()
    assert result.content_sha256 != result.retrieved_sha256
