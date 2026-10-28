"""The typed error envelope (spec section 18): stable code, message, retryability, stage and
correlation ID. Messages come from our code only; request input, provider text and exception
messages never appear, so an envelope cannot echo a key back."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from nessa.errors import ErrorCode, ErrorStage, NessaError

_log = logging.getLogger("nessa.api")

STATUS: dict[ErrorCode, int] = {
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.NOT_INVITED: 403,
    ErrorCode.ORIGIN_NOT_ALLOWED: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.HOST_NOT_ALLOWED: 400,
    ErrorCode.IDEMPOTENCY_KEY_REQUIRED: 400,
    ErrorCode.STALE_INPUT_VERSION: 409,
    ErrorCode.CREDENTIAL_EXISTS: 409,
    ErrorCode.BUDGET_EXCEEDED: 402,
    ErrorCode.FEATURE_NOT_IN_M0: 501,
    ErrorCode.STORE_UNAVAILABLE: 503,
    ErrorCode.AUTH_UNAVAILABLE: 503,
    ErrorCode.MODEL_UNAVAILABLE: 503,
    ErrorCode.INTERNAL_ERROR: 500,
}
DEFAULT_STATUS = 422


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str
    retryable: bool
    stage: ErrorStage
    correlation_id: str
    details: dict[str, str | int | list[str]] = {}


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorBody


ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    "4XX": {"model": ErrorEnvelope, "description": "Typed error envelope"},
    "5XX": {"model": ErrorEnvelope, "description": "Typed error envelope"},
}


def correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", "unknown"))


def envelope(error: NessaError, correlation: str) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorBody(
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            stage=error.stage,
            correlation_id=correlation,
            details=error.details,
        )
    )
    return JSONResponse(
        body.model_dump(mode="json"), status_code=STATUS.get(error.code, DEFAULT_STATUS)
    )


def _validation_details(error: RequestValidationError) -> list[str]:
    # Location and error type only: pydantic's default response would echo the input,
    # which for a credential request is the key itself.
    return [
        ".".join(str(part) for part in item.get("loc", ())) + f": {item.get('type', 'invalid')}"
        for item in error.errors()
    ][:20]


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NessaError)
    async def nessa_error(request: Request, error: NessaError) -> JSONResponse:
        return envelope(error, correlation_id(request))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        return envelope(
            NessaError(
                ErrorCode.VALIDATION_FAILED,
                "The request does not match the API contract.",
                stage=ErrorStage.REQUEST,
                details={"errors": _validation_details(error)},
            ),
            correlation_id(request),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        response = envelope(
            NessaError(ErrorCode.NOT_FOUND, "No such resource.", stage=ErrorStage.REQUEST),
            correlation_id(request),
        )
        response.status_code = error.status_code
        return response

    @app.exception_handler(Exception)
    async def unexpected(request: Request, error: Exception) -> JSONResponse:
        _log.error(
            "unexpected error",
            exc_info=error,
            extra={"correlation_id": correlation_id(request), "path": request.url.path},
        )
        return envelope(
            NessaError(
                ErrorCode.INTERNAL_ERROR,
                "Something went wrong on our side. Quote the correlation ID if you report it.",
                stage=ErrorStage.INTERNAL,
                retryable=True,
            ),
            correlation_id(request),
        )
