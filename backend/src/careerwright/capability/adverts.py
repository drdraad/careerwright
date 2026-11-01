"""The person's selection of spans in their own example adverts (Task 10; MAP1-01; ADR 0012,
decision 11's open item and its 2026-10-31 amendment). Pure: no SQL, no network, no model.

A target's examples are the adverts the person pasted for it (at most three, MAP1-01). What
an example asks for is read by the person's own selection of spans in its text, never by a
model run. A span is a pair of offsets into the example's text as it was kept (third
parties' contact details already removed), counted in UTF-16 code units as a browser's
selection counts them (review I1: an emoji or a mathematical bold letter is two units, one
character). The server converts them to characters and refuses an offset that falls inside
a character, so a selection never lands on the wrong words. Its words are read back from the
kept text, so a selection stores offsets only (as chosen, in UTF-16 units). Spans are checked
against the text before anything is recorded: inside it, on character boundaries, not empty,
not blank, not too long, and not overlapping.
"""

from collections.abc import Sequence
from itertools import pairwise

from pydantic import BaseModel, ConfigDict, Field

from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage

# A span is a phrase or a requirement line, never the whole advert (in characters).
MAX_SPAN_CHARS = 600
MAX_SPANS_PER_EXAMPLE = 12
_BMP_LAST = 0xFFFF  # a character above it is two UTF-16 code units (a surrogate pair)


class AdvertSpan(BaseModel):
    """Offsets into an example's text in UTF-16 code units, as a browser's selection counts
    them (an emoji or a mathematical bold letter is two): `start` inclusive, `end` exclusive.
    The server converts them to characters and refuses an offset inside a character."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start: int = Field(ge=0, description="Inclusive, in UTF-16 code units of the text.")
    end: int = Field(ge=1, description="Exclusive, in UTF-16 code units of the text.")


class SelectedSpan(AdvertSpan):
    excerpt: str  # the example's own words at these offsets, read back from the kept text


def _invalid(reason: str, message: str) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        message,
        stage=ErrorStage.CAPABILITY,
        details={"field": "spans", "reason": reason},
    )


def _boundaries(text: str) -> dict[int, int]:
    """Each UTF-16 offset that falls between characters, mapped to its character index."""
    found = {0: 0}
    units = 0
    for index, character in enumerate(text, start=1):
        units += 2 if ord(character) > _BMP_LAST else 1
        found[units] = index
    return found


def _characters(span: AdvertSpan, boundaries: dict[int, int]) -> tuple[int, int]:
    """A span's character offsets, or a refusal: past the text, or inside a character."""
    total = max(boundaries)
    if span.start > total or span.end > total:
        raise _invalid("span_outside_text", "A chosen part goes past the end of the advert.")
    if span.start not in boundaries or span.end not in boundaries:
        raise _invalid("span_splits_character", "A chosen part starts or ends inside a letter.")
    return boundaries[span.start], boundaries[span.end]


def check_spans(text: str, spans: Sequence[AdvertSpan]) -> list[AdvertSpan]:
    """The spans in text order (UTF-16 offsets, as given), or a refusal naming the first rule
    broken. An empty selection is allowed: it clears the example's spans."""
    if len(spans) > MAX_SPANS_PER_EXAMPLE:
        raise _invalid("too_many_spans", "Choose fewer parts of this advert.")
    ordered = sorted(spans, key=lambda s: (s.start, s.end))
    boundaries = _boundaries(text)
    for span in ordered:
        if span.end <= span.start:
            raise _invalid("span_empty", "Each chosen part needs at least one character.")
        start, end = _characters(span, boundaries)
        if end - start > MAX_SPAN_CHARS:
            raise _invalid("span_too_long", "Choose a shorter part of the advert.")
        if not text[start:end].strip():
            raise _invalid("span_blank", "A chosen part holds no words.")
    for before, after in pairwise(ordered):
        if after.start < before.end:
            raise _invalid("spans_overlap", "Two chosen parts overlap.")
    return ordered


def read_spans(text: str, spans: Sequence[AdvertSpan]) -> list[SelectedSpan]:
    """Each stored span (UTF-16 offsets, as chosen) with the example's words at it."""
    boundaries = _boundaries(text)
    found: list[SelectedSpan] = []
    for span in spans:
        start, end = _characters(span, boundaries)
        found.append(SelectedSpan(start=span.start, end=span.end, excerpt=text[start:end]))
    return found
