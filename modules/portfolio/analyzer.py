"""Deterministic GitHub, repository, project, and portfolio analyzer."""

from __future__ import annotations

from modules.core.text_utils import normalize_text
from modules.portfolio.commit_analysis import analyze_commits
from modules.portfolio.file_sampler import prioritize_paths
from modules.portfolio.schemas import ProjectAnalysisPayload, ProjectAnalysisReport

STACK_SIGNALS = {
    "Python": ("python", "pyproject.toml", "requirements.txt"),
    "JavaScript": ("javascript", "package.json", ".js"),
    "TypeScript": ("typescript", "tsconfig", ".ts"),
    "Docker": ("dockerfile", "docker-compose"),
    "GitHub Actions": (".github/workflows", "github actions"),
    "SQL": ("sql", "postgres", "mysql", "sqlite"),
    "React": ("react", "next.js", "nextjs"),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Streamlit": ("streamlit",),
    "Tests": ("pytest", "jest", "tests/"),
}


def analyze_project(payload: ProjectAnalysisPayload) -> ProjectAnalysisReport:
    """Build a transparent local report from public captured project signals."""
    sampled = prioritize_paths(payload.files_sampled)
    corpus = normalize_text(
        " ".join(
            [
                payload.title,
                payload.visible_text,
                payload.readme_text,
                *sampled,
                *payload.languages,
                *payload.topics,
            ]
        )
    )
    stack = list(
        dict.fromkeys(
            [
                *payload.languages,
                *[
                    label
                    for label, signals in STACK_SIGNALS.items()
                    if any(normalize_text(signal) in corpus for signal in signals)
                ],
            ]
        )
    )
    commits = analyze_commits(payload.commit_messages)
    documentation = _score_documentation(payload.readme_text, sampled, corpus)
    architecture = _score_architecture(sampled)
    technical_depth = _clamp(30 + len(stack) * 7 + min(len(sampled), 20) * 2)
    tests_score = 80 if any(path.casefold().startswith("tests/") for path in sampled) else 30
    repository = _average(documentation, architecture, technical_depth, tests_score)
    profile = _clamp(40 + len(payload.languages) * 8 + len(payload.topics) * 4)
    portfolio = _average(documentation, repository, commits.professionalism_score)
    project_quality = _average(repository, technical_depth, commits.maintenance_signal_score)
    recruiter = _average(documentation, commits.professionalism_score, technical_depth)
    evidence = _clamp(35 + len(stack) * 6 + min(len(payload.readme_text) // 300, 20))
    overall = _average(repository, portfolio, recruiter, evidence)
    strengths = _strengths(documentation, architecture, tests_score, commits, stack)
    weaknesses = _weaknesses(documentation, architecture, tests_score, commits, stack)
    recommendations = _recommendations(weaknesses)
    title = payload.title or payload.repo or payload.owner or "Projeto capturado"
    return ProjectAnalysisReport(
        url=payload.url,
        title=title,
        owner=payload.owner,
        repo=payload.repo,
        page_type=payload.page_type,
        provider_used=payload.provider_used,
        overall_score=overall,
        grade=_grade(overall),
        github_profile_score=profile,
        repository_quality_score=repository,
        portfolio_score=portfolio,
        project_quality_score=project_quality,
        recruiter_readiness_score=recruiter,
        documentation_score=documentation,
        commit_quality_score=commits.commit_quality_score,
        architecture_signal_score=architecture,
        technical_depth_score=technical_depth,
        ats_job_evidence_score=evidence,
        summary=(
            f"{title} recebeu nota {overall}/100. "
            f"Foram detectadas {len(stack)} tecnologias e {len(sampled)} arquivos centrais."
        ),
        stack=stack,
        strengths=strengths,
        weaknesses=weaknesses,
        risks=weaknesses[:4],
        relevant_projects=[title] if overall >= 60 else [],
        improvement_projects=[title] if overall < 60 else [],
        priority_recommendations=recommendations,
        technical_keywords=stack,
        resume_highlights=[
            f"Projeto {title}: {', '.join(stack[:6])} com documentação e arquitetura verificáveis."
        ]
        if stack
        else [],
        files_sampled=sampled,
        commit_analysis=commits,
    )


def _score_documentation(readme: str, paths: list[str], corpus: str) -> int:
    score = 20
    if readme.strip():
        score += min(45, len(readme.strip()) // 80)
    if any(path.casefold().startswith("docs/") for path in paths):
        score += 15
    if any(term in corpus for term in ("instalacao", "installation", "uso", "usage", "setup")):
        score += 15
    return _clamp(score)


def _score_architecture(paths: list[str]) -> int:
    prefixes = {"src", "app", "modules", "tests", "docs", ".github"}
    present = {path.split("/", 1)[0].casefold() for path in paths}
    return _clamp(25 + len(prefixes & present) * 12 + min(len(paths), 20))


def _strengths(documentation: int, architecture: int, tests: int, commits, stack: list[str]):
    output = []
    if documentation >= 65:
        output.append("Documentação útil para entendimento e uso.")
    if architecture >= 65:
        output.append("Estrutura do projeto transmite organização.")
    if tests >= 65:
        output.append("Há sinais visíveis de testes.")
    if commits.commit_quality_score >= 65:
        output.append("Mensagens de commit comunicam mudanças com clareza.")
    if stack:
        output.append("Stack técnica detectável e rastreável.")
    return output


def _weaknesses(documentation: int, architecture: int, tests: int, commits, stack: list[str]):
    output = []
    if documentation < 65:
        output.append("README/documentação precisa explicar melhor instalação, uso e decisões.")
    if architecture < 60:
        output.append("Estrutura do projeto oferece poucos sinais arquiteturais.")
    if tests < 60:
        output.append("Não foram encontrados sinais suficientes de testes.")
    if commits.commit_quality_score < 60:
        output.append("Mensagens de commit podem ser mais específicas e consistentes.")
    if not stack:
        output.append("Stack técnica pouco evidente na página analisada.")
    return output


def _recommendations(weaknesses: list[str]) -> list[str]:
    return [f"Prioridade {index + 1}: {weakness}" for index, weakness in enumerate(weaknesses[:5])]


def _average(*values: int) -> int:
    return round(sum(values) / len(values))


def _grade(score: int) -> str:
    return (
        "A"
        if score >= 85
        else "B"
        if score >= 70
        else "C"
        if score >= 55
        else "D"
        if score >= 40
        else "F"
    )


def _clamp(value: int) -> int:
    return max(0, min(100, value))
