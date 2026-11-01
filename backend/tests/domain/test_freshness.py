"""Freshness enforced on access (spec section 11; FRESH-02, FRESH-03, FRESH-04). Pure."""

from datetime import UTC, datetime, timedelta

import pytest

from careerwright.evidence.freshness import (
    MAX_UNVERIFIED_AGE,
    Freshness,
    FreshnessKind,
    RefreshDecision,
    SourceTimes,
    freshness,
    refresh_decision,
)

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def times(
    verified_hours_ago: float | None,
    *,
    attempted_hours_ago: float | None = None,
    valid_until: datetime | None = None,
    valid_from: datetime | None = None,
) -> SourceTimes:
    success = None if verified_hours_ago is None else NOW - timedelta(hours=verified_hours_ago)
    attempt = success if attempted_hours_ago is None else NOW - timedelta(hours=attempted_hours_ago)
    return SourceTimes(
        last_attempt_at=attempt,
        last_success_at=success,
        published_at=None,
        valid_from=valid_from,
        valid_until=valid_until,
    )


@pytest.mark.req("FRESH-02")
@pytest.mark.parametrize(
    ("kind", "limit"),
    [
        (FreshnessKind.JOB, timedelta(hours=24)),
        (FreshnessKind.COURSE_FEE_INTAKE, timedelta(days=7)),
        (FreshnessKind.FUNDING_AVAILABILITY, timedelta(hours=48)),
        (FreshnessKind.FUNDING_RULES, timedelta(days=30)),
        (FreshnessKind.COURSE_SYLLABUS, timedelta(days=90)),
    ],
)
def test_each_kind_is_current_up_to_its_maximum_age_and_not_after(
    kind: FreshnessKind, limit: timedelta
) -> None:
    assert MAX_UNVERIFIED_AGE[kind] == limit
    hours = limit.total_seconds() / 3600

    assert freshness(kind, times(hours), closed=False, now=NOW).state is not Freshness.STALE
    assert freshness(kind, times(hours + 0.01), closed=False, now=NOW).state is Freshness.STALE


@pytest.mark.req("FRESH-02")
def test_a_job_past_24_hours_awaits_recheck_and_is_never_shown_as_currently_available() -> None:
    view = freshness(FreshnessKind.JOB, times(25), closed=False, now=NOW)

    assert view.state is Freshness.STALE
    assert view.label == "awaiting recheck"
    assert not view.usable_as_current


@pytest.mark.req("FRESH-02")
def test_funding_rules_carry_a_stale_warning_after_a_week_within_their_30_days() -> None:
    view = freshness(FreshnessKind.FUNDING_RULES, times(24 * 8), closed=False, now=NOW)

    assert view.state is Freshness.CURRENT_WITH_WARNING
    assert view.usable_as_current


@pytest.mark.req("FRESH-03")
def test_a_failed_refresh_never_extends_validity() -> None:
    verified_23h_ago_then_refresh_failed_just_now = times(23, attempted_hours_ago=0)
    an_hour_later = NOW + timedelta(hours=2)

    view = freshness(
        FreshnessKind.JOB,
        verified_23h_ago_then_refresh_failed_just_now,
        closed=False,
        now=an_hour_later,
    )

    assert view.state is Freshness.STALE  # measured from the last success, not the attempt


@pytest.mark.req("FRESH-03")
def test_never_verified_is_its_own_state_not_current_and_not_closed() -> None:
    view = freshness(FreshnessKind.JOB, times(None, attempted_hours_ago=1), closed=False, now=NOW)

    assert view.state is Freshness.NEVER_VERIFIED
    assert not view.usable_as_current


@pytest.mark.req("FRESH-02")
def test_an_expiry_date_overrides_the_maximum_age_and_closure_overrides_both() -> None:
    expired = freshness(
        FreshnessKind.JOB, times(1, valid_until=NOW - timedelta(minutes=1)), closed=False, now=NOW
    )
    closed = freshness(FreshnessKind.JOB, times(1), closed=True, now=NOW)

    assert expired.state is Freshness.EXPIRED
    assert closed.state is Freshness.CLOSED
    assert not expired.usable_as_current
    assert not closed.usable_as_current


@pytest.mark.req("FRESH-03")
def test_not_yet_valid_is_not_current() -> None:
    view = freshness(
        FreshnessKind.COURSE_FEE_INTAKE,
        times(1, valid_from=NOW + timedelta(days=3)),
        closed=False,
        now=NOW,
    )

    assert view.state is Freshness.NOT_YET_VALID


@pytest.mark.req("FRESH-03")
def test_the_view_keeps_the_separate_timestamps_and_the_verified_until_time() -> None:
    source = times(2, attempted_hours_ago=1)
    view = freshness(FreshnessKind.JOB, source, closed=False, now=NOW)

    assert view.times == source
    assert view.verified_until == NOW - timedelta(hours=2) + timedelta(hours=24)


@pytest.mark.req("FRESH-04")
def test_a_refresh_already_in_flight_is_joined_not_repeated() -> None:
    decision = refresh_decision(
        in_flight=True, consecutive_failures=0, last_attempt_at=None, now=NOW
    )

    assert decision.action is RefreshDecision.Action.JOIN


@pytest.mark.req("FRESH-04")
@pytest.mark.parametrize(
    ("failures", "wait"),
    [
        (1, timedelta(minutes=1)),
        (2, timedelta(minutes=2)),
        (3, timedelta(minutes=4)),
        (12, timedelta(hours=1)),
    ],
)
def test_errors_back_off_exponentially_up_to_an_hour(failures: int, wait: timedelta) -> None:
    last = NOW - timedelta(seconds=5)

    early = refresh_decision(
        in_flight=False, consecutive_failures=failures, last_attempt_at=last, now=NOW
    )
    after = refresh_decision(
        in_flight=False, consecutive_failures=failures, last_attempt_at=last, now=last + wait
    )

    assert early.action is RefreshDecision.Action.BACK_OFF
    assert early.retry_at == last + wait
    assert after.action is RefreshDecision.Action.START


def test_a_first_refresh_starts() -> None:
    decision = refresh_decision(
        in_flight=False, consecutive_failures=0, last_attempt_at=None, now=NOW
    )

    assert decision.action is RefreshDecision.Action.START
