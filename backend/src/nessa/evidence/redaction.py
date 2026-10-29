"""Third parties' personal details removed from what is kept (session 1, "always true": "a
third party's personal details (recruiter names, phone numbers) never kept"; ADR 0009
decision 4). Pure and deterministic.

Applied to a retrieved page or API response before anything is hashed for spans, parsed
into claims or sealed, so bodies, excerpts and claim values all go without them:

- email addresses, anywhere;
- telephone numbers in UK national form (`020 7946 0958`, `(0161) 496 0000`,
  `07700 900123`) and international form (`+44 (0)20 7946 0958`, `+1 555 123 4567`), not
  inside a URL, a word or a longer number;
- in a page's JSON-LD, every name, email, telephone and fax number of an
  `applicationContact` or `contactPoint`.

A personal name in running text cannot be told apart from other words deterministically,
so it is not removed: a known limit, recorded in ADR 0009 for the product owner. A page's
JSON-LD blocks are found by the parser (`pages.redact_page`).
"""

import json
import re
from typing import Any

EMAIL_REMOVED = "[email removed]"
PHONE_REMOVED = "[phone removed]"
CONTACT_REMOVED = "[contact removed]"
CONTACT_KEYS = frozenset({"applicationContact", "contactPoint"})
CONTACT_FIELDS = frozenset({"name", "email", "telephone", "faxNumber"})

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
# Not preceded by a word character or anything that would put it inside a URL or a number.
_NOT_INSIDE = r"(?<![\w/=?&#%.+-])"
_PHONE = re.compile(
    _NOT_INSIDE
    + r"(?:\+\d{1,3}(?:[ .-]?\(0\))?(?:[ .-]?\(?\d{1,5}\)?){2,6}"  # international
    + r"|\(?0\d{2,4}\)?(?:[ .-]?\d{3,4}){2})"  # UK national
    + r"(?![\w/])"
)
_INTERNATIONAL_DIGITS = range(8, 16)
_NATIONAL_DIGITS = range(10, 12)


def _phone(match: re.Match[str]) -> str:
    found = match.group()
    digits = sum(c.isdigit() for c in found)
    allowed = _INTERNATIONAL_DIGITS if found.startswith("+") else _NATIONAL_DIGITS
    return PHONE_REMOVED if digits in allowed else found


def redact_text(text: str) -> str:
    """Email addresses and telephone numbers removed."""
    return _PHONE.sub(_phone, _EMAIL.sub(EMAIL_REMOVED, text))


def _without_contacts(value: Any) -> tuple[Any, bool]:
    if isinstance(value, list):
        items = [_without_contacts(item) for item in value]
        return [item for item, _ in items], any(changed for _, changed in items)
    if not isinstance(value, dict):
        return value, False
    out: dict[str, Any] = {}
    changed = False
    for key, item in value.items():
        if key in CONTACT_KEYS:
            item, removed = _contact(item)
            changed = changed or removed
        else:
            item, removed = _without_contacts(item)
            changed = changed or removed
        out[key] = item
    return out, changed


def _contact(value: Any) -> tuple[Any, bool]:
    if isinstance(value, list):
        items = [_contact(item) for item in value]
        return [item for item, _ in items], any(changed for _, changed in items)
    if not isinstance(value, dict):
        return (CONTACT_REMOVED, True) if isinstance(value, str) else (value, False)
    out = {
        key: CONTACT_REMOVED if key in CONTACT_FIELDS and isinstance(item, str) else item
        for key, item in value.items()
    }
    return out, out != value


def without_contacts(raw: str) -> str | None:
    """A JSON-LD block's text written again without its contacts, or None when it names
    none (or is not JSON) and stays as it was."""
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    cleaned, changed = _without_contacts(data)
    return json.dumps(cleaned, ensure_ascii=False, indent=2) if changed else None
