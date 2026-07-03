"""Conservative parser for pasted public exam notices and editais."""

from __future__ import annotations

import re
from collections.abc import Iterable
from hashlib import sha1
from typing import cast, get_args

from modules.core.text_utils import normalize_text

from .models import (
    ExamNotice,
    ExamRequirement,
    ExamRequirementKind,
    ExamRole,
    ExamSubject,
    ExamTimeline,
    PublicExamImportInput,
    PublicExamImportResult,
)

_REQUIREMENT_KINDS = set(get_args(ExamRequirementKind))

OFFICIAL_NOTICE_WARNING = (
    "O SotuHire ajuda a organizar e interpretar editais, mas o edital oficial "
    "sempre prevalece. Revise manualmente requisitos, datas, taxa, documentos, "
    "conteúdo programático e regras da banca."
)

_DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
_MONEY = r"R\$\s?[\d\.\,]+"
_NOTICE_RE = re.compile(r"\bedital\s*(?:n[ºo.]*)?\s*([0-9][\w./-]*)", re.IGNORECASE)
_BOARD_RE = re.compile(
    r"(?:banca(?:\s+organizadora)?|organizadora|instituto organizador|empresa organizadora)\s*[:\-]\s*([^\n.;]+)",
    re.IGNORECASE,
)
_ORG_RE = re.compile(
    r"(?:órgão|orgao|instituição|instituicao)\s*[:\-]\s*([^\n.;]+)",
    re.IGNORECASE,
)
_ROLE_RE = re.compile(
    r"(?:cargo|função|funcao|emprego|vaga|perfil)\s*[:\-]\s*([^\n.;]+)",
    re.IGNORECASE,
)
_SALARY_RE = re.compile(
    rf"(?:salário|salario|vencimento|remuneração|remuneracao|bolsa)[^\n:;]*[:\s-]*({_MONEY})",
    re.IGNORECASE,
)
_FEE_RE = re.compile(
    rf"(?:taxa de inscrição|taxa de inscricao|inscrição)[^\n:;]*[:\s-]*({_MONEY})",
    re.IGNORECASE,
)
_WORKLOAD_RE = re.compile(
    r"(?:carga horária|carga horaria|jornada)[^\n:;]*[:\s-]*([0-9]{1,3}\s*h(?:oras)?(?:\s*semanais)?)",
    re.IGNORECASE,
)
_VACANCY_RE = re.compile(
    r"(?:vagas?|cadastro reserva|cr)\s*[:\-]\s*([0-9]+|cadastro reserva|cr)",
    re.IGNORECASE,
)
_LOCATION_RE = re.compile(
    r"(?:lotação|lotacao|localidade|local de prova|cidade)\s*[:\-]\s*([^\n.;]+)",
    re.IGNORECASE,
)
_REGISTRY_RE = re.compile(r"\b(CREA|CFT|CRQ|COREN|CRP|CRM|OAB|CRC|CAU|CRMV|CRESS|CRN|CREFITO)\b")

_SECTION_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("requirements", ("requisitos", "requisitos basicos", "requisitos básicos")),
    ("documents", ("documentos", "documentacao", "documentação")),
    ("timeline", ("cronograma", "datas", "inscricoes", "inscrições")),
    ("subjects", ("conteudo programatico", "conteúdo programático", "programa")),
    ("stages", ("etapas", "provas", "avaliacao", "avaliação")),
)

_EDUCATION_LEVELS = (
    ("fundamental", ("ensino fundamental", "nivel fundamental", "nível fundamental")),
    ("médio", ("ensino medio", "ensino médio", "nivel medio", "nível médio")),
    ("técnico", ("curso tecnico", "curso técnico", "nivel tecnico", "nível técnico")),
    ("tecnólogo", ("tecnologo", "tecnólogo")),
    (
        "superior",
        ("nivel superior", "nível superior", "graduacao", "graduação", "bacharelado"),
    ),
    (
        "pós-graduação",
        (
            "pos-graduacao",
            "pós-graduação",
            "especializacao",
            "especialização",
            "mestrado",
            "doutorado",
        ),
    ),
)


def parse_public_exam_notice(payload: PublicExamImportInput) -> PublicExamImportResult:
    """Parse pasted edital text into a review-only draft."""
    text = payload.text.strip()
    lines = [line.strip(" \t-•") for line in text.splitlines() if line.strip(" \t-•")]
    sections = _sections(lines)
    timeline = _timeline(text, sections.get("timeline", []))
    requirements = _requirements(text, sections)
    subjects = _subjects(text, sections.get("subjects", []))
    documents = _documents(sections.get("documents", []), text)
    notice_id = _stable_id(text)
    roles = _roles(text, lines, requirements, subjects, notice_id)
    notice = ExamNotice(
        notice_id=notice_id,
        title=_title(text, payload.source_name),
        raw_text=text,
        source_url=payload.source_url,
        source_name=payload.source_name,
        organization=_organization(text),
        exam_board=_first_match(_BOARD_RE, text),
        notice_number=_first_match(_NOTICE_RE, text),
        publication_date=_publication_date(text),
        registration_fee=_fee(text),
        status="draft",
        opportunity_type=_opportunity_type(text),
        locations=_unique([*_locations(text), *[role.location for role in roles if role.location]]),
        roles=roles,
        timeline=timeline,
        documents=documents,
        general_requirements=requirements,
        subjects=subjects,
    )
    notice = notice.model_copy(update={"warnings": _warnings(text, notice, roles)})
    return PublicExamImportResult(
        notice=notice,
        roles=roles,
        timeline=timeline,
        subjects=subjects,
        requirements=requirements,
        warnings=notice.warnings,
        questions_to_confirm=[
            "Os cargos, datas e requisitos extraídos batem com o edital oficial?",
            "Algum requisito legal precisa de leitura manual da banca ou do órgão?",
            "Qual cargo você quer comparar com o seu Perfil Profissional Universal?",
        ],
        source_excerpts=_source_excerpts(lines),
        needs_user_review=True,
        provider_used="local",
        requested_provider="local",
        analysis_mode="local",
    )


def _stable_id(text: str) -> str:
    normalized = normalize_text(text)[:200]
    digest = sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"exam-{digest}"


def _sections(lines: list[str]) -> dict[str, list[str]]:
    current = "general"
    sections: dict[str, list[str]] = {current: []}
    for line in lines:
        normalized = normalize_text(line)
        matched = next(
            (
                name
                for name, aliases in _SECTION_MARKERS
                if any(alias in normalized for alias in aliases)
            ),
            None,
        )
        if matched and len(line) <= 120 and not _DATE_RE.search(line):
            current = matched
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _title(text: str, source_name: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if "edital" in normalize_text(cleaned) and len(cleaned) >= 8:
            return cleaned[:300]
    return source_name or "Edital importado para revisão"


def _organization(text: str) -> str:
    value = _first_match(_ORG_RE, text)
    if value:
        return value
    for line in text.splitlines()[:12]:
        cleaned = line.strip()
        normalized = normalize_text(cleaned)
        if any(
            marker in normalized
            for marker in (
                "prefeitura",
                "universidade",
                "instituto federal",
                "tribunal",
                "secretaria",
            )
        ):
            return cleaned[:240]
    return ""


def _publication_date(text: str) -> str:
    for line in text.splitlines():
        normalized = normalize_text(line)
        if "publicacao" in normalized or "publicação" in normalized:
            match = _DATE_RE.search(line)
            if match:
                return match.group(0)
    return ""


def _opportunity_type(text: str) -> str:
    normalized = normalize_text(text)
    if "residencia" in normalized or "residência" in normalized:
        return "residency"
    if "bolsa" in normalized:
        return "scholarship"
    if "estagio" in normalized or "estágio" in normalized:
        return "internship_public"
    if "chamada publica" in normalized or "chamada pública" in normalized:
        return "academic_call"
    return "public_exam"


def _roles(
    text: str,
    lines: list[str],
    requirements: list[ExamRequirement],
    subjects: list[ExamSubject],
    notice_id: str,
) -> list[ExamRole]:
    matches = [match.group(1).strip() for match in _ROLE_RE.finditer(text)]
    if not matches:
        matches = [
            line
            for line in lines
            if any(
                marker in normalize_text(line)
                for marker in (
                    "analista",
                    "tecnico",
                    "técnico",
                    "professor",
                    "medico",
                    "médico",
                    "engenheiro",
                    "assistente",
                )
            )
            and ("r$" in normalize_text(line) or "vagas" in normalize_text(line))
        ][:4]
    titles = _unique(matches) or ["Cargo a revisar"]
    roles = []
    for raw in titles[:8]:
        title = _clean_role_title(raw)
        roles.append(
            ExamRole(
                notice_id=notice_id,
                title=title or "Cargo a revisar",
                area=_area_for(title),
                level=_education_level(text),
                education_level=_education_level(text),
                required_degree=_required_degree(text),
                required_registry=_registry(text),
                required_experience=_required_experience(text),
                required_certifications=_certifications(text),
                salary=_salary(text),
                workload=_first_match(_WORKLOAD_RE, text),
                vacancies=_first_match(_VACANCY_RE, text),
                reserved_vacancies=_reserved_vacancies(text),
                quota_notes=_quota_notes(text),
                contract_type=_opportunity_type(text),
                employment_regime=_employment_regime(text),
                location=_first_match(_LOCATION_RE, text),
                requirements=requirements,
                subjects=subjects,
                stages=_stages(text),
            )
        )
    return roles


def _timeline(text: str, timeline_lines: list[str]) -> ExamTimeline:
    corpus = "\n".join(timeline_lines) if timeline_lines else text
    dates = _DATE_RE.findall(corpus)
    registration = _date_near(corpus, ("inscricao", "inscricoes"))
    payment = _date_near(corpus, ("pagamento", "taxa", "boleto"))
    exam = _date_near(corpus, ("prova", "exame", "objetiva"))
    result = _date_near(corpus, ("resultado", "classificacao"))
    docs = _date_near(corpus, ("documento", "documentacao", "titulo"))
    return ExamTimeline(
        registration_start=registration[0] if registration else "",
        registration_end=registration[-1] if registration else "",
        payment_deadline=payment[-1] if payment else "",
        exam_date=exam[0] if exam else "",
        result_date=result[0] if result else "",
        appeal_deadlines=_date_near(corpus, ("recurso", "recursos")),
        document_submission_deadline=docs[-1] if docs else "",
        other_dates=_unique(dates)[:20],
    )


def _requirements(text: str, sections: dict[str, list[str]]) -> list[ExamRequirement]:
    req_lines = [*sections.get("requirements", []), *sections.get("general", [])]
    requirements: list[ExamRequirement] = []
    normalized = normalize_text(text)
    degree = _required_degree(text)
    if degree:
        requirements.append(_requirement("degree", degree, "Diploma/certificado compatível."))
    education = _education_level(text)
    if education:
        requirements.append(
            _requirement(
                "education",
                f"Escolaridade exigida: {education}",
                "Comprovante de escolaridade.",
            )
        )
    registry = _registry(text)
    if registry:
        requirements.append(
            _requirement(
                "professional_registry",
                f"Registro profissional exigido: {registry}",
                f"Registro ativo em {registry}.",
            )
        )
    experience = _required_experience(text)
    if experience:
        requirements.append(
            _requirement("experience", experience, "Evidência de experiência compatível.")
        )
    fixed = {
        "driver_license": (
            "cnh",
            "carteira nacional de habilitacao",
            "carteira nacional de habilitação",
        ),
        "nationality": ("nacionalidade brasileira", "brasileiro nato", "brasileiro naturalizado"),
        "electoral_status": (
            "obrigacoes eleitorais",
            "obrigações eleitorais",
            "quitacao eleitoral",
        ),
        "military_status": ("servico militar", "serviço militar", "quitacao militar"),
        "medical": ("avaliacao medica", "avaliação médica"),
        "physical_test": ("taf", "teste de aptidao fisica", "aptidão física"),
    }
    for kind, markers in fixed.items():
        if any(marker in normalized for marker in markers):
            requirements.append(
                _requirement(kind, _label_for_kind(kind), "Documento/evidência conforme edital.")
            )
    for line in req_lines:
        clean = _short(line)
        norm = normalize_text(clean)
        if len(clean) < 12:
            continue
        if any(
            marker in norm
            for marker in ("requisito", "exigir", "devera", "deverá", "comprovar", "documento")
        ):
            requirements.append(
                _requirement(_requirement_kind(norm), clean, "Evidência/documento conforme edital.")
            )
    return _dedupe_requirements(requirements)


def _documents(lines: list[str], text: str) -> list[str]:
    docs = []
    corpus = "\n".join(lines) if lines else text
    markers = (
        "documento de identidade",
        "cpf",
        "diploma",
        "certificado",
        "comprovante",
        "registro profissional",
        "titulo",
        "título",
        "laudo",
    )
    for line in corpus.splitlines():
        clean = _short(line)
        norm = normalize_text(clean)
        if any(marker in norm for marker in markers):
            docs.append(clean)
    return _unique(docs)[:40]


def _subjects(text: str, subject_lines: list[str]) -> list[ExamSubject]:
    corpus = subject_lines or [
        line.strip(" \t-•") for line in text.splitlines() if line.strip(" \t-•")
    ]
    subjects: list[ExamSubject] = []
    known = {
        "Língua Portuguesa": ("portugues", "língua portuguesa", "lingua portuguesa"),
        "Matemática": ("matematica", "matemática", "raciocinio logico", "raciocínio lógico"),
        "Informática": ("informatica", "informática", "tecnologia da informação"),
        "Conhecimentos Gerais": ("conhecimentos gerais", "atualidades"),
        "Conhecimentos Específicos": ("conhecimentos especificos", "conhecimentos específicos"),
        "Legislação": ("legislacao", "legislação"),
    }
    for name, aliases in known.items():
        matching = [
            line for line in corpus if any(alias in normalize_text(line) for alias in aliases)
        ]
        if matching:
            subjects.append(
                ExamSubject(
                    name=name,
                    topics=_topics_from_lines(matching),
                    stage="prova objetiva" if "prova" in normalize_text(text) else "",
                    priority="high" if name == "Conhecimentos Específicos" else "medium",
                    source_excerpt=_short(" | ".join(matching), 1200),
                )
            )
    return _dedupe_subjects(subjects)


def _warnings(text: str, notice: ExamNotice, roles: list[ExamRole]) -> list[str]:
    warnings = [OFFICIAL_NOTICE_WARNING]
    if len(text) < 600:
        warnings.append("Texto curto: o edital pode estar truncado ou incompleto.")
    if not notice.timeline.registration_end:
        warnings.append("Não encontrei data clara de fim de inscrição.")
    if not notice.timeline.exam_date:
        warnings.append("Não encontrei data clara de prova.")
    if not notice.general_requirements and not any(role.requirements for role in roles):
        warnings.append("Não encontrei requisitos claros; revise o edital oficial.")
    if len(roles) > 1:
        warnings.append("Detectei múltiplos cargos; revise qual cargo será analisado.")
    if not any(role.salary for role in roles) and not _salary(text):
        warnings.append("Salário, vencimento ou bolsa não foi identificado com clareza.")
    if not _fee(text):
        warnings.append("Taxa de inscrição não foi identificada com clareza.")
    if not notice.subjects:
        warnings.append("Conteúdo programático não foi identificado ou parece incompleto.")
    if text.endswith("...") or "[...]" in text:
        warnings.append("Texto possivelmente truncado; revise o edital completo.")
    return _unique(warnings)


def _requirement(
    kind: ExamRequirementKind | str,
    description: str,
    evidence_needed: str,
) -> ExamRequirement:
    safe_kind = str(kind) if str(kind) in _REQUIREMENT_KINDS else "other"
    return ExamRequirement(
        kind=cast(ExamRequirementKind, safe_kind),
        description=_short(description, 2000),
        mandatory=True,
        evidence_needed=evidence_needed,
        match_status="uncertain",
        confidence="high" if description else "medium",
    )


def _requirement_kind(normalized_line: str) -> ExamRequirementKind:
    if any(
        marker in normalized_line for marker in ("diploma", "graduacao", "escolaridade", "ensino")
    ):
        return "education"
    if any(
        marker in normalized_line
        for marker in ("registro", "crea", "coren", "crm", "oab", "crc", "cft")
    ):
        return "professional_registry"
    if "experiencia" in normalized_line or "experiência" in normalized_line:
        return "experience"
    if "cnh" in normalized_line or "habilitacao" in normalized_line:
        return "driver_license"
    if "documento" in normalized_line or "comprovante" in normalized_line:
        return "document"
    return "other"


def _required_degree(text: str) -> str:
    patterns = [
        r"(?:graduação|graduacao|bacharelado|licenciatura|curso superior)[^.\n;]{0,120}",
        r"(?:técnico|tecnico)\s+em\s+[^.\n;]{2,120}",
        r"(?:mestrado|doutorado|especialização|especializacao)[^.\n;]{0,120}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _short(match.group(0), 240)
    return ""


def _education_level(text: str) -> str:
    normalized = normalize_text(text)
    for label, aliases in _EDUCATION_LEVELS:
        if any(alias in normalized for alias in aliases):
            return label
    return ""


def _registry(text: str) -> str:
    return ", ".join(_unique(_REGISTRY_RE.findall(text)))


def _salary(text: str) -> str:
    return _first_match(_SALARY_RE, text) or _money_near(
        text,
        ("salario", "vencimento", "remuneracao", "bolsa"),
    )


def _fee(text: str) -> str:
    return _first_match(_FEE_RE, text) or _money_near(
        text,
        ("taxa de inscricao", "inscricao"),
    )


def _required_experience(text: str) -> str:
    match = re.search(r"(?:experiência|experiencia)[^.\n;]{0,160}", text, re.IGNORECASE)
    return _short(match.group(0), 500) if match else ""


def _certifications(text: str) -> list[str]:
    certs = []
    for line in text.splitlines():
        norm = normalize_text(line)
        if "certificacao" in norm or "certificação" in norm or "certificado" in norm:
            certs.append(_short(line))
    return _unique(certs)[:20]


def _reserved_vacancies(text: str) -> str:
    lines = [
        _short(line)
        for line in text.splitlines()
        if any(marker in normalize_text(line) for marker in ("reserva", "cotas", "pcd", "negros"))
    ]
    return " | ".join(lines[:3])[:240]


def _quota_notes(text: str) -> str:
    lines = [
        _short(line)
        for line in text.splitlines()
        if any(
            marker in normalize_text(line)
            for marker in ("cotas", "reserva de vagas", "pcd", "negros")
        )
    ]
    return " | ".join(lines[:5])[:1000]


def _employment_regime(text: str) -> str:
    normalized = normalize_text(text)
    if "estatutario" in normalized or "estatutário" in normalized:
        return "estatutário"
    if "clt" in normalized:
        return "CLT"
    if "bolsa" in normalized:
        return "bolsa"
    if "temporario" in normalized or "temporário" in normalized:
        return "temporário"
    return ""


def _locations(text: str) -> list[str]:
    return [_short(match.group(1), 240) for match in _LOCATION_RE.finditer(text)]


def _stages(text: str) -> list[str]:
    normalized = normalize_text(text)
    stages = []
    stage_map = {
        "prova objetiva": ("prova objetiva",),
        "prova discursiva/redação": ("prova discursiva", "redacao", "redação"),
        "prova prática": ("prova pratica", "prova prática"),
        "prova de títulos": ("prova de titulos", "prova de títulos", "avaliacao de titulos"),
        "TAF": ("taf", "aptidao fisica", "aptidão física"),
        "avaliação médica/psicológica": (
            "avaliacao medica",
            "avaliação médica",
            "psicologica",
            "psicológica",
        ),
    }
    for label, markers in stage_map.items():
        if any(marker in normalized for marker in markers):
            stages.append(label)
    return stages


def _date_near(text: str, markers: Iterable[str]) -> list[str]:
    dates: list[str] = []
    for line in text.splitlines():
        normalized = normalize_text(line)
        if any(marker in normalized for marker in markers):
            dates.extend(_DATE_RE.findall(line))
    return _unique(dates)


def _money_near(text: str, markers: Iterable[str]) -> str:
    money_re = re.compile(_MONEY, re.IGNORECASE)
    for line in text.splitlines():
        normalized = normalize_text(line)
        if any(marker in normalized for marker in markers):
            match = money_re.search(line)
            if match:
                return _short(match.group(0), 160)
    return ""


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(1) if match.groups() else match.group(0)
    return _short(value, 240)


def _clean_role_title(value: str) -> str:
    value = re.split(r"\s{2,}|\t|\||;", value)[0]
    value = re.sub(r"\b\d+\s+vagas?.*", "", value, flags=re.IGNORECASE)
    return _short(value, 240)


def _area_for(role_title: str) -> str:
    normalized = normalize_text(role_title)
    if any(marker in normalized for marker in ("professor", "docente", "educacao")):
        return "Educação"
    if any(marker in normalized for marker in ("enfermeiro", "medico", "saude", "psicologo")):
        return "Saúde"
    if any(marker in normalized for marker in ("engenheiro", "tecnico", "analista de sistemas")):
        return "Técnica/Engenharia"
    if any(marker in normalized for marker in ("administrativo", "assistente", "analista")):
        return "Administração"
    return ""


def _topics_from_lines(lines: list[str]) -> list[str]:
    topics: list[str] = []
    for line in lines:
        topics.extend(
            _short(part, 160) for part in re.split(r"[,;•]", line) if len(part.strip()) > 3
        )
    return _unique(topics)[:30]


def _source_excerpts(lines: list[str]) -> list[str]:
    interesting = []
    for line in lines:
        norm = normalize_text(line)
        if any(
            marker in norm
            for marker in (
                "edital",
                "cargo",
                "inscricao",
                "prova",
                "requisito",
                "conteudo",
                "salario",
                "taxa",
            )
        ):
            interesting.append(_short(line, 400))
    return _unique(interesting)[:12]


def _label_for_kind(kind: str) -> str:
    labels = {
        "driver_license": "CNH exigida no edital.",
        "nationality": "Nacionalidade brasileira ou regra equivalente.",
        "electoral_status": "Quitação eleitoral.",
        "military_status": "Quitação militar, quando aplicável.",
        "medical": "Avaliação médica prevista.",
        "physical_test": "Teste de aptidão física previsto.",
    }
    return labels.get(kind, "Requisito a revisar.")


def _dedupe_requirements(requirements: list[ExamRequirement]) -> list[ExamRequirement]:
    unique: list[ExamRequirement] = []
    seen: set[str] = set()
    for requirement in requirements:
        key = normalize_text(f"{requirement.kind} {requirement.description}")
        if key and key not in seen:
            seen.add(key)
            unique.append(requirement)
    return unique


def _dedupe_subjects(subjects: list[ExamSubject]) -> list[ExamSubject]:
    unique: list[ExamSubject] = []
    seen: set[str] = set()
    for subject in subjects:
        key = normalize_text(subject.name)
        if key and key not in seen:
            seen.add(key)
            unique.append(subject)
    return unique


def _short(value: str, limit: int = 500) -> str:
    return re.sub(r"\s+", " ", str(value)).strip(" :-\t")[:limit]


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _short(value)
        key = normalize_text(cleaned)
        if cleaned and key and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result
