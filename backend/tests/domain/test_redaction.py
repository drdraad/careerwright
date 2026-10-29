"""Third parties' personal details are never kept (session 1, "always true"; ADR 0009
decision 4): emails, telephone numbers and JSON-LD contacts go before anything is hashed,
parsed or sealed. Every name, address and number here is synthetic."""

import base64
import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import quote

import pytest
from pydantic import SecretStr

from nessa.evidence import adzuna
from nessa.evidence.acquire import AcquisitionResult, Pacer, acquire_adzuna, acquire_page
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.pages import redact_page
from nessa.evidence.records import AttemptStatus, BodyNotKept, ClaimField, Retention
from nessa.evidence.redaction import (
    CONTACT_REMOVED,
    EMAIL_REMOVED,
    PHONE_REMOVED,
    redact_shown,
    redact_text,
)
from tests.domain.test_pages import POSTING, page
from tests.support.acquisition_service import LOOPBACK, scripted_resolver
from tests.support.source_server import SYNTHETIC_MARKER, Scripted, source_server

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

    assert redacted.unremovable is None
    assert not [p for p in PERSONAL if p in redacted.text]
    assert CONTACT_REMOVED in redacted.text
    assert "Northwind Analytics Ltd" in redacted.text  # the organisation is not a person
    assert "Data Quality Analyst" in redacted.text
    assert redact_page(page(POSTING)).text == page(POSTING)  # nothing to remove: unchanged


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


def _acquire_kept(body: bytes) -> tuple[AcquisitionResult, bytes]:
    with source_server({"/jobs/1": Scripted(body=body)}) as server:
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
    return result, base64.b64decode(result.body_b64) if result.body_b64 else b""


# Raw JSON-LD as a page writes it: escapes (`\n`, `\t`, `>`) right before an email or a
# telephone number, an identifier that looks like a number, and a contact (re-review A I-1,
# I-2, M-1).
ESCAPED_BLOCK = (
    '{"@context": "https://schema.org/", "@type": "JobPosting", "title": "Data Quality Analyst",'
    ' "identifier": {"@type": "PropertyValue", "value": "0123456789"},'
    ' "description": "Send your CV to:\\njane.smith@recruit.example\\tor call:\\n07700 900123'
    ' \\u003cp\\u003esam@agency.example\\u003c/p\\u003e Ask for\\u003e+44 20 7946 0958",'
    ' "applicationContact": {"@type": "ContactPoint", "name": "Jane Smith"},'
    ' "jobLocation": {"address": {"addressLocality": "Manchester"}}}'
)
ESCAPED_PERSONAL = [
    "jane.smith@recruit.example",
    "sam@agency.example",
    "07700",
    "7946",
    "Jane Smith",
]


def _escaped_page(newline: str = "\n") -> bytes:
    text = (
        f'<!doctype html><html><head>{SYNTHETIC_MARKER}{newline}<script type="application/ld+json">'
        f"{newline}{ESCAPED_BLOCK}{newline}</script></head><body><p>Or write to"
        f"{newline}hr@northwind.example</p></body></html>"
    )
    return text.encode()


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["LF", "CRLF"])
def test_details_after_json_escapes_and_on_crlf_pages_go_and_the_posting_still_parses(
    newline: str,
) -> None:
    result, kept = _acquire_kept(_escaped_page(newline))

    [copy] = result.copies  # the redacted block is still valid JSON-LD
    assert copy.title == "Data Quality Analyst"
    assert copy.source_job_id == "0123456789"  # an ID is never taken for a phone number
    assert not [p for p in [*ESCAPED_PERSONAL, "hr@northwind.example"] if p.encode() in kept]
    assert b"\r" not in kept  # line endings are normalised before anything else
    stored = json.dumps([c.model_dump(mode="json") for c in copy.claims])
    assert not [p for p in ESCAPED_PERSONAL if p in stored]
    assert kept.count(b"</script>") == 1  # the escaped `<\/p>` closes nothing early


@pytest.mark.req("ACQ-06")
def test_a_contact_block_that_cannot_be_located_means_the_body_is_never_kept() -> None:
    # The re-review's case 10: a raw NUL in the block, so the parser's view of it differs from
    # the page's text and it cannot be rewritten in place; its contact would stay, so the
    # body is not kept.
    block = json.dumps(
        {
            **POSTING,
            "description": "Call:\n07700 900123 or jane.smith@recruit.example",
            "applicationContact": {"name": "Jane Smith"},
        }
    ).replace("Data Quality Analyst", "Data Quality\x00Analyst")
    body = page_with_block(block)

    result, kept = _acquire_kept(body)

    assert kept == b""
    assert (result.retention, result.body_not_kept) == (
        Retention.EXCERPTS,
        BodyNotKept.CONTACT_UNLOCATED,
    )
    assert result.rights_status is not None
    assert "[" not in result.rights_status  # the rights statement only (review B N5)
    # Its claims come from redacted values, though cited by pointer (re-review A N-1 (a)).
    stored = json.dumps([c.model_dump(mode="json") for copy in result.copies for c in copy.claims])
    assert result.copies
    assert not [p for p in ESCAPED_PERSONAL if p in stored]


# The re-review's probe, cases 11 to 13 (re-review A N-1 (b) to (d)), on a keep-privately host.
APP_STATE = (
    '<script type="application/json">{"recruiter": "Call:\\n07700 900123 or '
    '\\u003cb\\u003ejane@recruit.example"}</script>'
)
NOT_JSON = (
    '{"@type": "JobPosting", "title": "Data Quality Analyst", '
    '"description": "Call:\\n07700 900123",}'  # a trailing comma: not JSON
)
REPEATED = (
    '{"@type": "JobPosting", "title": "Data Quality Analyst",'
    ' "description": "Call:\\n07700 900123", "description": "Apply online."}'
)


@pytest.mark.req("ACQ-06")
def test_inline_json_in_any_script_is_redacted_in_its_decoded_values() -> None:
    body = (
        f"<!doctype html><html><head>{SYNTHETIC_MARKER}{APP_STATE}</head><body>x</body></html>"
    ).encode()

    _, kept = _acquire_kept(body)

    assert kept  # kept, and redacted
    assert b"07700" not in kept
    assert b"jane@recruit.example" not in kept
    assert json.loads(kept.decode().split('json">')[1].split("</script>")[0])  # still JSON


@pytest.mark.req("ACQ-06")
def test_a_json_ld_block_that_is_not_json_and_holds_details_means_no_body() -> None:
    result, kept = _acquire_kept(page_with_block(NOT_JSON))

    assert kept == b""
    assert result.body_not_kept is BodyNotKept.BLOCK_UNREDACTABLE
    assert result.extraction is not None  # its posting was never read either


@pytest.mark.req("ACQ-06")
def test_a_repeated_key_s_shadowed_value_is_not_kept() -> None:
    result, kept = _acquire_kept(page_with_block(REPEATED))

    assert kept
    assert b"07700" not in kept  # the earlier, shadowed description went with the rewrite
    [copy] = result.copies
    assert copy.title == "Data Quality Analyst"


def page_with_block(block: str) -> bytes:
    return (
        f'<!doctype html><html><head>{SYNTHETIC_MARKER}<script type="application/ld+json">'
        f"{block}</script></head><body>x</body></html>"
    ).encode()


# Forms that show a detail only once the page's text is normalised (fix round 3: review C
# I1, re-review 3 A R3-2): its entity decoded, its whitespace collapsed, a character that
# does not print dropped.
HIDDEN_FORMS = {
    "a non-breaking space": "Call 0161&nbsp;496&nbsp;0000 today.",
    "a number split by newlines": "Call 0161\n496\n0000 today.",
    "a zero-width space": "Write to ada&#8203;@northwind.example today.",
    "a soft hyphen": "Write to ada@north&shy;wind.example today.",
}


def page_with_text(text: str) -> bytes:
    return (
        f"<!doctype html><html><head>{SYNTHETIC_MARKER}</head><body><p>{text}</p></body></html>"
    ).encode()


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("text", HIDDEN_FORMS.values(), ids=HIDDEN_FORMS.keys())
def test_a_kept_body_that_shows_a_detail_once_normalised_is_not_kept(text: str) -> None:
    result, kept = _acquire_kept(page_with_text(text))

    assert kept == b""
    assert (result.retention, result.body_not_kept) == (
        Retention.EXCERPTS,
        BodyNotKept.VISIBLE_TEXT_DETAIL,
    )


# Fix round 4 (re-review 4 A R4-1): an email split by inline markup, which a reader sees whole
# but which reads with a space by its "@" or a dot once the page's text is joined.
SPLIT_EMAILS = {
    "a span around the @": "Write to jane<span>@</span>recruit.example today.",
    "a tag around the domain": "Write to jane@<b>recruit</b>.example today.",
}
# An "@" with no address after it: no domain at all, or one sentence ending and the next
# starting with a capital, which never continues a domain (fix round 5, re-review 5 A R5-1).
ORDINARY_AT = {
    "no domain": "Tickets are £5 @ the door, or £8 for two.",
    "a handle ending a sentence": "Follow @GOVUK. Sign up",
    "a time ending a sentence": "Drop in @ 10am. Bring photo ID.",
}


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("text", SPLIT_EMAILS.values(), ids=SPLIT_EMAILS.keys())
def test_a_kept_body_with_an_email_split_by_inline_markup_is_not_kept(text: str) -> None:
    result, kept = _acquire_kept(page_with_text(text))

    assert kept == b""
    assert (result.retention, result.body_not_kept) == (
        Retention.EXCERPTS,
        BodyNotKept.VISIBLE_TEXT_DETAIL,
    )


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("sentence", ORDINARY_AT.values(), ids=ORDINARY_AT.keys())
def test_an_ordinary_sentence_with_an_at_sign_and_no_domain_keeps_its_body_unchanged(
    sentence: str,
) -> None:
    result, kept = _acquire_kept(page_with_text(sentence))

    assert (result.retention, result.body_not_kept) == (Retention.BODY, None)
    assert sentence.encode() in kept


# Fix round 5 (re-review 5 A R5-2): a link in the page's JSON is kept as written (an ID or a
# URL can look like a detail), so it is only looked at, its entities and percent-encoding
# decoded; a detail there means no body.
JSON_LINKS = {
    "a plain mailto: url": {"url": "mailto:jane@recruit.example"},
    "an entity-encoded url": {"url": "mailto:jane&#64;recruit.example"},
    "a percent-encoded sameAs": {"sameAs": "mailto:jane%40recruit.example"},
}


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("link", JSON_LINKS.values(), ids=JSON_LINKS.keys())
def test_a_json_ld_link_to_an_address_means_no_body(link: dict[str, str]) -> None:
    result, kept = _acquire_kept(page_with_block(json.dumps({**POSTING, **link})))

    assert kept == b""
    assert (result.retention, result.body_not_kept) == (
        Retention.EXCERPTS,
        BodyNotKept.LINK_DETAIL,
    )


@pytest.mark.req("ACQ-06")
def test_a_percent_encoded_mailto_link_with_no_visible_address_means_no_body() -> None:
    link = '<a href="mailto:jane%40recruit.example">Write to us</a>'

    result, kept = _acquire_kept(page_with_text(link))

    assert kept == b""
    assert (result.retention, result.body_not_kept) == (
        Retention.EXCERPTS,
        BodyNotKept.ATTRIBUTE_DETAIL,
    )


@pytest.mark.req("ACQ-06")
def test_an_entity_encoded_email_in_a_json_ld_string_leaves_the_body_and_its_excerpt() -> None:
    description = "<p>Email jane&#64;recruit.example for the details.</p>"

    result, kept = _acquire_kept(
        page_with_block(json.dumps({**POSTING, "description": description}))
    )

    assert (result.retention, result.body_not_kept) == (Retention.BODY, None)  # rewritten
    assert b"jane" not in kept
    assert b"recruit.example" not in kept
    [copy] = result.copies
    [claim] = [c for c in copy.claims if c.field is ClaimField.DESCRIPTION]
    assert claim.span.excerpt is not None
    assert "jane" not in claim.span.excerpt
    assert EMAIL_REMOVED in claim.span.excerpt


@pytest.mark.req("ACQ-06")
def test_an_entity_encoded_mailto_link_with_no_visible_address_means_no_body() -> None:
    # Fix round 4, item 1: the address is written as entities inside the link, so the page's
    # text holds no "@" for the text patterns, but a browser decodes it.
    link = '<a href="mailto:&#106;&#97;&#110;&#101;&#64;recruit&#46;example">Write to us</a>'

    result, kept = _acquire_kept(page_with_text(link))

    assert kept == b""
    assert (result.retention, result.body_not_kept) == (
        Retention.EXCERPTS,
        BodyNotKept.ATTRIBUTE_DETAIL,
    )


# Task 7 slice B, R6-1 (controller ruling): an image file extension is never an email's TLD,
# so an iOS-style name such as `logo@2x.png` is a path, not an address, in every place an
# employer page writes one.
IMAGE_NAMES = ["logo@2x.png", "hero@3x.webp", "icon@2x.svg", "photo@2x.jpeg", "Badge@2X.PNG"]
IMAGE_PLACES = {
    "a JSON-LD logo": lambda name: page_with_block(
        json.dumps(
            {
                **POSTING,
                "hiringOrganization": {"@type": "Organization", "logo": f"/media/{name}"},
            }
        )
    ),
    "a percent-encoded srcset": lambda name: page_with_text(
        f'<img alt="" srcset="/_next/image?url={quote("/media/" + name, safe="")}&amp;w=256 1x">'
    ),
    "a plain src": lambda name: page_with_text(f'<img alt="" src="/media/{name}">'),
    "a plain srcset": lambda name: page_with_text(
        f'<img alt="" srcset="/media/{name} 2x, /media/small.png 1x">'
    ),
}


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("name", IMAGE_NAMES)
def test_an_image_file_name_is_never_read_as_an_email_address(name: str) -> None:
    assert redact_text(f"/media/{name}") == f"/media/{name}"
    assert redact_shown(f"/media/{name} 2x") == f"/media/{name} 2x"


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("place", IMAGE_PLACES.values(), ids=IMAGE_PLACES.keys())
def test_an_image_named_at_2x_keeps_the_body_and_its_path(
    place: Callable[[str], bytes],
) -> None:
    result, kept = _acquire_kept(place("logo@2x.png"))

    assert (result.retention, result.body_not_kept) == (Retention.BODY, None)
    assert b"logo@2x.png" in kept or b"logo%402x.png" in kept
    assert EMAIL_REMOVED.encode() not in kept


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    "email",
    [
        "jane@recruit.example",
        "hr@northwind.co.uk",
        "jane@png.example",  # an image word as a label, not the TLD
        "jane@recruit.pngs",  # a TLD that only starts like an extension
        "a@b.jpg.example",  # an extension inside the domain, not at its end
    ],
)
def test_real_addresses_are_still_removed_beside_the_image_rule(email: str) -> None:
    assert redact_text(f"Write to {email} today.") == f"Write to {EMAIL_REMOVED} today."
    assert redact_shown(f"Write to {email} today.") == f"Write to {EMAIL_REMOVED} today."

    result, kept = _acquire_kept(page_with_text(f"Write to {email} today."))

    assert (result.retention, result.body_not_kept) == (Retention.BODY, None)
    assert email.encode() not in kept


def test_a_plain_mailto_link_loses_its_address_and_the_body_is_kept() -> None:
    # The control: an address the text patterns can see is removed in place.
    result, kept = _acquire_kept(
        page_with_text('<a href="mailto:jane@recruit.example">Write to us</a>')
    )

    assert (result.retention, result.body_not_kept) == (Retention.BODY, None)
    assert b"jane@recruit.example" not in kept
    assert f'href="mailto:{EMAIL_REMOVED}"'.encode() in kept


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    "space", [chr(0x00A0), chr(0x202F), chr(0x2009), "\t"], ids=["nbsp", "narrow", "thin", "tab"]
)
def test_a_number_spaced_with_horizontal_unicode_spaces_is_removed_and_the_body_kept(
    space: str,
) -> None:
    number = space.join(["0161", "496", "0000"])
    assert redact_text(f"Call {number} today.") == f"Call {PHONE_REMOVED} today."

    result, kept = _acquire_kept(page_with_text(f"Call {number} today."))

    assert (result.retention, result.body_not_kept) == (Retention.BODY, None)
    assert b"0161" not in kept
    assert PHONE_REMOVED.encode() in kept


def test_a_line_break_never_joins_a_number() -> None:
    # Only horizontal spaces separate a number's groups: text over several lines is several
    # values (a split number is caught once normalised, above).
    assert redact_text("Call 0161\n496\n0000 today.") == "Call 0161\n496\n0000 today."


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    "script",
    [
        'var d = "Call:\\x3e07700 900123";',  # re-review 3's probe case 15
        'var d = "Call:\\u{3e}07700 900123";',
        'var d = "Call:\\07607700 900123";',  # octal 076 is ">"
    ],
    ids=["\\x escape", "\\u{} escape", "octal escape"],
)
def test_a_script_hiding_a_detail_behind_a_javascript_escape_means_no_body(script: str) -> None:
    body = (
        f"<!doctype html><html><head>{SYNTHETIC_MARKER}<script>{script}</script></head>"
        "<body>x</body></html>"
    ).encode()

    result, kept = _acquire_kept(body)

    assert kept == b""
    assert result.body_not_kept is BodyNotKept.BLOCK_UNREDACTABLE


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize(
    "description",
    [
        "Call Jane on 07700 900123 or jane@recruit.example.",
        "Apply:\njane@recruit.example\nor call:\n07700 900123",  # escaped as \n in the JSON
        "<p>jane@recruit.example</p>\t07700 900123",  # json.dumps keeps < and >, \t escaped
    ],
    ids=["plain", "after newline escapes", "after a tag and a tab escape"],
)
def test_an_api_response_s_claims_hold_no_personal_details(description: str) -> None:
    body = json.dumps(
        {
            "count": 1,
            "results": [
                {
                    "id": "01234567890",
                    "title": "Data Quality Analyst",
                    "description": description,
                    "redirect_url": "https://www.adzuna.co.uk/jobs/land/ad/01234567890?se=s",
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

    assert result.status is AttemptStatus.SUCCEEDED  # the redacted response is still JSON
    [copy] = result.copies
    stored = json.dumps([c.model_dump(mode="json") for c in copy.claims])
    assert "07700" not in stored
    assert "jane@" not in stored
    assert copy.source_job_id == "01234567890"  # IDs and URLs are never redacted
    assert copy.apply_url == "https://www.adzuna.co.uk/jobs/land/ad/01234567890?se=s"
    assert result.retrieved_sha256 == hashlib.sha256(body).hexdigest()
    assert result.content_sha256 != result.retrieved_sha256
