"""Canonical jobs from source copies (spec section 7, "Search, canonicalisation and
matching"; JOB-01, JOB-02). Pure and deterministic.

Two copies are one job when they share a provider's source ID, or when nothing material
tells them apart (title with its level words, contract, locations, employer) and they share
an application URL or, for one named employer, the same description: the whole of it, or
the opening words a board's snippet keeps. Unknown values never prove two copies different,
and never prove them the same. Every copy is kept; a job with several cities is one job that
appears under each city and counts once in totals.

A staffing agency is told apart from the hiring employer by a reviewed list of staffing
words in its name; an agency's copy never names the agency as the employer, so the hiring
employer stays undisclosed unless a source discloses it.
"""

import hashlib
import re
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from nessa.catalogue.pay import (
    FloorUnknown,
    FloorVerdict,
    SalaryFloorRule,
    StatedPay,
    floor_verdict,
)
from nessa.evidence.records import AdvertiserKind, JobCopy, Salary

# Words in an advertiser's name that mark a staffing agency (reviewable list).
AGENCY_MARKERS = (
    "recruitment",
    "recruiting",
    "recruiters",
    "staffing",
    "resourcing",
    "personnel",
    "employment agency",
    "talent solutions",
    "search and selection",
)
LEGAL_FORMS = frozenset({"ltd", "limited", "plc", "llp", "llc", "inc", "incorporated"})
# Tracking parameters that never identify an application.
TRACKING_PARAMETERS = frozenset({"gclid", "fbclid", "ref", "source", "src", "referrer"})
# A board's snippet keeps the opening of the advert; this many words must match, and the
# snippet must hold at least one more (its last word may be cut).
LEAD_WORDS = 16
_GROUP_NAMESPACE = uuid.UUID("2f1b7c3e-8a40-4b0e-9f3e-6c1d2a7b5e10")
_WORD = re.compile(r"[a-z0-9]+")
_BRACKETED = re.compile(r"\([^)]*\)|\[[^\]]*\]")


def _words(text: str) -> list[str]:
    return _WORD.findall(text.casefold())


def description_fingerprints(text: str) -> tuple[str | None, str | None]:
    """(all words, opening words) of a plain-text description, each as SHA-256."""
    words = _words(text)
    if not words:
        return None, None
    whole = hashlib.sha256(" ".join(words).encode()).hexdigest()
    lead = (
        hashlib.sha256(" ".join(words[:LEAD_WORDS]).encode()).hexdigest()
        if len(words) > LEAD_WORDS
        else None
    )
    return whole, lead


def title_key(title: str) -> str:
    """Case, punctuation and bracketed notes folded; level words such as "senior" kept."""
    return " ".join(_words(_BRACKETED.sub(" ", title)))


def employer_key(name: str) -> str | None:
    words = [w for w in _words(name.replace("&", " and ")) if w not in LEGAL_FORMS]
    return " ".join(words) or None


def advertiser_kind(name: str | None, *, on_own_site: bool) -> AdvertiserKind:
    """Agency when the name carries a staffing word; the employer when it advertises on its
    own site; otherwise unknown (a board does not say who is advertising)."""
    if name is None:
        return AdvertiserKind.UNKNOWN
    folded = " ".join(_words(name))
    if any(marker in folded for marker in AGENCY_MARKERS):
        return AdvertiserKind.AGENCY
    return AdvertiserKind.EMPLOYER if on_own_site else AdvertiserKind.UNKNOWN


def application_key(url: str) -> str | None:
    """An application URL without its fragment, tracking parameters or host case."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if not parts.netloc:
        return None
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMETERS
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(sorted(query)),
            "",
        )
    )


# Contract words by dimension: hours and terms. Two copies differ in contract only when
# both state the same dimension differently (a board may give terms the employer omits).
_CONTRACT_TERMS = {
    "full_time": ("hours", "full_time"),
    "part_time": ("hours", "part_time"),
    "permanent": ("terms", "permanent"),
    "contract": ("terms", "contract"),
    "contractor": ("terms", "contract"),
    "temporary": ("terms", "temporary"),
    "temp": ("terms", "temporary"),
    "intern": ("terms", "internship"),
    "internship": ("terms", "internship"),
    "apprenticeship": ("terms", "apprenticeship"),
    "volunteer": ("terms", "volunteer"),
    "per_diem": ("terms", "per_diem"),
}


def _contract(employment_type: str | None) -> tuple[tuple[str, str], ...]:
    if not employment_type:
        return ()
    found = {
        _CONTRACT_TERMS[term]
        for part in employment_type.split(",")
        if (term := "_".join(_words(part))) in _CONTRACT_TERMS
    }
    return tuple(sorted(found))


@dataclass(frozen=True)
class CanonicalFacts:
    source_key: tuple[str, str] | None
    application: str | None
    employer_key: str | None
    title_key: str
    contract: tuple[tuple[str, str], ...]  # (dimension, value) pairs
    locations: frozenset[str]
    fingerprint: str | None
    lead: str | None


def canonical_facts(job: JobCopy, *, provider: str) -> CanonicalFacts:
    named = job.employer if job.advertiser is not AdvertiserKind.AGENCY else None
    return CanonicalFacts(
        source_key=(provider, job.source_job_id) if job.source_job_id else None,
        application=application_key(job.apply_url) if job.apply_url else None,
        employer_key=employer_key(named) if named else None,
        title_key=title_key(job.title),
        contract=_contract(job.employment_type),
        locations=frozenset(" ".join(_words(loc.locality or loc.label)) for loc in job.locations),
        fingerprint=job.description_fingerprint,
        lead=job.description_lead,
    )


def facts_json(facts: CanonicalFacts) -> dict[str, object]:
    """The facts as stored beside a copy, so later copies are matched without re-parsing."""
    return {
        "source_key": list(facts.source_key) if facts.source_key else None,
        "application": facts.application,
        "employer_key": facts.employer_key,
        "title_key": facts.title_key,
        "contract": [list(pair) for pair in facts.contract],
        "locations": sorted(facts.locations),
        "fingerprint": facts.fingerprint,
        "lead": facts.lead,
    }


def facts_from_json(data: dict[str, object]) -> CanonicalFacts:
    source_key = data.get("source_key")
    contract = data.get("contract")
    locations = data.get("locations")
    return CanonicalFacts(
        source_key=(str(source_key[0]), str(source_key[1]))
        if isinstance(source_key, list) and len(source_key) == 2
        else None,
        application=str(data["application"]) if data.get("application") else None,
        employer_key=str(data["employer_key"]) if data.get("employer_key") else None,
        title_key=str(data.get("title_key") or ""),
        contract=tuple(
            (str(pair[0]), str(pair[1]))
            for pair in (contract if isinstance(contract, list) else [])
            if isinstance(pair, list) and len(pair) == 2
        ),
        locations=frozenset(str(x) for x in (locations if isinstance(locations, list) else [])),
        fingerprint=str(data["fingerprint"]) if data.get("fingerprint") else None,
        lead=str(data["lead"]) if data.get("lead") else None,
    )


def _contracts_differ(a: CanonicalFacts, b: CanonicalFacts) -> bool:
    theirs = dict(b.contract)
    return any(
        dimension in theirs and theirs[dimension] != value for dimension, value in a.contract
    )


def _materially_different(a: CanonicalFacts, b: CanonicalFacts) -> bool:
    """Locations differ when they share no city: a board may list one city of a job that
    names several, but a job in Leeds is not a job in Manchester."""
    return (
        a.title_key != b.title_key
        or _contracts_differ(a, b)
        or (bool(a.locations) and bool(b.locations) and not a.locations & b.locations)
        or (
            a.employer_key is not None
            and b.employer_key is not None
            and a.employer_key != b.employer_key
        )
    )


def same_job(a: CanonicalFacts, b: CanonicalFacts) -> bool:
    if a.source_key is not None and a.source_key == b.source_key:
        return True
    if _materially_different(a, b):
        return False
    if a.application is not None and a.application == b.application:
        return True
    if a.employer_key is None or a.employer_key != b.employer_key:
        return False
    return (a.fingerprint is not None and a.fingerprint == b.fingerprint) or (
        a.lead is not None and a.lead == b.lead
    )


@dataclass(frozen=True)
class Grouped:
    """One canonical job and every source copy of it."""

    job_key: str
    copies: list[tuple[str, JobCopy]] = field(default_factory=list)

    @property
    def locations(self) -> frozenset[str]:
        return frozenset(
            " ".join(_words(loc.locality or loc.label))
            for _, job in self.copies
            for loc in job.locations
        )


def _signature(provider: str, facts: CanonicalFacts) -> str:
    return repr((provider, facts))


def groups_of(found: Sequence[CanonicalFacts]) -> list[list[int]]:
    """The indices of `found` grouped by `same_job`, transitively: the one rule both the
    grouping below and the stored path (`jobs_joined`) use. The grouping does not depend on
    the order."""
    parent = list(range(len(found)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            if same_job(found[i], found[j]):
                parent[root(j)] = root(i)
    members: dict[int, list[int]] = {}
    for i in range(len(found)):
        members.setdefault(root(i), []).append(i)
    return list(members.values())


def jobs_joined[Job](
    stored: Sequence[tuple[Job, CanonicalFacts]], new: CanonicalFacts
) -> list[Job]:
    """The stored jobs a new copy belongs to: each job with a copy in the new copy's group,
    by `groups_of` over the candidates and the new copy, in the order given (oldest job
    first). None: a new job. Several: the new copy bridges them, and they are one job."""
    found = [facts for _, facts in stored] + [new]
    group = next(g for g in groups_of(found) if len(stored) in g)
    return list(dict.fromkeys(stored[i][0] for i in sorted(group) if i < len(stored)))


def group_copies(copies: Iterable[tuple[str, JobCopy]]) -> list[Grouped]:
    """Copies grouped into jobs by `same_job`, transitively; the grouping and each job's key
    do not depend on the copies' order."""
    items = list(copies)
    found = [canonical_facts(job, provider=provider) for provider, job in items]
    groups = []
    for indices in groups_of(found):
        signature = min(_signature(items[i][0], found[i]) for i in indices)
        key = str(uuid.uuid5(_GROUP_NAMESPACE, signature))
        groups.append(Grouped(key, [items[i] for i in indices]))
    return sorted(groups, key=lambda group: group.job_key)


def job_against_floor(
    floor: SalaryFloorRule, salaries: Iterable[Salary | None]
) -> tuple[FloorVerdict, FloorUnknown | None]:
    """One job, from its copies' pay, against the person's salary floor (Task 7 slice B): it
    is below only when advertised GBP pay in the floor's period, the highest of its copies'
    amounts (the top of a range, or its one amount), is below. Advertised pay is read as
    gross, as UK adverts state pay (provisional, R6). Predicted, unknown and other-period
    pay is never below the floor (`pay.floor_verdict`)."""
    stated = [
        StatedPay(
            basis=s.basis.value,
            currency=s.currency,
            period=s.period.value if s.period else None,
            highest_minor_units=max(
                amount
                for amount in (s.minimum_minor_units, s.maximum_minor_units)
                if amount is not None
            ),
        )
        for s in salaries
        if s is not None
    ]
    return floor_verdict(floor, stated)


def city_views(groups: Iterable[Grouped]) -> dict[str, list[str]]:
    """City -> the jobs that appear there. A job in several cities appears under each; it is
    still one job, so totals count `len(groups)`, never the sum of these lists."""
    views: dict[str, list[str]] = {}
    for group in groups:
        for city in sorted(group.locations):
            views.setdefault(city, []).append(group.job_key)
    return views
