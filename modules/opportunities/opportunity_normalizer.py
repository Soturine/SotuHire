"""Convert scraped opportunities to the analyzer's existing job schema."""

from __future__ import annotations

from modules.parsers.job_description_parser import parse_job_description
from modules.schemas.job_posting import JobPostingSchema
from modules.scraping.schemas import ScrapedOpportunity


def opportunity_to_job_posting(opportunity: ScrapedOpportunity) -> JobPostingSchema:
    """Normalize one collected opportunity for analysis."""
    parsed = parse_job_description(opportunity.description)
    updates: dict[str, object] = {
        "title": opportunity.title or parsed.title,
        "company": opportunity.company or parsed.company,
        "location": opportunity.location or parsed.location,
        "seniority": opportunity.seniority or parsed.seniority,
        "contract": opportunity.contract_type or parsed.contract,
        "required_skills": opportunity.requirements or parsed.required_skills,
        "benefits": opportunity.benefits or parsed.benefits,
        "raw_text": opportunity.description,
    }
    if opportunity.modality in {"remote", "hybrid", "onsite"}:
        updates["modality"] = opportunity.modality
    return parsed.model_copy(update=updates)
