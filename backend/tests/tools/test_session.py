"""The live session's command, caps and ledger copy (Task 3b; ADR 0003, amendment), offline:
nothing here starts a stack or contacts Meta."""

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from careerwright.api.routes_credentials import ESTIMATED_KINDS
from careerwright.config import ApiSettings
from careerwright.identity.activity import run_worst_case_nano_usd
from careerwright.identity.model_choice import ModelChoice
from careerwright.identity.model_registry import WONDER_MODEL_ID
from careerwright.identity.records import RunKind
from careerwright.identity.spend import BudgetScope, SpendLimits, refused_scope
from careerwright.worker import TASKS
from tools.localenv import REPO_ROOT
from tools.session import (
    COPIED_COLUMNS,
    SESSION_RUN_LIMIT_NANO_USD,
    SESSION_SPEND_PER_WORKSPACE_NANO_USD,
    SessionCap,
    session_entry,
    session_limits,
    session_stack,
    session_summary,
)
from tools.stack import DEFAULT_PROJECT, Stack
from tools.stack import main as stack_main
from tools.usage_ledger import CallOutcome, Ledger


@pytest.mark.req("MODEL-11")
def test_the_session_is_the_normal_live_stack_with_wonder_and_the_session_s_caps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CAREERWRIGHT_PROJECT", raising=False)
    stack = session_stack()
    env = dict(stack.overrides)

    assert (stack.project, stack.live) == (DEFAULT_PROJECT, True)  # the data `make dev` uses
    assert env == {
        "CAREERWRIGHT_META_PRODUCTION_MODEL": "muse-wonder-1.0",
        "CAREERWRIGHT_SYNTHETIC_MODEL_ROLE": "test",
        "CAREERWRIGHT_DEFAULT_RUN_SPEND_LIMIT_NANO_USD": "750000000",
        "CAREERWRIGHT_DEFAULT_PERIOD_SPEND_LIMIT_NANO_USD": "5000000000",
    }
    # The test model is never touched: synthetic workspaces keep it.
    models = ModelChoice.configure(
        "muse-spark-1.3-contributor", env["CAREERWRIGHT_META_PRODUCTION_MODEL"], "test"
    )
    assert models.for_workspace(synthetic=True).model_id == "muse-spark-1.3-contributor"
    assert models.for_workspace(synthetic=False).model_id == WONDER_MODEL_ID


@pytest.mark.req("MODEL-11", "BND1-14")
def test_make_session_and_make_stop_act_on_the_same_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CAREERWRIGHT_PROJECT, left set in a shell, steers every stack command the same way:
    `make stop` can never stop one stack while `make session` started another."""
    stopped: list[str] = []

    def stop(self: Stack, services: tuple[str, ...] = ()) -> str:  # Docker is the system edge
        stopped.append(self.project)
        return "stopped"

    monkeypatch.setattr(Stack, "stop", stop)
    monkeypatch.setenv("CAREERWRIGHT_HOME", str(tmp_path))
    monkeypatch.delenv("CAREERWRIGHT_PROJECT", raising=False)
    stack_main(["stop"])
    assert session_stack().project == stopped[-1] == DEFAULT_PROJECT

    monkeypatch.setenv("CAREERWRIGHT_PROJECT", "careerwright-l0-elsewhere")
    stack_main(["stop"])
    assert session_stack().project == stopped[-1] == "careerwright-l0-elsewhere"


@pytest.mark.req("MODEL-11", "MODEL-08")
@pytest.mark.parametrize("kind", list(TASKS))
def test_every_run_fits_the_session_s_run_cap_on_wonder_and_the_session_cap_stops_spend(
    kind: RunKind,
) -> None:
    """The product's own reservation rule with the session's limits: all three attempts of
    any run kind fit the run cap on Wonder, so an outage is never called an exceeded budget,
    and once a workspace's $5 is nearly spent its next attempt is refused before its call."""
    per_attempt = TASKS[kind].worst_case_nano_usd(WONDER_MODEL_ID)
    committed = 1_234_567  # spent this month before the session
    command = session_limits(spend(committed))
    limits = SpendLimits(command["run_limit_nano_usd"], command["period_limit_nano_usd"])

    assert run_worst_case_nano_usd(TASKS[kind].worst_case_nano_usd, WONDER_MODEL_ID) <= (
        SESSION_RUN_LIMIT_NANO_USD
    )
    for attempt in range(3):
        assert (
            refused_scope(
                limits,
                period_committed=committed + attempt * per_attempt,
                run_committed=attempt * per_attempt,
                worst_case=per_attempt,
            )
            is None
        )
    nearly_spent = committed + SESSION_SPEND_PER_WORKSPACE_NANO_USD - per_attempt + 1
    assert (
        refused_scope(
            limits, period_committed=nearly_spent, run_committed=0, worst_case=per_attempt
        )
        is BudgetScope.PERIOD
    )


def spend(committed: int, version: int = 3) -> dict[str, Any]:
    return {
        "version": version,
        "run_limit_nano_usd": 150_000_000,
        "period_limit_nano_usd": 1_000_000_000,
        "period_committed_nano_usd": committed,
    }


@pytest.mark.req("MODEL-11")
def test_the_session_adds_five_dollars_to_what_the_workspace_s_month_has_committed() -> None:
    assert session_limits(spend(420_000_000)) == {
        "expected_version": 3,  # an expected-version command: a change meanwhile is refused
        "run_limit_nano_usd": 750_000_000,
        "period_limit_nano_usd": 5_420_000_000,
    }


@pytest.mark.req("MODEL-11")
def test_the_start_summary_says_the_caps_are_per_workspace_with_the_session_s_ceiling() -> None:
    """The product owner's ruling (31 October 2026): $5 per workspace. So the session's own
    ceiling is $5 for each workspace capped at start, and each workspace whose key is stored
    during the session adds $5."""
    capped = [
        SessionCap("w-1", "Ada's search", 420_000_000, 750_000_000, 5_420_000_000),
        SessionCap("w-2", "Second look", 0, 750_000_000, 5_000_000_000),
    ]

    assert session_summary("http://127.0.0.1:53000", capped).splitlines() == [
        "Careerwright: http://127.0.0.1:53000  (open this in a browser)",
        "Workspaces not marked synthetic run muse-wonder-1.0; synthetic ones keep the test model.",
        "The caps are per workspace: each run may reserve at most $0.750000, and each "
        "workspace may spend at most $5.000000 more this month.",
        "  Ada's search: $0.420000 committed this month, limit now $5.420000, each run at "
        "most $0.750000",
        "  Second look: $0.000000 committed this month, limit now $5.000000, each run at most "
        "$0.750000",
        "So this session can spend at most $10.000000 in all: $5.000000 for each of the 2 "
        "workspaces capped now. Each workspace whose key is stored during the session adds "
        "$5.000000.",
        "After the session, while the stack is still up (before `make stop`), run `make "
        "session-ledger`: it copies every model attempt in this stack's database into the "
        "cost ledger.",
    ]
    one = session_summary("http://127.0.0.1:53000", capped[:1]).splitlines()
    assert one[4] == (
        "So this session can spend at most $5.000000 in all: $5.000000 for the 1 workspace "
        "capped now. Each workspace whose key is stored during the session adds $5.000000."
    )
    none = session_summary("http://127.0.0.1:53000", []).splitlines()
    assert none[3:5] == [
        "  No live workspace yet: a new one gets these limits when its key is stored.",
        "So this session can spend at most $0.000000 in all: no workspace is capped yet. "
        "Each workspace whose key is stored during the session adds $5.000000.",
    ]


@pytest.mark.req("MODEL-11")
def test_the_api_s_default_limits_in_compose_are_config_s_unless_the_session_sets_them() -> None:
    compose = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")
    fields = ApiSettings.model_fields

    for variable, field in (
        ("CAREERWRIGHT_DEFAULT_RUN_SPEND_LIMIT_NANO_USD", "default_run_spend_limit_nano_usd"),
        ("CAREERWRIGHT_DEFAULT_PERIOD_SPEND_LIMIT_NANO_USD", "default_period_spend_limit_nano_usd"),
    ):
        found = re.search(rf"{variable}: \$\{{{variable}:-(\d+)\}}", compose)
        assert found is not None, variable
        assert int(found.group(1)) == fields[field].default


@pytest.mark.req("MODEL-08")
def test_each_estimated_kind_reserves_with_its_run_task_s_own_worst_case() -> None:
    for kind, attempt_worst_case in ESTIMATED_KINDS.items():
        assert attempt_worst_case is TASKS[kind].worst_case_nano_usd, kind


def attempt(**values: Any) -> dict[str, Any]:
    """A row as the copy's query returns it: exactly the columns it names."""
    base: dict[str, Any] = {
        "run_id": "6c2a0e4e-0000-4000-8000-000000000001",
        "attempt_id": 7,
        "model_id": WONDER_MODEL_ID,
        "kind": "interview_turn",
        "outcome": "succeeded",
        "spend_state": "reconciled",
        "reserved_nano_usd": 176_000_000,
        "cost_nano_usd": 14_832_000,
        "input_tokens": 1_033,
        "cached_input_tokens": 0,
        "output_tokens": 535,
        "reasoning_tokens": 295,
        "web_search_queries": 0,
        "requests_sent": 1,
        "started_at": datetime(2026, 11, 2, 10, 15, tzinfo=UTC),
    }
    assert set(base) == {column.split(".")[1] for column in COPIED_COLUMNS}
    return base | values


@pytest.mark.req("MODEL-11")
def test_a_copied_attempt_keeps_its_counts_and_an_unknown_cost_counts_its_reservation(
    tmp_path: Path,
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")

    known = ledger.append(session_entry(attempt()))
    unknown = ledger.append(
        session_entry(
            attempt(
                attempt_id=8,
                outcome="interrupted",
                spend_state="unknown",
                cost_nano_usd=None,
                input_tokens=None,
                cached_input_tokens=None,
                output_tokens=None,
                reasoning_tokens=None,
                web_search_queries=None,
                requests_sent=None,
            )
        )
    )

    # Labelled for what it copies: every attempt in the live stack's database, by date, made
    # under `make session` or `make dev` alike.
    assert known.budget_scope == unknown.budget_scope == "live-app-2026-11-02"
    assert known.purpose == (
        "live app: one interview turn attempt from the live stack's database (`make "
        "session-ledger` copies every attempt there, by its UTC date: model, kind, counts, "
        "cost and state only)"
    )
    assert (known.outcome, known.estimated_cost_nano_usd, known.input_tokens) == (
        CallOutcome.OK,
        14_832_000,
        1_033,
    )
    assert known.is_production_model
    assert (unknown.outcome, unknown.error_type) == (CallOutcome.FAILED, "interrupted")
    assert unknown.estimated_cost_nano_usd is None  # unknown, never zero
    assert unknown.http_requests == 2  # not recorded: every request it could send
    assert ledger.spent("live-app-2026-11-02").committed_nano_usd == 14_832_000 + 176_000_000
    assert json.loads(known.notes) == {
        "run_id": "6c2a0e4e-0000-4000-8000-000000000001",
        "attempt_id": 7,
        "started_at": "2026-11-02T10:15:00+00:00",
    }


@pytest.mark.req("MODEL-11")
def test_the_ledger_copy_names_no_text_column() -> None:
    """The query reads the attempt's identifiers, model, kind, counts, cost, reservation,
    state and time: none of the run records' text or sealed content
    (`tests/integration/test_live_session.py` runs it as a role granted only these)."""
    assert {column.split(".")[1] for column in COPIED_COLUMNS} == {
        "run_id",
        "attempt_id",
        "model_id",
        "kind",
        "outcome",
        "spend_state",
        "reserved_nano_usd",
        "cost_nano_usd",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_tokens",
        "web_search_queries",
        "requests_sent",
        "started_at",
    }


@pytest.mark.req("MODEL-11")
def test_the_session_commands_never_run_in_the_checks_or_the_acceptance_run() -> None:
    def recipe(target: str) -> str:
        return subprocess.run(  # noqa: S603 - fixed make dry run, nothing executes
            ["make", "-n", target],  # noqa: S607
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout

    assert "tools.session start" in recipe("session")
    assert "tools.session ledger" in recipe("session-ledger")
    for target in ("check", "acceptance"):
        assert "tools.session" not in recipe(target)
