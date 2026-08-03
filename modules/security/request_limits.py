"""Bounded request validation for loopback HTTP services."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class RequestLimitError(ValueError):
    def __init__(self, code: str, message: str, *, status_code: int = 413) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class RequestPolicy:
    max_body_bytes: int = 1_048_576
    max_batch_items: int = 100
    max_json_depth: int = 16
    timeout_seconds: float = 30.0
    rate_limit_requests: int = 120
    rate_limit_window_seconds: float = 60.0

    def validate_content_length(self, raw_value: str) -> None:
        if not raw_value:
            return
        try:
            content_length = int(raw_value)
        except ValueError:
            raise RequestLimitError(
                "invalid_content_length", "Content-Length inválido.", status_code=400
            ) from None
        if content_length < 0 or content_length > self.max_body_bytes:
            raise RequestLimitError("body_too_large", "O corpo da requisição excede o limite.")

    def validate_json(self, payload: Any) -> None:
        depth, largest_list = _json_shape(payload, stop_depth=self.max_json_depth)
        if depth > self.max_json_depth:
            raise RequestLimitError(
                "json_too_deep", "O JSON excede a profundidade permitida.", status_code=422
            )
        if largest_list > self.max_batch_items:
            raise RequestLimitError(
                "batch_too_large", "O lote excede a quantidade permitida.", status_code=422
            )


class LocalRateLimiter:
    """Small in-memory sliding window limiter for abuse containment."""

    def __init__(
        self,
        *,
        requests: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.requests = max(1, requests)
        self.window_seconds = max(1.0, window_seconds)
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self._clock()
        threshold = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= threshold:
                events.popleft()
            if len(events) >= self.requests:
                return False
            events.append(now)
            if len(self._events) > 1_000:
                self._events = defaultdict(
                    deque, {item: values for item, values in self._events.items() if values}
                )
            return True


def _json_shape(value: Any, *, stop_depth: int) -> tuple[int, int]:
    """Inspect untrusted JSON iteratively so nesting cannot exhaust Python recursion."""
    maximum_depth = 1
    largest_list = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        maximum_depth = max(maximum_depth, depth)
        if maximum_depth > stop_depth:
            return maximum_depth, largest_list
        if isinstance(current, list):
            largest_list = max(largest_list, len(current))
            stack.extend((item, depth + 1) for item in current)
        elif isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
    return maximum_depth, largest_list


__all__ = ["LocalRateLimiter", "RequestLimitError", "RequestPolicy"]
