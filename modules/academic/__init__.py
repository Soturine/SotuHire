"""Academic and Lattes evidence extraction helpers."""

from .lattes_models import (
    LattesConfirmResult,
    LattesImportInput,
    LattesImportResult,
)
from .lattes_parser import parse_lattes_text
from .lattes_service import LattesService

__all__ = [
    "LattesConfirmResult",
    "LattesImportInput",
    "LattesImportResult",
    "LattesService",
    "parse_lattes_text",
]
