"""Evidence collection for Match Engine 2."""

from __future__ import annotations

from collections.abc import Iterable

from modules.ai.schemas.common import CredentialSignal, LanguageSignal
from modules.ai.schemas.resume_extraction import (
    EducationEntry,
    ExtractedSkill,
    ResumeExtractionOutput,
)
from modules.github_analyzer.schemas import GitHubAnalyzerReport, SkillEvidence
from modules.matching.models import (
    CandidateEvidence,
    EvidenceSource,
    EvidenceStrength,
    RequirementCategory,
)
from modules.matching.requirement_matcher import evidence_from_text, normalize_requirement
from modules.portfolio.schemas import ProjectAnalysisReport


def collect_resume_evidence(resume: ResumeExtractionOutput | None) -> list[CandidateEvidence]:
    """Collect evidence from v0.10 structured resume extraction."""
    if resume is None:
        return []
    evidence: list[CandidateEvidence] = []
    for skill in [
        *resume.skills,
        *resume.tools,
        *resume.softwares,
        *resume.equipment,
    ]:
        evidence.append(_skill_evidence(skill))
    for credential in [*resume.certifications, *resume.professional_licenses]:
        evidence.append(_credential_evidence(credential))
    for language in resume.languages:
        evidence.append(_language_evidence(language))
    for education in resume.education:
        evidence.append(_education_evidence(education))
    for experience in resume.experiences:
        for item in [experience.title, experience.domain, *experience.tools_or_methods]:
            evidence.extend(
                evidence_from_text(item, source="resume", confidence=experience.confidence)
            )
    for project in resume.projects:
        for item in [project.name, *project.technologies_or_methods]:
            evidence.extend(
                evidence_from_text(item, source="resume", confidence=project.confidence)
            )
    return _dedupe_evidence(evidence)


def collect_github_evidence(report: GitHubAnalyzerReport | None) -> list[CandidateEvidence]:
    """Collect evidence from GitHub Analyzer 2 output."""
    if report is None:
        return []
    evidence: list[CandidateEvidence] = []
    for skill in report.portfolio_value.skills_demonstrated:
        evidence.append(_github_skill_evidence(skill))
    for technology in [
        *report.tech_stack.languages,
        *report.tech_stack.frameworks,
        *report.tech_stack.libraries,
        *report.tech_stack.tools,
        *report.tech_stack.databases,
        *report.tech_stack.devops,
        *report.tech_stack.testing_tools,
    ]:
        requirement = normalize_requirement(technology)
        evidence.append(
            CandidateEvidence(
                skill=technology,
                normalized_name=requirement.normalized_name,
                category=requirement.category,
                evidence_source="github",
                evidence_text=f"Detectado no GitHub Analyzer 2: {technology}",
                evidence_file=",".join(report.files_sampled[:5]),
                strength="medium",
                confidence=max(report.scores.confidence_score, 0.55),
            )
        )
    return _dedupe_evidence(evidence)


def collect_portfolio_evidence(report: ProjectAnalysisReport | None) -> list[CandidateEvidence]:
    """Collect evidence from the legacy portfolio/project report."""
    if report is None:
        return []
    evidence: list[CandidateEvidence] = []
    for keyword in [*report.stack, *report.technical_keywords]:
        requirement = normalize_requirement(keyword)
        evidence.append(
            CandidateEvidence(
                skill=keyword,
                normalized_name=requirement.normalized_name,
                category=requirement.category,
                evidence_source="portfolio",
                evidence_text=report.summary,
                evidence_file=",".join(report.files_sampled[:5]),
                strength="medium" if report.overall_score >= 55 else "weak",
                confidence=min(0.9, max(0.35, report.overall_score / 100)),
            )
        )
    return _dedupe_evidence(evidence)


def collect_text_evidence(
    text_items: Iterable[str],
    *,
    source: EvidenceSource = "memory",
    category: RequirementCategory = "other",
) -> list[CandidateEvidence]:
    """Collect lightweight evidence from memory/profile/manual text snippets."""
    evidence: list[CandidateEvidence] = []
    for text in text_items:
        evidence.extend(evidence_from_text(text, source=source, category=category))
    return _dedupe_evidence(evidence)


def combine_evidence(*groups: list[CandidateEvidence]) -> list[CandidateEvidence]:
    """Merge evidence groups with stable deduplication."""
    merged: list[CandidateEvidence] = []
    for group in groups:
        merged.extend(group)
    return _dedupe_evidence(merged)


def _skill_evidence(skill: ExtractedSkill) -> CandidateEvidence:
    requirement = normalize_requirement(
        skill.normalized_name or skill.name, category=skill.category
    )
    return CandidateEvidence(
        skill=skill.name,
        normalized_name=requirement.normalized_name,
        category=requirement.category,
        evidence_source="resume",
        evidence_text="; ".join(skill.evidence),
        strength=_strength(skill.confidence, bool(skill.evidence)),
        confidence=skill.confidence,
    )


def _credential_evidence(credential: CredentialSignal) -> CandidateEvidence:
    category: RequirementCategory = (
        "professional_license" if credential.type == "professional_license" else "certification"
    )
    requirement = normalize_requirement(credential.name, category=category)
    return CandidateEvidence(
        skill=credential.name,
        normalized_name=requirement.normalized_name,
        category=requirement.category,
        evidence_source="resume",
        evidence_text="; ".join(credential.evidence),
        strength=_strength(credential.confidence, bool(credential.evidence)),
        confidence=credential.confidence,
    )


def _language_evidence(language: LanguageSignal) -> CandidateEvidence:
    requirement = normalize_requirement(language.language, category="language")
    return CandidateEvidence(
        skill=language.language,
        normalized_name=requirement.normalized_name,
        category="language",
        evidence_source="resume",
        evidence_text="; ".join(language.evidence),
        strength=_strength(language.confidence, bool(language.evidence)),
        confidence=language.confidence,
    )


def _education_evidence(education: EducationEntry) -> CandidateEvidence:
    requirement = normalize_requirement(education.course, category="education")
    return CandidateEvidence(
        skill=education.course,
        normalized_name=requirement.normalized_name,
        category="education",
        evidence_source="resume",
        evidence_text="; ".join([education.course, education.institution, *education.evidence]),
        strength=_strength(education.confidence, bool(education.evidence)),
        confidence=education.confidence,
    )


def _github_skill_evidence(skill: SkillEvidence) -> CandidateEvidence:
    requirement = normalize_requirement(skill.skill, category=skill.category)
    return CandidateEvidence(
        skill=skill.skill,
        normalized_name=requirement.normalized_name,
        category=requirement.category,
        evidence_source="github",
        evidence_text=f"GitHub evidence: {skill.skill}",
        evidence_file=",".join(skill.evidence_files[:5]),
        strength=_strength(skill.confidence, bool(skill.evidence_files)),
        confidence=skill.confidence,
    )


def _strength(confidence: float, has_explicit_evidence: bool) -> EvidenceStrength:
    if confidence >= 0.9 and has_explicit_evidence:
        return "verified"
    if confidence >= 0.75:
        return "strong"
    if confidence >= 0.5:
        return "medium"
    if confidence > 0:
        return "weak"
    return "unclear"


def _dedupe_evidence(items: list[CandidateEvidence]) -> list[CandidateEvidence]:
    deduped: dict[tuple[str, str, str], CandidateEvidence] = {}
    for item in sorted(items, key=lambda evidence: evidence.confidence, reverse=True):
        key = (
            item.normalized_name.casefold(),
            item.category,
            item.evidence_source,
        )
        deduped.setdefault(key, item)
    return list(deduped.values())
