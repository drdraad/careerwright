"""Append-only JSONL ledger of live Meta calls, rendered into docs/evidence/live-usage.md
(ruling R5; promoted from the Sprint 0 spike). Every HTTP call to Meta made by Nessa tooling
is recorded, free and failed calls included. A charge that cannot be determined is
`unknown` (null), never zero, and counts its full reservation in the running total's caveat.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from nessa.identity.model_registry import PRICE_SOURCE, format_usd

LEDGER_PATH = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "live-usage.jsonl"
PRICES_CHECKED_ON = "2026-10-27"


class CallOutcome(StrEnum):
    OK = "ok"
    FAILED = "failed"


class LiveCallEntry(BaseModel):
    """One HTTP call to Meta, before a sequence number is assigned."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    budget_scope: str
    purpose: str
    model_id: str
    is_production_model: bool
    endpoint: str
    outcome: CallOutcome
    reserved_nano_usd: int = Field(ge=0)
    estimated_cost_nano_usd: int | None = Field(default=None, ge=0)
    http_status: int | None = None
    error_type: str | None = None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    web_search_queries: int | None = None
    provider_response_id: str | None = None
    notes: str = ""


class LiveCallRecord(LiveCallEntry):
    seq: int
    recorded_at: datetime


@dataclass(frozen=True)
class ScopeSpend:
    """What a budget scope has used so far, from the ledger."""

    calls: int
    production_calls: int
    committed_nano_usd: int  # known costs plus the full reservation of every unknown one


class Ledger:
    def __init__(self, path: Path = LEDGER_PATH) -> None:
        self._path = path

    def spent(self, scope: str) -> ScopeSpend:
        rows = [r for r in self.records() if r.budget_scope == scope]
        return ScopeSpend(
            calls=len(rows),
            production_calls=sum(r.is_production_model for r in rows),
            committed_nano_usd=sum(
                r.reserved_nano_usd
                if r.estimated_cost_nano_usd is None
                else r.estimated_cost_nano_usd
                for r in rows
            ),
        )

    def records(self) -> list[LiveCallRecord]:
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        return [LiveCallRecord.model_validate_json(line) for line in lines if line.strip()]

    def append(self, entry: LiveCallEntry) -> LiveCallRecord:
        record = LiveCallRecord(
            **entry.model_dump(), seq=len(self.records()) + 1, recorded_at=datetime.now(UTC)
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")
        return record

    def render_markdown_table(self) -> str:
        header = (
            "| # | UTC time | Scope | Purpose | Model | Endpoint | Outcome | In (cached) | Out "
            "(reasoning) | Searches | Est. cost | Running total | Response ID |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"
        )
        rows = []
        known_total = 0
        unknown_seen = False
        for r in self.records():
            if r.estimated_cost_nano_usd is None:
                unknown_seen = True
                cost = "unknown"
            else:
                known_total += r.estimated_cost_nano_usd
                cost = format_usd(r.estimated_cost_nano_usd)
            running = format_usd(known_total) + (" + unknown" if unknown_seen else "")
            outcome = r.outcome.value
            if r.outcome is CallOutcome.FAILED:
                known = [str(part) for part in (r.http_status, r.error_type) if part]
                outcome = f"failed ({' '.join(known) or 'no detail'})"
            rows.append(
                f"| {r.seq} | {r.recorded_at:%Y-%m-%d %H:%M:%S} | {r.budget_scope} | {r.purpose} "
                f"| `{r.model_id}`{' (production)' if r.is_production_model else ''} "
                f"| {r.endpoint} | {outcome} "
                f"| {_count(r.input_tokens)} ({_count(r.cached_input_tokens)}) "
                f"| {_count(r.output_tokens)} ({_count(r.reasoning_tokens)}) "
                f"| {_count(r.web_search_queries)} | {cost} | {running} "
                f"| {r.provider_response_id or '-'} |"
            )
        return "\n".join([header, *rows])

    def write_markdown(self) -> None:
        """Render next to the ledger (`live-usage.md` for the real one)."""
        self._path.with_suffix(".md").write_text(
            "# Live Meta usage log\n\n"
            "Every HTTP call to the Meta Model API made by Nessa tooling, including failures and\n"
            "free calls (ruling R5). Generated from `live-usage.jsonl` by\n"
            "`backend/tools/usage_ledger.py`; do not edit the table by hand.\n\n"
            f"- Prices: {PRICE_SOURCE} (checked {PRICES_CHECKED_ON}); costs are estimates from\n"
            "  reported usage, in USD before tax. `unknown` means the charge could not be\n"
            "  determined; the budget then counts the call's full reservation.\n"
            "- `In` includes cached tokens; `Out` includes reasoning tokens (Meta usage\n"
            "  semantics).\n"
            "- `Searches` is Pydantic AI's billed count: Meta's `tool_usage` count if present,\n"
            "  else `search` actions. Whether Meta reports `tool_usage` for search calls was not\n"
            "  captured, and Meta does not document whether other actions (`open_page`,\n"
            "  `find_in_page`) are billed. An upper bound adds $0.0025 per uncounted\n"
            "  `web_search_call` item (calls 5 and 7: one each; see the JSONL `notes`). Rows 3-5\n"
            "  predate raw-usage and action-type capture in the tool; their request path was\n"
            "  otherwise the same.\n"
            "- Remaining credit: not exposed by any documented Meta API endpoint; check the\n"
            "  developer dashboard.\n"
            "- Budgets: `task-1-sprint-0` (Sprint 0 spike): at most 15 calls, 5 on the production\n"
            "  model, $0.30 worst case. `live-smoke` (`make live-smoke`): each invocation at most\n"
            "  3 calls, none on the production model unless `PRODUCTION=1`, and a worst-case cost\n"
            "  cap; cumulatively at most 9 calls, 3 on the production model and $0.30 worst case\n"
            "  (unknown costs count their full reservation; `NESSA_LIVE_SMOKE_*` changes them).\n"
            "  Both are enforced in `backend/tools/live_smoke.py` before the stack starts.\n\n"
            f"{self.render_markdown_table()}\n",
            encoding="utf-8",
        )


def _count(value: int | None) -> str:
    return "-" if value is None else f"{value:,}"
