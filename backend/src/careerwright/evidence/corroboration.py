"""Role research's corroboration (ADR 0015 decision 2; spec section 4, DIV-1): whether a title
no list holds is found in independent sources. Pure: no database, no network, no model.

A page counts only where the title is verified, word for word, as a span of its visible text
(`span_offsets`: case, spacing and apostrophe forms aside, whole words at both ends). The
role is found when the title is verified on pages from at least two independent sources, or
on one page of an official class. Independent means distinct hosts or distinct employers;
copies of one advert fold into one source first, and never count twice (ADR 0009 decision 6):
two pages are copies when a posting of one is the same job as a posting of the other
(`jobs.same_job`), or when the title and the words after it are the same on both
(`PASSAGE_WORDS`). Two pages on one host are one source, unless each names an employer and
they name different ones. Otherwise the role stays "not yet found in independent sources":
visible, never hidden, never a suggestion.

Nothing a page says about itself, or asks a model to do, reaches this: a page's class comes
from the source manifest, and a span is checked by code. No model reads a role page.
"""

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from careerwright.evidence.jobs import CanonicalFacts, canonical_facts, same_job
from careerwright.evidence.pages import EXCERPT_CHARS
from careerwright.evidence.records import JobCopy, RightsClass
from careerwright.profile.slate_explanation import span_offsets

# The classes the corroboration rule calls official (ADR 0015 decision 2).
OFFICIAL_CLASSES = frozenset(
    {RightsClass.GOVUK, RightsClass.PUBLIC_SECTOR, RightsClass.PROFESSIONAL_BODY}
)
# The words after the title that two copies of one advert share: the title's own words, then
# this many more, compared as lower-case words.
PASSAGE_WORDS = 24
INDEPENDENT_SOURCES = 2
_WORD = re.compile(r"\w+")


@dataclass(frozen=True)
class TitleCheck:
    """What code found of a title on one page's visible text (the text itself is not kept)."""

    text_sha256: str  # of the visible text the span indexes into
    span: tuple[int, int] | None  # where the title is, in that text; None: not verified
    excerpt: str | None  # the page's own characters around the span, at most 200
    passage_sha256: str | None  # the title and the words after it, for copies of one advert
    postings: tuple[CanonicalFacts, ...] = ()  # the page's structured postings, if any

    @property
    def verified(self) -> bool:
        return self.span is not None

    @property
    def employers(self) -> frozenset[str]:
        return frozenset(p.employer_key for p in self.postings if p.employer_key)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def excerpt_around(text: str, start: int, end: int) -> str:
    """The span with what is around it, at most `EXCERPT_CHARS` characters, whole words where
    the cut allows."""
    room = max(0, EXCERPT_CHARS - (end - start))
    left = max(0, start - room // 2)
    right = min(len(text), max(end, left + EXCERPT_CHARS))
    left = max(0, min(left, right - EXCERPT_CHARS))
    if left > 0:  # a word cut at the left edge is left out, never the span's own
        space = text.find(" ", left, start)
        left = space + 1 if space != -1 else left
    if right < len(text):
        space = text.rfind(" ", end, right)
        right = space if space != -1 else right
    return text[left:right].strip()


def check_title(
    title: str, text: str, copies: Sequence[JobCopy] = (), *, provider: str
) -> TitleCheck:
    """The title against one page's visible text, and the page's postings for copies."""
    postings = tuple(
        canonical_facts(c, provider=provider) for c in copies if c.extraction_error is None
    )
    found = span_offsets(title, text)
    if found is None:
        return TitleCheck(_sha256(text), None, None, None, postings)
    start, end = found
    words = _WORD.findall(text[start:].casefold())
    passage = words[: len(_WORD.findall(title)) + PASSAGE_WORDS]
    return TitleCheck(
        text_sha256=_sha256(text),
        span=found,
        excerpt=excerpt_around(text, start, end),
        passage_sha256=_sha256(" ".join(passage)),
        postings=postings,
    )


class RoleVerdict(StrEnum):
    FOUND = "found"
    NOT_YET_FOUND = "not_yet_found"  # in independent sources: never "doesn't exist"


class NotYetFoundReason(StrEnum):
    """Why a role read from its pages is not yet found: never evidence it doesn't exist."""

    NOT_ON_ANY_PAGE = "not_on_any_page"  # no page read shows the title word for word
    ONE_SOURCE_ONLY = "one_source_only"  # it is, but on one source (copies counted once)


@dataclass(frozen=True)
class PageEvidence:
    """One read page's place in the rule: its host, its class (from the manifest) and what
    code found of the title there."""

    ref: str  # the attempt that read it
    host: str
    rights_class: RightsClass | None
    check: TitleCheck


@dataclass(frozen=True)
class Corroboration:
    verdict: RoleVerdict
    reason: NotYetFoundReason | None
    sources: int  # independent sources showing the title (copies counted once)
    official: bool  # an official page shows it
    # The pages showing the title, grouped by source: copies of one advert, and pages of one
    # host, share a group.
    groups: list[list[str]] = field(default_factory=list)


def _copies(a: TitleCheck, b: TitleCheck) -> bool:
    if a.passage_sha256 is not None and a.passage_sha256 == b.passage_sha256:
        return True
    return any(same_job(x, y) for x in a.postings for y in b.postings)


def _one_source(a: PageEvidence, b: PageEvidence) -> bool:
    if _copies(a.check, b.check):
        return True
    if a.host != b.host:
        return False
    employers_a, employers_b = a.check.employers, b.check.employers
    return not (employers_a and employers_b and not employers_a & employers_b)


def corroborate(pages: Sequence[PageEvidence]) -> Corroboration:
    """ADR 0015's rule over the pages read for one title, in the order given."""
    verified = [p for p in pages if p.check.verified]
    parent = list(range(len(verified)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(verified):
        for j in range(i):
            if _one_source(a, verified[j]):
                parent[root(i)] = root(j)
    grouped: dict[int, list[str]] = {}
    for i, page in enumerate(verified):
        grouped.setdefault(root(i), []).append(page.ref)
    groups = list(grouped.values())
    official = any(p.rights_class in OFFICIAL_CLASSES for p in verified)
    if official or len(groups) >= INDEPENDENT_SOURCES:
        return Corroboration(RoleVerdict.FOUND, None, len(groups), official, groups)
    reason = NotYetFoundReason.ONE_SOURCE_ONLY if verified else NotYetFoundReason.NOT_ON_ANY_PAGE
    return Corroboration(RoleVerdict.NOT_YET_FOUND, reason, len(groups), official, groups)
