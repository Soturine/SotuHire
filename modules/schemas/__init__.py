"""Typed schemas for SotuHire MVP."""

from .job_analysis import JobAnalysisSchema
from .json_resume import CareerEvidence, JSONResume
from .resume_tailor import ResumeTailorOutput, TailoredResumeSection
from .user_preferences import UserPreferences

__all__ = [
    "CareerEvidence",
    "JobAnalysisSchema",
    "JSONResume",
    "ResumeTailorOutput",
    "TailoredResumeSection",
    "UserPreferences",
]
