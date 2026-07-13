"""Repository interfaces and local persistence adapters."""

from .base import Entity, EntityRepository
from .json_repository import JsonlRepository, JsonRepository
from .sqlite_repository import SqliteRepository

__all__ = [
    "Entity",
    "EntityRepository",
    "JsonRepository",
    "JsonlRepository",
    "SqliteRepository",
]
