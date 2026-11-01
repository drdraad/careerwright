"""Freshness enforced on access (spec section 11, "M0 enforces applicable maximum-age and
invalidation rules on access, without a scheduled refresh service"; FRESH-02 to FRESH-04).

A source's age runs from its last *successful* verification: a failed refresh records an
attempt and nothing else, so it can never extend validity. An explicit closure overrides
everything, and an expiry date overrides the maximum age. The five timestamps stay
separate: last attempt, last success, publication, valid from and valid until.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class FreshnessKind(StrEnum):
    JOB = "job"  # a job search result or an individual live job
    COURSE_FEE_INTAKE = "course_fee_intake"  # fee, next intake, seats, deadline
    FUNDING_AVAILABILITY = "funding_availability"  # availability or deadline of funding
    FUNDING_RULES = "funding_rules"
    COURSE_SYLLABUS = "course_syllabus"  # syllabus and provider profile


# Maximum unverified age for normal use (spec section 11's table).
MAX_UNVERIFIED_AGE: dict[FreshnessKind, timedelta] = {
    FreshnessKind.JOB: timedelta(hours=24),
    FreshnessKind.COURSE_FEE_INTAKE: timedelta(days=7),
    FreshnessKind.FUNDING_AVAILABILITY: timedelta(hours=48),
    FreshnessKind.FUNDING_RULES: timedelta(days=30),
    FreshnessKind.COURSE_SYLLABUS: timedelta(days=90),
}
# Funding rules are refreshed weekly and used for 30 days "only with a stale warning".
WARN_AFTER: dict[FreshnessKind, timedelta] = {FreshnessKind.FUNDING_RULES: timedelta(days=7)}
STALE_LABEL: dict[FreshnessKind, str] = {FreshnessKind.JOB: "awaiting recheck"}


class Freshness(StrEnum):
    CURRENT = "current"
    CURRENT_WITH_WARNING = "current_with_warning"  # usable, shown with a stale warning
    STALE = "stale"  # older than its maximum age: never shown as current
    EXPIRED = "expired"  # its own expiry date has passed
    CLOSED = "closed"  # the source said it closed
    NOT_YET_VALID = "not_yet_valid"
    NEVER_VERIFIED = "never_verified"  # attempted, never successfully retrieved


@dataclass(frozen=True)
class SourceTimes:
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    published_at: datetime | None
    valid_from: datetime | None
    valid_until: datetime | None


@dataclass(frozen=True)
class FreshnessView:
    kind: FreshnessKind
    state: Freshness
    times: SourceTimes
    max_age: timedelta
    verified_until: datetime | None  # when the last success stops being current

    @property
    def usable_as_current(self) -> bool:
        return self.state in (Freshness.CURRENT, Freshness.CURRENT_WITH_WARNING)

    @property
    def label(self) -> str:
        if self.state is Freshness.STALE:
            return STALE_LABEL.get(self.kind, "stale")
        return self.state.value.replace("_", " ")


def freshness(
    kind: FreshnessKind, times: SourceTimes, *, closed: bool, now: datetime
) -> FreshnessView:
    max_age = MAX_UNVERIFIED_AGE[kind]
    verified_until = None if times.last_success_at is None else times.last_success_at + max_age

    def view(state: Freshness) -> FreshnessView:
        return FreshnessView(kind, state, times, max_age, verified_until)

    if closed:
        return view(Freshness.CLOSED)
    if times.valid_until is not None and now > times.valid_until:
        return view(Freshness.EXPIRED)
    if times.valid_from is not None and now < times.valid_from:
        return view(Freshness.NOT_YET_VALID)
    if times.last_success_at is None or verified_until is None:
        return view(Freshness.NEVER_VERIFIED)
    if now > verified_until:
        return view(Freshness.STALE)
    warn_after = WARN_AFTER.get(kind)
    if warn_after is not None and now > times.last_success_at + warn_after:
        return view(Freshness.CURRENT_WITH_WARNING)
    return view(Freshness.CURRENT)


# Refresh back-off after consecutive failures: one minute, doubling, at most an hour.
BACKOFF_FIRST = timedelta(minutes=1)
BACKOFF_MAX = timedelta(hours=1)


@dataclass(frozen=True)
class RefreshDecision:
    class Action(StrEnum):
        START = "start"
        JOIN = "join"  # a refresh of the same source is already in flight
        BACK_OFF = "back_off"  # it failed recently; try again at `retry_at`

    action: Action
    retry_at: datetime | None = None


def backoff(consecutive_failures: int) -> timedelta:
    if consecutive_failures <= 0:
        return timedelta(0)
    wait: timedelta = BACKOFF_FIRST * (1 << min(consecutive_failures - 1, 16))
    return min(wait, BACKOFF_MAX)


def refresh_decision(
    *,
    in_flight: bool,
    consecutive_failures: int,
    last_attempt_at: datetime | None,
    now: datetime,
) -> RefreshDecision:
    """Concurrent refreshes of one source are deduplicated; errors back off (FRESH-04)."""
    if in_flight:
        return RefreshDecision(RefreshDecision.Action.JOIN)
    if consecutive_failures > 0 and last_attempt_at is not None:
        retry_at = last_attempt_at + backoff(consecutive_failures)
        if now < retry_at:
            return RefreshDecision(RefreshDecision.Action.BACK_OFF, retry_at)
    return RefreshDecision(RefreshDecision.Action.START)
