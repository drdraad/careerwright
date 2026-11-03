"""No dash used as punctuation in what a model writes for the person to read (the product
owner, 3 November 2026: "Em-dashes are outlawed! Muse must never use them in a response").

Every prompt whose output the person reads carries `DASH_RULE`, and its check refuses an em
dash (U+2014) or an en dash (U+2013) with a space either side, used as one, through
`model_dash`, so the bounded repair asks again. Code never rewrites the model's words. A dash
the person wrote is theirs: it is quoted as they wrote it, so a dash that stands between the
same words in the person's own words is not refused. An en dash in a range (9 to 5 written
with one) and a hyphen are not dashes used as punctuation.
"""

import re
from collections.abc import Iterable

DASH_RULE = "Never write an em dash or a spaced en dash; use a comma, colon or full stop."
DASH_PROBLEM = "no em dash or spaced en dash; use a comma, colon or full stop"
EM_DASH, EN_DASH = chr(0x2014), chr(0x2013)

# A dash used as punctuation, with the word either side of it where there is one.
_DASH = re.compile(rf"(?:(\w+)\s*)?({EM_DASH}|(?<=\s){EN_DASH}(?=\s))(?:\s*(\w+))?")


def _folded(text: str) -> str:
    return " ".join(text.casefold().split())


def model_dash(text: str, own_words: Iterable[str] = ()) -> bool:
    """Whether `text` holds an em dash or a spaced en dash that is not the person's: one whose
    words either side, with the dash between, appear in none of `own_words`."""
    theirs = [_folded(words) for words in own_words]
    for match in _DASH.finditer(text):
        quoted = _folded(match.group(0))
        if not any(quoted in words for words in theirs):
            return True
    return False
