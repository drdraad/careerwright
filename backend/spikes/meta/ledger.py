"""Append-only JSONL ledger of live Meta calls, rendered into docs/evidence/live-usage.md."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from spikes.meta.budget import SpentSoFar
from spikes.meta.pricing import format_usd


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
    # None means the charge could not be determined; it is never silently zero.
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


class Ledger:
    def __init__(self, path: Path) -> None:
        self._path = path

    def records(self) -> list[LiveCallRecord]:
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        return [LiveCallRecord.model_validate_json(line) for line in lines if line.strip()]

    def append(self, entry: LiveCallEntry) -> LiveCallRecord:
        record = LiveCallRecord(
            **entry.model_dump(),
            seq=len(self.records()) + 1,
            recorded_at=datetime.now(UTC),
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")
        return record

    def spent(self, budget_scope: str) -> SpentSoFar:
        scoped = [r for r in self.records() if r.budget_scope == budget_scope]
        return SpentSoFar(
            calls=len(scoped),
            production_calls=sum(1 for r in scoped if r.is_production_model),
            committed_nano_usd=sum(_committed(r) for r in scoped),
        )

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
                outcome = f"failed ({r.http_status or '-'} {r.error_type or ''})".replace(" )", ")")
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


def _committed(record: LiveCallRecord) -> int:
    if record.estimated_cost_nano_usd is None:
        return record.reserved_nano_usd
    return record.estimated_cost_nano_usd


def _count(value: int | None) -> str:
    return "-" if value is None else f"{value:,}"
