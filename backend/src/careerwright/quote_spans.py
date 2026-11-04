"""Pure quotation matching shared by profile notes and source extraction."""

import unicodedata

_DOUBLE = '"' + "".join(map(chr, (0x201C, 0x201D, 0x201E, 0x201F, 0x00AB, 0x00BB)))
_OPEN_SINGLE, _CLOSE_SINGLE = chr(0x2018), chr(0x2019)
_APOSTROPHES = str.maketrans(
    {
        **dict.fromkeys(map(chr, (0x2018, 0x2019, 0x201B, 0x02BB, 0x02BC, 0x0060, 0x00B4)), "'"),
        **dict.fromkeys(map(chr, (0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212)), "-"),
    }
)
_EDGE_TRIM = f" \t\n{_DOUBLE}"
_CLOSING = f" .,;:!?{chr(0x2026)}"
_SINGLE_PAIRS = (("'", "'"), (_OPEN_SINGLE, _CLOSE_SINGLE))


def _bare(text: str) -> str:
    """Remove surrounding quote marks and closing punctuation until the text is bare."""
    previous = None
    while text != previous:
        previous = text
        text = text.strip(_EDGE_TRIM).rstrip(_CLOSING)
    return text


def unwrapped(text: str) -> str:
    """Trim quotation marks while preserving a lone source apostrophe."""
    text = _bare(text)
    for opening, closing in _SINGLE_PAIRS:
        if len(text) > 2 and text.startswith(opening) and text.endswith(closing):
            return _bare(text[1:-1])
    return text


def folded(text: str) -> tuple[str, list[int]]:
    """Fold spacing, case and punctuation while retaining source character offsets."""
    chars: list[str] = []
    index: list[int] = []
    space = True
    for i, original in enumerate(text):
        if original.isspace():
            if not space:
                chars.append(" ")
                index.append(i)
            space = True
            continue
        for char in unicodedata.normalize("NFKC", original).translate(_APOSTROPHES).lower():
            chars.append(char)
            index.append(i)
        space = False
    if chars and chars[-1] == " ":
        chars.pop()
        index.pop()
    return "".join(chars), index


def _in_word(text: str, i: int) -> bool:
    """Treat an apostrophe within or after a word as part of that word."""
    char = text[i]
    if char.isalnum():
        return True
    if char != "'":
        return False
    letter_before = i > 0 and text[i - 1].isalpha()
    letter_after = i + 1 < len(text) and text[i + 1].isalpha()
    return (letter_before and letter_after) or (i > 0 and text[i - 1] == "s" and not letter_after)


def span_offsets(quote: str, source: str) -> tuple[int, int] | None:
    """Locate a whole-word quotation in the source's original characters."""
    wanted, _ = folded(quote)
    text, index = folded(source)
    if not wanted:
        return None
    start = text.find(wanted)
    while start != -1:
        end = start + len(wanted)
        before = start == 0 or not _in_word(text, start - 1)
        after = end == len(text) or not _in_word(text, end)
        if before and after:
            return index[start], index[end - 1] + 1
        start = text.find(wanted, start + 1)
    return None
