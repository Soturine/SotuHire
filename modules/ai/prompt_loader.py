"""Initial structured prompt definitions for v0.10."""

from __future__ import annotations

from pydantic import BaseModel

from modules.ai.prompt_registry import PromptRegistry
from modules.ai.prompt_spec import PromptSpec

RESUME_EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured resume facts for a local-first career copilot. "
    "Use only evidence present in the resume. Return valid JSON only. "
    "Do not invent experience, education, certifications, professional licenses, "
    "languages, tools, metrics or employment. If a field is unclear, use low confidence "
    "and mark it for human review. Support multiple career domains, not only technology."
)

RESUME_EXTRACTION_USER_TEMPLATE = """Analyze the resume and return JSON matching the schema.

File type: {file_type}
Candidate preferences: {candidate_preferences}
Existing profile memory: {existing_profile_memory}
Local parser hints: {local_profile}
Language: {language}

RESUME:
{resume_text}
"""

JOB_EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured job-posting facts for any professional domain. "
    "Return valid JSON only. Do not invent company, salary, requirements, benefits, "
    "licenses or certifications. Distinguish required, preferred, optional and unclear "
    "requirements. Treat regulated professions conservatively."
)

JOB_EXTRACTION_USER_TEMPLATE = """Analyze the job posting and return JSON matching the schema.

Source: {source}
Candidate context: {candidate_context}
Local parser hints: {local_job}
Language: {language}

JOB POSTING:
{job_text}
"""

DOMAIN_CLASSIFICATION_SYSTEM_PROMPT = (
    "You classify professional domains using textual evidence. Do not force everything "
    "into technology. Accept mixed domains and return valid JSON only."
)

DOMAIN_CLASSIFICATION_USER_TEMPLATE = """Classify the professional domain in the text.

Text type: {text_type}
Known context: {known_context}
Language: {language}

TEXT:
{text}
"""

GITHUB_REPO_ANALYSIS_SYSTEM_PROMPT = (
    "You are a senior evaluator of software quality, architecture, security, documentation "
    "and professional portfolio value. Analyze only the evidence provided: metadata, tree, "
    "selected files, dependency graph and target role/job when present. Return valid JSON only. "
    "Do not invent technologies, metrics, users, companies, deploys, experience or outcomes. "
    "If tests appear in the tree, acknowledge their presence even when their content was not read."
)

GITHUB_REPO_ANALYSIS_USER_TEMPLATE = """Analyze the repository below.

Repository metadata:
{repository}

Analysis context:
{analysis_context}

Detected signals:
{detected_signals}

Complete directory tree:
{repository_structure}

Selected files:
{selected_files}

Dependency graph:
{dependency_graph}

Return only JSON matching the expected schema.
"""

MATCH_ANALYSIS_SYSTEM_PROMPT = (
    "You analyze resume/job compatibility for SotuHire using only provided evidence. "
    "Return valid JSON only. Do not invent jobs, education, skills, certifications, "
    "licenses, metrics or outcomes. Scores must be conservative and explainable. "
    "Missing evidence is a gap, not a fact about the candidate."
)

MATCH_ANALYSIS_USER_TEMPLATE = """Analyze compatibility and return JSON matching the schema.

Preferences:
{preferences}

Job details:
{job_details}

Authorized memory context:
{memory_context}

RESUME:
{resume_text}

JOB:
{job_text}
"""

ATS_ANALYSIS_SYSTEM_PROMPT = (
    "You review ATS keyword alignment using only the resume, job text and deterministic "
    "keyword review already provided. Return valid JSON only. Never recommend adding a "
    "claim unless the user confirms it is true."
)

ATS_ANALYSIS_USER_TEMPLATE = """Review ATS evidence and return JSON matching the schema.

Deterministic review:
{deterministic_review}

Keywords:
{keywords}

RESUME:
{resume_text}

JOB:
{job_text}
"""

RESUME_TAILOR_SYSTEM_PROMPT = (
    "You suggest resume tailoring improvements for SotuHire. Use only evidence supplied "
    "by the user. Return valid JSON only. Do not invent experience, credentials, tools, "
    "companies, numbers or achievements. Conditional suggestions must be clearly marked."
)

RESUME_TAILOR_USER_TEMPLATE = """Suggest safe resume tailoring ideas and return JSON matching the schema.

Target role: {target_role}
Target company: {target_company}
Deterministic tailor:
{deterministic_tailor}

JOB:
{job_text}

EVIDENCE:
{evidence_text}
"""

CAREER_ADVICE_SYSTEM_PROMPT = (
    "You provide cautious career guidance using only supplied SotuHire evidence. "
    "Return valid JSON only and separate safe actions from uncertain observations."
)

CAREER_ADVICE_USER_TEMPLATE = """Provide safe career insights and return JSON matching the schema.

Context:
{context}

Evidence:
{evidence}
"""

SOURCE_IMPORT_ENRICHMENT_SYSTEM_PROMPT = (
    "You enrich imported job opportunities for SotuHire intake. Use only the pasted text "
    "and source URL. Return valid JSON only. Do not invent requirements, company facts, "
    "salary, licenses, certifications, experience, metrics or application status. Separate "
    "facts from cautious inference and add warnings when evidence is weak."
)

SOURCE_IMPORT_ENRICHMENT_USER_TEMPLATE = """Enrich this imported opportunity and return JSON matching the schema.

Source URL: {source_url}
Language: {language}

JOB TEXT:
{job_text}
"""

JOB_RADAR_MATCH_SYSTEM_PROMPT = (
    "You explain Job Radar matches for SotuHire using only provided evidence. "
    "Return valid JSON only. Do not invent requirements, company facts, salary, credentials, "
    "candidate experience, metrics or application status. Separate facts from cautious inference. "
    "Final scores are owned by backend logic; explain them without changing them."
)

JOB_RADAR_MATCH_USER_TEMPLATE = """Explain why this radar result may match the wishlist.

Language: {language}

Job:
{job}

Wishlist:
{wishlist}

Local deterministic match:
{local_match}
"""

JOB_WISHLIST_BUILDER_SYSTEM_PROMPT = """Você é um assistente de estruturação de wishlist de vagas do SotuHire.

Sua tarefa é transformar o texto livre do usuário em uma wishlist estruturada
para busca/radar de vagas.

Não assuma que o usuário é desenvolvedor, profissional de TI ou pessoa com GitHub.
Classifique o domínio profissional a partir das evidências.

Considere qualquer área: saúde, direito, engenharia, educação, artes, indústria,
administração, pesquisa, laboratório, turismo, comunicação, serviços, concursos,
licenciaturas, bacharelados, técnicos, tecnólogos, pós-graduação, mestrado,
doutorado, profissões regulamentadas e transições de carreira.

Use somente o texto fornecido e o contexto local permitido. Não invente formação,
experiência, certificação, registro profissional, licença, número de conselho,
especialização, cargo, empresa, resultado ou habilidade.

Quando algo parecer necessário para uma vaga mas não estiver confirmado, marque como
pergunta, aviso, suposição ou item a confirmar.

A saída deve ser JSON válido, compatível com o schema esperado. Não inclua markdown.
Não inclua comentários fora do JSON. Não inclua API keys, segredos, cookies, tokens
ou dados sensíveis. A wishlist gerada deve sempre exigir revisão humana antes de salvar.
"""

JOB_WISHLIST_BUILDER_USER_TEMPLATE = """Transform this free-text career search request into an unsaved Job Radar wishlist draft.

Language: {language}

Free text:
{free_text}

Allowed local profile context:
{profile_context}

Return only JSON matching the expected schema.
"""

PROFILE_ITEMS_EXTRACTOR_SYSTEM_PROMPT = """Voce e um extrator de itens de Perfil Profissional Universal do SotuHire.

Extraia apenas informacoes presentes no texto fornecido.

Nao assuma que o usuario e de TI, dev ou possui GitHub.

Considere qualquer area profissional, academica, tecnica, cientifica, artistica
ou formativa: saude, direito, engenharia, educacao, artes, industria,
administracao, pesquisa, laboratorio, turismo, comunicacao, servicos,
concursos, tecnicos, tecnologos, licenciaturas, bacharelados, pos-graduacao,
mestrado, doutorado, profissoes regulamentadas e transicoes de carreira.

Nao invente formacao, experiencia, certificacao, registro profissional, licenca,
numero de conselho, instituicao, empresa, resultado, habilidade, idioma,
publicacao, projeto ou cargo.

Quando algo parecer provavel mas nao estiver explicito, coloque como baixa
confianca ou pergunta a confirmar, nao como fato confirmado.

Todo item extraido deve ter type, title, description, area/domain, source,
evidence, confidence e confirmed_by_user=false.

A saida deve ser JSON valido. Nao retorne markdown. Nao inclua comentarios fora
do JSON. Nao inclua segredos, API keys, cookies ou tokens.
"""

PROFILE_ITEMS_EXTRACTOR_USER_TEMPLATE = """Extract Universal Career Profile items from this user-provided text.

Language: {language}
Source type: {source_type}

Text:
{text}

Return only JSON matching the expected schema.
"""

PROFILE_LATTES_EXTRACTOR_SYSTEM_PROMPT = """Você é um extrator assistido de evidências acadêmicas para o Perfil Profissional Universal do SotuHire.

Use somente informações explícitas no texto fornecido pelo usuário. A IA organiza e sugere rascunhos, mas não é fonte de verdade.

Não invente formação, publicação, DOI, ISBN, ISSN, ORCID, Lattes ID, instituição, orientador, vínculo, registro, prêmio, autoria, cargo ou resultado.
Não faça login, scraping, crawler ou inferência de dados externos. Não salve nada automaticamente no Perfil.

Extraia candidatos de ProfileItem para formação, pesquisa, iniciação científica, extensão, docência, monitoria, publicações, artigos, anais, livros, capítulos, produção técnica, produção artística, eventos, apresentações, prêmios, bolsas, orientações, bancas, revisão, laboratório, campo, clínica, Lattes e ORCID quando estiverem explícitos.

Cada item deve preservar source, source_ref, evidence curta, confidence e confirmed_by_user=false.
Se algo estiver implícito ou incompleto, use confidence=low e coloque em assumptions, questions_to_confirm ou warnings.
Dados sensíveis devem ser marcados como sensitive=true quando aparecerem.

Retorne somente JSON válido, sem markdown, compatível com o schema esperado.
"""

PROFILE_LATTES_EXTRACTOR_USER_TEMPLATE = """Extract academic and Lattes evidence candidates from this pasted text.

Language: {language}
Source URL: {source_url}
Lattes ID: {lattes_id}
ORCID: {orcid}

Local parser draft, for comparison only:
{local_parser_draft}

PASTED LATTES OR ACADEMIC TEXT:
{text}

Return only JSON matching the expected schema.
"""


def initial_prompt_specs(
    schema_overrides: dict[str, type[BaseModel]] | None = None,
) -> list[PromptSpec]:
    """Build initial v0.10 prompt specs with their output schemas."""
    schemas = schema_overrides or _default_schemas()
    return [
        PromptSpec(
            prompt_id="resume_extraction_v1",
            version="1.0.0",
            system_prompt=RESUME_EXTRACTION_SYSTEM_PROMPT,
            user_template=RESUME_EXTRACTION_USER_TEMPLATE,
            output_schema=schemas["resume_extraction_v1"],
            temperature=0.1,
            mode="resume_extraction",
        ),
        PromptSpec(
            prompt_id="job_extraction_multi_domain_v1",
            version="1.0.0",
            system_prompt=JOB_EXTRACTION_SYSTEM_PROMPT,
            user_template=JOB_EXTRACTION_USER_TEMPLATE,
            output_schema=schemas["job_extraction_multi_domain_v1"],
            temperature=0.1,
            mode="job_extraction",
        ),
        PromptSpec(
            prompt_id="domain_classification_v1",
            version="1.0.0",
            system_prompt=DOMAIN_CLASSIFICATION_SYSTEM_PROMPT,
            user_template=DOMAIN_CLASSIFICATION_USER_TEMPLATE,
            output_schema=schemas["domain_classification_v1"],
            temperature=0.1,
            mode="domain_classification",
        ),
        PromptSpec(
            prompt_id="github_repo_analysis_v2",
            version="2.0.0",
            system_prompt=GITHUB_REPO_ANALYSIS_SYSTEM_PROMPT,
            user_template=GITHUB_REPO_ANALYSIS_USER_TEMPLATE,
            output_schema=schemas["github_repo_analysis_v2"],
            temperature=0.1,
            mode="github_repo_analysis",
        ),
        PromptSpec(
            prompt_id="match_analysis_evidence_based_v1",
            version="1.0.0",
            system_prompt=MATCH_ANALYSIS_SYSTEM_PROMPT,
            user_template=MATCH_ANALYSIS_USER_TEMPLATE,
            output_schema=schemas["match_analysis_evidence_based_v1"],
            temperature=0.1,
            mode="match_analysis",
        ),
        PromptSpec(
            prompt_id="ats_analysis_v1",
            version="1.0.0",
            system_prompt=ATS_ANALYSIS_SYSTEM_PROMPT,
            user_template=ATS_ANALYSIS_USER_TEMPLATE,
            output_schema=schemas["ats_analysis_v1"],
            temperature=0.1,
            mode="ats_analysis",
        ),
        PromptSpec(
            prompt_id="resume_tailor_v1",
            version="1.0.0",
            system_prompt=RESUME_TAILOR_SYSTEM_PROMPT,
            user_template=RESUME_TAILOR_USER_TEMPLATE,
            output_schema=schemas["resume_tailor_v1"],
            temperature=0.1,
            mode="resume_tailor",
        ),
        PromptSpec(
            prompt_id="career_advice_v1",
            version="1.0.0",
            system_prompt=CAREER_ADVICE_SYSTEM_PROMPT,
            user_template=CAREER_ADVICE_USER_TEMPLATE,
            output_schema=schemas["career_advice_v1"],
            temperature=0.1,
            mode="career_advice",
        ),
        PromptSpec(
            prompt_id="source_import_enrichment_v1",
            version="1.0.0",
            system_prompt=SOURCE_IMPORT_ENRICHMENT_SYSTEM_PROMPT,
            user_template=SOURCE_IMPORT_ENRICHMENT_USER_TEMPLATE,
            output_schema=schemas["source_import_enrichment_v1"],
            temperature=0.1,
            mode="source_import_enrichment",
        ),
        PromptSpec(
            prompt_id="job_radar_match_explanation_v1",
            version="1.0.0",
            system_prompt=JOB_RADAR_MATCH_SYSTEM_PROMPT,
            user_template=JOB_RADAR_MATCH_USER_TEMPLATE,
            output_schema=schemas["job_radar_match_explanation_v1"],
            temperature=0.1,
            mode="job_radar_match_explanation",
        ),
        PromptSpec(
            prompt_id="job_wishlist_builder_v1",
            version="1.0.0",
            system_prompt=JOB_WISHLIST_BUILDER_SYSTEM_PROMPT,
            user_template=JOB_WISHLIST_BUILDER_USER_TEMPLATE,
            output_schema=schemas["job_wishlist_builder_v1"],
            temperature=0.1,
            mode="job_wishlist_builder",
        ),
        PromptSpec(
            prompt_id="profile_items_extractor_v1",
            version="1.0.0",
            system_prompt=PROFILE_ITEMS_EXTRACTOR_SYSTEM_PROMPT,
            user_template=PROFILE_ITEMS_EXTRACTOR_USER_TEMPLATE,
            output_schema=schemas["profile_items_extractor_v1"],
            temperature=0.1,
            mode="profile_items_extractor",
        ),
        PromptSpec(
            prompt_id="profile_lattes_extractor_v1",
            version="1.0.0",
            system_prompt=PROFILE_LATTES_EXTRACTOR_SYSTEM_PROMPT,
            user_template=PROFILE_LATTES_EXTRACTOR_USER_TEMPLATE,
            output_schema=schemas["profile_lattes_extractor_v1"],
            temperature=0.0,
            mode="profile_lattes_extractor",
        ),
    ]


def default_prompt_registry() -> PromptRegistry:
    """Return the default prompt registry for structured extraction."""
    return PromptRegistry(initial_prompt_specs())


def _default_schemas() -> dict[str, type[BaseModel]]:
    from modules.academic.lattes_models import LattesImportResult
    from modules.ai.schemas.analysis_insights import (
        AtsAiReviewOutput,
        RadarMatchExplanationOutput,
        ResumeTailorAiOutput,
        SafeAiInsightOutput,
        SourceImportEnrichmentOutput,
        WishlistDraftOutput,
    )
    from modules.ai.schemas.domain_classification import DomainClassificationOutput
    from modules.ai.schemas.job_extraction import JobExtractionOutput
    from modules.ai.schemas.resume_extraction import ResumeExtractionOutput
    from modules.github_analyzer.schemas import GitHubRepoAnalysisOutput
    from modules.profile.models import ProfileImportDraft
    from modules.schemas.job_analysis import JobAnalysisSchema

    return {
        "resume_extraction_v1": ResumeExtractionOutput,
        "job_extraction_multi_domain_v1": JobExtractionOutput,
        "domain_classification_v1": DomainClassificationOutput,
        "github_repo_analysis_v2": GitHubRepoAnalysisOutput,
        "match_analysis_evidence_based_v1": JobAnalysisSchema,
        "ats_analysis_v1": AtsAiReviewOutput,
        "resume_tailor_v1": ResumeTailorAiOutput,
        "career_advice_v1": SafeAiInsightOutput,
        "source_import_enrichment_v1": SourceImportEnrichmentOutput,
        "job_radar_match_explanation_v1": RadarMatchExplanationOutput,
        "job_wishlist_builder_v1": WishlistDraftOutput,
        "profile_items_extractor_v1": ProfileImportDraft,
        "profile_lattes_extractor_v1": LattesImportResult,
    }
