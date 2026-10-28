"""URL and address checks before any retrieval (spec section 6, "Retrieval pipeline and
security boundary"; ACQ-01). Pure: no network. The fetcher applies the same address check to
every address a name resolves to, after every redirect (`test_fetcher.py`)."""

import ipaddress

import pytest

from nessa.evidence.addresses import CheckedUrl, UrlRefusal, address_refusal, check_url


@pytest.mark.req("ACQ-01")
def test_a_public_https_url_is_normalised_and_its_fragment_dropped() -> None:
    checked = check_url("HTTPS://Careers.Example.org/jobs/42?ref=a#apply")

    assert checked == CheckedUrl(
        url="https://careers.example.org/jobs/42?ref=a",
        scheme="https",
        host="careers.example.org",
        port=443,
        ip_literal=None,
    )


@pytest.mark.req("ACQ-01")
@pytest.mark.parametrize(
    ("raw", "refusal"),
    [
        ("ftp://example.org/x", UrlRefusal.SCHEME_NOT_ALLOWED),
        ("file:///etc/passwd", UrlRefusal.SCHEME_NOT_ALLOWED),
        ("gopher://example.org:70/", UrlRefusal.SCHEME_NOT_ALLOWED),
        ("javascript:alert(1)", UrlRefusal.SCHEME_NOT_ALLOWED),
        ("https://user:pass@example.org/", UrlRefusal.CREDENTIALS_IN_URL),
        ("https://example.org@127.0.0.1/", UrlRefusal.CREDENTIALS_IN_URL),
        ("https:///no-host", UrlRefusal.HOST_NOT_ALLOWED),
        ("https://example.org:8080/", UrlRefusal.PORT_NOT_ALLOWED),
        ("https://example.org:22/", UrlRefusal.PORT_NOT_ALLOWED),
        ("https://localhost/", UrlRefusal.HOST_NOT_ALLOWED),
        ("https://api.localhost/", UrlRefusal.HOST_NOT_ALLOWED),
        ("http://postgres:5432/", UrlRefusal.PORT_NOT_ALLOWED),
        ("http://postgres/", UrlRefusal.HOST_NOT_ALLOWED),  # a single-label (Compose) name
        ("http://printer.local/", UrlRefusal.HOST_NOT_ALLOWED),
        ("http://metadata.google.internal/", UrlRefusal.HOST_NOT_ALLOWED),
        ("https://exa mple.org/", UrlRefusal.MALFORMED),
        ("https://example.org\\@127.0.0.1/", UrlRefusal.MALFORMED),
        ("https://" + "a" * 64 + ".org/", UrlRefusal.HOST_NOT_ALLOWED),
        ("https://example.org/" + "a" * 2100, UrlRefusal.URL_TOO_LONG),
        ("not a url", UrlRefusal.MALFORMED),
        ("example.org/jobs", UrlRefusal.SCHEME_NOT_ALLOWED),
    ],
)
def test_unsafe_or_unsupported_urls_are_refused_before_any_lookup(
    raw: str, refusal: UrlRefusal
) -> None:
    assert check_url(raw) is refusal


@pytest.mark.req("ACQ-01")
@pytest.mark.parametrize(
    "raw",
    [
        "http://127.0.0.1/",
        "http://10.0.0.5/",
        "http://172.16.3.4/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://100.64.0.1/",  # shared address space
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[fc00::1]/",
        "http://[fd00:ec2::254]/",  # cloud metadata over IPv6
        "http://[::ffff:127.0.0.1]/",  # IPv4-mapped loopback
        "http://[::ffff:7f00:1]/",  # the same, written in hex
        "http://[64:ff9b::a00:1]/",  # NAT64 of 10.0.0.1
        "http://[2002:7f00:1::]/",  # 6to4 of 127.0.0.1
        "http://[ff02::1]/",  # multicast
        "http://224.0.0.1/",
    ],
)
def test_private_loopback_link_local_and_metadata_literals_are_refused(raw: str) -> None:
    assert check_url(raw) is UrlRefusal.ADDRESS_NOT_ALLOWED


@pytest.mark.req("ACQ-01")
@pytest.mark.parametrize(
    "raw",
    [
        "http://2130706433/",  # 127.0.0.1 as one decimal number
        "http://0x7f000001/",  # as one hex number
        "http://0177.0.0.1/",  # octal first octet
        "http://0x7f.0.0.1/",  # hex first octet
        "http://127.1/",  # short form
        "http://127.0.0.1./",  # trailing dot
        "http://%31%32%37.0.0.1/",  # percent-encoded
        "http://①②⑦.0.0.1/",  # Unicode digits that IDNA would fold to 127
        "http://[::127.0.0.1]/",  # IPv4-compatible (deprecated) loopback
    ],
)
def test_encoded_address_forms_are_refused(raw: str) -> None:
    assert check_url(raw) in (UrlRefusal.HOST_NOT_ALLOWED, UrlRefusal.ADDRESS_NOT_ALLOWED)


@pytest.mark.req("ACQ-01")
def test_an_internationalised_name_is_checked_in_its_ascii_form() -> None:
    checked = check_url("https://bücher.example/stellen")

    assert isinstance(checked, CheckedUrl)
    assert checked.host == "xn--bcher-kva.example"
    assert checked.url == "https://xn--bcher-kva.example/stellen"


@pytest.mark.req("ACQ-01")
def test_a_public_ip_literal_is_allowed_and_kept_as_an_address() -> None:
    checked = check_url("http://[2606:4700::1111]/x")

    assert isinstance(checked, CheckedUrl)
    assert checked.ip_literal == ipaddress.ip_address("2606:4700::1111")
    assert checked.port == 80


@pytest.mark.req("ACQ-01")
@pytest.mark.parametrize(
    ("address", "refused"),
    [
        ("93.184.215.14", False),
        ("2606:2800:21f:cb07:6820:80da:af6b:8b2c", False),
        ("127.0.0.53", True),
        ("::", True),
        ("::ffff:10.1.2.3", True),
        ("::ffff:93.184.215.14", True),  # every embedded-IPv4 form is refused, public or not
        ("2001:db8::1", True),  # documentation
        ("198.18.0.1", True),  # benchmarking
        ("240.0.0.1", True),  # reserved
        ("255.255.255.255", True),
    ],
)
def test_the_address_check_refuses_every_non_public_address(address: str, refused: bool) -> None:
    assert (address_refusal(ipaddress.ip_address(address)) is not None) is refused
