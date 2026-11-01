"""The DBOS worker's client for the restricted acquisition worker (ADR 0009).

Plain HTTP on the internal network, no proxy, bounded in time. The worker cannot be reached,
or answered with an error, is a transient failure: the DBOS step that called it owns the
retry (spec section 6, "DBOS owns bounded fetch retries").
"""

import json
import urllib.error
import urllib.request
from typing import Protocol

from pydantic import ValidationError

from careerwright.evidence.acquire import AcquisitionResult, AdzunaRequest, FetchRequest
from careerwright.evidence.adzuna import AdzunaQuery

# The worker's own bounds: robots.txt and the page each within the fetcher's 20 s, plus pacing.
REQUEST_TIMEOUT_S = 90.0


class AcquisitionUnavailableError(Exception):
    """The acquisition worker could not be reached or did not answer properly."""


class AcquisitionClient(Protocol):
    def fetch(self, url: str, *, read_text: bool = False) -> AcquisitionResult: ...

    def adzuna(self, query: AdzunaQuery) -> AcquisitionResult: ...


class HttpAcquisitionClient:
    def __init__(self, base_url: str, *, timeout_s: float = REQUEST_TIMEOUT_S) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_s
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _post(self, path: str, body: bytes) -> AcquisitionResult:
        request = urllib.request.Request(  # noqa: S310 - the internal worker's fixed base URL
            f"{self._base}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                payload = response.read()
        except (urllib.error.URLError, OSError, TimeoutError):
            raise AcquisitionUnavailableError from None
        try:
            return AcquisitionResult.model_validate(json.loads(payload))
        except (ValueError, ValidationError):
            raise AcquisitionUnavailableError from None

    def fetch(self, url: str, *, read_text: bool = False) -> AcquisitionResult:
        request = FetchRequest(url=url, read_text=read_text)
        return self._post("/v1/fetch", request.model_dump_json().encode())

    def adzuna(self, query: AdzunaQuery) -> AcquisitionResult:
        return self._post("/v1/adzuna", AdzunaRequest(query=query).model_dump_json().encode())
