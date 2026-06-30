from pathlib import Path

from modules.context import CareerContextEngine, CareerContextPurpose, context_to_memory_evidence
from modules.memory import CareerMemoryItem, MemoryRetriever, MemoryStore
from modules.profile import (
    CareerProfileStore,
    ProfileContextOrchestrator,
    ProfileItem,
    UniversalCareerProfile,
)
from modules.profile.store import UniversalCareerProfileStore


def _engine(tmp_path: Path) -> tuple[CareerContextEngine, UniversalCareerProfileStore, MemoryStore]:
    profile_store = UniversalCareerProfileStore(tmp_path / "profiles.json")
    memory_store = MemoryStore(tmp_path / "memory.jsonl")
    engine = CareerContextEngine(
        profile_orchestrator=ProfileContextOrchestrator(
            store=CareerProfileStore(tmp_path / "legacy-profile.json"),
            universal_store=profile_store,
        ),
        memory_retriever=MemoryRetriever(memory_store),
    )
    return engine, profile_store, memory_store


def test_context_includes_universal_profile_evidence(tmp_path: Path) -> None:
    engine, profile_store, _ = _engine(tmp_path)
    profile_store.save_active(
        UniversalCareerProfile(
            summary="Pessoa em transicao para dados.",
            target_roles=["Analista de Dados Junior"],
            primary_domains=["Dados"],
            preferred_locations=["Remoto"],
            preferred_work_models=["remoto"],
            items=[
                ProfileItem(
                    type="technical_skill",
                    title="Python",
                    evidence="Curso e projeto local informados pelo usuario.",
                    confidence="high",
                    confirmed_by_user=True,
                )
            ],
        )
    )

    context = engine.build(CareerContextPurpose.MATCH, query="vaga Python")

    assert context.profile_summary == "Pessoa em transicao para dados."
    assert "Analista de Dados Junior" in context.goals
    assert "Remoto" in context.locations
    assert context.evidence[0].title == "Python"
    assert context.evidence[0].confirmed_by_user is True


def test_context_includes_rag_evidence_when_query_matches(tmp_path: Path) -> None:
    engine, _, memory_store = _engine(tmp_path)
    memory_store.add_memory_item(
        CareerMemoryItem(
            kind="project",
            title="Projeto FastAPI",
            content="API Python com FastAPI, testes Pytest e PostgreSQL.",
            source="resume",
            tags=["Python", "FastAPI"],
        )
    )

    context = engine.build("match", query="vaga Python FastAPI", include_memory=True)

    assert any(item.title == "Projeto FastAPI" for item in context.evidence)
    assert context_to_memory_evidence(context)


def test_context_deduplicates_profile_and_memory_evidence(tmp_path: Path) -> None:
    engine, profile_store, memory_store = _engine(tmp_path)
    profile_store.save_active(
        UniversalCareerProfile(
            items=[
                ProfileItem(
                    type="project",
                    title="API FastAPI",
                    evidence="Projeto com FastAPI.",
                    confidence="high",
                    confirmed_by_user=True,
                )
            ],
        )
    )
    memory_store.add_memory_item(
        CareerMemoryItem(
            kind="project",
            title="API FastAPI",
            content="Projeto com FastAPI.",
            source="memory",
            confidence=0.7,
        )
    )

    context = engine.build("match", query="API FastAPI")

    assert [item.title for item in context.evidence].count("API FastAPI") == 1
    assert context.evidence[0].confirmed_by_user is True


def test_context_prioritizes_confirmed_high_confidence(tmp_path: Path) -> None:
    engine, profile_store, _ = _engine(tmp_path)
    profile_store.save_active(
        UniversalCareerProfile(
            items=[
                ProfileItem(type="technical_skill", title="A confirmar", confidence="low"),
                ProfileItem(
                    type="technical_skill",
                    title="Confirmado",
                    confidence="high",
                    confirmed_by_user=True,
                ),
            ],
        )
    )

    context = engine.build("ats", query="Confirmado")

    assert context.evidence[0].title == "Confirmado"


def test_context_works_without_profile_or_memory(tmp_path: Path) -> None:
    engine, _, _ = _engine(tmp_path)

    context = engine.build("dashboard", query="qualquer coisa")

    assert context.purpose == CareerContextPurpose.DASHBOARD
    assert context.evidence == []
    assert context.warnings


def test_context_marks_sensitive_privacy_notes(tmp_path: Path) -> None:
    engine, profile_store, _ = _engine(tmp_path)
    profile_store.save_active(
        UniversalCareerProfile(
            items=[
                ProfileItem(
                    type="professional_experience",
                    title="Experiencia com salario informado",
                    evidence="Salario anterior informado pelo usuario.",
                    confidence="medium",
                    sensitive=True,
                )
            ],
        )
    )

    context = engine.build("tailor", query="experiencia")

    assert context.evidence[0].sensitive is True
    assert any("sensiveis" in note for note in context.privacy_notes)
