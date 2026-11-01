"""The shared words every module, the API, the database and exports use for state and mode.

The TypeScript client is generated from the OpenAPI schema, so these enums are the single
definition (Global Constraint 10). Do not restate their values elsewhere.
"""

from enum import StrEnum


class WorkState(StrEnum):
    """One state vocabulary (spec section 3, STATE-01). A failure is never an empty success."""

    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    BLOCKED_MISSING_INFORMATION = "blocked_missing_information"
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    STALE = "stale"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    FAILED = "failed"


class DataMode(StrEnum):
    """Recorded on every workspace and run (Global Constraint 5, plan section 2)."""

    DEMO = "demo"
    LIVE_ASSISTED = "live_assisted"
    LIVE_VACANCY = "live_vacancy"
