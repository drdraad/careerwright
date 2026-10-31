"""`make live-eval`: the representative evaluation cases on the live test model, through the
whole product, budget-capped (plan Sprint 2: "Run a budget-capped live version of
representative cases"; ruling R5).

The cases are those marked `live` in `tools/evaluation_cases.json` (at most
`MAX_LIVE_CASES`), or a chosen subset (`CASES=INT-01,DSC-01`). Each runs in its own
synthetic workspace in the isolated live stack (`tools.live_smoke.smoke_stack`): the key is
stored through the API with consent, the case's preferences and answers are saved, then one
interview turn or one discovery runs on the test model (an explanation case, not in the
default run, runs a discovery and then its slate's written explanation), and its result is
checked with the same semantic checks as the offline run. Only synthetic inputs are sent
(the test model is a Contributor model). Each workspace's limits allow exactly one attempt
per run (two requests at most: the call and one validation repair), so the product's own
reservation refuses any retry at cost.

Caps, checked before the stack starts, under the ledger's exclusive lock:
- per invocation: at most `MAX_LIVE_CASES` cases, no production model, and a worst-case cost
  cap;
- per budget scope (`live-eval`), cumulatively over the ledger: provider requests,
  production requests (none by default) and worst-case cost (`CAREERWRIGHT_LIVE_EVAL_*`).
Afterwards the worker is stopped and every attempt of every case workspace is ledgered in
`docs/evidence/live-usage.*` with its cost; the results, with failures by type, are
appended to `docs/evidence/live-eval.md`, each case's output to the private evidence
directory (`CAREERWRIGHT_HOME/evidence/live-eval.jsonl`, never committed); and both databases,
every container log and the API's responses are scanned for the key.

`--wonder` (`make live-eval WONDER=1`, Muse Wonder's qualification; ADR 0003, amendment of
2026-10-31) runs the cases on `muse-wonder-1.0` as the production model, still on synthetic
workspaces and cases only (Wonder is a Standard-mode model), under its own per-invocation cap
(`WONDER_MAX_COST_NANO_USD`) and in the scope `wonder-qualification`, which
`make live-smoke WONDER=1` shares: $0.50 in all, every request a production request.

Run from `backend/`: `uv run --locked python -m tools.live_eval [--cases INT-01,DSC-01]
[--wonder]`.
"""

import argparse
import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.model_registry import WONDER_MODEL_ID, format_usd
from careerwright.profile import discovery, interview, slate_explanation
from tools.evaluation import (
    Case,
    CaseKind,
    Failure,
    FailureType,
    evaluate,
    failures_by_type,
    load_cases,
    profile_input_of,
)
from tools.live_smoke import (
    WONDER_BUDGET,
    WONDER_SCOPE,
    Api,
    CapExceededError,
    ScopeBudget,
    SmokeKind,
    SmokeTarget,
    assert_attempt_bound,
    leak_findings,
    ledger_workspace_calls,
    smoke_stack,
)
from tools.localenv import REPO_ROOT, careerwright_home
from tools.usage_ledger import Ledger, ScopeSpend

MAX_LIVE_CASES = 6  # the cap for this task's live run (controller, R5)
MAX_COST_NANO_USD = 50_000_000  # $0.05 worst case per invocation
# Per budget scope, cumulatively: the controller's per-scope request cap (R5), which holds
# one default run (four cases, at most eight requests); a further authorised run gets its
# own scope (`CAREERWRIGHT_LIVE_EVAL_SCOPE`).
SCOPE_MAX_CALLS = 9
SCOPE_MAX_COST_NANO_USD = 50_000_000
# Per invocation with `--wonder` (Muse Wonder, the production model, in the shared scope
# `wonder-qualification`): two cases, such as an interview ($0.176 worst case on Wonder) and a
# discovery ($0.156), or one explanation case ($0.368).
WONDER_MAX_COST_NANO_USD = 400_000_000
RESULTS_PATH = REPO_ROOT / "docs" / "evidence" / "live-eval.md"
EVAL_INTERVIEW = SmokeKind(
    "eval_interview",
    1,
    interview.MAX_REQUESTS,
    interview.worst_case_nano_usd,
    "live evaluation: one interview case via API and DBOS worker (synthetic case; key "
    "opened just in time)",
)
EVAL_DISCOVERY = SmokeKind(
    "eval_discovery",
    1,
    discovery.MAX_REQUESTS,
    discovery.worst_case_nano_usd,
    "live evaluation: one discovery case via API and DBOS worker (synthetic case; key "
    "opened just in time)",
)
# A discovery, then its slate's written explanation: two runs of one attempt each, each
# reserved at the larger of the two kinds' worst cases.
EVAL_EXPLANATION = SmokeKind(
    "eval_explanation",
    2,
    max(discovery.MAX_REQUESTS, slate_explanation.MAX_REQUESTS),
    lambda model_id: max(
        discovery.worst_case_nano_usd(model_id), slate_explanation.worst_case_nano_usd(model_id)
    ),
    "live evaluation: one discovery and its slate's written explanation via API and DBOS "
    "worker (synthetic case; key opened just in time)",
)
KINDS = {
    CaseKind.INTERVIEW: EVAL_INTERVIEW,
    CaseKind.DISCOVERY: EVAL_DISCOVERY,
    CaseKind.EXPLANATION: EVAL_EXPLANATION,
}


class EvalSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    api_key: SecretStr = Field(validation_alias="META_API_KEY")
    meta_test_model: str = Field(
        default="muse-spark-1.3-contributor", validation_alias="CAREERWRIGHT_META_TEST_MODEL"
    )
    meta_production_model: str = Field(
        default="muse-spark-1.3", validation_alias="CAREERWRIGHT_META_PRODUCTION_MODEL"
    )
    budget_scope: str = Field(default="live-eval", validation_alias="CAREERWRIGHT_LIVE_EVAL_SCOPE")
    scope_max_calls: int = Field(
        default=SCOPE_MAX_CALLS, ge=0, validation_alias="CAREERWRIGHT_LIVE_EVAL_MAX_CALLS"
    )
    scope_max_cost_nano_usd: int = Field(
        default=SCOPE_MAX_COST_NANO_USD,
        ge=0,
        validation_alias="CAREERWRIGHT_LIVE_EVAL_MAX_COST_NANO_USD",
    )

    def budget(self) -> ScopeBudget:
        return ScopeBudget(self.budget_scope, self.scope_max_calls, 0, self.scope_max_cost_nano_usd)


def select(cases: list[Case], chosen: list[str] | None) -> list[Case]:
    """The live cases, or the named ones; refused if any is not a live-capable kind or the
    paired case of a chosen one is missing."""
    by_id = {case.id: case for case in cases}
    if chosen is None:
        picked = [case for case in cases if case.live]
    else:
        unknown = [case_id for case_id in chosen if case_id not in by_id]
        if unknown:
            raise CapExceededError(f"no such cases: {unknown}")
        picked = [by_id[case_id] for case_id in chosen]
    wrong = [case.id for case in picked if case.kind not in KINDS]
    if wrong:
        raise CapExceededError(f"only interview, discovery and explanation cases run live: {wrong}")
    return picked


@dataclass(frozen=True)
class Plan:
    model_id: str
    cases: list[Case]
    calls: int
    worst_case_nano_usd: int
    production: bool = False  # Muse Wonder's qualification (`--wonder`)


def authorise_eval(
    models: ModelChoice,
    cases: list[Case],
    *,
    budget: ScopeBudget,
    spent: ScopeSpend,
    production: bool = False,
) -> Plan:
    """The model and the invocation's bounds, or a refusal before any call: the test model,
    or with `production` (Muse Wonder's qualification) the production model, under its own
    per-invocation cap and the scope's production-request cap."""
    if not 1 <= len(cases) <= MAX_LIVE_CASES:
        raise CapExceededError(f"1-{MAX_LIVE_CASES} live cases per invocation, not {len(cases)}")
    model_id = models.production.model_id if production else models.test.model_id
    if models.is_production(model_id) and not production:
        raise CapExceededError("the test model is the production model: refusing")
    calls = sum(KINDS[case.kind].calls() for case in cases)
    worst = sum(
        KINDS[case.kind].attempts * KINDS[case.kind].per_attempt_nano_usd(model_id)
        for case in cases
    )
    cap = WONDER_MAX_COST_NANO_USD if production else MAX_COST_NANO_USD
    if worst > cap:
        raise CapExceededError(f"worst case {format_usd(worst)} exceeds the cap {format_usd(cap)}")
    if spent.calls + calls > budget.max_calls:
        raise CapExceededError(
            f"scope {budget.scope}: {spent.calls} of {budget.max_calls} calls used, "
            f"{calls} more needed"
        )
    if production and spent.production_calls + calls > budget.max_production_calls:
        raise CapExceededError(
            f"scope {budget.scope}: {spent.production_calls} of {budget.max_production_calls} "
            f"production calls used, {calls} more needed"
        )
    if spent.committed_nano_usd + worst > budget.max_cost_nano_usd:
        raise CapExceededError(
            f"scope {budget.scope}: {format_usd(spent.committed_nano_usd)} of "
            f"{format_usd(budget.max_cost_nano_usd)} committed, worst case {format_usd(worst)} "
            "more"
        )
    return Plan(model_id, cases, calls, worst, production)


def _wait(api: Api, path: str, run_of: Callable[[dict[str, Any]], dict[str, Any]]) -> Any:
    deadline = time.monotonic() + EVAL_INTERVIEW.run_timeout_s()
    body = api.call("GET", path)
    while run_of(body)["status"] in ("queued", "running") and time.monotonic() < deadline:
        time.sleep(1)
        body = api.call("GET", path)
    return body


@dataclass
class CaseRun:
    case: Case
    workspace_id: str
    observed: dict[str, Any] | None = None
    status: str = "not started"


def _prepare(api: Api, case: Case, model_id: str, key: SecretStr) -> CaseRun:
    workspace = api.call(
        "POST",
        "/v1/workspaces",
        {
            "name": f"Live eval {case.id} (synthetic)",
            "data_mode": "live_assisted",
            "synthetic": True,
        },
    )
    run = CaseRun(case, workspace["workspace_id"])
    base = f"/v1/workspaces/{run.workspace_id}"
    # An explanation case's first run is its discovery; the explanation gets limits of its
    # own once the discovery has settled (`_explain`).
    per_attempt = (
        discovery.worst_case_nano_usd(model_id)
        if case.kind is CaseKind.EXPLANATION
        else KINDS[case.kind].per_attempt_nano_usd(model_id)
    )
    spend = api.call(
        "PUT",
        f"{base}/spend/limits",
        {
            "expected_version": 0,
            "run_limit_nano_usd": per_attempt,
            "period_limit_nano_usd": per_attempt,
        },
    )
    assert_attempt_bound(spend, per_attempt, 1)
    api.call(
        "POST",
        f"{base}/credentials",
        {"api_key": key.get_secret_value(), "consent_to_encrypted_storage": True},
    )
    if case.entry_mode or case.conversation_mode:
        api.call(
            "PUT",
            f"{base}/interview/preferences",
            {
                "expected_version": 0,
                "entry_mode": case.entry_mode,
                "conversation_mode": case.conversation_mode,
                "paused": False,
            },
        )
    if case.profile:
        api.call(
            "PUT",
            f"{base}/profile",
            {"expected_version": 0, "profile": profile_input_of(case.profile)},
        )
    return run


def _drive(api: Api, run: CaseRun, model_id: str) -> None:
    base = f"/v1/workspaces/{run.workspace_id}"
    version = api.call("GET", f"{base}/profile")["version"]
    if run.case.kind is CaseKind.INTERVIEW:
        submitted = api.call(
            "POST",
            f"{base}/interview/turns",
            {"expected_profile_version": version, "message": run.case.message},
        )
        turn = _wait(api, f"{base}/interview/turns/{submitted['turn_id']}", lambda b: b["run"])
        run.status, run.observed = turn["run"]["status"], turn
        return
    submitted = api.call("POST", f"{base}/discoveries", {"expected_profile_version": version})
    found = _wait(api, f"{base}/discoveries/{submitted['discovery_id']}", lambda b: b["run"])
    run.status = found["run"]["status"]
    if run.status != "complete":
        return
    first_view = api.call("GET", f"{base}/discoveries/{submitted['discovery_id']}/slate")
    if run.case.kind is CaseKind.DISCOVERY:
        # Each suggestion's essential skills from the taxonomy, as the offline run keeps them.
        essential = {}
        for suggestion in first_view["suggestions"]:
            detail = api.call("GET", f"/v1/taxonomy/occupations/{suggestion['concept_id']}")
            essential[suggestion["concept_id"]] = [
                s["preferred_label"] for s in detail["skills"] if s["relation"] == "essential"
            ]
        run.observed = {**first_view, "essential_skills": essential}
        return
    explained = _explain(api, run, version, first_view, model_id)
    run.status = f"discovery complete, explanation {explained}"


def _explain(
    api: Api, run: CaseRun, version: int, first_view: dict[str, Any], model_id: str
) -> str:
    """The slate's explanation, after limits that allow exactly one attempt of it; returns
    its run's status, and keeps the observation with ESCO's records from the taxonomy."""
    base = f"/v1/workspaces/{run.workspace_id}"
    worst = slate_explanation.worst_case_nano_usd(model_id)
    spend = api.call("GET", f"{base}/spend")
    limits = api.call(
        "PUT",
        f"{base}/spend/limits",
        {
            "expected_version": spend["version"],
            "run_limit_nano_usd": worst,
            "period_limit_nano_usd": spend["period_committed_nano_usd"] + worst,
        },
    )
    assert_attempt_bound(limits, worst, 1)
    discovery_id = first_view["discovery_id"]
    api.call(
        "POST",
        f"{base}/discoveries/{discovery_id}/explanation",
        {"expected_profile_version": version},
    )
    found = _wait(api, f"{base}/discoveries/{discovery_id}", lambda b: b["explanation"]["run"])
    records = {}
    for suggestion in first_view["suggestions"]:
        detail = api.call("GET", f"/v1/taxonomy/occupations/{suggestion['concept_id']}")
        essential = [s["preferred_label"] for s in detail["skills"] if s["relation"] == "essential"]
        records[suggestion["concept_id"]] = [
            detail["preferred_label"],
            detail["description"],
            *essential,
        ]
    run.observed = {"slate": first_view, "explanation": found["explanation"], "records": records}
    status: str = found["explanation"]["run"]["status"]
    return status


def results_of(runs: list[CaseRun]) -> dict[str, list[Failure]]:
    observed = {run.case.id: run.observed for run in runs if run.observed is not None}
    results: dict[str, list[Failure]] = {}
    for run in runs:
        if run.observed is None or (
            run.case.kind is CaseKind.INTERVIEW and run.observed.get("proposal") is None
        ):
            results[run.case.id] = [Failure(FailureType.SCHEMA_INVALID, f"run {run.status}")]
        else:
            results[run.case.id] = evaluate(run.case, run.observed, observed)
    return results


def _shown(path: Path) -> str:
    """A private path as the committed results name it: relative to CAREERWRIGHT_HOME, so no
    machine's home directory is written into the repository."""
    home = careerwright_home()
    return f"CAREERWRIGHT_HOME/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)


def write_results(
    path: Path,
    observations_path: Path,
    plan: Plan,
    runs: list[CaseRun],
    results: dict[str, list[Failure]],
    seqs: list[int],
    scope: str,
) -> None:
    lines = [
        f"## Live evaluation, {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        "",
        f"Budget scope `{scope}`. "
        f"Model `{plan.model_id}` ({'production' if plan.production else 'test'} model, "
        f"synthetic cases only); {len(runs)} cases; at most "
        f"{plan.calls} requests, worst case {format_usd(plan.worst_case_nano_usd)}; ledger rows "
        f"{seqs}. Failures by type: {failures_by_type(results) or 'none'}. Each case's output "
        f"is kept in the private evidence directory (`{_shown(observations_path)}`, not "
        "committed).",
        "",
        "| Case | Kind | Run | Result | Failures |",
        "|---|---|---|---|---|",
    ]
    for run in runs:
        failures = results.get(run.case.id, [])
        listed = "; ".join(f"{f.type.value}: {f.detail}" for f in failures) or "-"
        verdict = "pass" if not failures else "fail"
        lines.append(
            f"| {run.case.id} {run.case.title} | {run.case.kind.value} | {run.status} "
            f"| {verdict} | {listed.replace('|', '/')} |"
        )
    header = (
        "# Live evaluation results\n\nGenerated by `backend/tools/live_eval.py` (`make "
        "live-eval`); costs are in `live-usage.md`. Semantic checks only, never exact prose. "
        "A live pass is evidence for the tested model, prompt and case only.\n\n"
    )
    previous = path.read_text(encoding="utf-8") if path.exists() else header
    path.write_text(previous + "\n".join(lines) + "\n\n", encoding="utf-8")
    # What each case returned (synthetic inputs only), so a failure can be inspected later:
    # model output stays out of the repository, owner-only (plan section 2).
    observations_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    observations_path.parent.chmod(0o700)
    observations_path.touch(mode=0o600, exist_ok=True)
    observations_path.chmod(0o600)  # `tools.localenv.check_permissions` refuses anything wider
    with observations_path.open("a", encoding="utf-8") as observations:
        for run in runs:
            record = {
                "recorded_at": datetime.now(UTC).isoformat(),
                "model_id": plan.model_id,
                "case": run.case.id,
                "status": run.status,
                "failures": [
                    {"type": f.type.value, "detail": f.detail} for f in results[run.case.id]
                ],
                "observed": run.observed,
            }
            observations.write(json.dumps(record, ensure_ascii=False) + "\n")


def live_eval(
    target: SmokeTarget,
    key: SecretStr,
    plan: Plan,
    ledger: Ledger,
    models: ModelChoice,
    *,
    scope: str,
    results_path: Path = RESULTS_PATH,
    observations_path: Path | None = None,
) -> int:
    """Every case through the product, then the ledger (after the worker has stopped,
    whatever happened), the results and the leak scan."""
    api = Api(target, target.sign_in())
    runs: list[CaseRun] = []
    worker_stopped = True
    try:
        for case in plan.cases:
            run = _prepare(api, case, plan.model_id, key)
            runs.append(run)
            _drive(api, run, plan.model_id)
            print(f"{case.id}: {run.status}", flush=True)
    finally:
        interrupted: BaseException | None = None
        try:
            target.stop_worker()
        except Exception:
            worker_stopped = False
        except BaseException as interrupt:  # Ctrl-C during the stop: ledger first, then obey
            worker_stopped = False
            interrupted = interrupt
        seqs: list[int] = []
        for run in runs:
            seqs += ledger_workspace_calls(
                ledger,
                target,
                run.workspace_id,
                model_id=plan.model_id,
                models=models,
                scope=scope,
                worker_stopped=worker_stopped,
                kind=KINDS[run.case.kind],
            )
        ledger.write_markdown()
        print(f"ledger rows appended: {seqs}", flush=True)
        if interrupted is not None:
            raise interrupted
    results = results_of(runs)
    observed_at = observations_path or careerwright_home() / "evidence" / "live-eval.jsonl"
    write_results(results_path, observed_at, plan, runs, results, seqs, scope)
    print(f"failures by type: {failures_by_type(results)}", flush=True)
    scanned, findings = leak_findings(target, api, key)
    print(f"leak scan: {scanned} rows/logs/responses, findings: {findings}", flush=True)
    if not worker_stopped:
        raise RuntimeError("the worker could not be confirmed stopped; possible calls ledgered")
    return 1 if findings else 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", help="comma-separated case IDs (default: the live cases)")
    parser.add_argument(
        "--wonder",
        action="store_true",
        help=f"run the cases on Muse Wonder as the production model, in the scope {WONDER_SCOPE}",
    )
    args = parser.parse_args(argv)
    settings = EvalSettings()
    production_model = WONDER_MODEL_ID if args.wonder else settings.meta_production_model
    models = ModelChoice.configure(
        settings.meta_test_model, production_model, "production" if args.wonder else "test"
    )
    budget = WONDER_BUDGET if args.wonder else settings.budget()
    chosen = args.cases.split(",") if args.cases else None
    cases = select(load_cases(), chosen)
    ledger = Ledger()
    with ledger.exclusive():
        plan = authorise_eval(
            models, cases, budget=budget, spent=ledger.spent(budget.scope), production=args.wonder
        )
        print(
            f"live eval: model {plan.model_id} ({'production' if args.wonder else 'test'}); "
            f"{len(cases)} cases; at most {plan.calls} requests, worst case "
            f"{format_usd(plan.worst_case_nano_usd)}; scope {budget.scope}",
            flush=True,
        )
        with smoke_stack(
            production=args.wonder, production_model=WONDER_MODEL_ID if args.wonder else None
        ) as target:
            code = live_eval(target, settings.api_key, plan, ledger, models, scope=budget.scope)
    sys.exit(code)


if __name__ == "__main__":
    main()
