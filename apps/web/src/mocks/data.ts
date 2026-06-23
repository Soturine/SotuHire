import type {
  AtsReview,
  AiSettings,
  GithubReport,
  Health,
  JobPosting,
  MatchAnalysis,
  ResumeProfile,
  ResumeTailor,
  TrackerFunnel,
  TrackerJob,
  TrackerMetrics,
  TrackerRequirements,
  TrackerSources,
} from "@/lib/api/types";

export const mockHealth: Health = {
  status: "ok",
  version: "1.5.0",
  local_first: true,
  environment: "mock",
  capabilities: [
    "resume_extract",
    "job_extract",
    "match_analyze",
    "ats_analyze",
    "resume_tailor",
    "github_repo_analyze",
    "tracker_jobs",
    "application_intelligence",
    "ai_settings",
    "authenticated_browser_sources",
    "extension_bridge",
  ],
};

export const mockAiSettings: AiSettings = {
  provider: "local",
  model: "local",
  configured: true,
  status: "ready",
  use_ai: false,
  allow_match: true,
  allow_ats: true,
  allow_tailor: true,
  allow_github: true,
  allow_memory_context: false,
  warnings: [],
};

export const mockResume: ResumeProfile = {
  id: "profile_demo_backend_001",
  name: "Pessoa Fictícia",
  headline: "Desenvolvedora Backend Python",
  location: "Remoto · Brasil",
  seniority: "pleno",
  summary: "Perfil fictício com experiência em APIs, testes e integrações.",
  skills: ["Python", "FastAPI", "SQL", "Pytest", "APIs REST", "Git"],
  experience: [
    {
      role: "Desenvolvedor Backend",
      company: "Empresa Exemplo Alpha",
      period: "2022 — 2026",
      highlights: [
        "Construiu APIs internas com Python e testes automatizados.",
        "Participou de revisões de código e monitoramento de erros.",
      ],
    },
  ],
  education: [
    {
      name: "Tecnologia em Análise e Desenvolvimento de Sistemas",
      institution: "Faculdade Fictícia Central",
      status: "completed",
    },
  ],
  projects: [
    {
      name: "fictitious-api-lab",
      description: "API de estudo com FastAPI, SQL e testes.",
      links: ["https://github.com/example/fictitious-api-lab"],
    },
  ],
};

export const mockJob: JobPosting = {
  id: "job_demo_backend_001",
  title: "Desenvolvedor Backend Python",
  company: "Empresa Fictícia Delta",
  source: "LinkedIn",
  modality: "remote",
  seniority: "pleno",
  domain: "technology",
  required_skills: ["Python", "FastAPI", "SQL", "Testes automatizados"],
  preferred_skills: ["Docker", "Cloud", "CI/CD"],
  responsibilities: [
    "Desenvolver APIs REST.",
    "Escrever testes automatizados.",
    "Apoiar melhorias de observabilidade.",
  ],
};

export const mockMatch: MatchAnalysis = {
  analysis_version: "v2",
  match_score: 78,
  confidence_score: 0.66,
  evidence_score: 72,
  ats_score: 74,
  opportunity_fit_score: 81,
  risk_score: 18,
  domain: "technology",
  recommendation: "apply_with_adjustments",
  matched_requirements: [
    {
      name: "Python",
      category: "required_skill",
      evidence: [
        "Currículo cita Python em experiência backend.",
        "Repositório fictitious-api-lab usa Python.",
      ],
    },
    {
      name: "FastAPI",
      category: "required_skill",
      evidence: ["Projeto fictitious-api-lab cita FastAPI."],
    },
    {
      name: "Testes automatizados",
      category: "required_skill",
      evidence: ["Currículo cita Pytest e revisões de qualidade."],
    },
  ],
  partial_requirements: [
    {
      name: "Docker",
      category: "preferred_skill",
      reason: "A vaga pede Docker, mas o currículo fictício não evidencia experiência direta.",
    },
  ],
  missing_requirements: [
    {
      name: "Cloud",
      category: "preferred_skill",
      reason: "Nenhuma evidência explícita encontrada.",
    },
  ],
  critical_gaps: [],
  transferable_skills: [
    "Experiência com APIs pode apoiar onboarding em serviços cloud.",
    "Testes automatizados ajudam a demonstrar maturidade de engenharia.",
  ],
  safe_actions: [
    "Se tiver experiência real com Docker, descreva onde usou e qual problema resolveu.",
    "Não declare Cloud sem projeto, curso, certificação ou uso real verificável.",
  ],
};

export const mockAts: AtsReview = {
  ats_score: 74,
  present: ["Python", "FastAPI", "SQL", "Pytest", "APIs REST"],
  missing_but_safe_to_add_if_true: ["Docker", "CI/CD"],
  missing_without_evidence: ["Cloud", "Kubernetes"],
  warnings: [
    "Adicionar Docker somente se houver experiência real.",
    "Não declarar Kubernetes sem evidência.",
  ],
};

export const mockTailor: ResumeTailor = {
  safe_keywords: ["Python", "FastAPI", "SQL", "Pytest", "APIs REST"],
  suggested_bullets: [
    "Desenvolveu APIs REST em Python com FastAPI, SQL e testes automatizados.",
    "Apoiou melhorias de qualidade com Pytest, revisão de código e monitoramento de erros.",
    "Manteve documentação técnica para facilitar manutenção e onboarding.",
  ],
  conditional_suggestions: [
    {
      keyword: "Docker",
      text: "Se tiver experiência real, cite ambiente, imagem, compose ou pipeline em que usou Docker.",
    },
    { keyword: "CI/CD", text: "Se tiver participado de pipelines, descreva ferramenta e impacto." },
  ],
  warnings: [
    "Não inventar Cloud, Kubernetes, certificações ou cargos.",
    "Validar manualmente cada bullet antes de usar em candidatura real.",
  ],
  evidence_used: [
    "Currículo fictício",
    "Repositório público fictício",
    "Descrição de vaga fictícia",
  ],
};

export const mockGithub: GithubReport = {
  repo: {
    owner: "example",
    name: "fictitious-api-lab",
    url: "https://github.com/example/fictitious-api-lab",
    visibility: "public",
  },
  quality_score: 81,
  evidence_score: 76,
  languages: [
    { name: "Python", percent: 86 },
    { name: "Markdown", percent: 10 },
    { name: "Dockerfile", percent: 4 },
  ],
  positive_signals: [
    "README com instalação e exemplos.",
    "Testes automatizados com Pytest.",
    "Estrutura clara de API e camada de serviços.",
  ],
  risks: ["Docker aparece no repositório, mas não no currículo fictício."],
  portfolio_suggestions: [
    "Adicionar screenshot ou diagrama simples da arquitetura.",
    "Explicar tradeoffs técnicos no README.",
  ],
};

export const mockJobs: TrackerJob[] = [
  {
    id: "job_demo_001",
    title: "Desenvolvedor Backend Python",
    company: "Empresa Fictícia Delta",
    source: "LinkedIn",
    status: "applied",
    match_score: 78,
    ats_score: 74,
    created_at: "2026-06-01",
    updated_at: "2026-06-05",
    requirements: ["Python", "FastAPI", "Docker"],
  },
  {
    id: "job_demo_002",
    title: "Engenheiro de APIs",
    company: "Produto Exemplo Beta",
    source: "Gupy",
    status: "interview",
    match_score: 84,
    ats_score: 79,
    created_at: "2026-06-04",
    updated_at: "2026-06-12",
    requirements: ["Python", "SQL", "Testes"],
  },
  {
    id: "job_demo_003",
    title: "Desenvolvedor de Plataforma",
    company: "Serviço Fictício Orion",
    source: "Página de carreira",
    status: "ready_to_apply",
    match_score: 69,
    ats_score: 65,
    created_at: "2026-06-10",
    updated_at: "2026-06-10",
    requirements: ["APIs", "Cloud", "Observabilidade"],
  },
  {
    id: "job_demo_004",
    title: "Engenheiro Python Sênior",
    company: "Fictícia Cloud Co.",
    source: "LinkedIn",
    status: "analyzed",
    match_score: 72,
    ats_score: 70,
    created_at: "2026-06-11",
    updated_at: "2026-06-13",
    requirements: ["Python", "AWS", "Kubernetes"],
  },
  {
    id: "job_demo_005",
    title: "Desenvolvedor Backend",
    company: "Startup Fictícia Nova",
    source: "Gupy",
    status: "found",
    match_score: 63,
    ats_score: 60,
    created_at: "2026-06-14",
    updated_at: "2026-06-14",
    requirements: ["Node.js", "Postgres"],
  },
  {
    id: "job_demo_006",
    title: "Engenheiro Backend",
    company: "Fictícia Healthtech",
    source: "Página de carreira",
    status: "offer",
    match_score: 91,
    ats_score: 88,
    created_at: "2026-05-20",
    updated_at: "2026-06-15",
    requirements: ["Python", "FastAPI", "SQL"],
  },
  {
    id: "job_demo_007",
    title: "Backend Jr.",
    company: "Fictícia EdTech",
    source: "LinkedIn",
    status: "rejected",
    match_score: 55,
    ats_score: 58,
    created_at: "2026-05-15",
    updated_at: "2026-05-28",
    requirements: ["Java", "Spring"],
  },
  {
    id: "job_demo_008",
    title: "Engenheiro de Dados",
    company: "Fictícia Analytics",
    source: "LinkedIn",
    status: "follow_up",
    match_score: 70,
    ats_score: 67,
    created_at: "2026-06-02",
    updated_at: "2026-06-10",
    requirements: ["Python", "Airflow", "SQL"],
  },
  {
    id: "job_demo_009",
    title: "Engenheiro DevOps",
    company: "Fictícia Infra",
    source: "Gupy",
    status: "tech_test",
    match_score: 66,
    ats_score: 62,
    created_at: "2026-06-08",
    updated_at: "2026-06-13",
    requirements: ["Terraform", "AWS"],
  },
  {
    id: "job_demo_010",
    title: "Backend (Fintech)",
    company: "Fictícia Pay",
    source: "LinkedIn",
    status: "message_sent",
    match_score: 73,
    ats_score: 71,
    created_at: "2026-06-09",
    updated_at: "2026-06-11",
    requirements: ["Python", "Kafka"],
  },
];

export const mockMetrics: TrackerMetrics = {
  total_saved: 18,
  total_applied: 9,
  by_status: { saved: 6, applied: 9, interview: 2, offer: 1, rejected: 3 },
  average_match_by_status: { saved: 68, applied: 75, interview: 82, offer: 88 },
  average_ats: 73,
  response_rate: 0.33,
  interview_rate: 0.22,
  offer_rate: 0.05,
  weekly_applications: [
    { week: "2026-W20", count: 1 },
    { week: "2026-W21", count: 2 },
    { week: "2026-W22", count: 2 },
    { week: "2026-W23", count: 3 },
    { week: "2026-W24", count: 4 },
    { week: "2026-W25", count: 3 },
  ],
};

export const mockFunnel: TrackerFunnel = {
  stages: [
    { status: "saved", label: "Salvas", count: 18 },
    { status: "applied", label: "Aplicadas", count: 9 },
    { status: "response", label: "Com resposta", count: 3 },
    { status: "interview", label: "Entrevistas", count: 2 },
    { status: "offer", label: "Oferta", count: 1 },
  ],
  conversion_rates: [
    { from: "saved", to: "applied", rate: 0.5 },
    { from: "applied", to: "response", rate: 0.33 },
    { from: "response", to: "interview", rate: 0.66 },
    { from: "interview", to: "offer", rate: 0.5 },
  ],
};

export const mockRequirements: TrackerRequirements = {
  top_requirements: [
    { name: "Python", count: 12, sources: ["LinkedIn", "Gupy"], candidate_has_evidence: true },
    {
      name: "FastAPI",
      count: 8,
      sources: ["LinkedIn", "Página de carreira"],
      candidate_has_evidence: true,
    },
    { name: "Docker", count: 7, sources: ["Gupy", "LinkedIn"], candidate_has_evidence: false },
    { name: "SQL", count: 7, sources: ["Gupy"], candidate_has_evidence: true },
    { name: "Cloud", count: 6, sources: ["LinkedIn"], candidate_has_evidence: false },
    { name: "Kubernetes", count: 4, sources: ["LinkedIn"], candidate_has_evidence: false },
  ],
  critical_gaps: [
    {
      name: "Docker",
      count: 7,
      severity: "medium",
      safe_action: "Se tiver experiência real, evidencie no currículo.",
    },
    {
      name: "Cloud",
      count: 6,
      severity: "medium",
      safe_action: "Tratar como gap real até existir projeto, curso ou experiência verificável.",
    },
    {
      name: "Kubernetes",
      count: 4,
      severity: "high",
      safe_action: "Não declarar sem evidência prática.",
    },
  ],
  requirements_by_source: [
    { source: "LinkedIn", requirement: "Python", count: 6 },
    { source: "LinkedIn", requirement: "Docker", count: 4 },
    { source: "Gupy", requirement: "SQL", count: 5 },
    { source: "Página de carreira", requirement: "FastAPI", count: 3 },
  ],
  trend_over_time: [
    { month: "2026-04", requirement: "Docker", count: 3 },
    { month: "2026-05", requirement: "Docker", count: 5 },
    { month: "2026-06", requirement: "Docker", count: 7 },
  ],
};

export const mockSources: TrackerSources = {
  sources: [
    {
      name: "LinkedIn",
      saved: 8,
      applied: 4,
      interviews: 1,
      average_match: 76,
      top_requirements: ["Python", "Docker", "SQL"],
    },
    {
      name: "Gupy",
      saved: 5,
      applied: 3,
      interviews: 1,
      average_match: 69,
      top_requirements: ["SQL", "FastAPI", "Testes"],
    },
    {
      name: "Página de carreira",
      saved: 5,
      applied: 2,
      interviews: 0,
      average_match: 73,
      top_requirements: ["APIs", "Cloud", "Observabilidade"],
    },
  ],
};
