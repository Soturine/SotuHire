"""GitHub Analyzer 2 orchestration service."""

from __future__ import annotations

from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.providers.base import AIProvider
from modules.github_analyzer.context_builder import build_analysis_context, summarize_selected_files
from modules.github_analyzer.dependency_graph import build_dependency_graph
from modules.github_analyzer.evidence_index import EvidenceItem, build_evidence_index
from modules.github_analyzer.exceptions import GitHubAnalyzerError
from modules.github_analyzer.file_sampler import select_repository_files
from modules.github_analyzer.github_client import GitHubClient
from modules.github_analyzer.repository_models import (
    RepositoryAnalysisInput,
    RepositoryDetectedSignals,
    RepositoryIdentity,
    RepositoryMetadata,
    RepositoryTree,
    RepositoryTreeEntry,
    SelectedRepositoryFile,
)
from modules.github_analyzer.schemas import (
    ArchitectureAssessment,
    DimensionScores,
    ExecutiveSummary,
    FinalVerdict,
    GitHubAnalyzerReport,
    GitHubRepoAnalysisOutput,
    ImportantModule,
    PortfolioValueAssessment,
    RepositoryIdentityAssessment,
    ResumeEvidenceAssessment,
    SafeResumeBullet,
    SecurityAssessment,
    SecurityFlag,
    SkillEvidence,
    TechnologyEvidence,
    TechStackAssessment,
)
from modules.github_analyzer.scoring import calculate_scores, infer_dimension_scores
from modules.github_analyzer.tree_builder import build_directory_tree, detect_repository_signals
from modules.portfolio.commit_analysis import analyze_commits
from modules.portfolio.schemas import ProjectAnalysisPayload, ProjectAnalysisReport


def analyze_github_repository(
    value: str,
    *,
    client: GitHubClient | None = None,
    provider: AIProvider | None = None,
    analysis_input: RepositoryAnalysisInput | None = None,
    fallback_payload: ProjectAnalysisPayload | None = None,
) -> GitHubAnalyzerReport:
    """Analyze a public GitHub repository with API evidence and safe fallbacks."""
    github = client or GitHubClient()
    context = analysis_input or RepositoryAnalysisInput()
    try:
        identity = github.repository_identity(value)
        metadata = github.get_metadata(identity.owner, identity.name)
        ref = metadata.identity.ref_sha or metadata.identity.default_branch or "HEAD"
        tree = github.get_tree(identity.owner, identity.name, ref)
        directory_tree = build_directory_tree(tree)
        signals = detect_repository_signals(tree)
        selected = select_repository_files(tree)
        fetched = _fetch_selected_files(github, metadata, selected, ref)
        dependency_graph = build_dependency_graph(fetched)
        payload = build_analysis_context(
            metadata=metadata,
            directory_tree=directory_tree,
            selected_files=fetched,
            detected_signals=signals,
            dependency_graph=dependency_graph,
            analysis_input=context,
        )
        evidence = build_evidence_index(
            metadata=metadata,
            signals=signals,
            selected_files=fetched,
            dependency_graph=dependency_graph,
        )
        provider_output = _run_provider(provider, payload)
        dimensions = (
            provider_output.dimension_scores
            if provider_output
            else infer_dimension_scores(
                metadata=metadata,
                signals=signals,
                selected_files=fetched,
                dependency_graph=dependency_graph,
                analysis_input=context,
            )
        )
        return _build_report(
            metadata=metadata,
            signals=signals,
            selected_files=fetched,
            evidence=evidence,
            dimensions=dimensions,
            provider_output=provider_output,
            fallback_used=False,
            provider_used=provider.name if provider_output and provider else "local",
        )
    except GitHubAnalyzerError as exc:
        if fallback_payload is None:
            raise
        return _fallback_report(fallback_payload, str(exc))


def project_report_from_github_analysis(
    report: GitHubAnalyzerReport,
    payload: ProjectAnalysisPayload,
) -> ProjectAnalysisReport:
    """Convert a deep GitHub report to the legacy extension-safe project report."""
    commit_analysis = analyze_commits(payload.commit_messages)
    stack = _flatten_stack(report.tech_stack)
    bullets = [bullet.bullet for bullet in report.resume_evidence.safe_resume_bullets]
    risks = [
        flag.description
        for flag in report.security.security_flags
        if flag.severity in {"high", "critical"}
    ]
    weaknesses = [
        *report.final_verdict.main_blockers,
        *report.inconsistencies,
    ] or report.portfolio_value.career_weaknesses
    title = payload.title or report.repository_identity.name or payload.repo or "Projeto GitHub"
    return ProjectAnalysisReport(
        url=payload.url or report.repository_identity.url,
        title=title,
        owner=report.repository_identity.owner,
        repo=report.repository_identity.name,
        page_type="github_repo",
        provider_used=report.provider_used,
        overall_score=report.scores.overall_score,
        grade=report.scores.grade,
        github_profile_score=report.scores.portfolio_score,
        repository_quality_score=report.scores.technical_score,
        portfolio_score=report.scores.portfolio_score,
        project_quality_score=report.scores.technical_score,
        recruiter_readiness_score=report.scores.recruiter_readiness_score,
        documentation_score=report.scores.documentation_score,
        commit_quality_score=commit_analysis.commit_quality_score,
        architecture_signal_score=report.dimension_scores.architecture * 10,
        technical_depth_score=report.dimension_scores.code_quality * 10,
        ats_job_evidence_score=report.scores.resume_evidence_score,
        summary=report.executive_summary.short_summary,
        stack=stack,
        strengths=report.portfolio_value.career_strengths,
        weaknesses=weaknesses,
        risks=risks or weaknesses[:4],
        relevant_projects=[title] if report.scores.overall_score >= 60 else [],
        improvement_projects=[title] if report.scores.overall_score < 70 else [],
        priority_recommendations=report.recommendations or report.final_verdict.next_3_actions,
        technical_keywords=stack,
        resume_highlights=bullets,
        files_sampled=report.files_sampled,
        commit_analysis=commit_analysis,
    )


def _fetch_selected_files(
    client: GitHubClient,
    metadata: RepositoryMetadata,
    selected: list[SelectedRepositoryFile],
    ref: str,
) -> list[SelectedRepositoryFile]:
    fetched: list[SelectedRepositoryFile] = []
    for file in selected:
        try:
            fetched.append(
                client.fetch_file(
                    metadata.identity.owner,
                    metadata.identity.name,
                    ref,
                    file,
                )
            )
        except GitHubAnalyzerError:
            fetched.append(file)
    return fetched


def _run_provider(
    provider: AIProvider | None,
    payload: dict[str, object],
) -> GitHubRepoAnalysisOutput | None:
    if provider is None:
        return None
    try:
        spec = default_prompt_registry().get("github_repo_analysis_v2")
        output = provider.generate_structured(spec, payload)
        return GitHubRepoAnalysisOutput.model_validate(output)
    except Exception:
        return None


def _build_report(
    *,
    metadata: RepositoryMetadata,
    signals: RepositoryDetectedSignals,
    selected_files: list[SelectedRepositoryFile],
    evidence: list[EvidenceItem],
    dimensions: DimensionScores,
    provider_output: GitHubRepoAnalysisOutput | None,
    fallback_used: bool,
    provider_used: str,
) -> GitHubAnalyzerReport:
    deterministic = _deterministic_output(metadata, signals, selected_files, evidence, dimensions)
    output = _merge_provider_output(deterministic, provider_output)
    scores = calculate_scores(
        dimensions=output.dimension_scores,
        signals=signals,
        evidence_index=evidence,
        selected_files=selected_files,
    )
    return GitHubAnalyzerReport(
        repository_identity=output.repository_identity,
        executive_summary=output.executive_summary,
        dimension_scores=output.dimension_scores,
        score_explanation=[
            "Scores finais foram calculados por código a partir das dimensões e travas de calibração.",
            *scores.applied_caps,
        ],
        tech_stack=output.tech_stack,
        architecture=output.architecture,
        security=output.security,
        documentation=_documentation_notes(signals),
        testing=_testing_notes(signals),
        portfolio_value=output.portfolio_value,
        resume_evidence=output.resume_evidence,
        job_alignment=_job_alignment_notes(output.dimension_scores.job_alignment),
        inconsistencies=output.inconsistencies,
        recommendations=output.recommendations or output.final_verdict.next_3_actions,
        evidence_index=evidence or output.evidence_index,
        files_sampled=summarize_selected_files(selected_files),
        final_verdict=output.final_verdict,
        scores=scores,
        provider_used=provider_used,
        fallback_used=fallback_used,
    )


def _deterministic_output(
    metadata: RepositoryMetadata,
    signals: RepositoryDetectedSignals,
    selected_files: list[SelectedRepositoryFile],
    evidence: list[EvidenceItem],
    dimensions: DimensionScores,
) -> GitHubRepoAnalysisOutput:
    identity = RepositoryIdentityAssessment(
        owner=metadata.identity.owner,
        name=metadata.identity.name,
        url=metadata.identity.url,
        project_type=_project_type(metadata, selected_files),
        detected_domains=_detected_domains(metadata, selected_files),
        confidence=0.85 if selected_files else 0.55,
    )
    stack = _tech_stack(metadata, selected_files)
    architecture = _architecture(signals, selected_files)
    security = _security(evidence, signals)
    portfolio = _portfolio_value(stack, selected_files, signals)
    resume = _resume_evidence(metadata, stack, selected_files)
    verdict = _verdict(dimensions, signals, security)
    return GitHubRepoAnalysisOutput(
        repository_identity=identity,
        executive_summary=_summary(metadata, dimensions, signals),
        dimension_scores=dimensions,
        tech_stack=stack,
        architecture=architecture,
        portfolio_value=portfolio,
        resume_evidence=resume,
        security=security,
        evidence_index=evidence,
        final_verdict=verdict,
        inconsistencies=_inconsistencies(signals),
        recommendations=_recommendations(signals, dimensions),
        confidence_score=0.8 if selected_files else 0.5,
    )


def _merge_provider_output(
    deterministic: GitHubRepoAnalysisOutput,
    provider_output: GitHubRepoAnalysisOutput | None,
) -> GitHubRepoAnalysisOutput:
    if provider_output is None:
        return deterministic
    return provider_output.model_copy(
        update={
            "evidence_index": provider_output.evidence_index or deterministic.evidence_index,
            "recommendations": provider_output.recommendations or deterministic.recommendations,
            "confidence_score": min(provider_output.confidence_score or 0.0, 0.95),
        }
    )


def _fallback_report(payload: ProjectAnalysisPayload, reason: str) -> GitHubAnalyzerReport:
    identity = RepositoryIdentity(
        owner=payload.owner,
        name=payload.repo or payload.title or "unknown",
        url=payload.url,
        default_branch="",
        ref_sha="",
    )
    entries = [RepositoryTreeEntry(path=path, type="blob") for path in payload.files_sampled]
    metadata = RepositoryMetadata(
        identity=identity,
        description=payload.visible_text[:500],
        topics=payload.topics,
        languages={language: 1 for language in payload.languages},
    )
    tree = RepositoryTree(entries=entries, truncated=False, ref="")
    selected = [
        SelectedRepositoryFile(
            path=path,
            content=payload.readme_text if path.casefold().endswith("readme.md") else "",
            reason_selected="fallback",
            fetched=bool(payload.readme_text and path.casefold().endswith("readme.md")),
        )
        for path in payload.files_sampled[:30]
    ]
    signals = detect_repository_signals(tree)
    graph = build_dependency_graph(selected)
    evidence = build_evidence_index(
        metadata=metadata,
        signals=signals,
        selected_files=selected,
        dependency_graph=graph,
    )
    dimensions = infer_dimension_scores(
        metadata=metadata,
        signals=signals,
        selected_files=selected,
        dependency_graph=graph,
    )
    report = _build_report(
        metadata=metadata,
        signals=signals,
        selected_files=selected,
        evidence=evidence,
        dimensions=dimensions,
        provider_output=None,
        fallback_used=True,
        provider_used="local-fallback",
    )
    return report.model_copy(
        update={
            "score_explanation": [
                *report.score_explanation,
                f"GitHub API unavailable; used captured extension signals. Reason: {reason}",
            ],
            "fallback_used": True,
        }
    )


def _summary(
    metadata: RepositoryMetadata,
    dimensions: DimensionScores,
    signals: RepositoryDetectedSignals,
) -> ExecutiveSummary:
    repo = f"{metadata.identity.owner}/{metadata.identity.name}"
    limitations = []
    if signals.tree_truncated:
        limitations.append("A árvore do GitHub veio truncada.")
    if not signals.has_tests:
        limitations.append("Testes não foram encontrados na árvore analisada.")
    return ExecutiveSummary(
        short_summary=(
            f"{repo} tem nota técnica inicial {dimensions.architecture + dimensions.code_quality}/20 "
            f"e {len(metadata.languages)} linguagem(ns) detectada(s)."
        ),
        professional_summary=metadata.description
        or "Repositório analisado por estrutura e arquivos selecionados.",
        recruiter_summary="Use como evidência apenas os pontos com arquivos-fonte no índice de evidências.",
        limitations=limitations,
    )


def _tech_stack(
    metadata: RepositoryMetadata, files: list[SelectedRepositoryFile]
) -> TechStackAssessment:
    languages = list(
        dict.fromkeys(
            [
                *metadata.languages.keys(),
                *[file.language_hint for file in files if file.language_hint],
            ]
        )
    )
    detected = [
        TechnologyEvidence(
            technology=file.language_hint,
            evidence_file=file.path,
            confidence=0.72,
        )
        for file in files
        if file.language_hint
    ][:30]
    content = "\n".join(file.content.casefold() for file in files if file.content)
    frameworks = _detect_terms(
        content,
        {
            "FastAPI": "fastapi",
            "Django": "django",
            "Flask": "flask",
            "React": "react",
            "Next.js": "next",
            "Streamlit": "streamlit",
            "Express": "express",
        },
    )
    tools = _detect_terms(content, {"Ruff": "ruff", "Pytest": "pytest", "MkDocs": "mkdocs"})
    devops = _detect_terms(content, {"Docker": "docker", "GitHub Actions": "github"})
    return TechStackAssessment(
        languages=[language for language in languages if language],
        frameworks=frameworks,
        tools=tools,
        devops=devops,
        testing_tools=[tool for tool in tools if tool in {"Pytest"}],
        detected_from_files=detected,
    )


def _architecture(
    signals: RepositoryDetectedSignals,
    files: list[SelectedRepositoryFile],
) -> ArchitectureAssessment:
    source_files = [
        file for file in files if file.reason_selected in {"source", "dependency_central"}
    ]
    rating = (
        "good"
        if len(source_files) >= 5 and signals.has_tests
        else "fair"
        if source_files
        else "unclear"
    )
    modules = [
        ImportantModule(
            path=file.path, role=file.reason_selected, evidence="Arquivo selecionado para análise."
        )
        for file in source_files[:10]
    ]
    positives = []
    if signals.has_ci:
        positives.append("CI detectado na árvore.")
    if signals.has_tests:
        positives.append("Testes detectados na árvore.")
    if signals.has_package_manifest:
        positives.append("Manifestos de dependência/build detectados.")
    problems = [] if positives else ["Poucos sinais estruturais foram detectados."]
    return ArchitectureAssessment(
        rating=rating,
        style="modular" if any("/" in file.path for file in source_files) else "unknown",
        entry_points=[
            file.path
            for file in files
            if file.path.rsplit("/", 1)[-1] in {"app.py", "main.py", "index.js"}
        ],
        important_modules=modules,
        positive_signals=positives,
        problems=problems,
        improvement_suggestions=_architecture_suggestions(signals),
    )


def _portfolio_value(
    stack: TechStackAssessment,
    files: list[SelectedRepositoryFile],
    signals: RepositoryDetectedSignals,
) -> PortfolioValueAssessment:
    evidence_files = [
        file.path for file in files if file.reason_selected in {"source", "config", "readme"}
    ]
    skills = [
        SkillEvidence(
            skill=technology,
            category="language",
            evidence_files=[
                item.evidence_file
                for item in stack.detected_from_files
                if item.technology == technology
            ][:5],
            confidence=0.72,
        )
        for technology in stack.languages[:10]
    ]
    strengths = []
    if stack.languages:
        strengths.append("Stack técnica rastreável por arquivos do repositório.")
    if signals.has_readme:
        strengths.append("README ajuda recrutadores a entenderem o projeto.")
    weaknesses = []
    if not signals.has_tests:
        weaknesses.append("Adicionar testes melhoraria valor de portfólio.")
    if not signals.has_ci:
        weaknesses.append("CI simples deixaria manutenção mais demonstrável.")
    return PortfolioValueAssessment(
        best_fit_roles=_best_fit_roles(stack),
        skills_demonstrated=[skill for skill in skills if skill.evidence_files],
        career_strengths=strengths,
        career_weaknesses=weaknesses,
        how_to_present_in_interview=[
            f"Explique decisões usando evidências em {path}." for path in evidence_files[:3]
        ],
    )


def _resume_evidence(
    metadata: RepositoryMetadata,
    stack: TechStackAssessment,
    files: list[SelectedRepositoryFile],
) -> ResumeEvidenceAssessment:
    source_paths = [
        file.path
        for file in files
        if file.reason_selected in {"source", "dependency_central", "config", "workflow"}
    ][:6]
    technologies = _flatten_stack(stack)[:6]
    bullets = []
    if source_paths and technologies:
        bullets.append(
            SafeResumeBullet(
                bullet=(
                    f"Desenvolveu projeto {metadata.identity.name} com "
                    f"{', '.join(technologies[:4])}, com evidências versionadas no GitHub."
                ),
                supported_by=source_paths,
                confidence=0.78,
                risk_of_overclaiming="low",
            )
        )
    return ResumeEvidenceAssessment(
        safe_resume_bullets=bullets,
        skills_to_add_if_true=technologies,
        do_not_claim=[
            "Emprego, usuários reais, métricas de produção ou certificações sem evidência explícita."
        ],
    )


def _security(
    evidence: list[EvidenceItem], signals: RepositoryDetectedSignals
) -> SecurityAssessment:
    flags = [
        SecurityFlag(
            severity="critical",
            type="secret",
            description=item.claim,
            evidence_file=item.source_file,
            recommendation="Remover o segredo do histórico e rotacionar a credencial.",
        )
        for item in evidence
        if "secret" in item.claim.casefold()
    ]
    positives = []
    if signals.has_security_policy:
        positives.append("Arquivo ou configuração de segurança detectada.")
    if signals.has_env_example:
        positives.append("Exemplo de ambiente sugere separação de configuração.")
    risk = "critical" if flags else "low" if positives else "unclear"
    return SecurityAssessment(
        risk_level=risk,
        security_flags=flags,
        positive_security_signals=positives,
    )


def _verdict(
    dimensions: DimensionScores,
    signals: RepositoryDetectedSignals,
    security: SecurityAssessment,
) -> FinalVerdict:
    blockers = []
    if security.risk_level == "critical":
        blockers.append("Resolver possível segredo exposto antes de usar como portfólio.")
    if not signals.has_readme:
        blockers.append("Adicionar README com objetivo, setup e uso.")
    if not signals.has_tests and dimensions.tests <= 3:
        blockers.append("Adicionar testes ou documentar estratégia de validação.")
    return FinalVerdict(
        is_portfolio_ready=not blockers and dimensions.portfolio_value >= 6,
        main_blockers=blockers,
        next_3_actions=_next_actions(signals, security)[:3],
        one_sentence_verdict="Repositório pronto para portfólio."
        if not blockers
        else "Repositório útil, mas ainda precisa de ajustes antes de virar evidência forte.",
    )


def _documentation_notes(signals: RepositoryDetectedSignals) -> list[str]:
    notes = []
    if signals.has_readme:
        notes.append("README detectado.")
    if signals.has_docs:
        notes.append("Arquivos de documentação detectados.")
    if signals.has_license:
        notes.append("Licença detectada.")
    return notes or ["Documentação não encontrada na árvore analisada."]


def _testing_notes(signals: RepositoryDetectedSignals) -> list[str]:
    return (
        [f"Teste detectado: {path}" for path in signals.test_paths[:8]]
        if signals.has_tests
        else ["Testes não encontrados na árvore analisada."]
    )


def _job_alignment_notes(score: int) -> list[str]:
    if score >= 7:
        return ["O repositório possui sinais fortes para a vaga ou cargo alvo informado."]
    if score >= 5:
        return ["O repositório tem sinais parcialmente alinhados, mas exige revisão humana."]
    return ["Não há contexto suficiente para afirmar alinhamento com vaga específica."]


def _inconsistencies(signals: RepositoryDetectedSignals) -> list[str]:
    items = []
    if signals.has_dependency_lock and not signals.has_package_manifest:
        items.append("Lock file detectado sem manifesto correspondente na árvore filtrada.")
    if signals.tree_truncated:
        items.append("A árvore truncada pode ocultar arquivos relevantes.")
    return items


def _recommendations(signals: RepositoryDetectedSignals, dimensions: DimensionScores) -> list[str]:
    actions = _next_actions(signals, SecurityAssessment())
    if (
        dimensions.documentation < 6
        and "Melhorar README com objetivo, setup, uso e decisões." not in actions
    ):
        actions.append("Melhorar README com objetivo, setup, uso e decisões.")
    return actions[:5]


def _next_actions(signals: RepositoryDetectedSignals, security: SecurityAssessment) -> list[str]:
    actions = []
    if security.risk_level == "critical":
        actions.append("Remover segredos expostos e rotacionar credenciais.")
    if not signals.has_readme:
        actions.append("Criar README com objetivo, setup, uso e exemplos.")
    if not signals.has_tests:
        actions.append("Adicionar testes mínimos ou uma seção explicando validação.")
    if not signals.has_ci:
        actions.append("Adicionar workflow simples de CI.")
    if not signals.has_license:
        actions.append("Adicionar licença quando o projeto for público.")
    return actions or ["Manter evidências atualizadas e conectar o projeto a vagas-alvo."]


def _architecture_suggestions(signals: RepositoryDetectedSignals) -> list[str]:
    suggestions = []
    if not signals.has_tests:
        suggestions.append("Adicionar testes para comprovar comportamento.")
    if not signals.has_ci:
        suggestions.append("Adicionar CI para validar mudanças.")
    if not signals.has_package_manifest:
        suggestions.append("Adicionar manifesto de dependências/build quando aplicável.")
    return suggestions


def _project_type(metadata: RepositoryMetadata, files: list[SelectedRepositoryFile]) -> str:
    corpus = " ".join([metadata.description, *[file.path for file in files]]).casefold()
    if "extension" in corpus or "manifest.json" in corpus:
        return "extension"
    if "api" in corpus or "fastapi" in corpus or "express" in corpus:
        return "api"
    if "streamlit" in corpus or "react" in corpus or "app.py" in corpus:
        return "web_app"
    if "cli" in corpus:
        return "cli"
    return "unknown"


def _detected_domains(
    metadata: RepositoryMetadata, files: list[SelectedRepositoryFile]
) -> list[str]:
    corpus = " ".join(
        [metadata.description, *metadata.topics, *[file.path for file in files]]
    ).casefold()
    domains = []
    if any(term in corpus for term in ("security", "cyber", "auth")):
        domains.append("cybersecurity")
    if any(term in corpus for term in ("data", "ml", "analytics")):
        domains.append("data")
    if any(term in corpus for term in ("job", "career", "resume", "ats")):
        domains.append("career")
    if metadata.languages:
        domains.append("software")
    return list(dict.fromkeys(domains or ["general"]))


def _detect_terms(content: str, mapping: dict[str, str]) -> list[str]:
    return [label for label, needle in mapping.items() if needle in content]


def _best_fit_roles(stack: TechStackAssessment) -> list[str]:
    labels = set(_flatten_stack(stack))
    roles = []
    if {"Python", "FastAPI", "Django", "Flask"} & labels:
        roles.append("Backend Python")
    if {"React", "TypeScript", "JavaScript", "Next.js"} & labels:
        roles.append("Frontend/Web")
    if {"Docker", "GitHub Actions"} & labels:
        roles.append("DevOps/Platform júnior")
    return roles or ["Projeto técnico generalista"]


def _flatten_stack(stack: TechStackAssessment) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *stack.languages,
                *stack.frameworks,
                *stack.libraries,
                *stack.tools,
                *stack.databases,
                *stack.devops,
                *stack.testing_tools,
            ]
        )
    )
