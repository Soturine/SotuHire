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

export interface DataHealthIssue {
  code: string;
  severity: "info" | "warning" | "error";
  message: string;
  store: string;
  record_id: string;
}

export interface DataHealth {
  checked_at: string;
  healthy: boolean;
  database_present: boolean;
  schema_version: number;
  counts: Record<string, number>;
  issues: DataHealthIssue[];
}

export interface DataArchive {
  archive_name: string;
  kind: "backup" | "export";
  app_version: string;
  schema_version: number;
  created_at: string;
  size: number;
  files_count: number;
  download_url: string;
}

export interface DataArchivesResult {
  archives: DataArchive[];
}

export interface DataRestorePayload {
  archive_name: string;
  apply?: boolean;
  confirmation?: string;
}

export interface DataRestoreResult {
  archive_name: string;
  dry_run: boolean;
  files_validated: number;
  files_restored: number;
  pre_restore_backup_name: string;
  warnings: string[];
  message: string;
}

export type AnalysisMode = "local" | "ai" | "fallback";

export interface TraceEvidence {
  title: string;
  content?: string;
  kind?: string;
  source?: string;
  source_ref?: string;
  confidence?: "low" | "medium" | "high";
  confirmed_by_user?: boolean;
  sensitive?: boolean;
  score?: number;
}

export interface AnalysisMeta {
  provider_requested?: string;
  provider_used?: string;
  requested_provider?: string;
  analysis_mode?: AnalysisMode;
  fallback_used?: boolean;
  fallback_reason?: string;
  model_requested?: string;
  model_used?: string;
  model?: string;
  prompt_id?: string;
  prompt_version?: string;
  generated_at?: string;
  request_id?: string;
  source_refs?: string[];
  evidence_used?: TraceEvidence[];
  needs_user_review?: boolean;
  warnings?: string[];
}

export type AiProvider = "local" | "gemini" | "openai" | "openai_future";
export type AiSettingsStatus = "ready" | "configured" | "not_configured" | "planned" | "error";
export type AiSettingsPreset = "local_safe" | "basic" | "complete" | "custom";

export interface AiSettings {
  provider: AiProvider;
  model: string;
  configured: boolean;
  status: AiSettingsStatus;
  preset: AiSettingsPreset;
  use_ai: boolean;
  allow_profile: boolean;
  allow_lattes: boolean;
  allow_resume: boolean;
  allow_job: boolean;
  allow_public_exams: boolean;
  allow_match: boolean;
  allow_ats: boolean;
  allow_tailor: boolean;
  allow_github: boolean;
  allow_source_import: boolean;
  allow_extension: boolean;
  allow_radar: boolean;
  allow_notifications: boolean;
  allow_memory_context: boolean;
  updated_at?: string;
  warnings?: string[];
}

export interface AiSettingsPayload {
  provider: AiProvider;
  model: string;
  api_key?: string;
  preset?: AiSettingsPreset;
  use_ai: boolean;
  allow_profile?: boolean;
  allow_lattes?: boolean;
  allow_resume: boolean;
  allow_job: boolean;
  allow_public_exams?: boolean;
  allow_match: boolean;
  allow_ats: boolean;
  allow_tailor: boolean;
  allow_github: boolean;
  allow_source_import: boolean;
  allow_extension?: boolean;
  allow_radar: boolean;
  allow_notifications?: boolean;
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

export interface AiProviderInfo {
  id: "local" | "gemini" | "openai";
  label: string;
  status: string;
  requires_api_key: boolean;
  key_url?: string;
  supports_model_catalog: boolean;
  warnings?: string[];
}

export interface AiProvidersResult {
  providers: AiProviderInfo[];
}

export interface AiModelInfo {
  id: string;
  label: string;
  status: string;
  supports_structured_output: boolean;
  supports_json: boolean;
  recommended_for: string[];
}

export interface AiModelsResult {
  provider: "local" | "gemini" | "openai";
  models: AiModelInfo[];
  source: "cache" | "provider_api" | "builtin";
  updated_at?: string;
  warnings?: string[];
}

export type ProfileConfidence = "low" | "medium" | "high";

export interface ProfileItem {
  item_id: string;
  type: string;
  title: string;
  description?: string | null;
  area?: string | null;
  domain?: string | null;
  institution?: string | null;
  organization?: string | null;
  status?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  tags: string[];
  skills: string[];
  evidence?: string | null;
  source: string;
  source_ref?: string | null;
  confidence: ProfileConfidence;
  confirmed_by_user: boolean;
  sensitive: boolean;
  created_at: string;
  updated_at: string;
}

export interface UniversalCareerProfile {
  profile_id: string;
  display_name?: string | null;
  headline?: string | null;
  summary?: string | null;
  primary_domains: string[];
  secondary_domains: string[];
  career_moments: string[];
  target_roles: string[];
  target_seniority: string[];
  preferred_locations: string[];
  preferred_work_models: string[];
  preferred_contract_types: string[];
  constraints: ProfileItem[];
  items: ProfileItem[];
  source_summaries: Array<{
    source: string;
    source_type: string;
    item_count: number;
    last_imported_at?: string | null;
  }>;
  updated_at: string;
  created_at: string;
}

export interface ProfileResult {
  profile: UniversalCareerProfile;
  message?: string;
}

export interface ProfileItemResult {
  item: ProfileItem;
  message?: string;
}

export interface ProfileImportResult {
  items: ProfileItem[];
  detected_domains: string[];
  career_moments: string[];
  warnings: string[];
  questions_to_confirm: string[];
  provider_used: string;
  requested_provider: string;
  analysis_mode: AnalysisMode;
  needs_user_review: boolean;
}

export interface LattesImportResult {
  items: ProfileItem[];
  detected_sections: string[];
  assumptions: string[];
  questions_to_confirm: string[];
  warnings: string[];
  confidence: ProfileConfidence;
  needs_user_review: boolean;
  provider_used: string;
  requested_provider: string;
  analysis_mode: AnalysisMode;
}

export interface LattesConfirmResult {
  saved: ProfileItem[];
  skipped_duplicates: ProfileItem[];
  message: string;
}

export type ExamRequirementStatus = "matched" | "missing" | "uncertain";
export type ExamRecommendation =
  | "strong_fit"
  | "good_fit"
  | "review_requirements"
  | "risky"
  | "not_recommended"
  | "insufficient_information";

export interface ExamRequirement {
  requirement_id: string;
  kind: string;
  description: string;
  mandatory: boolean;
  evidence_needed: string;
  matched_profile_item_ids: string[];
  match_status: ExamRequirementStatus;
  confidence: ProfileConfidence;
  warnings: string[];
}

export interface ExamSubject {
  name: string;
  topics: string[];
  weight?: number | null;
  questions?: number | null;
  stage: string;
  priority: string;
  source_excerpt: string;
}

export interface ExamTimeline {
  registration_start: string;
  registration_end: string;
  payment_deadline: string;
  exam_date: string;
  result_date: string;
  appeal_deadlines: string[];
  document_submission_deadline: string;
  other_dates: string[];
  warnings: string[];
}

export interface ExamRole {
  role_id: string;
  notice_id: string;
  title: string;
  area: string;
  level: string;
  education_level: string;
  required_degree: string;
  required_registry: string;
  required_experience: string;
  required_certifications: string[];
  salary: string;
  workload: string;
  vacancies: string;
  reserved_vacancies: string;
  quota_notes: string;
  contract_type: string;
  employment_regime: string;
  location: string;
  requirements: ExamRequirement[];
  subjects: ExamSubject[];
  stages: string[];
}

export interface ExamNotice {
  notice_id: string;
  title: string;
  raw_text: string;
  source_url: string;
  source_name: string;
  organization: string;
  exam_board: string;
  notice_number: string;
  publication_date: string;
  registration_fee: string;
  status: string;
  opportunity_type: string;
  locations: string[];
  roles: ExamRole[];
  timeline: ExamTimeline;
  documents: string[];
  general_requirements: ExamRequirement[];
  subjects: ExamSubject[];
  warnings: string[];
  created_at: string;
  updated_at: string;
}

export interface ExamFitScore {
  overall_score: number;
  requirement_score: number;
  timeline_score: number;
  location_score: number;
  salary_score: number;
  study_effort_score: number;
  profile_alignment_score: number;
  risk_score: number;
  recommendation: ExamRecommendation;
  matched_requirements: ExamRequirement[];
  missing_requirements: ExamRequirement[];
  uncertain_requirements: ExamRequirement[];
  warnings: string[];
}

export interface StudyPlanDraft {
  days_until_exam?: number | null;
  weekly_hours: number;
  subjects: ExamSubject[];
  priority_topics: string[];
  schedule_blocks: string[];
  warnings: string[];
}

export interface PublicExamImportResult {
  notice: ExamNotice;
  roles: ExamRole[];
  timeline: ExamTimeline;
  subjects: ExamSubject[];
  requirements: ExamRequirement[];
  warnings: string[];
  questions_to_confirm: string[];
  source_excerpts: string[];
  needs_user_review: boolean;
  provider_used: string;
  requested_provider: string;
  analysis_mode: AnalysisMode;
}

export interface PublicExamListResult {
  notices: ExamNotice[];
}

export interface PublicExamConfirmResult {
  notice: ExamNotice;
  message: string;
}

export interface PublicExamAnalyzeResult {
  notice: ExamNotice;
  role?: ExamRole | null;
  fit_score: ExamFitScore;
  context_summary: string;
  checklist: ExamRequirement[];
  warnings: string[];
}

export interface PublicExamStudyPlanResult {
  notice: ExamNotice;
  role?: ExamRole | null;
  study_plan: StudyPlanDraft;
  warnings: string[];
}

export interface ProfileDeduplicateResult {
  suggestions: Array<{
    suggestion_id: string;
    item_ids: string[];
    reason: string;
    confidence: ProfileConfidence;
    proposed_title: string;
    proposed_description?: string | null;
    sources: string[];
  }>;
  message?: string;
}

export interface ProfileContextResult {
  context: {
    identity: Record<string, unknown>;
    career_goals: string[];
    education: ProfileItem[];
    experiences: ProfileItem[];
    academic_experiences: ProfileItem[];
    projects: ProfileItem[];
    certifications_and_registries: ProfileItem[];
    skills: ProfileItem[];
    languages: ProfileItem[];
    locations: string[];
    preferences: string[];
    constraints: string[];
    application_history_signals: string[];
  };
  message?: string;
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
  profile_evidence_candidates?: TraceEvidence[];
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
  job_snapshot_id?: string;
  resume_snapshot_id?: string;
  tailored_resume_snapshot_id?: string;
  match_analysis_snapshot_id?: string;
  ats_analysis_snapshot_id?: string;
  source_capture_id?: string;
  applied_at?: string;
  stage_history?: Array<Record<string, unknown>>;
  contact_history?: Array<Record<string, unknown>>;
  interview_notes?: string;
  follow_up_at?: string;
  outcome?: string;
  outcome_reason?: string;
}

export interface TrackerJobContext {
  context_summary: string;
  fit_reason: string;
  next_action_hint: string;
  aligned_with_profile?: boolean | null;
  recurring_gaps: string[];
}

export interface TrackerJobsResult {
  jobs: TrackerJob[];
  context_summary: string;
  job_contexts: Record<string, TrackerJobContext>;
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
  profile_available?: boolean;
  profile_summary?: string;
  enabled_flows?: string[];
  ai_provider_status?: string;
  warnings?: string[];
  extension_version?: string;
  companion_version?: string;
  api_version?: string;
  compatible?: boolean;
  capabilities?: string[];
}

export interface ExtensionHandshake {
  extension_version: string;
  companion_version: string;
  api_version: string;
  app_version: string;
  capabilities: string[];
  compatible: boolean;
  warnings: string[];
  min_supported_extension_version: string;
  max_tested_extension_version: string;
  min_supported_companion_version: string;
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
  profile_candidate_count?: number;
  context_signal?: string;
  captured_at?: string;
  updated_at?: string;
  snapshot_id?: string;
  content_hash?: string;
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

export interface ExtensionImportPublicExamResult {
  capture_id: string;
  draft: PublicExamImportResult;
  message: string;
}

export interface ExtensionCapturePatchResult {
  capture: ExtensionCapture;
  message: string;
}

export interface ExtensionContextResult {
  context_summary: string;
  message: string;
  profile_available?: boolean;
  profile_summary?: string;
  enabled_flows?: string[];
  ai_provider_status?: string;
  warnings?: string[];
}

export interface ExtensionProfileCandidatesResult {
  capture_id?: string;
  project_id?: string;
  candidates: ProfileItem[];
  context_summary?: string;
  warnings: string[];
  message: string;
}

export interface ExtensionAddToProfileResult {
  capture_id?: string;
  project_id?: string;
  added: ProfileItem[];
  skipped: string[];
  message: string;
}

export type SourceOrigin =
  | "manual_text"
  | "manual_url"
  | "csv_import"
  | "json_import"
  | "extension_capture"
  | "companion_capture"
  | "authenticated_assisted_capture"
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
  | "recurring_csv_json"
  | "authenticated_assisted_capture"
  | "public_exam"
  | "academic_call"
  | "scholarship"
  | "residency"
  | "internship_public";

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
  notes?: string;
  created_at?: string;
  updated_at?: string;
  is_active: boolean;
}

export interface WishlistDraftPayload {
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
  is_active: boolean;
  notes?: string;
}

export interface WishlistDraftResult {
  wishlist: WishlistDraftPayload;
  confidence: number;
  detected_domains: string[];
  detected_career_moments: string[];
  assumptions: string[];
  questions_to_confirm: string[];
  warnings: string[];
  needs_user_review: boolean;
  provider_used: string;
  analysis_mode: AnalysisMode;
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

export type RadarScheduleFrequency = "hourly" | "daily" | "weekly" | "custom_interval";
export type RadarScheduledRunStatus = "running" | "success" | "warning" | "error" | "skipped";
export type NotificationSeverity = "info" | "success" | "warning" | "error";

export interface RadarSchedule {
  schedule_id: string;
  name: string;
  enabled: boolean;
  wishlist_id?: string | null;
  source_ids: string[];
  keywords: string[];
  use_ai: boolean;
  use_profile_context: boolean;
  frequency: RadarScheduleFrequency;
  interval_minutes?: number | null;
  timezone: string;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  cooldown_minutes: number;
  min_match_score?: number | null;
  min_ats_score?: number | null;
  notify_on_new_matches: boolean;
  notify_on_score_threshold: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
}

export interface RadarScheduledRun {
  run_id: string;
  schedule_id: string;
  started_at?: string;
  finished_at?: string | null;
  status: RadarScheduledRunStatus;
  total_results: number;
  new_results: number;
  alerts_created: number;
  warnings: string[];
  error?: string | null;
  radar_run_id?: string | null;
  profile_context_used: boolean;
  manual: boolean;
  metadata?: Record<string, unknown>;
}

export interface LocalNotification {
  notification_id: string;
  type: string;
  title: string;
  message: string;
  severity: NotificationSeverity;
  source: string;
  related_entity_type?: string | null;
  related_entity_id?: string | null;
  created_at?: string;
  read_at?: string | null;
  dismissed_at?: string | null;
  metadata?: Record<string, unknown>;
}

export interface RadarSchedulerStatus {
  running: boolean;
  enabled_schedules: number;
  total_schedules: number;
  next_run_at?: string | null;
  due_schedules: number;
}

export interface RadarSchedulesResult {
  schedules: RadarSchedule[];
}

export interface RadarScheduleResult {
  schedule: RadarSchedule;
  message: string;
}

export interface RadarScheduledRunResult {
  scheduled_run: RadarScheduledRun;
  notifications: LocalNotification[];
  message: string;
}

export interface RadarScheduledRunsResult {
  scheduled_runs: RadarScheduledRun[];
}

export interface NotificationsResult {
  notifications: LocalNotification[];
  unread_count: number;
}

export interface NotificationResult {
  notification: LocalNotification;
  message: string;
}

export interface NotificationBulkResult {
  count: number;
  message: string;
}

export interface RadarResult {
  id: string;
  run_id?: string;
  source_id?: string;
  source_name?: string;
  source_type: RadarSourceType;
  opportunity_type?:
    | "job"
    | "public_exam"
    | "academic_call"
    | "scholarship"
    | "residency"
    | "internship_public";
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

export type SampleConfidence = "insufficient" | "indicative" | "comparable";

export interface AiQualitySummary {
  executions: number;
  schema_validity?: number | null;
  fallback_rate?: number | null;
  average_latency_ms?: number | null;
  total_tokens: number;
  estimated_cost: number | null;
  human_acceptance_rate?: number | null;
  human_edit_rate?: number | null;
  human_rejection_rate?: number | null;
  unsupported_claim_rate?: number | null;
  sample_confidence: SampleConfidence | string;
  empty_state: boolean;
  message: string;
}

export interface AiRunTrace {
  run_id: string;
  task_id: string;
  feature: string;
  provider_requested: string;
  provider_used: string;
  model_requested: string;
  model_used: string;
  prompt_id: string;
  prompt_version: string;
  analysis_mode: "local" | "ai" | "fallback";
  schema_valid: boolean;
  fallback_used: boolean;
  fallback_reason: string;
  latency_ms?: number | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  total_tokens?: number | null;
  estimated_cost?: number | null;
  context_purpose: string;
  context_item_count: number;
  evidence_count: number;
  warnings: string[];
  needs_user_review: boolean;
  started_at: string;
  finished_at: string;
}

export interface AiRunsPage {
  items: AiRunTrace[];
  total: number;
  limit: number;
  offset: number;
}

export interface AiProviderComparison {
  task: string;
  provider: string;
  model: string;
  sample_size: number;
  sample_confidence: SampleConfidence;
  quality: number;
  latency_ms?: number | null;
  cost: number;
  fallback_rate: number;
  acceptance_rate?: number | null;
}

export interface AiPromptQuality {
  task_id: string;
  prompt_id: string;
  prompt_version: string;
  evaluation_suite: string;
  providers_supported: string[];
  run_count: number;
  baseline_status: string;
}

export interface AiBenchmarkSummary {
  benchmark_run_id: string;
  git_sha: string;
  app_version: string;
  suite: string;
  providers: string[];
  models: string[];
  dataset_version: string;
  environment: string;
  started_at: string;
  finished_at: string;
  status: string;
}

export interface AiFeedback {
  feedback_id: string;
  run_id: string;
  task_id: string;
  rating: "useful" | "partial" | "not_useful";
  decision: "accepted" | "edited" | "rejected" | "ignored";
  edited: boolean;
  unsupported_claim: boolean;
  comment: string;
  created_at: string;
}

export interface AiFeedbackPage {
  items: AiFeedback[];
  limit: number;
  offset: number;
}

export interface OutcomeRate {
  value: number;
  numerator: number;
  denominator: number;
  sample_size: number;
  confidence: SampleConfidence;
  note: string;
}

export interface OutcomeGroup {
  key: string;
  applications: number;
  responses: number;
  interviews: number;
  offers: number;
  response_rate: number;
  confidence: SampleConfidence;
}

export interface OutcomeSummary {
  sample_size: number;
  confidence: SampleConfidence;
  response_rate: OutcomeRate;
  interview_rate: OutcomeRate;
  offer_rate: OutcomeRate;
  average_time_to_response_hours?: number | null;
  average_time_in_stage_hours?: number | null;
  source_effectiveness: OutcomeGroup[];
  resume_variant_effectiveness: OutcomeGroup[];
  match_score_vs_outcome: {
    sample_size: number;
    successful_average?: number | null;
    other_average?: number | null;
    confidence: SampleConfidence;
    note: string;
  };
  ats_score_vs_outcome: {
    sample_size: number;
    successful_average?: number | null;
    other_average?: number | null;
    confidence: SampleConfidence;
    note: string;
  };
  note: string;
}
