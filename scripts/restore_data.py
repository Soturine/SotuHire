"""Validate or restore a checksummed SotuHire data archive."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from modules.storage.backup import restore_backup

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Backup ZIP to validate or restore.")
    parser.add_argument("--destination", help="Override the local data directory.")
    parser.add_argument(
        "--apply", action="store_true", help="Restore after validation (default is dry-run)."
    )
    args = parser.parse_args()
    result = restore_backup(
        args.archive,
        destination=args.destination,
        dry_run=not args.apply,
    )
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
