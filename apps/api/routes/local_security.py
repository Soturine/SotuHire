"""Pairing endpoints for the localhost frontend session."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from modules.security import LocalAuthManager, PairingError
from pydantic import BaseModel, ConfigDict, Field

from apps.api.middleware.local_security import SESSION_COOKIE
from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api/v1/security", tags=["local-security"])


class PairingStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_kind: Literal["web"] = "web"
    client_name: str = Field(default="SotuHire Web", min_length=1, max_length=80)


class PairingCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(min_length=16, max_length=64)
    proof: str = Field(min_length=16, max_length=128)
    client_kind: Literal["web"] = "web"


def _manager(request: Request) -> LocalAuthManager:
    return request.app.state.local_auth


@router.post("/pairing/start", response_model=ApiEnvelope[dict[str, object]])
def start_pairing(
    payload: PairingStartRequest, request: Request
) -> ApiEnvelope[dict[str, object]]:
    del payload.client_name
    origin = request.headers.get("origin", "")
    try:
        challenge = _manager(request).start_pairing(
            origin=origin, client_kind=payload.client_kind
        )
    except PairingError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    return ok(
        {
            "challenge_id": challenge.challenge_id,
            "proof": challenge.proof,
            "expires_in_seconds": _manager(request).pairing_ttl_seconds,
        }
    )


@router.post("/pairing/complete", response_model=ApiEnvelope[dict[str, object]])
def complete_pairing(
    payload: PairingCompleteRequest, request: Request, response: Response
) -> ApiEnvelope[dict[str, object]]:
    origin = request.headers.get("origin", "")
    try:
        credentials = _manager(request).complete_pairing(
            challenge_id=payload.challenge_id,
            proof=payload.proof,
            origin=origin,
            client_kind=payload.client_kind,
        )
    except PairingError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from None
    response.set_cookie(
        SESSION_COOKIE,
        credentials.session_token,
        httponly=True,
        secure=False,
        samesite="strict",
        path="/api",
        max_age=_manager(request).session_ttl_seconds,
    )
    response.headers["Cache-Control"] = "no-store"
    return ok(
        {
            "paired": True,
            "csrf_token": credentials.csrf_token,
            "expires_in_seconds": _manager(request).session_ttl_seconds,
        }
    )


@router.get("/status", response_model=ApiEnvelope[dict[str, object]])
def pairing_status(request: Request) -> ApiEnvelope[dict[str, object]]:
    return ok({"paired": True, **_manager(request).public_status()})


__all__ = ["router"]
