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
from urllib.parse import urlsplit

from scrapling.parser import Selector

from nessa.evidence.addresses import apply_link
from nessa.evidence.amounts import minor_units
from nessa.evidence.jobs import advertiser_kind, description_fingerprints, title_key
from nessa.evidence.records import (
    Claim,
    ClaimField,
    ClaimValue,
    DescriptionKind,
    JobCopy,
    Location,
    PayBasis,
    Salary,
    SalaryPeriod,
    SourceSpan,
    ValidationState,
    WorkMode,
)
from nessa.evidence.redaction import redact_text, without_contacts

EXCERPT_CHARS = 200
_DECODER = json.JSONDecoder()
_COLON = re.compile(r"\s*:\s*")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_PERIODS = {p.value.upper(): p for p in SalaryPeriod}
_MISSING = object()


@dataclass(frozen=True)
class ParsedPage:
    sha256: str
    postings: list[JobCopy]
    issues: list[str] = field(default_factory=list)


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


def _hiring(posting: dict[str, Any]) -> tuple[str | None, object, list[str]]:
    """(name, the raw value holding it, hosts) of the hiring organisation."""
    organisation = posting.get("hiringOrganization")
    if isinstance(organisation, str):
        return organisation.strip() or None, organisation, []
    if not isinstance(organisation, dict):
        return None, None, []
    name = organisation.get("name")
    links = organisation.get("sameAs")
    candidates = [*(links if isinstance(links, list) else [links]), organisation.get("url")]
    hosts = [h for h in (_host(c) for c in candidates) if h]
    return (name.strip() or None) if isinstance(name, str) else None, name, hosts


def _location(place: object) -> tuple[Location | None, str, object]:
    address = place.get("address") if isinstance(place, dict) else place
    if isinstance(address, str) and address.strip():
        return Location(label=address.strip()[:200]), "address", address
    if not isinstance(address, dict):
        return None, "address", address
    country = address.get("addressCountry")
    country = country.get("name") if isinstance(country, dict) else country

    def text(key: str) -> str | None:
        value = address.get(key)
        return value.strip() or None if isinstance(value, str) else None

    locality, region, postal = text("addressLocality"), text("addressRegion"), text("postalCode")
    parts = [p for p in (locality, region) if p] or [p for p in (postal, country) if p]
    if not parts:
        return None, "address", address
    return (
        Location(
            label=", ".join(parts)[:200],
            locality=locality,
            region=region,
            postal_code=postal,
            country=country if isinstance(country, str) else None,
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
    if isinstance(source_id, (str, int)) and not isinstance(source_id, bool):
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

    # Untrusted: only a plain https link is kept (`addresses.apply_link`); anything else is
    # no claim at all.
    apply_url = apply_link(posting.get("url"))
    if apply_url is not None:
        claims.add(ClaimField.APPLY_URL, apply_url, "url", posting["url"])

    return JobCopy(
        source_job_id=source_job_id,
        title=title.strip()[:300],
        employer=employer[:300] if employer else None,
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


def _conflicts(postings: list[JobCopy]) -> list[JobCopy]:
    """Postings for one title that disagree on salary, expiry, contract or employer are all
    marked: which is right cannot be decided by code, so none is published."""
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


def redact_page(text: str) -> str:
    """A page's text without third parties' personal details (`nessa.evidence.redaction`):
    a JSON-LD block that names a contact is written again without it, every other block and
    all other text are kept as they were, then emails and telephone numbers go everywhere."""
    cursor = 0
    parts: list[str] = []
    for script in Selector(content=text).css('script[type="application/ld+json"]'):
        raw = str(script.text)
        offset = text.find(raw, cursor) if raw else -1
        if offset == -1:
            continue
        cleaned = without_contacts(raw)
        if cleaned is not None:
            parts += [text[cursor:offset], cleaned]
            cursor = offset + len(raw)
    parts.append(text[cursor:])
    return redact_text("".join(parts))


def parse_page(text: str, *, sha256: str, page_url: str) -> ParsedPage:
    """`text`: the decoded page whose bytes hashed to `sha256`; spans index into it."""
    page_host = _host(page_url)
    selector = Selector(content=text)
    postings: list[JobCopy] = []
    issues: list[str] = []
    cursor = 0
    for index, script in enumerate(selector.css('script[type="application/ld+json"]')):
        raw = str(script.text)
        offset = text.find(raw, cursor) if raw else -1
        if offset != -1:
            cursor = offset + len(raw)
        block = _Block(index, raw, offset if offset != -1 else None)
        try:
            data = json.loads(raw)
        except ValueError:
            issues.append("jsonld_invalid")
            continue
        for posting in _postings(data):
            copy = _copy(posting, _Claims(text, sha256, block), page_host)
            if copy is not None:
                postings.append(copy)
    if not postings and not issues:
        issues.append("no_structured_job_posting")
    return ParsedPage(sha256, _conflicts(postings), sorted(set(issues)))
