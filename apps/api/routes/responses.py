"""Response helpers for route handlers."""

from __future__ import annotations

from typing import TypeVar

from apps.api.schemas.common import ApiEnvelope

DataT = TypeVar("DataT")


def ok(
    data: DataT, *, warnings: list[str] | None = None, request_id: str = ""
) -> ApiEnvelope[DataT]:
    """Wrap a route payload in the v1 success envelope."""
    return ApiEnvelope(data=data, warnings=warnings or [], request_id=request_id)
