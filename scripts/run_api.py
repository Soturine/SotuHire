"""Run the SotuHire FastAPI layer locally."""

from __future__ import annotations

import uvicorn
from apps.api.config import ApiSettings


def main() -> None:
    """Start uvicorn with env-backed local API settings."""
    settings = ApiSettings.from_env()
    uvicorn.run(
        "apps.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
