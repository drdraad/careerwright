"""The Adzuna job-search adapter's contract (ruling R4; spec section 6: "Preserve
`salary_is_predicted`; predicted pay is not employer-advertised pay. API descriptions may be
snippets"; JOB-05). Pure: the HTTP call is the acquisition worker's (`nessa.acquisition`).

Adzuna takes its credentials as query parameters, so the request is recorded without them
(`recorded_url`); only the acquisition worker's single HTTP call uses `transport_url`, and
`redact` strips them from any URL as a second line of defence. Each result becomes a job
copy whose every value is a claim pointing into the hashed response (a JSON pointer). Pay
keeps its basis: `salary_is_predicted` "1" is predicted, "0" advertised, and a missing or
unreadable flag unknown. Adzuna does not document a pay period, so none is recorded.
Descriptions are snippets and never become full descriptions.
"""

import html
import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, SecretStr

from nessa.evidence.amounts import minor_units
from nessa.evidence.jobs import advertiser_kind, description_fingerprints
from nessa.evidence.records import (
    Claim,
    ClaimField,
    ClaimValue,
    DescriptionKind,
    JobCopy,
    Location,
    PayBasis,
    Salary,
    SourceSpan,
    StrictModel,
    ValidationState,
)

SEARCH_URL = "https://api.adzuna.com/v1/api/jobs/gb/search/{page}"
CREDENTIAL_PARAMETERS = frozenset({"app_id", "app_key"})
EXCERPT_CHARS = 200
_TAG = re.compile(r"<[^>]+>")
_CONTRACT = {
    "full_time": "FULL_TIME",
    "part_time": "PART_TIME",
    "permanent": "PERMANENT",
    "contract": "CONTRACTOR",
}


class AdzunaQuery(StrictModel):
    """One bounded search: a role and a place, one page of at most 50 results."""

    what: str = Field(min_length=1, max_length=100)
    where: str = Field(min_length=1, max_length=100)
    page: int = Field(default=1, ge=1, le=10)
    results_per_page: int = Field(default=20, ge=1, le=50)

    def _parameters(self) -> list[tuple[str, str]]:
        return [
            ("what", self.what),
            ("where", self.where),
            ("results_per_page", str(self.results_per_page)),
        ]


def recorded_url(query: AdzunaQuery) -> str:
    """The request as Nessa records it: never with the credentials."""
    return f"{SEARCH_URL.format(page=query.page)}?{urlencode(query._parameters())}"


def transport_url(query: AdzunaQuery, app_id: SecretStr, app_key: SecretStr) -> str:
    """The URL sent to Adzuna. Only the acquisition worker builds it, for one HTTP call;
    it is never stored, logged or returned."""
    parameters = [
        ("app_id", app_id.get_secret_value()),
        ("app_key", app_key.get_secret_value()),
        *query._parameters(),
        ("content-type", "application/json"),
    ]
    return f"{SEARCH_URL.format(page=query.page)}?{urlencode(parameters)}"


def redact(url: str) -> str:
    """`url` without any credential parameter (in any letter case), the transport-only
    `content-type` parameter or a fragment."""
    parts = urlsplit(url)
    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in CREDENTIAL_PARAMETERS and k.lower() != "content-type"
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), ""))


@dataclass(frozen=True)
class SearchPage:
    copies: list[JobCopy] = field(default_factory=list)
    total: int | None = None  # Adzuna's count of matching adverts
    error: str | None = None  # a malformed response: an error, never an empty page


def _plain(text: str) -> str:
    return " ".join(html.unescape(_TAG.sub(" ", text)).split())


@dataclass
class _Claims:
    sha256: str
    index: int
    claims: list[Claim] = field(default_factory=list)

    def add(
        self,
        field_name: ClaimField,
        value: ClaimValue,
        key: str | None,
        raw: object,
        *,
        validation: ValidationState = ValidationState.STRUCTURED,
        issue: str | None = None,
    ) -> None:
        pointer = f"/results/{self.index}" + (f"/{key}" if key else "")
        span = SourceSpan(
            source_sha256=self.sha256,
            pointer=pointer,
            excerpt=json.dumps(raw, ensure_ascii=False)[:EXCERPT_CHARS],
        )
        self.claims.append(
            Claim(field=field_name, value=value, span=span, validation=validation, issue=issue)
        )


def _basis(flag: object) -> PayBasis:
    if flag in ("1", 1):
        return PayBasis.PREDICTED
    if flag in ("0", 0):
        return PayBasis.ADVERTISED
    return PayBasis.UNKNOWN


def _salary(result: dict[str, Any], claims: _Claims) -> Salary | None:
    low, high = result.get("salary_min"), result.get("salary_max")
    if low is None and high is None:
        return None
    raw = {k: result.get(k) for k in ("salary_min", "salary_max", "salary_is_predicted")}
    amounts: list[int | None] = []
    for amount in (low, high):
        minor = None if amount is None else minor_units(amount)
        if isinstance(minor, str):
            claims.add(
                ClaimField.SALARY,
                None,
                None,
                raw,
                validation=ValidationState.QUARANTINED,
                issue=minor,
            )
            return None
        amounts.append(minor)
    try:
        salary = Salary(
            currency="GBP",
            minimum_minor_units=amounts[0],
            maximum_minor_units=amounts[1],
            period=None,
            basis=_basis(result.get("salary_is_predicted")),
        )
    except ValueError:
        claims.add(
            ClaimField.SALARY,
            None,
            None,
            raw,
            validation=ValidationState.QUARANTINED,
            issue="salary_invalid",
        )
        return None
    claims.add(ClaimField.SALARY, salary, None, raw)
    return salary


def _copy(result: dict[str, Any], claims: _Claims) -> JobCopy | None:
    title = result.get("title")
    if not isinstance(title, str) or not _plain(title):
        return None
    title = _plain(title)[:300]
    claims.add(ClaimField.TITLE, title, "title", result["title"])
    source_id = result.get("id")
    source_job_id = str(source_id) if isinstance(source_id, (str, int)) else None
    if source_job_id is not None:
        claims.add(ClaimField.SOURCE_JOB_ID, source_job_id, "id", source_id)
    company = result.get("company")
    name = company.get("display_name") if isinstance(company, dict) else None
    employer = _plain(name)[:300] if isinstance(name, str) and _plain(name) else None
    if employer is not None:
        claims.add(ClaimField.EMPLOYER, employer, "company", company)
    locations: list[Location] = []
    place = result.get("location")
    if isinstance(place, dict) and isinstance(place.get("display_name"), str):
        listed = place.get("area")
        area: list[Any] = listed if isinstance(listed, list) else []
        location = Location(
            label=_plain(place["display_name"])[:200],
            locality=str(area[3])[:120] if len(area) > 3 else None,
            region=str(area[1])[:120] if len(area) > 1 else None,
            country=str(area[0])[:60] if area else None,
        )
        locations.append(location)
        claims.add(ClaimField.LOCATION, location, "location", place)
    salary = _salary(result, claims)
    created = result.get("created")
    posted = None
    if isinstance(created, str):
        try:
            posted = date.fromisoformat(created[:10])
        except ValueError:
            posted = None
        claims.add(
            ClaimField.DATE_POSTED,
            posted,
            "created",
            created,
            validation=ValidationState.STRUCTURED if posted else ValidationState.QUARANTINED,
            issue=None if posted else "date_invalid",
        )
    terms = [
        _CONTRACT[t]
        for t in (result.get("contract_time"), result.get("contract_type"))
        if isinstance(t, str) and t in _CONTRACT
    ]
    employment_type = ",".join(terms) or None
    if employment_type is not None:
        raw_terms = {k: result.get(k) for k in ("contract_time", "contract_type") if k in result}
        claims.add(ClaimField.EMPLOYMENT_TYPE, employment_type, None, raw_terms)
    lead = None
    description = result.get("description")
    if isinstance(description, str) and description.strip():
        _, lead = description_fingerprints(_plain(description))
        claims.add(
            ClaimField.DESCRIPTION, DescriptionKind.SNIPPET.value, "description", description
        )
    redirect = result.get("redirect_url")
    apply_url = redirect if isinstance(redirect, str) and redirect.startswith("https://") else None
    if apply_url is not None:
        claims.add(ClaimField.APPLY_URL, apply_url, "redirect_url", redirect)
    return JobCopy(
        source_job_id=source_job_id,
        title=title,
        employer=employer,
        advertiser=advertiser_kind(employer, on_own_site=False),
        locations=locations,
        salary=salary,
        date_posted=posted,
        employment_type=employment_type,
        description_kind=DescriptionKind.SNIPPET if description else None,
        description_lead=lead,
        apply_url=apply_url,
        claims=claims.claims,
    )


def parse_search(body: bytes, *, sha256: str) -> SearchPage:
    try:
        data = json.loads(body)
    except ValueError:
        return SearchPage(error="response_invalid")
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        return SearchPage(error="response_invalid")
    count = data.get("count")
    copies = [
        copy
        for index, result in enumerate(data["results"])
        if isinstance(result, dict) and (copy := _copy(result, _Claims(sha256, index))) is not None
    ]
    return SearchPage(copies, count if isinstance(count, int) else None)
