"""Installation-bound authentication and short-lived localhost pairing."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

DEFAULT_PAIRING_TTL_SECONDS = 90
DEFAULT_SESSION_TTL_SECONDS = 12 * 60 * 60


class PairingError(ValueError):
    """A pairing proof is invalid, expired, or already consumed."""


@dataclass(frozen=True)
class PairingChallenge:
    challenge_id: str
    proof: str
    expires_at: float


@dataclass(frozen=True)
class SessionCredentials:
    session_token: str
    csrf_token: str
    expires_at: float


@dataclass(frozen=True)
class _PendingChallenge:
    proof_digest: str
    origin: str
    client_kind: str
    expires_at: float


@dataclass(frozen=True)
class _LocalSession:
    csrf_digest: str
    origin: str
    client_kind: str
    expires_at: float


class InstallationTokenStore:
    """Persist one random local token atomically, never in logs or responses."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def get_or_create(self) -> str:
        existing = self._read()
        if existing:
            return existing
        token = secrets.token_urlsafe(48)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        payload = json.dumps({"format": 1, "installation_token": token}) + "\n"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            with suppress(OSError):
                self.path.chmod(0o600)
        finally:
            temporary.unlink(missing_ok=True)
        return token

    def _read(self) -> str:
        if not self.path.is_file():
            return ""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            raise RuntimeError("O armazenamento de autenticação local está corrompido.") from None
        token = payload.get("installation_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or len(token) < 32:
            raise RuntimeError("O armazenamento de autenticação local é inválido.")
        return token


class LocalAuthManager:
    """Authenticate native clients and exchange one-use proofs for local sessions."""

    def __init__(
        self,
        *,
        installation_token: str = "",
        pairing_bootstrap: str = "",
        token_path: str | Path = "data/security/local-auth.json",
        pairing_ttl_seconds: int = DEFAULT_PAIRING_TTL_SECONDS,
        session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._explicit_token = installation_token.strip()
        self._pairing_bootstrap_digest = (
            _digest(pairing_bootstrap.strip()) if pairing_bootstrap.strip() else ""
        )
        self._store = InstallationTokenStore(token_path)
        self._installation_token = ""
        self.pairing_ttl_seconds = max(10, pairing_ttl_seconds)
        self.session_ttl_seconds = max(60, session_ttl_seconds)
        self._clock = clock
        self._pending: dict[str, _PendingChallenge] = {}
        self._sessions: dict[str, _LocalSession] = {}
        self._used: dict[str, float] = {}
        self._lock = threading.Lock()

    def authenticate_installation(self, provided: str) -> bool:
        if not provided:
            return False
        return hmac.compare_digest(provided, self._get_installation_token())

    def start_pairing(
        self,
        *,
        origin: str,
        client_kind: str,
        bootstrap_proof: str = "",
    ) -> PairingChallenge:
        if not origin:
            raise PairingError("O pairing exige uma origem local explícita.")
        if self._pairing_bootstrap_digest and not (
            bootstrap_proof
            and hmac.compare_digest(
                self._pairing_bootstrap_digest,
                _digest(bootstrap_proof),
            )
        ):
            raise PairingError("O pairing exige o bootstrap local desta instalacao.")
        now = self._clock()
        challenge_id = uuid4().hex
        proof = secrets.token_urlsafe(24)
        expires_at = now + self.pairing_ttl_seconds
        with self._lock:
            self._prune(now)
            if len(self._pending) >= 16:
                oldest = min(self._pending, key=lambda key: self._pending[key].expires_at)
                self._pending.pop(oldest, None)
            self._pending[challenge_id] = _PendingChallenge(
                proof_digest=_digest(proof),
                origin=origin,
                client_kind=client_kind,
                expires_at=expires_at,
            )
        return PairingChallenge(challenge_id=challenge_id, proof=proof, expires_at=expires_at)

    def complete_pairing(
        self,
        *,
        challenge_id: str,
        proof: str,
        origin: str,
        client_kind: str,
    ) -> SessionCredentials:
        now = self._clock()
        with self._lock:
            self._prune(now)
            if challenge_id in self._used:
                raise PairingError("O pairing já foi utilizado.")
            pending = self._pending.pop(challenge_id, None)
            if pending is None:
                raise PairingError("O pairing expirou ou não existe.")
            self._used[challenge_id] = now + self.pairing_ttl_seconds
            valid = (
                pending.expires_at >= now
                and hmac.compare_digest(pending.proof_digest, _digest(proof))
                and hmac.compare_digest(pending.origin, origin)
                and hmac.compare_digest(pending.client_kind, client_kind)
            )
            if not valid:
                raise PairingError("A prova de pairing é inválida.")
            session_token = secrets.token_urlsafe(48)
            csrf_token = secrets.token_urlsafe(32)
            expires_at = now + self.session_ttl_seconds
            self._sessions[_digest(session_token)] = _LocalSession(
                csrf_digest=_digest(csrf_token),
                origin=origin,
                client_kind=client_kind,
                expires_at=expires_at,
            )
        return SessionCredentials(
            session_token=session_token,
            csrf_token=csrf_token,
            expires_at=expires_at,
        )

    def authenticate_session(
        self,
        session_token: str,
        *,
        origin: str,
        csrf_token: str = "",
        require_csrf: bool = False,
    ) -> bool:
        if not session_token:
            return False
        now = self._clock()
        with self._lock:
            self._prune(now)
            session = self._sessions.get(_digest(session_token))
            if session is None or not hmac.compare_digest(session.origin, origin):
                return False
            return not require_csrf or (
                bool(csrf_token) and hmac.compare_digest(session.csrf_digest, _digest(csrf_token))
            )

    def revoke_session(self, session_token: str) -> None:
        if session_token:
            with self._lock:
                self._sessions.pop(_digest(session_token), None)

    def rotate_csrf(self, session_token: str, *, origin: str) -> str:
        """Rotate CSRF material for an authenticated same-origin browser session."""
        if not session_token:
            raise PairingError("A sessao local nao esta autenticada.")
        now = self._clock()
        session_digest = _digest(session_token)
        with self._lock:
            self._prune(now)
            session = self._sessions.get(session_digest)
            if session is None or not hmac.compare_digest(session.origin, origin):
                raise PairingError("A sessao local expirou ou pertence a outra origem.")
            csrf_token = secrets.token_urlsafe(32)
            self._sessions[session_digest] = _LocalSession(
                csrf_digest=_digest(csrf_token),
                origin=session.origin,
                client_kind=session.client_kind,
                expires_at=session.expires_at,
            )
        return csrf_token

    def public_status(self) -> dict[str, object]:
        now = self._clock()
        with self._lock:
            self._prune(now)
            return {
                "pairing_ttl_seconds": self.pairing_ttl_seconds,
                "session_ttl_seconds": self.session_ttl_seconds,
                "active_sessions": len(self._sessions),
            }

    def _get_installation_token(self) -> str:
        if self._explicit_token:
            return self._explicit_token
        if not self._installation_token:
            self._installation_token = self._store.get_or_create()
        return self._installation_token

    def _prune(self, now: float) -> None:
        self._pending = {
            key: value for key, value in self._pending.items() if value.expires_at >= now
        }
        self._sessions = {
            key: value for key, value in self._sessions.items() if value.expires_at >= now
        }
        self._used = {
            key: expires_at for key, expires_at in self._used.items() if expires_at >= now
        }


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = [
    "InstallationTokenStore",
    "LocalAuthManager",
    "PairingChallenge",
    "PairingError",
    "SessionCredentials",
]
