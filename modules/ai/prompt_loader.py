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
    ]


def default_prompt_registry() -> PromptRegistry:
    """Return the default prompt registry for structured extraction."""
    return PromptRegistry(initial_prompt_specs())


def _default_schemas() -> dict[str, type[BaseModel]]:
    from modules.ai.schemas.domain_classification import DomainClassificationOutput
    from modules.ai.schemas.job_extraction import JobExtractionOutput
    from modules.ai.schemas.resume_extraction import ResumeExtractionOutput

    return {
        "resume_extraction_v1": ResumeExtractionOutput,
        "job_extraction_multi_domain_v1": JobExtractionOutput,
        "domain_classification_v1": DomainClassificationOutput,
    }
