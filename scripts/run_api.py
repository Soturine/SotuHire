"""Run the SotuHire FastAPI layer locally."""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    """Start uvicorn with env-backed local API settings."""
    bootstrap = os.getenv("SOTUHIRE_PAIRING_BOOTSTRAP", "").strip()
    if not bootstrap:
        bootstrap = secrets.token_urlsafe(32)
        os.environ["SOTUHIRE_PAIRING_BOOTSTRAP"] = bootstrap
        print(
            "Bootstrap local criado. Abra o frontend com o fragmento temporario: "
            f"http://localhost:5173/#sotuhire-pairing={bootstrap}"
        )
    from apps.api.config import ApiSettings

    settings = ApiSettings.from_env()
    uvicorn.run(
        "apps.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
