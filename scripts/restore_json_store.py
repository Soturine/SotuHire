"""Restore one quarantined JSON/JSONL store from a validated local backup."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from modules.storage.json_recovery import json_store_health, restore_json_store

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", type=Path, help="Destination store in degraded state.")
    parser.add_argument("backup", type=Path, help="Known-good JSON or JSONL backup.")
    parser.add_argument("--jsonl", action="store_true", help="Validate as JSON Lines.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Restore the file; without this flag only validate and report health.",
    )
    args = parser.parse_args()
    if args.apply:
        restore_json_store(args.store, args.backup, json_lines=args.jsonl)
    else:
        content = args.backup.read_text(encoding="utf-8")
        if args.jsonl:
            for line in content.splitlines():
                if line.strip():
                    json.loads(line)
        else:
            json.loads(content)
    print(json_store_health(args.store).model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
