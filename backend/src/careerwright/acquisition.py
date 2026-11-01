"""The restricted acquisition worker (entry point; spec section 6, "Acquisition workers
receive no user profile or model key"; Global Constraint 8; ADR 0009).

A small HTTP service on the internal network, called only by the DBOS worker. It fetches one
permitted page, or runs one Adzuna search, per request (`careerwright.evidence.acquire`) and
returns the result; it records nothing. It has no database connection, master key, Meta key
or profile: its configuration has no setting for any of them, and Compose gives it no such
secret or mount. In live mode it alone has a route out for pages and Adzuna. The one
credential it may hold is Adzuna's, read from `CAREERWRIGHT_ADZUNA_CREDENTIALS_DIR` (placed under
`CAREERWRIGHT_HOME` by setup), registered for log redaction and used only to build one request.

Run: `python -m careerwright.acquisition`; health check:
`python -m careerwright.acquisition --check`.
"""

import json
import logging
import sys
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from careerwright.evidence import adzuna
from careerwright.evidence.acquire import (
    ADZUNA_PROVIDER,
    AcquisitionResult,
    AdzunaRequest,
    FetchRequest,
    Pacer,
    acquire_adzuna,
    acquire_page,
)
from careerwright.evidence.addresses import CheckedUrl, check_url
from careerwright.evidence.fetcher import Fetcher
from careerwright.evidence.records import AttemptReason, AttemptStatus, InputRoute
from careerwright.evidence.sources import load_manifest
from careerwright.logs import configure_logging, register_secret

DEFAULT_PORT = 8100
MAX_REQUEST_BYTES = 16_384
# Placed by `make setup` from `.env`'s `ADZUNA_APPLICATION_ID` and `ADZUNA_API_KEY`.
ADZUNA_ID_FILE = "adzuna_application_id"
ADZUNA_KEY_FILE = "adzuna_api_key"
_log = logging.getLogger("careerwright.acquisition")


class AcquisitionSettings(BaseSettings):
    """Everything the restricted worker is configured with. There is deliberately no
    database, master-key or model setting."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    environment: Literal["local"] = Field(validation_alias="CAREERWRIGHT_ENVIRONMENT")
    port: int = Field(
        default=DEFAULT_PORT, ge=1, le=65535, validation_alias="CAREERWRIGHT_ACQUISITION_PORT"
    )
    adzuna_credentials_dir: Path | None = Field(
        default=None, validation_alias="CAREERWRIGHT_ADZUNA_CREDENTIALS_DIR"
    )
    # The fetcher's proxy mode is the controller's tools' alone (ADR 0009, 2026-11-01
    # amendment): a value here is refused at start, never ignored.
    fetch_proxy: None = Field(default=None, validation_alias="CAREERWRIGHT_FETCH_PROXY")


def load_adzuna_credentials(directory: Path | None) -> tuple[SecretStr, SecretStr] | None:
    """Both Adzuna credentials, or None if either is missing. Registered for redaction at
    once; never printed."""
    if directory is None:
        return None
    try:
        app_id = (directory / ADZUNA_ID_FILE).read_text(encoding="utf-8").strip()
        app_key = (directory / ADZUNA_KEY_FILE).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not app_id or not app_key:
        return None
    register_secret(app_id)
    register_secret(app_key)
    return SecretStr(app_id), SecretStr(app_key)


def internal_failure(request: FetchRequest | AdzunaRequest, now: datetime) -> AcquisitionResult:
    """The attempt a defect ends: recorded against what was asked for, as far as it is safe
    to record (a checked URL, or the Adzuna request without its credentials)."""
    if isinstance(request, AdzunaRequest):
        route, provider = InputRoute.ADZUNA, ADZUNA_PROVIDER
        requested: str | None = adzuna.recorded_url(request.query)
    else:
        checked = check_url(request.url)
        route = InputRoute.FETCH
        provider = checked.host if isinstance(checked, CheckedUrl) else "unknown"
        requested = checked.url if isinstance(checked, CheckedUrl) else None
    return AcquisitionResult(
        route=route,
        provider=provider,
        requested_url=requested,
        status=AttemptStatus.FAILED,
        reason=AttemptReason.INTERNAL_ERROR,
        fetched_at=now,
    )


class AcquisitionService:
    def __init__(
        self,
        fetcher: Fetcher,
        *,
        credentials: tuple[SecretStr, SecretStr] | None,
        pacer: Pacer | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        adzuna_search_url: str = adzuna.SEARCH_URL,  # only a test's fixture server replaces it
    ) -> None:
        self._fetcher = fetcher
        self._credentials = credentials
        self._pacer = pacer or Pacer()
        self._clock = clock
        self._adzuna_search_url = adzuna_search_url

    @property
    def adzuna_configured(self) -> bool:
        return self._credentials is not None

    def handle(self, path: str, body: bytes) -> tuple[int, dict[str, object]]:
        """Only a malformed request is a 422. A failure while acquiring (a defect, never the
        source's fault) is answered as the attempt it is: failed `internal_error`, not
        transient, so the client never takes it for this worker being unavailable."""
        try:
            if path == "/v1/fetch":
                request: FetchRequest | AdzunaRequest = FetchRequest.model_validate_json(body)
            elif path == "/v1/adzuna":
                request = AdzunaRequest.model_validate_json(body)
            else:
                return 404, {"error": "not_found"}
        except ValidationError:
            return 422, {"error": "invalid_request"}
        now = self._clock()
        try:
            if isinstance(request, FetchRequest):
                result: AcquisitionResult = acquire_page(
                    self._fetcher, self._pacer, request.url, now=now, read_text=request.read_text
                )
            else:
                result = acquire_adzuna(
                    self._fetcher,
                    self._pacer,
                    request.query,
                    self._credentials,
                    now=now,
                    search_url=self._adzuna_search_url,
                )
        except Exception as error:  # its class only, never its message
            _log.warning("acquisition failed", extra={"error_class": type(error).__name__})
            result = internal_failure(request, now)
        return 200, json.loads(result.model_dump_json())


def make_server(service: AcquisitionService, host: str, port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:  # paths only, below
            return

        def _send(self, status: int, payload: dict[str, object]) -> None:
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/healthz":
                self._send(200, {"status": "ok"})
            else:
                self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:
            declared = self.headers.get("Content-Length") or "0"
            if not (declared.isascii() and declared.isdigit()):  # negative or not a number
                self.close_connection = True
                self._send(400, {"error": "invalid_content_length"})
                return
            length = int(declared)
            if length > MAX_REQUEST_BYTES:
                self._send(413, {"error": "request_too_large"})
                return
            body = self.rfile.read(length)
            try:
                status, payload = service.handle(self.path, body)
            except Exception as error:  # a defect: its class only, never its message
                _log.warning(
                    "acquisition request failed", extra={"error_class": type(error).__name__}
                )
                status, payload = 500, {"error": "internal"}
            _log.info("acquisition request", extra={"path": self.path, "status": status})
            self._send(status, payload)

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def check(port: int = DEFAULT_PORT) -> int:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=2) as response:
            return 0 if response.status == 200 else 1
    except OSError:
        return 1


def main() -> None:
    if sys.argv[1:] == ["--check"]:
        sys.exit(check())
    configure_logging("acquisition")
    settings = AcquisitionSettings()
    manifest = load_manifest()  # fail closed on an unreadable source manifest
    fetcher = Fetcher(user_agent=manifest.user_agent)  # production: no extra origins, no proxy
    service = AcquisitionService(
        fetcher, credentials=load_adzuna_credentials(settings.adzuna_credentials_dir)
    )
    server = make_server(service, "0.0.0.0", settings.port)  # noqa: S104 - internal network only
    _log.info("acquisition worker ready", extra={"adzuna": service.adzuna_configured})
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
