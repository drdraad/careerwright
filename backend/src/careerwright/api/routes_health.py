"""Liveness and readiness. No authentication, no data: only whether the API can serve."""

from fastapi import APIRouter

from careerwright.api.deps import Deps
from careerwright.api.schemas import Health
from careerwright.db import ping

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=Health)
def healthz() -> Health:
    return Health(status="ok")


@router.get("/readyz", response_model=Health)
def readyz(deps: Deps) -> Health:
    ping(deps.engine)
    return Health(status="ready")
