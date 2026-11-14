"""Allowlisted Copilot tools; no tool can bypass human approval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

TaskType = Literal[
    "follow_up",
    "interview",
    "application",
    "document",
    "certification",
    "project",
    "study",
    "networking",
    "custom",
]
TaskPriority = Literal["low", "medium", "high"]


class CreateTaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=240)
    # Same vocabulary as CareerTask: a Copilot task must be a valid Career task.
    task_type: TaskType = "custom"
    priority: TaskPriority = "medium"
    # Timezone-aware only: a naive "2026-12-01T12:00" is ambiguous for a deadline.
    due_at: AwareDatetime | None = None

    @field_validator("due_at")
    @classmethod
    def normalize_due_at(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value is not None else None


class ArchiveEvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str = Field(min_length=1, max_length=128)


class DraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(default="", max_length=20_000)


@dataclass(frozen=True)
class CopilotTool:
    tool_id: str
    description: str
    input_schema: type[BaseModel]
    output_schema: dict[str, str]
    read_only: bool
    requires_approval: bool
    risk_level: Literal["low", "medium", "high"]
    domain: str
    category: Literal["read", "draft", "write-local", "export"]
    # Execution is dispatched by CareerCopilot._execute_local on tool_id; there is no
    # per-tool handler (an unused ``handler`` field was removed, SH-AUD-020).


class ToolRegistry:
    """Closed registry rejecting unknown, forbidden and unapproved invocations."""

    FORBIDDEN_IDS = frozenset(
        {
            "submit_application",
            "send_email",
            "login",
            "capture_cookie",
            "capture_session",
            "payment",
            "bypass_captcha",
            "delete_profile",
        }
    )

    def __init__(self, tools: list[CopilotTool]) -> None:
        self._tools: dict[str, CopilotTool] = {}
        for tool in tools:
            if tool.tool_id in self.FORBIDDEN_IDS:
                raise ValueError(f"Forbidden Copilot tool: {tool.tool_id}")
            if not tool.read_only and not tool.requires_approval:
                raise ValueError(f"Write tool must require approval: {tool.tool_id}")
            if tool.tool_id in self._tools:
                raise ValueError(f"Duplicate Copilot tool: {tool.tool_id}")
            self._tools[tool.tool_id] = tool

    def get(self, tool_id: str) -> CopilotTool:
        if tool_id in self.FORBIDDEN_IDS:
            raise PermissionError(f"Forbidden Copilot tool: {tool_id}")
        try:
            return self._tools[tool_id]
        except KeyError as exc:
            raise KeyError(f"Unknown Copilot tool: {tool_id}") from exc

    def list(self) -> list[CopilotTool]:
        return sorted(self._tools.values(), key=lambda tool: tool.tool_id)

    def validate_input(self, tool_id: str, payload: dict[str, Any]) -> BaseModel:
        return self.get(tool_id).input_schema.model_validate(payload)


def default_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            CopilotTool(
                "read_career_state",
                "Lê o estado agregado da carreira.",
                DraftInput,
                {"state": "CareerState"},
                True,
                False,
                "low",
                "career",
                "read",
            ),
            CopilotTool(
                "draft_resume_variant",
                "Cria somente uma proposta de variante.",
                DraftInput,
                {"proposal_id": "str"},
                False,
                True,
                "medium",
                "resume",
                "draft",
            ),
            CopilotTool(
                "draft_follow_up",
                "Cria somente um rascunho local.",
                DraftInput,
                {"proposal_id": "str"},
                False,
                True,
                "low",
                "application",
                "draft",
            ),
            CopilotTool(
                "draft_interview_prep",
                "Cria preparação revisável.",
                DraftInput,
                {"proposal_id": "str"},
                False,
                True,
                "low",
                "interview",
                "draft",
            ),
            CopilotTool(
                "create_task",
                "Cria uma tarefa local após aprovação.",
                CreateTaskInput,
                {"task_id": "str"},
                False,
                True,
                "low",
                "career",
                "write-local",
            ),
            CopilotTool(
                "archive_evidence",
                "Arquiva evidência com undo.",
                ArchiveEvidenceInput,
                {"node_id": "str"},
                False,
                True,
                "medium",
                "evidence",
                "write-local",
            ),
        ]
    )
