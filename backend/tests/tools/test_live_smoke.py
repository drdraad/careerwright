"""The live smoke's caps refuse before any call, and every provider attempt is ledgered
(ruling R5). Offline: nothing here contacts Meta."""

import json
import subprocess
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, BuiltinToolCallsReturns, FunctionModel
from pydantic_ai.usage import RequestUsage

from careerwright.identity.model_choice import ModelChoice
from tests.support.fake_models import search_parts
from tools import live_smoke
from tools.live_smoke import (
    EXTRACT_BUDGET,
    INTERVIEW_TURN,
    MAX_CALLS,
    SEARCH_CITY,
    SEARCH_TARGET,
    WONDER_BUDGET,
    WONDER_MAX_COST_NANO_USD,
    WONDER_PAIR,
    CapExceededError,
    ScopeBudget,
    SmokeSettings,
    assert_attempt_bound,
    authorise,
    ledger_attempts,
    ledger_possible_calls,
    qualify_extraction,
    qualify_search_bound,
    qualify_wonder,
)
from tools.localenv import REPO_ROOT
from tools.usage_ledger import CallOutcome, Ledger, LedgerBusyError, LiveCallEntry, ScopeSpend

ROOMY = ScopeBudget("live-smoke", max_calls=99, max_production_calls=99, max_cost_nano_usd=10**12)
NOTHING_SPENT = ScopeSpend(0, 0, 0)


@pytest.mark.req("MODEL-09")
def test_the_test_model_fits_the_cap_and_is_not_a_production_call() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    model_id, worst_case = authorise(models, production=False, budget=ROOMY, spent=NOTHING_SPENT)

    assert model_id == "muse-spark-1.3-contributor"
    assert worst_case == MAX_CALLS * 809_600  # 4,000 in x $0.10/M + 2,048 out x $0.20/M


@pytest.mark.req("MODEL-09")
def test_an_interview_smoke_is_one_attempt_of_at_most_two_requests() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    test_model = authorise(
        models, production=False, budget=ROOMY, spent=NOTHING_SPENT, kind=INTERVIEW_TURN
    )
    production = authorise(
        models, production=True, budget=ROOMY, spent=NOTHING_SPENT, kind=INTERVIEW_TURN
    )

    assert INTERVIEW_TURN.calls() == 2
    assert test_model == ("muse-spark-1.3-contributor", 3_500_000)  # $0.0035 worst case
    assert production == ("muse-spark-1.3", 49_000_000)  # $0.049 worst case
    with pytest.raises(CapExceededError, match="2 more needed"):
        authorise(
            models,
            production=True,
            budget=ROOMY,
            spent=ScopeSpend(0, 98, 0),
            kind=INTERVIEW_TURN,
        )


@pytest.mark.req("MODEL-09")
def test_an_interview_attempt_is_ledgered_with_its_requests(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    attempts = [attempt(requests_sent=2), attempt(attempt_id=2, requests_sent=None)]

    ledger_attempts(
        ledger, attempts, scope="live-smoke", production_model="muse-spark-1.3", kind=INTERVIEW_TURN
    )

    # A request count that was not recorded counts every request the attempt could send.
    assert [r.http_requests for r in ledger.records()] == [2, 2]
    assert ledger.spent("live-smoke").calls == 4
    assert all(r.purpose == INTERVIEW_TURN.purpose for r in ledger.records())


@pytest.mark.req("MODEL-09")
def test_the_interview_smoke_workspace_allows_one_attempt_only() -> None:
    per_attempt = INTERVIEW_TURN.per_attempt_nano_usd("muse-spark-1.3-contributor")
    spend = {"run_limit_nano_usd": 2 * per_attempt, "period_limit_nano_usd": 2 * per_attempt}

    with pytest.raises(CapExceededError, match="allow 2 attempts, more than 1"):
        assert_attempt_bound(spend, per_attempt, INTERVIEW_TURN.attempts)


@pytest.mark.req("MODEL-09")
@pytest.mark.parametrize(("value", "interview"), [("1", True), ("0", False), ("", False)])
def test_only_interview_equals_one_runs_the_interview_smoke(value: str, interview: bool) -> None:
    dry_run = subprocess.run(  # noqa: S603 - fixed make dry run, nothing executes
        ["make", "-n", "live-smoke", f"INTERVIEW={value}"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

    assert ("--interview" in dry_run.stdout) is interview


@pytest.mark.req("MODEL-09")
def test_a_production_model_configured_as_the_test_model_needs_the_explicit_flag() -> None:
    models = ModelChoice.configure("muse-spark-1.3", "muse-spark-1.3", "test")

    with pytest.raises(CapExceededError, match="--production-model"):
        authorise(models, production=False, budget=ROOMY, spent=NOTHING_SPENT)
    assert authorise(models, production=True, budget=ROOMY, spent=NOTHING_SPENT)[0] == (
        "muse-spark-1.3"
    )


@pytest.mark.req("MODEL-09")
@pytest.mark.parametrize(
    ("value", "production"),
    [("1", True), ("0", False), ("false", False), ("yes", False), ("", False)],
)
def test_only_production_equals_one_opts_in_to_the_production_model(
    value: str, production: bool
) -> None:
    dry_run = subprocess.run(  # noqa: S603 - fixed make dry run, nothing executes
        ["make", "-n", "live-smoke", f"PRODUCTION={value}"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

    assert ("--production-model" in dry_run.stdout) is production


@pytest.mark.req("MODEL-09")
def test_a_model_whose_worst_case_breaks_the_cost_cap_is_refused() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-wonder-1.0", "test")

    with pytest.raises(CapExceededError, match="exceeds the cap"):
        authorise(models, production=True, budget=ROOMY, spent=NOTHING_SPENT)


@pytest.mark.req("MODEL-09")
@pytest.mark.parametrize(
    ("spent", "production", "refusal"),
    [
        (ScopeSpend(7, 0, 0), False, "of 9 calls used"),
        (ScopeSpend(1, 1, 0), True, "of 3 production calls used"),
        (ScopeSpend(1, 0, 298_000_000), False, "committed"),
    ],
)
def test_the_scope_s_cumulative_budget_refuses_once_the_next_invocation_would_breach_it(
    spent: ScopeSpend, production: bool, refusal: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key")
    budget = SmokeSettings(_env_file=None).budget()  # the conservative defaults
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    with pytest.raises(CapExceededError, match=refusal):
        authorise(models, production=production, budget=budget, spent=spent)
    assert authorise(models, production=production, budget=budget, spent=NOTHING_SPENT)


def attempt(**values: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "attempt_id": 1,
        "run_id": "run-1",
        "model_id": "muse-spark-1.3-contributor",
        "outcome": "succeeded",
        "spend_state": "reconciled",
        "reserved_nano_usd": 809_600,
        "cost_nano_usd": 40_000,
        "input_tokens": 150,
        "cached_input_tokens": 0,
        "output_tokens": 120,
        "reasoning_tokens": 80,
        "web_search_queries": 0,
        "provider_response_id": "resp_x",
    }
    return base | values


@pytest.mark.req("MODEL-09")
def test_every_attempt_that_reached_meta_is_ledgered_and_unknown_stays_unknown(
    tmp_path: Path,
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    attempts = [
        attempt(attempt_id=1, outcome="interrupted", spend_state="unknown", cost_nano_usd=None),
        attempt(attempt_id=2, outcome="credential_unavailable", spend_state="none"),
        attempt(attempt_id=3),
    ]

    seqs = ledger_attempts(ledger, attempts, scope="live-smoke", production_model="muse-spark-1.3")

    records = ledger.records()
    assert seqs == [1, 2]
    assert [r.outcome for r in records] == [CallOutcome.FAILED, CallOutcome.OK]
    assert records[0].estimated_cost_nano_usd is None  # unknown, never zero
    assert records[1].estimated_cost_nano_usd == 40_000
    assert not any(r.is_production_model for r in records)


@pytest.mark.req("MODEL-09")
def test_unreadable_attempts_are_ledgered_as_every_possible_call_with_unknown_cost(
    tmp_path: Path,
) -> None:
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-spark-1.3", "test")

    seqs = ledger_possible_calls(
        ledger, "muse-spark-1.3-contributor", 809_600, models, scope="live-smoke"
    )

    records = ledger.records()
    assert len(seqs) == MAX_CALLS
    assert all(r.estimated_cost_nano_usd is None for r in records)
    assert all(r.reserved_nano_usd == 809_600 for r in records)


@pytest.mark.req("MODEL-09")
def test_a_concurrent_smoke_refuses_before_its_stack_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """N6: the scope check and the final append happen under one lock, so two invocations
    cannot both pass the cap. The stack is the system edge: it must never start here."""

    def no_stack(**_: object) -> None:
        raise AssertionError("the smoke stack must not start")

    monkeypatch.setenv("META_API_KEY", "not-a-real-key")
    monkeypatch.setattr(live_smoke, "smoke_stack", no_stack)
    path = tmp_path / "live-usage.jsonl"

    with Ledger(path).exclusive(), pytest.raises(LedgerBusyError):
        live_smoke.run_smoke(SmokeSettings(_env_file=None), production=False, ledger=Ledger(path))


PER_ATTEMPT = 809_600  # the test model's per-attempt reservation


@pytest.mark.req("MODEL-09")
@pytest.mark.parametrize(
    ("run_limit", "period_limit", "allowed"),
    [
        (MAX_CALLS * PER_ATTEMPT, MAX_CALLS * PER_ATTEMPT, MAX_CALLS),
        (MAX_CALLS * PER_ATTEMPT, PER_ATTEMPT, 1),  # the tighter limit binds
        ((MAX_CALLS + 1) * PER_ATTEMPT - 1, MAX_CALLS * PER_ATTEMPT, MAX_CALLS),
    ],
)
def test_the_smoke_workspace_limits_allow_at_most_max_calls_attempts(
    run_limit: int, period_limit: int, allowed: int
) -> None:
    """M3: the ledger's fallback (every further possible call, up to MAX_CALLS) is only an
    upper bound if the product's reservations allow no more attempts than that."""
    spend = {"run_limit_nano_usd": run_limit, "period_limit_nano_usd": period_limit}

    assert assert_attempt_bound(spend, PER_ATTEMPT) == allowed


@pytest.mark.req("MODEL-09")
def test_limits_that_would_allow_a_fourth_attempt_stop_the_smoke_before_its_key_is_stored() -> None:
    spend = {
        "run_limit_nano_usd": (MAX_CALLS + 1) * PER_ATTEMPT,
        "period_limit_nano_usd": 10 * PER_ATTEMPT,
    }

    with pytest.raises(CapExceededError, match="allow 4 attempts"):
        assert_attempt_bound(spend, PER_ATTEMPT)


def _search_meta(searches: int) -> Callable[[str, SecretStr], FunctionModel]:
    """Meta's place, offline: a search reply reporting `searches` searches."""

    def build(model_id: str, api_key: SecretStr) -> FunctionModel:
        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            asked: dict[str, object] = {"role": SEARCH_TARGET, "city": SEARCH_CITY}
            usage = RequestUsage(
                input_tokens=9_000, output_tokens=200, details={"web_search_requests": searches}
            )
            return ModelResponse(parts=search_parts(asked, ""), usage=usage)

        return FunctionModel(respond)

    return build


@pytest.mark.req("MODEL-09", "MODEL-08")
@pytest.mark.parametrize(
    ("searches", "outcome", "error"),
    [(1, CallOutcome.OK, None), (2, CallOutcome.FAILED, "bound_exceeded:web_searches")],
    ids=["Meta keeps to one search", "Meta runs a second"],
)
def test_the_search_bound_qualification_asks_for_one_search_and_ledgers_what_meta_did(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    searches: int,
    outcome: CallOutcome,
    error: str | None,
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key")
    ledger = Ledger(tmp_path / "live-usage.jsonl")

    code = qualify_search_bound(SmokeSettings(_env_file=None), ledger, build=_search_meta(searches))

    [row] = ledger.records()
    assert code == (0 if outcome is CallOutcome.OK else 1)
    assert (row.budget_scope, row.outcome, row.error_type) == ("live-search", outcome, error)
    assert (row.http_requests, row.web_search_queries) == (1, searches)
    assert row.estimated_cost_nano_usd is not None  # booked at its cost either way
    notes = json.loads(row.notes)
    assert notes["max_tool_calls"] == 1
    if outcome is CallOutcome.OK:  # hosts only, never a URL
        assert notes["source_hosts"] == ["careers.northwind.example"]
        assert notes["excluded"] == [{"reason": "source_not_permitted", "host": "www.linkedin.com"}]
        assert "https://" not in row.notes


EXTRACTED = {
    "postings": [
        {
            "title": "Data Quality Analyst",
            "employer": "Northwind Analytics Ltd",
            "location": "Manchester",
            "work_mode": None,
            "salary": "£32,000 to £36,000 per year",
            "employment_type": None,
            "date_posted": None,
            "valid_through": "30 November 2026",
            "apply_url": None,
        }
    ]
}


def _extraction_meta(*replies: str, sent: list[str]) -> Callable[[str, SecretStr], FunctionModel]:
    """Meta's place, offline: each request gets the next reply, with its own usage."""

    def build(model_id: str, api_key: SecretStr) -> FunctionModel:
        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            sent.append(str(messages[0].parts[-1].content))  # type: ignore[union-attr]
            n = len(sent)
            usage = RequestUsage(input_tokens=1_000 * n, output_tokens=100 * n)
            return ModelResponse(parts=[TextPart(replies[n - 1])], usage=usage)

        return FunctionModel(respond)

    return build


@pytest.mark.req("MODEL-11")
@pytest.mark.parametrize("target", ["live-smoke", "live-eval"])
@pytest.mark.parametrize(("value", "wonder"), [("1", True), ("0", False), ("yes", False)])
def test_only_wonder_equals_one_puts_muse_wonder_in_a_live_command(
    target: str, value: str, wonder: bool
) -> None:
    dry_run = subprocess.run(  # noqa: S603 - fixed make dry run, nothing executes
        ["make", "-n", target, f"WONDER={value}"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

    assert ("--wonder" in dry_run.stdout) is wonder


@pytest.mark.req("MODEL-11")
def test_the_wonder_pair_has_its_own_cap_and_shared_scope() -> None:
    models = ModelChoice.configure("muse-spark-1.3-contributor", "muse-wonder-1.0", "production")
    pair = {"budget": WONDER_BUDGET, "kind": WONDER_PAIR}

    model_id, worst_case = authorise(
        models,
        production=True,
        spent=NOTHING_SPENT,
        max_cost_nano_usd=WONDER_MAX_COST_NANO_USD,
        **pair,  # type: ignore[arg-type]
    )

    # $0.05696 for the schema call (4,000 in x $4/M + 2,048 out x $20/M) and $0.0925 for the
    # streamed search with one tool call (15,000 in x $4/M + 1,500 out x $20/M + $0.0025).
    assert (model_id, worst_case) == ("muse-wonder-1.0", 56_960_000 + 92_500_000)
    assert WONDER_PAIR.calls() == 2
    assert (WONDER_BUDGET.scope, WONDER_BUDGET.max_cost_nano_usd) == (
        "wonder-qualification",
        5_000_000_000,
    )
    with pytest.raises(CapExceededError, match="exceeds the cap"):  # Spark's cap refuses it
        authorise(models, production=True, spent=NOTHING_SPENT, **pair)  # type: ignore[arg-type]
    with pytest.raises(CapExceededError, match="committed"):
        authorise(
            models,
            production=True,
            spent=ScopeSpend(2, 2, 5_000_000_000 - worst_case + 1),
            max_cost_nano_usd=WONDER_MAX_COST_NANO_USD,
            **pair,  # type: ignore[arg-type]
        )


def _wonder_meta(built: list[str], *, piece: int = 40) -> Callable[[str, SecretStr], Model]:
    """Meta's place, offline: the schema call answers whole; the search streams its tool
    parts, then its JSON in pieces of `piece` characters."""
    asked: dict[str, object] = {"role": SEARCH_TARGET, "city": SEARCH_CITY}
    call, returned, text = search_parts(asked, "")

    def build(model_id: str, api_key: SecretStr) -> FunctionModel:
        built.append(model_id)

        def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            answer = {"suggested_title": "Training coordinator", "reason": "Synthetic."}
            usage = RequestUsage(input_tokens=150, output_tokens=60)
            return ModelResponse(parts=[TextPart(json.dumps(answer))], usage=usage)

        async def stream(
            messages: list[ModelMessage], info: AgentInfo
        ) -> AsyncIterator[str | BuiltinToolCallsReturns]:
            yield {0: call, 1: returned}
            for start in range(0, len(text.content), piece):
                yield text.content[start : start + piece]

        return FunctionModel(respond, stream_function=stream)

    return build


@pytest.mark.req("MODEL-11", "MODEL-09")
def test_the_wonder_qualification_makes_both_calls_on_wonder_streams_the_search_and_ledgers_each(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key-for-this-test")
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    built: list[str] = []

    code = qualify_wonder(SmokeSettings(_env_file=None), ledger, build=_wonder_meta(built))

    assert code == 0
    # Wonder whatever is configured (the default production model is Spark).
    assert built == ["muse-wonder-1.0", "muse-wonder-1.0"]
    schema, streamed = ledger.records()
    assert {
        (r.budget_scope, r.model_id, r.is_production_model, r.http_requests)
        for r in (
            schema,
            streamed,
        )
    } == {("wonder-qualification", "muse-wonder-1.0", True, 1)}
    assert (schema.outcome, streamed.outcome) == (CallOutcome.OK, CallOutcome.OK)
    assert schema.estimated_cost_nano_usd == 150 * 4_000 + 60 * 20_000
    assert schema.reserved_nano_usd == 56_960_000
    assert streamed.reserved_nano_usd == 92_500_000
    notes = json.loads(streamed.notes)
    assert notes["streamed_deltas"] >= 2  # the JSON arrived in pieces: the request streamed
    assert (notes["max_tool_calls"], notes["searches"]) == (1, 1)
    assert "https://" not in streamed.notes  # hosts only, never a URL


@pytest.mark.req("MODEL-11")
def test_a_search_answered_in_one_piece_does_not_establish_streaming(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key-for-this-test")
    ledger = Ledger(tmp_path / "live-usage.jsonl")

    code = qualify_wonder(
        SmokeSettings(_env_file=None), ledger, build=_wonder_meta([], piece=10**6)
    )

    _, streamed = ledger.records()
    assert code == 1  # the call is booked at its cost, but streaming was not shown
    assert streamed.outcome is CallOutcome.OK
    assert json.loads(streamed.notes)["streamed_deltas"] < 2


@pytest.mark.req("MODEL-11")
def test_the_wonder_qualification_refuses_before_any_request_once_its_scope_is_spent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key-for-this-test")
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    ledger.append(
        LiveCallEntry(
            budget_scope="wonder-qualification",
            purpose="an earlier call whose cost Meta never reported",
            model_id="muse-wonder-1.0",
            is_production_model=True,
            endpoint="POST /v1/responses",
            outcome=CallOutcome.FAILED,
            reserved_nano_usd=5_000_000_000 - 149_460_000 + 1,
        )
    )
    built: list[str] = []

    with pytest.raises(
        CapExceededError, match=r"wonder-qualification: .* of \$5\.000000 committed"
    ):
        qualify_wonder(SmokeSettings(_env_file=None), ledger, build=_wonder_meta(built))
    assert built == []
    assert len(ledger.records()) == 1


@pytest.mark.req("MODEL-09", "ACQ-03")
def test_the_extraction_qualification_reads_the_fixture_page_and_ledgers_each_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key-for-this-test")
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    sent: list[str] = []
    build = _extraction_meta('{"postings": "none"}', json.dumps(EXTRACTED), sent=sent)

    code = qualify_extraction(SmokeSettings(_env_file=None), ledger, build=build)

    assert code == 0
    assert "Synthetic test page: not a real advert" in sent[0]  # the fixture page only
    first, second = ledger.records()  # the call and its schema repair, each its own row
    assert {(r.budget_scope, r.model_id, r.http_requests) for r in (first, second)} == {
        ("live-extract", "muse-spark-1.3-contributor", 1)
    }
    assert (
        (first.input_tokens, first.output_tokens),
        (second.input_tokens, second.output_tokens),
    ) == (
        (1_000, 100),
        (2_000, 200),
    )
    assert first.estimated_cost_nano_usd == 1_000 * 100 + 100 * 200
    assert first.notes == ""
    notes = json.loads(second.notes)
    assert (notes["postings"], notes["claims"]["model"], notes["followed_page_instruction"]) == (
        1,
        5,
        False,
    )
    assert notes["page"] == "fixtures/acquisition/extraction-page.html"


@pytest.mark.req("MODEL-09")
def test_the_extraction_scope_refuses_a_run_its_three_requests_cannot_cover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_API_KEY", "not-a-real-key-for-this-test")
    ledger = Ledger(tmp_path / "live-usage.jsonl")
    sent: list[str] = []
    build = _extraction_meta('{"postings": "none"}', json.dumps(EXTRACTED), sent=sent)
    assert qualify_extraction(SmokeSettings(_env_file=None), ledger, build=build) == 0

    with pytest.raises(CapExceededError, match="live-extract: 2 of 3 calls used, 2 more needed"):
        qualify_extraction(SmokeSettings(_env_file=None), ledger, build=build)
    assert len(sent) == 2  # refused before any request
    assert (EXTRACT_BUDGET.max_calls, EXTRACT_BUDGET.max_production_calls) == (3, 0)
    assert EXTRACT_BUDGET.max_cost_nano_usd == 300_000_000
