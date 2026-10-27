"""Search persisted rows for secrets and private text, including base64-pickled values.

Findings name the location and the needle's label only, so a report never repeats the secret.
"""

import base64
import binascii
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

_BASE64_TOKEN = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
# Postgres bytea as rendered by row_to_json: "\\x" followed by hex digits.
_BYTEA_HEX = re.compile(r"\\\\x((?:[0-9a-f]{2})+)")


@dataclass(frozen=True)
class Needle:
    label: str
    value: str
    # When set, any substring of this length also counts (catches truncated echoes).
    fragment_length: int | None = None

    def __repr__(self) -> str:
        return f"Needle(label={self.label!r}, value=<redacted>)"

    def fragments(self) -> set[bytes]:
        encoded = self.value.encode()
        if self.fragment_length is None or self.fragment_length >= len(encoded):
            return {encoded}
        size = self.fragment_length
        return {encoded[i : i + size] for i in range(len(encoded) - size + 1)}


@dataclass(frozen=True)
class Finding:
    location: str
    needle_label: str
    match: Literal["exact", "fragment"]
    encoding: Literal["text", "base64", "hex"]


def _views(text: str) -> Iterable[tuple[Literal["text", "base64", "hex"], bytes]]:
    yield "text", text.encode()
    for digits in _BYTEA_HEX.findall(text):
        yield "hex", bytes.fromhex(digits)
    for token in _BASE64_TOKEN.findall(text):
        try:
            yield "base64", base64.b64decode(token, validate=True)
        except (binascii.Error, ValueError):
            continue


def scan(cells: Iterable[tuple[str, str]], needles: Sequence[Needle]) -> list[Finding]:
    """Return one finding per (location, needle) whose value or a fragment occurs."""
    findings: list[Finding] = []
    for location, text in cells:
        views = list(_views(text))
        for needle in needles:
            exact = needle.value.encode()
            fragments = needle.fragments()
            for encoding, haystack in views:
                if exact in haystack:
                    findings.append(Finding(location, needle.label, "exact", encoding))
                    break
                if any(fragment in haystack for fragment in fragments):
                    findings.append(Finding(location, needle.label, "fragment", encoding))
                    break
    return findings
