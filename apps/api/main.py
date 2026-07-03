"""FastAPI application factory for the SotuHire frontend API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.config import ApiSettings
from apps.api.routes import (
    analysis,
    extension,
    health,
    notifications,
    profile,
    public_exams,
    radar,
    sources,
    tracker,
)
from apps.api.routes import settings as settings_routes
from apps.api.schemas.common import ApiError, ErrorEnvelope


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Create the FastAPI app with local-first defaults."""
    resolved = settings or ApiSettings.from_env()
    app = FastAPI(
        title="SotuHire Local Frontend API",
        version=resolved.version,
        description="Local-first API layer for SotuHire frontend clients.",
    )
    app.state.settings = resolved
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(health.router)
    app.include_router(analysis.router)
    app.include_router(tracker.router)
    app.include_router(settings_routes.router)
    app.include_router(profile.router)
    app.include_router(public_exams.router)
    app.include_router(sources.router)
    app.include_router(radar.router)
    app.include_router(notifications.router)
    app.include_router(extension.router)
    _install_exception_handlers(app)
    return app


def _install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(
            code="http_error",
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=_request_id(request),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            code="invalid_payload",
            message="Payload invalido para o contrato da API.",
            status_code=422,
            details={"errors": exc.errors()},
            request_id=_request_id(request),
        )


def _error_response(
    *,
    code: str,
    message: str,
    status_code: int,
    request_id: str = "",
    details: dict[str, object] | None = None,
) -> JSONResponse:
    payload = ErrorEnvelope(
        error=ApiError(code=code, message=message, details=details or {}),
        request_id=request_id,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def _request_id(request: Request) -> str:
    return request.headers.get("x-request-id", "")


app = create_app()
