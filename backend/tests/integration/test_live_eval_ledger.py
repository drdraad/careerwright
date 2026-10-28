"""`make live-eval`'s orchestration offline (ruling R5; MODEL-09, TEST1-10): the real API and a
real worker process with the fake model run two cases end to end; every attempt is ledgered
in the eval scope, the results record failures by type, and the key leaks nowhere. Nothing
contacts Meta: the fake's answers are not model behaviour, so failures are expected here."""

import secrets
from pathlib import Path

import pytest
from pydantic import SecretStr

from nessa.identity.model_choice import ModelChoice
from tests.integration.test_live_smoke_ledger import IntegrationTarget
from tests.support.client import ApiClient
from tests.support.infra import Infra
from tests.support.workers import start_worker
from tools.evaluation import load_cases
from tools.live_eval import authorise_eval, live_eval, select
from tools.live_smoke import ScopeBudget
from tools.usage_ledger import Ledger, ScopeSpend

pytestmark = pytest.mark.integration
TEST_MODEL = "muse-spark-1.3-contributor"


@pytest.mark.req("MODEL-09", "TEST1-10")
def test_every_case_attempt_is_ledgered_and_the_results_are_written(
    infra: Infra, api: ApiClient, tmp_path: Path
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    results = tmp_path / "live-eval.md"
    private = tmp_path / "nessa-home" / "evidence" / "live-eval.jsonl"
    models = ModelChoice.configure(TEST_MODEL, "muse-spark-1.3", "test")
    cases = select(load_cases(), ["INT-01", "DSC-01", "EXP-01"])
    plan = authorise_eval(
        models, cases, budget=ScopeBudget("eval-test", 99, 0, 10**9), spent=ScopeSpend(0, 0, 0)
    )
    worker = start_worker(infra, tmp_path / "worker.log")
    try:
        code = live_eval(
            IntegrationTarget(infra, api.http, worker),
            SecretStr(f"sk-eval-{secrets.token_urlsafe(32)}"),
            plan,
            ledger,
            models,
            scope="eval-test",
            results_path=results,
            observations_path=private,
        )
    finally:
        worker.kill_if_running()

    records = ledger.records()
    assert code == 0  # no leak
    assert len(records) == 4  # one attempt per run (EXP-01 has two), each reconciled
    assert {r.budget_scope for r in records} == {"eval-test"}
    assert all(r.estimated_cost_nano_usd is not None for r in records)
    written = results.read_text(encoding="utf-8")
    assert "| INT-01 " in written
    assert "| DSC-01 " in written
    assert "| EXP-01 " in written
    assert "explanation complete" in written
    assert "Failures by type:" in written
    assert "scope `eval-test`" in written  # re-review N-M5: each run names its budget scope
    # Each case's output is kept for inspection in the private evidence directory, never
    # beside the committed results (plan section 2; Task 6 review A-I-6).
    observed = private.read_text(encoding="utf-8").splitlines()
    assert len(observed) == 3
    assert not results.with_suffix(".jsonl").exists()
    assert private.parent.stat().st_mode & 0o777 == 0o700
    assert str(private) in written
