"""The product owner's live sessions on Muse Wonder (ADR 0003, amendment of 2026-10-31).

`make session` starts the normal live stack, as `make dev` does: the same Compose project
and CAREERWRIGHT_HOME, nothing reset or rebuilt. It differs in two settings, so a running
API and worker restart with them (Compose recreates both); a run in flight restarts too, its
interrupted call counted at its full reservation. Nothing else is stopped.
- `muse-wonder-1.0` is the production model, so every workspace not marked synthetic runs
  Wonder. Synthetic workspaces keep the test model, and the test model's safeguards (in code
  and the database CHECK) are untouched.
- The API's default limits are the session's caps, for a workspace whose key is first stored
  during the session.
Then it sets the session's caps, through the API as each invited person, on every live
workspace not marked synthetic. The caps are per workspace (the product owner's ruling of
31 October 2026): a run may reserve at most `SESSION_RUN_LIMIT_NANO_USD`, and a workspace's
monthly limit becomes what its month has already committed plus
`SESSION_SPEND_PER_WORKSPACE_NANO_USD`, so the session can add at most that to each
workspace. Its total ceiling is that much for each workspace capped at start, plus as much
again for each workspace whose key is stored during the session; the start summary prints
it. The product's own reservation enforces both caps before every call; unknown costs keep
their full reservation. Running `make dev` afterwards goes back to Spark (restarting the API
and worker again); the limits stay as set, and the spending line in the app changes them.

`make session-ledger` copies every model attempt in the live stack's database, under `make
session` or `make dev` alike, into `docs/evidence/live-usage.jsonl` and `.md` (ruling R5),
under the scope `live-app-<the attempt's UTC date>`; the dates keep each session's apart. It
reads the database through the stack's published port, so the stack must be up. It reads
only each attempt's model, run kind, token and search counts, cost, reservation, state and
time, and its identifiers, so that no attempt is copied twice: never a message, answer,
prompt, output or other text. A cost Meta did not report counts its full reservation. An
attempt still in flight is not copied yet, and the command fails until it has settled.

Neither ever runs in `make check` or `make acceptance`: starting a session is the product
owner's or the controller's act.

Run from `backend/`: `uv run --locked python -m tools.session start|ledger`.
"""

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence, Set
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx2
import psycopg
from psycopg.rows import dict_row

from careerwright.capability import strength
from careerwright.evidence import extraction, search
from careerwright.identity.model_registry import WONDER_MODEL_ID, ModelMode, format_usd, model_entry
from careerwright.identity.records import RunKind
from careerwright.profile import discovery, interview, slate_explanation
from careerwright.seed import INVITED_ACTORS
from careerwright.vocabulary import DataMode
from tools.live_smoke import RESPONSES_ENDPOINT, Api
from tools.localenv import careerwright_home, ensure_local_home
from tools.stack import CORE_SERVICES, Stack, ports_from_env, project_from_env
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry, LiveCallRecord

# The session's caps, each per workspace (the audit's Muse Wonder notes; ADR 0003, amendment
# and its qualification result; the product owner's ruling of 31 October 2026): $0.75 a run,
# so every run kind's three attempts fit on Wonder ($0.552 at most, a slate's written note),
# and $5 per workspace on top of what its month has committed.
SESSION_RUN_LIMIT_NANO_USD = 750_000_000
SESSION_SPEND_PER_WORKSPACE_NANO_USD = 5_000_000_000
# The ledger copy's scope: every attempt in the live stack's database, by its UTC date.
LEDGER_SCOPE_PREFIX = "live-app"
WORKSPACE_PAGE = 200  # the API's largest page

# What the ledger copy reads of the product's run records, and nothing else.
COPIED_COLUMNS = (
    "a.run_id",
    "a.attempt_id",
    "a.model_id",
    "r.kind",
    "a.outcome",
    "a.spend_state",
    "a.reserved_nano_usd",
    "a.cost_nano_usd",
    "a.input_tokens",
    "a.cached_input_tokens",
    "a.output_tokens",
    "a.reasoning_tokens",
    "a.web_search_queries",
    "a.requests_sent",
    "a.started_at",
)
ATTEMPTS_SQL = (
    f"SELECT {', '.join(COPIED_COLUMNS)} FROM careerwright.model_attempts a "  # noqa: S608
    "JOIN careerwright.runs r USING (run_id) WHERE a.spend_state <> 'none' "
    "ORDER BY a.attempt_id"
)
# The requests one attempt may send, counted in full when the attempt did not record them.
MAX_REQUESTS: Mapping[str, int] = {
    RunKind.CONNECTION_CHECK: 1,
    RunKind.INTERVIEW_TURN: interview.MAX_REQUESTS,
    RunKind.DISCOVERY: discovery.MAX_REQUESTS,
    RunKind.SLATE_EXPLANATION: slate_explanation.MAX_REQUESTS,
    RunKind.SOURCE_SEARCH: search.MAX_REQUESTS,
    RunKind.PAGE_EXTRACTION: extraction.MAX_REQUESTS,
    RunKind.STRENGTH_PROPOSAL: strength.MAX_REQUESTS,
}


def session_stack() -> Stack:
    """The normal live stack (`make dev`'s project, home and ports, read as every stack
    command reads them) with the session's two settings; the synthetic role is pinned to the
    test model."""
    return Stack(
        project=project_from_env(),
        home=careerwright_home(),
        ports=ports_from_env(),
        live=True,
        overrides=(
            ("CAREERWRIGHT_META_PRODUCTION_MODEL", WONDER_MODEL_ID),
            ("CAREERWRIGHT_SYNTHETIC_MODEL_ROLE", "test"),
            ("CAREERWRIGHT_DEFAULT_RUN_SPEND_LIMIT_NANO_USD", str(SESSION_RUN_LIMIT_NANO_USD)),
            (
                "CAREERWRIGHT_DEFAULT_PERIOD_SPEND_LIMIT_NANO_USD",
                str(SESSION_SPEND_PER_WORKSPACE_NANO_USD),
            ),
        ),
    )


def session_limits(spend: Mapping[str, Any]) -> dict[str, int]:
    """The session's limits for a workspace's spend as the API states it: the run cap, and
    this month's committed spend (unknown costs at their full reservation) plus the
    session's $5 for this workspace."""
    return {
        "expected_version": int(spend["version"]),
        "run_limit_nano_usd": SESSION_RUN_LIMIT_NANO_USD,
        "period_limit_nano_usd": int(spend["period_committed_nano_usd"])
        + SESSION_SPEND_PER_WORKSPACE_NANO_USD,
    }


@dataclass(frozen=True)
class SessionCap:
    workspace_id: str
    name: str
    committed_nano_usd: int  # this month, before the session
    run_limit_nano_usd: int
    period_limit_nano_usd: int


def _workspaces(api: Api) -> Iterable[dict[str, Any]]:
    cursor: str | None = None
    while True:
        query = f"?limit={WORKSPACE_PAGE}" + (f"&cursor={cursor}" if cursor else "")
        page = api.call("GET", f"/v1/workspaces{query}")
        yield from page["items"]
        cursor = page["next_cursor"]
        if cursor is None:
            return


def set_session_caps(api: Api) -> list[SessionCap]:
    """The session's caps on every workspace of the signed-in person where the production
    model runs: live (not demo) and not marked synthetic. Each is the product's own
    expected-version command, so a limit changed meanwhile is refused, never overwritten."""
    capped = []
    for workspace in _workspaces(api):
        if workspace["synthetic"] or workspace["data_mode"] == DataMode.DEMO:
            continue
        base = f"/v1/workspaces/{workspace['workspace_id']}"
        spend = api.call("GET", f"{base}/spend")
        limits = api.call("PUT", f"{base}/spend/limits", session_limits(spend))
        capped.append(
            SessionCap(
                workspace["workspace_id"],
                workspace["name"],
                int(spend["period_committed_nano_usd"]),
                int(limits["run_limit_nano_usd"]),
                int(limits["period_limit_nano_usd"]),
            )
        )
    return capped


@dataclass(frozen=True)
class StackApi:
    http: httpx2.Client
    web_origin: str


def _sign_in(stack: Stack, email: str) -> str:
    # The emulator's seeded local test identities (docker/auth/seed; the runbook lists them).
    password = f"careerwright-demo-{email.partition('@')[0]}"
    response = httpx2.post(
        f"{stack.auth_url}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
        params={"key": "emulator"},
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    response.raise_for_status()
    return str(response.json()["idToken"])


def session_summary(web_origin: str, capped: Sequence[SessionCap]) -> str:
    """What `make session` prints once its caps are set. The caps are per workspace, so the
    session's total ceiling is $5 for each workspace capped now, and each workspace whose key
    is stored during the session adds $5 (it gets the API's session defaults)."""
    per_workspace = format_usd(SESSION_SPEND_PER_WORKSPACE_NANO_USD)
    lines = [
        f"Careerwright: {web_origin}  (open this in a browser)",
        f"Workspaces not marked synthetic run {WONDER_MODEL_ID}; synthetic ones keep the test "
        "model.",
        "The caps are per workspace: each run may reserve at most "
        f"{format_usd(SESSION_RUN_LIMIT_NANO_USD)}, and each workspace may spend at most "
        f"{per_workspace} more this month.",
    ]
    lines += [
        f"  {cap.name}: {format_usd(cap.committed_nano_usd)} committed this month, limit now "
        f"{format_usd(cap.period_limit_nano_usd)}, each run at most "
        f"{format_usd(cap.run_limit_nano_usd)}"
        for cap in capped
    ]
    if not capped:
        lines.append("  No live workspace yet: a new one gets these limits when its key is stored.")
    if len(capped) > 1:
        which = f"{per_workspace} for each of the {len(capped)} workspaces capped now"
    elif capped:
        which = f"{per_workspace} for the 1 workspace capped now"
    else:
        which = "no workspace is capped yet"
    lines += [
        "So this session can spend at most "
        f"{format_usd(len(capped) * SESSION_SPEND_PER_WORKSPACE_NANO_USD)} in all: {which}. "
        f"Each workspace whose key is stored during the session adds {per_workspace}.",
        "After the session, while the stack is still up (before `make stop`), run `make "
        "session-ledger`: it copies every model attempt in this stack's database into the "
        "cost ledger.",
    ]
    return "\n".join(lines)


def start() -> int:
    stack = session_stack()
    ensure_local_home(stack.home)
    print(
        f"starting a live session on {WONDER_MODEL_ID} (project {stack.project}): a running "
        "API and worker restart with the session's settings, and a run in flight restarts, "
        "its interrupted call counted at its full reservation; nothing else is stopped and "
        "no data is reset...",
        flush=True,
    )
    stack.up(*CORE_SERVICES)
    capped: list[SessionCap] = []
    with httpx2.Client(base_url=stack.api_url, timeout=30) as http:
        for actor in INVITED_ACTORS:
            target = StackApi(http, stack.web_origin)
            capped += set_session_caps(Api(target, _sign_in(stack, actor.email)))
    print(session_summary(stack.web_origin, capped), flush=True)
    return 0


def _copied(records: Iterable[LiveCallRecord]) -> Set[tuple[str, int]]:
    """The attempts already in the ledger's `live-app-<date>` scopes, by (run ID, attempt
    ID)."""
    found = set()
    for record in records:
        if record.budget_scope.startswith(f"{LEDGER_SCOPE_PREFIX}-") and record.notes:
            notes = json.loads(record.notes)
            found.add((str(notes["run_id"]), int(notes["attempt_id"])))
    return found


def session_entry(attempt: Mapping[str, Any]) -> LiveCallEntry:
    """One ledger row from an attempt's counts, cost and state alone."""
    kind = RunKind(attempt["kind"])
    started: datetime = attempt["started_at"]
    succeeded = attempt["outcome"] == "succeeded"
    return LiveCallEntry(
        budget_scope=f"{LEDGER_SCOPE_PREFIX}-{started:%Y-%m-%d}",
        purpose=(
            f"live app: one {kind.value.replace('_', ' ')} attempt from the live stack's "
            "database (`make session-ledger` copies every attempt there, by its UTC date: "
            "model, kind, counts, cost and state only)"
        ),
        http_requests=max(1, attempt["requests_sent"] or MAX_REQUESTS[kind]),
        model_id=attempt["model_id"],
        is_production_model=model_entry(attempt["model_id"]).mode is ModelMode.STANDARD,
        endpoint=RESPONSES_ENDPOINT,
        outcome=CallOutcome.OK if succeeded else CallOutcome.FAILED,
        reserved_nano_usd=attempt["reserved_nano_usd"],
        estimated_cost_nano_usd=attempt["cost_nano_usd"],
        error_type=None if succeeded else attempt["outcome"] or attempt["spend_state"],
        input_tokens=attempt["input_tokens"],
        cached_input_tokens=attempt["cached_input_tokens"],
        output_tokens=attempt["output_tokens"],
        reasoning_tokens=attempt["reasoning_tokens"],
        web_search_queries=attempt["web_search_queries"],
        notes=json.dumps(
            {
                "run_id": str(attempt["run_id"]),
                "attempt_id": attempt["attempt_id"],
                "started_at": started.isoformat(),
            }
        ),
    )


@dataclass(frozen=True)
class LedgerCopy:
    copied: list[LiveCallRecord]
    in_flight: int  # attempts still held: copied once they settle
    already: int


def copy_session_calls(database_url: str, ledger: Ledger) -> LedgerCopy:
    """Every settled attempt that reached the provider and is not in the ledger yet."""
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        attempts = conn.execute(ATTEMPTS_SQL).fetchall()
    with ledger.exclusive():
        done = _copied(ledger.records())
        new = [a for a in attempts if (str(a["run_id"]), a["attempt_id"]) not in done]
        settled = [a for a in new if a["spend_state"] != "held"]
        copied = [ledger.append(session_entry(a)) for a in settled]
        ledger.write_markdown()
    return LedgerCopy(copied, len(new) - len(settled), len(attempts) - len(new))


def copy_ledger() -> int:
    stack = session_stack()
    password = (stack.home / "secrets" / "pg_superuser").read_text(encoding="utf-8").strip()
    url = f"postgresql://postgres:{password}@127.0.0.1:{stack.ports.postgres}/careerwright_app"
    result = copy_session_calls(url, Ledger())
    known = sum(r.estimated_cost_nano_usd or 0 for r in result.copied)
    unknown = [r for r in result.copied if r.estimated_cost_nano_usd is None]
    print(
        f"copied {len(result.copied)} attempts (rows "
        f"{', '.join(str(r.seq) for r in result.copied) or 'none'}): {format_usd(known)} known"
        + (
            f", plus {len(unknown)} with an unknown cost counted at their full reservation "
            f"({format_usd(sum(r.reserved_nano_usd for r in unknown))})"
            if unknown
            else ""
        )
        + f"; {result.already} already in the ledger",
        flush=True,
    )
    if result.in_flight:
        print(
            f"{result.in_flight} attempts are still in flight: run `make session-ledger` again "
            "once they have settled.",
            flush=True,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "ledger"))
    args = parser.parse_args(argv)
    sys.exit(start() if args.command == "start" else copy_ledger())


if __name__ == "__main__":
    main()
