"""Structured fields from a fetched page, first and deterministically (adapter: Scrapling's
parser; spec section 6: "Parse JSON-LD JobPosting, official JSON and stable selectors
first"; ACQ-03, ACQ-08).

Scrapling finds the page's JSON-LD blocks; each `JobPosting` in them becomes a job copy.
Every value is a claim whose span gives the character offsets of the value's literal in
the decoded page text that was hashed, with a minimal excerpt. A value that cannot be read
exactly (a salary that is not whole pence, an unsupported currency, a malformed date) is a
quarantined claim and the copy's value stays unknown: never guessed, never zero. Postings on
one page that disagree on a critical field are all marked with an extraction error, which
blocks their publication. Page text is data only: nothing in it is followed.

Adaptive element relocation is not used (spec section 6 allows it only as a candidate
match); source-specific selectors arrive with the template families Task 7b assigns.
"""

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import unquote, urlsplit

from scrapling.parser import Selector

from careerwright.evidence.addresses import apply_link
from careerwright.evidence.amounts import minor_units
from careerwright.evidence.jobs import advertiser_kind, description_fingerprints, title_key
from careerwright.evidence.records import (
    CLAIM_TEXT_CHARS,
    BodyNotKept,
    Claim,
    ClaimField,
    ClaimValue,
    DescriptionKind,
    Extraction,
    JobCopy,
    Location,
    PayBasis,
    Salary,
    SalaryPeriod,
    SourceSpan,
    ValidationState,
    WorkMode,
)
from careerwright.evidence.redaction import (
    link_strings,
    loads_json,
    redact_json,
    redact_shown,
    redact_text,
    redact_value,
    unescaped,
)

EXCERPT_CHARS = 200
LOCALITY_CHARS, POSTAL_CODE_CHARS, COUNTRY_CHARS = 120, 20, 60  # `records.Location`'s bounds
# The most of a page's visible text model extraction reads (`visible_text`): one advert's
# text fits, and the run's reservation is bounded by it (`careerwright.evidence.extraction`).
EXTRACTION_TEXT_BYTES = 8_000
# The most of a page's visible text role research checks a title against (`role_text`): no
# model reads it, so it is bounded only so one answer from the worker stays small.
ROLE_TEXT_BYTES = 200_000
_DECODER = json.JSONDecoder()
_COLON = re.compile(r"\s*:\s*")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_PERIODS = {p.value.upper(): p for p in SalaryPeriod}
_MISSING = object()


@dataclass(frozen=True)
class ParsedPage:
    sha256: str
    postings: list[JobCopy]
    extraction: Extraction | None = None  # why no posting could be published, if none could


@dataclass(frozen=True)
class _Block:
    index: int
    text: str
    offset: int | None  # where the block's text starts in the page, if found verbatim


def _locate(block: _Block, key: str, expected: object) -> tuple[int, int] | None:
    """The offsets of the literal that holds `expected` as the value of `key` in the block
    (a string's quotes excluded), relative to the page."""
    if block.offset is None:
        return None
    needle = json.dumps(key)
    position = 0
    while (found := block.text.find(needle, position)) != -1:
        after = found + len(needle)
        colon = _COLON.match(block.text, after)
        if colon is not None:
            start = colon.end()
            try:
                value, end = _DECODER.raw_decode(block.text, start)
            except ValueError:
                value = _MISSING
            if value == expected:
                if block.text[start] == '"':
                    start, end = start + 1, end - 1
                return block.offset + start, block.offset + end
        position = after
    return None


@dataclass
class _Claims:
    page: str
    sha256: str
    block: _Block
    claims: list[Claim] = field(default_factory=list)

    def add(
        self,
        field_name: ClaimField,
        value: ClaimValue,
        key: str,
        raw: object,
        *,
        issue: str | None = None,
    ) -> None:
        located = _locate(self.block, key, raw)
        if located is not None:
            start, end = located
            span = SourceSpan(
                source_sha256=self.sha256,
                start=start,
                end=end,
                excerpt=self.page[start:end][:EXCERPT_CHARS],
            )
        else:
            span = SourceSpan(
                source_sha256=self.sha256,
                pointer=f"/jsonld/{self.block.index}/{key}",
                excerpt=json.dumps(raw, ensure_ascii=False)[:EXCERPT_CHARS],
            )
        validation = ValidationState.QUARANTINED if issue else ValidationState.STRUCTURED
        self.claims.append(
            Claim(field=field_name, value=value, span=span, validation=validation, issue=issue)
        )


def _postings(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, list):
        for item in value:
            yield from _postings(item)
    elif isinstance(value, dict):
        kind = value.get("@type")
        kinds = kind if isinstance(kind, list) else [kind]
        if "JobPosting" in kinds:
            yield value
        elif "@graph" in value:
            yield from _postings(value["@graph"])


def _salary(raw: object) -> tuple[Salary | None, str | None]:
    if not isinstance(raw, dict):
        return None, "salary_invalid"
    currency = raw.get("currency")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        return None, "salary_invalid"
    value = raw.get("value")
    unit: object = raw.get("unitText")
    if isinstance(value, dict):
        low, high = value.get("minValue"), value.get("maxValue")
        unit = value.get("unitText", unit)
        if low is None and high is None:
            low = high = value.get("value")
    else:
        low = high = value
    amounts: list[int | None] = []
    for amount in (low, high):
        if amount is None:
            amounts.append(None)
            continue
        minor = minor_units(amount)
        if isinstance(minor, str):
            return None, minor
        amounts.append(minor)
    if amounts == [None, None]:
        return None, "salary_invalid"
    if currency != "GBP":
        return None, "currency_not_supported"
    period = _PERIODS.get(unit.upper()) if isinstance(unit, str) else None
    try:
        return (
            Salary(
                currency=currency,
                minimum_minor_units=amounts[0],
                maximum_minor_units=amounts[1],
                period=period,
                basis=PayBasis.ADVERTISED,
            ),
            None,
        )
    except ValueError:
        return None, "salary_invalid"


def _date(raw: object) -> date | None:
    if isinstance(raw, str) and _DATE.match(raw[:10]):
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None
    return None


def _until(raw: object) -> datetime | None:
    """A posting's expiry. A date alone expires at the start of that day (UTC), the earlier
    reading, so an expired posting is never shown as current; a time without a zone is UTC."""
    if not isinstance(raw, str):
        return None
    try:
        if _DATE.match(raw):
            day = date.fromisoformat(raw)
            return datetime(day.year, day.month, day.day, tzinfo=UTC)
        moment = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _host(url: object) -> str | None:
    if not isinstance(url, str):
        return None
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return None
    return host.lower().removeprefix("www.") if host else None


def _home_page_host(url: object) -> str | None:
    """The host of a link to a site's home page. A link deeper into a site (a job board's
    profile page for the advertiser, on the board's own host) says nothing about whose site
    it is (Task 7b, reproduced on the option pack's J01 and J12)."""
    if not isinstance(url, str):
        return None
    try:
        path = urlsplit(url).path
    except ValueError:
        return None
    return _host(url) if path in ("", "/") else None


def _hiring(posting: dict[str, Any]) -> tuple[str | None, object, list[str]]:
    """(name, the raw value holding it, hosts of the home pages it links) of the hiring
    organisation."""
    organisation = posting.get("hiringOrganization")
    if isinstance(organisation, str):
        return organisation.strip() or None, organisation, []
    if not isinstance(organisation, dict):
        return None, None, []
    name = organisation.get("name")
    links = organisation.get("sameAs")
    candidates = [*(links if isinstance(links, list) else [links]), organisation.get("url")]
    hosts = [h for h in (_home_page_host(c) for c in candidates) if h]
    return (name.strip() or None) if isinstance(name, str) else None, name, hosts


def _location(place: object) -> tuple[Location | None, str, object]:
    address = place.get("address") if isinstance(place, dict) else place
    if isinstance(address, str) and address.strip():
        return Location(label=address.strip()[:200]), "address", address
    if not isinstance(address, dict):
        return None, "address", address
    country = address.get("addressCountry")
    country = country.get("name") if isinstance(country, dict) else country

    def text(value: object, bound: int) -> str | None:
        """A part cut to its bound, like other claim text: a page cannot fail on its length
        (re-review A M-7)."""
        return (value.strip()[:bound] or None) if isinstance(value, str) else None

    locality = text(address.get("addressLocality"), LOCALITY_CHARS)
    region = text(address.get("addressRegion"), LOCALITY_CHARS)
    postal = text(address.get("postalCode"), POSTAL_CODE_CHARS)
    country = text(country, COUNTRY_CHARS)
    parts = [p for p in (locality, region) if p] or [p for p in (postal, country) if p]
    if not parts:
        return None, "address", address
    return (
        Location(
            label=", ".join(parts)[:200],
            locality=locality,
            region=region,
            postal_code=postal,
            country=country,
        ),
        "address",
        address,
    )


def _plain(html: str) -> str:
    return str(Selector(content=html).get_all_text(separator=" "))


def _copy(posting: dict[str, Any], claims: _Claims, page_host: str | None) -> JobCopy | None:
    title = posting.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    claims.add(ClaimField.TITLE, title.strip(), "title", title)

    identifier = posting.get("identifier")
    source_id = identifier.get("value") if isinstance(identifier, dict) else identifier
    # An ID longer than an excerpt is left unknown: cut short, it could match another's.
    if (
        isinstance(source_id, (str, int))
        and not isinstance(source_id, bool)
        and len(str(source_id)) <= CLAIM_TEXT_CHARS
    ):
        key = "value" if isinstance(identifier, dict) else "identifier"
        claims.add(ClaimField.SOURCE_JOB_ID, str(source_id), key, source_id)
        source_job_id: str | None = str(source_id)
    else:
        source_job_id = None

    employer, raw_employer, hiring_hosts = _hiring(posting)
    if employer is not None:
        key = (
            "name" if isinstance(posting.get("hiringOrganization"), dict) else "hiringOrganization"
        )
        claims.add(ClaimField.EMPLOYER, employer, key, raw_employer)
    on_own_site = page_host is not None and any(
        page_host == h or page_host.endswith(f".{h}") for h in hiring_hosts
    )

    places = posting.get("jobLocation")
    locations: list[Location] = []
    for place in places if isinstance(places, list) else ([places] if places else []):
        location, key, raw = _location(place)
        if location is not None:
            locations.append(location)
            claims.add(ClaimField.LOCATION, location, key, raw)

    work_mode = None
    if posting.get("jobLocationType") == "TELECOMMUTE":
        work_mode = WorkMode.REMOTE
        claims.add(ClaimField.WORK_MODE, work_mode.value, "jobLocationType", "TELECOMMUTE")

    salary = None
    if "baseSalary" in posting:
        salary, issue = _salary(posting["baseSalary"])
        claims.add(ClaimField.SALARY, salary, "baseSalary", posting["baseSalary"], issue=issue)

    posted = None
    if "datePosted" in posting:
        posted = _date(posting["datePosted"])
        claims.add(
            ClaimField.DATE_POSTED,
            posted,
            "datePosted",
            posting["datePosted"],
            issue=None if posted else "date_invalid",
        )
    until = None
    if "validThrough" in posting:
        until = _until(posting["validThrough"])
        claims.add(
            ClaimField.VALID_THROUGH,
            until.isoformat() if until else None,
            "validThrough",
            posting["validThrough"],
            issue=None if until else "date_invalid",
        )

    employment = posting.get("employmentType")
    employment_type = None
    if isinstance(employment, list) and all(isinstance(e, str) for e in employment) and employment:
        employment_type = ",".join(employment)
    elif isinstance(employment, str) and employment.strip():
        employment_type = employment.strip()
    if employment_type is not None:
        claims.add(ClaimField.EMPLOYMENT_TYPE, employment_type, "employmentType", employment)

    fingerprint = lead = None
    description = posting.get("description")
    if isinstance(description, str) and description.strip():
        fingerprint, lead = description_fingerprints(_plain(description))
        claims.add(ClaimField.DESCRIPTION, DescriptionKind.FULL.value, "description", description)

    # Untrusted: only a plain https link is kept (`addresses.apply_link`), and only one with
    # no third party's detail in it, decoded (fix round 5); anything else is no claim at all.
    apply_url = apply_link(posting.get("url"))
    if apply_url is not None and decoded_holds_detail(apply_url):
        apply_url = None
    if apply_url is not None:
        claims.add(ClaimField.APPLY_URL, apply_url, "url", posting["url"])

    return JobCopy(
        source_job_id=source_job_id,
        title=title.strip()[:CLAIM_TEXT_CHARS],
        employer=employer[:CLAIM_TEXT_CHARS] if employer else None,
        advertiser=advertiser_kind(employer, on_own_site=on_own_site),
        locations=locations[:20],
        work_mode=work_mode,
        salary=salary,
        date_posted=posted,
        valid_through=until,
        employment_type=employment_type[:60] if employment_type else None,
        description_kind=DescriptionKind.FULL if fingerprint else None,
        description_fingerprint=fingerprint,
        description_lead=lead,
        apply_url=apply_url,
        claims=claims.claims,
    )


def mark_conflicts(postings: list[JobCopy]) -> list[JobCopy]:
    """Postings for one title that disagree on salary, expiry, contract or employer are all
    marked: which is right cannot be decided by code, so none is published. Model extraction
    marks its postings by the same rule (`careerwright.evidence.extraction`)."""
    marked = []
    for job in postings:
        rivals = [
            p for p in postings if p is not job and title_key(p.title) == title_key(job.title)
        ]
        disagree = any(
            (a is not None and b is not None and a != b)
            for rival in rivals
            for a, b in (
                (job.salary, rival.salary),
                (job.valid_through, rival.valid_through),
                (job.employment_type, rival.employment_type),
                (job.employer, rival.employer),
            )
        )
        marked.append(
            job.model_copy(update={"extraction_error": "conflicting_job_postings"})
            if disagree
            else job
        )
    return marked


# JSON's escapes, and JavaScript's own (`\xNN`, `\u{...}`, octal): for detection only, never
# to rewrite a script (fix round 3, re-review 3 A R3-1). No JavaScript is parsed.
_ESCAPE = re.compile(
    r"\\(?:u\{([0-9a-fA-F]{1,6})\}|u([0-9a-fA-F]{4})|x([0-9a-fA-F]{2})|([0-7]{1,3})"
    r"|([nrtbfv/\\\"']))"
)
_ESCAPED = {
    "n": "\n",
    "r": "\n",
    "t": "\t",
    "b": " ",
    "f": " ",
    "v": " ",
    "/": "/",
    "\\": "\\",
    '"': '"',
    "'": "'",
}
_MAX_CODE_POINT = 0x10FFFF


def _unescaped(match: re.Match[str]) -> str:
    braced, unicode, hexadecimal, octal, single = match.groups()
    if single is not None:
        return _ESCAPED[single]
    code = int(octal, 8) if octal is not None else int(braced or unicode or hexadecimal, 16)
    return chr(code) if code <= _MAX_CODE_POINT else " "


def _holds_escaped_details(raw: str) -> bool:
    """Whether text that is not JSON holds an email or a telephone number once its escapes
    (JSON's and JavaScript's) are decoded."""
    decoded = _ESCAPE.sub(_unescaped, raw)
    return redact_text(decoded) != decoded


def normalised_text(plain: str) -> str:
    """Decoded text as a reader sees it: each run of whitespace of any kind (no-break spaces,
    line breaks, tabs) one space, and characters that do not print (a zero-width space, a
    soft hyphen) dropped, so a detail they split shows whole (fix round 3, review C I1)."""
    words = ("".join(ch for ch in word if ch.isprintable()) for word in plain.split())
    return " ".join(word for word in words if word)


def _shown_detail(shown: str) -> bool:
    return redact_shown(shown) != shown


def _shows_detail(html: str) -> bool:
    """Whether a page's visible text, normalised, still holds an email or a telephone
    number: then its markup hid one from the text patterns (an inline element splitting an
    email included, fix round 4, re-review 4 A R4-1), and its body is not kept."""
    return _shown_detail(normalised_text(_plain(html)))


def decoded_holds_detail(value: str) -> bool:
    """Detection only, never a rewrite: whether a value kept as written (an attribute's, a
    JSON link's) holds an email or a telephone number once its HTML entities and its
    percent-encoding are decoded and it is normalised (fix round 4, item 1; fix round 5,
    re-review 5 A R5-2). A browser decodes both: `mailto:jane%40recruit.example`."""
    decoded = unescaped(value)
    return any(_shown_detail(normalised_text(v)) for v in (decoded, unquote(decoded)))


def _attribute_shows_detail(html: str) -> bool:
    """Whether any attribute's value (its entities decoded by the parser) holds a detail
    once decoded (`decoded_holds_detail`): a `mailto:` link with no visible address."""
    return any(
        decoded_holds_detail(str(value)) for value in Selector(content=html).xpath("//@*").getall()
    )


def _links_show_detail(cleaned_json: str) -> bool:
    """Whether a JSON script's links (`redaction.LINK_KEYS`, kept as written) hold a detail
    once decoded: a JSON-LD `"url": "mailto:jane@recruit.example"`."""
    data, _ = loads_json(cleaned_json)
    return any(decoded_holds_detail(link) for link in link_strings(data))


@dataclass(frozen=True)
class RedactedPage:
    text: str  # line endings normalised, personal details removed: what is parsed and kept
    # Personal details that may remain, so the body must never be kept: a script holding
    # them could not be found in the page's text to be written again, a script holding them
    # is not JSON, so only its text could be redacted, the page's visible text, once
    # normalised, still shows one, or an attribute's decoded value holds one.
    unremovable: BodyNotKept | None


def redact_page(text: str) -> RedactedPage:
    """A page's text without third parties' personal details (`careerwright.evidence.redaction`).
    Line endings are normalised first (the parser reports a script's text with LF, so a
    CRLF page's scripts would not be found). Every script whose content is JSON (JSON-LD,
    an app's state) is redacted in its decoded values and written again when that, or a
    repeated key, changes it; a script that is not JSON, and the HTML around the scripts,
    are redacted as text (re-review A N-1). Then, fail safe, the result's visible text is
    normalised and looked at again: a detail the markup hid (an entity, a line break, an
    invisible character, an inline element splitting an email) means the body is not kept
    (fix round 3, review C I1; fix round 4, re-review 4 A R4-1); and so does one in an
    attribute's value once its entities are decoded (fix round 4, item 1)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    cursor = 0
    parts: list[str] = []
    unremovable: BodyNotKept | None = None
    for script in Selector(content=text).css("script"):
        raw = str(script.text)
        if not raw:
            continue
        cleaned = redact_json(raw)
        if cleaned is not None and _links_show_detail(cleaned):
            # Its links are kept as written, so a detail in one cannot be removed.
            unremovable = unremovable or BodyNotKept.LINK_DETAIL
        as_text = redact_text(raw) if cleaned is None else cleaned
        # Whether it holds details, looked for with escapes decoded too, since a detail right
        # after `\n` or `\x3e` is hidden from the text patterns.
        holds = as_text != raw or (cleaned is None and _holds_escaped_details(raw))
        offset = text.find(raw, cursor)
        if offset == -1:
            if holds:
                unremovable = unremovable or BodyNotKept.CONTACT_UNLOCATED
            continue
        if cleaned is None and holds:
            # A script that is not JSON (a JSON-LD block that does not parse, or code) and
            # holds details: text redaction cannot be trusted inside its escapes, so the
            # body is not kept (the ruling names JSON-LD; this holds for any script).
            unremovable = unremovable or BodyNotKept.BLOCK_UNREDACTABLE
        parts += [redact_text(text[cursor:offset]), as_text]
        cursor = offset + len(raw)
    parts.append(redact_text(text[cursor:]))
    redacted = "".join(parts)
    if unremovable is None and _shows_detail(redacted):
        unremovable = BodyNotKept.VISIBLE_TEXT_DETAIL
    if unremovable is None and _attribute_shows_detail(redacted):
        unremovable = BodyNotKept.ATTRIBUTE_DETAIL
    return RedactedPage(redacted, unremovable)


def parse_page(text: str, *, sha256: str, page_url: str) -> ParsedPage:
    """`text`: the decoded page whose bytes hashed to `sha256`; spans index into it."""
    page_host = _host(page_url)
    selector = Selector(content=text)
    postings: list[JobCopy] = []
    blocks = unreadable = 0
    cursor = 0
    for index, script in enumerate(selector.css('script[type="application/ld+json"]')):
        blocks += 1
        raw = str(script.text)
        offset = text.find(raw, cursor) if raw else -1
        if offset != -1:
            cursor = offset + len(raw)
        block = _Block(index, raw, offset if offset != -1 else None)
        try:
            # Claims come from redacted values, so a block that could not be rewritten in
            # the text (and so is cited by a pointer) still gives none (re-review A N-1).
            data = redact_value(json.loads(raw))
        except ValueError:
            unreadable += 1
            continue
        for posting in _postings(data):
            copy = _copy(posting, _Claims(text, sha256, block), page_host)
            if copy is not None:
                postings.append(copy)
            else:
                unreadable += 1
    marked = mark_conflicts(postings)
    return ParsedPage(sha256, marked, _extraction(marked, blocks=blocks, unreadable=unreadable))


def visible_text(text: str) -> str:
    """What model extraction reads of a redacted page (fix round 2, ruling 11; fix round 3,
    review C I1): its visible text (scripts and styles left out, entities decoded),
    normalised first (`normalised_text`), since decoding, collapsing whitespace and dropping
    what does not print can each reveal a detail; then with personal details removed, an
    email that inline markup split included (`redaction.redact_shown`; fix round 4,
    re-review 4 A R4-1); then cut to `EXTRACTION_TEXT_BYTES` of UTF-8. Spans index into
    exactly this text, and its hash is theirs."""
    return _shown(text, EXTRACTION_TEXT_BYTES)


def role_text(text: str) -> str:
    """What role research checks a title against (Task 6e; ADR 0015 decision 2): the page's
    visible text, normalised and without personal details as `visible_text` is, cut only at
    `ROLE_TEXT_BYTES`, since a title can be anywhere on the page. Text a reader never sees is
    left out (fix round 1, review M1): inside `<script>`, `<style>`, `<noscript>` or
    `<template>`, or an element marked `hidden` or styled `display: none` or `visibility:
    hidden` in its own `style` attribute (a style sheet's rules are not read). No model reads
    it, and it is never kept: only its hash, the span and the excerpt around it."""
    return _cut(redact_shown(normalised_text(_seen(text))), ROLE_TEXT_BYTES)


# Every text node without an ancestor a reader never sees (`role_text`). A `style` attribute is
# compared lower-cased and without spaces; `!important` and other declarations change nothing.
_STYLE = "translate(@style, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ \t\r\n', 'abcdefghijklmnopqrstuvwxyz')"
_SEEN_TEXT = (
    "//text()[not(ancestor::script or ancestor::style or ancestor::noscript "
    "or ancestor::template or ancestor::*[@hidden] "
    f"or ancestor::*[contains({_STYLE}, 'display:none')] "
    f"or ancestor::*[contains({_STYLE}, 'visibility:hidden')])]"
)


def _seen(html: str) -> str:
    """The page's text a reader sees, each text node apart, as `_plain` joins them."""
    nodes = (str(node) for node in Selector(content=html).xpath(_SEEN_TEXT))
    return " ".join(node for node in nodes if node.strip())


def _shown(text: str, limit: int) -> str:
    return _cut(redact_shown(normalised_text(_plain(text))), limit)


def _cut(text: str, limit: int) -> str:
    return text.encode()[:limit].decode(errors="ignore").rstrip()


def _extraction(postings: list[JobCopy], *, blocks: int, unreadable: int) -> Extraction | None:
    """Why the page gave no publishable posting, or None when it gave one."""
    if any(p.extraction_error is None for p in postings):
        return None
    if postings:
        return Extraction.CONFLICTING_JOB_POSTINGS
    if unreadable:
        return Extraction.JSONLD_INVALID
    return Extraction.NO_JOB_POSTING if blocks else Extraction.NO_STRUCTURED_DATA
