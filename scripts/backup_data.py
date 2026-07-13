"""Create a secret-safe SotuHire data backup or portable export."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from modules.storage.backup import create_backup

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", help="Override the local data directory.")
    parser.add_argument("--output", help="Archive destination.")
    parser.add_argument("--export", action="store_true", help="Use the portable export name.")
    args = parser.parse_args()
    result = create_backup(
        data_dir=args.data_dir,
        destination=args.output,
        kind="export" if args.export else "backup",
    )
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
