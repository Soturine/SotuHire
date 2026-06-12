"""Pure dashboard metrics built from local tracker records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.models import StoredAnalysis


class DashboardMetrics(BaseModel):
    """Summary displayed by the initial local dashboard."""

    model_config = ConfigDict(extra="forbid")

    total_analyzed: int = 0
    average_match_score: float = 0
    average_ats_score: float = 0
    average_opportunity_fit: float = 0
    recommended_to_apply: int = 0
    high_risk: int = 0
    latest: list[StoredAnalysis] = Field(default_factory=list)


def calculate_dashboard_metrics(records: list[StoredAnalysis]) -> DashboardMetrics:
    """Calculate stable metrics for an empty or populated history."""
    if not records:
        return DashboardMetrics()

    total = len(records)
    return DashboardMetrics(
        total_analyzed=total,
        average_match_score=round(sum(item.analysis.match_score for item in records) / total, 1),
        average_ats_score=round(sum(item.analysis.ats_score for item in records) / total, 1),
        average_opportunity_fit=round(
            sum(item.analysis.opportunity_fit_score for item in records) / total,
            1,
        ),
        recommended_to_apply=sum(item.analysis.should_apply() for item in records),
        high_risk=sum(item.analysis.risk_score >= 75 for item in records),
        latest=records[:5],
    )
