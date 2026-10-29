"""`make live-adzuna`: qualify the Adzuna adapter against the real API (ruling R4; controller
ruling for Task 7A), free tier only, capped and ledgered.

The credentials are read in code from the repository's gitignored `.env`, under the names the
product owner used (`ADZUNA_APPLICATION_ID`, `ADZUNA_API_KEY`; controller ruling, fix round
5), into `SecretStr`s, registered for log redaction, never printed and never a command
argument. If either name is absent (or empty) the command reports "blocked: Adzuna
credentials not found", which of the two is missing, and the names, never the values, of
the variables `.env` does set whose name holds "ADZUNA" (fix round 5, item 4), and makes no
request. Each request goes through the product's own path in the restricted acquisition
worker's code (`nessa.evidence.acquire.acquire_adzuna`: the guarded fetcher, the response
contract, the credential-free recorded URL) and is appended to
`docs/evidence/live-usage.jsonl` and `.md` with its request count, the endpoint as recorded
(no credentials), the result class and a cost of $0 (free tier). Nothing an advert says is
kept: the summary is counts only (session 1 class 6, reference only). Then the results, the
ledger rows this run wrote and the ledger's table are scanned for either credential
(`tools.leak_scan`); a finding, named by place and credential name only, fails the run.

Caps, enforced before any request under the ledger's exclusive lock: at most
`REQUESTS_PER_RUN` per invocation and `MAX_SCOPE_REQUESTS` in the `live-adzuna` scope.

Run from `backend/`: `uv run --locked python -m tools.live_adzuna`.
"""

import argparse
import json
import sys
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from nessa.evidence.acquire import AcquisitionResult, Pacer, acquire_adzuna
from nessa.evidence.adzuna import AdzunaQuery
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.jobs import group_copies
from nessa.evidence.records import AttemptStatus
from nessa.evidence.sources import load_manifest
from nessa.logs import register_secret
from tools.leak_scan import Needle, scan
from tools.localenv import ADZUNA_ENV, ENV_FILE, env_names_containing
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry, LiveCallRecord

SCOPE = "live-adzuna"
MAX_SCOPE_REQUESTS = 10
# Two pages of one ordinary search: the response contract, pay bases, snippets, pagination
# and deduplication across pages.
QUERIES = (
    AdzunaQuery(what="data analyst", where="Manchester", page=1, results_per_page=20),
    AdzunaQuery(what="data analyst", where="Manchester", page=2, results_per_page=20),
)
REQUESTS_PER_RUN = len(QUERIES)
MODEL_COLUMN = "adzuna-jobs-api"
BLOCKED = "blocked: Adzuna credentials not found"
ID_NAME, KEY_NAME = ADZUNA_ENV  # the `.env` names, the same ones setup reads

Acquire = Callable[..., AcquisitionResult]


class AdzunaSettings(BaseSettings):
    # An empty value is no credential, as setup reads it (`localenv.place_adzuna_credentials`).
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True
    )

    app_id: SecretStr | None = Field(default=None, validation_alias=ID_NAME)
    app_key: SecretStr | None = Field(default=None, validation_alias=KEY_NAME)


def _entry(query: AdzunaQuery, result: AcquisitionResult) -> LiveCallEntry:
    sent = result.status is not AttemptStatus.BLOCKED
    bases = Counter(c.salary.basis.value if c.salary else "none" for c in result.copies)
    kinds = sorted({c.description_kind.value for c in result.copies if c.description_kind})
    return LiveCallEntry(
        budget_scope=SCOPE,
        provider="adzuna",
        purpose=f"Adzuna search page {query.page} through the acquisition adapter (free tier)",
        http_requests=1,
        model_id=MODEL_COLUMN,
        is_production_model=False,
        endpoint=f"GET {result.requested_url}",
        outcome=CallOutcome.OK if result.status is AttemptStatus.SUCCEEDED else CallOutcome.FAILED,
        reserved_nano_usd=0,
        estimated_cost_nano_usd=0,
        http_status=result.http_status,
        error_type=result.reason,
        notes=(
            f"free tier ($0); request sent: {sent}; {len(result.copies)} adverts of "
            f"{result.total} matching; pay basis {dict(sorted(bases.items()))}; "
            f"descriptions {kinds}"
        ),
    )


def run(
    settings: AdzunaSettings,
    ledger: Ledger,
    *,
    acquire: Acquire = acquire_adzuna,
    fetcher: Fetcher | None = None,
    env_file: Path = ENV_FILE,
) -> dict[str, object]:
    """The qualification; returns its summary (counts and names only, never a credential)."""
    if settings.app_id is None or settings.app_key is None:
        found = {ID_NAME: settings.app_id, KEY_NAME: settings.app_key}
        return {
            "status": BLOCKED,
            "missing": [name for name, value in found.items() if value is None],
            "adzuna_names_in_env": env_names_containing(env_file, "ADZUNA"),
        }
    credentials = (settings.app_id, settings.app_key)
    for secret in credentials:
        register_secret(secret.get_secret_value())
    used = fetcher or Fetcher(user_agent=load_manifest().user_agent)
    results: list[AcquisitionResult] = []
    rows: list[LiveCallRecord] = []
    with ledger.exclusive():
        spent = ledger.spent(SCOPE).calls
        if spent + REQUESTS_PER_RUN > MAX_SCOPE_REQUESTS:
            raise SystemExit(
                f"refused: the {SCOPE} scope has used {spent} of {MAX_SCOPE_REQUESTS} requests"
            )
        pacer = Pacer()
        for query in QUERIES:
            result = acquire(used, pacer, query, credentials, now=datetime.now(UTC))
            rows.append(ledger.append(_entry(query, result)))
            results.append(result)
            if result.status is not AttemptStatus.SUCCEEDED:
                break  # a failed page is recorded; the next would only repeat it
        ledger.write_markdown()
    copies = [("adzuna", c) for r in results for c in r.copies]
    # Everything the worker would store (claims, URLs, excerpts) is scanned for either
    # credential's value, which Adzuna may echo in a landing link (review A M3), and so is
    # everything this run wrote to the ledger (fix round 5). A finding names its place and
    # the credential's `.env` name, never the value.
    cells = [
        *((f"result {n}", r.model_dump_json()) for n, r in enumerate(results, start=1)),
        *((f"ledger row {row.seq}", row.model_dump_json()) for row in rows),
        ("ledger table", ledger.render_markdown_table()),
    ]
    needles = [
        Needle(name, secret.get_secret_value())
        for name, secret in zip((ID_NAME, KEY_NAME), credentials, strict=True)
    ]
    findings = scan(cells, needles)
    echoed = len({f.location for f in findings if f.location.startswith("result ")})
    return {
        "status": "complete"
        if not findings and all(r.status is AttemptStatus.SUCCEEDED for r in results)
        else "failed",
        "results_holding_a_credential": echoed,
        "leak_scan": {
            "cells": len(cells),
            "findings": [f"{f.location}: {f.needle_label}" for f in findings],
        },
        "requests": len(results),
        "outcomes": [
            f"{r.status.value} {r.http_status or ''} {r.reason or ''}".strip() for r in results
        ],
        "adverts": len(copies),
        "distinct_jobs": len(group_copies(copies)),
        "pay_basis": dict(
            sorted(Counter(c.salary.basis.value if c.salary else "none" for _, c in copies).items())
        ),
        "with_period": sum(1 for _, c in copies if c.salary and c.salary.period),
        "descriptions": sorted({c.description_kind.value for _, c in copies if c.description_kind}),
        "agency_adverts": sum(1 for _, c in copies if c.advertiser.value == "agency"),
        "claims": sum(len(c.claims) for _, c in copies),
        "total_matching": results[0].total if results else None,
    }


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    summary = run(AdzunaSettings(), Ledger())
    print(json.dumps(summary, indent=2))
    sys.exit(0 if summary["status"] == "complete" else (2 if summary["status"] == BLOCKED else 1))


if __name__ == "__main__":
    main()
