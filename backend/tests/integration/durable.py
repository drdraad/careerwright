"""A durable-run scenario: a synthetic workspace with a stored key, real worker processes and
a leak scan of both databases and every worker log (shared by the durable test modules)."""

import json
import secrets
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tests.support.client import ApiClient, profile_with
from tests.support.infra import Infra
from tests.support.workers import Worker, start_worker, wait_for
from tools.leak_scan import Finding, Needle, scan

RUN_TIMEOUT_S = 60.0
TERMINAL = frozenset({"complete", "failed", "provider_unavailable", "cancelled"})


@dataclass
class Scenario:
    infra: Infra
    api: ApiClient
    token: str
    workspace_id: str
    api_key: str
    profile_sentinel: str
    output_sentinel: str
    log_dir: Path
    logs: list[Path] = field(default_factory=list)
    workers: list[Worker] = field(default_factory=list)
    retired_keys: list[str] = field(default_factory=list)  # replaced keys, still scanned for

    def submit(self) -> str:
        response = self.api.write(
            "POST",
            f"/v1/workspaces/{self.workspace_id}/runs",
            self.token,
            {"kind": "connection_check"},
        )
        assert response.status_code == 202, response.text
        return str(response.json()["run_id"])

    def worker(self, name: str, **settings: str) -> Worker:
        log = self.log_dir / f"{name}.log"
        self.logs.append(log)
        started = start_worker(self.infra, log, output_sentinel=self.output_sentinel, **settings)
        self.workers.append(started)
        return started

    def run(self, run_id: str) -> dict[str, Any]:
        return self.infra.query("SELECT * FROM nessa.runs WHERE run_id = %s", (run_id,))[0]

    def api_run(self, run_id: str) -> dict[str, Any]:
        response = self.api.get(f"/v1/workspaces/{self.workspace_id}/runs/{run_id}", self.token)
        body: dict[str, Any] = response.json()
        return body

    def attempts(self, run_id: str) -> list[dict[str, Any]]:
        return self.infra.query(
            "SELECT * FROM nessa.model_attempts WHERE run_id = %s ORDER BY attempt_id", (run_id,)
        )

    def outputs(self, run_id: str) -> list[dict[str, Any]]:
        return self.infra.query("SELECT * FROM nessa.run_outputs WHERE run_id = %s", (run_id,))

    def wait_terminal(self, run_id: str, timeout_s: float = RUN_TIMEOUT_S) -> dict[str, Any]:
        wait_for(lambda: self.run(run_id)["status"] in TERMINAL, timeout_s=timeout_s, what="run")
        return self.run(run_id)

    def journal(self, run_id: str) -> dict[str, list[dict[str, Any]]]:
        workflow = f"nessa-run-{run_id}"
        db = "nessa_dbos"
        q = self.infra.query
        return {
            "status": q(
                "SELECT * FROM dbos.workflow_status WHERE workflow_uuid = %s",
                (workflow,),
                database=db,
            ),
            "inputs": q(
                "SELECT inputs FROM dbos.workflow_input WHERE workflow_uuid = %s",
                (workflow,),
                database=db,
            ),
            "output": q(
                "SELECT output, error FROM dbos.workflow_output WHERE workflow_uuid = %s",
                (workflow,),
                database=db,
            ),
            "steps": q(
                "SELECT function_name, output, error FROM dbos.operation_outputs "
                "WHERE workflow_uuid = %s ORDER BY function_id",
                (workflow,),
                database=db,
            ),
        }

    def assert_identifier_only_journal(self, run_id: str) -> dict[str, Any]:
        journal = self.journal(run_id)
        assert json.loads(journal["inputs"][0]["inputs"]) == {
            "positionalArgs": [run_id],
            "namedArgs": {},
        }
        output: dict[str, Any] = json.loads(journal["output"][0]["output"])
        assert set(output) in ({"status", "output_id"}, {"status", "failure_class"})
        assert {s["function_name"] for s in journal["steps"]} <= {
            "nessa.bounded_model_activity",
            "nessa.publish_outcome",
        }
        return output

    def leaks(self) -> list[Finding]:
        """The key nowhere; the profile's private text never outside the application tables
        that own it; the model's output only sealed."""
        logs = [(log.name, log.read_text(encoding="utf-8")) for log in self.logs if log.exists()]
        dbos = self.infra.database_cells("nessa_dbos")
        app = self.infra.database_cells("nessa_app")
        keys = [
            Needle("credential", key, fragment_length=12)
            for key in (self.api_key, *self.retired_keys)
        ]
        output = Needle("model output", self.output_sentinel)
        profile = Needle("profile private text", self.profile_sentinel)
        return [
            *scan([*app, *dbos, *logs], [*keys, output]),
            *scan([*dbos, *logs], [profile]),
        ]


def make_scenario(infra: Infra, api: ApiClient, token: str, log_dir: Path) -> Scenario:
    workspace_id = api.create_workspace(token, "Durable run (synthetic)")["workspace_id"]
    # No fixed prefix: every 12-character window must be secret material, or the fragment
    # scan matches public strings (a Sprint 0 false positive).
    api_key = secrets.token_urlsafe(32)
    stored = api.write(
        "POST",
        f"/v1/workspaces/{workspace_id}/credentials",
        token,
        {"api_key": api_key, "consent_to_encrypted_storage": True},
    )
    assert stored.status_code == 201, stored.text
    profile_sentinel = f"PRIVATE-PROFILE-{secrets.token_hex(6)}"
    api.write(
        "PUT",
        f"/v1/workspaces/{workspace_id}/profile",
        token,
        {"expected_version": 0, "profile": profile_with(current_role=profile_sentinel)},
    )
    return Scenario(
        infra=infra,
        api=api,
        token=token,
        workspace_id=workspace_id,
        api_key=api_key,
        profile_sentinel=profile_sentinel,
        output_sentinel=f"OUTPUT-SENTINEL-{uuid.uuid4().hex[:12]}",
        log_dir=log_dir,
    )
