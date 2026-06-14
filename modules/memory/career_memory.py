"""Application-facing career memory operations."""

from __future__ import annotations

import hashlib
from pathlib import Path

from modules.memory.memory_retriever import MemoryRetriever
from modules.memory.memory_store import MemoryStore
from modules.memory.memory_summarizer import memory_markdown_summary
from modules.memory.schemas import CareerFeedback, CareerMemoryItem, MemoryKind
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.user_preferences import UserPreferences


class CareerMemory:
    """Ingest, retrieve, export, and clear local career context."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()
        self.retriever = MemoryRetriever(self.store)

    @staticmethod
    def _stable_id(kind: str, title: str, content: str, source_id: str | None) -> str:
        payload = "\0".join([kind, title, content, source_id or ""])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def remember_resume(self, profile: ResumeProfileSchema, source_id: str | None = None) -> int:
        """Persist structured resume facts without requiring external AI."""
        items: list[CareerMemoryItem] = []
        if profile.summary:
            item = CareerMemoryItem(
                kind="resume",
                title="Resumo profissional",
                content=profile.summary,
                source="resume",
                source_id=source_id,
                tags=profile.skills[:12],
            )
            items.append(
                item.model_copy(
                    update={"id": self._stable_id(item.kind, item.title, item.content, source_id)}
                )
            )
        skill_items = [
            CareerMemoryItem(
                kind="skill",
                title=f"Skill: {skill}",
                content=f"Skill presente no currículo: {skill}",
                source="resume",
                source_id=source_id,
                tags=[skill],
            )
            for skill in profile.skills
        ]
        items.extend(
            item.model_copy(
                update={"id": self._stable_id(item.kind, item.title, item.content, source_id)}
            )
            for item in skill_items
        )
        structured_sections: list[tuple[MemoryKind, list[str]]] = [
            ("experience", profile.experiences),
            ("project", profile.projects),
            ("education", profile.education),
        ]
        for kind, values in structured_sections:
            section_items = [
                CareerMemoryItem(
                    kind=kind,
                    title=value.splitlines()[0][:160],
                    content=value,
                    source="resume",
                    source_id=source_id,
                    tags=profile.skills[:8],
                )
                for value in values
            ]
            items.extend(
                item.model_copy(
                    update={"id": self._stable_id(item.kind, item.title, item.content, source_id)}
                )
                for item in section_items
            )
        for item in items:
            self.store.add_memory_item(item)
        return len(items)

    def remember_preferences(self, preferences: UserPreferences) -> int:
        """Persist explicit preferences as separate searchable facts."""
        facts = {
            "Modalidades preferidas": preferences.preferred_modalities,
            "Localizações preferidas": preferences.preferred_locations,
            "Contratos aceitos": preferences.accepted_contracts,
            "Senioridades alvo": preferences.target_levels,
            "Notas de prioridade": preferences.priority_notes,
        }
        items = [
            CareerMemoryItem(
                kind="preference",
                title=title,
                content=", ".join(values),
                source="user_preferences",
                tags=list(values),
            )
            for title, values in facts.items()
            if values
        ]
        for item in items:
            self.store.add_memory_item(item)
        return len(items)

    def remember_analysis(
        self,
        analysis: JobAnalysisSchema,
        *,
        job_title: str = "",
        company: str = "",
        source_id: str | None = None,
    ) -> CareerMemoryItem:
        """Persist a compact analysis outcome."""
        content = (
            f"Recomendação: {analysis.recommendation}. Match: {analysis.match_score}. "
            f"ATS: {analysis.ats_score}. Fit: {analysis.opportunity_fit_score}. "
            f"Fortes: {', '.join(analysis.strengths[:5])}. "
            f"Gaps: {', '.join(analysis.gaps[:5])}."
        )
        item = CareerMemoryItem(
            kind="job_analysis",
            title=f"Análise: {job_title or 'Vaga'}{f' · {company}' if company else ''}",
            content=content,
            source="analysis",
            source_id=source_id,
            tags=[analysis.recommendation, *analysis.missing_keywords[:8]],
        )
        return self.store.add_memory_item(
            item.model_copy(
                update={"id": self._stable_id(item.kind, item.title, item.content, source_id)}
            )
        )

    def remember_feedback(self, feedback: CareerFeedback) -> CareerMemoryItem:
        """Persist manual feedback for future deterministic personalization."""
        content = (
            f"Avaliação: {feedback.rating}. Motivo: {feedback.reason or 'não informado'}. "
            f"Mudança desejada: {feedback.change_requested or 'não informada'}. "
            f"Aplicou: {feedback.applied}. Retorno: {feedback.response_received}."
        )
        return self.store.add_memory_item(
            CareerMemoryItem(
                kind="feedback",
                title="Feedback de recomendação",
                content=content,
                source="manual_feedback",
                source_id=feedback.analysis_id,
                tags=[feedback.rating],
            )
        )

    def remember_opportunity(
        self,
        *,
        title: str,
        company: str = "",
        source: str = "tracker",
        source_id: str | None = None,
        details: str = "",
        tags: list[str] | None = None,
    ) -> CareerMemoryItem:
        """Persist a saved or previously applied opportunity."""
        item = CareerMemoryItem(
            kind="opportunity",
            title=f"{title or 'Vaga'}{f' · {company}' if company else ''}",
            content=details
            or f"Oportunidade salva: {title}. Empresa: {company or 'não informada'}.",
            source=source,
            source_id=source_id,
            tags=tags or [],
        )
        return self.store.add_memory_item(
            item.model_copy(
                update={"id": self._stable_id(item.kind, item.title, item.content, source_id)}
            )
        )

    def remember_tracker_event(
        self,
        *,
        record_id: str,
        status: str,
        job_title: str = "",
        company: str = "",
    ) -> CareerMemoryItem:
        """Persist one tracker status transition."""
        return self.store.add_memory_item(
            CareerMemoryItem(
                kind="tracker_event",
                title=f"Análise: {job_title or 'Vaga'}{f' · {company}' if company else ''}",
                content=f"Status do tracker: {status}.",
                source="tracker",
                source_id=record_id,
                tags=[status],
            )
        )

    def export_all(self, directory: str | Path = "exports/memory") -> dict[str, Path]:
        """Export JSON, JSONL, and Markdown summary."""
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        items = self.store.list_memory_items()
        markdown = target / "career-memory-summary.md"
        markdown.write_text(memory_markdown_summary(items), encoding="utf-8")
        return {
            "json": self.store.export_json(target / "career-memory.json"),
            "jsonl": self.store.export_jsonl(target / "career-memory.jsonl"),
            "markdown": markdown,
        }
