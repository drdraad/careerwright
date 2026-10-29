"""Third parties' personal details removed from what is kept (session 1, "always true": "a
third party's personal details (recruiter names, phone numbers) never kept"; ADR 0009
decision 4). Pure and deterministic.

Applied to a retrieved page, an API response or pasted text before anything is hashed for
spans, parsed into claims or sealed. What it removes:

- email addresses;
- telephone numbers in UK national form (`020 7946 0958`, `(0161) 496 0000`,
  `07700 900123`) and international form (`+44 (0)20 7946 0958`, `+1 555 123 4567`), not
  inside a URL, a word or a longer number;
- in JSON (a page's JSON-LD, Adzuna's response), every name, email, telephone and fax
  number of an `applicationContact` or `contactPoint`.

JSON is redacted in its decoded values, never as raw text: a value's escapes (`\\n`,
`\\u003e`) are decoded first, so a detail right after one is still found and the JSON stays
valid. IDs and URLs are never redacted (`NOT_TEXT`): an ID can look like a phone number.

A personal name in running text cannot be told apart from other words deterministically,
so it is not removed; nor is a detail written in an unusual form (an email as HTML entities,
a number spelt out). These are known limits, recorded in ADR 0009 for the product owner. A
page's JSON-LD blocks are found by the parser (`pages.redact_page`).
"""

import json
import re
from typing import Any

EMAIL_REMOVED = "[email removed]"
PHONE_REMOVED = "[phone removed]"
CONTACT_REMOVED = "[contact removed]"
CONTACT_KEYS = frozenset({"applicationContact", "contactPoint"})
CONTACT_FIELDS = frozenset({"name", "email", "telephone", "faxNumber"})
# Keys whose values are identifiers or links, never text: kept exactly (re-review A M-1).
NOT_TEXT = frozenset(
    {"@context", "@id", "@type", "identifier", "url", "sameAs", "logo", "image"}
    | {"id", "adref", "redirect_url", "__CLASS__"}  # Adzuna's
)

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
    """Email addresses and telephone numbers removed from plain text."""
    return _PHONE.sub(_phone, _EMAIL.sub(EMAIL_REMOVED, text))


def redact_value(value: Any) -> Any:
    """A decoded JSON value with personal details removed: a contact's fields replaced, every
    other string's emails and telephone numbers removed, IDs and URLs kept as they are."""
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    if not isinstance(value, dict):
        return value
    out: dict[str, Any] = {}
    for key, item in value.items():
        if key in NOT_TEXT:
            out[key] = item
        elif key in CONTACT_KEYS:
            out[key] = _contact(item)
        else:
            out[key] = redact_value(item)
    return out


def _contact(value: Any) -> Any:
    if isinstance(value, list):
        return [_contact(item) for item in value]
    if isinstance(value, str):
        return CONTACT_REMOVED
    if not isinstance(value, dict):
        return value
    return {
        key: CONTACT_REMOVED
        if key in CONTACT_FIELDS and isinstance(item, str)
        else redact_value(item)
        for key, item in value.items()
    }


def redact_json(raw: str) -> str | None:
    """JSON text with personal details removed from its decoded values, or None when it is
    not JSON. Unchanged JSON is returned exactly as it was; changed JSON is written again
    with every `</` escaped, so no value can close the script element holding it."""
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    cleaned = redact_value(data)
    if cleaned == data:
        return raw
    return json.dumps(cleaned, ensure_ascii=False, indent=2).replace("</", "<\\/")
