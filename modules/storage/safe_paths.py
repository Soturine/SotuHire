"""Explicit filesystem trust boundaries for server-managed local stores."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class UnsafeStorePath(ValueError):
    """Raised when a path escapes its declared local store root."""


def safe_component(value: str, *, label: str = "identificador") -> str:
    """Validate one portable filename component without separators or options."""
    if not _COMPONENT.fullmatch(value) or value in {".", ".."}:
        raise UnsafeStorePath(f"{label.capitalize()} de armazenamento invalido.")
    return value


def safe_relative(value: str) -> Path:
    """Parse a portable relative archive path and reject alternate separators."""
    if not value or "\\" in value or ":" in value or "\x00" in value:
        raise UnsafeStorePath("Caminho relativo de armazenamento invalido.")
    pure = PurePosixPath(value)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise UnsafeStorePath("Caminho relativo de armazenamento invalido.")
    return Path(*pure.parts)


def resolve_within(root: str | Path, relative: str | Path, *, allow_root: bool = False) -> Path:
    """Resolve a relative path under root, including symlink/junction escape checks."""
    trusted_root = Path(root).resolve()
    raw = Path(relative)
    if raw.is_absolute():
        raise UnsafeStorePath("Caminho absoluto externo nao e permitido.")
    portable = safe_relative(raw.as_posix())
    candidate = (trusted_root / portable).resolve()
    try:
        candidate.relative_to(trusted_root)
    except ValueError as exc:
        raise UnsafeStorePath("Caminho fora do armazenamento permitido.") from exc
    if candidate == trusted_root and not allow_root:
        raise UnsafeStorePath("O diretorio raiz nao pode ser usado como arquivo.")
    return candidate


def ensure_within(root: str | Path, candidate: str | Path) -> Path:
    """Validate an existing or prospective path against a trusted root."""
    trusted_root = Path(root).resolve()
    resolved = Path(candidate).resolve()
    try:
        resolved.relative_to(trusted_root)
    except ValueError as exc:
        raise UnsafeStorePath("Caminho fora do armazenamento permitido.") from exc
    return resolved


__all__ = [
    "UnsafeStorePath",
    "ensure_within",
    "resolve_within",
    "safe_component",
    "safe_relative",
]
