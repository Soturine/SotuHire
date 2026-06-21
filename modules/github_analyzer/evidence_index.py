"""Evidence indexing for repository-based claims."""

from __future__ import annotations

import re

from pydantic import Field

from modules.github_analyzer.dependency_graph import DependencyGraphSummary
from modules.github_analyzer.repository_models import (
    EvidenceType,
    RepositoryAnalyzerModel,
    RepositoryDetectedSignals,
    RepositoryMetadata,
    SelectedRepositoryFile,
)

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]{12,}['\"]"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
)


class EvidenceItem(RepositoryAnalyzerModel):
    """A single evidence-backed claim about a repository."""

    claim: str
    source_file: str = ""
    evidence_type: EvidenceType
    confidence: float = Field(ge=0, le=1)


def build_evidence_index(
    *,
    metadata: RepositoryMetadata,
    signals: RepositoryDetectedSignals,
    selected_files: list[SelectedRepositoryFile],
    dependency_graph: DependencyGraphSummary,
) -> list[EvidenceItem]:
    """Create evidence items from metadata, tree signals, sampled files and imports."""
    evidence: list[EvidenceItem] = [
        EvidenceItem(
            claim=f"Repository {metadata.identity.owner}/{metadata.identity.name} was resolved from GitHub metadata.",
            evidence_type="metadata",
            confidence=0.95,
        )
    ]
    evidence.extend(_signal_evidence(signals))
    evidence.extend(_file_evidence(selected_files))
    evidence.extend(_dependency_evidence(dependency_graph))
    evidence.extend(_secret_evidence(selected_files))
    return consolidate_evidence(evidence)


def consolidate_evidence(items: list[EvidenceItem]) -> list[EvidenceItem]:
    """Deduplicate evidence while keeping stronger confidence first."""
    deduped: dict[tuple[str, str, EvidenceType], EvidenceItem] = {}
    for item in sorted(items, key=lambda evidence: evidence.confidence, reverse=True):
        key = (item.claim, item.source_file, item.evidence_type)
        deduped.setdefault(key, item)
    return list(deduped.values())


def has_critical_secret(evidence: list[EvidenceItem]) -> bool:
    """Return whether evidence contains a likely exposed secret."""
    return any("secret" in item.claim.casefold() and item.confidence >= 0.8 for item in evidence)


def _signal_evidence(signals: RepositoryDetectedSignals) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    if signals.has_readme and signals.doc_paths:
        items.append(
            _presence("README/documentation is present.", signals.doc_paths[0], "readme", 0.9)
        )
    for path in signals.test_paths[:6]:
        items.append(
            _presence("Tests are present in the repository tree.", path, "file_presence", 0.84)
        )
    for path in signals.workflow_paths[:6]:
        items.append(_presence("CI workflow is present.", path, "workflow", 0.9))
    for path in signals.manifest_paths[:8]:
        items.append(
            _presence("Project manifest or build config is present.", path, "config", 0.82)
        )
    for path in signals.security_paths[:6]:
        items.append(_presence("Security-related configuration is present.", path, "config", 0.78))
    if signals.tree_truncated:
        items.append(
            EvidenceItem(
                claim="GitHub reported the repository tree as truncated.",
                evidence_type="tree",
                confidence=0.95,
            )
        )
    return items


def _file_evidence(files: list[SelectedRepositoryFile]) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for file in files:
        if not file.fetched:
            items.append(
                _presence("File exists in tree but content was not read.", file.path, "tree", 0.74)
            )
            continue
        confidence = 0.86 if file.content.strip() else 0.55
        items.append(
            EvidenceItem(
                claim=f"File content was read for analysis ({file.reason_selected}).",
                source_file=file.path,
                evidence_type="code_content" if file.reason_selected == "source" else "config",
                confidence=confidence,
            )
        )
        if file.truncated:
            items.append(
                EvidenceItem(
                    claim="File content was truncated before analysis.",
                    source_file=file.path,
                    evidence_type="code_content",
                    confidence=0.9,
                )
            )
    return items


def _dependency_evidence(graph: DependencyGraphSummary) -> list[EvidenceItem]:
    return [
        EvidenceItem(
            claim="File appears central in the sampled dependency graph.",
            source_file=path,
            evidence_type="dependency",
            confidence=0.72,
        )
        for path in graph.central_files[:10]
    ]


def _secret_evidence(files: list[SelectedRepositoryFile]) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for file in files:
        if not file.fetched or not file.content:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(file.content):
                items.append(
                    EvidenceItem(
                        claim="Possible exposed secret detected in sampled content.",
                        source_file=file.path,
                        evidence_type="code_content",
                        confidence=0.88,
                    )
                )
                break
    return items


def _presence(
    claim: str, source_file: str, evidence_type: EvidenceType, confidence: float
) -> EvidenceItem:
    return EvidenceItem(
        claim=claim,
        source_file=source_file,
        evidence_type=evidence_type,
        confidence=confidence,
    )
