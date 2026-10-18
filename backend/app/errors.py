"""Consistent error envelope and exception handlers.

Error responses never contain secrets, raw sensitive input, or stack
traces. A request_id correlates each error with redacted server logs.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging import redact

_logger = logging.getLogger("foundershield")

_STATUS_CODE_MAP = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "provider_unavailable",
}


def _envelope(code: str, message: str, request_id: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = str(uuid.uuid4())
    code = _STATUS_CODE_MAP.get(exc.status_code, "error")
    message = exc.detail if isinstance(exc.detail, str) else code
    return _envelope(code, redact(message), request_id, exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = str(uuid.uuid4())
    # Do not echo raw submitted values back to the client.
    return _envelope(
        "validation_error",
        "Request validation failed.",
        request_id,
        422,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid.uuid4())
    # Log redacted detail server-side; never leak internals to the client.
    _logger.error("unhandled_exception request_id=%s detail=%s", request_id, redact(str(exc)))
    return _envelope(
        "internal_error",
        "An unexpected error occurred.",
        request_id,
        500,
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
