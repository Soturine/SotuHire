"""Professional domain catalog for deterministic classification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainRule:
    """Keyword hints for a professional domain."""

    name: str
    keywords: tuple[str, ...]
    is_tech: bool = False


PROFESSIONAL_DOMAINS = (
    "software_engineering",
    "cybersecurity",
    "data",
    "qa",
    "biomedical_engineering",
    "civil_engineering",
    "electrical_engineering",
    "mechanical_engineering",
    "engineering",
    "nursing",
    "psychology",
    "pedagogy",
    "architecture",
    "interior_design",
    "business",
    "finance",
    "marketing",
    "logistics",
    "industrial",
    "technical_course",
    "healthcare",
    "education",
    "humanities",
    "general",
    "unknown",
)


DOMAIN_RULES: tuple[DomainRule, ...] = (
    DomainRule(
        "software_engineering",
        (
            "desenvolvedor",
            "developer",
            "backend",
            "frontend",
            "fullstack",
            "api",
            "python",
            "java",
            "javascript",
            "react",
            "node",
            "software",
        ),
        is_tech=True,
    ),
    DomainRule(
        "cybersecurity",
        (
            "cybersecurity",
            "seguranca da informacao",
            "soc",
            "siem",
            "hardening",
            "incidente",
            "vulnerabilidade",
            "grc",
            "iso 27001",
        ),
        is_tech=True,
    ),
    DomainRule(
        "data",
        (
            "dados",
            "data",
            "bi",
            "power bi",
            "sql",
            "etl",
            "analytics",
            "dashboard",
            "machine learning",
        ),
        is_tech=True,
    ),
    DomainRule("qa", ("qa", "qualidade de software", "testes", "selenium", "pytest"), True),
    DomainRule(
        "biomedical_engineering",
        (
            "engenharia biomedica",
            "equipamentos hospitalares",
            "metrologia",
            "calibracao",
            "anvisa",
            "manutencao preventiva",
            "manutencao corretiva",
        ),
    ),
    DomainRule(
        "civil_engineering",
        (
            "engenharia civil",
            "obra",
            "canteiro",
            "orcamento",
            "cronograma",
            "medicao",
            "autocad",
            "revit",
            "abnt",
            "concreto",
        ),
    ),
    DomainRule(
        "electrical_engineering",
        ("engenharia eletrica", "eletrica", "nr 10", "subestacao", "circuitos", "energia"),
    ),
    DomainRule(
        "mechanical_engineering",
        ("engenharia mecanica", "mecanica", "solidworks", "usinagem", "manutencao mecanica"),
    ),
    DomainRule("engineering", ("engenharia", "crea", "engenheiro", "engenheira")),
    DomainRule("nursing", ("enfermagem", "enfermeiro", "enfermeira", "coren", "uti", "plantao")),
    DomainRule("psychology", ("psicologia", "psicologo", "psicologa", "crp", "clinica", "aba")),
    DomainRule("pedagogy", ("pedagogia", "pedagogo", "professor", "bncc", "alfabetizacao")),
    DomainRule(
        "architecture",
        ("arquitetura", "arquiteto", "arquiteta", "cau", "revit", "sketchup", "projeto executivo"),
    ),
    DomainRule(
        "interior_design",
        ("design de interiores", "interiores", "promob", "render", "briefing", "moodboard"),
    ),
    DomainRule("business", ("administracao", "negocios", "processos", "rh", "recursos humanos")),
    DomainRule("finance", ("financeiro", "contabil", "contabilidade", "crc", "fiscal")),
    DomainRule("marketing", ("marketing", "seo", "midias sociais", "campanhas", "branding")),
    DomainRule("logistics", ("logistica", "estoque", "supply", "transporte", "roteirizacao")),
    DomainRule("industrial", ("industria", "industrial", "producao", "clp", "manufatura")),
    DomainRule("technical_course", ("tecnico", "curso tecnico", "cft", "eletrotecnica")),
    DomainRule("healthcare", ("saude", "hospital", "paciente", "prontuario", "uti")),
    DomainRule("education", ("educacao", "ensino", "escola", "aluno", "aprendizagem")),
    DomainRule("humanities", ("humanas", "social", "pesquisa qualitativa", "comunicacao")),
    DomainRule("general", ("assistente", "auxiliar", "atendimento", "administrativo")),
)
