"""Pure local analysis pipeline for the guided Application Lab."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass

from modules.ai.structured_job_extractor import extract_structured_job_local
from modules.ai.structured_resume_extractor import extract_structured_resume_local
from modules.analyzer.job_analyzer import job_analysis_from_match_v2
from modules.application_lab.export import resume_plain_text
from modules.application_lab.models import (
    ApplicationAtsAnalysis,
    ApplicationLabSession,
    ApplicationReadinessReport,
    MasterResume,
)
from modules.application_lab.readiness import build_readiness_report
from modules.ats.ats_score import analyze_ats_issues, calculate_simple_ats_score
from modules.context import (
    CareerContext,
    CareerContextEvidence,
    CareerContextPurpose,
    EvidenceReviewStatus,
    EvidenceScope,
)
from modules.core.dependency_graph import DependencyFingerprint, fingerprint_dependencies
from modules.core.text_utils import extract_keywords
from modules.matching.engine import analyze_match_v2
from modules.matching.models import MatchResultV2
from modules.resume_tailor.tailor_rules import build_safe_tailor_output
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.storage.snapshots import JobSnapshot


@dataclass(frozen=True, slots=True)
class LocalAnalysisProducts:
    scope: EvidenceScope
    selected_evidence: list[CareerContextEvidence]
    scoped_master: MasterResume
    resume_text: str
    job_text: str
    match_result: MatchResultV2
    ats_result: ApplicationAtsAnalysis
    readiness_report: ApplicationReadinessReport
    tailor_result: ResumeTailorOutput
    dependency: DependencyFingerprint


def build_local_analysis_products(
    session: ApplicationLabSession,
    master: MasterResume,
    job: JobSnapshot,
    context: CareerContext,
) -> LocalAnalysisProducts:
    """Call the four real local domain tools over one immutable evidence selection."""
    evidence = [*context.evidence, *_resume_entry_evidence(master)]
    selected_ids = (
        []
        if session.selected_context_refs
        else [
            item.evidence_id
            for item in evidence
            if item.review_status is EvidenceReviewStatus.CONFIRMED
        ]
    )
    scope = EvidenceScope.from_evidence(
        purpose=CareerContextPurpose.MATCH,
        evidence=evidence,
        selected_evidence_ids=selected_ids,
        selected_source_refs=session.selected_context_refs,
    )
    selected_evidence = [
        item
        for item in scope.select(evidence)
        if item.review_status is EvidenceReviewStatus.CONFIRMED
    ]
    scoped_master = _scoped_master(master, selected_evidence)
    resume_text = resume_plain_text(scoped_master)
    job_text = _job_text(job)
    resume_extraction = extract_structured_resume_local(resume_text)
    job_extraction = extract_structured_job_local(
        job_text,
        source={"url": job.source_url, "type": job.source_kind},
    )
    match_result = analyze_match_v2(
        resume=resume_extraction.output,
        job=job_extraction.output,
        profile_items=[item.content or item.title for item in selected_evidence],
        preferences_fit_score=60,
    )
    job_analysis = job_analysis_from_match_v2(match_result)
    job_keywords = extract_keywords(job_text)
    resume_keywords = set(extract_keywords(resume_text, limit=200))
    ats_result = ApplicationAtsAnalysis(
        ats_score=calculate_simple_ats_score(resume_text, job_text),
        issues=analyze_ats_issues(resume_text, job_text),
        present_keywords=[item for item in job_keywords if item in resume_keywords],
        missing_keywords=[item for item in job_keywords if item not in resume_keywords],
        assessment_status="sufficient" if resume_text.strip() else "insufficient",
    )
    readiness_report = build_readiness_report(session.session_id, scoped_master, job)
    tailor_result = build_safe_tailor_output(
        target_role=job.title or master.target_role or "Oportunidade selecionada",
        target_company=job.organization or None,
        job_text=job_text,
        evidence_text=resume_text,
        match_analysis=job_analysis,
    )
    dependency = fingerprint_dependencies(
        master_resume=scoped_master,
        job_snapshot=job,
        evidence_scope=scope,
        engine_versions={"match": "2", "ats": "1", "readiness": "2", "tailor": "1"},
    )
    return LocalAnalysisProducts(
        scope=scope,
        selected_evidence=selected_evidence,
        scoped_master=scoped_master,
        resume_text=resume_text,
        job_text=job_text,
        match_result=match_result,
        ats_result=ats_result,
        readiness_report=readiness_report,
        tailor_result=tailor_result,
        dependency=dependency,
    )


def match_result_to_job_analysis(result: MatchResultV2) -> JobAnalysisSchema:
    """Expose the canonical Match-to-Tracker adapter without provider routing."""
    return job_analysis_from_match_v2(result)


def _resume_entry_evidence(master: MasterResume) -> list[CareerContextEvidence]:
    evidence: list[CareerContextEvidence] = []
    for section in master.sections:
        if not section.enabled:
            continue
        for entry in section.entries:
            if not entry.enabled:
                continue
            for source_ref in entry.source_refs or [""]:
                evidence.append(
                    CareerContextEvidence(
                        title=entry.title or section.title,
                        content=" ".join(
                            value.strip()
                            for value in (entry.title, entry.subtitle, entry.content)
                            if value.strip()
                        ),
                        kind="resume_entry",
                        source=master.source_type,
                        source_ref=source_ref,
                        review_status=entry.review_status,
                        confirmed_by_user=entry.confirmed_by_user,
                        metadata={"entry_id": entry.entry_id, "section_id": section.section_id},
                    )
                )
    return evidence


def _scoped_master(
    master: MasterResume,
    selected_evidence: list[CareerContextEvidence],
) -> MasterResume:
    selected_entry_ids = {
        str(item.metadata.get("entry_id", ""))
        for item in selected_evidence
        if item.kind == "resume_entry"
    }
    sections = deepcopy(master.sections)
    for section in sections:
        section.content = ""
        section.entries = [
            entry
            for entry in section.entries
            if entry.entry_id in selected_entry_ids
            and entry.review_status is EvidenceReviewStatus.CONFIRMED
        ]
    selected_refs = list(
        dict.fromkeys(item.source_ref for item in selected_evidence if item.source_ref)
    )
    selected_profile_ids = list(
        dict.fromkeys(
            profile_item_id
            for section in sections
            for entry in section.entries
            for profile_item_id in entry.source_profile_item_ids
        )
    )
    selected_text = "\n".join(item.content for item in selected_evidence if item.content.strip())
    return master.model_copy(
        update={
            "summary": "",
            "raw_text": selected_text,
            "source_refs": selected_refs,
            "source_profile_item_ids": selected_profile_ids,
            "sections": sections,
        },
        deep=True,
    )


def _job_text(job: JobSnapshot) -> str:
    return "\n".join(
        value
        for value in (
            job.title,
            job.organization,
            job.location,
            job.description,
            job.raw_text,
            json.dumps(job.structured_data, ensure_ascii=False, sort_keys=True),
        )
        if value.strip()
    )


__all__ = [
    "LocalAnalysisProducts",
    "build_local_analysis_products",
    "match_result_to_job_analysis",
]
