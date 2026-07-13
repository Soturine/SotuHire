"""MkDocs build environment settings for deterministic strict builds."""

from __future__ import annotations

import os

# Material 9.7 emits an upstream informational warning about the unrelated
# MkDocs 2 project. Strict mode should continue to fail for SotuHire content,
# links and configuration warnings, not for this vendor announcement.
os.environ.setdefault("NO_MKDOCS_2_WARNING", "true")
