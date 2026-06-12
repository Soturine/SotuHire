"""User preference schemas for opportunity scoring."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Modality = Literal["remote", "hybrid", "onsite"]


class UserPreferences(BaseModel):
    """Career and lifestyle preferences used by Opportunity Fit Score."""

    model_config = ConfigDict(extra="forbid")

    preferred_locations: list[str] = Field(default_factory=list)
    preferred_modalities: list[Modality] = Field(default_factory=list)
    min_salary: int | None = Field(default=None, ge=0)
    accepted_contracts: list[str] = Field(default_factory=list)
    target_levels: list[str] = Field(default_factory=list)
    priority_notes: list[str] = Field(default_factory=list)

    salary_weight: float = Field(default=1.0, ge=0)
    modality_weight: float = Field(default=1.0, ge=0)
    location_weight: float = Field(default=1.0, ge=0)
    contract_weight: float = Field(default=1.0, ge=0)
    seniority_weight: float = Field(default=1.0, ge=0)

    def has_preferences(self) -> bool:
        """Return True when at least one concrete preference was configured."""
        return any(
            [
                self.preferred_locations,
                self.preferred_modalities,
                self.min_salary is not None,
                self.accepted_contracts,
                self.target_levels,
            ]
        )
