// SotuHire API DTOs for the v1 web frontend contract.

export interface ApiEnvelope<T> {
  ok: boolean;
  data?: T;
  warnings?: string[];
  request_id?: string;
  error?: { code: string; message: string; details?: Record<string, unknown> };
}

export interface Health {
  status: string;
  service?: string;
  version: string;
  local_first: boolean;
  environment?: string;
  capabilities: string[];
}

export type AnalysisMode = "local" | "ai" | "fallback";

export interface AnalysisMeta {
  provider_used?: string;
  requested_provider?: string;
  analysis_mode?: AnalysisMode;
  fallback_used?: boolean;
  model?: string;
}

export type AiProvider = "local" | "gemini" | "openai_future";
export type AiSettingsStatus = "ready" | "configured" | "not_configured" | "planned" | "error";

export interface AiSettings {
  provider: AiProvider;
  model: string;
  configured: boolean;
  status: AiSettingsStatus;
  use_ai: boolean;
  allow_match: boolean;
  allow_ats: boolean;
  allow_tailor: boolean;
  allow_github: boolean;
  allow_memory_context: boolean;
  updated_at?: string;
  warnings?: string[];
}

export interface AiSettingsPayload {
  provider: AiProvider;
  model: string;
  api_key?: string;
  use_ai: boolean;
  allow_match: boolean;
  allow_ats: boolean;
  allow_tailor: boolean;
  allow_github: boolean;
  allow_memory_context: boolean;
}

export interface AiSettingsTestPayload {
  provider?: AiProvider;
  model?: string;
  api_key?: string;
}

export interface AiSettingsTestResult {
  provider: AiProvider;
  model: string;
  success: boolean;
  configured: boolean;
  status: AiSettingsStatus;
  message: string;
}

export type AiUiState =
  | "disabled"
  | "provider_local"
  | "configured"
  | "unconfigured"
  | "analyzing"
  | "fallback"
  | "provider_error"
  | "provider_timeout"
  | "invalid_key";

export interface ResumeProfile {
  id?: string;
  name: string;
  headline?: string;
  email?: string;
  location?: string;
  seniority?: string;
  summary?: string;
  skills: string[];
  experience?: Array<{ role: string; company: string; period: string; highlights?: string[] }>;
  education?: Array<{ name: string; institution: string; status?: string }>;
  projects?: Array<{ name: string; description?: string; links?: string[] }>;
}

export interface ResumeExtractResult extends AnalysisMeta {
  profile: ResumeProfile;
  confidence: number;
  low_confidence_fields?: string[];
}

export interface JobPosting {
  id?: string;
  title: string;
  company?: string;
  source?: string;
  modality?: string;
  seniority?: string;
  domain?: string;
  required_skills: string[];
  preferred_skills?: string[];
  desired_skills?: string[];
  ats_keywords?: string[];
  responsibilities?: string[];
}

export interface JobExtractResult extends AnalysisMeta {
  job: JobPosting;
  confidence: number;
  low_confidence_fields?: string[];
}

export interface MatchRequirement {
  name: string;
  category?: string;
  evidence?: string[];
  reason?: string;
}

export interface MatchAnalysis {
  analysis_version?: string;
  match_score: number;
  confidence_score: number;
  evidence_score: number;
  ats_score: number;
  opportunity_fit_score: number;
  risk_score: number;
  domain?: string;
  recommendation?: string;
  matched_requirements: MatchRequirement[];
  partial_requirements: MatchRequirement[];
  missing_requirements: MatchRequirement[];
  critical_gaps: MatchRequirement[];
  transferable_skills?: string[];
  safe_actions: string[];
}

export interface MatchAnalyzeResult extends AnalysisMeta {
  local_first: boolean;
  memory_shared_with_provider?: boolean;
  analysis: MatchAnalysis;
}

export interface AtsReview extends AnalysisMeta {
  ats_score: number;
  present: string[];
  missing_but_safe_to_add_if_true: string[];
  missing_without_evidence: string[];
  warnings?: string[];
  ai_insights?: string[];
}

export interface ResumeTailor {
  safe_keywords: string[];
  suggested_bullets: string[];
  conditional_suggestions: Array<{ keyword: string; text: string }>;
  warnings: string[];
  evidence_used?: string[];
}

export interface ResumeTailorResult extends AnalysisMeta {
  safe_to_export: boolean;
  tailor: ResumeTailor;
  ai_suggestions?: string[];
}

export interface GithubReport {
  repo: { owner: string; name: string; url: string; visibility?: string };
  quality_score: number;
  evidence_score: number;
  languages: Array<{ name: string; percent: number }>;
  positive_signals: string[];
  risks: string[];
  portfolio_suggestions: string[];
}

export interface GithubAnalyzeResult extends AnalysisMeta {
  report: GithubReport;
}

export type TrackerStatus =
  | "found"
  | "analyzed"
  | "good_fit"
  | "applied"
  | "message_sent"
  | "follow_up"
  | "interview"
  | "technical_test"
  | "rejected"
  | "offer"
  | "archived";

export interface TrackerJob {
  id: string;
  title: string;
  company: string;
  source?: string;
  status: TrackerStatus;
  match_score?: number;
  ats_score?: number;
  created_at?: string;
  updated_at?: string;
  notes?: string;
  requirements?: string[];
}

export interface TrackerMetrics {
  total_saved: number;
  total_applied: number;
  by_status: Record<string, number>;
  average_match_by_status: Record<string, number>;
  average_ats?: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
  weekly_applications?: Array<{ week: string; count: number }>;
}

export interface TrackerFunnel {
  stages: Array<{ status: string; label: string; count: number }>;
  conversion_rates: Array<{ from: string; to: string; rate: number }>;
}

export interface TrackerRequirements {
  top_requirements: Array<{
    name: string;
    count: number;
    status_scope?: string;
    sources?: string[];
    candidate_has_evidence?: boolean;
  }>;
  critical_gaps?: Array<{ name: string; count: number; severity: string; safe_action: string }>;
  requirements_by_source?: Array<{ source: string; requirement: string; count: number }>;
  trend_over_time?: Array<{ month: string; requirement: string; count: number }>;
}

export interface TrackerSources {
  sources: Array<{
    name: string;
    saved: number;
    applied: number;
    interviews: number;
    average_match: number;
    top_requirements: string[];
  }>;
}

export interface AuthenticatedBrowserStatus {
  available: boolean;
  endpoint: string;
  browser?: string;
  message?: string;
}

export interface AuthenticatedBrowserCollectResult {
  new_count: number;
  duplicate_count: number;
  updated_count: number;
  failures: string[];
  opportunities: Array<{
    title: string;
    company?: string;
    source_url?: string;
    confidence: number;
  }>;
}

export interface ExtensionStatus {
  available: boolean;
  companion_url: string;
  capture_count: number;
  last_capture_at?: string;
  message?: string;
}

export interface ExtensionCapture {
  id: string;
  title: string;
  company?: string;
  url: string;
  domain?: string;
  kind?: string;
  source?: string;
  status: string;
  tracker_id?: string;
  captured_at?: string;
  updated_at?: string;
}

export interface ExtensionCapturesResult {
  captures: ExtensionCapture[];
}

export interface ExtensionImportJobResult {
  capture_id: string;
  job: JobPosting;
  message: string;
}

export interface ExtensionImportTrackerResult {
  capture_id: string;
  tracker_id?: string;
  message: string;
  provider: string;
}

export interface ExtensionImportGithubResult {
  capture_id: string;
  report?: GithubReport;
  message: string;
}

export interface ExtensionCapturePatchResult {
  capture: ExtensionCapture;
  message: string;
}

export type SourceOrigin =
  | "manual_text"
  | "manual_url"
  | "csv_import"
  | "json_import"
  | "extension_capture"
  | "companion_capture"
  | "public_source"
  | "public_feed"
  | "official_api_future";

export type SourceCaptureStatus =
  | "new"
  | "reviewed"
  | "imported_to_job"
  | "saved_to_tracker"
  | "ignored"
  | "archived"
  | "duplicate"
  | "error";

export interface OpportunityInboxItem {
  id: string;
  title: string;
  company?: string;
  source_type: SourceOrigin;
  source_name?: string;
  source_url?: string;
  origin: SourceOrigin;
  captured_at?: string;
  imported_at?: string;
  status: SourceCaptureStatus;
  raw_text?: string;
  job_url?: string;
  location?: string;
  work_model?: string;
  employment_type?: string;
  seniority?: string;
  domain?: string;
  tags: string[];
  source_confidence: number;
  dedupe_key?: string;
  duplicate_of?: string;
  match_score?: number;
  ats_score?: number;
  last_analysis_at?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface ImportBatch {
  id: string;
  origin: SourceOrigin;
  source_name?: string;
  source_url?: string;
  created_at?: string;
  total: number;
  imported: number;
  errors: number;
  duplicates: number;
  warnings: string[];
  item_ids: string[];
}

export interface DuplicateCandidate {
  item_id: string;
  duplicate_of: string;
  decision: "possible_duplicate" | "confirmed_duplicate" | "not_duplicate";
  reason: string;
  confidence: number;
}

export interface SourceImportsResult {
  items: OpportunityInboxItem[];
  batches: ImportBatch[];
}

export interface SourceImportResult {
  batch: ImportBatch;
  items: OpportunityInboxItem[];
  message: string;
}

export interface SourceCapturesResult {
  captures: OpportunityInboxItem[];
}

export interface SourceCaptureResult {
  capture: OpportunityInboxItem;
  message: string;
}

export interface SourceCaptureImportJobResult {
  capture: OpportunityInboxItem;
  job: JobPosting;
  message: string;
}

export interface SourceCaptureSaveTrackerResult {
  capture: OpportunityInboxItem;
  tracker_id: string;
  message: string;
}

export interface SourceDedupeResult {
  duplicates: DuplicateCandidate[];
}

export interface SourceStats {
  total: number;
  duplicates: number;
  errors: number;
  saved_to_tracker: number;
  by_status: Record<string, number>;
  by_origin: Record<string, number>;
}

export interface SourceDirectoryEntry {
  id: string;
  name: string;
  kind:
    | "public_career_page"
    | "public_feed"
    | "official_api"
    | "recurring_csv_json"
    | "manual_link"
    | "observed_origin";
  status: "available" | "planned" | "future" | "manual_review";
  base_url?: string;
  last_checked_at?: string;
  observation?: string;
  requires_manual_review: boolean;
}

export interface SourceDirectoryResult {
  sources: SourceDirectoryEntry[];
  query: string;
  warnings: string[];
}

export interface SourceExportResult {
  format: "csv" | "json";
  filename: string;
  content: string;
  item_count: number;
}

export type RadarSourceType =
  | "public_feed"
  | "official_api"
  | "manual_public_page"
  | "manual_url"
  | "recurring_csv_json";

export type RadarSourceStatus =
  | "available"
  | "experimental"
  | "requires_official_api"
  | "requires_user_key"
  | "planned"
  | "disabled"
  | "error";

export type RadarResultStatus =
  | "new"
  | "matched"
  | "ignored"
  | "saved_to_inbox"
  | "saved_to_tracker"
  | "duplicate"
  | "error"
  | "archived";

export type RadarAlertStatus = "unread" | "read" | "ignored" | "saved";

export interface JobWishlist {
  id: string;
  name: string;
  target_titles: string[];
  target_domains: string[];
  target_seniority: string[];
  required_skills: string[];
  desired_skills: string[];
  excluded_terms: string[];
  locations: string[];
  remote_preferences: string[];
  work_model?: string;
  employment_type?: string;
  salary_min?: number;
  salary_currency?: string;
  contract_types: string[];
  industries: string[];
  companies_include: string[];
  companies_exclude: string[];
  source_types: string[];
  min_match_score: number;
  min_ats_score: number;
  notify_on_new_matches: boolean;
  created_at?: string;
  updated_at?: string;
  is_active: boolean;
}

export interface RadarSource {
  id: string;
  name: string;
  source_type: RadarSourceType;
  url?: string;
  docs_url?: string;
  status: RadarSourceStatus;
  is_active: boolean;
  requires_api_key: boolean;
  api_key_configured: boolean;
  max_results: number;
  timeout_seconds: number;
  rate_limit_seconds: number;
  last_checked_at?: string;
  last_error?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface SourceAdapter {
  source_type: RadarSourceType;
  adapter_name: string;
  supported: boolean;
  notes?: string;
}

export interface RadarRun {
  id: string;
  started_at?: string;
  finished_at?: string;
  source_ids: string[];
  wishlist_id?: string;
  resume_used: boolean;
  total_sources: number;
  total_found: number;
  total_deduped: number;
  total_alerted: number;
  total_errors: number;
  duration_ms: number;
  warnings: string[];
  errors: string[];
  metadata?: Record<string, unknown>;
}

export interface RadarResult {
  id: string;
  run_id?: string;
  source_id?: string;
  source_name?: string;
  source_type: RadarSourceType;
  wishlist_id?: string;
  title: string;
  company?: string;
  url?: string;
  location?: string;
  work_model?: string;
  employment_type?: string;
  description?: string;
  published_at?: string;
  captured_at?: string;
  normalized_text?: string;
  dedupe_key?: string;
  duplicate_of?: string;
  match_score: number;
  ats_score: number;
  wishlist_score: number;
  radar_score: number;
  radar_status: RadarResultStatus;
  already_in_inbox: boolean;
  already_in_tracker: boolean;
  warnings: string[];
  reasons: string[];
  evidence: string[];
  gaps: string[];
  next_actions: string[];
  analysis_mode: AnalysisMode;
  provider_used?: string;
  metadata?: Record<string, unknown>;
}

export interface RadarAlert {
  id: string;
  run_id?: string;
  result_id?: string;
  wishlist_id?: string;
  title: string;
  message: string;
  score: number;
  status: RadarAlertStatus;
  created_at?: string;
  read_at?: string;
  metadata?: Record<string, unknown>;
}

export interface RadarStats {
  active_sources: number;
  total_sources: number;
  total_results: number;
  new_results: number;
  matched_results: number;
  unread_alerts: number;
  duplicates: number;
  source_errors: number;
  last_run_at?: string;
}

export interface RadarWishlistsResult {
  wishlists: JobWishlist[];
}

export interface RadarWishlistResult {
  wishlist: JobWishlist;
  message: string;
}

export interface RadarSourcesResult {
  sources: RadarSource[];
  adapters: SourceAdapter[];
}

export interface RadarSourceResult {
  source: RadarSource;
  message: string;
}

export interface RadarRunResult {
  run: RadarRun;
  results: RadarResult[];
  alerts: RadarAlert[];
  message: string;
}

export interface RadarRunsResult {
  runs: RadarRun[];
}

export interface RadarResultsResult {
  results: RadarResult[];
}

export interface RadarResultEnvelope {
  result: RadarResult;
  message: string;
}

export interface RadarSaveInboxResult {
  result: RadarResult;
  inbox_item: OpportunityInboxItem;
  message: string;
}

export interface RadarSaveTrackerResult {
  result: RadarResult;
  tracker_id: string;
  message: string;
}

export interface RadarAlertsResult {
  alerts: RadarAlert[];
}

export interface RadarAlertResult {
  alert: RadarAlert;
  message: string;
}
