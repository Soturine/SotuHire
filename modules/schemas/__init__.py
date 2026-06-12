"""Typed schemas for SotuHire MVP."""

from .job_analysis import JobAnalysisSchema
from .job_posting import JobPostingSchema
from .json_resume import CareerEvidence, JSONResume
from .resume_profile import ResumeProfileSchema
from .resume_tailor import ResumeTailorOutput, TailoredResumeSection
from .user_preferences import UserPreferences

__all__ = [
    "CareerEvidence",
    "JobAnalysisSchema",
    "JobPostingSchema",
    "JSONResume",
    "ResumeProfileSchema",
    "ResumeTailorOutput",
    "TailoredResumeSection",
    "UserPreferences",
]
