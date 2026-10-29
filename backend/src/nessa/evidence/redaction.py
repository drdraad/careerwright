"""Third parties' personal details removed from what is kept (session 1, "always true": "a
third party's personal details (recruiter names, phone numbers) never kept"; ADR 0009
decision 4). Pure and deterministic.

Applied to a retrieved page, an API response or pasted text before anything is hashed for
spans, parsed into claims or sealed. What it removes:

- email addresses;
- telephone numbers in UK national form (`020 7946 0958`, `(0161) 496 0000`,
  `07700 900123`) and international form (`+44 (0)20 7946 0958`, `+1 555 123 4567`), their
  groups separated by any horizontal space (a no-break space included), a dot or a hyphen,
  not inside a URL, a word or a longer number;
- in JSON (a page's JSON-LD, Adzuna's response), every name, email, telephone and fax
  number of an `applicationContact` or `contactPoint`.

JSON is redacted in its decoded values, never as raw text: a value's escapes (`\\n`,
`\\u003e`) are decoded first, so a detail right after one is still found and the JSON stays
valid. A string whose HTML entities, decoded, show a detail (`jane&#64;recruit.example`) is
replaced by its decoded, redacted form, so the JSON is written again (fix round 5, re-review
5 A R5-2). IDs and URLs are never redacted (`NOT_TEXT`): an ID can look like a phone number.
Links (`LINK_KEYS`) are only looked at, decoded, by `pages.redact_page`.

Text as a reader sees it (`pages.normalised_text`: a page's visible text, an attribute's
value) is redacted with `redact_shown`, which also removes an email address with whitespace
around its "@" or its domain's dots, where markup split it (fix round 4, re-review 4 A R4-1),
but never across a sentence's end (fix round 5, re-review 5 A R5-1).

A personal name in running text cannot be told apart from other words deterministically,
so it is not removed; nor is a detail written in an unusual form (a number spelt out). A
detail the page's markup hides (an entity, a line break, an invisible character, an inline
element, an attribute's entities) is not removed from a kept body either, but
`pages.redact_page` then keeps no body, and the text a model reads is normalised before it
is redacted (`pages.visible_text`). These are known limits, recorded in ADR 0009 for the
product owner. A page's scripts are found by the parser (`pages.redact_page`).
"""

import html
import json
import re
from collections.abc import Iterator
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
# The `NOT_TEXT` keys whose values are links (and what a link object holds): kept exactly,
# but looked at once decoded (`pages.redact_page`; fix round 5, re-review 5 A R5-2). IDs are
# not looked at: one can look like a telephone number.
LINK_KEYS = frozenset({"@context", "@id", "url", "sameAs", "logo", "image", "redirect_url"})

# An image file extension is never an email's TLD (none is a delegated TLD), so an image
# named like `logo@2x.png` is a path, not an address (Task 7 slice B, R6-1, controller ruling).
_NOT_IMAGE_EXTENSION = r"(?!(?i:png|jpe?g|gif|webp|avif|svg|ico|bmp|tiff?)(?![\w-]))"
_EMAIL = re.compile(
    rf"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.{_NOT_IMAGE_EXTENSION}[A-Za-z]{{2,}}"
)
# The same, as normalised text shows an address that inline markup split: optional whitespace
# around the "@" and the domain's dots ("jane<span>@</span>recruit.example" reads "jane @
# recruit.example"). The TLD is letters only, so "£5 @ the door" is no address. A dot with
# whitespace after it may end a sentence, so the label after it must start lowercase (or, in
# the middle, with a digit), and nothing that continues a word may follow the TLD: "Follow
# @GOVUK. Sign up" is no address (fix round 5, re-review 5 A R5-1).
_DOT_BEFORE_LABEL = r"(?:\.|\s+\.|\s*\.\s+(?=[a-z0-9]))"
_DOT_BEFORE_TLD = r"(?:\.|\s+\.|\s*\.\s+(?=[a-z]))"
_SHOWN_EMAIL = re.compile(
    rf"[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9-]+(?:{_DOT_BEFORE_LABEL}[A-Za-z0-9-]+)*"
    rf"{_DOT_BEFORE_TLD}{_NOT_IMAGE_EXTENSION}[A-Za-z]{{2,}}(?![\w-])"
)
# Not preceded by a word character or anything that would put it inside a URL or a number.
_NOT_INSIDE = r"(?<![\w/=?&#%.+-])"
# What may separate a number's digit groups: a space of any horizontal kind (tab, no-break,
# narrow, thin and the other Unicode spaces), a dot or a hyphen; never a line break, so
# separate values on separate lines are never joined (fix round 3, re-review 3 A R3-2).
_HORIZONTAL_SPACES = "".join(
    map(chr, (0x00A0, 0x1680, *range(0x2000, 0x200B), 0x202F, 0x205F, 0x3000))
)
_SEP = rf"[ \t.\-{_HORIZONTAL_SPACES}]"
_PHONE = re.compile(
    _NOT_INSIDE
    + rf"(?:\+\d{{1,3}}(?:{_SEP}?\(0\))?(?:{_SEP}?\(?\d{{1,5}}\)?){{2,6}}"  # international
    + rf"|\(?0\d{{2,4}}\)?(?:{_SEP}?\d{{3,4}}){{2}})"  # UK national
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


def redact_shown(text: str) -> str:
    """`redact_text` for normalised text, where markup may have left whitespace around an
    email's "@" or its domain's dots: an address written so goes too. Whole addresses go
    first, so a sentence after one is never taken for its domain."""
    return _SHOWN_EMAIL.sub(EMAIL_REMOVED, redact_text(text))


def unescaped(text: str) -> str:
    """`text` with its HTML entities decoded until none is left (`&amp;#64;` too), so a
    detail written as entities shows."""
    while (decoded := html.unescape(text)) != text:
        text = decoded
    return text


def _redacted_string(value: str) -> str:
    """A JSON string's emails and telephone numbers removed; if its entities, decoded, show
    one more (`jane&#64;recruit.example`), its decoded form, redacted (fix round 5, re-review
    5 A R5-2). Applied again, it changes nothing, so a rewritten block reads the same."""
    redacted = redact_text(value)
    decoded = unescaped(redacted)
    shown = redact_text(decoded)
    return redacted if shown == decoded else shown


def redact_value(value: Any) -> Any:
    """A decoded JSON value with personal details removed: a contact's fields replaced, every
    other string's emails and telephone numbers removed (also those its HTML entities hide),
    IDs and URLs kept as they are."""
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return _redacted_string(value)
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


def link_strings(value: Any) -> Iterator[str]:
    """Every string a decoded JSON value holds under a link key (`LINK_KEYS`), at any depth:
    what `redact_value` keeps as written, for `pages.redact_page` to look at."""
    if isinstance(value, list):
        for item in value:
            yield from link_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in LINK_KEYS:
                yield from _strings(item)
            elif key not in NOT_TEXT:
                yield from link_strings(item)


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, dict)):
        for item in value if isinstance(value, list) else value.values():
            yield from _strings(item)


def loads_json(raw: str) -> tuple[Any, bool]:
    """The decoded JSON (the last of a repeated key, as `json.loads` keeps it) and whether
    any object repeated a key. Raises ValueError when it is not JSON."""
    repeated = False

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal repeated
        repeated = repeated or len({key for key, _ in items}) != len(items)
        return dict(items)

    return json.loads(raw, object_pairs_hook=pairs), repeated


def redact_json(raw: str) -> str | None:
    """JSON text with personal details removed from its decoded values, or None when it is
    not JSON. JSON that redaction leaves unchanged, with no repeated key, is returned exactly
    as it was; any other is written again (a repeated key's earlier, shadowed value goes:
    re-review A N-1), with every `</` escaped, so no value can close the element holding
    it."""
    try:
        data, repeated = loads_json(raw)
    except ValueError:
        return None
    cleaned = redact_value(data)
    if cleaned == data and not repeated:
        return raw
    return json.dumps(cleaned, ensure_ascii=False, indent=2).replace("</", "<\\/")
