"""The person's selection of spans in their own example adverts (Task 10; MAP1-01; ADR 0012,
decision 11's open item and its 2026-10-31 amendment). Pure: no SQL, no network, no model.

A target's examples are the adverts the person pasted for it (at most three, MAP1-01). What
an example asks for is read by the person's own selection of spans in its text, never by a
model run. A span is a pair of character offsets into the example's text as it was kept
(third parties' contact details already removed); its words are read back from the kept text,
so a selection stores offsets only. Spans are checked against the text before anything is
recorded: inside it, not empty, not too long, and not overlapping.
"""

from collections.abc import Sequence
from itertools import pairwise

from pydantic import BaseModel, ConfigDict, Field

from careerwright.errors import CareerwrightError, ErrorCode, ErrorStage

# A span is a phrase or a requirement line, never the whole advert.
MAX_SPAN_CHARS = 600
MAX_SPANS_PER_EXAMPLE = 12


class AdvertSpan(BaseModel):
    """Character offsets into an example's text: `start` inclusive, `end` exclusive."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start: int = Field(ge=0)
    end: int = Field(ge=1)


class SelectedSpan(AdvertSpan):
    excerpt: str  # the example's own words at these offsets, read back from the kept text


def _invalid(reason: str, message: str) -> CareerwrightError:
    return CareerwrightError(
        ErrorCode.VALIDATION_FAILED,
        message,
        stage=ErrorStage.CAPABILITY,
        details={"field": "spans", "reason": reason},
    )


def check_spans(text: str, spans: Sequence[AdvertSpan]) -> list[AdvertSpan]:
    """The spans in text order, or a refusal naming the first rule broken. An empty
    selection is allowed: it clears the example's spans."""
    if len(spans) > MAX_SPANS_PER_EXAMPLE:
        raise _invalid("too_many_spans", "Choose fewer parts of this advert.")
    ordered = sorted(spans, key=lambda s: (s.start, s.end))
    for span in ordered:
        if span.end <= span.start:
            raise _invalid("span_empty", "Each chosen part needs at least one character.")
        if span.end > len(text):
            raise _invalid("span_outside_text", "A chosen part goes past the end of the advert.")
        if span.end - span.start > MAX_SPAN_CHARS:
            raise _invalid("span_too_long", "Choose a shorter part of the advert.")
        if not text[span.start : span.end].strip():
            raise _invalid("span_blank", "A chosen part holds no words.")
    for before, after in pairwise(ordered):
        if after.start < before.end:
            raise _invalid("spans_overlap", "Two chosen parts overlap.")
    return ordered


def read_spans(text: str, spans: Sequence[AdvertSpan]) -> list[SelectedSpan]:
    """Each stored span with the example's words at its offsets."""
    return [SelectedSpan(start=s.start, end=s.end, excerpt=text[s.start : s.end]) for s in spans]
