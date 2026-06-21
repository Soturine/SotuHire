"""Transferable skill matching for multi-domain career transitions."""

from __future__ import annotations

from modules.core.text_utils import normalize_text
from modules.matching.models import CandidateEvidence, MatchRequirement, TransferableSkillMatch

TRANSFERABLE_SKILL_RULES: dict[str, list[tuple[str, str, str]]] = {
    "professor": [
        (
            "treinamento",
            "medium",
            "Ensino pode apoiar treinamento, mas não comprova experiência corporativa direta.",
        ),
        (
            "comunicacao",
            "high",
            "Docência demonstra comunicação e planejamento com evidência adequada.",
        ),
        ("planejamento", "medium", "Planejamento pedagógico pode apoiar organização de rotinas."),
    ],
    "enfermagem": [
        (
            "protocolo",
            "high",
            "Protocolos clínicos transferem para ambientes regulados e documentados.",
        ),
        ("documentacao", "medium", "Registro assistencial apoia documentação operacional."),
        ("pressao", "medium", "Atuação em saúde pode demonstrar trabalho sob pressão."),
    ],
    "psicologia": [
        (
            "rh",
            "medium",
            "Psicologia pode apoiar RH, mas não substitui experiência direta na função.",
        ),
        ("escuta ativa", "high", "Escuta ativa é transferível quando há evidência no currículo."),
        ("desenvolvimento humano", "medium", "Pode apoiar trilhas de desenvolvimento e cultura."),
    ],
    "engenharia civil": [
        ("planejamento", "high", "Planejamento de obras transfere para cronograma e execução."),
        ("orcamento", "medium", "Orçamento de obra pode apoiar análise financeira operacional."),
        ("gestao de obra", "high", "Gestão de obra é evidência forte para coordenação técnica."),
    ],
    "arquitetura": [
        ("briefing", "high", "Briefing com cliente transfere para discovery e requisitos."),
        ("autocad", "medium", "CAD/BIM apoia requisitos de desenho técnico quando explicitado."),
        (
            "projeto",
            "medium",
            "Projetos acadêmicos/autorais ajudam, mas não viram experiência corporativa.",
        ),
    ],
    "manutencao": [
        ("diagnostico", "high", "Diagnóstico técnico transfere para suporte e análise de falhas."),
        ("manutencao preventiva", "high", "Manutenção preventiva é evidência operacional direta."),
        ("equipamentos", "medium", "Experiência com equipamentos apoia ambientes industriais."),
    ],
    "cybersecurity": [
        ("risco", "high", "Análise de risco transfere para compliance e segurança."),
        ("investigacao", "medium", "Investigação técnica apoia análise de incidentes."),
        ("documentacao", "medium", "Documentação técnica ajuda processos de segurança."),
    ],
}


def find_transferable_skills(
    evidence: list[CandidateEvidence],
    requirements: list[MatchRequirement],
) -> list[TransferableSkillMatch]:
    """Find transferable skills that support, but do not satisfy, requirements."""
    output: list[TransferableSkillMatch] = []
    requirement_names = {
        normalize_text(item.normalized_name or item.requirement_text) for item in requirements
    }
    for item in evidence:
        source_terms = _candidate_terms(item)
        for source_term in source_terms:
            for target, level, limitation in TRANSFERABLE_SKILL_RULES.get(source_term, []):
                if target in requirement_names or any(target in name for name in requirement_names):
                    output.append(
                        TransferableSkillMatch(
                            original_skill=item.skill,
                            target_requirement=target,
                            transfer_level=level,  # type: ignore[arg-type]
                            confidence=min(0.85, max(0.35, item.confidence * 0.85)),
                            limitation=limitation,
                        )
                    )
    return _dedupe(output)


def _candidate_terms(evidence: CandidateEvidence) -> list[str]:
    corpus = normalize_text(
        " ".join([evidence.skill, evidence.normalized_name, evidence.evidence_text])
    )
    terms = []
    for key in TRANSFERABLE_SKILL_RULES:
        if key in corpus:
            terms.append(key)
    if evidence.category in {"domain_knowledge", "experience"} and evidence.normalized_name:
        terms.append(normalize_text(evidence.normalized_name).replace("_", " "))
    return list(dict.fromkeys(terms))


def _dedupe(items: list[TransferableSkillMatch]) -> list[TransferableSkillMatch]:
    deduped: dict[tuple[str, str], TransferableSkillMatch] = {}
    for item in sorted(items, key=lambda match: match.confidence, reverse=True):
        deduped.setdefault((item.original_skill, item.target_requirement), item)
    return list(deduped.values())
