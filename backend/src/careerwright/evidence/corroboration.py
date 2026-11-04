"""Role research's corroboration (ADR 0015 decision 2; spec section 4, DIV-1): whether a title
no list holds is found in independent sources. Pure: no database, no network, no model.

A page counts only where the title is verified, word for word, as a span of its visible text
(`span_offsets`: case, spacing and apostrophe forms aside, whole words at both ends). The
role is found when the title is verified on pages from at least two independent sources, or
on one page of an official class. Independent means distinct sites or distinct employers;
copies of one advert fold into one source first, and never count twice (ADR 0009 decision 6):
two pages are copies when a posting of one is the same job as a posting of the other
(`jobs.same_job`), or when they share a passage around the title (`passages`): at any of the
title's places on each page (up to `MAX_PLACES`), the title with the `PASSAGE_WORDS` words
after it, or the `PASSAGE_WORDS` words before it with the title. So a page's own `<title>`,
navigation or footer, which name the title too, never make two copies of one advert differ:
the advert's body still shares its passage. Two pages of one site (`site`: the registrable
domain, so `www.` and `careers.` of one domain are one) are one source, unless each names an
employer and they name different ones. Otherwise the role stays "not yet found in
independent sources": visible, never hidden, never a suggestion.

Folding errs towards one source: two pages that share 24 words around the title (a common
template's words included) count once, and so do two sites under one two-level suffix this
module doesn't list (`_TWO_LEVEL_SUFFIXES`, the UK's): "not yet found" is said, never a
false "found".

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
from careerwright.quote_spans import span_offsets

# The classes the corroboration rule calls official (ADR 0015 decision 2).
OFFICIAL_CLASSES = frozenset(
    {RightsClass.GOVUK, RightsClass.PUBLIC_SECTOR, RightsClass.PROFESSIONAL_BODY}
)
# The words beside the title that two copies of one advert share: the title's own words with
# this many more after it, or this many before it, compared as lower-case words.
PASSAGE_WORDS = 24
# Fewer words on one side, where the text ends first: that side is too short to tell one page
# from another (a page that merely starts or ends with the title, or "<title> jobs"), so it
# isn't fingerprinted.
EDGE_WORDS = 8
# The title's places on one page whose passages are kept (a page names it in its <title>,
# navigation, heading, body and footer): so at most twice this many fingerprints a page.
MAX_PLACES = 16
INDEPENDENT_SOURCES = 2
_WORD = re.compile(r"\w+")
# Public suffixes of two labels under which each name is its own site (the UK's; ".gov.uk"'s
# "service.gov.uk" is three). Elsewhere a site is the host's last two labels.
_TWO_LEVEL_SUFFIXES = frozenset(
    {
        "ac.uk",
        "co.uk",
        "gov.uk",
        "ltd.uk",
        "me.uk",
        "mod.uk",
        "net.uk",
        "nhs.uk",
        "org.uk",
        "plc.uk",
        "police.uk",
        "sch.uk",
    }
)
_THREE_LEVEL_SUFFIXES = frozenset({"service.gov.uk"})


def site(host: str) -> str:
    """The site a host belongs to, its registrable domain: `careers.northwind.co.uk` and
    `www.northwind.co.uk` are both `northwind.co.uk`. Case and a final dot aside; an address
    is its own site."""
    name = host.casefold().rstrip(".")
    labels = name.split(".")
    if ":" in name or all(label.isdigit() for label in labels):
        return name
    for size, suffixes in ((3, _THREE_LEVEL_SUFFIXES), (2, _TWO_LEVEL_SUFFIXES)):
        if len(labels) > size and ".".join(labels[-size:]) in suffixes:
            return ".".join(labels[-size - 1 :])
    return ".".join(labels[-2:])


@dataclass(frozen=True)
class TitleCheck:
    """What code found of a title on one page's visible text (the text itself is not kept)."""

    text_sha256: str  # of the visible text the span indexes into
    span: tuple[int, int] | None  # where the title is, in that text; None: not verified
    excerpt: str | None  # the page's own characters around the span, at most 200
    # Fingerprints of the passages around the title's places (`passages`), for copies of one
    # advert; none where the title is not verified.
    passages: tuple[str, ...]
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


def passages(title: str, text: str) -> tuple[str, ...]:
    """Fingerprints of the passages around the title's places in the text, as lower-case words:
    at each of its first `MAX_PLACES` places, the title with the `PASSAGE_WORDS` words after it
    and the `PASSAGE_WORDS` words before it with the title (fewer where the text ends first),
    each side only where it holds at least `EDGE_WORDS` words (so a page that merely starts or
    ends with the title shares nothing with another that does); a place with neither side
    stands for the whole text, so two copies of one short page still match."""
    wanted = _WORD.findall(title.casefold())
    words = _WORD.findall(text.casefold())
    size = len(wanted)
    if not size:
        return ()
    places = [i for i in range(len(words) - size + 1) if words[i : i + size] == wanted]
    found: set[str] = set()
    for i in places[:MAX_PLACES]:
        after = words[i + size : i + size + PASSAGE_WORDS]
        before = words[max(0, i - PASSAGE_WORDS) : i]
        sides = [
            passage
            for side, passage in ((after, wanted + after), (before, before + wanted))
            if len(side) >= EDGE_WORDS
        ]
        for passage in sides or [words]:
            found.add(_sha256(" ".join(passage)))
    return tuple(sorted(found))


def check_title(
    title: str, text: str, copies: Sequence[JobCopy] = (), *, provider: str
) -> TitleCheck:
    """The title against one page's visible text, and the page's postings for copies."""
    postings = tuple(
        canonical_facts(c, provider=provider) for c in copies if c.extraction_error is None
    )
    found = span_offsets(title, text)
    if found is None:
        return TitleCheck(_sha256(text), None, None, (), postings)
    start, end = found
    return TitleCheck(
        text_sha256=_sha256(text),
        span=found,
        excerpt=excerpt_around(text, start, end),
        passages=passages(title, text) or (_sha256(" ".join(_WORD.findall(text.casefold()))),),
        postings=postings,
    )


class RoleVerdict(StrEnum):
    FOUND = "found"
    NOT_YET_FOUND = "not_yet_found"  # in independent sources: never "doesn't exist"


class NotYetFoundReason(StrEnum):
    """Why a role read from its pages is not yet found: never evidence it doesn't exist."""

    # Every page proposed was read, and none shows the title word for word.
    NOT_ON_ANY_PAGE = "not_on_any_page"
    ONE_SOURCE_ONLY = "one_source_only"  # it is, but on one source (copies counted once)
    # No page read shows it, and some (or all) couldn't be read: they might, so nothing is
    # said of them. A blocked, failed or unread page is never a page without the title.
    PAGES_UNREAD = "pages_unread"


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
    # site, share a group.
    groups: list[list[str]] = field(default_factory=list)
    unread: int = 0  # the pages proposed that couldn't be read (blocked, failed or not tried)


def _copies(a: TitleCheck, b: TitleCheck) -> bool:
    if set(a.passages) & set(b.passages):
        return True
    return any(same_job(x, y) for x in a.postings for y in b.postings)


def _one_source(a: PageEvidence, b: PageEvidence) -> bool:
    if _copies(a.check, b.check):
        return True
    if site(a.host) != site(b.host):
        return False
    employers_a, employers_b = a.check.employers, b.check.employers
    return not (employers_a and employers_b and not employers_a & employers_b)


def corroborate(pages: Sequence[PageEvidence], *, unread: int = 0) -> Corroboration:
    """ADR 0015's rule over the pages read for one title, in the order given, beside the
    `unread` pages proposed for it that couldn't be read. With no page at all there is
    nothing to say: that is the caller's "no pages", never a result."""
    if unread < 0 or not (pages or unread):
        raise ValueError("no page to corroborate")
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
        return Corroboration(RoleVerdict.FOUND, None, len(groups), official, groups, unread)
    if verified:
        reason = NotYetFoundReason.ONE_SOURCE_ONLY
    elif unread:
        reason = NotYetFoundReason.PAGES_UNREAD
    else:
        reason = NotYetFoundReason.NOT_ON_ANY_PAGE
    return Corroboration(RoleVerdict.NOT_YET_FOUND, reason, len(groups), official, groups, unread)
