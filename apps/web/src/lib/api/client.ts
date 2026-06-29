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
  ExtensionCapturePatchResult,
  ExtensionImportGithubResult,
  ExtensionImportJobResult,
  ExtensionImportTrackerResult,
  ExtensionStatus,
  GithubAnalyzeResult,
  GithubReport,
  Health,
  ImportBatch,
  JobExtractResult,
  JobPosting,
  JobWishlist,
  MatchAnalysis,
  MatchAnalyzeResult,
  MatchRequirement,
  ProfileDeduplicateResult,
  ProfileImportResult,
  ProfileItem,
  ProfileItemResult,
  ProfileResult,
  RadarAlert,
  RadarAlertResult,
  RadarAlertsResult,
  RadarResult,
  RadarResultEnvelope,
  RadarResultsResult,
  RadarRun,
  RadarRunResult,
  RadarRunsResult,
  RadarSaveInboxResult,
  RadarSaveTrackerResult,
  RadarSource,
  RadarSourceResult,
  RadarSourcesResult,
  RadarStats,
  WishlistDraftResult,
  RadarWishlistResult,
  RadarWishlistsResult,
  ResumeExtractResult,
  ResumeProfile,
  ResumeTailor,
  ResumeTailorResult,
  SourceCaptureImportJobResult,
  SourceCaptureResult,
  SourceCaptureSaveTrackerResult,
  SourceDirectoryResult,
  SourceDedupeResult,
  SourceExportResult,
  SourceImportResult,
  SourceImportsResult,
  SourceStats,
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

    profile: () =>
      call<ProfileResult>(
        mode,
        baseUrl,
        "/profile",
        undefined,
        mockProfileResult(),
        normalizeProfileResult,
      ),

    profileSave: (payload: Partial<ProfileResult["profile"]>) =>
      call<ProfileResult>(
        mode,
        baseUrl,
        "/profile",
        { method: "PUT", body: JSON.stringify(payload) },
        mockSavedProfile(payload),
        normalizeProfileResult,
      ),

    profileAddItem: (payload: Partial<ProfileItem>) =>
      call<ProfileItemResult>(
        mode,
        baseUrl,
        "/profile/items",
        { method: "POST", body: JSON.stringify(payload) },
        { item: normalizeProfileItem({ ...payload, confirmed_by_user: true }), message: "Demo" },
        normalizeProfileItemResult,
      ),

    profilePatchItem: (itemId: string, payload: Partial<ProfileItem>) =>
      call<ProfileItemResult>(
        mode,
        baseUrl,
        `/profile/items/${encodeURIComponent(itemId)}`,
        { method: "PATCH", body: JSON.stringify(payload) },
        { item: normalizeProfileItem({ ...payload, item_id: itemId, confirmed_by_user: true }) },
        normalizeProfileItemResult,
      ),

    profileDeleteItem: (itemId: string) =>
      call<ProfileResult>(
        mode,
        baseUrl,
        `/profile/items/${encodeURIComponent(itemId)}`,
        { method: "DELETE" },
        mockProfileResult(),
        normalizeProfileResult,
      ),

    profileImportText: (payload: {
      text: string;
      source_type: string;
      use_ai: boolean;
      language?: string;
    }) =>
      call<ProfileImportResult>(
        mode,
        baseUrl,
        "/profile/import-text",
        { method: "POST", body: JSON.stringify(payload) },
        mockProfileImport(payload.text, payload.source_type, payload.use_ai),
        normalizeProfileImportResult,
      ),

    profileDeduplicate: () =>
      call<ProfileDeduplicateResult>(
        mode,
        baseUrl,
        "/profile/deduplicate",
        { method: "POST" },
        { suggestions: [], message: "Sem duplicidades no modo demo." },
        normalizeProfileDeduplicateResult,
      ),

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

    extensionPatchCapture: (capture_id: string, status: string) =>
      call<ExtensionCapturePatchResult>(
        mode,
        baseUrl,
        `/extension/captures/${capture_id}`,
        { method: "PATCH", body: JSON.stringify({ status }) },
        {
          capture: {
            ...(mockSourceImports().items[2]
              ? {
                  id: "demo-capture-1",
                  title: "Backend Python Demo",
                  company: "Empresa Demo",
                  url: "https://example.invalid/jobs/backend",
                  domain: "example.invalid",
                  kind: "job",
                  source: "Extensao local demo",
                  status,
                }
              : {}),
          } as ExtensionCapturePatchResult["capture"],
          message: "Modo Demo: captura atualizada.",
        },
        normalizeExtensionPatchCapture,
      ),

    sourceImports: () =>
      call<SourceImportsResult>(
        mode,
        baseUrl,
        "/sources/imports",
        undefined,
        mockSourceImports(),
        normalizeSourceImports,
      ),

    sourceImportText: (payload: {
      text: string;
      url?: string;
      company?: string;
      title?: string;
      source_name?: string;
      notes?: string;
      use_ai?: boolean;
    }) =>
      call<SourceImportResult>(
        mode,
        baseUrl,
        "/sources/imports/text",
        { method: "POST", body: JSON.stringify(payload) },
        mockSourceImport(payload, "manual_text"),
        normalizeSourceImport,
      ),

    sourceImportUrl: (payload: {
      url: string;
      source_name?: string;
      notes?: string;
      use_ai?: boolean;
    }) =>
      call<SourceImportResult>(
        mode,
        baseUrl,
        "/sources/imports/url",
        { method: "POST", body: JSON.stringify(payload) },
        mockSourceImport(
          {
            text: "Cargo: Backend Python Demo\nEmpresa: Empresa Demo\nRequisitos: Python e APIs.",
            url: payload.url,
            title: "Backend Python Demo",
            company: "Empresa Demo",
            source_name: payload.source_name || "Link manual demo",
            notes: payload.notes,
          },
          "manual_url",
        ),
        normalizeSourceImport,
      ),

    sourceImportCsv: (payload: { csv_text: string; source_name?: string; use_ai?: boolean }) =>
      call<SourceImportResult>(
        mode,
        baseUrl,
        "/sources/imports/csv",
        { method: "POST", body: JSON.stringify(payload) },
        mockBatchImport("csv_import", payload.source_name || "CSV Manual"),
        normalizeSourceImport,
      ),

    sourceImportJson: (payload: {
      items?: Record<string, unknown>[];
      json_text?: string;
      source_name?: string;
      use_ai?: boolean;
    }) =>
      call<SourceImportResult>(
        mode,
        baseUrl,
        "/sources/imports/json",
        { method: "POST", body: JSON.stringify(payload) },
        mockBatchImport("json_import", payload.source_name || "JSON Manual"),
        normalizeSourceImport,
      ),

    sourcePatchCapture: (
      id: string,
      payload: { status?: string; notes?: string; duplicate_of?: string },
    ) =>
      call<SourceCaptureResult>(
        mode,
        baseUrl,
        `/sources/captures/${id}`,
        { method: "PATCH", body: JSON.stringify(payload) },
        {
          capture: {
            ...(mockSourceImports().items.find((item) => item.id === id) ??
              mockSourceImports().items[0]!),
            status: (payload.status as SourceCaptureResult["capture"]["status"]) || "reviewed",
            notes: payload.notes,
            duplicate_of: payload.duplicate_of,
          },
          message: "Modo Demo: item atualizado.",
        },
        normalizeSourceCaptureResult,
      ),

    sourceMergeCapture: (id: string, payload: { duplicate_of: string; notes?: string }) =>
      call<SourceCaptureResult>(
        mode,
        baseUrl,
        `/sources/captures/${id}/merge`,
        { method: "POST", body: JSON.stringify(payload) },
        {
          capture: {
            ...(mockSourceImports().items.find((item) => item.id === id) ??
              mockSourceImports().items[1]!),
            status: "archived",
            duplicate_of: payload.duplicate_of,
            notes: payload.notes || "Modo Demo: duplicata mesclada com histórico preservado.",
          },
          message: "Modo Demo: duplicata mesclada com histórico preservado.",
        },
        normalizeSourceCaptureResult,
      ),

    sourceImportCaptureJob: (id: string) =>
      call<SourceCaptureImportJobResult>(
        mode,
        baseUrl,
        `/sources/captures/${id}/import-job`,
        { method: "POST" },
        {
          capture: mockSourceImports().items[0]!,
          job: { ...mockJob },
          message: "Modo Demo: item importado para Vaga.",
        },
        normalizeSourceCaptureImportJob,
      ),

    sourceSaveCaptureTracker: (id: string) =>
      call<SourceCaptureSaveTrackerResult>(
        mode,
        baseUrl,
        `/sources/captures/${id}/save-tracker`,
        { method: "POST" },
        {
          capture: { ...mockSourceImports().items[0]!, status: "saved_to_tracker" },
          tracker_id: `job_${Math.random().toString(36).slice(2, 8)}`,
          message: "Modo Demo: item salvo em Candidaturas.",
        },
        normalizeSourceCaptureSaveTracker,
      ),

    sourceDedupe: () =>
      call<SourceDedupeResult>(
        mode,
        baseUrl,
        "/sources/dedupe",
        { method: "POST" },
        {
          duplicates: [
            {
              item_id: "source-demo-duplicate",
              duplicate_of: "source-demo-text",
              decision: "possible_duplicate",
              reason: "URL normalizada igual.",
              confidence: 0.92,
            },
          ],
        },
        normalizeSourceDedupe,
      ),

    sourceDirectory: (query = "") =>
      call<SourceDirectoryResult>(
        mode,
        baseUrl,
        `/sources/directory${query ? `?query=${encodeURIComponent(query)}` : ""}`,
        undefined,
        mockSourceDirectory(query),
        normalizeSourceDirectory,
      ),

    sourceExport: (payload: { format: "csv" | "json"; item_ids?: string[] }) =>
      call<SourceExportResult>(
        mode,
        baseUrl,
        "/sources/export",
        { method: "POST", body: JSON.stringify(payload) },
        mockSourceExport(payload.format, payload.item_ids),
        normalizeSourceExport,
      ),

    sourceStats: () =>
      call<SourceStats>(
        mode,
        baseUrl,
        "/sources/stats",
        undefined,
        {
          total: 4,
          duplicates: 1,
          errors: 0,
          saved_to_tracker: 1,
          by_status: { new: 2, duplicate: 1, saved_to_tracker: 1 },
          by_origin: { manual_text: 1, csv_import: 1, extension_capture: 1, public_feed: 1 },
        },
        normalizeSourceStats,
      ),

    radarWishlists: () =>
      call<RadarWishlistsResult>(
        mode,
        baseUrl,
        "/radar/wishlists",
        undefined,
        mockRadarWishlists(),
        normalizeRadarWishlists,
      ),

    radarCreateWishlist: (payload: Partial<JobWishlist>) =>
      call<RadarWishlistResult>(
        mode,
        baseUrl,
        "/radar/wishlists",
        { method: "POST", body: JSON.stringify(payload) },
        {
          wishlist: { ...mockRadarWishlists().wishlists[0]!, ...payload },
          message: "Modo Demo: wishlist criada.",
        },
        normalizeRadarWishlistResult,
      ),

    radarDraftWishlist: (payload: {
      free_text: string;
      use_profile_context?: boolean;
      language?: string;
    }) =>
      call<WishlistDraftResult>(
        mode,
        baseUrl,
        "/radar/wishlists/draft",
        { method: "POST", body: JSON.stringify(payload) },
        mockWishlistDraft(payload.free_text),
        normalizeWishlistDraft,
      ),

    radarSources: () =>
      call<RadarSourcesResult>(
        mode,
        baseUrl,
        "/radar/sources",
        undefined,
        mockRadarSources(),
        normalizeRadarSources,
      ),

    radarCreateSource: (payload: Partial<RadarSource>) =>
      call<RadarSourceResult>(
        mode,
        baseUrl,
        "/radar/sources",
        { method: "POST", body: JSON.stringify(payload) },
        {
          source: { ...mockRadarSources().sources[0]!, ...payload },
          message: "Modo Demo: fonte criada.",
        },
        normalizeRadarSourceResult,
      ),

    radarRun: (payload: {
      source_ids?: string[];
      wishlist_id?: string;
      resume_text?: string;
      keywords?: string[];
      use_ai?: boolean;
    }) =>
      call<RadarRunResult>(
        mode,
        baseUrl,
        "/radar/run",
        { method: "POST", body: JSON.stringify(payload) },
        mockRadarRun(payload),
        normalizeRadarRunResult,
      ),

    radarRuns: () =>
      call<RadarRunsResult>(
        mode,
        baseUrl,
        "/radar/runs",
        undefined,
        mockRadarRuns(),
        normalizeRadarRuns,
      ),

    radarResults: () =>
      call<RadarResultsResult>(
        mode,
        baseUrl,
        "/radar/results",
        undefined,
        mockRadarResults(),
        normalizeRadarResults,
      ),

    radarPatchResult: (id: string, payload: { status?: string }) =>
      call<RadarResultEnvelope>(
        mode,
        baseUrl,
        `/radar/results/${id}`,
        { method: "PATCH", body: JSON.stringify(payload) },
        {
          result: {
            ...(mockRadarResults().results.find((item) => item.id === id) ??
              mockRadarResults().results[0]!),
            radar_status: (payload.status as RadarResult["radar_status"]) || "ignored",
          },
          message: "Modo Demo: resultado atualizado.",
        },
        normalizeRadarResultEnvelope,
      ),

    radarSaveInbox: (id: string) =>
      call<RadarSaveInboxResult>(
        mode,
        baseUrl,
        `/radar/results/${id}/save-inbox`,
        { method: "POST" },
        {
          result: { ...mockRadarResults().results[0]!, radar_status: "saved_to_inbox" },
          inbox_item: {
            ...mockSourceImports().items[0]!,
            source_name: "Radar - Feed publico",
            origin: "public_feed",
            metadata: { source_flow: "job_radar", radar_result_id: id },
          },
          message: "Modo Demo: resultado salvo na Caixa de Entrada.",
        },
        normalizeRadarSaveInbox,
      ),

    radarSaveTracker: (id: string) =>
      call<RadarSaveTrackerResult>(
        mode,
        baseUrl,
        `/radar/results/${id}/save-tracker`,
        { method: "POST" },
        {
          result: { ...mockRadarResults().results[0]!, radar_status: "saved_to_tracker" },
          tracker_id: `job_${Math.random().toString(36).slice(2, 8)}`,
          message: "Modo Demo: resultado salvo em Candidaturas.",
        },
        normalizeRadarSaveTracker,
      ),

    radarAlerts: () =>
      call<RadarAlertsResult>(
        mode,
        baseUrl,
        "/radar/alerts",
        undefined,
        mockRadarAlerts(),
        normalizeRadarAlerts,
      ),

    radarPatchAlert: (id: string, payload: { status?: string }) =>
      call<RadarAlertResult>(
        mode,
        baseUrl,
        `/radar/alerts/${id}`,
        { method: "PATCH", body: JSON.stringify(payload) },
        {
          alert: {
            ...(mockRadarAlerts().alerts.find((item) => item.id === id) ??
              mockRadarAlerts().alerts[0]!),
            status: (payload.status as RadarAlert["status"]) || "read",
          },
          message: "Modo Demo: alerta atualizado.",
        },
        normalizeRadarAlertResult,
      ),

    radarStats: () =>
      call<RadarStats>(
        mode,
        baseUrl,
        "/radar/stats",
        undefined,
        mockRadarStats(),
        normalizeRadarStats,
      ),
  };
}

function mockSourceImports(): SourceImportsResult {
  const now = new Date().toISOString();
  return {
    items: [
      {
        id: "source-demo-text",
        title: "Analista de Dados Demo",
        company: "Empresa Exemplo",
        source_type: "manual_text",
        source_name: "Texto manual",
        source_url: "https://example.com/jobs/123",
        origin: "manual_text",
        captured_at: now,
        imported_at: now,
        status: "new",
        raw_text: "Cargo: Analista de Dados\nEmpresa: Empresa Exemplo\nRequisitos: Python e SQL.",
        job_url: "https://example.com/jobs/123",
        location: "Remoto",
        work_model: "remote",
        seniority: "junior",
        domain: "example.com",
        tags: ["Python", "SQL", "dashboards"],
        source_confidence: 0.82,
        notes: "vaga ficticia",
        metadata: {
          analysis_mode: "local",
          summary: "Vaga fictícia para demonstração de importação.",
          priority: "media",
        },
      },
      {
        id: "source-demo-duplicate",
        title: "Analista de Dados",
        company: "Empresa Exemplo",
        source_type: "csv_import",
        source_name: "CSV Manual",
        source_url: "https://example.com/jobs/123?utm=demo",
        origin: "csv_import",
        captured_at: now,
        imported_at: now,
        status: "duplicate",
        raw_text: "Python, SQL e dashboards.",
        job_url: "https://example.com/jobs/123?utm=demo",
        location: "Remoto",
        domain: "example.com",
        tags: ["Python", "SQL"],
        source_confidence: 0.72,
        duplicate_of: "source-demo-text",
        notes: "possivel duplicata ficticia",
        metadata: {
          analysis_mode: "local",
          duplicate_explanation: "URL normalizada igual ao item de texto manual.",
          priority: "media",
        },
      },
      {
        id: "source-demo-extension",
        title: "Backend Python Demo",
        company: "Empresa Demo",
        source_type: "extension_capture",
        source_name: "Extensao Local",
        source_url: "https://example.invalid/jobs/backend",
        origin: "extension_capture",
        captured_at: now,
        imported_at: now,
        status: "saved_to_tracker",
        raw_text: "Cargo: Backend Python\nRequisitos: FastAPI e testes.",
        job_url: "https://example.invalid/jobs/backend",
        location: "Hibrido",
        domain: "example.invalid",
        tags: ["Python", "FastAPI", "testes"],
        source_confidence: 0.8,
        notes: "captura ficticia",
        metadata: {
          analysis_mode: "local",
          summary: "Captura fictícia da extensão local.",
          priority: "media",
        },
      },
      {
        id: "source-demo-radar",
        title: "Desenvolvedor Backend Python",
        company: "Empresa Radar Demo",
        source_type: "public_feed",
        source_name: "Radar - Feed publico",
        source_url: "https://example.com/jobs/radar-1",
        origin: "public_feed",
        captured_at: now,
        imported_at: now,
        status: "new",
        raw_text: "Cargo: Desenvolvedor Backend Python\nRequisitos: Python, FastAPI e SQL.",
        job_url: "https://example.com/jobs/radar-1",
        location: "Remoto",
        work_model: "remote",
        domain: "example.com",
        tags: ["Python", "FastAPI", "Radar"],
        source_confidence: 0.82,
        match_score: 82,
        ats_score: 76,
        notes: "resultado ficticio do Radar",
        metadata: {
          source_flow: "job_radar",
          radar_score: 82,
          analysis_mode: "local",
        },
      },
    ],
    batches: [
      {
        id: "batch-demo",
        origin: "manual_text",
        source_name: "Demo",
        created_at: now,
        total: 4,
        imported: 4,
        errors: 0,
        duplicates: 1,
        warnings: [],
        item_ids: [
          "source-demo-text",
          "source-demo-duplicate",
          "source-demo-extension",
          "source-demo-radar",
        ],
      },
    ],
  };
}

function mockSourceImport(
  payload: {
    text?: string;
    url?: string;
    title?: string;
    company?: string;
    source_name?: string;
    notes?: string;
  },
  origin: SourceImportsResult["items"][number]["origin"],
): SourceImportResult {
  const now = new Date().toISOString();
  const item = {
    id: `source_${Math.random().toString(36).slice(2, 8)}`,
    title: payload.title || "Vaga importada demo",
    company: payload.company || "Empresa Exemplo",
    source_type: origin,
    source_name: payload.source_name || "Importacao demo",
    source_url: payload.url || "",
    origin,
    captured_at: now,
    imported_at: now,
    status: "new" as const,
    raw_text: payload.text || "",
    job_url: payload.url || "",
    location: "Remoto",
    work_model: "remote",
    tags: ["Python", "SQL"],
    source_confidence: 0.76,
    notes: payload.notes || "",
    metadata: {
      analysis_mode: "local",
      summary: "Importação fictícia do modo Demo.",
      priority: "media",
    },
  };
  return {
    batch: {
      id: `batch_${Math.random().toString(36).slice(2, 8)}`,
      origin,
      source_name: item.source_name,
      source_url: item.source_url,
      created_at: now,
      total: 1,
      imported: 1,
      errors: 0,
      duplicates: 0,
      warnings: [],
      item_ids: [item.id],
    },
    items: [item],
    message: "Modo Demo: importacao concluida.",
  };
}

function mockBatchImport(
  origin: SourceImportsResult["items"][number]["origin"],
  sourceName: string,
): SourceImportResult {
  const first = mockSourceImport(
    {
      title: origin === "csv_import" ? "Analista de Dados" : "Desenvolvedor Backend",
      company: origin === "csv_import" ? "Empresa Exemplo" : "Tech Exemplo",
      url:
        origin === "csv_import" ? "https://example.com/jobs/123" : "https://example.com/jobs/456",
      source_name: sourceName,
      text: "Python, SQL, APIs e testes.",
    },
    origin,
  );
  return {
    ...first,
    batch: { ...first.batch, total: 2, imported: 2, duplicates: 1 },
    message: "Modo Demo: importacao concluida: 2 itens, 1 duplicado.",
  };
}

function mockSourceDirectory(query: string): SourceDirectoryResult {
  const sources: SourceDirectoryResult["sources"] = [
    {
      id: "open-career-pages",
      name: "Páginas de carreira abertas",
      kind: "public_career_page",
      status: "planned",
      observation: "Leitura pública simples futura, sempre com revisão manual.",
      requires_manual_review: true,
    },
    {
      id: "public-rss-feeds",
      name: "Feeds RSS públicos",
      kind: "public_feed",
      status: "available",
      observation: "RSS/Atom publico disponivel no Radar de Vagas com refresh manual.",
      requires_manual_review: true,
    },
    {
      id: "official-apis",
      name: "APIs oficiais",
      kind: "official_api",
      status: "future",
      observation: "Somente APIs documentadas, com chave do usuário quando aplicável.",
      requires_manual_review: true,
    },
    {
      id: "recurring-csv-json",
      name: "CSV/JSON recorrente",
      kind: "recurring_csv_json",
      status: "available",
      observation: "Importação manual recorrente com preview e confirmação.",
      requires_manual_review: true,
    },
    {
      id: "manual-links",
      name: "Links manuais",
      kind: "manual_link",
      status: "available",
      observation: "Links adicionados pelo usuário e revisados na Caixa de Entrada.",
      requires_manual_review: true,
    },
  ];
  const normalizedQuery = query.trim().toLowerCase();
  return {
    sources: normalizedQuery
      ? sources.filter((source) =>
          [source.name, source.kind, source.status, source.observation]
            .join(" ")
            .toLowerCase()
            .includes(normalizedQuery),
        )
      : sources,
    query,
    warnings: [
      "Modo Demo: diretório seguro, sem login automático, bypass de CAPTCHA ou auto-apply.",
    ],
  };
}

function mockSourceExport(format: "csv" | "json", itemIds?: string[]): SourceExportResult {
  const items = mockSourceImports().items.filter(
    (item) => !itemIds?.length || itemIds.includes(item.id),
  );
  if (format === "json") {
    return {
      format,
      filename: "sotuhire-opportunities-demo.json",
      content: JSON.stringify(items, null, 2),
      item_count: items.length,
    };
  }
  const header = "cargo,empresa,link,origem,status,data,score,ats_score,tags,notas";
  const rows = items.map((item) =>
    [
      item.title,
      item.company || "",
      item.job_url || item.source_url || "",
      item.origin,
      item.status,
      item.imported_at || item.captured_at || "",
      item.match_score ?? "",
      item.ats_score ?? "",
      item.tags.join("; "),
      item.notes || "",
    ]
      .map((cell) => `"${String(cell).replaceAll('"', '""')}"`)
      .join(","),
  );
  return {
    format,
    filename: "sotuhire-opportunities-demo.csv",
    content: [header, ...rows].join("\n"),
    item_count: items.length,
  };
}

function mockWishlistDraft(freeText: string): WishlistDraftResult {
  const normalized = freeText.toLowerCase();
  const isHealth = /enferm|coren|hospital|saúde|saude/.test(normalized);
  const isLaw = /direito|juríd|jurid|oab|advoc/.test(normalized);
  const isArt = /design|arte|ilustra|portfólio|portfolio/.test(normalized);
  const isResearch = /pesquisa|lattes|laborat|congresso/.test(normalized);
  const domain = isHealth
    ? "Saúde"
    : isLaw
      ? "Direito"
      : isArt
        ? "Artes e Design"
        : isResearch
          ? "Pesquisa e Laboratório"
          : "Engenharia e Operações";
  const title = isHealth
    ? "Enfermeiro"
    : isLaw
      ? "Advogado Júnior"
      : isArt
        ? "Designer"
        : isResearch
          ? "Assistente de Pesquisa"
          : "Estágio em Engenharia";
  const skills = isHealth
    ? ["COREN", "triagem", "prontuário"]
    : isLaw
      ? ["OAB", "petições", "pesquisa jurídica"]
      : isArt
        ? ["portfólio", "identidade visual", "ilustração"]
        : isResearch
          ? ["Lattes", "metodologia", "relatório"]
          : ["Excel", "relatórios técnicos", "qualidade"];
  return {
    wishlist: {
      name: `Wishlist sugerida - ${domain}`,
      target_titles: [title],
      target_domains: [domain],
      target_seniority:
        normalized.includes("estágio") || normalized.includes("estagio") ? ["estágio"] : ["júnior"],
      required_skills: skills,
      desired_skills: ["comunicação", "organização"],
      excluded_terms: normalized.includes("pj") ? ["PJ"] : [],
      locations: normalized.includes("remoto") ? ["Remoto", "Brasil"] : ["Brasil"],
      remote_preferences: normalized.includes("remoto") ? ["remoto"] : [],
      work_model: normalized.includes("remoto") ? "remoto" : "",
      employment_type: normalized.includes("clt") ? "CLT" : "",
      salary_currency: "BRL",
      contract_types: normalized.includes("clt") ? ["CLT"] : [],
      industries: [domain],
      companies_include: [],
      companies_exclude: [],
      source_types: ["public_feed", "manual_url", "manual_public_page"],
      min_match_score: 70,
      min_ats_score: 60,
      notify_on_new_matches: true,
      is_active: true,
      notes: "Modo Demo: rascunho fictício. Revise antes de salvar.",
    },
    confidence: 0.74,
    detected_domains: [domain],
    detected_career_moments:
      normalized.includes("estágio") || normalized.includes("estagio") ? ["estágio"] : ["júnior"],
    assumptions: ["Usei apenas sinais do texto digitado."],
    questions_to_confirm: [
      "Quais cargos você realmente aceita?",
      "Há termos que devem ser excluídos?",
    ],
    warnings: ["A wishlist não foi salva automaticamente."],
    needs_user_review: true,
    provider_used: "local",
    analysis_mode: "local",
  };
}

function mockRadarWishlists(): RadarWishlistsResult {
  const now = new Date().toISOString();
  return {
    wishlists: [
      {
        id: "radar-wishlist-demo",
        name: "Backend Python remoto",
        target_titles: ["Desenvolvedor Backend", "Engenheiro de APIs"],
        target_domains: ["tecnologia", "produto"],
        target_seniority: ["pleno", "junior"],
        required_skills: ["Python", "FastAPI", "SQL"],
        desired_skills: ["Pytest", "Docker"],
        excluded_terms: ["presencial integral"],
        locations: ["Remoto", "Brasil"],
        remote_preferences: ["remoto"],
        work_model: "remote",
        employment_type: "CLT",
        salary_currency: "BRL",
        contract_types: ["CLT"],
        industries: ["software"],
        companies_include: ["Empresa Exemplo"],
        companies_exclude: ["Empresa Bloqueada"],
        source_types: ["public_feed", "manual_url"],
        min_match_score: 70,
        min_ats_score: 40,
        notify_on_new_matches: true,
        notes: "Wishlist fictícia do modo Demo.",
        created_at: now,
        updated_at: now,
        is_active: true,
      },
    ],
  };
}

function mockRadarSources(): RadarSourcesResult {
  const now = new Date().toISOString();
  return {
    sources: [
      {
        id: "radar-source-feed-demo",
        name: "Feed publico ficticio",
        source_type: "public_feed",
        url: "https://example.com/jobs.xml",
        status: "available",
        is_active: true,
        requires_api_key: false,
        api_key_configured: false,
        max_results: 20,
        timeout_seconds: 6,
        rate_limit_seconds: 1,
        last_checked_at: now,
        notes: "RSS publico ficticio para modo Demo.",
        created_at: now,
        updated_at: now,
      },
      {
        id: "radar-source-api-demo",
        name: "API oficial planejada",
        source_type: "official_api",
        url: "https://api.example.com/jobs",
        docs_url: "https://example.com/docs",
        status: "requires_official_api",
        is_active: true,
        requires_api_key: false,
        api_key_configured: false,
        max_results: 20,
        timeout_seconds: 6,
        rate_limit_seconds: 1,
        notes: "Estrutura preparada; conector real depende de API documentada.",
        created_at: now,
        updated_at: now,
      },
    ],
    adapters: [
      {
        source_type: "public_feed",
        adapter_name: "RSS/Atom publico",
        supported: true,
        notes: "Refresh manual e revisao humana.",
      },
      {
        source_type: "official_api",
        adapter_name: "API oficial planejada",
        supported: false,
        notes: "Requer contrato oficial documentado.",
      },
    ],
  };
}

function mockRadarResults(): RadarResultsResult {
  const now = new Date().toISOString();
  return {
    results: [
      {
        id: "radar-result-demo-1",
        run_id: "radar-run-demo",
        source_id: "radar-source-feed-demo",
        source_name: "Feed publico ficticio",
        source_type: "public_feed",
        wishlist_id: "radar-wishlist-demo",
        title: "Desenvolvedor Backend Python",
        company: "Empresa Exemplo",
        url: "https://example.com/jobs/radar-1",
        location: "Remoto",
        work_model: "remote",
        employment_type: "CLT",
        description: "Vaga ficticia com Python, FastAPI, SQL e testes.",
        captured_at: now,
        dedupe_key: "url:https://example.com/jobs/radar-1",
        match_score: 84,
        ats_score: 76,
        wishlist_score: 82,
        radar_score: 82,
        radar_status: "matched",
        already_in_inbox: false,
        already_in_tracker: false,
        warnings: [],
        reasons: ["Cargo desejado encontrado.", "Habilidades obrigatorias encontradas."],
        evidence: ["Fonte cita Python, FastAPI e SQL.", "Modelo remoto aceito."],
        gaps: ["Validar se Docker e Pytest sao exigidos."],
        next_actions: [
          "Salvar na Caixa de Entrada.",
          "Rodar compatibilidade com curriculo antes de aplicar.",
        ],
        analysis_mode: "local",
        provider_used: "local",
        metadata: { tags: ["Python", "FastAPI"], source_flow: "job_radar" },
      },
      {
        id: "radar-result-demo-2",
        run_id: "radar-run-demo",
        source_id: "radar-source-feed-demo",
        source_name: "Feed publico ficticio",
        source_type: "public_feed",
        wishlist_id: "radar-wishlist-demo",
        title: "Analista de Dados",
        company: "Empresa Exemplo",
        url: "https://example.com/jobs/radar-2",
        location: "Hibrido",
        description: "Vaga ficticia com SQL e dashboards.",
        captured_at: now,
        dedupe_key: "url:https://example.com/jobs/radar-2",
        match_score: 58,
        ats_score: 52,
        wishlist_score: 55,
        radar_score: 55,
        radar_status: "new",
        already_in_inbox: false,
        already_in_tracker: false,
        warnings: ["Sinais abaixo do minimo da wishlist."],
        reasons: ["Tem SQL, mas cargo diferente."],
        evidence: ["Fonte cita SQL e dashboards."],
        gaps: ["Nao cita FastAPI.", "Modelo hibrido precisa revisao."],
        next_actions: ["Revisar manualmente antes de salvar."],
        analysis_mode: "local",
        provider_used: "local",
        metadata: { tags: ["SQL"], source_flow: "job_radar" },
      },
    ],
  };
}

function mockRadarRun(payload: {
  source_ids?: string[];
  wishlist_id?: string;
  use_ai?: boolean;
}): RadarRunResult {
  const now = new Date().toISOString();
  const results = mockRadarResults().results.map((result) =>
    payload.use_ai
      ? {
          ...result,
          analysis_mode: "ai" as const,
          provider_used: "gemini",
          next_actions: [...result.next_actions, "Revisar explicacao da IA antes de agir."],
        }
      : result,
  );
  const alerts = mockRadarAlerts().alerts;
  return {
    run: {
      id: `radar_run_${Math.random().toString(36).slice(2, 8)}`,
      started_at: now,
      finished_at: now,
      source_ids: payload.source_ids?.length ? payload.source_ids : ["radar-source-feed-demo"],
      wishlist_id: payload.wishlist_id || "radar-wishlist-demo",
      resume_used: false,
      total_sources: 1,
      total_found: results.length,
      total_deduped: 0,
      total_alerted: alerts.length,
      total_errors: 0,
      duration_ms: 420,
      warnings: [],
      errors: [],
      metadata: { mode: "demo" },
    },
    results,
    alerts,
    message: "Modo Demo: Radar concluido com vagas ficticias.",
  };
}

function mockRadarRuns(): RadarRunsResult {
  return { runs: [mockRadarRun({}).run] };
}

function mockRadarAlerts(): RadarAlertsResult {
  const now = new Date().toISOString();
  return {
    alerts: [
      {
        id: "radar-alert-demo-1",
        run_id: "radar-run-demo",
        result_id: "radar-result-demo-1",
        wishlist_id: "radar-wishlist-demo",
        title: "Nova vaga com 82% de aderencia",
        message: "Desenvolvedor Backend Python em Empresa Exemplo",
        score: 82,
        status: "unread",
        created_at: now,
        metadata: { source_name: "Feed publico ficticio" },
      },
    ],
  };
}

function mockRadarStats(): RadarStats {
  return {
    active_sources: 1,
    total_sources: 2,
    total_results: 2,
    new_results: 1,
    matched_results: 1,
    unread_alerts: 1,
    duplicates: 0,
    source_errors: 0,
    last_run_at: new Date().toISOString(),
  };
}

function mockProfileResult(): ProfileResult {
  const now = new Date().toISOString();
  return {
    profile: {
      profile_id: "default",
      display_name: "Perfil Demo",
      headline: "Estudante de engenharia com projetos academicos",
      summary: "Perfil ficticio para demonstrar como o SotuHire organiza evidencias de carreira.",
      primary_domains: ["Engenharia", "Pesquisa e Laboratorio"],
      secondary_domains: ["Dados"],
      career_moments: ["estagio", "estudante"],
      target_roles: ["Estagio em Engenharia", "Assistente Tecnico"],
      target_seniority: ["estagio"],
      preferred_locations: ["Sao Jose dos Campos", "Remoto"],
      preferred_work_models: ["hibrido", "remoto"],
      preferred_contract_types: ["estagio"],
      constraints: [],
      items: [
        {
          item_id: "profile-demo-item-1",
          type: "higher_education",
          title: "Engenharia em andamento",
          description: "Graduação fictícia em andamento no período noturno.",
          area: "Engenharia",
          domain: "Engenharia",
          institution: "Instituição Exemplo",
          organization: null,
          status: "em andamento",
          start_date: null,
          end_date: null,
          tags: ["formação"],
          skills: ["relatórios técnicos"],
          evidence: "Texto fictício de currículo informado pelo usuário.",
          source: "demo",
          source_ref: null,
          confidence: "high",
          confirmed_by_user: true,
          sensitive: false,
          created_at: now,
          updated_at: now,
        },
      ],
      source_summaries: [
        { source: "demo", source_type: "demo", item_count: 1, last_imported_at: now },
      ],
      created_at: now,
      updated_at: now,
    },
    message: "Modo Demo: perfil ficticio.",
  };
}

function mockSavedProfile(payload: Partial<ProfileResult["profile"]>): ProfileResult {
  const base = mockProfileResult();
  return {
    profile: normalizeProfile({
      ...base.profile,
      ...payload,
      updated_at: new Date().toISOString(),
    }),
    message: "Perfil atualizado no modo Demo.",
  };
}

function mockProfileImport(text: string, sourceType: string, useAi: boolean): ProfileImportResult {
  const now = new Date().toISOString();
  const lower = text.toLowerCase();
  const domain = lower.includes("coren")
    ? "Saude"
    : lower.includes("oab")
      ? "Direito"
      : lower.includes("portfolio")
        ? "Artes e Design"
        : "Geral";
  return {
    items: [
      normalizeProfileItem({
        item_id: "profile-import-demo",
        type:
          lower.includes("coren") || lower.includes("oab") ? "professional_registry" : "project",
        title: lower.includes("coren") ? "COREN" : lower.includes("oab") ? "OAB" : "Item importado",
        description: text.slice(0, 220),
        area: domain,
        domain,
        source: sourceType,
        evidence: text.slice(0, 220),
        confidence: "medium",
        confirmed_by_user: false,
        created_at: now,
        updated_at: now,
      }),
    ],
    detected_domains: [domain],
    career_moments: lower.includes("estagio") ? ["estagio"] : [],
    warnings: [
      useAi
        ? "Modo Demo: IA simulada; revise antes de adicionar."
        : "Modo Demo: extração local simulada.",
    ],
    questions_to_confirm: ["Esse item deve entrar como fato confirmado no perfil?"],
    provider_used: useAi ? "gemini-demo" : "local",
    requested_provider: useAi ? "gemini" : "local",
    analysis_mode: useAi ? "ai" : "local",
    needs_user_review: true,
  };
}

function normalizeProfileResult(value: unknown): ProfileResult {
  const raw = asRecord(value);
  return {
    profile: normalizeProfile(raw.profile),
    message: asString(raw.message),
  };
}

function normalizeProfileItemResult(value: unknown): ProfileItemResult {
  const raw = asRecord(value);
  return {
    item: normalizeProfileItem(raw.item),
    message: asString(raw.message),
  };
}

function normalizeProfileImportResult(value: unknown): ProfileImportResult {
  const raw = asRecord(value);
  return {
    items: objectList(raw.items).map(normalizeProfileItem),
    detected_domains: stringList(raw.detected_domains),
    career_moments: stringList(raw.career_moments),
    warnings: stringList(raw.warnings),
    questions_to_confirm: stringList(raw.questions_to_confirm),
    provider_used: asString(raw.provider_used) || "local",
    requested_provider: asString(raw.requested_provider) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    needs_user_review: asBoolean(raw.needs_user_review, true),
  };
}

function normalizeProfileDeduplicateResult(value: unknown): ProfileDeduplicateResult {
  const raw = asRecord(value);
  return {
    suggestions: objectList(raw.suggestions).map((item) => {
      const suggestion = asRecord(item);
      return {
        suggestion_id: asString(suggestion.suggestion_id),
        item_ids: stringList(suggestion.item_ids),
        reason: asString(suggestion.reason),
        confidence: normalizeProfileConfidence(suggestion.confidence),
        proposed_title: asString(suggestion.proposed_title),
        proposed_description: asString(suggestion.proposed_description),
        sources: stringList(suggestion.sources),
      };
    }),
    message: asString(raw.message),
  };
}

function normalizeProfile(value: unknown): ProfileResult["profile"] {
  const raw = asRecord(value);
  const now = new Date().toISOString();
  return {
    profile_id: asString(raw.profile_id) || "default",
    display_name: asString(raw.display_name),
    headline: asString(raw.headline),
    summary: asString(raw.summary),
    primary_domains: stringList(raw.primary_domains),
    secondary_domains: stringList(raw.secondary_domains),
    career_moments: stringList(raw.career_moments),
    target_roles: stringList(raw.target_roles),
    target_seniority: stringList(raw.target_seniority),
    preferred_locations: stringList(raw.preferred_locations),
    preferred_work_models: stringList(raw.preferred_work_models),
    preferred_contract_types: stringList(raw.preferred_contract_types),
    constraints: objectList(raw.constraints).map(normalizeProfileItem),
    items: objectList(raw.items).map(normalizeProfileItem),
    source_summaries: objectList(raw.source_summaries).map((item) => {
      const summary = asRecord(item);
      return {
        source: asString(summary.source),
        source_type: asString(summary.source_type),
        item_count: asNumber(summary.item_count, 0),
        last_imported_at: asString(summary.last_imported_at),
      };
    }),
    created_at: asString(raw.created_at) || now,
    updated_at: asString(raw.updated_at) || now,
  };
}

function normalizeProfileItem(value: unknown): ProfileItem {
  const raw = asRecord(value);
  const now = new Date().toISOString();
  return {
    item_id: asString(raw.item_id) || `profile-item-${Math.random().toString(16).slice(2)}`,
    type: asString(raw.type) || "other",
    title: asString(raw.title) || "Item de perfil",
    description: asString(raw.description),
    area: asString(raw.area),
    domain: asString(raw.domain),
    institution: asString(raw.institution),
    organization: asString(raw.organization),
    status: asString(raw.status),
    start_date: asString(raw.start_date),
    end_date: asString(raw.end_date),
    tags: stringList(raw.tags),
    skills: stringList(raw.skills),
    evidence: asString(raw.evidence),
    source: asString(raw.source) || "manual",
    source_ref: asString(raw.source_ref),
    confidence: normalizeProfileConfidence(raw.confidence),
    confirmed_by_user: asBoolean(raw.confirmed_by_user, false),
    sensitive: asBoolean(raw.sensitive, false),
    created_at: asString(raw.created_at) || now,
    updated_at: asString(raw.updated_at) || now,
  };
}

function normalizeProfileConfidence(value: unknown): ProfileItem["confidence"] {
  return value === "low" || value === "medium" || value === "high" ? value : "medium";
}

function normalizeHealth(value: unknown): Health {
  const raw = asRecord(value);
  return {
    status: asString(raw.status) || "ok",
    service: asString(raw.service),
    version: asString(raw.version) || "1.8.1",
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
    allow_resume: asBoolean(raw.allow_resume, true),
    allow_job: asBoolean(raw.allow_job, true),
    allow_match: asBoolean(raw.allow_match, true),
    allow_ats: asBoolean(raw.allow_ats, true),
    allow_tailor: asBoolean(raw.allow_tailor, true),
    allow_github: asBoolean(raw.allow_github, true),
    allow_source_import: asBoolean(raw.allow_source_import, true),
    allow_radar: asBoolean(raw.allow_radar, true),
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
    allow_resume: payload.allow_resume,
    allow_job: payload.allow_job,
    allow_match: payload.allow_match,
    allow_ats: payload.allow_ats,
    allow_tailor: payload.allow_tailor,
    allow_github: payload.allow_github,
    allow_source_import: payload.allow_source_import,
    allow_radar: payload.allow_radar,
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

function normalizeExtensionPatchCapture(value: unknown): ExtensionCapturePatchResult {
  const raw = asRecord(value);
  const captures = normalizeExtensionCaptures({ captures: [raw.capture] }).captures;
  return {
    capture: captures[0] ?? {
      id: "",
      title: "",
      url: "",
      status: "reviewed",
    },
    message: asString(raw.message),
  };
}

function normalizeSourceImports(value: unknown): SourceImportsResult {
  const raw = asRecord(value);
  return {
    items: objectList(raw.items).map(normalizeInboxItem),
    batches: objectList(raw.batches).map(normalizeImportBatch),
  };
}

function normalizeSourceImport(value: unknown): SourceImportResult {
  const raw = asRecord(value);
  return {
    batch: normalizeImportBatch(raw.batch),
    items: objectList(raw.items).map(normalizeInboxItem),
    message: asString(raw.message),
  };
}

function normalizeSourceCaptureResult(value: unknown): SourceCaptureResult {
  const raw = asRecord(value);
  return {
    capture: normalizeInboxItem(raw.capture),
    message: asString(raw.message),
  };
}

function normalizeSourceCaptureImportJob(value: unknown): SourceCaptureImportJobResult {
  const raw = asRecord(value);
  return {
    capture: normalizeInboxItem(raw.capture),
    job: normalizeJobPosting(raw.job),
    message: asString(raw.message),
  };
}

function normalizeSourceCaptureSaveTracker(value: unknown): SourceCaptureSaveTrackerResult {
  const raw = asRecord(value);
  return {
    capture: normalizeInboxItem(raw.capture),
    tracker_id: asString(raw.tracker_id),
    message: asString(raw.message),
  };
}

function normalizeSourceDedupe(value: unknown): SourceDedupeResult {
  const raw = asRecord(value);
  return {
    duplicates: objectList(raw.duplicates).map((item) => ({
      item_id: asString(item.item_id),
      duplicate_of: asString(item.duplicate_of),
      decision:
        item.decision === "confirmed_duplicate" || item.decision === "not_duplicate"
          ? item.decision
          : "possible_duplicate",
      reason: asString(item.reason),
      confidence: asNumber(item.confidence, 0),
    })),
  };
}

function normalizeSourceDirectory(value: unknown): SourceDirectoryResult {
  const raw = asRecord(value);
  return {
    sources: objectList(raw.sources).map((source) => {
      const item = asRecord(source);
      const kind = asString(item.kind);
      const status = asString(item.status);
      return {
        id: asString(item.id),
        name: asString(item.name),
        kind:
          kind === "public_feed" ||
          kind === "official_api" ||
          kind === "recurring_csv_json" ||
          kind === "manual_link" ||
          kind === "observed_origin"
            ? kind
            : "public_career_page",
        status:
          status === "available" ||
          status === "future" ||
          status === "manual_review" ||
          status === "planned"
            ? status
            : "planned",
        base_url: asString(item.base_url),
        last_checked_at: asString(item.last_checked_at),
        observation: asString(item.observation),
        requires_manual_review: asBoolean(item.requires_manual_review, true),
      };
    }),
    query: asString(raw.query),
    warnings: stringList(raw.warnings),
  };
}

function normalizeSourceExport(value: unknown): SourceExportResult {
  const raw = asRecord(value);
  return {
    format: raw.format === "json" ? "json" : "csv",
    filename: asString(raw.filename),
    content: asString(raw.content),
    item_count: asNumber(raw.item_count, 0),
  };
}

function normalizeSourceStats(value: unknown): SourceStats {
  const raw = asRecord(value);
  return {
    total: asNumber(raw.total, 0),
    duplicates: asNumber(raw.duplicates, 0),
    errors: asNumber(raw.errors, 0),
    saved_to_tracker: asNumber(raw.saved_to_tracker, 0),
    by_status: numberRecord(raw.by_status),
    by_origin: numberRecord(raw.by_origin),
  };
}

function normalizeRadarWishlists(value: unknown): RadarWishlistsResult {
  return { wishlists: objectList(asRecord(value).wishlists).map(normalizeRadarWishlist) };
}

function normalizeRadarWishlistResult(value: unknown): RadarWishlistResult {
  const raw = asRecord(value);
  return { wishlist: normalizeRadarWishlist(raw.wishlist), message: asString(raw.message) };
}

function normalizeWishlistDraft(value: unknown): WishlistDraftResult {
  const raw = asRecord(value);
  const wishlist = normalizeWishlistDraftPayload(raw.wishlist);
  return {
    wishlist,
    confidence: asNumber(raw.confidence, 0),
    detected_domains: stringList(raw.detected_domains),
    detected_career_moments: stringList(raw.detected_career_moments),
    assumptions: stringList(raw.assumptions),
    questions_to_confirm: stringList(raw.questions_to_confirm),
    warnings: stringList(raw.warnings),
    needs_user_review: asBoolean(raw.needs_user_review, true),
    provider_used: asString(raw.provider_used) || "local",
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
  };
}

function normalizeWishlistDraftPayload(value: unknown): WishlistDraftResult["wishlist"] {
  const raw = asRecord(value);
  return {
    name: asString(raw.name) || "Wishlist sugerida",
    target_titles: stringList(raw.target_titles),
    target_domains: stringList(raw.target_domains),
    target_seniority: stringList(raw.target_seniority),
    required_skills: stringList(raw.required_skills),
    desired_skills: stringList(raw.desired_skills),
    excluded_terms: stringList(raw.excluded_terms),
    locations: stringList(raw.locations),
    remote_preferences: stringList(raw.remote_preferences),
    work_model: asString(raw.work_model),
    employment_type: asString(raw.employment_type),
    salary_min: definedNumber(raw.salary_min),
    salary_currency: asString(raw.salary_currency) || "BRL",
    contract_types: stringList(raw.contract_types),
    industries: stringList(raw.industries),
    companies_include: stringList(raw.companies_include),
    companies_exclude: stringList(raw.companies_exclude),
    source_types: stringList(raw.source_types),
    min_match_score: asNumber(raw.min_match_score, 70),
    min_ats_score: asNumber(raw.min_ats_score, 60),
    notify_on_new_matches: asBoolean(raw.notify_on_new_matches, true),
    is_active: asBoolean(raw.is_active, true),
    notes: asString(raw.notes),
  };
}

function normalizeRadarWishlist(value: unknown): JobWishlist {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    name: asString(raw.name) || "Wishlist",
    target_titles: stringList(raw.target_titles),
    target_domains: stringList(raw.target_domains),
    target_seniority: stringList(raw.target_seniority),
    required_skills: stringList(raw.required_skills),
    desired_skills: stringList(raw.desired_skills),
    excluded_terms: stringList(raw.excluded_terms),
    locations: stringList(raw.locations),
    remote_preferences: stringList(raw.remote_preferences),
    work_model: asString(raw.work_model),
    employment_type: asString(raw.employment_type),
    salary_min: definedNumber(raw.salary_min),
    salary_currency: asString(raw.salary_currency) || "BRL",
    contract_types: stringList(raw.contract_types),
    industries: stringList(raw.industries),
    companies_include: stringList(raw.companies_include),
    companies_exclude: stringList(raw.companies_exclude),
    source_types: stringList(raw.source_types),
    min_match_score: asNumber(raw.min_match_score, 70),
    min_ats_score: asNumber(raw.min_ats_score, 0),
    notify_on_new_matches: asBoolean(raw.notify_on_new_matches, true),
    notes: asString(raw.notes),
    created_at: asString(raw.created_at),
    updated_at: asString(raw.updated_at),
    is_active: asBoolean(raw.is_active, true),
  };
}

function normalizeRadarSources(value: unknown): RadarSourcesResult {
  const raw = asRecord(value);
  return {
    sources: objectList(raw.sources).map(normalizeRadarSource),
    adapters: objectList(raw.adapters).map((item) => ({
      source_type: normalizeRadarSourceType(item.source_type),
      adapter_name: asString(item.adapter_name),
      supported: asBoolean(item.supported, true),
      notes: asString(item.notes),
    })),
  };
}

function normalizeRadarSourceResult(value: unknown): RadarSourceResult {
  const raw = asRecord(value);
  return { source: normalizeRadarSource(raw.source), message: asString(raw.message) };
}

function normalizeRadarSource(value: unknown): RadarSource {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    name: asString(raw.name) || "Fonte",
    source_type: normalizeRadarSourceType(raw.source_type),
    url: asString(raw.url),
    docs_url: asString(raw.docs_url),
    status: normalizeRadarSourceStatus(raw.status),
    is_active: asBoolean(raw.is_active, true),
    requires_api_key: asBoolean(raw.requires_api_key, false),
    api_key_configured: asBoolean(raw.api_key_configured, false),
    max_results: asNumber(raw.max_results, 20),
    timeout_seconds: asNumber(raw.timeout_seconds, 6),
    rate_limit_seconds: asNumber(raw.rate_limit_seconds, 1),
    last_checked_at: asString(raw.last_checked_at),
    last_error: asString(raw.last_error),
    notes: asString(raw.notes),
    metadata: asRecord(raw.metadata),
    created_at: asString(raw.created_at),
    updated_at: asString(raw.updated_at),
  };
}

function normalizeRadarRunResult(value: unknown): RadarRunResult {
  const raw = asRecord(value);
  return {
    run: normalizeRadarRun(raw.run),
    results: objectList(raw.results).map(normalizeRadarResult),
    alerts: objectList(raw.alerts).map(normalizeRadarAlert),
    message: asString(raw.message),
  };
}

function normalizeRadarRuns(value: unknown): RadarRunsResult {
  return { runs: objectList(asRecord(value).runs).map(normalizeRadarRun) };
}

function normalizeRadarRun(value: unknown): RadarRun {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    started_at: asString(raw.started_at),
    finished_at: asString(raw.finished_at),
    source_ids: stringList(raw.source_ids),
    wishlist_id: asString(raw.wishlist_id),
    resume_used: asBoolean(raw.resume_used, false),
    total_sources: asNumber(raw.total_sources, 0),
    total_found: asNumber(raw.total_found, 0),
    total_deduped: asNumber(raw.total_deduped, 0),
    total_alerted: asNumber(raw.total_alerted, 0),
    total_errors: asNumber(raw.total_errors, 0),
    duration_ms: asNumber(raw.duration_ms, 0),
    warnings: stringList(raw.warnings),
    errors: stringList(raw.errors),
    metadata: asRecord(raw.metadata),
  };
}

function normalizeRadarResults(value: unknown): RadarResultsResult {
  return { results: objectList(asRecord(value).results).map(normalizeRadarResult) };
}

function normalizeRadarResultEnvelope(value: unknown): RadarResultEnvelope {
  const raw = asRecord(value);
  return { result: normalizeRadarResult(raw.result), message: asString(raw.message) };
}

function normalizeRadarSaveInbox(value: unknown): RadarSaveInboxResult {
  const raw = asRecord(value);
  return {
    result: normalizeRadarResult(raw.result),
    inbox_item: normalizeInboxItem(raw.inbox_item),
    message: asString(raw.message),
  };
}

function normalizeRadarSaveTracker(value: unknown): RadarSaveTrackerResult {
  const raw = asRecord(value);
  return {
    result: normalizeRadarResult(raw.result),
    tracker_id: asString(raw.tracker_id),
    message: asString(raw.message),
  };
}

function normalizeRadarResult(value: unknown): RadarResult {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    run_id: asString(raw.run_id),
    source_id: asString(raw.source_id),
    source_name: asString(raw.source_name),
    source_type: normalizeRadarSourceType(raw.source_type),
    wishlist_id: asString(raw.wishlist_id),
    title: asString(raw.title) || "Vaga sem titulo",
    company: asString(raw.company),
    url: asString(raw.url),
    location: asString(raw.location),
    work_model: asString(raw.work_model),
    employment_type: asString(raw.employment_type),
    description: asString(raw.description),
    published_at: asString(raw.published_at),
    captured_at: asString(raw.captured_at),
    normalized_text: asString(raw.normalized_text),
    dedupe_key: asString(raw.dedupe_key),
    duplicate_of: asString(raw.duplicate_of),
    match_score: asNumber(raw.match_score, 0),
    ats_score: asNumber(raw.ats_score, 0),
    wishlist_score: asNumber(raw.wishlist_score, 0),
    radar_score: asNumber(raw.radar_score, 0),
    radar_status: normalizeRadarResultStatus(raw.radar_status),
    already_in_inbox: asBoolean(raw.already_in_inbox, false),
    already_in_tracker: asBoolean(raw.already_in_tracker, false),
    warnings: stringList(raw.warnings),
    reasons: stringList(raw.reasons),
    evidence: stringList(raw.evidence),
    gaps: stringList(raw.gaps),
    next_actions: stringList(raw.next_actions),
    analysis_mode: normalizeAnalysisMode(raw.analysis_mode),
    provider_used: asString(raw.provider_used) || "local",
    metadata: asRecord(raw.metadata),
  };
}

function normalizeRadarAlerts(value: unknown): RadarAlertsResult {
  return { alerts: objectList(asRecord(value).alerts).map(normalizeRadarAlert) };
}

function normalizeRadarAlertResult(value: unknown): RadarAlertResult {
  const raw = asRecord(value);
  return { alert: normalizeRadarAlert(raw.alert), message: asString(raw.message) };
}

function normalizeRadarAlert(value: unknown): RadarAlert {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    run_id: asString(raw.run_id),
    result_id: asString(raw.result_id),
    wishlist_id: asString(raw.wishlist_id),
    title: asString(raw.title),
    message: asString(raw.message),
    score: asNumber(raw.score, 0),
    status: normalizeRadarAlertStatus(raw.status),
    created_at: asString(raw.created_at),
    read_at: asString(raw.read_at),
    metadata: asRecord(raw.metadata),
  };
}

function normalizeRadarStats(value: unknown): RadarStats {
  const raw = asRecord(value);
  return {
    active_sources: asNumber(raw.active_sources, 0),
    total_sources: asNumber(raw.total_sources, 0),
    total_results: asNumber(raw.total_results, 0),
    new_results: asNumber(raw.new_results, 0),
    matched_results: asNumber(raw.matched_results, 0),
    unread_alerts: asNumber(raw.unread_alerts, 0),
    duplicates: asNumber(raw.duplicates, 0),
    source_errors: asNumber(raw.source_errors, 0),
    last_run_at: asString(raw.last_run_at),
  };
}

function normalizeRadarSourceType(value: unknown): RadarSource["source_type"] {
  const allowed: RadarSource["source_type"][] = [
    "public_feed",
    "official_api",
    "manual_public_page",
    "manual_url",
    "recurring_csv_json",
  ];
  return allowed.includes(value as RadarSource["source_type"])
    ? (value as RadarSource["source_type"])
    : "public_feed";
}

function normalizeRadarSourceStatus(value: unknown): RadarSource["status"] {
  const allowed: RadarSource["status"][] = [
    "available",
    "experimental",
    "requires_official_api",
    "requires_user_key",
    "planned",
    "disabled",
    "error",
  ];
  return allowed.includes(value as RadarSource["status"])
    ? (value as RadarSource["status"])
    : "planned";
}

function normalizeRadarResultStatus(value: unknown): RadarResult["radar_status"] {
  const allowed: RadarResult["radar_status"][] = [
    "new",
    "matched",
    "ignored",
    "saved_to_inbox",
    "saved_to_tracker",
    "duplicate",
    "error",
    "archived",
  ];
  return allowed.includes(value as RadarResult["radar_status"])
    ? (value as RadarResult["radar_status"])
    : "new";
}

function normalizeRadarAlertStatus(value: unknown): RadarAlert["status"] {
  const allowed: RadarAlert["status"][] = ["unread", "read", "ignored", "saved"];
  return allowed.includes(value as RadarAlert["status"])
    ? (value as RadarAlert["status"])
    : "unread";
}

function normalizeInboxItem(value: unknown): SourceImportsResult["items"][number] {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    title: asString(raw.title) || "Vaga sem titulo",
    company: asString(raw.company),
    source_type: normalizeSourceOrigin(raw.source_type),
    source_name: asString(raw.source_name),
    source_url: asString(raw.source_url),
    origin: normalizeSourceOrigin(raw.origin),
    captured_at: asString(raw.captured_at),
    imported_at: asString(raw.imported_at),
    status: normalizeCaptureStatus(raw.status),
    raw_text: asString(raw.raw_text),
    job_url: asString(raw.job_url),
    location: asString(raw.location),
    work_model: asString(raw.work_model),
    employment_type: asString(raw.employment_type),
    seniority: asString(raw.seniority),
    domain: asString(raw.domain),
    tags: stringList(raw.tags),
    source_confidence: asNumber(raw.source_confidence, 0),
    dedupe_key: asString(raw.dedupe_key),
    duplicate_of: asString(raw.duplicate_of),
    match_score: definedNumber(raw.match_score),
    ats_score: definedNumber(raw.ats_score),
    last_analysis_at: asString(raw.last_analysis_at),
    notes: asString(raw.notes),
    metadata: asRecord(raw.metadata),
  };
}

function normalizeImportBatch(value: unknown): ImportBatch {
  const raw = asRecord(value);
  return {
    id: asString(raw.id),
    origin: normalizeSourceOrigin(raw.origin),
    source_name: asString(raw.source_name),
    source_url: asString(raw.source_url),
    created_at: asString(raw.created_at),
    total: asNumber(raw.total, 0),
    imported: asNumber(raw.imported, 0),
    errors: asNumber(raw.errors, 0),
    duplicates: asNumber(raw.duplicates, 0),
    warnings: stringList(raw.warnings),
    item_ids: stringList(raw.item_ids),
  };
}

function normalizeSourceOrigin(value: unknown): SourceImportsResult["items"][number]["origin"] {
  const allowed: SourceImportsResult["items"][number]["origin"][] = [
    "manual_text",
    "manual_url",
    "csv_import",
    "json_import",
    "extension_capture",
    "companion_capture",
    "authenticated_assisted_capture",
    "public_source",
    "public_feed",
    "official_api_future",
  ];
  return allowed.includes(value as SourceImportsResult["items"][number]["origin"])
    ? (value as SourceImportsResult["items"][number]["origin"])
    : "manual_text";
}

function normalizeCaptureStatus(value: unknown): SourceImportsResult["items"][number]["status"] {
  const allowed: SourceImportsResult["items"][number]["status"][] = [
    "new",
    "reviewed",
    "imported_to_job",
    "saved_to_tracker",
    "ignored",
    "archived",
    "duplicate",
    "error",
  ];
  return allowed.includes(value as SourceImportsResult["items"][number]["status"])
    ? (value as SourceImportsResult["items"][number]["status"])
    : "new";
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
