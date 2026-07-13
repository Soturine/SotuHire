"""Run read-only checks over SQLite and legacy SotuHire data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from modules.storage.health import check_data_health

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", help="Override the local data directory.")
    parser.add_argument("--database", help="Override the SQLite database path.")
    args = parser.parse_args()
    report = check_data_health(data_dir=args.data_dir, database_path=args.database)
    print(report.model_dump_json(indent=2))
    return 0 if report.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
