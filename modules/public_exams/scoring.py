"""Fit scoring between public exam requirements and the Universal Career Profile."""

from __future__ import annotations

from modules.context.models import CareerContext
from modules.core.scoring import clamp_score
from modules.core.text_utils import normalize_text
from modules.profile.models import ProfileItem, UniversalCareerProfile

from .models import ExamFitScore, ExamNotice, ExamRecommendation, ExamRequirement, ExamRole


def score_exam_fit(
    notice: ExamNotice,
    role: ExamRole | None,
    profile: UniversalCareerProfile,
    context: CareerContext,
) -> ExamFitScore:
    """Return a conservative fit score; never claims absolute eligibility."""
    selected_role = role or (notice.roles[0] if notice.roles else None)
    requirements = _requirements(notice, selected_role)
    profile_items = [*profile.items, *profile.constraints]
    scored = [_match_requirement(req, profile_items, context) for req in requirements]
    matched = [req for req in scored if req.match_status == "matched"]
    missing = [req for req in scored if req.match_status == "missing"]
    uncertain = [req for req in scored if req.match_status == "uncertain"]
    requirement_score = _requirement_score(scored)
    timeline_score = 80 if notice.timeline.registration_end or notice.timeline.exam_date else 45
    location_score = _location_score(selected_role, profile)
    salary_score = 70 if selected_role and selected_role.salary else 50
    study_effort_score = _study_effort_score(selected_role or notice)
    profile_alignment_score = _profile_alignment_score(selected_role, profile, context)
    risk_score = clamp_score(
        (len(missing) * 22)
        + (len(uncertain) * 10)
        + (0 if notice.timeline.registration_end else 15)
        + (0 if notice.timeline.exam_date else 8)
    )
    overall = clamp_score(
        requirement_score * 0.38
        + timeline_score * 0.12
        + location_score * 0.1
        + salary_score * 0.08
        + study_effort_score * 0.12
        + profile_alignment_score * 0.2
        - risk_score * 0.12
    )
    warnings = [
        "Pontuação inicial: revise requisitos legais e edital oficial antes de decidir.",
        "O SotuHire não presume registro profissional, graduação concluída ou inscrição feita.",
    ]
    if missing:
        warnings.append("Há requisitos obrigatórios sem evidência no Perfil.")
    if uncertain:
        warnings.append("Há requisitos que precisam de confirmação manual.")
    return ExamFitScore(
        overall_score=overall,
        requirement_score=requirement_score,
        timeline_score=timeline_score,
        location_score=location_score,
        salary_score=salary_score,
        study_effort_score=study_effort_score,
        profile_alignment_score=profile_alignment_score,
        risk_score=risk_score,
        recommendation=_recommendation(overall, missing, uncertain),
        matched_requirements=matched,
        missing_requirements=missing,
        uncertain_requirements=uncertain,
        warnings=warnings,
    )


def _requirements(notice: ExamNotice, role: ExamRole | None) -> list[ExamRequirement]:
    items = []
    if role:
        items.extend(role.requirements)
    items.extend(notice.general_requirements)
    if not items and role:
        if role.required_degree:
            items.append(
                ExamRequirement(
                    kind="degree",
                    description=role.required_degree,
                    evidence_needed="Diploma/certificado compatível.",
                )
            )
        if role.required_registry:
            items.append(
                ExamRequirement(
                    kind="professional_registry",
                    description=role.required_registry,
                    evidence_needed="Registro profissional ativo.",
                )
            )
    unique: list[ExamRequirement] = []
    seen = set()
    for item in items:
        key = normalize_text(f"{item.kind} {item.description}")
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _match_requirement(
    requirement: ExamRequirement,
    profile_items: list[ProfileItem],
    context: CareerContext,
) -> ExamRequirement:
    corpus_items = [
        (
            item.item_id,
            normalize_text(
                " ".join(
                    [
                        item.type,
                        item.title,
                        item.evidence or "",
                        item.description or "",
                        item.status or "",
                    ]
                )
            ),
        )
        for item in profile_items
        if item.confirmed_by_user
    ]
    context_titles = normalize_text(
        " ".join([item.title + " " + item.content for item in context.evidence])
    )
    req_text = normalize_text(requirement.description)
    matched_ids: list[str] = []
    status = "uncertain"
    warnings = list(requirement.warnings)
    if requirement.kind in {
        "professional_registry",
        "degree",
        "education",
        "certification",
        "experience",
    }:
        for item_id, corpus in corpus_items:
            if _matches(req_text, corpus, requirement.kind):
                matched_ids.append(item_id)
        if matched_ids:
            status = "matched"
        elif _context_suggests(req_text, context_titles, requirement.kind):
            status = "uncertain"
            warnings.append("Há sinal no contexto, mas falta evidência confirmada no Perfil.")
        else:
            status = "missing" if requirement.mandatory else "uncertain"
    elif any(_loose_overlap(req_text, corpus) for _, corpus in corpus_items):
        status = "matched"
    elif requirement.mandatory:
        status = "uncertain"
    return requirement.model_copy(
        update={
            "matched_profile_item_ids": matched_ids,
            "match_status": status,
            "warnings": warnings,
        }
    )


def _matches(req_text: str, corpus: str, kind: str) -> bool:
    if kind == "professional_registry":
        councils = ("crea", "cft", "crq", "coren", "crp", "crm", "oab", "crc", "cau", "crmv")
        return any(council in req_text and council in corpus for council in councils)
    if kind in {"degree", "education"}:
        concluded = any(
            marker in corpus
            for marker in (
                "concluido",
                "concluído",
                "diploma",
                "bacharel",
                "licenciatura",
                "tecnologo",
                "tecnólogo",
                "superior",
            )
        )
        if "superior" in req_text or "graduacao" in req_text or "graduação" in req_text:
            return concluded and "andamento" not in corpus
        return _loose_overlap(req_text, corpus)
    if kind == "experience":
        return (
            "experiencia" in corpus or "experiência" in corpus or _loose_overlap(req_text, corpus)
        )
    if kind == "certification":
        return "certificacao" in corpus or "certificação" in corpus or "certificado" in corpus
    return _loose_overlap(req_text, corpus)


def _context_suggests(req_text: str, context_titles: str, kind: str) -> bool:
    if not context_titles:
        return False
    if kind == "professional_registry":
        return any(
            council in req_text and council in context_titles
            for council in ("crea", "coren", "crm", "oab", "crc", "cft")
        )
    return _loose_overlap(req_text, context_titles)


def _loose_overlap(left: str, right: str) -> bool:
    left_tokens = {token for token in _split(left) if len(token) >= 4}
    if not left_tokens:
        return False
    right_tokens = {token for token in _split(right) if len(token) >= 4}
    return len(left_tokens.intersection(right_tokens)) >= 2


def _split(value: str) -> list[str]:
    return [part for part in value.replace("/", " ").replace("-", " ").split() if part]


def _requirement_score(requirements: list[ExamRequirement]) -> int:
    if not requirements:
        return 35
    points = 0
    for requirement in requirements:
        if requirement.match_status == "matched":
            points += 100
        elif requirement.match_status == "uncertain":
            points += 55
    return clamp_score(points / len(requirements))


def _location_score(role: ExamRole | None, profile: UniversalCareerProfile) -> int:
    if not role or not role.location:
        return 60
    desired = normalize_text(" ".join(profile.preferred_locations))
    location = normalize_text(role.location)
    if desired and (location in desired or desired in location):
        return 90
    return 55


def _study_effort_score(target: ExamRole | ExamNotice) -> int:
    subjects = target.subjects
    if not subjects:
        return 45
    total_topics = sum(len(subject.topics) for subject in subjects)
    if total_topics <= 10:
        return 80
    if total_topics <= 30:
        return 65
    return 45


def _profile_alignment_score(
    role: ExamRole | None,
    profile: UniversalCareerProfile,
    context: CareerContext,
) -> int:
    goals = normalize_text(
        " ".join(
            [*profile.target_roles, *profile.primary_domains, *context.goals, *context.domains]
        )
    )
    title = normalize_text(role.title if role else "")
    if title and _loose_overlap(title, goals):
        return 85
    if context.evidence:
        return 65
    return 45


def _recommendation(
    overall: int,
    missing: list[ExamRequirement],
    uncertain: list[ExamRequirement],
) -> ExamRecommendation:
    if not missing and overall >= 82:
        return "strong_fit"
    if not missing and overall >= 68:
        return "good_fit"
    if missing and overall < 45:
        return "not_recommended"
    if len(missing) >= 2:
        return "risky"
    if uncertain or missing:
        return "review_requirements"
    return "insufficient_information"
