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
  | "ready_to_apply"
  | "applied"
  | "message_sent"
  | "follow_up"
  | "interview"
  | "tech_test"
  | "rejected"
  | "offer"
  | "archived"
  | "saved"
  | "response";

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
  status: string;
  tracker_id?: string;
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
