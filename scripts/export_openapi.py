"""Write the Local API's OpenAPI document where the web client's contract test reads it.

    python scripts/export_openapi.py            # refresh apps/web/tests/contract/openapi.json
    python scripts/export_openapi.py --check    # exit 1 if the committed copy is stale

The web test `src/lib/api/contract.test.ts` sends the client's real request bodies through this
document: every request model forbids unknown fields, so a field the client adds (SH-NEW-032) is a
422 in API mode that sample mode never shows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "apps" / "web" / "tests" / "contract" / "openapi.json"


def render() -> str:
    sys.path.insert(0, str(ROOT))
    from apps.api.main import app

    return json.dumps(app.openapi(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != text:
            print(f"{TARGET.relative_to(ROOT)} is stale; run scripts/export_openapi.py")
            return 1
        return 0
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
