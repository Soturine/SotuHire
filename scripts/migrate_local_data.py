"""Inspect, apply or verify migration of legacy local stores."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from modules.storage.legacy_migration import migrate_local_data

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Inspect without writing anything.")
    mode.add_argument("--apply", action="store_true", help="Backup and migrate transactionally.")
    mode.add_argument("--verify", action="store_true", help="Verify schema and relations.")
    parser.add_argument("--data-dir", help="Override the local data directory.")
    parser.add_argument("--database", help="Override the SQLite database path.")
    args = parser.parse_args()
    selected = "apply" if args.apply else "verify" if args.verify else "dry-run"
    report = migrate_local_data(
        mode=selected,
        data_dir=args.data_dir,
        database_path=args.database,
    )
    print(report.model_dump_json(indent=2))
    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
