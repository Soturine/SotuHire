"""Aliases and synonyms used by the domain intelligence layer."""

from __future__ import annotations

import re
from dataclasses import dataclass

from modules.core.text_utils import normalize_text


@dataclass(frozen=True)
class AliasEntry:
    """Normalized representation of a known professional term."""

    normalized_name: str
    category: str
    domain: str
    confidence: float = 0.9


ALIASES: dict[str, AliasEntry] = {
    "js": AliasEntry("JavaScript", "hard_skill", "software_engineering"),
    "javascript": AliasEntry("JavaScript", "hard_skill", "software_engineering"),
    "reactjs": AliasEntry("React", "hard_skill", "software_engineering"),
    "react": AliasEntry("React", "hard_skill", "software_engineering"),
    "postgres": AliasEntry("PostgreSQL", "software", "data"),
    "postgresql": AliasEntry("PostgreSQL", "software", "data"),
    "coren": AliasEntry("COREN", "professional_license", "nursing", 0.95),
    "crp": AliasEntry("CRP", "professional_license", "psychology", 0.95),
    "crea": AliasEntry("CREA", "professional_license", "engineering", 0.95),
    "cau": AliasEntry("CAU", "professional_license", "architecture", 0.95),
    "cft": AliasEntry("CFT", "professional_license", "technical_course", 0.95),
    "oab": AliasEntry("OAB", "professional_license", "business", 0.9),
    "crc": AliasEntry("CRC", "professional_license", "finance", 0.9),
    "bncc": AliasEntry("BNCC", "regulation", "pedagogy", 0.9),
    "uti": AliasEntry("UTI", "other", "healthcare", 0.85),
    "autocad": AliasEntry("AutoCAD", "software", "civil_engineering", 0.9),
    "auto cad": AliasEntry("AutoCAD", "software", "civil_engineering", 0.9),
    "revit": AliasEntry("Revit", "software", "architecture", 0.9),
    "sketchup": AliasEntry("SketchUp", "software", "architecture", 0.9),
    "siem": AliasEntry("SIEM", "tool", "cybersecurity", 0.9),
    "soc": AliasEntry("SOC", "other", "cybersecurity", 0.85),
    "iso 27001": AliasEntry("ISO 27001", "regulation", "cybersecurity", 0.9),
    "lgpd": AliasEntry("LGPD", "regulation", "business", 0.8),
    "anvisa": AliasEntry("ANVISA", "regulation", "biomedical_engineering", 0.85),
    "nr 10": AliasEntry("NR-10", "regulation", "electrical_engineering", 0.85),
    "nr10": AliasEntry("NR-10", "regulation", "electrical_engineering", 0.85),
    "clp": AliasEntry("CLP", "equipment", "industrial", 0.85),
}


def find_aliases(text: str) -> dict[str, AliasEntry]:
    """Return aliases found in text keyed by the literal alias."""
    normalized = normalize_text(text)
    found: dict[str, AliasEntry] = {}
    for alias, entry in ALIASES.items():
        normalized_alias = normalize_text(alias)
        if re.search(rf"(?<!\w){re.escape(normalized_alias)}(?!\w)", normalized):
            found[alias] = entry
    return found


def normalize_alias(term: str) -> AliasEntry | None:
    """Resolve a single term to a known alias entry."""
    return ALIASES.get(normalize_text(term))
