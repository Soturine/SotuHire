"""Initial structured prompt definitions for v0.10."""

from __future__ import annotations

from pydantic import BaseModel

from modules.ai.prompt_registry import PromptRegistry
from modules.ai.prompt_spec import PromptSpec

RESUME_EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured resume facts for a local-first career copilot. "
    "Use only evidence present in the resume. Return valid JSON only. "
    "Do not invent experience, education, certifications, professional licenses, "
    "languages, tools, metrics or employment. If a field is unclear, use low confidence "
    "and mark it for human review. Support multiple career domains, not only technology."
)

RESUME_EXTRACTION_USER_TEMPLATE = """Analyze the resume and return JSON matching the schema.

File type: {file_type}
Candidate preferences: {candidate_preferences}
Existing profile memory: {existing_profile_memory}
Local parser hints: {local_profile}
Language: {language}

RESUME:
{resume_text}
"""

JOB_EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured job-posting facts for any professional domain. "
    "Return valid JSON only. Do not invent company, salary, requirements, benefits, "
    "licenses or certifications. Distinguish required, preferred, optional and unclear "
    "requirements. Treat regulated professions conservatively."
)

JOB_EXTRACTION_USER_TEMPLATE = """Analyze the job posting and return JSON matching the schema.

Source: {source}
Candidate context: {candidate_context}
Local parser hints: {local_job}
Language: {language}

JOB POSTING:
{job_text}
"""

DOMAIN_CLASSIFICATION_SYSTEM_PROMPT = (
    "You classify professional domains using textual evidence. Do not force everything "
    "into technology. Accept mixed domains and return valid JSON only."
)

DOMAIN_CLASSIFICATION_USER_TEMPLATE = """Classify the professional domain in the text.

Text type: {text_type}
Known context: {known_context}
Language: {language}

TEXT:
{text}
"""

GITHUB_REPO_ANALYSIS_SYSTEM_PROMPT = (
    "You are a senior evaluator of software quality, architecture, security, documentation "
    "and professional portfolio value. Analyze only the evidence provided: metadata, tree, "
    "selected files, dependency graph and target role/job when present. Return valid JSON only. "
    "Do not invent technologies, metrics, users, companies, deploys, experience or outcomes. "
    "If tests appear in the tree, acknowledge their presence even when their content was not read."
)

GITHUB_REPO_ANALYSIS_USER_TEMPLATE = """Analyze the repository below.

Repository metadata:
{repository}

Analysis context:
{analysis_context}

Detected signals:
{detected_signals}

Complete directory tree:
{repository_structure}

Selected files:
{selected_files}

Dependency graph:
{dependency_graph}

Return only JSON matching the expected schema.
"""

MATCH_ANALYSIS_SYSTEM_PROMPT = (
    "You analyze resume/job compatibility for SotuHire using only provided evidence. "
    "Return valid JSON only. Do not invent jobs, education, skills, certifications, "
    "licenses, metrics or outcomes. Scores must be conservative and explainable. "
    "Missing evidence is a gap, not a fact about the candidate."
)

MATCH_ANALYSIS_USER_TEMPLATE = """Analyze compatibility and return JSON matching the schema.

Preferences:
{preferences}

Job details:
{job_details}

Authorized memory context:
{memory_context}

RESUME:
{resume_text}

JOB:
{job_text}
"""

ATS_ANALYSIS_SYSTEM_PROMPT = (
    "You review ATS keyword alignment using only the resume, job text and deterministic "
    "keyword review already provided. Return valid JSON only. Never recommend adding a "
    "claim unless the user confirms it is true."
)

ATS_ANALYSIS_USER_TEMPLATE = """Review ATS evidence and return JSON matching the schema.

Deterministic review:
{deterministic_review}

Keywords:
{keywords}

RESUME:
{resume_text}

JOB:
{job_text}
"""

RESUME_TAILOR_SYSTEM_PROMPT = (
    "You suggest resume tailoring improvements for SotuHire. Use only evidence supplied "
    "by the user. Return valid JSON only. Do not invent experience, credentials, tools, "
    "companies, numbers or achievements. Conditional suggestions must be clearly marked."
)

RESUME_TAILOR_USER_TEMPLATE = """Suggest safe resume tailoring ideas and return JSON matching the schema.

Target role: {target_role}
Target company: {target_company}
Deterministic tailor:
{deterministic_tailor}

JOB:
{job_text}

EVIDENCE:
{evidence_text}
"""

CAREER_ADVICE_SYSTEM_PROMPT = (
    "You provide cautious career guidance using only supplied SotuHire evidence. "
    "Return valid JSON only and separate safe actions from uncertain observations."
)

CAREER_ADVICE_USER_TEMPLATE = """Provide safe career insights and return JSON matching the schema.

Context:
{context}

Evidence:
{evidence}
"""


def initial_prompt_specs(
    schema_overrides: dict[str, type[BaseModel]] | None = None,
) -> list[PromptSpec]:
    """Build initial v0.10 prompt specs with their output schemas."""
    schemas = schema_overrides or _default_schemas()
    return [
        PromptSpec(
            prompt_id="resume_extraction_v1",
            version="1.0.0",
            system_prompt=RESUME_EXTRACTION_SYSTEM_PROMPT,
            user_template=RESUME_EXTRACTION_USER_TEMPLATE,
            output_schema=schemas["resume_extraction_v1"],
            temperature=0.1,
            mode="resume_extraction",
        ),
        PromptSpec(
            prompt_id="job_extraction_multi_domain_v1",
            version="1.0.0",
            system_prompt=JOB_EXTRACTION_SYSTEM_PROMPT,
            user_template=JOB_EXTRACTION_USER_TEMPLATE,
            output_schema=schemas["job_extraction_multi_domain_v1"],
            temperature=0.1,
            mode="job_extraction",
        ),
        PromptSpec(
            prompt_id="domain_classification_v1",
            version="1.0.0",
            system_prompt=DOMAIN_CLASSIFICATION_SYSTEM_PROMPT,
            user_template=DOMAIN_CLASSIFICATION_USER_TEMPLATE,
            output_schema=schemas["domain_classification_v1"],
            temperature=0.1,
            mode="domain_classification",
        ),
        PromptSpec(
            prompt_id="github_repo_analysis_v2",
            version="2.0.0",
            system_prompt=GITHUB_REPO_ANALYSIS_SYSTEM_PROMPT,
            user_template=GITHUB_REPO_ANALYSIS_USER_TEMPLATE,
            output_schema=schemas["github_repo_analysis_v2"],
            temperature=0.1,
            mode="github_repo_analysis",
        ),
        PromptSpec(
            prompt_id="match_analysis_evidence_based_v1",
            version="1.0.0",
            system_prompt=MATCH_ANALYSIS_SYSTEM_PROMPT,
            user_template=MATCH_ANALYSIS_USER_TEMPLATE,
            output_schema=schemas["match_analysis_evidence_based_v1"],
            temperature=0.1,
            mode="match_analysis",
        ),
        PromptSpec(
            prompt_id="ats_analysis_v1",
            version="1.0.0",
            system_prompt=ATS_ANALYSIS_SYSTEM_PROMPT,
            user_template=ATS_ANALYSIS_USER_TEMPLATE,
            output_schema=schemas["ats_analysis_v1"],
            temperature=0.1,
            mode="ats_analysis",
        ),
        PromptSpec(
            prompt_id="resume_tailor_v1",
            version="1.0.0",
            system_prompt=RESUME_TAILOR_SYSTEM_PROMPT,
            user_template=RESUME_TAILOR_USER_TEMPLATE,
            output_schema=schemas["resume_tailor_v1"],
            temperature=0.1,
            mode="resume_tailor",
        ),
        PromptSpec(
            prompt_id="career_advice_v1",
            version="1.0.0",
            system_prompt=CAREER_ADVICE_SYSTEM_PROMPT,
            user_template=CAREER_ADVICE_USER_TEMPLATE,
            output_schema=schemas["career_advice_v1"],
            temperature=0.1,
            mode="career_advice",
        ),
    ]


def default_prompt_registry() -> PromptRegistry:
    """Return the default prompt registry for structured extraction."""
    return PromptRegistry(initial_prompt_specs())


def _default_schemas() -> dict[str, type[BaseModel]]:
    from modules.ai.schemas.analysis_insights import (
        AtsAiReviewOutput,
        ResumeTailorAiOutput,
        SafeAiInsightOutput,
    )
    from modules.ai.schemas.domain_classification import DomainClassificationOutput
    from modules.ai.schemas.job_extraction import JobExtractionOutput
    from modules.ai.schemas.resume_extraction import ResumeExtractionOutput
    from modules.github_analyzer.schemas import GitHubRepoAnalysisOutput
    from modules.schemas.job_analysis import JobAnalysisSchema

    return {
        "resume_extraction_v1": ResumeExtractionOutput,
        "job_extraction_multi_domain_v1": JobExtractionOutput,
        "domain_classification_v1": DomainClassificationOutput,
        "github_repo_analysis_v2": GitHubRepoAnalysisOutput,
        "match_analysis_evidence_based_v1": JobAnalysisSchema,
        "ats_analysis_v1": AtsAiReviewOutput,
        "resume_tailor_v1": ResumeTailorAiOutput,
        "career_advice_v1": SafeAiInsightOutput,
    }
