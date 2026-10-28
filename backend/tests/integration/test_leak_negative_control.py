"""The leak scan detects a real leak (ARC1-06): the naive DBOSDurability composition puts the
model's output into `dbos.operation_outputs`, and the same scan that passes for Nessa's own
runs finds it there. ADR 0002 decision 10 rests on this."""

import secrets
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from tests.support.infra import Infra
from tests.support.workers import BACKEND
from tools.leak_scan import Needle, scan

pytestmark = pytest.mark.integration


@pytest.mark.req("ARC1-06")
def test_the_scan_finds_the_output_the_durability_capability_journals(
    infra: Infra, tmp_path: Path
) -> None:
    sentinel = f"OUTPUT-SENTINEL-{uuid.uuid4().hex[:12]}"
    key = secrets.token_urlsafe(32)
    log = tmp_path / "probe.log"
    with log.open("wb") as handle:
        subprocess.run(
            [sys.executable, "-m", "tests.support.capability_probe"],
            cwd=BACKEND,
            env={
                **infra.worker_env(),
                "NESSA_TEST_OUTPUT_SENTINEL": sentinel,
                "NESSA_TEST_PROBE_KEY": key,
                "PYDANTIC_AI_NO_BANNER": "1",
            },
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=120,
        )

    findings = scan(infra.database_cells("nessa_dbos"), [Needle("model output", sentinel)])

    assert ("dbos.operation_outputs", "model output") in {
        (f.location, f.needle_label) for f in findings
    }
