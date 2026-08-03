"""FastAPI application factory for the SotuHire frontend API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from modules.security import LocalAuthManager, RequestPolicy

from apps.api.config import ApiSettings
from apps.api.middleware import LocalSecurityMiddleware
from apps.api.routes import (
    ai_quality,
    analysis,
    application_lab,
    data,
    extension,
    health,
    local_security,
    notifications,
    outcomes,
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
    app.state.local_auth = LocalAuthManager(
        installation_token=resolved.installation_token,
        token_path=resolved.auth_path,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-SotuHire-Token",
            "X-SotuHire-CSRF",
            "X-Idempotency-Key",
            "X-Request-ID",
        ],
    )
    app.add_middleware(
        LocalSecurityMiddleware,
        auth=app.state.local_auth,
        policy=RequestPolicy(
            max_body_bytes=resolved.max_body_bytes,
            max_batch_items=resolved.max_batch_items,
            max_json_depth=resolved.max_json_depth,
            timeout_seconds=resolved.request_timeout_seconds,
            rate_limit_requests=resolved.rate_limit_requests,
            rate_limit_window_seconds=resolved.rate_limit_window_seconds,
        ),
        allowed_origins=resolved.allowed_origins,
        allowed_hosts=resolved.allowed_hosts,
    )
    app.include_router(health.router)
    app.include_router(local_security.router)
    app.include_router(data.router)
    app.include_router(analysis.router)
    app.include_router(application_lab.application_lab_router)
    app.include_router(application_lab.resume_studio_router)
    app.include_router(ai_quality.router)
    app.include_router(outcomes.router)
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
