"""FastAPI application assembly (composition root for HTTP)."""

from fastapi import FastAPI

from nessa.api import (
    routes_events,
    routes_export,
    routes_health,
    routes_profile,
    routes_workspaces,
)
from nessa.api.deps import ApiDependencies
from nessa.api.envelope import install_error_handlers
from nessa.api.guard import RequestGuard

API_TITLE = "Nessa local API"
API_VERSION = "1"


def create_app(deps: ApiDependencies) -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION, docs_url=None, redoc_url=None)
    app.state.deps = deps
    install_error_handlers(app)
    for module in (routes_health, routes_workspaces, routes_profile, routes_events, routes_export):
        app.include_router(module.router)
    app.add_middleware(
        RequestGuard,
        allowed_hosts=deps.settings.allowed_hosts,
        allowed_origins=deps.settings.allowed_origins,
    )
    return app
