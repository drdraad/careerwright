"""What an attempt records (spec section 18, SourceAttempt; Task 7A fix round 1): its labels
are a fixed set the database also holds to, and a kept body that does not match its hash is
a labelled failure, never a success without its body (review B M6, I6)."""

import base64
import hashlib
import re
from datetime import UTC, datetime

import pytest

from nessa.evidence.acquire import AcquisitionResult
from nessa.evidence.acquisition import _kept_body_checked
from nessa.evidence.addresses import UrlRefusal
from nessa.evidence.records import (
    AttemptReason,
    AttemptStatus,
    BodyNotKept,
    ClaimField,
    Extraction,
    InputRoute,
    Retention,
    RightsClass,
)
from nessa.migrations.versions import r0017_job_merge_and_claim_integrity as r0017
from nessa.migrations.versions import r0018_internal_error_reason as r0018
from nessa.migrations.versions import r0019_only_an_api_says_none as r0019
from nessa.migrations.versions import r0026_link_detail as r0026

BODY = b"<html>synthetic</html>"


def _quoted(constraint: str) -> set[str]:
    """The reasons the latest migration that sets the constraint allows (0018)."""
    found = re.search(rf"{constraint} CHECK \(reason IN \((.*?)\)\)", r0018.SCHEMA, re.DOTALL)
    assert found is not None
    return set(re.findall(r"'([a-z_]+)'", found.group(1)))


def test_the_database_holds_attempt_reasons_to_the_code_s_labels() -> None:
    assert _quoted("attempt_reasons_are_labels") == {r.value for r in AttemptReason}
    assert {r.value for r in UrlRefusal} <= {r.value for r in AttemptReason}
    extraction = re.search(r"extraction IN \((.*?)\)\)", r0019.SCHEMA, re.DOTALL)  # latest
    assert extraction is not None
    assert set(re.findall(r"'([a-z_]+)'", extraction.group(1))) == {e.value for e in Extraction}


def test_the_database_holds_why_a_body_was_not_kept_to_the_code_s_reasons() -> None:
    found = re.search(r"body_not_kept IN \((.*?)\)\)", r0026.SCHEMA, re.DOTALL)  # latest

    assert found is not None
    assert set(re.findall(r"'([a-z_]+)'", found.group(1))) == {b.value for b in BodyNotKept}


def test_the_database_holds_claim_fields_to_the_code_s_fields() -> None:
    found = re.search(r"field IN \((.*?)\)\)", r0017.SCHEMA, re.DOTALL)

    assert found is not None
    assert set(re.findall(r"'([a-z_]+)'", found.group(1))) == {f.value for f in ClaimField}


def _kept(body: bytes | None, sha256: str) -> AcquisitionResult:
    return AcquisitionResult(
        route=InputRoute.FETCH,
        provider="www.gov.uk",
        requested_url="https://www.gov.uk/x",
        status=AttemptStatus.SUCCEEDED,
        content_sha256=sha256,
        rights_class=RightsClass.GOVUK,
        retention=Retention.BODY,
        body_b64=base64.b64encode(body).decode() if body is not None else None,
        fetched_at=datetime(2026, 10, 29, tzinfo=UTC),
    )


@pytest.mark.req("ACQ-06")
def test_a_kept_body_that_matches_its_hash_is_kept() -> None:
    result = _kept(BODY, hashlib.sha256(BODY).hexdigest())

    assert _kept_body_checked(result) is result


@pytest.mark.req("ACQ-06")
@pytest.mark.parametrize("body", [b"something else", None], ids=["a different body", "none"])
def test_a_kept_body_that_does_not_match_its_hash_fails_the_attempt_with_a_label(
    body: bytes | None,
) -> None:
    checked = _kept_body_checked(_kept(body, hashlib.sha256(BODY).hexdigest()))

    assert (checked.status, checked.reason, checked.transient) == (
        AttemptStatus.FAILED,
        AttemptReason.BODY_HASH_MISMATCH,
        False,
    )
    assert (checked.body_b64, checked.retention, checked.copies) == (None, None, [])
