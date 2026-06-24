import type {
  ApiEnvelope,
  AiProvider,
  AiSettings,
  AiSettingsPayload,
  AiSettingsStatus,
  AiSettingsTestPayload,
  AiSettingsTestResult,
  AtsReview,
  AuthenticatedBrowserCollectResult,
  AuthenticatedBrowserStatus,
  ExtensionCapturesResult,
  ExtensionImportGithubResult,
  ExtensionImportJobResult,
  ExtensionImportTrackerResult,
  ExtensionStatus,
  GithubAnalyzeResult,
  GithubReport,
  Health,
  JobExtractResult,
  JobPosting,
  MatchAnalysis,
  MatchAnalyzeResult,
  MatchRequirement,
  ResumeExtractResult,
  ResumeProfile,
  ResumeTailor,
  ResumeTailorResult,
  TrackerFunnel,
  TrackerJob,
  TrackerMetrics,
  TrackerRequirements,
  TrackerSources,
} from "./types";
import {
  mockAiSettings,
  mockAts,
  mockFunnel,
  mockGithub,
  mockHealth,
  mockJob,
  mockJobs,
  mockMatch,
  mockMetrics,
  mockRequirements,
  mockResume,
  mockSources,
  mockTailor,
} from "@/mocks/data";
import type { ApiMode } from "./mode";

type JsonRecord = Record<string, unknown>;

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function call<T>(
  mode: ApiMode,
  baseUrl: string,
  path: string,
  init: RequestInit | undefined,
  mockValue: T,
  normalize: (value: unknown) => T = (value) => value as T,
): Promise<T> {
  if (mode === "demo") {
    await sleep(400 + Math.random() * 400);
    return mockValue;
  }

  const res = await fetch(`${baseUrl.replace(/\/+$/, "")}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = "";
    try {
      const j = (await res.json()) as ApiEnvelope<unknown>;
      detail = j.error?.message ?? "";
    } catch {
      /* API may return an empty body for transport-level failures. */
    }
    throw new Error(detail || `Erro HTTP ${res.status} ao chamar ${path}`);
  }

  const json = (await res.json()) as ApiEnvelope<unknown>;
  if (!json.ok || json.data === undefined) {
    throw new Error(json.error?.message ?? "Resposta invalida da API.");
  }
  return normalize(json.data);
}

export function makeApi(mode: ApiMode, baseUrl: string) {
  return {
    health: () => call<Health>(mode, baseUrl, "/health", undefined, mockHealth, normalizeHealth),

    aiSettings: () =>
      call<AiSettings>(
        mode,
        baseUrl,
        "/settings/ai",
        undefined,
        mockAiSettings,
        normalizeAiSettings,
      ),

    aiSettingsStatus: () =>
      call<AiSettings>(
        mode,
        baseUrl,
        "/settings/ai/status",
        undefined,
        mockAiSettings,
        normalizeAiSettings,
      ),

    aiSettingsSave: (payload: AiSettingsPayload) =>
      call<AiSettings>(
        mode,
        baseUrl,
        "/settings/ai",
        { method: "POST", body: JSON.stringify(payload) },
        mockSavedAiSettings(payload),
        normalizeAiSettings,
      ),

    aiSettingsTest: (payload: AiSettingsTestPayload = {}) =>
      call<AiSettingsTestResult>(
        mode,
        baseUrl,
        "/settings/ai/test",
        { method: "POST", body: JSON.stringify(payload) },
        mockAiSettingsTest(payload),
        normalizeAiSettingsTest,
      ),

    aiSettingsDelete: () =>
      call<AiSettings>(
        mode,
        baseUrl,
        "/settings/ai",
        { method: "DELETE" },
        {
          ...mockAiSettings,
          provider: "gemini",
          model: "gemini-2.5-flash",
          configured: false,
          status: "not_configured",
        },
        normalizeAiSettings,
      ),

    resumeExtract: (resume_text: string) =>
      call<ResumeExtractResult>(
        mode,
        baseUrl,
        "/resume/extract",
        {
          method: "POST",
          body: JSON.stringify({ resume_text, source_type: "text", include_raw_text: false }),
        },
        {
          profile: { ...mockResume },
          confidence: 0.84,
          provider_used: "local",
          requested_provider: "local",
          analysis_mode: "local",
          fallback_used: false,
        },
        normalizeResumeExtract,
      ),

    jobExtract: (job_text: string, source_url?: string) =>
      call<JobExtractResult>(
        mode,
        baseUrl,
        "/job/extract",
        { method: "POST", body: JSON.stringify({ job_text, source_url, include_raw_text: false }) },
        {
          job: { ...mockJob },
          confidence: 0.8,
          provider_used: "local",
          requested_provider: "local",
          analysis_mode: "local",
          fallback_used: false,
        },
        normalizeJobExtract,
      ),

    matchAnalyze: (payload: { resume_text: string; job_text: string }) =>
      call<MatchAnalyzeResult>(
        mode,
        baseUrl,
        "/match/analyze",
        { method: "POST", body: JSON.stringify(payload) },
        {
          provider_used: "local",
          requested_provider: "local",
          analysis_mode: "local",
          fallback_used: false,
          local_first: true,
          analysis: { ...mockMatch },
        },
        normalizeMatchEnvelope,
      ),

    atsAnalyze: (payload: { resume_text: string; job_text: string; job_keywords?: string[] }) =>
      call<AtsReview>(
        mode,
        baseUrl,
        "/ats/analyze",
        { method: "POST", body: JSON.stringify(payload) },
        mockAts,
        normalizeAts,
      ),

    resumeTailor: (payload: {
      target_role: string;
      target_company?: string;
      job_text?: string;
      evidence_text?: string;
    }) =>
      call<ResumeTailorResult>(
        mode,
        baseUrl,
        "/resume/tailor",
        { method: "POST", body: JSON.stringify(payload) },
        {
          safe_to_export: true,
          tailor: { ...mockTailor },
          provider_used: "local",
          requested_provider: "local",
          analysis_mode: "local",
          fallback_used: false,
          ai_suggestions: [],
        },
        normalizeTailorEnvelope,
      ),

    githubAnalyze: (payload: { repo_url: string; target_role?: string }) =>
      call<GithubAnalyzeResult>(
        mode,
        baseUrl,
        "/github/repo/analyze",
        { method: "POST", body: JSON.stringify({ mode: "full", ...payload }) },
        {
          report: { ...mockGithub },
          provider_used: "local",
          requested_provider: "local",
          analysis_mode: "local",
          fallback_used: false,
        },
        normalizeGithubEnvelope,
      ),

    trackerJobs: () =>
      call<{ jobs: TrackerJob[] }>(
        mode,
        baseUrl,
        "/tracker/jobs",
        undefined,
        { jobs: mockJobs },
        normalizeTrackerJobs,
      ),

    trackerCreate: (payload: Partial<TrackerJob>) =>
      call<{ job: TrackerJob }>(
        mode,
        baseUrl,
        "/tracker/jobs",
        { method: "POST", body: JSON.stringify({ privacy_acknowledged: true, ...payload }) },
        {
          job: {
            id: `job_${Math.random().toString(36).slice(2, 8)}`,
            title: payload.title ?? "Nova vaga",
            company: payload.company ?? "-",
            source: payload.source,
            status: payload.status ?? "found",
            match_score: payload.match_score,
            ats_score: payload.ats_score,
            created_at: new Date().toISOString().slice(0, 10),
            updated_at: new Date().toISOString().slice(0, 10),
            notes: payload.notes,
          },
        },
        normalizeTrackerJobEnvelope,
      ),

    trackerUpdate: (id: string, patch: Partial<TrackerJob>) =>
      call<{ job: TrackerJob }>(
        mode,
        baseUrl,
        `/tracker/jobs/${id}`,
        { method: "PATCH", body: JSON.stringify(patch) },
        { job: { ...(mockJobs.find((j) => j.id === id) ?? mockJobs[0]!), ...patch } },
        normalizeTrackerJobEnvelope,
      ),

    trackerMetrics: () =>
      call<TrackerMetrics>(
        mode,
        baseUrl,
        "/tracker/metrics",
        undefined,
        mockMetrics,
        normalizeTrackerMetrics,
      ),
    trackerRequirements: () =>
      call<TrackerRequirements>(
        mode,
        baseUrl,
        "/tracker/requirements",
        undefined,
        mockRequirements,
        normalizeTrackerRequirements,
      ),
    trackerFunnel: () =>
      call<TrackerFunnel>(
        mode,
        baseUrl,
        "/tracker/funnel",
        undefined,
        mockFunnel,
        normalizeTrackerFunnel,
      ),
    trackerSources: () =>
      call<TrackerSources>(
        mode,
        baseUrl,
        "/tracker/sources",
        undefined,
        mockSources,
        normalizeTrackerSources,
      ),

    authenticatedBrowserStatus: (browser_cdp_url = "http://127.0.0.1:9222") =>
      call<AuthenticatedBrowserStatus>(
        mode,
        baseUrl,
        `/sources/authenticated-browser/status?browser_cdp_url=${encodeURIComponent(browser_cdp_url)}`,
        undefined,
        {
          available: false,
          endpoint: browser_cdp_url,
          browser: "Demo",
          message: "Modo Demo: nenhum navegador real foi aberto.",
        },
        normalizeAuthenticatedBrowserStatus,
      ),

    authenticatedBrowserLaunch: (payload: { start_url: string; browser_cdp_url: string }) =>
      call<AuthenticatedBrowserStatus>(
        mode,
        baseUrl,
        "/sources/authenticated-browser/launch",
        { method: "POST", body: JSON.stringify(payload) },
        {
          available: true,
          endpoint: payload.browser_cdp_url,
          browser: "Chromium Demo",
          message: "Modo Demo: navegador autenticado simulado.",
        },
        normalizeAuthenticatedBrowserStatus,
      ),

    authenticatedBrowserCollect: (payload: {
      name: string;
      url: string;
      browser_cdp_url: string;
      max_items: number;
      max_pages: number;
      authorized_use: boolean;
      authorization_reference: string;
    }) =>
      call<AuthenticatedBrowserCollectResult>(
        mode,
        baseUrl,
        "/sources/authenticated-browser/collect",
        { method: "POST", body: JSON.stringify(payload) },
        {
          new_count: 2,
          duplicate_count: 0,
          updated_count: 0,
          failures: [],
          opportunities: [
            {
              title: "Backend Developer Python",
              company: "Empresa Demo",
              source_url: payload.url,
              confidence: 0.86,
            },
            {
              title: "Data Analyst Junior",
              company: "Startup Demo",
              source_url: payload.url,
              confidence: 0.79,
            },
          ],
        },
        normalizeAuthenticatedBrowserCollect,
      ),

    extensionStatus: () =>
      call<ExtensionStatus>(
        mode,
        baseUrl,
        "/extension/status",
        undefined,
        {
          available: true,
          companion_url: "http://127.0.0.1:8765",
          capture_count: 2,
          last_capture_at: new Date().toISOString(),
          message: "Modo Demo: capturas ficticias da extensao local.",
        },
        normalizeExtensionStatus,
      ),

    extensionCaptures: () =>
      call<ExtensionCapturesResult>(
        mode,
        baseUrl,
        "/extension/captures",
        undefined,
        {
          captures: [
            {
              id: "demo-capture-1",
              title: "Backend Python Demo",
              company: "Empresa Demo",
              url: "https://example.invalid/jobs/backend",
              domain: "example.invalid",
              kind: "job",
              source: "Extensao local demo",
              status: "captured",
              captured_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            {
              id: "demo-capture-2",
              title: "fictitious-api-lab",
              company: "GitHub",
              url: "https://github.com/example/fictitious-api-lab",
              domain: "github.com",
              kind: "github_repo",
              source: "Extensao local demo",
              status: "analyzed",
              captured_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        },
        normalizeExtensionCaptures,
      ),

    extensionImportJob: (capture_id: string) =>
      call<ExtensionImportJobResult>(
        mode,
        baseUrl,
        "/extension/import/job",
        { method: "POST", body: JSON.stringify({ capture_id }) },
        { capture_id, job: { ...mockJob }, message: "Modo Demo: captura enviada para Vaga." },
        normalizeExtensionImportJob,
      ),

    extensionImportTracker: (capture_id: string) =>
      call<ExtensionImportTrackerResult>(
        mode,
        baseUrl,
        "/extension/import/tracker",
        { method: "POST", body: JSON.stringify({ capture_id, privacy_acknowledged: true }) },
        {
          capture_id,
          tracker_id: `job_${Math.random().toString(36).slice(2, 8)}`,
          message: "Modo Demo: captura salva em Candidaturas.",
          provider: "local",
        },
        normalizeExtensionImportTracker,
      ),

    extensionImportGithub: (capture_id: string) =>
      call<ExtensionImportGithubResult>(
        mode,
        baseUrl,
        "/extension/import/github",
        { method: "POST", body: JSON.stringify({ capture_id }) },
        {
          capture_id,
          report: { ...mockGithub },
          message: "Modo Demo: captura enviada para Analise de GitHub.",
        },
        normalizeExtensionImportGithub,
      ),
  };
}

function normalizeHealth(value: unknown): Health {
  const raw = asRecord(value);
  return {
    status: asString(raw.status) || "ok",
    service: asString(raw.service),
    version: asString(raw.version) || "1.5.0",
    local_first: asBoolean(raw.local_first, true),
    environment: asString(raw.environment),
    capabilities: stringList(raw.capabilities),
  };
}

function normalizeAiSettings(value: unknown): AiSettings {
  const raw = asRecord(value);
  const provider = normalizeAiProvider(raw.provider);
  const status = normalizeAiStatus(raw.status);
  return {
    provider,
    model: asString(raw.model) || (provider === "local" ? "local" : "gemini-2.5-flash"),
    configured: asBoolean(raw.configured, provider === "local"),
    status,
    use_ai: asBoolean(raw.use_ai, false),
    allow_match: asBoolean(raw.allow_match, true),
    allow_ats: asBoolean(raw.allow_ats, true),
    allow_tailor: asBoolean(raw.allow_tailor, true),
    allow_github: asBoolean(raw.allow_github, true),
    allow_memory_context: asBoolean(raw.allow_memory_context, false),
    updated_at: asString(raw.updated_at),
    warnings: stringList(raw.warnings),
  };
}

function normalizeAiSettingsTest(value: unknown): AiSettingsTestResult {
  const raw = asRecord(value);
  const provider = normalizeAiProvider(raw.provider);
  return {
    provider,
    model: asString(raw.model) || (provider === "local" ? "local" : "gemini-2.5-flash"),
    success: asBoolean(raw.success, false),
    configured: asBoolean(raw.configured, false),
    status: normalizeAiStatus(raw.status),
    message: asString(raw.message),
  };
}

function mockSavedAiSettings(payload: AiSettingsPayload): AiSettings {
  const configured =
    payload.provider === "local" || (payload.provider === "gemini" && Boolean(payload.api_key));
  return {
    ...mockAiSettings,
    provider: payload.provider,
    model: payload.provider === "local" ? "local" : payload.model,
    configured,
    status:
      payload.provider === "openai_future"
        ? "planned"
        : configured
          ? payload.provider === "local"
            ? "ready"
            : "configured"
          : "not_configured",
    use_ai: payload.use_ai,
    allow_match: payload.allow_match,
    allow_ats: payload.allow_ats,
    allow_tailor: payload.allow_tailor,
    allow_github: payload.allow_github,
    allow_memory_context: payload.allow_memory_context,
    updated_at: new Date().toISOString(),
    warnings:
      payload.provider === "openai_future" ? ["OpenAI esta planejado para uma versao futura."] : [],
  };
}

function mockAiSettingsTest(payload: AiSettingsTestPayload): AiSettingsTestResult {
  const provider = payload.provider ?? "local";
  const configured = provider === "local" || Boolean(payload.api_key);
  return {
    provider,
    model: provider === "local" ? "local" : payload.model || "gemini-2.5-flash",
    success: configured && provider !== "openai_future",
    configured,
    status:
      provider === "openai_future"
        ? "planned"
        : configured
          ? provider === "local"
            ? "ready"
            : "configured"
          : "not_configured",
    message:
      configured && provider !== "openai_future"
        ? "Provider configurado com sucesso."
        : "Nao foi possivel testar o provider. Verifique a chave e o modelo.",
  };
}

function normalizeAiProvider(value: unknown): AiProvider {
  return value === "gemini" || value === "openai_future" || value === "local" ? value : "local";
}

function normalizeAiStatus(value: unknown): AiSettingsStatus {
  return value === "configured" ||
    value === "not_configured" ||
    value === "planned" ||
    value === "error" ||
    value === "ready"
    ? value
    : "not_configured";
}

function normalizeAnalysisMode(value: unknown): "local" | "ai" | "fallback" {
  return value === "ai" || value === "fallback" || value === "local" ? value : "local";
}

function normalizeAuthenticatedBrowserStatus(value: unknown): AuthenticatedBrowserStatus {
  const raw = asRecord(value);
  return {
    available: asBoolean(raw.available, false),
    endpoint: asString(raw.endpoint) || "http://127.0.0.1:9222",
    browser: asString(raw.browser),
    message: asString(raw.message),
  };
}

function normalizeAuthenticatedBrowserCollect(value: unknown): AuthenticatedBrowserCollectResult {
  const raw = asRecord(value);
  return {
    new_count: asNumber(raw.new_count, 0),
    duplicate_count: asNumber(raw.duplicate_count, 0),
    updated_count: asNumber(raw.updated_count, 0),
    failures: stringList(raw.failures),
    opportunities: objectList(raw.opportunities).map((item) => ({
      title: asString(item.title) || "Oportunidade coletada",
      company: asString(item.company),
      source_url: asString(item.source_url),
      confidence: asNumber(item.confidence, 0),
    })),
  };
}

function normalizeResumeExtract(value: unknown): ResumeExtractResult {
  const raw = asRecord(value);
  return {
    profile: normalizeResumeProfile(raw.profile),
    confidence: asNumber(raw.confidence, 0),
    provider_used: asString(raw.provider_used) || "local",
    requested_provider: asString(raw.requested_provider) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    fallback_used: asBoolean(raw.fallback_used, false),
    low_confidence_fields: stringList(raw.low_confidence_fields),
  };
}

function normalizeResumeProfile(value: unknown): ResumeProfile {
  const raw = asRecord(value);
  const experience = objectList(raw.experience).length
    ? objectList(raw.experience).map((item) => ({
        role: asString(item.role) || "Experiencia",
        company: asString(item.company),
        period: asString(item.period),
        highlights: stringList(item.highlights),
      }))
    : stringList(raw.experiences).map(experienceFromText);

  return {
    id: asString(raw.id),
    name: asString(raw.name) || "Perfil sem nome",
    headline: asString(raw.headline) || firstSentence(asString(raw.summary)),
    email: asString(raw.email),
    location: asString(raw.location) || asString(raw.city),
    seniority: asString(raw.seniority),
    summary: asString(raw.summary),
    skills: stringList(raw.skills),
    experience,
    education: objectOrTextList(raw.education, "Formacao").map((item) => ({
      name: asString(item.name),
      institution: asString(item.institution),
      status: asString(item.status),
    })),
    projects: objectOrTextList(raw.projects, "Projeto").map((item) => ({
      name: asString(item.name),
      description: asString(item.description),
      links: stringList(item.links),
    })),
  };
}

function normalizeJobExtract(value: unknown): JobExtractResult {
  const raw = asRecord(value);
  return {
    job: normalizeJobPosting(raw.job),
    confidence: asNumber(raw.confidence, 0),
    provider_used: asString(raw.provider_used) || "local",
    requested_provider: asString(raw.requested_provider) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    fallback_used: asBoolean(raw.fallback_used, false),
    low_confidence_fields: stringList(raw.low_confidence_fields),
  };
}

function normalizeJobPosting(value: unknown): JobPosting {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    title: asString(raw.title) || "Vaga sem titulo",
    company: asString(raw.company),
    source: asString(raw.source) || asString(raw.source_url),
    modality: asString(raw.modality),
    seniority: asString(raw.seniority),
    domain: asString(raw.domain),
    required_skills: stringList(raw.required_skills),
    preferred_skills: stringList(raw.preferred_skills).length
      ? stringList(raw.preferred_skills)
      : stringList(raw.desired_skills),
    desired_skills: stringList(raw.desired_skills),
    ats_keywords: stringList(raw.ats_keywords),
    responsibilities: stringList(raw.responsibilities),
  };
}

function normalizeMatchEnvelope(value: unknown): MatchAnalyzeResult {
  const raw = asRecord(value);
  return {
    provider_used: asString(raw.provider_used) || "local",
    requested_provider: asString(raw.requested_provider) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    fallback_used: asBoolean(raw.fallback_used, false),
    model: asString(raw.model),
    local_first: asBoolean(raw.local_first, true),
    memory_shared_with_provider: asBoolean(raw.memory_shared_with_provider, false),
    analysis: normalizeMatch(raw.analysis),
  };
}

function normalizeMatch(value: unknown): MatchAnalysis {
  const raw = asRecord(value);
  return {
    analysis_version: "compatibility_v1",
    match_score: asNumber(raw.match_score, 0),
    confidence_score: asNumber(raw.confidence_score, 0),
    evidence_score: asNumber(raw.evidence_score, 0),
    ats_score: asNumber(raw.ats_score, 0),
    opportunity_fit_score: asNumber(raw.opportunity_fit_score, 0),
    risk_score: asNumber(raw.risk_score, 0),
    domain: asString(raw.domain),
    recommendation: asString(raw.recommendation),
    matched_requirements: requirementList(raw.matched_requirements),
    partial_requirements: requirementList(raw.partial_requirements),
    missing_requirements: requirementList(
      arrayFrom(raw.missing_requirements).length ? raw.missing_requirements : raw.missing_keywords,
    ),
    critical_gaps: requirementList(raw.critical_gaps),
    transferable_skills: stringList(raw.transferable_skills),
    safe_actions: stringList(raw.safe_actions).length
      ? stringList(raw.safe_actions)
      : stringList(raw.resume_improvements),
  };
}

function normalizeAts(value: unknown): AtsReview {
  const raw = asRecord(value);
  return {
    ats_score: asNumber(raw.ats_score, 0),
    present: stringList(raw.present),
    missing_but_safe_to_add_if_true: stringList(raw.missing_but_safe_to_add_if_true),
    missing_without_evidence: stringList(raw.missing_without_evidence),
    warnings: stringList(raw.warnings),
    ai_insights: stringList(raw.ai_insights),
    provider_used: asString(raw.provider_used) || "local",
    requested_provider: asString(raw.requested_provider) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    fallback_used: asBoolean(raw.fallback_used, false),
  };
}

function normalizeTailorEnvelope(value: unknown): ResumeTailorResult {
  const raw = asRecord(value);
  return {
    safe_to_export: asBoolean(raw.safe_to_export, false),
    tailor: normalizeTailor(raw.tailor),
    provider_used: asString(raw.provider_used) || "local",
    requested_provider: asString(raw.requested_provider) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    fallback_used: asBoolean(raw.fallback_used, false),
    ai_suggestions: stringList(raw.ai_suggestions),
  };
}

function normalizeTailor(value: unknown): ResumeTailor {
  const raw = asRecord(value);
  const conditional = objectList(raw.conditional_suggestions).map((item) => ({
    keyword: asString(item.keyword),
    text: asString(item.text),
  }));

  return {
    safe_keywords: stringList(raw.safe_keywords).length
      ? stringList(raw.safe_keywords)
      : stringList(raw.keywords_added),
    suggested_bullets: stringList(raw.suggested_bullets).length
      ? stringList(raw.suggested_bullets)
      : stringList(raw.improved_bullets),
    conditional_suggestions: conditional,
    warnings: stringList(raw.warnings),
    evidence_used: stringList(raw.evidence_used),
  };
}

function normalizeGithubEnvelope(value: unknown): GithubAnalyzeResult {
  const raw = asRecord(value);
  return {
    report: normalizeGithubReport(raw.report),
    provider_used: asString(raw.provider_used) || "local",
    requested_provider: asString(raw.requested_provider) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    fallback_used: asBoolean(raw.fallback_used, false),
  };
}

function normalizeGithubReport(value: unknown): GithubReport {
  const raw = asRecord(value);
  const identity = asRecord(raw.repository_identity || raw.repo);
  const scores = asRecord(raw.scores);
  const stack = asRecord(raw.tech_stack);
  const architecture = asRecord(raw.architecture);
  const security = asRecord(raw.security);
  const verdict = asRecord(raw.final_verdict);

  return {
    repo: {
      owner: asString(identity.owner) || "unknown",
      name: asString(identity.name) || "repository",
      url: asString(identity.url),
      visibility: asString(identity.visibility) || "public",
    },
    quality_score: asNumber(raw.quality_score, asNumber(scores.overall_score, 0)),
    evidence_score: asNumber(raw.evidence_score, asNumber(scores.resume_evidence_score, 0)),
    languages: normalizeLanguages(raw.languages, stack.languages),
    positive_signals: coalesceStrings(
      raw.positive_signals,
      architecture.positive_signals,
      raw.testing,
      raw.documentation,
    ),
    risks: coalesceStrings(
      raw.risks,
      raw.inconsistencies,
      security.security_flags,
      verdict.main_blockers,
    ),
    portfolio_suggestions: coalesceStrings(
      raw.portfolio_suggestions,
      raw.recommendations,
      verdict.next_3_actions,
    ),
  };
}

function normalizeExtensionStatus(value: unknown): ExtensionStatus {
  const raw = asRecord(value);
  return {
    available: asBoolean(raw.available, true),
    companion_url: asString(raw.companion_url) || "http://127.0.0.1:8765",
    capture_count: asNumber(raw.capture_count, 0),
    last_capture_at: asString(raw.last_capture_at),
    message: asString(raw.message),
  };
}

function normalizeExtensionCaptures(value: unknown): ExtensionCapturesResult {
  const raw = asRecord(value);
  return {
    captures: objectList(raw.captures).map((item) => ({
      id: asString(item.id),
      title: asString(item.title) || "Captura sem titulo",
      company: asString(item.company),
      url: asString(item.url),
      domain: asString(item.domain),
      kind: asString(item.kind),
      source: asString(item.source),
      status: asString(item.status) || "captured",
      tracker_id: asString(item.tracker_id),
      captured_at: asString(item.captured_at),
      updated_at: asString(item.updated_at),
    })),
  };
}

function normalizeExtensionImportJob(value: unknown): ExtensionImportJobResult {
  const raw = asRecord(value);
  return {
    capture_id: asString(raw.capture_id),
    job: normalizeJobPosting(raw.job),
    message: asString(raw.message),
  };
}

function normalizeExtensionImportTracker(value: unknown): ExtensionImportTrackerResult {
  const raw = asRecord(value);
  return {
    capture_id: asString(raw.capture_id),
    tracker_id: asString(raw.tracker_id),
    message: asString(raw.message),
    provider: asString(raw.provider) || "local",
  };
}

function normalizeExtensionImportGithub(value: unknown): ExtensionImportGithubResult {
  const raw = asRecord(value);
  return {
    capture_id: asString(raw.capture_id),
    report: Object.keys(asRecord(raw.report)).length
      ? normalizeGithubReport(raw.report)
      : undefined,
    message: asString(raw.message),
  };
}

function normalizeTrackerJobs(value: unknown): { jobs: TrackerJob[] } {
  return { jobs: arrayFrom(asRecord(value).jobs).map(normalizeTrackerJob) };
}

function normalizeTrackerJobEnvelope(value: unknown): { job: TrackerJob } {
  return { job: normalizeTrackerJob(asRecord(value).job) };
}

function normalizeTrackerJob(value: unknown): TrackerJob {
  const raw = asRecord(value);
  const analysis = asRecord(raw.analysis);
  return {
    id: asString(raw.id),
    title: asString(raw.title) || asString(raw.job_title) || "Vaga sem titulo",
    company: asString(raw.company),
    source: asString(raw.source) || asString(raw.source_url) || stringList(raw.source_domains)[0],
    status: normalizeStatus(asString(raw.status)),
    match_score: definedNumber(raw.match_score, analysis.match_score),
    ats_score: definedNumber(raw.ats_score, analysis.ats_score),
    created_at: asString(raw.created_at),
    updated_at: asString(raw.updated_at),
    notes: asString(raw.notes),
    requirements: stringList(raw.requirements).length
      ? stringList(raw.requirements)
      : stringList(analysis.missing_keywords),
  };
}

function normalizeTrackerMetrics(value: unknown): TrackerMetrics {
  const raw = asRecord(value);
  const metrics = asRecord(raw.metrics);
  return {
    total_saved: asNumber(raw.total_saved, asNumber(metrics.total_saved, 0)),
    total_applied: asNumber(raw.total_applied, asNumber(metrics.total_applied, 0)),
    by_status: numberRecord(raw.by_status),
    average_match_by_status: numberRecord(raw.average_match_by_status),
    average_ats: definedNumber(raw.average_ats, metrics.average_ats),
    response_rate: asNumber(raw.response_rate, 0),
    interview_rate: asNumber(raw.interview_rate, 0),
    offer_rate: asNumber(raw.offer_rate, 0),
    weekly_applications: objectList(raw.weekly_applications).map((item) => ({
      week: asString(item.week),
      count: asNumber(item.count, 0),
    })),
  };
}

function normalizeTrackerRequirements(value: unknown): TrackerRequirements {
  const raw = asRecord(value);
  return {
    top_requirements: objectList(raw.top_requirements).map((item) => ({
      name: asString(item.name),
      count: asNumber(item.count, 0),
      status_scope: asString(item.status_scope),
      sources: stringList(item.sources),
      candidate_has_evidence: asBoolean(item.candidate_has_evidence, false),
    })),
    critical_gaps: objectList(raw.critical_gaps).map((item) => ({
      name: asString(item.name),
      count: asNumber(item.count, 0),
      severity: asString(item.severity) || "medium",
      safe_action: asString(item.safe_action),
    })),
    requirements_by_source: objectList(raw.requirements_by_source).map((item) => ({
      source: asString(item.source),
      requirement: asString(item.requirement),
      count: asNumber(item.count, 0),
    })),
  };
}

function normalizeTrackerFunnel(value: unknown): TrackerFunnel {
  const raw = asRecord(value);
  return {
    stages: objectList(raw.stages).map((item) => ({
      status: asString(item.status),
      label: asString(item.label),
      count: asNumber(item.count, 0),
    })),
    conversion_rates: objectList(raw.conversion_rates).map((item) => ({
      from: asString(item.from) || asString(item.from_status),
      to: asString(item.to) || asString(item.to_status),
      rate: asNumber(item.rate, 0),
    })),
  };
}

function normalizeTrackerSources(value: unknown): TrackerSources {
  const raw = asRecord(value);
  return {
    sources: objectList(raw.sources).map((item) => ({
      name: asString(item.name),
      saved: asNumber(item.saved, 0),
      applied: asNumber(item.applied, 0),
      interviews: asNumber(item.interviews, 0),
      average_match: asNumber(item.average_match, 0),
      top_requirements: stringList(item.top_requirements),
    })),
  };
}

function requirementList(value: unknown): MatchRequirement[] {
  return arrayFrom(value).map((item) => {
    if (typeof item === "string") return { name: item };
    const raw = asRecord(item);
    return {
      name: asString(raw.name) || asString(raw.requirement) || "Requisito",
      category: asString(raw.category),
      evidence: stringList(raw.evidence),
      reason: asString(raw.reason),
    };
  });
}

function normalizeLanguages(primary: unknown, fallback: unknown): GithubReport["languages"] {
  const objects = objectList(primary);
  if (objects.length) {
    return objects.map((item) => ({
      name: asString(item.name),
      percent: asNumber(item.percent, 0),
    }));
  }

  const names = stringList(fallback);
  if (!names.length) return [];
  const percent = Math.round(100 / names.length);
  return names.map((name) => ({ name, percent }));
}

function coalesceStrings(...values: unknown[]): string[] {
  for (const value of values) {
    const strings = stringList(value);
    if (strings.length) return strings;
  }
  return [];
}

function objectOrTextList(value: unknown, fallbackName: string): JsonRecord[] {
  const objects = objectList(value);
  if (objects.length) return objects;
  return stringList(value).map((text) => ({
    name: fallbackName,
    description: text,
    institution: text,
  }));
}

function experienceFromText(text: string): NonNullable<ResumeProfile["experience"]>[number] {
  const [role = "Experiencia", rest = ""] = text.split(/\s+[—-]\s+/, 2);
  return {
    role: role.trim() || "Experiencia",
    company: rest.trim(),
    period: "",
    highlights: [text],
  };
}

function normalizeStatus(value: string): TrackerJob["status"] {
  const aliases: Record<string, TrackerJob["status"]> = {
    ready_to_apply: "good_fit",
    tech_test: "technical_test",
    saved: "analyzed",
    response: "follow_up",
  };
  if (aliases[value]) return aliases[value];

  const allowed: TrackerJob["status"][] = [
    "found",
    "analyzed",
    "good_fit",
    "applied",
    "message_sent",
    "follow_up",
    "technical_test",
    "interview",
    "offer",
    "rejected",
    "archived",
  ];
  return allowed.includes(value as TrackerJob["status"])
    ? (value as TrackerJob["status"])
    : "found";
}

function numberRecord(value: unknown): Record<string, number> {
  return Object.fromEntries(
    Object.entries(asRecord(value)).map(([key, item]) => [key, asNumber(item, 0)]),
  );
}

function definedNumber(...values: unknown[]): number | undefined {
  for (const value of values) {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() && Number.isFinite(Number(value)))
      return Number(value);
  }
  return undefined;
}

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonRecord) : {};
}

function objectList(value: unknown): JsonRecord[] {
  return arrayFrom(value)
    .map(asRecord)
    .filter((item) => Object.keys(item).length > 0);
}

function arrayFrom(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function stringList(value: unknown): string[] {
  return arrayFrom(value)
    .flatMap((item) => {
      if (typeof item === "string") return [item];
      const raw = asRecord(item);
      return [
        asString(raw.description) ||
          asString(raw.name) ||
          asString(raw.bullet) ||
          asString(raw.recommendation),
      ];
    })
    .map((item) => item.trim())
    .filter(Boolean);
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asNumber(value: unknown, fallback: number): number {
  const parsed = definedNumber(value);
  return parsed ?? fallback;
}

function asBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function firstSentence(value: string): string {
  return value.split(/[.!?]/)[0]?.trim() ?? "";
}

export type Api = ReturnType<typeof makeApi>;
