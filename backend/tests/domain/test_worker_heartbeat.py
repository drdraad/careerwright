"""The DBOS worker's health: healthy only while its last good pass is recent."""

import os
from pathlib import Path

import pytest

from careerwright.identity import heartbeat


@pytest.mark.req("ARC1-08")
def test_the_worker_is_healthy_only_while_its_last_good_pass_is_recent(tmp_path: Path) -> None:
    beat = tmp_path / "heartbeat"
    assert heartbeat.check(beat) == 1  # no pass yet

    heartbeat.beat(beat)
    written = beat.stat().st_mtime
    assert heartbeat.check(beat, now=written) == 0
    assert heartbeat.check(beat, now=written + heartbeat.HEARTBEAT_STALE_S - 1) == 0
    assert heartbeat.check(beat, now=written + heartbeat.HEARTBEAT_STALE_S) == 1

    os.utime(beat, (written - 60, written - 60))  # a stalled loop stops touching it
    assert heartbeat.check(beat, now=written) == 1
