"""`make live-smoke`: one real run through the whole product, budget-capped: a connection
check, or with `--interview` (`INTERVIEW=1`) one interview turn whose proposals are then
confirmed into the profile, proving the InterviewTurn schema round-trips.

Ruling R5. The key is read from the repository's gitignored `.env` into a `SecretStr`; it
is never a command argument and never printed. An isolated stack (its own Compose project,
ports, NESSA_HOME and volumes, removed afterwards) runs in live mode. The key travels the
product path: stored through the API with consent, sealed at once, opened only inside the
worker's bounded activity, which makes the call. Afterwards the worker is stopped, so no
further call can start, and then every attempt of the smoke workspace is appended to
`docs/evidence/live-usage.jsonl` (and the Markdown table) with its cost and its number of
provider requests, even if the run failed; if the worker cannot be confirmed stopped, every
further call its spend limits allow is ledgered too, with an unknown cost. Then both
databases, every container log and the API's own responses are scanned for the key.

Caps, checked before anything starts:
- per invocation: the kind's attempts (the connection check's retry budget; one interview
  attempt, of at most two requests: the call and one validation repair), enforced by the
  workspace's run spend limit, so the product's own reservation refuses any further
  attempt; none on the production model unless `--production-model` (`PRODUCTION=1`); and a
  worst-case cost cap;
- per budget scope, cumulative over the ledger: provider requests, production requests and
  worst-case cost (`ScopeBudget`; conservative defaults, configurable through
  `NESSA_LIVE_SMOKE_*`), checked and spent under an exclusive lock on the ledger, so a
  concurrent invocation refuses.
The test model is a Contributor model, so the workspace is synthetic, and the interview
message is a fixed synthetic persona.

`--search` runs one source search through the stack, in its own scope (`live-search`), and
its ledger row's notes record what it proposed, excluded (with reasons) and which hosts its
pages came from (hosts only). `--search-bound` asks one search, in this process, through
the product's task code, for `max_tool_calls` 1, and ledgers whether Meta kept to it (fix
round 1, review B I4). `--extract` (`make live-extract`) reads the synthetic fixture page
(`fixtures/acquisition/extraction-page.html`, never a real page) with one page extraction,
in this process, through the product's task code and check, in its own scope
(`live-extract`: at most 3 requests and $0.30), ledgering each request with its own tokens
and cost, then scans the result, the rows and the requests sent for the key (fix round 2).

Run from `backend/`: `uv run --locked python -m tools.live_smoke [--production-model]
[--interview | --search | --search-bound | --extract]`.
"""

import argparse
import json
import shutil
import sys
import tempfile
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx2
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import Field, SecretStr
from pydantic_ai import capture_run_messages
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
)
from pydantic_ai.models import Model
from pydantic_settings import BaseSettings, SettingsConfigDict

from nessa.evidence import extraction, search
from nessa.evidence.extraction import ExtractionInput, ExtractionProposal
from nessa.evidence.extraction_agent import run_extraction
from nessa.evidence.pages import redact_page, visible_text
from nessa.evidence.records import ValidationState
from nessa.evidence.search_agent import run_search
from nessa.identity import connection_check
from nessa.identity.activity import (
    ACTIVITY_MAX_ATTEMPTS,
    STORE_RETRY_BUDGET_S,
    PartialWriter,
    measured_usage,
)
from nessa.identity.failures import BoundExceededError, classify_failure
from nessa.identity.meta import REQUEST_TIMEOUT_S, meta_model
from nessa.identity.model_choice import ModelChoice
from nessa.identity.model_registry import ModelMode, estimate_cost_nano_usd, format_usd
from nessa.identity.workflow import ACTIVITY_BACKOFF_RATE, ACTIVITY_INTERVAL_S
from nessa.profile import interview
from tools.leak_scan import Finding, Needle, scan
from tools.localenv import REPO_ROOT, ensure_local_home
from tools.stack import CORE_SERVICES, Ports, Stack
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry, ScopeSpend

MAX_CALLS = ACTIVITY_MAX_ATTEMPTS  # the connection check's attempts
MAX_COST_NANO_USD = 100_000_000  # $0.10 worst case per invocation
SMOKE_PORTS = Ports(api=57800, auth=57899, postgres=57832, web=57900)
RESPONSES_ENDPOINT = "POST /v1/responses"
PURPOSE = "connection check via API, outbox and DBOS worker (key opened just in time)"
INTERVIEW_PURPOSE = (
    "interview turn via API, outbox and DBOS worker; proposals confirmed into the profile "
    "(synthetic message; key opened just in time)"
)
# A fixed synthetic persona (ADR 0003: the test model takes synthetic inputs only).
SYNTHETIC_MESSAGE = (
    "Synthetic test persona, not a real person: I'm a warehouse shift supervisor and I "
    "could work in Leeds or York. I could give about 6 hours a week to learning and spend "
    "up to £1,200 in total. I enjoy training new starters."
)


@dataclass(frozen=True)
class SmokeKind:
    """What one invocation runs, and its bounds."""

    name: str
    attempts: int  # attempts the workspace's run limit allows
    requests_per_attempt: int  # provider requests one attempt may send
    per_attempt_nano_usd: Callable[[str], int]
    purpose: str

    def calls(self) -> int:
        return self.attempts * self.requests_per_attempt

    def run_timeout_s(self) -> float:
        """Its worst case, where every request times out and both store transactions of
        every attempt (prepare, settle) spend the whole store budget, with the step's
        backoff between attempts, plus a minute for the stack. Ledger completeness does not
        depend on it: the worker is stopped before the attempts are read."""
        return (
            self.attempts
            * (self.requests_per_attempt * REQUEST_TIMEOUT_S + 2 * STORE_RETRY_BUDGET_S)
            + sum(ACTIVITY_INTERVAL_S * ACTIVITY_BACKOFF_RATE**i for i in range(self.attempts - 1))
            + 60.0
        )


CONNECTION_CHECK = SmokeKind(
    "connection_check", MAX_CALLS, 1, connection_check.worst_case_nano_usd, PURPOSE
)
INTERVIEW_TURN = SmokeKind(
    "interview_turn",
    1,  # a transient failure is then refused by the budget, never retried at cost
    interview.MAX_REQUESTS,
    interview.worst_case_nano_usd,
    INTERVIEW_PURPOSE,
)
SOURCE_SEARCH = SmokeKind(
    "source_search",
    1,  # one attempt: the budget refuses a retry, which would pay for every search again
    search.MAX_REQUESTS,
    search.worst_case_nano_usd,
    "source search via API, outbox and DBOS worker: Meta web search for a synthetic target "
    "and city, candidates checked (key opened just in time)",
)
# Fix round 1 (review B I4): whether Meta keeps to `max_tool_calls`, asked for one search.
BOUND_TOOL_CALLS = 1
SEARCH_BOUND = SmokeKind(
    "source_search_bound",
    1,
    search.MAX_REQUESTS,
    lambda model_id: search.worst_case_nano_usd(model_id, max_tool_calls=BOUND_TOOL_CALLS),
    "source search in process with max_tool_calls 1, to qualify that Meta keeps to the bound "
    "(synthetic target and city; the product's own task code and bound check)",
)
# The search kind's own budget scope (Task 7A): at most 9 requests and $0.30, test model.
SEARCH_SCOPE = "live-search"
SEARCH_TARGET, SEARCH_CITY = "Data analyst", "Manchester"
RUN_TIMEOUT_S = CONNECTION_CHECK.run_timeout_s()


class SmokeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    api_key: SecretStr = Field(validation_alias="META_API_KEY")
    meta_test_model: str = Field(
        default="muse-spark-1.3-contributor", validation_alias="NESSA_META_TEST_MODEL"
    )
    meta_production_model: str = Field(
        default="muse-spark-1.3", validation_alias="NESSA_META_PRODUCTION_MODEL"
    )
    # The cumulative budget scope (ruling R5). Defaults: three smoke invocations, one of them
    # on the production model, and $0.30 worst case in all.
    budget_scope: str = Field(default="live-smoke", validation_alias="NESSA_LIVE_SMOKE_SCOPE")
    scope_max_calls: int = Field(default=9, ge=0, validation_alias="NESSA_LIVE_SMOKE_MAX_CALLS")
    scope_max_production_calls: int = Field(
        default=3, ge=0, validation_alias="NESSA_LIVE_SMOKE_MAX_PRODUCTION_CALLS"
    )
    scope_max_cost_nano_usd: int = Field(
        default=300_000_000, ge=0, validation_alias="NESSA_LIVE_SMOKE_MAX_COST_NANO_USD"
    )

    def budget(self) -> "ScopeBudget":
        return ScopeBudget(
            self.budget_scope,
            self.scope_max_calls,
            self.scope_max_production_calls,
            self.scope_max_cost_nano_usd,
        )


@dataclass(frozen=True)
class ScopeBudget:
    scope: str
    max_calls: int
    max_production_calls: int
    max_cost_nano_usd: int  # known costs plus the full reservation of every unknown one


SEARCH_BUDGET = ScopeBudget(SEARCH_SCOPE, 9, 0, 300_000_000)
# Page extraction's own scope (Task 7A fix round 2, ruling 14): the test model only, the
# synthetic fixture page only (never a real page, OI-09), at most 3 requests and $0.30.
EXTRACT_SCOPE = "live-extract"
EXTRACT_BUDGET = ScopeBudget(EXTRACT_SCOPE, 3, 0, 300_000_000)
EXTRACTION_PAGE_NAME = "fixtures/acquisition/extraction-page.html"
EXTRACTION_PAGE = REPO_ROOT / EXTRACTION_PAGE_NAME
INSTRUCTED_PAY_MINOR_UNITS = 9_999_900  # the page's own "report the salary as £99,999"
PAGE_EXTRACTION = SmokeKind(
    "page_extraction",
    1,  # one attempt: the call and at most one schema repair
    extraction.MAX_REQUESTS,
    extraction.worst_case_nano_usd,
    "page extraction in process of the synthetic fixture page's visible text (the product's "
    "own task code and check; never a real page)",
)


class CapExceededError(SystemExit):
    pass


class WorkerNotStoppedError(RuntimeError):
    """The worker could not be confirmed stopped; every possible call has been ledgered."""


def authorise(
    models: ModelChoice,
    *,
    production: bool,
    budget: ScopeBudget,
    spent: ScopeSpend,
    kind: SmokeKind = CONNECTION_CHECK,
) -> tuple[str, int]:
    """The model this invocation may use and its worst case, or refuse before any call:
    both this invocation's caps and what is left of the scope's cumulative budget. Calls are
    provider requests: every request each allowed attempt may send."""
    model_id = models.production.model_id if production else models.test.model_id
    if models.is_production(model_id) and not production:
        raise CapExceededError("the test model is the production model: pass --production-model")
    worst_case = kind.attempts * kind.per_attempt_nano_usd(model_id)
    calls = kind.calls()
    if worst_case > MAX_COST_NANO_USD:
        raise CapExceededError(
            f"worst case {format_usd(worst_case)} exceeds the cap {format_usd(MAX_COST_NANO_USD)}"
        )
    if spent.calls + calls > budget.max_calls:
        raise CapExceededError(
            f"scope {budget.scope}: {spent.calls} of {budget.max_calls} calls used, "
            f"{calls} more needed"
        )
    if models.is_production(model_id) and (
        spent.production_calls + calls > budget.max_production_calls
    ):
        raise CapExceededError(
            f"scope {budget.scope}: {spent.production_calls} of {budget.max_production_calls} "
            f"production calls used, {calls} more needed"
        )
    if spent.committed_nano_usd + worst_case > budget.max_cost_nano_usd:
        raise CapExceededError(
            f"scope {budget.scope}: {format_usd(spent.committed_nano_usd)} of "
            f"{format_usd(budget.max_cost_nano_usd)} committed, worst case "
            f"{format_usd(worst_case)} more"
        )
    return model_id, worst_case


class SmokeTarget(Protocol):
    """A running Nessa the smoke drives: the isolated Compose stack (`StackTarget`), or in
    tests the integration stack with a fake-model worker."""

    @property
    def http(self) -> httpx2.Client: ...  # base URL: the API

    @property
    def web_origin(self) -> str: ...

    def sign_in(self) -> str: ...

    def superuser_url(self, database: str) -> str: ...

    def stop_worker(self) -> None: ...  # no model call can start after this returns

    def logs(self) -> str: ...


class Api:
    def __init__(self, target: SmokeTarget, token: str) -> None:
        self._target = target
        self._token = token
        self.responses: list[tuple[str, str]] = []

    def call(self, method: str, path: str, body: object = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._token}"}
        if method != "GET":
            headers |= {"Origin": self._target.web_origin, "Idempotency-Key": str(uuid.uuid4())}
        response = self._target.http.request(method, path, json=body, headers=headers)
        self.responses.append((f"{method} {path} -> {response.status_code}", response.text))
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed: {response.json()['error']['code']}")
        result: dict[str, Any] = response.json()
        return result


def _workspace_attempts(target: SmokeTarget, workspace_id: str) -> list[dict[str, Any]]:
    """Every attempt of the smoke workspace, whichever run made it, so no call escapes the
    ledger even if the client never learned its run ID."""
    with psycopg.connect(target.superuser_url("nessa_app"), row_factory=dict_row) as conn:
        return conn.execute(
            "SELECT * FROM nessa.model_attempts WHERE workspace_id = %s ORDER BY attempt_id",
            (workspace_id,),
        ).fetchall()


def ledger_attempts(
    ledger: Ledger,
    attempts: list[dict[str, Any]],
    *,
    scope: str,
    production_model: str,
    kind: SmokeKind = CONNECTION_CHECK,
    found: Mapping[str, object] | None = None,
) -> list[int]:
    """One ledger row per attempt that reached the provider (a reservation was taken), with
    the requests it sent; an attempt whose request count was not recorded counts every
    request it could send."""
    seqs = []
    for attempt in attempts:
        if attempt["spend_state"] == "none":
            continue  # refused before any call: nothing was sent to Meta
        outcome = attempt["outcome"] or "unfinished"
        requests = attempt.get("requests_sent") or kind.requests_per_attempt
        record = ledger.append(
            LiveCallEntry(
                budget_scope=scope,
                purpose=kind.purpose,
                http_requests=requests,
                model_id=attempt["model_id"],
                is_production_model=attempt["model_id"] == production_model,
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.OK if outcome == "succeeded" else CallOutcome.FAILED,
                reserved_nano_usd=attempt["reserved_nano_usd"],
                estimated_cost_nano_usd=attempt["cost_nano_usd"],
                error_type=None if outcome == "succeeded" else outcome,
                input_tokens=attempt["input_tokens"],
                cached_input_tokens=attempt["cached_input_tokens"],
                output_tokens=attempt["output_tokens"],
                reasoning_tokens=attempt["reasoning_tokens"],
                web_search_queries=attempt["web_search_queries"],
                provider_response_id=attempt["provider_response_id"],
                notes=json.dumps(
                    {
                        "run_id": str(attempt["run_id"]),
                        "attempt_id": attempt["attempt_id"],
                        **(found or {}),
                    }
                ),
            )
        )
        seqs.append(record.seq)
    return seqs


def ledger_possible_calls(
    ledger: Ledger,
    model_id: str,
    reserved_nano_usd: int,
    models: ModelChoice,
    *,
    scope: str,
    count: int = MAX_CALLS,
    reason: str = "attempts unreadable",
    kind: SmokeKind = CONNECTION_CHECK,
) -> list[int]:
    """Attempts that may have reached Meta but cannot be read back: record each one, with
    an unknown cost and every request it could send, rather than nothing."""
    return [
        ledger.append(
            LiveCallEntry(
                budget_scope=scope,
                purpose=f"{kind.purpose} (possible call; {reason})",
                http_requests=kind.requests_per_attempt,
                model_id=model_id,
                is_production_model=models.is_production(model_id),
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.FAILED,
                reserved_nano_usd=reserved_nano_usd,
                error_type="attempts_unreadable",
            )
        ).seq
        for _ in range(count)
    ]


def assert_attempt_bound(
    spend: Mapping[str, Any], per_attempt_nano_usd: int, max_attempts: int = MAX_CALLS
) -> int:
    """How many attempts the smoke workspace's stored limits allow, refusing more than
    `max_attempts`. Each attempt reserves `per_attempt_nano_usd` and keeps it unless it
    reports usage, which only a run's final attempt does (success or a terminal failure);
    so this count bounds the calls the ledger's possible-call fallback has to cover."""
    tighter = min(int(spend["run_limit_nano_usd"]), int(spend["period_limit_nano_usd"]))
    allowed = tighter // per_attempt_nano_usd
    if allowed > max_attempts:
        raise CapExceededError(
            f"the smoke workspace's limits allow {allowed} attempts, more than {max_attempts}"
        )
    return allowed


def ledger_workspace_calls(
    ledger: Ledger,
    target: SmokeTarget,
    workspace_id: str,
    *,
    model_id: str,
    models: ModelChoice,
    scope: str,
    worker_stopped: bool,
    kind: SmokeKind = CONNECTION_CHECK,
    found: Mapping[str, object] | None = None,
) -> list[int]:
    """Every attempt the smoke workspace recorded. If the worker may still be running, also
    every further attempt its spend limits allow (the kind's attempts in all,
    `assert_attempt_bound`), as possible calls at the product's own per-attempt reservation.
    `found`: what the run reported (a search's exclusions and source hosts), for the notes."""
    per_attempt = kind.per_attempt_nano_usd(model_id)
    try:
        attempts = _workspace_attempts(target, workspace_id)
    except psycopg.Error:
        return ledger_possible_calls(
            ledger, model_id, per_attempt, models, scope=scope, count=kind.attempts, kind=kind
        )
    seqs = ledger_attempts(
        ledger,
        attempts,
        scope=scope,
        production_model=models.production.model_id,
        kind=kind,
        found=found,
    )
    if not worker_stopped:
        seqs += ledger_possible_calls(
            ledger,
            model_id,
            per_attempt,
            models,
            scope=scope,
            count=max(0, kind.attempts - len(seqs)),
            reason="worker not confirmed stopped",
            kind=kind,
        )
    return seqs


def leak_findings(target: SmokeTarget, api: Api, key: SecretStr) -> tuple[int, list[Finding]]:
    cells: list[tuple[str, str]] = list(api.responses)
    for database in ("nessa_app", "nessa_dbos"):
        with psycopg.connect(target.superuser_url(database), row_factory=dict_row) as conn:
            tables = conn.execute(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' "
                "AND table_schema NOT IN ('pg_catalog', 'information_schema')"
            ).fetchall()
            for table in tables:
                rows = conn.execute(
                    sql.SQL("SELECT row_to_json(t)::text AS row FROM {}.{} t").format(
                        sql.Identifier(table["table_schema"]), sql.Identifier(table["table_name"])
                    )
                ).fetchall()
                name = f"{database}:{table['table_schema']}.{table['table_name']}"
                cells += [(name, str(row["row"])) for row in rows]
    cells.append(("container logs", target.logs()))
    needles = [Needle("Meta key", key.get_secret_value(), fragment_length=12)]
    return len(cells), scan(cells, needles)


@dataclass(frozen=True)
class SmokeResult:
    status: str  # the run's final status, or why there is none
    findings: list[Finding]
    ledger_seqs: list[int]


def _wait(
    api: Api, path: str, run_of: Callable[[dict[str, Any]], dict[str, Any]], timeout_s: float
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    body = api.call("GET", path)
    while run_of(body)["status"] in ("queued", "running") and time.monotonic() < deadline:
        time.sleep(1)
        body = api.call("GET", path)
    return body


def _connection_check(api: Api, base: str, model_id: str, timeout_s: float) -> str:
    submitted = api.call("POST", f"{base}/runs", {"kind": "connection_check"})
    if submitted["model_id"] != model_id:  # the bound above priced this model's attempts
        raise RuntimeError(f"the run uses {submitted['model_id']}, not {model_id}")
    run = _wait(api, f"{base}/runs/{submitted['run_id']}", lambda body: body, timeout_s)
    print(f"run {run['run_id']}: {run['status']} {run['failure_class'] or ''}".rstrip(), flush=True)
    if run["output"]:
        print(f"validated output: {run['output']}", flush=True)
    return str(run["status"])


def _interview_turn(api: Api, base: str, model_id: str, timeout_s: float) -> str:
    """One turn with the synthetic message, whose reply must have streamed; then every
    proposal is accepted (limits and targets confirmed explicitly) through the decision
    command, so the schema round-trips from model output to a new profile version."""
    submitted = api.call(
        "POST",
        f"{base}/interview/turns",
        {"expected_profile_version": 0, "message": SYNTHETIC_MESSAGE},
    )
    if submitted["run"]["model_id"] != model_id:
        raise RuntimeError(f"the run uses {submitted['run']['model_id']}, not {model_id}")
    path = f"{base}/interview/turns/{submitted['turn_id']}"
    turn = _wait(api, path, lambda body: body["run"], timeout_s)
    run = turn["run"]
    print(f"turn {turn['turn_id']}: {run['status']} {run['failure_class'] or ''}".rstrip())
    proposal = turn["proposal"]
    if run["status"] != "complete" or proposal is None:
        return str(run["status"])
    # The reply streamed (announced by events with IDs only), and the validated output has
    # superseded it.
    streamed = [
        event
        for event in api.call("GET", f"{base}/events")["items"]
        if event["kind"] == "run.partial_updated" and event["subject_id"] == turn["turn_id"]
    ]
    reply = api.call("GET", f"{path}/reply")
    print(f"streamed reply: {reply['completeness']} after {len(streamed)} writes", flush=True)
    if not streamed or reply["completeness"] != "superseded":
        return "complete without a streamed reply"
    changes = proposal["changes"]
    print(f"validated proposal: {json.dumps(changes, ensure_ascii=False)}", flush=True)
    if not changes or any(c["message_ids"] != [turn["message_id"]] for c in changes):
        return "complete without proposals citing the message"
    decided = api.call(
        "POST",
        f"{path}/decision",
        {
            "expected_version": 0,
            "accept": [c["change_id"] for c in changes],
            "confirm_hard_constraints": [c["field"] for c in changes if c["hard_constraint"]],
        },
    )
    document = decided["profile"]["document"]
    saved = {c["field"]: document[c["field"]]["value"] for c in changes}
    print(f"profile version {decided['profile']['version']}: {saved}", flush=True)
    return "complete" if decided["profile"]["version"] == 1 else "decision changed nothing"


def search_notes(proposal: Mapping[str, Any]) -> dict[str, object]:
    """What a search's ledger row records of it: counts, its exclusions with their reasons,
    the hosts its pages came from (hosts only, never a URL) and why it proposed nothing."""
    return {
        "prompt_version": search.PROMPT_VERSION,
        "candidates": len(proposal["candidates"]),
        "grounded": sum(1 for c in proposal["candidates"] if c["grounded"]),
        "excluded": [
            {"reason": e["reason"], "host": e.get("refused_host") or _host_of(e.get("url"))}
            for e in proposal["excluded"]
        ],
        "sources_seen": proposal["sources_seen"],
        "source_hosts": proposal.get("source_hosts", []),
        "searches": len(proposal["queries"]),
        "empty_reason": proposal.get("empty_reason"),
    }


def _host_of(url: object) -> str | None:
    return urlsplit(url).hostname if isinstance(url, str) else None


def _source_search(
    api: Api,
    base: str,
    model_id: str,
    timeout_s: float,
    found: dict[str, object] | None = None,
) -> str:
    """A synthetic target and city confirmed by direct entry, then one source search; its
    candidates, grounding and the searches it ran are printed (no page is fetched), and put
    in `found` for the ledger row."""
    fields = (
        "preferred_name",
        "current_role",
        "cities",
        "target_titles",
        "weekly_study_hours",
        "direct_spend_cap",
        "monthly_payment_cap",
        "enjoyed_tasks",
        "confident_tasks",
        "evidenced_tasks",
        "work_style",
        "minimum_salary",
    )
    profile: dict[str, Any] = {name: {"state": "unasked"} for name in fields}
    profile["cities"] = {"state": "provided", "value": [SEARCH_CITY]}
    profile["target_titles"] = {"state": "provided", "value": [SEARCH_TARGET]}
    saved = api.call("PUT", f"{base}/profile", {"expected_version": 0, "profile": profile})
    submitted = api.call(
        "POST",
        f"{base}/research/searches",
        {
            "expected_profile_version": saved["version"],
            "target": SEARCH_TARGET,
            "city": SEARCH_CITY,
        },
    )
    if submitted["run"]["model_id"] != model_id:
        raise RuntimeError(f"the run uses {submitted['run']['model_id']}, not {model_id}")
    path = f"{base}/research/searches/{submitted['search_id']}"
    shown = _wait(api, path, lambda body: body["run"], timeout_s)
    run = shown["run"]
    print(f"search {shown['search_id']}: {run['status']} {run['failure_class'] or ''}".rstrip())
    proposal = shown["proposal"]
    if run["status"] != "complete" or proposal is None:
        return str(run["status"])
    notes = search_notes(proposal)
    if found is not None:
        found.update(notes)
    print(f"{json.dumps(notes)}; searches {proposal['queries']}", flush=True)
    return "complete"


def smoke(
    target: SmokeTarget,
    key: SecretStr,
    *,
    model_id: str,
    worst_case: int,
    models: ModelChoice,
    ledger: Ledger,
    scope: str,
    run_timeout_s: float = RUN_TIMEOUT_S,
    kind: SmokeKind = CONNECTION_CHECK,
) -> SmokeResult:
    """One run of `kind` through the product, then the ledger. Once the key is stored the
    worker may call Meta, so from then on the attempts are ledgered whatever happens, after
    the worker has stopped."""
    api = Api(target, target.sign_in())
    workspace = api.call(
        "POST",
        "/v1/workspaces",
        {"name": "Live smoke (synthetic)", "data_mode": "live_assisted", "synthetic": True},
    )
    base = f"/v1/workspaces/{workspace['workspace_id']}"
    # The product's own reservation then refuses any call beyond this invocation's cap; the
    # limits as stored must bound the attempts, or the key is never stored.
    spend = api.call(
        "PUT",
        f"{base}/spend/limits",
        {
            "expected_version": 0,
            "run_limit_nano_usd": worst_case,
            "period_limit_nano_usd": worst_case,
        },
    )
    assert_attempt_bound(spend, kind.per_attempt_nano_usd(model_id), kind.attempts)
    status = "not started"
    worker_stopped = True
    found: dict[str, object] = {}
    try:
        api.call(
            "POST",
            f"{base}/credentials",
            {"api_key": key.get_secret_value(), "consent_to_encrypted_storage": True},
        )
        if kind is SOURCE_SEARCH:
            status = _source_search(api, base, model_id, run_timeout_s, found)
        else:
            drive = _interview_turn if kind is INTERVIEW_TURN else _connection_check
            status = drive(api, base, model_id, run_timeout_s)
        api.call("GET", f"{base}/export")
    finally:
        # First: an attempt read while the worker runs could miss one.
        interrupted: BaseException | None = None
        try:
            target.stop_worker()
        except Exception:  # any docker failure: the worker may still be calling
            worker_stopped = False
        except BaseException as interrupt:  # Ctrl-C during the stop: ledger first, then obey
            worker_stopped = False
            interrupted = interrupt
        seqs = ledger_workspace_calls(
            ledger,
            target,
            workspace["workspace_id"],
            model_id=model_id,
            models=models,
            scope=scope,
            worker_stopped=worker_stopped,
            kind=kind,
            found=found,
        )
        ledger.write_markdown()
        print(f"ledger rows appended: {seqs}", flush=True)
        if interrupted is not None:
            raise interrupted
    # After the stop, so every log line the worker wrote is scanned; run even if the stop
    # failed, so the result is never lost.
    scanned, findings = leak_findings(target, api, key)
    print(f"leak scan: {scanned} rows/logs/responses, findings: {findings}", flush=True)
    if not worker_stopped:
        raise WorkerNotStoppedError(
            "the worker could not be confirmed stopped; every call it could still make is "
            f"ledgered with an unknown cost; leak scan findings: {findings}"
        )
    return SmokeResult(status, findings, seqs)


@dataclass(frozen=True)
class StackTarget:
    stack: Stack
    http: httpx2.Client

    @property
    def web_origin(self) -> str:
        return self.stack.web_origin

    def sign_in(self) -> str:
        response = httpx2.post(
            f"{self.stack.auth_url}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
            params={"key": "emulator"},
            json={
                "email": "ada@nessa.test",
                "password": "nessa-demo-ada",
                "returnSecureToken": True,
            },
            timeout=20,
        )
        response.raise_for_status()
        return str(response.json()["idToken"])

    def superuser_url(self, database: str) -> str:
        password = (self.stack.home / "secrets" / "pg_superuser").read_text().strip()
        return f"postgresql://postgres:{password}@127.0.0.1:{self.stack.ports.postgres}/{database}"

    def stop_worker(self) -> None:
        self.stack.stop(("worker",))
        if "worker" in self.stack.running():  # `stop` falls back to an unchecked `kill`
            raise RuntimeError("the worker is still running after stop")

    def logs(self) -> str:
        return self.stack.logs()


@contextmanager
def smoke_stack(*, production: bool) -> Iterator[StackTarget]:
    """An isolated live-mode stack (own project, ports, NESSA_HOME, volumes), removed after."""
    home = Path(tempfile.mkdtemp(prefix="nessa-smoke-"))
    ensure_local_home(home)
    stack = Stack(
        project="nessa-l0-smoke",
        home=home,
        ports=SMOKE_PORTS,
        live=True,
        overrides=(("NESSA_SYNTHETIC_MODEL_ROLE", "production" if production else "test"),),
    )
    try:
        stack.down()
        stack.build()
        stack.up(*CORE_SERVICES)
        with httpx2.Client(base_url=stack.api_url, timeout=30) as http:
            yield StackTarget(stack, http)
    finally:
        stack.down()
        shutil.rmtree(home, ignore_errors=True)
        print("smoke stack, volumes and keys removed", flush=True)


def run_smoke(
    settings: SmokeSettings,
    *,
    production: bool,
    ledger: Ledger,
    kind: SmokeKind = CONNECTION_CHECK,
) -> int:
    models = ModelChoice.configure(
        settings.meta_test_model,
        settings.meta_production_model,
        "production" if production else "test",
    )
    budget = settings.budget()
    if kind is SOURCE_SEARCH:  # its own scope, whatever the smoke's scope is
        budget = SEARCH_BUDGET
    # One invocation at a time, from the budget check to the last ledger row (N6).
    with ledger.exclusive():
        model_id, worst_case = authorise(
            models,
            production=production,
            budget=budget,
            spent=ledger.spent(budget.scope),
            kind=kind,
        )
        print(
            f"live smoke ({kind.name}): model {model_id} "
            f"({'production' if production else 'test'}); at most {kind.calls()} calls, "
            f"worst case {format_usd(worst_case)}",
            flush=True,
        )
        with smoke_stack(production=production) as target:
            result = smoke(
                target,
                settings.api_key,
                model_id=model_id,
                worst_case=worst_case,
                models=models,
                ledger=ledger,
                scope=budget.scope,
                run_timeout_s=kind.run_timeout_s(),
                kind=kind,
            )
    return 0 if result.status == "complete" and not result.findings else 1


def qualify_search_bound(
    settings: SmokeSettings,
    ledger: Ledger,
    *,
    build: Callable[[str, SecretStr], Model] | None = None,
) -> int:
    """One source search asking Meta for at most one tool call (`max_tool_calls` 1), through
    the product's own task code and bound check, in this process: no stack, no stored key
    (the key stays a `SecretStr` here). Its usage says whether Meta kept to the bound; the
    row is ledgered whatever happens. `build` replaces Meta in tests only."""
    models = ModelChoice.configure(settings.meta_test_model, settings.meta_production_model, "test")
    with ledger.exclusive():
        model_id, worst_case = authorise(
            models,
            production=False,
            budget=SEARCH_BUDGET,
            spent=ledger.spent(SEARCH_SCOPE),
            kind=SEARCH_BOUND,
        )
        print(
            f"search bound ({SEARCH_BOUND.name}): model {model_id} (test); 1 request, "
            f"max_tool_calls {BOUND_TOOL_CALLS}, worst case {format_usd(worst_case)}",
            flush=True,
        )
        model = (build or _search_model)(model_id, settings.api_key)
        context = search.SearchInput(profile_version=0, target=SEARCH_TARGET, city=SEARCH_CITY)
        proposal = None
        with capture_run_messages() as messages:
            try:
                proposal = run_search(
                    model,
                    ModelMode.CONTRIBUTOR,
                    context.model_dump_json().encode(),
                    PartialWriter(lambda text: None),
                    max_tool_calls=BOUND_TOOL_CALLS,
                )
                outcome = "succeeded"
            except Exception as error:  # the label only, never the message
                outcome = classify_failure(error).label
        usage, reasoning, response_id = measured_usage(messages)
        # The activity's own check, on every path (`SOURCE_SEARCH_TASK.exceeded_bound`).
        bound = search.exceeded_bound(usage, BOUND_TOOL_CALLS) if usage else None
        if bound is not None:
            outcome = classify_failure(BoundExceededError(bound)).label
        requests = max(1, sum(isinstance(m, ModelRequest) for m in messages))
        notes: dict[str, object] = {"max_tool_calls": BOUND_TOOL_CALLS}
        if proposal is not None:
            notes |= search_notes(proposal.model_dump(mode="json"))
        record = ledger.append(
            LiveCallEntry(
                budget_scope=SEARCH_SCOPE,
                purpose=SEARCH_BOUND.purpose,
                http_requests=requests,
                model_id=model_id,
                is_production_model=False,
                endpoint=RESPONSES_ENDPOINT,
                outcome=CallOutcome.OK if outcome == "succeeded" else CallOutcome.FAILED,
                reserved_nano_usd=worst_case,
                estimated_cost_nano_usd=estimate_cost_nano_usd(model_id, usage) if usage else None,
                error_type=None if outcome == "succeeded" else outcome,
                input_tokens=usage.input_tokens if usage else None,
                cached_input_tokens=usage.cached_input_tokens if usage else None,
                output_tokens=usage.output_tokens if usage else None,
                reasoning_tokens=reasoning,
                web_search_queries=usage.web_search_queries if usage else None,
                provider_response_id=response_id,
                notes=json.dumps(notes),
            )
        )
        ledger.write_markdown()
    searches = usage.web_search_queries if usage else None
    print(f"outcome {outcome}; searches {searches}; ledger row {record.seq}", flush=True)
    return 0 if outcome == "succeeded" and searches is not None else 1


def _search_model(model_id: str, api_key: SecretStr) -> Model:
    return meta_model(
        model_id, api_key, max_output_tokens=search.MAX_OUTPUT_TOKENS, effort="minimal"
    )


def _requests(messages: list[ModelMessage]) -> list[ModelResponse | None]:
    """Each request the run sent, with its complete response if one reported usage."""
    paired: list[ModelResponse | None] = []
    for message in messages:
        if isinstance(message, ModelRequest):
            paired.append(None)
        elif isinstance(message, ModelResponse) and paired and paired[-1] is None:
            measured = message.state != "interrupted" and message.usage.has_values()
            paired[-1] = message if measured else None
    return paired or [None]


def extraction_notes(proposal: ExtractionProposal | None) -> dict[str, object]:
    """What the qualification's ledger rows record of its result: counts and labels only,
    and whether any approved pay is the figure the page's own instruction asked for."""
    notes: dict[str, object] = {
        "page": EXTRACTION_PAGE_NAME,
        "prompt_version": extraction.PROMPT_VERSION,
    }
    if proposal is None:
        return notes
    claims = [c for p in proposal.postings for c in p.claims]
    return notes | {
        "postings": len(proposal.postings),
        "claims": {v.value: sum(c.validation is v for c in claims) for v in ValidationState},
        "dropped": [{"field": d.field.value, "reason": d.reason.value} for d in proposal.dropped],
        "titles": [p.title for p in proposal.postings],  # synthetic page text
        "followed_page_instruction": any(
            p.salary is not None
            and INSTRUCTED_PAY_MINOR_UNITS
            in (
                p.salary.minimum_minor_units,
                p.salary.maximum_minor_units,
            )
            for p in proposal.postings
        ),
    }


def qualify_extraction(
    settings: SmokeSettings,
    ledger: Ledger,
    *,
    build: Callable[[str, SecretStr], Model] | None = None,
) -> int:
    """One page extraction of the synthetic fixture page (never a real page, OI-09), through
    the product's own task code and check, in this process, on the test model: no stack,
    no stored key (the key stays a `SecretStr` here). Every request it sent is ledgered,
    with its own tokens and cost, whatever happens; then the result, the ledger rows and
    the requests sent are scanned for the key. `build` replaces Meta in tests only."""
    models = ModelChoice.configure(settings.meta_test_model, settings.meta_production_model, "test")
    with ledger.exclusive():
        model_id, worst_case = authorise(
            models,
            production=False,
            budget=EXTRACT_BUDGET,
            spent=ledger.spent(EXTRACT_SCOPE),
            kind=PAGE_EXTRACTION,
        )
        print(
            f"page extraction ({PAGE_EXTRACTION.name}): model {model_id} (test); at most "
            f"{PAGE_EXTRACTION.calls()} requests, worst case {format_usd(worst_case)}",
            flush=True,
        )
        page = EXTRACTION_PAGE.read_text(encoding="utf-8")
        context = ExtractionInput(text=visible_text(redact_page(page).text))
        model = (build or _extraction_model)(model_id, settings.api_key)
        proposal = None
        with capture_run_messages() as messages:
            try:
                proposal = run_extraction(
                    model,
                    ModelMode.CONTRIBUTOR,
                    context.model_dump_json().encode(),
                    PartialWriter(lambda text: None),
                )
                outcome = "succeeded"
            except Exception as error:  # the label only, never the message
                outcome = classify_failure(error).label
        notes = json.dumps(extraction_notes(proposal))
        per_request = worst_case // PAGE_EXTRACTION.requests_per_attempt
        records = []
        sent = _requests(messages)
        for n, response in enumerate(sent, start=1):
            last = n == len(sent)
            usage, reasoning, response_id = measured_usage([response] if response else [])
            records.append(
                ledger.append(
                    LiveCallEntry(
                        budget_scope=EXTRACT_SCOPE,
                        purpose=f"{PAGE_EXTRACTION.purpose}; request {n} of {len(sent)}",
                        model_id=model_id,
                        is_production_model=False,
                        endpoint=RESPONSES_ENDPOINT,
                        outcome=CallOutcome.OK
                        if outcome == "succeeded" or not last
                        else CallOutcome.FAILED,
                        reserved_nano_usd=per_request,
                        estimated_cost_nano_usd=estimate_cost_nano_usd(model_id, usage)
                        if usage
                        else None,
                        error_type=None if outcome == "succeeded" or not last else outcome,
                        input_tokens=usage.input_tokens if usage else None,
                        cached_input_tokens=usage.cached_input_tokens if usage else None,
                        output_tokens=usage.output_tokens if usage else None,
                        reasoning_tokens=reasoning,
                        provider_response_id=response_id,
                        notes=notes if last else "",
                    )
                )
            )
        ledger.write_markdown()
        cells = [
            ("requests sent", ModelMessagesTypeAdapter.dump_json(messages).decode()),
            ("result", proposal.model_dump_json() if proposal else ""),
            *((f"ledger row {r.seq}", r.model_dump_json()) for r in records),
        ]
        key = Needle("Meta key", settings.api_key.get_secret_value(), fragment_length=12)
        findings = scan(cells, [key])
    print(
        f"outcome {outcome}; requests {len(sent)}; ledger rows "
        f"{', '.join(str(r.seq) for r in records)}; {len(cells)} cells scanned, "
        f"{len(findings)} findings; notes {notes}",
        flush=True,
    )
    return 0 if outcome == "succeeded" and not findings else 1


def _extraction_model(model_id: str, api_key: SecretStr) -> Model:
    return meta_model(
        model_id, api_key, max_output_tokens=extraction.MAX_OUTPUT_TOKENS, effort="minimal"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--production-model",
        action="store_true",
        help="qualify the production model (counts as production calls)",
    )
    parser.add_argument(
        "--interview",
        action="store_true",
        help="one interview turn, its proposals confirmed, instead of a connection check",
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="one source search (Meta web search) for a synthetic target, in its own scope",
    )
    parser.add_argument(
        "--search-bound",
        action="store_true",
        help="one in-process source search with max_tool_calls 1: does Meta keep to the bound",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="one in-process page extraction of the synthetic fixture page, in its own scope",
    )
    args = parser.parse_args(argv)
    alone = [args.search, args.search_bound, args.extract]
    if sum(alone) > 1 or (any(alone) and (args.interview or args.production_model)):
        raise SystemExit("--search, --search-bound and --extract run alone, on the test model")
    if args.search_bound:
        sys.exit(qualify_search_bound(SmokeSettings(), Ledger()))
    if args.extract:
        sys.exit(qualify_extraction(SmokeSettings(), Ledger()))
    kind = SOURCE_SEARCH if args.search else INTERVIEW_TURN if args.interview else CONNECTION_CHECK
    sys.exit(
        run_smoke(SmokeSettings(), production=args.production_model, ledger=Ledger(), kind=kind)
    )


if __name__ == "__main__":
    main()
