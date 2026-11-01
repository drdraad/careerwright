"""The source permission manifest (OI-11; `sources.json` beside this module) and the
session 1 rights policy (H-06) as code: whether a host may be fetched, what class its pages
belong to, and what a workspace keeps of them (ACQ-06).

The classes and what each permits come from the product owner's answers
(`docs/reviews/session-1.md`, Part A; `corpus/README.md`). A page is classified by its
host's manifest entry and nothing else: an employer's careers site or ATS host is an
employer posting (session 1 line A5) only when the manifest lists it so. What a page says
about itself (its JSON-LD `hiringOrganization`) never changes its class, since any page can
claim any organisation. An unlisted page is not clearly within a class and stays "pending
human rights review" (line A7), keeping the hash and minimal excerpts only, unless an
agent's dated classification is recorded for it (`tools/corpus.py`).
"""

import functools
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import Field

from careerwright.evidence.records import Retention, RightsClass, StrictModel

MANIFEST_PATH = Path(__file__).with_name("sources.json")
PENDING_REVIEW = "pending human rights review"
# The classes whose pages may be kept privately (session 1, lines A1 to A5).
_KEEP_PRIVATELY = frozenset(
    {
        RightsClass.GOVUK,
        RightsClass.PUBLIC_SECTOR,
        RightsClass.COURSE_PROVIDER,
        RightsClass.PROFESSIONAL_BODY,
        RightsClass.EMPLOYER_POSTING,
    }
)


class Access(StrEnum):
    PERMITTED = "permitted"  # fetched when its robots.txt allows
    API_ONLY = "api_only"  # read through its API only; its pages are never fetched
    DENIED = "denied"  # never fetched: the attempt is recorded as blocked


class SourceRule(StrictModel):
    rights_class: RightsClass
    access: Access
    purpose: str
    rate_limit_seconds: float = Field(ge=0)
    retained_fields: list[str]
    attribution: str
    terms: str
    terms_read_on: date | None
    reason: str


class SourceEntry(SourceRule):
    host: str = Field(pattern=r"^[a-z0-9.-]+$")
    include_subdomains: bool


class SourceManifest(StrictModel):
    manifest: str
    version: str
    updated: date
    open_item: str
    about: str
    user_agent: str
    robots: str
    default: SourceRule
    sources: list[SourceEntry]


@functools.cache
def load_manifest() -> SourceManifest:
    return SourceManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))


def _matches(entry: SourceEntry, host: str) -> bool:
    return host == entry.host or (entry.include_subdomains and host.endswith(f".{entry.host}"))


def rule_for(host: str) -> SourceRule:
    """The manifest's rule for a host (the longest matching entry), else the default."""
    manifest = load_manifest()
    matching = [e for e in manifest.sources if _matches(e, host.lower())]
    if not matching:
        return manifest.default
    entry = max(matching, key=lambda e: len(e.host))
    return SourceRule.model_validate(entry.model_dump(exclude={"host", "include_subdomains"}))


def retention(rights_class: RightsClass) -> Retention:
    return Retention.BODY if rights_class in _KEEP_PRIVATELY else Retention.EXCERPTS


@dataclass(frozen=True)
class PageRights:
    rights_class: RightsClass
    rights_status: str  # "<class>: <terms relied on, dated>" or "pending human rights review"
    retention: Retention


def classify_page(host: str) -> PageRights:
    """The page's class and rights status, and so what is kept of it: from its host's
    manifest entry only."""
    rule = rule_for(host)
    if rule.rights_class is RightsClass.OTHER:
        return PageRights(RightsClass.OTHER, PENDING_REVIEW, Retention.EXCERPTS)
    read_on = f"read {rule.terms_read_on}" if rule.terms_read_on else "no terms read"
    status = f"{rule.rights_class.value}: {rule.terms} ({read_on})"
    return PageRights(rule.rights_class, status, retention(rule.rights_class))


def is_listed(host: str) -> bool:
    """Whether the manifest has an entry for the host (else its default rule applies)."""
    return any(_matches(e, host.lower()) for e in load_manifest().sources)
