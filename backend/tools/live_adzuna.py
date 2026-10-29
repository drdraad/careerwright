"""`make live-adzuna`: qualify the Adzuna adapter against the real API (ruling R4; controller
ruling for Task 7A), free tier only, capped and ledgered.

The credentials are read in code from the repository's gitignored `.env` (`ADZUNA_APP_ID`,
`ADZUNA_APP_KEY`) into `SecretStr`s, registered for log redaction, never printed and never a
command argument. If either name is absent the command reports "blocked: Adzuna credentials
not found" and makes no request. Each request goes through the product's own path in the
restricted acquisition worker's code (`nessa.evidence.acquire.acquire_adzuna`: the guarded
fetcher, the response contract, the credential-free recorded URL) and is appended to
`docs/evidence/live-usage.jsonl` and `.md` with its request count, the endpoint as recorded
(no credentials), the result class and a cost of $0 (free tier). Nothing an advert says is
kept: the summary is counts only (session 1 class 6, reference only).

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

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from nessa.evidence.acquire import AcquisitionResult, Pacer, acquire_adzuna
from nessa.evidence.adzuna import AdzunaQuery
from nessa.evidence.fetcher import Fetcher
from nessa.evidence.jobs import group_copies
from nessa.evidence.records import AttemptStatus
from nessa.evidence.sources import load_manifest
from nessa.logs import register_secret
from tools.localenv import REPO_ROOT
from tools.usage_ledger import CallOutcome, Ledger, LiveCallEntry

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

Acquire = Callable[..., AcquisitionResult]


class AdzunaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_id: SecretStr | None = Field(default=None, validation_alias="ADZUNA_APP_ID")
    app_key: SecretStr | None = Field(default=None, validation_alias="ADZUNA_APP_KEY")


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
) -> dict[str, object]:
    """The qualification; returns its summary (counts only, never a credential)."""
    if settings.app_id is None or settings.app_key is None:
        return {"status": BLOCKED}
    credentials = (settings.app_id, settings.app_key)
    for secret in credentials:
        register_secret(secret.get_secret_value())
    used = fetcher or Fetcher(user_agent=load_manifest().user_agent)
    results: list[AcquisitionResult] = []
    with ledger.exclusive():
        spent = ledger.spent(SCOPE).calls
        if spent + REQUESTS_PER_RUN > MAX_SCOPE_REQUESTS:
            raise SystemExit(
                f"refused: the {SCOPE} scope has used {spent} of {MAX_SCOPE_REQUESTS} requests"
            )
        pacer = Pacer()
        for query in QUERIES:
            result = acquire(used, pacer, query, credentials, now=datetime.now(UTC))
            ledger.append(_entry(query, result))
            results.append(result)
            if result.status is not AttemptStatus.SUCCEEDED:
                break  # a failed page is recorded; the next would only repeat it
        ledger.write_markdown()
    copies = [("adzuna", c) for r in results for c in r.copies]
    # Everything the worker would store (claims, URLs, excerpts) is scanned for either
    # credential's value, which Adzuna may echo in a landing link (review A M3).
    echoed = sum(
        1 for r in results for s in credentials if s.get_secret_value() in r.model_dump_json()
    )
    return {
        "status": "complete"
        if echoed == 0 and all(r.status is AttemptStatus.SUCCEEDED for r in results)
        else "failed",
        "results_holding_a_credential": echoed,
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
