"""The acquisition pipeline the restricted acquisition worker runs for one source, and the
result it returns (spec section 6, "Retrieval pipeline and security boundary"; ADR 0009).

A page: its URL is checked, its host's manifest entry decides whether it may be fetched at
all (ACQ-06: a person supplying a URL never overrides it), robots.txt decides next, the host
is paced to its rate limit, and the page is fetched within the fetcher's bounds. Structured
fields are parsed, the page is classified under the session 1 rights policy by its final
host's manifest entry (never by what the page says about itself), and the body is returned
only when that class permits keeping it. An Adzuna search is one bounded API
request whose recorded URL never carries the credentials.

The worker holds no user secret, model key, master key or database access (GC8; ADR 0009):
it returns this result to the DBOS worker, which records it. Nothing here raises for a
source's failure: every outcome is a result with a status and a label.
"""

import base64
import hashlib
import math
import threading
import time
from collections.abc import Callable
from datetime import datetime

from pydantic import Field, SecretStr

from nessa.evidence import adzuna
from nessa.evidence.addresses import CheckedUrl, UrlRefusal
from nessa.evidence.adzuna import AdzunaQuery
from nessa.evidence.fetcher import JSON_TYPES, Admit, Fetched, Fetcher, FetchFailure
from nessa.evidence.pages import parse_page, redact_page
from nessa.evidence.records import (
    AttemptReason,
    AttemptStatus,
    BodyNotKept,
    Extraction,
    InputRoute,
    JobCopy,
    Retention,
    RightsClass,
    StrictModel,
)
from nessa.evidence.redaction import redact_json
from nessa.evidence.sources import Access, PageRights, classify_page, retention, rule_for

ADZUNA_PROVIDER = "adzuna"


class FetchRequest(StrictModel):
    url: str = Field(min_length=1, max_length=2_048)


class AdzunaRequest(StrictModel):
    query: AdzunaQuery


class AcquisitionResult(StrictModel):
    """One attempt's outcome, as the restricted worker reports it. URLs are as recorded:
    never with a credential."""

    route: InputRoute
    provider: str
    requested_url: str | None  # None for a URL refused by the checks: never recorded
    final_url: str | None = None
    redirects: list[str] = Field(default_factory=list)  # checked URLs only
    status: AttemptStatus
    reason: AttemptReason | None = None
    transient: bool = False
    http_status: int | None = None
    content_type: str | None = None
    address: str | None = None
    content_sha256: str | None = None  # of what was kept: personal details removed
    retrieved_sha256: str | None = None  # of the bytes as retrieved, for change detection
    byte_count: int | None = None
    rights_class: RightsClass | None = None
    rights_status: str | None = None
    retention: Retention | None = None
    # Why a body its class may keep was not kept (personal details could not be removed).
    body_not_kept: BodyNotKept | None = None
    body_b64: str | None = None  # only when the rights class permits keeping the body
    copies: list[JobCopy] = Field(default_factory=list)
    # A retrieved source with no publishable posting says why; only `no_job_posting` may
    # count as "none found".
    extraction: Extraction | None = None
    total: int | None = Field(default=None, ge=0)  # Adzuna's count of matching adverts
    http_requests: int = Field(default=0, ge=0)  # sent for it, robots.txt included
    fetched_at: datetime


class Pacer:
    """At most one request per host per its manifest rate limit (spec section 6: rate
    limits respected), across the worker's threads."""

    def __init__(
        self,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._clock = clock
        self._sleep = sleep
        self._next: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, host: str, interval_s: float, *, within_s: float = math.inf) -> bool:
        """Waits for the host's next slot and takes it; or, when that slot is more than
        `within_s` away, takes nothing, waits not at all and answers False."""
        with self._lock:
            now = self._clock()
            start = max(now, self._next.get(host, now))
            if start - now > within_s:
                return False
            self._next[host] = start + interval_s
        if start > now:
            self._sleep(start - now)
        return True


def _failure_result(
    route: InputRoute, provider: str, url: str, failure: FetchFailure, now: datetime
) -> AcquisitionResult:
    return AcquisitionResult(
        route=route,
        provider=provider,
        requested_url=url,
        final_url=failure.final_url,
        redirects=list(failure.redirects),
        status=failure.outcome,
        reason=failure.reason,
        transient=failure.transient,
        http_status=failure.http_status,
        address=failure.address,
        http_requests=failure.requests,
        fetched_at=now,
    )


def admission(pacer: Pacer) -> Admit:
    """The source permission manifest for each host a page fetch reaches, the first and
    every redirect's (ACQ-06): a denied or API-only host is refused before any request to
    it; a permitted one is paced to its rate limit, unless its next slot is past what is left
    of the page's time bound: then it is a transient timeout, with no wait and no slot taken."""

    def admit(checked: CheckedUrl, within_s: float) -> str | None:
        rule = rule_for(checked.host)
        if rule.access is Access.DENIED:
            return AttemptReason.SOURCE_DENIED.value
        if rule.access is Access.API_ONLY:
            return AttemptReason.SOURCE_API_ONLY.value
        if not pacer.wait(checked.host, rule.rate_limit_seconds, within_s=within_s):
            return AttemptReason.TIMEOUT.value
        return None

    return admit


def acquire_page(
    fetcher: Fetcher,
    pacer: Pacer,
    url: str,
    *,
    now: datetime,
    classify: Callable[[str], PageRights] = classify_page,
) -> AcquisitionResult:
    """`classify`: the page's class from its final host; the manifest's, except where the
    corpus tool records an agent's classification (`tools.corpus`). A refused URL is
    recorded without it: only a checked URL is ever recorded as one."""
    checked = fetcher.check(url)
    if isinstance(checked, UrlRefusal):
        return AcquisitionResult(
            route=InputRoute.FETCH,
            provider="unknown",
            requested_url=None,
            status=AttemptStatus.BLOCKED,
            reason=checked.value,
            fetched_at=now,
        )
    result = fetcher.fetch_page(checked.url, admission(pacer))
    if isinstance(result, FetchFailure):
        return _failure_result(InputRoute.FETCH, checked.host, checked.url, result, now)
    return _page_result(fetcher, result, checked.host, now, classify)


def _page_result(
    fetcher: Fetcher,
    page: Fetched,
    host: str,
    now: datetime,
    classify: Callable[[str], PageRights],
) -> AcquisitionResult:
    # Third parties' personal details go first, so the hash that spans index into, the
    # claims and any kept body are all without them; the retrieved bytes keep their own hash.
    redacted = redact_page(page.text)
    text = redacted.text
    kept = text.encode()
    digest = hashlib.sha256(kept).hexdigest()
    parsed = parse_page(text, sha256=digest, page_url=page.final_url)
    final_host = fetcher.check(page.final_url)
    rights = classify(final_host.host if not isinstance(final_host, UrlRefusal) else host)
    body_not_kept = None
    if redacted.unremovable is not None and rights.retention is Retention.BODY:
        # Fail safe: personal details may remain in a block that could not be rewritten.
        rights = PageRights(rights.rights_class, rights.rights_status, Retention.EXCERPTS)
        body_not_kept = redacted.unremovable
    keep = rights.retention is Retention.BODY
    return AcquisitionResult(
        route=InputRoute.FETCH,
        provider=host,
        requested_url=page.requested_url,
        final_url=page.final_url,
        redirects=list(page.redirects),
        status=AttemptStatus.SUCCEEDED,
        http_status=page.status,
        content_type=page.content_type,
        address=page.address,
        content_sha256=digest,
        retrieved_sha256=hashlib.sha256(page.body).hexdigest(),
        byte_count=len(kept),
        rights_class=rights.rights_class,
        rights_status=rights.rights_status,
        retention=rights.retention,
        body_not_kept=body_not_kept,
        body_b64=base64.b64encode(kept).decode() if keep else None,
        copies=parsed.postings,
        extraction=parsed.extraction,
        http_requests=page.requests,
        fetched_at=now,
    )


def acquire_adzuna(
    fetcher: Fetcher,
    pacer: Pacer,
    query: AdzunaQuery,
    credentials: tuple[SecretStr, SecretStr] | None,
    *,
    now: datetime,
    search_url: str = adzuna.SEARCH_URL,
) -> AcquisitionResult:
    """One Adzuna search page. The credentialed URL exists only for this call; the result
    carries the recorded URL and no redirect, final URL or address that could echo it.
    `search_url` is Adzuna's; only the fixture server's replaces it, in tests."""
    recorded = adzuna.recorded_url(query, search_url)
    rule = rule_for("api.adzuna.com")
    base = {
        "route": InputRoute.ADZUNA,
        "provider": ADZUNA_PROVIDER,
        "requested_url": recorded,
        "rights_class": rule.rights_class,
        "fetched_at": now,
    }
    if credentials is None:
        return AcquisitionResult(
            **base, status=AttemptStatus.BLOCKED, reason="adzuna_credentials_not_configured"
        )
    pacer.wait("api.adzuna.com", rule.rate_limit_seconds)
    result = fetcher.fetch(adzuna.transport_url(query, *credentials, search_url), accept=JSON_TYPES)
    if isinstance(result, FetchFailure):
        return AcquisitionResult(
            **base,
            status=result.outcome,
            reason=result.reason,
            transient=result.transient,
            http_status=result.http_status,
            http_requests=result.requests,
        )
    # Redacted in its decoded values, so it stays JSON; text that is not JSON is left for the
    # parser to report (`response_invalid`).
    stripped = adzuna.without_app_id(result.text, credentials[0].get_secret_value())
    kept = (redact_json(stripped) or stripped).encode()
    digest = hashlib.sha256(kept).hexdigest()
    page = adzuna.parse_search(kept, sha256=digest)
    rights = classify_page("api.adzuna.com")
    common = {
        **base,
        "http_requests": result.requests,
        "http_status": result.status,
        "content_type": result.content_type,
        "content_sha256": digest,
        "retrieved_sha256": hashlib.sha256(result.body).hexdigest(),
        "byte_count": len(kept),
        "rights_status": rights.rights_status,
        "retention": retention(rule.rights_class),
    }
    if page.error is not None:
        return AcquisitionResult(**common, status=AttemptStatus.FAILED, reason=page.error)
    return AcquisitionResult(
        **common,
        status=AttemptStatus.SUCCEEDED,
        copies=page.copies,
        total=page.total,
        extraction=_adzuna_extraction(page),
    )


def _adzuna_extraction(page: adzuna.SearchPage) -> Extraction | None:
    """Only Adzuna's own count of none says no advert matched; results it returned that
    could not be read, or an empty page of a search that matched some, say nothing."""
    if page.copies:
        return None
    return Extraction.NO_MATCHING_ADVERTS if page.total == 0 else Extraction.NO_JOB_POSTING
