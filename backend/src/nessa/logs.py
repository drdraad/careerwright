"""Structured JSON logs that hold identifiers and error classes, never secrets (spec section 19).

The primary rule is structural: code logs record IDs and labels only. The formatter adds
defence in depth: it drops exception messages (keeping the class and the stack frames),
and scrubs bearer tokens, JWTs, URL passwords and every secret the process registered.
"""

import json
import logging
import re
import sys
import traceback
from datetime import UTC, datetime
from types import TracebackType

_JWT = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*")
_BEARER = re.compile(r"(?i)(bearer\s+)\S+")
_URL_PASSWORD = re.compile(r"(://[^/\s:@]+:)[^@\s/]+@")
_STANDARD_ATTRIBUTES = frozenset(
    set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime", "taskName"}
)
_secrets: set[str] = set()
QUIET_LOGGERS = ("httpx", "httpx2", "httpcore", "openai", "urllib3", "google", "firebase_admin")


def register_secret(value: str) -> None:
    """Scrub this exact value from every later log line (process secrets such as passwords)."""
    if len(value) >= 8:
        _secrets.add(value)


def redact(text: str) -> str:
    for secret in _secrets:
        text = text.replace(secret, "[redacted]")
    text = _JWT.sub("[redacted-token]", text)
    text = _BEARER.sub(r"\1[redacted]", text)
    return _URL_PASSWORD.sub(r"\1[redacted]@", text)


def _frames(tb: TracebackType | None) -> list[str]:
    return [
        f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in traceback.extract_tb(tb)
    ]


class JsonFormatter(logging.Formatter):
    def __init__(self, *, service: str) -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "service": self._service,
            "logger": record.name,
            "msg": redact(record.getMessage()),
        }
        for key, value in vars(record).items():
            if key not in _STANDARD_ATTRIBUTES and not key.startswith("_"):
                entry[key] = redact(str(value))
        if record.exc_info and record.exc_info[0] is not None:
            # The class and the frames locate the fault; the message could quote anything.
            entry["error_class"] = record.exc_info[0].__name__
            entry["stack"] = [redact(frame) for frame in _frames(record.exc_info[2])]
        return json.dumps(entry, sort_keys=True)


def configure_logging(service: str, level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service=service))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    # DBOS and uvicorn install their own handlers; route them through ours instead.
    for name in ("dbos", "uvicorn", "uvicorn.error"):
        third_party = logging.getLogger(name)
        third_party.handlers[:] = []
        third_party.propagate = True
    logging.getLogger("uvicorn.access").disabled = True  # the API writes its own access log
