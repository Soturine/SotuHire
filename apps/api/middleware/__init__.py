"""HTTP middleware used by the local frontend API."""

from .local_security import LocalSecurityMiddleware

__all__ = ["LocalSecurityMiddleware"]
