"""Keep the test process isolated from a developer's local-first data directory."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

_TEST_DATA_DIR = Path.cwd() / ".pytest_cache" / "isolated-data" / uuid4().hex
os.environ.setdefault("SOTUHIRE_DATA_DIR", str(_TEST_DATA_DIR))
