"""FastAPI application assembly (composition root for HTTP)."""

from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

from nessa.api import (
    routes_capability,
    routes_credentials,
    routes_discovery,
    routes_events,
    routes_export,
    routes_health,
    routes_interview,
    routes_profile,
    routes_reference,
    routes_research,
    routes_runs,
    routes_taxonomy,
    routes_workspaces,
)
from nessa.api.deps import ApiDependencies
from nessa.api.envelope import install_error_handlers
from nessa.api.guard import RequestGuard

API_TITLE = "Nessa local API"
API_VERSION = "1"


def _operation_id(route: APIRoute) -> str:
    # The handler's name (or its explicit `operation_id`) names the generated client's
    # function; FastAPI warns, and the tests fail, if two operations share one.
    return route.name


def _routes() -> FastAPI:
    """Every route and error handler, with no runtime dependency attached."""
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        docs_url=None,
        redoc_url=None,
        generate_unique_id_function=_operation_id,
    )
    install_error_handlers(app)
    for module in (
        routes_health,
        routes_workspaces,
        routes_profile,
        routes_credentials,
        routes_runs,
        routes_interview,
        routes_discovery,
        routes_research,
        routes_reference,
        routes_capability,
        routes_taxonomy,
        routes_events,
        routes_export,
    ):
        app.include_router(module.router)
    return app


def create_app(deps: ApiDependencies) -> FastAPI:
    app = _routes()
    app.state.deps = deps
    app.add_middleware(
        RequestGuard,
        allowed_hosts=deps.settings.allowed_hosts,
        allowed_origins=deps.settings.allowed_origins,
        client_networks=deps.client_networks,
    )
    return app


def openapi_document() -> dict[str, Any]:
    """The contract `/openapi.json` serves, built without configuration, database or keys,
    so the web app's TypeScript client is generated from it offline (Global Constraint 10)."""
    return _routes().openapi()
